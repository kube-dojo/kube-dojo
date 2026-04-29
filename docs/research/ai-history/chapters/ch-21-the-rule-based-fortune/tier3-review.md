# Tier 3 adversarial review — Codex (gpt-5)

Direct user dispatch in worktree `/Users/krisztiankoos/projects/kubedojo/.claude/worktrees/agent-a3d6c9b3ff9d50034`. Task: cross-family adversarial review of Claude-authored Tier 3 proposal for AI History Chapter 21, with no chapter-prose edits. Codex verified the Green-source pull-quote candidates by fetching the primary PDFs, running `pdftotext` where available, and OCRing the scanned McDermott 1982 pages with `pdftoppm` plus `tesseract`.

---

## Codex's verdicts (verbatim)

> **Element 8: APPROVE-SKIP.** Universal skip per `READER_AIDS.md`; tooltip-style inline definitions are not currently allowed because they would modify prose lines.
>
> **Candidate A — McDermott 1982 ad hoc constraints: APPROVE-SKIP.** The Green source supports the idea, but the proposal's wording is not the exact sentence. OCR of McDermott 1982 p.42 verifies: "many of the constraints in this subtask have a strongly ad hoc flavor; they are not easily derivable from more general knowledge..." The chapter's "Knowledge As Constraints" paragraph already plain-reads this claim in adjacent prose ("Many had an ad hoc flavor. They were not easy to derive..."). A pull quote would repeat work the prose already performs.
>
> **Candidate B — Bachant/McDermott 1984 never-finished system: APPROVE-SKIP.** The source registry marks `R1 Revisited` Yellow because the available copy is mirror-sourced. Under `READER_AIDS.md` source discipline, Yellow sources cannot support verbatim quotation. The maintenance burden is also already central in the "Four Years In The Trenches" prose, so the skip is correct.
>
> **Candidate C — McDermott/Steele 1981 deployment reach: REJECT.** The primary IJCAI PDF is Green and verifies the load-bearing phrase, but the proposed block quote is not verbatim. `pdftotext -raw` verifies the wording as: "Since January, 1980, R1 has been used by Digital Equipment Corporation's manufacturing organization to configure almost all VAX 11 systems shipped..." The proposal shortens that to "Since January 1980" and "DEC manufacturing" and adds a hyphen in `VAX-11`. Even if corrected, the surrounding chapter paragraph already says that McDermott and Steele wrote R1 was "being used by DEC manufacturing to configure almost all VAX-11 systems shipped"; landing a note immediately after it would create adjacent repetition.
>
> **Candidate D — recognize-act cycle plain-reading aside: APPROVE-SKIP.** This paragraph is conceptually introductory, not symbolically dense. It contains no formulas, derivations, formal notation, or stacked abstractions that require a Tier 3 plain-reading aid.
>
> **Candidate E — OPS5 / Match paragraph plain-reading aside: APPROVE-SKIP.** The paragraph is architecture prose, not mathematical or symbolic exposition. It already says in plain language that R1 used domain structure rather than blind search.
>
> **Candidate F — rule splitting and context structure plain-reading aside: REJECT.** McDermott 1982 p.69 supports the terms, with OCR verifying "rule splitting" and "context spawning," but the chapter passage is not symbolically dense under the Tier 3 standard. It is narrative-technical prose about maintenance/refinement, and the next paragraph already explains the human loop of expert inspection and rule revision. A `Plain reading` callout would broaden the rule beyond its mathematical/symbolic-density purpose.
>
> **Missed primary-source sentence: No Tier-3-worthy missed sentence.** Green sources contain quotable lines, especially McDermott/Steele's "R1 does almost no backtracking..." and Smith's "developers should avoid a demonstration mentality," but the chapter already paraphrases those claims clearly in the immediately relevant sections. Pulling either into a callout would add provenance at the cost of repeating the surrounding prose rather than doing new reader-aid work.
>
> **Final Tier 3 count:** 0 APPROVED, 6 SKIPPED.

---

## Decisions and rationale

| # | Element | Codex verdict | Action taken | Why |
|---|---|---|---|---|
| 8 | Inline tooltip | APPROVE-SKIP | **SKIP** | Universal default; current tooltip mechanism would alter prose. |
| 9 / Cand A | McDermott 1982 ad hoc constraints | APPROVE-SKIP | **SKIP** | Green source supports the claim, but the chapter already plain-reads it in adjacent prose; no new work for a pull quote. |
| 9 / Cand B | Bachant/McDermott 1984 never-finished system | APPROVE-SKIP | **SKIP** | Yellow source cannot support verbatim quotation; maintenance claim is already in prose. |
| 9 / Cand C | McDermott/Steele 1981 deployment reach | REJECT | **SKIP** | Verified Green source wording differs from the proposed quote, and the same "almost all VAX-11 systems shipped" claim is already in the surrounding paragraph. |
| 10 / Cand D | Recognize-act cycle plain-reading | APPROVE-SKIP | **SKIP** | Not symbolically dense; already clear prose. |
| 10 / Cand E | OPS5 / Match plain-reading | APPROVE-SKIP | **SKIP** | Architecture/narrative density, not mathematical or symbolic density. |
| 10 / Cand F | Rule splitting/context structure plain-reading | REJECT | **SKIP** | Terms are source-backed, but the passage lacks symbolic density and the following paragraph already explains the concept. |
| — | Missed candidate | None Tier-3-worthy | — | Green-source paraphrases worth quoting are already doing their work in prose; no pull quote beats the repetition risk. |

---

## Final landed elements

None. No Tier 3 element should land in the chapter prose.

No insertion text and no paragraph anchor apply. The closest proposed anchor, the paragraph beginning "After validation, the system began producing configuration descriptions before assembly," should remain unchanged because Candidate C would repeat its central sentence.

**Tally: 0 APPROVED, 6 SKIPPED of 6 total candidates.**
