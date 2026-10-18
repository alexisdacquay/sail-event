"""Sync handlers must not block the event loop (#37)."""

from __future__ import annotations

import asyncio
import time

import httpx
import pytest

from app.auth import create_token
from app.main import app
from app.orm import User


@pytest.mark.anyio
async def test_search_does_not_block_event_loop(_db_session, monkeypatch):
    """A slow run_pipeline (2 s sleep) must not block GET /api/health."""
    user = _db_session.query(User).filter(User.username == "demo").first()
    token = create_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    def slow_pipeline(user, db, *, trigger):  # noqa: ARG001
        time.sleep(2)

        class _FakeRun:
            id = "fake"
            events_found = 0
            events_new = 0
            error = None

        return _FakeRun()

    monkeypatch.setattr("app.routers.search.run_pipeline", slow_pipeline)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        t0 = time.monotonic()
        health_elapsed = None

        async def timed_health():
            nonlocal health_elapsed
            resp = await ac.get("/api/health")
            health_elapsed = time.monotonic() - t0
            return resp

        health_task = asyncio.create_task(timed_health())
        search_task = asyncio.create_task(
            ac.post("/api/search", headers=headers),
        )
        health_resp, search_resp = await asyncio.gather(health_task, search_task)

    assert health_resp.status_code == 200
    assert health_elapsed < 1.0, f"health took {health_elapsed:.2f}s, blocked by search"
    assert search_resp.status_code == 200
