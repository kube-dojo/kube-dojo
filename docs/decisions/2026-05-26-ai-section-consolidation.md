# 2026-05-26 — AI Section Consolidation (Phase 4 of #1530)

## Status
Proposed — orchestrator review pending

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
