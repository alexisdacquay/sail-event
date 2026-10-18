"""Tests for FakeLanguageModel — recording replay keyed by prompt name, version and hash."""

from __future__ import annotations

import pytest

from app.adapters.llm_fake import FakeLanguageModel


class TestFakeLanguageModel:
    def test_replays_recording(self):
        model = FakeLanguageModel()
        result, usage = model.complete_json(
            prompt_name="guard",
            prompt_version="v1",
            variables={"text": "jazz in Berlin"},
            schema={"type": "object"},
        )
        assert result == {"blocked": False, "reason": "ok"}
        assert usage.tokens_in == 180
        assert usage.tokens_out == 12

    def test_missing_recording_raises(self):
        model = FakeLanguageModel()
        with pytest.raises(FileNotFoundError, match="guard"):
            model.complete_json(
                prompt_name="guard",
                prompt_version="v1",
                variables={"text": "this text has no recording"},
                schema={"type": "object"},
            )

    def test_model_id(self):
        model = FakeLanguageModel()
        assert model.model_id == "fake:recorded"
