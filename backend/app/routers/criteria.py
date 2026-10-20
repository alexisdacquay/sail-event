"""Criteria endpoints."""

from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import SaveCriteriaRequest
from .. import orm

router = APIRouter()


@router.get("/api/criteria", operation_id="getCriteria")
def get_criteria(
    user: orm.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    c = db.query(orm.Criteria).filter(orm.Criteria.user_id == user.id).first()
    if c is None:
        return {"text": "", "updatedAt": "", "timeZone": user.time_zone}
    return {
        "text": c.text,
        "updatedAt": c.updated_at.isoformat() if c.updated_at else "",
        "timeZone": user.time_zone,
    }


@router.put("/api/criteria", operation_id="saveCriteria", response_model=None)
def save_criteria(
    body: SaveCriteriaRequest,
    user: orm.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate timeZone if provided
    if body.time_zone is not None:
        try:
            ZoneInfo(body.time_zone)
        except (ZoneInfoNotFoundError, KeyError):
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid IANA time zone: {body.time_zone}"},
            )
        user.time_zone = body.time_zone

    # Guard the text before saving (Lakera primary, self-check fallback)
    if body.text:
        from ..adapters.factory import get_guardrail
        from ..adapters.guard_lakera import ContentFlagged

        guardrail = get_guardrail()
        try:
            guardrail.check(body.text, target="criteria")
        except ContentFlagged:
            return JSONResponse(
                status_code=400,
                content={"detail": "These criteria cannot be used."},
            )
        except RuntimeError:
            # Both guards failed — fail closed
            return JSONResponse(
                status_code=503,
                content={"detail": "Try again in a moment."},
            )
        except Exception:
            # GuardUnavailable with no fallback — fail closed
            return JSONResponse(
                status_code=503,
                content={"detail": "Try again in a moment."},
            )

    c = db.query(orm.Criteria).filter(orm.Criteria.user_id == user.id).first()
    if c is None:
        c = orm.Criteria(user_id=user.id, text=body.text)
        db.add(c)
    else:
        c.text = body.text
    db.commit()
    db.refresh(c)
    db.refresh(user)
    return {
        "text": c.text,
        "updatedAt": c.updated_at.isoformat() if c.updated_at else "",
        "timeZone": user.time_zone,
    }
