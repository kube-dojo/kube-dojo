# Spec v2: v2 Pipeline — Budget-Aware Job Queue

*Revised after parallel design review by Codex and Gemini (2026-04-14).*

Both reviewers independently identified THE critical flaw in v1 of this spec: **budget enforcement was not atomic with dispatch**. That is now fixed in this v2 via atomic SQLite reservations (see §Budget Reservation). Other agreed changes: expanded event set, rewrite escalation triggers, dead-letter queue, migration reordering, global kill-switch, human-in-the-loop state.

## Problem with v1

After a day of patching, we've confirmed v1 is the wrong shape:
- Phase state drifts (hit 4 distinct phase-drift bugs this session)
- Synchronous/serial (4min/write × 816 × 2-3 rewrites = ~1 week runtime)
- No cost tracking, no rate-limit awareness (pipelines just crash when budget runs out)
- Full rewrites when targeted patches would do (every fix regenerates 65K chars)
- Monolithic reviewer prompt (one giant call instead of per-check micro-calls)
- Fact ledger as blocking gate instead of helpful tool
- 300MB linear logs — grep-hostile, no per-module history (until #236)

Every convergence bug fix has been symptom-treatment. Time for root-cause fix.

## Goal

Rebuild as:
1. **Append-only event log** — attempts are immutable records, state is derived
2. **Budget-aware job queue** — per-model concurrency caps + weekly/hourly budget guards
3. **Worker pools** — one per phase type, independently scalable
4. **Targeted-patch-first loop** — full rewrite is the exception, not default
5. **Model tiering** — Flash for simple, Pro for writes, Claude for bounded patches
6. **Structured everything** — JSON events, JSON reviewer feedback, JSON-validated LLM outputs

## Budget awareness (user's hard constraint)

Before anything else: **the pipeline must never get the user rate-limited**.

### Budget config file

`.pipeline/budgets.yaml`:
```yaml
models:
  claude-sonnet-4-6:
    max_concurrent: 2                   # hard cap
    weekly_calls: 500                   # hard cap — pipeline HALTS at threshold
    weekly_budget_usd: 40.00            # hard cap
    hourly_calls: 50                    # soft cap (backs off)
    cooldown_after_rate_limit: 600      # seconds after 429 before resuming

  gemini-3.1-pro-preview:
    max_concurrent: 3
    weekly_calls: 2000
    hourly_calls: 200
    cooldown_after_rate_limit: 300

  gemini-3-flash-preview:
    max_concurrent: 5
    weekly_calls: 10000                 # Flash is cheap, spend freely
    hourly_calls: 800

defaults:
  max_concurrent: 1                     # if model not in config, serialize
  weekly_calls: 100
```

### Budget reservation (atomic — THE critical design point)

Both Codex and Gemini flagged this as the spec-breaking weak spot in v1. Fix:

**One SQLite transaction does EVERYTHING at dispatch time:**
```
BEGIN EXCLUSIVE;
  -- 1. Lease a job from the queue (SKIP LOCKED semantics via row state flip)
  SELECT id FROM jobs WHERE state='pending' AND model=?
    ORDER BY priority, enqueued_at LIMIT 1;
  UPDATE jobs SET state='leased', leased_by=?, leased_at=? WHERE id=?;

  -- 2. Reserve a concurrency slot (enforced by unique constraint on active_leases)
  INSERT INTO active_leases (model, job_id, lease_id, expires_at);
  -- Unique index on (model, slot_number) — raises IntegrityError if full

  -- 3. Reserve estimated budget (calls + dollars)
  SELECT SUM(reserved_calls), SUM(reserved_usd) FROM reservations
    WHERE model=? AND window='hourly';
  -- If reservation + estimate > cap: ROLLBACK, worker pauses

  INSERT INTO reservations (lease_id, model, window, reserved_calls,
                             reserved_usd, reserved_at);

  -- 4. Emit event
  INSERT INTO events (type='job_leased', lease_id, model, job_id, at);
COMMIT;
```

**Post-call reconciliation** (for dollar caps — actual cost arrives after API response):
```
BEGIN;
  INSERT INTO usage (lease_id, model, actual_calls=1, actual_usd=?,
                      tokens_in, tokens_out, completed_at);
  DELETE FROM reservations WHERE lease_id=?;
  DELETE FROM active_leases WHERE lease_id=?;
  INSERT INTO events (type=? 'attempt_succeeded'|'attempt_failed'|
                             'attempt_rate_limited', ...);
COMMIT;
```

**Why this works:**
- Two workers racing on the same budget: one wins the transaction, the other gets IntegrityError/ROLLBACK and retries or pauses
- Hard cap enforcement is atomic (not check-then-act)
- Post-hoc dollar reconciliation catches overruns; next reservation query sums actuals + pending reservations together
- Crash recovery: lease has `expires_at`; watchdog releases abandoned leases; idempotency keys prevent double-charge

### Budget tracker (built on the reservation model)

- `.pipeline/usage.db` (SQLite) with tables: `jobs`, `active_leases`, `reservations`, `usage`, `events`
- Unique index `(model, slot_number)` on `active_leases` enforces `max_concurrent` at the DB level
- Rolling windows: hourly = `WHERE reserved_at > datetime('now', '-1 hour')` + same for usage
- Weekly window: **UTC-based**, starts Monday 00:00 UTC (explicit timezone per Codex)
- Budget check = atomic query inside the same transaction as lease

### Cost estimation (for reservations)

- Approximate cost = `tokens_in_estimate * model_price_in + tokens_out_estimate * model_price_out`
- Token estimate: use `tiktoken` or provider-native counters on the prompt before dispatch
- For output: reserve conservatively (max tokens setting); refund delta post-response

### Global kill-switch (per Gemini)

If any model hits its hard weekly cap, config chooses policy:
- `PAUSE_ALL` — halt all workers, surface to user (safest)
- `DOWNGRADE` — route that phase to next tier (e.g., Pro → Flash for reviews)
- `CLAUDE_ONLY_PAUSE` — Claude-bound patch worker pauses, other workers keep running (default for user's setup)

### HTTP 429 handling

- Increments `rate_limit_events` counter for the model
- Starts cooldown: `cooldown_at = now + cooldown_seconds`
- ALL workers on that model pause until `cooldown_at`
- If 3x 429s in 10 minutes: exponential backoff (cooldown doubles each time)
- Emit event `attempt_rate_limited` with full context

### Why this is FIRST-class

v1 tracked nothing. v2 refuses to dispatch without clearance from the atomic reservation transaction. This makes the user's "2-3 parallel" constraint trivial to enforce: set `max_concurrent: 2` and the DB will REFUSE a third concurrent lease even if 10 workers race.

## Architecture

```
┌──────────────────┐
│   jobs queue     │  SQLite jobs table: id, module_key, phase, attempt, state
│   (.pipeline/    │  Immutable attempts table: attempt_id, inputs, outputs,
│    jobs.db)      │                              verdict, cost, duration
└────────┬─────────┘
         │
         ├─── write-worker  (gemini-pro, max_conc=1)
         ├─── review-worker (gemini-pro, max_conc=2)
         ├─── patch-worker  (claude-sonnet, max_conc=1) ← user's weekly constraint
         ├─── check-worker  (deterministic, max_conc=10)
         └─── ledger-worker (gemini-flash, max_conc=3)
         
         All workers consult budget tracker before each job.
```

### State = derived from events

No mutable `phase` field. Instead:
- Current state computed by folding events for a module
- Crash recovery = replay events
- Debugging = filter events
- "Why did this module fail?" = timeline of events

### Event taxonomy (expanded per Codex review)

**Module progress events**:
- `module_created`
- `attempt_started` (phase, model, lease_id)
- `attempt_succeeded`
- `attempt_failed`
- `attempt_timed_out`
- `attempt_rate_limited`
- `check_passed`
- `check_failed`
- `patch_apply_failed`
- `patch_degraded` (patch fixed A but introduced B, per Gemini)
- `rewrite_escalated` (targeted → severe)
- `done`
- `paused` (user or budget)
- `needs_human_intervention` (per Gemini — preserves work when auto-fix fails)
- `module_dead_lettered` (abandoned after max attempts)

**Control-plane events** (queue state, per Codex):
- `job_enqueued`
- `job_leased`
- `job_released`
- `dispatch_blocked_budget`
- `model_cooldown_started`
- `model_cooldown_ended`
- `worker_paused` / `worker_resumed`
- `kill_switch_triggered` (global or per-model)

### Immutable attempts

Every LLM call produces one immutable `attempt` record:
```
attempt_id, module_key, phase (write|review|patch|check),
model, prompt_hash, prompt_version,
input_content_hash, output_content_hash,
verdict (pass|fail|timeout|rate_limited),
failed_check_ids (list),
cost_usd, tokens_in, tokens_out, duration_ms,
started_at, completed_at
```

Retries create new attempts. Never modified after write. This replaces:
- `errors[]` append list (which accumulated stale errors forever)
- `checks_failed[]` (which was mutated)
- `sonnet_anchor_failures` counter (which never reset)
- `check_failures` counter (same problem)
- All the `ms.pop()` calls scattered through run_module

## The write-once + targeted-patch loop

```
1. WRITE (Gemini Pro, 1 attempt)
   └─> output content_hash_A

2. CHECK_PRE (deterministic, in-process, free)
   ├── markdownlint, yamllint, frontmatter schema, structural regex
   └── if fail: PATCH (structured fix, no LLM) or back to WRITE

3. REVIEW (Gemini Flash for simple checks, Pro only for DEPTH/WHY)
   └─> structured JSON: {failed_checks: [{id, line_range, evidence, fix_hint}]}

4. PATCH (Claude Sonnet, targeted edits only)
   ├── receives structured failures, not the whole module
   ├── returns bounded diffs (context-locked anchors)
   └── deterministic apply — if 100% apply, re-review; else escalate to severe

5. REVIEW again (confirmation only, Flash tier)
   └─> done or escalate
```

### Rewrite escalation triggers (per Codex — targeted patches alone won't converge for structural defects)

Automatic escalation from PATCH → severe rewrite when ANY of:
- PATCH apply failed (anchor not found, conflicting edits)
- Reviewer JSON shows `>3 dispersed failure ranges` (scattered across module)
- Overlapping edits detected
- `>2 patch rounds` without convergence
- Reviewer feedback contains `"requires reorganization"` or `"outline"` keywords
- Coverage gaps across `>N` sections (structural, not local)
- Inconsistent voice / tone flagged
- Patch introduces `patch_degraded` event (new issue emerged)

After `>3 rewrite attempts`: module transitions to `needs_human_intervention` (work preserved, not lost).

**Expected effect**: 1 write + 1-2 patches per module, 60% of review calls hit Flash not Pro. Cost drops ~70%. Convergence time drops ~5x.

## Model tiering (cost/speed optimization)

| Phase | Cheap (Flash) | Standard (Pro) | Expensive (Claude) |
|-------|:---:|:---:|:---:|
| Fact extraction | ✅ | — | — |
| Check: structural | free (no LLM) | — | — |
| Check: pedagogical | ✅ simple | ✅ DEPTH/WHY | — |
| Write (initial draft) | — | ✅ | — |
| Write (severe rewrite) | — | ✅ | — |
| Patch (targeted edit) | — | — | ✅ |
| Patch planning | ✅ | — | — |

Budget config per model lets the user shift expensive work under cap.

## Pre-flight deterministic checks (zero LLM cost)

Run BEFORE calling any LLM in REVIEW phase:
- `markdownlint` — formatting
- `yamllint --config k8s-relaxed` — multi-doc YAML, indentation
- Frontmatter schema (required fields, slug format)
- Regex: no leaked secrets (integrates with #237 work)
- Regex: no deprecated K8s APIs
- Link check (already exists, just gate earlier)

If any ERROR-severity fails: don't bother calling the LLM reviewer. Go straight to PATCH with the deterministic failure list.

**Estimated savings**: ~30% of review calls avoided (pre-flight catches most).

## Fact ledger as a tool

- Extract claims from module content (Flash tier, cheap)
- Cross-check against upstream docs (cached, reused across modules)
- **Inject top-K relevant facts into the writer prompt** (not blocking; gives the writer ground truth)
- Only flag `data_conflict` if writer's output contradicts ledger AND reviewer confirms
- No more dead-end `data_conflict` phase requiring `--refresh-fact-ledger`

## Observability (first-class, not retrofit)

### Required metrics

- `attempts_per_module` histogram (target p50=2, p95=4)
- `rewrite_vs_patch_ratio` (target: patches > rewrites by 3:1)
- `fail_reason_histogram` by check_id (which checks fail most?)
- `cost_per_module_usd` (total spent to reach DONE)
- `duration_per_phase_p50_p95_ms`
- `rate_limit_pauses_per_hour` (are we actually budget-constrained?)
- `model_utilization` (% of max_concurrent actually used per model)
- `stuck_modules` (no state change >X minutes)

### CLI commands

```
pipeline status                         # Overall health dashboard
pipeline show <module-key>              # Event timeline for one module
pipeline show flapping                  # Modules with >4 attempts
pipeline show stuck                     # No state change in >30 min
pipeline show most-expensive            # Modules that burned the most money
pipeline show budget                    # Current usage vs caps per model
pipeline show convergence-report        # Histograms, ratios, trends
```

## Migration plan (reordered per Codex — control plane first, not last)

v1 continues to run. v2 builds alongside. The FIRST week delivers the real control plane — not just an observer — because the whole spec hinges on atomic dispatch.

1. **Week 1 — Control plane (load-bearing)**:
   - Atomic queue lease + budget reservation (SQLite, transaction-bounded)
   - Event log with full event taxonomy
   - Lease expiry + watchdog (recover abandoned leases)
   - Idempotency keys for crash recovery
   - Kill/restart stress tests (kill -9 mid-dispatch, verify no double-charge)
   - `pipeline show budget` CLI
   
2. **Week 2 — Deterministic checks + review worker**:
   - Pre-flight linters (markdownlint, yamllint, frontmatter schema, regex gates)
   - Review worker on Gemini Flash for simple checks, Pro for escalated
   - Structured JSON reviewer output with schema validation
   - Compare review latency/cost vs v1 on 20 modules

3. **Week 3 — Patch worker + rewrite fallback policy**:
   - Claude Sonnet bounded patch worker
   - Rewrite escalation triggers (from §Rewrite escalation)
   - `needs_human_intervention` terminal state
   - Dead-letter queue

4. **Week 4 — Write migration + cutover**:
   - Migrate WRITE phase to v2 worker
   - A/B test 50 modules: v2 vs v1, measure convergence + cost
   - Cutover if v2 converges faster OR cheaper with equal quality
   - v1 archived read-only

Safe checkpoints: each week's deliverable is independently useful. v1 keeps running throughout.

## Acceptance Criteria

### Budget control (user's hard requirement)
- [ ] `.pipeline/budgets.yaml` config with per-model `max_concurrent`, `weekly_calls`, `hourly_calls`, `weekly_budget_usd`, `cooldown_after_rate_limit`
- [ ] Budget tracker (SQLite) enforces caps before EVERY dispatch
- [ ] Hourly cap hit → worker pauses, doesn't fail
- [ ] Weekly cap hit → worker halts, user notified
- [ ] HTTP 429 → model cooldown for configured seconds
- [ ] Default `max_concurrent: 1` for any model not in config

### Job queue
- [ ] SQLite `.pipeline/jobs.db` with jobs and attempts tables
- [ ] Workers pull from queue, dispatch to model with budget clearance
- [ ] Immutable attempts (no UPDATE on attempts table, only INSERT)
- [ ] Crash recovery = replay events to compute state

### Worker pools
- [ ] One worker pool per phase: write, review, patch, check, ledger
- [ ] Each pool has its own model binding + concurrency cap
- [ ] Pools run independently (check-worker not blocked by write-worker)

### Targeted-patch-first loop
- [ ] Default path: write → pre-flight → review → patch → re-review → done
- [ ] Full rewrite only triggered on: catastrophic PRES/COV failure, or malformed output
- [ ] Patches use structured edits, not full-content regeneration

### Model tiering
- [ ] Flash used for: fact extraction, simple checks, confirmation reviews
- [ ] Pro used for: first writes, DEPTH/WHY checks, severe rewrites
- [ ] Claude used for: targeted patches only
- [ ] Routing per spec table, configurable

### Pre-flight checks
- [ ] markdownlint, yamllint, frontmatter schema, leaked-secret regex, K8s API regex, link check
- [ ] Run before LLM review; failures route directly to PATCH

### Fact ledger
- [ ] Non-blocking: injected into writer prompt, never a hard gate
- [ ] No `data_conflict` phase

### Observability
- [ ] Event log: every transition emits one JSON event
- [ ] CLI: `pipeline show <module>`, `show flapping`, `show stuck`, `show most-expensive`, `show budget`, `show convergence-report`
- [ ] Per-module audit log (carries forward from #236)
- [ ] Metrics: attempts/module, rewrite:patch ratio, cost/module, rate-limit pauses, model utilization

### Tests
- [ ] Budget tracker enforces caps under concurrent load (stress test)
- [ ] Job queue survives kill -9 mid-dispatch (crash recovery test)
- [ ] Immutable attempts — cannot be UPDATE'd, only INSERT
- [ ] Targeted patch path converges 1 module end-to-end faster than v1
- [ ] Model tiering: review of a simple "clean" module uses Flash, not Pro

### Migration
- [ ] v1 and v2 can coexist (different state dirs)
- [ ] Feature flag switch per module or per track
- [ ] No data migration required (v2 starts fresh)

## Non-goals

- No real-time dashboard UI (JSON events + CLI is enough)
- No distributed workers (single machine)
- No custom model implementations (use existing dispatch.py + agent bridge)
- No fact-grounding rewrite (reuse existing ledger machinery, just change how it's used)

## Open questions

1. Job queue storage: SQLite (simple) vs JSON files (grep-able) vs Redis (external dep). Proposal: SQLite.
2. Event log format: append-only JSONL file vs SQLite events table. Proposal: both — JSONL for debugging, SQLite for queries.
3. Pre-flight linter runtime: pure Python vs subprocess to `markdownlint-cli2`. Proposal: subprocess (industry-standard rules).
4. Backoff strategy on 429: exponential, fixed, or adaptive? Proposal: fixed cooldown per spec (simple, predictable).
5. How do we handle Claude weekly budget exhaustion mid-run? Proposal: pause patch-worker, let write/review/check continue; user resumes when budget refreshes.

## Workflow

1. [x] Spec v1 written
2. [x] Codex + Gemini design review (parallel) — both flagged atomic reservation as THE weak spot
3. [x] Spec revised to v2 incorporating:
   - Atomic budget reservation in SQLite transaction
   - Post-call reconciliation for dollar caps
   - Expanded event taxonomy (module + control-plane)
   - Rewrite escalation triggers
   - `needs_human_intervention` terminal state
   - Dead-letter queue
   - Global kill-switch policy
   - Explicit week boundary (UTC, Monday 00:00)
   - Idempotency keys
   - Migration reordered: control plane in week 1, not last
4. [ ] GH issue with ACs (next)
5. [ ] Implementation in phases (per Migration plan)
6. [ ] Gemini reviews each phase → Claude reviews → merge
7. [ ] A/B test on 50 modules
8. [ ] Cutover

## Design Review Sign-Off

- [x] **Codex** (2026-04-14): Flagged atomic budget enforcement as the one flaw that would kill the rewrite. Fixed in v2.
- [x] **Gemini** (2026-04-14): APPROVE with changes — required token reservation system, global kill-switch, human-in-the-loop. All addressed in v2.
