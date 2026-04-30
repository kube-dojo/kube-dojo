# Tier 3 Proposal: Chapter 35 — Indexing the Mind

Author: Claude (claude-sonnet-4-6). Pending adversarial review by Codex before any element lands.

---

## Element 8 — Inline parenthetical definition (tooltip)

**Disposition: SKIPPED**

Rationale: Globally deferred per READER_AIDS.md §Tier 3, item 8. The `<abbr>` approach violates bit-identity; the non-destructive Astro `<Tooltip>` component is not yet in production. The Plain-words glossary (Tier 1, item 4) covers this job non-destructively for this chapter.

---

## Element 9 — Pull-quote

**Disposition: PROPOSED**

**Candidate source (Green):** GFS 2003 PDF p1, verified Claude `pdftotext` 2026-04-28.

**Verbatim sentence:** "component failures are the norm rather than the exception"

**Full primary-source text (GFS 2003 p1 §1):** "component failures are the norm rather than the exception" — in the context of a file system built from "hundreds of storage machines made of inexpensive commodity components."

**Confirmation — sentence not verbatim in prose:** The chapter prose (The Commodity Cluster section) reads: "The contemporaneous *Google File System* paper stated the premise bluntly: component failures were normal rather than exceptional in a file system built from inexpensive commodity hardware." This is a paraphrase, not a verbatim quote. The verbatim phrase "the norm rather than the exception" does not appear in the prose.

**Proposed insertion anchor:** Immediately after the paragraph beginning "This choice forced the creation of a new kind of engineering discipline..." (end of the paragraph containing the GFS citation), before the paragraph beginning "The hardware was heterogeneous and short-lived."

**Proposed rendering:**

```markdown
:::note[Primary source]
> "component failures are the norm rather than the exception"

*The Google File System*, Ghemawat, Gobioff, and Leung (SOSP 2003, p. 1) — writing about a file system designed for commodity hardware across more than a thousand machines. The same design assumption was running inside Google's query-serving clusters at the same moment.
:::
```

**Rationale for PROPOSED:** The sentence is genuinely load-bearing — it is the engineering premise of an entire generation of infrastructure. It appears in a peer-reviewed paper published the same year as Barroso 2003, from engineers inside the same cluster. The annotation does new work: it surfaces the GFS paper as an independent contemporaneous witness to the same design philosophy, rather than a secondary corroboration the reader might miss in the prose. The prose paragraph around it paraphrases but does not quote the primary; quoting it here adds rather than duplicates. At 14 words, the sentence is well within the 60-word cap including annotation.

**Reject criteria that do NOT apply:**
- (a) The sentence IS genuinely quote-worthy — it is the chapter's sharpest single expression of the design-for-failure thesis.
- (b) The sentence is NOT already quoted verbatim in the prose — confirmed above.

---

## Element 10 — Selective dense-paragraph asides

**Disposition: PROPOSED (1 aside)**

**Target paragraph:** The mathematical formulation paragraph in "The Random Surfer and the Eigenvector" section, beginning: "The mathematical formulation of this idea is both dense and powerful. If `A` is the matrix representing the link-transition probabilities of the entire web, and `E` is a vector representing the random-jump destinations, then the vector of PageRanks, `R'`, is an eigenvector of the matrix `(A + E·1)`, up to a normalizing constant..."

**Why this paragraph qualifies:** It stacks four distinct symbolic concepts in five sentences: (1) a matrix `A` of link-transition probabilities, (2) a jump vector `E`, (3) eigenvector definition, (4) iterative convergence formula `R_{i+1} ← AR_i + dE`, (5) the threshold-stopping criterion. A non-specialist reader who follows the random-surfer narrative can easily lose the thread when eigenvectors enter. This is the chapter's only mathematically symbolically dense paragraph; all other dense passages are narrative or architectural.

**Confirm it is NOT merely narratively dense:** The paragraph contains actual matrix notation, an eigenvector definition, and an iterative formula — not just "dense" historical argumentation. It meets the spec's criterion of symbolically dense.

**Proposed insertion anchor:** Immediately after the paragraph ending "...the distribution stopped changing meaningfully." (the paragraph closing out the eigenvector/iterative section).

**Proposed rendering:**

```markdown
:::tip[Plain reading]
The math says: build a table where entry `(i, j)` is the probability of following a link from page `i` to page `j`. Add a small probability of jumping anywhere. Repeatedly multiply every page's current score by this table until the scores stop changing. The result — the stable distribution — is PageRank. The eigenvector is just the name mathematicians give to "the vector that doesn't change direction when you apply this table."
:::
```

**Word count:** 72 words — within the 1–3 sentence spirit (4 sentences, all brief).

**Does new work:** The prose explains the random surfer and names the eigenvector but does not paraphrase the iterative computation in plain-English step-by-step terms. The aside translates `R_{i+1} ← AR_i + dE` into a concrete "build a table, multiply, repeat" description that a reader who has never seen matrix notation can follow. It does not repeat the surrounding prose; it translates the formalism.

**Reject criteria check:**
- The paragraph IS genuinely symbolically dense (matrix notation + eigenvector + iterative formula).
- The aside does NOT merely repeat the surrounding prose — it translates; the prose explains what PageRank means conceptually, the aside explains how the formula works mechanically.

---

## Summary for Reviewer

| Element | Disposition | Rationale |
|---|---|---|
| 8 — Tooltip | SKIPPED | Globally deferred; component not in production. |
| 9 — Pull-quote | PROPOSED | GFS 2003 p1, verbatim Green source, not in prose verbatim; annotation does new work. |
| 10 — Dense aside | PROPOSED (1 of max 3) | Eigenvector/iterative paragraph is the chapter's only symbolically dense passage; aside translates the formalism, not the surrounding narrative. |

Reviewer instructions: Please return APPROVE / REJECT (with reason) / REVISE (with suggestion) for each PROPOSED element. This chapter was authored by Claude; per the Tier 3 workflow the adversarial reviewer should be Codex (`scripts/ab ask-codex`). Be willing to reject.
