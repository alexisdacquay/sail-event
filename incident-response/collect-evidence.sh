#!/usr/bin/env bash
# Collect read-only evidence into <incident-dir>/evidence.md.
# Usage: collect-evidence.sh <incident-dir>
set -euo pipefail

dir="$1"
out="$dir/evidence.md"
prom="localhost:${PROMETHEUS_PORT:-9090}"
loki="localhost:${LOKI_PORT:-3100}"
app="localhost:${HOST_PORT:-8000}"

{
  echo "# Evidence packet"
  echo ""
  echo "Collected: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""

  echo "## Prometheus — error runs (last 10 min)"
  echo '```'
  curl -sf "http://$prom/api/v1/query?query=increase(sail_runs_total%7Boutcome%3D%22error%22%7D%5B10m%5D)" 2>&1 || echo "(query failed)"
  echo ""
  echo '```'
  echo ""

  echo "## Loki — last 20 error lines"
  echo '```'
  curl -sf "http://$loki/loki/api/v1/query_range" \
    --data-urlencode 'query={container=~".*sail-event.*"} |= "ERROR"' \
    --data-urlencode "limit=20" \
    --data-urlencode "start=$(date -u -v-10M +%s 2>/dev/null || date -u -d '10 minutes ago' +%s)000000000" \
    --data-urlencode "end=$(date -u +%s)000000000" 2>&1 || echo "(query failed)"
  echo ""
  echo '```'
  echo ""

  echo "## App health"
  echo '```'
  curl -sf "http://$app/api/health" 2>&1 || echo "(health check failed)"
  echo ""
  echo '```'
  echo ""

  echo "## Recent commits"
  echo '```'
  git log -5 --oneline
  echo '```'
  echo ""

  echo "## Deployed version"
  echo '```'
  if [ -n "${APP_VERSION:-}" ]; then
    echo "$APP_VERSION"
  else
    curl -sf "http://$app/api/health" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('version','unknown'))" 2>/dev/null || echo "unknown"
  fi
  echo '```'
} > "$out"

echo "evidence written to $out"
