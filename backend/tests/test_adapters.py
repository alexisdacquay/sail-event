"""Contract tests for adapter factory functions."""

import os

import pytest

from app.adapters import get_search_provider


# ---------- Factory functions ----------


class TestFactories:
    def test_get_search_provider_default(self, monkeypatch):
        monkeypatch.delenv("SEARCH_PROVIDER", raising=False)
        provider = get_search_provider()
        from app.adapters.fixture import FixtureProvider
        assert isinstance(provider, FixtureProvider)

    def test_get_search_provider_exa(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "exa")
        monkeypatch.setenv("EXA_API_KEY", "test-key")
        provider = get_search_provider()
        from app.adapters.search_exa import ExaProvider
        assert isinstance(provider, ExaProvider)

    def test_get_search_provider_raises_on_unknown(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "unknown")
        with pytest.raises(ValueError, match="unknown"):
            get_search_provider()

    def test_scorer_env_raises(self, monkeypatch):
        monkeypatch.setenv("SCORER", "anything")
        with pytest.raises(ValueError, match="unset SCORER; use LLM_PROVIDER"):
            get_search_provider()
