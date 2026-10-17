"""Tests for ClaudeScorer — all fixture-based, no live network."""

from __future__ import annotations

import json
import pathlib
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from app.adapters.scorer_claude import ClaudeScorer, _PROMPT_TEMPLATE
from app.adapters.base import RawEvent

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "claude"

_EVENT = RawEvent(
    title="Round the Island Race 2026",
    date_time="2026-06-20",
    place="Isle of Wight, UK",
    link="https://example.com/round-island-2026",
    description="The Round the Island Race is one of the largest yacht races in the world.",
)


def _make_response(text: str) -> SimpleNamespace:
    """Build a minimal object matching anthropic.types.Message shape."""
    block = SimpleNamespace(type="text", text=text)
    return SimpleNamespace(content=[block])


def _fixture_response(name: str) -> SimpleNamespace:
    raw = json.loads((FIXTURES / name).read_text())
    block = raw["content"][0]
    return _make_response(block["text"])


# ---------- prompt rendering ----------


class TestPromptRendering:
    def test_all_fields_present(self):
        rendered = _PROMPT_TEMPLATE.format(
            title=_EVENT.title,
            date_time=_EVENT.date_time,
            place=_EVENT.place,
            description=_EVENT.description,
            criteria="sailing regattas",
        )
        assert _EVENT.title in rendered
        assert _EVENT.date_time in rendered
        assert _EVENT.place in rendered
        assert _EVENT.description in rendered
        assert "sailing regattas" in rendered

    def test_username_absent(self):
        rendered = _PROMPT_TEMPLATE.format(
            title=_EVENT.title,
            date_time=_EVENT.date_time,
            place=_EVENT.place,
            description=_EVENT.description,
            criteria="sailing regattas",
        )
        assert "username" not in rendered.lower()


# ---------- valid response ----------


class TestValidResponse:
    @patch("app.adapters.scorer_claude.anthropic.Anthropic")
    def test_parses_valid_fixture(self, mock_cls, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = _fixture_response("valid_response.json")

        scorer = ClaudeScorer()
        score_val, reason = scorer.score(_EVENT, "sailing regattas")
        assert score_val == 82
        assert isinstance(reason, str)
        assert len(reason) <= 120

    @patch("app.adapters.scorer_claude.anthropic.Anthropic")
    def test_model_id_property(self, mock_cls, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_cls.return_value = MagicMock()
        scorer = ClaudeScorer()
        assert scorer.model_id == "claude:claude-haiku-5-5:scorer_v1"

    @patch("app.adapters.scorer_claude.anthropic.Anthropic")
    def test_custom_model(self, mock_cls, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("SCORER_MODEL", "claude-sonnet-5-5")
        mock_cls.return_value = MagicMock()
        scorer = ClaudeScorer()
        assert scorer.model_id == "claude:claude-sonnet-5-5:scorer_v1"


# ---------- score outside 0-100 ----------


class TestScoreRange:
    @patch("app.adapters.scorer_claude.anthropic.Anthropic")
    def test_score_above_100_raises(self, mock_cls, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_response(
            '{"score": 150, "reason": "too high"}'
        )
        scorer = ClaudeScorer()
        with pytest.raises(ValueError, match="outside 0–100"):
            scorer.score(_EVENT, "sailing regattas")

    @patch("app.adapters.scorer_claude.anthropic.Anthropic")
    def test_score_below_0_raises(self, mock_cls, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_response(
            '{"score": -5, "reason": "negative"}'
        )
        scorer = ClaudeScorer()
        with pytest.raises(ValueError, match="outside 0–100"):
            scorer.score(_EVENT, "sailing regattas")


# ---------- reason truncation ----------


class TestReasonTruncation:
    @patch("app.adapters.scorer_claude.anthropic.Anthropic")
    def test_long_reason_truncated(self, mock_cls, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        long_reason = "a" * 200
        mock_client.messages.create.return_value = _make_response(
            json.dumps({"score": 50, "reason": long_reason})
        )
        scorer = ClaudeScorer()
        _, reason = scorer.score(_EVENT, "sailing regattas")
        assert len(reason) == 120


# ---------- malformed response ----------


class TestMalformedResponse:
    @patch("app.adapters.scorer_claude.anthropic.Anthropic")
    def test_invalid_json_raises(self, mock_cls, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = _fixture_response("malformed_response.json")

        scorer = ClaudeScorer()
        with pytest.raises(RuntimeError, match="invalid JSON"):
            scorer.score(_EVENT, "sailing regattas")

    @patch("app.adapters.scorer_claude.anthropic.Anthropic")
    def test_missing_score_field_raises(self, mock_cls, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_response(
            '{"reason": "no score field"}'
        )
        scorer = ClaudeScorer()
        with pytest.raises(RuntimeError, match="integer 'score'"):
            scorer.score(_EVENT, "sailing regattas")

    @patch("app.adapters.scorer_claude.anthropic.Anthropic")
    def test_no_text_block_raises(self, mock_cls, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = SimpleNamespace(content=[])

        scorer = ClaudeScorer()
        with pytest.raises(RuntimeError, match="no text block"):
            scorer.score(_EVENT, "sailing regattas")


# ---------- missing API key ----------


class TestMissingKey:
    def test_missing_key_raises(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            ClaudeScorer()


# ---------- factory integration ----------


class TestFactory:
    @patch("app.adapters.scorer_claude.anthropic.Anthropic")
    def test_factory_returns_claude(self, mock_cls, monkeypatch):
        monkeypatch.setenv("SCORER", "claude")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_cls.return_value = MagicMock()
        from app.adapters import get_scorer
        scorer = get_scorer()
        assert isinstance(scorer, ClaudeScorer)

    def test_factory_missing_key_raises(self, monkeypatch):
        monkeypatch.setenv("SCORER", "claude")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from app.adapters import get_scorer
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            get_scorer()
