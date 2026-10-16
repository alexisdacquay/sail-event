"""Events endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from ..deps import get_current_user
from ..models import DecisionRequest, EventStatus
from ..store import UserRecord

router = APIRouter()


@router.get("/api/events", operation_id="listEvents")
async def list_events(
    status: Optional[str] = None,
    user: UserRecord = Depends(get_current_user),
) -> list[dict]:
    events = list(user.events.values())
    if status is not None:
        events = [e for e in events if e.status.value == status]
    return [
        {
            "id": e.id,
            "title": e.title,
            "dateTime": e.date_time,
            "place": e.place,
            "link": e.link,
            "description": e.description,
            "score": e.score,
            "scoreReason": e.score_reason,
            "status": e.status.value,
        }
        for e in events
    ]


@router.post("/api/events/{id}/decision", operation_id="decideEvent")
async def decide_event(
    id: str,
    body: DecisionRequest,
    user: UserRecord = Depends(get_current_user),
) -> JSONResponse:
    event = user.events.get(id)
    if event is None:
        return JSONResponse(status_code=404, content={"detail": "Event not found"})

    if event.status == EventStatus.rejected:
        return JSONResponse(
            status_code=400,
            content={"detail": "Cannot change decision on a rejected event"},
        )

    # Apply decision
    new_status = EventStatus(body.decision)
    # accepted → accepted is a no-op 200
    event.status = new_status

    return JSONResponse(
        content={
            "id": event.id,
            "title": event.title,
            "dateTime": event.date_time,
            "place": event.place,
            "link": event.link,
            "description": event.description,
            "score": event.score,
            "scoreReason": event.score_reason,
            "status": event.status.value,
        },
    )
