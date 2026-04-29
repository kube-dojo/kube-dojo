# Tier 3 proposal — Chapter 4: The Statistical Roots

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family adversarial).

Note: Ch04 is a **Tier 2 math chapter** (math sidebar applied) per `READER_AIDS.md` item 6. The Tier 2 sidebar absorbs the chapter's mathematical content (two-state chain definition, independence test $\delta = p_1 - p_0$, Markov's *Onegin* counts, the second-order chain, the dispersion coefficient as model fit). This shapes the Tier 3 analysis below.

## Element 1 — Pull-quote (`:::note`, ≤1 per chapter)

**Status: SKIPPED**

Rationale: Rule (b). Every quote-worthy sentence is already in-prose:

- Markov's "an abuse of mathematics" — already quoted (Nekrasov characterisation paragraph).
- Markov's "I am concerned only with questions of pure analysis…. I refer to the question of the applicability of probability theory with indifference" — already quoted (the 1906–1912 series paragraph).
- Markov's "stupidly stitched" — already quoted (the 1921 footwear paragraph).
- Hayes's "must have spent several days on these labors" — already quoted (the labor estimate paragraph).
- Link's "in those six years, Markov could not think of a practical illustration" — already quoted (the 1906–1912 series paragraph).
- Link's "a paper-automaton" / "a writing game with discrete characters" — already quoted (the table-method paragraph).
- Yamada-on-Nakashima quote — irrelevant; that's Ch03 material.
- Hayes's free-will paraphrase — already quoted in the Nekrasov-argument paragraph.

There are no quote-worthy candidate sentences that are not already in-prose. SKIP per (b), consistent with Ch01–Ch03 prototypes.

## Element 2 — Plain-reading aside on a dense paragraph

**Status: SKIPPED**

Rationale: The chapter's prose systematically plain-reads each symbolically dense paragraph in its own body, and the Tier 2 math sidebar absorbs the rest of the formal content. Specific candidates considered and rejected:

- **The block-variance paragraph** ("The arithmetic mean number of vowels per hundred-letter block was 43.19…"). REJECTED — the prose closes with its own plain-reading: "Independence, in other words, was not contradicted at the block level — a long sample averages out, regardless of the dependence within. The dependence would have to be looked for at the level of pairs." A callout would duplicate.
- **The first-order transition paragraph** ("Returning to the unbroken stream of letters, Markov counted the pair patterns…"). REJECTED — the prose closes with its own plain-reading: "Under independence, p1 and p0 would coincide; the larger the absolute gap, the deeper the dependence between successive letters. Half a unit was a substantial separation." A callout would duplicate.
- **The second-order triple paragraph** ("Markov did not stop at first-order dependence…"). REJECTED — the prose explicitly says "After two vowels in a row, the probability of a third vowel collapsed to 0.104 — lower than the unconditional rate of 0.432 by a factor of more than four, and lower even than p1, the probability of a vowel after a single vowel." That IS the plain-reading; another callout would triple-cover.
- **The dispersion-coefficient paragraph** ("When these figures were plugged into a two-step chain, the theoretical dispersion coefficient came to 0.195…"). REJECTED — the dispersion coefficient is fully covered in the new Tier 2 math sidebar, including the model-fit interpretation. A Tier 3 callout would duplicate the Tier 2 entry.
- **The transformer-vs-Markov-property close** ("The autoregressive language models…"). REJECTED — narratively dense, not symbolically dense. The whole paragraph IS already a Tier-3-shaped aside on the modern-vs-Markov distinction, written into the prose body.

`READER_AIDS.md` item 10 explicitly permits refusal: "Refuse on chapters where no paragraph is genuinely dense, and refuse the *individual* aside if its commentary would only repeat the surrounding prose." Both refusal grounds apply across every candidate in Ch04.

## Element 3 — Inline parenthetical definition (Starlight tooltip)

**Status: SKIPPED**

Rationale: `READER_AIDS.md` item 8 — universal SKIP across every chapter until a non-destructive tooltip component lands. Ch04 has many specialist terms (Weak Law of Large Numbers, transition probability, dispersion coefficient, n-gram, Markoff process, ω-consistency); the Plain-words glossary (Tier 1, item 4) and the new math sidebar (Tier 2, item 6) cover them non-destructively.

## Summary table (for the reviewer)

| # | Element | Status | Approve? Reject? Revise? |
|---|---|---|---|
| 1 | Pull-quote | SKIPPED (rule b) | reviewer: agree / disagree |
| 2 | Plain-reading aside | SKIPPED (no symbolically-dense paragraph that the prose doesn't already plain-read; Tier 2 sidebar absorbs the formal math) | reviewer: agree / disagree (or counter-propose) |
| 3 | Inline parenthetical | SKIPPED (universal) | reviewer: agree / disagree |

Calibration vs prior chapters:
- Ch01 prototype: 2/5 candidates landed (math-heavy, less inline plain-reading)
- Ch02: 0/4 candidates landed
- Ch03: 1/3 candidates landed (theorem-17b absorption-law revise)
- Ch04 proposes: 0/3 candidates outright

If the reviewer sees a paragraph the author missed, please counter-propose with anchor + draft. Otherwise the workflow ratifies the all-SKIP outcome — which is consistent with `READER_AIDS.md` item 10's explicit permission to refuse on chapters where the prose carries inline plain-reading work.
