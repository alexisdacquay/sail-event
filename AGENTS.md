Event finder: scores web-search results against a user's free-text criteria,
triages by threshold, and publishes accepted events to a per-user ICS feed.

Documents

Product and design
- [`_docs/plan.md`](_docs/plan.md) - what the product does and why (PRD)
- [`_docs/architecture.md`](_docs/architecture.md) - how it is built
- [`_docs/search-spec.md`](_docs/search-spec.md) - search quality targets
- [`_docs/ux-spec.md`](_docs/ux-spec.md) - screens and user jobs
- [`_docs/ui-design.md`](_docs/ui-design.md) - UI decisions (what, why, where); mockups in [`_docs/ui/`](_docs/ui/)

Process and team
- [`_docs/process.md`](_docs/process.md) - the agent team, how work flows, handoffs, the root-cause gate
- [`_docs/team/pm.md`](_docs/team/pm.md), [`_docs/team/software-engineer.md`](_docs/team/software-engineer.md), [`_docs/team/qa-engineer.md`](_docs/team/qa-engineer.md) - one file per role
- [`_docs/task-template.md`](_docs/task-template.md) - the four sections of a groomed issue
- GitHub issues at https://github.com/alexisdacquay/sail-event/issues - the backlog; issue N = task N of the original [`_docs/outdated/tasks.md`](_docs/outdated/tasks.md)

Run, test, ship
- [`docs/testing.md`](docs/testing.md), [`docs/deployment.md`](docs/deployment.md), [`docs/release-process.md`](docs/release-process.md), [`docs/api.md`](docs/api.md)
- [`openapi.yaml`](openapi.yaml) - the API contract
- [`observability/README.md`](observability/README.md) - metrics, logs, traces, alerts
- [`incident-response/README.md`](incident-response/README.md) - the on-call agent

Agents and tools
- [`.claude/agents/qa-engineer.md`](.claude/agents/qa-engineer.md) - the QA subagent
- [`.claude/skills/rubric-review/SKILL.md`](.claude/skills/rubric-review/SKILL.md), [`.claude/skills/status-update/SKILL.md`](.claude/skills/status-update/SKILL.md), [`.claude/skills/field-test/SKILL.md`](.claude/skills/field-test/SKILL.md), [`.claude/skills/reviewer-guide/SKILL.md`](.claude/skills/reviewer-guide/SKILL.md) (rebuilds [`docs/reviewer-guide.md`](docs/reviewer-guide.md))

State and history
- [`work/STATE.md`](work/STATE.md) - read the top block for where work stands
- [`work/`](work/) - logs, batch results, reviews; not instructions
- [`_docs/outdated/`](_docs/outdated/) - history only

Commands

- `make run` - start frontend and backend
- `make test` - backend and frontend tests, single exit code
- `make test-all` - unit + integration + e2e, single exit code (needs Docker)
- `make test-e2e` - bring up compose, run Playwright, tear down
- `make compose-up` - app + Postgres via docker-compose

Setup

- Run `make hooks` after cloning to install the pre-commit hook. Agent worktrees share `.git/hooks` from the main clone, so the hook applies there too.
- The QA subagent is defined at `.claude/agents/qa-engineer.md`
- Owner status updates follow `.claude/skills/status-update/SKILL.md` (`/status-update`)

Rules

- Python dependencies: uv. Frontend dependencies: npm
- Dependencies are pinned exactly. Do not add one without approval
- Configuration comes from environment variables, never hardcoded
- Backend tests live in `backend/tests/`. Frontend tests live beside
  their components
- Commit after every completed task
- Adapters are interfaces selected by env var
  (`SEARCH_PROVIDER`, `LLM_PROVIDER`, `GUARDRAIL`). Fixture implementations
  are the default; real implementations are toggled on in prod
