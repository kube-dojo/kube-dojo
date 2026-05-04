# Session handoff — 2026-05-04 (session 1) — Codex-out window cleanup, quality-board status-split, 4 PRs merged + 1 holding

> Picks up from `2026-05-02-5-388-day3-kcna-running-token-rotation.md`. Two-day gap (no sessions on 2026-05-03). The session-5 pending work (apply codex's `_summarize_388_events` NEEDS-CHANGES fix) was already shipped between sessions — verified via `/api/388/batches` endpoint working live before this session started. Today's session opened with **all Codex tiers exhausted of weekly quota until ~11:00 2026-05-05**, which forced a single-reviewer (Gemini OAuth) constraint and shaped the entire workflow.

## Decisions and contract changes

### Codex-out-window contingency protocol (memory `feedback_codex_offline_contingency.md`)

When all Codex tiers (`gpt-5.5`, `gpt-5.4-mini`, `gpt-5.3-codex-spark`) are out of weekly quota, the team is effectively two-agent (Claude orchestrator + Gemini OAuth). Operational rules during the window:

- **Gemini OAuth is the sole cross-family reviewer** for Claude-authored code (per AGENTS.md rule #10). Dispatch reviews EARLY before Gemini OAuth burns its own per-account quota.
- **Don't dispatch ANY codex tier**, including `gpt-5.4-mini` for cheap search. Use Claude haiku via `dispatch_smart.py --agent claude search` instead.
- **Claude can both write AND review** — but never the same PR (would be same-priors, not cross-family). If I write code, Gemini reviews; if I review Gemini's work, fine.
- **Content writing burden** falls to Claude (opus, sparingly) or Gemini-drafts + Claude-expansion. `project_budget_and_delegation.md`'s "Claude disqualified for bulk" rule is relaxed during a codex-out window for ≤5 modules of urgent #388 work, then resume.
- **`ab discuss` runs 2-way** with explicit note in any Decision Card: *"DELIBERATION 2-WAY DUE TO CODEX-OUT — priors more correlated than usual; user override weight increased."*

### Quality board status-split — `shipped_unreviewed` is a distinct status (PR #873 merged)

The `needs_review` orange chip on the quality board conflated 251 modules across two very different populations:
- **59 genuinely mid-pipeline** (stage AUDITED/ROUTED, awaiting reviewer)
- **192 ad-hoc shipments** (merged on main without ever entering the pipeline state machine — stage UNAUDITED + score≥4 + no banner)

That conflation was hiding the actionable review queue under bookkeeping debt — operator could not tell "review in flight" from "shipped without review tracking". The classifier in `_quality_board_classify` (`scripts/local_api.py:3715`) now has a new `shipped_unreviewed` branch:

```python
if score_val >= 4.0 and not revision_pending and stage == "UNAUDITED":
    return "shipped_unreviewed"
```

Wired through totals dict, per-track buckets, dashboard QB_STATUS list + label, two CSS rules (orange `#f97316` distinct from `needs_review`'s amber `#fbbf24`). Live counts post-merge: `done=78, needs_rewrite=424, needs_review=59, shipped_unreviewed=192, both=1, in_flight=0`.

### Cross-agent dispatch routing — codex tiers in `dispatch_smart.py` (PR #872 — HOLDING)

PR #870 (merged 2026-05-04) added an "Economical Multi-Agent Delegation" policy to `AGENTS.md` for Codex's *internal* multi-agent subagents (mini for general routine, spark for bounded code-heavy, gpt-5.5 for judgment). PR #872 mirrors the same tiering for cross-agent dispatches by extending `scripts/dispatch_smart.py` with `--agent {claude,codex}`. Routing table:

| task_class | claude | codex |
|---|---|---|
| `search` | `claude-haiku-4-5-20251001` | `gpt-5.4-mini` |
| `edit` | `claude-sonnet-4-6` | `gpt-5.3-codex-spark` |
| `draft` | `claude-sonnet-4-6` | `gpt-5.3-codex-spark` |
| `review` (new) | `claude-sonnet-4-6` | `gpt-5.5` |
| `architect` | `claude-opus-4-7` | `gpt-5.5` |

**Status: NEEDS CHANGES** per Gemini review. Blocker: smoke-test of new codex model strings (`gpt-5.4-mini`, `gpt-5.3-codex-spark`) on the bridge auth path is deferred — can't smoke-test while codex is out. **First task next session, after codex returns ~11:00 2026-05-05.**

### "Help the user decide" — refined dilemma-framing rule (memory `feedback_no_dilemma_framing.md`)

User clarified twice this session what they want when there are multiple paths forward:

> *"no you should be 'we have these options and i suggest this one because this is the best for reaching our quality goals'"*
> *"you should be helping me to decide"*

Format: state options briefly + give a recommendation tied to a stated quality/operational goal + default to executing the recommendation. Don't dump menus that punt the choice (enemy behavior per the user). Don't go silent and execute either (hides alternatives). The recommendation IS the orchestrator's job. Prior memory had over-corrected to "silent execute"; corrected mid-session.

### Codex model tiering (memory `feedback_codex_model_routing.md`)

Don't reflex to `gpt-5.5` for every Codex dispatch. Tier by task class same as Claude routes haiku/sonnet/opus. `gpt-5.3-codex-spark` is on a separate usage counter so bounded coding chores preserve the gpt-5.5 counter for judgment work (cross-family review, architecture). Saved 2026-05-04 morning before codex went fully offline; the smoke-test gate now applies to all three new model strings before any production dispatch.

## What's still in flight

- **PR #872 (`claude/codex-routing`)** — open, NEEDS CHANGES from Gemini review. Worktree at `.worktrees/claude-codex-routing`. Resolution path locked: smoke-test `gpt-5.4-mini` + `gpt-5.3-codex-spark` on bridge auth, address Gemini's finding (the deferred-smoke-test risk), request re-review.
- **387 modules at critical rubric score (<2.0)** — alert on briefing, separate workstream, untouched today. Codex-blocked.
- **No other Claude-authored PRs awaiting review.** Queue is clean.

## Cold-start smoketest (executable; the FIRST things to run in the new session)

```bash
cd /Users/krisztiankoos/projects/kubedojo
direnv allow .   # only if direnv didn't auto-load
set -a && source .envrc && set +a   # alternative if direnv is missing

# 1. Confirm gh auth points at the kube-dojo PAT
gh auth status 2>&1 | head -5
gh api user -q .login   # expect: krisztiankoos

# 2. Confirm main is current
git fetch origin main && git status --short
# expect: clean tree, "On branch main", "Your branch is up to date"

# 3. Confirm services-up
curl -s "http://127.0.0.1:8768/api/briefing/session?compact=1" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('alerts:', d.get('alerts', []))
print('blockers:', d.get('blockers', []))
"

# 4. Confirm the status-split classifier is live (should show shipped_unreviewed bucket)
curl -s "http://127.0.0.1:8768/api/quality/board" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('totals:', d['totals'])
"
# Expect: needs_review around 59, shipped_unreviewed around 192

# 5. Test if codex is back (the gating call for unblocking PR #872)
codex exec -m gpt-5.4-mini "echo hi" --skip-git-repo-check --sandbox read-only 2>&1 | tail -5
# If returns non-error stdout: codex is back, proceed with PR #872 smoke-test
# If returns 403/quota error: codex still out, skip step 6, work on other items
```

## Apply codex's NEEDS CHANGES on PR #872 (when codex is back)

```bash
cd /Users/krisztiankoos/projects/kubedojo/.worktrees/claude-codex-routing

# 1. Smoke-test both new codex model strings on the bridge auth path
for m in gpt-5.4-mini gpt-5.3-codex-spark; do
  echo "=== smoke-test $m ==="
  codex exec -m "$m" "echo hello-from-$m" --skip-git-repo-check --sandbox read-only 2>&1 | tail -10
done

# 2. If both work: nothing to fix in code — Gemini's finding was about the
#    DEFERRED smoke-test, which is now done. Document the smoke-test results
#    in a follow-up commit on the branch:
git commit --allow-empty -m "docs(dispatch): smoke-test gpt-5.4-mini and gpt-5.3-codex-spark verified

Gemini cross-family review on PR #872 flagged that the new model strings
were untested on the bridge auth path. Smoke-tested on $(date -u +%Y-%m-%d):

- gpt-5.4-mini: <result>
- gpt-5.3-codex-spark: <result>

Both reachable via codex exec with default config. Cleared NEEDS CHANGES.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"

git push
gh pr review 872 --comment --body "Smoke-test complete (see latest commit). Re-requesting review."

# 3. If either model returns 403/auth-error: the routing table was wrong.
#    Update dispatch_smart.py to use a verified-working model, push, request review.

# 4. Re-dispatch Gemini review on the updated branch
KUBEDOJO_GEMINI_SUBSCRIPTION=1 .venv/bin/python scripts/dispatch.py gemini --review --github 872 --timeout 900 - <<'EOF'
Re-review of PR #872 after smoke-test on the new codex model strings completed.
Gemini's previous finding was that gpt-5.4-mini and gpt-5.3-codex-spark were
untested. Smoke-test results are documented in the latest commit on the branch.

Verify the smoke-test commit + re-confirm the verdict.
EOF
```

## Files committed this session

```
ae16d5f7  docs(status): note codex-out-until-2026-05-05-11am blocker (#874)
a79d322f  fix(pipeline-v4): tech-debt cleanup — sys.executable, LOC gate, services-up (#875)
54472903  feat(quality-board): split shipped_unreviewed out of needs_review (#873)
c0c0f75b  feat(resolver): #344 extend citation-residuals resolver to overstated/off-topic + queued buckets (#876)
```

5 commits on main today (one of #875's was the rebase chain; counted as 1 PR-merge).

PR #875 closed AGENTS.md rule #3 violations across 5 production scripts (`scripts/ai_agent_bridge/_claude.py`, `scripts/on-prem/phase2-write-only.py`, `scripts/pipeline_v4.py`, `scripts/research/writer-calibration-rigorous.py`, `scripts/v2_ab_test.py`) by replacing `sys.executable` with explicit `.venv/bin/python`.

## Files holding (uncommitted at handoff time)

None. Working tree clean. Single open PR (#872) holds in its own worktree.

## Worktrees / branches cleanup this session

- **Pruned 18 worktrees + 18 branches** (all `upstream-gone` or `merged,upstream-gone`). Cross-checked branches via squash-merge subjects on main before deletion.
- **Pruned `codex-local-api-codeql`** — spark's PR #871 merged earlier today, worktree was leftover.
- **Pruned `review-gemini-merged`** — detached HEAD, verified ancestor of main before removal.
- **Pruned `codex-394-coverage-schema`** — superseded by merged PR #595 (`feat(ai-history): add review coverage tooling`).
- **Salvaged `codex-344`** — single feature commit (`b30ef924: feat(resolver): #344 extend resolver`) rebased clean onto main, lint pass, 4/4 tests pass. Shipped as PR #876, Issue #344 auto-closed.
- **4 stale PIDs cleaned** (`dev.pid`, `v2-patch-worker.pid`, `v2-review-worker.pid`, `v2-write-worker.pid`).

Final worktree count: **2** (primary main + claude-codex-routing-holding).

## New memory entries

- `feedback_codex_offline_contingency.md` — operational rules + pre-window checklist for Codex-out
- `feedback_codex_model_routing.md` — tier codex by task class, don't reflex to gpt-5.5
- `feedback_no_dilemma_framing.md` — help the user DECIDE (options + recommendation tied to a goal)
- Updated `reference_dispatch_smart.md` — extended for `--agent codex`
- Updated `reference_codex_models.md` — appended tiered routing section

## Cross-thread notes

**ADD:**

- **The `shipped_unreviewed` bucket is real review debt.** 192 modules shipped ad-hoc without ever entering the pipeline state machine. They pass the structural rubric (score≥4) but were never cross-family-reviewed. They are NOT bookkeeping artifacts that can be backfilled with synthetic verdicts — that would be lying per `feedback_citation_verify_or_remove.md` (the honesty rule applies to provenance too). The right resolution is real cross-family review when bandwidth allows.
- **Gemini OAuth review quality looks solid.** Across 5 reviews this session, Gemini caught real bugs (the 3 PR #873 findings were all legitimate: missing UI badge wiring, broken test assertion, stale docstring). PR #875 review included substantive analysis — confirmed sys.executable kept in tests, validated LOC-gate logic uses citation_v3 dict, identified the PID slack as the upstream race-fix. Quality during codex-out window is acceptable.
- **Direct commits to main violate AGENTS.md rule #1 — even for STATUS.md.** I committed STATUS.md to local main once this session, then caught it and reset/cherry-picked to a branch. Recent commit history shows every STATUS.md update goes through a PR. Don't shortcut.
- **Worktree pruning safety check pattern**: cross-reference `prunable_worktrees[]` with `prunable_branches[]` via the `/api/git/cleanup` endpoint, skip any worktree where `git status --porcelain` is non-empty (preserve in-flight work), then verify branch is on main via squash-merge subject grep before `git branch -D`. The `git cherry` per-commit-equivalence check produces false positives on squash-merged branches; subject grep catches them correctly.

**DROP / RESOLVE:**

- "Apply codex's NEEDS CHANGES fix to `_summarize_388_events`" (from session 5) — DONE between sessions, verified via live `/api/388/batches` endpoint at session start.
- "Triage held PRs from KCNA batch" (from session 5 TODO) — DONE between sessions. `/api/388/batches` shows `held_rollup: {merged: 16, total: 16, open: 0, resolved: 16}` for the 2026-05-02 KCNA batch — all 7 held PRs (5 nits + 1 NEEDS CHANGES + 1 ERROR) were triaged and merged before this session began.
- "Generalize cleanup script to accept `--input PATH.txt`" (from session 5 TODO) — DONE in session 5 itself, commit `ff116a40` (`fix(388): generalize cleanup script + pre-build KCSA bucket-2`). Was a duplicate carry-over.
- "Investigate the 8 module_skip events from KCNA bucket" (from session 5) — UNRESOLVED but no longer urgent; queue is dry, codex-out makes it un-actionable for now. Re-queued in this session's TODO.
- "Investigate codex-344, codex-394-coverage-schema, fix-pipeline-v4-tech-debt worktrees" (from session 5) — ALL DONE this session: tech-debt salvaged + shipped (#875), codex-394 pruned as superseded, codex-344 salvaged + shipped (#876).
- "Audit the 3 unknown worktrees" (today's earlier intra-session item) — DONE.
- "Open all pending PRs and dispatch Gemini reviews while quota fresh" — DONE.
- "PR #567 review + merge" (from STATUS.md Background) — RESOLVED. PR #567 was CLOSED (superseded by PR #595, merged earlier).
- "#344 (citation-residuals resolver work in `codex/issue-344` worktree)" (from STATUS.md Background) — RESOLVED. Shipped as PR #876 today; Issue #344 auto-closed.

## Blockers

- **Codex offline until ~11:00 2026-05-05** (all tiers — gpt-5.5, gpt-5.4-mini, gpt-5.3-codex-spark). Blocks: PR #872 smoke-test, any new codex content writing, any `dispatch_smart.py --agent codex` calls. Mitigation in `feedback_codex_offline_contingency.md` memory + STATUS.md blocker.
- **Gemini OAuth is the sole cross-family reviewer** during the window — track per-account quota; current Gemini account had no rate-limit issues across 5 reviews this session.
