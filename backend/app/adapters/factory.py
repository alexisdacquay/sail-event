"""Factory functions — select adapter implementation by env var."""

from __future__ import annotations

import os

from .fake import FakeScorer
from .fixture import FixtureSearchProvider


def get_search_provider() -> FixtureSearchProvider:
    value = os.environ.get("SEARCH_PROVIDER", "fixture")
    if value == "fixture":
        return FixtureSearchProvider()
    raise ValueError(f"Unknown SEARCH_PROVIDER: {value!r}")


def get_scorer() -> FakeScorer:
    value = os.environ.get("SCORER", "fake")
    if value == "fake":
        return FakeScorer()
    raise ValueError(f"Unknown SCORER: {value!r}")
