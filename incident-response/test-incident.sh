#!/usr/bin/env bash
# End-to-end test: injects a fault, drives failing searches, waits for
# Grafana's SearchRunFailures alert to fire via its real webhook, and
# confirms the responder creates an incident folder.  No synthetic alerts
# are posted — the alert path is Grafana -> webhook -> responder.
#
# Usage: ./test-incident.sh [--dry-run]
#
# --dry-run  runs the same chain but launches the responder with --dry-run
#            (collects evidence + creates worktree, skips the Claude CLI).
#            Proves: alert -> webhook -> evidence -> worktree, nothing more.
#
# Required env:
#   RESPONDER_WEBHOOK_SECRET   Bearer token shared with Grafana
#
# Optional env (defaults match make up-all):
#   HOST_PORT  GRAFANA_PORT  RESPONDER_PORT  COMPOSE_PROJECT_NAME
#   PROMETHEUS_PORT  LOKI_PORT  TEMPO_PORT  OTEL_COLLECTOR_PORT
#   OTEL_COLLECTOR_METRICS_PORT  SAIL_OBS_NETWORK
set -euo pipefail

DRY_RUN=""
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN="--dry-run"
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Ports and project — exported so docker compose picks them up
HOST_PORT="${HOST_PORT:-8000}"
GRAFANA_PORT="${GRAFANA_PORT:-3001}"
RESPONDER_PORT="${RESPONDER_PORT:-8001}"
PROMETHEUS_PORT="${PROMETHEUS_PORT:-9090}"
LOKI_PORT="${LOKI_PORT:-3100}"
TEMPO_PORT="${TEMPO_PORT:-3200}"
OTEL_COLLECTOR_PORT="${OTEL_COLLECTOR_PORT:-4318}"
OTEL_COLLECTOR_METRICS_PORT="${OTEL_COLLECTOR_METRICS_PORT:-8889}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-}"
SAIL_OBS_NETWORK="${SAIL_OBS_NETWORK:-sail-observability}"
RESPONDER_WEBHOOK_URL="http://host.docker.internal:${RESPONDER_PORT}/alerts"

export HOST_PORT GRAFANA_PORT RESPONDER_PORT PROMETHEUS_PORT LOKI_PORT
export TEMPO_PORT OTEL_COLLECTOR_PORT OTEL_COLLECTOR_METRICS_PORT
export SAIL_OBS_NETWORK RESPONDER_WEBHOOK_SECRET RESPONDER_WEBHOOK_URL

INCIDENTS_DIR="$REPO_ROOT/incident-response/incidents"
INJECT_BRANCH="test/inject-search-fault"
ORIG_BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
RESPONDER_PID=""
MARKER=$(mktemp)

# --- compose helpers --------------------------------------------------------
obs_compose() {
    if [ -n "$COMPOSE_PROJECT_NAME" ]; then
        docker compose -p "$COMPOSE_PROJECT_NAME" \
            -f "$REPO_ROOT/observability/docker-compose.yml" "$@"
    else
        docker compose -f "$REPO_ROOT/observability/docker-compose.yml" "$@"
    fi
}

app_compose() {
    if [ -n "$COMPOSE_PROJECT_NAME" ]; then
        docker compose -p "$COMPOSE_PROJECT_NAME" \
            -f "$REPO_ROOT/docker-compose.yml" \
            -f "$REPO_ROOT/docker-compose.observability.yml" "$@"
    else
        docker compose \
            -f "$REPO_ROOT/docker-compose.yml" \
            -f "$REPO_ROOT/docker-compose.observability.yml" "$@"
    fi
}

cleanup() {
    echo "--- cleanup ---"
    if [ -n "$RESPONDER_PID" ] && kill -0 "$RESPONDER_PID" 2>/dev/null; then
        kill "$RESPONDER_PID" 2>/dev/null || true
        wait "$RESPONDER_PID" 2>/dev/null || true
    fi
    git -C "$REPO_ROOT" checkout "$ORIG_BRANCH" 2>/dev/null || true
    git -C "$REPO_ROOT" branch -D "$INJECT_BRANCH" 2>/dev/null || true
    rm -f "$MARKER" 2>/dev/null || true
    # Rebuild app from clean code so the stack stays usable
    unset SEARCH_NOW_PER_HOUR 2>/dev/null || true
    app_compose up --build -d --wait 2>/dev/null || true
    echo "cleanup done"
}
trap cleanup EXIT

echo "=== test-incident.sh${DRY_RUN:+ (dry-run)} ==="

# --- verify env -------------------------------------------------------------
if [ -z "${RESPONDER_WEBHOOK_SECRET:-}" ]; then
    echo "FAIL: RESPONDER_WEBHOOK_SECRET must be set"
    exit 1
fi

# --- step 0: start the stack -----------------------------------------------
echo "--- starting stack ---"
docker network create "$SAIL_OBS_NETWORK" 2>/dev/null || true
obs_compose up -d --wait
app_compose up --build -d --wait
echo "  stack is up"

# --- step 1: start the responder -------------------------------------------
echo "--- starting responder ---"
python3 "$REPO_ROOT/incident-response/responder.py" $DRY_RUN &
RESPONDER_PID=$!
sleep 2
if ! kill -0 "$RESPONDER_PID" 2>/dev/null; then
    echo "FAIL: responder exited immediately"
    exit 1
fi
echo "  responder pid=$RESPONDER_PID"

# Verify the responder accepts auth
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "http://localhost:$RESPONDER_PORT/alerts" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $RESPONDER_WEBHOOK_SECRET" \
    -d '{"alerts":[{"status":"resolved","labels":{"alertname":"smoke"}}]}')
if [ "$HTTP_CODE" != "202" ]; then
    echo "FAIL: responder smoke-test expected 202, got $HTTP_CODE"
    exit 1
fi
echo "  smoke-test -> 202 OK"

# --- step 2: inject fault --------------------------------------------------
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
git -C "$REPO_ROOT" add "$REPO_ROOT/backend/app/adapters/fixture.py"
SKIP_HOOK_TESTS=1 git -C "$REPO_ROOT" commit -m "test: inject search-provider fault"
echo "  fault committed on $INJECT_BRANCH"

# Rebuild with fault + high rate limit so every request reaches the pipeline
echo "--- rebuilding app with fault ---"
export SEARCH_NOW_PER_HOUR=1000
app_compose up --build -d --wait

# --- step 3: drive failing searches ----------------------------------------
echo "--- driving failing searches ---"
B="http://localhost:$HOST_PORT"
T=$(curl -sf -X POST "$B/api/auth/login" \
    -H 'Content-Type: application/json' \
    -d '{"username":"demo","password":"demo"}' \
    | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')
for i in 1 2 3 4 5; do
    curl -sf -X POST "$B/api/search" -H "Authorization: Bearer $T" -o /dev/null 2>/dev/null || true
    sleep 5
done
echo "  five error requests sent"

# --- step 4: poll Grafana by rule name until it fires -----------------------
echo "--- waiting for SearchRunFailures to fire (up to 10 min) ---"
MAX_WAIT=600
ELAPSED=0
STATE=""
while [ $ELAPSED -lt $MAX_WAIT ]; do
    STATE=$(curl -sf "http://localhost:$GRAFANA_PORT/api/prometheus/grafana/api/v1/rules" 2>/dev/null \
        | python3 -c '
import sys, json
d = json.load(sys.stdin)
for g in d["data"]["groups"]:
    for r in g["rules"]:
        if r["name"] == "SearchRunFailures":
            print(r["state"])
            sys.exit(0)
print("not-found")
' 2>/dev/null || echo "error")
    printf "  %ds: SearchRunFailures=%s\n" "$ELAPSED" "$STATE"
    if [ "$STATE" = "firing" ]; then break; fi
    sleep 15
    ELAPSED=$((ELAPSED + 15))
    # keep sending errors so the condition holds across the 5m for-window
    curl -sf -X POST "$B/api/search" -H "Authorization: Bearer $T" -o /dev/null 2>/dev/null || true
done

if [ "$STATE" != "firing" ]; then
    echo "FAIL: SearchRunFailures did not fire after ${MAX_WAIT}s"
    curl -sf "http://localhost:$GRAFANA_PORT/api/prometheus/grafana/api/v1/rules" 2>/dev/null \
        | python3 -m json.tool 2>/dev/null || echo "(could not reach grafana)"
    exit 1
fi
echo "  alert is firing — Grafana's webhook will reach the responder"

# --- step 5: wait for incident folder + verdict ----------------------------
echo "--- waiting for incident folder (up to 5 min) ---"
INCIDENT_DIR=""
WAIT2=0
MAX_WAIT2=300
while [ $WAIT2 -lt $MAX_WAIT2 ]; do
    if [ -d "$INCIDENTS_DIR" ]; then
        INCIDENT_DIR=$(find "$INCIDENTS_DIR" -maxdepth 1 -name "*SearchRunFailures*" \
            -type d -newer "$MARKER" 2>/dev/null | sort | tail -1)
        if [ -n "$INCIDENT_DIR" ] && [ -f "$INCIDENT_DIR/verdict.json" ]; then
            echo "  incident complete after ${WAIT2}s"
            break
        fi
    fi
    sleep 10
    WAIT2=$((WAIT2 + 10))
    printf "  waiting... %ds\n" "$WAIT2"
done

if [ -z "$INCIDENT_DIR" ] || [ ! -f "$INCIDENT_DIR/verdict.json" ]; then
    echo "FAIL: no incident with verdict.json found after ${MAX_WAIT2}s"
    ls -la "$INCIDENTS_DIR/" 2>/dev/null || echo "(no incidents dir)"
    exit 1
fi

INCIDENT_ID="$(basename "$INCIDENT_DIR")"

# --- results ----------------------------------------------------------------
echo ""
echo "=== incident: $INCIDENT_ID ==="
echo ""
echo "--- directory contents ---"
ls -la "$INCIDENT_DIR/"
echo ""
echo "--- verdict.json ---"
cat "$INCIDENT_DIR/verdict.json"
echo ""

# Assertions
FAIL=0
for f in alert.json evidence.md agent.log verdict.json; do
    if [ ! -f "$INCIDENT_DIR/$f" ]; then
        echo "FAIL: missing $f"
        FAIL=1
    else
        echo "  $f present"
    fi
done

VERDICT=$(python3 -c "import json; print(json.load(open('$INCIDENT_DIR/verdict.json')).get('verdict',''))")
echo "  verdict: $VERDICT"

if [ -n "$DRY_RUN" ]; then
    if [ "$VERDICT" != "dry-run" ]; then
        echo "FAIL: dry-run expected verdict 'dry-run', got '$VERDICT'"
        FAIL=1
    fi
fi

if [ $FAIL -eq 0 ]; then
    echo ""
    echo "=== PASSED ==="
else
    echo ""
    echo "=== SOME ASSERTIONS FAILED ==="
    exit 1
fi
