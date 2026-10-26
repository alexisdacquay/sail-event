# Testing

The default suites use recordings and a fixed clock. They need no provider keys. Live field tests and adapter smoke runs are separate owner tools and spend provider credits.

## At a glance

```bash
make test-all      # in-process + integration + e2e; needs Docker
```

| Layer | Command | CI |
|---|---|---|
| Backend in-process | `make test` | `backend` job |
| Frontend components | `make test` | `frontend` job |
| HTTP integration against app + Postgres | `make test-integration` | `integration` job |
| Browser journeys, UI checks and screenshots | `make test-e2e` | `integration` job |

“In-process” includes functions, components and API routes through FastAPI TestClient with SQLite. Integration tests call the built app over HTTP without importing its internals. Browser tests use Chromium.

Needs: uv, Python 3.12+, Node/npm (Node 24 in `.nvmrc`; CI uses 22), and Docker for integration/e2e. Run `make test-all` without `-j` to execute the targets in order and stop at the first failure. Targets and CI wiring: [Makefile](../Makefile), [ci.yml](../.github/workflows/ci.yml).

Check counts and outcomes from CI rather than relying on a frozen total:

```bash
gh run list -R alexisdacquay/sail-event --workflow=ci.yml --branch main --limit 3
gh run view <run-id> --log | grep -E 'passed|Test Files|Tests '
```

For a dated example, [run 40251535674](https://github.com/alexisdacquay/sail-event/actions/runs/40251535674) passed on code snapshot `542e58c`. See [End-to-end tests](#end-to-end-tests-playwright) for browser coverage and screenshots.

## Adapter-stub approach

[FixtureProvider](../backend/app/adapters/fixture.py) returns the same recorded search-result pages regardless of query. [FakeLanguageModel](../backend/app/adapters/llm_fake.py) replays answers keyed by prompt name, version and rendered-prompt hash. It fails if a recording is missing. Use the recorded criteria rather than arbitrary text:

> jazz in Berlin (Germany) next week (19-21st October 2026)

`SEARCH_PROVIDER=fixture`, `LLM_PROVIDER=fake` and `GUARDRAIL=none` are defaults. Real implementations are selected through those variables. Backend tests block non-local socket connections ([conftest.py](../backend/tests/conftest.py)).

## Fixed clock

Backend tests and CI use `FAKE_NOW=2026-10-18T12:00:00+02:00`; compose and `make run` default to that value. It stabilizes date-dependent prompts and filters for the recordings. Run timestamps and rate limits still use real UTC. Real-adapter deployments should leave `FAKE_NOW` unset.

The integration HTTP clients omit `timeZone`, so their criteria default to UTC. Playwright sets `timezoneId: Europe/Berlin`, and the UI saves that browser zone with the criteria. Recordings must cover the time zones used by the relevant tests.

## Unit tests

Backend tests in `backend/tests/` cover auth, criteria, events, calendar, pipeline, ORM, adapters, thresholds and the schema contract. Frontend component tests live beside their sources in `frontend/src/`.

```bash
make test
```

Runs backend, frontend, then `incident-response/test_responder.py`. Installs missing frontend packages, starts no Docker stack, and returns non-zero on failure. Pytest excludes integration tests by default. Responder tests use the standard library and do not launch a model agent; run them alone with `python3 -I -B incident-response/test_responder.py`.

## Integration tests

[backend/tests/integration/](../backend/tests/integration/) covers health, the full user journey, duplicates, user isolation, scheduled enqueueing, ICS and data persistence across an app-container restart.

```bash
make test-integration
# Avoid a port/project collision:
TEST_HOST_PORT=8031 TEST_COMPOSE_PROJECT=sail-test-2 make test-integration
```

Without `SAIL_BASE_URL`, the target builds and starts a compose project (default `sail-test`, port 8030), runs pytest with `-m integration`, then tears down that project and its volumes. It returns the pytest exit status. Use a dedicated test project and database.

Against a stack you already own:

```bash
SAIL_BASE_URL=http://localhost:8010 make test-integration
```

This skips compose startup/teardown and normally skips `test_data_survives_restart`. Set `SAIL_COMPOSE_MANAGED=1` only when restarting the app container in your compose project is safe. CI starts compose itself and uses both variables, so its restart check runs.

## End-to-end tests (Playwright)

[e2e/](../e2e/) has its own npm package. Without `SAIL_BASE_URL`, the Make target installs missing packages and Chromium, builds a dedicated compose stack, runs Playwright, and removes that stack and its volumes.

```bash
make test-e2e
```

It shares `TEST_HOST_PORT` and `TEST_COMPOSE_PROJECT` with integration tests. For an existing local stack, install packages and Chromium first; that branch of the target does not install them:

```bash
npm ci --prefix e2e
npm exec --prefix e2e -- playwright install chromium
SAIL_BASE_URL=http://localhost:8010 make test-e2e
```

| File | Coverage |
|---|---|
| [journeys.spec.ts](../e2e/journeys.spec.ts) | Search, threshold persistence, decisions, reload, user isolation, phone layout and desktop screenshots |
| [screenshot-122.spec.ts](../e2e/screenshot-122.spec.ts) | Mid-run progress screenshots in light and dark themes |

Screenshots are written under `e2e/test-results/`.

## Owner tools (live, costs credits)

These commands are outside `make test-all`. Field tests register accounts and change criteria, thresholds and events on the target. Use dedicated test accounts on dev for owner-approved live testing.

<a id="four-phase-field-runner"></a>

## Field-test runner (four phases against a deployed service)

```bash
uv run --project backend python backend/tests/field/runner.py \
  --base-url https://sail-event-dev.onrender.com --phase 4
```

| Phase | Work |
|---|---|
| 1 | Persona battery against the data invariants in [invariants.py](../backend/tests/field/invariants.py) |
| 2 | Local offline regression tests in `backend/tests/regression/` |
| 3 | Breadth batch from `BATCH_TEXTS`, using ten workers |
| 4 | Recall against [triples.json](../backend/tests/ground_truth/triples.json); clears the recall test users’ existing events |

`--phase N` runs phases 1 through N. [runner.py](../backend/tests/field/runner.py) appends results and deltas against the previous log block to [work/RUN-LOG.md](../work/RUN-LOG.md). Records from the earlier separate tools are in [FIELD-TESTS.md](../work/FIELD-TESTS.md), [SEARCH-BATCHES.md](../work/SEARCH-BATCHES.md) and [RECALL.md](../work/RECALL.md).

## Real adapters smoke

[smoke_search.py](../backend/scripts/smoke_search.py) runs the pipeline with a temporary SQLite database: criteria, window, search, extraction, event pages, filtering, judging/triage, duplicate checking and persistence. Search submits the criteria text plus ` event`.

Configure the shell with `SEARCH_PROVIDER` (`exa`, `tavily` or `brave`), the matching provider key (`EXA_API_KEY`, `TAVILY_API_KEY` or `BRAVE_API_KEY`), and `LLM_PROVIDER=openai_compatible`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`, `LLM_JSON_MODE`. The tool inserts criteria into its temporary database. The [criteria endpoint tests](../backend/tests/test_guardrails.py) cover guardrail blocking and unavailable-guard responses.

```bash
# Load a locally maintained, git-ignored environment file if you use one:
set -a
. backend/.env.local
set +a
uv run --project backend python backend/scripts/smoke_search.py \
  --criteria "jazz in Berlin" --tz Europe/Berlin
```

Use `--repeat 3` to inspect score variation. At the `542e58c` code snapshot ([CI run](https://github.com/alexisdacquay/sail-event/actions/runs/40251535674)), `--batch` runs twenty entries with five workers and prints a Markdown report. The field runner uses ten workers. Check with `git grep -nE "BATCH_TEXTS|ThreadPoolExecutor|max_workers|--batch" -- backend/scripts/smoke_search.py backend/tests/field/runner.py`.

`--record` writes model responses into `backend/tests/fixtures/llm/`. Set the fixed clock and use the exact criteria and time zone required by the tests. Review the recordings before committing them; live answers and web results vary.
