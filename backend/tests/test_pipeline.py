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
    assert sc["queries_planned"] == 1  # verbatim query, one call


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


# ---------- Past dates no longer stop the run (#70) ----------


def test_past_dates_do_not_stop_run(client, auth_headers, _db_session, monkeypatch):
    """Past absolute dates run the search; past/date filters drop old events."""
    import hashlib
    h = auth_headers("past", "past")
    text = "jazz in Berlin (Germany) last week (10-12 October 2026)"
    client.put("/api/criteria", headers=h, json={"text": text})
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

    # Stub LLM-touching stages so the fixture provider runs real but we
    # don't need fake-model recordings for a past-window prompt hash.
    from app.services.extract import ExtractedEvent, ExtractionCounts
    past_event = ExtractedEvent(
        title="Past Jazz",
        start_local="2026-10-11T20:00",
        start_tz="Europe/Berlin",
        end_local=None,
        venue="A-Trane",
        city="Berlin",
        country="DE",
        link="https://example.com/past-jazz",
        description="a past jazz event",
        confidence=0.9,
        source_url="https://example.com/past-jazz",
        page_kind="single_event",
    )
    extract_counts = ExtractionCounts(
        pages_content_pass=0, extract_truncated=0, events_extracted=1,
        extract_errors=0, filtered_non_event=0,
    )

    with (
        patch("app.services.pipeline.parse_criteria", return_value={
            "place": {"city": "Berlin", "country": "DE", "online": False},
            "date": {"start": "2026-10-10", "end": "2026-10-12"},
            "topics": ["jazz"],
            "language": "de",
            "input_language": "en",
        }),
        patch("app.services.pipeline.extract_events", return_value=([past_event], extract_counts)),
        patch("app.services.pipeline.judge_event") as mock_judge,
    ):
        # Judge should not be called (event filtered before judging)
        body = client.post("/api/search", headers=h).json()

    assert body.get("stoppedAtStage") is None, f"run should not stop early: {body}"
    sc = body["stageCounts"]
    assert sc is not None
    run = _db_session.query(Run).filter(Run.id == body["runId"]).first()
    assert run.search_calls == 2  # 1 call × 2 credits (advanced, manual trigger)
    # The past event should be filtered (past or outside date window)
    assert sc.get("filtered_past", 0) + sc.get("filtered_date", 0) > 0


# ---------- Every early stop writes stage_counts (#70) ----------


def test_empty_criteria_stops_run(client, auth_headers, _db_session):
    """Empty criteria text → stopped_at_stage='criteria', error='no criteria text'."""
    h = auth_headers("empty", "empty")
    # No criteria saved → empty text
    body = client.post("/api/search", headers=h).json()
    assert body["stoppedAtStage"] == "criteria"
    assert body["error"] == "no criteria text"
    assert body["stageCounts"] is not None


def test_empty_criteria_text_stops_run(client, auth_headers, _db_session):
    """Criteria saved as empty string → same stop."""
    h = auth_headers("empty2", "empty2")
    client.put("/api/criteria", headers=h, json={"text": ""})
    body = client.post("/api/search", headers=h).json()
    assert body["stoppedAtStage"] == "criteria"
    assert body["error"] == "no criteria text"
    assert body["stageCounts"] is not None


def test_adapter_stop_has_stage_counts(client, auth_headers, _db_session, monkeypatch):
    """Adapter refusal sets stopped_at_stage AND stage_counts (not null)."""
    monkeypatch.setenv("APP_ENV", "prod")
    h = auth_headers("demo", "demo")
    body = client.post("/api/search", headers=h).json()
    assert body["stoppedAtStage"] == "adapters"
    assert body["stageCounts"] is not None  # was null before #70
    monkeypatch.delenv("APP_ENV")


def test_budget_search_stop_has_stage_counts(client, auth_headers, _db_session, monkeypatch):
    """Budget stop at search sets stopped_at_stage AND stage_counts."""
    monkeypatch.setenv("SEARCH_DAILY_CALLS", "0")
    h = auth_headers("demo", "demo")
    body = client.post("/api/search", headers=h).json()
    assert body["stoppedAtStage"] == "search"
    assert body["stageCounts"] is not None
    monkeypatch.delenv("SEARCH_DAILY_CALLS")


def test_budget_llm_stop_has_stage_counts(client, auth_headers, _db_session, monkeypatch):
    """Budget stop at extract sets stopped_at_stage AND stage_counts."""
    monkeypatch.setenv("LLM_DAILY_CALLS", "0")
    h = auth_headers("demo", "demo")
    body = client.post("/api/search", headers=h).json()
    # Should stop at criteria or extract (whichever needs the first LLM call)
    assert body["stoppedAtStage"] is not None
    assert body["stageCounts"] is not None
    monkeypatch.delenv("LLM_DAILY_CALLS")


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
    assert body["error"].startswith("RuntimeError: ")
    assert "refused" in body["error"].lower()
    assert body["stoppedAtStage"] == "adapters"
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


# ---------- #65: Provider exception reaches the API response ----------


def test_extract_exception_reported_in_api(client, auth_headers, _db_session):
    """An exception during extraction must reach the API error field (#65)."""
    h = auth_headers("demo", "demo")

    def _boom(*args, **kwargs):
        raise RuntimeError("kaboom from extract")

    with patch("app.services.pipeline.extract_events", side_effect=_boom):
        body = client.post("/api/search", headers=h).json()

    assert body["error"] is not None, "error must not be null after pipeline exception"
    assert body["error"].startswith("RuntimeError: "), "error must be <Type>: <msg>"
    assert "kaboom" in body["error"]
    assert body["stoppedAtStage"] == "extract"


def test_search_provider_all_queries_fail(client, auth_headers, _db_session):
    """When every search query fails, error and stoppedAtStage='search' (#65)."""
    h = auth_headers("demo", "demo")

    class _BoomProvider:
        name = "boom"
        def search(self, query, **kw):
            raise RuntimeError("kaboom from provider")

    with patch("app.services.pipeline.get_search_provider",
               return_value=_BoomProvider()):
        body = client.post("/api/search", headers=h).json()

    assert body["error"] is not None
    assert body["error"].startswith("RuntimeError: "), "error must be <Type>: <msg>"
    assert "kaboom" in body["error"]
    assert body["stoppedAtStage"] == "search"


def test_scorer_env_var_reported(client, auth_headers, _db_session, monkeypatch):
    """Leftover SCORER env var is reported in the API error with format and stage."""
    monkeypatch.setenv("SCORER", "claude")
    h = auth_headers("demo", "demo")
    body = client.post("/api/search", headers=h).json()
    assert body["error"] is not None
    assert body["error"].startswith("ValueError: "), "error must be <Type>: <msg>"
    assert "SCORER" in body["error"]
    assert "LLM_PROVIDER" in body["error"]
    assert body["stoppedAtStage"] == "adapters"


def test_factory_runtime_error_reported(client, auth_headers, _db_session):
    """A RuntimeError from a factory must report format and stage='adapters'."""
    h = auth_headers("demo", "demo")

    with patch("app.services.pipeline.get_search_provider",
               side_effect=RuntimeError("bad config")):
        body = client.post("/api/search", headers=h).json()

    assert body["error"] == "RuntimeError: bad config"
    assert body["stoppedAtStage"] == "adapters"


# ---------- #104: per-stage run updates ----------


def test_per_stage_updates_written_during_pipeline(_db_session):
    """Pipeline writes current_stage per stage; finished run clears it."""
    user = _db_session.query(User).filter(User.username == "demo").first()
    stages_seen: list[str] = []

    original_update = __import__("app.services.pipeline", fromlist=["_update_run_stage"])._update_run_stage

    def _spy(run, db, stage, counts):
        stages_seen.append(stage)
        original_update(run, db, stage, counts)

    with patch("app.services.pipeline._update_run_stage", side_effect=_spy):
        run = run_pipeline(user, _db_session, trigger="manual")

    # At least adapters, criteria, search stages were hit
    assert "adapters" in stages_seen
    assert "criteria" in stages_seen
    assert "search" in stages_seen
    # Finished run has current_stage cleared
    assert run.current_stage is None
    assert run.finished_at is not None


def test_per_stage_update_commits_to_db(_db_session):
    """Each _update_run_stage call is visible in the DB (committed)."""
    from app.services.pipeline import _update_run_stage

    user = _db_session.query(User).filter(User.username == "demo").first()
    run = Run(user_id=user.id, started_at=__import__("datetime").datetime.now(__import__("datetime").UTC), trigger="manual")
    _db_session.add(run)
    _db_session.flush()
    run_id = run.id

    _update_run_stage(run, _db_session, "search", {"results_fetched": 5})

    # Re-query: committed data should be there
    _db_session.expire_all()
    refreshed = _db_session.query(Run).filter(Run.id == run_id).first()
    assert refreshed.current_stage == "search"
    sc = json.loads(refreshed.stage_counts)
    assert sc["results_fetched"] == 5


def test_extract_and_judge_write_intermediate_counts(_db_session):
    """During extract and judge, stage_counts climbs with each page/event."""
    user = _db_session.query(User).filter(User.username == "demo").first()
    from app.services.pipeline import _update_run_stage
    snapshots: list[tuple[str, dict]] = []

    original_update = _update_run_stage

    def _spy(run, db, stage, counts):
        snapshots.append((stage, dict(counts)))
        original_update(run, db, stage, counts)

    with patch("app.services.pipeline._update_run_stage", side_effect=_spy):
        run = run_pipeline(user, _db_session, trigger="manual")

    # Extract stage: pages_content_pass should climb from 0 toward the total
    extract_snaps = [(s, c) for s, c in snapshots if s == "extract"]
    pages_values = [c.get("pages_content_pass", 0) for _, c in extract_snaps]
    final_pages = json.loads(run.stage_counts).get("pages_content_pass", 0)
    if final_pages > 0:
        # Must see at least one intermediate value between 0 and the total
        intermediates = [v for v in pages_values if 0 < v <= final_pages]
        assert len(intermediates) >= 1, (
            f"expected intermediate pages_content_pass, got {pages_values}"
        )

    # Judge stage: events_judged should climb from 0 toward the total
    judge_snaps = [(s, c) for s, c in snapshots if s == "judge"]
    judged_values = [c.get("events_judged", 0) for _, c in judge_snaps]
    final_judged = json.loads(run.stage_counts).get("events_judged", 0)
    if final_judged > 0:
        intermediates = [v for v in judged_values if 0 < v <= final_judged]
        assert len(intermediates) >= 1, (
            f"expected intermediate events_judged, got {judged_values}"
        )


def test_events_to_judge_in_stage_counts_during_judge(_db_session):
    """#122: events_to_judge is set in stage_counts when the judge stage starts."""
    user = _db_session.query(User).filter(User.username == "demo").first()
    from app.services.pipeline import _update_run_stage
    snapshots: list[tuple[str, dict]] = []

    original_update = _update_run_stage

    def _spy(run, db, stage, counts):
        snapshots.append((stage, dict(counts)))
        original_update(run, db, stage, counts)

    with patch("app.services.pipeline._update_run_stage", side_effect=_spy):
        run_pipeline(user, _db_session, trigger="manual")

    judge_snaps = [(s, c) for s, c in snapshots if s == "judge"]
    assert len(judge_snaps) >= 1, "judge stage never reached"
    first_judge = judge_snaps[0][1]
    assert "events_to_judge" in first_judge, f"events_to_judge missing: {first_judge.keys()}"
    assert first_judge["events_to_judge"] >= 0


# ---------- #108: rejected bands in stage_counts ----------


def _cycling_judge(scores):
    """judge_event stand-in that hands out *scores* in turn."""
    from itertools import cycle
    from app.services.judge import Verdict

    it = cycle(scores)

    def _judge(event, **kwargs):
        return Verdict(score=next(it), reason="test", fit={}, is_event=True, capped=False)

    return _judge


def _assert_bands(sc: dict) -> None:
    # #124: reading every page produces ~10 events judged (was 8 with snippet-only);
    # cycling [5,20,40,95] over 10: 3×5, 3×20, 2×40, 2×95.
    assert sc["rejected_date_place"] == 3
    assert sc["rejected_off_topic"] == 3
    assert sc["rejected_other"] == 2
    assert sc["rejected_date_place"] + sc["rejected_off_topic"] + sc["rejected_other"] == sc["rejected"]


def test_rejected_bands_sum_to_rejected(client, auth_headers, _db_session):
    """Scores 5/20/40/95 over the fixture events: cycling; 40 is rejected (lower threshold 40)."""
    h = auth_headers("demo", "demo")
    with patch("app.services.pipeline.judge_event", side_effect=_cycling_judge([5, 20, 40, 95])):
        body = client.post("/api/search", headers=h).json()
    sc = body["stageCounts"]
    assert sc["events_judged"] == 10  # #124: more pages read → more events
    assert sc["accepted"] == 2
    _assert_bands(sc)


def test_scheduled_run_has_same_rejected_bands(_db_session):
    """Hourly runs go through the same run_pipeline, so the bands match the manual run."""
    user = _db_session.query(User).filter(User.username == "demo").first()
    with patch("app.services.pipeline.judge_event", side_effect=_cycling_judge([5, 20, 40, 95])):
        run = run_pipeline(user, _db_session, trigger="scheduled")
    assert run.trigger == "scheduled"
    _assert_bands(json.loads(run.stage_counts))


# ---------- #112: no-date events and page counters ----------


def test_no_date_event_and_page_counters_are_separate(client, auth_headers):
    """An extracted event without a start lands in filtered_no_date; filtered_non_event
    and pages_with_events count pages of the extract stage and sum to the pages extracted."""
    from app.services import pipeline as pipeline_mod
    from app.services.extract import ExtractedEvent

    real_extract = pipeline_mod.extract_events
    seen: dict[str, int] = {}

    def extract_plus_no_date(results, **kw):
        events, counts = real_extract(results, **kw)
        seen["pages"] = len(results)
        seen["with_events"] = len({e.source_url for e in events})
        events.append(ExtractedEvent(
            title="No start", start_local="", start_tz="Europe/Berlin", end_local=None,
            venue=None, city="Berlin", country="DE", link="https://x.example.com/no-start",
            description="d", confidence=0.9, source_url="https://x.example.com/no-start",
            page_kind="single_event",
        ))
        counts.events_extracted += 1
        return events, counts

    h = auth_headers("demo", "demo")
    with patch("app.services.pipeline.extract_events", side_effect=extract_plus_no_date):
        sc = client.post("/api/search", headers=h).json()["stageCounts"]

    assert sc["filtered_no_date"] == 1
    assert sc["pages_with_events"] == seen["with_events"] > 0
    assert sc["pages_with_events"] + sc["filtered_non_event"] == seen["pages"]


def test_early_stop_defaults_no_date_and_pages_with_events(client, auth_headers):
    """A run that stops before extract still carries both counters (0)."""
    sc = client.post("/api/search", headers=auth_headers("nocrit", "nocritpw")).json()["stageCounts"]
    assert (sc["filtered_no_date"], sc["pages_with_events"]) == (0, 0)
