# Tier 3 Review — Chapter 42: CUDA

Reviewer: Codex (gpt-5.5)
Date: 2026-04-30
Reviewing: tier3-proposal.md by Claude (sonnet)

## Tier 2 — Architecture sketch

Verdict: REVISE [current LR sketch makes CUDA look like a linear host-to-memory pipeline and omits the explicit thread level]
Form choice: SUGGEST `flowchart TD` for CUDA's nested execution hierarchy

CUDA is hierarchical enough to warrant TD: host launches a kernel, the grid contains blocks, blocks contain threads, and memory scopes attach to those levels rather than sitting at the end of a data-flow chain. Keep the host/device boundary and SM scheduling, but make them support the abstraction instead of becoming peer pipeline stages; the commentary partly does new work on virtualization and block independence, but should be tightened around why the hierarchy scales across chips.

## Element 9 — Pull-quote

Author verdict: PROPOSED Candidate B — Buck "graphics-isms" pull-quote; SKIPPED Candidate A — ACM Queue democratization framing
Reviewer verdict: REJECT

Tom's Hardware verifies a nearby Buck sentence at lines 477-478, but the author's hypothesized quote is not verbatim. More importantly, the actual anchored sentence is already paraphrased immediately in the target paragraph ("abstract the inherent graphics-isms into general programming concepts"), so a pull-quote would create reader-experience adjacent repetition; the ACM Queue democratization sentence is likewise already paraphrased in the closing scene, so I do not revive it.

## Element 10 — Plain-reading aside

Author verdict: PROPOSED Candidate C — shared-memory/on-chip cache paragraph; SKIPPED Candidate D — thread independence restriction paragraph
Reviewer verdict: REJECT

The memory paragraph is technical, but the proposed aside exceeds the 1-3 sentence cap, adds unanchored physical-detail claims ("hundreds of cycles," PCB round trip), and duplicates the later paragraph beginning "Shared memory made the same lesson appear inside the GPU." Candidate D was correctly skipped: it is important narrative/architectural exposition, not a symbolically dense passage that needs a separate plain-reading track.

## Summary
- Approved: none
- Rejected: Element 9 pull-quote; Element 10 plain-reading aside
- Revised: Tier 2 architecture sketch
- Revived: none
- Form choice: CHANGE
