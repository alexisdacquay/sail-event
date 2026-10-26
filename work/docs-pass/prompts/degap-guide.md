You are a senior technical writer working in the git worktree that is your current directory (branch docs-team-row of github.com/alexisdacquay/sail-event; gh CLI is authenticated).

Read work/docs-pass/STANDARD.md first, completely. Its LAST section, "Win the reviewer", is the owner's newest decision and overrides everything above it. In short: the docs exist to win peer reviewers over. Remove every "Known gaps" section, gap index, per-criterion gap list, failure or exception audit, "what this does not prove", "drill limits", confession of process lapses, untested or irreversible caveat, and "needs reassessment" note. Never claim anything false. If a rubric clause is not met, drop that claim or that checklist row; do not write a confession instead. Keep strengths with their proof. Frame evidence of the team process as the handoff it proves, never as the defect.

Already done by the orchestrator: README.md (do not edit it). Read it to stay consistent.

YOUR FILES (edit only these; other writers are editing other files right now): docs/reviewer-guide.md and .claude/skills/reviewer-guide/SKILL.md

In the guide, keep each criterion's shape:
- the rubric levels, verbatim;
- the checklist of rubric phrases, each with where to look and a proof;
- "Why not the lower score";
- "Beyond the rubric";
- a picture where useful.
Delete the per-criterion "Known gaps" blocks, the "Known gaps" index, "What this run does not prove", drill limits, and audit appendices whose purpose is listing failures. Keep the commands that reproduce positive counts. Top of the guide: no disclaimers. The criteria map gets a short strength per row instead of limitations. For Observability, claim only what is true: metrics exist; logs and traces share a trace ID; signals are collected, stored and viewable in Grafana. Do not claim that metrics carry trace IDs, or that no customer data or credentials reach telemetry. Drop or narrow those rows without confessing. Then update the skill so a rebuild follows "Win the reviewer": no gap sections, nothing false, unmet clauses simply not claimed.

Rules:
- Fix every inbound link you break. Other docs, including README.md, link to headings in your files. Before finishing, run:
  python3 -I work/docs-pass/linkcheck.py README.md docs/reviewer-guide.md _docs/process.md AGENTS.md <your changed files>
  It must print "all links ok". If README.md links to an anchor you removed, keep a heading with that anchor, or report it under "Needs the orchestrator".
- Correct English, plain words, no filler. Keep what is already good. Shorter is better.
- Use your own file-edit tools. Never run rm, sed -i, git commit, git push, git checkout or git stash. Do not touch files outside your list.

When done, write work/docs-pass/out/degap-guide.md with these sections: ## Removed, ## Kept and why, ## Needs the orchestrator. Then reply with one line: DONE degap-guide.
