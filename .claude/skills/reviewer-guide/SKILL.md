---
name: reviewer-guide
description: Rebuild the Sail-event reviewer guide and, when in scope, the README reviewer map from the official rubric and verified repository evidence. Use before submission or when evidence changes.
---

# Reviewer guide

Write for busy, experienced engineers and executives evaluating the project. Follow the owner's [docs quality standard](../../../work/docs-pass/STANDARD.md) completely. Read [verified facts](../../../work/docs-pass/facts.md), especially `rubric`, and any assigned findings before editing. Read each owned file completely; review the whole file, not only flagged lines.

## Scope and sources

- Respect the current file ownership and change freeze. Update [docs/reviewer-guide.md](../../../docs/reviewer-guide.md); update [README.md](../../../README.md) only when assigned. Report cross-file changes to the owner instead of editing another writer's files.
- Fetch the [official rubric](https://raw.githubusercontent.com/DataTalksClub/ai-dev-tools-zoomcamp/main/project/README.md) with an HTTP GET and compare it with the saved `work/rubric-*.md` copy. If they differ, report the difference; do not silently replace the scoring contract.
- Verify claims using files, `git show`, `gh`, CI logs or HTTP GETs. A previous review is a lead, not proof. Do not invent users, numbers, dates, durations, behavior, deployment settings or guarantees. Remove claims without evidence.
- Write for main. For this docs pass, code-line links are pinned to `542e58cb0fe73065a905febec7637bfa377a77c4`; check every range against `git show 542e58c:<path>`. This is an evidence pin, never a claim about the deployed commit.
- Live versions come from `curl -s https://sail-event.onrender.com/api/health` and the corresponding dev endpoint. Do not hard-code their expected SHAs or claim a pinned commit is current main. Compare dev with `git ls-remote https://github.com/alexisdacquay/sail-event refs/heads/main`, allowing for deployment delay.

## Build each criterion in this order

Keep every `## N. Name` heading exactly: README links depend on them. Preserve other inbound anchors, or list each old → new anchor in the handoff.

1. **Rubric levels.** Quote every level and its points verbatim, including zero and intermediate levels. Do not paraphrase or narrow a clause.
2. **Checklist.** Split the full-marks wording into atomic phrases, in rubric order, using the phrase list in `facts.md` as the coverage check. First column: the rubric's phrases, verbatim. Other columns: where to look; a specific proof inspectable in under a minute. Do not mix project extras into this table. For agent-team/context criteria also check the lower-level responsibilities/project-description phrases, clearly labelled as such. Evidence may be partial or absent; say so in that row.
3. **Why not the lower score.** Quote the lower level exactly and explain what evidence closes that particular concern. Do not invent objections, count lines as proof of clarity, or recount earlier wording fixes. If a full-marks clause is unmet, keep it visible rather than declaring the lower level impossible.
4. **Beyond the rubric.** Keep only useful extras with evidence. Extras do not compensate for an unmet clause; avoid “extra credit” or self-scores.
5. **Picture.** Use one only where it helps verification or explains a complex flow. Otherwise say the linked record is more useful. Prefer an inspectable CI run or issue history over a screenshot of a login form. Inspect every retained image; caption its actual content, date/context and limitations. Do not edit images outside scope.
6. **Known gaps.** State the criterion's limitations plainly, with evidence. Keep the complete end-of-guide index aligned with these disclosures and the opening criteria map. Missing evidence is a gap, not a passed check.

The README map, when assigned, has criterion, guide/evidence links and a short proof or limitation. No points, Max, Total, pass threshold or self-grades. The guide may quote the rubric's points; it does not award itself a score.

## Explain the complex scored parts

Use careful steps for things an outsider cannot infer: agent launches and their context, role boundaries, process handoffs, context loading, CI/CD and promotion, and local telemetry → alerts → responder. Distinguish the written process from observed compliance. Do not explain basic form entry, account creation or web search.

- Agent evidence: name each role's input/output, who starts it and which artifact goes to the next role. Distinguish generic role-brief tasks from a runnable agent definition. A separate QA task is not proof of tool-enforced read-only access. Do not invent launch flags, model names or context behavior absent a source.
- Process evidence: replace “every task”, “each one” and “always” with a measured count, denominator and reproducible filter. Disclose ungroomed issues, orchestrator overreach, closures/merges without QA PASS, direct pushes and red merges. Date when owner-control and regression rules began. Shared GitHub authorship and role labels do not independently authenticate agents.
- Delivery evidence: Render settings live outside git. A matching health SHA is indirect evidence, not proof of the auto-deploy trigger. Separate PR CI, CI after push, dev deployment and manual production promotion. Disclose missing enforcement or missing settings captures.
- Rollback: documented does not mean exercised. In this pass rollback across the three new migrations is untested, and PR #150's deletion is irreversible. Any rollback mention must include those limits; do not prescribe an untested backup restore as a proven fix.
- Operations evidence: say up front that telemetry, alerts and the responder cover `make up-all` locally; the deployed app sends no telemetry to that stack. Distinguish application logs in Render from exported telemetry. Preserve “share a trace ID” for metrics, traces and logs: metrics lacking that ID is a gap. Include credential/privacy exposure from automatic HTTP spans and container access logs, not only attributes the app selects.
- Label injected-fault alert/on-call records **drills**, including captions and diagrams. Separate detection, evidence collection, model reasoning, code repair, tests, branch publication, deployment and verified recovery. The responder collects `evidence.md` before launching the agent. JSON fields alone do not prove a webhook's sender. Written autonomy policy is not enforcement; inspect the runtime code.
- Search behavior: “hourly” is the GitHub cron, not an observed interval. Measure actual gaps or omit an interval. Use sourced duration ranges, never a guessed “1–2 minutes”. Out rows are available through **show**; later searches do not revive them. Default thresholds are configurable and inclusive; the later duplicate check can reject a high-scoring event.

## Freshness and verification

- Avoid moving counts. If retained, state the date or evidence commit, the CI run link where relevant, and the exact command that reproduces them. Fetch latest CI with `gh run list -R alexisdacquay/sail-event --workflow=ci.yml -b main -L 3`; inspect its logs. Name what each CI job actually runs, local-only suites, expected failures and screenshot-oriented tests.
- Distinguish a combined test command existing from a recorded passing execution of that command. CI proving its component steps is not a captured `make test-all` pass.
- The five-minute check contains only quick, read-only availability/evidence checks. No builds, full test suites, registrations, logins or paid searches. State prerequisites and move longer local work elsewhere without guessing a runtime.
- Check local paths, heading anchors, reference links and external GET responses. Check what each anchored code range says, not only whether the number is in bounds. Keep `_docs/` (product/process) distinct from `docs/` (run/test/ship/review) and `work/` (evidence/history).
- Never print secrets or `.env` files. Do not register, log in or run searches on hosted sites during verification. Local probes must avoid exposing real feed tokens. No code changes, commits, pushes, promotions or issue creation are authorized by this skill.
- Review once more against STANDARD.md and the complete findings list. Record rejected findings with evidence, changed anchors and genuine owner decisions in the requested handoff. Use independent reviewers only when the current task authorizes delegation; do not repeat self-grading until reviewers agree.
