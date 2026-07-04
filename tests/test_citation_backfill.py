from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import citation_backfill  # noqa: E402


def test_primary_checkout_root_strips_worktree_layout() -> None:
    """From `<repo>/.worktrees/<name>/` (AGENTS.md §1 mandated layout)
    the helper must return `<repo>` — otherwise `_VENV_PYTHON` points
    at a non-existent `<worktree>/.venv/bin/python` and the subprocess
    launch fails inside a worktree.

    Pure function over paths; no filesystem required.
    """
    # Primary checkout case: no worktree, returns input unchanged.
    primary = Path("/home/user/kubedojo")
    assert citation_backfill._primary_checkout_root(primary) == primary

    # Worktree case: step up past .worktrees/<name>/ to the primary.
    worktree = Path("/home/user/kubedojo/.worktrees/feature-x")
    assert (
        citation_backfill._primary_checkout_root(worktree)
        == Path("/home/user/kubedojo")
    )

    # Edge: a directory literally named ".worktrees" as the parent of
    # a non-worktree path (unlikely but possible) — still handled
    # correctly by stepping up. Documents the name-based heuristic.
    nested = Path("/tmp/.worktrees/foo")
    assert (
        citation_backfill._primary_checkout_root(nested) == Path("/tmp")
    )


def test_venv_python_points_at_primary_even_when_loaded_from_worktree() -> None:
    """Regression guard for the #374 round-3 finding: _VENV_PYTHON
    must resolve to <primary>/.venv/bin/python, not
    <worktree>/.venv/bin/python. This test doesn't reload the module
    from a worktree (expensive) — it recomputes what the module would
    compute and asserts the shape.
    """
    pretend_worktree_root = Path("/home/u/kubedojo/.worktrees/feat-x")
    expected_interpreter = (
        citation_backfill._primary_checkout_root(pretend_worktree_root)
        / ".venv" / "bin" / "python"
    )
    assert expected_interpreter == Path("/home/u/kubedojo/.venv/bin/python"), (
        f"worktree lookup must resolve to primary .venv, got "
        f"{expected_interpreter}"
    )
    # And for the module's own _VENV_PYTHON in the primary checkout,
    # it must not contain '.worktrees' at all.
    assert ".worktrees" not in citation_backfill._VENV_PYTHON, (
        f"module-level _VENV_PYTHON leaked a worktree segment: "
        f"{citation_backfill._VENV_PYTHON}"
    )


def test_dispatch_agy_launches_dispatch_with_venv_python_and_absolute_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: dispatch_agy must launch dispatch.py with the
    primary-checkout venv's Python (AGENTS.md §3 forbids sys.executable
    — it misses venv-only deps) and an absolute path to dispatch.py.

    An earlier revision used `sys.executable`; PR #374 review (Codex)
    caught the rule violation. The interpreter path is derived from
    REPO_ROOT (i.e. from __file__), so it stays correct when the
    script is invoked from a git worktree — the worktree shares the
    primary checkout's .venv via this absolute path.
    """
    captured: dict[str, object] = {}

    class _Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def _fake_run(cmd: list[str], **kwargs: object) -> _Completed:
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")
        return _Completed()

    monkeypatch.setattr(subprocess, "run", _fake_run)

    ok, _ = citation_backfill.dispatch_agy("hello")

    assert ok is True
    cmd = captured["cmd"]
    assert isinstance(cmd, list) and cmd
    interpreter = Path(cmd[0])
    assert interpreter.is_absolute(), f"interpreter must be absolute, got {cmd[0]!r}"
    assert interpreter.name == "python", f"expected .venv/bin/python, got {cmd[0]!r}"
    assert ".venv" in interpreter.parts, (
        f"must use .venv python (AGENTS.md §3 bans sys.executable), got {cmd[0]!r}"
    )
    assert cmd[0] != sys.executable or sys.executable.endswith("/.venv/bin/python"), (
        "dispatch_agy must not use sys.executable (AGENTS.md §3)"
    )
    dispatch_arg = Path(cmd[1])
    assert dispatch_arg.is_absolute(), f"dispatch.py path must be absolute, got {cmd[1]!r}"
    assert dispatch_arg.name == "dispatch.py"
    assert "agy" in cmd


def test_dispatch_agy_default_timeout_unchanged_for_research_inject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run_research / run_inject still use the original 900s budget.

    citation_backfill.dispatch_agy is shared between whole-module
    work (research/inject — legitimately long prompts) and the short
    per-finding URL-candidate path. The former must NOT get the short
    timeout: a content-generation call can legitimately run 5-10 min,
    and a 120s cap there would turn every real generation into a false
    timeout. The per-finding cap lives at the call site instead.
    """
    captured: dict[str, object] = {}

    class _Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def _fake_run(cmd: list[str], **kwargs: object) -> _Completed:
        captured["cmd"] = cmd
        captured["timeout"] = kwargs.get("timeout")
        return _Completed()

    monkeypatch.setattr(subprocess, "run", _fake_run)
    citation_backfill.dispatch_agy("hello")  # no explicit timeout

    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    ti = cmd.index("--timeout")
    inner = int(cmd[ti + 1])
    outer = captured["timeout"]
    assert inner == outer
    assert inner == citation_backfill.GEMINI_DEFAULT_TIMEOUT
    assert inner >= 600, (
        f"default Gemini timeout is {inner}s — whole-module research/"
        "inject needs the longer budget; per-finding caps belong at the "
        "call site"
    )


def test_dispatch_agy_honors_explicit_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Per-finding callers must be able to pass a short timeout.

    Both the inner `--timeout` arg to dispatch.py and the outer
    subprocess.run(timeout=...) must reflect the caller's value — a
    drift would let the outer watchdog fire while the inner argument
    lied about its own budget.
    """
    captured: dict[str, object] = {}

    class _Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def _fake_run(cmd: list[str], **kwargs: object) -> _Completed:
        captured["cmd"] = cmd
        captured["timeout"] = kwargs.get("timeout")
        return _Completed()

    monkeypatch.setattr(subprocess, "run", _fake_run)
    citation_backfill.dispatch_agy("hello", timeout=120)

    cmd = captured["cmd"]
    ti = cmd.index("--timeout")
    assert int(cmd[ti + 1]) == 120
    assert captured["timeout"] == 120


def test_dispatch_agy_timeout_error_message_reflects_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the outer watchdog fires, the error string must name the
    actual configured budget — operators use this to distinguish a
    per-finding timeout (120s) from a whole-module one (900s) in logs.
    """
    def _raise_timeout(cmd: list[str], **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=kwargs.get("timeout") or 0)

    monkeypatch.setattr(subprocess, "run", _raise_timeout)
    ok, msg = citation_backfill.dispatch_agy("hello", timeout=120)
    assert ok is False
    assert "120" in msg, f"error should name the budget; got {msg!r}"


# ---- Claude dispatcher --------------------------------------------------


def test_dispatch_claude_raises_on_budget_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Per-process call-budget exhaustion is also retryable — next
    fresh process gets a new budget. Must raise DispatcherUnavailable,
    not return False."""
    class _P:
        returncode = 2
        stdout = ""
        stderr = "Claude call budget exhausted after 50 calls; restart to reset."

    monkeypatch.setattr(subprocess, "run", lambda c, **kw: _P())
    with pytest.raises(citation_backfill.DispatcherUnavailable, match="budget"):
        citation_backfill.dispatch_claude("hi", timeout=180)


def test_dispatch_claude_returns_false_on_ordinary_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-unavailability failures (e.g. malformed prompt, CLI crash)
    still return (False, message) as before — those ARE the "the LLM
    got nowhere" class and should fall through to unresolvable."""
    class _P:
        returncode = 1
        stdout = ""
        stderr = "TypeError: something broke"

    monkeypatch.setattr(subprocess, "run", lambda c, **kw: _P())
    ok, msg = citation_backfill.dispatch_claude("hi", timeout=180)
    assert ok is False
    assert "TypeError" in msg


def test_apply_inject_plan_skips_rewrite_disposition_claims() -> None:
    body = "Marcus ran a local model on 16 GB of RAM.\n"
    seed = {
        "claims": [
            {
                "claim_id": "C-rewrite",
                "disposition": "soften_to_illustration",
                "anchor_text": "Marcus ran a local model on 16 GB of RAM.",
                "suggested_rewrite": "A developer ran a local model.",
            }
        ],
        "further_reading": [],
    }

    new_body, applied = citation_backfill.apply_inject_plan(body, {}, seed)

    assert "Marcus ran a local model on 16 GB of RAM." in new_body
    assert "A developer ran a local model." not in new_body
    assert {
        "claim_id": "C-rewrite",
        "kind": "prose_rewrite",
        "status": "skipped",
        "reason": "rewrites_disabled_pending_redesign",
    } in applied


def test_apply_inject_plan_skips_overlapping_wrap_when_phrase_already_cited() -> None:
    """Regression test for #1216 (Pattern B): inject must not double-wrap a phrase
    that already lives inside an existing [label](url) region. The claim should
    be recorded as applied with note='already_cited_in_body' so the coverage
    gate in run_inject treats it as addressed."""
    body = "Lead.\\n\\n[Kubernetes](https://kubernetes.io/) is a container orchestrator.\\n"
    plan = {
        "inline_insertions": [
            {
                "claim_id": "k8s-orchestrator",
                "target_line": "[Kubernetes](https://kubernetes.io/) is a container orchestrator.",
                "original_phrase": "Kubernetes",
                "replace_with": "[Kubernetes](https://kubernetes.io/)",
            }
        ],
        "skipped_claims": [],
    }
    seed = {"claims": [{"claim_id": "k8s-orchestrator", "disposition": "supported"}]}
    new_body, applied = citation_backfill.apply_inject_plan(body, plan, seed)
    assert new_body == body, "body must not be mutated when phrase already cited"
    matching = [a for a in applied if a.get("claim_id") == "k8s-orchestrator"]
    assert len(matching) == 1
    assert matching[0]["status"] == "applied"
    assert matching[0]["note"] == "already_cited_in_body"


def test_apply_inject_plan_preserves_next_module_after_sources() -> None:
    body = (
        "Body text.\n\n"
        "## Sources\n\n"
        "- [Existing](https://example.com/a)\n\n"
        "## Next Module\n\n"
        "Continue to ...\n"
    )
    seed = {
        "claims": [],
        "further_reading": [
            {
                "title": "New",
                "url": "https://example.com/b",
                "why_relevant": "Additional context.",
            }
        ],
    }

    new_body, _ = citation_backfill.apply_inject_plan(body, {}, seed)

    assert "- [New](https://example.com/b)" in new_body
    assert "- [Existing](https://example.com/a)" in new_body
    assert "## Next Module\n\nContinue to ..." in new_body


def test_apply_inject_plan_sources_merge_dedupes_by_url() -> None:
    body = (
        "Body text.\n\n"
        "## Sources\n\n"
        "- [A](https://x.com/a)\n"
    )
    seed = {
        "claims": [],
        "further_reading": [
            {
                "title": "Different A",
                "url": "https://x.com/a",
                "why_relevant": "Duplicate URL.",
            },
            {
                "title": "B",
                "url": "https://y.com/b",
                "why_relevant": "New URL.",
            },
        ],
    }

    new_body, _ = citation_backfill.apply_inject_plan(body, {}, seed)
    bullets = [
        line for line in new_body.splitlines()
        if line.startswith("- ")
    ]

    assert len(bullets) == 2
    assert new_body.count("https://x.com/a") == 1
    assert "- [A](https://x.com/a)" in new_body
    assert "Different A" not in new_body
    assert "- [B](https://y.com/b)" in new_body


def test_run_inject_soft_skips_codex_dropped_cited_claims(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Use an isolated fake repo, so this test can run in parallel with
    # other citation fixtures without touching actual source files.
    monkeypatch.setattr(citation_backfill, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(citation_backfill, "DOCS_ROOT", tmp_path / "src" / "content" / "docs")
    monkeypatch.setattr(citation_backfill, "SEED_DIR", tmp_path / "docs" / "citation-seeds")

    module_key = "platform/cluster-api-demo"
    module_path = tmp_path / "src" / "content" / "docs" / "platform" / "cluster-api-demo.md"
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_body = (
        "Cluster API bootstraps nodes for production use.\n"
        "The operator reviews cluster events and scales workloads.\n"
        "Kubernetes handles control-plane scheduling automatically.\n"
    )
    module_path.write_text(module_body, encoding="utf-8")

    seed = {
        "claims": [
            {
                "claim_id": "C001",
                "disposition": "supported",
                "claim_text": "Cluster API bootstraps nodes for production use.",
                "span_hint": "line 1",
                "proposed_url": "https://kubernetes.io/docs/concepts/overview/",
            },
            {
                "claim_id": "C002",
                "disposition": "supported",
                "claim_text": "The operator reviews cluster events and scales workloads.",
                "span_hint": "line 2",
                "proposed_url": "https://kubernetes.io/docs/concepts/architecture/control-plane-node-communication/",
            },
            {
                "claim_id": "C003",
                "disposition": "supported",
                "claim_text": "Kubernetes handles control-plane scheduling automatically.",
                "span_hint": "line 3",
                "proposed_url": "https://kubernetes.io/docs/concepts/scheduling-eviction/",
            },
        ]
    }
    citation_backfill.seed_path_for(module_key).write_text(
        json.dumps(seed, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    plan = {
        "inline_insertions": [
            {
                "claim_id": "C001",
                "target_line": "Cluster API bootstraps nodes for production use.",
                "original_phrase": "Cluster API",
                "replace_with": "[Cluster API](https://kubernetes.io/docs/concepts/overview/)",
            },
            {
                "claim_id": "C002",
                "target_line": "The operator reviews cluster events and scales workloads.",
                "original_phrase": "scales workloads",
                "replace_with": "[scales workloads](https://kubernetes.io/docs/concepts/architecture/control-plane-node-communication/)",
            },
        ],
        "skipped_claims": [],
    }

    def _fake_dispatch(
        _prompt: str,
        *,
        task_id: str | None = None,
        timeout: int = 900,
    ) -> tuple[bool, str]:
        del _prompt, task_id, timeout
        return True, json.dumps(plan, ensure_ascii=False)

    monkeypatch.setattr(citation_backfill, "dispatch_codex", _fake_dispatch)

    result = citation_backfill.run_inject(module_key, agent="codex")

    assert result["ok"] is True
    assert not any(
        "cited_dispositions_not_addressed" in str(item)
        for item in result["diff_issues"]
    )
    assert result["codex_dropped_count"] == 1

    revision_rel = result["deferred_record"]
    assert isinstance(revision_rel, str)
    revision_path = tmp_path / revision_rel
    assert revision_path.exists()
    revision = json.loads(revision_path.read_text(encoding="utf-8"))
    dropped = revision.get("codex_dropped") or []
    assert len(dropped) == 1
    assert dropped[0]["claim_id"] == "C003"

    c003 = [entry for entry in result["applied"] if entry.get("claim_id") == "C003"]
    assert len(c003) == 1
    assert c003[0]["kind"] == "inline"
    assert c003[0]["status"] == "skipped"
    assert c003[0]["reason"] == "not_addressed_by_agent"


def test_run_research_agent_response_invalid_preserves_raw_snippets(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Regression for #1621: invalid agent JSON must retain raw_head/raw_tail."""
    module_path = tmp_path / "on-premises" / "storage" / "module-4.4-object-storage.md"
    module_path.parent.mkdir(parents=True)
    module_path.write_text("# Object storage\n\nBare-metal object storage notes.\n", encoding="utf-8")

    monkeypatch.setattr(citation_backfill, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(citation_backfill, "DOCS_ROOT", tmp_path)
    monkeypatch.setattr(citation_backfill, "resolve_module_path", lambda _key: module_path)
    monkeypatch.setattr(citation_backfill, "load_section_pool", lambda *a, **kw: None)

    pad_head = "HEAD-" * 80
    pad_tail = "TAIL-" * 80
    inner = json.dumps({"foo": "bar"})
    raw = f"{pad_head}{inner}{pad_tail}"

    def fake_dispatch(_prompt: str, *, task_id: str) -> tuple[bool, str]:
        del task_id
        return True, raw

    monkeypatch.setattr(citation_backfill, "dispatch_codex", fake_dispatch)

    result = citation_backfill.run_research(
        "on-premises/storage/module-4.4-object-storage-bare-metal",
        agent="codex",
    )

    assert result["ok"] is False
    assert result["error"] == "agent_response_invalid"
    assert result["detail"] == (
        "agent response missing claims/schema_version or bridge error payload"
    )
    assert result["raw_head"] == raw[:400]
    assert result["raw_tail"] == raw[-400:]
