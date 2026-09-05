# Chapter 2: mathematical correction evidence

Research packet for #2329 under #2289/#2272. Checked 2026-09-05 against published prose at `3904f9b4a666a5090d191fa330aee1048c8e1e41`. This is a partial research record pending independent source-fidelity review, not chapter acceptance or permission to expand beyond verified evidence. No published prose or lifecycle flags change here. PDF page numbers below are one-based; original journal markers and later-edition pagination are different locators.

## G1 — Preserve the hypothesis of Gödel's original result

Affected prose: `src/content/docs/ai-history/ch-02-the-universal-machine.md`, paragraph beginning “The proof rested on a coding device”. The preceding paragraph names omega-consistency, but this explanation replaces it with consistency for both proof directions.

Source: [Gödel 1931, partial English translation by Martin Hirzel, 27 November 2000](https://hirzels.com/martin/papers/canon00-goedel.pdf), Theorem VI and proof, original journal markers 187–189; PDF pages 14–16. The theorem assumes omega-consistency. Proof step 1 reaches inconsistency if the constructed universal sentence is provable; step 2 uses omega-consistency to exclude its negation. These are distinct obligations.

The source is a later translation with changed notation, omitted sections and no original footnotes (PDF page 1), not an original scan. Do not attribute translator commentary to Gödel. In this notation `r` is a predicate with a free variable; the closed sentence is `forall(17, r)`, not bare `r` (equations 12–13, PDF pages 15–16).

Correction boundary: explain the original theorem under omega-consistency and distinguish predicate from sentence. Do not claim plain consistency closes both branches of this particular proof.

## G2 — Identify Rosser's later strengthening separately

Source: [J. B. Rosser, “Extensions of some theorems of Gödel and Church,” JSL 1(3), September 1936, pp. 87–91](https://www.cambridge.org/core/journals/journal-of-symbolic-logic/article/abs/extensions-of-some-theorems-of-godel-and-church/0461E34DC1F219C459EE84CC2FA89068), DOI `10.2307/2269028`, publisher's article extract. The extract distinguishes changes to Gödel's proofs from a further result obtaining undecidable propositions under simple consistency, while explicitly sacrificing some generality.

Correction boundary: a later modified argument supplies a consistency-only strengthening. Do not silently substitute its hypothesis into the account of Gödel's 1931 proof. Only the primary article extract was inspected here; detailed Rosser proof claims require the full text. The site's later online-publication date is not the historical article date.

## T1 — Separate formal equivalence from the thesis

Affected prose: the glossary's Church–Turing thesis entry attributes the thesis to Turing's appendix.

Source: [Turing, “On Computable Numbers, with an Application to the Entscheidungsproblem”](https://www.cs.virginia.edu/~robins/Turing_Paper_1936.pdf), introduction p. 231/PDF page 2; appendix pp. 263–265/PDF pages 34–36. The introduction announces an equivalence proof. The appendix outlines both directions between lambda-definable sequences and machine-computable sequences; it explicitly leaves some auxiliary formula constructions unproved. It is a formal equivalence result, not a proof that a formal class exhausts every intuitive effective procedure.

Correction boundary: describe the appendix as an outline proof of equivalence. Separate the broader identification with intuitive calculation. Turing also discusses adequacy elsewhere in the paper; this correction must not imply that he made no thesis-related argument.

Source: [Church, “An Unsolvable Problem of Elementary Number Theory,” AJM 58(2), April 1936, pp. 345–363](https://ics.uci.edu/~lopes/teaching/inf212W12/readings/church.pdf), section 7, p. 356/PDF page 13. Church proposes identifying effective calculability with recursive or lambda-definable functions and discusses justification for matching a formal definition to an intuitive notion. This supports separating the definitional proposal and its justification from a theorem equating two formal systems.

## Remaining work and review boundary

- Independently recheck these exact sources and mathematical qualifications; record any translation limitations or disagreements. Existing contract Green labels do not replace this review.
- The physical-machine absence claims, modern architecture epilogue, Princeton chronology, publication/terminology anchors and inconsistent lifecycle metadata remain unresolved #2329 work. No conclusion about those claims follows from this packet.
- After the relevant research is reviewed and merged, correct the published glossary and explanation in a separate prose PR, with reader-facing references and source-fidelity/prose-quality reviews.
- A worked example can make the distinction easier to learn, but must be source-derived, checked and clearly separated from historical events. No fabricated discovery scene, dialogue or word-count padding.

Validation for this research-only packet: `git diff --check`; no executable code, generated state or published site changes. Independent-family review remains pending.
