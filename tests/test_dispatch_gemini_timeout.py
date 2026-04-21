from __future__ import annotations

import io
import signal
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import dispatch


def test_dispatch_gemini_starts_new_session():
    proc = MagicMock()
    proc.stdin = io.StringIO()
    proc.stdout = io.StringIO()
    proc.stderr = io.StringIO()
    proc.wait.return_value = 0
    proc.returncode = 0

    with patch("dispatch.subprocess.Popen", return_value=proc) as popen_mock, patch(
        "dispatch._stream_with_timeout", return_value=(["ok"], False)
    ), patch("dispatch._log"):
        ok, output = dispatch.dispatch_gemini("prompt", model="gemini-3-flash-preview")

    assert ok is True
    assert output == "ok"
    assert popen_mock.call_args.kwargs["start_new_session"] is True


def test_stream_timeout_kills_process_group_first():
    proc = MagicMock()
    proc.pid = 12345

    with patch("dispatch.os.killpg") as killpg:
        dispatch._kill_process_tree(proc)

    killpg.assert_called_once_with(12345, signal.SIGKILL)
    proc.kill.assert_not_called()


def test_stream_timeout_falls_back_to_proc_kill():
    proc = MagicMock()
    proc.pid = 12345

    with patch("dispatch.os.killpg", side_effect=OSError):
        dispatch._kill_process_tree(proc)

    proc.kill.assert_called_once()


def test_gemini_quiet_mode_defaults_on_in_pipeline_mode(monkeypatch):
    monkeypatch.delenv("KUBEDOJO_QUIET", raising=False)
    monkeypatch.setenv("KUBEDOJO_PIPELINE", "1")

    assert dispatch._gemini_quiet_mode_enabled() is True


def test_gemini_quiet_mode_defaults_off_outside_pipeline(monkeypatch):
    monkeypatch.delenv("KUBEDOJO_QUIET", raising=False)
    monkeypatch.delenv("KUBEDOJO_PIPELINE", raising=False)

    assert dispatch._gemini_quiet_mode_enabled() is False
