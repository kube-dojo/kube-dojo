# Tier 3 Proposal — Chapter 33: Deep Blue

Author: Claude (claude-sonnet-4-6)
Date: 2026-04-30

---

## Element 8 — Inline parenthetical definition (tooltip)

**SKIPPED** — globally per READER_AIDS.md spec. The non-destructive Astro `<Tooltip>` component does not yet exist. The plain-words glossary (Tier 1 item 4) covers the same job without touching prose.

---

## Element 9 — Pull-quote

**SKIPPED**

Rationale: Ch33 is a narrative-historical chapter. The most quotable load-bearing sentence in the chapter — "It was a fail-safe" / "panic managed by code" — is original prose, not a passage from a primary source. The Green-anchored primary sources in `sources.md` that contain actual quoted text are:

- Campbell's retrospective in Newborn 2003 p.151: "They conjectured that Deep Blue had looked 30-40 levels ahead at the alternatives — they were overestimating Deep Blue's talents here … this might have been a factor in the next game where, in the final position, Kasparov overestimated Deep Blue's strength." — This quote already appears in the chapter prose (Scene 3 / Game 1 bug episode), rendering a callout adjacent-repetitive.
- Campbell 2017 SciAm: "between 100 million and 200 million positions per second, depending on the type of position" and "we had achieved our goal." — Both are paraphrased in the chapter prose and neither is standalone-quotable at the sentence level without surrounding narrative context.
- Hsu 1999 IEEE Micro: technical paper; no single sentence rises to pull-quote worthiness without context.

No candidate meets both requirements (Green primary-source anchor + not already quoted verbatim in prose). Skipped on adjacent-repetition grounds.

---

## Element 10 — Plain-reading asides

**SKIPPED**

Rationale: Ch33 is entirely narrative-historical. There are no symbolically dense paragraphs — no mathematical derivations, no stacked abstract definitions, no formal notation. The "chip architecture" passages (Scene 2: chip block diagram, alpha-beta hierarchy, ply counting) are technically detailed but are narrated discursively in plain English, not as equations or symbolic formulas. The spec reserves Element 10 for paragraphs that are *symbolically* dense, not narratively dense. No paragraph in Ch33 meets that threshold.

The closest candidate is the search-hierarchy paragraph beginning "The search itself was a hierarchy…" — but it explains concepts in plain English prose and contains no notation that would benefit from a paraphrase aside. Adding one would only repeat surrounding text.
