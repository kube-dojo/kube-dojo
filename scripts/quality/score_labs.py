#!/usr/bin/env python3
"""KubeDojo Phase-F lab quality scorer.

Discovers every markdown module that carries a ``lab:`` frontmatter block,
scores it on five rubric dimensions (1-5 each), and writes a markdown (or
JSON) audit report.

Usage example::

    # Score everything, write docs/lab-audit-<today>.md
    python scripts/quality/score_labs.py

    # Only CKA labs, threshold 3.5, emit JSON for CI
    python scripts/quality/score_labs.py --track cka --threshold 3.5 --json

    # Custom output path
    python scripts/quality/score_labs.py --output /tmp/audit.md

Dimensions
----------
setup_clarity
    Does a Setup/Prerequisites section exist with concrete starting-state
    commands and prerequisite list?
acceptance_criteria
    Are there ``- [ ]`` checkbox items in an Acceptance-Criteria/Verification/
    Success-Criteria section with concrete observable state?
teardown
    Is there a Cleanup/Teardown section with concrete deletion commands?
time_estimate_realism
    Does the ``lab.duration`` field match lab complexity (kubectl cmd count +
    setup steps + acceptance items)?
hands_on_depth
    Does the lab require decisions (debug, fix, explain) or is it pure
    rote kubectl-by-rote?
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_ROOT = REPO_ROOT / "src" / "content" / "docs"
DOCS_OUT_ROOT = REPO_ROOT / "docs"

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

# Section headings (## or ### level)
_HEADING_RE = re.compile(r"^#{2,3}\s+(.+?)\s*$", re.MULTILINE)

# Checkbox items  - [ ] ...
CHECKBOX_RE = re.compile(r"^\s*-\s+\[ \]\s+.+", re.MULTILINE)

# kubectl invocations (kubectl or alias k at line-start / after ; & |)
KUBECTL_CMD_RE = re.compile(
    r"(?m)(?:^|[;&|]\s*)(?:kubectl|k)\s+"
    r"(?:get|describe|apply|delete|create|patch|scale|rollout|exec|logs|"
    r"run|expose|edit|label|annotate|drain|cordon|uncordon|taint|top|wait|"
    r"auth|config|set|diff|cp|port-forward|api-resources|version)\b"
)

# "kind delete cluster" or "kubectl delete ns ..." cleanup signals
CLEANUP_CMD_RE = re.compile(
    r"(?m)(?:kind\s+delete\s+cluster|kubectl\s+delete\s+(?:ns|namespace)\b)",
    re.IGNORECASE,
)

# Vague acceptance verbs (score-lowering signal)
VAGUE_VERB_RE = re.compile(
    r"\b(?:verify\s+it\s+works|check\s+that\s+it\s+works?|confirm\s+it\s+(?:is\s+)?working|"
    r"make\s+sure\s+it\s+works?|test\s+that\s+it\s+works?)\b",
    re.IGNORECASE,
)

# Concrete observable state patterns (score-raising signal)
CONCRETE_OBS_RE = re.compile(
    r"(?:kubectl\s+(?:get|describe|logs|auth|top|wait)\b"
    r"|shows?\s+\d+\s+Running"
    r"|shows?\s+(?:Ready|Bound|Running|Active|Succeeded)"
    r"|output\s+(?:shows?|contains?|includes?)"
    r"|\bRunning\b.*\bReady\b"
    r"|\bno\b.*\berrors?\b)",
    re.IGNORECASE,
)

# Decision-demanding verbs (score-raising for hands_on_depth)
DECISION_RE = re.compile(
    r"\b(?:debug|diagnose|fix|troubleshoot|identify\s+why|explain\s+why|"
    r"find\s+(?:the\s+)?(?:bug|issue|problem|root\s+cause)|"
    r"broken|misconfigur|why\s+(?:is|are|does|did)\b|"
    r"what\s+(?:is\s+wrong|went\s+wrong|caused)|"
    r"investigate|repair|recover|restore)\b",
    re.IGNORECASE,
)

# Rote patterns (score-lowering for hands_on_depth)
ROTE_RE = re.compile(
    r"\b(?:run\s+the\s+(?:following\s+)?command|copy\s+the\s+(?:following\s+)?yaml|"
    r"paste\s+the|apply\s+the\s+following|simply\s+run)\b",
    re.IGNORECASE,
)

# Duration parsing: "45 min", "1 hour", "1h30m", etc.
_DURATION_RE = re.compile(
    r"(?:(\d+(?:\.\d+)?)\s*h(?:our)?s?)?\s*(?:(\d+(?:\.\d+)?)\s*m(?:in)?)?",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class LabScore:
    """Scores for a single lab module."""

    path: str
    track: str
    lab_id: str
    duration_raw: str
    setup_clarity: int = 0
    acceptance_criteria: int = 0
    teardown: int = 0
    time_estimate_realism: int = 0
    hands_on_depth: int = 0
    # Derived
    overall: float = field(init=False, default=0.0)
    # Fix suggestions per dimension
    suggestions: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._recompute()

    def _recompute(self) -> None:
        dims = [
            self.setup_clarity,
            self.acceptance_criteria,
            self.teardown,
            self.time_estimate_realism,
            self.hands_on_depth,
        ]
        self.overall = round(sum(dims) / len(dims), 2)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["overall"] = self.overall
        return d


# ---------------------------------------------------------------------------
# Frontmatter + body parsing
# ---------------------------------------------------------------------------


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Return (frontmatter_dict, body_text) from a markdown string.

    Parameters
    ----------
    text:
        Raw file content.

    Returns
    -------
    tuple[dict, str]
        Parsed YAML dict (empty dict on failure) and the body after ``---``.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    body = text[m.end():]
    return fm, body


def _has_lab_block(frontmatter: dict[str, Any]) -> bool:
    """Return True when the frontmatter has a non-empty ``lab:`` block."""
    return isinstance(frontmatter.get("lab"), dict) and bool(frontmatter["lab"])


def _extract_section(body: str, *heading_variants: str) -> str:
    """Extract text below the first matching heading until the next heading.

    Parameters
    ----------
    body:
        Markdown body text.
    *heading_variants:
        Lower-cased heading names to search for (e.g. ``"setup"``, ``"prerequisites"``).

    Returns
    -------
    str
        Section content, or empty string if not found.
    """
    normalized_variants = tuple(v.lower() for v in heading_variants)
    lines = body.splitlines()
    start = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("##"):
            continue
        heading = stripped.lstrip("#").strip().lower()
        if any(variant in heading for variant in normalized_variants):
            start = i
            break
    if start < 0:
        return ""
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("##"):
            end = j
            break
    return "\n".join(lines[start + 1 : end])


# ---------------------------------------------------------------------------
# Scoring helpers (5 dimensions)
# ---------------------------------------------------------------------------


def _score_setup_clarity(body: str) -> int:
    """Score 1-5: setup section presence, commands, and prerequisites.

    Rubric
    ------
    1 — No Setup/Prerequisites section at all.
    2 — Section exists but is prose only, no shell commands or checklist.
    3 — Section exists with ≥1 shell command block; no explicit prerequisites.
    4 — Section has commands AND a prerequisites list.
    5 — Rich section: commands + prerequisites + concrete starting-state
        description (e.g. "you should have a running cluster with …").

    Parameters
    ----------
    body:
        Markdown body text (post-frontmatter).
    """
    section = _extract_section(body, "setup", "prerequisites", "pre-requisites")
    if not section:
        return 1

    has_code = "```" in section
    has_prereq_mention = bool(
        re.search(r"\bprerequisite|prereq\b|module\s+\d+|you\s+(?:need|should|must)\b", section, re.IGNORECASE)
    )
    has_starting_state = bool(
        re.search(
            r"running\s+cluster|existing\s+cluster|kind\s+cluster|kubeconfig|starting[-\s]state"
            r"|fresh\s+(?:cluster|node)|before\s+(?:you\s+)?begin",
            section,
            re.IGNORECASE,
        )
    )

    if has_code and has_prereq_mention and has_starting_state:
        return 5
    if has_code and has_prereq_mention:
        return 4
    if has_code:
        return 3
    return 2


def _score_acceptance_criteria(body: str) -> int:
    """Score 1-5: acceptance criteria quality.

    Rubric
    ------
    1 — No Acceptance Criteria / Verification / Success Criteria section.
    2 — Section exists but only has vague prose ("verify it works").
    3 — Section has ≥1 checkbox item but items are vague.
    4 — Section has ≥3 checkbox items, at least one is concrete.
    5 — Section has ≥5 checkbox items, majority are concrete observable
        state (kubectl command output, status strings, etc.) and no vague verbs.

    Parameters
    ----------
    body:
        Markdown body text.
    """
    section = _extract_section(
        body,
        "acceptance criteria",
        "verification",
        "success criteria",
        "success",
        "lab objectives",
    )
    if not section:
        return 1

    checkboxes = CHECKBOX_RE.findall(section)
    concrete_count = sum(1 for cb in checkboxes if CONCRETE_OBS_RE.search(cb))
    vague_count = sum(1 for cb in checkboxes if VAGUE_VERB_RE.search(cb))
    n = len(checkboxes)

    if n == 0:
        # Section exists but no checkboxes
        return 2
    if n < 3:
        return 3
    if n >= 5 and concrete_count >= 3 and vague_count == 0:
        return 5
    if n >= 3 and concrete_count >= 1:
        return 4
    return 3


def _score_teardown(body: str) -> int:
    """Score 1-5: teardown/cleanup completeness.

    Rubric
    ------
    1 — No Cleanup/Teardown section.
    2 — Section exists but has prose only, no commands.
    3 — Section has commands but they are generic ("kubectl delete -f …").
    4 — Section has explicit namespace or cluster deletion commands.
    5 — Section has namespace/cluster deletion AND verifies nothing leaked
        (e.g. lists remaining resources, checks node taints removed).

    Parameters
    ----------
    body:
        Markdown body text.
    """
    section = _extract_section(body, "cleanup", "teardown", "clean up")
    if not section:
        return 1

    has_code = "```" in section
    if not has_code:
        return 2

    has_concrete = bool(CLEANUP_CMD_RE.search(section))
    has_verify = bool(
        re.search(
            r"kubectl\s+get\s+(?:ns|namespace|pods?|nodes?)\b"
            r"|verify\s+(?:no|that\s+no)"
            r"|confirm\s+(?:no|that\s+no)"
            r"|no\s+(?:remaining|leftover)",
            section,
            re.IGNORECASE,
        )
    )

    if has_concrete and has_verify:
        return 5
    if has_concrete:
        return 4
    return 3


def _parse_duration_minutes(duration_raw: str) -> float | None:
    """Parse a duration string like ``"45 min"`` or ``"1h30m"`` into minutes.

    Parameters
    ----------
    duration_raw:
        Raw string from ``lab.duration`` frontmatter.

    Returns
    -------
    int | None
        Parsed minutes, or None if unparseable.
    """
    if not duration_raw:
        return None
    s = str(duration_raw).strip().lower()
    # Try "Xh Ym" / "X hour Y min" / "Xm"
    m = _DURATION_RE.fullmatch(s)
    if m and (m.group(1) or m.group(2)):
        hours = float(m.group(1) or 0)
        mins = float(m.group(2) or 0)
        total = hours * 60 + mins
        return total if total > 0 else None
    # Fallback: parse decimal units ("1.5 hour", "2.5 min", "0.5 hr", ...).
    normalized = (
        s.replace("hours", "hour")
        .replace("hrs", "hr")
        .replace("minutes", "min")
        .replace("minute", "min")
    )
    total_minutes = 0.0
    found = False
    for num_s, unit in re.findall(r"(\d+(?:\.\d+)?)\s*(hour|hr|min)", normalized):
        value = float(num_s)
        if unit in {"hour", "hr"}:
            total_minutes += value * 60
        else:
            total_minutes += value
        found = True
    if not found:
        return None
    if total_minutes <= 0:
        return None
    return round(total_minutes)


def _estimate_complexity_minutes(body: str) -> float:
    """Estimate lab complexity as expected completion minutes.

    Heuristic: ~30s per distinct kubectl command + 2 min per multi-step
    deployment (code block with ≥3 commands) + 1 min per acceptance item.

    Parameters
    ----------
    body:
        Markdown body text.
    """
    kubectl_cmds = KUBECTL_CMD_RE.findall(body)
    n_kubectl = len(kubectl_cmds)

    # Count multi-step deployment blocks (bash/sh blocks with ≥3 lines of commands)
    code_blocks = re.findall(r"```(?:bash|sh|shell)\n(.*?)```", body, re.DOTALL)
    n_complex_blocks = sum(
        1 for block in code_blocks if len(block.strip().splitlines()) >= 3
    )

    n_checkboxes = len(CHECKBOX_RE.findall(body))

    estimated = (n_kubectl * 0.5) + (n_complex_blocks * 2.0) + (n_checkboxes * 1.0)
    # Clamp minimum to 10 minutes for any non-trivial lab
    return max(estimated, 10.0)


def _score_time_estimate_realism(body: str, duration_raw: str) -> int:
    """Score 1-5: how realistic is the stated ``lab.duration``?

    Rubric
    ------
    1 — No duration field, or off by 3× or more from heuristic estimate.
    2 — Off by 2-3×.
    3 — Off by 1.5-2×.
    4 — Within 1.5× of estimate.
    5 — Within 1.2× of estimate.

    Parameters
    ----------
    body:
        Markdown body text.
    duration_raw:
        Raw duration string from frontmatter.
    """
    stated = _parse_duration_minutes(duration_raw)
    if stated is None:
        return 1

    estimated = _estimate_complexity_minutes(body)
    if estimated <= 0:
        return 3  # Can't compare

    ratio = max(stated, estimated) / min(stated, estimated)
    if ratio <= 1.2:
        return 5
    if ratio <= 1.5:
        return 4
    if ratio <= 2.0:
        return 3
    if ratio <= 3.0:
        return 2
    return 1


def _score_hands_on_depth(body: str) -> int:
    """Score 1-5: decision-making depth vs. rote kubectl-by-rote.

    Rubric
    ------
    1 — Pure rote: copy commands, observe output.  No decision required.
    2 — Mostly rote with one or two "what do you see?" questions.
    3 — Mix of rote and one decision point (fix a misconfiguration).
    4 — Multiple decision points; at least one debugging scenario.
    5 — Heavy diagnosis/debugging: broken state, root-cause analysis, fix,
        explain, verify — learner must think, not copy.

    Parameters
    ----------
    body:
        Markdown body text.
    """
    decision_count = len(DECISION_RE.findall(body))
    rote_count = len(ROTE_RE.findall(body))

    # Also count "YOUR TASK:" blocks as decision points
    task_count = len(re.findall(r"your\s+task", body, re.IGNORECASE))
    decision_count += task_count

    if decision_count == 0:
        return 1 if rote_count > 0 else 2
    if decision_count == 1:
        return 3
    if decision_count == 2:
        return 4 if rote_count <= 2 else 3
    # 3+ decision points
    if decision_count >= 3 and rote_count <= 2:
        return 5
    return 4


# ---------------------------------------------------------------------------
# Fix suggestions
# ---------------------------------------------------------------------------

_FIX_SUGGESTIONS: dict[str, dict[int, str]] = {
    "setup_clarity": {
        1: "Add a `## Setup` section with bash commands that create the lab environment.",
        2: "Add shell commands (kind create / kubectl apply) to the Setup section.",
        3: "List explicit prerequisites (e.g. '- Module 1.1 completed') in Setup.",
        4: "Add a concrete starting-state description ('you should have a running 2-node cluster…').",
    },
    "acceptance_criteria": {
        1: "Add a `### Success Criteria` section with `- [ ]` checkbox items.",
        2: "Replace vague prose with checkbox items containing observable kubectl output.",
        3: "Add ≥3 checkboxes with specific observable state (`kubectl get pods -n X shows 3 Running`).",
        4: "Expand to ≥5 checkboxes; remove vague phrases like 'verify it works'.",
    },
    "teardown": {
        1: "Add a `### Cleanup` section with `kubectl delete ns <lab-ns>` or `kind delete cluster`.",
        2: "Add shell commands to the Cleanup section (namespace deletion, cluster teardown).",
        3: "Replace generic delete with explicit namespace/cluster deletion command.",
        4: "Add a verification step after deletion (`kubectl get ns` should not show the lab namespace).",
    },
    "time_estimate_realism": {
        1: "Re-estimate duration: lab has many commands — consider 60+ min, or reduce lab scope.",
        2: "Duration is off by 2-3×; recalibrate against command count and deployment complexity.",
        3: "Duration is slightly off; adjust by ±30% to match heuristic estimate.",
        4: "Duration is close but could be tightened to match lab complexity.",
    },
    "hands_on_depth": {
        1: "Add a debugging scenario: break a configuration intentionally, ask learner to diagnose and fix.",
        2: "Include at least one 'YOUR TASK:' block requiring a decision or root-cause analysis.",
        3: "Add a second debugging challenge; require learner to explain *why* something failed.",
        4: "Promote to full diagnosis: provide broken state, ask for root-cause, fix, and verify steps.",
    },
}


def _suggestions_for(score_name: str, score: int) -> str:
    """Return a concrete 1-line fix suggestion for a low dimension score.

    Parameters
    ----------
    score_name:
        Dimension key (e.g. ``"setup_clarity"``).
    score:
        Current score (1-5).

    Returns
    -------
    str
        Suggestion string, or empty string if score is already 5.
    """
    if score >= 5:
        return ""
    return _FIX_SUGGESTIONS.get(score_name, {}).get(score, "")


# ---------------------------------------------------------------------------
# File scoring
# ---------------------------------------------------------------------------


def score_file(path: Path) -> LabScore | None:
    """Parse and score a single markdown file.

    Returns None if the file has no valid ``lab:`` block.

    Parameters
    ----------
    path:
        Absolute or repo-relative path to a ``.md`` file.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    fm, body = _split_frontmatter(text)
    if not _has_lab_block(fm):
        return None

    lab_block: dict[str, Any] = fm["lab"]
    lab_id = str(lab_block.get("id", path.stem))
    duration_raw = str(lab_block.get("duration", ""))

    # Derive track from path relative to CONTENT_ROOT
    try:
        rel = path.relative_to(CONTENT_ROOT)
        track = rel.parts[0] if len(rel.parts) > 1 else "misc"
    except ValueError:
        track = "misc"

    sc = LabScore(
        path=str(path.relative_to(REPO_ROOT)),
        track=track,
        lab_id=lab_id,
        duration_raw=duration_raw,
    )

    sc.setup_clarity = _score_setup_clarity(body)
    sc.acceptance_criteria = _score_acceptance_criteria(body)
    sc.teardown = _score_teardown(body)
    sc.time_estimate_realism = _score_time_estimate_realism(body, duration_raw)
    sc.hands_on_depth = _score_hands_on_depth(body)
    sc._recompute()

    for dim in ("setup_clarity", "acceptance_criteria", "teardown",
                "time_estimate_realism", "hands_on_depth"):
        suggestion = _suggestions_for(dim, getattr(sc, dim))
        if suggestion:
            sc.suggestions[dim] = suggestion

    return sc


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_lab_files(
    content_root: Path = CONTENT_ROOT,
    track_filter: str | None = None,
) -> list[Path]:
    """Recursively find all ``.md`` files that contain a ``lab:`` frontmatter block.

    Parameters
    ----------
    content_root:
        Root directory to scan (default: ``src/content/docs``).
    track_filter:
        Optional substring filter applied to the path relative to
        *content_root* (e.g. ``"cka"`` to restrict to CKA modules).

    Returns
    -------
    list[Path]
        Sorted list of matching paths.
    """
    candidates: list[Path] = []
    for md_path in sorted(content_root.rglob("*.md")):
        if track_filter and track_filter.lower() not in str(
            md_path.relative_to(content_root)
        ).lower():
            continue
        candidates.append(md_path)
    return candidates


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def _worst_quartile_threshold(scores: list[float]) -> float:
    """Return the value below which the worst 25% of labs fall."""
    if not scores:
        return 0.0
    sorted_scores = sorted(scores)
    idx = max(0, len(sorted_scores) // 4 - 1)
    return round(sorted_scores[idx], 2)


def build_markdown_report(
    results: list[LabScore],
    run_date: str,
    threshold: float,
) -> str:
    """Produce a full markdown audit report.

    Parameters
    ----------
    results:
        All scored labs.
    run_date:
        ISO date string (``YYYY-MM-DD``).
    threshold:
        Score below which labs get a punch-list entry.
    """
    if not results:
        return "# Lab Audit\n\nNo labs found.\n"

    overall_avg = round(sum(r.overall for r in results) / len(results), 2)

    lines: list[str] = []
    lines.append(f"# Lab Quality Audit — {run_date}\n")
    lines.append(
        f"**Run date:** {run_date}  \n"
        f"**Total labs scored:** {len(results)}  \n"
        f"**Overall average:** {overall_avg:.2f} / 5.00  \n"
        f"**Threshold for punch-list:** {threshold:.1f}\n"
    )

    # ---- Per-track summary ------------------------------------------------
    lines.append("\n## Per-Track Summary\n")
    lines.append(
        "| Track | Labs | Avg Score | Worst-Quartile Threshold |"
    )
    lines.append("| --- | ---: | ---: | ---: |")

    from collections import defaultdict

    by_track: dict[str, list[LabScore]] = defaultdict(list)
    for r in results:
        by_track[r.track].append(r)

    for track in sorted(by_track):
        track_results = by_track[track]
        track_scores = [r.overall for r in track_results]
        avg = round(sum(track_scores) / len(track_scores), 2)
        wq = _worst_quartile_threshold(track_scores)
        lines.append(f"| `{track}` | {len(track_results)} | {avg:.2f} | {wq:.2f} |")

    # ---- Punch list -------------------------------------------------------
    below_threshold = [r for r in results if r.overall < threshold]
    lines.append(f"\n## Punch List — Labs Below {threshold:.1f}\n")
    if not below_threshold:
        lines.append(f"_All labs score ≥ {threshold:.1f}. No action required._\n")
    else:
        lines.append(
            f"_{len(below_threshold)} lab(s) require attention._\n"
        )
        for r in sorted(below_threshold, key=lambda x: x.overall):
            lines.append(f"\n### `{r.lab_id}` — overall {r.overall:.2f}\n")
            lines.append(f"**File:** `{r.path}`\n")
            if r.suggestions:
                lines.append("**Failing dimensions and fixes:**\n")
                for dim, fix in r.suggestions.items():
                    score = getattr(r, dim)
                    lines.append(f"- **{dim}** (score {score}): {fix}")
            lines.append("")

    # ---- Full sortable table ----------------------------------------------
    lines.append("\n## All Labs — Full Score Table\n")
    lines.append(
        "| Lab ID | Track | Setup | Acceptance | Teardown | Time Est. | Depth | Overall |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")

    for r in sorted(results, key=lambda x: x.overall):
        lines.append(
            f"| `{r.lab_id}` | `{r.track}` "
            f"| {r.setup_clarity} | {r.acceptance_criteria} "
            f"| {r.teardown} | {r.time_estimate_realism} "
            f"| {r.hands_on_depth} | **{r.overall:.2f}** |"
        )

    return "\n".join(lines) + "\n"


def build_json_report(
    results: list[LabScore],
    run_date: str,
    threshold: float,
) -> str:
    """Produce a machine-readable JSON report.

    Parameters
    ----------
    results:
        All scored labs.
    run_date:
        ISO date string.
    threshold:
        Score cutoff.
    """
    overall_avg = round(sum(r.overall for r in results) / len(results), 2) if results else 0.0
    payload = {
        "run_date": run_date,
        "total_labs": len(results),
        "overall_avg": overall_avg,
        "threshold": threshold,
        "labs": [r.as_dict() for r in results],
    }
    return json.dumps(payload, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Score KubeDojo lab modules on a 5-dimension rubric.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--output",
        metavar="PATH",
        help="Output file path (default: docs/lab-audit-<YYYY-MM-DD>.md)",
    )
    p.add_argument(
        "--track",
        metavar="FILTER",
        help="Only score labs whose path contains FILTER (substring, case-insensitive).",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=3.0,
        metavar="N",
        help="Overall score cutoff for punch-list entries (default: 3.0).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="emit_json",
        help="Emit machine-readable JSON instead of markdown.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    """Entry point for the lab scorer.

    Parameters
    ----------
    argv:
        Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns
    -------
    int
        Exit code (0 = success).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    run_date = date.today().isoformat()

    # Resolve output path
    if args.output:
        out_path = Path(args.output)
    else:
        suffix = ".json" if args.emit_json else ".md"
        out_path = DOCS_OUT_ROOT / f"lab-audit-{run_date}{suffix}"

    # Discover files
    candidates = discover_lab_files(track_filter=args.track)
    print(
        f"[score_labs] Scanning {len(candidates)} candidate files"
        + (f" (track filter: {args.track!r})" if args.track else ""),
        file=sys.stderr,
    )

    results: list[LabScore] = []
    for path in candidates:
        rel = path.relative_to(CONTENT_ROOT)
        sc = score_file(path)
        if sc is None:
            continue
        results.append(sc)
        print(
            f"  scored  {rel}  →  {sc.overall:.2f}",
            file=sys.stderr,
        )

    print(
        f"[score_labs] {len(results)} labs scored, avg {sum(r.overall for r in results)/max(len(results),1):.2f}",
        file=sys.stderr,
    )

    if args.emit_json:
        report = build_json_report(results, run_date, args.threshold)
    else:
        report = build_markdown_report(results, run_date, args.threshold)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"[score_labs] Report written to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
