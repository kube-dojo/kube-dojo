# Citation-Aware Module Page — Design Proposal

**Status:** Proposal (for review)
**Issue:** #273
**Governs:** `docs/citation-upgrade-plan.md` (citation policy), `scripts/check_citations.py` (gate)
**Date:** 2026-04-18

## Problem

We are rewriting every module with citations. Inline sources make modules authoritative, but a naive implementation produces academic clutter: `[^1]` markers scattered through prose, a wall of references at the bottom, and a reading experience that buries the pedagogy under footnote noise.

The module page must stay readable for a learner skimming for concepts **and** serve a researcher who wants to check a claim — without asking either reader to pay for the other.

## Decision

**Three-tab module layout using Starlight's built-in `<Tabs syncKey>`**: Theory / Practice / Citations.

- **Theory tab** = the teaching content: Why This Module Matters, core sections (with ASCII/Mermaid diagrams, tables, code, worked examples), Did You Know (4 facts), Common Mistakes table, **inline active-learning prompts**, and inline citation markers (`[^1]`).
- **Practice tab** = assessment only: Quiz (6–8 scenario-based questions with `<details>` answers) and Hands-On Exercise (`- [ ]` success criteria).
- **Citations tab** = full bibliography: every inline `[^n]` resolves here, with URL, author/org, date accessed, and a 1–2 sentence why-we-cite-this note.

The three tabs share a `syncKey` so a learner's choice persists across modules.

## Why tabs (and why not the alternatives)

We considered three patterns. Tabs won on the "citations are first-class" goal without sacrificing readability.

| Pattern | Theory readability | Citations visibility | Mobile | Verdict |
|---|---|---|---|---|
| **3-tab (proposed)** | Clean — no bibliography wall | First-class (own tab + deep link) | Works (tab bar is compact) | **Chosen** |
| Single page + sticky TOC | Cluttered when bibliography is long | Buried at bottom, TOC helps but doesn't elevate | Sticky TOC eats screen | Rejected |
| Single page + collapsible sources | Clean while collapsed | Hidden by default — fails "first-class" goal | Works but defeats the purpose | Rejected |

**Single-page sticky-TOC** was the closest runner-up. We rejected it because a 30–50-source bibliography at the end of a long module **trains readers to skip it**. Making Citations a tab forces a deliberate choice to view it, which is the point.

## The four non-obvious modifications

A naive Theory/Practice/Citations split would degrade the pedagogy. Four deliberate modifications protect it:

### 1. Active-learning prompts stay in Theory, not Practice

Inline prompts ("Before you read the next section — predict what happens when X") are part of the **learning flow**, not the assessment. Moving them to Practice breaks the scaffold. Practice tab is reserved for **graded-style** assessment (quiz + hands-on).

### 2. Did You Know and Common Mistakes stay in Theory

Both are part of the conceptual frame. Did You Know reinforces retention during reading. Common Mistakes pre-empts misconceptions. Both would feel misplaced in Practice.

### 3. Inline `[^n]` markers in Theory deep-link into the Citations tab

Clicking `[^1]` in Theory switches to the Citations tab and scrolls to the matching entry (anchor `#cite-1`). Browser back button returns to Theory at the marker. This gives the researcher a 1-click path without forcing the skim-reader to acknowledge citations exist.

### 4. Deep-link via `?tab=citations` (and `&cite=1` to scroll)

Any module URL with `?tab=citations` opens on the Citations tab. `?tab=citations&cite=7` additionally scrolls to citation 7. This is how external references (PR reviews, study-group discussions, LLM answers) can link directly to a source without wrapping the whole module in context.

## Mobile

Starlight tabs collapse to a horizontal scrollable bar on narrow viewports — three labels fit without wrapping. The Citations tab on mobile uses a simple list (no two-column layout) with tap-to-expand for long "why-we-cite-this" notes. Tested mentally against 360px; no layout gymnastics needed.

## Component sketch

Pseudo-Astro (actual component will live in `src/components/ModuleTabs.astro`):

```astro
---
import { Tabs, TabItem } from '@astrojs/starlight/components';
const { theory, practice, citations } = Astro.props;
---
<Tabs syncKey="module-view">
  <TabItem label="Theory">
    <Fragment set:html={theory} />
  </TabItem>
  <TabItem label="Practice">
    <Fragment set:html={practice} />
  </TabItem>
  <TabItem label="Citations">
    <Fragment set:html={citations} />
  </TabItem>
</Tabs>
```

A small client script reads `?tab=` on load and activates the right tab. `[^n]` links get a click handler that switches the tab and scrolls.

## Content contract

Every module author (human or pipeline) must produce three content blocks. The split is driven by section headings, so existing modules migrate mechanically:

| Tab | Sections included |
|---|---|
| Theory | Learning Outcomes, Why This Module Matters, core sections (H2s), Did You Know, Common Mistakes, Next Module link |
| Practice | Quiz, Hands-On Exercise |
| Citations | Bibliography (generated from inline `[^n]` markers + metadata block at top of module) |

The Citations bibliography is **generated from frontmatter**, not hand-written per module. Frontmatter declares:

```yaml
citations:
  - id: 1
    url: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
    author: Kubernetes Authors
    accessed: 2026-04-18
    note: Canonical Deployment reference for rolling update semantics.
  - id: 2
    url: ...
```

A build-time integration walks `[^n]` markers in the Theory block and resolves them against `frontmatter.citations`. Missing ids fail the build (same gate as broken internal links).

## Migration plan for ~600 modules

Two-phase migration. Phase 1 is mechanical and safe; phase 2 is pipeline-driven and incremental.

### Phase 1 — Structural split (one-shot script)

`scripts/migrate_to_tabs.py` operates on every `.md` under `src/content/docs/`:

1. Parse the module. Split on known section headings (`## Quiz`, `## Hands-On Exercise`).
2. Everything before Quiz → Theory block. Quiz + Hands-On → Practice block.
3. Citations block = empty frontmatter `citations: []` for modules that don't have inline markers yet.
4. Rewrite the module body to use `<ModuleTabs>` wrapping three `<Fragment>` blocks.
5. Run `npm run build` — fail loud on any regression.

This is non-lossy: no module loses content, only the wrapping changes. A module with no citations yet renders an empty Citations tab (acceptable; Phase 2 fills it).

### Phase 2 — Citation fill (pipeline-driven, per-track)

Handled by the automated citation pipeline (issue #279): Gemini 3.1 Pro writes with citation seeds, Codex fact-checks. Each module that passes the citation gate gets its `frontmatter.citations` block populated and its Theory body gets `[^n]` markers inserted.

Starting track: AI foundations (seeds already staged in `docs/citation-seeds-ai-foundations.md`).

### Rollback

Phase 1 is a single commit. `git revert` restores flat-page rendering. Phase 2 is per-module so rollback is per-module.

## Open questions (for reviewer)

These are not blockers for merging the proposal, but the implementer should resolve them before writing `ModuleTabs.astro`:

1. **Print view**: when a user prints a module, do all three tabs render as sequential sections? (Recommendation: yes — use `@media print` to unhide all `<TabItem>` content.)
2. **Search indexing**: Pagefind indexes visible content. Do we force-index Citations tab content even when inactive? (Recommendation: yes — Citations content is text-valuable; use a hidden-but-indexed pattern.)
3. **Ukrainian sync**: do UK translations get the same three-tab split automatically via Phase 1? (Recommendation: yes — the script runs on `src/content/docs/uk/` with the same heading rules.)
4. **Progress tracking**: the Supabase progress migration (#157) tracks "module completed". Does "completed" require visiting Practice, or just Theory? (Recommendation: Practice — completion should imply the learner at least saw the quiz.)

## Acceptance checklist for implementation (tracked in a follow-up issue, not this one)

- [ ] `src/components/ModuleTabs.astro` component
- [ ] `scripts/migrate_to_tabs.py` migration script + dry-run mode
- [ ] Frontmatter citations schema + build-time resolver
- [ ] Deep-link handler for `?tab=` and `&cite=`
- [ ] Print stylesheet unhides all tabs
- [ ] Pagefind index covers all tabs
- [ ] Phase 1 migration PR for English modules
- [ ] Phase 1 migration PR for UK translations
- [ ] Mobile QA on 360px / 768px / 1280px viewports
- [ ] A11y pass: keyboard navigation between tabs, ARIA labels verified
