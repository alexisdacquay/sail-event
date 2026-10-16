"""Tests for GET/PUT /api/thresholds."""

from __future__ import annotations


def test_get_thresholds(client):
    r = client.get("/api/thresholds")
    assert r.status_code == 200
    assert r.json() == {"lowerThreshold": 30, "upperThreshold": 70}


def test_save_thresholds(client):
    r = client.put(
        "/api/thresholds",
        json={"lowerThreshold": 20, "upperThreshold": 80},
    )
    assert r.status_code == 200
    assert r.json() == {"lowerThreshold": 20, "upperThreshold": 80}

    # GET reflects the change
    r2 = client.get("/api/thresholds")
    assert r2.json() == {"lowerThreshold": 20, "upperThreshold": 80}


def test_save_thresholds_lower_ge_upper_returns_400(client):
    # lower == upper
    r = client.put(
        "/api/thresholds",
        json={"lowerThreshold": 50, "upperThreshold": 50},
    )
    assert r.status_code == 400

    # lower > upper
    r = client.put(
        "/api/thresholds",
        json={"lowerThreshold": 70, "upperThreshold": 30},
    )
    assert r.status_code == 400


def test_save_thresholds_missing_field_returns_400(client):
    r = client.put("/api/thresholds", json={"lowerThreshold": 20})
    assert r.status_code == 400
