# AI Usage Report — Sail-event

Scope note (2026-10-26): written on 2026-10-16, this report covers issues #1–#26 and their immediate corrections. Later handoffs and process gaps are in [the process record](../_docs/process.md#evidence-it-ran-this-way).

## Process

The initial intended loop was PM groom → engineer implementation → independent QA → orchestrator closure. On QA FAIL, the engineer received the findings for correction and re-check. Roles and prompts came from [work/METHOD.md](../work/METHOD.md) and the [role files](../_docs/team/).

“Orchestrator” throughout this report means the main Claude Code session, not the human owner. It launched role subagents with separate context. It also corrected grooms and performed browser checks itself, exceeding its dispatch role in the examples below. Current responsibilities and historical exceptions: [_docs/process.md](../_docs/process.md#team).

The initial loop was sequential. Later work ran concurrently in separate worktrees and PRs, for example PRs [#84](https://github.com/alexisdacquay/sail-event/pull/84), [#85](https://github.com/alexisdacquay/sail-event/pull/85), [#86](https://github.com/alexisdacquay/sail-event/pull/86) and [#87](https://github.com/alexisdacquay/sail-event/pull/87) on 2026-10-20. Owner-selected work and separate approval for production promotion followed on 2026-10-21.

## Tools

| Tool or configuration | Purpose | Evidence |
|---|---|---|
| Claude Code and role subagents | Orchestration, implementation and QA | [Role definitions](../_docs/team/), [work log](../work/STATE.md) |
| Project plugins: feature-dev, frontend-design, pr-review-toolkit, security-guidance, context7, Ponytail | Enabled project configuration; Ponytail supplies minimal-code guidance, not enforcement | [.claude/settings.json](../.claude/settings.json) |
| Course prompts | Step-by-step development method | [work/METHOD.md](../work/METHOD.md) |
| Semgrep via `uvx` | Static security scan | [Scan summary](../security-audit/runs/2026-10-16/semgrep-summary.md), [raw output](../security-audit/runs/2026-10-16/semgrep-output.json) |
| Headless Claude (`claude -p`) | Model security review | [Review output](../security-audit/runs/2026-10-16/model-review-output.json) |

Later tooling (as of 2026-10-26): project skills live in [.claude/skills/](../.claude/skills/) (rubric-review, field-test, status-update, reviewer-guide). The [work log](../work/STATE.md) records DeepSeek directly on Render or through Kilo locally. Runtime provider configuration is in [deployment.md](deployment.md#environment-variables); Lakera checks criteria, and the local headless on-call agent is described in [incident-response/README.md](../incident-response/README.md). These are separate from the early defect examples.

## Tracker as evidence

The issue bodies and comments expose grooms, implementation reports and QA verdicts. They are not uniform: [#17](https://github.com/alexisdacquay/sail-event/issues/17) and [#21](https://github.com/alexisdacquay/sail-event/issues/21) were AWS tasks delivered on Render instead, then closed without the four-section groom or QA verdict. Inspect them with `gh issue view 17 --comments` and `gh issue view 21 --comments`.

Issue [#7](https://github.com/alexisdacquay/sail-event/issues/7) is a complete recorded FAIL → fix → PASS cycle. The later [process record](../_docs/process.md#evidence-it-ran-this-way) gives reproducible counts and exceptions.

<a id="defects-the-orchestrator-caught"></a>

## Defects and corrections in the initial work

Items 1–6 are QA findings or checks; item 7 was corrected by the implementing engineer after challenge, item 8 was missed before merge, and item 9 was an orchestrator correction.

### 1. 500 on invalid decision value (`{"decision":"maybe"}`) — #6

`DecisionRequest.decision` typed as `str` instead of `Literal["accepted", "rejected"]`. Invalid values passed Pydantic validation, then raised `ValueError` unhandled. QA found it; fixed in commit `8940b2a`.

### 2. Password echoed by the validation handler — #7

Pydantic validation error for missing fields included raw `input` with plaintext password in the 400 response body (e.g. `'input': {'password': 'example'}`). QA found it; fixed in commit `db3499a` by stripping raw input from error responses.

### 3. SPA fallback swallowing `/api/*` paths — #14

The catch-all route `/{full_path:path}` matched unknown `/api/` paths, returning HTML instead of 404 JSON. QA identified it; the orchestrator also checked the Docker container in the browser; fixed in commit `dd304bb` by checking `full_path.startswith("api/")`.

### 4. Missing curl in Docker healthcheck — #15

`python:3.12-slim` has no `curl`. The compose healthcheck used `curl -f`, so `docker compose up --wait` never reported healthy. QA found it; fixed in commit `7dec86d` by switching to a Python `urllib.request` one-liner.

### 5. Misnamed test and false Makefile claim — #13

QA flagged `test_save_criteria_empty_text_returns_400` — function name says 400 but the assertion is 200 (empty text is allowed by design). The acceptance criterion assumed `make test` would exit 0 on backend failure. The engineer’s probe and QA check showed that make already stops at the first failing recipe line ([#13 comments](https://github.com/alexisdacquay/sail-event/issues/13)).

### 6. Tavily date fallback that never ran — #19

`_extract_date()` returned `"unknown"` (truthy) on no match, so `_extract_date(content) or _extract_date(title)` never reached the title fallback. QA proved it with the "Sydney to Hobart Dec 26, 2026" fixture. Fixed in commit `bf8e952`: `_extract_date` returns `None` on no match.

### 7. scorer_model mock object broke a test — #20

The engineer added `evt.scorer_model = getattr(scorer, 'model_id', None)` to the pipeline. When tests mock the scorer with `MagicMock`, `model_id` returns a MagicMock object that SQLAlchemy cannot bind. Initially reported as a "pre-existing" failure, it was challenged by the orchestrator and then corrected by the engineer in commit `678cd4c` with `isinstance(model_id, str)` guard.

### 8. CI integration job merged red — #22 (fixed in PR #32)

The `docker-compose.yml` referenced an external `sail-observability` network. CI's integration job ran `docker compose up` without that network, failing. Merged red because the orchestrator did not catch it until the next issue. Fixed in PR #32 by moving the external network and OTel wiring to a compose override file.

<a id="9-wrong-2025-image-tags-in-the-24-groom"></a>

### 9. Image versions corrected in the #24 groom

The PM’s initial groom for [#24](https://github.com/alexisdacquay/sail-event/issues/24) listed older image tags. The orchestrator substituted versions recorded as running locally: otel-collector 0.161.0, prometheus v3.15.0, loki 3.7.8, tempo 3.1.0, grafana 13.2.3.

<a id="what-was-verified-by-hand"></a>

## Browser and compose checks recorded by the orchestrator

- **Browser walk-throughs on #8**: the orchestrator session recorded the full user flow in the Claude desktop app's built-in browser — register, save criteria, run search, view events, accept/reject from the queue, reload, clear token to confirm login redirect
- **Browser walk-through on #14**: same flow against the Docker container in the built-in browser — verified SPA routing, API responses, static asset serving, deep links
- **Compose persistence on #15**: `docker compose down` then `up` — login works, events survive; `down -v` then `up` — clean slate

## Lessons learned

- **QA as a separate session matters**: the QA subagent, with fresh context and no knowledge of implementation decisions, found bugs the engineer missed. The password-leak bug (#7) and the decision-value 500 (#6) were found during QA.
- **"Pre-existing" is a red flag**: when an agent reports a test failure as pre-existing, verify. The scorer_model failure (#20) was caused by the agent's own change.
- **Compose defaults bite in CI**: dev-only compose features (external networks, host mounts) can break CI. The external network issue (#22/PR #32) merged red.
- **Independent verification needs a record**: a fix or an orchestrator’s self-check does not replace a fresh QA verdict. Later examples of this gap include [#39](https://github.com/alexisdacquay/sail-event/issues/39) and [#55](https://github.com/alexisdacquay/sail-event/issues/55), closed after the orchestrator fixed or re-checked a QA FAIL without a new QA PASS.

## Known process gaps

The record includes orchestrator overreach (groom corrections, implementation and testing), issue bodies missing required grooming sections, closures and merges without a QA PASS, and direct pushes to main. PR #31’s red merge is item 8 above; [PR #138](https://github.com/alexisdacquay/sail-event/pull/138) later merged before CI completed; its integration check subsequently failed. The role files began on 2026-10-16 (`98f3cf7`); the owner priority/prod gates date from 2026-10-21 ([process history](../_docs/process.md)); the red-test/root-cause gate entered the roles on 2026-10-25 (`c0f83e6`) and the process summary on 2026-10-26 (`ac54483`). Verify dates with `git show --no-patch --format=fuller <commit>`. The [process record](../_docs/process.md#evidence-it-ran-this-way) documents the exceptions and counting commands.
