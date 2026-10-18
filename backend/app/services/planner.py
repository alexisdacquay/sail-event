"""Query planner — build search queries from facets and window (design S5).

Pure function: ``plan(facets, window, *, max_queries, offset) -> list[PlannedQuery]``.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class PlannedQuery:
    text: str
    country: str | None
    language: str | None
    priority: int


# ---------- localisation tables ----------

_EVENTS_WORD: dict[str, str] = {
    "de": "Veranstaltungen",
    "fr": "événements",
    "es": "eventos",
    "pt": "eventos",
    "it": "eventi",
    "nl": "evenementen",
    "ja": "イベント",
    "ko": "이벤트",
    "zh": "活动",
    "ru": "события",
    "pl": "wydarzenia",
    "sv": "evenemang",
}

# Month names per supported language (1-indexed).
_MONTHS: dict[str, list[str]] = {
    "de": ["", "Januar", "Februar", "März", "April", "Mai", "Juni",
           "Juli", "August", "September", "Oktober", "November", "Dezember"],
    "fr": ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
           "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"],
    "es": ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
           "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
    "pt": ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
           "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"],
    "it": ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
           "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"],
    "nl": ["", "Januari", "Februari", "Maart", "April", "Mei", "Juni",
           "Juli", "Augustus", "September", "Oktober", "November", "December"],
}

# City name in the place's language (only entries that differ from English).
_CITY_LOCAL: dict[str, dict[str, str]] = {
    "pt": {"Lisbon": "Lisboa"},
    "de": {"Munich": "München", "Vienna": "Wien", "Cologne": "Köln"},
    "fr": {"London": "Londres", "Munich": "Munich"},
    "it": {"Milan": "Milano", "Rome": "Roma", "Florence": "Firenze"},
    "nl": {"The Hague": "Den Haag"},
    "ja": {"Tokyo": "東京"},
}


# ---------- helpers ----------


def _month_en(month: int) -> str:
    return calendar.month_name[month]


def _month_local(lang: str, month: int) -> str:
    table = _MONTHS.get(lang)
    if table:
        return table[month]
    return _month_en(month)


def _city_local(lang: str, city: str) -> str:
    return _CITY_LOCAL.get(lang, {}).get(city, city)


def _day_phrase_en(start_date: datetime, end_date: datetime, month: int, year: int) -> str:
    """Short day range: ``19–21 October 2026`` for <=7 days, else ``October 2026``."""
    span = (end_date.date() - start_date.date()).days
    if span <= 7:
        sd, ed = start_date.day, end_date.day
        if sd == ed:
            return f"{sd} {_month_en(month)} {year}"
        return f"{sd}–{ed} {_month_en(month)} {year}"
    return f"{_month_en(month)} {year}"


_LOWERCASE_MONTH_LANGS = {"pt", "fr", "es", "it"}


def _day_phrase_local(
    lang: str, start_date: datetime, end_date: datetime, month: int, year: int,
) -> str:
    """Localised day phrase: German uses ordinal dots, others use plain numbers.

    Romance languages lowercase the month in running text; German and Dutch keep it.
    """
    span = (end_date.date() - start_date.date()).days
    m = _month_local(lang, month)
    if lang in _LOWERCASE_MONTH_LANGS:
        m = m.lower()
    if span <= 7:
        sd, ed = start_date.day, end_date.day
        if lang == "de":
            if sd == ed:
                return f"{sd}. {m} {year}"
            return f"{sd}.–{ed}. {m} {year}"
        if sd == ed:
            return f"{sd} {m} {year}"
        return f"{sd}–{ed} {m} {year}"
    return f"{m} {year}"


def _window_short(start_utc: datetime, end_utc: datetime, tz: str):
    """Return (start_local, end_local, month, year, is_short) from a Window."""
    zone = ZoneInfo(tz)
    s = start_utc.astimezone(zone)
    e = end_utc.astimezone(zone)
    return s, e, s.month, s.year


# ---------- main entry ----------


def plan(
    facets: dict,
    window,
    *,
    max_queries: int = 6,
    offset: int = 0,
) -> list[PlannedQuery]:
    """Build the query plan from facets and a resolved window.

    Returns an empty list when there is no place and the criteria are not
    online-only.
    """
    place = facets.get("place")
    city: str | None = place.get("city") if place else None
    country: str | None = place.get("country") if place else None
    is_online: bool = place.get("online", False) if place else False

    # No city and not online -> empty plan.
    if not city and not is_online:
        return []

    lang: str | None = facets.get("language")
    topics: list[str] = facets.get("topics", [])[:2]
    topics_local: list[str] = facets.get("topics_local", [])[:2]
    formats: list[str] = facets.get("formats", [])

    start_local, end_local, month, year = _window_short(
        window.start_utc, window.end_utc, window.tz,
    )

    month_en = _month_en(month)
    month_loc = _month_local(lang, month) if lang and lang != "en" else None
    city_loc = _city_local(lang, city) if lang and lang != "en" and city else None

    dp_en = _day_phrase_en(start_local, end_local, month, year)
    dp_loc = (_day_phrase_local(lang, start_local, end_local, month, year)
              if lang and lang != "en" else None)

    is_short = (end_local.date() - start_local.date()).days <= 7

    raw: list[str] = []
    lang_flags: list[str | None] = []  # "en" or lang for each query

    def _add(text: str, qlang: str | None = "en") -> None:
        raw.append(text)
        lang_flags.append(qlang)

    # --- Template 1: {topic} {city} {Month} {year} ---
    if topics:
        for t in topics:
            if city:
                _add(f"{t} {city} {month_en} {year}")
    else:
        if city:
            _add(f"events {city} {month_en} {year}")

    # --- Template 2: {topic_local} {city_local} {Month_local} {year} (lang != en) ---
    if lang and lang != "en" and city:
        c = city_loc or city
        ml = month_loc or month_en
        if topics_local:
            for tl in topics_local:
                _add(f"{tl} {c} {ml} {year}", lang)
        else:
            ew = _EVENTS_WORD.get(lang, "events")
            _add(f"{ew} {c} {ml} {year}", lang)

    # --- Template 3: {topic} {format} {city} {day_phrase} ---
    if city:
        topic_word = topics[0] if topics else "events"
        if topics:
            fmt = formats[0] if formats else "concert"
            _add(f"{topic_word} {fmt} {city} {dp_en}")
        else:
            # "events {city} {day_phrase}" — no redundant format word
            _add(f"{topic_word} {city} {dp_en}")

    # --- Template 4: {city_local} {events_word} {topic_local} {day_phrase_local} (lang != en) ---
    if lang and lang != "en" and city and dp_loc:
        c = city_loc or city
        ew = _EVENTS_WORD.get(lang, "events")
        if topics_local:
            tl = topics_local[0]
            _add(f"{c} {ew} {tl} {dp_loc}", lang)
        else:
            _add(f"{c} {ew} {dp_loc}", lang)

    # --- Template 5: {topic} {city} tickets {Month} {year} ---
    if city:
        topic_word = topics[0] if topics else "events"
        _add(f"{topic_word} {city} tickets {month_en} {year}")

    # --- Template 6: {topic} {city} programme this week / program {Month} {year} ---
    if city and is_short:
        topic_word = topics[0] if topics else "events"
        _add(f"{topic_word} {city} programme this week")

    # --- Template 7: {topic} online {Month} {year} ---
    if is_online and not city:
        topic_word = topics[0] if topics else "events"
        _add(f"{topic_word} online {month_en} {year}")

    # Dedup case-insensitively, preserving order.
    seen: set[str] = set()
    deduped: list[tuple[str, str | None]] = []
    for text, ql in zip(raw, lang_flags):
        key = text.lower()
        if key not in seen:
            seen.add(key)
            deduped.append((text, ql))

    # Apply rotation offset and truncate.
    n = len(deduped)
    if n == 0:
        return []
    rotated = [deduped[(i + offset) % n] for i in range(n)]
    selected = rotated[:max_queries]

    return [
        PlannedQuery(
            text=text,
            country=country,
            language=ql if ql and ql != "en" else None,
            priority=i + 1,
        )
        for i, (text, ql) in enumerate(selected)
    ]
