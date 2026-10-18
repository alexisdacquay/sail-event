"""Fake scorer — deterministic score derived from event title via MD5."""

from __future__ import annotations

import hashlib
import struct

from .base import RawEvent


class FakeScorer:
    def score(self, event: RawEvent, criteria: str) -> tuple[int, str]:
        digest = hashlib.md5(event.title.encode()).digest()
        value = struct.unpack_from("<I", digest)[0] % 101
        return (value, "Sample reason from the fixture scorer.")
