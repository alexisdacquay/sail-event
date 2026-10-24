"""Ground-truth recall matching — moved from backend/scripts/recall.py."""
from __future__ import annotations

from difflib import SequenceMatcher
from urllib.parse import urlparse


def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def date_matches(event_dt: str | None, gt_date: str) -> bool:
    if not event_dt:
        return False
    return event_dt[:10] == gt_date[:10]


def url_matches(ev_url: str | None, gt_url: str) -> bool:
    if not ev_url or not gt_url:
        return False
    a, b = urlparse(ev_url), urlparse(gt_url)
    return (a.netloc.lower() == b.netloc.lower()
            and a.path.rstrip("/") == b.path.rstrip("/"))


def is_match(gt: dict, ev: dict) -> tuple[bool, float]:
    """Return (matched, similarity).

    A ground-truth event matches a found event when:
      - title similarity >= 0.75, OR
      - the found event's link or sourceUrl matches the GT URL (host+path), OR
      - title similarity >= 0.5 AND the date is the same day.
    """
    sim = title_similarity(gt["title"], ev.get("title", ""))
    if sim >= 0.75:
        return True, sim
    gt_url = gt.get("url", "")
    if url_matches(ev.get("link"), gt_url) or url_matches(ev.get("sourceUrl"), gt_url):
        return True, max(sim, 0.75)
    if sim >= 0.5 and date_matches(ev.get("dateTime"), gt["date"]):
        return True, sim
    return False, sim


def diagnose_miss(gt: dict, counts: dict) -> str:
    """Best guess at which stage lost a ground-truth event, from counts only."""
    extracted = counts.get("events_extracted", 0)
    non_event = counts.get("filtered_non_event", 0)
    fetched = counts.get("results_fetched", 0)

    if extracted == 0 and fetched == 0:
        return "not_fetched"
    if extracted == 0 and fetched > 0:
        return "no_event_extracted"
    if non_event > counts.get("pages_with_events", 0):
        return "likely_no_event_extracted"
    if counts.get("filtered_place", 0) > 0:
        return "possibly_filtered_place"
    if counts.get("filtered_date", 0) > 0:
        return "possibly_filtered_date"
    if counts.get("filtered_past", 0) > 0:
        return "possibly_filtered_past"
    if counts.get("filtered_incomplete", 0) > 0:
        return "possibly_filtered_incomplete"
    return "not_in_search_results"
