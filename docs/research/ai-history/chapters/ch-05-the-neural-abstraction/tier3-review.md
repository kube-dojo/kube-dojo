# Tier 3 review — Chapter 5: The Neural Abstraction

Reviewer: Codex (cross-family adversarial). Scope: `tier3-proposal.md`, `READER_AIDS.md`, Chapter 5 prose, and the Chapter 5 brief.

## Element 1 — Pull-quote (`:::note`, ≤1 per chapter)

**Verdict: AGREE WITH SKIP**

The skipped status is correct. The strongest candidates are either already quoted in the prose or would repeat claims the prose already carries at the right point. Adding a pull-quote here would create emphasis without new interpretive work, which fails `READER_AIDS.md` item 9.

## Element 2 — Plain-reading aside on the propositional-logic equivalence theorem paragraph

**Verdict: REJECT**

This is the right candidate to scrutinize, but it does not clear the Tier 3 bar. The surrounding prose already does the demonstration work: immediately before the theorem paragraph, the chapter states that conjunction, disjunction, and negation are enough to mechanize propositional calculus; that any well-formed formula can be parsed into a tree; that it can be assembled gate by gate into a net without circles; and that the resulting net fires exactly when the formula's truth conditions are met. That is already a plain-reading explanation of the construction, not just an abstract theorem statement.

The proposed formula, $(A \lor B) \land \lnot C$, is fair as a textbook example, but it is too close to the just-explained AND/OR/NOT paragraph to add new work. It combines exactly the three gates already introduced, in exactly the way the following paragraph already describes. The draft is within the 1-3 sentence cap, but cap compliance is not enough when the aside mainly restates the existing construction prose.

There is also a semantic concern: "an inhibitory afferent that fires when $C$ does" preserves the McCulloch-Pitts veto idea better than a generic NOT gate would, but calling every connective a "gate" risks flattening negation back into logic-gate vocabulary. The chapter's existing sentence is sharper: "Logical NOT was achieved through the fourth physical assumption: an absolute inhibitory connection." No worked example is needed unless it adds detail beyond the prose, and this one does not.

## Element 3 — Inline parenthetical definition (Starlight tooltip)

**Verdict: AGREE WITH SKIP**

Correct per `READER_AIDS.md` item 8. Until a non-destructive tooltip component exists, inline parentheticals would modify prose lines and violate the bit-identity rule. The Tier 1 glossary is the proper place for this aid.

## Selective dense-paragraph asides — additional candidates considered and rejected

**Verdict: AGREE WITH REJECTIONS**

The listed rejected candidates are correctly refused. In each case, the prose already supplies the plain-reading sentence or paragraph immediately adjacent to the dense material. Chapter 5 is unusually self-explanatory in its logic-construction sequence; forcing an extra Tier 3 callout would make the aid feel like a duplicate rather than a reader aid.

## Summary table

| # | Element | Proposal status | Review verdict |
|---|---|---|---|
| 1 | Pull-quote | SKIPPED | AGREE WITH SKIP |
| 2 | Plain-reading after the propositional-logic equivalence theorem paragraph | PROPOSED | REJECT |
| 3 | Inline parenthetical | SKIPPED | AGREE WITH SKIP |

Final result: land no Tier 3 elements for Chapter 5. The chapter's logic-construction prose already demonstrates the formula-to-net move clearly enough, so the worked example should not be added.
