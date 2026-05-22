# Calibration Scorer Brittleness

## Bug 1 — ContentReviewScorer 0.5-collapse (phase 1.1)

**Symptom**: `calibration/v1/reports/2026-05-21/matrix.html` shows content-review
scoring exactly 0.50 or 1.00 across all 14 models — no model scored 0.0 or any
intermediate value. This is the classic 0.5-collapse signature.

**Root cause**: Two binary gates AND-ed together:
```python
"planted_flaw_recall": len(found) == len(flaws),          # all-or-nothing
"review_precision":    not _contains_any(response, hallucination_terms),  # all-or-nothing
```
Every model hit *some* flaws AND mentioned at least one hallucination term, so
`planted_flaw_recall=True` and `review_precision=False` for virtually every
model → AND collapses to 0.5 with no spread.

**Fix** (`v1.2`): Replace both binary gates with ratio gates:
- `finding_recall`: `len(found) / len(flaws) >= PLANTED_FLAW_RECALL_THRESHOLD (0.6)`
- `hallucination_rate`: `sum(term hits) / len(terms) <= HALLUCINATION_RATE_THRESHOLD (0.25)`

Score range expands from `{0.5, 1.0}` to `{0.0, 0.5, 1.0}` — discrimination
restored. Gate names aligned with `CodeReviewScorer` (`finding_recall`,
`hallucination_rate`) to keep the schema consistent.

**Prevention**: Any new lane scorer with two or more binary keyword/substring gates
MUST use ratio gates instead. The `FINDING_RECALL_THRESHOLD` + `HALLUCINATION_RATE_THRESHOLD`
pattern is the canonical template — see `feedback_calibration_gate_brittleness.md`
(the parent memory class for this failure mode). The `CodeReviewScorer` v1.2 fix
(PR #1369) was the prior instance; `ContentReviewScorer` is the second.

---

## Bug 2 — FactCheckScorer parse fragility (phase 1.2)

**Symptom**: qwen3.6, qwen3.6-plus, grok-4.3, and dsv4-flash all score 0% on
`fact-check` despite models appearing to produce valid JSON. Suspected parse-fail,
not real failure.

**Root cause 1 — binary `verdict_class_match`**: Same antipattern as Bug 1. Required
`matched == total` (all-or-nothing), so a single wrong verdict collapses to 0.

**Root cause 2 — naive `_parse_json_response`**: Tried `json.loads(response)`
directly, then fell back to a fenced ` ```json ``` ` block. Many models (qwen3.6,
grok-4.3, dsv4-flash) prefix their JSON array with a prose sentence:
```
Based on my analysis, here are the verdicts:
[{"claim_id":"C1","verdict":"VERIFIED"}, ...]
```
Neither `json.loads` nor the fenced-block regex matches this format → returns `[]`
→ `matched=0`, `total>0` → both gates fail → score=0.

**Fix** (`v1.2`):
1. Replace `verdict_class_match` with `verdict_recall`: `matched/total >= VERDICT_RECALL_THRESHOLD (0.75)`.
2. Add a third extraction path to `_parse_json_response`: a balanced bracket scanner
   that walks the response char-by-char tracking `[`/`]` depth (nested `{}` inside
   the array are ignored), extracts the first balanced `[...]` block, and tries
   `json.loads` on it. Capped at 50 candidates to bound cost.

**Prevention**: `_parse_json_response` must be treated as an I/O boundary — LLM
outputs are not guaranteed to be bare JSON. Any scorer that parses model output
should use the three-path extraction (direct → fenced-block → bracket-scan) rather
than assuming bare JSON. Also follows from `feedback_calibration_gate_brittleness.md`:
prose-lane outputs are even more likely to wrap JSON in narrative text.
