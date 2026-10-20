"""Boundary tests for window.py — year end, DST, this_weekend on Sunday, past dates."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.services.window import resolve


def _local_date(w, which="start"):
    """Convert a Window's UTC datetime to its local date."""
    zone = ZoneInfo(w.tz)
    utc = w.start_utc if which == "start" else w.end_utc
    return utc.astimezone(zone).date()


class TestRelativeResolution:

    def test_this_weekend_on_sunday(self, monkeypatch):
        """2026-10-18 is Sunday → this_weekend end is today."""
        monkeypatch.setenv("FAKE_NOW", "2026-10-18T10:00:00+02:00")
        facets = {"start": None, "end": None, "relative": "this_weekend", "relative_n": None}
        w = resolve(facets, "Europe/Berlin")
        assert _local_date(w, "end") == date(2026, 10, 18)

    def test_this_weekend_start_clipped(self, monkeypatch):
        """On Sunday, start clipped to now (Saturday is past)."""
        monkeypatch.setenv("FAKE_NOW", "2026-10-18T12:00:00+02:00")
        facets = {"start": None, "end": None, "relative": "this_weekend", "relative_n": None}
        w = resolve(facets, "Europe/Berlin")
        assert w.tz == "Europe/Berlin"
        assert _local_date(w, "end") == date(2026, 10, 18)

    def test_next_week(self, monkeypatch):
        monkeypatch.setenv("FAKE_NOW", "2026-10-18T12:00:00+02:00")
        facets = {"start": None, "end": None, "relative": "next_week", "relative_n": None}
        w = resolve(facets, "Europe/Berlin")
        # Next week Mon 2026-10-19 → Sun 2026-10-25
        assert _local_date(w, "start") == date(2026, 10, 19)
        assert _local_date(w, "end") == date(2026, 10, 25)

    def test_default_30_days(self, monkeypatch):
        monkeypatch.setenv("FAKE_NOW", "2026-10-18T12:00:00+02:00")
        facets = {"start": None, "end": None, "relative": None, "relative_n": None}
        w = resolve(facets, "Europe/Berlin")
        assert _local_date(w, "end") == date(2026, 11, 17)

    def test_next_n_days(self, monkeypatch):
        monkeypatch.setenv("FAKE_NOW", "2026-10-18T12:00:00+02:00")
        facets = {"start": None, "end": None, "relative": "next_n_days", "relative_n": 10}
        w = resolve(facets, "Europe/Berlin")
        assert _local_date(w, "end") == date(2026, 10, 28)


class TestAbsoluteWins:

    def test_absolute_wins_over_relative(self, monkeypatch):
        monkeypatch.setenv("FAKE_NOW", "2026-10-18T12:00:00+02:00")
        facets = {
            "start": "2026-10-19",
            "end": "2026-10-21",
            "relative": "next_week",
            "relative_n": None,
        }
        w = resolve(facets, "Europe/Berlin")
        assert _local_date(w, "start") == date(2026, 10, 19)
        assert _local_date(w, "end") == date(2026, 10, 21)


class TestPastDatesReturnWindow:
    """Past absolute dates no longer raise; they return a window where
    start is clipped to now (so start > end), and filters handle the rest."""

    def test_c1_after_oct_22_returns_window(self, monkeypatch):
        """C1 criteria (19-21 Oct) run on Oct 22 → valid window, start > end."""
        monkeypatch.setenv("FAKE_NOW", "2026-10-22T12:00:00+02:00")
        facets = {
            "start": "2026-10-19",
            "end": "2026-10-21",
            "relative": "next_week",
            "relative_n": None,
        }
        w = resolve(facets, "Europe/Berlin")
        # start clipped to now, end stays Oct 21 → start > end
        assert w.start_utc > w.end_utc

    def test_both_dates_past_returns_window(self, monkeypatch):
        monkeypatch.setenv("FAKE_NOW", "2027-01-01T12:00:00+00:00")
        facets = {
            "start": "2026-10-19",
            "end": "2026-10-21",
            "relative": None,
            "relative_n": None,
        }
        w = resolve(facets, "UTC")
        assert w.start_utc > w.end_utc


class TestYearEnd:

    def test_next_month_december(self, monkeypatch):
        monkeypatch.setenv("FAKE_NOW", "2026-12-15T12:00:00+01:00")
        facets = {"start": None, "end": None, "relative": "next_month", "relative_n": None}
        w = resolve(facets, "Europe/Berlin")
        start_local = _local_date(w, "start")
        assert start_local.year == 2027
        assert start_local.month == 1


class TestDST:

    def test_dst_change_berlin(self, monkeypatch):
        """Window spanning DST change resolves without error."""
        monkeypatch.setenv("FAKE_NOW", "2026-10-24T12:00:00+02:00")
        facets = {"start": None, "end": None, "relative": "this_week", "relative_n": None}
        w = resolve(facets, "Europe/Berlin")
        assert w.end_utc is not None
        # Week ends Sunday Oct 25 (DST change day)
        assert _local_date(w, "end") == date(2026, 10, 25)


class TestStartClip:

    def test_this_month_clips_start(self, monkeypatch):
        monkeypatch.setenv("FAKE_NOW", "2026-10-18T12:00:00+02:00")
        facets = {"start": None, "end": None, "relative": "this_month", "relative_n": None}
        w = resolve(facets, "Europe/Berlin")
        start_local = _local_date(w, "start")
        assert start_local.day >= 18
