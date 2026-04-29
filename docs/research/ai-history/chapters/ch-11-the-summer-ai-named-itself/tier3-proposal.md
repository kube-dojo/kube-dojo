# Tier 3 Proposal — Chapter 11: The Summer AI Named Itself

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED on every chapter** per `READER_AIDS.md` until a non-destructive tooltip component lands. The collapsible *Plain-words glossary* (Tier 1) covers the same job non-destructively.

## Element 9 — Pull-quote (at most 1)

**PROPOSED.** The chapter has zero verbatim quotes from primary sources — it operates entirely through narrative paraphrase. That makes the question of which sentence to elevate non-trivial. The strongest candidate is the proposal's iconic opening declaration, which the chapter circles around (lines 62, 70, 100, 132) but never quotes:

**Candidate A — proposal opening sentence**

Source: McCarthy, Minsky, Rochester, Shannon, "A Proposal for the Dartmouth Summer Research Project on Artificial Intelligence," August 31, 1955, p. 1. Standard text widely reproduced in secondary literature:

> "We propose that a 2 month, 10 man study of artificial intelligence be carried out during the summer of 1956 at Dartmouth College in Hanover, New Hampshire."

**Insertion anchor:** immediately after the line at line 62 ending "…and Claude Shannon of Bell Labs."

**Proposed callout:**

```markdown
:::note
> "We propose that a 2 month, 10 man study of artificial intelligence be carried out during the summer of 1956 at Dartmouth College in Hanover, New Hampshire."

The proposal's opening line. Two months and ten men — a budget framing, not a research design. The "10 man study" never materialised; roughly six attendees stayed for substantial portions, and only three for the full eight weeks. The phrase that *did* materialise was the one in the title.
:::
```

**Why this clears the rule:** the candidate is not quoted verbatim anywhere in the chapter prose; the annotation does new work (anchors the framing-vs-actuality gap that the Scenes 3–4 prose unpacks); and the typographic event marks the chapter's load-bearing shift from "names on a proposal" to "the term that survived."

**Verification needed before Codex review approves:** the verbatim wording above should be checked against the Stanford-hosted PDF (jmc.stanford.edu/articles/dartmouth/dartmouth.pdf). If the actual proposal text differs (e.g. different punctuation, "ten man" vs "10 man," different sentence break), Codex should propose the corrected verbatim and I'll revise.

## Element 10 — Plain-reading asides (1–3 per chapter)

`READER_AIDS.md`: "Use only on paragraphs that are *symbolically* dense (mathematical formulas, derivations, abstract definitions stacked) — **not** narratively dense (history, biography, who-said-what)."

Chapter 11 is **almost entirely** narrative-analytical. Survey of the closest-to-symbolic paragraphs:

### Candidate B — the seven research topics (line 70)

> "Its seven topics were automatic computers, programming computers to use language, neuron nets, the size of a calculation, self-improvement, abstractions, and randomness and creativity."

**Status: SKIPPED.** The same paragraph immediately unpacks each topic in plain language ("Automatic computers pointed to the stored-program machinery…"). A Plain-reading aside would only repeat what the next eight sentences already do.

### Candidate C — the alternatives walkthrough (lines 86–92)

> "Cybernetics" / "Automata theory" / "Complex information processing" / "Thinking machines" — four paragraphs walking through rejected names.

**Status: SKIPPED.** This is narrative density (four discipline labels, each with its political baggage), not symbolic density. A Plain-reading aside would substitute commentary for prose without doing new work.

### Candidate D — the "institutional condensation" closing (line 132)

> "Dartmouth's durable achievement was institutional condensation. It condensed prior lines of thought into a fundable name. It condensed four credentials into a recognizable organizing group. It condensed a scattered set of machine-intelligence problems into seven topics that could be printed on a proposal and defended to a foundation. It condensed a disappointing summer into a later origin story."

**Status: SKIPPED.** The paragraph is metaphorical (the metaphor is "condensation"), not symbolic. The next paragraph already unpacks the metaphor explicitly ("avoids the false choice between invention and irrelevance"). A Plain-reading aside would duplicate.

## Summary verdict

- Element 8: SKIP (universal default).
- Element 9: 1 PROPOSED (proposal opening sentence).
- Element 10: 0 PROPOSED, 3 SKIPPED.

**Total: 1 PROPOSED, 4 SKIPPED.**

Author asks Codex to:
1. Verify the verbatim wording of the candidate pull-quote against the Stanford PDF, and propose the corrected text if mine is off.
2. Confirm or reject the SKIP rationale on B, C, D.
3. Identify any paragraph the author missed that genuinely deserves a Plain-reading aside (high bar: symbolic density + non-redundant clarification).
