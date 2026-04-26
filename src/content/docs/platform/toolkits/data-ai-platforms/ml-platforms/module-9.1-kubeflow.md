---
title: "Module 9.1: Kubeflow"
slug: platform/toolkits/data-ai-platforms/ml-platforms/module-9.1-kubeflow
sidebar:
  order: 2
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 50-60 minutes

## Learning Outcomes

After completing this module, you will be able to:

- **Evaluate** whether a team should adopt full Kubeflow, Kubeflow Pipelines only, or a smaller composed MLOps stack based on team size, operational maturity, and workflow complexity.
- **Design** a Kubernetes-native ML workflow that connects notebooks, pipelines, artifact storage, model serving, and experiment tracking without losing reproducibility between stages.
- **Debug** common Kubeflow pipeline failures involving artifacts, container images, resource requests, namespaces, and service access.
- **Configure** core Kubeflow resources for notebooks, Kubeflow Pipelines, KServe, Katib, and distributed training using Kubernetes manifests and Python pipeline definitions.
- **Compare** Kubeflow platform trade-offs against simpler alternatives such as MLflow, Ray, Argo Workflows, and standalone notebook environments.

**Prerequisites**:

- Kubernetes fundamentals, including Pods, Deployments, Services, PersistentVolumeClaims, and namespaces.
- Basic ML concepts, including training, validation, inference, model artifacts, and hyperparameters.
- Python familiarity, especially virtual environments, package installation, and function-based APIs.
- [MLOps Discipline](/platform/disciplines/data-ai/mlops/) recommended before this module.

## Why This Module Matters

A data science team ships a fraud detection notebook that looks excellent during a stakeholder demo. The model was trained on a sample dataset, the metrics were copied into a slide deck, and the notebook contains several cells that must be executed in exactly the right order. Two weeks later, the platform team is asked to put the model into production, but nobody can reproduce the training run, the dataset location changed, the model file lives on one engineer's laptop, and the inference service needs GPU access during business peaks.

That failure is not a machine learning failure. It is an operations failure around reproducibility, packaging, workflow orchestration, identity, storage, scheduling, and serving. Machine learning work becomes production work only when experiments can be rerun, artifacts can be traced, training jobs can be scheduled, models can be served safely, and teams can work in isolated spaces without stepping on each other's compute or credentials.

Kubeflow exists for that gap. It does not make modeling easy, and it does not replace good data science practice. It gives Kubernetes teams a way to treat ML workloads as platform workloads: notebooks run in namespaces, pipelines run as containerized steps, artifacts move through object storage, tuning jobs run as Kubernetes jobs, and models are served through Kubernetes-native resources.

A senior platform engineer does not adopt Kubeflow because it is popular. They adopt it when the organization needs the lifecycle integration strongly enough to justify the operational weight. This module teaches both sides: how the pieces fit together when Kubeflow is the right choice, and how to recognize when a smaller system is the better engineering decision.

## Start With The Problem Kubeflow Solves

Kubeflow is easiest to understand if you begin with the path a model takes from idea to production. A data scientist explores data, turns that exploration into repeatable training code, records metrics, saves model artifacts, compares variants, and eventually serves one approved model behind an API. Each step has different infrastructure needs, but the same model lineage has to survive across the whole path.

In a small team, these steps often begin as informal habits. A notebook reads from a shared bucket, a model is uploaded by hand, and a cron job runs a training script. That can be enough while the team is learning. It starts to break when more people depend on the same workflow, when GPUs are scarce, when auditability matters, or when production incidents require a fast answer to the question, "Which code, data, parameters, and image produced this model?"

Kubeflow is a collection of Kubernetes-native ML projects that tries to make those lifecycle boundaries explicit. Notebooks cover interactive development. Kubeflow Pipelines covers repeatable workflow execution. Katib covers hyperparameter tuning. Training operators cover distributed training. KServe covers model serving. Profiles and namespaces help isolate teams. Artifact and metadata systems connect runs to their inputs and outputs.

```ascii
KUBEFLOW PLATFORM ARCHITECTURE
====================================================================

┌──────────────────────────────────────────────────────────────────┐
│                      KUBEFLOW DASHBOARD                          │
│        Shared entry point for notebooks, pipelines, and runs      │
└───────────────────────────────┬──────────────────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   Notebooks     │   │    Pipelines    │   │     KServe      │
│ Interactive dev │   │ Repeatable DAGs │   │ Model inference │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                     │
         │                     ▼                     │
         │            ┌─────────────────┐            │
         │            │      Katib      │            │
         │            │ HPO and trials  │            │
         │            └────────┬────────┘            │
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                         Kubernetes                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Namespaces   │  │ Object store │  │ CPU, memory, GPU     │   │
│  │ RBAC quotas  │  │ PVC, S3, GCS │  │ scheduling and nodes │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

The diagram hides an important operational point. Kubeflow is not one binary that you install and forget. It is a platform made of controllers, custom resources, web UIs, backing stores, service mesh integration in many distributions, and workload components that still need normal Kubernetes care. If your team cannot already run namespaces, storage, ingress, identity, and resource quotas reliably, Kubeflow will expose those weaknesses quickly.

**Pause and predict:** before reading the component table, imagine your team only needs scheduled retraining and model artifact tracking. Which parts of the diagram would you keep, and which would you avoid at first? Write down your answer, then compare it with the decision guidance in the next section.

| Component | Purpose | Production question it answers |
|-----------|---------|--------------------------------|
| **Notebooks** | Jupyter-based workspaces running inside Kubernetes namespaces | How do data scientists explore data near the same credentials, images, and storage used by production workflows? |
| **Kubeflow Pipelines** | Containerized ML workflow orchestration with artifacts and metadata | How do we turn a training process into a repeatable, inspectable run instead of a manual notebook ritual? |
| **KServe** | Kubernetes-native model serving through `InferenceService` resources | How do we expose a model behind an inference endpoint with rollout and scaling behavior? |
| **Katib** | Hyperparameter tuning and neural architecture search | How do we run many training trials without hand-managing jobs and spreadsheets? |
| **Training Operators** | CRDs for distributed TensorFlow, PyTorch, MPI, and related jobs | How do we coordinate multi-worker training on Kubernetes without writing custom controllers? |
| **Profiles and namespaces** | Multi-tenant isolation for users or teams | How do we keep one team's notebooks, runs, secrets, and quotas separate from another team's work? |

A useful mental model is that Kubeflow turns machine learning lifecycle actions into Kubernetes resources and containerized executions. That is powerful when platform teams already have Kubernetes governance, observability, and automation. It is painful when the organization wants "an ML tool" but is not ready to operate the platform underneath it.

## Choosing The Right Kubeflow Scope

The first design decision is not how to install Kubeflow. The first decision is how much Kubeflow you actually need. A full install can provide a unified experience for multiple teams, but it also brings more moving parts than a standalone pipeline service or an MLflow tracking server.

Start with the user journey. If data scientists already have a managed notebook environment and only need repeatable training DAGs, Kubeflow Pipelines may be enough. If the platform team needs namespace isolation, notebooks, pipelines, tuning, serving, and a common dashboard across teams, full Kubeflow becomes more reasonable. If the main pain is experiment tracking and model registry, MLflow might be a better first move.

| Situation | Better starting point | Why |
|-----------|----------------------|-----|
| One project needs repeatable containerized training | Kubeflow Pipelines only | The team gets DAGs, artifacts, and run history without operating the entire platform surface. |
| Several teams need shared notebooks, quotas, and a central ML workspace | Full Kubeflow | Multi-tenancy and integrated UI become more valuable than a minimal install. |
| The team mostly needs metrics, parameters, and model registry | MLflow | Experiment tracking is the center of gravity, not Kubernetes-native orchestration. |
| Workloads are distributed Python or large-scale batch compute | Ray or Spark with selected MLOps tools | Cluster compute may matter more than Kubeflow's full lifecycle integration. |
| Platform team already standardizes on Argo Workflows | Argo plus ML-specific metadata tooling | Existing workflow operations may outweigh Kubeflow's opinionated ML UX. |
| Regulated ML needs run lineage from data to serving | Full Kubeflow with strict storage and identity design | The integrated lifecycle can support traceability when configured deliberately. |

The wrong adoption pattern is to install everything because ML is important. Importance does not reduce complexity. A better pattern is to identify the smallest slice that removes the team's current bottleneck, then add components when the next bottleneck is real.

**Active check:** your organization has five data scientists, no GPU workloads, a managed notebook product, and one training pipeline that runs nightly. Would you propose full Kubeflow, Kubeflow Pipelines only, or another tool? Justify the answer in terms of operational surface area, not feature count.

The answer is usually Kubeflow Pipelines only or a smaller workflow stack. Full Kubeflow may become appropriate later, but starting with the whole platform would create dashboard, profile, service mesh, notebook, and serving operations before the team has a demonstrated need for them. A senior recommendation includes what not to run.

## Installation And Access Patterns

Kubeflow installation varies by distribution and version, so treat installation commands as a pattern rather than a universal production recipe. The upstream manifests repository assembles many components, and production environments often wrap those manifests with GitOps, identity integration, certificate management, ingress configuration, and environment-specific overlays. Local development should be smaller whenever possible.

For full Kubeflow, teams commonly use the manifests repository with Kustomize. A production installation needs prerequisites such as a compatible Kubernetes cluster, working storage classes, ingress or service mesh decisions, certificate handling, and enough node capacity for the control plane components plus user workloads. The install loop is often repeated because custom resource definitions and controllers may not be ready on the first apply.

```bash
git clone https://github.com/kubeflow/manifests.git
cd manifests

while ! kustomize build example | kubectl apply -f -; do
  echo "Retrying while custom resources and controllers become ready..."
  sleep 10
done

kubectl get pods -n kubeflow --watch
```

After the first successful apply, the useful question is not "are there pods?" but "which components are ready, which are crash-looping, and which dependencies are missing?" In the rest of this module, `kubectl` is shown once and then abbreviated as `k`, a common shell alias for the same command. If you use the alias locally, define it explicitly with `alias k=kubectl`.

```bash
kubectl get namespaces
kubectl get pods -n kubeflow
kubectl get events -n kubeflow --sort-by='.lastTimestamp'
```

```bash
alias k=kubectl

k get pods -n kubeflow
k get svc -n kubeflow
k get crd | grep -E 'kubeflow|kserve|katib|pipelines'
```

For learning and for many early platform experiments, installing only Kubeflow Pipelines is a better lab path. It narrows the debugging area to pipeline services, metadata, artifact storage behavior, and the UI. It also helps learners understand the central Kubeflow pattern before adding notebooks, serving, tuning, and multi-tenancy.

```bash
kind create cluster --name kubeflow-lab

export PIPELINE_VERSION=2.0.5

kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/platform-agnostic-pns?ref=$PIPELINE_VERSION"

kubectl get pods -n kubeflow --watch
```

When the pipeline UI is ready, port-forwarding is enough for a local lab. In production, you would normally use an ingress path, authentication, authorization, TLS, and network policy instead of an unauthenticated local tunnel. The lab version teaches component behavior without pretending it is a production access model.

```bash
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
```

If the UI does not load, debug from the service inward. Check whether the service exists, whether endpoints are populated, whether pods are ready, and whether logs show database or metadata failures. This is ordinary Kubernetes troubleshooting applied to an ML platform.

```bash
k get svc -n kubeflow ml-pipeline-ui
k get endpoints -n kubeflow ml-pipeline-ui
k get pods -n kubeflow -l app=ml-pipeline-ui
k logs -n kubeflow deploy/ml-pipeline-ui --tail=100
```

A senior operator keeps installation state in Git, not in terminal history. Once the lab becomes a shared platform, pin versions, store overlays, review diffs, and promote changes through environments. Kubeflow is infrastructure, so the installation method should be as reproducible as the ML workflows it runs.

## Kubeflow Pipelines As The Backbone

Kubeflow Pipelines is often the first useful Kubeflow component because it changes a fragile training process into a versioned workflow. Each step runs in a container. Inputs and outputs are declared. Datasets, models, and metrics become artifacts. The pipeline run records what happened and gives the team a place to inspect failures.

The key shift is from "a script did several things" to "a graph of containerized steps produced named artifacts." That matters because machine learning work often moves large files that do not belong in a workflow database. A dataset, trained model, or evaluation report should live in artifact storage, while metadata records where it came from and how it was produced.

```ascii
PIPELINE STRUCTURE
====================================================================

Pipeline definition in Python DSL
           │
           ▼
┌────────────────────┐
│ Step 1: Load data  │
│ Output: Dataset    │
└─────────┬──────────┘
          │ Dataset artifact
          ▼
┌────────────────────┐
│ Step 2: Train      │
│ Input: Dataset     │
│ Output: Model      │
└─────────┬──────────┘
          │ Model artifact
          ▼
┌────────────────────┐
│ Step 3: Evaluate   │
│ Input: Model       │
│ Output: Metrics    │
└─────────┬──────────┘
          │ Metrics gate
          ▼
┌────────────────────┐
│ Step 4: Deploy     │
│ Runs only if safe  │
└────────────────────┘
```

A minimal KFP v2 pipeline begins with components. Components should be boring and explicit: choose a base image, declare packages, type inputs and outputs, and keep each step focused. The following worked example trains a small classifier, writes the model as an artifact, and records metrics separately so a later deployment decision can inspect the result.

```python
from kfp import compiler
from kfp import dsl
from kfp.dsl import Dataset
from kfp.dsl import Input
from kfp.dsl import Metrics
from kfp.dsl import Model
from kfp.dsl import Output


@dsl.component(
    base_image="python:3.11",
    packages_to_install=["pandas", "scikit-learn"],
)
def load_data(output_dataset: Output[Dataset]) -> None:
    import pandas as pd
    from sklearn.datasets import load_iris

    iris = load_iris(as_frame=True)
    df = iris.frame
    df.to_csv(output_dataset.path, index=False)


@dsl.component(
    base_image="python:3.11",
    packages_to_install=["joblib", "pandas", "scikit-learn"],
)
def train_model(
    dataset: Input[Dataset],
    output_model: Output[Model],
    n_estimators: int = 100,
) -> None:
    import joblib
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier

    df = pd.read_csv(dataset.path)
    x = df.drop("target", axis=1)
    y = df["target"]

    model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
    model.fit(x, y)

    joblib.dump(model, output_model.path)


@dsl.component(
    base_image="python:3.11",
    packages_to_install=["joblib", "pandas", "scikit-learn"],
)
def evaluate_model(
    dataset: Input[Dataset],
    model: Input[Model],
    metrics: Output[Metrics],
) -> None:
    import joblib
    import pandas as pd
    from sklearn.model_selection import cross_val_score

    df = pd.read_csv(dataset.path)
    x = df.drop("target", axis=1)
    y = df["target"]

    classifier = joblib.load(model.path)
    scores = cross_val_score(classifier, x, y, cv=5)

    metrics.log_metric("accuracy", float(scores.mean()))
    metrics.log_metric("std", float(scores.std()))


@dsl.pipeline(name="iris-training-pipeline")
def iris_pipeline(n_estimators: int = 100) -> None:
    load_task = load_data()

    train_task = train_model(
        dataset=load_task.outputs["output_dataset"],
        n_estimators=n_estimators,
    )

    evaluate_model(
        dataset=load_task.outputs["output_dataset"],
        model=train_task.outputs["output_model"],
    )


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=iris_pipeline,
        package_path="iris_pipeline.yaml",
    )
```

This example is intentionally small, but the production pattern is real. The loading step owns data preparation, the training step owns model creation, and the evaluation step owns measurable quality. If the run fails, the team can inspect the failed container logs and the upstream artifacts instead of rerunning an entire notebook and hoping the same cells execute.

```bash
python -m venv .venv-kfp
. .venv-kfp/bin/activate
pip install "kfp==2.14.2"
python pipeline.py
```

Submitting the compiled package creates a run in the pipeline backend. In a local port-forwarded lab, the client can target the forwarded UI or API endpoint. In a secured production setup, authentication and routing are environment-specific, so teams often wrap submission in an internal CLI or CI job.

```python
from kfp.client import Client

client = Client(host="http://127.0.0.1:8080")

run = client.create_run_from_pipeline_package(
    pipeline_file="iris_pipeline.yaml",
    arguments={"n_estimators": 200},
    experiment_name="iris-experiments",
)

print(f"Run ID: {run.run_id}")
```

**Pause and predict:** if `train_model` writes the model to `/tmp/model.joblib` instead of `output_model.path`, what will the next step receive? The container may finish successfully, but the pipeline artifact will not contain the expected model, so evaluation fails later or receives an empty artifact. This is why artifact paths are part of the component contract, not incidental file names.

Conditionals are how pipelines become deployment workflows rather than linear scripts. The evaluation step produces a metric, and the deployment step should run only when the metric passes a threshold. This teaches an important production habit: deployments should be controlled by explicit gates, not by the optimism of the person who started the run.

```python
@dsl.component(base_image="python:3.11")
def deploy_model(model: Input[Model]) -> None:
    print(f"Deploying model artifact from {model.path}")


@dsl.pipeline(name="conditional-deploy-pipeline")
def conditional_pipeline(accuracy_threshold: float = 0.90) -> None:
    load_task = load_data()

    train_task = train_model(
        dataset=load_task.outputs["output_dataset"],
    )

    eval_task = evaluate_model(
        dataset=load_task.outputs["output_dataset"],
        model=train_task.outputs["output_model"],
    )

    with dsl.If(eval_task.outputs["metrics"].get("accuracy") > accuracy_threshold):
        deploy_model(model=train_task.outputs["output_model"])
```

The worked example also shows a common trap. A pipeline can be syntactically correct and still be operationally weak if each component installs large packages at runtime, uses mutable base images, or downloads the same large dataset repeatedly. Senior teams eventually build stable component images, pin dependencies, cache deterministic steps, and monitor artifact storage costs.

## Notebooks And Team Workspaces

Kubeflow Notebooks give data scientists interactive Jupyter environments that run inside Kubernetes. That sounds simple, but the platform value is not merely "Jupyter in a pod." The value is that notebooks can use the same namespace, service account, storage patterns, container images, and GPU scheduling rules that the rest of the ML platform uses.

A notebook server should be treated like a development workload with production-adjacent constraints. It needs a persistent workspace so users do not lose work when a pod restarts. It needs resource requests so the scheduler can make sane placement decisions. It needs limits so one exploratory session does not starve the namespace. It may need GPU tolerations and node selectors if it uses accelerator nodes.

```yaml
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
        volumeMounts:
        - name: workspace
          mountPath: /home/jovyan
      volumes:
      - name: workspace
        persistentVolumeClaim:
          claimName: notebook-pvc
```

A GPU notebook adds another layer. Requesting `nvidia.com/gpu` is not enough if the cluster does not have GPU nodes, the device plugin is missing, or nodes are tainted without matching tolerations. This is where Kubernetes knowledge matters more than Kubeflow knowledge.

```yaml
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

If a GPU notebook stays Pending, do not debug the notebook UI first. Debug scheduling. Check node labels, taints, allocatable GPUs, namespace quotas, and events. Kubeflow submitted a Kubernetes workload; the scheduler is telling you why it cannot place it.

```bash
k describe notebook -n kubeflow-user gpu-notebook
k get pods -n kubeflow-user
k describe pod -n kubeflow-user gpu-notebook-0
k get nodes -o wide
k describe nodes | grep -A5 -B5 nvidia.com/gpu
k get resourcequota -n kubeflow-user
```

A mature notebook strategy also draws a boundary between exploration and production. Notebooks are excellent for discovery, inspection, and prototyping. They are weak as deployment artifacts because hidden state, manual cell ordering, and local edits are hard to reproduce. The healthy path is to use notebooks to learn, then move stable logic into versioned components, images, and pipelines.

## Multi-Tenancy, Profiles, And Resource Control

Kubeflow multi-tenancy is built around the idea that teams should have isolated workspaces. In Kubernetes terms, that usually means namespaces, service accounts, RoleBindings, secrets, PVCs, quotas, and network rules. Kubeflow Profiles help organize that model for users, but they do not remove the need to understand the underlying Kubernetes controls.

The practical design question is: what can each team see, run, and consume? A research team may need notebook access and moderate CPU. A computer vision team may need GPU quotas and large artifact storage. A regulated team may need stricter service accounts and separate buckets. Treating all teams identically is easy to install and hard to govern.

```ascii
MULTI-TENANT KUBEFLOW SHAPE
====================================================================

┌──────────────────────────────┐   ┌──────────────────────────────┐
│ Profile: fraud-ml            │   │ Profile: vision-ml           │
│ Namespace: team-fraud        │   │ Namespace: team-vision       │
│ ServiceAccount: fraud-runner │   │ ServiceAccount: vision-runner│
│ Quota: CPU + memory          │   │ Quota: CPU + memory + GPU    │
│ Bucket: s3://ml/fraud        │   │ Bucket: s3://ml/vision       │
└──────────────┬───────────────┘   └──────────────┬───────────────┘
               │                                  │
               ▼                                  ▼
       Pipelines, notebooks,               Pipelines, notebooks,
       secrets, PVCs, runs                 secrets, PVCs, runs
```

ResourceQuota is one of the simplest controls to add, and one of the easiest to forget. Without quotas, one team can consume shared cluster capacity with exploratory work. With quotas, failure becomes more predictable: the team sees that a workload exceeded its namespace budget instead of accidentally degrading every other user.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ml-team-quota
  namespace: kubeflow-user
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 80Gi
    limits.cpu: "40"
    limits.memory: 160Gi
    requests.nvidia.com/gpu: "2"
```

LimitRange complements quotas by setting defaults and bounds for individual containers. This prevents small notebook or pipeline steps from launching without requests, which would make scheduling and capacity planning unreliable.

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: ml-defaults
  namespace: kubeflow-user
spec:
  limits:
  - type: Container
    defaultRequest:
      cpu: 500m
      memory: 1Gi
    default:
      cpu: "2"
      memory: 4Gi
    max:
      cpu: "8"
      memory: 32Gi
```

**Active check:** a team reports that pipeline runs started failing after you added quotas. The error says a pod exceeded `requests.memory`. What changed from the team's perspective? The workload did not necessarily become worse; the platform started enforcing a budget that was previously implicit. Your next action is to inspect real resource needs, right-size requests, and decide whether the quota or the workload should change.

Multi-tenancy also changes secret design. A pipeline that reads from object storage should not use a cluster-wide credential mounted into every namespace. Each team should have scoped credentials, and each pipeline component should run with the minimum access it needs. Kubeflow makes it easy to run ML on Kubernetes; it does not automatically make that ML least-privilege.

## Serving Models With KServe

Training is only half of the lifecycle. A model becomes useful to an application when it can answer inference requests reliably. KServe provides a Kubernetes-native abstraction for model serving through `InferenceService` resources. Instead of hand-writing every Deployment, Service, autoscaling rule, and model loading behavior, the team declares the model server shape and storage location.

The simplest serving path uses a built-in runtime such as scikit-learn. The model artifact must already exist in a storage location the serving runtime can access. If the storage URI is wrong or credentials are missing, the `InferenceService` may create pods that fail while trying to load the model. That failure is a storage and identity issue, not a model science issue.

```yaml
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
          cpu: "1"
          memory: 1Gi
```

For custom servers, you provide a container that follows the expected serving contract. This is useful when preprocessing, postprocessing, model framework behavior, or request format does not fit a built-in runtime. The trade-off is ownership: your team now owns server code, image patching, health behavior, and runtime compatibility.

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: custom-model
  namespace: kubeflow-user
spec:
  predictor:
    containers:
    - name: kserve-container
      image: myregistry.example.com/ml/custom-model:v1
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

Canary rollout is valuable when the cost of a bad model is high. A new model can receive a small percentage of traffic while the previous version continues serving most requests. This does not remove the need for monitoring; it gives the platform a safer way to expose change while metrics are watched.

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: iris-classifier
  namespace: kubeflow-user
spec:
  predictor:
    canaryTrafficPercent: 10
    sklearn:
      storageUri: "s3://models/iris/v2"
```

When serving fails, work backward from readiness. Check the `InferenceService`, then the created revisions or pods, then logs, then storage credentials. Many serving incidents are caused by a mismatch between the model artifact, runtime image, and expected request format. The Kubernetes resource may be healthy enough to exist but not healthy enough to answer correct predictions.

```bash
k get inferenceservice -n kubeflow-user
k describe inferenceservice -n kubeflow-user iris-classifier
k get pods -n kubeflow-user
k logs -n kubeflow-user deploy/iris-classifier-predictor --tail=100
```

Senior teams treat serving as a contract. They version the model artifact, the serving image, the request schema, and the rollout plan. They also define rollback behavior before an incident, because discovering rollback mechanics during a model-quality event wastes the most expensive minutes.

## Hyperparameter Tuning With Katib

Hyperparameter tuning becomes painful when teams run many experiments manually and compare results by memory, notebook screenshots, or spreadsheets. Katib turns tuning into a Kubernetes-native experiment. You declare the objective, search algorithm, parameter space, trial template, and limits. Katib creates trials, watches results, and helps search the space more systematically.

The most important part of a Katib experiment is not the algorithm name. It is the objective metric and the way the training container reports it. If the training job does not emit the expected metric, Katib cannot optimize anything meaningful. The platform can schedule many trials, but it cannot infer what your model quality means.

```yaml
apiVersion: kubeflow.org/v1beta1
kind: Experiment
metadata:
  name: random-forest-tuning
  namespace: kubeflow-user
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
              image: myregistry.example.com/ml/rf-trainer:v1
              command:
              - "python"
              - "/workspace/train.py"
              - "--n-estimators=${trialParameters.n_estimators}"
              - "--max-depth=${trialParameters.max_depth}"
              - "--min-samples-split=${trialParameters.min_samples_split}"
            restartPolicy: Never
```

The algorithm choice should match the search space and budget. Random search is a strong baseline when you need quick exploration. Grid search is simple but grows badly as parameter count increases. Bayesian optimization can be effective for continuous spaces when each trial is expensive. Hyperband can help when you can stop poor trials early.

```ascii
KATIB OPTIMIZATION ALGORITHMS
====================================================================

┌──────────────────────┬─────────────────────────────┬─────────────┐
│ Algorithm            │ Best fit                    │ Risk        │
├──────────────────────┼─────────────────────────────┼─────────────┤
│ random               │ Baseline exploration        │ May waste   │
│ grid                 │ Tiny discrete spaces        │ Explodes    │
│ bayesianoptimization │ Expensive continuous trials │ Needs signal│
│ tpe                  │ Mixed parameter spaces      │ Tuning cost │
│ cmaes                │ Continuous many-parameter   │ Complex     │
│ hyperband            │ Early-stoppable training    │ Needs proxy │
│ enas                 │ Neural architecture search  │ Heavy       │
│ darts                │ Differentiable architecture │ Heavy       │
└──────────────────────┴─────────────────────────────┴─────────────┘
```

Katib is not a substitute for experimental discipline. If the validation split leaks data, Katib will efficiently optimize a misleading metric. If the search space includes nonsense values, Katib will spend cluster resources proving that nonsense is bad. Good tuning starts with a defensible objective and a constrained search space.

A practical debugging move is to run one trial container outside Katib first. If the command cannot train once, it will not train twelve times under a controller. Verify image pull, arguments, data access, metric output, and resource requests before asking Katib to multiply the workload.

## Distributed Training Operators

Distributed training is where Kubeflow's Kubernetes-native shape becomes especially useful. Frameworks such as PyTorch and TensorFlow need coordinated workers, roles, environment variables, restart behavior, and often GPU scheduling. Training operators encode those patterns as custom resources so teams do not reinvent a controller for every framework.

A PyTorch distributed job commonly has one master and several workers. The exact launch command depends on the framework version and training code, so production teams should treat the manifest and the training script as a pair. If the script expects different environment variables or rendezvous behavior than the operator provides, the pods may run but never form a healthy training group.

```yaml
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: pytorch-distributed
  namespace: kubeflow-user
spec:
  pytorchReplicaSpecs:
    Master:
      replicas: 1
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime
            command:
            - "python"
            - "-m"
            - "torch.distributed.run"
            - "--nproc_per_node=1"
            - "train.py"
            resources:
              limits:
                nvidia.com/gpu: "1"
    Worker:
      replicas: 3
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime
            command:
            - "python"
            - "-m"
            - "torch.distributed.run"
            - "--nproc_per_node=1"
            - "train.py"
            resources:
              limits:
                nvidia.com/gpu: "1"
```

TensorFlow jobs use a different role structure, often including parameter servers and workers. The operational questions remain the same: can the pods schedule, can they communicate, can they access data, do they have the right accelerator runtime, and do failures restart in a way the framework can tolerate?

```yaml
apiVersion: kubeflow.org/v1
kind: TFJob
metadata:
  name: tf-distributed
  namespace: kubeflow-user
spec:
  tfReplicaSpecs:
    PS:
      replicas: 2
      template:
        spec:
          containers:
          - name: tensorflow
            image: tensorflow/tensorflow:2.15.0-gpu
    Worker:
      replicas: 4
      template:
        spec:
          containers:
          - name: tensorflow
            image: tensorflow/tensorflow:2.15.0-gpu
            resources:
              limits:
                nvidia.com/gpu: "1"
```

Distributed training failure analysis is mostly sequencing. First check whether all pods exist. Then check scheduling events. Then check startup logs for rendezvous or dependency failures. Then check network policy, service discovery, and data access. Jumping straight into framework logs before confirming Kubernetes placement often wastes time.

```bash
k get pytorchjobs -n kubeflow-user
k describe pytorchjob -n kubeflow-user pytorch-distributed
k get pods -n kubeflow-user -l pytorch-job-name=pytorch-distributed
k describe pod -n kubeflow-user pytorch-distributed-master-0
k logs -n kubeflow-user pytorch-distributed-master-0 --tail=100
```

The senior-level judgment is knowing when distributed training is unnecessary. If a model trains in twenty minutes on one GPU, distributed training may add complexity without reducing real delivery time. If training takes days, blocks experimentation, and uses a framework that scales efficiently, the operator pattern is worth the platform investment.

## Worked Example: Diagnosing A Slow Pipeline

A platform team receives a complaint that a four-step training pipeline takes ten hours, even though the actual model training step uses only one hour of GPU time. The team suspects Kubeflow is slow. A better diagnosis starts by separating orchestration overhead, image startup time, data transfer, preprocessing, training, and evaluation.

```ascii
SLOW PIPELINE TIMELINE
====================================================================

┌──────────────┬──────────────────────────────┬────────────────────┐
│ Stage        │ Observed behavior             │ Likely pressure    │
├──────────────┼──────────────────────────────┼────────────────────┤
│ Load data    │ Downloads same dataset again  │ Object storage I/O │
│ Preprocess   │ CPU pod runs before GPU step  │ CPU scheduling     │
│ Train        │ GPU active for one hour       │ Compute            │
│ Evaluate     │ Downloads model and dataset   │ Artifact transfer  │
└──────────────┴──────────────────────────────┴────────────────────┘
```

The first fix is to stop treating object storage paths as informal strings passed between steps. Pipeline artifacts should represent the dataset and model outputs so downstream steps receive managed inputs. This does not eliminate object storage, but it makes the artifact flow explicit and inspectable.

```python
@dsl.component(
    base_image="python:3.11",
    packages_to_install=["pandas"],
)
def preprocess(
    raw_data: Input[Dataset],
    processed_data: Output[Dataset],
) -> None:
    import pandas as pd

    df = pd.read_csv(raw_data.path)
    cleaned = df.dropna()
    cleaned.to_parquet(processed_data.path)
```

The second fix is to enable caching only where it is safe. A deterministic preprocessing step with the same inputs can often be cached. A training step that intentionally includes randomness, reads external mutable data, or depends on time-sensitive features should be reviewed before caching. Caching is an engineering decision, not a magic speed button.

```python
@dsl.pipeline(name="cached-preprocessing-example")
def cached_pipeline() -> None:
    load_task = load_data()
    preprocess_task = preprocess(raw_data=load_task.outputs["output_dataset"])
    preprocess_task.set_caching_options(True)

    train_model(dataset=preprocess_task.outputs["processed_data"])
```

The third fix is image hygiene. Installing large Python packages on every run makes every step pay dependency setup costs. For common components, build and scan reusable images with pinned dependencies. Keep ad hoc `packages_to_install` for learning, prototypes, or rare steps where startup time is not material.

The fourth fix is to observe the timeline instead of guessing. Look at step duration, pod pending time, image pull time, artifact upload and download time, node placement, and GPU utilization. A ten-hour pipeline is rarely one problem. It is usually several small frictions multiplied by repeated runs.

## Did You Know?

1. Kubeflow began as Kubernetes tooling around TensorFlow workflows and grew into a broader collection of Kubernetes-native ML projects rather than remaining a single-framework platform.

2. Kubeflow Pipelines v2 compiles Python pipeline definitions into an intermediate representation YAML, which separates authoring from the runtime that executes the workflow.

3. Pipeline artifacts are designed for large ML outputs such as datasets, models, and metrics, while metadata records lineage so teams can inspect what produced each run result.

4. Kubeflow training operators reduce the custom coordination code needed for distributed jobs, but the training script still has to match the framework's distributed launch behavior.

## Common Mistakes

| Mistake | What happens | Better practice |
|---------|--------------|-----------------|
| Installing full Kubeflow for one simple workflow | The team inherits dashboards, controllers, identity, and serving components before it has a need for them. | Start with Kubeflow Pipelines or a smaller stack, then add components when a real workflow requires them. |
| Treating notebooks as production artifacts | Hidden state and manual cell order make training hard to reproduce during incidents or audits. | Move stable logic into versioned pipeline components, images, and tests. |
| Writing outputs to arbitrary container paths | Downstream steps cannot find the expected dataset, model, or metrics artifact. | Write to the `Output[...]` path provided by the KFP component contract. |
| Leaving requests and limits unset | Pods schedule unpredictably, notebooks consume shared capacity, and quota enforcement becomes confusing. | Define namespace quotas, default limits, and workload-specific requests. |
| Using one shared credential across all teams | A compromised notebook or pipeline can access data outside its intended scope. | Scope secrets by namespace, service account, and storage prefix. |
| Optimizing Katib before validating one trial | The controller multiplies an image, command, data, or metric bug across many failed jobs. | Run the training command once, verify metric output, then create the experiment. |
| Serving a model without versioning the request contract | Applications may send payloads the new model server cannot parse, even when the pod is healthy. | Version the model artifact, image, input schema, and rollout plan together. |
| Blaming Kubeflow before checking Kubernetes events | Scheduling, image pull, storage, and quota issues are mistaken for platform-specific failures. | Debug from Kubernetes resources inward: events, pods, logs, services, and backing storage. |

## Quiz

### Question 1

Your team has a managed notebook service, one nightly retraining job, and no need for shared Kubeflow dashboards. A manager asks you to install full Kubeflow because "we are doing MLOps now." What recommendation would you make, and what evidence would you use?

<details>
<summary>Show Answer</summary>

Recommend starting with Kubeflow Pipelines only, or another small workflow tool if it already fits the platform. The evidence is that the current bottleneck is repeatable scheduled training, not notebooks, multi-tenant dashboards, Katib, KServe, or distributed training. Full Kubeflow would add operational surface area before the team has a demonstrated need for it.

A senior answer also names the expansion path. If the team later needs namespace-isolated notebooks, shared experiment UI, hyperparameter tuning, or Kubernetes-native serving, those needs can justify adding more Kubeflow components. The decision should follow workflow pressure, not platform branding.

</details>

### Question 2

A Kubeflow Pipeline run shows the training step completed successfully, but the evaluation step fails because it cannot load the model file. The training component wrote `model.joblib` to `/tmp`. What is the likely design bug, and how would you fix it?

<details>
<summary>Show Answer</summary>

The training component violated the artifact contract. It wrote the model to an arbitrary local path instead of the `Output[Model]` path supplied by Kubeflow Pipelines. The container's local filesystem is not the durable artifact interface between steps.

Fix the component by declaring `output_model: Output[Model]` and writing the model to `output_model.path`. Then pass `train_task.outputs["output_model"]` into the evaluation component as an `Input[Model]`. After recompiling and rerunning, inspect the run artifacts to verify that the model output exists.

</details>

### Question 3

A GPU notebook remains Pending after a user selects a CUDA notebook image and requests one GPU. The notebook UI shows only a generic scheduling failure. What would you check first, and why?

<details>
<summary>Show Answer</summary>

Check Kubernetes scheduling conditions before debugging Kubeflow UI behavior. Run `k describe pod` for the notebook pod, inspect events, check whether nodes expose `nvidia.com/gpu`, confirm the NVIDIA device plugin is running, review taints and tolerations, and inspect namespace ResourceQuota.

The likely issue is not that Kubeflow failed to create a notebook. The more likely issue is that the scheduler cannot place the pod because GPU resources, tolerations, node labels, or quota do not match the request. Kubeflow submitted a Kubernetes workload, so Kubernetes events are the fastest source of truth.

</details>

### Question 4

A Katib experiment creates twelve failed trials. Every trial exits quickly, and none reports the objective metric named `accuracy`. The team wants to switch from random search to Bayesian optimization. What should you do instead?

<details>
<summary>Show Answer</summary>

Do not change the search algorithm first. Validate a single trial container outside Katib or with one controlled trial. Confirm that the image pulls, the command arguments match the training script, the dataset is accessible, and the script emits the objective metric in the format Katib expects.

Changing algorithms would only schedule failures differently. Katib can optimize a metric only after the trial template reliably produces that metric. The correct fix is to repair the trial contract before scaling the experiment.

</details>

### Question 5

A model served through KServe becomes Ready, but application requests fail with payload parsing errors. The model artifact is new, while the application still sends the old JSON shape. What went wrong operationally?

<details>
<summary>Show Answer</summary>

The rollout treated model serving as only a model artifact change, but inference is a contract among the model, serving image, request schema, and client application. Kubernetes readiness can show that the server process is running, while the business API contract is still broken.

The fix is to version and test the request schema with the model and serving image. Use canary traffic only after compatibility tests pass, monitor prediction errors and response codes, and keep a rollback path to the previous model and schema combination.

</details>

### Question 6

A pipeline that used to finish in two hours now takes most of the day. Logs show every step downloads the same large dataset from object storage, and GPU utilization is low until late in the run. What changes would you propose?

<details>
<summary>Show Answer</summary>

First, make dataset and processed data movement explicit through pipeline artifacts instead of repeatedly downloading the same raw object in every step. Second, cache deterministic preprocessing steps if their inputs are stable. Third, review component images so package installation and image pulls are not dominating runtime.

You should also inspect the run timeline: pod pending time, image pull time, artifact transfer time, preprocessing duration, and GPU utilization. The goal is to identify whether the bottleneck is orchestration, storage I/O, CPU preprocessing, or actual training compute. Low GPU utilization suggests the expensive accelerator is waiting for earlier stages.

</details>

### Question 7

Two teams share one Kubeflow cluster. One team launches large exploratory notebooks and the other team's pipelines start failing to schedule. There are no namespace quotas. What platform change would you make, and what trade-off should you explain?

<details>
<summary>Show Answer</summary>

Add namespace-level ResourceQuota and LimitRange policies for each team profile. Quotas prevent one namespace from consuming all shared CPU, memory, or GPU capacity. LimitRanges provide defaults and bounds so notebooks and pipeline steps cannot omit resource requests completely.

The trade-off is that some workloads will fail earlier with quota errors. That is usually a better failure mode than silent cluster starvation, but the platform team must help users right-size requests and create an escalation path when a legitimate experiment needs more capacity.

</details>

### Question 8

A distributed PyTorch job creates a master pod and three worker pods. All pods start, but training never progresses beyond rendezvous initialization. What Kubernetes and application-level checks would you perform?

<details>
<summary>Show Answer</summary>

At the Kubernetes level, verify all pods are Running, inspect logs for each role, check services or DNS names used for rendezvous, review network policies, and confirm that the pods can communicate inside the namespace. Also check GPU allocation and node placement if the job expects accelerators.

At the application level, confirm the launch command matches the PyTorch version and the training script's distributed assumptions. A manifest can be valid while the script expects different environment variables, ranks, ports, or worker counts. The operator coordinates the job shape, but the training code still has to participate correctly.

</details>

## Hands-On Exercise

### Objective

Deploy a minimal Kubeflow Pipelines environment, compile a small KFP v2 pipeline, run it, and debug it using Kubernetes and pipeline-level evidence. The goal is not to memorize installation commands. The goal is to practice the workflow you would use when a real team asks why an ML run is not reproducible.

### Part 1: Create a local cluster

Use a local `kind` cluster so the exercise does not depend on a shared environment. If you already have a cluster for Kubeflow practice, use a separate namespace and be careful not to reuse production credentials.

```bash
kind create cluster --name kubeflow-lab
kubectl cluster-info --context kind-kubeflow-lab
```

Success criteria:

- [ ] The `kind-kubeflow-lab` cluster exists.
- [ ] `kubectl cluster-info` returns a reachable control plane.
- [ ] You can run `kubectl get nodes` successfully.

### Part 2: Install Kubeflow Pipelines only

Install the pipeline component rather than full Kubeflow. This keeps the lab focused on workflow execution, artifacts, and run inspection.

```bash
export PIPELINE_VERSION=2.0.5

kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/platform-agnostic-pns?ref=$PIPELINE_VERSION"

kubectl get pods -n kubeflow --watch
```

Success criteria:

- [ ] The `kubeflow` namespace exists.
- [ ] Pipeline-related pods eventually reach Running or Completed.
- [ ] You can identify at least one service related to the pipeline UI or API.
- [ ] You inspected events for any pod that did not become ready on the first attempt.

### Part 3: Access the pipeline UI

Forward the pipeline UI locally. Use `127.0.0.1` for the browser URL.

```bash
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
```

Success criteria:

- [ ] The UI is reachable at `http://127.0.0.1:8080`.
- [ ] You can find the experiments or runs area.
- [ ] You can explain why this access method is acceptable for a lab but not for production.

### Part 4: Create and compile a simple pipeline

Save the following as `simple_pipeline.py`. This pipeline is intentionally small, but it still demonstrates component boundaries and data flow between steps.

```python
from kfp import compiler
from kfp import dsl


@dsl.component(base_image="python:3.11")
def say_hello(name: str) -> str:
    message = f"Hello, {name}!"
    print(message)
    return message


@dsl.component(base_image="python:3.11")
def process_message(message: str) -> str:
    result = message.upper()
    print(result)
    return result


@dsl.component(base_image="python:3.11")
def write_report(message: str) -> str:
    report = f"Processed message: {message}"
    print(report)
    return report


@dsl.pipeline(name="hello-pipeline")
def hello_pipeline(name: str = "Kubeflow") -> None:
    hello_task = say_hello(name=name)
    processed_task = process_message(message=hello_task.output)
    write_report(message=processed_task.output)


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=hello_pipeline,
        package_path="hello_pipeline.yaml",
    )
```

Compile it with a local virtual environment.

```bash
python -m venv .venv-kfp
. .venv-kfp/bin/activate
pip install "kfp==2.14.2"
python simple_pipeline.py
```

Success criteria:

- [ ] `hello_pipeline.yaml` is created.
- [ ] The pipeline has three components.
- [ ] You can point to where data moves from one component to the next.
- [ ] You can explain why this example returns strings rather than large model artifacts.

### Part 5: Upload and run the pipeline

Upload `hello_pipeline.yaml` through the UI, create a run, and set the input name to something other than the default. Watch each step execute.

Success criteria:

- [ ] The pipeline run starts successfully.
- [ ] Each step produces logs.
- [ ] The final step receives the processed output from the previous step.
- [ ] You can find the run ID and explain why run IDs matter for reproducibility.

### Part 6: Debug one intentional failure

Change the base image in one component to a non-existent image tag, recompile, upload the new version, and run it. Then debug the failure from Kubernetes events and pipeline UI evidence.

```python
@dsl.component(base_image="python:3.11-does-not-exist")
def process_message(message: str) -> str:
    result = message.upper()
    print(result)
    return result
```

Success criteria:

- [ ] The run fails for the expected image-related reason.
- [ ] You used `kubectl get pods -n kubeflow` or the relevant runtime namespace to find the failed pod.
- [ ] You inspected pod events or logs rather than guessing from the UI alone.
- [ ] You restored the valid image, recompiled, and ran the pipeline successfully.

### Part 7: Clean up

Delete the lab cluster when you are done.

```bash
kind delete cluster --name kubeflow-lab
```

Success criteria:

- [ ] The local lab cluster is deleted.
- [ ] You can summarize the difference between a pipeline definition, a compiled package, a run, a component, and an artifact.
- [ ] You can name one reason to adopt more Kubeflow components and one reason to avoid doing so too early.

## Next Module

Continue to [Module 9.2: MLflow](../module-9.2-mlflow/) to learn how experiment tracking and model registry patterns compare with Kubeflow's broader platform approach.

## Sources

- [github.com: kubeflow](https://github.com/kubeflow/kubeflow) — The Kubeflow repository overview explicitly describes Kubeflow as a foundation of multiple projects and lists the major component projects.
- [kubeflow-pipelines.readthedocs.io: overview.html](https://kubeflow-pipelines.readthedocs.io/en/sdk-2.14.2/source/overview.html) — The KFP overview explicitly covers IR YAML compilation, containerized component execution, artifact handling, run/experiment management, and caching.
- [github.com: katib](https://github.com/kubeflow/katib) — The Katib repository overview explicitly states support for hyperparameter tuning, early stopping, and neural architecture search.
- [Kubeflow Manifests](https://github.com/kubeflow/manifests) — Shows how the full Kubeflow platform is assembled and installed, including multi-component and multi-tenancy aspects.
