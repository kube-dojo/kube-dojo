from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.env_sanitize import build_agent_env
from ai_agent_bridge._config import agent_child_env


def _base_env() -> dict[str, str]:
    return {
        "PATH": "/bin:/usr/bin",
        "HOME": "/tmp/home",
        "GITHUB_TOKEN": "github_pat_012345678901234567890123456789",
        "GH_TOKEN": "ghp_012345678901234567890123456789012345",
        "AWS_SECRET_ACCESS_KEY": "aws-secret",
        "NPM_TOKEN": "npm_012345678901234567890123456789",
        "OPENAI_API_KEY": "sk-012345678901234567890123456789",
        "ANTHROPIC_API_KEY": "sk-ant-test-value",
        "GEMINI_API_KEY": "AIza012345678901234567890123456789",
        "GOOGLE_API_KEY": "google-api-key",
        "KUBEDOJO_GEMINI_SUBSCRIPTION": "1",
        "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS": "20000",
        "LEAKY_VALUE": "ghp_012345678901234567890123456789012345",
        "NORMAL_SETTING": "enabled",
    }


def test_generic_agent_env_strips_token_shaped_names_and_values():
    env = build_agent_env(base=_base_env())

    assert env["PATH"] == "/bin:/usr/bin"
    assert env["HOME"] == "/tmp/home"
    assert env["NORMAL_SETTING"] == "enabled"
    assert "GITHUB_TOKEN" not in env
    assert "GH_TOKEN" not in env
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert "NPM_TOKEN" not in env
    assert "LEAKY_VALUE" not in env
    assert "OPENAI_API_KEY" not in env
    assert "ANTHROPIC_API_KEY" not in env
    assert "GEMINI_API_KEY" not in env
    assert "GOOGLE_API_KEY" not in env


def test_provider_env_keeps_only_matching_provider_secret():
    codex_env = build_agent_env(provider="codex", base=_base_env())
    claude_env = build_agent_env(provider="claude", base=_base_env())
    gemini_env = build_agent_env(provider="gemini", base=_base_env())

    assert codex_env["OPENAI_API_KEY"].startswith("sk-")
    assert "ANTHROPIC_API_KEY" not in codex_env
    assert "GEMINI_API_KEY" not in codex_env
    assert "GITHUB_TOKEN" not in codex_env

    assert claude_env["ANTHROPIC_API_KEY"] == "sk-ant-test-value"
    assert "OPENAI_API_KEY" not in claude_env
    assert "GEMINI_API_KEY" not in claude_env
    assert "GH_TOKEN" not in claude_env

    assert gemini_env["GEMINI_API_KEY"].startswith("AIza")
    assert gemini_env["GOOGLE_API_KEY"] == "google-api-key"
    assert "OPENAI_API_KEY" not in gemini_env
    assert "ANTHROPIC_API_KEY" not in gemini_env
    assert "AWS_SECRET_ACCESS_KEY" not in gemini_env


def test_bridge_env_allows_llm_provider_keys_but_not_github_or_cloud_tokens():
    env = build_agent_env(provider="bridge", base=_base_env())

    assert "OPENAI_API_KEY" in env
    assert "ANTHROPIC_API_KEY" in env
    assert "GEMINI_API_KEY" in env
    assert "GOOGLE_API_KEY" in env
    assert "GITHUB_TOKEN" not in env
    assert "AWS_SECRET_ACCESS_KEY" not in env


def test_overrides_apply_before_sanitizing_and_none_removes_allowed_secret():
    env = build_agent_env(
        provider="gemini",
        base=_base_env(),
        overrides={
            "GEMINI_API_KEY": None,
            "GOOGLE_API_KEY": None,
            "KUBEDOJO_PIPELINE": "1",
            "GITHUB_TOKEN": "github_pat_999999999999999999999999999999",
        },
    )

    assert env["KUBEDOJO_PIPELINE"] == "1"
    assert "GEMINI_API_KEY" not in env
    assert "GOOGLE_API_KEY" not in env
    assert "GITHUB_TOKEN" not in env


def test_fake_agent_subprocess_cannot_read_unrelated_token_env():
    env = build_agent_env(provider="codex", base=_base_env())

    result = subprocess.run(
        [
            "sh",
            "-c",
            'printf "%s" "${GITHUB_TOKEN-unset}|${OPENAI_API_KEY-unset}|${AWS_SECRET_ACCESS_KEY-unset}"',
        ],
        env=env,
        text=True,
        capture_output=True,
        timeout=5,
        check=True,
    )

    assert result.stdout == f"unset|{_base_env()['OPENAI_API_KEY']}|unset"


def test_bridge_child_env_is_provider_scoped(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", _base_env()["OPENAI_API_KEY"])
    monkeypatch.setenv("ANTHROPIC_API_KEY", _base_env()["ANTHROPIC_API_KEY"])
    monkeypatch.setenv("GEMINI_API_KEY", _base_env()["GEMINI_API_KEY"])
    monkeypatch.setenv("GITHUB_TOKEN", _base_env()["GITHUB_TOKEN"])

    claude_env = agent_child_env("claude")
    gemini_env = agent_child_env("gemini")
    generic_env = agent_child_env()

    assert claude_env["ANTHROPIC_API_KEY"] == _base_env()["ANTHROPIC_API_KEY"]
    assert "OPENAI_API_KEY" not in claude_env
    assert "GEMINI_API_KEY" not in claude_env
    assert "GITHUB_TOKEN" not in claude_env

    assert gemini_env["GEMINI_API_KEY"] == _base_env()["GEMINI_API_KEY"]
    assert "OPENAI_API_KEY" not in gemini_env
    assert "ANTHROPIC_API_KEY" not in gemini_env
    assert "GITHUB_TOKEN" not in gemini_env

    assert "OPENAI_API_KEY" not in generic_env
    assert "ANTHROPIC_API_KEY" not in generic_env
    assert "GEMINI_API_KEY" not in generic_env
    assert "GITHUB_TOKEN" not in generic_env
