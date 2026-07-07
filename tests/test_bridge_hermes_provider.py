"""Regression tests for the ab-bridge Hermes provider mapping (#2245).

The bridge's ``_detect_provider`` had the same silent-OpenRouter catch-all as
``dispatch_smart`` — ``ask-hermes --to-model deepseek-v4-pro`` billed the
metered OpenRouter proxy instead of the first-party DeepSeek API. These tests
pin the explicit-only mapping (codex R1 P1 on PR #2246).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ai_agent_bridge._hermes import _build_command, _cli_model, _detect_provider  # noqa: E402


def test_bridge_deepseek_routes_first_party(monkeypatch) -> None:
    """deepseek-* via the bridge must hit the first-party API (#2245)."""
    monkeypatch.delenv("KUBEDOJO_HERMES_PROVIDER", raising=False)
    assert _detect_provider("deepseek-v4-pro") == "deepseek"
    assert _detect_provider("deepseek-v4-flash") == "deepseek"


def test_bridge_unknown_model_raises(monkeypatch) -> None:
    """Unknown models raise instead of silently billing a metered proxy (#2245)."""
    monkeypatch.delenv("KUBEDOJO_HERMES_PROVIDER", raising=False)
    with pytest.raises(ValueError, match="2245"):
        _detect_provider("kimi-k2.6")


def test_bridge_openrouter_prefix_is_the_explicit_opt_in(monkeypatch) -> None:
    """openrouter/ prefix selects the proxy; the prefix is stripped for -m."""
    monkeypatch.delenv("KUBEDOJO_HERMES_PROVIDER", raising=False)
    assert _detect_provider("openrouter/deepseek/deepseek-v4-pro") == "openrouter"
    assert _cli_model("openrouter/deepseek/deepseek-v4-pro") == "deepseek/deepseek-v4-pro"


def test_bridge_grok_and_qwen_mappings_unchanged(monkeypatch) -> None:
    """grok-* stays on xai; qwen keeps its documented explicit OpenRouter lane."""
    monkeypatch.delenv("KUBEDOJO_HERMES_PROVIDER", raising=False)
    assert _detect_provider("grok-4.3") == "xai"
    assert _detect_provider("qwen-3.6-flash") == "openrouter"


def test_bridge_build_command_deepseek(monkeypatch) -> None:
    """End-to-end argv: deepseek model → --provider deepseek, slug verbatim."""
    monkeypatch.delenv("KUBEDOJO_HERMES_PROVIDER", raising=False)
    cmd = _build_command("hello", "deepseek-v4-pro")
    assert cmd[cmd.index("--provider") + 1] == "deepseek"
    assert cmd[cmd.index("-m") + 1] == "deepseek-v4-pro"
    assert cmd[-1] == "--oneshot=hello"
