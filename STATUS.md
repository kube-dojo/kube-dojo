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
| 2026-05-28 | **62** | **Gap-analysis pivot after user course-correction.** Session 61 missed the standing gap-fill-first directive (ran a P2 sweep + UI bridge instead). User course-corrected on wake-up and added cursor to the gap-analysis reviewer pool. Dispatched cursor (composer-2.5) + cursor (auto-model) + codex against the same 2026-05-17 brief; cursor reports landed in 1-2 min each (26 KB + 27 KB), codex still in flight at handoff. **Key finding (verified live via API)**: all 3 Platform tracks now sit under 50 critical (Disciplines 45, Toolkits 36, Foundations 28). The quality-floor gate that has blocked gap-fill drafting since the May plan is now open everywhere. All cert tracks (CKA/CKAD/CKS/KCNA/KCSA) at 0 critical. Both cursor reports converge: top move is Platform critical-rubric burndown (especially FinOps 1.1-1.6) before any new breadth wave; only Tier-1 content gap remaining is 1 NATS JetStream-on-K8s operator module. 7 lower-confidence net-new gaps from cursor-auto (Gateway API ops, Wasm/WASI lab, SLSA L3 lab, Prefect + 3 others) need cross-checking against deepseek + codex before issue-filing. | [session-62](./docs/session-state/2026-05-28-session-62-gap-analysis-pivot-cursor-reports.html) |
| 2026-05-27 | 61 | **UI bridge shipped + P2 sweep (Learner-check defect caught + corrected).** PR #1613 merged — Lane A UI bridge (`ab send-codex-ui` / `ab send-cursor-ui` / `ab send-agy-ui`); cross-family R1 by ghim (in-IDE Cursor Auto-mode agent). Negative-result verified: bridge reaches Cursor's agent-transcripts surface (agent-to-agent works, ghim grepped it) but does NOT drive visible IDE Composer pane (separate cloud-backed store). 4 P2 PRs merged (#1615/#1616/#1617/#1619) — all 3 first-attempt PRs needed fix-pass for same systematic Learner-check brief defect (placed in module body instead of PR body, corrupted Sources list on PR #1616). PR #1618 (dispatch_smart bug #1586) merged with R1/R2 ping-pong — composer-2.5 caught codex runtime regression in first fix attempt; codex landed correct architectural split in fix-pass. citation_backfill research for module-4.4-object-storage-bare-metal running in flight at handoff (10+ min — first critical-rubric drain candidate of the session). 2 new issues filed (#1614 Lane C cursor-app-control MCP + Cursor SDK eval, #1620 codex cwd default follow-up to #1618). 2 memories updated (`reference_cursor_ui_bridge_primitives` NEW + `feedback_content_fix_brief_includes_learner_check` tightened with explicit "NEVER in the module" warning). Stuck cursor R1 of #1615 abandoned at ~85min 0-byte — likely OAuth-burst silent hang; codex R1 of #1617 caught equivalent issue so no signal lost. | [session-61](./docs/session-state/2026-05-27-session-61-ui-bridge-shipped-plus-p2-sweep.html) |
| 2026-05-27 | 60 | **Fix-pass storm — 4 PRs merged, #1577 epic CLOSED, production hash() bug killed.** PR #1606 (4.2-ceph-rook citation backfill — R1 fix-pass + CI dedup-gate xrefs), PR #1608 (#1577 final rename neural→numpy → #1577 epic closed), PR #1610 (mlops/1.9 hash() salted-per-process bug taught as A/B-testing best practice — now hashlib.sha256), PR #1611 (vault-eso 4 P1 security defects: ESO secret/data path × 8, VaultDynamicSecret rotation, Vault 1.21+ audiences, Q3 fix). 3 issues CLOSED (#1577, #1598, #1602). 3 new follow-up issues filed (#1609 real NN module to author, #1612 vault P2 nits) + 1 user-correction memory locked TOP PRIORITY (`feedback_gemini_cli_timeout_route_to_agy` — when gemini-cli hangs/fails autonomous, route to agy BEFORE codex; session 59 miss). Decision Card C symmetric routing validated end-to-end on 3 fix-pass cycles. Critical-rubric drain unchanged at 113. 4 P2 follow-ups now pending (#1601, #1604, #1607, #1612). | [session-60](./docs/session-state/2026-05-27-session-60-fix-pass-storm-and-1577-close.html) |
| 2026-05-26 → 27 | 59 | Autonomous overnight (user AFK 22:14). **4 citation-backfill PRs merged** + 1 left open: #1597 (2.4-declarative-bare-metal 16 inline citations), #1599 (8.1-multi-site-dr 8), #1600 (8.2-hybrid-connectivity 17), #1603 (4.1-storage-architecture 20 — R1 NEEDS_CHANGES → orchestrator inline VGS URL swap → merged), #1606 OPEN (4.2-ceph-rook 20 inline — R1 NEEDS_CHANGES → resolved session 60). **3 #1504 back-catalog reviews** filed: mlops/1.9 (NEEDS_CHANGES 1 P0 + 9 P1 → #1598), k8s/cnpa/1.3 (APPROVE_WITH_NITS), platform/.../vault-eso/4.1 (NEEDS_CHANGES 4 P1 security-critical → #1602). **6 issues filed**: #1598, #1601, #1602, #1604, #1605, #1607. **Bug discovered**: codex citation_backfill hangs reproducibly on on-premises/8.3-cloud-repatriation (#1605). Gemini citation_backfill not viable (timeout 900s); codex consistently 3-5 min per module. Composer-2.5 R1 caught 2 real NEEDS_CHANGES (VGS contradiction, uncited Paxos/Raft). | [session-59](./docs/session-state/2026-05-26-session-59-autonomous-overnight-citation-drain.html) |
| 2026-05-26 | 58 | Class A drain (11 of 12) + #373 Phase 1. **12 PRs merged**: #1583 (gitpod 4 A), #1584 (cloudwatch 3 A + 2 fix-passes), #1585 (network-admin 3 A + 2 sibling fixes), #1588 (#373 Phase 1 livenessprobe primitives), #1589 (0.9-software 3 A), #1590 (1.2-ebpf-deepdive 2 A), #1591 (5.3-memory-management 7 A — sibling-grep caught 5 extras), #1592 (kcsa-5.3-runtime-security 1 A + image-runnability fix), #1593 (7.4-observability 1 A), #1594 (12.1-sonarqube 2 A — codex re-fired after gemini quota crash), #1595 (5.4-fleet-management 2 A), #1596 (10-gitops-bridge 2 A). 2 issues filed (#1586 dispatch_smart codex-review --worktree bug, #1587 density follow-up). User course-corrections drove triage: oldest-first / skip Ukrainian / defer #386 until content done. 3 new memories (learner-check brief mandate, sibling-grep brief mandate, commit-subject avoid-fix-N pattern). Gemini-3.1-pro-preview hit terminal quota mid-session — 22h reset. Only `neural-network-fundamentals` remains from #1577 (scope mismatch, not a fix-pass). | [session-58](./docs/session-state/2026-05-26-session-58-class-a-drain-plus-373-phase1.html) |

Older predecessors: see [`docs/session-state/`](./docs/session-state/) (57 dated handoff files, sessions 13-59).

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
- **113 critical-rubric REWRITES remain** at <2.0 rubric (unchanged session 60 — focused on fix-pass closeout instead of new drain. Module 4.2 finished merging this session. Module 8.3 blocked on codex hang bug #1605).
- **274 modules still need composer-2.5 review** (#1504 epic full backfill). Session 60 cadence: **0 reviews** (paced down to close fix-pass debt).
- **#1577 Class A epic CLOSED** session 60 — all 12 modules resolved (11 fix-passes session 58 + final rename PR #1608 session 60). Follow-up #1609 tracks authoring a real Neural Network Fundamentals module from scratch.
- **#1598 mlops/1.9 hash() production-breaking bug FIXED on live site** (PR #1610) — module no longer teaches a salted-per-process A/B-routing pattern.
- **#1602 vault-eso 4 security defects FIXED on live site** (PR #1611) — ESO secret/data path + VaultDynamicSecret rotation + Vault 1.21+ audiences + Q3 corrected.
- **4 P2 follow-ups pending**: #1601 (8.2-hybrid wrong-page anchors), #1604 (4.1-storage docs.ceph.com), #1607 (4.2-ceph carry-forward), #1612 (vault-eso YAML indent + resultType). All non-blocking. Consider a P2 sweep next session.
- **#373 Phase 1 livenessprobe primitives shipped** (carried). Phase 2 + Phase 3 still future.
- **#386 lab audit refreshed** (`docs/lab-audit-2026-05-26.md`, 269 labs scored, avg 2.25/5) — baseline for when #386 unlocks post-content-gaps.
- Site: https://kube-dojo.github.io/ (Starlight/Astro, ~1,350 pages, ~30-40s build).
- Services: `./services.sh {start|stop|restart|status} {dev|api|feedback}` (api on :8768, dev on :4333).

## TODO

**Next session — top priorities (autonomous session 63 in progress; synthesis landed):**

- [ ] **Gap-plan synthesis written** at `docs/research/gap-plan-2026-05-28.html` (session 63). 6 convergent gap-fill picks (G1-G6) ready to file as issues. Codex 4th opinion skipped (cursor twin-convergence sufficient; sanity-check re-fire optional).
- [ ] **File per-track gap-fill issues G1-G6** under #1299, label `gap-fill-2026-05-28`. (in flight session 63)
- [ ] **Dispatch G1 NATS JetStream codex writer first** — smallest scope, validates new pipeline. Then fan out G3/G5/G6 capped at 3 concurrent.
- [ ] **Platform critical-rubric burndown in parallel** — FinOps 1.1-1.6 highest-leverage. Gated on #1605/#1621 root-cause.
- [ ] **Investigate #1621 + #1605 (codex citation_backfill failures)** — diagnostic in flight session 63.
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

- **#1621 + #1605 — codex citation_backfill module-specific failures** block critical-rubric drain on at least 2 known modules (4.4-object-storage-bare-metal returns agent_response_invalid; 8.3-cloud-repatriation hangs at 0 bytes). Drain can continue on other modules (4.5, finops 1.1-1.6) but each new module is a coin-flip until the root cause is found.
- **Quality-floor gate is now OPEN across the entire curriculum** (was blocking gap-fill drafting until session 61). Verified live 2026-05-28: Platform Disciplines 45, Platform Toolkits 36, Platform Foundations 28 — all under 50 critical. Cert tracks at 0 critical. Gap-fill writes are unblocked everywhere. (This is a non-blocker — moved here so the next session sees it explicitly.)

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
