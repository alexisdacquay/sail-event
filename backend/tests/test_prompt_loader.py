"""Tests for the prompt loader and prompt file conventions."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.adapters.prompts.loader import load_prompt, validate_response

_PROMPTS_DIR = Path(__file__).parent.parent / "app" / "adapters" / "prompts"


class TestLoader:
    def test_renders_variables(self):
        rendered, schema = load_prompt("guard", "v2", {"text": "hello"})
        assert "hello" in rendered
        assert "<<<" in rendered
        assert schema["type"] == "object"

    def test_missing_variable_raises(self):
        with pytest.raises(KeyError):
            load_prompt("guard", "v2", {})

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_prompt("nonexistent", "v99", {"text": "x"})


class TestPromptConventions:
    """Every prompts/*_v2.md ends with its schema and 'json'."""

    def _prompt_files(self):
        return list(_PROMPTS_DIR.glob("*_v2.md"))

    def test_all_prompts_end_with_json(self):
        files = self._prompt_files()
        assert len(files) >= 1, "Expected at least one *_v2.md prompt"
        for path in files:
            content = path.read_text()
            # Last non-empty line must contain "json"
            lines = [l for l in content.rstrip().split("\n") if l.strip()]
            last_line = lines[-1].lower()
            assert "json" in last_line, (
                f"{path.name} must end with a line containing 'json', "
                f"got: {lines[-1]!r}"
            )

    def test_all_prompts_have_schema_file(self):
        files = self._prompt_files()
        for path in files:
            stem = path.stem  # e.g. guard_v2
            schema_path = path.with_suffix(".schema.json")
            assert schema_path.exists(), f"Missing schema: {schema_path.name}"
            schema = json.loads(schema_path.read_text())
            assert "type" in schema, f"Schema missing 'type': {schema_path.name}"

    def test_all_prompts_contain_schema_block(self):
        """The .md file itself contains a JSON schema block."""
        files = self._prompt_files()
        for path in files:
            content = path.read_text()
            assert "```json" in content or '"type"' in content, (
                f"{path.name} must contain its schema inline"
            )


_GUARD_SCHEMA = {
    "type": "object",
    "properties": {
        "blocked": {"type": "boolean"},
        "reason": {"type": "string", "enum": ["injection", "ok"]},
    },
    "required": ["blocked", "reason"],
    "additionalProperties": False,
}


class TestValidateResponse:
    """validate_response raises RuntimeError('<prompt_name>: schema violation: ...')."""

    def test_valid_passes(self):
        validate_response("guard", {"blocked": False, "reason": "ok"}, _GUARD_SCHEMA)

    def test_missing_required_field(self):
        with pytest.raises(RuntimeError, match=r"guard: schema violation: missing required field 'reason'"):
            validate_response("guard", {"blocked": True}, _GUARD_SCHEMA)

    def test_wrong_type(self):
        with pytest.raises(RuntimeError, match=r"guard: schema violation: field 'blocked' expected boolean"):
            validate_response("guard", {"blocked": "yes", "reason": "ok"}, _GUARD_SCHEMA)

    def test_enum_violation(self):
        with pytest.raises(RuntimeError, match=r"guard: schema violation: field 'reason'.*not in"):
            validate_response("guard", {"blocked": False, "reason": "bad_value"}, _GUARD_SCHEMA)

    def test_additional_properties_stripped(self):
        """#125: extra fields are dropped (debug log), not rejected."""
        response = {"blocked": False, "reason": "ok", "extra": 1}
        validate_response("guard", response, _GUARD_SCHEMA)
        assert "extra" not in response  # stripped in place

    def test_not_an_object(self):
        with pytest.raises(RuntimeError, match=r"guard: schema violation: expected object"):
            validate_response("guard", [1, 2, 3], _GUARD_SCHEMA)  # type: ignore[arg-type]

    def test_permissive_schema_passes_anything(self):
        """A schema with no required/properties validates any dict."""
        validate_response("test", {"anything": "goes"}, {"type": "object"})
