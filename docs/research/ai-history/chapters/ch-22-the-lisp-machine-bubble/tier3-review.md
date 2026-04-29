# Tier 3 adversarial review - Codex (gpt-5)

Direct cross-family adversarial review requested by the user for Chapter 22. Author of the Tier 1 reader-aids and Tier 3 proposal was Claude (sonnet, headless agent). Codex verified the live verbatim claim by fetching the Green primary PDF from Bitsavers (`AIM-444.pdf`), extracting page images, running OCR with `tesseract`, and checking the proposed wording against the extracted page text. `pdftotext` alone produced only form feeds for the scanned Bitsavers PDFs, so page-image OCR was required.

---

## Codex's verdicts (verbatim)

> **Element 8: APPROVE-SKIP.** Universal skip per `READER_AIDS.md`: inline parenthetical definitions are reserved for a future tooltip component and must not modify prose lines.
>
> **Candidate A - Symbolics 3600 product-claim pull-quote: APPROVE-SKIP.** The Symbolics 3600 Technical Summary is Green for product specifications and vendor self-description, but this candidate is still vendor pitch. OCR verified the relevant product framing: "The Symbolics 3600 is a 36-bit single-user computer designed for high-productivity software development and for the execution of large symbolic programs," followed by the supermini/dedicated-workstation claim; the networking section likewise frames users as realizing "the best of two worlds" through timesharing benefits and single-user station advantages. The chapter already paraphrases those claims while labeling them as a pitch. Elevating one to the only pull-quote would give marketing voice too much interpretive weight.
>
> **Candidate B - AIM-444 address-space forecast: REVISE.** The Green primary source supports the idea, but the proposal's working quote is not verbatim. AIM-444 page 3 reads: "Future programs are likely to be quite a bit bigger; intelligent systems with natural language front ends may well be five or ten times the size of a PDP-10 address space." The chapter paraphrases this sentence but does not quote it verbatim, so there is no adjacent-repetition violation. Use this exact sentence, not the proposal's compressed wording.
>
> **Candidate C - tagged architecture plain-reading aside: APPROVE-SKIP.** The paragraph is technical but not symbolically dense under `READER_AIDS.md`. It has no formulas, derivations, or stacked abstract definitions; it already explains tags in ordinary language.
>
> **Candidate D - writable microcode plain-reading aside: APPROVE-SKIP.** This paragraph is also plain prose, not symbolic density. The surrounding sentences already do the reader-aid work by explaining that writable microcode kept the Lisp runtime close to the processor while leaving room to evolve.
>
> **Candidate E - Common Lisp portability exclusions plain-reading aside: APPROVE-SKIP.** The paragraph is an enumeration of features excluded or set aside for portability. A feature list can be dense, but it is not mathematical or symbolic density, and an aside would mostly repeat the paragraph.
>
> **Missed primary-source sentence: Yes, but do not land it under the one-pull-quote cap.** AIM-444 also contains a strong Green sentence in the personal-computing rationale: "It puts service to the user entirely ahead of efficiency considerations." That is paraphrased in the chapter and is quote-worthy. It does not displace Candidate B because the proposal's approved pull-quote is the sharper technical hinge for the Time-Sharing Wall section and directly explains the 24-bit virtual-address-space answer.
>
> **Source-fidelity check:** No Yellow-source verbatim claim should land. The only landed pull-quote should use AIM-444, a Green primary source.

---

## Decisions and rationale

| # | Element | Codex verdict | Action taken | Why |
|---|---|---|---|---|
| 8 | Inline tooltip | APPROVE-SKIP | **SKIP** | Universal default in `READER_AIDS.md`; no tooltip component exists that preserves prose bit-identity. |
| 9 / Cand A | Symbolics 3600 vendor product claim | APPROVE-SKIP | **SKIP** | Green for self-description, but still vendor marketing; chapter already paraphrases and contextualizes it as a pitch. |
| 9 / Cand B | AIM-444 address-space forecast | REVISE | **APPLY WITH REVISED VERBATIM TEXT** | The claim verifies against AIM-444 page 3, but the proposal's wording is not exact. No adjacent repetition in the surrounding prose. |
| 10 / Cand C | Tagged architecture plain-reading aside | APPROVE-SKIP | **SKIP** | Narratively technical, not symbolically dense; the paragraph already plain-reads itself. |
| 10 / Cand D | Writable microcode plain-reading aside | APPROVE-SKIP | **SKIP** | No formulas, derivations, or definition stack; surrounding prose is already accessible. |
| 10 / Cand E | Common Lisp exclusions plain-reading aside | APPROVE-SKIP | **SKIP** | Dense enumeration, not symbolic density; an aside would duplicate the prose. |
| - | Missed candidate | Do not land | **SKIP** | AIM-444's "service to the user" sentence is quote-worthy, but the cap is one and Candidate B is the stronger technical hinge. |

---

## Final landed elements

1. `:::note[The address-space forecast]` pull-quote callout immediately after the paragraph in the "## The Time-Sharing Wall" section ending with this unique anchor sentence:

   "The problem was that the hardware and operating assumptions around it were becoming too small."

   Exact text to insert:

   ```markdown
   :::note[The address-space forecast]
   > "Future programs are likely to be quite a bit bigger; intelligent systems with natural language front ends may well be five or ten times the size of a PDP-10 address space."

   In 1977, the Lisp Machine Group framed a dedicated 24-bit virtual address space as an engineering answer to this pressure.
   :::
   ```

**Tally: 1 APPROVED, 5 SKIPPED of 6 total candidates.** The one approval is conditional on the revised AIM-444 wording above; no plain-reading asides should land.
