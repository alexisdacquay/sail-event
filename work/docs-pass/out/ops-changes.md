## Files changed

- docs/ai-usage-report.md
- docs/api.md
- docs/deployment.md
- docs/operations-and-security-report.md
- docs/release-process.md
- docs/testing.md
- observability/README.md
- incident-response/README.md

Only those eight assigned documents and this requested handoff were written. Other writers’ concurrent changes were left alone. No images, application code, workflow files or contracts were edited; no commits or pushes were made.

## Changes (one line each: what and why)

Finding references F01–F48 below are the one-based order of entries in findings-ops.json (the JSON has no IDs).

- Deployment: kept the earlier version-check and configuration structure, removed unsupported current Render assertions, and wrote for main’s intended configuration rather than the pre-promotion build (F01, F11–F16).
- Deployment: exposed local-only telemetry immediately, corrected the scheduled job’s background-task blind spot, and supplied measured schedule gaps and the command to retrieve timestamps (F08, F10, F15, F17).
- Release process: replaced “all code through PRs” and “only this workflow” guarantees with the actual unprotected-main/direct-push/dashboard paths; retained the useful CI/promotion explanation (F05, F07).
- Release process: added candidate/CI/migration/backup/configuration checks and marked rollback untested across all three new migrations, with PR #150’s irreversible delete explicit (F04, F06).
- Release process: defined “release” as a deployed commit and removed the invented tag convention; workflow history does not include dashboard deploys (F09–F10).
- Observability: explained the instrumented journey, signal collection/storage/UI, metric names/labels and trace lookup before the alert runbook (F21).
- Observability: disclosed missing metric trace IDs, raw feed-token paths, IP/port/User-Agent, user UUIDs, exception text, host-wide filelog scope and the broken trace panel without narrowing the rubric (F20–F21).
- Observability: labeled all fault firings as drills, corrected the silence rule’s local scope and rate-limit wording, and added explicit fixture restoration before correlation checks (F17–F18, F22–F23).
- Observability: recorded the observed critical DatasourceNoData route with its existing-stack/config-drift limitation; no alert configuration was changed (F19).
- Incident response: documented the prompt, evidence fence, model, budget, timeout, real allowlist, worktree lifecycle, verdicts, credentials and human handoff without claiming sandbox enforcement (F24–F26, F29–F30, F33).
- Incident response: distinguished a fix commit from deployed recovery, explained the empty Loki/version evidence, disclosed the failed 2026-10-20 attempt and attributed saved diffs to manual follow-up (F24, F27, F32).
- Incident response: made the shared-secret startup order and checkout-changing drill/dry-run side effects explicit; repaired the output table and verdict-file failure case (F28–F31).
- AI usage: added the dated #1–#26 scope, used “orchestrator” consistently for the AI session, attributed QA/self-corrections accurately, and separated later tooling/process exceptions from the initial report (F34–F38).
- API: added getRun, fixed countsVersion and setAside, corrected reject bands and pages nullability, and split dense prose into endpoint/run/counter/history tables (F39–F42).
- API: additionally disclosed that the history identity can fail for incomplete/budget-stopped runs and that stored run snapshots are not rewritten by later decisions; clarified Out visibility and persistence.
- Testing: removed stale totals and unsupported timings, separated deterministic suites from owner-only paid tools, corrected fixture/time-zone semantics and documented the externally managed e2e installation path (F43–F48).
- Operations/security report: independently found and corrected historical-drill/user-impact overclaims, stale Anthropic scorer/data-policy claims, assumed policy enforcement, unverified recovery and blanket no-training/no-credentials guarantees.
- Cross-file handoff: openapi.yaml and frontend/src/services/api.ts still describe countsVersion 3; smoke_search.py’s help/docstring still says ten batch entries. These are outside this writer’s scope and are explicitly disclosed in the docs.
- Validation: read all assigned files before editing; checked workflow/code claims with git/rg, inspected the referenced Grafana/Tempo/Loki/scoring images, and checked every new pinned code range with git show 542e58c:<path>.
- Validation: relative links resolve, all original heading anchors survive (aliases below), the API table equals all 19 OpenAPI operations, shell blocks parse with bash -n after replacing CLI placeholders, and git diff --check passes for the owned files.
- Validation: python3 -I -B incident-response/test_responder.py passed (20 tests); no model was launched. CI run 40251535674 on code snapshot 542e58c was read, not re-run: backend 507, frontend 117, integration 7, Playwright 12; docs direct readers to retrieve counts from CI.
- Validation: GETs checked both live health/config endpoints and the existing local alert/Tempo APIs; no prod/dev registration, login or search, no new local search/drill, no deploy, migration, restore or rollback was performed.
- Validation: read all 15 promotion logs and checked successive target ancestry (all forward); the 50 scheduled timestamps span 2026-10-17 through 2026-10-26 with gaps 2.109–7.841 hours, median 4.450 hours, rather than asserting a punctual hourly service.

## Findings rejected (id or quote, reason, evidence)

No finding’s core documentation defect was dismissed. The following proposed fixes or categorical inferences were rejected or limited:

- F01/F11, “prod today (969a161)” / split the table around the old deployed SHA: rejected as the final presentation because the owner explicitly requires writing for main and will promote before submission. The intended Exa configuration is labeled as configuration, not a live environment export; health commands report deployed commits dynamically.
- F04, “code rollback works only between releases with the same migration head”: matching heads is not proof a rollback works. The docs label even the code-only path proposed/untested; Dockerfile line 25 and all-forward promotion history are the evidence, not a successful rollback test.
- F05 proposed replacement, “code changes go through PRs (since #30)”: rejected as another unsupported universal. The release doc uses an intended path, a verified direct-push example and the absent protection/rulesets instead of a categorical historical claim; gh api repos/alexisdacquay/sail-event/commits/542e58c/pulls returns [].
- F18, “guaranteed to fire 2 h 10 min later”: not established. The rule is per returned series, needs samples, uses a range increase and has noDataState OK; therefore the docs explain idle-series risk without promising that exact firing time. Evidence: rules.yaml and policies.yaml.
- F19, “Probably true but not run here”: refreshed, not accepted as unverified fact. GET /api/alertmanager/grafana/api/v2/alerts on the existing local stack returned active DatasourceNoData, severity critical, receiver responder-webhook; GET /api/v1/provisioning/alert-rules/search-run-failures confirmed NoData and the same expression. Its labels/runbook differed from main, so this is explicitly not a fresh-main reproduction.
- F26 proposed table input, “alert.json and evidence.md”: the responder retains alert.json but interpolates only the task and fenced evidence.md into the model prompt. The final controls table separates responder input from model input. Evidence: responder.py build_prompt and _handle_alert; responder-task.md.
- F32 proposed “ran twice” as a complete history: rejected; the failed 2026-10-20 attempt is disclosed. Its error verdict is retrievable with git show 75e00a1:incident-response/incidents/20261020-231500-SearchRunFailures/verdict.json, and ad56f19 explains the removal.
- F37 proposal to fold all later tooling into the initial report: limited to a clearly dated addendum so the requested 2026-10-16/#1–#26 scope stays honest; enabled plugins are not claimed to have all been invoked. Evidence: .claude/settings.json, work/STATE.md, .claude/skills/.
- F40/F42, “accepted + queued + rejected + setAside == eventsFound on every finished run”: not a universal contract. search.py’s setAside excludes budget-unjudged events, and pipeline.py’s reservation can leave them new even on a finished run. The formula is corrected and the incomplete-run limitation is disclosed rather than reasserting the universal.
- F45 proposed “20 texts, 10 in parallel” for smoke_search.py: false for that script. Its BATCH_TEXTS has 20 entries but _run_batch uses ThreadPoolExecutor(max_workers=5); ten workers belongs to backend/tests/field/runner.py. Both docs facts are corrected. No script help text was edited because code is out of scope.
- F03’s exact orphan-image count is not retained: concurrent doc rewrites change references. A read-only scan during this pass found more unreferenced images than the original 17; the owner should decide image cleanup against the final merged docs, not a moving count.

## Anchors changed (old -> new)

All old anchors below remain as explicit HTML aliases. No inbound link needs to change to keep working; other writers may adopt the clearer new names.

- docs/deployment.md#prove-cd-in-30-seconds -> #check-deployed-commits
- docs/ai-usage-report.md#defects-the-orchestrator-caught -> #defects-and-corrections-in-the-initial-work
- docs/ai-usage-report.md#9-wrong-2025-image-tags-in-the-24-groom -> #9-image-versions-corrected-in-the-24-groom
- docs/ai-usage-report.md#what-was-verified-by-hand -> #browser-and-compose-checks-recorded-by-the-orchestrator
- observability/README.md#what-telemetry-contains-and-never-contains -> #telemetry-contents-and-privacy-gaps
- incident-response/README.md#recorded-incidents -> #recorded-drills-fault-injected-on-purpose

## Needs the owner (only real decisions, not wording)

- Promotion/recovery risk: decide whether to proceed with the irreversible PR #150 migration after confirming a real backup/recovery point, or defer promotion. Rollback and restore remain untested; the recorded recovery/network settings have not been verified in the dashboard in this pass.
- Database access: restrict or explicitly accept the recorded prod external inbound rule 0.0.0.0/0; this is not a docs-only change.
- Images (F02/F03): decide whether to recapture/re-crop the clipped review-07-scoring.png or retire it, and whether to remove/archive unused captures after the other writers finish. No image was altered.
- After the code freeze: decide whether to accept the disclosed monitoring/security gaps for this submission or schedule fixes for critical no-data/idle wakeups, unenforced responder edit scope, telemetry privacy and missing metric trace IDs, and the broken dashboard trace panel. These cannot be fixed honestly by wording.
