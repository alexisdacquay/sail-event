"""Tests for services/judge.py — band words, reason validation."""

from __future__ import annotations

import pytest

from app.services.judge import (
    band_word,
    validate_reason,
)


# ---- band words ----


class TestBandWord:
    def test_fits(self):
        assert band_word(90) == "fits"
        assert band_word(100) == "fits"
        assert band_word(95) == "fits"

    def test_mostly_fits(self):
        assert band_word(70) == "mostly fits"
        assert band_word(89) == "mostly fits"

    def test_open_question(self):
        assert band_word(40) == "open question"
        assert band_word(69) == "open question"

    def test_off_topic(self):
        assert band_word(10) == "off topic"
        assert band_word(39) == "off topic"

    def test_not_a_fit(self):
        assert band_word(0) == "not a fit"
        assert band_word(9) == "not a fit"


# ---- reason validation ----


class TestValidateReason:
    def test_valid_reason(self):
        assert validate_reason("Jazz trio in Berlin on 20 Oct: fits your dates") is None

    def test_too_long(self):
        err = validate_reason("x" * 141)
        assert err is not None
        assert "too long" in err

    def test_contains_url(self):
        err = validate_reason("Jazz in Berlin on 20 Oct https://example.com: fits")
        assert err is not None
        assert "URL" in err

    def test_contains_markup(self):
        err = validate_reason("Jazz in Berlin on 20 Oct <b>fits</b> your dates")
        assert err is not None
        assert "markup" in err

    def test_exactly_140_chars(self):
        reason = "Jazz trio in Berlin on 20 Oct: fits" + " " * (140 - 35)
        reason = reason[:140]
        assert validate_reason(reason) is None


# ---- is_event=false ----


class TestIsEventFalse:
    def test_is_event_false_returns_not_a_fit(self):
        assert band_word(0) == "not a fit"
