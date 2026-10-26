# Testing

Three layers: unit, integration, end-to-end.

## At a glance

```
make test-all      # unit + integration + e2e, one exit code, needs Docker
```

| Layer | Count | Command | Runs in CI |
|---|---|---|---|
| Backend unit | 481 | `make test` | `backend` job |
| Frontend unit | 117 (12 files) | `make test` | `frontend` job |
| On-call responder unit | 20 | `make test` | no (local only) |
| Integration (HTTP against the compose stack) | 7 | `make test-integration` | `integration` job |
| End-to-end (Playwright, Chromium) | 12 | `make test-e2e` | `integration` job |

Verified on commit `8305160`, CI run [40242394581](https://github.com/alexisdacquay/sail-event/actions/runs/40242394581); responder count from `python3 incident-response/test_responder.py`.

**Unit** = one function or component, recorded fixtures, no network.
Many backend unit tests also go through the routes and the ORM in-process (FastAPI TestClient into SQLite), e.g. `test_events.py`, `test_pipeline.py`, `test_auth.py`.
**Integration** = the built container plus Postgres, called over HTTP only; no app code imported.

**Needs:** uv, Node 22+, python3; Docker for integration and e2e.
**No API keys:** search and model are recorded fixtures with a fixed clock (`FAKE_NOW`).
**Time:** the backend suite takes about 5 minutes (312 s in CI); integration and e2e add about 3-5 minutes, most of it the image build.
`make test-all` runs `test`, then `test-integration`, then `test-e2e`; make stops at the first failure.

## Unit tests

Backend tests live in `backend/tests/`. They cover auth, criteria, events,
calendar, pipeline, ORM, adapters, thresholds, and schema contract.

Frontend component tests sit beside their source files in `frontend/src/`.

```
make test
```

Runs backend, then frontend, then the on-call responder tests (`incident-response/test_responder.py`). Installs frontend packages on a fresh clone. Does not start Docker. Exits non-zero if any
fails. Integration tests are excluded by default (`-m "not integration"` in
pyproject.toml).

## Integration tests

Live in `backend/tests/integration/`. Pure HTTP tests against the compose
stack — no app internals imported. Marked `@pytest.mark.integration`.

Scenarios: health, full user journey (register → search → decide → re-fetch),
dedup, user isolation, search/all, ICS feed, data survives restart.

```
make test-integration
```

The target uses `TEST_HOST_PORT` (default 8030) and `TEST_COMPOSE_PROJECT`
(default `sail-test`). Override either to avoid clashes with a running stack:

```
TEST_HOST_PORT=8031 TEST_COMPOSE_PROJECT=sail-test-2 make test-integration
```

Steps:
1. `docker compose up --build -d --wait` under `COMPOSE_PROJECT_NAME=$TEST_COMPOSE_PROJECT`
2. Runs pytest on `backend/tests/integration/` with `-m integration`
3. `docker compose down -v` (same project name)
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

**First-time setup:** none. `make test-e2e` installs `e2e/` packages and Chromium when they are missing.

**Run:**

```
make test-e2e
```

The target uses the same `TEST_HOST_PORT` and `TEST_COMPOSE_PROJECT` variables
as `test-integration`:
1. `docker compose up --build -d --wait` under `COMPOSE_PROJECT_NAME=$TEST_COMPOSE_PROJECT`
2. Runs `npx playwright test` in `e2e/`
3. `docker compose down -v` (same project name)
4. Exit code = Playwright exit code

12 tests in three files:

| File | Tests | What |
|---|---|---|
| [journeys.spec.ts](../e2e/journeys.spec.ts) | 4 | Journey 1: register, save a threshold (persists after reload), search, add to calendar and reject from the stream; phone layout; light and dark screenshots. Journey 2: second user sees no events from the first |
| [field.spec.ts](../e2e/field.spec.ts) | 6 | U1-U4 from field tests: reload keeps the result, the Judged line matches the rows, slider equals the boxes, legend not clipped, copy feedback, the feed link is a `webcal:` subscription |
| [screenshot-122.spec.ts](../e2e/screenshot-122.spec.ts) | 2 | live progress line mid-run, light and dark |

The screenshot tests write PNGs to `e2e/test-results/` (e.g. `stream-desktop-light.png`, `funnel-light.png`).

To run against an already-running stack:

```
SAIL_BASE_URL=http://localhost:8010 make test-e2e
```

## Field-test runner (four phases against a deployed service)

One runner, four cumulative phases:

```
SSL_CERT_FILE=$(uv run --project backend python -m certifi) \
  uv run --project backend python backend/tests/field/runner.py \
    --base-url https://sail-event.onrender.com --phase 4
```

| Phase | What | Time |
|-------|------|------|
| 1 | Invariants battery (13 checks, personas from `personas.yaml`) | 5 min |
| 2 | Regression tests (`backend/tests/regression/`, offline fixtures) | <1 min |
| 3 | Breadth batch (20 dissimilar search texts, 10 in parallel) | 5 min |
| 4 | Recall ground truth (38 events from `triples.json`) | 10 min |

`--phase N` runs phases 1..N.  Each run appends numbers and deltas against
the last committed run to `work/RUN-LOG.md`.

Prod allows 5 registrations per IP per hour, so the first prod run creates
the users over a few hours; later runs reuse them and the "already known"
count shows the dedup at work. Dev has the limit raised.

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

The integration and e2e users register without a time zone and default to
UTC, so every re-recording must be done for both `--tz Europe/Berlin`
(unit tests) and `--tz UTC` (integration/e2e).

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
