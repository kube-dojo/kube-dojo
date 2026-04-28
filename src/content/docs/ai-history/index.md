---
title: "History of AI"
description: "A 68-chapter history of artificial intelligence, from Boole's logic to today's frontier models. Built collaboratively by Claude, Codex, and Gemini under team workflow rules."
sidebar:
  order: 0
---

# History of AI

A 68-chapter book about how artificial intelligence actually came to be — the math, the hardware, the funding, the people, and the constraints that shaped each era. The book is being written collaboratively by Claude, Codex, and Gemini under a strict cross-family review protocol designed to prevent overclaiming, fabrication, and lone-genius framing.

This page is the live status board. The lifecycle column reflects what is on the `main` branch — not what is in flight on per-chapter PRs.

## Lifecycle

Each chapter passes through these stages before the prose lands:

| Stage | Meaning |
|---|---|
| `researching` | Chapter shell only — no contract yet, or contract being reworked |
| `capacity_plan_drafted` | `brief.md` has a Prose Capacity Plan but layers do not yet reference page anchors |
| `capacity_plan_anchored` | Every plan layer references at least one page anchor in `sources.md` |
| `prose_ready` | Both cross-family reviewers cleared the contract; drafting may begin |
| `drafting` | Prose in flight on a `<author>/394-chNN-prose` branch |
| `prose_review` | Drafted, under cross-family prose review |
| `accepted` | Cleared all reviews and merged to `main` |

Honesty over output is the highest rule. When verified evidence cannot honestly support 4,000+ words, the chapter caps at its natural length. See [`TEAM_WORKFLOW.md`](https://github.com/kube-dojo/kube-dojo.github.io/blob/main/docs/research/ai-history/TEAM_WORKFLOW.md) for the full rules.

## Notes on the current state

- Several chapters have **legacy prose merged from the pre-2026 research pipeline** but their lifecycle still reads `researching` because the contract is being re-built under the new claim-level anchoring standard. Parts 1–2 are in active re-research; Parts 6–7 will follow.
- Active per-chapter pull requests are not reflected here until merged. See the [open PRs](https://github.com/kube-dojo/kube-dojo.github.io/pulls) for in-flight work.
- The book's tracking epic is [#394](https://github.com/kube-dojo/kube-dojo.github.io/issues/394).

## Role split (effective 2026-04-28)

After Gemini self-admitted to systemic URL/anchor hallucination across his prior research work, sourcing duties moved off Gemini:

- **Claude** owns the research contract for Parts 1, 2, 3, 6, 7, 9 (anchor extraction directly via `curl` + `pdftotext`).
- **Codex** owns the research contract for Parts 4, 5, 8 and helps with archive-blocked or scanned-PDF anchors when Claude is stuck. Continues as prose drafter for Part 3.
- **Gemini** stops touching sources entirely. Becomes the gap auditor on every chapter and the first-draft prose writer for Parts 1, 2, 6, 7 (Claude expands the draft).
- **Cross-family verdict** rule unchanged: every chapter needs a `READY_TO_DRAFT` or `READY_TO_DRAFT_WITH_CAP` from BOTH cross-family reviewers before drafting unlocks.

## Part 1 — The Mathematical Foundations (1840s–1940s)

Research: **Claude** · Prose: **Gemini → Claude expansion** · Tracking: [#399](https://github.com/kube-dojo/kube-dojo.github.io/issues/399)

Proving that human logic, reasoning, and probability can be formalized into mechanical algebra.

| Ch | Title | Lifecycle | Drafted |
|---:|---|---|---|
| 1 | The Laws of Thought | researching | [yes](./ch-01-the-laws-of-thought/) |
| 2 | The Universal Machine | researching | [yes](./ch-02-the-universal-machine/) |
| 3 | The Physical Bridge | researching | [yes](./ch-03-the-physical-bridge/) |
| 4 | The Statistical Roots | researching | [yes](./ch-04-the-statistical-roots/) |
| 5 | The Neural Abstraction | researching | [yes](./ch-05-the-neural-abstraction/) |

## Part 2 — The Analog Dream & Digital Blank Slate (1940s–1950s)

Research: **Claude** · Prose: **Gemini → Claude expansion** · Tracking: [#400](https://github.com/kube-dojo/kube-dojo.github.io/issues/400)

The transition from biology-inspired analog hardware to von Neumann digital architectures.

| Ch | Title | Lifecycle | Drafted |
|---:|---|---|---|
| 6 | The Cybernetics Movement | researching | [yes](./ch-06-the-cybernetics-movement/) |
| 7 | The Analog Bottleneck | researching | [yes](./ch-07-the-analog-bottleneck/) |
| 8 | The Stored Program | researching | [yes](./ch-08-the-stored-program/) |
| 9 | The Memory Miracle | researching | [yes](./ch-09-the-memory-miracle/) |
| 10 | The Imitation Game | researching | [yes](./ch-10-the-imitation-game/) |

## Part 3 — The Birth of Symbolic AI & Early Optimism (1950s–1960s)

Research: **Claude** · Prose: **Codex → Claude expansion** · Tracking: [#401](https://github.com/kube-dojo/kube-dojo.github.io/issues/401)

The Dartmouth consensus, early search algorithms, and military funding.

| Ch | Title | Lifecycle | Drafted |
|---:|---|---|---|
| 11 | The Summer AI Named Itself | prose_ready (cap 5,100) | no |
| 12 | Logic Theorist & GPS | prose_ready (cap 4,500) | no |
| 13 | The List Processor | prose_ready (cap 4,500) | no |
| 14 | The Perceptron | prose_ready (cap 4,500) | no |
| 15 | The Gradient Descent Concept | researching | no |
| 16 | The Cold War Blank Check | researching | no |

## Part 4 — The First Winter & The Shift to Knowledge (1970s–1980s)

Research: **Codex** · Prose: **Codex** · Tracking: [#402](https://github.com/kube-dojo/kube-dojo.github.io/issues/402)

The failure of early neural networks and the rise of hard-coded Expert Systems.

| Ch | Title | Lifecycle | Drafted |
|---:|---|---|---|
| 17 | The Perceptron's Fall | accepted | yes |
| 18 | The Lighthill Devastation | accepted | yes |
| 19 | Rules, Experts, and the Knowledge Bottleneck | accepted | yes |
| 20 | Project MAC | accepted | yes |
| 21 | The Rule-Based Fortune | capacity_plan_anchored | no |
| 22 | The LISP Machine Bubble | capacity_plan_anchored | no |
| 23 | The Japanese Threat | capacity_plan_anchored | no |

## Part 5 — The Mathematical Resurrection (1980s–1990s)

Research: **Codex** · Prose: **Codex** · Tracking: [#403](https://github.com/kube-dojo/kube-dojo.github.io/issues/403)

The silent algorithmic breakthroughs that laid the foundation for modern Machine Learning.

| Ch | Title | Lifecycle | Drafted |
|---:|---|---|---|
| 24 | The Math That Waited for the Machine | accepted | [yes](./ch-24-the-math-that-waited-for-the-machine/) |
| 25 | The Universal Approximation Theorem (1989) | accepted | [yes](./ch-25-the-universal-approximation-theorem-1989/) |
| 26 | Bayesian Networks | accepted | [yes](./ch-26-bayesian-networks/) |
| 27 | The Convolutional Breakthrough | accepted | [yes](./ch-27-the-convolutional-breakthrough/) |
| 28 | The Second AI Winter | accepted | [yes](./ch-28-the-second-ai-winter/) |
| 29 | Support Vector Machines (SVMs) | prose_review | [yes](./ch-29-support-vector-machines/) |
| 30 | The Statistical Underground | prose_review | [yes](./ch-30-the-statistical-underground/) |
| 31 | Reinforcement Learning Roots | prose_review | [yes](./ch-31-reinforcement-learning-roots/) |

## Part 6 — The Rise of Data & Distributed Compute (1990s–2000s)

Research: **Claude** · Prose: **Gemini → Claude expansion** · Tracking: [#404](https://github.com/kube-dojo/kube-dojo.github.io/issues/404)

The shift to empiricism, enabled by the internet and cluster computing.

| Ch | Title | Lifecycle | Drafted |
|---:|---|---|---|
| 32 | The DARPA SUR Program | researching | [yes](./ch-32-the-darpa-sur-program/) |
| 33 | Deep Blue | researching | [yes](./ch-33-deep-blue/) |
| 34 | The Accidental Corpus | researching | [yes](./ch-34-the-accidental-corpus/) |
| 35 | Indexing the Mind | researching | [yes](./ch-35-indexing-the-mind/) |
| 36 | The Multicore Wall | researching | [yes](./ch-36-the-multicore-wall/) |
| 37 | Distributing the Compute | researching | [yes](./ch-37-distributing-the-compute/) |
| 38 | The Human API | researching | [yes](./ch-38-the-human-api/) |
| 39 | The Vision Wall | researching | [yes](./ch-39-the-vision-wall/) |
| 40 | Data Becomes Infrastructure | researching | [yes](./ch-40-data-becomes-infrastructure/) |

## Part 7 — The Deep Learning Revolution & GPU Coup (2010s)

Research: **Claude** · Prose: **Gemini → Claude expansion** · Tracking: [#405](https://github.com/kube-dojo/kube-dojo.github.io/issues/405)

The repurposing of graphics cards for massive parallel matrix multiplication.

| Ch | Title | Lifecycle | Drafted |
|---:|---|---|---|
| 41 | The Graphics Hack | researching | [yes](./ch-41-the-graphics-hack/) |
| 42 | CUDA | researching | no |
| 43 | The ImageNet Smash | researching | [yes](./ch-43-the-imagenet-smash/) |
| 44 | The Latent Space | researching | no |
| 45 | Generative Adversarial Networks | researching | no |
| 46 | The Recurrent Bottleneck | researching | no |
| 47 | The Depths of Vision | researching | no |
| 48 | AlphaGo | researching | no |
| 49 | The Custom Silicon | researching | no |

## Part 8 — The Transformer, Scale & Open Source (2017–2022)

Research: **Codex** · Prose: **Codex** · Tracking: [#406](https://github.com/kube-dojo/kube-dojo.github.io/issues/406)

Scaling laws, Attention, and the democratization of AI through open weights.

| Ch | Title | Lifecycle | Drafted |
|---:|---|---|---|
| 50 | Attention Is All You Need | researching | no |
| 51 | The Open Source Distribution Layer | researching | no |
| 52 | Bidirectional Context | researching | no |
| 53 | The Dawn of Few-Shot Learning | researching | no |
| 54 | The Hub of Weights | researching | no |
| 55 | The Scaling Laws | researching | no |
| 56 | The Megacluster | researching | no |
| 57 | The Alignment Problem | researching | no |
| 58 | The Math of Noise | researching | no |

## Part 9 — The Product Shock & Physical Limits (2022–Present)

Research: **Claude** · Prose: **Claude** · Tracking: [#407](https://github.com/kube-dojo/kube-dojo.github.io/issues/407)

Consumer adoption, edge constraints, and AI transitioning to heavy industry.

| Ch | Title | Lifecycle | Drafted |
|---:|---|---|---|
| 59 | The Product Shock | researching | no |
| 60 | The Physics of Scale | researching | no |
| 61 | Inference Economics | researching | no |
| 62 | The Edge Compute Bottleneck | researching | no |
| 63 | The Open Weights Rebellion | researching | no |
| 64 | The Monopoly | researching | no |
| 65 | The Data Exhaustion Limit | researching | no |
| 66 | The Energy Grid Collision | researching | no |
| 67 | The Chip War | researching | no |
| 68 | The Infinite Datacenter | researching | no |

## Roll-up

| Stage | Count |
|---|---:|
| `accepted` (drafted, all reviews cleared) | 5 |
| `prose_review` (drafted, in review) | 3 |
| `prose_ready` (contract dual-cleared, awaiting prose draft) | 4 |
| `capacity_plan_anchored` (contract anchored, awaiting verdict) | 3 |
| `researching` with prose merged on legacy contract | 22 |
| `researching` (no prose yet) | 31 |
| **Total** | **68** |
