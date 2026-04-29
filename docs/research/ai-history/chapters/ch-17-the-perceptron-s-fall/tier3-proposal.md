# Tier 3 Proposal — Chapter 17: The Perceptron's Fall

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default per READER_AIDS.md §Tier 3.

## Element 9 — Pull-quote (at most 1)

Ch17 is densely narrative but does incorporate paraphrased and near-quoted primary-source material throughout. The best verbatim candidate from a named primary source is Minsky and Papert's *Perceptrons* (1969).

### Candidate A — Minsky and Papert on prior structure (Perceptrons intro, ~pp.16-17)

The chapter's "Mathematical Turn" section paraphrases the core argument: "meaningful learning at meaningful rates needs prior structure." This is a paraphrase, not a verbatim quotation. The original wording in the *Perceptrons* introduction (pp.16-17) is not reproduced verbatim in the chapter prose.

**Status: PROPOSED.** The prior-structure argument is the load-bearing intellectual claim that the chapter frames as "not anti-AI but a demand for theory." If the verbatim sentence from pp.16-17 differs from the paraphrase, it may add evidentiary force without adjacent-repetition — provided the verbatim does not exactly duplicate what the chapter has. Proposed insertion: in the "Mathematical Turn" section, after the paragraph ending "It exposed a real weakness in the way perceptrons had been promoted."

Working hypothesis for verbatim (Codex to verify against MIT Press 1969 first edition, pp.16-17):

> "The problem is not that the perceptron cannot learn to compute any particular predicate, but that it can do so only with weights that are the result of laborious and specific adjustment by the trainer."

If that wording is not accurate, Codex should propose the actual sentence. Annotation should note that the demand for prior structure — framed in 1969 as a mathematical observation — became the organizing premise of every subsequent neural-network architecture.

### Candidate B — Rosenblatt 1958 framing sentence (Psychological Review p.386)

The chapter summarises Rosenblatt's opening frame — recognition, generalization, storage, memory, behavior. A verbatim opening sentence from the 1958 abstract or introduction could anchor the contrast.

**Status: SKIPPED** in favour of Candidate A. Cap is 1. The Minsky/Papert prior-structure claim serves the chapter's hinge (from technical theorem to winter) more directly than Rosenblatt's positive program. Rosenblatt's position is already given sufficient narrative weight in the prose.

## Element 10 — Plain-reading asides (0–3 per chapter)

Ch17 is predominantly narrative-historical. Three passages are candidates for symbolic density.

### Candidate C — Connectedness proof paragraph

In "The Mathematical Turn," the paragraph beginning "Minsky and Papert showed that connectedness was not conjunctively local of any fixed order. They also showed that diameter-limited perceptrons could not compute connectedness" introduces two related theorems in quick succession. A non-specialist may stumble on the distinction between "not conjunctively local of any order" and "diameter-limited cannot compute."

**Status: PROPOSED.** The paragraph stacks two formal results that use technical vocabulary (conjunctively local, diameter-limited) without pausing to say they are two facets of the same geometric obstruction. A one-to-two sentence aside would bridge the formal statement to the intuition that any fixed-window test fails as the image grows — without duplicating the surrounding prose, which addresses the visual intuition separately.

Proposed anchor: immediately after the paragraph ending "the local pieces did not scale into the global judgment."

Proposed aside text (draft for Codex review):
> Both results say the same thing from different angles: no matter how many local patches you consult, if each patch is bounded in size, a sufficiently large image can always hide a connectivity gap that all the patches agree to miss.

### Candidate D — Order/parity paragraph

In "The Mathematical Turn," the paragraph "Parity is the bridge between the famous shorthand and the larger theorem. XOR is the two-input case that later readers remember; the harder historical claim is about parity as the input grows and the required order grows with it." This is already written as a plain-reading bridge. It does no new symbolic work.

**Status: SKIPPED.** Already plain-read in prose; not symbolically dense. An aside would only repeat the surrounding text.

### Candidate E — Predicate/linear-combination definition paragraph

The chapter's "The Mathematical Turn" opening: "a perceptron computes a predicate by combining partial predicates with weights and a threshold. A partial predicate looks at some limited part or feature of the input." This is the closest the chapter comes to a formal definition stack.

**Status: SKIPPED.** The chapter immediately unpacks both terms in the surrounding prose. An aside would duplicate rather than extend.

## Summary verdict

- Element 8: SKIP.
- Element 9: 1 PROPOSED (Candidate A — Minsky/Papert prior-structure verbatim), 1 SKIPPED.
- Element 10: 1 PROPOSED (Candidate C — connectedness double-theorem aside), 2 SKIPPED.

**Total: 2 PROPOSED, 3 SKIPPED.**

## Author asks Codex to

1. Verify Candidate A's proposed verbatim wording against the MIT Press 1969 first edition of *Perceptrons*, pp.16-17. Return the actual sentence that best captures the prior-structure argument; APPROVE / REJECT / REVISE the pull-quote candidate based on whether a strong verbatim sentence exists and is not already quoted in the chapter prose.
2. Verify that the connectedness proof paragraph (Candidate C, around "not conjunctively local of any fixed order" and "diameter-limited perceptrons could not compute connectedness") would benefit from the proposed aside, or whether the adjacent paragraph ("The example is powerful because it feels visually simple...") already covers the intuition sufficiently to make the aside redundant — APPROVE / REJECT / REVISE.
3. Confirm or reject the SKIPs on B, D, and E.
