# People: Chapter 2 — The Universal Machine

Verified protagonist bios. Bios are kept short — material that does not directly bear on the 1928-1938 window stays out. Verification colors track how confident the chapter can be in load-bearing biographical claims when drafting.

## The Hilbert Generation

### David Hilbert (1862-1943)
- **Position in 1928:** Professor of Mathematics, University of Göttingen; the most influential mathematician of his generation.
- **Role in the chapter:** Posed the *Entscheidungsproblem* via *Grundzüge der theoretischen Logik* (with Ackermann, Berlin: Springer, 1928), ch.3, and via his 1928 Bologna ICM address. The chapter treats the problem-statement as Hilbert's load-bearing contribution; his broader *Programm* (formalism vs. intuitionism) is background only.
- **Why he matters here:** The problem Church and Turing solved in 1936 is the problem Hilbert posed in 1928. The chapter cannot start without him.
- **Verification:** Yellow — biographical facts are well-documented in standard histories; specific claims about what Hilbert *thought* the *Entscheidungsproblem* required need primary archival anchor (Hilbert correspondence) before drafting.

### Wilhelm Ackermann (1896-1962)
- **Position in 1928:** Hilbert's former student, recently completed his doctoral work; co-author of the *Grundzüge*.
- **Role in the chapter:** Co-author of the 1928 textbook that gave the *Entscheidungsproblem* its canonical formulation. The chapter does not need a separate Ackermann scene; he is mentioned alongside Hilbert.
- **Why he matters here:** The book that Turing 1936 cites is *Hilbert and Ackermann*, not *Hilbert*. Ackermann did the textbook-writing labor.
- **Verification:** Yellow — same caveats as Hilbert; secondary attestation only in this contract.

### Kurt Gödel (1906-1978)
- **Position in 1930-1931:** Privatdozent at the University of Vienna, recently completed his doctoral thesis (the *completeness* theorem, 1929) — distinct from his 1931 *incompleteness* result.
- **Role in the chapter:** The 1931 *Monatshefte* paper proves Theorem (Proposition) VI: any ω-consistent recursive extension of *Principia Mathematica* contains arithmetical formulas that are neither provable nor disprovable. This demolishes Hilbert's *Vollständigkeit* and *Widerspruchsfreiheit* goals — but, the chapter must emphasize, does *not* settle the *Entscheidungsproblem* (decidability), as Turing himself notes in §11 of his 1936 paper.
- **Why he matters here:** Without Gödel 1931, the chapter has no first-act fall. With Gödel 1931, the *Entscheidungsproblem* becomes the last surviving piece of Hilbert's program for Church and Turing to demolish.
- **Verification:** **Green** for the 1931 publication facts (verified via Hirzel + Meltzer translations). Biographical detail beyond "young Austrian mathematician" (Braithwaite intro, Meltzer 1962 ed., book p.vii) is Yellow.

## The Two Who Solved It

### Alonzo Church (1903-1995)
- **Position in 1935-1936:** Assistant Professor of Mathematics, Princeton University; founder (with Curry) of the lambda calculus tradition.
- **Role in the chapter:** Presented "An Unsolvable Problem of Elementary Number Theory" to the AMS on April 19, 1935; published it in *Am. J. Math.* 58(2) in April 1936; published the *JSL* note "A Note on the Entscheidungsproblem" in March 1936. Theorem XIX in the *Am. J. Math.* paper, with corollary, establishes the unsolvability of the *Entscheidungsproblem* for any ω-consistent system "strong enough," explicitly *Principia Mathematica*. In §7 of the same paper, Church proposes identifying "effectively calculable" with recursive (or λ-definable) — what is now called Church's thesis. Reviews Turing 1936 in *JSL* 2(1) March 1937, coining the name "Turing machine" and acknowledging the machine model "has the advantage of making the identification with effectiveness... evident immediately" (p.43).
- **Why he matters here:** Church got there first. The chapter must not let Turing's later fame overshadow Church's priority. The chapter must also not let Church's priority overshadow Turing's machine-model contribution; both attributions are load-bearing.
- **Verification:** **Green** for the 1935 AMS presentation, the April 1936 publication, the §7 thesis statement, Theorem XIX p.363, and the *Principia Mathematica* corollary — all verified by Claude `pdftotext` 2026-04-28 against the UCI-hosted PDF. The 1937 *JSL* review attribution of "Turing machine" is **Yellow** until that volume is independently retrieved.

### Stephen Cole Kleene (1909-1994) [supporting role]
- **Position in 1935:** Just-completed Princeton Ph.D. under Church; published "A theory of positive integers in formal logic" in *Am. J. Math.* 57 (1935).
- **Role in the chapter:** Joint co-developer of λ-definability with Church. The 1935 *Am. J. Math.* paper provides the technical scaffolding cited in Church 1936 footnote on p.345 ("The notion of λ-definability is due jointly to the present author and S. C. Kleene") and again at p.346 footnote. Independently proved the equivalence of λ-definability and Gödel-Herbrand recursiveness around the same time.
- **Why he matters here:** The triangle of equivalences (λ-definable ↔ recursive ↔ Turing-computable) was completed in part by Kleene's earlier work, in part by Turing's appendix. The chapter should not erase Kleene from the equivalence story.
- **Verification:** Yellow — well-documented in standard sources; specific attestation in Church 1936 footnote pp.345-346 verified by Claude `pdftotext` 2026-04-28. Specific 1936 priority claims about who-proved-equivalence-when need finer page anchors before drafting.

### Alan Turing (1912-1954)
- **Position in 1935-1936:** Recently elected Fellow of King's College, Cambridge (1935, age 22, on the strength of his Central Limit Theorem dissertation). Reading Newman's foundations-of-mathematics course, which introduced him to the *Entscheidungsproblem*.
- **Role in the chapter:** Independently solved the *Entscheidungsproblem* in 1936 using a hypothetical machine model. Manuscript "On Computable Numbers, with an Application to the Entscheidungsproblem" received by LMS 28 May 1936; appendix "Added 28 August, 1936"; read 12 November 1936; published 1937 in *Proc. London Math. Soc.* (2) 42:230-265. The paper introduces (§§1-2) the a-machine; defines circle-free machines (§2); proves the unsolvability of the circle-freeness decision problem and the print-symbol generalization (§8); reduces the *Entscheidungsproblem* to that latter problem and concludes negatively (§11); introduces the universal computing machine (§6). The appendix, signed from "The Graduate College, Princeton University," proves λ-definability ↔ computability.
- **Why he matters here:** Turing is the chapter's central protagonist. The machine model was his original contribution; the equivalence proof in the appendix is what knit his work into Church's. The §6 universal computing machine is the architectural concept that — five years before any physical machine — made software a definable object.
- **Verification:** **Green** for all 1936 paper anchors (verified by Claude `pdftotext` 2026-04-28); for the 28 August 1936 appendix-from-Princeton; for the 28 May 1936 LMS receipt; for the 12 November 1936 read date. **Yellow** for biographical claims (King's Fellowship 1935, Newman course, Procter Fellowship 1937-38, Ph.D. June 1938, return summer 1938) until Hodges 1983 page anchors land.

### Max Newman (1897-1984) [supporting role]
- **Position in 1935-1936:** Cambridge mathematician; lectured the foundations-of-mathematics course Turing attended; a "father figure" mentor through Turing's Cambridge and Bletchley years.
- **Role in the chapter:** It was Newman's lectures that introduced Turing to Hilbert's *Entscheidungsproblem*. After Turing wrote "On Computable Numbers" Newman is reputed to have said the work was so original he initially could not believe it; Newman wrote to Church recommending Turing for Princeton.
- **Why he matters here:** Newman is the bridge between Hilbert/Gödel as background reading and Turing's direct attack on the *Entscheidungsproblem*. He also wrote the letter that got Turing to Princeton.
- **Verification:** Red→Yellow — biographical role is well-documented in Hodges 1983 and elsewhere, but specific claims about Newman's lectures, Newman's reaction to Turing's manuscript, and Newman's Princeton recommendation need Hodges page anchors before drafting. The chapter may decline to scene Newman if anchors do not land.

## Notes on bios

- All bios are kept narrowly to the 1928-1938 window. Later careers (Princeton-IAS for Gödel, Manchester for Newman, Bletchley for Turing, Princeton emeritus for Church, Wisconsin for Kleene) are deliberately out of scope.
- Bios mention each person's *position* in the relevant year because institutional location was load-bearing for who got cited and who got invited where.
- No invented quotes. Where a bio implies motive (e.g. "Newman recommended Turing for Princeton"), the implication must be cited from a secondary source with page anchor or marked as conjecture.
- Hilbert and Ackermann appear as background; the chapter's protagonists are Gödel, Church, and Turing. Kleene and Newman are supporting roles.
