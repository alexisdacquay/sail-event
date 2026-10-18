"""Search endpoints — HTTP concerns only; business logic in services/pipeline.py."""

from __future__ import annotations

import json
import os

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from .. import orm
from ..services.pipeline import run_pipeline

router = APIRouter()


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
