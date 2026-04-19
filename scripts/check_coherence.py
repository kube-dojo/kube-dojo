#!/usr/bin/env python3
"""Gate D — topical-coherence auditor.

For each section (H2-bounded block) of a module, an LLM reads the
whole section in context and flags paragraphs that don't belong to
the section's topic. Would have caught the GitLab-DB-outage paragraph
sitting inside the RAM/swapping section of ZTT 0.1.

Section-level batching (not paragraph-level) keeps LLM dispatch count
O(sections per module) instead of O(paragraphs per module) — a
typical KubeDojo module has 5-10 sections and 30-80 paragraphs.

Skipped regions: frontmatter, fenced code blocks, Mermaid, tables,
quiz <details>, and the `## Sources` section.

Usage:
    python scripts/check_coherence.py path/to/module.md
    python scripts/check_coherence.py path/to/module.md --agent gemini
    python scripts/check_coherence.py path/to/module.md --dry-run
    python scripts/check_coherence.py path/to/module.md --text
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from citation_backfill import (  # type: ignore  # noqa: E402
    dispatch_codex, dispatch_gemini, parse_agent_response,
)


H2_RE = re.compile(r"^##\s+(?!Sources\s*$)(.+?)\s*$", re.MULTILINE)
SOURCES_HEADING_RE = re.compile(r"^##\s+Sources\s*$", re.MULTILINE)
FENCE_RE = re.compile(r"^```")
FRONTMATTER_DELIM_RE = re.compile(r"^---\s*$")


def split_into_sections(body: str) -> list[dict[str, Any]]:
    """Return [{heading, start_line, end_line, content}, ...] for
    every H2 section, stopping before '## Sources'."""
    sources_idx = None
    m = SOURCES_HEADING_RE.search(body)
    if m:
        sources_idx = m.start()

    sections: list[dict[str, Any]] = []
    heads = list(H2_RE.finditer(body))
    for i, head in enumerate(heads):
        start = head.start()
        if sources_idx is not None and start >= sources_idx:
            break
        end = heads[i + 1].start() if i + 1 < len(heads) else (sources_idx or len(body))
        content = body[start:end].rstrip()
        start_line = body[:start].count("\n") + 1
        end_line = start_line + content.count("\n")
        sections.append({
            "heading": head.group(1).strip(),
            "start_line": start_line,
            "end_line": end_line,
            "content": content,
        })
    return sections


COHERENCE_PROMPT_TEMPLATE = """You are the topical-coherence gate of the
KubeDojo content pipeline. You receive ONE section of a module (bounded
by an H2 heading). Your job: identify paragraphs within the section that
do NOT belong — topically disconnected tangents, dropped-in war stories
that don't relate to the section's subject, or claims that jump to a
different domain.

Module context:
- Module title: {module_title}
- Module audience: {audience}

## Rules

- `on_topic` — paragraph advances the section's teaching arc. Keep.
- `off_topic` — paragraph introduces a subject that doesn't connect to
  the section's heading or its preceding paragraph. Examples: a
  database-outage war story in a RAM/swapping section; a pricing
  discussion in a CPU-architecture section.
- `tangential_but_acceptable` — paragraph slightly digresses but ties
  back (e.g., a history sidebar inside a "how X works" section). Keep.

Do NOT flag:
- Analogies, pedagogical framing, or warm language.
- Forward-references or foreshadowing ("we'll see this later").
- Hands-on callouts (Pause-and-predict, Stop-and-think).
- Example code walkthroughs.

For `off_topic`, propose in `suggested_action` one of:
- `move_to_section:<other section heading>`  if it fits elsewhere
- `delete` if it doesn't belong anywhere in this module
- `rewrite_to_fit` if a small rewrite would bridge it to the topic

## Output

Return ONE JSON object, no preamble, no markdown fences:

{{
  "section": "<section heading>",
  "paragraphs_flagged": [
    {{
      "excerpt": "<first ~200 chars of the offending paragraph>",
      "verdict": "off_topic" | "tangential_but_acceptable",
      "reason": "<one short sentence>",
      "suggested_action": "<as above, or null>"
    }}
  ]
}}

If no paragraphs are flagged, return `"paragraphs_flagged": []`.

## Section content

{section_content}

Return the JSON now.
"""


def build_coherence_prompt(module_title: str, audience: str,
                           section_content: str) -> str:
    return COHERENCE_PROMPT_TEMPLATE.format(
        module_title=module_title, audience=audience,
        section_content=section_content,
    )


def audience_for(path: Path) -> str:
    # Heuristic — matches the citation_backfill audience mapping.
    p = str(path).replace("\\", "/")
    if "prerequisites/zero-to-terminal" in p:
        return "absolute_beginner"
    if "prerequisites/" in p or "foundations/" in p or "kcna/" in p:
        return "beginner"
    if "cka/" in p or "ckad/" in p or "cloud/" in p:
        return "intermediate"
    return "advanced"


def module_title_for(body: str, path: Path) -> str:
    # Try frontmatter `title:`.
    m = re.search(r"^title:\s*[\"']?([^\"'\n]+)[\"']?\s*$", body, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return path.stem


BATCH_COHERENCE_PROMPT_TEMPLATE = """You are the topical-coherence gate of
the KubeDojo content pipeline. You receive ALL non-trivial sections of a
single module. For EACH section, identify paragraphs that don't belong —
topically disconnected tangents, dropped-in war stories that don't relate
to the section's subject, or claims that jump to a different domain.

Module context:
- Module title: {module_title}
- Module audience: {audience}

## Per-paragraph rules

- `on_topic` — paragraph advances the section's teaching arc. Keep.
- `off_topic` — paragraph introduces a subject that doesn't connect to
  the section's heading or its preceding paragraph.
- `tangential_but_acceptable` — slightly digresses but ties back. Keep.

Do NOT flag analogies, pedagogical framing, forward-references,
hands-on callouts, or example code walkthroughs.

For `off_topic`, propose `suggested_action`:
- `move_to_section:<other section heading>` if it fits elsewhere
- `delete` if it doesn't belong anywhere in this module
- `rewrite_to_fit` if a small rewrite would bridge it

## Output (STRICT)

Return ONE JSON object, no preamble, no markdown fences:

{{
  "sections": [
    {{
      "section_index": 0,
      "section": "<heading from input>",
      "paragraphs_flagged": [
        {{
          "excerpt": "<first ~200 chars of offending paragraph>",
          "verdict": "off_topic" | "tangential_but_acceptable",
          "reason": "<one short sentence>",
          "suggested_action": "<as above, or null>"
        }}
      ]
    }}
  ]
}}

Include EVERY input section in the `sections` array (in order, by
`section_index`), even when `paragraphs_flagged` is empty.

## Sections

{sections_block}

Return the JSON now.
"""


def _format_sections_block(sections: list[dict[str, Any]]) -> str:
    parts = []
    for i, s in enumerate(sections):
        parts.append(
            f"### section_index {i}: {s['heading']}\n"
            f"```\n{s['content']}\n```\n"
        )
    return "\n".join(parts)


def _dispatch_one(prompt: str, *, agent: str, task_id: str) -> tuple[bool, str]:
    if agent == "codex":
        return dispatch_codex(prompt, task_id=task_id)
    if agent == "gemini":
        return dispatch_gemini(prompt)
    return False, f"unknown_agent:{agent}"


def check_coherence(path: Path, *, agent: str = "gemini",
                    dry_run: bool = False, batch: bool = True) -> dict[str, Any]:
    body = path.read_text(encoding="utf-8")
    sections = split_into_sections(body)
    module_title = module_title_for(body, path)
    audience = audience_for(path)

    # Skip tiny sections regardless of mode (heading + 1 intro line).
    auditable = [s for s in sections if len(s["content"]) >= 200]

    if dry_run:
        return {"path": str(path),
                "module_title": module_title,
                "audience": audience,
                "section_count": len(sections),
                "sections": [{"heading": s["heading"],
                              "start_line": s["start_line"],
                              "char_count": len(s["content"])} for s in sections]}

    findings: list[dict[str, Any]] = []

    if batch and auditable:
        prompt = BATCH_COHERENCE_PROMPT_TEMPLATE.format(
            module_title=module_title, audience=audience,
            sections_block=_format_sections_block(auditable),
        )
        ts = _dt.datetime.now(_dt.UTC).strftime("%H%M%SZ")
        task_id = f"coherence-batch-{path.stem}-{ts}"
        ok, raw = _dispatch_one(prompt, agent=agent, task_id=task_id)
        if not ok:
            findings.append({"section": "(batch)",
                             "error": f"dispatch_failed:{raw[-200:]}"})
        else:
            try:
                parsed = parse_agent_response(raw)
            except Exception as exc:  # noqa: BLE001
                parsed = {"sections": []}
                findings.append({"section": "(batch)",
                                 "error": f"parse_failed:{exc}"})
            sections_in = parsed.get("sections") or []
            by_idx = {int(s.get("section_index", -1)): s
                      for s in sections_in if isinstance(s, dict)}
            for i, s in enumerate(auditable):
                hit = by_idx.get(i)
                if hit is None:
                    findings.append({"section": s["heading"],
                                     "error": "missing_in_batch"})
                    continue
                for f in (hit.get("paragraphs_flagged") or []):
                    f["section"] = s["heading"]
                    f["section_start_line"] = s["start_line"]
                    findings.append(f)
    else:
        for s in auditable:
            prompt = build_coherence_prompt(module_title, audience, s["content"])
            ts = _dt.datetime.now(_dt.UTC).strftime("%H%M%SZ")
            task_id = (f"coherence-{path.stem}-"
                       f"{re.sub(r'[^a-z0-9]+', '-', s['heading'].lower())[:30]}-{ts}")
            ok, raw = _dispatch_one(prompt, agent=agent, task_id=task_id)
            if not ok:
                findings.append({"section": s["heading"],
                                 "error": f"dispatch_failed:{raw[-200:]}"})
                continue
            try:
                parsed = parse_agent_response(raw)
            except Exception as exc:  # noqa: BLE001
                findings.append({"section": s["heading"],
                                 "error": f"parse_failed:{exc}"})
                continue
            flagged = parsed.get("paragraphs_flagged") or []
            for f in flagged:
                f["section"] = s["heading"]
                f["section_start_line"] = s["start_line"]
                findings.append(f)

    return {"path": str(path),
            "module_title": module_title,
            "audience": audience,
            "section_count": len(sections),
            "flag_count": len(findings),
            "findings": findings}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gate D — topical-coherence auditor")
    p.add_argument("paths", nargs="+")
    p.add_argument("--agent", default="gemini", choices=["codex", "gemini"])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--text", action="store_true")
    args = p.parse_args(argv)

    results = []
    for raw in args.paths:
        path = Path(raw)
        if not path.exists():
            results.append({"path": raw, "error": "missing_file"})
            continue
        results.append(check_coherence(path, agent=args.agent, dry_run=args.dry_run))

    if args.text:
        for r in results:
            print(f"=== {r.get('path')} — "
                  f"{r.get('flag_count', 0)} flag(s) across "
                  f"{r.get('section_count', 0)} section(s) ===")
            for f in r.get("findings") or []:
                verdict = f.get("verdict", "?")
                section = f.get("section", "?")
                print(f"  [{verdict}] in section '{section}'")
                print(f"    reason: {(f.get('reason') or '')[:180]}")
                print(f"    excerpt: {(f.get('excerpt') or '')[:180]}")
                if f.get("suggested_action"):
                    print(f"    action: {f['suggested_action']}")
    else:
        print(json.dumps(results, indent=2, ensure_ascii=False))

    any_hits = any((r.get("flag_count") or 0) > 0 for r in results)
    return 1 if any_hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
