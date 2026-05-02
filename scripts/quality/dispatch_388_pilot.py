#!/usr/bin/env python3
"""#388 Day 2 pilot dispatcher.

For each module in pilot-2026-05-02.txt:
  1. Worktree at .worktrees/codex-388-pilot-<slug> from origin/main
  2. Codex (gpt-5.5, mode=danger) rewrites per module-rewriter-388.md,
     runs verifier, commits, pushes, opens PR
  3. Gemini cross-family review on the PR (read-only)
  4. If APPROVE -> squash-merge with --delete-branch
  5. Brief pause; next module

Sequential per item. JSONL log at logs/388_pilot_2026-05-02.jsonl.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/Users/krisztiankoos/projects/kubedojo")
PILOT_FILE = REPO / "scripts/quality/pilot-2026-05-02.txt"
LOG = REPO / "logs/388_pilot_2026-05-02.jsonl"
BRIEF = REPO / "scripts/prompts/module-rewriter-388.md"
WRITER_BRIEF = REPO / "scripts/prompts/module-writer.md"

sys.path.insert(0, str(REPO / "scripts"))
from agent_runtime.runner import invoke  # noqa: E402
from agent_runtime.errors import (  # noqa: E402
    AgentTimeoutError,
    AgentUnavailableError,
    RateLimitedError,
)


def log(event: dict) -> None:
    event["ts"] = time.time()
    with open(LOG, "a") as f:
        f.write(json.dumps(event) + "\n")
    print(f"[{time.strftime('%H:%M:%S')}] {event.get('event')}: {event}", flush=True)


def slugify(path: str) -> str:
    stem = Path(path).stem
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")


def make_worktree(slug: str) -> Path:
    branch = f"codex/388-pilot-{slug}"
    wt = REPO / f".worktrees/codex-388-pilot-{slug}"
    if wt.exists():
        return wt
    subprocess.run(["git", "fetch", "origin", "main"], cwd=REPO, check=True)
    subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(wt), "origin/main"],
        cwd=REPO, check=True,
    )
    return wt


def codex_prompt(module_path: str) -> str:
    brief = BRIEF.read_text()
    writer = WRITER_BRIEF.read_text()
    return f"""You are rewriting one KubeDojo module to clear all #388 verifier gates.

MODULE TO REWRITE (relative to repo root): {module_path}

You are running in a fresh git worktree branched from origin/main. The full repo is checked out. You may read any file but must MODIFY ONLY the module path above.

PROCEDURE
1. Read the existing module to extract topic coverage, code blocks, ASCII/mermaid diagrams, tables, and source URLs. These are PROTECTED ASSETS — preserve them in the rewrite (you may rephrase surrounding prose).
2. Read scripts/prompts/module-rewriter-388.md (BELOW, BINDING) and scripts/prompts/module-writer.md (BELOW, structural baseline).
3. Rewrite the module IN PLACE at the path above.
4. Run the deterministic verifier:
     .venv/bin/python scripts/quality/verify_module.py --glob {module_path} --skip-source-check --summary --quiet
   Iterate until tier == T0 OR all density+structure+alignment+anti_leak+protected_assets gates pass. Sources gate may fail (we skip source check).
   Hard requirements: body_words >= 5000, mean_wpp >= 30, median_wpp >= 28, short_paragraph_rate <= 0.20, max_consecutive_short_run <= 2, exactly 4 Did You Know, 6-8 Common Mistakes, 6-8 Quiz with <details>, Hands-On with `- [ ]`. Section order per writer brief. No emojis. No number 47. K8s 1.35+. kubectl alias `k`.
5. Set frontmatter `revision_pending: false` (it is currently `true` — clear it as part of the rewrite). Then commit (sign-off optional, no --no-verify):
     git add {module_path}
     git commit -m "feat(388): density+structure rewrite of <module title> (#388 pilot)"
6. Push branch:
     git push -u origin HEAD
7. Open the PR:
     gh pr create --base main --title "feat(388): rewrite <slug> (#388 pilot)" --body "<body>"
   Body must include: verifier summary line (tiers + key metrics body_words/mean_wpp/median_wpp/short_rate/max_run), confirmation that protected assets were preserved with counts, and the commit SHA.
8. Reply with the PR URL on the last line.

DO NOT modify any file outside {module_path}. DO NOT change scripts/, docs/, sibling modules, or the verifier.

=== module-rewriter-388.md (BINDING) ===
{brief}

=== module-writer.md (structural baseline) ===
{writer}
"""


def dispatch_codex(module_path: str, wt: Path, slug: str):
    log({"event": "codex_dispatch_start", "module": module_path, "slug": slug, "wt": str(wt)})
    try:
        result = invoke(
            agent_name="codex",
            prompt=codex_prompt(module_path),
            mode="danger",
            cwd=wt,
            model="gpt-5.5",
            task_id=f"388-pilot-{slug}",
            entrypoint="dispatch",
            hard_timeout=5400,  # 90 min
        )
    except (AgentTimeoutError, RateLimitedError, AgentUnavailableError) as e:
        log({"event": "codex_error", "module": module_path, "error": repr(e)})
        return None
    log({
        "event": "codex_done",
        "module": module_path,
        "ok": result.ok,
        "elapsed_s": getattr(result, "elapsed_s", None),
        "response_excerpt": (result.response or "")[-2000:],
    })
    return result


def find_pr_number(text: str) -> int | None:
    m = re.search(r"github\.com/[^/]+/[^/]+/pull/(\d+)", text or "")
    return int(m.group(1)) if m else None


def gemini_review_prompt(pr_num: int, module_path: str) -> str:
    return f"""Adversary cross-family review of PR #{pr_num} on KubeDojo.

This is a #388 Day 2 pilot rewrite of: {module_path}

Per docs/review-protocol.md, you are the cross-family reviewer.

Inspect with `gh pr view {pr_num}` and `gh pr diff {pr_num}`. Then evaluate:

1. PEDAGOGY — Does it TEACH (Bloom's L3+)? Is the learning arc scaffolded? Are quiz questions scenario-based with reasoning explanations? Is there constructive alignment between Learning Outcomes, core sections, and the quiz/lab?
2. ACCURACY — All commands runnable? K8s 1.35+ surfaces? No hallucinated flags/APIs? Versions reasonable?
3. DENSITY DOES NOT EQUAL TEACHING — The deterministic verifier already gates on density. You must judge whether the prose is genuinely teaching or just padded to clear gates. Flag any padded paragraphs you find.
4. PROTECTED ASSETS — Code blocks, ASCII/mermaid diagrams, tables, source URLs preserved across the rewrite (counts in PR body should match).
5. SOURCES — Each source actually reaches a primary/vendor doc, not marketing fluff. Flag dead/redirect URLs if you can spot any.

End your review with EXACTLY ONE of:
  VERDICT: APPROVE
  VERDICT: APPROVE WITH NITS
  VERDICT: NEEDS CHANGES

Keep the review under 600 words.
"""


def dispatch_gemini_review(pr_num: int, module_path: str, slug: str):
    log({"event": "gemini_review_start", "pr": pr_num, "module": module_path})
    try:
        result = invoke(
            agent_name="gemini",
            prompt=gemini_review_prompt(pr_num, module_path),
            mode="workspace-write",  # needs gh shell access
            cwd=REPO,
            task_id=f"388-pilot-review-{slug}",
            entrypoint="dispatch",
            hard_timeout=900,
        )
    except Exception as e:  # noqa: BLE001
        log({"event": "gemini_error", "pr": pr_num, "error": repr(e)})
        return None, "ERROR"
    text = result.response or ""
    log({"event": "gemini_done", "pr": pr_num, "ok": result.ok, "response_excerpt": text[-2000:]})
    upper = text.upper()
    if "VERDICT: NEEDS CHANGES" in upper or "NEEDS CHANGES" in upper.split("VERDICT:")[-1]:
        verdict = "NEEDS CHANGES"
    elif "VERDICT: APPROVE" in upper:
        verdict = "APPROVE"
    else:
        verdict = "UNCLEAR"
    return text, verdict


def post_review_comment(pr_num: int, body: str) -> None:
    subprocess.run(
        ["gh", "pr", "comment", str(pr_num), "--body",
         f"## Gemini cross-family review (#388 pilot)\n\n{body}"],
        cwd=REPO, check=False,
    )


def merge_pr(pr_num: int) -> None:
    subprocess.run(
        ["gh", "pr", "merge", str(pr_num), "--squash", "--delete-branch"],
        cwd=REPO, check=False,
    )


def main() -> int:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    pilot = [l.strip() for l in PILOT_FILE.read_text().splitlines() if l.strip()]
    log({"event": "pilot_start", "count": len(pilot)})
    for module_path in pilot:
        slug = slugify(module_path)
        log({"event": "module_start", "module": module_path, "slug": slug})
        try:
            wt = make_worktree(slug)
        except Exception as e:  # noqa: BLE001
            log({"event": "worktree_error", "module": module_path, "error": repr(e)})
            continue
        codex_result = dispatch_codex(module_path, wt, slug)
        if codex_result is None or not codex_result.ok:
            log({"event": "module_skip", "module": module_path, "reason": "codex_failed"})
            continue
        pr_num = find_pr_number(codex_result.response or "")
        if pr_num is None:
            log({"event": "module_skip", "module": module_path, "reason": "no_pr_in_response"})
            continue
        review_text, verdict = dispatch_gemini_review(pr_num, module_path, slug)
        if review_text:
            post_review_comment(pr_num, review_text)
        if verdict == "APPROVE":
            merge_pr(pr_num)
            log({"event": "merged", "pr": pr_num, "module": module_path})
        else:
            log({"event": "merge_held", "pr": pr_num, "module": module_path, "verdict": verdict})
        time.sleep(5)
    log({"event": "pilot_done"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
