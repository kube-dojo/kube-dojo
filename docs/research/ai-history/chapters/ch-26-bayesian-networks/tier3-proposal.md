# Tier 3 Proposal — Chapter 26: Bayesian Networks

Author: Claude Sonnet 4.6
Date: 2026-04-30
Status: PROPOSED — awaiting adversarial review (ask-codex)

---

## Element 1: Pull-quote

**Status: PROPOSED**

**Candidate sentence** (verbatim from prose):

> "Bayesian networks made uncertainty into infrastructure."

**Source**: Final paragraph of "The Bridge to Causality and Learning" section (second-to-last paragraph of the chapter body).

**Insertion anchor**: After the paragraph ending "…given the probabilities a route for computation." (the paragraph immediately before the candidate sentence's own paragraph).

**Annotation (draft)**: This sentence is the chapter's load-bearing claim restated in its most compressed form — twelve words that distinguish infrastructure (reusable structure that other things are built on) from a one-off algorithmic trick. It marks Bayesian networks as a layer, not a solution.

**Rationale for PROPOSED**: The sentence is not already quoted in-prose; it is the chapter's thesis distilled. It does new work as a pull-quote because the annotation can name the infrastructure framing explicitly, which the surrounding prose states but does not pause on.

**Reject condition**: If the adversarial reviewer finds the surrounding paragraph already functions as a de facto pull-quote through repetition, REJECT and keep only the prose.

---

## Element 2: Plain-reading aside — "The Cost Returns" section

**Status: PROPOSED**

**Target paragraph**:

> "Gregory Cooper's 1990 paper made the limit explicit. Probabilistic inference in Bayesian belief networks is NP-hard in general. Cooper's result did not make Bayesian networks useless. It made the optimism honest. Singly connected cases and restricted topologies can be efficient. General multiply connected networks can be computationally difficult. The research program therefore had to include special cases, average-case behavior, approximations, and better algorithms."

**Insertion anchor**: Immediately after this paragraph.

**Proposed aside**:

```
:::tip[Plain reading]
NP-hard means: as the network grows, the worst-case computation time grows faster than any polynomial. For Bayesian networks, this applies to general multiply connected graphs — not to the singly connected trees where Pearl's local propagation runs efficiently. In practice, AI systems work around the limit by restricting graph topology, using approximate inference (Monte Carlo sampling, variational methods), or accepting that some queries are too expensive to compute exactly.
:::
```

**Rationale for PROPOSED**: The paragraph is symbolically dense in the computational-complexity sense. "NP-hard" is a technical term that general readers will recognise as bad without knowing what it means for this specific graph structure. The aside paraphrases the implication (topology restriction, approximation) without repeating the paragraph's words. It does work the surrounding prose does not: it names the workarounds by category.

**Reject condition**: If the reviewer judges the aside merely restates what follows in the next two paragraphs ("The research program therefore had to include special cases, average-case behavior, approximations…"), REJECT — the prose already covers it.

---

## Elements 3–10: SKIPPED

The following Tier 3 element types are skipped for Ch26:

- **Additional plain-reading asides**: The remaining dense passages in "Conditional Independence as Compression" and "Pearl's Propagation Problem" are narratively dense (explaining mechanisms in plain language), not symbolically dense (stacked formulas or abstract definitions). Asides there would paraphrase prose the chapter already wrote plainly.
- **Inline parenthetical definitions (tooltips)**: Globally SKIPPED per READER_AIDS.md until a non-destructive tooltip component exists.
- **Additional pull-quotes**: At most one per chapter; one candidate is already PROPOSED above.
