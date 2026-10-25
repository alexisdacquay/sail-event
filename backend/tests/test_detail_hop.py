"""Detail fetch must honour a total wall-clock deadline (issue #139).

urlopen's timeout is per socket read, so a server that drips one byte at a
time could hold a fetch forever (a 75-minute hang was observed).
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
