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
    body = r.json()
    assert body["lowerThreshold"] == 20
    assert body["upperThreshold"] == 80
    assert "eventsMoved" in body

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


def test_save_thresholds_reapplies_to_auto_events(client, auth_headers, _db_session):
    """Changing thresholds re-triages auto-decided events."""
    from app.orm import User, Event as OrmEvent

    h = auth_headers("demo", "demo")

    # Seed thresholds: lower=40, upper=90.
    # Seeded auto events: score 94 accepted, 92 accepted, 12 rejected, 78 queued(None).
    # Set lower=10, upper=80:
    # score 94 → >=80 → accepted (stays)
    # score 92 → >=80 → accepted (stays)
    # score 78 → between → queued (stays)
    # score 12 → 12>10 → between → queued (was rejected → moves)
    r = client.put(
        "/api/thresholds",
        json={"lowerThreshold": 10, "upperThreshold": 80},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["eventsMoved"] == 1  # score 12 moves rejected→queued

    # Now set upper=95 so the score-94 and score-92 events go from accepted → queued
    r = client.put(
        "/api/thresholds",
        json={"lowerThreshold": 10, "upperThreshold": 95},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["eventsMoved"] == 2  # 94 and 92 move to queued


def test_save_thresholds_does_not_touch_user_decisions(client, auth_headers):
    """User-decided events are not moved when thresholds change."""
    h = auth_headers("demo", "demo")

    # User-accept the queued event (score 78)
    queued = client.get("/api/events?status=queued", headers=h).json()
    eid = queued[0]["id"]
    client.post(f"/api/events/{eid}/decision", json={"decision": "accepted"}, headers=h)

    # Now set upper=95 — score 78 would normally be queued, but user decided it
    r = client.put(
        "/api/thresholds",
        json={"lowerThreshold": 10, "upperThreshold": 95},
        headers=h,
    )
    assert r.status_code == 200
    # The user-accepted event must stay accepted
    events = client.get("/api/events", headers=h).json()
    match = [e for e in events if e["id"] == eid]
    assert match[0]["status"] == "accepted"
    assert match[0]["decidedBy"] == "user"


def test_save_thresholds_response_includes_events_moved(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.put(
        "/api/thresholds",
        json={"lowerThreshold": 40, "upperThreshold": 90},
        headers=h,
    )
    assert r.status_code == 200
    assert "eventsMoved" in r.json()


def test_get_thresholds_no_auth_returns_401(client):
    r = client.get("/api/thresholds")
    assert r.status_code == 401
