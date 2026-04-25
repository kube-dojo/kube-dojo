"""Quality pipeline v2 CLI orchestrator.

Subcommands:

* ``bootstrap`` — scan ``src/content/docs/`` (excluding ``uk/`` and
  ``index.md``), assign permanent ``module_index`` by sorted path, and
  create one state file per module. Idempotent.
* ``status`` — counts by stage, useful for health-check and briefing.
* ``audit`` — drive every ``UNAUDITED`` module to ``AUDITED``.
* ``route`` — drive every ``AUDITED`` module to ``WRITE_PENDING`` (rewrite
  or structural track) or ``CITATION_CLEANUP_ONLY`` (score ≥ 4.0 +
  complete structure). ``SKIPPED`` is reached later by
  :func:`stages.citation_verify_one` on the cleanup-only path when
  nothing needed removal.
* ``run`` — drive a queue of modules through the full pipeline until
  a terminal state. Processes worst-score-first; writer alternation is
  determined by each module's permanent index (not processing order).
* ``run-module`` — drive a single slug. Used by smoke tests.
* ``reset-stage`` — admin tool; moves a module back to an earlier stage
  so a fix can be re-attempted without a full state-file hand edit.

Return codes: 0 on success, 1 on any module failing (so CI and shell
scripts can detect issues), 3 when aborted by dispatcher unavailability.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from . import state, stages
from .dispatchers import DispatcherUnavailable
from .prompts import assert_required_docs_exist
from .worktree import primary_checkout_root


_REPO_ROOT = primary_checkout_root(Path(__file__).resolve().parents[2])
_CONTENT_ROOT = _REPO_ROOT / "src" / "content" / "docs"

WORKER_CAP = 3
"""Hard cap per project memory ``feedback_batch_worker_cap.md`` —
above 3, Gemini 429s and user's Mac lags."""


# ---- bootstrap --------------------------------------------------------


def iter_all_modules() -> list[Path]:
    """Every eligible English content module, sorted by path.

    Sorting is the basis for the permanent ``module_index`` — changing
    the sort order after bootstrap would silently re-assign every
    module's writer (even→Codex vs odd→Claude), so this must stay
    deterministic across runs.
    """
    out: list[Path] = []
    for p in sorted(_CONTENT_ROOT.rglob("*.md")):
        posix = p.as_posix()
        if "/uk/" in posix or p.name == "index.md":
            continue
        out.append(p)
    return out


def cmd_bootstrap(args: argparse.Namespace) -> int:
    """Create state files for every module that doesn't have one and
    migrate any pre-v2 state files that lack ``module_index``.

    Preserves existing state files — re-running bootstrap after adding
    new modules only creates new state, never overwrites. The
    ``module_index`` stays stable because it's re-derived from the
    sorted path list, and a new module appended at the end of the
    alphabetical list only grows the index space.

    Migration: v1 state files had no ``module_index`` field. v2 needs
    it for writer round-robin. Bootstrap fills it in for any existing
    state that's missing it — non-destructive, preserves the audit
    and history fields intact.
    """
    modules = iter_all_modules()
    state.STATE_DIR.mkdir(parents=True, exist_ok=True)
    created = migrated = 0
    for i, module_path in enumerate(modules):
        slug = state.slug_for(module_path)
        existing = state.load_state(slug)
        if existing is None:
            st = state.new_state(module_path, module_index=i)
            state.save_state(st)
            created += 1
            continue
        if existing.get("module_index") is None:
            existing["module_index"] = i
            state.save_state(existing)
            migrated += 1
    unchanged = len(modules) - created - migrated
    print(
        f"bootstrap: {created} new state(s); {migrated} v1→v2 migrated; "
        f"{unchanged} already complete; total {len(modules)}"
    )
    return 0


# ---- status -----------------------------------------------------------


def iter_states(slug_filter: Iterable[str] | None = None) -> list[dict[str, Any]]:
    all_slugs = state.iter_state_slugs()
    if slug_filter is not None:
        wanted = set(slug_filter)
        all_slugs = [s for s in all_slugs if s in wanted]
    out: list[dict[str, Any]] = []
    for slug in all_slugs:
        st = state.load_state(slug)
        if st is not None:
            out.append(st)
    return out


def cmd_status(args: argparse.Namespace) -> int:
    states = iter_states(args.only or None)
    counts: Counter[str] = Counter(st["stage"] for st in states)
    print(f"total: {len(states)}")
    for stage in state.STAGES:
        n = counts.get(stage, 0)
        if n:
            print(f"  {stage}: {n}")
    if args.verbose:
        failed = [st for st in states if st["stage"] == "FAILED"]
        for st in failed[:20]:
            print(f"FAILED  {st['slug']}: {st.get('failure_reason') or '(no reason)'}")
    return 0


# ---- audit / route batch stages ---------------------------------------


def _process_batch(
    eligible_stages: set[str],
    fn,
    *,
    limit: int | None,
    only: Iterable[str] | None,
) -> tuple[int, int]:
    slugs = [st["slug"] for st in iter_states(only) if st["stage"] in eligible_stages]
    if limit is not None:
        slugs = slugs[:limit]
    ok = fail = 0
    for slug in slugs:
        try:
            fn(slug)
            ok += 1
        except DispatcherUnavailable as exc:
            print(f"[abort] dispatcher unavailable — {exc}")
            return ok, fail
        except Exception as exc:  # pragma: no cover — unexpected failures logged
            print(f"[fail] {slug}: {exc}")
            fail += 1
    return ok, fail


def cmd_audit(args: argparse.Namespace) -> int:
    ok, fail = _process_batch({"UNAUDITED"}, stages.audit_one, limit=args.limit, only=args.only)
    print(f"audit: ok={ok} fail={fail}")
    return 0 if fail == 0 else 1


def cmd_route(args: argparse.Namespace) -> int:
    ok, fail = _process_batch({"AUDITED"}, stages.route_one, limit=args.limit, only=args.only)
    print(f"route: ok={ok} fail={fail}")
    return 0 if fail == 0 else 1


# ---- run (full pipeline per module, worst-first) ---------------------


def _order_worst_first(slugs: list[str]) -> list[str]:
    """Sort slugs by ascending audit teaching_score, tiebreak by module_index.

    Modules without a score (UNAUDITED / audit failed) are placed at the
    BEGINNING — they still need to be processed, and their eventual
    score is unknown until audited.
    """
    def key(slug: str) -> tuple[float, int]:
        st = state.load_state(slug)
        if st is None:
            return (0.0, 10**9)
        audit = st.get("audit") or {}
        score = stages._audit_score(audit) if audit else -1.0
        return (score, st.get("module_index", 10**9))
    return sorted(slugs, key=key)


def cmd_run(args: argparse.Namespace) -> int:
    """Drive modules through the full pipeline.

    Respects the strict ``--workers 1`` default per memory
    ``feedback_batch_worker_cap.md``. ``--workers > 3`` is clamped with
    a warning.
    """
    assert_required_docs_exist()

    if args.workers < 1:
        args.workers = 1
    if args.workers > WORKER_CAP:
        print(f"[warn] --workers clamped from {args.workers} to {WORKER_CAP}")
        args.workers = WORKER_CAP
    if args.workers > 1:
        print("[warn] multi-worker mode processes modules concurrently; git worktrees are per-slug so it's safe, but Gemini 429 risk rises.")

    # Identify queue: everything not in a terminal state.
    all_states = iter_states(args.only or None)
    pending = [
        st["slug"]
        for st in all_states
        if st["stage"] not in state.TERMINAL_STAGES
    ]
    pending = _order_worst_first(pending)
    if args.limit is not None:
        pending = pending[: args.limit]

    print(f"run: {len(pending)} module(s) in queue (workers={args.workers})")
    ok = fail = aborted = 0
    if args.workers == 1:
        for slug in pending:
            rc = _run_one_with_abort(slug)
            if rc == "abort":
                aborted = 1
                break
            if rc == "ok":
                ok += 1
            else:
                fail += 1
    else:
        import concurrent.futures as cf

        with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(_run_one_with_abort, slug): slug for slug in pending}
            for fut in cf.as_completed(futures):
                rc = fut.result()
                if rc == "abort":
                    aborted = 1
                elif rc == "ok":
                    ok += 1
                else:
                    fail += 1

    print(f"run: ok={ok} fail={fail} aborted={aborted}")
    if aborted:
        return 3
    return 0 if fail == 0 else 1


def _run_one_with_abort(slug: str) -> str:
    """Return ``"ok"``, ``"fail"``, or ``"abort"``. Never raises."""
    try:
        terminal = stages.run_module(slug)
    except DispatcherUnavailable as exc:
        print(f"[abort] dispatcher unavailable at {slug}: {exc}")
        return "abort"
    except Exception as exc:
        print(f"[fail] {slug}: {exc}")
        return "fail"
    if terminal == "FAILED":
        print(f"[fail] {slug}: FAILED")
        return "fail"
    return "ok"


def cmd_run_module(args: argparse.Namespace) -> int:
    """Single-module smoke path — the primary vehicle for Phase D's
    ``k8s-capa-module-1.2-argo-events`` end-to-end test."""
    assert_required_docs_exist()
    slug = args.slug
    st = state.load_state(slug)
    if st is None:
        print(f"no state for slug {slug!r}; run bootstrap first")
        return 1
    try:
        terminal = stages.run_module(slug)
    except DispatcherUnavailable as exc:
        print(f"aborted: dispatcher unavailable — {exc}")
        return 3
    print(f"{slug}: {terminal}")
    return 0 if terminal not in ("FAILED",) else 1


# ---- backfill-pending (close the v2 → citation_backfill seam) ---------


_CITATION_BACKFILL_SCRIPT = _REPO_ROOT / "scripts" / "citation_backfill.py"
_VENV_PYTHON = str(_REPO_ROOT / ".venv" / "bin" / "python")


def _module_key_from_path(module_path: str) -> str:
    """Convert state.module_path to citation_backfill's module_key.

    e.g. ``src/content/docs/k8s/capa/module-1.2-argo-events.md`` →
    ``k8s/capa/module-1.2-argo-events``.
    """
    rel = module_path
    for prefix in ("src/content/docs/",):
        if rel.startswith(prefix):
            rel = rel[len(prefix):]
            break
    return rel.removesuffix(".md")


def _git(repo: Path, *args: str, check: bool = True) -> tuple[int, str, str]:
    """Run ``git`` in ``repo`` and return ``(returncode, stdout, stderr)``."""
    import subprocess
    proc = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed (rc={proc.returncode}): {proc.stderr.strip()}"
        )
    return proc.returncode, proc.stdout, proc.stderr


def _run_citation_subcommand(module_key: str, sub: str, *, agent: str | None = None) -> dict[str, Any]:
    """Subprocess-invoke ``scripts/citation_backfill.py {research,inject}``.

    Returns a dict shaped ``{"ok": bool, "stdout": str, "stderr": str,
    "returncode": int}``. The script's own JSON output (when it has any)
    is forwarded as-is in ``stdout`` so callers can re-parse if they need
    structured fields.
    """
    import subprocess
    cmd = [_VENV_PYTHON, str(_CITATION_BACKFILL_SCRIPT), sub]
    if agent:
        cmd += ["--agent", agent]
    cmd.append(module_key)
    proc = subprocess.run(
        cmd, cwd=str(_REPO_ROOT), capture_output=True, text=True, check=False,
        timeout=900,
    )
    return {
        "ok": proc.returncode == 0,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "returncode": proc.returncode,
    }


def _backfill_one(st: dict[str, Any], *, agent: str | None) -> dict[str, Any]:
    """Run research + inject for one COMMITTED module. Commit on success.

    Returns the outcome dict to be persisted to ``state.backfill``. On
    success, the working module file may have been edited and a new
    commit added on ``main``; on failure, leaves the worktree clean
    (``git restore`` rolls back any partial inject write).
    """
    slug = st["slug"]
    module_key = _module_key_from_path(st["module_path"])
    repo = _REPO_ROOT

    # Refuse to operate on a dirty primary — any pending edits must be
    # resolved before we mutate the same files. The pipeline never leaves
    # primary dirty between stages, but a human might.
    rc, stdout, _ = _git(repo, "status", "--porcelain", check=False)
    if rc != 0 or stdout.strip():
        return {
            "done": False, "ok": False,
            "error": "primary checkout has uncommitted changes — refusing to backfill",
            "module_key": module_key,
        }

    research = _run_citation_subcommand(module_key, "research", agent=agent)
    if not research["ok"]:
        return {
            "done": False, "ok": False, "stage_failed": "research",
            "error": (research["stderr"] or research["stdout"])[-500:],
            "module_key": module_key,
        }

    inject = _run_citation_subcommand(module_key, "inject", agent=agent)
    if not inject["ok"]:
        # Best-effort: discard any partial write so primary stays clean.
        _git(repo, "restore", st["module_path"], check=False)
        return {
            "done": False, "ok": False, "stage_failed": "inject",
            "error": (inject["stderr"] or inject["stdout"])[-500:],
            "module_key": module_key,
        }

    # The research step writes (or refreshes) the seed JSON; both
    # artifacts (module + seed) must land in the same commit so the
    # provenance is traceable in git history. ``git status --porcelain``
    # without a path lists every file we may need to stage.
    seed_rel = f"docs/citation-seeds/{module_key.replace('/', '-')}.json"
    rc, status_all, _ = _git(repo, "status", "--porcelain", check=False)
    if rc != 0:
        return {
            "done": False, "ok": False, "stage_failed": "git_status",
            "error": "git status failed after inject",
            "module_key": module_key,
        }
    changed_paths = {
        line[3:].strip() for line in status_all.splitlines()
        if line.strip()
    }
    backfill_paths = [p for p in (st["module_path"], seed_rel) if p in changed_paths]
    foreign_paths = changed_paths - set(backfill_paths)
    if foreign_paths:
        # Some other process touched the working tree mid-backfill —
        # refuse to drag those files into our commit. Roll back what
        # citation_backfill wrote so primary stays clean for retry.
        for p in backfill_paths:
            _git(repo, "restore", p, check=False)
        return {
            "done": False, "ok": False, "stage_failed": "concurrent_edit",
            "error": f"unexpected working-tree changes outside backfill scope: {sorted(foreign_paths)[:5]}",
            "module_key": module_key,
        }
    if not backfill_paths:
        # Inject succeeded with no diff (e.g. seed had no actionable claims).
        # Mark as done — backfill considered complete for this module.
        return {
            "done": True, "ok": True, "no_op": True,
            "module_key": module_key,
        }

    _git(repo, "add", *backfill_paths)
    msg = (
        f"quality(backfill): citation backfill {slug}\n\n"
        f"Sources injected via scripts/citation_backfill.py for module_key "
        f"`{module_key}`. Refs #375."
    )
    rc, _, stderr = _git(repo, "commit", "-m", msg, check=False)
    if rc != 0:
        for p in backfill_paths:
            _git(repo, "restore", "--staged", p, check=False)
            _git(repo, "restore", p, check=False)
        return {
            "done": False, "ok": False, "stage_failed": "git_commit",
            "error": stderr.strip()[-500:], "module_key": module_key,
        }

    _, sha, _ = _git(repo, "rev-parse", "HEAD")
    return {
        "done": True, "ok": True, "sha": sha.strip(),
        "module_key": module_key,
    }


def cmd_backfill_pending(args: argparse.Namespace) -> int:
    """Run citation_backfill (research + inject) on every COMMITTED module
    that hasn't been backfilled yet. Closes the v2 → citation_backfill
    seam in one command.

    Two-pipeline note: v2 ships modules without ``## Sources`` because
    citation insertion is owned by ``scripts/citation_backfill.py``.
    Without this command, an operator would have to manually loop every
    COMMITTED slug through ``research`` + ``inject``. After this command
    each module's state file gains a ``backfill`` field with ``done``,
    ``ok``, and either a commit ``sha`` or an ``error`` string for retry.
    """
    if not _CITATION_BACKFILL_SCRIPT.exists():
        print(f"missing dependency: {_CITATION_BACKFILL_SCRIPT}")
        return 1

    candidates = iter_states(args.only or None)
    pending = [
        st for st in candidates
        if st["stage"] == "COMMITTED" and not (st.get("backfill") or {}).get("done")
    ]
    if args.limit is not None:
        pending = pending[: args.limit]

    print(
        f"backfill-pending: {len(pending)} of {len(candidates)} module(s) "
        f"need backfill (agent={args.agent or 'default'})"
    )
    ok = fail = noop = 0
    for st in pending:
        slug = st["slug"]
        outcome = _backfill_one(st, agent=args.agent)
        with state.state_lease(slug) as lease:
            current = lease.load()
            if current is None:
                continue
            current["backfill"] = outcome
            current.setdefault("history", []).append({
                "at": state.now_iso(),
                "stage": current["stage"],
                "note": (
                    "backfill done" if outcome.get("ok") and not outcome.get("no_op")
                    else "backfill no-op" if outcome.get("no_op")
                    else f"backfill failed: {outcome.get('stage_failed') or 'unknown'}"
                ),
            })
            lease.save(current)
        if outcome.get("ok"):
            if outcome.get("no_op"):
                noop += 1
                print(f"[no-op] {slug}: nothing to inject")
            else:
                ok += 1
                print(f"[ok]    {slug}: {outcome.get('sha', '')[:8]}")
        else:
            fail += 1
            print(f"[fail]  {slug} at {outcome.get('stage_failed')}: {outcome.get('error', '')[:200]}")

    print(f"backfill-pending: ok={ok} no-op={noop} fail={fail}")
    return 0 if fail == 0 else 1


# ---- reset-stage (admin) ---------------------------------------------


def cmd_reset_stage(args: argparse.Namespace) -> int:
    """Force a module's state to an earlier stage — without the CAS check.

    Used to unstick modules whose state diverged from the on-disk
    reality (e.g. the worktree was manually removed). Prefer
    :func:`stages.recover_in_progress` first.
    """
    slug = args.slug
    to_stage = args.to_stage
    if to_stage not in state.STAGES:
        print(f"unknown stage {to_stage!r}; expected one of {list(state.STAGES)}")
        return 2
    with state.state_lease(slug) as lease:
        st = lease.load()
        if st is None:
            print(f"no state for {slug}")
            return 1
        old = st["stage"]
        st["stage"] = to_stage
        st.setdefault("history", []).append(
            {"at": state.now_iso(), "stage": to_stage, "note": f"admin reset from {old}"}
        )
        lease.save(st)
        print(f"{slug}: {old} → {to_stage}")
    return 0


# ---- main -------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="quality-pipeline", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_bootstrap = sub.add_parser("bootstrap", help="create state files for every module")
    p_bootstrap.set_defaults(func=cmd_bootstrap)

    p_status = sub.add_parser("status", help="stage counts + FAILED summary")
    p_status.add_argument("--only", nargs="*", help="filter by slug(s)")
    p_status.add_argument("-v", "--verbose", action="store_true", help="list FAILED modules")
    p_status.set_defaults(func=cmd_status)

    p_audit = sub.add_parser("audit", help="drive UNAUDITED → AUDITED")
    p_audit.add_argument("--limit", type=int, default=None)
    p_audit.add_argument("--only", nargs="*")
    p_audit.set_defaults(func=cmd_audit)

    p_route = sub.add_parser("route", help="drive AUDITED → WRITE_PENDING or CITATION_CLEANUP_ONLY")
    p_route.add_argument("--limit", type=int, default=None)
    p_route.add_argument("--only", nargs="*")
    p_route.set_defaults(func=cmd_route)

    p_run = sub.add_parser("run", help="drive modules through the full pipeline, worst-first")
    p_run.add_argument("--workers", type=int, default=1)
    p_run.add_argument("--limit", type=int, default=None)
    p_run.add_argument("--only", nargs="*")
    p_run.set_defaults(func=cmd_run)

    p_one = sub.add_parser("run-module", help="drive a single slug end-to-end (smoke)")
    p_one.add_argument("slug")
    p_one.set_defaults(func=cmd_run_module)

    p_reset = sub.add_parser("reset-stage", help="admin: force a module to a prior stage")
    p_reset.add_argument("slug")
    p_reset.add_argument("to_stage")
    p_reset.set_defaults(func=cmd_reset_stage)

    p_backfill = sub.add_parser(
        "backfill-pending",
        help="run citation_backfill (research+inject) on every COMMITTED module not yet backfilled",
    )
    p_backfill.add_argument("--limit", type=int, default=None)
    p_backfill.add_argument("--only", nargs="*", help="filter by slug(s)")
    p_backfill.add_argument(
        "--agent",
        choices=("codex", "gemini"),
        default=None,
        help="override the agent used by citation_backfill",
    )
    p_backfill.set_defaults(func=cmd_backfill_pending)

    ns = parser.parse_args(argv)
    return ns.func(ns)


if __name__ == "__main__":
    sys.exit(main())
