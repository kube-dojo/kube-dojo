# Session handoff — 2026-04-30 (night-4) — Part 7 reader-aids RELEASED + 26-PR merge sweep + lifecycle bookkeeping

> Picks up from `2026-04-30-part6-reader-aids-prs.md`. This session shipped **Part 7 reader-aids (Ch41–Ch49) end-to-end (9 PRs)** AND merged the entire backlog of 26 open reader-aid PRs (Parts 5/6/7) in one sweep, AND addressed Codex's bookkeeping note by adding `prose_state` + `reader_aids` lifecycle fields to all 72 chapter `status.yaml` files. **Parts 1–7 are now fully RELEASED on main (49 of 72 chapters).** Architecture-sketch form is locked: `flowchart LR` for sequential dataflow, `flowchart TD` only when topology is genuinely hierarchical.

## What shipped this session

### Part 7 reader-aids — Ch41–Ch49

| Ch | Form | PR | Tier 1 | Tier 2 | Tier 3 landed |
|---|---|---|---|---|---|
| Ch41 The Graphics Hack | flowchart LR (form-lock) | [#627](https://github.com/kube-dojo/kube-dojo.github.io/pull/627) | TL;DR / 5 cast / 4 timeline / 6 glossary | architecture sketch (6 nodes, GPGPU pipeline) | 1 — pull-quote (Oh & Jung 2004 p.1312, Codex REVISE on verbatim) |
| Ch42 CUDA | flowchart TD (deviation) | [#628](https://github.com/kube-dojo/kube-dojo.github.io/pull/628) | TL;DR / 6 cast / 8 timeline / 5 glossary | architecture sketch (7 nodes, CUDA hierarchy) | 0 (Codex REJECT both — Buck quote adj-rep, memory aside cap+adj-rep) |
| Ch43 ImageNet Smash | — | [#629](https://github.com/kube-dojo/kube-dojo.github.io/pull/629) | TL;DR / 6 cast / 10 timeline / 6 glossary | — | 1 — pull-quote (Russakovsky et al. 2015 p.32 lines 1921-1930, Codex REVIVE) |
| Ch44 The Latent Space | — | [#630](https://github.com/kube-dojo/kube-dojo.github.io/pull/630) | TL;DR / 6 cast / 7 timeline / 7 glossary | math sidebar (6 equations: skip-gram, neg-sample, subsampling, V^n bottleneck, O=ETQ, vector-offset) | 0 (Codex REJECT both — math sidebar carries the load) |
| Ch45 Generative Adversarial Networks | — | [#631](https://github.com/kube-dojo/kube-dojo.github.io/pull/631) | TL;DR / 6 cast / 7 timeline / 7 glossary | — | 1 — plain-reading aside (Codex REVISE: 4-sentence → 3-sentence on minimax direction reversal) |
| Ch46 The Recurrent Bottleneck | — | [#632](https://github.com/kube-dojo/kube-dojo.github.io/pull/632) | TL;DR / 6 cast / 8 timeline / 7 glossary | — | 0 (Codex REJECT both) |
| Ch47 The Depths of Vision | — | [#633](https://github.com/kube-dojo/kube-dojo.github.io/pull/633) | TL;DR / 6 cast / 7 timeline / 7 glossary | — | 1 — pull-quote (Krizhevsky et al. 2012 p.1 lines 74-77, Codex REVIVE: AlexNet's own forward bet on scale) |
| Ch48 AlphaGo | — | [#634](https://github.com/kube-dojo/kube-dojo.github.io/pull/634) | TL;DR / 6 cast / 4 timeline / 7 glossary | — | 0 (Codex APPROVE both skips) |
| Ch49 The Custom Silicon | flowchart LR (LR-reuse) | [#635](https://github.com/kube-dojo/kube-dojo.github.io/pull/635) | TL;DR / 6 cast / 9 timeline / 7 glossary | architecture sketch (8 nodes, TPU systolic array) | 0 (Codex APPROVE both skips) |

**Tier 3 yield: 4 of 18 (~22%)** — comparable to Part 6 (~22%), better than Part 5 (~12.5%). Codex revived 3 author-skips (Ch43 Russakovsky, Ch47 AlexNet, plus revising Ch41 Oh/Jung from paraphrase to verbatim). Codex revised 1 author-proposal (Ch45 sentence-cap + adj-rep). Codex rejected 1 form choice (Ch42 LR→TD).

### 26-PR merge sweep

All open reader-aid PRs merged:
- **Part 5 (Ch24–Ch31): 8 PRs #609–#616 merged** (had been open since 2026-04-30 night-2)
- **Part 6 (Ch32–Ch40): 9 PRs #618–#626 merged** (had been open since 2026-04-30 night-3)
- **Part 7 (Ch41–Ch49): 9 PRs #627–#635 merged** (this session)

Merge mechanics: `gh pr merge <num> --squash --delete-branch -R kube-dojo/kube-dojo.github.io` in a sequential bash loop. All 26 squash-merges succeeded on first try. Branch protection on main has `required_approving_review_count: 0` so admin merge worked end-to-end without per-PR approval (the Codex Tier 3 review embedded in `tier3-review.md` files in-tree IS the cross-family review for these PRs; the formal GitHub-review channel was not used). No merge conflicts despite Parts 5/6/7-pre-bookkeeping branches being branched from old main — feature branches don't touch other chapters' `status.yaml`, so 3-way merge picks up the lifecycle fields cleanly.

**Why the user-prompted merge sweep was the right call:** the per-Part PR-complete pattern (validated in Part 4) had only been through one squash flow before, so accumulating 24 PRs across 3 Parts was reasonable. But at 24, it became debt: future merges would have to reconcile against an ever-evolving main, and Part 9's autonomous Codex chain was advancing in parallel. One sweep, one bookkeeping commit, done.

### Codex bookkeeping fix — `prose_state` + `reader_aids` lifecycle fields

User forwarded Codex's review note 2026-04-30 mid-session: "the metadata is lagging the reality. Several status.yaml files in Parts 1-3 still say `capacity_plan_anchored` or `prose_ready` even though the prose and reader aids now exist." Codex offered two paths: (1) update existing `status` field, or (2) add a separate `reader_aids` status field so chapter research/prose status is not overloaded.

Took path 2. Added two new top-level YAML fields to all 72 chapter `status.yaml` files in commit `ab801bf7`:

- `prose_state`: `research_only | published_on_main` — initial value `published_on_main` for all 72 (Codex's autonomous Part 9 chain has shipped through Ch72 already; the old TODO line saying "Ch66-72 remain" was stale).
- `reader_aids`: `none | pr_open | landed` — flipped to `landed` for Ch01–Ch49 after this session's merges; `none` for Ch50–Ch72 (Parts 8–9 not yet started).
- `lifecycle_updated`: stamp date.

Existing `status` field is untouched, keeping its research-phase semantics. Lifecycle backfill generator: `/tmp/add_lifecycle_fields.py` (idempotent — re-runs do nothing if `reader_aids` field already present). Post-merge sweep generator: `/tmp/flip_to_landed.py`.

## What was decided

1. **Form-lock data point: keep Ch41's `flowchart LR` as the default; deviate to `flowchart TD` only when topology is genuinely hierarchical.** Ch42 (CUDA grid → block → thread) is the only Part 7 chapter that genuinely needed TD; Codex flagged it explicitly. Ch49 (TPU systolic array) tested as a borderline case but resolved to LR — its dataflow is genuinely linear (activations enter left, weights stream from FIFO, partial sums flow rightward through MAC cells). For Ch50/Ch52/Ch58, default to LR and only deviate with explicit justification.

2. **Per-PR status.yaml lifecycle bumps WITH the reader-aid commit.** Ch43–Ch49 worktrees were rebased onto current main BEFORE the agent dispatch so each agent could flip its own chapter's `reader_aids` from `none` → `landed` (or `pr_open`) as part of its commit. This keeps the post-merge state correct without a separate bookkeeping pass per chapter. Ch41/Ch42 worktrees were branched pre-bookkeeping; their lifecycle flips were handled in the bulk post-merge sweep (`/tmp/flip_to_landed.py`). For Parts 8/9, follow the Ch43+ pattern: rebase before dispatch.

3. **Codex's revive criterion holds.** Codex revived 3 of 9 author skips this Part. Pattern: author searches chapter for quote-worthy lines, finds adj-rep with prose paraphrases, SKIPs. Codex then walks the `sources.md` Green-primary pool, finds a Green sentence that does NEW work (e.g., a different framing than chapter prose), REVIVES with verbatim + page anchor + 1-sentence annotation that does new work. Ch47 AlexNet revive is the cleanest example: chapter is about ResNet/depth, but Codex found AlexNet's own forward bet on scale ("waiting for faster GPUs and bigger datasets") that Ch47 sets up but does not quote, framing it as the bet ResNet would later complicate.

4. **One-sentence verbatim verification on revives.** Ch43 had a near-miss: Codex revived a Russakovsky pull-quote citing lines 1921-1930 but its review only quoted a fragment ("would never have been possible on a smaller scale"). One follow-up dispatch to codex extracted the complete sentence (47 words, p.32: "On the plus side, of course, the major breakthroughs in object recognition accuracy (Section 5) and the analysis of the strength and weaknesses of current algorithms as a function of object class properties (Section 6.3) would never have been possible on a smaller scale."). The follow-up was needed because READER_AIDS.md spec requires a complete sentence in `>` blockquote, not a fragment. **Lesson: codex review prompts should explicitly require the COMPLETE verbatim sentence on revives, not a paraphrase or clause fragment.**

5. **Branch protection allows admin-merge with 0 required reviews.** All 26 squash-merges went through `gh pr merge --squash --delete-branch` without per-PR approval. The Codex Tier 3 review embedded in `tier3-review.md` IS the cross-family review of substance; bit-identity verification + in-tree review docs are the audit chain.

## Pace data

- Cold start (briefing + handoff read + verify Part 5/6 PRs still open): ~5 min
- Pre-create 7 Part 7 worktrees (Ch41–Ch49 minus already-existing): ~30 sec
- Ch41 (form-lock chapter): ~25 min including form-lock decision and follow-up
- Ch42 (form deviation): ~20 min
- Ch43 (Codex revive + follow-up for full sentence): ~25 min
- Ch44 (math sidebar): ~15 min
- Ch45 (revise on plain-reading aside): ~15 min
- Ch46–Ch48: ~10 min each
- Ch49 (form choice + dispatch): ~12 min
- Codex bookkeeping migration (script + commit): ~15 min
- 26-PR merge sweep: ~3 min
- Post-merge lifecycle flip + commit: ~5 min
- Handoff write: ~10 min
- **Total session: ~3 hr.** 9 chapters shipped + 26 PRs merged + bookkeeping migration.

## What's next

**Parts 8 & 9 — Ch50–Ch72 (23 chapters).** Codex's autonomous Part 9 chain has already shipped all the prose (verified by `wc -w` showing 4–5k words on every chapter). Reader-aids are all that remain.

**Tier 2 chapters in Parts 8–9 per `READER_AIDS.md`:**
- Math sidebars: **Ch50** (?), **Ch55**, **Ch58** ("the math of noise" — diffusion)
- Architecture sketches: **Ch50**, **Ch52**, **Ch58**

So Ch50 carries BOTH a math sidebar AND an architecture sketch. Ch55 is math-only. Ch58 carries BOTH. Ch52 is architecture-only. The other ~18 chapters are Tier-1-only.

**Recommended workflow for Parts 8–9 — INLINE / SEQUENTIAL:**

```text
For each chapter Ch50 → Ch72 in sequence:
  1. Pre-create per-chapter worktree on origin/main (post-bookkeeping; lifecycle field present)
  2. Dispatch ONE headless Claude (sonnet) per chapter
     - For Ch50/Ch58 dual-Tier-2: ask for both math AND architecture sketch
     - For Ch52: architecture sketch only — default flowchart LR; deviate only with justification
     - For Ch55: math sidebar
     - For others: Tier 1 + Why-still + Tier 3 author-propose
     - Always flip status.yaml `reader_aids: none → landed` in the same commit
  3. Run codex Tier 3 review
  4. Apply REVIVE/REVISE verdicts (or orchestrator-override if revive fails BOTH adj-rep AND anchor verification)
  5. Push + PR + immediate squash-merge (don't accumulate 23 PRs)
  6. Move to next chapter

No Agent(isolation="worktree") fan-out. Sequential single-agent dispatch only.
```

**Alternative scope-cut: ship Tier 1 only for the 23 remaining chapters in one sweep, then layer Tier 2/3 in a second pass.** This would close out the basic-coverage layer faster and let Tier 2/Tier 3 polish be a separate, more careful sweep. Worth considering if total session time is tight.

Estimated wall-clock: 23 chapters × ~10 min/chapter for narrative + ~15 min for Tier 2 chapters = ~4 hours. Two sessions or one long session. Per the merge-as-you-go discipline reset this session, **squash-merge each PR immediately after Codex review**, do not let the queue accumulate.

## Cold-start smoketest (executable)

```bash
# 1. Confirm Parts 1-7 fully on main (49 chapters with reader-aids)
git -C /Users/krisztiankoos/projects/kubedojo log --oneline | grep -E "docs\(ch[0-4][0-9]\): Tier" | wc -l
# expect: 49 (one commit per chapter; squashed PRs)

# 2. Confirm zero open reader-aid PRs
gh pr list -R kube-dojo/kube-dojo.github.io --state open --json headRefName --limit 50 | python3 -c "
import json, sys
print(sum(1 for p in json.load(sys.stdin) if 'reader-aids' in p['headRefName']))"
# expect: 0

# 3. Confirm lifecycle fields on all 72 chapter status.yaml
grep -l "^reader_aids:" docs/research/ai-history/chapters/ch-*/status.yaml | wc -l
# expect: 72

# 4. Confirm Ch01-49 marked landed; Ch50-72 marked none
for n in $(seq 1 72); do
  printf "ch%02d: " "$n"
  grep -h "^reader_aids:" docs/research/ai-history/chapters/ch-${n}-*/status.yaml | head -1
done | head -80
# expect: 01-49 → landed; 50-72 → none

# 5. Primary tree clean, main = origin/main
git -C /Users/krisztiankoos/projects/kubedojo status -sb
# expect: ## main...origin/main (no dirty)
```

## Cross-thread updates (for STATUS.md)

- **DROP / REPLACE**:
  - "Part 5 (Ch24-Ch31) PR-complete" — ALL MERGED in this session.
  - "Part 6 (Ch32-Ch40) PR-complete" — ALL MERGED in this session.
  - "Part 7 (Ch41-Ch49) is next" — DONE; ALL MERGED.
  - "AI history #394: Part 9 (Ch66-72, 7 chapters remain)" — STALE; Codex's chain shipped through Ch72 already (verified by file existence and word counts ≥4k).

- **ADD**:
  - **Parts 1–7 RELEASED on main (Ch01–Ch49) — 49 chapters with full reader-aids.** All 26 PRs merged this session.
  - **Architecture-sketch form-lock: `flowchart LR` (Ch41 + Ch49); deviates to `flowchart TD` for genuinely hierarchical topologies (Ch42 CUDA only).** Ch50/52/58 should default to LR with deviation only on explicit justification.
  - **Lifecycle fields added to all 72 chapter status.yaml** (`prose_state` + `reader_aids` + `lifecycle_updated`). Existing `status` field untouched (keeps research-phase semantics). Per-chapter agents now flip `reader_aids` directly in the reader-aid commit; bulk post-merge sweep handles pre-bookkeeping branches.
  - **Merge-as-you-go discipline reset.** Per-Part accumulation (8 PRs in Part 5, 9 in Part 6, 7 in Part 7-partial) became debt. For Parts 8/9, squash-merge each PR immediately after Codex review.
  - **"Verbatim COMPLETE sentence" rule for codex revives.** When codex revives an Element 9 pull-quote, the review must include the complete sentence in `>`-blockquote form, not a fragment. Add to the codex review prompt template.

## Memory updates suggested

- Consider new memory `feedback_codex_revive_fragment_problem.md`: when codex revives a pull-quote, prompt MUST require complete verbatim sentence, not fragment. Ch43 hit this; needed follow-up dispatch.
- Consider new memory `feedback_form_lock_evolution.md`: architecture-sketch form-lock is `flowchart LR` for sequential dataflow, `flowchart TD` only for genuinely hierarchical topologies. Two data points (Ch41 LR-lock, Ch42 TD-deviation, Ch49 LR-reuse) confirm.
- Consider new memory `feedback_merge_as_you_go.md`: per-Part PR accumulation creates debt; squash-merge each reader-aid PR immediately after codex Tier 3 review.

## Worktrees still in flight

The 26 merged feature branches' worktrees are still on disk under `.worktrees/claude-394-ch{24..49}-aids/`. They should be cleaned up at session end:

```bash
for ch in 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49; do
  git -C /Users/krisztiankoos/projects/kubedojo worktree remove ".worktrees/claude-394-ch${ch}-aids" 2>/dev/null
done
git -C /Users/krisztiankoos/projects/kubedojo worktree prune
```

Defer cleanup to next session if not blocking.

## Files modified this session

```
# Reader-aid additions (per-chapter, one PR each):
src/content/docs/ai-history/ch-{41..49}-*.md   (9 files)
docs/research/ai-history/chapters/ch-{41..49}-*/tier3-{proposal,review}.md  (18 files, all new)

# Lifecycle field migration (single commit on main):
docs/research/ai-history/chapters/ch-{01..72}-*/status.yaml  (72 files, +6 lines each)

# Post-merge bookkeeping (single commit on main):
docs/research/ai-history/chapters/ch-{24..47}-*/status.yaml  (22 files, pr_open → landed)
docs/research/ai-history/chapters/ch-49-the-custom-silicon/status.yaml  (1 file, pr_open → landed)
```

All on main (no open PRs at session end).

## Blockers

(none)
