"""Tests for OTel telemetry init (issue #23)."""

from __future__ import annotations

from app.telemetry import init


def test_init_noop_when_endpoint_unset(monkeypatch):
    """No SDK providers or background threads when endpoint is absent."""
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    init()  # should not raise


def test_init_noop_when_endpoint_empty(monkeypatch):
    """Whitespace-only endpoint treated as unset."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "  ")
    init()  # should not raise


def test_pipeline_spans_noop_without_endpoint(client, auth_headers, monkeypatch):
    """Pipeline runs successfully with no-op tracer/meter (no endpoint)."""
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    h = auth_headers("demo", "demo")
    r = client.post("/api/search", headers=h)
    assert r.status_code == 200
    assert "runId" in r.json()
