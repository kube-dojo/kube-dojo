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
| 2026-05-25 | **55** | 15-PR flood. CI cross-family review workflow shipped + operational on every subsequent PR (#1542). Hermes argv bug class fully eradicated across 4 PRs (#1543/#1547/#1549) — 5 call-sites switched to `--oneshot=<prompt>` equals-form, regression tests for all incl. flag-like-prompt edge case. 5 issues closed: #1517 #1518 #1520 #1523 #1538. #1530 Wave 2 author phase complete: all 4 PRs (#1552 #1553 #1554 #1556) merged (1554 auto-queued for CI). Cross-family review chain caught 6 real bugs (CI timeout · Calico v3 IPPool schema · BCC missing include · kind lab not kube-proxy-free · Shopify/Datadog citation breaks · Tetragon SIGKILL caveat). Wave 3.1 codex T0 in-flight at handoff write. | [session-55](./docs/session-state/2026-05-25-session-55-fifteen-pr-flood-wave-2-complete-plus-hermes-eradication.html) |
| 2026-05-25 | 54 | Research-driven 4-PR landing (#1532 Repository Engineering for Agents · #1539 Moshi/GPT-4o Realtime gap-fill · #1540 ch-73 The Algorithmic Response · #1541 module-1.10 Modern Transformers) + 2 research artifacts + 2 memory locks (codex-writer/composer-reviewer pair, no-premature-issue-close). #1530 reopened (Wave 3 row 2.2 ticked). CI cross-family review workflow scoped (branch `feat/ci-cross-family-code-review` — landed session 55). | [session-54](./docs/session-state/2026-05-25-session-54-research-driven-4-prs-plus-ai-engineering-foundations-2-2.html) |
| 2026-05-25 | 53 | Codex-as-T0-author pipeline validated; 5 PRs merged including 3 Phase E.1 residual modules (#1527 Edge K8s Distros, #1528 eBPF Fundamentals, #1526 IPv6 Fundamentals) + 2 orchestrator-skill policy locks. Issue #384 closed and replaced with 9 scoped follow-ups (#1516-#1524). Codex gpt-5.5 retry success 3/3; spark first-try 1/3 (rc=-9). Disk hygiene reclaimed 7 GB. | [session-53](./docs/session-state/2026-05-25-session-53-codex-as-t0-author-validated.html) |

Older predecessors: see [`docs/session-state/`](./docs/session-state/) (52 dated handoff files, sessions 13-52).

## Active policies

- **Decision Card C (accepted 2026-05-24)**: composer-2.5 = primary cross-family T0 content reviewer; codex = secondary. Symmetric routing: composer-2.5-authored content → codex reviews. Source: [`docs/decisions/2026-05-24-reviewer-routing-composer-2-5.md`](./docs/decisions/2026-05-24-reviewer-routing-composer-2-5.md).
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

- **761 English modules** (753 + 8 new session 55: Wave 2.1 prompt-fundamentals · 2.2 reasoning-and-logic-prompts · 2.3 prompt-safety-and-evaluation · 2.4 prompt-libraries-and-contracts · GRPO/RLVR · dual-stack K8s · eBPF tracing tools · Edge Fleet Patterns · eBPF security & networking deep-dive · Wave 3.1 retrieval-tools-and-memory-boundaries (PR #1557 merged after handoff)); **312 Ukrainian** (~41%).
- **Starter tracks 499/499 at heuristic 5.0** (prereqs 44 / linux 37 / ai 28 / ai-ml-engineering 103 / cloud 92 / k8s certs 195).
- **122 critical-rubric platform + 13 on-prem REWRITES remain** (unchanged session 55).
- **388 modules need composer-2.5 review** (heuristic-green but not yet composer-2.5-reviewed) — epic #1504, 77 sections, ~58h cursor wall-clock.
- **2 Phase E.1 residual issues remain open** for codex T0 author: #1521 Disconnected K8s · #1524 IPv6-only K8s. (Session 55 closed #1517/#1518/#1520/#1523.)
- **#1530 AI Engineering Foundations epic** — 9 boxes remain (1 Wave 3 module-2.4 dynamic-context-orchestration + 3 Wave 4 + 1 capstone + 5 Phase 4 migration). Wave 2 fully complete pending PR #1554 auto-merge; Wave 3.1 module-2.3 retrieval-tools merged in PR #1557 (post-handoff bonus).
- Site: https://kube-dojo.github.io/ (Starlight/Astro, ~1,350 pages, ~30-40s build).
- Services: `./services.sh {start|stop|restart|status} {dev|api|feedback}` (api on :8768, dev on :4333).

## TODO

**Next session — top priorities:**

- [ ] **Confirm PR #1554 (Wave 2.1) auto-merge landed** — queued for CI at session-55 close; will tick the final Wave 2 box of epic #1530 when it merges. If still stuck on CI, direct-merge (review-job failures are advisory; the 5 Analyze/Incident-dedup checks are the required gate).
- [ ] **Fire Wave 3.2 codex T0** — module-2.4 dynamic-context-orchestration (last open Wave-3 module; W3 = 2.2 session 54, W3.1 = 2.3 PR #1557 merged post-handoff). Closes Wave 3 of #1530.
- [ ] **Fire Wave 4 of #1530** — 3 harness modules (module-3.1 fundamentals · 3.2 guardrails · 3.3 operating) + 1 capstone (module-4.1 Symphony). Untouched. ~6-12 dispatches incl. R1/R2 cycles.
- [ ] **Phase 4 migration** (5 boxes after Wave 4 ships): relocate existing prompt/harness modules from `ai-ml-engineering/` + `ai/ai-native-work/` into new `ai/ai-engineering-foundations/` section; cross-link or deprecate originals.
- [ ] **Fire 2 remaining Phase E.1 residuals**: #1521 Disconnected & Air-gapped K8s · #1524 IPv6-only K8s. Both need scope-correction investigation first (per session-55 pattern: existing modules may cover parts). Use `--model gpt-5.5` explicit.
- [ ] **122 critical platform + 13 on-prem REWRITES** — top of `briefing.actions.next`. Codex gpt-5.5 author + cursor R1. Untouched session 55.
- [ ] **388-module composer-2.5 review epic #1504** — standing-watch: cursor comments "claiming section X" or opens a PR; orchestrator picks up the review queue.
- [ ] **Visual sanity-check the 14 merged session-55 modules** on the live site after deploy.yml runs (`feedback_dont_block_on_human_pass`).
- [ ] **User: add repo secrets `GEMINI_API_KEY` + `DEEPSEEK_API_KEY`** so the new CI cross-family review workflow can actually post comments. Without secrets, the 3 review jobs fail in 8-10s (HTTP 401); workflow stays comment-only/continue-on-error so merges still flow, but no useful review signal.
- [ ] **Save 5 memory entries from session-55 bug autopsies**: (1) `feedback_t0_length_target_use_words_not_lines` — Wave 2.1 cycle wasted 3 dispatches on lines-vs-words ambiguity; (2) `feedback_trust_code_not_comments_in_scope_investigation` — deepseek docstring misled my hermes-scope check, codex caught the actual code; (3) `feedback_chore_vs_fix_prefix_for_bugfix_hook` — link-cleanup PRs use chore() prefix; (4) `feedback_wave_cohort_index_conflict` — 4 PRs editing same index.md guarantee rebase conflicts; (5) `feedback_dispatch_smart_stale_branch_check_is_advisory` — codex review exit 1 with "branch missing remote" is the wrapper sanity check, not a real failure. Details in session-55 handoff.

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

## End-of-session ritual

1. Write today's full handoff to `docs/session-state/YYYY-MM-DD-<topic>.html`.
2. Add a row at top of **Latest handoff** with 1-line summary + link. Shift the third row off to the `docs/session-state/` directory pointer (don't accumulate >3 rows here).
3. Update **TODO** + **Blockers** (briefing API depends on these headings).
4. Commit with `docs(status): handoff <date> — <topic>` style.

---
**Maintenance rule**: this file is the index. Detail goes in the dated handoff HTMLs. Keep STATUS.md ≤100 lines.
