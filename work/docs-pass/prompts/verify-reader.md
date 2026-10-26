You work in the git worktree that is your current directory (branch docs-quality of github.com/alexisdacquay/sail-event; gh CLI is authenticated). The reviewer-facing docs were just rewritten on this branch. Read work/docs-pass/STANDARD.md first: it is the owner's standard. The full rubric, verbatim, is in work/docs-pass/facts.md, section "rubric".

You are READ-ONLY on the docs. Do not edit any file except your report. Never run rm, sed -i, git commit, git push, git checkout or git stash. Do not register, log in or search on the live sites; GETs are fine.

You have never seen this repo. Read README.md, then docs/reviewer-guide.md, then _docs/process.md, completely, as a senior engineer or exec peer-reviewing a course project with 10 minutes. Be harsh. Report:
- anything that does not make sense or is bad English;
- any header that does not match its content;
- anything written for children, or that explains the trivial;
- anything that sounds like marketing or self-grading;
- anything unclear in the agent-team, process, context, CI/CD, observability, alerting or on-call explanations;
- anything that contradicts itself across the three files;
- any place where you would stop trusting the docs.
Write your report to work/docs-pass/out/verify-reader.md. Use one numbered item per issue:
- file and location;
- the exact quote;
- the problem;
- the fix, with its source;
- severity: high, medium or low.
End the report with a one-line verdict: PASS (nothing high or medium) or FAIL. Then reply with one line: DONE verify-reader.
