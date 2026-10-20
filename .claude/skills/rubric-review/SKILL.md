---
name: rubric-review
description: Blind peer-review scoring of this repository against the Zoomcamp rubric, from three reviewer profiles that see only the public repo and the live URL. Use before a release, after a README change, or when the owner asks "how would reviewers score this"; append the result to work/RUBRIC-REVIEWS.md and turn gaps into issues.
---

# Rubric review

Three reviewers who have never seen the project score it independently; their agreement is the score, their disagreement is the gap list. Never score it yourself from inside the session: you know too much.

## Rubric (12 criteria, 24 points, pass 10)

1 Problem description (2) · 2 Product spec + public task tracker with acceptance criteria, agents used it (2) · 3 Agent team: roles + process (2) · 4 Context: AGENTS.md pointing to modular docs (2) · 5 Application: frontend + backend + DB, single local command (2) · 6 Testing: unit + integration, single command (2) · 7 Containerization incl. DB, single command (2) · 8 Deployment: public URL or clear demo (2) · 9 CI/CD: CI on PR, CD, manual prod promotion (3) · 10 Observability: one journey with metrics, traces and logs sharing a trace id, and a UI (2) · 11 Alert (1) · 12 On-call agent fixes on alert (2).

## Run

Launch three agents in parallel (Opus, background), each with a fresh `git clone https://github.com/alexisdacquay/sail-event` into its own scratch folder and nothing from the session. Each gets the rubric above and one profile:

- **A, strict grader**: grades only what it can verify with a path, a command or a URL; may use `gh` read-only and the live API with a throwaway user `peer_a_<random>`; no docker. Output: table `# | criterion | score | evidence | what would raise it`, total, "Top 3 risks for a stranger", "What impressed".
- **B, fifteen-minute reviewer**: README top to bottom, at most six links, repo page, live health; a point not reachable in two clicks is not earned; at most 15 tool calls. Output: table `# | criterion | score | where the README sent me | what would raise it`, total, "Where I got lost", "What convinced me fastest".
- **C, hands-on runner**: follows the README commands literally with `COMPOSE_PROJECT_NAME=peer-c HOST_PORT=8040` (8000, 8010, 8030, 3000, 3001, 9090 are taken on this machine), runs the app, the tests, the containers, one real search locally and on the live URL, tears everything down. Output: table `# | criterion | score | command I ran and what happened | what would raise it`, total, "Commands from the README that did not work as written", "Time from clone to a working search".

Machine rules in every brief: never `rm`, `sed -i`, `cd ... && ...`; absolute paths; no sub-agents; no dev-server launcher; never print secrets; no edits.

## Merge

Per criterion: the score is the minimum of the three (a stranger who misses the point is the one who grades you). Every "what would raise it" and every failed README command becomes a line in the gap list, ranked by points at stake then by how many reviewers hit it. File one issue per gap that costs a point or breaks a README command; note the rest in the log.

## Log

Append one block to `work/RUBRIC-REVIEWS.md`:

```
## <date> <main sha> — A <n>/24 · B <n>/24 · C <n>/24 · merged <n>/24
| # | A | B | C | min | gap |
...
risks: ...
failed commands: ...
issues filed: #...
```

Re-run after the gap issues close; the next block shows the movement.
