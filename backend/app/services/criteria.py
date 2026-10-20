"""Criteria understanding — parse free text into structured Facets via the LLM."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone

from ..services import clock

logger = logging.getLogger(__name__)

PROMPT_NAME = "criteria"
PROMPT_VERSION = "v2"


def _text_sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def needs_parse(
    text: str,
    facets_text_sha: str | None,
    facets_version: str | None,
    *,
    facets_json: str | None = None,
    user_tz: str = "UTC",
) -> bool:
    """Return True when the criteria text must be (re-)parsed.

    Re-parses when the text changed, the prompt version changed, or the
    stored *relative* window has expired (so date phrases like "next week"
    follow the calendar).  Absolute-only dates never trigger a re-parse
    because the LLM would return the same dates.
    """
    current_sha = _text_sha(text)
    expected_version = f"{PROMPT_NAME}_{PROMPT_VERSION}"
    if facets_text_sha != current_sha or facets_version != expected_version:
        return True
    if facets_json:
        return _relative_window_expired(facets_json, user_tz)
    return False


def _relative_window_expired(facets_json: str, user_tz: str) -> bool:
    """True when the facets carry a relative date expression whose resolved
    window end is now in the past.  Absolute-only dates never expire (the
    LLM would return the same result)."""
    try:
        facets = json.loads(facets_json)
    except (json.JSONDecodeError, TypeError):
        return False
    date_facets = facets.get("date") or {}
    # Only re-parse when there is a relative expression
    if not date_facets.get("relative"):
        return False
    end_str = date_facets.get("end")
    if not end_str:
        return False
    try:
        from datetime import date
        from zoneinfo import ZoneInfo
        end_date = date.fromisoformat(end_str)
    except ValueError:
        return False
    today_user = clock.now().astimezone(ZoneInfo(user_tz)).date()
    return end_date < today_user


def parse_criteria(text: str, user_tz: str, model) -> dict:
    """Parse criteria text into Facets using the language model.

    Returns the Facets dict.  The caller stores it alongside the metadata
    returned by ``parse_metadata``.
    """
    today = clock.now().astimezone(timezone.utc).strftime("%Y-%m-%d")

    schema_text = json.dumps(_read_schema(), indent=2)
    variables = {"text": text, "today": today, "user_tz": user_tz, "schema": schema_text}

    response, _usage = model.complete_json(
        prompt_name=PROMPT_NAME,
        prompt_version=PROMPT_VERSION,
        variables=variables,
    )
    return response


def parse_metadata(text: str) -> dict:
    """Return the metadata fields to store alongside parsed facets."""
    return {
        "facets_text_sha": _text_sha(text),
        "facets_version": f"{PROMPT_NAME}_{PROMPT_VERSION}",
        "parsed_at": clock.now(),
    }


def _read_schema() -> dict:
    from ..adapters.prompts.loader import _PROMPTS_DIR
    import json as _json
    path = _PROMPTS_DIR / f"{PROMPT_NAME}_{PROMPT_VERSION}.schema.json"
    return _json.loads(path.read_text())
