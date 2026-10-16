"""Thresholds endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from ..deps import get_current_user
from ..models import Thresholds
from ..store import UserRecord

router = APIRouter()


@router.get("/api/thresholds", operation_id="getThresholds")
async def get_thresholds(
    user: UserRecord = Depends(get_current_user),
) -> dict:
    t = user.thresholds
    return {"lowerThreshold": t.lower_threshold, "upperThreshold": t.upper_threshold}


@router.put("/api/thresholds", operation_id="saveThresholds")
async def save_thresholds(
    body: Thresholds,
    user: UserRecord = Depends(get_current_user),
) -> JSONResponse:
    if body.lower_threshold >= body.upper_threshold:
        return JSONResponse(
            status_code=400,
            content={"detail": "lowerThreshold must be less than upperThreshold"},
        )
    user.thresholds = body
    return JSONResponse(
        content={
            "lowerThreshold": body.lower_threshold,
            "upperThreshold": body.upper_threshold,
        },
    )
