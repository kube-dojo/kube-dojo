# 2026-05-26 — AI Section Consolidation (Phase 4 of #1530)

## Status
Accepted & executed — verified 2026-05-29 (session 68). See the 2026-05-29 addendum at the bottom: all decisions here were implemented, but this ADR **missed the root cause** of #1639 (the canonical track was absent from the sidebar). That gap is now fixed.

## Context
KubeDojo recently shipped 12 modules in `src/content/docs/ai/ai-engineering-foundations/` representing the new canonical home for prompt, context, harness, and Symphony engineering. These modules establish the foundational "AI Engineering" layer spanning prompt design, context management, and workflow automation.

However, three older "orphan" modules remain in the `ai-native-work` and `ai-native-development` sections. These modules duplicate content now covered comprehensively in the new foundational track. This ADR consolidates these orphans to remove duplication, streamline navigation, and establish a single source of truth for engineering concepts.

## Decision summary
| Orphan | Decision | Canonical target |
|---|---|---|
| module-1.6-prompt-engineering-fundamentals.md | Option A (Delete + Redirect) | `ai/ai-engineering-foundations/module-1.1-prompt-fundamentals.md` |
| module-2.1-harness-engineering.md | Option A (Delete + Redirect) | `ai/ai-engineering-foundations/module-3.1-harness-fundamentals-layers-and-system-of-record.md` |
| module-2.2-orchestrating-fleets-symphony.md | Option A (Delete + Redirect) | `ai/ai-engineering-foundations/module-4.1-symphony-work-orchestration-as-applied-harness.md` |

## Per-orphan decisions (detailed)

### Orphan 1: module-1.6-prompt-engineering-fundamentals
- **What it covers**: The anatomy of a prompt (context, role, instructions, structure, parameters), comparing prompting techniques (zero-shot, few-shot, role-based, structured output), prompt debugging workflows, and prompt evaluation/libraries.
- **Overlap with canonical**: This module is completely subsumed by the new prompt arc (`1.1` to `1.4`). The anatomy and techniques are expanded in `1.1-prompt-fundamentals.md` and `1.2-reasoning-and-logic-prompts.md`. Evaluation and debugging are covered in `1.3-prompt-safety-and-evaluation.md`, and library construction is handled in `1.4-prompt-libraries-and-contracts.md`.
- **Unique content worth preserving**: None. The script `validate_review_response.py` and small edge-case debugging examples are conceptually addressed by the structured output and evaluation content in the new modules.
- **Decision**: Option A. Delete and replace with a redirect stub. The prompt arc comprehensively extends and replaces this older introduction.
- **Execution steps**: 
  1. Replace the file at `src/content/docs/ai-ml-engineering/ai-native-development/module-1.6-prompt-engineering-fundamentals.md` with a frontmatter-only redirect stub.
  2. The stub content should be:
     ```markdown
     ---
     title: "Prompt Engineering Fundamentals"
     sidebar:
       order: 207
     ---
     This module has moved. See [Prompt Fundamentals](../../../ai/ai-engineering-foundations/module-1.1-prompt-fundamentals/).
     ```

### Orphan 2: module-2.1-harness-engineering
- **What it covers**: The seven principles of harness engineering, the 3-layer rule map (platform, advisory, enforcement), invariant enforcement via hooks, and trace-first recovery loops.
- **Overlap with canonical**: Entirely subsumed by the 3.x harness arc (`3.1`, `3.2`, `3.3`). The 3-layer model is expanded in `3.1-harness-fundamentals-layers-and-system-of-record.md`, invariant enforcement is covered in `3.2-guardrails-gates-and-agent-legible-apps.md`, and trace-first loops/maintenance are covered in `3.3-operating-the-harness.md`.
- **Unique content worth preserving**: None. All core principles and operational playbooks are deeply expanded across the new harness arc.
- **Decision**: Option A. Delete and replace with a redirect stub.
- **Execution steps**:
  1. Replace the file at `src/content/docs/ai/ai-native-work/module-2.1-harness-engineering.md` with a frontmatter-only redirect stub.
  2. The stub content should be:
     ```markdown
     ---
     title: "Harness Engineering"
     sidebar:
       order: 5
     ---
     This module has moved. See [Harness Fundamentals](../../ai-engineering-foundations/module-3.1-harness-fundamentals-layers-and-system-of-record/).
     ```

### Orphan 3: module-2.2-orchestrating-fleets-symphony
- **What it covers**: Using issue trackers as the control plane for autonomous fleets, designing a `WORKFLOW.md` contract, the four lifecycle hooks, state machine vs. objective-driven orchestration, and the KubeDojo `/goal` convergence.
- **Overlap with canonical**: Completely subsumed by `4.1-symphony-work-orchestration-as-applied-harness.md`. `4.1` includes the hands-on poller loop exercises, the KubeDojo `/goal` paradigm, and expanded WORKFLOW.md definitions.
- **Unique content worth preserving**: None. The new `4.1` module incorporates all practical scripting details and conceptual models from the orphan.
- **Decision**: Option A. Delete and replace with a redirect stub.
- **Execution steps**:
  1. Replace the file at `src/content/docs/ai/ai-native-work/module-2.2-orchestrating-fleets-symphony.md` with a frontmatter-only redirect stub.
  2. The stub content should be:
     ```markdown
     ---
     title: "Orchestrating Fleets: Symphony"
     sidebar:
       order: 6
     ---
     This module has moved. See [Symphony — Work Orchestration as Applied Harness](../../ai-engineering-foundations/module-4.1-symphony-work-orchestration-as-applied-harness/).
     ```

## Cross-link additions

### File 1: `src/content/docs/ai/ai-engineering-foundations/index.md`
**Anchor:** Add at the very end of the file under the `## Reading Path` block.
**Text to add:**
```markdown
For operators who need to learn AI tool habits before building systems, see [AI-Native Work](../ai-native-work/). If you are an engineer looking for IDE and CLI tooling, start with [AI-Native Development](../../ai-ml-engineering/ai-native-development/).
```

### File 2: `src/content/docs/ai/ai-native-work/index.md`
**Anchor:** Add under the `## After This Section` block, at the end of that section (just before the `## What This Section Does Not Repeat` header).
**Text to add:**
```markdown
When you are ready to design repeatable automation loops for teams, move to [AI Engineering Foundations](../ai-engineering-foundations/) to learn about prompts, context, and harness operations.
```

### File 3: `src/content/docs/ai-ml-engineering/ai-native-development/index.md`
**Anchor:** Add under the `## Boundary With The Top-Level AI Track` block, at the end of that section (just before the `## After This Phase` header).
**Text to add:**
```markdown
For deep architectural treatment of prompts, context boundaries, and harness orchestration, see [AI Engineering Foundations](../../ai/ai-engineering-foundations/).
```

## Context-engineering gap

**(a) Accept the split**

By moving the prompt and context-related orphan out of `ai-native-development`, the section becomes purely runtime and tooling-focused (CLI agents, IDE setups, MCPs). We should accept this split rather than adding a thin signpost module. Prompt constraints, context chunking, and memory boundaries fundamentally belong in the `ai-engineering-foundations` track. Attempting to backfill a context signpost in the tooling track blurs the architectural boundary. The cross-links added in the index files will effectively route learners to the engineering foundations section when they need deep conceptual theory.

## Risks & Open Questions
- **Stale links:** Other modules in the repository might still contain hardcoded markdown links to the 3 orphans. The redirect stubs prevent 404s, but a full repository lint/link check should be run during execution to capture trailing references.

## Execution plan (for the implementing PR)
1. Edit `src/content/docs/ai/ai-engineering-foundations/index.md` to append cross-link text.
2. Edit `src/content/docs/ai/ai-native-work/index.md` to append cross-link text.
3. Edit `src/content/docs/ai-ml-engineering/ai-native-development/index.md` to append cross-link text.
4. Replace `src/content/docs/ai-ml-engineering/ai-native-development/module-1.6-prompt-engineering-fundamentals.md` with the Option A redirect stub.
5. Replace `src/content/docs/ai/ai-native-work/module-2.1-harness-engineering.md` with the Option A redirect stub.
6. Replace `src/content/docs/ai/ai-native-work/module-2.2-orchestrating-fleets-symphony.md` with the Option A redirect stub.
7. Run the site builder / Markdown linter to verify no dangling broken references.

---

## Addendum — 2026-05-29 (session 68): execution verified + the missed root cause

This ADR was written and largely executed, but issue **#1639** ("the subject is scattered / buried") was re-opened by the user on 2026-05-28 because the subject still *felt* fragmented. A fresh audit this session found why — and it was something this ADR did not consider.

### What this ADR got right (verified executed)
- **All 3 orphans are redirect stubs** (Option A done): `ai-native-development/module-1.6-prompt-engineering-fundamentals`, `ai-native-work/module-2.1-harness-engineering`, `ai-native-work/module-2.2-orchestrating-fleets-symphony`. Each is a "this module has moved" stub pointing at the canonical spine module.
- **All 3 index cross-links exist**: `ai-engineering-foundations/index.md` (→ neighbors, line 52), `ai-native-work/index.md` (→ foundations), `ai-native-development/index.md` (→ foundations).
- **Context-engineering split accepted** — spine modules 2.1–2.4 cover context engineering at depth; no thin signpost module was added, as decided.

### The root cause this ADR MISSED — and the fix
The canonical `ai/ai-engineering-foundations/` track (13 modules) **was never added to any sidebar.** `grep ai-engineering-foundations astro.config.mjs` returned zero entries; git history shows it was never wired in when the track shipped (#1530). The redirects and cross-links all pointed *to* a track that was **unreachable through navigation** — visible only by direct URL. That invisibility, not duplication, is why the subject "looked done but stayed buried."

**Fix shipped 2026-05-29:**
- **PR #1642 (merged)** — added "AI Engineering Foundations" to the AI tab sidebar, between "AI Foundations" (literacy) and "AI-Native Work" (applied). Build-verified, 2133 pages.
- **PR #1644** — module-level "Go deeper" cross-links from 10 neighbor modules to the spine (this ADR only specified the 3 *index*-level cross-links; #1644 extends them down to individual modules across both the `ai/` and `ai-ml-engineering/` trees). Additive only (20 insertions, 0 deletions); codex cross-family review in progress at time of writing.

### Net status of #1639
Consolidation approach (keep tracks distinct + redirect orphans + cross-link) was correct and is **done**. With the sidebar fix, the canonical home is now discoverable. Remaining optional polish (not blockers; for user to weigh on return):
- The 3 redirect stubs still appear as near-empty entries in their sidebars. Could be removed entirely in favor of Starlight `redirects` in `astro.config.mjs` for a cleaner UX (changes URLs → slightly more consequential, hence flagged not auto-done).
- Consider a one-line pointer to the spine from the **AI/ML Engineering** tab hub (the spine lives in the *AI* tab; the two tabs are bridged only by cross-links today).

**Lesson:** a "consolidation" audit must include a **reachability check** (is the canonical target in the sidebar / nav?), not just a duplication check. Redirecting to an unreachable target hides the target instead of surfacing it.
