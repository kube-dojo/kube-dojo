"""Dispatch the prose pipeline for an AI History chapter (#394).

Per the 2026-04-29 prose pipeline pivot (TEAM_WORKFLOW.md § 5):

    Approved contract → Gemini first draft (~3k) →
        Codex expansion to cap (DEFAULT)
        Claude expansion (FALLBACK when Codex bandwidth exhausted)
        → Claude source-fidelity review
        → Gemini or Claude prose-quality review
        → merge

Both expansion paths obey the same strict-source rule: use only the
provided contract and claim matrix; if evidence is missing for a
scene, leave the scene thin rather than filling it. Do not add
sources, do not introduce page anchors, do not upgrade Yellow claims,
do not invent examples, do not expand beyond the approved Prose
Capacity Plan.

The 2026-04-28 → 2026-04-29 difference: previously the expansion role
went to Claude opus by default; now it goes to Codex (gpt-5.5,
reasoning=high) because gpt-5.5 has wider weekly bandwidth and
Codex's source-discipline instinct is the strongest of the three
families. Claude opus stays in the loop as the source-fidelity
reviewer (independent fresh session), and as the expansion fallback.

Approach: do NOT depend on the research PR being merged. Read the
contract files from the research branch via `git show` and embed them
in the dispatch prompt. Prose worktree branches off main, prose PR
opens against main with only the prose file diff.

Usage:
    .venv/bin/python scripts/dispatch_chapter_prose.py 6 \
        --slug ch-06-the-cybernetics-movement \
        --research-branch claude/394-ch06-research \
        --cap-words 5000 \
        --verdict-notes-pr 467 \
        --phases gemini,codex            # default Codex pipeline

    .venv/bin/python scripts/dispatch_chapter_prose.py 6 \
        --slug ch-06-the-cybernetics-movement \
        --research-branch claude/394-ch06-research \
        --cap-words 5000 \
        --verdict-notes-pr 467 \
        --phases gemini,claude           # Claude-fallback pipeline

Phases default to "gemini,codex" (the post-2026-04-29 pipeline). Use
"gemini" alone to fire just the draft, "codex" or "claude" alone to
expand a pre-drafted file.
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


STRICT_SOURCE_RULE = """\
**Strict source rule.** Use only the provided contract and claim
matrix. If evidence is missing for a scene, leave the scene thin
rather than filling it. Do NOT:

- add sources or citations not in `sources.md`
- introduce new page anchors, DOIs, or URLs
- upgrade Yellow claims to Green tone
- invent examples, dialogue, institutional motives, or causal links
- expand beyond the approved Prose Capacity Plan

If you can't anchor a claim, weaken the claim — never invent a source.
"""


def gemini_prompt(*, slug: str, ch_num: int, cap_words: int,
                  contract: str, verdicts: str, prose_path: str) -> str:
    return dedent(f"""\
        # Task: First-draft prose for Chapter {ch_num} (`{slug}`) (#394)

        You have **workspace-write** in this worktree. Replace the
        existing short stub at `{prose_path}` with a fresh first-draft
        prose based on the anchored research contract below.

        ## Pipeline position (post-2026-04-29 prose pivot)

        You are the **first-draft writer** in a four-step pipeline:

        ```
        1. Approved contract        ← already done, embedded below
        2. Gemini first draft       ← THIS STEP, target ~3,000 words
        3. Codex expansion to cap   ← downstream, will tighten + lengthen
        4. Cross-family review      ← downstream
        ```

        Don't try to hit the final {cap_words}-word cap. Write a tight,
        evidence-backed ~3,000-word first draft that captures every
        scene from the contract; Codex will expand the technical and
        biographical layers from the same contract.

        ## Your whitelist (where you add value)

        - narrative flow and pacing
        - scene ordering
        - making dry source material readable
        - spotting where the chapter feels thin

        ## Your blacklist (the Issue #421 hallucination filter)

        {STRICT_SOURCE_RULE}

        ## Other hard rules

        1. **Cap: {cap_words} words HARD CEILING** for the final
           chapter. Your first draft should land at ~3,000 words —
           well under.
        2. **Use the Boundary Contract.** The brief defines what the
           chapter is NOT. Don't anticipate later chapters.
        3. **Yellow claims hedge; Red claims stay out.** Yellow needs
           hedge phrasing ("according to Hailperin", "is sometimes
           argued"). Red claims do not appear except as flagged open
           questions.
        4. **Frontmatter required.** First lines:
           ```
           ---
           title: "Chapter {ch_num}: <Title from brief>"
           description: "<one-sentence chapter hook>"
           sidebar:
             order: {ch_num}
           ---
           ```
        5. **No emoji.** No bullet-list "list of facts" sections —
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
        3. Self-check: word count ~3,000, every Green claim has a
           `sources.md`-traceable phrasing, Yellow claims hedged,
           Red claims absent, no fabricated anchors.
        4. `git add {prose_path}` and commit:
           ```
           docs(ch-{ch_num:02d}): draft prose against anchored contract (#394)
           ```
        5. Print word count and any claims you couldn't anchor.

        Do NOT push. The orchestrator handles PR creation after the
        expansion phase.
        """)


def _expansion_prompt(*, agent_label: str, slug: str, ch_num: int,
                      cap_words: int, contract: str, verdicts: str,
                      prose_path: str) -> str:
    """Build the expansion prompt. Identical for Codex and Claude —
    same strict-source rule, same Prose Capacity Plan discipline."""
    return dedent(f"""\
        # Task: Expand and tighten Chapter {ch_num} prose (`{slug}`) (#394)

        You ({agent_label}) have **workspace-write** in this worktree.
        Gemini drafted prose at `{prose_path}` against the anchored
        research contract. Your job is to expand the draft from ~3k to
        {cap_words} words while sharpening anchor discipline and
        tightening narrative coherence.

        ## Pipeline position (post-2026-04-29 prose pivot)

        You are the **expansion writer** in a four-step pipeline:

        ```
        1. Approved contract        ← already done, embedded below
        2. Gemini first draft       ← already on disk at the path above
        3. Expansion to cap         ← THIS STEP — you ({agent_label})
        4. Cross-family review      ← downstream (Claude source-fidelity, Gemini/Claude prose-quality)
        ```

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

        ## Strict source rule (the load-bearing rule)

        {STRICT_SOURCE_RULE}

        Concretely, **if a layer of the Prose Capacity Plan can't be
        expanded from the contract's existing anchors, leave it thin.**
        Cap-padding by inventing scenes is a worse failure than landing
        below cap.

        ## Other hard rules

        1. **Cap: {cap_words} words. Hard cap, not target.** If the
           verified evidence runs out, cap below.
        2. **Yellow → hedge; Red → out.** Same as the drafter's rules.
        3. **Preserve Gemini's good prose.** This is expansion, not
           rewrite. Surgical paragraph additions and targeted edits,
           not wholesale replacement. If a Gemini paragraph is good,
           leave it.
        4. **No emoji. No bullet-list facts.** Narrative prose only.

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
        5. Print final word count and the layers you expanded. Note
           any layer you left thin because evidence ran out.
        """)


def codex_prompt(*, slug: str, ch_num: int, cap_words: int,
                 contract: str, verdicts: str, prose_path: str) -> str:
    return _expansion_prompt(
        agent_label="Codex (gpt-5.5, default expander)",
        slug=slug, ch_num=ch_num, cap_words=cap_words,
        contract=contract, verdicts=verdicts, prose_path=prose_path,
    )


def claude_prompt(*, slug: str, ch_num: int, cap_words: int,
                  contract: str, verdicts: str, prose_path: str) -> str:
    return _expansion_prompt(
        agent_label="Claude opus-4-7 (fallback expander when Codex bandwidth exhausted)",
        slug=slug, ch_num=ch_num, cap_words=cap_words,
        contract=contract, verdicts=verdicts, prose_path=prose_path,
    )


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
    elif agent == "codex":
        # gpt-5.5 + model_reasoning_effort=high pinned in
        # ~/.codex/config.toml.
        model = "gpt-5.5"
        timeout = 3600
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
    p.add_argument("--phases", default="gemini,codex",
                   help="comma-separated: gemini,codex (default post-2026-04-29) "
                        "or gemini,claude (Claude-fallback) or any single phase")
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
        elif phase == "codex":
            prompt = codex_prompt(
                slug=args.slug, ch_num=args.ch_num,
                cap_words=args.cap_words, contract=contract,
                verdicts=verdicts, prose_path=prose_path,
            )
            log = Path(f"/tmp/prose-ch{args.ch_num:02d}-codex.log")
            ok = fire_phase(
                agent="codex", prompt=prompt, worktree=worktree,
                task_id=f"prose-{args.slug}-codex", log_path=log,
            )
            if not ok:
                print("[main] Codex expansion FAILED")
                return 3
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
                print("[main] Claude expansion FAILED")
                return 4
        else:
            print(f"[err] unknown phase: {phase}", file=sys.stderr)
            return 1

    print(f"[done] worktree={worktree} branch={branch}")
    print(f"[next] cd {worktree} && git push -u origin {branch} "
          f"&& gh pr create --title 'Prose: Chapter {args.ch_num} ({args.slug}) (#394)' --body ...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
