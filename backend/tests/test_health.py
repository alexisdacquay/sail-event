"""Tests for GET /api/health."""

from __future__ import annotations


def test_health_returns_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert "commit" in r.json()


def test_health_reports_render_commit(client, monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abc1234")
    assert client.get("/api/health").json()["commit"] == "abc1234"
