"""Adapter interfaces and implementations."""

from .base import RawEvent, Scorer, SearchProvider
from .factory import get_scorer, get_search_provider
from .fake import FakeScorer
from .fixture import FixtureSearchProvider

__all__ = [
    "RawEvent",
    "SearchProvider",
    "Scorer",
    "FixtureSearchProvider",
    "FakeScorer",
    "get_search_provider",
    "get_scorer",
]
