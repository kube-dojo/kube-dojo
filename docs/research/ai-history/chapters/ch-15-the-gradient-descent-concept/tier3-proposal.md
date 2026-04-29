# Tier 3 Proposal — Chapter 15: The Gradient Descent Concept

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family). Note: Ch15 is on the Tier 2 math list — the math-on-demand sidebar already lands at Tier 2 level. Tier 3 candidates surveyed below address the *additional* pull-quote and plain-reading layers.

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default until a non-destructive tooltip component lands.

## Element 9 — Pull-quote (at most 1)

The chapter has scare-quote-fragment quotes throughout but no full-sentence verbatim pull-quote. Strongest candidates:

### Candidate A — Widrow-Hoff 1960 "method of steepest descent" sentence (`WidrowHoff60` p. 98)

The chapter (post-Tier-1 lines around the "Widrow, Hoff, and the Lunch-Pail Adaline" section) paraphrases and partially scare-quotes Widrow-Hoff's explicit steepest-descent framing. Brief.md anchors the exact phrase ("the method of searching that has proven most useful is the method of steepest descent. Vector adjustment changes are made in the direction of the gradient" — `WidrowHoff60` p. 98).

**Status: PROPOSED**, *pending Codex verbatim verification against the WESCON paper.* The full sentence captures the chapter's hinge: 1960 was the moment a learning rule was *named* a gradient method on a continuous loss surface, in print.

If verbatim correct, insertion immediately after the paragraph that introduces "What makes the 1960 WESCON paper a decisive conceptual node…" Codex picks the exact anchor.

### Candidate B — Cauchy 1847 own admission

Cauchy explicitly admits in the 1847 *Comptes Rendus* note that he is only "outlining the principles" and intends to return with a follow-up *Mémoire* that never appears. The chapter paraphrases this throughout the "Note Cauchy Never Followed Up" section.

**Status: SKIPPED** in favour of Candidate A. The Cauchy admission is structurally interesting but Candidate A serves the chapter's "1960 was the explicit-framing moment" hinge more directly. Cap is 1; A wins on thesis.

### Candidate C — Robbins-Monro 1951 problem statement

The chapter paraphrases Robbins-Monro's monotone-unknown-function root-finding problem statement throughout the "Stochastic Bridge" section. Verbatim from the paper opening would be quote-worthy.

**Status: SKIPPED** in favour of Candidate A. The paper's opening is technical-statistical rather than thesis-bearing; not the strongest pull-quote.

### Candidate D — Schmidhuber framing of Linnainmaa

The chapter paraphrases Schmidhuber's history (`Schmidhuber15` p. 91) on Linnainmaa as the first explicit reverse-mode AD. Schmidhuber's description is widely cited.

**Status: SKIPPED.** Pull-quote should come from a primary source, not a secondary historiographic anchor. Pulling Schmidhuber would be quoting *the historian* about Linnainmaa, not Linnainmaa himself; that violates the cross-family review pattern's source-fidelity preference.

## Element 10 — Plain-reading asides (1–3 per chapter)

The Tier 2 math sidebar covers the symbolically-densest content: Cauchy's two variants, Robbins-Monro step-size conditions, Widrow-Hoff LMS rule, time-constant calculation. That coverage substantially reduces the case for Tier 3 plain-reading asides on the same paragraphs.

### Candidate E — Cauchy's "two variants on same page" paragraph

The paragraph distinguishing the line-search variant (`Θ = f(x − θX, …)`) from the steepest-descent variant proper (`Θ′_θ = 0`) is symbolically dense.

**Status: SKIPPED.** The math sidebar already restates both variants at the level of clarity a Plain-reading aside would offer. An aside in addition would duplicate.

### Candidate F — Widrow-Hoff time-constant paragraph

The `1/17` per-pattern factor and `τ = n+1` time constant are explicitly stated.

**Status: SKIPPED.** The math sidebar already restates these. The chapter prose itself ("a single pattern would not instantaneously set the correct gains, but repeated presentations would drive the corresponding error downward at a predictable rate") is the plain-reading.

### Candidate G — Linnainmaa "linear cost" paragraph

The "computational costs of the forward pass… essentially equal the costs of the backward pass" claim — restated in the chapter as a key conceptual property.

**Status: SKIPPED.** The chapter paragraph already does the plain-reading work; the math sidebar covers the technical claim.

## Summary verdict

- Element 8: SKIP.
- Element 9: 1 PROPOSED (Candidate A — Widrow-Hoff steepest-descent sentence), 3 SKIPPED.
- Element 10: 0 PROPOSED, 3 SKIPPED — all because the Tier 2 math sidebar already covers the symbolically-dense ground a Plain-reading aside would re-state.

**Total: 1 PROPOSED, 6 SKIPPED.**

Author asks Codex to:
1. Verify Candidate A's verbatim wording against `WidrowHoff60` p. 98 (or the brief.md anchor; the contract has the full sentence noted). APPROVE / REJECT / REVISE with corrected text and exact insertion anchor.
2. Confirm or reject the Tier 2-overlap reasoning for SKIPs E/F/G. Is there a paragraph the math sidebar does NOT cover that warrants a Plain-reading aside?
3. Identify any paraphrased-but-not-quoted primary-source sentence I missed (the Ch10/Ch13 pattern).
