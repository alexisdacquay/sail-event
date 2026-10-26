You work in the git worktree that is your current directory (branch docs-quality of github.com/alexisdacquay/sail-event; gh CLI is authenticated). Read work/docs-pass/STANDARD.md first: it is the owner's standard and it is non-negotiable.

The docs were rewritten, then three blind checkers reviewed them. Their reports are:
- work/docs-pass/out/verify-reader.md
- work/docs-pass/out/verify-facts.md
- work/docs-pass/out/verify-rubric.md
- work/docs-pass/out/orchestrator-review.md (the orchestrator's own read; treat it as authoritative on tone and structure)
If it exists, also work/docs-pass/out/final-review.md.

YOUR FILES (edit only these; other fixers are editing the other docs right now): docs/*.md except docs/reviewer-guide.md, observability/README.md, incident-response/README.md

YOUR JOB
- Fix every issue in those reports that concerns your files. Verify each one first: run the command. Reject an issue you can disprove, with the evidence.
- If an issue in another file needs a change in yours (a link, an anchor, a contradiction), fix your side.
- Then re-read your files once, end to end, for sense, correct English and the standard.
- The original writer's brief, for context:
docs/deployment.md and docs/release-process.md were already partly rewritten by an earlier writer: review those edits critically, keep what is right, fix the rest. CI/CD, observability, alerting and on-call must be clear to an outsider, with drills labelled as drills and the local-only scope stated up front. docs/ai-usage-report.md is a dated report (written 2026-10-16, covering issues #1-#26): add a short dated scope note, and fix the places where 'orchestrator' now contradicts process.md. Do not churn files that have no defects. Findings about images: report them under Needs the owner, or fix the caption in a file you own; never edit an image.

- Use your own file-edit tools. Never run rm, sed -i, git commit, git push, git checkout or git stash. Do not touch files outside your list.
- After editing, run: python3 -I work/docs-pass/linkcheck.py <your changed .md files> README.md docs/reviewer-guide.md. Fix every broken link on your side.

When done, write work/docs-pass/out/fix-ops.md with: ## Fixed (one line each), ## Rejected (issue, reason, evidence), ## Needs the owner. Then reply with one line: DONE fix-ops.
