"""Event extraction — every fetched page read in full, in parallel.

Results with raw_content get a per-page model call (the pass-2 prompt);
results without raw_content fall back to a single snippet-only call.
Page reads run in parallel via ThreadPoolExecutor, EXTRACT_CONCURRENCY
(env var, default 5).

The guard runs only on criteria text at save; pages are never guarded.
"""

from __future__ import annotations

import contextvars
import json
import logging
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

from opentelemetry import trace

from ..adapters.search import SearchResult, canonical_url
from ..services import clock

tracer = trace.get_tracer("sail-event.extract")

logger = logging.getLogger(__name__)

PROMPT_NAME = "extract"
PROMPT_VERSION = "v2"
# 10, not 50: at 50 the model calls opened in 50-connection bursts and timed out on connect (PR 144).
EXTRACT_CONCURRENCY = int(os.environ.get("EXTRACT_CONCURRENCY", "10"))
# Rendered into the prompt only when a links block follows the page, so prompts without one are unchanged.
LINKS_RULE = ' When the page is followed by "Links on this page", take the event\'s own link from that list.'

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
class PageInfo:
    url: str
    title: str
    events: int
    kind: str  # single_event, listing, not_event, no_content, error


@dataclass
class ExtractionCounts:
    pages_content_pass: int = 0
    events_extracted: int = 0
    pages_with_events: int = 0
    filtered_non_event: int = 0  # pages whose full read returned no events
    extract_errors: int = 0
    page_details: list[PageInfo] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


def _read_schema() -> dict:
    from ..adapters.prompts.loader import _PROMPTS_DIR
    path = _PROMPTS_DIR / f"{PROMPT_NAME}_{PROMPT_VERSION}.schema.json"
    return json.loads(path.read_text())


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
    on_page_done=None,
    page_links=None,
) -> tuple[list[ExtractedEvent], ExtractionCounts]:
    """Run extraction over a list of search results. Returns (events, counts).

    Every result with raw_content is read in full (pass-2 prompt), in
    parallel up to EXTRACT_CONCURRENCY.  Results without raw_content
    fall back to a single snippet-only call covering all of them.
    page_links(url) -> [(name, url)] | None, when given, lists the links on each page read in full.
    """
    counts = ExtractionCounts()
    schema = _read_schema()
    schema_text = json.dumps(schema, indent=2)

    # Format dates in the user's local timezone for the prompt
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(user_tz)
    ws = window_start.astimezone(tz).strftime("%Y-%m-%d")
    we = window_end.astimezone(tz).strftime("%Y-%m-%d")
    today = clock.now().astimezone(tz).strftime("%Y-%m-%d")

    all_events: list[ExtractedEvent] = []
    error_urls: set[str] = set()  # pages where the model call failed

    # Split results: those with raw_content get full page reads,
    # those without fall back to snippet-only extraction.
    with_content = [r for r in results if r.raw_content]
    without_content = [r for r in results if not r.raw_content]

    # --- Full page reads (parallel) ---
    if with_content:
        concurrency = min(EXTRACT_CONCURRENCY, len(with_content))

        def _read_one_page(r: SearchResult) -> tuple[SearchResult, list[ExtractedEvent] | None]:
            """Read one page in full. Returns (result, events_or_None_on_error)."""
            links = page_links(r.url) if page_links else None
            content = f"URL: {r.url}\n\n{r.raw_content}"
            if links:  # the provider's page text has no URLs; the page's own links give the model some
                content += "\n\nLinks on this page:\n" + "\n".join(f"{name} -> {url}" for name, url in links)
            variables = {
                "today": today,
                "window_start": ws,
                "window_end": we,
                "target_city": target_city,
                "target_country": target_country,
                "content": content,
                "schema": schema_text,
                "links_rule": LINKS_RULE if links else "",
            }
            with tracer.start_as_current_span("page") as pspan:
                try:
                    response, _usage = model.complete_json(
                        prompt_name=PROMPT_NAME,
                        prompt_version=PROMPT_VERSION,
                        variables=variables,
                    )
                    page_events = _process_pass2(response, r, counts, links)
                    pspan.set_attribute("page_kind", response.get("page_kind", "unknown"))
                    pspan.set_attribute("event_count", len(page_events))
                    return r, page_events
                except Exception as exc:
                    logger.warning("extract page error for %s: %s", r.url, exc)
                    with counts._lock:
                        counts.extract_errors += 1
                        error_urls.add(r.url)
                    pspan.set_attribute("page_kind", "error")
                    pspan.set_attribute("event_count", 0)
                    return r, None

        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            # #142: copy the OTel context per task so page spans keep their parent
            futures = {pool.submit(contextvars.copy_context().run, _read_one_page, r): r for r in with_content}
            for future in as_completed(futures):
                r, page_events = future.result()
                with counts._lock:
                    counts.pages_content_pass += 1
                    if page_events is not None:
                        all_events.extend(page_events)
                if on_page_done:
                    on_page_done(counts)

    # --- Snippet-only fallback for results without raw_content ---
    if without_content:
        content = _format_pass1_content(without_content)
        variables = {
            "today": today,
            "window_start": ws,
            "window_end": we,
            "target_city": target_city,
            "target_country": target_country,
            "content": content,
            "schema": schema_text,
            "links_rule": "",
        }
        try:
            response, _usage = model.complete_json(
                prompt_name=PROMPT_NAME,
                prompt_version=PROMPT_VERSION,
                variables=variables,
            )
            pass1_events = _process_pass1(response, without_content, counts)
            all_events.extend(pass1_events)
        except Exception as exc:
            logger.warning("extract snippet-only error: %s", exc)
            counts.extract_errors += 1

    # Deterministic order: sort by source_url so dedup in filters is stable
    # regardless of thread completion order.
    all_events.sort(key=lambda e: (e.source_url, e.start_local or "", e.title))

    # Page counters derived once at the end
    counts.pages_with_events = len({e.source_url for e in all_events})
    counts.filtered_non_event = len(results) - counts.pages_with_events

    # Per-page detail for the run row
    events_by_url: dict[str, list[ExtractedEvent]] = {}
    for ev in all_events:
        events_by_url.setdefault(ev.source_url, []).append(ev)
    for r in results:
        evts = events_by_url.get(r.url, [])
        if evts:
            kind = evts[0].page_kind
        elif r.url in error_urls:
            kind = "error"
        elif not r.raw_content:
            kind = "no_content"
        else:
            kind = "not_event"
        counts.page_details.append(PageInfo(
            url=r.url, title=r.title, events=len(evts), kind=kind,
        ))

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
    """Process a snippet-only extraction response (multiple results in one call)."""
    raw_events = response.get("events", [])

    if not raw_events:
        return []

    # Build URL lookup
    url_set = {r.url for r in results}

    extracted: list[ExtractedEvent] = []
    for ev in raw_events:
        confidence = ev.get("confidence", 0)
        if confidence < 0.5:
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

    return extracted


def _process_pass2(
    response: dict,
    result: SearchResult,
    counts: ExtractionCounts,
    links: list[tuple[str, str]] | None = None,
) -> list[ExtractedEvent]:
    """Process a full-page extraction response (single page).

    page_kind comes from the model's answer, not inferred.
    With the page's links collected, an event link must be the page itself or one of them;
    without (fetch failed or not tried), the same-origin rule applies as before.
    """
    page_kind = response.get("page_kind", "not_event")
    raw_events = response.get("events", [])

    if page_kind == "not_event" or not raw_events:
        return []

    result_urls = {result.url}
    on_page = {canonical_url(u) for _, u in links} | {canonical_url(result.url)} if links else None
    extracted: list[ExtractedEvent] = []
    for ev in raw_events:
        confidence = ev.get("confidence", 0)
        if confidence < 0.5:
            continue

        link = ev.get("link") or result.url
        # Structure layer: link allow-list
        if not (canonical_url(link) in on_page if on_page else _link_allowed(link, result_urls)):
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
        with counts._lock:
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
