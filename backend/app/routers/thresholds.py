"""Thresholds endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import Thresholds
from .. import orm

router = APIRouter()


@router.get("/api/thresholds", operation_id="getThresholds")
async def get_thresholds(
    user: orm.User = Depends(get_current_user),
) -> dict:
    return {"lowerThreshold": user.lower_threshold, "upperThreshold": user.upper_threshold}


@router.put("/api/thresholds", operation_id="saveThresholds")
async def save_thresholds(
    body: Thresholds,
    user: orm.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    if body.lower_threshold >= body.upper_threshold:
        return JSONResponse(
            status_code=400,
            content={"detail": "lowerThreshold must be less than upperThreshold"},
        )
    user.lower_threshold = body.lower_threshold
    user.upper_threshold = body.upper_threshold
    db.commit()
    return JSONResponse(
        content={
            "lowerThreshold": body.lower_threshold,
            "upperThreshold": body.upper_threshold,
        },
    )
