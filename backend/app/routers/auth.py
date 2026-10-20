"""Auth endpoints: register, login, with in-memory rate limiting."""

from __future__ import annotations

import hmac
import math
import os
import time

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..auth import create_token, hash_password, verify_password
from ..db import get_db
from ..models import RegisterRequest, LoginRequest
from .. import orm

router = APIRouter()

# In-memory login rate limiter: (username, ip) → [failure timestamps]
_login_failures: dict[tuple[str, str], list[float]] = {}
_RATE_WINDOW = 900  # 15 minutes
_RATE_MAX = 10

# In-memory register rate limiter: ip → [success timestamps]
_register_successes: dict[str, list[float]] = {}
_REGISTER_WINDOW = 3600  # 1 hour

_now = time.monotonic  # seam for deterministic tests


def _client_ip(request: Request) -> str:
    """Real client IP: rightmost X-Forwarded-For hop when a proxy is trusted, else peer address.

    All IP-dependent code must call this, never request.client.host directly
    (uvicorn's ProxyHeadersMiddleware sets that to the leftmost hop when
    trusted_hosts='*', which the client can spoof).
    """
    if os.environ.get("FORWARDED_ALLOW_IPS", ""):
        xff = request.headers.get("x-forwarded-for", "")
        if xff:
            return xff.rsplit(",", 1)[-1].strip()
    return request.client.host if request.client else ""


@router.post("/api/auth/register", operation_id="register", status_code=201)
def register(
    body: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> JSONResponse:
    # 1. Rate-limit check (cheapest rejection)
    ip = _client_ip(request)
    now = _now()
    max_reg = int(os.environ.get("REGISTER_RATE_LIMIT_PER_HOUR", "5"))
    successes = [t for t in _register_successes.get(ip, []) if t > now - _REGISTER_WINDOW]
    _register_successes[ip] = successes
    if len(successes) >= max_reg:
        retry_after = max(math.ceil(successes[0] + _REGISTER_WINDOW - now), 1)
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many registrations. Try again later."},
            headers={"Retry-After": str(retry_after)},
        )

    # 2. Registration-code check
    reg_code = os.environ.get("REGISTRATION_CODE", "")
    if reg_code:
        submitted = body.registrationCode or ""
        if not hmac.compare_digest(reg_code, submitted):
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid registration code"},
            )

    # 3. Input validation
    if not body.username or not body.username.strip():
        return JSONResponse(
            status_code=400,
            content={"detail": "username must not be empty"},
        )
    if not body.password or not body.password.strip():
        return JSONResponse(
            status_code=400,
            content={"detail": "password must not be empty"},
        )

    # 4. DB queries
    existing = db.query(orm.User).filter(orm.User.username == body.username).first()
    if existing is not None:
        return JSONResponse(
            status_code=409,
            content={"detail": f"Username '{body.username}' is already taken"},
        )

    user = orm.User(
        username=body.username,
        password_hash=hash_password(body.password),
        upper_threshold=90,
        lower_threshold=40,
    )
    db.add(user)
    db.flush()
    criteria = orm.Criteria(user_id=user.id, text="")
    db.add(criteria)
    db.commit()

    # 5. Success — record for rate limiting
    successes.append(now)
    token = create_token(user.id)
    return JSONResponse(
        status_code=201,
        content={"token": token, "username": body.username},
    )


@router.post("/api/auth/login", operation_id="login")
def login(
    body: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> JSONResponse:
    if not body.username or not body.username.strip():
        return JSONResponse(
            status_code=400,
            content={"detail": "username must not be empty"},
        )
    if not body.password or not body.password.strip():
        return JSONResponse(
            status_code=400,
            content={"detail": "password must not be empty"},
        )

    ip = _client_ip(request)
    key = (body.username, ip)
    now = _now()

    # Prune expired entries and check rate limit
    failures = [t for t in _login_failures.get(key, []) if t > now - _RATE_WINDOW]
    _login_failures[key] = failures
    if len(failures) >= _RATE_MAX:
        retry_after = max(math.ceil(failures[0] + _RATE_WINDOW - now), 1)
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many failed login attempts. Try again later."},
            headers={"Retry-After": str(retry_after)},
        )

    user = db.query(orm.User).filter(orm.User.username == body.username).first()
    if user is None:
        failures.append(now)
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid username or password"},
        )

    if not verify_password(body.password, user.password_hash):
        failures.append(now)
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid username or password"},
        )

    _login_failures.pop(key, None)
    token = create_token(user.id)
    return JSONResponse(
        content={"token": token, "username": user.username},
    )
