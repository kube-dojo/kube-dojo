# Tier 3 Review — Chapter 47: The Depths of Vision

Reviewer: Codex (gpt-5.5)
Date: 2026-04-30
Reviewing: tier3-proposal.md by Claude (sonnet)

## Element 9 — Pull-quote
Author verdict: SKIPPED
Reviewer verdict: REVIVE
Claude is right to reject the ResNet identity-mapping and residual-formula candidates: the chapter already paraphrases those arguments adjacent to the likely insertion points. However, AlexNet provides a Green primary-source sentence worth reviving: “All of our experiments suggest that our results can be improved simply by waiting for faster GPUs and bigger datasets to become available” (Krizhevsky et al. 2012 PDF, p. 1; verified in local `pdftotext` extraction at lines 74–77). This is not just a result row; it crystallizes the scale assumption that the ResNet chapter later complicates, and the chapter does not already repeat that sentence’s “waiting for faster GPUs and bigger datasets” phrasing adjacent to the AlexNet setup.

## Element 10 — Plain-reading aside
Author verdict: SKIPPED
Reviewer verdict: REJECT
The only genuinely symbol-heavy paragraphs are the residual mapping, residual block, and projection shortcut paragraphs, and each is immediately followed or surrounded by prose that explains the notation in plain language. A separate `:::tip[Plain reading]` would mostly restate the chapter’s existing explanation of `F(x) + x`, identity shortcuts, and `Ws x`, so it fails the non-repetition test for Element 10.

## Summary
- Approved: none
- Rejected: Element 10 plain-reading aside; ResNet pull-quote candidates A and B as adjacent repetition; AlexNet data/result framing in Candidate C as originally stated
- Revised: none
- Revived: Element 9 pull-quote from AlexNet on faster GPUs and bigger datasets
