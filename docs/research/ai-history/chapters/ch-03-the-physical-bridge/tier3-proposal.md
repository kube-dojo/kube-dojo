# Tier 3 proposal — Chapter 3: The Physical Bridge

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family adversarial).

## Element 1 — Pull-quote (`:::note`, ≤1 per chapter)

**Status: SKIPPED**

Rationale: Rule (b) — every quote-worthy sentence is already in-prose:

- Owens's "in fact, a software problem" — already quoted (the §1 paragraph that pivots from the analyzer's mechanical setup to "needed an automatic-control theory").
- Shannon's hindrance definition (`"The symbol 0 (zero) will be used to represent the hinderance of a closed circuit"`) — already quoted in the postulates paragraph.
- Shannon's negation definition (`"If X is the hindrance of the make contacts of a relay, then X' is the hindrance of the break contacts of the same relay"`) — already quoted in the negation paragraph.
- Shannon's Boole identification (`"The algebra of logic ... originated by George Boole, is a symbolic method of investigating logical relationships"`) — already quoted.
- Shannon's "first satisfying one requirement and then making additions until all are satisfied" / "any expression formed with the operations of addition, multiplication, and negation represents explicitly a circuit containing only series and parallel connections" / "to manipulate the expression into the form in which the least number of letters appear" — all already quoted.
- Shannon's "probably the most economical circuit of any sort" — already quoted in the dual-network paragraph.
- Yamada's "the first paper on switching theory in the World" describing Nakashima — already quoted in the Nakashima introduction paragraph.
- Howard Gardner's "possibly the most important, and also the most famous, master's thesis of the century" — NOT in our prose body, but per `brief.md` and `timeline.md` the specific Gardner page anchor is Yellow (only WebFetch-confirmed Wikipedia phrasing). Promoting an unanchored secondary attribution to a pull-quote violates source discipline. SKIP.

Pull-quote: SKIP per (b) and source discipline. Same outcome as Ch01 and Ch02 prototypes.

## Element 2 — Plain-reading aside after the theorem-17b simplification paragraph

**Status: PROPOSED**

Anchor: end of the paragraph that runs the Figure 5 → Figure 6 reduction — the paragraph beginning "He provided a worked example to prove this methodology." This paragraph is symbolically dense — it carries the original 13-element hindrance expression, the post-reduction 5-element simplified form, and a *named theorem* (`17b`) without explaining what the theorem does algebraically.

The prose says:

> Through repeated application of theorem 17b—a rewriting rule that absorbed nested expressions of a single variable—and the distributive law, the function reduced to `Xab = W + X + Y + ZS'V`.

This sentence states *that* theorem 17b absorbs nested expressions, but does not spell out the algebra. A reader unfamiliar with Boolean simplification cannot at this point check the reduction; the paragraph then immediately corrects a popular folk-memory ("five relays to three") without giving the reader the tool needed to verify the actual claim.

Insertion: immediately after the paragraph ending "…the number of contacts and switch-blade elements dropped from thirteen to five."

Draft:
```
:::tip[Plain reading]
Theorem 17b is the absorption law: in Shannon's algebra, $X + XY = X$. A variable in series with anything its own product is just the variable. Apply it together with the distributive law $X(Y+Z) = XY + XZ$, and the original 13-contact expression collapses term by term until only `W + X + Y + ZS'V` remains. The simplification is mechanical — every step is the rewriting of one algebraic equality, no insight required.
:::
```

Rationale: The aside names the algebraic content of theorem 17b ($X + XY = X$, the absorption law) and points at the engine driving the reduction. The surrounding prose states the *result* but not the *rule*. Three sentences; within the 1-3 sentence cap.

The candidate paragraph qualifies as symbolically dense (named theorem applied to a 13-term expression, no algebraic explanation of the theorem given). It is *not* narratively dense — there is no who-said-what to summarise.

## Element 3 — Inline parenthetical definition (Starlight tooltip)

**Status: SKIPPED**

Rationale: READER_AIDS.md item 8 — universal SKIP across every chapter until a non-destructive tooltip component lands. Ch03 has several specialist terms (hindrance, postulate, perfect induction, make/break contact, calculus of propositions, symmetric function) that would be tooltip candidates; the Plain-words glossary covers them non-destructively.

## Selective dense-paragraph asides — additional candidates considered and rejected

- **The hindrance-convention paragraph** ("The hindrance convention is worth pausing on…"). REJECTED — the paragraph IS already a Tier-3-shaped plain-reading aside, written into the prose body. Adding a callout would be a third pass through the same explanation.
- **The dual-network simplification paragraph** ("He demonstrated even further reductions in his Section V *Selective Circuit* example…"). REJECTED — the prose already explains in plain language that "a transformation that exchanged series with parallel and break-contacts with make-contacts" is what duality means. A callout would duplicate.
- **The Boole-identification paragraph** ("Most importantly, Shannon explicitly identified his calculus with George Boole's work…"). REJECTED — narratively dense (citation chain Huntington 1904 → Boole 1854 → Shannon 1937), not symbolically dense. Plain-reading callouts are reserved for symbolic density per READER_AIDS.md item 10.
- **The Nakashima parallel-discovery paragraph** ("Nakashima developed his algebra initially without using symbolic notation…"). REJECTED — narratively dense (notation correspondence between Nakashima and Shannon, romanisation variants, kanji renderings), not symbolically dense.

## Summary table (for the reviewer)

| # | Element | Status | Approve? Reject? Revise? |
|---|---|---|---|
| 1 | Pull-quote | SKIPPED (rule b + source discipline) | reviewer: agree / disagree |
| 2 | Plain-reading after theorem-17b simplification paragraph | PROPOSED | reviewer: APPROVE / REJECT / REVISE |
| 3 | Inline parenthetical | SKIPPED (universal) | reviewer: agree / disagree |

Calibration: Ch01 prototype landed 2 of 5; Ch02 landed 0 of 4; Ch03 proposes 1 outright. Single-candidate proposals are appropriate when the prose carries inline plain-reading work — as Ch03's hindrance-convention and dual-network paragraphs already do.
