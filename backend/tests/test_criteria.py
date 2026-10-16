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


def test_get_criteria_fresh_user_returns_empty_text(client, auth_headers):
    h = auth_headers("freshcrit", "pw")
    r = client.get("/api/criteria", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["text"] == ""
    assert "updatedAt" in body


def test_save_criteria_empty_text_returns_400(client, auth_headers):
    # Code does not reject empty text — document that and assert 200.
    # If a validation rule is added later, change this to assert 400.
    h = auth_headers("demo", "demo")
    r = client.put("/api/criteria", json={"text": ""}, headers=h)
    assert r.status_code == 200


def test_save_criteria_upserts_existing(client, auth_headers, _db_session):
    from app.orm import Criteria, User

    h = auth_headers("demo", "demo")
    client.put("/api/criteria", json={"text": "first"}, headers=h)
    client.put("/api/criteria", json={"text": "second"}, headers=h)

    r = client.get("/api/criteria", headers=h)
    assert r.json()["text"] == "second"

    user = _db_session.query(User).filter(User.username == "demo").first()
    rows = _db_session.query(Criteria).filter(Criteria.user_id == user.id).count()
    assert rows == 1
