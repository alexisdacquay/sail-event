"""Field test, tier 1: run every persona in personas.yaml against a deployed Sail-event, check the invariants.

usage: SSL_CERT_FILE=$(uv run --project backend python -m certifi) \
       uv run --project backend python backend/tests/field/battery.py https://sail-event.onrender.com [id ...]
(SSL_CERT_FILE is for macOS, where urllib has no root certificates; "register 0" with a certificate error means it is missing.)

One fixed throwaway user per persona (field_<id>), reused across runs. Registration is capped per IP
(REGISTER_RATE_LIMIT_PER_HOUR, default 5): on a fresh host the first run registers five and reports the
rest as "register 429"; run again later or raise the cap for the window. Each persona costs one search
(two with a `then` criteria). Output: a Markdown table and the findings by invariant, for work/FIELD-TESTS.md.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from invariants import KEPT, check_events, check_isolation, check_run, check_stale  # noqa: E402

PASSWORD = "Field-pass-2026"
BASE = sys.argv[1].rstrip("/")
ONLY = set(sys.argv[2:])


def call(method, path, body=None, token=None, timeout=300):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
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


def ensure_user(p):
    """Login, registering first when needed. Sequential so the list order decides who registers."""
    user = f"field_{p['id']}"
    st, body = call("POST", "/api/auth/login", {"username": user, "password": PASSWORD}, timeout=60)
    if st != 200:
        rst, rbody = call("POST", "/api/auth/register", {"username": user, "password": PASSWORD}, timeout=60)
        if rst not in (200, 201):
            return None, f"register {rst} {str(rbody)[:60]}"
        st, body = call("POST", "/api/auth/login", {"username": user, "password": PASSWORD}, timeout=60)
    return (body["token"] if st == 200 else None), f"login {st}"


def search(tok):
    t0 = time.time()
    st, report = call("POST", "/api/search", None, tok, 600)
    return st, report if isinstance(report, dict) else {"error": str(report)[:120]}, round(time.time() - t0)


def flow(report):
    c = report.get("stageCounts") or {}
    return (f"{c.get('results_fetched', '-')} res → {c.get('events_extracted', '-')} ext → "
            f"{c.get('events_judged', 0)} judged → {c.get('accepted', 0)} acc / {c.get('queued', 0)} queued / {c.get('rejected', 0)} rej")


def run_persona(p, tok):
    findings, now = [], datetime.now(UTC)
    st, _ = call("PUT", "/api/criteria", {"text": p["text"], "timeZone": p["tz"]}, tok, 90)
    if st != 200:
        return f"criteria {st}", "", 0, findings, set()
    call("PUT", "/api/thresholds", {"lowerThreshold": 40, "upperThreshold": 90}, tok, 60)
    _, before = call("GET", "/api/events", None, tok, 60)
    st, report, secs = search(tok)
    if st != 200:
        return f"search {st}", (report.get("detail") or report.get("error") or "")[:60], secs, findings, set()
    _, events = call("GET", "/api/events", None, tok, 60)
    events = events or []
    findings += check_run(report, len(before or []), len(events))
    findings += check_events(events, p, now)

    queued = [e for e in events if e["status"] == "queued"]  # I9: reject, then take it back
    if queued:
        eid = queued[0]["id"]
        call("POST", f"/api/events/{eid}/decision", {"decision": "rejected"}, tok, 60)
        st, body = call("POST", f"/api/events/{eid}/decision", {"decision": "accepted"}, tok, 60)
        if st != 200:
            findings.append(("I9", f"a rejected event cannot be taken back: {st} {(body or {}).get('detail', '')}"))

    if p.get("then"):  # I8: change the criteria, search again, look for untouched reasons
        before_reasons = {e["id"]: e.get("scoreReason") for e in events if e["status"] in KEPT and e.get("decidedBy") != "user"}
        call("PUT", "/api/criteria", {"text": p["then"], "timeZone": p["tz"]}, tok, 90)
        st, report2, secs2 = search(tok)
        secs += secs2
        if st == 200:
            _, after = call("GET", "/api/events", None, tok, 60)
            findings += check_run(report2, len(events), len(after or []))
            findings += check_stale(before_reasons, after or [])
            findings += check_events(after or [], {**p, "country": None}, now)
        else:
            findings.append(("I10", f"second search {st}"))
    kept = sum(e["status"] in KEPT for e in events)
    status = report.get("stoppedAtStage") or "ok"
    line = f"{flow(report)} · kept {kept}"
    if p.get("want"):  # tier 3 recall: real events known to exist, found in any status or not at all
        titles = " | ".join((e.get("title") or "").lower() for e in events)
        found = sum(w["title"].lower() in titles for w in p["want"])
        line += f" · recall {found}/{len(p['want'])}"
    return status, line, secs, findings, {e["id"] for e in events}


def main():
    personas = yaml.safe_load((Path(__file__).parent / "personas.yaml").read_text())
    if ONLY:
        personas = [p for p in personas if p["id"] in ONLY]
    rows, tokens = [], {}
    for p in personas:
        tok, msg = ensure_user(p)
        if tok:
            tokens[p["id"]] = tok
        else:
            rows.append((p["id"], msg, "", 0, [], set()))

    def one(p):
        return (p["id"], *run_persona(p, tokens[p["id"]]))

    with ThreadPoolExecutor(max_workers=10) as ex:
        rows += list(ex.map(one, [p for p in personas if p["id"] in tokens]))

    ids_by_user = {r[0]: r[5] for r in rows}
    iso = check_isolation(ids_by_user)
    print(f"## {datetime.now(UTC):%Y-%m-%d %H:%M} tier 1 battery — {BASE} — {len(rows)} personas\n")
    print("| persona | status | flow | s | findings |")
    print("|---|---|---|---|---|")
    by_inv: dict[str, list[tuple[str, str]]] = {}
    for pid, status, fl, secs, findings, _ in rows:
        counts: dict[str, int] = {}
        for inv, ev in findings:
            counts[inv] = counts.get(inv, 0) + 1
            by_inv.setdefault(inv, []).append((pid, ev))
        print(f"| {pid} | {status} | {fl} | {secs} | {' '.join(f'{k}:{v}' for k, v in sorted(counts.items())) or '-'} |")
    for inv, ev in iso:
        by_inv.setdefault(inv, []).append(("*", ev))
    print("\n### Findings by invariant\n")
    for inv in sorted(by_inv):
        items = by_inv[inv]
        who = sorted({pid for pid, _ in items})
        print(f"- **{inv}** ×{len(items)} ({', '.join(who)})")
        for pid, ev in items[:4]:
            print(f"  - {pid}: {ev}")


if __name__ == "__main__":
    main()
