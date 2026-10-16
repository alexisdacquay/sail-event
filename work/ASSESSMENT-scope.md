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

## Phase plan, mirroring HW1-5
P1 lesson 1 (now): plan.md -> stack options -> tasks.md -> AGENTS.md, process.md,
   team roles. deliverable: backlog as GitHub issues.
P2 lesson 2: frontend with mocked service layer -> openapi.yaml -> FastAPI with
   in-memory store -> connect -> SQLite/SQLAlchemy. App v0 = accounts, criteria,
   event list, queue accept/reject, ICS feed. search = fixture provider, scorer =
   fake (deterministic). unit + frontend tests. docs/ai-usage-report.md.
P3 lesson 3: real search provider + real model behind env flags, key-less mode kept;
   Postgres; Dockerfile + compose; integration tests + Playwright e2e; deploy; CI/CD.
P4 lesson 4: hourly run as a job; OTel; alert on failed/empty run; evidence packet;
   headless responder (= the self-maintenance the user wants); Semgrep audit;
   operations-and-security-report.md.
P5 lesson 5: agent extension pack (skill, subagent, MCP server exposing
   upcoming_events/decide, hook, permissions note, demo script).
Each phase ends with something a reviewer can run. P2 alone already covers rubric
criteria 1-7 at full marks.

## Simplifications available if time runs short (in order)
1. drop the hourly scheduler: "Search now" only (P4 keeps an alert on a manual run)
2. one threshold instead of two: accept/queue, no auto-reject
3. scorer stays fake in production (demo mode), real model documented as optional
