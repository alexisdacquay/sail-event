"""Calendar feed endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from ..db import get_db
from .. import orm

router = APIRouter()

_VCALENDAR_EMPTY = (
    "BEGIN:VCALENDAR\r\n"
    "VERSION:2.0\r\n"
    "PRODID:-//sail-event//EN\r\n"
    "END:VCALENDAR\r\n"
)


@router.get("/api/calendar/{ics_token}", operation_id="getCalendarFeed")
async def get_calendar_feed(
    ics_token: str,
    db: Session = Depends(get_db),
) -> Response:
    user = db.query(orm.User).filter(orm.User.ics_token == ics_token).first()
    if user is None:
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    return Response(content=_VCALENDAR_EMPTY, media_type="text/calendar")
