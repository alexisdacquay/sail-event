"""Fake LLM — replays recorded responses keyed by prompt name, version and rendered-prompt hash."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .prompts.loader import load_prompt

_FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "llm"


class Usage:
    __slots__ = ("tokens_in", "tokens_out")

    def __init__(self, tokens_in: int = 0, tokens_out: int = 0) -> None:
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out


class FakeLanguageModel:
    """Replays recordings from tests/fixtures/llm/<name>_<version>/<hash[:16]>.json."""

    model_id: str = "fake:recorded"

    def complete_json(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        variables: dict[str, str],
        schema: dict | None = None,
    ) -> tuple[dict, Usage]:
        rendered, _schema = load_prompt(prompt_name, prompt_version, variables)
        prompt_hash = hashlib.sha256(rendered.encode()).hexdigest()[:16]

        recording_path = _FIXTURES_DIR / f"{prompt_name}_{prompt_version}" / f"{prompt_hash}.json"
        if not recording_path.exists():
            raise FileNotFoundError(
                f"{prompt_name}: no recording at {recording_path.name} "
                f"(hash={prompt_hash})"
            )

        data = json.loads(recording_path.read_text())
        response = data["response"]
        usage_raw = data.get("usage", {})
        usage = Usage(
            tokens_in=usage_raw.get("prompt_tokens", 0),
            tokens_out=usage_raw.get("completion_tokens", 0),
        )
        return response, usage
