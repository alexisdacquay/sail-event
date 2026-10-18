"""Tests for GET /api/config."""

from __future__ import annotations


def test_config_registration_code_unset(client, monkeypatch):
    monkeypatch.delenv("REGISTRATION_CODE", raising=False)
    r = client.get("/api/config")
    assert r.status_code == 200
    assert r.json() == {"registrationCodeRequired": False}


def test_config_registration_code_set(client, monkeypatch):
    monkeypatch.setenv("REGISTRATION_CODE", "invite123")
    r = client.get("/api/config")
    assert r.status_code == 200
    assert r.json() == {"registrationCodeRequired": True}
