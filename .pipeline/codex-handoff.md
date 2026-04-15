# Codex Handoff — 2026-04-15

> Claude is out of usage. Codex takes over. Read this fully before acting.

## What you are taking over

The KubeDojo v2 pipeline needs to be completed and started. We got partway through — the architecture was redesigned but the code changes are NOT yet applied to the repo. You need to apply them, test, and start the workers.

## Current repo state

- Branch: `main`, clean (last commit `8e1ab185`)
- v2 migration already ran: 562 modules in `.pipeline/v2.db` (102 done, 399 review queue, 53 write queue, 8 manual triage)
- Workers NOT yet started — nothing is running
- Tests: `scripts/tests/` — 179 passing as of last session

## Architecture decisions (FINAL — do not revisit)

| Worker | Model | Dispatch mode |
|--------|-------|---------------|
| Review | `gpt-5.3-codex-spark` (or `codex` default) | `codex --search exec --sandbox read-only` (internet ON for fact-checking) |
| Patch | `gpt-5.4` | `codex exec --dangerously-bypass-approvals-and-sandbox` (full write) |
| Write | `gemini-3.1-pro-preview` | unchanged |

**Fact-checking is mandatory** — every module review must include a `FACT_CHECK` step that verifies K8s API versions, command syntax, and feature availability against live sources. This is non-skippable.

## Verified CLI flags (you confirmed these yourself)

```
# Internet-enabled review (read-only filesystem)
codex --search exec --skip-git-repo-check --sandbox read-only

# Dangerous patch mode (full write, no prompts)
codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -m gpt-5.4
```

## Code changes needed

You already produced the full implementation in task `v2-codex-redesign` (message #117). Apply it now:

### 1. `scripts/dispatch.py` — add two new functions

```python
CODEX_REVIEW_DEFAULT_MODEL = "codex"
CODEX_PATCH_DEFAULT_MODEL = "gpt-5.4"

def dispatch_codex_review(prompt, model=CODEX_REVIEW_DEFAULT_MODEL, timeout=900):
    """codex --search exec --sandbox read-only"""
    cmd = [CODEX_CLI, "--search", "exec", "--skip-git-repo-check", "--sandbox", "read-only"]
    if model and model != "codex":
        cmd.extend(["-m", model])
    # ... same pattern as dispatch_codex

def dispatch_codex_patch(prompt, model=CODEX_PATCH_DEFAULT_MODEL, timeout=1200):
    """codex exec --dangerously-bypass-approvals-and-sandbox"""
    cmd = [CODEX_CLI, "exec", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox"]
    if model:
        cmd.extend(["-m", model])
    # ... same pattern as dispatch_codex
```

### 2. `scripts/pipeline_v2/review_worker.py`

- Change `REVIEW_MODEL` (or `FLASH_MODEL`) to `"gpt-5.3-codex-spark"`
- Change `dispatch_fn` default from `dispatch_gemini` to `dispatch_codex_review`
- Add `FACT_CHECK` to check IDs — must be in `DEEP_CHECK_IDS` and non-skippable
- `PATCH_MODEL = "codex"` is already set (from earlier this session)

### 3. `scripts/pipeline_v2/patch_worker.py`

- Change `dispatch_fn` default from `dispatch_codex` to `dispatch_codex_patch`
- Already imports `dispatch_codex` — swap to `dispatch_codex_patch`

### 4. `.pipeline/budgets.yaml`

Add `gpt-5.4` entry (already has `codex` entry from earlier this session):
```yaml
  gpt-5.4:
    cooldown_after_rate_limit: 600
    hourly_calls: 30
    max_concurrent: 1
    weekly_budget_usd: 50.0
    weekly_calls: 300
```

### 5. Tests — add to `scripts/tests/`

Add tests verifying:
1. `dispatch_codex_review` builds cmd with `--search` and `read-only`
2. `dispatch_codex_patch` builds cmd with `--dangerously-bypass-approvals-and-sandbox` and NO `read-only`
3. `FACT_CHECK` is in review worker check list and marked non-skippable
4. All subprocess calls mocked — no real Codex calls

## How to run after applying changes

```bash
# Verify tests still pass
PYTHONPATH=scripts .venv/bin/pytest scripts/tests/ -q

# Start workers (3 separate terminals or background)
PYTHONPATH=scripts .venv/bin/python -m pipeline_v2.cli review-worker loop &
PYTHONPATH=scripts .venv/bin/python -m pipeline_v2.cli patch-worker loop &
PYTHONPATH=scripts .venv/bin/python -m pipeline_v2.cli write-worker loop &

# Watch status
PYTHONPATH=scripts .venv/bin/python -m pipeline_v2.cli status
```

## How to coordinate with Gemini using the comm tools

The project has an agent bridge at `scripts/ab`. Use it to consult Gemini when you need adversarial review of your work before merging.

```bash
# Ask Gemini to review something (NEVER parallelize — runs sequential)
echo "Your prompt here" | scripts/ab ask-gemini \
  --task-id your-task-id \
  --model auto \
  -

# Read a response
scripts/ab read <message-id>

# Check your inbox (messages from other agents)
scripts/ab inbox

# Send a message to Claude (when Claude has usage again)
scripts/ab ask-claude --task-id handback-to-claude --from codex "Summary of what I did"
```

**Key rules for Gemini coordination:**
- NEVER parallelize Gemini calls — user runs other concurrent workloads, one at a time
- Use `--model auto` as the model (never hardpin flash/pro)
- Always send Gemini for adversarial review before closing any issue
- If Gemini says NEEDS CHANGES, fix before merging
- Post Gemini's review as a comment on the GH issue

**Gemini's role:**
1. Adversary reviewer — catches bugs Codex misses, flags technical errors
2. Does NOT write code — you (Codex) write, Gemini reviews

## Workflow for this task

1. Apply code changes (dispatch.py, review_worker.py, patch_worker.py, budgets.yaml)
2. Run tests: `PYTHONPATH=scripts .venv/bin/pytest scripts/tests/ -q`
3. Ask Gemini to review the changes: `echo "Review these pipeline changes for correctness..." | scripts/ab ask-gemini --task-id v2-codex-gemini-review --model auto -`
4. Fix any Gemini feedback
5. Commit: `git add scripts/dispatch.py scripts/pipeline_v2/review_worker.py scripts/pipeline_v2/patch_worker.py .pipeline/budgets.yaml && git commit -m "feat(v2): swap review→codex+internet, patch→gpt5.4+dangerous, add FACT_CHECK"`
6. Start workers and monitor

## Important project rules

- **Never merge without adversarial review** — Gemini must review before any PR/commit to main
- **Claude never edits module content** — pipeline workers do, not you directly
- **Never parallelize Gemini calls** — sequential only
- **Build before push**: `npm run build` — 0 warnings required
- **Never leave detached HEAD** — check `git status` before and after worktree ops
- Commit format: `feat:`, `fix:`, `docs:`, `chore:` with `#N` issue refs

## Open issues

| # | Title | Status |
|---|---|---|
| 239 | v2 pipeline | Workers not started yet — this is what you're completing |

## Key files

- `STATUS.md` — project status
- `.pipeline/state.yaml` — v1 state (migrated, don't modify)
- `.pipeline/v2.db` — v2 SQLite (active)
- `.pipeline/budgets.yaml` — runtime concurrency caps
- `scripts/dispatch.py` — all LLM dispatch functions
- `scripts/pipeline_v2/` — v2 worker code
- `scripts/tests/` — test suite

Good luck. When done, send Claude a summary via: `scripts/ab ask-claude --task-id codex-handback --from codex "Done: <summary>"`
