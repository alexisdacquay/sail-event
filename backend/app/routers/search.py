"""Search endpoints — HTTP concerns only; business logic in services/pipeline.py."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from .. import orm
from ..services.pipeline import run_pipeline

router = APIRouter()


@router.post("/api/search", operation_id="runSearch")
def run_search(
    user: orm.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = run_pipeline(user, db, trigger="manual")
    if run.error:
        return JSONResponse(status_code=500, content={"detail": run.error})
    return {
        "runId": run.id,
        "eventsFound": run.events_found,
        "eventsNew": run.events_new,
    }


@router.post("/api/search/all", operation_id="searchAll")
def search_all(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> JSONResponse:
    expected = os.environ.get("SEARCH_ALL_API_KEY")
    if not expected or x_api_key != expected:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    users = (
        db.query(orm.User)
        .join(orm.Criteria, orm.User.id == orm.Criteria.user_id)
        .all()
    )
    count = 0
    for user in users:
        run = run_pipeline(user, db, trigger="scheduled")
        if not run.error:
            count += 1

    return JSONResponse(content={"usersProcessed": count})
