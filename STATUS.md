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
| 2026-05-26 | **57** | Tech-debt focus + multi-agent deliberation. 2 PRs merged (#1574 /api/quality redirect-stub filter + upgrade-plan timestamp + stratified sampler; #1575 `claude_extensions/` → `agents_extensions/` rename with shared/per-agent split). 2 PRs in flight auto-merge (#1576 B′ decision result section; #1578 dispatch_smart `--auto-skill` flag, 10 tests). 1 tracking issue filed (#1577 24 Class A defects across 12 modules from back-catalog sample). **Decision Card B′ deliberation executed and aborted properly**: stratified n=15 sample found 80% NEEDS_CHANGES with at least one Class A learner-blocker across ALL 7 strata → reverted to Option A / Decision Card C / full #1504 backfill. Sample-first ordering caught the wrong assumption before stamping happened — zero artifact debt. 3 new top-priority memory entries. | [session-57](./docs/session-state/2026-05-26-session-57-b-prime-aborts-and-api-quality-fixed.html) |
| 2026-05-26 | 56 | 15-PR batch. Epic #1530 AI Engineering Foundations fully closed (Wave 2 + Wave 3 + Wave 4 + Phase 4). Critical-rubric drain begun: 5 of 122 on-prem modules rewritten to T0. **gemini-3.1-pro-preview proved viable as full T0 author** on first trial (PR #1569) — now the 4th T0 author option. CI cross-family review workflow end-to-end functional after user added API keys. 5 issues closed. Repo hygiene: 35 prunable worktrees + 42 prunable branches → 0. 13 new memory entries. | [session-56](./docs/session-state/2026-05-26-session-56-fifteen-prs-plus-gemini-t0-trial-plus-phase4-close.html) |
| 2026-05-25 | 55 | 15-PR flood. CI cross-family review workflow shipped (#1542). Hermes argv bug class fully eradicated. 5 issues closed. #1530 Wave 2 author phase complete. Cross-family review chain caught 6 real bugs. | [session-55](./docs/session-state/2026-05-25-session-55-fifteen-pr-flood-wave-2-complete-plus-hermes-eradication.html) |

Older predecessors: see [`docs/session-state/`](./docs/session-state/) (54 dated handoff files, sessions 13-56).

## Active policies

- **Decision Card B′ aborted; Decision Card C reinstated for the back-catalog (locked 2026-05-26, session 57)**: stratified n=15 sample found 80% NEEDS_CHANGES with Class A learner-blockers across ALL 7 strata. Rubric+no-issues is NOT a sufficient proxy for semantic correctness. The full 277-module composer-2.5 backfill via #1504 is reinstated. DO NOT repropose "skip cross-family review for high-rubric established modules" without naming what's different from this sample. Source: [`docs/decisions/2026-05-26-tiered-back-catalog-review-policy.md`](./docs/decisions/2026-05-26-tiered-back-catalog-review-policy.md). Memory: `feedback_back_catalog_full_review_required`.
- **agents_extensions/ replaces claude_extensions/ (locked 2026-05-26, PR #1575)**: source-of-truth dir for skills/hooks/statusline + per-agent extensions. `shared/skills/` is loaded by ANY agent; `claude/` materializes to `.claude/`; `codex/`/`cursor/`/`gemini/` placeholders for future. `deploy.sh --target claude|codex|cursor|gemini|all`. Dispatch-time auto-load (PR #1578) reads from `agents_extensions/shared/skills/<name>/SKILL.md`.
- **Skill auto-loading in dispatch_smart (locked 2026-05-26, PR #1578)**: `draft`/`edit` → curriculum-writer; `review` → cross-family-reviewer; `architect`/`search` → none. `--skill <name>` override, `--no-skill` disable. Headless agents (codex/cursor/gemini/deepseek) now get role discipline automatically.
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
- **CI cross-family review workflow now gemini-only (locked 2026-05-26 session 57 PR #1581)**: deepseek-v4-pro reviewer job REMOVED from CI after `api.deepseek.com` outbound from GH Actions runners triggered repo-level "Your account is suspended" 403 on every `actions/checkout` for ~3 hours, blocking 4 PR merges. Workflow now runs `Review (gemini-3.1-pro-preview)` only as CI cross-family safety-net. Local dispatches via `dispatch_smart.py --agent deepseek` are unaffected — deepseek stays a viable T0 author + local reviewer. Memory: `feedback_no_china_apis_from_gh_actions`.

## Current state

- **803 English modules** (down from 806 reported — 3 redirect stubs now excluded by `/api/quality` scorer; see PR #1574); **312 Ukrainian** (~40%).
- **Starter tracks 499/499 at heuristic 5.0** (unchanged).
- **117 critical-rubric REWRITES remain** (was 120 reported — 3 phantom redirect-stub criticals dropped after the scorer fix; ~115 real critical modules to drain).
- **277 modules still need composer-2.5 review** (#1504 epic reinstated as full backfill after B′ abort; sample-first proved auto-approve unsafe).
- **24 Class A learner-blockers documented** in #1577 across 12 modules — immediate-fix candidates regardless of policy outcome.
- **`/api/quality` endpoints validated correct** (count 803, critical_count 117, upgrade-plan now has `generated_at`).
- Site: https://kube-dojo.github.io/ (Starlight/Astro, ~1,350 pages, ~30-40s build).
- Services: `./services.sh {start|stop|restart|status} {dev|api|feedback}` (api on :8768, dev on :4333).

## TODO

**Next session — top priorities:**

- [ ] **Verify PR #1576 + #1578 merged** (auto-merge was enabled but CI was delayed at session 57 end). If still BLOCKED, push a no-op trigger commit or use `--admin` if you have it.
- [ ] **Fix the 12 Class A modules from #1577** — start with worst offenders (4 A: platform/toolkits/devex/8.5-gitpod-codespaces; 3 A: cloud/aws-essentials/1.10-cloudwatch, linux/operations/8.2-network-administration, prereqs/zero-to-terminal/0.9-software-and-packages). One module per PR, codex/cursor/deepseek/gemini-3.1-pro rotation, cross-family R1 each. Issue body has per-module checklist.
- [ ] **Continue critical-rubric drain** — ~115 remain. Briefing API surfaces top-5 in `actions.next`. Rotate all 4 T0 authors. Watch gemini quota.
- [ ] **#1504 backfill is the long-running work** — full 277-module composer-2.5 review reinstated after B′ abort. Recommended cadence: 3-5 reviews per session in background.
- [ ] **Codex review fallback gotcha**: `dispatch_smart.py review --agent codex` fails because `inject-codex-danger-mode.sh` hook injects `--mode danger` which requires `--worktree`. For read-only review dispatches, route to cursor/gemini, OR fix the hook to skip read-only task classes.
- [ ] **Codex spark default broken** for our prompt sizes (carried from session 56). Patch `scripts/dispatch_smart.py` draft task class to default to `gpt-5.5`.
- [ ] **Three-way-rule fix**: add `structure_core_sections_4_6` deterministic gate to `scripts/quality/verify_module.py`.
- [ ] **9 issues still open**: #14 monitoring · #143 Ukrainian full-coverage · #373 liveness probes · #383 UK re-sync · #386 lab quality · #393 AI history depth · #1299 gap analysis · #1350 gemini-cli → agy migration (deadline 2026-06-18) · #1401/#1402/#1404 calibration · #1502 calibration dashboard · #1504 review epic. None top-of-queue.
- [ ] **Visual sanity-check the merged session-56/57 modules** on live site after `deploy.yml` runs.

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
- 2026-05-26 session 56: Epic #1530 AI Engineering Foundations fully closed. gemini-3.1-pro-preview promoted to 4th T0 author option. Critical-rubric drain begun (7 of 122 closed). CI cross-family review workflow end-to-end functional after user added API keys.
- 2026-05-26 session 57: Decision Card B′ deliberation executed and aborted properly. n=15 stratified back-catalog sample → 80% NEEDS_CHANGES with Class A learner-blockers across ALL 7 strata → reverted to Option A / Decision Card C / #1504 full backfill. Sample-first ordering caught wrong assumption before stamping; zero artifact debt. `claude_extensions/` → `agents_extensions/` rename (shared + per-agent split). Dispatch-time skill auto-loading shipped (`dispatch_smart.py --auto-skill`). 24 Class A defects filed as #1577.

## End-of-session ritual

1. Write today's full handoff to `docs/session-state/YYYY-MM-DD-<topic>.html`.
2. Add a row at top of **Latest handoff** with 1-line summary + link. Shift the third row off to the `docs/session-state/` directory pointer (don't accumulate >3 rows here).
3. Update **TODO** + **Blockers** (briefing API depends on these headings).
4. Commit with `docs(status): handoff <date> — <topic>` style.

---
**Maintenance rule**: this file is the index. Detail goes in the dated handoff HTMLs. Keep STATUS.md ≤100 lines.
