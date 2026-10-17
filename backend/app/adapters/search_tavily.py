"""Tavily Search API adapter — real web search for event candidates."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from typing import ClassVar

from .base import RawEvent

# Regex for ISO date (YYYY-MM-DD with optional time) and two textual forms.
# Returns "unknown" for anything else — good enough until the scorer (#20)
# parses the full description text.
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2})?")
_TEXTUAL_DATE = re.compile(
    r"(?:January|February|March|April|May|June|July|August|September"
    r"|October|November|December)\s+\d{1,2},?\s+\d{4}"
)
_SHORT_DATE = re.compile(
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"\s+\d{1,2},?\s+\d{4}"
)


def _extract_date(text: str) -> str:
    """Best-effort date from text; 'unknown' otherwise."""
    for pattern in (_ISO_DATE, _TEXTUAL_DATE, _SHORT_DATE):
        m = pattern.search(text)
        if m:
            return m.group()
    return "unknown"


class TavilySearchProvider:
    API_URL: ClassVar[str] = "https://api.tavily.com/search"
    TIMEOUT: ClassVar[int] = 10
    MAX_PER_QUERY: ClassVar[int] = 5

    def __init__(self, api_key: str | None = None) -> None:
        self._key = api_key or os.environ.get("TAVILY_API_KEY", "")
        if not self._key:
            raise ValueError(
                "TAVILY_API_KEY environment variable is required "
                "when SEARCH_PROVIDER=tavily"
            )

    def search(self, queries: list[str]) -> list[RawEvent]:
        seen_urls: set[str] = set()
        results: list[RawEvent] = []
        cap = int(os.environ.get("MAX_EVENTS_PER_RUN", "50"))

        for q in queries:
            if len(results) >= cap:
                break
            for item in self._query(q):
                url = item.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                content = item.get("content", "")
                title = item.get("title", "")
                date_text = _extract_date(content) or _extract_date(title)

                results.append(RawEvent(
                    title=title,
                    date_time=date_text if date_text else "unknown",
                    place="unknown",
                    link=url,
                    description=content,
                ))
                if len(results) >= cap:
                    break

        return results

    def _query(self, q: str) -> list[dict]:
        body = json.dumps({
            "query": q,
            "search_depth": "basic",
            "max_results": self.MAX_PER_QUERY,
        }).encode()
        req = urllib.request.Request(
            self.API_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {self._key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Tavily API error: HTTP {exc.code}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Tavily API error: {exc.reason}"
            ) from exc
        return data.get("results", [])


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "sailing events 2026"
    provider = TavilySearchProvider()
    for event in provider.search([query]):
        print(f"{event.date_time}  {event.title}")
        print(f"  {event.link}")
        print(f"  {event.description[:120]}...")
        print()
