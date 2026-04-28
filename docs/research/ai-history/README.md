# AI History Research Wiki

## Status Board

This directory contains the operational research files for the definitive 68-chapter AI History Epic.

- **Golden Research (Parts 1-2, Chapters 1-10):** Currently under revision based on cross-family review (downgraded to `reviewing` while we convert to claim-level anchoring and resolve factual disputes).
- **Part 3 (The Birth of Symbolic AI):** Ch11-14 dual-cleared `prose_ready` 2026-04-28; Ch15-16 next.
- **Part 4 (The First Winter):** Ch17-23 cross-family cleared for capped prose drafting; Ch21 carries a Yellow-caveated Bachant/McDermott mirror-source guardrail.
- **Part 5 (The Mathematical Resurrection):** Ch24-28 prose `accepted`; Ch29-31 in `prose_review`.

All drafting is paused for any chapter whose contract is not at `prose_ready` or beyond.

The team workflow is maintained in `TEAM_WORKFLOW.md`. It defines the gates between research contracts, gap analysis, anchor extraction, prose readiness, drafting, and cross-family review.

## Structure

*   `source-catalog.md`: Shared bibliography for recurring sources (e.g., Hodges, Gleick, Dyson).
*   `chapters/`: The 68 chapter skeletons. Each must hit the KubeDojo sourcing standard (claim-level anchors, page/section references, independent confirmation) before unlocking for prose drafting.

## Role Split (effective 2026-04-28)

After Gemini self-admitted to systemic URL/anchor hallucination across his prior research work (epic commit `03640e20`, Issue #421), research duties were taken away from Gemini and redistributed:

- **Claude — research lead.** Owns the chapter contracts (brief.md, sources.md, scene-sketches.md, timeline.md, people.md, infrastructure-log.md, open-questions.md, status.yaml) for Parts 1, 2, 3, 6, 7, 9. Extracts anchors via `curl` + `pdftotext` + `pdfgrep` directly. Pulls Codex in as a helper for archive-blocked or scanned-PDF cases that need shell tooling Claude doesn't have on the path.
- **Codex — research lead.** Owns the chapter contracts for Parts 4, 5, 8. Continues to draft prose for Codex-authored chapters and as the prose drafter for Part 3 (Claude expands).
- **Gemini — gap auditor + prose drafter.** Stops touching sources entirely. Continues to gap-audit every chapter (his strength: detecting narrative gaps, missing scenes, capacity-plan honesty). Drafts first-pass prose for Parts 1, 2, 6, 7 from a Claude-built contract; Claude expands the draft to full depth.
- **Cross-family verdict** rule unchanged: every chapter requires a `READY_TO_DRAFT` or `READY_TO_DRAFT_WITH_CAP` verdict from BOTH cross-family reviewers (one not from the author's family) before drafting unlocks.

Why the split: Gemini fabricated URLs and page anchors; Codex's shell tooling extracts real anchors; Claude has the same tooling and integration discipline. Gemini's drafting and gap-audit value remains real — sourcing was the broken seam.

## Ownership & Tracking Issues

Coordination happens across 9 Part Tracking issues linked to Epic #394. The "Research" column owns the contract; the "Prose" column owns first-draft writing; both go through cross-family review:

| Part | Issue | Era | Research lead | Prose drafter |
|---|---|---|---|---|
| 1 | [#399](https://github.com/kube-dojo/kube-dojo.github.io/issues/399) | The Mathematical Foundations (Ch 1-5) | **Claude** (was Gemini) | **Gemini** → Claude expansion |
| 2 | [#400](https://github.com/kube-dojo/kube-dojo.github.io/issues/400) | The Analog Dream & Digital Blank Slate (Ch 6-10) | **Claude** (was Gemini) | **Gemini** → Claude expansion |
| 3 | [#401](https://github.com/kube-dojo/kube-dojo.github.io/issues/401) | The Birth of Symbolic AI (Ch 11-16) | **Claude** | **Codex** → Claude expansion |
| 4 | [#402](https://github.com/kube-dojo/kube-dojo.github.io/issues/402) | The First Winter (Ch 17-23) | **Codex** | **Codex** |
| 5 | [#403](https://github.com/kube-dojo/kube-dojo.github.io/issues/403) | The Mathematical Resurrection (Ch 24-31) | **Codex** | **Codex** |
| 6 | [#404](https://github.com/kube-dojo/kube-dojo.github.io/issues/404) | The Rise of Data & Distributed Compute (Ch 32-40) | **Claude** (was Gemini) | **Gemini** → Claude expansion |
| 7 | [#405](https://github.com/kube-dojo/kube-dojo.github.io/issues/405) | The Deep Learning Revolution & GPU Coup (Ch 41-49) | **Claude** (was Gemini) | **Gemini** → Claude expansion |
| 8 | [#406](https://github.com/kube-dojo/kube-dojo.github.io/issues/406) | The Transformer, Scale & Open Source (Ch 50-58) | **Codex** | **Codex** |
| 9 | [#407](https://github.com/kube-dojo/kube-dojo.github.io/issues/407) | The Product Shock & Physical Limits (Ch 59-68) | **Claude** | **Claude** |

Note: The 630 changed files in the original PR include automatically generated placeholder directories for the 68 chapters to ensure proper boundaries. These placeholders are intentional and expected in diff reviews.
