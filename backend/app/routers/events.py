"""Events endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import DecisionRequest, EventStatus
from .. import orm

router = APIRouter()


def _event_dict(e: orm.Event) -> dict:
    return {
        "id": e.id,
        "title": e.title,
        "dateTime": e.date_time,
        "place": e.place,
        "link": e.link,
        "description": e.description,
        "score": e.score,
        "scoreReason": e.score_reason,
        "status": e.status,
    }


@router.get("/api/events", operation_id="listEvents")
async def list_events(
    status: Optional[str] = None,
    user: orm.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = db.query(orm.Event).filter(orm.Event.user_id == user.id)
    if status is not None:
        query = query.filter(orm.Event.status == status)
    events = query.all()
    return [_event_dict(e) for e in events]


@router.post("/api/events/{id}/decision", operation_id="decideEvent")
async def decide_event(
    id: str,
    body: DecisionRequest,
    user: orm.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    event = db.query(orm.Event).filter(
        orm.Event.id == id,
        orm.Event.user_id == user.id,
    ).first()
    if event is None:
        return JSONResponse(status_code=404, content={"detail": "Event not found"})

    if event.status not in (EventStatus.queued.value, EventStatus.accepted.value):
        return JSONResponse(
            status_code=400,
            content={"detail": "Only queued and accepted events can be decided"},
        )

    event.status = body.decision
    db.commit()

    return JSONResponse(content=_event_dict(event))
