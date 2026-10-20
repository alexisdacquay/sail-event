#!/usr/bin/env bash
# End-to-end test of the incident-response loop.
#
# Prerequisites:
#   - `claude` CLI installed and signed in (budget cap stays $1)
#   - Docker running
#   - The observability + app stack already up (make up-all or equivalent)
#   - The responder already listening (make responder or
#     RESPONDER_PORT=... python3 incident-response/responder.py)
#   - RESPONDER_WEBHOOK_SECRET set (same value in Grafana and the responder)
#
# All ports and the compose project name come from env with safe defaults:
#   HOST_PORT             (default 8000)
#   GRAFANA_PORT          (default 3001)
#   RESPONDER_PORT        (default 8001)
#   COMPOSE_PROJECT_NAME  (default from docker compose)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST_PORT="${HOST_PORT:-8000}"
GRAFANA_PORT="${GRAFANA_PORT:-3001}"
RESPONDER_PORT="${RESPONDER_PORT:-8001}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-}"
INCIDENTS_DIR="$REPO_ROOT/incident-response/incidents"
INJECT_BRANCH="test/inject-search-fault"
ORIG_BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"

# Compose command with optional project name
compose_cmd() {
    if [ -n "$COMPOSE_PROJECT_NAME" ]; then
        docker compose -p "$COMPOSE_PROJECT_NAME" "$@"
    else
        docker compose "$@"
    fi
}

compose_overlay() {
    if [ -n "$COMPOSE_PROJECT_NAME" ]; then
        docker compose -p "$COMPOSE_PROJECT_NAME" -f docker-compose.yml -f docker-compose.observability.yml "$@"
    else
        docker compose -f docker-compose.yml -f docker-compose.observability.yml "$@"
    fi
}

cleanup() {
    echo "--- cleanup ---"
    git -C "$REPO_ROOT" checkout "$ORIG_BRANCH" 2>/dev/null || true
    git -C "$REPO_ROOT" branch -D "$INJECT_BRANCH" 2>/dev/null || true
    # Rebuild app from clean code
    HOST_PORT="$HOST_PORT" compose_overlay -f "$REPO_ROOT/docker-compose.yml" \
        -f "$REPO_ROOT/docker-compose.observability.yml" \
        up --build -d --wait 2>/dev/null || true
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

# Step 1: inject fault on a throwaway branch
# The fault goes into the search provider so a search run fails with outcome=error.
# A git commit is required so the agent's worktree (created from HEAD by the
# responder) contains the faulted code for investigation.
echo "--- injecting fault ---"
git -C "$REPO_ROOT" checkout -b "$INJECT_BRANCH"
python3 -c "
import pathlib, sys
p = pathlib.Path(sys.argv[1])
src = p.read_text()
patched = src.replace(
    'def search(',
    'def search(self, *a, **kw):\n        raise RuntimeError(\"injected fault\")\n\n    def _search_original(',
    1)
p.write_text(patched)
" "$REPO_ROOT/backend/app/adapters/fixture.py"
git -C "$REPO_ROOT" add backend/app/adapters/fixture.py
SKIP_HOOK_TESTS=1 git -C "$REPO_ROOT" commit -m "test: inject search-provider fault"
echo "  fault committed on $INJECT_BRANCH"

# Rebuild app container with the fault
echo "--- rebuilding app with fault ---"
HOST_PORT="$HOST_PORT" compose_overlay up --build -d --wait

# Step 2: trigger errors — need an auth token first
echo "--- triggering search errors ---"
B="http://localhost:$HOST_PORT"
T=$(curl -sf -X POST "$B/api/auth/login" \
    -H 'Content-Type: application/json' \
    -d '{"username":"demo","password":"demo"}' \
    | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')
curl -sf -X POST "$B/api/search" -H "Authorization: Bearer $T" -o /dev/null 2>/dev/null || true
sleep 5
curl -sf -X POST "$B/api/search" -H "Authorization: Bearer $T" -o /dev/null 2>/dev/null || true
sleep 5
curl -sf -X POST "$B/api/search" -H "Authorization: Bearer $T" -o /dev/null 2>/dev/null || true
echo "  three error requests sent"

# Step 3: wait for the alert to fire and the agent to finish
# SearchRunFailures: for=5m + 60s eval interval
echo "--- waiting for alert to fire (up to 10 minutes) ---"
MAX_WAIT=600
ELAPSED=0
INCIDENT_DIR=""

while [ $ELAPSED -lt $MAX_WAIT ]; do
    if [ -d "$INCIDENTS_DIR" ]; then
        INCIDENT_DIR=$(find "$INCIDENTS_DIR" -maxdepth 1 -name "*SearchRunFailures*" -type d 2>/dev/null \
            | sort | tail -1)
        if [ -n "$INCIDENT_DIR" ] && [ -f "$INCIDENT_DIR/verdict.json" ]; then
            echo "  incident complete after ${ELAPSED}s"
            break
        fi
    fi
    sleep 15
    ELAPSED=$((ELAPSED + 15))
    printf "  waiting... %ds" "$ELAPSED"
    if [ $((ELAPSED % 60)) -eq 0 ]; then
        STATE=$(curl -sf "http://localhost:$GRAFANA_PORT/api/alertmanager/grafana/api/v2/alerts" 2>/dev/null \
            | python3 -c "
import sys,json
a=json.load(sys.stdin)
print(len(a),'alert(s)',', '.join(
    x.get('labels',{}).get('alertname','?')+':'+x.get('status',{}).get('state','?')
    for x in a))" 2>/dev/null || echo "?")
        printf " [alerts: %s]" "$STATE"
    fi
    echo ""
done

if [ -z "$INCIDENT_DIR" ] || [ ! -f "$INCIDENT_DIR/verdict.json" ]; then
    echo "FAIL: no incident with verdict.json found after ${MAX_WAIT}s"
    echo "Alert state:"
    curl -sf "http://localhost:$GRAFANA_PORT/api/alertmanager/grafana/api/v2/alerts" 2>/dev/null \
        | python3 -m json.tool 2>/dev/null || echo "(could not reach grafana)"
    ls -la "$INCIDENTS_DIR/" 2>/dev/null || echo "(no incidents dir)"
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
    else
        echo "  $f present"
    fi
done

VERDICT=$(python3 -c "import json; v=json.load(open('$INCIDENT_DIR/verdict.json')); print(v.get('verdict',''))")
COMMIT=$(python3 -c "import json; v=json.load(open('$INCIDENT_DIR/verdict.json')); print(v.get('commit',''))")

echo "  verdict: $VERDICT"
if [ "$VERDICT" != "fix" ]; then
    echo "WARN: verdict is '$VERDICT', expected 'fix'"
fi
if [ -z "$COMMIT" ] && [ "$VERDICT" = "fix" ]; then
    echo "FAIL: commit is empty for a fix verdict"
    FAIL=1
fi

# Check incident branch exists
INCIDENT_BRANCH=$(git -C "$REPO_ROOT" branch --list "incident/$INCIDENT_ID" | sed 's/^[* ]*//')
if [ -z "$INCIDENT_BRANCH" ] && [ "$VERDICT" = "fix" ]; then
    echo "WARN: no incident/$INCIDENT_ID branch"
else
    echo "  incident branch: ${INCIDENT_BRANCH:-none}"
fi

echo ""
echo "--- incident directory contents ---"
ls -la "$INCIDENT_DIR/"
echo ""
echo "--- verdict.json ---"
cat "$INCIDENT_DIR/verdict.json"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo "=== TEST PASSED ==="
else
    echo ""
    echo "=== SOME ASSERTIONS FAILED ==="
    exit 1
fi
