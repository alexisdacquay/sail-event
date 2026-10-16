# Stack options v3 — Sail-event (2026-10-16; v2 + QA corrections)

## Option table (versions verified 2026-10-16; sources at end of file)

| | Frontend | Backend | DB | Scheduler | ICS feed | Auth | Tests | Deploy |
|---|---|---|---|---|---|---|---|---|
| **A** | React 19.3, Vite 8.3 | FastAPI 0.143, Python 3.12 | SQLAlchemy 2.1 — SQLite → Postgres 18 | APScheduler 3.11 | icalendar 7.3 | bcrypt 5.0 + PyJWT 2.15 | pytest 9.1 + Playwright 1.64 | Render / Railway |
| **B** | Jinja2 3.1 + HTMX 4.0 + Alpine 3.17 | FastAPI 0.143, Python 3.12 | SQLAlchemy 2.1 — SQLite → Postgres 18 | APScheduler 3.11 | icalendar 7.3 | bcrypt 5.0 + session cookie | pytest 9.1 + Playwright 1.64 | Render / Railway |
| **C** | React 19.3, Vite 8.3 | Hono 4.13, Node 22 | Drizzle 0.45 — better-sqlite3 → postgres.js | node-cron 4.6 | ical-generator 11.1 | bcryptjs + jose 6.2 | Vitest 5.0 + Playwright 1.64 | Render / Railway |

- python-jose → **PyJWT 2.15**: python-jose is unmaintained with unpatched critical CVE-2026-85394; PyJWT is actively maintained (4 releases in 2026), API-compatible, already a transitive dependency.

### Shared by all options

- **Contract**: openapi.yaml — auto-generated from FastAPI in A/B; hand-written in C
- **Container**: one image, backend serves the built frontend; docker compose for app + Postgres
- **CI/CD**: GitHub Actions — tests → build → deploy → health-check
- **Telemetry (course default)**: OTel collector → Prometheus + Loki + Tempo + Grafana in a separate compose
- **Telemetry (cheaper)**: OTel SDK → Grafana Cloud free tier (10k metrics, 50 GB logs, 50 GB traces/mo; no self-hosted stack)

## Option A — Course default (React + FastAPI + SQLAlchemy)

**For**
- Course prompts (METHOD.md lessons 2–4) run verbatim; every step S4–S12 has a tested path — no adaptation
- Python has the richest LLM SDK ecosystem; the scorer's structured-output parsing against per-user criteria is simplest here
- Alembic + SQLAlchemy handle the event dedup `ON CONFLICT DO NOTHING` on both SQLite and Postgres without dialect hacks at S7

**Against**
- The hourly search job and scorer both run in Python; React adds a Node build stage and a second dependency tree that neither touches at runtime
- APScheduler in-process loses the hourly schedule on container restart; needs an external trigger or a paid cron to run the search reliably
- The service-layer mock swap at S4 is pure scaffolding — the approval queue and per-user ICS link are pages a server-rendered stack ships directly

## Option B — Server-rendered (HTMX + FastAPI)

**For**
- The ICS feed endpoint, scorer, and hourly search job share one Python process; Dockerfile is a single stage with no Node toolchain
- The approval queue is per-user accept/reject buttons on scored events — HTMX partial swaps are the exact pattern; no client-side state for triage
- Multi-user auth is session cookies with CSRF; no JWT token-refresh logic, no client-side token storage leaking the per-user ICS secret

**Against**
- No course prompts for this stack; every lesson 2–4 prompt must be rewritten and the tested path disappears
- HTMX has no component-level tests; the criteria editor, threshold sliders, and scorer-flag toggle are checked only by Playwright e2e — regressions at S13 service-layer swap are caught later
- Alpine.js state management is adequate for the current approval queue but becomes a constraint if the criteria editor grows interactive (autocomplete, drag-to-reorder)

## Option C — TypeScript everywhere (React + Hono + Drizzle)

**For**
- The scorer's structured-output parser, the ICS generator, and the event dedup query all share TypeScript types checked at compile time
- The dedup query and per-user auth middleware can be unit-tested with Vitest against in-memory SQLite — same DB the hourly job fixture uses; no separate test harness
- Hono middlewares for per-user ICS feed auth and scorer-flag toggling are zero-dependency, typed, and testable without a running server

**Against**
- No course prompts; every lesson prompt must be adapted, and FastAPI's auto-generated openapi.yaml (used at S4) must be hand-written instead
- Node LLM SDKs exist but structured-output extraction — the scorer's core job parsing free-text criteria against event descriptions — is less mature than Python's Pydantic-based parsers
- The event dedup `ON CONFLICT DO NOTHING` + `INSERT ... RETURNING` works in both Drizzle dialects, but its SQLite → Postgres migration tooling is less proven than Alembic for the S7 switch

## Cross-cutting choices (independent of option)

### Adapter interfaces

| Adapter | Contract | Notes |
|---|---|---|
| Search provider | `search(queries) → list[RawEvent]` | Fixture returns canned results S4–S12; real provider at S13; env var selects which |
| Scorer | `score(event, criteria) → ScoredEvent` | Fake returns deterministic score from title hash; real calls LLM; env-var flag selects which |

### Deploy targets (verified 2026-10-16)

| Target | Tier | Sleeps idle? | In-process scheduler works? | Cheapest 24/7 hourly run | $/mo |
|---|---|---|---|---|---|
| Render | Free (750 h/mo, up to 25 services) | Yes, 15 min | **No** — dies on sleep | GH Actions cron → `POST /search` (public repo: free) | $0 |
| Render | Cron job (Starter) | N/A | N/A | Dedicated cron service, billed $0.00016/min, $1 floor | $1 |
| Render | Starter web (always-on) | No | Yes | In-process APScheduler / node-cron | $7 |
| Railway | Trial ($5 one-time, 30 days) | No (sleep opt-in) | Yes, within credit | In-process scheduler | $0 (trial) |
| Railway | Free ($1/mo credit) | No (sleep opt-in) | Unlikely — $1 may not cover 24/7 | Serverless + GH Actions cron → endpoint | $0? unverified: ~720 wake-ups/mo may exceed the $1 credit |
| Railway | Hobby ($5/mo incl. $5 usage) | No | Yes | In-process scheduler | $5 |
| Fly.io | None (no free tier since Oct 2024) | No (pay-per-second) | Yes | Smallest shared-cpu-1x Machine | ~$2.19 |

### ICS library per language

| Language | Library | Version | Notes |
|---|---|---|---|
| Python | icalendar | 7.3.0 | RFC 5545 generate + parse; mature |
| TypeScript | ical-generator | 11.1.2 | Generate-only (sufficient); upgrade to ≥11.1 to fix ICS injection CVE |

## Recommendation

**Option A** — course prompts run verbatim, Python is the natural home for the LLM scorer, and Alembic handles the SQLite → Postgres dedup migration without dialect workarounds.

Strongest fact against (applies to every option): on every free tier the in-process hourly scheduler dies when the service sleeps or restarts; the search loop, which is the product, only runs reliably from an external trigger (GitHub Actions cron → POST /search, $0 on a public repo) or an always-on paid service ($7/mo on Render).

## Sources

### Deploy targets
- Vendor pages (checked by QA 2026-10-16): https://render.com/pricing · https://railway.com/pricing · https://fly.io/pricing · https://docs.fly.io/about/discontinued-plans/
- Render pricing / sleep: https://temps.sh/blog/render-pricing-2026
- Render cron job per-minute billing: https://deploycloud.app/blog/render-pricing
- Render free-tier sleep workaround: https://dev.to/hassanyosuf/how-to-keep-your-render-free-tier-app-alive-without-paying-for-it-o8e
- Fly.io no free tier since Oct 2024: https://expresstech.io/7-fly-io-alternatives-in-2026-real-pricing-after-the-free-tier-died/
- Fly.io pay-as-you-go pricing: https://temps.sh/blog/fly-io-pricing-2026
- Railway pricing / trial / free: https://dev.to/nayankyada/railway-pricing-2026-free-tier-limits-usage-costs-when-to-upgrade-1acm
- Railway sleep behavior: https://encore.dev/articles/render-vs-railway
- GitHub Actions free tier: https://cicdcalculator.com/github-actions-free-tier

### Libraries
- FastAPI 0.143: https://pypi.org/project/fastapi/
- React 19.3: https://endoflife.date/react
- Vite 8.3: https://vite.dev/blog/announcing-vite8
- SQLAlchemy 2.1: https://www.sqlalchemy.org/download.html
- Playwright 1.64: https://www.npmjs.com/package/playwright
- pytest 9.1: https://pypi.org/project/pytest/
- PyJWT 2.15 / python-jose CVE: https://pypi.org/project/PyJWT/
- Hono 4.13: https://www.npmjs.com/package/hono
- Drizzle 0.45: https://www.npmjs.com/package/drizzle-orm
- Vitest 5.0: https://www.npmjs.com/package/vitest
- ical-generator 11.1: https://www.npmjs.com/package/ical-generator
- jose 6.2: https://www.npmjs.com/package/jose
- APScheduler 3.11: https://pypi.org/project/APScheduler/
- icalendar 7.3: https://libraries.io/pypi/icalendar
- HTMX 4.0: https://four.htmx.org/announcements/2026-08-28-htmx-4.0.0-is-released
- Alpine.js 3.17: https://www.npmjs.com/package/alpinejs
- node-cron 4.6: https://www.npmjs.com/package/node-cron
- Jinja2 3.1.6: https://security.snyk.io/package/pip/jinja2
