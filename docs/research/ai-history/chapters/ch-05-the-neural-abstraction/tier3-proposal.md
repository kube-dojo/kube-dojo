# Tier 3 proposal — Chapter 5: The Neural Abstraction

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family adversarial).

## Element 1 — Pull-quote (`:::note`, ≤1 per chapter)

**Status: SKIPPED**

Rationale: Rule (b). Every quote-worthy sentence in Ch05 is already in-prose:

- McCulloch-Pitts 1943 abstract phrasing — paraphrased in prose without verbatim quote-marks; the load-bearing claim is "neural events and the relations among them can be treated by means of propositional logic" (already echoed in the opening paragraph that introduces the paper).
- Theorem 7: "Alterable synapses can be replaced by circles" — already quoted (the Theorem 7 paragraph).
- Section 1 framing: "for nets undergoing both alterations [facilitation, extinction, and learning], we can substitute equivalent fictitious nets composed of neurons whose connections and thresholds are unaltered" — already quoted.
- Pitts to McCulloch from MIT: "I now understand at once some seven-eighths of what Wiener says, which I am told is something of an achievement" — already quoted.
- McCulloch on Pitts to Carnap: "the most omnivorous of scientists and scholars" / "in my long life, I have never seen a man so erudite or so really practical" — already quoted.
- Hebb's neurophysiological postulate: "When an axon of cell A is near enough to excite a cell B and repeatedly or persistently takes part in firing it, some growth process or metabolic change takes place in one or both cells such that A's efficiency, as one of the cells firing B, is increased" — already quoted in full.
- von Neumann *First Draft* §4.2: "Following W. Pitts and W. S. McCulloch ('A logical calculus of the ideas immanent in nervous activity', Bull. Math. Bio-physics, Vol. 5 (1943), pp 115-133) we ignore the more complicated aspects of neuron functioning…" — already quoted.

There are no quote-worthy candidate sentences not already in-prose. SKIP per (b), consistent with Ch01–Ch04.

## Element 2 — Plain-reading aside on the propositional-logic equivalence theorem paragraph

**Status: PROPOSED**

Anchor: end of the paragraph that states the equivalence theorem — beginning "Through these elegant constructions, the paper proved a profound theorem: every propositional-logic expression has a corresponding neural net without circles, and conversely, every net without circles realizes such an expression."

The paragraph is *abstractly* dense: it states a bidirectional equivalence between two formal systems (propositional logic and threshold-logic nets) at the level of "every formula → some net" and "every net → some formula" without giving a worked example. The follow-on prose explains the *philosophical* implication ("A physical network of nerve fibers… was mathematically equivalent to a system of formal propositional logic") but does *not* concretely walk a reader through the constructive translation. Earlier in the chapter the AND/OR/NOT gate constructions are described, but they aren't combined into a worked compound formula.

Insertion: immediately after the paragraph ending "…the architecture of an idealized nervous system was exactly the architecture of a deductive logic."

Draft (3 sentences, within the 1-3 sentence cap):
```
:::tip[Plain reading]
Concretely: take a formula like $(A \lor B) \land \lnot C$. The construction walks the parse tree — an OR-gate at threshold 1 fed by the input neurons for $A$ and $B$, an AND-gate at threshold 2 fed by that OR-gate and an inhibitory afferent that fires when $C$ does. Every connective in the formula becomes one threshold-logic gate; the whole formula becomes one net, and the net fires exactly when the formula is true.
:::
```

Rationale: The aside supplies the worked example the equivalence theorem lacks. It uses inline math notation consistent with the broader site (and the new Ch04 Tier 2 sidebar) and reuses vocabulary already introduced in the AND/OR/NOT gate paragraph. It does new work — the surrounding prose names the equivalence but does not demonstrate the construction.

## Element 3 — Inline parenthetical definition (Starlight tooltip)

**Status: SKIPPED**

Rationale: `READER_AIDS.md` item 8 — universal SKIP across every chapter until a non-destructive tooltip component lands. Ch05 has many specialist terms (a-machine, m-configuration, threshold-logic gate, all-or-none, recursive predicate, finite automaton, neurophysiological postulate); the Plain-words glossary covers them.

## Selective dense-paragraph asides — additional candidates considered and rejected

- **The five physical assumptions paragraph** ("In Section 2 of the paper, titled 'The Theory: Nets Without Circles,' the authors lay out five physical assumptions…"). REJECTED — symbolically dense, but the *next* paragraph is already a Tier-3-shaped explanation: "These assumptions deliberately stripped away the messy, continuous biological reality of real neurons—the varying conduction velocities, the synaptic delays… These numbers grounded the all-or-none assumption in the neurophysiology of the 1940s, but they did not enter the formal calculus." Plain-reading already in-prose.
- **The threshold-logic gates paragraph** (AND at threshold 2, OR at threshold 1, NOT by inhibition). REJECTED — the prose constructs each gate explicitly with reasoning ("The target neuron would only fire if both inputs fired simultaneously"). A callout would duplicate.
- **The temporal-shift functor paragraph** ($N_i(t)$, $S(P)(t) \equiv P(t-1)$). REJECTED — the prose closes with a plain-reading sentence: "if a neuron fired, the logical consequence of that firing would propagate to the next neuron with a precise delay of one time step." That IS the plain-reading.
- **The Hilbert-DNF / nets-with-circles paragraph** ("The argument across pages 124 to 130 used the Hilbert disjunctive normal form…"). REJECTED — the next sentence is already plain-reading: "A circle in the net effectively held a proposition in activity—neuron firing now because neuron fired one time step ago—and a finite population of such circles could carry forward the past states a recursive predicate required."
- **Theorem 7 paragraph** ("Alterable synapses can be replaced by circles"). REJECTED — the prose immediately translates: "If a neural network changes its connections over time—if it learns—that changing network can be mathematically re-expressed as a larger, fixed network containing extra circular pathways. These circular pathways, set into activity by specific peripheral afferents, would act as a memory of the learning event…" Plain-reading already in-prose.

## Summary table (for the reviewer)

| # | Element | Status | Approve? Reject? Revise? |
|---|---|---|---|
| 1 | Pull-quote | SKIPPED (rule b) | reviewer: agree / disagree |
| 2 | Plain-reading after the propositional-logic equivalence theorem paragraph | PROPOSED | reviewer: APPROVE / REJECT / REVISE |
| 3 | Inline parenthetical | SKIPPED (universal) | reviewer: agree / disagree |

Calibration vs prior chapters:
- Ch01: 2/5 landed
- Ch02: 0/4 landed
- Ch03: 1/3 landed (theorem-17b absorption-law revise)
- Ch04: 0/3 landed (Tier 2 sidebar absorbed the math)
- Ch05 proposes: 1/3

The PROPOSED element supplies the worked example the equivalence theorem lacks. If the reviewer judges the example duplicates the AND/OR/NOT gate paragraph, REJECT is the right call.
