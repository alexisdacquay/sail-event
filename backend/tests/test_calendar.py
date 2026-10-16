"""Tests for GET /api/calendar/{ics_token} and GET /api/calendar-url."""

from __future__ import annotations

from datetime import datetime, timedelta

from icalendar import Calendar

from app.orm import Event


def test_calendar_feed_valid_token(client, _db_session):
    r = client.get("/api/calendar/demo-ics-token")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/calendar")

    cal = Calendar.from_ical(r.content)
    assert cal["VERSION"] == "2.0"
    assert cal["PRODID"] == "-//sail-event//EN"
    assert "Sail-event — demo" in cal["X-WR-CALNAME"]


def test_calendar_feed_contains_accepted_events_only(client, _db_session):
    r = client.get("/api/calendar/demo-ics-token")
    cal = Calendar.from_ical(r.content)

    vevents = [c for c in cal.walk() if c.name == "VEVENT"]
    accepted_count = _db_session.query(Event).filter(
        Event.status == "accepted",
    ).count()
    assert len(vevents) == accepted_count
    assert accepted_count > 0  # sanity: fixture data has at least one


def test_calendar_feed_vevent_fields(client, _db_session):
    r = client.get("/api/calendar/demo-ics-token")
    cal = Calendar.from_ical(r.content)

    ve = [c for c in cal.walk() if c.name == "VEVENT"][0]
    uid = str(ve["UID"])
    assert uid.endswith("@sail-event")

    assert ve["SUMMARY"]
    assert ve["LOCATION"]
    assert ve["URL"]
    assert ve["DESCRIPTION"]
    assert ve["DTSTAMP"]

    dtstart = ve["DTSTART"].dt
    dtend = ve["DTEND"].dt
    assert dtend - dtstart == timedelta(hours=2)


def test_calendar_feed_description_with_score_reason(client, _db_session):
    """DESCRIPTION = description + newline + score_reason when present."""
    r = client.get("/api/calendar/demo-ics-token")
    cal = Calendar.from_ical(r.content)

    ve = [c for c in cal.walk() if c.name == "VEVENT"][0]
    desc = str(ve["DESCRIPTION"])
    # The accepted fixture events have score_reason set
    assert "\n" in desc


def test_calendar_feed_unknown_token_returns_404(client):
    r = client.get("/api/calendar/nonexistent-token")
    assert r.status_code == 404
    assert r.json()["detail"] == "Not found"


def test_empty_feed_for_user_with_no_accepted_events(client, _db_session):
    """User with zero accepted events gets a valid empty calendar."""
    # Reject all accepted events for demo user
    accepted = _db_session.query(Event).filter(Event.status == "accepted").all()
    for evt in accepted:
        evt.status = "rejected"
    _db_session.commit()

    r = client.get("/api/calendar/demo-ics-token")
    assert r.status_code == 200
    cal = Calendar.from_ical(r.content)
    vevents = [c for c in cal.walk() if c.name == "VEVENT"]
    assert len(vevents) == 0


def test_bad_date_time_skipped(client, _db_session):
    """An event with unparseable date_time is silently skipped."""
    from app.orm import User

    user = _db_session.query(User).filter(User.username == "demo").first()
    bad_evt = Event(
        user_id=user.id,
        title="Bad date event",
        date_time="not-a-date",
        place="Nowhere",
        link="https://example.com/bad-date-unique",
        description="desc",
        score=99,
        score_reason=None,
        status="accepted",
    )
    _db_session.add(bad_evt)
    _db_session.commit()

    r = client.get("/api/calendar/demo-ics-token")
    assert r.status_code == 200
    cal = Calendar.from_ical(r.content)
    uids = [str(c["UID"]) for c in cal.walk() if c.name == "VEVENT"]
    assert f"{bad_evt.id}@sail-event" not in uids


def test_rejected_event_removed_from_feed(client, _db_session):
    """Rejecting an accepted event removes it from the next feed GET."""
    # Find an accepted event
    accepted = _db_session.query(Event).filter(Event.status == "accepted").first()
    event_id = accepted.id

    # Verify it's in the feed
    r = client.get("/api/calendar/demo-ics-token")
    cal = Calendar.from_ical(r.content)
    uids = [str(c["UID"]) for c in cal.walk() if c.name == "VEVENT"]
    assert f"{event_id}@sail-event" in uids

    # Reject it
    accepted.status = "rejected"
    _db_session.commit()

    # Verify it's gone
    r = client.get("/api/calendar/demo-ics-token")
    cal = Calendar.from_ical(r.content)
    uids = [str(c["UID"]) for c in cal.walk() if c.name == "VEVENT"]
    assert f"{event_id}@sail-event" not in uids


def test_description_without_score_reason(client, _db_session):
    """When score_reason is None, DESCRIPTION is just the description text."""
    from app.orm import User

    user = _db_session.query(User).filter(User.username == "demo").first()
    evt = Event(
        user_id=user.id,
        title="No reason event",
        date_time="2026-11-07T10:00:00",
        place="Here",
        link="https://example.com/no-reason-unique",
        description="Just the description",
        score=99,
        score_reason=None,
        status="accepted",
    )
    _db_session.add(evt)
    _db_session.commit()

    r = client.get("/api/calendar/demo-ics-token")
    cal = Calendar.from_ical(r.content)
    for c in cal.walk():
        if c.name == "VEVENT" and str(c["UID"]) == f"{evt.id}@sail-event":
            assert str(c["DESCRIPTION"]) == "Just the description"
            break
    else:
        raise AssertionError("VEVENT not found")


# --- GET /api/calendar-url ---

def test_calendar_url_authenticated(client, auth_headers):
    headers = auth_headers("demo", "demo")
    r = client.get("/api/calendar-url", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "url" in body
    assert "/api/calendar/" in body["url"]
    assert "demo-ics-token" in body["url"]


def test_calendar_url_unauthenticated(client):
    r = client.get("/api/calendar-url")
    assert r.status_code == 401
