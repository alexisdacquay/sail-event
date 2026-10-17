"""Claude scorer adapter — real LLM scoring via the Anthropic API."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import anthropic

from .base import RawEvent

_PROMPT_PATH = Path(__file__).parent / "prompts" / "scorer_v1.md"
_PROMPT_TEMPLATE = _PROMPT_PATH.read_text()

_DEFAULT_MODEL = "claude-haiku-5-5"

_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer"},
        "reason": {"type": "string"},
    },
    "required": ["score", "reason"],
    "additionalProperties": False,
}


class ClaudeScorer:
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required "
                "when SCORER=claude"
            )
        self._model = os.environ.get("SCORER_MODEL", _DEFAULT_MODEL)
        self._client = anthropic.Anthropic(
            api_key=key, timeout=30, max_retries=1,
        )

    @property
    def model_id(self) -> str:
        return f"claude:{self._model}:scorer_v1"

    def score(self, event: RawEvent, criteria: str) -> tuple[int, str]:
        prompt = _PROMPT_TEMPLATE.format(
            title=event.title,
            date_time=event.date_time,
            place=event.place,
            description=event.description,
            criteria=criteria,
        )

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            output_config={
                "effort": "low",
                "format": {
                    "type": "json_schema",
                    "strict": True,
                    "schema": _SCHEMA,
                },
            },
        )

        text_block = next(
            (b for b in response.content if b.type == "text"), None,
        )
        if text_block is None:
            raise RuntimeError("Claude response contained no text block")

        try:
            data = json.loads(text_block.text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Claude returned invalid JSON: {exc}"
            ) from exc

        if not isinstance(data.get("score"), int):
            raise RuntimeError(
                f"Expected integer 'score', got {type(data.get('score')).__name__}"
            )
        if not isinstance(data.get("reason"), str):
            raise RuntimeError(
                f"Expected string 'reason', got {type(data.get('reason')).__name__}"
            )

        score_val: int = data["score"]
        reason: str = data["reason"][:120]

        if not 0 <= score_val <= 100:
            raise ValueError(
                f"Score {score_val} outside 0–100 range"
            )

        return (score_val, reason)


if __name__ == "__main__":
    criteria_arg = sys.argv[1] if len(sys.argv) > 1 else "sailing events"
    test_event = RawEvent(
        title="Round the Island Race 2026",
        date_time="2026-06-20",
        place="Isle of Wight, UK",
        link="https://example.com/round-island-2026",
        description="The Round the Island Race is one of the largest yacht races in the world.",
    )
    scorer = ClaudeScorer()
    score_val, reason = scorer.score(test_event, criteria_arg)
    print(f"Score: {score_val}")
    print(f"Reason: {reason}")
