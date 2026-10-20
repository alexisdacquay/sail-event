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


    def test_relative_window_expired_triggers_reparse(self, monkeypatch):
        """Relative date + stored end before today → re-parse."""
        monkeypatch.setenv("FAKE_NOW", "2026-10-26T12:00:00+02:00")
        text = "jazz in Berlin"
        sha = hashlib.sha256(text.encode()).hexdigest()
        import json
        facets_json = json.dumps({
            "date": {"start": "2026-10-19", "end": "2026-10-25", "relative": "next_week"},
        })
        assert needs_parse(text, sha, "criteria_v2", facets_json=facets_json, user_tz="Europe/Berlin") is True

    def test_relative_window_not_expired_no_reparse(self, monkeypatch):
        """Relative date + stored end in the future → no re-parse."""
        monkeypatch.setenv("FAKE_NOW", "2026-10-18T12:00:00+02:00")
        text = "jazz in Berlin"
        sha = hashlib.sha256(text.encode()).hexdigest()
        import json
        facets_json = json.dumps({
            "date": {"start": "2026-10-19", "end": "2026-10-25", "relative": "next_week"},
        })
        assert needs_parse(text, sha, "criteria_v2", facets_json=facets_json, user_tz="Europe/Berlin") is False

    def test_absolute_only_past_no_reparse(self, monkeypatch):
        """Absolute-only dates in the past never trigger re-parse."""
        monkeypatch.setenv("FAKE_NOW", "2026-10-22T12:00:00+02:00")
        text = "jazz in Berlin"
        sha = hashlib.sha256(text.encode()).hexdigest()
        import json
        facets_json = json.dumps({
            "date": {"start": "2026-10-19", "end": "2026-10-21"},
        })
        assert needs_parse(text, sha, "criteria_v2", facets_json=facets_json) is False

    def test_no_end_with_relative_no_reparse(self):
        """Relative but no stored end → no re-parse (end is resolved at runtime)."""
        text = "jazz in Berlin"
        sha = hashlib.sha256(text.encode()).hexdigest()
        import json
        facets_json = json.dumps({"date": {"relative": "next_week"}})
        assert needs_parse(text, sha, "criteria_v2", facets_json=facets_json) is False

    def test_expired_window_uses_user_tz(self, monkeypatch):
        """Window expiry compared in user's time zone, not UTC."""
        # 2026-10-21 23:30 UTC = 2026-10-22 01:30 Europe/Berlin
        # In Berlin it's already Oct 22, end Oct 21 is expired;
        # in UTC it's still Oct 21, not expired.
        monkeypatch.setenv("FAKE_NOW", "2026-10-21T23:30:00+00:00")
        text = "jazz in Berlin"
        sha = hashlib.sha256(text.encode()).hexdigest()
        import json
        facets_json = json.dumps({
            "date": {"start": "2026-10-19", "end": "2026-10-21", "relative": "next_week"},
        })
        # In Berlin: today is Oct 22 → expired
        assert needs_parse(text, sha, "criteria_v2", facets_json=facets_json, user_tz="Europe/Berlin") is True
        # In UTC: today is Oct 21 → not expired
        assert needs_parse(text, sha, "criteria_v2", facets_json=facets_json, user_tz="UTC") is False


class TestParseMetadata:
    def test_returns_sha_and_version(self, monkeypatch):
        monkeypatch.setenv("FAKE_NOW", "2026-10-18T12:00:00+02:00")
        text = "jazz in Berlin"
        meta = parse_metadata(text)
        assert meta["facets_text_sha"] == hashlib.sha256(text.encode()).hexdigest()
        assert meta["facets_version"] == "criteria_v2"
        assert meta["parsed_at"] is not None
