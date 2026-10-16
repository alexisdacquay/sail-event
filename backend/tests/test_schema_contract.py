"""Schema-contract test.

Parses openapi.yaml from disk and compares paths, methods, and
operationIds against the running app's /openapi.json.
Auth endpoints (out of scope until #7) are excluded from the check.
"""

from __future__ import annotations

from pathlib import Path

import yaml


_YAML_PATH = Path(__file__).resolve().parent.parent.parent / "openapi.yaml"
_AUTH_PREFIX = "/api/auth"


def _load_yaml_operations() -> set[tuple[str, str, str]]:
    """Return {(METHOD, path, operationId)} from openapi.yaml."""
    with open(_YAML_PATH) as f:
        spec = yaml.safe_load(f)
    ops: set[tuple[str, str, str]] = set()
    for path, methods in spec["paths"].items():
        for method, detail in methods.items():
            if method.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                ops.add((method.upper(), path, detail["operationId"]))
    return ops


def _load_app_operations(client) -> set[tuple[str, str, str]]:
    """Return {(METHOD, path, operationId)} from /openapi.json."""
    spec = client.get("/openapi.json").json()
    ops: set[tuple[str, str, str]] = set()
    for path, methods in spec["paths"].items():
        for method, detail in methods.items():
            if method.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                ops.add((method.upper(), path, detail.get("operationId", "")))
    return ops


def test_every_non_auth_yaml_path_present_in_app(client):
    yaml_ops = _load_yaml_operations()
    app_ops = _load_app_operations(client)
    non_auth = {t for t in yaml_ops if not t[1].startswith(_AUTH_PREFIX)}
    missing = non_auth - app_ops
    assert missing == set(), f"In openapi.yaml but not in app: {missing}"


def test_app_has_no_extra_non_yaml_paths(client):
    yaml_ops = _load_yaml_operations()
    app_ops = _load_app_operations(client)
    extra = app_ops - yaml_ops
    assert extra == set(), f"In app but not in openapi.yaml: {extra}"
