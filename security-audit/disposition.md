# Security Findings Disposition

## Semgrep findings (2)

| ID | Rule | Severity | Disposition | Detail |
|---|---|---|---|---|
| semgrep-001 | `python37-compatibility-importlib2` | ERROR | accepted | Project targets Python 3.12; `importlib.resources` is available. Not a real issue. |
| semgrep-002 | `dynamic-urllib-use-detected` | WARNING | accepted | URL is hardcoded to `https://api.tavily.com/search`, not user-controlled. The `file://` risk does not apply. |

## Model-review findings (20)

| ID | Severity | Title | Disposition | Detail |
|---|---|---|---|---|
| model-001 | critical | Hardcoded JWT fallback secret | deferred | Deferred to #33 |
| model-002 | high | docker-compose JWT_SECRET weak default | deferred | Deferred to #33 |
| model-003 | high | docker-compose SEARCH_ALL_API_KEY weak default | accepted | Dev-only default; production requires explicit env var. Documented in `.env.example`. |
| model-004 | high | Webhook /alerts has no auth | deferred | Deferred to #34 |
| model-005 | high | Agent inherits host env secrets | deferred | Deferred to #34 |
| model-006 | high | No rate limiting on login | deferred | Deferred to #35 |
| model-007 | medium | Postgres credentials hardcoded in compose | accepted | Dev-only compose file; production uses managed database with distinct credentials. |
| model-008 | medium | alertname path traversal | deferred | Deferred to #34 |
| model-009 | medium | Evidence prompt injection | deferred | Deferred to #34 |
| model-010 | medium | Bash(cat *) broad file read | deferred | Deferred to #34 |
| model-011 | medium | autonomy-policy.yaml not enforced | deferred | Deferred to #34 |
| model-012 | medium | Scorer prompt injection via search results | accepted | Inherent to LLM scoring of external content; scorer output is a bounded int (0-100) with reason truncation at 120 chars. Risk is manipulated scores, not data exfiltration. |
| model-013 | medium | Demo user weak credentials | accepted | Demo user exists only when `SEED_DEMO=1` (dev convenience). Production should not set it. |
| model-014 | medium | No input length limits | deferred | Deferred to #35 |
| model-015 | medium | CI no explicit permissions | fixed | Fixed in this commit — added `permissions: contents: read` to `ci.yml`. |
| model-016 | low | ICS token no rotation | deferred | Deferred to #36 |
| model-017 | low | CORS allows all methods/headers | deferred | Deferred to #36 |
| model-018 | low | Pipeline error stored verbatim | accepted | Run records are not exposed via any API endpoint; only visible in database. |
| model-019 | info | DATABASE_URL defaults to SQLite | accepted | Dev convenience; production always sets DATABASE_URL via compose or env. |
| model-020 | info | Events status filter accepts arbitrary strings | fixed | Fixed in this commit — added validation against `EventStatus` values. |

## Recommended follow-up

- Snyk Agent Scan for dependency vulnerability analysis (requires account signup; not performed)
