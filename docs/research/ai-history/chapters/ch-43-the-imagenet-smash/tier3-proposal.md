# Tier 3 Proposal — Chapter 43: The ImageNet Smash

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default per READER_AIDS.md §Tier 3.

## Element 9 — Pull-quote (at most 1)

The chapter's primary sources contain several technically precise statements. Survey of candidates:

### Candidate A — Russakovsky et al. "scale" conclusion

Russakovsky et al. 2015 (Green, G21) at p.32 lines 1921-1930 conclude that "major object-recognition breakthroughs would not have been possible on a smaller scale." The chapter prose at the final section paraphrases this directly: "Russakovsky et al. conclude that major object-recognition breakthroughs would not have been possible on a smaller scale." The phrasing is verbatim-adjacent to the source; elevating it to a pull-quote would create adjacent repetition, which READER_AIDS.md §Tier 3, Element 9 identifies as a refusal case.

**Status: SKIPPED.** Prose already represents this sentence closely; a pull-quote would duplicate it without adding interpretive distance.

### Candidate B — Russakovsky et al. "turning point" / "undisputed winner"

Russakovsky et al. 2015 (Green, G09) at p.17 lines 1134-1140 call ILSVRC2012 a turning point and SuperVision the "undisputed winner." The sources.md Green claim table flags "undisputed" as source wording and advises paraphrasing. The chapter prose does paraphrase ("Russakovsky and her co-authors later called ILSVRC2012 a turning point for large-scale object recognition, the moment when large-scale deep neural networks entered the scene"). The underlying verbatim from Russakovsky et al. is not independently quoted; however, the full sentence from p.17 is not available in this worktree's extracted text beyond the paraphrase. Without a confirmed verbatim sentence that adds interpretive weight beyond the prose paraphrase, promoting this to a pull-quote risks introducing inaccurate attribution.

**Status: SKIPPED.** Candidate depends on a verbatim not yet confirmed at line-level precision; paraphrase is already in the prose.

### Candidate C — AlexNet paper: "network size was limited mainly by GPU memory"

AlexNet PDF (Green, G10) at p.1 lines 56-59 states that the network size was limited mainly by GPU memory and tolerable training time. The chapter prose at the "physical architecture" section includes: "The authors identified two limiting factors: GPU memory and tolerable training time." This is a direct condensation, not a verbatim lift; the paper's formulation may differ enough to carry independent force. However, in the absence of a confirmed verbatim sentence (the extracted claim is a paraphrase), the rule against promoting unverified verbatim applies.

**Status: SKIPPED.** All three candidates are either paraphrased adjacent in the prose or lack confirmed verbatim sentence extraction from the Green source. No pull-quote is proposed for this chapter.

## Element 10 — Plain-reading asides (0–3 per chapter)

The chapter is predominantly narrative. One paragraph uses an inline math expression that may cause a non-specialist comprehension gap.

### Candidate D — Top-5 error paragraph with LaTeX

The paragraph beginning "The metric also deserves more attention than the shorthand usually gives it..." includes the expression `\(N\)` in the sentence "if there were \(N\) test images, top-5 error was the fraction for which the correct class was absent from the model's five highest-scoring guesses." The `\(N\)` renders as a LaTeX variable in the built site. The surrounding text does provide the plain-English version immediately before and after this sentence, however — making the LaTeX a redundant formalism on an otherwise well-explained concept. The paragraph is not symbolically dense in the stacked-abstraction sense (no formulas, no abstract definitions requiring multi-step parsing); the `\(N\)` is a single inline variable whose meaning the surrounding prose makes explicit.

**Status: SKIPPED.** The paragraph is narratively dense (many concrete numbers and caveats) but not symbolically dense in the way READER_AIDS.md §Tier 3, Element 10 targets. The surrounding prose already supplies the plain-reading version of the `\(N\)` expression. An aside would restate what the chapter explains without compressing additional meaning.

## Summary verdict

- Element 8: SKIPPED (universal).
- Element 9: SKIPPED — all surveyed candidates (A, B, C) are either paraphrased-adjacent in the prose or lack confirmed verbatim extraction from Green primary sources.
- Element 10: SKIPPED — no paragraph is symbolically dense with stacked formulas or abstract definitions; the one inline LaTeX variable (`\(N\)`) is immediately explained by the surrounding prose.

**Total: 0 PROPOSED, 3 SKIPPED.**
