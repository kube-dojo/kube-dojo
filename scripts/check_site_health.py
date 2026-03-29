#!/usr/bin/env python3
"""KubeDojo Site Health Check — validates content integrity for Starlight (Astro).

Checks:
  1. Frontmatter (title, sidebar.order)
  2. Slug fields for dotted filenames
  3. Internal link targets exist
  4. No .md extension in internal links
  5. No README.md files
  6. Ukrainian file placement
  7. Module count vs STATUS.md
  8. Index files reference their child modules
  9. Module naming consistency (X.Y format)
  10. Empty directories
  11. Sidebar config references valid directories
  12. No orphaned modules (every module dir has index.md)
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DOCS_DIR = REPO_ROOT / "src" / "content" / "docs"
CONFIG_FILE = REPO_ROOT / "astro.config.mjs"

errors = []
warnings = []
stats = {}


def error(msg: str):
    errors.append(msg)


def warn(msg: str):
    warnings.append(msg)


def get_all_slugs() -> set:
    """Build a set of all known slugs/paths from content files."""
    slugs = set()
    for md in DOCS_DIR.rglob("*.md"):
        rel = md.relative_to(DOCS_DIR)
        if str(rel).startswith("uk/"):
            continue

        content = md.read_text(errors="replace")
        fm = content.split("---")[1] if content.startswith("---") and content.count("---") >= 2 else ""

        # Use slug if present, otherwise derive from file path
        slug_match = re.search(r'^slug:\s*(.+)$', fm, re.MULTILINE)
        if slug_match:
            slug = slug_match.group(1).strip().strip('"').strip("'")
        else:
            # Derive slug from file path
            if md.name == "index.md":
                slug = str(rel.parent)
            else:
                slug = str(rel.with_suffix(""))
            slug = slug.replace("\\", "/")

        slugs.add(slug.rstrip("/"))
        # Also add with trailing slash for matching
        slugs.add(slug.rstrip("/") + "/")

    return slugs


# ── Check 1: Frontmatter ─────────────────────────────────────────────────────

def check_frontmatter():
    """Check all .md files have valid Starlight frontmatter."""
    print("\n 1. Frontmatter validation...")
    missing_fm = 0
    missing_title = 0
    missing_order = 0

    for md in sorted(DOCS_DIR.rglob("*.md")):
        rel = str(md.relative_to(DOCS_DIR))
        content = md.read_text(errors="replace")

        if not content.startswith("---"):
            error(f"Missing frontmatter: {rel}")
            missing_fm += 1
            continue

        parts = content.split("---", 2)
        if len(parts) < 3:
            error(f"Malformed frontmatter: {rel}")
            missing_fm += 1
            continue

        fm = parts[1]

        if "title:" not in fm:
            error(f"Missing title: {rel}")
            missing_title += 1

        # Module files should have sidebar.order
        if md.name.startswith("module-") and "order:" not in fm:
            warn(f"Missing sidebar.order: {rel}")
            missing_order += 1

    total = len(list(DOCS_DIR.rglob("*.md")))
    ok = total - missing_fm
    stats["total_files"] = total
    print(f"    {ok}/{total} files have valid frontmatter")
    if missing_title:
        print(f"    {missing_title} missing title")
    if missing_order:
        print(f"    {missing_order} modules missing sidebar.order")


# ── Check 2: Slug fields for dotted filenames ────────────────────────────────

def check_slugs():
    """Files with dots in name (module-1.1-foo.md) MUST have slug: field."""
    print("\n 2. Slug fields for dotted filenames...")
    missing = 0

    for md in sorted(DOCS_DIR.rglob("*.md")):
        rel = str(md.relative_to(DOCS_DIR))
        name = md.stem  # filename without .md

        # Check if filename has a dot (e.g., module-1.1-foo)
        if "." in name:
            content = md.read_text(errors="replace")
            fm = content.split("---")[1] if content.startswith("---") and content.count("---") >= 2 else ""
            if "slug:" not in fm:
                error(f"Dotted filename without slug: {rel}")
                missing += 1

    if missing == 0:
        print("    All dotted filenames have slug fields")
    else:
        print(f"    {missing} files need slug fields")


# ── Check 3: Internal link targets exist ──────────────────────────────────────

def check_link_targets():
    """Verify internal markdown link targets resolve to existing content."""
    print("\n 3. Internal link target resolution...")
    all_slugs = get_all_slugs()
    broken = 0
    checked = 0

    for md in sorted(DOCS_DIR.rglob("*.md")):
        rel = str(md.relative_to(DOCS_DIR))
        if rel.startswith("uk/"):
            continue

        content = md.read_text(errors="replace")
        # Strip fenced code blocks
        content_clean = re.sub(r'```[^`]*```', '', content, flags=re.DOTALL)

        # Find all markdown links
        for match in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', content_clean):
            link_text, link_path = match.group(1), match.group(2)

            # Skip external links, anchors, images, mailto
            if any(link_path.startswith(p) for p in ("http", "#", "mailto:", "/")):
                # For absolute internal links starting with /
                if link_path.startswith("/") and not link_path.startswith("//"):
                    abs_path = link_path.lstrip("/").split("#")[0].rstrip("/")
                    checked += 1
                    if abs_path and abs_path not in all_slugs and abs_path + "/" not in all_slugs:
                        # Check if the directory exists as a fallback
                        dir_path = DOCS_DIR / abs_path
                        if not dir_path.exists() and not (dir_path.parent / "index.md").exists():
                            warn(f"Possibly broken absolute link in {rel}: {link_path}")
                            broken += 1
                continue

            # Relative link — resolve against file's directory
            checked += 1
            target = link_path.split("#")[0].rstrip("/")
            if not target:
                continue

            # Resolve relative path against file's parent directory
            base_dir = md.parent
            resolved = (base_dir / target).resolve()

            # Check multiple ways the link could be valid:
            # 1. Target is an existing directory (Astro serves index.md)
            if resolved.is_dir():
                continue
            # 2. Target exists as a file
            if resolved.exists():
                continue
            # 3. Target is a directory with /index.md
            if (resolved / "index.md").exists():
                continue
            # 4. Target matches a known slug (Astro slug routing)
            try:
                rel_from_docs = str(resolved.relative_to(DOCS_DIR.resolve())).replace("\\", "/")
            except ValueError:
                rel_from_docs = None
            if rel_from_docs and (rel_from_docs in all_slugs or rel_from_docs + "/" in all_slugs):
                continue
            # 5. Check if stripping trailing path component matches a slug
            # (handles module-1.1-foo/ → slug: .../module-1.1-foo)
            if rel_from_docs:
                slug_guess = rel_from_docs.rstrip("/")
                if any(s.endswith(slug_guess) for s in all_slugs):
                    continue

            # 6. Starlight URL model: non-index files are served as directories
            # (foo/bar.md → URL foo/bar/), so relative links resolve from
            # foo/bar/ not foo/. Try this as a fallback.
            if md.name != "index.md":
                starlight_base = md.parent / md.stem
                starlight_resolved = (starlight_base / target).resolve()
                try:
                    starlight_rel = str(starlight_resolved.relative_to(DOCS_DIR.resolve())).replace("\\", "/")
                except ValueError:
                    starlight_rel = None
                if starlight_resolved.is_dir() or starlight_resolved.exists():
                    continue
                if (starlight_resolved / "index.md").exists():
                    continue
                if starlight_rel and (starlight_rel in all_slugs or starlight_rel + "/" in all_slugs):
                    continue
                if starlight_rel:
                    starlight_slug = starlight_rel.rstrip("/")
                    if any(s.endswith(starlight_slug) for s in all_slugs):
                        continue

            warn(f"Broken relative link in {rel}: [{link_text[:30]}]({link_path})")
            broken += 1

    stats["links_checked"] = checked
    print(f"    {checked} links checked, {broken} potentially broken")


# ── Check 4: No .md extension in internal links ──────────────────────────────

def check_no_md_links():
    """Internal links should use slug format, not .md extension."""
    print("\n 4. No .md extension in internal links...")
    found = 0

    for md in sorted(DOCS_DIR.rglob("*.md")):
        rel = str(md.relative_to(DOCS_DIR))
        if rel.startswith("uk/"):
            continue

        content = md.read_text(errors="replace")
        content_clean = re.sub(r'```[^`]*```', '', content, flags=re.DOTALL)

        for match in re.finditer(r'\[([^\]]*)\]\(([^)]+\.md(?:#[^)]*)?)\)', content_clean):
            link_path = match.group(2)
            if link_path.startswith("http"):
                continue
            error(f"Internal .md link in {rel}: {link_path}")
            found += 1

    if found == 0:
        print("    All internal links use slug format")
    else:
        print(f"    {found} links still use .md extension")


# ── Check 5: No README.md ────────────────────────────────────────────────────

def check_no_readme():
    """No README.md files should remain."""
    print("\n 5. No README.md files...")
    readmes = list(DOCS_DIR.rglob("README.md"))
    for r in readmes:
        error(f"README.md not renamed: {r.relative_to(DOCS_DIR)}")
    if not readmes:
        print("    All READMEs converted to index.md")


# ── Check 6: Ukrainian file placement ────────────────────────────────────────

def check_uk_placement():
    """Ukrainian files should be in uk/ subdirectory."""
    print("\n 6. Ukrainian file placement...")
    misplaced = [str(f.relative_to(DOCS_DIR)) for f in DOCS_DIR.rglob("*.uk.md")]
    for m in misplaced:
        error(f"Ukrainian file with .uk.md suffix: {m}")
    if not misplaced:
        print("    All Ukrainian files in uk/ directory")


# ── Check 7: Module count ────────────────────────────────────────────────────

def check_module_count():
    """Check STATUS.md module count matches reality."""
    print("\n 7. Module count consistency...")
    status_file = REPO_ROOT / "STATUS.md"
    if not status_file.exists():
        warn("STATUS.md not found")
        return

    status = status_file.read_text()
    m = re.search(r'\*\*(\d+)\*\*', status)
    if m:
        claimed = int(m.group(1))
        actual = len([f for f in DOCS_DIR.rglob("module-*.md")
                      if not str(f.relative_to(DOCS_DIR)).startswith("uk/")])
        stats["module_count"] = actual
        if claimed != actual:
            warn(f"STATUS.md claims {claimed} modules but found {actual}")
        else:
            print(f"    Module count matches: {actual}")
    else:
        warn("Could not parse module count from STATUS.md")


# ── Check 8: Index completeness ──────────────────────────────────────────────

def check_index_completeness():
    """Index files should reference their child modules."""
    print("\n 8. Index files reference child modules...")
    missing = 0

    for index in sorted(DOCS_DIR.rglob("index.md")):
        rel = str(index.relative_to(DOCS_DIR))
        if rel.startswith("uk/"):
            continue

        parent = index.parent
        # Only check direct child modules (not in subdirectories)
        modules = sorted(f for f in parent.glob("module-*.md"))
        if not modules:
            continue

        content = index.read_text(errors="replace")
        for mod in modules:
            # Check for slug-based reference or filename reference
            slug_name = mod.stem  # e.g., module-1.1-foo
            if slug_name not in content and mod.name not in content:
                warn(f"{rel} doesn't mention {mod.name}")
                missing += 1

    if missing == 0:
        print("    All index files reference their modules")
    else:
        print(f"    {missing} missing module references in index files")


# ── Check 9: Module naming consistency ────────────────────────────────────────

def check_naming_consistency():
    """All modules should use module-X.Y-name.md format."""
    print("\n 9. Module naming consistency (X.Y format)...")
    inconsistent = 0

    # Pattern: module-N-name (no dot) — these are the old format
    old_pattern = re.compile(r'^module-(\d+)-[a-z]')
    # Pattern: module-X.Y-name (with dot) — this is the correct format
    new_pattern = re.compile(r'^module-(\d+\.\d+)-[a-z]')

    for md in sorted(DOCS_DIR.rglob("module-*.md")):
        rel = str(md.relative_to(DOCS_DIR))
        if rel.startswith("uk/"):
            continue

        name = md.stem
        if old_pattern.match(name) and not new_pattern.match(name):
            warn(f"Old naming format (module-N, not X.Y): {rel}")
            inconsistent += 1

    if inconsistent == 0:
        print("    All modules use X.Y naming format")
    else:
        print(f"    {inconsistent} modules still use old naming")


# ── Check 10: Empty directories ──────────────────────────────────────────────

def check_empty_dirs():
    """No empty directories should exist in content."""
    print("\n10. Empty directories...")
    empty = 0

    for d in sorted(DOCS_DIR.rglob("*")):
        if d.is_dir() and not any(d.iterdir()):
            warn(f"Empty directory: {d.relative_to(DOCS_DIR)}")
            empty += 1

    if empty == 0:
        print("    No empty directories")
    else:
        print(f"    {empty} empty directories found")


# ── Check 11: Sidebar config references valid directories ─────────────────────

def check_sidebar_dirs():
    """All directory references in astro.config.mjs should exist."""
    print("\n11. Sidebar config directory references...")

    if not CONFIG_FILE.exists():
        warn("astro.config.mjs not found")
        return

    config = CONFIG_FILE.read_text()
    missing = 0

    for match in re.finditer(r"directory:\s*['\"]([^'\"]+)['\"]", config):
        dir_path = match.group(1)
        full_path = DOCS_DIR / dir_path
        if not full_path.is_dir():
            error(f"Sidebar references missing directory: {dir_path}")
            missing += 1

    if missing == 0:
        dirs_found = len(re.findall(r"directory:", config))
        print(f"    All {dirs_found} directory references valid")
    else:
        print(f"    {missing} missing directories")


# ── Check 12: Every module directory has index.md ─────────────────────────────

def check_dirs_have_index():
    """Every directory containing modules should have an index.md."""
    print("\n12. Module directories have index.md...")
    missing = 0

    for d in sorted(DOCS_DIR.rglob("*")):
        if not d.is_dir():
            continue
        rel = str(d.relative_to(DOCS_DIR))
        if rel.startswith("uk/"):
            continue

        modules = list(d.glob("module-*.md"))
        if modules and not (d / "index.md").exists():
            error(f"Directory has modules but no index.md: {rel}")
            missing += 1

    if missing == 0:
        print("    All module directories have index.md")
    else:
        print(f"    {missing} directories missing index.md")


# ── Check 13: Title matches filename numbering ───────────────────────────────

def check_title_numbering():
    """Module title number should match filename number."""
    print("\n13. Title-filename number consistency...")
    mismatches = 0

    for md in sorted(DOCS_DIR.rglob("module-*.md")):
        rel = str(md.relative_to(DOCS_DIR))
        if rel.startswith("uk/"):
            continue

        name = md.stem
        # Extract number from filename: module-1.3-foo → 1.3
        fn_match = re.match(r'module-(\d+\.?\d*)', name)
        if not fn_match:
            continue
        fn_num = fn_match.group(1)

        content = md.read_text(errors="replace")
        fm = content.split("---")[1] if content.startswith("---") and content.count("---") >= 2 else ""

        title_match = re.search(r'title:\s*["\']?(?:Module\s+)?(\d+\.?\d*)', fm)
        if title_match:
            title_num = title_match.group(1)
            if fn_num != title_num:
                warn(f"Number mismatch in {rel}: filename={fn_num}, title={title_num}")
                mismatches += 1

    if mismatches == 0:
        print("    All titles match filenames")
    else:
        print(f"    {mismatches} title-filename mismatches")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("KubeDojo Site Health Check (Comprehensive)")
    print("=" * 60)

    if not DOCS_DIR.exists():
        print(f"\nERROR: Content directory not found: {DOCS_DIR}")
        sys.exit(1)

    check_frontmatter()
    check_slugs()
    check_link_targets()
    check_no_md_links()
    check_no_readme()
    check_uk_placement()
    check_module_count()
    check_index_completeness()
    check_naming_consistency()
    check_empty_dirs()
    check_sidebar_dirs()
    check_dirs_have_index()
    check_title_numbering()

    print("\n" + "=" * 60)
    e_count = len(errors)
    w_count = len(warnings)
    print(f"RESULTS: {e_count} errors, {w_count} warnings")
    if stats:
        parts = []
        if "total_files" in stats:
            parts.append(f"{stats['total_files']} files")
        if "module_count" in stats:
            parts.append(f"{stats['module_count']} modules")
        if "links_checked" in stats:
            parts.append(f"{stats['links_checked']} links checked")
        print(f"STATS:   {', '.join(parts)}")
    print("=" * 60)

    if errors:
        print(f"\nERRORS ({e_count}):")
        for e in errors[:30]:
            print(f"  ✗ {e}")
        if e_count > 30:
            print(f"  ... and {e_count - 30} more")

    if warnings:
        print(f"\nWARNINGS ({w_count}):")
        for w in warnings[:50]:
            print(f"  ⚠ {w}")
        if w_count > 50:
            print(f"  ... and {w_count - 50} more")

    if not errors and not warnings:
        print("\nAll checks passed.")
    elif not errors:
        print("\nNo errors. Warnings are non-blocking.")
    else:
        print("\nFix errors before pushing.")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
