# Phase plan v2 (2026-10-16) — supersedes the table in ASSESSMENT-scope.md

## Rubric as of 2026-10-16 (changed since 2026-10-15; 12 criteria, 24 pts, pass = 10)

| # | Criterion | Pts | Lesson | Gone from the old draft |
|---|---|---|---|---|
| 1 | Problem description | 2 | 1 | |
| 2 | Product spec + public task tracker with acceptance criteria, agents used it | 2 | 1 | |
| 3 | Agent team: roles + process | 2 | 1 | new |
| 4 | Context: AGENTS.md pointing to modular docs | 2 | 1 | new |
| 5 | Application: frontend + backend + DB, single local command | 2 | 2 | OpenAPI, frontend tests no longer scored |
| 6 | Testing: unit + integration, single command | 2 | 2–3 | |
| 7 | Containerization incl. DB, single command | 2 | 3 | |
| 8 | Deployment: public URL or clear demo | 2 | 3 | |
| 9 | CI/CD: CI on PR / CD / manual prod | 3 | 3–4 | |
| 10 | Observability: one journey, metrics+traces+logs sharing a trace id, UI | 2 | 4 | |
| 11 | Alert | 1 | 4 | |
| 12 | On-call agent fixes on alert | 2 | 4 | |
| — | agent extension pack (lesson 5) | 0 | 5 | removed |
| — | security audit, reproducibility, DB multi-env | 0 | — | removed |

Guidance on the page: ~20 hours, "a small idea is fine", one app taken all the way.

## Overload check on plan v1

| v1 phase | Criteria carried | Pts | Verdict |
|---|---|---|---|
| P1 | 1, 2, 3, 4 | 8 | heavy but doc-only; v1 wrongly treated it as done |
| P2 | 5, half of 6 | 3 | fine |
| P3 | 6, 7, 8, 9 | 9 | overloaded: 37% of all points in one phase |
| P4 | 9(part), 10, 11, 12 | 6 | overloaded |
| P5 | none | 0 | waste under the new rubric |

## Plan v2: one or two criteria per step

| Step | Lesson | Criterion (pts) | Deliverable | Cum. pts |
|---|---|---|---|---|
| S1 | 1 | 1 (2) | README problem section; plan.md ✓ | 2 |
| S2 | 1 | 2 (2) | stack options → tasks.md → GitHub issues with acceptance criteria | 4 |
| S3 | 1 | 3 (2), 4 (2) | AGENTS.md, process.md, task-template.md, team/pm, swe, qa | 8 |
| S4 | 2 | 5 (part) | frontend with mocked service layer; openapi.yaml | 8 |
| S5 | 2 | 5 (part) | FastAPI, in-memory store, auth; frontend connected | 8 |
| S6 | 2 | 5 (2), 6 (1) | SQLite via SQLAlchemy; unit tests; one run command | 11 → pass |
| S7 | 3 | 6 (2), 7 (2) | Postgres, compose, integration tests, one test command | 14 |
| S8 | 3 | 8 (2) | deployed to a public URL (dev) | 16 |
| S9 | 3 | 9 (2) | CI on PR, CD to dev on main | 18 |
| S10 | 4 | 9 (3) | prod copy; manual promotion workflow | 19 |
| S11 | 4 | 10 (2) | OTel on the search→queue journey; collector, Grafana | 21 |
| S12 | 4 | 11 (1), 12 (2) | alert on failed/empty run; headless responder | 24 |
| S13 | — | 0 | real search provider + real scorer behind flags, key-less mode kept | 24 |
| S14 | 5 | 0 | agent pack: skill, subagent, MCP, hook — optional | 24 |

Mock boundary: S4–S12 run on a fixture provider and a deterministic fake scorer.

## v3 (2026-10-16): same 14 steps; unscored practices attached; sources judged

### Practices dropped from the rubric, kept as practice (no new steps)

| Practice | Why keep | Attached to |
|---|---|---|
| OpenAPI contract, frontend built on it | lesson 2 method; backend has a precise target | S4 |
| Frontend tests | catches the service-layer swap | S6 |
| DB agnostic via env var (SQLite ↔ Postgres) | lesson 2 prompt says so; S7 needs it | S6 → S7 |
| Reproducibility doc: setup, run, test, deploy | reviewers must run it | S8, S9 |
| Security audit: Semgrep + model review, human disposition | lesson 4 module deliverable | S12 |
| Agent extension pack | lesson 5 deliverable | S14, optional |

### Sources suggested by the user

| Source | What it is | Verdict | Where |
|---|---|---|---|
| humanlayer/12-factor-agents | 12 principles for production LLM software (own prompts, tools = structured outputs, own control flow, stateless reducer) | use as design reference, not a checklist | S12 responder, S13 scorer |
| DietrichGebert/ponytail | coding-agent skill: write only what the task needs; `/ponytail-review`, `/ponytail-audit` | install at project scope; it enforces "less is more" in code | S4–S13 |
| Sorbh/interview-me | spec interview skill + spec-vs-code drift check | skip now: the brainstorm is done and the PM role grooms tasks; `--verify` maybe later | — |

Against ponytail: it is a sixth plugin after the five of yesterday. If one must go, drop feature-dev (overlaps with the course's PM/engineer roles).

### Open

- S13 position: end (as placed) or after S6
- S14: do at all
- install ponytail at project scope: yes / no
