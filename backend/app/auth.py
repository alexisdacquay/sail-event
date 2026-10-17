"""Password hashing (bcrypt) and JWT encode/decode helpers."""

from __future__ import annotations

import logging
import os
import secrets
import sys
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

logger = logging.getLogger(__name__)


def _compute_jwt_secret() -> str:
    """Resolve JWT signing secret from environment.

    Called once at import time; result cached in ``_SECRET``.
    """
    secret = os.environ.get("JWT_SECRET", "").strip()
    if secret:
        return secret
    if os.environ.get("APP_ENV", "").strip().lower() == "prod":
        sys.exit("FATAL: JWT_SECRET environment variable is missing or empty (APP_ENV=prod)")
    logger.warning(
        "JWT_SECRET is unset — generated a random dev secret. "
        "Tokens will not survive restarts."
    )
    return secrets.token_hex(32)


_SECRET: str = _compute_jwt_secret()


def _jwt_secret() -> str:
    return _SECRET


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
