"""Tests for GET /api/events and POST /api/events/{id}/decision."""

from __future__ import annotations

from unittest.mock import patch

from app.models import EventStatus


def test_list_events_returns_all_seeded(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.get("/api/events", headers=h)
    assert r.status_code == 200
    events = r.json()
    assert len(events) == 4  # 2 accepted + 1 rejected + 1 queued


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


def test_triage_exact_boundaries(_db_session):
    """Scores at boundaries: demo user has 90/40 thresholds.
    90 = upper → accepted; 40 = lower → rejected; between → queued."""
    from app.orm import User, Event as OrmEvent
    user = _db_session.query(User).filter(User.username == "demo").first()

    cases = [
        (40, "rejected"),    # = lower_threshold → <=, rejected
        (41, "queued"),      # between thresholds
        (90, "accepted"),    # = upper_threshold → >=, accepted
        (89, "queued"),      # between thresholds
        (39, "rejected"),    # < lower_threshold
    ]
    for score_val, expected_status in cases:
        evt = OrmEvent(
            user_id=user.id,
            title=f"Boundary {score_val}",
            date_time="2026-10-20T20:00:00",
            place="Berlin",
            link=f"https://example.com/boundary-{score_val}",
            description="test",
            score=score_val,
            score_reason=f"stub score {score_val}",
            status=expected_status,
            decided_by="auto" if expected_status != "queued" else None,
            city="Berlin",
            country="DE",
        )
        _db_session.add(evt)
    _db_session.commit()

    # Verify the seeded events have correct status
    for score_val, expected_status in cases:
        evt = _db_session.query(OrmEvent).filter(
            OrmEvent.link == f"https://example.com/boundary-{score_val}",
        ).first()
        assert evt.status == expected_status, f"score={score_val}: expected {expected_status}"


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


def test_invalid_status_filter_returns_400(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.get("/api/events?status=bogus", headers=h)
    assert r.status_code == 400
    assert "detail" in r.json()


def test_valid_status_filter_still_works(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.get("/api/events?status=accepted", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_events_no_auth_returns_401(client):
    r = client.get("/api/events")
    assert r.status_code == 401


def test_decide_event_no_auth_returns_401(client):
    r = client.post("/api/events/some-id/decision", json={"decision": "accepted"})
    assert r.status_code == 401


def test_decide_new_event_returns_400(client, auth_headers, _db_session):
    """Events in 'new' status are not decidable — only queued and accepted are."""
    from app.orm import User, Event as OrmEvent

    h = auth_headers("demo", "demo")
    user = _db_session.query(User).filter(User.username == "demo").first()
    new_evt = OrmEvent(
        user_id=user.id,
        title="Still new",
        date_time="2026-01-01T00:00:00",
        place="P",
        link="https://example.com/still-new",
        description="d",
        status="new",
    )
    _db_session.add(new_evt)
    _db_session.commit()

    r = client.post(
        f"/api/events/{new_evt.id}/decision",
        json={"decision": "accepted"},
        headers=h,
    )
    assert r.status_code == 400


def test_decide_event_other_users_event_returns_404(client, auth_headers, _db_session):
    """User A cannot decide user B's queued event."""
    from app.orm import User, Event as OrmEvent

    h_a = auth_headers("userA", "pw")
    h_b = auth_headers("userB", "pw")

    # Directly seed an event for user B
    user_b = _db_session.query(User).filter(User.username == "userB").first()
    evt = OrmEvent(
        user_id=user_b.id,
        title="B's event",
        date_time="2026-10-20T20:00:00",
        place="Berlin",
        link="https://example.com/user-b-event",
        description="User B event",
        score=60,
        score_reason="Test event in Berlin on 20 Oct",
        status="queued",
        city="Berlin",
        country="DE",
    )
    _db_session.add(evt)
    _db_session.commit()

    r = client.post(
        f"/api/events/{evt.id}/decision",
        json={"decision": "accepted"},
        headers=h_a,
    )
    assert r.status_code == 404


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


def test_decided_by_auto_on_triage(client, auth_headers):
    """Pipeline triage sets decidedBy='auto' for accepted and rejected events."""
    h = auth_headers("demo", "demo")
    events = client.get("/api/events", headers=h).json()
    for e in events:
        if e["status"] in ("accepted", "rejected"):
            assert e["decidedBy"] == "auto", f"event {e['id']} status={e['status']} decidedBy={e['decidedBy']}"
        elif e["status"] == "queued":
            assert e["decidedBy"] is None


def test_decided_by_user_on_decision(client, auth_headers):
    """User decision sets decidedBy='user'."""
    h = auth_headers("demo", "demo")
    queued = client.get("/api/events?status=queued", headers=h).json()
    eid = queued[0]["id"]
    r = client.post(f"/api/events/{eid}/decision", json={"decision": "accepted"}, headers=h)
    assert r.status_code == 200
    assert r.json()["decidedBy"] == "user"


def test_decided_by_user_on_reject(client, auth_headers):
    """User rejection sets decidedBy='user'."""
    h = auth_headers("demo", "demo")
    queued = client.get("/api/events?status=queued", headers=h).json()
    eid = queued[0]["id"]
    r = client.post(f"/api/events/{eid}/decision", json={"decision": "rejected"}, headers=h)
    assert r.status_code == 200
    assert r.json()["decidedBy"] == "user"


# --- #71: on-read fallback keeps unknown zones naive, resolves country zones ---

def test_api_unknown_zone_stays_naive(client, auth_headers, _db_session):
    """Legacy row with start_tz NULL and country ZZ keeps naive dateTime in the API."""
    from app.orm import User, Event as OrmEvent

    h = auth_headers("demo", "demo")
    user = _db_session.query(User).filter(User.username == "demo").first()
    evt = OrmEvent(
        user_id=user.id,
        title="Unknown zone event",
        date_time="2026-10-22T19:00:00",
        place="Somewhere",
        link="https://example.com/unknown-zone-api",
        description="No zone",
        score=80,
        score_reason="OK",
        status="queued",
        start_tz=None,
        city="",
        country="ZZ",
    )
    _db_session.add(evt)
    _db_session.commit()

    events = client.get("/api/events?status=queued", headers=h).json()
    match = [e for e in events if e["title"] == "Unknown zone event"]
    assert len(match) == 1
    # dateTime must stay naive — no offset appended
    assert match[0]["dateTime"] == "2026-10-22T19:00:00"
    assert match[0]["startTz"] is None


def test_api_country_zone_gets_offset(client, auth_headers, _db_session):
    """Legacy row with start_tz NULL but country DE gets the Europe/Berlin offset."""
    from app.orm import User, Event as OrmEvent

    h = auth_headers("demo", "demo")
    user = _db_session.query(User).filter(User.username == "demo").first()
    evt = OrmEvent(
        user_id=user.id,
        title="Country zone event",
        date_time="2026-10-22T19:00:00",
        place="Berlin",
        link="https://example.com/country-zone-api",
        description="Country resolves",
        score=85,
        score_reason="Good",
        status="queued",
        start_tz=None,
        city="Berlin",
        country="DE",
    )
    _db_session.add(evt)
    _db_session.commit()

    events = client.get("/api/events?status=queued", headers=h).json()
    match = [e for e in events if e["title"] == "Country zone event"]
    assert len(match) == 1
    # October 22 in Europe/Berlin is CEST (+02:00)
    assert match[0]["dateTime"] == "2026-10-22T19:00:00+02:00"


# --- #94: past events hidden from list and ICS feed ---


def test_past_timed_event_hidden(client, auth_headers, _db_session):
    """A timed event whose start is before now is hidden from the API."""
    from app.orm import User, Event as OrmEvent

    h = auth_headers("demo", "demo")
    user = _db_session.query(User).filter(User.username == "demo").first()
    # FAKE_NOW is 2026-10-18T12:00 CEST → 10:00 UTC
    # This event started at 08:00 CEST → already past at 12:00 CEST
    past = OrmEvent(
        user_id=user.id,
        title="Morning conference",
        date_time="2026-10-18T08:00",
        place="Berlin",
        link="https://example.com/past-timed",
        description="Past timed event",
        score=92,
        score_reason="Fits well",
        status="accepted",
        decided_by="auto",
        start_tz="Europe/Berlin",
        city="Berlin",
        country="DE",
    )
    _db_session.add(past)
    _db_session.commit()

    events = client.get("/api/events", headers=h).json()
    titles = [e["title"] for e in events]
    assert "Morning conference" not in titles


def test_past_dateonly_event_hidden(client, auth_headers, _db_session):
    """A date-only event whose whole day is over is hidden."""
    from app.orm import User, Event as OrmEvent

    h = auth_headers("demo", "demo")
    user = _db_session.query(User).filter(User.username == "demo").first()
    # FAKE_NOW is 2026-10-18 → date 2026-10-17 is yesterday
    past = OrmEvent(
        user_id=user.id,
        title="Yesterday festival",
        date_time="2026-10-17",
        place="Berlin",
        link="https://example.com/past-dateonly",
        description="Past date-only event",
        score=88,
        score_reason="Fits",
        status="accepted",
        decided_by="auto",
        start_tz="Europe/Berlin",
        city="Berlin",
        country="DE",
    )
    _db_session.add(past)
    _db_session.commit()

    events = client.get("/api/events", headers=h).json()
    titles = [e["title"] for e in events]
    assert "Yesterday festival" not in titles


def test_today_timed_event_in_future_shown(client, auth_headers, _db_session):
    """A timed event later today is still shown."""
    from app.orm import User, Event as OrmEvent

    h = auth_headers("demo", "demo")
    user = _db_session.query(User).filter(User.username == "demo").first()
    # FAKE_NOW is 2026-10-18T12:00 CEST → this event at 14:00 is still future
    future = OrmEvent(
        user_id=user.id,
        title="Afternoon concert",
        date_time="2026-10-18T14:00",
        place="Berlin",
        link="https://example.com/today-future",
        description="Today but future",
        score=95,
        score_reason="Fits perfectly",
        status="accepted",
        decided_by="auto",
        start_tz="Europe/Berlin",
        city="Berlin",
        country="DE",
    )
    _db_session.add(future)
    _db_session.commit()

    events = client.get("/api/events", headers=h).json()
    titles = [e["title"] for e in events]
    assert "Afternoon concert" in titles


def test_past_events_hidden_from_ics_feed(client, _db_session):
    """Past events are excluded from the ICS calendar feed."""
    from app.orm import User, Event as OrmEvent

    user = _db_session.query(User).filter(User.username == "demo").first()
    past = OrmEvent(
        user_id=user.id,
        title="Past ICS event",
        date_time="2026-10-10T20:00",
        place="Berlin",
        link="https://example.com/past-ics",
        description="Past event for ICS",
        score=92,
        score_reason="OK",
        status="accepted",
        decided_by="auto",
        start_tz="Europe/Berlin",
        city="Berlin",
        country="DE",
    )
    _db_session.add(past)
    _db_session.commit()

    r = client.get(f"/api/calendar/{user.ics_token}")
    assert r.status_code == 200
    body = r.text
    assert "Past ICS event" not in body
    # Future accepted events should still be present
    assert "Jazz Trio at A-Trane" in body
