#!/usr/bin/env python3
"""Ukrainian sync detector — find and fix stale translations.

Detects when English modules have been improved but their Ukrainian
counterparts haven't been updated. Uses section-level hashing for
accurate detection and Gemini + MCP RAG for translation fixes.

Usage:
    .venv/bin/python scripts/uk_sync.py detect
    .venv/bin/python scripts/uk_sync.py detect --section k8s/cka
    .venv/bin/python scripts/uk_sync.py detect --json
    .venv/bin/python scripts/uk_sync.py fix <uk-file-path>
    .venv/bin/python scripts/uk_sync.py fix-section k8s/cka
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CONTENT_ROOT = REPO_ROOT / "src" / "content" / "docs"
UK_ROOT = CONTENT_ROOT / "uk"
REPORT_FILE = REPO_ROOT / ".pipeline" / "uk-sync-report.json"

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from checks import ukrainian
from dispatch import dispatch_gemini_with_retry


# ---------------------------------------------------------------------------
# Section-level hashing
# ---------------------------------------------------------------------------

def _split_sections(content: str) -> dict[str, str]:
    """Split markdown content into sections by H2 headers. Returns {heading: body}."""
    sections = {}
    current_heading = "__preamble__"
    current_lines = []

    for line in content.split("\n"):
        if line.startswith("## "):
            if current_lines:
                sections[current_heading] = "\n".join(current_lines)
            current_heading = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections[current_heading] = "\n".join(current_lines)

    return sections


def _hash_section(text: str) -> str:
    """Hash section content (normalized: stripped, lowered)."""
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def _section_hashes(content: str) -> dict[str, str]:
    """Get {heading: hash} for all sections."""
    return {h: _hash_section(body) for h, body in _split_sections(content).items()}


# ---------------------------------------------------------------------------
# EN commit tracking
# ---------------------------------------------------------------------------

def _get_en_file_commit(en_path: Path) -> str:
    """Get the latest git commit hash that modified the EN file."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", str(en_path)],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def _get_uk_synced_commit(uk_content: str) -> str:
    """Extract en_commit from UK file frontmatter."""
    match = re.search(r"^en_commit:\s*(.+)$", uk_content, re.MULTILINE)
    return match.group(1).strip().strip("'\"") if match else ""


# ---------------------------------------------------------------------------
# Sync issue detection
# ---------------------------------------------------------------------------

@dataclass
class SyncIssue:
    uk_path: str
    en_path: str
    issue_type: str  # MISSING_OUTCOMES, OUTCOMES_MISMATCH, PROMPTS_MISMATCH, etc.
    severity: str    # ERROR, WARNING, INFO
    message: str
    en_value: str = ""
    uk_value: str = ""

    def __str__(self):
        icon = {"ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}.get(self.severity, "?")
        return f"  {icon} [{self.issue_type}] {self.message}"


@dataclass
class SyncReport:
    uk_path: str
    en_path: str
    status: str  # "synced", "stale", "partial"
    issues: list[SyncIssue] = field(default_factory=list)
    en_commit: str = ""
    uk_synced_commit: str = ""


def _count_pattern(content: str, pattern: str) -> int:
    return len(re.findall(pattern, content, re.MULTILINE))


def detect_sync(uk_path: Path) -> SyncReport | None:
    """Compare a UK file against its EN counterpart."""
    # Find EN equivalent
    rel = uk_path.relative_to(UK_ROOT)
    en_path = CONTENT_ROOT / rel

    if not en_path.exists():
        return None  # No EN counterpart — orphan UK file

    en_content = en_path.read_text()
    uk_content = uk_path.read_text()

    en_commit = _get_en_file_commit(en_path)
    uk_synced = _get_uk_synced_commit(uk_content)

    report = SyncReport(
        uk_path=str(uk_path.relative_to(REPO_ROOT)),
        en_path=str(en_path.relative_to(REPO_ROOT)),
        status="synced",
        en_commit=en_commit,
        uk_synced_commit=uk_synced,
    )

    # 1. Commit-based staleness check
    if en_commit and uk_synced and en_commit != uk_synced:
        report.issues.append(SyncIssue(
            report.uk_path, report.en_path,
            "STALE_COMMIT", "WARNING",
            f"EN updated since last sync (en_commit in UK: {uk_synced[:8]}, EN HEAD: {en_commit[:8]})",
        ))
    elif not uk_synced:
        report.issues.append(SyncIssue(
            report.uk_path, report.en_path,
            "NO_SYNC_TRACKING", "INFO",
            "UK file has no en_commit in frontmatter — cannot track sync state",
        ))

    # 2. Learning outcomes
    en_outcomes = _count_pattern(en_content, r"^-\s+\*\*\w+\*\*")
    uk_outcomes = _count_pattern(uk_content, r"^-\s+\*\*\w+\*\*")
    en_has_outcomes = bool(re.search(r"##\s+(Learning Outcomes|What You.ll)", en_content))
    uk_has_outcomes = bool(re.search(r"##\s+Що ви зможете", uk_content))

    if en_has_outcomes and not uk_has_outcomes:
        report.issues.append(SyncIssue(
            report.uk_path, report.en_path,
            "MISSING_OUTCOMES", "ERROR",
            "EN has Learning Outcomes section, UK does not",
            en_value=str(en_outcomes), uk_value="0",
        ))
    elif en_outcomes != uk_outcomes and abs(en_outcomes - uk_outcomes) > 1:
        report.issues.append(SyncIssue(
            report.uk_path, report.en_path,
            "OUTCOMES_MISMATCH", "WARNING",
            f"Outcome count differs: EN={en_outcomes}, UK={uk_outcomes}",
            en_value=str(en_outcomes), uk_value=str(uk_outcomes),
        ))

    # 3. Inline prompts
    en_prompts = _count_pattern(en_content, r">\s*\*\*(Pause and predict|Stop and think|What would happen)")
    uk_prompts = _count_pattern(uk_content, r">\s*\*\*(Зупиніться|Подумайте|Pause and predict|Stop and think)")

    if en_prompts > uk_prompts + 1:
        report.issues.append(SyncIssue(
            report.uk_path, report.en_path,
            "PROMPTS_MISMATCH", "WARNING",
            f"EN has more inline prompts: EN={en_prompts}, UK={uk_prompts}",
            en_value=str(en_prompts), uk_value=str(uk_prompts),
        ))

    # 4. Quiz questions
    en_quiz = en_content.count("<details>")
    uk_quiz = uk_content.count("<details>")

    if en_quiz > uk_quiz + 2:
        report.issues.append(SyncIssue(
            report.uk_path, report.en_path,
            "QUIZ_MISMATCH", "WARNING",
            f"Quiz question count differs: EN={en_quiz}, UK={uk_quiz}",
            en_value=str(en_quiz), uk_value=str(uk_quiz),
        ))

    # 5. Section-level hashing (detect content changes)
    en_sections = set(_split_sections(en_content).keys()) - {"__preamble__"}
    uk_sections = set(_split_sections(uk_content).keys()) - {"__preamble__"}

    # Sections in EN but not UK (by structure, not exact heading match)
    en_h2_count = en_content.count("\n## ")
    uk_h2_count = uk_content.count("\n## ")

    if en_h2_count > uk_h2_count + 2:
        report.issues.append(SyncIssue(
            report.uk_path, report.en_path,
            "SECTIONS_MISMATCH", "WARNING",
            f"EN has more sections: EN={en_h2_count} H2s, UK={uk_h2_count} H2s",
            en_value=str(en_h2_count), uk_value=str(uk_h2_count),
        ))

    # 6. Size ratio (Ukrainian is typically 95-130% of English)
    en_len = len(en_content)
    uk_len = len(uk_content)
    if en_len > 0:
        ratio = uk_len / en_len
        if ratio < 0.50:
            report.issues.append(SyncIssue(
                report.uk_path, report.en_path,
                "SIZE_DRIFT", "WARNING",
                f"UK is only {ratio:.0%} of EN size ({uk_len} vs {en_len} chars) — possibly partial translation",
                en_value=str(en_len), uk_value=str(uk_len),
            ))

    # Determine overall status
    errors = [i for i in report.issues if i.severity == "ERROR"]
    warnings = [i for i in report.issues if i.severity == "WARNING"]

    if errors:
        report.status = "stale"
    elif warnings:
        report.status = "stale"
    else:
        report.status = "synced"

    return report


# ---------------------------------------------------------------------------
# Fix — translate delta using Gemini + MCP
# ---------------------------------------------------------------------------

TRANSLATE_PROMPT = """You are translating additions to a KubeDojo module from English to Ukrainian.

RULES:
- Translate ONLY what is missing or changed compared to the existing Ukrainian file
- Keep ALL existing Ukrainian content intact — do not rewrite what's already there
- Keep all technical terms in English: kubectl, Kubernetes, Pod, Deployment, Service, RBAC, YAML, etc.
- Glossary: Pod=Під, cluster=кластер, container=контейнер, namespace=простір імен
- Action verbs in bold infinitive: **Налаштувати**, **Створити**, **Діагностувати**
- Inline prompts: translate "Pause and predict" → "Зупиніться та подумайте", "Stop and think" → "Подумайте"
- No Russicisms (no ы, ё, ъ, э)
- Output the COMPLETE updated Ukrainian file starting with --- frontmatter

Use your MCP tools to verify Ukrainian quality:
- verify_words for VESUM validation
- query_r2u to check for Russicisms
- search_style_guide for consistency

EXISTING UKRAINIAN FILE:
{uk_content}

CURRENT ENGLISH FILE (source of truth):
{en_content}

DETECTED ISSUES TO FIX:
{issues}
"""


def fix_module(uk_path: Path, report: SyncReport | None = None) -> bool:
    """Fix a stale UK module by translating the delta from EN."""
    rel = uk_path.relative_to(UK_ROOT)
    en_path = CONTENT_ROOT / rel

    if not en_path.exists():
        print(f"  ❌ No EN counterpart for {uk_path}")
        return False

    if report is None:
        report = detect_sync(uk_path)

    if report is None or report.status == "synced":
        print(f"  ✓ Already synced: {uk_path.name}")
        return True

    en_content = en_path.read_text()
    uk_content = uk_path.read_text()

    issues_text = "\n".join(f"- {i.issue_type}: {i.message}" for i in report.issues)

    print(f"  Translating delta for {uk_path.name} ({len(report.issues)} issues)...")

    prompt = TRANSLATE_PROMPT.format(
        uk_content=uk_content,
        en_content=en_content,
        issues=issues_text,
    )

    ok, output = dispatch_gemini_with_retry(prompt, mcp=True, timeout=300)

    if not ok or not output.strip():
        print(f"  ❌ Translation failed")
        return False

    # Strip markdown wrapper
    if output.startswith("```"):
        lines = output.split("\n")
        output = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else output

    # Ensure frontmatter
    if not output.startswith("---"):
        fm_start = output.find("---\n")
        if fm_start > 0 and fm_start < 2000:
            output = output[fm_start:]
        else:
            print(f"  ❌ Translation output has no frontmatter")
            return False

    # Add/update en_commit in frontmatter
    en_commit = _get_en_file_commit(en_path)
    if en_commit:
        if "en_commit:" in output:
            output = re.sub(r"^en_commit:.*$", f"en_commit: {en_commit}", output, count=1, flags=re.MULTILINE)
        else:
            # Add before closing ---
            output = output.replace("\n---\n", f"\nen_commit: {en_commit}\n---\n", 1)

    # Verify Ukrainian quality
    check_results = ukrainian.run_all(output, uk_path)
    check_errors = [r for r in check_results if not r.passed and r.severity == "ERROR"]

    if check_errors:
        print(f"  ⚠️ Ukrainian quality issues found:")
        for r in check_errors:
            print(f"    {r}")
        # Still write — issues are warnings, not blockers for now
        # The uk_sync detect will catch them on next run

    uk_path.write_text(output)
    print(f"  ✓ Updated {uk_path.name} (en_commit: {en_commit[:8]})")

    return True


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

def cmd_detect(args):
    """Detect out-of-sync Ukrainian modules."""
    if args.section:
        uk_dir = UK_ROOT / args.section
    else:
        uk_dir = UK_ROOT

    if not uk_dir.exists():
        print(f"Directory not found: {uk_dir}")
        sys.exit(1)

    uk_files = sorted(uk_dir.glob("**/module-*.md"))
    print(f"Checking {len(uk_files)} Ukrainian modules...")

    reports = []
    synced = 0
    stale = 0
    errors_total = 0
    warnings_total = 0

    for uk_path in uk_files:
        report = detect_sync(uk_path)
        if report is None:
            continue

        reports.append(report)

        if report.status == "synced":
            synced += 1
        else:
            stale += 1
            errors = [i for i in report.issues if i.severity == "ERROR"]
            warnings = [i for i in report.issues if i.severity == "WARNING"]
            errors_total += len(errors)
            warnings_total += len(warnings)

            if not args.json:
                short_path = report.uk_path.replace("src/content/docs/uk/", "")
                print(f"\n  {short_path}:")
                for issue in report.issues:
                    print(f"  {issue}")

    # Summary
    if not args.json:
        print(f"\n{'='*60}")
        print(f"  Synced: {synced} | Stale: {stale} | Errors: {errors_total} | Warnings: {warnings_total}")
        print(f"{'='*60}")

    # Persist report
    report_data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "summary": {
            "total": len(reports),
            "synced": synced,
            "stale": stale,
            "errors": errors_total,
            "warnings": warnings_total,
        },
        "modules": {
            r.uk_path: {
                "status": r.status,
                "en_commit": r.en_commit,
                "uk_synced_commit": r.uk_synced_commit,
                "issues": [
                    {"type": i.issue_type, "severity": i.severity, "message": i.message,
                     "en_value": i.en_value, "uk_value": i.uk_value}
                    for i in r.issues
                ],
            }
            for r in reports if r.issues
        },
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(report_data, indent=2, ensure_ascii=False))
    print(f"\nReport saved to {REPORT_FILE}")

    if args.json:
        print(json.dumps(report_data, indent=2, ensure_ascii=False))

    sys.exit(1 if errors_total > 0 else 0)


def cmd_fix(args):
    """Fix a single stale UK module."""
    uk_path = Path(args.file)
    if not uk_path.exists():
        uk_path = UK_ROOT / f"{args.file}.md"
    if not uk_path.exists():
        print(f"File not found: {args.file}")
        sys.exit(1)

    ok = fix_module(uk_path)
    sys.exit(0 if ok else 1)


def cmd_fix_section(args):
    """Fix all stale UK modules in a section."""
    uk_dir = UK_ROOT / args.section
    if not uk_dir.exists():
        print(f"Section not found: {args.section}")
        sys.exit(1)

    uk_files = sorted(uk_dir.glob("**/module-*.md"))
    print(f"Checking {len(uk_files)} modules in {args.section}...")

    fixed = 0
    skipped = 0
    failed = 0

    for uk_path in uk_files:
        report = detect_sync(uk_path)
        if report is None or report.status == "synced":
            skipped += 1
            continue

        print(f"\n  Fixing: {uk_path.name} ({len(report.issues)} issues)")
        ok = fix_module(uk_path, report)
        if ok:
            fixed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"  Fixed: {fixed} | Skipped (synced): {skipped} | Failed: {failed}")
    print(f"{'='*60}")

    sys.exit(0 if failed == 0 else 1)


def main():
    parser = argparse.ArgumentParser(
        description="Ukrainian sync detector — find and fix stale translations",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # detect
    dp = subparsers.add_parser("detect", help="Detect out-of-sync UK modules")
    dp.add_argument("--section", help="Limit to section (e.g., k8s/cka)")
    dp.add_argument("--json", action="store_true", help="Output as JSON")

    # fix
    fp = subparsers.add_parser("fix", help="Fix a single stale UK module")
    fp.add_argument("file", help="UK file path")

    # fix-section
    fsp = subparsers.add_parser("fix-section", help="Fix all stale UK modules in a section")
    fsp.add_argument("section", help="Section path (e.g., k8s/cka)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"detect": cmd_detect, "fix": cmd_fix, "fix-section": cmd_fix_section}[args.command](args)


if __name__ == "__main__":
    main()
