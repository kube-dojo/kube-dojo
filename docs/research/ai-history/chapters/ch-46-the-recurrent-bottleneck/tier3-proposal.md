# Tier 3 Proposal — Chapter 46: The Recurrent Bottleneck

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default.

## Element 9 — Pull-quote (at most 1)

The chapter draws on several Green primary sources with citable sentences. Survey of candidates from sources.md Green rows, excluding sentences already quoted verbatim in prose:

### Candidate A — Vaswani et al. 2017 (P7): the parallelisation bottleneck sentence

The chapter's climactic diagnosis cites Vaswani et al.'s statement that recurrent models' "inherently sequential nature precludes parallelization within training examples." The chapter prose paraphrases this closely but does not quote the sentence verbatim. P7 HTML/PDF Introduction (p. 1) contains: "The inherently sequential nature [of recurrent models] precludes parallelization within training examples, which becomes critical at longer sequence lengths, as memory constraints limit batching across examples."

This sentence is the chapter's load-bearing claim — it names the bottleneck in the title and subtitle. The question is whether it is already so closely paraphrased in-prose that a pull-quote would create adjacent repetition.

Assessment: The chapter's paragraph at the relevant location paraphrases the constraint across several sentences rather than stating the quoted sentence directly. However, the paraphrase is so close to the source wording that readers who encounter the pull-quote immediately after the surrounding prose would experience near-duplication. The paragraph says "the computation inside a single training example is sequential along the time axis. It is impossible to calculate the final state without first calculating the intermediate states in order. This inherently sequential nature precludes parallelization within training examples." That last sentence is the Vaswani et al. sentence — it appears verbatim in the prose.

**Status: SKIPPED.** Rule 9(b) applies: the prose paragraph already quotes the sentence verbatim. A pull-quote would create adjacent repetition without doing new work.

### Candidate B — Hochreiter and Schmidhuber 1997 (P1): the LSTM motivation sentence

P1 abstract (PDF p. 0 / journal p. 1735) contains: "We propose a novel, efficient, gradient-based method called long short-term memory (LSTM). Truncating the gradient where this does not do harm, LSTM can learn to bridge minimal time lags in excess of 1000 discrete-time steps by enforcing constant error flow through constant error carousels within special units."

The chapter prose describes the LSTM's ability to bridge artificial time lags in excess of 1000 steps (quoting the 1000-step result), and explains the constant error carousel mechanism across several paragraphs. However, the verbatim phrase "enforcing constant error flow through constant error carousels within special units" is not reproduced in the chapter — the chapter uses "constant error carousel" as a term but describes rather than quotes the mechanism claim.

This sentence is technically precise, carries the chapter's load-bearing architectural claim, and locates the 1000-step result in the source with exact language. It would do new work by presenting the authors' own formulation of what the carousel does, in contrast to the surrounding prose which is the chapter author's explanation of the same idea.

**Status: PROPOSED.** Insertion anchor: immediately after the paragraph ending "It solved the long-dependency learning problem from inside recurrence rather than abandoning recurrence." (the paragraph beginning "The word 'constant' mattered"). The pull-quote would follow the paragraph that explains the carousel mechanism and introduce the authors' own precision before the prose continues to the gate discussion. Verbatim sentence:

> "LSTM can learn to bridge minimal time lags in excess of 1000 discrete-time steps by enforcing constant error flow through constant error carousels within special units."

Annotation: Hochreiter and Schmidhuber stated the carousel's purpose in operational terms — the unit was not a passive memory store but a mechanism for keeping the gradient path intact across an exact count of steps the problem required.

### Candidate C — Sutskever, Vinyals, and Le 2014 (P5): the reverse-source trick sentence

P5 (PDF p. 4, section 3.3) describes the reversal trick. The chapter prose explains this at length and attributes it to the authors, but the specific causal claim ("reversed the order of the words in all source sentences but not the target sentences") is paraphrased, not quoted.

The sentence in the paper is functional engineering prose, not a crisp formulation of a theoretical insight. The chapter's narrative already renders the trick more clearly for a general reader than the original sentence does. A pull-quote here would elevate engineering notation over the chapter's plain-reading of the same idea.

**Status: SKIPPED.** The candidate sentence is engineering procedural language, not a standalone formulation of intellectual weight. The chapter prose already renders the idea more clearly than the source sentence.

## Element 10 — Plain-reading asides (0–3 per chapter)

Survey for symbolically dense paragraphs (mathematical formulas, derivations, or stacked abstract definitions). The chapter is primarily narrative and mechanistic prose — it explains gradients in terms of chains of derivatives and products, but uses no mathematical notation, no formula blocks, and no formal derivations. Each technical concept (vanishing gradient, constant error carousel, multiplicative gate) is introduced through analogy and plain-language description.

### Candidate D — The gradient chain paragraph

The paragraph beginning "As the temporal distance between a relevant input..." describes a chain of derivatives and the multiplication-through-time structure. It uses phrases like "chain of derivatives linking one hidden state to the next" and "A useful signal does not merely travel through time; it is multiplied through time." This is the most technically dense passage in the chapter.

Assessment: The paragraph is narratively dense (explaining a technical phenomenon through plain-language analogy), not symbolically dense (no formulas, no notation, no stacked definitions). The prose itself is the plain reading — it does not assume prior familiarity with the mathematics and does not leave a comprehension gap that an aside would bridge.

**Status: SKIPPED.** Narratively dense, not symbolically dense. The paragraph already performs the plain-reading function.

### Candidate E — The constant error carousel paragraph

The paragraph beginning "The central feature of this new architecture..." explains the CEC with a fixed self-connection weight of 1.0 and the derivative remaining 1. No formula is given; the claim "the derivative of the signal passing through it was also one" is stated in plain language.

**Status: SKIPPED.** Same reason as Candidate D — the prose is already the plain-reading version of the mathematical fact. An aside would repeat what the surrounding sentences accomplish.

### Candidate F — The O(n) sequential operations paragraph

The paragraph beginning "Vaswani and his colleagues quantified this constraint structurally..." states that recurrent layers require O(n) sequential operations and self-attention requires O(1). No derivation or formula is given.

**Status: SKIPPED.** The O(n) and O(1) notation is used only as a shorthand for "proportional to sequence length" vs "constant." The surrounding sentences explain this in plain language. No comprehension gap requiring a dedicated aside.

## Summary verdict

- Element 8: SKIP (universal default).
- Element 9: 1 PROPOSED (Candidate B — Hochreiter and Schmidhuber 1997, carousel mechanism sentence), 2 SKIPPED (Candidate A — adjacent-repetition rule; Candidate C — engineering procedural language).
- Element 10: 0 PROPOSED, 3 SKIPPED (Candidates D, E, F — narratively dense, not symbolically dense).

**Total: 1 PROPOSED, 5 SKIPPED.**

## Author asks Codex to

1. Verify Candidate B's verbatim wording against P1 (Hochreiter & Schmidhuber 1997, PDF p. 0 / journal p. 1735 abstract). Does the abstract contain a sentence matching or closely approximating "LSTM can learn to bridge minimal time lags in excess of 1000 discrete-time steps by enforcing constant error flow through constant error carousels within special units"? Return the exact wording and APPROVE / REJECT / REVISE accordingly.
2. Confirm the SKIP on Candidate A (Vaswani et al. pull-quote) on adjacent-repetition grounds: the phrase "This inherently sequential nature precludes parallelization within training examples" does appear verbatim in the chapter prose. If Codex finds this phrase is NOT present verbatim in the chapter, re-evaluate Candidate A as PROPOSED.
3. Survey the chapter for any paragraph the author may have misclassified as narratively dense when it is genuinely symbolically dense (stacked formulas or abstract definitions requiring a reader unfamiliar with calculus to stop). APPROVE a plain-reading aside if found; otherwise confirm 0 PROPOSED for Element 10.
