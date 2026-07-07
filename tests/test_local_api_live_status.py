"""Regression tests for the live-status read-path (.agent/STATUS.md).

Session handoffs + the live status index are LOCAL agent state (user directive
s190b, memory ``feedback_handoff_commit_direct_no_worktree``): the briefing API
must prefer the gitignored ``.agent/STATUS.md`` when present so ending a
session never dirties git, and must fall back to the tracked ``STATUS.md``
(fresh clones, CI, worktrees).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parent.parent / "scripts" / "local_api.py"
    spec = importlib.util.spec_from_file_location("local_api_live_status", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


local_api = _load_module()


def test_live_status_prefers_agent_copy(tmp_path: Path) -> None:
    (tmp_path / "STATUS.md").write_text("# tracked\n", encoding="utf-8")
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()
    (agent_dir / "STATUS.md").write_text("# live\n", encoding="utf-8")

    assert local_api._live_status_path(tmp_path) == agent_dir / "STATUS.md"


def test_live_status_falls_back_to_tracked(tmp_path: Path) -> None:
    (tmp_path / "STATUS.md").write_text("# tracked\n", encoding="utf-8")

    assert local_api._live_status_path(tmp_path) == tmp_path / "STATUS.md"


def test_live_status_fallback_when_agent_dir_empty(tmp_path: Path) -> None:
    (tmp_path / "STATUS.md").write_text("# tracked\n", encoding="utf-8")
    (tmp_path / ".agent").mkdir()  # dir exists, no STATUS.md inside

    assert local_api._live_status_path(tmp_path) == tmp_path / "STATUS.md"


def test_session_briefing_reads_live_copy(tmp_path: Path) -> None:
    """PUBLIC path: build_session_briefing must surface the LIVE copy's TODO items —
    pins the actual briefing behavior, not just the private helper (codex R1 nit)."""
    (tmp_path / "STATUS.md").write_text(
        "# tracked\n\n## TODO\n\n- [ ] stale tracked item\n", encoding="utf-8"
    )
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()
    (agent_dir / "STATUS.md").write_text(
        "# live\n\n## TODO\n\n- [ ] live item from the current session\n",
        encoding="utf-8",
    )

    briefing = local_api.build_session_briefing(tmp_path)
    focus_blob = " ".join(str(x) for x in briefing.get("focus", []))
    assert "live item" in focus_blob
    assert "stale tracked item" not in focus_blob
