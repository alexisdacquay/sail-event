# Deployment

The app runs on Render, region Frankfurt: two web services built from the root [Dockerfile](../Dockerfile), each with its own Render Postgres 18. How a commit gets to each one: [release-process.md](release-process.md).

## Which version runs where

| Env | URL | Runs | Check |
|---|---|---|---|
| prod | https://sail-event.onrender.com | the sha the owner promoted last | `curl -s https://sail-event.onrender.com/api/health` |
| dev | https://sail-event-dev.onrender.com | the head of `main`, redeployed on every push | `curl -s https://sail-event-dev.onrender.com/api/health` |

`/api/health` prints `{"status":"ok","commit":"<sha>"}`; the sha comes from Render's `RENDER_GIT_COMMIT`. `git log --oneline -1 <sha>` names the commit.

## Prove CD in 30 seconds

```bash
# dev runs the newest commit on main (CD on every push)
curl -s https://sail-event-dev.onrender.com/api/health
git ls-remote https://github.com/alexisdacquay/sail-event refs/heads/main
# prod runs the sha of the last manual promote
curl -s https://sail-event.onrender.com/api/health
gh run list -R alexisdacquay/sail-event --workflow=promote.yml --limit 3
```

The auto-deploy setting lives in the Render dashboard, not in the repo: `sail-event-dev` → Settings → Auto-Deploy = On Commit; `sail-event` → Auto-Deploy = Off.

## Using the live sites

- Registration is open on both: `curl -s https://sail-event.onrender.com/api/config` prints `{"registrationCodeRequired":false}`.
- Dev also has a shared `demo` / `demo` account (`SEED_DEMO=1`). Prod has none.
- A search takes minutes, not seconds: about 300 s on dev ([#145](https://github.com/alexisdacquay/sail-event/issues/145)).
- Limits: 5 registrations per IP per hour (1000 on dev); 6 **Search now** per user per rolling hour; per day, across all users, 600 search credits and 5000 model calls.

## Services

| Environment | Web service | Database | Deploys when |
|---|---|---|---|
| dev | `sail-event-dev` (starter) | `sail-event-dev-db` (basic_256mb) | every push to `main` |
| prod | `sail-event` (starter) | `sail-event-db` (Basic, point-in-time recovery on) | only through promote.yml |

- Health check path `/api/health` on both services, so Render keeps the old instance serving until a new deploy answers it.
- The prod database accepts connections from any IP address (inbound rule `0.0.0.0/0`); its credentials are the only barrier. Narrowing the rule is an open owner task.
- These settings come from the Render dashboard, recorded in [work/DEPLOY-render.md](../work/DEPLOY-render.md) (17 Oct) and [work/STATE.md](../work/STATE.md) (health path, 20 Oct). The repo cannot show them.

## Scheduled search

- [hourly-search.yml](../.github/workflows/hourly-search.yml) is scheduled at minute 07 of every hour and calls prod only (repo variable `SAIL_BASE_URL` = `https://sail-event.onrender.com`). The app has no scheduler of its own.
- GitHub delays scheduled runs. The 50 scheduled runs from 17 to 26 Oct were 2.1 to 7.8 hours apart, median 4.5 h. Measure again: `gh run list --workflow=hourly-search.yml --event schedule --limit 50`.
- Each run checks that `/api/health` answers 200, then calls `POST /api/search/all` with the `X-API-Key` secret. The server queues every user with saved criteria, oldest last search first, up to `MAX_SCHEDULED_USERS`; it skips users whose search is still running. It answers `202` with `usersQueued` and `usersSkipped`, then runs the searches in background tasks.
- So the job turns red only when prod is down or refuses the key. A search that fails after the 202 never shows there. On 25 Oct the model provider's balance ran out (HTTP 402) and searches on dev and prod failed for about two hours ([work/HANDOVER-2026-10-25.md](../work/HANDOVER-2026-10-25.md)); every scheduled run that day reported success, and prod has no alert ([observability/README.md](../observability/README.md)).

Setup, once per target:

```bash
gh variable set SAIL_BASE_URL --body "https://sail-event.onrender.com"   # also read by promote.yml
gh secret set SEARCH_ALL_API_KEY                                          # same value as SEARCH_ALL_API_KEY on the server
```

Run it by hand: `gh workflow run hourly-search.yml`; history: `gh run list --workflow=hourly-search.yml`.

## Environment variables

Set in Render → service → Environment. Values are prod's; dev differs only where the last column says so. Secrets live only in Render and in GitHub secrets, never in the repo.

**Required**

| Key | Value | Dev |
|---|---|---|
| `DATABASE_URL` | Render's internal database URL, with the scheme changed to `postgresql+psycopg://`. With `APP_ENV=prod` the app refuses to start without it | its own database |
| `APP_ENV` | `prod`: the app refuses to start without `DATABASE_URL` or `JWT_SECRET`, and refuses the fixture search and the fake model | `dev` |
| `PORT` | `8000`, the port the container listens on | same |
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
| `REGISTER_RATE_LIMIT_PER_HOUR` | `5` | successful registrations per IP per hour (dev: `1000`) |
| `SEARCH_NOW_PER_HOUR` | `6` | **Search now** runs per user per rolling hour |
| `REGISTRATION_CODE` | unset | an invite code; unset = open registration |
| `MAX_SCHEDULED_USERS` | `50` | users per scheduled run |
| `SEARCH_DAILY_CALLS` | `600` | search credits per day, all users together |
| `LLM_DAILY_CALLS` | `5000` | model calls per day, all users together; the judge reserves 3 calls per event before it starts |
| `EXTRACT_CONCURRENCY` | `10` | pages read in parallel per search (result pages and event pages) |
| `JUDGE_CONCURRENCY` | `10` | judge calls in parallel per search; `1` = one at a time |
| `DETAIL_FETCH_TIMEOUT`, `DETAIL_FETCH_MAX_BYTES` | `10` s, 2 MiB | limits for fetching one event page |
| `JWT_EXPIRY_MINUTES` | `60` | login lifetime |
| `LOG_LEVEL` | `INFO` | |
| `CORS_ORIGINS` | `http://localhost:5173` | only for the Vite dev server; Render serves UI and API from one origin |
| `LLM_USD_PER_1K_IN`, `LLM_USD_PER_1K_OUT`, `SEARCH_USD_PER_CALL` | unset | prices; when all three are set, each run records `cost_usd` |

**Must stay unset on Render**

- `SCORER`: a leftover from the first scorer; if it has any value, every search fails with `unset SCORER; use LLM_PROVIDER`.
- `FAKE_NOW`: fixes the app's clock. Tests, CI, `make run` and docker compose use it so the recorded data stays in the future.
- `OTEL_EXPORTER_OTLP_ENDPOINT`: not set, because Render has no collector. The live sites export no metrics or traces; their logs are JSON lines in Render → service → Logs. Telemetry runs in the local stack only ([observability/README.md](../observability/README.md)).

## Access

- Logs and metrics: Render dashboard → service → Logs / Metrics
- Shell: Render dashboard → service → Shell
- Database: Render dashboard → `sail-event-db` → Info → PSQL Command (external URL; inbound rules under Networking)

## Database credential rotation

Render → `sail-event-db` → Info → Credential Rotation → New default credential. Update `DATABASE_URL` on the web service, then delete the old user once it shows 0 open connections.

## Teardown

Render dashboard → service → Settings → Delete, for the web service and then the database. Deleting the database cannot be undone.
