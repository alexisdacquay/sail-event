"""Tests for the query planner — C1, C4 verbatim expectations, rotation, no-place."""

from __future__ import annotations

from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

import pytest

from app.services.planner import plan, PlannedQuery
from app.services.window import Window


def _window(start_date, end_date, tz="Europe/Berlin"):
    """Build a Window from date strings."""
    zone = ZoneInfo(tz)
    s = datetime.combine(start_date, time.min, tzinfo=zone).astimezone(timezone.utc)
    e = datetime.combine(end_date, time(23, 59, 59), tzinfo=zone).astimezone(timezone.utc)
    return Window(start_utc=s, end_utc=e, tz=tz)


def _texts(queries):
    return [q.text for q in queries]


# ---------- C1: jazz in Berlin, 19-21 Oct 2026, language de ----------

class TestC1:
    @pytest.fixture()
    def facets(self):
        return {
            "place": {"city": "Berlin", "country": "DE", "region": None,
                      "radius_km": None, "online": False},
            "date": {"start": "2026-10-19", "end": "2026-10-21",
                     "relative": "next_week", "relative_n": None},
            "topics": ["jazz"],
            "topics_local": ["Jazz"],
            "formats": [],
            "budget": {"max_amount": None, "currency": None, "free_only": False},
            "language": "de",
            "input_language": "en",
        }

    @pytest.fixture()
    def window(self):
        from datetime import date
        return _window(date(2026, 10, 19), date(2026, 10, 21), "Europe/Berlin")

    def test_c1_plan_texts(self, facets, window):
        queries = plan(facets, window, max_queries=6, offset=0)
        expected = [
            "jazz Berlin October 2026",
            "Jazz Berlin Oktober 2026",
            "jazz concert Berlin 19–21 October 2026",
            "Berlin Veranstaltungen Jazz 19.–21. Oktober 2026",
            "jazz Berlin tickets October 2026",
            "jazz Berlin programme this week",
        ]
        assert _texts(queries) == expected

    def test_c1_country_and_language(self, facets, window):
        queries = plan(facets, window, max_queries=6, offset=0)
        # All queries carry country DE.
        for q in queries:
            assert q.country == "DE"
        # English queries have language None; local queries have "de".
        assert queries[0].language is None   # template 1 (en)
        assert queries[1].language == "de"   # template 2 (local)
        assert queries[2].language is None   # template 3 (en)
        assert queries[3].language == "de"   # template 4 (local)
        assert queries[4].language is None   # template 5 (en)
        assert queries[5].language is None   # template 6 (en)


# ---------- C4: Lisbon this weekend, no topics, language pt ----------

class TestC4:
    @pytest.fixture()
    def facets(self):
        return {
            "place": {"city": "Lisbon", "country": "PT", "region": None,
                      "radius_km": None, "online": False},
            "date": {"start": None, "end": None,
                     "relative": "this_weekend", "relative_n": None},
            "topics": [],
            "topics_local": [],
            "formats": [],
            "budget": {"max_amount": None, "currency": None, "free_only": False},
            "language": "pt",
            "input_language": "en",
        }

    @pytest.fixture()
    def window(self):
        from datetime import date
        return _window(date(2026, 10, 24), date(2026, 10, 25), "Europe/Lisbon")

    def test_c4_plan_texts(self, facets, window):
        queries = plan(facets, window, max_queries=6, offset=0)
        expected = [
            "events Lisbon October 2026",
            "eventos Lisboa Outubro 2026",
            "events Lisbon 24–25 October 2026",
            "Lisboa eventos 24–25 outubro 2026",
            "events Lisbon tickets October 2026",
            "events Lisbon programme this week",
        ]
        assert _texts(queries) == expected


# ---------- C3: no place, not online → empty plan ----------

class TestNoPlace:
    def test_no_place_empty(self):
        facets = {
            "place": None,
            "topics": [],
            "topics_local": [],
            "formats": [],
            "language": None,
        }
        window = _window(
            __import__("datetime").date(2026, 10, 24),
            __import__("datetime").date(2026, 10, 25),
        )
        assert plan(facets, window) == []

    def test_no_city_not_online_empty(self):
        facets = {
            "place": {"city": None, "country": None, "online": False},
            "topics": ["jazz"],
            "topics_local": [],
            "formats": [],
            "language": None,
        }
        window = _window(
            __import__("datetime").date(2026, 10, 19),
            __import__("datetime").date(2026, 10, 21),
        )
        assert plan(facets, window) == []


# ---------- Rotation: offset cycles through the plan ----------

class TestRotation:
    @pytest.fixture()
    def facets(self):
        return {
            "place": {"city": "Berlin", "country": "DE", "region": None,
                      "radius_km": None, "online": False},
            "topics": ["jazz"],
            "topics_local": ["Jazz"],
            "formats": [],
            "language": "de",
        }

    @pytest.fixture()
    def window(self):
        from datetime import date
        return _window(date(2026, 10, 19), date(2026, 10, 21), "Europe/Berlin")

    def test_three_runs_cover_full_plan(self, facets, window):
        """Three consecutive scheduled runs (max_queries=2) cover all 6 queries."""
        full = plan(facets, window, max_queries=6, offset=0)
        assert len(full) == 6

        covered: set[str] = set()
        for run_idx in range(3):
            batch = plan(facets, window, max_queries=2, offset=run_idx * 2)
            assert len(batch) == 2
            for q in batch:
                covered.add(q.text)

        # All 6 queries were issued across three runs.
        assert covered == {q.text for q in full}

    def test_offset_rotates_start(self, facets, window):
        """offset=2 starts at the third query."""
        batch0 = plan(facets, window, max_queries=2, offset=0)
        batch1 = plan(facets, window, max_queries=2, offset=2)
        assert batch0[0].text != batch1[0].text
        # batch1 starts where batch0 left off.
        full = plan(facets, window, max_queries=6, offset=0)
        assert batch1[0].text == full[2].text


# ---------- Online without city → template 7 ----------

class TestOnline:
    def test_online_no_city(self):
        facets = {
            "place": {"city": None, "country": None, "online": True},
            "topics": ["Rust"],
            "topics_local": [],
            "formats": ["webinar"],
            "language": None,
        }
        window = _window(
            __import__("datetime").date(2026, 11, 1),
            __import__("datetime").date(2026, 11, 30),
        )
        queries = plan(facets, window, max_queries=6, offset=0)
        texts = _texts(queries)
        assert "Rust online November 2026" in texts
