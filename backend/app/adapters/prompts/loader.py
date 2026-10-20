"""Prompt loader — reads prompt .md and .schema.json, renders variables, validates responses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_PROMPTS_DIR = Path(__file__).parent

# Subset validator for JSON Schema features used by the prompts:
# type (object/string/boolean/integer/number/array), required, enum,
# additionalProperties.  No $ref, no nested objects, no allOf/anyOf.
# Using stdlib only; pydantic available via FastAPI but not needed for this subset.

_JSON_TYPE_MAP = {
    "string": str,
    "boolean": bool,
    "integer": int,
    "number": (int, float),
    "array": list,
    "object": dict,
}


def validate_response(prompt_name: str, response: dict, schema: dict) -> None:
    """Validate *response* against a JSON Schema subset.

    Raises RuntimeError("<prompt_name>: schema violation: ...") on any mismatch.
    """
    if schema.get("type") == "object":
        if not isinstance(response, dict):
            raise RuntimeError(f"{prompt_name}: schema violation: expected object, got {type(response).__name__}")

        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for field in required:
            if field not in response:
                raise RuntimeError(f"{prompt_name}: schema violation: missing required field '{field}'")

        if schema.get("additionalProperties") is False:
            extra = set(response) - set(properties)
            if extra:
                raise RuntimeError(
                    f"{prompt_name}: schema violation: unexpected fields {sorted(extra)}"
                )

        for field, field_schema in properties.items():
            if field not in response:
                continue
            _validate_field(prompt_name, field, response[field], field_schema)


def _validate_field(prompt_name: str, field: str, value: Any, field_schema: dict) -> None:
    """Validate a single field value against its schema."""
    ftype = field_schema.get("type")
    if ftype and value is not None:
        expected = _JSON_TYPE_MAP.get(ftype)
        if expected and not isinstance(value, expected):
            # JSON has no integer; allow int where number is expected (already covered by tuple)
            raise RuntimeError(
                f"{prompt_name}: schema violation: field '{field}' expected {ftype}, "
                f"got {type(value).__name__}"
            )

    if "enum" in field_schema and value not in field_schema["enum"]:
        raise RuntimeError(
            f"{prompt_name}: schema violation: field '{field}' value {value!r} "
            f"not in {field_schema['enum']}"
        )

    if "minimum" in field_schema and isinstance(value, (int, float)) and value < field_schema["minimum"]:
        raise RuntimeError(
            f"{prompt_name}: schema violation: field '{field}' value {value} "
            f"< minimum {field_schema['minimum']}"
        )
    if "maximum" in field_schema and isinstance(value, (int, float)) and value > field_schema["maximum"]:
        raise RuntimeError(
            f"{prompt_name}: schema violation: field '{field}' value {value} "
            f"> maximum {field_schema['maximum']}"
        )


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
