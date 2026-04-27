# Sources: Chapter 13 - The List Processor

## Verification Key

- Green: claim has a primary source with verified page anchor, or a primary HTML section paired with a page-range bibliographic source and no unresolved attribution issue.
- Yellow: claim has a strong primary section anchor without page extraction, depends on retrospective memory, or needs a second source before prose.
- Red: claim should not be drafted.

Note: local shell `curl` was not useful in this sandbox, consistent with the Ch12 pass. Anchors below were verified through browser-accessible PDF/HTML text extraction and local repository inspection. Any claim without a checked page or section anchor remains Yellow or Red.

## Primary Sources

| ID | Source | Use | Verification |
|---|---|---|---|
| `AIM-001` | John McCarthy, "An Algebraic Language for the Manipulation of Symbolic Expressions," MIT Artificial Intelligence Project Memo No. 1, September 1958. PDF: https://www.softwarepreservation.org/projects/LISP/MIT/AIM-001.pdf | FLPL/FORTRAN boundary, IBM 704 target, list structures, S-expressions, M-expressions, recursive functions, `cond`, free storage, `read`, `erase`, `copy`, and `maplist`. | Green. Verified PDF anchors: p. 1 lists proposed applications and the goal of a language for symbolic expressions; pp. 1-3 describe FLPL and its FORTRAN limitations; pp. 3-6 introduce recursion, lambda notation, functions, and conditionals; pp. 6-12 define symbolic expressions, elementary operations, list notation, and representation in the IBM 704; pp. 11-13 discuss available space/free-storage machinery; pp. 14-15 list operations including `read`, `erase`, `copy`, and `maplist`. |
| `Recursive60` | John McCarthy, "Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I," *Communications of the ACM* 3(4), April 1960, pp. 184-195. Stanford HTML: https://www-formal.stanford.edu/jmc/recursive/recursive.html | Canonical published definition of S-expressions, elementary functions, `quote`, `atom`, `eq`, `car`, `cdr`, `cons`, `cond`, recursive functions, and the LISP system. | Green/Yellow. Green for section-verified claims in the Stanford HTML: the introduction names symbolic expressions and their machine computation; Section 1 defines S-expressions; Section 2 defines elementary functions and `cond`; Section 3 gives recursive function examples; later sections define universal functions and LISP implementation concepts. Yellow for exact CACM page offsets inside the article until a paginated PDF is extracted. |
| `LISP15` | John McCarthy, Paul W. Abrahams, Daniel J. Edwards, Timothy P. Hart, Michael I. Levin, *LISP 1.5 Programmer's Manual*, MIT Press, 1962. PDF: https://softwarepreservation.computerhistory.org/LISP/book/LISP%201.5%20Programmers%20Manual.pdf | Consolidated language and system reference: implementer credits, S-expressions, atoms/lists, functions, `eval`, READ/EVAL/PRINT, property lists, garbage collection, and macros. | Green. Verified PDF anchors: p. 4 says McCarthy wrote most of the manual, Levin prepared it for publication and wrote Appendix B, Hart and Minsky contributed suggestions, Russell and Edwards programmed the interpreter, and Hart/Minsky/Levin programmed the compiler; pp. 8-11 define S-expressions, atoms, lists, dot notation, and list notation; pp. 13-20 define functions and special forms; pp. 38-39 describe `eval`; p. 90 describes the LISP programmer's console with read, evaluate, and print cycle; pp. 91-94 describe storage allocation and garbage collection; pp. 98-100 describe FEXPRs and macros. |
| `HOPL-LISP` | John McCarthy, "History of Lisp," HOPL I / ACM SIGPLAN History of Programming Languages, 1978/1979; Stanford HTML: https://www-formal.stanford.edu/jmc/history/lisp/lisp.html | Retrospective on IPL, FLPL, LISP design, Russell's implementation of `eval`, S-expressions becoming the universal LISP language, garbage collection, and Project MAC/time-sharing continuation. | Yellow/Green. Green for McCarthy-authored section anchors as retrospective primary testimony; Yellow for exact page anchors because the accessible extraction used HTML sections rather than paginated HOPL pages. Do not make the Russell anecdote load-bearing Green until a paginated copy is extracted. |
| `ProgramsCS` | John McCarthy, "Programs with Common Sense," Symposium on the Mechanisation of Thought Processes, 1959. | Cross-link to Ch11 and McCarthy's commonsense reasoning program; useful only as a context source for why symbolic languages mattered. | Yellow in this chapter. Ch11 has already used this source; Ch13 did not re-extract pages. |
| `Ch12-IPL` | Chapter 12 contract sources on IPL, LT, and GPS, especially `P-868`, `P-1584`, and IPL worklist. Local path: `docs/research/ai-history/chapters/ch-12-logic-theorist-gps/sources.md`. | Boundary source proving that list processing predates LISP in the AI narrative and belongs to IPL/Newell-Shaw-Simon before McCarthy's language. | Green for Ch12-contract cross-link; primary IPL version details remain Yellow there. Use to avoid saying "first list-processing language." |
| `AIM-008` | John McCarthy, "The LISP Programming System," MIT AI Memo No. 8, March 1959. | Likely bridge between Memo No. 1 and CACM/LISP 1.5; expected to help exact implementation chronology. | Yellow. Bibliographic source identified through Lisp archive listings, but pages were not extracted in this pass. |

## Secondary Sources

| Source | Use | Verification |
|---|---|---|
| Guy L. Steele Jr. and Richard P. Gabriel, "The Evolution of Lisp," HOPL II, 1996. URL: https://www.dreamsongs.com/Files/HOPL2-Uncut.pdf | Best technical secondary history for Lisp lineage, design evolution, macros, and later dialects. | Yellow. PDF identified but not page-extracted in this pass. Use before prose review. |
| Herbert Stoyan / Software Preservation Group Lisp History pages. URL: https://www.softwarepreservation.org/projects/LISP/ | Bibliographic map for early LISP memos, manuals, and family-tree sources. | Yellow/Green split. Green for source discovery; Yellow for claims about chronology unless tied to primary pages. |
| Pamela McCorduck, *Machines Who Think* (1979 / 2004). | Narrative context for McCarthy, Minsky, MIT, and early AI-language culture. | Yellow. Physical/page access blocked here. |
| Daniel Crevier, *AI: The Tumultuous History of the Search for Artificial Intelligence* (1993). | Secondary context on LISP's spread through AI labs. | Yellow. Page anchors pending. |
| Paul Graham, Lisp essays. | Conflict/popularizer source for later overclaiming about Lisp's specialness. | Yellow. Use only as retrospective reception or overclaim contrast, not as technical anchor. |
| Computer History Museum Lisp materials. | Possible institutional secondary confirmation for LISP 1.5, IBM 704, and early implementation artifacts. | Yellow. Specific page anchors pending. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| McCarthy's 1958 memo proposes an algebraic language for symbolic expressions and names symbolic-expression manipulation as its subject. | 1 | `AIM-001`, p. 1 | `Recursive60`, introduction | Green | Safe opening claim. |
| FLPL was a FORTRAN-based list-processing language, and McCarthy found it restricted enough to motivate a more general language. | 1 | `AIM-001`, pp. 1-3 | `HOPL-LISP`, early design sections | Green | Blocks the "unrelated to FORTRAN" mistake. |
| IPL/Newell-Shaw-Simon list processing predates LISP in the AI story. | 1 | `Ch12-IPL`, sources and infrastructure log | `HOPL-LISP`, IPL discussion | Green/Yellow | Green for boundary; Yellow for exact IPL version pages. |
| The 1958 memo targets the IBM 704 and describes word-level representation of list structure. | 1, 4 | `AIM-001`, pp. 2, 9-12 | `LISP15`, storage chapters | Green | Use for machine-infrastructure setting. |
| S-expressions are built from atoms and dotted pairs, with list notation as abbreviation. | 2 | `AIM-001`, pp. 6-9; `LISP15`, pp. 8-11 | `Recursive60`, Section 1 | Green | Main teaching layer. |
| Elementary functions include `car`, `cdr`, `cons`, `atom`, `eq`, and `cond`. | 2, 3 | `AIM-001`, pp. 8-10; `Recursive60`, Section 2 | `LISP15`, pp. 13-20 | Green | Avoid modern syntax drift. |
| Lambda notation and recursive functions are central to McCarthy's presentation. | 3 | `AIM-001`, pp. 3-6; `Recursive60`, Sections 2-3 | `LISP15`, pp. 13-20 | Green | Supports the math/tool duality. |
| M-expressions were intended as external notation while S-expressions were the internal data notation. | 2 | `AIM-001`, pp. 6-9 | `HOPL-LISP`, S-expression section | Green/Yellow | Green for intended distinction in 1958; Yellow for later adoption story. |
| S-expressions became the practical universal LISP language while M-expressions did not become the dominant user-facing language. | 2 | `HOPL-LISP`, "S-expressions as the Universal LISP Language" section | Steele/Gabriel pending | Yellow | Strong but needs paginated HOPL or secondary page extraction before prose review. |
| McCarthy's 1960 paper canonicalized recursive functions of symbolic expressions in CACM. | 3 | `Recursive60`, introduction and sections | `LISP15`, preface/context | Green/Yellow | Green for text; Yellow for exact CACM page offset. |
| The LISP 1.5 manual credits Russell and Edwards with programming the interpreter. | 3 | `LISP15`, p. 4 | `HOPL-LISP`, implementation section | Green | Enough to name Russell and Edwards as implementation figures. |
| McCarthy later recalled that Russell realized `eval` could be implemented and hand-compiled it for the IBM 704. | 3 | `HOPL-LISP`, implementation section | `LISP15`, p. 4 partially confirms interpreter implementer | Yellow | Do not make the anecdote a Green centerpiece until page anchored. |
| LISP includes automatic storage reclamation / garbage collection for list cells. | 4 | `LISP15`, pp. 91-94 | `AIM-001`, pp. 11-13; `HOPL-LISP`, GC section | Green | Safe infrastructure claim. |
| LISP invented garbage collection. | 4 | `HOPL-LISP`, GC section | Steele/Gabriel pending | Yellow | Likely true in common histories, but keep priority claim cautious until second page anchor. |
| LISP 1.5 presents an interactive read/evaluate/print cycle at the programmer's console. | 5 | `LISP15`, p. 90 | `Recursive60`, LISP system sections | Green | Use READ/EVAL/PRINT as habit, not necessarily modern "REPL" terminology unless explained. |
| LISP 1.5 manualizes property lists, FEXPRs, and macros as extension machinery. | 5 | `LISP15`, pp. 38-39, 98-100 | Steele/Gabriel pending | Green/Yellow | Green for manual existence; Yellow for broad influence claims. |
| Hart, Minsky, and Levin were involved in compiler/manual work, with Levin preparing the manual for publication. | 5 | `LISP15`, p. 4 | `HOPL-LISP` context | Green | Keep authorship precise. |
| LISP made later symbolic AI practical as a whole field infrastructure. | 5 | `LISP15`, whole manual; `HOPL-LISP`, later sections | Steele/Gabriel / secondary pending | Yellow | Big interpretive claim; acceptable in thesis but needs careful prose support. |
| LISP was the first list-processing language. | 1 | None | Contradicted by Ch12/IPL | Red | Forbidden framing. |
| LISP was a single invention completed in 1958. | 1-3 | None | Contradicted by `AIM-001`, `Recursive60`, `LISP15` chronology | Red | Use staged chronology. |
| The LISP machine hardware story belongs in this chapter. | 5 | None | Ch22 owns hardware | Red | Forward-link only. |
| GPS was implemented in LISP. | 1 | None in this pass | Ch12 says GPS infrastructure was IPL | Red | Ch12 boundary: GPS was IPL-era, not a LISP-origin story. |
| McCarthy alone implemented LISP. | 3, 5 | None | `LISP15`, p. 4 credits Russell, Edwards, Hart, Minsky, Levin | Red | Keep implementation collective. |

## Conflict Notes

- **IPL versus LISP:** LISP should be framed as a successor and rival infrastructure for symbolic AI, not as the first list-processing language. IPL predates it in the LT/GPS line.
- **Mathematical definition versus running interpreter:** McCarthy's formal `eval` matters, but the first practical interpreter requires Russell/Edwards implementation evidence. Current contract keeps the famous Russell anecdote Yellow.
- **M-expressions versus S-expressions:** The 1958 design distinction is Green; the adoption irony is Yellow until HOPL page anchors or Steele/Gabriel pages are extracted.
- **Garbage-collection priority:** LISP clearly had GC by the manual and McCarthy retrospective. "Invented for LISP" should be drafted cautiously unless backed by a second source.
- **FORTRAN boundary:** LISP did not arise in isolation from numerical programming. FLPL is a critical setup.

## Page Anchor Worklist

### Done

- `AIM-001`: Done for FLPL/FORTRAN boundary, IBM 704 target, S-expression and M-expression definitions, elementary functions, list representation, free storage, and early list operations.
- `Recursive60`: Done at section level for symbolic expressions, elementary functions, recursive functions, `eval`/universal function concepts, and system framing.
- `LISP15`: Done for implementer/manual credits, S-expression definitions, functions and special forms, `eval`, console read/evaluate/print behavior, garbage collection, and macros.
- Ch12 cross-link: Done at contract level for IPL-before-LISP boundary.

### Tractable

- Extract a paginated PDF of `HOPL-LISP` and anchor Russell/`eval`, S-expression adoption, garbage-collection priority, and Project MAC/time-sharing sections by page.
- Extract `AIM-008` for the March 1959 "LISP Programming System" bridge between Memo No. 1 and CACM.
- Extract Steele/Gabriel HOPL II pages for M-expression/S-expression adoption, macro evolution, and dialect caution.
- Extract a secondary page source for LISP's spread through MIT, Stanford, BBN, and later AI laboratories.

### Archive-blocked

- McCorduck and Crevier page scans for narrative context.
- Internal MIT AI Project correspondence or listings around the first interpreter chronology.
- Exact IBM 704 console/session evidence for the earliest `eval` run.
