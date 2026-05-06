"""Tests for orchestrator-driven PR fallback in dispatch_388_pilot.py.

Covers:
  - orchestrator_open_pr happy path
  - branch missing on origin
  - gh pr create failure
  - classify_verdict works on Claude-style responses
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.quality.dispatch_388_pilot import (
    classify_verdict,
    find_pr_number,
    orchestrator_open_pr,
)


# ---------------------------------------------------------------------------
# orchestrator_open_pr — happy path
# ---------------------------------------------------------------------------

def _make_run(returncode: int, stdout: str = "", stderr: str = ""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


def test_orchestrator_open_pr_happy_path():
    ls_result = _make_run(0, stdout="abc123\trefs/heads/codex/388-pilot-my-module\n")
    create_result = _make_run(0, stdout="https://github.com/kube-dojo/kube-dojo.github.io/pull/917\n")

    with patch("scripts.quality.dispatch_388_pilot.subprocess.run", side_effect=[ls_result, create_result]), \
         patch("scripts.quality.dispatch_388_pilot.log") as mock_log:
        result = orchestrator_open_pr(
            slug="my-module",
            module_path="src/content/docs/k8s/cka/module-1.1.md",
            codex_response="Verifier: T0 | body_words=5800 | PR opened",
        )

    assert result == 917
    events = [c.args[0]["event"] for c in mock_log.call_args_list]
    assert "orchestrator_pr_opened" in events


# ---------------------------------------------------------------------------
# orchestrator_open_pr — branch missing on origin
# ---------------------------------------------------------------------------

def test_orchestrator_open_pr_branch_missing():
    ls_result = _make_run(0, stdout="")  # empty stdout = branch not found

    with patch("scripts.quality.dispatch_388_pilot.subprocess.run", return_value=ls_result), \
         patch("scripts.quality.dispatch_388_pilot.log") as mock_log:
        result = orchestrator_open_pr(
            slug="missing-module",
            module_path="src/content/docs/k8s/cka/module-1.2.md",
            codex_response="",
        )

    assert result is None
    events = [c.args[0]["event"] for c in mock_log.call_args_list]
    assert "orchestrator_pr_branch_missing" in events


def test_orchestrator_open_pr_branch_missing_nonzero_returncode():
    ls_result = _make_run(128, stdout="", stderr="fatal: unable to connect")

    with patch("scripts.quality.dispatch_388_pilot.subprocess.run", return_value=ls_result), \
         patch("scripts.quality.dispatch_388_pilot.log") as mock_log:
        result = orchestrator_open_pr(
            slug="error-module",
            module_path="src/content/docs/k8s/cka/module-1.3.md",
            codex_response="",
        )

    assert result is None
    events = [c.args[0]["event"] for c in mock_log.call_args_list]
    assert "orchestrator_pr_branch_missing" in events


# ---------------------------------------------------------------------------
# orchestrator_open_pr — gh pr create failure
# ---------------------------------------------------------------------------

def test_orchestrator_open_pr_create_failure():
    ls_result = _make_run(0, stdout="abc123\trefs/heads/codex/388-pilot-fail-module\n")
    create_result = _make_run(1, stdout="", stderr="GraphQL: already exists")

    with patch("scripts.quality.dispatch_388_pilot.subprocess.run", side_effect=[ls_result, create_result]), \
         patch("scripts.quality.dispatch_388_pilot.log") as mock_log:
        result = orchestrator_open_pr(
            slug="fail-module",
            module_path="src/content/docs/k8s/cka/module-1.4.md",
            codex_response="some codex output",
        )

    assert result is None
    events = [c.args[0]["event"] for c in mock_log.call_args_list]
    assert "orchestrator_pr_create_failed" in events


# ---------------------------------------------------------------------------
# classify_verdict — agent-agnostic (works on Claude-style responses)
# ---------------------------------------------------------------------------

def test_classify_verdict_approve():
    text = "The module teaches well. VERDICT: APPROVE"
    assert classify_verdict(text) == "APPROVE"


def test_classify_verdict_approve_with_nits():
    text = "Minor issues found.\nVERDICT: APPROVE WITH NITS"
    assert classify_verdict(text) == "APPROVE_WITH_NITS"


def test_classify_verdict_needs_changes():
    text = "Several errors detected.\nVERDICT: NEEDS CHANGES"
    assert classify_verdict(text) == "NEEDS CHANGES"


def test_classify_verdict_unclear():
    text = "I reviewed the PR and found it mostly fine."
    assert classify_verdict(text) == "UNCLEAR"


def test_classify_verdict_approve_with_nits_wins_over_approve():
    # Regression: "APPROVE WITH NITS" must not be classified as plain APPROVE
    text = "VERDICT: APPROVE WITH NITS — fix the kubectl alias usage."
    assert classify_verdict(text) == "APPROVE_WITH_NITS"


def test_classify_verdict_claude_style_response():
    # Claude tends to use structured markdown — verify the parser is robust
    claude_response = """
## Cross-family Review — PR #917

### Pedagogy
The module scaffolds concepts well from L1 to L3+ Bloom's.

### Accuracy
All commands verified against K8s 1.35 docs. No hallucinated flags.

### Density vs Teaching
Prose is genuinely explanatory, not padded.

### Protected Assets
3 code blocks, 1 ASCII diagram, 2 tables — all preserved per PR body.

### Sources
All 10 sources reach primary vendor documentation.

**VERDICT: APPROVE**
"""
    assert classify_verdict(claude_response) == "APPROVE"


# ---------------------------------------------------------------------------
# find_pr_number — sanity check (used by orchestrator_open_pr)
# ---------------------------------------------------------------------------

def test_find_pr_number_extracts_from_gh_output():
    stdout = "https://github.com/kube-dojo/kube-dojo.github.io/pull/917\n"
    assert find_pr_number(stdout) == 917


def test_find_pr_number_returns_none_on_no_match():
    assert find_pr_number("branch pushed but no PR URL") is None
