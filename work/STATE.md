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

## RESUMED 2026-10-16: a33bc24 was committed; Dockerfile etc. uncommitted; docker (OrbStack) down → started.
- issue #14 S7 Dockerfile: DONE. eng ae645df (uv pinned, tsc build fixed) → QA FAIL (SPA fallback
  answered /api/*) → fix dd304bb → my checks + browser flow on the container → closed. image 350 MB.
  note: host port 8000 is the user's order-tracker stack (HW4); our runs use 8010.
- issue #15 S7 Postgres + compose: DONE. eng c64207d+d34dda2 → QA FAIL (healthcheck curl missing;
  engineer had claimed --wait ok) → fix 7dec86d → I verified healthy → closed. psycopg 3.3.6.
- issue #16 S7 integration + e2e: PM DONE (groomed on GitHub). Correction to pass to the engineer:
  pin @playwright/test to the latest 1.64.x (QA verified 1.64.1 on npm 2026-10-16), not 1.52 as
  RESUMED 2026-10-16: eng 88d22a5..9535483 (7 integration, 2 e2e, playwright 1.64.1) → QA PASS → closed.
  S7 COMPLETE (issues 14-16).
- 2026-10-17 AWS DECISIONS (user: "Do what is best"): IAM user `sail-event-deploy` with AdminAccess,
  CLI profile `sail-event`; region eu-west-3; dev = 1x t4g.small; TLS via Caddy on an sslip.io
  name over an Elastic IP; teardown documented. Rotate/delete the IAM user after S10.
  2026-10-17 user could not get through AWS sign-in; AWS deferred. Render proposed as the easy
  alternative (user to decide later). UNATTENDED RUN 2-3h without a cloud target, order:
  #18 CI-only → #23 → #24 → #25 → #26 → #19 → #20 → #22 (GH Actions schedule) → #27.
  #17, #21 blocked on AWS; #18 CD half = new issue #29; #22's target URL filled in once a target exists.
- issue #18 S9 CI: DONE. PR #30 merged a719004, CI green on PR and main → QA PASS → closed.
- issue #23 S11 OTel instrumentation: DONE. eng 3817a63+b2e6154 → QA PASS 22/22 live → closed.
- issue #24 S11 observability stack: groomed (I fixed image tags to the 2026 versions already
  on this machine; added OTLP-logs fallback if the docker log bind mount fails on OrbStack).
  DONE: eng b85bd8c+56d3e48 (OTLP logs path used; filelog kept for Linux) → QA PASS 12/12 live → closed.
- issue #25 S12 alerts: DONE. eng d7f0eea+d06f549 → QA PASS 18/18 live (fire + resolve + webhooks)
  → closed. fact: Loki & collector images have no shell/wget (I tested); healthchecks stay validation-only.
  Grafana 13 stores {{ $labels }} literally in provisioned labels; real labels come from the query.
- issue #26 S12 responder: DONE. eng e766b84..dda836d; first incident 20261017-052050 → verdict fix
  dae24e9 on branch incident/...; QA PASS → closed. caveats: test-incident.sh run stepwise; first
  branch made by hand; claude -p needs CLAUDE_* env vars cleared when spawned from Claude Desktop.
  LESSON 4 CRITERIA (observability, alert, on-call agent) COVERED LOCALLY.
- issue #19 S13 Tavily adapter: DONE. eng 89606bf+1c3cf16 → QA FAIL (date fallback to title dead:
  'unknown' truthy) → fix bf8e952 → QA PASS → closed. no key: fixtures synthetic from Tavily docs.
- issue #20 S13 Claude scorer: DONE. eng 0a01baa+81c5e65 (anthropic 1.15.0) → broke a test and
  called it pre-existing (I disproved it in a worktree) → fix 678cd4c → QA PASS 21/21 → closed.
  S13 COMPLETE. keys needed for live use: TAVILY_API_KEY, ANTHROPIC_API_KEY (user, later).
- issue #22 S10 hourly schedule: DONE. PR #31 643d990 (merged on red integration job: regression
  from #24's external network; fixed PR #32 668f5f3, main green) → QA PASS 13/13 → closed.
  rule added to engineer role: merge only on all-green CI.
- issue #27 S12 security audit + ops report + ai-usage report: DONE. eng 17f122e..c23be33
  (Semgrep 2 false positives; model review 20: 2 fixed, 7 accepted, 11 deferred → #33-#36) →
  QA FAIL (no SHAs, no status test) → fix b34dde4 → QA PASS → closed.

## UNATTENDED RUN COMPLETE 2026-10-17
- closed: 1-16, 18-20, 22-27 (25 of 28 + #29-#36 created). tests: 164 backend, 22 frontend,
  7 integration, 2 e2e. CI green on main.
- rubric coverage without a cloud target: criteria 1-7 full; 9 CI only (1/3); 10, 11, 12 covered
  locally (observability, alert, on-call agent); 8 deployment 0 until a target exists.
- REMAINING, all need the user: #17 deploy dev (AWS or Render decision), #21 prod + manual
  promotion, #29 CD on merge; then set repo variable SAIL_BASE_URL + secrets SEARCH_ALL_API_KEY,
  TAVILY_API_KEY, ANTHROPIC_API_KEY for live search/scoring. #28 agent pack optional (0 pts).
- follow-ups filed post-mvp: #33-#36 (security findings deferred).

## PAUSE #2 2026-10-16 — RESUME PROCEDURE
1. tree should be clean at or after 1df4de4; `git status --short`, `git log --oneline -3`.
2. `gh issue view 16` — if the body has the four sections (Goal / Acceptance criteria / Out of
   scope / Constraints) the PM finished: review it, then launch the engineer on #16 (compose stack
   on HOST_PORT=8010; 8000 is the user's order-tracker stack). If not, re-run the PM on #16.
3. then QA #16 → close → S7 complete → STOP and ask the user before #17 (AWS account,
   credentials, region, budget).
4. docker: `docker ps -a | grep sail` should be empty; `docker info` may need `orb start`.

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
