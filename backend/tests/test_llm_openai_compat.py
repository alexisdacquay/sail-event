"""Contract tests for OpenAICompatibleModel against recorded DeepSeek-shaped responses."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import urllib.error

import pytest

FIXTURES = Path(__file__).parent / "fixtures" / "deepseek"

# Env vars needed by OpenAICompatibleModel.__init__
_ENV = {
    "LLM_BASE_URL": "https://api.deepseek.com",
    "LLM_API_KEY": "test-key-never-real",
    "LLM_MODEL": "deepseek-flash",
    "LLM_JSON_MODE": "json_object",
}


def _make_response(fixture_name: str):
    """Return a context-manager-compatible mock urlopen response."""
    data = (FIXTURES / fixture_name).read_bytes()
    resp = MagicMock()
    resp.read.return_value = data
    resp.__enter__ = lambda s: s
    resp.__exit__ = lambda s, *a: None
    return resp


def _make_model():
    from app.adapters.llm_openai_compat import OpenAICompatibleModel
    with patch.dict("os.environ", _ENV):
        return OpenAICompatibleModel()


class TestRequestBody:
    """Verify the request body sent to the API matches the spec."""

    def test_json_object_mode(self):
        model = _make_model()
        captured = {}

        def fake_urlopen(req, timeout=None):
            body = json.loads(req.data)
            captured.update(body)
            return _make_response("chat_completions_ok.json")

        with patch("app.adapters.llm_openai_compat.urllib.request.urlopen", fake_urlopen):
            model.complete_json(
                prompt_name="guard",
                prompt_version="v1",
                variables={"text": "jazz in Berlin"},
                schema={"type": "object"},
            )

        assert captured["model"] == "deepseek-flash"
        assert captured["temperature"] == 0
        assert captured["max_tokens"] == 16000  # all prompts use 16000 for reasoning models
        assert captured["response_format"] == {"type": "json_object"}
        assert len(captured["messages"]) == 1
        assert captured["messages"][0]["role"] == "user"

    def test_json_schema_mode(self):
        env = {**_ENV, "LLM_JSON_MODE": "json_schema"}
        captured = {}

        def fake_urlopen(req, timeout=None):
            body = json.loads(req.data)
            captured.update(body)
            return _make_response("chat_completions_ok.json")

        from app.adapters.llm_openai_compat import OpenAICompatibleModel
        with patch.dict("os.environ", env):
            model = OpenAICompatibleModel()

        with patch("app.adapters.llm_openai_compat.urllib.request.urlopen", fake_urlopen):
            model.complete_json(
                prompt_name="guard",
                prompt_version="v1",
                variables={"text": "test"},
                schema={"type": "object", "properties": {"blocked": {"type": "boolean"}}},
            )

        rf = captured["response_format"]
        assert rf["type"] == "json_schema"
        assert rf["json_schema"]["name"] == "guard"
        assert rf["json_schema"]["strict"] is True

    def test_max_tokens_per_prompt(self):
        """Each prompt name gets its own max_tokens."""
        model = _make_model()

        from app.adapters.llm_openai_compat import MAX_TOKENS
        for name, expected in MAX_TOKENS.items():
            captured = {}

            def fake_urlopen(req, timeout=None):
                body = json.loads(req.data)
                captured.update(body)
                return _make_response("chat_completions_ok.json")

            # Create a minimal prompt file if needed — guard_v1 is all we have
            if name == "guard":
                with patch("app.adapters.llm_openai_compat.urllib.request.urlopen", fake_urlopen):
                    model.complete_json(
                        prompt_name="guard",
                        prompt_version="v1",
                        variables={"text": "test"},
                        schema={"type": "object"},
                    )
                assert captured["max_tokens"] == expected

    def test_bearer_auth_header(self):
        model = _make_model()
        captured_headers = {}

        def fake_urlopen(req, timeout=None):
            captured_headers["auth"] = req.get_header("Authorization")
            return _make_response("chat_completions_ok.json")

        with patch("app.adapters.llm_openai_compat.urllib.request.urlopen", fake_urlopen):
            model.complete_json(
                prompt_name="guard",
                prompt_version="v1",
                variables={"text": "test"},
                schema={"type": "object"},
            )

        assert captured_headers["auth"] == "Bearer test-key-never-real"


class TestEmptyContentRetry:
    """Empty content → one retry then raise."""

    def test_empty_then_ok(self):
        model = _make_model()
        call_count = 0

        def fake_urlopen(req, timeout=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response("chat_completions_empty_then_ok.json")
            return _make_response("chat_completions_ok.json")

        with patch("app.adapters.llm_openai_compat.urllib.request.urlopen", fake_urlopen):
            with patch("app.adapters.llm_openai_compat.time.sleep"):
                result, usage = model.complete_json(
                    prompt_name="guard",
                    prompt_version="v1",
                    variables={"text": "test"},
                    schema={"type": "object"},
                )

        assert call_count == 2
        assert result["score"] == 85

    def test_empty_twice_raises(self):
        model = _make_model()

        def fake_urlopen(req, timeout=None):
            return _make_response("chat_completions_empty_twice.json")

        with patch("app.adapters.llm_openai_compat.urllib.request.urlopen", fake_urlopen):
            with patch("app.adapters.llm_openai_compat.time.sleep"):
                with pytest.raises(RuntimeError, match="empty content after retry"):
                    model.complete_json(
                        prompt_name="guard",
                        prompt_version="v1",
                        variables={"text": "test"},
                        schema={"type": "object"},
                    )


class TestRetry429:
    """429 → one retry after 2s; second failure raises."""

    def test_429_then_ok(self):
        model = _make_model()
        call_count = 0

        def fake_urlopen(req, timeout=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise urllib.error.HTTPError(
                    req.full_url, 429, "Too Many Requests", {}, io.BytesIO(b"")
                )
            return _make_response("chat_completions_ok.json")

        with patch("app.adapters.llm_openai_compat.urllib.request.urlopen", fake_urlopen):
            with patch("app.adapters.llm_openai_compat.time.sleep") as mock_sleep:
                result, usage = model.complete_json(
                    prompt_name="guard",
                    prompt_version="v1",
                    variables={"text": "test"},
                    schema={"type": "object"},
                )

        assert call_count == 2
        mock_sleep.assert_called_once_with(2)
        assert result["score"] == 85

    def test_429_twice_raises(self):
        model = _make_model()

        def fake_urlopen(req, timeout=None):
            raise urllib.error.HTTPError(
                req.full_url, 429, "Too Many Requests", {}, io.BytesIO(b"")
            )

        with patch("app.adapters.llm_openai_compat.urllib.request.urlopen", fake_urlopen):
            with patch("app.adapters.llm_openai_compat.time.sleep"):
                with pytest.raises(RuntimeError, match="HTTP 429"):
                    model.complete_json(
                        prompt_name="guard",
                        prompt_version="v1",
                        variables={"text": "test"},
                        schema={"type": "object"},
                    )

    def test_5xx_retried(self):
        model = _make_model()
        call_count = 0

        def fake_urlopen(req, timeout=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise urllib.error.HTTPError(
                    req.full_url, 502, "Bad Gateway", {}, io.BytesIO(b"")
                )
            return _make_response("chat_completions_ok.json")

        with patch("app.adapters.llm_openai_compat.urllib.request.urlopen", fake_urlopen):
            with patch("app.adapters.llm_openai_compat.time.sleep"):
                result, _ = model.complete_json(
                    prompt_name="guard",
                    prompt_version="v1",
                    variables={"text": "test"},
                    schema={"type": "object"},
                )

        assert call_count == 2

    def test_400_not_retried(self):
        model = _make_model()

        def fake_urlopen(req, timeout=None):
            raise urllib.error.HTTPError(
                req.full_url, 400, "Bad Request", {}, io.BytesIO(b"")
            )

        with patch("app.adapters.llm_openai_compat.urllib.request.urlopen", fake_urlopen):
            with pytest.raises(RuntimeError, match="HTTP 400"):
                model.complete_json(
                    prompt_name="guard",
                    prompt_version="v1",
                    variables={"text": "test"},
                    schema={"type": "object"},
                )


class TestSchemaValidation:
    """Every response validated against the prompt's JSON schema (design §3)."""

    # Use the real guard_v1.schema.json: {blocked: bool, reason: enum} required, no additionalProperties

    def test_malformed_json_raises_with_prompt_name(self):
        model = _make_model()

        def fake_urlopen(req, timeout=None):
            return _make_response("chat_completions_malformed_json.json")

        with patch("app.adapters.llm_openai_compat.urllib.request.urlopen", fake_urlopen):
            with pytest.raises(RuntimeError, match="guard: schema violation: malformed JSON"):
                model.complete_json(
                    prompt_name="guard",
                    prompt_version="v1",
                    variables={"text": "test"},
                )

    def test_missing_required_field_raises_with_field_name(self):
        model = _make_model()

        def fake_urlopen(req, timeout=None):
            return _make_response("chat_completions_missing_field.json")

        with patch("app.adapters.llm_openai_compat.urllib.request.urlopen", fake_urlopen):
            with pytest.raises(RuntimeError, match=r"guard: schema violation: missing required field 'reason'"):
                model.complete_json(
                    prompt_name="guard",
                    prompt_version="v1",
                    variables={"text": "test"},
                )

    def test_valid_response_passes(self):
        """A response matching the schema passes without error."""
        model = _make_model()

        # Build a response with valid guard output
        data = json.loads((FIXTURES / "chat_completions_ok.json").read_text())
        data["choices"][0]["message"]["content"] = json.dumps(
            {"blocked": False, "reason": "ok"}
        )
        raw = json.dumps(data).encode()

        def fake_urlopen(req, timeout=None):
            resp = MagicMock()
            resp.read.return_value = raw
            resp.__enter__ = lambda s: s
            resp.__exit__ = lambda s, *a: None
            return resp

        with patch("app.adapters.llm_openai_compat.urllib.request.urlopen", fake_urlopen):
            result, usage = model.complete_json(
                prompt_name="guard",
                prompt_version="v1",
                variables={"text": "test"},
            )

        assert result == {"blocked": False, "reason": "ok"}


class TestUsage:
    """Usage parsing from the DeepSeek response."""

    def test_usage_parsed(self):
        model = _make_model()

        def fake_urlopen(req, timeout=None):
            return _make_response("chat_completions_ok.json")

        with patch("app.adapters.llm_openai_compat.urllib.request.urlopen", fake_urlopen):
            _, usage = model.complete_json(
                prompt_name="guard",
                prompt_version="v1",
                variables={"text": "test"},
                schema={"type": "object"},
            )

        assert usage.tokens_in == 150
        assert usage.tokens_out == 20

    def test_usage_zeros_when_absent(self):
        model = _make_model()

        # Build a response with no usage field
        data = json.loads((FIXTURES / "chat_completions_ok.json").read_text())
        del data["usage"]
        raw = json.dumps(data).encode()

        def fake_urlopen(req, timeout=None):
            resp = MagicMock()
            resp.read.return_value = raw
            resp.__enter__ = lambda s: s
            resp.__exit__ = lambda s, *a: None
            return resp

        with patch("app.adapters.llm_openai_compat.urllib.request.urlopen", fake_urlopen):
            _, usage = model.complete_json(
                prompt_name="guard",
                prompt_version="v1",
                variables={"text": "test"},
                schema={"type": "object"},
            )

        assert usage.tokens_in == 0
        assert usage.tokens_out == 0
