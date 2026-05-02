# Session handoff — 2026-05-02 (session 2) — #388 Day 2 pilot launched (autonomous)

> Picks up from `2026-05-02-1-388-day-1-verifier-and-fix-pass.md`. User went auto + away; this session selected 9 pilot modules, wrote a sequential dispatcher (`scripts/quality/dispatch_388_pilot.py`), and launched it in background. The dispatcher self-orchestrates codex (mode=danger) → gemini cross-family review → squash-merge per item. Expected wall-clock: 9-13 hours for the full pilot. No babysitting required; the user reads the JSONL log on return.

## Decisions and contract changes

### Pilot list — 9 modules, 4 tracks, 3 word-bands

`scripts/quality/pilot-2026-05-02.txt` (one path per line):

| Track | Band | Body words | Median wpp | Module |
|---|---|---|---|---|
| certifications | small | 359 | 4.5 | `src/content/docs/k8s/ckad/part1-design-build/module-1.2-jobs-cronjobs.md` |
| cloud | small | 683 | 12.0 | `src/content/docs/cloud/managed-services/module-9.9-api-gateways.md` |
| cloud | mid | 2005 | 14.0 | `src/content/docs/cloud/gcp-essentials/module-2.7-cloud-run.md` |
| platform | small | 346 | 6.0 | `src/content/docs/platform/toolkits/infrastructure-networking/iac-tools/module-7.8-sst.md` |
| platform | large | 4774 | 101.5 | `src/content/docs/platform/toolkits/observability-intelligence/observability/module-1.3-grafana.md` |
| fundamentals | small | 592 | 6.0 | `src/content/docs/linux/foundations/container-primitives/module-2.3-capabilities-lsms.md` |
| fundamentals | mid | 2002 | 29.0 | `src/content/docs/prerequisites/git-deep-dive/module-1-git-internals.md` |
| onprem | large | 4985 | 53.5 | `src/content/docs/on-premises/security/module-6.4-compliance.md` |
| onprem | large | 4678 | 71.0 | `src/content/docs/on-premises/operations/module-7.8-observability-at-scale.md` |

Selection method: median pick of (track × band) groups sorted by `(median_wpp, body_words)`. Day 1 audit showed all 235 modules → T3, dominant gate is `body_words_5000` (234/235 fail), so even the "large" picks need expansion to clear the 5000-word floor (the "large" 4774-word grafana module has mwpp=101.5, meaning very few prose paragraphs — code-block-heavy, not prose-heavy).

The 235-module population skews heavily small: 105 cert, 69 platform-toolkits, 29 fundamentals are all in the `<1500 body words` band. Only 4 onprem and 2 platform modules are in the `4500+` band. The pilot deliberately includes both extremes (359 → 4985 body words) to stress-test the rewriter's behavior at both ends.

### Dispatcher contract — `scripts/quality/dispatch_388_pilot.py`

Sequential per-item loop. For each module:

1. Worktree at `.worktrees/codex-388-pilot-<slug>` from `origin/main`, branch `codex/388-pilot-<slug>`.
2. Codex dispatch via `agent_runtime.runner.invoke(agent_name="codex", model="gpt-5.5", mode="danger", cwd=wt, hard_timeout=5400)`.
   - Prompt embeds `scripts/prompts/module-rewriter-388.md` (binding) + `scripts/prompts/module-writer.md` (structural baseline).
   - Codex reads existing module → extracts protected assets (code/diagrams/tables/sources) → rewrites in place → runs verifier locally → iterates → commits → pushes → opens PR via `gh pr create` → returns PR URL on last line.
3. Parse PR number from codex response (`github.com/.../pull/<N>`).
4. Gemini cross-family review via `agent_runtime.runner.invoke(agent_name="gemini", mode="workspace-write", cwd=REPO, hard_timeout=900)`.
   - Prompt instructs gemini to use `gh pr view {N}` + `gh pr diff {N}` and end with `VERDICT: APPROVE | APPROVE WITH NITS | NEEDS CHANGES`.
5. Post review as PR comment.
6. If verdict contains `APPROVE` (not "NEEDS CHANGES") → `gh pr merge {N} --squash --delete-branch`.
7. Sleep 5s; next module.

JSONL log at `logs/388_pilot_2026-05-02.jsonl` with events: `pilot_start`, `module_start`, `worktree_error`, `codex_dispatch_start`, `codex_done`, `codex_error`, `module_skip`, `gemini_review_start`, `gemini_done`, `gemini_error`, `merged`, `merge_held`, `pilot_done`.

Stdout/stderr at `logs/388_pilot_2026-05-02.stdout.log`.

Mode = `danger` (not `workspace-write`) — per memory `feedback_codex_danger_for_git_gh.md` and the prior session's lesson that workspace-write blocks `.git/worktrees/<branch>/index.lock` writes and `api.github.com` calls. Danger lets codex commit + push + `gh pr create` from inside the worktree without manual intervention.

### Auth verified before launch

- `gh auth status` → logged in as `krisztiankoos`, scopes include `repo` + `workflow` (PR creation works).
- `scripts/ab ask-codex --new-session ... gpt-5.5` smoke → `OK` (2 chars) — codex CLI healthy on subscription auth.

### What is intentionally NOT in this pilot

- No "track-level coherence review every 3-4 batches" — that's a Day 3+ volume-run guardrail per Codex's earlier consult. Pilot's purpose is to expose the contract on varied modules, not to ship coherent track sweeps.
- No parallel codex dispatch. Per memory `feedback_overnight_autonomous_codex_chain.md`, the autonomous chain is per-item sequential. Day 1 confirmed 2x parallel is safe under load, but pilot stays sequential to keep the failure-mode read clean.
- No conditional re-dispatch on `NEEDS CHANGES`. The dispatcher logs verdict + holds the PR open; user inspects + decides on intervention next session. Per memory: "Skip on 3 rounds blocked" — for pilot we skip on first NEEDS CHANGES and move on.
- No verifier-output assertion in the dispatcher. Codex is responsible for verifying before commit; if codex commits without iterating, the gemini review will catch genuine quality issues even if gates passed.

## What's in flight

### Background process

- **PID:** `52373` (Python interpreter at `/opt/homebrew/Cellar/python@3.14/3.14.4/...`)
- **Command:** `.venv/bin/python scripts/quality/dispatch_388_pilot.py`
- **Started:** 09:01:17 local (2026-05-02)
- **Expected duration:** 9-13 hours sequential (60-90 min per module per Day 1 estimate)

### How to monitor (cold start)

```bash
# 1. Process alive?
/bin/ps -p 52373 -o pid,etime,comm

# 2. Latest events
tail -50 logs/388_pilot_2026-05-02.stdout.log
.venv/bin/python -c "
import json
recs = [json.loads(l) for l in open('logs/388_pilot_2026-05-02.jsonl')]
from collections import Counter
print('events:', Counter(r['event'] for r in recs))
print('latest:', recs[-1])
"

# 3. PRs opened by the pilot
gh pr list --label '' --search 'in:title 388 pilot' --state all --limit 20

# 4. Worktrees still in flight
git worktree list | grep 388-pilot
```

### How to intervene

```bash
# Kill the dispatcher (graceful — finishes current item or aborts mid-codex)
kill 52373

# Force kill if frozen
kill -9 52373

# Resume from where it stopped (manually re-edit the pilot file to remove completed modules,
# then re-launch — there is no built-in resume marker)
nohup .venv/bin/python scripts/quality/dispatch_388_pilot.py > logs/388_pilot_2026-05-02.stdout.log 2>&1 &

# Clean up a stuck pilot worktree
git worktree remove --force .worktrees/codex-388-pilot-<slug>
git branch -D codex/388-pilot-<slug>
```

### Failure modes to expect

1. **Codex sandbox refusal under danger mode** — first ever danger-mode dispatch in this session. If memory `feedback_codex_danger_for_git_gh.md` is correct it should be fine, but if codex still refuses git operations the symptom is `codex_done` event with response containing "blocked by sandbox" or similar. Mitigation: confirm `model_reasoning_effort` config and codex CLI version; check if a CODEX_SANDBOX env var is needed.
2. **PR not parsed from codex response** — `find_pr_number()` greps for `github.com/.../pull/<N>` in codex's reply. If codex prints the URL in a different form (e.g., `gh pr view <N>` URL) the parse may miss. Symptom: `module_skip reason=no_pr_in_response`. Mitigation: search the codex-side PR with `gh pr list --search 'codex/388-pilot-<slug>'` and run gemini review manually.
3. **Gemini APPROVE without VERDICT line** — gemini sometimes prints "I approve this PR" instead of "VERDICT: APPROVE". The verdict parser falls back to `UNCLEAR`, which holds the merge. Symptom: `merge_held verdict=UNCLEAR` on a clearly-good review. Mitigation: hand-merge after eyeballing the gemini comment.
4. **Codex iterates beyond hard_timeout (90 min)** — for the 4 large modules (4678-4985 body words → 5000+) the rewrite needs to add only a few hundred words, but for the 5 small modules (346-683 body words) codex must add 4400-4700 words. That's a lot; if codex iterates 3-4 times to satisfy density gates, 90 min may be tight. Symptom: `codex_error error=AgentTimeoutError`. Mitigation: bump `hard_timeout` in dispatcher and re-dispatch that module solo.

## Cross-thread notes

**ADD:**

- The 9-module pilot is the empirical input for "freeze thresholds before volume." Read the JSONL log + the gemini review verdicts as a batch when the dispatcher reports `pilot_done`; that's the moment to decide which density/structure thresholds need adjustment (or whether the rewriter brief itself needs editing).
- Danger-mode codex dispatch (`agent_runtime.runner.invoke` + `mode="danger"` + `cwd=worktree`) is the Day 2 baseline. If it works through the pilot, Day 3 volume run uses the same call shape.
- All 9 pilot modules are in the audit JSONL `scripts/quality/audit-2026-05-02-v2.jsonl`. After the pilot merges, re-run the verifier on those 9 specific paths to confirm they now pass:
  ```bash
  .venv/bin/python scripts/quality/verify_module.py --glob 'src/content/docs/k8s/ckad/part1-design-build/module-1.2-jobs-cronjobs.md' --skip-source-check --summary
  # repeat for each path; expect tier=T0
  ```
- The pilot's gemini reviews go on PR comments, not as `gh pr review --request-changes` / `--approve`. The dispatcher uses comments because gh formal reviews require a PAT with explicit review scope, and the bridge gh token's review scope was not verified in this session. User can convert good comments to formal approve-on-merge if desired.

**DROP / RESOLVE:**

- "TODO: Day 2 pilot — pick 8-12 modules" — DONE (9 selected, list at `scripts/quality/pilot-2026-05-02.txt`).
- "TODO: Day 2 pilot — write dispatcher" — DONE (`scripts/quality/dispatch_388_pilot.py` shipped, syntax-validated, launched).
- "TODO: Day 2 pilot — launch and run" — IN FLIGHT (PID 52373).

## Cold-start smoketest (executable)

```bash
# 1. Pilot dispatcher: alive or done?
/bin/ps -p 52373 -o pid,etime,comm 2>&1
# expect either: PID with elapsed time (alive) OR "no such process" (done/killed)

# 2. JSONL event tally
.venv/bin/python -c "
import json
from collections import Counter
recs = [json.loads(l) for l in open('logs/388_pilot_2026-05-02.jsonl')]
print('events:', dict(Counter(r['event'] for r in recs)))
"
# expect events including codex_dispatch_start, codex_done, gemini_done, merged

# 3. PRs opened
gh pr list --search 'in:title 388 pilot' --state all --limit 15

# 4. Pilot worktrees
git worktree list | grep -c 388-pilot
# expect: 9 if all dispatched; fewer if killed early

# 5. Verifier on a merged pilot module (replace path with one that merged)
.venv/bin/python scripts/quality/verify_module.py --glob '<merged-module-path>' --skip-source-check --summary
# expect tier=T0 (or close — sources gate may still fail)
```

## Files modified this session

```
scripts/quality/
  pilot-2026-05-02.txt             (new — 9 pilot module paths)
  dispatch_388_pilot.py            (new — sequential codex+gemini orchestrator)

logs/                              (created/appended by the running dispatcher)
  388_pilot_2026-05-02.jsonl       (event log)
  388_pilot_2026-05-02.stdout.log  (stdout/stderr capture)

docs/session-state/
  2026-05-02-2-388-day-2-pilot-launched.md  (this file)

STATUS.md  (Latest handoff promotion at session end)
```

Removed: `diff.txt`, `pr_diff.txt` (scratch files left from session 1).

## Blockers

(none for the dispatcher — it runs autonomously. Decisions on threshold-freeze and Day 3 volume run wait for the user to read the pilot results.)
