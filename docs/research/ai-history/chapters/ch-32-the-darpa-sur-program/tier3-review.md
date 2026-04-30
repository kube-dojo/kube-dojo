# Tier 3 review — Chapter 32

Reviewer: Codex (gpt-5.5, model_reasoning_effort=high), 2026-04-30, adversarial cross-family pass on PR for `claude/394-ch32-reader-aids`.

## Element 8 — Tooltip

Verdict: CONFIRM SKIP

One-line reason: `READER_AIDS.md` reserves tooltips for a future non-destructive component; adding inline HTML would modify prose, and the Tier 1 glossary already carries the definitional load.

## Element 9 — Pull-quote

Verdict: CONFIRM SKIP

One-line reason: The only quote-worthy Green-anchored sentences are already quoted verbatim in adjacent prose (Pierce via Jelinek/Church, Newell §8.6, Bahl-Jelinek-Mercer on perplexity, Mercer 1985, Jelinek 1988), so a callout would fail the adjacent-repetition gate.

## Element 10 — Plain-reading asides

Verdict: CONFIRM SKIP

One-line reason: The chapter has technical narrative about maximum-likelihood decoding, Markov models, perplexity, and Forward-Backward estimation, but no paragraph is symbolically dense in the required sense of formulas, derivations, or stacked abstract definitions; the closest IBM paragraphs already translate the ideas into plain prose.

## Summary

0 landed; 3 skipped (8 tooltip, 9 pull-quote, 10 plain-reading asides). The proposal's skips are justified: Element 8 is blocked globally by the current component constraint; Element 9 has no non-repetitive Green-primary quote worth reviving; Element 10 would turn narrative-technical prose into redundant commentary rather than a true plain-reading aid.
