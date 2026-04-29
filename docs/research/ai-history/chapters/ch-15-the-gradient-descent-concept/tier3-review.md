# Tier 3 adversarial review — Codex (gpt-5.5)

Direct `codex exec -m gpt-5.5 -c model_reasoning_effort=high` dispatch. Task `394-ch15-tier3-codex-review`. Codex downloaded the `WidrowHoff60` Stanford PDF, ran local OCR (`ocrmypdf` + `tesseract`) because the PDF had no text layer, and verified the Candidate A verbatim against the resulting plain text.

---

## Codex's verdicts (verbatim)

> **Element 9 / Candidate A: REVISE, then APPROVE.** The Widrow-Hoff wording is verified against the Stanford PDF, but the proposal's page anchor should be corrected from p. 98 to printed p. 99. Use the proposal's two-sentence quote unchanged. Insert immediately after the current paragraph beginning "They did not invent the gradient method…" in `src/content/docs/ai-history/ch-15-the-gradient-descent-concept.md:117`. Annotation should say the point is not later reconstruction: the 1960 paper names the search method in its own optimization vocabulary. Source checked: Stanford PDF, printed p. 99: https://isl.stanford.edu/~widrow/papers/c1960adaptiveswitching.pdf
>
> **Element 10 / Candidate E: APPROVE-SKIP.** Correct. The Cauchy two-variant paragraph is symbolically dense, but the Tier 2 math sidebar already states the line-search expression and stationarity condition, and the prose immediately explains the historical distinction.
>
> **Element 10 / Candidate F: APPROVE-SKIP.** Correct. The `1/17` and `τ = n + 1` material is already translated twice: once in the math sidebar and again in the following prose about learning having a measurable pace.
>
> **Element 10 / Candidate G: APPROVE-SKIP, but revise the rationale.** The skip is right, but not because the Tier 2 math sidebar substantially covers Linnainmaa. It is because the paragraph already plain-reads itself: forward pass, backward pass, cost explosion if repeated per parameter, and one backward sweep at similar order of work. It is abstract, not symbolically dense enough for Element 10.
>
> **Missed primary-source sentence:** Yes, one fallback candidate: Widrow-Hoff p. 97's sentence defining the feedback-control error signal as the gradient of mean-square error with respect to adjustment. It is primary, paraphrased but not fully quoted in prose, and thesis-bearing. Still, do **not** displace Candidate A: the p. 99 steepest-descent sentence better serves Ch15's Cauchy-to-Adaline hinge. Treat the p. 97 sentence as surveyed-and-skipped fallback under the one-quote cap.
>
> **Final tally:** Element 8 SKIP. Element 9 land 1 revised pull-quote. Element 10 land 0 plain-reading asides.

---

## Decisions and rationale

| # | Element | Codex verdict | Action taken | Why |
|---|---|---|---|---|
| 8 | Inline tooltip | APPROVE-SKIP | **SKIP** | Universal default. |
| 9 / Cand A | Pull-quote — Widrow-Hoff steepest-descent | REVISE then APPROVE — verbatim correct, page anchor corrected | **APPLY** | Codex OCR'd the Stanford PDF (no native text layer) and confirmed the two-sentence quote ("the method of searching that has proven most useful is the method of steepest descent. Vector adjustment changes are made in the direction of the gradient"). Page anchor 98 → 99. Insertion at the line 117 anchor Codex specified. The annotation Codex requested ("the point is not later reconstruction: the 1960 paper names the search method in its own optimization vocabulary") is what landed. |
| 10 / Cand E | Plain-reading: Cauchy two variants | APPROVE-SKIP | **SKIP** | Tier 2 math sidebar already restates the line-search expression and stationarity condition. |
| 10 / Cand F | Plain-reading: time-constant | APPROVE-SKIP | **SKIP** | Math sidebar + prose already cover. |
| 10 / Cand G | Plain-reading: Linnainmaa linear cost | APPROVE-SKIP — rationale corrected | **SKIP** | Codex's correction: not because the math sidebar covers Linnainmaa (it doesn't, much), but because the paragraph plain-reads itself. The "abstract, not symbolically dense" framing is the right one. Note this rationale-fix in the chapter's audit log. |
| — | Missed candidate (Widrow-Hoff p. 97) | Surveyed and skipped | **DECLINED** | Cap is one. The p. 99 steepest-descent sentence Codex landed serves Ch15's Cauchy-to-Adaline hinge better. The p. 97 gradient-of-MSE sentence is a fallback. |

---

## Final landed elements

1. `:::note[Widrow-Hoff name the method]` pull-quote callout immediately after the "They did not invent the gradient method…" paragraph (line 117 in the post-Tier-1 file), with verbatim two-sentence quote (Codex OCR-verified from `WidrowHoff60` p. 99) and Codex's tighter annotation framing the move as 1960's-own-vocabulary, not later reconstruction.

**Tally: 1 of 7 candidates landed (1 pull-quote, 0 plain-reading asides, 0 tooltip).** Calibration consistent with Ch10–Ch14 (1/5–1/7 each).

The author's PROPOSED Candidate A was verified and applied with a corrected page anchor. The author's rationale for SKIP-G ("Tier 2 sidebar covers Linnainmaa") was wrong — Codex corrected it on the merits while keeping the SKIP. Source-fidelity through OCR of an image-only PDF is exactly the kind of verification the cross-family review delivers when primary sources are not in plain text.
