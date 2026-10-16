"""Auth endpoints: register, login."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..auth import create_token, hash_password, verify_password
from ..db import get_db
from ..models import RegisterRequest, LoginRequest
from .. import orm

router = APIRouter()


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

    user = db.query(orm.User).filter(orm.User.username == body.username).first()
    if user is None:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid username or password"},
        )

    if not verify_password(body.password, user.password_hash):
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid username or password"},
        )

    token = create_token(user.id)
    return JSONResponse(
        content={"token": token, "username": user.username},
    )
