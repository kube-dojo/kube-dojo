# Infrastructure Log: Chapter 12 - Logic Theorist and GPS

## What Mattered

### RAND Corporation

- RAND supplied the institutional setting for Newell and Shaw's computing work and for the non-numerical simulation problems that prepared Newell for symbolic processing.
- `CBI91`, pp. 3-8 anchors RAND organizational simulations, Newell's work with Cliff Shaw, and the early computing context before JOHNNIAC was available to him.
- `P-868`, p. 1 identifies Newell and Simon with RAND/Carnegie Tech institutional affiliations.

### Carnegie Institute of Technology

- Carnegie Tech supplied Simon's organizational/cognitive-science setting and the Pittsburgh half of the Newell-Simon collaboration.
- `P-868`, p. 1 lists Carnegie Institute of Technology with Simon; `CBI91`, pp. 2-4 explains the RAND-to-CIT personal collaboration.
- The chapter should present RAND/CIT as a two-node research infrastructure: RAND for computing/programming and CIT for organizational/cognitive theory.

### JOHNNIAC

- JOHNNIAC is the likely machine for LT realization, but this pass did not extract a primary page anchor tying exact LT execution date, IPL version, and theorem trace to JOHNNIAC.
- `CBI91`, pp. 5-6 says JOHNNIAC was not available at the earliest RAND simulation phase; this is useful for chronology but not enough for LT run claims.
- Status: Yellow until `NSS57`, `Programming-LT`, or RAND/CMU archival pages are extracted.

### IPL and List Processing

- LT and GPS required a language/infrastructure for symbolic lists, memory references, goals, and expressions rather than ordinary numerical computation.
- `P-868`, pp. 5-16 anchors the pseudo-code/interpretive-language requirement, symbols, memories, theorem/problem lists, instructions, and routines.
- `P-1584`, p. 6 says realizing GPS-like programs was a major programming task and explicitly points to information-processing languages.
- **IPL versioning fix (per Gemini gap audit 2026-04-27):** the LT JOHNNIAC implementation used the *early* IPL line — IPL-I (drafted 1956) and IPL-II (implemented on JOHNNIAC 1956-57), with IPL-III as the LT-era successor. The widely-cited `IPL-V` manual is *RAND P-1897, 1960*; using it as the implementation reference for the 1956-57 LT runtime is a technical anachronism that risks misrepresenting the extreme memory and instruction-set constraints under which LT actually ran. Sources.md `IPL-V` entry now flags this distinction; `IPL-I/II/III` is added as a separate Yellow primary-source row.
- `Programming-LT` remains the tractable follow-up for the implementation-specific story.

### *Principia Mathematica*

- LT's domain was the sentential calculus as presented by Whitehead and Russell.
- `P-868`, p. 8 cites Whitehead and Russell's *Principia Mathematica*, Vol. 1, second edition, and explains that LT uses their proposition numbering while dropping the asterisk.
- Exact performance claims over Chapter 2 remain Yellow pending `NSS57`.

### Typewriter-Driven First Proof of Theorem 2.01

- This is likely the most vivid hand-simulation scene, but it is not Green yet.
- `P-868`, p. 3 supports the broader fact that LT could be hand simulated, barely.
- The specific Theorem 2.01/typewriter scene requires `Simon-Models` or another primary page anchor before prose drafting.

### RAND-Carnegie Correspondence as Infrastructure (per Gemini gap audit 2026-04-27)

- The two-node Newell-at-RAND / Simon-at-CIT collaboration was sustained by a steady flow of letters, memos, and technical drafts between Santa Monica and Pittsburgh.
- This "paper trail" infrastructure is as load-bearing as the JOHNNIAC memory map: without the regular correspondence, neither the hand-trace specification nor the move from chess-machine reasoning to LT to GPS happens at the speed it did.
- `CBI91` retrospectively confirms the bicoastal pattern but the correspondence itself sits in the RAND/CMU archives — Yellow worklist for any session with archival access.

## Infrastructure Lesson

The infrastructure is not just the computer. It is the whole chain: a symbolic task domain; a paper-traceable specification; a pseudo-code/list-processing language (and the *correct* IPL version for the date); a machine with enough memory and speed; and a research program willing to treat program traces as evidence about human problem solving — all sustained by the cross-coast correspondence that kept Newell and Simon working as one team.

## Claims to Keep Narrow

- "Running program" requires a run anchor; `P-868` alone is a specification anchor.
- "General problem solver" means general architecture over supplied task environments, not autonomous broad intelligence.
- "List processing" can be introduced from `P-868`/`P-1584`, but IPL technical details need `IPL-V` or `Programming-LT`.
