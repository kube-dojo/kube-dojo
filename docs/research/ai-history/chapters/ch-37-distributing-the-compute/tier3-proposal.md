# Tier 3 Proposal: Chapter 37 — Distributing the Compute

Author: Claude (Sonnet 4.6)
Date: 2026-04-30

---

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — globally deferred per READER_AIDS.md spec until a non-destructive tooltip component lands. The collapsible Plain-words glossary (Tier 1, item 4) covers the same job.

---

## Element 9 — Pull-quote

**SKIPPED**

### Rationale

The chapter's most load-bearing sentences are already quoted verbatim in the prose body. Three candidates were evaluated:

1. **"The machine learning era did not have to invent its own compute substrate; it rented one that web indexing had already paid for."** — This is the chapter's thesis sentence, appearing verbatim at the end of the opening paragraph. Adding it as a pull-quote immediately following would create adjacent repetition. REJECTED on ground (b) per spec.

2. **"The Lucene PMC has voted to split part of Nutch into a new sub-project named Hadoop."** — Quoted verbatim in the prose (paragraph on INFRA-700). Already appears in-text as a block quote with full context. Adjacent pull-quote would duplicate. REJECTED on ground (b).

3. **"a sort program took 1,283 seconds without backup tasks but only 891 seconds with them, a 44 percent slowdown when the mechanism was disabled"** — This sentence is verbatim in the prose paragraph on backup tasks. REJECTED on ground (b).

No candidate sentence survives the non-verbatim test: every genuinely quote-worthy sentence from the Green primary sources (MapReduce paper, JIRA ticket, Vance 2009 NYT, Morris 2013 CNBC) has already been woven into the prose body. Introducing a pull-quote from a Green source that is *not* already in the prose would require selecting a sentence that is not load-bearing enough to warrant a callout.

**Disposition: SKIPPED. No pull-quote lands.**

---

## Element 10 — Selective dense-paragraph asides (Plain reading)

**SKIPPED**

### Rationale

The task prompt directed a specific check: does the MapReduce formal type signature `map(k1,v1) → list(k2,v2); reduce(k2, list(v2)) → list(v2)` appear in symbolically dense form in the prose?

**Finding:** It does not. The chapter introduces MapReduce in natural language: *"The 'Map' function processed a key/value pair to generate a set of intermediate pairs, and the 'Reduce' function merged all intermediate values associated with the same key."* There is no formal type-signature notation, no lambda calculus, and no stacked mathematical definitions in the prose. The chapter is narrative and descriptive throughout.

The production statistics paragraph (29,423 jobs, 3,288 TB, 158 avg workers, 1.2 worker deaths per job) is numerically dense but it is a table-of-facts narrative, not a symbolically dense paragraph in the READER_AIDS.md sense (mathematical formulas, derivations, abstract definitions stacked).

No paragraph in Ch37 qualifies as symbolically dense. A plain-reading aside anywhere in this chapter would be paraphrasing narrative prose — exactly the use case READER_AIDS.md forbids: *"not narratively dense (history, biography, who-said-what)."*

**Disposition: SKIPPED. No plain-reading asides land.**

---

## Summary

| Element | Disposition | Reason |
|---|---|---|
| 8 — Tooltip | SKIPPED | Globally deferred per spec |
| 9 — Pull-quote | SKIPPED | All strong candidates are already verbatim in prose (adjacent repetition) |
| 10 — Plain-reading asides | SKIPPED | No symbolically dense paragraphs; prose is narrative throughout; formal MapReduce type signatures are not present |

No Tier 3 elements land on Chapter 37. This is consistent with the spec's guidance that Tier 3 is the place to refuse: the chapter's load is entirely in narrative and data presentation, not in symbolic density or uniquely quotable sentences absent from the prose body.
