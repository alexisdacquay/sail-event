# Orchestrator review of the rewrite (12:45 UTC)

I read README.md in full and docs/reviewer-guide.md through §3. The rewrite is accurate and honest, and the guide now has the shape the owner asked for. It fails the "Honest, not defensive" section of STANDARD.md: it reads like an audit report, and it buries the strengths. Fix the issues below and look for the same patterns everywhere else.

## Both files

1. Remove the bold disclaimers at the top: README line 25 and guide line 5. The local scope of observability, alerting and on-call is stated once, in those sections, in one sentence.
2. Never leak internal context to reviewers. Guide line 140, "requested by the owner", must go; reviewers do not know or care who asked for a structure. The same goes for "orchestrator added", "the owner's standard" and similar wording in reviewer-facing text.
3. Remove defensive hedges. Each limitation is stated once, where it matters. Examples to cut or rewrite:
   - README:
     - "Those measurements are not a Render benchmark."
     - "it is not a claim about all earlier work"
     - "These counts measure headings, not complete adherence to the process."
     - "It does not establish that every commit was tested."
     - "Dev's configured clock is an environment setting; the repository alone cannot establish its live value."
   - Guide:
     - "an evidence pin, not a claim about the deployed version"
     - "This is evidence for the workflow, not a claim that every item followed it."
     - "These are textual counts, not a quality verdict."
     - "A missing PR verdict alone does not prove there was none on its issue."
     - "The checklist checks those distinctions rather than the length of the prose."

## README.md (target: readable in about 5 minutes; now 3,300 words)

4. Line 11: drop the button trivia ("after a run, the button reads Search again").
5. Line 13: one sentence, e.g. "A live search takes a few minutes (86–493 s measured in PR #144)."
6. Line 50:
   - "The app parses criteria" is wrong. It sends the criteria text, plus the word "event", to the web search.
   - "Code screens out missing start dates or times" is bad English. Write "drops events that lack …".
7. Line 60: drop the widget-label inconsistency sentences, which are UI trivia. If the inclusive cutoff matters, it is already in the table.
8. Lines 62–68 (schedule): cut to one or two sentences and link the guide's schedule measurement. The `MAX_SCHEDULED_USERS` detail belongs in the guide or docs.
9. Lines 226–234 (observability, alerts, responder): keep what a reviewer needs to understand and run it:
   - what is instrumented and where it shows;
   - the two alert rules in plain words;
   - the alert → webhook → evidence → headless Claude Code in a worktree → fix branch or verdict chain, with its limits ($1, 300 s, no push);
   - the drill timings.
   PromQL internals, `noDataState` and the allowlist detail go to the guide or to observability/README.md.
10. Known gaps: keep it, but tighter: one line per gap, with a link to the guide for detail.

## docs/reviewer-guide.md

11. §2 Known gaps: summarise in 2–3 bullets (counts plus a link to [Tracker audit](#tracker-audit)). The lists of issue and PR numbers belong in the Tracker audit section.
12. Apply the same in every section: Known gaps per criterion are short; exhaustive lists go to the Evidence commands appendix.
13. Keep the rubric levels and the checklist shape exactly. They are right.

## _docs/process.md (read through "One cycle in one picture")

14. The Roles and Handoffs tables are good. Keep them.
15. The prose is telegraphic and uses insider shorthand. Write full sentences for an outsider. Examples:
   - "STATE also records Fable for judgment-heavy work." Readers don't know what STATE or Fable are.
   - "worktree/head".
   - "PM also reads this process, the task template, plan, architecture, contract and code".
   Explain once what a worktree and a "head" are, or use plain words: "its own copy of the repo on a separate branch" and "the exact commit QA checked".
16. Move the rollback and migration paragraph out of Lifecycle. It belongs in docs/release-process.md (the ops fixer owns it). Keep at most one line in this file's gaps.
17. "the original 2026-10-16 process ran an unattended backlog loop" is fine. Add one plain sentence on what changed on 2026-10-21 and why: the owner picks every item and approves every prod promote.
