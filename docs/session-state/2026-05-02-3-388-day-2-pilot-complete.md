# Session handoff — 2026-05-02 (session 3) — #388 Day 2 pilot COMPLETE (9/9 merged in ~90 min)

> Picks up from `2026-05-02-2-388-day-2-pilot-launched.md`. Pilot launched at 09:01 ran end-to-end in **~90 min wall time** (vs the 9-13 hour estimate in the prior handoff). All 9 modules cleared every #388 verifier gate, gemini cross-family review fired on every PR, 8/9 auto-merged, 1 needed orchestrator intervention to fix a dead source URL. Cleanup script ran clean: stale `revision_pending: true` flag fixed on 1 module, all 9 worktrees removed, branches deleted. Build passes, site healthy.

## Decisions and contract changes

### 9/9 pilot PRs merged (PRs #731 → #739)

| # | PR | Module | Track | Start body | End body | mwpp | Codex→merge time | Gemini verdict | Notes |
|---|----|--------|-------|------------|----------|------|------------------|----------------|-------|
| 1 | #731 | k8s/ckad/.../module-1.2-jobs-cronjobs | cert | 359 | 5260 | 73.5 | 9.3 min | APPROVE | GitLab incident framing |
| 2 | #732 | cloud/managed-services/module-9.9-api-gateways | cloud | 683 | 5106 | 69.0 | 16.0 min | APPROVE | Codex ran build + tests |
| 3 | #733 | cloud/gcp-essentials/module-2.7-cloud-run | cloud | 2005 | 5153 | 89.0 | 9.1 min | APPROVE | Knative + Cloud Run incident |
| 4 | #734 | platform/.../iac-tools/module-7.8-sst | platform | 346 | 5155 | 68.0 | 8.7 min | APPROVE | URL shortener exercise preserved |
| 5 | #735 | platform/.../observability/module-1.3-grafana | platform | 4774 | 5029 | 67.0 | 13.7 min | APPROVE | Tightest body=5029 (just 29 over floor) |
| 6 | #736 | linux/.../module-2.3-capabilities-lsms | fund | 592 | 5014 | (T0) | 12.7 min | APPROVE | 23 code blocks + 4 mermaid + 6 tables preserved |
| 7 | #737 | prerequisites/git-deep-dive/module-1-git-internals | fund | 2002 | 5060 | 74.0 | (manual) | **NEEDS CHANGES → fix → manual merge** | github.blog 404 → replaced with git-scm.com hash-function-transition |
| 8 | #738 | on-premises/security/module-6.4-compliance | onprem | 4985 | 5758 | (T0) | 12.9 min | APPROVE WITH NITS | Redundant `k() { kubectl }` after `alias k=kubectl` → orchestrator pushed 1-line fix |
| 9 | #739 | on-premises/operations/module-7.8-observability-at-scale | onprem | 4678 | 5327 | 83.0 | 10.2 min | APPROVE | Codex ran live source check + 166 tests |

**Pilot total wall time**: 09:01:17 → 10:31:25 = ~90 min for 9 sequential modules. Average 11.6 min per module (codex_dispatch_start → merged). My pre-pilot estimate of 9-13 hours was off by ~10x — codex on gpt-5.5 + danger mode is highly efficient at this work shape.

**Cumulative LOC change**: +1916 / -1144 across 9 modules. Plus 2 fix-up commits (URL replacement, alias nit).

### Cross-family review caught real bugs

Two of nine PRs needed orchestrator intervention based on gemini's review:

1. **PR #737** — gemini independently checked source URLs and found `github.blog/open-source/git/highlights-from-git-2-29/` returning 404 even though codex's "live source reachability check" had reported it OK. The blog post was deleted/moved (the 2020-pattern URL also redirects to a now-404 page). Orchestrator replaced with `git-scm.com/docs/hash-function-transition` (canonical primary doc on the same SHA-256 transition material), pushed fix-up commit, ran verifier (12 sources all 200 OK), merged.
2. **PR #738** — gemini caught a redundant `k() { kubectl "$@"; }` function defined immediately after `alias k=kubectl` in the hands-on lab. Function never wins (alias takes precedence interactively). Orchestrator pushed 1-line fix to main as a follow-up commit.

This is exactly the value cross-family review provides: codex's own verification missed both. Codex confirmed-OK + gemini-NEEDS-CHANGES → real issue.

### Codex calibration insight: tight to floor, dense by default

- Codex hit body_words_5000 with margin between 14 and 758 words. Median margin ~150 words. Codex calibrates to "floor + small buffer," not "blow past the floor for safety."
- Density gates (mean_wpp ≥ 30, median_wpp ≥ 28, short_rate ≤ 20%, max_run ≤ 2) were trivially satisfied. Observed mwpp range 67-89 — codex naturally writes 2-3x the density floor.
- Conclusion: **the density gates do not constrain codex.** The body_words_5000 floor is the binding constraint. If we lower the floor we get less content; if we raise it we get more. The gates describe codex's natural prose shape, not its expansion ceiling.

### Codex's `npm run build` workaround

When dispatched in `mode="danger"`, codex repeatedly created a temporary worktree at `/private/tmp/kubedojo-build-388-pilot` to run `npm run build` cleanly outside the per-PR `.worktrees/codex-388-pilot-*` worktree (because the project rule forbids building from `.worktrees/*`). This was unprompted — codex inferred the rule from CLAUDE.md and adapted. Worktree was reused across modules and cleaned up by the cleanup script.

### Frontmatter `revision_pending` clearing — codex was inconsistent

Codex got `revision_pending: false` right on 8 of 9 modules. Module 9.9 (PR #732) shipped with `revision_pending: true` still set — the verifier doesn't gate on this flag, so it slipped through. Cleanup script (`scripts/quality/cleanup_388_pilot.py`) caught it and pushed a 1-line fix in commit `53008fc2`.

The dispatcher prompt was updated mid-run (commit `7c144e0e`) to explicitly require flag-clearing for Day 3 — but the running Python process can't pick up source edits, so modules 3-9 ran on the unfixed prompt. Codex still got 7/8 right; pattern recognition kicked in.

### Cleanup script: `scripts/quality/cleanup_388_pilot.py`

Post-pilot housekeeping. Run after `pilot_done`:

1. Re-verify each pilot module on main (skip-source-check)
2. Clear stale `revision_pending: true` flags on modules that pass the verifier (won't touch modules that didn't merge)
3. Commit + push the flag-clear in one batch
4. Remove all pilot worktrees + delete pilot branches
5. Remove `/private/tmp/kubedojo-build-388-pilot`
6. Print per-module table

Has `--dry` flag for preview and `--no-fetch` to skip the initial git fetch. Used cleanly post-pilot; tighten on first re-use as needed.

## What's still in flight

Nothing from the pilot. Pipeline cleanly drained. Build passing.

## Day 3 volume run — recommendations from pilot data

- **Same dispatch pattern works**: `agent_runtime.runner.invoke(agent_name="codex", model="gpt-5.5", mode="danger", cwd=worktree)` + gemini cross-family review at `mode="workspace-write"` + auto-merge on APPROVE. Per-item sequential is fine.
- **Throughput is fine**: 12 min/module sequential = 5 modules/hour = 60-100 modules/day per single dispatcher. With 226 remaining (235 minus pilot), 1 lane finishes in ~5 days; 2 lanes in ~2.5 days. Codex 10x window expires 2026-05-17 (15 days remaining); window is comfortable.
- **Density thresholds: do not adjust**. They are trivially satisfied. The body_words_5000 floor is the only binding gate. Keep all gates as-is.
- **Source reachability: trust gemini, not codex**. Codex's "live source check" missed 1 dead URL out of ~100 sources across 9 modules (~1% miss rate). Always run `verify_module.py` *without* `--skip-source-check` post-merge OR add a gh comment recipe that auto-fixes dead URLs to a canonical replacement.
- **Track-level coherence review** (Codex's Day 1 consult recommendation): pilot was too small (9 modules across 5 tracks) to need this. Defer to volume run, run after every batch of ~10-15 PRs in the same track.
- **Per-PR review fatigue** is manageable: gemini reviewed 9 PRs in ~90 min with consistent rigor. No capacity flap on `gemini-3.1-pro-preview`. If volume run hits rate limit, fall back to `KUBEDOJO_GEMINI_REVIEW_MODEL=gemini-3-flash-preview` per existing memory.
- **One-line fixes are cheaper than re-dispatching codex**. PR #737 (URL fix) and PR #738 (nit fix) both took the orchestrator <2 min each. Only re-dispatch codex when the issue is structural (missing section, density failure) — for typos, dead URLs, redundant code lines, fix in-line.
- **Volume-run dispatcher**: extend `dispatch_388_pilot.py` to accept a `--input PATH.txt` arg + a `--lanes N` arg for parallelism. Add a per-PR auto-fix-up pass that runs gemini's verdict through a regex extractor for "URL X returns 404" / "remove Y line" patterns and applies them automatically.

## Cross-thread notes

**ADD:**

- `dispatch_388_pilot.py` works end-to-end in ~12 min/module on gpt-5.5 + danger mode. Pattern is sound for Day 3 volume run; just extend with `--input` + `--lanes` for batch + parallelism.
- Codex spontaneously creates `/private/tmp/kubedojo-build-388-pilot` to run `npm build` outside `.worktrees/`. Cleanup script removes it. Future dispatchers may want to pre-create + share this worktree across the run to save setup time.
- Cross-family review gives ~22% intervention rate (2/9). Both interventions were ≤2 min each (URL replace, 1-line removal). Budget orchestrator time accordingly: ~5 min/PR including review-reading + verification + auto-merge.
- The `cleanup_388_pilot.py` pattern (re-verify, fix stale flags, remove worktrees) is reusable for Day 3 — generalize to accept a list of merged module paths.

**DROP / RESOLVE:**

- "Pilot 8-12 modules — Day 2" — DONE (9 merged, all T0).
- "Switch Codex dispatch mode to `mode='danger'`" — DONE (ran clean across 9 dispatches; no sandbox refusals).
- "Volume run estimate: 9-13 hours per 9 modules" — REVISED to ~90 min per 9 modules (10x faster than estimate).

## Cold-start smoketest (executable)

```bash
# 1. Confirm all 9 pilot PRs merged
gh pr list --search 'in:title 388 pilot' --state all --limit 12 \
  --json number,state,title -q '.[] | "  PR #\(.number) [\(.state)] \(.title)"'
# expect 9 lines, all MERGED

# 2. All 9 pilot modules T0 on main
.venv/bin/python -c "
import json, subprocess
paths = open('scripts/quality/pilot-2026-05-02.txt').read().splitlines()
for p in paths:
    subprocess.run(['.venv/bin/python', 'scripts/quality/verify_module.py',
                    '--glob', p, '--skip-source-check',
                    '--out', '/tmp/check.jsonl', '--quiet'])
    with open('/tmp/check.jsonl') as f:
        rec = json.loads(f.readlines()[-1])
    print(f\"  {rec['tier']}  body={rec['metrics']['body_words']}  rp={rec['frontmatter'].get('revision_pending','?')}  {p}\")
"

# 3. No pilot worktrees lingering
git worktree list | grep -c 388-pilot   # expect 0

# 4. /private/tmp build worktree gone
ls /private/tmp/kubedojo-build-388-pilot 2>&1 | head -1   # expect "No such file"

# 5. Build still healthy
npm run build 2>&1 | tail -3   # expect "[build] Complete!" + 2018+ pages
```

## Files modified this session

```
scripts/quality/
  dispatch_388_pilot.py            (modified: added revision_pending: false to brief)
  cleanup_388_pilot.py             (new — post-pilot housekeeping)
  pilot-2026-05-02.txt             (unchanged — 9 paths)

logs/                              (gitignored)
  388_pilot_2026-05-02.jsonl       (full run log — useful audit trail)
  388_pilot_2026-05-02.stdout.log  (stdout)
  388_pilot_tracking.md            (per-module live tracking, useful artifact)

src/content/docs/
  k8s/ckad/part1-design-build/module-1.2-jobs-cronjobs.md         (PR #731)
  cloud/managed-services/module-9.9-api-gateways.md               (PR #732 + cleanup commit)
  cloud/gcp-essentials/module-2.7-cloud-run.md                    (PR #733)
  platform/toolkits/infrastructure-networking/iac-tools/module-7.8-sst.md             (PR #734)
  platform/toolkits/observability-intelligence/observability/module-1.3-grafana.md    (PR #735)
  linux/foundations/container-primitives/module-2.3-capabilities-lsms.md              (PR #736)
  prerequisites/git-deep-dive/module-1-git-internals.md           (PR #737 + URL fix-up)
  on-premises/security/module-6.4-compliance.md                   (PR #738 + alias nit fix)
  on-premises/operations/module-7.8-observability-at-scale.md     (PR #739)

docs/session-state/
  2026-05-02-3-388-day-2-pilot-complete.md   (this file)

STATUS.md  (Latest handoff promotion at session end)
```

## Use `ab discuss` for high-leverage decisions (agreed end-of-session)

User flagged that we underutilize `ab discuss --with claude,codex,gemini` — the agent bridge supports multi-agent rounds (default 2, cap 4). We've been treating ab as point-to-point dispatch (codex writes, gemini reviews, I merge) and missing real quorum reasoning.

**Scope agreement**: use it for high-leverage decisions only — architecture choices, threshold freezes, contested NEEDS CHANGES — NOT per-PR review (would 3x the latency we just measured at 12 min/module).

**Voting machinery**: do NOT build quorum/tie-break code yet. Start with a prompt convention — each agent ends its turn with `VOTE: YES|NO|ABSTAIN` + one-sentence reason, claude extracts the verdict. Add code only after 3-5 real discussions reveal where free-form actually fails.

**First test next session**: `ab discuss day3-388 --with claude,codex,gemini --max-rounds 3` on Day 3 volume-run architecture (lane count, batch shape, coherence-review cadence). That's the cleanest signal — a decision affecting 226 modules where a single-agent blind spot is genuinely costly.

## Blockers

(none — Day 3 volume run ready to plan + execute. First action: ab discuss session on Day 3 architecture per the agreement above.)
