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

Render service `sail-event-dev` builds the root `Dockerfile` and deploys on every push to `main` (auto-deploy, trigger: commit). See `docs/deployment.md`.

## Manual promotion to prod

`.github/workflows/promote.yml`, run by hand from the Actions tab (or `gh workflow run promote.yml -f sha=<full sha>`). It calls the prod service's deploy hook with `ref=<sha>`, then polls `GET /api/health` until prod reports that commit (`commit` field, from Render's `RENDER_GIT_COMMIT`) with status ok, or fails after 10 minutes. Prod (`sail-event`) has auto-deploy off; nothing reaches it except this workflow.

Setup (one-time): secret `RENDER_PROD_DEPLOY_HOOK` = the Deploy Hook URL from Render → sail-event → Settings; variable `SAIL_BASE_URL` = the prod URL.

## Rollback

Run the promote workflow with the previous commit's SHA.

## Scheduled search

`.github/workflows/hourly-search.yml` runs `POST /api/search/all` every hour (`:07`). It also supports manual dispatch.

**Setup** (one-time per environment):

```bash
# Point the workflow at your deployment
gh variable set SAIL_BASE_URL --body "https://sail-event.onrender.com"

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
