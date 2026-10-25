"""Judge — score one event against criteria via the LLM (v3: suitability only).

The caller counts judge_errors.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..services import clock
from ..services.extract import ExtractedEvent

PROMPT_NAME = "judge"
PROMPT_VERSION = "v3"


# ---------- band words (spec §8) ----------

_BANDS: list[tuple[int, int, str]] = [
    (90, 100, "fits"),
    (70, 89, "mostly fits"),
    (40, 69, "open question"),
    (10, 39, "off topic"),
    (0, 9, "not a fit"),
]


def band_word(score: int) -> str:
    """Return the human-readable band word for a score."""
    for lo, hi, word in _BANDS:
        if lo <= score <= hi:
            return word
    return "not a fit"


# ---------- reason validation ----------

_URL_RE = re.compile(r"https?://", re.IGNORECASE)
_MARKUP_RE = re.compile(r"<[^>]+>|&[a-z]+;|\[.*?\]", re.IGNORECASE)


def validate_reason(reason: str) -> str | None:
    """Return an error message if the reason fails basic checks, else None."""
    if len(reason) > 140:
        return f"reason too long ({len(reason)} chars, max 140)"
    if _URL_RE.search(reason):
        return "reason contains a URL"
    if _MARKUP_RE.search(reason):
        return "reason contains markup"
    return None


# ---------- result types ----------

@dataclass
class Verdict:
    score: int
    reason: str
    fit: dict[str, str]
    is_event: bool
    capped: bool  # kept for API compat; always False in v3
    repaired: bool = False
    # #142: what this judgement cost, set by judge_event; the caller sums them
    calls: int = field(default=1, compare=False)
    tokens_in: int = field(default=0, compare=False)
    tokens_out: int = field(default=0, compare=False)


@dataclass
class JudgeError:
    event: ExtractedEvent
    error: str
    calls: int = field(default=1, compare=False)
    tokens_in: int = field(default=0, compare=False)
    tokens_out: int = field(default=0, compare=False)


class _Metered:
    """Counts the calls and tokens of one judge_event; one per call, so no shared state across threads."""

    def __init__(self, model) -> None:
        self._model = model
        self.calls = self.tokens_in = self.tokens_out = 0

    def __getattr__(self, name):
        return getattr(self._model, name)

    def complete_json(self, **kwargs):
        self.calls += 1
        response, usage = self._model.complete_json(**kwargs)
        self.tokens_in += getattr(usage, "tokens_in", 0) or 0
        self.tokens_out += getattr(usage, "tokens_out", 0) or 0
        return response, usage


# ---------- main entry point ----------

def _read_schema() -> dict:
    from ..adapters.prompts.loader import _PROMPTS_DIR
    path = _PROMPTS_DIR / f"{PROMPT_NAME}_{PROMPT_VERSION}.schema.json"
    return json.loads(path.read_text())


def _event_to_json(ev: ExtractedEvent) -> str:
    """Serialize the event fields the judge needs."""
    obj = {
        "title": ev.title,
        "start_local": ev.start_local,
        "start_tz": ev.start_tz,
        "city": ev.city,
        "country": ev.country,
        "description": ev.description,
        "link": ev.link,
    }
    return json.dumps(obj)


_REPAIR_FIELDS = "score, reason, is_event"


def judge_event(event: ExtractedEvent, *, model, **kwargs) -> Verdict | JudgeError:
    """Judge one event.  Returns Verdict on success, JudgeError on failure.

    On a schema or reason violation the model is re-asked once.  A repaired
    Verdict has ``repaired=True`` so the caller can count ``judge_repaired``.
    The caller counts JudgeError as ``judge_errors``; the event stays ``new``.
    Both carry the calls made and tokens used (#142).
    """
    metered = _Metered(model)
    result = _judge(event, model=metered, **kwargs)
    result.calls, result.tokens_in, result.tokens_out = metered.calls, metered.tokens_in, metered.tokens_out
    return result


def _judge(
    event: ExtractedEvent,
    *,
    criteria_text: str,
    facets: dict,
    window_start: datetime,
    window_end: datetime,
    user_tz: str,
    model,
) -> Verdict | JudgeError:
    from ..adapters.prompts.loader import call_with_repair

    schema = _read_schema()
    schema_text = json.dumps(schema, indent=2)

    today = clock.now().astimezone(timezone.utc).strftime("%Y-%m-%d")

    variables = {
        "criteria_text": criteria_text,
        "event_json": _event_to_json(event),
        "today": today,
        "user_tz": user_tz,
        "schema": schema_text,
    }

    # Schema repair via the shared helper (includes assistant turn)
    try:
        response, usage, repaired = call_with_repair(
            model,
            prompt_name=PROMPT_NAME,
            prompt_version=PROMPT_VERSION,
            variables=variables,
            repair_hint=_REPAIR_FIELDS,
        )
    except Exception as exc:
        return JudgeError(event=event, error=f"model error: {exc}")

    raw_score = response.get("score", 0)
    reason = response.get("reason", "")
    is_event = response.get("is_event", True)

    # is_event=false → score 0, event dropped
    if not is_event:
        return Verdict(
            score=0, reason=reason, fit={}, is_event=False,
            capped=False, repaired=repaired,
        )

    # Reason validation — retry once with assistant turn, then error
    reason_err = validate_reason(reason)
    if reason_err is not None:
        if not repaired:
            bad_json = json.dumps(response)
            repair_msg = (
                f"Your answer was rejected: {reason_err}. "
                f"Answer again with exactly the fields: {_REPAIR_FIELDS}."
            )
            try:
                response, usage = model.complete_json(
                    prompt_name=PROMPT_NAME,
                    prompt_version=PROMPT_VERSION,
                    variables=variables,
                    repair_messages=[
                        {"role": "assistant", "content": bad_json},
                        {"role": "user", "content": repair_msg},
                    ],
                )
            except Exception as exc:
                return JudgeError(event=event, error=f"model error: {exc}")
            reason = response.get("reason", "")
            reason_err2 = validate_reason(reason)
            if reason_err2 is not None:
                return JudgeError(event=event, error=f"reason check: {reason_err2}")
            raw_score = response.get("score", 0)
            is_event = response.get("is_event", True)
            repaired = True
        else:
            return JudgeError(event=event, error=f"reason check: {reason_err}")

    return Verdict(
        score=raw_score, reason=reason, fit={}, is_event=True,
        capped=False, repaired=repaired,
    )
