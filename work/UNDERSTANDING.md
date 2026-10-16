# Understanding — AI Dev Tools Zoomcamp final project (read 2026-10-15)

Sources read: project page, logistics page, project/README.md (draft rubric),
course README, modules 01-05 (markdown only, not the videos/articles).

## What the project is
- one solo, end-to-end full-stack app of MY choice, built WITH AI tools, in a public repo
- the app itself is secondary; the graded thing is the disciplined workflow around it
- certificate = passing project + peer reviews. homework not required.
- rubric is DRAFT; may change. 14 criteria, max 30 pts.

## Rubric, compressed (max per item)
 1 problem description ............. 2
 2 AI workflow documented .......... 2  (prompts, context files, review, verification)
 3 tech + architecture ............. 2
 4 frontend (+tests) ............... 3
 5 OpenAPI contract ................ 2  (contract-first, drives backend)
 6 backend (+tests) ................ 3
 7 database, multi-env, documented . 2
 8 docker compose, one command ..... 2
 9 integration tests, separated .... 2
10 cloud deployment, live URL ...... 2
11 CI runs tests + CD deploys ...... 2
12 agent extension pack ............ 2  (instructions, skill, subagent, MCP server, hook, permissions note)
13 security/audit/ops .............. 2  (PR audit, Semgrep findings, agent security notes,
                                         incident diagnosis output, AI tool/data policy)
14 reproducibility ................. 2

## Required repo shape
README.md product-spec.md AGENTS.md frontend/ backend/ openapi.yaml
docker-compose.yml .github/workflows/ docs/ security/ ops/
+ agent-capabilities/ agent-hooks/ mcp-server/ plugins/|custom-agent/
+ docs/agent-extension-pack.md docs/permissions.md

## Course workflow the project must mirror (modules 1-5)
- M1 spec first: product-spec.md (user stories, acceptance criteria, non-goals), AGENTS.md,
  backlog of small tasks, PM/engineer/QA roles, loop (iterate until tests pass) + graph
  (DAG of tasks) engineering.
- M2 frontend prototype with mocked calls -> openapi.yaml as source of truth ->
  FastAPI backend from contract, mock store -> SQLite, DB-agnostic -> unit + frontend tests.
  docs/ai-usage-report.md.
- M3 integration tests on real DB -> multi-stage Dockerfile + compose, SQLite->Postgres ->
  GH Actions CI (lint, unit, integration, build) -> deploy (Render/Fly/Railway/Cloud Run) ->
  CD gated on tests, staging/prod, smoke test, rollback. docs/testing|deployment|release-process.md
- M4 OpenTelemetry -> Prometheus/Loki/Tempo/Grafana; one user-impact alert; evidence packet
  (read-only, allowlisted); headless agent responder with bounded permissions; Semgrep audit;
  Snyk Agent Scan; capability table. docs/operations-and-security-report.md
- M5 agent extension pack: AGENTS.md, skill, subagent, MCP server, hook, plugin or custom
  agent, permissions note, demo script.

## Constraints that shape idea choice
- reviewers must run it: free tiers, no private creds, public data or self-generated data
- cannot reuse course examples: Snake Arena, interview-canvas, retroloop, weekly-feedback,
  order-tracker
- 2-3 weeks of focused work is the norm -> SMALL app, big workflow
- the app needs: >=2 entities with a relation, a workflow worth integration-testing, an
  endpoint that can plausibly fail (for the incident demo), and data an MCP tool can expose
- course default stack: FastAPI + SQLite->Postgres + JS frontend + GH Actions + Docker. Free
  to deviate, but reviewers follow the default more easily.
