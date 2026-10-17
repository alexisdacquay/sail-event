# Operations and Security Report — Sail-event

## Incident reconstruction: 20261017-052050-SearchRunFailures

### 1. Deployed version and user impact

- **Deployed version**: unknown (`evidence.md` "Deployed version: unknown")
- **App health**: health check failed (`evidence.md` "App health: (health check failed)")
- **Error count**: ~23 failed search runs in 10 minutes (Prometheus `increase(sail_runs_total{outcome="error"}[10m])` = 27.69; alert annotation: "Observed 23 failed run(s)")
- **User impact**: all search runs failing — every call to `POST /api/search` and scheduled `POST /api/search/all` produced outcome=error

Reference: `incident-response/incidents/20261017-052050-SearchRunFailures/evidence.md`

### 2. Alert and evidence

- **Alert**: `SearchRunFailures`, severity critical, fired at `2026-10-17T05:20:20Z`
- **Source**: Grafana evaluation of `increase(sail_runs_total{outcome="error"}[10m]) > 1`, with `for: 5m`
- **Labels**: `service: sail-event-backend`, `deployment_environment: dev`, `trigger: manual`
- **Evidence collected**: Prometheus error count, Loki query (0 log results — OTLP log pipeline not capturing at that point), app health check (failed), recent commits, deployed version (unknown)

References:
- `incident-response/incidents/20261017-052050-SearchRunFailures/alert.json`
- `incident-response/incidents/20261017-052050-SearchRunFailures/evidence.md`

### 3. Model and configuration used, action proposed

- **Agent model**: Sonnet (`--model sonnet`)
- **Allowed tools**: `Read`, `Edit`, `Bash(make test)`, `Bash(cat *)`, `Bash(grep *)`, `Bash(find *)`, `Bash(ls *)`, `Bash(head *)`, `Bash(tail *)`, `Bash(git log *)`, `Bash(git diff *)`, `Bash(git status)`, `Bash(git add *)`, `Bash(git commit *)`, `Bash(git checkout -b *)`
- **Budget**: `--max-budget-usd 1`
- **Action proposed**: remove the injected `raise RuntimeError("injected: scorer fault")` from `FakeScorer.score()` in `backend/app/adapters/fake.py`

Reference: `incident-response/incidents/20261017-052050-SearchRunFailures/agent.log`

### 4. Policy decision and command executed

- **Autonomy policy** (`incident-response/autonomy-policy.yaml`):
  - Allowed edits: `backend/app/**`, `backend/tests/**`
  - Allowed execution: `make test`, read-only shell, git operations (no push)
  - Forbidden: push, modify Dockerfile/compose/.github/observability/.env, call external APIs
- **Agent actions**: edited `backend/app/adapters/fake.py` (removed the `raise RuntimeError` line), ran `uv run pytest tests/ -q` (131 passed), committed fix

### 5. Recovery verification

- **Verdict**: fix
- **Commit**: `dae24e9` on branch `incident/20261017-052050-SearchRunFailures`
- **Test result**: 131 passed, 0 errors
- **Recovery runbook**: `incident-response/runbooks/verify-recovery.sh` — runs backend + frontend tests on the incident branch

References:
- `incident-response/incidents/20261017-052050-SearchRunFailures/verdict.json`
- `incident-response/runbooks/verify-recovery.sh`

### 6. Related security findings and human disposition

- The responder agent's capabilities, credential scope, and merge authority are documented in `security-audit/capability-table.md`
- Security findings from the Semgrep scan and model review, with dispositions (fixed, accepted, or deferred to post-mvp issues), are in `security-audit/disposition.md`

## AI tool and data policy

- **Criteria and event text** are sent to the scorer model (Claude, via the Anthropic API) for relevance scoring. The scorer prompt contains: event title, date_time, place, description, and the user's criteria text. No usernames, tokens, or keys are included.
- **No user credentials or secrets** are sent to any model. The scorer prompt template (`backend/app/adapters/prompts/scorer_v1.md`) includes only five data fields. The validation error handler (`main.py`) strips raw input from error responses.
- **The responder agent** receives evidence (read-only telemetry data) and source code only. It does not receive user data, API keys, or tokens. It inherits `ANTHROPIC_API_KEY` from the host environment for its own API calls.
- **No production user data** is used for model training. The Anthropic API does not train on API inputs.
- **Keys and secrets** live in environment variables and GitHub Secrets only. `.env` is git-ignored; `.env.example` has placeholder values. Compose uses env-var substitution with dev defaults.
- **The responder's prompt** comes from a versioned repo file (`incident-response/responder-task.md`), not from user input. Evidence is injected from read-only telemetry queries.
