# ProjectOne — work state (resumable)

## 2026-10-20 12:10 — prod on b57bbaa; blind rubric review 24/24 ×3
- Promote of b57bbaa succeeded (run 39398819593). Three blind reviewers (strict, 15-minute, hands-on) each scored 24/24; log in work/RUBRIC-REVIEWS.md; skill `.claude/skills/rubric-review/SKILL.md` (`/rubric-review`) re-runs it. Fixes from the review: OTEL_COLLECTOR_PORT override, README lines (observability local-only, paid instances).
- Owner direction 12:00: rubric alignment is the top priority as a regular scoring mechanism; stabilise features, focus on scoring. Next: re-run /rubric-review after each release; keep the review log moving.
- STILL OWNER (bold in chat): Render dev TAVILY_API_KEY; both services LAKERA_API_KEY → then GUARDRAIL=lakera on both and a Lakera check on prod.

## 2026-10-20 11:25 — search v2 live, PRs 66 + 67 merged, prod promoting b57bbaa
- Merged: #67 card Where line (842dc31, promoted 11:05), #66 issue 65 (b57bbaa: run failures reported as `<Type>: <msg>` with stoppedAtStage incl. "adapters"; Lakera guard GuardUnavailable without key → 503/fallback; SCORER message; deployment.md removal list). Issue 65 closed. Promote run 39398819593 for b57bbaa started 11:24.
- README a2bf5b9: four screenshots from prod (accounts reviewer_104654 / reviewer_105356 on prod, real Berlin search), thresholds 90/40, adapter list, status text.
- Still OWNER: Render env — dev TAVILY_API_KEY; both LAKERA_API_KEY then GUARDRAIL=lakera on both (today GUARDRAIL=none); health check path /api/health; old DB user; prod DB inbound rule. After the keys: dev smoke (`scratchpad/smoke_remote.sh` pattern: register, PUT criteria, POST search, GET events) and a Lakera check (PUT criteria with an injection text → 400).
- Branches search-v2, search-v2-g/h/i still on origin (delete when convenient); no worktrees left.
- Not verified: budget-stop and WindowInPast branches in pipeline.py call _finalise_run without reassigning `run` (QA note on PR 66); the router may read a stale object there. Candidate issue.

## LIVE 2026-10-20 10:55 — prod runs search v2 on Tavily + DeepSeek
- Owner's word given 10:27. Render env set on dev + prod: SEARCH_PROVIDER=tavily, LLM_PROVIDER=openai_compatible, MAX_RESULTS_PER_QUERY=20, TAVILY_SEARCH_DEPTH=advanced, LLM_TIMEOUT_SECONDS=120, LLM_JSON_MODE=json_object (was missing on both → KeyError), SCORER="" (dev had the old value → ValueError), GUARDRAIL=none for now (LAKERA_API_KEY missing on both). Both services deployed main 487cb1a through the env change (prod auto-deploy stays off; promote.yml not needed this time).
- Prod smoke 10:43 (user smoke_*, Berlin text): 20 results → 30 extracted → 17 judged → 2 accepted (Ignaz Schick 95, 13 Kuukautta 92, both 21 Oct Berlin), 2 queued, 13 rejected (dates). Dev smoke blocked: TAVILY_API_KEY missing on dev.
- OWNER TODO on Render: dev TAVILY_API_KEY; both LAKERA_API_KEY (then set GUARDRAIL=lakera on both); health check path /api/health on both; delete old DB user; prod DB inbound rule.
- Open PRs: #66 (issue 65: run failures reported in the API with `<Type>: <msg>` and stoppedAtStage, Lakera guard GuardUnavailable without key, SCORER message, deployment.md) QA re-check running on ec1eeca; #67 (card Where line printed the country twice) CI running. After merge: prod needs a promote (auto-deploy off) — ask the owner or use promote.yml with the main sha.
- README screenshots: taken on prod with a fresh reviewer_* account (scratchpad/shots, script shots.mjs); retake in progress for 01-login and the home top; then copy into docs/images and commit.
- Worktrees: wt-g/h/i (old side branches, can be removed), wt-where (PR 67).

## MERGED 2026-10-20 10:28 — WAITING FOR OWNER'S WORD
- PR #64 merged into main (befe764): search v2 revision (verbatim query + "event", judge_v3 suitability, no planner, no price), #61 budgets/queue, #62 Lakera, #63 UI card. Issues #54-#63 closed. CI green on the branch (one fix 90790fd: hardcoded path in a test). Dev auto-deploys main (fixture/fake adapters, FAKE_NOW set).
- Waiting on the owner for: (a) promote befe764 to prod via promote.yml; (b) Render env on both services: SEARCH_PROVIDER=tavily, LLM_PROVIDER=openai_compatible, GUARDRAIL=lakera, MAX_RESULTS_PER_QUERY=20, TAVILY_SEARCH_DEPTH=advanced, LLM_TIMEOUT_SECONDS=120 (keys already there); dev also FAKE_NOW unset for real runs. Then a live Berlin smoke on dev and prod, README screenshots from dev.
- Owner-side leftovers unchanged: Render health check path /api/health on both services (dev shows empty), old DB user sail_event_db_user to delete, prod DB inbound rule.
- Branches search-v2, search-v2-g/h/i still on origin (delete after promote); worktrees wt-g/h/i in the scratchpad.
- Skill `.claude/skills/status-update/SKILL.md` (`/status-update`) for the owner's 5-minute status blocks; the cron was deleted at merge time, recreate on the next run.

## PAUSE 2026-10-20 08:03 (owner: laptop) — RESUME HERE
- Branch search-v2: rounds 1-3 committed (4f09844 quick path, b656aa5 strict judge + no code place/date filters, 8fb7099 Tavily 20 results + advanced depth). Round-3 table on issue 60: Berlin 3 real jazz events, Sevilla 3, Manchester 2, junk texts 0, Tokyo 15. WIP commit after 8fb7099 = the cleanup mid-flight (planner.py, test_planner.py, judge_v2 deleted; price columns migration c2d3e4f5a6b7; tests rewritten; judge_v3 + extract fixtures re-recorded) — `make test` NOT yet confirmed green; the engineer was killed while running the full suite. Resume: run `make test`, fix the red, commit "#60: cleanup ...", then compose fix (missing fake recording must fail loud), `HOST_PORT=8030 make test-integration`, `make test-e2e`.
- Side branches, all pushed, QA-clean: search-v2-g (#61, 0b3205c, QA PASS re-check), search-v2-h (#62 Lakera, a01e522, QA PASS), search-v2-i (#63 UI, 15c8705, price removed, QA defect fixed). Merge into search-v2 in that order after the cleanup is green; expect conflicts in pipeline.py, routers/search.py, extract.py, .env.example, test_pipeline.py, test_search.py, test_criteria_sentinel.py (its D3 test patches `plan_queries`, which no longer exists → patch the search call instead).
- Then PR search-v2 → main, CI, merge, owner's word before promote + Render switches (SEARCH_PROVIDER=tavily, LLM_PROVIDER=openai_compatible, GUARDRAIL=lakera, MAX_RESULTS_PER_QUERY=20, TAVILY_SEARCH_DEPTH=advanced, LLM_TIMEOUT_SECONDS=120). README screenshots after dev deploy.
- Owner process asks: status every 5 min as a fenced ASCII checklist block (cron was used; recreate on resume), no prose, parallelise, frequent real updates.

## REVISION 2026-10-18 evening (owner) — RESUME HERE
- Owner decisions: the query is the criteria text + the single word "event", sent to Tavily as is; no planner, no city/country rule, no stop for a missing place; extractor records no price; judge = one question "is this a good event for this query" → score 0-100 + reason sentence, no facet flags, no caps, no price/budget rule. Test early with wide variety (junk, other languages, long text, non-events, injections), not only Berlin jazz. Spec/design revision committed dc98ba4 (top of both docs, design §5).
- Steps: (1) quick path on `search-v2` in the main checkout: text+event query, judge_v3 prompt, live batch of 20 texts (10 original + 10 hard), table on issue 60 "quick path: text+event, suitability judge"; old judge/golden tests may be red at this commit. (2) if the table is sane: delete criteria facets, window?, planner, caps, price (ORM migration, API fields), re-record fixtures, `make test` green, compose zero-events cause fixed (fake model must fail loud on a missing recording), integration + e2e green. (3) merge branches search-v2-g (#61 budgets, QA FAIL on 3 observability defects: per-page extract spans, persist span, weak query sentinel test; fix was in progress when killed, nothing committed), search-v2-h (#62 Lakera, QA PASS a01e522), search-v2-i (#63 UI card, 4 commits, QA interrupted before verdict) into search-v2; resolve overlaps in routers/search.py, pipeline.py, extract.py, .env.example; full suites; PR → main. (4) owner's word before promote and Render switches.
- Worktrees: scratchpad/wt-g, wt-h, wt-i under /private/tmp/claude-503/-Users-ad-code-ProjectOne/88df4b5e-b416-4a37-ba3b-18ed01c2a6a0/ (branches pushed to origin; the worktrees can be recreated with `git worktree add <dir> search-v2-g` etc.).
- If an engineer was killed mid-run: `git status --short` in the main checkout shows its uncommitted work; keep or drop by reading the diff; the breadth batch is `uv run --project backend --directory backend python scripts/smoke_search.py --batch` with backend/.env.local sourced, GUARDRAIL=none, SSL_CERT_FILE from certifi, FAKE_NOW unset.

## RESUMED 2026-10-18 17:55 after context compaction
- Branch search-v2 at 3f61419, tree clean. Integration tests already have a city + `test_no_place_criteria_stops` (c8042dc). One Opus engineer launched on the rest of issue 60 (smoke_search.py, breadth batch, table on the issue, top cause fixed, docs/testing.md, integration + e2e green). Next: 61 → 62 → 63 → combined QA → PR → ask owner before promote/Render switches.

## STOP 2026-10-18 (owner: "gracefully stop") — RESUME PROCEDURE (search v2)
- Branch `search-v2`, last commit c8042dc (FAKE_NOW wired in CI, compose, tests, docs), pushed, tree clean, no worktrees.
- Issue 60 (F2): done = extraction prompt fix + live recording (cf4303c), pipeline swap (98f0438), old adapters deleted (90f4ff4), renames (78ba951), FAKE_NOW wiring (c8042dc). LEFT = `backend/scripts/smoke_search.py` with `--repeat`, `--record`, `--batch`; the breadth live run on the 10 criteria texts listed in the issue-60 thread (orchestrator message of 2026-10-18 evening: Berlin jazz, beer festival Ireland, tech meetup Lisbon, kids science Paris, free concerts Vienna, online AI webinar, "something fun this weekend" → expected stop, Mediterranean regattas July 2026, Spanish flamenco Sevilla, food trucks Manchester <20 GBP), failure table ranked, top cause fixed; integration tests `test_user_isolation` / `test_data_survives_restart` may still use place-less criteria (fails by design: "no place in criteria"): give them a city and add one test for the stop. Then issues 61 (budgets, hourly queue), 62 (Lakera guard), 63 (UI card: zone, band, run report), combined QA, PR, CI, merge, promote, Render switches (`SEARCH_PROVIDER=tavily`, `LLM_PROVIDER=openai_compatible`, `GUARDRAIL=lakera`; keys already there).
- Owner decisions today: breadth over depth (the 10-text table decides priorities); required event fields (spec §5); Lakera primary, self-check fallback; DeepSeek via OpenAI-compatible adapter; keys in backend/.env.local (git-ignored). VPN must be off for DeepSeek from this Mac (corporate exit resets TLS to api.deepseek.com).
- Process: engineers commit with SKIP_HOOK_TESTS=1 after `make test`; no sub-agents inside engineers; QA in a detached worktree in parallel (`git worktree add --detach <scratch>/wt-qa <sha>`, copy backend/.env.local in); tree check every 9 min with `git status --short | wc -l` and file mtimes, kill and relaunch on 20 min of silence; make test targets `test-integration`/`test-e2e` use compose project `sail-test` (`HOST_PORT=8030`) so the demo stack on 8010 survives.
- Machine: ports 8000/3000 = owner's other project; 8010 app demo, 3001 Grafana, 9090 Prometheus (may be down). Never `rm`, `sed -i`, `cd &&`, never the app's dev-server launcher (preview_start/launch.json); use git clean / Edit / Write. Local HTTPS for live calls: `SSL_CERT_FILE=$(uv run --project backend --directory backend python -m certifi)`.
- Breadth texts for the smoke `--batch` (owner priority): 1 "jazz in Berlin (Germany) next week (19-21st October 2026)"; 2 "beer festival in Ireland"; 3 "tech meetup in Lisbon this month"; 4 "kids science workshop in Paris this weekend"; 5 "free concerts in Vienna in December"; 6 "online webinar about AI next week"; 7 "something fun this weekend" (expected stop: no place); 8 "sailing regattas in the Mediterranean, July 2026"; 9 "conciertos de flamenco en Sevilla en noviembre"; 10 "food truck festival near Manchester, under 20 GBP". Table columns: text, stopped_at_stage or ok, counts per stage, calls, seconds, top 3 kept events. Rank: country/date leaks > empty results > stops.
- Render: prod `sail-event` srv-db9o8e6q1p3s739001d0 (auto-deploy off, promoted via promote.yml with a full sha), dev `sail-event-dev` srv-db9viuijnfac73dpph20 (auto-deploy on main), DBs in work/DEPLOY-render.md; keys LLM_*/TAVILY_API_KEY/LAKERA_API_KEY already on both services (owner set them); switches to flip after the merge: `SEARCH_PROVIDER=tavily`, `LLM_PROVIDER=openai_compatible`, `GUARDRAIL=lakera`, dev also `FAKE_NOW` unset for real runs (compose default only). Render MCP connector is authorised (list/get/update env vars, logs).

## (earlier) PAUSE 2026-10-18 evening — RESUME PROCEDURE (search v2)
- Branch `search-v2` (checkout is on it). Issues: A #54, B #55, C #56 closed (QA PASS). D #57 is a WIP commit (providers v2, planner, fixtures, 42 unit tests green) with `make test` and the issue comment still to do; E #58, F1 #59, F2 #60, G #61, H #62, I #63 pending. Tracker: work/FEEDBACK-2026-10-18.md (owner items a-g).
- Resume: 1) `git status --short` must be empty; 2) a fresh engineer finishes D from the WIP commit per issue 57 (run `make test`, comment, push), then QA D in a detached worktree (`git worktree add --detach <scratch>/wt-qa <sha>`, copy backend/.env.local into it) while the next engineer starts E in the main checkout; 3) continue E → F1 → F2 (pipeline swap + `backend/scripts/smoke_search.py` on C1 with the keys from backend/.env.local) → G → H → I; 4) PR search-v2 → main, CI, merge, promote, then set `SEARCH_PROVIDER=tavily`, `LLM_PROVIDER=openai_compatible`, `GUARDRAIL=lakera` on Render (keys already there) and run the Berlin smoke on dev and prod.
- Agent brief rules that avoid stalls: never `rm`/`sed -i`/`cd &&`; never the app's dev-server tools; commit with `SKIP_HOOK_TESTS=1` after running `make test`; live calls need `set -a; . backend/.env.local; set +a` and `SSL_CERT_FILE=$(uv run --project backend --directory backend python -m certifi)`; check `git status` every ~15 min for a stalled agent.
- Local stacks: app 8010 and Grafana 3001 may still be up (`make observability-down`, `HOST_PORT=8010 make compose-down`). Keys only in backend/.env.local (git-ignored) and on Render.


## Goal
Pick a project for DataTalksClub AI Dev Tools Zoomcamp (ProjectOne = temp name).

## Status (2026-10-17, resume point)
- MVP complete: issues 1-27, 29 closed; 21 closed (dev/prod on Render, promote.yml). CI green.
- Live: prod https://sail-event.onrender.com (promoted by hand), dev https://sail-event-dev.onrender.com (follows main). Details: work/DEPLOY-render.md.
- Hourly search: GitHub Actions hourly-search.yml → prod, fixture adapters (no API keys set).
- README rewritten for peer review (f55ed3b, b3ed32d). Rubric: all 12 criteria covered, CI/CD at 3/3.
- Hardening #33 #35 #36 #34 closed 2026-10-17 via the loop (d2d38b9, d2b33ac, 8ec23c0, 4cee1d6), CI green, promoted to prod (run 39081329740); prod and dev both on 4cee1d6. Tests: 180 backend, 25 frontend, 19 responder, 7 integration, 2 e2e.
- 2026-10-18 (overnight run): #28 reduced (QA subagent + pre-commit hook, `make hooks`), robustness #37 #38 #39 closed via the loop; CI red for 3 pushes (restart test vs GitHub runner reset) fixed in 93ad48f; promoted to prod run 39095094746; prod and dev on 93ad48f. Tests: 194 backend, 26 frontend, 19 responder, 7 integration (restart test now runs), 2 e2e. README gotchas from walkthrough 1 fixed (11f2828). Roadmap: work/ROADMAP.md. Robustness plan: work/ROBUSTNESS.md.
- Second walkthrough 23/24 → fixes pushed (7b9bccc). 
- UX redesign (roadmap P1) 2026-10-18: spec _docs/ux-spec.md, design _docs/ux-design.md, review _docs/ux-design-review.md (Fable); issues #40-#44 on branch ux-redesign, each QA PASS; PR #45 merged (5cbb5b9); polish #46 PR #47 merged (58ccdd9); README screenshots retaken (24e22b0). Dev shows the new UI; PROD STILL ON 93ad48f, owner promotes.
- Theme (P2) 2026-10-18: _docs/theme-design.md + review; issues #48-#50 on branch theme, QA PASS each; PR #51 merged (be1c25c). README screenshots on the new theme. Dev auto-deploys main. PROD PROMOTED 2026-10-18 to 5ef6911 (run 39144721076, owner's word): redesign + theme live at https://sail-event.onrender.com.
- Icon: b-sail-mark.svg is the favicon and header mark. Roadmap status in work/ROADMAP.md.
- Overnight incidents: two CI-only test timing flakes fixed (e2e scoring save race, App.test Search-now enable); one agent stall on the app's dev-server launcher (now banned in briefs; use Bash background `npm run dev`).
- Local stacks running: app 8010 (demo/demo, rebuilt on be1c25c), Grafana 3001, Prometheus 9090. Stop: `make observability-down` and `HOST_PORT=8010 make compose-down`.
- Machine rule: `rm`, `sed -i`, `cd ... &&` are denied by a permission rule and stall; use git clean, Edit/Write, absolute paths. Put it in every agent brief.
- Responder now needs RESPONDER_WEBHOOK_SECRET exported before `make responder` / `make observability-up` (incident-response/README.md).
- Tidy-up 2026-10-17: local stacks stopped; old prod DB user has 0 connections (verified by SQL), bin click is the user's; e2e/shots untracked temp folder, user deletes.
- Render MCP connector authorised; gh CLI works; Claude in Chrome not connected, built-in browser used.

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

## RENDER DEPLOY DONE 2026-10-17 (after the unattended run)
- AWS dropped (IAM cost); Render: prod + dev services, two Postgres, promote.yml, hourly cron via GH Actions; #17 #29 #21 closed. See work/DEPLOY-render.md.

## UNATTENDED RUN COMPLETE 2026-10-17 (historical)
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
