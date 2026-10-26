# Operations and Security Report — Sail-event

Scope note (2026-10-26): this report reconstructs the local fault-injection drill of 2026-10-17. The data-flow section describes main’s implementation.

## Local drill: 20261017-052050-SearchRunFailures

Observability, alerts and the on-call responder run in the local `make up-all` stack; the deployed app sends no telemetry to it. Fault commit [7318f2f](https://github.com/alexisdacquay/sail-event/commit/7318f2f) deliberately made the old `FakeScorer.score()` raise. The responder produced fix commit [dae24e9](https://github.com/alexisdacquay/sail-event/commit/dae24e9). The old scorer has since been replaced; [incident-response/README.md](../incident-response/README.md#recorded-incidents) also documents the later search-provider drill and a failed attempt.

### 1. Deployed version and user impact

The [evidence packet](../incident-response/incidents/20261017-052050-SearchRunFailures/evidence.md) records an unknown deployed version and a failed health GET. Its Prometheus query reports an interpolated increase of about 27.69 failed manual runs in ten minutes; the [alert](../incident-response/incidents/20261017-052050-SearchRunFailures/alert.json) annotates 23 at its earlier evaluation. The samples were taken at different times. The injected exception caused local searches to fail.

### 2. Alert and evidence

SearchRunFailures began firing at `2026-10-17T05:20:20Z`; the evidence was collected at `05:20:50Z`. The rule checks `increase(sail_runs_total{outcome="error"}[10m]) > 1` for five minutes. The packet contains metrics, a Loki query, health and recent commits. Loki returned no log lines. The collector query’s `container` selector does not match the OTLP service labels ([collector script](../incident-response/collect-evidence.sh)).

### 3. Agent action and current limits

The [agent log](../incident-response/incidents/20261017-052050-SearchRunFailures/agent.log) identifies the injected exception and reports removing it. The responder launches Sonnet through headless Claude Code, with a USD 1 budget limit and a 300-second subprocess timeout. Its current tools and environment are documented in [the responder controls table](../incident-response/README.md#on-call-agent-at-a-glance).

### 4. Repair policy and recorded tests

The [autonomy policy](../incident-response/autonomy-policy.yaml) specifies backend-only edits, tests and branch commits, with no push or infrastructure changes. The [implementation](../incident-response/responder.py) does not load that file: it passes a tool allowlist with unscoped `Read` and `Edit` plus `make test` and selected shell/git commands. A writable Makefile means the allowlist is not a reliable boundary against external actions.

The recorded [verdict](../incident-response/incidents/20261017-052050-SearchRunFailures/verdict.json) names `backend/app/adapters/fake.py` and `uv run pytest tests/ -q`. The log reports passing backend tests and explicitly says frontend tests were skipped. The retained log has no full test output.

### 5. Recovery verification

Verdict `fix` and commit `dae24e9` exist on branch `incident/20261017-052050-SearchRunFailures`. The [saved diff](../incident-response/incidents/20261017-052050-SearchRunFailures/fix.diff) was added manually afterwards; it is not responder output. No deployment, resolved webhook or post-deployment metric check is retained.

[verify-recovery.sh](../incident-response/runbooks/verify-recovery.sh) switches to the supplied branch and runs backend/frontend tests. It does not deploy or verify alert resolution. Use a disposable checkout if running it.

### 6. Related security findings and human disposition

The [2026-10-16 scan and model-review outputs](../security-audit/runs/2026-10-16/) and [disposition](../security-audit/disposition.md) are dated audit evidence, not a current security assessment. The disposition still describes the first scorer and findings then deferred to [#33](https://github.com/alexisdacquay/sail-event/issues/33)–[#36](https://github.com/alexisdacquay/sail-event/issues/36). Check those issues and current code before treating a listed mitigation as complete. The capability table is also historical; current responder limits and their gaps are above.

## AI tool and data policy

| Destination | Application data sent | Implementation |
|---|---|---|
| Search provider | Criteria text plus ` event` as the search query; configured search options | [pipeline.py](../backend/app/services/pipeline.py), [provider factory](../backend/app/adapters/factory.py) |
| Configured language model | Criteria, page content and extracted event fields for parsing, extraction, judging and duplicate checking | [OpenAI-compatible adapter](../backend/app/adapters/llm_openai_compat.py), [versioned prompts](../backend/app/adapters/prompts/) |
| Lakera, when selected | Criteria text on save for prompt-attack checks; moderation, PII and link detections are ignored | [criteria router](../backend/app/routers/criteria.py), [Lakera adapter](../backend/app/adapters/guard_lakera.py) |
| Fallback model, when selected | Text submitted to the self-check guard when Lakera is unavailable | [factory](../backend/app/adapters/factory.py), [self-check](../backend/app/services/guardrails/self_check.py) |
| On-call Claude agent | Fenced local evidence and access to the source worktree; CLI authentication/configuration available through its environment and `HOME` | [responder.py](../incident-response/responder.py), [task prompt](../incident-response/responder-task.md) |

The application uses an environment-selected model endpoint; the work log records DeepSeek directly on Render and Kilo locally. It no longer uses the first Anthropic scorer described in the original report. Data retention and training use follow the configured provider’s terms.

The validation handler omits raw request input from error responses ([main.py](../backend/app/main.py)). Authentication credentials are not deliberate prompt fields, but criteria and external content are untrusted and can themselves contain sensitive text. Prompt fencing and bounded output schemas reduce particular risks; they do not isolate models from that content.

The responder authenticates its webhook with a shared Bearer secret using constant-time comparison.

Keep keys out of tracked files. Configure them through environment variables, local git-ignored files or service/GitHub secret stores. Telemetry contents and unresolved privacy gaps are listed in the [observability runbook](../observability/README.md#what-telemetry-contains-and-never-contains).
