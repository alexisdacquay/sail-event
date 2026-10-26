You work in the git worktree that is your current directory (branch docs-quality of github.com/alexisdacquay/sail-event; gh CLI is authenticated). Read work/docs-pass/STANDARD.md first: it is the owner's standard and it is non-negotiable.

The docs were rewritten, then three blind checkers reviewed them. Their reports are:
- work/docs-pass/out/verify-reader.md
- work/docs-pass/out/verify-facts.md
- work/docs-pass/out/verify-rubric.md
- work/docs-pass/out/orchestrator-review.md (the orchestrator's own read; treat it as authoritative on tone and structure)
If it exists, also work/docs-pass/out/final-review.md.

YOUR FILES (edit only these; other fixers are editing the other docs right now): docs/reviewer-guide.md and .claude/skills/reviewer-guide/SKILL.md

YOUR JOB
- Fix every issue in those reports that concerns your files. Verify each one first: run the command. Reject an issue you can disprove, with the evidence.
- If an issue in another file needs a change in yours (a link, an anchor, a contradiction), fix your side.
- Then re-read your files once, end to end, for sense, correct English and the standard.
- The original writer's brief, for context:
Give every criterion the same fixed shape:
(a) the rubric's levels, quoted verbatim with points;
(b) a checklist whose first column holds the full-marks text split into its atomic phrases, verbatim and in rubric order (the list is in facts.md, section rubric); each row has where to look and a proof checkable in under a minute;
(c) why it is not the lower score: quote the lower level's exact wording and show what closes it;
(d) beyond the rubric: extras the repo can prove;
(e) a picture, only where one helps;
(f) known gaps for that criterion, honest and complete.
Keep the '## N. Name' headings exactly as they are (README links to them). Fix the top of the guide: no stale pin and no stale sha in the 5-minute check. Fix the Known gaps section and make it complete. Fix the 5-minute check. Then update the skill so the next rebuild follows STANDARD.md: the audience, nothing invented, the rubric phrases verbatim, careful explanation only for the complex scored parts, drills labelled as drills, no stale numbers without a command.

- Use your own file-edit tools. Never run rm, sed -i, git commit, git push, git checkout or git stash. Do not touch files outside your list.
- After editing, run: python3 -I work/docs-pass/linkcheck.py <your changed .md files> README.md docs/reviewer-guide.md. Fix every broken link on your side.

When done, write work/docs-pass/out/fix-guide.md with: ## Fixed (one line each), ## Rejected (issue, reason, evidence), ## Needs the owner. Then reply with one line: DONE fix-guide.
