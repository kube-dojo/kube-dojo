---
title: "Advanced Kubernetes"
slug: ai-ml-engineering/mlops/module-10.5-advanced-kubernetes
sidebar:
  order: 1106
---
> **AI/ML Engineering Track** | Complexity: `[MEDIUM]` | Time: 6-8
> **Migrated from neural-dojo** — pending pipeline polish

## The Night Spotify's Recommendations Went Silent

**Stockholm, Sweden. December 2019. 2:37 AM.**

The alert was the kind that makes your stomach drop: "Recommendation Service: 0 predictions served in last 5 minutes." Not slow. Not degraded. Zero. Complete silence from the system that personalizes music for 380 million users.

Emma Björklund, the on-call engineer, pulled up the Kubernetes dashboard from her laptop while her coffee went cold. Everything looked green. Pods were running. Health checks were passing. CPU usage was normal. But somehow, no predictions were flowing.

The root cause took four hours to find: a routine Kubernetes upgrade had changed how GPU memory was allocated to containers. Their TensorFlow Serving pods were silently crashing during model loading—the 50GB recommendation models couldn't fit in the new memory configuration—but Kubernetes kept restarting them. Each pod would start, attempt to load the model, fail, and restart. An infinite loop of failure that looked healthy from the outside.

**Josh Wills**, then Head of Data Engineering at Spotify (famous for his Twitter bio "I turn coffee and data into products"), led the post-mortem the next week. His team's conclusion would reshape how Spotify approached ML infrastructure: *"We had great ML models and great Kubernetes skills, but we didn't have a great ML-on-Kubernetes platform. The gap between 'running a container' and 'running ML at scale' is a chasm, not a crack."*

The solution wasn't more Kubernetes expertise or better models. It was a dedicated ML platform layer—tools specifically designed for the unique challenges of running machine learning in production. Six months later, Spotify had migrated their recommendation infrastructure to Kubeflow. The same incident that took four hours to diagnose could now be detected in seconds and auto-remediated in minutes. The models weren't smarter—the platform was.

This module teaches you the tools that bridge that chasm: Kubeflow, KServe, Ray, and Triton. These aren't just abstractions over Kubernetes—they're the accumulated wisdom of Google, Netflix, Uber, Spotify, Bloomberg, and hundreds of other companies who learned the hard way that ML in production requires more than containers and deployments.

Think of it like this: Kubernetes is the operating system for your cluster. But you wouldn't write applications directly against syscalls—you'd use frameworks, libraries, and runtimes that handle the complexity for you. The tools in this module are those frameworks for ML. They handle the orchestration, serving, distributed computing, and optimization that would otherwise require thousands of lines of custom code.

---

## What You'll Be Able to Do

By the end of this module, you will:
- Master Kubeflow for end-to-end ML workflows that scale to thousands of experiments
- Implement KServe for serverless model serving with automatic scaling and canary deployments
- Deploy Ray clusters on Kubernetes for distributed training across hundreds of GPUs
- Use NVIDIA Triton Inference Server for high-performance, multi-model inference with 10x throughput improvements
- Understand the decision matrix for choosing between tools based on your specific requirements

---

##  The ML Platform Stack on Kubernetes

In Module 46, you learned Kubernetes fundamentals—Pods, Deployments, Services, and the resource model that makes container orchestration possible. But if you've tried to run actual ML workloads on Kubernetes, you've probably discovered an uncomfortable truth: the primitives don't fit.

Consider what a typical ML workflow needs:

**Pipeline orchestration**: Training a model isn't a single container—it's a sequence of steps. Load data. Validate data. Feature engineering. Train model. Evaluate model. Register model. Deploy model. Each step might require different resources (CPUs for data processing, GPUs for training, CPU again for deployment). Each step produces artifacts that downstream steps need. Some steps can run in parallel; others must wait. Kubernetes has Jobs, but nothing that understands ML workflows.

**Experiment tracking**: When you train 100 different model configurations, which hyperparameters produced your best model? What dataset version was it trained on? What was the exact code commit? Kubernetes doesn't care about experiments—it just runs containers.

**Model serving**: Getting predictions from models is fundamentally different from serving web applications. You need batching (processing multiple requests together is drastically more efficient on GPUs). You need versioning (serving model v1 and v2 simultaneously for A/B testing). You need scaling that understands inference latency, not just CPU utilization. Kubernetes Deployments aren't designed for this.

**Distributed computing**: Modern neural networks often require more memory than a single GPU provides. Training GPT-3 required hundreds of GPUs working together, synchronized perfectly. Kubernetes can schedule pods across nodes, but it knows nothing about gradient synchronization or model parallelism.

**AutoML and hyperparameter optimization**: Running thousands of experiments with different configurations, tracking which ones succeed, pruning unpromising ones early—this is a specialized orchestration problem that standard Kubernetes schedulers can't handle.

These concerns don't fit neatly into Kubernetes primitives. That's why the ML community built a platform layer that sits on top of Kubernetes and speaks the language of ML engineering.

**Did You Know?** The term "ML Platform" emerged around 2017-2018, as companies like Google, Uber, and Netflix all realized they were building similar internal systems. **D. Sculley**, the lead author of Google's famous "Hidden Technical Debt in Machine Learning Systems" paper, noted that by 2015, Google was spending more engineering effort on ML infrastructure than on model development. *"Models were maybe 5% of the code,"* he wrote. *"The other 95% was everything needed to actually run those models in production."* This realization—that ML infrastructure is harder than ML models—drove the creation of the tools we'll explore in this module.

The ML platform layer handles concerns specific to machine learning that Kubernetes alone can't address. It tracks artifacts like datasets, model checkpoints, and evaluation metrics. It coordinates distributed training across multiple machines. It manages model versioning and A/B testing. It optimizes GPU inference through techniques like batching and TensorRT compilation.

This creates a three-layer architecture: Infrastructure (VMs, GPUs, storage), Kubernetes (container orchestration), and ML Platform (Kubeflow, KServe, Ray, Triton). Each layer handles its own concerns, and each builds on the layer below.

---

## 1. Kubeflow: The End-to-End ML Platform

### The Vision: ML as a Software Engineering Discipline

Imagine two companies, both building fraud detection systems. Company A has a brilliant data scientist named Marcus who builds his models in Jupyter notebooks on his laptop. When a model works, he emails the notebook to the operations team, who somehow get it running on a production server. There's no version control for the model. No one knows which dataset was used. When the model needs updating, Marcus tries to remember which notebook it came from.

Company B uses Kubeflow. Their data scientist, also named Marcus, develops models in a Kubeflow notebook that's automatically versioned and connected to their artifact store. When a model is ready, he adds it to a pipeline that runs automatically whenever new training data arrives. The pipeline tracks every input and output. The model is deployed with a single click, with automatic rollback if quality degrades. When the model needs updating, the entire history is available: exact data, exact code, exact hyperparameters.

Which company do you want to be when fraud losses hit $10 million?

Before Kubeflow, ML teams typically lived in Company A's world. Jupyter notebooks sat on laptops, unversioned and unreproducible. Training scripts ran on whatever machine had a free GPU. Deployment was "SSH into a server and hope nothing breaks." There was no systematic way to answer basic questions: "Which dataset trained this model? What hyperparameters were used? What version of the feature engineering code?"

Kubeflow's vision is to make ML development as rigorous as software engineering, with version control, CI/CD, and reproducible builds—but adapted for ML's unique needs. Just as software engineering evolved from "writing code" to "engineering software systems," ML engineering is evolving from "training models" to "building ML systems."

**Did You Know?** Kubeflow was born in 2017 from an unexpected source: Google's frustration with their own internal ML platform. Google had built TFX (TensorFlow Extended), a powerful system for running ML pipelines. But TFX was so tightly coupled to Google's internal infrastructure that it was nearly impossible for external companies to use. **Jeremy Lewi**, a Google engineer, was tasked with making TFX portable. After months of effort, he realized the coupling was too deep—a new approach was needed. He and his team started fresh, building something designed from the ground up to be portable across any Kubernetes cluster. *"We realized 80% of what ML engineers were doing was infrastructure work, not ML work,"* Jeremy later explained. *"Kubeflow was our attempt to flip that ratio."* By 2023, Kubeflow had over 10,000 GitHub stars and was deployed by Spotify, Bloomberg, and Uber. It had become the de facto standard for open-source ML platforms.

### Kubeflow's Architecture: A Complete ML Platform

Kubeflow isn't a single tool—it's a collection of components that work together to cover the entire ML lifecycle. Understanding these components helps you know which parts you need:

**Kubeflow Pipelines** is the orchestration engine. It lets you define multi-step ML workflows as Python code, where each step is a container. Pipelines handles scheduling, artifact passing between steps, failure recovery, and caching. When you hear "Kubeflow," people often mean Kubeflow Pipelines specifically.

**Kubeflow Notebooks** provides managed Jupyter notebooks running in Kubernetes. Unlike running Jupyter on your laptop, these notebooks have access to cluster resources—GPU nodes, distributed storage, and production data. They're also tied into the Kubeflow ecosystem, making it easy to turn experimental code into production pipelines.

**Katib** is Kubeflow's AutoML component, specializing in hyperparameter optimization. Instead of manually trying different learning rates and batch sizes, you define a search space and objective, and Katib runs experiments automatically, using algorithms like Bayesian optimization to find good configurations faster.

**Training Operators** handle distributed training for major frameworks. TensorFlow Training Operator, PyTorch Training Operator, and others understand how to set up distributed training jobs—creating the right number of workers, configuring communication, and handling failures.

**KServe** (formerly KFServing) provides serverless model serving. It's powerful enough that it's often used independently of the rest of Kubeflow. We'll cover it in detail in its own section.

**Central Dashboard** is the UI that ties everything together, letting you monitor pipelines, manage notebooks, and track experiments from a single interface.

Think of Kubeflow like a kitchen in a professional restaurant. Kubeflow Pipelines is the head chef, orchestrating the entire meal preparation. Notebooks are where the sous chefs experiment with new dishes. Katib is like having a panel of food critics giving feedback on different flavor combinations. Training Operators are the specialized equipment—the commercial ovens and blast chillers that handle tasks beyond normal kitchen tools. KServe is the waitstaff, delivering the finished dishes to customers. And the Dashboard is the window into the kitchen where you can see everything happening at once.

### Kubeflow Pipelines: Workflows as Code

The heart of Kubeflow is its pipeline system. A pipeline is a directed acyclic graph (DAG) where each node is a containerized step, and edges represent data dependencies between steps.

**Did You Know?** Kubeflow Pipelines was inspired by Apache Airflow, the workflow orchestration tool used by companies like Airbnb and Netflix. But there's a crucial difference. **Ajay Gopinathan**, a Kubeflow contributor at Google, explained the design decision: *"Airflow is great for data pipelines—moving data from A to B, running SQL queries, triggering services. But ML needs first-class artifact tracking. You can't reproduce an experiment if you don't know which exact dataset and which exact model checkpoint were used."* This insight led to Kubeflow's artifact-centric design. Every step in a Kubeflow pipeline explicitly declares its inputs (artifacts it needs) and outputs (artifacts it produces). The system tracks all of them, creating a complete lineage graph of how any artifact was created.

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

**Did You Know?** KServe was originally called KFServing (Kubeflow Serving), reflecting its origins as part of the Kubeflow project. It was renamed in 2021 to reflect its independence. **Dan Sun**, KServe's lead maintainer from Bloomberg, explained the change: *"We realized KFServing had outgrown Kubeflow. Companies were adopting it without the rest of Kubeflow. The rename acknowledged that reality."* Bloomberg now serves thousands of models through KServe, from small scikit-learn classifiers to large transformer models. The renaming also reflected a broader truth about the ML ecosystem: while the tools can work together, they're also valuable independently.

### How KServe Works: The InferenceService

KServe introduces a custom Kubernetes resource called InferenceService. Instead of writing Deployments, Services, and autoscalers, you declare what model you want to serve and how, and KServe handles the rest:

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

**Model storage integration**: The `storageUri` field supports S3, Google Cloud Storage, Azure Blob Storage, and PVCs. KServe automatically downloads the model from storage when the pod starts. You never have to worry about model shipping—just push to your model registry and update the URI.

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

When a request arrives, it flows through transformer → predictor → transformer (for postprocessing) → explainer (if explanation is requested). KServe handles the routing automatically.

### Canary Deployments: Safe Model Rollouts

Deploying a new model version is risky. The model that performed beautifully on your test set might behave completely differently in production with real data. Canary deployments mitigate this risk by sending a small percentage of traffic to the new version while the old version handles the rest.

Think of it like testing a new recipe at a restaurant. Instead of changing the entire menu immediately, you offer the new dish as a special to a few tables and watch how they react. If customers love it, you add it to the regular menu. If they don't, you tweak the recipe without having ruined dinner for everyone.

KServe makes canary deployments trivial:

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

With this configuration, 10% of traffic goes to v4 (the canary) and 90% stays on the previous version. You monitor metrics like latency, error rate, and business KPIs for both versions. If v4 performs better, you gradually increase traffic: 10% → 25% → 50% → 100%. If v4 has problems, you set `canaryTrafficPercent: 0` and roll back instantly.

The beauty of this approach is that your blast radius is limited. If the new model is catastrophically broken, only 10% of users are affected. Compare this to a traditional deployment where 100% of users suddenly hit a broken model.

---

## 3. Ray on Kubernetes: Distributed Computing Made Easy

### Why Ray Exists

At some point, your ML ambitions will outgrow a single machine. Maybe your model is so large it doesn't fit on one GPU. Maybe training takes weeks and you want to parallelize. Maybe you're doing hyperparameter search with thousands of configurations. Whatever the reason, you need distributed computing.

Traditional distributed computing frameworks like Apache Spark are designed for data processing—map-reduce style operations over huge datasets. They're great for ETL but terrible for ML. Training a neural network isn't MapReduce. It's many processes running the same code on different data, periodically synchronizing gradients. It's tight coupling, not embarrassingly parallel.

Ray is designed specifically for the communication patterns that ML needs. It provides primitives for remote functions, actors (stateful objects), and data objects that can be shared across processes. Building on these primitives, it offers Ray Train for distributed training, Ray Tune for hyperparameter search, and Ray Serve for serving.

**Did You Know?** Ray was created at UC Berkeley's RISELab by **Robert Nishihara** and **Philipp Moritz**, who were PhD students at the time. The name "Ray" refers to rays of light spreading out from a source—symbolizing how tasks fan out across a cluster. Their key insight was that ML workloads have different needs than traditional data processing: *"Existing systems like Spark were great for data processing, but terrible for ML. Training a neural network isn't MapReduce—it needs tight communication between workers. Spark's shuffle-based model added too much latency."* Ray's architecture—with its shared-memory object store and low-latency task scheduling—was designed from scratch for ML communication patterns. OpenAI uses Ray to coordinate training across thousands of GPUs, and it's used by companies like Uber, Amazon, and LinkedIn.

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

The cluster starts with 4 GPU workers but can autoscale up to 16 based on demand. When you submit a job that requires more workers than are available, the autoscaler spins up additional workers. When jobs finish and workers become idle, it scales back down to save costs.

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

The ASHA scheduler is particularly powerful. It runs many configurations with a small budget initially (few epochs), evaluates which ones look promising, and kills the rest. It then gives more budget to the survivors and repeats. This approach can find good configurations 10-100x faster than running all configurations to completion.

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

**Did You Know?** **Deepu Talla**, VP of Autonomous Vehicles at NVIDIA, revealed that NVIDIA's early self-driving car prototypes spent only 10% of GPU time on actual inference—the rest was waiting for data. This insight was embarrassing but illuminating: *"We had these incredibly powerful GPUs sitting mostly idle. The bottleneck wasn't compute—it was how we fed data to the compute."* That insight led to Triton's dynamic batching feature. Instead of processing requests immediately, Triton waits a configurable amount of time (microseconds to milliseconds) to collect a batch, then processes them together. With dynamic batching, Triton can achieve 10x higher throughput than naive serving. For high-traffic production systems, this is the difference between needing 10 GPUs and needing 100.

### How Triton Works

Triton Inference Server is NVIDIA's production inference platform. It's designed from the ground up for efficiency, with features like:

**Dynamic batching**: Triton automatically batches requests that arrive close together. You configure preferred batch sizes (e.g., 8, 16, 32) and a maximum wait time. Triton collects requests until it hits a preferred batch size or the timeout expires, then processes the batch.

**Concurrent model execution**: You can run multiple instances of a model on the same GPU, or spread instances across multiple GPUs. Triton handles request routing to maximize throughput.

**Multi-framework support**: Triton supports TensorFlow, PyTorch, ONNX, TensorRT, and custom backends. You can serve different models using different frameworks from the same server.

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

Choosing between these tools isn't always obvious. Here's a framework for thinking about it:

**Start with vanilla Kubernetes** if you have fewer than 3 models, simple serving requirements, and a team already comfortable with Kubernetes. Sometimes the overhead of ML-specific tooling isn't worth it.

**Add KServe** when you need intelligent autoscaling, canary deployments, or scale-to-zero. KServe's value is in its serverless semantics—you think about models, not pods.

**Add Triton** when throughput matters. If you're processing more than 1000 requests per second per model, Triton's dynamic batching can dramatically reduce the hardware you need. It's the difference between needing 10 GPUs and needing 100.

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

# Wait for ready and test
kubectl wait --for=condition=Ready inferenceservice/sklearn-iris --timeout=120s
```

### Exercise 2: Create a Kubeflow Pipeline

Build a simple two-step pipeline that adds numbers and multiplies the result. Compile it and view the DAG.

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
```

### Exercise 3: Deploy a Ray Cluster

Install the Ray operator and deploy a cluster. Submit a simple task to verify it's working.

```bash
# Install Ray operator
helm repo add kuberay https://ray-project.github.io/kuberay-helm/
helm install kuberay-operator kuberay/kuberay-operator

# Deploy cluster and submit job
kubectl apply -f ray-cluster.yaml
ray job submit --address http://ray-head:8265 -- python -c "import ray; ray.init(); print(ray.cluster_resources())"
```

---

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

**The 80/20 Rule of MLOps**: Multiple studies have confirmed what **Jeremy Lewi** observed at Google: roughly 80% of ML engineering effort goes into infrastructure, not models. Kubeflow's goal is to flip this ratio by making infrastructure disappear into declarative configuration.

**Kubernetes Was Never Designed for ML**: When Google donated Kubernetes to open source in 2014, GPUs weren't even in the picture. GPU support was added later, and ML-specific concerns like artifact tracking, distributed training, and model serving had to be built as extensions. The tools in this module are those extensions.

**The $440 Million Lesson**: Knight Capital's 2012 trading disaster (where a software deployment error caused $440 million in losses in 45 minutes) is studied in ML platform engineering. The parallel is clear: deploying a broken model to production can be just as catastrophic as deploying broken trading code. Canary deployments and gradual rollouts aren't just nice-to-haves—they're risk management.

---

## ⏭️ Next Steps

You now understand the advanced Kubernetes tools for ML at scale! These platforms are what transform experimental notebooks into production systems serving millions of users.

**Up Next**: Module 48 - MLOps & Experiment Tracking (MLflow, Weights & Biases, managing the experiment-to-production lifecycle)

---

*Module 47 Complete! You now understand Kubeflow, KServe, Ray, and Triton—the tools that power ML at scale at companies like Spotify, Bloomberg, and Netflix.*

*Remember Spotify's silent recommendations: the gap between "running a container" and "running ML at scale" is a platform, not just more containers. The platform is what makes the difference between 4 hours to diagnose an incident and 4 seconds.*

*"The best ML model is worthless if it can't serve predictions reliably at scale. The ML platform layer is what makes reliability possible."* — Lessons from the ML trenches
