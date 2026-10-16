"""FastAPI app — wire routers, CORS, and 422→400 validation handler."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers import auth, calendar, criteria, events, health, search, thresholds

app = FastAPI()

# CORS — origins from env, default to Vite dev server
_origins_raw = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
_origins = [o.strip() for o in _origins_raw.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(health.router)
app.include_router(criteria.router)
app.include_router(thresholds.router)
app.include_router(search.router)
app.include_router(events.router)
app.include_router(calendar.router)
