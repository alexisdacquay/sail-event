"""Criteria endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from ..deps import get_current_user
from ..models import Criteria, SaveCriteriaRequest
from ..store import UserRecord

router = APIRouter()


@router.get("/api/criteria", operation_id="getCriteria")
async def get_criteria(
    user: UserRecord = Depends(get_current_user),
) -> dict:
    c = user.criteria
    return {"text": c.text, "updatedAt": c.updated_at}


@router.put("/api/criteria", operation_id="saveCriteria")
async def save_criteria(
    body: SaveCriteriaRequest,
    user: UserRecord = Depends(get_current_user),
) -> dict:
    user.criteria = Criteria(
        text=body.text,
        updated_at=datetime.now(UTC).isoformat(),
    )
    c = user.criteria
    return {"text": c.text, "updatedAt": c.updated_at}
