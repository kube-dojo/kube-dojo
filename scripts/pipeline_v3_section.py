#!/usr/bin/env python3
"""Run the v3 citation pipeline for every module in a section.

Usage:
    python scripts/pipeline_v3_section.py <section_path>
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from citation_backfill import REPO_ROOT, flat_section_name  # type: ignore  # noqa: E402
from pipeline_v3 import run_pipeline  # type: ignore  # noqa: E402
from section_source_discovery import (  # type: ignore  # noqa: E402
    discover_section_sources,
    list_section_modules,
    normalize_section_key,
)


def _write_log(log_path: Path, entry: dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_section_pipeline(
    section_path: str,
    *,
    batch_size: int = 5,
    max_batch_chars: int = 28_000,
    auto_apply: bool = True,
    modules_override: list[str] | None = None,
) -> dict:
    section_key = normalize_section_key(section_path)
    log_path = REPO_ROOT / ".pipeline" / "v3" / "batches" / f"{flat_section_name(section_key)}.log"

    stage0 = discover_section_sources(
        section_key,
        batch_size=batch_size,
        max_batch_chars=max_batch_chars,
    )
    _write_log(log_path, {"stage": "section_source_discovery", **stage0})
    if not stage0.get("ok"):
        return {
            "ok": False,
            "section": section_key,
            "pool": stage0,
            "log_path": str(log_path.relative_to(REPO_ROOT)),
        }

    # `modules_override` lets the caller restrict the per-module stage
    # to a specific subset (e.g. "only modules still missing citations")
    # while still rebuilding the pool from the whole section — pool
    # completeness is what keeps source reuse stable.
    if modules_override is not None:
        modules = list(modules_override)
    else:
        modules = [
            module_path.relative_to((REPO_ROOT / "src" / "content" / "docs")).with_suffix("").as_posix()
            for module_path in list_section_modules(section_key)
        ]
    statuses: dict[str, int] = {}
    results: list[dict] = []
    for index, module_key in enumerate(modules, start=1):
        t0 = time.time()
        try:
            record = run_pipeline(
                module_key,
                auto_apply=auto_apply,
                section_pool_ref=str(stage0["pool_path"]),
            )
        except Exception as exc:  # noqa: BLE001
            entry = {
                "i": index,
                "module_key": module_key,
                "status": "exception",
                "elapsed_s": round(time.time() - t0, 1),
                "error": f"{type(exc).__name__}: {exc}",
            }
            _write_log(log_path, entry)
            results.append(entry)
            statuses["exception"] = statuses.get("exception", 0) + 1
            continue

        status = str(record.get("status") or "unknown")
        statuses[status] = statuses.get(status, 0) + 1
        entry = {
            "i": index,
            "module_key": module_key,
            "status": status,
            "elapsed_s": round(time.time() - t0, 1),
            "run_record": record.get("_run_record_path"),
        }
        _write_log(log_path, entry)
        results.append(entry)

    summary = {
        "ok": True,
        "section": section_key,
        "pool_path": stage0["pool_path"],
        "module_count": len(modules),
        "statuses": statuses,
        "results": results,
        "log_path": str(log_path.relative_to(REPO_ROOT)),
    }
    _write_log(log_path, {"summary": {"statuses": statuses, "module_count": len(modules)}})
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run pipeline_v3 with section source pools")
    parser.add_argument("section_path", help="Section path under src/content/docs/")
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--max-batch-chars", type=int, default=28_000)
    parser.add_argument("--no-auto-apply", action="store_true")
    args = parser.parse_args(argv)

    result = run_section_pipeline(
        args.section_path,
        batch_size=args.batch_size,
        max_batch_chars=args.max_batch_chars,
        auto_apply=not args.no_auto_apply,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
