"""RawEvent model and adapter protocols."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel


class RawEvent(BaseModel):
    title: str
    date_time: str
    place: str
    link: str
    description: str


class SearchProvider(Protocol):
    def search(self, queries: list[str]) -> list[RawEvent]: ...


class Scorer(Protocol):
    def score(self, event: RawEvent, criteria: str) -> tuple[int, str]: ...
