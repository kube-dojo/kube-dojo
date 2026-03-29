---
title: "Module 9.1: Kubeflow"
slug: platform/toolkits/data-ai-platforms/ml-platforms/module-9.1-kubeflow
sidebar:
  order: 2
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 50-60 minutes

## Overview

Kubeflow brings machine learning workflows to Kubernetes. It's not a single tool but a platform—pipelines, notebooks, model serving, and experiment tracking all running on K8s. This module covers Kubeflow's architecture and core components for production ML.

**What You'll Learn**:
- Kubeflow architecture and components
- Kubeflow Pipelines for ML workflows
- Notebooks and experiment management
- Model serving with KServe
- When to use Kubeflow vs simpler alternatives

**Prerequisites**:
- Kubernetes fundamentals
- Basic ML concepts (training, inference)
- Python familiarity
- [MLOps Discipline](../../../disciplines/data-ai/mlops/) recommended

---

## Why This Module Matters

ML teams struggle with the gap between experimentation and production. Data scientists work in notebooks; production needs containers, scaling, and monitoring. Kubeflow bridges this gap by providing a Kubernetes-native platform for the entire ML lifecycle.

> 💡 **Did You Know?** Kubeflow started at Google in 2017 as a way to run TensorFlow on Kubernetes. The name combines "Kube" (Kubernetes) and "Flow" (TensorFlow). It quickly evolved beyond TensorFlow to support any ML framework—PyTorch, XGBoost, scikit-learn—because the real problem was never the framework but the infrastructure.

---

## Kubeflow Architecture

```
KUBEFLOW PLATFORM ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                     KUBEFLOW DASHBOARD                          │
│              (Central UI for all components)                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    ▼                       ▼                       ▼
┌─────────┐          ┌─────────────┐          ┌─────────┐
│Notebooks│          │  Pipelines  │          │ KServe  │
│  (Dev)  │          │  (Workflow) │          │ (Serve) │
└────┬────┘          └──────┬──────┘          └────┬────┘
     │                      │                      │
     │                      ▼                      │
     │              ┌─────────────┐                │
     │              │  Katib      │                │
     │              │(AutoML/HPO) │                │
     │              └─────────────┘                │
     │                                             │
     └──────────────────┬──────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        KUBERNETES                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Training   │  │   Storage    │  │   GPUs/TPUs  │          │
│  │   Operators  │  │  (PVC, S3)   │  │  (Scheduler) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| **Notebooks** | JupyterHub for teams | Interactive development |
| **Pipelines** | ML workflow orchestration | Automated training |
| **KServe** | Model serving | Production inference |
| **Katib** | Hyperparameter tuning | AutoML, optimization |
| **Training Operators** | Distributed training | TF, PyTorch, MPI jobs |

> 💡 **Did You Know?** Kubeflow Pipelines was inspired by Airflow but designed specifically for ML. Unlike Airflow (which passes small data between tasks), Kubeflow Pipelines uses artifacts—large files like datasets and models—stored in object storage. This solved the "my model is too big to pass between steps" problem that plagued early ML automation.

---

## Installation

### Kubeflow Manifests (Production)

```bash
# Clone manifests repository
git clone https://github.com/kubeflow/manifests.git
cd manifests

# Install with kustomize (requires cert-manager, istio)
while ! kustomize build example | kubectl apply -f -; do
  echo "Retrying..."
  sleep 10
done

# This installs everything - can take 10-15 minutes
kubectl get pods -n kubeflow --watch
```

### Lightweight Alternative (Development)

```bash
# For local development, use kind + minimal install
kind create cluster --name kubeflow

# Install just Pipelines (most commonly needed component)
export PIPELINE_VERSION=2.0.5
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/platform-agnostic-pns?ref=$PIPELINE_VERSION"

# Access UI
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
```

---

## Kubeflow Pipelines

### Pipeline Concepts

```
PIPELINE STRUCTURE
════════════════════════════════════════════════════════════════════

Pipeline Definition (Python DSL)
         │
         ▼
    ┌─────────┐
    │  Step 1 │──▶ Container execution
    │  (Load) │    Output: dataset artifact
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │  Step 2 │──▶ Container execution
    │ (Train) │    Input: dataset, Output: model
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │  Step 3 │──▶ Container execution
    │ (Eval)  │    Input: model, Output: metrics
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │  Step 4 │──▶ Container execution
    │(Deploy) │    Conditional on metrics
    └─────────┘
```

### Creating a Pipeline (KFP v2)

```python
# pipeline.py
from kfp import dsl
from kfp.dsl import Dataset, Model, Metrics, Output, Input

@dsl.component(
    base_image="python:3.10",
    packages_to_install=["pandas", "scikit-learn"]
)
def load_data(output_dataset: Output[Dataset]):
    """Load and prepare training data."""
    import pandas as pd
    from sklearn.datasets import load_iris

    iris = load_iris(as_frame=True)
    df = iris.frame
    df.to_csv(output_dataset.path, index=False)

@dsl.component(
    base_image="python:3.10",
    packages_to_install=["pandas", "scikit-learn", "joblib"]
)
def train_model(
    dataset: Input[Dataset],
    output_model: Output[Model],
    n_estimators: int = 100
):
    """Train a RandomForest classifier."""
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    import joblib

    df = pd.read_csv(dataset.path)
    X = df.drop("target", axis=1)
    y = df["target"]

    model = RandomForestClassifier(n_estimators=n_estimators)
    model.fit(X, y)

    joblib.dump(model, output_model.path)

@dsl.component(
    base_image="python:3.10",
    packages_to_install=["pandas", "scikit-learn", "joblib"]
)
def evaluate_model(
    dataset: Input[Dataset],
    model: Input[Model],
    metrics: Output[Metrics]
):
    """Evaluate model accuracy."""
    import pandas as pd
    from sklearn.model_selection import cross_val_score
    import joblib

    df = pd.read_csv(dataset.path)
    X = df.drop("target", axis=1)
    y = df["target"]

    clf = joblib.load(model.path)
    scores = cross_val_score(clf, X, y, cv=5)

    metrics.log_metric("accuracy", float(scores.mean()))
    metrics.log_metric("std", float(scores.std()))

@dsl.pipeline(name="iris-training-pipeline")
def iris_pipeline(n_estimators: int = 100):
    """End-to-end ML training pipeline."""
    load_task = load_data()
    train_task = train_model(
        dataset=load_task.outputs["output_dataset"],
        n_estimators=n_estimators
    )
    evaluate_model(
        dataset=load_task.outputs["output_dataset"],
        model=train_task.outputs["output_model"]
    )

# Compile pipeline
if __name__ == "__main__":
    from kfp import compiler
    compiler.Compiler().compile(iris_pipeline, "iris_pipeline.yaml")
```

### Running Pipelines

```python
# Submit pipeline
from kfp.client import Client

client = Client(host="http://localhost:8080")

# Create a run
run = client.create_run_from_pipeline_package(
    "iris_pipeline.yaml",
    arguments={"n_estimators": 200},
    experiment_name="iris-experiments"
)

print(f"Run ID: {run.run_id}")
```

### Pipeline with Conditionals

```python
@dsl.pipeline(name="conditional-deploy-pipeline")
def conditional_pipeline(accuracy_threshold: float = 0.9):
    """Deploy only if accuracy meets threshold."""
    load_task = load_data()
    train_task = train_model(dataset=load_task.outputs["output_dataset"])
    eval_task = evaluate_model(
        dataset=load_task.outputs["output_dataset"],
        model=train_task.outputs["output_model"]
    )

    with dsl.Condition(
        eval_task.outputs["metrics"].get("accuracy") > accuracy_threshold
    ):
        deploy_model(model=train_task.outputs["output_model"])
```

> 💡 **Did You Know?** Kubeflow Pipelines v2 uses a new intermediate representation (IR) that's cloud-agnostic. The same pipeline YAML can run on Kubeflow, Vertex AI Pipelines (Google Cloud), or Amazon SageMaker Pipelines. Write once, run anywhere—the Docker promise finally coming to ML workflows.

---

## Kubeflow Notebooks

### Notebook Server Configuration

```yaml
# notebook-server.yaml
apiVersion: kubeflow.org/v1
kind: Notebook
metadata:
  name: my-notebook
  namespace: kubeflow-user
spec:
  template:
    spec:
      containers:
      - name: notebook
        image: kubeflownotebookswg/jupyter-scipy:v1.8.0
        resources:
          requests:
            cpu: "1"
            memory: 2Gi
          limits:
            cpu: "2"
            memory: 4Gi
            nvidia.com/gpu: "1"  # Request GPU
        volumeMounts:
        - name: workspace
          mountPath: /home/jovyan
      volumes:
      - name: workspace
        persistentVolumeClaim:
          claimName: notebook-pvc
```

### Notebook with GPU

```yaml
# gpu-notebook.yaml
apiVersion: kubeflow.org/v1
kind: Notebook
metadata:
  name: gpu-notebook
  namespace: kubeflow-user
spec:
  template:
    spec:
      containers:
      - name: notebook
        image: kubeflownotebookswg/jupyter-pytorch-cuda-full:v1.8.0
        resources:
          limits:
            nvidia.com/gpu: "1"
        env:
        - name: NVIDIA_VISIBLE_DEVICES
          value: "all"
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
```

---

## Model Serving with KServe

### InferenceService Basics

```yaml
# inference-service.yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: iris-classifier
  namespace: kubeflow-user
spec:
  predictor:
    sklearn:
      storageUri: "s3://models/iris/v1"
      resources:
        requests:
          cpu: 100m
          memory: 256Mi
        limits:
          cpu: 1
          memory: 1Gi
```

### Custom Model Server

```yaml
# custom-model.yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: custom-model
spec:
  predictor:
    containers:
    - name: kserve-container
      image: myregistry/custom-model:v1
      ports:
      - containerPort: 8080
        protocol: TCP
      env:
      - name: MODEL_PATH
        value: /mnt/models
      volumeMounts:
      - name: model-storage
        mountPath: /mnt/models
```

### Canary Deployments

```yaml
# canary-inference.yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: iris-classifier
spec:
  predictor:
    canaryTrafficPercent: 10  # 10% to new version
    sklearn:
      storageUri: "s3://models/iris/v2"
  # Previous version continues to receive 90%
```

---

## Hyperparameter Tuning with Katib

### Experiment Definition

```yaml
# katib-experiment.yaml
apiVersion: kubeflow.org/v1beta1
kind: Experiment
metadata:
  name: random-forest-tuning
  namespace: kubeflow
spec:
  objective:
    type: maximize
    goal: 0.99
    objectiveMetricName: accuracy
  algorithm:
    algorithmName: bayesianoptimization
  parallelTrialCount: 3
  maxTrialCount: 12
  maxFailedTrialCount: 3
  parameters:
  - name: n_estimators
    parameterType: int
    feasibleSpace:
      min: "50"
      max: "300"
  - name: max_depth
    parameterType: int
    feasibleSpace:
      min: "3"
      max: "20"
  - name: min_samples_split
    parameterType: int
    feasibleSpace:
      min: "2"
      max: "10"
  trialTemplate:
    primaryContainerName: training-container
    trialParameters:
    - name: n_estimators
      reference: n_estimators
    - name: max_depth
      reference: max_depth
    - name: min_samples_split
      reference: min_samples_split
    trialSpec:
      apiVersion: batch/v1
      kind: Job
      spec:
        template:
          spec:
            containers:
            - name: training-container
              image: myregistry/rf-trainer:v1
              command:
              - "python"
              - "/app/train.py"
              - "--n_estimators=${trialParameters.n_estimators}"
              - "--max_depth=${trialParameters.max_depth}"
              - "--min_samples_split=${trialParameters.min_samples_split}"
            restartPolicy: Never
```

### Katib Algorithms

```
KATIB OPTIMIZATION ALGORITHMS
════════════════════════════════════════════════════════════════════

Algorithm               Best For                    Speed
─────────────────────────────────────────────────────────────────
random                  Baseline, exploration       Fast
grid                    Small search spaces         Slow
bayesianoptimization    Continuous parameters       Medium
tpe                     Mixed parameter types       Medium
cmaes                   Continuous, many params     Medium
hyperband               Large search spaces         Fast
enas                    Neural architecture         Slow
darts                   Neural architecture         Slow
─────────────────────────────────────────────────────────────────
```

---

## Training Operators

### PyTorch Distributed Training

```yaml
# pytorch-job.yaml
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: pytorch-distributed
  namespace: kubeflow
spec:
  pytorchReplicaSpecs:
    Master:
      replicas: 1
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime
            command:
            - "python"
            - "-m"
            - "torch.distributed.launch"
            - "--nproc_per_node=1"
            - "train.py"
            resources:
              limits:
                nvidia.com/gpu: 1
    Worker:
      replicas: 3
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime
            command:
            - "python"
            - "-m"
            - "torch.distributed.launch"
            - "--nproc_per_node=1"
            - "train.py"
            resources:
              limits:
                nvidia.com/gpu: 1
```

### TensorFlow Distributed Training

```yaml
# tfjob.yaml
apiVersion: kubeflow.org/v1
kind: TFJob
metadata:
  name: tf-distributed
spec:
  tfReplicaSpecs:
    PS:
      replicas: 2
      template:
        spec:
          containers:
          - name: tensorflow
            image: tensorflow/tensorflow:2.13.0-gpu
    Worker:
      replicas: 4
      template:
        spec:
          containers:
          - name: tensorflow
            image: tensorflow/tensorflow:2.13.0-gpu
            resources:
              limits:
                nvidia.com/gpu: 1
```

> 💡 **Did You Know?** The Training Operators (TFJob, PyTorchJob, MPIJob) handle the hardest part of distributed training: coordinating workers. They set environment variables like `WORLD_SIZE`, `RANK`, and `MASTER_ADDR` automatically. Before these operators, teams spent weeks writing custom scripts to manage distributed training on Kubernetes.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Installing full Kubeflow for simple needs | Resource waste, complexity | Start with just Pipelines |
| Not setting resource limits | OOM kills, node starvation | Always set requests/limits |
| Ignoring artifact storage | Pipeline data lost | Configure S3/GCS properly |
| Skipping namespace isolation | Security, resource conflicts | Use Kubeflow profiles |
| No GPU node taints | GPU pods scheduled anywhere | Taint GPU nodes |
| Large Docker images | Slow pipeline starts | Use base images + pip install |

---

## War Story: The 10-Hour Pipeline

*A team built a beautiful Kubeflow pipeline: load data, preprocess, train, evaluate, deploy. Each step was a separate container. The pipeline took 10 hours to run.*

**What went wrong**:
1. Each step downloaded the full dataset from S3 (100GB)
2. Containers started from scratch every time
3. No caching of intermediate results
4. GPU was idle during data preprocessing

**The fix**:
```python
# Use artifacts to pass data between steps
@dsl.component
def preprocess(
    raw_data: Input[Dataset],
    processed_data: Output[Dataset]  # Artifact, not S3 path
):
    # Data flows through artifact storage
    # Next step picks up where this left off
    ...

# Enable caching for deterministic steps
@dsl.component
def load_data(output: Output[Dataset]):
    ...

load_task = load_data()
load_task.set_caching_options(True)  # Cache if inputs unchanged
```

**Result**: Pipeline went from 10 hours to 45 minutes. 90% of time was data transfer, not computation.

---

## Quiz

### Question 1
When should you use full Kubeflow vs just Kubeflow Pipelines?

<details>
<summary>Show Answer</summary>

**Full Kubeflow**:
- Multiple data science teams
- Need shared notebook servers
- Want integrated experiment tracking
- Require Katib for AutoML
- Enterprise with authentication needs

**Just Pipelines**:
- Single team or project
- Already have notebooks elsewhere
- Just need workflow orchestration
- Simpler deployment requirements
- Want to add components incrementally

Start with Pipelines. Add components as you need them.

</details>

### Question 2
How does Kubeflow Pipelines handle data between steps?

<details>
<summary>Show Answer</summary>

Kubeflow Pipelines uses **artifacts**:

1. Each step is a container
2. Outputs are saved to artifact storage (S3, GCS, MinIO)
3. Next step downloads artifacts as inputs
4. Metadata tracked in ML Metadata store

```python
@dsl.component
def step1(output: Output[Dataset]):
    # Saves to artifact storage
    df.to_csv(output.path)

@dsl.component
def step2(input_data: Input[Dataset]):
    # Downloads from artifact storage
    df = pd.read_csv(input_data.path)
```

This differs from Airflow (XCom) which passes small data in the database.

</details>

### Question 3
What problem does Katib solve?

<details>
<summary>Show Answer</summary>

Katib solves **hyperparameter optimization (HPO)** and **neural architecture search (NAS)**:

**Without Katib**:
- Manually try different hyperparameters
- Run experiments serially
- Track results in spreadsheets
- Waste compute on bad configurations

**With Katib**:
- Define search space declaratively
- Run trials in parallel
- Automatic early stopping of bad trials
- Bayesian optimization to find optima faster
- Results tracked and comparable

Katib is "AutoML for Kubernetes"—it automates the tedious hyperparameter search.

</details>

---

## Hands-On Exercise

### Objective
Deploy Kubeflow Pipelines and run an ML training pipeline.

### Tasks

1. **Install Kubeflow Pipelines**:
   ```bash
   # Create cluster
   kind create cluster --name kubeflow-lab

   # Install Pipelines
   export PIPELINE_VERSION=2.0.5
   kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
   kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
   kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/platform-agnostic-pns?ref=$PIPELINE_VERSION"

   # Wait for pods
   kubectl get pods -n kubeflow --watch
   ```

2. **Access the UI**:
   ```bash
   kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
   # Open http://localhost:8080
   ```

3. **Create a simple pipeline** (save as `simple_pipeline.py`):
   ```python
   from kfp import dsl, compiler

   @dsl.component(base_image="python:3.10")
   def say_hello(name: str) -> str:
       message = f"Hello, {name}!"
       print(message)
       return message

   @dsl.component(base_image="python:3.10")
   def process_message(message: str) -> str:
       result = message.upper()
       print(result)
       return result

   @dsl.pipeline(name="hello-pipeline")
   def hello_pipeline(name: str = "Kubeflow"):
       hello_task = say_hello(name=name)
       process_message(message=hello_task.output)

   if __name__ == "__main__":
       compiler.Compiler().compile(hello_pipeline, "hello_pipeline.yaml")
   ```

4. **Compile and upload**:
   ```bash
   pip install kfp==2.0.0
   python simple_pipeline.py
   # Upload hello_pipeline.yaml via UI
   ```

5. **Run the pipeline**:
   - Click "Create run"
   - Enter a name like "World"
   - Watch the pipeline execute

6. **Clean up**:
   ```bash
   kind delete cluster --name kubeflow-lab
   ```

### Success Criteria
- [ ] Kubeflow Pipelines installed
- [ ] UI accessible at localhost:8080
- [ ] Pipeline compiled to YAML
- [ ] Pipeline run completed successfully
- [ ] Can view logs for each step

### Bonus Challenge
Add a third component that takes the processed message and writes it to a file artifact.

---

## Further Reading

- [Kubeflow Documentation](https://www.kubeflow.org/docs/)
- [Kubeflow Pipelines SDK](https://kubeflow-pipelines.readthedocs.io/)
- [KServe Documentation](https://kserve.github.io/website/)
- [Katib User Guide](https://www.kubeflow.org/docs/components/katib/)

---

## Next Module

Continue to [Module 9.2: MLflow](module-9.2-mlflow/) to learn about experiment tracking and model registry.

---

*"Kubeflow isn't about making ML easy—it's about making ML reproducible. The difference between a notebook demo and production is infrastructure, and Kubeflow provides that infrastructure."*
