# Tier 3 Proposal — Chapter 41: The Graphics Hack

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default per READER_AIDS.md §Tier 3.

## Element 9 — Pull-quote (at most 1)

The chapter's primary sources contain several technically precise statements. Survey of candidates:

### Candidate A — Brook for GPUs framing of the API problem

Buck et al. 2004 (Green, C15) describes programming graphics APIs as "powerful but difficult to use for non-graphics applications" (paraphrased from Brook Section 1/PDF p.1). The chapter prose at "The Cost of the Hack" paraphrases this claim closely ("programming the GPU through existing graphics APIs was undeniably powerful, but it was incredibly hard to use for non-graphics applications"). The chapter already represents this claim verbatim-adjacent in the prose, so elevating it to a pull-quote would create adjacent repetition — the grounds READER_AIDS.md §Tier 3, Element 9 identifies as a refusal case.

**Status: SKIPPED.** Prose already quotes the claim closely; pull-quote would duplicate it.

### Candidate B — Oh and Jung's matrix-multiplication insight

Oh and Jung 2004 (Green, C09-C10) states at p.1312 that MLP layer inner products "can be replaced by matrix multiplication." The chapter's "Linear Algebra in Disguise" section paraphrases this ("the inner-product operations within the layers of a multilayer perceptron could be mathematically represented as matrix operations"), but does not quote the sentence verbatim. The Oh and Jung formulation is technically precise, historically load-bearing, and short enough to stand on its own.

**Working hypothesis** (Codex to verify verbatim against Oh and Jung 2004, p.1312, DOI: 10.1016/j.patcog.2004.01.013, open PDF at gwern.net):

> "The inner products of weight vectors and input vectors can be replaced by a matrix multiplication operation."

Proposed insertion anchor: "Linear Algebra in Disguise," after the paragraph beginning "In 2004, Kyoung-Su Oh and Keechul Jung provided a critical demonstration..." (the paragraph that introduces the MLP-to-matrix bridge). The annotation should note that this is the primary-source sentence that made the hack legible as a research claim, not merely an engineering convenience.

**Status: PROPOSED.** Source is Green (C09); sentence is verifiable at the cited page; prose paraphrases but does not quote verbatim; the sentence carries independent historiographical weight as the conceptual bridge of the chapter.

**Codex is asked to:** Confirm whether the verbatim wording matches. If the exact wording differs, return the actual sentence from p.1312 and APPROVE / REJECT / REVISE accordingly.

## Element 10 — Plain-reading asides (0–3 per chapter)

The chapter is primarily narrative, but the "Linear Algebra in Disguise" section contains one paragraph that describes the full-screen-rectangle / pixel-shader implementation in technical terms that stack multiple graphics abstractions at once.

### Candidate C — Full-screen rectangle paragraph

The paragraph beginning "To execute this matrix multiplication on an ATI Radeon 9700 Pro..." runs through: full-screen rectangle, texture encoding, pixel shader invocation, output element correspondence, and frame-buffer delivery — five interlocking concepts presented without a pause. A non-specialist reader familiar with neural networks but not with graphics pipelines faces a comprehension gap: why does rendering a rectangle produce a matrix multiplication? The paragraph is symbolically dense in the sense that it combines concrete API nouns (rectangle, texture, pixel, shader) with abstract mathematical intent (matrix entry, inner product) in a way that makes both levels hard to hold simultaneously.

**Status: PROPOSED.** Insertion anchor: after the paragraph beginning "To execute this matrix multiplication..." (the paragraph ending "A rectangle on the screen had become a launch grid..."). Proposed aside:

> :::tip[Plain reading]
> The trick is that the graphics hardware will run one pixel-shader invocation for each pixel position in the rendered output. By drawing a rectangle big enough to cover the whole screen, the researcher controls exactly how many invocations occur — one per output element of the target matrix. Each invocation reads texture values (the encoded matrix data) and writes a single output pixel (the computed matrix entry). The hardware interprets this as image rendering; the researcher reads it as a completed matrix multiplication.
> :::

The aside works only on this paragraph because the conceptual gap (rendering-as-computation) is specific to this section; the rest of the chapter is narratively dense (history, economics, constraints) without the same stacked abstraction structure.

**Codex is asked to:** APPROVE / REJECT / REVISE Candidate C. In particular: does the aside's commentary do new work relative to the surrounding prose, or does it merely restate what the chapter already explains in the following paragraph ("This is why the early GPU neural-network work can feel both ingenious and awkward...")?

## Summary verdict

- Element 8: SKIP (universal).
- Element 9: 1 PROPOSED (Candidate B — Oh and Jung matrix-multiplication sentence, p.1312), 1 SKIPPED (Candidate A — adjacent repetition).
- Element 10: 1 PROPOSED (Candidate C — full-screen rectangle mechanism), with Codex asked to confirm it does new work.

**Total: 2 PROPOSED, 2 SKIPPED.**
