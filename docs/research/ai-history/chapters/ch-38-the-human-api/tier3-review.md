# Tier 3 review — Chapter 38

Reviewer: Codex (gpt-5.5, model_reasoning_effort=high), 2026-04-30, adversarial cross-family pass on PR for `claude/394-ch38-reader-aids`.

## Element 8 — Tooltip

Verdict: CONFIRM SKIP

One-line reason: READER_AIDS.md makes tooltip support a global skip until a non-destructive component exists; Chapter 38 has no exception.

## Element 9 — Pull-quote

Verdict: REVIVE

One-line reason: The proposal correctly rejects its three local prose-derived candidates, but misses a Green primary-source sentence from the AWS launch announcement that states the chapter's API thesis without already appearing verbatim in prose.

Full proposed insertion, immediately after the anchor paragraph below:

```markdown
:::note[From the launch announcement]
> Amazon Mechanical Turk does this, providing a web services API for computers to integrate Artificial Artificial Intelligence directly into their processing.

AWS's own launch copy made the chapter's key move explicit: this was not only a marketplace, but an API vocabulary for routing work to people.
:::
```

Green primary anchor: Amazon Web Services, "Announcing Amazon Mechanical Turk," launch page, November 2, 2005; sources.md Green G9 anchors this sentence to the announcement body, lines 30-32.

Insertion-anchor paragraph:

> Amazon framed this service as providing a web-services API for computers to integrate "Artificial Artificial Intelligence" directly into their processing. The phrase was a deliberate and self-aware irony, pointing to the persistent gap between the ambition of artificial intelligence and the reality of what software could currently achieve on its own. The product’s name itself, Mechanical Turk, pointed back to an eighteenth-century illusion. As historical accounts explain, the original Mechanical Turk was a famous chess-playing automaton that appeared to be an autonomous, thinking machine, but actually hid a person inside its cabinet who operated it. Amazon’s modern namesake followed the same logic as an Internet service: software systems could present an automated, intelligent facade to the world, while relying on a distributed network of human workers to handle the cognitive steps the code could not execute.

Adjacent-repetition test: PASS. The chapter paraphrases the launch sentence and quotes only the phrase "Artificial Artificial Intelligence"; it does not quote the full AWS sentence verbatim. The callout would therefore foreground the primary launch language rather than duplicating an adjacent prose quotation. The annotation adds provenance and interface stakes rather than merely restating the paragraph.

## Element 10 — Plain-reading asides

Verdict: CONFIRM SKIP

One-line reason: The chapter has narrative and institutional density, but no symbolically dense paragraph with formulas, derivations, or stacked abstract definitions.

The closest candidates are the patent-parameter paragraph and the Snow et al. cost/redundancy paragraphs. Both explain operational mechanics in prose: task parameters, redundancy, bias control, votes, costs, and worker-market rules. They contain no mathematical notation, derivation, formal definition chain, or symbolic compression that would justify a `:::tip[Plain reading]` intervention under READER_AIDS.md item 10.

Symbolic-density justification: none qualifies. The numerical claims are ordinary historical evidence and cost accounting, not symbolic exposition; a plain-reading aside would repeat the prose instead of decoding a dense technical passage.

## Summary

1 landed/revived: Element 9 pull-quote, using the AWS 2005 launch announcement as the Green primary anchor. 2 skipped: Element 8 tooltip remains globally skipped; Element 10 plain-reading asides remain skipped because Chapter 38 is narrative-historical rather than symbolically dense.
