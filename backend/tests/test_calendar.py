"""Tests for GET /api/calendar/{ics_token}."""

from __future__ import annotations


def test_calendar_feed_valid_token(client):
    r = client.get("/api/calendar/demo-ics-token")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/calendar")
    assert "BEGIN:VCALENDAR" in r.text
    assert "END:VCALENDAR" in r.text


def test_calendar_feed_unknown_token_returns_404(client):
    r = client.get("/api/calendar/nonexistent-token")
    assert r.status_code == 404
