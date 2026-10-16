"""Tests for POST /api/search and POST /api/search/all."""

from __future__ import annotations


def test_run_search_returns_search_result(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.post("/api/search", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert "runId" in body
    assert "eventsFound" in body
    assert "eventsNew" in body


def test_run_search_dedup_no_new_events(client, auth_headers):
    """All fixture events are already seeded; a second run produces 0 new."""
    h = auth_headers("demo", "demo")
    r = client.post("/api/search", headers=h)
    body = r.json()
    assert body["eventsFound"] == 9  # raw fixture count including dup
    assert body["eventsNew"] == 0


def test_run_search_increments_run_id(client, auth_headers):
    h = auth_headers("demo", "demo")
    r1 = client.post("/api/search", headers=h)
    r2 = client.post("/api/search", headers=h)
    assert r1.json()["runId"] != r2.json()["runId"]


def test_search_all_missing_key_returns_401(client):
    r = client.post("/api/search/all")
    assert r.status_code == 401


def test_search_all_wrong_key_returns_401(client, monkeypatch):
    monkeypatch.setenv("SEARCH_ALL_API_KEY", "correct-key")
    r = client.post("/api/search/all", headers={"X-API-Key": "wrong-key"})
    assert r.status_code == 401


def test_search_all_unset_env_returns_401(client, monkeypatch):
    monkeypatch.delenv("SEARCH_ALL_API_KEY", raising=False)
    r = client.post("/api/search/all", headers={"X-API-Key": "anything"})
    assert r.status_code == 401


def test_search_all_correct_key(client, monkeypatch):
    monkeypatch.setenv("SEARCH_ALL_API_KEY", "test-secret")
    r = client.post("/api/search/all", headers={"X-API-Key": "test-secret"})
    assert r.status_code == 200
    assert r.json() == {"usersProcessed": 1}


def test_run_search_no_auth_returns_401(client):
    r = client.post("/api/search")
    assert r.status_code == 401
