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

## Tag convention

`YYYYMMDD-HHMMSS-shortsha` (e.g. `20261016-143022-a1b2c3d`).
