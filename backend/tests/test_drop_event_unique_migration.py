"""Migration a6b7c8d9e0f1: events are no longer unique on (user_id, link, date_time) (owner decision 2026-10-25)."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

BEFORE, DROP = "f5a6b7c8d9e0", "a6b7c8d9e0f1"
INSERT = sa.text(
    "INSERT INTO events (id, user_id, title, date_time, place, link, description, status, created_at)"
    " VALUES (:id, 'u', :id, '2026-10-29T18:00+00:00', 'London', 'https://listing.example/tech', 'd', 'new', '2026-10-25')"
)


def test_two_events_same_link_and_start_both_stored(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'm.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = Config()  # no ini file: env.py skips fileConfig, so pytest logging is left alone
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parent.parent / "alembic"))
    command.upgrade(cfg, BEFORE)
    engine = sa.create_engine(url)
    with engine.begin() as c:
        c.execute(sa.text(
            "INSERT INTO users (id, username, password_hash, upper_threshold, lower_threshold, ics_token, created_at)"
            " VALUES ('u', 'u', 'x', 90, 40, 'tok', '2026-10-25')"
        ))
        c.execute(INSERT, {"id": "movie-club"})
    with pytest.raises(sa.exc.IntegrityError), engine.begin() as c:
        c.execute(INSERT, {"id": "debate"})  # the constraint is there before

    command.upgrade(cfg, DROP)
    with engine.begin() as c:
        c.execute(INSERT, {"id": "debate"})
        assert c.execute(sa.text("SELECT count(*) FROM events")).scalar() == 2
        with pytest.raises(sa.exc.IntegrityError), c.begin_nested():
            c.execute(sa.text("UPDATE events SET status = 'bogus'"))  # status CHECK survives the table rebuild

    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM events WHERE id = 'debate'"))
    command.downgrade(cfg, BEFORE)  # restores the constraint once no two rows share the key
    with pytest.raises(sa.exc.IntegrityError), engine.begin() as c:
        c.execute(INSERT, {"id": "debate"})
    engine.dispose()
