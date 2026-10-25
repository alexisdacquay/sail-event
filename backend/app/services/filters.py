"""Hard filters before scoring — incomplete, past, and one duplicate check (#136).

Applied in the order from spec §6 (with incomplete first per owner requirement).
Each filter counts its drops.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from ..adapters.search import canonical_url
from ..services.extract import ExtractedEvent

# Country → single IANA zone; multi-zone countries (US, AU, BR, RU, CA) → None
_SINGLE_ZONE: dict[str, str] = {
    "DE": "Europe/Berlin", "AT": "Europe/Vienna", "FR": "Europe/Paris",
    "GB": "Europe/London", "PT": "Europe/Lisbon", "NL": "Europe/Amsterdam",
    "JP": "Asia/Tokyo", "CH": "Europe/Zurich", "IT": "Europe/Rome",
    "ES": "Europe/Madrid", "BE": "Europe/Brussels", "DK": "Europe/Copenhagen",
    "SE": "Europe/Stockholm", "NO": "Europe/Oslo", "FI": "Europe/Helsinki",
    "PL": "Europe/Warsaw", "CZ": "Europe/Prague", "IE": "Europe/Dublin",
    "GR": "Europe/Athens", "HU": "Europe/Budapest",
}

@dataclass
class FilterCounts:
    filtered_incomplete: int = 0
    filtered_past: int = 0
    filtered_date: int = 0
    filtered_place: int = 0
    filtered_no_date: int = 0
    filtered_no_time: int = 0
    filtered_duplicate: int = 0


def _is_complete(ev: ExtractedEvent) -> bool:
    """Check that all required fields are present and non-empty."""
    return bool(
        ev.title
        and ev.start_local
        and ev.start_tz
        and ev.city
        and ev.country
        and ev.description
    )


def _parse_event_dt(dt_str: str, tz_str: str | None, country: str | None, user_tz: str) -> datetime | None:
    """Parse an event date-time string into a tz-aware datetime."""
    if not dt_str:
        return None
    if len(dt_str) == 10 and "T" not in dt_str:
        d = date.fromisoformat(dt_str)
        zone = _resolve_zone(tz_str, country, user_tz)
        return datetime.combine(d, time.min, tzinfo=zone)
    try:
        dt = datetime.fromisoformat(dt_str)
    except ValueError:
        return None
    if dt.tzinfo is None:
        zone = _resolve_zone(tz_str, country, user_tz)
        dt = dt.replace(tzinfo=zone)
    return dt


def _resolve_zone(tz_str: str | None, country: str | None, user_tz: str) -> ZoneInfo:
    """Resolve zone: explicit > country single-zone > user_tz."""
    if tz_str:
        try:
            return ZoneInfo(tz_str)
        except (KeyError, ValueError):
            pass
    if country and country in _SINGLE_ZONE:
        return ZoneInfo(_SINGLE_ZONE[country])
    return ZoneInfo(user_tz)


def _is_date_only(dt_str: str) -> bool:
    return len(dt_str) == 10 and "T" not in dt_str


def resolve_iana_zone(start_tz: str | None, country: str | None) -> str | None:
    """Return the IANA zone name when one can be resolved, else None.

    Resolution order: explicit start_tz > country single-zone table.
    Returns None (not UTC) when neither source yields a zone.
    """
    if start_tz:
        try:
            ZoneInfo(start_tz)  # validate
            return start_tz
        except (KeyError, ValueError):
            pass
    if country and country in _SINGLE_ZONE:
        return _SINGLE_ZONE[country]
    return None


def attach_offset(dt_str: str, start_tz: str | None, country: str | None) -> str:
    """Attach UTC offset to a naive local datetime when the zone is known.

    Date-only strings and strings that already carry an offset pass through unchanged.
    When no zone can be resolved (start_tz invalid/None AND country not single-zone),
    the string is returned naive — never stamped as UTC.
    Preserves the original local-time string to avoid format changes (e.g. 'T21:00' stays,
    never becomes 'T21:00:00').
    """
    if not dt_str or _is_date_only(dt_str):
        return dt_str
    # Already has offset (+HH:MM, -HH:MM) or Z
    if "+" in dt_str[10:] or dt_str.endswith("Z") or dt_str[10:].count("-") > 0:
        return dt_str
    try:
        naive = datetime.fromisoformat(dt_str)
    except ValueError:
        return dt_str
    if naive.tzinfo is not None:
        return dt_str
    iana = resolve_iana_zone(start_tz, country)
    if iana is None:
        return dt_str  # no zone resolvable — leave naive
    zone = ZoneInfo(iana)
    # Compute the offset string and append to the original local-time string
    offset = zone.utcoffset(naive)
    total_seconds = int(offset.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    hh, mm = divmod(abs(total_seconds), 3600)
    mm //= 60
    return f"{dt_str}{sign}{hh:02d}:{mm:02d}"


def _event_end_utc(ev: ExtractedEvent, user_tz: str) -> datetime | None:
    """Compute the event's effective end in UTC.

    end_local if known, else start for timed events, else 23:59:59 of start day
    for date-only events.
    """
    if ev.end_local:
        dt = _parse_event_dt(ev.end_local, ev.start_tz, ev.country, user_tz)
        if dt:
            if _is_date_only(ev.end_local):
                return dt.replace(hour=23, minute=59, second=59).astimezone(timezone.utc)
            return dt.astimezone(timezone.utc)
    start = _parse_event_dt(ev.start_local, ev.start_tz, ev.country, user_tz)
    if not start:
        return None
    if _is_date_only(ev.start_local):
        return start.replace(hour=23, minute=59, second=59).astimezone(timezone.utc)
    else:
        return start.astimezone(timezone.utc)


def _event_start_utc(ev: ExtractedEvent, user_tz: str) -> datetime | None:
    dt = _parse_event_dt(ev.start_local, ev.start_tz, ev.country, user_tz)
    if dt:
        return dt.astimezone(timezone.utc)
    return None


def _event_calendar_date(ev: ExtractedEvent) -> str | None:
    """Extract the calendar date (YYYY-MM-DD) from start_local."""
    if not ev.start_local:
        return None
    return ev.start_local[:10]


# ---------- main filter pipeline ----------

def filter_events(
    events: list[ExtractedEvent],
    *,
    now_utc: datetime,
    window_start_utc: datetime,
    window_end_utc: datetime,
    target_city: str | None,
    target_country: str | None,
    user_tz: str,
    stored_events: list[dict] | None = None,
) -> tuple[list[ExtractedEvent], FilterCounts]:
    """Apply all hard filters in order. Returns (kept, counts).

    stored_events: list of dicts with keys link and date_time (others are ignored).
    """
    counts = FilterCounts()
    stored = stored_events or []
    # #136: the one duplicate check, an event page already stored for the same calendar date
    stored_pages = {(canonical_url(se.get("link", "")), (se.get("date_time") or "")[:10]) for se in stored}
    # The events table is unique on (user, link, date_time): a second row with that key cannot be stored
    stored_keys = {(se.get("link", ""), se.get("date_time") or "") for se in stored}
    run_keys: set[tuple[str, str]] = set()

    kept: list[ExtractedEvent] = []

    for ev in events:
        # #112: no start date gets its own counter, before the generic incomplete check
        if not ev.start_local:
            counts.filtered_no_date += 1
            continue

        # #134: date present but no time component → filtered_no_time
        if _is_date_only(ev.start_local):
            counts.filtered_no_time += 1
            continue

        # 0. Incomplete: required fields missing
        if not _is_complete(ev):
            counts.filtered_incomplete += 1
            continue

        # 1. Past filter
        end_utc = _event_end_utc(ev, user_tz)
        if end_utc and end_utc < now_utc:
            counts.filtered_past += 1
            continue

        # Place and date-window filtering removed — the judge decides.

        # 5. Duplicate: the event's own page (never a listing's URL) stored for the same day
        own_page = ev.page_kind != "listing" or canonical_url(ev.link) != canonical_url(ev.source_url)
        key = (ev.link, attach_offset(ev.start_local, ev.start_tz, ev.country))
        if (own_page and (canonical_url(ev.link), _event_calendar_date(ev)) in stored_pages) \
                or key in stored_keys or key in run_keys:
            counts.filtered_duplicate += 1
            continue

        run_keys.add(key)
        kept.append(ev)

    return kept, counts
