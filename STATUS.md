# Session Status

> **Read this first every session. Update before ending.**

## Active Work (2026-04-26 ~02:00 local — #388 Phase 0 6/9 done; pipeline integrated + 3 codex review rounds; ready for smoke test)

**Status**: Phase 0 of #388 advanced from 3/9 → 6/9. The new density-aware quality pipeline is wired into v2 (`scripts/quality/pipeline.py` / `stages.py`). 213 quality tests pass (was 188). 3 codex review rounds completed; all must-fixes addressed. **Branch `main`, ruff clean, work uncommitted.** Ready for the user-blocking smoke test on 1 AI/ML module before Phase 0 #8 (site-wide triage — first user-visible site change, needs explicit go).

### What shipped this session (uncommitted, ~865 LOC + 25 new tests)

| File | Δ | What |
|---|---|---|
| `scripts/prompts/teaching-judge.md` | NEW (124 lines) | Cross-family LLM reviewer prompt for #388 stage [2] (REVIEW-tier modules). JSON output `{verdict: approve|rewrite, patterns_present, must_fix, sample_paragraphs, reasoning}`. Pattern-focused: pad-bombs, punchy-bullets, essay-filler. **Not yet wired** — dispatcher integration deferred to Phase 2a. |
| `scripts/quality/density.py` | +63 | `DensityVerdict.{PASS, REVIEW, REWRITE}` 3-way classifier. `classify()` method on `DensityMetrics`. New REWRITE floors (`words<1000 OR w/ln<12 OR wpp<18`). New `reasons_failed_rewrite()` for hard-gate error messages. |
| `scripts/quality/queue.py` | +153 | `model_to_agent(model)` translator (queue model id → `(agent, model)` for dispatch). Split `ensure_queued(set_banner=True)` so route_one can attach without dirtying primary. **Bug fix**: `_iso_to_epoch` was using `time.mktime` (local-tz) on UTC ISO strings → blocks expired prematurely on +UTC machines. Switched to `calendar.timegm`. Refactored `record_attempt_start`/`record_block` into `_in_state(st)` lease-less primitives (caller saves) + thin lease-acquiring public wrappers. |
| `scripts/quality/gates.py` | +46 | `assert_density_threshold(primary, slug, module_relpath)` mirrors `assert_visual_aids_preserved`'s shape. Reads file at writer-branch tip via `_git_show`, classifies, raises `GateError` on REWRITE with REWRITE-tier-floor reasons. |
| `scripts/quality/stages.py` | +399 | `route_one`: density triage runs first; `_needs_writer()` is single source of truth; PASS or REVIEW with score≥4+complete-structure → CITATION_CLEANUP_ONLY (REVIEW-tier doesn't fall through to no-op structural prompt anymore); writer assignment via `queue.ensure_queued + queue.claim`; reviewer is universal-claude (codex if writer is claude). `merge_one`: `has_uncommitted` check moved INSIDE `_merge_lock` (race fix); density hard-gate runs after visual-aids gate; failure bounces via new `_handle_density_failure(st, reason)` (state.transition FIRST, then worktree teardown). New `_clear_banner_and_complete_queue` runs after merge_one releases its lease, acquires its own merge_lock briefly, runs `clear_revision_pending_frontmatter` + commits banner-clear, calls `queue.record_completion`. On commit failure: `git restore` + leave queue incomplete for future sweep. `write_one`: `queue._record_attempt_start_in_state(st)` before dispatch + `_record_block_in_state(st, ...)` on `DispatcherUnavailable` (BEFORE the transition, so the block survives the save). |
| `scripts/quality/pipeline.py` | +130 | `cmd_triage` subcommand. Dry-run by default; `--apply` bootstraps state for REWRITE-tier, calls `queue.ensure_queued(set_banner=True)` for each, prints counts. REVIEW-tier intentionally NOT enqueued in v1. |
| `scripts/quality/prompts.py` | +1 | `rewrite_prompt` instructs writers: "Do NOT preserve `revision_pending:` if present in input frontmatter". |
| `tests/test_quality_density.py` | NEW (~70) | 10 tests: classifier boundary cases for PASS/REVIEW/REWRITE; code blocks excluded from prose_words. |
| `tests/test_quality_queue.py` | NEW (~140) | 12 tests: `model_to_agent` round-trip + invalid; `route_writer` complexity-tag and track rules; `ensure_queued` banner toggle + writer stickiness; `claim` blocked/completed paths. |
| `tests/test_quality_stages.py` | +144 | 3 integration tests: density REWRITE in route_one overrides high audit score; density gate failure bounces to WRITE_PENDING; bounce after RETRY_CAP marks FAILED. Plus `fake_repo` fixture got a default density-bypass monkey-patch so the existing 43 stage tests don't trip on the new gate. |

**Dry-run scan**: 742 modules examined → **153 PASS, 182 REVIEW, 384 REWRITE** (23 skipped below `--min-prose 10`). The REWRITE count is much higher than #388's 165 estimate because my classifier catches pad-bombs (low w/ln) + thin modules (words<1000) in addition to wpp<18.

### Codex review history (3 rounds)

| Round | Verdict | Findings | Closed by |
|---|---|---|---|
| 1 | NEEDS_CHANGES | 5 must-fix: REVIEW falls through to structural; `ensure_queued` polluting non-rewrite queue; merge_one never clears banner / records completion; write_one missing `record_attempt_start`/`record_block`; density-bounce teardown before transition | All 5 + soft note (density message used PASS floors) addressed |
| 2 | NEEDS_CHANGES | 3 NEW must-fix: lease-less primitives saved behind caller's stale `st`; `has_uncommitted` outside `_merge_lock`; banner-clear commit failure left primary dirty + queue marked complete | All 3 addressed |
| 3 | NEEDS_CHANGES | 2 small must-fix: `clear_revision_pending` raise still marked queue complete (one-liner — fixed); no sweep for stranded COMMITTED+banner-incomplete entries (deferred — see Open Items) | #1 fixed; #2 deferred |

### Sticky decisions (this session)

- **Writer routing**: Gemini-3.1-pro for beginner tracks (`ai/foundations`, `ai/open-models-local-inference`), Codex gpt-5.5+high for advanced (everything else relevant), Claude Opus tertiary. Lives in `queue.route_writer`. (`writer_for_index` from 2026-04-25 effectively retired but kept in dispatchers.py for backward compat — unused.)
- **Reviewer**: claude is the universal cross-family reviewer when writer ≠ claude. Codex when writer is claude. Gemini reserved for audit / citation / tiebreak.
- **REVIEW-tier (in v1)**: not enqueued. Cleanup-only path or no-op. Teaching-judge LLM dispatch ships in Phase 2a. Banner is NOT set on REVIEW-tier modules.
- **Density gate is hard, post-rewrite**: REWRITE verdict on the merged file bounces back to WRITE_PENDING (max RETRY_CAP=2 retries), then FAILED.
- **Banner lifecycle**: set ONCE by `triage --apply` in a user-visible commit. Cleared at merge time by `_clear_banner_and_complete_queue` (also commits). Writers instructed to drop the field; banner-cleanup is defense-in-depth.

### Cold start (next session)

```bash
# 1. Confirm pipeline still green.
.venv/bin/python -m pytest tests/test_quality_*.py --timeout=30 -q
# expect: 213 passed

# 2. Confirm triage CLI works (dry-run, no mutation).
.venv/bin/python -m scripts.quality.pipeline triage --min-prose 10 | head -10
# expect: PASS=153 REVIEW=182 REWRITE=384

# 3. The next concrete action is Phase 0 #7 — smoke test on ONE Tier-2 AI/ML module.
#    Pick a Tier-2 module (NOT one of the worst 11 — those are Phase 1):
gh issue view 388  # see scope + remaining 3 task list
```

### Phase 0 — remaining tasks (3 of 9)

- ⏳ **#7** End-to-end smoke on one Tier-2 AI/ML module. Pick a slug, drive `pipeline run-module <slug>` with the new density+queue path. Verify: triage classifies, banner lifecycle works, writer dispatches at the queue's chosen model, cross-family review verdicts cleanly, citation_verify removes unverifiable URLs, density hard-gate passes, merge lands one commit on main, banner cleared. Record wall time + cost.
- ⏳ **#8** **FIRST USER-VISIBLE SITE CHANGE.** Site-wide triage scan + populate queue + commit `revision_pending: true` on ~384 module frontmatters in one batch. **Get explicit user GO before this.** One commit, one PR-style summary in chat showing the file list (or representative sample).
- ⏳ **#9** Phase 1 launch — AI/ML Tier 1 worst 11 modules through `pipeline run --workers 1`. 3-5h background. Stream progress every ~60s per `feedback_claude_owns_pipeline.md`.

### Subsequent phases (from #388)

- **Phase 2a** (2026-04-30 → 2026-05-05): site-wide triage + review pass for the remaining ~373 REWRITE-tier + ~182 REVIEW-tier. **Must finish before Gemini-3.1-pro downgrade on 2026-05-05.** REVIEW-tier is when teaching-judge LLM wiring lands.
- **Phase 2b** (2026-05-05 → 2026-05-17): rewrite Phase 2a failures during Codex 10x window. Multi-day batch, claude monitors.

### Open items (not blocking smoke test)

- **No sweep for stranded `COMMITTED + queue.completed_at=None` slugs** (codex round-3 must #2). Two failure modes that strand: banner-clear commit failure (we revert + leave incomplete, but no future job re-tries it), and `_merge_lock` timeout in `_clear_banner_and_complete_queue`. Track as a follow-up: add `pipeline cleanup-banners` subcommand that scans for COMMITTED states with banner still in frontmatter, retries the clear+commit. ~50 LOC.
- **Round-1/2 specific regression tests not yet added**: `write_one` preserves queue counters after success; `DispatcherUnavailable` persists `blocked_until`; banner-fail-stays-incomplete; concurrent merge pre-flight under banner cleanup; REVIEW-tier routing; PASS-cleanup-no-queue-doc. Codex flagged but accepted as follow-up.
- **Teaching-judge LLM dispatcher** for REVIEW-tier modules (#388 stage [2]). Prompt is written; dispatch helper + state-machine integration deferred to Phase 2a. Code shape: a new `density_judge_one(slug)` stage that loads `scripts/prompts/teaching-judge.md`, dispatches via `default_verifier` (gemini-flash), parses JSON verdict, transitions accordingly.

### Refs

- #388 — site-wide module quality rewrite
- 3 codex review prompts saved at `/tmp/388_codex_review_prompt.md`, `/tmp/388_codex_round2_prompt.md`, `/tmp/388_round3_prompt.md` (will not survive reboot — recreate from `git diff HEAD scripts/ tests/` if needed).

### Prior session entries follow —

---

## Active Work (2026-04-26 ~00:30 local — #387 manual 9.4 done + #388 site-wide style problem surfaced + Phase 0 pipeline 3/9)

**Status**: 9.4 manual rewrite COMMITTED (closes #387). While doing it, surfaced a **site-wide style consistency problem** that the v2/v3 audit rubric never caught — opened **#388** and built the first half of a new quality pipeline (Phase 0, 3 of 9 tasks). **Branch `main`, build green (1797 pages), ruff clean.**

### #388 — site-wide module quality rewrite (the new initiative)

A density scan over 1,339 modules found **165 below 18 wpp** (avg words / prose paragraph) — a signature of three distinct failure modes the rubric never caught:

1. **Codex pad-bombs** (e.g. 9.1 GPU at 2,199 lines / 10.9 wpp — every sentence on its own line, gaming the 600-line gate).
2. **v3 punchy-bullets** (e.g. ai/foundations/1.1 at 15.6 wpp — short fragments + heavy bullets).
3. **Gemini v4 thin-expansion essay-filler** (looks dense, teaches nothing — disqualifies the existing v4 pipeline as a fix).

Both the rubric AND I (Claude) were gamed by these modules — I had rewritten 9.4 today without noticing the systemic pattern until the user pointed at 9.1.

### Phase 0 — pipeline infrastructure (this session — 3/9 done)

- ✅ **`scripts/quality/density.py`** — productionized triple-gate (`words ≥ 1500 ∧ w/ln ≥ 18 ∧ wpp ≥ 22`). Validated: 5 PASS / 3 FAIL on a calibration set covering pad-bomb / v3-punchy / good-rewrite shapes. Run: `python -m scripts.quality.density <path>`.
- ✅ **`scripts/quality/queue.py`** — writer routing rule (Gemini=beginner, Codex=advanced, Claude=tertiary) with **stickiness**: transient errors trigger exponential backoff retry on the **same** writer (5min → 30min → 2h → 8h → 24h). After 5 attempts escalates to tertiary. Never cross-writer fallback (would defeat style consistency). Frontmatter helpers `set_revision_pending_frontmatter` / `clear_revision_pending_frontmatter` mutate `.md` files atomically. Routing verified on 5 modules.
- ✅ **`src/components/RevisionBanner.astro`** + PageTitle wiring + `revision_pending: z.boolean().optional()` in `src/content.config.ts` schema. Smoke-tested: set banner on 1.1, full build (1797 pages, 77.81s), banner HTML rendered correctly with proper styling, restored 1.1.

### Phase 0 — remaining tasks (next session picks up here)

- ⏳ **#4** `scripts/prompts/teaching-judge.md` — cross-family LLM reviewer prompt (Gemini reviews Codex / vice versa). JSON output with verdict + must-fix list.
- ⏳ **#5** `scripts/quality/citation_verify.py` — extract URLs/version/date claims, fetch each, dispatch LLM judge (`supports/partial/no/fail`); only `supports` kept per `feedback_citation_verify_or_remove.md`.
- ⏳ **#6** `scripts/quality_pipeline.py` — single CLI entrypoint with `triage / review / rewrite / status` subcommands. Uses queue.py + density.py + citations.
- ⏳ **#7** End-to-end smoke test on one Tier 2 AI/ML module before mass rollout.
- ⏳ **#8** Site-wide triage scan + populate queue + commit `revision_pending: true` on ~165 module frontmatters in one batch (**first user-visible site change — get explicit go from user before this**).
- ⏳ **#9** Phase 1 AI/ML Tier 1 (worst 11 modules) — 3-5h background, sequential workers=1.

### Decisions locked in this session

| Decision | Source |
|---|---|
| Writer routing: Gemini-3.1-pro for beginner, Codex gpt-5.5+high for advanced, Claude Opus 4.7 tertiary | User confirmed after reading calibration outputs |
| Density triple gate: `prose_words ≥ 1500 ∧ w/ln ≥ 18 ∧ wpp ≥ 22` | Calibration anchors in `density.py` docstring |
| Queue stickiness: NEVER cross-writer fallback on transient errors; escalate to tertiary only after 5 attempts | User: "sometimes gemini or gpt has problems and then we will try later and not assigning to the other type" |
| Student-facing `revision_pending` banner on every queued module until rewrite merges | User: "if we know a module has to be rewritten but couldn't yet we should mark it for the students" |

### Calibration (kept in `.calibration/`, gitignored)

| Module | Gemini-Pro | Codex-5.5 | Original |
|---|---|---|---|
| 1.1 what-is-ai | 174 ln / 2,568 w / wpp 69.8 | 231 ln / 3,604 w / wpp 60.3 | 326 ln / 1,729 w / wpp 15.6 |
| 5.1 mlops-fundamentals | 444 ln / 4,967 w | 1,086 ln / 12,010 w | 933 ln / 9,509 w / wpp 7.3 |
| 9.1 gpu-nodes | 1,288 ln / 10,113 w | 1,433 ln / 12,273 w | 2,199 ln / 10,496 w / wpp 10.9 |

User judgment: both teaching-grade. Codex adds depth on advanced topics, Gemini compresses to vivid essentials on beginner topics.

### Cold start (next session)

```bash
# Confirm Phase 0 still green
python -m scripts.quality.density \
  src/content/docs/on-premises/ai-ml-infrastructure/module-9.4-private-mlops-platform.md \
  src/content/docs/on-premises/ai-ml-infrastructure/module-9.1-gpu-nodes-accelerated.md
# expect: 9.4 PASS, 9.1 FAIL

python -c "from pathlib import Path; from scripts.quality.queue import route_writer; \
  print(route_writer(Path('src/content/docs/ai/foundations/module-1.1-what-is-ai.md')))"
# expect: gemini-3.1-pro-preview

# Pick up at task #4: write scripts/prompts/teaching-judge.md
gh issue view 388     # full project plan + open task list
```

### Refs

- #388 — site-wide module quality rewrite (this session's main initiative)
- #387 — 9.4 manual rewrite (CLOSED by today's commit)
- #378 — prior 12-module MLOps recovery batch
- `scripts/prompts/teaching-rewrite.md` — proven prompt (calibration evidence in `.calibration/`)

**Prior session summary follows** —

---

## Active Work (2026-04-25 ~22:00 local — #378 12-module recovery DONE; 11/12 green, 4 pipeline bugs fixed inline)

**Status**: #378 (12-module MLOps + on-prem AI/ML batch failure) recovered sequentially under workers=1. Result: 11/12 modules COMMITTED or SKIPPED, 1 FAILED on substantive grounds (9.4 has real audit gaps that 3 agents independently flagged — manual rewrite needed). Branch is `main`, clean, 40 commits ahead of `origin/main` (23 from this session). **188 quality tests, ruff clean.**

**Final outcomes (12 of 12)**:

| Slug | Outcome | Score |
|------|---------|-------|
| `platform-disciplines-data-ai-mlops-module-5.1-mlops-fundamentals` | COMMITTED | claude APPROVE 4.9 |
| `platform-disciplines-data-ai-mlops-module-5.2-feature-stores` | COMMITTED | cleanup-only (kept 3, removed 1 unverifiable Tecton URL) |
| `platform-disciplines-data-ai-mlops-module-5.3-model-training` | SKIPPED | cleanup-only (4 citations all verified, no changes) |
| `platform-disciplines-data-ai-mlops-module-5.4-model-serving` | COMMITTED | claude APPROVE 4.9 |
| `platform-disciplines-data-ai-mlops-module-5.5-model-monitoring` | COMMITTED | claude APPROVE 4.75 |
| `platform-disciplines-data-ai-mlops-module-5.6-ml-pipelines` | COMMITTED | claude APPROVE 4.7 |
| `on-premises-ai-ml-infrastructure-module-9.1-gpu-nodes-accelerated` | COMMITTED | claude APPROVE 4.8 |
| `on-premises-ai-ml-infrastructure-module-9.2-private-ai-training` | COMMITTED | claude APPROVE 4.7 |
| `on-premises-ai-ml-infrastructure-module-9.3-private-llm-serving` | COMMITTED | claude APPROVE 4.5 |
| `on-premises-ai-ml-infrastructure-module-9.4-private-mlops-platform` | **FAILED** | tiebreaker (gemini) flagged 3 audit gaps still unaddressed after 2 retries — manual rewrite required |
| `on-premises-ai-ml-infrastructure-module-9.5-private-aiops` | COMMITTED | claude APPROVE 4.9 |
| `on-premises-ai-ml-infrastructure-module-9.6-high-performance-storage-ai` | COMMITTED | cleanup-only (empty Sources section dropped) |

**4 pipeline bug fixes shipped during the recovery** (each caught by the run itself, not in tests):

| Commit | Fix | How it surfaced |
|---|---|---|
| `46e4ae24` | `diag(pipeline)`: print failure_reason + last history + diag path on `[fail]` | (proactive — adds debug info per user request) |
| `39028717` | `fix(gates)`: auto-commit ledger row after post-merge append | 5.2 canary's first green run left `docs/quality-progress.tsv` modified, blocking next module |
| `eb768229` | `fix(pipeline)`: pre-flight refuse `cmd_run` when primary dirty | My own pipeline.py edit dirtied primary, blocking 5.2 canary's merge |
| `eaa994e8` | `fix(stages)`: tiebreaker CHANGES is terminal, not a re-route loop | 9.4 looped 3 tiebreaker rounds with growing must-fix lists before I caught it |

**Git hygiene done at session start**: removed 3 merged quality worktrees + branches (5.2/5.3/5.4 — crash had wiped working tree state, branches sat at `4abd1f80`), removed detached-HEAD `codex-interactive` worktree, cleaned 0-byte `.tsv.lock` residue. Briefing alerts cleared.

**Next session**:
- ~~Push commits to `origin/main`~~ — done; 41 commits pushed.
- **#387 Manual rewrite of 9.4-private-mlops-platform** — full must-fix list + recommended approach in the issue body.
- The 11 newly-merged modules should land in the next `backfill-pending` cycle to attach `## Sources` sections.

**Prior session summary follows** —

---

## Active Work (2026-04-25 ~11:10 local — v2 + citation_backfill seam closed; both pipelines smoke-green)

**Status**: v2 quality pipeline ships modules end-to-end on both writer paths AND auto-orchestrates citation backfill via the new `backfill-pending` subcommand. **160 quality tests, ruff clean.** Two modules took the full path round-trip this morning:

| Slug | Rewrite | Backfill | Sources |
|------|---------|----------|---------|
| `k8s-capa-module-1.2-argo-events` | claude `4f911c49` (4.4) | `0e308451` | 3 upstream Argo Events URLs |
| `ai-ai-building-module-1.1-from-chat-to-ai-systems` | codex `63c91218` (4.6) | `498097e5` | Anthropic + OpenAI + NIST AI RMF |

Both lift from `audit_score < 4.0` → `COMMITTED` (rewrite) → `backfill.done=True` (sources injected) without any manual intervention.

**This morning's commits** (chronological, all pushed):
- `d017e8b9` P0 — hang-detection retry in `_write_in_worktree`
- `4f911c49` P1 — claude rewrite of argo-events
- `63c91218` P2 — codex rewrite of ai-ai-building 1.1
- `33eb89ad` P3+P4 handoff doc + STATUS update
- `ac112c88` Sources preservation in writer prompts + new `backfill-pending` subcommand + rubric doc consistency
- `497d0cd4` `backfill-pending` must commit seed JSON alongside module
- `9939ec4f` fixup: orphaned seed for backfill 498097e5
- `498097e5` ai-ai-building 1.1 backfill (codex agent, 3 sources)
- `0e308451` argo-events backfill (codex agent, 3 sources)

**Workflow now**:
```bash
.venv/bin/python -m scripts.quality.pipeline run --workers 1   # v2: rewrite to COMMITTED
.venv/bin/python -m scripts.quality.pipeline backfill-pending  # backfill: inject Sources
```

`backfill-pending` is idempotent (skips modules with `state.backfill.done=True`), refuses to run on dirty primary, rolls back partial inject writes on failure, and detects concurrent-edit races.

**Prior session summary follows** —

---

## Prior session (2026-04-25 ~10:25 local — v2 pipeline GREEN both writer paths; pushed)

**Status**: v2 quality pipeline ships modules end-to-end on both writer paths. **154 quality tests, ruff clean. 0 commits ahead of origin/main — pushed.**

**Read this first**: [`docs/sessions/2026-04-25-v2-smoke-green.md`](docs/sessions/2026-04-25-v2-smoke-green.md) — P0–P4 done, P3 design call findings, what next.

**This session closed P0–P4** from the prior handoff:

| Task | Result | Commit |
|------|--------|--------|
| P0 hang-retry in `_write_in_worktree` | shipped + 2 regression tests | `d017e8b9` |
| P1 re-smoke argo-events (claude writer + codex review) | COMMITTED in 11.5 min, codex APPROVE @ 4.4 | `4f911c49` |
| P2 codex-as-writer smoke (codex writer + claude review) | COMMITTED in 4.3 min, claude APPROVE @ 4.6 | `63c91218` |
| P3 citation-insertion design call | findings written up — see handoff doc | (no code) |
| P4 push to origin | 22 commits pushed, 0 ahead | — |

**Both LLM writer paths smoke-validated.** Final `merge_one` (rebase + ff-merge) now exercised on real data, twice (round-5 argo-events, round-6 ai-ai-building). The 6-stage pipeline (audit → route → write → citation_verify → review → merge) is durable.

**P3 design call (NEEDS USER DECISION)**: v2 ships modules without `## Sources` by intentional design — writer prompt forbids adding them, reviewer prompt tells reviewer to ignore them, citation_verify only verifies/removes existing. `scripts/citation_backfill.py` is the SEPARATE orchestrator that adds Sources. Two-pipeline workflow currently has NO orchestration handoff: v2 reaches COMMITTED, citation_backfill must be invoked separately. Three issues to decide:

1. **Existing Sources stripping risk**: 241 modules have `## Sources`. v2 rewrite track produces "complete replacement modules" without listing Sources as a protected asset, so any of those 241 that route to `rewrite` (audit < 4.0 OR missing structural section) will lose their Sources on rewrite. Most of them sit at score ≥ 4.0 + structurally complete → `CITATION_CLEANUP_ONLY` (cleanup-only path preserves them), so the actual hit count is likely small but nonzero. **Minimal fix**: 1-line addition to `rewrite_prompt` listing `## Sources` as a preserved asset alongside ASCII/Mermaid/tables.
2. **Orchestration gap**: nothing wires v2 → `citation_backfill` after `merge_one`. Newly-rewritten modules ship at score ≥ 4.0 teaching-wise but are still flagged `critical_quality` by the heuristic rubric scanner because Sources is missing. Two paths: (a) document a manual two-step (run `citation_backfill` on the slug list after each v2 batch); (b) add a 7th `CITATION_BACKFILL` stage post-COMMITTED that auto-invokes `scripts/citation_backfill.py`.
3. **Internal inconsistency in prompts**: `docs/quality-rubric.md` has a "Citation Gate (Mandatory Before Scoring)" — uncited modules cap at score 3 — but `review_prompt` line 213 explicitly tells the reviewer to "Ignore the `## Sources` section — do not penalize their absence." This is intentional (the reviewer mustn't double-penalize when the design defers Sources to a separate stage), but the rubric text should mention the deferral so future readers don't think there's a bug.

Recommendation: ship (1) as a 1-line prompt fix immediately (zero risk, prevents 241-module Sources loss), (2a) as a documentation update noting the manual two-step, defer (2b) to a future ticket once the manual workflow is exercised. (3) is a 1-line note added to the rubric.

### Smoke autopsy

| Round | Outcome | Discovered | Closed by |
|------|---------|------------|-----------|
| 1 | FAILED at extract — claude returned 1.1 KB summary instead of 80 KB module | Tools-enabled claude is agentic by default; rewrites worktree files via Edit/Write and returns only a summary on stdout | `912f56ee` (diag-save infra) + `b488e522` (`--no-tools` plumbing) |
| 2 | FAILED at write — claude hung 900 s with 0 B stdout | Wide `--disallowedTools` (incl. Read/Glob/Grep) sends claude into a state where it produces nothing | `c8a5f3d1` (narrow disallow list — only Bash/Edit/Write/NotebookEdit/WebFetch/WebSearch/Skill/Agent/ExitPlanMode blocked, read-only tools allowed) |
| 3 | FAILED at review — codex CLI subparser missing | Latent bug: `dispatch.py` exposed `dispatch_codex()` but never wired a `codex` argparse subparser; tests stub the function so it was never noticed | `2c2a80a5` (codex subparser added) |
| 4 | FAILED at write retry — claude hung 900 s with 0 B stdout, AGAIN | Initial write succeeded (84 KB, 7 min). Codex review correctly returned `changes_requested` with 3 must-fixes. Retry write hung at the second consecutive claude call | **NOT FIXED** — likely Anthropic-side throttling or sonnet-4.6 instability on consecutive heavy calls within a short window |

### What round 4 validated

End-to-end mechanics that work:

- ✅ Audit promotion (uses cached teaching-audit JSON)
- ✅ Route (score 3.8 → rewrite, writer=claude, reviewer=codex)
- ✅ Worktree create + claude writer dispatch (`--no-tools` narrow list)
- ✅ Module extraction from claude stdout (prose preamble stripped, frontmatter recovered)
- ✅ Worktree commit (`07dd4678`)
- ✅ Citation_verify (no `## Sources` in writer output → had_sources=false → kept=0/removed=0, clean transition)
- ✅ Cross-family review dispatched to codex
- ✅ Review verdict parsed (`changes_requested`, 3 must-fix items captured)
- ✅ REVIEW_CHANGES → WRITE_PENDING retry routing (`retry_count` incremented to 1 of cap 2)
- ✅ Worktree + branch teardown on FAILED transition (round-5 ownership-invariant fix held under real failure path)

The only unvalidated path is `merge_one` (rebase + ff-merge to main).

### Open issue: claude write retry hang

The retry write hung with 0 B stdout across 900 s — same signature as round 2, despite the narrow disallow list that worked for round 4 write 1. Hypothesis (unverified): Anthropic's max-plan API throttles or stalls on a second large claude-code call issued within ~10 min of the first. The `_claude_call_count` budget is per-process so each `dispatch_claude` starts fresh, but Anthropic-side rate windows are independent of our process.

Diagnostic data preserved: `.pipeline/quality-pipeline/k8s-capa-module-1.2-argo-events.write.36654ecb2e86.failed.json` (retry hang, 0 B stdout, "Claude timed out after 900s") and `.pipeline/quality-pipeline/k8s-capa-module-1.2-argo-events.write.d42d847f1341.failed.json` (round-2 wide-disallow hang).

### Options to unblock

1. **Wait + retry** — try the smoke after a longer cool-down (≥30 min from the last hang at 23:55 local). If the hang is rate-window-driven, this works without code changes.
2. **Add hang-detection retry inside `_write_in_worktree`** — on dispatch failure with stdout_len=0 + timeout signature, sleep N seconds then retry once with a fresh attempt_id. Bounds wasted compute at +1 attempt per write.
3. **Bump write timeout to 1800 s** — useful only if hang is "slow generation," not "stuck." Round-2 and round-4 hangs both produced zero bytes across 900 s, suggesting genuine stuck-state — bumping alone unlikely to help.
4. **Pin claude-haiku-4-5 for retry writes** — faster + likely a different rate bucket from sonnet-4.6 default.

Recommended order: 1 → 2.

### Commits this session (6, all unpushed)

| SHA | Title |
|-----|-------|
| `e240f551` | round-5 post-create-worktree race fix (Codex round-5 must) |
| `3ef9bddf` | STATUS — round-6 APPROVE notation |
| `912f56ee` | persist writer raw stdout/stderr on write failure |
| `b488e522` | force text-only output from claude writer/reviewer (`--no-tools` plumbing) |
| `c8a5f3d1` | narrow `--no-tools` disallow list |
| `2c2a80a5` | add missing `codex` subparser to `dispatch.py` |

**Read this first**: [`docs/sessions/2026-04-24-v2-implementation-handoff.md`](docs/sessions/2026-04-24-v2-implementation-handoff.md) — cold-start function with Codex must-fix→file:line→test mapping and the "what NOT to do" list.

**Next session — user runs smoke**:

```bash
# 1. Optional sanity (read-only)
.venv/bin/python -m pytest tests/test_quality_*.py -q             # 147 expected
.venv/bin/python -m scripts.quality.pipeline status | head

# 2. Bootstrap (idempotent — migrates v1 state files)
.venv/bin/python -m scripts.quality.pipeline bootstrap

# 3. Smoke on the designated target
.venv/bin/python -m scripts.quality.pipeline run-module k8s-capa-module-1.2-argo-events

# Expect: terminal state COMMITTED, .worktrees/ empty, one new commit on main.
# If not COMMITTED, inspect status + logs before retrying — per
# feedback_codex_review_before_running, iterate with Codex rather than push through.
```

After the smoke is COMMITTED, follow with the 3-module showcase (AWS IAM 1.1, CKA Pods 1.1, Platform Foundations 1.1) before scaling to 742 under `--workers 1`.

**Tracking issue**: [#375](https://github.com/kube-dojo/kube-dojo.github.io/issues/375).

**Codex review rounds (final)**:

| Round | Verdict | Findings | Closed by |
|-------|---------|----------|-----------|
| 1 | changes_requested | 2 fatal + 7 must + 3 nit | `6c62584b` |
| 2 | changes_requested | 1 must (write_text leak) | `b50cfe2e` |
| 3 | changes_requested | 1 must (post-create finalization) | `59001cbc` |
| 4 | changes_requested | 2 must (post-create window + st2-None) | `ec681076` |
| 5 | changes_requested | 1 must (post-create-worktree race) + 1 nit (flag-flip mismatch) | `e240f551` |
| 6 | **approve** | 0 | — |

Round 5 closed the race window and the flag-flip nit by replacing `worktree_created_here` (a flag flipped AFTER `create_worktree` returned, with a Python-bytecode-level race window) with `we_own_throwaway = (from_stage == "CITATION_CLEANUP_ONLY") and not preexisting_worktree` — both inputs immutable from entry. The BaseException handler also `.exists()`-probes as belt-and-braces. New regression test: `test_cleanup_only_scrubs_worktree_when_create_worktree_raises_after_creation`.

**Key memory**: `feedback_codex_review_before_running` reinforced again — five rounds caught progressively subtler leaks (write_text, finalization scope, st2-None, post-create-finalization window, post-create-worktree-itself race) that self-smoke would have shipped.

**Prior handoff preserved**: [`docs/sessions/2026-04-24-quality-pipeline-redesign.md`](docs/sessions/2026-04-24-quality-pipeline-redesign.md) — requirements still locked.

### What happened this afternoon

1. **Citation pilot reverted** — morning `--agent claude` pilot resolved 73 findings at 41.5% rate but spot-check showed lazy LLM fallbacks (same Capital One Wikipedia URL cited in both IAM and EC2 modules). 57 module edits reverted to HEAD; 73 resolved + 116 unresolvable findings requeued to `needs_citation` via one-off `scripts/requeue_pilot_findings.py`. Primary clean.
2. **Quality pipeline v1 built and rejected** — wrote `scripts/quality_pipeline.py` (~600 LOC, resumable state machine for Track 1 + Track 2). Smoke-tested safe stages only. Told user it was ready. User asked "did codex review it?" — it had not. Codex REJECTED with 10 must-fixes, including fatal bugs (reviewer reads wrong file; ff-merge breaks after first merge; REVIEW_CHANGES state is dead). New memory filed: `feedback_codex_review_before_running.md`.
3. **Requirements for v2 locked** (see handoff doc):
   - Worktrees per module — primary stays on main, clean.
   - Full sweep of all 742 modules; skip those scoring ≥4.0 on teaching audit.
   - Citation verify-or-remove — every URL Lightpanda-fetched + LLM-verified, unverifiable deleted (NOT left in place).
   - Equal Codex/Claude delegation as writers, cross-family review; budget memo overridden by explicit directive.
4. **Other durable learnings** — rubric `/api/quality/scores` is a structural regex, NOT a teaching-quality metric (see `reference_rubric_heuristic_structural.md`). Teaching-quality signal comes from `scripts/audit_teaching_quality.py` instead.

### Artifacts left on disk (untracked pre-handoff, committed at handoff)

- `scripts/quality_pipeline.py` — v1, REJECTED by Codex. Kept as historical reference for v2.
- `scripts/audit_teaching_quality.py` — audit-only, good; reused by v2. Produces `.pipeline/teaching-audit/<slug>.json`.
- `scripts/requeue_pilot_findings.py` — one-off citation-revert helper. Per "no staging scaffolding" memory, can be deleted after v2 lands.
- `.pipeline/teaching-audit/*.json` (21) — audits from the aborted 742-module batch (workers=3 lagged user's Mac during Zoom call).
- `.pipeline/quality-pipeline/*.json` (742) — state JSONs from v1 bootstrap. Idempotent; v2 may reuse or reset.

### Next session

Per the handoff doc:
1. Implement pipeline v2 per the locked requirements + Codex must-fix list.
2. Re-submit to Codex for a second review pass.
3. Smoke-test 1 module end-to-end (the `--only k8s-capa-module-1.2-argo-events` case).
4. Scale to all 742.

### Prior session content — preserved below

---

## Active Work (2026-04-24 morning — 4 PRs merged, phase-2 pilot unblocked via Claude dispatcher)

**Session context**: user pivoted from "start phase-2" to a broader "we have git problems all the time, need a durable solution" concern after I surfaced a 13-day-old stash on cold-start. Infrastructure-level response below. No curriculum or content changes this session.

### This session's shipments (all merged)

- **PR #370** (`fix(resolver): line-buffer stdout + per-module heartbeat (#343)`). Root cause of the morning pilot's apparent 16-min freeze: Python block-buffers stdout when piped to `tee`, so the first line flushed but all subsequent lines never reached the log. Fix: `sys.stdout.reconfigure(line_buffering=True)` at `main()` entry, plus `[i/N] <key>: start` / `: resolving` heartbeat per module so any future hang localizes to a specific phase. Codex APPROVE with one NIT (lock ordering, not just string presence) — addressed in follow-up commit.
- **PR #371** (`feat(briefing): surface silent-drift git hygiene signals`). Adds three alerts to `/api/briefing/session`: forgotten stashes (warn >24 h, escalate >7 d), detached-HEAD worktrees, uncommitted files on `main` only. None need rate-limiting — each is a real drift signal we've hit before. Codex APPROVE with two test-coverage NITs — both addressed. 107/107 `test_local_api.py` pass. The briefing service will surface these on next restart.
- **PR #372** (`fix(resolver): cap per-finding Gemini timeout at 120 s (#343)`). Second round with Codex — first rev was scoped too broadly (would have dropped `run_research` / `run_inject` paths from 900 s to 120 s). Rescoped to a `_dispatch_gemini_for_candidate` wrapper in `citation_residuals.py`; `citation_backfill.dispatch_gemini` keeps the 900 s default so research/inject are unaffected. Test locks in `inspect.signature` default-dispatcher wiring as a regression guard. 61/61 tests pass.
- **PR #374** (`feat(resolver): add --agent claude alternate dispatcher (#343, #373)`). The decisive pilot-unblocker. Empirical motivation: on `cloud/aws-essentials/module-1.1-iam` (Category-A, extremely well-documented) Gemini returned **0/2 resolved in 240 s** (2 × 120 s cap, every call killed mid-thought). Same module with `--agent claude`: **1/2 resolved in 85 s** (50% rate, 3× faster). Confirmed on `module-1.3-ec2`: **1/1 resolved in 176 s** (100%). Ships `dispatch_claude` mirror of `dispatch_gemini`, `CLAUDE_PER_FINDING_TIMEOUT=180`, `CANDIDATE_DISPATCHERS={gemini,claude}` registry, `--agent {gemini,claude}` flag, and a typed `DispatcherUnavailable` exception so Claude peak-hours / budget refusals abort the run cleanly (rc=3) without flipping in-flight findings to unresolvable. Four review rounds with Codex: retryability bug fixed, `sys.executable` → `.venv/bin/python` per AGENTS.md §3 (both Gemini and Claude paths), `_primary_checkout_root(repo_root)` helper for worktree safety (REPO_ROOT parents[1] resolves to the worktree dir, not the primary). 70/70 tests pass.

### Filed, not started — #373 liveness-probe EPIC

Triggered by mini-pilot data below. Mirrors [learn-ukrainian#1520](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1520): composite K8s-style liveness probes (ANY-mode over stdoutStreamed + procCpu + fileMTime) as a durable replacement for the 120 s band-aid. ~days of work — deliberately tracked as non-urgent (matching sister project's stance). Reprioritizes IF we can prove the 120 s cap is killing productive-slow calls, not just refusing fiction. See "pilot data" below for current evidence.

### Hung pilot autopsy — root cause found

Yesterday's 16-min silent hang in `citation_residuals.py resolve --all --limit-modules 10`:
1. **Visibility failure (fixed by #370)**: Python stdout block-buffered behind `tee`, so the intro line was the last thing flushed before Python's 8 KB buffer started filling silently.
2. **Subprocess-level hang (fixed by #372)**: SIGINT traceback (py-spy needs sudo on macOS) pinpointed `dispatch_gemini` at `citation_backfill.py:723` in `subprocess.run(..., timeout=900)` → `process.communicate` → `selector.select(None)`. The 900 s cap was inherited from the write-path pipeline; wrong for short structured URL-candidate prompts. Now 120 s per finding.

### Phase-2 pilot data (inconclusive on AI/ML batch)

Re-ran with heartbeat + timeout fix merged:

| Attempt | Command | Result |
|---|---|---|
| A (10 modules, killed at module 2) | `--all --limit-modules 10 --worker-id pilot-2` | Module 1.3-diffusion-models: 3 findings, all unresolvable, **1506 s** — anomalously long; suspected leftover-process artifact. Killed to investigate. |
| B (3 modules) | `--all --limit-modules 3 --worker-id pilot-2-mini` | 1.4 rlhf-alignment SKIPPED (stale lock from A, later released). 1.6 llm-evaluation: 3 findings / 0 resolved / **360.1 s** = exactly 3 × 120 s cap. 1.7 ai-red-teaming: 7 findings / 0 resolved / **795.3 s**. |

**TOTAL across completed modules**: considered=10, resolved=0, unresolvable=10, rate=0%.

What this does and doesn't tell us:
- **Cap works**: 360 s = 3 × 120 s is clean evidence the timeout fires correctly; the 1506 s anomaly was a one-off (killed-run cleanup artifact, not systemic).
- **0% resolve isn't conclusive**: the entire pilot sample was `ai-ml-engineering/advanced-genai/*` modules, which per residuals audit are heavy Category B (pedagogical fiction) — the LLM should refuse to fabricate URLs there, and refusals look like timeouts from outside.
- **Manual probe on module 1.4 finding[1]** (before it was locked): 2 candidates returned in 71 s — so the resolver isn't universally broken, just this batch.
- **Can't distinguish** "correctly refusing fiction" from "Pro killed mid-thought" from the outside. That's #373's argument.

### Housekeeping

- 13-day-old stash dropped (`stash@{0}` from 2026-04-11 — 714 lines of obsolete AI/ML audit against pre-#200 numbering + 112 lines of UK ZTT already re-translated in `f8a1c478`).
- `py-spy` installed (`brew install py-spy`) but needs `sudo` on macOS. SIGINT → Python traceback was cleaner.
- Stale module-write lock from killed pilot-2 on `module-1.4-rlhf-alignment` explicitly released via `module_lock.release_module_lock` so next run isn't gated on the lease.

### Cold-start for next session — phase-2 bulk is ready with `--agent claude`

Today's Category-A probes confirmed the 120 s Gemini cap was killing productive calls (not just Category-B refusals). Claude dispatcher resolves them.

```bash
# 10-module pilot, Claude backend, dry-run first:
.venv/bin/python scripts/citation_residuals.py resolve \
  --all --agent claude --worker-id pilot-claude \
  --limit-modules 10 --dry-run
```

Spot-check 2-3 resolved Sources lines from `--dry-run` output for quality. If good, drop `--dry-run` and run again to actually write. Claude peak hours (14:00-20:00 local Mon-Fri, 2× pricing) will trigger `DispatcherUnavailable` and abort with rc=3 — findings stay in `needs_citation` for a post-peak retry.

**Category mix reminder**: AI/ML advanced-genai is ~100% Category B (audit calls it out) — expect 0% resolve there by design. Cloud / On-Prem / Platform are where the 112 Category-A findings cluster.

**#373 reprioritization trigger**: if Claude also produces suspiciously low resolve rates at bulk scale, or if peak-hours aborts become disruptive, move the composite-probe EPIC (#373) up. For now Claude is the pragmatic unblock.

### Prior session content — preserved below

---

## Active Work (2026-04-24 early morning — session closed, 5 PRs merged, 2 issues closed, phase-2 pilot queued)

**Continuation of the past-midnight push.** Session ran from cold-start through to a clean close: audit shipped, feature shipped, two bug-fix PRs shipped, residuals-audit worktrees reaped. No open PRs at handoff. Phase-2 bulk pilot is the next move and deliberately held for explicit user approval (bigger blast radius than the one-line edits this session shipped).

### This session's shipments (all merged)

- **PR #366** (`docs: add 2026-04-24 residuals-audit classification`). Promoted `docs/residuals-audit-2026-04-24.md` to main. Final category counts after Gemini-review correction (Zillow "Million-Dollar Gradient Explosion" reclassified B→A): **112 A (sourceable, 57.4%) / 64 B (pedagogical fiction, 32.8%) / 1 C (hallucinated fact, 0.5%) / 18 D (ambiguous, 9.2%) = 195 total across 92 files**. Methodology notes extended with the lesson that excerpt-only classification is lossy when section headers supply names/dates — pull one paragraph of context for terse Category B excerpts.
- **PR #367** (`feat(#343): --limit-modules N for gradual pilot rollout`). Cap flag for safe gradual rollout. Codex caught both real failure modes first round: `--limit-modules 0` / `-1` / non-integer now rejected by argparse via a `_positive_int` type function; mixed empty/non-empty fixture test locks in the after-empty-queue-filter ordering. 43/43 tests pass.
- **PR #368** (`fix(#364): drop finding-excerpt-as-description in Sources line`). Closes #364. `_summarize_finding` removed; `build_source_line` emits `- [title](url)` only; `.html`/`.htm` stripped from URL-derived titles. Codex APPROVE with an independent smoke-test on a fixture residuals tree (confirmed `- [docs.aws.amazon.com: aft overview](url)` output). 47/47 tests pass. **#343 phase-2 bulk unblocked.**
- **PR #369** (`fix(#365): correct CloudWatch/EC2 launch-date historical error`). Closes #365. Single-line prose fix in `module-1.10-cloudwatch.md:41`: "launching alongside EC2 in 2009" → "Launched in May 2009 — about three years after EC2 (2006)". Also softened "over 1 trillion metrics per day" → "over a trillion metrics per day" (exact figure is conference-talk-sourced; qualitative claim holds). Codex review was the **first use of gpt-5.5 at model_reasoning_effort=high** per the new preference — and noticeably more thorough than the default codex model: ran live web searches against AWS announcement archives (CloudWatch May 17, 2009 beta; EC2 Aug 24, 2006 beta / Oct 22, 2008 GA; Logs Insights Nov 27, 2018 GA), cross-checked the trillion-metrics figure against AWS's own "1 quadrillion observations/month" disclosure, and grepped the full repo for lingering old wording. APPROVE, zero must-fix.

### Found and reverted — pilot residual on main

The working tree had an uncommitted line appended to `src/content/docs/cloud/advanced-operations/module-8.1-multi-account.md` — the "happy path" from last night's pilot. The URL was correct (AWS whitepaper) but the description text was the finding's own excerpt ("The root cause of this catastrophic failure…"), which is how I caught #364. Reverted to keep main shippable; the resolved URL will come back cleanly once #364 lands. Also removed the stale `.claude/scheduled_tasks.lock` (pid 43045 was dead).

### Review data points from this session

- **Codex on #367** (Claude-authored feat): NEEDS CHANGES first round, both findings legitimate. (1) `--limit-modules 0` / `-1` silently fell through to full bulk — a typo-unleashes-workers failure mode. (2) Original test fixture had findings in every queue file, so slice-before-filter vs slice-after-filter was indistinguishable. Both addressed, APPROVE on second round. Reaffirms the #350 data point: Codex is the rigorous reviewer for Claude-authored code.
- **Gemini Pro on #366** (Codex-authored audit): REQUEST CHANGES, one real finding — "Million-Dollar Gradient Explosion" misclassified as B because the excerpt-only line sounded anonymous; the surrounding section header named the real Zillow Nov 2021 incident. Dispatched via `--review` defaulted to Pro; **Pro stalled for ~12 min on capacity** before returning. For future content-review dispatches today, prefer `--model gemini-3-flash-preview` explicitly — flash re-review on the correction came back in <60 s.

### Codex model preference (2026-04-24 user instruction)

Use `gpt-5.5` at `model_reasoning_effort=high` for Codex dispatches going forward. Smoke-verified: the CLI echoes "reasoning effort: high" in the exec session header.

Invocation patterns:
- **Direct**: `codex exec -m gpt-5.5 -c model_reasoning_effort="high" --sandbox read-only - < prompt`. Bypasses bridge, output lands in a local file — you must post to the PR manually.
- **Via bridge `ab ask-codex`**: accepts `--to-model gpt-5.5` but has no first-class effort flag. Either pin `model_reasoning_effort="high"` in `~/.codex/config.toml` so everything inherits, or plumb an effort parameter through `scripts/agent_runtime/runner.py`. The first is one line and works immediately.
- **Via `scripts/dispatch.py`**: `CODEX_*_DEFAULT_MODEL` constants at `scripts/dispatch.py:79-81` use `"codex"` to mean "let the CLI pick" — so `~/.codex/config.toml` again covers it with no code change.

Full memory at `reference_codex_models.md`.

### Cold-start for next session (all prerequisites for phase-2 are on main)

1. **Phase-2 pilot — deliberately held for explicit user approval.** Fresh 10-module sample: `.venv/bin/python scripts/citation_residuals.py resolve --all --worker-id pilot-2 --limit-modules 10`. Target: ≥60 % resolve on Category A findings (~112 of 195 total across 92 files). After the run, spot-check 2–3 of the newly-added Sources lines to confirm the title-only output from #368 reads well in context. If green, authorize bulk at `--workers 3`.
2. **Pin Codex config.toml default (optional one-shot)**: add `model = "gpt-5.5"` and `model_reasoning_effort = "high"` to `~/.codex/config.toml` so every invocation path (bridge `ask-codex`, `dispatch.py`, direct `codex exec`) inherits the preference without per-call flags. Not done this session — user-scope config change, wanted an explicit thumbs-up first. See `reference_codex_models.md` for rationale.
3. **Follow-up on #364 (deferred)**: the higher-quality fix is an LLM one-liner per Sources line describing what the page documents (vs. the minimum-viable title-only output in #368). Defer until the phase-2 pilot validates the current output at scale; only invest in the LLM description if the title-only lines feel too spartan next to the human-curated ones in existing modules.

### Worktree hygiene

No active worktrees at handoff — primary repo on `main`, all branches from this session deleted, `.worktrees/codex-interactive` (idle detached HEAD) reaped during cleanup.

### Smoketest (first 30s of next session)

```bash
curl -s http://127.0.0.1:8768/api/briefing/session?compact=1    # fresh=1, stale=0 expected
git log --oneline -6                                             # expect fb466b93 (fix/#365) at top
gh issue view 364 --json state -q .state                         # CLOSED
gh issue view 365 --json state -q .state                         # CLOSED
gh pr list --state open --limit 5                                # expect empty
scripts/ab inbox show claude                                     # should be empty
```

---

## Prior active work — 2026-04-24 past-midnight (concurrency lock merged, pilot diagnosis landed, residuals audit kicked off)

**Continuation from earlier tonight (2026-04-23, see below).** After the 6-PR push, user asked me to run the phase-1.5 re-pilot and keep pushing overnight. Current state:

### 3-module re-pilot result

Resolver + quote-match ran on the reset 3-module set. **Raw numbers: 1 resolved / 4 attempted = 25%**, not the projected 60–75%. But **the failures were correct behavior, not resolver weakness** — diagnosis below.

### Diagnosis (key insight — captured here because it reframes the whole pilot plan)

3 of 4 failures died at `no_candidates_returned` — the LLM refused to propose URLs — **before** quote-match could act. Inspecting the finding excerpts:

- **fine-tuning-llms** finding: `signal: price_usd`, excerpt is a narrative case study (*"abandoned shopping carts incident"*, *"foundation models global endpoint throttling provisioned throughput revenue impact"*). **Pedagogical fiction** — no real public incident to cite.
- **cloud-ai-services** finding 1: same pattern, fictional scenario.
- **cloud-ai-services** finding 2 (`all_candidates_failed`, 3 attempts): module claims *"Azure's classic Foundry Agent Service docs were officially marked as deprecated as of 2027-03-31"* — a **hallucinated future date** (today is 2026-04-24). Microsoft's proposed URL correctly rejected at `no_anchor_match` because 2027 can't be found on the real page.
- **multi-account** finding: resolved successfully (the one happy path).

Reframe: the resolver is doing its job. It refused to polish fabrications (exactly per `feedback_advisory_vs_enforced_constraints.md`). The 25% isn't a resolver problem — it's a content problem. These findings belong in #344's lane (soften/delete claim), not #343's (source citation).

The 3-module pilot set was also selection-biased: these were phase-1 flunks. A fresh 10-module sample from the 64 batch-c residuals would give a real resolve-rate distribution.

### PR #363 — per-module write lock (MERGED `10d73c41`)

Unblocks phase-2 bulk by adding a DB-backed advisory lock so two resolvers can't clobber the same module. New `scripts/pipeline_common/module_lock.py` primitive (acquire / complete / release / sweep / context manager), wired into `citation_residuals.py resolve` with new flags `--worker-id`, `--lease-seconds`, `--no-lock`. 63/63 tests including a threaded stress test. Ruff clean.

Codex first-round NEEDS CHANGES caught one must-fix: lock was keyed on `qp.stem` (flattened filename) but the canonical `module_key` contains slashes — other writers using the canonical form wouldn't coordinate. Fixed at `bb131700`: lock now keys on `data["module_key"]` with stem fallback for legacy files. Added regression test using production-shaped fixture.

Codex re-review APPROVE with substantive answers to all 5 open review questions:
1. **Holder identity** (`pid@hostname`): adequate for two-shell-on-one-host model. No UUID nonce needed unless this becomes a long-lived daemon.
2. **Lock contention UX**: `--fail-on-locked` is reasonable for CI but not blocking. Default skip-and-log is fine.
3. **TTL = 1800s**: right default without heartbeat. Shortening would cause false steals.
4. **Partial-write crash**: real cross-file atomicity gap but not blocker for this PR — `save_queue_file()` is atomic for JSON only; module markdown written first, queue state second. Follow-up: add error outcome / recovery marker.
5. **Schema race**: no race. `_ensure_schema()` serialized in-process, `CREATE TABLE IF NOT EXISTS` benign cross-process, `BEGIN IMMEDIATE` + holder-guarded ops are the right boundary.

Worktree `.worktrees/citation-residuals-lock` cleaned up, branch deleted both local and remote.

### Residuals audit — in-flight, HEADLESS Codex

Task ID: `audit-residuals-classification`, bridge message 2709, dispatched via `scripts/ab ask-codex` in workspace-write mode.

Codex is classifying all ~64 `needs_citation` findings across the batch-c residuals files into:
- A. Sourceable (resolver should succeed)
- B. Pedagogical fiction (no real source exists)
- C. Hallucinated fact (content bug — future date, nonexistent product)
- D. Ambiguous

Output target: `.worktrees/residuals-audit/docs/residuals-audit-2026-04-24.md`. Branch: `audit/residuals-classification`. Codex will commit + push when done but NOT open a PR.

**Status at handoff: the .md file does not yet exist in the worktree — Codex still running.** Next session: check `ls -la .worktrees/residuals-audit/docs/residuals-audit-2026-04-24.md`. If present, read it and decide whether to promote to a content-bugs issue for #344 scope. If `scripts/ab read 2710+` (whatever the response ID ends up being) shows Codex's summary reply, that has the headline counts and top-3 Category C modules.

### WIP: pilot-n flag (UNPUSHED, in worktree)

Worktree: `.worktrees/pilot-n` on branch `feat/343-pilot-n-flag`. **Uncommitted change** adds `--limit-modules N` arg definition to `citation_residuals.py` `resolve` subcommand. Loop wiring NOT yet done. Purpose: cap `--all` runs at N modules for safe gradual rollout (postmortem followup from STATUS.md). Will conflict with #363 on citation_residuals.py — plan is to rebase on main after #363 merges, finish the loop wiring, add tests, open PR.

Next session action: either `git -C .worktrees/pilot-n diff` to resume the work or `git worktree remove --force .worktrees/pilot-n && git branch -D feat/343-pilot-n-flag` to abandon.

### Tech-debt delta this push

| Issue | Was | Now |
|---|---|---|
| #343 concurrency lock | deferred | PR #363 in re-review |
| #343 phase-1.5 pilot | not run | run — 25%, diagnosis done (content-quality issue, not resolver) |
| #344 input data | no categorized list | audit in-flight → will produce Categories A/B/C/D counts + per-module breakdown |
| `--pilot-n N` | postmortem followup | WIP in worktree (unfinished) |

### Cold-start for next session (UPDATED after #363 merge)

1. **Read the residuals audit** — `ls .worktrees/residuals-audit/docs/residuals-audit-2026-04-24.md`. If present: read the summary counts, extract Category C findings (hallucinated facts) into a new issue for #344 content-fix scope. Consider promoting the audit doc to `docs/` via a follow-up PR. Also check `scripts/ab read <latest-id-on-task audit-residuals-classification>` for Codex's summary reply with headline counts.
2. **Decide on pilot-n WIP** — finish or abandon per above. `.worktrees/pilot-n` on branch `feat/343-pilot-n-flag` has one uncommitted edit adding the arg; loop wiring is the remaining work. Must rebase onto main now that #363 landed (citation_residuals.py has moved).
3. **Phase-2 bulk prep**:
   - Fresh-sample pilot on 10 untouched batch-c residuals modules using `citation_residuals.py resolve --all --worker-id pilot-2 --limit-modules 10` (once pilot-n lands) or with explicit module_key args — new lock from #363 now safely coordinates concurrent runs.
   - If ≥60% resolve on Category A findings, run bulk at `--workers 3` (hard cap per `feedback_batch_worker_cap.md`).

---

## Prior active work — 2026-04-23 night (6 PRs out today, all merged; cross-family reviewer rule codified)

**Session deliverables (chronological):**

- **PR #355** (`3294d16f`, merged, earlier today) — phase-1 citation residuals resolver.
- **Commit `55e0e9a2`** — 3-module pilot: 1/5 auto-resolved (20%). Exposed two hallucination classes (URL-existence, URL-content) that capped phase-1.
- **Issues filed:** #351 (missing Sources audit), #352 (Gate A prose/quiz contradictions), #353 (zombie gemini), #354 (orphan check_pre), #356 (URL hallucination mitigation).
- **PR #357** (`2d6908c3`, merged) — **#356 Part 1**: HEAD-check + allowlist pre-filter in `request_candidates`. Codex review approved with 2 nits (HEAD→range-GET→plain-GET escalation, narrow bare-except) — both fixed in `19e4ab05` before merge.
- **PR #358** (`1e9a0b75`, merged) — **#354 fix**: removed orphan-check_pre enqueue after APPROVE. Preflight already runs at top of review function; reducer now sees APPROVE → `done` immediately. Codex nit about testing the reducer symptom (not just the mechanical cause) addressed in `065c84d7`.
- **PR #359** (`5de7e33f`, merged) — **#351 fix**: `audit_missing_sources()` in `pipeline_v4_batch.py` post-batch. Codex caught 2 real must-fix issues (false-positive under `--skip-citation`; header regex too strict on trailing whitespace / EOF-without-newline) — both fixed in `1fad9f3e`.
- **PR #360** (`f6418853`, merged) — **#356 Part 2**: quote-match verification rescues anchorless findings. Initial Codex NEEDS CHANGES — 2 must-fix correctness bugs: (1) quote could override contradictory anchors, (2) prefix-only drift fallback accepted generic lead-ins. Both fixed in `3404ab8b`: anchors authoritative when present (quote-only acceptance limited to anchorless findings); drift fallback replaced with start-AND-end-window match in order. 37/37 tests pass. Re-review APPROVE.
- **PR #361** (`4a3e544b`, merged) — **postmortem follow-up**: added `## Reviewer Assignment (cross-family rule)` section to `docs/review-protocol.md`. Codifies the three model families (Claude / Codex / Gemini), default pairings, and the rule that a PR's reviewer must be from a different family than the author. Codex NEEDS CHANGES caught one must-fix — original "Enforcement" paragraph overclaimed a hard CLI mechanism that doesn't exist. Reworded at `8071805b` to "Operator workflow (not automated enforcement)" with explicit "enforced by convention and reviewer discipline, not by a hard CLI check". Re-review APPROVE.
- **PR #362** (`4416d745`, merged) — **#361 follow-up**: aligned `.claude/rules/gemini-workflow.md`, `CLAUDE.md`, `.pipeline/codex-handoff.md`, and `docs/best-practices/agent-bridge.md` with the cross-family rule. Two Codex NEEDS-CHANGES rounds: (1) caught `.pipeline/codex-handoff.md:151` still mandating Gemini → fixed at `6c73db06`; (2) caught `docs/best-practices/agent-bridge.md:82,85` still hardcoded `--to gemini` and `Reviewed-By: gemini-3.1-pro-preview` in generic operator guidance → fixed at `7cc728ae`, also took nit to relabel dated codex-handoff workflow as "Historical execution notes (2026-04-15 v2-pipeline handoff)". APPROVE on second re-review.

**Non-PR cleanup this session:**

- **Stale `.pids/api.pid`** — contained dead pid `4983`; actual API listener is pid `47928`. Fixed by writing correct pid + re-aging file (briefing stopped flagging stale).
- **Services catalog placeholders** — `feedback` (GitHub Issue Watcher) and `pipeline` (Pipeline Supervisor) are listed in `scripts/local_api.py:52-53` but have no launcher script anywhere; pid files have never existed. Either dead catalog entries or planned-but-unbuilt services. Left alone — no active harm.

**Tech-debt status:**

| Issue | State |
|---|---|
| #351 | ✅ closed (PR #359 merged) |
| #352 | open — Gate A prose/quiz contradictions (deferred; needs pipeline design session) |
| #353 | open — zombie gemini (deferred; low urgency, auto-fallback covers) |
| #354 | ✅ closed (PR #358 merged) |
| #356 Part 1 | ✅ closed (PR #357 merged) |
| #356 Part 2 | ✅ closed (PR #360 merged) |
| #356 Part 3 | open — Codex candidate-fallback (do after Part 2 pilot) |
| #344 | open — extend resolver to overstated/off-topic findings |
| #343 | in progress — phase-1 + phase-2 + phase-1.5 (#356 parts 1+2) landed |

**Key reviewer-rule data points (captured in codified doc):**

- Codex-as-reviewer on PR #362 caught TWO file-level misses across two re-review rounds (`.pipeline/codex-handoff.md`, then `docs/best-practices/agent-bridge.md`). My grep pattern was too narrow ("Gemini for review" vs the actual phrases "Gemini must review" / "--to gemini"). Lesson: when sweeping for a deprecated convention, grep the conjugations + imperative/passive voice + CLI flag values, not just the natural-language form. Codified implicitly via the cross-family doc, not explicitly as a memory.
- **Explicitly deferred (not blocking per Codex)**: `.pipeline/spec-lab-pipeline.md:273,296,299` and `.pipeline/spec-v2-pipeline.md:519` still reference Gemini as reviewer in pending checklist items. Decision: left as historical 2026-04-14 design-spec docs rather than rewriting past design records. Future operators consult `docs/review-protocol.md` for the live rule.

**New learning saved to memory:** `feedback_advisory_vs_enforced_constraints.md` (from earlier in session) — LLM prompt constraints are advisory; enforce deterministically in code before any side-effect.

---

## Cold-start (earlier version — superseded by the top of this file for 2026-04-24)

**1. Re-pilot the 3-module set** — #360 (quote-match verification) merged, so the anchorless-findings class (`named_incident` / `attribution`) should now resolve. Expected: 60–75% resolve rate (up from 20% on phase-1). Reset the queue files first — previous pilot moved findings to `unresolvable_findings[]`:

```bash
.venv/bin/python - <<'EOF'
import json
from pathlib import Path
for stem in ("ai-ml-engineering-advanced-genai-module-1.1-fine-tuning-llms",
             "ai-ml-engineering-ai-infrastructure-module-1.1-cloud-ai-services",
             "cloud-advanced-operations-module-8.1-multi-account"):
    qp = Path(".pipeline/v3/human-review") / f"{stem}.json"
    d = json.loads(qp.read_text())
    restored = []
    for f in d.pop("unresolvable_findings", []):
        restored.append({k: v for k, v in f.items() if k not in ("unresolvable_reason", "attempts", "resolved_at")})
    d["queued_findings"]["needs_citation"] = restored + d["queued_findings"].get("needs_citation", [])
    qp.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
    print(f"reset {stem}: restored {len(restored)}")
EOF

.venv/bin/python scripts/citation_residuals.py resolve ai-ml-engineering-advanced-genai-module-1.1-fine-tuning-llms
# ...repeat for the other two
```

**2. If re-pilot is good (≥60%), prep bulk phase-2 PR:**
- Raise `--workers` cap to ≤3 (per memory `feedback_batch_worker_cap.md`).
- File concurrency fix first — PR #357's Codex review flagged that two resolvers on the same module clobber each other's writes (deferred from #343 phase-1; bit me during the pilot when I accidentally ran one in foreground + background). Needs a `.pipeline/v2.db` lease before bulk.

**3. Other open tech debt (ranked):**
- **#356 Part 3** (Codex candidate fallback) — do after phase-2 bulk if resolve rate is below target.
- **#344** (extend resolver to overstated/off-topic classes) — 257 findings across 4 categories. Design decision needed on the simpler "apply pre-composed fix" cases vs. the harder "soften the claim" cases.
- **#352** (Gate A prose/quiz contradiction) — needs pipeline-design session, not a small PR.
- **#353** (zombie gemini) — low urgency unless next batch shows orphan processes.

**4. Postmortem follow-up:**
- ✅ Make cross-family reviewer rule explicit in `docs/review-protocol.md` — landed via PR #361 + #362.
- Add `--pilot-n N` flag to bulk scripts for gradual rollout.
- Require prompt-change ablations on ≥3 fixture findings before merge.

---

## Smoketest (first 30s of next session)

```bash
curl -s http://127.0.0.1:8768/api/briefing/session?compact=1        # should show 100% convergence, stale=0
git log --oneline -5                                                 # last merge should be #359 (1e9a0b75 or 5de7e33f)
gh pr view 360 --json state,mergeable                                # #360 status
scripts/ab inbox show claude                                         # any Codex responses pending ack
```

Expect: briefing shows stale=0 running≥5, last 5 commits include the PR-359 merge, PR #360 state=OPEN, inbox either empty or has Codex's #360 review response.

---

## Prior (2026-04-23 morning — batch-c cloud citation backfill merged, dispatch auto-fallback landed)

**Today's merges:**

- **PR #349** (`3d8ede2e`) — `fix(dispatch): auto-fallback from API-key to OAuth on Gemini 429`. Auto-flips to OAuth on first rate-limit (independent quota, no backoff); `KUBEDOJO_GEMINI_SUBSCRIPTION=1` preserved as force-subscription opt-out. Codex caught a `max_retries=1` edge case — addressed in `eb8d622c` with 2 regression tests. 10/10 tests pass.
- **PR #350** (`59d62bbd`) — `content(cloud): v4 batch-c — 78 modules citation backfill 1.5 → 5.0`. Overnight `pipeline_v4_batch --track cloud --workers 2` ran 9h40m, 78 modules all cleared rubric at score 5.0 (14 clean, 64 with citation residuals queued). Codex review found real gaps; `84f56a38` addresses: missing `## Sources` in module-2.7-cloud-run + module-7.5-aks-fleet-manager; GKE Autopilot quiz teaching obsolete defaults; AKS identity quiz putting label on SA instead of pod; stale Kafka `/10/` URL.

**Impact on #180 rubric bar:** critical-quality (<2.0) count dropped **562 → 485**. Cloud Advanced Ops no longer appears in the briefing's top-5 critical list. Remaining critical concentrates in AI/ML Ai Native Development, Cloud Architecture Patterns, K8S Capa, K8S Cba.

**Review-protocol data point:** Gemini flash 3 APPROVED PR #350 while Codex caught 3 real content issues in sampled-same modules. **Codex was notably more rigorous on this content batch.** For bulk content review, prefer Codex as the gating reviewer; Gemini is lighter/faster but missed the specific quiz inconsistencies.

**Pipeline gaps surfaced — worth tracking as future improvements (not filed yet):**
1. `citation_v3` silently left 2 of 78 modules with no `## Sources` at all (`module-2.7-cloud-run`, `module-7.5-aks-fleet-manager`). Possible systemic trigger worth investigating before next bulk run — audit for "module touched but no sources added" as a post-batch CI check.
2. Gate A overstatement softener updates main prose but doesn't always update quiz answers citing the same claim, producing module-internal contradictions. Observed on 2 of 5 Codex-sampled modules (6.1 Autopilot defaults, 7.3 AKS identity label).
3. Zombie `node gemini` grandchildren survive `killpg` on dispatch timeout (PPID reparents to init) — #253 was closed as fixed 2026-04-16 but the fix is incomplete. Not filed; real but low-urgency since batch-c produced zero zombies after auto-fallback landed.

**Gotchas updated this session:**
- `KUBEDOJO_GEMINI_SUBSCRIPTION=1` currently errors with `"you must specify the GEMINI_API_KEY environment variable"` — OAuth creds in `~/.gemini/oauth_creds.json` appear to not be picked up by the CLI today (may need interactive `gemini` re-auth). Fall back to explicit API key + `--model gemini-3-flash-preview` for reviews when `gemini-3.1-pro-preview` is at capacity.
- `gemini-3-flash-preview` reliably works via API key today; `gemini-3.1-pro-preview` hitting `No capacity available` most of the afternoon.
- `gemini-2.5-flash` is explicitly off-limits as a fallback — user rejected; quality tier too low (see memory `feedback_gemini_models.md`).

**Next session starts here:**
1. If restarting batches, smoke-check gemini CLI first: `echo OK | gemini -m gemini-3-flash-preview -y` (via API-key path). The new auto-fallback in `dispatch.py` handles rate-limit flips automatically — no env var needed.
2. Batch-c's scope was `--track cloud` only. Remaining critical-quality concentrations per post-merge briefing: AI/ML Ai Native Dev, Cloud Architecture Patterns (odd — confirm not cleared yet), K8S Capa, K8S Cba.
3. The 64 `residuals_filed` modules from batch-c have citation-triage findings queued in `.pipeline/v3/human-review/`. Issues #341 / #343 / #344 track the auto-resolver epic — that's the scalable path before running more bulk batches.
4. 2 stale pid files per briefing — `scripts/cleanup_pids.py` or similar.

---

## Prior: Session 11 (2026-04-21) — pipeline_v4 built end-to-end, tech debt cleared, dogfood validated

Session 10 handoff: [`docs/sessions/2026-04-21-session-10-handoff.md`](./docs/sessions/2026-04-21-session-10-handoff.md).
Session 11 handoff: [`docs/sessions/2026-04-21-session-11-handoff.md`](./docs/sessions/2026-04-21-session-11-handoff.md).

**Session 11 landed (9 commits on main, 2,936 LOC of new pipeline + 5 tech-debt fixes):**

Tech debt:
- `2eedc994` pipeline_v2 sibling-module imports (v4 needed v2 worker infra; this was the blocker). 40/40 v2 tests pass.
- `10aa1a67` autopilot_v3 `--content-stable-only` gate (skip thin modules when prepping for v4). Queue filtered 108→98 sections on first dry-run.
- `7b7210ef` `pyrightconfig.json` with `extraPaths: ["scripts"]`.
- `2d4a6a90` v1_pipeline drops orphan `.staging.md` before fresh write-phase attempt. Root cause: cleanup only ran on `pending/audit` branch, not `phase="write"` resume branch. 102 orphan staging files deleted inline.
- `ba8cf489` `/api/quality/scores` adds `path` field; v3 gate keys by path (not reconstructed label). Issue #325 closed. Delete ~90 LOC of label-reconstruction helpers.

Pipeline v4 (issue #322 rewritten based on Gemini NEEDS CHANGES review; 5 structural findings addressed):
- `ad590be3` `scripts/rubric_gaps.py` — Stage 1 gap identification, 224 LOC + 126 test LOC. 9 tests pass.
- `3d172a59` `scripts/module_sections.py` — H2-based section splitter with round-trip fidelity, 426 LOC + 289 test LOC. 18 tests pass.
- `747bd53c` `scripts/expand_module.py` — Stage 2 gap-driven expansion (quiz, mistakes, exercise, outcomes via Codex; thin via Gemini multi-pass). 641 LOC + 311 test LOC. Provenance markers (`<!-- v4:generated ... -->`) wrap every generated block. Diff-lint rejects any rewrite of human-authored paragraphs.
- `e663088d` `scripts/pipeline_v4.py` — Stage 1-5 orchestrator. 533 LOC + 386 test LOC. 9 tests pass. Retry budget 2, regression epsilon 0.2, generated-LOC threshold guard against citation-over-LLM-prose.

35/35 pipeline_v4 tests pass. Dogfood run on `ai/ai-for-kubernetes-platform-work/module-1.2-ai-for-kubernetes-troubleshooting-and-triage`: **2.0 → 4.2 score in 7m6s**, outcome=clean. Stage 4 (citation_v3) skipped via `--skip-citation`; its guards are unit-tested. Expanded module preserved in `.worktrees/dogfood-v4/` pending review.

Issues closed: #325 (scorer paths), #272 (AI for K8s section — all 4 modules exist, quality tracked by #180), #198 (Master Execution Plan — duplicated STATUS.md + handoffs).

**Next session starts here:**
1. Fix retry-refresh-gaps bug in pipeline_v4.py — Stage 3 retry uses original gap list instead of refreshed. See session 11 handoff for fix sketch. Small change, single unit test.
2. Decide what to do with the dogfood worktree (commit to main, delete, or keep as golden reference).
3. Build `scripts/pipeline_v4_batch.py` — wrap `run_pipeline_v4` with `.pipeline/v2.db` lease coordination for concurrent runs (8-way default, aim for ~32 h across 620 modules instead of 206 h sequential).
4. Dogfood batch on the 5 "AI/ML Engineering Ai Infrastructure" critical-quality modules the briefing flags.

**v4-specific bugs (none blockers, see session 11 handoff for details):**
- Stage 3 retry doesn't re-fetch gaps (listed above).
- `loc_after` in ExpandResult drifts from actual disk state.
- Gemini CLI YOLO mode self-lints with markdownlint (~30s/section latency).

**Known gotchas — updated this session:**
- Codex sandbox blocks `.git/worktrees/*/index.lock`. Every delegation returned "files written, commit failed". Pattern: Codex writes, Claude commits from primary-repo side. Prompts should instruct Codex NOT to attempt commits.
- Gemini 3.1-pro is frequently at-capacity. Pass `--model gemini-3-flash-preview` explicitly when 3.1-pro is congested; dispatch.py doesn't auto-fallback on rate limit (same-quota assumption).
- Rubric scorer weights section presence > line count. Dogfood crossed 4.0 at 258 LOC (target 600). `target_loc` is a ceiling for effort, not a floor for success.
- Carry-over: Codex auth can go flaky under load; smoke-check with `echo hi | timeout 25 codex exec --full-auto --skip-git-repo-check`.
- Carry-over: 900s Codex dispatch hard-timeout; large runs need phasing.

**Lower-priority carry-over:**
- 5 critical-quality modules at 1.5 (AI/ML Advanced GenAI 1.1 fine-tuning, 1.2 LoRA, 1.3 diffusion, 1.10 single-GPU, 1.11 multi-GPU) — perfect targets for v4 batch dogfood.
- 2 CKA inject_failed modules from session 10 handoff: RESOLVED — `module-3.1-services` and `module-3.6-network-policies` have clean `## Sources` from later v3 runs (commits `2112507f`, `17084227`). Handoff was stale.

---

## Prior session-5 handoff (first half of the day)

Session 5 landed two things: the heuristic quality scorer now auto-fails modules with no `## Sources` section (reveal: 726/726 critical, old 4.71 avg was fabricated; commit `c1220cd0`), and the `## Sources` vs `## Authoritative Sources` contract drift between `check_citations.py` and `v1_pipeline.py` is unified (commit `1918d262`). Full handoff with the citation-backfill plan + next-session blockers: [`docs/sessions/2026-04-19-session-5-citation-backfill-design.md`](./docs/sessions/2026-04-19-session-5-citation-backfill-design.md).

**Session 5 progress (landed this session, 9 commits from `c1220cd0` → `a769aede`):**
1. ✅ Scorer truth-gate + Pyright cleanup (726/726 critical — real baseline).
2. ✅ Sources-header contract unified across v1 pipeline + tests.
3. ✅ `docs/citation-trusted-domains.yaml` — tiered allowlist.
4. ✅ `scripts/fetch_citation.py` — 20/20 dry-run pass; bot-protected domains (NIST, OWASP, Microsoft, Google, CISA, Anthropic) all returned text via browser UA.
5. ✅ `scripts/citation_backfill.py research` — disposition-aware (supported/weak_anchor/unciteable). Honest flagging, no forced weak anchors.
6. ✅ `scripts/citation_backfill.py inject` — structured edit plan, mechanical wrap application, diff linter verifies additive-only. `check_citations.py` passes on ZTT 0.1 staging.
7. ✅ Revision queue — unciteable claims routed to `.pipeline/citation-revisions/` for future content-softening pass.
8. ✅ Calibration on 3 ZTT modules: 45 claims, 51% supported, 44% unciteable. Pipeline refuses to polish fabrications.

**Next session starts here:**
1. Implement verify step (Gate B) — 2nd LLM semantic check against cached page text.
2. Design the merge workflow: staging.md → main, auto-PR via worktree (user confirmed no humans in loop).
3. Scale research to ZTT 0.3–0.10 (8 more modules).
4. Expand allowlist for recurring unciteable patterns (GitLab, CERN) or write a revision-softening worker.
5. Open design: grounded-search API (MVP skipped it — 0 hallucinations so far suggests maybe unneeded); weekly budget caps in `control_plane.budgets`.
6. Scale order (user-confirmed): ZTT → AI → prereqs → cloud → AI/ML → linux → on-prem → platform → certs.

**Prior queue (session 4, still valid but now lower priority than citation backfill):**
1. #277 — `/api/build/run` + `/api/build/status` endpoints (~150 LOC, clear spec)
2. #258 — Local API audit + cold-start cost (broad; dispatch for split plan first)
3. #248 — Review Batch triage (probably closable)
4. #319 — Remove AUDIT compat shims (~50 LOC, low priority)
5. #311 — Finish factoring `append_review_audit` (~120 LOC)
6. #313 — AI foundations 1.1/1.2/1.3 regen (needs user enqueue; see handoff)
7. #315–#318 — Pipeline v2 follow-ups from the #239 audit split

**Infra shipped in session 4** — skim before resuming delegations:
- `docs/review-protocol.md` — canonical reviewer contract with mandatory FINDING format
- `scripts/verify_review.py` — post-hoc grep-verification of reviewer quotes (pipe a review through it when findings look suspect)
- `--review` flag on `ask-gemini`/`ask-codex`/`ask-claude` (bridge parity)
- Gemini Pro is the default for `--review`; Flash only if explicitly requested

**Side lane for user** (handoff has the exact commands):
- Enqueue 7 critical-quality modules (<2.0 score) into pipeline v2
- Triage 2 dead-letter translation modules (`distributed-systems/5.1`, `5.3`)

---

## Prior session archive (sessions 1–3 content below, kept for reference)

Lead: Claude. Citation-first infra for automated pipeline (Gemini 3.1 Pro writes → Codex reviews/fact-checks/applies). Full handoff: [`docs/sessions/2026-04-18-lead-dev-citation-infra.md`](./docs/sessions/2026-04-18-lead-dev-citation-infra.md).

**Session 2 progress (autonomous run):**
- Pushed 4 citation-infra commits to `origin/main` (build verified green, 1797 pages, 0 errors).
- Read V3 proposal #217 in full — most already shipped via #219/#224/#226. Remaining: pin Gemini, per-track rubric, sampling.
- Drafted 4 infra GH issues: **#276** (local API GH endpoints), **#277** (local API build endpoints), **#278** (pipeline v3 remaining — 3 PRs), **#279** (automated citation pipeline wiring).
- Opened **PR #280** — citation-aware module page design proposal (3-tab Theory/Practice/Citations via Starlight `<Tabs syncKey>`; resolves design scope of #273).
- Delegated all 5 to Codex via agent bridge (task-ids infra-276..279, review-280). Build-report-in-PR-body convention included in each delegation to avoid future Claude-side build hops.

**Role-swap decision:** picked Codex adversarial on every PR (role-swap per PR) — consistent with Codex-as-reviewer memory and #235 queue ownership pattern. Gemini stays as fallback only if Codex is unavailable.

**Session 2 — autonomous run additions (while user AFK):**

API stability (committed d19a1016):
- Killed runaway API instance (stale port 8768 lock); restarted on 127.0.0.1:8768 (per `localhost_only` rule).
- Added `timeout=5` to two unbounded `subprocess.run` calls in `scripts/local_api.py` (`build_worktree_status`, `list_worktrees`) — they can hang the briefing endpoint when git hits lock contention.
- Wrapped `do_GET` response-send in `BrokenPipeError`/`ConnectionResetError` handler — client disconnects no longer noisy.
- Explicit `ThreadingHTTPServer.daemon_threads = True` and `allow_reuse_address = True` — eliminates "port in use" startup loops.

Pipeline running (foreground now; survives session end):
- Killed 4 stale PID files (patch/review/write/pipeline).
- Started 3 v2 workers via Bash background: patch-worker (PID 87463), review-worker (PID 87941), write-worker (PID 88084). All orphaned from parent shell.
- Sleep interval: 30s. Workers are live and picking up work — pipeline moved 1 pending_patch job through patch → review since start.
- Current state: `pending_review: 1, pending_write: 0, pending_patch: 0, done: 566, dead_letter: 0, in_progress: 0`. Convergence 99.8%. flapping_count: 12 (up 1; minor).

Codex delegation (with `CODEX_BRIDGE_MODE=danger` since prior `safe` mode blocked writes + network):
- `infra-277-v2` (rerun of #277 build API endpoints) — running in background task `b6n7sz9tq`.
- `infra-235-race` (CRITICAL parallel race condition from #235, lines 3049-3063 / 190-201 / 2848-2864 of v1_pipeline.py) — running in background task `b7u81pwe3`.
- Earlier `review-280` completed successfully: substantive adversarial review (5 concrete findings, corpus-scan evidence). Posted as PR comment since Codex has no network to `gh`.

Issue triage / comments posted:
- **#217** — status audit posted; remaining work tracked in #278; recommended close once PR 1 lands.
- **#274** — ACs 1-3 marked done with commit references; AC4 handled; AC5 deferred to #279.
- **#180** — AI Foundations batch reset announced per #274.

Uncommitted in tree:
- `src/content/docs/k8s/lfcs/module-1.4-storage-services-and-users-practice.md` — **worker WIP**, don't touch.
- `docs/sessions/` — untracked session handoff docs.

**PRs opened by Codex, reviewed by Claude (role-swap convention). All OPEN, waiting for user merge:**

#235 HIGH-severity bug fixes (14 of 14 closed):
- #281 serialize parallel worker state mutations (CRITICAL)
- #284 defer data_conflict check until after draft
- #285 malformed review JSON fails closed
- #287 _merge_fact_ledgers is pure and idempotent
- #288 needs_independent_review revived for last-resort approvals
- #289 content-aware ledger covers late sections (40k windowing)
- #290 check_failures tracks consecutive, not lifetime
- #291 last-attempt edit success triggers re-review, not reject
- #292 write-only preserves draft for review (regression test lock-in)
- #293 fresh restart clears stale resume metadata
- #294 review fallback chain continues to last-resort
- #295 severe rewrite clears stale targeted_fix, uses full rewrite model
- #296 CHECK retries in-function, shields outer circuit breaker
- #297 rewrite retries extract knowledge packet from baseline
- #298 unify retry policy across serial/parallel/reset-stuck modes

#277/#278 infra (pipeline v3 remaining + build API):
- #282 feat: /api/build/run + /api/build/status (#277) — **note: re-run ruff + npm run build from main before merge**, worktree build-path bug was environmental
- #283 refactor: pin Gemini writer model via single constant (#278 PR 1, narrow)
- #286 refactor: pin Gemini constant across remaining workers (#278 PR 1b, full)

#273 design:
- #280 citation-aware module page design proposal

**Full session PR tally — 21 PRs opened, 21 reviewed:**

#235 HIGH-severity (14/14 closed):
#281 parallel-race, #284 data_conflict, #285 malformed-JSON, #287 merge-ledgers-pure,
#288 needs_indep_review, #289 ledger-40k-windowing, #290 consecutive-check_failures,
#291 last-attempt-re-review, #292 write-only-regression, #293 fresh-restart-cleanup,
#294 fallback-chain-last-resort, #295 severe-rewrite-full-model,
#296 CHECK-retries-in-function, #297 rewrite-from-baseline, #298 unified-retry-policy

#235 MEDIUM (1 closed, more remaining):
#302 rejected-drafts-do-not-poison-ledger

#277 (local API build endpoints):
#282 /api/build/run + /api/build/status

#278 (pipeline v3 remaining, all 4 sub-PRs complete):
#283 pin Gemini 1a (narrow), #286 pin Gemini 1b (full), #300 per-track rubric profiles,
#301 second-reviewer sampling

#276 (local API GH endpoints):
#299 /api/gh/issues + /api/gh/prs

#273 design:
#280 citation-aware module page (3-tab proposal)

**Codex queue state:**
- `infra-279` (citation pipeline wiring) — **TIMED OUT at 900s**, no PR. Partial work (+655 LOC across 3 files) uncommitted in `.worktrees/citation-pipeline`. Don't commit as-is. #279 comment posted with recommendation to split into 3 sub-tasks (#279a seed injection, #279b citation gate step, #279c rubric dimension + e2e test).
- All other originally-queued tasks now have PRs.

**Merge ordering guidance for user return:**
1. First: #281 (parallel race — highest-impact), #285 (fail-closed), #290 (consecutive counter — composes with #296)
2. Then: all other #235 HIGH bugs (can merge in any order, some compose — see individual review comments)
3. Then: #278 PR 1a (#283) → PR 1b (#286) (stacked — 1b needs 1a first) → PR 2 (#300) → PR 3 (#301)
4. Then: #276 (#299), #277 (#282 — but re-run build from main first)
5. Then: #302 (composes with #287, #289)
6. #280 (design proposal) merge decision separate — reviews posted
7. #279 (citation pipeline) — pending Codex completion

**Service state at handoff:**
- API: 127.0.0.1:8768, PID 82871, uptime 20 min
- v2 patch/review/write workers: PIDs 87463 / 87941 / 88084, all 19 min uptime
- dev server: unchanged (existing)
- Pipeline convergence: 99.8%, 566 done, 1 pending_review (flapping on LFCS module-1.4, known issue being tracked in #235)
- 0 stale pid files, 1 stopped (pipeline supervisor, intentional — workers are direct-run, no supervisor layer active)

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

### Certifications Breakdown
| Cert | Modules |
|------|---------|
| CKA | 47 |
| CKAD | 30 |
| CKS | 30 |
| KCNA | 28 |
| KCSA | 26 |
| Extending K8s | 8 |

### Cloud Breakdown
| Section | Modules |
|---------|---------|
| Hyperscaler Rosetta Stone | 1 |
| AWS Essentials | 12 |
| GCP Essentials | 12 |
| Azure Essentials | 12 |
| Architecture Patterns | 4 |
| EKS Deep Dive | 5 |
| GKE Deep Dive | 5 |
| AKS Deep Dive | 4 |
| Advanced Operations | 10 |
| Managed Services | 10 |
| Enterprise & Hybrid | 10 |

### On-Premises Breakdown
| Section | Modules |
|---------|---------|
| Planning & Economics | 4 |
| Bare Metal Provisioning | 4 |
| Networking | 4 |
| Storage | 3 |
| Multi-Cluster | 3 |
| Security | 4 |
| Operations | 5 |
| Resilience | 3 |

### Platform Engineering Breakdown
| Section | Modules |
|---------|---------|
| Foundations | 32 |
| Disciplines (SRE, Platform Eng, GitOps, DevSecOps, MLOps, AIOps + Release Eng, Chaos Eng, FinOps, Data Eng, Networking, AI/GPU Infra, Leadership) | 71 |
| Toolkits (17 categories) | 96 |
| Supply Chain Defense Guide | 1 |
| CNPE Learning Path | 1 |

### AI/ML Engineering Breakdown
Migrated from neural-dojo + modernized with 8 new 2026 modules (#199, Phase 4b). All modules passed the v1 quality pipeline at 38–40/40.

| Section | Modules |
|---------|---------|
| Prerequisites | 4 |
| AI-Native Development | 10 |
| Generative AI | 6 |
| Vector DBs & RAG | 6 |
| Frameworks & Agents | 10 |
| AI Infrastructure | 5 |
| Advanced GenAI | 11 |
| Multimodal AI | 4 |
| Deep Learning | 7 |
| MLOps | 12 |
| Classical ML | 3 |
| History | 1 |

### AI Breakdown
Top-level learner-first AI track designed as the bridge from AI literacy into real AI building and then into AI/ML Engineering.

| Section | Modules |
|---------|---------|
| Foundations | 6 |
| AI-Native Work | 4 |
| AI Building | 4 |
| Open Models & Local Inference | 7 |
| AI for Kubernetes & Platform Work | 4 |

### Ukrainian Translations
| Track | Translated | Total |
|-------|-----------|-------|
| Prerequisites | 35 | 33 |
| CKA | 47 | 47 |
| CKAD | 30 | 30 |
| CKS | 0 | 30 |
| KCNA | 0 | 28 |
| KCSA | 0 | 26 |
| AI/ML Engineering | 0 | 68 |
| **Total** | **115** | **626** |

## Quality Standard

**Rubric-based quality system** (docs/quality-rubric.md): 7 dimensions scored 1-5. Pass = avg >= 3.5, no dimension at 1.

**Audit results** (docs/quality-audit-results.md, 2026-04-03): 31 modules scored.
- Overall avg: 3.3/5 (GOOD)
- Gold standard: Systems Thinking (4.6), On-Prem Case (4.4)
- 5 critical stubs fixed (expanded from 49-74 lines to 266-918 lines)
- 3 high-priority modules improved (API Deprecations, etcd-operator, Deployments)
- Remaining: 8 medium, 11 low priority modules need improvements

**Systemic issues found & being addressed**:
1. No modules had formal learning outcomes → added to all rewritten modules + codified in writer prompt
2. Active learning back-loaded to end in 87% of modules → inline prompts added to rewrites
3. Quiz questions tested recall not understanding → scenario-based quizzes in all rewrites

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

## Recently Closed (Session 3)
| # | Issue | Status |
|---|-------|--------|
| #174 | Phase 1: Research Educational Frameworks | Closed — docs/pedagogical-framework.md |
| #175 | Phase 2: Create Quality Rubric | Closed — docs/quality-rubric.md |
| #176 | Phase 3: Audit Modules Against Rubric | Closed — 31 modules scored |
| #178 | Phase 5: Codify Quality Standards | Closed — writer prompt, rules, skill updated |
| #170-173 | Gemini's buzzword issues | Closed — replaced by concrete sub-tickets |

## TODO

- [x] Prerequisites: all 33 modules improved (outcomes, inline prompts, quiz upgrades, emoji fixes) — EN + UK complete
- [x] Linux: all 37 modules improved (outcomes added) — EN + UK complete
- [x] CKA: all 41 modules — outcomes + inline prompts + scenario quizzes (Parts 0-5 complete) — EN complete, UK outcomes synced
- [x] CKAD: all 24 modules — outcomes + inline prompts + scenario quizzes — EN complete, UK outcomes synced
- [x] CKS: 30 modules — outcomes + inline prompts + scenario quizzes — EN complete, UK outcomes synced
- [x] KCNA: 28 modules — outcomes + inline prompts + scenario quizzes — EN complete, UK outcomes synced
- [x] KCSA: 26 modules — outcomes + inline prompts + scenario quizzes — EN complete, UK outcomes synced
- [x] On-Premises: all 30 modules — inline prompts + narrative between code blocks + quiz improvements
- [x] Fundamentals track reorder: Zero to Terminal → Everyday Linux → Cloud Native 101 → K8s Basics → Philosophy & Design → Modern DevOps
- [x] Zero to Terminal: Next Module link fixes (0.1→0.2, UK 0.2→0.3)
- [x] Git Deep Dive course: 10 modules + Git Basics in ZTT — #190
- [x] v1 quality pipeline built: AUDIT→WRITE→REVIEW→CHECK→SCORE — #188
- [x] Gap detection (within-track + cross-track) — #188
- [x] Zero to Terminal: 10/10 modules pass pipeline (29+/35)
- [x] All prerequisites pass pipeline (43/44 done, 29+/35) — #180
- [x] 6 rejected prereq modules rewritten by Gemini + passed pipeline (35/35, 34/35)
- [x] ZTT module numbering collision fixed (0.6 git-basics + 0.6 networking → renumbered 0.7-0.11)
- [x] Pipeline v2: Gemini defaults, e2e command, track aliases, safety hardening
- [x] uk_sync.py consolidated: status/detect/fix/translate/e2e with track aliases
- [x] Certs pipeline: 150/164 pass, 3 fail, 8 WIP — #180
- [x] Cloud pipeline: 80/86 pass — #180
- [x] Linux pipeline: 34/38 pass — #180
- [x] Pipeline v3: knowledge packets, block-level rewrite, ASCII→Mermaid — #192
- [x] Pipeline: section index.md rewrite (EN) + auto-translate (UK) after section completes
- [x] Pipeline: 41 integration tests (test_pipeline.py)
- [x] Pipeline: subsection aliases (ztt, cka, aws, etc.) + auto-discover from any dir path
- [x] Nav fix: all 156 index.md files (EN+UK) set to sidebar.order: 0
- [x] Nav fix: slug corrections for ZTT module-0.6, git-deep-dive modules 1 and 9
- [x] K8S_API check: demoted to WARNING, strips code blocks + inline code (false positives)
- [x] .staging file glob bug fixed (was creating bogus state entries)
- [x] Token analysis: subagents are 74% of volume but mostly cheap cache reads. Not the cost monster claimed.
- [x] AI/ML Engineering track migrated from neural-dojo (60 existing + 8 new 2026 modules, #199 Phase 4b). All 8 new pass v1 pipeline at 40/40.
- [x] v1 pipeline fixes: 300s→900s timeouts, targeted-fix / nitpick / previous_output scaffolding, short-output guard (enables quality-rubric retries to converge)
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
- Pinned zod@3.25.76 (zod v4 breaks Starlight schema validation)
- `defaultLocale: 'root'` for Starlight i18n — English at root URLs, Ukrainian at `/uk/`
- On-prem modules written by parallel agents (~500 lines each), need Gemini adversary review

---
**Maintenance Rule**: Claude updates this file at session end or after completing modules.
