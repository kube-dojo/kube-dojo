---
title: "AI/GPU Infrastructure on Kubernetes"
sidebar:
  order: 1
  label: "AI Infrastructure"
---
**The infrastructure side of AI — GPU scheduling, distributed training, and LLM serving at scale.**

This discipline focuses on the infrastructure challenges of running AI workloads on Kubernetes. It complements the existing [MLOps discipline](../mlops/) (model lifecycle) and [ML Platforms toolkit](../../../toolkits/data-ai-platforms/ml-platforms/) (tools like Kubeflow, MLflow). Here you'll learn to provision GPUs, schedule them efficiently, run distributed training, and serve models in production.

---

## Modules

| # | Module | Time | What You'll Learn |
|---|--------|------|-------------------|
| 1.1 | [GPU Provisioning & Device Plugins](module-1.1-gpu-provisioning/) | 3h | GPU Operator, NFD, DCGM-Exporter |
| 1.2 | [Advanced GPU Scheduling & Sharing](module-1.2-gpu-scheduling/) | 4h | MIG, time-slicing, DRA, topology-aware |
| 1.3 | [Distributed Training Infrastructure](module-1.3-distributed-training/) | 5h | NCCL, Multus CNI, PyTorch Operator |
| 1.4 | [High-Performance Storage for AI](module-1.4-ai-storage/) | 3h | NVMe caching, JuiceFS, Fluid/Alluxio |
| 1.5 | [Serving LLMs at Scale](module-1.5-llm-serving/) | 4h | vLLM, TGI, PagedAttention, KEDA autoscaling |
| 1.6 | [Cost & Capacity Planning](module-1.6-ai-cost/) | 3h | Spot GPUs, Karpenter, Kueue, cost per inference |

**Total time**: ~22 hours

---

## Prerequisites

- Kubernetes Administration (CKA level)
- Basic Linux hardware knowledge
- Familiarity with ML concepts (helpful but not required)
