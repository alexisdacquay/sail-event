"""Ground-truth recall measurement against a deployed Sail-event service.

For each triple in backend/tests/ground_truth/triples.json:
  1. Register a throwaway user (gt_<triple_id>)
  2. Save the criteria and thresholds
  3. Run a search, poll to completion
  4. Compare the returned events against the ground-truth list
  5. Report per-triple recall and the stage that lost each miss

Summary: recall@run (found / total) and accepted-recall (accepted / total).
Appends a dated block to work/RECALL.md.

Usage:
    python3 recall.py [--base-url URL] [--triple ID]

Default base_url: https://sail-event-dev.onrender.com
One throwaway user per triple, prefixed gt_. Dev allows many registrations
and 6 searches per user per hour, so one user per triple stays within limits.
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, date, datetime
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlparse

TRIPLES_PATH = Path(__file__).resolve().parent.parent / "tests" / "ground_truth" / "triples.json"
RECALL_MD = Path(__file__).resolve().parent.parent.parent / "work" / "RECALL.md"
PASSWORD = "Gt-recall-2026"


def call(base: str, method: str, path: str, body=None, token=None, timeout=300):
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
    except Exception as e:
        return 0, str(e)


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def _title_similarity(a: str, b: str) -> float:
    """Normalised similarity between two event titles."""
    a = a.lower().strip()
    b = b.lower().strip()
    return SequenceMatcher(None, a, b).ratio()


def _date_matches(event_dt: str | None, gt_date: str) -> bool:
    """Check if the event's dateTime starts with the ground-truth date."""
    if not event_dt:
        return False
    return event_dt[:10] == gt_date[:10]


def _url_matches(ev_url: str | None, gt_url: str) -> bool:
    """Match by host + path (ignore query/fragment)."""
    if not ev_url or not gt_url:
        return False
    a, b = urlparse(ev_url), urlparse(gt_url)
    return (a.netloc.lower() == b.netloc.lower()
            and a.path.rstrip("/") == b.path.rstrip("/"))


def _is_match(gt: dict, ev: dict) -> tuple[bool, float]:
    """Return (matched, similarity).

    A ground-truth event matches a found event when:
      - title similarity >= 0.75, OR
      - the found event's link or sourceUrl matches the GT URL (host+path), OR
      - title similarity >= 0.5 AND the date is the same day.
    """
    sim = _title_similarity(gt["title"], ev.get("title", ""))
    if sim >= 0.75:
        return True, sim
    gt_url = gt.get("url", "")
    if _url_matches(ev.get("link"), gt_url) or _url_matches(ev.get("sourceUrl"), gt_url):
        return True, max(sim, 0.75)
    if sim >= 0.5 and _date_matches(ev.get("dateTime"), gt["date"]):
        return True, sim
    return False, sim


def run_triple(triple: dict, base: str) -> dict:
    """Run one triple and return a result dict."""
    tid = triple["id"]
    user = f"gt_{tid}"
    criteria_text = triple["criteria"]
    tz = triple["timeZone"]
    gt_events = triple["events"]

    # Skip triples whose events are all in the past
    today = date.today().isoformat()
    future_events = [e for e in gt_events if e["date"] >= today]
    if not future_events:
        return {
            "id": tid,
            "criteria": criteria_text,
            "gt_count": len(gt_events),
            "gt_future": 0,
            "found": 0,
            "accepted": 0,
            "misses": [],
            "skipped": "all events in the past",
        }

    # Register (idempotent: may already exist)
    st, body = call(base, "POST", "/api/auth/login", {"username": user, "password": PASSWORD}, timeout=60)
    if st != 200:
        call(base, "POST", "/api/auth/register", {"username": user, "password": PASSWORD}, timeout=60)
        st, body = call(base, "POST", "/api/auth/login", {"username": user, "password": PASSWORD}, timeout=60)
    if st != 200:
        return {"id": tid, "error": f"login failed: {st}"}
    tok = body["token"]

    # Delete old events to get a clean measurement
    call(base, "DELETE", "/api/events", None, tok, 60)

    # Save criteria
    st, _ = call(base, "PUT", "/api/criteria", {"text": criteria_text, "timeZone": tz}, tok, 90)
    if st != 200:
        return {"id": tid, "error": f"criteria failed: {st}"}

    # Set thresholds to 90/40
    call(base, "PUT", "/api/thresholds", {"lowerThreshold": 40, "upperThreshold": 90}, tok, 60)

    # Run search — the POST response contains stageCounts directly
    t0 = time.time()
    st, run_resp = call(base, "POST", "/api/search", None, tok, 600)
    elapsed = round(time.time() - t0)
    if st not in (200, 202) or not isinstance(run_resp, dict):
        return {"id": tid, "error": f"search failed: {st}", "detail": str(run_resp)[:200]}

    # stageCounts from the POST response (top-level, not nested)
    stage_counts = run_resp.get("stageCounts") or {}

    # Also try last-run for the run_id (to fetch pages if available)
    run_id = run_resp.get("runId")

    # Get events
    st, events = call(base, "GET", "/api/events", None, tok, 60)
    if st != 200 or not isinstance(events, list):
        return {"id": tid, "error": f"events failed: {st}"}

    # If POST response had no stageCounts, try last-run (note: nested under "run")
    if not stage_counts:
        st2, last_run_resp = call(base, "GET", "/api/search/last-run", None, tok, 60)
        if st2 == 200 and isinstance(last_run_resp, dict):
            run_obj = last_run_resp.get("run") or last_run_resp
            stage_counts = run_obj.get("stageCounts") or {}

    # Try to get page list from run detail (issue 124 adds this)
    no_event_pages = _sample_no_event_pages(base, tok, run_id)

    # Match ground-truth events to returned events
    matches = []
    misses = []
    accepted_matches = 0

    for gt in future_events:
        best_match = None
        best_sim = 0.0
        for ev in events:
            matched, sim = _is_match(gt, ev)
            if matched and sim > best_sim:
                best_sim = sim
                best_match = ev

        if best_match:
            status = best_match.get("status", "unknown")
            matches.append({
                "gt_title": gt["title"],
                "found_title": best_match.get("title"),
                "status": status,
                "score": best_match.get("score"),
                "similarity": round(best_sim, 2),
            })
            if status == "accepted":
                accepted_matches += 1
        else:
            stage = _diagnose_miss(gt, stage_counts)
            misses.append({
                "gt_title": gt["title"],
                "gt_date": gt["date"],
                "lost_at": stage,
            })

    # Summary of all events the run extracted (for debugging matching)
    extracted = [
        {"title": ev.get("title", "?"), "date": (ev.get("dateTime") or "?")[:10],
         "status": ev.get("status", "?"), "score": ev.get("score")}
        for ev in events
    ]

    return {
        "id": tid,
        "criteria": criteria_text,
        "gt_count": len(gt_events),
        "gt_future": len(future_events),
        "found": len(matches),
        "accepted": accepted_matches,
        "misses": misses,
        "matches": matches,
        "extracted_events": extracted,
        "elapsed_s": elapsed,
        "stage_counts": stage_counts,
        "no_event_pages": no_event_pages,
    }


def _sample_no_event_pages(base: str, tok: str, run_id: str | None) -> list[dict] | None:
    """Try to get 5 random no-event pages from the run's page list.

    Issue 124 adds `pages` to the run row and to the last-run / runs/{id}
    endpoints. When present, sample 5 with events == 0. When absent, return None.
    """
    if not run_id:
        return None
    # Try runs/{runId} first (issue 124 adds pages there)
    st, body = call(base, "GET", f"/api/search/runs/{run_id}", None, tok, 30)
    pages = None
    if st == 200 and isinstance(body, dict):
        pages = body.get("pages")
    if not pages:
        # Try last-run
        st, body = call(base, "GET", "/api/search/last-run", None, tok, 30)
        if st == 200 and isinstance(body, dict):
            run_obj = body.get("run") or body
            pages = run_obj.get("pages")
    if not pages or not isinstance(pages, list):
        return None
    no_event = [p for p in pages if p.get("events", 0) == 0]
    if not no_event:
        return []
    return random.sample(no_event, min(5, len(no_event)))


def _diagnose_miss(gt: dict, counts: dict) -> str:
    """Best guess at which stage lost a ground-truth event, from counts only."""
    extracted = counts.get("events_extracted", 0)
    non_event = counts.get("filtered_non_event", 0)
    fetched = counts.get("results_fetched", 0)

    if extracted == 0 and fetched == 0:
        return "not_fetched"
    if extracted == 0 and fetched > 0:
        return "no_event_extracted"
    if non_event > counts.get("pages_with_events", 0):
        return "likely_no_event_extracted"
    if counts.get("filtered_place", 0) > 0:
        return "possibly_filtered_place"
    if counts.get("filtered_date", 0) > 0:
        return "possibly_filtered_date"
    if counts.get("filtered_past", 0) > 0:
        return "possibly_filtered_past"
    if counts.get("filtered_incomplete", 0) > 0:
        return "possibly_filtered_incomplete"
    return "not_in_search_results"


def main():
    parser = argparse.ArgumentParser(description="Ground-truth recall measurement")
    parser.add_argument("--base-url", default="https://sail-event-dev.onrender.com",
                        help="Base URL of the deployed service (default: dev)")
    parser.add_argument("--triple", default=None,
                        help="Run only this triple ID (e.g. berlin_jazz)")
    # Keep positional base_url for backward compat
    parser.add_argument("legacy_base", nargs="?", default=None,
                        help=argparse.SUPPRESS)
    args = parser.parse_args()

    base = (args.legacy_base or args.base_url).rstrip("/")

    triples_data = json.loads(TRIPLES_PATH.read_text())
    triples = triples_data["triples"]

    if args.triple:
        triples = [t for t in triples if t["id"] == args.triple]
        if not triples:
            print(f"Triple '{args.triple}' not found in triples.json")
            return 1

    print(f"Recall measurement against {base}")
    print(f"Triples: {len(triples)}, commit: {git_sha()}\n")

    results = []
    total_gt = 0
    total_found = 0
    total_accepted = 0

    for triple in triples:
        tid = triple["id"]
        print(f"  [{tid}] {triple['criteria'][:60]}...", end=" ", flush=True)
        result = run_triple(triple, base)
        results.append(result)

        if "error" in result:
            print(f"ERROR: {result['error']}")
            continue
        if result.get("skipped"):
            print(f"SKIPPED: {result['skipped']}")
            continue

        gt_future = result["gt_future"]
        found = result["found"]
        accepted = result["accepted"]
        total_gt += gt_future
        total_found += found
        total_accepted += accepted

        recall = f"{found}/{gt_future}"
        extracted = result.get("extracted_events", [])
        print(f"recall {recall}, accepted {accepted}, {len(extracted)} events, {result['elapsed_s']}s")
        for ev in extracted:
            print(f"    {ev['status']:>8} {ev['score'] or '?':>3}  {ev['date']}  {ev['title'][:50]}")
        for m in result.get("misses", []):
            print(f"    MISS: {m['gt_title'][:50]} ({m['lost_at']})")

    # Print sampled no-event pages
    print("\n### Sampled no-event pages")
    any_pages = False
    for r in results:
        pages = r.get("no_event_pages")
        if pages is None:
            continue
        any_pages = True
        if pages:
            for p in pages:
                print(f"  [{r['id']}] {p.get('title', '?')[:60]}  {p.get('url', '?')}")
    if not any_pages:
        print("  Page list not available on this server.")

    # Summary
    recall_pct = f"{total_found}/{total_gt}" if total_gt else "0/0"
    acc_pct = f"{total_accepted}/{total_gt}" if total_gt else "0/0"
    recall_rate = round(total_found / total_gt * 100, 1) if total_gt else 0
    acc_rate = round(total_accepted / total_gt * 100, 1) if total_gt else 0

    # Abort on errors: do not write a broken table to RECALL.md
    has_errors = any("error" in r for r in results)
    all_skipped = all(r.get("skipped") or "error" in r for r in results)
    if has_errors or all_skipped:
        print(f"\n=== Summary ===")
        print(f"  recall@run: {recall_pct} ({recall_rate}%)")
        print(f"  accepted-recall: {acc_pct} ({acc_rate}%)")
        if has_errors:
            print("\nErrors encountered; RECALL.md not updated.")
            return 1
        print("\nAll triples skipped; RECALL.md not updated.")
        return 0

    print(f"\n=== Summary ===")
    print(f"  recall@run: {recall_pct} ({recall_rate}%)")
    print(f"  accepted-recall: {acc_pct} ({acc_rate}%)")

    # Build markdown block
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    sha = git_sha()
    lines = [
        f"\n## {now} -- recall measurement -- {base} -- {sha}\n",
        f"| triple | criteria | gt | found | accepted | misses |",
        f"|--------|----------|----|-------|----------|--------|",
    ]
    for r in results:
        if "error" in r:
            lines.append(f"| {r['id']} | -- | -- | ERROR | {r['error'][:40]} | -- |")
            continue
        if r.get("skipped"):
            lines.append(f"| {r['id']} | {r.get('criteria', '')[:40]} | {r['gt_count']} | SKIP | {r['skipped']} | -- |")
            continue
        miss_text = "; ".join(f"{m['gt_title'][:30]} ({m['lost_at']})" for m in r.get("misses", []))
        lines.append(
            f"| {r['id']} | {r['criteria'][:40]} | {r['gt_future']} "
            f"| {r['found']} | {r['accepted']} | {miss_text or '--'} |"
        )
    lines.append(f"\nrecall@run: **{recall_pct} ({recall_rate}%)**  ")
    lines.append(f"accepted-recall: **{acc_pct} ({acc_rate}%)**\n")

    md_block = "\n".join(lines)
    print(f"\nWriting to {RECALL_MD}")

    # Append to RECALL.md
    if RECALL_MD.exists():
        existing = RECALL_MD.read_text()
    else:
        existing = "# Recall measurements\n"
    RECALL_MD.write_text(existing + md_block)

    return 0


if __name__ == "__main__":
    sys.exit(main())
