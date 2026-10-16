"""Tests for GET/PUT /api/criteria."""

from __future__ import annotations


def test_get_criteria(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.get("/api/criteria", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert "text" in body and body["text"] != ""
    assert "updatedAt" in body and body["updatedAt"] != ""


def test_save_criteria(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.put("/api/criteria", json={"text": "new criteria text"}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["text"] == "new criteria text"
    assert "updatedAt" in body

    # GET reflects the change
    r2 = client.get("/api/criteria", headers=h)
    assert r2.json()["text"] == "new criteria text"


def test_save_criteria_missing_text_returns_400(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.put("/api/criteria", json={}, headers=h)
    assert r.status_code == 400


def test_get_criteria_no_auth_returns_401(client):
    r = client.get("/api/criteria")
    assert r.status_code == 401
