# Robustness plan — Sail-event (2026-10-17)

Goal: every rubric point survives a hurried, less-skilled peer reviewer, and the public deployment survives real users.
Two inputs: a fresh-clone reviewer walkthrough (agent, scratchpad/review-clone) and a code read for production failure modes.

## A. Production failure modes found by code read

| # | Risk | Evidence | Impact | Fix | Size |
|---|---|---|---|---|---|
| A1 | Search blocks the whole server | `routers/search.py`: `async def run_search` calls sync `run_pipeline`; all handlers are `async def` with sync DB and bcrypt | with real adapters one search freezes every other request for seconds to minutes; health check fails; Render restarts the instance | make DB-touching handlers plain `def` (FastAPI threadpool), or `run_in_threadpool` for the pipeline | S |
| A2 | `search/all` is one long HTTP request over all users | `routers/search.py:35` loop | with N users and real adapters the hourly call exceeds the 5-min job; partial work lost? (Run rows per user exist) | per-user try/except with Run.error (verify), cap users per call or process newest-criteria first; job timeout documented | S |
| A3 | Prod silently falls back to SQLite | `db.py:12` default `sqlite:///./sail_event.db`; dev first deploy crashed on it | a missing DATABASE_URL on Render = data loss or crash loop | `APP_ENV=prod` requires DATABASE_URL (same guard pattern as JWT_SECRET) | S |
| A4 | Open registration + hourly paid searches | no cap on users; hourly job searches every user with criteria | spam accounts burn Tavily/Anthropic credit; cost unbounded | rate-limit register per IP; `MAX_USERS` or search only users seen in last 30 days; daily cap on scored events | M |
| A5 | No health check path on Render | `healthCheckPath: ""` on both services (connector read) | a broken deploy takes traffic | user sets `/api/health` in Settings (2 clicks) | user |
| A6 | Prod DB open to all IPs | `ipAllowList 0.0.0.0/0` on sail-event-db | password is the only guard | remove the rule (Render internal network still works) | user |
| A7 | Old DB credential still active | `sail_event_db_user` exists, 0 connections | leaked password still valid | delete in Render | user |
| A8 | Adapter timeouts | tavily `TIMEOUT` set; claude timeout 30s, 1 retry | bounded; fine | none | — |
| A9 | Single uvicorn worker, no restart policy knowledge | Dockerfile CMD | Render restarts on crash; OK | none | — |

## Walkthrough result (fresh clone, agent as hurried reviewer, 2026-10-17)
- Score given: full marks on every criterion (24/24 by the table; the agent wrote 22). All commands ran; live URL exercised end to end; metrics, traces, logs with trace id confirmed via APIs.
- Stumbles, ranked by the reviewer: (1) `make test-e2e` needs Playwright browsers, README silent; (2) `make responder` fails without RESPONDER_WEBHOOK_SECRET, README silent; (3) metrics appear ~60 s after the first search; (4) no curl walkthrough: queue is `/api/events?status=queued`, decision values are accepted/rejected; (5) port 8000 clash, HOST_PORT undocumented in README; (6) README test counts stale (165/22 → 178/25 + 19 responder); (7) plan.md "Later, after the MVP" reads as if on-call was not delivered; (8) Grafana "No data" on first boot; (9) `make up-all` needs the secret too; (10) restart integration test always skipped.
- Not checked by the reviewer: promote workflow (needs secrets), real adapters, Grafana UI.

## B. Reviewer-experience risks (merged with the walkthrough)
| # | Fix in README unless stated | Status |
|---|---|---|
| W1 | Tests section: one-time `cd e2e && npm ci && npx playwright install chromium` before `make test-e2e` | todo |
| W2 | When it breaks: `export RESPONDER_WEBHOOK_SECRET=any-string` before `make up-all` and `make responder` | todo |
| W3 | Observability: "run a search, wait 60 s, refresh" | todo |
| W4 | "Try it with curl" block: register, login, criteria, search, queue, decision, calendar | todo |
| W5 | Port clash line: `HOST_PORT=8010 docker compose up --build` | todo |
| W6 | Test counts: 178 backend, 25 frontend, 19 responder, 7 integration, 2 e2e | todo |
| W7 | plan.md: one line that the "Later" items shipped as #25 #26 | todo |
| W10 | restart test: issue filed with A3 | issue |

| # | Risk | Fix | Size |
|---|---|---|---|
| B1 | e2e needs Playwright browsers installed; README does not say | README Tests section: one-time `cd e2e && npm ci && npx playwright install chromium` | S |
| B2 | Port 8000 busy on a reviewer machine → compose fails | README: `HOST_PORT=8010 docker compose up` one-liner | S |
| B3 | `make` missing on Windows | README: the compose command is the single command; make targets are convenience | S |
| B4 | On-call agent not runnable by a reviewer (needs `claude` CLI + account) | README says so and points to the recorded incident; keep test-incident.sh runnable up to the webhook | S |
| B5 | Public URL shows canned events (fixture adapters) | real keys on prod (user decision) or a README sentence saying scoring is simulated until keys are set | user |
| B6 | Observability needs 6 containers; memory | README: note ~2 GB RAM, `make up-all` | S |

## Status 2026-10-18
- A1 → #37 closed (755ca1e). A3 + W10 → #38 closed (c994654, 93ad48f). A2 + A4 → #39 closed (fff0c24, 937352a). W1–W7 → README 11f2828. All promoted to prod (93ad48f).
- Still the user's: A5 health check path, A6 DB inbound rule, A7 old DB user, B5 API keys.
- Second walkthrough running; results appended below when in.

## C. Order
1. Walkthrough report → merge into B, re-rank.
2. File issues for A1, A3, A2, A4 (post-mvp label? no: label `mvp`-adjacent "robustness"), run through the loop, promote.
3. README fixes from B in one commit.
4. User items A5, A6, A7, B5.
