# Tier 3 adversarial review — Codex (gpt-5)

Direct cross-family review requested for Claude-authored Tier 1 reader-aids and Tier 3 proposal for Chapter 23, "The Japanese Threat." Codex verified the proposed verbatim material against Green primary sources using `curl` plus `pdftotext`; Furukawa TR-228 required local `pdftoppm` plus `tesseract` OCR because the PDF has no embedded text. Review is against `READER_AIDS.md` Tier 3 rules, especially the pull-quote adjacent-repetition rule and the symbolic-density threshold for plain-reading asides.

---

## Codex's verdicts (verbatim)

> **Element 8: APPROVE-SKIP.** Universal skip per `READER_AIDS.md`; destructive inline tooltip markup is still disallowed.
>
> **Candidate A — Fuchi 1992 retrospective on the exaggerated image: REVISE.** The proposed sentence is not verbatim. Fuchi does not write, "The 1981 conference generated sensational news all over the world and created an exaggerated image of the FGCS project." The Green Bitsavers PDF verifies two nearby source sentences: "The substance of those discussions was reported as sensational news all over the world" and "When this project started, an exaggerated image of the project was engendered, which seems to persist even now." Use the second sentence as the pull-quote because it carries the chapter's central corrective without requiring a stitched paraphrase. This is not adjacent repetition: the chapter paraphrases the point but does not quote the sentence verbatim.
>
> **Candidate B — OTA 1983 "competitive onslaught" framing: APPROVE-SKIP.** The phrase is Green and verbatim enough in the OTA PDF, but the surrounding prose already gives OTA's threat framing. Landing it would amplify the alarm layer rather than the chapter's corrective hinge. Candidate A, revised to Fuchi's actual wording, is the better single pull-quote.
>
> **Candidate C — Feigenbaum and McCorduck pull-quote: APPROVE-SKIP.** Correct skip. This source is not in the current Green anchor set, so it cannot support a Tier 3 verbatim element in this pass.
>
> **Candidate D — Uchida/Fuchi Final Evaluation Workshop framing: APPROVE-SKIP.** Verified Green source, but the sentence is institutional description, not a quote-worthy hinge. The prose already integrates the same frame in the evaluation section.
>
> **Candidate E — Prolog/logic-programming bridge plain-reading aside: APPROVE-SKIP.** Correct skip. The paragraph is explanatory prose, not mathematically or symbolically dense, and it already plain-reads the stack.
>
> **Candidate F — GHC/KL1/Multi-PSI plain-reading aside: REJECT.** Furukawa TR-228 supports the lineage in broad terms: GHC is a logic programming language for concurrent programming and parallel execution, successor to Relational Language, Concurrent Prolog, and PARLOG; Fuchi/Kurozumi support KL1 as the final-stage integrating language. But `READER_AIDS.md` limits plain-reading asides to symbolically dense paragraphs. This paragraph is an acronym/architecture survey, not a formula, derivation, or stacked abstract definition. The proposed aside also overstates GHC as "extended Prolog with concurrency primitives"; the primary wording is "logic programming language for concurrent programming and parallel execution," not an extension of Prolog. No aside should land.
>
> **Candidate G — PIM/KLIPS architecture aside: APPROVE-SKIP.** Correct skip. The chapter does not develop KLIPS/PIM architecture deeply enough to warrant an aid, and the relevant material is not symbolically dense under the Tier 3 rule.
>
> **Missed primary-source sentence: Yes, but APPROVE-SKIP under the cap.** OTA 1983 contains a strong paraphrased-but-not-quoted sentence: "Japan's gamble is that it can jump ahead of American entrants with families of computer systems having performance capabilities that will render present-day software inventories obsolete." It is Green and quote-worthy for the software-lock-in scene, but it does not beat the revised Fuchi sentence as the chapter's single pull-quote because the chapter's main task is to separate threat perception from project reality.

---

## Decisions and rationale

| # | Element | Codex verdict | Action taken | Why |
|---|---|---|---|---|
| 8 | Inline tooltip | APPROVE-SKIP | **SKIP** | Universal default in `READER_AIDS.md`. |
| 9 / Cand A | Fuchi 1992 exaggerated-image pull-quote | REVISE — source verified, proposed wording not verbatim | **APPLY REVISED** | Green source supports the idea, but not the proposed stitched sentence. Use Fuchi's exact "exaggerated image" sentence. |
| 9 / Cand B | OTA "competitive onslaught" pull-quote | APPROVE-SKIP | **SKIP** | Green and forceful, but redundant with the threat prose and weaker than Fuchi as the chapter hinge. |
| 9 / Cand C | Feigenbaum and McCorduck pull-quote | APPROVE-SKIP | **SKIP** | Not in the current Green anchor set. |
| 9 / Cand D | Final Evaluation Workshop framing | APPROVE-SKIP | **SKIP** | Descriptive institutional self-frame; prose already carries it. |
| 10 / Cand E | Logic-programming bridge plain-reading aside | APPROVE-SKIP | **SKIP** | Not symbolically dense, and the prose explains the concept directly. |
| 10 / Cand F | GHC/KL1/Multi-PSI plain-reading aside | REJECT | **SKIP** | Acronym density is not Tier 3 symbolic density; the aside also needs a more faithful GHC wording if reused elsewhere. |
| 10 / Cand G | PIM/KLIPS architecture aside | APPROVE-SKIP | **SKIP** | Underdeveloped in prose and not symbolically dense. |
| — | Missed OTA software-lock-in sentence | APPROVE-SKIP | **SKIP** | Green and quote-worthy, but loses to Fuchi under the one-pull-quote cap. |

---

## Final landed elements

1. `:::note[The project director's correction]` pull-quote callout immediately after the paragraph in the "## The Hype Narrows" section anchored by the unique sentence: "The actual program centered on the infrastructure for parallel inference and knowledge information processing."

Exact text to insert:

```markdown
:::note[The project director's correction]
> "When this project started, an exaggerated image of the project was engendered, which seems to persist even now."

Fuchi's 1992 correction matters because it came from ICOT's director, not from a foreign critic trying to dismiss the project after the fact.
:::
```

No plain-reading asides should land.

**Tally: 1 APPROVED, 7 SKIPPED of 8 total candidates.**

