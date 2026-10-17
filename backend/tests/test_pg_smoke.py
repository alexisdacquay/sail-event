"""Postgres smoke test — skipped when TEST_DATABASE_URL is not set."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.orm import Event, User

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    TEST_DATABASE_URL is None,
    reason="TEST_DATABASE_URL not set",
)


@pytest.fixture()
def pg_session():
    """Session against an existing Postgres (schema from alembic); rolls back after the test."""
    engine = create_engine(TEST_DATABASE_URL)
    conn = engine.connect()
    txn = conn.begin()
    session = sessionmaker(bind=conn)()
    yield session
    session.close()
    txn.rollback()
    conn.close()
    engine.dispose()


def test_insert_and_query(pg_session: Session) -> None:
    user = User(
        username="pgtest",
        password_hash="x",
        upper_threshold=70,
        lower_threshold=30,
    )
    pg_session.add(user)
    pg_session.flush()

    evt = Event(
        user_id=user.id,
        title="PG smoke event",
        date_time="2026-01-01T10:00:00",
        place="Testville",
        link="https://example.com/pg-smoke",
        description="Smoke test event",
        score=55,
        score_reason="test",
        status="queued",
    )
    pg_session.add(evt)
    pg_session.commit()

    row = pg_session.query(Event).filter_by(user_id=user.id).one()
    assert row.title == "PG smoke event"
    assert row.link == "https://example.com/pg-smoke"
