"""Tests for GET /api/health."""

from __future__ import annotations


def test_health_returns_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
