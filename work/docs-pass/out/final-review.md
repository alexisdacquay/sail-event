# Final review: README.md, docs/reviewer-guide.md, _docs/process.md, AGENTS.md

Reviewed 2026-10-26 at docs-quality HEAD 89b9e97. The docs are unchanged since edeeb55. Read-only; GETs only on the live sites.

Summary: 5 medium, 17 low, 0 high. Rubric mapping: all 50 checklist rows are verbatim rubric substrings (checked by script). Each row has a place to look and a proof. The README table reaches every guide section. 24 fact checks were run (list at the end): 22 hold, 2 are stale or wrong (items 1 and 7).

1. **docs/reviewer-guide.md:637, :123, :640; _docs/process.md:175-176, :218**
   - Quote: "**30/56** PRs with QA headings" (guide:637); "30/56 PRs have a QA heading" (process:176); "**14 of 42 merged PRs** from #66 onward lacked a PR QA heading" (guide:123); "14 of the 42 merged PRs from #66 onward" (process:218).
   - Problem: stale today, and wrong when reviewers read it. Both docs' own commands now print `PR QA / total: 30 57` and `PRs 57 with QA 30`, because the docs PR #153 is open. Once #153 merges, "merged since #66" becomes 43, and the no-QA list gains #153 unless it gets a verdict. The guide says "The filters below reproduce" these numbers, and they no longer do.
   - Fix: bound both scripts to `x['number'] <= 152`, and say "PRs #1–#152" in the prose. Alternatively, recount after the merge.
   - Severity: medium

2. **Defensive "X, not Y" hedging, across the guide and process.md**
   - Quotes:
     - guide:372 "“Full system” here describes the application and database, not an unattended production operations deployment."
     - guide:537 "This behavior follows from the expression/configuration; a live false-alarm test is not recorded."
     - guide:310 "sequentially under normal make execution"
     - guide:347 "External trigger/ops components are disclosed below."
     - guide:680 "rather than interpreting the counts as PASS coverage"
     - guide:706 "Current health/version alignment and that historical record are separate checks"
     - guide:744 "Loki transport of that access-log line remains unverified."
     - guide:725 heading "What this run does not prove"
     - process:116 "issue-body boxes need not be the review record."
     - process:123-124 "It applies to bug fixes, not every feature since the project began."
     - process:132-133 "the written causal analysis and commit sequence remain review obligations, not a mechanical enforcement gate."
     - process:152 "Labels do not prove grooming or completion."
     - process:211 "Its old implementation details are historical, not today's pipeline contract."
     - process:216 "A body with acceptance criteria does not establish PM involvement."
     - README:57 "No duplicate accepted/queued events in this scenario; rejected repeat rows may remain"
   - Problem: this is the legalistic pattern STANDARD "Honest, not defensive" says to remove ("These counts measure headings, not complete adherence" and similar). None of these stops a reviewer from misreading a rubric clause. Together they make the guide's appendix read as an audit report, not a guide. The four "… audit" headings add to that.
   - Fix:
     - Delete the sentences quoted above.
     - README:57: write "No event shows twice in In calendar or Review".
     - Rename "What this run does not prove" to "Drill limits".
     - Keep the caveats that do protect a rubric clause: §10 "Partial"/"Not met", and §6 "a green result does not mean those bugs are fixed".
   - Severity: medium

3. **README.md:182; docs/reviewer-guide.md:291**
   - Quote: "discovery and model judgments are imperfect" (README:182); "Search quality after the event-page changes is unmeasured in [the recall log](../work/RECALL.md)" (guide:291).
   - Problem: the known gaps are incomplete and softened.
     - work/RECALL.md has one full recall run (2026-10-24, ab21641, local): "recall@run: 3/38 (7.9%)", "accepted-recall: 0/38". The number appears only in _docs/search-spec.md:34-35.
     - The README calls it "imperfect". The guide says only that the later code is unmeasured, which hides the measured result.
     - Neither doc points to the 11 open issues (#72, #75, #78, #94, #95, #96, #99, #100, #101, #102, #131), which a reviewer will see in the tracker.
   - Fix:
     - Add one sentence to guide §5 Known gaps and to the README Product bullet: "The one full recall run (local, 2026-10-24, before the event-page hop) found 3 of 38 ground-truth events and accepted none; the ground truth is unvetted."
     - Add "Open defects: [open issues](https://github.com/alexisdacquay/sail-event/issues?q=is%3Aissue+is%3Aopen)".
   - Severity: medium

4. **docs/reviewer-guide.md:106-107, :122**
   - Quote: "The example has Goal, Acceptance criteria, Out of scope and Constraints. Coverage counts and exceptions are below." (guide:106); "On 2026-10-26, **38 of 96 issue bodies** lacked at least one template heading; **27** were closed. **91** contained “acceptance criteria”." (guide:122)
   - Problem: a strength is buried. The rubric phrase is "The tasks define acceptance criteria" (plural). The checklist offers one example. The coverage figure (91/96 with acceptance criteria, 58 with all four sections) appears only inside a Known gaps bullet that leads with the negative. QA's 69 verdicts, 23 of them FAILs sent back for a fix, also appear only in the Tracker audit appendix. That is the best evidence that the agents used the tracker.
   - Fix:
     - In row guide:106 write: "91 of 96 issues contain acceptance criteria; 58 use all four template sections (2026-10-26; command in [Tracker audit](#tracker-audit))."
     - In row guide:107 add: "69 issues carry a QA verdict; 23 of them a FAIL that went back to the engineer."
     - Keep the 38/27 line in Known gaps.
   - Severity: medium

5. **README.md:76, :80, :83, :181**
   - Quote: "| Owner | Picks work; approves merge and a named production commit separately | — |" (:80); "Implements in a separate checkout" (:83); "QA through the [qa-engineer definition]" (:76); "**Process:** incomplete grooming/QA records, orchestrator overreach, direct pushes and red merges" (:181)
   - Problem: the README presents the operating model without dates. Per process.md:50-52, :138-143 and :221:
     - worktrees and PR review began on 2026-10-20 (#65);
     - the owner's pick and prod approval began on 2026-10-21;
     - 14 of the 15 promote runs predate that gate;
     - QA ran as general-purpose until 2026-10-20.
     The README dates the regression rule (:114) but not these. STANDARD: "A rule introduced on a date is dated." A reviewer who opens the promote history sees 8 dispatches on 2026-10-20 and reads them as owner-approved.
   - Fix: add to the :181 Process bullet: "operating model as shown since 2026-10-20/21: worktrees and PR review from #65 (2026-10-20), owner pick and prod approval from 2026-10-21".
   - Severity: medium

6. **docs/reviewer-guide.md:163**
   - Quote: "Verify with `git log -S 'committed while red' --format='%h %cs %s' -- _docs/team/software-engineer.md` and `git log -S 'Root-cause gate' --format='%h %cs %s' -- _docs/process.md`."
   - Problem: both commands now print two lines. The first is "88d44ab 2026-10-26 wip: docs pass step 2 in progress (codex writers mid-run)". After the merge, the squash commit of #153 will print first. The reviewer has to work out that the oldest line is the one that counts.
   - Fix: append `| tail -1` to both commands, or say "the oldest line shows c0f83e6 (2026-10-25) and ac54483 (2026-10-26)".
   - Severity: low

7. **_docs/process.md:30-31**
   - Quote: "Recorded launches select `model: opus`."
   - Problem: the local transcript does not support "all".
     - 12 engineer launches passed `model: fable`.
     - 56 of the 65 `qa-engineer` launches passed no model, so they inherited the session model.
     - The previous draft mentioned the other model; the rewrite dropped it and made the claim absolute.
   - Fix: "Most recorded launches select `model: opus`; `qa-engineer` launches usually inherit the session model, and some engineer launches used another model."
   - Severity: low

8. **README.md:50**
   - Quote: "the [guide's schedule evidence](docs/reviewer-guide.md#1-problem-description) explains the delays."
   - Problem:
     - The guide measures the gaps (2.1–7.8 h, reproduced today) but gives no cause.
     - It also omits a cause that is known: each run queues at most `MAX_SCHEDULED_USERS` = 50 users. Run 40325804781 (2026-10-26 12:51Z) logged "usersQueued: 50" and "usersSkipped: 23". This is stated only as configuration in docs/deployment.md:53.
   - Fix: change "explains the delays" to "measures the gaps". Add to guide §1 Known gaps: "Each run queues at most 50 users; the 2026-10-26 12:51Z run skipped 23."
   - Severity: low

9. **README.md:182**
   - Quote: "past rows remain listed … ([Guide §1](docs/reviewer-guide.md#1-problem-description), [§5](docs/reviewer-guide.md#5-application))"
   - Problem: neither linked section mentions past rows. The only source is the title of open issue #94.
   - Fix: link [#94](https://github.com/alexisdacquay/sail-event/issues/94), or add a §5 bullet.
   - Severity: low

10. **docs/reviewer-guide.md:82**
    - Quote: "Local demo data, with the application clock fixed at 18 October 2026 so the 19–21 October fixtures remain usable."
    - Problem: the screenshot directly above shows "26 Oct 01:06 · your run", and the rail calendar marks 26 October as today. The server clock is fixed; the browser calendar is not. A reviewer sees a contradiction.
    - Fix: "The server clock is fixed at 18 October 2026 …; the run time and mini-calendar show the real capture date (26 October)."
    - Severity: low

11. **_docs/process.md:21, :87, :122-124, :221; docs/reviewer-guide.md:163, :200, :325, :461**
    - Quote: "follows the dated root-cause gate below" (process:21); "For bug fixes since 2026-10-25, the engineer also follows the root-cause gate." (process:87); "Bug fixes require a red regression test under the rule introduced on 2026-10-25 (see §3)." (guide:325); "Rollback was never exercised, the three new migrations make rollback untested" (guide:461)
    - Problem: the same limitation is repeated within one document. The root-cause gate's date appears four times in process.md and three times in the guide. Guide:461 says "never exercised" and "untested" in one sentence. STANDARD: state each limitation once.
    - Fix:
      - Date the gate once per document: the process.md "Root-cause gate" section, and guide §3 Beyond.
      - Delete process:87, the word "dated" at process:21, and the last sentence of guide:325.
      - Guide:461: "Rollback is untested; PR #150's migration deletes data irreversibly."
    - Severity: low

12. **docs/reviewer-guide.md:461**
    - Quote: "the three new migrations"
    - Problem: "new" relative to what? After the owner promotes, a reviewer cannot tell which migrations are meant. The README names the PRs; the guide does not.
    - Fix: "the three migrations added in PRs #128 and #150 (`e4f5a6b7c8d9`, `f5a6b7c8d9e0`, `a6b7c8d9e0f1`)".
    - Severity: low

13. **docs/reviewer-guide.md:329**
    - Quote: "No captured combined `make test-all` result is offered here."
    - Problem: the rubric phrase is "run with a single command, and pass". CI runs `uv run pytest`, `npm test`, `make test-integration` and `make test-e2e` as separate steps (guide:315). Nothing shows the single command passing. The score risk is small, because the lower level ("Only unit tests or only integration tests") does not fit. But the "pass" row is not proven as written.
    - Fix: run `make test-all` once at the final docs commit. Record its summary lines, commit and date in docs/testing.md, and link them from the §6 "pass" row. Delete the quoted sentence.
    - Severity: low

14. **docs/reviewer-guide.md:289**
    - Quote: "`mock.ts` is also selected by a bare frontend dev run when `VITE_API_URL` is absent; it is not limited to tests (…). Use the documented startup commands."
    - Problem: developer trivia. A reviewer who uses the documented commands never sees it: `make run` sets `VITE_API_URL`, and the Dockerfile sets it to "".
    - Fix: delete the bullet, and "frontend mock selection" in the index at guide:624.
    - Severity: low

15. **README.md:36**
    - Quote: "Calendar aggregation collects known listings."
    - Problem: unclear. Who collects? Known to whom?
    - Fix: "Calendar aggregators only collect listings from sources they already know."
    - Severity: low

16. **README.md:127**
    - Quote: "PM adds the [task template](_docs/task-template.md);"
    - Problem: this reads as "the PM writes the template". It means "the PM also reads the template".
    - Fix: "PM also reads the task template;"
    - Severity: low

17. **README.md:64, :74, :129**
    - Quote: "## Try it" (:64); "## How it was built: an agent team" (:74); "## How it is built" (:129)
    - Problem: headers do not match content, or nearly duplicate each other.
      - "Try it" is local setup plus test commands, next to "Try it live".
      - "How it was built" and "How it is built" differ by one word.
    - Fix: rename them "Run it locally" and "Architecture".
    - Severity: low

18. **README.md:143**
    - Quote: "C --> A[Owner: push to prod]"
    - Problem: "push" reads as `git push`. It is the owner's chat wording.
    - Fix: "C --> A[Owner approves that SHA]".
    - Severity: low

19. **docs/reviewer-guide.md:5, :155, :202, :421, :552**
    - Quotes:
      - :5 "Proof checks mean inspecting a linked file, record or screenshot; building and running the system takes longer."
      - :155 "“Fresh” means a separate verification task"
      - :202 "QA re-checks can reuse an agent; #7 did so (…). Dependent parallel changes also need review at their final commit, as [#142](…) depended on #141."
      - :421 "The [deployment record](…) records an automatic dev deployment on 2026-10-17."
      - :552 "A quiet outcome/trigger series can satisfy it while other searches succeed"
    - Problem: English and sense.
      - :5 is awkward.
      - :155 quotes "Fresh" with no source.
      - :202 never states the gap. #142 closed through PR #143 with no QA verdict at its final commit.
      - :421 says "record records".
      - :552 uses "satisfy" where it means "fire".
    - Fix:
      - :5 "Each proof is a file, record or screenshot you can open in under a minute."
      - :155 "The QA definition says “Start fresh”: …"
      - :202 "A re-check by the same QA agent keeps its earlier context (#7). PR #143 (#142) was rebased onto #141 and merged with no QA check at its final commit."
      - :421 "The 2026-10-17 deployment log shows dev auto-deploying 10d4701."
      - :552 "It can fire for one quiet series, for example `trigger=scheduled`, while other searches succeed."
    - Severity: low

20. **docs/reviewer-guide.md:619-631**
    - Quote: "| [12](#12-on-call-agent) | Checkout revision, easy drill, incomplete evidence/tests/recovery, broad tools, host runtime and shared identity |"; rows "| [5](#5-application), [7](#7-containerization) |" and "| [7](#7-containerization) |", and "| [8](#8-deployment), [11](#11-alerting-on-user-impact) |" and "| [11](#11-alerting-on-user-impact) |"
    - Problem: the gap index is telegraphic insider shorthand. Criteria 7 and 11 each appear in two rows, so the index is hard to scan. The row for 4 includes "instruction-based QA separation", which is a §3 gap.
    - Fix: one row per criterion, each gap in plain words of five words or fewer. Move the QA separation gap to row 3.
    - Severity: low

21. **_docs/process.md:113, :115, :136**
    - Quote: "The exception is a deliberately red regression-test commit under the gate below." (:113); "In the shared checkout a clean-tree check covered the engineer's work too; in a separate QA worktree it covers only the reviewed checkout." (:115); "## Phase 2 (from issue #65): worktrees and PRs" (:136)
    - Problem:
      - :113 does not say what it is an exception to.
      - :115 is opaque to an outsider.
      - The :136 header covers Phase 1 as well.
    - Fix:
      - :113 "Exception: a deliberately red regression-test commit (root-cause gate step 2) is committed with `SKIP_HOOK_TESTS=1`."
      - :115 "In Phase 1, QA shared the engineer's checkout, so its `git status` check also caught uncommitted engineer work. In a QA worktree, it only shows that QA changed nothing."
      - Rename :136 to "Phase 1 and Phase 2".
    - Severity: low

22. **docs/reviewer-guide.md:718, :744, :751-753; _docs/process.md:118**
    - Quote: "git show --stat 8ceef57 6b2fcc4 571b751" (:718); "The 2026-10-26 invalid-path probe returned HTTP 404" (:744); "/api/calendar/docs-quality-invalid-probe" (:751); "Current freeze (owner, 2026-10-26): documentation only; no new product work." (process:118)
    - Problem: internal context leaks to reviewers.
      - :718 gives three shas with no word on what they show. They are 2026-10-21 direct pushes that changed code, tests and incident records.
      - :744 cites a probe nobody describes. It was run by the docs pass.
      - The probe string carries the branch name.
      - process:118 is agent state that goes stale at submission.
    - Fix:
      - :718 add the comment "# examples of direct pushes that changed code or tests".
      - :744 "A local probe on 2026-10-26, using the commands below, returned …".
      - Rename the probe to `invalid-probe-token`.
      - Delete process:118. AGENTS.md:4 already carries the freeze for agents.
    - Severity: low

Fact checks run (24). They match except where an item above says otherwise:
- `curl /api/health`: prod 969a161…, dev 542e58c… = `git ls-remote` main. `/api/config` `registrationCodeRequired:false` on both.
- `work/rubric-2026-10-16.md`: `cmp`-identical to the live course README.
- CI run 40251535674: push on 542e58c, 3 jobs green. Backend 507 passed / 4 skipped / 7 deselected; 117 Vitest; 7 integration (`test_data_survives_restart PASSED`); 12 Playwright.
- `python3 -I incident-response/test_responder.py`: 20 tests OK.
- Guide tracker script: 96/85; 58 four headings; 91 AC phrase; 38/27 ungroomed; [17, 21, 46, 102, 145] without AC; 69/23 QA; 45 closing notes; 42 merged since #66 with the same 14 numbers; 21 without MVP label. Exception: PRs now 57 (item 1). process.md commands agree.
- GraphQL closer: 8 issues closed by PR (#46, #52, #68, #76, #83, #120, #122, #142).
- Spec before code: fa345ba 2026-10-15, 98f3cf7 2026-10-16 11:50, 6ccfdec 12:08.
- c0f83e6 2026-10-25, ac54483 2026-10-26, a41b405 2026-10-17.
- Drills:
  - 3d9f6b8 07:32:59Z; alert startsAt 07:41:20Z; 8d2f839 07:46:12Z (4 min 52 s).
  - 7318f2f / dae24e9 on 2026-10-17 UTC.
  - fix.diff is +1/−4; verdict.json is "fix".
- Promote: 15 runs, all `workflow_dispatch` and success. Last run 2026-10-23 at 969a161. 13 runs before 2026-10-21 and 2 on 2026-10-21 before the 11:40 owner pause, so "14 of 15 predate" holds.
- Hourly: cron `7 * * * *`. Last 50 scheduled runs: gaps 2.1–7.8 h. `SAIL_BASE_URL` = prod only.
- PR #31 and PR #138: integration FAILURE at merge. main protection 404. Rulesets and deployments empty. 34 of the last 60 first-parent subjects at 542e58c lack a PR marker.
- Migrations after 969a161: e4f5a6b7c8d9 (#128), f5a6b7c8d9e0 and a6b7c8d9e0f1 (#150). f5a6's downgrade is `pass`.
- PR #144 body: 86.0 s minimum and 493 s maximum, Tavily + DeepSeek, "on this Mac".
- Issue #11: created 18:54Z, groomed 22:09Z, closed 22:25Z 2026-10-16, edited 2026-10-20.
- Issue #7: FAIL → `## QA fix: db3499a` → PASS → orchestrator close.
- PRs #30–#32 created 2026-10-17. PR #66 is the first with a QA heading. Issue #65 is dated 2026-10-20.
- #39, #52 and #55 record the orchestrator fixing a QA FAIL.
- `docker compose config --services` prints postgres, app. Compose FAKE_NOW defaults to 2026-10-18T12:00+02:00. `.nvmrc` 24. Dockerfile L7 `VITE_API_URL=""`, L25 `alembic upgrade head`.
- Makefile `test` includes `test_responder.py`. `test-all: test test-integration test-e2e`. ci.yml has no responder step. The integration job `needs: [backend, frontend]`.
- Pinned anchors at 542e58c land on the named code: test_pipeline L306, test_events L111/L150, test_integration L37/L103/L135/L254, test_calendar L112/L255, journeys L60-67, auth L100-101, pipeline L737-750/L547-556/L39-77, dedup L67-104, responder L27-33/L151-166/L188-195, main L26-37/L117-126, api.ts L67-71, search.py L289-314, Makefile L25-32.
- rules.yaml:
  - interval 60s;
  - SearchRunFailures > 1 for 5m;
  - SearchRunsSilent `increase(sail_runs_total[2h]) < 1` for 10m, `noDataState: OK`;
  - runbook link added in ac54483, while the stored alert says "TODO".
- Grafana anonymous Admin. The `search_run` span carries `user_id`. The Loki screenshot trace ID 9da6b9bd797b3bdc96b17585867e9f6f matches the guide.
- Adapter defaults: fixture / fake / none (AGENTS.md:65-66).
- `work/docs-pass/linkcheck.py` on the four files: all links and anchors resolve.

FAIL

## Re-check (b410455)

Checked on 2026-10-26, read-only. HEAD is b480c44, which changes only work/STATE.md after b410455. The four docs are as at b410455; AGENTS.md is unchanged since 89b9e97. Line numbers below are current.

Commands re-run at this commit:
- `work/docs-pass/linkcheck.py` on the four files: all links and anchors resolve. This covers the kept `<a id>` anchors (`#try-it`, `#phase-2-from-issue-65-worktrees-and-prs`, `#tracker-audit` and the others) and the RECALL.md heading anchor, which is unique.
- Guide tracker script (the ≤ #152 version) and the process.md scripts: 96/85, 58, 91, 38/27, 69/23, 45, 30/56, 42 with the same 14 numbers, 21 without an MVP label. These match the prose again.
- Schedule command with `--created '<=2026-10-26T12:51:46Z'`: "50 runs; gap hours 2.1 to 7.8". The run 40325804781 grep prints "usersQueued: 50" and "usersSkipped: 23".
- Promote list with `--created`: 15 runs.
- `git show c0f83e6 -- …` shows "+ … committed while red"; `git show ac54483 -- _docs/process.md` shows "+## Root-cause gate".
- The guide's make test-all summary matches scratchpad/test-all.log (the orchestrator's run on 3e33fc9): 507/4/7, 117, 20 OK, 7, 12, exit=0.

### Status of the 22 items

1. Fixed.
   - guide:107-108, :123-125, :661, :664 and process:178-181, :221 now say "#1–#152".
   - Both scripts filter `number <= 152` (guide:680-682, process:186, :196, :207) and reproduce every number.
2. Fixed.
   - All 15 quoted hedges are gone: guide:311, :368, :393, :558, :706, :740, :785; process:115, :120-135, :155, :215, :219; README:57.
   - "What this run does not prove" is now "Drill limits" (guide:764).
   - The four "… audit" headings are now "… evidence" (guide:659, :734, :758, :780).
3. Fixed.
   - README:195 gives the 3/38, 0/38 recall run with date, commit and RECALL.md link, plus an open-issues link.
   - guide:291 and :294 do the same.
4. Fixed. guide:107 gives "91 of 96 contain acceptance criteria; 58 use all four template sections". guide:108 gives "69 carry a QA verdict; 23 include a FAIL requesting a fix". The 38/27 line stays in Known gaps (guide:123).
5. Fixed. README:80-89 adds a "Since / What started" table, and README:194 dates worktrees/PR review, the QA agent and the owner gates. This fix introduced N1 and N2 below.
6. Fixed. guide:164 and process:122-127 replace the `git log -S` commands with `git show` of c0f83e6 and ac54483, which print only the adding commits.
7. Fixed. process:30-32 says "Most recorded launches select `model: opus`; `qa-engineer` launches usually inherit the session model, and some engineer launches used another model."
8. Fixed. README:50 now says "measures the gaps". The scheduled-user cap is now a gap at guide:87, with the reproduce command at guide:726-730.
9. Fixed. README:195 links "past rows remain listed (#94)", and guide:294 adds the matching bullet.
10. Fixed. guide:82 says "the run time and mini-calendar show the real capture date, 26 October".
11. Fixed in the guide and process.md.
    - process:21 no longer says "dated", and the old process:87 sentence is gone.
    - The guide:346 regression sentence is gone.
    - guide:201 is a single dated line.
    - guide:482 says "Rollback is untested; PR #150's migration deletes data irreversibly".
    - The README now repeats the dates itself; see N2.
12. Fixed. guide:738 says "The three migrations added in PR #128 and PR #150 are `e4f5a6b7c8d9`, `f5a6b7c8d9e0` and `a6b7c8d9e0f1`". guide:482 no longer says "new".
13. Fixed. guide:312 and :324-340 record a `make test-all` exit 0 with per-suite counts, and the old guide:329 sentence is gone. The command shown introduced N3.
14. Fixed. The mock.ts bullet is gone from §5 Known gaps (guide:289-294) and from the index row for criterion 5 (guide:646).
15. Fixed. README:36 says "Calendar aggregators only collect listings from sources they already know."
16. Fixed. README:140 says "PM also reads the task template".
17. Fixed. README:66 is "Run it locally", and `<a id="try-it">` is kept at README:64. README:142 is "Architecture".
18. Fixed. README:156 says "Owner approves that SHA".
19. Fixed. guide:5, :156 ("The QA definition says “Start fresh”"), :203, :442 ("2026-10-17 deployment log shows dev auto-deploying `10d4701`") and :573 ("It can fire for one quiet series").
20. Fixed. guide:640-653 has one row per criterion, and the QA write gap has moved to row 3. Small wording points remain; see N4.
21. Partly fixed.
    - process:114 (clean-tree check) is fixed, and process:139 is now "## Phase 1 and Phase 2" with its old anchor kept.
    - process:112 is still unclear: "Exception: a deliberately red regression-test commit (root-cause gate step 2) is committed with `SKIP_HOOK_TESTS=1`." The sentence before it already allows `SKIP_HOOK_TESTS=1`, so the reader still cannot tell what the exception is (the commit is made while `make test` fails).
    - Fix: "Exception: the deliberately red regression-test commit (root-cause gate step 2) is made while `make test` fails, with `SKIP_HOOK_TESTS=1`."
    - Severity: low
22. Fixed.
    - guide:752 explains the three shas.
    - guide:785 says "A local probe on 2026-10-26, using the commands below".
    - The probe is renamed `invalid-probe-token` (guide:792-794).
    - The process:118 freeze line is gone. AGENTS.md:4 keeps it for agents.

### New issues from the fixes (README re-read end to end, plus changed guide lines)

N1. **README.md:86**
   - Quote: "| 2026-10-21 | The owner picks every item and approves every prod promote; 14 of the 15 promote runs came earlier |"
   - Problem: this goes stale on the next deploy. STANDARD says the owner promotes prod to the final docs commit before submission. At that point the run history shows 16 promote runs, so "of the 15" is wrong when reviewers read it. The guide (guide:738, "through 2026-10-26 12:51:46 UTC") and process.md (process:224, "Fourteen of the 15 promotes before 2026-10-26") bound the count; the README does not.
   - Fix: "14 of the 15 promote runs before 26 October came earlier".
   - Severity: medium

N2. **README.md:84-87, :127, :194**
   - Quote: "| 2026-10-25 | The bug-fix root-cause gate |" (:87) and "Since 25 October 2026, bug fixes require a causal explanation, …" (:127); "Worktrees and PR review began with [#65](…) on 20 October 2026; QA began using its agent definition that day. Owner pick and prod approval began on 21 October 2026." (:194)
   - Problem: the item-5 fix states each rule's start date twice in the README, once in the new table and again in Known gaps. The root-cause date also appears in both the table and :127. STANDARD: state each limitation once.
   - Fix:
     - Keep the table.
     - Cut :194 to "…; see [Guide §2] … and [§9]. Rule start dates: [timeline](#how-it-was-built-an-agent-team)."
     - Drop "Since 25 October 2026," from :127, or drop the 2026-10-25 table row.
   - Severity: low

N3. **docs/reviewer-guide.md:328-332**
   - Quote: "PYTHONDONTWRITEBYTECODE=1 TEST_COMPOSE_PROJECT=sail-docs-guide-round2 TEST_HOST_PORT=8046 make test-all"; "At `ca4cf2b` on 2026-10-26"
   - Problem:
     - The command leaks the internal docs-pass run name ("sail-docs-guide-round2"). A reviewer runs plain `make test-all`.
     - ca4cf2b is a work-only commit on the docs branch. A squash merge, which this repo uses, leaves it off main.
     - The orchestrator's equivalent run on 3e33fc9 (scratchpad/test-all.log) is not the one cited.
   - Fix: show `make test-all`, and write "At `ca4cf2b` (application code identical to `542e58c`) on 2026-10-26".
   - Severity: low

N4. **docs/reviewer-guide.md:644**
   - Quote: "rules introduced after implementation; … final commits lack QA"
   - Problem: "final commits lack QA" reads as all final commits; the record is one PR (#143, guide:203). "Introduced after implementation" is vague.
   - Fix: "rules introduced mid-project (2026-10-20 to 2026-10-25); one PR merged without QA at its final commit (#143)".
   - Severity: low

README length after the fixes: 1,810 words including tables, diagrams and link definitions. It still reads in about 5 to 6 minutes. I found no new high issue.

Summary: 21 fixed, 1 partly fixed (low), 4 new (1 medium, 3 low). Remaining medium: N1.

FAIL
