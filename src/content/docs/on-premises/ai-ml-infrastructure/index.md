---
title: "AI/ML Infrastructure (On-Prem)"
sidebar:
  order: 0
---

> **Complexity**: `[ADVANCED]` | 6 modules | ~6 hours
>
> **Prerequisites**: [Planning & Economics](../planning/), [Day-2 Operations](../operations/), practical familiarity with Kubernetes GPU workloads.

Running AI and ML workloads on bare metal is a different sport from running them in the cloud. There is no managed SageMaker, no Vertex AI, no `g5.24xlarge` you can spin up for an afternoon. You pick the GPU vendor, rack the hardware, tune the driver stack, build the networking fabric that keeps NCCL happy, and decide how training datasets move through your storage tier without starving the GPUs. This section covers the entire private-AI-infrastructure stack — from GPU scheduling primitives to a full on-prem MLOps platform — with the tradeoffs that only matter when you can't hand the bill to a hyperscaler.

## Modules

| Module | Focus | Time |
|--------|-------|------|
| [9.1 GPU Nodes & Accelerated Computing](module-9.1-gpu-nodes-accelerated/) | NVIDIA GPU Operator, MIG, time slicing, DCGM monitoring, AMD ROCm, Intel Gaudi | 60 min |
| [9.2 Private AI Training Infrastructure](module-9.2-private-ai-training/) | Distributed training, NCCL over InfiniBand/RoCE, Volcano/Kueue, fault-tolerant jobs | 75 min |
| [9.3 Private LLM Serving](module-9.3-private-llm-serving/) | vLLM, TGI, Ollama at scale, quantization, KServe, continuous batching | 75 min |
| [9.4 Private MLOps Platform](module-9.4-private-mlops-platform/) | Kubeflow, MLflow, Feast, model registry, experiment tracking on bare metal | 60 min |
| [9.5 Private AIOps](module-9.5-private-aiops/) | Anomaly detection, predictive scaling, AI-augmented incident response with guardrails | 60 min |
| [9.6 High-Performance Storage for AI](module-9.6-high-performance-storage-ai/) | NFS-over-RDMA, Lustre/BeeGFS/WekaFS, avoiding GPU idle from storage bottlenecks | 60 min |

---

## Why a dedicated section?

The rest of the on-prem track covers general Kubernetes operations. Accelerated computing adds a layer of complexity that doesn't exist in CPU-only workloads: driver management, MIG partitioning, RDMA fabrics, and dataset I/O patterns that can cost you 50% of your GPU utilization if the storage tier can't keep up. These modules assume you already know how to run a bare-metal K8s cluster and focus on what's specific to AI workloads.

## Not covered here

- **General Kubernetes cluster operations** — see [Day-2 Operations](../operations/)
- **Cloud AI services** — see the Cloud track's managed-services section
- **Platform engineering for AI teams (org design, self-service)** — see [Platform Engineering](../../platform/)
- **AI/ML curriculum content (LLMs, transformers, RAG, fine-tuning)** — see the [AI/ML Engineering](../../ai-ml-engineering/) track
