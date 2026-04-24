"""Per-stage orchestration: audit / route / write / verify / review / merge.

The state machine lives in :mod:`state` (durable states + leases + CAS).
This module drives state forward by calling dispatchers, running the
citation verify pass inside a per-module worktree, and calling the
worktree helpers to merge cleanly.

Directly closes the remaining Codex must-fixes:

* **#1** — :func:`review_one` reads the module from the writer's
  worktree, not from ``main``. The v1 bug was catastrophic: reviewer
  always approved because the worktree changes were invisible to it.
* **#4** — :func:`handle_review_changes` routes ``REVIEW_CHANGES`` back
  to ``WRITE_PENDING`` with the reviewer's ``must_fix`` list as
  retry context, bumping ``retry_count``. After ``RETRY_CAP`` retries,
  :func:`tiebreaker_one` calls Gemini to break the loop.

And the crash-resume correctness:

* **#5 (runtime half)** — :func:`recover_in_progress` reconciles
  ``WRITE_IN_PROGRESS`` / ``REVIEW_IN_PROGRESS`` state on startup. If
  the writer's branch has a commit, advance to ``WRITE_DONE`` (don't
  redo the work); else revert to ``WRITE_PENDING``. Pairs with the
  ``attempt_id`` stamping from :mod:`state.start_in_progress`.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from . import state
from .citations import process_module_citations
from .dispatchers import (
    DispatcherUnavailable,
    DispatchResult,
    dispatch,
    tiebreaker_agent,
    writer_for_index,
)
from .extractors import (
    JsonExtractError,
    ModuleExtractError,
    extract_last_json,
    extract_module_markdown,
)
from .prompts import (
    build_audit_context,
    review_prompt,
    rewrite_prompt,
    structural_prompt,
)
from .worktree import (
    WorktreeError,
    branch_name,
    create_worktree,
    current_branch,
    has_uncommitted,
    merge_ff_only,
    primary_checkout_root,
    rebase_onto_main,
    remove_worktree,
    worktree_dir,
)


_REPO_ROOT = primary_checkout_root(Path(__file__).resolve().parents[2])
_AUDIT_DIR = _REPO_ROOT / ".pipeline" / "teaching-audit"
_AUDIT_SCRIPT = _REPO_ROOT / "scripts" / "audit_teaching_quality.py"
_VENV_PYTHON = str(_REPO_ROOT / ".venv" / "bin" / "python")

RETRY_CAP = 2
"""Codex↔Claude retries before Gemini tiebreaks. Per #375 locked requirements."""

SCORE_SKIP_THRESHOLD = 4.0
"""Audit score at or above which the rewrite stage is skipped. Citation
verify still runs unconditionally."""


class StageError(RuntimeError):
    """Stage couldn't complete for non-retryable reasons (parse fail, git fail, etc.).

    Callers mark the module ``FAILED`` with ``str(exc)`` as the reason.
    """


# ---- helpers -----------------------------------------------------------


def _primary() -> Path:
    return _REPO_ROOT


def _module_path(st: dict[str, Any]) -> Path:
    return _REPO_ROOT / st["module_path"]


def _module_path_in_worktree(slug: str, module_relpath: str) -> Path:
    return worktree_dir(_primary(), slug) / module_relpath


def _audit_json_for(slug: str) -> Path:
    return _AUDIT_DIR / f"{slug}.json"


def _audit_score(audit: dict[str, Any]) -> float:
    """Extract the numeric teaching-score from an audit payload.

    The audit script's schema uses ``teaching_score`` (v3 script); older
    variants used ``score``. Return a conservative fallback (1.0) if
    neither is present so the pipeline treats unknown-schema modules as
    needing rewrite rather than skipping.
    """
    for key in ("teaching_score", "score", "rubric_score"):
        v = audit.get(key)
        if isinstance(v, (int, float)):
            return float(v)
    return 1.0


# ---- audit stage -------------------------------------------------------


def audit_one(slug: str, *, timeout: int = 600) -> None:
    """UNAUDITED → AUDITED. Reuses ``.pipeline/teaching-audit/<slug>.json``
    if already present; otherwise subprocesses ``audit_teaching_quality.py``
    to produce one.

    Kept as a subprocess (not an import) so one module's audit crash
    doesn't contaminate the in-process state.
    """
    audit_file = _audit_json_for(slug)
    with state.state_lease(slug) as lease:
        st = lease.load()
        if st is None:
            raise StageError(f"state missing for {slug}")
        if st["stage"] != "UNAUDITED":
            return  # another worker advanced it already

        if not audit_file.exists():
            module_rel = st["module_path"]
            cmd = [
                _VENV_PYTHON,
                str(_AUDIT_SCRIPT),
                "--module",
                module_rel,
            ]
            proc = subprocess.run(
                cmd, cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=timeout + 30
            )
            if proc.returncode != 0 or not audit_file.exists():
                state.record_failure(st, f"audit failed: {proc.stderr.strip()[:400]}")
                return

        audit = json.loads(audit_file.read_text(encoding="utf-8"))
        state.transition(st, "UNAUDITED", "AUDITED", audit=audit, note="audit promoted")


# ---- route stage -------------------------------------------------------


def route_one(slug: str) -> None:
    """AUDITED → ROUTED / SKIPPED / CITATION_CLEANUP_ONLY.

    Route rules:
    * score ≥ 4.0 AND no missing structural sections → ``CITATION_CLEANUP_ONLY``
      (citation pass still runs — everything goes through verify)
    * score ≥ 4.0 BUT missing quiz/exercise → ``ROUTED`` with track=structural
    * score < 4.0 → ``ROUTED`` with track=rewrite
    """
    with state.state_lease(slug) as lease:
        st = lease.load()
        if st is None:
            raise StageError(f"state missing for {slug}")
        if st["stage"] != "AUDITED":
            return

        audit = st.get("audit") or {}
        score = _audit_score(audit)
        missing = _missing_structural_sections(_module_path(st).read_text(encoding="utf-8"))

        if score >= SCORE_SKIP_THRESHOLD and not missing:
            state.transition(
                st, "AUDITED", "CITATION_CLEANUP_ONLY",
                route={"reason": f"score {score:.1f} + structure complete", "track": "cleanup_only"},
                note=f"skip rewrite (score {score:.1f})",
            )
            return

        track = "rewrite" if score < SCORE_SKIP_THRESHOLD else "structural"
        writer, reviewer = writer_for_index(st["module_index"])
        state.transition(
            st, "AUDITED", "ROUTED",
            route={"track": track, "score": score, "missing": missing},
            writer=writer,
            reviewer=reviewer,
            note=f"track={track} writer={writer}",
        )
        # ROUTED → WRITE_PENDING in the same lease so the run-loop can
        # pick this up as a writable module immediately.
        state.transition(st, "ROUTED", "WRITE_PENDING", note="queued for write")


def _missing_structural_sections(text: str) -> list[str]:
    """Detect missing required sections by heading pattern.

    Deliberately simple — matches on heading text rather than any
    structural parsing. The ``quiz_details_check`` is filtered out of
    the ``has_diagram`` false-positive class (v1 bug noted in Codex
    should-fix list: quiz ``<details>`` were mis-counted as diagrams).
    """
    lowered = text.lower()
    missing: list[str] = []
    if "## quiz" not in lowered and "## self-check" not in lowered:
        missing.append("quiz")
    if "## hands-on" not in lowered and "## lab" not in lowered and "## exercise" not in lowered:
        missing.append("hands-on-exercise")
    if "## common mistake" not in lowered:
        missing.append("common-mistakes")
    if "## did you know" not in lowered:
        missing.append("did-you-know")
    return missing


# ---- write stage -------------------------------------------------------


def write_one(slug: str, *, timeout: int = 900) -> None:
    """WRITE_PENDING → WRITE_IN_PROGRESS → WRITE_DONE.

    Holds the lease for the full subprocess duration. On SIGKILL the
    state stays at ``WRITE_IN_PROGRESS`` with the current ``attempt_id``;
    :func:`recover_in_progress` reconciles on the next run.

    If the dispatcher is unavailable (peak hours, budget), REVERTS the
    state to ``WRITE_PENDING`` and leaves the module for a later
    invocation — the module is not FAILED.
    """
    with state.state_lease(slug, timeout=5.0) as lease:
        st = lease.load()
        if st is None or st["stage"] != "WRITE_PENDING":
            return

        attempt_id = state.start_in_progress(st, "WRITE_PENDING", "WRITE_IN_PROGRESS")
        try:
            wt, commit_sha = _write_in_worktree(st, timeout=timeout, attempt_id=attempt_id)
        except DispatcherUnavailable:
            # Revert — module stays retryable, branch cleaned up.
            remove_worktree(_primary(), slug, delete_branch=True)
            state.transition(
                st, "WRITE_IN_PROGRESS", "WRITE_PENDING",
                note="dispatcher unavailable; will retry",
            )
            raise
        except (ModuleExtractError, WorktreeError, StageError) as exc:
            remove_worktree(_primary(), slug, delete_branch=False)
            state.record_failure(st, f"write: {exc}")
            return

        state.transition(
            st, "WRITE_IN_PROGRESS", "WRITE_DONE",
            write={
                "agent": st["writer"],
                "attempt_id": attempt_id,
                "commit_sha": commit_sha,
                "worktree": str(wt.relative_to(_REPO_ROOT)),
            },
            note=f"{st['writer']} wrote {commit_sha[:8]}",
        )


def _write_in_worktree(
    st: dict[str, Any], *, timeout: int, attempt_id: str
) -> tuple[Path, str]:
    """Dispatch the writer inside a worktree and commit. Returns ``(wt, sha)``.

    Must NOT commit the state transition — caller handles that under the
    lease so a lease-rejection doesn't leave a stale git commit.
    """
    slug = st["slug"]
    writer = st["writer"]
    track = (st.get("route") or {}).get("track", "rewrite")
    module_rel = st["module_path"]

    # Build prompt from the ORIGINAL module content, not the worktree's
    # copy — they start identical but this makes the prompt's "current
    # module content" unambiguous: it's what the audit scored.
    original_text = _module_path(st).read_text(encoding="utf-8")
    audit_gaps = build_audit_context(st.get("audit"))
    retry_must_fix = (st.get("review") or {}).get("must_fix") or []

    if track == "structural":
        missing = (st.get("route") or {}).get("missing") or []
        prompt = structural_prompt(
            module_path=module_rel,
            module_text=original_text,
            missing_sections=missing,
        )
    else:
        prompt = rewrite_prompt(
            module_path=module_rel,
            module_text=original_text,
            teaching_gaps=audit_gaps + [f"(retry) {x}" for x in retry_must_fix],
        )

    # Worktree PERSISTS through the whole module lifecycle (write → citation
    # verify → review → merge). Only teardown paths are:
    # 1. write_one() failure → remove_worktree(delete_branch=False) for postmortem
    # 2. merge_one() success → remove_worktree(delete_branch=True)
    # 3. DispatcherUnavailable → remove_worktree(delete_branch=True) so retry is clean
    # Using ``worktree_session`` here would destroy the worktree before
    # the reviewer (Codex must-fix #1) could read from it.
    wt = create_worktree(_primary(), slug)
    try:
        result = dispatch(writer, prompt, timeout=timeout, cwd=wt)
    except BaseException:
        remove_worktree(_primary(), slug, delete_branch=True)
        raise
    if not result.ok:
        remove_worktree(_primary(), slug, delete_branch=False)
        raise StageError(
            f"{writer} dispatch failed (rc={result.returncode}): "
            f"{result.stderr.strip()[:400]}"
        )
    try:
        extract = extract_module_markdown(result.stdout)
    except ModuleExtractError:
        remove_worktree(_primary(), slug, delete_branch=False)
        raise
    target = wt / module_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(extract.text, encoding="utf-8")
    commit_msg = (
        f"quality({track}): {writer} rewrite {slug} (attempt {attempt_id})\n"
        f"\nRefs #375."
    )
    subprocess.run(
        ["git", "add", module_rel], cwd=wt, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", commit_msg], cwd=wt, check=True, capture_output=True
    )
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=wt, check=True, capture_output=True, text=True
    ).stdout.strip()
    return wt, sha


# ---- citation verify stage --------------------------------------------


def citation_verify_one(slug: str, *, verifier_fn=None) -> None:
    """WRITE_DONE → CITATION_VERIFY → REVIEW_PENDING (or CITATION_CLEANUP_ONLY
    when the skip-rewrite path leads here directly).

    ``verifier_fn`` is injectable for testing; defaults to the live
    Gemini-flash verifier in :mod:`citations`.
    """
    from .citations import default_verifier  # local import avoids import-time side effects

    with state.state_lease(slug) as lease:
        st = lease.load()
        if st is None or st["stage"] not in ("WRITE_DONE", "CITATION_CLEANUP_ONLY"):
            return

        from_stage = st["stage"]
        to_stage = "CITATION_VERIFY"
        state.transition(st, from_stage, to_stage, note=f"verifying citations (from {from_stage})")

    # Citation work outside the lease — it's long and independent of state.
    module_rel = st["module_path"]
    slug = st["slug"]
    if from_stage == "WRITE_DONE":
        module_file = _module_path_in_worktree(slug, module_rel)
    else:
        module_file = _module_path(st)
    if not module_file.exists():
        with state.state_lease(slug) as lease:
            st = lease.load()
            if st is not None:
                state.record_failure(st, f"module file missing at {module_file}")
        return

    result = process_module_citations(
        module_file, verifier=verifier_fn or default_verifier
    )

    with state.state_lease(slug) as lease:
        st = lease.load()
        if st is None:
            return
        citations_meta = {
            "had_sources": result.had_sources_section,
            "kept": len(result.kept),
            "removed": len(result.removed),
            "section_dropped": result.section_dropped,
            "removed_details": [
                {"url": p.entry.url, "verdict": p.verdict.value, "reason": p.reasoning[:200]}
                for p in result.removed
            ],
        }

        if result.changed:
            module_file.write_text(result.new_text, encoding="utf-8")
            if from_stage == "WRITE_DONE":
                # Amend the writer's commit inside the worktree.
                wt = worktree_dir(_primary(), slug)
                subprocess.run(["git", "add", module_rel], cwd=wt, check=True, capture_output=True)
                subprocess.run(
                    ["git", "commit", "--amend", "--no-edit"],
                    cwd=wt, check=True, capture_output=True,
                )
            else:
                # CLEANUP_ONLY path: worktree needed for a clean commit.
                _commit_cleanup_in_worktree(slug, module_rel, citations_meta)

        next_stage = "REVIEW_PENDING" if from_stage == "WRITE_DONE" else "REVIEW_APPROVED"
        state.transition(
            st, "CITATION_VERIFY", next_stage,
            citations=citations_meta,
            note=f"kept={len(result.kept)} removed={len(result.removed)}",
        )


def _commit_cleanup_in_worktree(slug: str, module_rel: str, meta: dict[str, Any]) -> None:
    """For the CITATION_CLEANUP_ONLY path, we need a worktree to commit in.

    The module file was already edited in the primary checkout by the
    caller; we copy the cleaned version into a fresh worktree, commit,
    and let :func:`merge_one` merge it back.
    """
    wt = worktree_dir(_primary(), slug)
    if not wt.exists():
        from .worktree import create_worktree  # local import to avoid cycle
        create_worktree(_primary(), slug)
    # Re-read the post-cleanup text from primary and overwrite in worktree.
    primary_text = (_REPO_ROOT / module_rel).read_text(encoding="utf-8")
    (wt / module_rel).write_text(primary_text, encoding="utf-8")
    msg = f"quality(citations): verify-or-remove for {slug}\n\nRemoved {meta['removed']} unverifiable citation(s).\nRefs #375."
    subprocess.run(["git", "add", module_rel], cwd=wt, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", msg], cwd=wt, check=True, capture_output=True)


# ---- review stage ------------------------------------------------------


def review_one(slug: str, *, timeout: int = 900) -> None:
    """REVIEW_PENDING → REVIEW_IN_PROGRESS → REVIEW_APPROVED / REVIEW_CHANGES.

    Critical: the reviewer reads the module from the WRITER'S WORKTREE.
    v1 bug was catastrophic here — reviewer read from primary (which
    was still on ``main``), always approved because the diff was
    invisible. Fix: ``_module_path_in_worktree``.
    """
    with state.state_lease(slug, timeout=5.0) as lease:
        st = lease.load()
        if st is None or st["stage"] != "REVIEW_PENDING":
            return
        attempt_id = state.start_in_progress(st, "REVIEW_PENDING", "REVIEW_IN_PROGRESS")

        reviewer = st["reviewer"]
        track = (st.get("route") or {}).get("track", "rewrite")
        module_rel = st["module_path"]
        module_file = _module_path_in_worktree(slug, module_rel)
        if not module_file.exists():
            state.record_failure(st, f"review: module missing at {module_file}")
            return
        module_text = module_file.read_text(encoding="utf-8")

        prompt = review_prompt(
            module_path=module_rel,
            module_text=module_text,
            writer_agent=st["writer"],
            track=track,
            original_gaps=build_audit_context(st.get("audit")),
        )

        try:
            result = dispatch(reviewer, prompt, timeout=timeout)
        except DispatcherUnavailable:
            # Revert to REVIEW_PENDING so the next run can re-attempt.
            state.transition(
                st, "REVIEW_IN_PROGRESS", "REVIEW_PENDING",
                note="reviewer unavailable; will retry",
            )
            raise

        if not result.ok:
            state.record_failure(
                st,
                f"review: {reviewer} dispatch failed (rc={result.returncode}): "
                f"{result.stderr.strip()[:400]}",
            )
            return

        verdict = _parse_review_verdict(result)
        if verdict is None:
            state.record_failure(st, "review: could not parse verdict JSON")
            return

        review_meta = {
            "agent": reviewer,
            "attempt_id": attempt_id,
            **verdict,
        }
        if verdict["verdict"] == "approve":
            state.transition(
                st, "REVIEW_IN_PROGRESS", "REVIEW_APPROVED",
                review=review_meta,
                note=f"{reviewer} APPROVE score={verdict.get('rubric_score')}",
            )
        else:
            state.transition(
                st, "REVIEW_IN_PROGRESS", "REVIEW_CHANGES",
                review=review_meta,
                note=f"{reviewer} CHANGES ({len(verdict.get('must_fix') or [])} must-fix)",
            )


def _parse_review_verdict(result: DispatchResult) -> dict[str, Any] | None:
    try:
        payload = extract_last_json(
            result.stdout,
            required_keys={"verdict", "rubric_score", "teaching_score", "must_fix"},
        )
    except JsonExtractError:
        return None
    verdict = str(payload.get("verdict", "")).strip().lower()
    if verdict not in ("approve", "changes_requested"):
        return None
    payload["verdict"] = verdict
    return payload


# ---- review-changes retry ---------------------------------------------


def handle_review_changes(slug: str) -> None:
    """REVIEW_CHANGES → WRITE_PENDING (retry) OR → tiebreaker.

    Closes Codex must-fix #4: the v1 bug was that ``REVIEW_CHANGES`` was
    a state nothing consumed. Here we route it back to the writer with
    the reviewer's ``must_fix`` list, bump ``retry_count``, and cap at
    :data:`RETRY_CAP`. Beyond the cap, :func:`tiebreaker_one` runs.
    """
    with state.state_lease(slug) as lease:
        st = lease.load()
        if st is None or st["stage"] != "REVIEW_CHANGES":
            return
        retry_count = st.get("retry_count", 0)
        if retry_count >= RETRY_CAP:
            # Hand off to Gemini tiebreaker.
            state.transition(
                st, "REVIEW_CHANGES", "REVIEW_PENDING",
                retry_count=retry_count,
                reviewer=tiebreaker_agent(),
                note="retry cap hit; Gemini tiebreaker",
            )
            return
        # Retry: back to WRITE_PENDING with must_fix context preserved.
        state.transition(
            st, "REVIEW_CHANGES", "WRITE_PENDING",
            retry_count=retry_count + 1,
            note=f"retry {retry_count + 1}/{RETRY_CAP}",
        )


# ---- merge stage -------------------------------------------------------


def merge_one(slug: str) -> None:
    """REVIEW_APPROVED → COMMITTED. Rebase worktree branch, ff-merge, tear down.

    The rebase makes sure successive modules in a batch can all merge
    ff-only even as ``main`` advances between them (Codex must-fix #3).
    """
    with state.state_lease(slug) as lease:
        st = lease.load()
        if st is None or st["stage"] != "REVIEW_APPROVED":
            return
        primary = _primary()
        if current_branch(primary) != "main":
            state.record_failure(st, "merge: primary not on main — manual intervention")
            return
        if has_uncommitted(primary):
            state.record_failure(st, "merge: primary has uncommitted changes — manual intervention")
            return
        try:
            rebase_onto_main(primary, slug)
            merge_sha = merge_ff_only(primary, slug)
        except WorktreeError as exc:
            # Rebase or merge failed — could be a race (another merge landed
            # on main). Leave the branch for retry; mark FAILED only after
            # repeated retries would — but that's a run-loop concern.
            state.record_failure(st, f"merge: {exc}")
            return
        remove_worktree(primary, slug, delete_branch=True)
        state.transition(
            st, "REVIEW_APPROVED", "COMMITTED",
            commit={"sha": merge_sha, "branch": branch_name(slug)},
            note=f"merged {merge_sha[:8]}",
        )


# ---- resume logic -----------------------------------------------------


def recover_in_progress(slug: str) -> None:
    """Reconcile a state stuck at ``WRITE_IN_PROGRESS`` / ``REVIEW_IN_PROGRESS``.

    Called by pipeline startup. Idempotent — safe to call on any state.
    """
    with state.state_lease(slug) as lease:
        st = lease.load()
        if st is None:
            return
        if st["stage"] == "WRITE_IN_PROGRESS":
            _recover_write_in_progress(st)
        elif st["stage"] == "REVIEW_IN_PROGRESS":
            # No durable side effect from a half-done review; just revert.
            state.transition(
                st, "REVIEW_IN_PROGRESS", "REVIEW_PENDING",
                note="recovered from WRITE_IN_PROGRESS SIGKILL",
            )


def _recover_write_in_progress(st: dict[str, Any]) -> None:
    """If the worktree's branch has the module commit, advance to WRITE_DONE.
    Otherwise revert to WRITE_PENDING."""
    slug = st["slug"]
    primary = _primary()
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--verify", branch_name(slug)],
            cwd=primary, capture_output=True, text=True, check=False,
        ).stdout.strip()
    except Exception:
        sha = ""

    if sha and sha != _main_sha():
        # There's a commit on the branch that isn't already on main — trust it.
        state.transition(
            st, "WRITE_IN_PROGRESS", "WRITE_DONE",
            write={
                "agent": st.get("writer"),
                "attempt_id": st.get("attempt_id"),
                "commit_sha": sha,
                "worktree": f".worktrees/quality-{slug}",
                "recovered": True,
            },
            note="recovered WRITE_IN_PROGRESS: branch had a commit",
        )
    else:
        # Nothing to salvage — scrub and retry.
        remove_worktree(primary, slug, delete_branch=True)
        state.transition(
            st, "WRITE_IN_PROGRESS", "WRITE_PENDING",
            note="recovered WRITE_IN_PROGRESS: nothing on branch, requeued",
        )


def _main_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "main"], cwd=_primary(), capture_output=True, text=True, check=False
    ).stdout.strip()


# ---- driver (single module through all stages) ------------------------


_STAGE_FN = {
    "UNAUDITED": audit_one,
    "AUDITED": route_one,
    "ROUTED": route_one,  # double-checked by route_one itself
    "WRITE_PENDING": write_one,
    "WRITE_DONE": citation_verify_one,
    "CITATION_CLEANUP_ONLY": citation_verify_one,
    "REVIEW_PENDING": review_one,
    "REVIEW_CHANGES": handle_review_changes,
    "REVIEW_APPROVED": merge_one,
}


def run_module(slug: str, *, max_cycles: int = 20) -> str:
    """Drive a single slug through stages until it reaches a terminal state
    or stops making progress.

    Returns the final stage name. ``max_cycles`` guards against a buggy
    state machine looping; in practice the pipeline needs at most
    ``1 + RETRY_CAP + 1`` cycles per module (audit → route → write →
    verify → review → [changes → write → verify → review] × RETRY_CAP →
    merge).

    Raises :class:`DispatcherUnavailable` unwrapped — the caller (pipeline
    run-loop) uses it as the signal to stop the whole batch rather than
    crashing one module at a time.
    """
    recover_in_progress(slug)
    last_stage: str | None = None
    for _ in range(max_cycles):
        st = state.load_state(slug)
        if st is None:
            raise StageError(f"state missing for {slug}")
        stage = st["stage"]
        if stage in state.TERMINAL_STAGES:
            return stage
        fn = _STAGE_FN.get(stage)
        if fn is None:
            # In-progress states should have been reconciled above. If
            # we still see one, something is wrong — fail rather than spin.
            raise StageError(f"no stage function for {stage!r} (slug={slug!r})")
        fn(slug)
        st_after = state.load_state(slug)
        new_stage = st_after["stage"] if st_after else stage
        if new_stage == last_stage == stage:
            # No progress — give up to avoid an infinite loop.
            return stage
        last_stage = stage
    return state.load_state(slug)["stage"] if state.load_state(slug) else "FAILED"  # type: ignore[index]
