"""Page classification test against labelled ground-truth pages.

Runs the pass-2 (raw_content) extractor over the snapshots in pages.json
and checks that every has_events=true page yields at least 1 event.
Reports the ratio; fails under 90%.

This calls the content extraction path directly, bypassing the snippet gate
(pass 1), because we are testing whether the model can find events in the
page content, not whether the snippet heuristic triggers pass 2.

Requires LLM_PROVIDER to be set (uses the real model, not recorded).
Skips gracefully when no model is available so `make test` stays green.

Usage with live model:
    set -a; . backend/.env.local; set +a
    uv run --project backend --directory backend pytest \
        tests/ground_truth/test_page_classification.py -v -s
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

PAGES_PATH = Path(__file__).parent / "pages.json"

_has_llm = bool(os.environ.get("LLM_PROVIDER"))

pytestmark = pytest.mark.skipif(
    not _has_llm,
    reason="LLM_PROVIDER not set; page classification needs a live model",
)


@pytest.fixture(scope="module")
def pages():
    with open(PAGES_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def model():
    from app.adapters.factory import get_language_model
    return get_language_model()


def _extract_page_pass2(page: dict, model) -> list[dict]:
    """Run the pass-2 (raw_content) extractor directly on one page."""
    from app.adapters.search import SearchResult
    from app.services.extract import (
        PROMPT_NAME, PROMPT_VERSION,
        _read_schema, _process_pass2,
        ExtractionCounts,
    )
    from app.services import clock

    raw_content = page.get("raw_content", "")
    if not raw_content:
        return []

    result = SearchResult(
        url=page["url"],
        title=page["title"],
        snippet="",
        raw_content=raw_content,
        provider="ground_truth_snapshot",
    )

    # Broad window
    window_start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    window_end = datetime(2027, 1, 1, tzinfo=timezone.utc)

    schema = _read_schema()
    schema_text = json.dumps(schema, indent=2)

    ws = window_start.strftime("%Y-%m-%d")
    we = window_end.strftime("%Y-%m-%d")
    today = clock.now().strftime("%Y-%m-%d")

    variables = {
        "today": today,
        "window_start": ws,
        "window_end": we,
        "target_city": "",
        "target_country": "",
        "content": f"URL: {page['url']}\n\n{raw_content}",
        "schema": schema_text,
        "links_rule": "",
    }

    try:
        response, _usage = model.complete_json(
            prompt_name=PROMPT_NAME,
            prompt_version=PROMPT_VERSION,
            variables=variables,
        )
    except Exception as exc:
        print(f"    extract error for {page['url'][:60]}: {exc}")
        return []

    counts = ExtractionCounts()
    events = _process_pass2(response, result, counts)
    return [
        {"title": e.title, "start": e.start_local, "city": e.city}
        for e in events
    ]


def test_page_classification(pages, model):
    """Every has_events=true page should yield >= 1 event from the extractor."""
    true_pages = [p for p in pages if p["has_events"]]
    assert len(true_pages) > 0, "No has_events=true pages in pages.json"

    hits = 0
    misses = []

    for i, p in enumerate(true_pages):
        print(f"  [{i+1}/{len(true_pages)}] {p['title'][:50]}...", end=" ", flush=True)
        events = _extract_page_pass2(p, model)
        if len(events) >= 1:
            hits += 1
            print(f"OK ({len(events)} events)")
        else:
            misses.append(p["url"])
            print(f"MISS (0 events)")

    total = len(true_pages)
    ratio = hits / total if total else 0

    # Report
    print(f"\n=== Page classification results ===")
    print(f"  has_events=true pages: {total}")
    print(f"  pages with >= 1 extracted event: {hits}")
    print(f"  ratio: {ratio:.1%}")
    if misses:
        print(f"  misses ({len(misses)}):")
        for url in misses:
            print(f"    - {url}")

    assert ratio >= 0.9, (
        f"Page classification ratio {ratio:.1%} is below 90% target. "
        f"Misses: {misses}"
    )
