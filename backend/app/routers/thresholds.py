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
def get_thresholds(
    user: orm.User = Depends(get_current_user),
) -> dict:
    return {"lowerThreshold": user.lower_threshold, "upperThreshold": user.upper_threshold}


def _reapply_thresholds(db: Session, user: orm.User) -> int:
    """Move auto-decided events to match new thresholds. Returns count moved."""
    events = (
        db.query(orm.Event)
        .filter(
            orm.Event.user_id == user.id,
            orm.Event.score.isnot(None),
            # Only touch auto-decided or undecided events, never user decisions
            orm.Event.decided_by.in_(("auto", None)),
            orm.Event.status.in_(("accepted", "rejected", "queued")),
        )
        .all()
    )
    moved = 0
    lo, hi = user.lower_threshold, user.upper_threshold
    for evt in events:
        if evt.score >= hi:
            new_status, new_by = "accepted", "auto"
        elif evt.score <= lo:
            new_status, new_by = "rejected", "auto"
        else:
            new_status, new_by = "queued", None
        if evt.status != new_status:
            evt.status = new_status
            evt.decided_by = new_by
            moved += 1
    return moved


@router.put("/api/thresholds", operation_id="saveThresholds")
def save_thresholds(
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
    moved = _reapply_thresholds(db, user)
    db.commit()
    return JSONResponse(
        content={
            "lowerThreshold": body.lower_threshold,
            "upperThreshold": body.upper_threshold,
            "eventsMoved": moved,
        },
    )
