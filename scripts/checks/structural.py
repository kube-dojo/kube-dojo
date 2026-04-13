"""Structural checks — frontmatter, sections, line count, code blocks, K8s versions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    check: str
    passed: bool
    message: str
    severity: str = "ERROR"  # ERROR, WARNING, INFO

    def __str__(self):
        icon = "✓" if self.passed else "✗" if self.severity == "ERROR" else "⚠"
        return f"  {icon} [{self.check}] {self.message}"


def check_frontmatter(content: str, path: Path) -> list[CheckResult]:
    """Check that required frontmatter fields exist."""
    results = []

    if not content.startswith("---"):
        results.append(CheckResult("FRONTMATTER", False, "No frontmatter found"))
        return results

    end = content.find("---", 3)
    if end == -1:
        results.append(CheckResult("FRONTMATTER", False, "Frontmatter not closed"))
        return results

    fm = content[3:end]

    if "title:" not in fm:
        results.append(CheckResult("FRONTMATTER", False, "Missing title:"))
    else:
        results.append(CheckResult("FRONTMATTER", True, "title: present"))

    if "sidebar:" not in fm:
        results.append(CheckResult("FRONTMATTER", False, "Missing sidebar:", "WARNING"))

    # Check for slug if filename has dots (Astro requirement)
    if "." in path.stem and path.stem.count(".") > 0:
        if "slug:" not in fm:
            results.append(CheckResult("FRONTMATTER", False,
                                       f"Filename has dots ({path.stem}) but no slug: field",
                                       "WARNING"))

    return results


def check_required_sections(content: str) -> list[CheckResult]:
    """Check that required module sections exist."""
    results = []
    body = content.split("---", 2)[-1] if content.startswith("---") else content

    checks = [
        ("SECTION_OUTCOMES", r"##\s+(Learning Outcomes|What You.ll|Що ви зможете)",
         "Learning Outcomes section"),
        ("SECTION_QUIZ", r"##\s+(Quiz|Knowledge Check|Тест|Контрольні запитання)",
         "Quiz section"),
    ]

    for check_id, pattern, label in checks:
        found = bool(re.search(pattern, body))
        results.append(CheckResult(check_id, found, f"{label}: {'found' if found else 'MISSING'}"))

    # Inline prompts (at least 2)
    prompt_pattern = r">\s*\*\*(Pause and predict|Stop and think|What would happen|Try it yourself|Before you look|Active Learning|Try this now|Before running|Think about this|Зупиніться|Подумайте)"
    prompts = re.findall(prompt_pattern, body)
    count = len(prompts)
    passed = count >= 2
    results.append(CheckResult("INLINE_PROMPTS", passed,
                               f"Inline active learning prompts: {count} found (need >= 2)"))

    # Quiz uses <details> (scenario-based format)
    details_count = body.count("<details>")
    passed = details_count >= 4
    results.append(CheckResult("QUIZ_FORMAT", passed,
                               f"Quiz <details> blocks: {details_count} (need >= 4)"))

    # Quiz answer depth: answers should be 3-5 sentences (not one-liners)
    quiz_blocks = re.findall(r"<details>\s*<summary>.*?</summary>([\s\S]*?)</details>", body)
    if quiz_blocks:
        shallow = 0
        for answer in quiz_blocks:
            # Strip code blocks from answer before counting
            text = re.sub(r"```[\s\S]*?```", "", answer).strip()
            word_count = len(text.split())
            if word_count < 20:  # ~2 sentences minimum
                shallow += 1
        passed = shallow == 0
        results.append(CheckResult("QUIZ_DEPTH", passed,
                                   f"Quiz answers too shallow: {shallow}/{len(quiz_blocks)} have < 20 words"
                                   if shallow else f"All {len(quiz_blocks)} quiz answers have adequate depth",
                                   severity="WARNING"))

    return results


def check_content_lines(content: str, path: Path | None = None) -> list[CheckResult]:
    """Check content line count (excluding code blocks and frontmatter)."""
    # Remove frontmatter
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        body = parts[2] if len(parts) > 2 else ""

    # Remove code blocks
    body_no_code = re.sub(r"```[\s\S]*?```", "", body)

    lines = [l for l in body_no_code.strip().split("\n") if l.strip()]
    count = len(lines)

    # Track-aware thresholds
    threshold = 250
    path_str = str(path) if path else ""
    if "prerequisites" in path_str or "zero-to-terminal" in path_str:
        threshold = 100  # Beginner modules are intentionally shorter
    elif "linux" in path_str:
        threshold = 150  # Linux practical modules — command-heavy, less prose
    elif "kcna" in path_str:
        threshold = 150  # Associate-level theory modules

    passed = count >= threshold
    return [CheckResult("LINE_COUNT", passed,
                        f"Content lines (excl. code blocks): {count} (threshold: {threshold})",
                        severity="WARNING")]  # Demoted — LLM scoring catches thin content


def check_code_blocks(content: str) -> list[CheckResult]:
    """Check that code blocks have language specifiers."""
    results = []
    bare_blocks = re.findall(r"^```\s*$", content, re.MULTILINE)
    count = len(bare_blocks)
    passed = count == 0
    results.append(CheckResult("CODE_LANG", passed,
                               f"Code blocks without language: {count}" if count > 0 else
                               "All code blocks have language specifiers",
                               severity="WARNING"))  # Demoted — pre-existing in many modules
    return results


def check_no_emojis(content: str) -> list[CheckResult]:
    """Check for emoji usage (not allowed in KubeDojo)."""
    # Strip code blocks first — checkmarks etc. inside code are fine
    content_no_code = re.sub(r"```[\s\S]*?```", "", content)

    # Common emoji ranges (excludes technical symbols like ✓ ✗ → ←)
    emoji_pattern = re.compile(
        "[\U0001F300-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]"
    )
    matches = emoji_pattern.findall(content_no_code)
    passed = len(matches) == 0
    return [CheckResult("NO_EMOJI", passed,
                        f"Emojis found: {len(matches)}" if matches else
                        "No emojis")]


def check_k8s_versions(content: str) -> list[CheckResult]:
    """Check for deprecated K8s API versions outside code blocks.

    Modules about API deprecations/upgrades legitimately reference old APIs
    in code blocks, inline code, tables, and prose as teaching examples.
    Demoted to WARNING — the LLM scoring catches real misuse.
    """
    results = []

    # Strip fenced code blocks and inline code
    stripped = re.sub(r"```[\s\S]*?```", "", content)
    stripped = re.sub(r"`[^`]+`", "", stripped)

    # Deprecated API versions
    deprecated = [
        (r"extensions/v1beta1", "extensions/v1beta1 — removed in K8s 1.22"),
        (r"apps/v1beta[12]", "apps/v1beta — removed in K8s 1.16"),
        (r"networking\.k8s\.io/v1beta1", "networking.k8s.io/v1beta1 — check if still valid"),
        (r"policy/v1beta1", "policy/v1beta1 — removed in K8s 1.25"),
        (r"rbac\.authorization\.k8s\.io/v1beta1", "rbac v1beta1 — removed in K8s 1.22"),
        (r"apiextensions\.k8s\.io/v1beta1", "CRD v1beta1 — removed in K8s 1.22"),
    ]

    for pattern, msg in deprecated:
        if re.search(pattern, stripped):
            results.append(CheckResult("K8S_API", False, f"Deprecated API: {msg}",
                                       severity="WARNING"))

    if not results:
        results.append(CheckResult("K8S_API", True, "No deprecated K8s APIs found"))

    return results


def check_leaked_secrets(content: str) -> list[CheckResult]:
    """Detect realistic-looking secrets that would trigger GitHub push protection."""
    # Strip fenced code blocks — we still check them because GitHub scans everything
    patterns = [
        (r"https://hooks\.slack\.com/services/T[A-Z0-9]{8,}/B[A-Z0-9]{8,}/[A-Za-z0-9]{20,}",
         "Slack webhook URL (use https://hooks.slack.com/services/YOUR/WEBHOOK/HERE)"),
        (r"xox[bpors]-[0-9]{10,}-[0-9]{10,}-[A-Za-z0-9]{20,}",
         "Slack API token (use xoxb-your-token-here)"),
        (r"AKIA[0-9A-Z]{16}",
         "AWS access key (use AKIAIOSFODNN7EXAMPLE)"),
        (r"ghp_[A-Za-z0-9]{36}",
         "GitHub personal access token (use ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)"),
        (r"gho_[A-Za-z0-9]{36}",
         "GitHub OAuth token"),
        (r"github_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59}",
         "GitHub fine-grained PAT"),
        (r"sk-[A-Za-z0-9]{48}",
         "OpenAI API key (use sk-your-key-here)"),
        (r"AIza[0-9A-Za-z_-]{35}",
         "Google API key (use AIzaSyYOUR_KEY_HERE)"),
    ]

    results = []
    for pattern, msg in patterns:
        matches = re.findall(pattern, content)
        if matches:
            results.append(CheckResult("LEAKED_SECRET", False,
                                       f"Potential secret detected: {msg}"))
    if not results:
        results.append(CheckResult("LEAKED_SECRET", True, "No leaked secrets detected"))
    return results


def run_all(content: str, path: Path) -> list[CheckResult]:
    """Run all structural checks."""
    results = []
    results.extend(check_frontmatter(content, path))
    results.extend(check_required_sections(content))
    results.extend(check_content_lines(content, path))
    results.extend(check_code_blocks(content))
    results.extend(check_no_emojis(content))
    results.extend(check_k8s_versions(content))
    results.extend(check_leaked_secrets(content))
    return results
