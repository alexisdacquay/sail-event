"""Hard filters before scoring — incomplete, past, window, place, non-event, dedup.

Applied in the order from spec §6 (with incomplete first per owner requirement).
Each filter counts its drops.
"""

from __future__ import annotations

import re
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

# Stopwords for title-key computation (en, de, fr, es, pt, it, nl)
_STOPWORDS = frozenset(
    "the a an of at in and or for to with by on is "
    "der die das im am und ein eine für zu mit von den dem des "
    "le la de du des les un une et en "
    "el los las y del en un una con por "
    "o a os as do da dos das em no na "
    "il lo la di da del dei delle in e un una "
    "het een de van in en op met".split()
)


@dataclass
class FilterCounts:
    filtered_incomplete: int = 0
    filtered_past: int = 0
    filtered_date: int = 0
    filtered_place: int = 0
    filtered_non_event: int = 0
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


# ---------- title key for near-match ----------

def title_key(title: str) -> frozenset[str]:
    """Lowercase, remove punctuation, split on whitespace, drop stopwords."""
    cleaned = re.sub(r"[^\w\s]", "", title.lower())
    tokens = cleaned.split()
    return frozenset(t for t in tokens if t not in _STOPWORDS)


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def is_near_match(key_a: frozenset[str], key_b: frozenset[str]) -> bool:
    """Jaccard >= 0.8, or subset only when the smaller has >= 3 tokens."""
    if jaccard(key_a, key_b) >= 0.8:
        return True
    smaller, larger = (key_a, key_b) if len(key_a) <= len(key_b) else (key_b, key_a)
    if len(smaller) >= 3 and smaller <= larger:
        return True
    return False


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

    stored_events: list of dicts with keys: link, date_time, title, status, page_kind.
    """
    counts = FilterCounts()
    stored = stored_events or []

    # Build stored lookup structures
    stored_links: set[tuple[str, str]] = set()  # (canonical_link, calendar_date)
    stored_title_date: list[tuple[frozenset[str], str, str]] = []  # (key, cal_date, status)
    for se in stored:
        link = se.get("link", "")
        dt = se.get("date_time", "")
        cal_date = dt[:10] if dt else ""
        stored_links.add((canonical_url(link), cal_date))
        stored_title_date.append((title_key(se.get("title", "")), cal_date, se.get("status", "")))

    # In-run dedup tracking
    run_links: set[tuple[str, str]] = set()
    run_title_date: list[tuple[frozenset[str], str]] = []

    kept: list[ExtractedEvent] = []

    for ev in events:
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

        # 2. Non-event: already handled in extract (confidence < 0.5 dropped there)
        if not ev.start_local:
            counts.filtered_non_event += 1
            continue

        # 5. Duplicate by link
        cal_date = _event_calendar_date(ev) or ""
        canon = canonical_url(ev.link)

        if (canon, cal_date) in stored_links:
            counts.filtered_duplicate += 1
            continue
        if (canon, cal_date) in run_links:
            counts.filtered_duplicate += 1
            continue

        # 6. Near-match by title+date
        ev_key = title_key(ev.title)
        is_dup = False

        for s_key, s_date, s_status in stored_title_date:
            if s_date == cal_date and is_near_match(ev_key, s_key):
                is_dup = True
                break

        if not is_dup:
            for r_key, r_date in run_title_date:
                if r_date == cal_date and is_near_match(ev_key, r_key):
                    is_dup = True
                    break

        if is_dup:
            counts.filtered_duplicate += 1
            continue

        # Event passes all filters
        run_links.add((canon, cal_date))
        run_title_date.append((ev_key, cal_date))
        kept.append(ev)

    return kept, counts
