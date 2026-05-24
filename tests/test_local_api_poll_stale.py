from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parent.parent / "scripts" / "local_api.py"
    spec = importlib.util.spec_from_file_location("local_api_poll_stale", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_ui_fragments():
    module_path = (
        Path(__file__).resolve().parent.parent / "scripts" / "local_api" / "routes" / "ui_fragments.py"
    )
    spec = importlib.util.spec_from_file_location("ui_fragments_poll_stale", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


local_api = _load_module()
ui_fragments = _load_ui_fragments()


POLL_PAGES = ("/", "/operator", "/pipeline", "/activity", "/health", "/quality")


def test_poll_stale_script_marks_elements_older_than_24h() -> None:
    script = ui_fragments.render_poll_stale_script()
    assert "setPollTs" in script
    assert "poll-stale" in script
    assert "24 * 60 * 60 * 1000" in script


def test_auto_refresh_pages_include_poll_stale_assets(tmp_path: Path) -> None:
    for route in POLL_PAGES:
        status, body, content_type = local_api.route_request(tmp_path, route)
        assert status == 200, route
        assert "text/html" in content_type, route
        assert ".poll-stale" in body, route
        assert "setPollTs" in body, route
        assert "markStalePolls" in body, route


def test_auto_refresh_pages_wire_set_poll_ts_in_refresh_handlers(tmp_path: Path) -> None:
    status, body, _ = local_api.route_request(tmp_path, "/operator")
    assert status == 200
    assert "setPollTs($('#last-updated'), briefing)" in body

    status, body, _ = local_api.route_request(tmp_path, "/quality")
    assert status == 200
    assert "setPollTs($('#last-updated'), board)" in body
