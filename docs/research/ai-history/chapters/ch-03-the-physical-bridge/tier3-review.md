# Tier 3 review - Chapter 3: The Physical Bridge

Reviewer: Codex (cross-family adversarial)

## Element 1 - Pull-quote (`:::note`, <=1 per chapter)

**Verdict: AGREE**

The skip is correct. The strongest candidate quotations are already quoted in the prose body, so a pull-quote would create adjacent repetition under `READER_AIDS.md` rule 9(b). The Gardner line should also stay out: the proposal correctly treats the page anchor as insufficiently firm for a promoted pull-quote.

## Element 2 - Plain-reading aside after the theorem-17b simplification paragraph

**Verdict: REJECT**

The candidate does identify a real gap: the prose names theorem 17b as an absorption-style rewriting rule, but it does not state the algebraic form `$X + XY = X$`. That part would do new work for a reader trying to understand the reduction.

However, the submitted draft is four sentences, not three, so it violates the Tier 3 1-3 sentence cap. The second sentence is also awkward ("anything its own product"), and the final "no insight required" line overstates the point by turning a mechanical rewrite method into a claim about the intellectual content of the simplification. Under the review instruction to reject candidates that exceed the cap, this should not land as drafted.

If the author resubmits, a cap-compliant version would be:

```markdown
:::tip[Plain reading]
Theorem 17b is the absorption law: in Shannon's algebra, $X + XY = X$, meaning that a variable already present in a branch absorbs a product that includes the same variable. Used with the distributive law `$X(Y+Z) = XY + XZ`, it lets the 13-contact expression collapse by equality-preserving rewrites until only `W + X + Y + ZS'V` remains.
:::
```

## Element 3 - Inline parenthetical definition (Starlight tooltip)

**Verdict: AGREE**

The skip is correct. `READER_AIDS.md` item 8 reserves inline parenthetical definitions for a future non-destructive tooltip component, and adding them now would violate the rule that aids do not edit prose lines. The Tier 1 glossary is the right current mechanism.

## Selective dense-paragraph asides - additional candidates considered and rejected

**Verdict: AGREE**

The rejected alternatives are correctly classified. The hindrance and dual-network paragraphs already do their plain-reading work in prose; the Boole-identification and Nakashima paragraphs are narratively dense rather than symbolically dense. Adding callouts there would duplicate or broaden Tier 3 beyond its stated purpose.

## Summary table

| # | Element | Proposal status | Review verdict |
|---|---|---|---|
| 1 | Pull-quote | SKIPPED | AGREE |
| 2 | Plain-reading after theorem-17b simplification paragraph | PROPOSED | REJECT |
| 3 | Inline parenthetical | SKIPPED | AGREE |
