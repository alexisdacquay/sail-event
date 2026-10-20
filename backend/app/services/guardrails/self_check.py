"""Self-check fallback guardrail — single prompt-injection question on the LLM.

Runs only when Lakera is unavailable (GuardUnavailable) and GUARD_FALLBACK=self_check.
"""

from __future__ import annotations

import logging

from ...adapters.guard_lakera import ContentFlagged, GuardUnavailable

logger = logging.getLogger(__name__)

PROMPT_NAME = "guard"
PROMPT_VERSION = "v2"


class SelfCheckGuardrail:
    """Fallback: one LLM call with the guard_v2 prompt-injection check."""

    def __init__(self, model) -> None:
        self._model = model

    def check(self, text: str) -> None:
        """Raise ContentFlagged if the model says blocked, RuntimeError on model error."""
        try:
            response, _usage = self._model.complete_json(
                prompt_name=PROMPT_NAME,
                prompt_version=PROMPT_VERSION,
                variables={"text": text},
            )
        except Exception as exc:
            raise RuntimeError(f"self_check model error: {exc}") from exc

        if response.get("blocked"):
            raise ContentFlagged(f"self_check: {response.get('reason', 'blocked')}")
