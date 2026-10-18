"""Events endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import DecisionRequest, EventStatus
from ..services.judge import band_word
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
        "startTz": e.start_tz,
        "endTime": e.end_time,
        "city": e.city,
        "country": e.country,
        "priceAmount": e.price_amount,
        "priceCurrency": e.price_currency,
        "sourceUrl": e.source_url,
        "band": band_word(e.score) if e.score is not None else None,
        "score": e.score,
        "scoreReason": e.score_reason,
        "status": e.status,
        "decidedBy": e.decided_by,
    }


_VALID_STATUSES = {s.value for s in EventStatus}


@router.get("/api/events", operation_id="listEvents")
def list_events(
    status: Optional[str] = None,
    user: orm.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = db.query(orm.Event).filter(orm.Event.user_id == user.id)
    if status is not None:
        if status not in _VALID_STATUSES:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid status filter: {status}"},
            )
        query = query.filter(orm.Event.status == status)
    events = query.all()
    return [_event_dict(e) for e in events]


@router.post("/api/events/{id}/decision", operation_id="decideEvent")
def decide_event(
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
    event.decided_by = "user"
    db.commit()

    return JSONResponse(content=_event_dict(event))
