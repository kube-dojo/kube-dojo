#!/usr/bin/env python3
"""Overstatement-detection gate.

Two-stage audit:
1. Deterministic: scan module prose for absolute-claim triggers
   ("always", "never", "universal", "cancels anything", ...).
2. LLM (--llm): dispatch each candidate sentence+context to Codex for a
   verdict of `overstated` | `acceptable` | `not_a_claim` with a
   `suggested_rewrite`.

Skipped regions: fenced code blocks, Mermaid blocks, frontmatter,
tables (heuristic), quiz <details> answers (kept — they teach),
and the `## Sources` section.

Usage:
    python scripts/check_overstatement.py path/to/module.md
    python scripts/check_overstatement.py path/to/module.md --llm
    python scripts/check_overstatement.py path/to/module.md --json

Exits 0 when there are no candidates; 1 if any are emitted (so CI can
gate on it).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))


# Absolute-claim trigger patterns. Case-insensitive. Each entry is
# (label, regex). The goal is HIGH RECALL; the LLM stage triages.
TRIGGERS: list[tuple[str, re.Pattern[str]]] = [
    ("universal",           re.compile(r"\buniversal(ly)?\b", re.I)),
    ("always",              re.compile(r"\balways\b", re.I)),
    ("never",               re.compile(r"\bnever\b", re.I)),
    ("every_single",        re.compile(r"\bevery\s+single\b", re.I)),
    ("first_ever",          re.compile(r"\bfirst\s+ever\b", re.I)),
    ("the_oldest",          re.compile(r"\bthe\s+oldest\b", re.I)),
    ("the_fastest",         re.compile(r"\bthe\s+fastest\b", re.I)),
    ("the_slowest",         re.compile(r"\bthe\s+slowest\b", re.I)),
    ("the_most",            re.compile(r"\bthe\s+most\b", re.I)),
    ("the_only",            re.compile(r"\bthe\s+only\b", re.I)),
    ("100_percent",         re.compile(r"\b100\s*%|\bzero\s+percent\b", re.I)),
    ("guaranteed_to",       re.compile(r"\bguaranteed\s+to\b", re.I)),
    ("impossible",          re.compile(r"\bimpossibl[ey]\b", re.I)),
    ("instantly",           re.compile(r"\binstantly\b", re.I)),
    ("immediately",         re.compile(r"\bimmediately\b", re.I)),
    ("cancels_anything",    re.compile(r"\bcancels?\s+(?:almost\s+)?anything\b", re.I)),
    ("fixes_anything",      re.compile(r"\bfixes?\s+(?:almost\s+)?anything\b", re.I)),
    ("stop_anything",       re.compile(r"\bstop(?:s)?\s+(?:almost\s+)?anything\b", re.I)),
    ("reliable_escape",     re.compile(r"\breliabl[ey]\s+escape\b", re.I)),
    ("always_works",        re.compile(r"\balways\s+works?\b", re.I)),
    ("never_fails",         re.compile(r"\bnever\s+fails?\b", re.I)),
    ("any_and_all",         re.compile(r"\bany\s+and\s+all\b", re.I)),
]

# Phrases that, when present in the sentence, suppress the flag
# because they're legitimately absolute (definitions, constants,
# math statements, quotes).
HEDGE_WHITELIST_RE = re.compile(
    r"\b(approximately|roughly|typically|usually|often|generally|most(?:ly)?|"
    r"some(?:times)?|many|several|may\b|might\b|can\b|could\b|"
    r"for\s+example|for\s+instance|e\.g\.|in\s+theory|in\s+practice|"
    r"depends\s+on|depending\s+on|varies|unless|except|"
    r"for\s+the\s+common\s+case|in\s+the\s+common\s+case|in\s+most\s+cases|"
    r"this\s+module|this\s+exercise|this\s+lab|this\s+section)\b",
    re.I,
)

# Negation within ~30 chars BEFORE the trigger cancels the flag
# ("doesn't always", "not universal", "it is not the only", "rarely immediately").
NEGATION_BEFORE_RE = re.compile(
    r"\b(?:n[o']t|never|rarely|seldom|hardly|barely|isn[o']t|wasn[o']t|"
    r"doesn[o']t|don[o']t|didn[o']t|won[o']t|can[o']t|cannot|aren[o']t|"
    r"no\b)\b[^.]{0,30}$",
    re.I,
)


FENCE_RE = re.compile(r"^```")
HEADING_RE = re.compile(r"^#{1,6}\s")
SOURCES_HEADING_RE = re.compile(r"^##\s+Sources\s*$", re.MULTILINE)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\[])")


def split_into_scoped_lines(body: str) -> list[tuple[int, str]]:
    """Return [(line_no, text), ...] for lines where prose claims can
    live. Skip fenced code blocks, frontmatter, and sources section."""
    out: list[tuple[int, str]] = []
    in_code = False
    in_frontmatter = False
    lines = body.splitlines()
    sources_idx = None
    m = SOURCES_HEADING_RE.search(body)
    if m:
        # Convert byte offset to line index.
        sources_idx = body[: m.start()].count("\n")
    for i, line in enumerate(lines):
        if sources_idx is not None and i >= sources_idx:
            break
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if line.strip() == "---":
                in_frontmatter = False
            continue
        if FENCE_RE.match(line):
            in_code = not in_code
            continue
        if in_code:
            continue
        if HEADING_RE.match(line):
            continue
        if not line.strip():
            continue
        out.append((i + 1, line))
    return out


_SENT_BOUNDARY_RE = re.compile(r"[.!?](?=\s|$)")


def _sentence_span(line: str, match_start: int, match_end: int) -> tuple[int, int]:
    """Return (start, end_exclusive) of the sentence containing the trigger
    match. Sentence boundaries are `.`, `!`, or `?` followed by whitespace
    or end-of-line — so periods inside `.git`, `.gitignore`, `e.g.`, file
    extensions, and version numbers do NOT split a sentence. The end index
    is INCLUSIVE of the terminating punctuation, so substring-replacement
    later does not leave dangling periods."""
    start = 0
    for m in _SENT_BOUNDARY_RE.finditer(line, 0, match_start):
        start = m.end()  # one past the period
    # Skip leading whitespace.
    while start < match_start and line[start].isspace():
        start += 1
    end = len(line)
    m_end = _SENT_BOUNDARY_RE.search(line, match_end)
    if m_end:
        end = m_end.end()  # include the terminating punctuation
    return start, end


def find_candidates(body: str) -> list[dict[str, Any]]:
    """Deterministic pass. Returns a list of candidate flag records."""
    hits: list[dict[str, Any]] = []
    for line_no, line in split_into_scoped_lines(body):
        # Work sentence-by-sentence inside the line.
        # Tables and list markers are preserved so context is readable.
        for trigger_label, pattern in TRIGGERS:
            m = pattern.search(line)
            if not m:
                continue
            # Whitelisted-hedge suppression: if the SAME sentence carries
            # a hedging word, don't flag.
            sent_start, sent_end = _sentence_span(line, m.start(), m.end())
            sentence = line[sent_start:sent_end].strip()
            if HEDGE_WHITELIST_RE.search(sentence):
                continue
            # Negation right before the trigger: the sentence is already
            # hedging ("doesn't always work", "not universal").
            prefix = line[max(0, m.start() - 50):m.start()]
            if NEGATION_BEFORE_RE.search(prefix):
                continue
            hits.append({
                "line": line_no,
                "trigger": trigger_label,
                "match": m.group(0),
                "sentence": sentence,
                "raw_line": line,
            })
    # De-dupe: same (line, match_span) only once.
    seen: set[tuple[int, str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for h in hits:
        key = (h["line"], h["match"].lower(), h["sentence"][:80])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(h)
    return deduped


# ---- LLM verdict pass -----------------------------------------------------

LLM_PROMPT_TEMPLATE = """You are the overstatement-audit step of the KubeDojo
content pipeline. You receive a SINGLE sentence from a module and a short
surrounding context. Decide whether the sentence is overstated, and if so,
propose a softened rewrite that preserves teaching intent.

## Rules

- `overstated` if the claim is absolute ("always", "never", "first ever",
  "universal", "cancels anything") in a domain where edge cases exist. Things
  that are genuinely universal (math identities, language keywords) are NOT
  overstated.
- `acceptable` if the absolute-seeming language is bounded by context
  (e.g., "in this module" + "always"), hedged elsewhere in the sentence,
  or simply not a factual overclaim.
- `not_a_claim` if the sentence is a question, imperative, code comment,
  or teaching analogy rather than a factual assertion.

If `overstated`, `suggested_rewrite` MUST:
- Preserve the pedagogical point.
- Replace the absolute language with accurate hedging ("usually",
  "in most cases", "for the common beginner case").
- Be a DROP-IN replacement for `sentence` (same sentence count, same
  topic, same voice — the orchestrator substring-swaps it).

## Output

Return ONE JSON object. No preamble, no markdown fences.

{{
  "verdict": "overstated" | "acceptable" | "not_a_claim",
  "reason": "<one short sentence>",
  "suggested_rewrite": "<full replacement sentence, or null>"
}}

## Sentence

{sentence}

## Surrounding context (paragraph)

{context}

## Trigger pattern that flagged this sentence

{trigger}

Return the JSON object now.
"""


def build_llm_prompt(sentence: str, context: str, trigger: str) -> str:
    return LLM_PROMPT_TEMPLATE.format(
        sentence=sentence, context=context, trigger=trigger,
    )


def llm_verdict(sentence: str, context: str, trigger: str,
                agent: str = "codex", task_id: str | None = None) -> dict[str, Any]:
    # Lazy import to avoid pulling in heavy deps when --llm isn't used.
    from citation_backfill import (  # type: ignore
        dispatch_codex, dispatch_gemini, parse_agent_response,
    )
    prompt = build_llm_prompt(sentence, context, trigger)
    if agent == "codex":
        ok, raw = dispatch_codex(prompt, task_id=task_id or "overstatement-audit")
    elif agent == "gemini":
        ok, raw = dispatch_gemini(prompt)
    else:
        return {"verdict": "error", "reason": f"unknown_agent:{agent}"}
    if not ok:
        return {"verdict": "error", "reason": f"dispatch_failed: {raw[-200:]}"}
    try:
        return parse_agent_response(raw)
    except Exception as exc:  # noqa: BLE001
        return {"verdict": "error", "reason": f"parse_failed: {exc}"}


def paragraph_around(body: str, line_no: int, radius: int = 3) -> str:
    lines = body.splitlines()
    lo = max(0, line_no - 1 - radius)
    hi = min(len(lines), line_no + radius)
    return "\n".join(lines[lo:hi])


# ---- batched LLM verdict pass --------------------------------------------

BATCH_LLM_PROMPT_TEMPLATE = """You are the overstatement-audit step of the
KubeDojo content pipeline. You receive a LIST of sentences flagged by a
deterministic absolute-claim detector. For EACH sentence, decide whether
it is overstated and, if so, propose a softened drop-in rewrite.

## Verdict rules (per item)

- `overstated` if the claim is absolute ("always", "never", "first ever",
  "universal", "cancels anything") in a domain where edge cases exist.
  Things that are genuinely universal (math identities, language keywords)
  are NOT overstated.
- `acceptable` if the absolute-seeming language is bounded by context
  (e.g., "in this module" + "always"), hedged elsewhere in the sentence,
  or simply not a factual overclaim.
- `not_a_claim` if the sentence is a question, imperative, code comment,
  or teaching analogy.

## suggested_rewrite rules (when verdict=overstated)

- Preserve the pedagogical point.
- Replace the absolute language with accurate hedging ("usually", "in
  most cases", "for the common beginner case").
- MUST be a DROP-IN replacement for the SAME `sentence` text. Same
  ending punctuation. Same surrounding voice. The orchestrator will
  literally substring-swap `sentence` for `suggested_rewrite` — keep
  punctuation aligned so the swap doesn't introduce `..` or dangling
  fragments.
- Otherwise, set to null.

## Output (STRICT)

Return ONE JSON object, no preamble, no markdown fences:

{{
  "verdicts": [
    {{
      "index": 0,
      "verdict": "overstated" | "acceptable" | "not_a_claim",
      "reason": "<one short sentence>",
      "suggested_rewrite": "<full replacement sentence, or null>"
    }}
  ]
}}

The `verdicts` array MUST contain exactly {count} items, one per input
candidate, in the SAME ORDER as the input (matched by `index`).

## Module title

{module_title}

## Candidates

{candidates_block}

Return the JSON object now.
"""


def _format_candidates_block(items: list[dict[str, Any]]) -> str:
    parts = []
    for i, c in enumerate(items):
        parts.append(
            f"### index {i}\n"
            f"- trigger: `{c['trigger']}`\n"
            f"- line {c['line']}\n"
            f"- sentence: {c['sentence']!r}\n"
            f"- context (paragraph):\n```\n{c['context']}\n```\n"
        )
    return "\n".join(parts)


def batched_llm_verdicts(candidates: list[dict[str, Any]], *,
                         module_title: str, agent: str = "codex",
                         task_id: str | None = None) -> list[dict[str, Any]]:
    """Dispatch ONE LLM call covering every candidate. Returns a verdict
    list aligned to the input order. Falls back to per-call mode for
    individual items the LLM omitted or returned malformed."""
    if not candidates:
        return []
    from citation_backfill import (  # type: ignore
        dispatch_codex, dispatch_gemini, parse_agent_response,
    )
    prompt = BATCH_LLM_PROMPT_TEMPLATE.format(
        count=len(candidates),
        module_title=module_title,
        candidates_block=_format_candidates_block(candidates),
    )
    if agent == "codex":
        ok, raw = dispatch_codex(prompt, task_id=task_id or "overstatement-batch")
    elif agent == "gemini":
        ok, raw = dispatch_gemini(prompt)
    else:
        return [{"verdict": "error", "reason": f"unknown_agent:{agent}"}
                for _ in candidates]
    if not ok:
        return [{"verdict": "error", "reason": f"dispatch_failed: {raw[-160:]}"}
                for _ in candidates]
    try:
        parsed = parse_agent_response(raw)
    except Exception as exc:  # noqa: BLE001
        return [{"verdict": "error", "reason": f"parse_failed: {exc}"}
                for _ in candidates]

    verdicts_in = parsed.get("verdicts") or parsed.get("results") or []
    by_index: dict[int, dict[str, Any]] = {}
    for v in verdicts_in:
        if isinstance(v, dict) and isinstance(v.get("index"), int):
            by_index[int(v["index"])] = v
    out: list[dict[str, Any]] = []
    missing_indices: list[int] = []
    for i, _ in enumerate(candidates):
        v = by_index.get(i)
        if v is None:
            missing_indices.append(i)
            out.append({"verdict": "error", "reason": "missing_in_batch"})
        else:
            out.append(v)
    # Fallback: per-call retry for any candidates the batch missed.
    for i in missing_indices:
        c = candidates[i]
        out[i] = llm_verdict(c["sentence"], c["context"], c["trigger"],
                             agent=agent,
                             task_id=f"overstate-fallback-{i}")
    return out


# ---- CLI -----------------------------------------------------------------


def audit_file(path: Path, *, use_llm: bool, agent: str,
               batch: bool = True) -> dict[str, Any]:
    body = path.read_text(encoding="utf-8")
    candidates = find_candidates(body)
    if use_llm and candidates:
        # Materialize per-candidate context once so batched + fallback
        # paths share the same input shape.
        for c in candidates:
            c["context"] = paragraph_around(body, c["line"])
        if batch:
            module_title = _module_title(body, path)
            verdicts = batched_llm_verdicts(
                candidates, module_title=module_title, agent=agent,
                task_id=f"overstate-{path.stem}",
            )
            for c, v in zip(candidates, verdicts, strict=False):
                c["verdict"] = v
        else:
            for c in candidates:
                verdict = llm_verdict(c["sentence"], c["context"], c["trigger"],
                                      agent=agent,
                                      task_id=f"overstate-{path.stem}-L{c['line']}")
                c["verdict"] = verdict
    return {
        "path": str(path),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def _module_title(body: str, path: Path) -> str:
    m = re.search(r"^title:\s*[\"']?([^\"'\n]+)[\"']?\s*$", body, re.MULTILINE)
    return m.group(1).strip() if m else path.stem


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Overstatement-detection gate")
    p.add_argument("paths", nargs="+", help="module .md paths")
    p.add_argument("--llm", action="store_true",
                   help="dispatch each candidate to Codex for verdict")
    p.add_argument("--agent", default="codex", choices=["codex", "gemini"])
    p.add_argument("--json", action="store_true", help="emit JSON (default)")
    p.add_argument("--text", action="store_true",
                   help="emit human-readable table instead of JSON")
    args = p.parse_args(argv)

    results = []
    for raw in args.paths:
        path = Path(raw)
        if not path.exists():
            results.append({"path": raw, "error": "missing_file"})
            continue
        results.append(audit_file(path, use_llm=args.llm, agent=args.agent))

    if args.text:
        for r in results:
            print(f"=== {r.get('path')} — {r.get('candidate_count', 0)} candidates ===")
            for c in r.get("candidates") or []:
                marker = c.get("verdict", {}).get("verdict") if args.llm else ""
                print(f"L{c['line']:<4}  [{c['trigger']:18s}] {marker:>12s}  {c['match']}")
                print(f"       > {c['sentence'][:200]}")
                if args.llm and c.get("verdict", {}).get("suggested_rewrite"):
                    print(f"       ~ {c['verdict']['suggested_rewrite'][:200]}")
    else:
        print(json.dumps(results, indent=2, ensure_ascii=False))

    any_hits = any((r.get("candidate_count") or 0) > 0 for r in results)
    return 1 if any_hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
