#!/usr/bin/env python3
"""Gate C — unsourced-assertion detector.

Flags paragraphs that LOOK factual (dated, named-entity, statistical,
war-story framed) but carry no inline citation. Would have caught the
Pixar Toy Story 2 war story in ZTT 0.3.

Two-stage like the overstatement gate:
1. Deterministic: scan paragraphs; combine factual-signal patterns
   AND absence-of-citation to identify candidates.
2. LLM (--llm): per-candidate verdict `needs_citation` |
   `teaching_hypothetical` | `not_a_claim` plus a proposed search
   hint.

Skipped: fenced code, Mermaid, frontmatter, tables, quiz <details>
(they test recall — teacher writes the "right" answer), and the
existing `## Sources` section.

Usage:
    python scripts/check_unsourced.py path/to/module.md
    python scripts/check_unsourced.py path/to/module.md --text
    python scripts/check_unsourced.py path/to/module.md --llm
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))


# Factual-signal patterns. A paragraph that matches any of these
# raises suspicion — if it ALSO lacks any inline citation, it becomes
# a candidate.
FACTUAL_SIGNALS: list[tuple[str, re.Pattern[str]]] = [
    ("dated_year",          re.compile(r"\bIn\s+(19|20)\d{2}\b")),
    ("year_reference",      re.compile(r"\b(19|20)\d{2}\b")),
    ("named_incident",      re.compile(r"\b(outage|breach|incident|accident|attack|postmortem|leaked|deleted\s+the|wiped\s+the)\b", re.I)),
    ("war_story_prefix",    re.compile(r"^\s*\*{0,2}(Real[- ]?World\s+War\s+Story|War\s+Story|Case\s+Study)\s*:?\*{0,2}", re.I | re.M)),
    ("oldest_first_only",   re.compile(r"\b(the\s+oldest|oldest\s+surviving|first\s+ever|the\s+first\s+(?:commercial|computer|programming|operating|Unix|version))\b", re.I)),
    ("named_company_cap",   re.compile(r"\b(GitLab|Google|Apple|Microsoft|Amazon|AWS|Pixar|Facebook|Meta|Twitter|Netflix|Uber|Stripe|Cloudflare|NASA|IBM|Oracle|Red\s*Hat|SUSE|Canonical|Docker|Kubernetes)\b")),
    ("statistic_percent",   re.compile(r"\b\d{1,3}(?:\.\d+)?\s*%\b")),
    ("statistic_large_num", re.compile(r"\b\d{3,}(?:,\d{3})*(?:\.\d+)?\s*(?:users|customers|servers|dollars|employees|people|tons|miles|kilometers)\b", re.I)),
    ("price_usd",           re.compile(r"\$\s*\d+(?:\.\d+)?(?:\s*\/\s*(?:hour|hr|month|mo|year|yr))?")),
    ("attribution",         re.compile(r"\baccording\s+to\b|\breports?\s+say|studies?\s+show|researchers?\s+found", re.I)),
    ("vendor_since",        re.compile(r"\b(since|as\s+of)\s+(version|release)?\s*\d", re.I)),
    ("named_standard",      re.compile(r"\b(RFC|KEP|CVE|NIST|ISO|IEC|OWASP|FedRAMP|GDPR|HIPAA|PCI\s*DSS)\s*[-–—]?\s*\d", re.I)),
]

# These patterns mean "this paragraph already has a citation" — skip it.
CITATION_PATTERNS = [
    re.compile(r"\[[^\]]+\]\(https?://[^)]+\)"),    # inline markdown link
    re.compile(r"^\s*Source\s*:", re.I | re.M),     # Source: line
    re.compile(r"\[\^[^\]]+\]"),                     # footnote ref
]


FENCE_RE = re.compile(r"^```")
MERMAID_START_RE = re.compile(r"^```mermaid")
HEADING_RE = re.compile(r"^#{1,6}\s")
SOURCES_HEADING_RE = re.compile(r"^##\s+Sources\s*$", re.MULTILINE)
DETAILS_OPEN_RE = re.compile(r"<details\b", re.I)
DETAILS_CLOSE_RE = re.compile(r"</details>", re.I)
TABLE_ROW_RE = re.compile(r"^\s*\|")
ADMONITION_RE = re.compile(r"^\s*:::|^\s*>\s")


def iter_paragraphs(body: str) -> list[tuple[int, str]]:
    """Yield (start_line, paragraph_text) tuples for prose paragraphs
    outside of code/mermaid/tables/frontmatter/sources/details."""
    out: list[tuple[int, str]] = []
    in_code = False
    in_frontmatter = False
    in_details = False
    lines = body.splitlines()
    sources_idx = None
    m = SOURCES_HEADING_RE.search(body)
    if m:
        sources_idx = body[: m.start()].count("\n")

    buf: list[str] = []
    buf_start = 0

    def flush():
        nonlocal buf, buf_start
        if buf:
            paragraph = "\n".join(buf).strip()
            if paragraph:
                out.append((buf_start, paragraph))
        buf = []

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
            flush()
            in_code = not in_code
            continue
        if in_code:
            continue
        if DETAILS_OPEN_RE.search(line):
            flush()
            in_details = True
            continue
        if DETAILS_CLOSE_RE.search(line):
            in_details = False
            flush()
            continue
        if in_details:
            continue
        if HEADING_RE.match(line):
            flush()
            continue
        if TABLE_ROW_RE.match(line):
            flush()
            continue
        if not line.strip():
            flush()
            continue
        if not buf:
            buf_start = i + 1
        buf.append(line)
    flush()
    return out


def paragraph_has_citation(paragraph: str) -> bool:
    return any(p.search(paragraph) for p in CITATION_PATTERNS)


def score_paragraph(paragraph: str) -> list[str]:
    """Return the list of factual-signal labels matched in a paragraph."""
    hits: list[str] = []
    for label, pat in FACTUAL_SIGNALS:
        if pat.search(paragraph):
            hits.append(label)
    return hits


STRONG_SIGNALS = {
    "dated_year", "war_story_prefix", "statistic_percent",
    "statistic_large_num", "price_usd", "attribution",
    "vendor_since", "named_standard", "oldest_first_only",
    "named_incident",
}


def find_candidates(body: str, *, aggressive: bool = False) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for line_no, paragraph in iter_paragraphs(body):
        signals = score_paragraph(paragraph)
        if not signals:
            continue
        if paragraph_has_citation(paragraph):
            continue
        # Skip single-signal hits on weak patterns (just mentioning a
        # company name or a bare year isn't a factual assertion).
        # Require at least one strong signal unless --aggressive.
        if not aggressive:
            if not any(s in STRONG_SIGNALS for s in signals):
                continue
        # Skip admonition-only prompts like "Stop and think" callouts —
        # those are pedagogical, not factual assertions.
        lines = paragraph.splitlines()
        if all(ADMONITION_RE.match(line) for line in lines):
            continue
        candidates.append({
            "line": line_no,
            "signals": signals,
            "excerpt": paragraph[:300] + ("…" if len(paragraph) > 300 else ""),
            "length": len(paragraph),
            "paragraph": paragraph,
        })
    return candidates


# ---- LLM verdict ---------------------------------------------------------

LLM_PROMPT_TEMPLATE = """You are the unsourced-assertion gate of the KubeDojo
content pipeline. You receive a paragraph from a module that pattern-matched
on factual signals (dated year, named company, statistic, war-story prefix,
etc.) but has NO inline citation.

Decide whether this paragraph needs a citation.

## Rules

- `needs_citation` — the paragraph states a real-world fact that a reader
  could verify against a source. Examples: war stories with named companies
  and dates, statistics with specific numbers, attributed standards.
- `teaching_hypothetical` — the paragraph is illustrative ("a team might
  pay $400/month" / "imagine you accidentally delete..."). No citation
  needed IF the hypothetical framing is already explicit. If the text
  presents a specific dated event as fact, use `needs_citation` instead.
- `not_a_claim` — prose, analogy, instruction, or framing, no factual
  assertion.

If `needs_citation`, in `search_hint` propose 2-3 short search queries
a researcher could use to find the primary source.

## Output

Return ONE JSON object, no preamble, no markdown fences:

{{
  "verdict": "needs_citation" | "teaching_hypothetical" | "not_a_claim",
  "reason": "<one short sentence>",
  "search_hint": ["query 1", "query 2"] | null
}}

## Paragraph

{paragraph}

Return the JSON now.
"""


def llm_verdict(paragraph: str, *, agent: str = "codex",
                task_id: str | None = None) -> dict[str, Any]:
    from citation_backfill import (  # type: ignore
        dispatch_codex, dispatch_gemini, parse_agent_response,
    )
    prompt = LLM_PROMPT_TEMPLATE.format(paragraph=paragraph)
    if agent == "codex":
        ok, raw = dispatch_codex(prompt, task_id=task_id or "unsourced-audit")
    elif agent == "gemini":
        ok, raw = dispatch_gemini(prompt)
    else:
        return {"verdict": "error", "reason": f"unknown_agent:{agent}"}
    if not ok:
        return {"verdict": "error", "reason": f"dispatch_failed:{raw[-200:]}"}
    try:
        return parse_agent_response(raw)
    except Exception as exc:  # noqa: BLE001
        return {"verdict": "error", "reason": f"parse_failed:{exc}"}


BATCH_LLM_PROMPT_TEMPLATE = """You are the unsourced-assertion gate of the
KubeDojo content pipeline. You receive a LIST of paragraphs that pattern-
matched on factual signals (dated year, named company, statistic,
war-story prefix, etc.) but carry NO inline citation. For EACH paragraph,
decide whether it needs a citation.

## Verdict rules (per item)

- `needs_citation` — the paragraph states a real-world fact a reader could
  verify against a source. Examples: war stories with named companies and
  dates, statistics with specific numbers, attributed standards.
- `teaching_hypothetical` — illustrative ("a team might pay $400/month",
  "imagine you accidentally delete..."). No citation needed IF the framing
  is already explicit. If the text presents a specific dated event as
  fact, use `needs_citation` instead.
- `not_a_claim` — prose, analogy, instruction, framing.

For each `needs_citation`, propose 2-3 short search queries in
`search_hint`.

## Output (STRICT)

Return ONE JSON object, no preamble, no markdown fences:

{{
  "verdicts": [
    {{
      "index": 0,
      "verdict": "needs_citation" | "teaching_hypothetical" | "not_a_claim",
      "reason": "<one short sentence>",
      "search_hint": ["query 1", "query 2"] | null
    }}
  ]
}}

The `verdicts` array MUST contain exactly {count} items, in the SAME
ORDER as the input (matched by `index`).

## Paragraphs

{paragraphs_block}

Return the JSON now.
"""


def _format_paragraphs_block(items: list[dict[str, Any]]) -> str:
    parts = []
    for i, c in enumerate(items):
        parts.append(
            f"### index {i}\n"
            f"- line {c['line']}\n"
            f"- signals: {','.join(c['signals'])}\n"
            f"- paragraph:\n```\n{c['paragraph']}\n```\n"
        )
    return "\n".join(parts)


def batched_llm_verdicts(items: list[dict[str, Any]], *,
                         agent: str = "codex",
                         task_id: str | None = None) -> list[dict[str, Any]]:
    if not items:
        return []
    from citation_backfill import (  # type: ignore
        dispatch_codex, dispatch_gemini, parse_agent_response,
    )
    prompt = BATCH_LLM_PROMPT_TEMPLATE.format(
        count=len(items),
        paragraphs_block=_format_paragraphs_block(items),
    )
    if agent == "codex":
        ok, raw = dispatch_codex(prompt, task_id=task_id or "unsourced-batch")
    elif agent == "gemini":
        ok, raw = dispatch_gemini(prompt)
    else:
        return [{"verdict": "error", "reason": f"unknown_agent:{agent}"}
                for _ in items]
    if not ok:
        return [{"verdict": "error", "reason": f"dispatch_failed:{raw[-160:]}"}
                for _ in items]
    try:
        parsed = parse_agent_response(raw)
    except Exception as exc:  # noqa: BLE001
        return [{"verdict": "error", "reason": f"parse_failed:{exc}"}
                for _ in items]

    verdicts_in = parsed.get("verdicts") or parsed.get("results") or []
    by_index: dict[int, dict[str, Any]] = {}
    for v in verdicts_in:
        if isinstance(v, dict) and isinstance(v.get("index"), int):
            by_index[int(v["index"])] = v
    out: list[dict[str, Any]] = []
    missing: list[int] = []
    for i in range(len(items)):
        v = by_index.get(i)
        if v is None:
            missing.append(i)
            out.append({"verdict": "error", "reason": "missing_in_batch"})
        else:
            out.append(v)
    for i in missing:
        out[i] = llm_verdict(items[i]["paragraph"], agent=agent,
                             task_id=f"unsourced-fallback-{i}")
    return out


# ---- CLI -----------------------------------------------------------------


def audit_file(path: Path, *, use_llm: bool, agent: str,
               aggressive: bool = False, batch: bool = True) -> dict[str, Any]:
    body = path.read_text(encoding="utf-8")
    candidates = find_candidates(body, aggressive=aggressive)
    if use_llm and candidates:
        if batch:
            verdicts = batched_llm_verdicts(
                candidates, agent=agent, task_id=f"unsourced-{path.stem}",
            )
            for c, v in zip(candidates, verdicts, strict=False):
                c["verdict"] = v
        else:
            for c in candidates:
                verdict = llm_verdict(c["paragraph"], agent=agent,
                                      task_id=f"unsourced-{path.stem}-L{c['line']}")
                c["verdict"] = verdict
    # Strip bulky paragraph field from the public output.
    for c in candidates:
        c.pop("paragraph", None)
    return {"path": str(path),
            "candidate_count": len(candidates),
            "candidates": candidates}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gate C — unsourced-assertion detector")
    p.add_argument("paths", nargs="+")
    p.add_argument("--llm", action="store_true")
    p.add_argument("--agent", default="codex", choices=["codex", "gemini"])
    p.add_argument("--text", action="store_true")
    p.add_argument("--aggressive", action="store_true",
                   help="flag weak single-signal paragraphs too")
    args = p.parse_args(argv)

    results = []
    for raw in args.paths:
        path = Path(raw)
        if not path.exists():
            results.append({"path": raw, "error": "missing_file"})
            continue
        results.append(audit_file(path, use_llm=args.llm, agent=args.agent,
                                  aggressive=args.aggressive))

    if args.text:
        for r in results:
            print(f"=== {r.get('path')} — {r.get('candidate_count', 0)} candidates ===")
            for c in r.get("candidates") or []:
                marker = ""
                if args.llm and c.get("verdict"):
                    marker = c["verdict"].get("verdict", "")
                print(f"L{c['line']:<4}  [{','.join(c['signals'])[:40]:40s}]  {marker}")
                print(f"       > {c['excerpt'][:240]}")
    else:
        print(json.dumps(results, indent=2, ensure_ascii=False))

    any_hits = any((r.get("candidate_count") or 0) > 0 for r in results)
    return 1 if any_hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
