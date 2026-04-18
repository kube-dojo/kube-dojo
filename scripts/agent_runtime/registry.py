"""Agent registry — catalog of all agents known to the runtime.

Each entry describes how to reach an agent's adapter, its default model, cost
tier (for budgeting), capability tags (informational only; benchmark harness
will populate real scores later), and its resume_policy.

Resume policy is data-driven (see docs/design/agent-runtime.md § 6.3):

- ``bridge_only`` — Session resume allowed ONLY when caller is the bridge
  (multi-turn task_id messaging). Forbidden for delegate/dispatch. Claude
  and Gemini use this policy because their providers charge per cache-read
  token; dropping resume would reproduce the March 20-21 cost fiasco.
- ``never`` — No resume ever. Codex uses this because (a) its quota is
  per-message so resume saves nothing, and (b) session-across-worktree
  contamination is the #1 footgun flagged in Codex's own consultation.
- The runner does NOT enforce resume policy — callers do. The policy is
  stored here for documentation and for delegate.py's assertion layer.

Issue: #1184
"""
from __future__ import annotations

import os
from typing import TypedDict

try:
    from dispatch import GEMINI_WRITER_MODEL
except ImportError:  # pragma: no cover - package import path variant
    from scripts.dispatch import GEMINI_WRITER_MODEL  # type: ignore


class AgentEntry(TypedDict):
    """Registry row shape."""

    adapter: str               # fully-qualified "module:ClassName" import path
    default_model: str | None
    cost_tier: str             # "low" | "medium" | "high" | "unknown"
    capabilities: frozenset[str]
    cli_available: bool
    resume_policy: str         # "bridge_only" | "never"


AGENTS: dict[str, AgentEntry] = {
    "codex": {
        "adapter": "scripts.agent_runtime.adapters.codex:CodexAdapter",
        "default_model": "gpt-5.4",
        "cost_tier": "medium",
        "capabilities": frozenset({
            "code_writing",
            "code_review",
            "debugging",
            "adversarial_review",
        }),
        "cli_available": True,
        "resume_policy": "never",
    },
    "claude": {
        "adapter": "scripts.agent_runtime.adapters.claude:ClaudeAdapter",
        "default_model": os.environ.get("AB_CLAUDE_MODEL", "claude-opus-4-7"),
        "cost_tier": "high",
        "capabilities": frozenset({
            "architecture",
            "review",
            "content_a1",
            "planning",
        }),
        "cli_available": True,
        "resume_policy": "bridge_only",
    },
    "gemini": {
        "adapter": "scripts.agent_runtime.adapters.gemini:GeminiAdapter",
        "default_model": GEMINI_WRITER_MODEL,
        "cost_tier": "low",
        "capabilities": frozenset({
            "content_writing",
            "content_review",
            "adversarial_review",
        }),
        "cli_available": True,
        "resume_policy": "bridge_only",
    },
    "grok": {
        "adapter": "scripts.agent_runtime.adapters.grok:GrokAdapter",
        "default_model": None,
        "cost_tier": "unknown",
        "capabilities": frozenset(),
        "cli_available": False,
        "resume_policy": "never",
    },
}


def get_agent_entry(name: str) -> AgentEntry:
    """Look up an agent entry by name.

    Raises:
        KeyError: If ``name`` is not in AGENTS. Runner catches this and
            converts to AgentUnavailableError with a friendlier message.
    """
    return AGENTS[name]


def available_agents() -> list[str]:
    """Return names of agents whose cli_available is True.

    Used by consult.py (future) and introspection / debugging. Does not
    check whether the CLI is actually installed on PATH — that's the
    adapter's responsibility at invocation time.
    """
    return [name for name, entry in AGENTS.items() if entry["cli_available"]]
