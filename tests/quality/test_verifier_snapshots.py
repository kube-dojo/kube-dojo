"""Hermetic tests for scripts/quality/verifier_snapshots.py.

All subprocess.run calls are mocked; no real commands are executed.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.quality.verifier_snapshots import (
    CommandResult,
    _module_key,
    is_allowed,
    run_command,
    snapshot_module,
)


# ---------------------------------------------------------------------------
# Allowlist tests
# ---------------------------------------------------------------------------

class TestAllowlist:
    def test_kubectl_get_allowed(self):
        assert is_allowed("kubectl get pods")

    def test_kubectl_get_yaml_allowed(self):
        assert is_allowed("kubectl get pods -o yaml")

    def test_kubectl_get_json_allowed(self):
        assert is_allowed("kubectl get deployment my-app -o json")

    def test_kubectl_describe_allowed(self):
        assert is_allowed("kubectl describe pod my-pod")

    def test_kubectl_version_allowed(self):
        assert is_allowed("kubectl version --client")

    def test_kubectl_explain_allowed(self):
        assert is_allowed("kubectl explain pod.spec.containers")

    def test_kubectl_apply_dry_run_allowed(self):
        assert is_allowed("kubectl apply --dry-run=client -f pod.yaml")

    def test_kubectl_create_dry_run_allowed(self):
        assert is_allowed("kubectl create deployment nginx --image=nginx --dry-run=client")

    def test_helm_template_allowed(self):
        assert is_allowed("helm template my-release ./mychart")

    def test_helm_version_allowed(self):
        assert is_allowed("helm version")

    def test_kind_get_clusters_allowed(self):
        assert is_allowed("kind get clusters")

    def test_k3d_version_allowed(self):
        assert is_allowed("k3d version")

    def test_k3d_help_flag_allowed(self):
        assert is_allowed("k3d cluster --help")


# ---------------------------------------------------------------------------
# Denylist tests
# ---------------------------------------------------------------------------

class TestDenylist:
    def test_kubectl_delete_no_dry_run_denied(self):
        assert not is_allowed("kubectl delete pod my-pod")

    def test_kubectl_delete_with_dry_run_allowed(self):
        assert is_allowed("kubectl delete pod my-pod --dry-run=client")

    def test_kubectl_apply_force_denied(self):
        assert not is_allowed("kubectl apply --force -f pod.yaml")

    def test_rm_command_denied(self):
        assert not is_allowed("rm -rf /tmp/foo")

    def test_kill_command_denied(self):
        assert not is_allowed("kill -9 1234")

    def test_unknown_command_denied(self):
        assert not is_allowed("curl https://example.com")

    def test_docker_denied(self):
        assert not is_allowed("docker run --rm nginx")

    def test_empty_line_denied(self):
        assert not is_allowed("")

    def test_comment_only_denied(self):
        assert not is_allowed("# kubectl get pods")


# ---------------------------------------------------------------------------
# Shell-metachar regression tests (blocker from sonnet R1 review)
# ---------------------------------------------------------------------------

class TestShellMetacharDenial:
    def test_pipe_with_delete_is_denied(self):
        # Piped command: shlex sees cmd='kubectl', sub='get' → allowlist passes
        # without the metachar check.  The metachar check must fire first.
        assert not is_allowed("kubectl get pods | xargs kubectl delete pod")

    def test_redirect_to_file_is_denied(self):
        assert not is_allowed("kubectl get pods > /tmp/dump.yaml")

    def test_semicolon_chain_with_rm_is_denied(self):
        assert not is_allowed("kubectl version ; rm -rf /tmp")

    def test_kubectl_delete_with_dry_run_client_is_allowed(self):
        assert is_allowed("kubectl delete -f manifest.yaml --dry-run=client")

    def test_kubectl_delete_without_dry_run_is_denied(self):
        assert not is_allowed("kubectl delete -f manifest.yaml")

    def test_command_substitution_is_denied(self):
        assert not is_allowed("echo $(kubectl get pods -o name)")


# ---------------------------------------------------------------------------
# Timeout handling
# ---------------------------------------------------------------------------

class TestRunCommand:
    def test_timeout_returns_sentinel(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("kubectl", 30)):
            result = run_command("kubectl version --client")
        assert result.exit_code == -1
        assert "TIMEOUT" in result.output

    def test_success_captures_stdout_and_stderr(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Client Version: v1.29.0\n"
        mock_proc.stderr = ""
        with patch("subprocess.run", return_value=mock_proc):
            result = run_command("kubectl version --client")
        assert result.exit_code == 0
        assert "Client Version" in result.output

    def test_exception_captured(self):
        with patch("subprocess.run", side_effect=OSError("no such file")):
            result = run_command("kubectl version --client")
        assert result.exit_code == -2
        assert "ERROR" in result.output


# ---------------------------------------------------------------------------
# Snapshot path layout
# ---------------------------------------------------------------------------

class TestSnapshotPathLayout:
    def _make_module(self, tmp_path: Path, content: str) -> Path:
        module = tmp_path / "test-module.md"
        module.write_text(content, encoding="utf-8")
        return module

    def _fixed_run(self, output: str = "Client Version: v1.29.0") -> MagicMock:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = output
        mock_proc.stderr = ""
        return mock_proc

    def test_snapshot_directory_is_module_key(self, tmp_path: Path):
        module = self._make_module(tmp_path, "---\ntitle: Test\n---\n\n```bash\nkubectl version --client\n```")
        snap_dir = tmp_path / "snapshots"
        with patch("subprocess.run", return_value=self._fixed_run()):
            result = snapshot_module(module, out_dir=snap_dir)
        assert result is not None
        assert result.parent.name == _module_key(module)

    def test_snapshot_filename_is_today(self, tmp_path: Path):
        module = self._make_module(tmp_path, "---\ntitle: Test\n---\n\n```bash\nkubectl version --client\n```")
        snap_dir = tmp_path / "snapshots"
        with patch("subprocess.run", return_value=self._fixed_run()):
            result = snapshot_module(module, out_dir=snap_dir)
        assert result is not None
        assert result.name == f"{date.today().isoformat()}.txt"

    def test_no_allowed_commands_returns_none(self, tmp_path: Path):
        module = self._make_module(
            tmp_path,
            "---\ntitle: Test\n---\n\n```bash\ncurl https://example.com\nrm -rf /tmp\n```",
        )
        result = snapshot_module(module, out_dir=tmp_path / "snapshots")
        assert result is None

    def test_non_bash_blocks_skipped(self, tmp_path: Path):
        module = self._make_module(
            tmp_path,
            "---\ntitle: Test\n---\n\n```yaml\nkubectl get pods\n```\n\n```python\nkubectl get pods\n```\n\n```bash\nkubectl version --client\n```",
        )
        snap_dir = tmp_path / "snapshots"
        with patch("subprocess.run", return_value=self._fixed_run()) as mock_run:
            result = snapshot_module(module, out_dir=snap_dir)
        assert result is not None
        # subprocess.run called exactly once — yaml and python blocks were skipped
        assert mock_run.call_count == 1

    def test_snapshot_contains_sha256_header(self, tmp_path: Path):
        module = self._make_module(tmp_path, "---\ntitle: Test\n---\n\n```bash\nkubectl version --client\n```")
        snap_dir = tmp_path / "snapshots"
        with patch("subprocess.run", return_value=self._fixed_run()):
            result = snapshot_module(module, out_dir=snap_dir)
        assert result is not None
        text = result.read_text()
        assert any(line.startswith("# SHA256:") for line in text.splitlines())


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_same_output_same_hash(self, tmp_path: Path):
        """Same command output → identical SHA256 across two independent runs."""
        module = tmp_path / "mod.md"
        module.write_text(
            "---\ntitle: Test\n---\n\n```bash\nkubectl version --client\n```",
            encoding="utf-8",
        )
        fixed_output = "Client Version: v1.29.0"
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = fixed_output
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc):
            r1 = snapshot_module(module, out_dir=tmp_path / "snap1")
        with patch("subprocess.run", return_value=mock_proc):
            r2 = snapshot_module(module, out_dir=tmp_path / "snap2")

        assert r1 is not None and r2 is not None

        def sha_line(path: Path) -> str:
            for line in path.read_text().splitlines():
                if line.startswith("# SHA256:"):
                    return line
            return ""

        assert sha_line(r1) == sha_line(r2)
        assert sha_line(r1) != ""
