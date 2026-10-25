"""Regression: Musikverein listing-page hop — issue #139.

Root cause: the Musikverein listing page says "7 November" with no time.
The event's own page (one hop away) says "7 November 2026 at 19:30".
Without the hop, filtered_no_time drops the Lise Davidsen recital.

Written RED before the fix; passes after criterion A of issue 139.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from app.adapters.search import SearchResult
from app.services.extract import extract_events, ExtractedEvent
from app.services.detail_hop import detail_hop
from app.services.filters import filter_events

_LISTING = Path(__file__).resolve().parent / "issue_139_musikverein_listing.html"
_DETAIL = Path(__file__).resolve().parent / "issue_139_musikverein_detail.html"

_LISTING_URL = "https://www.musikverein.at/en"
_DETAIL_URL = "https://www.musikverein.at/en/konzert/lise-davidsen-james-baillieu-0006accc/"

_TARGET_TITLE = "Lise Davidsen recital"
_TARGET_START = "2026-11-07T19:30"

_WINDOW_START = datetime(2026, 10, 18, 0, 0, tzinfo=timezone.utc)
_WINDOW_END = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
_NOW = datetime(2026, 10, 18, 10, 0, tzinfo=timezone.utc)


class _ListingModel:
    """Returns Davidsen with date-only from the listing page.

    When the content is the detail page (contains '19:30'), returns
    Davidsen with full date-time.
    """

    model_id = "test:regression-139"

    def complete_json(self, **kwargs):
        content = kwargs.get("variables", {}).get("content", "")
        if "19:30" in content:
            # Detail page — model sees the time
            events = [{
                "title": _TARGET_TITLE,
                "start_local": "2026-11-07T19:30",
                "start_tz": "Europe/Vienna",
                "end_local": None,
                "venue": "Großer Saal, Musikverein",
                "city": "Vienna",
                "country": "AT",
                "link": _DETAIL_URL,
                "description": "Lise Davidsen and James Baillieu perform Schubert lieder at the Musikverein.",
                "confidence": 0.95,
            }]
            return {"page_kind": "single_event", "events": events}, _usage()
        else:
            # Listing page — no time visible
            events = [
                {
                    "title": "Vienna Philharmonic",
                    "start_local": "2026-10-25T19:30",
                    "start_tz": "Europe/Vienna",
                    "end_local": None,
                    "venue": "Großer Saal",
                    "city": "Vienna",
                    "country": "AT",
                    "link": "https://www.musikverein.at/en/konzert/wiener-philharmoniker-001/",
                    "description": "Vienna Philharmonic concert.",
                    "confidence": 0.9,
                },
                {
                    "title": _TARGET_TITLE,
                    "start_local": "2026-11-07",  # date-only — no time on listing page
                    "start_tz": "Europe/Vienna",
                    "end_local": None,
                    "venue": "Musikverein",
                    "city": "Vienna",
                    "country": "AT",
                    "link": _DETAIL_URL,
                    "description": "Lise Davidsen soprano recital at the Musikverein, 7 November.",
                    "confidence": 0.9,
                },
            ]
            return {"page_kind": "listing", "events": events}, _usage()


def _usage():
    return type("U", (), {"tokens_in": 0, "tokens_out": 0})()


def _mock_urlopen(detail_html: str):
    """Return a mock urlopen that serves the detail page for the Davidsen URL."""
    def _urlopen(req, *, timeout=10):
        resp = MagicMock()
        resp.status = 200
        resp.headers = MagicMock()
        resp.headers.get_content_type.return_value = "text/html"
        resp.read1.side_effect = [detail_html.encode("utf-8"), b""]
        resp.__enter__ = lambda s: s
        resp.__exit__ = lambda s, *a: None
        return resp
    return _urlopen


class TestMusikvereinHop:
    """Issue #139 — the Davidsen recital must survive via the detail-page hop."""

    @pytest.fixture()
    def listing_html(self) -> str:
        return _LISTING.read_text()

    @pytest.fixture()
    def detail_html(self) -> str:
        return _DETAIL.read_text()

    def test_davidsen_survives_with_hop(self, listing_html: str, detail_html: str):
        result = SearchResult(
            url=_LISTING_URL,
            title="Musikverein Wien — Concerts",
            snippet="Concert programme of the Musikverein Vienna.",
            raw_content=listing_html,
            published_at=None,
            provider="tavily",
        )
        model = _ListingModel()

        # Step 1: extract from the listing page
        events, ecounts = extract_events(
            [result],
            window_start=_WINDOW_START,
            window_end=_WINDOW_END,
            target_city="Vienna",
            target_country="AT",
            language=None,
            user_tz="Europe/Vienna",
            model=model,
        )

        # The Davidsen event should be extracted with date-only
        davidsen_pre = [e for e in events if _TARGET_TITLE in e.title]
        assert davidsen_pre, "Davidsen not extracted from listing page"
        assert davidsen_pre[0].start_local == "2026-11-07", "Expected date-only before hop"

        # Step 2: detail-page hop
        with patch("app.services.detail_hop.urllib.request.urlopen", _mock_urlopen(detail_html)):
            hopped, hop_counts = detail_hop(
                events,
                model=model,
                user_tz="Europe/Vienna",
                window_start=_WINDOW_START,
                window_end=_WINDOW_END,
                target_city="Vienna",
                target_country="AT",
            )

        # Step 3: filter
        kept, fcounts = filter_events(
            hopped,
            now_utc=_NOW,
            window_start_utc=_WINDOW_START,
            window_end_utc=_WINDOW_END,
            target_city="Vienna",
            target_country="AT",
            user_tz="Europe/Vienna",
        )

        # The Davidsen recital must survive with the time from the detail page
        titles = {e.title for e in kept}
        assert _TARGET_TITLE in titles, (
            f"Davidsen not found among {len(kept)} kept events. "
            f"Titles: {[e.title for e in kept]}. "
            f"filtered_no_time={fcounts.filtered_no_time}"
        )
        target = next(e for e in kept if e.title == _TARGET_TITLE)
        assert target.start_local == _TARGET_START
