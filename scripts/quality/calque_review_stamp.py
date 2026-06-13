#!/usr/bin/env python3
"""Per-page calque review stamp stored in UK markdown frontmatter."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

_CALQUE_KEY_RE = re.compile(r"^calque_review:\s*$")
_CHILD_KV_RE = re.compile(r"^(\s*)(\w+):\s*(.*)$")


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _split_frontmatter(text: str) -> tuple[str | None, str]:
    if not text.startswith("---\n"):
        return None, text
    _, _, rest = text.partition("---\n")
    frontmatter, sep, body = rest.partition("\n---\n")
    if not sep:
        return None, text
    return frontmatter, body


def _join_frontmatter(frontmatter: str, body: str) -> str:
    fm = frontmatter
    if fm and not fm.endswith("\n"):
        fm += "\n"
    return f"---\n{fm}---\n{body}"


def _iter_frontmatter_lines(frontmatter: str) -> list[str]:
    if not frontmatter:
        return []
    return frontmatter.splitlines(keepends=True)


def _remove_calque_block_from_frontmatter(frontmatter: str) -> str:
    lines = _iter_frontmatter_lines(frontmatter)
    if not lines:
        return frontmatter

    result: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if _CALQUE_KEY_RE.match(line.rstrip("\r\n")):
            parent_indent = _indent_of(line)
            index += 1
            while index < len(lines):
                child = lines[index]
                if child.strip() == "":
                    index += 1
                    continue
                if _indent_of(child) <= parent_indent:
                    break
                index += 1
            continue
        result.append(line)
        index += 1
    return "".join(result)


def strip_calque_block(text: str) -> str:
    frontmatter, body = _split_frontmatter(text)
    if frontmatter is None:
        return text
    stripped = _remove_calque_block_from_frontmatter(frontmatter)
    return _join_frontmatter(stripped, body)


def compute_content_sha(text: str) -> str:
    return hashlib.sha256(strip_calque_block(text).encode("utf-8")).hexdigest()


def _parse_scalar(value: str) -> str | int:
    value = value.strip()
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        return value[1:-1]
    if value.startswith("'") and value.endswith("'") and len(value) >= 2:
        return value[1:-1]
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)
    return value


def _parse_calque_block(frontmatter: str) -> dict[str, str | int] | None:
    lines = frontmatter.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if _CALQUE_KEY_RE.match(line):
            start = index
            break
    if start is None:
        return None

    parent_indent = _indent_of(lines[start])
    data: dict[str, str | int] = {}
    index = start + 1
    while index < len(lines):
        line = lines[index]
        if line.strip() == "":
            index += 1
            continue
        indent = _indent_of(line)
        if indent <= parent_indent:
            break
        match = _CHILD_KV_RE.match(line)
        if match and _indent_of(match.group(1)) > parent_indent:
            key = match.group(2)
            data[key] = _parse_scalar(match.group(3))
        index += 1

    if not data:
        return None
    return data


def _calque_block_lines(
    *,
    reviewed_at: str,
    detector_version: str,
    status: str,
    flags_resolved: int,
    content_sha: str,
) -> list[str]:
    return [
        "calque_review:\n",
        f'  reviewed_at: "{reviewed_at}"\n',
        f'  detector_version: "{detector_version}"\n',
        f'  status: "{status}"\n',
        f"  flags_resolved: {flags_resolved}\n",
        f'  content_sha: "{content_sha}"\n',
    ]


def _insert_calque_block(frontmatter: str, block_lines: list[str]) -> str:
    cleaned = _remove_calque_block_from_frontmatter(frontmatter)
    if cleaned and not cleaned.endswith("\n"):
        cleaned += "\n"
    return cleaned + "".join(block_lines)


def stamp(
    path: Path,
    *,
    detector_version: str,
    flags_resolved: int,
    status: str = "reviewed",
) -> None:
    text = path.read_text(encoding="utf-8")
    content_sha = compute_content_sha(text)
    frontmatter, body = _split_frontmatter(text)
    if frontmatter is None:
        raise ValueError(f"{path}: missing YAML frontmatter")

    reviewed_at = datetime.date.today().isoformat()
    block_lines = _calque_block_lines(
        reviewed_at=reviewed_at,
        detector_version=detector_version,
        status=status,
        flags_resolved=flags_resolved,
        content_sha=content_sha,
    )
    updated_frontmatter = _insert_calque_block(frontmatter, block_lines)
    path.write_text(_join_frontmatter(updated_frontmatter, body), encoding="utf-8")


def read_status(path: Path) -> dict[str, str | int | bool] | None:
    text = path.read_text(encoding="utf-8")
    frontmatter, _ = _split_frontmatter(text)
    if frontmatter is None:
        return None

    parsed = _parse_calque_block(frontmatter)
    if parsed is None:
        return None

    stored_sha = str(parsed.get("content_sha", ""))
    current_sha = compute_content_sha(text)
    flags = parsed.get("flags_resolved", 0)
    return {
        "status": str(parsed.get("status", "")),
        "reviewed_at": str(parsed.get("reviewed_at", "")),
        "detector_version": str(parsed.get("detector_version", "")),
        "flags_resolved": int(flags) if isinstance(flags, int) else int(str(flags)),
        "stale": stored_sha != current_sha,
    }


def _cmd_stamp(args: argparse.Namespace) -> None:
    stamp(
        Path(args.file),
        detector_version=args.detector_version,
        flags_resolved=args.flags,
        status=args.status,
    )


def _cmd_status(args: argparse.Namespace) -> None:
    result = read_status(Path(args.file))
    print(result)


def main() -> int:
    parser = argparse.ArgumentParser(description="Calque review frontmatter stamp helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    stamp_parser = subparsers.add_parser("stamp", help="Write calque_review stamp to a UK page")
    stamp_parser.add_argument("file", help="UK markdown file path")
    stamp_parser.add_argument("--flags", type=int, required=True, help="Number of calque flags resolved")
    stamp_parser.add_argument(
        "--status",
        choices=("reviewed", "clean"),
        default="reviewed",
        help='Review outcome (default: "reviewed")',
    )
    stamp_parser.add_argument(
        "--detector-version",
        default="v1",
        help='Detector version label (default: "v1")',
    )
    stamp_parser.set_defaults(func=_cmd_stamp)

    status_parser = subparsers.add_parser("status", help="Read calque_review stamp from a UK page")
    status_parser.add_argument("file", help="UK markdown file path")
    status_parser.set_defaults(func=_cmd_status)

    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
