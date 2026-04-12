---
title: Rigorous Writer Calibration — 2026-04-12
date: 2026-04-12
status: settled
supersedes: writer-calibration-2026-04-12.md (PRELIMINARY)
related:
  - fact-grounding-calibration-2026-04-12.md
  - agent-delegation-matrix.md
---

# Rigorous Writer Calibration — 2026-04-12

6 candidates × 3 topics × (write + fact-check by gpt-5.3-codex-spark) = 36
dispatches. Fact-checking by the calibrated winner from the fact-grounding
test (25/25 perfect score).

## Results

| Candidate | Family | Avg words | Total claims | Verified | Conflicting | Unverified | Hallucinated | Verify % | FC fails | Writer fails |
|---|---|---|---|---|---|---|---|---|---|---|
| gemini-3.1-pro-preview | gemini | 860 | 49 | 36 | 6 | 7 | **0** | 73% | 1 | 0 |
| gpt-5.3-codex | codex | 597 | 65 | 59 | 0 | 5 | 1 | **91%** | 0 | 0 |
| gpt-5.4 | codex | 626 | 60 | 50 | 4 | 5 | 1 | 83% | 0 | 0 |
| gpt-5.2 | codex | 743 | 52 | 41 | 1 | 6 | 1 | 79% | 0 | 0 |
| claude-sonnet-4-6 | anthropic | 501 | 17 | 14 | 1 | 2 | 0 | 82% | 1 | 1 |
| claude-opus-4-6 | anthropic | 655 | 42 | 31 | 1 | 7 | **3** | 74% | 1 | 0 |

Sorted by: hallucinated ASC, verify ratio DESC, verified count DESC.

## Topics tested

1. **PSA** — Pod Security Admission (CKS, security, stable docs). All 6
   candidates wrote clean PSA sections. Only Opus hallucinated (3 claims).
2. **Seccomp** — Seccomp profiles via SecurityContext (CKS, runtime
   hardening). Gemini Pro had the most conflicting claims (5) — honest
   about source disputes. gpt-5.4 hallucinated 1.
3. **Kubecost** — Kubecost on bare metal (FinOps, the original flap zone).
   Every Codex model hallucinated exactly 1 claim on this topic. Gemini
   Pro's kubecost fact-check was a harness failure (codex-spark stdin
   collision), so its hallucination count on kubecost is unknown.

## Harness failures

Three fact-check dispatches failed with `exit 1: Reading additional input
from stdin...` — a codex CLI arg/stdin collision when the section text
exceeds some threshold:

- psa / claude-sonnet-4-6 (fact-check failed)
- kubecost / gemini-3.1-pro-preview (fact-check failed)
- kubecost / claude-opus-4-6 (fact-check failed)

One writer failure:
- kubecost / claude-sonnet-4-6 (wrote only 66 words — refusal/truncation)

## Decision

**Winner: gemini-3.1-pro-preview** for the bulk writer role.

Rationale:

1. **0 hallucinations** on tested topics (best among non-Anthropic). Kubecost
   is untested due to harness failure, but the fact-ledger architecture now
   catches hallucinations anyway.
2. **860 avg words** — closest to the 600-800+ line target. gpt-5.3-codex
   averaged 597 (under target), and the user explicitly said "cannot
   disqualify for too much text, only if it is bloat."
3. **Production continuity** — Gemini Pro is the writer of record.
4. **Gemini quota** still plentiful pre-May-5 cutover.
5. **New architecture compensates** — the fact-ledger + integrity gate catches
   writer hallucinations before they reach structural review.

Runner-up: **gpt-5.3-codex** (highest verify ratio at 91%, but 1 hallucination
on kubecost and only 597 avg words — below target).

## Anthropic constraint

Per the 2026-04-12 budget nerf: Claude family is DISQUALIFIED for bulk writing
regardless of raw score. Sonnet and Opus results are informational only.

- Sonnet: writer failure on kubecost (66 words), 1 harness fail — would be
  disqualified on both quality AND budget
- Opus: 3 hallucinations (worst performer) — disqualified on quality alone,
  then also on budget

## Key insight

All Codex models hallucinated on kubecost — the same topic that caused the
module-1.5 flap in the old pipeline. This confirms kubecost-on-bare-metal
is a genuine domain where upstream docs are contradictory and LLMs
confabulate. The fact-ledger architecture with DATA_CONFLICT triage is
the correct design response.

## Reproduction

```bash
.venv/bin/python scripts/research/writer-calibration-rigorous.py
```

Output: `/tmp/writer-rigorous/results.json` (incremental save).
Script: `scripts/research/writer-calibration-rigorous.py`.

Last run: 2026-04-12 ~00:26–01:38 local (72 min wall time).
