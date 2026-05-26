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
| 2026-05-26 | **58** | Class A drain (11 of 12) + #373 Phase 1. **12 PRs merged**: #1583 (gitpod 4 A), #1584 (cloudwatch 3 A + 2 fix-passes), #1585 (network-admin 3 A + 2 sibling fixes), #1588 (#373 Phase 1 livenessprobe primitives), #1589 (0.9-software 3 A), #1590 (1.2-ebpf-deepdive 2 A), #1591 (5.3-memory-management 7 A — sibling-grep caught 5 extras), #1592 (kcsa-5.3-runtime-security 1 A + image-runnability fix), #1593 (7.4-observability 1 A), #1594 (12.1-sonarqube 2 A — codex re-fired after gemini quota crash), #1595 (5.4-fleet-management 2 A), #1596 (10-gitops-bridge 2 A). 2 issues filed (#1586 dispatch_smart codex-review --worktree bug, #1587 density follow-up). User course-corrections drove triage: oldest-first / skip Ukrainian / defer #386 until content done. 3 new memories (learner-check brief mandate, sibling-grep brief mandate, commit-subject avoid-fix-N pattern). Gemini-3.1-pro-preview hit terminal quota mid-session — 22h reset. Only `neural-network-fundamentals` remains from #1577 (scope mismatch, not a fix-pass). | [session-58](./docs/session-state/2026-05-26-session-58-class-a-drain-plus-373-phase1.html) |
| 2026-05-26 | 57 | Tech-debt focus + multi-agent deliberation. 2 PRs merged (#1574 /api/quality redirect-stub filter + upgrade-plan timestamp + stratified sampler; #1575 `claude_extensions/` → `agents_extensions/` rename with shared/per-agent split). 2 PRs in flight auto-merge (#1576 B′ decision result section; #1578 dispatch_smart `--auto-skill` flag, 10 tests). 1 tracking issue filed (#1577 24 Class A defects across 12 modules from back-catalog sample). **Decision Card B′ deliberation executed and aborted properly**: stratified n=15 sample found 80% NEEDS_CHANGES with at least one Class A learner-blocker across ALL 7 strata → reverted to Option A / Decision Card C / full #1504 backfill. Sample-first ordering caught the wrong assumption before stamping happened — zero artifact debt. 3 new top-priority memory entries. | [session-57](./docs/session-state/2026-05-26-session-57-b-prime-aborts-and-api-quality-fixed.html) |
| 2026-05-26 | 56 | 15-PR batch. Epic #1530 AI Engineering Foundations fully closed (Wave 2 + Wave 3 + Wave 4 + Phase 4). Critical-rubric drain begun: 5 of 122 on-prem modules rewritten to T0. **gemini-3.1-pro-preview proved viable as full T0 author** on first trial (PR #1569) — now the 4th T0 author option. CI cross-family review workflow end-to-end functional after user added API keys. 5 issues closed. Repo hygiene: 35 prunable worktrees + 42 prunable branches → 0. 13 new memory entries. | [session-56](./docs/session-state/2026-05-26-session-56-fifteen-prs-plus-gemini-t0-trial-plus-phase4-close.html) |

Older predecessors: see [`docs/session-state/`](./docs/session-state/) (55 dated handoff files, sessions 13-57).

## Active policies

- **Oldest-first triage; Ukrainian + #386 deferred (locked 2026-05-26, session 58 user directive)**: work through open tickets oldest-first; Ukrainian translation epics (#143, #383) defer until EN modules production-ready; #386 lab audit + expansion defers until all gaps filled and all content written. Source: session-58 handoff "Policy moves" section. Operational consequence — active queue is #1577 → critical-rubric drain → #1299 gap-fill → #393 anchor depth → #1350 (deadline 2026-06-18) → #1504 backfill cadence; do NOT dispatch #386 lab rewrites until critical-count drops and #1577 finishes.
- **Content-fix briefs MUST mandate `## Learner check` blockquote (locked 2026-05-26, session 58)**: `.claude/hooks/block-content-merge-without-learner-check.sh` blocks merge on any PR touching `src/content/docs/**` without a verbatim-quote blockquote ≥30 chars from a touched module. Briefs sent to authors must include the requirement; orchestrator uses `gh pr edit --body-file` (heredoc chained with `&&` is flaky). Memory: `feedback_content_fix_brief_includes_learner_check`.
- **Class A fix briefs MUST mandate sibling-grep before changes (locked 2026-05-26, session 58)**: issue listings are sampled, not exhaustive. Roughly 1-in-3 Class A defects had siblings in the same module on session 58. Brief author to grep for the same anti-pattern across the full file FIRST and fix all occurrences in the same commit. Memory: `feedback_class_a_fix_includes_sibling_grep`.
- **Commit subjects MUST avoid `fix/closes/resolves #N` for epics that must stay open (locked 2026-05-26, session 58)**: #1577 auto-closed twice this session from `chore(content): fix #1577 module X` subjects despite `Refs #1577` in PR body. PR body `Refs` does NOT override the commit-subject auto-close. Use `chore(content): #N module X — defects fixed` or `module X refresh per #N`. Memory: `feedback_commit_subject_avoid_fix_n_pattern`.
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

- **803 English modules**; **312 Ukrainian** (~40%, deferred per user until EN production-ready).
- **Starter tracks 499/499 at heuristic 5.0** (unchanged).
- **117 critical-rubric REWRITES remain** at <2.0 rubric (unchanged from session 57; session 58 worked on Class A correctness, not rubric criticals).
- **277 modules still need composer-2.5 review** (#1504 epic full backfill). Session 58 cadence: **0 reviews**.
- **#1577 Class A epic**: **11 of 12 modules merged** this session (#1583, #1584, #1585, #1589, #1590, #1591, #1592, #1593, #1594, #1595, #1596). Only `ai-ml-engineering/deep-learning/module-1.1-neural-network-fundamentals.md` remains — its defect is a title/content scope mismatch (not a Class A fix-pass; needs rename-or-rewrite decision from user).
- **#373 Phase 1 livenessprobe primitives shipped** (PR #1588, `scripts/dispatch_livenessprobe.py` + 25 tests). Phase 2 (dispatch.py wiring) + Phase 3 (citation_backfill) still future.
- **#386 lab audit refreshed** (`docs/lab-audit-2026-05-26.md`, 269 labs scored, avg 2.25/5) — baseline for when #386 unlocks post-content-gaps.
- Site: https://kube-dojo.github.io/ (Starlight/Astro, ~1,350 pages, ~30-40s build).
- Services: `./services.sh {start|stop|restart|status} {dev|api|feedback}` (api on :8768, dev on :4333).

## TODO

**Next session — top priorities (oldest-first per user, skipping UK + #386):**

- [ ] **#1577 final module — neural-network-fundamentals** (scope decision required from user). Defect: title/path promises neural-network fundamentals but content teaches NumPy/pandas/visualization. Either (a) rename module to match content (`module-1.1-numpy-pandas-data-tooling.md`) + file follow-up for a real neural-network entry, OR (b) rewrite the body. NOT a Class A fix-pass — needs explicit direction.
- [ ] **Critical-rubric drain (117 at <2.0)** — briefing API surfaces top-5 in `actions.next`. Rotate all 4 T0 authors. Watch gemini quota.
- [ ] **#1504 backfill cadence** — 3-5 composer-2.5 cross-family reviews per session. ZERO this session; resume in parallel with content dispatches.
- [ ] **#393 AI/ML history depth pass UNBLOCKED** (#388 closed 2026-05-12). 4 of 6 anchor modules located: `ai/foundations/module-1.1-what-is-ai.md`, `module-1.2-what-are-llms.md`, `ai-ml-engineering/deep-learning/module-1.3-training-neural-networks.md`, `module-1.7-backpropagation-and-autograd-from-scratch.md`. Locate Transformers from Scratch + Single-GPU Fine-tuning. Codex suggested owner.
- [ ] **#1299 gap analysis** — quality-floor gate ("track critical-count < 50") currently closed. Survey state of per-module gap-fill issues; downstream of rubric drain.
- [ ] **#1350 agy migration (23 days to 2026-06-18 deadline)** — 30+ gemini-cli touchpoints. Untouched this session. Surface early next session.
- [ ] **#1586 dispatch_smart codex-review --worktree bug** — small code fix, unblocks codex as cross-family reviewer. Carve out review/search from the danger-mode forcing block at `scripts/dispatch_smart.py:619-627`.
- [ ] **#1587 density follow-up for #1577 modules** — 8.5-gitpod (1102 words) and 1.10-cloudwatch (1506 words) are rubric 5.0 but failing body_words floor. Filed; awaits prioritization.
- [ ] **#373 Phase 2 (dispatch.py wiring) + Phase 3 (citation_backfill integration)** — defer until content work clears.
- [ ] **Codex spark default broken** for our prompt sizes (carried from session 56-57). Patch `scripts/dispatch_smart.py` draft task class to default to `gpt-5.5`.
- [ ] **Three-way-rule fix**: add `structure_core_sections_4_6` deterministic gate to `scripts/quality/verify_module.py`.

**Date-bound:**

- 2026-06-08: claude-i wrapper pilot.
- 2026-06-15: agentic-credit-pool flip (claude-throttle expires).
- 2026-06-18: drop gemini-cli adapter (agy Phase 3 cutover) — see issue #1350.
- 2026-07-13: weekly-double bump expires.

**Deferred per user (session 58 directive):**

- #143 Ukrainian full-coverage · #383 UK re-sync — until EN modules production-ready.
- #386 Phase F lab quality audit + expansion — until all gaps filled and content written. Re-run `score_labs.py` at that point; baseline is `docs/lab-audit-2026-05-26.md`.

**Long-running epics (not currently top-of-queue):**

- #197 On-Premises track expansion · #14 monitoring (permanent) · #1401/#1402/#1404 calibration · #1413 calibration single-fixture lanes · #1416 calibration auto-render hook · #1502 calibration dashboard.

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
- 2026-05-26 session 58: **12 PRs merged** (11 of 12 #1577 Class A modules + #373 Phase 1 livenessprobe primitives). Discovered + fixed 3 new orchestration failure modes (commit-subject auto-close pattern, missing learner-check brief instruction, missing sibling-grep brief instruction) → 3 new memories locked. PR #1588 R1 caught real package/module shadowing bug. Gemini-3.1-pro-preview hit terminal quota mid-session (22h reset) — composer-2.5 + claude-headless absorbed review load. User course-corrected twice to keep momentum: "why are you not solving other open tickets?" → oldest-first triage; "what do you mean nothing to do?" → resume dispatching after premature wrap. Only `neural-network-fundamentals` (#1577 scope-mismatch case) remains for next session.

## End-of-session ritual

1. Write today's full handoff to `docs/session-state/YYYY-MM-DD-<topic>.html`.
2. Add a row at top of **Latest handoff** with 1-line summary + link. Shift the third row off to the `docs/session-state/` directory pointer (don't accumulate >3 rows here).
3. Update **TODO** + **Blockers** (briefing API depends on these headings).
4. Commit with `docs(status): handoff <date> — <topic>` style.

---
**Maintenance rule**: this file is the index. Detail goes in the dated handoff HTMLs. Keep STATUS.md ≤100 lines.
