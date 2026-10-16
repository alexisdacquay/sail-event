# METHOD — lesson 1, as written (read 2026-10-15)

Sources: article "AI-Native Development: Specifications, Loop and Graph Engineering"
(aishippingblog.com/p/ai-native-development-specifications); retroloop repo
(AGENTS.md, _docs/process.md, task-template.md, team/*.md, outdated/plan.md,
tasks.md, architecture.md); weekly-feedback (the cautionary example).

Principle: "We no longer spend most of our time typing. We spend it saying
precisely what we want and checking what came back."

## Step 1 — brainstorm in chat (spec before code)
Prompt, verbatim:
```
I want to build <vague idea>.

Help me set the scope for this project precisely. I want to brainstorm with you
and understand how the tool should work. Give me options.

Ask me one question at a time and keep your output short.
```
Rules for me in this step: one question per message, options offered, short.
Example questions from the article: who contributes? what format? anonymous?
what can people see? how is X revealed? what happens next? what is recorded?
what is NOT in the first version?
End with:
```
Save everything to a markdown file that I can download.
```
-> _docs/plan.md. Its shape (retroloop): Product goal / Core workflow numbered
steps / "Decisions made for the MVP": each = Decision, Why, Alternatives considered
/ out of scope for v1.

## Step 2 — bootstrap
`git init`; `_docs/plan.md`; commit "Add project plan". Commit after every decision.

## Step 3 — stack and architecture
```
Read _docs/plan.md. Propose multiple options for the tech stack and
explain each option.

Don't write code yet.
```
User picks what they can review. Result: _docs/architecture.md (stack table with
verified versions, components, data model, "no code yet").

## Step 4 — backlog
```
Create a backlog with tasks in _docs/tasks.md.

Each task should be small enough to finish in one session, and
independent enough that I could hand it to someone who has not read
the others.

Use this template for each task:

## <number>. <title>
Goal: <one line>
Description: <two or three sentences on what the task involves>

The first task should be setting up an empty project with a passing test.

Don't write code yet.
```
Then: merge too-small, split too-big, remove non-MVP. Then:
```
Create a public GitHub repo for this project.
Move each task from _docs/tasks.md into a GitHub issue.
```
From then on GitHub issues are the only backlog.

## Step 5 — context engineering
AGENTS.md (commands, rules, documents list). CLAUDE.md = `@AGENTS.md`.
_docs/process.md (tasks are issues, one at a time; read acceptance criteria
before start and before close; commit regularly; roles; orchestrator).
Other docs loaded on demand: testing-guidelines.md, design-system.md, api.md,
decisions.md ("do not reopen a decision without changing it there first").
When corrected mid-session:
```
Based on the corrections I made, find the relevant documents and update them.
Commit the current work before changing the documents.
```

## Step 6 — first task
`Implement task 1.` (empty project + passing test)

## Step 7 — roles (graph), _docs/team/
- pm.md: grooms an issue into the 4-section template (Goal / Acceptance criteria
  checkable / Out of scope with follow-up issue links / Constraints). No code.
- software-engineer.md: implements one groomed issue against the criteria, tests,
  commits, does NOT close the issue, comments what was done.
- qa-engineer.md: verdict PASS/FAIL per criterion, runs tests, names them, changes
  nothing. "Only the acceptance criteria and the running code count."
Prompts: `Groom issue #4` / `Implement issue #2` / `Test issue #2`.

## Step 8 — loop engineering
`Groom all GitHub issues. Process one issue at a time.` -> `/goal groom all issues`.
Stop condition must be checkable.

## Step 9 — orchestrator (graph engineering)
Main session = orchestrator; launches PM, engineer, QA as subagents; never grooms,
implements or tests itself. Lifecycle: pick issue -> PM -> engineer -> QA ->
FAIL: back to engineer with the QA comment -> PASS: close -> repeat.
`/goal work through the backlog`. Note from the article: costs much more; often a
simple loop is enough.

## Where ProjectOne is in this method
- Step 1 in progress (2026-10-15). Idea K, event finder. Shape seeds kept in IDEAS.md.
