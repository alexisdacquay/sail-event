"""Fixture search provider — returns canned events from fixtures.json."""

from __future__ import annotations

import importlib.resources
import json

from .base import RawEvent


class FixtureSearchProvider:
    def __init__(self) -> None:
        ref = importlib.resources.files(__package__).joinpath("fixtures.json")
        raw = ref.read_text(encoding="utf-8")
        self._events: list[RawEvent] = [RawEvent(**e) for e in json.loads(raw)]

    def search(self, queries: list[str]) -> list[RawEvent]:
        return list(self._events)
