---
title: "Module 5.1: MLOps Fundamentals"
slug: platform/disciplines/data-ai/mlops/module-5.1-mlops-fundamentals
sidebar:
  order: 2
---
> **Discipline Track** | Complexity: `[MEDIUM]` | Time: 35-40 min

## Prerequisites

Before starting this module:
- Basic machine learning concepts (training, inference, models)
- [DevOps fundamentals](../devsecops/module-4.1-devsecops-fundamentals/)
- Understanding of CI/CD pipelines
- Python basics

## Why This Module Matters

Most machine learning projects never make it to production. Not because the models aren't good enough—but because teams don't know how to operationalize them. Data scientists build great prototypes in Jupyter notebooks, then hand them off expecting someone else to "just deploy it."

MLOps bridges this gap. It's the discipline that transforms experimental notebooks into reliable production systems. Without MLOps, you're stuck in an endless cycle of "works on my machine" and "the model was fine last week."

Companies that master MLOps ship models 10x faster and maintain them with far less pain.

## Did You Know?

- **87% of ML projects never reach production** according to Gartner—not due to model quality, but deployment and maintenance challenges
- **Google's first ML production rule** is "Do machine learning like the great engineer you are, not like the great ML expert you aren't"—emphasizing engineering practices over model sophistication
- **Netflix serves millions of ML predictions per second** using a platform that took years to build—their lesson: invest in infrastructure early
- **The term "MLOps" was coined around 2015** but didn't gain mainstream adoption until 2020, showing how young this discipline really is

## What is MLOps?

MLOps (Machine Learning Operations) applies DevOps principles to machine learning systems. But ML systems are fundamentally different from traditional software:

```
TRADITIONAL SOFTWARE                ML SYSTEMS
────────────────────────────────────────────────────────────────

Code ──▶ Test ──▶ Deploy           Code + Data + Model ──▶ Deploy
                                              │
Fixed behavior                     Behavior CHANGES with data
                                              │
Test coverage = confidence         Model performance DEGRADES
                                              │
Version code                       Version code + data + model
                                              │
Rollback = previous code           Rollback = retrain or old model
```

### Why ML is Different

| Aspect | Traditional Software | ML Systems |
|--------|---------------------|------------|
| **Input** | Code | Code + Data + Hyperparameters |
| **Output** | Deterministic | Probabilistic |
| **Testing** | Unit tests pass/fail | Model metrics (accuracy, F1) |
| **Versioning** | Git for code | Git + DVC/MLflow for data/models |
| **Debugging** | Stack traces | Data quality, drift, feature issues |
| **Failure modes** | Crashes, errors | Silent degradation |

### War Story: The Model That Worked Until It Didn't

A team deployed a fraud detection model that performed brilliantly—96% accuracy in testing. Three months later, fraud losses tripled. The model was still running, still returning predictions, no errors in logs.

What happened? The fraud patterns changed. New attack vectors emerged. The model's accuracy dropped to 60%, but nobody was monitoring it. The model was "working" (returning predictions) while completely failing at its job.

This is the core challenge MLOps addresses: **ML systems fail silently**.

## MLOps Maturity Levels

Organizations progress through maturity levels:

```
┌─────────────────────────────────────────────────────────────────┐
│                   MLOPS MATURITY LEVELS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LEVEL 0: Manual                                                 │
│  ├── Jupyter notebooks                                          │
│  ├── Manual model training                                      │
│  ├── Manual deployment (copy files)                             │
│  └── No monitoring                                              │
│                                                                  │
│  LEVEL 1: ML Pipeline                                           │
│  ├── Automated training pipeline                                │
│  ├── Experiment tracking                                        │
│  ├── Manual deployment trigger                                  │
│  └── Basic monitoring                                           │
│                                                                  │
│  LEVEL 2: CI/CD for ML                                          │
│  ├── Automated training + deployment                            │
│  ├── Model registry with staging                                │
│  ├── A/B testing capability                                     │
│  └── Performance monitoring                                     │
│                                                                  │
│  LEVEL 3: Full Automation                                       │
│  ├── Continuous training (data triggers)                        │
│  ├── Automated retraining on drift                              │
│  ├── Feature stores                                             │
│  └── Full observability                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Most organizations are at Level 0 or 1.** Getting to Level 2 is the biggest leap in value.

## The ML Lifecycle

### End-to-End Pipeline

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

### Pipeline Components

| Component | Purpose | Key Questions |
|-----------|---------|---------------|
| **Data Ingestion** | Collect, validate data | Is data fresh? Complete? |
| **Feature Engineering** | Transform raw data | Consistent train/serve? |
| **Training** | Build models | Reproducible? Scalable? |
| **Validation** | Test model quality | Meets performance bar? |
| **Registry** | Version, stage models | Who approved for prod? |
| **Serving** | Deploy for inference | Latency? Throughput? |
| **Monitoring** | Track health | Drift? Degradation? |

## MLOps vs DevOps

While MLOps borrows heavily from DevOps, key differences exist:

```
DEVOPS PIPELINE
─────────────────────────────────────────────────────────────────

Code ──▶ Build ──▶ Test ──▶ Deploy ──▶ Monitor
  │         │        │         │          │
  └── Git   └── CI   └── QA    └── CD     └── APM


MLOPS PIPELINE
─────────────────────────────────────────────────────────────────

Data ──┬──▶ Validate ──▶ Transform ──▶ Feature Store
       │                                    │
Code ──┼──▶ Train ──▶ Validate ──▶ Registry ──▶ Deploy ──▶ Monitor
       │                                              │      │
Params─┘                                              │      │
                                                      │      │
                              Retrain ◀───────────────┴──────┘
```

### Additional MLOps Concerns

| Concern | Description |
|---------|-------------|
| **Data versioning** | Track which data trained which model |
| **Experiment tracking** | Compare hyperparameters, metrics |
| **Feature stores** | Consistent features train/serve |
| **Model lineage** | What data, code, params made this? |
| **Drift detection** | Data distribution changes |
| **A/B testing** | Compare model versions |

## Core MLOps Principles

### 1. Reproducibility

Every training run must be reproducible:

```python
# BAD: Non-reproducible
model = train(data)  # Which data? What params?

# GOOD: Reproducible
model = train(
    data_version="v2.3.1",
    commit_sha="abc123",
    hyperparams={
        "learning_rate": 0.01,
        "epochs": 100,
        "seed": 42
    }
)
```

### 2. Automation

Automate everything that can be automated:

```yaml
# Trigger retraining on new data
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:
    inputs:
      data_version:
        required: true

jobs:
  train:
    steps:
      - name: Fetch data
        run: dvc pull data/

      - name: Train model
        run: python train.py --data-version ${{ inputs.data_version }}

      - name: Validate model
        run: python validate.py --threshold 0.85

      - name: Register model
        if: success()
        run: python register.py --stage staging
```

### 3. Versioning Everything

```
PROJECT VERSIONING
─────────────────────────────────────────────────────────────────

Code (Git)         Data (DVC)          Model (MLflow)
───────────        ──────────          ──────────────
commit: abc123     version: v2.3       version: 3
date: 2024-01-15   hash: def456        metrics:
message: "Fix      files:                accuracy: 0.94
  feature bug"       train.csv           f1: 0.91
                     test.csv          params:
                                         lr: 0.01
                                         epochs: 100
                                       artifacts:
                                         model.pkl

LINEAGE: Model v3 = Code abc123 + Data v2.3
```

### 4. Continuous Monitoring

Monitor more than just uptime:

| Metric Type | What to Track |
|-------------|---------------|
| **Infrastructure** | Latency, throughput, errors, CPU/memory |
| **Data Quality** | Schema, nulls, distributions |
| **Model Performance** | Accuracy, precision, recall (if labels) |
| **Business Impact** | Conversion, revenue, user satisfaction |

## The MLOps Tool Landscape

```
┌─────────────────────────────────────────────────────────────────┐
│                    MLOPS TOOL LANDSCAPE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DATA LAYER                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │   DVC    │ │  Delta   │ │   Feast  │ │  Great   │           │
│  │ (version)│ │  Lake    │ │ (feature)│ │Expectat. │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
│  EXPERIMENT & TRAINING                                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  MLflow  │ │   W&B    │ │ Kubeflow │ │  Katib   │           │
│  │(tracking)│ │(tracking)│ │(pipeline)│ │  (HPO)   │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
│  SERVING & DEPLOYMENT                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  KServe  │ │  Seldon  │ │BentoML   │ │TorchServe│           │
│  │(k8s serv)│ │  Core    │ │          │ │          │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
│  MONITORING                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Evidently│ │ WhyLabs  │ │  Arize   │ │  NannyML │           │
│  │  (drift) │ │(observ.) │ │ (LLM ok) │ │(no label)│           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
│  PLATFORMS (End-to-End)                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Kubeflow │ │SageMaker │ │Vertex AI │ │Databricks│           │
│  │ (K8s)    │ │  (AWS)   │ │  (GCP)   │ │ (Spark)  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Notebook to production | Not reproducible, no versioning | Proper training pipelines |
| No experiment tracking | Can't reproduce good results | MLflow, W&B from day one |
| Training/serving skew | Different predictions | Feature stores |
| No model validation | Bad models reach prod | Automated quality gates |
| Ignoring drift | Silent performance degradation | Continuous monitoring |
| Manual deployments | Slow, error-prone | CI/CD for ML |

## Quiz

Test your understanding:

<details>
<summary>1. Why do ML systems require different operational practices than traditional software?</summary>

**Answer**: ML systems have three key differences:
1. **Multiple artifacts**: Code + data + model (not just code)
2. **Probabilistic behavior**: Outputs are predictions, not deterministic results
3. **Silent degradation**: Performance degrades as data drifts, without errors or crashes

Traditional monitoring (uptime, errors) misses ML-specific failures.
</details>

<details>
<summary>2. What is "training/serving skew" and why is it dangerous?</summary>

**Answer**: Training/serving skew occurs when features are computed differently during training vs. inference. For example:
- Training uses batch-computed features (correct)
- Serving computes features differently (bugs, missing data)

This causes models to perform well in testing but poorly in production. Feature stores solve this by ensuring identical feature computation.
</details>

<details>
<summary>3. Why is Level 2 (CI/CD for ML) the biggest leap in MLOps maturity?</summary>

**Answer**: Level 2 provides:
- **Reproducibility**: Automated, versioned training
- **Quality gates**: Models validated before deployment
- **Speed**: Days to deploy vs. weeks
- **Reliability**: Consistent deployment process

Most organizations struggle to reach Level 2 but gain most value there. Level 3 optimizations provide incremental improvements.
</details>

<details>
<summary>4. What makes ML monitoring different from traditional APM?</summary>

**Answer**: Traditional APM monitors infrastructure (latency, errors, uptime). ML monitoring adds:
- **Data quality**: Schema changes, distribution shifts
- **Model performance**: Accuracy, precision, recall
- **Drift detection**: Feature and prediction distribution changes
- **Business metrics**: Impact on actual outcomes

A model can be "up" with good latency while making terrible predictions.
</details>

## Hands-On Exercise: Your First MLOps Pipeline

Let's build a minimal but complete MLOps pipeline:

### Setup

```bash
# Create project
mkdir mlops-intro && cd mlops-intro

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install mlflow scikit-learn pandas
```

### Step 1: Create Training Script with Tracking

```python
# train.py
import mlflow
import mlflow.sklearn
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
import argparse

def train(n_estimators, max_depth, random_state):
    # Load data
    iris = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(
        iris.data, iris.target, test_size=0.2, random_state=random_state
    )

    # Start MLflow run
    with mlflow.start_run():
        # Log parameters
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("max_depth", max_depth)
        mlflow.log_param("random_state", random_state)

        # Train model
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state
        )
        model.fit(X_train, y_train)

        # Evaluate
        predictions = model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        f1 = f1_score(y_test, predictions, average='weighted')

        # Log metrics
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)

        # Log model
        mlflow.sklearn.log_model(model, "model")

        print(f"Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
        return accuracy

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument("--max-depth", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    mlflow.set_experiment("iris-classifier")
    train(args.n_estimators, args.max_depth, args.seed)
```

### Step 2: Run Experiments

```bash
# Run multiple experiments
python train.py --n-estimators 50 --max-depth 3
python train.py --n-estimators 100 --max-depth 5
python train.py --n-estimators 200 --max-depth 10

# View results in MLflow UI
mlflow ui
# Open http://localhost:5000
```

### Step 3: Register Best Model

```python
# register.py
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Find best run
experiment = client.get_experiment_by_name("iris-classifier")
runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["metrics.accuracy DESC"],
    max_results=1
)

best_run = runs[0]
print(f"Best run: {best_run.info.run_id}")
print(f"Accuracy: {best_run.data.metrics['accuracy']:.4f}")

# Register model
model_uri = f"runs:/{best_run.info.run_id}/model"
model_name = "iris-classifier"

mlflow.register_model(model_uri, model_name)
print(f"Model registered as '{model_name}'")
```

### Step 4: Create Inference Script

```python
# predict.py
import mlflow

# Load model from registry
model_name = "iris-classifier"
model = mlflow.sklearn.load_model(f"models:/{model_name}/latest")

# Make predictions
sample = [[5.1, 3.5, 1.4, 0.2]]  # Setosa
prediction = model.predict(sample)
print(f"Prediction: {prediction[0]} (0=setosa, 1=versicolor, 2=virginica)")
```

### Success Criteria

You've completed this exercise when you can:
- [ ] Run training with experiment tracking
- [ ] View experiments in MLflow UI
- [ ] Compare runs with different hyperparameters
- [ ] Register the best model
- [ ] Load and use the registered model for inference

## Key Takeaways

1. **ML systems are different**: They include code, data, AND models—all must be versioned
2. **Silent failures are the norm**: Models degrade without crashing—monitoring is critical
3. **Reproducibility is non-negotiable**: Every training run must be reproducible
4. **Automate the pipeline**: Manual processes don't scale
5. **Start simple**: MLflow + basic monitoring beats complex platforms with no adoption

## Further Reading

- [Google's Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml) — Best practices from Google
- [MLOps Maturity Model](https://learn.microsoft.com/en-us/azure/architecture/example-scenario/mlops/mlops-maturity-model) — Microsoft's maturity framework
- [Made With ML](https://madewithml.com/) — Production ML course
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html) — Experiment tracking

## Summary

MLOps brings engineering rigor to machine learning. By treating ML systems as software systems (with additional complexity), we can move from notebook experiments to reliable production systems. The core practices—versioning, automation, monitoring, reproducibility—aren't optional. They're what separate successful ML projects from the 87% that never reach production.

---

## Next Module

Continue to [Module 5.2: Feature Engineering & Stores](module-5.2-feature-stores/) to learn how feature stores ensure consistency between training and serving.
