# DECISION — #1639 prompt/context/harness consolidation plan

**Date:** 2026-05-29 (session 68) · **Epic:** kube-dojo/kube-dojo.github.io#1639
**Audit by:** codex gpt-5.5 (read-only) · **Verified by:** orchestrator (claude)

> **DECIDED 2026-05-29:** User approved **Option B — full consolidation**
> ("go all the way. we have git after all no?"). Execution deferred to a
> FRESH session (user is picking up a new Claude Code CLI bugfix release
> first; also matches the fresh-session-after-interview rule). This plan is
> the brief for that session — execute Sections 1–4 below, gates, then PR.
> NOT YET EXECUTED.

## Headline finding (verified, not just codex's claim)

The prompt / context / harness teaching content is **already mostly
consolidated** into `ai/ai-engineering-foundations/` (a 12-module
prompt→context→harness→symphony spine). A prior session moved the duplicated
material there and left behind tiny "this module has moved" stubs:

- `ai/ai-native-work/module-2.1-harness-engineering.md` — 23 words, stub
- `ai/ai-native-work/module-2.2-orchestrating-fleets-symphony.md` — 25 words, stub
- `ai-ml-engineering/ai-native-development/module-1.6-prompt-engineering-fundamentals.md` — 18 words, stub ("This module has moved. See Prompt Fundamentals.")

**The real reason it still feels scattered/buried:** the canonical
`ai-engineering-foundations` section **is NOT in the AI sidebar in
`astro.config.mjs`** (verified: grep returns nothing), and its `sidebar.order`
collides with `ai/foundations`. The unified home exists on disk but learners
cannot navigate to it. *That* is the burial — not live duplication.

Teaching-content only. No labs (those are #386).

## Remaining work

### 1. Make the section navigable (highest value, non-destructive)
- Add `AI Engineering Foundations` to the AI sidebar in `astro.config.mjs`
  (between `AI Foundations` and `AI-Native Work`).
- Resolve the `sidebar.order` collision with `ai/foundations` (foundations
  stays order 1 → AI-Eng-Foundations becomes order 2, shift later AI sections).
- Update `src/content/docs/ai/index.md`: 5 sections/25 modules → 6 sections/37
  modules; add it to the route diagram + boundary table + good-first-clicks.

### 2. Cross-links (non-destructive) — ~23 one-line "see foundations X.Y" links
So neighbor modules stop re-teaching the basics. Full map below.

### 3. Fix stale links (non-destructive)
- `ai-native-development/module-1.2-local-models-for-ai-coding.md` — next-module
  text points at the old "Prompt Engineering Fundamentals" → repoint.
- `ai-native-development/module-1.5-cli-ai-coding-agents.md` — links to
  nonexistent `/ai-ml-engineering/ai-native-development/module-02-prompt-fundamentals/`
  → replace with `/ai/ai-engineering-foundations/module-1.1-prompt-fundamentals/`.

### 4. Cleanup (DESTRUCTIVE — needs explicit approval)
- Retire the 3 dead stubs from visible nav. Keep slugs alive via `redirects`
  in `astro.config.mjs`, THEN optionally delete the stub files.
- Dedupe `ai-ml-engineering/frameworks-agents/module-1.3-langgraph-for-agents.md`:
  despite its title it teaches CoT / ReAct / self-consistency (overlaps
  foundations 1.2). Port any unique ReAct material into foundations 1.2; reduce
  the local reteaching. Preserve the file + slug.

## Per-module recommendations (from audit)

**RETIRE (already empty stubs):** ai-native-work 2.1, 2.2
**DEDUPE-INTO-FOUNDATIONS:** ai-native-development 1.6 (stub, nothing to port).
**RECONCILE (title/content scramble — see section below):** frameworks-agents
1.3-langgraph + 1.4-llamaindex.
**KEEP-AS-NEIGHBOR + cross-link (all others):** ai-native-work 1.1–1.4;
ai-native-development 1.1–1.5, 1.7–1.10; frameworks-agents 1.1–1.2, 1.5–1.10.
These are genuinely distinct subjects (using AI coding tools; building agentic
apps with LangChain/MCP/multi-agent) — they should LINK to foundations, not
re-teach it.

## Frameworks-agents 1.3 / 1.4 reconciliation (folded in 2026-05-29 per user — handle in one swoop, no separate ticket)

VERIFIED title/content scramble:
- `frameworks-agents/module-1.3-langgraph-for-agents.md` — titled LangGraph,
  but body teaches CoT / ReAct / self-consistency (reasoning basics that
  duplicate foundations `1.2 Reasoning and Logic Prompts`).
- `frameworks-agents/module-1.4-llamaindex.md` — titled "LlamaIndex" (slug
  `...module-1.4-llamaindex`), but body is a full, *good* LangGraph course
  (33 LangGraph refs / 19 StateGraph / only 2 LlamaIndex; all 6 sections are
  LangGraph: StateGraph, nodes/edges, cycles, multi-agent, persistence).
- Net effect: LangGraph is taught (in the wrong file), reasoning basics are
  duplicated, and **LlamaIndex is genuinely not covered at all**.

RECOMMENDED reconciliation (the fresh session should confirm before executing):
1. **LangGraph** → move 1.4's strong LangGraph body into `1.3` (which is
   already titled/slugged "langgraph-for-agents"). 1.3 becomes the real
   LangGraph module.
2. **Reasoning basics** currently mis-filed in 1.3 → port any unique ReAct /
   reasoning-action material into foundations `1.2`, drop the rest (it dupes
   1.2). This satisfies the original DEDUPE-INTO-FOUNDATIONS intent.
3. **LlamaIndex** → `1.4` now needs a real LlamaIndex teaching module authored
   (net-new teaching content, ~5000+ words, T0 gates, NO labs). This is the
   one genuine *missing module* this restructure surfaces — author via codex,
   composer-2.5 R1 per Decision Card C.
   Alternative if authoring LlamaIndex is out of appetite: retitle 1.4 to
   LangGraph-advanced and merge with 1.3 — but that LEAVES LlamaIndex
   uncovered, so prefer authoring it.

## Final canonical section shape
`ai-engineering-foundations` stays 12 modules: 1.1–1.4 (prompt), 2.1–2.4
(context), 3.1–3.3 (harness), 4.1 (symphony). frameworks-agents keeps its
module count but 1.3 becomes real LangGraph and 1.4 becomes real LlamaIndex.

## Cross-link map (neighbor → foundations modules to link)
ai-native-work: 1.1→{1.1,2.1}; 1.2→{2.3,3.1,3.2}; 1.3→{3.1,4.1}; 1.4→{3.2,3.3}
ai-native-development: 1.1→{2.1,3.2}; 1.2→{1.1,2.1}; 1.3→{2.2,2.3,2.4,3.2};
1.4→{2.1,3.1}; 1.5→{3.1,3.2,3.3}; 1.7→{1.1,1.2,1.3}; 1.8→{1.1,1.3,3.2};
1.9→{2.1,2.3,3.1}; 1.10→{2.3,2.4,3.2,3.3}
frameworks-agents: 1.1→{1.1,2.3,3.2}; 1.2→{2.3,3.2}; 1.3→{1.2}; 1.4→{2.4,4.1};
1.5→{2.3,4.1}; 1.6→{1.2,2.3,2.4}; 1.7→{3.2,3.3,4.1}; 1.8→{2.3}; 1.9→{2.4,3.2};
1.10→{2.3,2.4,4.1}

## Gates after execution
`git diff --check` · `check_links.py` · `check_site_health.py` ·
`test_pipeline.py` · `npm run build` (from primary checkout, post-merge).

## Risks
- Deleting stubs without `redirects` would break inbound links → add redirects first.
- Known bad link in 1.5-cli-ai-coding-agents (above) — fix regardless.
- No UK mirror files for these AI sections (no immediate uk/ edits).
- `frameworks-agents/1.3` + `1.4` title/content scramble is now folded into
  this restructure (see reconciliation section above) — NOT a separate ticket.
  Risk: the LlamaIndex rewrite is net-new authoring; if appetite is limited,
  do the non-authoring parts (nav + cross-links + LangGraph move + 1.2 dedupe)
  and leave the LlamaIndex author dispatch as the single follow-up.

## DECIDED — Option B (full consolidation), execute next session
- **A — Wire-up + cross-links + link-fixes (non-destructive).** Sections 1–3.
- **B — Full consolidation (CHOSEN).** A + stub retirement w/ redirects +
  frameworks-agents 1.3/1.4 reconciliation (LangGraph move, foundations-1.2
  dedupe, LlamaIndex author).
- **C — Hold.**

**User chose B 2026-05-29** ("go all the way. we have git after all no?") and
folded in the 1.4 fix ("more effective to do them in one swoop"). Suggested
execution order for the fresh session, each its own commit so any step is
revertible: (1) nav wiring → build green; (2) link fixes + cross-links → build;
(3) stub retirement w/ redirects → build; (4) LangGraph move 1.4→1.3 +
foundations-1.2 dedupe → build; (5) author real LlamaIndex 1.4 (codex →
composer-2.5 R1). All gates per the Gates section. One PR (or a small stack).
