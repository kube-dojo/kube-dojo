# Tier 3 reader-aid proposal — Ch45 Generative Adversarial Networks

Issue #394 / #562. Drafted by Claude. Adversarial review by Codex required before any element lands.

The hard constraint is bit-identity of the existing prose body. Every proposal here is an *inserted* callout between paragraphs; no proposal modifies an existing prose line. After application, `git diff main -- src/content/docs/ai-history/ch-45-generative-adversarial-networks.md | grep -E '^-[^-]'` must remain empty.

---

## 1. Inline parenthetical definition (Starlight tooltip)

**SKIPPED.**

**Reason:** Element 8 is globally skipped on every chapter. Starlight does not ship a tooltip component, and wrapping words inside the existing prose body in `<abbr>` tags modifies those lines, violating the bit-identity rule. The Tier 1 plain-words glossary covers the same job non-destructively. See `READER_AIDS.md` Element 8 for the canonical rationale.

---

## 2. Pull-quote (Element 9)

**SKIPPED — no candidate from Green primary sources meets the bar.**

Surveyed the following candidates from Green primary sources in `sources.md`:

**Candidate A:** The counterfeiter/police analogy from Goodfellow et al. 2014, p.1 Introduction (claim G6):

> "The generative model can be thought of as analogous to a team of counterfeiters, trying to produce fake currency and use it without detection, while the discriminative model is analogous to the police, trying to detect the counterfeit currency."

**Reason for rejection:** The chapter prose (scene "The Game on One Page," paragraph beginning "To make the mechanics of this relationship accessible...") paraphrases this analogy at length and renders it in the chapter's own discursive voice. Displaying the verbatim sentence as a pull-quote callout immediately after that paragraph would create adjacent repetition: the reader has just absorbed the same content in expanded narrative form. This is rejection ground (b) from the READER_AIDS.md rubric: "the prose paragraph already quotes the sentence verbatim" — or in this case, fully paraphrases and elaborates it so completely that a separate typographic lift adds nothing.

**Candidate B:** Goodfellow 2016 tutorial, p.17 (claim G11): "GANs introduced a new disadvantage: training requires finding a Nash equilibrium, harder than optimizing an objective function."

**Reason for rejection:** The chapter's closing paragraph of "Why This Was Different" and the entire arc of the "Instability Tax" section treat this at sufficient length that a pull-quote would paraphrase already-stated prose. The tutorial framing is also not verbatim in the sources.md; the claim-level anchor is Green but the exact sentence wording is the chapter's paraphrase, not a direct quote from the PDF. Promoting an adjacent paraphrase as a pull-quote violates the "refuse adjacent-paraphrased candidates" rule.

**Candidate C:** The acknowledgment line from Goodfellow et al. 2014, p.8 (claim G3):

> "We would also like to thank Les Trois Brasseurs for stimulating our creativity."

**Reason for rejection:** This sentence is quoted nearly verbatim in the chapter prose (scene "The Montreal Spark," final paragraph: "…they offered a note of gratitude to Les Trois Brasseurs for 'stimulating our creativity.'"). Duplicating it as a pull-quote callout directly after that paragraph produces adjacent repetition. Rejection ground (b) applies.

**Conclusion:** No Green-primary-sourced candidate survives all three rejection tests. The pull-quote is SKIPPED for Ch45.

---

## 3. Selective dense-paragraph asides (Element 10)

**PROPOSED — one aside on the minimax value function paragraph.**

### 3a. Plain reading after the minimax value function explanation

**PROPOSED.**

**Insertion anchor.** Immediately after the paragraph in scene "The Game on One Page" that begins "The paper's central equation expressed that opposition in two expected log terms..." and ends "...It could learn that measure indirectly because the discriminator was constantly refit to the current boundary between real and generated examples."

**Why it qualifies as symbolically dense.** The paragraph invokes two expected log terms and states: "One term rewarded the discriminator for assigning high probability to real data. The other rewarded it for assigning low probability to samples made by the generator. The generator's objective ran against the second term: it wanted the discriminator to treat generated samples as real." This is the mathematical heart of the minimax objective, and its three-move structure (discriminator reward on real, discriminator reward on fake, generator direction reversal) can slide past a non-specialist reader who tracks the English but loses the *direction* of the opposition. The paragraph does not display the equation in full; it renders it as a verbal description that depends on the reader holding the two log terms in mind simultaneously.

**Proposed text:**

```markdown
:::tip[Plain reading]
The discriminator is rewarded for correctly labeling real data as real and generated data as fake — both terms push its parameters in the same direction. The generator is rewarded for exactly one thing: getting the discriminator to label its outputs as real. So the generator steers toward the same boundary the discriminator is trying to maintain — but from the opposite side. Each update reshapes what the other network faces in the next round.
:::
```

**Why it does new work.** The surrounding prose says the generator's objective "ran against" the discriminator's second term. The plain-reading caption makes the *direction reversal* concrete by naming both sides of the boundary explicitly and anchoring the "each update reshapes" consequence that the prose implies but does not state as a single crisp sentence. This is not a paraphrase of the paragraph; it names the geometric picture the paragraph's vocabulary points toward.

### 3b. Plain reading on remaining paragraphs

**SKIPPED.**

The remaining mathematically adjacent paragraphs in "The Game on One Page" — the minimax game description, the training algorithm, and the global optimum proof — are narratively dense (who trains what in which order, what the equilibrium means) rather than symbolically dense in the sense that requires a plain-reading aside. The prose glosses each move in the same paragraph where it introduces it. A plain-reading caption after the training-algorithm paragraph, for example, would only restate the update order the paragraph already gives step by step. The "Why This Was Different" and instability paragraphs are similarly narrative in texture. Refusing those asides on the rubric's criterion: no genuinely symbolically dense paragraph, no aside.

---

## Summary for Codex

| # | Element | Status | Rationale to test |
|---|---|---|---|
| 8 | Inline tooltip | SKIPPED | Globally skipped; no Starlight tooltip component; HTML `<abbr>` violates bit-identity. |
| 9 | Pull-quote | SKIPPED | Candidate A (counterfeiter analogy) fully paraphrased by adjacent prose. Candidate B (Nash equilibrium framing) is a paraphrase not a verbatim Green quote. Candidate C (Les Trois Brasseurs acknowledgment) already quoted in prose. No surviving candidate. |
| 10a | Plain reading after minimax value-function paragraph | PROPOSED | Three-move opposition structure can slide past non-specialists; aside names the direction-reversal concretely without paraphrasing the paragraph. |
| 10b | Plain reading on remaining paragraphs | SKIPPED | Narratively dense, not symbolically dense; prose already glosses each move inline. |

For element 10a, please return APPROVE / REJECT (with reason) / REVISE (with suggestion). Be willing to reject. The goal is to keep only what genuinely helps a reader who has stalled at the equation structure.
