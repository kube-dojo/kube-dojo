# Tier 3 Proposal — Chapter 49: The Custom Silicon

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default per READER_AIDS.md §Tier 3.

## Element 9 — Pull-quote (at most 1)

The chapter's primary sources contain several technically crisp statements. Survey of candidates from Green sources in sources.md:

### Candidate A — The "double the datacenter" projection

The TPU paper (P1, p.2) states that serving voice search with DNN speech recognition via conventional CPUs "would have required us to double our datacenters." The chapter prose at paragraphs 4–5 renders this claim extensively and directly ("would require the company to double its entire datacenter capacity"). The sentence is already the load-bearing opener of the narrative; elevating it as a pull-quote would create adjacent repetition — the grounds READER_AIDS.md §Tier 3, Element 9 identifies as a refusal case.

**Status: SKIPPED.** Prose already presents this claim as the central scene opener; pull-quote would duplicate it immediately adjacent.

### Candidate B — MLP0 latency constraint from Table 4

The TPU paper (P1, p.8, Table 4) specifies that the MLP0 benchmark had "a strict limit of 7.0 ms" as its 99th-percentile response time. The chapter prose at "The ultimate validation..." section quotes "7 milliseconds" and "225,000 inferences per second" but does not lift the constraint framing as a verbatim sentence. A pull-quote version could read:

> "The 99th-percentile response time had to remain under 7.0 ms — operating against that ceiling, the TPU delivered 225,000 inferences per second."

However, this composite is a paraphrase assembled from the chapter's own prose rather than a verbatim sentence from the primary source. The paper's Table 4 presents numbers in tabular form; the prose sentences in the chapter already fully represent the claim. Elevating this as a pull-quote would not bring a distinct primary-source voice — it would re-present the chapter's own expository language as a quotation.

**Status: SKIPPED.** No primary-source sentence is verbatim-quotable here; the table data is already fully represented in prose, and a paraphrase pull-quote risks false attribution.

### Candidate C — Hennessy and Patterson on domain-specific architecture

The CACM 2019 paper (S1, "Example DSA TPU v1") frames TPU v1 as demonstrating that domain-specific hardware can "improve performance by more than an order of magnitude while dramatically reducing energy usage." The chapter's final paragraphs paraphrase this framing closely ("tenfold improvement," "30 to 80 times higher" performance per watt). The secondary source sentence, even if quoted verbatim, would arrive after the chapter has already built the same argument with primary-source numbers. The pull-quote would summarize what the chapter has already demonstrated rather than doing new historiographical work.

**Status: SKIPPED.** The CACM framing is a secondary synthesis of what the primary paper already shows; a pull-quote at the close would restate rather than illuminate.

**Summary for Element 9:** All three candidates skipped. No sentence from the Green primary sources is (a) verbatim-quotable, (b) not already represented adjacent in the prose, and (c) doing historiographical work the prose does not. Element 9 does not land in Ch49.

## Element 10 — Plain-reading asides (0–3 per chapter)

The chapter is primarily economic and engineering narrative. Two sections contain technical content that might benefit from a plain-reading aside.

### Candidate D — Systolic execution paragraph

The paragraph beginning "Feeding a calculation engine of this size presented a severe memory-bandwidth challenge..." through the paragraph beginning "The name 'systolic' evokes a pulse..." uses the phrase "diagonal wavefronts," describes data and weights flowing "in coordinated, diagonal wavefronts," and invokes a pulse metaphor. This is moderately abstract, but the chapter's own next paragraph immediately unpacks it ("Values move from one cell to the next, and each cell performs its multiply-add at the right moment as the wave passes through"). The chapter provides its own plain reading in the following sentence sequence without assistance.

**Status: SKIPPED.** The chapter prose does the unpacking work internally; an aside would restate what the immediately following paragraph already provides.

### Candidate E — MIP/CISC instruction-set paragraph

The paragraph beginning "Because the TPU was designed solely to execute these dense matrix operations, its instruction set could be stripped down to the bare essentials..." introduces CISC-style instructions and names the operations (Read/Write host memory, Read weights, MatrixMultiply/Convolve, Activate). This is a specialist term (CISC), but the paragraph immediately follows with a plain explanation of why the narrow instruction set was sufficient. No symbolically dense formula or layered abstraction is present — the paragraph is narratively dense (who-decided-what), not symbolically dense.

**Status: SKIPPED.** Not symbolically dense; READER_AIDS.md §Tier 3, Element 10 restricts asides to symbolically dense paragraphs (mathematical formulas, derivations, abstract definitions stacked). This paragraph does not qualify.

## Summary verdict

- Element 8: SKIP (universal).
- Element 9: 3 candidates surveyed, all 3 SKIPPED (adjacent repetition / no verbatim sentence doing new work).
- Element 10: 2 candidates surveyed, both SKIPPED (prose self-unpacks; not symbolically dense).

**Total: 0 PROPOSED, 5 SKIPPED.** No Tier 3 elements land in Ch49.
