# Incident Response

Automated on-call responder: receives Grafana alert webhooks, collects
evidence, and launches a headless Claude Code agent to investigate.

## Required environment variables

| Variable | Required | Description |
|---|---|---|
| `RESPONDER_WEBHOOK_SECRET` | **yes** | Bearer token shared with Grafana; the server refuses to start without it |
| `ANTHROPIC_API_KEY` | for real runs | Passed to the agent subprocess |
| `RESPONDER_PORT` | no | Listen port (default `8001`) |
| `CLAUDE_BIN` | no | Path to the Claude CLI binary (default `claude`) |
| `SKIP_HOOK_TESTS` | no | Set to `1` in the agent env so commits in incident worktrees skip the pre-commit test gate |

## Start

```sh
export RESPONDER_WEBHOOK_SECRET=<value>
make responder
```

## Recorded incidents

**2026-10-17 (`20261017-052050-SearchRunFailures`)** -- the complete run.
Alert fired from Grafana after an injected fault in the search provider.
The agent read the evidence, found the `raise RuntimeError`, fixed it on
branch `incident/20261017-052050-SearchRunFailures`, and committed
`dae24e9`.  All five files are present: `alert.json`, `evidence.md`,
`agent.log`, `verdict.json`, `fix.diff`.

## Reproduce the full loop (test-incident.sh)

Prerequisites:

- `claude` CLI installed and signed in (`claude --version` to verify)
- Run from a normal terminal, not from inside a Claude Code session
  (the session exports `ANTHROPIC_*` and `CLAUDE_*` vars that the
  allowlist strips; the CLI must use its own OAuth store)
- No VPN that blocks `api.anthropic.com`
- Docker running

The script starts the full stack (observability + app) and the responder
itself, injects a fault into the search provider (`fixture.py`), drives
failing searches, and waits for Grafana's SearchRunFailures alert to fire.
Grafana's own webhook delivers the alert to the responder.  One terminal
is enough:

```sh
RESPONDER_WEBHOOK_SECRET=any-string incident-response/test-incident.sh
```

All ports come from env with safe defaults.  Override to avoid clashes:

```sh
COMPOSE_PROJECT_NAME=exam3 HOST_PORT=8070 GRAFANA_PORT=3071 \
  PROMETHEUS_PORT=9071 LOKI_PORT=3171 TEMPO_PORT=3271 \
  OTEL_COLLECTOR_PORT=4371 OTEL_COLLECTOR_METRICS_PORT=8871 \
  SAIL_OBS_NETWORK=exam3-obs RESPONDER_PORT=8071 \
  RESPONDER_WEBHOOK_SECRET=any-string \
  incident-response/test-incident.sh
```

### `--dry-run` mode

Add `--dry-run` to prove the alert-to-evidence chain without the
Anthropic API:

```sh
RESPONDER_WEBHOOK_SECRET=any-string incident-response/test-incident.sh --dry-run
```

Dry-run proves: alert &rarr; webhook &rarr; evidence collection &rarr;
worktree creation, and nothing more.  The verdict is `"dry-run"`, the
agent is never launched, and no fix is attempted.

### Expected output

Incidents are written to `incident-response/incidents/<timestamp>-<alertname>/`.
Each folder contains:

| File | Contents |
|------|----------|
| `alert.json` | Raw Grafana alert payload |
| `evidence.md` | Prometheus metrics, Loki error logs, app health, recent commits |
| `agent.log` | Claude CLI output (or `"dry-run: agent not launched"` in dry-run) |
| `verdict.json` | `{"verdict": "fix"|"dry-run"|...}` with summary, files, commit |
