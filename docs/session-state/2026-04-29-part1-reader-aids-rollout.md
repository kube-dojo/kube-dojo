# Session handoff — 2026-04-29 — Part 1 reader-aids rollout (Ch02–Ch06 shipped, Ch07–Ch09 pending)

> Picks up after the same-day Ch01 prototype + reader-aid pattern freeze. User decided per-part rollout (T1+T2+T3 per chapter, then next chapter) over layered (T1 broad → T2 surgical → T3 selective). Five of eight Part 1 chapters now in PRs. Codex's autonomous chain shipped Ch59–61 to main during the session.

## What was decided

1. **Per-part rollout, not layered.** User pushed back on the layered (T1-broad-first) plan I proposed. Their argument prevailed on context-locality (one read per chapter × 3 tiers > three passes), reader distribution (Part 1 has ~5–10× the traffic of Part 9, so deep polish on early parts compounds), and milestone shape (each completed Part is a shippable unit). I conceded; the rollout is now per-chapter T1+T2+T3 sequential, in reader-order. **`feedback_codex_default_prose_expander.md` does not apply** — these are reader-aid PRs from Claude, not prose drafts.

2. **Cross-family review pattern: Codex on Tier 3 only.** Per-chapter Codex adversarial review on the Tier 3 proposal is the cross-family check; we skip per-chapter Gemini review. Ch01 prototype landed without external Gemini review (PR #566 had 0 reviews/comments before merge), and Codex Tier 3 review covers the only judgment-rich layer. Bit-identity + build + Codex T3 = the per-chapter cross-family check. A single Gemini batch pattern audit is queued for the end of Part 1 if desired.

3. **Tier 3 calibration: refusal is the right default.** Across Ch02–Ch06, only Ch03 landed a Tier 3 element (the theorem-17b absorption-law plain-reading, via Codex REVISE). The pattern: chapters whose prose carries inline plain-reading work in their own bodies — and Tier 2 math chapters where the math sidebar absorbs the formal content — refuse Tier 3 cleanly. The Ch01 prototype's 2/5 ratio was a calibration high; later chapters at 0–1/3 are consistent with the rule rather than a regression.

4. **PR-hygiene gotchas, both fixed.** Two issues surfaced on Ch05:
   - **Lost-edits gotcha**: `git checkout -b` interaction with a chapter file lacking a trailing newline silently dropped the working-tree edits between the commit invocation and what the commit actually captured. Memory: `feedback_verify_aids_after_branch.md`. Defensive habit: `printf '\n' >> ch-XX-*.md` before any branch op, and `git show --stat HEAD` after every commit to confirm chapter file is in the diff.
   - **Stale-base contamination**: PRs branched while Codex's Part 9 chain was advancing main can pick up Ch59/60/61 commits as part of their diff if main fast-forwards mid-session. Confirmed on Ch03 (PR #578 contaminated) and Ch05 (PR #580 contaminated). Fix: recreate the branch from current `main`, cherry-pick only the intended files via `git checkout <old-branch> -- <files>`. Replacement PRs #582 (Ch03) and #581 (Ch05) are clean. PR #577 (Ch02) and #579 (Ch04) were not affected.

## What shipped on main this session

Nothing from Claude landed on main yet — all five Part 1 PRs are open awaiting review/merge. Codex's Part 9 autonomous chain landed:

```
620aaf5e docs(ai-history): publish ch61 physics of scale (#394)
b8f58579 docs(ai-history): publish ch60 agent turn (#394)
ddfb22a4 docs(ai-history): publish ch59 product shock (#394)
```

**61 of 72 chapters on main.** Codex's chain is presumably still rolling on Ch62–72.

## Open PRs (5 of 8 Part 1 chapters)

| PR | Chapter | Tier 3 result | State | Notes |
|---|---|---|---|---|
| **#577** | Ch02 The Universal Machine | 0/4 | OPEN | Clean diff |
| **#582** | Ch03 The Physical Bridge | **1/3** (theorem-17b absorption law via Codex REVISE) | OPEN | Replaces #578 (closed; stale base) |
| **#579** | Ch04 The Statistical Roots | 0/3 | OPEN | Includes Tier 2 math sidebar (Markov chain transition probabilities, Onegin counts, dispersion coefficient) |
| **#581** | Ch05 The Neural Abstraction | 0/3 | OPEN | Replaces #580 (closed; lost-edits + stale base) |
| **#583** | Ch06 The Cybernetics Movement | 0/3 | OPEN | Narratively dense, no symbolic-density paragraphs |
| #578 | Ch03 (broken) | — | **CLOSED** | Superseded by #582 |
| #580 | Ch05 (broken) | — | **CLOSED** | Superseded by #581 |

## Pending Part 1 work (Ch07, Ch08, Ch09)

Same per-chapter playbook:

1. Read prose + contract files (`people.md`, `timeline.md`, `brief.md`) for the chapter.
2. Apply Tier 1 inline (TL;DR + cast 6 rows + timeline year-range + glossary 5–7 terms + still-matters note). For Ch07/Ch08/Ch09: **none of the three is on the Tier 2 math-sidebar list** per `docs/research/ai-history/READER_AIDS.md` item 6 — Tier 2 doesn't apply.
3. Defensive: `printf '\n' >> ch-XX-*.md` before any branch op.
4. Write `tier3-proposal.md` in the chapter's contract dir; default to all-SKIP unless a paragraph is genuinely symbolically dense (mathematical formulas, derivations, stacked abstract definitions). For institutional/biographical narrative, all-SKIP is the right answer — Codex agrees.
5. Dispatch `scripts/ab ask-codex --task-id ch0X-tier3-review --from claude --from-model claude-opus-4-7 --to-model gpt-5.5 --new-session --data <proposal-path> -` with a brief instruction message (see Ch04/Ch06 dispatches for templates). Run in background; build in parallel.
6. When Codex's review file lands, apply any APPROVE-d or REVISE-d candidates.
7. Branch from current main: `git checkout -b claude/394-ch0X-reader-aids main`.
8. Stage **only** the intended files: `git add src/content/docs/ai-history/ch-0X-*.md docs/research/ai-history/chapters/ch-0X-*/tier3-{proposal,review}.md`.
9. Commit. Then **`git show --stat HEAD`** — confirm the chapter `.md` is in the diff with non-trivial insertions (~50–60 lines T1; ~70 with T2; ~150+ with all three).
10. Push + open PR. Title pattern: `docs(ai-history): Tier 1 reader aids — Ch0X (#562, #564)` (or `Tier 1 + T3 (Y/Z)` if a Tier 3 element landed).

## Cold-start smoketest (executable)

```bash
# 1. State of Part 1 PRs:
gh pr list --state open --search 'claude/394-ch0' --limit 10

# 2. Confirm main is current (Codex Part 9 may have advanced it):
git fetch origin && git log --oneline origin/main..HEAD origin/main -5

# 3. Verify the canonical reader-aid doc and Ch01 prototype are present:
ls docs/research/ai-history/READER_AIDS.md
head -15 src/content/docs/ai-history/ch-01-the-laws-of-thought.md  # should show :::tip[In one paragraph]

# 4. Confirm the prior-session PRs of mine are visible:
for pr in 577 579 581 582 583; do gh pr view $pr --json number,title,state --jq '{n:.number,t:.title,s:.state}'; done

# 5. Pop the dashboard stash if you want to continue dashboard panel work:
git stash list  # expect: 1 entry "WIP: book progress + module distribution dashboard panels"
# git stash pop  # only if user wants
```

## What's next (lanes the next session can pick up in any order)

1. **Ship Ch07, Ch08, Ch09** to complete Part 1. Same playbook above. Estimated ~10 min orchestration per chapter (faster now that the pattern is calibrated; Codex review is ~1–2 min in the background).
2. **Wrap-up after Part 1 closes**: STATUS.md cross-thread notes, single Gemini pattern-audit dispatch (optional), pop the dashboard stash for the user.
3. **Then Part 2 (Ch10–17)**: same per-chapter rollout. Heads-up — Ch10 is "The Imitation Game" (Turing 1950); the Pierce/Lighthill thread doesn't kick in until later parts. Should be straightforward T1; no Tier 2 chapters in Part 2 (Ch15 is "The Gradient Descent Concept" — verify its math-sidebar applicability against `READER_AIDS.md` item 6).

## Cross-thread updates (for STATUS.md)

- DONE this session, drop from cross-thread notes:
  - PR #558 (Ch51 stale prose) — still pending; not touched this session.
  - PR #565 (Ch52 stale prose) — still pending; not touched this session.
  - **NEW**: PR #578 and PR #580 — closed-and-superseded by #582 and #581 respectively.
- ADD to cross-thread notes:
  - **Per-chapter reader-aid playbook** is calibrated across Ch02–Ch06. Tier 3 lands cleanly when prose has symbolic density and the math sidebar isn't already covering it; otherwise all-SKIP is the right outcome. Ratio so far: Ch01 2/5; Ch02 0/4; Ch03 1/3; Ch04 0/3; Ch05 0/3; Ch06 0/3.
  - **Two PR-hygiene gotchas now memorised**: lost-edits across `checkout -b` on no-trailing-newline files (memory: `feedback_verify_aids_after_branch.md`); stale-base contamination from concurrent Codex Part 9 advances (recreate from current main + cherry-pick).
  - **Codex Part 9 chain is past Ch61** at session end. Don't disturb; expect Ch62+ on main soon.
  - **Dashboard WIP stashed**: `WIP: book progress + module distribution dashboard panels (paused for Part 1 reader-aid rollout)`. Pop after Part 1 ships.

## Cleanup items still pending

- **PR #558 (Ch51) + PR #565 (Ch52)** — still stale from prior session; content already on main. Not touched this session.
- **PR #567 (review-coverage schema)** — still open from prior session; not touched.
- **Tier 2 math sidebar review across Part 1**: only Ch04 was Tier 2 in Part 1. The next Tier 2 chapter is Ch15 (in Part 2).
- **Tier 3 inline-definition mechanism (item 8)**: still SKIPPED universally; needs a Tooltip component decision before any chapter can land an inline parenthetical.

## Pace data

- Cold start (briefing + git + state read): ~3 min
- Per-chapter T1+T3+ship orchestration: ~8–12 min (Ch02 was longest at ~15 min as the calibration; Ch04 with Tier 2 was ~12 min; Ch06 was ~10 min)
- Codex T3 review dispatch: ~1–2 min sequential (cannot parallelise per `feedback_codex_dispatch_sequential.md`)
- Build verification: ~80 s wall-clock; runs in background concurrent with T3 dispatch
- PR hygiene incident (Ch05 lost-edits + stale-base contamination + recreate-and-supersede #578 and #580): ~25 min total

Total session: ~3 h, including the contamination cleanup. Net throughput: 5 chapter PRs in ~3 h ≈ ~36 min/chapter end-to-end at this rate.
