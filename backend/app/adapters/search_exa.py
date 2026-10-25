"""Exa Search API adapter.

Verbatim query; page text fetched live (maxAgeHours 0) so no stale cached copies.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import ClassVar

from .search import SearchResult


class ExaProvider:
    API_URL: ClassVar[str] = "https://api.exa.ai/search"
    # Live crawl of 20 pages took 7.5-12.3 s on 2026-10-25; Tavily's 10 s would cut it.
    TIMEOUT: ClassVar[int] = 60

    name: str = "exa"

    def __init__(self, api_key: str | None = None) -> None:
        self._key = api_key or os.environ.get("EXA_API_KEY", "")
        if not self._key:
            raise ValueError(
                "EXA_API_KEY environment variable is required "
                "when SEARCH_PROVIDER=exa"
            )

    def search(
        self,
        query: str,
        *,
        country: str | None = None,
        language: str | None = None,
        freshness_days: int | None = None,
        max_results: int = 20,
        **kwargs: object,
    ) -> list[SearchResult]:
        body = {
            "query": query,
            "numResults": max_results,
            "type": "auto",
            "contents": {"text": True, "maxAgeHours": 0},
        }

        data = self._post(body)
        return [
            SearchResult(
                url=item.get("url", ""),
                title=item.get("title") or "",
                snippet="",  # Exa sends no snippet; extraction reads raw_content
                raw_content=item.get("text") or None,
                published_at=item.get("publishedDate") or None,
                provider="exa",
            )
            for item in data.get("results", [])
        ]

    def _post(self, body: dict) -> dict:
        """POST with one retry on 429/5xx."""
        payload = json.dumps(body).encode()
        last_exc: Exception | None = None
        for attempt in range(2):
            req = urllib.request.Request(
                self.API_URL,
                data=payload,
                headers={
                    "x-api-key": self._key,
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 500, 502, 503, 504) and attempt == 0:
                    import time
                    time.sleep(2)
                    last_exc = exc
                    continue
                raise RuntimeError(f"Exa API error: HTTP {exc.code}") from exc
            except urllib.error.URLError as exc:
                if isinstance(exc.reason, TimeoutError) and attempt == 0:
                    import time
                    time.sleep(2)
                    last_exc = exc
                    continue
                raise RuntimeError(f"Exa API error: {exc.reason}") from exc
            except TimeoutError as exc:
                if attempt == 0:
                    import time
                    time.sleep(2)
                    last_exc = exc
                    continue
                raise RuntimeError(f"Exa API error: {exc}") from exc
        raise RuntimeError(f"Exa API error after retry: HTTP {getattr(last_exc, 'code', last_exc)}") from last_exc
