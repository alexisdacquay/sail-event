"""LLM smoke test — prove the key works by sending one judge-shaped request.

Reads LLM_BASE_URL, LLM_MODEL, LLM_API_KEY, LLM_JSON_MODE from env.
Prints the parsed result and token usage, never the key.

Usage:
    LLM_BASE_URL=https://api.deepseek.com \
    LLM_MODEL=deepseek-flash \
    LLM_API_KEY=<key> \
    LLM_JSON_MODE=json_object \
    uv run python backend/scripts/llm_smoke.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    base_url = os.environ.get("LLM_BASE_URL")
    model = os.environ.get("LLM_MODEL")
    api_key = os.environ.get("LLM_API_KEY")
    json_mode = os.environ.get("LLM_JSON_MODE", "json_object")

    missing = [k for k in ("LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY")
               if not os.environ.get(k)]
    if missing:
        print(f"Missing env vars: {', '.join(missing)}", file=sys.stderr)
        return 1

    prompt = (
        'Score the following event against the criteria.\n\n'
        'Event: Jazz trio at A-Trane in Berlin on 20 Oct 2026, 18 EUR.\n'
        'Criteria: jazz in Berlin next week.\n\n'
        'Return a JSON object: {"score": <int 0-100>, "reason": <string>}\n'
        'Respond with json.'
    )

    body: dict = {
        "model": model,
        "temperature": 0,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}],
    }

    if json_mode == "json_object":
        body["response_format"] = {"type": "json_object"}
    elif json_mode == "json_schema":
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "smoke",
                "schema": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer"},
                        "reason": {"type": "string"},
                    },
                    "required": ["score", "reason"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        }

    url = f"{base_url.rstrip('/')}/chat/completions"
    raw = json.dumps(body).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(url, data=raw, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code}: {exc.read().decode()[:500]}", file=sys.stderr)
        return 1

    content = data["choices"][0]["message"].get("content", "")
    usage = data.get("usage", {})

    print("=== Parsed result ===")
    try:
        parsed = json.loads(content)
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        print(f"Raw (not JSON): {content}")

    print("\n=== Token usage ===")
    print(f"  prompt_tokens:     {usage.get('prompt_tokens', '?')}")
    print(f"  completion_tokens: {usage.get('completion_tokens', '?')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
