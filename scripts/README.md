# KubeDojo Scripts

## check_site_health.py

Validates site integrity — run before every push.

```bash
# Run the health check
python scripts/check_site_health.py
```

**What it checks:**
1. All `mkdocs.yml` nav entries point to existing files
2. No orphaned `.md` files missing from navigation
3. All internal markdown links resolve (`[text](path.md)`)
4. Changelog has links for every mentioned module
5. No duplicate nav entries
6. Module count in STATUS.md matches actual files
7. README files reference their child modules

**Exit codes:** 0 = pass, 1 = errors found

**When to run:**
- Before every `git push`
- After adding new modules
- After updating navigation or changelog

---

## ztt_status.py

Unified `Zero to Terminal` readiness report.

```bash
python scripts/ztt_status.py
python scripts/ztt_status.py --json
```

**What it reports:**
1. English ZTT theory modules present and fact-ledger audited
2. ZTT lab review state from `.pipeline/lab-state.yaml`
3. Ukrainian ZTT file presence and commit-sync state against English source files

---

## status.py

Unified repo-level operational status.

```bash
python scripts/status.py
python scripts/status.py --json
```

**What it reports:**
1. v2 pipeline queue/convergence state from `.pipeline/v2.db`
2. Translation ownership and repo-wide Ukrainian sync state
3. Lab review state from `.pipeline/lab-state.yaml`
4. Zero to Terminal readiness snapshot

---

## local_api.py

Read-only deterministic local API for repo and pipeline state.

```bash
python scripts/local_api.py
python scripts/local_api.py --host 0.0.0.0 --port 8768
```

**First endpoints:**
1. `/` and `/dashboard` — lightweight local monitor UI
2. `/healthz`
3. `/api/status/summary`
4. `/api/pipeline/v2/status`
5. `/api/translation/v2/status?section=prerequisites/zero-to-terminal`
6. `/api/labs/status`
7. `/api/ztt/status`
8. `/api/git/worktree`
9. `/api/issue-watch/248`
10. `/api/module/<module-key>/state`
11. `/api/module/<module-key>/orchestration/latest`

**Why it exists:**
1. Reduces repeated shell/file probes for stable state
2. Exposes deterministic JSON for pipeline, translation, labs, worktree, and module-level views
3. Adds a lightweight local dashboard so the API is easier to inspect without curl-only workflows

---

## issue_watch.py

Watch GitHub issue comments into local state and log files.

```bash
python scripts/issue_watch.py run 248
python scripts/issue_watch.py loop 248 --interval-seconds 1800
```

**What it does:**
1. Polls `gh issue view` for the target issue
2. Stores the latest snapshot under `.pipeline/issue-watch/<issue>.json`
3. Appends newly seen comments to `.pipeline/issue-watch/<issue>.log`
4. Gives long-running feedback review a durable local trail instead of relying on memory

---

## translation_v2.py

Queue-based Ukrainian sync control plane.

```bash
python scripts/translation_v2.py status --section prerequisites/zero-to-terminal
python scripts/translation_v2.py enqueue-section prerequisites/zero-to-terminal --limit 3
python scripts/translation_v2.py worker run --json
python scripts/translation_v2.py verify-worker run --json
python scripts/translation_v2.py watchdog sweep
```

**What it does:**
1. Detects per-module Ukrainian freshness (`synced / stale / missing / unknown`)
2. Enqueues translation jobs one module at a time on `.pipeline/translation_v2.db`
3. Runs a `write -> review` flow:
   - `worker`: translate or refresh the Ukrainian module
   - `verify-worker`: run deterministic freshness + Ukrainian quality verification
4. Retries failed modules without blocking whole-section progress

---

## dispatch.py

Direct CLI dispatch for Gemini and Claude — calls CLIs as subprocesses with no broker or database.

### Quick Usage

```bash
# Review a module (--review adds KubeDojo review context)
python scripts/dispatch.py gemini \
  "Review docs/k8s/cka/part3-services-networking/module-3.5-gateway-api.md for technical accuracy" \
  --review

# Review a GitHub issue and post result as comment
python scripts/dispatch.py gemini \
  "Review issue #66: $(gh issue view 66 --json body --jq .body)" \
  --review --github 66

# Review a diff
python scripts/dispatch.py gemini \
  "Review this diff for accuracy: $(git diff HEAD~3..HEAD -- docs/)" \
  --review

# Read prompt from stdin
cat prompt.txt | python scripts/dispatch.py gemini - --review

# Use Claude for expansion
python scripts/dispatch.py claude "Expand this draft to full depth..."
```

### Programmatic Usage

```python
from scripts.dispatch import GEMINI_WRITER_MODEL, dispatch_gemini_with_retry, post_to_github

ok, output = dispatch_gemini_with_retry("Review this module...", review=True)
if ok:
    post_to_github(66, output, GEMINI_WRITER_MODEL)
```

### Review Criteria

Gemini reviews KubeDojo content against these criteria (auto-injected with `--review`):
- **Technical accuracy**: K8s commands correct and runnable, version numbers accurate
- **Exam alignment**: Content matches current CNCF exam curriculum
- **Completeness**: Acceptance criteria thorough, edge cases covered
- **Junior-friendly**: Beginner-accessible, "why" explained not just "what"

### Architecture

- **No broker** — direct `subprocess.Popen` / `subprocess.run` calls to `gemini` and `claude` CLIs
- **Streaming** — Gemini output streams to stdout in real-time
- **Retry** — exponential backoff on rate limits (default 3 retries)
- **GitHub integration** — posts reviews as issue comments via `gh` CLI (with chunking for long reviews)
