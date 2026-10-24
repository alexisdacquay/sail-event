"""Regression: #125 — judge missing is_event is repaired; extra fields are dropped.

Root cause: judge_v3.md never mentioned is_event, and validate_response
rejected unknown extra fields.  Fix: prompt describes is_event, validation
drops extras with a debug log, repair loop retries once on schema violation.
"""
from app.adapters.prompts.loader import validate_response


def _judge_schema():
    """Minimal subset of the judge schema with is_event, score, reason."""
    return {
        "type": "object",
        "required": ["score", "reason", "is_event"],
        "additionalProperties": False,
        "properties": {
            "score": {"type": "number", "minimum": 0, "maximum": 100},
            "reason": {"type": "string"},
            "is_event": {"type": "boolean"},
        },
    }


def test_extra_field_dropped_not_rejected():
    """#125: an unknown extra field (e.g. 'type') is silently dropped."""
    response = {"score": 80, "reason": "ok", "is_event": True, "type": "suitability"}
    validate_response("judge_v3", response, _judge_schema())
    assert "type" not in response
    assert response["score"] == 80


def test_missing_is_event_raises_for_repair():
    """#125: missing is_event triggers a RuntimeError so the repair loop fires."""
    response = {"score": 80, "reason": "ok"}
    try:
        validate_response("judge_v3", response, _judge_schema())
        assert False, "expected RuntimeError for missing is_event"
    except RuntimeError as e:
        assert "is_event" in str(e)
