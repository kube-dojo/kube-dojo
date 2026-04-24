# 2026-04-24 — Quality Pipeline v2 implementation handoff

**State on handoff**: v2 implemented as `scripts/quality/` package. 610 tests green, ruff clean, 10 commits ahead of `origin/main` on `main`. Not pushed. All 10 v1 Codex must-fixes + 10 v2 Codex must-fixes (across 4 review rounds) have regression-guard tests. **No real modules touched yet** — final Codex approve still pending before the smoke run.

**Next session task**: run one more Codex re-review on commit `ec681076`; if approved, smoke on `k8s-capa-module-1.2-argo-events`; scale from there.

## Cold-start smoketest

```bash
# 1. State of play
curl -s http://127.0.0.1:8768/api/briefing/session?compact=1 | head -40
git log --oneline origin/main..HEAD       # should list 10 commits, top = ec681076
.venv/bin/python -m pytest tests/test_quality_*.py -q   # 131 quality tests, all pass
.venv/bin/ruff check scripts/quality/ tests/test_quality_*.py   # clean

# 2. If confident → skip to step 3. Otherwise, run one more Codex pass:
codex exec --skip-git-repo-check --sandbox read-only -m gpt-5.5 \
    -c model_reasoning_effort="high" - \
    < /tmp/kd_v2_fourthreview.md \
    > /tmp/kd_v2_passN_output.txt 2>&1
# (prior prompts: /tmp/kd_v2_review.md, /tmp/kd_v2_rereview.md, /tmp/kd_v2_finalreview.md, /tmp/kd_v2_fourthreview.md)

# 3. Smoke on one real module (k8s-capa-module-1.2-argo-events exists
# and has a teaching-audit JSON on disk already).
.venv/bin/python -m scripts.quality.pipeline bootstrap
.venv/bin/python -m scripts.quality.pipeline status | head
.venv/bin/python -m scripts.quality.pipeline run-module k8s-capa-module-1.2-argo-events

# Expect: final state == COMMITTED, .worktrees/ empty, new commit on main.
```

If anything other than `COMMITTED` comes back, the status + logs tell you which stage failed. Don't retry without inspecting — per `feedback_codex_review_before_running`, iterate with Codex rather than pushing through.

## What shipped this session

Ten commits on `main`, all under issue #375:

| SHA | Title |
|-----|-------|
| `8e7be95b` | Phase A — state, worktree, extractors |
| `b9798ed9` | Phase B — dispatchers, prompts, citations |
| `26bd0fed` | Phase C — stages, pipeline orchestrator |
| `eb705026` | v1→v2 state migration (module_index) |
| `3825726a` | STATUS snapshot after Phase C |
| `6c62584b` | Codex round-1 fixes — 2 fatals + 7 musts |
| `b50cfe2e` | Codex round-2 — cleanup-only write_text leak |
| `59001cbc` | Codex round-3 — wrap entire cleanup-only finalization |
| `ec681076` | Codex round-4 — post-create-worktree windows + st2-is-None |
| (GitHub comment on #375 with Phase A-C coverage table) | |

Plus this handoff commit.

## Codex review rounds (for context)

| Round | Verdict | Findings | Commit addressing |
|-------|---------|----------|---------------------|
| 1 | `changes_requested` | 2 fatal + 7 must + 3 nit (9 items closed) | `6c62584b` |
| 2 | `changes_requested` | 1 new must (cleanup-only write_text leak) + 1 nit | `b50cfe2e` |
| 3 | `changes_requested` | 1 new must (post-create finalization unguarded) | `59001cbc` |
| 4 | `changes_requested` | 2 new musts (post-create-worktree window + st2-is-None) | `ec681076` |

Pattern: Codex is systematically walking the cleanup-only path's exception surface. Each round uncovers one more edge case. After round 4 the entire post-`create_worktree` block is inside one `try/except BaseException` with explicit `worktree_owned_by_next_stage` tracking. I'd expect round 5 to approve — if it rejects, it's finding something genuinely subtle.

## Codex must-fix mapping (where each is closed)

| Item | File:line | Regression test |
|------|-----------|-----------------|
| **v1 #1** reviewer reads wrong file | `stages.py::review_one` reads from `worktree_dir(slug)/module_rel` | `test_reviewer_reads_module_from_worktree_not_primary` |
| **v1 #2** primary checkout mutation | `stages.py::citation_verify_one` cleanup-only path creates own worktree | `test_cleanup_only_never_writes_primary_checkout` |
| **v1 #3** ff-merge breaks after first merge | `worktree.py::rebase_onto_main` before `merge_ff_only` | `test_ff_merge_after_main_advances_with_real_pipeline_modules` |
| **v1 #4** REVIEW_CHANGES dead-end | `stages.py::handle_review_changes` | `test_review_changes_routes_back_to_write_pending_with_retry_count`, `test_review_changes_tiebreaker_after_cap` |
| **v1 #5** write crash-resume false-positive | `stages.py::_recover_write_in_progress` uses `git rev-list --count main..<branch>` | `test_recovery_does_not_trust_stale_branch_at_old_main` |
| **v1 #6** git cleanup not in finally | `stages.py::_write_in_worktree` wraps all in `try/except BaseException` | `test_write_cleanup_even_when_commit_fails` |
| **v1 #7** `_extract_module_markdown` too weak | `extractors.py::extract_module_markdown` | 14 tests in `test_quality_extractors.py` |
| **v1 #8** `_extract_json` first-balanced bug | `extractors.py::extract_last_json` | `test_last_matching_json_wins_over_reasoning_json` |
| **v1 #9** worktree venv bug | `worktree.py::primary_checkout_root` ported | `test_primary_checkout_root_strips_worktree_layout` |
| **v1 #10** no state lease/CAS | `state.py::state_lease` + `transition` | `test_lease_blocks_concurrent_holder`, `test_transition_rejected_when_disk_advanced_underneath` |
| **v2 round-1 fatal #1** cleanup-only mutates primary | `stages.py::citation_verify_one` creates own worktree | `test_cleanup_only_never_writes_primary_checkout` |
| **v2 round-1 fatal #2** high-score no-op can't merge | transitions to `SKIPPED` (terminal) | `test_cleanup_only_no_changes_ends_at_skipped_without_merge` |
| **v2 round-1 must #3** CITATION_VERIFY not resumable | `citation_origin` field + registered in `_STAGE_FN` | `test_citation_verify_is_resumable_after_sigkill` |
| **v2 round-1 must #5** multi-worker merge race | `_merge_lock` + retry cap | `test_merge_retries_on_transient_rebase_failure`, `test_merge_lock_timeout_reaches_fail_and_cleanup` |
| **v2 round-1 must #6** strict citation for unparseable | `rebuild_section` drops non-bullet URL lines | `test_rebuild_drops_non_bullet_url_lines`, `test_process_drops_section_with_only_unparseable_urls`, `test_process_preserves_pure_prose_sources_section` |
| **v2 round-1 must #7** score gate missing | `_parse_review_verdict` demotes approve < 4.0 | `test_approve_verdict_demoted_when_score_below_gate`, `test_approve_verdict_demoted_when_score_missing`, `test_approve_verdict_kept_when_both_scores_meet_gate` |
| **v2 round-1 must #9** FAILED leaks branches | `_fail_and_cleanup` wrapper | `test_failed_modules_have_branches_cleaned_up` |
| **v2 round-2 must** cleanup-only write_text leak | `write_text` inside shared handler | `test_cleanup_only_removes_worktree_when_write_text_raises` |
| **v2 round-3 must** post-create finalization | big `try/except BaseException` wraps everything | `test_cleanup_only_removes_worktree_when_lease_raises_after_create` |
| **v2 round-4 must** post-create windows | even earlier start of handler | `test_cleanup_only_scrubs_worktree_when_state_file_disappears` |

## Strict citation policy (user-locked this session)

"We don't publish lies." Implemented in `citations.py`:

- `supports` (page clearly and explicitly backs the claim) → **keep**
- `partial` / `no` / fetch-fail / verifier-error / ambiguous → **remove**
- Non-bullet URL lines inside `## Sources` (e.g. `See https://... for details`) → **remove** — strict policy is every URL must be a parseable bullet AND verified
- `## Sources` section with no parseable entries but URLs present → **drop entire section**
- Pure prose `## Sources` (no URLs, e.g. "Adapted from Kleppmann's DDIA") → **preserved**

No grandfathering — applies to existing citations, writer-added citations, and the 189 findings queued in `.pipeline/v3/human-review/`.

## What the next session should NOT do

- **Don't run `run-module` / `run` against real modules until Codex approves** (same rule as from the prior handoff — self-smoke ≠ review).
- Don't push to `origin/main` without explicit user approval. 10 commits waiting.
- Don't delete `.pipeline/quality-pipeline/*.json` — the migration in `bootstrap` handles v1 state transparently. A wipe loses 21 already-promoted AUDITED states.
- Don't raise `--workers` above 3. Hard cap per `feedback_batch_worker_cap.md` memory. Default 1.
- Don't let Gemini-flash citation verify run at full bore without sampling output first — strict policy is only as good as the verdict JSON, and a misbehaving verifier could falsely remove legitimate citations. Sample 10-20 verdicts before full sweep.
- Don't extend `quality_pipeline.py` (v1). The package at `scripts/quality/` is the new one. v1 is kept in git history as reference only.

## Expected smoke run behavior (mental model for "is it working")

The smoke module is `src/content/docs/k8s/capa/module-1.2-argo-events.md`. Its permanent `module_index` is determined by sorted-path position at bootstrap time (around ~200s in 742).

Under `run-module`:
- Audit is already done (`.pipeline/teaching-audit/k8s-capa-module-1.2-argo-events.json` exists). → `AUDITED`
- Route reads score + structural. At score 1.5 → `WRITE_PENDING` with track=rewrite. Writer assigned by `i%2`.
- Write: Codex OR Claude (depending on module_index parity) dispatches a rewrite in worktree. → `WRITE_IN_PROGRESS` → `WRITE_DONE`.
- Citation verify: Lightpanda + Gemini-flash for each URL in `## Sources`. Likely 5-10 URLs. → `CITATION_VERIFY` → `REVIEW_PENDING`.
- Review: cross-family reviewer (the OTHER of Codex/Claude) reads from worktree. Must return `approve` with scores ≥ 4.0 on both axes. → `REVIEW_APPROVED`.
- Merge: rebase + ff-merge. Worktree + branch torn down. → `COMMITTED`.

Any stage failing is a real signal. In particular: if review returns `changes_requested`, that's `REVIEW_CHANGES` → back to `WRITE_PENDING` with `retry_count=1`. After 2 retries, Gemini tiebreaker.

## Pipeline CLI reference

```bash
.venv/bin/python -m scripts.quality.pipeline bootstrap    # idempotent
.venv/bin/python -m scripts.quality.pipeline status -v    # counts + FAILED list
.venv/bin/python -m scripts.quality.pipeline run-module <slug>     # single module
.venv/bin/python -m scripts.quality.pipeline run --workers 1 --limit 10    # batch
.venv/bin/python -m scripts.quality.pipeline reset-stage <slug> <stage>    # admin
```

Sub-stages (`audit`, `route`) can drive the state machine forward one step at a time, useful when investigating a stuck module. Normal operation is `run`.

## Package layout

```
scripts/quality/
├── __init__.py        # package docstring
├── state.py           # fcntl.flock lease + CAS transitions
├── worktree.py        # worktree lifecycle + primary_checkout_root
├── extractors.py      # module-markdown + last-balanced-JSON
├── dispatchers.py     # Codex/Claude/Gemini wrappers + round-robin
├── prompts.py         # rewrite/structural/review/citation-verify builders
├── citations.py       # Lightpanda fetch + strict verify-or-remove
├── stages.py          # audit/route/write/verify/review/merge + recover
└── pipeline.py        # CLI orchestrator

tests/
├── test_quality_state.py        # 14 tests
├── test_quality_extractors.py   # 27 tests
├── test_quality_worktree.py     # 11 tests
├── test_quality_dispatchers.py  # 14 tests
├── test_quality_prompts.py      # 17 tests
├── test_quality_citations.py    # 32 tests
└── test_quality_stages.py       # 26 tests
(total: 141 in quality; 610 total repo-wide)
```

## Reference

- Issue #375 — main tracking issue with phase checklist + Codex coverage table
- Prior handoff: `docs/sessions/2026-04-24-quality-pipeline-redesign.md` — requirements + v1 must-fix list
- Codex review prompts at `/tmp/kd_v2_{review,rereview,finalreview,fourthreview}.md`
- Codex review verdicts at `/tmp/kd_v2_{review,rereview,finalreview,fourthreview}_output.txt`
