"""Contract tests for TavilyProviderV2 against the recorded C1 response."""

from __future__ import annotations

import io
import json
import pathlib
from unittest.mock import patch, MagicMock

import pytest

from app.adapters.search_tavily_v2 import TavilyProviderV2

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "tavily_v2" / "search_c1_query1.json"


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
    def test_country_germany_and_language_de(self, mock_urlopen, monkeypatch):
        """Local-language query sends country='germany' and language='de'."""
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()

        provider = TavilyProviderV2()
        provider.search(
            "Jazz Berlin Oktober 2026",
            country="DE",
            language="de",
            max_results=6,
        )

        # Inspect the request body sent to urlopen.
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        body = json.loads(req.data)

        assert body["country"] == "germany"
        assert body["language"] == "de"
        assert body["include_raw_content"] is True
        assert body["max_results"] == 6

    @patch("urllib.request.urlopen")
    def test_english_query_no_language(self, mock_urlopen, monkeypatch):
        """English query sends country but no language key."""
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()

        provider = TavilyProviderV2()
        provider.search(
            "jazz Berlin October 2026",
            country="DE",
            language=None,
            max_results=6,
        )

        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)

        assert body["country"] == "germany"
        assert "language" not in body

    @patch("urllib.request.urlopen")
    def test_unknown_country_omitted(self, mock_urlopen, monkeypatch):
        """Country code not in the table → country param omitted."""
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()

        provider = TavilyProviderV2()
        provider.search("test", country="ZZ", max_results=6)

        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert "country" not in body


# ---------- response mapping ----------


class TestMapping:
    @patch("urllib.request.urlopen")
    def test_maps_fields_from_recorded_response(self, mock_urlopen, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()

        provider = TavilyProviderV2()
        results = provider.search("jazz Berlin October 2026", country="DE", max_results=6)

        assert len(results) > 0
        first = results[0]
        assert first.url
        assert first.title
        assert first.snippet  # mapped from 'content'
        assert first.provider == "tavily"
        # Recorded response has raw_content for some results.
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
        provider = TavilyProviderV2()
        with pytest.raises(RuntimeError, match="HTTP 401"):
            provider.search("q")

    @patch("urllib.request.urlopen")
    def test_429_raises(self, mock_urlopen, monkeypatch):
        import urllib.error
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.tavily.com/search", 429, "Too Many Requests", {}, io.BytesIO(b""),
        )
        provider = TavilyProviderV2()
        with pytest.raises(RuntimeError, match="HTTP 429"):
            provider.search("q")

    @patch("urllib.request.urlopen")
    def test_5xx_raises(self, mock_urlopen, monkeypatch):
        import urllib.error
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.tavily.com/search", 503, "Service Unavailable", {}, io.BytesIO(b""),
        )
        provider = TavilyProviderV2()
        with pytest.raises(RuntimeError, match="HTTP 503"):
            provider.search("q")

    @patch("urllib.request.urlopen")
    def test_url_error_raises(self, mock_urlopen, monkeypatch):
        import urllib.error
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        mock_urlopen.side_effect = urllib.error.URLError("Connection timed out")
        provider = TavilyProviderV2()
        with pytest.raises(RuntimeError, match="Connection timed out"):
            provider.search("q")


# ---------- missing key ----------


class TestMissingKey:
    def test_missing_key_raises(self, monkeypatch):
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            TavilyProviderV2()
