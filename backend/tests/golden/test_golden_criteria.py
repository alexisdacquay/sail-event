"""Golden set A — 13 criteria texts → expected Facets via the fake model."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import timezone
from pathlib import Path

import pytest

# FAKE_NOW must be set for stable prompt hashes
pytestmark = pytest.mark.skipif(
    not os.environ.get("FAKE_NOW"),
    reason="FAKE_NOW required for golden tests",
)

GOLDEN_PATH = Path(__file__).parent / "criteria.json"


def _load_golden():
    data = json.loads(GOLDEN_PATH.read_text())
    return data["entries"]


def _ids(entries):
    return [e["id"] for e in entries]


@pytest.fixture(params=_load_golden(), ids=_ids(_load_golden()))
def golden_entry(request):
    return request.param


def test_golden_criteria(golden_entry, monkeypatch):
    """Parse criteria text through the fake model and compare to expected facets."""
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    from app.adapters.factory import get_language_model
    from app.services.criteria import parse_criteria

    entry = golden_entry
    text = entry["text"]
    user_tz = entry["user_tz"]
    expected = entry["expected"]

    model = get_language_model()
    result = parse_criteria(text, user_tz, model)

    # Field-level comparison
    _compare_place(expected.get("place"), result.get("place"), entry["id"])
    _compare_date(expected.get("date"), result.get("date"), entry["id"])
    _compare_topics(expected.get("topics", []), result.get("topics", []), entry["id"])
    _compare_topics_local_nonempty(expected.get("topics", []), result.get("topics_local", []), entry["id"], expected.get("language"))
    _compare_formats(expected.get("formats", []), result.get("formats", []), entry["id"])
    _compare_budget(expected.get("budget"), result.get("budget"), entry["id"])
    _compare_scalar("language", expected.get("language"), result.get("language"), entry["id"])
    _compare_scalar("input_language", expected.get("input_language"), result.get("input_language"), entry["id"])


def _compare_place(expected, actual, cid):
    if expected is None:
        assert actual is None, f"{cid}: expected place=null, got {actual}"
        return
    assert actual is not None, f"{cid}: expected place, got null"
    assert actual["city"] == expected["city"], f"{cid}: city"
    assert actual["country"] == expected["country"], f"{cid}: country"
    if expected.get("region") is not None:
        assert actual.get("region") is not None, f"{cid}: expected region"
        # Allow "the Solent" vs "Solent" etc.
        assert expected["region"].lower() in actual["region"].lower() or actual["region"].lower() in expected["region"].lower(), \
            f"{cid}: region expected={expected['region']!r}, got={actual.get('region')!r}"
    if expected.get("radius_km") is not None:
        assert actual.get("radius_km") is not None, f"{cid}: expected radius_km"
        assert abs(actual["radius_km"] - expected["radius_km"]) <= 10, \
            f"{cid}: radius_km expected≈{expected['radius_km']}, got={actual.get('radius_km')}"
    assert actual["online"] == expected["online"], f"{cid}: online"


def _compare_date(expected, actual, cid):
    if expected is None:
        return
    assert actual is not None, f"{cid}: expected date, got null"
    assert actual["start"] == expected["start"], f"{cid}: date.start"
    assert actual["end"] == expected["end"], f"{cid}: date.end"
    assert actual["relative"] == expected["relative"], f"{cid}: date.relative"
    assert actual.get("relative_n") == expected.get("relative_n"), f"{cid}: date.relative_n"


def _compare_topics(expected, actual, cid):
    """Each expected topic keyword appears in at least one actual topic (case-insensitive)."""
    actual_lower = [t.lower() for t in actual]
    for exp in expected:
        found = any(exp.lower() in act for act in actual_lower)
        assert found, f"{cid}: expected topic {exp!r} not found in {actual}"


def _compare_topics_local_nonempty(expected_topics, actual_local, cid, language):
    """When there are topics and the language is not English, topics_local must be non-empty."""
    if expected_topics and language and language != "en":
        assert len(actual_local) > 0, f"{cid}: topics_local should be non-empty for language={language}"


def _compare_formats(expected, actual, cid):
    exp_set = {f.lower() for f in expected}
    act_set = {f.lower() for f in actual}
    assert exp_set.issubset(act_set), f"{cid}: formats missing {exp_set - act_set}, got {act_set}"


def _compare_budget(expected, actual, cid):
    if expected is None:
        return
    assert actual is not None, f"{cid}: expected budget, got null"
    assert actual["max_amount"] == expected["max_amount"], f"{cid}: budget.max_amount"
    assert actual["currency"] == expected["currency"], f"{cid}: budget.currency"
    assert actual["free_only"] == expected["free_only"], f"{cid}: budget.free_only"


def _compare_scalar(name, expected, actual, cid):
    assert actual == expected, f"{cid}: {name} expected={expected!r}, got={actual!r}"
