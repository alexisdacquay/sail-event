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

## Real adapters smoke

`backend/scripts/smoke_search.py` runs the full pipeline (criteria parse,
window, plan, search, extract, filter, judge) against live adapters using a
throwaway SQLite database (never touches the dev database).

**Single criteria:**

```
set -a; . backend/.env.local; set +a
SSL_CERT_FILE=$(uv run --project backend --directory backend python -m certifi) \
  uv run --project backend --directory backend python scripts/smoke_search.py \
    --criteria "jazz in Berlin (Germany) next week (19-21st October 2026)" \
    --tz Europe/Berlin
```

**Score spread (consistency check):**

```
uv run --project backend --directory backend python scripts/smoke_search.py \
    --criteria "jazz in Berlin" --tz Europe/Berlin --repeat 3
```

**Record model responses as fixtures:**

```
FAKE_NOW=2026-10-18T12:00:00+02:00 \
  uv run --project backend --directory backend python scripts/smoke_search.py \
    --criteria "jazz in Berlin (Germany) next week" --tz Europe/Berlin --record
```

Writes to `backend/tests/fixtures/llm/` under the same hash the
`FakeLanguageModel` replays. Set `FAKE_NOW` so hashes match test
expectations.

**Batch suite (10 texts):**

```
uv run --project backend --directory backend python scripts/smoke_search.py --batch
```

Prints a Markdown table: text, status, stage counts, calls, seconds, top 3
kept events.

**Environment:** keys (`TAVILY_API_KEY`, `LLM_BASE_URL`, `LLM_API_KEY`,
`LLM_MODEL`, `LLM_JSON_MODE`, `GUARDRAIL`) come from `backend/.env.local`
(git-ignored). Set `GUARDRAIL=none` until the Lakera adapter is wired.

CI stays fixture-only; `make test` never hits the network.

## Adapter-stub approach

`FixtureProvider` returns canned events from `fixtures.json`.
`FakeLanguageModel` replays recorded responses keyed by prompt hash.

These stubs keep tests key-free and offline. Env vars
`SEARCH_PROVIDER` and `LLM_PROVIDER` toggle real implementations;
fixture/fake are the default when unset.

## Fixed clock

All tests, CI, compose and the dev service run with
`FAKE_NOW=2026-10-18T12:00:00+02:00` so that fixture recordings and
date-dependent filters produce stable results. Production never sets
`FAKE_NOW`.
