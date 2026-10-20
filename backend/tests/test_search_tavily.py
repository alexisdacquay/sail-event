"""Contract tests for TavilyProvider against the recorded C1 response."""
from __future__ import annotations

import io
import json
import pathlib
from unittest.mock import patch, MagicMock

import pytest

from app.adapters.search_tavily import TavilyProvider

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "tavily" / "search_c1_query1.json"


def _fake_urlopen(fixture_path: pathlib.Path = FIXTURE):
    """Return a context-manager mock that yields the fixture JSON."""
    data = fixture_path.read_bytes()
    resp = MagicMock()
    resp.read.return_value = data
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ---------- request body assertions ----------


class TestRequestBody:
    @patch("urllib.request.urlopen")
    def test_verbatim_query_no_country_no_language(self, mock_urlopen, monkeypatch):
        """Verbatim query: no country, no language param sent."""
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()

        provider = TavilyProvider()
        provider.search("jazz Berlin October 2026 event", max_results=20)

        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)

        assert body["query"] == "jazz Berlin October 2026 event"
        assert "country" not in body
        assert "language" not in body
        assert body["include_raw_content"] is True
        assert body["max_results"] == 20
        assert body["search_depth"] == "advanced"

    @patch("urllib.request.urlopen")
    def test_search_depth_from_env(self, mock_urlopen, monkeypatch):
        """TAVILY_SEARCH_DEPTH env overrides the default."""
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        monkeypatch.setenv("TAVILY_SEARCH_DEPTH", "basic")
        mock_urlopen.return_value = _fake_urlopen()

        provider = TavilyProvider()
        provider.search("test", max_results=6)

        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert body["search_depth"] == "basic"


# ---------- response mapping ----------


class TestMapping:
    @patch("urllib.request.urlopen")
    def test_maps_fields_from_recorded_response(self, mock_urlopen, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()

        provider = TavilyProvider()
        results = provider.search("jazz Berlin October 2026", max_results=6)

        assert len(results) > 0
        first = results[0]
        assert first.url
        assert first.title
        assert first.snippet  # mapped from 'content'
        assert first.provider == "tavily"
        has_raw = any(r.raw_content for r in results)
        assert has_raw, "At least one result should have raw_content"


# ---------- error handling ----------


class TestErrors:
    @patch("urllib.request.urlopen")
    def test_401_raises(self, mock_urlopen, monkeypatch):
        import urllib.error
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.tavily.com/search", 401, "Unauthorized", {}, io.BytesIO(b""),
        )
        provider = TavilyProvider()
        with pytest.raises(RuntimeError, match="HTTP 401"):
            provider.search("q")

    @patch("urllib.request.urlopen")
    def test_429_retries_then_raises(self, mock_urlopen, monkeypatch):
        import urllib.error
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.tavily.com/search", 429, "Too Many Requests", {}, io.BytesIO(b""),
        )
        provider = TavilyProvider()
        with pytest.raises(RuntimeError, match="HTTP 429"):
            provider.search("q")
        assert mock_urlopen.call_count == 2  # retry once

    @patch("urllib.request.urlopen")
    def test_5xx_raises(self, mock_urlopen, monkeypatch):
        import urllib.error
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.tavily.com/search", 503, "Service Unavailable", {}, io.BytesIO(b""),
        )
        provider = TavilyProvider()
        with pytest.raises(RuntimeError, match="HTTP 503"):
            provider.search("q")

    @patch("urllib.request.urlopen")
    def test_url_error_raises(self, mock_urlopen, monkeypatch):
        import urllib.error
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.side_effect = urllib.error.URLError("Connection timed out")
        provider = TavilyProvider()
        with pytest.raises(RuntimeError, match="Connection timed out"):
            provider.search("q")


# ---------- missing key ----------


class TestMissingKey:
    def test_missing_key_raises(self, monkeypatch):
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            TavilyProvider()
