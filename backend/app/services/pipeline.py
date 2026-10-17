"""Search-run pipeline: derive queries, search, dedup, score, triage, record."""

from __future__ import annotations

import logging
import os
import re
import time
from datetime import UTC, datetime

from opentelemetry import trace, metrics
from sqlalchemy.orm import Session

from ..adapters import get_scorer, get_search_provider
from ..adapters.base import RawEvent
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


def derive_queries(criteria_text: str) -> list[str]:
    """Return full text as first query plus up to 5 comma/newline fragments."""
    queries = [criteria_text]
    fragments = [f.strip() for f in re.split(r"[,\n]", criteria_text) if f.strip()]
    if len(fragments) > 1:
        queries.extend(fragments[:5])
    return queries


def run_pipeline(user: orm.User, db: Session, *, trigger: str) -> orm.Run:
    """Execute one search run for a user. Always returns a Run row."""
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

        events_found = 0
        events_new = 0
        error_msg: str | None = None

        try:
            criteria_row = db.query(orm.Criteria).filter(
                orm.Criteria.user_id == user.id,
            ).first()
            criteria_text = criteria_row.text if criteria_row else ""
            scorer = get_scorer()

            # Recovery: score leftover `new` events from prior crashed runs
            leftover = db.query(orm.Event).filter(
                orm.Event.user_id == user.id,
                orm.Event.status == "new",
            ).all()
            if leftover:
                _score_and_triage(leftover, criteria_text, scorer, user)
                db.commit()

            # Search
            with tracer.start_as_current_span("search"):
                provider = get_search_provider()
                queries = derive_queries(criteria_text)
                raw_events = provider.search(queries)
                events_found = len(raw_events)

            # Dedup
            with tracer.start_as_current_span("dedup"):
                existing_links: set[str] = {
                    link
                    for (link,) in db.query(orm.Event.link)
                    .filter(orm.Event.user_id == user.id)
                    .all()
                }
                seen: set[str] = set(existing_links)
                new_raws: list[RawEvent] = []
                for raw in raw_events:
                    if raw.link not in seen:
                        seen.add(raw.link)
                        new_raws.append(raw)

                # Cap
                cap = int(os.environ.get("MAX_EVENTS_PER_RUN", "50"))
                new_raws = new_raws[:cap]
                events_new = len(new_raws)

            # Phase 1: insert as `new`, commit (crash-recoverable)
            for raw in new_raws:
                db.add(orm.Event(
                    user_id=user.id,
                    title=raw.title,
                    date_time=raw.date_time,
                    place=raw.place,
                    link=raw.link,
                    description=raw.description,
                    status="new",
                    run_id=run.id,
                ))
            db.commit()

            # Phase 2: score and triage the just-inserted events
            if events_new > 0:
                inserted = db.query(orm.Event).filter(
                    orm.Event.user_id == user.id,
                    orm.Event.status == "new",
                    orm.Event.run_id == run.id,
                ).all()
                _score_and_triage(inserted, criteria_text, scorer, user)
                db.commit()

            span.set_attribute("events_found", events_found)
            span.set_attribute("events_new", events_new)
            logger.info("search run completed")

        except Exception as exc:
            error_msg = str(exc)
            span.record_exception(exc)
            span.set_status(trace.StatusCode.ERROR, type(exc).__name__)
            logger.error("search run failed: %s", type(exc).__name__)
            db.rollback()

        # Finalize: always write finished_at and counts
        run = db.merge(run)
        run.finished_at = datetime.now(UTC)
        run.events_found = events_found
        run.events_new = events_new
        run.error = error_msg
        db.commit()

        elapsed = time.monotonic() - t0
        outcome = "error" if error_msg else "ok"
        _runs_counter.add(1, {"trigger": trigger, "outcome": outcome})
        _events_found_counter.add(events_found)
        _events_new_counter.add(events_new)
        _run_duration.record(elapsed)

        return run


def _score_and_triage(
    events: list[orm.Event],
    criteria_text: str,
    scorer: object,
    user: orm.User,
) -> None:
    """Score events and set status based on user thresholds. Does not commit."""
    with tracer.start_as_current_span("score"):
        for evt in events:
            raw = RawEvent(
                title=evt.title,
                date_time=evt.date_time,
                place=evt.place,
                link=evt.link,
                description=evt.description,
            )
            score_val, reason = scorer.score(raw, criteria_text)
            evt.score = score_val
            evt.score_reason = reason
            model_id = getattr(scorer, "model_id", None)
            evt.scorer_model = model_id if isinstance(model_id, str) else None

    with tracer.start_as_current_span("triage"):
        for evt in events:
            if evt.score > user.upper_threshold:
                evt.status = "accepted"
            elif evt.score < user.lower_threshold:
                evt.status = "rejected"
            else:
                evt.status = "queued"
