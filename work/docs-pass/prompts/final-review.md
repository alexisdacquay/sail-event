You are the final reviewer of the reviewer-facing docs of Sail-event, before they are merged and peer reviewers read them today. Work read-only in the git worktree /private/tmp/claude-503/-Users-ad-code-ProjectOne/88df4b5e-b416-4a37-ba3b-18ed01c2a6a0/scratchpad/wt-dq (branch docs-quality). Do not edit any file except your report. Do not commit. Do not register, log in or search on the live sites; GETs are fine.

Read first:
- work/docs-pass/STANDARD.md: the owner's standard. Apply all of it, especially "Honest, not defensive".
- work/docs-pass/facts.md, section "rubric": the full rubric, verbatim.

Then read completely, as an experienced engineer peer-reviewing with 10 minutes and no context: README.md, then docs/reviewer-guide.md, then _docs/process.md, then AGENTS.md.

Judge, and report every failure:
1. English and sense: every sentence makes sense; every header matches its content; no insider shorthand left unexplained.
2. Tone: confident and factual.
   - No patronising explanation of the trivial.
   - No marketing.
   - No defensive hedging; each limitation stated once.
   - No bold disclaimers at the top.
   - No internal context leaked to reviewers, e.g. "the owner asked" or "orchestrator added".
3. Facts: spot-check at least 15 claims (numbers, dates, commits, issue and PR numbers, commands) by running the command. Report anything wrong, invented or stale.
4. Rubric: for each of the 12 criteria, can a reviewer tick every atomic phrase of the full-marks text in the guide within a minute? Are the checklist rows the rubric's words, verbatim? Is the README table enough to get there?
5. Length and flow:
   - Is the README readable in about 5 minutes?
   - Is anything in the wrong place?
   - Would you stop reading anywhere?
6. Honesty: are the known gaps complete, and stated plainly? Is any strength buried?

Write work/docs-pass/out/final-review.md as a numbered list. Each item gives:
- file:line;
- the exact quote;
- the problem;
- the fix;
- severity: high, medium or low.

End with one line: PASS (no high or medium issues) or FAIL. Return that last line as your final answer.
