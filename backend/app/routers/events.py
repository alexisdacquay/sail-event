"""Events endpoints."""

from __future__ import annotations

import hashlib
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import DecisionRequest, EventStatus
from ..services import clock
from ..services.filters import attach_offset, is_event_past
from ..services.judge import band_word
from .. import orm

router = APIRouter()


def _event_dict(e: orm.Event, current_criteria_hash: str | None = None) -> dict:
    # On-read fallback: attach offset to naive datetimes from pre-#71 rows
    dt = attach_offset(e.date_time, e.start_tz, e.country if e.country != "ZZ" else None)
    et = attach_offset(e.end_time, e.start_tz, e.country if e.country != "ZZ" else None) if e.end_time else None
    stale = (
        e.criteria_hash is not None
        and current_criteria_hash is not None
        and e.criteria_hash != current_criteria_hash
    )
    return {
        "id": e.id,
        "title": e.title,
        "dateTime": dt,
        "place": e.place,
        "link": e.link,
        "description": e.description,
        "startTz": e.start_tz,
        "endTime": et,
        "city": e.city,
        "country": e.country,
        "sourceUrl": e.source_url,
        "band": band_word(e.score) if e.score is not None else None,
        "score": e.score,
        "scoreReason": e.score_reason,
        "status": e.status,
        "decidedBy": e.decided_by,
        "criteriaStale": stale,
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
    user_tz = user.time_zone or "UTC"
    now_utc = clock.now()
    criteria_row = db.query(orm.Criteria).filter(orm.Criteria.user_id == user.id).first()
    crit_hash = hashlib.sha256(criteria_row.text.encode()).hexdigest()[:16] if criteria_row and criteria_row.text else None
    return [
        _event_dict(e, crit_hash) for e in events
        if not is_event_past(e.date_time, e.start_tz,
                             e.country if e.country != "ZZ" else None,
                             user_tz, now_utc)
    ]


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
