"""Brave Search API adapter.

GET with country=DE, search_lang, extra_snippets; no freshness sent;
page_age best-effort; raw_content always null.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import ClassVar

from .search import SearchResult


class BraveProvider:
    API_URL: ClassVar[str] = "https://api.search.brave.com/res/v1/web/search"
    TIMEOUT: ClassVar[int] = 10

    name: str = "brave"

    def __init__(self, api_key: str | None = None) -> None:
        self._key = api_key or os.environ.get("BRAVE_API_KEY", "")
        if not self._key:
            raise ValueError(
                "BRAVE_API_KEY environment variable is required "
                "when SEARCH_PROVIDER=brave"
            )

    def search(
        self,
        query: str,
        *,
        country: str | None = None,
        language: str | None = None,
        freshness_days: int | None = None,
        max_results: int = 6,
    ) -> list[SearchResult]:
        params: dict[str, str] = {
            "q": query,
            "count": str(max_results),
            "extra_snippets": "true",
        }

        url = f"{self.API_URL}?{urllib.parse.urlencode(params)}"
        data = self._get(url)

        results: list[SearchResult] = []
        for item in data.get("web", {}).get("results", []):
            snippet_parts = [item.get("description", "")]
            for extra in item.get("extra_snippets", []):
                snippet_parts.append(extra)
            snippet = "\n".join(s for s in snippet_parts if s)

            published_at = item.get("page_age") or None

            results.append(SearchResult(
                url=item.get("url", ""),
                title=item.get("title", ""),
                snippet=snippet,
                raw_content=None,
                published_at=published_at,
                provider="brave",
            ))
        return results

    def _get(self, url: str) -> dict:
        """GET with one retry on 429/5xx (§8 backoff)."""
        last_exc: Exception | None = None
        for attempt in range(2):
            req = urllib.request.Request(url, headers={
                "X-Subscription-Token": self._key,
                "Accept": "application/json",
            })
            try:
                with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 500, 502, 503, 504) and attempt == 0:
                    import time
                    time.sleep(2)
                    last_exc = exc
                    continue
                raise RuntimeError(f"Brave API error: HTTP {exc.code}") from exc
            except urllib.error.URLError as exc:
                if isinstance(exc.reason, TimeoutError) and attempt == 0:
                    import time
                    time.sleep(2)
                    last_exc = exc
                    continue
                raise RuntimeError(f"Brave API error: {exc.reason}") from exc
            except TimeoutError as exc:
                if attempt == 0:
                    import time
                    time.sleep(2)
                    last_exc = exc
                    continue
                raise RuntimeError(f"Brave API error: {exc}") from exc
        raise RuntimeError(f"Brave API error after retry: HTTP {getattr(last_exc, 'code', last_exc)}") from last_exc
