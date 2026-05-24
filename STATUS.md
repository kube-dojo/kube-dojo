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
| 2026-05-24 | **52** | Cursor-as-author PR pipeline operational; 9 PRs merged (#1506, #1507, #1508, #1509, #1510, #1511, #1512, #1513, #1514); 388-module composer-2.5 review epic #1504 filed; starter tracks 499/499 at heuristic 5.0; cursor IDE shifted to author-only mode (no more direct merges). | [session-52](./docs/session-state/2026-05-24-session-52-cursor-as-author-pr-pipeline-6-merged.html) |
| 2026-05-24 | 51 | Cursor bug-fix spree 3-for-3 + Linux 3.3/6.4 T0 rewrites + Decision Card C accepted; 5 PRs merged. | [session-51](./docs/session-state/2026-05-24-session-51-cursor-bug-fix-spree-plus-two-linux-t0.html) |
| 2026-05-23/24 | 50 | composer-2.5 promotion stress test + reviewer A/B + entire OnPrem MC 5.1-5.9 + OnPrem Networking 3.4-3.6 to T0; 12 PRs merged. | [session-50](./docs/session-state/2026-05-24-session-50-composer-2-5-stress-test-and-reviewer-a-b.html) |

Older predecessors: see [`docs/session-state/`](./docs/session-state/) (49 dated handoff files, sessions 13-49).

## Active policies

- **Decision Card C (accepted 2026-05-24)**: composer-2.5 = primary cross-family T0 content reviewer; codex = secondary. Symmetric routing: composer-2.5-authored content → codex reviews. Source: [`docs/decisions/2026-05-24-reviewer-routing-composer-2-5.md`](./docs/decisions/2026-05-24-reviewer-routing-composer-2-5.md).
- **Cursor no-merge arrangement (locked 2026-05-24)**: cursor creates issues + opens PRs + comments "claiming"; orchestrator merges after cross-family review.
- **HTML-first artifact policy**: orchestrator artifacts (handoffs, audits, dispatch briefs, autopsies) default to `.html`; STATUS.md / CLAUDE.md / `.claude/rules/` / memory stay `.md`.
- **No separate dispatch watchers**: the `run_in_background: true` exit notification IS the signal. Read `logs/dispatch_responses/<task-id>.txt` directly when wrapper fires. See `feedback_no_separate_dispatch_watcher.md`.

## Current state

- **746 English modules** across 8 published tracks; **312 Ukrainian** (~42%).
- **Starter tracks 499/499 at heuristic 5.0** (prereqs 44 / linux 37 / ai 28 / ai-ml-engineering 103 / cloud 92 / k8s certs 195).
- **121 critical-rubric platform + 13 on-prem REWRITES remain** (`/api/quality/critical`).
- **388 modules need composer-2.5 review** (heuristic-green but not yet composer-2.5-reviewed) — epic #1504, 77 sections, ~58h cursor wall-clock.
- Site: https://kube-dojo.github.io/ (Starlight/Astro, ~1,350 pages, ~30-40s build).
- Services: `./services.sh {start|stop|restart|status} {dev|api|feedback}` (api on :8768, dev on :4333).

## TODO

**Next session — top priorities:**

- [ ] **Cursor starts on epic #1504 — 388 module composer-2.5 reviews across 77 sections.** Standing-watch: cursor comments "claiming section X" or opens a PR; orchestrator picks up the review queue. Start with small sections (prerequisites/cloud-native-101 — 5 modules, prerequisites/philosophy-design — 4). **Each cursor session must use `composer-2.5` model** (not `-fast`, not `auto`).
- [ ] **121 critical platform + 13 on-prem REWRITES** — top of `briefing.actions.next`. Cursor composer-2.5 author + codex R1 review pattern (proven across 14+ PRs sessions 51+52).
- [ ] **5 broken-link warnings** in AI/ML tracks (Class B dangling forward-refs; 5min cleanup, same pattern as PR #1490).
- [ ] **Claude weekly budget resets 2026-05-25 morning** — claude headless dispatches return to rotation.

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
