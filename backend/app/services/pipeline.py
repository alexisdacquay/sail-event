"""Search-run pipeline v2: nine stages — criteria, window, plan, search,
extract, filter, judge, triage, persist run."""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import UTC, datetime

from opentelemetry import trace, metrics
from sqlalchemy.orm import Session

from ..adapters.factory import get_language_model, get_search_provider, get_guardrail
from ..adapters.search import remove_known_pages
from ..services import clock
from ..services.criteria import needs_parse, parse_criteria, parse_metadata
from ..services.window import WindowInPast, resolve
from ..services.planner import plan as plan_queries
from ..services.extract import extract_events
from ..services.filters import filter_events
from ..services.judge import judge_event, Verdict, JudgeError, band_word
from .. import orm

logger = logging.getLogger("sail-event.pipeline")
tracer = trace.get_tracer("sail-event.pipeline")
meter = metrics.get_meter("sail-event.pipeline")

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


def run_pipeline(user: orm.User, db: Session, *, trigger: str) -> orm.Run:
    """Execute one search run for a user.  Always returns a Run row."""
    t0 = time.monotonic()

    with tracer.start_as_current_span("search_run", attributes={
        "user_id": user.id,
        "trigger": trigger,
    }) as span:
        logger.info("search run started")

        run = orm.Run(user_id=user.id, started_at=datetime.now(UTC), trigger=trigger)
        db.add(run)
        db.flush()
        span.set_attribute("run_id", run.id)

        # Accumulators
        counts: dict[str, int] = {}
        search_calls = 0
        llm_calls = 0
        llm_tokens_in = 0
        llm_tokens_out = 0
        events_found = 0
        events_new = 0
        error_msg: str | None = None
        error_detail: str | None = None
        stopped_at_stage: str | None = None

        try:
            # --- get adapters (may fail in prod with fixture/fake) ---
            try:
                provider = get_search_provider()
                model = get_language_model()
                guardrail = get_guardrail()
            except RuntimeError as exc:
                error_msg = str(exc)
                _finalise_run(
                    run, db, events_found, events_new, error_msg,
                    counts, search_calls, llm_calls, llm_tokens_in, llm_tokens_out,
                    stopped_at_stage, error_detail,
                )
                elapsed = time.monotonic() - t0
                _emit_metrics(trigger, error_msg, events_found, events_new, elapsed)
                return run

            # Deferred prod guards refuse at first use
            if getattr(provider, '_refused', False) or getattr(model, '_refused', False):
                error_msg = "adapters refused in prod: set SEARCH_PROVIDER and LLM_PROVIDER"
                _finalise_run(
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
            leftover = db.query(orm.Event).filter(
                orm.Event.user_id == user.id,
                orm.Event.status == "new",
            ).all()
            if leftover:
                llm_c, tok_in, tok_out, j_err = _judge_and_triage(
                    leftover, criteria_row, criteria_text, user_tz, user, model, db,
                )
                llm_calls += llm_c
                llm_tokens_in += tok_in
                llm_tokens_out += tok_out
                counts["judge_errors"] = counts.get("judge_errors", 0) + j_err
                db.commit()

            # --- Stage 1: understand criteria ---
            with tracer.start_as_current_span("criteria"):
                if criteria_row and criteria_text:
                    if needs_parse(criteria_text, criteria_row.facets_text_sha, criteria_row.facets_version):
                        facets_dict = parse_criteria(criteria_text, user_tz, model)
                        meta = parse_metadata(criteria_text)
                        criteria_row.facets_json = json.dumps(facets_dict)
                        criteria_row.facets_version = meta["facets_version"]
                        criteria_row.facets_text_sha = meta["facets_text_sha"]
                        criteria_row.parsed_at = meta["parsed_at"]
                        llm_calls += 1
                        db.flush()

                facets = json.loads(criteria_row.facets_json) if criteria_row and criteria_row.facets_json else {}

            # --- Stage 2: resolve window ---
            with tracer.start_as_current_span("window"):
                date_facets = facets.get("date", {}) or {}
                try:
                    window = resolve(date_facets, user_tz)
                except WindowInPast:
                    error_msg = "dates in the past: edit your criteria"
                    _finalise_run(
                        run, db, events_found, events_new, error_msg,
                        counts, search_calls, llm_calls, llm_tokens_in, llm_tokens_out,
                        stopped_at_stage, error_detail,
                    )
                    elapsed = time.monotonic() - t0
                    _emit_metrics(trigger, error_msg, events_found, events_new, elapsed)
                    return run

            # --- Stage 3: plan queries ---
            with tracer.start_as_current_span("plan"):
                max_q = int(os.environ.get("MAX_QUERIES_PER_RUN", "6"))
                if trigger == "scheduled":
                    max_q = int(os.environ.get("MAX_QUERIES_SCHEDULED", "2"))
                # offset for scheduled: count of user's scheduled runs mod plan length
                offset = 0
                if trigger == "scheduled":
                    sched_count = db.query(orm.Run).filter(
                        orm.Run.user_id == user.id,
                        orm.Run.trigger == "scheduled",
                    ).count()
                    offset = sched_count

                planned = plan_queries(facets, window, max_queries=max_q, offset=offset)
                counts["queries_planned"] = len(planned)

                if not planned:
                    place = facets.get("place")
                    is_online = place.get("online", False) if place else False
                    if not is_online:
                        error_msg = "no place in criteria"
                        stopped_at_stage = "search"
                        _finalise_run(
                            run, db, events_found, events_new, error_msg,
                            counts, search_calls, llm_calls, llm_tokens_in, llm_tokens_out,
                            stopped_at_stage, error_detail,
                        )
                        elapsed = time.monotonic() - t0
                        _emit_metrics(trigger, error_msg, events_found, events_new, elapsed)
                        return run

            # --- Stage 4: search ---
            from ..adapters.search import SearchResult as SResult
            max_results_per_q = int(os.environ.get("MAX_RESULTS_PER_QUERY", "6"))
            all_results: list[SResult] = []

            with tracer.start_as_current_span("search"):
                search_errors = 0
                for pq in planned:
                    try:
                        results = provider.search(
                            pq.text,
                            country=pq.country,
                            language=pq.language,
                            max_results=max_results_per_q,
                        )
                        search_calls += 1
                        all_results.extend(results)
                    except Exception as exc:
                        search_errors += 1
                        search_calls += 1
                        if not error_detail:
                            error_detail = f"search: {type(exc).__name__}: {str(exc)[:200]}"
                        logger.warning("search error for query: %s", type(exc).__name__)

                counts["search_errors"] = search_errors
                counts["results_fetched"] = len(all_results)

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
            with tracer.start_as_current_span("extract"):
                place = facets.get("place") or {}
                target_city = place.get("city") or ""
                target_country = place.get("country") or ""
                language = facets.get("language")

                extracted, extract_counts = extract_events(
                    all_results,
                    window_start=window.start_utc,
                    window_end=window.end_utc,
                    target_city=target_city,
                    target_country=target_country,
                    language=language,
                    user_tz=user_tz,
                    model=model,
                    guardrail=guardrail,
                )
                # Count LLM calls from extraction: 1 for pass-1 (if results) + pages_content_pass for pass-2
                if all_results:
                    llm_calls += 1  # pass 1
                llm_calls += extract_counts.pages_content_pass  # pass 2 calls

                counts["pages_content_pass"] = extract_counts.pages_content_pass
                counts["extract_truncated"] = extract_counts.extract_truncated
                counts["events_extracted"] = extract_counts.events_extracted
                counts["extract_errors"] = extract_counts.extract_errors
                counts["guard_skipped"] = extract_counts.guard_skipped
                counts["guard_fallback"] = extract_counts.guard_fallback
                counts["guard_errors"] = extract_counts.guard_errors
                # Non-event count from extraction
                counts["filtered_non_event"] = extract_counts.filtered_non_event

            # --- Stage 6: filter ---
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
                counts["filtered_non_event"] = counts.get("filtered_non_event", 0) + filter_counts.filtered_non_event
                counts["filtered_duplicate"] = filter_counts.filtered_duplicate

            # --- Phase 1: insert kept events as `new`, commit (crash-recoverable) ---
            cap = int(os.environ.get("MAX_EVENTS_PER_RUN", "50"))
            to_judge = kept[:cap]
            events_new = len(to_judge)

            for ev in to_judge:
                db.add(orm.Event(
                    user_id=user.id,
                    title=ev.title,
                    date_time=ev.start_local,
                    place=f"{ev.venue or ''}, {ev.city or ''}, {ev.country or ''}".strip(", "),
                    link=ev.link,
                    description=ev.description,
                    start_tz=ev.start_tz,
                    end_time=ev.end_local,
                    source_url=ev.source_url,
                    page_kind=ev.page_kind,
                    city=ev.city or "",
                    country=ev.country or "ZZ",
                    price_amount=ev.price_amount,
                    price_currency=ev.price_currency,
                    source_query=None,
                    extraction_confidence=ev.confidence,
                    status="new",
                    run_id=run.id,
                ))
            db.commit()

            # --- Stage 7 + 8: judge and triage ---
            if events_new > 0:
                inserted = db.query(orm.Event).filter(
                    orm.Event.user_id == user.id,
                    orm.Event.status == "new",
                    orm.Event.run_id == run.id,
                ).all()

                llm_c, tok_in, tok_out, j_err = _judge_and_triage(
                    inserted, criteria_row, criteria_text, user_tz, user, model, db,
                )
                llm_calls += llm_c
                llm_tokens_in += tok_in
                llm_tokens_out += tok_out
                judge_errs = counts.get("judge_errors", 0) + j_err
                counts["judge_errors"] = judge_errs
                if j_err and not error_detail:
                    error_detail = f"judge: errors on {j_err} event(s)"
                db.commit()

            # Count triage outcomes
            if events_new > 0:
                triaged = db.query(orm.Event).filter(
                    orm.Event.run_id == run.id,
                ).all()
                counts["events_judged"] = sum(1 for e in triaged if e.score is not None)
                counts["accepted"] = sum(1 for e in triaged if e.status == "accepted")
                counts["rejected"] = sum(1 for e in triaged if e.status == "rejected")
                counts["queued"] = sum(1 for e in triaged if e.status == "queued")

            span.set_attribute("events_found", events_found)
            span.set_attribute("events_new", events_new)
            logger.info("search run completed")

        except Exception as exc:
            error_msg = str(exc)
            if not error_detail:
                error_detail = f"pipeline: {type(exc).__name__}: {str(exc)[:200]}"
            span.record_exception(exc)
            span.set_status(trace.StatusCode.ERROR, type(exc).__name__)
            logger.error("search run failed: %s", type(exc).__name__)
            db.rollback()

        # --- Stage 9: persist run ---
        _finalise_run(
            run, db, events_found, events_new, error_msg,
            counts, search_calls, llm_calls, llm_tokens_in, llm_tokens_out,
            stopped_at_stage, error_detail,
        )

        elapsed = time.monotonic() - t0
        _emit_metrics(trigger, error_msg, events_found, events_new, elapsed)
        return run


def _judge_and_triage(
    events: list[orm.Event],
    criteria_row: orm.Criteria | None,
    criteria_text: str,
    user_tz: str,
    user: orm.User,
    model,
    db: Session,
) -> tuple[int, int, int, int]:
    """Judge events and triage.  Returns (llm_calls, tokens_in, tokens_out, judge_errors)."""
    facets = json.loads(criteria_row.facets_json) if criteria_row and criteria_row.facets_json else {}
    date_facets = facets.get("date", {}) or {}

    # We need a window for the judge; re-resolve (safe since we already checked WindowInPast)
    try:
        window = resolve(date_facets, user_tz)
    except WindowInPast:
        # For recovery of old events, just use a wide window
        now_utc = clock.now()
        from ..services.window import Window
        from datetime import timedelta
        window = Window(start_utc=now_utc, end_utc=now_utc + timedelta(days=30), tz=user_tz)

    llm_calls = 0
    tokens_in = 0
    tokens_out = 0
    judge_errors = 0

    from ..services.extract import ExtractedEvent

    with tracer.start_as_current_span("judge"):
        for evt in events:
            # Build an ExtractedEvent from the ORM event for the judge
            extracted = ExtractedEvent(
                title=evt.title,
                start_local=evt.date_time,
                start_tz=evt.start_tz,
                end_local=evt.end_time,
                venue=None,
                city=evt.city,
                country=evt.country,
                link=evt.link,
                price_amount=evt.price_amount,
                price_currency=evt.price_currency,
                is_free=evt.price_amount == 0 if evt.price_amount is not None else None,
                description=evt.description,
                confidence=evt.extraction_confidence or 1.0,
                source_url=evt.source_url or evt.link,
                page_kind=evt.page_kind or "single_event",
            )

            result = judge_event(
                extracted,
                criteria_text=criteria_text,
                facets=facets,
                window_start=window.start_utc,
                window_end=window.end_utc,
                user_tz=user_tz,
                model=model,
            )
            llm_calls += 1

            if isinstance(result, JudgeError):
                judge_errors += 1
                # event stays `new`
                continue

            if isinstance(result, Verdict):
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
                evt.judge_version = "judge_v2"

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

    return llm_calls, tokens_in, tokens_out, judge_errors


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
) -> None:
    """Write final fields on the run row and commit."""
    run = db.merge(run)
    run.finished_at = datetime.now(UTC)
    run.events_found = events_found
    run.events_new = events_new
    run.error = error_msg
    run.stage_counts = json.dumps(counts) if counts else None
    run.search_calls = search_calls
    run.llm_calls = llm_calls
    run.llm_tokens_in = llm_tokens_in
    run.llm_tokens_out = llm_tokens_out
    run.stopped_at_stage = stopped_at_stage
    run.error_detail = error_detail
    db.commit()


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
