"""Integration tests for ``scripts.quality.stages`` + ``pipeline``.

Uses a real temp git repo (not mocked subprocess) + stubbed LLM dispatch
so the worktree + merge + rebase behavior is exercised end-to-end. This
is where the Codex must-fixes that Phase C closes get their regression
guards:

* **#1** — reviewer reads from the worktree, not ``main``
* **#3** — rebase-before-ff survives main advancing between sibling merges
* **#4** — ``REVIEW_CHANGES`` routes back with ``must_fix``, retries
  capped at 2, Gemini tiebreaker kicks in after the cap
* **#5 (runtime half)** — crash recovery from ``WRITE_IN_PROGRESS`` /
  ``REVIEW_IN_PROGRESS``
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.quality import dispatchers, pipeline, stages, state, worktree  # noqa: E402
from scripts.quality.citations import CitationResult  # noqa: E402
from scripts.quality.dispatchers import DispatchResult  # noqa: E402


# ---- fixtures ---------------------------------------------------------


@pytest.fixture
def fake_repo(tmp_path: Path, monkeypatch):
    """Real git repo in tmpdir + module seed + path monkey-patches.

    Points every ``_REPO_ROOT`` / ``_CONTENT_ROOT`` / ``STATE_DIR``
    reference across the quality package at this isolated repo so tests
    don't collide with the real project state.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    for k, v in [("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")]:
        subprocess.run(["git", "config", k, v], cwd=repo, check=True)
    (repo / ".gitignore").write_text(".worktrees/\n.pipeline/\n")
    (repo / "README.md").write_text("seed\n")

    # Seed one module at a realistic path.
    module_rel = "src/content/docs/k8s/cka/module-1.1-pods.md"
    module_file = repo / module_rel
    module_file.parent.mkdir(parents=True)
    module_file.write_text("""---
title: Pods Fundamentals
sidebar:
  order: 1
---

# Pods

Original content about pods. The module has some quiz.

## Quiz

Question 1.
""")

    # Seed a teaching audit so route_one has score + gaps immediately.
    audit_dir = repo / ".pipeline" / "teaching-audit"
    audit_dir.mkdir(parents=True)
    slug = "k8s-cka-module-1.1-pods"
    (audit_dir / f"{slug}.json").write_text(json.dumps({
        "teaching_score": 2.5,
        "rubric_score": 2.5,
        "teaching_gaps": ["Quiz tests recall, not scenarios", "No worked example"],
    }))

    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=repo, check=True, capture_output=True)

    # Patch every module's root pointer. Each module captured ``_REPO_ROOT``
    # at import time; overwrite them all to the fake repo.
    monkeypatch.setattr(state, "REPO_ROOT", repo)
    monkeypatch.setattr(state, "STATE_DIR", repo / ".pipeline" / "quality-pipeline")
    monkeypatch.setattr(state, "CONTENT_ROOT", repo / "src" / "content" / "docs")
    monkeypatch.setattr(stages, "_REPO_ROOT", repo)
    monkeypatch.setattr(stages, "_AUDIT_DIR", repo / ".pipeline" / "teaching-audit")
    monkeypatch.setattr(pipeline, "_REPO_ROOT", repo)
    monkeypatch.setattr(pipeline, "_CONTENT_ROOT", repo / "src" / "content" / "docs")
    # Prompt docs aren't present in the fake repo; stub the startup check.
    monkeypatch.setattr("scripts.quality.pipeline.assert_required_docs_exist", lambda: None)

    return repo


def _bootstrap(fake_repo: Path) -> str:
    """Run bootstrap against the fake repo; return the seeded slug."""
    modules = pipeline.iter_all_modules()
    assert len(modules) == 1
    module_path = modules[0]
    slug = state.slug_for(module_path)
    st = state.new_state(module_path, module_index=0)
    state.save_state(st)
    return slug


# ---- dispatch stubs ---------------------------------------------------


_REWRITTEN_MODULE = """---
title: Pods Fundamentals
sidebar:
  order: 1
---

# Pods

Rewritten pedagogically sound content.

## Quiz

Scenario-based question.
"""


def _writer_stub_output(track: str = "rewrite") -> str:
    """Codex-style output: reasoning prose, then the module."""
    return f"Here is the {track}-ed module with improvements:\n\n{_REWRITTEN_MODULE}"


def _review_approve_output() -> str:
    """Reviewer verdict with reasoning prose FIRST, verdict JSON LAST."""
    payload = {
        "verdict": "approve",
        "rubric_score": 4.5,
        "teaching_score": 4.3,
        "must_fix": [],
        "nits": [],
        "strengths": ["Good worked example"],
        "reasoning": "Now teaches properly.",
    }
    return (
        "Let me reason through this module.\n\n"
        '{"thinking": "checking scenarios", "draft_score": 4.0}\n\n'
        "My verdict:\n\n" + json.dumps(payload)
    )


def _review_changes_output(must_fix: list[str]) -> str:
    payload = {
        "verdict": "changes_requested",
        "rubric_score": 3.5,
        "teaching_score": 3.5,
        "must_fix": must_fix,
        "nits": [],
        "strengths": [],
        "reasoning": "Quiz still weak.",
    }
    return "Reviewing.\n\n" + json.dumps(payload)


def _stubbed_dispatch(writer_out: str, review_out: str):
    """Build a dispatch fake keyed by agent — so write and review paths
    can return different content, matching the cross-family boundary."""
    def fake_dispatch(agent, prompt, *, timeout, model=None, cwd=None):
        if "## Your task" in prompt and "reviewing a KubeDojo module" in prompt:
            return DispatchResult(
                ok=True, stdout=review_out, stderr="", returncode=0,
                duration_sec=0.1, agent=agent, model=model,
            )
        return DispatchResult(
            ok=True, stdout=writer_out, stderr="", returncode=0,
            duration_sec=0.1, agent=agent, model=model,
        )
    return fake_dispatch


# ---- unit-ish stage tests --------------------------------------------


def test_route_rewrite_when_score_below_threshold(fake_repo, monkeypatch):
    slug = _bootstrap(fake_repo)
    stages.audit_one(slug)
    st = state.load_state(slug)
    assert st["stage"] == "AUDITED"
    assert st["audit"]["teaching_score"] == 2.5

    stages.route_one(slug)
    st = state.load_state(slug)
    assert st["stage"] == "WRITE_PENDING"
    assert st["route"]["track"] == "rewrite"
    assert st["writer"] == "codex"  # module_index=0 → even → codex writes
    assert st["reviewer"] == "claude"


def test_route_skips_rewrite_when_score_high_and_structure_complete(fake_repo, monkeypatch):
    """Score ≥ 4.0 AND all structural sections present → CITATION_CLEANUP_ONLY."""
    slug = _bootstrap(fake_repo)
    # Seed a high audit score and a complete module.
    st = state.load_state(slug)
    st["audit"] = {"teaching_score": 4.5, "teaching_gaps": []}
    st["stage"] = "AUDITED"
    state.save_state(st)
    # Make the module structurally complete.
    full_module = """---
title: Pods
sidebar:
  order: 1
---

## Quiz

Q.

## Hands-On Exercise

Do the thing.

## Common Mistakes

Table.

## Did You Know?

Facts.
"""
    (fake_repo / st["module_path"]).write_text(full_module)
    stages.route_one(slug)
    st = state.load_state(slug)
    assert st["stage"] == "CITATION_CLEANUP_ONLY"


def test_write_one_happy_path_creates_worktree_commit(fake_repo, monkeypatch):
    slug = _bootstrap(fake_repo)
    stages.audit_one(slug)
    stages.route_one(slug)

    monkeypatch.setattr(stages, "dispatch", _stubbed_dispatch(_writer_stub_output(), _review_approve_output()))

    stages.write_one(slug, timeout=10)
    st = state.load_state(slug)
    assert st["stage"] == "WRITE_DONE"
    assert st["write"]["commit_sha"]
    assert st["write"]["agent"] == "codex"
    # The worktree should exist with the new content.
    wt = worktree.worktree_dir(fake_repo, slug)
    assert wt.exists()
    assert "Rewritten pedagogically sound content" in (wt / st["module_path"]).read_text()


def test_write_one_extract_failure_marks_failed(fake_repo, monkeypatch):
    """If Codex's output is truncated mid-code-block, extractor raises → FAILED."""
    slug = _bootstrap(fake_repo)
    stages.audit_one(slug)
    stages.route_one(slug)

    truncated = """---
title: Pods
---

Start of body.

```bash
kubectl get pods
"""  # no closing fence

    def bad_dispatch(agent, prompt, *, timeout, model=None, cwd=None):
        return DispatchResult(
            ok=True, stdout=truncated, stderr="", returncode=0,
            duration_sec=0.1, agent=agent, model=model,
        )

    monkeypatch.setattr(stages, "dispatch", bad_dispatch)
    stages.write_one(slug, timeout=10)
    st = state.load_state(slug)
    assert st["stage"] == "FAILED"
    assert "truncated" in (st.get("failure_reason") or "").lower()


def test_write_one_dispatcher_unavailable_reverts_to_pending(fake_repo, monkeypatch):
    """Peak-hours / budget refusal must REVERT to WRITE_PENDING so the
    module stays retryable. v1's failure mode silently drained the queue."""
    slug = _bootstrap(fake_repo)
    stages.audit_one(slug)
    stages.route_one(slug)

    def unavail(agent, prompt, *, timeout, model=None, cwd=None):
        raise dispatchers.DispatcherUnavailable("claude peak hours")

    monkeypatch.setattr(stages, "dispatch", unavail)
    with pytest.raises(dispatchers.DispatcherUnavailable):
        stages.write_one(slug, timeout=10)
    st = state.load_state(slug)
    assert st["stage"] == "WRITE_PENDING"
    # Branch cleaned up so next run starts fresh.
    assert not worktree.worktree_dir(fake_repo, slug).exists()


# ---- reviewer-reads-from-worktree regression guard (Codex must-fix #1) ----


def test_reviewer_reads_module_from_worktree_not_primary(fake_repo, monkeypatch):
    """Codex must-fix #1 regression guard.

    v1 reviewer always read from ``main``. In this test, the worktree
    has the new content, primary has the old content. The reviewer
    prompt captured by our stub must contain the NEW content — if it
    contains the old content, the fix regressed.
    """
    slug = _bootstrap(fake_repo)
    stages.audit_one(slug)
    stages.route_one(slug)

    captured_review_prompt: list[str] = []

    def capturing_dispatch(agent, prompt, *, timeout, model=None, cwd=None):
        if "reviewing a KubeDojo module" in prompt:
            captured_review_prompt.append(prompt)
            return DispatchResult(
                ok=True, stdout=_review_approve_output(), stderr="", returncode=0,
                duration_sec=0.1, agent=agent, model=model,
            )
        return DispatchResult(
            ok=True, stdout=_writer_stub_output(), stderr="", returncode=0,
            duration_sec=0.1, agent=agent, model=model,
        )

    monkeypatch.setattr(stages, "dispatch", capturing_dispatch)
    # No-op citations so we reach review.
    monkeypatch.setattr(
        stages, "process_module_citations",
        lambda p, *, verifier=None, fetcher=None: CitationResult(new_text=p.read_text(), had_sources_section=False),
    )

    stages.write_one(slug, timeout=10)
    stages.citation_verify_one(slug)
    stages.review_one(slug, timeout=10)

    assert captured_review_prompt, "reviewer was never invoked"
    prompt = captured_review_prompt[0]
    # The primary file still has "Original content about pods". The
    # worktree has "Rewritten pedagogically sound content". Regression
    # guard: the NEW text must be in the reviewer prompt.
    assert "Rewritten pedagogically sound content" in prompt
    assert "Original content about pods" not in prompt


# ---- REVIEW_CHANGES retry loop (Codex must-fix #4) -------------------


def test_review_changes_routes_back_to_write_pending_with_retry_count(fake_repo, monkeypatch):
    slug = _bootstrap(fake_repo)
    stages.audit_one(slug)
    stages.route_one(slug)

    monkeypatch.setattr(
        stages, "dispatch",
        _stubbed_dispatch(_writer_stub_output(), _review_changes_output(["fix quiz Q3"])),
    )
    monkeypatch.setattr(
        stages, "process_module_citations",
        lambda p, *, verifier=None, fetcher=None: CitationResult(new_text=p.read_text(), had_sources_section=False),
    )

    stages.write_one(slug, timeout=10)
    stages.citation_verify_one(slug)
    stages.review_one(slug, timeout=10)
    st = state.load_state(slug)
    assert st["stage"] == "REVIEW_CHANGES"
    assert st["review"]["must_fix"] == ["fix quiz Q3"]

    # Must route back to WRITE_PENDING with retry_count bumped.
    stages.handle_review_changes(slug)
    st = state.load_state(slug)
    assert st["stage"] == "WRITE_PENDING"
    assert st["retry_count"] == 1


def test_review_changes_tiebreaker_after_cap(fake_repo, monkeypatch):
    slug = _bootstrap(fake_repo)
    st = state.load_state(slug)
    st["stage"] = "REVIEW_CHANGES"
    st["retry_count"] = stages.RETRY_CAP
    st["writer"] = "codex"
    st["reviewer"] = "claude"
    state.save_state(st)

    stages.handle_review_changes(slug)
    st = state.load_state(slug)
    assert st["stage"] == "REVIEW_PENDING"
    assert st["reviewer"] == "gemini"
    assert st["retry_count"] == stages.RETRY_CAP  # not bumped past cap


# ---- rebase-then-ff merge across main advancing (Codex must-fix #3) ---


def test_ff_merge_after_main_advances_with_real_pipeline_modules(fake_repo, monkeypatch):
    """Two modules merge cleanly even though the second's branch was cut
    before the first's merge landed on main.

    Uses the stages + merge path (not the worktree helpers directly) so
    the regression guard covers the full pipeline wiring of Codex #3,
    not just the ``rebase_onto_main`` helper (already tested in
    test_quality_worktree.py)."""
    # Add a second module.
    mod2_rel = "src/content/docs/k8s/cka/module-1.2-services.md"
    (fake_repo / mod2_rel).parent.mkdir(parents=True, exist_ok=True)
    (fake_repo / mod2_rel).write_text("---\ntitle: Services\nsidebar:\n  order: 2\n---\n\nBody.\n")
    audit_dir = fake_repo / ".pipeline" / "teaching-audit"
    slug2 = "k8s-cka-module-1.2-services"
    (audit_dir / f"{slug2}.json").write_text(json.dumps({
        "teaching_score": 2.0,
        "teaching_gaps": ["Thin"],
    }))
    subprocess.run(["git", "add", "-A"], cwd=fake_repo, check=True)
    subprocess.run(["git", "commit", "-m", "seed m2"], cwd=fake_repo, check=True, capture_output=True)

    monkeypatch.setattr(
        stages, "dispatch",
        _stubbed_dispatch(_writer_stub_output(), _review_approve_output()),
    )
    monkeypatch.setattr(
        stages, "process_module_citations",
        lambda p, *, verifier=None, fetcher=None: CitationResult(new_text=p.read_text(), had_sources_section=False),
    )

    modules = sorted(pipeline.iter_all_modules())
    for i, mod_path in enumerate(modules):
        slug = state.slug_for(mod_path)
        if state.load_state(slug) is None:
            st = state.new_state(mod_path, module_index=i)
            state.save_state(st)

    # Drive both through a full run — they both merge to main.
    slugs = sorted(state.iter_state_slugs())
    for slug in slugs:
        terminal = stages.run_module(slug)
        assert terminal == "COMMITTED", f"{slug}: expected COMMITTED, got {terminal}"

    # Both files now on main with rewritten content.
    log = subprocess.run(
        ["git", "log", "--oneline", "-5"], cwd=fake_repo, capture_output=True, text=True, check=True
    ).stdout
    assert "rewrite" in log.lower() or "quality" in log.lower()
    # Primary stays on main, clean.
    assert worktree.current_branch(fake_repo) == "main"
    assert not worktree.has_uncommitted(fake_repo)


# ---- crash recovery ---------------------------------------------------


def test_recover_write_in_progress_with_branch_commit_advances_to_done(fake_repo, monkeypatch):
    slug = _bootstrap(fake_repo)
    stages.audit_one(slug)
    stages.route_one(slug)
    monkeypatch.setattr(
        stages, "dispatch",
        _stubbed_dispatch(_writer_stub_output(), _review_approve_output()),
    )
    # Start the write, then simulate SIGKILL: manually reset stage to
    # WRITE_IN_PROGRESS after the branch has a commit.
    stages.write_one(slug, timeout=10)
    st = state.load_state(slug)
    assert st["stage"] == "WRITE_DONE"
    committed_sha = st["write"]["commit_sha"]
    # Simulate SIGKILL scenario: stage back to WRITE_IN_PROGRESS, branch
    # still has the commit.
    st["stage"] = "WRITE_IN_PROGRESS"
    state.save_state(st)

    stages.recover_in_progress(slug)
    st = state.load_state(slug)
    assert st["stage"] == "WRITE_DONE"
    assert st["write"]["commit_sha"] == committed_sha
    assert st["write"].get("recovered") is True


def test_recover_write_in_progress_with_no_branch_reverts_to_pending(fake_repo):
    slug = _bootstrap(fake_repo)
    st = state.load_state(slug)
    st["stage"] = "WRITE_IN_PROGRESS"
    st["attempt_id"] = "abcdef123456"
    state.save_state(st)

    stages.recover_in_progress(slug)
    st = state.load_state(slug)
    assert st["stage"] == "WRITE_PENDING"


def test_recover_review_in_progress_reverts_to_pending(fake_repo):
    slug = _bootstrap(fake_repo)
    st = state.load_state(slug)
    st["stage"] = "REVIEW_IN_PROGRESS"
    state.save_state(st)
    stages.recover_in_progress(slug)
    st = state.load_state(slug)
    assert st["stage"] == "REVIEW_PENDING"


# ---- full-pipeline happy path ----------------------------------------


def test_full_pipeline_single_module_ends_committed(fake_repo, monkeypatch):
    slug = _bootstrap(fake_repo)
    monkeypatch.setattr(
        stages, "dispatch",
        _stubbed_dispatch(_writer_stub_output(), _review_approve_output()),
    )
    monkeypatch.setattr(
        stages, "process_module_citations",
        lambda p, *, verifier=None, fetcher=None: CitationResult(new_text=p.read_text(), had_sources_section=False),
    )

    terminal = stages.run_module(slug)
    assert terminal == "COMMITTED"

    st = state.load_state(slug)
    assert st["write"]["commit_sha"]
    assert st["review"]["verdict"] == "approve"
    assert st["commit"]["sha"]
    # Primary has the new content.
    new_text = (fake_repo / st["module_path"]).read_text()
    assert "Rewritten pedagogically sound content" in new_text
    # Worktree torn down.
    assert not worktree.worktree_dir(fake_repo, slug).exists()


# ---- pipeline CLI helpers ---------------------------------------------


def test_iter_all_modules_excludes_uk_and_index(fake_repo, monkeypatch):
    # Seed a UK translation and an index.md — both must be excluded.
    (fake_repo / "src/content/docs/uk/cka").mkdir(parents=True, exist_ok=True)
    (fake_repo / "src/content/docs/uk/cka/module-1.1-pods.md").write_text("---\ntitle: UK\n---\n")
    (fake_repo / "src/content/docs/k8s/cka/index.md").write_text("---\ntitle: Index\n---\n")
    modules = pipeline.iter_all_modules()
    assert all("/uk/" not in p.as_posix() for p in modules)
    assert all(p.name != "index.md" for p in modules)


def test_bootstrap_is_idempotent(fake_repo, monkeypatch):
    class NSMock:
        pass

    ns = NSMock()
    pipeline.cmd_bootstrap(ns)  # type: ignore[arg-type]
    first_slugs = state.iter_state_slugs()
    pipeline.cmd_bootstrap(ns)  # type: ignore[arg-type]
    second_slugs = state.iter_state_slugs()
    assert first_slugs == second_slugs


def test_bootstrap_migrates_v1_state_missing_module_index(fake_repo, monkeypatch):
    """v1 state files had no ``module_index``. Bootstrap must add it
    without destroying audit / history fields — non-destructive migration.
    """
    # Seed a v1-shaped state (no module_index, has audit + history).
    modules = pipeline.iter_all_modules()
    assert modules
    slug = state.slug_for(modules[0])
    state.STATE_DIR.mkdir(parents=True, exist_ok=True)
    v1_state = {
        "slug": slug,
        "module_path": modules[0].relative_to(fake_repo).as_posix(),
        "stage": "AUDITED",
        "audit": {"teaching_score": 3.0, "teaching_gaps": ["thin"]},
        "history": [{"at": "2026-04-24T00:00:00Z", "stage": "AUDITED", "note": "v1"}],
        "retry_count": 0,
    }
    state.save_state(v1_state)

    class NSMock:
        pass

    pipeline.cmd_bootstrap(NSMock())  # type: ignore[arg-type]
    migrated = state.load_state(slug)
    assert migrated is not None
    assert migrated["module_index"] == 0  # first module in sorted order
    # Pre-existing fields preserved.
    assert migrated["stage"] == "AUDITED"
    assert migrated["audit"]["teaching_score"] == 3.0
    assert migrated["history"][0]["note"] == "v1"


# ---- Codex v2-review fatals + musts --------------------------------


def _high_score_module_setup(fake_repo: Path) -> str:
    """Helper: seed a module at high audit score + complete structure
    so route_one sends it to CITATION_CLEANUP_ONLY.

    COMMITS the module content — the cleanup-only path creates a
    worktree from ``main``'s tip, so uncommitted primary changes would
    be invisible to the citation pass.
    """
    slug = _bootstrap(fake_repo)
    st = state.load_state(slug)
    assert st is not None
    st["audit"] = {"teaching_score": 4.5, "teaching_gaps": []}
    st["stage"] = "AUDITED"
    state.save_state(st)
    module_path = fake_repo / st["module_path"]
    module_path.write_text("""---
title: Pods
sidebar:
  order: 1
---

# Body

## Quiz

Q.

## Hands-On Exercise

Do.

## Common Mistakes

Table.

## Did You Know?

Facts.

## Sources

- [Official docs](https://kubernetes.io/docs/) — authoritative reference

## Next
""")
    subprocess.run(["git", "add", st["module_path"]], cwd=fake_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "seed high-score module"],
        cwd=fake_repo, check=True, capture_output=True,
    )
    stages.route_one(slug)
    return slug


def test_cleanup_only_never_writes_primary_checkout(fake_repo, monkeypatch):
    """Codex fatal #1 regression guard.

    CITATION_CLEANUP_ONLY path must NOT mutate the primary module file.
    All work happens in a throwaway worktree from main.
    """
    slug = _high_score_module_setup(fake_repo)
    st = state.load_state(slug)
    assert st["stage"] == "CITATION_CLEANUP_ONLY"
    primary_module = fake_repo / st["module_path"]
    primary_content_before = primary_module.read_text()

    # Citation has a removal, so result.changed is True.
    def partial_verifier(_prompt):
        return DispatchResult(
            ok=True,
            stdout=json.dumps({"verdict": "partial", "reasoning": "weak", "excerpt": ""}),
            stderr="", returncode=0, duration_sec=0.1, agent="gemini", model=None,
        )

    stages.citation_verify_one(
        slug, verifier_fn=partial_verifier, fetcher_fn=lambda _u: "page"
    )
    # Primary must be byte-identical through the cleanup-only stage.
    assert primary_module.read_text() == primary_content_before

    # The work landed on a worktree branch, not main.
    st = state.load_state(slug)
    assert st["stage"] == "REVIEW_APPROVED"
    assert worktree.current_branch(fake_repo) == "main"
    assert not worktree.has_uncommitted(fake_repo)
    wt = worktree.worktree_dir(fake_repo, slug)
    assert wt.exists()
    # Worktree version has the removed citation; primary still does not.
    assert "kubernetes.io/docs" not in (wt / st["module_path"]).read_text()
    assert "kubernetes.io/docs" in primary_content_before


def test_cleanup_only_no_changes_ends_at_skipped_without_merge(fake_repo, monkeypatch):
    """Codex fatal #2 regression guard.

    When every citation verifies as 'supports', the cleanup-only path
    must NOT create a mergeable branch. It terminates at SKIPPED and
    tears down the throwaway worktree.
    """
    slug = _high_score_module_setup(fake_repo)

    def supports_verifier(_prompt):
        return DispatchResult(
            ok=True,
            stdout=json.dumps({"verdict": "supports", "reasoning": "direct", "excerpt": "q"}),
            stderr="", returncode=0, duration_sec=0.1, agent="gemini", model=None,
        )

    stages.citation_verify_one(
        slug, verifier_fn=supports_verifier, fetcher_fn=lambda _u: "page"
    )
    st = state.load_state(slug)
    assert st["stage"] == "SKIPPED"
    # Worktree torn down — no merge required.
    assert not worktree.worktree_dir(fake_repo, slug).exists()
    # No branch left over.
    import subprocess as _sp
    branch = worktree.branch_name(slug)
    rc = _sp.run(
        ["git", "rev-parse", "--verify", branch], cwd=fake_repo, capture_output=True
    ).returncode
    assert rc != 0, "branch should be cleaned up"


def test_citation_verify_is_resumable_after_sigkill(fake_repo, monkeypatch):
    """Codex must #3 regression guard.

    If a SIGKILL lands after CITATION_VERIFY transition but before
    completion, re-running citation_verify_one should resume (not
    raise and not duplicate the transition).
    """
    slug = _high_score_module_setup(fake_repo)
    # Simulate "entered CITATION_VERIFY, then process died" by manually
    # setting the state without completing the work.
    st = state.load_state(slug)
    st["stage"] = "CITATION_VERIFY"
    st["citation_origin"] = "CITATION_CLEANUP_ONLY"
    state.save_state(st)

    def partial_verifier(_prompt):
        return DispatchResult(
            ok=True,
            stdout=json.dumps({"verdict": "partial", "reasoning": "weak", "excerpt": ""}),
            stderr="", returncode=0, duration_sec=0.1, agent="gemini", model=None,
        )

    # Resume — must not raise, must complete.
    stages.citation_verify_one(
        slug, verifier_fn=partial_verifier, fetcher_fn=lambda _u: "page"
    )
    st = state.load_state(slug)
    assert st["stage"] in ("REVIEW_APPROVED", "SKIPPED")  # depends on changes
    # _STAGE_FN also has CITATION_VERIFY handler so run_module can drive it.
    assert "CITATION_VERIFY" in stages._STAGE_FN


def test_recovery_does_not_trust_stale_branch_at_old_main(fake_repo, monkeypatch):
    """Codex must #4 regression guard.

    A branch sitting at the old main tip (no writer commit appended)
    should NOT falsely count as a completed write after main advances.
    """
    slug = _bootstrap(fake_repo)
    stages.audit_one(slug)
    stages.route_one(slug)

    import subprocess as _sp
    # Create the worktree/branch at current main, simulating the
    # writer's worktree just after create_worktree but before commit.
    worktree.create_worktree(fake_repo, slug)
    # Advance main via an unrelated commit on the primary.
    (fake_repo / "UNRELATED.md").write_text("advance\n")
    _sp.run(["git", "add", "UNRELATED.md"], cwd=fake_repo, check=True)
    _sp.run(["git", "commit", "-m", "unrelated"], cwd=fake_repo, check=True, capture_output=True)

    # Mark state WRITE_IN_PROGRESS as if a SIGKILL had landed pre-commit.
    st = state.load_state(slug)
    st["stage"] = "WRITE_IN_PROGRESS"
    st["attempt_id"] = "deadbeef"
    state.save_state(st)

    stages.recover_in_progress(slug)
    st = state.load_state(slug)
    # Branch never had a commit AHEAD of main, so recovery MUST revert.
    assert st["stage"] == "WRITE_PENDING"


def test_failed_modules_have_branches_cleaned_up(fake_repo, monkeypatch):
    """Codex must #9 regression guard.

    record_failure via _fail_and_cleanup must delete the worktree branch
    so FAILED modules don't leak branches forever.
    """
    slug = _bootstrap(fake_repo)
    stages.audit_one(slug)
    stages.route_one(slug)

    # Force a write failure by making Codex output malformed.
    def bad_dispatch(agent, prompt, *, timeout, model=None, cwd=None):
        return DispatchResult(
            ok=True, stdout="garbage no frontmatter",
            stderr="", returncode=0, duration_sec=0.1, agent=agent, model=model,
        )
    monkeypatch.setattr(stages, "dispatch", bad_dispatch)

    stages.write_one(slug, timeout=10)
    st = state.load_state(slug)
    assert st["stage"] == "FAILED"

    # Branch deleted.
    import subprocess as _sp
    branch = worktree.branch_name(slug)
    rc = _sp.run(
        ["git", "rev-parse", "--verify", branch], cwd=fake_repo, capture_output=True
    ).returncode
    assert rc != 0, "FAILED module must not leak its branch"
    # Worktree gone.
    assert not worktree.worktree_dir(fake_repo, slug).exists()


def test_approve_verdict_demoted_when_score_below_gate() -> None:
    """Codex must #7 regression guard.

    ``verdict=approve`` with numeric rubric_score < 4.0 must be
    demoted to ``changes_requested`` with a must_fix note.
    """
    payload = json.dumps({
        "verdict": "approve",
        "rubric_score": 3.0,
        "teaching_score": 4.5,
        "must_fix": [],
    })
    result = DispatchResult(
        ok=True, stdout=payload, stderr="", returncode=0,
        duration_sec=0.1, agent="claude", model=None,
    )
    verdict = stages._parse_review_verdict(result)
    assert verdict is not None
    assert verdict["verdict"] == "changes_requested"
    assert verdict.get("score_gate_demotion") is True
    assert any("scores don't meet" in m or "score" in m.lower() for m in verdict["must_fix"])


def test_approve_verdict_demoted_when_score_missing() -> None:
    payload = json.dumps({
        "verdict": "approve",
        "rubric_score": "n/a",  # non-numeric
        "teaching_score": 4.5,
        "must_fix": [],
    })
    result = DispatchResult(
        ok=True, stdout=payload, stderr="", returncode=0,
        duration_sec=0.1, agent="claude", model=None,
    )
    verdict = stages._parse_review_verdict(result)
    assert verdict is not None
    assert verdict["verdict"] == "changes_requested"


def test_approve_verdict_kept_when_both_scores_meet_gate() -> None:
    payload = json.dumps({
        "verdict": "approve",
        "rubric_score": 4.2,
        "teaching_score": 4.0,
        "must_fix": [],
    })
    result = DispatchResult(
        ok=True, stdout=payload, stderr="", returncode=0,
        duration_sec=0.1, agent="claude", model=None,
    )
    verdict = stages._parse_review_verdict(result)
    assert verdict is not None
    assert verdict["verdict"] == "approve"
    assert verdict.get("score_gate_demotion") is not True


def test_merge_retries_on_transient_rebase_failure(fake_repo, monkeypatch):
    """Codex must #5 regression guard for the retry aspect.

    When rebase/ff fails (simulating a lost race — another worker landed
    on main first), merge_one should re-enter the lock + re-rebase +
    re-merge up to ``_MERGE_RETRY_CAP`` times rather than marking FAILED
    on first failure. This lets workers>1 operate without incorrectly
    killing racing modules.
    """
    slug = _bootstrap(fake_repo)
    monkeypatch.setattr(
        stages, "dispatch",
        _stubbed_dispatch(_writer_stub_output(), _review_approve_output()),
    )
    monkeypatch.setattr(
        stages, "process_module_citations",
        lambda p, *, verifier=None, fetcher=None: CitationResult(new_text=p.read_text(), had_sources_section=False),
    )
    stages.audit_one(slug)
    stages.route_one(slug)
    stages.write_one(slug, timeout=10)
    stages.citation_verify_one(slug)
    stages.review_one(slug, timeout=10)

    calls = {"rebase": 0}
    real_rebase = stages.rebase_onto_main

    def flaky_rebase(primary, slug_arg, **kw):
        calls["rebase"] += 1
        if calls["rebase"] == 1:
            raise worktree.WorktreeError("simulated race: another merge landed first")
        return real_rebase(primary, slug_arg, **kw)

    monkeypatch.setattr(stages, "rebase_onto_main", flaky_rebase)
    stages.merge_one(slug)

    st = state.load_state(slug)
    assert st["stage"] == "COMMITTED", f"retry should succeed after transient failure, got {st['stage']}"
    assert calls["rebase"] == 2, "rebase should have been retried once"


def test_write_cleanup_even_when_commit_fails(fake_repo, monkeypatch):
    """Codex must #8 regression guard.

    If git add/commit/rev-parse (post-dispatch operations) raise, the
    worktree + branch must still be cleaned up — the write path's
    try/except BaseException catches all exception classes.
    """
    slug = _bootstrap(fake_repo)
    stages.audit_one(slug)
    stages.route_one(slug)
    # Writer dispatch succeeds with valid module content.
    monkeypatch.setattr(stages, "dispatch", _stubbed_dispatch(_writer_stub_output(), ""))

    # But let git commit raise — simulate a post-dispatch git failure.
    original_run = subprocess.run

    def boomy_run(args, *a, **k):
        if args[:2] == ["git", "commit"]:
            raise subprocess.CalledProcessError(1, args, stderr="simulated commit failure")
        return original_run(args, *a, **k)

    monkeypatch.setattr(stages.subprocess, "run", boomy_run)

    with pytest.raises(subprocess.CalledProcessError):
        stages.write_one(slug, timeout=10)

    # Worktree + branch removed despite the crash mid-stage.
    assert not worktree.worktree_dir(fake_repo, slug).exists()
    import subprocess as _sp
    branch = worktree.branch_name(slug)
    rc = _sp.run(
        ["git", "rev-parse", "--verify", branch], cwd=fake_repo, capture_output=True
    ).returncode
    assert rc != 0


def test_run_order_is_worst_first(fake_repo, monkeypatch):
    # Add a second module with HIGHER score.
    mod2_rel = "src/content/docs/k8s/cka/module-1.2-services.md"
    (fake_repo / mod2_rel).parent.mkdir(parents=True, exist_ok=True)
    (fake_repo / mod2_rel).write_text("---\ntitle: Services\nsidebar:\n  order: 2\n---\n\n")
    audit_dir = fake_repo / ".pipeline" / "teaching-audit"
    slug2 = "k8s-cka-module-1.2-services"
    (audit_dir / f"{slug2}.json").write_text(json.dumps({
        "teaching_score": 3.9, "teaching_gaps": [],
    }))
    subprocess.run(["git", "add", "-A"], cwd=fake_repo, check=True)
    subprocess.run(["git", "commit", "-m", "m2"], cwd=fake_repo, check=True, capture_output=True)

    # Bootstrap so both have state + audit.
    modules = pipeline.iter_all_modules()
    for i, m in enumerate(modules):
        st = state.new_state(m, module_index=i)
        state.save_state(st)
        stages.audit_one(state.slug_for(m))

    slugs = state.iter_state_slugs()
    ordered = pipeline._order_worst_first(slugs)
    # Module 1.1 (score 2.5) should come before module 1.2 (score 3.9).
    assert ordered.index("k8s-cka-module-1.1-pods") < ordered.index(slug2)
