You work in the git worktree that is your current directory (branch docs-quality of github.com/alexisdacquay/sail-event; gh CLI is authenticated). The reviewer-facing docs were just rewritten on this branch. Read work/docs-pass/STANDARD.md first: it is the owner's standard. The full rubric, verbatim, is in work/docs-pass/facts.md, section "rubric".

You are READ-ONLY on the docs. Do not edit any file except your report. Never run rm, sed -i, git commit, git push, git checkout or git stash. Do not register, log in or search on the live sites; GETs are fine.

Fact and link check of everything this branch changed.
1) Run: python3 -I work/docs-pass/linkcheck.py $(git diff --name-only origin/main -- '*.md' | grep -v '^work/') README.md docs/reviewer-guide.md AGENTS.md. Report every broken link.
2) Read `git diff origin/main -- '*.md' ':!work'`. For every number, count, date, duration, commit, issue or PR number, CI run, file path, command, env var and URL in an added or changed line, run the command that proves or disproves it (git, gh, grep, ls, curl GET). Report every claim that is wrong, unverifiable, invented, stale (it will change on the next commit or deploy with no command given), or that contradicts another doc. You may spot-check unchanged lines too.
Write your report to work/docs-pass/out/verify-facts.md. Use one numbered item per issue:
- file and location;
- the exact quote;
- the problem;
- the fix, with its source;
- severity: high, medium or low.
End the report with a one-line verdict: PASS (nothing high or medium) or FAIL. Then reply with one line: DONE verify-facts.
