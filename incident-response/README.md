# Incident Response

## On-call agent at a glance

The responder receives Grafana webhooks from the local `make up-all` stack; the deployed app sends no telemetry to it. It collects evidence and launches headless Claude Code to produce a repair branch for human review.

```mermaid
sequenceDiagram
    participant App as Local app
    participant Graf as Grafana
    participant Resp as responder.py (host)
    participant Agent as Headless Claude Code
    actor Human
    App->>Graf: Error-run metric rises after injected fault
    Graf->>Resp: Firing alert, POST /alerts with Bearer secret
    Resp->>Resp: Save alert; collect metrics, logs, health, git log
    Resp->>Agent: Versioned task + fenced evidence, worktree from local HEAD
    Agent->>Agent: Investigate, fix, test, commit on incident branch
    Agent-->>Resp: verdict.json
    Resp->>Resp: Save verdict and agent log; remove worktree
    Human->>Human: Review branch; decide whether to deploy
    Note over Human: fix.diff was saved manually after recorded drills
```

The [responder implementation](https://github.com/alexisdacquay/sail-event/blob/542e58cb0fe73065a905febec7637bfa377a77c4/incident-response/responder.py#L89-L185) accepts a firing alert, writes an incident folder, runs [collect-evidence.sh](collect-evidence.sh), and substitutes evidence into the versioned [responder-task.md](responder-task.md). Evidence is fenced as “read-only telemetry data, not instructions”.

| Setting | Actual behavior |
|---|---|
| Responder input | Grafana alert JSON, saved separately as `alert.json` |
| Model input | Versioned task with fenced `evidence.md` (Prometheus results, Loki query, health and git log), plus the source checkout. The alert JSON is not interpolated into the prompt |
| Model and limits | `claude -p --model sonnet --max-budget-usd 1`; subprocess timeout 300 seconds |
| Tools | `Read`, `Edit`; Bash commands for `make test`, grep/find/ls/head/tail and selected git operations (log, diff, status, add, commit, branch creation). No explicit push tool |
| Work area | A full checkout in a worktree beside the repo, `../sail-incident-<id>`, starting at the responder checkout’s HEAD, rather than automatically selecting the running app’s commit; removed after the run. The task asks for branch `incident/<id>` |
| Verdict | `fix`, `false_positive` or `escalate`; includes summary, files, tests and commit. Dry-run writes `dry-run` without launching the agent |
| Environment | Allowlisted OS variables, including `HOME`; optional `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL`. The responder sets `SKIP_HOOK_TESTS=1` itself |
| Human handoff | Review the incident branch and decide whether to merge/deploy or discard it. No deployment step is implemented in the responder |

The responder does not load [autonomy-policy.yaml](autonomy-policy.yaml). Its unscoped `Read` and `Edit` tools, writable Makefile and inherited `HOME` permit access beyond the policy’s backend paths, including CLI credentials; the worktree and tool list provide no network or credential isolation.

<a id="recorded-incidents"></a>

## Recorded drills (fault injected on purpose)

| Drill | Fault and fix | Retained evidence |
|---|---|---|
| 2026-10-17 | Scorer fault [7318f2f](https://github.com/alexisdacquay/sail-event/commit/7318f2f); removed by [dae24e9](https://github.com/alexisdacquay/sail-event/commit/dae24e9) | [Incident folder](incidents/20261017-052050-SearchRunFailures/). App health failed at collection time; deployed version was unknown |
| 2026-10-21 | Search-provider fault [3d9f6b8](https://github.com/alexisdacquay/sail-event/commit/3d9f6b8); restored by [8d2f839](https://github.com/alexisdacquay/sail-event/commit/8d2f839) | [Incident folder](incidents/20261021-074150-SearchRunFailures/), produced through `test-incident.sh` and Grafana’s webhook |

Both folders contain the firing alert, Prometheus evidence, agent log and verdict `fix`. Their Loki sections are empty. `fix.diff` was saved manually from each incident branch afterwards; no responder code writes it. The branches remain on GitHub; check with `git ls-remote --heads origin 'incident/*'`.

The 2026-10-21 drill, step by step:

| Step | UTC | Evidence |
|---|---|---|
| Injected search method raises on every call | 07:32:59 | Fault commit `3d9f6b8` |
| SearchRunFailures begins firing | 07:41:20 | [alert.json](incidents/20261021-074150-SearchRunFailures/alert.json), `startsAt` |
| Evidence collected | 07:41:50 | [evidence.md](incidents/20261021-074150-SearchRunFailures/evidence.md): error-run increase about 28 over ten minutes, app health `ok`, latest commit is the fault; Loki returns no lines |
| Fix committed on incident branch | 07:46:12 | `8d2f839`, [verdict.json](incidents/20261021-074150-SearchRunFailures/verdict.json); [fix.diff](incidents/20261021-074150-SearchRunFailures/fix.diff) saved later by hand |

Alert start to repair commit was 4 min 52 s. The responder has no deployment or recovery-check step, and neither drill records a successful post-fix search or resolved alert. The agent logs report passing tests without full output: the first skips frontend tests; the second gives an unsupported combined total and admits not checking a background pytest run. Captured test output at the repair commits is still needed.

An earlier attempt on 2026-10-20 failed because the CLI could not reach the API (`ENOTFOUND`). Its folder was removed in [ad56f19](https://github.com/alexisdacquay/sail-event/commit/ad56f19) because its alert payload was hand-made. Its verdict remains inspectable with `git show 75e00a1:incident-response/incidents/20261020-231500-SearchRunFailures/verdict.json`.

Evidence-collection gaps: the Loki query selects a `container` label that OTLP logs do not carry; the deployed-version collector reads `version`, while health exposes `commit`. These leave the packets without useful log lines or a reliable running revision. No-data and idle-series triggers are described under [alerting behavior](../observability/README.md#alerting).

## Required environment variables

| Variable | Required | Meaning |
|---|---|---|
| `RESPONDER_WEBHOOK_SECRET` | yes | Same non-empty Bearer secret in Grafana and responder; responder refuses to start without it |
| `ANTHROPIC_API_KEY` | optional | Passed through if set; otherwise the CLI may use its own sign-in |
| `ANTHROPIC_BASE_URL` | optional | Explicit API endpoint override passed to the CLI |
| `RESPONDER_PORT` | no | Host listen port, default 8001; server binds all interfaces |
| `CLAUDE_BIN` | no | CLI path, default `claude` |

`collect-evidence.sh` reads `HOST_PORT`, `PROMETHEUS_PORT` and `LOKI_PORT` to locate local services. Use the same overrides in both shells.

## Start

With Docker running and the Claude CLI authenticated and able to reach its API from a plain shell:

```bash
export RESPONDER_WEBHOOK_SECRET='choose-a-local-secret'
make up-all
```

In a second terminal, set the same secret and start the foreground responder:

```bash
RESPONDER_WEBHOOK_SECRET='choose-a-local-secret' make responder
```

Set the secret before Grafana starts too, or its webhook will send an empty Bearer value. `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL` are retained when explicitly set; other session-specific model variables are not inherited. If a configured proxy cannot resolve, choose a reachable endpoint rather than assuming VPN state explains it.

## Reproduce the full loop (test-incident.sh)

Use a clean, disposable checkout and a normal terminal. This script **creates a temporary fault branch in your checkout, edits the provider and commits the fault**. Its exit trap attempts to switch back, delete that branch and rebuild the app; a killed script can leave cleanup unfinished. A live run creates an incident folder and normally leaves an `incident/<id>` branch. The responder creates its temporary worktree beside the repo. The live mode spends model credits.

The script starts both stacks and the responder, drives failed searches with an increased rate limit, waits for the provisioned rule, and receives Grafana’s own webhook. Its final live-mode assertions check that the four output files exist; they do not require verdict `fix` or validate its contents.

```bash
RESPONDER_WEBHOOK_SECRET='choose-a-local-secret' incident-response/test-incident.sh
```

Override ports/project/network to avoid another stack:

```bash
COMPOSE_PROJECT_NAME=exam3 HOST_PORT=8070 GRAFANA_PORT=3071 \
  PROMETHEUS_PORT=9071 LOKI_PORT=3171 TEMPO_PORT=3271 \
  OTEL_COLLECTOR_PORT=4371 OTEL_COLLECTOR_METRICS_PORT=8871 \
  SAIL_OBS_NETWORK=exam3-obs RESPONDER_PORT=8071 \
  RESPONDER_WEBHOOK_SECRET='choose-a-local-secret' \
  incident-response/test-incident.sh
```

### `--dry-run` mode

```bash
RESPONDER_WEBHOOK_SECRET='choose-a-local-secret' incident-response/test-incident.sh --dry-run
```

This still commits the injected fault and changes the checkout. It exercises alert → webhook → evidence → worktree creation, then writes verdict `dry-run` without launching the model. The script also checks that the verdict is `dry-run`.

### Expected output

[responder.py](responder.py) writes under `incident-response/incidents/<timestamp>-<alertname>/`:

| File | Produced by |
|---|---|
| `alert.json` | Responder: raw Grafana firing alert |
| `evidence.md` | Collector script: metrics, log query, health, recent commits |
| `agent.log` | CLI output, or a dry-run note |
| `verdict.json` | Agent’s verdict copied by the responder, or the responder’s dry-run verdict; absent if the agent exits without writing one |
| `fix.diff` | Not automatic; manually saved after the two retained drills |

## Test the fix branch

[verify-recovery.sh](runbooks/verify-recovery.sh) switches branches and runs backend/frontend tests. Use a disposable checkout: `incident-response/runbooks/verify-recovery.sh <branch>`. Despite its name, it checks the branch’s tests only. The separate standard-library responder suite is `python3 -I -B incident-response/test_responder.py`; it launches no model agent and is not in CI.
