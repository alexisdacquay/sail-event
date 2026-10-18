"""Tests for services/filters.py — canonical URL, near-match, filter pipeline."""

from __future__ import annotations

from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

import pytest

from app.adapters.search_v2 import canonical_url
from app.services.extract import ExtractedEvent
from app.services.filters import (
    FilterCounts,
    filter_events,
    is_near_match,
    jaccard,
    title_key,
)


# ---------- canonical URL ----------


class TestCanonicalUrl:
    def test_utm_params_stripped(self):
        assert canonical_url(
            "https://example.com/event?utm_source=x&utm_medium=y&id=123"
        ) == "https://example.com/event?id=123"

    def test_fragment_stripped(self):
        assert canonical_url(
            "https://example.com/event#section"
        ) == "https://example.com/event"

    def test_trailing_slash_stripped(self):
        assert canonical_url(
            "https://example.com/event/"
        ) == "https://example.com/event"

    def test_default_port_stripped_http(self):
        assert canonical_url(
            "http://example.com:80/event"
        ) == "http://example.com/event"

    def test_default_port_stripped_https(self):
        assert canonical_url(
            "https://example.com:443/event"
        ) == "https://example.com/event"

    def test_nondefault_port_kept(self):
        assert canonical_url(
            "https://example.com:8080/event"
        ) == "https://example.com:8080/event"

    def test_scheme_and_host_lowered(self):
        assert canonical_url(
            "HTTPS://Example.COM/Event"
        ) == "https://example.com/Event"

    def test_fbclid_stripped(self):
        assert canonical_url(
            "https://example.com/page?fbclid=abc123"
        ) == "https://example.com/page"

    def test_gclid_stripped(self):
        assert canonical_url(
            "https://example.com/page?gclid=abc&keep=1"
        ) == "https://example.com/page?keep=1"

    def test_ref_and_source_stripped(self):
        assert canonical_url(
            "https://example.com/page?ref=twitter&source=social"
        ) == "https://example.com/page"

    def test_all_params_stripped_leaves_no_query(self):
        url = "https://example.com/page?utm_source=x&fbclid=y"
        assert canonical_url(url) == "https://example.com/page"


# ---------- title key ----------


class TestTitleKey:
    def test_basic(self):
        assert title_key("Jazz Trio at A-Trane") == frozenset({"jazz", "trio", "atrane"})

    def test_stopwords_removed(self):
        assert title_key("The Jazz Concert in Berlin") == frozenset({"jazz", "concert", "berlin"})

    def test_punctuation_removed(self):
        assert title_key("A-Trane: Jazz Trio!") == frozenset({"atrane", "jazz", "trio"})

    def test_german_stopwords(self):
        assert title_key("Jazz im Tiergarten") == frozenset({"jazz", "tiergarten"})


# ---------- near-match ----------


class TestNearMatch:
    def test_e19_matches_e1(self):
        """E19 'A-Trane: Jazz Trio' matches E1 'Jazz Trio at A-Trane'."""
        k1 = title_key("Jazz Trio at A-Trane")  # {jazz, trio, atrane}
        k19 = title_key("A-Trane: Jazz Trio")   # {atrane, jazz, trio}
        assert is_near_match(k1, k19)

    def test_atrane_jazz_vs_atrane_jazz_trio_no_match(self):
        """'A-Trane Jazz' vs 'A-Trane Jazz Trio' same night — no match (Jaccard 2/3)."""
        ka = title_key("A-Trane Jazz")       # {atrane, jazz}
        kb = title_key("A-Trane Jazz Trio")  # {atrane, jazz, trio}
        j = jaccard(ka, kb)
        assert j == pytest.approx(2 / 3, abs=0.01)
        assert not is_near_match(ka, kb)

    def test_jazz_vs_jazz_trio_atrane_no_match(self):
        """{jazz} vs {jazz, trio, atrane} — subset but < 3 tokens, no match."""
        ka = frozenset({"jazz"})
        kb = frozenset({"jazz", "trio", "atrane"})
        # {jazz} ⊂ {jazz, trio, atrane} but len({jazz}) = 1 < 3
        assert ka <= kb
        assert not is_near_match(ka, kb)

    def test_subset_with_3_tokens_matches(self):
        """{jazz, trio, berlin} ⊂ {jazz, trio, berlin, concert} — match (subset with ≥ 3)."""
        ka = frozenset({"jazz", "trio", "berlin"})
        kb = frozenset({"jazz", "trio", "berlin", "concert"})
        assert is_near_match(ka, kb)

    def test_different_events_no_match(self):
        k1 = title_key("Jazz Trio at A-Trane")
        k2 = title_key("Techno Night at Berghain")
        assert not is_near_match(k1, k2)


# ---------- filter pipeline ----------

def _make_event(**kwargs) -> ExtractedEvent:
    defaults = dict(
        title="Test Event",
        start_local="2026-10-20T20:00",
        start_tz="Europe/Berlin",
        end_local=None,
        venue=None,
        city="Berlin",
        country="DE",
        link="https://example.com/event",
        price_amount=None,
        price_currency=None,
        is_free=None,
        description="A test event.",
        confidence=0.9,
        source_url="https://example.com/event",
        page_kind="single_event",
    )
    defaults.update(kwargs)
    return ExtractedEvent(**defaults)


# Window: 2026-10-19 00:00 → 2026-10-21 23:59:59 Europe/Berlin
_TZ = ZoneInfo("Europe/Berlin")
_NOW = datetime(2026, 10, 18, 12, 0, 0, tzinfo=_TZ).astimezone(timezone.utc)
_WS = datetime.combine(datetime(2026, 10, 19).date(), time.min, tzinfo=_TZ).astimezone(timezone.utc)
_WE = datetime.combine(datetime(2026, 10, 21).date(), time(23, 59, 59), tzinfo=_TZ).astimezone(timezone.utc)


def _filter_one(ev, **kwargs):
    defaults = dict(
        now_utc=_NOW,
        window_start_utc=_WS,
        window_end_utc=_WE,
        target_city="Berlin",
        target_country="DE",
        user_tz="Europe/Berlin",
    )
    defaults.update(kwargs)
    return filter_events([ev], **defaults)


class TestFilterPipeline:
    def test_passing_event(self):
        ev = _make_event()
        kept, counts = _filter_one(ev)
        assert len(kept) == 1
        assert counts.filtered_past == 0

    def test_past_event_filtered(self):
        ev = _make_event(start_local="2026-10-10T15:00")
        kept, counts = _filter_one(ev)
        assert len(kept) == 0
        assert counts.filtered_past == 1

    def test_past_date_only_2359_rule(self):
        """Date-only event on Oct 17 (yesterday): ends at 23:59:59, before now (Oct 18 12:00)."""
        ev = _make_event(start_local="2026-10-17")
        kept, counts = _filter_one(ev)
        assert len(kept) == 0
        assert counts.filtered_past == 1

    def test_date_only_today_kept(self):
        """Date-only event on Oct 18 (today): ends at 23:59:59, after now (12:00)."""
        ev = _make_event(start_local="2026-10-18")
        # This event is today, not in the window (19-21), so filtered_date
        kept, counts = _filter_one(ev)
        assert len(kept) == 0
        assert counts.filtered_date == 1

    def test_window_overlap_festival(self):
        """Festival 17-22 Oct overlaps 19-21 Oct window."""
        ev = _make_event(
            start_local="2026-10-17",
            end_local="2026-10-22",
        )
        kept, counts = _filter_one(ev)
        assert len(kept) == 1

    def test_outside_window_filtered(self):
        ev = _make_event(start_local="2026-11-05T20:00")
        kept, counts = _filter_one(ev)
        assert len(kept) == 0
        assert counts.filtered_date == 1

    def test_wrong_country_filtered(self):
        ev = _make_event(city="Chicago", country="US", start_tz="America/Chicago")
        kept, counts = _filter_one(ev)
        assert len(kept) == 0
        assert counts.filtered_place == 1

    def test_wrong_city_same_country_filtered(self):
        ev = _make_event(city="Potsdam")
        kept, counts = _filter_one(ev)
        assert len(kept) == 0
        assert counts.filtered_place == 1

    def test_unknown_country_filtered(self):
        ev = _make_event(country="ZZ")
        kept, counts = _filter_one(ev)
        assert len(kept) == 0
        assert counts.filtered_place == 1

    def test_null_country_filtered(self):
        ev = _make_event(country=None)
        kept, counts = _filter_one(ev)
        assert len(kept) == 0
        assert counts.filtered_incomplete == 1  # country is required

    def test_incomplete_missing_start_tz(self):
        ev = _make_event(start_tz=None)
        kept, counts = _filter_one(ev)
        assert len(kept) == 0
        assert counts.filtered_incomplete == 1

    def test_incomplete_missing_description(self):
        ev = _make_event(description="")
        kept, counts = _filter_one(ev)
        assert len(kept) == 0
        assert counts.filtered_incomplete == 1

    def test_incomplete_missing_city(self):
        ev = _make_event(city=None)
        kept, counts = _filter_one(ev)
        assert len(kept) == 0
        assert counts.filtered_incomplete == 1

    def test_duplicate_link_filtered(self):
        ev1 = _make_event(link="https://example.com/event1", title="Event 1")
        ev2 = _make_event(link="https://example.com/event1", title="Event 2")
        kept, counts = filter_events(
            [ev1, ev2],
            now_utc=_NOW,
            window_start_utc=_WS,
            window_end_utc=_WE,
            target_city="Berlin",
            target_country="DE",
            user_tz="Europe/Berlin",
        )
        assert len(kept) == 1
        assert counts.filtered_duplicate == 1

    def test_duplicate_utm_link_filtered(self):
        ev1 = _make_event(link="https://example.com/event1")
        ev2 = _make_event(link="https://example.com/event1?utm_source=x")
        kept, counts = filter_events(
            [ev1, ev2],
            now_utc=_NOW,
            window_start_utc=_WS,
            window_end_utc=_WE,
            target_city="Berlin",
            target_country="DE",
            user_tz="Europe/Berlin",
        )
        assert len(kept) == 1
        assert counts.filtered_duplicate == 1

    def test_near_match_stored_rejected_dropped(self):
        """A near-match of a rejected stored event is dropped."""
        ev = _make_event(title="Jazz Trio at A-Trane")
        stored = [
            {"link": "https://other.com/atrane", "date_time": "2026-10-20T21:00",
             "title": "A-Trane: Jazz Trio", "status": "rejected", "page_kind": "single_event"},
        ]
        kept, counts = filter_events(
            [ev],
            now_utc=_NOW,
            window_start_utc=_WS,
            window_end_utc=_WE,
            target_city="Berlin",
            target_country="DE",
            user_tz="Europe/Berlin",
            stored_events=stored,
        )
        assert len(kept) == 0
        assert counts.filtered_duplicate == 1

    def test_listing_stored_occurrences_deduped_new_kept(self):
        """A listing page's stored occurrences are deduped, new ones kept."""
        # Stored: one occurrence from a previous run
        stored = [
            {"link": "https://venue.com/programme", "date_time": "2026-10-19T21:00",
             "title": "Jazz Monday", "status": "accepted", "page_kind": "listing"},
        ]
        # Run 2: same occurrence + a new one
        ev_old = _make_event(
            title="Jazz Monday",
            start_local="2026-10-19T21:00",
            link="https://venue.com/programme",
        )
        ev_new = _make_event(
            title="Jazz Tuesday",
            start_local="2026-10-20T21:00",
            link="https://venue.com/programme",
        )
        kept, counts = filter_events(
            [ev_old, ev_new],
            now_utc=_NOW,
            window_start_utc=_WS,
            window_end_utc=_WE,
            target_city="Berlin",
            target_country="DE",
            user_tz="Europe/Berlin",
            stored_events=stored,
        )
        # ev_old is a duplicate (same link + date), ev_new is new
        assert len(kept) == 1
        assert kept[0].title == "Jazz Tuesday"
        assert counts.filtered_duplicate == 1
