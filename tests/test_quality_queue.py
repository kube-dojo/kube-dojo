"""Queue routing + writer stickiness + model→agent translator (#388)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.quality import queue, state
from conftest import _read_frontmatter


@pytest.fixture
def tmp_repo(tmp_path: Path, monkeypatch):
    """Minimal repo skeleton + content root + state dir, all pointed at tmp."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "src" / "content" / "docs").mkdir(parents=True)
    monkeypatch.setattr(state, "REPO_ROOT", repo)
    monkeypatch.setattr(state, "STATE_DIR", repo / ".pipeline" / "quality-pipeline")
    monkeypatch.setattr(state, "CONTENT_ROOT", repo / "src" / "content" / "docs")
    return repo


def _seed_module(repo: Path, rel: str, *, complexity: str | None = None, with_state: bool = True) -> Path:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    fm_extra = f"complexity: {complexity}\n" if complexity else ""
    p.write_text(f"---\ntitle: T\n{fm_extra}---\n\nbody\n")
    if with_state:
        st = state.new_state(p, module_index=0)
        state.save_state(st)
    return p


# ---- model_to_agent translator ----------------------------------------


def test_model_to_agent_known_models():
    assert queue.model_to_agent(queue.PRIMARY_BEGINNER) == ("agy", queue.PRIMARY_BEGINNER)
    assert queue.model_to_agent(queue.PRIMARY_ADVANCED) == ("agy", queue.PRIMARY_ADVANCED)
    assert queue.model_to_agent(queue.TERTIARY) == ("claude", queue.TERTIARY)


def test_model_to_agent_unknown_raises():
    with pytest.raises(ValueError, match="unknown writer model"):
        queue.model_to_agent("not-a-real-model")


# ---- route_writer rules -----------------------------------------------


def test_route_writer_complexity_quick_routes_beginner(tmp_repo):
    p = _seed_module(tmp_repo, "src/content/docs/k8s/cka/x.md", complexity="quick")
    assert queue.route_writer(p) == queue.PRIMARY_BEGINNER


def test_route_writer_complexity_complex_routes_advanced(tmp_repo):
    p = _seed_module(tmp_repo, "src/content/docs/ai/foundations/x.md", complexity="complex")
    assert queue.route_writer(p) == queue.PRIMARY_ADVANCED


def test_route_writer_track_beginner_falls_back_to_gemini(tmp_repo):
    p = _seed_module(tmp_repo, "src/content/docs/ai/foundations/m.md")
    assert queue.route_writer(p) == queue.PRIMARY_BEGINNER


def test_route_writer_track_advanced_falls_back_to_codex(tmp_repo):
    p = _seed_module(tmp_repo, "src/content/docs/k8s/cka/m.md")
    assert queue.route_writer(p) == queue.PRIMARY_ADVANCED


def test_route_writer_unknown_track_routes_tertiary(tmp_repo):
    p = _seed_module(tmp_repo, "src/content/docs/uncategorized/m.md")
    assert queue.route_writer(p) == queue.TERTIARY


# ---- ensure_queued + banner toggle ------------------------------------


def test_ensure_queued_default_sets_banner(tmp_repo):
    p = _seed_module(tmp_repo, "src/content/docs/ai/foundations/m.md")
    slug = state.slug_for(p)
    queue.ensure_queued(slug, p)
    assert "revision_pending: true" in p.read_text()


def test_ensure_queued_no_banner_keeps_frontmatter_clean(tmp_repo):
    p = _seed_module(tmp_repo, "src/content/docs/ai/foundations/m.md")
    slug = state.slug_for(p)
    before = p.read_text()
    queue.ensure_queued(slug, p, set_banner=False)
    assert p.read_text() == before  # not mutated
    # but the queue doc IS attached
    st = state.load_state(slug)
    assert st is not None and "queue" in st


def test_ensure_queued_is_idempotent_in_writer_choice(tmp_repo):
    """Re-calling ensure_queued does NOT re-route (stickiness preserved)."""
    p = _seed_module(tmp_repo, "src/content/docs/ai/foundations/m.md")
    slug = state.slug_for(p)
    first = queue.ensure_queued(slug, p, set_banner=False)
    # Mutate the file's frontmatter to change the route_writer output —
    # if ensure_queued re-routed, we'd see the new writer.
    p.write_text(p.read_text().replace("title: T\n", "title: T\ncomplexity: complex\n"))
    second = queue.ensure_queued(slug, p, set_banner=False)
    assert first["assigned_writer"] == second["assigned_writer"]


def test_set_citations_verified_frontmatter_sets_and_removes(tmp_repo):
    p = _seed_module(tmp_repo, "src/content/docs/ai/foundations/m.md")
    queue.set_citations_verified_frontmatter(p)
    fm = _read_frontmatter(p)
    assert fm["citations_verified"] is True

    queue.set_citations_verified_frontmatter(p, verified=False)
    fm = _read_frontmatter(p)
    assert "citations_verified" not in fm


def test_set_citations_verified_frontmatter_keeps_other_frontmatter_keys(tmp_repo):
    p = tmp_repo / "src/content/docs/ai/foundations/m.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("""---
title: M
sidebar:
  order: 4
complexity: quick
---

body
""")
    queue.set_citations_verified_frontmatter(p)
    fm = _read_frontmatter(p)
    assert fm["title"] == "M"
    assert fm["sidebar"] == {"order": 4}
    assert fm["complexity"] == "quick"
    assert fm["citations_verified"] is True


def test_set_citations_verified_frontmatter_is_idempotent_for_true(tmp_repo):
    p = _seed_module(tmp_repo, "src/content/docs/ai/foundations/m.md")
    first = p.read_bytes()
    queue.set_citations_verified_frontmatter(p)
    second = p.read_bytes()
    queue.set_citations_verified_frontmatter(p)
    third = p.read_bytes()
    assert first != second
    assert second == third


# ---- claim ------------------------------------------------------------


def test_claim_returns_writer_when_not_blocked(tmp_repo):
    p = _seed_module(tmp_repo, "src/content/docs/ai/foundations/m.md")
    slug = state.slug_for(p)
    queue.ensure_queued(slug, p, set_banner=False)
    claim = queue.claim(slug)
    assert claim.writer == queue.PRIMARY_BEGINNER
    assert claim.reason is None


def test_claim_returns_none_when_blocked(tmp_repo):
    p = _seed_module(tmp_repo, "src/content/docs/ai/foundations/m.md")
    slug = state.slug_for(p)
    queue.ensure_queued(slug, p, set_banner=False)
    queue.record_attempt_start(slug)
    queue.record_block(slug, "rate limit")
    claim = queue.claim(slug)
    assert claim.writer is None
    assert "blocked" in (claim.reason or "")


def test_claim_returns_none_when_completed(tmp_repo):
    p = _seed_module(tmp_repo, "src/content/docs/ai/foundations/m.md")
    slug = state.slug_for(p)
    queue.ensure_queued(slug, p, set_banner=False)
    queue.record_completion(slug, p)
    claim = queue.claim(slug)
    assert claim.writer is None
    assert claim.reason == "already completed"
