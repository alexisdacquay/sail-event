"""Tests for GET/PUT /api/criteria."""

from __future__ import annotations


def test_get_criteria(client):
    r = client.get("/api/criteria")
    assert r.status_code == 200
    body = r.json()
    assert "text" in body and body["text"] != ""
    assert "updatedAt" in body and body["updatedAt"] != ""


def test_save_criteria(client):
    r = client.put("/api/criteria", json={"text": "new criteria text"})
    assert r.status_code == 200
    body = r.json()
    assert body["text"] == "new criteria text"
    assert "updatedAt" in body

    # GET reflects the change
    r2 = client.get("/api/criteria")
    assert r2.json()["text"] == "new criteria text"


def test_save_criteria_missing_text_returns_400(client):
    r = client.put("/api/criteria", json={})
    assert r.status_code == 400
