"""Unit tests for the ``DeepSeekAdapter`` Hermes integration."""
from __future__ import annotations

from pathlib import Path

from agent_runtime.adapters.deepseek import DeepSeekAdapter


def test_build_invocation_read_only(monkeypatch) -> None:
    monkeypatch.setattr("agent_runtime.adapters.deepseek.shutil.which", lambda _: "hermes")
    adapter = DeepSeekAdapter()
    plan = adapter.build_invocation(
        prompt="p",
        mode="read-only",
        cwd=Path("/tmp"),
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    cmd = plan.cmd
    assert cmd == [
        "hermes",
        "-m",
        "deepseek-v4-pro",
        "--provider",
        "deepseek",
        "-t",
        "web,browser",
        "--oneshot=p",
    ]
    assert "--yolo" not in cmd
    assert "-z" not in cmd


def test_build_invocation_workspace_write(monkeypatch) -> None:
    monkeypatch.setattr("agent_runtime.adapters.deepseek.shutil.which", lambda _: "hermes")
    adapter = DeepSeekAdapter()
    plan = adapter.build_invocation(
        prompt="p",
        mode="workspace-write",
        cwd=Path("/tmp"),
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    cmd = plan.cmd
    assert "--yolo" in cmd
    toolsets = cmd[cmd.index("-t") + 1]
    assert toolsets == "web,browser,file,terminal,code_execution,todo"


def test_build_invocation_danger(monkeypatch) -> None:
    monkeypatch.setattr("agent_runtime.adapters.deepseek.shutil.which", lambda _: "hermes")
    adapter = DeepSeekAdapter()
    plan = adapter.build_invocation(
        prompt="p",
        mode="danger",
        cwd=Path("/tmp"),
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    toolsets = plan.cmd[plan.cmd.index("-t") + 1]
    assert "memory" in toolsets
    assert "skills" in toolsets


def test_model_override(monkeypatch) -> None:
    monkeypatch.setattr("agent_runtime.adapters.deepseek.shutil.which", lambda _: "hermes")
    adapter = DeepSeekAdapter()
    plan = adapter.build_invocation(
        prompt="p",
        mode="read-only",
        cwd=Path("/tmp"),
        model="deepseek-v4-flash",
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    assert plan.cmd[plan.cmd.index("-m") + 1] == "deepseek-v4-flash"


def _provider_of(plan) -> str:
    return plan.cmd[plan.cmd.index("--provider") + 1]


def _build(monkeypatch, *, model=None, tool_config=None):
    monkeypatch.setattr("agent_runtime.adapters.deepseek.shutil.which", lambda _: "hermes")
    return DeepSeekAdapter().build_invocation(
        prompt="p",
        mode="read-only",
        cwd=Path("/tmp"),
        model=model,
        task_id=None,
        session_id=None,
        tool_config=tool_config,
    )


def test_provider_default_is_first_party_deepseek(monkeypatch) -> None:
    """No override + bare first-party slug → China-hosted ``deepseek`` provider."""
    monkeypatch.delenv("KUBEDOJO_HERMES_PROVIDER", raising=False)
    plan = _build(monkeypatch)
    assert _provider_of(plan) == "deepseek"
    assert plan.cmd[plan.cmd.index("-m") + 1] == "deepseek-v4-pro"


def test_provider_openrouter_inferred_from_slug(monkeypatch) -> None:
    """An OpenRouter-style ``vendor/model`` slug routes via ``openrouter``."""
    monkeypatch.delenv("KUBEDOJO_HERMES_PROVIDER", raising=False)
    plan = _build(monkeypatch, model="deepseek/deepseek-v3.2-exp")
    assert _provider_of(plan) == "openrouter"
    # The slug is forwarded verbatim to hermes -m.
    assert plan.cmd[plan.cmd.index("-m") + 1] == "deepseek/deepseek-v3.2-exp"


def test_provider_explicit_tool_config_wins(monkeypatch) -> None:
    """Explicit tool_config provider is honored even with a first-party slug."""
    monkeypatch.delenv("KUBEDOJO_HERMES_PROVIDER", raising=False)
    plan = _build(monkeypatch, tool_config={"provider": "openrouter"})
    assert _provider_of(plan) == "openrouter"


def test_provider_env_override(monkeypatch) -> None:
    """KUBEDOJO_HERMES_PROVIDER selects the provider for a default dispatch."""
    monkeypatch.setenv("KUBEDOJO_HERMES_PROVIDER", "openrouter")
    plan = _build(monkeypatch)
    assert _provider_of(plan) == "openrouter"


def test_provider_explicit_beats_env(monkeypatch) -> None:
    """Explicit tool_config provider takes precedence over the env override."""
    monkeypatch.setenv("KUBEDOJO_HERMES_PROVIDER", "openrouter")
    plan = _build(monkeypatch, tool_config={"provider": "deepseek"})
    assert _provider_of(plan) == "deepseek"


def test_parse_response_strips_hermes_banner() -> None:
    adapter = DeepSeekAdapter()
    result = adapter.parse_response(
        stdout="💡 Python project detected. Run with hermes -z.\n\nAnswer",
        stderr="",
        returncode=0,
        output_file=None,
        plan=None,
        call_start_time=None,
    )

    assert result.ok is True
    assert result.response == "Answer"


def test_parse_response_detects_rate_limit() -> None:
    adapter = DeepSeekAdapter()
    result = adapter.parse_response(
        stdout="",
        stderr="rate limit exceeded",
        returncode=1,
        output_file=None,
        plan=None,
        call_start_time=None,
    )

    assert result.rate_limited is True
    assert result.ok is False


def test_parse_response_detects_unfulfilled_tool_use_intent() -> None:
    """DS Pro tool-use intent without execution → ok=False, helpful stderr."""
    adapter = DeepSeekAdapter()
    raw = (
        "I'll verify the PR commits first and then systematically review the diff.\n"
        "<bash>gh pr view 1288 --json commits</bash>"
    )
    result = adapter.parse_response(
        stdout=raw,
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.ok is False
    assert result.response == ""
    assert "tool-use intent" in (result.stderr_excerpt or "")
    assert "workspace-write" in (result.stderr_excerpt or "")


def test_parse_response_long_response_with_bash_codeblock_still_passes() -> None:
    """A long real review that happens to quote <bash> in a code block must pass."""
    adapter = DeepSeekAdapter()
    raw = (
        "VERDICT: APPROVE\n\n"
        + "SUMMARY: All criteria met. " * 40
        + "\n\nThe author also added the `<bash>` toolset gating which is correct."
    )
    result = adapter.parse_response(
        stdout=raw,
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.ok is True
    assert result.response.startswith("VERDICT: APPROVE")


def test_deepseek_hermes_argv_puts_oneshot_last(monkeypatch) -> None:
    """Hermes --oneshot=<prompt> must follow --provider and -m (equals-form)."""
    monkeypatch.setattr("agent_runtime.adapters.deepseek.shutil.which", lambda _: "hermes")
    adapter = DeepSeekAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=Path("/tmp"),
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    cmd = plan.cmd
    assert cmd[-1] == "--oneshot=hello"
    assert "-z" not in cmd
    assert cmd[0] == "hermes"
    assert cmd[cmd.index("-m") + 1] == "deepseek-v4-pro"
    assert cmd[cmd.index("--provider") + 1] == "deepseek"


def test_deepseek_hermes_argv_handles_flag_like_prompt(monkeypatch) -> None:
    """Flag-like prompts bind via --oneshot= so argparse never treats them as flags."""
    monkeypatch.setattr("agent_runtime.adapters.deepseek.shutil.which", lambda _: "hermes")
    adapter = DeepSeekAdapter()
    plan = adapter.build_invocation(
        prompt="--provider",
        mode="read-only",
        cwd=Path("/tmp"),
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    cmd = plan.cmd
    assert "--oneshot=--provider" in cmd
    assert "-z" not in cmd
