# Gap Analysis: Chapter 12 - Logic Theorist & GPS

Source: Gemini gap analysis (gemini-3-flash-preview, message #2913) on
PR #419 / Issue #401, recorded 2026-04-27. Codex authored the contract
with 14 Green / 4 Yellow / 4 Red claims. Claude integrated Gemini's
audit (commit `a3e227ae`).

## Current Verdict

Research contract approved with status `capacity_plan_anchored` and
review_state `claude_integrated_gemini_2026-04-27`. Codex's primary
anchors are `LT57-Newell-Shaw-Simon` (the 1957 IRE paper "Empirical
Explorations of the Logic Theory Machine"), `IPL-V` (the 1960 IPL-V
programmer's reference manual — flagged by Gemini as anachronistic for
LT's 1956 IPL-I/II/III runs), `NSS57` (the *Psychological Review* GPS
paper), and `Newell58Heuristic` (the 1958 RAND paper). Four Red
framings block: LT live-executed at Dartmouth; LT as a deductive
universal theorem prover; GPS as a trivially "general" intelligence
model; JOHNNIAC as an unconstrained machine.

## Gemini's Audit (verbatim categories, integrated)

### Must-fix (substantive gaps that block accepted status)

1. **Absence of the Chess-Program Prelude (P-671):** Newell's 1955
   paper "The Chess Machine" served as the intellectual bridge between
   organizational simulation and symbolic search. Without this prelude,
   the "Selfridge trigger" feels isolated rather than a step toward an
   already-emerging technical realization. **Integrated** — added
   `Newell55Chess` (P-671) to sources.md and Scene 1 prelude beat.
2. **The 1957 Protocol-Data Turn:** the transition from LT to GPS was
   not just a move toward "generality" — it was the methodological
   pivot to use human thinking-aloud protocols to define GPS's
   operators, which transformed GPS from a logic-solver into a theory
   of human cognition. **Integrated** — Scene 4 protocol-analysis
   methodological-pivot beat.
3. **IPL Versioning Anachronism:** `IPL-V` (1960) cannot describe the
   1956-1957 LT implementation context; LT was implemented and run
   in IPL-I through IPL-III iterations. **Integrated** —
   infrastructure-log.md flags the IPL-I/II/III versioning for the
   1956-1957 LT runs and reserves `IPL-V` for the GPS-era discussion;
   sources.md adds `IPL-II56` worklist item.
4. **Theorem Count Dependency:** the "38 of 52" claim is the chapter's
   primary performance data point but is currently Yellow. Drafting a
   4,000+ word chapter before verifying this specific count in
   `NSS57` / `LT57-Newell-Shaw-Simon` is a risk. **Integrated** —
   open-questions.md flags the theorem-count anchor as a
   prose-readiness blocker.

### Should-add (gap-fills that strengthen but don't block)

1. **EPAM (Feigenbaum 1959/1961):** as a direct descendant of the
   Newell-Simon-Shaw symbolic architecture, EPAM shows the breadth of
   the Information Processing Psychology program beyond logic.
   **Integrated** — added to sources.md as Yellow worklist; Scene 5
   forward-link beat.
2. **Competing Symbolic Claims (SAD-SAM, 1958):** Lindsay's SAD-SAM
   shows that by GPS's 1959 Paris presentation, other researchers were
   already applying list-processing to natural language, challenging
   the "uniqueness" of the Carnegie/RAND trajectory. **Integrated** —
   added to sources.md as Yellow worklist.
3. **The General Inquirer (Stone et al., 1960s):** anchors the
   "generality" claim against other non-AI symbolic systems, clarifying
   what made GPS's means-ends analysis distinct. **Integrated** —
   open-questions.md cites it as a "generality" boundary worklist
   item.
4. **Project MAC GPS-Derivative Work (STRIPS, early planners):**
   closes the "Generality Ceiling" scene by showing the architecture
   migrated out of the Carnegie/RAND ecosystem. **Integrated** —
   Scene 5 forward-link beat (Project MAC = Ch20 forward-pointer).

### Framing observations (boundary contract notes)

1. **Performance vs. Simulation Tension:** the contract identifies the
   boundary in scope, but Scene Sketches don't yet surface this as
   a conflict — was GPS a failure (couldn't solve hard problems) or a
   success (failed in the same way humans do)? **Integrated** —
   brief.md Historiographic Axis beat; Scene 4 protocol-pivot scene
   makes the simulation-success vs. performance-failure ambiguity
   explicit.
2. **The "Logic Theorist" Naming Hinge:** the files oscillate between
   "Logic Theory Machine" (1956) and "Logic Theorist" (later). The
   chapter should explicitly note when the shift occurred — it
   reflects the field's transition from "machine" to "agent."
   **Integrated** — Scene 2 naming-hinge note.
3. **Institutional Correspondence:** the RAND-Carnegie correspondence
   (letters/memos) was as important as JOHNNIAC memory maps in
   enabling the two-node collaboration. **Integrated** —
   infrastructure-log.md adds the RAND-Carnegie correspondence as a
   working-infrastructure beat.

### Yellow → Red proposals

1. **Theorem 2.85 and JSL Rejection (Yellow → Red).** The "rejection"
   story is core AI folklore often used to paint logicians as
   Luddites; historical accounts suggest the rejection was for
   technical reasons (the proof was not a significant new contribution
   to logic). Drafting a vivid scene without the exact text of the
   rejection risks perpetuating a biased narrative. **Integrated** —
   Scene-Level Claim Table Red row added against the
   "logicians-as-Luddites" framing; Scene 3 keeps the rejection beat
   neutral.
2. **Dartmouth Live Execution.** The contract already marks LT live-
   executed at Dartmouth as Red. **Already in place** — keeping this
   guardrail prevents collapsing into a triumphalist machine-room
   scene that contradicts the actual "discussion/demonstration"
   reality at Dartmouth. **Confirmed kept.**

## Claims Still Yellow or Red

| Claim Area | Status | Why |
|---|---|---|
| 38 of 52 theorems claim | Yellow | Primary count not yet verbatim-extracted from `LT57-Newell-Shaw-Simon` / `NSS57`. |
| IPL-I/II/III runtime details for 1956-1957 LT | Yellow | `IPL-V` is anachronistic; earlier IPL versioning manuals not yet anchored. |
| RAND-Carnegie correspondence content | Yellow | Existence well-attested; specific letters/memos not page-anchored. |
| Theorem 2.85 JSL rejection text | Red as folklore framing / Yellow as event | Event happened; exact rejection wording and reasoning need primary record. |
| Protocol-analysis 1957 methodological pivot detail | Yellow | `NSS57` evidence Green at high level; specific protocol-analysis sessions Yellow. |

Five Red framings remain forbidden in prose: LT live-executed at
Dartmouth (it was discussed/demonstrated, not run live); LT as a
deductive universal theorem prover; GPS as trivially "general"
intelligence; JOHNNIAC as unconstrained; logicians-as-Luddites JSL
rejection framing.

## Word Count Assessment

- Core range now: `4k-7k supported`. The Newell/Simon/Shaw primary
  papers plus Gemini's added beats support a 4,500-6,000 word chapter.
- Stretch range with the 38/52 theorem-count anchor, IPL-I/II/III
  versioning record, and RAND-Carnegie correspondence: 6,000-7,000
  words.

## Required Anchors Before Prose Readiness

- Theorem-count primary anchor in `LT57-Newell-Shaw-Simon` or `NSS57`.
- IPL-I/II/III earlier-versioning manual or `Newell58Heuristic`
  appendix to replace the `IPL-V` anachronism for the 1956-1957
  context.
- Newell 1955 chess-machine paper P-671 — already added to sources.md
  worklist.
- RAND-Carnegie correspondence indicative records.

## Scene Strength

| Scene | Strength | Notes |
|---|---|---|
| Scene 1 — Newell's chess-machine prelude + Selfridge trigger | Medium-strong | P-671 worklist + `Newell58Heuristic` Green; chess-prelude beat now explicit. |
| Scene 2 — The Logic Theory Machine, 1956 | Medium-strong | `LT57-Newell-Shaw-Simon` anchors LT's design; theorem count pending. |
| Scene 3 — Dartmouth Discussion, Not Live Execution | Strong | Red guardrail prevents triumphalist framing; Ch11 cross-link Green. |
| Scene 4 — Protocol Analysis and the GPS Pivot | Medium-strong | `NSS57` anchors GPS's means-ends framework; specific protocol sessions Yellow. |
| Scene 5 — Generality Ceiling, EPAM, and the IPP Successor Lineage | Medium | EPAM/SAD-SAM/Stone Yellow worklist items; Project MAC = Ch20 forward link. |

## Handoff Requests

- Codex anchor verification: confirm Newell 1955 P-671 ("The Chess
  Machine") existence in RAND archives and produce a usable page
  anchor.
- Codex extraction: locate `IPL-II56` or equivalent for the
  1956-1957 LT implementation context (the `IPL-V` anachronism must
  be repaired).
- Verify the 38/52 theorem count in `LT57-Newell-Shaw-Simon` or the
  Newell/Simon retrospective records.
- Decide whether EPAM, SAD-SAM, and the General Inquirer need their
  own primary anchors or only secondary citation.
- Pull RAND-Carnegie correspondence indicative records (Carnegie Mellon
  archive, RAND archive) for the Scene-2/3 institutional-correspondence
  beat.
