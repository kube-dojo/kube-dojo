# Session handoff — 2026-05-02 (session 4) — Day 3 KCNA proving batch LAUNCHED + dispatcher hardened per ab-discuss day3-388

> Picks up from `2026-05-02-3-388-day-2-pilot-complete.md`. This session: ran the deliberated `ab discuss day3-388` per the prior handoff's "What to do next session" plan, agents converged on **A2+B3+C3+D1** with two load-bearing dispatcher prerequisites, applied the prerequisites, built the B3 first bucket (28 KCNA modules), and launched the proving batch. Batch is running in background as of 14:48 UTC; expected wall ~5-6 hours single-lane. A2 multi-lane plumbing deferred until the proving batch validates the hardened single-lane path.

## Decisions and contract changes

### `ab discuss day3-388` — converged at round 2 on `A2+B3+C3+D1`

Channel: `day3-388` (created in `.bridge/messages.db`, 7 messages). Three agents (claude/codex/gemini) over 2 rounds, all signed `[AGREE]`. Per `.claude/rules/decision-card.md`, **convergence ⇒ no Decision Card emitted** — orchestrator just proceeds.

**Bundle agreed**:

- **A2** — Two parallel lanes (memory cap is 3, not a target; codex flagged this explicitly per `scripts/quality/pipeline.py:199-225` and `scripts/pipeline_v4_batch.py:10-18`). Gemini 429s are the bottleneck above 2, not worktree isolation.
- **B3** — Bucket by track AND difficulty; foundational tracks first as warm-up (KCNA/KCSA), CKS-class tracks last. Coherence review sparse — at track boundaries OR after the proving batch, NOT every 10-15 PRs (that would burn gemini quota for marginal value at n=9 drift evidence).
- **C3** — Orchestrator-classify NEEDS-CHANGES: trivial nits (<5 lines, no semantic risk) → inline fix; semantic failures → re-dispatch codex. C2 (regex auto-fix) rejected as premature — `feedback_advisory_vs_enforced_constraints.md` says enforce in code only after the pattern is stable; n=9 has not stabilized.
- **D1** — Day 3 = 30-50 module proving batch; D2/D3 (full 226 / 497) deferred until the proving batch lands cleanly. Codex 10x window expires 2026-05-17 (15 days remain) — comfortable.

### Two load-bearing dispatcher prerequisites — codex flagged, gemini ratified, claude agreed (commit `a63cdad3`)

**Prereq 1 — hard-coded REPO path** at `scripts/quality/dispatch_388_pilot.py:23` was `Path("/Users/krisztiankoos/projects/kubedojo")`. AGENTS.md violation. Under any A2 multi-lane setup where the dispatcher might run from a worktree, this would silently write to the wrong tree.

Fix: `REPO = Path(__file__).resolve().parents[2]` — derives from script location, works from primary OR any worktree.

**Prereq 2 — APPROVE_WITH_NITS verdict collapse** at lines 172-178. The original parser:
```python
if "VERDICT: NEEDS CHANGES" in upper or ...:
    verdict = "NEEDS CHANGES"
elif "VERDICT: APPROVE" in upper:    # ← matches "VERDICT: APPROVE WITH NITS" too
    verdict = "APPROVE"
```
PR #738 (Day 2 pilot) had `VERDICT: APPROVE WITH NITS` and got auto-merged with the redundant `k() { kubectl }` nit — the orchestrator caught it manually after the fact and pushed a follow-up commit. Under C3 we *want* nits to route to a fix-up lane, not auto-merge.

Fix: extracted `classify_verdict(text)` returning one of `APPROVE / APPROVE_WITH_NITS / NEEDS CHANGES / UNCLEAR`. Order in checks: NEEDS CHANGES → APPROVE_WITH_NITS → APPROVE. 8/8 unit-test fixtures pass including the PR #738 bug case (`tests` are inlined in this session's exploration; commit them later if the pattern is reused).

`main()` now routes:
- `APPROVE` → `merge_pr` + log `merged`
- `APPROVE_WITH_NITS` → `post_review_comment` + log `merge_held_nits` (no auto-merge — orchestrator triages)
- anything else → log `merge_held` (re-dispatch decision pending)

### Generalization — three new flags

Added argparse to `dispatch_388_pilot.py`:

- `--input PATH` — module list (one path per line, `#` comments). Default unchanged (`scripts/quality/pilot-2026-05-02.txt`).
- `--max N` — stop after N modules (0 = unlimited). Useful for canary runs.
- `--log PATH` — override JSONL log location. Default unchanged.

Backward-compatible: running with no args reproduces Day 2 pilot behavior (modulo the now-fixed verdict routing).

### B3 first bucket — KCNA, 28 modules at <2.0 critical-rubric

`scripts/quality/day3-bucket1-kcna.txt` enumerates all KCNA modules in critical state (sourced from `/api/quality/scores`). Single track, foundational, "lowest-difficulty" per claude-r2 — pedagogical drift is easiest to spot here, so review-coherence behavior gets its cleanest test before harder tracks land.

All 28 paths verified to exist on main.

## Batch launch (in flight)

```
.venv/bin/python scripts/quality/dispatch_388_pilot.py \
  --input scripts/quality/day3-bucket1-kcna.txt \
  --log logs/388_day3_bucket1_2026-05-02.jsonl
```

- **Started**: 2026-05-02 14:48:39 UTC (`pilot_start`)
- **Queue**: 28 modules
- **Lane**: 1 (single-lane; A2 plumbing deferred — see below)
- **Logs**: `logs/388_day3_bucket1_2026-05-02.jsonl` (events) + `logs/388_day3_bucket1_2026-05-02.stdout.log` (raw)
- **Expected wall**: ~5-6 hours at 11.6 min/module (Day 2 average)
- **First module**: `module-0.1-kcna-overview.md`

## A2 (two-lane) plumbing — deliberately deferred

The deliberation converged on A2 as the END-STATE; the IMMEDIATE state is single-lane because:

1. **`feedback_codex_dispatch_sequential.md` (memory)** — concurrent codex dispatches die silently with empty stdout/stderr. A2 needs two physically separate sandboxes, each with internally-serialized codex queues. That's real plumbing, not a flag flip.
2. **`npm run build` is a serialized shared resource** — repo policy forbids building from `.worktrees/*`. Day 2 codex spontaneously created `/private/tmp/kubedojo-build-388-pilot` to work around this. Under A2, two lanes contend for the primary checkout's build slot. Pilot data shows ~38s build / ~10 min cycle = ~6% serialized overhead at A2 — acceptable but not free.
3. **Day 2 single-lane shipped 9 modules in 90 min cleanly** — that pattern scales linearly to 28 modules in ~5.4 hours, well within a working day. The A2 wall-time savings (5.4 hr → ~3 hr) does not justify shipping unproven plumbing for the first proving batch.

If the proving batch lands cleanly, A2 plumbing is a clean follow-up: split the input file into 2 partitions, run two background processes with separate logs, share the cleanup script. Estimated half-day of work.

## What's still in flight

- **28 KCNA modules** running through the hardened dispatcher. Each module: codex (gpt-5.5, danger) → gemini cross-family review → APPROVE auto-merges, APPROVE_WITH_NITS holds for orchestrator triage, NEEDS CHANGES holds for re-dispatch decision.
- **Codex 10x window** expires 2026-05-17 (15 days remain).
- **3 unrelated codex worktrees** still on disk: `codex/issue-344`, `codex/391-status-page`, `codex/394-review-coverage-schema`. Out of scope this session; investigate if they're current or abandoned next time the queue is dry.

## Post-batch ritual (when `pilot_done` lands)

1. **Snapshot status**:
   ```bash
   gh pr list --search 'in:title 388' --state all --limit 50 \
     --json number,state,title -q '.[] | "  PR #\(.number) [\(.state)] \(.title)"' \
     | grep kcna
   ```
2. **Triage held PRs**:
   ```bash
   grep -E '"event": "merge_held' logs/388_day3_bucket1_2026-05-02.jsonl
   ```
   Per C3: trivial nits (<5 lines, no semantic risk) → inline fix-up commit + manual merge; structural failures → re-dispatch codex with the gemini review as the brief.
3. **Run generalized cleanup**:
   ```bash
   .venv/bin/python scripts/quality/cleanup_388_pilot.py
   ```
   Note: `cleanup_388_pilot.py` is currently hard-coded to `pilot-2026-05-02.txt`. Generalize to `--input PATH.txt` next session — same fix shape as the dispatcher generalization.
4. **Coherence sweep** (B3 boundary check) — dispatch one fresh codex+gemini pair to read the cumulative diff across the 28 KCNA modules. Question: any cross-module style drift, terminology inconsistency, or example-overlap?
5. **Decide on A2 plumbing OR move to KCSA bucket-2** — depends on proving-batch hold rate and orchestrator backlog.

## Cross-thread notes

**ADD:**

- **`ab discuss` pattern works** as designed — 2 rounds of 3 agents converged on A2+B3+C3+D1 in <2 min wall (codex r1 ~30s, gemini r1 ~30s, claude r1 inline, then converged in r2). The protocol forces explicit option-naming (`[OPTION X-N]` / `[AGREE]` / `[DEFER]`) which surfaces the disagreement on prerequisites that would otherwise have been buried in prose. Channel transcript: `ab channel tail day3-388 -n 20`.
- **Decision-Card-on-convergence rule held** — no card emitted because agents agreed. The user got direct progress instead of a stamp-and-wait card. Save cards for genuine multi-option output.
- **Codex bridge model defaults to `gpt-5.4`** when `ab discuss` is invoked without an explicit model override — visible in process listing during deliberation. The dispatcher's explicit `model="gpt-5.5"` override at `dispatch_388_pilot.py:108` works fine; the discrepancy is a bridge-default issue, not a dispatch issue. Worth a follow-up to align the bridge with `reference_codex_models.md`.
- **`classify_verdict()` is now a pure function** — extract for reuse if other dispatchers (cleanup, residuals) ever need to parse codex/gemini verdicts.

**DROP / RESOLVE:**

- "Build Day 3 volume-run dispatcher with `--input` + `--lanes`" — partially DONE (`--input` + `--max` + `--log` shipped; `--lanes` deferred with explicit rationale).
- "Add per-PR auto-fix-up pass (regex)" — REJECTED via deliberation (C2 was the wrong axis; C3 is right). C2 may revive after ~30 NEEDS-CHANGES cases stabilize the regex categories; explicit "not yet" decision.
- "Run Day 3 in batches of ~10-15 PRs per track" (B2) — REJECTED via deliberation. Coherence review at track boundaries / after-batch only (B3-style). Cheaper, same drift detection.

## Cold-start smoketest (executable)

```bash
# 1. Confirm batch is still running (or finished)
ls -la logs/388_day3_bucket1_2026-05-02.jsonl
tail -3 logs/388_day3_bucket1_2026-05-02.jsonl
/bin/ps -A | grep "dispatch_388_pilot.py" | grep -v grep   # 1 line if running, 0 if done

# 2. Per-module status
.venv/bin/python -c "
import json
events = [json.loads(l) for l in open('logs/388_day3_bucket1_2026-05-02.jsonl')]
for kind in ['module_start', 'merged', 'merge_held_nits', 'merge_held', 'module_skip', 'pilot_done']:
    n = sum(1 for e in events if e['event'] == kind)
    print(f'  {kind:20s} {n}')
"

# 3. Held PRs awaiting triage
grep -E '\"event\": \"merge_held' logs/388_day3_bucket1_2026-05-02.jsonl \
  | .venv/bin/python -c "
import json, sys
for line in sys.stdin:
    e = json.loads(line)
    print(f\"  PR #{e['pr']} [{e['verdict']}]  {e['module']}\")
"

# 4. Verifier check on merged modules (T0 expected)
.venv/bin/python -c "
import json, subprocess
events = [json.loads(l) for l in open('logs/388_day3_bucket1_2026-05-02.jsonl')]
merged = [e['module'] for e in events if e['event'] == 'merged']
for p in merged[:5]:
    subprocess.run(['.venv/bin/python', 'scripts/quality/verify_module.py',
                    '--glob', p, '--skip-source-check', '--out', '/tmp/check.jsonl', '--quiet'])
    rec = json.loads(open('/tmp/check.jsonl').readlines()[-1])
    print(f\"  {rec['tier']}  body={rec['metrics']['body_words']}  rp={rec['frontmatter'].get('revision_pending','?')}  {p}\")
"

# 5. Worktrees still around (cleanup script will remove these post-batch)
git worktree list | grep -c 388-pilot-module-

# 6. Build still green?
npm run build 2>&1 | tail -3
```

## Files modified this session

```
scripts/quality/
  dispatch_388_pilot.py            (modified — verdict parser fix, REPO portability, --input/--max/--log)
  day3-bucket1-kcna.txt            (new — 28 KCNA modules, B3 first bucket)
  cleanup_388_pilot.py             (unchanged — hard-coded to Day 2 pilot file; generalize next session)

.claude/rules/decision-card.md     (already on main from session 3 commit 8acb26e1; no edits this session)

logs/                              (gitignored)
  388_day3_bucket1_2026-05-02.jsonl       (new, batch in flight)
  388_day3_bucket1_2026-05-02.stdout.log  (new, batch stdout)

docs/session-state/
  2026-05-02-4-388-day3-bucket1-launched.md   (this file)

STATUS.md  (Latest handoff promotion at session end)
```

## Blockers

(none — proving batch running. Next session orchestrator triages held PRs from the queue, runs cleanup, decides on A2 plumbing vs straight to KCSA bucket-2.)
