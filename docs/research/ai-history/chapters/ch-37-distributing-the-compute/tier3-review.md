# Tier 3 review — Chapter 37

Reviewer: Codex (gpt-5.5, model_reasoning_effort=high), 2026-04-30, adversarial cross-family pass on PR for `claude/394-ch37-reader-aids`.

## Element 8 — Tooltip

Verdict: CONFIRM SKIP

One-line reason: READER_AIDS.md reserves Starlight tooltips for a future non-destructive component; adding any inline tooltip now would modify prose and violate the bit-identity rule.

## Element 9 — Pull-quote

Verdict: REVIVE

One-line reason: The proposal correctly rejects the thesis, INFRA-700, and backup-task candidates, but it misses a short Green primary-source sentence from the MapReduce abstract that is quote-worthy and not already quoted in the prose.

Full proposed insertion:

```markdown
:::note[Primary source]
> "Programs written in this functional style are automatically parallelized and executed on a large cluster of commodity machines."

Dean and Ghemawat's key promise was not the names Map and Reduce; it was turning distribution into a runtime guarantee.
:::
```

Green primary anchor: Jeffrey Dean and Sanjay Ghemawat, "MapReduce: Simplified Data Processing on Large Clusters," OSDI 2004, p.1 abstract. `sources.md` marks the MapReduce paper Green and cites the p.1 abstract for the programming model and runtime-handled distribution claim.

Insertion-anchor paragraph, immediately after this paragraph in `src/content/docs/ai-history/ch-37-distributing-the-compute.md`:

> On top of this storage layer sat MapReduce. If GFS was the cluster's hard drive, MapReduce was its operating system for batch data work. The 2004 paper described a programming model that reduced many massive data-processing jobs to two primitives. The "Map" function processed a key/value pair to generate a set of intermediate pairs, and the "Reduce" function merged all intermediate values associated with the same key. The programmer wrote those two functions. The runtime handled partitioning the input, scheduling execution across machines, recovering from machine failures, and managing inter-machine communication. By restricting the user-facing model, MapReduce made parallelism a property of the system rather than a custom engineering project for each application.

Adjacent-repetition test: survives. The surrounding prose paraphrases the runtime bargain, but the exact Green-source sentence is not already quoted in prose. The callout adds primary-source wording for the chapter's central systems claim, and the annotation points to the intellectual stake rather than merely restating the paragraph.

## Element 10 — Plain-reading asides

Verdict: CONFIRM SKIP

One-line reason: No paragraph is symbolically dense enough under the Tier 3 gate; the chapter is explanatory systems prose with numbers and definitions, not stacked notation, derivation, or math.

The closest candidate is the MapReduce primitives paragraph quoted above, because it defines Map, Reduce, and runtime responsibilities in one place. I still reject a Plain reading aside there: the paragraph is already written in natural language, the Tier 1 glossary already explains MapReduce, and any aside would repeat the same "map transforms records; reduce groups them; runtime handles distribution" gloss. The August 2004 production-statistics paragraph is numerically dense, but numerical density is not symbolic density under READER_AIDS.md.

Symbolic-density justification for skip: there is no formal `map(k1,v1)` / `reduce(k2, list(v2))` signature in the chapter, no equations, and no derivation. The abstract definitions that do appear are unpacked sentence by sentence, so a Plain reading callout would become filler.

## Summary

1 landed: Element 9 pull-quote, revived from the MapReduce 2004 p.1 abstract.

2 skipped: Element 8 tooltip remains globally deferred; Element 10 plain-reading asides remain inappropriate because the chapter has no genuinely symbolic dense paragraph.

Reasoning: the proposal was too strict on pull-quotes by treating "all strong candidates" as already consumed in prose; one Green primary sentence survives the exact adjacent-repetition test and reinforces the chapter's core infrastructure argument. The proposal was correct to refuse tooltips and plain-reading asides.
