---
title: Fact-Grounding Model Calibration
date: 2026-04-12
status: settled
related_prs: [#222, #224]
related_issues: [#223]
---

# Fact-Grounding Model Calibration — Empirical Test (2026-04-12)

## TL;DR

We empirically tested 7 LLM candidates as fact-grounders for the KubeDojo
content pipeline using 5 hard questions in the Kubecost / OpenCost / Kyverno
domain — the exact failure zone that flapped Codex on `module-1.5-onprem-finops-chargeback`
through 5 review rounds without converging. The cheapest Codex variant
(`gpt-5.3-codex-spark`, marketed as "ultra-fast coding model") scored a
perfect 25/25 with self-consistency confirmed across two runs. The frontier
Codex model (`gpt-5.4`) scored 20/25 — five points worse than the cheapest
tier in the same family — by reproducing the exact confirmation-bias
failure that flapped the pipeline in production.

**Production decision**: `MODELS["fact_grounding"] = "gpt-5.3-codex-spark"`,
fallback `claude-sonnet-4-6`. The frontier model would have shipped the same
flap problem.

## Context

After the binary quality gate shipped in PR #224, `module-1.5-onprem-finops-chargeback`
hit a never-converging review loop. Across rounds 3 and 4, Codex flip-flopped
between two contradictory IBM Kubecost docs:

- Round 3 cited *"Kubecost 3.x: Prometheus is not optional. Disabling Prometheus will result in zero costs"* with one IBM doc URL.
- Round 4 cited *"Kubecost 3.0 introduced a new agent that removes the dependency on Prometheus"* with a different IBM doc URL.

Both URLs exist. IBM publishes contradictory documentation across the 3.x release.
The pipeline applied each round's structured edits cleanly, the next round demanded
the reverse, and the module never converged.

The naive conclusion was *"LLM-as-judge for fast-moving factual content is unworkable; switch models or remove FACT entirely."* We tested that conclusion before redesigning anything.

## Methodology

### Question selection

5 hard fact-check questions in the original flap zone. Each question targets
the exact failure modes that crashed `module-1.5`:

1. **Q1 — Kubecost 3.x Prometheus dependency**. Tests whether the model recognizes IBM's contradictory documentation.
2. **Q2 — OpenCost helm `customPricing.costModel` schema**. Tests whether the model finds the canonical chart values.yaml. Codex got this wrong on module-1.5 (cited `cpuHourlyCost` / `ramHourlyCost`; actual schema uses `CPU` / `RAM` / `GPU` / `storage`).
3. **Q3 — Kyverno `validationFailureAction` deprecation**. Tests deprecation tracking.
4. **Q4 — VPA recommender metrics source**. Codex got this wrong on module-1.5 (claimed Prometheus dependency; actual source is `metrics.k8s.io` API).
5. **Q5 — OpenCost API allocation endpoint path**. Codex got this wrong on module-1.5 (cited `/allocation/compute`; actual is `/allocation`).

### Ground-truth verification

Manually verified against upstream docs:

| Q | Verified against |
|---|---|
| Q1 | Module-1.5 flap evidence — IBM publishes both narratives across 3.x docs |
| Q2 | github.com/opencost/opencost-helm-chart/blob/main/charts/opencost/values.yaml |
| Q3 | kyverno.io/docs/policy-types/cluster-policy/validate/ |
| Q4 | kubernetes.io/docs/concepts/workloads/autoscaling/vertical-pod-autoscale/ |
| Q5 | opencost.io/docs/integrations/api/ |

### Test prompt

Identical structured-JSON prompt to all candidates. Key constraints:

- Anchored `as_of_date = 2026-04-12` (eliminates time-of-dispatch variance)
- Explicit "DO NOT answer from memory" rule
- Three verdict types: `VERIFIED` / `CONFLICTING` / `UNVERIFIED`
- "Saying 'I don't know' costs you nothing. Confident wrong answers cost you a lot."
- Required citations for `VERIFIED` (URL + date) and `CONFLICTING` (≥2 URLs)
- Strict JSON output schema, no prose

Full prompt preserved in MEMORY.md → `project_fact_grounding_calibration.md`.

### Candidates tested (7 total)

| Family | Model | Tier |
|---|---|---|
| Codex | gpt-5.4 | Frontier |
| Codex | gpt-5.3-codex-spark | Ultra-fast / cheapest |
| Gemini | gemini-3.1-pro-preview | Frontier |
| Gemini | gemini-3-flash-preview | Cheapest |
| Anthropic | claude-opus-4-6 | Frontier |
| Anthropic | claude-sonnet-4-6 | Mid |
| Anthropic | claude-haiku-4-5 | Cheapest |

### Scoring rubric

- **Accuracy (max 20)**: 4 points per question for correct verdict + correct fact + canonical URL.
- **Honesty (max 5)**: 1 point per question for honest uncertainty signaling (correct `CONFLICTING` / `UNVERIFIED` when warranted, no overclaim).
- **Total: 25 points.**

Self-consistency check on the winning candidate via a second dispatch ~5 minutes later, comparing verdict-by-verdict.

## Results

### Final leaderboard

| Rank | Model | Score | Q1 (the discriminator) | Cost in family |
|---|---|---|---|---|
| 🥇 | **gpt-5.3-codex-spark** | **25/25 (100%)** | ✅ CONFLICTING + both IBM URLs cited | **Cheapest Codex** |
| 🥈 | claude-sonnet-4-6 | 23/25 (92%) | ✅ UNVERIFIED + transparent about IBM 403 | Mid Anthropic |
| 🥈 | claude-opus-4-6 | 23/25 (92%) | ✅ UNVERIFIED + transparent about IBM 403 | Frontier Anthropic |
| 4 | gpt-5.4 | 20/25 (80%) | ❌ VERIFIED — picked one side | **Frontier Codex** |
| 4 | claude-haiku-4-5 | 20/25 (80%) | ❌ VERIFIED — picked one side | Cheapest Anthropic |
| 4 | gemini-3-flash-preview | 20/25 (80%) | ❌ VERIFIED — picked one side | Cheapest Gemini |
| 7 | gemini-3.1-pro-preview | 19/25 (76%) | ❌ VERIFIED — picked one side | Frontier Gemini |

### Self-consistency check (winner only)

`gpt-5.3-codex-spark` was re-dispatched ~5 minutes after the initial run with the
identical prompt. Result: **5/5 verdict match with run 1**. Q1 was `CONFLICTING`
in both runs, citing the same two IBM URLs verbatim. Q2-Q5 all matched substantively.
The 25/25 is not a one-shot fluke.

## Three patterns from the data

### Pattern 1 — Inverse cost-quality within Codex family

`gpt-5.3-codex-spark` (cheapest) scored 5 points higher than `gpt-5.4` (frontier)
on the same test. The frontier model's higher reasoning effort actually HURT
fact-grounding performance: it found supporting sources for its conclusion, then
synthesized a confident answer instead of searching for contradictions.

The codex-spark variant — explicitly marketed as an ultra-fast coding model —
gave terse direct answers and happened to be more honest about uncertainty.
**Frontier reasoning is not always an asset for narrow grounding tasks.**

### Pattern 2 — Inverse cost-quality within Gemini family

`gemini-3-flash-preview` (cheapest, 20/25) beat `gemini-3.1-pro-preview` (frontier, 19/25)
by 1 point. Same direction as Codex. Frontier Gemini Pro lost the extra point on
Q3 (dropped a `[*]` array index from the field path) and Q4 (added a stale historical
`--storage` flag detail that current upstream docs don't reference). Smaller
difference than Codex but the same direction.

### Pattern 3 — Flat cost-quality within Anthropic family

`claude-opus-4-6` and `claude-sonnet-4-6` both scored 23/25. **No quality premium
for Opus on this task.** Both took the epistemically conservative path on Q1
(UNVERIFIED + transparent explanation that IBM's docs returned 403 to programmatic
fetches) — same answer pattern, same citations.

The user's instinct that "Opus is overkill" for this kind of work is empirically
confirmed. Save Opus quota for tasks where its strengths matter (long reasoning,
main-session work).

## The discriminating question

Q1 was the only meaningfully discriminating question. Q2-Q5 were answered correctly
by 6 of 7 candidates, with Gemini Pro losing minor points on imprecisions.

**Only spark, Sonnet, and Opus handled Q1 honestly.** The other four (gpt-5.4,
Haiku, Flash, Gemini Pro) all picked the same wrong side ("Prometheus removed in
Kubecost 3.x") and confidently asserted it as fact — exactly the failure mode that
flapped Codex on module-1.5.

The axis that actually matters is **whether the model searches for contradicting
evidence after finding a confirming source**. spark and Anthropic models do;
gpt-5.4, Gemini Pro/Flash, and Haiku don't.

This axis does not correlate with model size, family, or cost.

## What this means for the architecture

Before this calibration, the proposed redesign was building toward "drop FACT
from the LLM reviewer entirely; build a deterministic tier-1 layer because LLMs
are unreliable on factual currency." The data corrects that conclusion.

**Corrected lesson**: LLM-as-judge for FACT is workable IF the selected model is
in the "honest about contradiction" group. Model selection IS the lever; the
deterministic tier-1 layer is still valuable as a safety net but is no longer
the primary fix.

The architecture decision shifts:

| Old plan | New plan |
|---|---|
| Drop FACT from LLM reviewer | Keep FACT but route to spark, not gpt-5.4 default |
| Build full deterministic tier-1 | Keep deterministic tier-1 as a safety net only |
| Codex generates knowledge cards | Spark generates fact ledgers (structured) |
| Gemini reviews structurally | Gemini still reviews structurally, but FACT moves out |

## Reproduction instructions

The full test prompt is preserved in
`MEMORY.md → project_fact_grounding_calibration.md`.

To re-run the test (e.g. when a new model lands):

```bash
# 1. Save the test prompt to a file
cat > /tmp/calibration-test.md <<'EOF'
[full prompt from project_fact_grounding_calibration.md]
EOF

# 2. Dispatch to candidates in parallel
codex exec --skip-git-repo-check --sandbox read-only \
  -m gpt-5.3-codex-spark "$(cat /tmp/calibration-test.md)"

python scripts/dispatch.py claude - --model claude-sonnet-4-6 \
  < /tmp/calibration-test.md

# 3. Score against the answer key in this doc.
```

The answer key is stable until upstream docs change. The next time it should
be re-validated is when:

- A new Kubecost release changes Prometheus dependency status (Q1 may flip from CONFLICTING to a clear answer)
- The OpenCost helm chart changes the customPricing schema (Q2)
- Kyverno officially removes `validationFailureAction` (Q3 deprecation becomes a removal)
- VPA changes its metrics source (unlikely, Q4 is stable)
- OpenCost rearranges its API paths (Q5)

## Decisions locked in

```python
# scripts/v1_pipeline.py MODELS dict
MODELS = {
    "write": "gemini-3.1-pro-preview",            # Drafter
    "write_targeted": "claude-sonnet-4-6",        # Surgical fixer (PR #221/222 path)
    "fact_grounding": "gpt-5.3-codex-spark",      # NEW — calibration winner
    "structural_review": "gemini-3.1-pro-preview", # Gemini reviews structure
    "fact_fallback": "claude-sonnet-4-6",         # Cross-family backup for facts
    "knowledge_card": "gpt-5.3-codex-spark",      # Aligned with fact_grounding
}
```

**Disqualified for fact-grounding role** (do not use, do not re-test without a new model release):

- `gpt-5.4` — confirmation bias, 20/25
- `gemini-3.1-pro-preview` — confidence error, 19/25
- `gemini-3-flash-preview` — confidence error, 20/25
- `claude-haiku-4-5` — confidence error, 20/25

## Honest limitations of this test

- **Single domain**. Only Kubecost / OpenCost / Kyverno was tested. The findings
  may not generalize to (a) less contested upstream sources, (b) other fast-moving
  ecosystems like AI infrastructure, (c) static topics with stable canonical sources.
  The calibration is "this model can be trusted on the proven flap zone" — that's
  enough to ship the architecture redesign, not a universal verdict.
- **5 questions**. Small sample. If the test set were 50 questions, individual
  model rankings might shift by a point or two. The TOP-vs-BOTTOM gap (spark vs
  Gemini Pro = 6 points) is robust to small-sample noise; finer rankings within
  the bottom tier are less robust.
- **Manual ground truth**. The human verifier (Claude Opus 4.6 in-session) read
  upstream docs to write the answer key. If the human was wrong on any question,
  the model rankings on that question are wrong. Spot-check against this doc
  before treating the answer key as authoritative.
- **No tool-use difference accounted for**. The candidates have different web-search
  tools (Codex uses its built-in search, Gemini uses Google search, Anthropic models
  use Anthropic's web fetch). Some of the variance may come from search-tool quality,
  not model quality. We can't disentangle these from a 7-candidate test.

## Surprising finding worth flagging

The single most counterintuitive result: **the frontier model in two of three
families was outperformed by a cheaper variant in the same family on this task.**
For Codex: spark (cheapest) > gpt-5.4 (frontier) by 5 points. For Gemini: Flash
(cheapest) > Pro (frontier) by 1 point. Anthropic was the only family where the
frontier-vs-budget delta was zero (Opus = Sonnet).

The pre-test prior — "frontier models are universally better" — was wrong for
this task. The lesson generalizes beyond fact-grounding: **for narrow tasks
with clean success criteria, calibrate against the actual task before assuming
the most expensive model is the right pick.** The 40-minute calibration test
saved us from hardcoding the wrong default.

---

*This document is the durable record of the calibration test. The session memory
file `project_fact_grounding_calibration.md` is the live operational summary.*
