#!/usr/bin/env python3
"""Deterministic #388 curriculum module verifier."""
from __future__ import annotations

import argparse
import concurrent.futures
import glob as globlib
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

_HERE = str(Path(__file__).resolve().parent)
sys.path = [p for p in sys.path if p not in ("", _HERE)]

REPO_ROOT = Path(__file__).resolve().parents[2]

WORD_RE = re.compile(r"(?=\S*[A-Za-z0-9])\S+")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
MD_LINK_RE = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)")
BARE_URL_RE = re.compile(r"(?<![(\[])\bhttps?://[^\s)<>\]]+")
LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
FORBIDDEN_TOKENS = [
    "TBD",
    "TODO",
    "FIXME",
    "XXX",
    "lorem ipsum",
    "as an AI",
    "I cannot",
    "I'm sorry",
    "as a large language model",
    "###  ",
    "[INSERT",
    "[REPLACE",
    "<placeholder>",
]
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "using",
    "use",
    "module",
    "learn",
    "explain",
    "describe",
    "identify",
    "implement",
    "configure",
    "debug",
    "troubleshoot",
    "compare",
}
KUBECTL_COMMAND_RE = re.compile(
    r"\bk\s+(?:get|apply|delete|describe|logs|exec|create|edit|scale|rollout|"
    r"config|cluster-info|version|auth|top|cordon|drain|taint|label|annotate)\b",
    re.IGNORECASE,
)
ALIAS_RE = re.compile(r"\balias\s+k=(?:kubectl|'kubectl'|\"kubectl\")\b", re.IGNORECASE)

LEARNING_OUTCOME_HEADINGS = (
    "Learning Outcomes",
    "Learning Objectives",
    "What You'll Be Able to Do",
    "What You'll Learn",
    "What You Will Learn",
)
DID_YOU_KNOW_HEADINGS = ("Did You Know", "Did You Know?")
COMMON_MISTAKES_PREFIX_HEADINGS = ("Common Mistakes",)
QUIZ_HEADINGS = ("Knowledge Check",)
QUIZ_PREFIX_HEADINGS = ("Quiz",)
HANDS_ON_HEADINGS = ("Lab", "Exercise", "Hands-On Practice", "Hands-On Practical Exercises")
HANDS_ON_PREFIX_HEADINGS = ("Hands-On",)
SOURCES_HEADINGS = ("Sources", "Further Reading", "References", "Resources")

try:
    import regex as _regex  # type: ignore

    EMOJI_RE = _regex.compile(r"\p{Emoji_Presentation}|\p{Extended_Pictographic}")
except ImportError:
    EMOJI_RE = re.compile(r"[\U0001f300-\U0001faff\u2600-\u27bf]")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)(.*)\Z", text, re.DOTALL)
    if not match:
        return {}, text
    frontmatter: dict[str, object] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip("\"'")
        lowered = value.lower()
        if lowered == "true":
            parsed: object = True
        elif lowered == "false":
            parsed = False
        elif re.fullmatch(r"-?\d+", value):
            parsed = int(value)
        else:
            parsed = value
        frontmatter[key.strip()] = parsed
    return frontmatter, match.group(2)


def _strip_code_blocks(text: str, replacement: str = "") -> str:
    return re.sub(r"```.*?```", replacement, text, flags=re.DOTALL)


def _word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def _line_has_diagram_chars(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    diagram_chars = sum(1 for char in stripped if char in "|+-─│┌└┐┘┬┴┼")
    return diagram_chars >= max(2, len(stripped) // 5)


def _ascii_diagram_line_indexes(lines: list[str]) -> set[int]:
    indexes: set[int] = set()
    start: int | None = None
    hits = 0
    total = 0
    for idx, line in enumerate(lines + [""]):
        if line.strip():
            if start is None:
                start = idx
                hits = 0
                total = 0
            total += 1
            if _line_has_diagram_chars(line):
                hits += 1
            continue
        if start is not None:
            if total >= 2 and hits / total > 0.5:
                indexes.update(range(start, idx))
            start = None
    return indexes


def extract_body_paragraphs(text: str) -> list[str]:
    """Return canonical body teaching paragraphs for density metrics."""
    _, body = _strip_frontmatter(text)
    lines = body.splitlines()
    ascii_indexes = _ascii_diagram_line_indexes(lines)
    kept: list[str] = []
    in_fence = False
    in_html: str | None = None
    in_sources = False
    in_list = False
    in_table = False
    seen_heading = False

    for idx, line in enumerate(lines):
        stripped = line.strip()
        lower = stripped.lower()

        if stripped.startswith("```"):
            in_fence = not in_fence
            kept.append("")
            continue
        if in_fence:
            kept.append("")
            continue

        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", stripped)
        if heading:
            seen_heading = True
        if heading and len(heading.group(1)) <= 2:
            in_sources = _heading_matches(heading.group(2), SOURCES_HEADINGS)
        if in_sources:
            kept.append("")
            continue

        if not seen_heading and stripped.startswith(">"):
            kept.append("")
            continue
        if in_html:
            if f"</{in_html}" in lower:
                in_html = None
            kept.append("")
            continue
        html_open = re.match(r"^<([a-zA-Z][\w:-]*)\b", stripped)
        if html_open:
            tag = html_open.group(1).lower()
            if not re.search(rf"</{re.escape(tag)}\s*>", lower):
                in_html = tag
            kept.append("")
            continue

        if not stripped:
            in_list = False
            in_table = False
            kept.append("")
            continue
        if re.fullmatch(r"-{3,}", stripped):
            kept.append("")
            continue

        if idx in ascii_indexes:
            kept.append("")
            continue
        if heading:
            kept.append("")
            continue

        next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
        if TABLE_SEPARATOR_RE.match(stripped) or (
            "|" in stripped and TABLE_SEPARATOR_RE.match(next_line.strip())
        ):
            in_table = True
            kept.append("")
            continue
        if in_table and "|" in stripped:
            kept.append("")
            continue
        if in_table and "|" not in stripped:
            in_table = False

        if LIST_RE.match(line):
            in_list = True
            kept.append("")
            continue
        if in_list and (line.startswith((" ", "\t")) or not stripped):
            kept.append("")
            continue
        in_list = False

        kept.append(line)

    paragraphs: list[str] = []
    current: list[str] = []
    for line in kept:
        if line.strip():
            current.append(line.strip())
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def _sentence_lengths(paragraphs: list[str]) -> list[int]:
    prose = " ".join(paragraphs)
    parts = re.split(r"[.!?]+(?=\s+[A-Z]|\s*$)", prose)
    return [count for part in parts if (count := _word_count(part)) >= 3]


def density_metrics(text: str) -> dict[str, float | int]:
    paragraphs = extract_body_paragraphs(text)
    counts = [_word_count(paragraph) for paragraph in paragraphs]
    sentence_counts = _sentence_lengths(paragraphs)
    short_flags = [count < 18 for count in counts]
    max_run = 0
    current = 0
    for is_short in short_flags:
        current = current + 1 if is_short else 0
        max_run = max(max_run, current)
    return {
        "body_words": sum(counts),
        "paragraph_count": len(counts),
        "mean_wpp": round(statistics.mean(counts), 1) if counts else 0.0,
        "median_wpp": statistics.median(counts) if counts else 0,
        "short_paragraph_rate": round((sum(short_flags) / len(counts)) if counts else 0.0, 3),
        "max_consecutive_short_run": max_run,
        "mean_sentence_length": round(statistics.mean(sentence_counts), 1) if sentence_counts else 0.0,
        "sentence_count": len(sentence_counts),
    }


def _sections(body: str) -> list[dict[str, object]]:
    matches = _markdown_heading_matches(body)
    sections: list[dict[str, object]] = []
    for idx, match in enumerate(matches):
        level = len(match.group(1))
        start = match.end()
        end = len(body)
        for next_match in matches[idx + 1 :]:
            if len(next_match.group(1)) <= level:
                end = next_match.start()
                break
        sections.append(
            {
                "level": level,
                "title": match.group(2).strip(),
                "start": match.start(),
                "content": body[start:end],
            }
        )
    return sections


def _markdown_heading_matches(body: str) -> list[re.Match[str]]:
    matches: list[re.Match[str]] = []
    in_fence = False
    offset = 0
    for line in body.splitlines(keepends=True):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            offset += len(line)
            continue
        if not in_fence:
            match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.rstrip("\n"))
            if match:
                matches.append(HEADING_RE.match(body, offset))  # type: ignore[arg-type]
        offset += len(line)
    return [match for match in matches if match is not None]


def _heading_title(line: str) -> str:
    match = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)
    title = match.group(1) if match else line
    return re.sub(r"\s+#+\s*$", "", title).strip()


def _heading_matches(line: str, candidates: Iterable[str], prefix: bool = False) -> bool:
    title = _heading_title(line).casefold()
    for candidate in candidates:
        expected = candidate.casefold()
        if title == expected or title.startswith(f"{expected}:"):
            return True
        if prefix and (title.startswith(f"{expected} ") or title.startswith(f"{expected}:")):
            return True
    return False


def _find_h2(body: str, pattern: str) -> dict[str, object] | None:
    regex = re.compile(pattern, re.IGNORECASE)
    for section in _sections(body):
        if section["level"] == 2 and regex.search(str(section["title"])):
            return section
    return None


def _find_matching_h2(body: str, candidates: Iterable[str], prefix: bool = False) -> dict[str, object] | None:
    for section in _sections(body):
        if section["level"] == 2 and _heading_matches(str(section["title"]), candidates, prefix):
            return section
    return None


def _count_bullets(section: dict[str, object] | None) -> int:
    if not section:
        return 0
    return sum(
        1
        for line in str(section["content"]).splitlines()
        if re.match(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)", line)
    )


def _common_mistakes_rows(section: dict[str, object] | None) -> int:
    if not section:
        return 0
    rows = [line.strip() for line in str(section["content"]).splitlines() if line.strip().startswith("|")]
    data_rows = 0
    seen_separator = False
    for row in rows:
        if TABLE_SEPARATOR_RE.match(row):
            seen_separator = True
            continue
        if seen_separator:
            data_rows += 1
    return data_rows


def _quiz_items(section: dict[str, object] | None) -> list[tuple[str, str]]:
    if not section:
        return []
    content = str(section["content"])
    details = list(
        re.finditer(
            r"<details\b[^>]*>\s*<summary>(.*?)</summary>(.*?)</details>",
            content,
            re.IGNORECASE | re.DOTALL,
        )
    )
    if details:
        return [
            (re.sub(r"\s+", " ", match.group(1)).strip(), f"<details>{match.group(2)}</details>")
            for match in details
        ]
    matches = list(re.finditer(r"^(?:###\s+(.+)|\s*\d+[.)]\s+(.+))$", content, re.MULTILINE))
    items: list[tuple[str, str]] = []
    for idx, match in enumerate(matches):
        question = (match.group(1) or match.group(2) or "").strip()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        items.append((question, content[match.end() : end]))
    return items


def _hands_on_lines(section: dict[str, object] | None) -> list[str]:
    if not section:
        return []
    return [
        line.strip()
        for line in str(section["content"]).splitlines()
        if re.match(r"^\s*-\s+\[\s*\]\s+", line)
    ]


def _next_module_link(body: str) -> bool:
    if _find_h2(body, r"^Next Module$"):
        return True
    for line in reversed([line.strip() for line in body.splitlines()]):
        if not line:
            continue
        return bool(("[Next" in line or "Next Module" in line) and re.search(r"\[[^\]]+\]\([^)]+\)", line))
    return False


def structure_metrics(text: str) -> dict[str, object]:
    _, body = _strip_frontmatter(text)
    learning = _find_matching_h2(body, LEARNING_OUTCOME_HEADINGS)
    why = next(
        (
            section
            for section in _sections(body)
            if section["level"] == 2
            and re.search("why", str(section["title"]), re.IGNORECASE)
            and re.search(r"matter|module", str(section["title"]), re.IGNORECASE)
        ),
        None,
    )
    common = _find_matching_h2(body, COMMON_MISTAKES_PREFIX_HEADINGS, prefix=True)
    quiz = _find_matching_h2(body, QUIZ_HEADINGS) or _find_matching_h2(body, QUIZ_PREFIX_HEADINGS, prefix=True)
    hands = _find_matching_h2(body, HANDS_ON_HEADINGS) or _find_matching_h2(
        body, HANDS_ON_PREFIX_HEADINGS, prefix=True
    )
    quiz_items = _quiz_items(quiz)
    did_section = _find_matching_h2(body, DID_YOU_KNOW_HEADINGS)
    did_you_know_count = _count_bullets(did_section)
    if did_you_know_count == 0:
        did_you_know_count = sum(
            1
            for line in body.splitlines()
            if re.match(r"^\s*(?:#{2,6}\s+|[-*+]\s+).*Did You Know\b", line, re.IGNORECASE)
        )

    positions = {
        "learning": learning["start"] if learning else None,
        "why": why["start"] if why else None,
        "did": body.lower().find("did you know") if "did you know" in body.lower() else None,
        "common": common["start"] if common else None,
        "quiz": quiz["start"] if quiz else None,
        "hands": hands["start"] if hands else None,
        "next": _find_h2(body, r"^Next Module$")["start"] if _find_h2(body, r"^Next Module$") else None,
    }
    next_link = _next_module_link(body)
    ordered_values = [positions[key] for key in ("learning", "why", "did", "common", "quiz", "hands", "next")]
    section_order_correct = (
        next_link
        and all(value is not None for value in ordered_values)
        and ordered_values == sorted(ordered_values)
    )

    return {
        "has_learning_outcomes": learning is not None,
        "learning_outcome_count": _count_bullets(learning),
        "has_why_matters": why is not None,
        "did_you_know_count": did_you_know_count,
        "common_mistakes_rows": _common_mistakes_rows(common),
        "quiz_count": len(quiz_items),
        "quiz_with_details": sum(1 for _, block in quiz_items if "<details" in block.lower()),
        "hands_on_checkboxes": len(_hands_on_lines(hands)),
        "section_order_correct": section_order_correct,
        "next_module_link": next_link,
    }


def _extract_section_text(text: str, pattern: str) -> str:
    _, body = _strip_frontmatter(text)
    section = _find_h2(body, pattern)
    return str(section["content"]) if section else ""


def _extract_matching_section_text(text: str, candidates: Iterable[str], prefix: bool = False) -> str:
    _, body = _strip_frontmatter(text)
    section = _find_matching_h2(body, candidates, prefix)
    return str(section["content"]) if section else ""


def extract_urls(section_text: str) -> list[str]:
    seen: dict[str, None] = {}
    for url in MD_LINK_RE.findall(section_text):
        seen.setdefault(url.rstrip(".,);'\""), None)
    for url in BARE_URL_RE.findall(section_text):
        cleaned = url.rstrip(".,);'\"")
        seen.setdefault(cleaned, None)
    return list(seen)


def _check_url(url: str) -> str:
    try:
        import requests

        session = requests.Session()
        session.max_redirects = 5
        response = session.head(url, timeout=10, allow_redirects=True)
        if response.status_code in (403, 405, 501):
            response = session.get(url, timeout=10, allow_redirects=True, stream=True)
            response.close()
    except Exception:
        return "fetch_failed"
    if 200 <= response.status_code <= 299:
        return "redirect" if response.history else "200"
    return "404"


def sources_metrics(text: str, skip_source_check: bool, max_workers: int) -> dict[str, object]:
    section = _extract_matching_section_text(text, SOURCES_HEADINGS)
    urls = extract_urls(section)
    if skip_source_check:
        statuses: dict[str, int] = {"skipped": len(urls)}
    else:
        statuses = {"200": 0, "redirect": 0, "404": 0, "fetch_failed": 0}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            for status in executor.map(_check_url, urls):
                statuses[status] = statuses.get(status, 0) + 1
    return {"count": len(urls), "url_status": statuses, "urls": urls}


def anti_leak_metrics(text: str) -> dict[str, object]:
    _, body = _strip_frontmatter(text)
    body_no_code = _strip_code_blocks(body, " ")
    lowered = body_no_code.lower()
    forbidden = [token for token in FORBIDDEN_TOKENS if token.lower() in lowered]
    has_k_shortcut = bool(KUBECTL_COMMAND_RE.search(body_no_code))
    if not has_k_shortcut:
        kubectl_alias_introduced = True
    else:
        # Search the original body because alias definitions normally live
        # inside fenced bash snippets. The alias only needs to appear before
        # the first shorthand command, not before every long-form kubectl
        # mention in explanatory prose.
        first_shortcut = KUBECTL_COMMAND_RE.search(body)
        alias = ALIAS_RE.search(body)
        kubectl_alias_introduced = bool(
            first_shortcut and alias and alias.start() < first_shortcut.start()
        )
    return {
        "forbidden_tokens": forbidden,
        "has_emoji": bool(EMOJI_RE.search(body_no_code)),
        "has_47": bool(re.search(r"(?<!\d)47(?!\d)", body_no_code)),
        "kubectl_alias_introduced": kubectl_alias_introduced,
    }


def _strip_top_metadata(body: str) -> str:
    """Drop canonical metadata blockquotes before prose checks."""
    lines = body.splitlines()
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1
    while start < len(lines) and lines[start].strip().startswith(">"):
        start += 1
    while start < len(lines) and not lines[start].strip():
        start += 1
    if start < len(lines) and re.fullmatch(r"-{3,}", lines[start].strip()):
        start += 1
    while start < len(lines) and not lines[start].strip():
        start += 1
    return "\n".join(lines[start:])


def protected_assets(text: str) -> dict[str, int]:
    _, body = _strip_frontmatter(text)
    fences = re.findall(r"```([^\n]*)\n.*?```", body, flags=re.DOTALL)
    lines = body.splitlines()
    return {
        "code_blocks": len(fences),
        "ascii_diagrams": _count_ascii_diagrams(lines),
        "mermaid_diagrams": sum(1 for info in fences if info.strip().lower().startswith("mermaid")),
        "tables": _count_markdown_tables(lines),
    }


def _count_ascii_diagrams(lines: list[str]) -> int:
    indexes = sorted(_ascii_diagram_line_indexes(lines))
    if not indexes:
        return 0
    groups = 1
    for prev, current in zip(indexes, indexes[1:]):
        if current != prev + 1:
            groups += 1
    return groups


def _count_markdown_tables(lines: list[str]) -> int:
    count = 0
    for idx, line in enumerate(lines[:-1]):
        if "|" in line and TABLE_SEPARATOR_RE.match(lines[idx + 1].strip()):
            count += 1
    return count


def _content_tokens(text: str) -> list[str]:
    tokens = [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9-]*", text)]
    tokens = [token[:-1] if len(token) > 4 and token.endswith("s") else token for token in tokens]
    return [token for token in tokens if len(token) >= 3 and token not in STOPWORDS]


def _token_match(outcome_tokens: list[str], target: str) -> bool:
    if not outcome_tokens:
        return False
    target_tokens = set(_content_tokens(target))
    required = min(2, len(outcome_tokens))
    return len(set(outcome_tokens) & target_tokens) >= required


def _learning_outcomes(text: str) -> list[str]:
    section_text = _extract_matching_section_text(text, LEARNING_OUTCOME_HEADINGS)
    outcomes = []
    for line in section_text.splitlines():
        match = re.match(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(.+)", line)
        if match:
            outcomes.append(match.group(1).strip())
    return outcomes


def alignment_metrics(text: str) -> dict[str, object]:
    _, body = _strip_frontmatter(text)
    outcomes = _learning_outcomes(text)
    paragraphs = extract_body_paragraphs(text)
    sections = _sections(body)
    section_targets = [str(section["title"]) for section in sections if section["level"] == 2]
    section_targets.extend(paragraphs)
    quiz = _find_matching_h2(body, QUIZ_HEADINGS) or _find_matching_h2(body, QUIZ_PREFIX_HEADINGS, prefix=True)
    hands = _find_matching_h2(body, HANDS_ON_HEADINGS) or _find_matching_h2(
        body, HANDS_ON_PREFIX_HEADINGS, prefix=True
    )
    assessment_items = [
        (f"quiz_{idx}", f"{question} {block}")
        for idx, (question, block) in enumerate(_quiz_items(quiz), 1)
    ]
    assessment_items.extend(
        (f"hands_on_{idx}", line) for idx, line in enumerate(_hands_on_lines(hands), 1)
    )

    section_results: list[dict[str, object]] = []
    assessment_results: list[dict[str, object]] = []
    for outcome in outcomes:
        tokens = _content_tokens(outcome)[:8]
        section_name: str | None = None
        assessment_name: str | None = None
        if tokens:
            for target in section_targets:
                if _token_match(tokens, target):
                    section_name = target[:80]
                    break
            for name, target in assessment_items:
                if _token_match(tokens, target):
                    assessment_name = name
                    break
        section_results.append({"outcome": outcome, "covered": section_name is not None, "section": section_name})
        assessment_results.append({"outcome": outcome, "covered_by": assessment_name})
    all_covered = bool(outcomes) and all(item["covered"] for item in section_results) and all(
        item["covered_by"] for item in assessment_results
    )
    return {
        "outcomes_to_sections": section_results,
        "outcomes_to_assessment": assessment_results,
        "all_outcomes_covered": all_covered,
    }


def gate_results(
    metrics: dict[str, float | int],
    structure: dict[str, object],
    sources: dict[str, object],
    anti_leak: dict[str, object],
    alignment: dict[str, object],
    skip_source_check: bool,
) -> dict[str, bool | None]:
    quiz_count = int(structure["quiz_count"])
    gates: dict[str, bool | None] = {
        "density_mean_wpp_30": float(metrics["mean_wpp"]) >= 30,
        "density_median_wpp_28": float(metrics["median_wpp"]) >= 28,
        "density_short_rate_20pct": float(metrics["short_paragraph_rate"]) <= 0.20,
        "density_max_consecutive_short_2": int(metrics["max_consecutive_short_run"]) <= 2,
        "body_words_5000": int(metrics["body_words"]) >= 5000,
        "sentence_length_12_28": 12 <= float(metrics["mean_sentence_length"]) <= 28,
        "structure_sections_present": bool(structure["has_learning_outcomes"])
        and 3 <= int(structure["learning_outcome_count"]) <= 5
        and bool(structure["has_why_matters"])
        and bool(structure["next_module_link"]),
        "structure_order_correct": bool(structure["section_order_correct"]),
        "structure_did_you_know_4": int(structure["did_you_know_count"]) == 4,
        "structure_common_mistakes_6_8": 6 <= int(structure["common_mistakes_rows"]) <= 8,
        "structure_quiz_6_8_with_details": 6 <= quiz_count <= 8
        and int(structure["quiz_with_details"]) == quiz_count,
        "structure_hands_on_checkboxes": int(structure["hands_on_checkboxes"]) >= 3,
        "sources_min_10": int(sources["count"]) >= 10,
        "sources_all_reachable": None
        if skip_source_check
        else not any(int(sources["url_status"].get(key, 0)) for key in ("404", "fetch_failed")),  # type: ignore[union-attr]
        "anti_leak": not anti_leak["forbidden_tokens"]
        and not anti_leak["has_emoji"]
        and not anti_leak["has_47"]
        and bool(anti_leak["kubectl_alias_introduced"]),
        "outcomes_aligned": bool(alignment["all_outcomes_covered"]),
    }
    return gates


def classify_tier(metrics: dict[str, float | int], gates: dict[str, bool | None]) -> tuple[str, list[str]]:
    failed = [key for key, value in gates.items() if value is False]
    if int(metrics["body_words"]) < 3000:
        return "T3", failed
    if not failed:
        return "T0", []
    density_keys = {
        "density_mean_wpp_30",
        "density_median_wpp_28",
        "density_short_rate_20pct",
        "density_max_consecutive_short_2",
        "sentence_length_12_28",
        "body_words_5000",
    }
    structure_failed = [key for key in failed if key.startswith("structure_")]
    density_failed = [key for key in failed if key in density_keys]
    other_failed = [key for key in failed if key not in density_keys and not key.startswith("structure_")]
    if density_failed and structure_failed:
        return "T3", failed
    if structure_failed and not density_failed and not other_failed and len(structure_failed) <= 2:
        return "T1", failed
    if density_failed and not structure_failed and not other_failed:
        return "T2", failed
    return "T3", failed


def verify(path: str | Path, skip_source_check: bool = False, max_workers: int = 8) -> dict[str, object]:
    module_path = Path(path)
    text = _read(module_path)
    frontmatter, _ = _strip_frontmatter(text)
    metrics = density_metrics(text)
    structure = structure_metrics(text)
    sources = sources_metrics(text, skip_source_check, max_workers)
    assets = protected_assets(text)
    anti = anti_leak_metrics(text)
    alignment = alignment_metrics(text)
    gates = gate_results(metrics, structure, sources, anti, alignment, skip_source_check)
    tier, reasons = classify_tier(metrics, gates)
    passed = all(value is not False for value in gates.values())
    try:
        display_path = str(module_path.relative_to(REPO_ROOT))
    except ValueError:
        display_path = str(module_path)
    return {
        "path": display_path,
        "title": str(frontmatter.get("title", "")),
        "tier": tier,
        "tier_reasons": reasons,
        "metrics": metrics,
        "structure": structure,
        "sources": sources,
        "protected_assets": assets,
        "anti_leak": anti,
        "alignment": alignment,
        "gates": gates,
        "passed": passed,
        "frontmatter": frontmatter,
    }


def _frontmatter_revision_pending(path: Path) -> bool:
    frontmatter, _ = _strip_frontmatter(_read(path))
    return frontmatter.get("revision_pending") is True


def _collect_paths(args: argparse.Namespace) -> list[Path]:
    paths = [Path(path) for path in args.paths]
    if args.glob:
        paths.extend(Path(path) for path in globlib.glob(args.glob, recursive=True))
    if args.all_revision_pending:
        paths.extend(
            path
            for path in (REPO_ROOT / "src/content/docs").glob("**/*.md")
            if _frontmatter_revision_pending(path)
        )
    seen: dict[Path, None] = {}
    for path in paths:
        seen.setdefault(path, None)
    return list(seen)


def _write_records(records: Iterable[dict[str, object]], out: Path | None, tier_only: bool) -> None:
    handle = out.open("w", encoding="utf-8") if out else sys.stdout
    try:
        for record in records:
            if tier_only:
                handle.write(f"{record['path']}: {record['tier']}\n")
            else:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    finally:
        if out:
            handle.close()


def _print_summary(records: list[dict[str, object]]) -> None:
    tiers = Counter(str(record["tier"]) for record in records)
    failures = Counter(
        reason
        for record in records
        for reason in record.get("tier_reasons", [])  # type: ignore[union-attr]
    )
    print("summary:")
    print("tiers:", json.dumps(dict(sorted(tiers.items())), sort_keys=True))
    print("failure_gates:", json.dumps(dict(sorted(failures.items())), sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify KubeDojo modules against the #388 contract.")
    parser.add_argument("paths", nargs="*", help="Markdown module paths")
    parser.add_argument("-g", "--glob", help="Glob pattern for markdown modules")
    parser.add_argument("-A", "--all-revision-pending", action="store_true", help="Scan revision_pending modules")
    parser.add_argument("-o", "--out", type=Path, help="Write JSONL output to this path")
    parser.add_argument("-s", "--summary", action="store_true", help="Print aggregate tier and gate counts")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress per-module progress")
    parser.add_argument("--skip-source-check", action="store_true", help="Skip live source reachability checks")
    parser.add_argument("--max-workers", type=int, default=8, help="Max source-check worker threads")
    parser.add_argument("--tier-only", action="store_true", help='Print "path: tier" for fast triage')
    args = parser.parse_args(argv)

    paths = _collect_paths(args)
    if not paths:
        parser.error("provide paths, --glob, or --all-revision-pending")
    records: list[dict[str, object]] = []
    for path in paths:
        if not args.quiet and args.out:
            print(f"verifying {path}", file=sys.stderr)
        records.append(verify(path, skip_source_check=args.skip_source_check, max_workers=args.max_workers))
    _write_records(records, args.out, args.tier_only)
    if args.summary:
        _print_summary(records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
