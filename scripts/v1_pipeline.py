#!/usr/bin/env python3
"""KubeDojo Module Quality Pipeline — v1.

Processes each module through all 7 quality dimensions to reach 29/35.
Uses Gemini for writing/translating, Claude for evaluation/review,
and deterministic Python checks as quality gates.

Usage:
    python scripts/v1_pipeline.py audit <module-path>
    python scripts/v1_pipeline.py audit-all [--section cloud/aws-essentials]
    python scripts/v1_pipeline.py run <module-path>
    python scripts/v1_pipeline.py run-section <section-path>
    python scripts/v1_pipeline.py status
    python scripts/v1_pipeline.py resume
"""

from __future__ import annotations

import argparse
import builtins
import fcntl
import json
import os
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
    elif any(k in msg for k in ("PASS", "FAIL", "CIRCUIT", "E2E COMPLETE", "SECTION:", "PHASE 1",
                                  "SKIP:", "Resumed:", "passed,", "BREAKER")):
        _original_print(*args, **kwargs)


builtins.print = _logged_print

# Add scripts to path for imports
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from checks import structural, ukrainian, gaps
from dispatch import (
    dispatch_gemini_with_retry,
    dispatch_claude,
)


def dispatch_auto(prompt: str, model: str, timeout: int = 120) -> tuple[bool, str]:
    """Route to Gemini or Claude based on model name."""
    if model.startswith("gemini"):
        return dispatch_gemini_with_retry(prompt, model=model, timeout=timeout)
    if model.startswith("claude"):
        return dispatch_claude(prompt, model=model, timeout=timeout)
    raise ValueError(f"Unknown model family: {model!r} — must start with 'gemini' or 'claude'")


# ---------------------------------------------------------------------------
# Model configuration (overridable via CLI)
# ---------------------------------------------------------------------------

MODELS = {
    "audit": "gemini-3.1-pro-preview",     # AUDIT+PLAN: rubric evaluation + plan
    "write": "gemini-3.1-pro-preview",     # WRITE: draft improvements
    "review": "gemini-3.1-pro-preview",    # REVIEW: strict rubric review
    "translate": "gemini-3.1-pro-preview", # TRANSLATE: Ukrainian with MCP
}

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

RUBRIC_PROMPT = """You are scoring a KubeDojo module against 7 quality dimensions.

Score each dimension 1-5 using the rubric below. Be STRICT — a 4 means genuinely good, not just "present."

## Dimensions
D1 Learning Outcomes: 4 = clear, measurable, Bloom's L3+. 5 = testable, every outcome delivered.
D2 Scaffolding: 4 = clear progression, explicit bridges. 5 = worked examples before practice, complexity gradient.
D3 Active Learning: 4 = multiple inline prompts, scenario quizzes. 5 = woven throughout, learner constructs knowledge.
D4 Real-World: 4 = war stories with specific impact, common mistakes table. 5 = integrated throughout, honest trade-offs.
D5 Assessment: 4 = tests analysis not recall, explains WHY. 5 = aligned with every outcome, progressive difficulty.
D6 Cognitive Load: 4 = good chunking, diagrams with text, worked examples. 5 = split-attention eliminated, dual coding.
D7 Engagement: 4 = conversational, strong hook, good analogies. 5 = memorable, reader would recommend.

## Instructions
1. Read the module carefully.
2. Score each dimension 1-5.
3. For any dimension below 4, explain SPECIFICALLY what's missing.
4. Output ONLY this JSON (no markdown, no explanation outside JSON):

{"scores": [D1, D2, D3, D4, D5, D6, D7], "notes": {"D1": "...", "D2": "...", ...}, "plan": "If any dimension < 4, write a specific improvement plan. If all >= 4, write 'PASS'."}
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
    ok, output = dispatch_auto(prompt, model=model, timeout=120)

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
    if not isinstance(scores, list) or len(scores) != 7:
        print(f"  ❌ Expected 7 scores, got {scores!r}")
        return None

    try:
        scores = [int(s) for s in scores]
    except (ValueError, TypeError):
        print(f"  ❌ Non-numeric scores: {scores}")
        return None

    total = sum(scores)
    minimum = min(scores)
    passes = minimum >= 4 and total >= 29

    print(f"\n  Scores: {scores}")
    print(f"  Sum: {total}/35 | Min: {minimum} | {'PASS' if passes else 'FAIL'}")

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

IMPROVEMENT PLAN:
{plan}

---

CURRENT MODULE:
{content}
"""


REWRITE_PROMPT_TEMPLATE = """CRITICAL INSTRUCTION: Your response must be ONLY the raw markdown content. Start with the --- frontmatter delimiter. No preamble, no explanation — ONLY the markdown file.

TASK: Write a complete KubeDojo educational module FROM SCRATCH. The existing module scored too low to improve — rewrite it completely.

The file path is: {file_path}
Keep the EXACT same frontmatter (title, slug, sidebar order).

Use the existing module ONLY for topic reference — do NOT preserve its structure or text.

TOPICS TO COVER (from audit):
{plan}

QUALITY REQUIREMENTS:
- 600-800 lines of content minimum (visual aids don't count toward this)
- Learning Outcomes: 3-5 measurable, Bloom's L3+ verbs (debug, design, evaluate, compare, diagnose, implement)
- Why This Module Matters: open with dramatic real-world incident, real company, real financial impact. 2-3 paragraphs.
- Core content (3-6 sections): explanations with analogies, runnable code blocks, ASCII diagrams, tables, war stories
- At least 2 inline active learning prompts distributed throughout: > **Pause and predict**: or > **Stop and think**:
- Did You Know?: exactly 4 facts with real numbers/dates
- Common Mistakes: table with 6-8 rows (Mistake | Why | Fix)
- Quiz: 6-8 questions in <details> tags, at least 4 scenario-based. Answers 3-5 sentences explaining WHY.
- Hands-On Exercise: 4-6 progressive tasks with solutions in <details> tags, success checklist
- Next Module: link with teaser
- NO emojis, NO recall quiz questions, NO thin outlines, NO number 47

EXISTING MODULE (for topic reference only):
{content}
"""


def step_write(module_path: Path, plan: str, model: str = MODELS["write"],
               rewrite: bool = False) -> str | None:
    """Gemini drafts improvements or full rewrite based on the plan."""
    content = module_path.read_text()
    key = module_key_from_path(module_path)
    mode = "REWRITE" if rewrite else "WRITE"
    print(f"\n  {mode}: {key} (using {model})")

    if rewrite:
        prompt = REWRITE_PROMPT_TEMPLATE.format(
            file_path=key, plan=plan, content=content)
    else:
        prompt = WRITE_PROMPT_TEMPLATE.format(plan=plan, content=content)

    ok, output = dispatch_gemini_with_retry(prompt, model=model, timeout=300)

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

    print(f"  ✓ WRITE produced {len(output)} chars")
    return output


# ---------------------------------------------------------------------------
# REVIEW step — Claude strict review
# ---------------------------------------------------------------------------

REVIEW_PROMPT_TEMPLATE = """You are the STRICT quality reviewer for KubeDojo. A module has been improved by another LLM.

Your job: compare the improved version against the quality rubric. Be EXTREMELY strict.

RULES:
1. Score all 7 dimensions 1-5
2. If ANY dimension is below 4: REJECT and explain what's wrong
3. If the improved version removed content, diagrams, or code blocks: REJECT
4. If quiz questions are recall-based instead of scenario-based: REJECT
5. If inline prompts are trivial or have obvious answers: REJECT

Output ONLY this JSON:
{{"verdict": "APPROVE" or "REJECT", "scores": [D1-D7], "feedback": "specific feedback if REJECT"}}

---

ORIGINAL MODULE:
{original}

---

IMPROVED MODULE:
{improved}
"""


def step_review(module_path: Path, improved: str, model: str = MODELS["review"]) -> dict | None:
    """Claude reviews the improved module strictly."""
    original = module_path.read_text()
    key = module_key_from_path(module_path)
    print(f"\n  REVIEW: {key} (using {model})")

    prompt = REVIEW_PROMPT_TEMPLATE.format(original=original, improved=improved)

    ok, output = dispatch_auto(prompt, model=model, timeout=120)

    if not ok:
        print(f"  ❌ REVIEW failed")
        return None

    try:
        json_match = output.strip()
        if json_match.startswith("```"):
            json_match = json_match.split("```")[1]
            if json_match.startswith("json"):
                json_match = json_match[4:]
        result = json.loads(json_match)
    except (json.JSONDecodeError, IndexError):
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

        if audit["passes"] and audit["check_errors"] == 0:
            print(f"\n  ✓ Module already passes! ({audit['sum']}/35)")
            ms["phase"] = "done"
            save_state(state)
            return True

        plan = audit.get("plan", "")
        if not plan or plan == "PASS":
            plan = f"Improve weak dimensions. Scores: {audit['scores']}. Notes: {audit.get('notes', {})}"

        if dry_run:
            print(f"\n  [DRY RUN] Would improve: {[f'D{i+1}={s}' for i, s in enumerate(audit['scores']) if s < 4]}")
            print(f"  [DRY RUN] Plan: {plan[:300]}")
            return False

        ms["phase"] = "write"
        save_state(state)
    else:
        # Resuming — reconstruct plan from state
        plan = f"Resume improvement. Last scores: {ms.get('scores', 'unknown')}."

    # WRITE → REVIEW loop (max retries)
    # Auto-detect rewrite mode: score < 25 means "improve" won't cut it
    needs_rewrite = (ms.get("sum") or 0) < 25
    if needs_rewrite:
        print(f"  Score {ms.get('sum')}/35 < 25 — using REWRITE mode")

    improved = None
    for attempt in range(max_retries + 1):
        if ms["phase"] in ("write",):
            improved = step_write(module_path, plan, model=m["write"],
                                  rewrite=needs_rewrite)
            if improved is None:
                ms["errors"].append(f"Write failed attempt {attempt+1}")
                save_state(state)
                if attempt < max_retries:
                    continue
                return False

            ms["phase"] = "review"
            save_state(state)

        if ms["phase"] == "review":
            review = step_review(module_path, improved or module_path.read_text(), model=m["review"])
            if review is None:
                ms["errors"].append(f"Review failed attempt {attempt+1}")
                ms["phase"] = "write"
                save_state(state)
                if attempt < max_retries:
                    continue
                return False

            if review.get("verdict") == "APPROVE":
                # Save review scores (these reflect the IMPROVED content)
                if review.get("scores") and len(review["scores"]) == 7:
                    ms["scores"] = review["scores"]
                    ms["sum"] = sum(review["scores"])
                ms["phase"] = "check"
                save_state(state)
                break
            else:
                # Rejected — feed back to WRITE
                plan = f"PREVIOUS REVIEW REJECTED. Feedback: {review.get('feedback', '')}. Fix these issues."
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
        scores = ms.get("scores", [4, 4, 4, 4, 4, 4, 4])
        total = sum(scores)
        minimum = min(scores)
        passes = minimum >= 4 and total >= 29

        ms["passes"] = passes
        ms["sum"] = total
        ms["phase"] = "done" if passes else "score"
        ms["last_run"] = datetime.now(UTC).isoformat()
        save_state(state)

        if passes:
            print(f"\n  ✓ PASS: {total}/35 (min: {minimum})")
            # Auto-commit
            add_result = subprocess.run(
                ["git", "add", str(module_path)],
                cwd=str(REPO_ROOT), capture_output=True, text=True,
            )
            if add_result.returncode != 0:
                print(f"  ⚠ git add failed: {add_result.stderr[:200]}")

            commit_result = subprocess.run(
                ["git", "commit", "-m",
                 f"chore(quality): v1 pipeline pass [{key}] ({total}/35)"],
                cwd=str(REPO_ROOT), capture_output=True, text=True,
            )
            if commit_result.returncode != 0:
                print(f"  ⚠ git commit failed: {commit_result.stderr[:200]}")
            else:
                print(f"  ✓ Committed")
            return True
        else:
            print(f"\n  ✗ FAIL: {total}/35 (min: {minimum}) — needs manual intervention")
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
    modules = [m for m in modules if "/uk/" not in str(m)]

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
    modules = [m for m in modules if "/uk/" not in str(m)]

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
    if parts[0] in ("cloud", "platform", "on-premises"):
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

    print(f"\n  Modules: {g_total} total | {g_pass} pass (29+) | {g_fail} fail | {g_wip} in progress | {g_todo} not started")
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
        modules = [m for m in modules if "/uk/" not in str(m)]
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
  on-prem    planning, provisioning, networking, storage, multi-cluster, security, operations, resilience
  linux      container-primitives, networking, system-essentials, everyday-use, operations, security

examples:
  e2e                      run everything
  e2e prereqs              just prerequisites
  e2e certs cloud          certs + cloud
  e2e k8s/cka              single section
""", formatter_class=argparse.RawDescriptionHelpFormatter)
    e2e_parser.add_argument("sections", nargs="*", help="track aliases or section paths (default: all)")
    e2e_parser.add_argument("--verbose", "-v", action="store_true", help="print full output to stdout (default: quiet, log only)")

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
