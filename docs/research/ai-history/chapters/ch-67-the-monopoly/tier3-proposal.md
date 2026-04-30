# Chapter 67 — Tier 3 reader-aid proposal

Author: Claude (claude-opus-4-7), 2026-04-30
Reviewer (cross-family): Codex (gpt-5.5)
Spec: `docs/research/ai-history/READER_AIDS.md` Tier 3 (elements 8, 9, 10).

## Element 8 — Inline parenthetical definition

**SKIPPED.** Per the spec, every chapter skips this element until a non-destructive Astro `<Tooltip>` component lands. The Tier 1 *Plain-words glossary* covers stack concentration, 6(b) inquiry, exclusive cloud provider, AWS Trainium, stateless API, and vertical control / horizontal rivalry.

## Element 9 — Pull-quote (`:::note[]` callout)

**PROPOSED-by-concept.** I cannot supply a verified verbatim string from the contract sources (`brief.md`, `people.md`, `timeline.md`, `sources.md`) — the contract paraphrases primary-source language but does not transcribe block-quotable sentences. The strongest quote-worthy targets I can identify by concept are:

### Candidate A (preferred): July 2024 joint US/EU/UK competition statement, on key inputs

**Concept:** A sentence from the joint statement (FTC/DOJ/EC/CMA, "Joint Statement on Competition in Generative AI Foundation Models and AI Products," July 23, 2024) describing concentrated control of chips, compute, data, and technical expertise as critical ingredients that could create bottlenecks. Sources.md cites lines 40-46 of the joint statement PDF.

**Insertion anchor:** Immediately after the chapter paragraph beginning "The joint US/EU/UK competition statement in July 2024 gave the concern a broader vocabulary…" (paragraph at chapter line ~128, before "That language was careful").

**Rationale:**
- The joint statement is the chapter's "regulators name the pattern" anchor. Pairing the chapter's exposition with the statement's voice converts the regulator-risk frame from author-summary to documented evidence.
- The chapter paraphrases but does not block-quote any sentence from the joint statement. Adjacent-repetition risk is therefore low.
- A regulator's verbatim wording on key-input concentration is harder to dismiss than the chapter's gloss.

**Annotation (1 sentence, doing new work):** Note the careful "could" — the joint statement names risks and incentives, not findings, and that hedging is precisely why "concentration" rather than "monopoly" is the operative word in this chapter.

**ACTION FOR CODEX:** Please fetch the FTC PDF (`https://www.ftc.gov/system/files/ftc_gov/pdf/ai-joint-statement.pdf`) and either (a) confirm a verbatim quote-worthy sentence from the lines 40-46 region on key-input concentration, or (b) supply a different verbatim sentence from the joint statement that names the chapter's load-bearing claim. If neither is available, REJECT.

### Candidate B (fallback): OpenAI April 27, 2026 amendment

**Concept:** A sentence from the OpenAI April 27, 2026 announcement ("The next phase of the Microsoft OpenAI partnership," `https://openai.com/index/next-phase-of-microsoft-partnership/`) describing the new amendment's terms. Sources.md cites lines 31-39.

**Insertion anchor:** Immediately after the chapter paragraph beginning "Then, on April 27, 2026, OpenAI announced another amendment…" (paragraph at chapter line ~82, before "The lesson is not that exclusivity vanished").

**Rationale:**
- This is the chapter's freshness guardrail — the most recent partnership state and the place a stale paraphrase would most embarrass the chapter. Block-quoting a primary-source sentence dates the claim and forces the reader to read OpenAI's own framing rather than the chapter's gloss.
- The chapter paraphrases the amendment in detail but does not block-quote.

**Annotation (1 sentence, doing new work):** "Primary cloud partner" is not "exclusive cloud provider"; the chapter's earlier point about exclusivity becoming granular rests on this exact phrase shift, which is why the verbatim sentence carries the date discipline the chapter argues for.

**ACTION FOR CODEX:** Please fetch the OpenAI page and verify a quote-worthy verbatim sentence from the lines 31-39 region. If both Candidate A and Candidate B can be verified, prefer Candidate A (regulator voice carries more institutional weight than company self-description).

## Element 10 — Plain-reading aside

**SKIPPED.** Ch67's prose is narrative/historical: stack concentration as institutional pattern, partnership chronologies, regulator-risk framing, dated exclusivity-language evolution. There are no symbolically dense paragraphs (no formulas, derivations, or stacked abstract definitions). NVIDIA's revenue numbers are concrete financial figures, not symbolic density. Plain-reading asides apply only to formula/derivation/stacked-definition density per the spec.

## Summary

| Element | Author proposal | Rationale |
|---|---|---|
| 8 | SKIP | Bit-identity rule (spec-mandated until `<Tooltip>` lands) |
| 9 | PROPOSED-by-concept | Two candidates (July 2024 joint statement preferred, OpenAI Apr 2026 fallback). Codex must fetch and verify verbatim. |
| 10 | SKIP | Narrative density, not symbolic density |

**Awaiting Codex adversarial review.** Be willing to REJECT (if the chapter's existing paraphrase already captures what a verbatim quote would add), REVISE (annotation length or candidate sentence), or REVIVE (a different verbatim sentence from a different primary source — e.g., NVIDIA 10-K language about data-center demand, or the OpenAI 2019 announcement's "exclusive cloud provider" framing).
