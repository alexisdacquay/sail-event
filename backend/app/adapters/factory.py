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


def get_search_provider():
    if os.environ.get("SCORER"):
        raise ValueError("unset SCORER; use LLM_PROVIDER")

    value = os.environ.get("SEARCH_PROVIDER", "fixture")
    is_prod = os.environ.get("APP_ENV") == "prod"

    if value == "fixture":
        if is_prod:
            return _DeferredProdSearchGuard()
        from .fixture import FixtureProvider
        return FixtureProvider()

    if value == "tavily":
        from .search_tavily import TavilyProvider
        return TavilyProvider()

    if value == "brave":
        from .search_brave import BraveProvider
        return BraveProvider()

    raise ValueError(f"Unknown SEARCH_PROVIDER: {value!r}")


def get_language_model() -> LanguageModel:
    if os.environ.get("SCORER"):
        raise ValueError("unset SCORER; use LLM_PROVIDER")

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

    def check(self, text: str, *, target: str = "criteria") -> None:
        """No-op: always passes."""


class _CompositeGuardrail:
    """Lakera primary, self-check fallback, metrics on every call.

    Raises ContentFlagged when the text is flagged (criteria → 400; page → skip).
    Raises GuardUnavailable only when both Lakera and the fallback fail AND
    GUARD_FALLBACK != self_check (i.e., no fallback configured).
    Raises RuntimeError when both fail and the caller must fail closed (criteria → 503).
    """

    def __init__(self, lakera, fallback, *, guard_counter) -> None:
        self._lakera = lakera
        self._fallback = fallback  # None when GUARD_FALLBACK != self_check
        self._counter = guard_counter

    def check(self, text: str, *, target: str = "criteria") -> None:
        from .guard_lakera import ContentFlagged, GuardUnavailable

        try:
            self._lakera.check(text)
            self._counter.add(1, {"guard": "lakera", "target": target, "outcome": "allowed"})
            return
        except ContentFlagged:
            self._counter.add(1, {"guard": "lakera", "target": target, "outcome": "flagged"})
            raise
        except GuardUnavailable:
            self._counter.add(1, {"guard": "lakera", "target": target, "outcome": "error"})
            if self._fallback is None:
                raise
            # Fall through to self-check
            try:
                self._fallback.check(text)
                self._counter.add(1, {"guard": "self_check", "target": target, "outcome": "allowed"})
                return
            except ContentFlagged:
                self._counter.add(1, {"guard": "self_check", "target": target, "outcome": "flagged"})
                raise
            except Exception:
                self._counter.add(1, {"guard": "self_check", "target": target, "outcome": "error"})
                raise RuntimeError("both guards failed")


def get_guardrail():
    from opentelemetry import metrics as otel_metrics

    value = os.environ.get("GUARDRAIL", "none")
    if value == "none":
        return _NoOpGuardrail()

    if value == "lakera":
        from .guard_lakera import LakeraGuardrail
        lakera = LakeraGuardrail()

        fallback = None
        if os.environ.get("GUARD_FALLBACK") == "self_check":
            model = get_language_model()
            from ..services.guardrails.self_check import SelfCheckGuardrail
            fallback = SelfCheckGuardrail(model)

        meter = otel_metrics.get_meter("sail-event.pipeline")
        counter = meter.create_counter(
            "sail_guard_runs_total",
            description="Guardrail check outcomes",
        )
        return _CompositeGuardrail(lakera, fallback, guard_counter=counter)

    raise ValueError(f"Unknown GUARDRAIL: {value!r}")
