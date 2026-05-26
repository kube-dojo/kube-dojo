# Session Status — index

> Index, not log. Per-session handoffs in [`docs/session-state/`](./docs/session-state/) — this file points at them.
> Briefing API parses `## TODO` and `## Blockers` (keep those headings populated).
> Older sessions (pre-2026-05-24) live in [`docs/session-state/archive-pre-2026-05-24.md`](./docs/session-state/archive-pre-2026-05-24.md) plus the dated `.html` files alongside.

## Cold-start protocol

1. **Issue-driven**: `KUBEDOJO_ISSUE=N bash scripts/cold-start.sh` after reading the issue verbatim.
   **Standalone**: `bash scripts/cold-start.sh` (add `--manifest` for route discovery).
   The script does services-up, `git status`, pending decisions, briefing, orient, handoff pointer. Exit 0 with `STATUS.md` fallback on API failure.
2. Scan [`docs/decisions/pending/`](./docs/decisions/pending/) before unrelated work (also surfaced by the script).
3. Read **Latest handoff** below only if briefing/orient leave a narrative gap.

## Latest handoff

| Date | Session | Summary | Handoff |
|------|---------|---------|---------|
| 2026-05-26 | **56** | 15-PR batch. Epic #1530 AI Engineering Foundations fully closed (Wave 2 + Wave 3 + Wave 4 + Phase 4 — all 12 modules of the new section shipped + ADR + 3 orphan redirect stubs + 3 cross-link additions). Critical-rubric drain begun: 5 of 122 on-prem modules rewritten to T0 in this batch (modules 7.4, 1.3, 1.5, 2.2, 2.3 + Phase E.1 #1521 + #1524). **gemini-3.1-pro-preview proved viable as full T0 author** on first trial (PR #1569 — 5034 body_words, T0 first-pass) — now the 4th T0 author option alongside codex/cursor/deepseek. CI cross-family review workflow end-to-end functional after user added API keys (PR #1564 dropped redundant gemini-3.5-flash@high). 5 issues closed (#1521 #1524 #1530 #1534 #1535). Repo hygiene: 35 prunable worktrees + 42 prunable branches → 0. 13 new memory entries. | [session-56](./docs/session-state/2026-05-26-session-56-fifteen-prs-plus-gemini-t0-trial-plus-phase4-close.html) |
| 2026-05-25 | 55 | 15-PR flood. CI cross-family review workflow shipped + operational on every subsequent PR (#1542). Hermes argv bug class fully eradicated across 4 PRs. 5 issues closed (#1517/#1518/#1520/#1523/#1538). #1530 Wave 2 author phase complete (4 PRs merged). Cross-family review chain caught 6 real bugs. Wave 3.1 codex T0 in-flight at handoff write. | [session-55](./docs/session-state/2026-05-25-session-55-fifteen-pr-flood-wave-2-complete-plus-hermes-eradication.html) |
| 2026-05-25 | 54 | Research-driven 4-PR landing (#1532/#1539/#1540/#1541) + 2 research artifacts + 2 memory locks (codex-writer/composer-reviewer pair, no-premature-issue-close). #1530 reopened. CI cross-family review workflow scoped. | [session-54](./docs/session-state/2026-05-25-session-54-research-driven-4-prs-plus-ai-engineering-foundations-2-2.html) |

Older predecessors: see [`docs/session-state/`](./docs/session-state/) (53 dated handoff files, sessions 13-55).

## Active policies

- **Decision Card C (accepted 2026-05-24)**: composer-2.5 = primary cross-family T0 content reviewer; codex = secondary. Symmetric routing: composer-2.5-authored content → codex reviews. Source: [`docs/decisions/2026-05-24-reviewer-routing-composer-2-5.md`](./docs/decisions/2026-05-24-reviewer-routing-composer-2-5.md).
- **gemini-3.1-pro-preview is 4th T0 author option (locked 2026-05-26 PR #1569 trial)**: T0 rotation now codex / cursor composer-2.5 / deepseek-v4-pro / **gemini-3.1-pro-preview**. Reviewer-of-gemini stays composer-2.5 (cursor) per Decision Card C. Watch 3x weekly buff burnable in ~2hrs of heavy use. Memory: `feedback_gemini_3_1_pro_viable_t0_author`.
- **MAX 6 core sections is HARD CAP — agent-class-wide overshoot pattern (session 55 + 56)**: cursor, gemini, and occasionally codex default to 7 H2 core sections when brief lists 7+ topic bullets. Brief language locked: "MAX 6 (HARD CAP) — fold the two most-related topic bullets into one H2 with H3 subsections" + post-write count step. Three-way-rule fix candidate: add `structure_core_sections_4_6` deterministic gate to `verify_module.py`. Memory: `feedback_cursor_overshoots_core_section_limit`.
- **deepseek review requires `--mode workspace-write`**: `dispatch_smart.py review --agent deepseek --mode read-only` fails in ~31s ("tool-use intent without execution"). Mode upgrade is required. cursor + gemini work fine with read-only. Memory: `feedback_deepseek_review_needs_workspace_write_mode`.
- **agy + deepseek review-class hallucination patterns**: agy invents fix-pass narratives during review (claims to have "applied changes" not in git log); deepseek invents fake verifier gate names. Mitigation: include actual `verify_module.py` output in deepseek brief; cross-check agy claimed-fixes against git log. Memory: `feedback_agy_and_deepseek_hallucinate_reviews`.
- **agy unsafe for clean-branch T0 authoring (session 56 PR #1559 closed)**: agy TUI persists branch state across dispatches → ignores `--new-branch` + `--worktree`. STAYS approved for review/architect/edit-on-existing-branch. Memory: `feedback_agy_tui_session_bleed_t0_author`.
- **Condition-dependent T0 author lane (locked 2026-05-25, PR #1525)**: codex gpt-5.5 is T0 primary when codex cap healthy; cursor composer-2.5 takes over during throttle. Reviewer side unchanged. Use `--model gpt-5.5` explicitly (spark dies rc=-9 at our prompt sizes — 2/3 first-tries failed session 53).
- **Codex-writer / composer-2.5-reviewer pair (locked 2026-05-25 user directive, session 54)**: default T0 content shape — codex authors, composer-2.5 reviews. Memory: `feedback_codex_writer_composer_reviewer_pair.md`.
- **Cursor reviewer must use explicit `--model composer-2.5`**: cursor CLI rejected implicit `gpt-5.5` model name mid-session 54 with "AI Model Not Found". Workaround locked: every `dispatch_smart.py review --agent cursor` call passes `--model composer-2.5` explicitly.
- **Issues stay open until QG'd (locked 2026-05-25, session 54)**: no-bureaucracy ≠ no-discipline. Epics with unchecked acceptance-criterion boxes stay OPEN even after their first wave merges. Cold-start scans open epics for unchecked boxes idle ≥7 days. Memory: `feedback_no_premature_issue_close.md`.
- **curriculum-orchestrator skill loads at session start (locked 2026-05-25, session 54)**: `CLAUDE.md` Agent Orientation section names this as FIRST ACTION every session. `scripts/cold-start.sh` reinforces by printing the directive at both exit paths.
- **Autocompact disabled (2026-05-25)**: `CLAUDE_CODE_AUTO_COMPACT_WINDOW=1000000` in `start-claude.sh`. Auto-compact is destructive; durable handoff via `docs/session-state/*.html` + STATUS.md is strictly better. Statusline goes bold-red at 500K used — handoff trigger.
- **Cursor no-merge arrangement (locked 2026-05-24)**: cursor creates issues + opens PRs + comments "claiming"; orchestrator merges after cross-family review.
- **HTML-first artifact policy**: orchestrator artifacts (handoffs, audits, dispatch briefs, autopsies) default to `.html`; STATUS.md / CLAUDE.md / `.claude/rules/` / memory stay `.md`.
- **No separate dispatch watchers**: the `run_in_background: true` exit notification IS the signal. Read `logs/dispatch_responses/<task-id>.txt` directly when wrapper fires. See `feedback_no_separate_dispatch_watcher.md`.
- **Learner-check hook is load-bearing**: `.claude/hooks/block-content-merge-without-learner-check.sh` blocks `gh pr merge` on content PRs without a `## Learner check` section quoting verbatim from a touched module. **Gotchas confirmed session 55**: (1) chained `gh pr edit && gh pr merge` triggers the hook on the merge intent BEFORE the edit runs — split into separate Bash calls; (2) bugfix-merge hook also triggers on `fix(` prefix — content-cleanup PRs without a real test file should use `chore(` prefix instead (memory: `feedback_chore_vs_fix_prefix_for_bugfix_hook`).
- **CI cross-family review workflow operational (locked 2026-05-25 PR #1542)**: every PR runs 3 reviewer jobs (gemini-3.1-pro-preview / gemini-3.5-flash@high / deepseek-v4-pro). Comment-only / continue-on-error so merges still flow even when jobs fail. **User must add repo secrets `GEMINI_API_KEY` + `DEEPSEEK_API_KEY`** before the workflow can post actual review comments.

## Current state

- **~776 English modules** (761 + 15 new session 56: Wave 3.2 module-2.4 dynamic-context-orchestration · Wave 4 harness-fundamentals/guardrails/operating/Symphony · #1521 Disconnected K8s · #1524 IPv6-only K8s + 5 critical-rubric rewrites + Phase 4 stubs); **312 Ukrainian** (~40%).
- **Starter tracks 499/499 at heuristic 5.0** (unchanged).
- **~115 critical-rubric REWRITES remain** (was 122 — session 56 closed 7: modules 7.4 observability, 1.3 cluster-topology, 1.5 onprem-finops, 2.2 PXE, 2.3 immutable-OS, plus #1521 + #1524 new-modules-not-strictly-rewrites).
- **388 modules need composer-2.5 review** (heuristic-green but not yet composer-2.5-reviewed) — epic #1504, 77 sections, ~58h cursor wall-clock.
- **All Phase E.1 residual issues closed** (#1521 + #1524 merged via PR #1566 + PR #1567).
- **#1530 AI Engineering Foundations epic FULLY CLOSED** via PR #1565 (Phase 4 cleanup). All 12 modules of the new section shipped + ADR + 3 orphan-redirect stubs + bidirectional cross-links.
- Site: https://kube-dojo.github.io/ (Starlight/Astro, ~1,350 pages, ~30-40s build).
- Services: `./services.sh {start|stop|restart|status} {dev|api|feedback}` (api on :8768, dev on :4333).

## TODO

**Next session — top priorities:**

- [ ] **Continue the 122 critical-rubric drain** — 7 closed session 56 (modules 7.4, 1.3, 1.5, 2.2, 2.3 on-prem + #1521 + #1524). ~115 remain. Briefing API surfaces top-5 in `actions.next`. Rotate across all 4 T0 authors (codex / cursor / deepseek / gemini-3.1-pro). Watch gemini quota (3x buff burns in ~2hrs of heavy use).
- [ ] **Visual sanity-check the 15 merged session-56 modules** on the live site after `deploy.yml` runs (`feedback_dont_block_on_human_pass`).
- [ ] **388-module composer-2.5 review epic #1504** — standing-watch unchanged: cursor comments "claiming section X" or opens a PR; orchestrator picks up the review queue.
- [ ] **Phase 4 follow-up verification**: after deploy, visually confirm the 3 orphan-redirect stubs (prompt 1.6, harness 2.1, Symphony 2.2 in legacy locations) actually render the "moved to" link correctly in Starlight. Mixed path styles used (absolute `/ai/...` vs relative `../../ai-engineering-foundations/...`) — both should resolve but worth a check.
- [ ] **Codex spark default broken** for our prompt sizes (PR #1521 first attempt 65s empty response). Either (a) patch `scripts/dispatch_smart.py` to default codex draft to gpt-5.5, OR (b) keep passing `--model gpt-5.5` explicitly. Patch is the better fix.
- [ ] **Three-way-rule fix** for the 4-6 core-section overshoot pattern: add `structure_core_sections_4_6` deterministic gate to `scripts/quality/verify_module.py` so the verifier catches overshoots before reviewer.
- [ ] **9 issues still open**: #14 monitoring · #143 Ukrainian full-coverage · #373 liveness probes · #383 UK re-sync · #386 lab quality · #393 AI history depth · #1299 gap analysis · #1350 gemini-cli → agy migration (deadline 2026-06-18) · #1401/#1402/#1404 calibration · #1502 calibration dashboard · #1504 review epic. None are top-of-queue.
- [ ] **Build the 12-week LLM-engineering sub-track** (Osman gap analysis recommended in #1535 close comment): 3 net-new modules (Speculative Decoding+Medusa, MoE Architectures, Mechanistic Interpretability) + `ai-ml-engineering/synthesis-apps/the-12-week-llm-stack/` index threading existing scattered modules.

**Date-bound:**

- 2026-06-08: claude-i wrapper pilot.
- 2026-06-15: agentic-credit-pool flip (claude-throttle expires).
- 2026-06-18: drop gemini-cli adapter (agy Phase 3 cutover) — see issue #1350.
- 2026-07-13: weekly-double bump expires.

**Long-running epics (not currently top-of-queue):**

- #197 On-Premises track expansion · #143 Ukrainian full-coverage · #14 monitoring (permanent) · #393 AI history depth · #386 lab quality audit · #1299 gap analysis · #1413 calibration single-fixture lanes · #1416 calibration auto-render hook.

## Blockers

_None._

## Key decisions / facts

- Starlight (Astro) replaces MkDocs Material; defaultLocale `root` (English at `/`, Ukrainian at `/uk/`).
- `scripts/dispatch_smart.py` is the canonical task-class agent dispatcher.
- GH Actions SHA-pinned, requirements hash-locked, Dependabot enabled, branch protection on `main` (4 required checks, no force push).
- 2026-04-28: STATUS.md migrated to index pattern (was a 1,623-line forever-growing log).
- 2026-05-24: STATUS.md re-compressed to ~100 lines; sessions 13-51 narrative moved to [`docs/session-state/`](./docs/session-state/) HTMLs.
- 2026-05-25 session 55: Hermes argv bug class fully eradicated (5 call-sites, all to `--oneshot=<prompt>` equals-form); CI cross-family review workflow operational on every PR.
- 2026-05-26 session 56: Epic #1530 AI Engineering Foundations fully closed (Wave 2 + Wave 3 + Wave 4 + Phase 4 all shipped). gemini-3.1-pro-preview promoted to 4th T0 author option after first-trial success on PR #1569. Critical-rubric drain begun (7 of 122 closed). CI cross-family review workflow end-to-end functional after user added API keys.

## End-of-session ritual

1. Write today's full handoff to `docs/session-state/YYYY-MM-DD-<topic>.html`.
2. Add a row at top of **Latest handoff** with 1-line summary + link. Shift the third row off to the `docs/session-state/` directory pointer (don't accumulate >3 rows here).
3. Update **TODO** + **Blockers** (briefing API depends on these headings).
4. Commit with `docs(status): handoff <date> — <topic>` style.

---
**Maintenance rule**: this file is the index. Detail goes in the dated handoff HTMLs. Keep STATUS.md ≤100 lines.
