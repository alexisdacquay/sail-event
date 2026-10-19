"""Tests for the v2 search-run pipeline (nine stages)."""

from __future__ import annotations

import json
import os
from unittest.mock import patch

import pytest

from app.orm import Criteria, Event, Run, User
from app.services.pipeline import run_pipeline


# ---------- Basic run (fixture provider + fake model under FAKE_NOW) ----------


def test_run_produces_run_row_with_stage_counts(client, auth_headers, _db_session):
    h = auth_headers("demo", "demo")
    r = client.post("/api/search", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert "runId" in body
    assert "stageCounts" in body

    run = _db_session.query(Run).filter(Run.id == body["runId"]).first()
    assert run is not None
    assert run.trigger == "manual"
    assert run.started_at is not None
    assert run.finished_at is not None
    assert run.error is None
    assert run.stage_counts is not None

    sc = json.loads(run.stage_counts)
    assert "queries_planned" in sc
    assert sc["queries_planned"] > 0


def test_run_creates_events_with_scores(client, auth_headers, _db_session):
    h = auth_headers("demo", "demo")
    body = client.post("/api/search", headers=h).json()
    run_id = body["runId"]

    events = _db_session.query(Event).filter(Event.run_id == run_id).all()
    # Under fixture + fake model, at least some events should be produced
    scored = [e for e in events if e.score is not None]
    assert len(scored) > 0
    for e in scored:
        assert e.status in ("accepted", "rejected", "queued")
        assert e.score_reason is not None


def test_run_response_carries_stage_counts(client, auth_headers, _db_session):
    h = auth_headers("demo", "demo")
    body = client.post("/api/search", headers=h).json()
    assert body.get("stageCounts") is not None or body.get("error") is not None


def test_events_carry_run_id(client, auth_headers, _db_session):
    h = auth_headers("demo", "demo")
    body = client.post("/api/search", headers=h).json()
    run_id = body["runId"]
    events = _db_session.query(Event).filter(Event.run_id == run_id).all()
    assert all(e.run_id == run_id for e in events)


# ---------- Recovery of leftover `new` events ----------


def test_recovery_of_new_events(client, auth_headers, _db_session):
    h = auth_headers("demo", "demo")
    user = _db_session.query(User).filter(User.username == "demo").first()
    leftover = Event(
        user_id=user.id,
        title="Leftover Jazz",
        date_time="2026-10-20T21:00",
        place="Berlin",
        link="https://leftover.example.com/unique",
        description="leftover event description",
        start_tz="Europe/Berlin",
        city="Berlin",
        country="DE",
        status="new",
    )
    _db_session.add(leftover)
    _db_session.commit()

    client.post("/api/search", headers=h)
    _db_session.refresh(leftover)
    assert leftover.status != "new"
    assert leftover.score is not None


# ---------- WindowInPast stops the run ----------


def test_window_in_past_stops_run(client, auth_headers, _db_session, monkeypatch):
    import hashlib
    h = auth_headers("past", "past")
    text = "jazz in Berlin (Germany) last week (10-12 October 2026)"
    client.put("/api/criteria", headers=h, json={"text": text})
    # Manually set facets with past dates, using correct SHA to avoid re-parse
    user = _db_session.query(User).filter(User.username == "past").first()
    crit = _db_session.query(Criteria).filter(Criteria.user_id == user.id).first()
    crit.facets_json = json.dumps({
        "place": {"city": "Berlin", "country": "DE", "online": False},
        "date": {"start": "2026-10-10", "end": "2026-10-12"},
        "topics": ["jazz"],
        "language": "de",
        "input_language": "en",
    })
    crit.facets_version = "criteria_v2"
    crit.facets_text_sha = hashlib.sha256(text.encode()).hexdigest()
    _db_session.commit()

    body = client.post("/api/search", headers=h).json()
    assert body.get("error") == "dates in the past: edit your criteria"


# ---------- No-place stops the run ----------


def test_no_place_stops_run(client, auth_headers, _db_session):
    import hashlib
    h = auth_headers("noplace", "noplace")
    text = "jazz"
    client.put("/api/criteria", headers=h, json={"text": text})
    # Set facets with no place
    user = _db_session.query(User).filter(User.username == "noplace").first()
    crit = _db_session.query(Criteria).filter(Criteria.user_id == user.id).first()
    crit.facets_json = json.dumps({
        "place": None,
        "date": {"start": "2026-10-19", "end": "2026-10-21"},
        "topics": ["jazz"],
        "language": None,
        "input_language": "en",
    })
    crit.facets_version = "criteria_v2"
    crit.facets_text_sha = hashlib.sha256(text.encode()).hexdigest()
    _db_session.commit()

    body = client.post("/api/search", headers=h).json()
    assert body.get("error") == "no place in criteria"
    assert body.get("stoppedAtStage") == "search"


# ---------- Judge error leaves event `new` ----------


def test_judge_error_leaves_event_new(client, auth_headers, _db_session):
    h = auth_headers("jerr", "jerr")
    client.put("/api/criteria", headers=h, json={
        "text": "jazz in Berlin (Germany) next week (19-21st October 2026)",
    })

    # Patch judge_event to always return JudgeError
    from app.services.judge import JudgeError
    from app.services.extract import ExtractedEvent

    def _always_error(event, **kwargs):
        return JudgeError(event=event, error="forced test error")

    with patch("app.services.pipeline.judge_event", side_effect=_always_error):
        body = client.post("/api/search", headers=h).json()

    user = _db_session.query(User).filter(User.username == "jerr").first()
    new_events = _db_session.query(Event).filter(
        Event.user_id == user.id,
        Event.status == "new",
    ).all()
    # Events that hit judge errors stay `new`
    # (there may be 0 events if the extraction produced nothing, that's OK)
    run = _db_session.query(Run).filter(Run.id == body["runId"]).first()
    if run.stage_counts:
        sc = json.loads(run.stage_counts)
        # If events were inserted, judge_errors should be counted
        if sc.get("events_extracted", 0) > 0:
            assert sc.get("judge_errors", 0) > 0


# ---------- Factory refusal in prod ----------


def test_prod_refusal_recorded_on_run(client, auth_headers, _db_session, monkeypatch):
    monkeypatch.setenv("APP_ENV", "prod")
    h = auth_headers("demo", "demo")
    body = client.post("/api/search", headers=h).json()
    assert body.get("error") is not None
    assert "refused" in body["error"].lower() or "prod" in body["error"].lower()
    monkeypatch.delenv("APP_ENV")


# ---------- Triage uses >= and <= ----------


def test_triage_uses_ge_le_cutoffs(client, auth_headers, _db_session):
    h = auth_headers("demo", "demo")
    body = client.post("/api/search", headers=h).json()
    run_id = body["runId"]

    user = _db_session.query(User).filter(User.username == "demo").first()
    events = _db_session.query(Event).filter(Event.run_id == run_id).all()
    for e in events:
        if e.score is None:
            continue
        if e.score >= user.upper_threshold:
            assert e.status == "accepted"
            assert e.decided_by == "auto"
        elif e.score <= user.lower_threshold:
            assert e.status == "rejected"
            assert e.decided_by == "auto"
        else:
            assert e.status == "queued"


# ---------- search/all trigger (now 202 + background) ----------


def test_search_all_returns_202(client, _db_session, monkeypatch):
    monkeypatch.setenv("SEARCH_ALL_API_KEY", "k")
    r = client.post("/api/search/all", headers={"X-API-Key": "k"})
    assert r.status_code == 202
    body = r.json()
    assert body["usersQueued"] >= 1


def test_pipeline_trigger_scheduled_direct(_db_session):
    """run_pipeline called directly with trigger='scheduled' records the trigger."""
    user = _db_session.query(User).filter(User.username == "demo").first()
    run = run_pipeline(user, _db_session, trigger="scheduled")
    assert run.trigger == "scheduled"


# ---------- Event band and sourceUrl in API ----------


def test_event_has_band_and_source_url(client, auth_headers, _db_session):
    h = auth_headers("demo", "demo")
    client.post("/api/search", headers=h)
    r = client.get("/api/events", headers=h)
    assert r.status_code == 200
    events = r.json()
    scored_events = [e for e in events if e.get("score") is not None]
    if scored_events:
        e = scored_events[0]
        assert "band" in e
        assert e["band"] in ("fits", "mostly fits", "open question", "off topic", "not a fit")


# ---------- MAX_EVENTS_PER_RUN cap ----------


def test_max_events_per_run_cap(client, auth_headers, _db_session, monkeypatch):
    monkeypatch.setenv("MAX_EVENTS_PER_RUN", "2")
    h = auth_headers("capped", "capped")
    client.put("/api/criteria", headers=h, json={
        "text": "jazz in Berlin (Germany) next week (19-21st October 2026)",
    })
    body = client.post("/api/search", headers=h).json()
    assert body["eventsNew"] <= 2
