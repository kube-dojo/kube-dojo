"""Regression tests for dispatch_qwen hermes argv (--oneshot= equals-form)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


def _load_dispatch():
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location("dispatch", SCRIPTS_DIR / "dispatch.py")
    dispatch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dispatch)  # type: ignore[union-attr]
    return dispatch


def _capture_qwen_cmd(**kwargs) -> list[str]:
    dispatch = _load_dispatch()
    captured_cmd: list[str] = []

    class FakeResult:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(cmd, *_args, **_kwargs):
        captured_cmd.extend(cmd)
        return FakeResult()

    dispatch._run_with_process_group = fake_run  # type: ignore[attr-defined]
    defaults = {
        "prompt": "hello",
        "model": "qwen/qwen3.6-plus",
        "timeout": 10,
    }
    defaults.update(kwargs)
    dispatch.dispatch_qwen(**defaults)
    return captured_cmd


def test_dispatch_qwen_hermes_argv_puts_oneshot_last() -> None:
    """Hermes --oneshot=<prompt> must follow --provider and -m (equals-form)."""
    cmd = _capture_qwen_cmd(prompt="hello")
    assert cmd[-1] == "--oneshot=hello"
    assert "-z" not in cmd
    assert cmd[0] == "hermes"
    assert cmd[cmd.index("-m") + 1] == "qwen/qwen3.6-plus"
    assert cmd[cmd.index("--provider") + 1] == "openrouter"


def test_dispatch_qwen_hermes_argv_handles_flag_like_prompt() -> None:
    """Flag-like prompts bind via --oneshot= so argparse never treats them as flags."""
    cmd = _capture_qwen_cmd(prompt="--provider")
    assert "--oneshot=--provider" in cmd
    assert "-z" not in cmd
