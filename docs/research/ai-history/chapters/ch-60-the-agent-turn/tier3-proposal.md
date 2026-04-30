# Chapter 60 — Tier 3 reader-aid proposal

Author: Claude (claude-opus-4-7), 2026-04-30
Reviewer (cross-family): Codex (gpt-5.5)
Spec: `docs/research/ai-history/READER_AIDS.md` Tier 3 (elements 8, 9, 10).

## Element 8 — Inline parenthetical definition

**SKIPPED.** Per the spec, every chapter skips this element until a non-destructive Astro `<Tooltip>` component lands. The Tier 1 *Plain-words glossary* covers parametric/non-parametric memory, RAG, chain-of-thought, ReAct loop, function calling, and prompt injection.

## Element 9 — Pull-quote (`:::note[]` callout)

**PROPOSED.** Candidate sentence — ReAct paper (Yao et al. 2022, arXiv:2210.03629), abstract:

> we explore the use of LLMs to generate both reasoning traces and task-specific actions in an interleaved manner

**Insertion anchor:** immediately after the chapter paragraph beginning "Shunyu Yao and collaborators described ReAct as interleaving reasoning traces and task-specific actions." (the paragraph that paraphrases this exact abstract claim). The pull-quote installs the paper's voice over the chapter's paraphrase before the loop-mechanics paragraph that follows.

**Rationale:**
- The chapter explicitly paraphrases this line ("interleaving reasoning traces and task-specific actions") — block-quoting the abstract converts the chapter's summary to documented evidence and lets readers see the exact phrasing the paper uses for the architectural grammar.
- "Interleaved" is the load-bearing word. The chapter's later "thought, action, observation" framing depends on the interleaving claim. The block-quote anchors the readers' eyes on the paper's own choice of word before the loop is unpacked.
- The chapter does not block-quote any primary source; pulling one in for the architectural hinge of the chapter is high-yield.

**Annotation (1 sentence, doing new work):** This is the architectural grammar of the agent turn — every later "agentic" framework, from LangChain agents to OpenAI function calling, restates this same interleave of generated reasoning and selected action.

**Word budget:** 18 words quoted + ~32 words annotation ≈ 50 words. Under 60-word cap.

**Alternative if rejected (REVIVE candidate):** The Toolformer abstract sentence "we propose Toolformer, a model trained to decide which APIs to call, when to call them, what arguments to pass, and how to best incorporate the results into future token prediction" (Schick et al. 2023) — fuller technical statement of self-supervised tool-use, but ~35 words quoted alone, leaving little room for annotation.

**Second alternative:** AutoGPT v0.1.0 README "NEXT COMMAND" instruction line — distinctive cultural artifact, but the chapter already paraphrases it explicitly, so adjacent-repetition risk is high.

## Element 10 — Plain-reading aside

**SKIPPED.** Ch60's prose is narrative/architectural — RAG infrastructure description, search workflow framing, ReAct loop grammar, plugin and function-calling product framing. There are no symbolically dense paragraphs (no formula derivations, no stacked technical definitions requiring pause). Plain-reading asides apply only to formula/derivation density per the spec.

## Summary

| Element | Author proposal | Rationale |
|---|---|---|
| 8 | SKIP | Bit-identity rule until `<Tooltip>` lands |
| 9 | PROPOSE | ReAct abstract sentence; chapter paraphrases the architectural hinge but does not block-quote it |
| 10 | SKIP | No symbolic density |

**Awaiting Codex adversarial review.** Be willing to REJECT (if you judge the chapter's "interleaving reasoning traces and task-specific actions" paragraph paraphrases the same content too closely — adjacent-repetition risk), REVISE (annotation length or anchor placement), or REVIVE (a different verbatim sentence — e.g., the Toolformer abstract, the OpenAI plugins page Overview line, the OpenAI function-calling page line on JSON arguments, or the AutoGPT README "NEXT COMMAND" line).
