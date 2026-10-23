"""Page classification test against labelled ground-truth pages.

Runs the extractor over the raw_content snapshots in pages.json and checks
that every has_events=true page yields at least 1 event. Reports the ratio;
fails under 90%.

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


def _extract_page(page: dict, model) -> list[dict]:
    """Run the extractor over a single page's raw_content snapshot."""
    from app.adapters.search import SearchResult
    from app.services.extract import extract_events

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

    # Use a broad window so the extractor doesn't filter by date
    window_start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    window_end = datetime(2027, 1, 1, tzinfo=timezone.utc)

    events, _counts = extract_events(
        [result],
        window_start=window_start,
        window_end=window_end,
        target_city="",
        target_country="",
        language=None,
        user_tz="UTC",
        model=model,
    )
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

    for p in true_pages:
        events = _extract_page(p, model)
        if len(events) >= 1:
            hits += 1
        else:
            misses.append(p["url"])

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
        f"Page classification ratio {ratio:.1%} is below 90% threshold. "
        f"Misses: {misses}"
    )
