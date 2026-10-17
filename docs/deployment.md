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
| `DATABASE_URL` | Render internal database URL with the prefix changed to `postgresql+psycopg://` |
| `APP_ENV` | `prod` |
| `PORT` | `8000` |
| `JWT_SECRET` | random |
| `SEARCH_ALL_API_KEY` | random; the same value is the GitHub Actions secret `SEARCH_ALL_API_KEY` |
| `SEARCH_PROVIDER`, `TAVILY_API_KEY` | `tavily` + key for real web search; unset = fixtures |
| `SCORER`, `ANTHROPIC_API_KEY` | `claude` + key for real scoring; unset = fake scorer |

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
