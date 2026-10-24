"""Tests for FakeLanguageModel — recording replay keyed by prompt name, version and hash."""

from __future__ import annotations

import pytest

from app.adapters.llm_fake import FakeLanguageModel


class TestFakeLanguageModel:
    def test_replays_recording(self):
        model = FakeLanguageModel()
        result, usage = model.complete_json(
            prompt_name="guard",
            prompt_version="v2",
            variables={"text": "something fun this weekend"},
            schema={"type": "object"},
        )
        assert result == {"blocked": False, "reason": "ok"}
        assert usage.tokens_in == 174
        assert usage.tokens_out == 43

    def test_missing_recording_raises(self):
        model = FakeLanguageModel()
        with pytest.raises(FileNotFoundError, match="guard"):
            model.complete_json(
                prompt_name="guard",
                prompt_version="v2",
                variables={"text": "this text has no recording"},
                schema={"type": "object"},
            )

    def test_model_id(self):
        model = FakeLanguageModel()
        assert model.model_id == "fake:recorded"


class TestFixtureIntegrity:
    """Every committed fixture must be a real model recording, never hand-written."""

    def test_no_placeholder_fixtures(self):
        import json
        from pathlib import Path

        fixtures_root = Path(__file__).parent / "fixtures" / "llm"
        bad = []
        for f in fixtures_root.rglob("*.json"):
            data = json.loads(f.read_text())
            reason = data.get("response", {}).get("reason", "")
            recorded = data.get("recorded", "")
            recorded_at = data.get("recorded_at", "")
            if reason == "unused fixture":
                bad.append(f"{f.relative_to(fixtures_root)}: reason is 'unused fixture'")
            if recorded == "live" and not recorded_at:
                bad.append(f"{f.relative_to(fixtures_root)}: recorded=live without recorded_at")
        assert not bad, "Fixture integrity failures:\n" + "\n".join(bad)
