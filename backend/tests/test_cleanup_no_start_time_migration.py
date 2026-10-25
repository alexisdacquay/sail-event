"""Data migration f5a6b7c8d9e0: stored events without a start time are deleted (owner decision 2026-10-25)."""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config

BEFORE, CLEANUP = "e4f5a6b7c8d9", "f5a6b7c8d9e0"
STATUSES = ("accepted", "queued", "rejected", "new")


def _snapshot(engine) -> dict[str, list[tuple]]:
    with engine.connect() as c:
        return {t: sorted(map(tuple, c.execute(sa.text(f"SELECT * FROM {t}"))))
                for t in ("users", "criteria", "runs", "events")}


def test_cleanup_deletes_date_only_events_and_downgrade_is_noop(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'm.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = Config()  # no ini file: env.py skips fileConfig, so pytest logging is left alone
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parent.parent / "alembic"))
    command.upgrade(cfg, BEFORE)

    engine = sa.create_engine(url)
    with engine.begin() as c:
        c.execute(sa.text(
            "INSERT INTO users (id, username, password_hash, upper_threshold, lower_threshold, ics_token, created_at)"
            " VALUES ('u', 'u', 'x', 90, 40, 'tok', '2026-10-20')"
        ))
        c.execute(sa.text("INSERT INTO criteria (id, user_id, text, updated_at) VALUES ('c', 'u', 'jazz', '2026-10-20')"))
        c.execute(sa.text(
            "INSERT INTO runs (id, user_id, started_at, events_found, events_new, trigger)"
            " VALUES ('r', 'u', '2026-10-20', 8, 8, 'manual')"
        ))
        # One date-only and one timed event per status; "accepted-day" is the reported "Best Of", Berlin, no time.
        for status in STATUSES:
            for kind, dt in (("day", "2026-10-21"), ("timed", "2026-10-21T19:00:00+02:00")):
                c.execute(sa.text(
                    "INSERT INTO events (id, user_id, title, date_time, place, link, description, status, run_id, created_at)"
                    " VALUES (:id, 'u', 'Best Of', :dt, 'Berlin', :link, 'd', :status, 'r', '2026-10-20')"
                ), {"id": f"{status}-{kind}", "dt": dt, "link": f"https://example.com/{status}-{kind}", "status": status})
    before = _snapshot(engine)

    command.upgrade(cfg, CLEANUP)
    after = _snapshot(engine)
    assert sorted(r[0] for r in after["events"]) == sorted(f"{s}-timed" for s in STATUSES)
    assert after["events"] == [r for r in before["events"] if r[0].endswith("-timed")]  # timed rows unchanged
    for table in ("users", "criteria", "runs"):
        assert after[table] == before[table]

    command.downgrade(cfg, BEFORE)  # irreversible: nothing comes back, nothing else changes
    assert _snapshot(engine) == after
    engine.dispose()
