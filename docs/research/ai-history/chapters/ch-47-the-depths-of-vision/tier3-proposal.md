# Tier 3 Proposal — Chapter 47: The Depths of Vision

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default per READER_AIDS.md.

## Element 9 — Pull-quote (at most 1)

The chapter draws on the ResNet paper (Green, G1–G26) as its central primary source. Survey of candidate sentences from the Green primary sources in sources.md:

### Candidate A — ResNet paper: the identity-mapping argument

The ResNet paper (sources.md primary, Green) contains the core framing sentence: if a shallower architecture is used as a reference, the added layers in the deeper model need only learn identity mappings to match the shallower network's training error — and yet the optimizer fails to achieve this. The chapter prose renders this argument in full (paragraphs beginning "The authors framed the problem by construction" and "The argument did not require the added layers to discover..."). The paper itself does not produce a single pithy quotable sentence for this argument; its exposition is equation-dense and spread across Sections 1 and 3.1 of the PDF. The chapter's paraphrase is already more accessible than any isolated sentence would be.

**Status: SKIPPED.** No single sentence from the primary source carries the argument independently. The paper presents the identity-mapping argument formally across multiple paragraphs with equations; lifting one sentence would strip essential context. The chapter's prose already does the explanatory work. Pull-quote would either duplicate the paraphrase or excerpt an equation fragment, neither of which earns pull-quote status under READER_AIDS.md rules.

### Candidate B — ResNet paper: the residual mapping definition

The paper defines the residual mapping formally (F(x) := H(x) − x) at Section 3.1. This appears in-prose in the chapter in equation form. The chapter quotes the mathematical notation directly in the prose body.

**Status: SKIPPED.** The prose already quotes the mathematical definition verbatim. Duplicating it as a pull-quote creates adjacent repetition, which is an explicit refusal condition under READER_AIDS.md (rule b for Element 9).

### Candidate C — AlexNet paper context sentences

The AlexNet paper (G1, Green) anchors the starting point of the chapter. The chapter renders AlexNet's contribution narratively without verbatim quotation from the paper. However, AlexNet's result sentences (top-1 / top-5 error, GPU description) are data claims, not prose with intellectual weight worth pull-quoting independently.

**Status: SKIPPED.** Data rows and numerical results are not quote-worthy in the pull-quote sense; they lack the intellectual or historiographical framing that earns pull-quote status. The chapter handles these as factual anchors, which is the right treatment.

## Element 10 — Plain-reading asides (0–3 per chapter)

Survey of symbolically dense paragraphs (mathematical formulas, derivations, stacked abstract definitions — not narratively dense history or biography):

### Candidate D — Residual mapping formulation paragraph

The paragraph beginning "The Microsoft Research team reformulated the problem through residual learning..." introduces F(x) := H(x) − x and the addition F(x) + x. This involves a mathematical reformulation, but the chapter immediately follows it with a plain-English explanation of what the algebra means ("If the optimal mapping is closer to an identity function..."). The two paragraphs together constitute a pedagogical unit where the formal statement is followed by the interpretation. The chapter prose therefore already does the plain-reading job.

**Status: SKIPPED.** The surrounding prose provides the plain reading immediately. An aside would restate what the next paragraph already says.

### Candidate E — Residual block formalization paragraph

The paragraph beginning "The residual block was formalized elegantly as y = F(x, {Wi}) + x..." is the equation-dense moment. It introduces the formal notation and cites the projection shortcut variant y = F(x, {Wi}) + Ws x. However, the paragraph immediately follows with the interpretation: "This design... added neither extra parameters nor computational complexity." The structural explanation (shortcut, branch, addition) is built into the surrounding prose.

**Status: SKIPPED.** The paragraph is technically dense but the surrounding text already plain-reads the notation. An aside would duplicate the prose immediately below the equations.

### Candidate F — Bottleneck architecture paragraph

The paragraph beginning "To afford these extreme depths, the authors redesigned the residual block for networks of fifty layers and deeper..." describes the three-layer bottleneck (1×1, 3×3, 1×1). This is an architectural description rather than symbolic mathematics. The "bottleneck" metaphor is self-explanatory in the prose.

**Status: SKIPPED.** Not symbolically dense; architectural description with a self-glossing metaphor. No formulas or derivations. The comprehension gap that plain-reading asides are designed to bridge does not exist here.

## Summary verdict

- Element 8: SKIP (universal).
- Element 9: 0 PROPOSED, 3 SKIPPED (Candidates A, B, C — no candidate earns pull-quote status; either the prose already quotes or paraphrases the load-bearing content, or the source sentences are data rows without independent intellectual weight).
- Element 10: 0 PROPOSED, 3 SKIPPED (Candidates D, E, F — mathematically dense moments are immediately followed by plain-English interpretation in-prose; no comprehension gap requiring a separate aside).

**Total: 0 PROPOSED, 6 SKIPPED.**

The chapter's prose structure explains each technical concept immediately before or after introducing it formally. Tier 3 aids would add repetition, not comprehension. All three elements are skipped.
