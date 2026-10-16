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
  12/18/25) + mine (no EventBridge trigger task) → 12-point revision in progress → I verify
- S2c GitHub issues: needs public repo → USER DECIDES name/visibility (blocking)
- S3 AGENTS.md, process.md, task-template.md, team/: after S2b
- git: branch main, no remote yet, tree clean at 3abcb4a

## Notes
- datasheet-info-collector is a desktop-app session skill (Application Support/Claude/...),
  not removable from here; user manages it in the app's Skills settings.
- engineering:* skills (architecture, system-design, testing-strategy...) come from a
  desktop-app bundled plugin, global, not project-scoped.
