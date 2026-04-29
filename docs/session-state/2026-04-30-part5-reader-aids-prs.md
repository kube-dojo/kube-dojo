# Session handoff — 2026-04-30 (night-2) — Part 5 reader-aids (Ch24–Ch31) — 8 PRs open

> Picks up from `2026-04-30-part4-reader-aids-prs.md`. Part 4 was merged on main as `5c4562f5` before this session began. This session shipped Part 5 reader-aids end-to-end despite a serious worktree GC race that required mid-session recovery. **Pattern lesson locked in: do not fan out chapter batches via parallel `Agent(isolation="worktree")`.**

## What shipped this session

| Ch | Branch | PR | Tier 1 | Tier 2 | Tier 3 landed |
|---|---|---|---|---|---|
| Ch24 The Math That Waited for the Machine | `claude/394-ch24-reader-aids` | [#609](https://github.com/kube-dojo/kube-dojo.github.io/pull/609) | TL;DR / 6 cast / 7 timeline / 7 glossary | 6-equation math sidebar (chain rule, reverse-mode AD, generalized delta rule, hidden-unit error signal, logistic + derivative, $O(n)$ memory) | 1 plain-reading aside (REVISED by Codex — hidden-unit error signal) |
| Ch25 The Universal Approximation Theorem (1989) | `claude/394-ch25-reader-aids` | [#610](https://github.com/kube-dojo/kube-dojo.github.io/pull/610) | TL;DR / 6 cast / 7 timeline / 7 glossary | math sidebar (Cybenko Thm 1+2, HSW $L^p$, Funahashi, Barron rate, three logical separations) | 1 plain-reading aside (REVISED by Codex — universal approximation guardrails) |
| Ch26 Bayesian Networks | `claude/394-ch26-reader-aids` | [#611](https://github.com/kube-dojo/kube-dojo.github.io/pull/611) | TL;DR / 5 cast / 6 timeline / 6 glossary | — | 0 (1 proposed → REJECTED) |
| Ch27 The Convolutional Breakthrough | `claude/394-ch27-reader-aids` | [#612](https://github.com/kube-dojo/kube-dojo.github.io/pull/612) | TL;DR / 6 cast / 5 timeline / 6 glossary | math sidebar (convolution, weight-sharing parameter count, pooling, gradient flow, translation tolerance, LeNet-5 $10^8$ multiplications) | 1 plain-reading aside (REVISED by Codex — expressiveness vs. learnability) |
| Ch28 The Second AI Winter | `claude/394-ch28-reader-aids` | [#613](https://github.com/kube-dojo/kube-dojo.github.io/pull/613) | TL;DR / 6 cast / 9 timeline / 7 glossary | — | 0 (2 proposed → 2 REJECTED) |
| Ch29 Support Vector Machines | `claude/394-ch29-reader-aids` | [#614](https://github.com/kube-dojo/kube-dojo.github.io/pull/614) | TL;DR / 6 cast / 6 timeline / 6 glossary | math sidebar (margin objective, support vectors, dual / KKT, kernel trick / Mercer, soft-margin slack, structural risk minimisation) | 0 (2 proposed → 2 REJECTED) |
| Ch30 The Statistical Underground | `claude/394-ch30-reader-aids` | [#615](https://github.com/kube-dojo/kube-dojo.github.io/pull/615) | TL;DR / 6 cast / 6+ timeline / 6 glossary | — | 0 (1 proposed → REJECTED) |
| Ch31 Reinforcement Learning Roots | `claude/394-ch31-reader-aids` | [#616](https://github.com/kube-dojo/kube-dojo.github.io/pull/616) | TL;DR / 6 cast / 8 timeline / 7 glossary | — | 0 (1 proposed → REJECTED) |

**Tier 3 landing rate: 3 of 12 candidates (~25%).** Lower than Part 4 (~85%) — see "What was decided" §4 below for why.

**Bit-identity verified across all 8 branches**: `git diff main -- src/content/docs/ai-history/ch-XX-*.md | grep '^-[^-]'` empty in every case.

## What was decided

1. **Worktree GC race hit 5 of 8 agents — fan-out retired.** The `Agent(subagent_type="general-purpose", model="sonnet", isolation="worktree")` parallel dispatch worked end-to-end on Part 4 (1 of 7 agents missed). On Part 5, **5 of 8 agents** committed to primary `main` instead of their isolated worktree branches, despite each agent being instructed to `touch .worktree-sentinel` as the very first action. The sentinel-file mitigation **does not prevent the race**. User instruction post-incident: "do not fan out next time. dont break these but next time dont fan out." Memory `feedback_no_parallel_agent_fanout.md` written; rule is **inline / sequential for chapter batches, full stop**. The headless-Claude delegation rule (`feedback_dispatch_to_headless_claude.md`) remains scoped to single heavy tasks, not parallel batches.

2. **Codex parallel `codex exec` still works.** The Tier 3 review batch ran sequentially this session (per the no-fan-out rule, applied broadly to be safe), but parallel `codex exec` on Part 4 was cleanly successful. The bug is specific to `Agent(isolation="worktree")`, not all parallelism. Future codex-only batches can still parallelize if needed.

3. **Recovery procedure validated.** `reference_agent_worktree_recovery.md` documents the cherry-pick + reset pattern. Steps:
   - Save safety branch at current main HEAD.
   - For each stray commit on main: `git checkout -B claude/394-chXX-reader-aids <CLEAN_BASE> && git cherry-pick <stray-sha>`. Each cherry-pick produces a single-commit branch (the chapters are independent file-wise, so no conflicts).
   - `git update-ref refs/heads/main <CLEAN_BASE>` (avoids switching HEAD).
   - `git reset --hard main` to clean primary working tree (cherry-pick chain pollutes the index).
   - For agents that DID succeed in their worktrees, `git branch claude/394-chXX-reader-aids <agent-sha>` to alias their commits onto canonical names.
   - Bit-identity verify all 8 branches.
   - `git worktree remove --force` + `git branch -D` for stale records and branches.
   - Total recovery time: ~10 min.

4. **Tier 3 pull-quote landing rate dropped to 0 of 8** because the headless-Claude proposals all cited "Chapter XX prose" as the source attribution rather than a Green primary source (the actual papers, books, archives). Codex correctly refused every pull-quote on adjacent-repetition + non-Green-source grounds. **Procedural lesson for future chapters: the Tier 1 dispatch prompt must instruct the agent to cite a Green primary source for Tier 3 pull-quotes, not the chapter prose.** Codex did approve REVISED versions of 3 plain-reading asides where the target paragraph was symbolically dense and the agent's commentary did new work — those landed on Ch24/Ch25/Ch27.

5. **Sequential codex Tier 3 batch ran in ~16 min wall-clock** (vs. ~5 min for parallel on Part 4). Acceptable trade-off for reliability under the no-fan-out rule. Each chapter took ~1.5–2.5 min including PDF fetches for source-verbatim verification (Codex curl'd Samuel 1959, Bahl/Jelinek/Mercer 1983, Cortes/Vapnik 1995, Burges 1998, LeCun 1990 PDFs and grep'd them).

## Pace data

- Cold start (briefing + handoff read + verify Part 4 merged): ~3 min
- Headless Claude Tier 1 batch (8 in parallel, sonnet, isolation=worktree): ~10 min wall-clock — **but 5 of 8 agents missed their worktrees**, leaving 5 stray commits on primary main
- Recovery (cherry-pick + reset + branch aliasing + bit-identity verify + worktree cleanup): ~10 min
- Codex Tier 3 batch (8 sequential via direct `codex exec`, gpt-5.5, danger-full-access): ~16 min wall-clock
- Verdict-application (3 chapters got REVISED asides, 5 got 0 elements): ~5 min
- Commit + push + PR creation × 8: ~5 min
- **Total session: ~50 min for 8 chapters.** Same wall-clock as Part 4, but with significantly more recovery overhead. Sequential-only would have saved the 10 min of recovery for ~+15 min of slower dispatch.

## What's next

**Part 6 / Ch32–37 — the 1990s deep-learning revival, statistical ascent, dotcom-era infrastructure.** Full chapter list to be confirmed by reading roadmap + actual ch-32-*.md to ch-37-*.md filenames (the canonical roadmap document differed from actual filenames on Ch24–Ch31, so verify before drafting).

**Tier 2 math chapters in Part 6 per READER_AIDS.md §Tier 2 list:** Ch44 is the next math chapter; nothing in Ch32–43 needs Tier 2.

**Tier 2 architecture-sketch chapters from Part 6:** Ch41, Ch42 (per READER_AIDS.md §Tier 2 item 7).

**Recommended workflow for Part 6 — INLINE, NOT FAN-OUT:**

```text
For each chapter in sequence:
  1. Read READER_AIDS.md, Ch01 prototype, Ch17 (closest pure-Tier-1 example), prior Part 5 chapters
  2. Read the chapter's prose + brief.md + people.md + timeline.md + sources.md
  3. Insert Tier 1 (TL;DR + Cast + Timeline + Glossary) after frontmatter
  4. Insert "Why this still matters today" :::note before bibliography
  5. [Tier 2 chapters only] Insert "The math, on demand" sidebar
  6. Write tier3-proposal.md — IMPORTANT: cite a Green primary source for the pull-quote, not "chapter prose"
  7. Bit-identity check: git diff main -- <chapter> | grep '^-[^-]' must be empty
  8. Skip npm run build; rely on CI post-merge
  9. Commit (do not push yet)
  10. Run codex Tier 3 review on the branch
  11. Apply REVISE / APPROVE verdicts; SKIP REJECTED
  12. Commit + push + PR

No Agent(isolation="worktree") fan-out. The orchestrator does the work directly.
```

Per-chapter wall-clock should be ~10–15 min if done inline; full Part 6 = 6 chapters × 12 min = ~75 min. Comparable to a fan-out-and-recover session, with no recovery risk.

## Cold-start smoketest (executable)

```bash
# 1. Confirm 8 PRs are open against main (#609–#616)
gh pr list --state open --search "ch2[4-9] OR ch3[01] in:title" --limit 10

# 2. Confirm branches exist on origin
for ch in 24 25 26 27 28 29 30 31; do
  git ls-remote --heads origin "claude/394-ch${ch}-reader-aids" | wc -l
done
# expect: 8 lines, each = 1

# 3. Confirm tier3-review.md exists for each chapter on its branch
for ch in 24 25 26 27 28 29 30 31; do
  git show "origin/claude/394-ch${ch}-reader-aids":docs/research/ai-history/chapters/ch-${ch}-*/tier3-review.md 2>/dev/null | head -1
done

# 4. Primary tree clean, main at 5cab4276
git status -sb && git rev-parse main
# expect: ## main...origin/main + 5cab4276...
```

Expected: 8 PRs visible, 8 branches on origin, 8 tier3-review.md files, primary main at `5cab4276` (Codex Part 9 PR #607).

## Cross-thread updates (for STATUS.md)

- **DROP**:
  - Old "Parts 1, 2, 3, 4 RELEASED on main (2026-04-30)" — promote to "Parts 1–4 RELEASED; Part 5 PR-complete (#609–#616)".
  - "Parallel `codex exec` dispatch confirmed working" — keep but qualify: Tier 3 ran sequentially this session under the no-fan-out rule.
  - "Headless Claude `isolation=worktree` race" — replace with stronger rule: **the Agent worktree fan-out is retired**; sentinel-file mitigation does not work.

- **ADD**:
  - **Part 5 reader-aids (Ch24–Ch31) PR-complete (2026-04-30 night-2).** 8 PRs open: #609 (Ch24), #610 (Ch25), #611 (Ch26), #612 (Ch27), #613 (Ch28), #614 (Ch29), #615 (Ch30), #616 (Ch31). 4 chapters carry Tier 2 math sidebars (Ch24/25/27/29 per canonical READER_AIDS list); 3 chapters land 1 Tier 3 plain-reading aside each (Ch24/25/27, REVISED by Codex). 0 pull-quotes landed across all 8 — author proposals all cited chapter prose instead of Green primary sources, so Codex correctly rejected every one.
  - **Worktree GC race retires Agent fan-out for chapter batches.** 5 of 8 agents missed their worktrees on Part 5 (vs. 1 of 7 on Part 4) despite sentinel-file mitigation. Memory `feedback_no_parallel_agent_fanout.md` and `reference_agent_worktree_recovery.md` saved. Future chapter batches must be inline / sequential.
  - **Tier 3 pull-quote source-attribution lesson:** the Tier 1 dispatch prompt must instruct the author to cite a Green primary source for the pull-quote, not "chapter prose." This caused 0/8 pull-quotes to land in this batch.

## Blockers

- (none) — all 8 PRs are mergeable.

## Files modified this session

```
src/content/docs/ai-history/ch-24-the-math-that-waited-for-the-machine.md       (+53 lines, Tier 1 + Tier 2 + 1 Tier 3)
src/content/docs/ai-history/ch-25-the-universal-approximation-theorem-1989.md   (+54 lines, Tier 1 + Tier 2 + 1 Tier 3)
src/content/docs/ai-history/ch-26-bayesian-networks.md                          (+38 lines, Tier 1 only)
src/content/docs/ai-history/ch-27-the-convolutional-breakthrough.md             (+51 lines, Tier 1 + Tier 2 + 1 Tier 3)
src/content/docs/ai-history/ch-28-the-second-ai-winter.md                       (+43 lines, Tier 1 only)
src/content/docs/ai-history/ch-29-support-vector-machines.md                    (+48 lines, Tier 1 + Tier 2)
src/content/docs/ai-history/ch-30-the-statistical-underground.md                (+41 lines, Tier 1 only)
src/content/docs/ai-history/ch-31-reinforcement-learning-roots.md               (+42 lines, Tier 1 only)

docs/research/ai-history/chapters/ch-{24..31}-*/tier3-{proposal,review}.md      (16 files, all new)
```

All on feature branches; primary `main` is unchanged at `5cab4276`.

## Memory updates

- `feedback_no_parallel_agent_fanout.md` (new) — TOP PRIORITY rule against `Agent(isolation="worktree")` chapter fan-out.
- `reference_agent_worktree_recovery.md` (new) — cherry-pick + reset recovery procedure when the race hits anyway.
- `MEMORY.md` (updated) — pointers added under TOP PRIORITY.

## Worktrees still in flight

8 per-branch worktrees remain at `.worktrees/claude-394-chXX-aids` (sequential, orchestrator-managed — these are NOT the broken Agent worktrees, those were cleaned up during recovery). After PRs merge, run `git worktree remove .worktrees/claude-394-chXX-aids` × 8.

```
.worktrees/claude-394-ch24-aids   [claude/394-ch24-reader-aids]
.worktrees/claude-394-ch25-aids   [claude/394-ch25-reader-aids]
.worktrees/claude-394-ch26-aids   [claude/394-ch26-reader-aids]
.worktrees/claude-394-ch27-aids   [claude/394-ch27-reader-aids]
.worktrees/claude-394-ch28-aids   [claude/394-ch28-reader-aids]
.worktrees/claude-394-ch29-aids   [claude/394-ch29-reader-aids]
.worktrees/claude-394-ch30-aids   [claude/394-ch30-reader-aids]
.worktrees/claude-394-ch31-aids   [claude/394-ch31-reader-aids]
```
