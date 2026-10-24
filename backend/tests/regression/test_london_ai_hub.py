"""Regression: London AI Hub events page — issue #134.

Root cause: the 20 000-char content slice and the 10-event per-page cap
dropped "The Infrastructure Decisions That Define Your Trajectory"
(2026-10-27T17:30, London).  The model never saw the full page, and even
if it did, the cap would drop events beyond position 10.

Written RED before the fix; passes after criteria A–C of issue 134.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.adapters.search import SearchResult
from app.services.extract import extract_events
from app.services.filters import filter_events

_FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "london_ai_hub_events.html"

# The target event that must survive the full pipeline.
_TARGET_TITLE = "The Infrastructure Decisions That Define Your Trajectory"
_TARGET_START = "2026-10-27T17:30"

# Window matching the October 2026 period.
_WINDOW_START = datetime(2026, 10, 18, 0, 0, tzinfo=timezone.utc)
_WINDOW_END = datetime(2026, 10, 31, 23, 59, 59, tzinfo=timezone.utc)
_NOW = datetime(2026, 10, 18, 10, 0, tzinfo=timezone.utc)


def _make_events(n: int, *, include_target: bool) -> list[dict]:
    """Build a realistic model response: n filler events plus the target."""
    events = []
    for i in range(1, n + 1):
        events.append({
            "title": f"AI Meetup #{i}",
            "start_local": f"2026-10-{20 + (i % 8):02d}T18:00",
            "start_tz": "Europe/London",
            "end_local": None,
            "venue": "Some Venue",
            "city": "London",
            "country": "GB",
            "link": f"https://www.londonaihub.co.uk/events/meetup-{i}",
            "description": f"AI Meetup number {i} in London.",
            "confidence": 0.9,
        })
    if include_target:
        events.append({
            "title": _TARGET_TITLE,
            "start_local": _TARGET_START,
            "start_tz": "Europe/London",
            "end_local": None,
            "venue": "London AI Hub",
            "city": "London",
            "country": "GB",
            "link": "https://www.londonaihub.co.uk/events/the-infrastructure-decisions-that-define-your-trajectory",
            "description": "How early infrastructure choices shape your AI product's long-term trajectory.",
            "confidence": 0.95,
        })
    return events


class _ContentAwareModel:
    """Returns the target event only when the model receives the full page.

    On current main the 20k slice truncates the 220k page, so the content
    variable is short and the model 'cannot see' the target event.  After
    fix A (slice removed) the full content arrives.  The response also has
    12 filler events so that fix B (cap removed) is needed too.
    """

    model_id = "test:regression"

    def complete_json(self, **kwargs):
        content = kwargs.get("variables", {}).get("content", "")
        # Full page is ~220 k chars; sliced is ~20 k.
        full_page = len(content) > 25_000
        response = {
            "page_kind": "listing",
            "events": _make_events(12, include_target=full_page),
        }
        usage = type("U", (), {"tokens_in": 0, "tokens_out": 0})()
        return response, usage


class TestLondonAIHubRegression:
    """Issue #134 — the target event must survive extract + filter."""

    @pytest.fixture()
    def raw_content(self) -> str:
        return _FIXTURE.read_text()

    def test_infrastructure_decisions_survives(self, raw_content: str):
        result = SearchResult(
            url="https://www.londonaihub.co.uk/events",
            title="Events — London AI Hub",
            snippet="Browse upcoming AI events in London.",
            raw_content=raw_content,
            published_at=None,
            provider="tavily",
        )
        model = _ContentAwareModel()
        events, _counts = extract_events(
            [result],
            window_start=_WINDOW_START,
            window_end=_WINDOW_END,
            target_city="London",
            target_country="GB",
            language=None,
            user_tz="Europe/London",
            model=model,
        )
        kept, _fcounts = filter_events(
            events,
            now_utc=_NOW,
            window_start_utc=_WINDOW_START,
            window_end_utc=_WINDOW_END,
            target_city="London",
            target_country="GB",
            user_tz="Europe/London",
        )

        titles = {e.title for e in kept}
        assert _TARGET_TITLE in titles, (
            f"Target event not found among {len(kept)} kept events. "
            f"Extracted {len(events)}, titles: {[e.title for e in events]}"
        )
        target = next(e for e in kept if e.title == _TARGET_TITLE)
        assert target.start_local == _TARGET_START
