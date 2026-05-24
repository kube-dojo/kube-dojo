"""Regression tests for build_quality_scores heuristics (citations, diagrams)."""

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


def _clear_quality_cache() -> None:
    with local_api._QUALITY_AUDIT_CACHE_LOCK:
        local_api._QUALITY_AUDIT_CACHE.clear()


def _module_with_diagram(rel_path: str, title: str, diagram_block: str) -> None:
    body = "\n".join(
        [
            "---",
            f'title: "{title}"',
            "---",
            "",
            "## Overview",
            "",
            diagram_block,
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
            "- https://example.com",
        ]
    )
    _write(Path(rel_path), body + "\n")


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

    _clear_quality_cache()

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


def test_build_quality_scores_detects_diagram_formats(quality_repo: Path) -> None:
    """Issue #1503: has_diagram must recognize Mermaid, details, and ASCII box art.

    ASCII diagrams need at least five lines with Unicode box-drawing characters
    (U+2500-U+257F). Fewer lines are incidental decoration and must not count.
    """
    docs = quality_repo / "src" / "content" / "docs" / "ai" / "diagrams"
    _module_with_diagram(
        str(docs / "module-1.1-mermaid.md"),
        "Mermaid Diagram",
        "```mermaid\nflowchart LR\n  A --> B\n```",
    )
    _module_with_diagram(
        str(docs / "module-1.2-details.md"),
        "Details Diagram",
        "<details>\n<summary>Architecture</summary>\n<pre>svc</pre>\n</details>",
    )
    ascii_five = "\n".join(
        [
            "┌─────────┐     ┌─────────┐",
            "│ Source  │────▶│  Sink   │",
            "└─────────┘     └─────────┘",
            "       │               │",
            "       └───────┬───────┘",
        ]
    )
    _module_with_diagram(
        str(docs / "module-1.3-ascii-five.md"),
        "ASCII Diagram",
        ascii_five,
    )
    ascii_three = "\n".join(
        [
            "┌─────┐",
            "│ one │",
            "└─────┘",
            "plain text line",
            "another plain line",
        ]
    )
    _module_with_diagram(
        str(docs / "module-1.4-ascii-few.md"),
        "ASCII Decoration",
        ascii_three,
    )
    _module_with_diagram(
        str(docs / "module-1.5-none.md"),
        "No Diagram",
        "Just prose about pipelines with no visual.",
    )

    _clear_quality_cache()
    quality = local_api.build_quality_scores(quality_repo)
    by_path = {entry["path"]: entry for entry in quality["modules"]}

    for path in (
        "ai/diagrams/module-1.1-mermaid.md",
        "ai/diagrams/module-1.2-details.md",
        "ai/diagrams/module-1.3-ascii-five.md",
    ):
        module = by_path[path]
        assert "no diagram" not in module["primary_issue"], path
        assert module["score"] == pytest.approx(4.3), path

    for path in (
        "ai/diagrams/module-1.4-ascii-few.md",
        "ai/diagrams/module-1.5-none.md",
    ):
        module = by_path[path]
        assert "no diagram" in module["primary_issue"], path
        assert module["score"] == pytest.approx(3.6), path
