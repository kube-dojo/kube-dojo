# Tier 3 Proposal — Chapter 18: The Lighthill Devastation

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default per READER_AIDS.md.

## Element 9 — Pull-quote (at most 1)

The chapter is narratively and institutionally dense throughout. The primary-source candidate universe is:

- The **1973 Lighthill Report** ("Artificial Intelligence: A General Survey"): the report contains scathing direct language about combinatorial explosion and the failure of category B. The chapter paraphrases extensively but does not quote verbatim full sentences from Lighthill's own text.
- The **BBC *Controversy* televised debate** (June 1973, Royal Institution): the chapter explicitly notes this has not yet been watched/logged and places a guardrail against inferring what any participant said. No verbatim lines from the debate may be proposed.

### Candidate A — Lighthill's own words on combinatorial explosion

The chapter's key technical argument (the "Combinatorial Explosion Becomes Policy" section) paraphrases Lighthill's Part I pp.8–20. Lighthill's report is documented as Green-status primary source, and it contains direct declarative sentences about the combinatorial-explosion problem.

**Status: PROPOSED.**

Rationale: The sentence-level verdict from Lighthill's pen would anchor the chapter's pivot from technical critique to policy argument better than any paraphrase. The report's pp.8–20 are the technical hinge; a verbatim sentence from those pages placed after the paragraph introducing combinatorial explosion would do new work — signalling that this is Lighthill's own analytical language, not a later historian's reconstruction. Insertion anchor: in the "## Combinatorial Explosion Becomes Policy" section, after the paragraph ending "…the methods did not automatically scale into open-ended reasoning."

Working hypothesis (Codex to verify against the Lighthill report, AIAI PDF at aiai.ed.ac.uk/events/lighthill1973/lighthill.pdf, pp.8–10 of Part I):

> The possibility of a "combinatorial explosion" — a combinatorial increase in the range of possible combinations of symbols too great for any computer then available or foreseeable to handle — is, I suggest, at the root of many of the disappointments of the past.

If verbatim correct, annotation should note that this sentence turns a mathematical scaling problem into a policy verdict: it is not a diagnosis of current hardware limits, but an argument that the *field's* core strategy — general search over symbolic states — had encountered a structural ceiling.

### Candidate B — BBC *Controversy* debate verbatim

**Status: SKIPPED.** The contract has not logged the 81-minute broadcast; no verbatim lines may be proposed without a primary-source watch-and-log. The AIAI page confirms the event and participants only.

### Candidate C — In-prose existing callout

The chapter already contains an in-prose `> [!note] Pedagogical Insight: The Bridge Was the Target` callout (lines 88–91 of the current prose body), which serves the same structural function a pull-quote would serve for the introduction. Adding a second callout in the same register would produce adjacent repetition. This reinforces the 1-per-chapter cap: Candidate A must be the sole candidate if approved.

## Element 10 — Plain-reading asides (1–3 per chapter)

Ch18 is narrative-institutional throughout: institutional commissioning, ABC policy classification, funding logic, rebuttal table, infrastructure politics, and aftermath framing. There are no mathematical derivations, no formulae, and no abstract definitions stacked without context. Survey:

### Candidate D — ABC classification paragraph

The paragraph in "## The ABC Trap" explaining categories A, B, and C (the bridge metaphor).

**Status: SKIPPED.** The paragraph is narratively clear; no symbolic density. Plain-reading commentary would only paraphrase what the prose already says.

### Candidate E — Combinatorial explosion scaling argument

The paragraph describing how search spaces expand and exceptions multiply.

**Status: SKIPPED.** The passage is discursive rather than symbolic; the chapter prose carries its own plain-English explanation ("programs that looked intelligent in a narrow world stopped looking general"). An aside would add no new clarity.

### Candidate F — SHRDLU/blocks-world paragraph

The Winograd passage: "Winograd's blocks-world language work made the issue concrete…"

**Status: SKIPPED.** Already written in accessible narrative; the prose is doing the plain-reading job itself. No dense abstraction is stacked here.

## Summary verdict

- Element 8: SKIP.
- Element 9: 1 PROPOSED (Candidate A — Lighthill's combinatorial-explosion sentence from Part I pp.8–10), 2 SKIPPED (B — BBC debate verbatim unglogged; C — existing in-prose callout displaces a second pull-quote).
- Element 10: 0 PROPOSED, 3 SKIPPED (D, E, F — all narrative-institutional, no symbolic density).

**Total: 1 PROPOSED, 5 SKIPPED.**

## Author asks Codex to

1. **Verify Candidate A's verbatim wording** against the Lighthill 1972 report, available at `https://www.aiai.ed.ac.uk/events/lighthill1973/lighthill.pdf`, Part I pp.8–10. Confirm or correct the proposed quotation word-for-word; APPROVE / REJECT / REVISE.
2. **Confirm whether the in-prose `> [!note]` callout** (lines 88–91 of the prose body, "Pedagogical Insight: The Bridge Was the Target") already quotes or closely paraphrases the same Lighthill sentence being proposed — if so, the adjacent-repetition condition applies and the pull-quote must be REJECTED regardless of source-fidelity.
3. **Survey Part I pp.1–7 and pp.18–20** for any other primary-source sentence (Lighthill's direct voice) that the chapter paraphrases but does not quote; flag any additional candidate the author may have missed.
