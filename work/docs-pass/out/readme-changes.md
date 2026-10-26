## Files changed

- `README.md`
- `work/docs-pass/out/readme-changes.md` (this requested report)

## Changes (one line each: what and why)

- Rebuilt the opening as product description → screenshot → live trial → three-column reviewer table; removed self-scoring, repetitive signup instructions and invented user numbers.
- Rewrote Problem from the pre-PR-152 basis: scattered small events, aggregators collecting known events, and search pages still needing checks and calendar entry.
- Kept the hero image untouched and captioned its local fixture dates and two reported failed fetches without inventing a cause.
- Condensed functionality; documented query suffix, event-page attempts, inclusive thresholds, both duplicate checks and Out's show toggle.
- Corrected repeat-search expectations: duplicate rows may be stored as Out; the integration test proves no duplicate visible accepted/review events, not zero duplicate rows.
- Trimmed expected-behaviour claims to their actual proofs, including threshold reload persistence and events remaining listed after their dates pass.
- Replaced latency promises with PR #144's 86–493-second Mac measurements, explicitly identifying their environment rather than claiming a Render benchmark.
- Labelled scheduled-run samples by date, included recent 2–6-hour gaps and the older 7.8-hour maximum, and supplied the timestamp command; documented user rotation and enqueue-only success.
- Added all team roles, boundaries, artifact handoffs, PR/CI stages, the owner's separate merge/promote words, and a sequence diagram.
- Added agent context loading: CLAUDE.md/AGENTS.md, modular docs, the orchestrator's brief, role-specific reading, QA re-check reuse and STATE handover.
- Replaced universal process claims with dated 58/96, 69/96, 23 and 30/56 heading counts, linked to reproducing commands; disclosed ungroomed issues, missing QA, orchestrator overreach, direct pushes, unprotected main and red merges.
- Dated process origins, owner gates and the bug-fix regression rule rather than applying them backwards in time.
- Separated CI/dev/prod delivery from local observability; retained health-based version checks instead of fixed deployed SHAs and disclosed the historical environment-change redeploy.
- Stated at every rollback mention that the three-migration path is untested and PR #150's deletion is irreversible; corrected the migration origins to PRs #128/#150 using git history.
- Explained the local telemetry/alert/responder loop with a diagram, startup requirements, separate responder process, alert expressions and silence/no-data limitations.
- Labelled both recorded incidents as injected-fault drills, retained the UTC 4 min 52 s timeline, and disclosed empty Loki evidence, the labelled culprit and unsupported agent test total.
- Preserved the rubric's trace-ID scope and disclosed missing metric correlation, feed-token exposure, exception text, broad container-log collection and the broken trace panel.
- Removed the duplicate curl mutation walkthrough and image tables; API instructions remain in docs/api.md and telemetry screenshots remain in observability/README.md.
- Retained existing linked section headings and replaced the long document inventory with AGENTS.md plus the main review/operations links.
- Verified 91 local links/anchors, 23 external URLs by HTTP GET, all 13 line ranges with git show 542e58c:<path>, and git diff --check; all passed.
- Rechecked live health/config by GET, main CI run 40251535674 and its restart-test log, PR #144 measurements, tracker queries, rule history, migration source and recorded incident evidence; no accounts, logins or searches were run on either live site.
- No code tests were rerun for this documentation-only change; passing CI is identified as recorded evidence at 542e58c, not as a new local result.

## Findings rejected (id or quote, reason, evidence)

IDs below are the one-based array positions in `findings-readme.json` (F001–F101), which has no explicit ID field. All 101 were read; overlapping findings were fixed together. The following rejects concern unsupported claims or proposed remedies; the valid underlying defects were addressed.

- **F001/F002/F015/F016/F048/F066/F096: add an old-prod caveat or send the main trial to dev.** Superseded by the owner's explicit instruction to write for main and promote before submission. Main's save-and-search form, detail hop, no-time filter and funnel were checked with `git show 542e58c:<path>`; health uses the requested GET command, with no deployed SHA hard-coded.
- **F009/F078/F079: declare dev's clock frozen at 18 October.** Not established live. The older deployment table conflicted with `work/STATE.md:128,155`, which calls for FAKE_NOW to be unset for real runs. The revised deployment doc also explicitly says Render was not rechecked. README explains Compose's verified fixed clock and labels dev's live value unknown; shared-demo warnings were applied.
- **F012/F052: describe the two failed fetches as deliberately failing offline/by design.** The screenshot proves the failures, not their cause. Current pipeline code passes `fetch_pages=provider_name in _WEB_PROVIDERS` (`git show 542e58c:backend/app/services/pipeline.py`, lines 418–428). The caption states only what the unchanged image shows.
- **F027: prescribe downgrade/PITR as a working rollback recipe.** Neither recovery path was tested. The migration's `downgrade()` is `pass`; Dockerfile runs `alembic upgrade head` at boot. README states the untested schema path, irreversible delete and backup requirement without inventing a validated recovery procedure.
- **F047/F090: replace the date claim with “all screenshots captured 2026-10-26.”** That proposed blanket date is not supported: facts.md records telemetry captures dated 25 October. README retains only the hero, whose visible chronology is 26 October, and removes the broad screenshot-origin/date assertion.
- **F050/F068: retain 1–2 minutes or replace it with 2–5 minutes.** `gh pr view 144 -R alexisdacquay/sail-event --json body` includes 86.0-second and 493-second runs. Neither suggested range covers that evidence; README gives 86–493 seconds with the environment and source.
- **F065: add “paid starter instances: no sleep, no cold start.”** A recorded plan name does not establish a no-cold-start guarantee. Current Render settings were not inspected; this unsupported promise remains omitted.
- **F070: infer 237 direct commits by subtracting 30 squash-style subjects from 267 commits.** That calculation misses ordinary PR merges. `git show -s --format='%h %P %s' a348152` shows two parents and `Merge pull request #92 ...`, without the `(#N)` suffix. README discloses direct pushes without reusing that invalid count.

## Anchors changed (old -> new)

- `#try-it-in-60-seconds` → `#try-it-live` (removed the unsupported time promise; repository Markdown search found no inbound links to the old anchor).
- All other existing section anchors remain, including `#try-it`, `#problem`, `#what-it-does`, `#what-it-does-not-do`, `#expected-behaviour`, `#for-reviewers`, `#how-it-was-built-an-agent-team`, `#how-it-is-built-the-stack`, `#ship-it-watch-it-fix-it`, `#all-the-docs` and `#status`.

## Needs the owner (only real decisions, not wording)

- No new decision. The existing owner-only database-backup and production-promotion gate remains in force; this pass does not perform it.
