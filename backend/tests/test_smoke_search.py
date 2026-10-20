"""Tests for smoke_search.py — table formatting and CLI argument parsing."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "smoke_search.py"


def test_batch_table_has_header_and_ten_rows(tmp_path, monkeypatch):
    """Import _run_batch's table builder indirectly: just verify the Markdown
    structure from _run_batch by calling the module-level helper."""
    # We can't run live adapters in unit tests, but we can test the table
    # builder by importing and calling with mocked data.
    sys.path.insert(0, str(SCRIPT.parent.parent))
    from scripts.smoke_search import _run_batch, _run_once, BATCH_TEXTS

    call_count = 0

    def fake_run_once(text, tz, record):
        nonlocal call_count
        call_count += 1
        run = {
            "stopped_at_stage": None if call_count != 7 else "search",
            "error": None if call_count != 7 else "no place in criteria",
            "error_detail": None,
            "search_calls": 2,
            "llm_calls": 3,
            "llm_tokens_in": 100,
            "llm_tokens_out": 50,
            "events_found": 4,
            "events_new": 2,
            "stage_counts": {
                "queries_planned": 2,
                "results_fetched": 6,
                "events_extracted": 3,
            },
            "started_at": None,
            "finished_at": None,
        }
        events = [
            {"title": "Test Event", "score": 85, "status": "accepted",
             "score_reason": "good", "date_time": "2026-10-20",
             "start_tz": "Europe/Berlin", "city": "Berlin", "country": "DE",
             "link": "https://example.com/1"},
        ] if call_count != 7 else []
        return run, events

    monkeypatch.setattr("scripts.smoke_search._run_once", fake_run_once)

    table = _run_batch("Europe/Berlin")
    lines = table.strip().split("\n")

    # Header + separator + N data rows (one per BATCH_TEXTS entry)
    assert len(lines) == 2 + len(BATCH_TEXTS)
    assert lines[0].startswith("| # |")
    assert lines[1].startswith("|---|")
    # Each data row starts with | N |
    for i, line in enumerate(lines[2:], 1):
        assert line.startswith(f"| {i} |"), f"Row {i} malformed: {line[:30]}"


def test_cli_requires_criteria_or_batch():
    """--criteria or --batch is required."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "criteria" in result.stderr.lower() or "batch" in result.stderr.lower()
