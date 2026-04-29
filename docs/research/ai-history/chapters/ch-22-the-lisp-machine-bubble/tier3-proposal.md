# Tier 3 Proposal — Chapter 22: The Lisp Machine Bubble

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default.

## Element 9 — Pull-quote (at most 1)

The chapter is narratively dense (technical and economic history) with very few verbatim quotations from primary sources. Survey of candidates:

### Candidate A — Symbolics 3600 Technical Summary product claim

The chapter discusses Symbolics' self-presentation of the 3600 as combining "supermini power with a dedicated workstation," and the summary's framing of the network as preserving time-sharing's "communication and resource-sharing benefits" while giving single-user response. These are paraphrased in-prose; no full verbatim sentence from the Symbolics 3600 Technical Summary is currently quoted in the chapter.

**Status: SKIPPED.** The Symbolics 3600 Technical Summary is a vendor marketing document. Elevating a product-pitch sentence to a pull-quote would give vendor voice unwarranted authority; the chapter already notes the source is a pitch and should be read as one. A pull-quote works best when the sentence carries historiographical or intellectual weight independently of its origin. Vendor self-promotion does not meet that bar.

### Candidate B — AIM-444 formulation of the time-sharing problem

AIM-444 (August 1977) frames the machine's rationale in technically precise terms: the mismatch between large interactive Lisp programs and time-shared PDP-10 systems, and the projection that future intelligent systems might need "five to ten times" the PDP-10 address space. The chapter paraphrases this but does not quote verbatim. The AIM-444 sentence is a primary-source engineering judgment from the chapter's central institutional actor.

**Status: PROPOSED.** The AIM-444 is the chapter's load-bearing technical primary source (Green). A verbatim sentence stating the address-space projection is quote-worthy: it is a measured engineering forecast, not marketing. Insertion: in the "The Time-Sharing Wall" section, after the paragraph that introduces the MACSYMA and LUNAR address-space problem. The annotation should note that this was a 1977 engineering estimate from the group that designed the answer, not hindsight.

Working hypothesis (Codex to verify against AIM-444 pp.2-3):

> "Future intelligent programs may require five to ten times the address space of the PDP-10."

If the verbatim wording differs (the chapter's paraphrase may condense it), revise to actual text. Annotation: The Lisp Machine Group quantified the pressure before building the solution — the machine's 24-bit virtual address space was a direct answer to this specific forecast.

## Element 10 — Plain-reading asides (0–3 per chapter)

The chapter is predominantly narrative and institutional. Survey for symbolically dense paragraphs:

### Candidate C — Tagged architecture paragraph ("The tag idea is especially revealing...")

The paragraph in "CONS To CADR" explaining tag bits runs: "Lisp programs manipulate many kinds of objects: symbols, numbers, lists, functions, arrays, and internal structures that point to other structures. A conventional machine can represent all of that in software, but the runtime pays for the translation. A machine with tag bits and microcode support could make the representation part of the hardware contract." This is somewhat technical but the chapter's prose already plain-reads it in the following sentences. No stacked formulas or abstract definitions.

**Status: SKIPPED.** The paragraph is narratively dense (explaining a technical idea through analogy), not symbolically dense (no formulas, derivations, or stacked definitions). The prose already does the plain-reading job; an aside would repeat what the surrounding sentences accomplish.

### Candidate D — Writable microcode paragraph

The paragraph explaining writable microcode ("It let the implementation of the Lisp runtime live close to the processor without freezing every design choice forever") is similarly technical but already written for a general reader. No symbolic notation; the analogy is immediate in-prose.

**Status: SKIPPED.** Same reason as Candidate C — narrative density, not symbolic density.

### Candidate E — Common Lisp portability exclusions paragraph

The paragraph listing what Common Lisp excluded (hardware/microcode-specific features, graphics, window systems, Flavors, locatives, multiprocessing, multitasking) is a dense enumeration but not symbolically dense in the READER_AIDS.md sense; it is a feature list, not a formula or abstract definition stack.

**Status: SKIPPED.** Not symbolically dense; listing features does not create the comprehension gap that plain-reading asides are designed to bridge.

## Summary verdict

- Element 8: SKIP.
- Element 9: 1 PROPOSED (Candidate B — AIM-444 address-space forecast), 1 SKIPPED (Candidate A).
- Element 10: 0 PROPOSED, 3 SKIPPED (Candidates C, D, E).

**Total: 1 PROPOSED, 4 SKIPPED.**

## Author asks Codex to

1. Verify Candidate B's verbatim wording against AIM-444 pp.2-3 (bitsavers scan). Does the document contain a sentence projecting that future intelligent systems would need five to ten times the PDP-10 address space? Return the exact sentence or the closest equivalent, and APPROVE / REJECT / REVISE the proposed pull-quote accordingly.
2. Confirm or reject the SKIP on Candidate A (Symbolics vendor pitch as pull-quote). Is there a sentence in the Symbolics 3600 Technical Summary (Green source) that carries enough independent historiographical weight to earn pull-quote status, and that is not already quoted or closely paraphrased in-prose?
3. Survey the "CONS To CADR" and "The Operating System Was Also Lisp" sections for any paragraph that is genuinely symbolically dense (stacked abstract definitions or technical formalism) that the author may have under-weighted as merely narratively dense. APPROVE a plain-reading aside if one is found; otherwise confirm 0 PROPOSED.
