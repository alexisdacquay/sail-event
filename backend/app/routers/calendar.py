"""Calendar feed endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

from ..store import store

router = APIRouter()

_VCALENDAR_EMPTY = (
    "BEGIN:VCALENDAR\r\n"
    "VERSION:2.0\r\n"
    "PRODID:-//sail-event//EN\r\n"
    "END:VCALENDAR\r\n"
)


@router.get("/api/calendar/{ics_token}", operation_id="getCalendarFeed")
async def get_calendar_feed(ics_token: str) -> Response:
    user_id = store.ics_token_to_user.get(ics_token)
    if user_id is None:
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    return Response(content=_VCALENDAR_EMPTY, media_type="text/calendar")
