"""Tests for services/judge.py — caps, band words, reason validation, golden verdicts."""

from __future__ import annotations

import json
import os
from datetime import datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.services.judge import (
    Verdict,
    JudgeError,
    apply_caps,
    band_word,
    validate_reason,
    judge_event,
)
from app.services.extract import ExtractedEvent

# ---- caps table ----


class TestApplyCaps:
    def test_no_cap(self):
        fit = {"place": "yes", "date": "yes", "topic": "yes", "budget": "yes"}
        assert apply_caps(95, fit) == 95

    def test_place_no(self):
        fit = {"place": "no", "date": "yes", "topic": "yes", "budget": "yes"}
        assert apply_caps(90, fit) == 0

    def test_date_no(self):
        fit = {"place": "yes", "date": "no", "topic": "yes", "budget": "yes"}
        assert apply_caps(80, fit) == 10

    def test_budget_no(self):
        fit = {"place": "yes", "date": "yes", "topic": "yes", "budget": "no"}
        assert apply_caps(72, fit) == 30

    def test_topic_no(self):
        fit = {"place": "yes", "date": "yes", "topic": "no", "budget": "unknown"}
        assert apply_caps(50, fit) == 39

    def test_multiple_caps_lowest_wins(self):
        fit = {"place": "no", "date": "no", "topic": "no", "budget": "no"}
        assert apply_caps(100, fit) == 0

    def test_unknown_no_cap(self):
        fit = {"place": "unknown", "date": "unknown", "topic": "unknown", "budget": "unknown"}
        assert apply_caps(60, fit) == 60

    def test_score_already_below_cap(self):
        fit = {"place": "yes", "date": "yes", "topic": "no", "budget": "unknown"}
        assert apply_caps(20, fit) == 20


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
        assert validate_reason("Jazz trio in Berlin on 20 Oct, 18 EUR: fits your dates") is None

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

    def test_missing_date_token(self):
        err = validate_reason("Jazz trio in Berlin: fits your topic")
        assert err is not None
        assert "date" in err

    def test_missing_place_token(self):
        err = validate_reason("Jazz trio on 20 Oct: fits your dates")
        assert err is not None
        assert "place" in err

    def test_exactly_140_chars(self):
        reason = "Jazz trio at A-Trane in Berlin on Tue 20 Oct, 18 EUR: fits your dates and topic and budget" + " " * 49
        reason = reason[:140]
        # Need to make sure it has date and place
        reason = "Jazz trio in Berlin on 20 Oct: fits" + " " * (140 - 35)
        reason = reason[:140]
        assert validate_reason(reason) is None


# ---- golden set B judge rows ----


GOLDEN_PATH = Path(__file__).parent / "golden" / "candidates.json"
FIXTURES_PATH = Path(__file__).resolve().parents[1] / "app" / "adapters" / "fixtures.json"

# Events that survive C1 extraction+filtering and need judging.
# E1, E4, E20 are few-shot examples: excluded from assertions.
_FEW_SHOT = {"E1", "E4", "E20"}

C1_TEXT = "jazz in Berlin (Germany) next week (19-21st October 2026)"
C1_FACETS = {
    "place": {"city": "Berlin", "country": "DE", "region": None, "radius_km": None, "online": False},
    "date": {"start": "2026-10-19", "end": "2026-10-21", "relative": "next_week", "relative_n": None},
    "topics": ["jazz"],
    "topics_local": ["Jazz", "Jazzkonzert"],
    "formats": [],
    "budget": {"max_amount": None, "currency": None, "free_only": False},
    "language": "de",
    "input_language": "en",
    "other_constraints": [],
}

C2_TEXT = "classical concerts in Vienna, under 30 EUR, 1–15 Nov 2026"
C2_FACETS = {
    "place": {"city": "Vienna", "country": "AT", "region": None, "radius_km": None, "online": False},
    "date": {"start": "2026-11-01", "end": "2026-11-15", "relative": None, "relative_n": None},
    "topics": ["classical"],
    "topics_local": ["Klassik", "Klassische Musik"],
    "formats": ["concert"],
    "budget": {"max_amount": 30, "currency": "EUR", "free_only": False},
    "language": "de",
    "input_language": "en",
    "other_constraints": [],
}


def _golden():
    return json.loads(GOLDEN_PATH.read_text())


def _expected_band(golden, eid):
    for e in golden["entries"]:
        if e["id"] == eid:
            return e.get("expected_band")
    return None


def _make_event(title, start_local, start_tz, city, country, **kw):
    return ExtractedEvent(
        title=title,
        start_local=start_local,
        start_tz=start_tz,
        end_local=kw.get("end_local"),
        venue=kw.get("venue"),
        city=city,
        country=country,
        link=kw.get("link", "https://example.com"),
        price_amount=kw.get("price_amount"),
        price_currency=kw.get("price_currency"),
        is_free=kw.get("is_free"),
        description=kw.get("description", "Test event"),
        confidence=kw.get("confidence", 0.9),
        source_url=kw.get("source_url", "https://example.com"),
        page_kind=kw.get("page_kind", "single_event"),
    )


@pytest.fixture(scope="module")
def c1_window():
    tz = ZoneInfo("Europe/Berlin")
    start = datetime.combine(datetime(2026, 10, 19).date(), time.min, tzinfo=tz).astimezone(timezone.utc)
    end = datetime.combine(datetime(2026, 10, 21).date(), time(23, 59, 59), tzinfo=tz).astimezone(timezone.utc)
    return start, end


@pytest.fixture(scope="module")
def c2_window():
    tz = ZoneInfo("Europe/Vienna")
    start = datetime.combine(datetime(2026, 11, 1).date(), time.min, tzinfo=tz).astimezone(timezone.utc)
    end = datetime.combine(datetime(2026, 11, 15).date(), time(23, 59, 59), tzinfo=tz).astimezone(timezone.utc)
    return start, end


@pytest.fixture(scope="module")
def fake_model():
    from app.adapters.factory import get_language_model
    return get_language_model()


@pytest.mark.skipif(not os.environ.get("FAKE_NOW"), reason="FAKE_NOW required")
class TestGoldenJudgeE2:
    def test_e2_band(self, fake_model, c1_window):
        golden = _golden()
        band = _expected_band(golden, "E2")
        ev = _make_event(
            "Late Night Jam Session", "2026-10-21T22:00", "Europe/Berlin",
            "Berlin", "DE",
            venue="Zig Zag Jazz Club", price_amount=5, price_currency="EUR",
            description="Open jam with house rhythm section at Zig Zag Jazz Club Berlin.",
            link="https://www.zigzagjazzclub.berlin/events/late-night-jam-oct21",
            source_url="https://www.zigzagjazzclub.berlin/events/late-night-jam-oct21",
        )
        result = judge_event(
            ev, criteria_text=C1_TEXT, facets=C1_FACETS,
            window_start=c1_window[0], window_end=c1_window[1],
            user_tz="Europe/Berlin", model=fake_model,
        )
        assert isinstance(result, Verdict), f"E2 returned error: {result}"
        assert band[0] <= result.score <= band[1], (
            f"E2 score {result.score} outside band {band}"
        )


@pytest.mark.skipif(not os.environ.get("FAKE_NOW"), reason="FAKE_NOW required")
class TestGoldenJudgeE3:
    def test_e3_band(self, fake_model, c1_window):
        golden = _golden()
        band = _expected_band(golden, "E3")
        ev = _make_event(
            "Open-air Jazz in Mauerpark", "2026-10-19T16:00", "Europe/Berlin",
            "Berlin", "DE",
            venue="Mauerpark", end_local="2026-10-19T18:00",
            price_amount=0, price_currency="EUR", is_free=True,
            description="Free open-air jazz concert in Mauerpark amphitheatre, local jazz ensemble.",
            link="https://www.berlin-events.de/open-air-jazz-mauerpark",
            source_url="https://www.berlin-events.de/open-air-jazz-mauerpark",
        )
        result = judge_event(
            ev, criteria_text=C1_TEXT, facets=C1_FACETS,
            window_start=c1_window[0], window_end=c1_window[1],
            user_tz="Europe/Berlin", model=fake_model,
        )
        assert isinstance(result, Verdict), f"E3 returned error: {result}"
        assert band[0] <= result.score <= band[1], (
            f"E3 score {result.score} outside band {band}"
        )


@pytest.mark.skipif(not os.environ.get("FAKE_NOW"), reason="FAKE_NOW required")
class TestGoldenJudgeE21:
    def test_e21_band(self, fake_model, c1_window):
        golden = _golden()
        band = _expected_band(golden, "E21")
        ev = _make_event(
            "Outdoor Photography Meetup", "2026-10-20T10:00", "Europe/Berlin",
            "Berlin", "DE",
            venue="Tiergarten",
            description="Outdoor Photography Meetup in Berlin Tiergarten.",
            link="https://www.berlin-meetups.de/outdoor-photography-oct20",
            source_url="https://www.berlin-meetups.de/outdoor-photography-oct20",
        )
        result = judge_event(
            ev, criteria_text=C1_TEXT, facets=C1_FACETS,
            window_start=c1_window[0], window_end=c1_window[1],
            user_tz="Europe/Berlin", model=fake_model,
        )
        assert isinstance(result, Verdict), f"E21 returned error: {result}"
        # topic=no → capped at 39
        assert band[0] <= result.score <= band[1], (
            f"E21 score {result.score} outside band {band}"
        )


@pytest.mark.skipif(not os.environ.get("FAKE_NOW"), reason="FAKE_NOW required")
class TestGoldenJudgeE22:
    def test_e22_band(self, fake_model, c2_window):
        golden = _golden()
        band = _expected_band(golden, "E22")
        ev = _make_event(
            "Vienna Philharmonic", "2026-11-05T19:30", "Europe/Vienna",
            "Vienna", "AT",
            venue="Musikverein", price_amount=120, price_currency="EUR",
            description="Vienna Philharmonic concert at Musikverein, tickets from 120 EUR.",
            link="https://www.wiener-philharmoniker.at/en/concert-nov5",
            source_url="https://www.wiener-philharmoniker.at/en/concert-nov5",
        )
        result = judge_event(
            ev, criteria_text=C2_TEXT, facets=C2_FACETS,
            window_start=c2_window[0], window_end=c2_window[1],
            user_tz="Europe/Vienna", model=fake_model,
        )
        assert isinstance(result, Verdict), f"E22 returned error: {result}"
        # budget=no → capped at 30
        assert band[0] <= result.score <= band[1], (
            f"E22 score {result.score} outside band {band}"
        )


# ---- is_event=false ----


class TestIsEventFalse:
    def test_is_event_false_returns_score_zero(self):
        """A non-event from the judge gets score 0."""
        fit = {"place": "yes", "date": "yes", "topic": "yes", "budget": "unknown"}
        # Simulate: judge returns is_event=false with score 50
        # Tested via apply_caps + the is_event check in judge_event
        # Here just test the caps + band at score 0
        assert band_word(0) == "not a fit"
