# Chapter 69 — Tier 3 reader-aid proposal

Author: Claude (claude-opus-4-7), 2026-04-30
Reviewer (cross-family): Codex (gpt-5.5)
Spec: `docs/research/ai-history/READER_AIDS.md` Tier 3 (elements 8, 9, 10).

## Element 8 — Inline parenthetical definition

**SKIPPED.** Per the spec, every chapter skips this element until a non-destructive Astro `<Tooltip>` component lands. The Tier 1 *Plain-words glossary* covers Chinchilla-optimal scaling, token, Common Crawl, multi-epoch training, synthetic data, model collapse, and benchmark contamination — the load-bearing terms a non-specialist would stumble on.

## Element 9 — Pull-quote (`:::note[]` callout)

**PROPOSED (concept-only — Codex must verify verbatim).**

Two candidate sentences are in scope. The chapter's load-bearing claims trace to (a) Villalobos et al. 2024's exhaustion forecast and (b) Shumailov et al. 2024's model-collapse warning. The chapter prose paraphrases both but does not block-quote either.

### Candidate A — Villalobos et al. 2024 (preferred)

**Source:** Villalobos et al., "Will we run out of data? Limits of LLM scaling based on human-generated data," arXiv:2211.04325v2 / Epoch AI June 2024. PDF: https://arxiv.org/pdf/2211.04325 — `sources.md` cites lines 14–46 as the anchor.

**Concept the quote should carry:** the paper's headline forecast — public human text could be fully utilized between 2026 and 2032 if trends continue, paired with the explicit naming of synthetic data, transfer learning, and data efficiency as responses.

**Insertion anchor:** immediately after the chapter paragraph beginning "Epoch AI and Villalobos and collaborators put a clock on that feeling…" (the paragraph that paraphrases the 2026–2032 result-claim but does not block-quote it).

**PROPOSED-by-concept verbatim** (from `sources.md` summary; Codex must fetch the PDF and confirm the exact wording from lines 14–46 — replace with the verified verbatim sentence if this paraphrase is wrong):

> If current trends continue, language models will fully utilize this stock between 2026 and 2032, or slightly earlier if models are overtrained.

**Annotation (1 sentence, doing new work):** Note the load-bearing qualifier "if current trends continue" — the chapter's prose later explains this is a model, not a prediction; the same paper names synthetic data, transfer learning, and data efficiency as the responses that bend the curve.

**Word budget:** approximately 24 words quoted + ~32 words annotation ≈ 56 words. Within the ≤60 cap.

### Candidate B — Shumailov et al. 2024 (fallback)

**Source:** Shumailov et al., "The Curse of Recursion: Training on Generated Data Makes Models Forget," arXiv:2305.17493 / Nature 2024. PDF: https://arxiv.org/pdf/2305.17493 — `sources.md` cites lines 60–74 and 92–97.

**Concept:** model collapse defined as forgetting the true distribution when training on model-produced data, paired with the claim that genuine human-generated content remains essential.

**Insertion anchor:** immediately after the chapter paragraph beginning "Shumailov and collaborators called attention to this danger through model collapse…"

**PROPOSED-by-concept verbatim** (Codex must fetch and confirm; replace if paraphrased): a sentence from lines 92–97 articulating that genuine human-generated content remains essential to avoid collapse.

**Codex preference order:** A first; fall back to B only if A's verbatim cannot be confirmed in the cited line range.

## Element 10 — Plain-reading aside

**SKIPPED.** Ch69's prose is conceptually rich but narratively dense, not symbolically dense. The chapter has no formula derivations, no stacked abstract definitions, and no equation paragraphs. The closest candidates — the Epoch "300T quality-and-repetition-adjusted tokens" vs "4e14 indexed-web tokens" passage and the "stock vs pile" framing — are explained inline in the chapter's own voice; a *Plain reading* aside next to either would only repeat the prose. Per the spec ("Refuse on chapters where no paragraph is genuinely dense, and refuse the *individual* aside if its commentary would only repeat the surrounding prose"), no element 10 candidates land.

## Summary

| Element | Author proposal | Rationale |
|---|---|---|
| 8 | SKIP | Bit-identity rule |
| 9 | PROPOSE (concept-only — needs verbatim verification) | Villalobos 2026–2032 forecast (preferred) or Shumailov collapse-essential-human-data (fallback); chapter paraphrases both |
| 10 | SKIP | No symbolic density |

**Awaiting Codex adversarial review.** Be willing to:
- REJECT (if you judge the Villalobos paragraph paraphrases the same content too closely, creating adjacent-repetition risk; or if the verbatim sentence cannot be confirmed in the cited PDF lines).
- REVISE (annotation length or wording, or substitute Candidate B if A fails verbatim verification).
- REVIVE (a different verbatim sentence from Villalobos, Shumailov, Hoffmann, Muennighoff, Gunasekar, or White et al. — the chapter has multiple valid load-bearing sentences across its primary sources).

For Element 9: per the dispatch instructions, if the proposal is concept-only, you MUST fetch the cited primary source and either confirm the verbatim wording or supply a verified replacement.
