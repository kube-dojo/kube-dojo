#!/usr/bin/env python3
"""Stage 1 gap identification for pipeline v4.

Fetches ``/api/quality/scores`` and turns the scorer's heuristic output
into a per-module gap list that downstream expansion code can consume
without re-implementing score interpretation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

QUALITY_SCORES_URL = "http://127.0.0.1:8768/api/quality/scores"
_KNOWN_GAP_MAP = {
    "thin": "thin",
    "no quiz": "no_quiz",
    "no citations": "no_citations",
    "no mistakes": "no_mistakes",
    "no exercise": "no_exercise",
    "no diagram": "no_diagram",
    "no outcomes": "no_outcomes",
}
_BALANCED_ISSUES = {"", "balanced"}


class QualityScoresError(RuntimeError):
    """Raised when the live quality-score endpoint cannot be read."""


def _iter_quality_score_entries(payload: object) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []

    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    modules = payload.get("modules")
    if isinstance(modules, list):
        for entry in modules:
            if not isinstance(entry, dict):
                continue
            path = entry.get("path")
            module = entry.get("module")
            key = path if isinstance(path, str) else module if isinstance(module, str) else None
            if key is None or key in seen:
                continue
            seen.add(key)
            entries.append(entry)

    for key, value in payload.items():
        if key == "modules" or not isinstance(value, list):
            continue
        for entry in value:
            if not isinstance(entry, dict):
                continue
            path = entry.get("path")
            module = entry.get("module")
            dedupe_key = path if isinstance(path, str) else module if isinstance(module, str) else None
            if dedupe_key is None or dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            entries.append(entry)
    return entries


def _normalize_gap_token(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized


def parse_primary_issue(primary_issue: str | None) -> list[str]:
    """Parse scorer ``primary_issue`` text into normalized gap ids."""
    if primary_issue is None:
        return []

    stripped = primary_issue.strip()
    if stripped.lower() in _BALANCED_ISSUES:
        return []

    gaps: list[str] = []
    for raw_part in stripped.split(","):
        part = raw_part.strip()
        if not part:
            continue
        mapped = _KNOWN_GAP_MAP.get(part.lower())
        gaps.append(mapped if mapped is not None else _normalize_gap_token(part))
    return gaps


def target_loc_for_path(path: str) -> int:
    """Return the curriculum target line count for a module path."""
    return 250 if path.startswith("k8s/kcna/") else 600


def _module_key_from_path(path: str) -> str:
    return path[:-3] if path.endswith(".md") else path


def _normalize_severity(raw_severity: object, score: float) -> str:
    if isinstance(raw_severity, str):
        lowered = raw_severity.strip().lower()
        if lowered in {"critical", "poor", "good", "excellent"}:
            return lowered
        if lowered == "needs_work":
            return "poor"

    if score < 2.0:
        return "critical"
    if score < 3.5:
        return "poor"
    if score < 4.5:
        return "good"
    return "excellent"


def _fetch_quality_scores(timeout_s: float = 5.0) -> object:
    try:
        with urlopen(QUALITY_SCORES_URL, timeout=timeout_s) as response:
            return json.load(response)
    except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise QualityScoresError(f"could not load {QUALITY_SCORES_URL}: {exc}") from exc


def fetch_gap_list(min_score: float | None = None, max_score: float | None = None) -> list[dict[str, Any]]:
    """Fetch ``/api/quality/scores`` and parse it into a structured gap list."""
    payload = _fetch_quality_scores()
    gap_list: list[dict[str, Any]] = []
    for entry in _iter_quality_score_entries(payload):
        path = entry.get("path")
        if not isinstance(path, str) or not path:
            continue

        raw_score = entry.get("score")
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            continue

        if min_score is not None and score < min_score:
            continue
        if max_score is not None and score > max_score:
            continue

        primary_issue = entry.get("primary_issue")
        primary_issue_text = primary_issue.strip() if isinstance(primary_issue, str) else ""
        module = entry.get("module")
        gap_list.append(
            {
                "module_key": _module_key_from_path(path),
                "path": path,
                "module": module if isinstance(module, str) and module else path,
                "score": score,
                "severity": _normalize_severity(entry.get("severity"), score),
                "primary_issue": primary_issue_text,
                "gaps": parse_primary_issue(primary_issue_text),
                "target_loc": target_loc_for_path(path),
            }
        )

    gap_list.sort(key=lambda item: (item["score"], item["module_key"]))
    return gap_list


def gaps_for_module(module_key: str) -> dict[str, Any] | None:
    """Convenience lookup for a single module key."""
    normalized_key = module_key[:-3] if module_key.endswith(".md") else module_key
    for item in fetch_gap_list():
        if item["module_key"] == normalized_key:
            return item
    return None


def _filter_by_gaps(items: list[dict[str, Any]], required_gaps: list[str]) -> list[dict[str, Any]]:
    if not required_gaps:
        return items
    required = {_normalize_gap_token(gap) for gap in required_gaps}
    return [item for item in items if required.issubset(set(item["gaps"]))]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--all", action="store_true", help="Dump every module as JSONL.")
    mode.add_argument("--critical", action="store_true", help="Dump modules with score < 2.0.")
    mode.add_argument("--module", help="Dump one module by module key.")
    parser.add_argument(
        "--has-gap",
        action="append",
        default=[],
        help="Require a normalized gap id; repeat for AND semantics.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.module:
            item = gaps_for_module(args.module)
            if item is None:
                print(f"module not found in /api/quality/scores: {args.module}", file=sys.stderr)
                return 1
            items = _filter_by_gaps([item], args.has_gap)
        else:
            items = fetch_gap_list()
            if args.critical:
                items = [item for item in items if item["score"] < 2.0]
            items = _filter_by_gaps(items, args.has_gap)
    except QualityScoresError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for item in items:
        print(json.dumps(item, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
