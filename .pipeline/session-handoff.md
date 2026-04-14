# Session Handoff — 2026-04-14 evening

> **READ THIS FIRST.** Picks up where the previous session ended. All work pushed to `main` at commit `d6311ee6`. Nothing currently running in the background.

## What landed today (in commit order)

1. **#235 — v1 pipeline convergence fixes** (Codex+Gemini, 18 bugs)
   - Atomic state writes, dynamic concurrency, stale resume metadata cleared
   - `cmd_reset_stuck` added with regex-based error matching
   - 126 v1 tests pass

2. **#236 — Per-module review audit log**
   - `.pipeline/reviews/{module_key}.md` with full reviewer feedback
   - `fcntl.flock` cross-process safe, atomic writes, reverse-chronological
   - 7 new tests (133 total)

3. **#237 — Decoupled lab pipeline + LAB removed from module review**
   - Module reviewer no longer evaluates inline "Hands-On Exercise" sections
   - New `scripts/lab_pipeline.py` operates on `~/projects/kubedojo-labs/`
   - Bi-directional metadata: `lab:` in module frontmatter, `module:` in lab `index.json`
   - `--static` (no Docker) and `--exec` (Docker) tiers
   - End-to-end demo: fixed `cka-1.1-control-plane` lab, REJECT severe → APPROVE clean
   - 8 new lab tests (141 total)

4. **#238 — INVALID_YAML multi-doc fix**
   - `yaml.safe_load` → `yaml.safe_load_all` accepts K8s-style multi-doc YAML

5. **Reset-stuck migrates stale `phase=write` → `phase=review`**
   - 93 modules left over from old `--write-only` runs no longer get rewritten

6. **Audit log Plan field no longer truncated at 500 chars**
   - Full reviewer feedback now visible in WRITE entries

7. **#239 — v2 pipeline (Weeks 1-4 ALL complete)**
   - `scripts/pipeline_v2/` — control plane, review/patch/write workers
   - `.pipeline/v2.db` (SQLite, WAL mode) replaces mutable phase state
   - **Atomic budget reservation** in single SQLite transaction
   - **Dynamic `max_concurrent`** — edit `.pipeline/budgets.yaml` or `pipeline budget set <model> max_concurrent <N>`
   - Model tiering: Flash for simple checks, Pro for writes/deep, Claude for bounded patches
   - Pre-flight linters (markdownlint, yamllint, secrets, K8s API) skip LLM call when fail
   - Targeted-patch-first loop with content slicing (NOT full module to LLM)
   - Rewrite escalation triggers + `needs_human_intervention` dead-letter
   - HTTP 429 cooldown + 20% token buffer + global kill-switch policies
   - 38 v2 tests (41 total = 38 v2 + 3 lab) — full v1+v2 test suite at **179 tests**
   - Reviewed iteratively by Codex (impl) + Gemini (catches bugs Codex misses)

8. **Anti-compaction harness** (`.claude/hooks/context-monitor.sh`)
   - PostToolUse hook fires after every tool, estimates context vs `autoCompactWindow`
   - Tiers: 75% heads-up, 85% critical, 95% emergency
   - `autoCompactWindow: 1000000` (max) for runway
   - Source in `claude_extensions/hooks/`, deploys via `deploy.sh`

## Current pipeline state

```
.venv/bin/python scripts/v1_pipeline.py status
```

Last known: 102 pass, 1 fail, 431 in progress, 282 not started (816 total). Numbers may have moved if v1 pipelines ran briefly.

## What's NOT running

- No v1 pipeline processes (`pgrep -fl v1_pipeline` empty)
- No v2 workers
- No background Codex/Gemini agents

## Choose your next move (3 paths)

### Path A — v2 cutover (recommended; this is what we built today)
```bash
# 1. Migrate v1 state into v2 (idempotent, safe to re-run)
.venv/bin/python scripts/pipeline_v2/cli.py migrate-v1 \
  --state /Users/krisztiankoos/projects/kubedojo/.pipeline/state.yaml

# 2. Start workers (separate terminals or & background)
#    Adjust max_concurrent in .pipeline/budgets.yaml first if needed
.venv/bin/python scripts/pipeline_v2/cli.py write-worker loop &
.venv/bin/python scripts/pipeline_v2/cli.py review-worker loop &
.venv/bin/python scripts/pipeline_v2/cli.py patch-worker loop &

# 3. Watch progress
.venv/bin/python scripts/pipeline_v2/cli.py status
.venv/bin/python scripts/pipeline_v2/cli.py show budget
```

### Path B — A/B test v2 vs v1 first (safer — 50 modules to validate convergence/cost)
```bash
.venv/bin/python scripts/v2_ab_test.py --count 50 --modules cloud
# Reports convergence, estimated cost, wall time per cohort
```

### Path C — Stick with v1 for now (all v1 fixes from today are live)
```bash
# Reset stale modules first (also handles stale phase=write)
.venv/bin/python scripts/v1_pipeline.py reset-stuck

# Resume — v1 fixes mean modules converge faster, no LAB rewrites
KUBEDOJO_MAX_CLAUDE_CALLS=100 .venv/bin/python scripts/v1_pipeline.py e2e \
  cloud linux platform on-prem specialty prereqs --no-translate \
  >> /tmp/wave-restart.log 2>&1 &
```

## Open GH issues (in priority order)

| # | Title | Status |
|---|---|---|
| 239 | v2 pipeline budget-aware job queue rewrite | All 4 weeks merged; ready for cutover |
| 235 | Pipeline convergence | All fixes merged |
| 236 | Per-module review audit log | Closed |
| 237 | Decoupled lab pipeline + LAB removal | Closed |
| 238 | INVALID_YAML multi-doc | Closed |

## Important files

- `.pipeline/spec-v2-pipeline.md` — v2 spec (post-review v2)
- `.pipeline/budgets.yaml` — runtime-adjustable concurrency caps per model
- `.pipeline/state.yaml` — v1 state (still source of truth until cutover)
- `.pipeline/v2.db` — v2 SQLite (created on first migrate-v1 run)
- `STATUS.md` — high-level project status
- `.claude/hooks/context-monitor.sh` — anti-compaction warning system

## Things to know about the hook

- It runs after every tool call, so you'll see warnings in this/future sessions
- If it warns and you're in the middle of something — finish that one task, then update this handoff and `/exit`
- To temporarily silence: set env var `CLAUDE_NON_INTERACTIVE=1` for that command

## How to start next session

```bash
cd /Users/krisztiankoos/projects/kubedojo
claude --continue   # if you want to resume context (NOT recommended — heavy)
# OR (recommended):
claude              # fresh session — first thing: read this file
```

In the new session, paste this prompt:
> Read `.pipeline/session-handoff.md` and brief me on where we are.

That gives the new session full context for ~3KB instead of replaying our 3.5MB conversation.
