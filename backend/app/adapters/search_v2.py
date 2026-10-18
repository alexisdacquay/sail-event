"""SearchProvider v2 protocol and SearchResult model.

The old SearchProvider / RawEvent in base.py stay until the swap (issue F2).
"""

from __future__ import annotations

from typing import Protocol
from urllib.parse import urlparse, urlencode, parse_qs

from pydantic import BaseModel


class SearchResult(BaseModel):
    url: str
    title: str
    snippet: str
    raw_content: str | None = None
    published_at: str | None = None
    provider: str


class SearchProvider(Protocol):
    name: str

    def search(
        self,
        query: str,
        *,
        country: str | None = None,
        language: str | None = None,
        freshness_days: int | None = None,
        max_results: int = 6,
    ) -> list[SearchResult]: ...


# ---------- canonical URL ----------

_DROP_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term",
                "utm_content", "fbclid", "gclid", "ref", "source"}


def canonical_url(raw: str) -> str:
    """Lowercase scheme+host, drop fragment, drop tracking params, strip trailing /."""
    p = urlparse(raw)
    scheme = p.scheme.lower()
    host = p.netloc.lower()
    # drop default port
    if (scheme == "http" and host.endswith(":80")):
        host = host[:-3]
    elif (scheme == "https" and host.endswith(":443")):
        host = host[:-4]
    path = p.path.rstrip("/") or ""
    # filter query params
    qs = parse_qs(p.query, keep_blank_values=True)
    filtered = {k: v for k, v in qs.items() if k not in _DROP_PARAMS}
    query_str = urlencode(filtered, doseq=True) if filtered else ""
    parts = f"{scheme}://{host}{path}"
    if query_str:
        parts += f"?{query_str}"
    return parts


# ---------- known-page removal ----------


def remove_known_pages(
    results: list[SearchResult],
    stored_pages: list[dict],
) -> tuple[list[SearchResult], int]:
    """Remove results whose canonical URL matches a stored single_event page.

    *stored_pages* is a list of dicts with keys ``source_url`` and ``page_kind``.
    A stored ``listing`` page is kept for re-extraction.

    Returns (kept_results, results_known_count).
    """
    single_event_urls: set[str] = set()
    for page in stored_pages:
        if page.get("page_kind") == "single_event" and page.get("source_url"):
            single_event_urls.add(canonical_url(page["source_url"]))

    kept: list[SearchResult] = []
    known = 0
    for r in results:
        if canonical_url(r.url) in single_event_urls:
            known += 1
        else:
            kept.append(r)
    return kept, known
