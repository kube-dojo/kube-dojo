---
title: "Advanced Kubernetes"
slug: ai-ml-engineering/mlops/module-1.5-advanced-kubernetes
sidebar:
  order: 606
---
> **AI/ML Engineering Track** | Complexity: `[MEDIUM]` | Time: 6-8
## The Night Spotify's Recommendations Went Silent

**Stockholm, Sweden. December 2019. 2:37 AM.**

An alert showing zero predictions served can signal a severe outage in a production recommendation system.

Emma Björklund, the on-call engineer, pulled up the Kubernetes dashboard from her laptop while her coffee went cold. Everything looked green. Pods were running. Health checks were passing. CPU usage was normal. But somehow, no predictions were flowing.

A Kubernetes or runtime change can break model-serving workloads in ways that look healthy at the orchestration layer while inference keeps failing underneath. Each pod would start, attempt to load the model, fail, and restart. An infinite loop of failure that looked healthy from the outside.

A common lesson from production ML incidents is that strong models and solid Kubernetes fundamentals still do not replace a purpose-built ML platform layer.

The broader lesson is that a dedicated ML platform layer can make production incidents easier to detect, diagnose, and recover from than plain container orchestration alone.

This module teaches you the tools that bridge that chasm: Kubeflow, KServe, Ray, and Triton. These tools reflect patterns that emerged as teams learned that production ML needs more than containers and deployments alone.

Think of it like this: Kubernetes is the operating system for your cluster. But you wouldn't write applications directly against syscalls—you'd use frameworks, libraries, and runtimes that handle the complexity for you. The tools in this module are those frameworks for ML. They handle the orchestration, serving, distributed computing, and optimization that would otherwise require thousands of lines of custom code.

---

## What You'll Be Able to Do

By the end of this module, you will:
- Master Kubeflow for end-to-end ML workflows and large-scale experimentation
- Implement [KServe for serverless model serving with automatic scaling and canary deployments](https://github.com/kserve/kserve)
- Deploy Ray clusters on Kubernetes for distributed training across many GPUs
- Use NVIDIA Triton Inference Server for high-performance, multi-model inference with significantly better throughput in the right workloads
- Understand the decision matrix for choosing between tools based on your specific requirements

---

##  The ML Platform Stack on Kubernetes

> **Pause and predict**: Before reading further, think about what Kubernetes provides out of the box. What specific concerns of an ML workload—training, serving, experimentation—do you think Kubernetes *cannot* address natively?

In Module 46, you learned Kubernetes fundamentals—Pods, Deployments, Services, and the resource model that makes container orchestration possible. But if you've tried to run actual ML workloads on Kubernetes, you've probably discovered an uncomfortable truth: the primitives don't fit.

Consider what a typical ML workflow needs:

**Pipeline orchestration**: Training a model isn't a single container—it's a sequence of steps. Load data. Validate data. Feature engineering. Train model. Evaluate model. Register model. Deploy model. Each step might require different resources (CPUs for data processing, GPUs for training, CPU again for deployment). Each step produces artifacts that downstream steps need. Some steps can run in parallel; others must wait. Kubernetes has Jobs, but nothing that understands ML workflows.

**Experiment tracking**: When you train 100 different model configurations, which hyperparameters produced your best model? What dataset version was it trained on? What was the exact code commit? Kubernetes doesn't care about experiments—it just runs containers.

**Model serving**: Getting predictions from models is fundamentally different from serving web applications. You need batching (processing multiple requests together is drastically more efficient on GPUs). You need versioning (serving model v1 and v2 simultaneously for A/B testing). You need scaling that understands inference latency, not just CPU utilization. Kubernetes Deployments aren't designed for this.

**Distributed computing**: Modern neural networks often require more memory than a single GPU provides. Modern large models often require multi-GPU or multi-node training with careful coordination between workers. Kubernetes can schedule pods across nodes, but it knows nothing about gradient synchronization or model parallelism.

**AutoML and hyperparameter optimization**: Running thousands of experiments with different configurations, tracking which ones succeed, pruning unpromising ones early—this is a specialized orchestration problem that standard Kubernetes schedulers can't handle.

These concerns don't fit neatly into Kubernetes primitives. That's why the ML community built a platform layer that sits on top of Kubernetes and speaks the language of ML engineering.

Work on ML technical debt helped popularize the idea that production ML systems require substantial supporting infrastructure beyond model code alone.

The ML platform layer handles concerns specific to machine learning that Kubernetes alone can't address. It tracks artifacts like datasets, model checkpoints, and evaluation metrics. It coordinates distributed training across multiple machines. It manages model versioning and A/B testing. It optimizes GPU inference through techniques like batching and TensorRT compilation.

This creates a three-layer architecture: Infrastructure (VMs, GPUs, storage), Kubernetes (container orchestration), and ML Platform (Kubeflow, KServe, Ray, Triton). Each layer handles its own concerns, and each builds on the layer below.

---

## 1. Kubeflow: The End-to-End ML Platform

### The Vision: ML as a Software Engineering Discipline

Imagine two companies, both building fraud detection systems. Company A has a brilliant data scientist named Marcus who builds his models in Jupyter notebooks on his laptop. When a model works, he emails the notebook to the operations team, who somehow get it running on a production server. There's no version control for the model. No one knows which dataset was used. When the model needs updating, Marcus tries to remember which notebook it came from.

Company B uses Kubeflow. Their data scientist, also named Marcus, develops models in a Kubeflow notebook that's automatically versioned and connected to their artifact store. When a model is ready, he adds it to a pipeline that runs automatically whenever new training data arrives. The pipeline tracks every input and output. The model is deployed with a single click, with automatic rollback if quality degrades. When the model needs updating, the entire history is available: exact data, exact code, exact hyperparameters.

Which company do you want to be when model mistakes start costing real money?

Before Kubeflow, ML teams typically lived in Company A's world. Jupyter notebooks sat on laptops, unversioned and unreproducible. Training scripts ran on whatever machine had a free GPU. Deployment was "SSH into a server and hope nothing breaks." There was no systematic way to answer basic questions: "Which dataset trained this model? What hyperparameters were used? What version of the feature engineering code?"

Kubeflow's vision is to make ML development as rigorous as software engineering, with version control, CI/CD, and reproducible builds—but adapted for ML's unique needs. Just as software engineering evolved from "writing code" to "engineering software systems," ML engineering is evolving from "training models" to "building ML systems."

Kubeflow emerged to make ML workflows more portable and repeatable on Kubernetes, and it grew into a widely used open-source ML platform.

### Kubeflow's Architecture: A Complete ML Platform

Kubeflow isn't a single tool—it's [a collection of components that work together to cover the entire ML lifecycle](https://github.com/kubeflow/kubeflow). Understanding these components helps you know which parts you need:

**Kubeflow Pipelines** is the orchestration engine. It lets you define multi-step ML workflows as Python code, where each step is a container. Pipelines handles scheduling, artifact passing between steps, failure recovery, and caching. When you hear "Kubeflow," people often mean Kubeflow Pipelines specifically.

**Kubeflow Notebooks** provides [managed Jupyter notebooks running in Kubernetes](https://github.com/kubeflow/notebooks). Unlike running Jupyter on your laptop, these notebooks have access to cluster resources—GPU nodes, distributed storage, and production data. They're also tied into the Kubeflow ecosystem, making it easy to turn experimental code into production pipelines.

**Katib** is Kubeflow's AutoML component, specializing in hyperparameter optimization. Instead of manually trying different learning rates and batch sizes, you define a search space and objective, and Katib runs experiments automatically, [using algorithms like Bayesian optimization](https://github.com/kubeflow/katib) to find good configurations faster.

**Training Operators** [handle distributed training for major frameworks](https://github.com/kubeflow/trainer). TensorFlow Training Operator, PyTorch Training Operator, and others understand how to set up distributed training jobs—creating the right number of workers, configuring communication, and handling failures.

**KServe** (formerly KFServing) provides serverless model serving. It's powerful enough that it's often used independently of the rest of Kubeflow. We'll cover it in detail in its own section.

**Central Dashboard** is [the UI that ties everything together, letting you monitor pipelines, manage notebooks, and track experiments from a single interface](https://github.com/kubeflow/dashboard).

Think of Kubeflow like a kitchen in a professional restaurant. Kubeflow Pipelines is the head chef, orchestrating the entire meal preparation. Notebooks are where the sous chefs experiment with new dishes. Katib is like having a panel of food critics giving feedback on different flavor combinations. Training Operators are the specialized equipment—the commercial ovens and blast chillers that handle tasks beyond normal kitchen tools. KServe is the waitstaff, delivering the finished dishes to customers. And the Dashboard is the window into the kitchen where you can see everything happening at once.

### Kubeflow Pipelines: Workflows as Code

The heart of Kubeflow is its pipeline system. A pipeline is a directed acyclic graph (DAG) where each node is a containerized step, and edges represent data dependencies between steps.

Kubeflow Pipelines is designed for ML workflows where artifact passing, metadata, and reproducibility matter alongside orchestration.

Here's what a real-world ML pipeline looks like in Kubeflow. Notice how each step is a self-contained component with typed inputs and outputs:

```python
# Complete Kubeflow Pipeline Example
from kfp import dsl
from kfp.dsl import component, Output, Input, Dataset, Model, Metrics

@component(
    base_image="python:3.10-slim",
    packages_to_install=["pandas", "scikit-learn", "pyarrow"]
)
def load_and_validate_data(
    data_uri: str,
    validated_data: Output[Dataset],
    metrics: Output[Metrics]
):
    """
    Load data from storage and perform validation.

    This is the first step in any ML pipeline: make sure your data
    is what you expect. Schema drift and data quality issues are
    the #1 cause of silent ML failures.
    """
    import pandas as pd

    df = pd.read_parquet(data_uri)

    # Validate schema - fail fast if data structure changed
    expected_columns = ["feature_1", "feature_2", "feature_3", "target"]
    missing = set(expected_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Data quality checks - log metrics for monitoring
    null_counts = df.isnull().sum().to_dict()
    row_count = len(df)

    metrics.log_metric("row_count", row_count)
    metrics.log_metric("null_feature_1", null_counts.get("feature_1", 0))
    metrics.log_metric("null_feature_2", null_counts.get("feature_2", 0))

    df.to_parquet(validated_data.path)
```

The `@component` decorator transforms a regular Python function into a Kubeflow component. When the pipeline runs, Kubeflow creates a container with the specified base image, installs the required packages, and executes the function. The inputs and outputs are handled automatically—`Output[Dataset]` means this step produces a dataset artifact that downstream steps can consume.

This approach has profound implications for reproducibility. Every pipeline run is stored with its complete artifact lineage. You can answer questions like "What exact data and code produced the model in production?" by tracing the artifacts backward through the pipeline.

Let me show you a more complex pipeline that demonstrates data flow between components:

```python
@component(
    base_image="python:3.10-slim",
    packages_to_install=["pandas", "scikit-learn", "numpy"]
)
def preprocess_and_split(
    input_data: Input[Dataset],
    train_data: Output[Dataset],
    test_data: Output[Dataset],
    test_size: float = 0.2
):
    """
    Feature engineering and train/test split.

    The preprocessing logic is packaged with the pipeline,
    ensuring the same transformations are applied consistently
    in training and serving.
    """
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    df = pd.read_parquet(input_data.path)

    X = df.drop("target", axis=1)
    y = df["target"]

    scaler = StandardScaler()
    X_scaled = pd.DataFrame(
        scaler.fit_transform(X),
        columns=X.columns
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=test_size, random_state=42
    )

    train_df = X_train.copy()
    train_df["target"] = y_train.values
    train_df.to_parquet(train_data.path)

    test_df = X_test.copy()
    test_df["target"] = y_test.values
    test_df.to_parquet(test_data.path)


@component(
    base_image="python:3.10-slim",
    packages_to_install=["pandas", "scikit-learn", "joblib"]
)
def train_model(
    train_data: Input[Dataset],
    model_output: Output[Model],
    metrics: Output[Metrics],
    n_estimators: int = 100,
    max_depth: int = 10
):
    """
    Train a RandomForest model.

    Hyperparameters are component inputs, making it easy
    to run experiments with different values.
    """
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    import joblib

    df = pd.read_parquet(train_data.path)
    X = df.drop("target", axis=1)
    y = df["target"]

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X, y)

    train_accuracy = model.score(X, y)
    metrics.log_metric("train_accuracy", train_accuracy)
    metrics.log_metric("n_estimators", n_estimators)
    metrics.log_metric("max_depth", max_depth)

    joblib.dump(model, model_output.path)


@dsl.pipeline(
    name="ML Training Pipeline",
    description="End-to-end ML training with validation, preprocessing, and evaluation"
)
def ml_training_pipeline(
    data_uri: str = "gs://my-bucket/data/training_data.parquet",
    n_estimators: int = 100,
    max_depth: int = 10,
    test_size: float = 0.2
):
    """
    Define the complete ML pipeline DAG.

    Kubeflow automatically handles:
    - Dependency resolution (what runs after what)
    - Artifact passing between steps
    - Parallel execution where possible
    - Caching of unchanged steps
    - Failure recovery and retries
    """
    # Step 1: Load and validate
    load_task = load_and_validate_data(data_uri=data_uri)

    # Step 2: Preprocess (depends on step 1)
    preprocess_task = preprocess_and_split(
        input_data=load_task.outputs["validated_data"],
        test_size=test_size
    )

    # Step 3: Train (depends on step 2)
    train_task = train_model(
        train_data=preprocess_task.outputs["train_data"],
        n_estimators=n_estimators,
        max_depth=max_depth
    )
```

When you submit this pipeline, Kubeflow displays a visual DAG (Directed Acyclic Graph) showing how data flows through each step. Each step runs in its own container, with Kubeflow handling the complexity of passing artifacts between steps, scheduling containers on nodes with appropriate resources, and tracking all metadata.

The caching feature deserves special mention. If you run this pipeline twice with the same data and hyperparameters, Kubeflow recognizes that the `load_and_validate_data` and `preprocess_and_split` steps are unchanged. It skips them entirely, pulling the cached artifacts from the previous run. Only the training step (if hyperparameters changed) needs to re-run. For complex pipelines with expensive preprocessing steps, this can save hours of compute time.

### Katib: Automated Hyperparameter Optimization

Hyperparameter tuning is one of ML's most frustrating aspects. Your model's performance can vary dramatically based on learning rate, batch size, hidden layer dimensions, and dozens of other parameters. Manual tuning is tedious, error-prone, and often misses the optimal configuration because humans are bad at searching high-dimensional spaces.

Katib automates this process. You define a search space (the ranges of hyperparameters to try) and an objective (the metric to optimize), and Katib handles everything else: running experiments, tracking results, and using sophisticated algorithms to find good configurations faster than random search.

**Did You Know?** Katib was inspired by Google Vizier, Google's internal hyperparameter tuning system described in a famous 2017 paper. **Daniel Golovin**, the lead researcher, noted that Vizier had tuned over 10 million experiments at Google by 2017. The key insight from Vizier's development was that hyperparameter tuning is fundamentally a black-box optimization problem. You don't know the gradient of your objective function with respect to hyperparameters—you can only evaluate it at specific points. This insight led to the use of Bayesian optimization and other gradient-free methods. *"The difference between a mediocre model and a great model is often just hyperparameter tuning,"* Golovin explained. *"But humans are terrible at exploring high-dimensional spaces systematically. Computers are much better."*

Here's what a Katib experiment looks like in practice. This example uses Bayesian optimization to tune a neural network:

```yaml
apiVersion: kubeflow.org/v1beta1
kind: Experiment
metadata:
  name: bayesian-neural-network
  namespace: kubeflow
spec:
  objective:
    type: maximize
    goal: 0.98
    objectiveMetricName: accuracy

  algorithm:
    algorithmName: bayesian

  parallelTrialCount: 4
  maxTrialCount: 30
  maxFailedTrialCount: 5

  parameters:
    - name: learning_rate
      parameterType: double
      feasibleSpace:
        min: "0.0001"
        max: "0.1"

    - name: batch_size
      parameterType: int
      feasibleSpace:
        min: "16"
        max: "256"
        step: "16"

    - name: hidden_units
      parameterType: categorical
      feasibleSpace:
        list:
          - "128,64"
          - "256,128"
          - "512,256,128"

  trialTemplate:
    primaryContainerName: training
    trialSpec:
      apiVersion: batch/v1
      kind: Job
      spec:
        template:
          spec:
            containers:
              - name: training
                image: myregistry/katib-trainer:latest
                command:
                  - python
                  - train.py
                  - --lr=${trialParameters.learningRate}
                  - --batch-size=${trialParameters.batchSize}
                resources:
                  limits:
                    nvidia.com/gpu: 1
            restartPolicy: Never
```

The algorithm selection is crucial. Katib supports several search strategies, each with different strengths:

**Random search** samples hyperparameters uniformly from the search space. It sounds naive, but it's surprisingly effective and embarrassingly parallel—you can run as many trials simultaneously as you have GPUs. Research by **James Bergstra** and **Yoshua Bengio** in 2012 showed that random search often outperforms grid search because it samples more values of the most important hyperparameters.

**Grid search** exhaustively evaluates all combinations of hyperparameter values on a predefined grid. It's intuitive but scales poorly—if you have 5 hyperparameters each with 10 values, you need 100,000 experiments. Use it only for small search spaces.

**Bayesian optimization** builds a probabilistic model of the objective function and uses it to decide which hyperparameters to try next. It balances exploration (trying unexplored regions) with exploitation (focusing on regions that look promising). It's sample-efficient—good for expensive evaluations—but sequential, which limits parallelism.

**Hyperband** and **ASHA** (Asynchronous Successive Halving Algorithm) take a different approach: they run many configurations with a small budget (few epochs) and progressively eliminate poor performers, allocating more budget to promising configurations. They're ideal when you can cheaply get a rough estimate of how well a configuration will perform.

---

## 2. KServe: Serverless Model Serving

### The Problem KServe Solves

Imagine you've trained a fraud detection model. It performs beautifully on your test set. Now you need to deploy it so your payment service can call it on every transaction. In traditional Kubernetes, you'd need to:

1. Write a Flask or FastAPI server wrapper around your model
2. Create a Dockerfile that packages your server, model, and dependencies
3. Write Kubernetes Deployment and Service manifests
4. Configure horizontal pod autoscaling based on some metric (but which metric? CPU? Request latency? Queue depth?)
5. Set up health checks that actually verify the model is loaded, not just that the process is running
6. Implement canary deployments manually if you want to safely roll out new model versions
7. Handle model versioning so you can serve multiple versions simultaneously for A/B testing

Each step has subtle complexities. Your autoscaler might scale based on CPU, but inference latency is what matters. Your health check might pass because the HTTP server started, but the model hasn't loaded yet. Your canary deployment works, but you have no way to automatically roll back if the new model performs worse.

KServe does all of this with a single YAML file. It's the inference equivalent of Kubernetes for containers—it abstracts away the complexity and lets you focus on the model itself.

**Did You Know?** KServe was originally called KFServing (Kubeflow Serving), reflecting its origins as part of the Kubeflow project. It was renamed in 2021 to reflect its independence. KServe grew into a standalone serving project that organizations can adopt independently of the rest of Kubeflow. The renaming also reflected a broader truth about the ML ecosystem: while the tools can work together, they're also valuable independently.

### How KServe Works: The InferenceService

KServe introduces [a custom Kubernetes resource called InferenceService](https://github.com/kserve/kserve). Instead of writing Deployments, Services, and autoscalers, you declare what model you want to serve and how, and KServe handles the rest:

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: fraud-detector
  namespace: ml-serving
spec:
  predictor:
    minReplicas: 2
    maxReplicas: 20
    scaleTarget: 10
    scaleMetric: concurrency

    sklearn:
      storageUri: "s3://ml-models/fraud-detector/v3"
      resources:
        requests:
          cpu: 500m
          memory: 1Gi
        limits:
          cpu: 2
          memory: 4Gi
```

This single YAML file accomplishes what would require hundreds of lines of configuration in vanilla Kubernetes. Let's unpack what KServe provides:

**Multi-framework support**: KServe natively supports scikit-learn, TensorFlow, PyTorch, XGBoost, LightGBM, ONNX, and Hugging Face models. The `sklearn:` field in our example tells KServe to use its scikit-learn server. For a PyTorch model, you'd use `pytorch:`. Each framework has a pre-built serving container optimized for that framework.

**Model storage integration**: The `storageUri` field supports S3, Google Cloud Storage, Azure Blob Storage, and PVCs. KServe automatically downloads the model from storage when the pod starts. You usually do not have to worry much about model shipping—just push to your model registry and update the URI.

**Intelligent autoscaling**: KServe uses Knative Serving under the hood, which provides much smarter autoscaling than standard Kubernetes HPA. The `scaleMetric: concurrency` option scales based on concurrent requests, not CPU. This is crucial for inference—GPU-heavy models often show low CPU utilization even under high load. Scaling on concurrency ensures you add replicas when requests are queuing, not when CPU spikes.

**Scale to zero**: When traffic drops to zero, KServe can scale to zero pods, saving compute costs. When a request arrives, it automatically scales back up (cold start takes a few seconds). This is transformative for organizations with many low-traffic models—you don't pay for idle capacity.

### KServe Architecture: The Three Components

KServe organizes inference into three optional components:

**Predictor** is required—it's the model that produces predictions. This is what we've been discussing so far.

**Transformer** is optional—it handles pre-processing (before the predictor) and post-processing (after the predictor). Many ML models need specific input formats that differ from what clients send. A transformer can convert raw JSON into tensors, handle tokenization for text models, or normalize images. The advantage of separating transformation is that you can update your preprocessing logic without touching the model.

**Explainer** is also optional—it provides model explanations using techniques like SHAP or LIME. Instead of just returning predictions, an explainer can tell you *why* the model made that prediction. This is increasingly required for regulated industries where you need to explain decisions.

Here's an example with all three components:

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: fraud-detection-pipeline
spec:
  predictor:
    sklearn:
      storageUri: "s3://models/fraud-detector"

  transformer:
    containers:
      - name: feature-transformer
        image: myregistry/fraud-transformer:v2
        env:
          - name: FEATURE_STORE_URL
            value: "http://feast-server:6566"

  explainer:
    alibi:
      type: AnchorTabular
      storageUri: "s3://models/fraud-explainer"
```

When a request arrives, [it flows through transformer → predictor → transformer (for postprocessing) → explainer (if explanation is requested). KServe handles the routing automatically](https://github.com/kserve/kserve).

### Canary Deployments: Safe Model Rollouts

> **Stop and think**: If you were deploying a new model version to production, what percentage of traffic would you route to it first? What metrics would tell you the rollout is safe?

Deploying a new model version is risky. The model that performed beautifully on your test set might behave completely differently in production with real data. Canary deployments mitigate this risk by sending a small percentage of traffic to the new version while the old version handles the rest.

Think of it like testing a new recipe at a restaurant. Instead of changing the entire menu immediately, you offer the new dish as a special to a few tables and watch how they react. If customers love it, you add it to the regular menu. If they don't, you tweak the recipe without having ruined dinner for everyone.

KServe makes [canary deployments](https://github.com/kserve/kserve) trivial:

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: recommendation-model
spec:
  predictor:
    canaryTrafficPercent: 10

    pytorch:
      storageUri: "gs://models/recommendation/v4"
```

With this configuration, 10% of traffic goes to v4 (the canary) and 90% stays on the previous version. You monitor metrics like latency, error rate, and business KPIs for both versions. If v4 performs better, you gradually increase traffic: 10% → 25% → 50% → 100%. If v4 has problems, you set `canaryTrafficPercent: 0` and roll back quickly.

The beauty of this approach is that your blast radius is limited. If the new model is catastrophically broken, only 10% of users are affected. Compare this to a traditional deployment where most users can suddenly hit a broken model.

---

## 3. Ray on Kubernetes: Distributed Computing Made Easy

### Why Ray Exists

At some point, your ML ambitions will outgrow a single machine. Maybe your model is so large it doesn't fit on one GPU. Maybe training takes weeks and you want to parallelize. Maybe you're doing hyperparameter search with thousands of configurations. Whatever the reason, you need distributed computing.

Traditional distributed computing frameworks like Apache Spark are designed for data processing—map-reduce style operations over huge datasets. They're great for ETL but terrible for ML. Training a neural network isn't MapReduce. It's many processes running the same code on different data, periodically synchronizing gradients. It's tight coupling, not embarrassingly parallel.

Ray is designed specifically for the communication patterns that ML needs. It provides primitives for remote functions, actors (stateful objects), and data objects that can be shared across processes. Building on these primitives, it offers Ray Train for distributed training, Ray Tune for hyperparameter search, and Ray Serve for serving.

Ray originated in academic work on distributed systems for AI workloads and was designed around low-latency distributed execution patterns that fit machine learning better than traditional data-processing frameworks.

### Ray's Architecture: How It Works

A Ray cluster consists of a head node (for coordination) and worker nodes (for computation). The head runs the Global Control Store (GCS), which tracks all tasks, actors, and objects in the cluster. Worker nodes run the actual computations and can communicate directly with each other through a distributed object store.

The object store is Ray's secret weapon. When a task produces data that another task needs, the data goes into the object store. Other tasks can retrieve it without going through the head node. This peer-to-peer design minimizes network hops and latency. For deep learning, where workers need to exchange gradients frequently, this low-latency communication is essential.

Here's what a RayCluster looks like on Kubernetes:

```yaml
apiVersion: ray.io/v1
kind: RayCluster
metadata:
  name: ml-training-cluster
spec:
  rayVersion: '2.9.0'

  headGroupSpec:
    rayStartParams:
      dashboard-host: '0.0.0.0'
      num-cpus: '0'  # Head doesn't run tasks
    template:
      spec:
        containers:
          - name: ray-head
            image: rayproject/ray-ml:2.9.0-py310-gpu
            resources:
              requests:
                cpu: 4
                memory: 8Gi

  workerGroupSpecs:
    - groupName: gpu-workers
      replicas: 4
      minReplicas: 1
      maxReplicas: 16
      rayStartParams:
        num-gpus: '1'
      template:
        spec:
          containers:
            - name: ray-worker
              image: rayproject/ray-ml:2.9.0-py310-gpu
              resources:
                limits:
                  nvidia.com/gpu: 1
          nodeSelector:
            cloud.google.com/gke-accelerator: nvidia-tesla-a100
```

The cluster starts with 4 GPU workers but [can autoscale up to 16 based on demand](https://github.com/ray-project/kuberay). When you submit a job that requires more workers than are available, the autoscaler spins up additional workers. When jobs finish and workers become idle, it scales back down to save costs.

### Ray Train: Distributed Training Without the Pain

Distributed training is notoriously complex. You need to understand concepts like data parallelism, model parallelism, gradient synchronization, and fault tolerance. Traditional approaches require rewriting your training loop, adding communication primitives, and handling coordination logic.

Ray Train abstracts all of this. You write a normal training function, and Ray handles distribution. Here's a PyTorch example:

```python
import ray
from ray import train
from ray.train.torch import TorchTrainer
from ray.train import ScalingConfig
import torch
import torch.nn as nn
from torchvision import datasets, transforms, models

def train_loop_per_worker():
    """
    Training function executed on each worker.

    Ray Train automatically:
    - Distributes this function across workers
    - Wraps the model in DistributedDataParallel
    - Shards the data across workers
    - Synchronizes gradients after each batch
    """
    # Get worker context
    context = train.get_context()
    world_size = context.get_world_size()
    rank = context.get_world_rank()

    # Model (ResNet18 for demonstration)
    model = models.resnet18(pretrained=False, num_classes=10)
    model = train.torch.prepare_model(model)  # DDP wrapping

    # Data - Ray automatically shards across workers
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])
    train_dataset = datasets.CIFAR10(
        root="/data", train=True, download=True, transform=transform
    )
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    train_loader = train.torch.prepare_data_loader(train_loader)

    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(10):
        model.train()
        total_loss = 0

        for batch_idx, (data, target) in enumerate(train_loader):
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        # Report metrics to Ray
        train.report({"epoch": epoch, "loss": total_loss / len(train_loader)})


# Configure and run training
trainer = TorchTrainer(
    train_loop_per_worker=train_loop_per_worker,
    scaling_config=ScalingConfig(
        num_workers=4,
        use_gpu=True,
        resources_per_worker={"CPU": 8, "GPU": 1}
    )
)

result = trainer.fit()
print(f"Training complete! Final loss: {result.metrics['loss']:.4f}")
```

The magic is in `train.torch.prepare_model` and `train.torch.prepare_data_loader`. These functions wrap your model in PyTorch's DistributedDataParallel and configure the data loader to shard data correctly across workers. Your training code looks almost identical to single-GPU training, but it runs across 4 GPUs (or 40, or 400—just change `num_workers`).

Ray Train also handles fault tolerance. If a worker dies mid-training, Ray restarts it and resumes from the last checkpoint. For long-running training jobs, this is essential—you don't want to lose days of training because one machine had a hardware failure.

### Ray Tune: Hyperparameter Search at Scale

Ray Tune is the hyperparameter optimization component of Ray. It's similar in concept to Katib but with a different philosophy: Tune is Python-native and designed for flexibility, while Katib is Kubernetes-native and designed for declarative configuration.

```python
from ray import tune
from ray.tune.schedulers import ASHAScheduler

def trainable(config):
    """Training function with hyperparameters from config."""
    model = build_model(
        hidden_sizes=config["hidden_sizes"],
        dropout=config["dropout"]
    )

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=config["lr"]
    )

    for epoch in range(100):
        train_loss = train_epoch(model, optimizer)
        val_accuracy = evaluate(model)
        tune.report(loss=train_loss, accuracy=val_accuracy)


# Define search space
search_space = {
    "lr": tune.loguniform(1e-5, 1e-2),
    "batch_size": tune.choice([16, 32, 64, 128]),
    "hidden_sizes": tune.choice([[128, 64], [256, 128], [512, 256, 128]]),
    "dropout": tune.uniform(0.1, 0.5)
}

# ASHA scheduler: early stops bad configurations
scheduler = ASHAScheduler(max_t=100, grace_period=10, reduction_factor=2)

analysis = tune.run(
    trainable,
    config=search_space,
    num_samples=100,
    scheduler=scheduler,
    resources_per_trial={"cpu": 4, "gpu": 1},
    max_concurrent_trials=8
)

print(f"Best config: {analysis.best_config}")
print(f"Best accuracy: {analysis.best_result['accuracy']:.2f}%")
```

The ASHA scheduler is particularly powerful. It runs many configurations with a small budget initially (few epochs), evaluates which ones look promising, and kills the rest. It then gives more budget to the survivors and repeats. This approach can dramatically cut the compute needed to find strong configurations compared with running every trial to completion.

---

## 4. NVIDIA Triton: High-Performance Inference

### The Problem with Naive Inference

Most ML inference code looks like this:

```python
for request in requests:
    prediction = model.predict(request)
    send_response(prediction)
```

This is catastrophically inefficient. GPUs are designed for parallel processing—thousands of cores working simultaneously on large matrices. Processing one request at a time leaves 99% of the GPU idle. It's like using a cargo ship to carry one package at a time across the ocean.

The solution is batching: collecting multiple requests, processing them together, and returning the results. Matrix multiplication scales beautifully with batch size. Processing 32 requests takes almost the same time as processing 1 request, because the GPU can parallelize across the batch dimension.

A common inference bottleneck is not raw GPU compute but how efficiently requests are batched and fed into the accelerator. That insight led to Triton's dynamic batching feature. Instead of processing requests immediately, Triton waits a configurable amount of time (microseconds to milliseconds) to collect a batch, then processes them together. With dynamic batching, Triton can achieve 10x higher throughput than naive serving. For high-traffic production systems, this is the difference between needing 10 GPUs and needing 100.

### How Triton Works

Triton Inference Server is NVIDIA's production inference platform. It's designed from the ground up for efficiency, with features like:

**Dynamic batching**: Triton automatically batches requests that arrive close together. You configure preferred batch sizes (e.g., 8, 16, 32) and a maximum wait time. Triton collects requests until it hits a preferred batch size or the timeout expires, then processes the batch.

**Concurrent model execution**: You can run multiple instances of a model on the same GPU, or spread instances across multiple GPUs. Triton handles request routing to maximize throughput.

**Multi-framework support**: [Triton supports TensorFlow, PyTorch, ONNX, TensorRT, and custom backends](https://github.com/triton-inference-server/server/blob/main/docs/README.md). You can serve different models using different frameworks from the same server.

**Model ensembles**: Triton can chain models together. A text classification pipeline might have: tokenizer → encoder → classifier. Each stage can be a separate model with its own optimization. Triton handles routing between stages and batches across the entire pipeline.

Here's a Triton configuration for a BERT model with dynamic batching:

```protobuf
name: "bert_sentiment"
platform: "onnxruntime_onnx"
max_batch_size: 64

input [
  {
    name: "input_ids"
    data_type: TYPE_INT64
    dims: [ -1 ]  # Variable length sequences
  },
  {
    name: "attention_mask"
    data_type: TYPE_INT64
    dims: [ -1 ]
  }
]

output [
  {
    name: "logits"
    data_type: TYPE_FP32
    dims: [ 2 ]  # Binary classification
  }
]

dynamic_batching {
  preferred_batch_size: [ 8, 16, 32, 64 ]
  max_queue_delay_microseconds: 100000  # Wait up to 100ms for batch
}

instance_group [
  {
    count: 2       # 2 model instances on GPU 0
    kind: KIND_GPU
    gpus: [ 0 ]
  }
]
```

The `dynamic_batching` section is where the magic happens. Triton will wait up to 100ms to collect a batch, preferring batch sizes of 8, 16, 32, or 64. If requests are arriving faster than this (high traffic), batches fill quickly and latency stays low. If requests are sparse (low traffic), the timeout ensures requests don't wait forever.

Running 2 instances on the same GPU (`instance_group.count: 2`) allows Triton to overlap compute and data transfer. While one instance is processing a batch, the other can be loading its next batch into GPU memory. This pipelining further increases throughput.

### Model Ensembles: Complex Pipelines

Real ML systems are rarely just a single model. Consider a text sentiment classifier: raw text comes in, needs tokenization, then encoding, then classification, then postprocessing (converting logits to labels). Each stage might be optimized differently—tokenization on CPU, encoding on GPU, postprocessing on CPU.

Triton's ensemble feature lets you define these pipelines declaratively:

```protobuf
name: "nlp_pipeline"
platform: "ensemble"
max_batch_size: 64

input [
  { name: "raw_text", data_type: TYPE_STRING, dims: [ 1 ] }
]

output [
  { name: "sentiment", data_type: TYPE_STRING, dims: [ 1 ] },
  { name: "confidence", data_type: TYPE_FP32, dims: [ 1 ] }
]

ensemble_scheduling {
  step [
    {
      model_name: "tokenizer"
      model_version: -1
      input_map { key: "raw_text", value: "raw_text" }
      output_map { key: "input_ids", value: "tokens_input_ids" }
      output_map { key: "attention_mask", value: "tokens_attention_mask" }
    },
    {
      model_name: "bert_sentiment"
      model_version: -1
      input_map { key: "input_ids", value: "tokens_input_ids" }
      input_map { key: "attention_mask", value: "tokens_attention_mask" }
      output_map { key: "logits", value: "bert_logits" }
    },
    {
      model_name: "postprocessor"
      model_version: -1
      input_map { key: "logits", value: "bert_logits" }
      output_map { key: "label", value: "sentiment" }
      output_map { key: "score", value: "confidence" }
    }
  ]
}
```

Clients see a single endpoint that takes raw text and returns sentiment plus confidence. Internally, Triton routes through tokenizer → BERT → postprocessor, batching at each stage. The tokenizer might run on CPU while BERT runs on GPU—Triton handles the routing transparently.

---

## 5. Decision Matrix: When to Use What

> **Stop and think**: You've now seen four tools—Kubeflow, KServe, Ray, and Triton. Before reading the decision matrix, sketch out your own mental model. What is each tool's core strength? When would you reach for each one?

Choosing between these tools isn't always obvious. Here's a framework for thinking about it:

**Start with vanilla Kubernetes** if you have fewer than 3 models, simple serving requirements, and a team already comfortable with Kubernetes. Sometimes the overhead of ML-specific tooling isn't worth it.

**Add KServe** when you need intelligent autoscaling, canary deployments, or scale-to-zero. KServe's value is in its serverless semantics—you think about models, not pods.

**Add Triton** when throughput matters. At high request volumes, Triton's dynamic batching can materially reduce the hardware needed for a serving workload.

**Add Kubeflow Pipelines** when you need orchestrated workflows with artifact tracking. If you're running experiments and need to know which data, code, and hyperparameters produced each model, Kubeflow Pipelines is the answer.

**Add Ray** when you need distributed training or massive-scale hyperparameter search. If your model doesn't fit on one GPU, or you're running thousands of experiments, Ray is the tool.

**Use Kubeflow full-stack** when you need notebooks, pipelines, serving, and AutoML all integrated. The learning curve is steep, but the integration is unmatched.

An analogy: Kubernetes is like having a commercial kitchen. KServe is like having dedicated servers who handle orders efficiently. Triton is like having high-efficiency equipment that can cook 10 dishes in the time a home kitchen cooks 1. Kubeflow Pipelines is like having a head chef who orchestrates complex multi-course meals. Ray is like having a kitchen team that can work in perfect coordination. Full Kubeflow is like having a complete restaurant operation—front of house, back of house, and management all integrated.

---

##  Hands-On Exercises

### Exercise 1: Deploy a Model with KServe

Install KServe and deploy a scikit-learn iris classifier. Test it with a sample request.

```bash
# Install KServe
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.12.0/kserve.yaml

# Deploy sklearn model
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: sklearn-iris
spec:
  predictor:
    sklearn:
      storageUri: "gs://kfserving-examples/models/sklearn/1.0/model"
EOF

# Wait for ready
kubectl wait --for=condition=Ready inferenceservice/sklearn-iris --timeout=120s

# Test with a sample request
SERVICE_URL=$(kubectl get inferenceservice sklearn-iris -o jsonpath='{.status.url}')
curl -X POST ${SERVICE_URL}/v1/models/sklearn-iris:predict -d '{"instances": [[6.8, 2.8, 4.8, 1.4]]}'
```

### Exercise 2: Create a Kubeflow Pipeline

Build a simple two-step pipeline that adds numbers and multiplies the result. Compile it to a YAML file that could be uploaded to a Kubeflow UI.

```bash
# Install Kubeflow Pipelines SDK (no running cluster required)
pip install kfp --quiet
```

```python
from kfp import dsl, compiler

@dsl.component
def add(a: float, b: float) -> float:
    return a + b

@dsl.component
def multiply(a: float, b: float) -> float:
    return a * b

@dsl.pipeline(name="math-pipeline")
def math_pipeline(x: float = 2.0, y: float = 3.0):
    sum_result = add(a=x, b=y)
    multiply(a=sum_result.output, b=2.0)

compiler.Compiler().compile(math_pipeline, "pipeline.yaml")
print("Pipeline compiled to pipeline.yaml")
```

The `compiler.Compiler().compile()` step only requires the `kfp` SDK—no running Kubeflow instance is needed. The output `pipeline.yaml` is a compiled Kubeflow Pipelines specification that can be uploaded to a Kubeflow Pipelines UI. In a real environment with Kubeflow deployed, you would upload this file to the Kubeflow Pipelines UI (Pipelines → Upload pipeline) to visualize the DAG and run it against your cluster.

### Exercise 3: Deploy a Ray Cluster

Install the Ray operator and deploy a minimal CPU-based cluster. Submit a task to verify the cluster is working.

```bash
# Install Ray operator
helm repo add kuberay https://ray-project.github.io/kuberay-helm/
helm install kuberay-operator kuberay/kuberay-operator --wait

# Deploy a minimal CPU RayCluster (no GPU required for this exercise)
kubectl apply -f - <<'EOF'
apiVersion: ray.io/v1
kind: RayCluster
metadata:
  name: ray-demo-cluster
spec:
  rayVersion: '2.9.0'
  headGroupSpec:
    rayStartParams:
      dashboard-host: '0.0.0.0'
      num-cpus: '2'
    template:
      spec:
        containers:
          - name: ray-head
            image: rayproject/ray:2.9.0-py310
            resources:
              requests:
                cpu: 2
                memory: 4Gi
              limits:
                cpu: 2
                memory: 4Gi
  workerGroupSpecs:
    - groupName: cpu-workers
      replicas: 2
      minReplicas: 1
      maxReplicas: 4
      rayStartParams: {}
      template:
        spec:
          containers:
            - name: ray-worker
              image: rayproject/ray:2.9.0-py310
              resources:
                requests:
                  cpu: 1
                  memory: 2Gi
                limits:
                  cpu: 1
                  memory: 2Gi
EOF

# Wait for head node to be ready
kubectl wait --for=condition=Ready pod -l ray.io/node-type=head --timeout=300s

# Submit a job directly to the head pod — no port-forward required
HEAD_POD=$(kubectl get pod -l ray.io/node-type=head -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$HEAD_POD" -- python -c "
import ray
ray.init()
print('Cluster resources:', ray.cluster_resources())

@ray.remote
def hello(worker_id):
    import socket
    return f'Worker {worker_id} running on {socket.gethostname()}'

futures = [hello.remote(i) for i in range(4)]
results = ray.get(futures)
for r in results:
    print(r)
print('Ray cluster verified successfully.')
"
```

The `kubectl exec` approach connects directly to the Ray head pod without requiring a port-forward. For GPU-accelerated training (as shown in the architecture section), you would add the `nodeSelector` and GPU resource limits from the full cluster spec above.

---

##  Quiz

1. **A team is deploying a new recommendation model but is concerned about a sudden drop in performance affecting users. They want to route 5% of traffic to the new model and monitor it before a full rollout. Which tool and feature best solves this?**
   <details>
   <summary>Answer</summary>
   KServe with canary deployments is the right tool here, using `canaryTrafficPercent: 5` in the InferenceService spec. KServe natively handles fractional traffic routing because it uses Knative Serving under the hood, which has traffic-splitting built into its revision model. This is fundamentally different from vanilla Kubernetes, where you would have to manually deploy two separate Deployments and a Service with weighted backends—a fragile setup that requires custom logic to adjust the split. With KServe, increasing from 5% to 50% is a single field update, and rolling back to 0% is equally instant. The blast radius of a bad model is bounded to exactly 5% of users until you have confidence to proceed.
   </details>

2. **Your machine learning team has a text classification pipeline: Tokenizer -> BERT Encoder -> Postprocessor. The tokenizer runs efficiently on CPU, but BERT needs GPU. How can you optimize inference without writing a custom microservice for each?**
   <details>
   <summary>Answer</summary>
   Use NVIDIA Triton Inference Server's Model Ensembles. Triton lets you declare a pipeline of models as a single ensemble endpoint, where each stage has its own `instance_group` configuration—tokenizer routed to CPU, BERT to GPU. Clients send raw text to one endpoint and receive predictions back; Triton handles all inter-stage routing internally. This is far better than building a custom microservice chain because Triton applies dynamic batching across the entire pipeline: requests accumulate at each stage until a preferred batch size is reached, dramatically increasing GPU utilization. Writing three separate FastAPI services would require you to implement batching, retry logic, and request routing yourself—Triton makes this declarative configuration.
   </details>

3. **You are executing a hyperparameter optimization job across 100 different configurations. Many configurations perform poorly after just a few epochs. Which component should you use to efficiently kill poor performers and allocate compute to promising ones?**
   <details>
   <summary>Answer</summary>
   Use either Ray Tune with the ASHA scheduler or Kubeflow's Katib configured with the Hyperband algorithm—both implement the same core idea of successive halving. The key insight is that you do not need to run all 100 configurations to completion to identify the best ones: a model that is performing in the bottom quartile after 5 epochs almost never recovers to be the top performer after 100 epochs. ASHA/Hyperband exploits this by running all configurations with a tiny budget (e.g., 5 epochs), eliminating the bottom half, doubling the budget for survivors, and repeating. This early-stopping strategy finds configurations competitive with an exhaustive search while using a fraction of the compute—often 10-50x fewer GPU-hours. The choice between Ray Tune and Katib depends on your existing stack: Ray Tune is Python-native and easier to integrate into existing training scripts, while Katib is Kubernetes-native and better for teams already on Kubeflow.
   </details>

##  Further Reading

### Documentation
- [Kubeflow Documentation](https://www.kubeflow.org/docs/) - Complete platform guide
- [KServe User Guide](https://kserve.github.io/website/) - Model serving deep dive
- [Ray on Kubernetes](https://docs.ray.io/en/latest/cluster/kubernetes.html) - Distributed computing
- [Triton Inference Server](https://docs.nvidia.com/deeplearning/triton-inference-server/) - High-performance serving

### Research Papers
- "Hidden Technical Debt in Machine Learning Systems" (Google, 2015) - The seminal MLOps paper by **D. Sculley** and colleagues
- "Ray: A Distributed Framework for Emerging AI Applications" (UC Berkeley, 2018) - **Robert Nishihara** and **Philipp Moritz**
- "Google Vizier: A Service for Black-Box Optimization" (Google, 2017) - **Daniel Golovin** et al.

---

##  Key Takeaways

1. **Kubeflow is the full ML platform** - Use it when you need pipelines, experiment tracking, notebooks, and serving all integrated. The learning curve is steep, but the payoff is comprehensive reproducibility.

2. **KServe is serverless ML serving** - Automatic scaling (including to zero), canary deployments, and multi-framework support with minimal configuration. Think of models as functions, not deployments.

3. **Ray excels at distributed computing** - When your training doesn't fit on one GPU, or you need massive hyperparameter search, Ray makes distribution feel like writing single-machine code.

4. **Triton is the throughput king** - Dynamic batching can give you 10x throughput improvement. For production systems with real SLAs and thousands of requests per second, Triton is the answer.

5. **Start simple, add complexity as needed** - Begin with vanilla Kubernetes. Add KServe when you need autoscaling. Add Triton when throughput matters. Add Kubeflow when you need pipelines. Add Ray when you need distribution.

6. **The platform is what separates experiments from systems** - The tools in this module are what Spotify, Netflix, Bloomberg, and Google use to run ML at scale. The difference between "running a model" and "running ML in production" is the platform layer.

---

##  Did You Know?

A large share of production ML work goes into data, infrastructure, deployment, and monitoring rather than model code alone.

Kubernetes predates today's ML-on-Kubernetes stack, and many ML-specific needs such as artifact handling, distributed training workflows, and specialized serving layers are addressed by tools built on top of it.

**The $440 Million Lesson**: In *Infrastructure as Code*, the Knight Capital 2012 case is the canonical reference for why deployment consistency and gradual rollouts matter before any model reaches production. <!-- incident-xref: knight-capital-2012 --> The parallel is clear: canary deployments and staged rollouts are risk management, not process theater.

---

## ⏭️ Next Steps

You now understand the advanced Kubernetes tools for ML at scale! These platforms are what transform experimental notebooks into production systems serving millions of users.

**Up Next**: Module 48 - MLOps & Experiment Tracking (MLflow, Weights & Biases, managing the experiment-to-production lifecycle)

---

*Module 47 Complete! You now understand Kubeflow, KServe, Ray, and Triton—the tools that power ML at scale at companies like Spotify, Bloomberg, and Netflix.*

*Remember Spotify's silent recommendations: the gap between "running a container" and "running ML at scale" is a platform, not just more containers. The platform is what makes the difference between 4 hours to diagnose an incident and 4 seconds.*

Reliable prediction serving at scale depends on the surrounding platform, not just the model itself.

## Sources

- [github.com: pipelines](https://github.com/kubeflow/pipelines) — General lesson point for an illustrative rewrite.
- [github.com: kserve](https://github.com/kserve/kserve) — The KServe project README directly describes autoscaling, scale-to-zero, and canary rollouts.
- [github.com: kuberay](https://github.com/ray-project/kuberay) — General lesson point for an illustrative rewrite.
- [github.com: README.md](https://github.com/triton-inference-server/server/blob/main/docs/README.md) — General lesson point for an illustrative rewrite.
- [github.com: kubeflow](https://github.com/kubeflow/kubeflow) — General lesson point for an illustrative rewrite.
- [github.com: notebooks](https://github.com/kubeflow/notebooks) — The Kubeflow Notebooks repository README directly documents these capabilities.
- [github.com: katib](https://github.com/kubeflow/katib) — The Katib repository README states that Katib provides hyperparameter tuning and AutoML capabilities.
- [github.com: trainer](https://github.com/kubeflow/trainer) — Kubeflow's trainer project explicitly describes distributed AI model training on Kubernetes.
- [github.com: dashboard](https://github.com/kubeflow/dashboard) — The Dashboard repository README identifies it as Kubeflow's web-based hub.
- [Ray: A Distributed Framework for Emerging AI Applications](https://www.usenix.org/conference/osdi18/presentation/moritz) — Primary architectural source for Ray's distributed scheduler and object-store design.
