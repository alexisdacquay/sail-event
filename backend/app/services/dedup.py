"""After-storage duplicate check (#136): at the end of a run, one model call per
new accepted or queued event, against the user's other stored events on its
calendar date.  A same event keeps the stored one; the new one is rejected."""

from __future__ import annotations

import contextvars
import json
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session

from .. import orm
from ..adapters.prompts.loader import _PROMPTS_DIR, call_with_repair
from .budget import reserve_llm_calls
from .judge import _Metered

logger = logging.getLogger("sail-event.dedup")

PROMPT_NAME = "dedup"
PROMPT_VERSION = "v1"
DUPLICATE_PREFIX = "Duplicate of "


def _order(e: orm.Event) -> tuple:
    # (link, date_time) is no longer unique: the prompt's fields order the rest; rows equal in them render the same prompt
    return (e.date_time or "", e.title or "", e.link or "", e.place or "", e.description or "", e.id or "")


def _fields(e: orm.Event) -> dict:
    return {"title": e.title, "start": e.date_time, "place": e.place, "description": e.description}


def _inputs(e: orm.Event, others: list[orm.Event]) -> tuple[str, str, int]:
    """Prompt inputs as plain strings; candidate ids are 1-based positions, so recordings stay stable."""
    return json.dumps(_fields(e)), json.dumps([{"id": i, **_fields(c)} for i, c in enumerate(others, 1)]), len(others)


def same_as(event_json: str, candidates_json: str, n_candidates: int, *, model) -> int | None:
    """1-based id of the candidate that is the same event, or None.  Raises on a model or schema error."""
    schema = (_PROMPTS_DIR / f"{PROMPT_NAME}_{PROMPT_VERSION}.schema.json").read_text()
    response, _usage, _repaired = call_with_repair(
        model,
        prompt_name=PROMPT_NAME,
        prompt_version=PROMPT_VERSION,
        variables={"event_json": event_json, "candidates_json": candidates_json, "schema": schema},
        repair_hint="same_as, reason",
    )
    found = response.get("same_as")
    if found is not None and not 1 <= found <= n_candidates:
        raise ValueError(f"dedup: same_as {found!r} is not a candidate id")
    return found


def dedup_run(db: Session, run: orm.Run, user_id: str, model, spent: int, workers: int) -> dict[str, int]:
    """Check this run's new accepted/queued events; returns calls, tokens and the dedup counts."""
    stored = db.query(orm.Event).filter(orm.Event.user_id == user_id).all()
    by_day: dict[str, list[orm.Event]] = defaultdict(list)
    for e in sorted(stored, key=_order):
        # an earlier merge already points at the event it duplicates; this run's own rejects never outrank a kept event
        if not (e.score_reason or "").startswith(DUPLICATE_PREFIX) \
                and (e.run_id != run.id or e.status in ("accepted", "queued")):
            by_day[(e.date_time or "")[:10]].append(e)
    work = []
    # lower scores are applied first, so two new events naming each other keep the better-scored one
    for e in sorted(stored, key=lambda e: (e.score or 0, *_order(e))):
        if e.run_id == run.id and e.status in ("accepted", "queued"):
            others = [c for c in by_day[(e.date_time or "")[:10]] if c.id != e.id]
            if others:
                work.append((e, others))

    # Same reservation as the judge; what does not fit keeps both events
    fit = reserve_llm_calls(db, run, spent, len(work))
    short = len(work) - fit
    work = work[:fit]
    # Workers get plain strings, never the session or ORM rows
    inputs = [_inputs(e, others) for e, others in work]

    def _one(args):
        metered = _Metered(model)
        try:
            return same_as(*args, model=metered), metered
        except Exception as exc:
            logger.warning("dedup error: %s", type(exc).__name__)
            return exc, metered

    results = []
    if inputs:
        with ThreadPoolExecutor(max_workers=min(workers, len(inputs))) as pool:
            results = list(pool.map(lambda a: contextvars.copy_context().run(_one, a), inputs))

    out = {"calls": 0, "tokens_in": 0, "tokens_out": 0, "dedup_merged": 0, "dedup_errors": 0, "short": short}
    merged: set[str] = set()
    for (e, others), (found, metered) in zip(work, results):
        out["calls"] += metered.calls
        out["tokens_in"] += metered.tokens_in
        out["tokens_out"] += metered.tokens_out
        if isinstance(found, Exception):
            out["dedup_errors"] += 1
            continue
        if found is None or others[found - 1].id in merged:
            continue  # A same as B, B same as A: A is merged first, so B stays
        e.status = "rejected"
        e.decided_by = "auto"
        e.score_reason = f"{DUPLICATE_PREFIX}{others[found - 1].title}"
        merged.add(e.id)
        out["dedup_merged"] += 1
    db.commit()
    return out
