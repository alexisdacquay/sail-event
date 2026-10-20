"""Contract tests for BraveProvider against a hand-written fixture.

No Brave API key is available; the fixture is constructed from Brave's
documented response schema.
"""

from __future__ import annotations

import io
import json
import pathlib
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse, parse_qs

import pytest

from app.adapters.search_brave import BraveProvider

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "brave" / "search_c1_query1.json"


def _fake_urlopen(fixture_path: pathlib.Path = FIXTURE):
    data = fixture_path.read_bytes()
    resp = MagicMock()
    resp.read.return_value = data
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ---------- request param assertions ----------


class TestRequestParams:
    @patch("urllib.request.urlopen")
    def test_verbatim_query_no_country_no_language(self, mock_urlopen, monkeypatch):
        """Verbatim query: no country or search_lang params sent."""
        monkeypatch.setenv("BRAVE_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()

        provider = BraveProvider()
        provider.search("Jazz Berlin Oktober 2026 event", max_results=6)

        req = mock_urlopen.call_args[0][0]
        url = req.full_url
        params = parse_qs(urlparse(url).query)

        assert "country" not in params
        assert "search_lang" not in params
        assert "freshness" not in params

    @patch("urllib.request.urlopen")
    def test_no_freshness_param(self, mock_urlopen, monkeypatch):
        """freshness_days is accepted but never sent."""
        monkeypatch.setenv("BRAVE_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()

        provider = BraveProvider()
        provider.search("q", freshness_days=30, max_results=6)

        req = mock_urlopen.call_args[0][0]
        params = parse_qs(urlparse(req.full_url).query)
        assert "freshness" not in params

    @patch("urllib.request.urlopen")
    def test_subscription_token_header(self, mock_urlopen, monkeypatch):
        monkeypatch.setenv("BRAVE_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()

        provider = BraveProvider()
        provider.search("q")

        req = mock_urlopen.call_args[0][0]
        assert req.get_header("X-subscription-token") == "test-key"


# ---------- response mapping ----------


class TestMapping:
    @patch("urllib.request.urlopen")
    def test_maps_fields_from_fixture(self, mock_urlopen, monkeypatch):
        monkeypatch.setenv("BRAVE_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()

        provider = BraveProvider()
        results = provider.search("jazz Berlin October 2026", country="DE", max_results=6)

        assert len(results) == 3
        first = results[0]
        assert first.url == "https://www.berlinerfestspiele.de/en/jazzfest-berlin"
        assert "Jazzfest" in first.title
        assert first.provider == "brave"
        assert first.raw_content is None  # Brave never has raw_content

    @patch("urllib.request.urlopen")
    def test_extra_snippets_joined(self, mock_urlopen, monkeypatch):
        monkeypatch.setenv("BRAVE_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()

        provider = BraveProvider()
        results = provider.search("q")

        first = results[0]
        # extra_snippets are joined into the snippet.
        assert "24 acts" in first.snippet

    @patch("urllib.request.urlopen")
    def test_page_age_mapped(self, mock_urlopen, monkeypatch):
        """page_age present → published_at set."""
        monkeypatch.setenv("BRAVE_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()

        provider = BraveProvider()
        results = provider.search("q")

        first = results[0]
        assert first.published_at == "2026-10-01T00:00:00"

    @patch("urllib.request.urlopen")
    def test_page_age_absent_tolerated(self, mock_urlopen, monkeypatch):
        """page_age missing → published_at is None, no error."""
        monkeypatch.setenv("BRAVE_API_KEY", "test-key")
        mock_urlopen.return_value = _fake_urlopen()

        provider = BraveProvider()
        results = provider.search("q")

        # Second result has no page_age in the fixture.
        second = results[1]
        assert second.published_at is None


# ---------- error handling ----------


class TestErrors:
    @patch("urllib.request.urlopen")
    def test_401_raises(self, mock_urlopen, monkeypatch):
        import urllib.error
        monkeypatch.setenv("BRAVE_API_KEY", "test-key")
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.search.brave.com/", 401, "Unauthorized", {}, io.BytesIO(b""),
        )
        provider = BraveProvider()
        with pytest.raises(RuntimeError, match="HTTP 401"):
            provider.search("q")

    @patch("urllib.request.urlopen")
    def test_429_raises(self, mock_urlopen, monkeypatch):
        import urllib.error
        monkeypatch.setenv("BRAVE_API_KEY", "test-key")
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.search.brave.com/", 429, "Too Many Requests", {}, io.BytesIO(b""),
        )
        provider = BraveProvider()
        with pytest.raises(RuntimeError, match="HTTP 429"):
            provider.search("q")

    @patch("urllib.request.urlopen")
    def test_5xx_raises(self, mock_urlopen, monkeypatch):
        import urllib.error
        monkeypatch.setenv("BRAVE_API_KEY", "test-key")
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.search.brave.com/", 500, "Server Error", {}, io.BytesIO(b""),
        )
        provider = BraveProvider()
        with pytest.raises(RuntimeError, match="HTTP 500"):
            provider.search("q")


# ---------- missing key ----------


class TestMissingKey:
    def test_missing_key_raises(self, monkeypatch):
        monkeypatch.delenv("BRAVE_API_KEY", raising=False)
        with pytest.raises(ValueError, match="BRAVE_API_KEY"):
            BraveProvider()
