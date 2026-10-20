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

**2026-10-20 (`20261020-231500-SearchRunFailures`)** -- proves the chain
up to the agent launch on the current code.  The alert fired, the
responder created the incident directory, collected evidence, created a
git worktree, and launched the headless Claude CLI.  The CLI could not
reach the Anthropic API from this host at that time (ENOTFOUND); the real
CLI stderr is in `agent.log` and the verdict records the error.

## Reproduce the full loop (test-incident.sh)

Prerequisites:

- `claude` CLI installed and signed in (`claude --version` to verify)
- Run from a normal terminal, not from inside a Claude Code session
  (the session exports `ANTHROPIC_*` and `CLAUDE_*` vars that the
  allowlist strips; the CLI must use its own OAuth store)
- No VPN that blocks `api.anthropic.com`
- Docker running
- The observability + app stack already up (`make up-all`)
- The responder already listening in another terminal (`make responder`)
- `RESPONDER_WEBHOOK_SECRET` set to the same value in both terminals

The script injects a fault into the search provider (`fixture.py`), rebuilds
the app container, and waits for the SearchRunFailures alert to fire.  The
responder picks up the alert, collects evidence, and launches a headless
Claude Code agent in a git worktree to investigate and fix.

All ports come from env with safe defaults:

```sh
export RESPONDER_WEBHOOK_SECRET=any-string   # same value in both terminals

# terminal 1 -- responder
RESPONDER_PORT=8071 make responder

# terminal 2 -- stack + test
export COMPOSE_PROJECT_NAME=exam3
export HOST_PORT=8070
export GRAFANA_PORT=3071
export PROMETHEUS_PORT=9071
export LOKI_PORT=3171
export TEMPO_PORT=3271
export OTEL_COLLECTOR_PORT=4371
export OTEL_COLLECTOR_METRICS_PORT=8871
export RESPONDER_PORT=8071

make up-all
incident-response/test-incident.sh
```

Incidents are written to `incident-response/incidents/<timestamp>-<alertname>/`.
