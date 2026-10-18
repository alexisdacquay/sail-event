"""Factory functions — select adapter implementation by env var."""

from __future__ import annotations

import os
from typing import Protocol


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
    _refused: bool = True

    def __init__(self, provider: str) -> None:
        self._provider = provider
        self.model_id = f"{provider}:deferred"

    def complete_json(self, **kwargs):
        raise RuntimeError(
            f"adapters refused in prod: LLM_PROVIDER={self._provider!r} "
            "is not allowed when APP_ENV=prod"
        )


class _DeferredProdSearchGuard:
    """Raises at first use in prod when SEARCH_PROVIDER is fixture."""

    name: str = "fixture"
    _refused: bool = True

    def search(self, *args, **kwargs):
        raise RuntimeError(
            "adapters refused in prod: set SEARCH_PROVIDER and LLM_PROVIDER"
        )


# --- old-style factories (kept for backward compat until old code deleted) ---


def get_search_provider():
    if os.environ.get("SCORER"):
        raise ValueError("SCORER is replaced by LLM_PROVIDER")

    value = os.environ.get("SEARCH_PROVIDER", "fixture")
    is_prod = os.environ.get("APP_ENV") == "prod"

    if value == "fixture":
        if is_prod:
            return _DeferredProdSearchGuard()
        from .fixture_v2 import FixtureProviderV2
        return FixtureProviderV2()

    if value == "tavily":
        from .search_tavily_v2 import TavilyProviderV2
        return TavilyProviderV2()

    if value == "brave":
        from .search_brave import BraveProvider
        return BraveProvider()

    raise ValueError(f"Unknown SEARCH_PROVIDER: {value!r}")


def get_scorer():
    if os.environ.get("SCORER"):
        raise ValueError("SCORER is replaced by LLM_PROVIDER")
    # Legacy: only fake scorer remains until deletion
    from .fake import FakeScorer
    return FakeScorer()


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


class _NoOpGuardrail:
    """GUARDRAIL=none — always allows, no network."""

    def check(self, text: str) -> None:
        """No-op: always passes."""


def get_guardrail() -> _NoOpGuardrail:
    value = os.environ.get("GUARDRAIL", "none")
    if value == "none":
        return _NoOpGuardrail()
    # Real guardrails wired in issue H
    raise ValueError(f"Unknown GUARDRAIL: {value!r}")
