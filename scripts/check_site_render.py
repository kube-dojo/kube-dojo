#!/usr/bin/env python3
"""KubeDojo Site Render Check — validates the built HTML for rendering issues.

Requires the MkDocs dev server to be running at http://127.0.0.1:8001/kubedojo/

Run: python scripts/check_site_render.py
"""

import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "http://127.0.0.1:8001/kubedojo"
DOCS_DIR = Path(__file__).parent.parent / "docs"
MKDOCS_YML = Path(__file__).parent.parent / "mkdocs.yml"

errors = []
warnings = []
pages_checked = 0


def error(msg: str):
    errors.append(msg)
    print(f"  FAIL: {msg}")


def warn(msg: str):
    warnings.append(msg)
    print(f"  WARN: {msg}")


def fetch(path: str) -> str | None:
    """Fetch a page from the local dev server."""
    url = f"{BASE_URL}/{path}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        error(f"HTTP {e.code} for /{path}")
        return None
    except Exception as e:
        error(f"Cannot fetch /{path}: {e}")
        return None


def get_all_pages() -> list[str]:
    """Extract all page paths from mkdocs.yml nav."""
    pages = []
    with open(MKDOCS_YML) as f:
        for line in f:
            line = line.strip()
            m = re.match(r'^-\s+(?:.*:\s+)?(.+\.md)\s*$', line)
            if m:
                filepath = m.group(1).strip().strip('"').strip("'")
                # Convert docs path to URL path
                url_path = filepath.replace(".md", "/").replace("README/", "")
                if url_path.endswith("index/"):
                    url_path = url_path.replace("index/", "")
                pages.append((filepath, url_path))
    return pages


def check_page_renders(filepath: str, url_path: str) -> dict:
    """Check a single page for rendering issues. Returns stats dict."""
    global pages_checked
    html = fetch(url_path)
    if html is None:
        return {}

    pages_checked += 1
    stats = {"tables": 0, "raw_tables": 0, "sidebar": 0, "toc": 0, "broken_links": 0}
    page_id = filepath

    # 1. Check for raw markdown tables rendered as text (pipe chars outside <table> and <code> tags)
    # First strip all code blocks from the HTML to avoid false positives
    html_no_code = re.sub(r'<code[^>]*>.*?</code>', '', html, flags=re.DOTALL)
    html_no_code = re.sub(r'<pre[^>]*>.*?</pre>', '', html_no_code, flags=re.DOTALL)
    raw_table_lines = re.findall(r'(?<!</td>)\|\s*---', html_no_code)
    stats["raw_tables"] = len(raw_table_lines)
    if raw_table_lines:
        error(f"{page_id}: {len(raw_table_lines)} raw markdown table(s) not rendering as HTML")

    # 2. Check for raw markdown rendered as text (common patterns)
    raw_bold = len(re.findall(r'(?<!<code>)\*\*[^*]+\*\*(?!</code>)', html))
    # Only flag if there's a LOT of raw markdown (some ** in code blocks is fine)
    raw_headers = re.findall(r'(?<!</code>)(?<!<pre>)^#{1,6}\s+\w', html, re.MULTILINE)
    if raw_headers:
        warn(f"{page_id}: {len(raw_headers)} raw markdown headers found in HTML")

    # 3. Check HTML tables exist where expected
    stats["tables"] = len(re.findall(r'<table', html))

    # 4. Check sidebar navigation exists
    sidebar_links = re.findall(r'md-nav__link', html)
    stats["sidebar"] = len(sidebar_links)
    if len(sidebar_links) < 5:
        warn(f"{page_id}: Only {len(sidebar_links)} sidebar links (may be missing sidebar nav)")

    # 5. Check right-side TOC (table of contents) exists
    toc_items = re.findall(r'md-nav__link--active.*?class="md-nav__link"', html, re.DOTALL)
    toc_links = re.findall(r'class="md-nav__link"\s+href="#', html)
    stats["toc"] = len(toc_links)

    # 6. Check for broken internal links (404 anchors)
    internal_links = re.findall(r'href="(/kubedojo/[^"#]+)"', html)
    for link in internal_links[:20]:  # Sample first 20 to avoid hammering
        try:
            urllib.request.urlopen(f"http://127.0.0.1:8001{link}", timeout=5)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                stats["broken_links"] += 1
                error(f"{page_id}: Broken link in rendered HTML: {link}")
        except Exception:
            pass

    # 7. Check for empty content (page loaded but no real content)
    content_area = re.findall(r'class="md-content".*?</article>', html, re.DOTALL)
    if content_area:
        text_content = re.sub(r'<[^>]+>', '', content_area[0])
        if len(text_content.strip()) < 100:
            warn(f"{page_id}: Very little content ({len(text_content.strip())} chars)")

    # 8. Check for unresolved Jinja/template variables
    jinja_vars = re.findall(r'\{\{[^}]+\}\}', html)
    if jinja_vars:
        warn(f"{page_id}: {len(jinja_vars)} unresolved template variable(s)")

    return stats


def check_nav_consistency():
    """Check that the sidebar nav is consistent across pages in the same section."""
    print("\n2. Checking navigation consistency...")

    sections = {
        "CKA": "k8s/cka/",
        "CKAD": "k8s/ckad/",
        "CKS": "k8s/cks/",
        "KCNA": "k8s/kcna/",
        "Platform Foundations": "platform/foundations/systems-thinking/",
    }

    for name, prefix in sections.items():
        pages = get_all_pages()
        section_pages = [(f, u) for f, u in pages if f.startswith(prefix)][:3]

        nav_counts = []
        for filepath, url_path in section_pages:
            html = fetch(url_path)
            if html:
                count = len(re.findall(r'md-nav__link', html))
                nav_counts.append(count)

        if nav_counts and max(nav_counts) - min(nav_counts) > 50:
            warn(f"{name}: Inconsistent sidebar link counts across pages: {nav_counts}")
        elif nav_counts:
            print(f"  {name}: Sidebar consistent ({nav_counts[0]} links)")


def check_cert_landing_pages():
    """Check that certification landing pages have proper structure."""
    print("\n3. Checking certification landing pages...")

    certs = {
        "CNPE": "k8s/cnpe/",
        "CBA": "k8s/cba/",
        "OTCA": "k8s/otca/",
        "KCA": "k8s/kca/",
        "CAPA": "k8s/capa/",
        "CKA": "k8s/cka/",
        "CKAD": "k8s/ckad/",
        "CKS": "k8s/cks/",
        "KCNA": "k8s/kcna/",
        "KCSA": "k8s/kcsa/",
    }

    for name, path in certs.items():
        html = fetch(path)
        if not html:
            continue

        tables = len(re.findall(r'<table', html))
        raw_pipes = len(re.findall(r'\|\s*---', html))
        has_h1 = bool(re.search(r'<h1[^>]*>', html))
        has_h2 = len(re.findall(r'<h2[^>]*>', html))

        issues = []
        if raw_pipes > 0:
            issues.append(f"{raw_pipes} raw tables")
        if not has_h1:
            issues.append("missing H1")
        if has_h2 < 2:
            issues.append(f"only {has_h2} H2 sections")
        if tables == 0 and "README" not in path:
            issues.append("no HTML tables")

        if issues:
            warn(f"{name} ({path}): {', '.join(issues)}")
        else:
            print(f"  {name}: OK ({tables} tables, {has_h2} sections)")


def main():
    print("=" * 60)
    print("KubeDojo Site Render Check")
    print(f"Server: {BASE_URL}")
    print("=" * 60)

    # Quick connectivity test
    print("\n0. Testing server connectivity...")
    html = fetch("")
    if html is None:
        print("\nServer not reachable. Start it with: bash start-docs.sh")
        sys.exit(1)
    print("  Server is up")

    # 1. Sample render check across all sections
    print("\n1. Checking page rendering (sampling across all tracks)...")
    all_pages = get_all_pages()

    # Sample: first and last page of each major section
    sampled = set()
    sections_seen = set()
    for filepath, url_path in all_pages:
        section = filepath.split("/")[0] if "/" in filepath else "root"
        subsection = "/".join(filepath.split("/")[:2]) if filepath.count("/") > 1 else section
        key = subsection

        if key not in sections_seen:
            sections_seen.add(key)
            sampled.add((filepath, url_path))

    # Also add the last page of each section
    last_by_section = {}
    for filepath, url_path in all_pages:
        subsection = "/".join(filepath.split("/")[:2]) if filepath.count("/") > 1 else filepath.split("/")[0]
        last_by_section[subsection] = (filepath, url_path)
    for fp, up in last_by_section.values():
        sampled.add((fp, up))

    total_raw_tables = 0
    total_broken = 0
    for filepath, url_path in sorted(sampled):
        stats = check_page_renders(filepath, url_path)
        total_raw_tables += stats.get("raw_tables", 0)
        total_broken += stats.get("broken_links", 0)

    print(f"  Checked {pages_checked} pages, {total_raw_tables} raw table issues, {total_broken} broken links")

    # 2. Nav consistency
    check_nav_consistency()

    # 3. Cert landing pages
    check_cert_landing_pages()

    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {len(errors)} errors, {len(warnings)} warnings")
    print(f"Pages checked: {pages_checked}")
    print("=" * 60)

    if errors:
        print("\nERRORS (must fix):")
        for e in errors:
            print(f"  - {e}")

    if warnings:
        print("\nWARNINGS:")
        for w in warnings[:20]:
            print(f"  - {w}")
        if len(warnings) > 20:
            print(f"  ... and {len(warnings) - 20} more")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
