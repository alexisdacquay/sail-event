"""Window resolution — turn Facets.date into a UTC time window."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from ..services import clock


@dataclass(frozen=True)
class Window:
    start_utc: datetime
    end_utc: datetime
    tz: str


def resolve(date_facets: dict, tz: str) -> Window:
    """Resolve date facets into a Window.

    Rules (§6):
    - Absolute dates win over relative.
    - Neither → now → +30 days.
    - Start clipped to now.
    """
    now_utc = clock.now()
    zone = ZoneInfo(tz)
    now_local = now_utc.astimezone(zone)

    abs_start = date_facets.get("start")
    abs_end = date_facets.get("end")
    relative = date_facets.get("relative")
    relative_n = date_facets.get("relative_n")

    start_local: datetime | None = None
    end_local: datetime | None = None

    # Absolute dates
    if abs_start:
        d = date.fromisoformat(abs_start)
        start_local = datetime.combine(d, time.min, tzinfo=zone)
    if abs_end:
        d = date.fromisoformat(abs_end)
        end_local = datetime.combine(d, time(23, 59, 59), tzinfo=zone)

    # Relative dates: only used when absolute dates are absent
    if start_local is None and end_local is None and relative:
        start_local, end_local = _resolve_relative(relative, relative_n, now_local, zone)

    # Default: now → +30 days
    if start_local is None and end_local is None:
        start_local = now_local
        end_local = now_local + timedelta(days=30)
        end_local = datetime.combine(end_local.date(), time(23, 59, 59), tzinfo=zone)

    # Fill in missing side
    if start_local is None:
        start_local = now_local
    if end_local is None:
        end_local = start_local + timedelta(days=30)
        end_local = datetime.combine(end_local.date(), time(23, 59, 59), tzinfo=zone)

    # Clip start to now
    if start_local < now_local:
        start_local = now_local

    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)

    return Window(start_utc=start_utc, end_utc=end_utc, tz=tz)


def _resolve_relative(
    relative: str,
    relative_n: int | None,
    now_local: datetime,
    zone: ZoneInfo,
) -> tuple[datetime, datetime]:
    today = now_local.date()

    if relative == "today":
        s = datetime.combine(today, time.min, tzinfo=zone)
        e = datetime.combine(today, time(23, 59, 59), tzinfo=zone)

    elif relative == "tomorrow":
        d = today + timedelta(days=1)
        s = datetime.combine(d, time.min, tzinfo=zone)
        e = datetime.combine(d, time(23, 59, 59), tzinfo=zone)

    elif relative == "this_week":
        # ISO week: Monday–Sunday
        mon = today - timedelta(days=today.weekday())
        sun = mon + timedelta(days=6)
        s = datetime.combine(mon, time.min, tzinfo=zone)
        e = datetime.combine(sun, time(23, 59, 59), tzinfo=zone)

    elif relative == "next_week":
        mon = today - timedelta(days=today.weekday()) + timedelta(weeks=1)
        sun = mon + timedelta(days=6)
        s = datetime.combine(mon, time.min, tzinfo=zone)
        e = datetime.combine(sun, time(23, 59, 59), tzinfo=zone)

    elif relative == "this_weekend":
        # Saturday–Sunday of the current ISO week
        # On a Sunday, "this weekend" is the rest of today
        sat = today - timedelta(days=today.weekday()) + timedelta(days=5)
        sun = sat + timedelta(days=1)
        s = datetime.combine(sat, time.min, tzinfo=zone)
        e = datetime.combine(sun, time(23, 59, 59), tzinfo=zone)

    elif relative == "next_weekend":
        sat = today - timedelta(days=today.weekday()) + timedelta(days=5 + 7)
        sun = sat + timedelta(days=1)
        s = datetime.combine(sat, time.min, tzinfo=zone)
        e = datetime.combine(sun, time(23, 59, 59), tzinfo=zone)

    elif relative == "this_month":
        first = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        last = today.replace(day=last_day)
        s = datetime.combine(first, time.min, tzinfo=zone)
        e = datetime.combine(last, time(23, 59, 59), tzinfo=zone)

    elif relative == "next_month":
        if today.month == 12:
            first = today.replace(year=today.year + 1, month=1, day=1)
        else:
            first = today.replace(month=today.month + 1, day=1)
        last_day = calendar.monthrange(first.year, first.month)[1]
        last = first.replace(day=last_day)
        s = datetime.combine(first, time.min, tzinfo=zone)
        e = datetime.combine(last, time(23, 59, 59), tzinfo=zone)

    elif relative == "next_n_days":
        n = relative_n or 30
        s = now_local
        end_date = (now_local + timedelta(days=n)).date()
        e = datetime.combine(end_date, time(23, 59, 59), tzinfo=zone)

    else:
        raise ValueError(f"Unknown relative expression: {relative!r}")

    return s, e
