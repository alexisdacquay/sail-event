# AI Usage Report — Sail-event

## Process

The project follows the method from "AI-Native Development: Specifications, Loop and Graph Engineering" (aishippingblog.com), documented in `work/METHOD.md`.

- **Roles**: PM (grooms issues into the 4-section template), Software Engineer (implements against acceptance criteria), QA Engineer (verdict PASS/FAIL per criterion). Each role runs as a separate Claude Code subagent with its own context.
- **Orchestrator**: the main Claude Code session launches PM, Engineer, QA as subagents. It never grooms, implements, or tests — it dispatches roles, passes work along, closes on QA PASS, and makes judgment calls with a written reason. The human owner picks issues and approves every merge and every prod promote. Team table: [`_docs/process.md`](../_docs/process.md#team).
- **One issue at a time**: each issue goes through PM groom, engineer implementation, QA verdict. On FAIL, the issue returns to the engineer with the QA comment. On PASS, the orchestrator closes it.

## Tools

- **Claude Code** with Opus model, launching subagents (Sonnet/Opus) per role
- **Ponytail plugin** installed at project scope — enforces minimal code, no over-engineering
- **Course prompts** from `work/METHOD.md` — verbatim prompts from the article, applied step by step
- **Semgrep** (via `uvx`, not installed) for static security analysis
- **Claude headless** (`claude -p`) for model-based security review

## Tracker as evidence

Issues #1 through #26 on GitHub, each with:
- Groomed body in 4-section template: Goal, Acceptance criteria (checkable), Out of scope (with follow-up issue links), Constraints
- QA verdicts: PASS/FAIL per criterion, with commands run and output pasted
- Engineer comments: what was done, commits, test output, smaller option not taken

## Defects the orchestrator caught

### 1. 500 on invalid decision value (`{"decision":"maybe"}`) — #6

`DecisionRequest.decision` typed as `str` instead of `Literal["accepted", "rejected"]`. Invalid values passed Pydantic validation, then raised `ValueError` unhandled. QA found it; fixed in commit `8940b2a`.

### 2. Password echoed by the validation handler — #7

Pydantic validation error for missing fields included raw `input` with plaintext password in the 400 response body (e.g. `'input': {'password': 'secret123'}'`). QA found it; fixed in commit `db3499a` by stripping raw input from error responses.

### 3. SPA fallback swallowing `/api/*` paths — #14

The catch-all route `/{full_path:path}` matched unknown `/api/` paths, returning HTML instead of 404 JSON. QA found it during browser walk-through against the Docker container; fixed in commit `dd304bb` by checking `full_path.startswith("api/")`.

### 4. Missing curl in Docker healthcheck — #15

`python:3.12-slim` has no `curl`. The compose healthcheck used `curl -f`, so `docker compose up --wait` never reported healthy. QA found it; fixed in commit `7dec86d` by switching to a Python `urllib.request` one-liner.

### 5. Misnamed test and false Makefile claim — #13

QA flagged `test_save_criteria_empty_text_returns_400` — function name says 400 but the assertion is 200 (empty text is allowed by design). The Makefile was also claimed to need a fix for exit-code propagation, but `make` already stops at the first failed recipe line; QA confirmed the claim was wrong.

### 6. Tavily date fallback that never ran — #19

`_extract_date()` returned `"unknown"` (truthy) on no match, so `_extract_date(content) or _extract_date(title)` never reached the title fallback. QA proved it with the "Sydney to Hobart Dec 26, 2026" fixture. Fixed in commit `bf8e952`: `_extract_date` returns `None` on no match.

### 7. scorer_model mock object broke a test — #20

The engineer added `evt.scorer_model = getattr(scorer, 'model_id', None)` to the pipeline. When tests mock the scorer with `MagicMock`, `model_id` returns a MagicMock object that SQLAlchemy cannot bind. Initially reported as "pre-existing" failure — the engineer corrected themselves and fixed it in commit `678cd4c` with `isinstance(model_id, str)` guard.

### 8. CI integration job merged red — #22 (fixed in PR #32)

The `docker-compose.yml` referenced an external `sail-observability` network. CI's integration job ran `docker compose up` without that network, failing. Merged red because the orchestrator did not catch it until the next issue. Fixed in PR #32 by moving the external network and OTel wiring to a compose override file.

### 9. Wrong 2025 image tags in the #24 groom

The PM's initial groom for #24 (observability stack) listed 2025-era image tags. The orchestrator corrected them with the actual versions running on the machine (2026-10-17 releases): otel-collector 0.161.0, prometheus v3.15.0, loki 3.7.8, tempo 3.1.0, grafana 13.2.3.

## What was verified by hand

- **Browser walk-throughs on #8**: the orchestrator performed the full user flow in the Claude desktop app's built-in browser — register, save criteria, run search, view events, accept/reject from the queue, reload, clear token to confirm login redirect
- **Browser walk-through on #14**: same flow against the Docker container in the built-in browser — verified SPA routing, API responses, static asset serving, deep links
- **Compose persistence on #15**: `docker compose down` then `up` — login works, events survive; `down -v` then `up` — clean slate

## Lessons learned

- **QA as a separate session matters**: the QA subagent, with fresh context and no knowledge of implementation decisions, found bugs the engineer missed. The password-leak bug (#7) and the decision-value 500 (#6) were invisible to the implementing session.
- **"Pre-existing" is a red flag**: when an agent reports a test failure as pre-existing, verify. The scorer_model failure (#20) was caused by the agent's own change.
- **Compose defaults bite in CI**: dev-only compose features (external networks, host mounts) fail silently in CI. The external network issue (#22/PR #32) merged red.
- **Orchestrator corrections are the quality gate**: the PM grooms get the structure right but can propose wrong versions or miss edge cases. The orchestrator's role is not process — it is judgment.
