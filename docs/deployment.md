# Deployment

The app runs on Render: one Web Service built from the root `Dockerfile`, one managed Postgres. Region Frankfurt.

| Piece | Where | Notes |
|---|---|---|
| App | Render Web Service `sail-event` | Docker runtime, branch `main`, auto-deploy on every commit |
| URL | https://sail-event.onrender.com | TLS by Render |
| Database | Render Postgres `sail-event-db` | Postgres 18, point-in-time recovery on |
| Hourly search | GitHub Actions `hourly-search.yml` | see `docs/release-process.md`, Scheduled search |

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

`GET /api/health` returns `{"status":"ok"}`. Set it as the health check path in Render → sail-event → Settings so a failed deploy never takes traffic.

## Access

- Logs and metrics: Render dashboard → sail-event → Logs / Metrics
- Shell: Render dashboard → sail-event → Shell
- Database: Render dashboard → sail-event-db → Info → PSQL Command (external URL; inbound rules under Networking)

## Database credential rotation

Render → sail-event-db → Info → Credential Rotation → New default credential, then update `DATABASE_URL` on the web service and delete the old user once it shows 0 open connections.

## Teardown

Render dashboard → service → Settings → Delete, for the web service and then the database. Deleting the database is irreversible.
