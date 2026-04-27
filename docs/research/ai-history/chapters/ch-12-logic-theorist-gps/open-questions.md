# Open Questions: Chapter 12 - Logic Theorist and GPS

## Must Resolve Before `reviewing`

- Can `NSS57` be obtained and searched for the exact LT performance claims: 38 of 52, theorem list, run conditions, JOHNNIAC, and IPL?
- What is the primary page anchor for the Theorem 2.85 cleaner-proof story and the *Journal of Symbolic Logic* rejection? `Simon-Models` is likely, but not verified here.
- What source anchors the typewriter-driven first proof of Theorem 2.01? `P-868` supports hand simulation only generally.
- What is the exact chronology between hand trace, `P-868`, Dartmouth discussion, JOHNNIAC realization, and WJCC empirical report?
- Did Newell and Simon demonstrate LT at Dartmouth by walking through a trace, by showing output, or by some other form of evidence? Ch11 currently keeps this Yellow.
- Which source best supports "first running symbolic-AI program" without collapsing into the broader and contested "first AI program" claim?
- How much GPS capability was present in GPS-I versus later GPS variants through 1972? The chapter should not project later Ernst/Newell claims backward onto 1959.
- Which Dreyfus or Schank passages should be used for the GPS generality critique, if any?

## Resolved Anchors

- `P-868`, p. 1: LT is specified as a proof-discovery system in symbolic logic; the paper is about specification, not computer realization; Shaw is credited for realization work.
- `P-868`, p. 3: LT is complex, heuristic, and barely hand-simulatable.
- `P-868`, pp. 5-6: digital-computer realization requires suitable pseudo-code/interpretive language; limits are speed and memory; a similar language was being coded.
- `P-868`, pp. 7-16: symbolic expressions, memories, lists, theorem/problem lists, instructions, branches, and routines are anchored.
- `P-1584`, p. 1: GPS-I is a digital-computer program and the research method is synthesis through programs exhibiting intelligent behavior.
- `P-1584`, pp. 3-6: objects/operators framing, planning, special heuristics, information-processing languages, evaluation, and exponential possibility spaces are anchored.
- `GPS61`, pp. 109-117: GPS as protocol-based human-problem-solving simulation, three goal types, recursive subgoals, feasibility tests, and difference/operator tables are anchored.
- `CBI91`, pp. 3-12: Newell's RAND/Shaw/Selfridge/Dartmouth retrospective is anchored.

## Drafting Warnings

- Do not write "LT was the first AI program" without "symbolic" and surrounding caveats.
- Do not say LT ran at Dartmouth unless a primary source proves it.
- Do not write the "38 of 52" claim in confident prose until `NSS57` is page-anchored.
- Do not write the Theorem 2.85/JSL rejection anecdote as a scene until `Simon-Models` or an equivalent primary source is extracted. **Demoted to Red 2026-04-27** per Gemini gap audit — the "Luddite logic establishment" framing is contested and risks perpetuating a biased narrative.
- Do not let GPS's name imply broad general intelligence. Its own primary sources show supplied task vocabularies, heuristics, evaluation, and programming infrastructure.
- Do not turn the chapter into a Dartmouth rerun. Ch11 owns the naming conference; Ch12 owns the program architecture.
- Do not cite `IPL-V` (RAND P-1897, 1960) as the LT runtime reference — LT used IPL-I/II/III in 1956-57. Citing IPL-V is a technical anachronism.

## Gap-Audit Worklist (per Gemini 2026-04-27)

### Must-fix tractable
- `P-671` (Newell, "The Chess Machine," March 1955) — the chess prelude that primed Newell on heuristic search before the Selfridge talk. Without it, Scene 1's Selfridge moment reads as an isolated epiphany. Add when extracted.
- 1957 protocol-data turn — make explicit in the GPS scene as the methodological pivot from solver to cognitive theory. Already substantively present in `GPS61` p.109 and pp.111-113; Scene 4b added to surface it.
- IPL versioning correction (IPL-I/II/III for 1956-57, not IPL-V 1960) — applied to infrastructure-log.md and sources.md.
- Theorem-count dependency — chapter prose capped near 4500 words until `NSS57` anchors the "38 of 52" specifically. If `NSS57` reveals a different number or run condition, Scene 2 needs a rewrite, not a patch.

### Should-add
- EPAM (Feigenbaum 1959/1961) — symbolic architecture extended to perception/memory; demonstrates Information Processing Psychology breadth. Yellow source row added.
- SAD-SAM (Lindsay 1958) — concurrent symbolic-AI claim applying list-processing to natural language; challenges Carnegie/RAND uniqueness. Yellow source row added.
- General Inquirer (Stone et al., 1960s) — non-AI symbolic system contrast for the "what made GPS distinct" beat. Yellow source row added.
- Project MAC GPS-derivative work (STRIPS / Fikes-Nilsson 1971+) — forward-link from Generality Ceiling scene; belongs primarily in Ch20.

### Framing observations
- LT/Logic Theorist naming hinge — files use both "The Logic Theory Machine" (1956 paper title) and "Logic Theorist" (later usage). The shift reflects field maturation from "machine artifact" to "agent/theorist." Note the moment in prose without making it a section.
- Performance vs Simulation tension — make the historiographic axis explicit in Scene 5: did GPS fail (couldn't solve hard problems) or succeed (failed in the same way humans do)?
- RAND-Carnegie correspondence as load-bearing infrastructure — added to infrastructure-log.md.
