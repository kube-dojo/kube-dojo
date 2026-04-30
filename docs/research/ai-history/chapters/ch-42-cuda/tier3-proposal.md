# Tier 3 Proposal — Chapter 42: CUDA

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default per READER_AIDS.md §Tier 3.

## Element 9 — Pull-quote (at most 1)

The chapter's primary sources are dense but most verbatim text is anchored at line ranges rather than quoted directly in `sources.md`. Survey of candidates:

### Candidate A — ACM Queue "democratization" framing

The 2008 ACM Queue article (Green, G18) is cited for the claim that CUDA "had tens of thousands of developers" and was framed as "a democratization of parallel programming." The chapter prose represents this at: "technical reports noted that the CUDA platform had rapidly attracted tens of thousands of developers, framing the release as a genuine democratization of parallel programming." The prose already incorporates the language closely; a pull-quote would sit immediately adjacent to its own paraphrase. The sources.md anchor (lines 115-119) does not supply a verbatim sentence distinct enough from the prose paraphrase to earn an independent pull-quote.

**Status: SKIPPED.** Prose paraphrases the claim closely; no distinct verbatim sentence available from sources.md without fetching full text.

### Candidate B — Buck retrospective on "graphics-isms" (Tom's Hardware 2009)

G4 (Tom's Hardware lines 476-478, Green) records Buck in his own words describing Brook as abstracting "graphics-isms" into general programming concepts. The `sources.md` entry for G4 paraphrases this claim rather than quoting it verbatim: "He described Brook as an attempt to systematically abstract the inherent 'graphics-isms' into general programming concepts." The chapter prose (paragraph 5 from the end of Scene 2) reproduces this same paraphrase almost word-for-word. A pull-quote would require fetching the exact sentence from Tom's Hardware lines 476-478 to confirm verbatim text that differs meaningfully from the prose.

**Working hypothesis** (Codex to verify verbatim against Tom's Hardware interview, September 3, 2009, URL: https://www.tomshardware.com/reviews/ian-buck-nvidia%2C2393.html, lines 476-478):

> "We had to basically abstract out all the graphics-isms out of the programming model and make it a general-purpose computing device."

Proposed insertion anchor: the paragraph in Scene 2 beginning "In a later retrospective interview, Ian Buck explained the pressing necessity..." — immediately after "He described Brook as an attempt to systematically abstract the inherent 'graphics-isms' into general programming concepts." The annotation should note that this is Buck's own formulation of why Brook existed, and by extension why CUDA was necessary: the problem was the metaphor, not the mathematics.

**Status: PROPOSED** (contingent on Codex verbatim confirmation). Source is Green (G4); the sentence carries independent historiographical weight as the primary-source articulation of the chapter's central abstraction argument; prose paraphrases but does not quote verbatim; the Buck framing is short and self-contained.

**Codex is asked to:** Confirm whether the working hypothesis verbatim matches lines 476-478. If the exact wording differs, return the actual sentence and APPROVE / REJECT / REVISE accordingly.

## Element 10 — Plain-reading asides (0–3 per chapter)

The chapter is primarily narrative and historical. Two passages contain stacked technical abstractions that may create comprehension gaps for readers familiar with parallel computing concepts but not with the CUDA memory model.

### Candidate C — Shared memory / on-chip cache paragraph

The paragraph beginning "To support and feed this massively parallel execution model, CUDA exposed distinct, explicit memory spaces..." (Scene 4) introduces four distinct concepts in rapid succession: local thread memory, shared memory, its physical mapping to on-chip SRAM, and global memory in board DRAM. A non-specialist reader encounters "low-latency, on-chip random-access memory" and "software-managed cache" in the same breath, without a pause to clarify why this matters relative to the alternative (going to board DRAM for every value). The paragraph is symbolically dense in the relevant sense: it stacks abstract memory-hierarchy vocabulary over a concrete performance claim (the twenty-percent gain example) without explaining the underlying physical reason for the gap.

**Status: PROPOSED.** Insertion anchor: after the paragraph beginning "To support and feed this massively parallel execution model..." (the paragraph ending "...yielded roughly a twenty percent gain simply by optimizing data access patterns"). Proposed aside:

> :::tip[Plain reading]
> The key contrast: on-chip shared memory is physically close to the arithmetic units — wires are short, access takes a handful of clock cycles. Board DRAM is physically distant — the signal has to leave the chip, travel across the PCB, and return. That round trip costs hundreds of cycles. When threads in a block all need the same values (a row of weights, a tile of input data), loading once into shared memory and reusing it many times converts hundreds of slow round trips into one. The programmer controls this explicitly; CUDA does not do it automatically.
> :::

The aside does new work relative to the surrounding prose: the following paragraph ("Yet, this computational power came with strict rules and limitations...") discusses independence restrictions, not the physical reason for the memory-speed gap. The aside explains the *why* of the shared-memory optimization, which the prose leaves implicit.

**Codex is asked to:** APPROVE / REJECT / REVISE Candidate C. In particular: does the aside duplicate explanation already present in the paragraph beginning "Shared memory made the same lesson appear inside the GPU..." (Scene 4, later)? If so, REJECT and note the anchor.

### Candidate D — Thread independence restriction paragraph

The paragraph beginning "Yet, this computational power came with strict rules and limitations..." (Scene 4) explains that blocks must be independent and that no direct communication between blocks is permitted within a kernel grid. This is important but it is stated clearly and without stacked abstractions. The reasoning ("allowed the hardware to execute blocks in any arbitrary order without risking deadlocks") is spelled out in the same sentence.

**Status: SKIPPED.** The restriction is narratively dense but not symbolically dense; the prose already supplies the reasoning without requiring a parallel track for a specialist vs. non-specialist reader.

## Summary verdict

- Element 8: SKIP (universal).
- Element 9: 1 PROPOSED (Candidate B — Buck "graphics-isms" verbatim, Tom's Hardware lines 476-478; contingent on Codex verbatim confirmation), 1 SKIPPED (Candidate A — adjacent paraphrase).
- Element 10: 1 PROPOSED (Candidate C — shared-memory on-chip/off-chip physical gap), 1 SKIPPED (Candidate D — block independence, not symbolically dense).

**Total: 2 PROPOSED, 2 SKIPPED.**
