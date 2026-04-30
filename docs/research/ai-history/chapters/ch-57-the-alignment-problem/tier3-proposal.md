# Chapter 57 — Tier 3 reader-aid proposal

Author: Claude (claude-opus-4-7), 2026-04-30

## Element 8 — SKIPPED (Tooltip component not available)

## Element 9 — Pull-quote

**PROPOSED.** Candidate sentence from Ouyang et al. 2022 (InstructGPT paper, Section 5.2 "Limitations"):

> Our labelers and the researchers writing the labeling instructions, however, are not representative of all of humanity, and we cannot expect their preferences to align with those of all humans.

(Actual wording per the paper section title and subject matter; Codex should verify the exact phrasing in the Ouyang §5.2 limitations text.)

**Insertion anchor:** immediately after the chapter paragraph beginning "The phrase 'alignment' can become too large too quickly..." (the paragraph that paraphrases this exact representativeness caveat — "OpenAI was trying to make language models follow user intent better on a measured distribution of prompts, according to preferences collected from labelers and shaped by researcher instructions").

**Rationale:**
- The chapter's central historiographical move is *narrowing* the alignment claim from "alignment to humanity" to "alignment to specific labellers + specific instructions + specific prompt distribution." The paper's own §5.2 limitation sentence states this *in the authors' voice*. The chapter paraphrases but does not block-quote.
- The "we cannot expect their preferences to align with those of all humans" clause is the load-bearing public admission that RLHF is not solving alignment in the broad sense. Block-quoting installs the admission in OpenAI's own words rather than as a chapter assertion.

**Annotation (1 sentence, doing new work):** Reading this caveat against the next chapter (the product shock) is essential — it is the labour-economics and value-pluralism critique that the 2026 alignment debate has not yet resolved.

**Word budget:** ~30 words quoted + ~28 words annotation = ~58 words. Within ≤60 cap.

## Element 10 — SKIPPED

Ch57 is conceptual/methodological narrative — RLHF pipeline, comparison-vs-coding-rewards, labour-pool composition, evaluation tradeoffs. No formula/derivation/stacked-symbolic-definition paragraphs in the prose body.

## Summary

| Element | Author proposal | Rationale |
|---|---|---|
| 8 | SKIP | Bit-identity rule |
| 9 | PROPOSE | Ouyang §5.2 representativeness-limitation sentence; chapter paraphrases but does not block-quote |
| 10 | SKIP | No symbolic density |

**Awaiting Codex adversarial review.** I am not 100% certain about the *exact* verbatim wording of the §5.2 sentence. Please verify against the actual paper and either confirm-with-revise or revive a different verbatim sentence. The Ch43 Russakovsky precedent applies: exact verbatim wording is required, not a paraphrase.
