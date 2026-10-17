"""Tests for TavilySearchProvider — all fixture-based, no live network."""

from __future__ import annotations

import io
import json
import pathlib
from unittest.mock import patch, MagicMock

import pytest

from app.adapters.search_tavily import TavilySearchProvider, _extract_date

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "tavily" / "search_response.json"


def _fake_urlopen(fixture_path: pathlib.Path = FIXTURE):
    """Return a context-manager mock that yields the fixture JSON."""
    data = fixture_path.read_bytes()
    resp = MagicMock()
    resp.read.return_value = data
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ---------- date extraction ----------


class TestExtractDate:
    def test_iso_date(self):
        assert _extract_date("Event on 2026-06-20 in London") == "2026-06-20"

    def test_iso_datetime(self):
        assert _extract_date("Starts 2026-10-15T14:00 sharp") == "2026-10-15T14:00"

    def test_textual_long(self):
        assert _extract_date("Deadline January 15, 2026") == "January 15, 2026"

    def test_textual_short(self):
        assert _extract_date("Opens Jan 3, 2026") == "Jan 3, 2026"

    def test_no_date(self):
        assert _extract_date("No dates here at all") is None


# ---------- mapping correctness ----------


class TestMapping:
    @patch("urllib.request.urlopen")
    def test_maps_fields_from_fixture(self, mock_urlopen, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()
        provider = TavilySearchProvider()
        events = provider.search(["sailing regattas"])

        first = events[0]
        assert first.title == "Round the Island Race 2026"
        assert first.link == "https://example.com/round-island-2026"
        assert first.description.startswith("The Round the Island Race")
        assert first.date_time == "2026-06-20"
        assert first.place == "unknown"

    @patch("urllib.request.urlopen")
    def test_date_from_title_when_content_has_none(self, mock_urlopen, monkeypatch):
        """Sydney to Hobart has 'Dec 26, 2026' only in the title."""
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()
        provider = TavilySearchProvider()
        events = provider.search(["q"])

        syd = [e for e in events if "Sydney" in e.title]
        assert len(syd) == 1
        assert syd[0].date_time == "Dec 26, 2026"

    @patch("urllib.request.urlopen")
    def test_unknown_date_when_none_in_content(self, mock_urlopen, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()
        provider = TavilySearchProvider()
        events = provider.search(["q"])

        med = [e for e in events if "Mediterranean" in e.title]
        assert len(med) == 1
        # "Dec 26, 2026" is in the *next* result's title, not this one's content
        # Mediterranean has no date in content or title
        assert med[0].date_time == "unknown"


# ---------- dedup ----------


class TestDedup:
    @patch("urllib.request.urlopen")
    def test_dedup_by_url(self, mock_urlopen, monkeypatch):
        """Fixture has two results with the same URL; only one should survive."""
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()
        provider = TavilySearchProvider()
        events = provider.search(["q"])

        urls = [e.link for e in events]
        assert len(urls) == len(set(urls))
        # Fixture has 5 results, one duplicate URL → 4 unique
        assert len(events) == 4


# ---------- MAX_EVENTS_PER_RUN cap ----------


class TestCap:
    @patch("urllib.request.urlopen")
    def test_max_events_cap(self, mock_urlopen, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        monkeypatch.setenv("MAX_EVENTS_PER_RUN", "2")
        mock_urlopen.return_value = _fake_urlopen()
        provider = TavilySearchProvider()
        events = provider.search(["q"])
        assert len(events) == 2


# ---------- missing API key ----------


class TestMissingKey:
    def test_missing_key_raises(self, monkeypatch):
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            TavilySearchProvider()


# ---------- HTTP error ----------


class TestHTTPError:
    @patch("urllib.request.urlopen")
    def test_http_error_raises(self, mock_urlopen, monkeypatch):
        import urllib.error

        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.tavily.com/search", 401, "Unauthorized", {}, io.BytesIO(b"")
        )
        provider = TavilySearchProvider()
        with pytest.raises(RuntimeError, match="HTTP 401"):
            provider.search(["q"])

    @patch("urllib.request.urlopen")
    def test_url_error_raises(self, mock_urlopen, monkeypatch):
        import urllib.error

        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.side_effect = urllib.error.URLError("Connection timed out")
        provider = TavilySearchProvider()
        with pytest.raises(RuntimeError, match="Connection timed out"):
            provider.search(["q"])


# ---------- factory integration ----------


class TestFactory:
    def test_factory_returns_tavily(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "tavily")
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        from app.adapters import get_search_provider

        provider = get_search_provider()
        assert isinstance(provider, TavilySearchProvider)

    def test_factory_missing_key_raises(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "tavily")
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        from app.adapters import get_search_provider

        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            get_search_provider()
