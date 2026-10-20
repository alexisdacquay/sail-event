"""Tavily Search API adapter.

Verbatim query, raw_content requested, no country/language/freshness parameters.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import ClassVar

from .search import SearchResult


class TavilyProvider:
    API_URL: ClassVar[str] = "https://api.tavily.com/search"
    TIMEOUT: ClassVar[int] = 10

    name: str = "tavily"

    def __init__(self, api_key: str | None = None) -> None:
        self._key = api_key or os.environ.get("TAVILY_API_KEY", "")
        if not self._key:
            raise ValueError(
                "TAVILY_API_KEY environment variable is required "
                "when SEARCH_PROVIDER=tavily"
            )

    def search(
        self,
        query: str,
        *,
        country: str | None = None,
        language: str | None = None,
        freshness_days: int | None = None,
        max_results: int = 20,
    ) -> list[SearchResult]:
        depth = os.environ.get("TAVILY_SEARCH_DEPTH", "advanced")
        body: dict = {
            "query": query,
            "search_depth": depth,
            "max_results": max_results,
            "include_raw_content": True,
        }

        data = self._post(body)
        results: list[SearchResult] = []
        for item in data.get("results", []):
            results.append(SearchResult(
                url=item.get("url", ""),
                title=item.get("title", ""),
                snippet=item.get("content", ""),
                raw_content=item.get("raw_content") or None,
                published_at=item.get("published_date") or None,
                provider="tavily",
            ))
        return results

    def _post(self, body: dict) -> dict:
        import time as _time
        payload = json.dumps(body).encode()
        for attempt in range(2):
            req = urllib.request.Request(
                self.API_URL,
                data=payload,
                headers={
                    "Authorization": f"Bearer {self._key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as exc:
                if exc.code == 429 and attempt == 0:
                    _time.sleep(3)
                    continue
                raise RuntimeError(f"Tavily API error: HTTP {exc.code}") from exc
            except urllib.error.URLError as exc:
                raise RuntimeError(f"Tavily API error: {exc.reason}") from exc
        raise RuntimeError("Tavily API: failed after retry")
