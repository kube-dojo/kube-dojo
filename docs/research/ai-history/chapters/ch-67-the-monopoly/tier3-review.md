# Chapter 67 — Tier 3 reader-aid review (Codex)

Reviewer: gpt-5.5, 2026-04-30

**Element 8: APPROVE skip.**
The Tier 3 spec explicitly says inline parenthetical definitions are skipped on every chapter until a non-destructive Tooltip component exists. See [READER_AIDS.md](/Users/krisztiankoos/projects/kubedojo/docs/research/ai-history/READER_AIDS.md:43).

**Element 9: REVIVE.**
I fetched the FTC joint statement and the OpenAI April 27, 2026 page. Candidate A is the right source, but the proposed key-input sentence would closely repeat the chapter's existing paragraph at [ch-67-the-monopoly.md](/Users/krisztiankoos/projects/kubedojo/.worktrees/ch67-reader-aids/src/content/docs/ai-history/ch-67-the-monopoly.md:128). Use this different verified sentence from the same FTC/DOJ/EC/CMA primary source instead:

```md
note[Regulators' stack vocabulary]
> "For example, platforms may have substantial market power at multiple levels related to the AI stack."

That sentence matters because it makes "platform power" vertical and layered, not a finding that one firm is a legal monopoly.

```

Insertion anchor: immediately after the paragraph beginning "The joint US/EU/UK competition statement…" at chapter line 128.

Primary source: FTC PDF, lines 47-50 region: https://www.ftc.gov/system/files/ftc_gov/pdf/ai-joint-statement.pdf
OpenAI fallback also verifies the April 27, 2026 terms, but I would not use it here; the regulator sentence does more chapter-level work than company self-description: https://openai.com/index/next-phase-of-microsoft-partnership/

**Element 10: APPROVE skip.**
Chapter 67 is narratively and institutionally dense, not symbolically dense. I found no formulas, derivations, or stacked abstract definitions that justify a `:::tip[Plain reading]` aside under the Tier 3 rule.

## Verdict summary

| Element | Verdict | Notes |
|---|---|---|
| 8 | APPROVE skip | Spec-mandated until Tooltip component lands |
| 9 | REVIVE | Different verified verbatim sentence from same FTC joint statement |
| 10 | APPROVE skip | No symbolic density |

Tier 3 yield: **1 of 3** elements land (E9 with revived sentence).
