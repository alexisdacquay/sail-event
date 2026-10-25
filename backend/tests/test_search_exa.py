"""Contract tests for ExaProvider against a recorded live response (2026-10-25)."""
from __future__ import annotations

import io
import json
import pathlib
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from app.adapters.search_exa import ExaProvider

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "exa" / "search_jazz_berlin.json"


def _fake_urlopen():
    resp = MagicMock()
    resp.read.return_value = FIXTURE.read_bytes()
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(ExaProvider.API_URL, code, "err", {}, io.BytesIO(b""))


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("EXA_API_KEY", "test-key")
    return ExaProvider()


@patch("urllib.request.urlopen")
def test_request_body_and_header(mock_urlopen, provider):
    mock_urlopen.return_value = _fake_urlopen()
    provider.search("jazz Berlin October 2026 event", max_results=20, search_depth="advanced")

    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://api.exa.ai/search"
    assert req.get_header("X-api-key") == "test-key"
    assert json.loads(req.data) == {
        "query": "jazz Berlin October 2026 event",
        "numResults": 20,
        "type": "auto",
        "contents": {"text": True, "maxAgeHours": 0},
    }


@patch("urllib.request.urlopen")
def test_maps_recorded_response(mock_urlopen, provider):
    mock_urlopen.return_value = _fake_urlopen()
    results = provider.search("jazz concerts in Berlin next week event", max_results=3)

    recorded = json.loads(FIXTURE.read_bytes())["results"]
    assert len(results) == len(recorded) == 3
    for r, item in zip(results, recorded):
        assert r.url == item["url"]
        assert r.title == item["title"]
        assert r.raw_content == item["text"]  # full live page text
        assert r.published_at == item.get("publishedDate")  # absent in this recording
        assert r.provider == "exa"


@patch("time.sleep")
@patch("urllib.request.urlopen")
def test_429_retries_then_raises(mock_urlopen, _sleep, provider):
    mock_urlopen.side_effect = _http_error(429)
    with pytest.raises(RuntimeError, match="Exa API error: HTTP 429"):
        provider.search("q")
    assert mock_urlopen.call_count == 2


@pytest.mark.parametrize("code", [401, 400])
@patch("urllib.request.urlopen")
def test_client_error_raises_without_retry(mock_urlopen, provider, code):
    mock_urlopen.side_effect = _http_error(code)
    with pytest.raises(RuntimeError, match=f"HTTP {code}"):
        provider.search("q")
    assert mock_urlopen.call_count == 1


@patch("time.sleep")
@patch("urllib.request.urlopen")
def test_timeout_retries_then_succeeds(mock_urlopen, _sleep, provider):
    import socket
    mock_urlopen.side_effect = [
        urllib.error.URLError(socket.timeout("The read operation timed out")),
        _fake_urlopen(),
    ]
    assert len(provider.search("q")) == 3
    assert mock_urlopen.call_count == 2


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    with pytest.raises(ValueError, match="EXA_API_KEY"):
        ExaProvider()
