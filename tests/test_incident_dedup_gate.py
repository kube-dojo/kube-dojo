from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_SCRIPT = REPO_ROOT / "scripts/quality/incident_dedup_gate.py"
PYTHON_BIN = shutil.which("python3") or shutil.which("python") or "python"


def _git(repo: Path, args: list[str]) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_repo_with_scripts(repo: Path) -> None:
    scripts_dir = repo / "scripts"
    quality_dir = scripts_dir / "quality"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    quality_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / "scripts" / "check_incident_reuse.py", scripts_dir / "check_incident_reuse.py")
    shutil.copy(REPO_ROOT / "scripts" / "audit_incident_reuse.py", scripts_dir / "audit_incident_reuse.py")
    shutil.copy(GATE_SCRIPT, quality_dir / "incident_dedup_gate.py")

    _git(repo, ["init", "-b", "main"])
    _git(repo, ["config", "user.email", "test@example.com"])
    _git(repo, ["config", "user.name", "test"])
    _git(repo, ["add", "scripts"])
    _git(repo, ["commit", "-m", "add incident scripts"])


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _commit(repo: Path, path: str, content: str, message: str) -> None:
    target = repo / path
    _write_text(target, content)
    _git(repo, ["add", path])
    _git(repo, ["commit", "-m", message])


def _branch(repo: Path, name: str) -> None:
    _git(repo, ["checkout", "-b", name])


def _run_gate(repo: Path, *, base: str = "main", mode: str = "delta", emit_json: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = [PYTHON_BIN, str(repo / "scripts/quality/incident_dedup_gate.py"), "--base", base, "--mode", mode]
    if emit_json:
        cmd.append("--json")
    return subprocess.run(
        cmd,
        cwd=repo,
        capture_output=True,
        text=True,
    )


VIOLATION_UBER = "Uber had a security event with MFA fatigue in 2022.\n"
VIOLATION_TARGET = "Target had an HVAC-related incident around the 2013 breach.\n"
VIOLATION_NONE = "This module contains only generic conceptual guidance.\n"


def _parse_gate_payload(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.returncode in (0, 1)
    payload = json.loads(result.stdout)
    assert isinstance(payload, dict)
    return payload


def test_delta_mode_pass_when_set_is_identical(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_scripts(repo)
    _commit(repo, "src/content/docs/module.md", VIOLATION_UBER, "seed base")
    _branch(repo, "delta-identical")

    result = _run_gate(repo, base="main", mode="delta", emit_json=False)
    assert result.returncode == 0


def test_delta_mode_fails_when_new_triple_added(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_scripts(repo)
    _commit(repo, "src/content/docs/module.md", VIOLATION_UBER, "seed base")
    _branch(repo, "delta-new-triple")
    _commit(repo, "src/content/docs/new/module.md", VIOLATION_TARGET, "add new triple")

    result = _run_gate(repo, base="main", mode="delta", emit_json=True)
    payload = _parse_gate_payload(result)
    assert result.returncode == 1
    assert payload["status"] == "fail"
    assert payload["mode"] == "delta"
    assert ["duplicate", "Target 2013 breach", "src/content/docs/new/module.md"] in payload["added"]


def test_delta_mode_pass_when_old_triple_removed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_scripts(repo)
    _commit(repo, "src/content/docs/module.md", VIOLATION_UBER, "seed base")
    _branch(repo, "delta-removed")
    _commit(repo, "src/content/docs/module.md", VIOLATION_NONE, "remove violation")

    result = _run_gate(repo, base="main", mode="delta", emit_json=True)
    payload = _parse_gate_payload(result)
    assert result.returncode == 0
    assert payload["status"] == "pass"
    assert payload["added"] == []


def test_delta_mode_fails_when_old_replaced_by_different_triple(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_scripts(repo)
    _commit(repo, "src/content/docs/module.md", VIOLATION_UBER, "seed base")
    _branch(repo, "delta-replace")
    _commit(repo, "src/content/docs/module.md", VIOLATION_NONE, "remove old violation")
    _commit(repo, "src/content/docs/other/module.md", VIOLATION_TARGET, "add replacement violation")

    result = _run_gate(repo, base="main", mode="delta", emit_json=True)
    payload = _parse_gate_payload(result)
    assert result.returncode == 1
    assert payload["status"] == "fail"
    assert ["duplicate", "Target 2013 breach", "src/content/docs/other/module.md"] in payload["added"]
    assert ["duplicate", "Uber 2022 hardcoded credentials", "src/content/docs/module.md"] in payload["removed"]


def test_absolute_mode_fails_when_any_after_violation_exists(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_scripts(repo)
    _commit(repo, "src/content/docs/module.md", VIOLATION_NONE, "seed base")
    _branch(repo, "absolute-fails")
    _commit(repo, "src/content/docs/new/module.md", VIOLATION_UBER, "add violation")

    result = _run_gate(repo, base="main", mode="absolute", emit_json=True)
    payload = _parse_gate_payload(result)
    assert result.returncode == 1
    assert payload["status"] == "fail"
    assert payload["mode"] == "absolute"
    assert payload["after_count"] == 1
