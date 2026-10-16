"""SPA fallback: unknown /api paths get 404 JSON, non-API paths get index.html."""

from __future__ import annotations

from pathlib import Path

import pytest

_DIST_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
_has_dist = _DIST_DIR.is_dir()


@pytest.mark.skipif(not _has_dist, reason="frontend/dist not built")
def test_unknown_api_path_returns_404_json(client):
    r = client.get("/api/nope")
    assert r.status_code == 404
    assert r.json() == {"detail": "Not found"}


@pytest.mark.skipif(not _has_dist, reason="frontend/dist not built")
def test_non_api_path_returns_spa_html(client):
    r = client.get("/some/deep/path")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert 'id="root"' in r.text
