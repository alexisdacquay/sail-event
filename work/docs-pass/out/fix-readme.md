## Fixed

- Reader 1 / rubric 11 / orchestrator README length: reduced README from 3,295 to 1,665 source words (about 1,357 prose/table words excluding fences, link destinations and reference definitions), retaining the requested opening order, reviewer map and four complex-process diagrams.
- Reader 2 / rubric 12 / orchestrator 3: removed the five defensive hedges, stale live-clock aside, audit counts and repeated historical defenses; verified the original wording with `cat README.md` and the rewrite with a phrase scan.
- Reader 3 / rubric 13 / orchestrator 1: removed top-level bold warnings and repeated operations caveats; local coverage is stated once in its feature section, and injected-fault runs are labeled drills where presented.
- Reader 4 / rubric 14 / orchestrator 4 and 7: removed button-renaming and widget-label trivia while retaining meaningful thresholds and save/search behavior.
- Reader 5: narrowed the aggregator comparison to aggregation of known listings, preserving the product gap required by the brief; checked `git show 'ac54483^:README.md'` and `_docs/plan.md` before rewriting.
- Reader 6 / orchestrator 6: corrected the score-range header, literal criteria-plus-event search description, and filtering English; verified `pipeline.py:286,487–510,743–750`, `filters.py`, and the pipeline-exercising triage test.
- Orchestrator 8: reduced scheduling to two sentences with guide evidence; inspected `hourly-search.yml` and ran `gh run list -R alexisdacquay/sail-event --workflow hourly-search.yml --event schedule -L 50 --json createdAt` without triggering work.
- Rubric 5: scoped duplicate-removal behavior to the fixture integration scenario and retained one explicit error/budget limitation; verified `dedup.py:74–104`, `test_dedup.py`, integration test lines 103–129 and the PRD.
- Reader 11–13 cross-document handoffs: retained the orchestrator boundary, made fix/recheck routing explicit, described owner-granted/rejected waivers with QA remaining FAIL, and verified the concurrently updated process now agrees.
- Reader 19: made the second-terminal webhook-secret assignment explicit; verified Makefile's responder target and `responder.py:272–275`, rather than starting a paid drill.
- Reader 20: specified that repair worktrees start at the operator checkout's HEAD rather than automatically selecting the deployed revision; verified `responder.py:127–133`.
- Reader 21 / rubric 6 / orchestrator 9: labeled the 4 min 52 s interval as alert to repair commit and kept the missing-recovery disclosure; computed the interval from `alert.json` and `git show -s --format=%aI 8d2f839` and inspected the fix stat.
- Rubric 1–3, 7 and 15: kept metric-correlation/privacy failures, incident test-evidence weakness and the working Explore → Tempo route; inspected telemetry instrumentation, alert rules, responder limits and recorded artifacts.
- Facts 6 / orchestrator 10: added the no-place auto-accept and unusable Out-event restore gaps, and shortened the remaining gap index; verified `gh issue view 101 --json state,title,url`, EventDetail.tsx:81–86 and events.py:80–84.
- Reviewer evidence: verified prod health/config through read-only GETs, PR #144's latency table, issues #7/#11 and passing CI run 40251535674 including the restart test; retained pinned evidence without presenting a fixed commit as current main.
- Re-read the completed README end to end for meaning, English and STANDARD.md; `git diff --check -- README.md` and standalone `python3 -I work/docs-pass/linkcheck.py README.md` pass, and every README guide fragment uses a numbered criterion heading.
- Final required combined link check, `python3 -I work/docs-pass/linkcheck.py README.md README.md docs/reviewer-guide.md`, passes with `all links ok` after the other fixers completed their link corrections.
- Checked for `work/docs-pass/out/final-review.md` at handoff; it does not exist.

## Rejected

- None of the README findings required rejection; the aggregator sentence was narrowed instead of retaining the blanket industry claim.

## Needs the owner

- None for this README fix; existing product, telemetry, delivery and drill limitations remain disclosed for separately scoped work.
