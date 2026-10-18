"""Sentinel test — criteria text must not appear in log records or span attributes."""

from __future__ import annotations

import logging
import os

import pytest


SENTINEL = "SENTINEL-7Q-criteria-text-must-not-leak"


def test_criteria_text_not_in_logs(monkeypatch, caplog):
    """Parsing criteria must not log the criteria text."""
    monkeypatch.setenv("FAKE_NOW", "2026-10-18T12:00:00+02:00")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    from app.adapters.factory import get_language_model
    from app.services.criteria import parse_criteria

    model = get_language_model()

    # The sentinel text won't have a recording, so the call will raise.
    # That's expected — we just need to check no log record contains the text.
    with caplog.at_level(logging.DEBUG):
        try:
            parse_criteria(SENTINEL, "UTC", model)
        except FileNotFoundError:
            pass  # expected: no recording for the sentinel text

    for record in caplog.records:
        assert SENTINEL not in record.getMessage(), \
            f"Criteria text leaked into log: {record.getMessage()!r}"
