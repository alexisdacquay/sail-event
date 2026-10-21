"""Fixture search provider — returns golden set B pages.

Shaped as SearchResult; dates inside the fixed clock's window.
"""

from __future__ import annotations

import importlib.resources
import json

from .search import SearchResult


class FixtureProvider:
    name: str = "fixture"

    def __init__(self) -> None:
        ref = importlib.resources.files(__package__).joinpath("fixtures.json")
        raw = json.loads(ref.read_text(encoding="utf-8"))
        self._results: list[SearchResult] = [
            SearchResult(**{k: v for k, v in entry.items() if k != "id"})
            for entry in raw
        ]

    def search(
        self,
        query: str,
        *,
        country: str | None = None,
        language: str | None = None,
        freshness_days: int | None = None,
        max_results: int = 6,
        **kwargs: object,
    ) -> list[SearchResult]:
        # Return all fixture results regardless of query; the pipeline's
        # filters and extraction decide what passes.
        return list(self._results)
