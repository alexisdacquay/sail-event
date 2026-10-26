## Fixed

- Reader 11: `_docs/process.md` now routes a failed criterion and evidence to the owner for an explicit waiver decision, records that decision, preserves QA FAIL and shows the path in the diagram; verified against the original lifecycle, rules and role files.
- Reader 12: the orchestrator's prohibited actions explicitly include grooming, implementation and QA, matching the README and the documented historical exceptions; verified with `rg` across the process, README and reviewer guide.
- Reader 13: the handoff table now explains that the orchestrator routes reports and briefs the next role; verified against the launch/context paragraphs and role inputs.
- Reader 14 and orchestrator 15: removed unexplained Fable shorthand, rewrote launch instructions as full sentences and defined worktree and PR head; checked `work/STATE.md`, the role files and recorded launch evidence in `work/docs-pass/facts.md`.
- Reader 15: replaced the owner's non-prohibition with an em dash in the “Must not do” column.
- Reader 16: renamed the empty four-phase heading to “Field-test references” and explained authorization and the return to the issue cycle; checked the actual phase table in `docs/testing.md` and the historical field log.
- Reader 17: renamed “Evidence it ran this way” to “Process records and exceptions” and retained its old anchor for incoming links.
- Reader 18: replaced the ambiguous “contract” prohibition with the issue's acceptance criteria, matching `_docs/team/software-engineer.md`.
- Orchestrator 16: removed migration/rollback detail from Lifecycle and kept one linked gap pointing to `docs/release-process.md#rollback`, whose recovery instructions were checked.
- Orchestrator 17: explained the change from the unattended loop to owner priority and production checks on 2026-10-21; verified the dated rule record and `git log` for process/role history.
- Facts 1: `_docs/search-spec.md` now distinguishes exact result-URL deduplication from canonical matching against stored single-event pages; read `pipeline.py:322–340` and `search.py:40–87`, then executed the source canonicalizer: two raw URLs, one canonical URL.
- Rubric 4, supporting PRD correction: `_docs/plan.md` now labels inclusive boundaries as implementation evidence and the linked pipeline test as fixture-search evidence; inspected `pipeline.py:743–750`, `test_pipeline.py:306–323` and the seeded-only test in `test_events.py`.
- Applied the orchestrator's tone guidance to architecture, search design and UX: moved telemetry limitations into their section, removed repeated rollback/no-place caveats, removed account-button trivia and shortened defensive explanations while retaining the concrete gaps.
- Expanded architecture's duplicate limitation to include exhausted budgets, verified in `dedup.py:73–104`; checked its schema against `orm.py` and telemetry disclosures against pipeline instrumentation, `telemetry.py` and collector configuration.
- Added `input` and `event-detail` anchors on our side for incoming reviewer-guide links; confirmed issue #101 and PR #103 remain OPEN and the request dates from 2026-10-21 using `gh issue view` and `gh pr view`.
- Re-ran the process's two tracker-audit command blocks: 96 issues, 58 with four sections, 69 issue QA headings, 23 FAIL headings, 45 closing notes, 30/56 PR QA headings, 14/42 later merges without that PR heading and eight PR-driven issue closures all reproduced.
- Re-read all six changed documents end to end; checked AGENTS.md, role files and the runnable QA definition and left those unchanged because no correction was needed.
- Validation: prescribed linkcheck over the six changed docs plus README and reviewer guide returned `all links ok`; separate AGENTS/QA-agent linkcheck also passed, and `git diff --check -- _docs AGENTS.md .claude/agents/qa-engineer.md` was clean.

## Rejected

- None. All findings concerning the assigned files were reproduced.

## Needs the owner

- None for these documentation fixes. No final-review.md existed at the final check.
