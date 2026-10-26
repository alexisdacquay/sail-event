You work in the git worktree that is your current directory (branch docs-quality of github.com/alexisdacquay/sail-event; gh CLI is authenticated). The reviewer-facing docs were just rewritten on this branch. Read work/docs-pass/STANDARD.md first: it is the owner's standard. The full rubric, verbatim, is in work/docs-pass/facts.md, section "rubric".

You are READ-ONLY on the docs. Do not edit any file except your report. Never run rm, sed -i, git commit, git push, git checkout or git stash. Do not register, log in or search on the live sites; GETs are fine.

Blind peer reviewer. Start from README.md only, as a reviewer would. Use the rubric verbatim from facts.md. For each of the 12 criteria:
- find the evidence the docs point to and check it (open the file, run the command, GET the URL);
- give the score you would give, with a one-line reason;
- report as issues: any atomic phrase of the full-marks text you could not tick within one minute, any proof that did not hold, anything that would push you to the lower score, and anything unclear;
- check that the guide's checklist rows are the rubric's words verbatim.
Start the report with a 12-row score table.
Write your report to work/docs-pass/out/verify-rubric.md. Use one numbered item per issue:
- file and location;
- the exact quote;
- the problem;
- the fix, with its source;
- severity: high, medium or low.
End the report with a one-line verdict: PASS (nothing high or medium) or FAIL. Then reply with one line: DONE verify-rubric.
