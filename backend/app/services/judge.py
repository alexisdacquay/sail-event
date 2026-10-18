"""Judge — score one event against criteria via the LLM, then apply caps.

Not wired into the pipeline yet (F2). The caller counts judge_errors.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from ..services import clock
from ..services.extract import ExtractedEvent

PROMPT_NAME = "judge"
PROMPT_VERSION = "v2"

# ---------- caps table (spec §7) ----------

_CAPS: list[tuple[str, str, int]] = [
    # (flag_name, flag_value_that_triggers_cap, max_score)
    ("place", "no", 0),
    ("date", "no", 10),
    ("budget", "no", 30),
    ("topic", "no", 39),
]


def apply_caps(score: int, fit: dict[str, str]) -> int:
    """Enforce the caps table: each flag=no limits the score."""
    for flag, trigger, cap in _CAPS:
        if fit.get(flag) == trigger:
            score = min(score, cap)
    return score


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
# Date tokens: month names (abbreviated or full), or digits that look like a date
_DATE_TOKEN_RE = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|"
    r"January|February|March|April|June|July|August|September|October|November|December|"
    r"Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember|"
    r"\d{1,2}[\./\-]\d{1,2}|\d{1,2}\s+\w+\s+\d{4}|\d{1,2}\s+\w+)\b",
    re.IGNORECASE,
)
# Place token: any capitalised word that could be a city (at least one word starting uppercase)
_PLACE_TOKEN_RE = re.compile(r"\bin\s+[A-ZÀ-ɏ][\w\-]+", re.UNICODE)


def validate_reason(reason: str) -> str | None:
    """Return an error message if the reason fails the pattern check, else None."""
    if len(reason) > 140:
        return f"reason too long ({len(reason)} chars, max 140)"
    if _URL_RE.search(reason):
        return "reason contains a URL"
    if _MARKUP_RE.search(reason):
        return "reason contains markup"
    if not _DATE_TOKEN_RE.search(reason):
        return "reason missing a date token"
    if not _PLACE_TOKEN_RE.search(reason):
        return "reason missing a place token"
    return None


# ---------- result types ----------

@dataclass
class Verdict:
    score: int
    reason: str
    fit: dict[str, str]
    is_event: bool
    capped: bool  # True when caps changed the score


@dataclass
class JudgeError:
    event: ExtractedEvent
    error: str


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
        "end_local": ev.end_local,
        "venue": ev.venue,
        "city": ev.city,
        "country": ev.country,
        "price_amount": ev.price_amount,
        "price_currency": ev.price_currency,
        "description": ev.description,
    }
    return json.dumps(obj)


def judge_event(
    event: ExtractedEvent,
    *,
    criteria_text: str,
    facets: dict,
    window_start: datetime,
    window_end: datetime,
    user_tz: str,
    model,
) -> Verdict | JudgeError:
    """Judge one event. Returns Verdict on success, JudgeError on failure.

    The caller counts JudgeError as judge_errors; the event stays `new`.
    """
    from zoneinfo import ZoneInfo

    schema = _read_schema()
    schema_text = json.dumps(schema, indent=2)

    tz = ZoneInfo(user_tz)
    ws = window_start.astimezone(tz).strftime("%Y-%m-%d")
    we = window_end.astimezone(tz).strftime("%Y-%m-%d")
    today = clock.now().astimezone(tz).strftime("%Y-%m-%d")
    input_language = facets.get("input_language", "en")

    variables = {
        "criteria_text": criteria_text,
        "facets_json": json.dumps(facets),
        "window_start": ws,
        "window_end": we,
        "event_json": _event_to_json(event),
        "today": today,
        "input_language": input_language,
        "schema": schema_text,
    }

    try:
        response, usage = model.complete_json(
            prompt_name=PROMPT_NAME,
            prompt_version=PROMPT_VERSION,
            variables=variables,
        )
    except Exception as exc:
        return JudgeError(event=event, error=f"model error: {exc}")

    raw_score = response.get("score", 0)
    reason = response.get("reason", "")
    fit = response.get("fit", {})
    is_event = response.get("is_event", True)

    # is_event=false → score 0, event dropped
    if not is_event:
        return Verdict(
            score=0, reason=reason, fit=fit, is_event=False, capped=raw_score != 0,
        )

    # Reason validation → error result, not an exception
    reason_err = validate_reason(reason)
    if reason_err is not None:
        return JudgeError(event=event, error=f"reason check: {reason_err}")

    # Apply caps
    capped_score = apply_caps(raw_score, fit)

    return Verdict(
        score=capped_score,
        reason=reason,
        fit=fit,
        is_event=True,
        capped=capped_score != raw_score,
    )
