# Tier 3 Review — Chapter 52: Bidirectional Context

Reviewer: Codex (gpt-5.5)
Date: 2026-04-30
Reviewing: tier3-proposal.md by Claude (claude-opus-4-7)

## Element 8 — Inline parenthetical definition
Author verdict: SKIPPED — Tooltip component is not available; `<abbr>` would modify prose and violate bit-identity.
Reviewer verdict: APPROVE
I approve the skip. The spec makes Element 8 skipped on every chapter until a non-destructive tooltip component exists, and the Tier 1 glossary already carries the plain-language definitions without touching verified prose.

## Element 9 — Pull-quote
Author verdict: PROPOSED — BERT abstract sentence on deep bidirectional pre-training after the ELMo/GPT contrast paragraph, with an adjacent-repetition warning.
Reviewer verdict: REJECT
Reject the proposed quote. It is primary, Green-source, and quote-worthy in isolation, but it fails the Element 9 adjacent-repetition test. The intended insertion point is immediately after chapter line 99, which already says BERT's central claim was deep bidirectionality and that every layer could condition on left and right context. The proposed sentence repeats the same claim in the same order: deep bidirectional representations, unlabeled pre-training, left and right context, all layers. The proposed annotation also repeats contrast material already present at chapter lines 91, 97, 99, and 113.

I would not revive the two obvious substitutes. The BERT abstract's "fine-tuned with just one additional output layer" sentence repeats chapter lines 123 and 127, where the prose already explains minimal task-specific architecture change and the added output layer. The Google blog's "30 minutes on a single Cloud TPU" sentence repeats chapter line 137 almost verbatim. Both would create a second callout that restates an adjacent or nearby prose claim rather than adding provenance, stakes, or intellectual lineage.

## Element 10 — Plain-reading aside
Author verdict: SKIPPED — Conceptual/architectural narrative; no symbolically dense paragraph.
Reviewer verdict: APPROVE
I approve the skip. The technical passages here are enumerations and workflow explanations: MLM percentages, WordPiece/input embeddings, model sizes, TPU counts, and fine-tuning economics. They are not formula, derivation, or stacked-definition paragraphs under Element 10, and the existing prose already plain-reads the architecture.

## Summary
- Approved: Element 8 skip; Element 10 skip
- Rejected: Element 9 pull-quote
- Revised: None
- Revived: None
