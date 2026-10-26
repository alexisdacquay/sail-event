---
name: reviewer-guide
description: Rebuild the Sail-event reviewer guide and, when assigned, the README reviewer map from the official rubric and verified evidence. Use before submission or when evidence changes.
---

# Reviewer guide

Write for busy, experienced engineers and executives evaluating the project. Read the owner's [docs quality standard](../../../work/docs-pass/STANDARD.md) completely. Its final section, **Win the reviewer**, overrides earlier guidance. Read [verified facts](../../../work/docs-pass/facts.md), especially `rubric`, and any assigned findings. Read each owned file completely before editing.

## Win the reviewer

Show what works, with proof a reviewer can check in a minute. State strengths plainly and keep claims within the evidence.

- Keep the rubric levels verbatim. Claim only supported clauses in the checklist; omit an unmet clause or narrow the claim to the part the evidence supports. Do not replace an omitted claim with a confession.
- Include no Known gaps sections, gap indexes, per-criterion gap lists, failure or exception audits, “what this does not prove”, “drill limits”, confessions of process lapses, untested or irreversible caveats, or “needs reassessment” notes.
- Frame process evidence as the handoff it proves: a groomed issue, an engineer's report, QA's verdict per criterion, work sent back and re-checked, or an owner decision.
- Keep positive counts with their command and sample: 58 groomed issues, 69 issues with QA verdicts and 23 issues where QA sent work back in the #1–#152 snapshot. Verify the count before retaining it. QA's return-and-recheck cycle demonstrates independent review.
- Keep normal, accurate labels such as **drill** and dates explaining when a rule began. Never describe an injected-fault drill as an actual outage.

## Scope and sources

- Respect file ownership and the change freeze. Update [docs/reviewer-guide.md](../../../docs/reviewer-guide.md); update [README.md](../../../README.md) only when assigned. Report needed changes in another writer's files to the orchestrator.
- Fetch the [official rubric](https://raw.githubusercontent.com/DataTalksClub/ai-dev-tools-zoomcamp/main/project/README.md) with an HTTP GET and compare it with the saved `work/rubric-*.md` copy. Report any difference; do not silently change the scoring contract.
- Verify claims using files, `git show`, `gh`, CI logs or HTTP GETs. A previous review is a lead. Do not invent users, numbers, dates, durations, behavior, deployment settings or guarantees. Remove claims without evidence.
- Write for main. Resolve its evidence commit with `git ls-remote https://github.com/alexisdacquay/sail-event refs/heads/main`; pin source links to that full commit and inspect each range with `git show COMMIT:path`. Date the snapshot. A source pin identifies the evidence version.
- Check live versions with `curl -fsS https://sail-event.onrender.com/api/health` and the corresponding dev endpoint. Link the check rather than hard-coding a changing expected SHA. The owner will promote the final docs commit before submission.

## Build each criterion in this order

Keep every `## N. Name` heading exactly: README links depend on them. Preserve other inbound anchors with a useful heading or explicit anchor; report any cross-file link change outside your ownership.

1. **Rubric levels.** Quote every level and its points verbatim, including zero and intermediate levels.
2. **Checklist.** Use supported atomic phrases from the full-marks wording, in rubric order. First column: exact contiguous rubric quotations. Other columns: where to look; a specific proof inspectable in under a minute. Keep shared predicates intact, such as “Both unit and integration tests exist”. For agent-team/context criteria, also check the lower-level responsibilities/project-description phrases, clearly labelled as such. Omit unsupported rows. Keep extras outside this table.
3. **Why not the lower score.** Quote the lower level exactly and explain the positive evidence relevant to it. Describe the demonstrated behavior without awarding a score or implying unsupported clauses are met.
4. **Beyond the rubric.** Keep only distinct, provable additions. Put core evidence in the checklist or main explanation. Do not self-grade.
5. **Picture.** Include a useful diagram or screenshot; omit empty Picture sections. Inspect retained images and caption their actual content, date and context. Prefer a CI run or issue history over a login-form screenshot. Do not edit images outside scope.

The criteria map gives a short strength per row. When assigned, the README map gives the criterion, evidence link and a short proof. No points, Max, Total, pass threshold or self-grades in the README.

## Explain the complex scored parts

Explain what an outsider cannot infer: agent launches, their context, role boundaries, process handoffs, context loading, CI/CD and promotion, and local telemetry → alerts → responder. Do not explain basic form entry, account creation or web search.

Use plain words and short sentences. No opening disclaimers, defensive hedges, editing history or references to the owner's instructions in reviewer-facing text. Headers must describe their contents. The README should take about five minutes to read; put detail in the guide and specialist docs.

- **Agent evidence:** name each role's input/output, who starts it and which artifact goes to the next role. Distinguish role-brief tasks from a runnable agent definition. Describe QA's instructions and independent checks accurately. Do not invent launch flags, model names, context behavior or tool enforcement.
- **Review handoffs:** QA sends findings to the engineer for a fix and re-check. The orchestrator sends any waiver request, criterion and evidence to the owner; only the owner grants or rejects it. Record that decision before merge. Show the handoff in prose and diagrams.
- **Process records:** use measured counts bounded to named issue/PR numbers or a fixed time range. Show representative specification → implementation → QA → owner handoffs. Verify rule dates against their introduction commits. Describe the operating rules as rules and recorded cycles as examples.
- **Delivery evidence:** distinguish PR CI, CI after push, dev deployment and manual production promotion. Use the dated Render deployment record for auto-deploy evidence, workflow/run history for production dispatches, and health responses for the running commit. The owner checks dev and approves a named production commit separately.
- **Observability:** state once that `make up-all` starts the local telemetry stack. Claim the supported facts: metrics exist; logs and traces share a trace ID; signals are collected, stored and viewable in Grafana. Scope the “share a trace ID” checklist proof explicitly to logs and traces. Do not claim metrics carry trace IDs or that no customer data or credentials reach telemetry. Keep the full rubric quotation, but omit unsupported checklist clauses. Show the working Tempo Explore and Loki views.
- **On-call evidence:** label injected-fault records **drills**, including captions and diagrams. Explain alert delivery, evidence collection, model launch and the repair commit. Name timings by their actual endpoints, such as “alert to fix commit”. The responder collects `evidence.md` before launch and creates its worktree from its checkout's HEAD. Describe runtime controls from the code. Claim only recorded actions; show human review/publication/deployment as separate steps.
- **Diagrams:** in Mermaid, `;` ends a statement, so never put it in message text or unquoted labels. The link checker flags this. If a GitHub preview is available, inspect changed diagrams there.
- **Search behavior:** use the scheduled workflow as evidence of the trigger. Use sourced duration ranges. Default thresholds are configurable and inclusive; the later duplicate check can reject a high-scoring event. Verify behavior against the pipeline and test assertions.

## Freshness and verification

- Avoid moving counts. If retained, give the date or evidence commit, the CI run where relevant, and the exact command that reproduces them. Bound tracker counts to a named issue/PR range and historical samples to a fixed cutoff or commit. Rerun the retained filters.
- Fetch CI with `gh run list -R alexisdacquay/sail-event --workflow=ci.yml -b main -L 3`; inspect the relevant run's logs. Name what each job runs. For the rubric's combined “run with a single command, and pass” evidence, use a recorded `make test-all` result with command, application-code commit, date, suite summary and exit status. Include only results supported by that record.
- Keep the five-minute check quick and read-only: availability, CI and tracker evidence. State prerequisites. Put builds and full test suites in the longer local review path.
- Verify local paths, heading anchors, reference links and external GET responses. Read each anchored code range. Keep `_docs/` (product/process), `docs/` (run/test/ship/review) and `work/` (evidence/history) distinct.
- Inspect a test's assertions before citing it as behavior proof. Use the test that executes the behavior being claimed. Use portable Compose service commands with the startup project's flags. A second terminal needs its own environment assignments.
- Never print secrets or `.env` files. Do not register, log in or run searches on hosted sites during verification. No code changes, commits, pushes, promotions or issue creation are authorized by this skill. Do not run `rm` or `sed -i`.
- Re-read owned files end to end. Run `python3 -I work/docs-pass/linkcheck.py README.md docs/reviewer-guide.md _docs/process.md AGENTS.md` plus every changed Markdown file. Require `all links ok`. Check inbound anchors from other docs too. Fix links within scope; report cross-file work under “Needs the orchestrator” in the requested handoff. Use independent agents only when the current task explicitly authorizes delegation.
