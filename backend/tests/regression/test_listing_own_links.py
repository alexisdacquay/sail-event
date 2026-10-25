"""Regression: listing events keep the listing URL as their link, so no event page is opened.

Root cause (owner's search "AI events or hackathons in London next week", 2026-10-25):
all 308 events from 8 listing pages got link = the listing URL.
  1. The search provider's page text carries no URLs, so the model has none to give.
  2. extract._process_pass2 rewrote any link on another host to the listing URL.
  3. detail_hop._needs_hop refused to hop a link on another host.
The live listing HTML holds the events' own URLs (anchors, JSON-LD), e.g. aisa.to
"Internet Icons: Jeffrey Veen" -> https://luma.com/granola-jeffrey-veen.

Inputs are saved real pages: the listing HTML as fetched live, and the page text Exa returned.
Written RED before the fix.
"""

from __future__ import annotations

import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.adapters.search import SearchResult
from app.orm import User
from app.services import pipeline as pipeline_mod
from app.services.pipeline import run_pipeline

_HERE = Path(__file__).resolve().parent

_CASES = [
    # (saved page stem, listing URL, event title, event's own URL as linked from the listing)
    ("aisa_to_ai_events_london", "https://aisa.to/ai-events-london",
     "Internet Icons: Jeffrey Veen", "https://luma.com/granola-jeffrey-veen"),
    ("ukhackathons_ai_hackathons", "https://ukhackathons.com/ai-hackathons",
     "Greentech Hackathon", "https://ukhackathons.com/events/greentech-hackathon"),
]
_DECOY = "https://evil.example/not-on-the-page"


def _usage():
    return type("U", (), {"tokens_in": 0, "tokens_out": 0})()


class _Provider:
    name = "exa"

    def __init__(self, result: SearchResult):
        self._result = result

    def search(self, query, **kwargs):
        return [self._result]


class _Model:
    """A model can only copy a URL it was shown: the own link when it is in the content, else the listing."""

    model_id = "test:listing-own-links"

    def __init__(self, listing: str, title: str, own: str):
        self.listing, self.title, self.own = listing, title, own

    def complete_json(self, *, prompt_name, prompt_version, variables, **kwargs):
        if prompt_name != "extract":  # the judge is past the point under test
            raise RuntimeError(f"not exercised here: {prompt_name}")
        content = variables["content"]
        event = {"title": self.title, "start_local": "2026-11-10T18:00", "start_tz": "Europe/London",
                 "end_local": None, "venue": None, "city": "London", "country": "GB",
                 "description": "An event.", "confidence": 0.9}
        if content.startswith(f"URL: {self.own}\n"):
            return {"page_kind": "single_event", "events": [{**event, "link": self.own}]}, _usage()
        assert content.startswith(f"URL: {self.listing}\n"), content[:100]
        link = self.own if self.own in content else self.listing
        decoy = {**event, "title": "Decoy", "link": _DECOY}
        return {"page_kind": "listing", "events": [{**event, "link": link}, decoy]}, _usage()


def _urlopen(pages: dict[str, str]):
    def _open(req, *, timeout=10):
        url = req.full_url
        if url not in pages:
            raise urllib.error.URLError(f"not served in this test: {url}")
        resp = MagicMock()
        resp.status = 200
        resp.headers.get_content_type.return_value = "text/html"
        resp.read1.side_effect = [pages[url].encode("utf-8"), b""]
        resp.__enter__ = lambda s: s
        resp.__exit__ = lambda s, *a: None
        return resp
    return _open


@pytest.mark.parametrize("stem,listing,title,own", _CASES, ids=[c[0] for c in _CASES])
def test_listing_event_gets_its_own_link_and_page(_db_session, stem, listing, title, own):
    result = SearchResult(url=listing, title="listing", snippet="", provider="exa",
                          raw_content=(_HERE / f"{stem}.txt").read_text())
    pages = {listing: (_HERE / f"{stem}.html").read_text(),
             own: f"<html><body><h1>{title}</h1><p>10 November 2026, 18:00</p></body></html>"}
    seen: list = []
    real_filter = pipeline_mod.filter_events

    def _spy_filter(events, **kwargs):
        seen.extend(events)
        return real_filter(events, **kwargs)

    user = _db_session.query(User).filter(User.username == "demo").first()
    with patch("app.services.pipeline.get_search_provider", return_value=_Provider(result)), \
            patch("app.services.pipeline.get_language_model", return_value=_Model(listing, title, own)), \
            patch("app.services.detail_hop.urllib.request.urlopen", _urlopen(pages)), \
            patch("app.services.pipeline.filter_events", side_effect=_spy_filter):
        run_pipeline(user, _db_session, trigger="manual")

    event = next(e for e in seen if e.title == title)
    assert event.link == own, f"{title!r} kept link {event.link!r}"
    assert event.source_url == own, f"{title!r} was not opened on its own page (source {event.source_url!r})"
    decoy = next(e for e in seen if e.title == "Decoy")
    assert decoy.link == listing, "a link that is not on the page must fall back to the listing URL"
