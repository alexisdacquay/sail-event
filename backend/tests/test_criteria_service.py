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


    def test_window_expired_triggers_reparse(self, monkeypatch):
        """When stored date.end is before today, needs_parse returns True."""
        monkeypatch.setenv("FAKE_NOW", "2026-10-22T12:00:00+02:00")
        text = "jazz in Berlin"
        sha = hashlib.sha256(text.encode()).hexdigest()
        import json
        facets_json = json.dumps({"date": {"end": "2026-10-21"}})
        assert needs_parse(text, sha, "criteria_v2", facets_json=facets_json) is True

    def test_window_not_expired_no_reparse(self, monkeypatch):
        """When stored date.end is in the future, text unchanged → no re-parse."""
        monkeypatch.setenv("FAKE_NOW", "2026-10-18T12:00:00+02:00")
        text = "jazz in Berlin"
        sha = hashlib.sha256(text.encode()).hexdigest()
        import json
        facets_json = json.dumps({"date": {"end": "2026-10-21"}})
        assert needs_parse(text, sha, "criteria_v2", facets_json=facets_json) is False

    def test_no_date_end_no_reparse(self):
        """When there is no absolute end, no window-based re-parse."""
        text = "jazz in Berlin"
        sha = hashlib.sha256(text.encode()).hexdigest()
        import json
        facets_json = json.dumps({"date": {"relative": "next_week"}})
        assert needs_parse(text, sha, "criteria_v2", facets_json=facets_json) is False


class TestParseMetadata:
    def test_returns_sha_and_version(self, monkeypatch):
        monkeypatch.setenv("FAKE_NOW", "2026-10-18T12:00:00+02:00")
        text = "jazz in Berlin"
        meta = parse_metadata(text)
        assert meta["facets_text_sha"] == hashlib.sha256(text.encode()).hexdigest()
        assert meta["facets_version"] == "criteria_v2"
        assert meta["parsed_at"] is not None
