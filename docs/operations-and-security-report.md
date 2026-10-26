# Operations and Security Report — Sail-event

Updated 2026-10-26. This report follows the local fault-injection drill of 2026-10-17 and the operational changes that followed. The data-flow section describes main’s implementation.

## Local drill: 20261017-052050-SearchRunFailures

The local `make up-all` stack connects observability, alerting and the on-call responder. Fault commit [7318f2f](https://github.com/alexisdacquay/sail-event/commit/7318f2f) deliberately made the original scorer raise an exception. The responder produced repair commit [dae24e9](https://github.com/alexisdacquay/sail-event/commit/dae24e9) for human review.

| Handoff | Recorded evidence |
|---|---|
| Search failures → alert | [alert.json](../incident-response/incidents/20261017-052050-SearchRunFailures/alert.json): SearchRunFailures began firing at `2026-10-17T05:20:20Z` |
| Alert → investigation | [evidence.md](../incident-response/incidents/20261017-052050-SearchRunFailures/evidence.md): collected at `05:20:50Z`, with Prometheus results, a log query, health request and recent commits |
| Investigation → repair branch | [agent.log](../incident-response/incidents/20261017-052050-SearchRunFailures/agent.log), [verdict.json](../incident-response/incidents/20261017-052050-SearchRunFailures/verdict.json): verdict `fix`, file changed and repair commit |
| Repair branch → human review | Branch `incident/20261017-052050-SearchRunFailures`; [repair diff](../incident-response/incidents/20261017-052050-SearchRunFailures/fix.diff) saved after the drill |

The rule checks `increase(sail_runs_total{outcome="error"}[10m]) > 1` for five minutes. The agent log identifies the injected exception and reports its removal. The [verdict](../incident-response/incidents/20261017-052050-SearchRunFailures/verdict.json) records the backend test command `uv run pytest tests/ -q`.

The responder launches Sonnet through headless Claude Code with a USD 1 budget and a 300-second timeout. Its [runbook](../incident-response/README.md#on-call-agent-at-a-glance) describes the task, tools, worktree and review handoff.

## Lessons applied after the drill

| Lesson | Change and date | Evidence |
|---|---|---|
| Authenticate and structure the alert handoff | On 2026-10-17, webhook hardening added constant-time secret comparison, alert-name validation, an allowlisted agent environment, fenced evidence and a narrower command list | [Commit 4cee1d6](https://github.com/alexisdacquay/sail-event/commit/4cee1d6) |
| Reproduce the handoff through Grafana | On 2026-10-21, the drill script used Grafana’s own webhook and added `--dry-run` for the alert → evidence → worktree chain | [Commit ad56f19](https://github.com/alexisdacquay/sail-event/commit/ad56f19), [drill instructions](../incident-response/README.md#reproduce-the-full-loop-test-incidentsh) |
| Make the model endpoint an operator setting | On 2026-10-21, the responder added explicit `ANTHROPIC_BASE_URL` passthrough | [Commit dd84f8a](https://github.com/alexisdacquay/sail-event/commit/dd84f8a), [environment settings](../incident-response/README.md#required-environment-variables) |
| Preserve a complete repair handoff | The 2026-10-21 search-provider drill retained the alert, evidence, agent log, verdict and repair diff. Alert start to repair commit took 4 min 52 s | [Recorded drill timeline](../incident-response/README.md#recorded-incidents) |

Verify change dates and code with `git show --format=fuller <commit>`.

## Review the repair branch

Use a disposable checkout to run `incident-response/runbooks/verify-recovery.sh <branch>`. The [script](../incident-response/runbooks/verify-recovery.sh) selects the branch and runs backend and frontend tests. Review the diff and verdict, then follow the owner’s [release procedure](release-process.md).

## Security review records

The [2026-10-16 Semgrep and model-review outputs](../security-audit/runs/2026-10-16/) and [human disposition](../security-audit/disposition.md) preserve the scan → review → follow-up handoff. The 2026-10-17 responder-hardening commit above records the resulting implementation changes.

## AI tool and data policy

| Destination | Application data sent | Implementation |
|---|---|---|
| Search provider | Criteria text plus ` event` as the search query; configured search options | [pipeline.py](../backend/app/services/pipeline.py), [provider factory](../backend/app/adapters/factory.py) |
| Configured language model | Criteria, page content and extracted event fields for parsing, extraction, judging and duplicate checking | [OpenAI-compatible adapter](../backend/app/adapters/llm_openai_compat.py), [versioned prompts](../backend/app/adapters/prompts/) |
| Lakera, when selected | Criteria text on save for prompt-attack checks | [criteria router](../backend/app/routers/criteria.py), [Lakera adapter](../backend/app/adapters/guard_lakera.py) |
| Fallback model, when selected | Text submitted to the self-check guard when Lakera is unavailable | [factory](../backend/app/adapters/factory.py), [self-check](../backend/app/services/guardrails/self_check.py) |
| On-call Claude agent | Fenced local evidence and the source worktree | [responder.py](../incident-response/responder.py), [task prompt](../incident-response/responder-task.md) |

The application uses an environment-selected model endpoint; the work log records DeepSeek directly on Render and Kilo locally. Select providers whose retention and training terms meet the intended data policy.

The [validation handler](../backend/app/main.py) omits raw request input from error responses. Versioned prompts fence external content, and schemas validate model output. The responder authenticates its webhook with a shared Bearer secret using constant-time comparison.

Store keys in environment variables, local git-ignored files or service/GitHub secret stores. Keep sensitive text out of criteria. Before sharing telemetry, review the [signal contents](../observability/README.md#telemetry-contents) and redact feed tokens, client identifiers, URLs and provider exception text.
