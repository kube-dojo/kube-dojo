# Tier 3 review -- Chapter 35

Reviewer: Codex (gpt-5.5, model_reasoning_effort=high), 2026-04-30, adversarial cross-family pass on PR for `claude/394-ch35-reader-aids`.

## Element 8 -- Tooltip
Verdict: CONFIRM SKIP

One-line reason: The spec says Tier 3 tooltip support is globally deferred until a non-destructive component exists; reviving it here would violate the current reader-aid rule rather than improve the chapter.

## Element 9 -- Pull-quote
Verdict: CONFIRM PROPOSE

One-line reason: The GFS sentence is Green-primary, quote-worthy, under the cap, and not already quoted verbatim in the adjacent prose.

Green primary anchor: Ghemawat, Gobioff, and Leung, "The Google File System" (SOSP 2003), p. 1, for "component failures are the norm rather than the exception" and the commodity-hardware context.

Adjacent-repetition check: The chapter prose says "component failures were normal rather than exceptional," which is a paraphrase. The proposed pull-quote uses the primary source's exact sentence fragment and therefore does not duplicate an already-quoted prose sentence.

## Element 10 -- Plain-reading asides
Verdict: REVISE

One-line reason: The target paragraph is genuinely symbolically dense, but the proposed aside is four sentences; Tier 3 caps plain-reading asides at 1-3 sentences.

Green primary anchor: Page, Brin, Motwani, and Winograd, "The PageRank Citation Ranking: Bringing Order to the Web," Stanford InfoLab Tech Report 1999-66, p. 5 for the eigenvector formulation and random-surfer model, and p. 6 for the iterative computation `R_{i+1} <- AR_i + dE`.

Full proposed insertion:

```markdown
:::tip[Plain reading]
The math says: treat the web as a transition table where each page passes probability through its outgoing links, while a smaller jump term lets the surfer restart elsewhere. Start with provisional page scores and keep applying that table, so rank flows through links and the jump term prevents closed loops from trapping all the probability. When the scores stop changing meaningfully, that stable vector is PageRank; "eigenvector" is the mathematical name for a vector that keeps its direction under this operation.
:::
```

Insertion-anchor paragraph:

> The mathematical formulation of this idea is both dense and powerful. If `A` is the matrix representing the link-transition probabilities of the entire web, and `E` is a vector representing the random-jump destinations, then the vector of PageRanks, `R'`, is an eigenvector of the matrix `(A + E·1)`, up to a normalizing constant. In historical terms, this is the chapter's crucial turn: a question that had looked like editorial judgment became a linear-algebra calculation on a graph. Because the rank of a page depends on the ranks of the pages pointing to it, the solution cannot be calculated in a single pass. It requires a fixed-point computation. The PageRank paper gives the iterative algorithm as `R_{i+1} ← AR_i + dE`, repeated until the difference between successive rank vectors falls below a small threshold. The algorithm's power lay partly in this operational simplicity. It did not require a human editor to inspect the web; it repeatedly redistributed rank through the link graph until the distribution stopped changing meaningfully.

Symbolic-density justification: This paragraph stacks matrix notation (`A`), vector notation (`E`, `R'`), an eigenvector definition, a fixed-point computation, an iterative update formula, and a convergence threshold. That is symbolic density, not merely narrative density.

Adjacent-repetition check: The aside does not repeat a source sentence or a prose sentence verbatim. It compresses the formalism into a three-step operational gloss -- transition table, repeated application, stable vector -- which is different work from the surrounding prose's historical explanation.

## Summary

2 landed: Element 9 as proposed, and Element 10 only in the revised three-sentence form above. 1 skipped: Element 8, because tooltip support remains globally deferred by the reader-aid spec. The review rejects filler by keeping the tooltip skipped and forcing the plain-reading aside to meet the actual Tier 3 sentence cap while preserving the one genuinely useful symbolic-density aid.
