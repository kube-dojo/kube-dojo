# Scene Sketches: Chapter 12 - Logic Theorist and GPS

## Scene 1: The Paper Machine

- **Setting:** RAND/Carnegie Tech in the moment before a clean machine-run story exists.
- **Beat:** LT is first a program one can barely hand simulate. The drama is not a blinking console. It is the discovery that a stack of symbolic routines can be followed as if a person were executing a machine.
- **Narrative Use:** Opens the chapter by correcting the timeline: hand trace first, computer realization later. This gives the reader a precise boundary for the "first running symbolic-AI program" claim.
- **Evidence Anchors:** `P-868`, p. 1 for specification-not-realization; `P-868`, p. 3 for hand simulation; `CBI91`, pp. 3-9 for Newell's RAND/Shaw/Selfridge path.
- **Pedagogical Demonstration:** Show a theorem-proving program as a recipe over paper memories: read expression, compare expression, choose rule, add result to a list.
- **Should-Extract (per Gemini gap audit 2026-04-27):** `P-671` (Newell, "The Chess Machine," March 1955) as the intellectual bridge between RAND organizational simulations and symbolic search. Without it, the Selfridge talk reads as an isolated epiphany rather than a turn within already-active conceptual work toward a specific technical realization. Yellow until extracted.

## Scene 1b: The Selfridge Trigger and the Chess Prelude (deferred merge into Scene 1 once `P-671` is anchored)

- **Setting:** Late 1954 — Newell has already drafted "The Chess Machine" and circulated it through RAND-Carnegie correspondence. Selfridge's RAND talk lands in a mind already organized around heuristic search.
- **Beat:** "Information processing as a way to understand thinking" was not a sudden revelation; it was a clarification of work already in motion. The chess paper is the precondition that lets LT happen so quickly.
- **Narrative Use:** Tightens Scene 1 by replacing the implicit "Selfridge cause / LT effect" reading with a more accurate "concurrent trajectories meeting" reading.
- **Evidence Anchors:** `P-671` pending; `CBI91` p. 9 for Newell's "made it clear" recollection.

## Scene 2: The Theorem-Proving Search

- **Setting:** The sentential calculus of *Principia Mathematica*, represented as symbols, elements, memories, theorem lists, active problem lists, and routines.
- **Beat:** LT does not "understand" mathematics in a human literary sense. It manipulates expressions and searches for proofs using heuristics. The important move is treating proof discovery as structured symbol search.
- **Narrative Use:** This is the chapter's main teaching scene. It should explain why proof search can explode combinatorially and why heuristics mattered.
- **Evidence Anchors:** `P-868`, pp. 7-16 for representation machinery; `P-868`, pp. 2-3 for heuristic-vs.-algorithm framing; `P-868`, p. 8 for the *Principia Mathematica* source domain.
- **Pedagogical Demonstration:** Use one symbolic expression from `P-868` rather than inventing a new one. Avoid exact theorem-count claims until `NSS57` is anchored.

## Scene 3: Dartmouth From the Other Side

- **Setting:** Ch11's Dartmouth summer, viewed briefly from Newell and Simon's arriving research program rather than from McCarthy's naming agenda.
- **Beat:** LT is the concrete symbolic program in a summer otherwise dominated by proposals, conversations, and disciplinary positioning. But the Ch12 prose must say "demonstrated/discussed" unless a source proves live execution.
- **Narrative Use:** Cross-links Ch11 Scene 3 while preventing a duplicate Dartmouth chapter.
- **Evidence Anchors:** Ch11 `sources.md` Yellow LT-at-Dartmouth claim; `CBI91`, pp. 10-12 for Newell's recollection of Dartmouth and the still-unnamed field; `P-868`, p. 1 for post-summer IRE presentation.

## Scene 4: GPS and Means-Ends Analysis

- **Setting:** The post-LT laboratory and conference-paper environment where Newell, Shaw, and Simon try to generalize proof-search lessons.
- **Beat:** GPS turns a problem into objects, operators, differences, goals, and subgoals. The machine asks: what is different between where I am and where I want to be, what operator might reduce that difference, and what subgoal must be solved to apply it?
- **Narrative Use:** This is the conceptual payoff. It explains why GPS mattered even though it was not general intelligence.
- **Evidence Anchors:** `P-1584`, pp. 1, 3-6; `GPS61`, pp. 114-117.
- **Pedagogical Demonstration:** Use the three GPS goal types from `GPS61`: transform object A into object B; reduce difference D; apply operator Q.

## Scene 4b: The Protocol-Data Turn (per Gemini gap audit must-fix #2)

- **Setting:** Mid-1957 onward, in the Newell-Simon laboratory at Carnegie Tech.
- **Beat:** GPS does not become "general" by being given more theorems to prove. It becomes a different kind of object: a *theory of human problem solving* whose operators and differences are derived from human thinking-aloud protocols. The methodological pivot is from "build a better solver" to "let the solver's structure be defined by what humans actually do." This is the move that makes GPS publishable in psychology journals as well as computer science conferences.
- **Narrative Use:** Sharpens Scene 4 by separating "GPS as algorithm" from "GPS as cognitive theory." Without this beat, the Generality Ceiling scene reads as engineering disappointment rather than methodological repositioning.
- **Evidence Anchors:** `GPS61`, p. 109 (GPS as theory developed from protocol data, dual AI/psychology role); `GPS61`, pp. 111-113 (experimental symbolic-logic problem with rules, solution trace, protocol).
- **Conflict to surface:** historiographic debate "did GPS fail because it could not solve hard problems (Performance reading) or succeed because it failed in the same way humans do (Simulation reading)?"

## Scene 5: The Generality Ceiling

- **Setting:** The same GPS architecture seen from its limits: task vocabularies, operator tables, feasibility tests, evaluation, memory, and IPL-style implementation.
- **Beat:** GPS is general in the shape of its control structure but dependent on supplied task environments and hand-built methods. The program can be brilliant and limited at the same time.
- **Narrative Use:** Prevents triumphalist AGI framing and sets up later chapters on symbolic AI's successes and bottlenecks. Make the historiographic axis explicit per Gemini gap audit (Performance reading vs Simulation reading), and forward-link to STRIPS / Project MAC planning work in Ch20 to show GPS architecture migration out of Carnegie/RAND.
- **Evidence Anchors:** `P-1584`, p. 6 for special heuristics, programming-language effort, evaluation, and exponential possibility spaces; `GPS61`, pp. 114-117 for goal/subgoal mechanics.
- **Should-link:** SAD-SAM (Lindsay 1958) and EPAM (Feigenbaum 1959/1961) as concurrent symbolic-AI work outside Newell-Simon, both Yellow follow-up sources.

## Anti-Padding Rule

If the final prose needs more length, expand the verified mechanics: memories, lists, routines, goal types, and means-ends analysis. Do not add invented Dartmouth dialogue, unsourced typewriter drama, unverified theorem counts, or claims that GPS was close to general intelligence.
