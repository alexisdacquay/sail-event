# Testing

## Unit tests

Backend tests live in `backend/tests/`. They cover:

- **Auth** — register, login, token lifecycle, cross-user isolation, malformed tokens
- **Criteria** — CRUD, upsert, fresh-user defaults
- **Events** — listing, filtering, decision logic, status transitions, cross-user isolation
- **Calendar** — ICS feed generation, content-type, DTSTAMP, bad date handling, empty feeds
- **Pipeline** — derive_queries, search-run lifecycle, dedup, cap, failure recording, recovery
- **ORM** — uniqueness constraints, threshold check constraints, status enum
- **Adapters** — fixture search provider and fake scorer contracts
- **Thresholds** — get/put, validation

Run them:

```
cd backend && uv run pytest
```

## Frontend tests

Frontend component tests sit beside their source files in `frontend/src/`.

```
cd frontend && npm test
```

## Running all

```
make test
```

Runs backend then frontend. Exits non-zero if either fails.

## Adapter-stub approach

`FixtureSearchProvider` returns canned events from `fixtures.json`.
`FakeScorer` produces a deterministic score via `md5(title) mod 101`.

These stubs keep tests key-free and offline through S12. Env vars
`SEARCH_PROVIDER` and `SCORER` toggle real implementations (S13);
fixture/fake are the default when unset.
