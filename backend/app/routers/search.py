"""Search endpoints and pipeline."""

from __future__ import annotations

import os
from uuid import uuid4

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..adapters import get_scorer, get_search_provider
from ..db import get_db
from ..deps import get_current_user
from .. import orm

router = APIRouter()


def run_pipeline(user: orm.User, db: Session) -> dict:
    """Search -> dedup -> score -> triage. Returns SearchResult dict."""
    provider = get_search_provider()
    scorer = get_scorer()

    criteria_row = db.query(orm.Criteria).filter(orm.Criteria.user_id == user.id).first()
    criteria_text = criteria_row.text if criteria_row else ""

    raw_events = provider.search([criteria_text])
    events_found = len(raw_events)

    # Dedup: pre-select existing links for this user, then dedup within batch
    existing_links: set[str] = {
        link for (link,) in db.query(orm.Event.link).filter(orm.Event.user_id == user.id).all()
    }
    seen: set[str] = set(existing_links)
    new_raws = []
    for raw in raw_events:
        if raw.link not in seen:
            seen.add(raw.link)
            new_raws.append(raw)
    events_new = len(new_raws)

    # Score and triage new events
    lower = user.lower_threshold
    upper = user.upper_threshold
    run_id = str(uuid4())

    for raw in new_raws:
        score_val, reason = scorer.score(raw, criteria_text)

        if score_val > upper:
            status = "accepted"
        elif score_val < lower:
            status = "rejected"
        else:
            status = "queued"

        event = orm.Event(
            user_id=user.id,
            title=raw.title,
            date_time=raw.date_time,
            place=raw.place,
            link=raw.link,
            description=raw.description,
            score=score_val,
            score_reason=reason,
            status=status,
        )
        db.add(event)

    db.commit()

    return {
        "runId": run_id,
        "eventsFound": events_found,
        "eventsNew": events_new,
    }


@router.post("/api/search", operation_id="runSearch")
async def run_search(
    user: orm.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return run_pipeline(user, db)


@router.post("/api/search/all", operation_id="searchAll")
async def search_all(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> JSONResponse:
    expected = os.environ.get("SEARCH_ALL_API_KEY")
    if not expected or x_api_key != expected:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    # Users that have a Criteria row
    users = (
        db.query(orm.User)
        .join(orm.Criteria, orm.User.id == orm.Criteria.user_id)
        .all()
    )
    count = 0
    for user in users:
        run_pipeline(user, db)
        count += 1

    return JSONResponse(content={"usersProcessed": count})
