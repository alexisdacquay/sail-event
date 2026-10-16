# Is Sail-event too ambitious? (2026-10-16)

## Evidence: 2025 cohort, top-scored projects
Source: courses.datatalks.club/ai-dev-tools-2025/project/{project1,project2}/list,
50 repos listed at 25-26/26, 49 READMEs read (6 repos deleted/private).
- 2025 rubric max 26; the 2026 draft adds 2 criteria (agent pack, security/ops) -> 30.
- what scored 26: habit tracker, vacation manager, quote keeper, expense tracker,
  meeting decision tracker, diary, memory game, tower defense, world-cup predictor.
  mostly 2-4 entities, CRUD, no run-time external dependency.
- also 26 with external API + LLM + scheduler: trip-weaver (LLM, cron, external
  API), VeriHub (recurring LLM audits), data-cleaning assistant (LLM, cron), habit
  tracker (LLM, cron, k8s), helpdesk triage (LLM), cookbook AI (LLM).
- conclusion: a search-provider + model + scheduler shape has precedent at full score.
  the rubric caps the reward; ambition beyond it earns nothing and costs time.

## Verdict
Not too ambitious AS A WHOLE, on one condition: the three risky pieces (search
provider, model scorer, hourly scheduler) sit behind the mocked service boundary
the course itself prescribes (lesson 2: "mock it so the whole app runs without a
real backend"). Phase 2 ships the full user workflow on a fixture provider and a
fake scorer; the real ones arrive in phase 3 behind flags.
Strongest fact against: the 2025 full-score CRUD apps had zero run-time external
dependencies; ours has two paid APIs at run time. If the key-less mode slips, the
reproducibility criterion (14) and the live deployment (10) both drop a point.

## Phase plan

| Phase | Lesson | Build | Search / scorer | Reviewer can run | Rubric |
|---|---|---|---|---|---|
| P1 | 1 | spec, stack, backlog, AGENTS.md, roles | — | backlog | 1, 2 |
| P2 | 2 | frontend (mock service) → openapi → FastAPI → SQLite. accounts, criteria, events, queue, ICS feed | fixture + fake | local app, tests | 3–7 |
| P3 | 3 | Postgres, compose, integration + e2e, deploy, CI/CD | real, behind flags; key-less kept | public URL | 8–11, 14 |
| P4 | 4 | hourly job, OTel, alert, evidence, responder, Semgrep | — | incident report | 13 |
| P5 | 5 | skill, subagent, MCP server, hook, permissions | — | agent demo | 12 |

## If time runs short, cut in this order

1. hourly job → "Search now" only
2. two thresholds → one (accept / queue)
3. real scorer → fake stays, real documented as optional
