"""OpenTelemetry SDK bootstrap — no-op when OTEL_EXPORTER_OTLP_ENDPOINT is unset."""

from __future__ import annotations

import os


def init(*, app: object | None = None) -> None:
    """Initialise TracerProvider + MeterProvider with OTLP HTTP exporters.

    Returns immediately (no-op providers, no background threads) when
    OTEL_EXPORTER_OTLP_ENDPOINT is empty, so tests run clean.
    """
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        return

    from opentelemetry import trace, metrics
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor

    resource = Resource.create({
        "service.name": "sail-event-backend",
        "deployment.environment": os.environ.get("APP_ENV", "dev"),
        "service.version": os.environ.get("APP_VERSION", "dev"),
    })

    # Traces
    tp = TracerProvider(resource=resource)
    tp.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tp)

    # Metrics
    reader = PeriodicExportingMetricReader(OTLPMetricExporter())
    mp = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(mp)

    # FastAPI auto-instrumentation (HTTP spans + request metrics)
    if app is not None:
        FastAPIInstrumentor.instrument_app(app)
    else:
        FastAPIInstrumentor.instrument()

    # Inject trace_id / span_id into stdlib log records
    LoggingInstrumentor().instrument(set_logging_format=False)
