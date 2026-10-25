"""Daily budget enforcement — §8 of search-design.md.

daily_used() sums today's runs; check_* returns a stop reason or None.
"""

from __future__ import annotations

import os
import threading
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import orm

# Defaults sized for 10 users (§8)
_DEFAULT_SEARCH_DAILY = 600
_DEFAULT_LLM_DAILY = 5000


def daily_used(db: Session, column: str) -> int:
    """SUM(runs.<column>) where started_at >= today 00:00 UTC."""
    col = getattr(orm.Run, column)
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    result = (
        db.query(func.coalesce(func.sum(col), 0))
        .filter(orm.Run.started_at >= today_start)
        .scalar()
    )
    return int(result)


def check_search_budget(db: Session, planned_count: int) -> str | None:
    """Return 'budget: search' if adding *planned_count* would breach the cap."""
    cap = int(os.environ.get("SEARCH_DAILY_CALLS", str(_DEFAULT_SEARCH_DAILY)))
    used = daily_used(db, "search_calls")
    if used + planned_count > cap:
        return "budget: search"
    return None


def check_llm_budget(db: Session) -> str | None:
    """Return 'budget: llm' if one more LLM call would breach the cap."""
    cap = int(os.environ.get("LLM_DAILY_CALLS", str(_DEFAULT_LLM_DAILY)))
    used = daily_used(db, "llm_calls")
    if used + 1 > cap:
        return "budget: llm"
    return None


# shortcut: process lock, upgrade to a DB row lock if uvicorn ever runs --workers > 1
_reserve_lock = threading.Lock()


def reserve_llm_calls(db: Session, run: orm.Run, spent: int, n_events: int) -> int:
    """#142: reserve the judge's worst case (3 calls per event: first, schema repair, reason retry) on the run row.

    Writes ``spent`` + the reservation to ``run.llm_calls`` and commits, so
    concurrent runs see it.  Returns how many events fit; _finalise_run
    later overwrites the reservation with the actual count.
    """
    cap = int(os.environ.get("LLM_DAILY_CALLS", str(_DEFAULT_LLM_DAILY)))
    with _reserve_lock:
        run.llm_calls = spent
        db.flush()
        remaining = cap - daily_used(db, "llm_calls")
        fit = max(0, min(n_events, remaining // 3))
        run.llm_calls = spent + 3 * fit
        db.commit()
    return fit
