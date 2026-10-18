"""FastAPI app — wire routers, CORS, seed, SPA static files, and 422→400 validation handler."""

from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .auth import hash_password
from .db import get_db
from . import orm
from .routers import auth, calendar, config, criteria, events, health, search, thresholds
from . import telemetry

_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


class _JsonFormatter(logging.Formatter):
    """Single-line JSON log records with OTel trace context."""

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "otelTraceID", ""),
            "span_id": getattr(record, "otelSpanID", ""),
        })


def _configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())


def _seed_demo() -> None:
    """Create demo user + criteria row if absent. Idempotent."""
    db = next(get_db())
    try:
        existing = db.query(orm.User).filter(orm.User.username == "demo").first()
        if existing is None:
            user = orm.User(
                username="demo",
                password_hash=hash_password("demo"),
                upper_threshold=90,
                lower_threshold=40,
            )
            db.add(user)
            db.flush()
            c = orm.Criteria(
                user_id=user.id,
                text="jazz in Berlin (Germany) next week (19-21st October 2026)",
            )
            db.add(c)
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_logging()
    telemetry.init(app=app)
    if os.environ.get("SEED_DEMO") == "1":
        _seed_demo()
    yield


app = FastAPI(lifespan=lifespan)

# CORS — origins from env, default to Vite dev server
_origins_raw = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
_origins = [o.strip() for o in _origins_raw.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)

# 422 → 400 for all request validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    # Build a short detail string from field locations + messages only.
    # Never include the raw input — it may contain passwords or secrets.
    parts = []
    for err in exc.errors():
        loc = ".".join(str(s) for s in err["loc"] if s != "body")
        parts.append(f"{loc}: {err['msg']}" if loc else err["msg"])
    detail = "; ".join(parts)
    return JSONResponse(status_code=400, content={"detail": detail})


app.include_router(auth.router)
app.include_router(config.router)
app.include_router(health.router)
app.include_router(criteria.router)
app.include_router(thresholds.router)
app.include_router(search.router)
app.include_router(events.router)
app.include_router(calendar.router)

# --- SPA static files (served only when frontend/dist exists) ---
if _STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=_STATIC_DIR / "assets"), name="static-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def _spa_fallback(request: Request, full_path: str):
        """Return index.html for SPA routes; 404 JSON for unmatched /api paths."""
        if full_path.startswith("api/") or full_path == "api":
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        return FileResponse(_STATIC_DIR / "index.html")
