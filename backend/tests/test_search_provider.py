"""Tests for adapters.search: canonical_url and remove_known_pages."""

from __future__ import annotations

import pytest

from app.adapters.search import SearchResult, canonical_url, remove_known_pages


# ---------- canonical_url ----------

class TestCanonicalUrl:
    def test_strip_utm(self):
        assert canonical_url("https://example.com/page?utm_source=x&id=1") == \
            "https://example.com/page?id=1"

    def test_strip_fragment(self):
        assert canonical_url("https://example.com/page#section") == \
            "https://example.com/page"

    def test_strip_trailing_slash(self):
        assert canonical_url("https://example.com/page/") == \
            "https://example.com/page"

    def test_lowercase_host(self):
        assert canonical_url("https://EXAMPLE.COM/Page") == \
            "https://example.com/Page"

    def test_drop_default_port_443(self):
        assert canonical_url("https://example.com:443/page") == \
            "https://example.com/page"

    def test_drop_default_port_80(self):
        assert canonical_url("http://example.com:80/page") == \
            "http://example.com/page"

    def test_keep_nondefault_port(self):
        assert canonical_url("https://example.com:8080/page") == \
            "https://example.com:8080/page"

    def test_drop_fbclid(self):
        assert canonical_url("https://example.com/?fbclid=abc") == \
            "https://example.com"

    def test_keep_other_params(self):
        assert canonical_url("https://example.com/search?q=jazz&page=2") == \
            "https://example.com/search?q=jazz&page=2"


# ---------- remove_known_pages ----------

def _result(url: str) -> SearchResult:
    return SearchResult(url=url, title="T", snippet="S", provider="test")


class TestRemoveKnownPages:
    def test_single_event_removed(self):
        """A stored single_event page is dropped from results."""
        results = [
            _result("https://example.com/event-1"),
            _result("https://example.com/event-2"),
        ]
        stored = [
            {"source_url": "https://example.com/event-1", "page_kind": "single_event"},
        ]
        kept, count = remove_known_pages(results, stored)
        assert len(kept) == 1
        assert kept[0].url == "https://example.com/event-2"
        assert count == 1

    def test_listing_page_kept(self):
        """A stored listing page is returned for re-extraction."""
        results = [
            _result("https://example.com/programme"),
            _result("https://example.com/event-2"),
        ]
        stored = [
            {"source_url": "https://example.com/programme", "page_kind": "listing"},
        ]
        kept, count = remove_known_pages(results, stored)
        assert len(kept) == 2
        assert count == 0

    def test_canonical_match(self):
        """Known-page match works through canonical URL normalization."""
        results = [
            _result("https://example.com/event-1?utm_source=facebook"),
        ]
        stored = [
            {"source_url": "https://example.com/event-1", "page_kind": "single_event"},
        ]
        kept, count = remove_known_pages(results, stored)
        assert len(kept) == 0
        assert count == 1

    def test_mixed(self):
        """One single_event and one listing among results."""
        results = [
            _result("https://example.com/event-1"),
            _result("https://example.com/programme"),
            _result("https://example.com/event-3"),
        ]
        stored = [
            {"source_url": "https://example.com/event-1", "page_kind": "single_event"},
            {"source_url": "https://example.com/programme", "page_kind": "listing"},
        ]
        kept, count = remove_known_pages(results, stored)
        assert len(kept) == 2  # programme + event-3
        assert count == 1

    def test_empty_stored(self):
        results = [_result("https://example.com/a")]
        kept, count = remove_known_pages(results, [])
        assert len(kept) == 1
        assert count == 0
