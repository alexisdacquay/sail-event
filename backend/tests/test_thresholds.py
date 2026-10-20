"""Tests for GET/PUT /api/thresholds."""

from __future__ import annotations


def test_get_thresholds(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.get("/api/thresholds", headers=h)
    assert r.status_code == 200
    assert r.json() == {"lowerThreshold": 40, "upperThreshold": 90}


def test_save_thresholds(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.put(
        "/api/thresholds",
        json={"lowerThreshold": 20, "upperThreshold": 80},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json() == {"lowerThreshold": 20, "upperThreshold": 80}

    # GET reflects the change
    r2 = client.get("/api/thresholds", headers=h)
    assert r2.json() == {"lowerThreshold": 20, "upperThreshold": 80}


def test_save_thresholds_lower_ge_upper_returns_400(client, auth_headers):
    h = auth_headers("demo", "demo")
    # lower == upper
    r = client.put(
        "/api/thresholds",
        json={"lowerThreshold": 50, "upperThreshold": 50},
        headers=h,
    )
    assert r.status_code == 400

    # lower > upper
    r = client.put(
        "/api/thresholds",
        json={"lowerThreshold": 70, "upperThreshold": 30},
        headers=h,
    )
    assert r.status_code == 400


def test_save_thresholds_missing_field_returns_400(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.put("/api/thresholds", json={"lowerThreshold": 20}, headers=h)
    assert r.status_code == 400


def test_get_thresholds_no_auth_returns_401(client):
    r = client.get("/api/thresholds")
    assert r.status_code == 401
