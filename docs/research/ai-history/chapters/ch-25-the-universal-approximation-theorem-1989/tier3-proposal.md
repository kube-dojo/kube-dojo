# Tier 3 Proposal — Chapter 25: The Universal Approximation Theorem

Author: Claude (Sonnet 4.6). Awaiting adversarial review by Codex before any element lands in prose.

---

## Element 1 — Pull-quote

**Status: PROPOSED**

**Candidate sentence:**

> "That was narrower than the myth and more important than the myth. The theorem did not make neural networks practical. It made them worth continuing to make practical."

**Verbatim source attribution:** Ch25 prose, "Existence, Not Recipe" section, paragraph 4 (lines immediately following the four-sentence "The cluster of results around 1989..." paragraph).

**Insertion anchor:** Immediately after the paragraph ending "…multilayer networks were not merely heuristic gadgets. Under real assumptions, they had representational power." — i.e., after the 1989-cluster summary paragraph and before the explicit "That was narrower than the myth" sentence.

**Rationale:** This two-sentence passage does the intellectual work of the entire chapter in the most compressed form available in the prose. It names the actual historical claim (legitimacy, not practicality), names the historiographical correction (the myth), and draws the correct causal arrow. It is also structurally self-contained: a reader who read only this block would understand the chapter's thesis. The sentence is not currently displayed as a blockquote in the prose — it appears as ordinary running text — so a pull-quote would not create adjacent repetition.

**Risk:** The prose immediately precedes "That was narrower than the myth and more important than the myth." If the pull-quote is placed after the paragraph that introduces it, the reader sees the sentence twice in close proximity (once as ordinary prose, once as the callout). Reviewer should evaluate whether the repetition is adjacent enough to violate the "refuse if prose paragraph already quotes the sentence verbatim" rule. The sentence is not quoted in the paragraph above; it is the paragraph's closing line. Proposer assessment: acceptable because the callout is pedagogically distinct (it frames the thesis, not just restates it), but this is the strongest objection and should be weighed carefully.

---

## Element 2 — Selective dense-paragraph aside (Plain reading)

**Status: PROPOSED**

**Target paragraph:** The paragraph in "Existence, Not Recipe" that begins "The words around that claim carry much of the discipline. Continuous functions are not arbitrary functions. Compact domains are not the whole uncontrolled world. Sigmoidal units are not every possible activation. 'There exists' is not 'we know how to find.' 'Finite' is not 'small.' Approximation is not exact symbolic reasoning. Uniform approximation is a particular mathematical demand, not a general certificate of intelligence."

**Proposed aside text:**

:::tip[Plain reading]
This paragraph strips five assumptions from the theorem's headline. Each sentence is a one-line check: the result covers *continuous* functions (not arbitrary ones), on *compact* domains (not the whole real world), using *sigmoidal* units (one specific activation family), and says only that some suitable network *exists* — not that anyone can find it, or that it will be small enough to build.
:::

**Insertion anchor:** Immediately after the paragraph ending "…not a general certificate of intelligence." in the "Existence, Not Recipe" section.

**Rationale:** This paragraph is symbolically dense in the relevant sense: it stacks five paired distinctions (continuous/arbitrary, compact/whole world, sigmoidal/every activation, exists/find, finite/small, approximation/symbolic, uniform/general) in rapid succession. A reader who is not already fluent in approximation theory needs to slow down and reprocess each pair independently. The aside does new work by numbering and summarising the five qualifications as a checklist, which the prose does not do explicitly.

**Risk:** The paragraph is clear in natural-language terms — it uses no mathematical notation and no jargon that the Tier 1 glossary does not cover. A reviewer may judge it narratively dense rather than symbolically dense, in which case the aside should be refused. Proposer assessment: borderline. The density is conceptual (stacked logical negations, paired distinctions) rather than notational. Worth review.

---

## Element 3 — Selective dense-paragraph aside (Plain reading)

**Status: PROPOSED**

**Target paragraph:** The paragraph beginning "Barron's work helps sharpen the issue. Once one asks how approximation error falls as units are added, the slogan becomes a cost question..." through "...how efficiently, under what assumptions, and with what training procedure?"

**Proposed aside text:**

:::tip[Plain reading]
Barron's result reframes the theorem as an engineering question: not just "can a network approximate this?" but "how many units does it take, and how fast does error fall as you add more?" A family can be universal and still be impractical if error falls only slowly — you need too many units to get close enough.
:::

**Insertion anchor:** Immediately after the paragraph ending "…'how efficiently, under what assumptions, and with what training procedure?'" in "The Cost of Being Universal."

**Rationale:** This passage introduces Barron's rate-of-convergence framing, which is the move from an existence claim to an efficiency claim. The conceptual step (existence → rate → cost) requires readers to hold two distinct mathematical ideas in parallel. The aside makes that logical step explicit by naming the reframe.

**Risk:** Similar to Element 2 — the paragraph is not mathematically notated, so reviewers may judge it narratively rather than symbolically dense. Proposer leans toward keeping it because the cost-vs-existence distinction is the chapter's most practically important point and the prose moves through it quickly.

---

## Element 4 — Inline parenthetical definition (Starlight tooltip)

**Status: SKIPPED**

**Reason:** Skipped on every chapter per READER_AIDS.md §Tier 3 item 8. No non-destructive tooltip component exists in the Starlight build; using `<abbr>` modifies the prose line and violates the bit-identity rule.

---

## Summary table

| Element | Type | Status | Key risk for reviewer |
|---|---|---|---|
| "That was narrower than the myth..." | Pull-quote | PROPOSED | Potential adjacent repetition — sentence appears as prose immediately after the callout insertion point |
| "The words around that claim carry much of the discipline..." | Plain reading aside | PROPOSED | May be conceptually dense rather than symbolically dense; reviewer call |
| "Barron's work helps sharpen the issue..." | Plain reading aside | PROPOSED | Same density-type question; reviewer call |
| Inline tooltip | Tooltip | SKIPPED | Component does not exist; destructive to prose |
