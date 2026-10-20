"""Calendar feed and calendar-URL endpoints."""

from __future__ import annotations

import logging
from datetime import date as date_type, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from icalendar import Calendar, Event as IcsEvent
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..services.filters import attach_offset
from .. import orm

logger = logging.getLogger(__name__)

router = APIRouter()

_EVENT_DURATION = timedelta(hours=2)


def _build_calendar(user: orm.User, events: list[orm.Event]) -> bytes:
    cal = Calendar()
    cal.add("version", "2.0")
    cal.add("prodid", "-//sail-event//EN")
    cal.add("x-wr-calname", f"Sail-event — {user.username}")

    for evt in events:
        dt_str = attach_offset(evt.date_time, evt.start_tz,
                               evt.country if getattr(evt, "country", "ZZ") != "ZZ" else None)

        # Date-only events: VALUE=DATE
        if len(dt_str) == 10 and "T" not in dt_str:
            try:
                d = date_type.fromisoformat(dt_str)
            except ValueError:
                logger.warning("Skipping event %s: unparseable date_time %r", evt.id, evt.date_time)
                continue
            ve = IcsEvent()
            ve.add("uid", f"{evt.id}@sail-event")
            ve.add("summary", evt.title)
            ve.add("dtstart", d)
            ve.add("dtend", d + timedelta(days=1))
            ve.add("location", evt.place)
            ve.add("url", evt.link)
            desc = evt.description
            if evt.score_reason:
                desc = desc + "\n" + evt.score_reason
            ve.add("description", desc)
            ve.add("dtstamp", evt.created_at)
            cal.add_component(ve)
            continue

        # Timed events
        try:
            dtstart = datetime.fromisoformat(dt_str)
        except (ValueError, TypeError):
            logger.warning("Skipping event %s: unparseable date_time %r", evt.id, evt.date_time)
            continue

        ve = IcsEvent()
        ve.add("uid", f"{evt.id}@sail-event")
        ve.add("summary", evt.title)

        if evt.start_tz:
            # DTSTART with TZID: convert to local time in the event zone
            tz = ZoneInfo(evt.start_tz)
            local_dt = dtstart.astimezone(tz) if dtstart.tzinfo else dtstart.replace(tzinfo=tz)
            naive_local = local_dt.replace(tzinfo=None)
            ve.add("dtstart", naive_local, parameters={"TZID": evt.start_tz})
            ve.add("dtend", naive_local + _EVENT_DURATION, parameters={"TZID": evt.start_tz})
        else:
            # No zone: floating local time (unchanged for legacy)
            ve.add("dtstart", dtstart)
            ve.add("dtend", dtstart + _EVENT_DURATION)

        ve.add("location", evt.place)
        ve.add("url", evt.link)

        desc = evt.description
        if evt.score_reason:
            desc = desc + "\n" + evt.score_reason
        ve.add("description", desc)

        ve.add("dtstamp", evt.created_at)

        cal.add_component(ve)

    return cal.to_ical()


@router.get("/api/calendar/{ics_token}", operation_id="getCalendarFeed")
def get_calendar_feed(
    ics_token: str,
    db: Session = Depends(get_db),
) -> Response:
    user = db.query(orm.User).filter(orm.User.ics_token == ics_token).first()
    if user is None:
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    accepted = (
        db.query(orm.Event)
        .filter(orm.Event.user_id == user.id, orm.Event.status == "accepted")
        .all()
    )

    body = _build_calendar(user, accepted)
    return Response(content=body, media_type="text/calendar; charset=utf-8")


def _build_feed_url(request: Request, user: orm.User) -> str:
    base = str(request.base_url).rstrip("/")
    return f"{base}/api/calendar/{user.ics_token}"


@router.get("/api/calendar-url", operation_id="getCalendarUrl")
def get_calendar_url(
    request: Request,
    user: orm.User = Depends(get_current_user),
) -> JSONResponse:
    return JSONResponse(content={"url": _build_feed_url(request, user)})


@router.post("/api/calendar/rotate", operation_id="rotateCalendarUrl")
def rotate_calendar_url(
    request: Request,
    user: orm.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    user.ics_token = orm._uuid()
    db.commit()
    db.refresh(user)
    return JSONResponse(content={"url": _build_feed_url(request, user)})
