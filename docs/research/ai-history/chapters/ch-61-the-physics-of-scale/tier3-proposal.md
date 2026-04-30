# Chapter 61 — Tier 3 reader-aid proposal

Author: Claude (claude-opus-4-7), 2026-04-30

## Element 8 — SKIPPED (Tooltip component not available)

The Tier 1 plain-words glossary already handles the chapter's specialised terms (data/pipeline/tensor parallelism, pipeline bubble, ZeRO, PTD-P, MFU) without modifying verified prose. `<abbr title="…">` would violate the bit-identity rule.

## Element 9 — Pull-quote

**PROPOSED.** Candidate sentence from the Chinchilla paper (Hoffmann et al. 2022, arXiv:2203.15556, abstract):

> We find that current large language models are significantly undertrained, a consequence of the recent focus on scaling language models whilst keeping the amount of training data constant.

**Insertion anchor:** immediately after the chapter paragraph beginning "Hoffmann and collaborators argued that many large language models were undertrained for their compute budget." (the paragraph that paraphrases this exact claim).

**Rationale:**
- This is Chinchilla's load-bearing public claim — the sentence the rest of the field lifted into the term "Chinchilla-optimal." The chapter paraphrases ("argued that many large language models were undertrained for their compute budget") but does **not** block-quote the original.
- Block-quoting preserves the paper's diagnostic phrasing — "*significantly* undertrained" — which the chapter softens. The original sentence also names the *cause* (scaling parameters while holding tokens constant), which the chapter prose explains separately but never quotes.
- No verbatim repetition; adjacent-repetition risk is low.
- Primary anchor verification: `sources.md` lists the Chinchilla PDF as Green, downloaded 2026-04-28. Codex should fetch `https://arxiv.org/pdf/2203.15556` and confirm the verbatim sentence (or supply the precise abstract phrasing if I have it slightly wrong).

**Annotation (1 sentence, doing new work):** Chinchilla turned the scaling-laws conversation from "more parameters" into "more tokens *for those* parameters" — the correction that quietly reshaped every serious training plan from 2022 onward.

**Word budget:** ~30 words quoted + ~30 words annotation = ~60 words. At the cap.

## Element 10 — SKIPPED

Ch61 is a narrative systems chapter — pipeline scheduling, communication topology, optimizer-state inventory, cluster-topology fusion, MFU economics. **No paragraph is symbolically dense.** The chapter contains zero formulas, zero derivations, zero stacked abstract definitions. The MLP-split paragraph and the ZeRO ladder paragraph are *narratively* dense systems explanations — they walk through algebraic structure in plain English — but they are not the symbolic-density target Element 10 is reserved for. A "plain reading" callout would only restate the existing natural-language explanation, which the spec explicitly forbids.

The chapter's quantitative anchors (8.3B / 512 GPUs, 1T / 3072 GPUs / 502 petaFLOP/s, 540B / 6144 TPU v4 / 46.2% MFU, 70B / 1.4T tokens) are reported numbers, not formulas the reader needs help parsing.

## Summary

| Element | Author proposal | Rationale |
|---|---|---|
| 8 | SKIP | Bit-identity rule; Tier 1 glossary covers the same job |
| 9 | PROPOSE | Chinchilla abstract sentence; chapter paraphrases but does not block-quote — Codex must fetch the arXiv PDF and confirm verbatim |
| 10 | SKIP | No symbolically dense paragraphs; chapter is narrative systems prose |

**Awaiting Codex adversarial review.** Be willing to REJECT (paraphrase too close, or no verbatim match), REVISE annotation length, or REVIVE a different sentence — strong alternative candidates include the Megatron-LM 2019 "trainable with a few communication operations" abstract sentence (chapter paraphrases the "few well-placed communication operations" idea), or the ZeRO abstract sentence on memory redundancy.
