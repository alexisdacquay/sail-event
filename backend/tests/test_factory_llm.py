"""Tests for factory.get_language_model() and SCORER guard."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.adapters.factory import get_language_model


class TestGetLanguageModel:
    def test_default_is_fake(self):
        with patch.dict("os.environ", {}, clear=True):
            model = get_language_model()
        assert model.model_id == "fake:recorded"

    def test_fake_explicit(self):
        with patch.dict("os.environ", {"LLM_PROVIDER": "fake"}):
            model = get_language_model()
        assert model.model_id == "fake:recorded"

    def test_openai_compatible(self):
        env = {
            "LLM_PROVIDER": "openai_compatible",
            "LLM_BASE_URL": "https://api.deepseek.com",
            "LLM_API_KEY": "test-key",
            "LLM_MODEL": "deepseek-flash",
            "LLM_JSON_MODE": "json_object",
        }
        with patch.dict("os.environ", env):
            model = get_language_model()
        assert model.model_id == "openai_compatible:deepseek-flash"

    def test_unknown_provider_raises(self):
        with patch.dict("os.environ", {"LLM_PROVIDER": "gpt4"}):
            with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
                get_language_model()

    def test_scorer_set_raises(self):
        with patch.dict("os.environ", {"SCORER": "claude"}):
            with pytest.raises(ValueError, match="unset SCORER; use LLM_PROVIDER"):
                get_language_model()


class TestProdRefusal:
    """APP_ENV=prod + fake → refuses at first use, not at import."""

    def test_prod_fake_import_succeeds(self):
        """Importing main with APP_ENV=prod and no LLM keys must not crash."""
        env = {"APP_ENV": "prod"}
        with patch.dict("os.environ", env):
            model = get_language_model()
        # model_id is set — no error at construction
        assert "deferred" in model.model_id

    def test_import_main_with_prod_no_keys(self):
        """app.main must be importable with APP_ENV=prod and no LLM keys."""
        import importlib
        env = {"APP_ENV": "prod", "DATABASE_URL": "sqlite://"}
        with patch.dict("os.environ", env):
            import app.main  # noqa: F401
            importlib.reload(app.main)
        # No error — the factory is not called at import time

    def test_prod_fake_use_raises(self):
        env = {"APP_ENV": "prod", "LLM_PROVIDER": "fake"}
        with patch.dict("os.environ", env):
            model = get_language_model()
        with pytest.raises(RuntimeError, match="adapters refused in prod"):
            model.complete_json(
                prompt_name="guard",
                prompt_version="v1",
                variables={"text": "test"},
                schema={"type": "object"},
            )
