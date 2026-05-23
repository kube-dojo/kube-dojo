from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def test_hermes_provider_auto_detection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ai_agent_bridge import _hermes

    monkeypatch.delenv("KUBEDOJO_HERMES_PROVIDER", raising=False)

    assert _hermes._detect_provider("claude-sonnet-4-6") == "anthropic"
    assert _hermes._detect_provider("claude-opus-4-6") == "anthropic"
    assert _hermes._detect_provider("grok-4.3") == "xai"
    assert _hermes._detect_provider("openrouter/qwen/qwen3.7-max") == "openrouter"
    assert _hermes._detect_provider("qwen-3.6-flash") == "openrouter"

    monkeypatch.setenv("KUBEDOJO_HERMES_PROVIDER", "local-test")

    assert _hermes._detect_provider("claude-sonnet-4-6") == "local-test"


def test_openrouter_prefix_routes_to_openrouter() -> None:
    from scripts.ai_agent_bridge._hermes import _detect_provider

    assert (
        _detect_provider("openrouter/anthropic/claude-opus-4-6")
        == "openrouter"
    )
    assert _detect_provider("openrouter/qwen/qwen3.7-max") == "openrouter"


def test_opencode_command_construction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from ai_agent_bridge import _opencode

    captured: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(cmd, 0, stdout="OPENCODE OK\n", stderr="")

    monkeypatch.setenv("KUBEDOJO_OPENCODE_CMD", "opencode")
    monkeypatch.setattr(_opencode.subprocess, "run", fake_run)

    ok, response, stderr = _opencode._invoke_opencode(
        "prompt",
        "openrouter/qwen/qwen3.7-max",
        timeout_s=3,
        cwd=tmp_path,
    )

    assert ok is True
    assert response == "OPENCODE OK"
    assert stderr == ""
    assert captured["cmd"] == [
        "opencode",
        "run",
        "-m",
        "openrouter/qwen/qwen3.7-max",
        "-",
    ]
    assert captured["kwargs"]["input"] == "prompt"
    assert captured["kwargs"]["cwd"] == tmp_path
    assert captured["kwargs"]["timeout"] == 3
    assert captured["kwargs"]["capture_output"] is True


def test_hermes_command_construction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from ai_agent_bridge import _hermes

    captured: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(cmd, 0, stdout="HERMES OK\n", stderr="")

    monkeypatch.setenv("KUBEDOJO_HERMES_CMD", "hermes")
    monkeypatch.delenv("KUBEDOJO_HERMES_PROVIDER", raising=False)
    monkeypatch.setattr(_hermes.subprocess, "run", fake_run)

    ok, response, stderr = _hermes._invoke_hermes(
        "prompt",
        "claude-sonnet-4-6",
        timeout_s=3,
        cwd=tmp_path,
    )

    assert ok is True
    assert response == "HERMES OK"
    assert stderr == ""
    assert captured["cmd"] == [
        "hermes",
        "-z",
        "prompt",
        "--provider",
        "anthropic",
        "-m",
        "claude-sonnet-4-6",
    ]
    assert captured["kwargs"]["input"] == ""
    assert captured["kwargs"]["cwd"] == tmp_path
    assert captured["kwargs"]["timeout"] == 3
    assert captured["kwargs"]["capture_output"] is True


def test_hermes_qwen_route_label_maps_to_cli_model(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from ai_agent_bridge import _hermes

    captured: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(cmd, 0, stdout="HERMES OK\n", stderr="")

    monkeypatch.setenv("KUBEDOJO_HERMES_CMD", "hermes")
    monkeypatch.delenv("KUBEDOJO_HERMES_PROVIDER", raising=False)
    monkeypatch.setattr(_hermes.subprocess, "run", fake_run)

    ok, response, stderr = _hermes._invoke_hermes(
        "prompt",
        "qwen-3.6-flash",
        timeout_s=3,
        cwd=tmp_path,
    )

    assert ok is True
    assert response == "HERMES OK"
    assert stderr == ""
    assert captured["cmd"] == [
        "hermes",
        "-z",
        "prompt",
        "--provider",
        "openrouter",
        "-m",
        "qwen/qwen3.6-flash",
    ]
    assert captured["kwargs"]["input"] == ""


def test_task_classes_include_opencode_and_hermes() -> None:
    from dispatch_smart import SUPPORTED_AGENTS, TASK_CLASSES

    expected = {
        "search": {
            "opencode": "openrouter/qwen/qwen3.6-flash",
            "hermes": "qwen-3.6-flash",
        },
        "edit": {
            "opencode": "openrouter/qwen/qwen3.7-max",
            "hermes": "grok-4.3",
        },
        "draft": {
            "opencode": "openrouter/qwen/qwen3.7-max",
            "hermes": "grok-4.3",
        },
        "review": {
            "opencode": "openrouter/qwen/qwen3.7-max",
            "hermes": "claude-sonnet-4-6",
        },
        "architect": {
            "opencode": "openrouter/anthropic/claude-sonnet-4.5",
            "hermes": "claude-opus-4-6",
        },
    }

    assert "opencode" in SUPPORTED_AGENTS
    assert "hermes" in SUPPORTED_AGENTS
    for task_class, models in expected.items():
        for agent, model in models.items():
            assert TASK_CLASSES[task_class].models[agent] == model
