# Architecture — Sail-event
## Stack
| Concern | Choice | Version |
|---|---|---|
| Frontend framework | React + TypeScript | 19.3 |
| Frontend build | Vite | 8.3 |
| Frontend styling | Tailwind CSS + shadcn/ui | — |
| Backend framework | FastAPI (Python) | 0.143 |
| Python runtime | — | 3.12 |
| ORM | SQLAlchemy | 2.1 |
| Migrations | Alembic | — |
| DB (dev) | SQLite | — |
| DB (prod) | PostgreSQL | 18 |
| ICS feed | icalendar | 7.3 |
| Auth | bcrypt + PyJWT | 5.0 / 2.15 |
| Tests (backend) | pytest | 9.1 |
| Tests (e2e) | Playwright | 1.64 |
| CI/CD | GitHub Actions | — |
| Deploy | Render Web Service (Docker, auto-deploy on push to main) + Render Postgres | — |
| Scheduler | GitHub Actions cron → POST /api/search/all | — |
| Contract | openapi.yaml (written from frontend at S4; backend implements it; CI checks match) | — |
| Container | Docker; docker-compose for app + Postgres | — |
| Telemetry | OTel → Prometheus + Loki + Tempo + Grafana | — |

## Repo layout
| Path | Purpose |
|---|---|
| `frontend/` | React app (Vite, Tailwind, shadcn/ui) |
| `backend/` | FastAPI app (routers, models, services, adapters) |
| `openapi.yaml` | API contract; written from frontend at S4, backend implements it |
| `docker-compose.yml` | App + Postgres services |
| `.github/workflows/` | CI (test on PR) and CD (deploy on main) |
| `_docs/` | Product spec, architecture, tasks |
| `observability/` | OTel collector config, Grafana dashboards, docker-compose |
| `incident-response/` | On-call agent prompt, runbooks |
| `e2e/` | Playwright end-to-end tests |
| `Makefile` | Run, test, build, deploy commands |

## Data model
| Table | Columns | Constraints |
|---|---|---|
| User | id, username, password_hash, upper_threshold, lower_threshold, ics_token, created_at | username UNIQUE; lower_threshold < upper_threshold (validated on write) |
| Criteria | id, user_id FK, text, updated_at | user_id UNIQUE (one profile per user) |
| Event | id, user_id FK, title, date_time, place, link, description, score, score_reason, scorer_model, status, run_id FK, created_at | status ENUM(new, accepted, rejected, queued); UNIQUE(user_id, link) for dedup |
| Run | id, user_id FK, started_at, finished_at, events_found, events_new, trigger | one row per search execution |
- Events enter as `new`; each run first scores any leftover `new` events (recovery after a crash between insert and scoring)

## Adapter interfaces
| Adapter | Signature | Implementations |
|---|---|---|
| SearchProvider | `search(queries) -> list[RawEvent]` | `FixtureSearchProvider` (canned results, S4-S12); real provider at S13 |
| Scorer | `score(event, criteria) -> (score, reason)` | `FakeScorer` (deterministic score from title hash, S4-S12); real LLM scorer at S13 |
- Env var selects fixture vs real for each adapter; fixture is the default in CI

## Request flow — one hourly run
1. Manual: signed-in user triggers `POST /api/search` (their own criteria only)
2. Hourly: GitHub Actions calls `POST /api/search/all` with a shared-secret header; server iterates every user with criteria, one Run per user
3. For each user: derive search queries from criteria text
4. `SearchProvider.search(queries)` returns candidate events
5. Dedup: `INSERT ... ON CONFLICT(user_id, link) DO NOTHING`; keep only new rows
6. Score any of the user's events still in `new` (recovery), then score each new event via `Scorer.score`
7. Triage: score > upper threshold -> accepted; score < lower threshold -> rejected; otherwise (including equal) -> queued
8. Run row written with events_found, events_new, trigger, timestamps
9. Accepted events appear in the user's ICS feed at `GET /api/calendar/{ics_token}`

## Environments
| Aspect | Dev | Prod |
|---|---|---|
| DB | SQLite (local) / Postgres (compose) / Render Postgres (dev service) | Render Postgres |
| URL | localhost / https://sail-event-dev.onrender.com | https://sail-event.onrender.com (promoted by hand) |
| Secrets | .env file | Render env vars |
| Adapters | fixture + fake scorer | real (env var toggles) |
| Scheduler | manual / compose | GitHub Actions hourly |
| Reverse proxy | none | Render (TLS) |

## Known limitations
- Dedup is by (user_id, link); the same event under two URLs appears twice
- Run is an engineering table for the failed/empty-run alert, not a product concept
