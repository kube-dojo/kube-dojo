#!/usr/bin/env python3
"""Benchmark agent cold-start orientation cost.

Measures how many tokens and milliseconds a fresh agent would burn to
orient itself in the repo. Compares two paths:

1. **Baseline** — what agents do today: ``cat CLAUDE.md`` + ``cat STATUS.md``
   + ``git log -20`` + ``ls`` of top-level dirs.
2. **API path** — a single call to ``/api/briefing/session`` (optionally
   ``?compact=1``) followed by at most one targeted drill-down.

Token counting uses ``tiktoken`` (``cl100k_base``) when installed; otherwise
falls back to a 4-characters-per-token approximation — an underestimate for
markdown but consistent across runs.

Usage::

    python scripts/bench_orientation.py [--repo-root PATH]

Prints a small table and exits 0. Intended to be run in CI to guard against
regressions in cold-start cost.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def _try_tiktoken():
    try:
        import tiktoken  # type: ignore
    except ImportError:
        return None
    try:
        return tiktoken.get_encoding("cl100k_base")
    except Exception:  # noqa: BLE001
        return None


_TOKENIZER = _try_tiktoken()


def count_tokens(text: str) -> int:
    if _TOKENIZER is not None:
        return len(_TOKENIZER.encode(text))
    # Rough fallback: ~4 chars per token for English prose. Underestimates
    # markdown/code; fine for regression tracking.
    return max(1, len(text) // 4)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def baseline_orientation(repo_root: Path) -> dict:
    """Approximate the tokens a typical agent reads to orient today."""
    parts: dict[str, str] = {
        "CLAUDE.md": _read(repo_root / "CLAUDE.md"),
        "STATUS.md": _read(repo_root / "STATUS.md"),
    }
    try:
        git_log = subprocess.run(
            ["git", "log", "-n20", "--oneline"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        git_log = ""
    parts["git log -20"] = git_log
    try:
        git_status = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        git_status = ""
    parts["git status"] = git_status
    try:
        ls = subprocess.run(
            ["ls", str(repo_root)],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        ls = ""
    parts["ls repo"] = ls

    per_part = {name: count_tokens(text) for name, text in parts.items()}
    return {
        "mode": "baseline",
        "tokens": sum(per_part.values()),
        "per_source": per_part,
        "byte_total": sum(len(v) for v in parts.values()),
    }


def api_orientation(repo_root: Path, *, compact: bool = False) -> dict:
    """Measure tokens returned by the briefing endpoint, wall-time included."""
    sys.path.insert(0, str(repo_root / "scripts"))
    import local_api  # noqa: PLC0415

    t0 = time.time()
    suffix = "?compact=1" if compact else ""
    code, body, _ct, etag = local_api.serve_request(
        repo_root, "/api/briefing/session" + suffix
    )
    dur_ms = (time.time() - t0) * 1000.0
    text = body.decode("utf-8", errors="replace")
    return {
        "mode": "api" + ("+compact" if compact else ""),
        "status": code,
        "tokens": count_tokens(text),
        "byte_total": len(body),
        "build_ms": dur_ms,
        "etag": etag,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark agent cold-start orientation cost"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Path to the repo root (default: auto-detected)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit one JSON object per line instead of a table",
    )
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()

    results = [
        baseline_orientation(repo_root),
        api_orientation(repo_root, compact=False),
        api_orientation(repo_root, compact=True),
    ]

    if args.json:
        for r in results:
            print(json.dumps(r, sort_keys=True))
        return 0

    print(f"Tokenizer: {'tiktoken cl100k_base' if _TOKENIZER else 'fallback (~4c/tok)'}")
    print(f"Repo root: {repo_root}")
    print()
    print(f"{'mode':<18}  {'tokens':>8}  {'bytes':>8}  {'extra':<40}")
    print("-" * 80)
    for r in results:
        extra = ""
        if r["mode"] == "baseline":
            extra = ", ".join(f"{k}:{v}" for k, v in r["per_source"].items())
        else:
            extra = f"build={r.get('build_ms', 0):.1f}ms"
        print(f"{r['mode']:<18}  {r['tokens']:>8}  {r['byte_total']:>8}  {extra}")

    baseline = results[0]["tokens"]
    api_full = results[1]["tokens"]
    api_compact = results[2]["tokens"]
    print()
    print(f"Saving vs baseline: full briefing = {baseline - api_full:+d} tokens"
          f" ({(1 - api_full / baseline) * 100:.0f}% reduction)")
    print(f"Saving vs baseline: compact      = {baseline - api_compact:+d} tokens"
          f" ({(1 - api_compact / baseline) * 100:.0f}% reduction)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
