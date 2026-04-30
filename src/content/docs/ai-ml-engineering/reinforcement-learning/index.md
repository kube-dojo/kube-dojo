---
title: "Reinforcement Learning"
description: "RL practitioner foundations — PPO/DQN/SAC, offline RL, imitation learning."
slug: ai-ml-engineering/reinforcement-learning
sidebar:
  order: 0
  label: "Reinforcement Learning"
---

> **AI/ML Engineering Track**

## Overview

Reinforcement Learning is the slice of machine learning where an agent learns by acting in an environment and observing the consequences, instead of being shown labeled examples. This section is for practitioners who need a working understanding of modern RL — what algorithm to reach for, how to wire it up against an environment, how to evaluate it, and how to debug it when training silently fails.

The path here stays grounded in tools that are actually used in production and in research labs: Gymnasium for environments, Stable-Baselines3 for the standard online algorithms (PPO, DQN, SAC, A2C), and the offline / imitation-learning toolkits for the much more common case where you cannot let an agent freely explore.

If you have not yet worked through `machine-learning/` or `deep-learning/`, do that first — most RL pain in practice is just supervised-learning pain (overfitting, leakage, brittle features) wearing a different hat.

## Modules

| # | Module | Status |
|---|---|---|
| 1.1 | RL Practitioner Foundations | Coming soon (Phase 2) |
| 2.1 | Offline RL & Imitation Learning | Coming soon (Phase 3) |

See the full plan in [issue #677](https://github.com/kube-dojo/kube-dojo.github.io/issues/677).

## Cross-Links

- For tabular and supervised foundations: [Machine Learning](../machine-learning/)
- For deep network building blocks used inside policy and value networks: [Deep Learning Foundations](../deep-learning/)
- For RLHF and preference optimization on language models: [Advanced GenAI & Safety](../advanced-genai/)
