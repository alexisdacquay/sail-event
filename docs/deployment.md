# Deployment

The app runs on Render: separate dev and prod web services, each with its own database. Both build the root [Dockerfile](../Dockerfile). CI, dev deployment and manual promotion are explained in [release-process.md](release-process.md).

## Which version runs where

| Env | URL | Runs | Check |
|---|---|---|---|
| prod | https://sail-event.onrender.com | manually selected commit | `curl -s https://sail-event.onrender.com/api/health` |
| dev | https://sail-event-dev.onrender.com | follows `main`; deployment may still be building | `curl -s https://sail-event-dev.onrender.com/api/health` |

`/api/health` prints `{"status":"ok","commit":"<sha>"}`; the sha comes from Render's `RENDER_GIT_COMMIT`. `git log --oneline -1 <sha>` names the commit.

<a id="prove-cd-in-30-seconds"></a>

## Check deployed commits

```bash
# Compare dev with main after the Render build completes
curl -s https://sail-event-dev.onrender.com/api/health
git ls-remote https://github.com/alexisdacquay/sail-event refs/heads/main
# Compare prod with the manual promotion history
curl -s https://sail-event.onrender.com/api/health
gh run list -R alexisdacquay/sail-event --workflow=promote.yml --limit 3
```

The commands compare the deployed commits with main and promotion history. [The deployment log](../work/DEPLOY-render.md) records an automatic dev deploy after a push on 2026-10-17, with these settings: `sail-event-dev` → Settings → Auto-Deploy = On Commit; `sail-event` → Auto-Deploy = Off.

## Using the live sites

- Registration is open on both: `curl -s https://sail-event.onrender.com/api/config` prints `{"registrationCodeRequired":false}`.
- The deployment log records `SEED_DEMO=1` on dev, which creates the shared `demo` / `demo` account. Keep it unset on prod.
- Live-adapter searches measured 86–493 seconds across local runs on different code revisions in [PR #144](https://github.com/alexisdacquay/sail-event/pull/144).
- Default limits: 5 successful registrations per IP per hour; 6 manual searches per user per rolling hour; daily budgets of 600 search credits and 5000 model calls across users. Settings are configurable; see [Environment variables](#environment-variables).

## Services

The [deployment log](../work/DEPLOY-render.md) records these services in Frankfurt with Postgres 18 on 2026-10-17:

| Environment | Web service | Database | Deploys when |
|---|---|---|---|
| dev | `sail-event-dev` (starter) | `sail-event-dev-db` (basic_256mb) | every push to `main` |
| prod | `sail-event` (starter) | `sail-event-db` (Basic, point-in-time recovery on) | manual promotion; dashboard changes can also redeploy |

- Setting Render’s health check path to `/api/health` remains open in the deployment log.
- The log records the prod database inbound rule as `0.0.0.0/0`, with a pending decision to restrict or accept external access.
- Saving environment variables can trigger a deploy independently of `promote.yml`; the [work log](../work/STATE.md) records this on 2026-10-20.

## Scheduled search

- [hourly-search.yml](../.github/workflows/hourly-search.yml) is scheduled at minute 07 of every hour and calls prod only (repo variable `SAIL_BASE_URL` = `https://sail-event.onrender.com`). The app has no scheduler of its own.
- GitHub delays scheduled runs. The 50 scheduled runs from 17 to 26 Oct were 2.1 to 7.8 hours apart, median 4.8 h (sample ending 2026-10-26 12:51 UTC). Reproduce the timestamps: `gh run list -R alexisdacquay/sail-event --workflow=hourly-search.yml --event schedule --limit 50 --json createdAt`; sort them and subtract adjacent timestamps.
- Each run checks that `/api/health` answers 200, then calls `POST /api/search/all` with the `X-API-Key` secret. The server queues every user with saved criteria, oldest last search first, up to `MAX_SCHEDULED_USERS`; it skips users with an unfinished run started in the last 55 minutes and those beyond the cap. It answers `202` with `usersQueued` and `usersSkipped`, then runs the searches in background tasks.
- The job fails on a failed health GET, a non-2xx enqueue response or an unreadable response body. Success confirms enqueueing; searches that fail after the 202 are not reflected in the job result. See [Monitoring](#monitoring) for search-failure coverage.

Setup, once per target:

```bash
gh variable set SAIL_BASE_URL --body "https://sail-event.onrender.com"   # also read by promote.yml
gh secret set SEARCH_ALL_API_KEY                                          # same value as SEARCH_ALL_API_KEY on the server
```

Run it by hand: `gh workflow run hourly-search.yml`; history: `gh run list --workflow=hourly-search.yml`.

## Monitoring

Project observability, alerts and the on-call responder cover the local stack (`make up-all`); the deployed app sends no telemetry to it. Render provides service logs and platform metrics separately. The [observability runbook](../observability/README.md) explains the signals, alerts and recorded drills.

## Environment variables

Set in Render → service → Environment. These settings target main. Confirm provider choices against the [promotion checklist](release-process.md#manual-promotion-to-prod) when deploying. Secrets belong in environment variables and GitHub secrets, never in tracked files.

**Required**

| Key | Value | Dev |
|---|---|---|
| `DATABASE_URL` | Render's internal database URL, with the scheme changed to `postgresql+psycopg://`. With `APP_ENV=prod` the app refuses to start without it | its own database |
| `APP_ENV` | `prod`: the app refuses to start without `DATABASE_URL` or `JWT_SECRET`, and refuses the fixture search and the fake model | `dev` |
| `PORT` | `8000`; the Dockerfile runs Uvicorn on this fixed port (it does not read `PORT`) | same |
| `JWT_SECRET` | random | own value |
| `SEARCH_ALL_API_KEY` | random; the GitHub secret `SEARCH_ALL_API_KEY` holds the same value | own value |
| `FORWARDED_ALLOW_IPS` | `*`: take the client IP from Render's proxy header. Unset behind Render, all users share one rate-limit bucket and `/api/calendar-url` returns `http://` links | same |
| `SEED_DEMO` | unset | `1`: creates the `demo` / `demo` account at start |

**Search**

| Key | Value | Dev |
|---|---|---|
| `SEARCH_PROVIDER` | `exa` (reads live page text). Also accepted: `tavily`, `brave`. Unset = `fixture`, recorded pages, refused when `APP_ENV=prod` | `exa` |
| `EXA_API_KEY` | Exa key. `TAVILY_API_KEY` or `BRAVE_API_KEY` for the other providers | same |
| `MAX_RESULTS_PER_QUERY` | `10`; default `20` | |
| `TAVILY_SEARCH_DEPTH` | `advanced` (default) for **Search now**; `TAVILY_SEARCH_DEPTH_SCHEDULED`, `basic` (default), for scheduled runs. Tavily reads them; for every provider they also set the budget cost of a call | same |
| `SEARCH_CREDITS_ADVANCED` | `2`: budget credits per advanced call (basic = 1) | same |

**Model**

| Key | Value | Dev |
|---|---|---|
| `LLM_PROVIDER` | `openai_compatible`. Unset = `fake`, recorded answers, refused when `APP_ENV=prod` | same |
| `LLM_BASE_URL` | `https://api.deepseek.com` | same |
| `LLM_MODEL` | `deepseek-flash` | same |
| `LLM_API_KEY` | DeepSeek key | same |
| `LLM_JSON_MODE` | `json_object`; `json_schema` for providers that support it. Required with `openai_compatible` | same |
| `LLM_TIMEOUT_SECONDS` | `120` (also the default) | same |

**Guardrail** (checks the criteria text when the user saves it)

| Key | Value | Dev |
|---|---|---|
| `GUARDRAIL` | `lakera`; default `none`. Blocks prompt attacks only; Lakera's moderation, PII and link detections are ignored | same |
| `LAKERA_API_KEY` | required with `lakera` | same |
| `GUARD_FALLBACK` | `self_check`: when Lakera fails or is out of quota (a 429 is retried once), the model checks the text for prompt injection instead | same |

**Limits, budgets, speed**

| Key | Default | Meaning |
|---|---|---|
| `REGISTER_RATE_LIMIT_PER_HOUR` | `5` | successful registrations per IP per hour; the work log records dev configured at `1000` |
| `SEARCH_NOW_PER_HOUR` | `6` | **Search now** runs per user per rolling hour |
| `REGISTRATION_CODE` | unset | an invite code; unset = open registration |
| `MAX_SCHEDULED_USERS` | `50` | users per scheduled run |
| `SEARCH_DAILY_CALLS` | `600` | search credits per day, all users together |
| `LLM_DAILY_CALLS` | `5000` | model calls per day, all users together; the judge reserves 3 calls per event before it starts |
| `EXTRACT_CONCURRENCY` | `10` | pages read in parallel per search (result pages and event pages) |
| `JUDGE_CONCURRENCY` | `10` | judge calls in parallel per search; `1` = one at a time |
| `DETAIL_FETCH_TIMEOUT`, `DETAIL_FETCH_MAX_BYTES` | `10` s, 2 MiB | limits for fetching one event page |
| `JWT_EXPIRY_MINUTES` | `60` | login lifetime |
| `LOG_LEVEL` | `INFO` | application log level |
| `APP_VERSION` | `dev` | telemetry service version; does not set the health endpoint’s `commit` |
| `CORS_ORIGINS` | `http://localhost:5173` | only for the Vite dev server; Render serves UI and API from one origin |
| `LLM_USD_PER_1K_IN`, `LLM_USD_PER_1K_OUT`, `SEARCH_USD_PER_CALL` | unset | prices; when all three are set, each run records `cost_usd` |

**Legacy and local-only settings**

- `SCORER`: a leftover from the first scorer; if it has any value, every search fails with `unset SCORER; use LLM_PROVIDER`.
- `FAKE_NOW`: freezes date-dependent search logic. CI, `make run` and compose use a fixed date for recordings; real-adapter deployments should leave it unset.
- `OTEL_EXPORTER_OTLP_ENDPOINT`: leave unset on Render. See [Monitoring](#monitoring) for the collection setup.

## Health

`GET /api/health` returns a status and the deployed commit, not database or provider readiness. A green health check can coexist with failed searches. The container runs migrations before starting Uvicorn. Migration and data-recovery requirements are in [Rollback](release-process.md#rollback).

## Access

- Logs and metrics: Render dashboard → service → Logs / Metrics
- Shell: Render dashboard → service → Shell
- Database: Render dashboard → `sail-event-db` → Info → PSQL Command (external URL; inbound rules under Networking)

## Database credential rotation

Render → `sail-event-db` → Info → Credential Rotation → New default credential. Update `DATABASE_URL` on the web service, then delete the old user once it shows 0 open connections.

## Teardown

Render dashboard → service → Settings → Delete, for the web service and then the database. Deleting the database cannot be undone.
