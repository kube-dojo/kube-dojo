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
import fcntl
import json
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

# Add scripts to path for imports
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from checks import structural, ukrainian
from dispatch import (
    dispatch_gemini_with_retry,
    dispatch_claude,
)

# ---------------------------------------------------------------------------
# Model configuration (overridable via CLI)
# ---------------------------------------------------------------------------

MODELS = {
    "audit": "claude-opus-4-6",          # AUDIT+PLAN: nuanced rubric evaluation + plan
    "write": "gemini-3.1-pro-preview",   # WRITE: draft improvements (Pro for quality)
    "review": "claude-opus-4-6",         # REVIEW: strict rubric review (Opus catches more)
    "translate": "gemini-3.1-pro-preview",  # TRANSLATE: Ukrainian with MCP
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
    """Save state with file locking for thread safety."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock_file = STATE_FILE.with_suffix(".lock")
    with open(lock_file, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            STATE_FILE.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False))
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
    rel = path.relative_to(CONTENT_ROOT)
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
    ok, output = dispatch_claude(prompt, model=model, timeout=120)

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

    scores = result.get("scores", [])
    if len(scores) != 7:
        print(f"  ❌ Expected 7 scores, got {len(scores)}")
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

WRITE_PROMPT_TEMPLATE = """You are improving a KubeDojo module. You will receive the current module content and an improvement plan.

RULES:
- Output the COMPLETE improved module (full file replacement)
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


def step_write(module_path: Path, plan: str, model: str = MODELS["write"]) -> str | None:
    """Gemini drafts improvements based on the plan."""
    content = module_path.read_text()
    key = module_key_from_path(module_path)
    print(f"\n  WRITE: {key} (using {model})")

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

    ok, output = dispatch_claude(prompt, model=model, timeout=120)

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

    verdict = result.get("verdict", "REJECT")
    scores = result.get("scores", [])
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
               models: dict | None = None) -> bool:
    """Run a single module through the full pipeline."""
    m = models or MODELS
    key = module_key_from_path(module_path)
    ms = get_module_state(state, key)

    print(f"\n{'='*60}")
    print(f"  PIPELINE: {key}")
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

        ms["phase"] = "write"
        save_state(state)
    else:
        # Resuming — reconstruct plan from state
        plan = f"Resume improvement. Last scores: {ms.get('scores', 'unknown')}."

    # WRITE → REVIEW loop (max retries)
    improved = None
    for attempt in range(max_retries + 1):
        if ms["phase"] in ("write",):
            improved = step_write(module_path, plan, model=m["write"])
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
    if ms["phase"] == "check" and improved:
        passed, results = step_check(improved, module_path)
        if not passed:
            ms["errors"].append("Deterministic checks failed after review")
            save_state(state)
            return False

        # Write the improved file
        module_path.write_text(improved)
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
    ok = run_module(path, state, models=models)
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

    workers = args.workers or 1

    if workers == 1:
        for i, path in enumerate(modules, 1):
            key = module_key_from_path(path)
            print(f"\n[{i}/{len(modules)}] {key}")
            ok = run_module(path, state, models=models)
            if ok:
                passed += 1
            else:
                failed += 1
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(run_module, path, state, 2, models): path
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
    print(f"  DONE: {passed} passed, {failed} failed out of {len(modules)}")
    print(f"{'='*60}")

    sys.exit(0 if failed == 0 else 1)


def cmd_status(args):
    """Show pipeline status."""
    state = load_state()
    modules = state.get("modules", {})

    if not modules:
        print("No modules processed yet.")
        return

    by_phase = {}
    for key, ms in modules.items():
        phase = ms.get("phase", "unknown")
        by_phase.setdefault(phase, []).append(key)

    print(f"\nPipeline status: {len(modules)} modules tracked\n")
    for phase in PHASES + ["unknown"]:
        if phase in by_phase:
            print(f"  {phase:10s}: {len(by_phase[phase])}")

    # Show failures
    failed = [k for k, m in modules.items() if m.get("errors")]
    if failed:
        print(f"\n  Modules with errors: {len(failed)}")
        for k in failed[:10]:
            latest_error = modules[k]["errors"][-1] if modules[k]["errors"] else "?"
            print(f"    {k}: {latest_error}")
        if len(failed) > 10:
            print(f"    ... and {len(failed) - 10} more")


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

    models = dict(MODELS)
    if args.audit_model:
        models["audit"] = args.audit_model

    for key, ms in incomplete.items():
        path = find_module_path(key)
        if path and path.exists():
            run_module(path, state, models=models)


def main():
    parser = argparse.ArgumentParser(
        description="KubeDojo Module Quality Pipeline v1",
    )
    # Global model overrides
    parser.add_argument("--audit-model", help="Model for AUDIT+PLAN step")
    parser.add_argument("--write-model", help="Model for WRITE step")
    parser.add_argument("--review-model", help="Model for REVIEW step")

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

    # run-section
    rsp = subparsers.add_parser("run-section", help="Run all modules in a section")
    rsp.add_argument("section", help="Section path (e.g., cloud/aws-essentials)")
    rsp.add_argument("--workers", type=int, default=1, help="Parallel workers (default: 1)")

    # status
    subparsers.add_parser("status", help="Show pipeline status")

    # resume
    subparsers.add_parser("resume", help="Resume incomplete modules")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmd_map = {
        "audit": cmd_audit,
        "audit-all": cmd_audit_all,
        "run": cmd_run,
        "run-section": cmd_run_section,
        "status": cmd_status,
        "resume": cmd_resume,
    }

    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
