# Session handoff — 2026-04-30 (night-3) — Part 6 reader-aids (Ch32–Ch40) — 9 PRs open

> Picks up from `2026-04-30-part5-reader-aids-prs.md`. Part 5 PRs (#609–#616) are still open and unmerged at the start of this session. This session shipped **Part 6 reader-aids end-to-end (9 chapters / 9 PRs)** using the inline-sequential rollout with single-headless-Claude dispatch per chapter. **Zero worktree GC races** because the no-fan-out rule was respected.

## What shipped this session

| Ch | Branch | PR | Tier 1 | Tier 2 | Tier 3 landed |
|---|---|---|---|---|---|
| Ch32 The DARPA SUR Program | `claude/394-ch32-reader-aids` | [#618](https://github.com/kube-dojo/kube-dojo.github.io/pull/618) | TL;DR / 6 cast / 9 timeline / 7 glossary | — | 0 (3/3 SKIPs Codex-confirmed) |
| Ch33 Deep Blue | `claude/394-ch33-reader-aids` | [#619](https://github.com/kube-dojo/kube-dojo.github.io/pull/619) | TL;DR / cast / timeline / glossary | — | 1 pull-quote (Newborn 2003 p.151 — Codex REVIVE) |
| Ch34 The Accidental Corpus | `claude/394-ch34-reader-aids` | [#620](https://github.com/kube-dojo/kube-dojo.github.io/pull/620) | TL;DR / cast / timeline / glossary | — | 0 (3/3 SKIPs Codex-confirmed) |
| Ch35 Indexing the Mind | `claude/394-ch35-reader-aids` | [#621](https://github.com/kube-dojo/kube-dojo.github.io/pull/621) | TL;DR / cast / timeline / glossary | — | **2** — pull-quote (GFS 2003 p.1 — Codex CONFIRM PROPOSE) **+** plain-reading aside (Codex REVISE: 3-sentence version of the eigenvector explanation) |
| Ch36 The Multicore Wall | `claude/394-ch36-reader-aids` | [#622](https://github.com/kube-dojo/kube-dojo.github.io/pull/622) | TL;DR 80w / 6 cast / timeline / 7 glossary | — | 0 (3/3 SKIPs Codex-confirmed) |
| Ch37 Distributing the Compute | `claude/394-ch37-reader-aids` | [#623](https://github.com/kube-dojo/kube-dojo.github.io/pull/623) | TL;DR 77w / 6 cast / timeline / 7 glossary | — | 1 pull-quote (Dean & Ghemawat OSDI 2004 abstract — Codex REVIVE) |
| Ch38 The Human API | `claude/394-ch38-reader-aids` | [#624](https://github.com/kube-dojo/kube-dojo.github.io/pull/624) | TL;DR 80w / 6 cast / timeline / 6 glossary | — | 0 (Codex REVIVE → **orchestrator OVERRIDE → SKIP** on adj-rep + anchor grounds) |
| Ch39 The Vision Wall | `claude/394-ch39-reader-aids` | [#625](https://github.com/kube-dojo/kube-dojo.github.io/pull/625) | TL;DR 80w / 6 cast / timeline / 7 glossary | — | 1 pull-quote (Torralba & Efros CVPR 2011 p.1522 — Codex REVIVE) |
| Ch40 Data Becomes Infrastructure | `claude/394-ch40-reader-aids` | [#626](https://github.com/kube-dojo/kube-dojo.github.io/pull/626) | TL;DR 73w / 6 cast / timeline / 7 glossary | — | 1 pull-quote (Deng et al. CVPR 2009 p.248 abstract — Codex REVIVE) |

**Tier 3 landing rate: 6 of 27 candidates (~22%).** Compare to Part 5: 3 of 24 (~12.5%). Higher yield because the Part-5 lesson on citing Green primary sources (not "chapter prose") was baked into the dispatch prompts; reviewer kept catching cases where the author's adjacent-repetition test was over-strict against primary-source pools.

**No Tier 2 work this part.** Per `READER_AIDS.md`: next math chapter is Ch44, next architecture sketch is Ch41 — both in Part 7.

**Bit-identity verified across all 9 branches**: `git diff origin/main -- src/content/docs/ai-history/ch-XX-*.md | grep '^-[^-]'` empty in every case (verified before each commit AND after every applied Tier 3 element).

## What was decided

1. **Inline-sequential rollout works at 9-chapter scale.** Pattern: pre-create 9 worktrees in advance; for each chapter, dispatch ONE headless Claude (sonnet, no `isolation` flag, instructed to operate in the pre-created worktree path); orchestrator runs codex Tier 3 review on the branch; orchestrator applies any REVIVE/REVISE verdicts inline; orchestrator pushes + opens PR; move to next chapter. Wall-clock per chapter: ~8–12 min. Total session: ~90 min for 9 chapters. **Zero worktree GC races** because (a) Agent without `isolation=worktree` doesn't trigger the race, and (b) sequential dispatch means only one in-flight at a time.

2. **Codex REVIVE rate jumped to 5 of 9 chapters.** Codex correctly identified that several author proposals had limited their Tier 3 candidate search to chapter prose, missing valid Green-primary-source pulls. The pattern: author searches the chapter for quote-worthy lines, finds they're all paraphrased adjacent to where the pull-quote would land, SKIPs on adj-rep grounds. Codex then walks the `sources.md` Green-primary pool, finds a sentence that appears in the source but NOT in chapter prose, REVIVES with that sentence + a substantive annotation. Successful Codex revives this session: Ch33 (Newborn 2003), Ch37 (MapReduce abstract), Ch39 (Torralba & Efros), Ch40 (Deng et al.). Codex's REVIVE on Ch35 (GFS 2003) had been already PROPOSED by the author and was simply CONFIRMED.

3. **Orchestrator-level override on Codex (Ch38).** First override of the Part 5/6 rollout. Codex revived an AWS Mechanical Turk launch-announcement sentence as a pull-quote. Orchestrator overrode on two grounds: **(a)** chapter prose at line 71 paraphrases the same sentence with only cosmetic word changes ("Amazon framed this service as providing a web-services API for computers to integrate 'Artificial Artificial Intelligence' directly into their processing" vs. Codex candidate "Amazon Mechanical Turk does this, providing a web services API for computers to integrate Artificial Artificial Intelligence directly into their processing"); reading them back-to-back is reader-experience adjacent-repetition even if literal-verbatim repetition gate passes. **(b)** Codex's claimed verbatim wording does not match `sources.md` G9 row at line-level — unanchored wording should not promote Yellow → Green (cf. `feedback_gemini_hallucinates_anchors.md` precedent). Override documented in-tree at `docs/research/ai-history/chapters/ch-38-the-human-api/tier3-orchestrator-override.md` so the audit chain is reproducible. The bar applied: a Codex revive that fails BOTH (a) reader-experience adj-rep AND (b) line-level anchor verification justifies an override; either ground alone might not.

4. **Primary tree stayed clean throughout.** `git status -sb` on the orchestrator's primary tree returned `## main...origin/main` after every chapter — no stray commits, no GC race. Confirms that the sequential single-Agent dispatch (no `isolation=worktree`) plus `cd <worktree> && git ...` discipline holds up at scale.

5. **Codex direct invocation under `--dangerously-bypass-approvals-and-sandbox` was perfect.** 9 sequential codex reviews, all completed cleanly within the 600s timeout. Total codex token usage: ~600K across all 9 reviews (~66K avg per review). No 429s, no auth flaps. The `~/.codex/config.toml` route via `codex exec -m gpt-5.5 -c model_reasoning_effort="high"` is the canonical path.

## Pace data

- Cold start (briefing + handoff read + verify Part 5 PRs still open): ~5 min
- Pre-create 9 worktrees: ~30 sec
- Ch32 inline (orchestrator-direct, since prose was already in context): ~10 min
- Ch33–Ch40 each (headless Claude dispatch + codex review + apply verdicts + push + PR): ~9 min avg × 8 chapters = ~72 min
- Session handoff write: ~5 min
- **Total session: ~95 min for 9 chapters.** Comparable per-chapter rate to Part 4 fan-out (~7 min/ch) and Part 5 sequential (~6 min/ch), with **zero recovery overhead**.

## What's next

**Part 7 / Ch41–49 — the deep-learning revolution & GPU coup (2010s).** This part introduces the FIRST Tier 2 architecture-sketch chapters (Ch41 GPGPU, Ch42 CUDA, Ch49 unspecified per `READER_AIDS.md` §Tier 2 item 7) and the next Tier 2 math chapter (Ch44 Word2Vec / latent space).

**Tier 2 chapters in Part 7 per `READER_AIDS.md`:**
- Math sidebars: **Ch44** (Word2Vec / latent space)
- Architecture sketches: **Ch41** (Graphics Hack / GPGPU), **Ch42** (CUDA), **Ch49** (Distillation / Pruning per the Tier-2 list — verify chapter title before drafting)

**Tier 2 architecture-sketch form:** the form is "to be finalised in those chapters; not part of the Ch01 prototype" per `READER_AIDS.md`. **Lock the form in Ch41 before drafting Ch42 / Ch49 / Ch50 / Ch52 / Ch58.** Likely candidates: Mermaid `flowchart LR/TD` showing data path through GPU shader pipeline → general-purpose compute → kernel launch (for Ch41/Ch42); Mermaid `sequenceDiagram` for distributed training (for Ch49+).

**Recommended workflow for Part 7 — INLINE / SEQUENTIAL, same pattern as Part 6:**

```text
For each chapter Ch41 → Ch49 in sequence:
  1. Pre-create per-chapter worktree on origin/main
  2. Dispatch ONE headless Claude (sonnet, no isolation flag) with chapter-specific prompt
     - For Ch41: ask the agent to also propose the architecture-sketch form (Mermaid flowchart vs. block diagram). Lock the form in Ch41's PR description so Ch42/49+ can reuse it without re-litigation.
     - For Ch44: include the math-sidebar reminder (cf. Ch24/25/27/29 examples)
  3. Run codex Tier 3 review on the branch
  4. Apply REVIVE/REVISE verdicts inline; OVERRIDE selectively if a revive fails reader-experience adj-rep AND line-level anchor (Ch38 precedent)
  5. Push + PR
  6. Move to next chapter

No Agent(isolation="worktree") fan-out. The orchestrator stays single-threaded.
```

Estimated wall-clock: ~12 min/chapter for narrative-only chapters; ~18 min/chapter for Tier-2 chapters (Ch41/42/44/49). Part 7 = ~9 chapters × ~14 min avg = ~125 min. One full session.

## Cold-start smoketest (executable)

```bash
# 1. Confirm 9 PRs are open against main (#618-#626)
gh pr list --state open --limit 30 --json number,title,headRefName | \
  python3 -c "import json,sys;d=json.load(sys.stdin);[print(f\"#{p['number']:>3}  {p['headRefName']:<40}  {p['title']}\") for p in d if 'reader-aids' in p['headRefName'] and ('-ch3' in p['headRefName'] or '-ch4' in p['headRefName'])]"
# expect: 17 PRs across both Part 5 (8 PRs #609-#616) and Part 6 (9 PRs #618-#626)

# 2. Confirm Part 6 branches exist on origin
for ch in 32 33 34 35 36 37 38 39 40; do
  git ls-remote --heads origin "claude/394-ch${ch}-reader-aids" | wc -l
done
# expect: 9 lines, each = 1

# 3. Confirm tier3-review.md exists for each Part 6 chapter
for ch in 32 33 34 35 36 37 38 39 40; do
  git show "origin/claude/394-ch${ch}-reader-aids":docs/research/ai-history/chapters/ch-${ch}-*/tier3-review.md 2>/dev/null | head -1
done

# 4. Primary tree clean, main matches origin/main
git status -sb && git rev-parse --abbrev-ref HEAD
# expect: ## main...origin/main + main
```

Expected: 17 reader-aid PRs (8 Part 5 + 9 Part 6), 9 Part 6 branches on origin, 9 tier3-review.md files, primary tree clean.

## Cross-thread updates (for STATUS.md)

- **DROP**:
  - "Part 5 (Ch24–Ch31) PR-complete (2026-04-30 night-2)" — keep but qualify: still PR-complete, not yet merged.
  - "Part 6 (Ch32–Ch37) is next" — replace with "Part 6 (Ch32–Ch40) PR-complete (2026-04-30 night-3); Part 7 (Ch41–Ch49) is next, introduces Tier 2 architecture-sketch form".

- **ADD**:
  - **Part 6 reader-aids (Ch32–Ch40) PR-complete (2026-04-30 night-3).** 9 PRs open: #618 (Ch32), #619 (Ch33), #620 (Ch34), #621 (Ch35), #622 (Ch36), #623 (Ch37), #624 (Ch38), #625 (Ch39), #626 (Ch40). Tier 3 yield = 6 of 27 candidates (~22%) — higher than Part 5 (~12.5%) thanks to dispatch-prompt update on Green-primary-source citation. Codex REVIVE rate = 5 of 9 chapters; orchestrator override on Ch38 (#624) on adj-rep + anchor grounds.
  - **Inline-sequential single-Agent-dispatch pattern validated at 9-chapter scale.** Zero worktree GC races. Per-chapter wall-clock ~9 min. Pattern documented in this handoff for re-use on Parts 7+.
  - **Orchestrator override precedent established (Ch38).** Bar: a Codex revive that fails BOTH (a) reader-experience adj-rep AND (b) line-level anchor verification justifies override; either ground alone might not. Override documented in-tree at `tier3-orchestrator-override.md`.

## Blockers

- (none) — all 9 PRs are mergeable.

## Files modified this session

```
src/content/docs/ai-history/ch-32-the-darpa-sur-program.md
src/content/docs/ai-history/ch-33-deep-blue.md
src/content/docs/ai-history/ch-34-the-accidental-corpus.md
src/content/docs/ai-history/ch-35-indexing-the-mind.md
src/content/docs/ai-history/ch-36-the-multicore-wall.md
src/content/docs/ai-history/ch-37-distributing-the-compute.md
src/content/docs/ai-history/ch-38-the-human-api.md
src/content/docs/ai-history/ch-39-the-vision-wall.md
src/content/docs/ai-history/ch-40-data-becomes-infrastructure.md

docs/research/ai-history/chapters/ch-{32..40}-*/tier3-{proposal,review}.md   (18 files, all new)
docs/research/ai-history/chapters/ch-38-the-human-api/tier3-orchestrator-override.md  (1 file, new — first override doc)
```

All on feature branches; primary `main` is unchanged.

## Memory updates

- (none new this session) — the existing memory pointers (`feedback_no_parallel_agent_fanout.md`, `feedback_dispatch_to_headless_claude.md`, `reference_agent_worktree_recovery.md`, `feedback_codex_danger_for_git_gh.md`) all held up unchanged through the 9-chapter rollout. Consider adding `feedback_orchestrator_override_codex_tier3.md` after a second instance to confirm the precedent.

## Worktrees still in flight

9 per-branch worktrees at `.worktrees/claude-394-chXX-aids` for Ch32–Ch40. After PRs merge, run `git worktree remove .worktrees/claude-394-chXX-aids` × 9. The Part 5 worktrees (.worktrees/claude-394-ch{24..31}-aids) also remain — clear those first when their PRs merge.

```
.worktrees/claude-394-ch32-aids   [claude/394-ch32-reader-aids]
.worktrees/claude-394-ch33-aids   [claude/394-ch33-reader-aids]
.worktrees/claude-394-ch34-aids   [claude/394-ch34-reader-aids]
.worktrees/claude-394-ch35-aids   [claude/394-ch35-reader-aids]
.worktrees/claude-394-ch36-aids   [claude/394-ch36-reader-aids]
.worktrees/claude-394-ch37-aids   [claude/394-ch37-reader-aids]
.worktrees/claude-394-ch38-aids   [claude/394-ch38-reader-aids]
.worktrees/claude-394-ch39-aids   [claude/394-ch39-reader-aids]
.worktrees/claude-394-ch40-aids   [claude/394-ch40-reader-aids]
```
