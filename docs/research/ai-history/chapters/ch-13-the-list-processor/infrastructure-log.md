# Infrastructure Log: Chapter 13 - The List Processor

## What Mattered

### IBM 704 at MIT

- McCarthy's 1958 memo explicitly targets machine computation and discusses representation in the IBM 704.
- `AIM-001`, pp. 2, 9-12 anchors the IBM 704 setting and word/list representation layer.
- The chapter should show why symbolic AI needed memory layout, list cells, and reclaimable storage, not just elegant notation.
- **`car` and `cdr` derive directly from IBM 704 register opcodes (per Gemini gap audit framing #1, 2026-04-27):** `car` = *Contents of Address Register*, `cdr` = *Contents of Decrement Register*. These are not arbitrary mathematical names — they are machine artifacts. This is one of LISP's quiet "machine-derived math" signatures and contradicts the Graham-esque "LISP was Platonically discovered" framing. The IBM 704's 36-bit word with separate 15-bit address and decrement halves is what made `cons`/`car`/`cdr` natural; on a different architecture the LISP cell representation would have been different. Surface in Scene 1 prose; do not labor it.
- **IBM/FORTRAN cultural mismatch:** The 704 was designed for numerical simulation. The FORTRAN group at IBM was uninterested in symbolic manipulation. McCarthy's brief IBM-orbit experience and the FORTRAN-group disinterest are part of *why* LISP became a separate language rather than a FORTRAN extension. Scene 1 cultural foil per Gemini Should-add #1.

### FLPL and FORTRAN Boundary

- FLPL was McCarthy's FORTRAN-based list-processing route before LISP proper.
- `AIM-001`, pp. 1-3 says FLPL was developed in FORTRAN and identifies limitations that motivated a more general algebraic language.
- This is the antidote to two bad framings: LISP as unrelated to FORTRAN, and LISP as the first list-processing language.

### IPL as Prior List-Processing Infrastructure

- Ch12's LT/GPS line used IPL before LISP's MIT trajectory becomes the dominant symbolic-AI language story.
- This chapter should say LISP displaced or superseded IPL as broader AI-lab infrastructure only with careful sourcing. The safe Green claim is narrower: IPL predates LISP in the narrative and LISP's distinction is not list processing alone.
- Cross-link: Ch12 Scene 5 and infrastructure log.

### S-Expressions and M-Expressions

- S-expressions are the list structures made of atoms and pairs; M-expressions are the intended mathematical/external language.
- `AIM-001`, pp. 6-9 and `LISP15`, pp. 8-11 anchor the notation layer.
- The historical irony, per `HOPL-LISP`, is that S-expressions became the practical universal language while M-expressions did not dominate. Keep that as Yellow until page-extracted.

### `eval`, Lambda, `cond`, and Recursion

- The language bundle matters because symbolic programs can be expressed as data structures and interpreted by a function defined in the same symbolic universe.
- `AIM-001`, pp. 3-6 anchors lambda notation, recursive definitions, and conditionals; `Recursive60` gives the canonical published presentation; `LISP15`, pp. 13-20 and 38-39 anchors manualized functions and `eval`.
- `LISP15`, p. 4 anchors Russell/Edwards as interpreter implementers. The precise Russell `eval` realization story remains Yellow pending HOPL page extraction.

### Free Storage and Garbage Collection

- LISP's list cells require a storage discipline. Free-storage lists and garbage collection turn allocation/reclamation into part of the language environment.
- `AIM-001`, pp. 11-13 anchors available-space mechanics in the original memo.
- `LISP15`, pp. 91-94 anchors allocation and garbage collection in the manualized system.
- **Priority claim correction (per Gemini gap audit Yellow→Red 2026-04-27):** "LISP invented garbage collection" is now **Red** in the claim table. Reference counting was already in use (Gelernter 1960, FLPL/IBM 704) and IPL had explicit list-management. LISP's contribution is *automated mark-and-sweep over a free-storage list inside the language runtime* — a different and more defensible claim. Use this distinction in any prose. The Yellow claim "LISP automated GC earlier and more cleanly than the contemporary alternatives, making GC standard infrastructure for managed runtimes that followed" remains the safe Yellow upgrade target.

### READ / EVAL / PRINT cycle

- The manual presents a console cycle in which the system reads an expression, evaluates it, and prints the result.
- `LISP15`, p. 90 anchors the behavior.
- **Hard rule (per Gemini gap audit framing #2 2026-04-27):** Use the period-accurate phrase "READ / EVAL / PRINT cycle" in prose. Do **not** use the acronym "REPL" — it is a later coinage (early 1980s usage) and projecting it backward into the 1962 LISP 1.5 environment is anachronistic.
- The scene should emphasize interactivity: symbolic AI researchers could test expressions, functions, and representations directly.

### Property Lists, FEXPRs, and Macros

- The LISP 1.5 system includes mechanisms for associating information with symbols and extending language behavior.
- `LISP15`, pp. 38-39 and 98-100 anchors `eval` behavior, FEXPRs, and macros.
- The macro layer should be used to show extensibility, not to detour into modern macro culture.

### Time-Sharing and Project MAC

- Project MAC belongs primarily to Ch20. Ch13 can point forward to the way Lisp became more interactive in time-sharing settings.
- Current anchor is `HOPL-LISP` later sections only; page extraction pending.
- Do not turn Ch13 into a PDP-6/PDP-10 chapter.

## Infrastructure Lesson

LISP's infrastructure was not just a syntax. It was a compact stack: a representation for symbolic structures; primitive operations over that representation; recursive function definitions; a conditional expression form; an interpreter; automatic storage reclamation; console interaction; and language-extension tools. Symbolic AI became easier to build because the same list structures could be the program, the data, and the object of inspection.

## Claims to Keep Narrow

- "List processing" alone belongs partly to IPL.
- "First interpreter" needs stronger page anchors than the current section-level HOPL extraction.
- "Garbage collection invented by LISP" is plausible but should stay cautious until corroborated.
- "LISP machine" hardware is out of scope.
