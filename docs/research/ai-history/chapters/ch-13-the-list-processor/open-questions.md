# Open Questions: Chapter 13 - The List Processor

## Must Resolve Before `reviewing`

- Can a paginated copy of McCarthy's "History of Lisp" be extracted for Russell's `eval` anecdote, S-expression adoption, garbage-collection priority, and Project MAC/time-sharing sections?
- Can MIT AI Memo No. 8 be extracted to bridge the 1958 memo and the 1960 CACM paper?
- What is the strongest page anchor for the exact first running LISP interpreter chronology: date, machine, implementers, and what counted as the first run?
- Which primary source best supports the priority claim "garbage collection was invented for LISP" without relying only on later retrospective phrasing?
- How should the prose distinguish McCarthy's formal `eval` from Russell and Edwards programming the interpreter?
- Which secondary source should be used to explain how LISP spread from MIT into Stanford, BBN, and later symbolic-AI labs?
- How much macro history belongs here versus later Lisp-family chapters or sidebars?
- What exact forward-link should Ch20 receive: Project MAC time-sharing, PDP-6/PDP-10 Lisp, or the AI-lab workbench culture?

## Resolved Anchors

- `AIM-001`, pp. 1-3: FLPL, FORTRAN, proposed symbolic-expression language, and IBM 704 context are anchored.
- `AIM-001`, pp. 3-6: lambda notation, recursive functions, and conditionals are anchored.
- `AIM-001`, pp. 6-12: S-expressions, list notation, elementary operations, and machine representation are anchored.
- `AIM-001`, pp. 11-13: free-storage/available-space machinery is anchored.
- `LISP15`, p. 4: manual authorship, Russell/Edwards interpreter credit, Hart/Minsky/Levin compiler credit, and Levin's publication role are anchored.
- `LISP15`, pp. 8-20: S-expression definitions, atoms/lists, functions, and special forms are anchored.
- `LISP15`, pp. 38-39: `eval` manual behavior is anchored.
- `LISP15`, p. 90: read/evaluate/print console behavior is anchored.
- `LISP15`, pp. 91-94: storage allocation and garbage collection are anchored.
- `LISP15`, pp. 98-100: FEXPRs and macros are anchored.
- Ch12 contract: IPL-before-LISP boundary is anchored at the chapter-contract level.

## Drafting Warnings

- Do not write that LISP was the first list-processing language. IPL predates it in this AI-history sequence.
- Do not collapse 1958, 1960, and 1962 into one invention moment.
- Do not write that McCarthy alone implemented LISP. The manual names Russell, Edwards, Hart, Minsky, and Levin in implementation/manual roles.
- Do not draft the Russell `eval` anecdote as a fully Green scene until paginated HOPL extraction is completed.
- Do not write that GPS was LISP-based. Ch12's GPS infrastructure is IPL.
- Do not introduce LISP machines except as a forward-link to Ch22.
- Do not make S-expression adoption sound inevitable. Treat it as historical irony and support it with extracted sources.
- Do not use Paul Graham or other popular essays as technical anchors; use them only for later reception/conflict framing.

## Gap-Audit Worklist Scaffold

### Must-fix tractable

- `HOPL-LISP` paginated extraction: Russell `eval`, S-expression adoption, GC priority, Project MAC link.
- `AIM-008` extraction: 1959 implementation-system bridge.
- Steele/Gabriel HOPL II extraction: independent support for S-expression adoption and macro evolution.
- One institutional secondary source for LISP's spread through AI labs.

### Should-add

- Compare FLPL, IPL, and LISP in a short source-backed table for the prose reviewer.
- Add one source on IBM 704 memory layout if the storage scene needs more technical specificity.
- Add one source on early LISP users outside McCarthy's immediate MIT circle.
- Add a Ch22 handoff note once the Lisp-machine chapter contract exists.

### Framing observations

- LISP's historical role is strongest when framed as "enabling substrate" rather than "first list processor."
- The M-expression/S-expression story is a useful humility beat: designers do not always know which part of a system users will adopt.
- Garbage collection belongs with language history and AI history at once. It is a local memory solution with a long managed-runtime afterlife.
