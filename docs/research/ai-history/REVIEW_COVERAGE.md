# AI History Review Coverage

`review_coverage` is the per-chapter audit block used to track whether AI
History research and prose reviews satisfy the cross-family rule for Issue #559.
It lives in each chapter status file:

`docs/research/ai-history/chapters/ch-NN-slug/status.yaml`

## Schema

```yaml
review_coverage:
  research:
    claude_anchor: done | pending | n/a
    gemini_gap: done | pending | n/a
    codex_anchor: done | pending | n/a
  prose:
    claude_source_fidelity: done | pending | n/a
    gemini_prose_quality: done | pending | n/a
    codex_prose_quality: done | pending | n/a
  cross_family_satisfied:
    research: true | false
    prose: true | false
    overall: true | false
  backfill_pending: true | false
  last_audited: 2026-04-29
```

Field values:

- `done`: the audit found the expected review marker.
- `pending`: the marker is expected but has not been found yet.
- `n/a`: that reviewer is not expected for this chapter or lane.
- `cross_family_satisfied.research`: true when the research lane has the two
  non-author reviewer families required by the chapter ownership model.
- `cross_family_satisfied.prose`: true when the prose lane has the two
  non-author reviewer families required by the chapter ownership model.
- `cross_family_satisfied.overall`: true only when both lanes are satisfied.
- `backfill_pending`: true exactly when `cross_family_satisfied.overall` is
  false.
- `last_audited`: date the block was last written by the audit script.

## Cross-Family Rule

Each lane needs at least one reviewer from each non-author model family.

Author mapping for this audit:

| Chapters | Author family | Required research markers | Required prose markers |
|---|---|---|---|
| Ch01-Ch15 | Claude | `codex_anchor`, `gemini_gap` | `codex_prose_quality`, `gemini_prose_quality` |
| Ch16-Ch72 | Codex | `claude_anchor`, `gemini_gap` | `claude_source_fidelity`, `gemini_prose_quality` |

Self-review markers may still be recorded as `done` when present, but they do
not satisfy the cross-family rule.

## Running The Audit

Run from the repository root:

```bash
.venv/bin/python scripts/audit_review_coverage.py
```

The script fetches merged PRs with `gh pr list`, reads PR comments with
`gh api`, detects marker tags, computes `review_coverage`, writes each
`status.yaml`, and prints a summary table.

Use strict mode when you want the command to fail instead of using the offline
fallback:

```bash
.venv/bin/python scripts/audit_review_coverage.py --strict-gh
```

This worktree could not reach `api.github.com` on 2026-04-29, so the initial
schema application used the script's conservative local fallback. Rerun with
GitHub access before relying on the audit as marker-authoritative.

## Coverage Summary

Initial audit source: offline fallback because `gh` could not reach GitHub.

| chapter | research | prose | backfill_pending | source |
|---|---:|---:|---:|---|
| ch-01-the-laws-of-thought | false | true | true | offline |
| ch-02-the-universal-machine | false | true | true | offline |
| ch-03-the-physical-bridge | false | true | true | offline |
| ch-04-the-statistical-roots | false | true | true | offline |
| ch-05-the-neural-abstraction | false | true | true | offline |
| ch-06-the-cybernetics-movement | false | true | true | offline |
| ch-07-the-analog-bottleneck | false | true | true | offline |
| ch-08-the-stored-program | false | true | true | offline |
| ch-09-the-memory-miracle | false | true | true | offline |
| ch-10-the-imitation-game | true | true | false | offline |
| ch-11-the-summer-ai-named-itself | true | true | false | offline |
| ch-12-logic-theorist-gps | true | true | false | offline |
| ch-13-the-list-processor | true | true | false | offline |
| ch-14-the-perceptron | true | true | false | offline |
| ch-15-the-gradient-descent-concept | true | true | false | offline |
| ch-16-the-cold-war-blank-check | true | true | false | offline |
| ch-17-the-perceptron-s-fall | false | true | true | offline |
| ch-18-the-lighthill-devastation | false | true | true | offline |
| ch-19-rules-experts-and-the-knowledge-bottleneck | false | true | true | offline |
| ch-20-project-mac | false | true | true | offline |
| ch-21-the-rule-based-fortune | false | true | true | offline |
| ch-22-the-lisp-machine-bubble | false | true | true | offline |
| ch-23-the-japanese-threat | false | true | true | offline |
| ch-24-the-math-that-waited-for-the-machine | false | false | true | offline |
| ch-25-the-universal-approximation-theorem-1989 | false | false | true | offline |
| ch-26-bayesian-networks | false | false | true | offline |
| ch-27-the-convolutional-breakthrough | false | false | true | offline |
| ch-28-the-second-ai-winter | false | false | true | offline |
| ch-29-support-vector-machines-svms | false | false | true | offline |
| ch-30-the-statistical-underground | false | false | true | offline |
| ch-31-reinforcement-learning-roots | false | false | true | offline |
| ch-32-the-darpa-sur-program | false | true | true | offline |
| ch-33-deep-blue | false | true | true | offline |
| ch-34-the-accidental-corpus | false | true | true | offline |
| ch-35-indexing-the-mind | false | true | true | offline |
| ch-36-the-multicore-wall | false | true | true | offline |
| ch-37-distributing-the-compute | false | true | true | offline |
| ch-38-the-human-api | true | true | false | offline |
| ch-39-the-vision-wall | true | true | false | offline |
| ch-40-data-becomes-infrastructure | true | true | false | offline |
| ch-41-the-graphics-hack | true | true | false | offline |
| ch-42-cuda | true | true | false | offline |
| ch-43-the-imagenet-smash | true | true | false | offline |
| ch-44-the-latent-space | true | true | false | offline |
| ch-45-generative-adversarial-networks | true | true | false | offline |
| ch-46-the-recurrent-bottleneck | true | true | false | offline |
| ch-47-the-depths-of-vision | true | true | false | offline |
| ch-48-alphago | true | true | false | offline |
| ch-49-the-custom-silicon | true | true | false | offline |
| ch-50-attention-is-all-you-need | true | true | false | offline |
| ch-51-the-open-source-distribution-layer | true | true | false | offline |
| ch-52-bidirectional-context | true | true | false | offline |
| ch-53-the-dawn-of-few-shot-learning | true | true | false | offline |
| ch-54-the-hub-of-weights | true | true | false | offline |
| ch-55-the-scaling-laws | true | true | false | offline |
| ch-56-the-megacluster | true | true | false | offline |
| ch-57-the-alignment-problem | true | true | false | offline |
| ch-58-the-math-of-noise | true | true | false | offline |
| ch-59-the-product-shock | true | true | false | offline |
| ch-60-the-agent-turn | true | true | false | offline |
| ch-61-the-physics-of-scale | true | true | false | offline |
| ch-62-multimodal-convergence | true | true | false | offline |
| ch-63-inference-economics | true | true | false | offline |
| ch-64-the-edge-compute-bottleneck | true | true | false | offline |
| ch-65-the-open-weights-rebellion | true | true | false | offline |
| ch-66-benchmark-wars | true | true | false | offline |
| ch-67-the-monopoly | true | true | false | offline |
| ch-68-data-labor-and-the-copyright-reckoning | true | true | false | offline |
| ch-69-the-data-exhaustion-limit | true | true | false | offline |
| ch-70-the-energy-grid-collision | true | true | false | offline |
| ch-71-the-chip-war | true | true | false | offline |
| ch-72-the-infinite-datacenter | true | true | false | offline |

`backfill_pending_count: 30`
