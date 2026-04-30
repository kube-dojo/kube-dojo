# Tier 3 Proposal: Chapter 36 — The Multicore Wall

Author: Claude (Sonnet 4.6), 2026-04-30.
Cross-family review target: Codex (adversarial, per Tier 3 workflow in READER_AIDS.md).

---

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED globally.** Per READER_AIDS.md §Tier 3 element 8: reserved for a future tooltip component; plain HTML `<abbr>` violates the bit-identity rule. The collapsible Plain-words glossary (Tier 1) covers the same job non-destructively.

---

## Element 9 — Pull-quote

**SKIPPED.**

Rationale: Every load-bearing quotable sentence in the chapter is already rendered verbatim as an attributed inline quote in the prose body:

- Sutter: "CPU performance growth as we have known it hit a wall two years ago." / "Most people have only recently started to notice." — quoted inline, paragraph 3 of "The Free Lunch Is Over."
- Sutter: "Single-threaded programs are likely not to get much faster any more for now except for benefits from further cache size growth." — quoted inline, paragraph 4 of "The Free Lunch Is Over."
- Sutter: "the buffet will only be serving that one entrée and that one dessert" — quoted inline, paragraph 6 of "The Free Lunch Is Over."
- Intel spokesman (via Vance/*The Register*): "We are accelerating our dual-core schedule for 2005." — quoted inline, "The Quiet Cancellation."

All four candidate sentences hit READER_AIDS.md refusal rule (b): "the prose paragraph already quotes the sentence verbatim — duplicating it as a callout creates adjacent repetition." No non-verbatim sentence rises to quote-worthy on its own.

Disposition: **SKIP** — no candidate survives the adjacent-repetition test.

---

## Element 10 — Selective dense-paragraph asides (`:::tip[Plain reading]`)

**SKIPPED.**

Rationale: READER_AIDS.md restricts plain-reading asides to paragraphs that are *symbolically* dense — mathematical formulas, derivations, abstract definitions stacked. Ch36 is a narrative chapter throughout. Checking the prose for symbolic density:

- **Dennard scaling** is described in prose as "shrink transistor dimensions by about 30% per generation, keep the electric field constant, double density, and gain speed while lowering voltage" — a qualitative engineering recipe, not a formula.
- **Power Wall / Memory Wall / ILP Wall** are named conceptually (Power Wall + Memory Wall + ILP Wall = Brick Wall) — a conceptual equation cited in the Berkeley View report, but not a derivation or mathematical notation in the chapter prose.
- **Pollack's Rule** appears in people.md as a background reference only; it is not rendered in the chapter prose with symbolic notation.
- No chapter paragraph contains mathematical notation, inline LaTeX ($…$), integral or summation signs, or abstract symbol definitions.

The chapter is narratively dense (it has a large cast, five distinct scenes, and a compressed timeline) but that does not qualify for a plain-reading aside per spec. Applying asides to narrative prose would produce commentary that merely paraphrases the surrounding sentences — exactly the condition the spec says to refuse.

Disposition: **SKIP** — no symbolically dense paragraph present. Default SKIP for narrative confirmed.
