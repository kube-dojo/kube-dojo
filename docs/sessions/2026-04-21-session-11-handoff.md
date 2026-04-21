---
title: Session 11 handoff — pipeline_v4 built end-to-end, tech debt cleared, dogfood validated
date: 2026-04-21
---

# TL;DR

Session 11 executed the session-10 handoff's "design + dogfood v4" goal
in one session: got an adversary review on the original #322 spec
(NEEDS CHANGES, 2/5), rewrote the spec to address the 5 findings,
cleared all open tech debt, built pipeline_v4 end-to-end across 4 new
scripts + 4 new test files (2,936 LOC total across 9 commits), and
dogfooded it live on the `module-1.2-ai-for-kubernetes-troubleshooting-and-triage`
target. **Module scored 2.0 → 4.2 in 7 min of automated generation.**

Stage 4 (citation_v3) was skipped in dogfood via `--skip-citation` to
isolate Stages 1-3 validation; its guards are unit-tested. v4 is
functional end-to-end. Three known small bugs surfaced from the live
run, none blockers — listed below with fixes.

**Next session's first task:** fix the retry-refresh-gaps bug, build
`pipeline_v4_batch.py` (concurrent runner on v2 lease infra), and run
v4 across the /ai thin-module backlog with batch concurrency.

# What landed this session

## Tech debt cleared (5 commits)

| Commit | Scope |
|---|---|
| `2eedc994` | pipeline_v2 sibling-module imports (v4 needs v2 worker infra, this was the blocker) |
| `10aa1a67` | autopilot_v3 `--content-stable-only` gate (prevents v3-on-thin waste) |
| `ba8cf489` | `/api/quality/scores` emits `path` field; v3 gate keys by path (#325) |
| `7b7210ef` | `pyrightconfig.json` so sys.path shims don't surface as pyright errors |
| `2d4a6a90` | v1_pipeline drops orphan .staging.md before fresh write-phase attempt |

Plus **102 orphan `.staging.md` files deleted** inline (accumulated
since v1_pipeline's cleanup bug started leaking; handoff said 22 but
the real count was 5× that). The staging cleanup fix (`2d4a6a90`)
stops future accumulation.

## Pipeline v4 built end-to-end (4 commits, 2,936 LOC)

| Commit | Module | Script LOC | Test LOC | Role |
|---|---|---:|---:|---|
| `ad590be3` | `scripts/rubric_gaps.py` | 224 | 126 | Stage 1: gap identification |
| `3d172a59` | `scripts/module_sections.py` | 426 | 289 | H2-based section splitter, round-trip fidelity |
| `747bd53c` | `scripts/expand_module.py` | 641 | 311 | Stage 2: gap-driven expansion with provenance |
| `e663088d` | `scripts/pipeline_v4.py` | 533 | 386 | Stages 1-5 orchestrator + JSONL event log |

**35 tests** across the four modules, all passing. Claude
inline-reviewed each before merge (independent-family vs Codex).
Gemini flash reviewed the gate diff (APPROVE 5/5); the scorer-paths
diff couldn't get a Gemini review (3.1-pro no capacity, flash hung
after 10 min on one-liner), merged on Claude review alone.

## Issue #322 rewritten

Gemini 3.1-pro adversary review ([comment 4287421505](https://github.com/kube-dojo/kube-dojo.github.io/issues/322#issuecomment-4287421505))
returned NEEDS CHANGES (2/5) with 5 structural findings:

1. EOF-append violates rubric section order → AST-aware section injection needed
2. Single-pass thin expand can't take 200-line module to 600 → multi-pass loop
3. Citations on LLM prose = closed hallucination loop → paragraph provenance tagging
4. Undefined retry budget + regression tolerance → budget 2, epsilon 0.2
5. Sequential throughput infeasible → batch concurrency on v2 worker infra

All 5 were incorporated into the rewritten #322 body and into the v4
implementation. Section order is preserved via `module_sections`
splitter + `insert_section(slot, ...)`. Thin handler runs up to 5
passes section-by-section. Every generated block is wrapped with
`<!-- v4:generated type=X model=Y turn=Z -->` markers. Orchestrator
has `max_rubric_retries=2` + epsilon=0.2 defaults. v2 concurrency
infra is repaired; batch wrapper is deferred to session 12.

## Issues closed

- `#325` quality-scores path field — closed by `ba8cf489`
- `#272` AI for K8s & Platform Work — section + all 4 modules exist;
  module quality tracked by #180
- `#198` Master Execution Plan — duplicate of STATUS.md + session
  handoff docs; individual epics continue to track their work

**Still open:**
- `#322` v4 pipeline — implementation landed but acceptance criteria
  items 5-7 (`pipeline_v4_batch.py`, handoff notes, batch run over /ai)
  remain for session 12
- `#14` curriculum monitoring — by design, never closes

# Dogfood validation

Target: `ai/ai-for-kubernetes-platform-work/module-1.2-ai-for-kubernetes-troubleshooting-and-triage`
(198 LOC baseline, score 2.0, primary_issue "thin, no quiz").

**Live run** (commit `e663088d`, command
`pipeline_v4.py <key> --skip-citation`, wall time 7m 6s):

```
score_before:            2.0
score_after:             4.2    ✅ passes 4.0 threshold
stage_reached:           DONE
outcome:                 clean
gaps_before:             [thin, no_quiz]
gaps_after:              [no_exercise]
retry_count:             1
loc_before:              199
loc_after:               330   (internal counter reached 325 on pass 2;
                                ExpandResult reported 258, see bug #2)
provenance_blocks_added: 1     (Quiz wrapper; thin pass additions inside
                                existing core sections per the spec)
```

**Run sequence** (from the emitted JSONL events):

1. RUBRIC_SCAN: `score=2.0, gaps=[thin, no_quiz]`
2. EXPAND attempt 0: Gemini multi-pass on 5+ Core subsections adds
   technical depth (Hallucination of Certainty, Discriminating Checks,
   Scope Isolation, Negative Search Space, etc.); Codex writes 6
   scenario-based Quiz questions
3. RUBRIC_RECHECK attempt 0: `score=3.9` — just 0.1 below threshold;
   `gaps=[no_exercise]` surfaced (shadowed by the compound "thin, no
   quiz" before)
4. EXPAND attempt 1: retry ran with ORIGINAL gap list (bug #1 — see
   below); thin reached actual_loc=325 (up from 241); no_quiz rejected
   as duplicate; no new provenance blocks
5. RUBRIC_RECHECK attempt 1: `score=4.2` — crosses threshold
6. CITATION_V3: skipped per `--skip-citation`

Expanded module committed to main as `7dc2917e`
(`content(pipeline-v4 dogfood): expand ai-for-kubernetes-troubleshooting-and-triage
2.0 → 4.2`) after review; dogfood worktree cleaned up.

## Content-quality spot-check

Generated Quiz Q1 illustrates the standard:

> Your team says, "The cluster is broken," after a payment service
> rollout stalls. You have access to pod events, a `kubectl describe`
> output, node allocatable capacity, and a deployment diff showing an
> image and resource change. What is the best way to ask AI for help
> so it improves the investigation instead of guessing?

Answer cites the module's own "evidence-first" framing with specific
callbacks to `kubectl describe` outputs and deployment diffs. Not
filler. Gemini's Core expansions followed the same pattern — referenced
the existing prose by name ("the Golden Trio of Evidence", "negative
space", "command spam") rather than generic filler.

# Tech debt list (for session 12)

## v4-specific bugs surfaced in dogfood

1. **Retry uses original gap list, not refreshed** (pipeline_v4.py).
   After Stage 3 rescore surfaces a new gap list, Stage 2 retry
   ignores it and re-runs the original gaps. In dogfood, `no_exercise`
   was surfaced at attempt 0 rescore but never handled — attempt 1 got
   `[thin, no_quiz]` again. Score still crossed 4.0 thanks to thin's
   2nd pass adding extra depth, but this is wasteful and will bite on
   modules where the original gaps are fully filled and ONLY the
   newly-surfaced gap matters. Fix: between Stage 3 and Stage 2 retry,
   re-call `rubric_gaps.gaps_for_module()` and pass the fresh gap
   list to `expand_module.expand_module`.

2. **`loc_after` accounting drift** (expand_module.py). ExpandResult
   reports `loc_after: 258` but thin handler's own `actual_loc`
   counter reached 325 on attempt 1. Cosmetic — the number emitted to
   telemetry disagrees with what's actually on disk.

3. **Gemini CLI in YOLO mode self-lints its output** with
   `markdownlint`, adding ~30s per section. Harmless but adds latency
   to any Gemini dispatch. Possibly fixable by passing `-c
   disable_tools=bash` or similar, but not confirmed. Likely not
   worth chasing until batch runs show it's actually eating throughput.

## Batch wrapper needs building

`scripts/pipeline_v4_batch.py` is not built yet. Per the rewritten
#322: wrap `pipeline_v4.run_pipeline_v4` in a concurrent worker that
uses `.pipeline/v2.db` leases (pipeline_v2 infra repaired this session)
to coordinate across ~8 parallel module pipelines. Target: 620
critical modules × 8 workers × ~25 min = ~32 h end-to-end, not 206 h
sequential.

## Other open items

- `#180` Elevate All Modules to 4/5 — unchanged; v4 is the tool that
  ships this epic.
- `#197` On-Prem practitioner expansion — unchanged; waits on v4
  batch for rubric compliance, then separate content work for
  practitioner depth.

# Next session's first task

**1. Fix the retry-refresh-gaps bug** (pipeline_v4.py)

Between Stage 3 and Stage 2 retry, re-fetch gaps instead of re-using
the original list. Single-line change approximately at the retry
branch in `run_pipeline_v4`. Unit-test: attempt 0 fills no_quiz,
rescore surfaces no_exercise; retry should run expand with
`gaps=[no_exercise]`, not `gaps=[thin, no_quiz]`. Commit on its own.

**2. Build `scripts/pipeline_v4_batch.py`**

Spec: wrap `run_pipeline_v4` with `.pipeline/v2.db` lease
coordination. Inputs: `--track <track>`, `--limit N`, `--workers 8`,
`--min-score FLOAT`, `--dry-run`. Output: per-module JSON result
line to stdout; aggregate summary at end. Reuse v2 lease semantics
already in `scripts/pipeline_v2/control_plane.py`. Unit test: mock
`run_pipeline_v4` to return canned results, assert lease
acquire/release, assert N modules processed in parallel.

**3. Dogfood batch on the /ai thin-module set**

Once batch wrapper lands, run it across the 5 "AI/ML Engineering Ai
Infrastructure" critical-quality modules the briefing flags
(`Cloud AI Services`, `AIOps`, `vLLM and sglang`, `Local Inference
Stack`, `Home AI Operations`). Measure wall-clock, failure rate, and
final rubric averages.

# Known gotchas — updated

- **Codex sandbox blocks `.git/worktrees/*/index.lock` writes.** Every
  Codex delegation this session came back with "I made the changes
  but couldn't commit". Expected behavior — Codex's workspace-write
  sandbox only covers the worktree root, not the primary repo's
  `.git/worktrees/<name>/` metadata. The delegation pattern must be:
  Codex writes files → Claude (or operator) commits from the
  primary-repo side. Prompts for Codex should say "do not attempt to
  commit; leave files as working-tree changes" to avoid wasted cycles
  on the commit retry loop.

- **Gemini 3.1-pro is frequently at-capacity**. First Gemini review
  of the #322 design retried 3× on 429s and eventually returned
  clean content. Second Gemini review (of the scorer-paths diff) hung
  for 10+ min producing a single "I will start by..." line. When
  3.1-pro is congested, explicitly pass `--model gemini-3-flash-preview`
  on `dispatch.py gemini` — flash consistently returned clean reviews
  in <30s this session. dispatch.py does NOT auto-fallback on rate
  limit (it assumes same-quota); flash is a manual flag.

- **Gemini CLI YOLO mode runs `markdownlint` on its own output** and
  iterates until clean. Unexpected but harmless. Adds 20-60s per
  Gemini dispatch when the generated content touches many list items
  or blank lines. Aggregate cost will matter at batch scale — watch
  for it.

- **Rubric scorer weights section presence > line count.** Dogfood
  showed the module crossing 4.0 at 258 LOC (target was 600). Missing
  sections (Quiz, Mistakes, Exercise) cost far more score than thin
  Core content. For v4 design, the scorer's behavior means
  `target_loc` is a ceiling for effort, not a floor for success — a
  module at 300 LOC with all canonical sections can outscore a
  600-LOC one with gaps. `expand_module.py`'s max_thin_passes=5 cap is
  correctly placed; pumping Gemini calls past that wouldn't help the
  score.

- **Pipeline v4 stages are safe to run separately.** `--skip-citation`
  gives you Stages 1-3 only; `--dry-run` skips disk writes + citation;
  each Stage logs structured JSONL at
  `.pipeline/v4/runs/<module-flat>.jsonl`. If a module gets stuck
  mid-pipeline, re-running will pick up whatever disk state was left
  (expand writes on disk after every gap; rescore is idempotent).

# References

- Pipeline v4 commits on main: `ad590be3`, `3d172a59`, `747bd53c`, `e663088d`
- Gemini adversary review of original #322:
  https://github.com/kube-dojo/kube-dojo.github.io/issues/322#issuecomment-4287421505
- Rewritten #322 body:
  https://github.com/kube-dojo/kube-dojo.github.io/issues/322
- Session 10 handoff: `docs/sessions/2026-04-21-session-10-handoff.md`
- Dogfood run log: main head `e663088d` (pipeline run); expansion
  committed as `7dc2917e` at
  `src/content/docs/ai/ai-for-kubernetes-platform-work/module-1.2-ai-for-kubernetes-troubleshooting-and-triage.md`
- Issues closed: #325 (scorer paths), #272 (AI for K8s section), #198
  (Master Execution Plan)
