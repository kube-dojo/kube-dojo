# Tier 3 review — Chapter 33

Reviewer: Codex (gpt-5.5, model_reasoning_effort=high), 2026-04-30, adversarial cross-family pass on PR for `claude/394-ch33-reader-aids`.

## Element 8 — Tooltip
Verdict: CONFIRM SKIP
One-line reason: READER_AIDS.md globally skips tooltips until a non-destructive Starlight component exists, and the Tier 1 glossary already covers the needed vocabulary.

## Element 9 — Pull-quote
Verdict: REVIVE
One-line reason: The proposal incorrectly treats Campbell's Newborn p.151 sentence as already quoted verbatim; the chapter paraphrases it, so one short Green-anchored pull-quote can add provenance without adjacent repetition.

Green primary anchor: Newborn 2003 p.151, Green in `sources.md` claim #16, quoting Murray Campbell's retrospective interpretation of how Kasparov's team read the Game 1 bug.

Candidate insertion anchor, immediately after this paragraph:

> Campbell later offered a cautious interpretation of what followed. Kasparov's team, trying to understand why the machine had made so poor a move, examined alternatives and found that they also lost. From that, Campbell believed, they may have inferred that Deep Blue had searched thirty or forty plies ahead, seen that all roads lost, and therefore played any move at all. That was not what had happened. The move was not a resigned insight into the future; it was a fail-safe. Still, the misunderstanding mattered because it changed the atmosphere around the machine. A random move from a bug could be mistaken for a glimpse of impossible depth.

Proposed insertion:

```markdown
:::note[Campbell's caution]
> "They were overestimating Deep Blue's talents here."

Campbell's sentence is evidence for IBM's interpretation of the misreading, not proof of Kasparov's private psychology.
:::
```

Adjacent-repetition test: the chapter already explains the idea, but it does not quote this sentence verbatim; the callout adds source provenance and the epistemic limit of Campbell's claim.

## Element 10 — Plain-reading asides
Verdict: CONFIRM SKIP
One-line reason: The chip and search paragraphs are technical but not symbolically dense; they contain no formulas, derivations, or stacked abstract definitions that need a separate plain-reading paraphrase.

## Summary
1 landed (Element 9 pull-quote), 2 skipped (Element 8 tooltip; Element 10 plain-reading asides). The revived pull-quote is narrow because it corrects the proposal's adjacent-repetition premise; the other Tier 3 skips remain correct under the spec.
