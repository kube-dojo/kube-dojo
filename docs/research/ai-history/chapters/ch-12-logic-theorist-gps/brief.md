# Brief: Chapter 12 - Logic Theorist and GPS

## Thesis

Logic Theorist and GPS made symbolic AI executable in two different senses. Logic Theorist showed that a machine-oriented symbol system could search for proofs in the sentential calculus, using heuristics instead of a blind decision procedure. GPS then tried to lift part of that success into a reusable architecture: objects, operators, differences, goals, subgoals, means-ends analysis, and planning. The chapter's historical hinge is not "machines became generally intelligent." It is narrower and stronger: Newell, Simon, and Shaw turned problem solving into inspectable symbol manipulation, then discovered how much infrastructure and task knowledge were still needed.

## Scope (IN/OUT)

- IN SCOPE: Logic Theorist as a symbolic theorem-proving program; the hand-trace before machine realization; JOHNNIAC and IPL as implementation infrastructure; RAND and Carnegie Tech as research settings; *Principia Mathematica* Chapter 2 as the task domain; the transition from LT heuristics to GPS means-ends analysis; GPS-I and later GPS variants as problem-solving architectures; the boundary between AI performance and psychological simulation.
- OUT OF SCOPE: Dartmouth as the naming event except for the Ch11 cross-link; McCarthy's LISP except as Ch13 handoff; the perceptron and neural programs except for first-AI-program boundary nuance; later resolution theorem proving and expert systems; Newell and Simon's later Physical Symbol System Hypothesis except as a brief downstream pointer.

## Boundary Contract

This chapter should call Logic Theorist the first running symbolic-AI program only with the qualifier "symbolic" and only after separating three moments: the late-1955/early-1956 hand simulation, the June/September 1956 specification paper, and the later computer realization work associated with Shaw and IPL. It must not call LT the first AI program without qualification. McCulloch-Pitts neural modeling predates it in a different paradigm, Samuel's checkers work is contemporaneous, and Ch11 has already positioned Dartmouth as a naming event rather than an origin point.

GPS must be framed as a move from a problem-specific proof searcher toward a general problem-solving architecture, not as working general intelligence. Its durable contribution is means-ends analysis and the separation between task-environment knowledge and problem-solving methods. The program still needed correlative definitions, hand-built operator/difference tables, feasibility tests, memory organization, and later revisions.

Do not conflate LT and GPS. LT's dramatic scene is theorem proving in Whitehead and Russell's sentential calculus. GPS's dramatic scene is the architecture that turns a problem into objects, operators, differences, goals, and recursive subgoals.

## Scenes Outline

1. **The Paper Machine.** Newell and Simon can barely hand-simulate LT before it is realized on a computer. The scene should show paper, lists, and symbolic expressions rather than a magical machine-room breakthrough. Anchor: `P-868`, pp. 1, 3, 5-6; `CBI91`, pp. 3, 9-12.
2. **The Theorem-Proving Search.** LT works in the sentential calculus of *Principia Mathematica*, treating expressions as symbol structures, storing theorem/problem lists, and applying heuristics to avoid blind enumeration. Anchor: `P-868`, pp. 7-16; `P-1584`, pp. 1, 6.
3. **Dartmouth Cross-Link.** Ch11 Scene 3 can mention Newell and Simon arriving with LT as the substantial running symbolic program, but Ch12 owns the technical explanation and should preserve the hand-trace vs. computer-run distinction. Anchor: Ch11 `sources.md` Yellow claim; `CBI91`, pp. 10-12; `P-868`, p. 1.
4. **From LT to GPS.** GPS grows out of LT and laboratory protocol work, then recasts problem solving around objects, operators, differences, goals, subgoals, means-ends analysis, and planning. Anchor: `P-1584`, pp. 1, 3-6; `GPS61`, pp. 109-117.
5. **The Generality Ceiling.** GPS is intentionally general in architecture but limited in practice by supplied task representations, operator tables, evaluation heuristics, and programming-language infrastructure. Anchor: `P-1584`, p. 6; `GPS61`, pp. 114-117.

## Prose Capacity Plan

This chapter can support a 4,000-6,000 word narrative if it stays inside the verified layers below:

- 700-900 words: **Paper before machine** - Scene 1, anchored to `P-868` pp. 1, 3, 5-6 and `CBI91` pp. 3, 9-10. Use this to explain why the first demo should be staged as hand-simulation and specification work, not as an immediate JOHNNIAC scene.
- 900-1,100 words: **How LT represented logic** - Scene 2, anchored to `P-868` pp. 7-16. Explain expressions as trees/lists, theorem/problem lists, working and storage memories, and routines. This is the main pedagogical demonstration layer.
- 500-700 words: **What LT did and did not prove** - Scene 2, anchored to `P-868` pp. 1, 3 plus the Yellow `NSS57` worklist for theorem-count and Theorem 2.85 claims. Keep the exact "38 of 52" and JSL rejection story out of Green prose until a primary page anchor is extracted.
- 500-700 words: **Dartmouth as cross-link, not origin** - Scene 3, anchored to Ch11 `brief.md`/`sources.md` plus `CBI91` pp. 10-12. Use only a compact bridge; Ch11 owns the naming event.
- 900-1,200 words: **GPS architecture** - Scene 4, anchored to `P-1584` pp. 1, 3-6 and `GPS61` pp. 109-117. Explain objects/operators/differences and the three goal types without claiming general intelligence.
- 500-800 words: **Infrastructure ceiling** - Scene 5, anchored to `P-1584` p. 6, `GPS61` pp. 114-117, and `P-868` pp. 5-6. Show why IPL, memory organization, evaluation, and task encodings matter.
- 300-500 words: **Honest attribution close** - Scenes 3 and 5, anchored to `CBI91` pp. 10-12 and the Yellow secondary-source worklist. Distinguish first running symbolic-AI program, first AI program, and first general-purpose intelligence claims.

If the theorem-count, Theorem 2.85, and JSL rejection anchors remain Yellow, cap the chapter near 4,500 words and do not pad with folklore.

## Citation Bar

- Minimum primary sources before prose review: `P-868`, `P-1584`, `GPS61`, and one implementation source — `IPL-I/II/III` for the 1956-57 LT runtime (not `IPL-V` 1960), or "Programming the Logic Theory Machine" (`Programming-LT`) — with page anchors.
- Minimum secondary/context sources before prose review: McCorduck, Crevier, Nilsson, and one critique or retrospective source on GPS's limits.
- Current status: core LT representation and GPS means-ends architecture are Green from verified PDF page anchors. Exact theorem-count folklore and typewriter-driven Theorem 2.01 remain Yellow until a primary page anchor is extracted. The Theorem 2.85/JSL rejection anecdote was demoted to Red 2026-04-27 per Gemini gap audit (the "Luddite establishment" framing is contested and primary-source-blocked).

## Historiographic Axis (per Gemini gap audit 2026-04-27)

The Performance-vs-Simulation tension should be surfaced explicitly: did GPS fail because it could not solve hard problems (Performance reading, Dreyfus 1972 trajectory) or succeed because it failed in the same way humans do (Simulation reading, the GPS61 protocol-data trajectory)? The chapter is more honest if it presents this as a structural debate than if it picks a side. Scene 5 carries this framing.
