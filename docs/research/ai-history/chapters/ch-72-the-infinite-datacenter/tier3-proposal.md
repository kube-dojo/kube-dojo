# Chapter 72 — Tier 3 reader-aid proposal

Author: Claude (claude-opus-4-7), 2026-04-30
Reviewer (cross-family): Codex (gpt-5.5)
Spec: `docs/research/ai-history/READER_AIDS.md` Tier 3 (elements 8, 9, 10).
Chapter: closing chapter of the 72-chapter book.

## Element 8 — Inline parenthetical definition

**SKIPPED.** Per the spec, every chapter skips this element until a non-destructive Astro `<Tooltip>` component lands. The Tier 1 *Plain-words glossary* covers capex, gigawatt, PUE, WUE/closed-loop cooling, JV/residual value guarantee, Project Rainier/UltraCluster, and the DOE/LBNL data-center load figures.

## Element 9 — Pull-quote (`:::note[]` callout)

**PROPOSED-by-concept (verify-or-replace requested).** Candidate sentence (OpenAI, "Announcing The Stargate Project," Jan. 21, 2025):

> As part of Stargate, OpenAI is evaluating sites and asking firms across power, land, construction, and the built data-center infrastructure landscape to contact us.

(Per `sources.md`, the OpenAI Jan. 21, 2025 announcement at https://openai.com/index/announcing-the-stargate-project/ contains, on web lines 43–44, the language soliciting firms across "power, land, construction, equipment, and the built data-center infrastructure landscape." Codex should fetch and confirm the verbatim sentence — the wording above is the proposer's reconstruction from the contract excerpt and may need verbatim correction.)

**Insertion anchor:** immediately after the chapter paragraph beginning "OpenAI's January 2025 Stargate announcement made the language shift impossible to miss…" and before the paragraph "That is not the language of a software release." That is, after the paragraph that ends "asked firms across power, land, construction, equipment, and the built data-center infrastructure landscape to contact it."

**Adjacent-repetition risk:** the chapter paragraph itself already names "power, land, construction, equipment, and the built data-center infrastructure landscape" in its closing sentence. That makes this candidate fall under the Ch01 prototype's adjacent-repetition rule — the load-bearing fragment is already in-prose. Codex should consider REJECT on adjacent-repetition grounds, exactly as on Ch01.

**Annotation (1 sentence, doing new work, ≤60 words including quote):** This is the language of a megaproject solicitation, not a software release — power, land, and construction firms are not the audience for an API launch, and OpenAI naming them as the bottleneck installs the chapter's whole thesis in a single sentence.

**Word budget:** ~28 words quoted + ~46 words annotation ≈ 74 words. **Over the 60-word cap.** Codex should REVISE the annotation length if landing, or REJECT on adjacent-repetition grounds.

**Alternative REVIVE candidate** (Codex may replace with a different verbatim sentence): the Brad Smith Microsoft essay (Jan. 3, 2025, https://blogs.microsoft.com/on-the-issues/2025/01/03/the-golden-opportunity-for-american-ai/, web line 30) describes datacenters as "built by construction firms, steel manufacturers, electricity and liquid-cooling advances, electricians, and pipefitters." The chapter prose paraphrases this almost verbatim ("massive data centers as built by construction firms, steel manufacturers, electricity and liquid-cooling advances, electricians, and pipefitters") — same adjacent-repetition risk. Both Stargate-line and Smith-line candidates are at risk of duplicating in-prose paraphrase. **Codex may judge that no Ch72 source sentence survives the adjacent-repetition test and should be SKIPPED on those grounds, like Ch01 prototype.**

## Element 10 — Plain-reading aside

**SKIPPED.** Ch72 is the book's closing chapter, and its prose is narratively dense (megaproject announcements, capex disclosures, JV financing structure, named clusters, DOE baselines, community bargain, book-arc synthesis), not *symbolically* dense (formulas, derivations, stacked abstract definitions). Per the spec, plain-reading asides apply only to symbolic density. There is no equation, derivation, or stack-of-formal-definitions paragraph in this chapter. Forcing one would create filler.

## Summary

| Element | Author proposal | Rationale |
|---|---|---|
| 8 | SKIP | Bit-identity rule (every chapter skips until tooltip component) |
| 9 | PROPOSE-by-concept (Stargate solicitation line) with REVIVE alternative (Brad Smith pipefitters line); both at adjacent-repetition risk; possibly SKIP | Both candidate verbatim sentences are already paraphrased in-prose; Codex should fetch verbatim, judge adjacent-repetition, and either approve a revised annotation, revive a different sentence, or skip |
| 10 | SKIP | No symbolic density — chapter is narrative/historical, not formula-stacked |

**Awaiting Codex adversarial review.** This is the closing chapter — the bar for landing a Tier 3 element is *higher*, not lower. Be willing to REJECT all three. A SKIP across the board is a defensible verdict and matches the spec's "refuse on chapters where no paragraph is genuinely dense, and refuse the *individual* aside if its commentary would only repeat the surrounding prose."
