# Docs quality standard (owner, 2026-10-26)

Every writer and reviewer in this pass applies this. It is the owner's standard, not a style suggestion.

## Context

- Sail-event is the final project of the DataTalksClub AI Dev Tools Zoomcamp 2026. Peers score it against a 12-criterion rubric (full text in `work/docs-pass/facts.md`, section `rubric`). They read `README.md` and `docs/reviewer-guide.md` first.
- The owner calls the docs the most important part of the project.
- Live sites: prod <https://sail-event.onrender.com> runs an OLD commit (969a161). Dev <https://sail-event-dev.onrender.com> runs main. **The owner will promote prod to the final docs commit before submission**, so write for main. Do not add "prod is older" caveats. Report a prod mismatch only if it would still exist after the promote.
- The README before PR 152 is `git show 'ac54483^:README.md'`. Its product wording was more accurate.
- Change freeze: docs only, no code changes.

## Audience and tone

- Readers are experienced engineers and execs: busy, short attention span, not novices.
- Never explain the trivial: typing a sentence in a box, what a web search is, clicking Register. Never sell a trivial thing as a feature or a goal.
- Give careful, step-by-step explanations only for the complex parts that are scored and that nobody can guess from outside:
  - how the agent team works: who, what each role does and never does, how an agent is started and what context it gets;
  - the process and its handoffs;
  - context management;
  - CI/CD and promotion;
  - observability, alerting and the on-call agent.
- Bare minimum: correct English that makes sense. Every header matches its content: no "Who" over a column of jobs. No checklist column called "Rubric words" unless the rows really are the rubric's words.
- Nothing contradicts the real world. Example: "users cannot type what they mean" ignores search engines. The real gap is that a search returns pages, not checked events in your calendar, and you have to repeat it every day.
- Plain words, short sentences, no filler, no marketing, no self-praise.

## Facts

- Invent nothing. Every number, date, count, commit, duration and claim traces to a source you can show: a file, git, gh, a CI run or an HTTP GET. If a claim has no source, verify it or remove it.
- Facts that go stale on the next commit or deploy: avoid hard-coded shas, test counts and "current main is X". If a number stays, give the command that reproduces it, or label it "at commit X, date".
- Honest labels. A drill with an injected fault is a drill, never "fired for real". A rollback that was never run is "untested". A rule introduced on a date is dated.
- Known gaps stay visible, and the list is complete. A reviewer who finds an undisclosed gap distrusts everything else. Disclose plainly and briefly, without grovelling, and keep the real strengths visible.

## Rubric presentation

- The README does not grade itself: no points column, no "Max", no "Total 24", no "Pass is 10".
- The reviewer guide may quote the rubric's levels and points, verbatim.
- For each criterion, the guide splits the full-marks text into its atomic phrases, verbatim and in order, so a reviewer can tick them one by one. Each phrase gets where to look and a proof checkable in under a minute.
- The guide also names the lower-level wording and shows what closes that risk, and lists extras beyond the rubric that the repo can prove.
- The owner's own example, Agent Team Specification:
  - Levels: "No agent team described (0)", "Roles or agents are mentioned, but responsibilities are unclear (1)", "The project defines the agent team and process of how they work together (2)".
  - A reviewer ticks: roles mentioned; responsibilities clear (and why we are not at the 1-point "unclear" level); team defined; process defined; how they work together; extras.

## Safety

- Never print secrets or `.env` files.
- Do not register accounts, log in, or run searches on prod or dev; it costs money. Plain HTTP GETs are fine.
- No `rm`, no `sed -i` on tracked files, no `git commit`, no `git push`. The orchestrator commits.
