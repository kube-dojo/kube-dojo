---
title: "Open Models & Local Inference"
slug: ai/open-models-local-inference
sidebar:
  order: 4
  label: "Open Models & Local Inference"
---

> **Open Models & Local Inference** | 7 modules | ~14-20 hours

## Overview

This section teaches the practical open-model path for learners who want to move beyond hosted chat tools.

The goal is not to turn every learner into an infrastructure engineer on day one.

The goal is to help learners understand:
- where open models come from
- how to evaluate them responsibly
- how to run them on Apple Silicon or Linux boxes
- how quantization changes what is realistic on real hardware
- how to choose between runtimes without turning local inference into cargo cult

This is still part of the top-level `AI` track.

It sits between [AI Building](../ai-building/) and [AI for Kubernetes & Platform Work](../ai-for-kubernetes-platform-work/), before the deeper [AI/ML Engineering](../../ai-ml-engineering/) sections.

## Modules

| Module | Topic |
|---|---|
| 1.1 | [Open Models and Model Hubs](module-1.1-open-models-and-model-hubs/) |
| 1.2 | [Hugging Face for Learners](module-1.2-hugging-face-for-learners/) |
| 1.3 | [Quantization and Model Formats](module-1.3-quantization-and-model-formats/) |
| 1.4 | [MLX on Apple Silicon](module-1.4-mlx-on-apple-silicon/) |
| 1.5 | [Running Open Models on Linux Boxes](module-1.5-running-open-models-on-linux-boxes/) |
| 1.6 | [Choosing Between Ollama, MLX, Transformers, and vLLM](module-1.6-choosing-between-ollama-mlx-transformers-vllm/) |
| 1.7 | [Gemma 4 and the Open-Model Landscape](module-1.7-gemma-4-and-the-open-model-landscape/) |

## Outcome

By the end of this section, you should be able to:
- explain the difference between open-model access and closed API use
- read a model card without treating it like marketing copy
- understand why quantization changes hardware requirements and quality tradeoffs
- choose a sane local runtime for Apple Silicon or Linux
- know when local inference is enough and when deeper AI/ML engineering is needed

## Recommended Route

```text
AI Foundations
   |
AI-Native Work
   |
AI Building
   |
Open Models & Local Inference
   |
AI for Kubernetes & Platform Work
   |
AI/ML Engineering (optional deeper path)
```

## After This Section

Choose the next route based on your goal:

| Goal | Next Step |
|---|---|
| use AI safely in Kubernetes and platform workflows | [AI for Kubernetes & Platform Work](../ai-for-kubernetes-platform-work/) |
| build practical local-first AI apps | [AI/ML Engineering: AI-Native Development](../../ai-ml-engineering/ai-native-development/) |
| build retrieval-backed applications | [AI/ML Engineering: Vector Search & RAG](../../ai-ml-engineering/vector-rag/) |
| study model behavior more deeply | [AI/ML Engineering: Generative AI](../../ai-ml-engineering/generative-ai/) |
| operate local or private serving seriously | [AI/ML Engineering: AI Infrastructure](../../ai-ml-engineering/ai-infrastructure/) |
