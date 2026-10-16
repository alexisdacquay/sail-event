"""Tests for GET /api/events and POST /api/events/{id}/decision."""

from __future__ import annotations


def test_list_events_returns_all_seeded(client):
    r = client.get("/api/events")
    assert r.status_code == 200
    events = r.json()
    assert len(events) == 8


def test_list_events_filter_by_status(client):
    r = client.get("/api/events?status=queued")
    assert r.status_code == 200
    events = r.json()
    assert len(events) > 0
    assert all(e["status"] == "queued" for e in events)

    r = client.get("/api/events?status=accepted")
    assert r.status_code == 200
    assert all(e["status"] == "accepted" for e in r.json())


def test_decide_event_accept_queued(client):
    queued = client.get("/api/events?status=queued").json()
    assert len(queued) > 0
    eid = queued[0]["id"]

    r = client.post(f"/api/events/{eid}/decision", json={"decision": "accepted"})
    assert r.status_code == 200
    assert r.json()["status"] == "accepted"


def test_decide_event_reject_queued(client):
    queued = client.get("/api/events?status=queued").json()
    eid = queued[0]["id"]

    r = client.post(f"/api/events/{eid}/decision", json={"decision": "rejected"})
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_decide_event_reject_accepted(client):
    accepted = client.get("/api/events?status=accepted").json()
    assert len(accepted) > 0
    eid = accepted[0]["id"]

    r = client.post(f"/api/events/{eid}/decision", json={"decision": "rejected"})
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_decide_event_accept_already_accepted_is_noop(client):
    accepted = client.get("/api/events?status=accepted").json()
    eid = accepted[0]["id"]

    r = client.post(f"/api/events/{eid}/decision", json={"decision": "accepted"})
    assert r.status_code == 200
    assert r.json()["status"] == "accepted"


def test_decide_event_rejected_returns_400(client):
    # First, reject a queued event
    queued = client.get("/api/events?status=queued").json()
    eid = queued[0]["id"]
    client.post(f"/api/events/{eid}/decision", json={"decision": "rejected"})

    # Now try to change it
    r = client.post(f"/api/events/{eid}/decision", json={"decision": "accepted"})
    assert r.status_code == 400


def test_decide_event_not_found_returns_404(client):
    r = client.post(
        "/api/events/nonexistent-id/decision",
        json={"decision": "accepted"},
    )
    assert r.status_code == 404


def test_decide_event_invalid_body_returns_400(client):
    queued = client.get("/api/events?status=queued").json()
    eid = queued[0]["id"]
    r = client.post(f"/api/events/{eid}/decision", json={})
    assert r.status_code == 400
