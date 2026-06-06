---
title: "Deep Learning Foundations"
description: "Deep learning from first principles: build a neural network and a scalar autograd engine in NumPy, cross the bridge to PyTorch, master the training loop, then climb through embeddings, attention, transformers, CNNs, RNNs, and a real end-to-end capstone."
slug: ai-ml-engineering/deep-learning
sidebar:
  order: 0
  label: "Deep Learning Foundations"
---

> **AI/ML Engineering Track** | Phase 9 · 27 modules · ~70–110 hours

## Overview

This section teaches deep learning the way it actually clicks: **from scratch first, framework second.** You build a working multi-layer perceptron — forward pass, loss, backprop, and a scalar autograd engine — in plain NumPy before you are allowed to `import torch`. Once the mechanics are no longer magic, you cross the bridge to PyTorch and learn to run reproducible training loops, diagnose why a network won't converge, and reason about numerical stability.

From there the section climbs the modern architecture stack one idea at a time — embeddings, residual connections, attention, and a transformer block you assemble by hand — then applies it across vision (CNNs), sequences (RNNs), and a capstone where you train a real network end-to-end. The final modules reach into self-supervised learning, graph neural networks, and the attention variants (RoPE, ALiBi) that power current frontier models.

Every module is taught at Bloom Level 3+ — derive it, implement it, debug it — not "remember the API." If the math feels intimidating, start with the warm-up (1.1.1); it assumes nothing beyond high-school calculus and rebuilds the rest.

## How This Section Is Organized

The 27 modules form one spine with five sub-chains. Work them roughly in order — each chain assumes the previous one.

### From-Scratch Foundations (NumPy)

Build the whole stack by hand — neuron, MLP, activations, losses, backprop, and a scalar autograd engine — so nothing in PyTorch is ever a black box.

| # | Module |
|---|--------|
| 1.1 | [NumPy, Pandas & Data Tooling for ML](/ai-ml-engineering/deep-learning/module-1.1-numpy-pandas-data-tooling/) |
| 1.1.1 | [Neural Network Math Warm-Up](/ai-ml-engineering/deep-learning/module-1.1.1-nn-math-warmup/) |
| 1.1.2 | [The Neuron & Perceptron from Scratch](/ai-ml-engineering/deep-learning/module-1.1.2-neuron-from-scratch/) |
| 1.1.3 | [Forward Propagation in Multi-Layer Perceptrons](/ai-ml-engineering/deep-learning/module-1.1.3-forward-propagation-mlp/) |
| 1.1.4 | [Activation Functions in Depth](/ai-ml-engineering/deep-learning/module-1.1.4-activation-functions/) |
| 1.1.5 | [Loss Functions & Output Heads](/ai-ml-engineering/deep-learning/module-1.1.5-loss-functions-output-heads/) |
| 1.1.6 | [Backprop by Hand for Dense Nets](/ai-ml-engineering/deep-learning/module-1.1.6-backprop-by-hand-dense-nets/) |
| 1.1.7 | [Tiny NumPy NN Lab: XOR to Fashion-MNIST](/ai-ml-engineering/deep-learning/module-1.1.7-tiny-numpy-nn-lab/) |
| 1.1.8 | [Computational Graphs & Scalar Autograd](/ai-ml-engineering/deep-learning/module-1.1.8-computational-graphs-scalar-autograd/) |

### PyTorch & the Training Loop

Port your NumPy engine to `torch`, then turn one gradient step into a reproducible run: initialization, optimizers, regularization, normalization, a diagnostics playbook, and numerical-stability discipline.

| # | Module |
|---|--------|
| 1.2 | [The PyTorch Bridge: From Your NumPy Engine to torch](/ai-ml-engineering/deep-learning/module-1.2-pytorch-fundamentals/) |
| 1.3 | [The Training Loop: From One Step to a Reproducible Run](/ai-ml-engineering/deep-learning/module-1.3-training-neural-networks/) |
| 1.3.1 | [Initialization & Signal Propagation](/ai-ml-engineering/deep-learning/module-1.3.1-initialization-signal-propagation/) |
| 1.3.2 | [Optimizers & Learning-Rate Dynamics](/ai-ml-engineering/deep-learning/module-1.3.2-optimizers-lr-dynamics/) |
| 1.3.3 | [Regularization & Generalization](/ai-ml-engineering/deep-learning/module-1.3.3-regularization-generalization/) |
| 1.3.4 | [Normalization Layers](/ai-ml-engineering/deep-learning/module-1.3.4-normalization-layers/) |
| 1.3.5 | [Training-Diagnostics Playbook](/ai-ml-engineering/deep-learning/module-1.3.5-training-diagnostics-playbook/) |
| 1.3.6 | [Numerical Stability & Precision](/ai-ml-engineering/deep-learning/module-1.3.6-numerical-stability-precision/) |

### Representations, Attention & Transformers

The conceptual core of modern deep learning: embeddings, residual depth, attention from first principles, and the transformer block assembled from those parts.

| # | Module |
|---|--------|
| 1.4.1 | [Embeddings & Representation Learning](/ai-ml-engineering/deep-learning/module-1.4.1-embeddings-representation-learning/) |
| 1.4.2 | [Residual Connections & Deep-Architecture Patterns](/ai-ml-engineering/deep-learning/module-1.4.2-residual-deep-architectures/) |
| 1.4.3 | [Attention from Scratch](/ai-ml-engineering/deep-learning/module-1.4.3-attention-from-scratch/) |
| 1.4.4 | [The Transformer Block from Scratch](/ai-ml-engineering/deep-learning/module-1.4.4-transformer-block-from-scratch/) |

### Architectures & Capstone

Apply the stack to real data — convolutional networks for vision, recurrent networks for sequences — then train a complete network end-to-end.

| # | Module |
|---|--------|
| 1.5 | [Convolutional Neural Networks & Computer Vision](/ai-ml-engineering/deep-learning/module-1.5-cnns-computer-vision/) |
| 1.6 | [Recurrent Networks & Sequence Models](/ai-ml-engineering/deep-learning/module-1.6-rnns-sequence-models/) |
| 1.7 | [Capstone: Train a Real Net End-to-End](/ai-ml-engineering/deep-learning/module-1.7-capstone-train-a-real-net/) |

### Advanced Topics

Where the field is heading: learning without labels, learning on graphs, and the attention variants behind current frontier models.

| # | Module |
|---|--------|
| 1.8 | [Self-Supervised Learning](/ai-ml-engineering/deep-learning/module-1.8-self-supervised-learning/) |
| 1.9 | [Graph Neural Networks](/ai-ml-engineering/deep-learning/module-1.9-graph-neural-networks/) |
| 1.10 | [Modern Transformers: RoPE, ALiBi, and Attention Variants](/ai-ml-engineering/deep-learning/module-1.10-modern-transformers-rope-and-attention/) |

## Recommended Order

1. If the math feels shaky, do **1.1.1** first — everything else builds on it.
2. Walk **1.1 → 1.1.8 in order.** The from-scratch chain is cumulative; skipping a step breaks the next module's assumptions.
3. Only then cross to PyTorch (**1.2**) and the training loop (**1.3** plus 1.3.1–1.3.6). Resist jumping here first — the framework hides exactly the mechanics you just built by hand.
4. Climb the representation chain **1.4.1 → 1.4.4** before any specific architecture; attention and residual connections reappear everywhere downstream.
5. Choose by interest across **1.5 (vision)** and **1.6 (sequences)**, then lock it all in with the **1.7 capstone.**
6. Treat **1.8–1.10** as advanced electives once the spine is solid.

## Cross-Links

- **Before this section:** [Prerequisites](../prerequisites/) for Python and reproducible environments, and [Machine Learning](../machine-learning/) for the tabular-data discipline most production ML still runs on.
- **After this section:** [Generative AI](../generative-ai/) and [Advanced GenAI & Safety](../advanced-genai/) apply transformers at scale; [AI Infrastructure](../ai-infrastructure/) and [MLOps & LLMOps](../mlops/) deploy and operate the models you train here.
- **Historical context:** [Appendix A: History of AI/ML](../history/) and the top-level [History of AI](/ai-history/) trace how these ideas emerged.
