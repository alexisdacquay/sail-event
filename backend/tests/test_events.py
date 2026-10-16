"""Tests for GET /api/events and POST /api/events/{id}/decision."""

from __future__ import annotations

from unittest.mock import patch

from app.adapters.base import RawEvent
from app.models import EventStatus


def test_list_events_returns_all_seeded(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.get("/api/events", headers=h)
    assert r.status_code == 200
    events = r.json()
    assert len(events) == 8


def test_list_events_filter_by_status(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.get("/api/events?status=queued", headers=h)
    assert r.status_code == 200
    events = r.json()
    assert len(events) > 0
    assert all(e["status"] == "queued" for e in events)

    r = client.get("/api/events?status=accepted", headers=h)
    assert r.status_code == 200
    assert all(e["status"] == "accepted" for e in r.json())


def test_decide_event_accept_queued(client, auth_headers):
    h = auth_headers("demo", "demo")
    queued = client.get("/api/events?status=queued", headers=h).json()
    assert len(queued) > 0
    eid = queued[0]["id"]

    r = client.post(f"/api/events/{eid}/decision", json={"decision": "accepted"}, headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "accepted"


def test_decide_event_reject_queued(client, auth_headers):
    h = auth_headers("demo", "demo")
    queued = client.get("/api/events?status=queued", headers=h).json()
    eid = queued[0]["id"]

    r = client.post(f"/api/events/{eid}/decision", json={"decision": "rejected"}, headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_decide_event_reject_accepted(client, auth_headers):
    h = auth_headers("demo", "demo")
    accepted = client.get("/api/events?status=accepted", headers=h).json()
    assert len(accepted) > 0
    eid = accepted[0]["id"]

    r = client.post(f"/api/events/{eid}/decision", json={"decision": "rejected"}, headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_decide_event_accept_already_accepted_is_noop(client, auth_headers):
    h = auth_headers("demo", "demo")
    accepted = client.get("/api/events?status=accepted", headers=h).json()
    eid = accepted[0]["id"]

    r = client.post(f"/api/events/{eid}/decision", json={"decision": "accepted"}, headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "accepted"


def test_decide_event_rejected_returns_400(client, auth_headers):
    h = auth_headers("demo", "demo")
    # First, reject a queued event
    queued = client.get("/api/events?status=queued", headers=h).json()
    eid = queued[0]["id"]
    client.post(f"/api/events/{eid}/decision", json={"decision": "rejected"}, headers=h)

    # Now try to change it
    r = client.post(f"/api/events/{eid}/decision", json={"decision": "accepted"}, headers=h)
    assert r.status_code == 400


def test_decide_event_not_found_returns_404(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.post(
        "/api/events/nonexistent-id/decision",
        json={"decision": "accepted"},
        headers=h,
    )
    assert r.status_code == 404


def test_decide_event_invalid_body_returns_400(client, auth_headers):
    h = auth_headers("demo", "demo")
    queued = client.get("/api/events?status=queued", headers=h).json()
    eid = queued[0]["id"]
    r = client.post(f"/api/events/{eid}/decision", json={}, headers=h)
    assert r.status_code == 400


def test_decide_event_invalid_decision_value_returns_400(client, auth_headers):
    h = auth_headers("demo", "demo")
    queued = client.get("/api/events?status=queued", headers=h).json()
    eid = queued[0]["id"]
    r = client.post(f"/api/events/{eid}/decision", json={"decision": "maybe"}, headers=h)
    assert r.status_code == 400


def test_triage_exact_boundaries(client, auth_headers):
    """Scores 30 and 70 -> queued; 71 -> accepted; 29 -> rejected."""
    h = auth_headers("demo", "demo")
    _raw = RawEvent(
        title="x", date_time="2026-01-01T00:00:00",
        place="p", link="https://example.com/boundary-{score}",
        description="d",
    )
    cases = [
        (30, EventStatus.queued),
        (70, EventStatus.queued),
        (71, EventStatus.accepted),
        (29, EventStatus.rejected),
    ]
    for score_val, expected_status in cases:
        raw = _raw.model_copy(
            update={"link": f"https://example.com/boundary-{score_val}"}
        )

        def fake_score(event, criteria, _sv=score_val):
            return (_sv, f"stub score {_sv}")

        with (
            patch("app.services.pipeline.get_search_provider") as mock_sp,
            patch("app.services.pipeline.get_scorer") as mock_sc,
        ):
            mock_sp.return_value.search.return_value = [raw]
            mock_sc.return_value.score.side_effect = fake_score
            r = client.post("/api/search", headers=h)
            assert r.status_code == 200

        events = client.get("/api/events", headers=h).json()
        matched = [e for e in events if e["link"] == raw.link]
        assert len(matched) == 1, f"score={score_val}: expected 1 event, got {len(matched)}"
        assert matched[0]["status"] == expected_status.value, (
            f"score={score_val}: expected {expected_status.value}, got {matched[0]['status']}"
        )


def test_rejected_event_survives_later_search(client, auth_headers):
    """A rejected event is never overwritten by a later search run."""
    h = auth_headers("demo", "demo")
    # Reject a queued event
    queued = client.get("/api/events?status=queued", headers=h).json()
    eid = queued[0]["id"]
    link = queued[0]["link"]
    client.post(f"/api/events/{eid}/decision", json={"decision": "rejected"}, headers=h)

    # Run search again — the rejected event must stay rejected
    client.post("/api/search", headers=h)

    events = client.get("/api/events", headers=h).json()
    matched = [e for e in events if e["id"] == eid]
    assert len(matched) == 1
    assert matched[0]["status"] == "rejected"


def test_filter_rejected_returns_only_rejected(client, auth_headers):
    h = auth_headers("demo", "demo")
    # Reject a queued event first to ensure at least one rejected exists
    queued = client.get("/api/events?status=queued", headers=h).json()
    eid = queued[0]["id"]
    client.post(f"/api/events/{eid}/decision", json={"decision": "rejected"}, headers=h)

    r = client.get("/api/events?status=rejected", headers=h)
    assert r.status_code == 200
    rejected = r.json()
    assert len(rejected) >= 1
    assert all(e["status"] == "rejected" for e in rejected)


def test_list_events_no_auth_returns_401(client):
    r = client.get("/api/events")
    assert r.status_code == 401


def test_decide_event_no_auth_returns_401(client):
    r = client.post("/api/events/some-id/decision", json={"decision": "accepted"})
    assert r.status_code == 401


def test_user_isolation_events(client, auth_headers):
    """User A cannot see or decide user B's events."""
    h_a = auth_headers("alice", "pw1")
    h_b = auth_headers("bob", "pw2")

    # Alice has no events
    events_a = client.get("/api/events", headers=h_a).json()
    assert events_a == []

    # Demo has events; alice cannot see them
    h_demo = auth_headers("demo", "demo")
    events_demo = client.get("/api/events", headers=h_demo).json()
    assert len(events_demo) > 0

    eid = events_demo[0]["id"]
    # Alice trying to decide demo's event -> 404
    r = client.post(f"/api/events/{eid}/decision", json={"decision": "accepted"}, headers=h_a)
    assert r.status_code == 404
