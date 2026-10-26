## Files changed

- `AGENTS.md`
- `.claude/agents/qa-engineer.md`
- `_docs/process.md`
- `_docs/team/pm.md`
- `_docs/team/software-engineer.md`
- `_docs/team/qa-engineer.md`
- `_docs/task-template.md`
- `_docs/plan.md`
- `_docs/architecture.md`
- `_docs/search-spec.md`
- `_docs/search-design.md`
- `_docs/ux-spec.md`
- `_docs/ui-design.md`
- `_docs/ux-design.md`
- `_docs/theme-design.md`
- `_docs/icon-proposals/README.md`
- `work/docs-pass/out/team-changes.md` (this requested handoff)

## Changes (one line each: what and why)

- Applied the standard’s tone addendum: removed repeated caveats and consolidated the threshold-label gap in UX.
- Rebuilt the process overview around roles, launch briefs, input context, worktrees, lifecycle and handoffs so an outsider can find the operating model quickly; detailed evidence follows it.
- Added an abridged real engineer brief, background/model choices, reused QA contexts, supervision and compaction handoffs from the local session transcript and STATE.
- Distinguished operating rules from historical compliance; dated shared-checkout/PR phases, owner gates, QA-agent use and the regression gate.
- Disclosed orchestrator overreach, skipped grooming, missing QA verdicts, failed CI at merge, direct pushes and unprotected main; public reproduction commands return the documented counts.
- Aligned PM, engineer, QA and runnable-agent instructions on inputs, owner choices, commit exceptions, PR verdicts and meaningful red/green verification.
- Kept AGENTS short, corrected the original-task mapping, test command scope, default adapters and owner/freeze context.
- Replaced the invented problem and site-count comparison with the real repeated work between search results and a calendar; defined the user jobs once in UX.
- Corrected the query suffix, inclusive cutoffs, Out visibility, duplicate-check sequence, background scheduling scope, measured durations and recent schedule intervals.
- Added the missing PR #144/#150/#151 changes and removed unsupported product-history claims; wrote for main as directed.
- Replaced the stale schema with ORM columns and constraints; documented three environments, criteria-save guarding and the limits of leftover-event recovery.
- Put local-only telemetry up front, disclosed metrics without trace IDs and privacy limits, and labeled both incident examples as injected-fault drills.
- Disclosed untested rollback across the three migrations and PR #150’s irreversible deletion wherever rollback is discussed in these files.
- Rewrote stale search spec/design sections to match the actual pipeline, prompts, budgets, extraction, duplicate handling and API; separated quality targets from measured results.
- Corrected recall reporting to the 2026-10-24 20:04 record: 3/38 found, 0/38 accepted at ab21641; the reference set remains unvetted.
- Rewrote UX for the Stream, preserved linked section headings, and disclosed the threshold-label and rejected-event action gaps.
- Marked the older UX/theme proposals as historical instead of presenting their obsolete code assumptions as current; kept their design record and headings.
- Marked the October 25 UI decisions as built from PRs #146/#148 and corrected the icon README to the implemented sail mark.
- Tightened proof claims: the duplicate integration test checks visible uniqueness, the restart test checks event count, and the seeded-status boundary test is not presented as independent triage proof.
- Verified all 29 distinct code-line ranges against `git show 542e58c:<path>` and pinned links to full 542e58cb0fe73065a905febec7637bfa377a77c4.
- Checked relative paths, Markdown anchors and inbound links; no broken links into changed files were found; scoped whitespace checks passed.
- Ran the process’s tracker/GraphQL blocks verbatim, schedule/promote queries, PR-state/date checks and protection/ruleset GETs; did not run paid searches or modify application code.

## Findings rejected (id or quote, reason, evidence)

Numbers below are the 1-based positions in `findings-team.json`, which supplies no IDs. All 51 findings were reviewed; the substantive defects were fixed except the incorrect task-count proposal. These proposed fixes needed correction or qualification:

- **31, “issues 1–29 = tasks 1–29”: rejected.** The source has 28 numbered tasks. `rg '^## [0-9]+\.' _docs/outdated/tasks.md` lists 1–28; issue #29 split CD from task #18. AGENTS now states that mapping.
- **3, “58 … by the PM; 33 … by the orchestrator”: attribution not established by the evidence.** The body regex proves four sections on 58 issues, not who authored them; tracker comments share the owner’s login. Kept the reproducible structural counts and disclosed overreach separately. Likewise, finding 2’s approximate transcript-call totals are not presented as exact authorship counts.
- **7, “the hook always blocks secrets”: rejected as a guarantee.** `scripts/pre-commit` scans specified added-line patterns and exempts `.env.example`; it cannot establish detection of every credential. The docs say the pattern scan still runs when the test gate is skipped.
- **8/29/30, regression must fail at `<head>^`: replaced with the actual pre-fix/test-only red commit.** PR #144’s commit sequence and body contain multiple test/fix rounds; the immediate parent of the submitted head is not necessarily pre-fix code. QA instructions now require recorded red/green heads without editing reviewed files.
- **41, replace timing with a different whole-history average: not used.** Followed the owner’s recent-window decision: the latest 20 scheduled runs span 2026-10-22T23:17:45Z–2026-10-26T06:04:25Z, with gaps 2.47–5.84 hours. The PRD gives the reproducing `gh run list` command and the PR #144 source for 86–493-second local measurements.
- **43, mark changes “dev; prod still 969a161”: not applied.** The owner explicitly requires main-oriented docs for the final promotion. The deployment-health GET replaces hard-coded deployed SHAs.
- **45, “Never in In calendar or Review”: retained as a quality target, not a guarantee.** Model extraction/judging/dedup can fail; `dedup.py` keeps both rows on errors. The docs disclose those limits.
- **Additional fact-sheet correction:** “3/38 accepted” is not what `work/RECALL.md` says. Its 2026-10-24 20:04 entry records recall@run 3/38 and accepted-recall 0/38; the rewritten search spec preserves that distinction.

## Anchors changed (old -> new)

No inbound links use the removed subsection anchors. All headings linked from other files were retained.

- `_docs/ux-spec.md#event-card-queue-variant` -> `_docs/ux-spec.md#3d-queue`
- `_docs/ux-spec.md#empty-state` -> `_docs/ux-spec.md#3d-queue`
- `_docs/ux-spec.md#event-card-read-only-variant` -> `_docs/ux-spec.md#3e-all-events`
- `_docs/ux-spec.md#empty-state-1` -> `_docs/ux-spec.md#3e-all-events`

## Needs the owner (only real decisions, not wording)

- After the docs freeze, decide whether rejected events should remain terminal or become restorable. `EventDetail.tsx` renders **Add to calendar** for rejected events, while `routers/events.py` returns 400; the UI/API mismatch is disclosed in UX. This was verified from source, not by a paid live search.
