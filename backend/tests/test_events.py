"""Tests for GET /api/events and POST /api/events/{id}/decision."""

from __future__ import annotations

from unittest.mock import patch

from app.adapters.base import RawEvent
from app.models import EventStatus


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


def test_decide_event_invalid_decision_value_returns_400(client):
    queued = client.get("/api/events?status=queued").json()
    eid = queued[0]["id"]
    r = client.post(f"/api/events/{eid}/decision", json={"decision": "maybe"})
    assert r.status_code == 400


def test_triage_exact_boundaries(client):
    """Scores 30 and 70 → queued; 71 → accepted; 29 → rejected."""
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
            patch("app.routers.search.get_search_provider") as mock_sp,
            patch("app.routers.search.get_scorer") as mock_sc,
        ):
            mock_sp.return_value.search.return_value = [raw]
            mock_sc.return_value.score.side_effect = fake_score
            r = client.post("/api/search")
            assert r.status_code == 200

        events = client.get(f"/api/events").json()
        matched = [e for e in events if e["link"] == raw.link]
        assert len(matched) == 1, f"score={score_val}: expected 1 event, got {len(matched)}"
        assert matched[0]["status"] == expected_status.value, (
            f"score={score_val}: expected {expected_status.value}, got {matched[0]['status']}"
        )


def test_rejected_event_survives_later_search(client):
    """A rejected event is never overwritten by a later search run."""
    # Reject a queued event
    queued = client.get("/api/events?status=queued").json()
    eid = queued[0]["id"]
    link = queued[0]["link"]
    client.post(f"/api/events/{eid}/decision", json={"decision": "rejected"})

    # Run search again — the rejected event must stay rejected
    client.post("/api/search")

    events = client.get("/api/events").json()
    matched = [e for e in events if e["id"] == eid]
    assert len(matched) == 1
    assert matched[0]["status"] == "rejected"


def test_filter_rejected_returns_only_rejected(client):
    # Reject a queued event first to ensure at least one rejected exists
    queued = client.get("/api/events?status=queued").json()
    eid = queued[0]["id"]
    client.post(f"/api/events/{eid}/decision", json={"decision": "rejected"})

    r = client.get("/api/events?status=rejected")
    assert r.status_code == 200
    rejected = r.json()
    assert len(rejected) >= 1
    assert all(e["status"] == "rejected" for e in rejected)
