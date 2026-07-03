"""Regression tests for scripts/normalize_complexity_markers.py.

Covers the deterministic tier-token transform, the false-positive guards (prose
"complexity"/"advanced" must be left alone), frontmatter-key removal, container
preservation, and idempotency.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _load():
    module_path = Path(__file__).resolve().parents[1] / "normalize_complexity_markers.py"
    spec = importlib.util.spec_from_file_location("normalize_complexity_markers", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ncm = _load()


@pytest.mark.parametrize(
    "line,expected",
    [
        # already-canonical -> unchanged
        ("> **Complexity**: `[QUICK]` - Absolute beginner\n", "> **Complexity**: `[QUICK]` - Absolute beginner\n"),
        ("## Complexity: `[COMPLEX]`\n", "## Complexity: `[COMPLEX]`\n"),
        ("| **Complexity** | `[QUICK]` - Essential orientation |\n", "| **Complexity** | `[QUICK]` - Essential orientation |\n"),
        # bare bracket -> backticked (container preserved: heading stays a heading)
        ("## Complexity: [MEDIUM]\n", "## Complexity: `[MEDIUM]`\n"),
        ("> **Complexity**: [MEDIUM]\n", "> **Complexity**: `[MEDIUM]`\n"),
        ("> **Complexity:** [MEDIUM]\n", "> **Complexity:** `[MEDIUM]`\n"),
        # bareword sanctioned -> backticked bracket
        ("> **Complexity**: MEDIUM\n", "> **Complexity**: `[MEDIUM]`\n"),
        ("> **Complexity**: Advanced\n", "> **Complexity**: `[ADVANCED]`\n"),
        ("> **Complexity**: Complex\n", "> **Complexity**: `[COMPLEX]`\n"),
        # synonyms
        ("> **Complexity**: Intermediate\n", "> **Complexity**: `[MEDIUM]`\n"),
        ("**Complexity**: Intermediate<br>\n", "**Complexity**: `[MEDIUM]`<br>\n"),
        ("> **Complexity**: [BEGINNER]\n", "> **Complexity**: `[QUICK]`\n"),
        ("> **Complexity**: `[INTERMEDIATE]`\n", "> **Complexity**: `[MEDIUM]`\n"),
        # ranges map to the ceiling tier (spaced AND hyphenated, listed and unlisted)
        ("**Complexity**: Intermediate to Advanced  \n", "**Complexity**: `[ADVANCED]`  \n"),
        ("> **Complexity:** Beginner to intermediate  \n", "> **Complexity:** `[MEDIUM]`  \n"),
        # regression #2217-R1: hyphenated range must not partial-replace to `[MEDIUM]`-to-Advanced
        (
            "> Track: AI/ML Engineering | Complexity: Intermediate-to-Advanced | Time: 100-120 minutes\n",
            "> Track: AI/ML Engineering | Complexity: `[ADVANCED]` | Time: 100-120 minutes\n",
        ),
        ("> **Complexity**: Beginner-to-Advanced\n", "> **Complexity**: `[ADVANCED]`\n"),
        ("> **Complexity**: Beginner to Advanced\n", "> **Complexity**: `[ADVANCED]`\n"),
        # blockquote banner with track prefix, non-bold Complexity
        (
            "> Track: AI/ML Engineering | Complexity: Intermediate | Time: 90-120 minutes\n",
            "> Track: AI/ML Engineering | Complexity: `[MEDIUM]` | Time: 90-120 minutes\n",
        ),
        # inline sentence, non-blockquote -> container preserved
        (
            "**Complexity:** Advanced. **Time to complete:** 90-120 minutes.\n",
            "**Complexity:** `[ADVANCED]`. **Time to complete:** 90-120 minutes.\n",
        ),
    ],
)
def test_normalize_marker_line(line, expected):
    got, _changed, _b, _a = ncm.normalize_marker_line(line)
    assert got == expected


@pytest.mark.parametrize(
    "line",
    [
        # prose: lowercase "complexity" -> never a marker
        "This adds complexity: advanced users can tune it.\n",
        "The complexity of distributed systems grows quickly.\n",
        # prose with lowercase tier word after a capital-Complexity mention but unframed
        "Complexity here is advanced compared to before, in normal prose.\n",
        # regression #2217-R1 P2: line-leading capital-Complexity prose is NOT a framed
        # marker (no bold, no >/#/|) -> must be left untouched
        "Complexity: Advanced users can tune it.\n",
    ],
)
def test_prose_is_not_rewritten(line):
    got, changed, _b, _a = ncm.normalize_marker_line(line)
    assert got == line
    assert changed is False


def test_idempotent():
    line = "> **Complexity**: Intermediate\n"
    once, _c, _b, _a = ncm.normalize_marker_line(line)
    twice, changed2, _b2, _a2 = ncm.normalize_marker_line(once)
    assert once == twice
    assert changed2 is False


@pytest.mark.parametrize(
    "raw,tier",
    [
        ("Intermediate", "MEDIUM"),
        ("intermediate", "MEDIUM"),
        ("Beginner", "QUICK"),
        ("[BEGINNER]", "QUICK"),
        ("`[INTERMEDIATE]`", "MEDIUM"),
        ("Beginner to intermediate", "MEDIUM"),
        ("Intermediate to Advanced", "ADVANCED"),
        ("Intermediate-to-Advanced", "ADVANCED"),
        ("Beginner-to-Advanced", "ADVANCED"),
        ("Beginner to Advanced", "ADVANCED"),
        ("Advanced to Intermediate", "ADVANCED"),
        ("MEDIUM", "MEDIUM"),
        ("`[COMPLEX]`", "COMPLEX"),
    ],
)
def test_canonical_tier(raw, tier):
    assert ncm.canonical_tier(raw) == tier


def test_canonical_tier_rejects_unknown():
    with pytest.raises(ValueError):
        ncm.canonical_tier("Legendary")


def test_process_file_drops_frontmatter_key(tmp_path):
    p = tmp_path / "m.md"
    p.write_text(
        "---\n"
        'title: "X"\n'
        'complexity: "MEDIUM"\n'
        "sidebar:\n"
        "  order: 3\n"
        "---\n"
        "\n"
        "> **Complexity**: MEDIUM\n"
        "\n"
        "Body mentions complexity: advanced in prose and must not change.\n",
        encoding="utf-8",
    )
    res = ncm.process_file(str(p))
    assert res is not None
    out = res["new_content"]
    assert "complexity:" not in out.split("---\n")[1]  # frontmatter key gone
    assert "> **Complexity**: `[MEDIUM]`\n" in out  # body token canonicalized
    assert "complexity: advanced in prose" in out  # prose untouched


def test_process_file_noop_when_canonical(tmp_path):
    p = tmp_path / "m.md"
    p.write_text(
        "---\ntitle: X\n---\n\n> **Complexity**: `[MEDIUM]`\n\nBody.\n",
        encoding="utf-8",
    )
    assert ncm.process_file(str(p)) is None
