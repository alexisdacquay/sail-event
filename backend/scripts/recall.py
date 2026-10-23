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
    python3 recall.py [base_url]

Default base_url: https://sail-event-dev.onrender.com
One throwaway user per triple, prefixed gt_. Dev allows many registrations
and 6 searches per user per hour, so one user per triple stays within limits.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, date, datetime
from difflib import SequenceMatcher
from pathlib import Path

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://sail-event-dev.onrender.com").rstrip("/")
TRIPLES_PATH = Path(__file__).resolve().parent.parent / "tests" / "ground_truth" / "triples.json"
RECALL_MD = Path(__file__).resolve().parent.parent.parent / "work" / "RECALL.md"
PASSWORD = "Gt-recall-2026"


def call(method: str, path: str, body=None, token=None, timeout=300):
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


def run_triple(triple: dict) -> dict:
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
    st, body = call("POST", "/api/auth/login", {"username": user, "password": PASSWORD}, timeout=60)
    if st != 200:
        call("POST", "/api/auth/register", {"username": user, "password": PASSWORD}, timeout=60)
        st, body = call("POST", "/api/auth/login", {"username": user, "password": PASSWORD}, timeout=60)
    if st != 200:
        return {"id": tid, "error": f"login failed: {st}"}
    tok = body["token"]

    # Delete old events to get a clean measurement
    call("DELETE", "/api/events", None, tok, 60)

    # Save criteria
    st, _ = call("PUT", "/api/criteria", {"text": criteria_text, "timeZone": tz}, tok, 90)
    if st != 200:
        return {"id": tid, "error": f"criteria failed: {st}"}

    # Set thresholds to 90/40
    call("PUT", "/api/thresholds", {"lowerThreshold": 40, "upperThreshold": 90}, tok, 60)

    # Run search
    t0 = time.time()
    st, run = call("POST", "/api/search", None, tok, 600)
    elapsed = round(time.time() - t0)
    if st not in (200, 202) or not isinstance(run, dict):
        return {"id": tid, "error": f"search failed: {st}", "detail": str(run)[:200]}

    # Get events
    st, events = call("GET", "/api/events", None, tok, 60)
    if st != 200 or not isinstance(events, list):
        return {"id": tid, "error": f"events failed: {st}"}

    # Get last run for stage counts
    st, last_run = call("GET", "/api/search/last-run", None, tok, 60)
    stage_counts = (last_run or {}).get("stageCounts", {}) if isinstance(last_run, dict) else {}

    # Match ground-truth events to returned events
    matches = []
    misses = []
    accepted_matches = 0

    for gt in future_events:
        best_match = None
        best_sim = 0.0
        for ev in events:
            # Match by title similarity and date
            sim = _title_similarity(gt["title"], ev.get("title", ""))
            if sim > best_sim and sim >= 0.4:
                if _date_matches(ev.get("dateTime"), gt["date"]):
                    best_sim = sim
                    best_match = ev
                elif sim >= 0.7:
                    # High title match even without exact date
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
            # Determine which stage lost it
            stage = _diagnose_miss(gt, events, stage_counts)
            misses.append({
                "gt_title": gt["title"],
                "gt_date": gt["date"],
                "lost_at": stage,
            })

    return {
        "id": tid,
        "criteria": criteria_text,
        "gt_count": len(gt_events),
        "gt_future": len(future_events),
        "found": len(matches),
        "accepted": accepted_matches,
        "misses": misses,
        "matches": matches,
        "elapsed_s": elapsed,
        "stage_counts": stage_counts,
    }


def _diagnose_miss(gt: dict, events: list, counts: dict) -> str:
    """Best guess at which stage lost a ground-truth event."""
    # If there are no events at all and filtered_non_event is high,
    # the pages were likely not read
    if counts.get("filtered_non_event", 0) > counts.get("pages_with_events", 0):
        return "not_fetched_or_no_event_extracted"
    if counts.get("events_extracted", 0) == 0:
        return "not_fetched"
    # Check if any event with a similar title was filtered
    for ev in events:
        sim = _title_similarity(gt["title"], ev.get("title", ""))
        if sim >= 0.4:
            status = ev.get("status", "")
            if status == "rejected":
                return "judged_out"
    # Check filters
    if counts.get("filtered_place", 0) > 0:
        return "possibly_filtered_place"
    if counts.get("filtered_date", 0) > 0:
        return "possibly_filtered_date"
    if counts.get("filtered_past", 0) > 0:
        return "possibly_filtered_past"
    return "not_fetched_or_no_event_extracted"


def main():
    triples_data = json.loads(TRIPLES_PATH.read_text())
    triples = triples_data["triples"]

    print(f"Recall measurement against {BASE}")
    print(f"Triples: {len(triples)}, commit: {git_sha()}\n")

    results = []
    total_gt = 0
    total_found = 0
    total_accepted = 0

    for triple in triples:
        tid = triple["id"]
        print(f"  [{tid}] {triple['criteria'][:60]}...", end=" ", flush=True)
        result = run_triple(triple)
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
        print(f"recall {recall}, accepted {accepted}, {result['elapsed_s']}s")
        for m in result.get("misses", []):
            print(f"    MISS: {m['gt_title'][:50]} ({m['lost_at']})")

    # Summary
    recall_pct = f"{total_found}/{total_gt}" if total_gt else "0/0"
    acc_pct = f"{total_accepted}/{total_gt}" if total_gt else "0/0"
    recall_rate = round(total_found / total_gt * 100, 1) if total_gt else 0
    acc_rate = round(total_accepted / total_gt * 100, 1) if total_gt else 0

    print(f"\n=== Summary ===")
    print(f"  recall@run: {recall_pct} ({recall_rate}%)")
    print(f"  accepted-recall: {acc_pct} ({acc_rate}%)")

    # Build markdown block
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    sha = git_sha()
    lines = [
        f"\n## {now} — recall measurement — {BASE} — {sha}\n",
        f"| triple | criteria | gt | found | accepted | misses |",
        f"|--------|----------|----|-------|----------|--------|",
    ]
    for r in results:
        if "error" in r:
            lines.append(f"| {r['id']} | — | — | ERROR | {r['error'][:40]} | — |")
            continue
        if r.get("skipped"):
            lines.append(f"| {r['id']} | {r.get('criteria', '')[:40]} | {r['gt_count']} | SKIP | {r['skipped']} | — |")
            continue
        miss_text = "; ".join(f"{m['gt_title'][:30]} ({m['lost_at']})" for m in r.get("misses", []))
        lines.append(
            f"| {r['id']} | {r['criteria'][:40]} | {r['gt_future']} "
            f"| {r['found']} | {r['accepted']} | {miss_text or '—'} |"
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
