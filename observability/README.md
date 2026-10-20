# Observability

`make up-all` starts both the app (with `docker-compose.observability.yml` overlay) and the observability stack; `make observability-up` starts the stack alone (collector, Prometheus, Loki, Tempo, Grafana).
`make observability-down` tears it down.

Grafana is at `http://localhost:3001` (or `$GRAFANA_PORT`). Every host port has an override: `GRAFANA_PORT`, `PROMETHEUS_PORT`, `LOKI_PORT`, `TEMPO_PORT`, `OTEL_COLLECTOR_PORT` (default 4318), `OTEL_COLLECTOR_METRICS_PORT` (default 8889).

## Alerting

Two provisioned alert rules evaluate every minute against the Prometheus datasource.

| Rule | Expression | `for` | Fires when |
|------|-----------|-------|------------|
| **SearchRunFailures** | `increase(sail_runs_total{outcome="error"}[10m]) >= 2` | 5 m | Two or more search runs failed in a 10-minute window and the condition held for 5 minutes |
| **SearchRunsSilent** | `increase(sail_runs_total[2h]) == 0` | 10 m | No run completed in 2 hours (`noDataState: OK` — a fresh stack with no metrics stays Normal) |

Alerts with `severity=critical` route to the **responder-webhook** contact point, which POSTs to `$RESPONDER_WEBHOOK_URL` (default `http://host.docker.internal:8001/alerts`).

### Fire the alert locally (copy-paste block)

Everything runs in one terminal. The overlay file connects the app to the
collector network so metrics reach Prometheus.

```bash
# 1. Start the observability stack + the app with an invalid search provider
make up-all
# Override just the app with SEARCH_PROVIDER=unknown so every search errors
SEARCH_PROVIDER=unknown docker compose -f docker-compose.yml -f docker-compose.observability.yml up --build -d --wait

# 2. Get a token (demo user is seeded automatically)
B=http://localhost:${HOST_PORT:-8000}
T=$(curl -s -X POST $B/api/auth/login -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

# 3. Send failing searches every 30 s (the rule's `for: 5m` needs sustained errors)
for i in $(seq 1 14); do
  curl -s -X POST $B/api/search -H "Authorization: Bearer $T" | head -1
  sleep 30
done

# 5. Check the alert
curl -s http://localhost:${GRAFANA_PORT:-3001}/api/alertmanager/grafana/api/v2/alerts | python3 -m json.tool
```

Expected output (abridged): an array with one object whose
`labels.alertname` is `SearchRunFailures` and `status.state` is `active`.

```json
[
  {
    "labels": {
      "alertname": "SearchRunFailures",
      "severity": "critical",
      "service": "sail-event-backend"
    },
    "status": { "state": "active" }
  }
]
```

## Trace-id correlation proof

After at least one successful search run (`SEARCH_PROVIDER=fixture`), the
trace id appears in both Loki (structured log) and Tempo (distributed trace).

```bash
# 1. Find a trace id in the logs (Loki)
#    trace_id is a stream label set by the OTel log exporter
curl -sG http://localhost:${LOKI_PORT:-3100}/loki/api/v1/query_range \
  --data-urlencode 'query={service_name="sail-event-backend"} |= "search run completed"' \
  --data-urlencode 'limit=1' | python3 -c '
import sys, json
r = json.load(sys.stdin)
stream = r["data"]["result"][0]["stream"]
print("trace_id:", stream["trace_id"])
'

# 2. Fetch that trace from Tempo
TRACE_ID=<paste the trace_id from step 1>
curl -s http://localhost:${TEMPO_PORT:-3200}/api/traces/$TRACE_ID | python3 -c '
import sys, json; d = json.load(sys.stdin)
for b in d["batches"]:
  for s in b["scopeSpans"]:
    for sp in s["spans"]:
      print(sp["name"])
'
```

Expected: the Loki query returns a log line with a non-zero `trace_id`, and
the Tempo query returns the same trace with spans including `search_run`,
`search`, `extract`, `filter`, `persist`, `judge`, `triage`.

## `otel-collector` hostname collision

Both compose files (`observability/docker-compose.yml` and the app overlay)
place services on the shared `sail-observability` network. The collector's
hostname is `otel-collector` in that network. If you run a second
observability stack on the same Docker network (e.g. for another project),
the hostname will collide. Override with `SAIL_OBS_NETWORK` to use a
separate network per project:

```bash
SAIL_OBS_NETWORK=my-project-obs docker network create my-project-obs
SAIL_OBS_NETWORK=my-project-obs make up-all
```

### Linux caveat

On native Linux `host.docker.internal` does not resolve by default.
The compose file adds `extra_hosts: ["host.docker.internal:host-gateway"]` to the
Grafana service for compatibility.
