"""Auth endpoints: register, login."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..auth import create_token, hash_password, verify_password
from ..models import RegisterRequest, LoginRequest, Criteria, Thresholds
from ..store import UserRecord, store

router = APIRouter()


@router.post("/api/auth/register", operation_id="register", status_code=201)
async def register(body: RegisterRequest) -> JSONResponse:
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

    if body.username in store.username_to_user_id:
        return JSONResponse(
            status_code=409,
            content={"detail": f"Username '{body.username}' is already taken"},
        )

    user_id = str(uuid4())
    record = UserRecord(
        user_id=user_id,
        username=body.username,
        password_hash=hash_password(body.password),
        criteria=Criteria(text="", updated_at=datetime.now(UTC).isoformat()),
        thresholds=Thresholds(lower_threshold=30, upper_threshold=70),
        ics_token=str(uuid4()),
    )
    store.add_user(record)

    token = create_token(user_id)
    return JSONResponse(
        status_code=201,
        content={"token": token, "username": body.username},
    )


@router.post("/api/auth/login", operation_id="login")
async def login(body: LoginRequest) -> JSONResponse:
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

    user_id = store.username_to_user_id.get(body.username)
    if user_id is None:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid username or password"},
        )

    user = store.users[user_id]
    if not verify_password(body.password, user.password_hash):
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid username or password"},
        )

    token = create_token(user_id)
    return JSONResponse(
        content={"token": token, "username": user.username},
    )
