"""Tests for services/filters.py — canonical URL, filter pipeline."""

from __future__ import annotations

from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

import pytest

from app.adapters.search import canonical_url
from app.services.extract import ExtractedEvent
from app.services.filters import (
    FilterCounts,
    filter_events,
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

    def test_past_date_only_filtered_no_time(self):
        """Date-only event on Oct 17: #134 drops it as filtered_no_time before the past check."""
        ev = _make_event(start_local="2026-10-17")
        kept, counts = _filter_one(ev)
        assert len(kept) == 0
        assert counts.filtered_no_time == 1

    def test_date_only_today_filtered_no_time(self):
        """Date-only event on Oct 18: #134 drops it as filtered_no_time (no time component)."""
        ev = _make_event(start_local="2026-10-18")
        kept, counts = _filter_one(ev)
        assert len(kept) == 0
        assert counts.filtered_no_time == 1

    def test_outside_window_not_filtered(self):
        """Date-window filter removed; events outside the window are kept for the judge."""
        ev = _make_event(start_local="2026-11-05T20:00")
        kept, counts = _filter_one(ev)
        assert len(kept) == 1

    def test_wrong_country_not_filtered(self):
        """Place filter removed; wrong-country events are kept for the judge."""
        ev = _make_event(city="Chicago", country="US", start_tz="America/Chicago")
        kept, counts = _filter_one(ev)
        assert len(kept) == 1

    def test_null_country_filtered_incomplete(self):
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

    def test_no_start_date_counted_no_date(self):
        """#112: a missing start is filtered_no_date, not incomplete and never a page count."""
        ev = _make_event(start_local="")
        kept, counts = _filter_one(ev)
        assert len(kept) == 0
        assert counts.filtered_no_date == 1
        assert counts.filtered_incomplete == 0
        assert not hasattr(counts, "filtered_non_event")

    def test_same_link_and_start_both_kept(self):
        """Owner 2026-10-25: two events may share a link and start minute; the after-storage check decides."""
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
        assert kept == [ev1, ev2]
        assert counts.filtered_duplicate == 0

    def test_in_run_utm_link_variant_kept(self):
        """#136: no in-run link check; the after-storage check compares them."""
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
        assert len(kept) == 2
        assert counts.filtered_duplicate == 0

    def test_title_match_of_stored_event_kept(self):
        """#136: no title match against stored events; the after-storage check compares them."""
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
        assert len(kept) == 1
        assert counts.filtered_duplicate == 0

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


# ---------- #136: owner's London AI search ----------

_LISTING = "https://hiddenevents.online/london/tech-events"


def test_136_two_listing_events_same_date_both_kept():
    """#136 evidence: two different talks on one listing page, same day, link = listing URL; both are kept."""
    movie = _make_event(
        title="AI Movie Club x The Terminator (1984)", start_local="2026-10-29T18:00",
        start_tz="Europe/London", city="London", country="GB", venue="Kensington Central Library",
        link=_LISTING, source_url=_LISTING, page_kind="listing",
    )
    debate = _make_event(
        title="Is AI making us less creative?: An Oxford-style debate", start_local="2026-10-29T18:30",
        start_tz="Europe/London", city="London", country="GB", venue="Granola",
        link=_LISTING, source_url=_LISTING, page_kind="listing",
    )
    kept, counts = filter_events(
        [movie, debate], now_utc=_NOW, window_start_utc=_WS, window_end_utc=_WE,
        target_city="London", target_country="GB", user_tz="Europe/London",
    )
    assert [e.title for e in kept] == [movie.title, debate.title]
    assert counts.filtered_duplicate == 0


def test_136_stored_event_page_same_day_is_duplicate():
    """#136: the one check, the event's own page stored for the same calendar date, at another time."""
    stored = [{"link": "https://example.com/event?utm_source=x", "date_time": "2026-10-20T18:00+02:00"}]
    kept, counts = _filter_one(_make_event(), stored_events=stored)
    assert kept == []
    assert counts.filtered_duplicate == 1


def test_136_stored_listing_url_same_day_other_event_kept():
    """#136: a listing's own URL is never an event page; a stored event from that listing does not drop another."""
    stored = [{"link": _LISTING, "date_time": "2026-10-29T18:00+00:00"}]
    debate = _make_event(
        title="Is AI making us less creative?: An Oxford-style debate", start_local="2026-10-29T18:30",
        start_tz="Europe/London", city="London", country="GB",
        link=_LISTING, source_url=_LISTING, page_kind="listing",
    )
    kept, counts = _filter_one(debate, stored_events=stored, user_tz="Europe/London")
    assert kept == [debate]
    assert counts.filtered_duplicate == 0


def test_stored_listing_url_same_minute_other_event_kept():
    """Owner 2026-10-25: a stored event with the same listing link and start minute does not drop another event."""
    stored = [{"link": _LISTING, "date_time": "2026-10-29T18:00+00:00"}]
    debate = _make_event(
        title="Is AI making us less creative?: An Oxford-style debate", start_local="2026-10-29T18:00",
        start_tz="Europe/London", city="London", country="GB",
        link=_LISTING, source_url=_LISTING, page_kind="listing",
    )
    kept, counts = _filter_one(debate, stored_events=stored, user_tz="Europe/London")
    assert kept == [debate]
    assert counts.filtered_duplicate == 0
