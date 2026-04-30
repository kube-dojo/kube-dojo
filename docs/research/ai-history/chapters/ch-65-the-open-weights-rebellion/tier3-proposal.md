## Element 8 — Inline parenthetical definition

**SKIPPED.** Spec excludes Element 8 from every chapter until a non-destructive Astro `<Tooltip>` component lands. The Tier 1 *Plain-words glossary* covers open weights, open source, LoRA, QLoRA, adapter, instruction tuning, and permissive license.

## Element 9 — Pull-quote (`:::note[]` callout)

**PROPOSED.** Candidate verbatim sentence from the LoRA paper abstract (Hu et al., arXiv:2106.09685). The chapter paraphrases this load-bearing claim at line 66 ("up to a 10,000x reduction in trainable parameters and a 3x reduction in GPU memory") but never block-quotes the paper's voice.

> We propose Low-Rank Adaptation, or LoRA, which freezes the pre-trained model weights and injects trainable rank decomposition matrices into each layer of the Transformer architecture, greatly reducing the number of trainable parameters for downstream tasks.

PROPOSED-by-concept — the exact wording above is reconstructed from sources.md row 4 and the public arXiv abstract; Codex MUST fetch `https://arxiv.org/pdf/2106.09685` (downloaded 2026-04-28 per sources.md) and confirm verbatim before approving. If the actual abstract sentence is different, REVIVE with the verified text.

**Insertion anchor:** immediately after the chapter paragraph beginning "LoRA had shown how to make fine-tuning less like retraining an entire giant model…" (line 66) — the paragraph that paraphrases freezing + low-rank matrices + parameter/memory reduction in author voice but does not block-quote the paper.

**Rationale:**
- Three different anchors across the chapter rest on this one paper claim: line 66 (freeze + rank decomposition), line 70 (adapter as portable behavior), line 72 ("base remains common; adapter becomes the community's contribution"). Block-quoting the paper's own framing converts the architecture-rebellion thesis from author summary to documented mechanism.
- The chapter's "rebellion was technical before it was rhetorical" closing argument (line 84) collapses without LoRA. A verbatim near line 66 installs the technical foundation in the paper's voice before the prose builds adapters → QLoRA → community fine-tunes on top of it.
- No verbatim repetition: the chapter says "freezing pretrained weights and injecting trainable low-rank matrices" but does not block-quote any sentence from the LoRA paper. Adjacent-repetition risk is low.

**Annotation (1 sentence, doing new work):** Note "into each layer of the Transformer architecture" — the rebellion's modularity depends on adapters living *inside* the frozen base, not as a wrapper around it; that placement is what makes a LoRA file a few MB rather than a few GB.

**Word budget:** ~46 words quoted + ~40 words annotation ≈ 86 words. Over the ≤60 cap. Codex MUST REVISE annotation length down to ~14 words if approving the verbatim, or REVIVE with a shorter sentence from the same paper (e.g., "LoRA can reduce the number of trainable parameters by 10,000 times and the GPU memory requirement by 3 times").

**Alternative REVIVE candidates** (Codex pick if primary fails verbatim check):
1. Llama 2 paper (arXiv:2307.09288) intro — sentence about general-public research-and-commercial release plus net-benefit framing. Anchors line 114 ("released to the general public for research and commercial use") and line 116 ("open weights became a mainstream commercial strategy").
2. Mistral 7B announcement — verbatim "Apache 2.0 license" + "without restrictions" framing. Anchors line 126 ("released under Apache 2.0 and framed as usable without restrictions"). This is a very short candidate good for the ≤60 word budget.
3. Stanford Alpaca blog — verbatim non-commercial/academic-only restriction sentence. Anchors line 88 ("academic-only and non-commercial because of upstream LLaMA and OpenAI terms").

Prefer (2) Mistral if (1) LoRA fails verbatim — it is the shortest, most quotable, and the only Apache 2.0 anchor in the chapter.

## Element 10 — Plain-reading aside

**SKIPPED.** Ch65's prose is narrative/historical: license ladders, release chronologies, governance trade-offs, ecosystem politics. There are no symbolically dense paragraphs (no formulas, no derivations, no stacked abstract definitions). The closest candidate — line 78 on QLoRA's 4-bit quantization, NF4, double quantization, paged optimizers, 780GB → 48GB — is dense with proper nouns but not symbolically dense; it is a list of named techniques the reader is meant to take on faith and pass through, exactly the case Ch63's plain-reading aside spec was designed to avoid stretching to.

## Summary

| Element | Author proposal | Rationale |
|---|---|---|
| 8 | SKIP | Bit-identity rule until `<Tooltip>` component lands |
| 9 | PROPOSE | LoRA abstract verbatim; chapter heavily paraphrases at line 66 but never block-quotes. Codex must verify exact wording. |
| 10 | SKIP | No symbolic density; chapter is narrative/license/governance prose |

**Awaiting Codex adversarial review.** Be willing to REJECT (if you judge the chapter's "LoRA had shown how to make fine-tuning less like retraining…" paragraph paraphrases the paper too closely for a verbatim to add value), REVISE (annotation length), or REVIVE (a different verbatim — Mistral 7B Apache 2.0 sentence is the strongest backup; Llama 2 commercial-release sentence is the second).
