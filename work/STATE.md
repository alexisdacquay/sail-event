# ProjectOne — work state (resumable)

## Goal
Pick a project for DataTalksClub AI Dev Tools Zoomcamp (ProjectOne = temp name).

## Status
- [x] git init, work file created (2026-10-15)
- [x] fetch project instructions + rubric
- [x] read course modules 01-05
- [x] record understanding (work/UNDERSTANDING.md)
- [x] propose ideas (work/IDEAS.md)
- [ ] user picks idea (OPEN ASK since 2026-10-15)

## Decisions
- 2026-10-15 plugins installed at project scope (user: "yes deploy the 5 skills"):
  feature-dev, frontend-design, pr-review-toolkit, security-guidance, context7.
  -> .claude/settings.json in this folder. global settings unchanged (verified: langfuse only).
  active from the next session start.
- 2026-10-15 skills sonic-hw-recon / datasheet-info-collector: cannot unload mid-session;
  rule: never invoke or infer from them.

- 2026-10-15 user: shape axes (sources, relevance, output, users, operations, non-goals)
  are seeds, keep them all. We follow the course method, lesson by lesson. work/METHOD.md.
- 2026-10-15 idea K (event finder) is the working idea; formal confirmation comes out of
  the lesson-1 brainstorm (plan.md), not a chat yes.

- 2026-10-15 brainstorm closed (Q1-Q9 in work/BRAINSTORM.md). name: Sail-event.
  users: multi. source: web search only. criteria: free text, model-scored. triage:
  auto-accept / auto-reject / queue. calendar: ICS feed per user. run: hourly + button.
  no notifications. self-maintenance = lesson 4/5, later phase.

## Where we are in the method (see work/METHOD.md)
- lesson 1 step 1 done: _docs/plan.md v1 (2026-10-15), awaiting user review
- step 2 bootstrap: git exists; plan committed
- next: step 3 stack options ("Read _docs/plan.md. Propose multiple options for the
  tech stack...") -> step 4 tasks.md -> step 5 AGENTS.md/process.md -> roles

## Open asks
- user reviews _docs/plan.md; corrections -> plan.md v2 (never overwrite silently)
- 2026-10-16 user asked: too ambitious? -> work/ASSESSMENT-scope.md: no, if P2 ships on
  mocks. user: "good."
- 2026-10-16 RUBRIC CHANGED (12 criteria, 24 pts, pass 10; lesson 5 ungraded). recorded in
  work/PHASES.md with plan v2 (S1-S14). UNDERSTANDING.md rubric section is stale: see PHASES.md.
  user: keep the removed-but-good practices; judge 3 sources; less is more.
  -> PHASES.md v3 ADOPTED 2026-10-16. ponytail installed (project scope). 12-factor =
  work/REFERENCES.md. S13 after S9, S14 last optional: CONFIRMED by user 2026-10-16.

## Phase 1 started 2026-10-16 (user: "progressing with the next phase", orchestration mode)
- mode: I orchestrate; Opus agents draft; a fresh Opus agent reviews; I arbitrate.
- S1 README: draft v1 → my review (kayaker example, "local" cut) → QA PASS, auth step
  missing → fix in progress
- S2a stack options: draft v1 → QA FAIL (Fly free tier gone, Railway/Render prices wrong,
  2024 versions, course default incomplete, generic bullets, python-jose) + my flag
  (free tier sleeps → in-process scheduler dies) → v2 → QA#2: facts verified, 2 residuals
  (Render "1 service", Railway $0 unverified), wrong counter-fact → I applied 7 edits = v3.
  README: QA PASS + auth step added.
  DECIDED 2026-10-16: deploy = AWS course path (EC2 per env via CloudFormation, lessons 3-4
  prompts verbatim); hourly run = EventBridge cron → search endpoint (to verify at S8).
  DECIDED 2026-10-16 stack A: React+TS+Vite, Tailwind+shadcn/ui, FastAPI, SQLAlchemy, SQLite→Postgres,
  bcrypt auth, pytest+Playwright, EventBridge cron for the hourly run.
- S2b architecture.md + tasks.md: draft v1 (28 tasks) → QA: arch PASS w/ defects (openapi
  direction, triage boundary inclusive vs plan's strict, hourly flow single-user, `new` status
  recovery), tasks FAIL (S13 misplaced after S12, task 19 depends on S13, split 5 & 8, merge
  12/18/25) + mine (no EventBridge trigger task) → 12-point revision → I verified (order,
  merges, arch diff) → DONE 2026-10-16: _docs/architecture.md v2, _docs/tasks.md v2 (28 tasks)
- S2c DONE 2026-10-16: public repo github.com/alexisdacquay/sail-event, main pushed, labels
  mvp/post-mvp, issues #1-#28 = tasks 1-28 (#28 post-mvp). tasks.md -> _docs/outdated/.
- S3 DONE 2026-10-16: AGENTS.md, CLAUDE.md=@AGENTS.md, _docs/process.md, task-template.md,
  team/{pm,software-engineer,qa-engineer}.md — course texts, my review, committed
- git: origin = github.com/alexisdacquay/sail-event (public). work/ is pushed too (no secrets).

## Phase 2 started 2026-10-16 — orchestrator loop (process.md)
- issue #1 S4 scaffold: DONE 2026-10-16. PM (Node pin fixed 22→24) → engineer 6ccfdec →
  QA PASS 10/10 (missed dirty tree) → cleanup 48cf3c3 → I verified → closed.
  lesson: QA must check `git status` explicitly; add to qa-engineer.md before #2.
- issue #2 S4 criteria/thresholds/auth screens + mock service layer: DONE 2026-10-16.
  PM (no correction) → engineer 5e7620e → QA PASS 16/16, 4 test gaps → +tests 2ffedb2 → closed.
- 2026-10-16 user: chain issues without asking; stop only on a problem I cannot resolve.
  known stops ahead: #17 (AWS credentials), #19/#20 (search + model API keys).
- issue #3 S4 events list + queue: DONE. PM (fixed 'sailing' mock titles) → eng 9b6d9c7 →
  QA PASS 15/15, 4 gaps → +2 tests ef87cec → closed.
- issue #4 S4 openapi.yaml + docs/api.md: DONE. PM (no fix) → eng a3dd774 → QA PASS 12/12 → closed.
  S4 COMPLETE (issues 1-4).
- issue #5 S5 adapters: DONE. eng 6bc4ff9 → QA PASS 22/22, 6 gaps → +3 tests 4758aae → closed.
- issue #6 S5 routers + store + pipeline: DONE. eng 13a9fe4+3b122fa → pyyaml dev dep approved
  (contract test reads openapi.yaml) 9b1c537 → QA FAIL (invalid decision → 500) → fix 8940b2a
  → QA PASS → closed. first real bug caught by the loop.
- issue #7 S5 auth: DONE. PM (bcrypt pin fixed 4.3→5.0) → eng d7e3a11..21bc6a4 → QA FAIL
  (validation handler echoed plaintext password) → fix db3499a → QA PASS → closed.
- issue #8 S5 connect: DONE. eng bc2344a+a60b386 → QA PASS (curl + reading; no browser for the
  subagent) → I did the browser walk-through myself (built-in browser): all good → closed.
  S5 COMPLETE (issues 5-8). lesson: QA subagents lack the built-in browser; browser checks are mine.
- issue #9 S6 ORM + Alembic: DONE. eng 9153884..e14d614 → QA PASS 21/21 (1 gap → #13) → closed.
- issue #10 S6 store→ORM: DONE. eng 5a66fe3+4090425 → QA PASS 23/23 (4 gaps → #13) → closed.
- 2026-10-16 ponytail lite ON in my session; its rule added to _docs/team/software-engineer.md (13f0fd3)
- issue #11 S6 pipeline: DONE. eng 6394a7a..11912b5 (services/pipeline.py, Run rows + error,
  recovery, derive_queries, cap) → QA PASS 15/15 live (3 gaps → #13) → closed.
- issue #12 S6 ICS feed + calendar-url + dashboard copy: DONE. eng ffae95d+edff16d → QA PASS
  21/21 live (3 gaps → #13) → closed.
- issue #13 S6 test gap-fill + docs/testing.md: DONE. eng ad888e4+509154c (+18 tests; found and
  fixed: `new` events were decidable; Makefile claim disproved, exit 2) → QA PASS 22/22 → closed.
  S6 COMPLETE (issues 9-13). tests: 128 backend, 22 frontend.
- issue #14 S7 Dockerfile: PM groomed (same-origin VITE_API_URL="", SPA fallback, node:24-alpine +
  python:3.12-slim, uv sync --no-dev --frozen, alembic in entrypoint, /data volume).
  ENGINEER IN FLIGHT at pause time 2026-10-16 (laptop closed). Not pushed.

## RESUMED 2026-10-16: found a33bc24 committed + Dockerfile/.dockerignore/Makefile uncommitted;
  docker daemon was down (OrbStack), started. Fresh engineer finishing #14 with two corrections:
  pin the uv image tag; fix the tsc build instead of bypassing it.

## (kept) PAUSE PROCEDURE 2026-10-16
1. `git -C /Users/ad/code/ProjectOne status --short` and `git log --oneline -5`.
   - commits with prefix "S7:" present and tree clean → engineer finished: run QA on #14
     (fresh Opus agent, role _docs/team/qa-engineer.md; verify docker build/run live, SPA
     fallback, persistence via volume, no pytest in image), then close, push, go to #15.
   - tree dirty or no S7 commits → engineer was cut: `git stash` or discard partial work
     (`git checkout -- . && git clean -fd` after reading what is there), re-run the engineer
     on #14 from the groomed issue.
   - also check `docker ps -a` for a leftover sail-event container; remove it.
2. loop continues: #15 Postgres+compose → #16 integration+e2e → STOP before #17 (needs the
   user's AWS credentials and account decisions).
3. process reminders: QA role checks git status; engineer role carries the lean-code rule;
   orchestrator does the browser walk-through itself (subagents have no browser);
   carry test gaps to the next test issue; one issue at a time.
- toolchain: uv 0.11, python 3.13 (arch says 3.12: PM to pin), node 24, npm 11, docker up

## Notes
- datasheet-info-collector is a desktop-app session skill (Application Support/Claude/...),
  not removable from here; user manages it in the app's Skills settings.
- engineering:* skills (architecture, system-design, testing-strategy...) come from a
  desktop-app bundled plugin, global, not project-scoped.
