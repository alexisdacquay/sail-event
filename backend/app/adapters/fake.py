"""Fake scorer — deterministic score derived from event title via MD5."""

from __future__ import annotations

import hashlib
import struct

from .base import RawEvent


class FakeScorer:
    def score(self, event: RawEvent, criteria: str) -> tuple[int, str]:
        raise RuntimeError("injected: scorer fault")
        digest = hashlib.md5(event.title.encode()).digest()
        value = struct.unpack_from("<I", digest)[0] % 101
        return (value, f"md5(title) first-4-bytes mod 101 = {value}")
