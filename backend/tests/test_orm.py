"""ORM constraint tests — in-memory SQLite, no migration needed."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.orm import Base, Criteria, Event, Run, User


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite://")

    # Enable FK enforcement for SQLite.
    @event.listens_for(engine, "connect")
    def _pragma(dbapi_conn, _rec):  # noqa: ANN001
        import sqlite3
        if isinstance(dbapi_conn, sqlite3.Connection):
            dbapi_conn.execute("PRAGMA foreign_keys = ON")

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _user(**overrides) -> User:
    defaults = dict(
        username="alice",
        password_hash="hashed",
        upper_threshold=70,
        lower_threshold=30,
    )
    defaults.update(overrides)
    return User(**defaults)


def _insert_user(db: Session, **overrides) -> User:
    u = _user(**overrides)
    db.add(u)
    db.commit()
    return u


# --- valid insert ---

def test_insert_valid_rows(db: Session) -> None:
    user = _insert_user(db)
    assert user.id is not None
    assert user.ics_token is not None

    crit = Criteria(user_id=user.id, text="outdoor music")
    db.add(crit)
    db.commit()
    assert crit.id is not None

    run = Run(user_id=user.id, started_at=user.created_at, trigger="manual")
    db.add(run)
    db.commit()

    evt = Event(
        user_id=user.id,
        title="Jazz Fest",
        date_time="2026-07-01T18:00",
        place="Portland",
        link="https://example.com/jazz",
        description="A jazz festival",
        status="new",
        run_id=run.id,
    )
    db.add(evt)
    db.commit()
    assert evt.id is not None


# --- (a) duplicate username ---

def test_duplicate_username(db: Session) -> None:
    _insert_user(db, username="bob")
    with pytest.raises(IntegrityError):
        _insert_user(db, username="bob")


# --- (b) duplicate ics_token ---

def test_duplicate_ics_token(db: Session) -> None:
    u1 = _insert_user(db, username="carol")
    token = u1.ics_token
    with pytest.raises(IntegrityError):
        u2 = User(
            username="dave",
            password_hash="hashed",
            upper_threshold=80,
            lower_threshold=20,
            ics_token=token,
        )
        db.add(u2)
        db.commit()


# --- (c) duplicate (user_id, link, date_time) on Event ---

def test_duplicate_user_link_date(db: Session) -> None:
    """Same user + link + date_time → IntegrityError."""
    user = _insert_user(db)
    e1 = Event(
        user_id=user.id,
        title="E1",
        date_time="2026-07-01",
        place="P",
        link="https://example.com/dup",
        description="D",
        status="new",
    )
    db.add(e1)
    db.commit()

    e2 = Event(
        user_id=user.id,
        title="E2",
        date_time="2026-07-01",
        place="P2",
        link="https://example.com/dup",
        description="D2",
        status="new",
    )
    db.add(e2)
    with pytest.raises(IntegrityError):
        db.commit()


def test_same_link_different_date_allowed(db: Session) -> None:
    """Same user + link with different date_time is allowed (listing pages)."""
    user = _insert_user(db)
    e1 = Event(
        user_id=user.id,
        title="E1",
        date_time="2026-07-01",
        place="P",
        link="https://example.com/dup",
        description="D",
        status="new",
    )
    db.add(e1)
    db.commit()

    e2 = Event(
        user_id=user.id,
        title="E2",
        date_time="2026-07-02",
        place="P2",
        link="https://example.com/dup",
        description="D2",
        status="new",
    )
    db.add(e2)
    db.commit()
    assert e2.id is not None


# --- (d) lower_threshold >= upper_threshold ---

def test_threshold_check(db: Session) -> None:
    with pytest.raises(IntegrityError):
        _insert_user(db, username="eve", lower_threshold=70, upper_threshold=70)


def test_threshold_lower_gt_upper_raises_integrity_error(db: Session) -> None:
    with pytest.raises(IntegrityError):
        _insert_user(db, username="flip", lower_threshold=80, upper_threshold=70)


# --- (e) invalid status on Event ---

def test_invalid_event_status(db: Session) -> None:
    user = _insert_user(db)
    evt = Event(
        user_id=user.id,
        title="Bad",
        date_time="2026-07-01",
        place="P",
        link="https://example.com/bad",
        description="D",
        status="bogus",
    )
    db.add(evt)
    with pytest.raises(IntegrityError):
        db.commit()
