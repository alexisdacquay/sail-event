"""Criteria endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import SaveCriteriaRequest
from .. import orm

router = APIRouter()


@router.get("/api/criteria", operation_id="getCriteria")
async def get_criteria(
    user: orm.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    c = db.query(orm.Criteria).filter(orm.Criteria.user_id == user.id).first()
    if c is None:
        return {"text": "", "updatedAt": ""}
    return {"text": c.text, "updatedAt": c.updated_at.isoformat() if c.updated_at else ""}


@router.put("/api/criteria", operation_id="saveCriteria")
async def save_criteria(
    body: SaveCriteriaRequest,
    user: orm.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    c = db.query(orm.Criteria).filter(orm.Criteria.user_id == user.id).first()
    if c is None:
        c = orm.Criteria(user_id=user.id, text=body.text)
        db.add(c)
    else:
        c.text = body.text
    db.commit()
    db.refresh(c)
    return {"text": c.text, "updatedAt": c.updated_at.isoformat() if c.updated_at else ""}
