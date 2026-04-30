# Tier 3 Review — Chapter 50: Attention Is All You Need

Reviewer: Codex (gpt-5.5)
Date: 2026-04-30
Reviewing: tier3-proposal.md by Claude (claude-opus-4-7)

## Element 8 — Inline parenthetical definition
Author verdict: SKIPPED — Tooltip component is not available; `<abbr>` would modify prose and violate bit-identity.
Reviewer verdict: APPROVE
I approve the skip. The spec makes Element 8 skipped on every chapter until a non-destructive tooltip component exists (`READER_AIDS.md` line 43), and the proposal follows that rule directly at `tier3-proposal.md` line 11.

## Element 9 — Pull-quote
Author verdict: PROPOSED — Vaswani et al. 2017 abstract sentence after the rhetoric paragraph, with annotation contrasting the sober architectural claim against the title.
Reviewer verdict: REVISE
The sentence is quote-worthy and sourced: `sources.md` line 13 identifies the abstract as Green evidence for the attention-only/no-recurrence claim, and the prose at lines 178-180 paraphrases nearby abstract material without verbatim repeating this sentence. Revise the annotation, though, because the proposed note at `tier3-proposal.md` line 26 repeats the adjacent prose's "narrower than the title" point from chapter line 178 instead of doing new work.

Use this exact quoted sentence:

> We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.

New annotation: This abstract sentence is the paper's own mission statement before the later tables and experiments make the engineering case: remove recurrence and convolution, then prove the attention-only stack can compete on translation.

Primary anchor: Vaswani et al. 2017, abstract, p. 1.

## Element 10 — Plain-reading aside
Author verdict: SKIPPED — No symbolically dense prose paragraphs; math sidebar carries the notation.
Reviewer verdict: APPROVE
I approve the skip. Element 10 is only for formulas, derivations, or stacked abstract definitions (`READER_AIDS.md` line 47), while the prose explanation of query-key-value attention, scaling, heads, and positional encodings at chapter lines 140-158 is deliberately natural-language; the symbolic load appears in the Tier 2 math sidebar at lines 59-70.

## Summary
- Approved: Element 8 skip; Element 10 skip
- Rejected: None
- Revised: Element 9 pull-quote annotation
- Revived: None
