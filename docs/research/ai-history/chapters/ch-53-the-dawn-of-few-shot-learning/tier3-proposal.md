# Chapter 53 — Tier 3 reader-aid proposal

Author: Claude (claude-opus-4-7), 2026-04-30
Reviewer (cross-family): Codex (gpt-5.5)
Spec: `docs/research/ai-history/READER_AIDS.md` Tier 3 (elements 8, 9, 10).

## Element 8 — Inline parenthetical definition

**SKIPPED.** Per the spec, every chapter skips this element until a non-destructive Astro `<Tooltip>` component lands. The Tier 1 *Plain-words glossary* covers prompt, in-context learning, zero/one/few-shot, WebText, and staged release.

## Element 9 — Pull-quote (`:::note[]` callout)

**PROPOSED.** Candidate sentence (Brown et al. 2020, GPT-3 paper, abstract):

> Here we show that scaling up language models greatly improves task-agnostic, few-shot performance, sometimes even reaching competitiveness with prior state-of-the-art fine-tuning approaches.

**Insertion anchor:** immediately after the chapter paragraph beginning "GPT-3 moved the technical center from zero-shot transfer to in-context learning…" (the paragraph that paraphrases the result-claim but does not block-quote the abstract sentence).

**Rationale:**
- The sentence is OpenAI's own headline claim: scaling + few-shot + *sometimes* matching task-specific fine-tuning. The chapter paraphrases the architectural setup but does not block-quote the result-statement. Pairing the chapter's exposition with the paper's voice converts the result from author-summary to documented evidence.
- The "sometimes" qualifier is the load-bearing word the chapter's later "uneven capability rising with scale" claim depends on. Block-quoting it at the start of the GPT-3 section installs the qualifier in the reader's eye before the breadth-of-results paragraph.
- No verbatim repetition in the surrounding prose. Adjacent-repetition risk is low.

**Annotation (1 sentence, doing new work):** Note "sometimes" — the abstract claims competitiveness in *some* cases, not victory; the paper itself records weaker results on WebQuestions, Natural Questions, and tasks needing common-sense physics, which the chapter unpacks below.

**Word budget:** 24 words quoted + ~37 words annotation ≈ 61 words. ~1 word over the ≤60 cap. Codex should REVISE the annotation length if landing.

## Element 10 — Plain-reading aside

**SKIPPED.** Ch53's prose is conceptual/historical narrative — release-strategy chronology, training-corpus construction, in-context learning definitions — with no symbolically dense paragraphs. Plain-reading asides apply only to formula/derivation/stacked-definition density per the spec.

## Summary

| Element | Author proposal | Rationale |
|---|---|---|
| 8 | SKIP | Bit-identity rule |
| 9 | PROPOSE | GPT-3 abstract result-statement; chapter paraphrases architecture but does not block-quote the headline claim |
| 10 | SKIP | No symbolic density |

**Awaiting Codex adversarial review.** Be willing to REJECT (if you judge the chapter's "GPT-3 moved the technical center" paragraph paraphrases the same content too closely), REVISE (annotation length), or REVIVE (a different verbatim sentence — e.g., the GPT-2 paper's "language models begin to learn these tasks without any explicit supervision when trained on a new dataset of millions of webpages called WebText" claim).
