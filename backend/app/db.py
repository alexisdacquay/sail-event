"""Database engine, session factory, and FastAPI dependency."""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./sail_event.db")

engine = create_engine(DATABASE_URL)

# SQLite disables foreign keys by default; enable them on every connection.
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):  # noqa: ANN001
    import sqlite3
    if isinstance(dbapi_conn, sqlite3.Connection):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a session and closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
