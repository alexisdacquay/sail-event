# Reader verification

Read work/docs-pass/STANDARD.md and the rubric in work/docs-pass/facts.md first, then README.md, docs/reviewer-guide.md and _docs/process.md in that order, completely. Findings below concern the checked-out rewrite. Linked code, role files, the public tracker and the pinned CI log were inspected where needed to substantiate a fix. No live account, login or search was used.

1. **File and location:** README.md:21–252, especially the reviewer map, team, delivery and Known gaps sections

   **Exact quote:**

   README.md:

   > ## For reviewers



   README.md:

   > ## Ship it, watch it, fix it



   **Problem:** The README is about 3,150 words after removing link destinations and reference definitions. It is a second reviewer guide, with a twelve-row rubric map, several diagrams, audit counts, reproduction commands and repeated caveats. A five-minute reader cannot absorb this before reaching the actual guide. The problem statement starts only after the large reviewer map.


   **Fix, with source:** Keep the product problem, behavior, one local command, a short team/delivery summary, a concise gap summary and links. Move audit detail and operational procedures into the guide or their existing specialist docs. Source: work/docs-pass/STANDARD.md, “Honest, not defensive”: “The README should read in about 5 minutes. Detail belongs in the guide and the linked docs.” The word count is from these checked-out contents, counting word tokens after stripping Markdown link destinations and reference definitions.


   **Severity:** medium.

2. **File and location:** README.md:13, 106, 152, 154 and 165

   **Exact quote:**

   README.md:

   > Those measurements are not a Render benchmark.



   README.md:

   > the repository alone cannot establish its live value.



   README.md:

   > it is not a claim about all earlier work.



   README.md:

   > These counts measure headings, not complete adherence to the process.



   README.md:

   > It does not establish that every commit was tested.



   **Problem:** These are almost the owner’s verbatim examples of legalistic hedging to remove. They repeatedly defend against claims the reader has not made. Their survival makes the rewrite look unchecked against its governing standard.


   **Fix, with source:** State the bounded facts positively: the measurements were local; the rule began on its stated date; the counts match the documented filters; the hook runs the named checks and has a bypass. Remove the unverified live-clock aside unless needed to run a review. Source: work/docs-pass/STANDARD.md, “Honest, not defensive,” explicitly lists these phrases or their near-identical forms as examples to remove.


   **Severity:** medium.

3. **File and location:** README.md:25, 202 and 250; docs/reviewer-guide.md:5, 24–26, 471, 518, 522, 538, 558, 564, 622 and 650

   **Exact quote:**

   README.md:

   > **Observability, alerting and the on-call responder run locally. The deployed app exports no telemetry to that stack, so these alerts do not monitor the live sites. The recorded incidents are drills.**



   docs/reviewer-guide.md:

   > **Observability, alerts and the on-call responder cover the local stack (`make up-all`). The deployed app sends no telemetry to that stack. Both recorded on-call runs are drills with injected faults.**



   **Problem:** Both pages open with the bold disclaimer the owner expressly prohibited, then repeat local-only scope and drill status through maps, section introductions, gap lists and the final gap index. The limitation is important; this repetition turns the documents into a defense brief and crowds out the working demonstration.


   **Fix, with source:** State local scope once in the observability explanation and identify each recorded incident as a drill where presented. Let maps and gap indexes link to that explanation rather than restate it. Keep the actual missing rubric clauses visible. Source: work/docs-pass/STANDARD.md, “Honest, not defensive”: no bold disclaimers at the top; state each limitation once, where it matters.


   **Severity:** medium.

4. **File and location:** README.md:11 and 60; docs/reviewer-guide.md:399

   **Exact quote:**

   README.md:

   > after a run, the button reads **Search again**.



   README.md:

   > The funnel calls Review “to review” and Out “rejected”.



   docs/reviewer-guide.md:

   > The UI uses **Create one** / **Create account**



   **Problem:** Button renaming and synonym translation are UI trivia. They do not help an experienced reviewer understand the system or prove deployment. The deployment section even presents account-button wording under “Beyond the rubric.”


   **Fix, with source:** Remove these label notes. Keep the substantive one-action save/search behavior, inclusive threshold behavior and registration configuration where relevant. Source: work/docs-pass/STANDARD.md, “Audience and tone” and “Honest, not defensive,” explicitly reject trivial instructions and button/label inconsistencies unless needed to follow a step.


   **Severity:** low.

5. **File and location:** README.md:46, Problem

   **Exact quote:**

   README.md:

   > Calendar aggregators collect events you already know about.



   **Problem:** This unqualified industry claim is unsupported by the linked project evidence and reads as a straw-man comparison. It distracts from the concrete, credible gap in the next sentence: repeating discovery, checking details and copying events.


   **Fix, with source:** Delete the aggregator claim and use the narrower problem already stated in _docs/plan.md:19–25: web search returns pages and the person must check, choose, copy and repeat. Sources: _docs/plan.md, Problem; work/docs-pass/STANDARD.md, “Facts” and its real-world-gap example.


   **Severity:** medium.

6. **File and location:** README.md:54, threshold table

   **Exact quote:**

   README.md:

   > | Default score | Status | Result |



   **Problem:** There is no default event score in this table. Its rows are score ranges evaluated using the default thresholds. The header names the wrong thing.


   **Fix, with source:** Use “Score at default thresholds” or “Score range (default thresholds).” Sources: README.md:52 and 56–58; backend/app/services/pipeline.py triage comparisons; work/docs-pass/STANDARD.md requires headers to match their content.


   **Severity:** low.

7. **File and location:** docs/reviewer-guide.md:116–118, 281–283, 324–326 and 401–403

   **Exact quote:**

   docs/reviewer-guide.md:

   > **Picture**



   docs/reviewer-guide.md:

   > a screenshot would hide its revision history.



   docs/reviewer-guide.md:

   > another app screenshot adds no persistence evidence.



   docs/reviewer-guide.md:

   > a static screenshot would become stale.



   docs/reviewer-guide.md:

   > No image is needed: the public URL and response are directly inspectable.



   **Problem:** Several “Picture” sections contain no picture and instead explain why there is none. These are unremoved template instructions, not useful reviewer content. The header repeatedly fails the owner’s basic matching-content rule.


   **Fix, with source:** Remove empty Picture sections. Fold useful issue-history or CI links into the evidence paragraphs. Retain actual diagrams and screenshots where useful. Sources: work/docs-pass/STANDARD.md, “Audience and tone”; the guide’s own introduction says a picture is included “where useful,” not in every section.


   **Severity:** low.

8. **File and location:** docs/reviewer-guide.md:72–75, 314–322, 500–502 and 592–595

   **Exact quote:**

   docs/reviewer-guide.md:

   > **Beyond the rubric**



   docs/reviewer-guide.md:

   > - Thresholds are per user.



   docs/reviewer-guide.md:

   > The app exports OTLP to the collector; Prometheus scrapes collector metrics; Loki and Tempo receive logs/traces.



   docs/reviewer-guide.md:

   > - A second drill, **2026-10-17**, injected a scorer fault



   **Problem:** The “Beyond” sections mix true extras with ordinary product behavior, test-pass evidence, the telemetry collection path and another demonstration of the scored on-call requirement. Calling required evidence an extra is inflated labeling. It also hides the complex observability explanation below a heading that suggests optional material.


   **Fix, with source:** Move core evidence and operational explanations into the relevant criterion’s main explanation. Keep “Beyond the rubric” only for distinct, provable additions, such as API-contract checking or specific responder controls. Sources: full rubric in work/docs-pass/facts.md, “rubric” (Testing, Observability and On-Call Agent); work/docs-pass/STANDARD.md, “Rubric presentation” and “Honest labels.”


   **Severity:** medium.

9. **File and location:** docs/reviewer-guide.md:496–498, Observability

   **Exact quote:**

   docs/reviewer-guide.md:

   > **Why not the lower score**



   docs/reviewer-guide.md:

   > This closes the absence-of-signals concern.



   docs/reviewer-guide.md:

   > The rubric has no intermediate level for this combination; the reviewer decides.



   **Problem:** The heading argues against the lower score, but the section itself admits the full requirement is unmet. The quoted lower level includes an inability to correlate signals to a single request, not just missing signals. A log/trace screenshot does not close the metric-correlation problem. The appeal to the reviewer reads like score negotiation.


   **Fix, with source:** Use a neutral label such as “Lower-level wording and remaining gaps,” identify the demonstrated log/trace correlation, and state the remaining metric/privacy failures once. Retain the verbatim rubric without implying a score is ruled out. Sources: work/docs-pass/facts.md, “rubric,” Observability levels; this guide’s checklist at 489–491; owner standard requires evidence against lower-level risks, not self-grading.


   **Severity:** medium.

10. **File and location:** docs/reviewer-guide.md:122, Product specification gaps

   **Exact quote:**

   docs/reviewer-guide.md:

   > The other **38** were never groomed into the full template, including **27** already closed.



   **Problem:** “Never” is a historical assertion that the supplied audit does not establish. The audit examines current issue bodies for four headings. It cannot show that a previous body never contained them. The adjacent textual-count qualification does not repair that overclaim.


   **Fix, with source:** Say “38 issue bodies lacked at least one of the four headings at the 26 October check; 27 were closed.” Sources: docs/reviewer-guide.md:671–680, the actual groom filter; _docs/process.md:204 already uses the bounded wording. Verify revision histories before retaining any “never” claim.


   **Severity:** medium.

11. **File and location:** docs/reviewer-guide.md:158 and 180–188; _docs/process.md:45 and 105

   **Exact quote:**

   docs/reviewer-guide.md:

   > PASS, or an explicit waiver, goes to the owner with the PR summary.



   docs/reviewer-guide.md:

   > loop implement and verify until PASS or explicit waiver



   _docs/process.md:

   > Any waiver records the unmet criterion and owner's decision.



   **Problem:** The sequence makes the waiver look like an alternative outcome produced before the owner is consulted. Elsewhere the owner is the person who must grant it. Neither diagram shows the request/decision path when QA remains FAIL. This is a missing handoff at the exact point the normal approval gate changes.


   **Fix, with source:** Show FAIL → engineer fix/recheck, or orchestrator sends the unmet criterion and evidence to the owner → owner explicitly grants/rejects a waiver → record that decision before merge. Do not depict a preexisting waiver as a QA outcome. Sources: _docs/process.md:45 and 105; README.md:115 specifies owner-approved waivers.


   **Severity:** medium.

12. **File and location:** README.md:115 versus _docs/process.md:23

   **Exact quote:**

   README.md:

   > Must not groom, implement or perform QA itself



   _docs/process.md:

   > Substitute its own implementation or test result for independent QA; start the next item without the owner's pick



   **Problem:** The orchestrator’s prohibition is stronger in the README than in the process’s authoritative “Must not do” cell. The latter forbids substituting its own work for QA, but does not explicitly prohibit grooming or implementation. A reader can interpret it as allowing orchestrator implementation if someone else later checks it. The guide calls such edits overreach.


   **Fix, with source:** Make the process cell explicitly prohibit grooming, implementation and QA, matching the README; keep the historical exceptions as exceptions. Sources: README.md:115; docs/reviewer-guide.md:194; _docs/process.md:203. This is a documentation alignment, not a new role policy.


   **Severity:** medium.

13. **File and location:** _docs/process.md:58–60, Handoffs

   **Exact quote:**

   _docs/process.md:

   > | PM → Engineer | Four-section issue body and linked follow-ups | Issue body and **edited** history |



   _docs/process.md:

   > | Engineer → QA | Committed head, PR, implementation summary, commands/results | PR and issue/PR comments |



   **Problem:** The table does not say whether these arrows mean direct agent communication or merely artifact provenance. The surrounding process and README sequence say the orchestrator receives reports and briefs each next agent. For a document explaining how agents actually collaborate, that distinction matters.


   **Fix, with source:** Label the column “Artifact producer → consumer (routed by orchestrator),” or include the orchestrator in these handoffs. Sources: README.md:130–139 and 150; _docs/process.md:4–6 and 33–38. Preserve the existing artifact records.


   **Severity:** low.

14. **File and location:** _docs/process.md:30–31, Starting an agent

   **Exact quote:**

   _docs/process.md:

   > Recorded launches use `model: opus`;

   > STATE also records Fable for judgment-heavy work.



   **Problem:** “Fable” is unexplained project shorthand beside a concrete model selector. A newcomer cannot tell whether it names a model, a registered agent, a person or another session. STATE repeats the shorthand but does not make this sentence self-contained.


   **Fix, with source:** Remove the incidental Fable reference, or define what it denotes using a verifiable launch record. Do not guess a model mapping. Sources: work/STATE.md:25 and 31 record the usage but not a definition; work/docs-pass/STANDARD.md requires plain words and sourced facts.


   **Severity:** low.

15. **File and location:** _docs/process.md:18 and 24, Roles table

   **Exact quote:**

   _docs/process.md:

   > | Role | Does | Must not do |



   _docs/process.md:

   > | Owner | Sets scope and priority; approves merge and prod separately | No automated role restriction |



   **Problem:** “No automated role restriction” is neither a prohibited action nor useful information about a human owner. It puts an implementation disclaimer in a column of behavioral boundaries.


   **Fix, with source:** Use an em dash for the owner’s prohibition cell, or put any necessary statement about human authority in the Does cell. Sources: the table’s own header and work/docs-pass/STANDARD.md, “Every header matches its content.”


   **Severity:** low.

16. **File and location:** _docs/process.md:212–218, final section

   **Exact quote:**

   _docs/process.md:

   > ## Test runner — four phases



   _docs/process.md:

   > The field runner is described in [docs/testing.md](../docs/testing.md) and the

   > [field-test skill](../.claude/skills/field-test/SKILL.md).



   **Problem:** The header promises four phases, but the section names none. It contains links and caveats. As the final section of the team process it also arrives without explaining how field runs enter the owner/engineer/QA cycle.


   **Fix, with source:** Rename it “Field-test references” and give the existing authorization boundary, or summarize the four phases and identify the responsible role. Do not leave a phase-count heading over no phases. Sources: docs/testing.md:104–118 contains the actual four-phase table; work/docs-pass/STANDARD.md requires matching headers and clear handoffs.


   **Severity:** low.

17. **File and location:** _docs/process.md:161–210

   **Exact quote:**

   _docs/process.md:

   > ## Evidence it ran this way



   _docs/process.md:

   > - **CI bypassed:** PRs #31 and #138 merged with a failed integration check.



   **Problem:** “Evidence it ran this way” sounds like confirmation of the prescribed workflow. The section actually contains heading counts, mixed historical phases and substantial evidence that the prescribed workflow was bypassed. The stronger headline is not supported by the full content beneath it.


   **Fix, with source:** Use “Process records and exceptions” or “Recorded workflow and coverage.” Keep the concrete successful cycle and the exceptions under that neutral heading. Sources: this section’s own dated counts and Known gaps; work/docs-pass/STANDARD.md, matching headers, honest labels and no self-praise.


   **Severity:** low.

18. **File and location:** _docs/process.md:103, Rules

   **Exact quote:**

   _docs/process.md:

   > If a criterion is wrong, the engineer comments and waits; it does not edit the contract.



   **Problem:** “The contract” is ambiguous here. These docs also call openapi.yaml the API contract, which engineers legitimately change when implementing API work. The intended prohibition concerns issue acceptance criteria.


   **Fix, with source:** Say “does not rewrite the issue’s acceptance criteria.” Sources: _docs/team/software-engineer.md:5 and 11–12; README.md:117. Those sources express the intended boundary without overloading “contract.”


   **Severity:** low.

19. **File and location:** README.md:221–230, starting the responder

   **Exact quote:**

   README.md:

   > export RESPONDER_WEBHOOK_SECRET=local-drill-secret

   > make up-all



   README.md:

   > In another terminal, `make responder` uses the same exported secret.



   **Problem:** A new terminal does not inherit an export made in the first terminal. Following the instructions literally can therefore fail before any alert handling starts. The Make target does not load or transfer this variable, and the responder exits when it is absent.


   **Fix, with source:** Give an explicit second-terminal command that sets RESPONDER_WEBHOOK_SECRET to the same demonstration value before running make responder, or run both commands from the already-configured shell. Sources: Makefile:83–85; incident-response/responder.py:272–275. This is a concrete missing setup step, not trivial UI guidance.


   **Severity:** medium.

20. **File and location:** docs/reviewer-guide.md:589, on-call implemented sequence; README.md:230

   **Exact quote:**

   docs/reviewer-guide.md:

   > Create a local git worktree.



   README.md:

   > It launches `claude -p` in a git worktree with a $1 budget and a 300-second timeout.



   **Problem:** Neither explanation identifies the source revision for the repair worktree. The code uses the operator checkout’s HEAD, not the version returned by the health endpoint. A reviewer cannot tell whether an alert causes repair of the running build or unrelated local code. That omission is material in the section claiming to explain the implemented sequence.


   **Fix, with source:** State that the responder creates the worktree from its checkout’s HEAD and does not automatically select the deployed commit. Keep publication/deployment as the existing separate human step. Source: incident-response/responder.py:127–133, specifically the git worktree add arguments ending in HEAD; the evidence collector separately reads health and recent local commits.


   **Severity:** medium.

21. **File and location:** README.md:40 and 232 versus docs/reviewer-guide.md:578, 590, 595 and 626

   **Exact quote:**

   README.md:

   > alert to fix took 4 min 52 s.



   README.md:

   > This proves the alert-to-fix drill, not diagnosis of an unlabelled production fault.



   docs/reviewer-guide.md:

   > **4 min 52 s** to a commit, not to recovery.



   docs/reviewer-guide.md:

   > No successful post-fix search or resolved alert is recorded.



   **Problem:** The README’s headline metric is “alert to fix,” while the guide carefully limits the same interval to a code commit. In an on-call explanation, “fix” can mean restored service. Here the faulty image was not replaced by the responder and no successful recovery is recorded. The wording becomes less trustworthy when the guide later narrows it.


   **Fix, with source:** Use “alert to repair commit: 4 min 52 s” in the README and describe the demonstrated result as alert-triggered code repair. Retain the single recovery limitation in the on-call section. Sources: the guide’s own timeline/recovery statements; incident-response/responder.py:148–185 has launch, verdict copy and worktree cleanup but no deployment/recovery step.


   **Severity:** medium.

22. **File and location:** docs/reviewer-guide.md:728–733, Local privacy check

   **Exact quote:**

   docs/reviewer-guide.md:

   > Substitute your local app port.



   docs/reviewer-guide.md:

   > docker logs --since 5m projectone-app-1 2>&1 | grep 'docs-quality-invalid-probe'



   **Problem:** The reproduction adapts the port but hardcodes the author’s Compose container name. A fresh clone/worktree need not create projectone-app-1, so the central log check can fail against the wrong container name. That is a trust problem in evidence offered to verify a privacy gap.


   **Fix, with source:** Use docker compose logs --since 5m app from the same Compose project that started the app, and mention any project/override flags must match the startup command. Sources: docker-compose.yml defines service app but no fixed project/container name; Makefile:78–81 shows the observability startup invocation. Do not present one machine’s generated container name as a portable check.


   **Severity:** medium.

FAIL
