"""Tests for extract.py — issue 124 acceptance criteria.

AC 1: listing page whose snippet has no event, raw_content has three →
      all three extracted; pages_with_events counts it; filtered_non_event
      does not.
AC 2: parallelism — 20 results with content → 20 pass-2 calls, wall time
      bounded (fake model with a sleep); counters monotonic.
AC 3: page_kind from the model's answer; known-link removal only for
      single_event pages; test for a one-event listing and a zero-event listing.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.adapters.search import SearchResult
from app.services.extract import (
    ExtractionCounts,
    extract_events,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_WINDOW_START = datetime(2026, 10, 19, tzinfo=timezone.utc)
_WINDOW_END = datetime(2026, 10, 21, 23, 59, 59, tzinfo=timezone.utc)


def _make_result(url: str, title: str = "page", snippet: str = "",
                 raw_content: str | None = None) -> SearchResult:
    return SearchResult(
        url=url,
        title=title,
        snippet=snippet,
        raw_content=raw_content,
        published_at=None,
        provider="test",
    )


class _StubModel:
    """Return a canned response for every complete_json call."""

    model_id = "test:stub"

    def __init__(self, response: dict):
        self._response = response
        self.calls: list[dict] = []

    def complete_json(self, **kwargs):
        self.calls.append(kwargs)
        return self._response, type("U", (), {"tokens_in": 0, "tokens_out": 0})()


class _SleepModel:
    """Sleeps for a fixed duration per call, records timestamps."""

    model_id = "test:sleep"

    def __init__(self, response: dict, sleep_seconds: float = 0.1):
        self._response = response
        self._sleep = sleep_seconds
        self.call_times: list[float] = []
        self._lock = threading.Lock()

    def complete_json(self, **kwargs):
        t = time.monotonic()
        time.sleep(self._sleep)
        with self._lock:
            self.call_times.append(t)
        return self._response, type("U", (), {"tokens_in": 0, "tokens_out": 0})()


# ---------------------------------------------------------------------------
# AC 1: listing page with events only in raw_content
# ---------------------------------------------------------------------------

class TestListingPageExtracted:
    """A listing page whose snippet has no event data but whose raw_content
    has three events must have all three extracted."""

    def test_listing_page_all_events_extracted(self):
        listing_url = "https://listings.example.com/london-ai"
        result = _make_result(
            url=listing_url,
            title="AI Events London",
            snippet="27 AI events in London — browse the full list",
            raw_content="<page with events>",
        )
        model = _StubModel({
            "page_kind": "listing",
            "events": [
                {"title": "AI Hack Day", "start_local": "2026-10-20T09:00",
                 "tz": "Europe/London", "city": "London", "country": "GB",
                 "link": listing_url, "description": "A hackathon",
                 "confidence": 0.9},
                {"title": "ML Workshop", "start_local": "2026-10-20T14:00",
                 "tz": "Europe/London", "city": "London", "country": "GB",
                 "link": listing_url, "description": "ML hands-on",
                 "confidence": 0.85},
                {"title": "LLM Meetup", "start_local": "2026-10-21T18:00",
                 "tz": "Europe/London", "city": "London", "country": "GB",
                 "link": listing_url, "description": "LLM talk",
                 "confidence": 0.88},
            ],
        })

        events, counts = extract_events(
            [result],
            window_start=_WINDOW_START,
            window_end=_WINDOW_END,
            target_city="London",
            target_country="GB",
            language="en",
            user_tz="Europe/London",
            model=model,
        )

        assert len(events) == 3
        assert counts.pages_with_events == 1
        assert counts.filtered_non_event == 0
        # page_kind comes from the model's answer
        for ev in events:
            assert ev.page_kind == "listing"
            assert ev.source_url == listing_url

    def test_listing_page_no_snippet_pass(self):
        """With raw_content present, the snippet-only pass is NOT used."""
        result = _make_result(
            url="https://example.com/events",
            snippet="Browse events",
            raw_content="full page text with events",
        )
        model = _StubModel({
            "page_kind": "listing",
            "events": [
                {"title": "Event One", "start_local": "2026-10-20T10:00",
                 "tz": "Europe/London", "city": "London", "country": "GB",
                 "link": "https://example.com/events",
                 "description": "Desc", "confidence": 0.9},
            ],
        })

        events, counts = extract_events(
            [result],
            window_start=_WINDOW_START,
            window_end=_WINDOW_END,
            target_city="London",
            target_country="GB",
            language=None,
            user_tz="UTC",
            model=model,
        )

        # Only one call — the full page read, no snippet call
        assert len(model.calls) == 1
        assert counts.pages_content_pass == 1


# ---------------------------------------------------------------------------
# AC 2: parallelism — 20 results, wall time bounded, counters monotonic
# ---------------------------------------------------------------------------

class TestParallelism:
    SLEEP_PER_CALL = 0.15

    def test_20_results_parallel_bounded_wall_time(self):
        """20 results with content → 20 pass-2 calls, wall time < 20 * sleep / 2."""
        results = [
            _make_result(
                url=f"https://example.com/page/{i}",
                raw_content=f"page content {i}",
            )
            for i in range(20)
        ]
        model = _SleepModel(
            {"page_kind": "single_event", "events": [
                {"title": f"Event", "start_local": "2026-10-20T10:00",
                 "tz": "UTC", "city": "X", "country": "GB",
                 "link": "https://example.com/page/0",
                 "description": "D", "confidence": 0.9},
            ]},
            sleep_seconds=self.SLEEP_PER_CALL,
        )

        # Track counter progression for monotonicity
        counter_snapshots: list[int] = []
        lock = threading.Lock()

        def _on_page_done(ec):
            with lock:
                counter_snapshots.append(ec.pages_content_pass)

        t0 = time.monotonic()
        events, counts = extract_events(
            results,
            window_start=_WINDOW_START,
            window_end=_WINDOW_END,
            target_city="X",
            target_country="GB",
            language=None,
            user_tz="UTC",
            model=model,
            on_page_done=_on_page_done,
        )
        wall = time.monotonic() - t0

        assert counts.pages_content_pass == 20
        assert len(model.call_times) == 20

        # Wall time bounded: with 5 workers, 20 calls * 0.15s each = 3s sequential.
        # Parallel should take ~0.6s. Use generous bound: < 20 * sleep / 2 = 1.5s
        max_wall = 20 * self.SLEEP_PER_CALL / 2
        assert wall < max_wall, f"wall time {wall:.2f}s exceeds {max_wall:.2f}s"

        # Counters monotonic
        for i in range(1, len(counter_snapshots)):
            assert counter_snapshots[i] >= counter_snapshots[i - 1], \
                f"pages_content_pass went from {counter_snapshots[i-1]} to {counter_snapshots[i]}"


# ---------------------------------------------------------------------------
# AC 3: page_kind from the model's answer; known-link removal for single_event only
# ---------------------------------------------------------------------------

class TestPageKindFromModel:
    """page_kind comes from the model's pass-2 answer, not inferred."""

    def test_single_event_page_kind(self):
        result = _make_result(
            url="https://venue.example.com/show",
            raw_content="Event details",
        )
        model = _StubModel({
            "page_kind": "single_event",
            "events": [
                {"title": "Solo Show", "start_local": "2026-10-20T20:00",
                 "tz": "Europe/London", "city": "London", "country": "GB",
                 "link": "https://venue.example.com/show",
                 "description": "One event", "confidence": 0.95},
            ],
        })
        events, _ = extract_events(
            [result],
            window_start=_WINDOW_START,
            window_end=_WINDOW_END,
            target_city="London",
            target_country="GB",
            language=None,
            user_tz="UTC",
            model=model,
        )
        assert len(events) == 1
        assert events[0].page_kind == "single_event"

    def test_listing_with_one_event(self):
        """A listing page that returns only one event keeps page_kind=listing."""
        result = _make_result(
            url="https://venue.example.com/programme",
            raw_content="Programme page",
        )
        model = _StubModel({
            "page_kind": "listing",
            "events": [
                {"title": "Tonight Only", "start_local": "2026-10-20T20:00",
                 "tz": "Europe/London", "city": "London", "country": "GB",
                 "link": "https://venue.example.com/programme",
                 "description": "One event from listing", "confidence": 0.9},
            ],
        })
        events, _ = extract_events(
            [result],
            window_start=_WINDOW_START,
            window_end=_WINDOW_END,
            target_city="London",
            target_country="GB",
            language=None,
            user_tz="UTC",
            model=model,
        )
        assert len(events) == 1
        assert events[0].page_kind == "listing"

    def test_not_event_listing(self):
        """A page the model marks not_event yields zero events."""
        result = _make_result(
            url="https://news.example.com/article",
            raw_content="An article about AI",
        )
        model = _StubModel({
            "page_kind": "not_event",
            "events": [],
        })
        events, counts = extract_events(
            [result],
            window_start=_WINDOW_START,
            window_end=_WINDOW_END,
            target_city="London",
            target_country="GB",
            language=None,
            user_tz="UTC",
            model=model,
        )
        assert len(events) == 0
        assert counts.filtered_non_event == 1

    def test_snippet_fallback_for_no_raw_content(self):
        """Results without raw_content use snippet-only extraction."""
        result = _make_result(
            url="https://example.com/no-content",
            title="Some Event",
            snippet="Jazz at A-Trane on 20 Oct",
            raw_content=None,
        )
        model = _StubModel({
            "page_kind": "single_event",
            "events": [
                {"title": "Jazz at A-Trane", "start_local": "2026-10-20T21:00",
                 "tz": "Europe/Berlin", "city": "Berlin", "country": "DE",
                 "link": "https://example.com/no-content",
                 "description": "Live jazz", "confidence": 0.9},
            ],
        })
        events, counts = extract_events(
            [result],
            window_start=_WINDOW_START,
            window_end=_WINDOW_END,
            target_city="Berlin",
            target_country="DE",
            language=None,
            user_tz="UTC",
            model=model,
        )
        assert len(events) == 1
        # Snippet fallback: pages_content_pass should be 0
        assert counts.pages_content_pass == 0


class TestKnownLinkRemoval:
    """Known-link removal applies only for single_event pages (design §7).

    This test verifies the remove_known_pages function in search.py,
    not extract.py — but AC 3 specifies it together.
    """

    def test_single_event_page_removed(self):
        from app.adapters.search import remove_known_pages
        results = [
            _make_result("https://venue.example.com/show", raw_content="x"),
        ]
        stored_pages = [
            {"source_url": "https://venue.example.com/show", "page_kind": "single_event"},
        ]
        kept, known = remove_known_pages(results, stored_pages)
        assert known == 1
        assert len(kept) == 0

    def test_listing_page_not_removed(self):
        from app.adapters.search import remove_known_pages
        results = [
            _make_result("https://venue.example.com/programme", raw_content="x"),
        ]
        stored_pages = [
            {"source_url": "https://venue.example.com/programme", "page_kind": "listing"},
        ]
        kept, known = remove_known_pages(results, stored_pages)
        assert known == 0
        assert len(kept) == 1
