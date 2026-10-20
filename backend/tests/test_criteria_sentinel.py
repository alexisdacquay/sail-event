"""Sentinel test — criteria, query and page text must not appear in log records."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.adapters.search import SearchResult
from app.services.extract import ExtractedEvent


SENTINEL = "SENTINEL-7Q-criteria-text-must-not-leak"
QUERY_SENTINEL = "QUERY-SENTINEL-8X-must-not-leak"
PAGE_SENTINEL = "PAGE-SENTINEL-9Y-must-not-leak"


def test_criteria_text_not_in_logs(monkeypatch, caplog):
    """Parsing criteria must not log the criteria text."""
    monkeypatch.setenv("FAKE_NOW", "2026-10-18T12:00:00+02:00")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    from app.adapters.factory import get_language_model
    from app.services.criteria import parse_criteria

    model = get_language_model()

    # The sentinel text won't have a recording, so the call will raise.
    # That's expected — we just need to check no log record contains the text.
    with caplog.at_level(logging.DEBUG):
        try:
            parse_criteria(SENTINEL, "UTC", model)
        except FileNotFoundError:
            pass  # expected: no recording for the sentinel text

    for record in caplog.records:
        assert SENTINEL not in record.getMessage(), \
            f"Criteria text leaked into log: {record.getMessage()!r}"


def test_query_text_not_in_logs(monkeypatch, caplog, _db_session):
    """Query text flowing through the search stage must not appear in logs.

    Patches the planner to emit a query carrying the sentinel, and the search
    provider to accept it. The pipeline's search loop processes the sentinel
    query; no log record may contain it.
    """
    monkeypatch.setenv("FAKE_NOW", "2026-10-18T12:00:00+02:00")

    from app.orm import User, Criteria
    from app.services.pipeline import run_pipeline
    from app.services.planner import PlannedQuery

    user = _db_session.query(User).filter(User.username == "demo").first()

    # Provider that records what query text it received
    class _SentinelProvider:
        name = "sentinel_test"
        def search(self, query, **kw):
            # Return one result so the pipeline continues
            return [SearchResult(
                url="https://example.com/sentinel",
                title="Sentinel Result",
                snippet="snippet",
                raw_content=None,
                published_at=None,
                provider="sentinel_test",
            )]

    # Planner that emits the sentinel query
    def _sentinel_plan(facets, window, **kw):
        return [PlannedQuery(text=QUERY_SENTINEL, country="DE", language="de", priority=1)]

    with caplog.at_level(logging.DEBUG):
        with patch("app.services.pipeline.get_search_provider", return_value=_SentinelProvider()), \
             patch("app.services.pipeline.plan_queries", side_effect=_sentinel_plan):
            run_pipeline(user, _db_session, trigger="manual")

    for record in caplog.records:
        assert QUERY_SENTINEL not in record.getMessage(), \
            f"Query text leaked into log: {record.getMessage()!r}"


def test_page_text_not_in_logs(monkeypatch, caplog, _db_session):
    """Page raw_content flowing through extract must not appear in logs.

    Patches the search provider to return a result whose raw_content is the
    sentinel, then runs the pipeline. No log record may contain the sentinel.
    """
    monkeypatch.setenv("FAKE_NOW", "2026-10-18T12:00:00+02:00")

    from app.orm import User
    from app.services.pipeline import run_pipeline
    from app.services.planner import PlannedQuery

    user = _db_session.query(User).filter(User.username == "demo").first()

    class _PageSentinelProvider:
        name = "sentinel_test"
        def search(self, query, **kw):
            return [SearchResult(
                url="https://example.com/page-sentinel",
                title="Page Sentinel",
                snippet="snippet",
                raw_content=PAGE_SENTINEL * 10,
                published_at=None,
                provider="sentinel_test",
            )]

    def _plan(facets, window, **kw):
        return [PlannedQuery(text="safe query text", country="DE", language="de", priority=1)]

    with caplog.at_level(logging.DEBUG):
        with patch("app.services.pipeline.get_search_provider", return_value=_PageSentinelProvider()), \
             patch("app.services.pipeline.plan_queries", side_effect=_plan):
            run_pipeline(user, _db_session, trigger="manual")

    for record in caplog.records:
        assert PAGE_SENTINEL not in record.getMessage(), \
            f"Page text leaked into log: {record.getMessage()!r}"
