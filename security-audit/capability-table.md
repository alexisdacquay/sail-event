# Responder Agent Capability Table

Documents the on-call incident responder as currently implemented in
`incident-response/responder.py`, `autonomy-policy.yaml`, and `responder-task.md`.

## Read access

| Path pattern | Source |
|---|---|
| `backend/app/**` | `--allowedTools Read`, `Bash(cat *)`, `Bash(grep *)`, `Bash(find *)`, `Bash(ls *)`, `Bash(head *)`, `Bash(tail *)` |
| `backend/tests/**` | Same tools |
| Incident evidence (`evidence.md`, `alert.json`) | Injected into prompt via `{evidence}` placeholder |
| Git history | `Bash(git log *)`, `Bash(git diff *)`, `Bash(git status)` |

## Write access

| Path pattern | Source |
|---|---|
| `backend/app/**` | `--allowedTools Edit` |
| `backend/tests/**` | `--allowedTools Edit` |
| `verdict.json` (repo root in worktree) | Written by agent per `responder-task.md` instructions |
| Git index + commits | `Bash(git add *)`, `Bash(git commit *)`, `Bash(git checkout -b *)` |

## Execute access

| Command | Source |
|---|---|
| `make test` | `--allowedTools Bash(make test)` |
| Read-only shell: `cat`, `grep`, `find`, `ls`, `head`, `tail` | `--allowedTools` glob patterns |
| Git read: `git log`, `git diff`, `git status` | `--allowedTools` |
| Git write: `git add`, `git commit`, `git checkout -b` | `--allowedTools` |

## Credentials

| Credential | How held |
|---|---|
| `ANTHROPIC_API_KEY` | Inherited from host environment (used by `claude -p` for API auth) |
| App secrets (`JWT_SECRET`, `SEARCH_ALL_API_KEY`, `TAVILY_API_KEY`) | Not available — not passed to agent env |

## Prompt source

`incident-response/responder-task.md` — a versioned repo file with `{evidence}` and
`{incident_id}` placeholders injected at runtime by `responder.py` line 58.
The prompt is not derived from user input or external data beyond the evidence packet
(which is read-only telemetry queries).

## Trigger

Grafana webhook `POST /alerts` on port 8001, handled by `responder.py`'s
`AlertHandler`. Contact point configured in
`observability/grafana/provisioning/alerting/contactpoints.yaml` with URL
`$RESPONDER_WEBHOOK_URL` (default `http://host.docker.internal:8001/alerts`).

## Budget and timeout

| Limit | Value | Source |
|---|---|---|
| Token budget | `--max-budget-usd 1` | `responder.py` line 89 |
| Subprocess timeout | 300 seconds | `responder.py` line 97, `subprocess.run(timeout=300)` |
| Evidence collection timeout | 60 seconds | `responder.py` line 53, `subprocess.run(timeout=60)` |

## Merge authority

None. The agent commits to a git worktree branch (`incident/<id>`). Push is
forbidden by both `--allowedTools` (not listed) and `autonomy-policy.yaml`
(explicitly in the `forbidden` list). A human must review and merge the branch.
