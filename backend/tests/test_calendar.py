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


# --- carry-over and audit tests ---

def test_bad_date_time_logs_warning(client, _db_session, caplog):
    import logging
    from app.orm import User

    user = _db_session.query(User).filter(User.username == "demo").first()
    bad = Event(
        user_id=user.id,
        title="Bad date caplog",
        date_time="not-a-date",
        place="Nowhere",
        link="https://example.com/bad-date-caplog",
        description="desc",
        score=99,
        status="accepted",
    )
    _db_session.add(bad)
    _db_session.commit()

    with caplog.at_level(logging.WARNING, logger="app.routers.calendar"):
        client.get("/api/calendar/demo-ics-token")

    assert any("unparseable date_time" in m for m in caplog.messages)


def test_dtstamp_equals_created_at(client, _db_session):
    from app.orm import User

    user = _db_session.query(User).filter(User.username == "demo").first()
    evt = Event(
        user_id=user.id,
        title="Known created_at",
        date_time="2026-11-07T10:00:00",
        place="Here",
        link="https://example.com/dtstamp-test",
        description="d",
        score=99,
        status="accepted",
    )
    _db_session.add(evt)
    _db_session.commit()
    _db_session.refresh(evt)
    # ICS DTSTAMP drops microseconds; compare at second resolution
    expected = evt.created_at.replace(microsecond=0)

    r = client.get("/api/calendar/demo-ics-token")
    cal = Calendar.from_ical(r.content)
    for c in cal.walk():
        if c.name == "VEVENT" and str(c["UID"]) == f"{evt.id}@sail-event":
            got = c["DTSTAMP"].dt.replace(tzinfo=None)
            assert got == expected
            break
    else:
        raise AssertionError("VEVENT not found")


def test_calendar_content_type_full_value(client):
    r = client.get("/api/calendar/demo-ics-token")
    assert r.headers["content-type"] == "text/calendar; charset=utf-8"


# --- POST /api/calendar/rotate ---

def test_rotate_returns_new_url(client, auth_headers):
    headers = auth_headers("demo", "demo")
    r = client.post("/api/calendar/rotate", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "url" in body
    assert "/api/calendar/" in body["url"]
    assert "demo-ics-token" not in body["url"]


def test_old_token_404_after_rotate(client, auth_headers):
    headers = auth_headers("demo", "demo")
    client.post("/api/calendar/rotate", headers=headers)
    r = client.get("/api/calendar/demo-ics-token")
    assert r.status_code == 404


def test_new_token_200_after_rotate(client, auth_headers):
    headers = auth_headers("demo", "demo")
    rotate_resp = client.post("/api/calendar/rotate", headers=headers)
    new_url = rotate_resp.json()["url"]
    new_token = new_url.split("/api/calendar/")[-1]
    r = client.get(f"/api/calendar/{new_token}")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/calendar")


def test_rotate_unauthenticated(client):
    r = client.post("/api/calendar/rotate")
    assert r.status_code == 401


def test_calendar_feed_freshly_registered_user(client, auth_headers):
    h = auth_headers("caluser", "pw")
    r = client.get("/api/calendar-url", headers=h)
    ics_token = r.json()["url"].split("/api/calendar/")[-1]

    r2 = client.get(f"/api/calendar/{ics_token}")
    assert r2.status_code == 200
    cal = Calendar.from_ical(r2.content)
    assert cal["VERSION"] == "2.0"
    vevents = [c for c in cal.walk() if c.name == "VEVENT"]
    assert len(vevents) == 0


# --- #71: DTSTART carries TZID or DATE ---

def test_ics_dtstart_has_tzid_when_start_tz_set(client, _db_session):
    """Timed events with start_tz get DTSTART;TZID=<tz> in the ICS feed."""
    r = client.get("/api/calendar/demo-ics-token")
    cal = Calendar.from_ical(r.content)

    ve = [c for c in cal.walk() if c.name == "VEVENT"][0]
    dtstart_prop = ve.get("DTSTART")
    # The TZID parameter should be set
    assert dtstart_prop.params.get("TZID") == "Europe/Berlin"
    # The value is a naive datetime (local in the TZID zone), not UTC
    dt = dtstart_prop.dt
    assert dt.tzinfo is None or "Berlin" in str(dt.tzinfo)


def test_ics_date_only_uses_value_date(client, _db_session):
    """Date-only events get DTSTART;VALUE=DATE in the ICS feed."""
    from app.orm import User

    user = _db_session.query(User).filter(User.username == "demo").first()
    evt = Event(
        user_id=user.id,
        title="Date only fest",
        date_time="2026-10-22",
        place="Berlin",
        link="https://example.com/date-only-ics",
        description="All-day event",
        score=95,
        score_reason="Fits perfectly",
        status="accepted",
        start_tz=None,
        city="Berlin",
        country="DE",
    )
    _db_session.add(evt)
    _db_session.commit()

    r = client.get("/api/calendar/demo-ics-token")
    cal = Calendar.from_ical(r.content)
    for c in cal.walk():
        if c.name == "VEVENT" and str(c["UID"]) == f"{evt.id}@sail-event":
            from datetime import date as date_type
            assert isinstance(c["DTSTART"].dt, date_type)
            assert not isinstance(c["DTSTART"].dt, datetime)
            assert c["DTSTART"].dt.isoformat() == "2026-10-22"
            break
    else:
        raise AssertionError("Date-only VEVENT not found")


def test_ics_naive_row_fallback(client, _db_session):
    """Pre-#71 naive rows with start_tz still get TZID in the ICS feed."""
    from app.orm import User

    user = _db_session.query(User).filter(User.username == "demo").first()
    # Simulate a pre-#71 naive row
    evt = Event(
        user_id=user.id,
        title="Legacy naive event",
        date_time="2026-10-22T19:00:00",  # no offset
        place="Berlin",
        link="https://example.com/naive-ics",
        description="Legacy row",
        score=90,
        score_reason="Good",
        status="accepted",
        start_tz="Europe/Berlin",
        city="Berlin",
        country="DE",
    )
    _db_session.add(evt)
    _db_session.commit()

    r = client.get("/api/calendar/demo-ics-token")
    cal = Calendar.from_ical(r.content)
    for c in cal.walk():
        if c.name == "VEVENT" and str(c["UID"]) == f"{evt.id}@sail-event":
            dtstart_prop = c.get("DTSTART")
            assert dtstart_prop.params.get("TZID") == "Europe/Berlin"
            # The local time should be 19:00 (unchanged — the naive value IS the local time)
            assert dtstart_prop.dt.hour == 19
            break
    else:
        raise AssertionError("Legacy naive VEVENT not found")


def test_ics_unknown_zone_stays_floating(client, _db_session):
    """Legacy row with start_tz NULL and country ZZ stays floating, not UTC."""
    from app.orm import User

    user = _db_session.query(User).filter(User.username == "demo").first()
    evt = Event(
        user_id=user.id,
        title="Unknown zone event",
        date_time="2026-10-22T19:00:00",
        place="Somewhere",
        link="https://example.com/unknown-zone-ics",
        description="No zone info",
        score=80,
        score_reason="OK",
        status="accepted",
        start_tz=None,
        city="",
        country="ZZ",
    )
    _db_session.add(evt)
    _db_session.commit()

    r = client.get("/api/calendar/demo-ics-token")
    cal = Calendar.from_ical(r.content)
    for c in cal.walk():
        if c.name == "VEVENT" and str(c["UID"]) == f"{evt.id}@sail-event":
            dtstart_prop = c.get("DTSTART")
            # No TZID parameter — floating local time
            assert "TZID" not in dtstart_prop.params
            # Time is 19:00, not shifted
            assert dtstart_prop.dt.hour == 19
            # No timezone — naive
            assert dtstart_prop.dt.tzinfo is None
            break
    else:
        raise AssertionError("Unknown-zone VEVENT not found")


def test_ics_country_zone_uses_iana_tzid(client, _db_session):
    """Legacy row with start_tz NULL but single-zone country gets IANA TZID."""
    from app.orm import User

    user = _db_session.query(User).filter(User.username == "demo").first()
    evt = Event(
        user_id=user.id,
        title="Country zone event",
        date_time="2026-10-22T19:00:00",
        place="Berlin",
        link="https://example.com/country-zone-ics",
        description="Country DE resolves to Europe/Berlin",
        score=85,
        score_reason="Good",
        status="accepted",
        start_tz=None,
        city="Berlin",
        country="DE",
    )
    _db_session.add(evt)
    _db_session.commit()

    r = client.get("/api/calendar/demo-ics-token")
    cal = Calendar.from_ical(r.content)
    for c in cal.walk():
        if c.name == "VEVENT" and str(c["UID"]) == f"{evt.id}@sail-event":
            dtstart_prop = c.get("DTSTART")
            # IANA TZID from country table, not a pseudo-TZID like "UTC+02:00"
            assert dtstart_prop.params.get("TZID") == "Europe/Berlin"
            assert dtstart_prop.dt.hour == 19
            break
    else:
        raise AssertionError("Country-zone VEVENT not found")
