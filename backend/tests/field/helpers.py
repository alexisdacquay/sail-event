"""Shared HTTP helpers for the field-test runner and the battery.

Every function talks to a deployed Sail-event service through its public API.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request


def call(base: str, method: str, path: str, body=None, token=None, timeout=300):
    """One HTTP round-trip; returns (status_code, parsed_json)."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    req.add_header("content-type", "application/json")
    if token:
        req.add_header("authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"null")
        except Exception:
            return e.code, None
    except Exception as e:  # network, timeout
        return 0, str(e)


def ensure_user(base: str, username: str, password: str):
    """Login, registering first when needed.  Returns (token | None, message)."""
    st, body = call(base, "POST", "/api/auth/login",
                    {"username": username, "password": password}, timeout=60)
    if st != 200:
        rst, rbody = call(base, "POST", "/api/auth/register",
                          {"username": username, "password": password}, timeout=60)
        if rst not in (200, 201):
            return None, f"register {rst} {str(rbody)[:60]}"
        st, body = call(base, "POST", "/api/auth/login",
                        {"username": username, "password": password}, timeout=60)
    return (body["token"] if st == 200 else None), f"login {st}"


def timed_search(base: str, token: str, timeout=600):
    """POST /api/search and return (status, report_dict, elapsed_seconds)."""
    t0 = time.time()
    st, report = call(base, "POST", "/api/search", None, token, timeout)
    return st, report if isinstance(report, dict) else {"error": str(report)[:120]}, round(time.time() - t0)
