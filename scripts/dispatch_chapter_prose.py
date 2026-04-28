"""Dispatch the prose pipeline for an AI History chapter (#394).

Per the 2026-04-28 research role split:
- Part 1, 2, 6, 7: Gemini drafts ~3k words, Claude opus-4-7 expands to
  the verdict-capped target (typically 4-5k words).
- Part 3 (Ch11-16): Codex drafts, Claude expands.

This script handles the **Gemini → Claude** flow (Parts 1, 2, 6, 7).
The Codex variant (Part 3) is handled by `dispatch_chapter_research.py`'s
prose mode — different beast.

Approach: do NOT depend on the research PR being merged. Read the
contract files from the research branch via `git show` and embed them
in the dispatch prompt. Prose worktree branches off main, prose PR
opens against main with only the prose file diff.

Usage:
    .venv/bin/python scripts/dispatch_chapter_prose.py 1 \
        --slug ch-01-the-laws-of-thought \
        --research-branch claude/394-ch01-research \
        --cap-words 5000 \
        --verdict-notes-pr 456 \
        --phases gemini,claude

Phases default to "gemini,claude" (full pipeline). Use "gemini" alone
to fire just the draft, "claude" alone to expand a pre-drafted file.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

REPO = Path("/Users/krisztiankoos/projects/kubedojo")

CONTRACT_FILES = ["brief.md", "sources.md", "scene-sketches.md",
                  "timeline.md", "people.md", "infrastructure-log.md",
                  "open-questions.md", "status.yaml"]


def read_branch_file(branch: str, path: str) -> str:
    subprocess.run(
        ["git", "fetch", "origin", branch],
        cwd=REPO, capture_output=True, check=False,
    )
    r = subprocess.run(
        ["git", "show", f"origin/{branch}:{path}"],
        cwd=REPO, capture_output=True, text=True,
    )
    return r.stdout if r.returncode == 0 else ""


def gather_contract(*, research_branch: str, slug: str) -> str:
    chunks = []
    for fn in CONTRACT_FILES:
        body = read_branch_file(
            research_branch,
            f"docs/research/ai-history/chapters/{slug}/{fn}",
        )
        if not body:
            continue
        chunks.append(f"### `{fn}`\n\n```\n{body}\n```\n")
    return "\n".join(chunks)


def fetch_pr_verdicts(pr_num: int) -> str:
    """Pull the codex+gemini verdict comments from a PR so the drafter
    sees the cap rationale."""
    out = subprocess.run(
        ["gh", "pr", "view", str(pr_num), "--json", "comments",
         "--jq", '.comments[] | select(.body | startswith("<!-- verdict")) | .body'],
        cwd=REPO, capture_output=True, text=True, check=False,
    ).stdout
    return out or "(no verdict comments retrieved)"


def gemini_prompt(*, slug: str, ch_num: int, cap_words: int,
                  contract: str, verdicts: str, prose_path: str) -> str:
    return dedent(f"""\
        # Task: Draft prose for Chapter {ch_num} (`{slug}`) (#394)

        You have **workspace-write** in this worktree. Replace the
        existing short stub at `{prose_path}` with a fresh draft based
        on the anchored research contract below.

        ## Role split (effective 2026-04-28)

        For Part 1/2/6/7 chapters, **you draft first** (target ~3,000
        words, anchored, structurally complete). Claude then expands to
        the verdict-capped target. Don't try to hit the final word
        count yourself — write a tight, evidence-backed first draft;
        Claude will expand the technical and biographical layers from
        the same contract.

        ## Hard rules

        1. **Cap: {cap_words} words.** Do NOT exceed. The verdict
           reviewers (Codex + Gemini) capped this chapter; the cap
           reflects evidence density, not arbitrariness.
        2. **No fabricated URLs, page numbers, DOIs, or quotes.** Every
           citation in the prose must trace to an entry in the
           contract's `sources.md`. If you can't anchor a claim, weaken
           the claim — never invent a source.
        3. **Use the Boundary Contract.** The brief defines what the
           chapter is NOT. Don't anticipate later chapters.
        4. **Yellow claims hedge; Red claims stay out.** If a claim is
           Yellow in `sources.md`, prose must hedge ("according to
           Hailperin", "is sometimes argued"). Red claims do not appear
           in prose except as flagged open questions.
        5. **Frontmatter required.** First lines:
           ```
           ---
           title: "Chapter {ch_num}: <Title from brief>"
           description: "<one-sentence chapter hook>"
           sidebar:
             order: {ch_num}
           ---
           ```
        6. **No emoji.** No bullet-list "list of facts" sections —
           narrative prose only.

        ## Verdicts (with caveats — respect them)

        {verdicts}

        ## Research contract

        {contract}

        ## Workflow

        1. Read the contract files above. Internalize the brief's
           Prose Capacity Plan.
        2. Replace `{prose_path}` with your draft. Use the title
           from `brief.md`'s thesis. Use scene structure from
           `scene-sketches.md`.
        3. Self-check: word count ≤ {cap_words}; every Green claim has
           a `sources.md`-traceable phrasing; Yellow claims are
           hedged; Red claims absent.
        4. `git add {prose_path}` and commit:
           ```
           docs(ch-{ch_num:02d}): draft prose against anchored contract (#394)
           ```
        5. Print word count and any claims you couldn't anchor.

        Do NOT push. The orchestrator handles PR creation after Claude
        expansion.
        """)


def claude_prompt(*, slug: str, ch_num: int, cap_words: int,
                  contract: str, verdicts: str, prose_path: str) -> str:
    return dedent(f"""\
        # Task: Expand and tighten Chapter {ch_num} prose (`{slug}`) (#394)

        You have **workspace-write** in this worktree. Gemini drafted
        prose at `{prose_path}` against the anchored research contract.
        Your job is to expand the draft from ~3k to {cap_words} words
        while sharpening anchor discipline and tightening narrative
        coherence.

        ## What "expand" means here (it's NOT padding)

        Per the contract's Prose Capacity Plan, each layer of the plan
        cites specific page anchors in `sources.md`. Gemini's draft
        likely covers the structural skeleton but under-uses the
        technical and biographical layers. Your expansion budget should
        go to:

        - **Technical density**: equations, system mechanics, what
          actually happened in the science, anchored to `sources.md`.
        - **Infrastructure detail**: from `infrastructure-log.md`.
        - **Anchored biographical scenes**: tight scenes citing
          specific page numbers from biographies/oral histories.
        - **Conflict notes**: where the historical record disagrees,
          show the disagreement instead of papering over it.

        DO NOT pad with:
        - Generic textbook explanation
        - Repeated summary
        - Modern hindsight
        - Unanchored deployment scale or business impact

        ## Hard rules

        1. **Cap: {cap_words} words. Hard cap, not target.**
        2. **No fabricated URLs, page numbers, DOIs, quotes.**
        3. **Yellow → hedge; Red → out.** Same as Gemini's instructions.
        4. **Preserve Gemini's good prose.** This is expansion, not
           rewrite. Surgical paragraph additions and targeted edits, not
           wholesale replacement.
        5. **No emoji. No bullet-list facts.**

        ## Verdict caveats

        {verdicts}

        ## Research contract

        {contract}

        ## Workflow

        1. Read `{prose_path}` (Gemini's draft) and the contract files
           above.
        2. Identify under-developed Plan layers. Add anchored content
           targeted at those layers. Tighten any unanchored claims
           Gemini left in.
        3. Run `wc -w {prose_path}` after each substantial edit to
           stay under the cap.
        4. `git add {prose_path}` and commit:
           ```
           docs(ch-{ch_num:02d}): expand prose to verdict cap with anchored layers (#394)
           ```
        5. Print final word count and the layers you expanded.
        """)


def setup_worktree(*, ch_num: int, slug: str) -> tuple[Path, str]:
    """Create or reuse `.worktrees/prose-394-chNN`."""
    branch = f"prose/394-ch{ch_num:02d}"
    worktree = REPO / f".worktrees/prose-394-ch{ch_num:02d}"
    if worktree.exists():
        print(f"[setup] worktree already exists: {worktree} — reusing")
        return worktree, branch
    subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(worktree), "main"],
        cwd=REPO, check=True,
    )
    return worktree, branch


def fire_phase(*, agent: str, prompt: str, worktree: Path, task_id: str,
               log_path: Path) -> bool:
    sys.path.insert(0, str(REPO / "scripts"))
    from agent_runtime.runner import invoke

    if agent == "gemini":
        model = "gemini-3.1-pro-preview"
        timeout = 2400
    elif agent == "claude":
        model = "claude-opus-4-7"
        timeout = 3600
    else:
        raise ValueError(agent)

    print(f"[fire] {agent} ({model}) on {task_id}")
    r = invoke(
        agent, prompt,
        mode="workspace-write",
        cwd=worktree,
        model=model,
        task_id=task_id,
        entrypoint="delegate",
        hard_timeout=timeout,
    )
    log_path.write_text("\n".join([
        f"OK: {r.ok}",
        f"session_id: {r.session_id}",
        f"response chars: {len(r.response or '')}",
        "=" * 70,
        r.response or "(no response)",
        "=" * 70,
        f"stderr_excerpt: {r.stderr_excerpt or '(none)'}",
    ]))
    print(f"[fire] {agent} OK={r.ok}, log -> {log_path}")
    return r.ok


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("ch_num", type=int)
    p.add_argument("--slug", required=True)
    p.add_argument("--research-branch", required=True)
    p.add_argument("--cap-words", type=int, required=True)
    p.add_argument("--verdict-notes-pr", type=int, default=None,
                   help="PR number to fetch codex+gemini verdict notes from")
    p.add_argument("--phases", default="gemini,claude",
                   help="comma-separated: gemini,claude or just one")
    args = p.parse_args()

    contract = gather_contract(
        research_branch=args.research_branch, slug=args.slug,
    )
    if not contract:
        print(f"[err] no contract found on branch {args.research_branch}",
              file=sys.stderr)
        return 1

    verdicts = ""
    if args.verdict_notes_pr is not None:
        verdicts = fetch_pr_verdicts(args.verdict_notes_pr)

    worktree, branch = setup_worktree(ch_num=args.ch_num, slug=args.slug)
    prose_path = f"src/content/docs/ai-history/{args.slug}.md"

    phases = [s.strip() for s in args.phases.split(",") if s.strip()]
    for phase in phases:
        if phase == "gemini":
            prompt = gemini_prompt(
                slug=args.slug, ch_num=args.ch_num,
                cap_words=args.cap_words, contract=contract,
                verdicts=verdicts, prose_path=prose_path,
            )
            log = Path(f"/tmp/prose-ch{args.ch_num:02d}-gemini.log")
            ok = fire_phase(
                agent="gemini", prompt=prompt, worktree=worktree,
                task_id=f"prose-{args.slug}-gemini", log_path=log,
            )
            if not ok:
                print("[main] Gemini phase FAILED, stopping pipeline")
                return 2
        elif phase == "claude":
            prompt = claude_prompt(
                slug=args.slug, ch_num=args.ch_num,
                cap_words=args.cap_words, contract=contract,
                verdicts=verdicts, prose_path=prose_path,
            )
            log = Path(f"/tmp/prose-ch{args.ch_num:02d}-claude.log")
            ok = fire_phase(
                agent="claude", prompt=prompt, worktree=worktree,
                task_id=f"prose-{args.slug}-claude", log_path=log,
            )
            if not ok:
                print("[main] Claude phase FAILED")
                return 3
        else:
            print(f"[err] unknown phase: {phase}", file=sys.stderr)
            return 1

    print(f"[done] worktree={worktree} branch={branch}")
    print(f"[next] cd {worktree} && git push -u origin {branch} "
          f"&& gh pr create --title 'Prose: Chapter {args.ch_num} ({args.slug}) (#394)' --body ...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
