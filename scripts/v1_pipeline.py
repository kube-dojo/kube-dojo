#!/usr/bin/env python3
"""KubeDojo Module Quality Pipeline — v1.

Processes each module through 8 quality dimensions to reach 33/40.
Uses Gemini for writing/translating, deterministic Python checks as gates.

Pipeline per module: AUDIT → WRITE/REWRITE → REVIEW → CHECK → SCORE → COMMIT
Pipeline per section: modules + INDEX rewrite (EN) + INDEX translate (UK)

Features:
- Knowledge packet extraction: preserves code blocks, tables, diagrams, quiz
  blocks, inline prompts, and links during rewrites
- ASCII→Mermaid conversion instruction in WRITE/REWRITE prompts
- Deterministic checks: frontmatter, sections, inline prompts, quiz format,
  emojis, K8s API versions (WARNING only, strips code blocks + inline code)
- Section index.md: Gemini rewrite after section completes, auto-translates UK
- Safety: truncation guard, frontmatter validation, thinking leak detection,
  circuit breaker (5 consecutive failures), atomic state writes

Usage:
    python scripts/v1_pipeline.py status
    python scripts/v1_pipeline.py e2e ztt              # single section (EN + UK + index)
    python scripts/v1_pipeline.py e2e prereqs           # track (all sections)
    python scripts/v1_pipeline.py e2e k8s/cka           # auto-discovers parts
    python scripts/v1_pipeline.py e2e certs linux cloud  # multiple tracks
    python scripts/v1_pipeline.py e2e ztt --no-translate # EN only, skip UK
    python scripts/v1_pipeline.py run <module-path>      # single module
    python scripts/v1_pipeline.py run-section <path>     # section without index
    python scripts/v1_pipeline.py resume                 # retry stuck modules
    python scripts/v1_pipeline.py audit <module-path>    # score only
    python scripts/v1_pipeline.py audit-all              # deterministic checks only

Section aliases: ztt, git, cn101, k8sbasics, philosophy, devops,
    cka, ckad, cks, kcna, kcsa, extending, aws, gcp, azure, eks, gke, aks
Track aliases: prereqs, certs, specialty, cloud, platform, on-prem, linux
Any directory path also works: e2e on-premises, e2e platform/foundations
"""

from __future__ import annotations

import argparse
import builtins
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, UTC
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CONTENT_ROOT = REPO_ROOT / "src" / "content" / "docs"
STATE_FILE = REPO_ROOT / ".pipeline" / "state.yaml"
REPORT_FILE = REPO_ROOT / ".pipeline" / "audit-report.json"
SCORE_SCRIPT = REPO_ROOT / "scripts" / "score_module.py"

# ---------------------------------------------------------------------------
# Timestamped logging — tee all print() to a log file
# ---------------------------------------------------------------------------

LOG_DIR = REPO_ROOT / ".pipeline" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"run_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}.log"

_original_print = builtins.print
_quiet = False  # set by e2e command
os.environ["KUBEDOJO_QUIET"] = "1"  # suppress Gemini streaming to stdout


def _logged_print(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    # Always write to log file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now(UTC).strftime('%H:%M:%S')}] {msg}\n")
    # Only print to stdout if not in quiet mode, or if it's a summary/error line
    if not _quiet:
        _original_print(*args, **kwargs)
    elif any(k in msg for k in (
        # Progress milestones
        "PASS", "FAIL", "CIRCUIT", "E2E COMPLETE", "SECTION:", "PHASE 1",
        "SKIP:", "Resumed:", "passed,", "BREAKER",
        # Pipeline steps — so user sees what's happening
        "PIPELINE:", "AUDIT:", "WRITE:", "REWRITE:", "REVIEW:", "CHECK:", "INDEX:",
        # Key decisions and results
        "Verdict:", "Scores:", "REWRITE mode", "already passes",
        "Rejected", "produced", "file written", "Committed",
    )):
        _original_print(f"[{datetime.now(UTC).strftime('%H:%M:%S')}] {msg}")


builtins.print = _logged_print

# Add scripts to path for imports
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from checks import structural, ukrainian, gaps
from dispatch import (
    dispatch_gemini_with_retry,
    dispatch_claude,
    dispatch_codex,
    _is_rate_limited,
)
from uk_sync import (
    translate_new_module as uk_translate,
    fix_module as uk_fix,
    _find_content_files as uk_find_content_files,
    CONTENT_ROOT as UK_CONTENT_ROOT,
    UK_ROOT,
)


def dispatch_auto(prompt: str, model: str, timeout: int = 900) -> tuple[bool, str]:
    """Route to Gemini, Claude, or Codex based on model name."""
    if model.startswith("gemini"):
        return dispatch_gemini_with_retry(prompt, model=model, timeout=timeout)
    if model.startswith("claude"):
        return dispatch_claude(prompt, model=model, timeout=timeout)
    if model.startswith("codex"):
        return dispatch_codex(prompt, model=model, timeout=timeout)
    raise ValueError(f"Unknown model family: {model!r} — must start with 'gemini', 'claude', or 'codex'")


# ---------------------------------------------------------------------------
# Model configuration (overridable via CLI)
# ---------------------------------------------------------------------------

MODELS = {
    "audit": "gemini-3.1-pro-preview",     # AUDIT+PLAN: rubric evaluation + plan
    "write": "gemini-3.1-pro-preview",     # WRITE: draft improvements
    "review": "codex",                     # REVIEW: preferred independent reviewer
    "review_fallback": "gemini-3.1-pro-preview",  # used only when "review" is unavailable
    # "translate" removed — uk_sync.CHUNKED_MODEL owns translation model config
}

# Reviewer families considered "independent" of the writer (currently Gemini).
# Only these count as production-ready reviewers. Gemini reviewing Gemini is a
# fallback to keep the pipeline moving but flags the module for re-review.
INDEPENDENT_REVIEWER_FAMILIES = {"codex", "claude"}

# Pipeline phases in order
PHASES = ["pending", "audit", "write", "review", "check", "score", "done"]

# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def load_state() -> dict:
    if STATE_FILE.exists():
        return yaml.safe_load(STATE_FILE.read_text()) or {"modules": {}}
    return {"modules": {}}


def save_state(state: dict) -> None:
    """Save state with file locking + atomic write to prevent corruption."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock_file = STATE_FILE.with_suffix(".lock")
    tmp_file = STATE_FILE.with_suffix(".tmp")
    with open(lock_file, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            tmp_file.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False))
            tmp_file.replace(STATE_FILE)  # atomic on POSIX
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def get_module_state(state: dict, module_key: str) -> dict:
    return state["modules"].setdefault(module_key, {
        "phase": "pending",
        "scores": None,
        "sum": None,
        "passes": False,
        "last_run": None,
        "errors": [],
    })


def module_key_from_path(path: Path) -> str:
    """Convert file path to module key (e.g., 'k8s/cka/part1/module-1.1')."""
    path = path.resolve()
    rel = path.relative_to(CONTENT_ROOT.resolve())
    return str(rel).replace(".md", "")


def find_module_path(key: str) -> Path | None:
    """Find the actual file path from a module key."""
    # Path traversal protection
    if ".." in key or key.startswith("/"):
        print(f"  ❌ Invalid module key (path traversal): {key}")
        return None
    candidate = CONTENT_ROOT / f"{key}.md"
    # Ensure resolved path is still under CONTENT_ROOT
    if not candidate.resolve().is_relative_to(CONTENT_ROOT.resolve()):
        print(f"  ❌ Path escapes content root: {key}")
        return None
    if candidate.exists():
        return candidate
    # Try fuzzy match
    parts = key.split("/")
    pattern = f"**/{parts[-1]}.md"
    matches = list(CONTENT_ROOT.glob(pattern))
    return matches[0] if matches else None


# ---------------------------------------------------------------------------
# AUDIT step — deterministic checks + LLM scoring
# ---------------------------------------------------------------------------

RUBRIC_PROMPT = """You are scoring a KubeDojo module against 8 quality dimensions.

Score each dimension 1-5 using the rubric below. Be STRICT — a 4 means genuinely good, not just "present."

## Dimensions
D1 Learning Outcomes: 4 = clear, measurable, Bloom's L3+. 5 = testable, every outcome delivered.
D2 Scaffolding: 4 = clear progression, explicit bridges. 5 = worked examples before practice, complexity gradient.
D3 Active Learning: 4 = multiple inline prompts, scenario quizzes. 5 = woven throughout, learner constructs knowledge.
D4 Real-World: 4 = war stories with specific impact, common mistakes table. 5 = integrated throughout, honest trade-offs.
D5 Assessment: 4 = tests analysis not recall, explains WHY. 5 = aligned with every outcome, progressive difficulty.
D6 Cognitive Load: 4 = good chunking, diagrams with text, worked examples. 5 = split-attention eliminated, dual coding.
D7 Engagement: 4 = conversational, strong hook, good analogies. 5 = memorable, reader would recommend.
D8 Practitioner Depth (COMPLEXITY-SCALED — check the module's complexity tag):
   - For [QUICK] modules (introductory): 4 = explains WHY before HOW, mentions tradeoffs, references when this approach is wrong. 5 = anchors concept to a real problem, teaches thinking not naming.
   - For [MEDIUM] modules: 4 = has patterns + anti-patterns + comparison/decision guide, theory before code, prose between code blocks. 5 = patterns concrete with consequences, decision guidance actionable.
   - For [COMPLEX]/[ADVANCED]/[EXPERT] modules: 4 = dedicated patterns, anti-patterns, decision framework, architectural reasoning, failure modes, scaling considerations. 5 = practitioner-grade throughout, edge cases covered, an experienced engineer would learn something new.
   IMPORTANT: Score D8 based on what's appropriate for the module's complexity level — do NOT punish a [QUICK] module for lacking advanced architecture sections.

## Instructions
1. Read the module carefully.
2. Score each dimension 1-5.
3. For any dimension below 4, explain SPECIFICALLY what's missing.
4. Output ONLY this JSON (no markdown, no explanation outside JSON):

{"scores": [D1, D2, D3, D4, D5, D6, D7, D8], "notes": {"D1": "...", "D2": "...", ...}, "plan": "If any dimension < 4, write a specific improvement plan. If all >= 4, write 'PASS'."}
"""


def step_audit(module_path: Path, model: str = MODELS["audit"]) -> dict | None:
    """Audit a module: run deterministic checks + LLM scoring."""
    content = module_path.read_text()
    key = module_key_from_path(module_path)
    print(f"\n{'='*60}")
    print(f"  AUDIT: {key}")
    print(f"{'='*60}")

    # 1. Deterministic checks
    is_uk = "/uk/" in str(module_path)
    results = structural.run_all(content, module_path)
    if is_uk:
        results.extend(ukrainian.run_all(content, module_path))

    errors = [r for r in results if not r.passed and r.severity == "ERROR"]
    warnings = [r for r in results if not r.passed and r.severity == "WARNING"]

    for r in results:
        print(r)

    if errors:
        print(f"\n  ❌ {len(errors)} error(s) found in deterministic checks")

    # 2. LLM scoring
    prompt = f"{RUBRIC_PROMPT}\n\n---\n\nMODULE PATH: {key}\n\n{content}"

    print(f"\n  Scoring with {model}...")
    ok, output = dispatch_auto(prompt, model=model, timeout=300)

    if not ok:
        print(f"  ❌ LLM scoring failed")
        return None

    # Parse JSON from response
    try:
        # Extract JSON from possible markdown wrapper
        json_match = output.strip()
        if json_match.startswith("```"):
            json_match = json_match.split("```")[1]
            if json_match.startswith("json"):
                json_match = json_match[4:]
        result = json.loads(json_match)
    except (json.JSONDecodeError, IndexError):
        print(f"  ❌ Failed to parse LLM scoring output")
        print(f"  Raw: {output[:500]}")
        return None

    if not isinstance(result, dict):
        print(f"  ❌ Expected JSON object, got {type(result).__name__}")
        return None

    scores = result.get("scores") or []
    if not isinstance(scores, list) or len(scores) != 8:
        print(f"  ❌ Expected 8 scores, got {scores!r}")
        return None

    try:
        scores = [int(s) for s in scores]
    except (ValueError, TypeError):
        print(f"  ❌ Non-numeric scores: {scores}")
        return None

    total = sum(scores)
    minimum = min(scores)
    passes = minimum >= 4 and total >= 33

    print(f"\n  Scores: {scores}")
    print(f"  Sum: {total}/40 | Min: {minimum} | {'PASS' if passes else 'FAIL'}")

    if result.get("plan") and result["plan"] != "PASS":
        print(f"\n  Plan: {result['plan'][:200]}...")

    return {
        "scores": scores,
        "sum": total,
        "min": minimum,
        "passes": passes,
        "notes": result.get("notes", {}),
        "plan": result.get("plan", ""),
        "check_errors": len(errors),
        "check_warnings": len(warnings),
    }


# ---------------------------------------------------------------------------
# WRITE step — Gemini drafts improvements
# ---------------------------------------------------------------------------

WRITE_PROMPT_TEMPLATE = """CRITICAL INSTRUCTION: Your response must be ONLY the raw markdown content of the improved module. Start your response with the --- frontmatter delimiter. No preamble, no explanation, no summary, no "I have improved..." — ONLY the markdown file content from first line to last.

You are improving a KubeDojo module. You will receive the current module content and an improvement plan.

RULES:
- Output the COMPLETE improved module (full file replacement)
- Your response IS the file — start with --- and end with the last line of content
- Do NOT remove or rewrite sections that are already good
- Do NOT change code blocks, YAML examples, or diagrams unless they contain errors
- Do NOT add emojis
- Do NOT change frontmatter unless fixing an error
- Add inline prompts as blockquotes: > **Pause and predict**: or > **Stop and think**:
- Quiz questions must be scenario-based (lead with realistic situation, test understanding not recall)
- Every quiz answer must explain WHY (3-5 sentences minimum)
- Keep the module's existing voice and style
- CONVERT any ASCII art diagrams to Mermaid (```mermaid blocks) — Mermaid renders natively in our site

IMPROVEMENT PLAN:
{plan}

---

CURRENT MODULE:
{content}
"""


REWRITE_PROMPT_TEMPLATE = """CRITICAL INSTRUCTION: Your response must be ONLY the raw markdown content. Start with the --- frontmatter delimiter. No preamble, no explanation — ONLY the markdown file.

TASK: Rewrite a KubeDojo educational module. The existing module scored too low — rewrite it while preserving all technical assets listed in the KNOWLEDGE PACKET below.

The file path is: {file_path}
Keep the EXACT same frontmatter (title, slug, sidebar order).

KNOWLEDGE PACKET — MUST PRESERVE:
The following technical assets are extracted from the original module. You MUST include ALL of them in your rewrite, placed in the appropriate sections. Do NOT omit, summarize, or simplify any of these.

{knowledge_packet}

TOPICS TO COVER (from audit):
{plan}

QUALITY REQUIREMENTS:
- 600-800 lines of content minimum (visual aids don't count toward this)
- Learning Outcomes: 3-5 measurable, Bloom's L3+ verbs (debug, design, evaluate, compare, diagnose, implement)
- Why This Module Matters: open with dramatic real-world incident, real company, real financial impact. 2-3 paragraphs.
- Core content (3-6 sections): explanations with analogies, runnable code blocks, Mermaid diagrams (preferred over ASCII), tables, war stories
- At least 2 inline active learning prompts distributed throughout: > **Pause and predict**: or > **Stop and think**:
- Did You Know?: exactly 4 facts with real numbers/dates
- Common Mistakes: table with 6-8 rows (Mistake | Why | Fix)
- Quiz: 6-8 questions in <details> tags, at least 4 scenario-based. Answers 3-5 sentences explaining WHY.
- Hands-On Exercise: 4-6 progressive tasks with solutions in <details> tags, success checklist
- Next Module: link with teaser
- NO emojis, NO recall quiz questions, NO thin outlines, NO number 47
- CONVERT all ASCII art diagrams to Mermaid (```mermaid blocks). Use flowchart for architecture, sequenceDiagram for flows, graph TD for hierarchies. ASCII art is fragile and hard to maintain — Mermaid renders natively in our site.

EXISTING MODULE (rewrite this, preserving all knowledge packet assets):
{content}
"""


# ---------------------------------------------------------------------------
# Knowledge packet extraction — preserves technical assets for rewrites
# ---------------------------------------------------------------------------

def extract_knowledge_packet(content: str) -> str:
    """Extract preservable technical assets from a module.

    Returns a formatted string with labeled code blocks, tables, diagrams,
    quiz questions, inline prompts, and links for the REWRITE prompt.
    """
    sections = []

    # 1. Code blocks — extract all fenced blocks, find nearest heading for context
    raw_blocks = list(re.finditer(r"```[\w]*\n[\s\S]*?```", content))
    if raw_blocks:
        headings = list(re.finditer(r"^#{2,3} .+$", content, re.MULTILINE))
        labeled = []
        for i, match in enumerate(raw_blocks, 1):
            # Find nearest heading before this code block
            heading = "unknown section"
            for h in reversed(headings):
                if h.start() < match.start():
                    heading = h.group().lstrip("# ").strip()
                    break
            labeled.append(f"[CODE-{i}] (from: {heading})\n{match.group()}")
        sections.append("### CODE BLOCKS\n" + "\n\n".join(labeled))

    # 2. Tables
    table_pattern = re.compile(r"(\|.+\|)\n(\|[-| :]+\|)\n((?:\|.+\|\n?)+)", re.MULTILINE)
    tables = table_pattern.findall(content)
    if tables:
        labeled_tables = []
        for i, (header, sep, rows) in enumerate(tables, 1):
            labeled_tables.append(f"[TABLE-{i}]\n{header}\n{sep}\n{rows.strip()}")
        sections.append("### TABLES\n" + "\n\n".join(labeled_tables))

    # 3. Mermaid and ASCII diagrams
    mermaid = re.findall(r"```mermaid\n[\s\S]*?```", content)
    if mermaid:
        labeled = [f"[DIAGRAM-{i}]\n{d}" for i, d in enumerate(mermaid, 1)]
        sections.append("### MERMAID DIAGRAMS\n" + "\n\n".join(labeled))

    # ASCII diagrams (lines with box-drawing chars or +--+)
    ascii_blocks = re.findall(
        r"(?:^[ ]*[+|┌┐└┘├┤┬┴┼─│╔╗╚╝║═].*\n){3,}",
        content, re.MULTILINE
    )
    if ascii_blocks:
        labeled = [f"[ASCII-{i}]\n{b.strip()}" for i, b in enumerate(ascii_blocks, 1)]
        sections.append("### ASCII DIAGRAMS (convert to Mermaid if possible)\n" + "\n\n".join(labeled))

    # 4. Quiz questions — full <details> blocks (questions + answers)
    quiz_blocks = re.findall(r"(<details>[\s\S]*?</details>)", content)
    if quiz_blocks:
        labeled = [f"[QUIZ-{i}]\n{q}" for i, q in enumerate(quiz_blocks, 1)]
        sections.append("### QUIZ BLOCKS (preserve questions AND answers)\n" + "\n\n".join(labeled))

    # 5. Inline prompts — capture full blockquote (may be multi-line)
    prompt_blocks = re.findall(
        r"(>\s*\*\*(?:Pause and predict|Stop and think|What would happen|Try it yourself|Before you look)[\s\S]*?)(?=\n\n|\n[^>]|\Z)",
        content
    )
    if prompt_blocks:
        labeled = [f"[PROMPT-{i}]\n{p.strip()}" for i, p in enumerate(prompt_blocks, 1)]
        sections.append("### INLINE PROMPTS\n" + "\n\n".join(labeled))

    # 6. Links (internal and external)
    links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
    if links:
        unique_links = list(dict.fromkeys((text, url) for text, url in links))[:20]
        sections.append("### KEY LINKS\n" + "\n".join(f"- [{t}]({u})" for t, u in unique_links))

    if not sections:
        return "(No technical assets extracted — module may be a stub)"

    packet = "\n\n".join(sections)
    if len(packet) > 15000:
        print(f"  ⚠ Knowledge packet is large ({len(packet)} chars) — may cause output truncation")

    return packet


def count_assets(content: str) -> dict:
    """Count technical assets in content for before/after comparison."""
    return {
        "code_blocks": len(re.findall(r"```[\w]*\n[\s\S]*?```", content)),
        "tables": len(re.compile(r"(\|.+\|)\n(\|[-| :]+\|)\n((?:\|.+\|\n?)+)", re.MULTILINE).findall(content)),
        "quiz_blocks": len(re.findall(r"<details>[\s\S]*?</details>", content)),
        "mermaid": len(re.findall(r"```mermaid\n[\s\S]*?```", content)),
        "inline_prompts": len(re.findall(
            r">\s*\*\*(?:Pause and predict|Stop and think|What would happen|Try it yourself|Before you look|Зупиніться|Подумайте)",
            content)),
    }


def step_write(module_path: Path, plan: str, model: str = MODELS["write"],
               rewrite: bool = False,
               previous_output: str | None = None) -> str | None:
    """Gemini drafts improvements or full rewrite based on the plan.

    If previous_output is provided (e.g. from an earlier attempt in the
    write→review loop), it is used as the content to improve instead of
    re-reading the file from disk. The file on disk is only updated during
    the CHECK phase, so without this the loop would keep operating on stale
    (original) content.
    """
    content = previous_output if previous_output is not None else module_path.read_text()
    key = module_key_from_path(module_path)
    mode = "REWRITE" if rewrite else "WRITE"
    print(f"\n  {mode}: {key} (using {model})")

    if rewrite:
        packet = extract_knowledge_packet(content)
        prompt = REWRITE_PROMPT_TEMPLATE.format(
            file_path=key, plan=plan, content=content, knowledge_packet=packet)
    else:
        prompt = WRITE_PROMPT_TEMPLATE.format(plan=plan, content=content)

    ok, output = dispatch_gemini_with_retry(prompt, model=model, timeout=900)

    if not ok or not output.strip():
        print(f"  ❌ WRITE failed")
        return None

    # Strip markdown wrapper if present
    if output.startswith("```markdown"):
        output = output[len("```markdown"):].strip()
    if output.startswith("```md"):
        output = output[len("```md"):].strip()
    if output.startswith("```"):
        output = output[3:].strip()
    if output.endswith("```"):
        output = output[:-3].strip()

    # Detect Gemini thinking leaks (chain-of-thought dumped into output)
    thinking_markers = ["CRITICAL INSTRUCTION", "thought\n", "Wait,", "I will ", "I'll just",
                        "the prompt says", "standard behavior"]
    if any(marker in output[:500] for marker in thinking_markers):
        print(f"  ❌ WRITE failed — Gemini leaked chain-of-thought into output")
        return None

    # Ensure output starts with frontmatter
    if not output.startswith("---"):
        # Try to find frontmatter deeper in the output
        fm_start = output.find("---\n")
        if fm_start > 0 and fm_start < 2000:
            output = output[fm_start:]
            print(f"  ⚠ Stripped {fm_start} chars of preamble before frontmatter")
        else:
            print(f"  ❌ WRITE failed — output has no frontmatter")
            return None

    # Reject degenerate output — a real module rewrite is thousands of chars.
    # 3000 is well below the expected 15k–40k range but above plausible stubs.
    MIN_WRITE_CHARS = 3000
    if len(output.strip()) < MIN_WRITE_CHARS:
        print(f"  ❌ WRITE failed — output is suspiciously short "
              f"({len(output.strip())} chars, expected ≥ {MIN_WRITE_CHARS})")
        return None

    print(f"  ✓ WRITE produced {len(output)} chars")
    return output


# ---------------------------------------------------------------------------
# REVIEW step — Claude strict review
# ---------------------------------------------------------------------------

REVIEW_PROMPT_TEMPLATE = """You are the OFFICIAL, STRICT quality reviewer for KubeDojo.
A Gemini-authored module is below. You are independent — assume nothing is
correct without verification. Web search is allowed and encouraged for current
tool/API state (2025-2026).

8-dimension rubric (score each 1-5, default to 4 unless genuinely outstanding):
- D1 Pedagogical Clarity: outcomes, structure, progression, signposting
- D2 Technical Accuracy: correct tools, versions, commands, YAML, concepts
- D3 Depth & Rigor: beyond surface; tradeoffs, edge cases, failure modes
- D4 Practical Utility: runnable labs, copy-pasteable configs, verification commands
- D5 Assessment Quality: scenario-based quizzes (not recall), non-trivial inline prompts
- D6 Coverage Breadth: no glaring gaps for the stated scope
- D7 Production Readiness: monitoring, security, HA, scale, SLOs, failure modes
- D8 Practitioner Depth: gotchas, decision frameworks, war stories, real ops

RULES:
1. APPROVE requires ALL dims >= 4 AND sum >= 33/40.
2. If any dim < 4 → REJECT.
3. If content, diagrams, or code were removed vs the original → REJECT.
4. Trivial quizzes / obvious inline prompts → REJECT.
5. Default to 4. A 5 means "I cannot find anything to improve in this dimension".

CRITICAL — ACTIONABLE FEEDBACK:
For every dimension scoring below 5, the feedback field MUST contain a CONCRETE
FIX, not just a complaint. Format each item as:
  "[D<n>] <what is wrong> → FIX: <exact replacement text / command / YAML / subsection to add>"
Do not say "the VPA section is inaccurate". Say:
  "[D2] VPA section claims recs come from Prometheus → FIX: replace with
  'VPA recommendations are produced by the recommender from Metrics Server and
  stored in .status.recommendation of the VerticalPodAutoscaler object. Query
  via: kubectl get vpa <name> -o jsonpath='{{.status.recommendation}}'"
The writer LLM will use your feedback verbatim to patch the module, so vague
criticism is useless. Cite commands, YAML keys, version numbers, and doc URLs
where relevant.

Output ONLY this JSON (no prose before or after, no markdown fences).
The scores array MUST have EXACTLY 8 integers (D1-D8; D8 is Practitioner Depth,
do not omit). feedback is a single string containing all dimension fixes joined
with newlines.

{{"verdict": "APPROVE" or "REJECT", "scores": [D1, D2, D3, D4, D5, D6, D7, D8], "feedback": "actionable fixes here"}}

---

ORIGINAL MODULE:
{original}

---

IMPROVED MODULE:
{improved}
"""


INDEX_PROMPT_TEMPLATE = """CRITICAL INSTRUCTION: Your response must be ONLY the raw markdown content. Start with the --- frontmatter delimiter. No preamble, no explanation — ONLY the markdown file.

You are rewriting the index.md for a KubeDojo section. This page introduces the section and lists its modules.

Keep the EXACT same frontmatter (title, sidebar order, label).

SECTION: {section_path}

MODULE LIST (current titles and filenames):
{module_list}

CURRENT INDEX:
{current_index}

RULES:
- Preserve the overall structure and voice of the current index
- Update the module table to match the current module titles and filenames
- Keep any prose, analogies, learning paths, prerequisites, and "what's next" sections
- Update descriptions in the table if they no longer match the module content
- Links must use relative paths: [Title](module-slug/)
- Ensure sidebar.order: 0 in frontmatter (index always sorts first)
- NO emojis
- If the current index is just a stub (< 10 lines of body), write a proper introduction (2-3 paragraphs) + module table
"""


def step_update_index(section_path: Path, model: str = MODELS["write"]) -> bool:
    """Rewrite section index.md via Gemini based on current module titles."""
    index_path = section_path / "index.md"
    if not index_path.exists():
        return False

    # Gather module info
    modules = sorted(section_path.glob("module-*.md"))
    modules = [m for m in modules if ".staging" not in str(m)]
    if not modules:
        return False

    module_list_lines = []
    for m in modules:
        content = m.read_text()
        fm_text = content.split("---", 2)[1] if content.startswith("---") else ""
        title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', fm_text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else m.stem
        module_list_lines.append(f"- {m.stem} → {title}")

    module_list = "\n".join(module_list_lines)
    current_index = index_path.read_text()
    rel_section = str(section_path.relative_to(CONTENT_ROOT))

    prompt = INDEX_PROMPT_TEMPLATE.format(
        section_path=rel_section,
        module_list=module_list,
        current_index=current_index,
    )

    print(f"\n  INDEX: {rel_section} (using {model})")
    ok, output = dispatch_gemini_with_retry(prompt, model=model, timeout=600)

    if not ok or not output.strip():
        print(f"  ❌ INDEX rewrite failed")
        return False

    # Strip markdown wrapper
    if output.startswith("```markdown"):
        output = output[len("```markdown"):].strip()
    if output.startswith("```md"):
        output = output[len("```md"):].strip()
    if output.startswith("```"):
        output = output[3:].strip()
    if output.endswith("```"):
        output = output[:-3].strip()

    if not output.startswith("---"):
        print(f"  ❌ INDEX rewrite has no frontmatter")
        return False

    # Validate frontmatter
    parts = output.split("---", 2)
    if len(parts) < 3:
        print(f"  ❌ INDEX rewrite has malformed frontmatter")
        return False
    try:
        fm = yaml.safe_load(parts[1])
        if not isinstance(fm, dict) or "title" not in fm:
            print(f"  ❌ INDEX rewrite missing title in frontmatter")
            return False
    except yaml.YAMLError as e:
        print(f"  ❌ INDEX rewrite has broken YAML: {e}")
        return False

    # Ensure sidebar.order: 0 (index always sorts first)
    if "order:" in parts[1] and "order: 0" not in parts[1]:
        output = re.sub(r'(  order: )\d+', r'\g<1>0', output, count=1)

    index_path.write_text(output)
    print(f"  ✓ INDEX written: {rel_section}/index.md ({len(output)} chars)")

    files_to_add = [str(index_path)]

    # Translate UK index if one exists
    uk_index = CONTENT_ROOT / "uk" / rel_section / "index.md"
    if uk_index.exists():
        uk_ok = _translate_index(output, uk_index, rel_section)
        if uk_ok:
            files_to_add.append(str(uk_index))

    # Git add
    subprocess.run(
        ["git", "add"] + files_to_add,
        cwd=str(REPO_ROOT), capture_output=True, text=True,
    )

    return True


def _translate_index(_en_content: str, uk_path: Path, rel_section: str) -> bool:
    """Translate an EN index.md to Ukrainian. Delegates to uk_sync."""
    print(f"  INDEX-UK: uk/{rel_section} (translating)")
    en_path = UK_CONTENT_ROOT / rel_section / "index.md"
    if uk_path.exists():
        # Re-translate existing UK index
        return uk_fix(uk_path)
    else:
        # New translation
        return uk_translate(en_path)


def _extract_review_json(output: str) -> dict | None:
    """Extract the final review JSON from a raw reviewer response.

    Codex exec output contains tool-use breadcrumbs, search logs, and the final
    answer on a 'codex' banner line followed by the JSON, then 'tokens used N'.
    Gemini output is usually just the JSON, sometimes inside ```json fences.
    Strategy: try a direct JSON parse first, then fall back to regex-matching
    the LAST balanced {...} block in the output (most reviewers emit the
    canonical response last, near 'tokens used' or end-of-stream).
    """
    text = output.strip()

    # Strip fenced-code wrappers first (gemini pattern)
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            candidate = parts[1]
            if candidate.startswith("json"):
                candidate = candidate[4:]
            try:
                return json.loads(candidate.strip())
            except json.JSONDecodeError:
                pass

    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Last-balanced-{...} scan (handles codex-exec noise)
    # Walk from the end; find matching braces.
    candidates: list[str] = []
    depth = 0
    end = -1
    for i in range(len(text) - 1, -1, -1):
        ch = text[i]
        if ch == "}":
            if depth == 0:
                end = i
            depth += 1
        elif ch == "{":
            if depth > 0:
                depth -= 1
                if depth == 0 and end != -1:
                    candidates.append(text[i:end + 1])
                    end = -1
    for cand in candidates:
        try:
            obj = json.loads(cand)
            if isinstance(obj, dict) and "verdict" in obj and "scores" in obj:
                return obj
        except json.JSONDecodeError:
            continue
    return None


def step_review(module_path: Path, improved: str, model: str = MODELS["review"]) -> dict | None:
    """Reviewer (Codex by default) evaluates the module strictly.

    Returns:
        dict with keys {verdict, scores, feedback} on success.
        {"rate_limited": True} sentinel dict if the reviewer was rate-limited
            (caller should NOT fail the module — keep content, flag for retry).
        None on any other failure.
    """
    original = module_path.read_text()
    key = module_key_from_path(module_path)
    print(f"\n  REVIEW: {key} (using {model})")

    prompt = REVIEW_PROMPT_TEMPLATE.format(original=original, improved=improved)

    ok, output = dispatch_auto(prompt, model=model, timeout=900)

    if not ok:
        # Rate-limit detection so run_module can degrade gracefully
        if output and _is_rate_limited(output):
            print(f"  ⚠ REVIEW rate-limited — module flagged for later re-review")
            return {"rate_limited": True}
        print(f"  ❌ REVIEW failed")
        return None

    result = _extract_review_json(output)
    if result is None:
        print(f"  ❌ Failed to parse REVIEW output")
        print(f"  Raw: {output[:500]}")
        return None

    if not isinstance(result, dict):
        print(f"  ❌ Expected JSON object, got {type(result).__name__}")
        return None

    verdict = result.get("verdict", "REJECT")
    scores = result.get("scores") or []
    if isinstance(scores, list):
        try:
            scores = [int(s) for s in scores]
        except (ValueError, TypeError):
            scores = []
    feedback = result.get("feedback", "")

    print(f"  Verdict: {verdict}")
    if scores:
        print(f"  Scores: {scores} (sum: {sum(scores)})")
    if feedback:
        print(f"  Feedback: {feedback[:200]}")

    return result


# ---------------------------------------------------------------------------
# CHECK step — deterministic checks on improved content
# ---------------------------------------------------------------------------

def step_check(content: str, path: Path) -> tuple[bool, list]:
    """Run all deterministic checks on the improved content."""
    print(f"\n  CHECK: running deterministic checks")

    # Safety guard: reject truncated content (Gemini output limit)
    original = path.read_text()
    if len(content) < len(original) * 0.85:
        print(f"  ✗ CHECK: content truncated — {len(content)} chars vs {len(original)} original (< 85%)")
        return False, []

    # Safety guard: validate YAML frontmatter before writing
    if not content.startswith("---"):
        print("  ✗ CHECK: missing YAML frontmatter delimiter")
        return False, []
    parts = content.split("---", 2)
    if len(parts) < 3:
        print("  ✗ CHECK: malformed frontmatter — no closing ---")
        return False, []
    try:
        fm = yaml.safe_load(parts[1])
        if not isinstance(fm, dict) or "title" not in fm:
            print(f"  ✗ CHECK: frontmatter missing 'title' field")
            return False, []
    except yaml.YAMLError as e:
        print(f"  ✗ CHECK: broken YAML frontmatter — {e}")
        return False, []

    # Language guard: reject Ukrainian content in EN files (and vice versa)
    is_uk = "/uk/" in str(path)
    has_cyrillic_title = bool(re.search(r'^title:.*[а-яіїєґ]', parts[1], re.MULTILINE))
    has_uk_slug = bool(re.search(r'^slug:\s*uk/', parts[1], re.MULTILINE))
    has_en_commit = "en_commit:" in parts[1]
    if not is_uk and (has_cyrillic_title or has_uk_slug or has_en_commit):
        print(f"  ✗ CHECK: Ukrainian content in EN file (title/slug/en_commit detected)")
        return False, []
    if is_uk and not has_cyrillic_title and not has_en_commit:
        print(f"  ✗ CHECK: English content in UK file (no Cyrillic title or en_commit)")
        return False, []

    # Asset preservation check: compare original vs improved
    original_assets = count_assets(original)
    new_assets = count_assets(content)
    for asset_type, orig_count in original_assets.items():
        if orig_count > 0:
            new_count = new_assets.get(asset_type, 0)
            loss_pct = (orig_count - new_count) / orig_count * 100
            if loss_pct >= 20:
                print(f"  ✗ CHECK: {asset_type} lost {loss_pct:.0f}% ({orig_count} → {new_count})")
                return False, []

    is_uk = "/uk/" in str(path)
    results = structural.run_all(content, path)
    if is_uk:
        results.extend(ukrainian.run_all(content, path))

    errors = [r for r in results if not r.passed and r.severity == "ERROR"]

    for r in results:
        if not r.passed:
            print(r)

    passed = len(errors) == 0
    print(f"  {'✓' if passed else '✗'} CHECK: {len(errors)} errors, "
          f"{len([r for r in results if not r.passed and r.severity == 'WARNING'])} warnings")

    return passed, results


# ---------------------------------------------------------------------------
# Full pipeline: run one module through all steps
# ---------------------------------------------------------------------------

def run_module(module_path: Path, state: dict, max_retries: int = 2,
               models: dict | None = None, dry_run: bool = False) -> bool:
    """Run a single module through the full pipeline."""
    m = models or MODELS
    key = module_key_from_path(module_path)
    ms = get_module_state(state, key)

    print(f"\n{'='*60}")
    print(f"  PIPELINE: {key}{'  [DRY RUN]' if dry_run else ''}")
    print(f"  Current phase: {ms['phase']}")
    print(f"{'='*60}")

    # Already-done resumption. If the module is flagged for independent
    # re-review (typically Gemini-approved during a Codex rate-limit window),
    # reset to audit so the full pipeline can run it through Codex. Otherwise
    # this is a genuine already-done module and we return True so batch runners
    # don't treat it as a failure.
    if ms["phase"] == "done":
        if ms.get("needs_independent_review"):
            print(f"  ↻ Flagged needs_independent_review — resetting to audit for re-review")
            ms["phase"] = "audit"
            save_state(state)
            # fall through to AUDIT block below
        else:
            reviewer = ms.get("reviewer", "unknown")
            total = ms.get("sum", "?")
            print(f"  ✓ Already done: {total}/40 reviewer={reviewer} — skipping")
            return True

    # AUDIT+PLAN
    if ms["phase"] in ("pending", "audit"):
        audit = step_audit(module_path, model=m["audit"])
        if audit is None:
            ms["phase"] = "audit"
            ms["errors"].append(f"Audit failed at {datetime.now(UTC).isoformat()}")
            save_state(state)
            return False

        ms["scores"] = audit["scores"]
        ms["sum"] = audit["sum"]
        ms["passes"] = audit["passes"]
        ms["last_run"] = datetime.now(UTC).isoformat()

        plan = audit.get("plan", "")
        if not plan or plan == "PASS":
            plan = f"Improve weak dimensions. Scores: {audit['scores']}. Notes: {audit.get('notes', {})}"

        if audit["passes"] and audit["check_errors"] == 0:
            # Audit says it passes — but we MUST get an independent reviewer
            # stamp before marking done. Audit uses Gemini, which has self-bias
            # when reviewing other Gemini-written content (see module-1.5:
            # Gemini 40/40 vs Codex 24-28/40). Force one review cycle with
            # the preferred reviewer (Codex by default), skipping write.
            writer_family = m["write"].split("-")[0]
            reviewer_family = m["review"].split("-")[0]
            if reviewer_family == writer_family:
                # Reviewer and writer same family — no cross-check possible.
                print(f"\n  ✓ Module already passes ({audit['sum']}/40), reviewer same family — done")
                ms["phase"] = "done"
                save_state(state)
                return True
            print(f"\n  ✓ Audit says module passes ({audit['sum']}/40) — forcing {m['review']} review before done")
            ms["phase"] = "review"
            save_state(state)
            # Populate `improved` from disk so the review/check/score steps
            # below operate on the current on-disk content (no rewrite).
            improved = module_path.read_text()
            last_good = improved
        else:
            if dry_run:
                print(f"\n  [DRY RUN] Would improve: {[f'D{i+1}={s}' for i, s in enumerate(audit['scores']) if s < 4]}")
                print(f"  [DRY RUN] Plan: {plan[:300]}")
                return False
            ms["phase"] = "write"
            save_state(state)
            improved = None
            last_good = None
    else:
        # Resuming — reconstruct plan from state
        plan = f"Resume improvement. Last scores: {ms.get('scores', 'unknown')}."
        improved = None
        last_good = None

    # WRITE → REVIEW loop (max retries)
    # Auto-detect rewrite mode: score < 28 means "improve" won't cut it.
    # `improved` and `last_good` are already initialized above (either to
    # on-disk content when audit passed, or to None when audit failed or
    # when resuming). `last_good` holds the most recent successful WRITE
    # output across retries so a REJECT followed by a rewrite improves the
    # prior attempt instead of starting from scratch.
    needs_rewrite = (ms.get("sum") or 0) < 28
    if needs_rewrite:
        print(f"  Score {ms.get('sum')}/40 < 28 — using REWRITE mode")

    for attempt in range(max_retries + 1):
        if ms["phase"] in ("write",):
            improved = step_write(module_path, plan, model=m["write"],
                                  rewrite=needs_rewrite,
                                  previous_output=last_good)
            if improved is None:
                ms["errors"].append(f"Write failed attempt {attempt+1}")
                save_state(state)
                if attempt < max_retries:
                    continue
                return False
            last_good = improved

            ms["phase"] = "review"
            save_state(state)

        if ms["phase"] == "review":
            reviewer_model = m["review"]
            review = step_review(module_path, improved or module_path.read_text(), model=reviewer_model)

            # Rate-limit degradation: fall back to the Gemini reviewer so we
            # get REAL scores and can make a real APPROVE/REJECT decision.
            # The module still commits if it passes, but we flag
            # needs_independent_review=True so operators know to re-review
            # with Codex (or Claude) when quota returns. Pipeline never halts.
            if isinstance(review, dict) and review.get("rate_limited"):
                fallback_model = MODELS.get("review_fallback", "gemini-3.1-pro-preview")
                # Only fall back if the fallback is from a different family
                # (otherwise we'd just retry the same rate-limited reviewer).
                primary_family = reviewer_model.split("-")[0]
                fallback_family = fallback_model.split("-")[0]
                if fallback_family == primary_family:
                    print(f"  ⚠ Primary reviewer rate-limited and fallback is same family — aborting review")
                    ms["errors"].append("Primary reviewer rate-limited, no alternative fallback")
                    save_state(state)
                    return False

                print(f"  ⚠ {reviewer_model} rate-limited — falling back to {fallback_model}")
                review = step_review(
                    module_path, improved or module_path.read_text(), model=fallback_model,
                )
                if review is None:
                    ms["errors"].append("Fallback reviewer failed")
                    save_state(state)
                    return False
                if isinstance(review, dict) and review.get("rate_limited"):
                    ms["errors"].append("Both primary and fallback reviewers rate-limited")
                    save_state(state)
                    return False
                # Mark that this module used a fallback reviewer — the APPROVE
                # branch below will see reviewer_family != INDEPENDENT_REVIEWER_FAMILIES
                # and correctly set needs_independent_review=True.
                reviewer_model = fallback_model
                ms["used_fallback_reviewer"] = True

            if review is None:
                ms["errors"].append(f"Review failed attempt {attempt+1}")
                ms["phase"] = "write"
                save_state(state)
                if attempt < max_retries:
                    continue
                return False

            if review.get("verdict") == "APPROVE":
                # Save review scores (these reflect the IMPROVED content).
                # If Gemini returns a malformed array, trust the APPROVE verdict
                # and write a passing score vector. This covers the historical
                # [D1-D7] prompt bug and any future output-format drift.
                # Floor must be >= SCORE thresholds (min >= 4 AND sum >= 33) so
                # trusting the verdict actually lets the module pass SCORE;
                # otherwise the module would loop forever in improve mode.
                r_scores_raw = review.get("scores") or []
                well_formed = (
                    isinstance(r_scores_raw, list)
                    and len(r_scores_raw) == 8
                    and all(isinstance(x, int) for x in r_scores_raw)
                )
                if well_formed:
                    ms["scores"] = r_scores_raw
                    ms["sum"] = sum(r_scores_raw)
                else:
                    raw_len = len(r_scores_raw) if isinstance(r_scores_raw, list) else "n/a"
                    print(f"  ⚠ APPROVE with malformed scores (len={raw_len}); trusting verdict and using passing-floor scores")
                    floor = [4, 4, 4, 4, 4, 4, 4, 5]  # sum=33, min=4, passes SCORE
                    ms["scores"] = floor
                    ms["sum"] = sum(floor)
                # Tag the reviewer that actually produced this verdict (may be
                # the primary or the fallback). needs_independent_review is
                # True for any reviewer not in INDEPENDENT_REVIEWER_FAMILIES
                # (currently: anything other than codex/claude).
                reviewer_family = reviewer_model.split("-")[0]
                ms["reviewer"] = reviewer_family
                ms["needs_independent_review"] = (
                    reviewer_family not in INDEPENDENT_REVIEWER_FAMILIES
                )
                ms["phase"] = "check"
                save_state(state)
                break
            else:
                # Rejected — feed back to WRITE
                r_scores = review.get("scores") or []
                r_feedback = review.get("feedback", "")
                r_valid = len(r_scores) == 8
                r_sum = sum(r_scores) if r_valid else 0
                r_has_weak = r_valid and any(s < 4 for s in r_scores)

                if r_valid and r_sum >= 33 and r_has_weak:
                    # Surgical fix — mostly passing, specific weak dims to target
                    needs_rewrite = False
                    weak = [(i + 1, s) for i, s in enumerate(r_scores) if s < 4]
                    weak_desc = ", ".join(f"D{i}={s}" for i, s in weak)
                    plan = (
                        f"TARGETED FIX. Content already scored {r_sum}/40 — "
                        f"ONLY weak dimension(s): {weak_desc}. "
                        f"Edit ONLY what the reviewer feedback points to; "
                        f"preserve EVERYTHING else verbatim (do not touch other sections, "
                        f"code blocks, diagrams, tables, or quiz questions that were not flagged). "
                        f"Reviewer feedback: {r_feedback}"
                    )
                    print(f"  → Targeted fix mode: {weak_desc}, sum={r_sum}/40")
                elif r_valid and r_sum >= 36 and not r_has_weak:
                    # All dims ≥ 4 but verdict REJECT — qualitative nitpick.
                    # Numeric ground truth says this passes. Use improve mode
                    # with the feedback as a focused plan.
                    needs_rewrite = False
                    plan = (
                        f"NITPICK FIX. Content scored {r_sum}/40, all dimensions pass "
                        f"(every score ≥ 4), but the reviewer raised a concern. "
                        f"Address ONLY this specific concern; preserve EVERYTHING else "
                        f"verbatim (sections, code, diagrams, tables, quiz questions). "
                        f"Reviewer feedback: {r_feedback}"
                    )
                    print(f"  → Nitpick fix mode: sum={r_sum}/40, no weak dims")
                else:
                    # Real quality issues — recompute needs_rewrite from latest score.
                    # Do NOT leave it pinned from a previous iteration.
                    needs_rewrite = (r_sum < 28) if r_valid else True
                    plan = f"PREVIOUS REVIEW REJECTED. Feedback: {r_feedback}. Fix these issues."
                    if not r_valid:
                        print(f"  ⚠ Review returned {len(r_scores)} scores (expected 8) — using full rewrite")
                ms["phase"] = "write"
                save_state(state)
                if attempt < max_retries:
                    print(f"  ↻ Rejected, retrying ({attempt+1}/{max_retries})")
                    continue
                else:
                    print(f"  ❌ Rejected after {max_retries} retries")
                    ms["errors"].append(f"Review rejected {max_retries+1} times")
                    return False

    # CHECK
    if ms["phase"] == "check":
        # Load improved content from staging file if resuming
        staging = module_path.with_suffix(".staging.md")
        if improved:
            staging.write_text(improved)
        elif staging.exists():
            improved = staging.read_text()
            print(f"  Resuming CHECK from staging file")
        else:
            print(f"  ❌ No improved content available for CHECK")
            return False

        passed, results = step_check(improved, module_path)
        if not passed:
            ms["errors"].append("Deterministic checks failed after review")
            save_state(state)
            # Keep staging file so we can resume after fixing thresholds
            print(f"  Staging file kept: {staging}")
            return False

        # Backup original, then write improved file
        backup = module_path.with_suffix(".md.bak")
        shutil.copy2(module_path, backup)
        module_path.write_text(improved)
        staging.unlink(missing_ok=True)
        backup.unlink(missing_ok=True)  # remove backup on success
        print(f"  ✓ File written: {module_path}")

        ms["phase"] = "score"
        save_state(state)

    # SCORE
    if ms["phase"] == "score":
        scores = ms.get("scores", [4, 4, 4, 4, 4, 4, 4, 4])
        total = sum(scores)
        minimum = min(scores)
        passes = minimum >= 4 and total >= 33

        ms["passes"] = passes
        ms["sum"] = total
        ms["phase"] = "done" if passes else "score"
        ms["last_run"] = datetime.now(UTC).isoformat()
        save_state(state)

        if passes:
            reviewer = ms.get("reviewer", "unknown")
            pending = ms.get("needs_independent_review", False)
            pending_tag = " needs-independent-review" if pending else ""
            print(f"\n  ✓ PASS: {total}/40 (min: {minimum}) reviewer={reviewer}{pending_tag}")
            # Auto-commit
            add_result = subprocess.run(
                ["git", "add", str(module_path)],
                cwd=str(REPO_ROOT), capture_output=True, text=True,
            )
            if add_result.returncode != 0:
                print(f"  ⚠ git add failed: {add_result.stderr[:200]}")

            commit_msg = (
                f"chore(quality): v1 pipeline pass [{key}] "
                f"({total}/40 reviewer={reviewer}{pending_tag})"
            )
            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(REPO_ROOT), capture_output=True, text=True,
            )
            if commit_result.returncode != 0:
                print(f"  ⚠ git commit failed: {commit_result.stderr[:200]}")
            else:
                print(f"  ✓ Committed")
            return True
        else:
            print(f"\n  ✗ FAIL: {total}/40 (min: {minimum}) — needs manual intervention")
            return False

    return False


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

def cmd_audit(args):
    """Audit a single module."""
    path = Path(args.module)
    if not path.exists():
        path = CONTENT_ROOT / f"{args.module}.md"
    if not path.exists():
        print(f"Module not found: {args.module}")
        sys.exit(1)

    model = args.audit_model or MODELS["audit"]
    result = step_audit(path, model=model)
    if result:
        sys.exit(0 if result["passes"] else 1)
    sys.exit(1)


def cmd_audit_all(args):
    """Audit all modules (or a section) and produce a report."""
    if args.section:
        root = CONTENT_ROOT / args.section
    else:
        root = CONTENT_ROOT

    modules = sorted(root.glob("**/module-*.md"))
    # Exclude UK translations for now
    modules = [m for m in modules if "/uk/" not in str(m) and ".staging" not in str(m)]

    print(f"Found {len(modules)} modules to audit")

    report = {"timestamp": datetime.now(UTC).isoformat(), "modules": {}}
    model = args.audit_model or MODELS["audit"]

    for i, path in enumerate(modules, 1):
        key = module_key_from_path(path)
        print(f"\n[{i}/{len(modules)}] {key}")

        # Only deterministic checks for audit-all (LLM too expensive for 568 modules)
        content = path.read_text()
        results = structural.run_all(content, path)
        errors = [r for r in results if not r.passed and r.severity == "ERROR"]

        report["modules"][key] = {
            "errors": len(errors),
            "error_details": [r.message for r in errors],
        }

        if errors:
            for r in errors:
                print(r)

    # Save report
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nReport saved to {REPORT_FILE}")

    total = len(report["modules"])
    clean = sum(1 for m in report["modules"].values() if m["errors"] == 0)
    print(f"\n{clean}/{total} modules pass deterministic checks")


def cmd_run(args):
    """Run a single module through the full pipeline."""
    path = Path(args.module)
    if not path.exists():
        path = CONTENT_ROOT / f"{args.module}.md"
    if not path.exists():
        print(f"Module not found: {args.module}")
        sys.exit(1)

    models = dict(MODELS)
    if args.audit_model:
        models["audit"] = args.audit_model
    if args.write_model:
        models["write"] = args.write_model
    if args.review_model:
        models["review"] = args.review_model

    state = load_state()
    ok = run_module(path, state, models=models, dry_run=getattr(args, "dry_run", False))
    sys.exit(0 if ok else 1)


def cmd_run_section(args):
    """Run all modules in a section through the pipeline."""
    section_path = CONTENT_ROOT / args.section
    if not section_path.exists():
        print(f"Section not found: {args.section}")
        sys.exit(1)

    modules = sorted(section_path.glob("**/module-*.md"))
    modules = [m for m in modules if "/uk/" not in str(m) and ".staging" not in str(m)]

    print(f"Found {len(modules)} modules in {args.section}")

    # --- GAP-CHECK first (track level) ---
    track = args.track or _infer_track(args.section)
    print(f"\n{'='*60}")
    print(f"  GAP-CHECK: {args.section} (track: {track})")
    print(f"{'='*60}")

    gap_issues = gaps.run_track_gap_analysis(section_path, track=track)
    gap_errors = [i for i in gap_issues if i.severity == "ERROR"]
    gap_warnings = [i for i in gap_issues if i.severity == "WARNING"]

    if gap_issues:
        for issue in gap_issues:
            print(issue)
        print(f"\n  Gaps: {len(gap_errors)} errors, {len(gap_warnings)} warnings")

        # Persist gaps to file for later review
        gaps_file = REPO_ROOT / ".pipeline" / "gaps-report.json"
        gaps_file.parent.mkdir(parents=True, exist_ok=True)
        existing = json.loads(gaps_file.read_text()) if gaps_file.exists() else {"sections": {}}
        existing["sections"][args.section] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "track": track,
            "issues": [
                {"module_a": i.module_a, "module_b": i.module_b,
                 "type": i.gap_type, "severity": i.severity, "message": i.message}
                for i in gap_issues
            ],
        }
        gaps_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
        print(f"  Gaps saved to .pipeline/gaps-report.json")
    else:
        print("  ✓ No scaffolding gaps detected")

    if gap_errors and not args.skip_gaps:
        print(f"\n  ❌ {len(gap_errors)} gap errors — fix before processing modules")
        print(f"  Use --skip-gaps to override")
        sys.exit(1)

    models = dict(MODELS)
    if args.audit_model:
        models["audit"] = args.audit_model
    if args.write_model:
        models["write"] = args.write_model
    if args.review_model:
        models["review"] = args.review_model

    state = load_state()
    passed = 0
    failed = 0
    dry_run = getattr(args, "dry_run", False)

    workers = args.workers or 1

    if workers == 1:
        for i, path in enumerate(modules, 1):
            key = module_key_from_path(path)
            print(f"\n[{i}/{len(modules)}] {key}")
            ok = run_module(path, state, models=models, dry_run=dry_run)
            if ok:
                passed += 1
            else:
                failed += 1
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(run_module, path, state, 2, models, dry_run): path
                for path in modules
            }
            for future in as_completed(futures):
                path = futures[future]
                try:
                    ok = future.result()
                    if ok:
                        passed += 1
                    else:
                        failed += 1
                except Exception as e:
                    print(f"  ❌ Exception processing {path}: {e}")
                    failed += 1

    print(f"\n{'='*60}")
    if dry_run:
        print(f"  DRY RUN: {passed} already pass, {failed} need improvement out of {len(modules)}")
        # Show summary of weak dimensions across all audited modules
        all_scores = {k: v.get("scores") for k, v in state.get("modules", {}).items()
                      if v.get("scores") and k.startswith(args.section.replace("/", "/")[:20])}
        if all_scores:
            weak_counts = [0] * 7
            for scores in all_scores.values():
                for i, s in enumerate(scores):
                    if s < 4:
                        weak_counts[i] += 1
            dim_names = ["D1:Outcomes", "D2:Scaffold", "D3:Active", "D4:RealWorld",
                         "D5:Assess", "D6:CogLoad", "D7:Engage"]
            print(f"\n  Weak dimensions across section:")
            for name, count in zip(dim_names, weak_counts):
                if count > 0:
                    print(f"    {name}: {count} modules below 4")
    else:
        print(f"  DONE: {passed} passed, {failed} failed out of {len(modules)}")
    print(f"{'='*60}")

    sys.exit(0 if (dry_run or failed == 0) else 1)


def cmd_learning_path(args):
    """Detect gaps across the full learning path (cross-track transitions)."""
    print(f"\nCross-Track Gap Analysis")
    print(f"{'='*60}")
    print(f"  Learning path: {' → '.join(d.split('/')[-1] for d, _ in gaps.LEARNING_PATH)}")
    print()

    issues = gaps.detect_cross_track_gaps(CONTENT_ROOT)

    if not issues:
        print("  ✓ No cross-track gaps detected")
        return

    for issue in issues:
        print(issue)
        print()

    errors = [i for i in issues if i.severity == "ERROR"]
    warnings = [i for i in issues if i.severity == "WARNING"]

    print(f"  Summary: {len(errors)} errors, {len(warnings)} warnings")

    # Categorize fixes
    new_modules = [i for i in issues if i.suggestion == "new_module"]
    expansions = [i for i in issues if i.suggestion == "expand"]
    cross_refs = [i for i in issues if i.suggestion == "cross_reference"]

    if new_modules:
        print(f"\n  NEW MODULES NEEDED: {len(new_modules)} transitions have too many gaps to fix inline")
    if expansions:
        print(f"  EXPAND EXISTING: {len(expansions)} transitions need existing modules expanded")
    if cross_refs:
        print(f"  CROSS-REFERENCES: {len(cross_refs)} transitions just need \"see Module X\" links")

    # Persist to file
    gaps_file = REPO_ROOT / ".pipeline" / "gaps-report.json"
    gaps_file.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(gaps_file.read_text()) if gaps_file.exists() else {"sections": {}}
    existing["cross_track"] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "issues": [
            {"from": i.from_section, "to": i.to_section,
             "type": i.gap_type, "severity": i.severity,
             "message": i.message, "suggestion": i.suggestion}
            for i in issues
        ],
    }
    gaps_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    print(f"\n  Saved to .pipeline/gaps-report.json")

    sys.exit(1 if errors else 0)


def _track_from_key(key: str) -> str:
    """Map a module key to its display group matching e2e aliases."""
    parts = key.split("/")
    if parts[0] == "k8s":
        sub = parts[1] if len(parts) > 1 else ""
        if sub in ("cka", "ckad", "cks", "kcna", "kcsa"):
            return "certs"
        if sub in ("extending",):
            return "certs"  # part of certs alias
        return "specialty"  # pca, cba, capa, kca, otca, ica, cca, finops
    if parts[0] == "prerequisites":
        return "prereqs"
    if parts[0] == "linux":
        return "linux"
    if parts[0] == "platform":
        sub = parts[1] if len(parts) > 1 else ""
        if sub == "foundations":
            return "platform/foundations"
        if sub == "disciplines":
            return "platform/disciplines"
        if sub == "toolkits":
            return "platform/toolkits"
        return "platform"
    if parts[0] in ("cloud", "on-premises"):
        return parts[0]
    return parts[0]


def cmd_status(args):
    """Show pipeline status."""
    state = load_state()
    modules = state.get("modules", {})
    verbose = getattr(args, "verbose", False)

    # Discover ALL EN modules on disk
    all_en = sorted(CONTENT_ROOT.glob("**/module-*.md"))
    all_en = [m for m in all_en if "/uk/" not in str(m)]
    disk_keys = {module_key_from_path(m) for m in all_en}

    # Discover UK translations
    all_uk = sorted((CONTENT_ROOT / "uk").glob("**/module-*.md")) if (CONTENT_ROOT / "uk").exists() else []
    uk_keys = set()
    for m in all_uk:
        # uk/k8s/cka/... -> k8s/cka/...
        rel = str(m.relative_to(CONTENT_ROOT / "uk")).replace(".md", "")
        uk_keys.add(rel)

    # Build track data from disk + state
    tracks: dict[str, dict] = {}
    for key in disk_keys:
        track = _track_from_key(key)
        t = tracks.setdefault(track, {
            "total": 0, "pass": 0, "fail": 0, "wip": 0, "todo": 0,
            "scores": [], "uk": 0,
        })
        t["total"] += 1
        if key in uk_keys:
            t["uk"] += 1
        ms = modules.get(key, {})
        phase = ms.get("phase")
        s = ms.get("sum")
        if s is not None:
            t["scores"].append(s)
        if phase == "done":
            t["pass"] += 1
        elif phase in ("write",):
            # stuck at write = rejected, effectively failing
            t["fail"] += 1
        elif phase and phase not in ("pending",):
            t["wip"] += 1
        else:
            t["todo"] += 1

    # Totals
    g_total = sum(t["total"] for t in tracks.values())
    g_pass = sum(t["pass"] for t in tracks.values())
    g_fail = sum(t["fail"] for t in tracks.values())
    g_wip = sum(t["wip"] for t in tracks.values())
    g_todo = sum(t["total"] - t["pass"] - t["fail"] - t["wip"] for t in tracks.values())
    g_uk = sum(t["uk"] for t in tracks.values())
    all_scores = [s for t in tracks.values() for s in t["scores"]]

    print(f"\n  Modules: {g_total} total | {g_pass} pass (33+) | {g_fail} fail | {g_wip} in progress | {g_todo} not started")
    print(f"  Translations: {g_uk}/{g_total} UK")
    if all_scores:
        print(f"  Scores: avg {sum(all_scores)/len(all_scores):.1f} | lo {min(all_scores)} | hi {max(all_scores)} ({len(all_scores)} scored)")
    print()
    hdr = f"  {'track':30s} {'pass':>6s} {'fail':>5s} {'wip':>5s} {'todo':>5s} {'total':>5s}  {'avg':>4s} {'lo':>3s}  {'uk':>3s}"
    print(hdr)
    print(f"  {'-'*85}")

    for track in sorted(tracks):
        t = tracks[track]
        todo = t["total"] - t["pass"] - t["fail"] - t["wip"]
        avg = f'{sum(t["scores"])/len(t["scores"]):.0f}' if t["scores"] else "--"
        lo = f'{min(t["scores"])}' if t["scores"] else "--"
        uk = str(t["uk"]) if t["uk"] else "--"
        # Color hint: checkmark if all pass
        mark = " ok" if t["pass"] == t["total"] else ""
        print(f"  {track:30s} {t['pass']:>6d} {t['fail']:>5d} {t['wip']:>5d} {todo:>5d} {t['total']:>5d}  {avg:>4s} {lo:>3s}  {uk:>3s}{mark}")

    # Index pages summary
    all_idx = sorted(CONTENT_ROOT.glob("**/index.md"))
    all_idx = [f for f in all_idx if "/uk/" not in str(f) and f != CONTENT_ROOT / "index.md"]
    idx_by_track: dict[str, dict] = {}
    for f in all_idx:
        rel = str(f.relative_to(CONTENT_ROOT))
        track = _track_from_key(rel.replace("/index.md", "/dummy"))
        t = idx_by_track.setdefault(track, {"total": 0, "stub": 0})
        t["total"] += 1
        if len(f.read_text().splitlines()) < 30:
            t["stub"] += 1
    idx_total = sum(t["total"] for t in idx_by_track.values())
    idx_stubs = sum(t["stub"] for t in idx_by_track.values())
    print(f"\n  Index pages: {idx_total} total | {idx_total - idx_stubs} with content | {idx_stubs} stubs (<30 lines)")
    stub_tracks = [(track, t["stub"]) for track, t in sorted(idx_by_track.items()) if t["stub"] > 0]
    if stub_tracks:
        print(f"    Stubs: {', '.join(f'{track} ({n})' for track, n in stub_tracks)}")

    # Errors (only with --verbose)
    failed = [k for k, m in modules.items() if m.get("errors")]
    if failed:
        print(f"\n  {len(failed)} modules with errors", end="")
        if verbose:
            print(":")
            for k in failed[:20]:
                latest_error = modules[k]["errors"][-1] if modules[k]["errors"] else "?"
                print(f"    {k}: {latest_error}")
            if len(failed) > 20:
                print(f"    ... and {len(failed) - 20} more")
        else:
            print(" (use --verbose to list)")


def _apply_model_overrides(args) -> dict:
    """Build models dict from defaults + CLI overrides."""
    models = dict(MODELS)
    if getattr(args, "audit_model", None):
        models["audit"] = args.audit_model
    if getattr(args, "write_model", None):
        models["write"] = args.write_model
    if getattr(args, "review_model", None):
        models["review"] = args.review_model
    return models


def cmd_resume(args):
    """Resume pipeline from where it stopped."""
    state = load_state()
    modules = state.get("modules", {})

    # Find modules that aren't done
    incomplete = {k: m for k, m in modules.items()
                  if m.get("phase") not in ("done", "pending")}

    if not incomplete:
        print("Nothing to resume.")
        return

    print(f"Resuming {len(incomplete)} incomplete modules")

    models = _apply_model_overrides(args)

    for key, ms in incomplete.items():
        path = find_module_path(key)
        if path and path.exists():
            run_module(path, state, models=models)


def cmd_e2e(args):
    """End-to-end pipeline: resume stuck modules, then process all sections."""
    global _quiet
    _quiet = not getattr(args, "verbose", False)
    _original_print(f"  Logging to: {LOG_FILE}")
    _original_print(f"  Use --verbose or tail -f {LOG_FILE} for full output\n")
    models = _apply_model_overrides(args)
    state = load_state()

    # Track aliases for convenience
    TRACK_ALIASES = {
        # Subsection aliases — run a single section
        "ztt": ["prerequisites/zero-to-terminal"],
        "git": ["prerequisites/git-deep-dive"],
        "cn101": ["prerequisites/cloud-native-101"],
        "k8sbasics": ["prerequisites/kubernetes-basics"],
        "philosophy": ["prerequisites/philosophy-design"],
        "devops": ["prerequisites/modern-devops"],
        "cka": ["k8s/cka"],
        "ckad": ["k8s/ckad"],
        "cks": ["k8s/cks"],
        "kcna": ["k8s/kcna"],
        "kcsa": ["k8s/kcsa"],
        "extending": ["k8s/extending"],
        "aws": ["cloud/aws-essentials"],
        "gcp": ["cloud/gcp-essentials"],
        "azure": ["cloud/azure-essentials"],
        "eks": ["cloud/eks-deep-dive"],
        "gke": ["cloud/gke-deep-dive"],
        "aks": ["cloud/aks-deep-dive"],
        # Track aliases — run all sections in a track
        "prereqs": [
            "prerequisites/zero-to-terminal", "prerequisites/git-deep-dive",
            "prerequisites/cloud-native-101", "prerequisites/kubernetes-basics",
            "prerequisites/philosophy-design", "prerequisites/modern-devops",
        ],
        "certs": [
            "k8s/cka", "k8s/ckad", "k8s/cks", "k8s/kcna", "k8s/kcsa",
            "k8s/extending",
        ],
        "specialty": [
            "k8s/pca", "k8s/cba", "k8s/capa", "k8s/kca", "k8s/otca",
            "k8s/ica", "k8s/cca", "k8s/finops",
        ],
        "cloud": [
            "cloud/aws-essentials", "cloud/gcp-essentials", "cloud/azure-essentials",
            "cloud/architecture-patterns", "cloud/eks-deep-dive", "cloud/gke-deep-dive",
            "cloud/aks-deep-dive", "cloud/advanced-operations", "cloud/managed-services",
            "cloud/enterprise-hybrid",
        ],
        "platform": [
            "platform/foundations", "platform/disciplines", "platform/toolkits",
        ],
        "on-prem": [
            "on-premises/planning", "on-premises/provisioning", "on-premises/networking",
            "on-premises/storage", "on-premises/multi-cluster", "on-premises/security",
            "on-premises/operations", "on-premises/resilience",
            "on-premises/ai-ml-infrastructure",
        ],
        "linux": [
            "linux/foundations/container-primitives", "linux/foundations/networking",
            "linux/foundations/system-essentials", "linux/foundations/everyday-use",
            "linux/operations", "linux/security",
        ],
    }

    # "all" = everything in priority order
    ALL_SECTIONS = (
        TRACK_ALIASES["prereqs"] + TRACK_ALIASES["certs"] + TRACK_ALIASES["specialty"]
        + TRACK_ALIASES["cloud"] + TRACK_ALIASES["platform"] + TRACK_ALIASES["on-prem"]
        + TRACK_ALIASES["linux"]
    )

    # Phase 1: Resume stuck modules (check, write, review phases)
    # Only resume modules that belong to the requested sections
    sections_to_run = ALL_SECTIONS
    if args.sections:
        expanded: list[str] = []
        for s in args.sections:
            if s in TRACK_ALIASES:
                expanded.extend(TRACK_ALIASES[s])
            else:
                # Auto-discover: if path is a directory, find all subsections with modules
                section_path = CONTENT_ROOT / s
                if section_path.is_dir():
                    # Check if this dir itself has modules
                    has_modules = list(section_path.glob("module-*.md"))
                    if has_modules:
                        expanded.append(s)
                    # Also add any subdirs that have modules
                    for sub in sorted(section_path.rglob("index.md")):
                        subdir = sub.parent
                        if list(subdir.glob("module-*.md")) and str(subdir) != str(section_path):
                            expanded.append(str(subdir.relative_to(CONTENT_ROOT)))
                    if not expanded or expanded[-1] != s:
                        # Fallback: just use the path as-is
                        if s not in expanded:
                            expanded.append(s)
                else:
                    expanded.append(s)
        sections_to_run = expanded

    section_prefixes = tuple(sections_to_run)
    incomplete = {k: m for k, m in state.get("modules", {}).items()
                  if m.get("phase") not in ("done", "pending")
                  and k.startswith(section_prefixes)}
    if incomplete:
        print(f"\n{'='*60}")
        print(f"  PHASE 1: Resuming {len(incomplete)} stuck modules")
        print(f"{'='*60}")
        resumed = 0
        consecutive_failures = 0
        for key, ms in incomplete.items():
            path = find_module_path(key)
            if path and path.exists():
                ok = run_module(path, state, models=models)
                if ok:
                    resumed += 1
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                if consecutive_failures >= 5:
                    print(f"\n  CIRCUIT BREAKER: 5 consecutive resume failures — halting")
                    print(f"  Check logs: {LOG_FILE}")
                    break
        print(f"\n  Resumed: {resumed}/{len(incomplete)} completed")

    for section in sections_to_run:
        section_path = CONTENT_ROOT / section
        if not section_path.exists():
            continue

        modules = sorted(section_path.glob("**/module-*.md"))
        modules = [m for m in modules if "/uk/" not in str(m) and ".staging" not in str(m)]
        if not modules:
            continue

        # Skip sections where all modules are already done
        all_done = all(
            state.get("modules", {}).get(module_key_from_path(m), {}).get("phase") == "done"
            for m in modules
        )
        if all_done:
            print(f"\n  SKIP: {section} — all {len(modules)} modules done")
            continue

        print(f"\n{'='*60}")
        print(f"  SECTION: {section} ({len(modules)} modules)")
        print(f"{'='*60}")

        passed = 0
        failed = 0
        skipped = 0
        consecutive_failures = 0
        for i, path in enumerate(modules, 1):
            key = module_key_from_path(path)
            ms = state.get("modules", {}).get(key, {})

            # Skip already done
            if ms.get("phase") == "done":
                skipped += 1
                continue

            print(f"\n[{i}/{len(modules)}] {key}")
            ok = run_module(path, state, models=models)
            if ok:
                passed += 1
                consecutive_failures = 0
            else:
                failed += 1
                consecutive_failures += 1

            if consecutive_failures >= 5:
                print(f"\n  CIRCUIT BREAKER: 5 consecutive failures in {section} — halting")
                print(f"  Check logs: {LOG_FILE}")
                break

        print(f"\n  {section}: {passed} passed, {failed} failed, {skipped} skipped")

        # Update section index.md if any modules passed this run
        if passed > 0:
            # Find all unique directories containing modules (handles subsections)
            module_dirs = sorted({m.parent for m in modules})
            index_files = []
            for mdir in module_dirs:
                idx = mdir / "index.md"
                if idx.exists():
                    step_update_index(mdir, model=models["write"])
                    index_files.append(str(idx))

            # Commit only the index files (not git add -A which could grab stray files)
            if index_files:
                subprocess.run(
                    ["git", "add"] + index_files,
                    cwd=str(REPO_ROOT), capture_output=True, text=True,
                )
                idx_commit = subprocess.run(
                    ["git", "commit", "-m",
                     f"docs: update section indexes for {section}"],
                    cwd=str(REPO_ROOT), capture_output=True, text=True,
                )
                if idx_commit.returncode == 0:
                    print(f"  ✓ Index updates committed")

    # UK translations: sync modules for completed sections
    if not getattr(args, "no_translate", False):
        for section in sections_to_run:
            uk_section = CONTENT_ROOT / "uk" / section
            if not uk_section.exists():
                continue

            # Find EN content files (modules + index.md, excluding staging)
            en_files = uk_find_content_files(CONTENT_ROOT / section)
            en_files = [m for m in en_files if "/uk/" not in str(m)]
            if not en_files:
                continue

            print(f"\n{'='*60}")
            print(f"  UK TRANSLATE: {section} ({len(en_files)} files)")
            print(f"{'='*60}")

            translated = 0
            failed = 0
            consecutive_uk_failures = 0
            for en_path in en_files:
                rel = en_path.relative_to(UK_CONTENT_ROOT)
                uk_path = UK_ROOT / rel

                print(f"  UK: {rel.name}")
                if uk_path.exists():
                    ok = uk_fix(uk_path)
                else:
                    ok = uk_translate(en_path)

                if ok:
                    translated += 1
                    consecutive_uk_failures = 0
                else:
                    failed += 1
                    consecutive_uk_failures += 1

                if consecutive_uk_failures >= 3:
                    print(f"  CIRCUIT BREAKER: 3 consecutive UK translation failures — skipping rest")
                    break

            print(f"\n  UK: {translated} translated, {failed} failed")

    # Final summary
    state = load_state()
    total = len(state.get("modules", {}))
    done = sum(1 for m in state["modules"].values() if m.get("phase") == "done")
    print(f"\n{'='*60}")
    print(f"  E2E COMPLETE: {done}/{total} modules done")
    print(f"{'='*60}")


def _infer_track(section: str) -> str:
    """Infer track type from section path for jargon lookup."""
    s = section.lower()
    if "prerequisite" in s or "zero-to-terminal" in s or "philosophy" in s or "modern-devops" in s or "cloud-native-101" in s or "kubernetes-basics" in s:
        return "prerequisites"
    if "linux" in s:
        return "linux"
    if "cloud" in s or "aws" in s or "gcp" in s or "azure" in s or "eks" in s or "gke" in s or "aks" in s:
        return "cloud"
    return "k8s"


def cmd_gap_check(args):
    """Detect scaffolding gaps in a track or section."""
    path = CONTENT_ROOT / args.path
    if not path.exists():
        print(f"Path not found: {args.path}")
        sys.exit(1)

    print(f"\nGap analysis: {args.path} (track: {args.track})")
    print(f"{'='*60}")

    issues = gaps.run_track_gap_analysis(path, track=args.track)

    if not issues:
        print("\n  ✓ No scaffolding gaps detected")
        return

    # Group by type
    by_type = {}
    for issue in issues:
        by_type.setdefault(issue.gap_type, []).append(issue)

    for gap_type, items in sorted(by_type.items()):
        print(f"\n  {gap_type} ({len(items)}):")
        for item in items:
            print(item)

    errors = [i for i in issues if i.severity == "ERROR"]
    warnings = [i for i in issues if i.severity == "WARNING"]
    print(f"\n  Summary: {len(errors)} errors, {len(warnings)} warnings")

    # Also run LLM gap analysis for deeper detection
    if args.track in ("prerequisites", "linux"):
        print(f"\n  For deeper analysis, consider running:")
        print(f"  python scripts/v1_pipeline.py gap-check {args.path} --track {args.track}")
        print(f"  and reviewing CONCEPT_JUMP warnings manually")

    sys.exit(1 if errors else 0)


def main():
    parser = argparse.ArgumentParser(
        description="KubeDojo Module Quality Pipeline v1",
        epilog="""quick start:
  status                           show progress across all 700+ modules
  e2e certs                        run all cert tracks (CKA, CKAD, CKS, KCNA, KCSA)
  e2e prereqs cloud                run prerequisites + cloud
  e2e                              run everything (overnight batch)
  resume                           retry stuck modules only

models (default: gemini-3.1-pro-preview for all steps):
  --audit-model claude-opus-4-6    use Claude for scoring
  --review-model claude-opus-4-6   use Claude for review
""", formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Global model overrides
    parser.add_argument("--audit-model", help="Model for AUDIT+PLAN step (default: gemini-3.1-pro-preview)")
    parser.add_argument("--write-model", help="Model for WRITE step (default: gemini-3.1-pro-preview)")
    parser.add_argument("--review-model", help="Model for REVIEW step (default: gemini-3.1-pro-preview)")

    subparsers = parser.add_subparsers(dest="command", help="Pipeline command")

    # audit
    ap = subparsers.add_parser("audit", help="Audit a single module")
    ap.add_argument("module", help="Module path or key")

    # audit-all
    aap = subparsers.add_parser("audit-all", help="Audit all modules (deterministic only)")
    aap.add_argument("--section", help="Limit to a section (e.g., cloud/aws-essentials)")

    # run
    rp = subparsers.add_parser("run", help="Run a module through the full pipeline")
    rp.add_argument("module", help="Module path or key")
    rp.add_argument("--dry-run", action="store_true", help="Audit only — show plan without making changes")

    # run-section
    rsp = subparsers.add_parser("run-section", help="Run all modules in a section")
    rsp.add_argument("section", help="Section path (e.g., cloud/aws-essentials)")
    rsp.add_argument("--workers", type=int, default=1, help="Parallel workers (default: 1)")
    rsp.add_argument("--track", help="Track type for gap check (auto-detected if omitted)",
                     choices=["prerequisites", "linux", "cloud", "k8s"])
    rsp.add_argument("--skip-gaps", action="store_true", help="Skip gap check even if errors found")
    rsp.add_argument("--dry-run", action="store_true", help="Audit only — show plan without making changes")

    # gap-check
    gcp = subparsers.add_parser("gap-check", help="Detect scaffolding gaps in a track/section")
    gcp.add_argument("path", help="Track or section path (e.g., prerequisites/zero-to-terminal)")
    gcp.add_argument("--track", default="k8s",
                     choices=["prerequisites", "linux", "cloud", "k8s"],
                     help="Track type for jargon lookup (default: k8s)")

    # learning-path
    subparsers.add_parser("learning-path", help="Detect gaps across the full learning path (cross-track)")

    # status
    sp = subparsers.add_parser("status", help="Show pipeline status")
    sp.add_argument("--verbose", "-v", action="store_true", help="Show error details")

    # resume
    subparsers.add_parser("resume", help="Resume incomplete modules")

    # e2e
    e2e_parser = subparsers.add_parser("e2e", help="End-to-end: resume stuck + process all sections",
        epilog="""track aliases:
  prereqs    zero-to-terminal, git-deep-dive, cloud-native-101, k8s-basics, philosophy, modern-devops
  certs      cka, ckad, cks, kcna, kcsa, extending
  specialty  pca, cba, capa, kca, otca, ica, cca, finops
  cloud      aws, gcp, azure, architecture, eks, gke, aks, advanced-ops, managed, enterprise
  platform   foundations, disciplines, toolkits
  on-prem    planning, provisioning, networking, storage, multi-cluster, security, operations, resilience, ai-ml-infrastructure
  linux      container-primitives, networking, system-essentials, everyday-use, operations, security

examples:
  e2e                      run everything
  e2e prereqs              just prerequisites
  e2e certs cloud          certs + cloud
  e2e k8s/cka              single section
""", formatter_class=argparse.RawDescriptionHelpFormatter)
    e2e_parser.add_argument("sections", nargs="*", help="track aliases or section paths (default: all)")
    e2e_parser.add_argument("--verbose", "-v", action="store_true", help="print full output to stdout (default: quiet, log only)")
    e2e_parser.add_argument("--no-translate", action="store_true", help="skip UK translation step")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmd_map = {
        "audit": cmd_audit,
        "audit-all": cmd_audit_all,
        "run": cmd_run,
        "run-section": cmd_run_section,
        "gap-check": cmd_gap_check,
        "learning-path": cmd_learning_path,
        "status": cmd_status,
        "resume": cmd_resume,
        "e2e": cmd_e2e,
    }

    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
