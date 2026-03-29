---
title: "ML Platforms Toolkit"
sidebar:
  order: 1
  label: "ML Platforms"
---
> **Toolkit Track** | 6 Modules | ~5 hours total

## Overview

The ML Platforms Toolkit covers the infrastructure for production machine learning on Kubernetes. From traditional ML pipelines with Kubeflow and MLflow to the LLM revolution with vLLM and LangChain—this toolkit provides the complete foundation for modern AI/ML infrastructure. Whether you're running batch training, serving real-time predictions, or building RAG applications, these tools form the backbone of production AI systems.

This toolkit applies concepts from [MLOps Discipline](../../disciplines/data-ai/mlops/).

## Prerequisites

Before starting this toolkit:
- [MLOps Discipline](../../disciplines/data-ai/mlops/)
- Kubernetes fundamentals
- Basic ML concepts (training, inference)
- Python familiarity

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 9.1 | [Kubeflow](module-9.1-kubeflow/) | `[COMPLEX]` | 50-60 min |
| 9.2 | [MLflow](module-9.2-mlflow/) | `[MEDIUM]` | 40-45 min |
| 9.3 | [Feature Stores](module-9.3-feature-stores/) | `[MEDIUM]` | 40-45 min |
| 9.4 | [vLLM](module-9.4-vllm/) | `[COMPLEX]` | 50-60 min |
| 9.5 | [Ray Serve](module-9.5-ray-serve/) | `[COMPLEX]` | 50-60 min |
| 9.6 | [LangChain & LlamaIndex](module-9.6-langchain-llamaindex/) | `[COMPLEX]` | 50-60 min |
| 9.7 | [GPU Scheduling](module-9.7-gpu-scheduling/) | `[COMPLEX]` | 50 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Deploy Kubeflow** — Pipelines, notebooks, model serving
2. **Track experiments** — MLflow tracking and model registry
3. **Manage features** — Feast offline and online stores
4. **Serve LLMs efficiently** — vLLM with PagedAttention for high throughput
5. **Build distributed inference** — Ray Serve for multi-model pipelines
6. **Create RAG applications** — LangChain and LlamaIndex for LLM apps

## Tool Selection Guide

```
WHICH ML PLATFORM TOOL?
─────────────────────────────────────────────────────────────────

"I need to orchestrate ML training pipelines"
└──▶ Kubeflow Pipelines
     • Workflow orchestration
     • Artifact management
     • Kubernetes-native
     • GPU scheduling

"I need to track experiments and models"
└──▶ MLflow
     • Parameter/metric logging
     • Model versioning
     • Model registry
     • Framework-agnostic

"I need to manage and serve features"
└──▶ Feast
     • Feature definitions
     • Point-in-time correctness
     • Online/offline stores
     • Training-serving consistency

"I need AutoML / hyperparameter tuning"
└──▶ Kubeflow Katib
     • Bayesian optimization
     • Neural architecture search
     • Parallel trials
     • Early stopping

"I need to serve models at scale"
└──▶ KServe (with Kubeflow)
     • Auto-scaling
     • Canary deployments
     • Multi-framework support
     • GPU inference

"I need to serve LLMs with high throughput"
└──▶ vLLM
     • PagedAttention memory optimization
     • Continuous batching
     • OpenAI-compatible API
     • Multi-GPU tensor parallelism

"I need distributed model serving"
└──▶ Ray Serve
     • Model composition
     • Fractional GPU allocation
     • Auto-scaling
     • A/B testing built-in

"I need to build LLM applications"
└──▶ LangChain / LlamaIndex
     • RAG (Retrieval-Augmented Generation)
     • Chains and agents
     • Memory management
     • Document processing

ML PLATFORM STACK:
─────────────────────────────────────────────────────────────────
                      ML Workflow
─────────────────────────────────────────────────────────────────
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌─────────┐        ┌───────────┐        ┌─────────┐
│Kubeflow │        │  MLflow   │        │  Feast  │
│Pipelines│        │ Tracking  │        │Features │
└─────────┘        └───────────┘        └─────────┘
    │                     │                     │
    ▼                     ▼                     ▼
Training            Model Registry       Feature Store
Orchestration       Versioning          Online/Offline
```

## The ML Platform Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                    ML PLATFORM ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EXPERIMENTATION                                                │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Kubeflow Notebooks                                        │ │
│  │  • JupyterHub  • GPU access  • Shared storage             │ │
│  │                                                            │ │
│  │  MLflow Tracking                                          │ │
│  │  • Parameters  • Metrics  • Artifacts                     │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  TRAINING                                                       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Kubeflow Pipelines                                        │ │
│  │  • Workflow DAGs  • Artifact tracking  • Caching          │ │
│  │                                                            │ │
│  │  Katib (AutoML)                                           │ │
│  │  • Hyperparameter tuning  • Neural architecture search    │ │
│  │                                                            │ │
│  │  Training Operators                                        │ │
│  │  • TFJob  • PyTorchJob  • MPIJob                          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  FEATURE MANAGEMENT                                             │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Feast                                                     │ │
│  │  • Offline store (training)  • Online store (inference)   │ │
│  │  • Point-in-time joins  • Feature serving                 │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  SERVING & PRODUCTION                                           │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  MLflow Model Registry                                     │ │
│  │  • Model versions  • Stages  • Aliases                    │ │
│  │                                                            │ │
│  │  KServe                                                    │ │
│  │  • Model serving  • Auto-scaling  • Canary rollouts       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Study Path

```
Module 9.1: Kubeflow
     │
     │  ML platform foundation
     │  Pipelines, notebooks, training
     ▼
Module 9.2: MLflow
     │
     │  Experiment tracking
     │  Model registry
     ▼
Module 9.3: Feature Stores
     │
     │  Feature management
     │  Training-serving consistency
     ▼
Module 9.4: vLLM
     │
     │  High-throughput LLM serving
     │  PagedAttention optimization
     ▼
Module 9.5: Ray Serve
     │
     │  Distributed inference
     │  Model composition
     ▼
Module 9.6: LangChain & LlamaIndex
     │
     │  LLM application frameworks
     │  RAG and agents
     ▼
[Toolkit Complete] → Production AI/ML!
```

## Key Concepts

### MLOps Platform Principles

| Principle | Tool | Implementation |
|-----------|------|----------------|
| **Reproducibility** | Kubeflow Pipelines | Containerized steps, artifacts |
| **Experiment tracking** | MLflow | Parameters, metrics, models |
| **Feature consistency** | Feast | Point-in-time correct features |
| **Model lifecycle** | MLflow Registry | Versions, stages, aliases |
| **Scalable training** | Kubeflow Operators | Distributed training |
| **Model serving** | KServe | Auto-scaling inference |

### Platform Components

```
ML PLATFORM COMPONENTS
─────────────────────────────────────────────────────────────────

KUBEFLOW
├── Notebooks - Interactive development
├── Pipelines - Workflow orchestration
├── Katib - Hyperparameter tuning
├── Training Operators - Distributed training
└── KServe - Model serving

MLFLOW
├── Tracking - Experiment logging
├── Projects - Reproducible packaging
├── Models - Unified model format
└── Registry - Model lifecycle

FEAST
├── Feature Views - Feature definitions
├── Offline Store - Historical features
├── Online Store - Latest features
└── Feature Server - Real-time serving
```

## Integration Patterns

### Complete ML Pipeline

```
INTEGRATED ML WORKFLOW
─────────────────────────────────────────────────────────────────

Data                    Features                Training
  │                        │                       │
  ▼                        ▼                       ▼
┌──────────┐        ┌──────────┐        ┌──────────────────┐
│Raw Data  │───────▶│  Feast   │───────▶│Kubeflow Pipeline │
│(S3, GCS) │        │(Features)│        │                  │
└──────────┘        └──────────┘        │ 1. Load features │
                                        │ 2. Train model   │
                                        │ 3. Evaluate      │
                                        │ 4. Register      │
                                        └────────┬─────────┘
                                                 │
                    ┌────────────────────────────┼────────────┐
                    │                            │            │
                    ▼                            ▼            ▼
             ┌──────────┐                 ┌──────────┐ ┌──────────┐
             │  MLflow  │                 │  MLflow  │ │  KServe  │
             │ Tracking │                 │ Registry │ │(Serving) │
             └──────────┘                 └──────────┘ └──────────┘
```

### Kubeflow + MLflow

```python
# Pipeline step with MLflow tracking
@dsl.component(packages_to_install=["mlflow"])
def train_with_tracking(mlflow_uri: str):
    import mlflow

    mlflow.set_tracking_uri(mlflow_uri)

    with mlflow.start_run():
        # Train model
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(model, "model",
            registered_model_name="my-model")
```

### MLflow + Feast

```python
# Training with Feast features and MLflow tracking
import mlflow
from feast import FeatureStore

store = FeatureStore()
mlflow.set_tracking_uri("http://mlflow:5000")

# Get training features
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=["user_features:feature1", "user_features:feature2"]
).to_df()

with mlflow.start_run():
    mlflow.log_param("feature_store", "feast")
    mlflow.log_param("feature_view", "user_features")

    model.fit(training_df)
    mlflow.sklearn.log_model(model, "model")
```

## Common Architectures

### Development to Production

```
ML DEVELOPMENT TO PRODUCTION
─────────────────────────────────────────────────────────────────

DEVELOPMENT                 STAGING                 PRODUCTION
─────────────────────────────────────────────────────────────────

┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Notebooks  │      │  Pipelines  │      │   KServe    │
│  (Kubeflow) │      │  (Kubeflow) │      │  (Serving)  │
└──────┬──────┘      └──────┬──────┘      └──────┬──────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   MLflow    │      │   MLflow    │      │   MLflow    │
│  Tracking   │─────▶│  Registry   │─────▶│  Registry   │
│             │      │  (Staging)  │      │(Production) │
└─────────────┘      └─────────────┘      └─────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Feast     │      │   Feast     │      │   Feast     │
│ (Dev Store) │─────▶│(Stage Store)│─────▶│(Prod Store) │
└─────────────┘      └─────────────┘      └─────────────┘
```

### Real-Time ML System

```
REAL-TIME ML SERVING
─────────────────────────────────────────────────────────────────

Request                     Feast                    Model
  │                           │                        │
  │ user_id=123               │                        │
  │ ─────────────────▶        │                        │
  │                           │                        │
  │                     Get features                   │
  │                     ─────────────────────────────▶ │
  │                           │                        │
  │                     features = [...]               │
  │                     ◀───────────────────────────── │
  │                           │                        │
  │                           │  Predict               │
  │                           │  ─────────────────────▶│
  │                           │                        │
  │ prediction                │  prediction            │
  │ ◀─────────────────────────────────────────────────│

Latency: < 100ms total
  - Feature fetch: ~10ms (Redis)
  - Model inference: ~50ms (GPU)
```

## Hands-On Focus

| Module | Key Exercise |
|--------|--------------|
| Kubeflow | Deploy Pipelines, run training pipeline |
| MLflow | Track experiment, register model |
| Feature Stores | Define features, serve online/offline |
| vLLM | Deploy LLM with PagedAttention, benchmark throughput |
| Ray Serve | Build multi-model pipeline with composition |
| LangChain/LlamaIndex | Create RAG application with vector store |

## Tool Comparison

```
ML PLATFORM TOOLS
─────────────────────────────────────────────────────────────────

                   Kubeflow        MLflow          Feast
─────────────────────────────────────────────────────────────────
Primary focus      Workflows       Tracking        Features
Kubernetes-native  ✓✓              ✓               ✓
Standalone         ✗               ✓✓              ✓
Experiment log     Basic           ✓✓              ✗
Model registry     ✗               ✓✓              ✗
Feature store      ✗               ✗               ✓✓
Pipeline DAGs      ✓✓              Projects        ✗
AutoML             Katib           ✗               ✗
Model serving      KServe          Basic           ✗
─────────────────────────────────────────────────────────────────

RECOMMENDATION: Use all three together
- Kubeflow: Orchestration & training
- MLflow: Tracking & model registry
- Feast: Feature management
```

## Related Tracks

- **Before**: [MLOps Discipline](../../disciplines/data-ai/mlops/) — MLOps concepts and practices
- **Related**: [IaC Discipline](../../disciplines/delivery-automation/iac/) — Infrastructure provisioning for ML platforms
- **Related**: [IaC Tools Toolkit](../iac-tools/) — Terraform modules for ML infrastructure
- **Related**: [Observability Toolkit](../observability/) — Monitor ML systems
- **Related**: [GitOps & Deployments Toolkit](../gitops-deployments/) — Deploy ML infrastructure
- **Related**: [Scaling & Reliability Toolkit](../scaling-reliability/) — Scale ML workloads

---

*"The best ML platform is invisible to data scientists. They focus on models; the platform handles everything else."*
