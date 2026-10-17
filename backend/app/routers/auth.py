"""Auth endpoints: register, login, with in-memory login rate limiting."""

from __future__ import annotations

import math
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
_now = time.monotonic  # seam for deterministic tests


@router.post("/api/auth/register", operation_id="register", status_code=201)
async def register(
    body: RegisterRequest,
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

    existing = db.query(orm.User).filter(orm.User.username == body.username).first()
    if existing is not None:
        return JSONResponse(
            status_code=409,
            content={"detail": f"Username '{body.username}' is already taken"},
        )

    user = orm.User(
        username=body.username,
        password_hash=hash_password(body.password),
        upper_threshold=70,
        lower_threshold=30,
    )
    db.add(user)
    db.flush()
    criteria = orm.Criteria(user_id=user.id, text="")
    db.add(criteria)
    db.commit()

    token = create_token(user.id)
    return JSONResponse(
        status_code=201,
        content={"token": token, "username": body.username},
    )


@router.post("/api/auth/login", operation_id="login")
async def login(
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

    ip = request.client.host if request.client else ""
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
