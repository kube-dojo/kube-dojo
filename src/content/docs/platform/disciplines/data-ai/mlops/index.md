---
title: "MLOps Discipline"
sidebar:
  order: 0
  label: "MLOps"
---
> **Discipline Track** | 12 Modules | ~10 hours total

## Overview

MLOps brings engineering rigor to machine learning. Most ML projects fail not because of bad models, but because teams can't operationalize them. Data scientists build prototypes; MLOps turns them into production systems.

This track covers the complete ML lifecycle—from experiment tracking and feature stores to data versioning, model serving, monitoring, and automated pipelines—giving you the skills to deploy and maintain ML systems at scale.

## Prerequisites

Before starting this track:
- [Observability Theory Track](../../../foundations/observability-theory/) — Monitoring fundamentals
- Basic machine learning concepts (training, inference, models)
- Python programming experience
- Understanding of CI/CD concepts
- At least one Kubernetes route, such as Kubernetes Basics, KCNA, CKA, or equivalent production experience; the model-serving and pipeline modules assume Pods, Services, Deployments, namespaces, and YAML are familiar

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 5.1 | [MLOps Fundamentals](module-5.1-mlops-fundamentals/) | `[MEDIUM]` | 35-40 min |
| 5.2 | [Feature Engineering & Stores](module-5.2-feature-stores/) | `[COMPLEX]` | 40-45 min |
| 5.3 | [Model Training & Experimentation](module-5.3-model-training/) | `[COMPLEX]` | 40-45 min |
| 5.4 | [Model Serving & Inference](module-5.4-model-serving/) | `[COMPLEX]` | 40-45 min |
| 5.5 | [Model Monitoring & Observability](module-5.5-model-monitoring/) | `[COMPLEX]` | 40-45 min |
| 5.6 | [ML Pipelines & Automation](module-5.6-ml-pipelines/) | `[COMPLEX]` | 40-45 min |
| 5.7 | [Data Versioning with DVC](module-5.7-dvc-data-versioning/) | `[COMPLEX]` | 50-60 min |
| 5.8 | [Great Expectations Data Quality](module-5.8-great-expectations-data-quality/) | `[COMPLEX]` | 50-60 min |
| 5.9 | [ML Repository Hygiene](module-5.9-ml-repository-hygiene/) | `[COMPLEX]` | 45-55 min |
| 5.10 | [Production Model-Serving Traffic Patterns](module-5.10-model-serving-traffic-patterns/) | `[COMPLEX]` | 55-65 min |
| 5.11 | [Drift-Triggered Auto-Retraining Loop](module-5.11-drift-triggered-retraining/) | `[COMPLEX]` | 60-70 min |
| 5.12 | [CML for ML CI](module-5.12-cml-for-ml-ci/) | `[COMPLEX]` | 55-60 min |

## Learning Outcomes

After completing this track, you will be able to:

1. **Understand MLOps maturity** — From notebooks to automated pipelines
2. **Build feature stores** — Ensure consistency between training and serving
3. **Track experiments** — Reproduce results, compare approaches systematically
4. **Deploy models** — KServe, canary deployments, A/B testing
5. **Monitor ML systems** — Detect drift, track performance without labels
6. **Automate pipelines** — Kubeflow, continuous training, CI/CD for ML
7. **Version data and models** — Use DVC to connect Git commits, data hashes, model artifacts, and metrics
8. **Gate data quality** — Use Great Expectations to validate schema, completeness, and distribution contracts before training or serving
9. **Maintain clean ML repositories** — Keep data, models, notebooks, dependencies, hooks, and CI policies reviewable without bloating Git history
10. **Control serving exposure** — Use canary, A/B, shadow, mirroring, and bandit patterns to promote models with measurable rollback and cost controls
11. **Close the model lifecycle loop** — Close the model lifecycle loop with drift-triggered automated retraining, gated promotion, and forensic rollback
12. **Surface model review evidence** — Surface model metric deltas, validation reports, and deployment health back into the Git PR review surface using CML on GitHub Actions or GitLab CI.

## Key Concepts

### The ML Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                      ML LIFECYCLE                                │
│                                                                  │
│  DATA                 EXPERIMENTATION           PRODUCTION       │
│  ┌──────────┐        ┌──────────┐            ┌──────────┐       │
│  │  Data    │        │  Model   │            │  Model   │       │
│  │ Ingestion│───────▶│ Training │────────────▶│ Serving  │       │
│  └────┬─────┘        └────┬─────┘            └────┬─────┘       │
│       │                   │                       │              │
│  ┌────▼─────┐        ┌────▼─────┐            ┌────▼─────┐       │
│  │  Data    │        │  Model   │            │  Model   │       │
│  │Validation│        │Validation│            │Monitoring│       │
│  └────┬─────┘        └────┬─────┘            └────┬─────┘       │
│       │                   │                       │              │
│  ┌────▼─────┐        ┌────▼─────┐            ┌────▼─────┐       │
│  │ Feature  │        │  Model   │            │ Trigger  │       │
│  │  Store   │        │ Registry │            │ Retrain  │◀──────┘
│  └──────────┘        └──────────┘            └──────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **Reproducibility** — Every training run must be reproducible
2. **Automation** — Automate everything from training to deployment
3. **Versioning** — Version code, data, AND models
4. **Monitoring** — ML systems fail silently; monitor everything
5. **Continuous Training** — Models degrade; keep them fresh

### MLOps vs DevOps

| Aspect | DevOps | MLOps |
|--------|--------|-------|
| **Artifact** | Code | Code + Data + Model |
| **Testing** | Unit, integration | + Model validation, drift tests |
| **Versioning** | Git | Git + DVC/MLflow |
| **Monitoring** | Infrastructure | + Data quality, model performance |
| **CI/CD** | Build, test, deploy | + Train, validate, serve |

## Tools Covered

| Category | Tools |
|----------|-------|
| **Experiment Tracking** | MLflow, Weights & Biases, Neptune |
| **Feature Stores** | Feast, Tecton, Hopsworks |
| **Model Serving** | KServe, Seldon Core, BentoML, TorchServe |
| **Pipeline Orchestration** | Kubeflow Pipelines, Apache Airflow, Argo |
| **Monitoring** | Evidently, WhyLabs, Arize, NannyML |
| **Hyperparameter Tuning** | Optuna, Katib, Ray Tune |
| **Platforms** | Kubeflow, SageMaker, Vertex AI, Databricks |

## Study Path

```
Module 5.1: MLOps Fundamentals
     │
     │  Why ML is different, maturity levels
     ▼
Module 5.2: Feature Engineering & Stores
     │
     │  Training/serving skew, Feast
     ▼
Module 5.3: Model Training & Experimentation
     │
     │  MLflow, HPO, reproducibility
     ▼
Module 5.4: Model Serving & Inference
     │
     │  KServe, deployment patterns
     ▼
Module 5.5: Model Monitoring & Observability
     │
     │  Drift detection, Evidently
     ▼
Module 5.6: ML Pipelines & Automation
     │
     │  Kubeflow, CI/CD for ML
     ▼
Module 5.7: Data Versioning with DVC
     │
     │  Git + DVC metadata, remotes, reproducible data pipelines
     ▼
Module 5.8: Great Expectations Data Quality
     │
     │  Data contracts, checkpoints, Data Docs, K8s validation Jobs
     ▼
Module 5.9: ML Repository Hygiene
     │
     │  src layout, ignore policy, lock files, notebook discipline, pre-commit gates
     ▼
Module 5.10: Production Model-Serving Traffic Patterns
     │
     │  KServe canary, Istio A/B, shadow, mirroring, bandits, cost controls
     ▼
Module 5.11: Drift-Triggered Auto-Retraining Loop
     │
     │  Drift signals, Argo triggers, retraining DAGs, validation gates, rollback
     ▼
Module 5.12: CML for ML CI
     │
     │  PR comments, DVC metric deltas, validation reports, runner cost controls
     ▼
[Track Complete] → ML Platforms Toolkit
```

## Related Tracks

- **Before**: [Observability Theory](../../../foundations/observability-theory/) — Monitoring foundations
- **Related**: [IaC Discipline](../../delivery-automation/iac/) — Infrastructure provisioning for ML platforms
- **Related**: [DevSecOps](../../reliability-security/devsecops/) — Security for ML pipelines
- **After**: [ML Platforms Toolkit](../../../toolkits/data-ai-platforms/ml-platforms/) — Hands-on implementations
- **After**: [IaC Tools Toolkit](../../../toolkits/infrastructure-networking/iac-tools/) — Terraform modules for ML infrastructure

---

*"A model is only as good as the system that serves it. MLOps is that system."*
