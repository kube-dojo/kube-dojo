# Tier 3 adversarial review — Codex (gpt-5.5)

Direct `codex exec -m gpt-5.5 -c model_reasoning_effort=high` dispatch. Task `394-ch16-tier3-codex-review`. Codex verified the Mansfield Amendment verbatim against the Congress.gov *Statutes at Large* PDF for Public Law 91-121 §203, lines 99-102.

---

## Codex's verdicts (verbatim)

> **Element 8: APPROVE-SKIP.** Universal skip per `READER_AIDS.md`.
>
> **Candidate A — Mansfield Amendment pull-quote: APPROVE.** Verified against Public Law 91-121 §203, 83 Stat. 206. The proposal's statutory sentence is verbatim correct; keep `may`, ignoring OCR noise in some transcriptions. Place immediately after the Mansfield paragraph. Annotation should emphasize the legal/rhetorical narrowing from Licklider's broad symbiosis/command-and-control vocabulary to Mansfield's "direct and apparent" test.
>
> **Candidate B — Licklider pull-quote: APPROVE-SKIP.** Licklider has quotable lines, but the cap is one and Mansfield is the better chapter hinge. A Licklider quote would pull the aid back toward vision rather than the chapter's tightening bargain.
>
> **Candidate C — IPTO budget logic plain-reading aside: APPROVE-SKIP.** Narrative/institutional, already plain-read in prose, not symbolically dense.
>
> **Candidate D — Mansfield rhetorical-shift plain-reading aside: APPROVE-SKIP.** The paragraph already explains the shift clearly; a `Plain reading` callout would duplicate it.
>
> **Missed primary-source sentence: No** Tier-3-worthy missed sentence. Licklider's "hope" framing and Project MAC's online-computing objective are plausible primary-source quote candidates, but neither beats the Mansfield statutory hinge under the one-pull-quote cap.
>
> **Final Tier 3 count:** 1 APPROVED, 3 SKIPPED.

---

## Decisions and rationale

| # | Element | Codex verdict | Action taken | Why |
|---|---|---|---|---|
| 8 | Inline tooltip | APPROVE-SKIP | **SKIP** | Universal default. |
| 9 / Cand A | Mansfield statutory text | APPROVE — verbatim verified | **APPLY** | Codex confirmed against the Congress.gov *Statutes at Large* PDF. Inserted after the Mansfield paragraph, with the annotation emphasising the legal/rhetorical narrowing. |
| 9 / Cand B | Licklider pull-quote | APPROVE-SKIP | **SKIP** | Cap is one; Mansfield serves the chapter hinge. |
| 10 / Cand C | IPTO budget logic plain-reading | APPROVE-SKIP | **SKIP** | Narrative, not symbolic. |
| 10 / Cand D | Mansfield rhetorical-shift plain-reading | APPROVE-SKIP | **SKIP** | Paragraph already plain-reads itself. |
| — | Missed candidate | None Tier-3-worthy | — | Codex confirmed nothing else clears the cap. |

---

## Final landed elements

1. `:::note[The statutory text]` pull-quote callout immediately after the Mansfield paragraph in the "## The Check Gets a Memo Line" section, with verbatim Public Law 91-121 §203 wording (Codex-verified) and an annotation framing the move as "the legal/rhetorical narrowing from Licklider's broad symbiosis-and-thinking-centres vocabulary to the 'direct and apparent' test happens in one sentence on the page."

**Tally: 1 of 4 candidates landed (1 pull-quote, 0 plain-reading asides, 0 tooltip).** Calibration consistent with Ch10–Ch15.

This closes Part 3 reader-aids work (Ch11–Ch16 all complete). The author's PROPOSED Candidate A was applied as-written; Codex verified the verbatim and confirmed the annotation framing.
