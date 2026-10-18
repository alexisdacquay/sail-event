Event finder: scores web-search results against a user's free-text criteria,
triages by threshold, and publishes accepted events to a per-user ICS feed.

Documents

- `_docs/plan.md` - what the product does
- `_docs/architecture.md` - how it is built
- `_docs/process.md` - how work is organised
- GitHub issues at github.com/alexisdacquay/sail-event/issues - the backlog; issue N = task N of the original `_docs/outdated/tasks.md`

Commands

These targets exist once task 1 (project scaffold) and later Makefile tasks land:

- `make run` - start frontend and backend
- `make test` - backend and frontend tests, single exit code
- `make test-e2e` - bring up compose, run Playwright, tear down
- `make compose-up` - app + Postgres via docker-compose

Setup

- Run `make hooks` after cloning to install the pre-commit hook. Agent worktrees share `.git/hooks` from the main clone, so the hook applies there too.
- The QA subagent is defined at `.claude/agents/qa-engineer.md`

Rules

- Python dependencies: uv. Frontend dependencies: npm
- Dependencies are pinned exactly. Do not add one without approval
- Configuration comes from environment variables, never hardcoded
- Backend tests live in `backend/tests/`. Frontend tests live beside
  their components
- Commit after every completed task
- Search provider and scorer are adapter interfaces selected by env var
  (`SEARCH_PROVIDER`, `SCORER`). Fixture implementations are the default;
  real implementations are toggled on in prod
