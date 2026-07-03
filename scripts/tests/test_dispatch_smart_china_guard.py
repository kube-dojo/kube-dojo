"""Regression tests for the #2171 China-provider CI guard in dispatch_smart."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _load():
    p = Path(__file__).resolve().parents[1] / "dispatch_smart.py"
    spec = importlib.util.spec_from_file_location("dispatch_smart", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


ds = _load()


def _clear_ci(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("CI", raising=False)


@pytest.mark.parametrize("ci_env", [("GITHUB_ACTIONS", "true"), ("CI", "true"), ("CI", "1")])
@pytest.mark.parametrize(
    "agent,model",
    [
        ("opencode", "zai-coding-plan/glm-5.2"),
        ("opencode", "zai-coding-plan/glm-4.6"),
        ("opencode", "z.ai/glm-5.2"),
        ("glm", "glm-5.2"),
    ],
)
def test_glm_blocked_in_ci(monkeypatch, ci_env, agent, model):
    _clear_ci(monkeypatch)
    monkeypatch.setenv(*ci_env)
    with pytest.raises(SystemExit):
        ds.guard_no_china_provider_in_ci(agent, model)


@pytest.mark.parametrize(
    "agent,model",
    [
        ("opencode", "openrouter/qwen/qwen3.7-max"),   # US-hosted proxy -> allowed
        ("opencode", "openrouter/deepseek/deepseek-v3"),
        ("codex", "gpt-5.5"),
        ("claude", "claude-sonnet-5"),
    ],
)
def test_non_china_allowed_in_ci(monkeypatch, agent, model):
    _clear_ci(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    ds.guard_no_china_provider_in_ci(agent, model)  # must NOT raise


@pytest.mark.parametrize(
    "agent,model",
    [
        ("opencode", "zai-coding-plan/glm-5.2"),  # local: GLM allowed
        ("glm", "glm-5.2"),
    ],
)
def test_glm_allowed_locally(monkeypatch, agent, model):
    _clear_ci(monkeypatch)  # not in CI
    ds.guard_no_china_provider_in_ci(agent, model)  # must NOT raise
