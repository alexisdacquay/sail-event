# Rubric reviews (blind peers, see .claude/skills/rubric-review/SKILL.md)

## 2026-10-20 8df755d (prod b57bbaa) — A 24/24 · B 24/24 · C 24/24 · merged 24/24

Reviewers: A strict grader (evidence only, live API search as a throwaway user), B fifteen-minute README reader (15 tool calls), C hands-on runner (ran every README command on its own compose project and ports, real search locally and on prod).

| # | Criterion | A | B | C | min | gap / note |
|---|---|---|---|---|---|---|
| 1 | Problem description | 2 | 2 | 2 | 2 | |
| 2 | Spec + tracker + agents used it | 2 | 2 | 2 | 2 | issues #5 #18 #25 #63 checked: groom, commit, QA verdict |
| 3 | Agent team roles + process | 2 | 2 | 2 | 2 | |
| 4 | AGENTS.md modular context | 2 | 2 | 2 | 2 | |
| 5 | App: FE + BE + DB, one command | 2 | 2 | 2 | 2 | C: clone to working search in 4 min |
| 6 | Tests: unit + integration, one command | 2 | 2 | 2 | 2 | C: 365 + 80 + 19 unit, 7 integration green |
| 7 | Containers incl. DB, one command | 2 | 2 | 2 | 2 | |
| 8 | Deployment public URL | 2 | 2 | 2 | 2 | A and C ran real searches on prod (Tavily + DeepSeek) |
| 9 | CI/CD: PR CI, CD, manual promote | 3 | 3 | 3 | 3 | |
| 10 | Observability journey + UI | 2 | 2 | 2 | 2 | B: a visible single-trace walkthrough would remove doubt; C: collector port 4318 hardcoded → fixed same day (env override) |
| 11 | Alert | 1 | 1 | 1 | 1 | |
| 12 | On-call agent | 2 | 2 | 2 | 2 | A: incident was a staged fault (README says so, line "deliberate fault") |

risks (A): observability local-only (README line added), staged incident (already stated in README), cold start (false: paid instances, 0.4 s health; README line added).
failed commands (C): `make up-all` when port 4318 is busy → `OTEL_COLLECTOR_PORT` override added to observability/docker-compose.yml.
lost (B): nowhere; fastest convincer: the recorded incident folder.
issues filed: none (no point at stake); the three fixes landed in the same commit as this log.

## 2026-10-21 571b751 — ruthless examiner (Fable): 17 → 22 → 24/24
Three literal, run-everything passes over two days drove the fixes in PRs 88-93 and the real recorded incident. Full tables in work/EXAMINER-2026-10-20.md.
