"""FastAPI dependencies — auth stub replaced by #7."""

from __future__ import annotations

from .store import UserRecord, store


def get_current_user() -> UserRecord:
    """Stub: always returns the single seeded 'demo' user."""
    return store.users["demo"]
