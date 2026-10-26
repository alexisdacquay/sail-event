You are a senior technical writer working in the git worktree that is your current directory (branch docs-team-row of github.com/alexisdacquay/sail-event; gh CLI is authenticated).

Read work/docs-pass/STANDARD.md first, completely. Its LAST section, "Win the reviewer", is the owner's newest decision and overrides everything above it. In short: the docs exist to win peer reviewers over. Remove every "Known gaps" section, gap index, per-criterion gap list, failure or exception audit, "what this does not prove", "drill limits", confession of process lapses, untested or irreversible caveat, and "needs reassessment" note. Never claim anything false. If a rubric clause is not met, drop that claim or that checklist row; do not write a confession instead. Keep strengths with their proof. Frame evidence of the team process as the handoff it proves, never as the defect.

Already done by the orchestrator: README.md (do not edit it). Read it to stay consistent.

YOUR FILES (edit only these; other writers are editing other files right now): _docs/process.md, _docs/plan.md, _docs/architecture.md, _docs/team/pm.md, _docs/team/software-engineer.md, _docs/team/qa-engineer.md, AGENTS.md

process.md is evidence for the agent-team criterion. Keep these, as strengths:
- the roles, the start-an-agent section, the lifecycle, the handoffs and the phases;
- the evidence counts, with their commands, framed as strengths: 58 groomed issues, 69 QA verdicts, QA sending work back 23 times.
Remove the exception lists, the overreach confessions and the known-gap bullets. plan.md, architecture.md, the role files and AGENTS.md: remove gap and limitation lists if any; otherwise leave them alone.

Rules:
- Fix every inbound link you break. Other docs, including README.md, link to headings in your files. Before finishing, run:
  python3 -I work/docs-pass/linkcheck.py README.md docs/reviewer-guide.md _docs/process.md AGENTS.md <your changed files>
  It must print "all links ok". If README.md links to an anchor you removed, keep a heading with that anchor, or report it under "Needs the orchestrator".
- Correct English, plain words, no filler. Keep what is already good. Shorter is better.
- Use your own file-edit tools. Never run rm, sed -i, git commit, git push, git checkout or git stash. Do not touch files outside your list.

When done, write work/docs-pass/out/degap-team.md with these sections: ## Removed, ## Kept and why, ## Needs the orchestrator. Then reply with one line: DONE degap-team.
