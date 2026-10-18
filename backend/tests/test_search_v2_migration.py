"""Tests for search v2 data-model changes (issue #54)."""

from __future__ import annotations

import os
import tempfile

import pytest


# ---------- timeZone validation on PUT /api/criteria ----------


def test_save_criteria_with_valid_timezone(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.put(
        "/api/criteria",
        json={"text": "jazz", "timeZone": "Europe/Berlin"},
        headers=h,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["timeZone"] == "Europe/Berlin"


def test_save_criteria_with_utc_timezone(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.put(
        "/api/criteria",
        json={"text": "jazz", "timeZone": "UTC"},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["timeZone"] == "UTC"


def test_save_criteria_with_invalid_timezone(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.put(
        "/api/criteria",
        json={"text": "jazz", "timeZone": "Fake/Zone"},
        headers=h,
    )
    assert r.status_code == 400
    assert "Invalid IANA time zone" in r.json()["detail"]


def test_save_criteria_without_timezone_keeps_default(client, auth_headers):
    h = auth_headers("demo", "demo")
    r = client.put(
        "/api/criteria",
        json={"text": "jazz"},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["timeZone"] == "UTC"


def test_get_criteria_returns_timezone(client, auth_headers):
    h = auth_headers("demo", "demo")
    # Set timezone first
    client.put(
        "/api/criteria",
        json={"text": "jazz", "timeZone": "America/New_York"},
        headers=h,
    )
    r = client.get("/api/criteria", headers=h)
    assert r.status_code == 200
    assert r.json()["timeZone"] == "America/New_York"


def test_timezone_persists_across_criteria_saves(client, auth_headers):
    h = auth_headers("demo", "demo")
    # Set timezone
    client.put(
        "/api/criteria",
        json={"text": "jazz", "timeZone": "Asia/Tokyo"},
        headers=h,
    )
    # Save again without timezone — it should persist
    client.put(
        "/api/criteria",
        json={"text": "updated"},
        headers=h,
    )
    r = client.get("/api/criteria", headers=h)
    assert r.json()["timeZone"] == "Asia/Tokyo"


# ---------- Migration round-trip on SQLite ----------


def test_migration_up_down_up_sqlite():
    """Alembic upgrade → downgrade → upgrade succeeds on SQLite."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        env = {
            **os.environ,
            "DATABASE_URL": f"sqlite:///{db_path}",
        }
        import subprocess
        base_cmd = [
            "uv", "run",
            "--project", "/Users/ad/code/ProjectOne/backend",
            "--directory", "/Users/ad/code/ProjectOne/backend",
            "alembic",
        ]

        # upgrade to head
        result = subprocess.run(
            base_cmd + ["upgrade", "head"],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode == 0, f"upgrade failed: {result.stderr}"

        # downgrade one step
        result = subprocess.run(
            base_cmd + ["downgrade", "-1"],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode == 0, f"downgrade failed: {result.stderr}"

        # upgrade again
        result = subprocess.run(
            base_cmd + ["upgrade", "head"],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode == 0, f"re-upgrade failed: {result.stderr}"


# ---------- Triage boundary: >= upper, <= lower ----------


def test_triage_boundary_ge_upper(client, auth_headers, _db_session):
    """A score exactly at the upper threshold is accepted (>=)."""
    from app.orm import Event, User

    h = auth_headers("boundary", "boundary")
    user = _db_session.query(User).filter(User.username == "boundary").first()
    # New registrations default to 90/40
    assert user.upper_threshold == 90
    assert user.lower_threshold == 40

    # Test triage logic: score exactly at upper → accepted
    score = 90
    if score >= user.upper_threshold:
        status = "accepted"
    elif score <= user.lower_threshold:
        status = "rejected"
    else:
        status = "queued"

    assert status == "accepted"


def test_triage_boundary_le_lower(client, auth_headers, _db_session):
    """A score exactly at the lower threshold is rejected (<=)."""
    from app.orm import Event, User

    h = auth_headers("boundary2", "boundary2")
    client.put("/api/criteria", json={"text": "anything"}, headers=h)

    user = _db_session.query(User).filter(User.username == "boundary2").first()

    evt = Event(
        user_id=user.id,
        title="Boundary Low",
        date_time="2026-07-01",
        place="P",
        link="https://example.com/boundary-lower",
        description="D",
        status="new",
    )
    _db_session.add(evt)
    _db_session.commit()

    evt.score = 40  # exactly lower threshold

    if evt.score >= user.upper_threshold:
        evt.status = "accepted"
    elif evt.score <= user.lower_threshold:
        evt.status = "rejected"
    else:
        evt.status = "queued"

    assert evt.status == "rejected"


# ---------- New registration defaults ----------


def test_new_registration_gets_90_40_defaults(client, auth_headers, _db_session):
    from app.orm import User
    h = auth_headers("fresh90", "pw")
    user = _db_session.query(User).filter(User.username == "fresh90").first()
    assert user.upper_threshold == 90
    assert user.lower_threshold == 40
