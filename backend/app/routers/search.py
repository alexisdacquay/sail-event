"""Search endpoints — HTTP concerns only; business logic in services/pipeline.py."""

from __future__ import annotations

import json
import logging
import math
import os
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from .. import orm
from ..services.pipeline import run_pipeline

logger = logging.getLogger("sail-event.search")

router = APIRouter()

# §8: 55-minute overlap guard
_OVERLAP_MINUTES = 55
_SEARCH_NOW_WINDOW = 3600  # 1 hour in seconds


def _run_response(run: orm.Run) -> dict:
    """Build the SearchResult response dict from a Run row."""
    stage_counts = json.loads(run.stage_counts) if run.stage_counts else None
    return {
        "runId": run.id,
        "eventsFound": run.events_found,
        "eventsNew": run.events_new,
        "stageCounts": stage_counts,
        "stoppedAtStage": run.stopped_at_stage,
        "error": run.error,
    }


@router.post("/api/search", operation_id="runSearch")
def run_search(
    user: orm.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Rate limit: SEARCH_NOW_PER_HOUR manual runs per user per rolling hour
    # Run timestamps use real UTC (datetime.now(UTC)), not FAKE_NOW
    limit = int(os.environ.get("SEARCH_NOW_PER_HOUR", "6"))
    now = datetime.now(UTC)
    cutoff = now - timedelta(seconds=_SEARCH_NOW_WINDOW)

    recent_runs = (
        db.query(orm.Run)
        .filter(
            orm.Run.user_id == user.id,
            orm.Run.trigger == "manual",
            orm.Run.started_at >= cutoff,
        )
        .order_by(orm.Run.started_at.asc())
        .all()
    )

    if len(recent_runs) >= limit:
        oldest = recent_runs[0].started_at
        # SQLite may strip timezone; ensure aware for subtraction
        if oldest.tzinfo is None:
            oldest = oldest.replace(tzinfo=UTC)
        retry_after = math.ceil(
            _SEARCH_NOW_WINDOW - (now - oldest).total_seconds()
        )
        retry_after = max(retry_after, 1)
        return JSONResponse(
            status_code=429,
            content={"detail": "Search limit reached, try again later."},
            headers={"Retry-After": str(retry_after)},
        )

    run = run_pipeline(user, db, trigger="manual")
    return _run_response(run)


def _select_users(db: Session, max_users: int) -> tuple[list[orm.User], int]:
    """Select users for the hourly job: skip still-running, order oldest last run.

    Returns (users_to_queue, users_skipped_count).
    """
    cutoff = datetime.now(UTC) - timedelta(minutes=_OVERLAP_MINUTES)

    # All users with criteria
    all_users = (
        db.query(orm.User)
        .join(orm.Criteria, orm.User.id == orm.Criteria.user_id)
        .all()
    )

    # Users with an unfinished run started < 55 min ago
    still_running_ids: set[str] = set()
    for u in all_users:
        unfinished = (
            db.query(orm.Run)
            .filter(
                orm.Run.user_id == u.id,
                orm.Run.started_at >= cutoff,
                orm.Run.finished_at.is_(None),
            )
            .first()
        )
        if unfinished:
            still_running_ids.add(u.id)

    eligible = [u for u in all_users if u.id not in still_running_ids]
    skipped_running = len(still_running_ids)

    # Order by oldest last run (never-run first)
    _epoch = datetime(1970, 1, 1, tzinfo=UTC)

    def _last_run_key(u: orm.User) -> datetime:
        last = (
            db.query(func.max(orm.Run.started_at))
            .filter(orm.Run.user_id == u.id)
            .scalar()
        )
        if last is None:
            return _epoch
        # SQLite returns naive datetimes; treat as UTC
        if last.tzinfo is None:
            return last.replace(tzinfo=UTC)
        return last

    eligible.sort(key=_last_run_key)

    queued = eligible[:max_users]
    skipped_cap = len(eligible) - len(queued)

    return queued, skipped_running + skipped_cap


# Patchable session factory for background tasks (tests swap this)
_session_factory = None


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        from ..db import SessionLocal
        _session_factory = SessionLocal
    return _session_factory


def _finalise_orphan_run(run_id: str, error: str) -> None:
    """Best-effort finalise an enqueue-time Run row that never reached run_pipeline."""
    try:
        factory = _get_session_factory()
        db2 = factory()
        try:
            row = db2.query(orm.Run).filter(orm.Run.id == run_id).first()
            if row and row.finished_at is None:
                row.finished_at = datetime.now(UTC)
                row.error = error
                row.stopped_at_stage = "enqueue"
                db2.commit()
        finally:
            db2.close()
    except Exception:
        logger.warning("could not finalise orphan run %s", run_id)


def _run_scheduled_user(user_id: str, run_id: str) -> None:
    """Background task: run the pipeline for one user with a fresh DB session."""
    factory = _get_session_factory()
    db = factory()
    try:
        user = db.query(orm.User).filter(orm.User.id == user_id).first()
        if user:
            run_pipeline(user, db, trigger="scheduled", run_id=run_id)
        else:
            _finalise_orphan_run(run_id, "user not found")
    except Exception as exc:
        logger.exception("scheduled run failed for user %s", user_id)
        _finalise_orphan_run(run_id, f"{type(exc).__name__}: {str(exc)[:200]}")
    finally:
        db.close()


@router.post("/api/search/all", operation_id="searchAll")
def search_all(
    background_tasks: BackgroundTasks,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> JSONResponse:
    expected = os.environ.get("SEARCH_ALL_API_KEY")
    if not expected or x_api_key != expected:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    max_users = int(os.environ.get("MAX_SCHEDULED_USERS", "50"))
    queued, skipped = _select_users(db, max_users)

    # #73: write Run rows at enqueue time so the 55-min skip sees queued users
    now = datetime.now(UTC)
    for user in queued:
        run = orm.Run(user_id=user.id, started_at=now, trigger="scheduled")
        db.add(run)
        db.flush()
        background_tasks.add_task(_run_scheduled_user, user.id, run.id)
    db.commit()

    return JSONResponse(
        status_code=202,
        content={"usersQueued": len(queued), "usersSkipped": skipped},
    )
