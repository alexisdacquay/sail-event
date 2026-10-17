# Release process

## Branching

Trunk-based development. All work lands on `main` via pull request.

## CI checks

`.github/workflows/ci.yml` runs on every PR to `main` and every push to `main`.

| Job | What it runs |
|---|---|
| backend | `uv sync --frozen`, `uv run pytest` (unit only; integration excluded via `addopts`) |
| frontend | `npm ci`, `npm test`, `npm run build`, `npx @redocly/cli lint openapi.yaml` |
| integration | `docker compose up --build`, `make test-integration`, `make test-e2e` (Playwright/Chromium) |

`backend` and `frontend` run in parallel. `integration` runs after both pass.

## CD to dev on merge

On merge to `main`, build the container image and deploy to the dev environment. Not yet automated — lands with #29 and #17.

## Manual promotion to prod

Tag the image and deploy to production via manual workflow dispatch. Not yet automated — lands with #21.

## Rollback

Redeploy the previous image tag.

## Scheduled search

`.github/workflows/hourly-search.yml` runs `POST /api/search/all` every hour (`:07`). It also supports manual dispatch.

**Setup** (one-time per environment):

```bash
# Point the workflow at your deployment
gh variable set SAIL_BASE_URL --body "https://your-host.example.com"

# Set the shared API key (must match SEARCH_ALL_API_KEY on the server)
gh secret set SEARCH_ALL_API_KEY
```

If `SAIL_BASE_URL` is not set, the workflow exits cleanly — safe to merge before any deployment exists.

**Manual trigger and logs:**

```bash
gh workflow run hourly-search.yml
gh run list --workflow=hourly-search.yml
```

## Tag convention

`YYYYMMDD-HHMMSS-shortsha` (e.g. `20261016-143022-a1b2c3d`).
