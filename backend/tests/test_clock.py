"""Tests for services/clock.py — FAKE_NOW and UTC fallback."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from app.services.clock import now


class TestClock:
    def test_fake_now(self):
        with patch.dict("os.environ", {"FAKE_NOW": "2026-10-18T12:00:00+02:00"}):
            result = now()
        assert result.year == 2026
        assert result.month == 10
        assert result.day == 18
        assert result.hour == 12
        assert result.tzinfo is not None

    def test_real_now_is_utc(self):
        with patch.dict("os.environ", {}, clear=True):
            result = now()
        assert result.tzinfo == UTC

    def test_fake_now_unset_returns_current(self):
        with patch.dict("os.environ", {}, clear=True):
            before = datetime.now(UTC)
            result = now()
            after = datetime.now(UTC)
        assert before <= result <= after
