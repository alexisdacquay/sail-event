| Criterion | Score | One-line reason |
|---|---:|---|
| Problem Description | 2/2 | README explains the problem, pipeline and expected behavior; two supporting claims need correction. |
| Product Specification | 2/2 | Written specs, public acceptance criteria and implementation/QA records are directly inspectable. |
| Agent Team Specification | 2/2 | Roles, boundaries, launch context and handoffs are defined, with historical exceptions disclosed. |
| Context Management | 2/2 | AGENTS.md describes the project and links modular product, process, role and operations docs. |
| Application | 2/2 | Browser/HTTP journeys and a passing container-restart test establish connected frontend, backend and database. |
| Testing | 2/2 | Unit and integration suites pass in CI; Makefile supplies one combined command; responder tests also passed in this review. |
| Containerization | 2/2 | Compose starts app and Postgres together; the recorded CI build/start and integration checks passed. |
| Deployment | 2/2 | Both public roots and health endpoints returned HTTP 200; production registration configuration is accessible. |
| CI/CD | 3/3 | CI runs on PRs; the dated deployment record documents automatic dev delivery; successful manual prod runs exist. |
| Observability | 1/2 | Logs/traces correlate, but shared metric trace IDs and the customer-data/credential clauses are unmet. |
| Alerting on User Impact | 1/1 | A provisioned failed-search rule and its recorded firing prove an alert exists. |
| On-Call Agent | 2/2 | The drill records alert-triggered Claude code repair; restored service and reliable incident-test output remain unproved. |

Score: **23/24**. The report verdict below concerns documentation quality and unresolved evidence risks, not a passing course score.

## Scope and checks

Reviewed on 2026-10-26, branch `docs-quality`. Read the owner's `work/docs-pass/STANDARD.md` first, then entered through README.md and followed its reviewer-guide links. Applied the full rubric in `work/docs-pass/facts.md`, section `rubric`; did not use the prior review scores as evidence.

Read-only checks included linked source files, `gh` GETs of issues/PRs/runs, CI logs, public HTTP GETs, `docker compose config --services`, and `python3 -I -B incident-response/test_responder.py` (20 tests, OK). No accounts, login or searches on either hosted site; no deployment, drill, build, application test journey or database restart was initiated. Local application/test startup would create state, so existing CI records supply that runtime evidence.

All relative file links and local heading/explicit anchors in README.md, docs/reviewer-guide.md and AGENTS.md resolved. The 29 distinct pinned source files linked from README and the guide have no differences from the local reviewed versions. All rubric-level quotations in the guide match facts.md exactly; the official course README fetched through `gh api` also matches the saved rubric byte for byte. Checklist wording has two exceptions, issues 8–9 below. The team/context tables explicitly identify their additional lower-level phrases; those are not silently presented as full-marks wording.

## Evidence checked for each criterion

### Problem Description

> The README clearly describes the problem, the system functionality, and expected behavior. (2 points)

Checked README's Problem, What it does, threshold table and Expected behaviour. Opened the linked pipeline, triage, rejection, isolation, feed-removal, token-rotation and rate-limit tests; checked the browser assertions for saved thresholds, decisions and user isolation. The pipeline implements inclusive cutoffs. The boundary-test link and unconditional duplicate statement fail stronger readings of their proof: issues 4–5. These defects do not make the overall functionality unclear, so I retain 2 rather than the rubric's “The problem is described briefly, but it is unclear what the system does or what functionality is expected. (1 point)”.

### Product Specification

> A specification exists and there's a publicly accessible task tracker. The tasks define acceptance criteria and there's evidence that the agents used the tracker. (2 points)

Opened the PRD, search spec, task template and schema-contract test. `gh issue view 11 --json body,url,state` showed the four sections and 15 checkable criteria; its implementation/QA comments record their use. Issue #7 contains implementation → QA FAIL → fix `db3499a` → QA PASS → closing note. PR #149 preserves a checked head and per-criterion QA PASS. Repository API reports public visibility. Reproduced 96 issues, 85 closed, 58 groomed, 91 with “acceptance criteria”, 69 issue QA headings, 23 FAIL headings, and 30/56 PR QA headings. These match the guide. Shared identity and incomplete process coverage are disclosed; the rubric does not require perfect historical compliance.

### Agent Team Specification

> The project defines the agent team and process of how they work together. (2 points)

Opened process.md, all three role files and the runnable QA definition. Responsibilities, exclusions, brief contents, worktree ownership, FAIL/re-check and owner handoffs are explicit. Issue #7 and PR #149 demonstrate public handoff artifacts. The dated gates distinguish the present process from the original unattended workflow. This closes the lower-level ambiguity: “Roles or agents are mentioned, but responsibilities are unclear. (1 point)”. Exact private launch prompts remain supported by the documented transcript excerpt rather than independently public transcripts; that limitation is stated.

### Context Management

> AGENTS.md exists and it also points to modular docs (process, teams, etc.). (2 points)

Opened AGENTS.md and CLAUDE.md (`@AGENTS.md`), process/role docs and the top STATE block. The project summary and modular links exist; the context/brief section explains task-specific reads, handoffs and resumption. This exceeds the preceding “An AGENTS.md (or equivalent) exists and describes the project. (1 point)” level.

### Application

> Full-stack application works end to end: frontend talks to backend, data persists in a database. Application runs locally with a single command. (2 points)

Opened Dockerfile, client selection, SPA serving, Compose, browser journey, HTTP journey and restart test. `VITE_API_URL=""` selects HTTP; the image serves React with FastAPI; Postgres has a named volume. The restart test creates nonzero events, restarts only the app, reauthenticates and compares event count. CI run `40251535674`, integration job `121346455358`, explicitly reports `test_data_survives_restart PASSED`, seven integration passes and twelve browser passes. The count-only persistence assertion and fixture providers are disclosed and sufficient for this rubric; no new local end-to-end claim is made.

### Testing

> Both unit and integration tests exist, run with a single command, and pass. (2 points)

Read Makefile's `test-all: test test-integration test-e2e`, the CI workflow, test sources and testing.md. Fetched the named CI run/log: at `542e58c`, backend **507 passed, 4 skipped, 7 deselected**, frontend **117 passed**, integration **7 passed**, Playwright **12 passed**. Ran the additional responder suite: **20 tests OK**. The expected browser failures and responder's absence from CI are disclosed. The same `make test-all` invocation was not rerun; its constituent passing suites and the inspected target support the score. Checklist wording needs issue 8's correction.

### Containerization

> The full system, including the database, runs via Docker or Docker Compose and starts with a single command. (2 points)

`docker compose config --services` returned `postgres` and `app`. Inspected Dockerfile's frontend build and Alembic/Uvicorn startup, Compose's database dependency, volume and demo-seeding setting, and the startup seed hook. The named CI run records a successful `docker compose up --build -d --wait` followed by passing HTTP/browser tests. This proves the application/database interpretation of “full system”; the external scheduler and separate operations/responder scope are explicitly disclosed.

### Deployment

> The application is deployed and reachable at a public URL, or there's a clear demo with the deployment. (2 points)

GETs of both hosted `/` paths returned **200 HTML**; `/api/health` returned **200**, status `ok`. Production reported `969a16144b909f57359f38f8a5f8e05a0ef5b491`; dev reported `542e58cb0fe73065a905febec7637bfa377a77c4`. Both `/api/config` GETs returned `registrationCodeRequired: false`. Following STANDARD.md, the planned production promotion is not reported as a documentation mismatch. These GETs establish reachability, not a paid search's success.

### CI/CD

> CI runs tests, CD deploys to dev, and there's a manual deploy to production. (3 points)

Read CI and promote workflows, deployment.md and work/DEPLOY-render.md. CI triggers on PRs to main and main pushes. Dev health equals `git ls-remote ... refs/heads/main`. The deployment record explicitly records a push of `10d4701` automatically deploying dev and prod auto-deploy being disabled. Promote history contains successful `workflow_dispatch` runs; the workflow selects a full SHA, invokes the deploy hook and checks health/identity. I accept the recorded automatic deployment for 3; current independent verification of the external trigger remains the risk in issue 10. Red merges, direct pushes and untested migration rollback are disclosed and are not additional requirements in this rubric sentence.

### Observability

> A key user journey is instrumented with metrics, traces, and structured logs that share a trace ID; no customer data or credentials are sent to telemetry; and the signals are collected, stored, and viewable in a UI. (2 points)

Opened pipeline instrumentation, telemetry.py, JSON formatter, collector pipelines, storage/provisioning and both linked screenshots. Tempo's search spans and Loki's completion log show the same `9da6b9bd797b3bdc96b17585867e9f6f`. The source/configuration supports collection/storage and the captures prove UI viewing. Could not tick the metric correlation or either privacy condition: issues 1–3. The trace-panel workaround is valid but remains a defect, issue 15.

GETs of the already-running local stack gave Grafana health 200 and Tempo ready 200, but Loki ready 503 and an empty current `sail_runs_total` result. This was an existing stack, not a fresh checkout/startup, and no search was generated; it does not establish a fresh-checkout failure or invalidate the dated screenshots. Current live signal availability was not re-established.

### Alerting on User Impact

> At least one alert exists. (1 point)

Opened rules.yaml, notification policy, contact point and the stored firing alert. `SearchRunFailures` checks an error-run increase >1 over ten minutes, held five minutes, evaluated every 60 seconds. The stored alert is firing from `2026-10-21T07:41:20Z`. Critical routing leads to the Bearer webhook. The per-series silence/no-data limitations and absence of hosted coverage are disclosed. They do not erase the qualifying failed-search alert.

### On-Call Agent

> An agent wakes up on an alert and fixes the issue. (2 points)

Opened responder.py, task, drill script, stored alert/evidence/verdict/agent log/diff and actual fix commit. The responder accepts firing webhooks and starts headless Claude; the script's direct webhook POST is only a resolved liveness ping. Commit `8d2f839` actually removes the injected exception and restores `FixtureProvider.search` (+1/−4). Its timestamp is 07:46:12 UTC, exactly **4 min 52 s** after the recorded alert start. I award 2 for alert-triggered code repair of the injected fault; the rubric does not explicitly demand production deployment. A reviewer requiring recovered user service could award 0: issue 6. The incident's test claim is not reliable proof: issue 7. Neither the drill nor its cleanup was run here.

## Issues

1. **File/location:** docs/reviewer-guide.md:491, §10, credential checklist row; backend/app/telemetry.py; observability/collector.yaml.
   **Exact quote:** “**Not met:** raw HTTP paths can include the feed token, which grants feed access. No redaction processor is configured.”
   **Problem:** Cannot tick the credential part of “no customer data or credentials are sent to telemetry”. The feed route accepts a bearer secret in the path; HTTP auto-instrumentation is enabled without a sanitization hook and collector pipelines have no redaction. This is an acknowledged implementation gap, not a hidden documentation error. No real token was requested or printed to test it.
   **Fix, with source:** Keep this gap visible and do not imply full observability marks. Removing the gap requires separately authorized path/attribute sanitization and a synthetic-token telemetry check after the docs-only freeze; source: facts.md:302, telemetry.py, collector.yaml and STANDARD.md's freeze/honest-label rules.
   **Severity:** high.

2. **File/location:** docs/reviewer-guide.md:490, §10, customer-data checklist row; backend/app/services/pipeline.py:112.
   **Exact quote:** “**Not met:** spans include the user's UUID and HTTP client metadata.”
   **Problem:** Cannot tick “no customer data”. The search span explicitly attaches `user_id`; HTTP instrumentation adds client metadata, and provider exception recording is another uncontrolled channel. The screenshots do not establish a data-free telemetry boundary.
   **Fix, with source:** Retain the one-point limitation. Any later full-marks claim needs an authorized attribute allowlist/sanitization change and privacy proof; source: facts.md:302, pipeline.py's run attributes/exception recording and telemetry.py. Do not remove the disclosure to make the checklist look complete.
   **Severity:** medium.

3. **File/location:** docs/reviewer-guide.md:489, §10, correlation checklist row.
   **Exact quote:** “**Partial:** Loki and Tempo share the displayed ID. Metrics have no trace ID/exemplar correlation; joining by time does not meet this whole phrase.”
   **Problem:** Cannot tick “share a trace ID” across all three required signals. The pictures prove log/trace correlation only; the metrics definitions and recorded proof do not close the metric part. This is the other direct reason for 1/2.
   **Fix, with source:** Preserve the limitation during the freeze. To claim 2 later, add and demonstrate request-linked metric exemplars or another mechanism satisfying the exact clause; source: facts.md:302, pipeline.py metric definitions/updates and the two screenshots. No such code change is authorized by this review.
   **Severity:** medium.

4. **File/location:** docs/reviewer-guide.md:66, §1 “expected behavior”, reference `[boundaries]` at line 737.
   **Exact quote:** “[boundary test][boundaries]” and “Saved thresholds control triage”.
   **Problem:** The linked `test_triage_exact_boundaries` is not boundary-behavior proof: test_events.py:134 inserts `status=expected_status`, then line 147 reads it back and asserts the same value. It never invokes triage, and its loaded user is unused. That proof does not hold. The actual pipeline code does implement the inclusive comparisons.
   **Fix, with source:** Link the existing triage implementation at pipeline.py:743–750 and the pipeline-exercising test_pipeline.py:306 instead; label these as source/pipeline proof rather than claiming the seeded test executes boundary behavior. Source: the inspected test and pipeline. A proper exact-score regression is future code work, outside the freeze.
   **Severity:** medium.

5. **File/location:** README.md:79, Expected behaviour, repeated-search row.
   **Exact quote:** “Only one copy of an event remains in In calendar or Review; repeat rows may exist in Out”.
   **Problem:** This unconditional result is stronger than its fixture-only evidence and contradicts explicit failure behavior. dedup.py:74 says budget-short work keeps both events; lines 100–104 also leave events unchanged on model error/no match. The integration test checks one recorded scenario using title/dateTime/city tuples. The PRD already limits its corresponding claim to that fixture scenario.
   **Fix, with source:** Use the PRD's scoped wording, “leaves no duplicate accepted/queued events in the fixture integration scenario; rejected repeat rows may remain”, and state once that model failure/budget exhaustion can retain duplicates. Source: _docs/plan.md, Expected behaviour; backend/tests/integration/test_integration.py:103; backend/app/services/dedup.py:74–104 and test_dedup.py's error-keeps-both case.
   **Severity:** medium.

6. **File/location:** docs/reviewer-guide.md:578 and 626, §12 “fixes the issue” / Recovery; README.md:40.
   **Exact quote:** “No recovered running service or resolved alert is recorded.”
   **Problem:** Within one minute I can tick a code repair, not restored service. The responder commits in a worktree and never deploys the fix. A stricter reading of “fixes the issue” as restored user service could reduce this criterion from 2 to 0. The guide correctly discloses this; the README's “alert to fix” wording leaves the endpoint of that measurement less clear.
   **Fix, with source:** Change the README timing label to “alert to fix commit”, using the guide's existing wording. Retain the missing-recovery disclosure; only separately authorized future evidence of a post-fix successful search/resolved alert can close it. Source: facts.md:304, responder.py, actual commit `8d2f839`, and guide §12. Do not launch a new drill during this docs-only pass.
   **Severity:** medium.

7. **File/location:** docs/reviewer-guide.md:625, §12 Reliable test evidence; linked 20261021 incident agent.log.
   **Exact quote:** “All 84 frontend + backend tests + 20 incident-responder tests pass.”
   **Problem:** The underlying agent report is not credible test verification: it lacks full output and also admits not checking background pytest completion. The fix diff proves removal of the stub, but the verdict's `tests_run: ["make test"]` does not prove a passing repaired application. This increases the risk of 0 under a stricter on-call assessment. The guide appropriately identifies the weakness.
   **Fix, with source:** Keep the claim explicitly attributed as unverified, as §12 does; never use that total as passing-test proof elsewhere. Closing the evidence gap later needs a captured test command, exit status and output at the named incident commit, not an invented reconstructed total. Source: incident agent.log/verdict.json and STANDARD.md's evidence rule. No rerun with repository writes is authorized here.
   **Severity:** medium.

8. **File/location:** docs/reviewer-guide.md:305, §6 checklist label.
   **Exact quote:** “unit tests exist”.
   **Problem:** Not verbatim: the full-marks sentence is “Both unit and integration tests exist, run with a single command, and pass.” The label splices nonadjacent words. The proof column explains the shared predicate, but that does not make the label an exact quotation. The informal atomic hints in facts.md also use this shorthand; the user's requested full rubric is the verbatim authority.
   **Fix, with source:** Quote “Both unit and integration tests exist” as one checklist row and supply separate unit/integration proof checks within it, or use exact fragments with their shared predicate explicit. Source: facts.md:298 and STANDARD.md's Rubric presentation rule. Preserve the successful test evidence.
   **Severity:** medium.

9. **File/location:** docs/reviewer-guide.md:491, §10 checklist label.
   **Exact quote:** “no credentials”.
   **Problem:** Not verbatim: the full text says “no customer data or credentials are sent to telemetry”. There is no contiguous “no credentials” in that sentence. Again, the atomic hints use shorthand, but the required full rubric does not.
   **Fix, with source:** Use the exact combined clause “no customer data or credentials are sent to telemetry”, with distinct privacy and credential checks, or label the second fragment “credentials” under the full quoted negative clause. Source: facts.md:302 and STANDARD.md's verbatim requirement.
   **Severity:** medium.

10. **File/location:** docs/reviewer-guide.md:426 and 431, §9 automatic dev delivery evidence.
    **Exact quote:** “Equality is indirect evidence; it does not itself prove the Render trigger setting.”
    **Problem:** The suggested current health/main comparison cannot distinguish an automatic deploy from a manual one. I accept the dated automatic-deploy event in work/DEPLOY-render.md for 3/3, but cannot independently tick current automatic operation from this quick check. A reviewer requiring current external proof could withhold CD credit. This is disclosed rather than falsely proved.
    **Fix, with source:** Link a dated, sanitized Render auto-deploy-setting/deploy-history capture directly in this row when the owner can supply one. Keep the existing historical event and version comparison as distinct evidence. Source: guide §9, deployment.md's Check deployed commits, and work/DEPLOY-render.md's completed dev/prod split entry. No login or setting mutation is needed or authorized in this review.
    **Severity:** low.

11. **File/location:** README.md, entire document, especially agent/context detail and Ship it, watch it, fix it.
    **Exact quote:** “## How it was built: an agent team” and “## Ship it, watch it, fix it”.
    **Problem:** The entry document misses the owner's five-minute reading target. It contains 3,295 whitespace-separated source words; even after removing fenced code, reference definitions and link destinations, approximately 2,990 remain. At 250 words/minute that is about twelve minutes, before following evidence. Much of the detailed audit history and operations explanation duplicates the guide.
    **Fix, with source:** Keep the problem, behavior, startup, concise team/context/promotion/ops explanations and reviewer links; move detailed counts, historical exceptions and long operations walkthroughs into the already linked guide/process/runbooks. Source: STANDARD.md, “The README should read in about 5 minutes. Detail belongs in the guide and the linked docs.” Counts are reproducible with `len(Path("README.md").read_text().split())`; the displayed-word estimate is approximate, not a timed reading study.
    **Severity:** medium.

12. **File/location:** README.md:13, 106, 152, 154 and 165.
    **Exact quote:** “Those measurements are not a Render benchmark.”; “the repository alone cannot establish its live value.”; “it is not a claim about all earlier work.”; “These counts measure headings, not complete adherence to the process.”; “It does not establish that every commit was tested.”
    **Problem:** These reproduce the owner's explicit examples of legalistic hedging to remove. The measured range is already identified as local, the process rules are dated, the counts name headings and the hook bypass is stated. The extra defenses slow the reviewer without closing a new rubric clause.
    **Fix, with source:** Delete the redundant defenses; retain the concrete measurement context, dates, headings/count command and bypass fact. Keep genuine scoring limitations where they affect the criterion. Source: STANDARD.md, Honest, not defensive, including its quoted removal examples.
    **Severity:** medium.

13. **File/location:** README.md:25, 202 and 250; docs/reviewer-guide.md:5, 471, 522 and §12 opening; observability/README.md opening.
    **Exact quote:** “**Observability, alerting and the on-call responder run locally. The deployed app exports no telemetry to that stack, so these alerts do not monitor the live sites. The recorded incidents are drills.**”
    **Problem:** Local-only scope and drill status are repeated as bold warnings at the top, again in sections, and again in gap indexes. The fact must remain visible, but the presentation directly violates the owner's instruction against a bold disclaimer at the top and repeated caveats. It also contributes to the README's length.
    **Fix, with source:** State local scope/drill status once, in plain prose in each relevant feature section, and have the overview/gap index link there rather than restating the warning. Source: STANDARD.md, “No bold disclaimers at the top of a page” and “State each limitation once, in one sentence, where it matters”. Preserve the underlying limitation.
    **Severity:** medium.

14. **File/location:** README.md:11 and 60.
    **Exact quote:** “after a run, the button reads **Search again**” and “The funnel calls Review “to review” and Out “rejected”.”
    **Problem:** These are label trivia, not reviewer evidence of functionality. The reviewer can run the documented action without learning the button's later label or an extra mapping of result wording. The inclusive threshold rule in the same paragraph is meaningful and should remain.
    **Fix, with source:** Remove the button-renaming and redundant funnel-wording sentences; retain Search now, the three outcome definitions and inclusive cutoffs. Source: STANDARD.md, Audience and tone / “Do not document UI trivia”.
    **Severity:** low.

15. **File/location:** docs/reviewer-guide.md:517, §10 dashboard limitation; README.md:226.
    **Exact quote:** “the dashboard's traces panel errors”.
    **Problem:** The main advertised dashboard is not a completely working proof surface for traces. The linked Tempo Explore capture supplies an adequate alternative for “viewable in a UI”, so this does not cost an additional point, but a reviewer following only the dashboard hits a failure. The guide discloses it.
    **Fix, with source:** Keep the working Explore → Tempo route directly beside the dashboard link and retain one concise gap. A panel repair is future authorized code/configuration work, not a docs-only fix. Source: docs/images/review-40-grafana-dashboard.png, the verified review-41 Tempo capture and facts.md:302.
    **Severity:** low.

FAIL
