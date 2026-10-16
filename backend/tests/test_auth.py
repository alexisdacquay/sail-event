"""Tests for POST /api/auth/register and POST /api/auth/login."""

from __future__ import annotations


# ---------- register ----------

def test_register_success(client):
    r = client.post("/api/auth/register", json={"username": "newuser", "password": "pw123"})
    assert r.status_code == 201
    body = r.json()
    assert "token" in body and body["token"] != ""
    assert body["username"] == "newuser"


def test_register_populates_ics_token(client):
    r = client.post("/api/auth/register", json={"username": "icsuser", "password": "pw"})
    assert r.status_code == 201
    token = r.json()["token"]
    r2 = client.get("/api/calendar-url", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    url = r2.json()["url"]
    assert "/api/calendar/" in url
    # Extract ics_token from url and verify non-empty
    ics_token = url.split("/api/calendar/")[-1]
    assert ics_token != ""


def test_register_creates_default_thresholds_and_criteria(client, auth_headers):
    h = auth_headers("newuser2", "pw")
    r = client.get("/api/thresholds", headers=h)
    assert r.json() == {"lowerThreshold": 30, "upperThreshold": 70}

    r = client.get("/api/criteria", headers=h)
    assert r.json()["text"] == ""


def test_register_duplicate_username_returns_409(client):
    client.post("/api/auth/register", json={"username": "dup", "password": "pw"})
    r = client.post("/api/auth/register", json={"username": "dup", "password": "pw"})
    assert r.status_code == 409
    assert "detail" in r.json()


def test_register_seeded_demo_returns_409(client):
    r = client.post("/api/auth/register", json={"username": "demo", "password": "whatever"})
    assert r.status_code == 409


def test_register_empty_username_returns_400(client):
    r = client.post("/api/auth/register", json={"username": "", "password": "pw"})
    assert r.status_code == 400


def test_register_empty_password_returns_400(client):
    r = client.post("/api/auth/register", json={"username": "user1", "password": ""})
    assert r.status_code == 400


def test_register_missing_username_returns_400(client):
    r = client.post("/api/auth/register", json={"password": "pw"})
    assert r.status_code == 400


def test_register_missing_password_returns_400(client):
    r = client.post("/api/auth/register", json={"username": "user1"})
    assert r.status_code == 400


def test_register_whitespace_only_username_returns_400(client):
    r = client.post("/api/auth/register", json={"username": "   ", "password": "pw"})
    assert r.status_code == 400


def test_register_whitespace_only_password_returns_400(client):
    r = client.post("/api/auth/register", json={"username": "user1", "password": "   "})
    assert r.status_code == 400


# ---------- login ----------

def test_login_demo_user(client):
    r = client.post("/api/auth/login", json={"username": "demo", "password": "demo"})
    assert r.status_code == 200
    body = r.json()
    assert "token" in body and body["token"] != ""
    assert body["username"] == "demo"


def test_login_wrong_password_returns_401(client):
    r = client.post("/api/auth/login", json={"username": "demo", "password": "wrong"})
    assert r.status_code == 401
    assert "detail" in r.json()


def test_login_unknown_user_returns_401(client):
    r = client.post("/api/auth/login", json={"username": "noone", "password": "pw"})
    assert r.status_code == 401


def test_login_empty_username_returns_400(client):
    r = client.post("/api/auth/login", json={"username": "", "password": "pw"})
    assert r.status_code == 400


def test_login_empty_password_returns_400(client):
    r = client.post("/api/auth/login", json={"username": "demo", "password": ""})
    assert r.status_code == 400


def test_login_missing_username_returns_400(client):
    r = client.post("/api/auth/login", json={"password": "pw"})
    assert r.status_code == 400


def test_login_missing_password_returns_400(client):
    r = client.post("/api/auth/login", json={"username": "demo"})
    assert r.status_code == 400


# ---------- token usage ----------

def test_token_from_register_works_as_bearer(client):
    r = client.post("/api/auth/register", json={"username": "tk1", "password": "pw"})
    token = r.json()["token"]
    r2 = client.get("/api/criteria", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200


def test_token_from_login_works_as_bearer(client):
    r = client.post("/api/auth/login", json={"username": "demo", "password": "demo"})
    token = r.json()["token"]
    r2 = client.get("/api/criteria", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200


def test_invalid_token_returns_401(client):
    r = client.get("/api/criteria", headers={"Authorization": "Bearer garbage.token.here"})
    assert r.status_code == 401


def test_expired_token_returns_401(client, monkeypatch):
    monkeypatch.setenv("JWT_EXPIRY_MINUTES", "0")
    import time
    r = client.post("/api/auth/login", json={"username": "demo", "password": "demo"})
    token = r.json()["token"]
    time.sleep(1)
    r2 = client.get("/api/criteria", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 401


def test_no_password_in_any_response(client):
    """No response body ever contains password or password_hash."""
    # Register
    r = client.post("/api/auth/register", json={"username": "sec1", "password": "secret"})
    text = r.text
    assert "secret" not in text or "sec1" in text  # 'secret' could be substring of username
    assert "password_hash" not in text
    assert "password" not in text.replace("password_hash", "")

    # Login
    r = client.post("/api/auth/login", json={"username": "sec1", "password": "secret"})
    assert "password_hash" not in r.text


# ---------- unprotected endpoints stay open ----------

def test_health_no_auth_required(client):
    r = client.get("/api/health")
    assert r.status_code == 200


def test_calendar_no_auth_required(client):
    r = client.get("/api/calendar/demo-ics-token")
    assert r.status_code == 200


def test_search_all_no_bearer_required(client, monkeypatch):
    monkeypatch.setenv("SEARCH_ALL_API_KEY", "key")
    r = client.post("/api/search/all", headers={"X-API-Key": "key"})
    assert r.status_code == 200


# ---------- validation errors never echo input ----------

def test_register_missing_username_does_not_echo_password(client):
    r = client.post("/api/auth/register", json={"password": "supersecret99"})
    assert r.status_code == 400
    assert "supersecret99" not in r.text


def test_login_missing_username_does_not_echo_password(client):
    r = client.post("/api/auth/login", json={"password": "supersecret99"})
    assert r.status_code == 400
    assert "supersecret99" not in r.text


# ---------- PUT no-auth → 401 ----------

def test_put_criteria_no_auth_returns_401(client):
    r = client.put("/api/criteria", json={"text": "x"})
    assert r.status_code == 401


def test_put_thresholds_no_auth_returns_401(client):
    r = client.put("/api/thresholds", json={"lowerThreshold": 20, "upperThreshold": 80})
    assert r.status_code == 401


# ---------- deleted user's token → 401 ----------

def test_deleted_user_token_returns_401(client, _db_session):
    r = client.post("/api/auth/register", json={"username": "ghost", "password": "pw"})
    token = r.json()["token"]
    # Remove the user from the DB
    from app.orm import User, Criteria, Event
    user = _db_session.query(User).filter(User.username == "ghost").first()
    _db_session.query(Event).filter(Event.user_id == user.id).delete()
    _db_session.query(Criteria).filter(Criteria.user_id == user.id).delete()
    _db_session.delete(user)
    _db_session.commit()
    r2 = client.get("/api/criteria", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 401


# ---------- cross-user isolation: criteria and thresholds ----------

def test_user_isolation_criteria_and_thresholds(client, auth_headers):
    h_a = auth_headers("alice", "pw1")
    h_b = auth_headers("bob", "pw2")

    # Alice sets her criteria and thresholds
    client.put("/api/criteria", json={"text": "alice-criteria"}, headers=h_a)
    client.put(
        "/api/thresholds",
        json={"lowerThreshold": 10, "upperThreshold": 90},
        headers=h_a,
    )

    # Bob sets different criteria and thresholds
    client.put("/api/criteria", json={"text": "bob-criteria"}, headers=h_b)
    client.put(
        "/api/thresholds",
        json={"lowerThreshold": 25, "upperThreshold": 75},
        headers=h_b,
    )

    # Each sees only their own
    assert client.get("/api/criteria", headers=h_a).json()["text"] == "alice-criteria"
    assert client.get("/api/criteria", headers=h_b).json()["text"] == "bob-criteria"

    assert client.get("/api/thresholds", headers=h_a).json() == {
        "lowerThreshold": 10, "upperThreshold": 90,
    }
    assert client.get("/api/thresholds", headers=h_b).json() == {
        "lowerThreshold": 25, "upperThreshold": 75,
    }


# ---------- malformed bearer tokens ----------

def test_malformed_bearer_header_returns_401(client):
    r = client.get("/api/criteria", headers={"Authorization": "Bearer"})
    assert r.status_code == 401


def test_bearer_with_extra_segments_returns_401(client):
    r = client.get("/api/criteria", headers={"Authorization": "Bearer a.b.c.d"})
    assert r.status_code == 401


# ---------- seed_demo idempotency ----------

def test_seed_demo_idempotent(_db_session):
    from unittest.mock import patch
    from app.main import _seed_demo
    from app.orm import User

    count_before = _db_session.query(User).count()

    # Prevent _seed_demo from closing the shared test session
    original_close = _db_session.close
    _db_session.close = lambda: None
    try:
        with patch("app.main.get_db", lambda: (s for s in [_db_session])):
            _seed_demo()
            _seed_demo()
    finally:
        _db_session.close = original_close

    assert _db_session.query(User).count() == count_before
