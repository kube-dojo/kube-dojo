# Tier 3 review — Chapter 36

Reviewer: Codex (gpt-5.5, model_reasoning_effort=high), 2026-04-30, adversarial cross-family pass on PR for `claude/394-ch36-reader-aids`.

## Element 8 — Tooltip

Verdict: CONFIRM SKIP
One-line reason: The Tier 3 spec reserves tooltips for a future non-destructive component; adding inline tooltip markup now would alter prose lines and violate the bit-identity rule.

## Element 9 — Pull-quote

Verdict: CONFIRM SKIP
One-line reason: The quote-worthy Green primary sentences are already quoted in the chapter body, and the remaining Green candidates would only restage nearby paraphrase instead of adding provenance, stakes, or lineage.

I checked the obvious revival candidates against the adjacent-repetition gate. Sutter's "CPU performance growth..." and "Single-threaded programs..." sentences, the Intel spokesman's "We are accelerating..." sentence, Sutter's buffet metaphor, and the Berkeley View "recent switch..." sentence already appear verbatim in the prose. Berkeley View table lines such as "Power Wall + Memory Wall + ILP Wall = Brick Wall" and "Power is expensive, but transistors are free" are Green, but the surrounding "Naming the Wall" paragraphs already do that explanatory work; turning them into a callout would be decorative repetition rather than a Tier 3 aid.

## Element 10 — Plain-reading asides

Verdict: CONFIRM SKIP
One-line reason: The chapter is narratively and historically dense, but it does not contain the math, derivation, or stacked symbolic definition density that the spec requires for `:::tip[Plain reading]`.

The closest candidates are the Dennard-scaling paragraph and the Berkeley "Brick Wall" paragraph. Both are already written in plain prose: the former gives a qualitative recipe rather than symbolic notation, and the latter names three conceptual limits rather than deriving or defining a formal expression. A plain-reading aside after either paragraph would paraphrase rather than decode.

## Summary

0 landed. 3 skipped: Element 8 tooltip remains globally unavailable under the current component model; Element 9 pull-quote fails the adjacent-repetition/usefulness test; Element 10 plain-reading asides fail the symbolic-density gate. The author's proposal is confirmed without revival.
