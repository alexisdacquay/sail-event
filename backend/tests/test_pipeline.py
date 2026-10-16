"""Tests for the search-run pipeline (issue #11)."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

from app.orm import Event, Run
from app.services.pipeline import derive_queries


# ---------- derive_queries ----------


def test_derive_queries_empty():
    assert derive_queries("") == [""]


def test_derive_queries_single_phrase():
    assert derive_queries("hiking") == ["hiking"]


def test_derive_queries_commas():
    result = derive_queries("a, b, c")
    assert result == ["a, b, c", "a", "b", "c"]


def test_derive_queries_newlines():
    result = derive_queries("a\nb\nc")
    assert result == ["a\nb\nc", "a", "b", "c"]


def test_derive_queries_mixed():
    result = derive_queries("a, b\nc")
    assert result == ["a, b\nc", "a", "b", "c"]


def test_derive_queries_truncate_to_5_extras():
    result = derive_queries("a,b,c,d,e,f,g")
    assert result[0] == "a,b,c,d,e,f,g"
    assert result[1:] == ["a", "b", "c", "d", "e"]
    assert len(result) == 6


# ---------- Run row written (POST /api/search) ----------


def test_run_row_written_after_search(client, auth_headers, _db_session):
    h = auth_headers("demo", "demo")
    r = client.post("/api/search", headers=h)
    assert r.status_code == 200
    body = r.json()

    run = _db_session.query(Run).filter(Run.id == body["runId"]).first()
    assert run is not None
    assert run.trigger == "manual"
    assert run.events_found == body["eventsFound"]
    assert run.events_new == body["eventsNew"]
    assert run.started_at is not None
    assert run.finished_at is not None
    assert run.error is None


# ---------- Run row trigger after POST /api/search/all ----------


def test_run_row_trigger_scheduled(client, _db_session, monkeypatch):
    monkeypatch.setenv("SEARCH_ALL_API_KEY", "k")
    client.post("/api/search/all", headers={"X-API-Key": "k"})

    runs = _db_session.query(Run).all()
    assert len(runs) >= 1
    assert all(r.trigger == "scheduled" for r in runs)


# ---------- runId matches DB ----------


def test_run_id_matches_db(client, auth_headers, _db_session):
    h = auth_headers("demo", "demo")
    body = client.post("/api/search", headers=h).json()
    assert _db_session.query(Run).filter(Run.id == body["runId"]).count() == 1


# ---------- Events carry run_id ----------


def test_events_carry_run_id(client, auth_headers, _db_session):
    h = auth_headers("fresh", "fresh")
    # Save criteria so the pipeline finds them
    client.put("/api/criteria", headers=h, json={"text": "anything"})
    body = client.post("/api/search", headers=h).json()
    run_id = body["runId"]

    events = (
        _db_session.query(Event)
        .filter(Event.run_id == run_id)
        .all()
    )
    assert len(events) == body["eventsNew"]
    assert all(e.run_id == run_id for e in events)


# ---------- Recovery of leftover `new` events ----------


def test_recovery_of_new_events(client, auth_headers, _db_session):
    h = auth_headers("demo", "demo")
    # Manually insert a leftover `new` event (simulating prior crash)
    from app.orm import User
    user = _db_session.query(User).filter(User.username == "demo").first()
    leftover = Event(
        user_id=user.id,
        title="Leftover",
        date_time="2026-01-01T00:00:00",
        place="Nowhere",
        link="https://leftover.example.com/unique",
        description="leftover event",
        status="new",
    )
    _db_session.add(leftover)
    _db_session.commit()

    # Run pipeline — should recover the leftover
    client.post("/api/search", headers=h)
    _db_session.refresh(leftover)
    assert leftover.status != "new"
    assert leftover.score is not None


# ---------- MAX_EVENTS_PER_RUN cap ----------


def test_max_events_per_run_cap(client, auth_headers, _db_session, monkeypatch):
    monkeypatch.setenv("MAX_EVENTS_PER_RUN", "3")
    h = auth_headers("capped", "capped")
    client.put("/api/criteria", headers=h, json={"text": "anything"})
    body = client.post("/api/search", headers=h).json()
    # Fixture has 8 unique events; cap at 3
    assert body["eventsNew"] == 3


# ---------- Failure path ----------


def _raise_provider():
    """Return a search provider that always raises."""
    class _Boom:
        def search(self, queries):
            raise RuntimeError("boom")
    return _Boom()


def test_failure_writes_run_with_error(client, auth_headers, _db_session):
    h = auth_headers("demo", "demo")
    with patch("app.services.pipeline.get_search_provider", _raise_provider):
        r = client.post("/api/search", headers=h)
    assert r.status_code == 500
    body = r.json()
    assert "boom" in body["detail"]

    run = _db_session.query(Run).filter(Run.error.isnot(None)).first()
    assert run is not None
    assert run.finished_at is not None
    assert "boom" in run.error


def test_search_returns_500_on_failure(client, auth_headers):
    h = auth_headers("demo", "demo")
    with patch("app.services.pipeline.get_search_provider", _raise_provider):
        r = client.post("/api/search", headers=h)
    assert r.status_code == 500
    assert "detail" in r.json()


# ---------- search/all continues after one user fails ----------


def test_search_all_continues_after_failure(client, auth_headers, _db_session, monkeypatch):
    monkeypatch.setenv("SEARCH_ALL_API_KEY", "k")
    # Create a second user with criteria
    h2 = auth_headers("user2", "user2")
    client.put("/api/criteria", headers=h2, json={"text": "stuff"})

    call_count = 0

    def _flaky_provider():
        nonlocal call_count
        call_count += 1

        class _P:
            def __init__(self, n):
                self._n = n

            def search(self, queries):
                if self._n == 1:
                    raise RuntimeError("flaky")
                from app.adapters import FixtureSearchProvider
                return FixtureSearchProvider().search(queries)

        return _P(call_count)

    with patch("app.services.pipeline.get_search_provider", _flaky_provider):
        r = client.post("/api/search/all", headers={"X-API-Key": "k"})

    assert r.status_code == 200
    # One user failed, one succeeded
    assert r.json()["usersProcessed"] == 1

    # Both users have Run rows; one has error
    runs = _db_session.query(Run).all()
    assert len(runs) == 2
    errors = [r for r in runs if r.error]
    assert len(errors) == 1


# ---------- carry-over tests ----------


def test_run_partial_failure_records_events_found_with_error(
    client, auth_headers, _db_session,
):
    h = auth_headers("partial", "partial")
    client.put("/api/criteria", headers=h, json={"text": "anything"})

    call_count = 0

    def partial_fail(event, criteria):
        nonlocal call_count
        call_count += 1
        if call_count > 2:
            raise RuntimeError("scorer partial boom")
        return (50, "ok")

    with patch("app.services.pipeline.get_scorer") as mock_sc:
        mock_sc.return_value.score.side_effect = partial_fail
        r = client.post("/api/search", headers=h)

    assert r.status_code == 500

    from app.orm import User
    user = _db_session.query(User).filter(User.username == "partial").first()
    run = (
        _db_session.query(Run)
        .filter(Run.user_id == user.id, Run.error.isnot(None))
        .first()
    )
    assert run is not None
    assert run.events_found > 0
    assert run.error is not None


def test_events_found_vs_events_new_under_cap_and_dedup(
    client, auth_headers, _db_session, monkeypatch,
):
    h = auth_headers("dedup", "dedup")
    client.put("/api/criteria", headers=h, json={"text": "anything"})

    # Pre-insert 3 events with links matching fixture events
    from app.orm import User
    user = _db_session.query(User).filter(User.username == "dedup").first()
    fixture_links = [
        "https://events.example.com/photo-meetup-nov",
        "https://events.example.com/ceramic-glazing",
        "https://events.example.com/jazz-stars-dec",
    ]
    for link in fixture_links:
        _db_session.add(Event(
            user_id=user.id,
            title="pre",
            date_time="2026-01-01",
            place="p",
            link=link,
            description="d",
            status="accepted",
        ))
    _db_session.commit()

    monkeypatch.setenv("MAX_EVENTS_PER_RUN", "3")
    body = client.post("/api/search", headers=h).json()

    assert body["eventsFound"] > body["eventsNew"]
    assert body["eventsNew"] <= 3


def test_pipeline_calls_derive_queries_with_user_criteria(
    client, auth_headers, _db_session,
):
    h = auth_headers("dquser", "dquser")
    client.put("/api/criteria", headers=h, json={"text": "sailing, regattas"})

    with patch("app.services.pipeline.derive_queries", wraps=derive_queries) as spy:
        client.post("/api/search", headers=h)

    spy.assert_called_once_with("sailing, regattas")
