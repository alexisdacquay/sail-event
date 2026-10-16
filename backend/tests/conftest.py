"""Shared test fixtures — reset store before each test."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.deps as deps_mod
import app.routers.auth as auth_router_mod
import app.routers.calendar as calendar_mod
import app.routers.search as search_mod
import app.store as store_mod
from app.main import app


@pytest.fixture(autouse=True)
def _reset_store():
    """Replace the global store with a fresh seed before every test."""
    fresh = store_mod._seed()
    store_mod.store = fresh
    deps_mod.store = fresh
    search_mod.store = fresh
    calendar_mod.store = fresh
    auth_router_mod.store = fresh
    yield


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def auth_headers(client):
    """Factory fixture: register+login a user, return Bearer headers dict.

    Usage: headers = auth_headers("alice", "pw123")
    The seeded 'demo' user can be logged in with auth_headers("demo", "demo").
    """
    def _make(username: str = "demo", password: str = "demo") -> dict[str, str]:
        # For non-demo users, register first
        if username != "demo":
            r = client.post(
                "/api/auth/register",
                json={"username": username, "password": password},
            )
            assert r.status_code == 201, f"register failed: {r.text}"

        r = client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        assert r.status_code == 200, f"login failed: {r.text}"
        token = r.json()["token"]
        return {"Authorization": f"Bearer {token}"}

    return _make
