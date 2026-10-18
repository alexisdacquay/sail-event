"""Tests for the prompt loader and prompt file conventions."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.adapters.prompts.loader import load_prompt

_PROMPTS_DIR = Path(__file__).parent.parent / "app" / "adapters" / "prompts"


class TestLoader:
    def test_renders_variables(self):
        rendered, schema = load_prompt("guard", "v1", {"text": "hello"})
        assert "hello" in rendered
        assert "<<<" in rendered
        assert schema["type"] == "object"

    def test_missing_variable_raises(self):
        with pytest.raises(KeyError):
            load_prompt("guard", "v1", {})

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_prompt("nonexistent", "v99", {"text": "x"})


class TestPromptConventions:
    """Every prompts/*_v2.md and guard_v1.md ends with its schema and 'json'."""

    def _prompt_files(self):
        files = list(_PROMPTS_DIR.glob("*_v2.md"))
        guard = _PROMPTS_DIR / "guard_v1.md"
        if guard.exists():
            files.append(guard)
        return files

    def test_all_prompts_end_with_json(self):
        files = self._prompt_files()
        assert len(files) >= 1, "Expected at least guard_v1.md"
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
            stem = path.stem  # e.g. guard_v1
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
