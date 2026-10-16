"""Password hashing (bcrypt) and JWT encode/decode helpers."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

logger = logging.getLogger(__name__)

_DEV_SECRET = "sail-event-dev-secret-do-not-use-in-prod"


def _jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET", "").strip()
    if not secret:
        logger.warning(
            "JWT_SECRET is unset or empty — using hardcoded dev default. "
            "Do NOT use this in production."
        )
        return _DEV_SECRET
    return secret


def _jwt_expiry_minutes() -> int:
    return int(os.environ.get("JWT_EXPIRY_MINUTES", "60"))


# -- password helpers --

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# -- JWT helpers --

def create_token(user_id: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "exp": now + timedelta(minutes=_jwt_expiry_minutes()),
        "iat": now,
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decode and verify a JWT. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
