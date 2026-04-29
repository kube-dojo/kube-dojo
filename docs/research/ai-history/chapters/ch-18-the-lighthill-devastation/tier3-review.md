# Tier 3 adversarial review — Codex

Direct user dispatch in `agent-ac8eb2d1d1c5f081e` worktree. Task: cross-family adversarial review of Claude-authored Tier 3 proposal for Chapter 18, with verbatim verification against Green primary sources and no modification to chapter prose.

Codex fetched `https://www.aiai.ed.ac.uk/events/lighthill1973/lighthill.pdf`, ran `pdftotext`, and checked the relevant passages against the Green Chilton HTML text for Lighthill Part I.

---

## Codex's verdicts (verbatim)

> **Element 8: APPROVE-SKIP.** Universal skip per `READER_AIDS.md`; tooltips remain unavailable without modifying prose lines.
>
> **Candidate A — Lighthill combinatorial-explosion pull-quote: REVISE.** The proposed sentence is not verbatim in the Green AIAI PDF or Chilton Part I HTML. The verified Part I p.8 wording frames the cause as "failure to recognise the implications of the combinatorial explosion," not the proposal's constructed sentence. However, the same Green source contains a stronger, shorter Lighthill sentence in the Winograd/postscript passage that the chapter paraphrases but does not quote. It should replace the proposed wording and move the anchor to the Winograd paragraph, where it does direct source-work without adjacent repetition.
>
> **Candidate B — BBC *Controversy* debate verbatim: APPROVE-SKIP.** The AIAI page is Yellow in this contract and confirms event metadata only. No debate line should be quoted until the 81-minute broadcast is watched and logged from a primary source.
>
> **Candidate C — Existing in-prose callout: APPROVE-SKIP.** The existing `Pedagogical Insight: The Bridge Was the Target` callout is not an adjacent verbatim repetition of the revised Lighthill quote. It does, however, already covers the introductory structural role, so it should not become a second pull-quote candidate. The revised quote belongs later, inside the combinatorial-explosion section, under the one-pull-quote cap.
>
> **Candidate D — ABC classification plain-reading aside: APPROVE-SKIP.** The ABC paragraph is narrative and institutional, not symbolically dense. The prose already explains the bridge metaphor and funding stakes.
>
> **Candidate E — Combinatorial explosion scaling aside: APPROVE-SKIP.** The passage is conceptually important but not mathematically dense in the Tier 3 sense. It uses plain prose, not formulas, derivations, or stacked abstract notation.
>
> **Candidate F — SHRDLU/blocks-world aside: APPROVE-SKIP.** The Winograd paragraph is accessible narrative explanation. A plain-reading aside would repeat the surrounding prose rather than reduce symbolic density.
>
> **Missed primary-source sentence: Yes.** Lighthill's Winograd/postscript sentence is the missed quote-worthy sentence. It is Green-source, short enough for the cap, paraphrased by the chapter, and more vivid than the non-verbatim proposed sentence.
>
> **Final Tier 3 count:** 1 APPROVED as a revision, 5 SKIPPED.

---

## Decisions and rationale

| # | Element | Codex verdict | Action taken | Why |
|---|---|---|---|---|
| 8 | Inline tooltip | APPROVE-SKIP | **SKIP** | Universal default in `READER_AIDS.md`. |
| 9 / Cand A | Lighthill combinatorial-explosion pull-quote | REVISE — proposed wording failed verbatim check | **APPLY REVISED** | AIAI PDF plus Chilton HTML do not contain the proposed sentence. A nearby Green-source Lighthill sentence in the Winograd discussion is exact, shorter, and better anchored to the prose's SHRDLU paragraph. |
| 9 / Cand B | BBC debate verbatim | APPROVE-SKIP | **SKIP** | Source registry marks the AIAI debate page Yellow for metadata only; no logged transcript exists. |
| 9 / Cand C | Existing in-prose note | APPROVE-SKIP | **SKIP** | The existing note should stay as Tier 1/Tier 1-adjacent reader aid context; it is not a second pull-quote candidate. |
| 10 / Cand D | ABC classification plain-reading | APPROVE-SKIP | **SKIP** | Narrative/institutional, already clear, not symbolically dense. |
| 10 / Cand E | Scaling argument plain-reading | APPROVE-SKIP | **SKIP** | Important but already written in plain prose; no formulas or derivations. |
| 10 / Cand F | SHRDLU plain-reading | APPROVE-SKIP | **SKIP** | Concrete narrative example; an aside would duplicate the paragraph. |
| — | Missed candidate | Found and folded into Candidate A revision | **APPLY REVISED** | The missed Green-source sentence supplies the pull-quote that should land under the one-quote cap. |

---

## Final landed elements

1. `:::note[Lighthill's scaling objection]` pull-quote callout immediately after the paragraph in the "## Combinatorial Explosion Becomes Policy" section anchored by this unique sentence:

   `The achievement did not dissolve the problem of wider language and wider common sense.`

   Exact text to insert:

   ```markdown
   :::note[Lighthill's scaling objection]
   > Extension of the methods used to a much wider universe of discourse would be opposed violently by the combinatorial explosion.

   This is not a hardware complaint; it is Lighthill turning Winograd's success into evidence that fenced domains could not yet carry general AI.
   :::
   ```

**Tally: 1 APPROVED, 5 SKIPPED of 6 total candidates.**

The author's proposed pull-quote did not survive verbatim verification as written, but the chapter should still land one revised pull-quote from Lighthill Part I. No plain-reading asides should land.
