"""Detail-page hop — fetch each listing event's own page, re-extract.

For every event extracted from a page the model classed as `listing`,
when the event's link differs from source_url, is same-site HTTP(S),
the pipeline fetches that page and re-extracts the event.  The judge
receives the record from the detail page (richer: title, time, description).

Fetches run in parallel via the existing EXTRACT_CONCURRENCY pool.
# shortcut: plain urllib.request; upgrade to Tavily Extract when blocked sites (403s) matter
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse

from ..services.extract import (
    ExtractedEvent,
    EXTRACT_CONCURRENCY,
    PROMPT_NAME,
    PROMPT_VERSION,
    _read_schema,
    _strip_markup,
    _link_allowed,
)
from ..services import clock

logger = logging.getLogger("sail-event.detail_hop")

DETAIL_FETCH_TIMEOUT = int(os.environ.get("DETAIL_FETCH_TIMEOUT", "10"))
DETAIL_FETCH_MAX_BYTES = int(os.environ.get("DETAIL_FETCH_MAX_BYTES", str(2 * 1024 * 1024)))


@dataclass
class HopCounts:
    pages_detail_fetched: int = 0
    detail_fetch_errors: int = 0
    detail_llm_calls: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


def _needs_hop(ev: ExtractedEvent) -> bool:
    """True when the event came from a listing and has a same-site detail link."""
    if ev.page_kind != "listing":
        return False
    if not ev.link or ev.link == ev.source_url:
        return False
    parsed_link = urlparse(ev.link)
    parsed_source = urlparse(ev.source_url)
    if parsed_link.scheme not in ("http", "https"):
        return False
    if parsed_link.netloc != parsed_source.netloc:
        return False
    return True


def _fetch_detail(url: str) -> str | None:
    """Fetch a detail page.  Returns HTML text or None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "sail-event/1.0"})
        with urllib.request.urlopen(req, timeout=DETAIL_FETCH_TIMEOUT) as resp:
            if resp.status >= 400:
                return None
            ct = resp.headers.get_content_type() if hasattr(resp.headers, "get_content_type") else ""
            if ct and "html" not in ct:
                return None
            # urlopen's timeout is per socket read; a slow-drip server needs a total deadline
            deadline = time.monotonic() + DETAIL_FETCH_TIMEOUT
            body = b""
            while len(body) <= DETAIL_FETCH_MAX_BYTES:
                if time.monotonic() > deadline:
                    raise TimeoutError(f"detail fetch exceeded {DETAIL_FETCH_TIMEOUT}s total")
                chunk = resp.read1(64 * 1024)
                if not chunk:
                    break
                body += chunk
            if len(body) > DETAIL_FETCH_MAX_BYTES:
                return None
            return body.decode("utf-8", errors="replace")
    except Exception as exc:
        logger.debug("detail fetch failed for %s: %s", url, exc)
        return None


def detail_hop(
    events: list[ExtractedEvent],
    *,
    model,
    user_tz: str,
    window_start: datetime,
    window_end: datetime,
    target_city: str,
    target_country: str,
) -> tuple[list[ExtractedEvent], HopCounts]:
    """Replace listing events with their detail-page re-extraction where possible.

    Events that don't need a hop, or whose hop fails, pass through unchanged.
    """
    counts = HopCounts()

    # Split: events needing hop vs pass-through
    to_hop: list[tuple[int, ExtractedEvent]] = []
    for i, ev in enumerate(events):
        if _needs_hop(ev):
            to_hop.append((i, ev))

    if not to_hop:
        return events, counts

    schema = _read_schema()
    schema_text = json.dumps(schema, indent=2)
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(user_tz)
    ws = window_start.astimezone(tz).strftime("%Y-%m-%d")
    we = window_end.astimezone(tz).strftime("%Y-%m-%d")
    today = clock.now().astimezone(tz).strftime("%Y-%m-%d")

    result_events = list(events)  # shallow copy

    def _hop_one(idx: int, ev: ExtractedEvent) -> tuple[int, ExtractedEvent | None]:
        """Fetch detail page and re-extract.  Returns (index, new_event_or_None)."""
        html = _fetch_detail(ev.link)
        if html is None:
            with counts._lock:
                counts.detail_fetch_errors += 1
            return idx, None

        with counts._lock:
            counts.pages_detail_fetched += 1

        # Re-extract from the detail page
        variables = {
            "today": today,
            "window_start": ws,
            "window_end": we,
            "target_city": target_city,
            "target_country": target_country,
            "content": f"URL: {ev.link}\n\n{html}",
            "schema": schema_text,
        }
        try:
            response, _usage = model.complete_json(
                prompt_name=PROMPT_NAME,
                prompt_version=PROMPT_VERSION,
                variables=variables,
            )
            with counts._lock:
                counts.detail_llm_calls += 1
        except Exception as exc:
            logger.warning("detail extract error for %s: %s", ev.link, exc)
            with counts._lock:
                counts.detail_fetch_errors += 1
            return idx, None

        # Pick the best event from the detail page response
        raw_events = response.get("events", [])
        if not raw_events:
            return idx, None

        # Take the first event with confidence >= 0.5
        for rev in raw_events:
            confidence = rev.get("confidence", 0)
            if confidence < 0.5:
                continue

            link = rev.get("link", ev.link)
            result_urls = {ev.link, ev.source_url}
            if not _link_allowed(link, result_urls):
                link = ev.link

            title = _strip_markup(rev.get("title", ""))[:200]
            description = _strip_markup(rev.get("description", ""))[:500]

            return idx, ExtractedEvent(
                title=title,
                start_local=rev.get("start_local", ""),
                start_tz=rev.get("start_tz"),
                end_local=rev.get("end_local"),
                venue=rev.get("venue"),
                city=rev.get("city"),
                country=rev.get("country"),
                link=link,
                description=description,
                confidence=confidence,
                source_url=ev.link,  # detail page is the new source
                page_kind=response.get("page_kind", "single_event"),
            )

        return idx, None  # no usable event on detail page

    concurrency = min(EXTRACT_CONCURRENCY, len(to_hop))
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(_hop_one, idx, ev): idx for idx, ev in to_hop}
        for future in as_completed(futures):
            idx, new_ev = future.result()
            if new_ev is not None:
                result_events[idx] = new_ev

    return result_events, counts
