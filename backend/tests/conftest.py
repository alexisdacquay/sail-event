"""Shared test fixtures — per-test in-memory SQLite via ORM."""

from __future__ import annotations

import ipaddress
import os
import socket

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import hash_password
from app.db import get_db
from app.main import app
from app.orm import Base, Criteria, Event, User


# Default FAKE_NOW so all tests run on the fixed clock
os.environ.setdefault("FAKE_NOW", "2026-10-18T12:00:00+02:00")


_C1_TEXT = "jazz in Berlin (Germany) next week (19-21st October 2026)"
_C1_FACETS = {
    "place": {"city": "Berlin", "country": "DE", "region": None, "radius_km": None, "online": False},
    "date": {"start": "2026-10-19", "end": "2026-10-21", "relative": "next_week", "relative_n": None},
    "topics": ["jazz"],
    "topics_local": ["Jazz"],
    "formats": [],
    "budget": {"max_amount": None, "currency": None, "free_only": False},
    "language": "de",
    "input_language": "en",
    "other_constraints": [],
}


def _seed(db: Session) -> None:
    """Insert demo user with C1 criteria (90/40 thresholds), facets pre-parsed."""
    import hashlib
    import json

    user = User(
        username="demo",
        password_hash=hash_password("demo"),
        upper_threshold=90,
        lower_threshold=40,
        time_zone="Europe/Berlin",
        ics_token="demo-ics-token",
    )
    db.add(user)
    db.flush()

    text_sha = hashlib.sha256(_C1_TEXT.encode()).hexdigest()
    criteria = Criteria(
        user_id=user.id,
        text=_C1_TEXT,
        facets_json=json.dumps(_C1_FACETS),
        facets_version="criteria_v2",
        facets_text_sha=text_sha,
    )
    db.add(criteria)
    db.flush()

    # Seed accepted/queued/rejected events for tests that need them
    _seed_events = [
        {"title": "Jazz Trio at A-Trane", "date_time": "2026-10-20T21:00:00",
         "place": "A-Trane, Berlin", "link": "https://www.a-trane.de/events/jazz-trio",
         "description": "Live jazz trio", "score": 94,
         "score_reason": "Jazz trio at A-Trane in Berlin on Tue 20 Oct, 18 EUR: fits your dates and topic",
         "status": "accepted", "decided_by": "auto",
         "city": "Berlin", "country": "DE", "start_tz": "Europe/Berlin"},
        {"title": "Late Night Jam", "date_time": "2026-10-21T22:00:00",
         "place": "Zig Zag, Berlin", "link": "https://zigzag.example.com/jam",
         "description": "Jam session", "score": 92,
         "score_reason": "Late night jam at Zig Zag in Berlin on Wed 21 Oct: fits your dates and topic",
         "status": "accepted", "decided_by": "auto",
         "city": "Berlin", "country": "DE", "start_tz": "Europe/Berlin"},
        {"title": "Techno Night", "date_time": "2026-10-20T23:00:00",
         "place": "Berghain, Berlin", "link": "https://berghain.example.com/techno",
         "description": "Techno night", "score": 12,
         "score_reason": "Techno night at Berghain in Berlin on 20 Oct: right place and dates, not jazz",
         "status": "rejected", "decided_by": "auto",
         "city": "Berlin", "country": "DE", "start_tz": "Europe/Berlin"},
        {"title": "Jazz Workshop", "date_time": "2026-10-21T18:00:00",
         "place": "Berlin", "link": "https://workshop.example.com/jazz",
         "description": "Vocal jazz workshop", "score": 78,
         "score_reason": "Jazz vocal workshop in Berlin on Tue 21 Oct: fits your dates and topic",
         "status": "queued", "decided_by": None,
         "city": "Berlin", "country": "DE", "start_tz": "Europe/Berlin"},
    ]
    for ev_data in _seed_events:
        db.add(Event(user_id=user.id, **ev_data))

    db.commit()


def _loopback(host) -> bool:
    try:
        return ipaddress.ip_address(str(host).split("%")[0]).is_loopback
    except ValueError:
        return False


@pytest.fixture(autouse=True)
def _no_network(request, monkeypatch):
    """make test is offline: a test that looks up a host name or connects off loopback fails, even
    when the code under test swallowed the error.  Numeric hosts resolve without the network."""
    if request.node.get_closest_marker("integration"):
        yield
        return
    calls: list[str] = []
    real_getaddrinfo, real_connect = socket.getaddrinfo, socket.socket.connect

    def _getaddrinfo(host, port, *args, **kwargs):
        if host != "localhost":
            try:
                real_getaddrinfo(host, port, flags=socket.AI_NUMERICHOST)
            except (OSError, UnicodeError):
                calls.append(f"dns {host}")
                raise OSError(f"network blocked in tests: lookup of {host}")
        return real_getaddrinfo(host, port, *args, **kwargs)

    def _connect(self, address):
        if isinstance(address, tuple) and not _loopback(address[0]):
            calls.append(f"connect {address[0]}")
            raise OSError(f"network blocked in tests: connect to {address[0]}")
        return real_connect(self, address)

    monkeypatch.setattr(socket, "getaddrinfo", _getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", _connect)
    yield
    if calls:
        pytest.fail(f"live network in a unit test: {sorted(set(calls))}")


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
