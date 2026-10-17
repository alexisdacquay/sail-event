# Deploy — Render (replaces AWS, decided 2026-10-16)

## Why
- AWS IAM setup cost too high for one-person project
- Render: no IAM, managed Postgres with PITR, deploy on push

## What exists on Render (workspace: Alexis's workspace, region: Frankfurt)
| Render object | id | notes |
|---|---|---|
| Postgres `sail-event-db` | dpg-db9gpa3bc2fs73do1jc0-a | Basic, Postgres 18, PITR on, HA off, inbound 0.0.0.0/0 |
| Web Service `sail-event` | srv-db9o8e6q1p3s739001d0 | Docker, branch main, auto-deploy on commit, plan 0.5c-512mb, port 8000 |
| URL | https://sail-event.onrender.com | first deploy 2026-10-17, commit b6ec32f |

## Env vars on the Web Service (values live in Render, never here)
DATABASE_URL  postgresql+psycopg://… (Render gives postgresql://, prefix changed)
APP_ENV       prod
PORT          8000
JWT_SECRET    Render-generated
SEARCH_ALL_API_KEY  Render-generated; same value in GitHub Actions secret

## Done
- [x] first deploy green 2026-10-17: health 200, SPA 200, DB login 401, search/all no-key 401
- [x] DB credential rotated 2026-10-17: new default `saileventdb_bf45_user`, DATABASE_URL updated, redeploy green
- [x] hourly search: GitHub Actions `hourly-search.yml` (not a Render cron); repo var `SAIL_BASE_URL` + secret `SEARCH_ALL_API_KEY` set; manual run 39072719769 passed, usersProcessed 0
- [x] Render MCP connector authorised 2026-10-17 (read service, set env vars)
- [x] no CloudFormation/EventBridge files existed in the repo; only doc rows to fix

## Not done yet
- [ ] delete old DB user `sail_event_db_user` (Credential Rotation, bin icon) once it shows 0 open connections — user
- [ ] health check path on the web service is empty in Render Settings; set to `/api/health` — user
- [ ] SEARCH_PROVIDER=tavily + TAVILY_API_KEY; SCORER=claude + ANTHROPIC_API_KEY — keys are the user's
- [ ] DB inbound 0.0.0.0/0: restrict or accept (Render services reach it on the internal host anyway)
- [ ] docs updated for Render (architecture.md, release-process.md, new docs/deployment.md) — in working tree, commit on word
- [ ] issues #17 and #29: close as done on Render; #21 (separate prod + manual promotion) stays open
