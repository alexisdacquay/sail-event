"""Detail-page hop — stub, not yet implemented.

Issue #139: for listing-page events with a same-site link, fetch the
event's own page and re-extract.  This stub returns events unchanged.
"""

from __future__ import annotations

import urllib.request  # noqa: F401 — used by tests via patch
from dataclasses import dataclass
from datetime import datetime

from ..services.extract import ExtractedEvent


@dataclass
class HopCounts:
    pages_detail_fetched: int = 0
    detail_fetch_errors: int = 0


def detail_hop(
    events: list[ExtractedEvent],
    *,
    model,
    user_tz: str,
    window_start: datetime,
    window_end: datetime,
    target_city: str,
    target_country: str,
) -> tuple[list[ExtractedEvent], HopCounts]:
    """Placeholder — returns events unchanged.  Implemented in #139."""
    return events, HopCounts()
