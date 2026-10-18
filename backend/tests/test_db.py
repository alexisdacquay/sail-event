"""Tests for backend/app/db.py guard function."""

from __future__ import annotations

import pytest

from app.db import _resolve_database_url


# ---------- _resolve_database_url ----------


def test_resolve_database_url_exits_in_prod_without_url(monkeypatch):
    """APP_ENV=prod with no DATABASE_URL must exit immediately."""
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(SystemExit):
        _resolve_database_url()


def test_resolve_database_url_default_in_dev(monkeypatch):
    """Without DATABASE_URL and APP_ENV!=prod, returns the SQLite default."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    result = _resolve_database_url()
    assert result == "sqlite:///./sail_event.db"
