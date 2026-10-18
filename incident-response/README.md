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
| `SKIP_HOOK_TESTS` | no | Set to `1` in the agent env allowlist so commits in incident worktrees skip the pre-commit test gate |

## Start

```sh
export RESPONDER_WEBHOOK_SECRET=<value>
make responder
```
