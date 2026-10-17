#!/usr/bin/env bash
# End-to-end test of the incident-response loop.
# Assumes: app on HOST_PORT=8010, observability on GRAFANA_PORT=3001,
#          responder on port 8001.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST_PORT="${HOST_PORT:-8010}"
GRAFANA_PORT="${GRAFANA_PORT:-3001}"
RESPONDER_PORT="${RESPONDER_PORT:-8001}"
INJECT_BRANCH="test/inject-scorer-fault"

cleanup() {
    echo "--- cleanup ---"
    cd "$REPO_ROOT"
    git checkout main 2>/dev/null || true
    git branch -D "$INJECT_BRANCH" 2>/dev/null || true
    # Remove any leftover worktrees from this test
    git worktree list --porcelain | grep -A0 "^worktree.*sail-incident" | sed 's/^worktree //' | while read -r wt; do
        git worktree remove "$wt" --force 2>/dev/null || true
    done
    # Rebuild app from main
    OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318 HOST_PORT="$HOST_PORT" \
        docker compose up --build -d --wait 2>/dev/null || true
    echo "cleanup done"
}
trap cleanup EXIT

echo "=== test-incident.sh ==="

# Step 0: verify responder auth (requires RESPONDER_WEBHOOK_SECRET)
echo "--- verifying responder auth ---"
if [ -z "${RESPONDER_WEBHOOK_SECRET:-}" ]; then
    echo "FAIL: RESPONDER_WEBHOOK_SECRET must be set"
    exit 1
fi

SMOKE_PAYLOAD='{"alerts":[{"status":"resolved","labels":{"alertname":"smoke"}}]}'

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "http://localhost:$RESPONDER_PORT/alerts" \
    -H "Content-Type: application/json" \
    -d "$SMOKE_PAYLOAD")
if [ "$HTTP_CODE" != "401" ]; then
    echo "FAIL: expected 401 without auth header, got $HTTP_CODE"
    exit 1
fi
echo "  no-auth -> 401 OK"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "http://localhost:$RESPONDER_PORT/alerts" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $RESPONDER_WEBHOOK_SECRET" \
    -d "$SMOKE_PAYLOAD")
if [ "$HTTP_CODE" != "202" ]; then
    echo "FAIL: expected 202 with auth header, got $HTTP_CODE"
    exit 1
fi
echo "  auth -> 202 OK"

# Step 1: inject fault on a temporary branch
echo "--- injecting fault ---"
cd "$REPO_ROOT"
git checkout -b "$INJECT_BRANCH"
sed -i.bak '1s/^/    def score(self, event, criteria):\n        raise RuntimeError("injected: scorer fault")\n/' \
    /dev/null  # no-op; use python for portable patching
python3 -c "
import pathlib
p = pathlib.Path('backend/app/adapters/fake.py')
src = p.read_text()
# Insert raise as the first line of FakeScorer.score
patched = src.replace(
    'def score(self, event: RawEvent, criteria: str) -> tuple[int, str]:',
    'def score(self, event: RawEvent, criteria: str) -> tuple[int, str]:\n        raise RuntimeError(\"injected: scorer fault\")',
    1)
p.write_text(patched)
"
git add backend/app/adapters/fake.py
git commit -m "test: inject scorer fault"

# Rebuild app container from injected branch
echo "--- rebuilding app with fault ---"
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318 HOST_PORT="$HOST_PORT" \
    docker compose up --build -d --wait

# Switch back to main so the responder's worktree is based on clean code
git checkout main

# Step 2: trigger errors
echo "--- triggering search errors ---"
curl -sf -X POST "http://localhost:$HOST_PORT/api/search" -o /dev/null || true
sleep 5
curl -sf -X POST "http://localhost:$HOST_PORT/api/search" -o /dev/null || true
echo "two error requests sent"

# Step 3: wait for the alert to fire and the agent to finish
# SearchRunFailures has a 5-minute `for` window + 60s eval interval
echo "--- waiting for alert to fire (up to 8 minutes) ---"
MAX_WAIT=480
ELAPSED=0
INCIDENT_DIR=""

while [ $ELAPSED -lt $MAX_WAIT ]; do
    # Check if any incident directory appeared
    if [ -d "$REPO_ROOT/incidents" ]; then
        INCIDENT_DIR=$(find "$REPO_ROOT/incidents" -maxdepth 1 -name "*SearchRunFailures*" -type d | head -1)
        if [ -n "$INCIDENT_DIR" ] && [ -f "$INCIDENT_DIR/verdict.json" ]; then
            echo "incident complete after ${ELAPSED}s"
            break
        fi
    fi
    sleep 15
    ELAPSED=$((ELAPSED + 15))
    echo "  waiting... ${ELAPSED}s"
done

if [ -z "$INCIDENT_DIR" ] || [ ! -f "$INCIDENT_DIR/verdict.json" ]; then
    echo "FAIL: no incident with verdict.json found after ${MAX_WAIT}s"
    # Debug: check alert state
    echo "Alert state:"
    curl -sf "http://localhost:$GRAFANA_PORT/api/alertmanager/grafana/api/v2/alerts" 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "(could not reach grafana)"
    ls -la "$REPO_ROOT/incidents/" 2>/dev/null || echo "(no incidents dir)"
    exit 1
fi

INCIDENT_ID="$(basename "$INCIDENT_DIR")"
echo "incident id: $INCIDENT_ID"

# Step 4: assertions
echo "--- assertions ---"
FAIL=0

for f in alert.json evidence.md agent.log verdict.json; do
    if [ ! -f "$INCIDENT_DIR/$f" ]; then
        echo "FAIL: missing $f"
        FAIL=1
    fi
done

# verdict.json has verdict: "fix" and non-empty commit
VERDICT=$(python3 -c "import json; v=json.load(open('$INCIDENT_DIR/verdict.json')); print(v.get('verdict',''))")
COMMIT=$(python3 -c "import json; v=json.load(open('$INCIDENT_DIR/verdict.json')); print(v.get('commit',''))")

if [ "$VERDICT" != "fix" ]; then
    echo "FAIL: verdict is '$VERDICT', expected 'fix'"
    FAIL=1
fi
if [ -z "$COMMIT" ]; then
    echo "FAIL: commit is empty"
    FAIL=1
fi

# Check incident branch exists
INCIDENT_BRANCH=$(git branch --list "incident/*" | head -1 | sed 's/^[* ]*//')
if [ -z "$INCIDENT_BRANCH" ]; then
    echo "FAIL: no incident/* branch found"
    FAIL=1
else
    echo "incident branch: $INCIDENT_BRANCH"

    # Run verify-recovery on the incident branch
    echo "--- verify-recovery ---"
    bash "$REPO_ROOT/incident-response/runbooks/verify-recovery.sh" "$INCIDENT_BRANCH" || FAIL=1

    git checkout main
fi

# Print results
echo ""
echo "--- incident directory contents ---"
ls -la "$INCIDENT_DIR/"

echo ""
echo "--- verdict.json ---"
cat "$INCIDENT_DIR/verdict.json"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo "=== ALL ASSERTIONS PASSED ==="
else
    echo ""
    echo "=== SOME ASSERTIONS FAILED ==="
    exit 1
fi
