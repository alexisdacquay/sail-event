"""Adapter interfaces and implementations."""

from .base import RawEvent, Scorer, SearchProvider
from .factory import get_scorer, get_search_provider
from .fake import FakeScorer
from .fixture import FixtureSearchProvider
from .search_tavily import TavilySearchProvider
from .scorer_claude import ClaudeScorer

__all__ = [
    "RawEvent",
    "SearchProvider",
    "Scorer",
    "FixtureSearchProvider",
    "FakeScorer",
    "TavilySearchProvider",
    "ClaudeScorer",
    "get_search_provider",
    "get_scorer",
]
