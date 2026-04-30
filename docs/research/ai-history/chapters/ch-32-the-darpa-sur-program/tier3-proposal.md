# Tier 3 proposal — Chapter 32: The DARPA SUR Program

Author: Claude (Opus 4.7) — orchestrator-direct draft, 2026-04-30 (Part 6 inline rollout).

Per `docs/research/ai-history/READER_AIDS.md` §Tier 3, this proposal lists each candidate Tier 3 element with PROPOSED / SKIPPED status, insertion anchor, and rationale. Cross-family Codex review will accept, revise, reject, or agree with skips per element.

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**Status:** SKIPPED (per READER_AIDS.md §Tier 3 element 8 — non-destructive tooltip component does not exist; bit-identity rule blocks `<abbr>` HTML; Plain-words glossary covers the same job).

## Element 9 — Pull-quote (at most one)

**Status:** SKIPPED.

**Rationale.** The chapter's load-bearing primary-source quotations are already integrated verbatim into the prose paragraphs. Adding any of them as a `:::note` callout immediately after the same paragraph would create the adjacent-repetition problem the READER_AIDS spec explicitly refuses. Specifically:

- **Pierce 1969 (*JASA*) "schemes for turning water into gasoline…"** — quoted verbatim in paragraph 2 (line 10 of the chapter). Anchor: Pierce 1969 (Green-by-convergence via Jelinek 2005 LREC slides PDF p.2 + Church 2018 NLE). Adjacent-repetition reject.
- **Pierce 1969 "most recognizers behave not like scientists…"** — quoted verbatim in paragraph 3 (line 12). Same anchor, same reject reason.
- **Newell 1971 §8.6 "If the claims are not made against a background of publicly available high quality data of known structure…"** — quoted verbatim in the §8.6 paragraph mid-chapter. Anchor: Newell et al. 1971 §8.6 (Green, primary, page-anchored; CMU PDF p.50 per `sources.md`). Adjacent-repetition reject.
- **Jelinek 1988 "Whenever I fire a linguist our system performance improves."** — quoted verbatim in the post-1976/Wayne section. Anchor: Jelinek 2005 LREC slides PDF p.2 ("The Quote" slide). Adjacent-repetition reject.
- **Mercer 1985 (Arden House) "There is no data like more data."** — quoted verbatim in the same section. Anchor: Jelinek 2005 LREC slides PDF p.5. Adjacent-repetition reject.

No candidate pull-quote survives the adjacent-repetition test. SKIP.

## Element 10 — Selective dense-paragraph asides (`:::tip[Plain reading]`)

**Status:** SKIPPED.

**Rationale.** READER_AIDS.md §Tier 3 element 10 reserves plain-reading asides for paragraphs that are **symbolically** dense (mathematical formulas, derivations, abstract definitions stacked) — explicitly **not** narratively dense. Chapter 32 is narrative-historical: it traces an institutional arc from Pierce (1966–1969) through Newell (1971), the September 1976 demonstration, the IBM parallel track (1971–1983), the funding winter (1975–1986), and the Wayne revival (mid-1980s). The chapter contains no equations, no symbolic derivations, and no stacks of abstract definitions.

The closest the prose comes to symbolic density is the maximum-likelihood decomposition paragraph that explains the IBM noisy-channel framing in plain prose ("Given an acoustic observation, the recognizer seeks the word sequence with the highest probability. That probability can be decomposed into two parts: how likely the words are as language, and how likely the observed sounds are if those words were spoken"). That paragraph already does the plain-reading work in-prose; an aside would be tautological commentary. SKIP.

## Verdict summary

- 8 (tooltip): SKIP — component unavailable, glossary covers it.
- 9 (pull-quote): SKIP — adjacent-repetition rule rejects every candidate; all load-bearing quotes are already in-prose verbatim.
- 10 (plain-reading asides): SKIP — no symbolically dense paragraphs in this chapter; the maximum-likelihood paragraph already explains itself in prose.

Codex review is asked to either confirm these three SKIPs or revive a candidate the author missed (with a Green primary anchor and a paragraph that survives the adjacent-repetition / symbolically-dense gates).
