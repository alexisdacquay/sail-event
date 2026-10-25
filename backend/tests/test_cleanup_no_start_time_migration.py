"""Data migration f5a6b7c8d9e0: stored events without a start time leave the calendar (owner decision 2026-10-25)."""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config

BEFORE, CLEANUP = "e4f5a6b7c8d9", "f5a6b7c8d9e0"
REASON = "No start time (cleanup 2026-10-25)"


def _rows(engine) -> dict[str, tuple]:
    with engine.connect() as c:
        return {r[0]: tuple(r[1:]) for r in c.execute(sa.text("SELECT id, status, score_reason, decided_by FROM events"))}


def test_cleanup_rejects_date_only_events_and_downgrade_requeues(tmp_path, monkeypatch):
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
        for id_, dt, status, decided_by in [
            ("best-of", "2026-10-21", "accepted", "user"),  # the reported "Best Of", Berlin, no time
            ("queued-day", "2026-10-22", "queued", None),
            ("timed", "2026-10-21T19:00:00+02:00", "accepted", "auto"),
            ("new-day", "2026-10-23", "new", None),
            ("rejected-day", "2026-10-24", "rejected", "auto"),
        ]:
            c.execute(sa.text(
                "INSERT INTO events (id, user_id, title, date_time, place, link, description, score_reason,"
                " status, decided_by, created_at)"
                " VALUES (:id, 'u', 't', :dt, 'Berlin', :link, 'd', 'judge says fit', :status, :decided_by, '2026-10-20')"
            ), {"id": id_, "dt": dt, "link": f"https://example.com/{id_}", "status": status, "decided_by": decided_by})

    command.upgrade(cfg, CLEANUP)
    rows = _rows(engine)
    assert rows["best-of"] == ("rejected", REASON, "user")
    assert rows["queued-day"] == ("rejected", REASON, None)
    assert rows["timed"] == ("accepted", "judge says fit", "auto")
    assert rows["new-day"] == ("new", "judge says fit", None)
    assert rows["rejected-day"] == ("rejected", "judge says fit", "auto")

    command.downgrade(cfg, BEFORE)
    rows = _rows(engine)
    assert len(rows) == 5
    assert rows["best-of"][0] == "queued"
    assert rows["queued-day"][0] == "queued"
    assert rows["timed"] == ("accepted", "judge says fit", "auto")
    assert rows["rejected-day"] == ("rejected", "judge says fit", "auto")
    engine.dispose()
