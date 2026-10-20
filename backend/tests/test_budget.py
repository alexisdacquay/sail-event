"""Tests for budget enforcement (§8) and cost_usd."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from app.orm import Criteria, Run, User
from app.services.pipeline import run_pipeline


# ---------- Budget: search ----------


def test_search_budget_stops_run(client, auth_headers, _db_session, monkeypatch):
    """When the search-call cap is hit, the run stops with 'budget: search'."""
    monkeypatch.setenv("SEARCH_DAILY_CALLS", "0")  # cap already exhausted
    h = auth_headers("demo", "demo")
    body = client.post("/api/search", headers=h).json()
    assert body["error"] == "budget: search"
    assert body["stoppedAtStage"] == "search"
    # Still HTTP 200
    r = client.post("/api/search", headers=h)
    assert r.status_code == 200


def test_llm_budget_stops_run(client, auth_headers, _db_session, monkeypatch):
    """When the LLM-call cap is hit, the run stops with 'budget: llm'."""
    monkeypatch.setenv("LLM_DAILY_CALLS", "0")
    h = auth_headers("demo", "demo")
    body = client.post("/api/search", headers=h).json()
    # Pipeline should stop at extract or judge with budget: llm
    assert body["error"] == "budget: llm"
    assert body["stoppedAtStage"] in ("criteria", "extract", "judge")


# ---------- Budget stop persists across users via search/all ----------


def test_budget_stop_across_users_and_202(_db_session, monkeypatch):
    """After a budget stop for one user, the next user also stops,
    and the endpoint still returns 202.

    Tests run_pipeline directly (background tasks use a different session).
    """
    import hashlib
    from tests.conftest import _C1_FACETS, _C1_TEXT
    from app.auth import hash_password

    # Set search cap to 0 so both users hit the budget immediately
    monkeypatch.setenv("SEARCH_DAILY_CALLS", "0")

    # Create two users with criteria
    users = []
    for name in ("budg_a", "budg_b"):
        u = User(
            username=name,
            password_hash=hash_password(name),
            upper_threshold=90,
            lower_threshold=40,
            ics_token=f"ics-{name}",
        )
        _db_session.add(u)
        _db_session.flush()

        text_sha = hashlib.sha256(_C1_TEXT.encode()).hexdigest()
        c = Criteria(
            user_id=u.id,
            text=_C1_TEXT,
            facets_json=json.dumps(_C1_FACETS),
            facets_version="criteria_v2",
            facets_text_sha=text_sha,
        )
        _db_session.add(c)
        users.append(u)
    _db_session.commit()

    runs = []
    for u in users:
        run = run_pipeline(u, _db_session, trigger="scheduled")
        runs.append(run)

    # Both users should hit the same budget stop
    assert runs[0].error == "budget: search"
    assert runs[0].stopped_at_stage == "search"
    assert runs[1].error == "budget: search"
    assert runs[1].stopped_at_stage == "search"

    # Verify search/all still returns 202
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv("SEARCH_ALL_API_KEY", "k")
    with TestClient(app) as tc:
        r = tc.post("/api/search/all", headers={"X-API-Key": "k"})
    assert r.status_code == 202


# ---------- cost_usd ----------


def test_cost_usd_computed_when_prices_set(_db_session, monkeypatch):
    monkeypatch.setenv("LLM_USD_PER_1K_IN", "0.001")
    monkeypatch.setenv("LLM_USD_PER_1K_OUT", "0.002")
    monkeypatch.setenv("SEARCH_USD_PER_CALL", "0.01")

    user = _db_session.query(User).filter(User.username == "demo").first()
    run = run_pipeline(user, _db_session, trigger="manual")

    # cost_usd should be set (search_calls and llm_calls may be 0 with fixtures)
    assert run.cost_usd is not None
    assert run.cost_usd >= 0.0


def test_cost_usd_null_when_prices_unset(_db_session, monkeypatch):
    monkeypatch.delenv("LLM_USD_PER_1K_IN", raising=False)
    monkeypatch.delenv("LLM_USD_PER_1K_OUT", raising=False)
    monkeypatch.delenv("SEARCH_USD_PER_CALL", raising=False)

    user = _db_session.query(User).filter(User.username == "demo").first()
    run = run_pipeline(user, _db_session, trigger="manual")
    assert run.cost_usd is None


# ---------- #77: scheduled runs use basic depth, budget counts credits ----------


def test_scheduled_uses_basic_depth(_db_session, monkeypatch):
    """Scheduled trigger → basic depth → 1 credit on search_calls."""
    monkeypatch.delenv("TAVILY_SEARCH_DEPTH_SCHEDULED", raising=False)
    monkeypatch.delenv("SEARCH_CREDITS_ADVANCED", raising=False)
    user = _db_session.query(User).filter(User.username == "demo").first()
    run = run_pipeline(user, _db_session, trigger="scheduled")
    # Fixture provider: 1 call × 1 credit (basic) = 1
    assert run.search_calls == 1


def test_manual_uses_advanced_depth(_db_session, monkeypatch):
    """Manual trigger → advanced depth → 2 credits on search_calls."""
    monkeypatch.delenv("TAVILY_SEARCH_DEPTH", raising=False)
    monkeypatch.delenv("SEARCH_CREDITS_ADVANCED", raising=False)
    user = _db_session.query(User).filter(User.username == "demo").first()
    run = run_pipeline(user, _db_session, trigger="manual")
    # Fixture provider: 1 call × 2 credits (advanced) = 2
    assert run.search_calls == 2


def test_credits_advanced_env_override(_db_session, monkeypatch):
    """SEARCH_CREDITS_ADVANCED overrides the default 2."""
    monkeypatch.setenv("SEARCH_CREDITS_ADVANCED", "3")
    user = _db_session.query(User).filter(User.username == "demo").first()
    run = run_pipeline(user, _db_session, trigger="manual")
    assert run.search_calls == 3


def test_budget_counts_credits_not_calls(_db_session, monkeypatch):
    """Budget cap of 1 blocks an advanced call (2 credits) but not basic (1 credit)."""
    monkeypatch.setenv("SEARCH_DAILY_CALLS", "1")
    user = _db_session.query(User).filter(User.username == "demo").first()

    # Advanced (2 credits) should be blocked by cap=1
    run_adv = run_pipeline(user, _db_session, trigger="manual")
    assert run_adv.error == "budget: search"
    assert run_adv.search_calls == 0  # never called

    # Basic (1 credit) should fit under cap=1
    run_basic = run_pipeline(user, _db_session, trigger="scheduled")
    assert run_basic.error != "budget: search"
    assert run_basic.search_calls >= 1  # provider was called


def test_failed_call_still_counts_credits(_db_session, monkeypatch):
    """A failed search call still charges credits."""
    from unittest.mock import patch

    class _BoomProvider:
        name = "boom"
        def search(self, query, **kw):
            raise RuntimeError("boom")

    user = _db_session.query(User).filter(User.username == "demo").first()
    with patch("app.services.pipeline.get_search_provider",
               return_value=_BoomProvider()):
        run = run_pipeline(user, _db_session, trigger="manual")
    # advanced default = 2 credits, even though the call failed
    assert run.search_calls == 2


# ---------- daily_used helper ----------


def test_daily_used_sums_today(_db_session):
    from app.services.budget import daily_used

    user = _db_session.query(User).filter(User.username == "demo").first()
    _db_session.add(Run(
        user_id=user.id, started_at=datetime.now(UTC), trigger="manual",
        search_calls=10, llm_calls=5,
    ))
    _db_session.commit()

    assert daily_used(_db_session, "search_calls") >= 10
    assert daily_used(_db_session, "llm_calls") >= 5
