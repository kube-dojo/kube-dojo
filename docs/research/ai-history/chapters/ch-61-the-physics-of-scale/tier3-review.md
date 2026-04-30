# Chapter 61 — Tier 3 reader-aid review (Codex)

Reviewer: gpt-5.5, 2026-04-30
Reviewing: tier3-proposal.md by Claude (claude-opus-4-7)

## Element 8 — Inline parenthetical definition

Author verdict: SKIPPED — Tooltip component is not available; `<abbr>` would modify prose and violate bit-identity.

**Reviewer verdict: APPROVE skip.** The spec says tooltip-style inline definitions are skipped on every chapter until a non-destructive component exists. Tier 1 glossary is the right place for these terms.

## Element 9 — Pull-quote

Author verdict: PROPOSED — Chinchilla abstract sentence after the paragraph beginning "Hoffmann and collaborators argued that many large language models were undertrained for their compute budget."

**Reviewer verdict: REVISE.** I fetched the primary source and confirmed the proposed sentence is verbatim in the arXiv abstract metadata and PDF p.1, aside from PDF line-wrap hyphenation of "undertrained." Source: https://arxiv.org/abs/2203.15556 and https://arxiv.org/pdf/2203.15556

The quote is acceptable, but revise the annotation. "Every serious training plan" overclaims beyond the Ch61 contract. Use:

> Chinchilla shifted the scale question from parameter count alone to compute allocation: how many parameters, how many tokens, and under what fixed training budget.

This stays within the word cap and does new work without claiming field-wide adoption.

## Element 10 — Plain-reading aside

Author verdict: SKIPPED — No symbolically dense paragraphs; chapter is narrative systems prose.

**Reviewer verdict: APPROVE skip.** I checked the chapter prose. The MLP split, ZeRO ladder, PTD-P, and MFU passages are narratively/systems dense, not symbolically dense. There are no formulas, derivations, or stacked abstract definitions that justify a `:::tip[Plain reading]` aside under the spec.

## Summary

- Approved: Element 8 skip; Element 10 skip
- Rejected: None
- Revised: Element 9 pull-quote annotation (verbatim quote confirmed via arXiv 2203.15556; new annotation supplied)
- Revived: None

**Tier 3 yield: 1 of 3 candidates land** (Element 9, with revised annotation).
