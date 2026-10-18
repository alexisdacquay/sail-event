# Testing

Three layers: unit, integration, end-to-end.

## Unit tests

Backend tests live in `backend/tests/`. They cover auth, criteria, events,
calendar, pipeline, ORM, adapters, thresholds, and schema contract.

Frontend component tests sit beside their source files in `frontend/src/`.

```
make test
```

Runs backend then frontend. Does not start Docker. Exits non-zero if either
fails. Integration tests are excluded by default (`-m "not integration"` in
pyproject.toml).

## Integration tests

Live in `backend/tests/integration/`. Pure HTTP tests against the compose
stack — no app internals imported. Marked `@pytest.mark.integration`.

Scenarios: health, full user journey (register → search → decide → re-fetch),
dedup, user isolation, search/all, ICS feed, data survives restart.

```
HOST_PORT=8010 make test-integration
```

The target:
1. `docker compose up --build -d --wait` (reads `HOST_PORT`, default 8000)
2. Runs pytest on `backend/tests/integration/` with `-m integration`
3. `docker compose down -v`
4. Exit code = pytest exit code

To run against an already-running stack (skips compose lifecycle):

```
SAIL_BASE_URL=http://localhost:8010 make test-integration
```

When `SAIL_BASE_URL` is set, `test_data_survives_restart` is skipped by
default because the caller may not own the compose stack. Set
`SAIL_COMPOSE_MANAGED=1` to signal that container restarts are safe:

```
SAIL_BASE_URL=http://localhost:8010 SAIL_COMPOSE_MANAGED=1 make test-integration
```

## End-to-end tests (Playwright)

Live in `e2e/` at the repo root with their own `package.json`.
Chromium only.

**First-time setup:**

```
cd e2e && npm install && npx playwright install chromium
```

**Run:**

```
HOST_PORT=8010 make test-e2e
```

The target:
1. `docker compose up --build -d --wait`
2. Runs `npx playwright test` in `e2e/`
3. `docker compose down -v`
4. Exit code = Playwright exit code

Journeys:
- Journey 1: register, set criteria, search, queue accept/reject, verify events page
- Journey 2: second user sees no events from first user

To run against an already-running stack:

```
SAIL_BASE_URL=http://localhost:8010 make test-e2e
```

## Real adapters

To smoke-test the Tavily adapter against the live API (not run in CI):

```
SEARCH_PROVIDER=tavily TAVILY_API_KEY=... uv run python -m app.adapters.search_tavily "sailing regattas 2026"
```

CI stays fixture-only; `make test` never hits the network.

To smoke-test the Claude scorer adapter against the live API (not run in CI):

```
SCORER=claude ANTHROPIC_API_KEY=... uv run python -m app.adapters.scorer_claude "<criteria>"
```

Scores one hard-coded fixture event, prints score and reason. CI stays fixture-only.

## Adapter-stub approach

`FixtureSearchProvider` returns canned events from `fixtures.json`.
`FakeScorer` produces a deterministic score via `md5(title) mod 101`.

These stubs keep tests key-free and offline through S12. Env vars
`SEARCH_PROVIDER` and `SCORER` toggle real implementations (S13);
fixture/fake are the default when unset.
