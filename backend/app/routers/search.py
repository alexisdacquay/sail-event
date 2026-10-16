"""Search endpoints and pipeline."""

from __future__ import annotations

import os
from uuid import uuid4

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from ..adapters import get_scorer, get_search_provider
from ..deps import get_current_user
from ..models import Event, EventStatus
from ..store import UserRecord, store

router = APIRouter()


def run_pipeline(user: UserRecord) -> dict:
    """Search -> dedup -> score -> triage. Returns SearchResult dict."""
    provider = get_search_provider()
    scorer = get_scorer()

    raw_events = provider.search([user.criteria.text])
    events_found = len(raw_events)

    # Dedup by link against events already in the store for this user
    new_raws = []
    for raw in raw_events:
        if raw.link not in user.events_by_link:
            new_raws.append(raw)

    events_new = len(new_raws)

    # Score and triage new events
    lower = user.thresholds.lower_threshold
    upper = user.thresholds.upper_threshold
    run_id = store.next_run_id()

    for raw in new_raws:
        score_val, reason = scorer.score(raw, user.criteria.text)

        if score_val > upper:
            status = EventStatus.accepted
        elif score_val < lower:
            status = EventStatus.rejected
        else:
            status = EventStatus.queued

        event = Event(
            id=str(uuid4()),
            title=raw.title,
            date_time=raw.date_time,
            place=raw.place,
            link=raw.link,
            description=raw.description,
            score=score_val,
            score_reason=reason,
            status=status,
        )
        store.add_event(user.user_id, event)

    return {
        "runId": run_id,
        "eventsFound": events_found,
        "eventsNew": events_new,
    }


@router.post("/api/search", operation_id="runSearch")
async def run_search(
    user: UserRecord = Depends(get_current_user),
) -> dict:
    return run_pipeline(user)


@router.post("/api/search/all", operation_id="searchAll")
async def search_all(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> JSONResponse:
    expected = os.environ.get("SEARCH_ALL_API_KEY")
    if not expected or x_api_key != expected:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    count = 0
    for user in store.users.values():
        run_pipeline(user)
        count += 1

    return JSONResponse(content={"usersProcessed": count})
