#!/usr/bin/env python3
"""Migrate neural-dojo curriculum into kubedojo as a new AI Engineering track.

Reads:
  - /Users/krisztiankoos/projects/neural-dojo/curriculum.yaml (structure)
  - /Users/krisztiankoos/projects/neural-dojo/docs/curriculum/notes/module_*.md (content)

Writes:
  - src/content/docs/ai-ml-engineering/<phase>/module-<P>.<S>-<slug>.md

Conversions:
  - H1 title → YAML frontmatter `title:`
  - Add slug, sidebar.order, complexity, time fields
  - Strip emojis (kubedojo rule)
  - Rename Duration → Time to Complete, Learning Objectives → What You'll Be Able to Do
  - Convert internal links (module_47_* → module-2.1-* relative paths)
  - Drop status badges, last updated lines

Usage:
    python scripts/migrate_neural_dojo.py --dry-run
    python scripts/migrate_neural_dojo.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
NEURAL_DOJO_ROOT = Path("/Users/krisztiankoos/projects/neural-dojo")
CURRICULUM_YAML = NEURAL_DOJO_ROOT / "curriculum.yaml"
NOTES_DIR = NEURAL_DOJO_ROOT / "docs" / "curriculum" / "notes"

TARGET_ROOT = REPO_ROOT / "src" / "content" / "docs" / "ai-ml-engineering"

# Phase → directory slug mapping (kubedojo conventions)
PHASE_SLUGS = {
    0: "prerequisites",
    1: "ai-native-development",
    2: "generative-ai",
    3: "vector-rag",
    4: "frameworks-agents",
    5: "multimodal-ai",
    6: "deep-learning",
    7: "advanced-genai",
    8: "classical-ml",
    9: "ai-safety",
    10: "mlops",
    11: "ai-infrastructure",
    12: "history",
}

# Emoji stripping (kubedojo rule: no emojis in content)
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U00002600-\U000027BF"  # misc symbols + dingbats
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002700-\U000027BF"  # dingbats
    "\U0001FA70-\U0001FAFF"  # symbols & pictographs ext-A
    "\u2705"                 # check mark
    "\u274C"                 # cross mark
    "\u26A0"                 # warning
    "]+"
)


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def strip_emojis(text: str) -> str:
    """Remove emoji characters from text."""
    return EMOJI_RE.sub("", text)


def extract_title(content: str) -> str | None:
    """Extract H1 title from markdown content."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if not match:
        return None
    title = match.group(1).strip()
    # Strip emojis from title
    title = strip_emojis(title).strip()
    return title


def detect_complexity(content: str, hours_str: str) -> str:
    """Infer complexity from content size and stated hours."""
    line_count = len(content.splitlines())
    # Parse hours like "2-3", "7-8", "4"
    hours_match = re.search(r"(\d+)", hours_str or "")
    hours = int(hours_match.group(1)) if hours_match else 0

    if line_count < 400 or hours <= 2:
        return "[QUICK]"
    if line_count < 1000 or hours <= 4:
        return "[MEDIUM]"
    return "[COMPLEX]"


def convert_section_names(content: str) -> str:
    """Rename neural-dojo section headings to kubedojo conventions."""
    replacements = [
        (r"##\s+Learning Objectives", "## What You'll Be Able to Do"),
        (r"##\s+Why\s+([\w\s]+)\?", r"## Why This Module Matters"),
    ]
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, count=1)
    return content


def convert_internal_links(content: str, module_map: dict[str, str]) -> str:
    """Convert neural-dojo internal links to kubedojo relative paths.

    module_map: {legacy_id (e.g. "46") → new_path (e.g. "../mlops/module-10.1-kubernetes-for-ml")}
    """

    def replace_link(match: re.Match) -> str:
        full_match = match.group(0)
        link_target = match.group(1)
        # Extract module number from legacy filename
        m = re.match(r"module_(\d+)(?:\.\d+)?_", link_target)
        if not m:
            return full_match
        legacy_id = m.group(1).lstrip("0") or "0"
        if legacy_id in module_map:
            return full_match.replace(link_target, module_map[legacy_id])
        return full_match

    return re.sub(r"\(([\w/.-]*module_\d+(?:\.\d+)?_[\w-]+)(?:\.md)?\)", replace_link, content)


def strip_metadata_lines(content: str) -> str:
    """Remove neural-dojo metadata lines (Last Updated, Status, Duration)."""
    lines = content.split("\n")
    cleaned = []
    skip_until_separator = False
    metadata_re = re.compile(r"^\*\*(?:Last Updated|Status|Duration)\*\*:")

    for line in lines:
        if metadata_re.match(line):
            skip_until_separator = True
            continue
        if skip_until_separator and line.strip() == "---":
            skip_until_separator = False
            continue
        if skip_until_separator and not line.strip():
            continue
        skip_until_separator = False
        cleaned.append(line)

    return "\n".join(cleaned)


def build_frontmatter(
    title: str, slug: str, order: int, complexity: str, hours: str
) -> str:
    """Build kubedojo-compatible frontmatter."""
    return f"""---
title: "{title}"
slug: {slug}
sidebar:
  order: {order}
---
> **AI/ML Engineering Track** | Complexity: `{complexity}` | Time: {hours}
> **Migrated from neural-dojo** — pending pipeline polish

"""


def convert_module(
    source_path: Path,
    title: str,
    new_slug: str,
    order: int,
    hours: str,
    module_map: dict[str, str],
) -> str:
    """Convert a neural-dojo module to kubedojo format."""
    raw = source_path.read_text()

    # Strip the H1 title (will be in frontmatter)
    body = re.sub(r"^#\s+.+\n", "", raw, count=1)

    # Strip metadata lines
    body = strip_metadata_lines(body)

    # Strip emojis from body
    body = strip_emojis(body)

    # Convert section names
    body = convert_section_names(body)

    # Convert internal links
    body = convert_internal_links(body, module_map)

    # Remove orphaned blank lines at start
    body = body.lstrip("\n")

    # Detect complexity
    complexity = detect_complexity(body, hours)

    # Build final content
    fm = build_frontmatter(title, new_slug, order, complexity, hours)
    return fm + body


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate neural-dojo to kubedojo")
    parser.add_argument("--dry-run", action="store_true", help="Show plan, don't write files")
    parser.add_argument("--phase", type=int, help="Migrate only specific phase")
    args = parser.parse_args()

    if not CURRICULUM_YAML.exists():
        print(f"ERROR: {CURRICULUM_YAML} not found")
        return 1

    curriculum = yaml.safe_load(CURRICULUM_YAML.read_text())
    phases = curriculum.get("phases", [])

    # Build module_map first (needed for internal link conversion)
    module_map: dict[str, str] = {}
    plan: list[dict] = []

    for phase in phases:
        phase_id = phase["id"]
        if args.phase is not None and phase_id != args.phase:
            continue
        phase_slug = PHASE_SLUGS.get(phase_id)
        if not phase_slug:
            continue

        for module in phase.get("modules", []):
            seq = module["seq"]
            legacy_id = str(module.get("legacy_id", "")).lstrip("0") or "0"
            if not legacy_id:
                continue

            # Find source file
            source_files = list(NOTES_DIR.glob(f"module_{module['legacy_id']}_*.md"))
            if not source_files:
                # Try with leading zero
                source_files = list(NOTES_DIR.glob(f"module_{int(legacy_id):02d}_*.md"))
            if not source_files:
                continue
            source_path = source_files[0]

            name = module.get("name", source_path.stem)
            file_slug = slugify(name)
            new_slug = f"ai-ml-engineering/{phase_slug}/module-{phase_id}.{seq}-{file_slug}"
            target_dir = TARGET_ROOT / phase_slug
            target_path = target_dir / f"module-{phase_id}.{seq}-{file_slug}.md"

            # Order: phase * 100 + seq for stable sort
            order = (phase_id + 1) * 100 + seq + 1

            module_map[legacy_id] = f"../{phase_slug}/module-{phase_id}.{seq}-{file_slug}/"
            plan.append({
                "source": source_path,
                "target": target_path,
                "title": name,
                "slug": new_slug,
                "order": order,
                "hours": module.get("hours", ""),
                "phase_id": phase_id,
                "phase_slug": phase_slug,
                "phase_name": phase["name"],
            })

    print(f"Migration plan: {len(plan)} modules across {len({p['phase_id'] for p in plan})} phases")
    print()

    if args.dry_run:
        for item in plan:
            print(f"  {item['source'].name}")
            print(f"    → {item['target'].relative_to(REPO_ROOT)}")
            print(f"    title: {item['title']}")
            print(f"    slug: {item['slug']}")
        return 0

    # Write files
    written = 0
    for item in plan:
        try:
            content = convert_module(
                item["source"],
                item["title"],
                item["slug"],
                item["order"],
                item["hours"],
                module_map,
            )
            item["target"].parent.mkdir(parents=True, exist_ok=True)
            item["target"].write_text(content)
            written += 1
            print(f"  ✓ {item['target'].relative_to(REPO_ROOT)}")
        except Exception as e:
            print(f"  ✗ {item['source'].name}: {e}", file=sys.stderr)

    print(f"\nMigrated {written}/{len(plan)} modules")

    # Generate phase index files
    phases_seen: dict[int, dict] = {}
    for item in plan:
        pid = item["phase_id"]
        if pid not in phases_seen:
            phases_seen[pid] = {
                "name": item["phase_name"],
                "slug": item["phase_slug"],
                "modules": [],
            }
        phases_seen[pid]["modules"].append(item)

    for pid, phase in phases_seen.items():
        index_path = TARGET_ROOT / phase["slug"] / "index.md"
        index_content = f"""---
title: "{phase['name']}"
sidebar:
  order: 0
  label: "{phase['name']}"
---

> **AI/ML Engineering Track** | Phase {pid}

## Modules

| # | Module |
|---|--------|
"""
        for m in phase["modules"]:
            mod_slug = m["target"].stem
            index_content += f"| {pid}.{m['target'].stem.split('-')[1].split('.')[1]} | [{m['title']}]({mod_slug}/) |\n"

        index_path.write_text(index_content)
        print(f"  ✓ {index_path.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
