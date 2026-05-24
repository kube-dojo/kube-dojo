from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_repo_guard():
    module_path = Path(__file__).resolve().parent.parent / "scripts" / "local_api" / "repo_guard.py"
    spec = importlib.util.spec_from_file_location("repo_guard_test", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_healthz_payload_ok_on_clean_tmp_path(tmp_path: Path) -> None:
    repo_guard = _load_repo_guard()
    payload = repo_guard.build_healthz_payload(tmp_path)
    assert payload["ok"] is True
    assert payload["repo_root"] == str(tmp_path.resolve())
    assert not any("dead process" in warning for warning in payload["warnings"])


def test_healthz_route_uses_repo_guard(tmp_path: Path) -> None:
    local_api_path = Path(__file__).resolve().parent.parent / "scripts" / "local_api.py"
    spec = importlib.util.spec_from_file_location("local_api_healthz", local_api_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    status, body, content_type = module.route_request(tmp_path, "/healthz")
    assert status == 200
    assert content_type == "application/json; charset=utf-8"
    assert body["ok"] is True
    assert "warnings" in body
