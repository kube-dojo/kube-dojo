# Tier 3 adversarial review — Codex (gpt-5)

Direct Codex review in worktree `agent-a99e009126f8f237f`. Task: adversarial review of Claude-authored Tier 3 proposal for Chapter 19, with verbatim checks against Green primary sources where feasible. Codex fetched Feigenbaum 1977 from the IJCAI PDF and Buchanan/Shortliffe Chapter 7, Chapter 31, and Chapter 36 from the Columbia MYCIN book PDFs, then extracted text with `pdftotext`. ResearchGate and ScienceDirect access to the 1983 Shortliffe interview returned HTTP 403 under `curl`, so no Shortliffe 1983 verbatim is approved here.

---

## Codex's verdicts (verbatim)

> **Element 8: APPROVE-SKIP.** Universal skip per `READER_AIDS.md`: inline tooltip machinery is not yet available without modifying prose lines.
>
> **Candidate A — Feigenbaum 1977 knowledge-is-power pull-quote: REVISE.** The proposed sentence is not verbatim in the IJCAI PDF, and its cited page range is slightly off: the closest load-bearing formulation appears on p.1016, not pp.1014-1015. The better verified sentence is: "Our agents must be knowledge-rich, even if they are methods-poor." This is Green, short enough for the pull-quote cap, not already quoted in the adjacent prose, and directly voices the chapter's hinge from general inference methods to domain knowledge.
>
> **Candidate B — Buchanan/Shortliffe Chapter 7 bottleneck definition: APPROVE-SKIP.** Chapter 7 is Green and does define knowledge acquisition, but the proposal's combined wording is not a single verbatim sentence: the PDF says knowledge acquisition is transfer and transformation "from some knowledge source to a program," then lists experts, textbooks, databases, and experience in the following sentence. Even with corrected wording, it reads as a technical definition that the surrounding prose already handles cleanly; it should not displace the Feigenbaum maxim under the one-pull-quote cap.
>
> **Candidate C — Shortliffe 1983 non-deployment statement: APPROVE-SKIP.** I could not verify a Shortliffe 1983 verbatim sentence from the Green source within reasonable effort because both the ResearchGate URL in `sources.md` and the ScienceDirect page blocked `curl` with HTTP 403. The skip is still correct: the chapter's non-deployment paragraph deliberately spreads responsibility across knowledge-base incompleteness, research-machine constraints, consultation time, cost, workflow, collaborator loss, and legal ambiguity. A single Shortliffe interview sentence would either over-isolate one cause or become too qualified to work as a pull quote.
>
> **Candidate D — certainty-factor plain-reading aside: APPROVE-SKIP.** This paragraph is conceptually technical but not symbolically dense in the `READER_AIDS.md` sense. It uses ordinary prose, no formulas, no derivation, and no stacked formal definitions. A `Plain reading` aside would restate the paragraph's own plain-language explanation.
>
> **Candidate E — backward-chaining plain-reading aside: APPROVE-SKIP.** This is a mechanism paragraph, but not a symbolic-density paragraph. The prose already explains backward chaining as working backward from a goal and asking only relevant questions; an aside would duplicate it.
>
> **Candidate F — knowledge-acquisition bottleneck plain-reading aside: APPROVE-SKIP.** The paragraph is narrative and labor-process dense, not mathematical or symbolic. It already translates the bottleneck into everyday examples of physicians, rules, exceptions, and testing failures.
>
> **Missed primary-source sentence: No Ch31 sentence beats the revised Feigenbaum pull quote.** Chapter 31 contains quotable evaluation sentences, including the higher-rating result and the small-case limitation, but using either as the chapter's one pull quote would pull attention toward "MYCIN beat doctors" framing or toward study-method caveats already well handled in prose. Chapter 36 has a clean non-deployment sentence about intended ward testing never being undertaken, but it likewise serves a later corrective paragraph rather than the chapter's central knowledge-engineering hinge. Do not add a second pull quote.
>
> **Final Tier 3 count:** 1 APPROVED via revision, 6 SKIPPED.

---

## Decisions and rationale

| # | Element | Codex verdict | Action taken | Why |
|---|---|---|---|---|
| 8 | Inline tooltip | APPROVE-SKIP | **SKIP** | Universal default until a non-destructive tooltip component exists. |
| 9 / Cand A | Feigenbaum knowledge-is-power pull-quote | REVISE | **APPLY REVISED** | The proposed wording is not in the PDF. The verified p.1016 sentence "Our agents must be knowledge-rich, even if they are methods-poor." is Green, compact, and not adjacent repetition. |
| 9 / Cand B | Buchanan/Shortliffe bottleneck definition | APPROVE-SKIP | **SKIP** | The proposal's wording blends two sentences; the corrected definition is useful but technical and already paraphrased well in prose. |
| 9 / Cand C | Shortliffe 1983 non-deployment statement | APPROVE-SKIP | **SKIP** | Could not verify verbatim through blocked sources, and a single interview sentence would flatten the multi-cause non-deployment account. |
| 10 / Cand D | Certainty-factor plain-reading aside | APPROVE-SKIP | **SKIP** | Technical but not symbolically dense; the paragraph already plain-reads itself. |
| 10 / Cand E | Backward-chaining plain-reading aside | APPROVE-SKIP | **SKIP** | Mechanism prose, not mathematical/symbolic density; an aside would repeat the explanation. |
| 10 / Cand F | Knowledge-acquisition bottleneck plain-reading aside | APPROVE-SKIP | **SKIP** | Narrative labor-process explanation, not symbolic density. |
| — | Missed candidate | None to land | — | Ch31 and Ch36 have quotable lines, but none beats the revised Feigenbaum sentence under the one-pull-quote cap. |

---

## Final landed elements

1. `:::note[Feigenbaum's maxim]` pull-quote callout immediately after the paragraph in the "## After General Methods" section anchored by this unique sentence:

   > If the knowledge was the source of power, then the acquisition of knowledge became the central problem.

   Exact text to insert:

   ```markdown
   :::note[Feigenbaum's maxim]
   > "Our agents must be knowledge-rich, even if they are methods-poor."

   Feigenbaum made this the expert-system era's organizing maxim in 1977: power would come from specialist knowledge, while reusable inference methods stayed secondary.
   :::
   ```

**Tally: 1 APPROVED, 6 SKIPPED of 7 total candidates.** The one approved element requires the revised Feigenbaum wording above; no plain-reading asides should land.
