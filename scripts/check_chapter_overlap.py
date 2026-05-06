#!/usr/bin/env python3
"""Find paragraph-level overlap across the AI History book.

The scanner is deterministic and local-only. It strips frontmatter, code
blocks, reader-aid details blocks, and Starlight asides before comparing prose
paragraphs. Each paragraph is represented as word n-gram shingles and scored
with Jaccard similarity against paragraphs from other chapters.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHAPTERS_DIR = REPO_ROOT / "src" / "content" / "docs" / "ai-history"
WORD_RE = re.compile(r"[\w]+", re.UNICODE)


@dataclass(frozen=True)
class Paragraph:
    id: int
    chapter: str
    path: str
    start_line: int
    text: str
    words: int
    shingles: frozenset[str]


@dataclass(frozen=True)
class Candidate:
    score: float
    shared_shingles: int
    left_chapter: str
    left_line: int
    left_words: int
    left_excerpt: str
    right_chapter: str
    right_line: int
    right_words: int
    right_excerpt: str


def _blank_reader_aids(lines: list[str]) -> list[str]:
    out: list[str] = []
    in_frontmatter = False
    in_code = False
    in_details = False
    in_aside = False

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if idx == 0 and stripped == "---":
            in_frontmatter = True
            out.append("")
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            out.append("")
            continue
        if stripped.startswith("```"):
            in_code = not in_code
            out.append("")
            continue
        if in_code:
            out.append("")
            continue
        if re.match(r"<details\b", stripped, re.IGNORECASE):
            if re.search(r"</details>", stripped, re.IGNORECASE):
                pass
            else:
                in_details = True
            out.append("")
            continue
        if in_details:
            if re.search(r"</details>", stripped, re.IGNORECASE):
                in_details = False
            out.append("")
            continue
        if stripped.startswith(":::") and stripped != ":::":
            in_aside = True
            out.append("")
            continue
        if in_aside:
            if stripped == ":::":
                in_aside = False
            out.append("")
            continue
        out.append(line)
    return out


def _paragraphs_with_lines(path: Path) -> list[tuple[int, str]]:
    lines = _blank_reader_aids(path.read_text(encoding="utf-8").splitlines())
    paragraphs: list[tuple[int, str]] = []
    buffer: list[str] = []
    start_line = 0

    def flush() -> None:
        nonlocal buffer, start_line
        if not buffer:
            return
        text = " ".join(part.strip() for part in buffer).strip()
        if text and not text.startswith(("#", "|", ">")):
            paragraphs.append((start_line, text))
        buffer = []
        start_line = 0

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith(">"):
            stripped = stripped[1:].strip()
        if stripped.startswith(("- ", "* ")):
            stripped = stripped[2:].strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith(("#", "|")):
            flush()
            continue
        if not buffer:
            start_line = lineno
        buffer.append(stripped)
    flush()
    return paragraphs


def _words(text: str) -> list[str]:
    return WORD_RE.findall(text.lower())


def _shingles(words: list[str], size: int) -> frozenset[str]:
    if len(words) < size:
        return frozenset()
    return frozenset(" ".join(words[idx : idx + size]) for idx in range(len(words) - size + 1))


def _excerpt(text: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def load_paragraphs(min_words: int, shingle_size: int, chapters_dir: Path = CHAPTERS_DIR) -> list[Paragraph]:
    paragraphs: list[Paragraph] = []
    for path in sorted(chapters_dir.glob("ch-*.md")):
        for start_line, text in _paragraphs_with_lines(path):
            words = _words(text)
            if len(words) < min_words:
                continue
            shingles = _shingles(words, shingle_size)
            if not shingles:
                continue
            paragraphs.append(
                Paragraph(
                    id=len(paragraphs),
                    chapter=path.stem,
                    path=str(path.relative_to(REPO_ROOT)),
                    start_line=start_line,
                    text=text,
                    words=len(words),
                    shingles=shingles,
                )
            )
    return paragraphs


def find_candidates(paragraphs: list[Paragraph], threshold: float) -> list[Candidate]:
    shingle_index: dict[str, list[int]] = {}
    overlap_counts: dict[tuple[int, int], int] = {}

    for paragraph in paragraphs:
        for shingle in paragraph.shingles:
            for other_id in shingle_index.get(shingle, []):
                other = paragraphs[other_id]
                if other.chapter == paragraph.chapter:
                    continue
                key = (other_id, paragraph.id)
                overlap_counts[key] = overlap_counts.get(key, 0) + 1
            shingle_index.setdefault(shingle, []).append(paragraph.id)

    candidates: list[Candidate] = []
    for (left_id, right_id), shared in overlap_counts.items():
        left = paragraphs[left_id]
        right = paragraphs[right_id]
        union = len(left.shingles) + len(right.shingles) - shared
        if union <= 0:
            continue
        score = shared / union
        if score < threshold:
            continue
        candidates.append(
            Candidate(
                score=round(score, 4),
                shared_shingles=shared,
                left_chapter=left.chapter,
                left_line=left.start_line,
                left_words=left.words,
                left_excerpt=_excerpt(left.text),
                right_chapter=right.chapter,
                right_line=right.start_line,
                right_words=right.words,
                right_excerpt=_excerpt(right.text),
            )
        )
    return sorted(candidates, key=lambda item: (-item.score, -item.shared_shingles, item.left_chapter))


def render_markdown(candidates: list[Candidate], total: int, args: argparse.Namespace) -> None:
    print("# AI History Paragraph Overlap Report")
    print()
    print(f"- paragraphs scanned: {total}")
    print(f"- shingle size: {args.shingle_size} words")
    print(f"- minimum paragraph length: {args.min_words} words")
    print(f"- similarity threshold: {args.threshold:.2f}")
    print(f"- candidates found: {len(candidates)}")
    print()
    if not candidates:
        print("No cross-chapter paragraph pairs met the threshold.")
        return
    print(f"Showing top {min(args.top, len(candidates))} candidates.")
    print()
    for idx, candidate in enumerate(candidates[: args.top], start=1):
        print(
            f"## {idx}. score {candidate.score:.4f} "
            f"({candidate.shared_shingles} shared shingles)"
        )
        print()
        print(
            f"- left: `{candidate.left_chapter}` line {candidate.left_line} "
            f"({candidate.left_words} words)"
        )
        print(
            f"- right: `{candidate.right_chapter}` line {candidate.right_line} "
            f"({candidate.right_words} words)"
        )
        print()
        print(f"> {candidate.left_excerpt}")
        print()
        print(f"> {candidate.right_excerpt}")
        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "chapter_dir",
        nargs="?",
        default=str(CHAPTERS_DIR),
        help="Directory containing chapter files",
    )
    parser.add_argument("--threshold", type=float, default=0.55, help="Jaccard threshold")
    parser.add_argument("--shingle-size", type=int, default=5, help="word n-gram size")
    parser.add_argument("--min-words", type=int, default=25, help="minimum paragraph length")
    parser.add_argument("--top", type=int, default=50, help="candidate rows to print")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    parser.add_argument(
        "--fail-on-candidates",
        action="store_true",
        help="exit 1 when any candidate meets the threshold",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.threshold <= 0 or args.threshold > 1:
        raise SystemExit("--threshold must be >0 and <=1")
    if args.shingle_size < 2:
        raise SystemExit("--shingle-size must be >=2")
    if args.min_words < args.shingle_size:
        raise SystemExit("--min-words must be >= --shingle-size")

    chapter_dir = Path(args.chapter_dir).resolve()
    if not chapter_dir.is_dir():
        raise SystemExit(f"chapter_dir not found: {args.chapter_dir}")
    paragraphs = load_paragraphs(args.min_words, args.shingle_size, chapter_dir)
    candidates = find_candidates(paragraphs, args.threshold)
    if args.json:
        print(
            json.dumps(
                {
                    "paragraphs_scanned": len(paragraphs),
                    "threshold": args.threshold,
                    "shingle_size": args.shingle_size,
                    "min_words": args.min_words,
                    "candidate_count": len(candidates),
                    "candidates": [asdict(candidate) for candidate in candidates[: args.top]],
                },
                indent=2,
            )
        )
    else:
        render_markdown(candidates, len(paragraphs), args)
    return 1 if args.fail_on_candidates and candidates else 0


if __name__ == "__main__":
    raise SystemExit(main())
