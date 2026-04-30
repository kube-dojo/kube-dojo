# Tier 3 Proposal — Chapter 27: The Convolutional Breakthrough

Author: Claude (Sonnet 4.6). Awaiting cross-family adversarial review (Codex).

---

## Element 1 — Pull-quote

**Status: PROPOSED**

**Candidate sentence (verbatim from prose):**

> "The convolutional breakthrough was therefore not just a network. It was a discipline: constrain the learner, respect the data, measure the throughput, and embed the model in a workflow that has to operate outside a paper."

**Source:** Ch27 prose, final paragraph of "Why It Mattered" section.

**Anchor:** After the paragraph ending "…embed the model in a workflow that has to operate outside a paper." (before the paragraph beginning "It also sharpened the relationship…")

**Annotation (proposed):** This sentence names the chapter's four-part discipline — architectural constraint, data respect, throughput measurement, pipeline integration — that distinguishes industrial AI from academic demonstration. It is not paraphrase; it reframes four themes the preceding paragraphs develop separately.

**Rationale for PROPOSED:** The sentence is genuinely load-bearing — it is the chapter's thesis compressed into two sentences. It does not merely repeat the surrounding prose; it names a pattern the prose has been building toward. The surrounding paragraphs do not quote or block-display it. Adjacent-repetition risk is low.

---

## Element 2 — Plain-reading aside (math-dense paragraph)

**Status: PROPOSED**

**Target paragraph (opening of "Two Symbols, One Law" equivalent — the parameter-reduction argument in "Pixels With Structure"):**

The paragraph beginning "The distinction is important because it separates expressiveness from learnability. A large fully connected network might have enough expressive power…" through "…the number of independent choices the optimizer has to make."

**Proposed aside text:**

:::tip[Plain reading]
Expressiveness and learnability are different things. A large fully connected network can, in principle, represent any digit classifier — but it has too many free knobs for limited data to tighten. A convolutional network spends those knobs differently: instead of learning a separate detector at every pixel location, it learns one detector and reuses it everywhere. The data then does less work per parameter.
:::

**Anchor:** Immediately after the paragraph ending "…the number of independent choices the optimizer has to make."

**Rationale for PROPOSED:** The paragraph is conceptually dense — it distinguishes two properties (expressiveness, learnability), introduces the optimizer's-degrees-of-freedom framing, and connects it to weight sharing, all in one block. The aside does new work: it concretizes the abstraction as a "too many knobs" metaphor not present in the surrounding prose.

---

## Element 3 — Plain-reading aside (DSP/operational paragraph)

**Status: SKIPPED**

**Target paragraph:** The paragraph about SUN workstation training, DSP implementation, and classifications-per-second figures in "The Postal Code Laboratory."

**Reason for SKIPPED:** The paragraph is narratively dense (engineering details, hardware names, throughput numbers) but not symbolically/mathematically dense. The READER_AIDS.md rule restricts plain-reading asides to paragraphs that are "symbolically dense (mathematical formulas, derivations, abstract definitions stacked)" — not narratively dense. An aside here would only restate the engineering facts already expressed plainly in the prose.

---

## Summary Table

| Element | Type | Status | Anchor |
|---|---|---|---|
| "It was a discipline…" sentence | Pull-quote | PROPOSED | After "Why It Mattered" para 5, before "It also sharpened…" |
| Expressiveness vs. learnability | Plain-reading aside | PROPOSED | After "Pixels With Structure" para 8 |
| DSP/operational details | Plain-reading aside | SKIPPED | Not symbolically dense |
