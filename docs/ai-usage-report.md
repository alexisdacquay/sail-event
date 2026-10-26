# AI Usage Report — Sail-event

Written on 2026-10-16 for issues #1–#26; updated on 2026-10-26 with the process changes that followed. The [process record](../_docs/process.md#process-records) links later handoffs and reproducible tracker counts.

## Process

The initial loop was PM groom → engineer implementation → independent QA → orchestrator closure. QA findings returned to the engineer for a fix and a re-check. Roles and prompts came from [work/METHOD.md](../work/METHOD.md) and the [role files](../_docs/team/).

“Orchestrator” means the main Claude Code session. It launches role subagents with separate context and routes their reports to the next role. [Current responsibilities](../_docs/process.md#roles) define each handoff.

The initial loop was sequential. On 2026-10-20, separate worktrees and PRs supported concurrent work, including PRs [#84](https://github.com/alexisdacquay/sail-event/pull/84), [#85](https://github.com/alexisdacquay/sail-event/pull/85), [#86](https://github.com/alexisdacquay/sail-event/pull/86) and [#87](https://github.com/alexisdacquay/sail-event/pull/87). Owner-selected work and separate approval for production promotion followed on 2026-10-21.

## Tools

| Tool or configuration | Purpose | Evidence |
|---|---|---|
| Claude Code and role subagents | Orchestration, implementation and QA | [Role definitions](../_docs/team/), [work log](../work/STATE.md) |
| Project plugins: feature-dev, frontend-design, pr-review-toolkit, security-guidance, context7, Ponytail | Project guidance; Ponytail supplies minimal-code guidance | [.claude/settings.json](../.claude/settings.json) |
| Course prompts | Step-by-step development method | [work/METHOD.md](../work/METHOD.md) |
| Semgrep via `uvx` | Static security scan | [Scan summary](../security-audit/runs/2026-10-16/semgrep-summary.md), [raw output](../security-audit/runs/2026-10-16/semgrep-output.json) |
| Headless Claude (`claude -p`) | Model security review | [Review output](../security-audit/runs/2026-10-16/model-review-output.json) |

By 2026-10-26, project skills covered [rubric review, field tests, status updates and the reviewer guide](../.claude/skills/). The [work log](../work/STATE.md) records DeepSeek directly on Render or through Kilo locally. Runtime adapters are selected through [environment variables](deployment.md#environment-variables). Lakera checks criteria; the local headless on-call agent is described in [incident-response/README.md](../incident-response/README.md).

## Tracker as evidence

Issue bodies and comments preserve PM specifications, engineer reports and QA verdicts. Issue [#7](https://github.com/alexisdacquay/sail-event/issues/7) shows the full handoff: QA sent work back, the engineer submitted `db3499a`, and QA re-checked and passed it. Issue [#11](https://github.com/alexisdacquay/sail-event/issues/11)’s **edited** history shows the PM turning a raw task into a four-section specification.

The [process record](../_docs/process.md#process-records) includes commands to reproduce the 2026-10-26 tracker counts: 58 groomed issues, 69 issues with QA verdicts and 23 issues sent back by QA.

<a id="defects-the-orchestrator-caught"></a>
<a id="defects-and-corrections-in-the-initial-work"></a>

## Lessons applied to the workflow

| Lesson | Change and date | Checkable evidence |
|---|---|---|
| Independent QA makes acceptance criteria concrete | On 2026-10-16, engineer fixes and QA re-checks established decision validation and response-input handling | [#6](https://github.com/alexisdacquay/sail-event/issues/6), commit `8940b2a`; [#7](https://github.com/alexisdacquay/sail-event/issues/7), commit `db3499a` |
| Test the packaged application | On 2026-10-16, QA checks led to explicit API routing in the SPA fallback and a Python-based container healthcheck | [#14](https://github.com/alexisdacquay/sail-event/issues/14), commit `dd304bb`; [#15](https://github.com/alexisdacquay/sail-event/issues/15), commit `7dec86d` |
| Keep the base compose stack self-contained | PR #32, merged on 2026-10-17, moved the external observability network and OTel wiring to an optional overlay | [PR #32](https://github.com/alexisdacquay/sail-event/pull/32), [overlay](../docker-compose.observability.yml) |
| Separate implementation and review contexts | From issue #65 on 2026-10-20, engineers used assigned worktrees and QA reviewed PR commits | [Process phases](../_docs/process.md#phase-1-and-phase-2) |
| Keep priority and release decisions with the owner | From 2026-10-21, each next item required the owner’s pick, and production promotion required a dev check and approval of a named commit | [Lifecycle](../_docs/process.md#lifecycle), [release procedure](release-process.md#manual-promotion-to-prod) |
| Make causal verification repeatable | On 2026-10-25, the role files added the root-cause gate: causal explanation, regression test committed while failing, fix and independent red/green QA check. The process summary followed on 2026-10-26 | [Root-cause gate](../_docs/process.md#root-cause-gate), commits `c0f83e6` and `ac54483` |

Verify a change date and its diff with `git show --format=fuller <commit>`.

<a id="what-was-verified-by-hand"></a>

## Recorded browser and compose checks

The early session records include:

- **#8:** browser journey through criteria, search, event decisions, reload and authentication redirects.
- **#14:** the same journey against the Docker container, including API routing, static assets and deep links.
- **#15:** compose restart checks for login and event persistence, followed by a fresh-volume check.

Repeatable browser journeys and HTTP persistence checks now run through the [test targets](testing.md).
