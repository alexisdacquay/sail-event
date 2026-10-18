"""Prompt loader — reads prompt .md and .schema.json, renders variables."""

from __future__ import annotations

import json
from pathlib import Path


_PROMPTS_DIR = Path(__file__).parent


def load_prompt(
    name: str,
    version: str,
    variables: dict[str, str],
) -> tuple[str, dict]:
    """Return (rendered_text, json_schema) for the given prompt.

    Raises FileNotFoundError if the prompt file is missing.
    Raises KeyError if a variable is missing from *variables*.
    """
    md_path = _PROMPTS_DIR / f"{name}_{version}.md"
    schema_path = _PROMPTS_DIR / f"{name}_{version}.schema.json"

    template = md_path.read_text()
    schema = json.loads(schema_path.read_text())

    # str.format — a missing variable raises KeyError with the var name
    rendered = template.format(**variables)

    return rendered, schema
