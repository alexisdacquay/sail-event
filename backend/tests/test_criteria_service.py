"""Unit tests for services/criteria.py."""

from __future__ import annotations

import hashlib

from app.services.criteria import needs_parse, parse_metadata


class TestNeedsParse:
    def test_new_criteria(self):
        assert needs_parse("jazz in Berlin", None, None) is True

    def test_same_text_same_version(self):
        text = "jazz in Berlin"
        sha = hashlib.sha256(text.encode()).hexdigest()
        assert needs_parse(text, sha, "criteria_v2") is False

    def test_text_changed(self):
        text_old = "jazz in Berlin"
        text_new = "classical in Vienna"
        sha_old = hashlib.sha256(text_old.encode()).hexdigest()
        assert needs_parse(text_new, sha_old, "criteria_v2") is True

    def test_version_changed(self):
        text = "jazz in Berlin"
        sha = hashlib.sha256(text.encode()).hexdigest()
        assert needs_parse(text, sha, "criteria_v1") is True


class TestParseMetadata:
    def test_returns_sha_and_version(self, monkeypatch):
        monkeypatch.setenv("FAKE_NOW", "2026-10-18T12:00:00+02:00")
        text = "jazz in Berlin"
        meta = parse_metadata(text)
        assert meta["facets_text_sha"] == hashlib.sha256(text.encode()).hexdigest()
        assert meta["facets_version"] == "criteria_v2"
        assert meta["parsed_at"] is not None
