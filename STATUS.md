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
| 2026-05-25 | **54** | Research-driven 4-PR landing (#1532 Repository Engineering for Agents · #1539 Moshi/GPT-4o Realtime gap-fill · #1540 ch-73 The Algorithmic Response (MLA case study) · #1541 module-1.10 Modern Transformers RoPE/ALiBi/MQA/GQA/MLA) + 2 research artifacts in `docs/research/` (DeepSeek fact-check, Osman 12-week gap-analysis) + 2 memory locks (codex-writer/composer-reviewer pair, no-premature-issue-close). AI Engineering Foundations epic #1530 reopened (Wave 3 row 2.2 ticked; 14 boxes remain). CI cross-family review workflow in-flight (branch `feat/ci-cross-family-code-review`). Heaviest session by dispatches (~32 codex+cursor+grok+gemini). | [session-54](./docs/session-state/2026-05-25-session-54-research-driven-4-prs-plus-ai-engineering-foundations-2-2.html) |
| 2026-05-25 | 53 | Codex-as-T0-author pipeline validated; 5 PRs merged including 3 Phase E.1 residual modules (#1527 Edge K8s Distros, #1528 eBPF Fundamentals, #1526 IPv6 Fundamentals) + 2 orchestrator-skill policy locks (#1515 role slate, #1525 condition-dependent T0 routing). Issue #384 closed and replaced with 9 scoped follow-ups (#1516-#1524). Codex gpt-5.5 retry success 3/3; spark first-try 1/3 (rc=-9). Disk hygiene reclaimed 7 GB. | [session-53](./docs/session-state/2026-05-25-session-53-codex-as-t0-author-validated.html) |
| 2026-05-24 | 52 | Cursor-as-author PR pipeline operational; 9 PRs merged (#1506-#1514); 388-module composer-2.5 review epic #1504 filed; starter tracks 499/499 at heuristic 5.0; cursor IDE shifted to author-only mode. | [session-52](./docs/session-state/2026-05-24-session-52-cursor-as-author-pr-pipeline-6-merged.html) |

Older predecessors: see [`docs/session-state/`](./docs/session-state/) (51 dated handoff files, sessions 13-51).

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
- **Learner-check hook is load-bearing**: `.claude/hooks/block-content-merge-without-learner-check.sh` blocks `gh pr merge` on content PRs without a `## Learner check` section quoting verbatim from a touched module. Don't dodge it; quote a real line. **Two gotchas this session**: (1) chained `gh pr edit && gh pr merge` triggers the hook on the merge intent BEFORE the edit runs — split into separate Bash calls. (2) File may use Unicode curly quotes (U+201C/U+201D); ASCII straight quotes in your blockquote won't match verbatim. Pick quote lines without quotation marks if possible.

## Current state

- **753 English modules** (749 + 4 new session 54: module-2.2 Repository Engineering for Agents, ch-73 The Algorithmic Response, module-1.10 Modern Transformers, plus Moshi section added to module-1.1 Voice/Audio AI) across 8 published tracks; **312 Ukrainian** (~41%).
- **Starter tracks 499/499 at heuristic 5.0** (prereqs 44 / linux 37 / ai 28 / ai-ml-engineering 103 / cloud 92 / k8s certs 195).
- **121 critical-rubric platform + 13 on-prem REWRITES remain** (`/api/quality/critical`).
- **388 modules need composer-2.5 review** (heuristic-green but not yet composer-2.5-reviewed) — epic #1504, 77 sections, ~58h cursor wall-clock.
- **6 Phase E.1 residual issues queued** for codex T0 author: #1517, #1518, #1520, #1521, #1523, #1524.
- **#1530 AI Engineering Foundations epic** — 14 acceptance boxes still unchecked (4 prompt + 3 context + 3 harness + 1 capstone + 3 Phase 4 migration). Wave 3 row 2.2 ticked session 54 (PR #1532). Per `feedback_no_premature_issue_close`, do NOT close until every box done.
- **#1538 queued** — Reasoning-model RL (GRPO/RLVR/DeepSeek-R1) module. Codex T0 not yet dispatched; brief in issue body ready.
- Site: https://kube-dojo.github.io/ (Starlight/Astro, ~1,350 pages, ~30-40s build).
- Services: `./services.sh {start|stop|restart|status} {dev|api|feedback}` (api on :8768, dev on :4333).

## TODO

**Next session — top priorities:**

- [ ] **Finish CI cross-family review workflow** — branch `feat/ci-cross-family-code-review` has `scripts/ci/cross_family_review.sh` written (160 lines, comment-only, retries on 5xx). Still TODO: write `.github/workflows/cross-family-code-review.yml` with three jobs (gemini-3.1-pro-preview baseline + gemini-3.5-flash@high + deepseek-v4-pro). Commit + push + open PR. Document required secrets (`GEMINI_API_KEY`, `DEEPSEEK_API_KEY`) in PR body — user adds them before workflow can run.
- [ ] **Dispatch #1538 codex T0** — Reasoning-model RL / GRPO / DeepSeek-R1 module. Held session 54 for codex burn-rate discipline (~13 codex dispatches). Fire first thing if codex cap healthy. **Use `--model gpt-5.5` explicit**.
- [ ] **File dispatch_smart.py hermes argv bug** — script builds hermes argv as `-z PROMPT -m MODEL` which argparse misreads (consumed `--provider` as `-z` value). Reorder fix. Send to cursor (bug-fixer routing per `feedback_cursor_is_strong_bug_fixer`).
- [ ] **Drive #1530 AI Engineering Foundations epic onward** — 14 acceptance boxes unchecked. At session-54 burn rate (~5-6 dispatches per module × 4 rounds avg), closing all 14 needs ~60+ dispatches. Pace this; do NOT close the epic until every box ticked per `feedback_no_premature_issue_close`.
- [ ] **Fire 3 codex T0 drafts for the queued Phase E.1 residuals**: #1517 eBPF Observability + #1520 Fleet Mgmt at Edge + #1523 Dual-stack K8s Setup. **Use `--model gpt-5.5` explicit** (spark died rc=-9 on 2/3 first-tries session 53). Cursor R1 reviewer per Decision Card C.
- [ ] **388-module composer-2.5 review epic #1504** — standing-watch: cursor comments "claiming section X" or opens a PR; orchestrator picks up the review queue.
- [ ] **121 critical platform + 13 on-prem REWRITES** — top of `briefing.actions.next`. Codex gpt-5.5 author + cursor R1.
- [ ] **Read the 4 merged session-54 modules on the live site** after deploy.yml runs — visual sanity-check (we trusted verify_module.py + cursor reviews; human pass happens post-deploy per `feedback_dont_block_on_human_pass`).
- [ ] **Verify statusline is visible** — user reported invisible 2026-05-25 mid-session. Statusline migrated to `claude_extensions/statusline/statusline.sh`; settings.json repointed. Confirm at next session start that the new bar shows the 4-band thresholds (green<300K, yellow 300-400K, red 400-500K, bold-red 500K+).
- [ ] **5 broken-link warnings** in AI/ML tracks (Class B dangling forward-refs; 5min cleanup, same pattern as PR #1490).
- [ ] **Save memory entries** flagged in session-53 handoff: (1) codex spark unreliable for T0 author; (2) Learner-check hook works.

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

## End-of-session ritual

1. Write today's full handoff to `docs/session-state/YYYY-MM-DD-<topic>.html`.
2. Add a row at top of **Latest handoff** with 1-line summary + link. Shift the third row off to the `docs/session-state/` directory pointer (don't accumulate >3 rows here).
3. Update **TODO** + **Blockers** (briefing API depends on these headings).
4. Commit with `docs(status): handoff <date> — <topic>` style.

---
**Maintenance rule**: this file is the index. Detail goes in the dated handoff HTMLs. Keep STATUS.md ≤100 lines.
