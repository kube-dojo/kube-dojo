---
name: mlops-expert
description: MLOps discipline knowledge. Use for ML lifecycle, model serving, feature stores, Kubeflow, MLflow, model monitoring, ML pipelines. Triggers on "MLOps", "machine learning", "model serving", "Kubeflow", "MLflow", "feature store".
---

# MLOps Expert Skill

Authoritative knowledge source for MLOps principles, ML lifecycle management, and production ML systems. Covers the intersection of machine learning, DevOps, and data engineering.

## When to Use
- Writing or reviewing MLOps curriculum content
- Designing ML pipelines and workflows
- Evaluating ML platforms (Kubeflow, MLflow, etc.)
- Model serving and deployment strategies
- Feature engineering and store architecture

## Core MLOps Principles

### What is MLOps?

MLOps (Machine Learning Operations) is a set of practices that combines ML, DevOps, and Data Engineering to deploy and maintain ML systems in production reliably and efficiently.

### Why MLOps is Different

```
TRADITIONAL SOFTWARE              ML SYSTEMS
─────────────────────────────────────────────────────────────
Code ──▶ Test ──▶ Deploy         Code + Data + Model ──▶ Deploy
                                           │
Fixed behavior                    Behavior changes with data
                                           │
Test coverage = confidence        Model performance degrades
                                           │
Version code                      Version code + data + model
```

### MLOps vs DevOps

| Aspect | DevOps | MLOps |
|--------|--------|-------|
| Artifact | Code | Code + Data + Model |
| Testing | Unit, integration | + Model validation |
| Versioning | Code | + Data + Model lineage |
| Monitoring | App metrics | + Model performance |
| CI/CD | Build, test, deploy | + Train, validate, serve |
| Rollback | Previous version | Retrain or previous model |

### MLOps Maturity Levels

| Level | Description | Characteristics |
|-------|-------------|-----------------|
| 0 | Manual | Jupyter notebooks, manual deployment |
| 1 | ML Pipeline | Automated training, manual deploy |
| 2 | CI/CD for ML | Automated training + deployment |
| 3 | Full Automation | Continuous training, monitoring, retraining |

## The ML Lifecycle

### End-to-End Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                      ML LIFECYCLE                                │
│                                                                  │
│  DATA                 EXPERIMENTATION           PRODUCTION       │
│  ┌──────────┐        ┌──────────┐            ┌──────────┐       │
│  │  Data    │        │  Model   │            │  Model   │       │
│  │  Ingestion│───────▶│ Training │────────────▶│ Serving  │       │
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

| Component | Purpose | Tools |
|-----------|---------|-------|
| Data Ingestion | Collect, store data | Kafka, Airflow, Spark |
| Data Validation | Quality checks | Great Expectations, TFDV |
| Feature Store | Feature management | Feast, Tecton, Hopsworks |
| Training | Model training | Kubeflow, SageMaker, Vertex AI |
| Model Registry | Version, track models | MLflow, Neptune, Weights & Biases |
| Serving | Deploy models | KServe, Seldon, TorchServe |
| Monitoring | Track performance | Evidently, WhyLabs, Arize |

## Feature Engineering

### What is a Feature Store?

A feature store is a centralized repository for storing, sharing, and serving ML features, ensuring consistency between training and inference.

### Feature Store Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FEATURE STORE                            │
│                                                              │
│  OFFLINE STORE              │         ONLINE STORE          │
│  (Training)                 │         (Inference)           │
│  ┌───────────────┐          │         ┌───────────────┐     │
│  │   Data Lake   │          │         │  Redis/DynamoDB│    │
│  │   (Parquet)   │          │         │  (low latency) │    │
│  └───────┬───────┘          │         └───────┬───────┘     │
│          │                  │                 │              │
│          │    ┌─────────────┴────────────┐    │              │
│          └────│   Feature Definitions    │────┘              │
│               │   (Schema, transforms)   │                   │
│               └──────────────────────────┘                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Feature Store Benefits

- **Consistency**: Same features for training and serving
- **Reusability**: Share features across teams/models
- **Point-in-time correctness**: Avoid data leakage
- **Feature freshness**: Scheduled/streaming updates

### Feast Example

```python
from feast import FeatureStore

store = FeatureStore(repo_path=".")

# Define feature view
@feature_view(
    entities=["user_id"],
    ttl=timedelta(days=1),
    source=user_activity_source,
)
def user_features(events):
    return events[["user_id", "purchase_count", "avg_order_value"]]

# Get features for training
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=["user_features:purchase_count", "user_features:avg_order_value"],
)

# Get features for inference
features = store.get_online_features(
    features=["user_features:purchase_count"],
    entity_rows=[{"user_id": 123}],
)
```

## Model Training

### Training Pipeline Best Practices

1. **Reproducibility**
   - Version data, code, and hyperparameters
   - Set random seeds
   - Use deterministic operations

2. **Scalability**
   - Distributed training for large models
   - GPU/TPU utilization
   - Efficient data loading

3. **Experiment Tracking**
   - Log metrics, parameters, artifacts
   - Compare experiments
   - Track lineage

### Kubeflow Pipelines

```python
from kfp import dsl

@dsl.component
def train_model(data_path: str, model_path: str):
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    import joblib

    df = pd.read_csv(data_path)
    X, y = df.drop('target', axis=1), df['target']
    model = RandomForestClassifier()
    model.fit(X, y)
    joblib.dump(model, model_path)

@dsl.pipeline(name="training-pipeline")
def ml_pipeline(data_path: str):
    train_task = train_model(data_path=data_path, model_path="/models/model.pkl")
```

### MLflow Tracking

```python
import mlflow

mlflow.set_experiment("my-experiment")

with mlflow.start_run():
    # Log parameters
    mlflow.log_param("learning_rate", 0.01)
    mlflow.log_param("epochs", 100)

    # Train model
    model = train(...)

    # Log metrics
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_metric("f1_score", 0.93)

    # Log model
    mlflow.sklearn.log_model(model, "model")
```

## Model Registry

### What is a Model Registry?

A central repository to store, version, and manage ML models throughout their lifecycle.

### Model Registry Features

| Feature | Purpose |
|---------|---------|
| Versioning | Track model iterations |
| Staging | Dev → Staging → Prod transitions |
| Metadata | Store metrics, parameters, lineage |
| Governance | Approval workflows |
| Reproducibility | Link to training data/code |

### MLflow Model Registry

```python
import mlflow

# Register model
model_uri = "runs:/<run_id>/model"
mlflow.register_model(model_uri, "my-model")

# Transition stages
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="my-model",
    version=1,
    stage="Production"
)
```

## Model Serving

### Serving Patterns

| Pattern | Use Case | Latency | Throughput |
|---------|----------|---------|------------|
| Online (sync) | Real-time predictions | Low | Medium |
| Batch | Bulk predictions | High | High |
| Streaming | Event-driven | Medium | High |
| Edge | On-device inference | Very low | Low |

### Serving Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MODEL SERVING                             │
│                                                              │
│  ┌──────────────┐                                           │
│  │   Gateway    │                                           │
│  │  (Istio)     │                                           │
│  └──────┬───────┘                                           │
│         │                                                    │
│  ┌──────▼───────┐     ┌──────────────┐                      │
│  │  Inference   │     │   Model      │                      │
│  │   Service    │◀────│   Store      │                      │
│  │  (KServe)    │     │   (S3)       │                      │
│  └──────┬───────┘     └──────────────┘                      │
│         │                                                    │
│  ┌──────▼───────┐     ┌──────────────┐                      │
│  │  Feature     │     │  Monitoring  │                      │
│  │  Store       │     │  (Evidently) │                      │
│  └──────────────┘     └──────────────┘                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### KServe (Kubeflow Serving)

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: sklearn-model
spec:
  predictor:
    model:
      modelFormat:
        name: sklearn
      storageUri: s3://models/sklearn/model
      resources:
        requests:
          cpu: 100m
          memory: 256Mi
        limits:
          cpu: 1
          memory: 1Gi
```

### Seldon Core

```yaml
apiVersion: machinelearning.seldon.io/v1
kind: SeldonDeployment
metadata:
  name: iris-model
spec:
  predictors:
    - name: default
      graph:
        name: classifier
        implementation: SKLEARN_SERVER
        modelUri: gs://models/sklearn/iris
      componentSpecs:
        - spec:
            containers:
              - name: classifier
                resources:
                  requests:
                    memory: 1Gi
```

## Model Deployment Strategies

### Deployment Patterns

```
SHADOW DEPLOYMENT
─────────────────────────────────────────────────────────────
                    ┌─────────────┐
User ──────────────▶│ Production  │──▶ Response
     │              │   Model     │
     │              └─────────────┘
     │
     └─────────────▶┌─────────────┐
       (copy)       │   Shadow    │──▶ Log only
                    │   Model     │
                    └─────────────┘

CANARY DEPLOYMENT
─────────────────────────────────────────────────────────────
                    ┌─────────────┐
User ──┬───90%─────▶│ Production  │──▶ Response
       │            │   Model     │
       │            └─────────────┘
       │
       └───10%─────▶┌─────────────┐
                    │   Canary    │──▶ Response
                    │   Model     │
                    └─────────────┘

A/B TEST
─────────────────────────────────────────────────────────────
                    ┌─────────────┐
User ──┬───50%─────▶│  Model A    │──▶ Response + metrics
       │            └─────────────┘
       │
       └───50%─────▶┌─────────────┐
                    │  Model B    │──▶ Response + metrics
                    └─────────────┘
```

## Model Monitoring

### What to Monitor

| Category | Metrics |
|----------|---------|
| **Infrastructure** | Latency, throughput, errors, resources |
| **Data Quality** | Schema changes, null rates, distributions |
| **Model Performance** | Accuracy, precision, recall (if labels available) |
| **Data Drift** | Feature distribution changes |
| **Concept Drift** | Relationship between features and target changes |
| **Prediction Drift** | Output distribution changes |

### Drift Detection

```
TRAINING DATA               PRODUCTION DATA
─────────────────────────────────────────────────────────────
Distribution                Distribution
    ▲                           ▲
    │   ╱╲                      │       ╱╲
    │  ╱  ╲                     │      ╱  ╲
    │ ╱    ╲                    │    ╱    ╲
    │╱      ╲                   │  ╱        ╲
    └────────────▶              └────────────▶
         Feature                     Feature

         DRIFT = Statistical difference between distributions
```

### Monitoring Tools

| Tool | Features |
|------|----------|
| Evidently | Open source, drift detection, reports |
| WhyLabs | SaaS, observability platform |
| Arize | SaaS, embeddings, LLM monitoring |
| Fiddler | Explainability, bias detection |
| NannyML | Performance estimation without labels |

### Evidently Example

```python
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

report = Report(metrics=[DataDriftPreset()])
report.run(
    reference_data=training_df,
    current_data=production_df,
    column_mapping=ColumnMapping()
)
report.save_html("drift_report.html")
```

## ML Platforms

### Platform Comparison

| Platform | Type | Best For |
|----------|------|----------|
| Kubeflow | Open source, K8s native | K8s organizations |
| MLflow | Open source, lightweight | Experiment tracking |
| SageMaker | AWS managed | AWS shops |
| Vertex AI | GCP managed | GCP shops |
| Azure ML | Azure managed | Azure shops |
| Databricks | Unified analytics | Spark workloads |

### Kubeflow Components

```
┌─────────────────────────────────────────────────────────────┐
│                       KUBEFLOW                               │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Pipelines  │  │   Katib      │  │   KServe     │       │
│  │  (workflows) │  │ (AutoML/HPO) │  │  (serving)   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Notebooks   │  │   Training   │  │   Metadata   │       │
│  │  (Jupyter)   │  │  Operators   │  │    Store     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## LLMOps Considerations

### LLM-Specific Challenges

| Challenge | Solution |
|-----------|----------|
| Large model sizes | Quantization, distillation |
| High inference cost | Batching, caching, edge deployment |
| Prompt engineering | Version prompts, A/B test |
| Hallucination | RAG, fine-tuning, guardrails |
| Evaluation | Custom benchmarks, human eval |

### RAG Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG PIPELINE                              │
│                                                              │
│  Query ──▶ Embed ──▶ Vector Search ──▶ Context + Query      │
│                           │                    │             │
│                    ┌──────▼──────┐      ┌──────▼──────┐     │
│                    │   Vector    │      │    LLM      │     │
│                    │   Store     │      │  (Generate) │     │
│                    └─────────────┘      └──────┬──────┘     │
│                                                │             │
│                                          Response            │
└─────────────────────────────────────────────────────────────┘
```

## Common MLOps Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Notebook to prod | Not reproducible | Proper pipelines |
| No versioning | Can't reproduce | Version everything |
| Training/serving skew | Different predictions | Feature stores |
| No monitoring | Silent failures | Monitor data + model |
| Manual deployments | Slow, error-prone | CI/CD for ML |
| Ignoring drift | Degraded performance | Automated retraining |

## Key Resources

- **MLOps Community** - mlops.community
- **Made With ML** - madewithml.com
- **Full Stack Deep Learning** - fullstackdeeplearning.com
- **Kubeflow Docs** - kubeflow.org
- **MLflow Docs** - mlflow.org

*"A model is only as good as the system that serves it."*
