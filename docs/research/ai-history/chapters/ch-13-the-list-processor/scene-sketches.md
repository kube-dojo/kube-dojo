# Scene Sketches: Chapter 13 - The List Processor

## Scene 1: The FORTRAN Detour

- **Setting:** MIT, 1958, with McCarthy trying to make symbolic manipulation practical on existing computing machinery.
- **Beat:** The chapter opens with FLPL, not pure LISP. McCarthy starts from a FORTRAN-based list-processing route, then uses its limits to motivate a more general algebraic language.
- **Narrative Use:** Prevents origin myth. LISP is not born outside prior programming-language practice; it reacts to it.
- **Evidence Anchors:** `AIM-001`, pp. 1-3; Ch12 IPL boundary notes.
- **Pedagogical Demonstration:** Explain why numerical FORTRAN habits do not naturally fit expressions that are trees, lists, and symbols.

## Scene 2: Two Notations, One Medium

- **Setting:** The whiteboard/paper level of the 1958 memo and the later LISP 1.5 manual.
- **Beat:** M-expressions are the planned human algebra; S-expressions are the list structures underneath. The quiet reversal is that the internal notation becomes the language people actually use.
- **Narrative Use:** Shows the central irony of LISP without turning it into a joke. The system becomes powerful because code and data share a representation.
- **Evidence Anchors:** `AIM-001`, pp. 6-9; `LISP15`, pp. 8-11; `HOPL-LISP` S-expression section as Yellow for the adoption story.
- **Pedagogical Demonstration:** Use an atom/list/dotted-pair explanation drawn from the manual. Avoid modern examples unless clearly labeled as explanatory simplification.

## Scene 3: `eval` Becomes a Machine

- **Setting:** MIT's IBM 704 implementation setting, after McCarthy's formal definitions exist on paper.
- **Beat:** `eval` moves from definition to interpreter. Russell and Edwards are the named manual-credited implementers; Russell's later-famous realization that `eval` could be compiled belongs in the scene only with Yellow caution.
- **Narrative Use:** This is the chapter's realization moment. It should teach program-as-data by showing the interpreter as a bridge between expression and execution.
- **Evidence Anchors:** `LISP15`, p. 4 for interpreter credits; `LISP15`, pp. 38-39 for `eval`; `HOPL-LISP` implementation section for the anecdote, pending page anchor.
- **Pedagogical Demonstration:** Walk the reader through the idea that an expression can be read as data, evaluated by rules, and returned as a value. Keep it conceptual, not a code tutorial.

## Scene 4: The Machine Has to Forget

- **Setting:** List cells accumulating inside memory.
- **Beat:** Symbol manipulation creates temporary structure. Without automatic reclamation, the language's elegance would be buried under bookkeeping. Garbage collection is not a side feature; it is the price of making symbolic programs usable.
- **Narrative Use:** Turns a low-level memory detail into a central infrastructure scene.
- **Evidence Anchors:** `AIM-001`, pp. 11-13; `LISP15`, pp. 91-94; `HOPL-LISP` garbage-collection section for priority nuance.
- **Pedagogical Demonstration:** Describe free-storage cells being consumed by `cons`, then reclaimed when no longer reachable. Avoid unanchored claims about exact runtime cost.

## Scene 5: The Research Workbench

- **Setting:** LISP 1.5 as used by a programmer at the console.
- **Beat:** READ/EVAL/PRINT makes symbolic AI experimental. Property lists and macros make the system extensible. The manual turns an MIT system into something another researcher can learn.
- **Narrative Use:** Closes the chapter by showing why later symbolic AI work moves toward Lisp environments while preserving the Ch20 handoff to Project MAC.
- **Evidence Anchors:** `LISP15`, pp. 4, 90, 98-100; `HOPL-LISP` Project MAC/time-sharing sections as Yellow forward-link.
- **Pedagogical Demonstration:** Show the loop as a rhythm: type symbolic expression, evaluate, inspect printed result, revise representation.

## Anti-Padding Rule

If the final prose needs more length, expand only the verified mechanics: FLPL limits, S-expression structure, lambda/`cond`/recursion, `eval`, storage reclamation, and the LISP 1.5 console. Do not add invented MIT dialogue, unverified first-run drama, heroic single-inventor framing, or LISP-machine hardware material.
