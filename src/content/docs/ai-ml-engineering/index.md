---
title: "AI/ML Engineering"
slug: ai-ml-engineering
sidebar:
  order: 0
  label: "AI/ML Engineering"
---
> **AI/ML Engineering Track** | 60+ Modules | 13 Phases | ~230-310 hours

## Overview

A complete curriculum for engineers building AI and ML systems in production. Covers everything from AI-native development with Claude Code, through generative AI and RAG, to deep learning, machine learning, reinforcement learning, MLOps, and AI infrastructure on Kubernetes.

This track is for engineers who need to understand AI/ML deeply enough to build, deploy, and operate it — not just call APIs.

If your goal is AI literacy, safer AI use, practical AI work habits, or a bridge from AI use into AI product thinking rather than system building, start with the top-level [AI](../ai/) track first.

## What This Track Does Not Repeat

This track assumes you are now moving past AI literacy and bridge content.

It does **not** try to reteach the top-level `AI` track’s main job:
- beginner AI literacy
- basic prompting habits
- general-use trust and verification habits
- introductory workflow discipline
- lightweight practitioner bridge material

Those live in:
- [AI Foundations](../ai/foundations/)
- [AI-Native Work](../ai/ai-native-work/)
- [AI Building](../ai/ai-building/)
- [Open Models & Local Inference](../ai/open-models-local-inference/)
- [AI for Kubernetes & Platform Work](../ai/ai-for-kubernetes-platform-work/)

This track starts where the work becomes engineering:
- reproducible environments
- local and remote runtimes as systems
- framework implementation
- model behavior in depth
- deployment and operations

## Do Not Start Here First If

- you still need basic terminal, Git, or software-installation confidence
- Python environments and local tooling still drift out of control for you
- you want platform or infrastructure depth before you understand AI/ML workflows themselves

In those cases, strengthen [Prerequisites](../prerequisites/) or the AI/ML [Prerequisites](prerequisites/) phase first.

If you need a non-engineering front door first, use [AI Foundations](../ai/foundations/), [AI-Native Work](../ai/ai-native-work/), [AI Building](../ai/ai-building/), and [Open Models & Local Inference](../ai/open-models-local-inference/) before returning here.

## Start Here

If you are unsure where to begin, use one of these entry routes:

| Goal | Start With | Then Go To |
|---|---|---|
| Build AI apps with strong engineering habits | [Prerequisites](prerequisites/) | [AI-Native Development](ai-native-development/) -> [Generative AI](generative-ai/) -> [Vector Search & RAG](vector-rag/) |
| Learn local-first AI from a laptop or workstation | [Prerequisites](prerequisites/) | [AI-Native Development](ai-native-development/) -> [AI Infrastructure](ai-infrastructure/) -> [Advanced GenAI & Safety](advanced-genai/) |
| Move into MLOps / AI platform work | [Prerequisites](prerequisites/) | [MLOps & LLMOps](mlops/) -> [AI Infrastructure](ai-infrastructure/) -> [Platform Engineering: Data & AI](../platform/disciplines/data-ai/) |
| Understand model training and tuning deeply | [Generative AI](generative-ai/) | [Deep Learning Foundations](deep-learning/) -> [Advanced GenAI & Safety](advanced-genai/) |

## What Makes This Track Different

- it treats local-first and home-scale AI as valid starting points
- it teaches the bridge from notebooks to reproducible systems explicitly
- it links application engineering, model work, and infrastructure instead of treating them as separate worlds
- it cross-links into platform and on-prem sections instead of duplicating advanced ops material

## Phases

The track is organized as one main spine with several valid learner routes.

| # | Phase | Focus |
|---|-------|-------|
| 0 | [Prerequisites](prerequisites/) | Environment setup, Python, dev tools |
| 1 | [AI-Native Development](ai-native-development/) | Claude Code, Cursor, prompt engineering, AI coding agents |
| 2 | [Generative AI](generative-ai/) | LLMs, tokenization, embeddings, text generation, reasoning models |
| 3 | [Vector Search & RAG](vector-rag/) | Vector spaces, vector databases, RAG patterns, long-context |
| 4 | [Frameworks & Agents](frameworks-agents/) | LangChain, LangGraph, LlamaIndex, agentic AI, MCP |
| 5 | [MLOps & LLMOps](mlops/) | Kubernetes for ML, experiment tracking, pipelines, deployment |
| 6 | [AI Infrastructure](ai-infrastructure/) | Cloud management, AIOps, vLLM, GPU scheduling |
| 7 | [Advanced GenAI & Safety](advanced-genai/) | Fine-tuning, RLHF, diffusion, alignment, red teaming, evaluation |
| 8 | [Multimodal AI](multimodal-ai/) | Speech, vision, video, native multimodal models |
| 9 | [Deep Learning Foundations](deep-learning/) | PyTorch, neural networks, CNNs, transformers, backprop |
| 10 | [Machine Learning](machine-learning/) | Tabular ML practitioner essentials: sklearn API, regression, evaluation, feature engineering, trees, boosting, clustering, anomaly detection, dimensionality reduction, HPO, time series — plus Tier-2 imbalance, interpretability, recommenders, conformal prediction, fairness, causal inference |
| 11 | [Reinforcement Learning](reinforcement-learning/) | RL practitioner foundations (PPO/DQN/SAC, SB3, Gymnasium) and offline RL / imitation learning |
| A | [History of AI/ML](history/) | Historical context (appendix) |

## Recommended Default Route

For most learners, this is the safest progression:

```text
Prerequisites
   |
AI-Native Development
   |
Generative AI
   |
Vector Search & RAG
   |
Frameworks & Agents
   |
MLOps & LLMOps
   |
AI Infrastructure
```

After that, branch based on interest:
- go to [Advanced GenAI & Safety](advanced-genai/) if you want tuning, evaluation, and alignment depth
- go to [Deep Learning Foundations](deep-learning/) if you want stronger model-building fundamentals
- go to [Platform Engineering: Data & AI](../platform/disciplines/data-ai/) if your focus is operating AI systems at scale

## Common Persona Routes

- `AI application builder`: Prerequisites -> AI-Native Development -> Generative AI -> Vector Search & RAG
- `Local-first builder`: Prerequisites -> AI-Native Development -> AI Infrastructure -> Advanced GenAI
- `MLOps / AI platform`: Prerequisites -> MLOps & LLMOps -> AI Infrastructure -> Platform Data & AI
- `Model-focused learner`: Generative AI -> Deep Learning Foundations -> Advanced GenAI

## When Another Track Becomes Necessary

| If your blocker is... | Go to... | Why |
|---|---|---|
| weak cluster, YAML, or workload fundamentals | [Kubernetes Certifications](../k8s/) | the MLOps and infrastructure phases assume real Kubernetes comfort |
| reproducibility, deployment workflow, service ownership, or team operations | [Platform Engineering](../platform/) | that is no longer just app-building; it is platform and operations work |
| private GPUs, air-gapped environments, datacenter economics, or bare-metal serving | [On-Premises](../on-premises/) | local-first intuition does not automatically transfer to private infrastructure |
| Linux process, package, and service management pain | [Linux](../linux/) | a surprising amount of AI/ML failure is really systems failure |

## Who This Is For

- **AI/ML Engineers** building production ML systems
- **Platform Engineers** supporting ML workloads on Kubernetes
- **Backend Engineers** integrating LLMs and generative AI into products
- **MLOps Specialists** operating model pipelines at scale
- **DevOps Engineers** moving into AI infrastructure roles

## Prerequisites

- **Programming**: Python proficiency required (Phase 0 covers setup)
- **Kubernetes basics**: helpful for MLOps phases — see [CKA track](../k8s/cka/) if needed
- **Linux fundamentals**: see [Linux track](../linux/) if needed
- **Math intuition**: linear algebra and statistics helpful for deep learning phases

## Related Tracks

- **[Platform Engineering: Data & AI](../platform/disciplines/data-ai/)** — production deployment of ML systems
- **[CKA / CKAD](../k8s/)** — Kubernetes fundamentals for the MLOps phases
- **[On-Premises](../on-premises/)** — running ML infrastructure on bare metal

## When To Leave This Track For Another One

- go to [Platform Engineering](../platform/) when your main problem becomes operating systems and teams, not just building models or apps
- go to [On-Premises](../on-premises/) when local-first or private AI work grows into real private infrastructure concerns
- go to [Kubernetes Certifications](../k8s/) if your MLOps path is blocked by weak cluster fundamentals

## Common Failure Modes In This Track

- starting in advanced infrastructure before local environments and workflows are reproducible
- treating notebooks as a permanent workflow when the real problem is packaging, deployment, or operations
- jumping to private AI infrastructure because the hardware sounds interesting before the application path is solid

## Good First Clicks

- [Home AI Workstation Fundamentals](prerequisites/module-1.2-home-ai-workstation-fundamentals/) if you want a realistic local setup path
- [AI Coding Tools Landscape](ai-native-development/module-1.1-ai-coding-tools-landscape/) if you want to orient around the modern agent/tooling ecosystem
- [Building RAG Systems](vector-rag/module-1.2-building-rag-systems/) if your goal is practical LLM applications
- [Notebooks to Production for ML/LLMs](mlops/module-1.11-notebooks-to-production-for-ml-llms/) if you already experiment in notebooks and need a more serious workflow
- [Local Inference Stack for Learners](ai-infrastructure/module-1.4-local-inference-stack-for-learners/) if you want to run models yourself without jumping straight into datacenter thinking


*"The best AI engineers understand both the model and the infrastructure it runs on."*
