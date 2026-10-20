# Observability

`make up-all` starts both the app (with `docker-compose.observability.yml` overlay) and the observability stack; `make observability-up` starts the stack alone (collector, Prometheus, Loki, Tempo, Grafana).
`make observability-down` tears it down.

Grafana is at `http://localhost:3001` (or `$GRAFANA_PORT`). Every host port has an override: `GRAFANA_PORT`, `PROMETHEUS_PORT`, `LOKI_PORT`, `TEMPO_PORT`, `OTEL_COLLECTOR_PORT` (default 4318).

## Alerting

Two provisioned alert rules evaluate every minute against the Prometheus datasource.

| Rule | Expression | `for` | Fires when |
|------|-----------|-------|------------|
| **SearchRunFailures** | `increase(sail_runs_total{outcome="error"}[10m]) >= 2` | 5 m | Two or more search runs failed in a 10-minute window and the condition held for 5 minutes |
| **SearchRunsSilent** | `increase(sail_runs_total[2h]) == 0` | 10 m | No run completed in 2 hours (`noDataState: OK` — a fresh stack with no metrics stays Normal) |

Alerts with `severity=critical` route to the **responder-webhook** contact point, which POSTs to `$RESPONDER_WEBHOOK_URL` (default `http://host.docker.internal:8001/alerts`).

### Testing with a throwaway listener

```bash
# terminal 1 — tiny POST listener
python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, sys

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        print(json.dumps(json.loads(body), indent=2), flush=True)
        self.send_response(200)
        self.end_headers()

HTTPServer(('', 8001), H).serve_forever()
"

# terminal 2 — trigger failures
SEARCH_PROVIDER=unknown HOST_PORT=8010 docker compose up --build -d --wait
curl -s -X POST http://localhost:8010/api/search | head
# wait ~1 min, send a second request
curl -s -X POST http://localhost:8010/api/search | head
# wait 5-6 minutes, then check
curl -s http://localhost:3001/api/alertmanager/grafana/api/v2/alerts | python3 -m json.tool
```

### Linux caveat

On native Linux `host.docker.internal` does not resolve by default.
The compose file adds `extra_hosts: ["host.docker.internal:host-gateway"]` to the
Grafana service for compatibility.
