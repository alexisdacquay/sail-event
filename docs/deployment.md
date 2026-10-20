# Deployment

The app runs on Render, region Frankfurt, two environments built from the same root `Dockerfile`:

| Environment | Web Service | URL | Database | Deploys when |
|---|---|---|---|---|
| dev | `sail-event-dev` (starter) | https://sail-event-dev.onrender.com | `sail-event-dev-db` (basic) | every push to `main` |
| prod | `sail-event` (starter) | https://sail-event.onrender.com | `sail-event-db` (basic, PITR on) | the promote workflow, by hand; auto-deploy off |

Hourly search runs against prod from GitHub Actions `hourly-search.yml` (see `docs/release-process.md`). Dev seeds the `demo` / `demo` user (`SEED_DEMO=1`); prod does not.

## Environment variables (set in Render → sail-event → Environment)

| Key | Value |
|---|---|
| `DATABASE_URL` | Render internal database URL with the prefix changed to `postgresql+psycopg://`. Required when `APP_ENV=prod` |
| `APP_ENV` | `prod` |
| `PORT` | `8000` |
| `JWT_SECRET` | random |
| `SEARCH_ALL_API_KEY` | random; the same value is the GitHub Actions secret `SEARCH_ALL_API_KEY` |
| `SEARCH_PROVIDER`, `TAVILY_API_KEY` | `tavily` + key for real web search; unset = fixtures |
| `TAVILY_SEARCH_DEPTH` | `advanced` (default) or `basic` |
| `MAX_RESULTS_PER_QUERY` | `20` (default, Tavily max) |
| `SCORER`, `ANTHROPIC_API_KEY` | **Remove after v2 upgrade** (replaced by `LLM_PROVIDER`, `LLM_API_KEY`). Also remove `SCORER_MODEL` |
| `LLM_PROVIDER` | `openai_compatible` for real scoring; `fake` (default outside prod) |
| `LLM_BASE_URL` | `https://api.deepseek.com` (required when `LLM_PROVIDER=openai_compatible`) |
| `LLM_MODEL` | `deepseek-flash` |
| `LLM_API_KEY` | DeepSeek API key (required when `LLM_PROVIDER=openai_compatible`) |
| `LLM_JSON_MODE` | `json_object` (DeepSeek) or `json_schema` |
| `FAKE_NOW` | ISO-8601 instant; set in dev/CI/compose (`2026-10-18T12:00:00+02:00`), unset in prod |
| `MAX_SCHEDULED_USERS` | `50` — max users per scheduled search |
| `REGISTER_RATE_LIMIT_PER_HOUR` | `5` — successful registrations per IP per hour |
| `REGISTRATION_CODE` | optional — invite code for registration; unset = open |
| `SEARCH_DAILY_CALLS` | `600` — daily search-call budget across all users |
| `LLM_DAILY_CALLS` | `5000` — daily LLM-call budget across all users |
| `LLM_USD_PER_1K_IN` | cost per 1 000 input tokens; set all three price vars to enable `cost_usd` |
| `LLM_USD_PER_1K_OUT` | cost per 1 000 output tokens |
| `SEARCH_USD_PER_CALL` | cost per search API call |
| `GUARDRAIL` | `lakera` (prod) or `none` (default, dev/CI); set at issue H promote. The Lakera guard blocks `prompt_attack` detectors only; content-moderation, PII and unknown-link detections are ignored |
| `LAKERA_API_KEY` | Lakera Guard API key (required when `GUARDRAIL=lakera`) |
| `GUARD_FALLBACK` | `self_check` (prod) or `none`; used only when Lakera errors or quota exhausted. The fallback checks for prompt injection only (not content moderation); Lakera 429 is retried once before falling back |
| `SEARCH_NOW_PER_HOUR` | `6` — "Search now" manual runs per user per rolling hour |

Dev environment (`sail-event-dev`): `APP_ENV=dev`, `FAKE_NOW=2026-10-18T12:00:00+02:00`, `SEED_DEMO=1`.

`docker-compose.yml` defaults `FAKE_NOW` to `2026-10-18T12:00:00+02:00`
so `docker compose up` with no env gives the demo a non-empty queue.
Render dev sets `FAKE_NOW` explicitly; prod never sets it.

Secrets live only in Render and GitHub secrets, never in the repo.

## Health

`GET /api/health` returns `{"status":"ok","commit":"<git sha>"}`; the commit comes from Render's `RENDER_GIT_COMMIT` and is what the promote workflow checks. Set `/api/health` as the health check path in each service's Settings so a failed deploy never takes traffic.

## Access

- Logs and metrics: Render dashboard → sail-event → Logs / Metrics
- Shell: Render dashboard → sail-event → Shell
- Database: Render dashboard → sail-event-db → Info → PSQL Command (external URL; inbound rules under Networking)

## Database credential rotation

Render → sail-event-db → Info → Credential Rotation → New default credential, then update `DATABASE_URL` on the web service and delete the old user once it shows 0 open connections.

## Teardown

Render dashboard → service → Settings → Delete, for the web service and then the database. Deleting the database is irreversible.
