# Tier 3 Review — Chapter 41: The Graphics Hack

Reviewer: Codex (gpt-5.5)
Date: 2026-04-30
Reviewing: tier3-proposal.md by Claude (sonnet)

## Tier 2 — Architecture sketch

Verdict: APPROVE
Form-lock recommendation: KEEP `flowchart LR` for Ch42/49

`flowchart LR` is the right form for this chapter because the reader needs to see a left-to-right data-flow pipeline, not a hierarchy or actor-by-actor exchange. The six nodes are the right level of abstraction: merging the shader/rasteriser stages would hide the central GPGPU trick, while splitting them further would turn the aid into a graphics-pipeline tutorial. The commentary does enough new work by naming how to read the diagram as matrix arithmetic moving through a rendering pipeline; keep LR as the default architecture-sketch form for Ch42/49, with each chapter still free to choose chapter-specific node labels.

## Element 9 — Pull-quote

Author verdict: PROPOSED [Candidate B — Oh and Jung matrix-multiplication sentence, p.1312]; SKIPPED [Candidate A — Brook API-friction sentence due adjacent repetition]
Reviewer verdict: REVISE [replace the proposed paraphrase with the exact verified source wording]

I verified the Oh/Jung PDF from `sources.md`; Claude's proposed wording is not verbatim. Use the exact p.1312 sentence instead: "Moreover, many inner-product operations can be replaced with a matrix multiplication, which is more appropriate for GPU implementation." This is Green-anchored via Oh and Jung 2004 / C09 and is quote-worthy enough to land, but the annotation must stay provenance-focused because the nearby prose already paraphrases the conceptual bridge.

## Element 10 — Plain-reading aside

Author verdict: PROPOSED [Candidate C — full-screen rectangle mechanism]
Reviewer verdict: REJECT [not symbolically dense enough; adjacent prose already explains it]

The candidate paragraph is technically dense, but it is not the kind of symbolically dense math/formula/definition stack Element 10 is reserved for. More importantly, the following prose already explains the same mapping: rectangle as launch grid, texture as numerical array, pixel value as matrix element. Adding the aside would create reader-experience repetition rather than a new plain reading.

## Summary

- Approved: Tier 2 architecture sketch
- Rejected: Element 10 plain-reading aside
- Revised: Element 9 pull-quote must use exact Oh/Jung p.1312 wording
- Revived: none
- Form-lock: KEEP
