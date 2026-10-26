"""Detail-page hop — fetch each listing event's own page, re-extract.

For every event extracted from a page the model classed as `listing`,
when the event's link differs from source_url and its host resolves only to public
addresses (extract only accepts links found on the listing page), the pipeline
fetches that page, reduces its HTML to text, and re-extracts the event.  The judge
receives the record from the detail page (richer: title, time, description).

Fetches run in parallel via the existing EXTRACT_CONCURRENCY pool.
# shortcut: plain urllib.request; upgrade to Tavily Extract when blocked sites (403s) matter
"""

from __future__ import annotations

import ipaddress
import json
import logging
import os
import re
import socket
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from ..adapters.search import canonical_url

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
    detail_extract_errors: int = 0  # model re-extraction failed; the page itself was fetched
    detail_llm_calls: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


def _public(url: str) -> bool:
    """True when url is http(s) and every address its host resolves to is global.

    Resolving lets the OS read every spelling (127.1, 2130706433, localhost., metadata names);
    loopback, private, link-local, unique-local and unspecified addresses are all refused.
    # shortcut: urllib resolves again to connect (a DNS-rebinding window); pin the checked address if that matters
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        return bool(infos) and all(ipaddress.ip_address(i[4][0].split("%")[0]).is_global for i in infos)
    except (OSError, ValueError, UnicodeError):  # unresolvable or malformed: refuse
        return False


class _PublicOnly(urllib.request.BaseHandler):
    """Refuses every request, the first one and each redirect, to a non-public destination."""

    def http_request(self, req):
        if not _public(req.full_url):
            raise urllib.error.URLError(f"non-public destination refused: {req.full_url}")
        return req

    https_request = http_request


_redirects = urllib.request.HTTPRedirectHandler()
_redirects.max_redirections = 5
_OPENER = urllib.request.build_opener(_PublicOnly, _redirects)


def _needs_hop(ev: ExtractedEvent) -> bool:
    """True when the event came from a listing and has its own link on a public host."""
    if ev.page_kind != "listing":
        return False
    if not ev.link or canonical_url(ev.link) == canonical_url(ev.source_url):
        return False
    return _public(ev.link)


_SKIP_TAGS = {"script", "style", "noscript", "svg", "template"}
_BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "br", "dd", "div", "dl", "dt",
    "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6",
    "header", "hr", "li", "main", "nav", "ol", "p", "pre", "section", "table",
    "td", "th", "title", "tr", "ul",
}
# meta/microdata whose content often carries the date and time (Musikverein: only there)
_CONTENT_KEYS = {"description", "og:title", "og:description", "startdate", "enddate", "doortime"}


class _TextParser(HTMLParser):
    """Visible text, <title>, JSON-LD and date-bearing meta; drops tags, scripts, styles, svg.

    Also keeps each anchor (text, href) and each JSON-LD blob, for page_links.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0  # depth inside elements whose content is dropped
        self._ld = False  # inside <script type="application/ld+json">
        self._seen: set[str] = set()  # description and og:description are usually equal
        self._open: list[tuple[str, int]] = []  # open <a>: (href, index into parts)
        self.anchors: list[tuple[str, str]] = []
        self.ld_blobs: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        key = (a.get("name") or a.get("property") or a.get("itemprop") or "").lower()
        if not self._skip and a.get("content") and key in _CONTENT_KEYS and a["content"] not in self._seen:
            self._seen.add(a["content"])
            self.parts.append(f"\n{a['content']}\n")
        if not self._skip and tag == "time" and a.get("datetime"):
            self.parts.append(f" {a['datetime']} ")
        if tag == "a" and a.get("href"):
            self._open.append((a["href"], len(self.parts)))
        if tag == "script" and (a.get("type") or "").strip().lower() == "application/ld+json":
            self._ld = True  # script content is CDATA to html.parser: no nested tags
            self.ld_blobs.append("")
        elif tag in _SKIP_TAGS:
            self._skip += 1
        self.parts.append("\n" if tag in _BLOCK_TAGS else " ")

    def handle_endtag(self, tag):
        if tag == "a" and self._open:
            href, start = self._open.pop()
            self.anchors.append((" ".join("".join(self.parts[start:]).split()), href))
        if tag == "script" and self._ld:
            self._ld = False
        elif tag in _SKIP_TAGS and self._skip:
            self._skip -= 1
        self.parts.append("\n" if tag in _BLOCK_TAGS else " ")

    def handle_data(self, data):
        if self._ld:
            self.ld_blobs[-1] += data
        if self._ld or not self._skip:
            self.parts.append(data)


def _html_to_text(html: str) -> str:
    parser = _TextParser()
    parser.feed(html)
    parser.close()
    text = re.sub(r"[^\S\n]+", " ", "".join(parser.parts))
    return re.sub(r"\s*\n\s*", "\n", text).strip()


def _ld_pairs(node, acc: list[tuple[str, str]]) -> None:
    """Every JSON-LD object with a string name and url (Event, ItemList items, ...)."""
    if isinstance(node, dict):
        if isinstance(node.get("name"), str) and isinstance(node.get("url"), str):
            acc.append((node["name"], node["url"]))
        node = list(node.values())
    if isinstance(node, list):
        for item in node:
            _ld_pairs(item, acc)


def page_links(url: str) -> list[tuple[str, str]] | None:
    """(name, absolute URL) for each link on the page: anchors and JSON-LD.  None when the fetch fails."""
    html = _fetch_html(url)
    if html is None:
        return None
    try:
        parser = _TextParser()
        parser.feed(html)
        parser.close()
        pairs = list(parser.anchors)
        for blob in parser.ld_blobs:
            try:
                _ld_pairs(json.loads(blob), pairs)
            except ValueError:
                pass
        own = canonical_url(url)
        links: dict[str, tuple[str, str]] = {}  # canonical URL -> (name, URL); first non-empty name wins
        for name, href in pairs:
            try:
                absolute = urljoin(url, href.strip())
                key = canonical_url(absolute)
            except ValueError:  # malformed href, e.g. a broken IPv6 host
                continue
            if urlparse(absolute).scheme not in ("http", "https") or key == own:
                continue
            if key not in links or not links[key][0]:
                links[key] = (name.strip()[:100], absolute)
        return list(links.values())
    except Exception as exc:  # untrusted HTML must never fail the page read: carry on without links
        logger.warning("page links failed for %s: %s", url, exc)
        return None


def _fetch_detail(url: str) -> str | None:
    """Fetch a detail page.  Returns its text (not HTML) or None on failure.

    Raw HTML was 98.2% of a London search's input tokens; text is ~5% of the HTML.
    """
    html = _fetch_html(url)
    return None if html is None else _html_to_text(html)


def _fetch_html(url: str) -> str | None:
    """Fetch a page's HTML under the deadline and size limit, or None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "sail-event/1.0"})
        with _OPENER.open(req, timeout=DETAIL_FETCH_TIMEOUT) as resp:
            if resp.status >= 400:
                return None
            ct = resp.headers.get_content_type() if hasattr(resp.headers, "get_content_type") else ""
            if ct and "html" not in ct:
                logger.warning("detail fetch failed for %s: content type %s", url, ct)
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
                logger.warning("detail fetch failed for %s: over %d bytes", url, DETAIL_FETCH_MAX_BYTES)
                return None
            return body.decode("utf-8", errors="replace")
    except Exception as exc:
        logger.warning("detail fetch failed for %s: %s", url, exc)
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
    on_page_done=None,
    fetch_pages: bool = True,
) -> tuple[list[ExtractedEvent], HopCounts]:
    """Replace listing events with their detail-page re-extraction where possible.

    Events that don't need a hop, or whose hop fails, pass through unchanged.
    on_page_done(done, total) is called once with 0 before the first page and after each page.
    fetch_pages=False (results not from the web) passes every event through.
    """
    counts = HopCounts()
    if not fetch_pages:
        return events, counts

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
        text = _fetch_detail(ev.link)
        if text is None:
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
            "content": f"URL: {ev.link}\n\n{text}",
            "schema": schema_text,
            "links_rule": "",
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
                counts.detail_extract_errors += 1
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
        if on_page_done:
            on_page_done(0, len(to_hop))
        for done, future in enumerate(as_completed(futures), 1):
            idx, new_ev = future.result()
            if new_ev is not None:
                result_events[idx] = new_ev
            if on_page_done:
                on_page_done(done, len(to_hop))

    return result_events, counts
