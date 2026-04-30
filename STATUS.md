# Session Status — index

> **Read this first every session. Update before ending.**
>
> This file is an **index**, not a log. Per-session handoffs live in
> [`docs/session-state/`](./docs/session-state/) as dated files; this file
> just points at them. When you finish a session, **add a row to "Latest
> handoff" and shift the previous Latest into "Predecessor chain" — do
> NOT replace this whole file**.

## Cold-start protocol

1. Hit `curl -s http://127.0.0.1:8768/api/briefing/session?compact=1` (the API parses the `## TODO` and `## Blockers` sections of this file).
2. Read the row in **Latest handoff** below — that's the only file you need for current state.
3. Skim **Cross-thread notes (still active)** for stuff that spans sessions.
4. If picking up a long-running thread, click into the relevant **Predecessor chain** row.
5. Pre-2026-04-28 sessions (29 of them, going back to session 1) live in [`docs/session-state/archive-pre-2026-04-28.md`](./docs/session-state/archive-pre-2026-04-28.md) — kept for spelunking only, not actively maintained.

## Latest handoff

| Date | Thread | File | Status |
|------|--------|------|--------|
| 2026-04-30 (night-4) | Part 7 reader-aids (Ch41–Ch49) RELEASED + 26-PR merge sweep + lifecycle bookkeeping migration — Parts 1–7 fully on main (49 chapters); arch-sketch form-lock confirmed (LR for sequential, TD for hierarchies) | [`docs/session-state/2026-04-30-part7-reader-aids-shipped.md`](./docs/session-state/2026-04-30-part7-reader-aids-shipped.md) | **All Part 5/6/7 PRs merged** — 4/18 Part 7 Tier 3 candidates landed (~22%); Codex revived 3, revised 2; lifecycle fields (`prose_state` + `reader_aids`) on all 72 chapter status.yaml |

## Predecessor chain (most-recent first)

| Date | Thread | Where to find it |
|------|--------|------------------|
| 2026-04-30 (night-3) | Part 6 reader-aids (Ch32–Ch40) PR-complete — 9 PRs open; inline-sequential single-Agent-dispatch pattern validated at 9-chapter scale; first orchestrator-override of a Codex Tier 3 verdict (Ch38) | [`docs/session-state/2026-04-30-part6-reader-aids-prs.md`](./docs/session-state/2026-04-30-part6-reader-aids-prs.md) |
| 2026-04-30 (night-2) | Part 5 reader-aids (Ch24–Ch31) PR-complete — 8 PRs open; Agent worktree fan-out retired after 5/8 race incident; Tier 3 ran sequential | [`docs/session-state/2026-04-30-part5-reader-aids-prs.md`](./docs/session-state/2026-04-30-part5-reader-aids-prs.md) |
| 2026-04-30 | Part 4 reader-aids (Ch17–Ch23) RELEASED — 7 PRs #600–#606 merged via squash; parallel headless-Claude + parallel Codex Tier 3 dispatch | [`docs/session-state/2026-04-30-part4-reader-aids-prs.md`](./docs/session-state/2026-04-30-part4-reader-aids-prs.md) |
| 2026-04-29 (night-2) | Parts 2 & 3 reader-aids RELEASED — Ch10 closes Part 2; Ch11–Ch16 close Part 3; Mermaid click-to-enlarge modal shipped | [`docs/session-state/2026-04-29-parts-2-3-closed.md`](./docs/session-state/2026-04-29-parts-2-3-closed.md) |
| 2026-04-29 (night) | Part 1 RELEASED — section-header fix on Ch01–Ch09 + 9 PRs merged; right-nav now works | [`docs/session-state/2026-04-29-part1-released.md`](./docs/session-state/2026-04-29-part1-released.md) |
| 2026-04-29 (evening) | Part 1 reader-aids PR-complete — Ch07/Ch08/Ch09 shipped (3 PRs); all 8 Part 1 PRs open | [`docs/session-state/2026-04-29-part1-reader-aids-complete.md`](./docs/session-state/2026-04-29-part1-reader-aids-complete.md) |
| 2026-04-29 (afternoon) | Part 1 reader-aids rollout — Ch02–Ch06 shipped (5 PRs); PR-hygiene gotchas memorised | [`docs/session-state/2026-04-29-part1-reader-aids-rollout.md`](./docs/session-state/2026-04-29-part1-reader-aids-rollout.md) |
| 2026-04-29 (morning) | Ch01 reader-aid prototype (Tier 1+2+3) + math rendering fix + 6 sub-issues for rollout | [`docs/session-state/2026-04-29-reader-aids-ch01-prototype.md`](./docs/session-state/2026-04-29-reader-aids-ch01-prototype.md) |
| 2026-04-29 (overnight) | Parts 3/6/7 shipped (13 chapters) + STATUS.md index migration + STEP 0 routing | [`docs/session-state/2026-04-29-parts-3-6-7-shipped.md`](./docs/session-state/2026-04-29-parts-3-6-7-shipped.md) |
| 2026-04-28 night | Parts 3/6/7 finish queue setup (Ch16 + Ch38-40 + Ch41-49 plan) | [`docs/session-state/2026-04-28-night-handoff-2.md`](./docs/session-state/2026-04-28-night-handoff-2.md) |
| 2026-04-28 night | Part 6 fully closed (Ch32-37 + roll-up) | archive § "2026-04-28 night — Part 6 fully closed" |
| 2026-04-28 evening | Smart-router wrapper shipped; Claude resumes Parts 2/3 | archive § "2026-04-28 evening — smart-router wrapper" |
| 2026-04-28 | AI History Part 1 prose shipped | archive § "2026-04-28 — AI History Part 1 prose shipped" |
| 2026-04-27 evening | Part 3 dual-reviewed pipeline + ownership rebalance | archive § "2026-04-27 evening" |
| 2026-04-26 night | v4 handoff: bridges + drain-fix + What's New | archive § "2026-04-26 ~20:15 local — v4 handoff" |
| 2026-04-26 | #388 deferred-review batch under `KUBEDOJO_SKIP_REVIEW` | archive § "2026-04-26 ~10:55 local" |
| 2026-04-26 morning | #388 single-batch mode after concurrency-race compounding | archive § "2026-04-26 ~06:40 local" |
| 2026-04-26 ~03:35 | #388 batch resumed under hardened rewrite prompt | archive § "2026-04-26 ~03:35 local" |
| 2026-04-26 ~02:45 | #388 Phase 0 + #8 done; prioritized rewrite batch | archive § "2026-04-26 ~02:45 local" |
| 2026-04-25 night | #378 12-module recovery; 11/12 green | archive § "2026-04-25 ~22:00 local" |
| 2026-04-24 morning | 4 PRs merged, phase-2 pilot unblocked | archive § "2026-04-24 morning" |
| 2026-04-23 night | 6 PRs merged; cross-family reviewer rule codified | archive § "2026-04-23 night" |
| 2026-04-21 | pipeline_v4 built end-to-end, dogfood validated | archive § "Session 11 (2026-04-21)" |
| ≤2026-04-18 | Sessions 1–3 (citation-first infra, role-swap) | archive § "Prior session archive (sessions 1–3)" |

## Cross-thread notes (still active)

These are state items that span individual sessions. Prune entries as threads close.

- **#394 AI History — all 72 chapters of prose are on main.** Codex's autonomous Part 9 chain shipped through Ch72 (verified by file existence and word counts ≥4k each). The "Ch66–72 remain" line that lived here for the past few sessions was stale; corrected 2026-04-30 night-4.
- **Parts 1–7 reader-aids RELEASED on main (Ch01–Ch49 — 49 chapters).** All 26 reader-aid PRs (Parts 5/6/7) merged in one sweep 2026-04-30 night-4 after the user flagged the queue piling up. Each chapter carries Tier 1 (TL;DR + cast + timeline + glossary + Why-still-matters) plus selective Tier 2 (math sidebars on Ch01/04/15/24/25/27/29/44; architecture sketches on Ch41/42/49) plus selective Tier 3 (~20% landing rate, all Codex-reviewed cross-family).
- **Parts 8 & 9 reader-aids pending (Ch50–Ch72 — 23 chapters).** Tier 2 needed: Ch50 (math + arch), Ch52 (arch), Ch55 (math), Ch58 (math + arch). The other 18 chapters are Tier-1-only.
- **Architecture-sketch form-lock confirmed: `flowchart LR` for sequential dataflow, `flowchart TD` only when topology is genuinely hierarchical.** Three data points: Ch41 LR-lock, Ch42 LR→TD-deviation (CUDA grid → block → thread is hierarchical), Ch49 LR-reuse (TPU systolic array is linear). For Ch50/Ch52/Ch58, default to LR with explicit deviation justification only.
- **Lifecycle fields added to all 72 chapter status.yaml** (commit `ab801bf7`, addressing Codex bookkeeping note forwarded by user). New top-level fields: `prose_state` (`research_only | published_on_main`), `reader_aids` (`none | pr_open | landed`), `lifecycle_updated`. Existing `status` field untouched (keeps research-phase semantics). Per-chapter agents now flip `reader_aids` directly in their reader-aid commit.
- **Merge-as-you-go discipline reset.** Per-Part PR accumulation became debt at 24 open PRs. Going forward: squash-merge each reader-aid PR immediately after Codex Tier 3 review, do not let the queue accumulate.
- **Verbatim COMPLETE sentence rule for codex revives.** When codex revives an Element 9 pull-quote, the review must include the COMPLETE verbatim sentence in `>`-blockquote form, not a fragment. Ch43 Russakovsky revive needed a follow-up dispatch to extract the full sentence.
- **Inline-sequential single-Agent-dispatch pattern (no `isolation=worktree`) validated through 9 + 9 + 9 = 27 chapters (Parts 6/7).** Pre-create per-chapter worktree → dispatch one headless sonnet Agent (no isolation flag) with explicit `cd <worktree>` discipline → codex Tier 3 review → apply verdicts inline → push + PR → squash-merge → next chapter. Zero worktree GC races across the full sweep. ~9–15 min per chapter (Tier 2 chapters longer).
- **Agent worktree fan-out is RETIRED for chapter batches.** 5 of 8 agents missed their worktrees on Part 5 despite `touch .worktree-sentinel` mitigation (vs. 1 of 7 on Part 4). The race is unfixable from the prompt side; `Agent(isolation="worktree")` for parallel chapter work commits to primary main instead of the worktree branch. Future Part 6+ batches must be **inline / sequential** in the orchestrator. Recovery procedure documented at memory `reference_agent_worktree_recovery.md` (cherry-pick + reset).
- **Codex parallel `codex exec` still works** under `--dangerously-bypass-approvals-and-sandbox` direct invocation (6 in parallel Part 4 = ~5 min). The fan-out retirement is specific to `Agent(isolation="worktree")`, not all parallelism. Part 5 ran codex sequentially anyway (~16 min for 8) under the no-fan-out instruction; either pattern is acceptable for codex-only review batches.
- **Tier 1 dispatch prompt must require Green primary source for Tier 3 pull-quotes.** Every Part 5 author proposal cited "Chapter XX prose" as source, which fails Tier 3 source-discipline. Add to next dispatch prompt: "for the pull-quote, cite a Green primary source and confirm verbatim before proposing."
- **Concurrent `npm run build` in N worktrees corrupts the shared vite/astro cache** — all Part 4 agents flagged a false-alarm CSS build error from parallel-build interleaving. Mitigation: skip build verify; rely on CI post-merge.
- **Mermaid click-to-enlarge modal shipped** (`00ce1f1b`). Inline diagrams stay column-fit with a small "Click to enlarge" hint; click opens a fullscreen modal that clones the SVG, sizes it from its viewBox, and renders both-axis-scrollable at fullscreen. Light + dark themes verified. Close via X / Escape / backdrop click; focus restores; body scroll locks.
- **`scripts/ab ask-codex` wrapper drops stdin silently.** Two consecutive dispatches died with zero-byte output and exit 0 this session. Direct `codex exec -m gpt-5.5 -c model_reasoning_effort=high < /tmp/prompt.txt` works first try. Use the direct path until the wrapper is fixed.
- **Headless-Claude delegation rule reinforced** (memory `feedback_dispatch_to_headless_claude.md`). Tier 1 reader-aid design is exactly the kind of clean text-writing job that should go to `Agent(subagent_type="general-purpose")` so the orchestrator's context survives the batch. Plan locked in for Part 4.
- **Reader-aid layout pattern frozen** — Tier 1 + 2 + 3, non-invasive on bit-identical prose. Canonical doc: `docs/research/ai-history/READER_AIDS.md`. Ch01 prototype on `main` as `49e8e299` (PR #566). Tier 3 coeditor: Claude proposes / Codex reviews adversarially / Gemini for tie-breaks (Issue #564, memory `feedback_tier3_coeditor_pattern.md`).
- **Math rendering live** — `remark-math` + `rehype-katex` + KaTeX CSS in `astro.config.mjs` (commit `8c93d8db`). `$inline$` and `$$display$$` LaTeX both render. Fixes inline math across the entire AI history book retroactively.
- **STEP 0 routing shipped** (`scripts/dispatch_research_verdict.py`): branch-prefix routing puts Claude on anchor verification for `codex/394-...` research PRs and Codex for `claude/394-...` PRs.
- **`gemini-3.1-pro-preview` capacity flap intermittent under combined load.** When two chains run in parallel, pro-preview can return 429 "No capacity available". Fix: `KUBEDOJO_GEMINI_REVIEW_MODEL=gemini-3-flash-preview` env override.
- **Codex `mode="danger"` rule** for end-to-end dispatches that include `git push` + `gh pr create` (memory `feedback_codex_danger_for_git_gh.md`). Workspace-write silently fails on `.git/worktrees/.../index.lock` and `api.github.com`.
- **PR #558 (Ch51) and PR #565 (Ch52)** — both stale, content already on main. Close or rebase the index.md changes before next prose chain ships.
- **PR #567 (review-coverage schema)** — open, ready to review. After merge, re-run `scripts/audit_review_coverage.py` with live `gh` access (initial audit ran in offline-fallback mode, count of 30 backfill_pending may revise downward).
- **User-side dirty files to leave alone**: `test_rendering.js` (orphan). The `scripts/local_api.py` dashboard panel WIP from prior session is now stashed (`git stash list` shows `WIP: book progress + module distribution dashboard panels (paused for Part 1 reader-aid rollout)`); pop after Part 1 ships.
- **PR-hygiene gotchas memorised this session** (memory `feedback_verify_aids_after_branch.md`): (1) `git checkout -b` on a chapter file lacking a trailing newline silently drops working-tree edits — defensive habit `printf '\n' >> ch-XX-*.md` before any branch op + `git show --stat HEAD` after every commit; (2) PRs branched from main while Codex's Part 9 chain advances can pick up unrelated chapter commits in their diff — recreate from current main + cherry-pick.

## End-of-session ritual

1. Write today's full handoff to `docs/session-state/YYYY-MM-DD-<topic>.md` (or `YYYY-MM-DD-<topic>-N.md` if multiple in a day).
2. Edit this file:
   - Promote the new file to **Latest handoff** (overwrite the row).
   - Move the previous Latest into **Predecessor chain** (newest at top).
   - Update **Cross-thread notes** — add new long-running items, prune resolved ones.
3. Update **TODO** + **Blockers** below with current state (briefing API depends on these headings).
4. Commit with `docs(status): handoff <date> — <topic>` style message.

The pre-2026-04-28 archive is intentionally append-only; don't edit it. If a stale entry needs correction, do it in this index instead.

## Current State

**726 modules** across 8 published tracks. **115 Ukrainian translations** (~16% — certs + prereqs; AI/ML and AI not yet translated).

**Website:** https://kube-dojo.github.io/ (Starlight/Astro, ~1,350 pages, ~30-40s build)

**Site tabs:** Home | Fundamentals | Linux | Cloud | Certifications | Platform | On-Premises | AI | AI/ML Engineering

## Curriculum Summary

| Track | Modules | Status |
|-------|---------|--------|
| Fundamentals | 44 | Complete |
| Linux Deep Dive | 37 | Complete |
| Cloud | 85 | Complete |
| Certifications (CKA/CKAD/CKS/KCNA/KCSA/Extending + 12 learning paths) | 195 | Complete |
| Platform Engineering | 210 | Complete |
| On-Premises Kubernetes | 51 | Complete (needs Gemini review) |
| AI | 21 | Expanded bridge track; needs production-quality upgrades |
| AI/ML Engineering | 79 | Complete (expanded beyond Phase 4b; needs ongoing quality upgrades) |
| **Total** | **726** | **Complete** |

Per-track breakdowns (Cert / Cloud / On-Prem / Platform / AI/ML / AI / UK translations) live in the curriculum directories themselves; they were trimmed from this file 2026-04-28 because they were stable reference material that didn't belong in a session index.

## Quality Standard

**Rubric-based quality system** (`docs/quality-rubric.md`): 7 dimensions scored 1-5. Pass = avg ≥ 3.5, no dimension at 1.

**Audit results** (`docs/quality-audit-results.md`, 2026-04-03): 31 modules scored. Overall avg 3.3/5. Gold standard: Systems Thinking (4.6), On-Prem Case (4.4). 5 critical stubs fixed, 3 high-priority modules improved. 8 medium + 11 low priority remain.

**Systemic issues addressed**: formal learning outcomes added to all rewritten modules + writer prompt; inline active-learning prompts added (was back-loaded in 87% of modules); scenario-based quizzes replace recall-only.

## Open GitHub Issues

| # | Issue | Status |
|---|-------|--------|
| #14 | Curriculum Monitoring & Official Sources | Open |
| #143 | Ukrainian Translation — Full Coverage | Open (~40%) |
| #157 | Supabase Auth + Progress Migration | Open |
| #156 | CKA Parts 3-5 Labs | Open |
| #165 | Epic: Pedagogical Quality Review | Open (Phases 1-3,5 done; Phase 4: CKA/CKAD/On-Prem complete) |
| #180 | Elevate All Modules to 4/5 | Open (CKA/CKAD/On-Prem done; CKS/KCNA/KCSA/Cloud/Platform pending) |
| #177 | Improve Lowest-Quality Modules | Open (8 critical/high done, ~19 remaining) |
| #179 | Improve Lowest-Quality Labs | Open (blocked on Phase 3 lab audit) |
| #199 | AI/ML Engineering track migration + modernization | Open (Phase 4b done; Phase 7 cross-link + Phase 8 UK translate remain) |
| #200 | AI/ML local per-section module numbering (filename rename) | Open (delegated to Codex in worktree) |
| #394 | AI History book — 72-chapter prose lift | All prose on main (Ch01–Ch72); reader-aids #562 RELEASED for Parts 1–7 (Ch01–Ch49); reader-aids #562 pending for Parts 8–9 (Ch50–Ch72) |

## TODO

- [ ] AI history #559: cross-family review backfill on Ch01-31 (28 chapters, 30 marked backfill_pending per offline audit)
- [ ] AI history #562: Tier 1 reader-aid rollout — **Parts 1–7 RELEASED on main (Ch01–Ch49); Parts 8–9 (Ch50–Ch72, 23 chapters) remain.** INLINE / SEQUENTIAL with merge-as-you-go (squash each PR immediately after Codex review).
- [ ] Google Search Console verification — user will paste the meta-tag token (or HTML file). Then submit `https://kube-dojo.github.io/sitemap-index.xml` to GSC. Same flow optional for Bing Webmaster Tools.
- [ ] AI history #563: Tier 2 math + architecture sidebars on remaining target chapters: **Ch50 (math + arch), Ch52 (arch), Ch55 (math), Ch58 (math + arch)** — done: Ch01/Ch04/Ch15/Ch24/Ch25/Ch27/Ch29/Ch41/Ch42/Ch44/Ch49.
- [ ] AI history #564: Tier 3 selective passes — pattern proven on Ch01–Ch49; ~20% landing rate; all Codex cross-family-reviewed.
- [ ] PR #567 review + merge → then re-run audit_review_coverage.py with live gh
- [ ] PR #558 + PR #565 stale-prose cleanup (content already on main)
- [ ] AI/ML Engineering #199 remaining: Phase 7 cross-link (run), Phase 8 UK translate (skipped for now)
- [ ] AI/ML Engineering #200: local per-section module numbering (delegated to Codex)
- [ ] Remaining pipeline: On-Premises (30), Platform (209), Specialty (18) — #180
- [ ] Stuck modules: ~11 at WRITE (Gemini rejection loop), need knowledge packet retry
- [ ] ASCII→Mermaid conversion pass for all 587 modules — #193 (after #180)
- [ ] UK prereqs translation: re-sync after pipeline rewrites
- [ ] Lab quality audit and improvements — #179

## Blockers

- Gemini CLI output inconsistency: sometimes writes to files, sometimes returns to stdout — handled but fragile

## Key Decisions

- Migrated from MkDocs Material to Starlight (Astro) — faster builds, proper i18n, modern stack
- `scripts/dispatch.py` replaces `ai_agent_bridge/` — direct CLI dispatch, no SQLite broker
- GH Actions pinned to commit SHA, requirements locked with hashes, Dependabot enabled
- Pinned `zod@3.25.76` (zod v4 breaks Starlight schema validation)
- `defaultLocale: 'root'` for Starlight i18n — English at root URLs, Ukrainian at `/uk/`
- On-prem modules written by parallel agents (~500 lines each), need Gemini adversary review
- 2026-04-28: STATUS.md migrated to **index pattern** (was a 1623-line forever-growing log). Per-session handoffs now live in `docs/session-state/`; this file just points at them.

---
**Maintenance Rule**: Claude updates this file at session end or after completing modules. Per-session detail goes into a new `docs/session-state/YYYY-MM-DD-*.md` file, not inline.
