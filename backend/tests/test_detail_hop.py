"""Detail fetch must honour a total wall-clock deadline (issue #139).

urlopen's timeout is per socket read, so a server that drips one byte at a
time could hold a fetch forever (a 75-minute hang was observed).
"""

from __future__ import annotations

import socket
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import MagicMock, patch

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


@pytest.fixture
def loopback_is_public(monkeypatch):
    """These tests serve pages from a 127.0.0.1 server, which the hop refuses in production."""
    monkeypatch.setattr(hop_mod, "_public", lambda url: True)


def test_slow_drip_server_does_not_hold_detail_fetch(drip_server, monkeypatch, loopback_is_public):
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


def test_fetch_and_extract_errors_are_counted_and_logged_apart(status_server, caplog, loopback_is_public):
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


def test_model_reads_the_event_page_as_text_not_html(page_server, loopback_is_public):
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



# What resolvers answer for these names (RFC 6761 localhost, GCP metadata), without the network.
_NAMES = {"localhost.": "127.0.0.1", "foo.localhost": "127.0.0.1",
          "metadata.google.internal": "169.254.169.254", "luma.com": "93.184.216.34"}


@pytest.fixture
def resolver(monkeypatch):
    numeric = socket.getaddrinfo  # the conftest guard: numeric hosts only

    def _getaddrinfo(host, port, *args, **kwargs):
        if host in _NAMES:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (_NAMES[host], port or 80))]
        return numeric(host, port, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", _getaddrinfo)


def _listing_event(link: str) -> ExtractedEvent:
    return ExtractedEvent(
        title="t", start_local="2026-11-10T18:00", start_tz=None, end_local=None,
        venue=None, city=None, country=None, link=link,
        description="", confidence=0.9, source_url="https://aisa.to/ai-events-london",
        page_kind="listing",
    )


def test_hop_to_another_public_host(resolver):
    assert hop_mod._needs_hop(_listing_event("https://luma.com/granola-jeffrey-veen"))


@pytest.mark.parametrize("url", [
    "http://127.1/x", "http://2130706433/x", "http://0x7f000001/x", "http://localhost./x",
    "http://foo.localhost/x", "http://metadata.google.internal/computeMetadata/v1/", "http://localhost:8000/x",
    "http://10.1.2.3/x", "http://169.254.169.254/latest/meta-data", "http://[::1]/x", "http://[fc00::1]/x",
    "http://[64:ff9b::7f00:1]/x", "http://[64:ff9b::a00:1]/x", "http://[2002:7f00:1::1]/x",  # NAT64, 6to4
    "ftp://93.184.216.34/x", "file:///etc/passwd",
])
def test_hop_refuses_every_spelling_of_a_private_address(resolver, url):
    """QA on PR 151: a listing may link anywhere; the hop goes only where the host resolves to public addresses."""
    assert not hop_mod._needs_hop(_listing_event(url))


@pytest.fixture
def local_server():
    """127.0.0.1 only: /start redirects to loopback /secret, /r<n> redirects to /r<n+1> forever."""
    hits: list[str] = []

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            port = self.server.server_address[1]
            if self.path.startswith("/to-"):  # /to-<url>: redirect anywhere, e.g. ftp:// or file://
                self.send_response(302)
                self.send_header("Location", self.path[4:])
                self.end_headers()
                return
            if self.path == "/start" or self.path.startswith("/r"):
                nxt = "/secret" if self.path == "/start" else f"/r{int(self.path[2:]) + 1}"
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{port}{nxt}")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<p>secret</p>")

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server.server_address[1], hits
    server.shutdown()
    server.server_close()


def test_fetch_refuses_loopback_spellings(local_server):
    port, hits = local_server
    for host in ("127.1", "2130706433", "0x7f000001"):
        assert hop_mod._fetch_html(f"http://{host}:{port}/secret") is None, host
    assert hits == []


def test_fetch_refuses_a_redirect_to_loopback(local_server):
    port, hits = local_server
    start = f"http://127.0.0.1:{port}/start"
    with patch.object(hop_mod, "_public", lambda url: url == start, create=True):  # only the start counts as public
        assert hop_mod._fetch_html(start) is None
    assert hits == ["/start"], "the redirect target must be checked before it is opened"


def test_fetch_caps_redirects(local_server):
    port, hits = local_server
    with patch.object(hop_mod, "_public", lambda url: True, create=True):
        assert hop_mod._fetch_html(f"http://127.0.0.1:{port}/r0") is None
    assert len(hits) <= 6, f"{len(hits)} requests: redirects are not capped at 5"


@pytest.fixture
def tcp_listener():
    """A bare TCP listener on 127.0.0.1 that counts connections (stands in for an internal FTP or Redis)."""
    accepted: list[int] = []
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen()
    srv.settimeout(0.2)
    stop = threading.Event()

    def _accept():
        while not stop.is_set():
            try:
                conn, _ = srv.accept()
            except OSError:
                continue
            accepted.append(1)
            conn.close()

    threading.Thread(target=_accept, daemon=True).start()
    yield srv.getsockname()[1], accepted
    stop.set()
    srv.close()


def test_fetch_never_follows_a_redirect_off_http(local_server, tcp_listener):
    """QA round 2 on PR 151: a 302 to ftp:// skipped the address check and the opener dialled the host."""
    port, hits = local_server
    ftp_port, accepted = tcp_listener
    for target in (f"ftp://127.0.0.1:{ftp_port}/secret.html", "file:///etc/passwd"):
        start = f"http://127.0.0.1:{port}/to-{target}"
        with patch.object(hop_mod, "_public", lambda url: url == start):
            assert hop_mod._fetch_html(start) is None, target
        # even if the address check were wrong, the opener must not speak anything but http(s)
        with patch.object(hop_mod, "_public", lambda url: True):
            assert hop_mod._fetch_html(start) is None, target
    time.sleep(0.3)
    assert accepted == [], "a connection was opened to the redirect target"
