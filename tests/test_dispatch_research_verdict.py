"""Regression tests for dispatch_research_verdict marker mapping (#2230).

The agy (Google) lane replaced the retired gemini-cli. Research verdicts still
post the ``<!-- verdict gemini -->`` marker for the agy lane so that
``audit_review_coverage.py`` (which maps that marker to ``gemini_gap``, matching
existing chapter status files) keeps recognizing them. This test locks that
mapping — the coverage regression composer-2.5 caught on PR #2232 R1.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import dispatch_research_verdict as drv  # noqa: E402


def test_agy_lane_keeps_gemini_marker_token() -> None:
    # audit_review_coverage.py:174 matches `<!-- verdict gemini` → gemini_gap.
    assert drv.verdict_marker_agent("agy") == "gemini"


def test_codex_and_claude_markers_are_unchanged() -> None:
    assert drv.verdict_marker_agent("codex") == "codex"
    assert drv.verdict_marker_agent("claude") == "claude"


def test_marker_matches_audit_coverage_matcher() -> None:
    # The literal string audit_review_coverage.py greps for.
    agent = "agy"
    marker_line = f"<!-- verdict {drv.verdict_marker_agent(agent)} -->"
    assert "<!-- verdict gemini" in marker_line.lower()
