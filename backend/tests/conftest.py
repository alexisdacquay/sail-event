"""Shared test fixtures — per-test in-memory SQLite via ORM."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.adapters import FakeScorer, FixtureSearchProvider
from app.auth import hash_password
from app.db import get_db
from app.main import app
from app.orm import Base, Criteria, Event, User


def _seed(db: Session) -> None:
    """Insert demo user, criteria, and fixture events."""
    user = User(
        username="demo",
        password_hash=hash_password("demo"),
        upper_threshold=70,
        lower_threshold=30,
        ics_token="demo-ics-token",
    )
    db.add(user)
    db.flush()

    criteria = Criteria(
        user_id=user.id,
        text="outdoor activities, live music, and art workshops near Portland",
    )
    db.add(criteria)
    db.flush()

    # Generate fixture events: search, dedup, score, triage
    provider = FixtureSearchProvider()
    scorer = FakeScorer()
    raw_events = provider.search([])

    seen_links: set[str] = set()
    for raw in raw_events:
        if raw.link in seen_links:
            continue
        seen_links.add(raw.link)

        score_val, reason = scorer.score(raw, criteria.text)

        if score_val > user.upper_threshold:
            status = "accepted"
            decided_by = "auto"
        elif score_val < user.lower_threshold:
            status = "rejected"
            decided_by = "auto"
        else:
            status = "queued"
            decided_by = None

        evt = Event(
            user_id=user.id,
            title=raw.title,
            date_time=raw.date_time,
            place=raw.place,
            link=raw.link,
            description=raw.description,
            score=score_val,
            score_reason=reason,
            status=status,
            decided_by=decided_by,
        )
        db.add(evt)

    db.commit()


@pytest.fixture(autouse=True)
def _db_session():
    """Per-test in-memory SQLite with schema and seed data."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _pragma(dbapi_conn, _rec):
        import sqlite3
        if isinstance(dbapi_conn, sqlite3.Connection):
            dbapi_conn.execute("PRAGMA foreign_keys = ON")

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    session = TestingSessionLocal()
    _seed(session)

    def override_get_db():
        try:
            yield session
        finally:
            pass  # session stays open for the whole test

    app.dependency_overrides[get_db] = override_get_db
    yield session
    session.close()
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _clear_rate_limiter():
    """Reset rate limiters between tests."""
    from app.routers.auth import _login_failures, _register_successes
    _login_failures.clear()
    _register_successes.clear()
    yield
    _login_failures.clear()
    _register_successes.clear()


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
