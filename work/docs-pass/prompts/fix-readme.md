You work in the git worktree that is your current directory (branch docs-quality of github.com/alexisdacquay/sail-event; gh CLI is authenticated). Read work/docs-pass/STANDARD.md first: it is the owner's standard and it is non-negotiable.

The docs were rewritten, then three blind checkers reviewed them. Their reports are:
- work/docs-pass/out/verify-reader.md
- work/docs-pass/out/verify-facts.md
- work/docs-pass/out/verify-rubric.md
If it exists, also work/docs-pass/out/final-review.md.

YOUR FILES (edit only these; other fixers are editing the other docs right now): README.md

YOUR JOB
- Fix every issue in those reports that concerns your files. Verify each one first: run the command. Reject an issue you can disprove, with the evidence.
- If an issue in another file needs a change in yours (a link, an anchor, a contradiction), fix your side.
- Then re-read your files once, end to end, for sense, correct English and the standard.
- The original writer's brief, for context:
README.md is the first screen for every reviewer. Aim for this structure:
- what Sail-event is, in 1-2 accurate sentences, no hype;
- the screenshot;
- how to try it live;
- a reviewer table: criterion, where to look, and evidence checkable fast; no points column;
- then the rest.
The product part must be short and written for adults: a precise Problem (use the pre-PR-152 README's accurate wording as a base: no single source lists small events, aggregators only collect what you already know, a search gives pages not checked events in your calendar), what it does, and expected behaviour. The complex scored parts get the clear diagrams and steps: the agent team (all roles including the orchestrator, the PR, CI and the owner's merge and promote words), context management (how an agent gets its context: AGENTS.md then modular docs, plus the brief the orchestrator writes), CI/CD and promotion, and observability, alerting and on-call (local stack, drills). Every link must resolve. Anchors into docs/reviewer-guide.md use its '## N. Name' headings, which the guide writer keeps unchanged.

- Use your own file-edit tools. Never run rm, sed -i, git commit, git push, git checkout or git stash. Do not touch files outside your list.
- After editing, run: python3 -I work/docs-pass/linkcheck.py <your changed .md files> README.md docs/reviewer-guide.md. Fix every broken link on your side.

When done, write work/docs-pass/out/fix-readme.md with: ## Fixed (one line each), ## Rejected (issue, reason, evidence), ## Needs the owner. Then reply with one line: DONE fix-readme.
