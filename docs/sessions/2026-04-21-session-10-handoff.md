---
title: Session 10 handoff — v3 validated + human-automation layer shipped, strategic pivot to v4
date: 2026-04-21
---

# TL;DR

Session 10 executed the session-9 handoff end-to-end (PR #324 merged
after Gemini review cycle, main reconciled, 51 seeds caught up),
then dogfooded the v3 section pipeline at scale (32 modules cited
across 5 sections, 1 pipeline bug fixed), and finally shipped a
human-triggered automation layer (`autopilot_v3.py` +
`run_section_v3.py`) so the operator says "go" once and the
machine drains the queue.

**Strategic pivot noted at session end:** running v3 on thin
modules (<600 lines, missing quiz/exercises) is waste because v4's
body expansion will invalidate anchor_text and shuffle citations.
Next session should design + implement v4 (issue #322) rather than
keep v3 running on the thin queue. Mature modules (aws-essentials,
azure-essentials, gcp-essentials, et al.) remain legitimate v3
work if we want to keep v3 autopilot running in parallel.

# What landed this session

## PR #324 — merged as `d89ef3de`

Two-round Gemini review (Codex was rate-limited with "high demand"
websocket errors at session start, recovered mid-session):

- **Round 1: NEEDS CHANGES** — 3 findings:
  1. `_build_sources_section_from_seed` leaked `source_ids` +
     `lesson_point_url` for non-cited dispositions (model drift would
     surface hallucinated URLs in rendered Sources).
  2. `AttributeError` risk in `section_source_discovery.py` if
     `parse_agent_response` ever returned a non-dict (defensive —
     `parse_agent_response` architecturally carves `{...}` so not
     actually exploitable, but cheap tightening).
  3. Unclosed file descriptor in `pipeline_v3_batch_commit.py`'s
     log handling (crash on Ctrl-C leaked the fd).
- **Fix commit `0e57664e`** addressed all three + bonus fix for a
  pre-existing test-isolation bug where `_load_module` helper
  created two `citation_backfill` instances, so monkeypatching
  `CITATION_POOL_DIR` missed the copy used by
  `section_source_discovery.section_pool_path_for` — the discovery
  test was silently overwriting the live
  `docs/citation-pools/platform-toolkits-cicd-delivery-gitops-deployments.json`
  on every pytest run.
- **Round 2: APPROVE.** Merged squash.

## Main reconciled — merge commit `4e672139`

Local main was 45 commits ahead of origin (session 8/9 content
work never pushed), origin had the new PR squash. Merged with
`git merge origin/main -X theirs --no-edit` so origin's
PR-validated content wins on conflicts while preserving the
local-only files (session 9 handoff most notably). Worked cleanly
— massive overlap meant many diffs were identical-in-content and
git auto-merged.

## 51 seeds catch-up — `b9337448`

Session 8/9 landed module-content commits for ~40 modules without
their paired `docs/citation-seeds/<module>.json` files. Those seeds
were sitting untracked. Gitignore excludes `.pipeline/` but not
`docs/citation-seeds/` — convention (36 prior tracked seeds) is
to commit them as source-of-truth for the research phase.
Recovered from a `git stash drop` I'd accidentally executed before
the merge (dropped stashes remain in git's reflog for ~30 days,
stash sha was printed in the drop output; `git stash apply <sha>`
got them back).

## v3 section pipeline dogfooded at scale (32 modules cited)

| Section | Modules landed | Notes |
|---|---|---|
| `platform/toolkits/cicd-delivery/source-control` | 3/3 | First post-#324 dogfood. Pool-sharing was low (gitlab/gitea/github are distinct ecosystems). |
| `ai-ml-engineering/advanced-genai` | 11/11 real modules | All 5 rubric-critical 1.5-score modules cleared. 3 `.staging.md` siblings were also processed before the filter fix (wasted ~45 min). |
| `k8s/cka/part3-services-networking` | 6/8 | **Inject_failed:** 3.1 services + 3.6 network-policies. Seeds reverted. Needs manual inspection — likely diff-lint tripping on a specific prose pattern. |
| `platform/toolkits/data-ai-platforms/cloud-native-databases` | 5/5 | Clean run. |
| `platform/toolkits/data-ai-platforms/ml-platforms` | 7/7 | Clean run. |

Commits: one per module + one per section pool, per convention.

## Pipeline bug fix — `5446d165`

`list_section_modules` was picking up `.staging.md` files
(v1_pipeline's write-phase artifacts; gitignored) and wasting
~15 min per staging file on research/verify/inject dispatches.
The advanced-genai run processed 14 modules but only 11 were
real — 3 staging copies burned Codex time and the 1.5.staging
run even inject-failed. Added a
`not path.name.endswith(".staging.md")` guard in
`scripts/section_source_discovery.py::list_section_modules`.

## Human-automation layer — `533006da`, renamed in `71348653`

Two scripts, explicitly versioned for v3 so v4 gets its own
namespace without accumulating flags:

- **`scripts/run_section_v3.py`** — one-shot end-to-end for a
  single section: preflight (git clean + codex auth) → discovery
  → per-module pipeline → per-module commit → `npm run build`
  → `git push`. New flags:
    - `--auto-pick` — resolves the densest uncited section
    - `--only-uncited` — skips modules already having `## Sources`
      so partial sections resume cleanly
    - `--min-uncited N` — threshold for auto-pick (default 3)
    - `--no-build`, `--no-push`, `--no-commit`, `--allow-dirty`,
      `--skip-preflight` — for edge cases
- **`scripts/autopilot_v3.py`** — loops `run_section_v3 --auto-pick
  --only-uncited` with a stop condition:
    - `--max-sections N` or
    - `--until-time HH:MM` (wall-clock)
    - `--dry-run` previews the queue
    - Each iteration is an independent run_section invocation so
      failures don't poison the loop; Ctrl-C between sections
      leaves no bad state.
    - Per-day JSONL log at `.pipeline/v3/autopilot/<yyyy-mm-dd>.jsonl`.

**Queue at session end:** 108 sections with ≥3 uncited modules.
Top of queue: `cloud/aws-essentials` (12/12), `cloud/azure-essentials`
(12/12), `cloud/gcp-essentials` (12/12), `cloud/advanced-operations`
(10/10), `cloud/managed-services` (10/10), etc.

## Strategic pivot noted: v3-on-thin is waste

The user raised this at session end: running v3 on modules that
will get v4 body expansion wastes the v3 work — anchor_text in
every seed references paragraphs that don't survive the rewrite.
Confirmed correct via issue #322. I wasted two runs this session
on 1.10 single-GPU (288 lines) and 1.11 multi-GPU (271 lines,
both below the 600-line minimum).

**Proposed gate (not yet implemented):** `autopilot_v3.py` should
filter the queue via `/api/quality/scores` `primary_issue` field:
only pick modules with exact `primary_issue == "no citations"`.
Anything with `"thin"` or `"no quiz"` in the issue string parks
for v4.

# Tech debt list (for v4 prep)

1. **2 CKA inject_failed modules** — 3.1 services, 3.6 network-policies.
   Seeds reverted. Need `scripts/pipeline_v3.py <key>` retry with
   the verbose output to surface the exact diff-lint rejection
   reason. Could be a systemic inject bug that'd manifest again
   at scale.
2. **`autopilot_v3.py` content-stable gate** — the v3-on-thin waste
   filter. ~20 LOC; should land before next autopilot run.
3. **pipeline v2 workers are broken** — briefing alerts:
   `ModuleNotFoundError: No module named 'scripts'` in pipeline v2
   status. v4 will likely need pipeline v2 infrastructure (workers,
   `.pipeline/v2.db`, leases); fix that before building on top.
4. **3 orphan `.staging.md` files** in `ai-ml-engineering/advanced-genai/`
   (modules 1.4, 1.5, 1.8). Gitignored, harmless in production,
   but evidence that v1_pipeline's "fresh restart drops staged
   draft" cleanup logic isn't firing. Not a blocker.
5. **Pyright false positives** on test_section_source_discovery.py
   and pipeline_v3_section.py (sys.path-based imports confuse the
   type checker). Benign.

# Next session's first task — design + dogfood v4 (issue #322)

The issue #322 has a proposed design:

```
Stage 1  RUBRIC_SCAN     → identify gaps (thin, no_quiz, no_mistakes,
                           no_exercise, …). Score >=4.0 skips to stage 4.
Stage 2  EXPAND          → one additive-only generation per gap type.
                           Codex: structured (quiz, mistakes, exercise).
                           Gemini: prose expansion.
                           Diff-lint forbids rewriting existing paragraphs.
Stage 3  RUBRIC_RECHECK  → re-score; <4.0 → human queue.
Stage 4  CITATION_V3     → run existing pipeline_v3 on now-stable content.
Stage 5  FINAL_RECHECK   → rubric didn't regress after citation pass.
```

Files to build (per issue #322):
- `scripts/rubric_gaps.py` — structured gap list from scorer
- `scripts/expand_module.py` — gap-driven expansion
- `scripts/pipeline_v4.py` — stage orchestrator
- `scripts/pipeline_v4_batch.py` — batch wrapper
- Later: `scripts/run_section_v4.py`, `scripts/autopilot_v4.py`
  (mirror the v3 human-automation layer)

**First task of session 11:**

1. **Design sanity check.** Issue #322 is a proposal, not a final
   design. Read it, push back if anything's thin. Consider: how
   does "additive-only expand" interact with a module that's
   already 500+ lines but missing quiz only vs. one that's 200
   lines needing full body fill? The current spec's single
   additive-only rule may not fit both.
2. **Dogfood target pick.** Issue #322 suggests
   `ai/ai-for-kubernetes-platform-work/module-1.2-ai-for-kubernetes-troubleshooting-and-triage`
   — but verify that module actually exists and is thin. Look at
   the briefing's `critical_quality` list for thinner-than-rubric
   modules that still have usable content to expand from.
3. **Address pipeline v2 breakage first.** v4 likely wants worker
   infrastructure. Don't build v4 on top of broken v2.
4. **Add the `autopilot_v3` content-stable gate before any more
   v3 runs.** Cheap ~20 LOC change so accidental v3-on-thin
   waste stops.

# Known gotchas — updated

- **Codex websocket under load**: smoke-check
  `echo hi | timeout 20 codex exec --full-auto --skip-git-repo-check`
  at cold start. Session 10 hit "high demand" errors at start, cleared
  within ~30 min. Gemini (`gemini-3.1-pro-preview`) is a legitimate
  family-diverse alternative reviewer when Codex is down — used it
  for the #324 review cycle.
- **`-X theirs` for main reconciliation**: when local and origin both
  touch the same content-heavy files but the origin version is the
  PR-validated canon, `git merge origin/main -X theirs` saves hours.
  Don't use it when local changes are the authority.
- **Recover dropped stashes** via the sha printed by `git stash drop`
  (git retains for ~30 days): `git stash apply <sha>`. Saved 51
  citation-seeds that I almost lost.
- **Section pool test isolation**: tests must use standard
  `sys.path.insert` + `import`, not `importlib.util.spec_from_file_location`,
  or you get two module instances and monkeypatches miss the live
  one. Fixed for `test_section_source_discovery.py`; apply the
  pattern if future tests spawn their own loaders.
- **`.staging.md` is a v1_pipeline write-phase artifact**, gitignored,
  should be invisible to downstream pipelines. Filter explicitly
  where it matters (`section_source_discovery.list_section_modules`
  does now; `pipeline_v4` enumeration should too).

# References

- PR #324 (merged): https://github.com/kube-dojo/kube-dojo.github.io/pull/324
- Issue #323 (section source pool, closed by #324):
  https://github.com/kube-dojo/kube-dojo.github.io/issues/323
- Issue #322 (v4 design, next): https://github.com/kube-dojo/kube-dojo.github.io/issues/322
- Session 9 handoff: `docs/sessions/2026-04-21-session-9-handoff.md`
- Main head at session end: check `git log --oneline -1 main`
  (last pushed was `71348653` rename commit, may be newer if
  handoff commit landed)
- Autopilot state dir: `.pipeline/v3/autopilot/` (per-day JSONL logs)
- Pipeline v3 batch logs: `.pipeline/v3/batches/<section-flat>.log`
- Pipeline v3 run records: `.pipeline/v3/runs/<module-flat>.json`
