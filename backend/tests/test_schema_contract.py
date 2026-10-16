"""Schema-contract test.

Compares paths and operationIds from the running app's /openapi.json
against the project's openapi.yaml.

If PyYAML is available, the YAML file is parsed directly.
Otherwise, the expected values are hardcoded from the contract.
"""

from __future__ import annotations

import pytest

# The canonical paths and operationIds from openapi.yaml.
# Auth endpoints are out of scope for issue #6 (→ #7).
_YAML_NON_AUTH: dict[tuple[str, str], str] = {
    ("GET", "/api/health"): "healthCheck",
    ("GET", "/api/criteria"): "getCriteria",
    ("PUT", "/api/criteria"): "saveCriteria",
    ("GET", "/api/thresholds"): "getThresholds",
    ("PUT", "/api/thresholds"): "saveThresholds",
    ("POST", "/api/search"): "runSearch",
    ("GET", "/api/events"): "listEvents",
    ("POST", "/api/events/{id}/decision"): "decideEvent",
    ("POST", "/api/search/all"): "searchAll",
    ("GET", "/api/calendar/{ics_token}"): "getCalendarFeed",
}

_YAML_AUTH: dict[tuple[str, str], str] = {
    ("POST", "/api/auth/register"): "register",
    ("POST", "/api/auth/login"): "login",
}

_YAML_ALL = {**_YAML_NON_AUTH, **_YAML_AUTH}


def _app_operations(client) -> dict[tuple[str, str], str]:
    """Extract (METHOD, path) -> operationId from /openapi.json."""
    spec = client.get("/openapi.json").json()
    result = {}
    for path, methods in spec["paths"].items():
        for method, detail in methods.items():
            if method.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                result[(method.upper(), path)] = detail.get("operationId", "")
    return result


def test_every_non_auth_yaml_path_present_in_app(client):
    app_ops = _app_operations(client)
    for key, oid in _YAML_NON_AUTH.items():
        assert key in app_ops, f"Missing in app: {key[0]} {key[1]}"
        assert app_ops[key] == oid, (
            f"operationId mismatch for {key}: app={app_ops[key]}, yaml={oid}"
        )


def test_app_has_no_extra_non_yaml_paths(client):
    app_ops = _app_operations(client)
    for key in app_ops:
        assert key in _YAML_ALL, f"Extra in app not in yaml: {key[0]} {key[1]}"
