"""Tests for POST /api/search and POST /api/search/all."""

from __future__ import annotations


def test_run_search_returns_search_result(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.post("/api/search", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert "runId" in body
    assert "eventsFound" in body
    assert "eventsNew" in body


def test_run_search_second_run_fewer_new(client, auth_headers):
    """A second run after the first produces fewer (or zero) new events."""
    h = auth_headers("demo", "demo")
    r1 = client.post("/api/search", headers=h)
    body1 = r1.json()
    r2 = client.post("/api/search", headers=h)
    body2 = r2.json()
    # Second run should have fewer or equal new events (dedup works)
    assert body2["eventsNew"] <= body1["eventsNew"]


def test_run_search_increments_run_id(client, auth_headers):
    h = auth_headers("demo", "demo")
    r1 = client.post("/api/search", headers=h)
    r2 = client.post("/api/search", headers=h)
    assert r1.json()["runId"] != r2.json()["runId"]


def test_search_all_missing_key_returns_401(client):
    r = client.post("/api/search/all")
    assert r.status_code == 401


def test_search_all_wrong_key_returns_401(client, monkeypatch):
    monkeypatch.setenv("SEARCH_ALL_API_KEY", "correct-key")
    r = client.post("/api/search/all", headers={"X-API-Key": "wrong-key"})
    assert r.status_code == 401


def test_search_all_unset_env_returns_401(client, monkeypatch):
    monkeypatch.delenv("SEARCH_ALL_API_KEY", raising=False)
    r = client.post("/api/search/all", headers={"X-API-Key": "anything"})
    assert r.status_code == 401


def test_search_all_returns_202_with_users_queued(client, monkeypatch):
    monkeypatch.setenv("SEARCH_ALL_API_KEY", "test-secret")
    r = client.post("/api/search/all", headers={"X-API-Key": "test-secret"})
    assert r.status_code == 202
    body = r.json()
    assert "usersQueued" in body
    assert "usersSkipped" in body
    assert body["usersQueued"] >= 1


def test_run_search_no_auth_returns_401(client):
    r = client.post("/api/search")
    assert r.status_code == 401


def test_search_all_max_scheduled_users(client, auth_headers, _db_session, monkeypatch):
    import hashlib
    import json
    monkeypatch.setenv("SEARCH_ALL_API_KEY", "k")
    monkeypatch.setenv("MAX_SCHEDULED_USERS", "2")

    # Register 2 more users with criteria
    h_a = auth_headers("msu_a", "pw")
    h_b = auth_headers("msu_b", "pw")
    client.put("/api/criteria", headers=h_a, json={
        "text": "jazz in Berlin (Germany) next week (19-21st October 2026)",
    })
    client.put("/api/criteria", headers=h_b, json={
        "text": "jazz in Berlin (Germany) next week (19-21st October 2026)",
    })

    # Pre-seed facets for all users so the pipeline doesn't need criteria parsing
    from app.orm import Criteria, User
    from datetime import datetime, UTC
    from tests.conftest import _C1_FACETS, _C1_TEXT

    text_sha = hashlib.sha256(_C1_TEXT.encode()).hexdigest()
    for i, name in enumerate(["demo", "msu_a", "msu_b"]):
        user = _db_session.query(User).filter(User.username == name).first()
        crit = _db_session.query(Criteria).filter(Criteria.user_id == user.id).first()
        crit.facets_json = json.dumps(_C1_FACETS)
        crit.facets_version = "criteria_v2"
        crit.facets_text_sha = text_sha
        crit.updated_at = datetime(2026, 1, 1 + i, tzinfo=UTC)
    _db_session.commit()

    r = client.post("/api/search/all", headers={"X-API-Key": "k"})
    assert r.status_code == 202
    body = r.json()
    assert body["usersQueued"] == 2
    assert body["usersSkipped"] == 1


def test_search_all_cap_gte_total_no_skip(client, monkeypatch):
    monkeypatch.setenv("SEARCH_ALL_API_KEY", "k")
    monkeypatch.setenv("MAX_SCHEDULED_USERS", "100")

    r = client.post("/api/search/all", headers={"X-API-Key": "k"})
    assert r.status_code == 202
    assert r.json()["usersSkipped"] == 0


def test_search_all_skips_user_without_criteria(client, auth_headers, _db_session, monkeypatch):
    monkeypatch.setenv("SEARCH_ALL_API_KEY", "k")

    # Register user then delete their criteria row
    auth_headers("nocrit", "nocrit")
    from app.orm import User, Criteria
    user = _db_session.query(User).filter(User.username == "nocrit").first()
    _db_session.query(Criteria).filter(Criteria.user_id == user.id).delete()
    _db_session.commit()

    r = client.post("/api/search/all", headers={"X-API-Key": "k"})
    assert r.status_code == 202
    # Only 1 user queued (demo), nocrit skipped by join
    assert r.json()["usersQueued"] == 1


def test_search_all_second_call_skips_queued_users(client, _db_session, monkeypatch):
    """Two consecutive search/all calls: first queues the user, second skips it.

    A slow pipeline means the enqueue-time Run row still has finished_at=NULL
    when the next hourly call arrives (#73).
    """
    from unittest.mock import patch
    from app.orm import Run, User

    monkeypatch.setenv("SEARCH_ALL_API_KEY", "k")

    # Patch _run_scheduled_user to be a no-op (simulates slow pipeline)
    with patch("app.routers.search._run_scheduled_user"):
        r1 = client.post("/api/search/all", headers={"X-API-Key": "k"})
        assert r1.status_code == 202
        assert r1.json()["usersQueued"] == 1
        assert r1.json()["usersSkipped"] == 0

        # The enqueue-time Run row exists with finished_at=NULL
        user = _db_session.query(User).filter(User.username == "demo").first()
        runs = _db_session.query(Run).filter(
            Run.user_id == user.id, Run.finished_at.is_(None),
        ).all()
        assert len(runs) == 1

        # Second call sees the unfinished row and skips the user
        r2 = client.post("/api/search/all", headers={"X-API-Key": "k"})
        assert r2.status_code == 202
        assert r2.json()["usersQueued"] == 0
        assert r2.json()["usersSkipped"] == 1


def test_search_all_crashed_row_does_not_block_forever(client, _db_session, monkeypatch):
    """An enqueue-time Run row older than the overlap window does not block the user."""
    from datetime import datetime, UTC, timedelta
    from app.orm import Run, User
    from unittest.mock import patch

    monkeypatch.setenv("SEARCH_ALL_API_KEY", "k")
    user = _db_session.query(User).filter(User.username == "demo").first()

    # Simulate a crashed enqueue-time row: started 60 min ago, never finished
    old = datetime.now(UTC) - timedelta(minutes=60)
    _db_session.add(Run(
        user_id=user.id, started_at=old, trigger="scheduled",
    ))
    _db_session.commit()

    # The stale row is older than the 55-min window, so the user is eligible
    with patch("app.routers.search._run_scheduled_user"):
        r = client.post("/api/search/all", headers={"X-API-Key": "k"})
    assert r.status_code == 202
    assert r.json()["usersQueued"] == 1
    assert r.json()["usersSkipped"] == 0


def test_search_all_skips_user_with_unfinished_run(client, _db_session, monkeypatch):
    """A user with an unfinished run started < 55 min ago is skipped."""
    from datetime import datetime, UTC, timedelta
    from app.orm import Run, User

    monkeypatch.setenv("SEARCH_ALL_API_KEY", "k")
    user = _db_session.query(User).filter(User.username == "demo").first()

    # Insert an unfinished run started 10 minutes ago
    recent = datetime.now(UTC) - timedelta(minutes=10)
    _db_session.add(Run(
        user_id=user.id, started_at=recent, trigger="scheduled",
    ))
    _db_session.commit()

    r = client.post("/api/search/all", headers={"X-API-Key": "k"})
    assert r.status_code == 202
    assert r.json()["usersQueued"] == 0
    assert r.json()["usersSkipped"] == 1


# ---------- #73 D1: orphan-row finalisation ----------


def test_scheduled_user_exception_finalises_run(_db_session, monkeypatch):
    """If _run_scheduled_user raises before run_pipeline, the enqueue-time row is finalised."""
    from datetime import datetime, UTC
    from unittest.mock import patch
    from sqlalchemy.orm import sessionmaker
    from app.orm import Run, User
    from app.routers.search import _run_scheduled_user
    import app.routers.search as search_mod

    engine = _db_session.get_bind()
    SiblingSession = sessionmaker(bind=engine)
    old_factory = search_mod._session_factory
    search_mod._session_factory = SiblingSession

    try:
        user = _db_session.query(User).filter(User.username == "demo").first()
        run = Run(user_id=user.id, started_at=datetime.now(UTC), trigger="scheduled")
        _db_session.add(run)
        _db_session.flush()
        run_id = run.id
        _db_session.commit()

        # Patch run_pipeline to explode
        with patch("app.routers.search.run_pipeline", side_effect=RuntimeError("boom")):
            _run_scheduled_user(user.id, run_id)

        _db_session.expire_all()
        row = _db_session.query(Run).filter(Run.id == run_id).first()
        assert row.finished_at is not None
        assert "RuntimeError: boom" in row.error
    finally:
        search_mod._session_factory = old_factory


def test_scheduled_user_not_found_finalises_run(_db_session, monkeypatch):
    """If the user is gone when the background task runs, the enqueue-time row is finalised."""
    from datetime import datetime, UTC
    from sqlalchemy.orm import sessionmaker
    from app.orm import Run, User
    from app.routers.search import _run_scheduled_user
    import app.routers.search as search_mod

    engine = _db_session.get_bind()
    SiblingSession = sessionmaker(bind=engine)
    old_factory = search_mod._session_factory
    search_mod._session_factory = SiblingSession

    try:
        user = _db_session.query(User).filter(User.username == "demo").first()
        run = Run(user_id=user.id, started_at=datetime.now(UTC), trigger="scheduled")
        _db_session.add(run)
        _db_session.flush()
        run_id = run.id
        _db_session.commit()

        # Pass a wrong user_id so the lookup returns None
        _run_scheduled_user("no-such-id", run_id)

        _db_session.expire_all()
        row = _db_session.query(Run).filter(Run.id == run_id).first()
        assert row.finished_at is not None
        assert row.error == "user not found"
    finally:
        search_mod._session_factory = old_factory


def test_scheduled_user_real_pipeline_single_row(client, _db_session, monkeypatch):
    """Real _run_scheduled_user (not mocked) produces exactly one Run row with counts."""
    from sqlalchemy.orm import sessionmaker
    from app.orm import Run, User
    import app.routers.search as search_mod

    monkeypatch.setenv("SEARCH_ALL_API_KEY", "k")

    # Factory that creates sibling sessions on the same in-memory engine
    # (StaticPool shares one connection, so they see each other's writes).
    engine = _db_session.get_bind()
    SiblingSession = sessionmaker(bind=engine)

    old_factory = search_mod._session_factory
    search_mod._session_factory = SiblingSession
    try:
        user = _db_session.query(User).filter(User.username == "demo").first()
        # Clear any pre-existing runs
        _db_session.query(Run).filter(Run.user_id == user.id).delete()
        _db_session.commit()

        r = client.post("/api/search/all", headers={"X-API-Key": "k"})
        assert r.status_code == 202
        assert r.json()["usersQueued"] == 1

        # Background task ran synchronously in TestClient; check the DB
        _db_session.expire_all()
        runs = _db_session.query(Run).filter(Run.user_id == user.id).all()
        assert len(runs) == 1, f"expected 1 run, got {len(runs)}"
        run = runs[0]
        assert run.trigger == "scheduled"
        assert run.finished_at is not None
        assert run.stage_counts is not None
    finally:
        search_mod._session_factory = old_factory


# ---------- #104: GET /api/search/last-run ----------


def test_last_run_returns_null_when_no_runs(client, auth_headers):
    h = auth_headers("fresh", "fresh")
    r = client.get("/api/search/last-run", headers=h)
    assert r.status_code == 200
    assert r.json()["run"] is None


def test_last_run_returns_most_recent(client, auth_headers):
    h = auth_headers("demo", "demo")
    # Run a search first so there is a run
    client.post("/api/search", headers=h)
    r = client.get("/api/search/last-run", headers=h)
    assert r.status_code == 200
    run = r.json()["run"]
    assert run is not None
    assert "runId" in run
    assert "currentStage" in run
    assert "startedAt" in run
    assert "finishedAt" in run
    # Finished run has currentStage null
    assert run["currentStage"] is None
    assert run["finishedAt"] is not None


def test_last_run_no_auth_returns_401(client):
    r = client.get("/api/search/last-run")
    assert r.status_code == 401


# ---------- #108: durationSeconds, trigger, GET /api/search/runs ----------

_RUN_SUMMARY_KEYS = {
    "runId", "startedAt", "finishedAt", "durationSeconds", "trigger",
    "eventsFound", "accepted", "queued", "rejected", "setAside",
    "pagesRead", "pagesWithEvents", "pagesSkipped", "error", "countsVersion",
}


def test_counts_version_stamped_and_exposed(client, auth_headers):
    """#118/#139: every finished run carries counts_version 4; last-run and /runs expose it as countsVersion."""
    h = auth_headers("demo", "demo")
    body = client.post("/api/search", headers=h).json()
    assert body["stageCounts"]["counts_version"] == 4
    assert body["countsVersion"] == 4
    assert client.get("/api/search/last-run", headers=h).json()["run"]["countsVersion"] == 4
    assert client.get("/api/search/runs", headers=h).json()["runs"][0]["countsVersion"] == 4
    # a run that stopped early is stamped too
    stopped = client.post("/api/search", headers=auth_headers("nocrit", "nocritpw")).json()
    assert stopped["stoppedAtStage"] and stopped["stageCounts"]["counts_version"] == 4


def test_old_run_reports_version_1_and_recomputes_bands(client, auth_headers, _db_session):
    """#118: a run row stored before the bands reports countsVersion 1 and its bands from its events' scores."""
    import json
    from datetime import UTC, datetime
    from app.orm import Event, Run, User

    h = auth_headers("demo", "demo")
    user = _db_session.query(User).filter(User.username == "demo").first()
    now = datetime.now(UTC)
    run = Run(user_id=user.id, started_at=now, finished_at=now, trigger="scheduled",
              stage_counts=json.dumps({"results_fetched": 5, "events_extracted": 4, "accepted": 1, "rejected": 3}))
    _db_session.add(run)
    _db_session.flush()
    for i, (status, score) in enumerate([("accepted", 90), ("rejected", 5), ("rejected", 20), ("rejected", 50)]):
        _db_session.add(Event(
            user_id=user.id, run_id=run.id, title=f"e{i}", date_time="2026-10-20T20:00:00+02:00",
            place="Berlin", link=f"https://x.example.com/{i}", description="d", status=status, score=score,
        ))
    _db_session.commit()

    last = client.get("/api/search/last-run", headers=h).json()["run"]
    assert last["runId"] == run.id
    assert last["countsVersion"] == 1
    sc = last["stageCounts"]
    assert (sc["rejected_date_place"], sc["rejected_off_topic"], sc["rejected_other"]) == (1, 1, 1)
    assert "counts_version" not in sc
    assert client.get("/api/search/runs", headers=h).json()["runs"][0]["countsVersion"] == 1


def test_last_run_has_duration_and_trigger(client, auth_headers):
    h = auth_headers("demo", "demo")
    client.post("/api/search", headers=h)
    run = client.get("/api/search/last-run", headers=h).json()["run"]
    assert run["trigger"] == "manual"
    assert isinstance(run["durationSeconds"], float)
    assert run["durationSeconds"] >= 0


def test_last_run_duration_null_while_running(client, auth_headers, _db_session):
    from datetime import UTC, datetime
    from app.orm import Run, User

    h = auth_headers("demo", "demo")
    user = _db_session.query(User).filter(User.username == "demo").first()
    _db_session.add(Run(user_id=user.id, started_at=datetime.now(UTC), trigger="scheduled",
                        current_stage="search"))
    _db_session.commit()
    run = client.get("/api/search/last-run", headers=h).json()["run"]
    assert run["durationSeconds"] is None
    assert run["trigger"] == "scheduled"


def test_runs_newest_first_and_own_only(client, auth_headers):
    h_demo = auth_headers("demo", "demo")
    h_alice = auth_headers("alice", "alicepw")
    first = client.post("/api/search", headers=h_demo).json()["runId"]
    second = client.post("/api/search", headers=h_demo).json()["runId"]
    alice_run = client.post("/api/search", headers=h_alice).json()["runId"]

    runs = client.get("/api/search/runs", headers=h_demo).json()["runs"]
    assert [r["runId"] for r in runs] == [second, first]

    alice_runs = client.get("/api/search/runs", headers=h_alice).json()["runs"]
    assert [r["runId"] for r in alice_runs] == [alice_run]


def test_runs_summary_fields_and_set_aside(client, auth_headers):
    h = auth_headers("demo", "demo")
    body = client.post("/api/search", headers=h).json()
    sc = body["stageCounts"]
    summary = client.get("/api/search/runs", headers=h).json()["runs"][0]
    assert set(summary) == _RUN_SUMMARY_KEYS
    assert summary["runId"] == body["runId"]
    assert summary["trigger"] == "manual"
    assert summary["durationSeconds"] == body["durationSeconds"]
    assert summary["eventsFound"] == sc["events_extracted"]
    assert summary["accepted"] == sc["accepted"]
    assert summary["queued"] == sc["queued"]
    assert summary["rejected"] == sc["rejected"]
    assert summary["setAside"] == (
        sc["filtered_no_date"] + sc.get("filtered_no_time", 0) + sc["filtered_incomplete"] + sc["filtered_past"] + sc["filtered_date"]
        + sc["filtered_place"] + sc["filtered_duplicate"] + sc["judge_errors"]
    )
    assert summary["setAside"] > 0
    assert summary["pagesRead"] == sc["results_fetched"]
    assert summary["pagesWithEvents"] == sc["pages_with_events"] > 0
    assert summary["pagesSkipped"] == sc["filtered_non_event"]
    assert summary["pagesWithEvents"] + summary["pagesSkipped"] <= summary["pagesRead"]
    assert summary["error"] is None
    # the funnel invariant: every extracted event lands in exactly one bar
    assert summary["accepted"] + summary["queued"] + summary["rejected"] + summary["setAside"] == summary["eventsFound"]


def test_runs_invariant_holds_for_every_finished_run(client, auth_headers):
    """Manual run with a no-date event (#112), repeat run with nothing new, and an error run (no criteria)."""
    from unittest.mock import patch
    from app.services import pipeline as pipeline_mod
    from app.services.extract import ExtractedEvent

    real_extract = pipeline_mod.extract_events

    def extract_plus_no_date(results, **kw):
        events, counts = real_extract(results, **kw)
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
    # setAside includes filtered_no_date, filtered_duplicate, judge_errors, etc.
    s0 = client.get("/api/search/runs", headers=h).json()["runs"][0]
    assert s0["setAside"] >= sc["filtered_no_date"]
    assert s0["accepted"] + s0["queued"] + s0["rejected"] + s0["setAside"] == s0["eventsFound"]
    client.post("/api/search", headers=h)
    h_fresh = auth_headers("fresh", "freshpw")
    client.post("/api/search", headers=h_fresh)
    for hdr in (h, h_fresh):
        runs = client.get("/api/search/runs", headers=hdr).json()["runs"]
        assert runs
        for s in runs:
            assert s["finishedAt"] is not None
            # every extracted event lands in exactly one bar; recovery errors belong to the older run
            assert s["accepted"] + s["queued"] + s["rejected"] + s["setAside"] == s["eventsFound"]
        last = client.get("/api/search/last-run", headers=hdr).json()["run"]
        sc = last["stageCounts"]
        assert (sc["rejected_date_place"], sc["rejected_off_topic"], sc["rejected_other"]) == (0, 0, 0)


def test_runs_invariant_holds_with_incomplete_and_unjudged(client, auth_headers, monkeypatch):
    """One incomplete extracted event and one judge error: all set aside, none lost."""
    from unittest.mock import patch
    from app.services import pipeline as pipeline_mod
    from app.services.extract import ExtractedEvent
    from app.services.judge import JudgeError, Verdict

    real_extract = pipeline_mod.extract_events

    def extract_plus_incomplete(results, **kw):
        events, counts = real_extract(results, **kw)
        events.append(ExtractedEvent(
            title="No city", start_local="2026-10-20T20:00:00", start_tz="Europe/Berlin", end_local=None,
            venue=None, city=None, country="DE", link="https://x.example.com/no-city", description="d",
            confidence=0.9, source_url="https://x.example.com/no-city", page_kind="single_event",
        ))
        counts.events_extracted += 1
        return events, counts

    calls = []

    def judge_fails_once(event, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            return JudgeError(event=event, error="forced")
        return Verdict(score=95, reason="t", fit={}, is_event=True, capped=False)

    h = auth_headers("demo", "demo")
    with patch("app.services.pipeline.extract_events", side_effect=extract_plus_incomplete), \
            patch("app.services.pipeline.judge_event", side_effect=judge_fails_once):
        sc = client.post("/api/search", headers=h).json()["stageCounts"]

    assert sc["filtered_incomplete"] == 1
    # #134: no per-page cap and no per-search cap → all survivors are judged: 1 error, the rest scored 95
    # #136: 20 survivors (no in-run or title checks); the after-storage check merges the repeats
    assert "events_capped" not in sc
    assert sc["events_to_judge"] == 20
    assert sc["judge_errors"] == 1
    assert (sc["accepted"], sc["dedup_merged"]) == (12, 7)
    s = client.get("/api/search/runs", headers=h).json()["runs"][0]
    assert s["eventsFound"] == sc["events_extracted"]
    assert s["accepted"] + s["queued"] + s["rejected"] + s["setAside"] == s["eventsFound"]


def test_runs_limit_validated(client, auth_headers):
    h = auth_headers("demo", "demo")
    client.post("/api/search", headers=h)
    client.post("/api/search", headers=h)
    assert client.get("/api/search/runs?limit=0", headers=h).status_code == 400
    assert client.get("/api/search/runs?limit=101", headers=h).status_code == 400
    assert client.get("/api/search/runs?limit=x", headers=h).status_code == 400
    assert len(client.get("/api/search/runs?limit=1", headers=h).json()["runs"]) == 1
    assert len(client.get("/api/search/runs", headers=h).json()["runs"]) == 2


def test_runs_no_auth_returns_401(client):
    assert client.get("/api/search/runs").status_code == 401
