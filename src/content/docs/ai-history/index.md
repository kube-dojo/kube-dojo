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

- Several Part 2/6/7 chapters have **legacy prose merged from the pre-2026 research pipeline**; their lifecycle reads `researching` until each chapter's claim-level-anchored research contract lands on `main` and the prose is re-drafted from it.
- Parts 1, 2, 4, and 5 are fully shipped (verified-anchor research + prose merged). Part 3 is 4/6 shipped; Ch15 prose is pending and Ch16 is still researching.
- Active per-chapter pull requests are not reflected here until merged. See the [open PRs](https://github.com/kube-dojo/kube-dojo.github.io/pulls) for in-flight work.
- The book's tracking epic is [#394](https://github.com/kube-dojo/kube-dojo.github.io/issues/394).

## Role split (effective 2026-04-28 PM)

After Gemini self-admitted to systemic URL/anchor hallucination across his prior research work, sourcing duties moved off Gemini. After empirical comparison of Codex-drafted vs Claude-drafted prose this session, the writer seat consolidated to Codex; Claude's role is now purely orchestration + source-fidelity review.

- **Codex** is the writer and researcher for ALL remaining chapters. Drives Parts 8 and 9 end-to-end autonomously (research → prose → review-fix → merge). Drives the writer/researcher seat for Parts 3, 6, 7 too — but Claude orchestrates those (firing pipelines, running reviews, applying fix-passes, merge dance). Same shell tooling for research (`pdftotext`, `pdfgrep`, `curl`). Sequential dispatches per `feedback_codex_dispatch_sequential.md`.
- **Claude** orchestrates Parts 3, 6, 7 + serves as cross-family source-fidelity reviewer on every chapter. No drafting. No primary research. The credit-burn that triggered the 2026-04-28 evening hand-off was Claude doing research; this policy locks that off.
- **Gemini** is the prose-quality cross-family reviewer (Codex is conflicted as author) + gap auditor. Never cites URLs, page anchors, or DOIs.
- **Cross-family verdict** rule unchanged: every chapter needs a `READY_TO_DRAFT` or `READY_TO_DRAFT_WITH_CAP` from BOTH cross-family reviewers before drafting unlocks.

Already-merged Claude-authored research and prose (Parts 1, 2, 3 Ch11–14, plus the Part 6 supersede research PRs #471–#476) stays as-is and follows the standard verdict-pass-then-merge path. After those land, Claude does no more drafting or research.

## Part 1 — The Mathematical Foundations (1840s–1940s)

Research: **Claude** · Prose: **Gemini → Claude expansion** · Tracking: [#399](https://github.com/kube-dojo/kube-dojo.github.io/issues/399)

Proving that human logic, reasoning, and probability can be formalized into mechanical algebra.

| Ch | Title | Lifecycle | Drafted |
|---:|---|---|---|
| 1 | The Laws of Thought | accepted | [yes](./ch-01-the-laws-of-thought/) |
| 2 | The Universal Machine | accepted | [yes](./ch-02-the-universal-machine/) |
| 3 | The Physical Bridge | accepted | [yes](./ch-03-the-physical-bridge/) |
| 4 | The Statistical Roots | accepted | [yes](./ch-04-the-statistical-roots/) |
| 5 | The Neural Abstraction | accepted | [yes](./ch-05-the-neural-abstraction/) |

## Part 2 — The Analog Dream & Digital Blank Slate (1940s–1950s)

Research: **Claude** · Prose: **Gemini → Claude expansion** · Tracking: [#400](https://github.com/kube-dojo/kube-dojo.github.io/issues/400)

The transition from biology-inspired analog hardware to von Neumann digital architectures.

| Ch | Title | Lifecycle | Drafted |
|---:|---|---|---|
| 6 | The Cybernetics Movement | accepted | [yes](./ch-06-the-cybernetics-movement/) |
| 7 | The Analog Bottleneck | accepted | [yes](./ch-07-the-analog-bottleneck/) |
| 8 | The Stored Program | accepted | [yes](./ch-08-the-stored-program/) |
| 9 | The Memory Miracle | accepted | [yes](./ch-09-the-memory-miracle/) |
| 10 | The Imitation Game | accepted | [yes](./ch-10-the-imitation-game/) |

## Part 3 — The Birth of Symbolic AI & Early Optimism (1950s–1960s)

Research: **Claude (Ch11–14, merged) → Codex (Ch15–16)** · Prose: **Codex** · Orchestrator: **Claude** · Tracking: [#401](https://github.com/kube-dojo/kube-dojo.github.io/issues/401)

The Dartmouth consensus, early search algorithms, and military funding.

| Ch | Title | Lifecycle | Drafted |
|---:|---|---|---|
| 11 | The Summer AI Named Itself | accepted | [yes](./ch-11-the-summer-ai-named-itself/) |
| 12 | Logic Theorist & GPS | accepted | [yes](./ch-12-logic-theorist-gps/) |
| 13 | The List Processor | accepted | [yes](./ch-13-the-list-processor/) |
| 14 | The Perceptron | accepted | [yes](./ch-14-the-perceptron/) |
| 15 | The Gradient Descent Concept | prose_ready (cap 4,900) | no |
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
| 21 | The Rule-Based Fortune | accepted | yes |
| 22 | The LISP Machine Bubble | accepted | yes |
| 23 | The Japanese Threat | accepted | yes |

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
| 29 | Support Vector Machines (SVMs) | accepted | [yes](./ch-29-support-vector-machines/) |
| 30 | The Statistical Underground | accepted | [yes](./ch-30-the-statistical-underground/) |
| 31 | Reinforcement Learning Roots | accepted | [yes](./ch-31-reinforcement-learning-roots/) |

## Part 6 — The Rise of Data & Distributed Compute (1990s–2000s)

Research: **Codex** · Prose: **Codex** · Orchestrator: **Claude** · Tracking: [#404](https://github.com/kube-dojo/kube-dojo.github.io/issues/404)

The shift to empiricism, enabled by the internet and cluster computing.

| Ch | Title | Lifecycle | Drafted |
|---:|---|---|---|
| 32 | The DARPA SUR Program | prose_ready (cap 5,600) | [yes](./ch-32-the-darpa-sur-program/) |
| 33 | Deep Blue | prose_ready (cap 4,900) | [yes](./ch-33-deep-blue/) |
| 34 | The Accidental Corpus | prose_ready (cap 5,200) | [yes](./ch-34-the-accidental-corpus/) |
| 35 | Indexing the Mind | prose_ready (cap 4,300) | [yes](./ch-35-indexing-the-mind/) |
| 36 | The Multicore Wall | prose_ready (cap 5,000) | [yes](./ch-36-the-multicore-wall/) |
| 37 | Distributing the Compute | prose_ready (cap 5,000) | [yes](./ch-37-distributing-the-compute/) |
| 38 | The Human API | researching | [yes](./ch-38-the-human-api/) |
| 39 | The Vision Wall | researching | [yes](./ch-39-the-vision-wall/) |
| 40 | Data Becomes Infrastructure | researching | [yes](./ch-40-data-becomes-infrastructure/) |

## Part 7 — The Deep Learning Revolution & GPU Coup (2010s)

Research: **Codex** · Prose: **Codex** · Orchestrator: **Claude** · Tracking: [#405](https://github.com/kube-dojo/kube-dojo.github.io/issues/405)

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
| 50 | Attention Is All You Need | prose_ready | no |
| 51 | The Open Source Distribution Layer | prose_ready | no |
| 52 | Bidirectional Context | prose_ready | no |
| 53 | The Dawn of Few-Shot Learning | prose_ready (cap 5,000) | no |
| 54 | The Hub of Weights | prose_ready (cap 4,800) | no |
| 55 | The Scaling Laws | prose_ready (cap 5,500) | no |
| 56 | The Megacluster | researching | no |
| 57 | The Alignment Problem | researching | no |
| 58 | The Math of Noise | researching | no |

## Part 9 — The Product Shock & Physical Limits (2022–Present)

Research: **Codex** · Prose: **Codex** · Tracking: [#407](https://github.com/kube-dojo/kube-dojo.github.io/issues/407)

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
| `accepted` (drafted, all reviews cleared) | 29 |
| `prose_review` (drafted, in review) | 0 |
| `prose_ready` (contract dual-cleared, awaiting prose draft) | 13 |
| `capacity_plan_anchored` (contract anchored, awaiting verdict) | 0 |
| `researching` with prose merged on legacy contract | 5 |
| `researching` (no prose yet) | 21 |
| **Total** | **68** |
