"""Contract tests for adapter interfaces and fixture/fake implementations."""

import os

import pytest

from app.adapters import (
    FakeScorer,
    FixtureSearchProvider,
    RawEvent,
    get_scorer,
    get_search_provider,
)


# ---------- FixtureSearchProvider ----------


class TestFixtureSearchProvider:
    def test_returns_non_empty_list_of_raw_events(self):
        provider = FixtureSearchProvider()
        events = provider.search(["anything"])
        assert len(events) > 0
        for event in events:
            assert isinstance(event, RawEvent)
            assert isinstance(event.title, str) and event.title != ""
            assert isinstance(event.date_time, str) and event.date_time != ""
            assert isinstance(event.place, str) and event.place != ""
            assert isinstance(event.link, str) and event.link != ""
            assert isinstance(event.description, str) and event.description != ""

    def test_returns_same_list_on_repeated_calls(self):
        provider = FixtureSearchProvider()
        first = provider.search(["q1"])
        second = provider.search(["q2"])
        assert first == second

    def test_at_least_8_events_and_exactly_two_share_a_link(self):
        events = FixtureSearchProvider().search([])
        assert len(events) >= 8
        from collections import Counter
        counts = Counter(e.link for e in events)
        duplicated = [link for link, n in counts.items() if n > 1]
        assert len(duplicated) == 1
        assert counts[duplicated[0]] == 2


# ---------- FakeScorer ----------


class TestFakeScorer:
    def test_deterministic_for_same_event_and_criteria(self):
        scorer = FakeScorer()
        event = FixtureSearchProvider().search([])[0]
        first = scorer.score(event, "some criteria")
        second = scorer.score(event, "some criteria")
        assert first == second

    def test_same_score_with_different_criteria(self):
        scorer = FakeScorer()
        event = FixtureSearchProvider().search([])[0]
        first = scorer.score(event, "outdoor activities")
        second = scorer.score(event, "tech conferences")
        assert first == second

    def test_score_range_and_reason_for_all_fixtures(self):
        scorer = FakeScorer()
        events = FixtureSearchProvider().search([])
        for event in events:
            score, reason = scorer.score(event, "test criteria")
            assert isinstance(score, int)
            assert 0 <= score <= 100
            assert reason == "Sample reason from the fixture scorer."


# ---------- Factory functions ----------


class TestFactories:
    def test_get_search_provider_default(self, monkeypatch):
        monkeypatch.delenv("SEARCH_PROVIDER", raising=False)
        provider = get_search_provider()
        assert isinstance(provider, FixtureSearchProvider)

    def test_get_scorer_default(self, monkeypatch):
        monkeypatch.delenv("SCORER", raising=False)
        scorer = get_scorer()
        assert isinstance(scorer, FakeScorer)

    def test_explicit_env_returns_expected_classes(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "fixture")
        monkeypatch.setenv("SCORER", "fake")
        assert isinstance(get_search_provider(), FixtureSearchProvider)
        assert isinstance(get_scorer(), FakeScorer)

    def test_get_search_provider_raises_on_unknown(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "unknown")
        with pytest.raises(ValueError, match="unknown"):
            get_search_provider()

    def test_get_scorer_raises_on_unknown(self, monkeypatch):
        monkeypatch.setenv("SCORER", "unknown")
        with pytest.raises(ValueError, match="unknown"):
            get_scorer()
