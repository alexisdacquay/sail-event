"""OpenAI-compatible LLM adapter — stdlib urllib, no new dependency."""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from .prompts.loader import load_prompt

logger = logging.getLogger(__name__)

# max_tokens per prompt name
MAX_TOKENS: dict[str, int] = {
    "criteria": 600,
    "extract": 4000,
    "judge": 300,
    "guard": 100,
}
_DEFAULT_MAX_TOKENS = 600


@dataclass(frozen=True)
class Usage:
    tokens_in: int
    tokens_out: int


class OpenAICompatibleModel:
    """Calls an OpenAI-compatible chat/completions endpoint."""

    def __init__(self) -> None:
        self.base_url = os.environ["LLM_BASE_URL"].rstrip("/")
        self.api_key = os.environ["LLM_API_KEY"]
        self.model = os.environ["LLM_MODEL"]
        self.json_mode = os.environ["LLM_JSON_MODE"]
        self.model_id = f"openai_compatible:{self.model}"

    def complete_json(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        variables: dict[str, str],
        schema: dict | None = None,
    ) -> tuple[dict, Usage]:
        rendered, loaded_schema = load_prompt(prompt_name, prompt_version, variables)
        effective_schema = schema if schema is not None else loaded_schema

        body = self._build_body(prompt_name, rendered, effective_schema)
        data = self._call_api(body, prompt_name=prompt_name)
        return data, self._parse_usage(data)

    def _build_body(self, prompt_name: str, rendered: str, schema: dict) -> dict[str, Any]:
        max_tokens = MAX_TOKENS.get(prompt_name, _DEFAULT_MAX_TOKENS)

        body: dict[str, Any] = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": rendered}],
        }

        if self.json_mode == "json_object":
            body["response_format"] = {"type": "json_object"}
        elif self.json_mode == "json_schema":
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": prompt_name,
                    "schema": schema,
                    "strict": True,
                },
            }
        else:
            raise ValueError(f"Unknown LLM_JSON_MODE: {self.json_mode!r}")

        return body

    def _call_api(self, body: dict, *, prompt_name: str) -> dict:
        """POST to chat/completions with one retry on 429/5xx and empty content."""
        url = f"{self.base_url}/chat/completions"
        raw_body = json.dumps(body).encode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        last_err: Exception | None = None
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=raw_body, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read())

                content = data["choices"][0]["message"].get("content") or ""
                if not content.strip():
                    if attempt == 0:
                        logger.warning("%s: empty content, retrying", prompt_name)
                        time.sleep(2)
                        continue
                    raise RuntimeError(f"{prompt_name}: empty content after retry")

                parsed = json.loads(content)
                # Attach raw response data for usage extraction
                parsed["_raw_response"] = data
                return parsed

            except urllib.error.HTTPError as exc:
                if exc.code in (429, 500, 502, 503, 504) and attempt == 0:
                    logger.warning("%s: HTTP %d, retrying in 2s", prompt_name, exc.code)
                    time.sleep(2)
                    last_err = exc
                    continue
                raise RuntimeError(f"{prompt_name}: HTTP {exc.code}") from exc

        raise RuntimeError(f"{prompt_name}: failed after retry") from last_err

    @staticmethod
    def _parse_usage(data: dict) -> Usage:
        raw = data.pop("_raw_response", {})
        usage = raw.get("usage", {})
        return Usage(
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
        )
