# Tier 3 Review — Chapter 57: The Alignment Problem

Reviewer: Codex (gpt-5.5)
Date: 2026-04-30
Reviewing: tier3-proposal.md by Claude (claude-opus-4-7)

## Element 8 — Inline parenthetical definition
Author verdict: SKIPPED — Tooltip component is not available; `<abbr>` would modify prose and violate bit-identity.
Reviewer verdict: APPROVE
I approve the skip. The spec keeps Element 8 skipped until a non-destructive tooltip component exists, and the Tier 1 glossary already defines the chapter's key terms without altering verified prose.

## Element 9 — Pull-quote
Author verdict: PROPOSED — Ouyang et al. 2022 Section 5.2 representativeness caveat after the paragraph beginning "The phrase "alignment" can become too large too quickly."
Reviewer verdict: REVISE
The pull-quote should land, but not with the proposed wording. I verified the InstructGPT paper text (arXiv:2203.02155, Section 5.2, "Who are we aligning to?"); the proposed sentence does not appear there verbatim. The closest useful move is to use a complete, verified sentence from the same section that states the same limitation without inventing wording.

Use this complete quoted sentence:

> We are not claiming that researchers, the labelers we hired, or our API customers are the right source of preferences.

New annotation: This keeps RLHF's reference group explicit: practical alignment was not a universal-values settlement.

Primary anchor: Ouyang et al. 2022, Section 5.2, "Who are we aligning to?"

Do not use the originally proposed sentence. I prefer the Section 5.2 sentence above over the nearby Section 5.3 "representative" limitation because the proposal's insertion anchor is about narrowing the alignment claim, not about the later methodology limitations paragraph.

## Element 10 — Plain-reading aside
Author verdict: SKIPPED — No symbolic density.
Reviewer verdict: APPROVE
I approve the skip. The chapter is conceptually dense, but its RLHF, reward-model, labeler-labor, and product-deployment explanations are written in ordinary prose. There are no formulas, derivations, or stacked symbolic definitions that would justify a `:::tip[Plain reading]` aside.

## Summary
- Approved: Element 8 skip; Element 10 skip
- Rejected: None
- Revised: Element 9 pull-quote sentence and annotation
- Revived: None
