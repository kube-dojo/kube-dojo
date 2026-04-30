# Chapter 66 — Tier 3 reader-aid proposal

Author: Claude (claude-opus-4-7), 2026-04-30
Reviewer (cross-family): Codex (gpt-5.5)
Spec: `docs/research/ai-history/READER_AIDS.md` Tier 3 (elements 8, 9, 10).

## Element 8 — Inline parenthetical definition

**SKIPPED.** Per the spec, every chapter skips this element until a non-destructive Astro `<Tooltip>` component lands. The Tier 1 *Plain-words glossary* covers MMLU, BIG-bench, HELM, MT-Bench / Chatbot Arena, LLM-as-judge, contamination/leakage, and Goodhart's law.

## Element 9 — Pull-quote (`:::note[]` callout)

**PROPOSED-BY-CONCEPT (Codex must verify verbatim before approval).** Two candidate sentences in priority order. Codex should fetch the source PDF and either confirm verbatim or supply a verified replacement.

### Candidate A (primary) — BIG-bench on benchmark mortality

**Conceptual claim to quote:** BIG-bench's explicit institutional warning that benchmarks have *restricted scope and short useful lifespans*. This is the load-bearing argument the chapter's "Goodhart cycle" and "every successful metric creates the conditions for its own erosion" sections rest on, and the source is a community-authored benchmark paper warning *about its own cohort*. That self-referential humility is the rare quote-worthy register in benchmark-paper prose.

**Source:** Beyond the Imitation Game collaborators, "Beyond the Imitation Game: Quantifying and extrapolating the capabilities of language models," arXiv:2206.04615, Section 1.2.

**Insertion anchor:** Immediately after the chapter paragraph beginning *"BIG-bench also made a quieter point about benchmark mortality. The authors discussed the restricted scope and short useful lifespans of benchmarks…"* — the chapter paraphrases the claim but does not block-quote the paper's own sentence.

**Annotation (1 sentence, doing new work):** Coming from a 450-author collective publishing a 204-task benchmark, this is *self-indictment* — the warning that their own scoreboard would saturate is built into the paper that delivered the scoreboard, and that institutional reflexivity is what the chapter's Goodhart-cycle section borrows.

**Codex verification request:** Please curl https://arxiv.org/pdf/2206.04615 (or the local PDF if cached at `docs/research/ai-history/sources/big-bench-2206.04615.pdf`) and locate Section 1.2 ("Beyond the imitation game" or equivalent intro). Confirm a verbatim sentence about *restricted scope* and/or *short useful lifespans* of benchmarks, or supply the closest verbatim equivalent. The chapter sources.md (Conflict-Notes-eligible) cites this exact framing as **Green** with the note: "Section 1.2 discusses restricted benchmark scope and short useful lifespans."

### Candidate B (fallback) — Goodhart's law restated

**Conceptual claim to quote:** Manheim & Garrabrant's restatement of Goodhart-like overoptimization — "when a measure becomes a target, it ceases to be a good measure" or the paper's variant-defining sentence. The chapter paraphrases this aphorism and the four-variant taxonomy without block-quoting either.

**Source:** David Manheim and Scott Garrabrant, "Categorizing Variants of Goodhart's Law," arXiv:1803.04585, abstract.

**Insertion anchor:** Immediately after the chapter paragraph beginning *"Goodhart's law is often summarized as: when a measure becomes a target, it ceases to be a good measure. David Manheim and Scott Garrabrant categorized variants of this failure…"*

**Risk:** The chapter already paraphrases Goodhart's restatement *in the same paragraph*. Adjacent-repetition risk is meaningful — Ch01 prototype skipped its pull-quote on this exact ground. **Probably REJECT** under the spec's "(b) the prose paragraph already quotes the sentence verbatim" clause unless Codex finds a *different* verbatim sentence in the abstract that does new work.

## Element 10 — Plain-reading aside

**SKIPPED.** Ch66 is narrative/historical institutional history — MMLU release framing, BIG-bench community formation, HELM multi-metric argument, GPT-4 release-table politics, Chatbot Arena social dynamics, contamination disclosure, Goodhart cycle, SWE-bench design. There are no symbolically dense paragraphs (no formulas, derivations, stacked abstract definitions). Plain-reading asides apply only to symbolic density per the spec; refusing them on narrative-dense paragraphs is the correct calibration.

## Summary

| Element | Author proposal | Rationale |
|---|---|---|
| 8 | SKIP | Bit-identity rule (universal until `<Tooltip>` component) |
| 9 | PROPOSE-BY-CONCEPT (Candidate A primary; Candidate B fallback) | BIG-bench self-referential mortality warning; chapter paraphrases without block-quoting |
| 10 | SKIP | No symbolic density — Ch66 is narrative/historical |

**Awaiting Codex adversarial review.** Codex must:

1. Fetch arXiv:2206.04615 and verify a verbatim Candidate A sentence — APPROVE / REVISE (different verbatim) / REVIVE (Candidate B if Candidate A is unverifiable) / REJECT (if no genuine quote-worthy candidate exists in either source).
2. Confirm Element 8 SKIP and Element 10 SKIP on the same grounds the proposal cites.
3. Be willing to reject Candidate B outright on adjacent-repetition grounds if it is the only available fallback.
