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
) -> bool:
    """Return True when the criteria text must be (re-)parsed.

    Re-parses when the text changed, the prompt version changed, or the
    stored absolute window end is in the past (so date phrases follow the
    calendar without a stale cache).
    """
    current_sha = _text_sha(text)
    expected_version = f"{PROMPT_NAME}_{PROMPT_VERSION}"
    if facets_text_sha != current_sha or facets_version != expected_version:
        return True
    if facets_json:
        return _window_expired(facets_json)
    return False


def _window_expired(facets_json: str) -> bool:
    """True when the stored absolute date.end is before today."""
    try:
        facets = json.loads(facets_json)
    except (json.JSONDecodeError, TypeError):
        return False
    date_facets = facets.get("date") or {}
    end_str = date_facets.get("end")
    if not end_str:
        return False
    try:
        from datetime import date
        end_date = date.fromisoformat(end_str)
    except ValueError:
        return False
    return end_date < clock.now().date()


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
