---
title: "Module 5.3: Model Training & Experimentation"
slug: platform/disciplines/data-ai/mlops/module-5.3-model-training
sidebar:
  order: 4
---
> **Discipline Track** | Complexity: `[COMPLEX]` | Time: 40-45 min

## Prerequisites

Before starting this module:
- [Module 5.1: MLOps Fundamentals](../module-5.1-mlops-fundamentals/)
- [Module 5.2: Feature Engineering & Stores](../module-5.2-feature-stores/)
- Experience training ML models (any framework)
- Basic understanding of hyperparameters

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Implement model training pipelines on Kubernetes using Kubeflow, MLflow, or custom operators**
- **Design experiment tracking workflows that capture hyperparameters, metrics, and artifacts reproducibly**
- **Configure training infrastructure with proper GPU scheduling, checkpointing, and fault tolerance**
- **Build automated hyperparameter tuning using Katib or Optuna on Kubernetes clusters**

## Why This Module Matters

Data scientists run hundreds of experiments. "Try learning rate 0.01... now 0.001... add a layer... remove dropout..." Most of these experiments are lost to time—run in notebooks, results forgotten, impossible to reproduce.

When a model works, the question becomes: "What exactly did we do?" Without experiment tracking, the answer is often "I don't remember." You can't reproduce what you can't track.

Experiment tracking isn't just nice-to-have—it's the difference between scientific machine learning and random guessing.

## Did You Know?

- **The average ML team runs 1,000+ experiments** before finding a production-worthy model—without tracking, most learnings are lost
- **Weights & Biases found that teams using experiment tracking** ship models 2x faster because they don't repeat failed experiments
- **Hyperparameter optimization can improve model performance by 10-50%** but manual tuning rarely explores the full space
- **Random search beats grid search** for hyperparameter optimization in most cases—and this was only proven through systematic experimentation
- **Kubernetes 1.35 introduced native Gang Scheduling** (alpha) — ensuring all pods in an ML training job are scheduled together or not at all, eliminating the deadlock problem where partial pod groups hold resources while waiting for the rest

## The Experiment Tracking Problem

Without proper tracking:

```
DATA SCIENTIST'S NOTEBOOK
─────────────────────────────────────────────────────────────────

Experiment 1: accuracy = 0.85
Experiment 2: accuracy = 0.87  # Better!
Experiment 3: accuracy = 0.82  # Worse
...
Experiment 47: accuracy = 0.91  # Best yet!

Question: What were the hyperparameters for Experiment 47?
Answer: "I think learning_rate was 0.01... or 0.001?"

Question: Can we reproduce Experiment 47?
Answer: "The notebook was modified... let me try..."

Question: What data version was used?
Answer: "Um... the current one? Maybe?"
```

### The Cost of Poor Tracking

| Problem | Impact |
|---------|--------|
| Can't reproduce results | Best model is lost forever |
| Repeat failed experiments | Waste time and compute |
| No comparison baseline | Don't know if new approach is better |
| Lost institutional knowledge | New team members start from scratch |
| Debugging in production | "Which experiment is deployed?" |

## Experiment Tracking with MLflow

MLflow is the most popular open-source experiment tracking tool. It tracks:

```
┌─────────────────────────────────────────────────────────────────┐
│                    MLFLOW TRACKING                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EXPERIMENT: fraud-detection                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ RUN: abc123                                                │  │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │  │
│  │ │ PARAMETERS  │ │   METRICS   │ │     ARTIFACTS       │   │  │
│  │ ├─────────────┤ ├─────────────┤ ├─────────────────────┤   │  │
│  │ │ lr: 0.01    │ │ accuracy:   │ │ model.pkl           │   │  │
│  │ │ epochs: 100 │ │   0.95      │ │ confusion_matrix.png│   │  │
│  │ │ batch: 32   │ │ f1: 0.93    │ │ feature_importance  │   │  │
│  │ │ model: RF   │ │ auc: 0.97   │ │   .csv              │   │  │
│  │ │ seed: 42    │ │ loss: 0.12  │ │ requirements.txt    │   │  │
│  │ └─────────────┘ └─────────────┘ └─────────────────────┘   │  │
│  │                                                            │  │
│  │ TAGS: production-candidate, team-fraud                     │  │
│  │ GIT: commit abc123, branch main                            │  │
│  │ STARTED: 2024-01-15 10:30:00                               │  │
│  │ DURATION: 45 minutes                                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  RUN: def456 │ RUN: ghi789 │ RUN: jkl012 │ ...                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### War Story: The Vanishing Model

A team at a startup had their best fraud model—deployed, working great. Six months later, fraud patterns changed. They needed to retrain.

"Let's start from the best model." But which was it? The data scientist who trained it had left. Notebooks were scattered across laptops. The model file existed but no one knew what hyperparameters produced it.

They spent two weeks recreating experiments from scratch. MLflow would have saved them with one command: `mlflow.search_runs(order_by=['metrics.f1 DESC'])`

## MLflow in Practice

### Basic Tracking

```python
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

# Set experiment
mlflow.set_experiment("fraud-detection")

# Training function with tracking
def train_model(X_train, y_train, X_test, y_test, params):
    with mlflow.start_run():
        # Log parameters
        mlflow.log_params(params)

        # Train model
        model = RandomForestClassifier(**params)
        model.fit(X_train, y_train)

        # Evaluate
        predictions = model.predict(X_test)
        proba = model.predict_proba(X_test)[:, 1]

        accuracy = accuracy_score(y_test, predictions)
        f1 = f1_score(y_test, predictions)
        auc = roc_auc_score(y_test, proba)

        # Log metrics
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1", f1)
        mlflow.log_metric("auc", auc)

        # Log model
        mlflow.sklearn.log_model(model, "model")

        # Log artifacts (plots, reports, etc.)
        mlflow.log_artifact("confusion_matrix.png")

        return model, {"accuracy": accuracy, "f1": f1, "auc": auc}

# Run experiments
params_list = [
    {"n_estimators": 100, "max_depth": 5, "random_state": 42},
    {"n_estimators": 200, "max_depth": 10, "random_state": 42},
    {"n_estimators": 300, "max_depth": 15, "random_state": 42},
]

for params in params_list:
    train_model(X_train, y_train, X_test, y_test, params)
```

### Comparing Experiments

```python
# Find best run
from mlflow.tracking import MlflowClient

client = MlflowClient()
experiment = client.get_experiment_by_name("fraud-detection")

runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    filter_string="metrics.f1 > 0.9",
    order_by=["metrics.f1 DESC"],
    max_results=5,
)

print("Top 5 runs by F1 score:")
for run in runs:
    print(f"  Run {run.info.run_id[:8]}: F1={run.data.metrics['f1']:.4f}")
```

### MLflow UI

```bash
# Start UI server
mlflow ui --port 5000

# Access at http://localhost:5000
```

The UI provides:
- Experiment comparison tables
- Metric visualization (charts, plots)
- Parameter search and filtering
- Artifact browsing
- Run diff comparison

## Model Registry

The Model Registry manages model versions and lifecycle stages:

```
┌─────────────────────────────────────────────────────────────────┐
│                    MODEL REGISTRY                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MODEL: fraud-detector                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  Version 1        Version 2        Version 3              │  │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐            │  │
│  │  │ Archived │    │Production│    │ Staging  │            │  │
│  │  │          │    │          │    │          │            │  │
│  │  │ F1: 0.89 │    │ F1: 0.93 │    │ F1: 0.95 │            │  │
│  │  │ Date:    │    │ Date:    │    │ Date:    │            │  │
│  │  │ Jan 1    │    │ Feb 1    │    │ Mar 1    │            │  │
│  │  └──────────┘    └──────────┘    └──────────┘            │  │
│  │                        │              │                   │  │
│  │                        ▼              ▼                   │  │
│  │                   Live traffic    Shadow traffic          │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Model Stages

| Stage | Purpose |
|-------|---------|
| **None** | Just registered, not evaluated |
| **Staging** | Under evaluation, shadow traffic |
| **Production** | Live traffic, actively monitored |
| **Archived** | Deprecated, kept for reference |

### Using the Registry

```python
import mlflow

# Register model from run
model_uri = f"runs:/{best_run.info.run_id}/model"
model_name = "fraud-detector"

# Register new version
mlflow.register_model(model_uri, model_name)

# Transition stages
client = MlflowClient()
client.transition_model_version_stage(
    name=model_name,
    version=3,
    stage="Staging"
)

# After validation, promote to production
client.transition_model_version_stage(
    name=model_name,
    version=3,
    stage="Production"
)

# Load production model
model = mlflow.sklearn.load_model(f"models:/{model_name}/Production")
```

## Hyperparameter Optimization

### The Search Space Problem

```
HYPERPARAMETER SEARCH SPACE
─────────────────────────────────────────────────────────────────

Model: Random Forest
Parameters:
  n_estimators:  [50, 100, 200, 500, 1000]     = 5 options
  max_depth:     [3, 5, 10, 15, 20, None]      = 6 options
  min_samples:   [2, 5, 10, 20]                = 4 options
  max_features:  ['sqrt', 'log2', None]        = 3 options

Grid Search: 5 × 6 × 4 × 3 = 360 combinations
At 5 min/train: 30 hours!

Random Search: 50 random combinations = 4 hours
  → Often finds near-optimal in ~60 iterations
```

### Grid vs. Random vs. Bayesian

```
SEARCH STRATEGIES
─────────────────────────────────────────────────────────────────

GRID SEARCH                    RANDOM SEARCH
┌─────────────────────┐        ┌─────────────────────┐
│  ●  ●  ●  ●  ●  ●  │        │  ●        ●        │
│  ●  ●  ●  ●  ●  ●  │        │     ●           ●  │
│  ●  ●  ●  ●  ●  ●  │        │        ●     ●     │
│  ●  ●  ●  ●  ●  ●  │        │  ●              ●  │
│  ●  ●  ●  ●  ●  ●  │        │        ●  ●       │
└─────────────────────┘        └─────────────────────┘
Exhaustive but slow            Better coverage, faster

BAYESIAN OPTIMIZATION
┌─────────────────────┐
│  ●        ●     ●  │  Points cluster around
│     ●●●●           │  promising regions
│  ●●●●●●●  ●        │  based on prior results
│     ●●●●           │
│  ●                 │
└─────────────────────┘
Intelligent exploration
```

### Optuna for HPO

```python
import optuna
import mlflow

def objective(trial):
    # Suggest hyperparameters
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 50, 500),
        "max_depth": trial.suggest_int("max_depth", 3, 20),
        "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
        "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
    }

    with mlflow.start_run(nested=True):
        mlflow.log_params(params)

        # Train and evaluate
        model = RandomForestClassifier(**params, random_state=42)
        model.fit(X_train, y_train)
        f1 = f1_score(y_test, model.predict(X_test))

        mlflow.log_metric("f1", f1)

        return f1

# Run optimization
with mlflow.start_run(run_name="hpo-study"):
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=100)

    # Log best params
    mlflow.log_params(study.best_params)
    mlflow.log_metric("best_f1", study.best_value)

print(f"Best F1: {study.best_value:.4f}")
print(f"Best params: {study.best_params}")
```

### Katib (Kubernetes-Native HPO)

For Kubernetes environments, Katib provides distributed HPO:

```yaml
apiVersion: kubeflow.org/v1beta1
kind: Experiment
metadata:
  name: fraud-hpo
spec:
  objective:
    type: maximize
    goal: 0.95
    objectiveMetricName: f1-score
  algorithm:
    algorithmName: bayesianoptimization
  parallelTrialCount: 3
  maxTrialCount: 30
  maxFailedTrialCount: 3
  parameters:
    - name: learning_rate
      parameterType: double
      feasibleSpace:
        min: "0.001"
        max: "0.1"
    - name: num_epochs
      parameterType: int
      feasibleSpace:
        min: "10"
        max: "100"
  trialTemplate:
    primaryContainerName: training
    trialParameters:
      - name: learningRate
        reference: learning_rate
      - name: epochs
        reference: num_epochs
    trialSpec:
      apiVersion: batch/v1
      kind: Job
      spec:
        template:
          spec:
            containers:
              - name: training
                image: my-training-image
                command:
                  - python
                  - train.py
                  - --lr=${trialParameters.learningRate}
                  - --epochs=${trialParameters.epochs}
            restartPolicy: Never
```

## Reproducibility Best Practices

### 1. Version Everything

```python
import mlflow
import subprocess

# Log environment
mlflow.log_artifact("requirements.txt")

# Log git info
git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
git_branch = subprocess.check_output(["git", "branch", "--show-current"]).decode().strip()

mlflow.set_tags({
    "git.commit": git_commit,
    "git.branch": git_branch,
})
```

### 2. Set Random Seeds

```python
import numpy as np
import random
import torch

def set_seeds(seed=42):
    """Set all random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    # For CUDA determinism
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
```

### 3. Data Versioning with DVC

```bash
# Initialize DVC
dvc init

# Track data files
dvc add data/training.csv
git add data/training.csv.dvc .gitignore
git commit -m "Track training data with DVC"

# Push data to remote
dvc remote add -d storage s3://my-bucket/dvc
dvc push

# In MLflow, log data version
mlflow.log_param("data_version", "abc123")  # DVC hash
```

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No experiment names | "What was run xyz?" | Descriptive experiment/run names |
| Missing parameters | Can't reproduce | Log ALL hyperparameters |
| No git tracking | Code version unknown | Auto-log git commit |
| Overwriting runs | History lost | Each run is immutable |
| No validation data | Overfitting to test | Log train/val/test splits |
| Ignoring hardware | "Works on my GPU" | Log hardware, CUDA version |

## Quiz

Test your understanding:

<details>
<summary>1. Why is experiment tracking essential for ML teams?</summary>

**Answer**: Experiment tracking enables:
1. **Reproducibility**: Know exactly what produced each result
2. **Comparison**: Objectively compare approaches
3. **Knowledge preservation**: New team members learn from history
4. **Debugging**: Trace production models to training runs
5. **Compliance**: Audit trail for regulated industries

Without tracking, most experiments are lost, leading to repeated work and inability to reproduce successful models.
</details>

<details>
<summary>2. What's the difference between parameters, metrics, and artifacts in MLflow?</summary>

**Answer**:
- **Parameters**: Inputs to the training process (learning_rate, epochs, batch_size). Set once, don't change during training.
- **Metrics**: Outputs measuring model performance (accuracy, F1, loss). Can be logged multiple times to track progress.
- **Artifacts**: Files generated during training (model files, plots, reports, config files). Stored for later reference.
</details>

<details>
<summary>3. Why does random search often beat grid search?</summary>

**Answer**: Grid search is exhaustive but inefficient:
- Wastes time on unimportant parameter dimensions
- May miss optimal regions between grid points

Random search:
- Better coverage of the search space
- More likely to sample near-optimal regions
- With the same budget, explores more diverse combinations
- Research shows it finds good hyperparameters in ~60 random iterations for most problems
</details>

<details>
<summary>4. What makes a training run reproducible?</summary>

**Answer**: Reproducibility requires tracking:
1. **Code version**: Git commit hash
2. **Data version**: DVC hash or data registry
3. **Dependencies**: requirements.txt, Dockerfile
4. **Hyperparameters**: All model configuration
5. **Random seeds**: For all randomness sources
6. **Hardware**: GPU type, CUDA version
7. **Environment**: OS, Python version

Missing any of these can make reproduction impossible.
</details>

## Hands-On Exercise: Complete Experiment Pipeline

Build a full experiment tracking setup:

### Setup

```bash
mkdir ml-experiments && cd ml-experiments
python -m venv venv
source venv/bin/activate
pip install mlflow scikit-learn optuna pandas matplotlib
```

### Step 1: Create Experiment Script

```python
# train.py
import mlflow
import mlflow.sklearn
import optuna
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
import numpy as np
import matplotlib.pyplot as plt
import subprocess

def get_git_info():
    """Get current git info for tracking."""
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()[:8]
        return {"git_commit": commit}
    except Exception:
        return {"git_commit": "unknown"}

def create_dataset(n_samples=1000, n_features=20, random_state=42):
    """Create synthetic classification dataset."""
    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=10,
        n_redundant=5,
        random_state=random_state,
    )
    return train_test_split(X, y, test_size=0.2, random_state=random_state)

def train_and_evaluate(model, X_train, y_train, X_test, y_test):
    """Train model and return metrics."""
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]

    return {
        "accuracy": accuracy_score(y_test, predictions),
        "f1": f1_score(y_test, predictions),
        "auc": roc_auc_score(y_test, proba),
    }

def plot_feature_importance(model, n_features=20):
    """Create and save feature importance plot."""
    importance = model.feature_importances_
    indices = np.argsort(importance)[::-1][:10]  # Top 10

    plt.figure(figsize=(10, 6))
    plt.title("Feature Importance (Top 10)")
    plt.bar(range(10), importance[indices])
    plt.xticks(range(10), [f"Feature {i}" for i in indices])
    plt.tight_layout()
    plt.savefig("feature_importance.png")
    plt.close()

def run_experiment(model_type, params, X_train, y_train, X_test, y_test):
    """Run single experiment with tracking."""
    with mlflow.start_run():
        # Log git info
        mlflow.set_tags(get_git_info())
        mlflow.set_tag("model_type", model_type)

        # Log parameters
        mlflow.log_params(params)

        # Create model
        if model_type == "random_forest":
            model = RandomForestClassifier(**params, random_state=42)
        else:
            model = GradientBoostingClassifier(**params, random_state=42)

        # Train and evaluate
        metrics = train_and_evaluate(model, X_train, y_train, X_test, y_test)

        # Cross-validation score
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1')
        metrics["cv_f1_mean"] = cv_scores.mean()
        metrics["cv_f1_std"] = cv_scores.std()

        # Log metrics
        mlflow.log_metrics(metrics)

        # Log artifacts
        plot_feature_importance(model)
        mlflow.log_artifact("feature_importance.png")

        # Log model
        mlflow.sklearn.log_model(model, "model")

        return metrics

def hpo_objective(trial, X_train, y_train, X_test, y_test):
    """Optuna objective for HPO."""
    model_type = trial.suggest_categorical("model_type", ["random_forest", "gradient_boosting"])

    if model_type == "random_forest":
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300),
            "max_depth": trial.suggest_int("max_depth", 3, 15),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
        }
    else:
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300),
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3),
        }

    with mlflow.start_run(nested=True):
        mlflow.log_params(params)
        mlflow.set_tag("model_type", model_type)

        if model_type == "random_forest":
            model = RandomForestClassifier(**params, random_state=42)
        else:
            model = GradientBoostingClassifier(**params, random_state=42)

        metrics = train_and_evaluate(model, X_train, y_train, X_test, y_test)
        mlflow.log_metrics(metrics)

        return metrics["f1"]

def main():
    # Setup
    mlflow.set_experiment("classification-experiments")
    X_train, X_test, y_train, y_test = create_dataset()

    # Run HPO study
    with mlflow.start_run(run_name="hpo-study"):
        study = optuna.create_study(direction="maximize")
        study.optimize(
            lambda trial: hpo_objective(trial, X_train, y_train, X_test, y_test),
            n_trials=20,
        )

        # Log best results
        mlflow.log_params(study.best_params)
        mlflow.log_metric("best_f1", study.best_value)

        print(f"\nBest F1: {study.best_value:.4f}")
        print(f"Best params: {study.best_params}")

if __name__ == "__main__":
    main()
```

### Step 2: Run and Analyze

```bash
# Run experiments
python train.py

# Start MLflow UI
mlflow ui

# Open http://localhost:5000 and explore:
# - Compare runs side-by-side
# - View parameter/metric correlations
# - Download artifacts
```

### Step 3: Register Best Model

```python
# register_best.py
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()
experiment = client.get_experiment_by_name("classification-experiments")

# Find best run
runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    filter_string="tags.model_type IS NOT NULL",
    order_by=["metrics.f1 DESC"],
    max_results=1,
)

best_run = runs[0]
print(f"Best run: {best_run.info.run_id}")
print(f"F1: {best_run.data.metrics['f1']:.4f}")

# Register
model_uri = f"runs:/{best_run.info.run_id}/model"
mlflow.register_model(model_uri, "best-classifier")

# Promote to staging
client.transition_model_version_stage(
    name="best-classifier",
    version=1,
    stage="Staging"
)

print("Model registered and promoted to Staging")
```

### Success Criteria

You've completed this exercise when you can:
- [ ] Run HPO with multiple model types
- [ ] View experiments in MLflow UI
- [ ] Compare runs and their parameters
- [ ] Register the best model
- [ ] Transition model to Staging stage

## Key Takeaways

1. **Track everything**: Parameters, metrics, artifacts, code version
2. **Use HPO**: Random/Bayesian search finds better hyperparameters than manual tuning
3. **Reproducibility requires discipline**: Seeds, versions, environment—all must be tracked
4. **Model registry manages lifecycle**: Stage models from development to production
5. **MLflow is a great starting point**: Open source, flexible, widely adopted

## Further Reading

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html) — Complete MLflow guide
- [Optuna Documentation](https://optuna.org/) — HPO library
- [Random Search for Hyper-Parameter Optimization](https://www.jmlr.org/papers/v13/bergstra12a.html) — Foundational paper
- [DVC Documentation](https://dvc.org/doc) — Data versioning

## Summary

Experiment tracking transforms ML from guesswork into science. By tracking parameters, metrics, and artifacts for every run, you build a searchable history of what works (and what doesn't). Combined with hyperparameter optimization, you systematically explore the search space instead of randomly hoping for good results. The model registry then manages the transition from experiment to production.

---

## Next Module

Continue to [Module 5.4: Model Serving & Inference](../module-5.4-model-serving/) to learn how to deploy trained models for production inference.
