# Tier 3 Proposal — Chapter 48: AlphaGo

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default per READER_AIDS.md §Tier 3.

## Element 9 — Pull-quote (at most 1)

Surveying Green primary sources in `sources.md` for candidates.

### Candidate A — Silver on Move 37 probability

David Silver told WIRED (S5, "A One in Ten Thousand Probability" section, lines 98-102 — Green, G27): AlphaGo's human-move model gave Move 37 a probability of roughly one in ten thousand, but other training made the move look promising.

The chapter prose at "Seoul And Move 37" paraphrases this closely: "AlphaGo's human-move model gave that move a probability of roughly one in ten thousand; a human expert, judged by the supervised policy trained on human games, was exceedingly unlikely to choose it."

Since the chapter already represents this claim with the verbatim-adjacent phrase "roughly one in ten thousand," elevating it to a pull-quote callout immediately after the same paragraph would produce adjacent repetition — the grounds READER_AIDS.md §Tier 3, Element 9 identifies as a refusal case.

**Status: SKIPPED.** Prose already quotes the probability framing closely; pull-quote would duplicate it.

### Candidate B — Silver et al. *Nature* abstract on the Fan Hui milestone

Silver et al. (S1, *Nature* abstract, p.484, lines 72-80 — Green) states that the Fan Hui victory had been considered at least a decade away. The chapter prose at "The Hidden Machine" uses Google's framing ("roughly a decade earlier than many predicted") and at "The Human Reply" attributes the "decade away" claim to Google's official summaries (G22). The abstract's exact wording is not quoted verbatim in the prose.

A candidate pull-quote from the abstract would be: "Here we introduce a new approach to computer Go that uses value networks to evaluate board positions and policy networks to select moves." This is technically accurate and load-bearing, but it describes the architecture rather than the chapter's defining scene; the glossary and TL;DR already cover this framing adequately in Tier 1.

**Status: SKIPPED.** No candidate sentence is genuinely quote-worthy beyond what TL;DR already conveys. The architecture description is more at home in the glossary than as a pull-quote. The milestone framing is already in the prose without exact verbatim quoting of the abstract.

### Candidate C — Lee Sedol's Game 4 win

The official Google match post (S3 — Green, G20) identifies Lee's Move 78 and AlphaGo's following Move 79 as the turning point of Game 4. This is paraphrased directly in the chapter: "Google's own post-game account singled out Lee's Move 78 and AlphaGo's following Move 79 as the turning point." The source material is in official post prose rather than a quotable sentence with independent weight; the chapter's paraphrase carries the same information.

**Status: SKIPPED.** Official post does not yield a verbatim sentence distinct enough from the prose paraphrase to justify a pull-quote.

**Element 9 summary:** 0 PROPOSED, 3 surveyed and SKIPPED. No candidate from Green primary sources clears the pull-quote bar without adjacent repetition or substitution for existing Tier 1 coverage.

## Element 10 — Plain-reading asides (0–3 per chapter)

The chapter is primarily narrative and historical. Surveying for symbolically dense paragraphs (mathematical formulas, abstract definitions stacked) versus narratively dense paragraphs (history, biography, match commentary).

### Candidate D — MCTS action-value paragraph

The paragraph at "Policy, Value, Search" beginning "Ultimately, AlphaGo wrapped these learned judgments into a sophisticated Monte Carlo tree search. During the search, AlphaGo stored action values, visit counts, and prior probabilities for possible moves..." stacks four technical concepts (action values, visit counts, prior probabilities, leaf-node evaluation combining value network and rollouts) in sequence. A non-specialist reader may struggle to hold all four simultaneously.

However, the following paragraph immediately unpacks the interaction between these components: "The procedure created a useful tension. The policy network could suggest where expert-like or self-play-hardened experience pointed. The value network could quickly judge positions..." This paragraph already does the plain-reading work an aside would do, making the mechanism accessible without introducing a callout. An aside here would restate what the next paragraph already explains — the adjacent-prose redundancy condition.

**Status: SKIPPED.** The surrounding prose resolves the density within one paragraph; an aside would duplicate rather than extend.

### Candidate E — Supervised policy accuracy sentence cluster

The paragraph describing "57.0 percent" expert-move prediction accuracy is technically precise but not symbolically dense in the relevant sense. The chapter prose immediately unpacks what 57% means: "It meant that, when shown positions from expert games, the network could often place substantial probability on the move a strong human had actually chosen." No additional aside is needed.

**Status: SKIPPED.** Prose already provides the plain-reading layer inline.

**Element 10 summary:** 0 PROPOSED, 2 surveyed and SKIPPED. No paragraph is symbolically dense in the sense READER_AIDS.md requires (mathematical formulas, derivations, abstract definitions stacked without adjacent resolution). The chapter is dense narratively and technically, but its prose resolves its own abstractions paragraph-by-paragraph.

## Summary verdict

- Element 8: SKIP (universal).
- Element 9: 0 PROPOSED — 3 candidates surveyed, all SKIPPED (adjacent repetition, TL;DR substitution, paraphrase-equivalence).
- Element 10: 0 PROPOSED — 2 candidates surveyed, both SKIPPED (adjacent prose already resolves the density).

**Total: 0 PROPOSED, 5 SKIPPED.**
