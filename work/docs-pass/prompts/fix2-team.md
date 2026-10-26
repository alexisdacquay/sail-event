You work in the git worktree that is your current directory (branch docs-quality of github.com/alexisdacquay/sail-event; gh CLI is authenticated). Read work/docs-pass/STANDARD.md first: it is the owner's standard and it is non-negotiable.

The docs were rewritten, then three blind checkers reviewed them. Their reports are:
- work/docs-pass/out/verify-reader.md
- work/docs-pass/out/verify-facts.md
- work/docs-pass/out/verify-rubric.md
- work/docs-pass/out/orchestrator-review.md (the orchestrator's own read; treat it as authoritative on tone and structure)
If it exists, also work/docs-pass/out/final-review.md.

YOUR FILES (edit only these; other fixers are editing the other docs right now): everything under _docs/ (only files that need it), AGENTS.md, .claude/agents/qa-engineer.md

YOUR JOB
- THIS ROUND (round 2): the earlier reports are already handled. Fix the issues in work/docs-pass/out/final-review.md only. Count-type claims must be bounded so they cannot drift: e.g. limit PR counts to PRs up to #152 and say so, and make `git log -S` verify commands immune to work/wip commits, e.g. by filtering to the role-file commits or by naming the commit directly.
- Fix every issue in those reports that concerns your files. Verify each one first: run the command. Reject an issue you can disprove, with the evidence.
- If an issue in another file needs a change in yours (a link, an anchor, a contradiction), fix your side.
- Then re-read your files once, end to end, for sense, correct English and the standard.
- The original writer's brief, for context:
_docs/process.md must let an outsider understand the agent team and process in 2 minutes: who the roles are; what each does and never does; how each agent is started and what context it gets (role file, issue, brief, AGENTS.md); how work moves; the handoffs; how to check that it happened (commands); and the honest gaps, with dates when rules started. _docs/plan.md: fix the invented and incorrect Problem text, the stale anchors and the wrong facts. _docs/architecture.md: fix the stale data model and the wrong facts. Do not churn files that have no defects. AGENTS.md is the context file other agents load: keep it accurate and short, and keep its links working.

- Use your own file-edit tools. Never run rm, sed -i, git commit, git push, git checkout or git stash. Do not touch files outside your list.
- After editing, run: python3 -I work/docs-pass/linkcheck.py <your changed .md files> README.md docs/reviewer-guide.md. Fix every broken link on your side.

When done, write work/docs-pass/out/fix2-team.md with: ## Fixed (one line each), ## Rejected (issue, reason, evidence), ## Needs the owner. Then reply with one line: DONE fix2-team.
