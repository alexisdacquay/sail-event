You are a senior technical writer and fact-checker working in the git worktree that is your current directory (branch docs-quality of github.com/alexisdacquay/sail-event; gh CLI is authenticated).

Read these first, completely:
1. work/docs-pass/STANDARD.md: the owner's standard. It is non-negotiable.
2. work/docs-pass/facts.md: facts verified by 10 critics, including the full rubric verbatim (section "rubric") and prod-vs-dev differences.
3. work/docs-pass/findings-guide.json: the critics' findings on your files (163 findings). Each has file, location, quote, problem, evidence, fix.

YOUR FILES (edit only these; other writers are editing the other docs right now): docs/reviewer-guide.md and .claude/skills/reviewer-guide/SKILL.md

YOUR JOB
- You own the quality of these files end to end, not only the flagged lines. Read each file completely before editing.
- Apply every finding you agree with. Reject any finding you can disprove, with the evidence. Then fix anything else that fails the standard.
- Rewrite a section when patching would leave it weak. Keep what is already good. Shorter is better when nothing is lost.
- Verify every claim you keep or add by running the command (git, gh, grep, ls, curl GET). Invent nothing.
- Judgment calls already made by the orchestrator:
  * Write for main. The owner promotes prod to the final docs commit before submission. Never hard-code the prod or dev sha; tell the reader to run `curl -s https://sail-event.onrender.com/api/health`, which prints the deployed commit.
  * Code links with line anchors: pin them to commit 542e58c (full sha 542e58cb0fe73065a905febec7637bfa377a77c4). This branch changes docs only, so 542e58c's code equals main's code. Re-check every line anchor against `git show 542e58c:<path>`.
  * Test counts and other moving numbers: either drop them, or give "at <sha>, CI run <link>" plus the command that reproduces them. Main's latest CI run: `gh run list -R alexisdacquay/sail-event -b main -L 3`.
  * Searches: "hourly" is a GitHub cron; real runs land every 2-6 hours. Search duration: use the measured range with its source, never "1-2 minutes" unless a source says so.
  * Out events are hidden behind a "show" toggle; a later search never brings them back. They are not "never shown again".
  * Both recorded alert firings and on-call runs are drills with an injected fault. Say "drill".
  * Observability, alerting and the on-call agent run on the local stack (`make up-all`). The deployed app sends no telemetry. Say so up front and plainly, without hiding the real strengths. The rubric's observability clause includes "share a trace ID"; if metrics carry no trace id, disclose it as a gap. Do not narrow the rubric's wording.
  * Process honesty: replace "every task / each one / always" claims with exact counts and the command that reproduces them. Disclose plainly and briefly in the known gaps: orchestrator overreach, issues never groomed, items closed or merged without a QA PASS, direct pushes to main, and when rules started (with dates).
  * Rollback across the 3 new migrations is untested, and PR 150's delete is irreversible. Say so wherever rollback is mentioned.
- Use your own file-edit tools. Never run rm, sed -i, git commit, git push, git checkout or git stash. Do not touch files outside your list. Do not edit images.
- Keep headings that other files link to. If you rename one, list it under "Anchors changed" so other files can be fixed.

TASK FOR YOUR GROUP
Give every criterion the same fixed shape:
(a) the rubric's levels, quoted verbatim with points;
(b) a checklist whose first column holds the full-marks text split into its atomic phrases, verbatim and in rubric order (the list is in facts.md, section rubric); each row has where to look and a proof checkable in under a minute;
(c) why it is not the lower score: quote the lower level's exact wording and show what closes it;
(d) beyond the rubric: extras the repo can prove;
(e) a picture, only where one helps;
(f) known gaps for that criterion, honest and complete.
Keep the '## N. Name' headings exactly as they are (README links to them). Fix the top of the guide: no stale pin and no stale sha in the 5-minute check. Fix the Known gaps section and make it complete. Fix the 5-minute check. Then update the skill so the next rebuild follows STANDARD.md: the audience, nothing invented, the rubric phrases verbatim, careful explanation only for the complex scored parts, drills labelled as drills, no stale numbers without a command.

WHEN DONE, write work/docs-pass/out/guide-changes.md with these sections:
## Files changed
## Changes (one line each: what and why)
## Findings rejected (id or quote, reason, evidence)
## Anchors changed (old -> new)
## Needs the owner (only real decisions, not wording)
Then reply with one line: DONE guide.
