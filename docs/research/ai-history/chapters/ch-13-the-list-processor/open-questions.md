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
- Do not write that LISP was the first AI language. IPL has prior claim. **Demoted to Red 2026-04-27** per Gemini gap audit. Frame LISP as *successor / universal infrastructure*.
- Do not collapse 1958, 1960, and 1962 into one invention moment.
- Do not write that McCarthy alone implemented LISP — the manual names Russell, Edwards, Hart, Minsky, and Levin. **Strengthened 2026-04-27** to also block "McCarthy as sole *designer*" — Minsky's compiler suggestions and the implementers' contributions were integrated into LISP 1.5 design, not just code.
- Do not draft the Russell `eval` anecdote as a fully Green scene until paginated HOPL extraction is completed.
- Do not write "LISP invented garbage collection" without qualification. **Demoted to Red 2026-04-27.** Reference counting (Gelernter 1960 FLPL) and IPL list management are prior art. The defensible claim is "LISP automated GC via mark-and-sweep" (Yellow upgrade target).
- Do not write that LISP 1.5 was a purely functional language. **Per Gemini gap audit must-fix #2:** `prog`, `setq`, and property-list mutation are part of the manual. Naming these prevents retrospective "LISP as pure functional" projection.
- Do not use the acronym "REPL" in prose. **Per Gemini gap audit framing #2:** use "READ / EVAL / PRINT cycle" — REPL is later (1980s) usage and is anachronistic for LISP 1.5.
- Do not present LISP as Platonically *discovered*. **Per Gemini gap audit framing #1:** `car`/`cdr` are IBM 704 register-opcode names; LISP is machine-derived math, not pure abstraction.
- Do not write that GPS was LISP-based. Ch12's GPS infrastructure is IPL.
- Do not introduce LISP machines except as a forward-link to Ch22.
- Do not make S-expression adoption sound inevitable. Treat it as historical irony and support it with extracted sources.
- Do not use Paul Graham or other popular essays as technical anchors; use them only for later reception/conflict framing.

## Gap-Audit Worklist (per Gemini 2026-04-27)

### Must-fix tractable

- `HOPL-LISP` paginated extraction: Russell `eval`, S-expression adoption, GC priority, Project MAC link.
- `AIM-008` extraction: 1959 implementation-system bridge.
- `AIM-040` (LISP I Programmer's Manual, 1962) — pre-1.5 manual bridge.
- `AIM-099` (1966) — McCarthy's mid-1960s formalization work.
- `Bobrow-BBN-Lisp` early papers — Interlisp branch evidence; supports the Maclisp/BBN-Lisp bifurcation framing.
- `Baker78-GC` — settles the GC priority question by separating LISP's mark-and-sweep automation from the broader concept.
- Steele/Gabriel HOPL II extraction: independent support for S-expression adoption and macro evolution.
- One institutional secondary source for LISP's spread through AI labs.

### Should-add (gap-fills that strengthen but don't block)

- Advice Taker / "Programs with Common Sense" connection — already added to Scene 1 narrative; primary anchor is Ch11 cross-link.
- IBM/FORTRAN cultural foil — McCarthy's brief IBM time, FORTRAN group's disinterest in symbolic manipulation. Scene 1.
- Steve Russell hacker context — Spacewar!, MIT TMRC culture; explains why pragmatic S-expressions won. Scene 3.
- Cambridge Lisp Conference 1962 — transition from MIT-only to shared AI infrastructure. Scene 5 or standalone bridge.
- IBM 704 register naming — `car` = Contents of Address Register, `cdr` = Contents of Decrement Register. Already added to infrastructure-log.md.
- Compare FLPL, IPL, and LISP in a short source-backed table for the prose reviewer.
- Add a Ch22 handoff note once the Lisp-machine chapter contract exists.

### Framing observations

- LISP's historical role is strongest when framed as "enabling substrate" rather than "first list processor."
- The M-expression/S-expression story is a useful humility beat: designers do not always know which part of a system users will adopt.
- Garbage collection belongs with language history and AI history at once. It is a local memory solution with a long managed-runtime afterlife.
- The "purely functional" myth — LISP 1.5 had `prog`, `setq`, property mutation. Guard against retrospective projection.
- The "REPL" anachronism — use "READ / EVAL / PRINT cycle" in prose.
- The "LISP is Math" trap — guard against Graham-esque "discovered" framing; LISP is machine-derived.
- Lisp-1 vs Lisp-2 namespace origin — within LISP 1.5 era, in `eval` design. Flag and forward-link rather than draft.
- Hart/Levin compiler line — interpreted `eval` to compiled production AI infrastructure transition; deserves its own beat in Scene 5b.
