---
title: "AI Infrastructure"
sidebar:
  order: 0
  label: "AI Infrastructure"
---

> **AI/ML Engineering Track** | Phase 6

**Best for:** learners moving from model/application work into inference, cost, and infrastructure decisions.

This phase is intentionally split between:
- learner-scale local infrastructure
- production-oriented AI infra concepts

That means not every module should be read in pure numeric order if your immediate goal is local-first work.

## Modules

| # | Module |
|---|--------|
| 1.1 | [Cloud AI Services](/ai-ml-engineering/ai-infrastructure/module-1.1-cloud-ai-services/) |
| 1.2 | [AIOps](/ai-ml-engineering/ai-infrastructure/module-1.2-aiops/) |
| 1.3 | [High-Performance LLM Inference: vLLM and sglang](/ai-ml-engineering/ai-infrastructure/module-1.3-vllm-sglang-inference/) |
| 1.4 | [Local Inference Stack for Learners](/ai-ml-engineering/ai-infrastructure/module-1.4-local-inference-stack-for-learners/) |
| 1.5 | [Home AI Operations and Cost Model](/ai-ml-engineering/ai-infrastructure/module-1.5-home-ai-operations-cost-model/) |
| 1.6 | [GPU Memory Hierarchy and Bandwidth Math for LLM Inference](/ai-ml-engineering/ai-infrastructure/module-1.6-memory-bandwidth-math/) |
| 1.7 | [Production-Tier LLM Inference Engines: Decision Framework](/ai-ml-engineering/ai-infrastructure/module-1.7-production-inference-engines/) |
| 1.8 | [Benchmarking LLM Inference: TTFT, TPOT, and Workload-Aware Load Shaping](/ai-ml-engineering/ai-infrastructure/module-1.8-inference-benchmarking/) |

## Suggested Paths

### Local-First Route

- [Local Inference Stack for Learners](module-1.4-local-inference-stack-for-learners/)
- [Home AI Operations and Cost Model](module-1.5-home-ai-operations-cost-model/)
- then branch into [Single-GPU Local Fine-Tuning](../advanced-genai/module-1.10-single-gpu-local-fine-tuning/) or [Home-Scale RAG Systems](../vector-rag/module-1.6-home-scale-rag-systems/)

### Production-Oriented Route

- [Cloud AI Services](module-1.1-cloud-ai-services/)
- [High-Performance LLM Inference: vLLM and sglang](module-1.3-vllm-sglang-inference/)
- then continue into [Platform Engineering: Data & AI](../../platform/disciplines/data-ai/) or [On-Premises AI/ML Infrastructure](../../on-premises/ai-ml-infrastructure/)

## Key Distinction

This section is not only about datacenter-scale AI.
It also teaches when a learner should stay simple, local, and private instead of prematurely copying large-scale serving architecture.
