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

# LESSON 2 — Build and Ship (article read 2026-10-15)
Order: spec -> frontend with mocked service layer -> openapi.yaml from the frontend
client -> FastAPI backend with in-memory store -> connect -> SQLite via SQLAlchemy.
"At each stage we get something concrete that we can test." New session per step.
Repo shape: /backend /docs /frontend AGENTS.md openapi.yaml. Spec -> docs/spec.md.
Homework 2 adds: name the app in the brainstorm; spec settles on 2-4 features (HW1).
Prompts, verbatim:
```
Create a <app>.
[Paste the specification here.]
Centralize every backend call in one services layer, and create a mock
implementation of it so the whole app runs without a real backend.
Add tests.
```
```
Read the frontend's API client in frontend/
Create openapi.yaml at the repository root.
Specify the backend this frontend expects: every endpoint, method, path, request body, response body, and which endpoints need authentication.
```
```
Build a FastAPI backend in backend/ that implements the openapi.yaml spec.
Use an in-memory store and seed it with data so the frontend has something to show. Add authentication with hashed passwords and bearer tokens for the endpoints that need it.
Split the code into modules - routers, models, store, auth
Write tests
```
`Create a Makefile so I can easily run it.` / `Switch the frontend to use the real backend client.`
```
Replace the in-memory store with a database. Use SQLite and SQLAlchemy.
Use an environment variable to configure which DB the server should connect to.
Make it database-agnostic - later we will add support for other databases (e.g. Postgres).
```

# LESSON 3 — Deploy (article read 2026-10-15)
Order: one container (backend serves built frontend) -> Postgres -> docker-compose ->
integration + Playwright e2e against compose -> deploy (AWS CloudFormation in the
article; Render/Fly/Railway fine) -> CI/CD with OIDC, deploy only on green, health check.
Prompts, verbatim:
```
Create a Dockerfile that builds the frontend with Node, then builds a Python image with the backend and the frontend static files.
Backend should serve the frontend.
```
`Add Postgres support to the backend.` / `Create docker-compose.yaml with two services: Postgres and the app.`
`Create integration tests that run against docker-compose.yaml. What scenarios should we test?`
```
Add an end-to-end test that runs against docker-compose.yaml.
Use Playwright to: <numbered user journey, two sessions>
Put the tests in the e2e/ folder in the repository root.
```
`Deploy this application to AWS. Use AWS CloudFormation.`
```
Create a CI/CD pipeline that:
- runs backend and frontend tests in parallel
- builds the Docker Compose stack and runs integration and end-to-end tests against it
- deploys to AWS using a GitHub OIDC role
- validates that the deploy is successful by checking the health endpoint
```
Homework 3 variant: kind (local k8s) + act; "keep the existing version running and stop
the deployment" when a test fails.

# LESSON 4 — DevOps and observability (article read 2026-10-15)
Order: dev + prod envs -> manual promotion workflow -> build/deploy split with a
registry, tag YYYYMMDD-HHMMSS-shortsha -> OTel instrumentation (service, env,
version) -> collector + Prometheus/Loki/Tempo/Grafana in observability/ as a separate
compose -> app-specific metrics -> dashboard -> actionable alert (threshold, duration,
service, env, version, owner, dashboard URL) -> on-call agent: poll alerts, headless
agent with the on-call prompt -> introduce a realistic bug to test the loop.
Module page adds the guardrails the article skips: evidence packet (read-only,
allowlisted), autonomy policy, verify recovery, escalation, Semgrep audit, capability
table, operations-and-security-report.md.
On-call prompt, verbatim:
```
You are the on-call engineer for this repository. An alert just fired.
Investigate the root cause. Read the code and reproduce the failure.
If you find a real bug, make the smallest correction, run the backend tests,
and commit the fix with a clear message.
If the alert is a false positive, explain why and do not change the code.
```
Homework 4: responder at POST /alerts :8001, Grafana webhook, 5xx alert.

# LESSON 5 — skills and subagents (article read 2026-10-15)
- skill = SKILL.md with name/description frontmatter in .agents/skills/<name>/
  (.claude/skills symlink). Create it AFTER doing the task once with corrections:
```
Save this as a skill. Cover the workflow we followed and keep all the corrections I made in mind, so the next agent can do the task correctly from the start.
This skill is specific to this project, so don't create a global skill.
```
- subagent = .agents/agents/<name>.md (.claude/agents/), can just say
  "Read your role definition from _docs/team/swe.md". Fresh context per role:
  never test in the session that implemented.
- orchestrator in process.md; parallel = one worktree per issue, up to five agents,
  fresh reviewer, merge one at a time, never implement itself.
Module deliverable: AGENTS.md, 1 skill, 1 subagent, 1 MCP server, 1 hook, 1 plugin
or custom agent, permissions note, demo script.

## Where ProjectOne is in this method
- Step 1 in progress (2026-10-15). Idea K, event finder. Shape seeds kept in IDEAS.md.
