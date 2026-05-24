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


def _load_local_api():
    module_path = Path(__file__).resolve().parent.parent / "scripts" / "local_api.py"
    spec = importlib.util.spec_from_file_location("local_api_repo_guard", module_path)
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


def test_build_healthz_payload_fails_on_stale_api_pid(tmp_path: Path) -> None:
    repo_guard = _load_repo_guard()
    pid_dir = tmp_path / ".pids"
    pid_dir.mkdir()
    (pid_dir / "api.pid").write_text("999999999", encoding="utf-8")

    payload = repo_guard.build_healthz_payload(tmp_path)

    assert payload["ok"] is False
    assert any("dead process" in warning for warning in payload["warnings"])


def test_malformed_pid_file_content(tmp_path: Path) -> None:
    repo_guard = _load_repo_guard()
    pid_dir = tmp_path / ".pids"
    pid_dir.mkdir()
    (pid_dir / "api.pid").write_text("not-a-pid", encoding="utf-8")

    payload = repo_guard.build_healthz_payload(tmp_path)

    assert payload["ok"] is False
    assert any("unreadable" in warning for warning in payload["warnings"])


def test_unreadable_pid_file_oserror(tmp_path: Path) -> None:
    repo_guard = _load_repo_guard()
    pid_dir = tmp_path / ".pids"
    pid_dir.mkdir()
    pid_file = pid_dir / "api.pid"
    pid_file.write_text("12345", encoding="utf-8")
    pid_file.chmod(0o000)

    try:
        payload = repo_guard.build_healthz_payload(tmp_path)
    finally:
        pid_file.chmod(0o644)

    assert payload["ok"] is False
    assert any("unreadable" in warning for warning in payload["warnings"])


def test_inspect_repo_root_warns_when_not_primary(tmp_path: Path, monkeypatch) -> None:
    repo_guard = _load_repo_guard()
    primary = tmp_path / "primary"
    primary.mkdir()
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    monkeypatch.setattr(repo_guard, "resolve_primary_repo_root", lambda _start=None: primary)

    inspection = repo_guard.inspect_repo_root(worktree)

    assert inspection["repo_root"] == str(worktree.resolve())
    assert inspection["primary_repo_root"] == str(primary.resolve())
    assert any("not the primary checkout" in warning for warning in inspection["warnings"])
    assert repo_guard.build_healthz_payload(worktree)["ok"] is False


def test_inspect_repo_root_worktree_cwd_is_informational(tmp_path: Path, monkeypatch) -> None:
    repo_guard = _load_repo_guard()
    worktree = tmp_path / ".worktrees" / "sample"
    worktree.mkdir(parents=True)
    monkeypatch.chdir(worktree)

    inspection = repo_guard.inspect_repo_root(tmp_path)

    assert any("git worktree" in warning for warning in inspection["warnings"])
    assert repo_guard.build_healthz_payload(tmp_path)["ok"] is True


def test_healthz_route_uses_repo_guard(tmp_path: Path) -> None:
    local_api = _load_local_api()
    status, body, content_type = local_api.route_request(tmp_path, "/healthz")
    assert status == 200
    assert content_type == "application/json; charset=utf-8"
    assert body["ok"] is True
    assert "warnings" in body


def test_schema_documents_healthz_contract() -> None:
    local_api = _load_local_api()
    schema = local_api.build_api_schema()
    healthz = next(entry for entry in schema["endpoints"] if entry["path"] == "/healthz")
    assert healthz["fields"] == ["ok", "repo_root", "primary_repo_root", "warnings"]
    assert "dead/unreadable" in healthz["desc"]


def test_schema_documents_runtime_services_repo_field() -> None:
    local_api = _load_local_api()
    schema = local_api.build_api_schema()
    runtime = next(entry for entry in schema["endpoints"] if entry["path"] == "/api/runtime/services")
    assert runtime["fields"] == ["running", "stopped", "stale", "total", "services", "repo"]
    assert runtime["repo"]["fields"] == [
        "repo_root",
        "primary_repo_root",
        "process_cwd",
        "warnings",
    ]
    assert "inspect_repo_root" in runtime["repo"]["desc"]
