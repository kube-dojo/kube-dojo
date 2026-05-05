#!/usr/bin/env python3
"""sweep_ai_history_aids.py — Phase E batch audit-and-fix for ai-history chapters.

Per chapter: dispatch claude headless with a prompt that returns a
JSON fix-list (not full markdown). Driver applies each `before → after`
substitution after strict validation, atomic-writes the result, and
gates progress per-Part for human inspection.

Reviewed cross-family pre-launch:
  - codex gpt-5.5 (engineering correctness + race conditions + sanity)
  - gemini (stylistic risk + voice preservation)
Both REQUEST CHANGES; this revision integrates their must-fix items.

Decision-log: docs/decisions/2026-05-05-phase-e-scope.md
PR #888 reference: scripts/dispatch.py allows WebFetch+WebSearch in
  --no-tools mode; commit `733cfff0` on trunk.

Usage:
    .venv/bin/python scripts/sweep_ai_history_aids.py --part 1 [--dry-run]

Parts:
    1: ch-01 .. ch-08    5: ch-33 .. ch-40
    2: ch-09 .. ch-16    6: ch-41 .. ch-48
    3: ch-17 .. ch-24    7: ch-49 .. ch-56
    4: ch-25 .. ch-32    8: ch-57 .. ch-64
                         9: ch-65 .. ch-72

Default skip set: ch-33, ch-34, ch-58 (already audited + fixed inline
in the pilot phase).
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, UTC
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROSE_DIR = REPO / "src" / "content" / "docs" / "ai-history"
BUNDLE_DIR = REPO / "docs" / "research" / "ai-history" / "chapters"
LOG_DIR = REPO / ".tmp" / "sweep-logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_PATH = LOG_DIR / "summary.jsonl"

# Already audited and fixed inline this session.
DEFAULT_SKIP = {"ch-33", "ch-34", "ch-58"}

# Per-Part chunks. Each Part = 8 chapters = 1 commit boundary.
PARTS: dict[int, tuple[int, int]] = {
    1: (1, 8),
    2: (9, 16),
    3: (17, 24),
    4: (25, 32),
    5: (33, 40),
    6: (41, 48),
    7: (49, 56),
    8: (57, 64),
    9: (65, 72),
}

VENV_PYTHON = REPO / ".venv" / "bin" / "python"

PROMPT_TEMPLATE = """\
# Phase E sweep — audit AI History {chapter_id} for wrong-specifics

You are a forensic fact-checker for one ai-history book chapter. Your job is to identify *factually-wrong specifics* (and ONLY those) that contradict the research bundle or a primary web source. You do NOT have edit authority; you produce a JSON fix-list that a separate driver applies after validation.

## What you have

Chapter prose:    {prose_path}
Research bundle: {bundle_dir}/
  - brief.md, sources.md, timeline.md, people.md, scene-sketches.md,
    infrastructure-log.md, open-questions.md, tier3-proposal.md, tier3-review.md

WebFetch and WebSearch are available. Use them sparingly — see "When NOT to use the web" below.

## What counts as a wrong-specific (FIX THESE)

A claim is "wrong" if AT LEAST ONE of:
1. It directly contradicts the research bundle (people.md / sources.md / timeline.md / scene-sketches.md / infrastructure-log.md). Example: bundle says "2650+", prose says "2500".
2. It directly contradicts a primary web source you fetched (Wikipedia + 1 corroborating source). Example: a person's title, an organization's affiliation, a year, a publication venue.
3. It is a forward-looking claim about 2024-2025 frontier models that is contradicted by the current state-of-field. Example: "DDPM is still the dominant training objective" when SD3 / FLUX use rectified flow.

## What is NOT a wrong-specific (DO NOT propose fixes for these)

- **Paraphrase / rounding**: "forty years earlier" when source says "thirty-nine". Skip.
- **Rhetorical flourishes / metaphors / historical shorthand**: "flooded the AI winter with cash", "a citadel of human calculation", "a chessboard made out of silicon". Skip.
- **Editorial framings or interpretations**: "the moment AI 'arrived'", "an architectural dead end". Skip.
- **Voice / tone / sentence-structure preferences**. Skip.
- **Missing-context elaborations** that aren't factually wrong. Skip.
- **Anything in S:timeline (Mermaid diagram) that aligns with timeline.md**. Pilots show timeline blocks are template-derived and clean. Skip.
- **Math sidebars / formulas in Tier 2 chapters** that already had the codex math-review pass (most Tier 2 chapters did). Only flag if you can verify against the cited paper that a formula is symbolically wrong. Otherwise skip.

## When NOT to use the web

- For S:matters claims about a 2022-or-earlier topic: bundle usually covers it; web is unnecessary.
- DO NOT search current news / current state-of-field for paraphrase-drift cases.
- DO NOT add "As of {{year}}" boilerplate. The book's voice is timeless-historical, not journalistic.
- For S:cast / S:glossary: consult the bundle FIRST. Only fall back to the web when bundle is silent and the claim seems suspicious.

## Section identification

Identify sections by their `<summary>` text or admonition label, normalized (strip `<strong>`, lowercase, ignore punctuation). Match against keywords:

- `cast` / `characters`              → S:cast
- `timeline`                          → S:timeline
- `glossary` / `plain-words`          → S:glossary
- `math` / `formulas` / `equations`   → S:math
- `architecture` / `sketch`           → S:architecture
- `:::tip[In one paragraph]`         → S:lede
- `:::note[Why this still matters today]` → S:matters
- (other prose between sections)      → S:body

If a section type is missing from a chapter, just skip it.

## Output format (STRICT)

Return EXACTLY ONE valid JSON object. The driver tolerates prose preamble/epilogue, but the LAST JSON object containing a `fixes` field is the one that gets parsed — so if you absolutely must reason in prose first, put the prose BEFORE the JSON, never after, and emit only one final object. No markdown code fence. The driver uses `JSONDecoder.raw_decode` so trailing whitespace is fine.

Schema:

```
{{
  "chapter_id": "{chapter_id}",
  "fixes": [
    {{
      "section": "S:cast" | "S:glossary" | "S:matters" | "S:body" | "S:lede" | "S:architecture" | "S:timeline" | "S:math",
      "before": "exact substring from the chapter, MUST be unique in the file",
      "after":  "minimum edit that fixes the wrong-specific while preserving voice",
      "severity": "wrong-specific",
      "source": "bundle:<file>:<section>" OR "web:<url>",
      "rationale": "one sentence explaining why this is wrong"
    }}
  ],
  "audit_summary": "1-3 sentences describing what you checked. Required even if fixes is empty."
}}
```

## Hard constraints on each fix

- `before` MUST appear exactly once in the chapter file. If your candidate substring is not unique, expand its context (more surrounding words) until it is.
- `after` MUST preserve voice and surrounding structure. Apply the *minimum* edit.
- Neither `before` nor `after` may contain a markdown heading marker (`##`, `###`), a `<details>` / `</details>` tag, or a `:::` admonition fence. Stay within a sentence or contiguous block.
- Neither may cross the YAML frontmatter boundary.
- DO NOT add citations / footnotes / "as of {{year}}" boilerplate / URLs in the prose itself.
- DO NOT introduce new facts beyond what is needed to correct a wrong-specific.

## Hard limits

- Max 25 web operations.
- Walltime cap ~25 min.

If you have no wrong-specifics to propose, return `{{"chapter_id": "...", "fixes": [], "audit_summary": "..."}}`.

Begin.
"""


SECTION_HEADER_RE = re.compile(r"^##\s+", re.MULTILINE)
DETAILS_OPEN_RE = re.compile(r"^<details>", re.MULTILINE)
DETAILS_CLOSE_RE = re.compile(r"^</details>", re.MULTILINE)
ADMONITION_RE = re.compile(r"^:::\w+", re.MULTILINE)
ADMONITION_CLOSE_RE = re.compile(r"^:::\s*$", re.MULTILINE)
JSON_FENCE_RE = re.compile(r"^```(?:json|JSON)?\s*\n?|\n?```\s*$", re.MULTILINE)


# ----- helpers -----------------------------------------------------------


@contextmanager
def chapter_lock(chapter_id: str):
    """Per-chapter advisory lock; prevents concurrent runs on the same chapter."""
    lock_path = LOG_DIR / f"{chapter_id}.lock"
    with lock_path.open("w", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def list_chapter_ids() -> list[str]:
    ids = []
    for path in sorted(PROSE_DIR.glob("ch-*.md")):
        # filename like ch-01-the-laws-of-thought.md → ch-01
        parts = path.stem.split("-")
        ids.append(f"{parts[0]}-{parts[1]}")
    return ids


def chapter_prose_path(chapter_id: str) -> Path:
    matches = list(PROSE_DIR.glob(f"{chapter_id}-*.md"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected 1 prose file for {chapter_id}, found {len(matches)}")
    return matches[0]


def chapter_bundle_dir(chapter_id: str) -> Path:
    matches = list(BUNDLE_DIR.glob(f"{chapter_id}-*"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected 1 bundle dir for {chapter_id}, found {len(matches)}")
    return matches[0]


def build_prompt(chapter_id: str) -> str:
    return PROMPT_TEMPLATE.format(
        chapter_id=chapter_id,
        prose_path=chapter_prose_path(chapter_id),
        bundle_dir=chapter_bundle_dir(chapter_id),
    )


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def frontmatter_block(text: str) -> str | None:
    """Return the verbatim YAML frontmatter block (`---` to next `---`)."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return None
    for i in range(1, min(len(lines), 80)):
        if lines[i] == "---":
            return "\n".join(lines[: i + 1])
    return None


def structural_counts(text: str) -> dict:
    return {
        "h2_headings": len(SECTION_HEADER_RE.findall(text)),
        "details_open": len(DETAILS_OPEN_RE.findall(text)),
        "details_close": len(DETAILS_CLOSE_RE.findall(text)),
        "admonition_open": len(ADMONITION_RE.findall(text)),
        # admonition close is :::, but :::word matches both. Filter to bare :::
        "admonition_close": sum(1 for line in text.splitlines() if line.strip() == ":::"),
        "lines": len(text.splitlines()),
        "frontmatter": frontmatter_block(text),
    }


def dispatch_claude(prompt: str, timeout: int = 1500) -> tuple[bool, str, str]:
    """Run dispatch.py claude --no-tools with the prompt on stdin."""
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    cmd = [
        python,
        str(REPO / "scripts" / "dispatch.py"),
        "claude",
        "--no-tools",
        "--timeout",
        str(timeout),
        "-",
    ]
    try:
        proc = subprocess.run(
            cmd, input=prompt, text=True, capture_output=True,
            timeout=timeout + 60, cwd=str(REPO),
        )
    except subprocess.TimeoutExpired:
        return False, "", "TIMEOUT"
    return proc.returncode == 0, proc.stdout, proc.stderr


def parse_json_response(raw: str) -> tuple[bool, dict | str]:
    """Extract a JSON object from anywhere in the response.

    Tolerates: code-fence wrap, prose preamble before the object, prose
    epilogue after the object. Looks for an object containing the
    expected `chapter_id` and `fixes` keys; on tie, prefers the last
    parseable one (often the final answer after reasoning preamble).
    """
    body = raw.strip()
    body = JSON_FENCE_RE.sub("", body).strip()
    decoder = json.JSONDecoder()
    candidates: list[dict] = []
    last_err: str | None = None
    # Scan every '{' position; raw_decode parses one JSON value starting there.
    for i, ch in enumerate(body):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(body[i:])
        except json.JSONDecodeError as exc:
            last_err = f"raw_decode at {i}: {exc.msg}"
            continue
        if isinstance(obj, dict) and "fixes" in obj:
            candidates.append(obj)
    if not candidates:
        return False, last_err or "no JSON object with 'fixes' key found in response"
    data = candidates[-1]
    if not isinstance(data["fixes"], list):
        return False, "'fixes' is not a list"
    return True, data


def validate_fix(fix: dict, original: str) -> tuple[bool, str]:
    for required in ("section", "before", "after", "source"):
        if required not in fix:
            return False, f"fix missing required field: {required}"
    before = fix["before"]
    after = fix["after"]
    if not isinstance(before, str) or not isinstance(after, str):
        return False, "before/after must be strings"
    if before == after:
        return False, "before == after (no-op fix)"
    # Forbid spans that cross structural boundaries.
    forbidden = ("\n## ", "\n### ", "<details>", "</details>", "\n:::")
    for token in forbidden:
        if token in before or token in after:
            return False, f"span includes forbidden structural token: {token!r}"
    # Must not touch frontmatter.
    fm = frontmatter_block(original)
    if fm and (before in fm or after.startswith("---\n")):
        return False, "fix overlaps frontmatter"
    # Uniqueness of `before` in original.
    occurrences = original.count(before)
    if occurrences == 0:
        return False, "before substring not found in original"
    if occurrences > 1:
        return False, f"before substring not unique ({occurrences} matches); expand context"
    # Length sanity: after should not be wildly longer than before.
    if len(after) > 3 * max(len(before), 80):
        return False, f"after is suspiciously long ({len(after)} vs before {len(before)})"
    return True, "ok"


def apply_fixes(original: str, fixes: list[dict]) -> tuple[bool, str, list[str]]:
    """Apply each fix's before→after substitution. Returns (ok, fixed_text, errors)."""
    errors: list[str] = []
    text = original
    for i, fix in enumerate(fixes):
        ok, msg = validate_fix(fix, text)
        if not ok:
            errors.append(f"fix #{i+1} ({fix.get('section')}): {msg}")
            continue
        text = text.replace(fix["before"], fix["after"], 1)
    return (len(errors) == 0, text, errors)


def post_apply_sanity(original: str, fixed: str) -> tuple[bool, str]:
    """Compare structural counts; reject if structure changed."""
    before_counts = structural_counts(original)
    after_counts = structural_counts(fixed)
    if before_counts["frontmatter"] != after_counts["frontmatter"]:
        return False, "frontmatter block changed"
    if before_counts["h2_headings"] != after_counts["h2_headings"]:
        return False, f"h2 heading count changed: {before_counts['h2_headings']} -> {after_counts['h2_headings']}"
    if before_counts["details_open"] != after_counts["details_open"] or \
       before_counts["details_close"] != after_counts["details_close"]:
        return False, "details block count changed"
    if before_counts["admonition_open"] != after_counts["admonition_open"]:
        return False, "admonition open count changed"
    if before_counts["admonition_close"] != after_counts["admonition_close"]:
        return False, "admonition close count changed"
    delta = after_counts["lines"] - before_counts["lines"]
    if abs(delta) > 5:
        return False, f"line count delta {delta} (> ±5)"
    if not (0.92 * len(original) <= len(fixed) <= 1.08 * len(original)):
        return False, f"size delta out of band (orig {len(original)}, fixed {len(fixed)})"
    return True, "ok"


def atomic_write(path: Path, content: str) -> None:
    """Write content to path via tempfile in same dir, then os.replace."""
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    tmp = Path(tmp_name)
    try:
        with __import__("os").fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            __import__("os").fsync(fh.fileno())
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()


def log_event(event: dict) -> None:
    event["ts"] = datetime.now(UTC).isoformat()
    with SUMMARY_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def is_rate_limited(stderr_tail: str) -> bool:
    pat = re.compile(r"rate.?limit|quota.?exceeded|too many requests|\b429\b|usage limit", re.IGNORECASE)
    return bool(pat.search(stderr_tail or ""))


# ----- per-chapter pipeline ----------------------------------------------


def process_chapter(chapter_id: str, dry_run: bool, halt_on_rate_limit: bool) -> tuple[dict, bool]:
    """Returns (event_dict, should_halt_sweep)."""
    print(f"\n=== {chapter_id} === [{datetime.now().strftime('%H:%M:%S')}]", flush=True)
    prose_path = chapter_prose_path(chapter_id)
    bundle_dir = chapter_bundle_dir(chapter_id)
    if not (bundle_dir / "sources.md").exists():
        print("  skip — bundle/sources.md missing", flush=True)
        return ({"chapter": chapter_id, "kind": "skip-no-bundle"}, False)

    with chapter_lock(chapter_id):
        original = prose_path.read_text(encoding="utf-8")
        original_hash = hash_text(original)

        prompt = build_prompt(chapter_id)
        t0 = time.time()
        ok, stdout, stderr = dispatch_claude(prompt)
        elapsed = time.time() - t0

        if not ok:
            stderr_tail = (stderr or "")[-400:]
            rate_limited = is_rate_limited(stderr_tail)
            print(f"  dispatch failed ({elapsed:.0f}s) — rate-limited={rate_limited}; stderr tail: {stderr_tail!r}", flush=True)
            return ({"chapter": chapter_id, "kind": "dispatch-fail",
                     "elapsed_s": elapsed, "rate_limited": rate_limited,
                     "stderr_tail": stderr_tail}, halt_on_rate_limit and rate_limited)

        parsed_ok, parsed = parse_json_response(stdout)
        if not parsed_ok:
            debug_path = LOG_DIR / f"{chapter_id}-raw.md"
            debug_path.write_text(stdout, encoding="utf-8")
            print(f"  UNPARSEABLE response ({elapsed:.0f}s) — {parsed!r}; raw saved", flush=True)
            return ({"chapter": chapter_id, "kind": "unparseable",
                     "elapsed_s": elapsed, "error": str(parsed),
                     "raw_saved": str(debug_path)}, False)

        assert isinstance(parsed, dict)
        fixes = parsed.get("fixes", [])
        audit_summary = parsed.get("audit_summary", "")

        if not fixes:
            print(f"  no_changes ({elapsed:.0f}s) — '{audit_summary[:80]}...'", flush=True)
            return ({"chapter": chapter_id, "kind": "no_changes",
                     "elapsed_s": elapsed, "audit_summary": audit_summary,
                     "fix_count": 0}, False)

        # Apply each fix in sequence. Validation per-fix.
        applied_ok, fixed, errors = apply_fixes(original, fixes)
        if not applied_ok:
            debug_path = LOG_DIR / f"{chapter_id}-rejected.json"
            debug_path.write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  REJECT — fix validation errors ({elapsed:.0f}s):", flush=True)
            for e in errors:
                print(f"    - {e}", flush=True)
            return ({"chapter": chapter_id, "kind": "rejected-validation",
                     "elapsed_s": elapsed, "errors": errors,
                     "raw_saved": str(debug_path), "fix_count": len(fixes)}, False)

        # Post-apply structural sanity check.
        sanity_ok, sanity_msg = post_apply_sanity(original, fixed)
        if not sanity_ok:
            debug_path = LOG_DIR / f"{chapter_id}-rejected-sanity.md"
            debug_path.write_text(fixed, encoding="utf-8")
            print(f"  REJECT — post-apply sanity ({elapsed:.0f}s) — {sanity_msg}", flush=True)
            return ({"chapter": chapter_id, "kind": "rejected-sanity",
                     "elapsed_s": elapsed, "reason": sanity_msg,
                     "raw_saved": str(debug_path), "fix_count": len(fixes)}, False)

        # Concurrent-modification check before write.
        current = prose_path.read_text(encoding="utf-8")
        if hash_text(current) != original_hash:
            print(f"  ABORT — source changed during dispatch", flush=True)
            return ({"chapter": chapter_id, "kind": "source-changed",
                     "elapsed_s": elapsed, "fix_count": len(fixes)}, False)

        # Log audit trail BEFORE atomic-applying.
        audit_path = LOG_DIR / f"{chapter_id}-audit.json"
        audit_path.write_text(json.dumps({
            "chapter_id": chapter_id,
            "fix_count": len(fixes),
            "fixes": fixes,
            "audit_summary": audit_summary,
            "original_hash": original_hash,
            "elapsed_s": elapsed,
            "applied_at": datetime.now(UTC).isoformat() if not dry_run else None,
        }, indent=2, ensure_ascii=False), encoding="utf-8")

        if dry_run:
            diff_path = LOG_DIR / f"{chapter_id}-diff.md"
            import difflib
            diff = "".join(difflib.unified_diff(
                original.splitlines(keepends=True),
                fixed.splitlines(keepends=True),
                fromfile="before", tofile="after", n=2,
            ))
            diff_path.write_text(diff, encoding="utf-8")
            print(f"  DRY-RUN ok ({elapsed:.0f}s); {len(fixes)} fix(es); diff at {diff_path}", flush=True)
            return ({"chapter": chapter_id, "kind": "dry-run-ok",
                     "elapsed_s": elapsed, "fix_count": len(fixes),
                     "audit_path": str(audit_path), "diff_path": str(diff_path)}, False)

        atomic_write(prose_path, fixed)
        print(f"  fixed + applied ({elapsed:.0f}s); {len(fixes)} fix(es); audit at {audit_path}", flush=True)
        return ({"chapter": chapter_id, "kind": "fixed",
                 "elapsed_s": elapsed, "fix_count": len(fixes),
                 "audit_path": str(audit_path)}, False)


# ----- main --------------------------------------------------------------


def chapters_for_part(part: int) -> list[str]:
    if part not in PARTS:
        raise ValueError(f"unknown part {part}; valid: {sorted(PARTS.keys())}")
    lo, hi = PARTS[part]
    ids = list_chapter_ids()
    return [c for c in ids if lo <= int(c.split("-")[1]) <= hi]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--part", type=int, help="Run a single Part (1-9). Required unless --only.")
    parser.add_argument("--only", help="Comma-separated chapter ids (overrides --part). For testing.")
    parser.add_argument("--skip", default=",".join(sorted(DEFAULT_SKIP)),
                        help="Comma-separated chapter ids to skip (default: 33/34/58 already audited)")
    parser.add_argument("--dry-run", action="store_true", help="Validate but don't write any files")
    parser.add_argument("--continue-on-rate-limit", action="store_true",
                        help="Don't halt the sweep on rate-limit; default is HALT.")
    args = parser.parse_args()

    if not args.only and args.part is None:
        parser.error("--part or --only required")

    if args.only:
        chapter_ids = [c.strip() for c in args.only.split(",") if c.strip()]
    else:
        skip = {s.strip() for s in args.skip.split(",") if s.strip()}
        chapter_ids = [c for c in chapters_for_part(args.part) if c not in skip]

    print(f"[sweep] starting at {datetime.now().isoformat()}")
    if not chapter_ids:
        print("[sweep] no chapters to process — exiting")
        return 0
    print(f"[sweep] chapters: {len(chapter_ids)}: {chapter_ids[0]} .. {chapter_ids[-1]}")
    print(f"[sweep] dry-run: {args.dry_run}")
    print(f"[sweep] halt-on-rate-limit: {not args.continue_on_rate_limit}")
    print()

    halt_on_rate_limit = not args.continue_on_rate_limit
    halted = False
    for ch in chapter_ids:
        event, should_halt = process_chapter(ch, dry_run=args.dry_run, halt_on_rate_limit=halt_on_rate_limit)
        log_event(event)
        if should_halt:
            print(f"\n[sweep] HALT — rate-limit detected on {ch}; resume later with --part {args.part}")
            halted = True
            break

    if not halted:
        print(f"\n[sweep] complete at {datetime.now().isoformat()}")
        print(f"[sweep] summary log: {SUMMARY_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
