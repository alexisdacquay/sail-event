# Tasks — Sail-event

## 1. S4 — Project scaffold with passing test
Goal: Empty repo with both stacks runnable and one passing test per side.
Description: Create `frontend/` with Vite + React 19 + TypeScript + Tailwind + shadcn/ui and one component test. Create `backend/` with a FastAPI hello-world and one pytest test. Add a `Makefile` with targets `run-frontend`, `run-backend`, and `test`. Commit the scaffold with `.gitignore` and `_docs/plan.md`.

## 2. S4 — Criteria editor and dashboard UI
Goal: User can log in, edit criteria, adjust thresholds, and press Search Now — all against a mocked service layer.
Description: Build login/register screens, a criteria free-text editor, upper/lower threshold controls, and a Search Now button in `frontend/src/`. Create a mock service layer in `frontend/src/services/mock.ts` that returns canned data for every backend call. Add component tests for the editor and threshold controls.

## 3. S4 — Event list and approval queue UI
Goal: User can see scored events and accept or reject queued ones.
Description: Add an event-list page and a queue page in `frontend/src/pages/`. Each event card shows title, date, place, score, reason, and status. Queued events have accept/reject buttons. The mock service layer returns a mix of accepted, rejected, and queued events. Add component tests for the event card and queue actions.

## 4. S4 — OpenAPI specification
Goal: A machine-readable contract capturing every endpoint the frontend expects.
Description: Read the frontend's API client in `frontend/src/services/` and write `openapi.yaml` at the repo root. Specify every endpoint, method, path, request/response body, and which endpoints require authentication. The backend will implement this spec at S5.

## 5. S5 — Adapter interfaces and fixture implementations
Goal: Define adapter contracts and their test-mode implementations.
Description: Create `SearchProvider` and `Scorer` interfaces in `backend/adapters/`. Implement `FixtureSearchProvider` (returns canned events) and `FakeScorer` (deterministic score from title hash). Write contract tests in `backend/tests/` verifying both implementations satisfy the interface.

## 6. S5 — FastAPI routers with in-memory store
Goal: Backend serves every endpoint in openapi.yaml with seed data.
Description: Implement routers, Pydantic models, and an in-memory store in `backend/`. Seed the store with one user and sample events. Wire the adapters from task 5 into the search endpoint. Write pytest tests for each router.

## 7. S5 — User authentication
Goal: Registration, login, and protected endpoints with hashed passwords and JWTs.
Description: Add registration and login endpoints in `backend/routers/auth.py`. Hash passwords with bcrypt, issue JWTs with PyJWT, and add a bearer-token dependency that protects all user-specific endpoints. Write pytest tests for registration, login, token validation, and rejection of bad credentials.

## 8. S5 — Connect frontend to real backend
Goal: The app runs end-to-end with frontend calling the real backend.
Description: Replace the mock service layer toggle in `frontend/src/services/` so the frontend calls the real backend when `VITE_API_URL` is set. Update the `Makefile` so `make run` starts both processes with the correct env vars. Verify the login, criteria edit, search-now, and queue flow works manually.

## 9. S6 — ORM models and Alembic setup
Goal: ORM models and migration tooling ready for the database switch.
Description: Define SQLAlchemy ORM models in `backend/models/` for User, Criteria, Event, and Run. Add `UNIQUE(user_id, link)` on Event for dedup, a status enum (new, accepted, rejected, queued), and a check that `lower_threshold < upper_threshold` on User. Configure `DATABASE_URL` env var (SQLite default). Initialise Alembic in `backend/alembic/` and write the initial migration.

## 10. S6 — Swap in-memory store for ORM
Goal: All routers use the database; in-memory store removed.
Description: Replace the in-memory store with SQLAlchemy ORM calls in every router in `backend/routers/`. Run the existing test suite and fix any breakage from the switch. Remove the in-memory store module.

## 11. S6 — Search-run pipeline
Goal: Two endpoints execute the full search, dedup, score, triage cycle and record a Run per user.
Description: Implement `POST /api/search` (single user, bearer auth) and `POST /api/search/all` (all users with criteria, shared-secret header) in `backend/routers/search.py`. Per-user logic: derive queries from criteria, search via adapter, dedup with `ON CONFLICT DO NOTHING`, score leftover `new` events then new events, triage (score > upper -> accepted; < lower -> rejected; otherwise -> queued), write a Run row. Write pytest tests covering dedup, threshold boundaries, `new`-recovery, secret rejection, and Run recording.

## 12. S6 — ICS calendar feed
Goal: Each user has a subscribable calendar feed of accepted events.
Description: Add `GET /api/calendar/{ics_token}` in `backend/routers/calendar.py`. Generate the feed with the `icalendar` library from all accepted events for the user identified by `ics_token` (a per-user secret on the User row). Write tests that the ICS output contains the right VEVENT entries and that an invalid token returns 404.

## 13. S6 — Backend unit tests and single run command
Goal: Full backend test suite, a one-command test runner, and test documentation.
Description: Audit and fill gaps in `backend/tests/`: criteria CRUD, event status transitions, auth edge cases, adapter contract tests for both fixture and fake implementations. Update the `Makefile` so `make test` runs backend and frontend tests with a single exit code. Write `docs/testing.md` covering test categories, how to run, what is covered, and the adapter-stub approach that keeps tests key-free until S13.

## 14. S7 — Dockerfile
Goal: One image that builds the frontend and serves it from the backend.
Description: Write a multi-stage `Dockerfile` at the repo root. Stage 1: Node, build the frontend. Stage 2: Python, copy the backend and the built static files, install dependencies, configure FastAPI to serve the frontend assets. Verify `docker build` and `docker run` serve the app on a single port.

## 15. S7 — Postgres support and docker-compose
Goal: The app runs against Postgres in a single `docker compose up`.
Description: Ensure SQLAlchemy models and Alembic migrations work on Postgres (test `ON CONFLICT` dedup, enum type). Write `docker-compose.yml` with two services: the app image and Postgres 18. Add a healthcheck on the app container. Add `make compose-up` and `make compose-down` to the `Makefile`.

## 16. S7 — Integration and end-to-end tests
Goal: Automated tests run the full stack in containers and verify user journeys.
Description: Write integration tests in `backend/tests/integration/` that run against the docker-compose stack. Write Playwright end-to-end tests in `e2e/` covering: (1) register, set criteria, search, review queue, accept/reject; (2) a second user sees only their own events. Add `make test-e2e` that brings up compose, runs tests, and tears down.

## 17. S8 — Deploy dev environment to AWS
Goal: The app is live at a public URL on a dev EC2 instance.
Description: Write a CloudFormation template in `infra/dev.yaml` that provisions an EC2 instance, installs Docker, pulls the app image, and runs it behind Caddy for TLS. Add `GET /api/health` to the backend. Write `docs/deployment.md` covering: infrastructure, access, SSH, teardown, and the env vars required.

## 18. S9 — CI/CD pipeline with GitHub Actions
Goal: PRs run tests; merges to main deploy to dev automatically; release process documented.
Description: Create `.github/workflows/ci.yml`: backend and frontend tests in parallel, Docker build, integration and e2e tests. Create `.github/workflows/cd.yml`: on push to main, build and push the image, deploy to dev EC2 via SSH or SSM, validate the health endpoint. Use GitHub OIDC for AWS credentials. Fixture adapters in CI; no API keys required. Write `docs/release-process.md` covering branching strategy, PR workflow, CI checks, CD to dev, manual promotion to prod, rollback procedure, and image tagging convention (YYYYMMDD-HHMMSS-shortsha).

## 19. S13 — Real search provider adapter
Goal: A web-search provider returns real event candidates, toggled by env var.
Description: Implement a real `SearchProvider` in `backend/adapters/search_real.py` that calls a web-search API. Parse results into `RawEvent` objects. Select between fixture and real via `SEARCH_PROVIDER` env var. Write tests with recorded HTTP responses (no live API call in CI). Update `docs/deployment.md` with the required API key.

## 20. S13 — Real scorer adapter
Goal: An LLM scores events against user criteria, toggled by env var.
Description: Implement a real `Scorer` in `backend/adapters/scorer_real.py` that sends each event and the user's criteria to an LLM and parses a structured (score, reason) response. Select between fake and real via `SCORER` env var. Write tests with recorded LLM responses. Key-less mode (fake scorer) remains the CI default. Update `docs/deployment.md` with the required model API key.

## 21. S10 — Production environment and manual promotion
Goal: A separate prod EC2 runs the app; promotion from dev is manual.
Description: Add `infra/prod.yaml` CloudFormation template for the prod EC2 (Caddy, Postgres, secrets via AWS SSM). Create `.github/workflows/promote.yml`: manually triggered, deploys a tagged image to prod, validates the health endpoint. Prod enables the real adapters built at S13 via env vars; dev and CI keep the fixtures.

## 22. S10 — Hourly trigger
Goal: EventBridge triggers the search for every user on an hourly schedule.
Description: Add an EventBridge schedule rule in `infra/dev.yaml` and `infra/prod.yaml` calling `POST /api/search/all` every hour with the shared-secret header. Store the secret in AWS SSM. Write a test in `backend/tests/` that a call to `/api/search/all` without the correct header is rejected.

## 23. S11 — OpenTelemetry instrumentation
Goal: The search-run journey carries a trace with metrics and logs sharing a trace ID.
Description: Add the OTel SDK to `backend/telemetry.py`. Instrument the search-run pipeline: one span per step (search, dedup, score, triage), counters for events_found and events_new, structured log lines with the trace ID. Tag every signal with service name, environment, and version.

## 24. S11 — Observability stack and dashboard
Goal: Grafana shows the search-run journey with traces, metrics, and logs.
Description: Add `observability/docker-compose.yml` with OTel Collector, Prometheus, Loki, Tempo, and Grafana. Configure the collector to receive from the app and route to each store. Build a Grafana dashboard for the search-run journey: request rate, error rate, latency histogram, trace-to-logs drill-down.

## 25. S12 — Alert on failed or empty search run
Goal: An actionable alert fires when a search run fails or returns zero new events.
Description: Add a Grafana alert rule on the search-run error counter and on `events_new == 0` sustained beyond a threshold. The notification includes: threshold, duration, service, environment, version, owner, and dashboard URL. Route to a webhook. Write alert definitions in `observability/alerts/`.

## 26. S12 — On-call responder agent
Goal: A headless agent investigates alerts and either fixes the bug or reports a false positive.
Description: Create the responder prompt in `incident-response/responder.md` using the course on-call prompt. Wire the Grafana webhook to a separate incident-response service listening on port 8001 at `POST /alerts`. The responder reads code, reproduces the failure, applies the smallest fix, runs tests, and commits — or explains the false positive. Introduce a test bug to verify the loop.

## 27. S12 — Security audit and operations documentation
Goal: Security audit, operations report, and AI usage report.
Description: Run Semgrep against `backend/` and `frontend/`. Model-review auth, JWT handling, ICS token secrecy, and input validation. Write `docs/operations-and-security-report.md` covering: Semgrep results, model-review findings, human dispositions, capability table, autonomy policy, and escalation path. Fix any critical findings. Write `docs/ai-usage-report.md` covering which agents and roles were used, what they did well, where they needed correction, and lessons learned.

## 28. S14 — Agent extension pack (optional)
Goal: Course lesson-5 deliverables: one skill, one subagent, one MCP server, one hook.
Description: Create a project skill in `.agents/skills/` for the search-run pipeline. Define a subagent in `.agents/agents/` for the QA role. Add one MCP server and one hook relevant to the project workflow. Update `AGENTS.md`. This task is optional and scores zero course points.
