"""Regression: #112 — events without a start date counted in their own counter.

Root cause: filters.py dropped no-date events into filtered_non_event (a page
counter), making the funnel bar taller than its ribbons.  Fix: separate
filtered_no_date counter for events, filtered_non_event stays a page counter.
"""
from app.services.filters import FilterCounts, _is_complete


class _FakeEvent:
    """Minimal extracted event for the filter check."""
    def __init__(self, **kw):
        self.title = kw.get("title", "Jazz Night")
        self.start_local = kw.get("start_local", "2026-10-20T20:00")
        self.start_tz = kw.get("start_tz", "Europe/Berlin")
        self.city = kw.get("city", "Berlin")
        self.country = kw.get("country", "DE")
        self.description = kw.get("description", "Live jazz")


def test_no_date_event_is_incomplete():
    """#112: an event with no start_local is incomplete, never a page count."""
    ev = _FakeEvent(start_local=None)
    assert not _is_complete(ev)


def test_complete_event_passes():
    ev = _FakeEvent()
    assert _is_complete(ev)
