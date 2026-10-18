"""Factory functions — select adapter implementation by env var."""

from __future__ import annotations

import os
from typing import Protocol

from .fake import FakeScorer
from .fixture import FixtureSearchProvider


def get_search_provider() -> FixtureSearchProvider:
    value = os.environ.get("SEARCH_PROVIDER", "fixture")
    if value == "fixture":
        return FixtureSearchProvider()
    if value == "tavily":
        from .search_tavily import TavilySearchProvider
        return TavilySearchProvider()
    raise ValueError(f"Unknown SEARCH_PROVIDER: {value!r}")


def get_scorer() -> FakeScorer:
    if os.environ.get("SCORER"):
        raise ValueError("SCORER is replaced by LLM_PROVIDER")
    value = os.environ.get("SCORER", "fake")
    if value == "fake":
        return FakeScorer()
    if value == "claude":
        from .scorer_claude import ClaudeScorer
        return ClaudeScorer()
    raise ValueError(f"Unknown SCORER: {value!r}")


class LanguageModel(Protocol):
    """Common interface for LLM adapters."""

    model_id: str

    def complete_json(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        variables: dict[str, str],
        schema: dict,
    ) -> tuple[dict, object]: ...


class _DeferredProdGuard:
    """Wraps an LLM adapter that refuses at first use in prod, not at import."""

    def __init__(self, provider: str) -> None:
        self._provider = provider
        self.model_id = f"{provider}:deferred"

    def complete_json(self, **kwargs):
        raise RuntimeError(
            f"adapters refused in prod: LLM_PROVIDER={self._provider!r} "
            "is not allowed when APP_ENV=prod"
        )


def get_language_model() -> LanguageModel:
    if os.environ.get("SCORER"):
        raise ValueError("SCORER is replaced by LLM_PROVIDER")

    value = os.environ.get("LLM_PROVIDER", "fake")
    is_prod = os.environ.get("APP_ENV") == "prod"

    if value == "fake":
        if is_prod:
            return _DeferredProdGuard("fake")  # type: ignore[return-value]
        from .llm_fake import FakeLanguageModel
        return FakeLanguageModel()  # type: ignore[return-value]

    if value == "openai_compatible":
        from .llm_openai_compat import OpenAICompatibleModel
        return OpenAICompatibleModel()  # type: ignore[return-value]

    raise ValueError(f"Unknown LLM_PROVIDER: {value!r}")
