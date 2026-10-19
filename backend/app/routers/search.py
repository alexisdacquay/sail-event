"""Search endpoints — HTTP concerns only; business logic in services/pipeline.py."""

from __future__ import annotations

import json
import math
import os
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from .. import orm
from ..services.pipeline import run_pipeline

router = APIRouter()

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


@router.post("/api/search/all", operation_id="searchAll")
def search_all(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> JSONResponse:
    expected = os.environ.get("SEARCH_ALL_API_KEY")
    if not expected or x_api_key != expected:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    max_users = int(os.environ.get("MAX_SCHEDULED_USERS", "50"))
    users = (
        db.query(orm.User)
        .join(orm.Criteria, orm.User.id == orm.Criteria.user_id)
        .order_by(orm.Criteria.updated_at.desc())
        .all()
    )
    attempted = users[:max_users]
    count = 0
    for user in attempted:
        run = run_pipeline(user, db, trigger="scheduled")
        if not run.error:
            count += 1

    skipped = len(users) - len(attempted)
    return JSONResponse(content={"usersProcessed": count, "usersSkipped": skipped})
