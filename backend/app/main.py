"""FastAPI app — wire routers and 422→400 validation handler."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .routers import calendar, criteria, events, health, search, thresholds

app = FastAPI()

# 422 → 400 for all request validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


app.include_router(health.router)
app.include_router(criteria.router)
app.include_router(thresholds.router)
app.include_router(search.router)
app.include_router(events.router)
app.include_router(calendar.router)
