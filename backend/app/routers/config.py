"""Public config endpoint — exposes non-secret feature flags."""

from __future__ import annotations

import os

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/config", operation_id="getConfig")
def get_config():
    return {
        "registrationCodeRequired": bool(os.environ.get("REGISTRATION_CODE", "")),
    }
