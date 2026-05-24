"""Regression tests for build_quality_scores citation detection."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _load_local_api():
    module_path = Path(__file__).resolve().parents[1] / "local_api.py"
    spec = importlib.util.spec_from_file_location("local_api_quality", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


local_api = _load_local_api()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _module_with_sources(rel_path: str, title: str, sources_lines: list[str]) -> None:
    body = "\n".join(
        [
            "---",
            f'title: "{title}"',
            "---",
            "",
            "## Overview",
            "",
            *[f"Line {i}" for i in range(120)],
            "",
            "## Quick Quiz",
            "",
            "- Question",
            "",
            "## Hands-On",
            "",
            "1. Do thing",
            "",
            "## Sources",
            "",
            *sources_lines,
        ]
    )
    _write(Path(rel_path), body + "\n")


@pytest.fixture
def quality_repo(tmp_path: Path) -> Path:
    """Minimal docs tree root for build_quality_scores."""
    return tmp_path


def test_build_quality_scores_accepts_common_citation_formats(quality_repo: Path) -> None:
    """Issue #1489: bare-URL regex must match angle autolinks and labeled bullets.

    The scorer bounds detection to the ## Sources block; any https?:// URL
    there counts as a citation. All three formats must score above the 1.5
    no-citation cap (have_citations true).
    """
    docs = quality_repo / "src" / "content" / "docs" / "ai" / "open-models"
    _module_with_sources(
        str(docs / "module-1.1-bare-url.md"),
        "Bare URL Sources",
        ["- https://example.com"],
    )
    _module_with_sources(
        str(docs / "module-1.2-angle-url.md"),
        "Angle URL Sources",
        ["- <https://example.com>"],
    )
    _module_with_sources(
        str(docs / "module-1.3-labeled-url.md"),
        "Labeled URL Sources",
        ["- Label: https://example.com"],
    )

    with local_api._QUALITY_AUDIT_CACHE_LOCK:
        local_api._QUALITY_AUDIT_CACHE.clear()

    quality = local_api.build_quality_scores(quality_repo)
    by_path = {entry["path"]: entry for entry in quality["modules"]}

    for path in (
        "ai/open-models/module-1.1-bare-url.md",
        "ai/open-models/module-1.2-angle-url.md",
        "ai/open-models/module-1.3-labeled-url.md",
    ):
        module = by_path[path]
        assert module["score"] > 1.5, path
        assert not module["primary_issue"].startswith("no citations"), path
