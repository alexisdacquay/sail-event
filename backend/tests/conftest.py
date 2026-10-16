"""Shared test fixtures — reset store before each test."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.deps as deps_mod
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
    yield


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
