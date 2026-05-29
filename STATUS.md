# Session Status — index

> Index, not log. Per-session handoffs in [`docs/session-state/`](./docs/session-state/) — this file points at them.
> Briefing API parses `## TODO` and `## Blockers` (keep those headings populated).
> Older sessions (pre-2026-05-24) live in [`docs/session-state/archive-pre-2026-05-24.md`](./docs/session-state/archive-pre-2026-05-24.md) plus the dated `.html` files alongside.

## Cold-start protocol

1. **Issue-driven**: `KUBEDOJO_ISSUE=N bash scripts/cold-start.sh` after reading the issue verbatim.
   **Standalone**: `bash scripts/cold-start.sh` (add `--manifest` for route discovery).
   The script does services-up, `git status`, pending decisions, briefing, orient, handoff pointer. Exit 0 with `STATUS.md` fallback on API failure.
2. Scan [`docs/decisions/pending/`](./docs/decisions/pending/) before unrelated work (also surfaced by the script). **Approved decisions live in [`docs/decisions/`](./docs/decisions/)** — `2026-05-29-1639-ai-engineering-consolidation.md` is now fully executed (§1–4, session 70); nothing pending awaiting execution.
3. Read **Latest handoff** below only if briefing/orient leave a narrative gap.

## Latest handoff

| Date | Session | Summary | Handoff |
|------|---------|---------|---------|
| 2026-05-29 | **70** | **#1639 Option B §4 COMPLETE — 3 PRs merged; structural consolidation done.** Clean cold-start (synced origin first per the new memory). Verified the title/content scramble against ref-counts, then fanned out: **#1649** retired 3 moved-stubs w/ astro `redirects` (orchestrator inline); **#1650** moved the mis-filed LangGraph course into `1.3-langgraph` + ported unique ReAct into foundations `1.2` (stays T0); **#1651** authored the genuinely-missing **LlamaIndex** `1.4` module (T0 PASS, 5292w, v0.10+ API). Both content PRs codex→composer-2.5 R1 (Decision Card C). **Caught + fixed a regression** (codex over-added a 9th mistakes row + 9th quiz to 1.2, breaking the 6-8 caps) and **2 real LangGraph runnability bugs** + a placeholder ROI table (R1 findings). **codex "post-write hang" diagnosed** = edit-class 1800s timeout SIGKILL after-edit-before-commit → recovered from worktree (memory `feedback_codex_sigkill_at_timeout_recover_from_worktree`; use `draft`/`--timeout 3600` for big edits). **Residuals → audit**: 1.3 carries pre-existing T3 density (the move didn't regress it); context-eng gap-check. #1639 left OPEN. | [session-70](./docs/session-state/2026-05-29-session-70-1639-option-b-section-4-complete.html) |
| 2026-05-29 | **69** | **#1639 Option B Steps 1–3 executed + carried tech-debt cleared — 6 PRs merged/merging, autonomous parallel run.** Continued session 68's approved Option B in a fresh session. ⚠️ Cold-start read **stale local main** (showed session 67) → I re-ran the already-done #1639 audit + re-burned 2 codex-danger dispatches until a mid-session `git pull` surfaced the approved brief (memory `feedback_cold_start_sync_origin_main`). Shipped: **#1642** added the `ai-engineering-foundations` spine to the AI sidebar (it was in NO sidebar — the real "burial"); **#1643** briefing no longer leads with critical-rubric (verified live: `actions.next` empty, `critical_quality` field intact); **#1644** + **#1646** the full neighbor→spine cross-link map + `ai/index.md` 6-section/37-module update + **2 stale-link bug fixes**; **#1645** #1629 hook propagated to `agents_extensions/` source + ADR addendum. #1626 re-scoped to teaching-content. MEMORY.md trimmed 211→197. **Remaining = Option B §4 only** (stub retirement w/ redirects + frameworks 1.3/1.4 LangGraph move + author LlamaIndex). | [session-69](./docs/session-state/2026-05-29-session-69-1639-option-b-execution.html) |
| 2026-05-29 | **68** | **G3 gap-fill merged (both dist-systems modules) + #1639 consolidation plan approved (Option B).** User directive: "have the missing modules built before we start improving them." Trimmed dist-systems **5.4 (#1638)** + **5.5 (#1637)** from over-built runnable kind labs to teaching content (theory + light exercise, sibling 5.2/5.3 pattern) — both MERGED. codex R1 caught 5.5 teaching Lamport-as-dedup (real error) → fixed. Re-scoped gap tickets **#1627 (G5 workload identity)** + **#1628 (G6 OTel)** to teaching-content-only (lab specs parked for #386). For **#1639**: codex audit + orchestrator verification reframed the problem — the prompt/context/harness content is ALREADY consolidated into `ai-engineering-foundations`; the real burial is that section is missing from the AI sidebar (`astro.config.mjs`). Also found a title/content scramble in `frameworks-agents` (1.3-langgraph teaches reasoning basics; 1.4-llamaindex teaches LangGraph; LlamaIndex uncovered). User approved **Option B (full consolidation)**, folded in the 1.4 fix ("one swoop, no separate ticket"), and asked to execute in a FRESH session that picks up a new Claude Code CLI bugfix first. Zero Claude sub-agents this session (all cursor/codex). | [session-68](./docs/session-state/2026-05-29-session-68-g3-gap-fill-merged-plus-1639-consolidation-plan.html) |

Older predecessors: see [`docs/session-state/`](./docs/session-state/) (66 dated handoff files, sessions 13-69; session 67 = Opus 4.8 migration + gap-scope correction; session 66 = SessionStart hook; sessions 63-65 = autonomous gap-fill wave + citation-backfill cohort + standing-decisions discussion).

## Active policies

- **#1639 Option B — §1–4 ALL DONE (session 70)**. Brief = [`docs/decisions/2026-05-29-1639-ai-engineering-consolidation.md`](./docs/decisions/2026-05-29-1639-ai-engineering-consolidation.md). ✅ §1–3 (s69: #1642/#1644/#1646) + §4 (s70: #1649 stub retirement+redirects, #1650 frameworks 1.3/1.4 scramble + ReAct→foundations-1.2, #1651 net-new LlamaIndex 1.4). Issue left **OPEN** (per no-premature-close): residuals fold into the audit — (1) `1.3-langgraph` carries pre-existing T3 density (move didn't regress it; T0 upgrade = a `draft`-class dispatch), (2) goal-item-4 context-engineering gap-check.
- **One swoop, not separate tickets (locked 2026-05-29, session 68)**: fold related fixes into the current effort rather than spawning separate tickets. User: "i really dont like this bureaucratic way of handling problems. it is more effective to do them in one swoop." Memory: `feedback_one_swoop_not_separate_tickets`. (Discipline ≠ bureaucracy — epics still stay open until QG'd per below.)
- **Gap-fill = teaching content, labs separate (locked session 67, reaffirmed session 68)**: theory + a LIGHT conceptual `## Hands-On Exercise` (sibling pattern). Full runnable kind labs → labs project #386. Re-scope any "practice labs" ticket BEFORE dispatching. Memory: `feedback_gap_fill_is_teaching_content_not_labs`.
- **Gap-fill phase 1-5 of #1299 is NOT blocked by critical-count <50 (locked 2026-05-28, session 62)**: only step 6 (codex writes new modules) is gated. Reviewer dispatches + synthesis + issue filing run any time.
- **Oldest-first triage; Ukrainian + #386 deferred (locked 2026-05-26, session 58)**: oldest-first; UK epics (#143, #383) defer until EN production-ready; #386 lab work defers until gaps filled + content written.
- **Content-fix briefs MUST mandate `## Learner check` blockquote (session 58)**: hook `block-content-merge-without-learner-check.sh` blocks merge without a ≥30-char verbatim quote from a touched module. Use `gh pr edit --body-file`. Memory: `feedback_content_fix_brief_includes_learner_check`.
- **Class A fix briefs MUST mandate sibling-grep (session 58)**: issue listings are sampled. Grep the full file for the anti-pattern, fix all occurrences in one commit. Memory: `feedback_class_a_fix_includes_sibling_grep`.
- **Commit subjects avoid `fix/closes/resolves #N` for epics that must stay open (session 58)**: PR-body `Refs` does NOT override the subject auto-close. Memory: `feedback_commit_subject_avoid_fix_n_pattern`.
- **`chore(` not `fix(` for content/typo/link PRs**: `fix(` triggers the bugfix-merge hook requiring a `Regression test:` line. Memory: `feedback_chore_vs_fix_prefix_for_bugfix_hook`.
- **Back-catalog needs full composer-2.5 review (Decision Card C reinstated, session 57)**: n=15 sample = 80% NEEDS_CHANGES Class A across all strata. #1504 full backfill stands. Do NOT repropose "skip review for high-rubric modules." [`docs/decisions/2026-05-26-tiered-back-catalog-review-policy.md`](./docs/decisions/2026-05-26-tiered-back-catalog-review-policy.md).
- **Decision Card C (2026-05-24)**: composer-2.5 = primary cross-family T0 reviewer; codex = secondary. Symmetric: composer-2.5-authored → codex reviews; everyone-else-authored → composer-2.5. [`docs/decisions/2026-05-24-reviewer-routing-composer-2-5.md`](./docs/decisions/2026-05-24-reviewer-routing-composer-2-5.md).
- **codex review dispatch**: codex ALWAYS runs danger mode — do NOT pass `--mode`, DO pass `--worktree` (cwd is mandatory for danger). Session 68 burned 2 dispatches learning this. composer-2.5/gemini reviews take `--mode read-only` fine.
- **T0 author rotation**: codex gpt-5.5 primary (cap healthy) → cursor auto-model / composer-2.5 / deepseek-v4-pro / gemini-3.1-pro-preview on throttle. Cursor reviewer needs explicit `--model composer-2.5`. Memory: `feedback_codex_writer_composer_reviewer_pair`, `feedback_gemini_3_1_pro_viable_t0_author`.
- **Core H2 section cap RELAXED to 7 (session 65)**: was MAX 6; agents produced 7 anyway. Stop fighting the natural shape.
- **agy unsafe for clean-branch T0 authoring (session 56)**: TUI persists branch state. OK for review/architect/edit-on-existing-branch. Memory: `feedback_agy_tui_session_bleed_t0_author`.
- **No China APIs from GH Actions (session 57)**: `api.deepseek.com` from runners → repo-level 403. CI cross-family review is gemini-3.1-pro-only. Local deepseek dispatches fine. Memory: `feedback_no_china_apis_from_gh_actions`.
- **agents_extensions/ is source-of-truth (PR #1575)**; `deploy.sh --target claude|...` materializes to `.claude/`. Dispatch-time skill auto-load: draft/edit→curriculum-writer, review→cross-family-reviewer.
- **No premature issue close (session 54)**: epics stay open until every AC box is QG'd. Memory: `feedback_no_premature_issue_close`.
- **Autocompact disabled (2026-05-25)**: durable handoff via `docs/session-state/*.html` + STATUS.md. Statusline bold-red at 500K = handoff trigger.
- **No separate dispatch watchers**: the `run_in_background` exit notification IS the signal. Read `logs/dispatch_responses/<task-id>.txt`.
- **HTML-first artifacts**: handoffs/audits/briefs default `.html`; STATUS.md / CLAUDE.md / `.claude/rules/` / memory / decision-cards stay `.md`.

## Current state

- **806 English modules** (+2 session 68: dist-systems 5.4 + 5.5); **312 Ukrainian** (~40%, deferred until EN production-ready).
- **Starter tracks 499/499 at heuristic 5.0** (unchanged).
- **109 critical-rubric modules remain** (unchanged session 68 — focus was gaps, not drain). Average rubric ~4.52. ~106 are "no citations" — `citation_backfill` pipeline confirmed working.
- **~274 modules need composer-2.5 review** (#1504 epic). Backfill cadence 0 sessions 60-68 (focus elsewhere); resume 3-5/session.
- **Gap-fill (#1299) status**: G1 NATS shipped (session 63); **G3 dist-systems 5.4+5.5 MERGED (session 68)**; G5 #1627 + G6 #1628 re-scoped to teaching content, ready to dispatch; G4 #1626 + G2 #1623 gated (see TODO). #1624 (G3) stays open (covers 2-3 lessons).
- **#1639 Option B fully executed** (§1–4, session 70). 3 stub modules retired (redirected); `frameworks-agents/1.3` now real LangGraph, `1.4` now real LlamaIndex (T0); foundations `1.2` gained a ReAct section. Net module-file count −3 (inert stubs). Issue OPEN for 2 audit-residuals.
- **Follow-up / tech-debt issues open**: #1601, #1604, #1607, #1612 (P2 nits); #1634 (seed `cannot_be_salvaged` residuals).
- **#386 lab audit** baseline `docs/lab-audit-2026-05-26.md` (269 labs, avg 2.25/5) — for when #386 unlocks.
- Site: https://kube-dojo.github.io/ (Starlight/Astro, ~1,350 pages, ~30-40s build). Services: `./services.sh {start|stop|restart|status} {dev|api|feedback}` (api :8768, dev :4333).

## TODO

**Next session:**

- [x] ~~Finish #1639 Option B §4~~ — DONE session 70 (#1649 stubs+redirects, #1650 frameworks scramble + ReAct port, #1651 LlamaIndex). All merged, gates green. #1639 OPEN for the 2 audit-residuals below.
- [ ] **More serious curriculum audit (user 2026-05-29 "we need to do a more serious audit after these") — NOW THE TOP NEXT-WORK.** The frameworks-agents 1.3/1.4 title/content scramble was found by accident, so a systematic pass is warranted: hunt mislabeled modules (title vs body), scattered/duplicate teaching content, dead/moved-page stubs not wired to redirects, broken/dangling internal links, and orphaned-from-nav sections. Start with the AI tracks (where the scramble surfaced), then widen. Scope it as its own audit phase with a written report. **Fold in the 2 #1639 residuals: (1) bring `frameworks-agents/1.3-langgraph` to T0 (it's T3 — 1520 prose words, 2 sources, section order, DYK→4 — a single `draft`-class codex dispatch); (2) confirm context-engineering coverage in foundations 2.1–2.4 (#1639 goal item 4).**
- [ ] **Dispatch G5 #1627 + G6 #1628** — already re-scoped to teaching content; codex author → composer-2.5 R1; keep codex ≤2 concurrent.
- [ ] **G4 #1626** gated on modules 9.4/1.5/3.1 rubric ≥3 (run prereq check). **G2 #1623** gated until Platform Foundations critical < 20 (currently 28).
- [x] ~~Fix briefing priority logic~~ — DONE session 69 (#1643): `critical_quality` no longer injected into `actions.next`; verified live (`actions.next` empty, dedicated field intact).

**Carried tech-debt (not content):**

- [x] ~~Propagate PR #1629 hook fix to `agents_extensions/` source~~ — DONE session 69 (#1645); source==deployed, `deploy.sh` no-op verified.
- [x] ~~Trim MEMORY.md~~ — DONE session 69 (211→197 lines; closed AI-history book cluster consolidated into `project_ai_history_book_closed`).
- [ ] **citation_backfill REPO_ROOT pinning** — writes to PRIMARY repo dir regardless of `cd`; add `--repo-root` arg or document the worktree-local copy pattern.
- [ ] **inject step `rewrites_disabled_pending_redesign`** — root cause of #1634; design pass.
- [ ] **Investigate headless-claude "Prompt is too long" (user-requested 2026-05-29)** — `dispatch_smart edit --agent claude` fails instantly; the headless `npx claude-code` loads every connected MCP server's tool schemas and overflows. Lead: the adapter (`scripts/agent_runtime/adapters/claude.py:169-172,181`) already supports `--mcp-config`/`--allowedTools`/`--exclude-dynamic-system-prompt-sections`, but `dispatch_smart.py` doesn't pass them for write classes. Fix: pass a minimal `.mcp.json` + tight `--allowedTools` (and/or always `--exclude-dynamic-system-prompt-sections`) for `--agent claude`. Repro + full notes in memory `feedback_claude_headless_mcp_prompt_bloat`.
- [ ] **#1620** dispatch_smart cwd default for codex review · **#1609** author real Neural Network Fundamentals module · **#1504** backfill cadence (resume 3-5/session) · **#1350** agy migration (deadline 2026-06-18) · **#393** AI/ML history depth pass · **#373** Phase 2/3 (defer until content clears).

**Date-bound:**

- 2026-06-08: claude-i wrapper pilot · 2026-06-15: agentic-credit-pool flip (claude-throttle expires) · 2026-06-18: drop gemini-cli adapter (#1350) · 2026-07-13: weekly-double bump expires.

**Deferred per user (session 58):** #143 / #383 Ukrainian — until EN production-ready; #386 lab audit + expansion — until gaps filled + content written.

**Long-running epics:** #197 On-Premises expansion · #14 monitoring · #1401/#1402/#1404/#1413/#1416/#1502 calibration.

## Blockers

- **Quality-floor gate OPEN across the curriculum** (verified 2026-05-28: Platform Disciplines 45, Toolkits 36, Foundations 28 critical; cert tracks 0). Gap-fill writes unblocked everywhere. (Non-blocker — visibility.)
- **Codex "post-write hang" DIAGNOSED (session 70)**: it's the **edit-class 1800s timeout SIGKILLing (rc=-9)** a big gpt-5.5 multi-file edit after-edit-before-commit, not a freeze. The §4(b/c) edit hit it; the §4(d) `draft`-class (3600s) dispatch committed fine. **Mitigation**: use `draft` class or `--timeout 3600` for large edits; recover any killed dispatch's work from the worktree (verify complete, commit yourself). Memory: `feedback_codex_sigkill_at_timeout_recover_from_worktree`.

## Key decisions / facts

- Starlight (Astro) replaces MkDocs Material; defaultLocale `root` (English at `/`, Ukrainian at `/uk/`). `scripts/dispatch_smart.py` is the canonical task-class dispatcher.
- GH Actions SHA-pinned, requirements hash-locked, Dependabot enabled, branch protection on `main` (required checks, no force push). Note: force-pushing a rebased content branch re-triggers required checks → use `gh pr merge --auto`.
- 2026-04-28: STATUS.md migrated to index pattern. 2026-05-24: re-compressed; sessions 13-51 narrative → `docs/session-state/` HTMLs.
- 2026-05-26 session 56: Epic #1530 AI Engineering Foundations closed; critical-rubric drain begun; CI cross-family review functional.
- 2026-05-26 session 57: Decision Card B′ aborted (n=15 → 80% Class A) → Option A / Card C / #1504 full backfill. `claude_extensions/`→`agents_extensions/` rename; dispatch-time skill auto-loading.
- 2026-05-26 → 27 sessions 58-60: 12 #1577 Class A PRs + fix-pass storm merged; #1577 epic CLOSED; production hash()-salting bug killed; `feedback_gemini_cli_timeout_route_to_agy` locked.
- 2026-05-28 sessions 63-64: autonomous gap-fill wave (G1 NATS shipped, 6 gap issues filed under #1299) + citation-backfill cohort (#1631/#1632/#1633) merged after OpenAI outage healed.
- 2026-05-28 session 67: Opus 4.8 migration shipped (PR #1636) — model sweep 4-7→4-8, `effortLevel: xhigh`, skill briefs tuned. Detail in session-67 handoff.

## End-of-session ritual

1. Write today's full handoff to `docs/session-state/YYYY-MM-DD-<topic>.html`.
2. Add a row at top of **Latest handoff** (1-line summary + link). Keep ≤3 rows here; shift older rows to the `docs/session-state/` pointer.
3. Update **TODO** + **Blockers** (briefing API depends on these headings).
4. Commit with `docs(status): handoff <date> — <topic>` style.

---
**Maintenance rule**: this file is the index. Detail goes in the dated handoff HTMLs. Keep STATUS.md lean.
