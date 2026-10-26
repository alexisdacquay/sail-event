# Verified facts from the 10 critics (2026-10-26)

## live-journey

PROD vs DEV, checked 2026-10-26 by HTTP GET, live JS bundles and git show:
- Commit: prod /api/health → 969a16144b909f57359f38f8a5f8e05a0ef5b491 (promote run #15, id 39979831552, workflow_dispatch, 2026-10-23T15:37Z). Dev → 542e58cb0fe73065a905febec7637bfa377a77c4 = main head. Prod is 41 commits behind (git log 969a161..542e58c).
- Bundles: prod /assets/index-CPfb2K8m.js, dev /assets/index-CHvwH0Z6.js (saved under /private/tmp/claude-503/-Users-ad-code-ProjectOne/88df4b5e-b416-4a37-ba3b-18ed01c2a6a0/scratchpad/bundles/).
- Registration: /api/config → {"registrationCodeRequired":false} on both. No invitation field is shown.
- Sign-up path, same on both: the Sign in page says 'No account? Create one'; the form heading and button say 'Create account'. There is no 'Register' control anywhere in the UI.
- Demo user: only where SEED_DEMO=1, i.e. dev and docker compose (work/DEPLOY-render.md L32; docs/deployment.md L44: prod does not seed). Seeded criteria: 'jazz in Berlin (Germany) next week (19-21st October 2026)' (backend/app/main.py). docs/deployment.md L83 says dev sets FAKE_NOW=2026-10-18T12:00:00+02:00; not verifiable without login.
- Search box. Prod: textarea saves on Enter or blur; Search now is disabled until saved criteria exist; hint 'click the text to change it · Enter saves'; 'Saved.'; 'Times shown in UTC until you save your criteria.'; placeholder '…, under 40 EUR'. Dev: one form, Search saves then runs; 'Saved for the next search' if a run is going; placeholder without a price.
- Button text, same on both: 'Search now', then 'Search again' after a run, 'Searching…' while running.
- Progress text. Prod: 'Starting up…', 'Searching the web…', 'Reading pages X of Y…', 'Filtering events…', 'Judging X of Y events…'; no progress bar. Dev: 'Reading pages X / Y…', 'Opening event pages X / Y…', 'Judging events X / Y…', plus a hairline progress bar.
- Chronology. Prod: 'Not judged: N', 'Judged N · a in calendar, q to review, r out', 'Done: … r out'. Dev: 'Opened N event pages[, F failed]', 'Screened out: N', 'Judged N · … r rejected[, e not scored yet]', 'Done: … r rejected'.
- Funnel. Prod: theme greys; nodes 'found', 'judged', 'not judged' (subs: no date, past, duplicate, date, place, incomplete, capped, errors), 'in calendar', 'to review', 'out' (subs: date or place, topic, other). Dev: fixed colours; 'screened out' (subs: already over, duplicate(s), no start time, no start date, wrong dates, wrong place, missing details), 'rejected' (subs: wrong date or place, off topic, below your threshold, duplicate(s)), 'not scored yet'. The funnel is hidden below 768 px on both.
- Same on both: row statuses 'In calendar' / 'Review' / 'Out' / 'New'; 'Results' heading (shown only when there are events); 'Clear all' (irreversible); Results footer 'N out, mostly <reason> · show'; rail 'Calendar feed' with Copy and 'Reset link'; 'Searches' with '+ new search' disabled ('coming later'); collapsed 'Scoring' with slider legend 'Out / You decide / On your calendar' and inputs 'Auto-reject below' / 'Auto-accept above'; detail panel 'Add to calendar' / 'Reject', 'Score N%', 'Source'.
- Pipeline on prod only: no event-page (detail_hop) stage (#141); events with no start time are kept, and STATE says 603 date-only events are in prod calendars; at most 50 events judged per run (MAX_EVENTS_PER_RUN), the rest counted 'capped'; judging is sequential (parallel came in #143); no model duplicate check (#149); search providers in code are fixture, tavily and brave only (Exa came in #147). Per work/STATE.md, prod uses SEARCH_PROVIDER=tavily and dev uses exa, both with DeepSeek flash (env vars not checked live).
- Both prod and main append ' event' to the sentence before searching (pipeline.py).
- Triage code on main: score >= upper → accepted, score <= lower → rejected (pipeline.py L743, L746).
- Hourly job: cron '7 * * * *' against prod only. Recent runs land every 2.5-5.9 h. Each of the last 4 runs logged usersQueued 50 and usersSkipped 23 (MAX_SCHEDULED_USERS=50, oldest last run first).
- CI: run 40242394581 (#284, push, 8305160): backend 481, frontend 117, integration 7, e2e 12. Run 40251535674 (#297, push, 542e58c = current main and dev): backend 507, frontend 117, integration 7, e2e 12.
- Promote workflow: 15 runs, all workflow_dispatch, all success (gh run list --workflow=promote.yml).
- Tracker counts verified with the guide's own commands: 58 groomed, 69 issues with a QA verdict, 23 with a FAIL, 30 PRs with a verdict, 45 'closed by the orchestrator'; 85 closed and 11 open issues.
- Rubric: work/rubric-2026-10-16.md is byte-identical (5142 bytes, empty diff) to https://raw.githubusercontent.com/DataTalksClub/ai-dev-tools-zoomcamp/main/project/README.md fetched 2026-10-26. 12 criteria, 24 points, pass at 10. CI/CD levels 1, 2, 3; Alerting max 1; On-call 0 or 2.
- Incidents: both recorded runs were injected faults. 7318f2f 'test: inject scorer fault' was fixed by dae24e9 (2026-10-17); 3d9f6b8 'test: inject search-provider fault' was fixed by 8d2f839 (2026-10-21). Both branches incident/20261017-052050-SearchRunFailures and incident/20261021-074150-SearchRunFailures are on GitHub.
- Screenshot captions that match their pictures: review-02, 06, 08, 09, 10, 20-23, 25, 30, 31, 32, 33, 36a, 36b, 40, 41 (42 spans, detail_hop present, local), 41b, 42, 46. Problem screenshots: review-03 (dev UI, '2 failed', 'Stream' jargon), review-07 (legend cut off), review-43 and review-44 (a 2026-10-25 local screenshot drill; review-44 shows 'runbook TODO').
- All relative links and anchors in README.md, docs/reviewer-guide.md and docs/deployment.md resolve.
- Will go stale if the owner promotes before the deadline (STATE has a promote checklist): every '969a161' in README rows 8 and Status, guide lines 42, 523, 525, 553, and docs/deployment.md L17.

<!-- live-journey summary: I did the reviewer journey against both live sites using only HTTP GETs: /api/health, /api/config, the HTML and the JS bundles. I also read the prod code with git show 969a161, opened all 31 screenshots that README.md and docs/reviewer-guide.md use, and checked the CI, promote and hourly-search runs with gh.

The main problem: README "Try it in 60 seconds" sends reviewers to prod (969a161). Prod is 41 commits behind dev and its UI is older. The README, the hero image and the guide all describe dev and main.

Problems a reviewer hits by following the README:
- **Search now does nothing on prod. -->

## guide-facts-2

I verified the following against git, gh and HTTP GETs on 2026-10-26.
- Live: prod /api/health commit is 969a16144b909f57359f38f8a5f8e05a0ef5b491. Dev /api/health commit is 542e58cb0fe73065a905febec7637bfa377a77c4, which equals main's head. /api/config on both returns {"registrationCodeRequired":false}.
- 969a161 ("docs: Sankey funnel built (PR 119)", 2026-10-23) is on main, is 39 commits behind 542e58c, and has no associated PR (it was a direct push).
- CI run 40242394581 is a push on main at 8305160 (2026-10-25T22:55Z), with jobs frontend 121316788834, backend 121316788991 and integration 121317996594, all green. The guide's grep command reproduces its log lines: postgres Healthy 23:01:22, app Healthy 23:01:28, "7 passed" 23:02:25, "12 passed" 23:02:51. All 7 integration tests passed, including test_data_survives_restart. Teardown ran docker compose down -v.
- PR 149's CI was 3 green jobs (run 40241696437). promote.yml has 15 runs, all workflow_dispatch and all success. Run 39979831552 promoted 969a161 (prod was previously on 571b751). The sha input is optional.
- hourly-search.yml has cron '7 * * * *'. Over the last 50 scheduled runs the gaps were 2.1-7.8 h. /api/search/all returns 202 and runs the searches as BackgroundTasks.
- rules.yaml: L9 is search-run-failures (> 1, for 5m) and L66 is search-runs-silent (< 1 over 2h, for 10m, noDataState OK). The group interval is 60s and both rules are severity critical. policies.yaml routes critical to responder-webhook; contactpoints.yaml uses a Bearer $RESPONDER_WEBHOOK_SECRET.
- Incident 20261021: alert startsAt 07:41:20Z and evidence collected 07:41:50Z. Fault commit 3d9f6b8 at 07:32:59Z; fix 8d2f839 at 07:46:12Z (4 min 52 s). Neither commit is an ancestor of origin/main; both are on the remote branch incident/20261021-074150-SearchRunFailures. Backend def test_ count at those commits is 217. fix.diff is +1 -4.
- Incident 20261017: fault 7318f2f 'test: inject scorer fault', fix dae24e9. App health had failed at collection time.
- In both incidents the Loki evidence section is empty.
- responder.py: model sonnet, --max-budget-usd 1, timeout=300; ALLOWED_TOOLS has bare Read and Edit and no git push. autonomy-policy.yaml is never read by any code.
- test_responder.py: 20 tests, stdlib only, all OK when run locally. They are not in ci.yml.
- Telemetry is a no-op unless OTEL_EXPORTER_OTLP_ENDPOINT is set. Only docker-compose.observability.yml sets it; deployment.md does not. make up-all starts 7 containers (5 observability + postgres + app).
- 9 metrics are defined at pipeline.py L39-L75 at 8305160. Screenshots: the trace has 42 spans and otelTraceID 9da6b9bd...; the Grafana alert screenshot shows runbook TODO; telemetry screenshots are dated 2026-10-25, although README line 287 says 'All captured 2026-10-26'.
- Real outage: on 2026-10-25, about 09:xx-11:09 UTC, the DeepSeek balance was empty (HTTP 402) and every search on dev and prod failed. Source: commits ed50266, 6458221, 7d7b898 (work/HANDOVER-2026-10-25.md).
- 3 migrations on main are not on prod. f5a6b7c8d9e0 is irreversible; STATE.md says it will delete 3,279 prod events, 603 of them in calendars.
- 34 of the last 60 first-parent commits on main have no PR.
- Rubric source: work/rubric-2026-10-16.md. All the rubric quotes in §7-§12 match it verbatim.
- Every relative link and #anchor in lines 454-865 resolves, and every blob/8305160 reference link points at the code it describes.

<!-- guide-facts-2 summary: I checked docs/reviewer-guide.md from §7 (line 454) to the end against the repo, git, gh and plain HTTP GETs. Every relative link and #anchor in that range resolves, and all pinned blob/8305160 line ranges show the code the text describes. The CI log extract, the 4 min 52 s timeline, the 217 backend test functions, the 9 metrics, the 42 spans, the 7 containers and the 20 responder tests (I ran them: 20 OK) are also correct. The defects are elsewhere:
(1) Drills are labelled as real ("It fired for real", "The alert was real"). The guide also claims "Nobody can schedule a real outage", but a rea -->

## guide-reader-1

All checked on 2026-10-26, read-only.
- **Live sites and main:** prod /api/health = 969a16144b90. Dev /api/health = 542e58cb0fe7, the same as main and origin/main. Two code PRs landed after 8305160: 73056d0 (#150) and 0f4ed0e (#151).
- **CI runs:**
  - Run 40242394581 is on 83051604 (not current main): backend 481 passed / 4 skipped / 7 deselected (312 s), frontend 117 (12 files), integration 7, e2e 12.
  - CI on main 542e58c is run 40251535674: backend 507 passed / 4 skipped / 7 deselected (200 s), frontend 117, integration 7, e2e 12.
  - incident-response/test_responder.py has 20 `def test_`.
- **CI layout:** ci.yml L28 `uv run pytest`, L43 `npm test`, L70-71 `make test-integration` / `make test-e2e`. Makefile L29 runs the responder tests in `make test`.
- **Rubric:** work/rubric-2026-10-16.md is byte-identical to DataTalksClub/ai-dev-tools-zoomcamp project/README.md (gh api, diffed today).
- **Tracker counts:**
  - 96 issues (85 closed, 11 open). 58 with all four sections. 91/96 with an acceptance-criteria heading or checkboxes (without: 17, 21, 46, 102, 145).
  - 69 issues with a `## QA: PASS/FAIL` comment, 23 with a FAIL. 30 PRs with a verdict. 45 issues with 'closed by the orchestrator'.
  - 42 PRs merged since #66; 28 carry a QA heading. 14 have none: 67, 88, 89, 91, 92, 93, 137, 138, 140, 141, 143, 144, 146, 152.
- **Red merges:** PRs #138 and #31 merged with the integration check FAILURE (gh pr statusCheckRollup). #31 is disclosed in docs/ai-usage-report.md §8. #138 appears only in work/STATE.md.
- **Issue #134:** two `## QA: FAIL` comments and no `## QA: PASS`. The PASS is claimed in the orchestrator's closing note only.
- **Issue #11:**
  - Created 2026-10-16T18:54:46Z with a raw body of 627 characters. Groomed at 22:09:56Z. Ticked on 2026-10-20.
  - Out of scope links #12, #13, #19, #22, #25. Closing note: 'Test gaps carried to #13'.
  - Its criteria derive_queries and MAX_EVENTS_PER_RUN no longer exist in backend/app.
- **Issue #7:** QA FAIL ('400 ... echoes the raw input including the plaintext password'), then '## QA fix: db3499a', then QA PASS, then the orchestrator close. `gh issue view 7 --comments | grep -E '^## QA|^Closed by the orchestrator'` works.
- **tasks.md:** 28 tasks. Issues 1-28 match them; task 18 was split into #18 (CI) and #29 (CD).
- **plan.md change log:** 6 dated rows plus 1 'not shipped' (#101).
- **Commit subjects:**
  - 6b77835 'QA role: a dirty working tree is a FAIL'
  - 13f0fd3 'Engineer role: write only what the task needs'
  - 54dca8a 'Engineer role: merge only on green CI; issue 22 closed'
  - c0f83e6 '#135: one test runner, four phases, bug store (#137)', which introduced the regression-test rule on 2026-10-25
  - 8239e4f changed AGENTS.md by +7/-5; the big AGENTS.md rewrite is ac54483 (+34/-13)
- **Scheduled runs:** the last 40 scheduled hourly-search runs are 2.1-7.8 h apart, median about 5 h.
- **Product behaviour:**
  - Default thresholds are 90/40 at registration (routers/auth.py:100-101, main.py:58-59). Triage uses >= upper and <= lower (pipeline.py L743 at HEAD, L739-745 at 8305160).
  - The UI labels read 'Auto-accept above' and 'Auto-reject below'.
  - Rejected events are viewable through the 'N out · show' toggle (MainPage.tsx:397, 511-515).
  - After storage the model runs a duplicate check (pipeline.py:547-556).
  - The judge reason quote and score 85 match fixture backend/tests/fixtures/llm/judge_v3/b039a28fb76f3e2d.json.
- **Compose:** postgres:18-alpine with volume pgdata. SEED_DEMO defaults to 1, FAKE_NOW to 2026-10-18T12:00+02:00, LLM_PROVIDER to fake, SEARCH_PROVIDER to fixture. The Dockerfile L7 build sets VITE_API_URL="", and L25 runs `alembic upgrade head` on start.
- **Contract first:** openapi.yaml was added at 13:31 on 2026-10-16, before the routers (13:51 and 14:08). The backend scaffold (health only) was added at 12:08.
- **Links and agent files:**
  - All relative links and anchors in guide lines 1-452 resolve. The AGENTS.md link check command exits 0. AGENTS.md is 60 lines. CLAUDE.md is exactly '@AGENTS.md'.
  - .claude/agents/qa-engineer.md has tools 'Bash, Read, Grep, Glob' and says to post the verdict 'on the issue'; _docs/team/qa-engineer.md says the same.
  - The pre-commit hook runs `make test` only when code directories change. It is installed by `make hooks` (a symlink).
- **Origin of '5-10 sites':** first appears in ac54483, in README.md and _docs/plan.md. The pre-PR-152 README problem wording: 'Events surface too late or not at all because no single source lists them. Calendar aggregators only collect events you already know about, and structured filters cannot express ...'.

<!-- guide-reader-1 summary: I read docs/reviewer-guide.md from line 1 through §6 (line 452) and checked every number, sha, link, anchor and image against git, gh, CI logs, the code and live GETs. All relative links and anchors resolve. The rubric copy is byte-identical to the live one (diffed 2026-10-26). The tracker counts (96/85/11, 58, 69, 23, 30, 45) reproduce.

The defects are of six kinds:
1. **Stale facts on the first screen and in §6.** 8305160 is called "current main, and what dev runs", but main and dev both run 542e58c, two code PRs later. Backend tests are 507 on main, not 481, and the "Stale counts" risk row -->

## guide-reader-2

Rubric (work/rubric-2026-10-16.md):
- Containerization 2: "The full system, including the database, runs via Docker or Docker Compose and starts with a single command."
- Deployment 2: "The application is deployed and reachable at a public URL, or there's a clear demo with the deployment."
- CI/CD 3: "CI runs tests, CD deploys to dev, and there's a manual deploy to production." CI/CD 2: "CI runs tests and CD automatically deploys."
- Observability 2: "A key user journey is instrumented with metrics, traces, and structured logs that share a trace ID; no customer data or credentials are sent to telemetry; and the signals are collected, stored, and viewable in a UI."
- Alerting 1: "At least one alert exists." On-call 2: "An agent wakes up on an alert and fixes the issue."
- Course intro: "wire CI/CD with a rollback path", "alert on real user impact instead of CPU graphs".

Live state (HTTP GET / gh, 2026-10-26):
- prod /api/health commit 969a16144b90...; dev /api/health 542e58cb0fe7... = main head. Prod /api/config {"registrationCodeRequired":false}.
- Latest main CI run 40251535674 on 542e58c: backend 507 passed / 4 skipped, frontend 117, integration 7, e2e 12. Guide §6 still says backend 481 (from run 40242394581 on 8305160).
- promote.yml: 15 runs, all workflow_dispatch, all success; run 39979831552 polled until 'prod is healthy on 969a161...' (previous prod 571b751).
- hourly-search.yml: last 30 runs all success; gaps between scheduled runs 2.47-5.84 h; it only enqueues (POST /api/search/all -> BackgroundTasks).
- main has no branch protection (gh api 404). 79 first-parent commits since 2026-10-20 have no PR; PRs #31 and #138 merged with integration FAILURE (#138 merged before backend finished).

Code and config:
- telemetry.py does nothing without OTEL_EXPORTER_OTLP_ENDPOINT. Only docker-compose.observability.yml sets it, so prod exports no telemetry. APP_VERSION defaults to 'dev'.
- Compose defaults: SEARCH_PROVIDER=fixture, LLM_PROVIDER=fake, FAKE_NOW=2026-10-18T12:00:00+02:00, SEED_DEMO=1, JWT_SECRET empty.
- Dockerfile line 25: `alembic upgrade head && uvicorn`. Three migrations were added after 969a161, including irreversible f5a6b7c8d9e0 (DELETE events without a T; downgrade pass).
- Alert rules: SearchRunFailures `increase(...{outcome="error"}[10m]) > 1`, for 5m, noDataState NoData. SearchRunsSilent `increase(sail_runs_total[2h]) < 1`, for 10m, noDataState OK. Both severity=critical, routed to the webhook with Bearer. Alerts are checked per series (alert.json labels include trigger, outcome, exported_instance).
- responder.py ALLOWED_TOOLS includes bare Read and Edit (not path-limited). Agent env passes HOME and SKIP_HOOK_TESTS=1; model sonnet, --max-budget-usd 1, timeout 300. Webhook URL default http://host.docker.internal:8001/alerts (runs on the host). security-audit/capability-table.md last changed 2026-10-16 and is out of date.
- test-incident.sh injects the fault (renames the real method to _search_original), commits 'test: inject search-provider fault', starts responder.py, curls failing searches with SEARCH_NOW_PER_HOUR=1000, waits for Grafana to fire. Cleanup restores the branch.

Incidents:
- 2026-10-21: fault 3d9f6b8 at 07:32:59Z; alert startsAt 07:41:20Z (alert says 24 failed, evidence 28.04); evidence collected 07:41:50Z with an empty Loki section; fix 8d2f839 at 07:46:12Z, authored by alexisdacquay, +1 -4, made with SKIP_HOOK_TESTS=1; 217 backend test functions at 8d2f839; agent.log claims '84 ... tests pass' and '~28 errors/min'.
- 2026-10-17: fault 7318f2f 'test: inject scorer fault', alert 05:20:20Z, fix dae24e9 at 05:23:32Z, Loki section also empty.
- Neither fault commit is on main.

Other checks:
- deployment.md lacks 9 variables the backend reads: APP_VERSION, BRAVE_API_KEY, CORS_ORIGINS, DETAIL_FETCH_MAX_BYTES, DETAIL_FETCH_TIMEOUT, JWT_EXPIRY_MINUTES, LLM_TIMEOUT_SECONDS, LOG_LEVEL, OTEL_EXPORTER_OTLP_ENDPOINT.
- All relative links, anchors and the 14 images in §7 to the end resolve. Pinned code line ranges (pipeline L39-76, L109-126; main L26-37, L117-119) match 8305160.
- 21 issues lack both mvp and post-mvp: 94-96, 99-102, 104, 106, 108, 109, 112, 113, 116, 118, 120, 122, 124-126, 131. #139 and #142 have no QA comment; #39, #52 and #55 have one QA FAIL each.

Not checked: Render dashboard settings and env values (not read, to avoid exposing secrets); screenshot contents other than review-43 and review-36b. The SearchRunsSilent per-series false alarm is inferred from Grafana's per-series checking and the alert.json labels; it was not seen live.

<!-- guide-reader-2 summary: I reviewed docs/reviewer-guide.md from §7 to the end, plus the Known gaps table, the link block and "Check it in 5 minutes". I checked every claim against files, git, gh and plain HTTP GETs. It is not just wording that is wrong. Several claims are false or stale, and the honest-sounding sections leave out the biggest gaps.

Wrong or stale facts:
- Dev now runs 542e58c, not 8305160. The code links are pinned to a commit that runs nowhere.
- The rollback claim fails after the planned promote. The start command runs `alembic upgrade head`, the old code does not know the new migration revisions, a -->

## readme-reader

Verified on 2026-10-26 (sources in brackets):
- Prod /api/health = 969a16144b909f57359f38f8a5f8e05a0ef5b491; dev = 542e58cb0fe73065a905febec7637bfa377a77c4 [curl]. /api/config on both: {"registrationCodeRequired":false} [curl].
- Last prod promote: run 39979831552, 2026-10-23T15:37Z, sha 969a161. 15 promote runs on record, every one to a newer sha, so a rollback has never been run [gh run list --workflow=promote.yml; inputs read from the run logs].
- work/STATE.md L119: on 2026-10-20 prod deployed main 487cb1a through a Render env change, with no promote.yml run.
- work/STATE.md L8: the next promote runs PR 150's migration, which deletes 3,279 date-only events on prod (603 in calendars) and cannot be undone. 969a161→main adds 3 Alembic migrations: a6b7c8d9e0f1, e4f5a6b7c8d9, f5a6b7c8d9e0. f5a6's downgrade is `pass`. Dockerfile L25 runs `alembic upgrade head` on start.
- Tracker [gh, process.md commands]: 96 issues, 85 closed; 58 groomed in all four sections; 69 with a QA verdict; 23 with a FAIL; 30 of 56 PRs with a QA verdict.
  - Closed with no Goal/AC groom: 145,126,125,124,122,120,118,116,113,112,109,108,106,104,83,46,21,17.
  - Closed with no QA verdict: 142,139,136,74,60,59,29,21,17.
  - #33-#36 are closed, each with one '## QA: PASS'. Issue #7 shows QA FAIL (password echoed in a 400), then fix db3499a, then QA PASS.
- CI:
  - Run 40242394581 = push on 8305160: backend 481 passed, frontend 117, integration 7, e2e 12; backend job ~5 min.
  - Latest main run 40251535674 (542e58c): backend 507 passed, 117, 7, 12; backend pytest 3m19s.
  - The 20 responder tests are not run in CI.
- Hourly search: cron '7 * * * *', POSTs to vars.SAIL_BASE_URL (prod per docs/deployment.md L45). The last 25 scheduled runs are spaced 2.5-5.9 h apart. The app has no in-process scheduler.
- Alerts [rules.yaml]:
  - SearchRunFailures: increase(sail_runs_total{outcome="error"}[10m]) > 1 for 5m.
  - SearchRunsSilent: increase(sail_runs_total[2h]) < 1 for 10m, described as 'the hourly scheduler may be stopped'.
  - Telemetry is on only when OTEL_EXPORTER_OTLP_ENDPOINT is set. Local stack only (observability/README.md L107).
- Incidents:
  - 2026-10-21: alert.json startsAt 07:41:20Z, status firing. Fix commit 8d2f839 at 07:46:12Z (4 min 52 s), on GitHub on branch incident/20261021-074150-SearchRunFailures.
  - 2026-10-17: fault commit 7318f2f 'test: inject scorer fault', fix dae24e9. The 10-21 fault commit is 3d9f6b8 'test: inject search-provider fault'.
  - The Loki part of the evidence came back empty (incident-response/README.md L43). Responder budget: --max-budget-usd 1, timeout 300 s.
- All README screenshots were committed in ac54483 (PR 152) on 2026-10-26, including review-43 (alert firing), so that image is not from the 10-21 run.
- Product behaviour on main:
  - Search query = criteria_text + ' event' (pipeline.py L289). A model first parses the sentence into facets (criteria stage).
  - Code screens out: no start date, no start time, a missing field, already over, same page and date already stored. Place and date are judged by the model, not by code.
  - After storage, a dedup_v1 model call moves duplicates to Out (#136). Screenshot review-05b shows rows at 95% and 90% marked Out.
  - Out rows can be listed via a 'N out ... show' link (review-06, review-05b).
  - Triage: score >= upper → accepted, <= lower → rejected (pipeline.py at 8305160 L739-746).
- UI labels:
  - Scoring inputs read 'Auto-reject below' and 'Auto-accept above'. The legend reads 'Out / You decide / Your calendar', and is clipped in review-07.
  - Statuses read 'In calendar / Review / Out'; the funnel says 'in calendar / to review / rejected'. The button reads 'Search again' after the first run.
  - Prod (969a161) differs: the funnel says 'not judged', not 'screened out', and the placeholder says 'e.g. jazz or folk concerts near Paris on weekends, under 40 EUR'.
- Limits: SEARCH_NOW_PER_HOUR=6 per user; 5 registrations per IP per hour; criteria text max 2000 characters.
- Local demo: FAKE_NOW defaults to 2026-10-18T12:00+02:00 in compose and the Makefile, so the recorded 19-21 Oct fixtures stay in the future. Dev seeds the shared demo/demo account with the sentence 'jazz in Berlin (Germany) next week (19-21st October 2026)'. FAKE_NOW is unset on dev (STATE.md); prod has no demo user.
- `make up-all` / observability-up / responder require `export RESPONDER_WEBHOOK_SECRET` (Makefile comments). Dashboard title: 'Sail-event — Search Run Journey'.
- Node: .nvmrc 24, Dockerfile node:24-alpine, CI node 22.
- Contract: backend/tests/test_schema_contract.py compares paths, methods and operationIds of openapi.yaml with the app's /openapi.json; CI also runs redocly lint.
- Rubric (work/rubric-2026-10-16.md): 12 criteria, 24 points, pass at 10; CI/CD 3 levels up to 3, Alerting max 1.
- Cross-doc defects found while checking README links:
  - docs/reviewer-guide.md L16 and its 'Check it in 5 minutes' block say dev runs 8305160; dev runs 542e58c (stale).
  - docs/ai-usage-report.md heading L26 says 'Defects the orchestrator caught', while its bodies say 'QA found it'.
  - _docs/plan.md L36 contains the same invented 'Open 5-10 sites a day' row.
- Not verified: the Postgres version on Render; which search provider and guardrail prod uses now. The Render MCP needs the owner to pick a workspace, and plain GETs cannot tell. Alembic failing to start the old image after a forward migration is expected behaviour but was not run.
- All relative links in README.md resolve to existing files.

<!-- readme-reader summary: I read README.md from top to bottom against the repo, git, gh, the CI logs, plain HTTP GETs to prod and dev, and the README's own screenshots. It has many more defects than the six calibration items. The worst ones are structural, not wording.

1. **The first action sends reviewers to the wrong build.** "Try it in 60 seconds" sends reviewers to prod (969a161), but the README describes main/dev. Prod lacks the "screened out" funnel, the detail-page hop, the no-start-time drop, the model duplicate check, Exa and the one-action search box. The title is also false: the same README says a live sear -->

## readme-facts

Verified on 2026-10-26 (sources in brackets):
- Rubric: 12 criteria worth 24 points, 10 to pass. CI/CD has a 3-point level ("CI runs tests, CD deploys to dev, and there's a manual deploy to production"). Alerting tops out at 1 ("At least one alert exists"). On-call 2 = "An agent wakes up on an alert and fixes the issue". Observability 2 includes "no customer data or credentials are sent to telemetry". The intro asks for "CI/CD with a rollback path". [gh api repos/DataTalksClub/ai-dev-tools-zoomcamp/contents/project/README.md, copy at /private/tmp/claude-503/-Users-ad-code-ProjectOne/88df4b5e-b416-4a37-ba3b-18ed01c2a6a0/scratchpad/rubric.md]
- Prod /api/health = 969a16144b909f57359f38f8a5f8e05a0ef5b491 (commit date 2026-10-23, promote run 39979831552 at 2026-10-23T15:37Z). Dev = 542e58c (main HEAD). /api/config on both = {"registrationCodeRequired":false}. [curl]
- Prod is 39 commits / 18 merged PRs behind main. Missing on prod: the #121 search box, #123 progress hairline, #141/#151 event-page hop, #134 no-time filter, #144 concurrency 10, #146 'screened out' funnel, #147 Exa, #149 model dedup, #150 deleting events without a start time. Prod funnel labels: found / judged / not judged / not accounted / in calendar / to review / out. [git log 969a161..542e58c; git show 969a161:frontend/src/components/Funnel.tsx]
- CI run 40242394581 ran on 8305160: backend 481 passed, frontend 117, integration 7, e2e 12. Latest main run 40251535674 (542e58c): backend 507, frontend 117, integration 7, e2e 12. test_data_survives_restart PASSED in both. [gh run view --log]
- The UI has no 'Register' control: the login link reads 'Create one', the form button 'Create account'. The search button reads 'Search now' before the first run and 'Search again' after. [frontend/src/pages/LoginPage.tsx L91, RegisterPage.tsx L107, MainPage.tsx L433]
- Out events stay visible on demand: '16 out ... · show' and rejected-toggle. [e2e/journeys.spec.ts L93-101, review-06 screenshot]
- Hourly cron '7 * * * *' targets prod only (repo var SAIL_BASE_URL=https://sail-event.onrender.com). Last 50 scheduled runs: gaps 2.1-7.8 h, median 4.5 h, all successful. [gh run list --workflow hourly-search.yml; gh variable list]
- Measured live-adapter search durations: 86-493 s (PR 144 body), 124 -> 208 s with the hop (work/HANDOVER-2026-10-25.md:73). No source supports '1-2 minutes' on current code.
- Dev runs FAKE_NOW=2026-10-18T12:00:00+02:00 and SEED_DEMO=1 [docs/deployment.md L83]. Compose and make run also default FAKE_NOW to 2026-10-18 [docker-compose.yml, Makefile L7].
- Defaults: thresholds 90/40, accept if score >= upper, reject if <= lower [auth.py:100-101, pipeline.py:743-746]; SEARCH_NOW_PER_HOUR 6 [search.py:152]; REGISTER_RATE_LIMIT_PER_HOUR 5 [auth.py:56]; query = sentence + ' event', max 20 results [pipeline.py:279,286].
- Issues: 96 total, 85 closed, 58 groomed into all four sections, 69 with a QA verdict, 23 with a QA FAIL. PRs: 56 total, 30 with a QA verdict, first PR #30 (2026-10-17). [process.md commands, rerun]
- First-parent commits on main: 267; 30 carry '(#N)'. [git log --first-parent]
- Incidents: two, both drills. 2026-10-17 (fault 7318f2f, fix dae24e9) and 2026-10-21 (fault 3d9f6b8 at 07:32:59Z, alert startsAt 07:41:20Z, fix 8d2f839 at 07:46:12Z = 4 min 52 s). Both incident/ branches are on origin (git ls-remote). The responder runs model sonnet with --max-budget-usd 1 and timeout 300 s, on port 8001 by default; push is denied by incident-response/autonomy-policy.yaml.
- Alert rules: SearchRunFailures = increase(sail_runs_total{outcome="error"}[10m]) > 1 for 5m. SearchRunsSilent = increase(sail_runs_total[2h]) < 1 for 10m with noDataState OK. Grafana runs only in the local stack (anonymous Admin, port 3001). The dashboard is titled 'Sail-event — Search Run Journey', uid sail-event-overview.
- Custom metrics: 10 (9 in pipeline.py, plus sail_guard_runs_total in adapters/factory.py:165). The Tempo screenshot shows 42 spans for trace 9da6b9bd..., and the same id appears in the Loki screenshot.
- 20 responder tests (incident-response/test_responder.py) run in make test; CI does not run them.
- openapi.yaml was committed first (a3dd774, 13:31) and the routers after (13a9fe4, 13:51, 2026-10-16); CI lints it with redocly.
- Stack versions: react 19.3.1, vite 8.3.4, tailwind 4.3.3, vitest 5.0.5, shadcn 4.22.0, fastapi 0.143.0, sqlalchemy 2.1.5, alembic 1.20.0, pyjwt 2.15.1, bcrypt 5.0.0, icalendar 7.3.0. Dockerfile: node:24-alpine and python:3.12-slim; CI uses node 22; postgres:18-alpine; Render Postgres 18 per work/DEPLOY-render.md.
- 'Open 5-10 sites a day' is absent from plan.md before ac54483; it was introduced in PR 152.
- The only full ground-truth recall run on record: 3/38 (7.9%), local, ab21641, 2026-10-24 [work/RECALL.md L139-155]. Recall after the event-page hop was never measured [PR 141].
- The app's sign-in pitch on main and prod is still 'Tell it what events you like, in plain words. It searches the web every hour, ...' [LoginPage.tsx L9-10].

<!-- readme-facts summary: I checked every factual claim in README.md (301 lines) against git, gh, CI logs, the code at 969a161 (prod) and 542e58c (main), the screenshots and plain HTTP GETs. All relative links and #anchors resolve, and the pinned #L anchors at 8305160 point at the right tests. Several numbers check out: the issue/PR counts (58, 69, 23, 30), the incident timings (07:41:20 → 07:46:12, 4 min 52 s), the promote date, the 7th-search 429, the 90/40 boundaries, open registration (/api/config), the restart-persistence test, and the dashboard title.

The content has serious problems:
(1) The README sends review -->

## guide-facts-1

Verified on 2026-10-26 from worktree /private/tmp/claude-503/-Users-ad-code-ProjectOne/88df4b5e-b416-4a37-ba3b-18ed01c2a6a0/scratchpad/wt-dq:

Live versions and CI
- `curl https://sail-event.onrender.com/api/health` gives commit 969a16144b90... (prod).
- `curl https://sail-event-dev.onrender.com/api/health` gives commit 542e58cb0fe7... (dev = main head).
- Commits on main after 8305160: 73056d0 (#150), 0f4ed0e (#151), ac54483 (#152), 542e58c.
- `gh run list --workflow ci.yml --branch main`: the run for the main head is 40251535674 (542e58c). 40242394581 is for 8305160.
- Counts from `gh run view --log`:
  - 40242394581 (8305160): 481 passed, 4 skipped, 7 deselected, 312.96 s; 117 Vitest (12 files); 7 integration; 12 Playwright.
  - 40251535674 (542e58c): 507 passed, 4 skipped, 7 deselected, 199.80 s; 117; 7; 12.
- The Playwright log shows 2 tests marked ✘ that count as passed: field.spec.ts:48 and :72 use `test.fail(true, ...)` for open issues #94 and #95.
- Three of the 12 Playwright tests are screenshot generators: screenshot-122.spec.ts in light and dark, and journeys.spec.ts:139.

Responder tests
- `python3 incident-response/test_responder.py`: "Ran 20 tests in 0.537s OK", 1.4 s wall time. The 202 test posts a "resolved" alert, which the handler ignores, so no agent is spawned.

Rubric
- work/rubric-2026-10-16.md is byte-identical (cmp) to raw.githubusercontent.com/DataTalksClub/ai-dev-tools-zoomcamp/main/project/README.md (5142 bytes).
- The rubric says: "There are 12 criteria worth 24 points. You need 10 points to pass." All quoted rubric levels in §1-§6 match it.

Tracker counts
- The guide's five gh commands give 58, 69, 23, 30, 45.
- 96 issues: 85 closed, 11 open. Repo visibility is PUBLIC.
- GraphQL ClosedEvent.closer lists 8 issues closed by a PR merge: #46, #52, #68, #76 (PR #86), #83, #120, #122, #142.
- Issues with neither the mvp nor the post-mvp label: 21 (#94-#131).
- _docs/outdated/tasks.md has 28 tasks. Issue #29 ("S9 — CD to dev on merge") was split out of task 18.

Role-file history
- `git log -S` shows the root-cause gate, "red test first" and "FAIL any bug fix without a regression test" first entered _docs/team in c0f83e6 on 2026-10-25.
- Project span: first commit 8ba8df7 on 2026-10-15, last commit 2026-10-26.

Prod vs main UI
- Prod 969a161 frontend Funnel.tsx labels the step "not judged". Main labels it "screened out" (owner change on 2026-10-25).
- The `rejected-toggle` that shows Out rows exists in both prod and main MainPage.tsx.

Other code facts
- The pinned line anchors at 8305160 are correct. On main, pipeline triage moved to L743.
- The Makefile `test` target runs pytest, npm test and test_responder.py (L29).
- `test-all` is test, then test-integration, then test-e2e.
- ci.yml L28, L43, L70 and L71 are as cited.
- scripts/pre-commit runs `make test` only when backend/, frontend/src/ or incident-response/ files are staged. It is skippable with SKIP_HOOK_TESTS=1.
- The event uniqueness constraint was dropped in 73056d0 (#150). _docs/architecture.md still lists UNIQUE(user_id, link, date_time).
- The worked example comes from backend/app/adapters/fixtures.json entry E4 (a hand-made fixture page, berlin-workshops.de). Its judge answer is recorded live in backend/tests/fixtures/llm/judge_v3/b039a28fb76f3e2d.json (score 85; the quoted reason matches).
- Measured gaps between the last 50 scheduled hourly-search runs (cron '7 * * * *'): 2.1 h to 7.8 h. Two gaps exceed 6 h.
- The sign-in PITCH constant is two sentences ("Tell it what events you like, in plain words. It searches ..."). The README's opening is three different sentences.

<!-- guide-facts-1 summary: I reviewed docs/reviewer-guide.md from the top through §6 (lines 1-452). Every relative link and #anchor resolves (122 checked). Every pinned blob, issue, PR, commit and CI URL returns 200. The rubric copy is byte-identical to the live rubric. The five gh counting commands still give 58/69/23/30/45, and the 96/85/11 issue totals are correct. The 20 responder tests pass in 0.5 s.

The defects that matter:
1. The 5-minute check and line 16 say dev and main are at 8305160. Both are at 542e58c. The test counts (481) and the CI run come from that older commit; main's CI now shows 507 backend tests. -->

## rubric

OFFICIAL RUBRIC, verbatim. Source: `gh api repos/DataTalksClub/ai-dev-tools-zoomcamp/contents/project/README.md -H 'Accept: application/vnd.github.raw'`, last changed 2026-10-16 (commits 3ef6f18 'Revise project criteria and scoring', 526d9c1 'Lower project pass threshold to 10 points'). `diff` against work/rubric-2026-10-16.md prints nothing (IDENTICAL, checked 2026-10-26).
"There are 12 criteria worth 24 points. You need 10 points to pass. You do not have to score full marks on every criterion."
Problem Description: "The problem is not described. (0 points)" / "The problem is described briefly, but it is unclear what the system does or what functionality is expected. (1 point)" / "The README clearly describes the problem, the system functionality, and expected behavior. (2 points)"
Product Specification: "No written specs. (0 points)" / "A spec exists, but no public task tracker. (1 point)" / "A specification exists and there's a publicly accessible task tracker. The tasks define acceptance criteria and there's evidence that the agents used the tracker. (2 points)"
Agent Team Specification: "No agent team described. (0 points)" / "Roles or agents are mentioned, but responsibilities are unclear. (1 point)" / "The project defines the agent team and process of how they work together. (2 points)"
Context Management: "No project docs. (0 points)" / "An AGENTS.md (or equivalent) exists and describes the project. (1 point)" / "AGENTS.md exists and it also points to modular docs (process, teams, etc.). (2 points)"
Application: "No working application, or frontend, backend, or persistent storage is missing. (0 points)" / "Frontend, backend, and database exist but are not fully connected. (1 point)" / "Full-stack application works end to end: frontend talks to backend, data persists in a database. Application runs locally with a single command. (2 points)"
Testing: "No tests, or the tests do not run. (0 points)" / "Only unit tests or only integration tests exist. (1 point)" / "Both unit and integration tests exist, run with a single command, and pass. (2 points)"
Containerization: "No containerization. (0 points)" / "Dockerfiles exist, but running the full system requires manual steps. (1 point)" / "The full system, including the database, runs via Docker or Docker Compose and starts with a single command. (2 points)"
Deployment: "Application is not deployed. (0 points)" / "Deployment steps are described, but no working deployment is shown. (1 point)" / "The application is deployed and reachable at a public URL, or there's a clear demo with the deployment. (2 points)"
CI/CD: "No CI/CD pipeline. (0 points)" / "CI runs the tests automatically on every pull request. (1 point)" / "CI runs tests and CD automatically deploys. (2 points)" / "CI runs tests, CD deploys to dev, and there's a manual deploy to production. (3 points)"
Observability: "No telemetry. (0 points)" / "The app emits logs, but there are no metrics or traces, or the signals cannot be correlated to a single request. (1 point)" / "A key user journey is instrumented with metrics, traces, and structured logs that share a trace ID; no customer data or credentials are sent to telemetry; and the signals are collected, stored, and viewable in a UI. (2 points)"
Alerting on User Impact: "No alerts. (0 points)" / "At least one alert exists. (1 point)"
On-Call Agent: "No on-call agent. (0 points)" / "An agent wakes up on an alert and fixes the issue. (2 points)"
The course intro also lists: "specify the problem and its acceptance criteria before writing the code"; "cover it with unit, frontend, and integration tests"; "wire CI/CD with a rollback path"; "instrument it and alert on real user impact instead of CPU graphs"; "create an alert trigger"; "implement a responder agent".

ATOMIC PHRASES FOR FULL MARKS, in rubric order (for the guide's checklists):
1: README · clearly · describes the problem · the system functionality · expected behavior. Risk: 'described briefly' / 'unclear what the system does or what functionality is expected'.
2: a specification exists · publicly accessible task tracker · tasks define acceptance criteria · evidence the agents used the tracker. Risk: 'no public task tracker'.
3: roles or agents mentioned · responsibilities clear (not 'unclear') · defines the agent team · process · how they work together.
4: AGENTS.md exists · describes the project · points to modular docs · (process · teams · etc.).
5: works end to end · frontend talks to backend · data persists in a database · runs locally · single command. Risk: 'not fully connected'.
6: unit tests exist · integration tests exist · run with a single command · pass. Risk: 'only unit or only integration'.
7: full system · including the database · Docker or Docker Compose · single command. Risk: 'manual steps'.
8: deployed · reachable at a public URL (or clear demo). Risk: 'steps described, no working deployment'.
9: CI runs tests (on every PR) · CD deploys to dev (automatically) · manual deploy to production.
10: key user journey · metrics · traces · structured logs · share a trace ID · no customer data · no credentials · collected · stored · viewable in a UI.
11: at least one alert exists (title: on user impact).
12: an agent · wakes up on an alert · fixes the issue.

VERIFIED STATE (2026-10-26):
- Prod health: `curl -s https://sail-event.onrender.com/api/health` gives commit 969a16144b90.
- Dev health gives 542e58cb0fe7. `git ls-remote ... refs/heads/main` gives 542e58c.
- Prod /api/config gives registrationCodeRequired false.
- 39 commits on main after 969a161: `git log --oneline 969a161..origin/main | wc -l`.
- CI run 40242394581: push on 8305160, all 3 jobs success. Backend 481 passed, 4 skipped, 7 deselected (312.96 s). Frontend 117. Integration 7 (test_data_survives_restart PASSED). e2e 12. Integration job id 121317996594.
- Latest main CI run 40251535674 (542e58c): backend 507 passed, frontend 117, integration 7, e2e 12.
- Responder: `python3 -I incident-response/test_responder.py` ran 20 tests, OK.
- Issues: 96 total, 85 closed, 11 open. 58 have all 4 template headings. 91 contain the text 'acceptance criteria'. Only 4 have no 'acceptance' word at all (#17, #21, #102, #145).
- QA verdicts: 69 issues have one, 23 have a FAIL. 30 of 56 PRs carry one. 45 issues have 'closed by the orchestrator'.
- Closed with no QA verdict on the issue or its PR: #17, #21, #29, #59, #60, #74, #139, #142.
- Issues closed by a PR via GitHub: #46, #52, #68, #76, #83, #120, #122, #142 (8, not 7).
- Of 42 PRs merged since #66, 14 have no QA verdict on the PR. With no linked issue: #67, #88, #89, #91, #92, #93, #146, #152.
- tasks.md has 28 tasks. Issues 1-28 match except #18 (renamed). #29 is not in tasks.md.
- Spec before code: plan.md fa345ba 2026-10-15 23:19 -0700; AGENTS.md/process/roles 98f3cf7 2026-10-16 11:50; first code 6ccfdec 2026-10-16 12:08.
- Root-cause gate: added to the role files in c0f83e6 (2026-10-25); added to process.md in ac54483 (2026-10-26).
- promote.yml: 15 runs, all workflow_dispatch, all success, every sha moved forward (10d4701 … 969a161). Rollback never run.
- hourly-search: 50 scheduled runs (10-17 to 10-26). Gaps: min 2.1 h, median 4.5 h, max 7.8 h. All success. /api/search/all returns 202 after queuing background tasks (backend/app/routers/search.py L290-313).
- Incidents: 3d9f6b8 'test: inject search-provider fault' (07:32:59Z). Alert startsAt 07:41:20Z. Fix 8d2f839 at 07:46:12Z. 3d9f6b8 is not an ancestor of main. 2026-10-17 fault 7318f2f 'test: inject scorer fault', fix dae24e9. In the 2026-10-21 evidence.md: Loki returned 0 lines, health commit "", deployed version 'unknown'.
- autonomy-policy.yaml is read by no code (git grep). Enforcement is responder.py: ALLOWED_TOOLS L27-33 (plain 'Edit', no path limit), --max-budget-usd 1 (L159), timeout=300 (L166).
- Real outage: work/HANDOVER-2026-10-25.md L61, 'DeepSeek balance ran out (HTTP 402 ...), searches on dev/prod failed'.
- Telemetry is on only when OTEL_EXPORTER_OTLP_ENDPOINT is set (observability/README.md L107). docs/deployment.md's env table lists no such variable.
- GitHub has no deployment records: `gh api repos/alexisdacquay/sail-event/deployments` is empty.

<!-- rubric summary: I fetched the official rubric with `gh api repos/DataTalksClub/ai-dev-tools-zoomcamp/contents/project/README.md`. It is byte-identical to work/rubric-2026-10-16.md, so the guide's rubric quotes are correct. All relative links and #anchors in README.md, docs/reviewer-guide.md and AGENTS.md resolve, and every pinned code-line link lands on the test or code it names. Today's live counts (58/69/23/30/45, 96/85/11) match.

The mapping itself has structural and factual gaps that a careful reviewer will hit:
1. Every 'Checklist' table mixes made-up rows with paraphrased rubric phrases, out of the rub -->

## team-docs

Verified on 2026-10-26. R=alexisdacquay/sail-event. Local JSON dumps of all issues and PRs are in /private/tmp/claude-503/-Users-ad-code-ProjectOne/88df4b5e-b416-4a37-ba3b-18ed01c2a6a0/scratchpad/dqv/.

**Tracker counts**
- 96 issues (85 closed, 11 open) and 56 PRs.
- 58 issues have all four groom sections; the process.md regexes reproduce 58/69/23/30/45 exactly.
- 91 of 96 issues have the words "acceptance criteria" plus checkboxes. Only #17, #21, #46, #102 and #145 have neither.
- The 38 ungroomed issues include 27 closed ones: 17, 21, 46, 65, 68, 70, 71, 73, 74, 76, 77, 81, 83, 104, 106, 108, 109, 112, 113, 116, 118, 120, 122, 124, 125, 126, 145.
- 21 issues carry neither mvp nor post-mvp: 94-131.
- Other labels: enhancement 11, search-v2 10, ux 7, bug 5, theme 3, robustness 3.
- All 373 comments are authored by alexisdacquay (gh api repos/$R/issues/comments).
- 173 of 373 comments start with none of the prefixes in process.md "Who wrote a comment". Examples: "## S5 implementation complete" (#7), "## QA FAIL" (PR #66, #85), "## QA final check: PASS" (#122), "PR: https://" (10 comments), "Owner decisions, 2026-10-25 (recorded by the orchestrator)" (#136, #145), "Closed by the owner, ..." (PRs 97, 98, 132, 133).

**Who closed what**
- GitHub ClosedEvent.closer shows a PR closed 8 issues: #46←PR47, #52←PR53, #68←PR69, #76←PR86, #83←PR84, #120←PR121, #122←PR123, #142←PR143.
- Query: `gh api graphql -f query='{repository(owner:"alexisdacquay",name:"sail-event"){issues(first:100,states:CLOSED){nodes{number timelineItems(itemTypes:[CLOSED_EVENT],last:1){nodes{... on ClosedEvent{closer{__typename ... on PullRequest{number}}}}}}}}}'`
- Closed with no QA verdict on the issue or its PR: #17, #21, #29, #59 ("Closed by the orchestrator on the engineer's report"), #60 (PR #64 has 0 comments), #74 (no PR or commit references it), #139, #142.
- PRs existed before #65: #30, #31, #32 (2026-10-17), #45, #47, #51, #53, #64. PR #66 is the first PR with a `## QA` verdict.

**Live state and commits**
- GET /api/health: prod 969a16144b909f57359f38f8a5f8e05a0ef5b491, dev 542e58cb0fe73065a905febec7637bfa377a77c4.
- main is 542e58c; `git diff --stat 8305160 542e58c` shows 131 files.
- Prod 969a161 has no detail_hop.py, dedup.py or search_exa.py, no filtered_no_time, and no "screened out" in MainPage.tsx.
- Search query = criteria text + " event": backend/app/services/pipeline.py L286 (L271 at 969a161).
- Event has only ck_event_status; UNIQUE(user_id, link, date_time) was dropped by 73056d0 (#150).
- promote.yml: 15 successful runs, 2026-10-17T23:00 to 2026-10-23T15:37. 14 predate the owner rule of 2026-10-21 ("do not promote to prod without me checking first", memory file feedback-no-prod-promote-without-owner.md). The other owner rule, "I want to decide myself by priority", is also dated 2026-10-21.
- Hourly search: repo var SAIL_BASE_URL=https://sail-event.onrender.com, so the hourly job hits prod only. 52 runs from 2026-10-17 to 2026-10-26; gaps 0.5-7.8 h, median 4.5 h.
- Only open PR: #103 (6 files, not ScoreScale.tsx).

**When process rules started (git log -S)**
- process.md sections Root-cause gate, Phase 2, Who wrote a comment, Evidence and Never does: ac54483 (2026-10-26).
- "committed while red" in the engineer role: c0f83e6 (2026-10-25).
- QA agent file created a41b405 (2026-10-17).
- The original process.md (98f3cf7, 2026-10-16) had Lifecycle step 1 "Pick the next issue", with no owner.

**Pre-commit hook**
- scripts/pre-commit runs `make test` on backend/, frontend/src/ or incident-response/ changes; SKIP_HOOK_TESTS=1 skips it.
- work/STATE.md L152 and L160: "engineers commit with SKIP_HOOK_TESTS=1 after `make test`".

**Session transcript** (/Users/ad/.claude/projects/-Users-ad-code-ProjectOne/88df4b5e-b416-4a37-ba3b-18ed01c2a6a0.jsonl; local, not public; starts 2026-10-16T05:03Z)
- Each role is started as a general-purpose subagent (model opus, run in background). The brief reads like this: "You're a Software Engineer on the Sail-event project ... Your role is defined in `_docs/team/software-engineer.md`; read it first and follow it exactly. Read `AGENTS.md`, `_docs/architecture.md`, `openapi.yaml` ...", plus issue-specific notes and a reply format.
- The PM brief also lists process.md, task-template.md and plan.md.
- QA launches: 63 as general-purpose with full tools (2026-10-16 to 10-20, plus 2 on 10-25); 49 as the qa-engineer agent (from 2026-10-20).
- Re-checks sent to the same QA agent via SendMessage: #6, #7 ("The engineer fixed issue #7 in commit db3499a. Re-verify"), #19, #27.
- The main session ran `gh issue create` about 40 times and made about 30 Edit/Write calls on backend/frontend/e2e/incident-response files, e.g. backend/app/routers/health.py (10-17), frontend/src/pages/MainPage.tsx (10-18, 10-20), incident-response/responder.py (10-21).

**Other verified numbers and anchors**
- Measured run time: issue #145 records about 300 s on dev (303.9 s); locally 298 s on main and 137 s on the PR 144 branch.
- Runner numbers are correct: 13 invariants (I1-I13), 20 BATCH_TEXTS, 38 ground-truth events in 10 triples.
- work/RUN-LOG.md is 7 lines with no run logged.
- tasks.md has 29 tasks.
- Issue #11 edit history: the first version is 627 chars; it has 15 criteria.
- Anchors still correct at HEAD: test_pipeline L306, test_events L111/L150, test_integration L103, test_calendar L112/L255, test_guardrails L404, journeys L37-67/L60-67/L158, ScoreScale L80-86, main.py L117-119, Dockerfile L7/L25, api.ts L67.
- Anchors wrong at HEAD (they matched 8305160): filters.py L197-200 (now 195-197), L202-205 (200-202), L207-210 (205-207), L212-216 (210-213), L220-226 (217-221); pipeline.py L739-745 (now 743-750) and L611 (now 615); test_integration L131 (now 135) and L250 (now 254).
- Stack versions in architecture.md all match package.json and pyproject.
- Makefile `test` also runs incident-response/test_responder.py.
- compose has only the postgres and app services.
- The guardrail runs on PUT /api/criteria (routers/criteria.py L56-58).
- Daily caps: SEARCH_DAILY_CALLS 600 and LLM_DAILY_CALLS 5000 (services/budget.py).

<!-- team-docs summary: I read all 8 files from start to end and ran checks against git, gh (GraphQL included), the code, the live /api/health GETs and the local session transcript (read-only). The counts in process.md reproduce exactly: 58, 69, 23, 30 and 45. Every relative link and #anchor resolves.

The defects are elsewhere, and they are serious:

1. **Rules applied backwards in time.** process.md takes rules that started late and presents them as if they held from day one: "Owner picks", "approves every prod promote", the root-cause gate and red test first. The owner rules date from 2026-10-21, the gate from 202 -->

## ops-docs

Verified on 2026-10-26 (HTTP GETs, gh, git):
- Prod /api/health: commit 969a16144b909f57359f38f8a5f8e05a0ef5b491 (= 969a161, 'docs: Sankey funnel built (PR 119)', a direct push to main). Dev /api/health: 542e58cb0fe73065a905febec7637bfa377a77c4, the same as remote main. Both /api/config: {"registrationCodeRequired":false}.
- reviewer-guide L16 and L43 ('8305160 (current main, and what dev runs)') are stale: dev and main are 542e58c.
- promote.yml: 15 runs, all workflow_dispatch, all success, every one moving forward (no rollback ever). The latest is 39979831552 on 2026-10-23T15:37Z, promoting 969a161, healthy at 15:39:22Z. Prod was also deployed outside promote.yml once: 487cb1a on 2026-10-20 by a Render env change (work/STATE.md L119).
- CI run 40242394581 on 8305160 (push): backend 481 passed / 4 skipped / 7 deselected in 312.96 s; frontend 117 tests in 12 files; integration 7 passed; e2e 12 passed. Jobs ran 22:55-23:03Z. Current main CI run 40251535674 (542e58c): backend 507 passed in 199.80 s, frontend 117, integration 7, e2e 12. PR 149 checks: backend pass 6m34s, frontend 30s, integration 2m25s.
- `python3 incident-response/test_responder.py`: 'Ran 20 tests in 0.524s OK' (stdlib only, spawns no agent).
- main: 267 first-parent commits, 50 through PRs. Since the first PR (a719004, #30): 179 commits, 130 direct pushes (59 'work:' notes). main is unprotected (protection API 404, no rulesets). The repo is public. No git tags, no GitHub releases.
- Migrations on main that prod lacks: e4f5a6b7c8d9_add_pages_to_runs, f5a6b7c8d9e0_cleanup_events_without_start_time (downgrade: pass, irreversible), a6b7c8d9e0f1_drop_event_user_link_date_unique. Dockerfile CMD runs `alembic upgrade head` on start. work/STATE.md L8 prod promote checklist: back up the DB first (deletes 3,279 events, 603 of them in calendars), then set EXA_API_KEY, SEARCH_PROVIDER=exa and MAX_RESULTS_PER_QUERY=10 on prod. Prod code 969a161 has no Exa adapter (factory: tavily and brave only).
- Hourly-search: 50 scheduled runs from 2026-10-17 to 2026-10-26, gaps 2.1-7.8 h, median 4.5 h, all 'success'. /api/search/all returns 202 and runs searches as background tasks, so the workflow cannot see failed runs. Real outage: 2026-10-25 ~09:xx UTC, DeepSeek 402, every search on dev and prod failed (commit ed50266, work/HANDOVER-2026-10-25.md). No alert exists in prod.
- Telemetry is off unless OTEL_EXPORTER_OTLP_ENDPOINT is set (telemetry.py L1, L14); only docker-compose.observability.yml sets it. Metrics: 9 instruments in pipeline.py plus sail_guard_runs_total in factory.py = 10. Span names: search_run, criteria, window, search, query, extract, page, detail_hop, filter, judge, event, triage, dedup, persist. ASGI instrumentation 0.66b1 also records client IP/port and User-Agent on HTTP spans.
- rules.yaml: L9 SearchRunFailures (increase error[10m] > 1, for 5m, noDataState NoData); L66 SearchRunsSilent (increase[2h] < 1, for 10m, noDataState OK); both severity critical, so both route to responder-webhook (group_wait 30s, repeat 1h). Grafana: anonymous Admin, login form disabled, port 3001→3000. RESPONDER_WEBHOOK_SECRET defaults to empty in observability compose. The app has no in-process scheduler.
- Incident 2026-10-21: fault 3d9f6b8 at 07:32:59Z; alert startsAt 07:41:20Z; evidence collected 07:41:50Z (28.04 error runs in 10 min, health ok, Loki empty); fix 8d2f839 at 07:46:12Z, so 4 min 52 s is correct. Both incident branches exist on GitHub (pushed by a human). fix.diff files were added by hand (571b751, 75e00a1); no code writes them. A failed 2026-10-20 attempt (verdict 'error') was deleted in ad56f19. Incident 2026-10-17: 7318f2f at 05:13:20Z, alert 05:20:20Z, fix dae24e9 at 05:23:32Z.
- Responder: claude -p --model sonnet --max-budget-usd 1, timeout 300 s. Tools: Read, Edit (unscoped), Bash(make test), grep/find/ls/head/tail, git log/diff/status/add/commit/checkout -b. It binds to all interfaces on :8001. The env allowlist passes ANTHROPIC_API_KEY and ANTHROPIC_BASE_URL and always sets SKIP_HOOK_TESTS=1.
- AI usage report: all cited commits exist (8940b2a, db3499a, dd304bb, 7dec86d, bf8e952, 678cd4c) and PR 32 merged 2026-10-17. Issue 24's edit history confirms the image-tag correction (0.119.0/v2.55.1/3.6.18/2.10.8/11.6.16 → 0.161.0/v3.15.0/3.7.8/3.1.0/13.2.3). Issues #17 and #21 (AWS) have no groom and no QA. The tracker has 96 issues (max #145); 56 PRs exist.
- Every relative link and #anchor in the 7 docs resolves, and so does every inbound anchor from other .md files. The only rendering defect is incident-response/README.md L141 (pipes inside a code span break the table).
- Not checked here: Render dashboard settings (the Render connector needs you to pick a workspace), dev's FAKE_NOW value, the DatasourceNoData behaviour (needs a running stack).

<!-- ops-docs summary: I read all 7 docs line by line and checked their claims against git, gh, the code, CI logs and live HTTP GETs. Relative links and #anchors all resolve, both outgoing and incoming. The doc rewrite never touched the factual layer underneath, and that layer is stale or wrong in ways no reviewer will catch from outside.

Worst problems:
(1) The rollback in release-process.md is unsafe and has never run. All 15 promote runs moved forward. Main now has 3 Alembic migrations that prod lacks, one of them an irreversible delete. Old code booting on a newer database fails at `alembic upgrade head`.
(2) " -->
