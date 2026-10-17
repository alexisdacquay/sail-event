# Semgrep Scan Summary

- **Version**: 1.181.0
- **Command**: `uvx semgrep --config auto --json backend/`
- **Date**: 2026-10-16
- **Findings**: 2

## Findings

| # | Rule ID | File | Line | Severity |
|---|---------|------|------|----------|
| 1 | `python.lang.compatibility.python37.python37-compatibility-importlib2` | `backend/app/adapters/fixture.py` | 5 | ERROR |
| 2 | `python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected` | `backend/app/adapters/search_tavily.py` | 96 | WARNING |

### Finding 1 — importlib.resources compatibility

`importlib.resources` requires Python 3.7+. The project targets Python 3.12 (`pyproject.toml`), so this is not a real issue.

### Finding 2 — dynamic urllib use

`urllib.request.urlopen()` with a dynamic URL in `search_tavily.py`. The URL is constructed from a hardcoded `https://api.tavily.com/search` base — not user-controlled. The `file://` scheme risk does not apply because the URL is not derived from user input.
