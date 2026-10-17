"""Integration test fixtures — HTTP client against the live compose stack."""

from __future__ import annotations

import os

import httpx
import pytest

BASE_URL = os.environ.get(
    "SAIL_BASE_URL",
    f"http://localhost:{os.environ.get('HOST_PORT', '8000')}",
)


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def api_key() -> str:
    return os.environ.get("SEARCH_ALL_API_KEY", "dev-api-key")


@pytest.fixture()
def http() -> httpx.Client:
    with httpx.Client(base_url=BASE_URL, timeout=10) as c:
        yield c


def _register_and_login(
    http: httpx.Client, username: str, password: str
) -> dict[str, str]:
    """Register + login, return Bearer headers."""
    http.post("/api/auth/register", json={"username": username, "password": password})
    r = http.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, f"login failed for {username}: {r.text}"
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture()
def user_factory(http):
    """Factory: user_factory("alice", "pw") -> headers dict."""
    return lambda u, p: _register_and_login(http, u, p)
