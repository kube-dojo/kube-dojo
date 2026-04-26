from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.adapters.claude import ClaudeAdapter
from dispatch import dispatch_claude


SPECIAL_PROMPT = """--monitor snapshot
{"--foo": "bar", "note": "keep this out of argv"}
Shell metacharacters: $(echo nope); `uname`; | & > < *
"""


def _completed_process(cmd: list[str], *, stdout: str = "ok", stderr: str = ""):
    return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr=stderr)


def test_dispatch_claude_pipes_special_prompt_to_stdin(monkeypatch):
    captured: dict[str, object] = {}

    def fake_run_with_process_group(cmd, prompt, timeout, cwd, env):
        captured["cmd"] = cmd
        captured["prompt"] = prompt
        return _completed_process(cmd)

    monkeypatch.setattr("dispatch._run_with_process_group", fake_run_with_process_group)
    monkeypatch.setattr("dispatch._log", lambda *args, **kwargs: None)
    monkeypatch.setattr("dispatch._is_claude_peak_hours", lambda: False)
    monkeypatch.setattr("dispatch._check_claude_budget", lambda: None)
    monkeypatch.setattr("dispatch._claude_call_count", 0)

    ok, output = dispatch_claude(SPECIAL_PROMPT, model="claude-test", timeout=1)

    assert ok is True
    assert output == "ok"
    assert captured["prompt"] == SPECIAL_PROMPT
    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    assert "-p" in cmd
    assert "--model" in cmd
    assert SPECIAL_PROMPT not in cmd
    assert not any('{"--foo": "bar"' in arg for arg in cmd)
    assert not any("$(echo nope)" in arg for arg in cmd)


def test_claude_runtime_adapter_pipes_special_prompt_to_stdin(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    plan = ClaudeAdapter().build_invocation(
        prompt=SPECIAL_PROMPT,
        mode="read-only",
        cwd=Path.cwd(),
        model="claude-test",
        task_id=None,
        session_id=None,
        tool_config={"cmd_prefix": ["claude"], "use_bare": False},
    )

    assert plan.stdin_payload == SPECIAL_PROMPT
    assert plan.cmd[:2] == ["claude", "-p"]
    assert "--model" in plan.cmd
    assert SPECIAL_PROMPT not in plan.cmd
    assert not any('{"--foo": "bar"' in arg for arg in plan.cmd)
    assert not any("$(echo nope)" in arg for arg in plan.cmd)
