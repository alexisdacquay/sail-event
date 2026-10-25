"""Search-run pipeline v2: nine stages — criteria, window, plan, search,
extract, detail-hop, filter, judge, triage, persist run."""

from __future__ import annotations

import contextvars
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime

from opentelemetry import trace, metrics
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..adapters.factory import get_language_model, get_search_provider
from ..adapters.search import remove_known_pages
from ..services import clock
from ..services.budget import check_search_budget, check_llm_budget, reserve_llm_calls
from ..services.criteria import needs_parse, parse_criteria, parse_metadata
from ..services.window import resolve
from ..services.extract import extract_events
from ..services.detail_hop import detail_hop
from ..services.filters import attach_offset, filter_events
from ..services.judge import judge_event, Verdict, JudgeError, band_word
from ..services.dedup import DUPLICATE_PREFIX, dedup_run
from .. import orm

logger = logging.getLogger("sail-event.pipeline")
tracer = trace.get_tracer("sail-event.pipeline")
meter = metrics.get_meter("sail-event.pipeline")
# 10, not 50: see EXTRACT_CONCURRENCY in extract.py.
JUDGE_CONCURRENCY = int(os.environ.get("JUDGE_CONCURRENCY", "10"))

# --- §9 metrics ---

_runs_counter = meter.create_counter(
    "sail_runs_total",
    description="Total search runs",
)
_events_found_counter = meter.create_counter(
    "sail_events_found_total",
    description="Total events found across runs",
)
_events_new_counter = meter.create_counter(
    "sail_events_new_total",
    description="Total new events across runs",
)
_run_duration = meter.create_histogram(
    "sail_run_duration_seconds",
    description="Elapsed wall-time of one run_pipeline call",
    unit="s",
)
_stage_items = meter.create_counter(
    "sail_stage_items_total",
    description="Items per stage with outcome (filter reason or kept)",
)
_llm_calls_counter = meter.create_counter(
    "sail_llm_calls_total",
    description="LLM calls by prompt and provider",
)
_llm_tokens_counter = meter.create_counter(
    "sail_llm_tokens_total",
    description="LLM tokens by direction",
)
_search_calls_counter = meter.create_counter(
    "sail_search_calls_total",
    description="Search calls by provider and outcome",
)
_budget_stops_counter = meter.create_counter(
    "sail_budget_stops_total",
    description="Budget stop events by type",
)


def _compute_cost(search_calls: int, llm_tokens_in: int, llm_tokens_out: int) -> float | None:
    """cost_usd from §8: null when any price env var is unset."""
    raw_in = os.environ.get("LLM_USD_PER_1K_IN")
    raw_out = os.environ.get("LLM_USD_PER_1K_OUT")
    raw_search = os.environ.get("SEARCH_USD_PER_CALL")
    if raw_in is None or raw_out is None or raw_search is None:
        return None
    return (
        llm_tokens_in / 1000 * float(raw_in)
        + llm_tokens_out / 1000 * float(raw_out)
        + search_calls * float(raw_search)
    )


def _update_run_stage(run: orm.Run, db: Session, stage: str, counts: dict[str, int]) -> None:
    """Write current_stage and stage_counts to the run row (one UPDATE per stage)."""
    run.current_stage = stage
    run.stage_counts = json.dumps(counts)
    db.commit()


def run_pipeline(
    user: orm.User, db: Session, *, trigger: str, run_id: str | None = None,
) -> orm.Run:
    """Execute one search run for a user.  Always returns a Run row.

    When *run_id* is given (enqueue-time row from search_all), reuse it
    instead of creating a second row.
    """
    t0 = time.monotonic()

    with tracer.start_as_current_span("search_run", attributes={
        "user_id": user.id,
        "trigger": trigger,
    }) as span:
        logger.info("search run started")

        if run_id:
            run = db.query(orm.Run).filter(orm.Run.id == run_id).first()
            if run is None:
                # Row deleted between enqueue and execution; create a new one
                run = orm.Run(user_id=user.id, started_at=datetime.now(UTC), trigger=trigger)
                db.add(run)
                db.flush()
        else:
            run = orm.Run(user_id=user.id, started_at=datetime.now(UTC), trigger=trigger)
            db.add(run)
            db.flush()
        span.set_attribute("run_id", run.id)

        # Accumulators; the version goes in from the start so a live run never reads as an old one
        counts: dict[str, int] = {"counts_version": COUNTS_VERSION}
        search_calls = 0
        llm_calls = 0
        llm_tokens_in = 0
        llm_tokens_out = 0
        events_found = 0
        events_new = 0
        error_msg: str | None = None
        error_detail: str | None = None
        stopped_at_stage: str | None = None
        current_stage: str | None = None

        try:
            # --- get adapters (may fail in prod with fixture/fake) ---
            current_stage = "adapters"
            _update_run_stage(run, db, current_stage, counts)
            try:
                provider = get_search_provider()
                model = get_language_model()
            except Exception as exc:
                error_msg = f"{type(exc).__name__}: {str(exc)[:200]}"
                stopped_at_stage = "adapters"
                run = _finalise_run(
                    run, db, events_found, events_new, error_msg,
                    counts, search_calls, llm_calls, llm_tokens_in, llm_tokens_out,
                    stopped_at_stage, error_detail,
                )
                elapsed = time.monotonic() - t0
                _emit_metrics(trigger, error_msg, events_found, events_new, elapsed)
                return run

            # Deferred prod guards refuse at first use
            if getattr(provider, '_refused', False) or getattr(model, '_refused', False):
                error_msg = "RuntimeError: adapters refused in prod: set SEARCH_PROVIDER and LLM_PROVIDER"
                stopped_at_stage = "adapters"
                run = _finalise_run(
                    run, db, events_found, events_new, error_msg,
                    counts, search_calls, llm_calls, llm_tokens_in, llm_tokens_out,
                    stopped_at_stage, error_detail,
                )
                elapsed = time.monotonic() - t0
                _emit_metrics(trigger, error_msg, events_found, events_new, elapsed)
                return run

            criteria_row = db.query(orm.Criteria).filter(
                orm.Criteria.user_id == user.id,
            ).first()
            criteria_text = criteria_row.text if criteria_row else ""
            user_tz = user.time_zone or "UTC"

            # --- Recovery: score leftover `new` events from prior crashed runs ---
            # #142: only events of finished runs; a run still in flight is judging its own
            leftover = db.query(orm.Event).outerjoin(orm.Run, orm.Event.run_id == orm.Run.id).filter(
                orm.Event.user_id == user.id,
                orm.Event.status == "new",
                or_(orm.Event.run_id.is_(None), orm.Run.finished_at.isnot(None)),
            ).all()
            leftover = _reserve_judge(db, run, llm_calls, leftover)
            if leftover:
                llm_c, tok_in, tok_out, j_err, j_rep = _judge_and_triage(
                    leftover, criteria_row, criteria_text, user_tz, user, model, db,
                )
                llm_calls += llm_c
                llm_tokens_in += tok_in
                llm_tokens_out += tok_out
                # an older run's events: kept apart so judge_errors is this run's own "not scored yet"
                counts["recovery_judge_errors"] = j_err
                counts["judge_repaired"] = counts.get("judge_repaired", 0) + j_rep
            run.llm_calls = llm_calls  # release the unused reservation
            db.commit()

            # --- Stage 1: understand criteria ---
            current_stage = "criteria"
            _update_run_stage(run, db, current_stage, counts)
            if not criteria_text:
                error_msg = "no criteria text"
                stopped_at_stage = "criteria"
                _finalise_run(
                    run, db, events_found, events_new, error_msg,
                    counts, search_calls, llm_calls, llm_tokens_in, llm_tokens_out,
                    stopped_at_stage, error_detail,
                )
                elapsed = time.monotonic() - t0
                _emit_metrics(trigger, error_msg, events_found, events_new, elapsed)
                return run

            with tracer.start_as_current_span("criteria"):
                if criteria_row and criteria_text:
                    # Budget check before criteria LLM call
                    if needs_parse(criteria_text, criteria_row.facets_text_sha, criteria_row.facets_version):
                        budget_stop = check_llm_budget(db)
                        if budget_stop:
                            error_msg = budget_stop
                            stopped_at_stage = "criteria"
                            _budget_stops_counter.add(1, {"which": "llm"})
                            _finalise_run(
                                run, db, events_found, events_new, error_msg,
                                counts, search_calls, llm_calls, llm_tokens_in, llm_tokens_out,
                                stopped_at_stage, error_detail,
                            )
                            elapsed = time.monotonic() - t0
                            _emit_metrics(trigger, error_msg, events_found, events_new, elapsed)
                            return run

                        facets_dict = parse_criteria(criteria_text, user_tz, model)
                        meta = parse_metadata(criteria_text)
                        criteria_row.facets_json = json.dumps(facets_dict)
                        criteria_row.facets_version = meta["facets_version"]
                        criteria_row.facets_text_sha = meta["facets_text_sha"]
                        criteria_row.parsed_at = meta["parsed_at"]
                        llm_calls += 1
                        _llm_calls_counter.add(1, {"prompt": "criteria", "provider": getattr(model, "model_id", "unknown")})
                        db.flush()

                facets = json.loads(criteria_row.facets_json) if criteria_row and criteria_row.facets_json else {}

            # --- Stage 2: resolve window ---
            current_stage = "window"
            _update_run_stage(run, db, current_stage, counts)
            with tracer.start_as_current_span("window"):
                date_facets = facets.get("date", {}) or {}
                window = resolve(date_facets, user_tz)

            # --- Stage 3: search (verbatim query, no planner) ---
            current_stage = "search"
            _update_run_stage(run, db, current_stage, counts)
            # Depth selection: scheduled runs default to basic (cheap)
            if trigger == "scheduled":
                search_depth = os.environ.get("TAVILY_SEARCH_DEPTH_SCHEDULED", "basic")
            else:
                search_depth = os.environ.get("TAVILY_SEARCH_DEPTH", "advanced")
            credits_per_call = int(os.environ.get("SEARCH_CREDITS_ADVANCED", "2")) if search_depth == "advanced" else 1
            # Budget check before search (credits, not calls)
            budget_stop = check_search_budget(db, credits_per_call)
            if budget_stop:
                error_msg = budget_stop
                stopped_at_stage = "search"
                _budget_stops_counter.add(1, {"which": "search"})
                _finalise_run(
                    run, db, events_found, events_new, error_msg,
                    counts, search_calls, llm_calls, llm_tokens_in, llm_tokens_out,
                    stopped_at_stage, error_detail,
                )
                elapsed = time.monotonic() - t0
                _emit_metrics(trigger, error_msg, events_found, events_new, elapsed)
                return run

            from ..adapters.search import SearchResult as SResult
            max_results_per_q = int(os.environ.get("MAX_RESULTS_PER_QUERY", "20"))
            all_results: list[SResult] = []
            provider_name = getattr(provider, "name", "unknown")

            with tracer.start_as_current_span("search"):
                search_errors = 0
                first_search_exc: str | None = None
                query_text = (criteria_text + " event") if criteria_text else ""
                counts["queries_planned"] = 1 if query_text else 0

                if query_text:
                    with tracer.start_as_current_span("query", attributes={
                        "provider": provider_name,
                    }) as qspan:
                        try:
                            results = provider.search(
                                query_text,
                                max_results=max_results_per_q,
                                search_depth=search_depth,
                            )
                            search_calls += credits_per_call
                            _search_calls_counter.add(1, {"provider": provider_name, "outcome": "ok"})
                            qspan.set_attribute("result_count", len(results))
                            all_results.extend(results)
                        except Exception as exc:
                            search_errors += 1
                            search_calls += credits_per_call
                            _search_calls_counter.add(1, {"provider": provider_name, "outcome": "error"})
                            if first_search_exc is None:
                                first_search_exc = f"{type(exc).__name__}: {str(exc)[:200]}"
                            if not error_detail:
                                error_detail = f"search: {first_search_exc}"
                            logger.warning("search error for query: %s", type(exc).__name__)

                counts["search_errors"] = search_errors
                counts["results_fetched"] = len(all_results)

                # When every query failed, promote to run error
                queries_planned = counts["queries_planned"]
                if queries_planned > 0 and search_errors >= queries_planned:
                    error_msg = first_search_exc
                    stopped_at_stage = "search"

                # Dedup results by URL
                seen_urls: set[str] = set()
                deduped_results: list[SResult] = []
                for r in all_results:
                    if r.url not in seen_urls:
                        seen_urls.add(r.url)
                        deduped_results.append(r)
                all_results = deduped_results

                # Remove known single-event pages
                stored_pages = [
                    {"source_url": e.source_url, "page_kind": e.page_kind}
                    for e in db.query(orm.Event).filter(
                        orm.Event.user_id == user.id,
                        orm.Event.source_url.isnot(None),
                    ).all()
                ]
                all_results, results_known = remove_known_pages(all_results, stored_pages)
                counts["results_known"] = results_known

                events_found = len(all_results)

            # --- Stage 5: extract ---
            current_stage = "extract"
            _update_run_stage(run, db, current_stage, counts)
            with tracer.start_as_current_span("extract"):
                # Budget check before extract LLM calls
                budget_stop = check_llm_budget(db)
                if budget_stop:
                    error_msg = budget_stop
                    stopped_at_stage = "extract"
                    _budget_stops_counter.add(1, {"which": "llm"})
                    _finalise_run(
                        run, db, events_found, events_new, error_msg,
                        counts, search_calls, llm_calls, llm_tokens_in, llm_tokens_out,
                        stopped_at_stage, error_detail,
                    )
                    elapsed = time.monotonic() - t0
                    _emit_metrics(trigger, error_msg, events_found, events_new, elapsed)
                    return run

                place = facets.get("place") or {}
                target_city = place.get("city") or ""
                target_country = place.get("country") or ""
                language = facets.get("language")

                def _on_page_done(ec):
                    counts["pages_content_pass"] = ec.pages_content_pass
                    _update_run_stage(run, db, "extract", counts)

                extracted, extract_counts = extract_events(
                    all_results,
                    window_start=window.start_utc,
                    window_end=window.end_utc,
                    target_city=target_city,
                    target_country=target_country,
                    language=language,
                    user_tz=user_tz,
                    model=model,
                    on_page_done=_on_page_done,
                )
                # Count LLM calls: 1 per full-page read + 1 if snippet-only fallback ran
                snippet_only = len([r for r in all_results if not r.raw_content])
                llm_calls += extract_counts.pages_content_pass
                if snippet_only:
                    llm_calls += 1  # snippet-only call
                extract_llm = extract_counts.pages_content_pass + (1 if snippet_only else 0)
                if extract_llm:
                    _llm_calls_counter.add(extract_llm, {"prompt": "extract", "provider": getattr(model, "model_id", "unknown")})

                counts["pages_content_pass"] = extract_counts.pages_content_pass
                counts["events_extracted"] = extract_counts.events_extracted
                counts["extract_errors"] = extract_counts.extract_errors
                if extract_counts.extract_errors > 0 and not error_detail:
                    error_detail = f"extract: {extract_counts.extract_errors} error(s)"
                # Page-level counts from extraction (#112: pages only, never events)
                counts["pages_with_events"] = extract_counts.pages_with_events
                counts["filtered_non_event"] = extract_counts.filtered_non_event
                # Per-page detail (#124)
                if extract_counts.page_details:
                    from ..services.extract import PageInfo
                    run.pages = json.dumps([
                        {"url": p.url, "title": p.title, "events": p.events, "kind": p.kind}
                        for p in extract_counts.page_details
                    ])

            # --- Stage 5b: detail-page hop ---
            current_stage = "detail_hop"
            _update_run_stage(run, db, current_stage, counts)
            with tracer.start_as_current_span("detail_hop"):
                def _on_detail_page_done(done, total):
                    counts["detail_pages_done"] = done
                    counts["detail_pages_to_open"] = total
                    _update_run_stage(run, db, "detail_hop", counts)

                extracted, hop_counts = detail_hop(
                    extracted,
                    model=model,
                    user_tz=user_tz,
                    window_start=window.start_utc,
                    window_end=window.end_utc,
                    target_city=target_city,
                    target_country=target_country,
                    on_page_done=_on_detail_page_done,
                )
                counts["pages_detail_fetched"] = hop_counts.pages_detail_fetched
                counts["detail_fetch_errors"] = hop_counts.detail_fetch_errors
                counts["detail_extract_errors"] = hop_counts.detail_extract_errors
                llm_calls += hop_counts.detail_llm_calls
                if hop_counts.detail_llm_calls:
                    _llm_calls_counter.add(hop_counts.detail_llm_calls, {"prompt": "extract", "provider": getattr(model, "model_id", "unknown")})
                if (hop_counts.detail_fetch_errors or hop_counts.detail_extract_errors) and not error_detail:
                    error_detail = (f"detail_hop: {hop_counts.detail_fetch_errors} fetch error(s), "
                                    f"{hop_counts.detail_extract_errors} extract error(s)")

            # --- Stage 6: filter ---
            current_stage = "filter"
            _update_run_stage(run, db, current_stage, counts)
            with tracer.start_as_current_span("filter"):
                now_utc = clock.now()
                # Stored events for dedup
                stored_events_raw = db.query(orm.Event).filter(
                    orm.Event.user_id == user.id,
                ).all()
                stored_for_filter = [
                    {
                        "link": e.link,
                        "date_time": e.date_time,
                        "title": e.title,
                        "status": e.status,
                        "page_kind": e.page_kind,
                    }
                    for e in stored_events_raw
                ]

                kept, filter_counts = filter_events(
                    extracted,
                    now_utc=now_utc,
                    window_start_utc=window.start_utc,
                    window_end_utc=window.end_utc,
                    target_city=place.get("city"),
                    target_country=place.get("country"),
                    user_tz=user_tz,
                    stored_events=stored_for_filter,
                )
                counts["filtered_incomplete"] = filter_counts.filtered_incomplete
                counts["filtered_past"] = filter_counts.filtered_past
                counts["filtered_date"] = filter_counts.filtered_date
                counts["filtered_place"] = filter_counts.filtered_place
                counts["filtered_no_date"] = filter_counts.filtered_no_date
                counts["filtered_no_time"] = filter_counts.filtered_no_time
                counts["filtered_duplicate"] = filter_counts.filtered_duplicate

                # §9 stage_items metrics
                _stage_items.add(filter_counts.filtered_incomplete, {"stage": "filter", "outcome": "incomplete"})
                _stage_items.add(filter_counts.filtered_past, {"stage": "filter", "outcome": "past"})
                _stage_items.add(filter_counts.filtered_date, {"stage": "filter", "outcome": "date"})
                _stage_items.add(filter_counts.filtered_place, {"stage": "filter", "outcome": "place"})
                _stage_items.add(filter_counts.filtered_no_date, {"stage": "filter", "outcome": "no_date"})
                _stage_items.add(filter_counts.filtered_no_time, {"stage": "filter", "outcome": "no_time"})
                _stage_items.add(filter_counts.filtered_duplicate, {"stage": "filter", "outcome": "duplicate"})
                _stage_items.add(len(kept), {"stage": "filter", "outcome": "kept"})

            # --- Phase 1: insert kept events as `new`, commit (crash-recoverable) ---
            to_judge = kept  # no per-search cap: every event that passes the filters is judged
            events_new = len(to_judge)

            for ev in to_judge:
                db.add(orm.Event(
                    user_id=user.id,
                    title=ev.title,
                    date_time=attach_offset(ev.start_local, ev.start_tz, ev.country),
                    place=f"{ev.venue or ''}, {ev.city or ''}, {ev.country or ''}".strip(", "),
                    link=ev.link,
                    description=ev.description,
                    start_tz=ev.start_tz,
                    end_time=attach_offset(ev.end_local, ev.start_tz, ev.country) if ev.end_local else None,
                    source_url=ev.source_url,
                    page_kind=ev.page_kind,
                    city=ev.city or "",
                    country=ev.country or "ZZ",
                    source_query=None,
                    extraction_confidence=ev.confidence,
                    status="new",
                    run_id=run.id,
                ))
            db.commit()

            # --- Stage 7 + 8: judge and triage ---
            current_stage = "judge"
            counts["events_to_judge"] = events_new  # live total for the progress bar
            _update_run_stage(run, db, current_stage, counts)
            if events_new > 0:
                inserted = db.query(orm.Event).filter(
                    orm.Event.user_id == user.id,
                    orm.Event.status == "new",
                    orm.Event.run_id == run.id,
                ).all()
                # Reserve the worst case before any judge call; what does not fit stays `new`
                to_run = _reserve_judge(db, run, llm_calls, inserted)
                if len(to_run) < len(inserted):
                    error_msg = "budget: llm"
                    stopped_at_stage = "judge"
                    _budget_stops_counter.add(1, {"which": "llm"})

                def _on_event_done(judged_so_far):
                    counts["events_judged"] = judged_so_far
                    _update_run_stage(run, db, "judge", counts)

                llm_c, tok_in, tok_out, j_err, j_rep = _judge_and_triage(
                    to_run, criteria_row, criteria_text, user_tz, user, model, db,
                    on_event_done=_on_event_done,
                )
                llm_calls += llm_c
                llm_tokens_in += tok_in
                llm_tokens_out += tok_out
                judge_errs = counts.get("judge_errors", 0) + j_err
                counts["judge_errors"] = judge_errs
                counts["judge_repaired"] = counts.get("judge_repaired", 0) + j_rep
                if j_err and not error_detail:
                    error_detail = f"judge: errors on {j_err} event(s)"
                db.commit()

            # --- #136: after-storage duplicate check, the run's last model step ---
            with tracer.start_as_current_span("dedup"):
                d = dedup_run(db, run, user.id, model, llm_calls, JUDGE_CONCURRENCY)
                llm_calls += d["calls"]
                llm_tokens_in += d["tokens_in"]
                llm_tokens_out += d["tokens_out"]
                if d["calls"]:
                    _llm_calls_counter.add(d["calls"], {"prompt": "dedup", "provider": getattr(model, "model_id", "unknown")})
                counts["dedup_merged"] = d["dedup_merged"]
                counts["dedup_errors"] = d["dedup_errors"]
                if d["short"] and not error_msg:
                    error_msg = "budget: llm"
                    stopped_at_stage = "judge"
                    _budget_stops_counter.add(1, {"which": "llm"})
                if d["dedup_errors"] and not error_detail:
                    error_detail = f"dedup: errors on {d['dedup_errors']} event(s)"

            # Count triage outcomes
            if events_new > 0:
                triaged = db.query(orm.Event).filter(
                    orm.Event.run_id == run.id,
                ).all()
                counts["events_judged"] = sum(1 for e in triaged if e.score is not None)
                counts["accepted"] = sum(1 for e in triaged if e.status == "accepted")
                counts["rejected"] = sum(1 for e in triaged if e.status == "rejected")
                counts["queued"] = sum(1 for e in triaged if e.status == "queued")
                counts.update(reject_bands(triaged))

            span.set_attribute("events_found", events_found)
            span.set_attribute("events_new", events_new)
            logger.info("search run completed")

        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {str(exc)[:200]}"
            if not error_detail:
                error_detail = f"pipeline: {error_msg}"
            if not stopped_at_stage:
                stopped_at_stage = current_stage
            span.record_exception(exc)
            span.set_status(trace.StatusCode.ERROR, type(exc).__name__)
            logger.error("search run failed: %s", type(exc).__name__)
            db.rollback()

        # --- Stage 9: persist run ---
        with tracer.start_as_current_span("persist"):
            run = _finalise_run(
                run, db, events_found, events_new, error_msg,
                counts, search_calls, llm_calls, llm_tokens_in, llm_tokens_out,
                stopped_at_stage, error_detail,
            )

        elapsed = time.monotonic() - t0
        _emit_metrics(trigger, error_msg, events_found, events_new, elapsed)
        return run


def _judge_order(evt: orm.Event) -> tuple:
    return (evt.source_url or "", evt.date_time or "", evt.title or "", evt.id or "")


def _reserve_judge(db: Session, run: orm.Run, spent: int, events: list[orm.Event]) -> list[orm.Event]:
    """#142: the events, in judge order, whose worst-case calls fit the daily budget (reserved on the run)."""
    if not events:
        return []
    events = sorted(events, key=_judge_order)
    return events[:reserve_llm_calls(db, run, spent, len(events))]


def _judge_and_triage(
    events: list[orm.Event],
    criteria_row: orm.Criteria | None,
    criteria_text: str,
    user_tz: str,
    user: orm.User,
    model,
    db: Session,
    on_event_done=None,
) -> tuple[int, int, int, int, int]:
    """Judge events and triage.  Returns (llm_calls, tokens_in, tokens_out, judge_errors, judge_repaired)."""
    facets = json.loads(criteria_row.facets_json) if criteria_row and criteria_row.facets_json else {}
    date_facets = facets.get("date", {}) or {}

    window = resolve(date_facets, user_tz)

    llm_calls = 0
    tokens_in = 0
    tokens_out = 0
    judge_errors = 0
    judge_repaired = 0

    from ..services.extract import ExtractedEvent

    def _strip_offset(dt_str: str | None) -> str | None:
        """Strip UTC offset from a stored datetime for the judge prompt.

        The judge sees local times as the extractor produced them;
        the offset is a storage/display concern only.
        """
        if not dt_str or len(dt_str) <= 10:
            return dt_str
        # Chop +HH:MM or -HH:MM or Z suffix
        import re
        return re.sub(r"[+-]\d{2}:\d{2}$|Z$", "", dt_str)

    # #142: sorted for determinism; inputs built here so workers never touch the session or ORM rows
    events = sorted(events, key=_judge_order)
    inputs = [
        ExtractedEvent(
            title=evt.title,
            start_local=_strip_offset(evt.date_time),
            start_tz=evt.start_tz,
            end_local=_strip_offset(evt.end_time),
            venue=None,
            city=evt.city,
            country=evt.country,
            link=evt.link,
            description=evt.description,
            confidence=evt.extraction_confidence or 1.0,
            source_url=evt.source_url or evt.link,
            page_kind=evt.page_kind or "single_event",
        )
        for evt in events
    ]
    results: list[Verdict | JudgeError | None] = [None] * len(events)
    provider = getattr(model, "model_id", "unknown")

    def _judge_one(i: int):
        """Worker: plain dataclass in, (index, result) out; no db, counters or callbacks."""
        extracted = inputs[i]
        with tracer.start_as_current_span("event", attributes={"capped": False}) as espan:
            result = judge_event(
                extracted,
                criteria_text=criteria_text,
                facets=facets,
                window_start=window.start_utc,
                window_end=window.end_utc,
                user_tz=user_tz,
                model=model,
            )
            if isinstance(result, Verdict):
                espan.set_attribute("score", result.score)
                espan.set_attribute("capped", result.capped)
                try:
                    from urllib.parse import urlparse
                    espan.set_attribute("source_host", urlparse(extracted.source_url).hostname or "")
                except Exception:
                    pass
            return i, result

    with tracer.start_as_current_span("judge"):
        if events:
            with ThreadPoolExecutor(max_workers=min(JUDGE_CONCURRENCY, len(events))) as pool:
                futures = [pool.submit(contextvars.copy_context().run, _judge_one, i) for i in range(len(events))]
                try:
                    for done, future in enumerate(as_completed(futures), 1):
                        i, result = future.result()
                        results[i] = result
                        llm_calls += result.calls
                        tokens_in += result.tokens_in
                        tokens_out += result.tokens_out
                        _llm_calls_counter.add(result.calls, {"prompt": "judge", "provider": provider})
                        if isinstance(result, JudgeError):
                            judge_errors += 1  # event stays `new`
                            logger.warning("judge error: %s", result.error)
                        elif result.repaired:
                            judge_repaired += 1
                        if on_event_done:
                            on_event_done(done)
                except BaseException:
                    # A failed run stops spending: drop queued calls, events stay `new`
                    pool.shutdown(cancel_futures=True)
                    raise

        # Apply in sorted order, never completion order
        for evt, result in zip(events, results):
            if not isinstance(result, Verdict):
                continue
            if not result.is_event:
                # Drop non-events: mark rejected with score 0
                evt.score = 0
                evt.score_reason = result.reason or "not an event"
                evt.status = "rejected"
                evt.decided_by = "auto"
            else:
                evt.score = result.score
                evt.score_reason = result.reason
            evt.judge_model = model.model_id if hasattr(model, "model_id") else None
            evt.judge_version = "judge_v3"

    # Triage
    with tracer.start_as_current_span("triage"):
        for evt in events:
            if evt.score is None:
                continue  # judge errored, stays new
            if evt.status == "rejected" and evt.decided_by == "auto":
                continue  # already handled (non-event)
            if evt.score >= user.upper_threshold:
                evt.status = "accepted"
                evt.decided_by = "auto"
            elif evt.score <= user.lower_threshold:
                evt.status = "rejected"
                evt.decided_by = "auto"
            else:
                evt.status = "queued"

    return llm_calls, tokens_in, tokens_out, judge_errors, judge_repaired


# #118: shape of stage_counts. 1 = before reject bands, 2 = before filtered_no_date, 3 = before detail hop, 4 = now.
COUNTS_VERSION = 4


def reject_bands(events: list[orm.Event]) -> dict[str, int]:
    """#108 funnel bands of a run's rejected events: judge scores 0-9 mean wrong place/dates, 10-39 off topic.

    #136: a duplicate keeps its judge score but is counted in dedup_merged, never in a band.
    """
    scores = [e.score or 0 for e in events
              if e.status == "rejected" and not (e.score_reason or "").startswith(DUPLICATE_PREFIX)]
    return {
        "rejected_date_place": sum(1 for s in scores if s <= 9),
        "rejected_off_topic": sum(1 for s in scores if 10 <= s <= 39),
        "rejected_other": sum(1 for s in scores if s >= 40),
    }


def _finalise_run(
    run: orm.Run,
    db: Session,
    events_found: int,
    events_new: int,
    error_msg: str | None,
    counts: dict[str, int],
    search_calls: int,
    llm_calls: int,
    llm_tokens_in: int,
    llm_tokens_out: int,
    stopped_at_stage: str | None,
    error_detail: str | None,
) -> orm.Run:
    """Write final fields on the run row and commit.  Returns the attached row."""
    run = db.merge(run)
    # #108/#112: the funnel reads these on every finished run, also when it stopped early
    for k in ("rejected_date_place", "rejected_off_topic", "rejected_other",
              "filtered_no_date", "filtered_no_time", "pages_with_events",
              "pages_detail_fetched", "detail_fetch_errors", "detail_extract_errors",
              "dedup_merged", "dedup_errors"):
        counts.setdefault(k, 0)
    counts["counts_version"] = COUNTS_VERSION
    run.finished_at = datetime.now(UTC)
    run.events_found = events_found
    run.events_new = events_new
    run.error = error_msg
    run.stage_counts = json.dumps(counts)
    run.search_calls = search_calls
    run.llm_calls = llm_calls
    run.llm_tokens_in = llm_tokens_in
    run.llm_tokens_out = llm_tokens_out
    run.cost_usd = _compute_cost(search_calls, llm_tokens_in, llm_tokens_out)
    run.current_stage = None  # run is done
    run.stopped_at_stage = stopped_at_stage
    run.error_detail = error_detail

    # §9 token metrics
    if llm_tokens_in:
        _llm_tokens_counter.add(llm_tokens_in, {"direction": "in"})
    if llm_tokens_out:
        _llm_tokens_counter.add(llm_tokens_out, {"direction": "out"})

    db.commit()
    return run


def _emit_metrics(
    trigger: str,
    error_msg: str | None,
    events_found: int,
    events_new: int,
    elapsed: float,
) -> None:
    outcome = "error" if error_msg else "ok"
    _runs_counter.add(1, {"trigger": trigger, "outcome": outcome})
    _events_found_counter.add(events_found)
    _events_new_counter.add(events_new)
    _run_duration.record(elapsed)
