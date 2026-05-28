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
| 2026-05-28 | **66** | **PR #1635 merged: SessionStart hook now prepends FIRST ACTION reminder to invoke curriculum-orchestrator skill.** User asked if kubedojo could match learn-ukrainian's auto-orient. Investigation: learn-ukrainian uses AGENT pattern (`.claude/agents/curriculum-orchestrator.md` with `initialPrompt:` frontmatter + `"agent"` field in settings.json) — not a hook trick. Full SKILL→AGENT conversion would tax every session ~200 lines and collapse sub-skill structure (cold-start, dispatch-router, cross-family-reviewer). Chose lighter fix: hook prepends one-line `FIRST ACTION` reminder to `additionalContext`; headless paths (`CLAUDE_NON_INTERACTIVE` / `KUBEDOJO_PIPELINE` / `GEMINI_SESSION`) early-exit unchanged. Composer-2.5 R1 APPROVE (1 cosmetic comment nit, skipped). Merged as `4747cc26` via rebase. **Memory locked**: `feedback_git_C_over_cd_for_worktree_ops` — I used `cd /path/to/worktree && git commit` instead of `git -C <path>`; Bash tool cwd persisted 4 calls until user caught it. **Findings**: (a) pre-existing drift in `.claude/hooks/inject-codex-danger-mode.sh` — deployed copy missing `|| true` safety + comment from source — needs separate cleanup PR; (b) MEMORY.md at 207 lines, past 200 truncation. User picked Lane A FinOps 1.2-1.6 for next session, restarting to switch to claude-opus-4.8. | [session-66](./docs/session-state/2026-05-28-session-66-session-setup-hook-first-action-reminder.html) |
| 2026-05-28 | 65 | **Standing-decisions discussion attempted, format failed, 2 changes locked.** User asked to talk through standing decisions before continuing gap-fill work. Orchestrator turned the discussion into a 17-item AskUserQuestion voting form; user pushed back ("I DONT FUCKKING NO. SUE ME"; "you are supposed to help me and not interogate me"). Lesson: when user asks to discuss policy, orchestrator should arrive with positions and defend them, NOT surface every item as a vote. **2 changes locked**: (1) condition-dependent T0 fallback refined — codex throttle → **cursor auto-model** (not specifically composer-2.5); (2) core H2 section cap relaxed MAX 6 → ≤7 (stop fighting the agent-class natural shape). **9 standing decisions left as-is** with orchestrator recommendations documented in handoff. **5 agenda items the discussion never reached** (Lane A vs G3 priority, REPO_ROOT pinning fix, #1634 inject soften re-enable, codex T0 post-write hang, hook miss) — orchestrator recommended dispositions in handoff for next-session pickup. | [session-65](./docs/session-state/2026-05-28-session-65-standing-decisions-discussion-aborted.html) |
| 2026-05-28 | 64 | **Citation backfill cohort merged after OpenAI outage healed.** User confirmed ChatGPT reported overnight outage; codex bridge hangs from session 63 were external, not a code bug. Retried 3 flaky citation_backfill research calls (FinOps 1.1, 4.4 object-storage, 8.3 cloud-repatriation) — all succeeded clean. Ran inject → cursor R1 → cursor fix-pass → merge for all 3. **3 PRs merged**: #1631 FinOps 1.1, #1632 on-prem 4.4, #1633 on-prem 8.3. **2 issues closed**: #1605 (was OpenAI outage hang), #1621 (was OpenAI outage schema fail). **1 follow-up filed**: #1634 to track seed `cannot_be_salvaged` residuals (uncited adjacent claims that survive inject because inject step has `rewrites_disabled_pending_redesign`; R1 caught the pattern on all 3 PRs). Critical-rubric count 112 → 109. 3 operational findings for memory: (1) citation_backfill writes to PRIMARY repo dir via REPO_ROOT pinning, not the cd'd worktree — must run worktree-local script copy for inject; (2) Learner-check hook needs literal `## Learner check` (single H2); blockquote must be VERBATIM from a touched module including any markdown-link syntax codex's inject added; (3) seed `cannot_be_salvaged` disposition leaves uncited claims in prose by design — known limitation worth a Decision Card. User asked for end-of-session discussion of standing decisions + how to handle gaps + tech debts before continuing. | [session-64](./docs/session-state/2026-05-28-session-64-citation-backfill-cohort-merged.html) |
| 2026-05-28 | 63 | **Autonomous gap-fill wave starts: G1 NATS JetStream shipped + 5 issues filed + 2 infra fixes.** User went to sleep ~02:30 asking for auto mode. Outcomes: (1) gap-plan synthesis written at `docs/research/gap-plan-2026-05-28.html` from deepseek 2026-05-17 baseline + cursor composer-2.5 + cursor-auto; (2) 6 gap-fill issues filed under #1299 with label `gap-fill-2026-05` (#1622 G1 NATS, #1623 G2 engineering craft, #1624 G3 dist-systems labs, #1626 G4 LLM golden path, #1627 G5 workload identity, #1628 G6 OTEL Collector); (3) **PR #1630 G1 MERGED** — module 1.9 NATS JetStream on Kubernetes T0 quality (5157 body words, 21/21 verifier gates, 21 sources @ 200 OK), composer-2.5 R1 NEEDS_CHANGES → orchestrator inline fix-pass (sidebar entry + restore-cmd arg + sidebar.order 19→10), #1622 closed; (4) **PR #1625 MERGED** — cursor composer-2.5 added `raw_head`+`raw_tail` to `agent_response_invalid` diagnostic path, codex R1 APPROVE; (5) **PR #1629 MERGED** — hook fix: `inject-codex-danger-mode.sh` silenced grep-no-match pipefail that was emitting "PreToolUse:Bash hook error" noise on every plain Bash call. Lane A FinOps 1.1 backfill hung (codex bridge issue — diagnosed session 64 as overnight OpenAI outage). | [session-63](./docs/session-state/2026-05-28-session-63-autonomous-gap-fill-g1-and-hook-fix.html) |

Older predecessors: see [`docs/session-state/`](./docs/session-state/) (58 dated handoff files, sessions 13-62).

## Active policies

- **Gap-fill phase 1-5 of #1299 is NOT blocked by critical-count <50 (locked 2026-05-28, session 62 user correction)**: only step 6 (codex writes new modules into a track) is gated. Reviewer dispatches + synthesis + per-track issue filing can run any time and SHOULD run when standing gap inventories age past ~2 weeks. Conflating the two cost a session of misdirected fix-pass work. Source: user "you keep on fixing modules against my order to cover the gaps fir and you should ask gap analysis from cursor as well" (2026-05-28 wake-up).
- **Oldest-first triage; Ukrainian + #386 deferred (locked 2026-05-26, session 58 user directive)**: work through open tickets oldest-first; Ukrainian translation epics (#143, #383) defer until EN modules production-ready; #386 lab audit + expansion defers until all gaps filled and all content written. Source: session-58 handoff "Policy moves" section. Operational consequence — active queue is #1577 → critical-rubric drain → #1299 gap-fill → #393 anchor depth → #1350 (deadline 2026-06-18) → #1504 backfill cadence; do NOT dispatch #386 lab rewrites until critical-count drops and #1577 finishes.
- **Content-fix briefs MUST mandate `## Learner check` blockquote (locked 2026-05-26, session 58)**: `.claude/hooks/block-content-merge-without-learner-check.sh` blocks merge on any PR touching `src/content/docs/**` without a verbatim-quote blockquote ≥30 chars from a touched module. Briefs sent to authors must include the requirement; orchestrator uses `gh pr edit --body-file` (heredoc chained with `&&` is flaky). Memory: `feedback_content_fix_brief_includes_learner_check`.
- **Class A fix briefs MUST mandate sibling-grep before changes (locked 2026-05-26, session 58)**: issue listings are sampled, not exhaustive. Roughly 1-in-3 Class A defects had siblings in the same module on session 58. Brief author to grep for the same anti-pattern across the full file FIRST and fix all occurrences in the same commit. Memory: `feedback_class_a_fix_includes_sibling_grep`.
- **Commit subjects MUST avoid `fix/closes/resolves #N` for epics that must stay open (locked 2026-05-26, session 58)**: #1577 auto-closed twice this session from `chore(content): fix #1577 module X` subjects despite `Refs #1577` in PR body. PR body `Refs` does NOT override the commit-subject auto-close. Use `chore(content): #N module X — defects fixed` or `module X refresh per #N`. Memory: `feedback_commit_subject_avoid_fix_n_pattern`.
- **Decision Card B′ aborted; Decision Card C reinstated for the back-catalog (locked 2026-05-26, session 57)**: stratified n=15 sample found 80% NEEDS_CHANGES with Class A learner-blockers across ALL 7 strata. Rubric+no-issues is NOT a sufficient proxy for semantic correctness. The full 277-module composer-2.5 backfill via #1504 is reinstated. DO NOT repropose "skip cross-family review for high-rubric established modules" without naming what's different from this sample. Source: [`docs/decisions/2026-05-26-tiered-back-catalog-review-policy.md`](./docs/decisions/2026-05-26-tiered-back-catalog-review-policy.md). Memory: `feedback_back_catalog_full_review_required`.
- **agents_extensions/ replaces claude_extensions/ (locked 2026-05-26, PR #1575)**: source-of-truth dir for skills/hooks/statusline + per-agent extensions. `shared/skills/` is loaded by ANY agent; `claude/` materializes to `.claude/`; `codex/`/`cursor/`/`gemini/` placeholders for future. `deploy.sh --target claude|codex|cursor|gemini|all`. Dispatch-time auto-load (PR #1578) reads from `agents_extensions/shared/skills/<name>/SKILL.md`.
- **Skill auto-loading in dispatch_smart (locked 2026-05-26, PR #1578)**: `draft`/`edit` → curriculum-writer; `review` → cross-family-reviewer; `architect`/`search` → none. `--skill <name>` override, `--no-skill` disable. Headless agents (codex/cursor/gemini/deepseek) now get role discipline automatically.
- **Decision Card C (accepted 2026-05-24)**: composer-2.5 = primary cross-family T0 content reviewer; codex = secondary. Symmetric routing: composer-2.5-authored content → codex reviews. Source: [`docs/decisions/2026-05-24-reviewer-routing-composer-2-5.md`](./docs/decisions/2026-05-24-reviewer-routing-composer-2-5.md).
- **gemini-3.1-pro-preview is 4th T0 author option (locked 2026-05-26 PR #1569 trial)**: T0 rotation now codex / cursor composer-2.5 / deepseek-v4-pro / **gemini-3.1-pro-preview**. Reviewer-of-gemini stays composer-2.5 (cursor) per Decision Card C. Watch 3x weekly buff burnable in ~2hrs of heavy use. Memory: `feedback_gemini_3_1_pro_viable_t0_author`.
- **Core H2 section cap RELAXED to 7 (locked 2026-05-28 session 65, user directive)**: was MAX 6 HARD CAP from sessions 55-56; cursor/gemini/codex consistently produced 7 anyway. Brief language updates: drop the "MAX 6 HARD CAP — fold two related topic bullets" instruction; allow up to 7 core H2s. Stop fighting the natural shape. Verifier gate proposal `structure_core_sections_4_6` deprecated. Memory `feedback_cursor_overshoots_core_section_limit` to be updated.
- **deepseek review requires `--mode workspace-write`**: `dispatch_smart.py review --agent deepseek --mode read-only` fails in ~31s ("tool-use intent without execution"). Mode upgrade is required. cursor + gemini work fine with read-only. Memory: `feedback_deepseek_review_needs_workspace_write_mode`.
- **agy + deepseek review-class hallucination patterns**: agy invents fix-pass narratives during review (claims to have "applied changes" not in git log); deepseek invents fake verifier gate names. Mitigation: include actual `verify_module.py` output in deepseek brief; cross-check agy claimed-fixes against git log. Memory: `feedback_agy_and_deepseek_hallucinate_reviews`.
- **agy unsafe for clean-branch T0 authoring (session 56 PR #1559 closed)**: agy TUI persists branch state across dispatches → ignores `--new-branch` + `--worktree`. STAYS approved for review/architect/edit-on-existing-branch. Memory: `feedback_agy_tui_session_bleed_t0_author`.
- **Condition-dependent T0 author lane (refined 2026-05-28 session 65, user directive)**: codex gpt-5.5 is T0 primary when codex cap healthy; **cursor auto-model** (NOT specifically composer-2.5) takes over during throttle — cursor's auto-model picks the best available. Reviewer side unchanged. Use `--model gpt-5.5` for codex explicitly (spark dies rc=-9 at our prompt sizes). For cursor fallback, dispatch_smart should default to auto-model on draft class when codex throttled.
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

- **804 English modules** (G1 NATS JetStream shipped session 63); **312 Ukrainian** (~40%, deferred until EN production-ready).
- **Starter tracks 499/499 at heuristic 5.0** (unchanged).
- **109 critical-rubric modules remain** (-3 session 64: FinOps 1.1, on-prem 4.4, on-prem 8.3 drained via citation backfill). Average rubric 4.52 (+0.01 session 64). 106 of remaining 109 still "no citations" — citation_backfill pipeline confirmed working; same pattern applies to FinOps 1.2-1.6 + remaining 99 modules.
- **274 modules need composer-2.5 review** (#1504 epic; ~277 minus session 64's 3 backfill PRs that landed with composer-2.5 R1). Session 64 cadence: 3 R1s on the backfill cohort (all via composer-2.5 per Decision Card C). Back-catalog backfill cadence: 0 (skipped this morning to focus the codex slots on the citation cohort).
- **#1622 G1 CLOSED** session 63; **#1605 + #1621 CLOSED** session 64 (overnight OpenAI outage, not code bugs).
- **Citation backfill cohort merged session 64**: #1631 (FinOps 1.1), #1632 (on-prem 4.4 object storage), #1633 (on-prem 8.3 cloud repatriation).
- **Diagnostic PRs merged session 63**: #1625 (citation_backfill raw_head/raw_tail), #1629 (Bash hook silent-exit-1 fixed).
- **5 gap-fill issues open under #1299**: #1623 G2 (gated), #1624 G3, #1626 G4 (gated), #1627 G5, #1628 G6.
- **5 follow-up / tech-debt issues open**: #1601, #1604, #1607, #1612 (P2 nits from prior sessions); **#1634 NEW** (track seed `cannot_be_salvaged` residuals — 3-of-3 R1s flagged this in session 64).
- **#373 Phase 1 livenessprobe primitives shipped** (carried). Phase 2 + Phase 3 still future.
- **#386 lab audit refreshed** (`docs/lab-audit-2026-05-26.md`, 269 labs scored, avg 2.25/5) — baseline for when #386 unlocks post-content-gaps.
- Site: https://kube-dojo.github.io/ (Starlight/Astro, ~1,350 pages, ~30-40s build).
- Services: `./services.sh {start|stop|restart|status} {dev|api|feedback}` (api on :8768, dev on :4333).

## TODO

**Next session — top priorities (orchestrator-recommended sequence per session 65 handoff):**

- [ ] **Lane A continuation — FinOps 1.2-1.6 citation backfill cohort** (5 modules, same pipeline as session 64 cohort). Highest per-PR impact on critical-rubric drain. **User-picked for next session (session 66 close).** Recommend doing FIRST before any G3-G6 dispatch.
- [ ] **Propagate PR #1629 hook fix back to `agents_extensions/` source** — direction-corrected at session 66 close: HEAD's `.claude/hooks/inject-codex-danger-mode.sh` has the safe `|| true` + comment (added by PR #1629), but `agents_extensions/claude/hooks/inject-codex-danger-mode.sh` source is STILL the unsafe pre-#1629 version. Any future `deploy.sh --target claude` run will silently regress the fix. Small PR: copy the safe block from `.claude/` back to source, verify `deploy.sh` is now a no-op. Stash@{0} on session 66 captures the recurring drift if reproduction is needed.
- [ ] **Trim MEMORY.md** (207 lines, past 200 truncate limit). Session 66 added `feedback_git_C_over_cd_for_worktree_ops`. Hook flagged at every cold start; lines past 200 are invisible to future agent context.
- [ ] **Lane A continuation — remaining critical modules** (109 → after FinOps cohort, focus on other Platform Disciplines + Toolkits + Foundations modules with "no citations" primary issue).
- [ ] **#1634 NEW — decide approach for seed `cannot_be_salvaged` residuals** — 3 proposed: (a) re-enable inject `soften_to_illustration` rewrites, (b) per-module follow-up PRs, (c) accept-and-document. Worth a Decision Card.
- [ ] **Dispatch G3 codex T0 writer** (#1624 distributed-systems mental models, 2-3 practice-lab modules). Single dispatch.
- [ ] **Dispatch G5 codex T0 writer** (#1627 cross-cloud workload identity rosetta, 1 module). After G3.
- [ ] **Dispatch G6 codex T0 writer** (#1628 OTEL Collector at production scale, 1-2 modules). After G5.
- [ ] **G2 (#1623) Stage-1 brief only** — software engineering craft. Blocked until Platform Foundations critical < 20 (currently 28). Issue stays open.
- [ ] **G4 (#1626) LLM golden path** — gated on existing modules 9.4, 1.5, 3.1 having rubric ≥3. Run prerequisite check before dispatching.
- [ ] **Tech debt — citation_backfill REPO_ROOT pinning**: script writes to PRIMARY repo dir regardless of `cd`. Either (a) refactor to take a `--repo-root` arg, or (b) document the "run worktree-local script copy" pattern. Session 64 finding.
- [ ] **Tech debt — inject step `rewrites_disabled_pending_redesign`**: this is the root cause of #1634. Worth a design pass.
- [ ] **Codex T0 author hangs post-write** — session 63 finding on G1. Still unexplained; needs reproduction on next T0 dispatch.
- [ ] **Block-branch-create hook missed primary-dir checkout** — session 63 finding (`HEAD@{1}: checkout: moving from main to build/g1-nats-jetstream`). Reproduce + fix.
- [ ] **#1620 dispatch_smart cwd default for codex review** — small follow-up to land #1586 fix end-to-end.
- [ ] **#1614 Lane C cursor-app-control MCP + Cursor SDK eval** — environment-steering integration; out-of-scope for PR #1613 (Lane A only).
- [ ] **#1609 author real Neural Network Fundamentals module** — T0 codex dispatch for new module at deep-learning/1.1.5. ~5000-7000 words.
- [ ] **#1504 backfill cadence** — 0 reviews sessions 60/61/62. Resume 3-5 per session.
- [ ] **Wire agy as third agent in `scripts/citation_backfill.py`** — fallback when gemini-cli OAuth hangs.
- [ ] **#1350 agy migration (21 days to 2026-06-18 deadline)** — 30+ gemini-cli touchpoints. Surface early next session.
- [ ] **#393 AI/ML history depth pass** (unblocked since #388 closed 2026-05-12).
- [ ] **#1587 density follow-up for #1577 modules**.
- [ ] **#373 Phase 2 + Phase 3** — defer until content work clears.
- [ ] **Codex spark default broken** for our prompt sizes. Patch `scripts/dispatch_smart.py` draft task class to default to `gpt-5.5`.
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

- **Quality-floor gate is OPEN across the entire curriculum**. Verified 2026-05-28: Platform Disciplines 45, Platform Toolkits 36, Platform Foundations 28 — all under 50 critical. Cert tracks at 0. Gap-fill writes unblocked everywhere. (Non-blocker — kept for visibility.)
- **Codex T0 author post-write hang** (G1 PR #1630 session 63). Codex wrote 5157 words, then froze before commit. Orchestrator did the inline close-out. Cause still unexplained; if reproducible on future T0 dispatches, codex CLI may have a stuck post-write phase under `--mode danger`. Worth tracing on next codex T0 dispatch.
- **#1605 + #1621 RESOLVED** session 64 — was overnight OpenAI outage, not a code bug. Citation backfill pipeline confirmed healthy on 3-of-3 retries.

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
- 2026-05-26 → 27 session 59: **Autonomous overnight** (user AFK ~22:14 to handoff). **4 citation-backfill PRs merged** (#1597 2.4, #1599 8.1, #1600 8.2, #1603 4.1 with R1 inline URL fix) + 1 left OPEN (#1606 4.2-ceph-rook NEEDS_CHANGES → #1607). **3 #1504 composer-2.5 back-catalog reviews** filed on issue (mlops/1.9 → #1598 1 P0+9 P1; cnpa/1.3 APPROVE_WITH_NITS clean; vault-eso/4.1 → #1602 4 P1 security-critical). Sample rate 2/3 Class A — consistent with prior n=15 80%-Class-A finding. **Bug discovered**: codex citation_backfill hangs reproducibly on 8.3-cloud-repatriation (#1605); same wrapper succeeds on 4 sibling modules. **Pipeline data**: codex consistently 3-5min/module on 381-856 line modules; gemini 900s-timeout on citation_backfill (not viable); composer-2.5 R1 150-300s/PR; cursor R1 caught 2 real NEEDS_CHANGES (VGS contradiction, uncited Paxos/Raft). 6 issues filed total (#1598, #1601, #1602, #1604, #1605, #1607).
- 2026-05-27 session 60: **Fix-pass storm — 4 PRs merged, #1577 epic CLOSED, production hash() bug killed.** PR #1606 (4.2-ceph-rook fix-pass + CI dedup-gate xrefs), PR #1608 (#1577 final rename — user picked Option A), PR #1610 (mlops/1.9 hash() salted-per-process bug → hashlib.sha256 + 9 P1 + Zillow nit), PR #1611 (vault-eso/4.1 4 security defects: secret/data path × 8, VaultDynamicSecret rotation, Vault 1.21+ audiences, Q3 fix). 3 issues CLOSED (#1577, #1598, #1602). 3 new follow-ups filed (#1609 real NN module to author, #1612 vault P2 nits) + 1 user-correction memory locked TOP PRIORITY (`feedback_gemini_cli_timeout_route_to_agy` — when gemini-cli hangs/fails autonomous, route to agy BEFORE codex). Decision Card C symmetric routing validated end-to-end on 3 fix-pass cycles (codex 60-80s per fix-pass when brief includes precise R1 line refs). Critical-rubric drain unchanged (focus was closeout, not new drain). 4 P2 follow-ups now pending (#1601, #1604, #1607, #1612) — recurring pattern worth a sweep next session.

## End-of-session ritual

1. Write today's full handoff to `docs/session-state/YYYY-MM-DD-<topic>.html`.
2. Add a row at top of **Latest handoff** with 1-line summary + link. Shift the third row off to the `docs/session-state/` directory pointer (don't accumulate >3 rows here).
3. Update **TODO** + **Blockers** (briefing API depends on these headings).
4. Commit with `docs(status): handoff <date> — <topic>` style.

---
**Maintenance rule**: this file is the index. Detail goes in the dated handoff HTMLs. Keep STATUS.md ≤100 lines.
