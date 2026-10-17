"""Health check endpoint."""

from __future__ import annotations

import os

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health", operation_id="healthCheck")
async def health_check() -> dict:
    # Render sets RENDER_GIT_COMMIT; the promote workflow polls it to confirm which commit is live.
    return {"status": "ok", "commit": os.environ.get("RENDER_GIT_COMMIT", "")}
