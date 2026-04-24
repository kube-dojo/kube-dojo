# 2026-04-24 — Quality Pipeline v2 Redesign (handoff)

**State on handoff**: v1 pipeline script (`scripts/quality_pipeline.py`) REJECTED by Codex cross-family review. Requirements locked with user. Redesign not started. Primary repo clean on `main`, no in-flight worktrees, no uncommitted changes.

**Next session task**: implement pipeline v2 per the locked requirements below, re-submit to Codex for a second review, then 1-module end-to-end smoke test before scaling to 742 modules.

## Cold-start smoketest

```bash
curl -s http://127.0.0.1:8768/api/briefing/session?compact=1 | head -40
git log --oneline -5                     # expect the v1-rejected commit at top
ls scripts/quality_pipeline.py           # v1, do not run write/review/commit stages
ls .pipeline/teaching-audit/ | wc -l     # expect 21 (pilot + 19 audited before kill)
ls .pipeline/quality-pipeline/ | wc -l   # expect 742 state JSONs (or 0 if you want to reset)
```

If the count of state JSONs is 742, bootstrap already ran — fine to resume from there (state is idempotent; re-running bootstrap is a no-op). If you want a clean slate, `rm .pipeline/quality-pipeline/*.json` and start over.

## Locked requirements (user-confirmed 2026-04-24)

1. **Git hygiene via worktrees.** Primary checkout stays on `main`, clean. Every module runs in `.worktrees/quality-<slug>/` on its own branch. Rebase before merge. Worktree + branch cleaned up on all exit paths (success, failure, SIGKILL recovery).
2. **Full sweep.** Process all 742 English content modules (`src/content/docs/**/*.md`, exclude `uk/` and `index.md`). Idempotent resumption.
3. **Skip score ≥ 4.0.** Modules scoring ≥4.0 on the teaching audit skip the rewrite stage, but still run citation verification.
4. **Citation verify-or-remove (STRICT).** For every module touched: Lightpanda-fetch each URL in `## Sources`, LLM-verify it supports the nearest claim. Keep **only** on a clear `supports` verdict. Everything else (`partial`, `no`, fetch-fail, ambiguous) → remove. Burden of proof is on keeping. Applies uniformly to existing citations, writer-added citations, and the 189 findings already queued — no grandfathering. We don't publish lies.
5. **Equal Codex/Claude delegation.** Writers alternate by module index: odd → Codex writes + Claude reviews, even → Claude writes + Codex reviews. Gemini used only for the pre-classification teaching audit and as a tiebreaker if a Codex↔Claude retry loop stalls. Budget memo ("Claude disqualified for bulk") is overridden by this explicit user directive for this pipeline.

## Architecture (per Codex's design concern)

The v1 broke because it used **one mutable checkout** as orchestrator + writer workspace + reviewer input + merge target. Redesign splits those roles.

```
Primary checkout           .worktrees/quality-<slug>/      main
(always on main, clean)    (writer operates here)           
       │                            │
       ├─ pipeline orchestrator     ├─ git branch quality/<slug>
       ├─ state files (atomic)      ├─ writer makes edits + commits
       ├─ read-only for reviewer    ├─ reviewer READS from here
       └─ merges via rebase + ff    └─ torn down on completion
```

### Revised state machine

```
UNAUDITED
  → AUDITED                 (Gemini audit against pedagogical framework)
  → ROUTED
      score ≥ 4.0 AND all citations verify  → SKIPPED (committed, no change)
      score ≥ 4.0 BUT bad citations         → CITATION_CLEANUP_ONLY → COMMITTED
      score <  4.0                          → WRITE_PENDING
  → WRITE_PENDING
      writer = round-robin(Codex, Claude) by module index
      dispatches in .worktrees/quality-<slug>/
      commits to branch quality/<slug> IN WORKTREE
  → CITATION_VERIFY
      for each URL in ## Sources: Lightpanda fetch → Gemini-flash verify
      unverifiable → removed in worktree, amended commit
  → REVIEW_PENDING
      reviewer = cross-family (the other of Codex/Claude)
      READS module from worktree, not from primary
  → REVIEW_APPROVED OR REVIEW_CHANGES
      APPROVED → MERGE → COMMITTED (worktree + branch torn down)
      CHANGES  → back to WRITE_PENDING with reviewer's must_fix list, retry_count++
                 retry cap 2. After 2 failures, Gemini breaks tie or state → FAILED.
```

### Durable in-progress states (Codex feedback)

v1 declared `WRITE_PENDING` / `REVIEW_PENDING` as states but didn't use them durably. v2 MUST use them so that a SIGKILL between "started writing" and "write succeeded" leaves state at `WRITE_IN_PROGRESS`, and resume can either reclaim the branch via `write.commit_sha` check or re-create the worktree.

## Codex review must-fixes (from 2026-04-24 review)

Every item below must be addressed in v2. File:line refs are to the v1 file; use them as design guidance, not as patches.

1. **Reviewer reads wrong file** (`write_one:598`, `review_one:633`): v1 checks out `main` after write; reviewer then reads the ORIGINAL module. FIX: reviewer reads from the worktree, not primary.
2. **Primary checkout mutation** (`write_one:524`): v1 checks out feature branches in primary. FIX: worktrees.
3. **ff-only merge breaks after the first merge** (`commit_one:777`): each branch cut from old `main`. FIX: rebase branch onto main before merge, or use merge commits intentionally.
4. **`REVIEW_CHANGES` is dead** (`review_one:746`): no command consumes it. FIX: route back to `WRITE_PENDING` with reviewer must_fix list as feedback.
5. **Write not crash-resumable** (`write_one:506`): SIGKILL between commit and advance leaves state at `ROUTED` but branch has commit. FIX: explicit `WRITE_IN_PROGRESS` durable state + idempotence check against `write.commit_sha`.
6. **Git cleanup not in `finally`** (`write_one:583`, `:598`): some failure paths skip checkout-back-to-main. FIX: `try/finally` around every branch mutation; with worktrees this becomes `try/finally` around worktree lifecycle.
7. **`_extract_module_markdown` too weak** (`_extract_module_markdown:602`): fails on code fences, prose prefixes, truncation. FIX: tolerate code fence; find frontmatter closing `---`; validate title+slug survive; fail loudly if truncated mid-block.
8. **`_extract_json` takes first balanced object** (`_extract_json:685`): picks reasoning JSON over verdict JSON. FIX: find the LAST balanced JSON object, or require a sentinel prefix in the prompt and scan from there. Also schema-enforce and don't trust `verdict=approve` unless scores are numeric ≥4.0.
9. **Worktree venv bug** (`_VENV_PYTHON:51`): breaks if invoked from a worktree. FIX: port `_primary_checkout_root(repo_root)` from PR #374.
10. **No state file lease/CAS** (`save_state:260`): two workers can double-process. FIX: file-lock via `fcntl.flock` on state file for the duration of stage transition, OR compare-and-swap via `stage` field check before write.

### Should-fix (next-tier)

- `cmd_run` always returns 0 even after failures (line 808).
- Workers not clamped to ≥1; `--workers 0` breaks `ThreadPoolExecutor` (line 621).
- Review prompt says "ignore missing Sources" but bundles rubric text that penalizes Sources — may cause false rejections.
- Include `docs/quality-rubric.md` in review context if `rubric_score` is a gating field.
- `has_diagram = "<details>" in text` treats quiz answer `<details>` as diagrams (false positive).
- Tests missing: output extractors (fixtures for fenced/prose/truncated Codex output, multi-object JSON), REVIEW_CHANGES retry transition, worktree venv root, ff-merge-after-main-advanced, end-to-end state transition with fake git.

## Suggested package layout for v2

Keep the script monolithic unless it exceeds ~1200 LOC, then split:

```
scripts/quality/
  __init__.py
  pipeline.py         # orchestrator + subcommands + main
  state.py            # atomic state I/O + leases
  worktree.py         # git worktree lifecycle + primary_checkout_root
  stages.py           # audit / route / write / verify / review / commit
  prompts.py          # prompt builders (rewrite, structural, review, citation-verify)
  citations.py        # Lightpanda fetch + LLM verify + Sources section edit
  dispatchers.py      # Codex / Claude / Gemini wrappers with round-robin
  extractors.py       # module-markdown + JSON extractors with robust parsing
tests/
  test_quality_pipeline.py       # state transitions, round-robin, score cutoff
  test_quality_extractors.py     # code-fence, prose, truncation, multi-JSON
  test_quality_worktree.py       # lifecycle, primary root, cleanup on SIGKILL
  test_quality_citations.py      # verify-or-remove with mocked Lightpanda
```

## Delegation scheme (equal Codex/Claude, Gemini auxiliary)

```python
def writer_for_index(i: int) -> tuple[str, str]:
    """Returns (writer, reviewer) for module index i."""
    return ("codex", "claude") if i % 2 == 0 else ("claude", "codex")

def tiebreaker() -> str:
    return "gemini"  # only used when Codex↔Claude retry loop stalls
```

Gemini roles:
- **Teaching audit** (`audit_teaching_quality.py`, existing — keep)
- **Citation verification** — Gemini flash for cheap URL↔claim yes/no
- **Tiebreaker** — if retry_count == 2 and still REVIEW_CHANGES, run Gemini as arbiter

## Citation verify-or-remove details

**Rule (user-confirmed strict, 2026-04-24 evening)**: burden of proof is on keeping. If we cannot prove the page supports the claim, we remove the citation. An unverified citation is a potential lie — not acceptable to publish. No grandfathering: applies to existing entries, writer-added entries, and the 189 findings in `.pipeline/v3/human-review/`.

For each URL in `## Sources`:

1. Lightpanda: `lightpanda fetch --dump markdown --strip-mode full <url>` (timeout 30s)
2. Extract the claim: the description after `— ` on the source line, OR the surrounding paragraph in the module body if the source line is title-only.
3. Dispatch to Gemini flash:
   ```
   Given this page content [markdown dump], does it CLEARLY AND EXPLICITLY support this claim [claim text]?
   Return JSON: {"verdict": "supports|partial|no", "excerpt": "<60-word cite>"}
   Only use "supports" when the page states or demonstrates the claim directly. If it only implies, touches on, or is tangentially related, use "partial".
   ```
4. **KEEP only on `supports`**. **REMOVE on anything else** — `partial`, `no`, fetch failed, 404, page changed, ambiguous, or any tool error. No "flag + keep" path.

If after removal the `## Sources` section is empty, remove the heading too.

## Re-review loop

After v2 implementation:

```bash
# 1. Re-submit to Codex
codex exec -m gpt-5.5 -c model_reasoning_effort="high" "$(cat scripts/quality/*.py | \
    head -c 300000)"  # or use the full review prompt from /tmp/kd_pipeline_review.md

# 2. Smoke-test 1 module end-to-end
.venv/bin/python scripts/quality/pipeline.py bootstrap --module src/content/docs/k8s/capa/module-1.2-argo-events.md
.venv/bin/python scripts/quality/pipeline.py run --only k8s-capa-module-1.2-argo-events --limit 1 --workers 1

# 3. Verify the worktree was cleaned up
ls .worktrees/ 2>/dev/null  # should be empty

# 4. Verify the commit landed on main
git log --oneline -3

# 5. If passes, scale
.venv/bin/python scripts/quality/pipeline.py bootstrap          # all 742
.venv/bin/python scripts/quality/pipeline.py run --workers 1 --limit 10
```

## Existing artifacts and their status

- `scripts/quality_pipeline.py` — v1, REJECTED. Delete or keep as a reference. User voted commit-with-note at handoff so fresh session sees the bad version in git history.
- `scripts/audit_teaching_quality.py` — audit-only, fine, reused by v1 and should be reused by v2. Produces `.pipeline/teaching-audit/<slug>.json`.
- `scripts/requeue_pilot_findings.py` — one-off for today's citation revert. Per "no staging scaffolding" memory, should be deleted — but committed first for the history.
- `.pipeline/teaching-audit/` — 21 audit JSONs from the aborted batch run. Keep; v2 will promote them on bootstrap just like v1 did.
- `.pipeline/quality-pipeline/` — 742 state JSONs from v1 bootstrap. Keep OR reset; v2 should be able to use them (audit stage is the same).
- `.pipeline/v3/human-review/` — citation queue with 189 findings requeued from today's pilot revert. Unchanged by this handoff.

## Decisions + contract changes made this session

- **Citation pilot reverted**: 57 module edits reverted to HEAD, 73 resolved + 116 unresolvable findings requeued to `needs_citation`. See `scripts/requeue_pilot_findings.py`.
- **Lightpanda adopted** for citation work: already installed at `/opt/homebrew/bin/lightpanda`, 61.9 MB. Native `mcp` server. Replaces the "build a RAG over AWS docs" plan (also dead for now because disk freed up from 28 GB to 195 GB but we're still picking the simpler architecture).
- **Rubric heuristic is structural-only**: the 485 "rubric-critical" count was heuristic — capping at 1.5 solely on missing `## Sources`. True teaching quality requires the LLM audit. Confirmed by reading `scripts/local_api.py:2088-2110`.
- **Cross-family review failure mode acknowledged**: I claimed v1 was "smoke-tested and safe" before sending to Codex. That's a process failure — new memory recorded.

## What the next session should NOT do

- Run `scripts/quality_pipeline.py write|review|commit` against any real module. The v1 script's write/review/commit stages have the structural bugs listed above.
- Re-launch the audit batch run without workers=1 (the 3-worker run lagged user's Mac during a Zoom call).
- Resume citation backfill (Track 3) as a separate workstream — citation verification is now integrated into the quality pipeline per requirement 4.
- Build a local RAG over cloud docs. Disk is no longer the blocker but Lightpanda + verify-or-remove is simpler.
