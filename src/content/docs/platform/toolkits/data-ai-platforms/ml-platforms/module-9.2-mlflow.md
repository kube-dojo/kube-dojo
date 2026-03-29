---
title: "Module 9.2: MLflow"
slug: platform/toolkits/data-ai-platforms/ml-platforms/module-9.2-mlflow
sidebar:
  order: 3
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes

## Overview

MLflow is the experiment tracking and model registry tool that data scientists actually use. While Kubeflow handles infrastructure, MLflow handles the metadata—what parameters did you try, what metrics did you get, where is the model? This module covers MLflow's core components and Kubernetes deployment.

**What You'll Learn**:
- MLflow Tracking for experiments
- Model Registry for lifecycle management
- MLflow on Kubernetes deployment
- Integration with Kubeflow Pipelines
- When to use MLflow vs alternatives

**Prerequisites**:
- Python basics
- Basic ML concepts
- Kubernetes fundamentals
- [MLOps Discipline](../../../disciplines/data-ai/mlops/) recommended

---

## Why This Module Matters

Data scientists run hundreds of experiments. Without tracking, they lose which parameters produced which results. MLflow provides a central record of every experiment, making ML reproducible. It's the Git for machine learning—you wouldn't code without version control, and you shouldn't train models without experiment tracking.

> 💡 **Did You Know?** MLflow was created by Databricks and open-sourced in 2018. It became the most popular ML experiment tracking tool because it was framework-agnostic and simple. While competitors required specific ML frameworks or complex setups, MLflow worked with any Python code by adding just a few lines. Simplicity won.

---

## MLflow Architecture

```
MLFLOW COMPONENTS
════════════════════════════════════════════════════════════════════

                    ┌─────────────────────────────────────────┐
                    │           MLflow Tracking Server         │
                    │                                          │
                    │  ┌────────────┐    ┌────────────────┐  │
                    │  │  Backend   │    │  Artifact Store │  │
                    │  │   Store    │    │    (S3/GCS)     │  │
                    │  │ (Postgres) │    │                 │  │
                    │  └────────────┘    └────────────────┘  │
                    └────────────────────┬────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         │                               │                               │
         ▼                               ▼                               ▼
┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
│   Experiments   │           │     Models      │           │     Projects    │
│                 │           │                 │           │                 │
│ • Runs          │           │ • Registry      │           │ • Packaging     │
│ • Parameters    │           │ • Versions      │           │ • Dependencies  │
│ • Metrics       │           │ • Stages        │           │ • Reproducibility│
│ • Artifacts     │           │ • Aliases       │           │                 │
└─────────────────┘           └─────────────────┘           └─────────────────┘

DATA FLOW:
─────────────────────────────────────────────────────────────────

Training Code                    MLflow Server                 Storage
     │                               │                            │
     │  mlflow.log_param("lr", 0.01)│                            │
     │ ─────────────────────────────▶                            │
     │                               │ Store in Postgres          │
     │                               │ ────────────────────────▶  │
     │                               │                            │
     │  mlflow.log_artifact(model)  │                            │
     │ ─────────────────────────────▶                            │
     │                               │ Upload to S3               │
     │                               │ ────────────────────────▶  │
```

### Core Components

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| **Tracking** | Log experiments | Parameters, metrics, artifacts |
| **Registry** | Model lifecycle | Versions, stages, aliases |
| **Projects** | Reproducibility | Package code + dependencies |
| **Models** | Deployment | Unified model format |

> 💡 **Did You Know?** MLflow's Model Registry introduced the concept of "model stages" (Staging, Production, Archived) to ML. This simple idea transformed how teams think about models—not as files but as artifacts with lifecycles. A model in "Staging" means something different than one in "Production," and everyone on the team knows it.

---

## MLflow Tracking

### Basic Tracking

```python
# train.py
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

# Set tracking URI (server address)
mlflow.set_tracking_uri("http://mlflow-server:5000")

# Set experiment
mlflow.set_experiment("iris-classification")

# Load data
iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(
    iris.data, iris.target, test_size=0.2
)

# Start a run
with mlflow.start_run():
    # Log parameters
    n_estimators = 100
    max_depth = 10
    mlflow.log_param("n_estimators", n_estimators)
    mlflow.log_param("max_depth", max_depth)

    # Train model
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth
    )
    model.fit(X_train, y_train)

    # Log metrics
    accuracy = model.score(X_test, y_test)
    mlflow.log_metric("accuracy", accuracy)

    # Log model
    mlflow.sklearn.log_model(model, "model")

    print(f"Run ID: {mlflow.active_run().info.run_id}")
    print(f"Accuracy: {accuracy}")
```

### Autologging

```python
# autolog.py
import mlflow

# Enable autologging for supported frameworks
mlflow.autolog()

# For specific frameworks:
mlflow.sklearn.autolog()
mlflow.pytorch.autolog()
mlflow.tensorflow.autolog()
mlflow.xgboost.autolog()

# Now just train - everything is logged automatically
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)
# Parameters, metrics, and model logged automatically!
```

### Tracking Custom Artifacts

```python
import mlflow
import matplotlib.pyplot as plt
import json

with mlflow.start_run():
    # Log parameters and train...

    # Log confusion matrix as image
    plt.figure()
    # ... create confusion matrix plot ...
    plt.savefig("confusion_matrix.png")
    mlflow.log_artifact("confusion_matrix.png")

    # Log custom JSON
    metadata = {
        "training_date": "2024-01-15",
        "data_version": "v2.3",
        "feature_count": 10
    }
    with open("metadata.json", "w") as f:
        json.dump(metadata, f)
    mlflow.log_artifact("metadata.json")

    # Log entire directory
    mlflow.log_artifacts("./plots", artifact_path="visualizations")
```

---

## MLflow on Kubernetes

### Deployment Architecture

```yaml
# mlflow-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow-server
  namespace: mlflow
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mlflow
  template:
    metadata:
      labels:
        app: mlflow
    spec:
      containers:
      - name: mlflow
        image: ghcr.io/mlflow/mlflow:v2.9.0
        command:
        - mlflow
        - server
        - --host=0.0.0.0
        - --port=5000
        - --backend-store-uri=postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgres:5432/mlflow
        - --default-artifact-root=s3://mlflow-artifacts/
        - --serve-artifacts
        ports:
        - containerPort: 5000
        env:
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: mlflow-secrets
              key: postgres-user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mlflow-secrets
              key: postgres-password
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: mlflow-secrets
              key: aws-access-key
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: mlflow-secrets
              key: aws-secret-key
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
---
apiVersion: v1
kind: Service
metadata:
  name: mlflow-server
  namespace: mlflow
spec:
  selector:
    app: mlflow
  ports:
  - port: 5000
    targetPort: 5000
  type: ClusterIP
```

### PostgreSQL Backend

```yaml
# postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: mlflow
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: mlflow
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: mlflow-secrets
              key: postgres-user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mlflow-secrets
              key: postgres-password
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

### Ingress Configuration

```yaml
# mlflow-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mlflow-ingress
  namespace: mlflow
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/auth-type: basic
    nginx.ingress.kubernetes.io/auth-secret: mlflow-basic-auth
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - mlflow.example.com
    secretName: mlflow-tls
  rules:
  - host: mlflow.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: mlflow-server
            port:
              number: 5000
```

> 💡 **Did You Know?** MLflow 2.0 introduced "serve-artifacts" mode where the tracking server proxies artifact uploads. This solved a common pain point: clients no longer need direct access to S3/GCS. They just talk to MLflow, which handles storage. This simplified network configurations significantly, especially in Kubernetes.

> 💡 **Did You Know?** MLflow's `search_runs()` API uses a SQL-like syntax that can query across thousands of experiments in milliseconds. You can find "all runs with accuracy > 0.95 and learning_rate < 0.01" instantly. Before this, teams would export CSVs and write pandas queries—now it's built into the platform. Some organizations have millions of logged runs, all queryable through this single API.

---

## Model Registry

### Registering Models

```python
import mlflow
from mlflow.tracking import MlflowClient

# Register during training
with mlflow.start_run():
    # Train model...
    mlflow.sklearn.log_model(
        model,
        "model",
        registered_model_name="iris-classifier"
    )

# Or register from existing run
client = MlflowClient()
result = client.create_registered_model("iris-classifier")

# Create version from run
run_id = "abc123..."
model_uri = f"runs:/{run_id}/model"
client.create_model_version(
    name="iris-classifier",
    source=model_uri,
    run_id=run_id
)
```

### Model Stages and Aliases

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Transition to staging
client.transition_model_version_stage(
    name="iris-classifier",
    version=1,
    stage="Staging"
)

# Transition to production
client.transition_model_version_stage(
    name="iris-classifier",
    version=1,
    stage="Production"
)

# Using aliases (MLflow 2.3+)
client.set_registered_model_alias(
    name="iris-classifier",
    alias="champion",
    version=1
)

# Load by alias
model = mlflow.pyfunc.load_model("models:/iris-classifier@champion")
```

### Model Registry Workflow

```
MODEL REGISTRY WORKFLOW
════════════════════════════════════════════════════════════════════

Version 1 ──▶ None ──▶ Staging ──▶ Production ──▶ Archived
   │                      │            │
   │                      ▼            ▼
   │                   Testing      Serving
   │                   Validation   Inference
   │
Version 2 ──▶ None ──▶ Staging ──▶ Production
                          │            │
                          ▼            ▼
                       Testing      (replaces v1)
                       A/B Test

ALIAS WORKFLOW (Recommended):
─────────────────────────────────────────────────────────────────

Version 1 ◀── alias: "champion" ◀── Production uses this
Version 2 ◀── alias: "challenger"
Version 3     (no alias - testing)

# Switch production in one command:
client.set_registered_model_alias("model", "champion", version=2)
```

---

## Integration with Kubeflow

### MLflow in Kubeflow Pipelines

```python
# pipeline_with_mlflow.py
from kfp import dsl
from kfp.dsl import Dataset, Model, Output, Input

@dsl.component(
    base_image="python:3.10",
    packages_to_install=["mlflow", "scikit-learn", "boto3"]
)
def train_with_mlflow(
    mlflow_uri: str,
    experiment_name: str,
    n_estimators: int,
    output_run_id: Output[str]
):
    import mlflow
    import mlflow.sklearn
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split

    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment(experiment_name)

    iris = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(
        iris.data, iris.target, test_size=0.2
    )

    with mlflow.start_run() as run:
        mlflow.log_param("n_estimators", n_estimators)

        model = RandomForestClassifier(n_estimators=n_estimators)
        model.fit(X_train, y_train)

        accuracy = model.score(X_test, y_test)
        mlflow.log_metric("accuracy", accuracy)

        mlflow.sklearn.log_model(
            model, "model",
            registered_model_name="iris-classifier"
        )

        # Output run ID for downstream components
        with open(output_run_id.path, "w") as f:
            f.write(run.info.run_id)

@dsl.pipeline(name="mlflow-training-pipeline")
def training_pipeline(
    mlflow_uri: str = "http://mlflow-server.mlflow:5000",
    experiment_name: str = "kubeflow-experiments",
    n_estimators: int = 100
):
    train_task = train_with_mlflow(
        mlflow_uri=mlflow_uri,
        experiment_name=experiment_name,
        n_estimators=n_estimators
    )
```

---

## MLflow Model Serving

### Local Serving

```bash
# Serve model from registry
mlflow models serve \
  --model-uri "models:/iris-classifier@champion" \
  --host 0.0.0.0 \
  --port 5001

# Test endpoint
curl -X POST http://localhost:5001/invocations \
  -H "Content-Type: application/json" \
  -d '{"inputs": [[5.1, 3.5, 1.4, 0.2]]}'
```

### Kubernetes Serving

```yaml
# mlflow-model-server.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iris-model-server
  namespace: ml-serving
spec:
  replicas: 3
  selector:
    matchLabels:
      app: iris-model
  template:
    metadata:
      labels:
        app: iris-model
    spec:
      containers:
      - name: model-server
        image: ghcr.io/mlflow/mlflow:v2.9.0
        command:
        - mlflow
        - models
        - serve
        - --model-uri=models:/iris-classifier@champion
        - --host=0.0.0.0
        - --port=5001
        - --no-conda
        ports:
        - containerPort: 5001
        env:
        - name: MLFLOW_TRACKING_URI
          value: "http://mlflow-server.mlflow:5000"
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: mlflow-secrets
              key: aws-access-key
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: mlflow-secrets
              key: aws-secret-key
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
        readinessProbe:
          httpGet:
            path: /health
            port: 5001
---
apiVersion: v1
kind: Service
metadata:
  name: iris-model-server
  namespace: ml-serving
spec:
  selector:
    app: iris-model
  ports:
  - port: 80
    targetPort: 5001
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No tracking URI set | Logs to local ./mlruns | Set MLFLOW_TRACKING_URI |
| Missing artifact store | Model files lost | Configure S3/GCS backend |
| No run context | Metrics not logged | Use `with mlflow.start_run():` |
| Logging in loops | Thousands of metrics | Log after training, not per iteration |
| No model signature | Serving issues | Use `infer_signature()` |
| Ignoring run IDs | Can't reproduce | Always log/save run ID |

---

## War Story: The Lost Experiment

*A data scientist achieved 98% accuracy. Best model ever! But they forgot which parameters produced it. They spent a week trying to reproduce it.*

**What went wrong**:
1. Running experiments in Jupyter without MLflow
2. Overwriting variables as they experimented
3. No systematic parameter tracking
4. "I'll remember which one was best"

**The fix**:
```python
# Always track, even in notebooks
import mlflow

mlflow.set_tracking_uri("http://mlflow-server:5000")
mlflow.set_experiment("notebook-experiments")

# Now every experiment is recorded
with mlflow.start_run(run_name="experiment-v42"):
    mlflow.log_params({
        "learning_rate": 0.01,
        "batch_size": 32,
        "epochs": 100,
        "architecture": "resnet50"
    })
    # Train...
    mlflow.log_metric("accuracy", 0.98)
    mlflow.log_model(model, "model")

# Later: "Which run had 98% accuracy?"
# Just filter in MLflow UI or:
runs = mlflow.search_runs(filter_string="metrics.accuracy > 0.97")
```

**Lesson**: If you didn't log it, it didn't happen.

---

## Quiz

### Question 1
What's the difference between MLflow Tracking and Model Registry?

<details>
<summary>Show Answer</summary>

**MLflow Tracking**:
- Logs individual training runs
- Captures parameters, metrics, artifacts
- Organized by experiments
- Focus: "What did I try?"

**Model Registry**:
- Manages model lifecycle
- Versions of registered models
- Stages (Staging, Production)
- Aliases for easy reference
- Focus: "Which model should I use?"

Tracking is for experimentation. Registry is for production. A model logged in tracking can be promoted to the registry when it's ready for deployment.

</details>

### Question 2
Why use MLflow with Kubeflow Pipelines?

<details>
<summary>Show Answer</summary>

They solve different problems:

**Kubeflow Pipelines**:
- Orchestrates ML workflows
- Manages compute resources
- Handles data flow between steps
- Kubernetes-native execution

**MLflow**:
- Tracks experiment metadata
- Manages model versions
- Framework-agnostic
- Works outside Kubernetes too

Together:
- Kubeflow runs the pipeline
- MLflow tracks what happened
- Models registered in MLflow can be served by KServe
- Best of both: reproducible workflows + experiment tracking

</details>

### Question 3
How do model aliases improve deployment?

<details>
<summary>Show Answer</summary>

**Without aliases** (stage-based):
```python
# Load "Production" stage model
model = mlflow.pyfunc.load_model("models:/mymodel/Production")

# Problem: Only one model per stage
# Problem: Stage transitions are destructive
```

**With aliases**:
```python
# Load by alias
model = mlflow.pyfunc.load_model("models:/mymodel@champion")

# Benefits:
# - Multiple aliases per model
# - Switch production with one command
# - Keep "champion" and "challenger" simultaneously
# - Alias history tracked

# Switch production:
client.set_registered_model_alias("mymodel", "champion", version=5)
# All services loading @champion now get version 5
```

Aliases provide atomic, rollback-safe deployments.

</details>

---

## Hands-On Exercise

### Objective
Deploy MLflow on Kubernetes and track an ML experiment.

### Tasks

1. **Create MLflow namespace and secrets**:
   ```bash
   kubectl create namespace mlflow

   kubectl create secret generic mlflow-secrets \
     --namespace mlflow \
     --from-literal=postgres-user=mlflow \
     --from-literal=postgres-password=mlflow123
   ```

2. **Deploy minimal MLflow** (SQLite, no S3):
   ```yaml
   # Save as mlflow-minimal.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: mlflow-server
     namespace: mlflow
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: mlflow
     template:
       metadata:
         labels:
           app: mlflow
       spec:
         containers:
         - name: mlflow
           image: ghcr.io/mlflow/mlflow:v2.9.0
           command: ["mlflow", "server", "--host=0.0.0.0", "--port=5000"]
           ports:
           - containerPort: 5000
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: mlflow-server
     namespace: mlflow
   spec:
     selector:
       app: mlflow
     ports:
     - port: 5000
   ```

   ```bash
   kubectl apply -f mlflow-minimal.yaml
   ```

3. **Port-forward and access UI**:
   ```bash
   kubectl port-forward -n mlflow svc/mlflow-server 5000:5000
   # Open http://localhost:5000
   ```

4. **Run tracking example**:
   ```python
   # tracking_example.py
   import mlflow

   mlflow.set_tracking_uri("http://localhost:5000")
   mlflow.set_experiment("k8s-demo")

   with mlflow.start_run():
       mlflow.log_param("learning_rate", 0.01)
       mlflow.log_param("epochs", 10)
       mlflow.log_metric("accuracy", 0.95)
       mlflow.log_metric("loss", 0.05)
       print(f"Run: {mlflow.active_run().info.run_id}")
   ```

   ```bash
   pip install mlflow
   python tracking_example.py
   ```

5. **View in UI**:
   - Refresh http://localhost:5000
   - Click on "k8s-demo" experiment
   - See logged parameters and metrics

6. **Clean up**:
   ```bash
   kubectl delete namespace mlflow
   ```

### Success Criteria
- [ ] MLflow deployed on Kubernetes
- [ ] UI accessible via port-forward
- [ ] Experiment created and visible
- [ ] Parameters and metrics logged
- [ ] Can compare multiple runs

### Bonus Challenge
Register a model to the Model Registry and load it by alias.

---

## Further Reading

- [MLflow Documentation](https://mlflow.org/docs/latest/)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)
- [MLflow on Kubernetes Guide](https://mlflow.org/docs/latest/tracking.html#scenario-5-mlflow-tracking-server-enabled-with-proxied-artifact-storage-access)
- [MLflow + Kubeflow Integration](https://www.kubeflow.org/docs/external-add-ons/mlflow/)

---

## Next Module

Continue to [Module 9.3: Feature Stores](module-9.3-feature-stores/) to learn about managing ML features at scale.

---

*"Experiment tracking isn't overhead—it's insurance. Every hour you spend logging is paid back tenfold when you need to reproduce results or debug a production model."*
