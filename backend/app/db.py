"""Database engine, session factory, and FastAPI dependency."""

from __future__ import annotations

import os
import sys
from collections.abc import Generator

from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def _resolve_database_url() -> str:
    """Resolve database URL from environment.

    Called once at import time; result cached in ``DATABASE_URL``.
    """
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return url
    if os.environ.get("APP_ENV", "").strip().lower() == "prod":
        sys.exit(
            "FATAL: DATABASE_URL environment variable is missing or empty"
            " (APP_ENV=prod)"
        )
    return "sqlite:///./sail_event.db"


DATABASE_URL: str = _resolve_database_url()

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
