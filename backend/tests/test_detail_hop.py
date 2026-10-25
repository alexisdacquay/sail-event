"""Detail fetch must honour a total wall-clock deadline (issue #139).

urlopen's timeout is per socket read, so a server that drips one byte at a
time could hold a fetch forever (a 75-minute hang was observed).
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.services import detail_hop as hop_mod
from app.services.extract import ExtractedEvent


class _DripHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        try:
            for _ in range(60):  # one byte per 0.5 s for 30 s
                self.wfile.write(b"x")
                self.wfile.flush()
                time.sleep(0.5)
        except OSError:
            pass  # client gave up

    def log_message(self, *args):
        pass


@pytest.fixture
def drip_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _DripHandler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def test_slow_drip_server_does_not_hold_detail_fetch(drip_server, monkeypatch):
    monkeypatch.setattr(hop_mod, "DETAIL_FETCH_TIMEOUT", 1)
    ev = ExtractedEvent(
        title="t", start_local="2026-11-07", start_tz=None, end_local=None,
        venue=None, city=None, country=None, link=f"{drip_server}/event",
        description="", confidence=0.9, source_url=f"{drip_server}/listing",
        page_kind="listing",
    )
    started = time.monotonic()
    events, counts = hop_mod.detail_hop(
        [ev], model=MagicMock(), user_tz="UTC",
        window_start=datetime(2026, 10, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        target_city="Vienna", target_country="AT",
    )
    elapsed = time.monotonic() - started
    assert elapsed < 2.5, f"fetch held for {elapsed:.1f}s"
    assert counts.detail_fetch_errors == 1
    assert counts.pages_detail_fetched == 0
    assert events == [ev]


class _StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/gone":  # musicofvienna answers a past performance this way
            self.send_response(410)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html>concert 2026-11-07 20:00</html>")

    def log_message(self, *args):
        pass


@pytest.fixture
def status_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _StatusHandler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def test_fetch_and_extract_errors_are_counted_and_logged_apart(status_server, caplog):
    """Dev Berlin run 2026-10-25: detail_fetch_errors=26 included one model error ('malformed JSON'
    on visitberlin.de/node/2249214), and fetch failures were logged at DEBUG, below dev's INFO,
    so dev's logs could not show which page failed or why."""
    import logging

    def ev(path):
        return ExtractedEvent(
            title="t", start_local="2026-11-07", start_tz=None, end_local=None,
            venue=None, city=None, country=None, link=f"{status_server}{path}",
            description="", confidence=0.9, source_url=f"{status_server}/listing",
            page_kind="listing",
        )

    model = MagicMock()
    model.complete_json.side_effect = RuntimeError("extract: schema violation: malformed JSON")
    with caplog.at_level(logging.INFO, logger="sail-event.detail_hop"):
        _, counts = hop_mod.detail_hop(
            [ev("/gone"), ev("/ok")], model=model, user_tz="UTC",
            window_start=datetime(2026, 10, 1, tzinfo=timezone.utc),
            window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
            target_city="Vienna", target_country="AT",
        )

    assert counts.detail_fetch_errors == 1
    assert counts.pages_detail_fetched == 1
    assert counts.detail_extract_errors == 1
    assert any(
        r.levelno >= logging.WARNING and "/gone" in r.getMessage() and "410" in r.getMessage()
        for r in caplog.records
    ), [r.getMessage() for r in caplog.records]


_MUSIKVEREIN = Path(__file__).resolve().parent / "regression" / "issue_139_musikverein_detail.html"


class _PageHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(_MUSIKVEREIN.read_bytes())

    def log_message(self, *args):
        pass


@pytest.fixture
def page_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _PageHandler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def test_model_reads_the_event_page_as_text_not_html(page_server):
    """London run: the event pages' raw HTML was 7,455,055 of 7,590,352 input tokens (98.2%).
    The Musikverein page carries its 19:30 start only in its meta description."""
    model = MagicMock()
    model.complete_json.return_value = ({"page_kind": "single_event", "events": []}, None)
    ev = ExtractedEvent(
        title="t", start_local="2026-11-07", start_tz=None, end_local=None,
        venue=None, city=None, country=None, link=f"{page_server}/konzert",
        description="", confidence=0.9, source_url=f"{page_server}/listing",
        page_kind="listing",
    )
    hop_mod.detail_hop(
        [ev], model=model, user_tz="Europe/Vienna",
        window_start=datetime(2026, 10, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        target_city="Vienna", target_country="AT",
    )

    content = model.complete_json.call_args.kwargs["variables"]["content"]
    assert "<div" not in content
    assert "<script" not in content
    assert "19:30" in content
    assert '"@context":"https:\\/\\/schema.org"' in content  # JSON-LD body kept
    assert len(content) < 10_000, len(content)  # the HTML is 136,706 characters


def test_hop_to_another_host_only_when_public():
    """A listing may link anywhere; a link on another host must not aim the hop at a private address."""
    from dataclasses import replace
    ev = ExtractedEvent(
        title="t", start_local="2026-11-10T18:00", start_tz=None, end_local=None,
        venue=None, city=None, country=None, link="https://luma.com/granola-jeffrey-veen",
        description="", confidence=0.9, source_url="https://aisa.to/ai-events-london",
        page_kind="listing",
    )
    assert hop_mod._needs_hop(ev)
    for private in ("http://169.254.169.254/latest/meta-data", "http://10.0.0.1/x", "http://localhost:8000/x"):
        assert not hop_mod._needs_hop(replace(ev, link=private)), private
