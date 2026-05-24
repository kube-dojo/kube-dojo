"""Regression tests for the local-API Activity page split."""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parent.parent / "scripts" / "local_api.py"
    spec = importlib.util.spec_from_file_location("local_api_activity", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


local_api = _load_module()


def _route(tmp_path: Path, path: str) -> str:
    status, body, content_type = local_api.route_request(tmp_path, path)
    assert status == 200
    assert "text/html" in content_type
    return body


def test_activity_route_returns_real_page_with_filters(tmp_path: Path) -> None:
    html = _route(tmp_path, "/activity")
    assert 'id="activity-body"' in html
    assert '<a class="navlink active" href="/activity"' in html
    assert 'id="activity-track-filter"' in html
    assert 'id="activity-agent-filter"' in html
    for label in ["Fundamentals", "Cloud", "Certifications", "Platform", "Other"]:
        assert f">{label}</option>" in html
    for label in ["claude", "codex", "gemini", "grok", "deepseek", "qwen", "cursor", "composer", "autopilot"]:
        assert f">{label}</option>" in html


def test_dashboard_does_not_embed_full_activity_feed(tmp_path: Path) -> None:
    html = _route(tmp_path, "/")
    assert 'id="activity-body"' not in html
    assert 'id="activity-badge"' not in html
    assert "activity-feed" not in html


def test_dashboard_activity_summary_links_to_full_page(tmp_path: Path) -> None:
    html = _route(tmp_path, "/")
    assert 'class="activity-summary-card" href="/activity"' in html
    assert 'id="activity-summary-items"' in html
    assert "fetchJson('/api/activity?limit=3')" in html
    summary_markup = html.split('id="activity-summary-items"', 1)[1].split("</ul>", 1)[0]
    assert len(re.findall(r'class="activity-summary-item"', summary_markup)) <= 3
