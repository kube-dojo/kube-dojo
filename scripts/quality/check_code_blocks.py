#!/usr/bin/env python3
"""Syntax-check every fenced ```python``` block in module markdown files.

Phase 0 of the ML curriculum expansion (issue #677) ships hard rails on
code correctness. This script is one of two: it extracts every fenced
``python`` code block from a markdown file and runs ``ast.parse`` on
each. Fails on ``SyntaxError``.

With ``--imports-only`` the script additionally tries to import every
top-level module that the block imports. Blocks containing the sentinel
``# CODE-CHECK: skip`` are ignored.

The script is intentionally stdlib-only and safe to run in CI.

Usage::

    .venv/bin/python scripts/quality/check_code_blocks.py path/to/module.md
    .venv/bin/python scripts/quality/check_code_blocks.py --imports-only file.md
    .venv/bin/python scripts/quality/check_code_blocks.py --json file.md
"""
from __future__ import annotations

import argparse
import ast
import importlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

CODE_FENCE_RE = re.compile(
    r"```python\s*\n(.*?)```",
    flags=re.DOTALL,
)
SKIP_SENTINEL = "# CODE-CHECK: skip"


@dataclass
class BlockCheck:
    file: str
    block_index: int
    line_start: int
    ok: bool
    error: str | None
    failed_imports: list[str]


def extract_blocks(text: str) -> list[tuple[int, str]]:
    """Return list of (line_number, block_body) for every ```python block."""
    out: list[tuple[int, str]] = []
    # Walk match by match so we can recover line numbers.
    for m in CODE_FENCE_RE.finditer(text):
        body = m.group(1)
        line_no = text.count("\n", 0, m.start()) + 1
        out.append((line_no, body))
    return out


def check_block_syntax(body: str) -> str | None:
    """Return error message on syntax failure, None on success."""
    try:
        ast.parse(body)
    except SyntaxError as exc:
        return f"SyntaxError: {exc.msg} at block-line {exc.lineno}"
    return None


def extract_top_level_imports(body: str) -> list[str]:
    """Return the set of top-level module names this block imports.

    Only top-level packages are returned (``sklearn`` rather than
    ``sklearn.linear_model``) — that is sufficient to verify the block
    references real packages without spinning up the full sub-tree.
    """
    try:
        tree = ast.parse(body)
    except SyntaxError:
        return []
    seen: dict[str, None] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                seen.setdefault(alias.name.split(".")[0], None)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                seen.setdefault(node.module.split(".")[0], None)
    return list(seen)


def try_imports(modules: list[str]) -> list[str]:
    """Return the names that failed to import."""
    failed: list[str] = []
    for name in modules:
        try:
            importlib.import_module(name)
        except Exception:  # noqa: BLE001 — we report whatever broke
            failed.append(name)
    return failed


def check_file(path: Path, imports_only: bool) -> list[BlockCheck]:
    text = path.read_text(encoding="utf-8")
    blocks = extract_blocks(text)
    out: list[BlockCheck] = []
    for index, (line_no, body) in enumerate(blocks):
        if SKIP_SENTINEL in body:
            continue
        err = check_block_syntax(body)
        failed_imports: list[str] = []
        if err is None and imports_only:
            mods = extract_top_level_imports(body)
            failed_imports = try_imports(mods)
            if failed_imports:
                err = f"failed imports: {', '.join(failed_imports)}"
        out.append(
            BlockCheck(
                file=str(path),
                block_index=index,
                line_start=line_no,
                ok=err is None,
                error=err,
                failed_imports=failed_imports,
            )
        )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("paths", nargs="+", help="markdown files to check")
    parser.add_argument(
        "--imports-only",
        action="store_true",
        help=(
            "additionally try `import` for every top-level module the "
            "block imports; skip blocks containing the # CODE-CHECK: skip "
            "sentinel"
        ),
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="emit machine-readable JSON instead of a human report",
    )
    args = parser.parse_args(argv)

    all_results: list[BlockCheck] = []
    for p in args.paths:
        path = Path(p).resolve()
        if not path.exists():
            print(f"warning: {path} does not exist", file=sys.stderr)
            continue
        all_results.extend(check_file(path, args.imports_only))

    if args.json_output:
        json.dump([asdict(r) for r in all_results], sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        if not all_results:
            print("no python code blocks found")
        else:
            print(f"{'STATUS':<8} {'BLOCK':<7} {'LINE':<7} FILE")
            print("-" * 80)
            for r in all_results:
                tag = "OK" if r.ok else "FAIL"
                print(f"{tag:<8} {r.block_index:<7} {r.line_start:<7} {r.file}")
                if r.error:
                    print(f"        - {r.error}")

    failures = [r for r in all_results if not r.ok]
    if failures:
        print(
            f"\n{len(failures)} of {len(all_results)} block(s) failed.",
            file=sys.stderr,
        )
        return 1
    print(
        f"\nAll {len(all_results)} python block(s) parsed cleanly.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
