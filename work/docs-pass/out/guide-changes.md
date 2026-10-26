# Reviewer-guide handoff — 2026-10-26

## Files changed

- `docs/reviewer-guide.md`
- `.claude/skills/reviewer-guide/SKILL.md`
- `work/docs-pass/out/guide-changes.md` (this required handoff)

## Changes

- Rebuilt all twelve criteria with the same six parts: verbatim levels, atomic-phrase checklist, exact lower-level wording, proven extras, useful pictures and known gaps.
- Checked all 35 quoted rubric levels against the saved official rubric; the fetched course source matched that copy.
- Replaced the self-scored scorecard with a criteria map and visible limitations; preserved all twelve numbered headings and the linked five-minute/known-gaps headings.
- Removed expected live SHAs; health GETs report deployment identity, while code-line evidence uses the required full `542e58cb0fe73065a905febec7637bfa377a77c4` pin.
- Rebuilt the five-minute check around read-only HTTP/git/gh evidence; moved Docker builds and test suites outside its time promise.
- Corrected the product framing, inclusive configurable thresholds, event-page and later duplicate stages, Out/show behavior, fixture limitations and fixed demo clock.
- Replaced guessed search timings with PR #144's qualified 86–493-second observations and a reproducible scheduled-run gap measurement of 2.1–7.8 hours.
- Replaced universal process claims with dated tracker counts, denominators and commands; disclosed ungroomed issues, missing QA verdicts/PASSes, orchestrator overreach, role attribution limits and late rules.
- Explained agent launches, role inputs/outputs, handoffs, context loading/compression and re-check reuse; distinguished written instructions from enforced boundaries.
- Distinguished PR CI, main-push CI, dev deployment and manual production promotion; disclosed red merges, direct pushes, missing gates and external Render-setting evidence.
- Removed guaranteed rollback claims; disclosed untested rollback across all three new migrations and PR #150's irreversible deletion wherever rollback is discussed.
- Put local-only telemetry, alerts and responder coverage up front; retained the full trace-ID/privacy rubric and marked metrics correlation and credential/customer-data clauses incomplete.
- Checked the invalid local calendar-path probe against access logs and Loki; disclosed observed path/IP logging and unverified transport into Loki without exposing a real feed token.
- Labelled both alert/responder records as injected-fault drills; separated evidence collection, agent reasoning, local repair, human publication and unrecorded deployment/recovery.
- Corrected responder tool/policy claims, empty drill evidence, weak test claims and the +1/−4 repair description; removed unsupported claims of safe file restrictions or proven recovery.
- Inspected all four retained embedded/linked screenshots; retained only pictures that support the nearby evidence and disclosed the broken dashboard traces panel.
- Pinned CI counts to run `40251535674` at `542e58c`, added reproduction commands, and disclosed expected browser failures, screenshot tests, local-only responder tests and no captured combined `make test-all` pass.
- Updated the rebuild skill to enforce STANDARD.md's audience, verification, verbatim rubric mapping, complex-part explanations, honest drills/gaps, freshness rules and assigned-file boundaries.
- Verified 209 guide link usages and 5 skill links against current files/anchors, checked pinned code ranges with `git show`, and received HTTP 200 for all 42 unique external HTTPS URLs checked.
- Verified all eight bash blocks parse, the skill validator passes, and `git diff --check` passes; the responder's 20 tests passed without launching an agent. Full application suites and incident-branch tests were not rerun.

## Findings rejected

Numbers below are one-based positions in `findings-guide.json`, which has no explicit IDs. These reject specific factual details or proposed fixes; the underlying documentation defects were otherwise corrected.

- **#144, “#17, #21 and #29 … have no acceptance criteria”:** false for #29. `gh issue view 29 -R alexisdacquay/sail-event --json body` shows Goal, Acceptance criteria, Out of scope and Constraints. Its historical AWS criteria are stale, and its missing QA verdict remains disclosed.
- **#30, proposed “A search takes 1–2 minutes”:** contradicted by `gh pr view 144 -R alexisdacquay/sail-event --json body`, whose measurements span 86–493 seconds across different revisions/configurations. The guide uses that qualified range.
- **#48, proposed seven GitHub-closed issues:** conflicts with #116/#131 and the verified eight cases (#46, #52, #68, #76, #83, #120, #122, #142). The guide explains merge-triggered closure without retaining the unnecessary moving count.
- **#49, proposed “20 went back to the engineer”:** subtracting three exceptions from 23 FAIL issues does not establish that claim; #14/#15 also record orchestrator verification. The guide retains the reproducible FAIL count and names the role exceptions instead.
- **#147, proposed Grafana-only JSON fields as sender proof:** any authenticated client can supply those strings. `git show 542e58c:incident-response/test-incident.sh` instead supports the drill chain: its direct `/alerts` POST is resolved, then it drives failures and waits for Grafana to fire.
- **#10/#80, proposed guaranteed same-schema rollback or blanket restore/fix-forward instructions:** no recorded rollback/recovery test supports such a guarantee. `git show 542e58c:backend/alembic/versions/f5a6b7c8d9e0_cleanup_events_without_start_time.py` proves the irreversible delete and empty downgrade; the guide discloses the untested recovery boundary rather than presenting a procedure as proven.
- **#20/#118, proposed persistent old-production caveats:** the observed lag was valid during review, but the owner's explicit write-for-main/final-promotion instruction supersedes carrying that snapshot into the submission. The guide labels local screenshots and reads deployed identity from health, without hard-coding either environment's SHA.

## Anchors changed

- `docs/reviewer-guide.md#scorecard` → `docs/reviewer-guide.md#criteria-map`.
- `.claude/skills/reviewer-guide/SKILL.md#steps` → `.claude/skills/reviewer-guide/SKILL.md#build-each-criterion-in-this-order`.
- `.claude/skills/reviewer-guide/SKILL.md#rules` → `.claude/skills/reviewer-guide/SKILL.md#freshness-and-verification` (requirements also organized under the new scope and complex-parts headings).
- All twelve numbered guide anchors, `#check-it-in-5-minutes`, `#known-gaps` and `#what-this-run-does-not-prove` are preserved. No inbound references to the renamed anchors were found with `rg`.

## Needs the owner

None within this documentation assignment.
