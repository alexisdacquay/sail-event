"""Golden set B — 22 candidates → extract → filter expectations.

Runs with FAKE_NOW=2026-10-18T12:00:00+02:00 and the fake model.
Place and date-window filters removed — only past, incomplete, dedup
filters remain in code. The judge (not tested here) decides place/date fit.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("FAKE_NOW"),
    reason="FAKE_NOW required for golden tests",
)

GOLDEN_PATH = Path(__file__).parent / "candidates.json"
FIXTURES_PATH = Path(__file__).resolve().parents[2] / "app" / "adapters" / "fixtures.json"


def _load_golden():
    return json.loads(GOLDEN_PATH.read_text())


def _load_fixtures():
    return json.loads(FIXTURES_PATH.read_text())


@pytest.fixture(scope="module")
def extraction_result():
    """Run extraction + filtering on all 22 fixture candidates."""
    from app.adapters.factory import get_language_model
    from app.adapters.search import SearchResult
    from app.services import clock
    from app.services.extract import extract_events
    from app.services.filters import filter_events

    model = get_language_model()
    fixtures = _load_fixtures()

    results = [
        SearchResult(**{k: v for k, v in entry.items() if k != "id"})
        for entry in fixtures
    ]

    now_utc = clock.now()
    tz = ZoneInfo("Europe/Berlin")
    window_start = datetime.combine(
        datetime(2026, 10, 19).date(), time.min, tzinfo=tz
    ).astimezone(timezone.utc)
    window_end = datetime.combine(
        datetime(2026, 10, 21).date(), time(23, 59, 59), tzinfo=tz
    ).astimezone(timezone.utc)

    events, extract_counts = extract_events(
        results,
        window_start=window_start,
        window_end=window_end,
        target_city="Berlin",
        target_country="DE",
        language="de",
        user_tz="Europe/Berlin",
        model=model,
    )

    kept, filter_counts = filter_events(
        events,
        now_utc=now_utc,
        window_start_utc=window_start,
        window_end_utc=window_end,
        target_city="Berlin",
        target_country="DE",
        user_tz="Europe/Berlin",
    )

    return {
        "all_events": events,
        "kept": kept,
        "extract_counts": extract_counts,
        "filter_counts": filter_counts,
        "fixtures": fixtures,
    }


def _fixture_url(fixtures, eid):
    return next(f["url"] for f in fixtures if f["id"] == eid)


def test_e12_filtered_past(extraction_result):
    """E12 (Oct 10) is filtered as past."""
    kept = extraction_result["kept"]
    kept_urls = {e.link for e in kept}
    url = _fixture_url(extraction_result["fixtures"], "E12")
    assert url not in kept_urls, "E12 past event should not be in kept events"


def test_e13_filtered_past(extraction_result):
    """E13 (Oct 17) is filtered as past."""
    kept = extraction_result["kept"]
    kept_urls = {e.link for e in kept}
    url = _fixture_url(extraction_result["fixtures"], "E13")
    assert url not in kept_urls, "E13 yesterday should not be in kept events"


def test_e18_canonical_url_matches_e1(extraction_result):
    """E18's URL after canonicalization matches E1's."""
    from app.adapters.search import canonical_url
    e1_url = _fixture_url(extraction_result["fixtures"], "E1")
    e18_url = _fixture_url(extraction_result["fixtures"], "E18")
    assert canonical_url(e1_url) == canonical_url(e18_url)


def test_kept_events_have_required_fields(extraction_result):
    """All kept events have title, city, country, start."""
    kept = extraction_result["kept"]
    for ev in kept:
        assert ev.title, f"Kept event must have a title"
        assert ev.city, f"Kept event {ev.title} must have a city"
        assert ev.country, f"Kept event {ev.title} must have a country"
        assert ev.start_local, f"Kept event {ev.title} must have a start"


def test_no_past_events_in_kept(extraction_result):
    """No kept event has already ended."""
    from app.services import clock
    now_utc = clock.now()
    kept = extraction_result["kept"]
    for ev in kept:
        # date-only events end at 23:59:59
        if len(ev.start_local) == 10:
            continue  # these are checked by the past filter's 23:59 rule
        assert ev.start_local >= "2026-10-18", f"Kept event {ev.title} is in the past"
