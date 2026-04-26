# AI History — Research Wiki

Working space for the multi-agent AI history book (epic [#394](https://github.com/kube-dojo/kube-dojo.github.io/issues/394)).

This is **internal research material**, not publishable prose. It feeds the chapter contracts that gate writing. Final prose lives under `src/content/docs/ai-history/`.

## Status board

| # | Chapter | Owner | Reviewer | Status |
|---|---|---|---|---|
| 1 | The Dream Before the Machine (Cybernetics → Dartmouth) | Gemini | Codex | researching |
| 2 | The Summer AI Named Itself (Dartmouth + Cold War) | Claude | Gemini | researching |
| 3 | The Perceptron and the First Hype Cycle | Claude | Gemini | researching |
| 4 | Rules, Experts, and the Knowledge Bottleneck | Claude | Gemini | researching |
| 5 | The Statistical Underground | Codex | Claude | researching |
| 6 | Data Becomes Infrastructure (ImageNet) | Gemini | Codex | researching |
| 7 | The GPU Coup (CUDA / AlexNet) | Codex | Claude | researching |
| 8 | Attention, Scale, and the Language Turn | Gemini | Codex | researching |
| 9 | The Product Shock (GPT-2 → ChatGPT) | Claude | Gemini | researching |
| 10 | The New Industrial Stack (K8s, inference economics, regulation) | Codex | Claude | researching |

Each chapter's `status.yaml` is the source of truth — this table is a hand-summary.

Status values: `researching` → `verified` → `drafting` → `reviewing` → `done`.

## Workflow gate

Prose drafting in `src/content/docs/ai-history/` cannot start until **both** of the following are signed off by the cross-family reviewer:

- `chapters/ch-NN-slug/brief.md` — chapter contract: thesis, scope, scenes outline, citation bar
- `chapters/ch-NN-slug/sources.md` — annotated bibliography with verification colors on every source the chapter will lean on

Sign-off lands as a comment on issue [#394](https://github.com/kube-dojo/kube-dojo.github.io/issues/394) referencing the chapter slug.

## Sourcing standard

- 2-3 independent sources per scene-level passage
- ≥ 1 primary (paper, memo, transcript, oral history)
- ≥ 1 high-quality secondary (contemporary tech journalism or verified retrospective)
- No invented dialogue or internal states
- Verification colors:
  - **Green** — ≥ 2 independent confirmations from credible sources
  - **Yellow** — 1 source, plausible, no contradicting evidence
  - **Red** — uncited / single source / actively disputed → cannot be used in prose without resolution

## Master timeline

Populated as chapters lock their `timeline.md`. Cross-chapter date conflicts get resolved here.

| Year | Event | Chapter | Verification |
|---|---|---|---|
| _to be populated_ | | | |

## Cross-chapter sources

See [`source-catalog.md`](source-catalog.md). Sources cited in 2+ chapters live there to avoid duplicate annotation.

## Public output spec (reference)

- ~1500 lines of prose per chapter (excluding code/diagrams)
- Public route under `src/content/docs/ai-history/` (NEW location)
- Module-1.1 at `ai-ml-engineering/history/module-1.1-history-of-ai-machine-learning.md` is UNTOUCHED and stays as the technical-timeline appendix
