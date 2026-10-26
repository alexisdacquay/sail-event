## Fixed

- Fact review #2: corrected `docs/testing.md` to say the smoke tool bypasses criteria-save guardrails for every `GUARDRAIL` setting; verified with `nl -ba backend/scripts/smoke_search.py`, `nl -ba backend/app/routers/criteria.py` and `rg -n 'get_guardrail|GUARDRAIL|GUARD_FALLBACK' backend/scripts/smoke_search.py backend/app/adapters/factory.py backend/tests/test_guardrails.py`.
- Fact review #3: documented live attempt counts versus finished scored-event counts for `events_judged` in `docs/api.md`; verified `pipeline.py:514,529–535,569,701–714` with `nl -ba`.
- Fact review #4: documented schema and reason repairs, including recovery of older events, for `judge_repaired`; verified `judge.py:125–130,187–218` and `pipeline.py:181–198,708–712` with `nl -ba`.
- Reader #3, rubric #13 and orchestrator #1–3: removed bold opening disclaimers and repeated defensive qualifications from assigned ops docs; local scope is stated in the relevant feature section, with substantive limitations retained.
- Orchestrator #16: centralized rollback guidance in `docs/release-process.md`, with links to all three migration files and their recovery effects; verified each file and PR associations with `gh pr view 128 --json files` and `gh pr view 150 --json files`.
- Reader #19: added an explicit matching-secret command for a second responder terminal, without starting two responders; verified Makefile's target and `responder.py:272–275`.
- Reader #20: made the responder diagram/table explicit that repair starts at its checkout's HEAD and does not select the running app's revision automatically; verified `responder.py:127–133`.
- Reader #21 and rubric #6–7: kept the drill duration explicitly alert-to-repair-commit and made missing recovery and historical test output clear once; verified alert `startsAt`, `git show -s --format='%h %cI %s' 8d2f839`, both saved verdicts and agent logs.
- Rubric #1–3 and #15: retained telemetry privacy and metric-correlation gaps, and kept Explore → Tempo beside the dashboard link; inspected `telemetry.py`, pipeline attributes/metrics, `collector.yaml` and the saved dashboard image without editing images.
- Clarified that the incident script's final live assertions check file presence, while dry-run additionally checks its verdict; verified by reading `incident-response/test-incident.sh`, without running it.
- Rechecked alert configuration and the existing local alert endpoint; documented the observed `DatasourceNoData` route without implying failed searches or a new drill (`curl --max-time 5 -fsS http://localhost:3001/api/alertmanager/grafana/api/v2/alerts`, selecting only alert labels and receiver names).
- Reviewed CI/dev/promotion descriptions against all three workflows, Makefile and the dated Render deployment log; independently confirmed unprotected main, empty rulesets and the successful cited CI run using `gh` GETs.
- Corrected the inherited PR #138 chronology in release/AI reports: it merged before CI finished, then integration failed; `gh pr view 138 -R alexisdacquay/sail-event --json mergedAt,statusCheckRollup` reports merge 2026-10-24 21:08:59Z and integration completion 21:11:39Z.
- Refreshed the dated scheduler sample in deployment docs: 50 runs ending 2026-10-26 12:51 UTC span 2.1–7.8 hours between runs, median 4.8 hours; reproduced with `gh run list --workflow=hourly-search.yml --event schedule --limit 50 --json createdAt`, sorted adjacent timestamp differences and Python statistics.median.
- Kept the short dated scope and correct AI-orchestrator identity in `docs/ai-usage-report.md`, removed unexplained Fable shorthand and unsupported historical “never” wording, and preserved the disclosed role exceptions; checked process/STATE and dated role-history commits.
- Added the reviewer guide's `four-phase-field-runner` anchor on the testing-doc side; preserved other compatibility anchors.
- Re-read all eight assigned Markdown files end to end for meaning and English; `git diff --check` on those files passed.
- Final required link check passed with `all links ok`: `python3 -I work/docs-pass/linkcheck.py docs/api.md docs/testing.md docs/deployment.md docs/release-process.md docs/ai-usage-report.md docs/operations-and-security-report.md observability/README.md incident-response/README.md README.md docs/reviewer-guide.md`.

## Rejected

- None of the applicable review findings were disproved. Already accurate gap disclosures were retained and tightened rather than removed. `work/docs-pass/out/final-review.md` did not exist at the completion check.

## Needs the owner

- Rubric #10: a dated, sanitized Render auto-deploy-settings/deploy-history capture would close the remaining external-trigger evidence gap; the docs distinguish the recorded automatic deployment from commit comparisons. No dashboard login, setting change or image edit was performed.
- Rubric #1–3 and #15: telemetry sanitization, metric-to-trace correlation and the broken dashboard traces panel require implementation/configuration work after the docs-only freeze; all remain disclosed.
- Rubric #6–7: captured tests at the repair commits and a successful post-fix search/resolved alert are still missing; the retained drills establish code repair, not service recovery. No new drill or paid search was run.
- Rollback/restore remains untested; Render health-check-path and database-inbound decisions remain pending in the dated deployment log.
- Cross-file precision: `_docs/process.md` still groups PRs #31/#138 as merged with a failed integration check; the process fixer should distinguish #31's pre-merge failure from #138's failure after merge, using the timestamps above. This file is outside my write scope.
