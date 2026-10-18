"""Integration tests — full compose stack over HTTP.

Every test is marked @pytest.mark.integration and excluded from `make test`.
"""

from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

import httpx
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]

pytestmark = pytest.mark.integration


def _unique(prefix: str = "u") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ---------- health ----------


def test_health(http: httpx.Client):
    r = http.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------- full user journey ----------


def test_full_journey(http: httpx.Client):
    """register → login → criteria → thresholds → search → list → decide → re-fetch."""
    user, pw = _unique(), "pass1234"

    # register + login
    r = http.post("/api/auth/register", json={"username": user, "password": pw})
    assert r.status_code == 201
    r = http.post("/api/auth/login", json={"username": user, "password": pw})
    assert r.status_code == 200
    headers = {"Authorization": f"Bearer {r.json()['token']}"}

    # set criteria
    r = http.put("/api/criteria", json={"text": "outdoor concerts"}, headers=headers)
    assert r.status_code == 200

    # set thresholds
    r = http.put(
        "/api/thresholds",
        json={"lowerThreshold": 20, "upperThreshold": 80},
        headers=headers,
    )
    assert r.status_code == 200

    # search
    r = http.post("/api/search", headers=headers)
    assert r.status_code == 200
    assert r.json()["eventsFound"] >= 0

    # list events (all statuses)
    r = http.get("/api/events", headers=headers)
    assert r.status_code == 200
    events = r.json()
    assert isinstance(events, list)

    # pick two events to decide on — need at least two
    if len(events) < 2:
        pytest.skip("fixture returned fewer than 2 events")
    evt_accept, evt_reject = events[0], events[1]

    # accept one
    r = http.post(
        f"/api/events/{evt_accept['id']}/decision",
        json={"decision": "accepted"},
        headers=headers,
    )
    assert r.status_code == 200

    # reject one
    r = http.post(
        f"/api/events/{evt_reject['id']}/decision",
        json={"decision": "rejected"},
        headers=headers,
    )
    assert r.status_code == 200

    # re-fetch and verify status persists
    r = http.get("/api/events", headers=headers)
    by_id = {e["id"]: e for e in r.json()}
    assert by_id[evt_accept["id"]]["status"] == "accepted"
    assert by_id[evt_reject["id"]]["status"] == "rejected"


# ---------- dedup ----------


def test_dedup(http: httpx.Client):
    """Two searches with identical criteria produce no duplicate events."""
    user, pw = _unique(), "pass1234"
    r = http.post("/api/auth/register", json={"username": user, "password": pw})
    assert r.status_code == 201
    r = http.post("/api/auth/login", json={"username": user, "password": pw})
    headers = {"Authorization": f"Bearer {r.json()['token']}"}

    http.put("/api/criteria", json={"text": "anything"}, headers=headers)
    http.put(
        "/api/thresholds",
        json={"lowerThreshold": 20, "upperThreshold": 80},
        headers=headers,
    )

    http.post("/api/search", headers=headers)
    http.post("/api/search", headers=headers)

    r = http.get("/api/events", headers=headers)
    events = r.json()
    links = [e["link"] for e in events]
    assert len(links) == len(set(links)), "duplicate events after two searches"


# ---------- user isolation ----------


def test_user_isolation(http: httpx.Client):
    """User A's events are invisible to user B."""
    ua, pa = _unique("a"), "pass"
    ub, pb = _unique("b"), "pass"

    # user A: register, criteria, search
    http.post("/api/auth/register", json={"username": ua, "password": pa})
    r = http.post("/api/auth/login", json={"username": ua, "password": pa})
    ha = {"Authorization": f"Bearer {r.json()['token']}"}
    http.put("/api/criteria", json={"text": "music"}, headers=ha)
    http.put(
        "/api/thresholds",
        json={"lowerThreshold": 20, "upperThreshold": 80},
        headers=ha,
    )
    http.post("/api/search", headers=ha)

    r = http.get("/api/events", headers=ha)
    assert len(r.json()) > 0, "user A should have events"

    # user B: register, no search
    http.post("/api/auth/register", json={"username": ub, "password": pb})
    r = http.post("/api/auth/login", json={"username": ub, "password": pb})
    hb = {"Authorization": f"Bearer {r.json()['token']}"}

    r = http.get("/api/events", headers=hb)
    assert len(r.json()) == 0, "user B sees user A's events"


# ---------- search/all ----------


def test_search_all(http: httpx.Client, api_key: str):
    """POST /api/search/all creates runs for users with criteria."""
    user, pw = _unique(), "pass"
    http.post("/api/auth/register", json={"username": user, "password": pw})
    r = http.post("/api/auth/login", json={"username": user, "password": pw})
    headers = {"Authorization": f"Bearer {r.json()['token']}"}
    http.put("/api/criteria", json={"text": "festivals"}, headers=headers)
    http.put(
        "/api/thresholds",
        json={"lowerThreshold": 20, "upperThreshold": 80},
        headers=headers,
    )

    r = http.post("/api/search/all", headers={"X-API-Key": api_key})
    assert r.status_code == 200
    assert r.json()["usersProcessed"] >= 1


# ---------- ICS feed ----------


def test_ics_feed(http: httpx.Client):
    """ICS feed lists accepted events; rejecting an accepted event removes it."""
    user, pw = _unique(), "pass"
    http.post("/api/auth/register", json={"username": user, "password": pw})
    r = http.post("/api/auth/login", json={"username": user, "password": pw})
    headers = {"Authorization": f"Bearer {r.json()['token']}"}

    http.put("/api/criteria", json={"text": "art"}, headers=headers)
    http.put(
        "/api/thresholds",
        json={"lowerThreshold": 20, "upperThreshold": 80},
        headers=headers,
    )
    http.post("/api/search", headers=headers)

    # get calendar URL
    r = http.get("/api/calendar-url", headers=headers)
    assert r.status_code == 200
    cal_url = r.json()["url"]
    # cal_url is absolute; extract path
    from urllib.parse import urlparse

    cal_path = urlparse(cal_url).path

    # accept one event
    r = http.get("/api/events", headers=headers)
    events = r.json()
    if not events:
        pytest.skip("no events to test ICS with")
    evt = events[0]
    http.post(
        f"/api/events/{evt['id']}/decision",
        json={"decision": "accepted"},
        headers=headers,
    )

    # ICS should contain the event
    r = http.get(cal_path)
    assert r.status_code == 200
    assert "VEVENT" in r.text
    assert evt["title"] in r.text

    # reject that event
    http.post(
        f"/api/events/{evt['id']}/decision",
        json={"decision": "rejected"},
        headers=headers,
    )

    # ICS should no longer contain it
    r = http.get(cal_path)
    assert evt["title"] not in r.text


# ---------- data survives restart ----------


@pytest.mark.skipif(
    "SAIL_BASE_URL" in os.environ and os.environ.get("SAIL_COMPOSE_MANAGED") != "1",
    reason="compose managed externally; cannot restart app",
)
def test_data_survives_restart(http: httpx.Client, base_url: str):
    """Data persists across docker compose restart app."""
    user, pw = _unique(), "pass"
    http.post("/api/auth/register", json={"username": user, "password": pw})
    r = http.post("/api/auth/login", json={"username": user, "password": pw})
    headers = {"Authorization": f"Bearer {r.json()['token']}"}

    http.put("/api/criteria", json={"text": "sailing"}, headers=headers)
    http.put(
        "/api/thresholds",
        json={"lowerThreshold": 20, "upperThreshold": 80},
        headers=headers,
    )
    http.post("/api/search", headers=headers)

    r = http.get("/api/events", headers=headers)
    count_before = len(r.json())
    assert count_before > 0

    # restart app service (not postgres)
    subprocess.run(
        ["docker", "compose", "restart", "app"],
        cwd=str(_REPO_ROOT),
        check=True,
        capture_output=True,
    )

    # wait for health
    import time

    for _ in range(30):
        try:
            r = http.get("/api/health")
            if r.status_code == 200:
                break
        except (httpx.ConnectError, httpx.RemoteProtocolError):
            pass
        time.sleep(1)
    else:
        pytest.fail("app did not become healthy after restart")

    # re-login (JWT may still be valid, but re-login to be safe)
    r = http.post("/api/auth/login", json={"username": user, "password": pw})
    assert r.status_code == 200
    headers = {"Authorization": f"Bearer {r.json()['token']}"}

    r = http.get("/api/events", headers=headers)
    assert len(r.json()) == count_before
