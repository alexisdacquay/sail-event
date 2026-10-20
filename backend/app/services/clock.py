"""Clock — all 'now' values come from here.

Honours FAKE_NOW (ISO-8601) when set, else datetime.now(UTC).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime


def now() -> datetime:
    fake = os.environ.get("FAKE_NOW")
    if fake:
        return datetime.fromisoformat(fake)
    return datetime.now(UTC)
