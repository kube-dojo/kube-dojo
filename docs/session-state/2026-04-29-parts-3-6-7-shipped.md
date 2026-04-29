# Session handoff — 2026-04-29 — Parts 3/6/7 shipped, STATUS migration, STEP 0

> 7-hour overnight session (2026-04-28 23:00 → 2026-04-29 06:00). Ran the user-directed Parts 3/6/7 finish queue end-to-end on top of an index-pattern migration of `STATUS.md` and the STEP 0 verdict-pass routing fix. 13 chapters shipped. 30+ chapter-pipeline PRs merged in sequence. Branch: `main` at `0603f2ab` (clean apart from the pre-existing user-side dirty `scripts/local_api.py` and orphan `test_rendering.js`).

## What shipped

### 1. STATUS.md → index pattern (1623 → 141 lines)

Lifted from learn-ukrainian's `docs/session-state/current.md` pattern: `STATUS.md` is now an index that points at per-session files in `docs/session-state/`. End-of-session ritual: write a new dated handoff, promote it to "Latest" in the index, demote the previous Latest into "Predecessor chain". Briefing API parser unchanged (still reads `## TODO` and `## Blockers`); regression-tested live before commit.

- Commit: `8b51d6c8 docs(status): migrate STATUS.md to index pattern`
- Files: `STATUS.md` rewritten; `docs/session-state/2026-04-28-night-handoff-2.md` (extracted handoff); `docs/session-state/archive-pre-2026-04-28.md` (29 prior `## Prior` sections).

### 2. STEP 0 — Claude anchor reviewer in `dispatch_research_verdict.py`

Without this, Codex-authored research (every Part 6/7 chapter and Ch16) would have been verdict-passed by Codex reviewing itself = cross-family-rule violation. Added `claude_anchor_prompt(...)` mirroring `codex_prompt`, a `"claude"` branch in `fire()` with `claude-opus-4-7`, and `_anchor_agent_for_branch()` that routes by PR-branch prefix (`codex/394-...` → Claude, `claude/394-...` → Codex). Added `claude` to `--only` choices.

- Commit: `6295478c feat(ai-history): add Claude anchor reviewer + branch-based routing (#394)`
- First live use: PR #519 (Ch16). Routing log line confirmed `anchor=claude` on every Codex-authored verdict pass that followed (#525, #528, #532, #536, #539, #543, #545, #547, #549, #551, #553, #555).

### 3. Part 3 closure (Ch16 + cosmetic index links)

- Cosmetic Drafted-column links for Ch15 + Ch17-23: `86653146`.
- Ch16 full pipeline: `1b3e6337` (research, 27G/7Y/2R after fix-pass) → `cf8e64dd` (prose, 4,078w) → `9a4cf731` (Ch16 accepted roll-up). **Part 3 fully closed**.

### 4. Part 6 closure (Ch38 + Ch39 + Ch40)

| Ch | Research PR | Prose PR | Final words / cap | Lifecycle commit |
|---|---|---|---|---|
| 38 | #525 → `128310cf` | #527 → `eebc4b0c` | 4,404 / 5,100 | `de5d1d47` |
| 39 | #528 → `68d571cd` | #530 → `712c1d15` | 3,694 / 4,000 (Gemini cap) | `b36efe43` |
| 40 | #532 → `f9989995` | #534 → `fc14492c` | 3,950 / 4,700 | `569afee8` |

**Part 6 fully closed** at `569afee8`. Ch32-40 all accepted.

### 5. Part 7 closure (Ch41-49, 9 chapters)

| Ch | Topic | Research PR | Prose PR | Words / cap | Lifecycle |
|---|---|---|---|---|---|
| 41 | The Graphics Hack | #536 → `9bbc9ec9` | #537 → `510037f9` | 3,710 / 4,500 | `39ade8d0` |
| 42 | CUDA | #539 → `5465c182` | #541 → `7bd39bb9` | 4,155 / 4,500 | `413df329` |
| 43 | The ImageNet Smash | #543 → `6ce2bdbe` | #544 → `96c49e80` | 3,731 / 5,150 | `c9106447` |
| 44 | The Latent Space | #545 → `4cdc5428` | #546 → `4d42e0b9` | 4,107 / 4,950 | `b39e5420` |
| 45 | Generative Adversarial Networks | #547 → `e31a7f89` | #548 → `8ed0e98c` | 4,437 / 5,100 | `133710ba` |
| 46 | The Recurrent Bottleneck | #549 → `c4bcdc02` | #550 → `96c546da` | ~4,080 / 4,500 | `6f307a29` |
| 47 | The Depths of Vision | #551 → `1929f2a1` | #552 → `eec261d4` | 4,407 / 5,300 | `0f1b2538` |
| 48 | AlphaGo | #553 → `25d40e06` | #554 → `e322ed60` | 4,166 / 4,700 | `9884fd9b` |
| 49 | The Custom Silicon | #555 → `aacca110` | #556 → `29397990` | 4,298 / 4,900 | `0603f2ab` |

**Part 7 fully closed** at `0603f2ab`. Ch41-49 all accepted.

## Pace data

- Cold start (orientation + STATUS migration + STEP 0): ~25 min
- Per-chapter wall time: 20-35 min end-to-end (research dispatch → research PR open → verdict pass → research merge → prose dispatch → prose PR open → dual review → fix-pass + merge → index flip + commit)
- 13 chapters in ~7 hours = 32 min/chapter average
- Typical breakdown:
  - Codex research dispatch: 8-11 min
  - Verdict pass (Claude anchor + Gemini gap, parallel): 2-4 min
  - Research merge + prose dispatch (Gemini draft + Codex expand, sequential): 7-13 min
  - Prose dual review (parallel): 2-13 min depending on Gemini load
  - Fix-pass (when needed) + merge + index flip: 1-3 min

## Reusable lessons learned this session

1. **macOS `sed -i` quoting** breaks under bash command-substitution chains; the quoted `''` empty-extension argument gets eaten and the substitution string is treated as a filename. **Fix**: use the Edit tool, not `sed -i`, for in-place edits.

2. **`gh pr merge` race window**: chaining `git push branch` → `gh pr merge` → `git fetch main` in one bash call hits "Base branch was modified" or "fatal: Not possible to fast-forward" when GitHub's mergeability check hasn't refreshed yet OR when the autonomous Part 9 chain pushed an anchor commit between. **Fix**: poll `gh pr view N --json mergeStateStatus --jq '.mergeStateStatus'` until `CLEAN` or `UNSTABLE` before merge; on race failure, sleep 8s and retry once. Already coded into the `for i in 1..6` loop pattern used for every merge.

3. **Don't chain merge → prose-dispatch in one bash call**. If the merge races, the prose dispatch fires with the wrong base (research not yet on main → prose worktree built from stale main → useless output). **Fix**: split into two bash calls. Hit Ch38, Ch39, Ch41 with this; cleaned up each time but it cost a re-fire.

4. **Gemini word-count estimation undercounts by ~50%**. Multiple chapters this session flagged "below word-count target" when the dispatcher's `[read] prose: NN words` print showed actual words at or above target. Trust the dispatcher count, not Gemini's review estimate. Already documented from prior sessions; reaffirmed on Ch49 (Gemini said 2,150, actual 4,298).

5. **Pro-preview capacity exhaustion mid-session**. Around 03:50 Gemini-3.1-pro-preview started returning HTTP 429 "No capacity available" on review dispatches (autonomous Part 9 chain + my chain saturated the model). **Fix**: `KUBEDOJO_GEMINI_REVIEW_MODEL=gemini-3-flash-preview` env override. Used for every Ch46-49 review and one Ch45 review retry. Flash performed equivalently for the prose-quality lane.

6. **Codex sandbox can't write `.git/worktrees/.../index.lock`**. Every research dispatch produces `OK=True` from the agent runtime but no commit. Files are edited in the worktree; commit must happen from the parent worktree's git via `git -C <parent-tree> add <changed-paths>`. Built into every research-merge step.

7. **Gemini false-failure recovery worked perfectly**. The dispatcher's `[fire] gemini runner classified failure but commit on src/content/docs/ai-history/ch-NN-slug.md is present — treating as success` saved Ch42, Ch44, Ch45, Ch46, Ch47, Ch48. The prior session's recovery patch keeps paying off.

8. **Gemini once flagged a path-injection glitch (`Folding @docs/citation-seeds/...`) on Ch42 prose that didn't actually exist in the file**. Hallucinated artefact — the prose cleanly said "Stanford-based Folding@Home project". Flag cosmetically but do NOT auto-trust Gemini's "I see X in the prose" claims; verify with `grep` before applying.

## Cross-thread notes (active)

- **Autonomous Codex Part 9 chain** (`codex resume 019dcbc8-...`, started 2026-04-28 07:18 AM) anchored Ch63, Ch64, Ch65, Ch66, Ch67, Ch68, Ch69, Ch70, Ch71, Ch72 over the course of this session — coexisted cleanly with my dispatches. Don't disturb.
- **`gemini-3.1-pro-preview` capacity flap** (2026-04-28 PM and 2026-04-29 early AM) — saturated by combined load. Flash override env vars used routinely. Drop them when load returns to normal.
- **Stale worktrees not cleaned** (no urgency): `codex-344`, `gemini-394-ch01-research`, `gemini-394-ch06-research`, `gemini-394-ch08-research`. Origin branches are safety net.
- **User-side dirty files** still untouched: `scripts/local_api.py` (dashboard panel WIP), `test_rendering.js` (orphan).
- **Cosmetic backlog**: `dispatch_prose_review.py:368-381` reuses `codex_prose_quality_prompt` for the Gemini reviewer — header reads "Codex Prose Review" and prompt instructs reviewer to use shell tools Gemini doesn't have. Extract a `gemini_prose_quality_prompt` (carried from prior handoff, still pending).

## What's next

- All three user-directed parts (3, 6, 7) are now fully closed. Codex's autonomous chain is finishing Part 9 in parallel.
- Remaining at the AI-history book level: Part 8 (Ch50-58, all driven by Codex autonomously per the 2026-04-28 split) and Part 9 tail (Ch67-72, Codex autonomous chain has been anchoring). No Claude orchestration required.
- Next likely user direction: review the 13 freshly-shipped chapters; or pick up the broader rubric-critical rewrite track (485 modules at score <2.0 per the briefing's "actions.next") that has been waiting under the AI-history priority.

## Cold-start protocol (next session)

```bash
curl -s http://127.0.0.1:8768/api/briefing/session?compact=1
git log --oneline -5                    # confirm 0603f2ab + ...
git worktree list                       # codex-407-chXX-research workreees expected (autonomous chain)
gh pr list --search 'is:open #394'      # likely just autonomous chain in flight
```
