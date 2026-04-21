---
title: Session 12 handoff — pipeline_v4 bug fixes + batch wrapper landed; real batch run queued for operator
date: 2026-04-21
---

# TL;DR

Cleared three of the four items the session 11 handoff queued: the
retry-refresh-gaps bug, the batch wrapper (`scripts/pipeline_v4_batch.py`
+ 14 tests), and a previously-unknown Stage-2-skip bug that surfaced
during the batch dogfood dry-run. 4 commits on main. 26 pipeline_v4
family tests passing (was 10 last session).

The fourth item — the actual batch run against the 5
`ai-ml-engineering/ai-infrastructure` modules — is **queued for
operator execution**. The run mutates content, spawns several
pipeline_v3 subprocesses for citation injection, and will consume
real Gemini / Codex budget over an estimated 40-60 min wall clock
with 5 workers. The exact invocation is at the bottom of this
handoff.

**Next session's first task** (after the operator kicks off the real
batch and reviews output): verify the batch produced the expected
score lifts, then either (a) push the fixes through to
`on-premises/ai-ml-infrastructure/module-9.5-private-aiops` and the
12 `platform/disciplines/data-ai/aiops/` + `platform/toolkits/.../aiops-tools/`
modules which share the same "no citations" pattern, or (b) take the
loc_after accounting drift bug (#2 in session 11 handoff) since it's
the last known small bug before v4 is production-ready.

# What landed this session

## 4 commits on main (top-down)

| Commit | Scope |
|---|---|
| `2f460a0e` | fix(pipeline-v4): skip Stage 2 when only Stage-4 gaps remain |
| `fb9f9fc4` | feat(pipeline-v4): add scripts/pipeline_v4_batch.py — concurrent batch runner |
| `7ed19057` | fix(pipeline-v4): retry with rescore-refreshed gap list, not original |
| `b0a914a7` | docs(sessions): reflect dogfood commit 7dc2917e in session 11 handoff |

## 1. Retry-refresh-gaps fix (`7ed19057`)

`run_pipeline_v4` was calling `expand_module.expand_module` with
`result.gaps_before` on every retry iteration. That field is set once
at Stage 1 and never refreshed, so rescore results after Stage 3
were ignored on retry. Dogfood on module-1.2-ai-for-kubernetes-troubleshooting-and-triage
caught it in session 11 but the fix was deferred.

Introduced a local `current_gaps` in `run_pipeline_v4` that starts
from `result.gaps_before` and rotates to the rescore's gap list
before each retry. `gaps_before` stays intact as the "gaps at
pipeline start" telemetry field.

Strengthened `test_stage_3_retry` to assert the retry call receives
the refreshed gap list (not the original), and added
`test_stage_3_retry_uses_newly_surfaced_gap` — the dogfood scenario
directly: attempt 0 gets [thin, no_quiz], rescore returns
[no_exercise], retry must call expand with [no_exercise]. Both pass.

## 2. Batch wrapper (`fb9f9fc4`)

`scripts/pipeline_v4_batch.py` wraps `run_pipeline_v4` in a
ThreadPoolExecutor bounded by `--workers` (default 8). Each worker
claims its module via a per-module SQLite lease in `.pipeline/v2.db`
so two concurrent batches can't collide — stale leases (expired or
completed) get evicted inside the acquire transaction so repeat
runs don't accumulate dead rows.

Flags match the session 11 spec: `--track /prefix`, `--limit N`,
`--workers N`, `--min-score FLOAT`, `--max-score FLOAT` (default
4.0), `--dry-run`, `--skip-citation`, `--lease-seconds`.
`select_candidates()` pulls from `local_api.build_quality_scores`,
filters by path prefix + score bounds, sorts lowest-score-first so
the neediest modules run first. Exposed `quality_fetch` / `runner` /
`emit` seams for test injection.

Each per-module result is emitted as a JSON line to stdout and a
final `{"summary": ...}` aggregates processed count, outcome
breakdown, score delta total, and score delta average.

One concurrency bug surfaced while writing tests: concurrent threads
calling `_connect()` on a fresh SQLite DB raced on the CREATE TABLE
IF NOT EXISTS inside `executescript()`, producing "OperationalError:
database is locked" roughly 1-in-3 runs. Serialized schema init
behind `_INIT_LOCK` + per-DB-path sentinel set so each unique DB
gets one setup pass, subsequent connects skip straight to connecting.
Deterministic across 5 repeat runs afterward.

14 batch tests. Lease acquire/release/expire/complete contracts;
candidate filter-by-track / min-score / limit; happy-path batch
run; parallel-execution detector (asserts >= 2 workers run
simultaneously under a 50ms sleep); error-releases-lease path;
locked-module-skips path; no-candidates path; and CLI exit codes.

## 3. Stage-4-skip fix (`2f460a0e`)

Dogfood dry-run of the batch wrapper against the 5
`ai-ml-engineering/ai-infrastructure` modules revealed a second
latent bug in pipeline_v4: when the only gap is `no_citations` or
`no_diagram` (both in `expand_module._SKIP_REASONS` — handled by
Stage 4, not Stage 2), the pipeline burned its full retry budget on
no-op Stage 2 expansions and failed `rubric_stage_3_unmet` without
ever reaching Stage 4. Stage 4 would have been the one thing that
could have actually filled the gap.

Two-part fix:

- Added `expand_module.can_expand(gaps) -> bool` — True iff any gap
  has a Stage 2 handler. Lets callers distinguish "worth running
  Stage 2" from "skip straight to Stage 4".
- `pipeline_v4._run_pipeline_v4` consults `can_expand` twice: at
  entry (if `gaps_before` has no expandable gaps, skip Stage 2/3
  entirely) and inside the retry loop (if rescore's new gap list
  has no expandable gaps, break out instead of retrying). In both
  cases fall-through reaches Stage 4 with the module's prose
  intact.

Added `test_skip_stage_2_when_only_stage_4_gaps` (Stage 2 mock
raises if invoked, pipeline still reaches CITATION_V3) and
`test_break_to_stage_4_when_retry_gaps_become_stage_4_only`
(expand called once, retry_count stays 0 after rescore surfaces
only no_citations).

Verified on the 5-module dry-run post-fix: the 3 "no citations
only" modules finish `outcome=clean, stage_reached=DONE,
retry_count=0` with CITATION_V3 the only stage logged after
RUBRIC_SCAN. The 2 "no citations, no quiz" modules still cycle the
dry-run retry budget because dry-run Stage 2 is a no-op by design
(no content written) — under real execution Stage 2 fills no_quiz,
rescore narrows to `[no_citations]`, the new break kicks in, Stage
4 runs.

# Operator-run batch (queued)

The session 11 handoff's item 4 — "dogfood batch on the /ai thin-
module set" — is a content-mutating, API-cost-consuming operation.
Per `feedback_no_run_scripts.md`, pipeline mutations are operator-
run. Queuing the invocation here:

```bash
.venv/bin/python scripts/pipeline_v4_batch.py \
    --track ai-ml-engineering/ai-infrastructure \
    --limit 5
```

`--workers` defaults to 1 and is hard-capped at 3. Values above 3
clamp with a stderr WARNING. Gemini rate-limits on parallel calls
(429 MODEL_CAPACITY_EXHAUSTED) and pipeline_v4's internal Gemini
dispatches are the dominant cost; on top of the operator's usual
concurrent translations/reviews, even 3 is aggressive. The batch
wrapper's concurrency infra exists for cross-process lease safety
(resumable if the batch crashes, cannot collide with a second
terminal's batch), not for within-process parallelism.

I initially posted this invocation with `--workers 5` — that was
wrong and would have burned the Gemini quota on 429s. Landed a
`MAX_WORKERS=3` clamp + warning + test in the follow-up commit so
future invocations can't repeat the mistake. Added
`feedback_batch_worker_cap.md` to memory.

Candidate set verified (all 5 at score 1.5):

| Path | Primary issue |
|---|---|
| `ai-ml-engineering/ai-infrastructure/module-1.1-cloud-ai-services.md` | no citations |
| `ai-ml-engineering/ai-infrastructure/module-1.2-aiops.md` | no citations |
| `ai-ml-engineering/ai-infrastructure/module-1.3-vllm-sglang-inference.md` | no citations |
| `ai-ml-engineering/ai-infrastructure/module-1.4-local-inference-stack-for-learners.md` | no citations, no quiz |
| `ai-ml-engineering/ai-infrastructure/module-1.5-home-ai-operations-cost-model.md` | no citations, no quiz |

**Expected flow per module type:**

- Three "no citations only" (1.1, 1.2, 1.3): Stage 1 → skip Stage 2 →
  Stage 4 (pipeline_v3 subprocess, fills citations) → Stage 5 rescore.
  Per module: ~10-20 min wall clock.
- Two "no citations + no quiz" (1.4, 1.5): Stage 1 → Stage 2 (Gemini
  dispatch for quiz) → Stage 3 rescore, now `[no_citations]` only →
  break to Stage 4 → Stage 5. Per module: ~30-40 min.

With `--workers 5`, wall clock should land around 40-50 min end-to-
end.

**What to watch for during the run:**

- pipeline_v3 invocations produce a lot of stderr. `pipeline_v4_batch`
  captures the subprocess output via `_tail_lines` and includes only
  the last 50 lines in the JSONL event record. Full output is in
  pipeline_v3's own artifacts.
- Each module writes to `.pipeline/v4/runs/<module-flat>.jsonl` —
  tail those to watch progress live.
- Lease rows in `.pipeline/v2.db` table `v4_batch_leases` — if the
  batch crashes mid-run, stale rows older than `--lease-seconds`
  (1800s default) are evicted on re-acquire, so a second invocation
  is safe.
- Budget: citation_v3 internally uses Claude-adjacent dispatch +
  Gemini for research/verify; no_quiz uses Codex via expand_module.
  Neither path has a hard cap inside pipeline_v4 itself — budget
  enforcement lives in pipeline_v2's control plane but pipeline_v4's
  subprocess pipeline_v3 invocation bypasses that. **Watch the
  quota live.**

**If the operator prefers a safer first step:** run with
`--limit 1 --workers 1` on just module-1.1 first, verify score lift,
then expand. The batch wrapper is idempotent — re-running skips
already-completed leases and only re-runs failed ones.

# Tech debt still open

## Small

- **loc_after accounting drift** (`expand_module.py`). ExpandResult
  reports `loc_after: 258` but thin handler's own `actual_loc`
  counter reached 325 on attempt 1 in the session 11 dogfood.
  Cosmetic; telemetry-only.
- **Gemini CLI self-lints output** with markdownlint, adding ~30s
  per section. Harmless, aggregate cost matters only at batch scale.
- **Pre-existing test failure**:
  `tests/test_expand_module.py::test_expand_module_integration_shape_and_file_content`
  asserts `gaps_failed == []` but the integration fixture's module
  already has a quiz section, so `no_quiz` correctly fails with
  "section already exists for slot quiz". Failure predates session
  11. Fix is a one-line assertion change in the test to expect the
  known-collision, but it's not touching pipeline behavior.
- **Pre-existing pyright errors in pipeline_v4.py** lines 192, 219,
  311 — `float(entry.get("score"))` patterns where `.get()` is
  typed `Any | None`. Wrapped in try/except so runtime is safe. Six
  errors. Also predate session 11.

## Medium

- **Batch run against the other 17 critical-quality modules.** The
  same "no citations" pattern appears in 12 `platform/disciplines/data-ai/aiops/`
  + `platform/toolkits/observability-intelligence/aiops-tools/`
  modules and the on-premises/ai-ml-infrastructure/module-9.5.
  Once the `ai-ml-engineering` dogfood validates, the same batch
  command with a different `--track` prefix handles each tranche.

## Architectural (future)

- **#322 acceptance criteria item 6 not met**: "handoff notes". Partly
  addressed by this document and session 11's handoff; fully closing
  #322 probably wants a scripts/prompts/pipeline_v4_ops.md or similar.

# Known gotchas — new this session

- **`git stash pop` is not idempotent with old stash entries**. Mid-
  session I ran `git stash && pyright ... && git stash pop` to check
  whether pre-existing pyright errors were from my edits. The first
  `stash` saw no local changes ("No local changes to save") but the
  `pop` popped an *unrelated* pre-existing stash entry (`pre-vuln-fix
  stash`) that had been sitting on the stack. Recovered cleanly via
  `git restore --staged <files> && git checkout -- <files>`, and the
  pre-vuln stash was preserved in the pop-aborted state. Lesson:
  always `git stash list` before running stash commands, especially
  on shared worktrees. The old stash entry is still there
  (`stash@{0}: On main: session: pre-vuln-fix stash`).

- **Concurrent SQLite schema init can race**. Two threads both
  running `CREATE TABLE IF NOT EXISTS` via `executescript()` on a
  freshly-created DB file collided with "database is locked" about
  33% of the time. Serializing schema init behind a threading.Lock +
  per-path sentinel set fixed it. Row-level operations under WAL
  mode don't have this issue; only the initial DDL pass is
  race-prone.

# References

- This session's commits on main: `7ed19057`, `fb9f9fc4`, `2f460a0e`
  (+ the docs fix `b0a914a7` correcting session 11's handoff)
- Session 11 handoff: `docs/sessions/2026-04-21-session-11-handoff.md`
- Batch wrapper: `scripts/pipeline_v4_batch.py`
- Batch wrapper tests: `tests/test_pipeline_v4_batch.py`
- Operator-run batch invocation: see "Operator-run batch (queued)"
  section above.
