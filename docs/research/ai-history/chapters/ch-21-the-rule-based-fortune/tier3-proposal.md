# Tier 3 Proposal — Chapter 21: The Rule-Based Fortune

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default per READER_AIDS.md §Tier 3.

## Element 9 — Pull-quote (at most 1)

The chapter is narratively dense (factory scene, production-system mechanics, deployment arc) and quotes scare-quote fragments throughout. Candidates surveyed:

### Candidate A — McDermott 1982 on ad hoc constraints

McDermott's 1982 *Artificial Intelligence* paper (p.42) contains the sentence that many configuration constraints "had an ad hoc flavor and were not easily derived from general knowledge." The chapter paraphrases this near-verbatim in the "Knowledge As Constraints" section ("Many had an ad hoc flavor. They were not easy to derive from clean physical laws or a compact mathematical model."). The load-bearing claim is already quoted in-prose.

**Status: SKIPPED.** Rule (b) applies: the candidate sentence is already paraphrased so closely in the surrounding prose that a callout would create adjacent repetition without doing new work.

### Candidate B — Bachant/McDermott 1984 on the never-finished system

The 1984 "R1 Revisited" paper's conclusion — that the authors expected R1 might eventually enter maintenance mode but by 1984 found it hard to believe R1 would ever be done — is the chapter's load-bearing maintenance claim. However:

1. The Bachant/McDermott source is Yellow (mirror-sourced; see `sources.md`); verbatim quotation of a Yellow-status source is not safe at this anchor-fidelity level.
2. The gist is already fully paraphrased in the "Four Years In The Trenches" section.

**Status: SKIPPED.** Yellow source status prevents confident verbatim; prose already covers the claim.

### Candidate C — McDermott/Steele 1981 on deployment reach

McDermott and Steele (1981, p.824) state that since January 1980 R1 had been used by DEC manufacturing to configure "almost all VAX-11 systems shipped." The phrase "almost all VAX-11 systems shipped" is a genuine primary-source sentence, Green-status, and carries the deployment-scale claim the chapter needs. The chapter currently paraphrases it in the "Into Manufacturing" section.

**Status: PROPOSED.** The phrase is genuinely quotable (scope + scale in five words), its Green status supports verbatim treatment, and a callout can do new annotation work — specifically, naming the paper's publication date and IJCAI context, then noting that "almost all" rather than "all" reflects the honest production-use claim the chapter upholds. This does not duplicate the surrounding prose; the callout adds provenance and the rhetorical significance of "almost."

Proposed callout (insertion after the paragraph starting "McDermott and Steele wrote in 1981"):

```markdown
:::note[Primary source]
> "Since January 1980, R1 has been used by DEC manufacturing to configure
> almost all VAX-11 systems shipped."
>
> — McDermott and Steele, *Extending a Knowledge-Based System to Deal with
> Ad Hoc Constraints*, IJCAI 1981, p.824

The word "almost" is load-bearing. It is not false modesty: McDermott and
Steele wrote before R1 had been extended to the VAX-11/750 (March 1981)
or later system families. The claim is precise rather than absolute, which
is exactly the discipline the chapter argues for.
:::
```

Cap check: 54 words including annotation — within the 60-word cap.

## Element 10 — Plain-reading asides (0–3)

Ch21 is narrative throughout. Symbolically dense paragraphs surveyed:

### Candidate D — Recognize-act cycle paragraph ("Rules That Recognize" section)

The paragraph explaining the recognize-act cycle ("The system maintained a working memory … This is the recognize-act rhythm.") is the chapter's most technically abstract passage. However, the prose itself is already written at plain-reading level — no symbolic notation, no stacked definitions, no mathematical formulas. The next paragraph immediately explains why the drama is not the cycle's mystery. An aside would only repeat the surrounding prose.

**Status: SKIPPED.** Not symbolically dense; prose already does the plain-reading work.

### Candidate E — OPS5 / Match paragraph ("Rules That Recognize" section)

The paragraph on Match ("R1 did not wander through a huge abstract search space … rules to recognize meaningful situations") is conceptually dense but not symbolically dense. No formulas or formal notation appear.

**Status: SKIPPED.** Narratively dense (strategy/architecture), not symbolically dense. The Tier 3 criterion requires symbolic density.

### Candidate F — Rule splitting and context structure ("Rules That Recognize" section)

The sentence "McDermott emphasized that rule splitting and context structure helped confine many changes to related parts of the knowledge base" is the most technically loaded phrasing in the chapter, but it is not accompanied by any notation or formalism. A one-sentence aside ("Rule splitting: when a rule is too general, split it into two rules covering narrower conditions. Context structure: group rules by the subtask they belong to so changes in one context rarely affect another.") could be useful.

**Status: PROPOSED (conditional).** If Codex agrees the passage would benefit from plain-reading — given that "rule splitting" and "context structure" are unexplained technical terms — a short aside is justified. If Codex judges the surrounding prose sufficient (the chapter's glossary defines "production system" and "recognize-act cycle"), SKIP.

Proposed callout (insertion after the paragraph ending "A modular rule base could be taught."):

```markdown
:::tip[Plain reading]
Rule splitting: when one rule's condition is too broad and fires in wrong
situations, replace it with two narrower rules, each covering only the
appropriate cases. Context structure: R1 organized rules by active subtask,
so splitting a rule in one subtask rarely broke rules in other subtasks.
Together, these made the knowledge base teachable rather than fragile.
:::
```

## Summary verdict

- Element 8: SKIP.
- Element 9: 1 PROPOSED (Candidate C — McDermott/Steele 1981 deployment claim), 2 SKIPPED.
- Element 10: 1 PROPOSED conditional (Candidate F — rule splitting/context structure), 2 SKIPPED.

**Total: 2 PROPOSED, 4 SKIPPED.**

## Author asks Codex to:

1. Verify Candidate C's verbatim wording ("almost all VAX-11 systems shipped") against McDermott and Steele, IJCAI 1981, p.824. APPROVE / REJECT / REVISE. If the exact phrasing differs, supply the correct verbatim and REVISE the callout.
2. Evaluate Candidate F (rule-splitting aside): does "rule splitting" and "context structure" in the "Rules That Recognize" section constitute symbolic density under READER_AIDS.md §Tier 3 Element 10 criteria, or is the surrounding prose already sufficient? APPROVE / REJECT.
3. Confirm or reject the SKIPs on Candidates A, B, D, and E — specifically whether any paraphrased primary-source sentence in the chapter is quote-worthy and not yet covered by the proposed Candidate C callout.
