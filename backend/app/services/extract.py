"""Event extraction — two-pass: snippets (pass 1), raw content (pass 2).

Pass 1: one call per query over its results (title + snippet each, numbered).
Pass 2: one call per listing or incomplete page, using the 20 000-char
         month-anchored slice of raw_content.

The get_guardrail() hook runs before every pass-2 call (no-op when GUARDRAIL=none).
"""

from __future__ import annotations

import calendar
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

from opentelemetry import trace

from ..adapters.search import SearchResult
from ..services import clock

tracer = trace.get_tracer("sail-event.extract")

logger = logging.getLogger(__name__)

PROMPT_NAME = "extract"
PROMPT_VERSION = "v2"
MAX_EVENTS_PER_PAGE = 10
CONTENT_SLICE = 20_000

# --- structure layer helpers (§10) ---
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_CTRL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _strip_markup(text: str) -> str:
    """Remove HTML tags and control characters."""
    text = _HTML_TAG_RE.sub("", text)
    text = _CTRL_CHAR_RE.sub("", text)
    return text.strip()


def _link_allowed(link: str, result_urls: set[str]) -> bool:
    """A link is allowed only when it equals a search-result URL or shares origin."""
    if link in result_urls:
        return True
    parsed_link = urlparse(link)
    for rurl in result_urls:
        parsed_r = urlparse(rurl)
        if (parsed_r.scheme == parsed_link.scheme
                and parsed_r.netloc == parsed_link.netloc):
            return True
    return False


@dataclass
class ExtractedEvent:
    title: str
    start_local: str
    start_tz: str | None
    end_local: str | None
    venue: str | None
    city: str | None
    country: str | None
    link: str
    description: str
    confidence: float
    source_url: str
    page_kind: str


@dataclass
class ExtractionCounts:
    pages_content_pass: int = 0
    extract_truncated: int = 0
    events_extracted: int = 0
    filtered_non_event: int = 0
    extract_errors: int = 0
    guard_skipped: int = 0
    guard_fallback: int = 0
    guard_errors: int = 0


def _read_schema() -> dict:
    from ..adapters.prompts.loader import _PROMPTS_DIR
    path = _PROMPTS_DIR / f"{PROMPT_NAME}_{PROMPT_VERSION}.schema.json"
    return json.loads(path.read_text())


def _month_anchor(window_start: datetime, window_end: datetime, language: str | None) -> list[str]:
    """Month names to search for in raw_content (English + local)."""
    months: set[str] = set()
    for dt in (window_start, window_end):
        months.add(calendar.month_name[dt.month])
        months.add(calendar.month_abbr[dt.month])
    _LOCAL_MONTHS = {
        "de": ["", "Januar", "Februar", "März", "April", "Mai", "Juni",
               "Juli", "August", "September", "Oktober", "November", "Dezember"],
        "fr": ["", "janvier", "février", "mars", "avril", "mai", "juin",
               "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
        "es": ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
               "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
        "pt": ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
               "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"],
        "it": ["", "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
               "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
        "nl": ["", "januari", "februari", "maart", "april", "mei", "juni",
               "juli", "augustus", "september", "oktober", "november", "december"],
    }
    if language and language in _LOCAL_MONTHS:
        table = _LOCAL_MONTHS[language]
        for dt in (window_start, window_end):
            months.add(table[dt.month])
    return list(months)


def _slice_content(raw_content: str, anchors: list[str]) -> tuple[str, bool]:
    """Slice raw_content to CONTENT_SLICE chars, starting at the first month anchor."""
    if len(raw_content) <= CONTENT_SLICE:
        return raw_content, False
    best = len(raw_content)
    for anchor in anchors:
        idx = raw_content.lower().find(anchor.lower())
        if idx != -1 and idx < best:
            best = idx
    if best == len(raw_content):
        best = 0
    sliced = raw_content[best:best + CONTENT_SLICE]
    truncated = (best + CONTENT_SLICE) < len(raw_content) or best > 0
    return sliced, truncated


def _format_pass1_content(results: list[SearchResult]) -> str:
    """Format results as numbered title + snippet for pass 1."""
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"Result {i} (URL: {r.url}):\n{r.title}\n{r.snippet}")
    return "\n\n".join(lines)


def extract_events(
    results: list[SearchResult],
    *,
    window_start: datetime,
    window_end: datetime,
    target_city: str,
    target_country: str,
    language: str | None,
    user_tz: str,
    model,
    guardrail,
) -> tuple[list[ExtractedEvent], ExtractionCounts]:
    """Run extraction over a list of search results. Returns (events, counts)."""
    counts = ExtractionCounts()
    schema = _read_schema()
    schema_text = json.dumps(schema, indent=2)

    # Format dates in the user's local timezone for the prompt
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(user_tz)
    ws = window_start.astimezone(tz).strftime("%Y-%m-%d")
    we = window_end.astimezone(tz).strftime("%Y-%m-%d")
    today = clock.now().astimezone(tz).strftime("%Y-%m-%d")
    anchors = _month_anchor(window_start, window_end, language)

    all_events: list[ExtractedEvent] = []

    # Pass 1: over snippets
    if results:
        content = _format_pass1_content(results)
        variables = {
            "today": today,
            "window_start": ws,
            "window_end": we,
            "target_city": target_city,
            "target_country": target_country,
            "content": content,
            "schema": schema_text,
        }
        try:
            response, _usage = model.complete_json(
                prompt_name=PROMPT_NAME,
                prompt_version=PROMPT_VERSION,
                variables=variables,
            )
            pass1_events = _process_pass1(response, results, counts)
            all_events.extend(pass1_events)
        except Exception as exc:
            logger.warning("extract pass 1 error: %s", exc)
            counts.extract_errors += 1

    # Pass 2: per listing or incomplete page with raw_content
    # Group events by source_url to determine which results need pass 2
    events_by_url: dict[str, list[ExtractedEvent]] = {}
    for ev in all_events:
        events_by_url.setdefault(ev.source_url, []).append(ev)

    for r in results:
        if not r.raw_content:
            continue
        url_events = events_by_url.get(r.url, [])
        needs_p2 = (
            any(e.page_kind == "listing" for e in url_events)
            or any(not e.start_local or not e.city for e in url_events)
        )
        if not needs_p2:
            continue

        counts.pages_content_pass += 1

        with tracer.start_as_current_span("page") as pspan:
            sliced, truncated = _slice_content(r.raw_content, anchors)
            if truncated:
                counts.extract_truncated += 1

            try:
                guardrail.check(sliced, target="page")
            except Exception as exc:
                from ..adapters.guard_lakera import ContentFlagged
                if isinstance(exc, ContentFlagged):
                    counts.guard_skipped += 1
                else:
                    # Both guards failed or RuntimeError — skip page, count error
                    counts.guard_errors += 1
                pspan.set_attribute("page_kind", "guard_blocked")
                pspan.set_attribute("event_count", 0)
                continue

            variables = {
                "today": today,
                "window_start": ws,
                "window_end": we,
                "target_city": target_city,
                "target_country": target_country,
                "content": f"URL: {r.url}\n\n{sliced}",
                "schema": schema_text,
            }
            try:
                response, _usage = model.complete_json(
                    prompt_name=PROMPT_NAME,
                    prompt_version=PROMPT_VERSION,
                    variables=variables,
                )
                # Replace pass-1 events for this URL with pass-2 events
                all_events = [e for e in all_events if e.source_url != r.url]
                pass2_events = _process_pass2(response, r, counts)
                all_events.extend(pass2_events)
                pspan.set_attribute("page_kind", response.get("page_kind", "unknown"))
                pspan.set_attribute("event_count", len(pass2_events))
            except Exception as exc:
                logger.warning("extract pass 2 error for %s: %s", r.url, exc)
                counts.extract_errors += 1
                pspan.set_attribute("page_kind", "error")
                pspan.set_attribute("event_count", 0)

    return all_events, counts


def _infer_page_kind(url: str, all_events_from_url: int) -> str:
    """Infer page_kind from the count of events extracted for this URL."""
    if all_events_from_url == 0:
        return "not_event"
    if all_events_from_url == 1:
        return "single_event"
    return "listing"


def _process_pass1(
    response: dict,
    results: list[SearchResult],
    counts: ExtractionCounts,
) -> list[ExtractedEvent]:
    """Process a pass-1 extraction response (multiple results in one call)."""
    raw_events = response.get("events", [])

    if not raw_events:
        counts.filtered_non_event += len(results)
        return []

    # Build URL lookup
    url_set = {r.url for r in results}

    extracted: list[ExtractedEvent] = []
    for ev in raw_events:
        confidence = ev.get("confidence", 0)
        if confidence < 0.5:
            counts.filtered_non_event += 1
            continue

        link = ev.get("link", "")
        source_url = _match_source_url(link, results)
        # Structure layer: link allow-list
        if not _link_allowed(link, url_set):
            link = source_url if source_url in url_set else results[0].url
            source_url = link
        # Structure layer: strip markup and control chars, truncate
        title = _strip_markup(ev.get("title", ""))[:200]
        description = _strip_markup(ev.get("description", ""))[:500]

        extracted.append(ExtractedEvent(
            title=title,
            start_local=ev.get("start_local", ""),
            start_tz=ev.get("start_tz"),
            end_local=ev.get("end_local"),
            venue=ev.get("venue"),
            city=ev.get("city"),
            country=ev.get("country"),
            link=link,
            description=description,
            confidence=confidence,
            source_url=source_url,
            page_kind="single_event",  # refined below
        ))
        counts.events_extracted += 1

    # Refine page_kind per source_url
    url_counts: dict[str, int] = {}
    for ev in extracted:
        url_counts[ev.source_url] = url_counts.get(ev.source_url, 0) + 1
    for ev in extracted:
        ev.page_kind = _infer_page_kind(ev.source_url, url_counts.get(ev.source_url, 0))

    # Count non-event results (URLs that produced no events)
    result_urls_with_events = {ev.source_url for ev in extracted}
    for r in results:
        if r.url not in result_urls_with_events:
            counts.filtered_non_event += 1

    return extracted


def _process_pass2(
    response: dict,
    result: SearchResult,
    counts: ExtractionCounts,
) -> list[ExtractedEvent]:
    """Process a pass-2 extraction response (single page)."""
    page_kind = response.get("page_kind", "not_event")
    raw_events = response.get("events", [])

    if page_kind == "not_event" or not raw_events:
        counts.filtered_non_event += 1
        return []

    result_urls = {result.url}
    extracted: list[ExtractedEvent] = []
    for ev in raw_events[:MAX_EVENTS_PER_PAGE]:
        confidence = ev.get("confidence", 0)
        if confidence < 0.5:
            counts.filtered_non_event += 1
            continue

        link = ev.get("link", result.url)
        # Structure layer: link allow-list
        if not _link_allowed(link, result_urls):
            link = result.url
        # Structure layer: strip markup and control chars, truncate
        title = _strip_markup(ev.get("title", ""))[:200]
        description = _strip_markup(ev.get("description", ""))[:500]

        extracted.append(ExtractedEvent(
            title=title,
            start_local=ev.get("start_local", ""),
            start_tz=ev.get("start_tz"),
            end_local=ev.get("end_local"),
            venue=ev.get("venue"),
            city=ev.get("city"),
            country=ev.get("country"),
            link=link,
            description=description,
            confidence=confidence,
            source_url=result.url,
            page_kind=page_kind,
        ))
        counts.events_extracted += 1

    return extracted


def _match_source_url(link: str, results: list[SearchResult]) -> str:
    """Find the result whose URL matches or is the origin of the link."""
    for r in results:
        if r.url == link:
            return r.url
    parsed_l = urlparse(link)
    for r in results:
        parsed_r = urlparse(r.url)
        if parsed_r.scheme == parsed_l.scheme and parsed_r.netloc == parsed_l.netloc:
            return r.url
    return link
