---
title: "Module 9.9: Seldon Core — Multi-Framework Model Serving with Inference Graphs"
slug: module-9.9-seldon-core
sidebar:
  order: 10
---

# Module 9.9: Seldon Core — Multi-Framework Model Serving with Inference Graphs

> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 55-65 minutes
>
> **Prerequisites**: Kubernetes basics (Pods, Services, Deployments), container fundamentals, basic ML model serving concepts (request/response lifecycle, what inference means). KServe module 9.8 is helpful but not required.

## Learning Outcomes

After completing this module, you will be able to:

- **Compare** Seldon Core 2, Seldon Core 1, KServe, and plain Kubernetes Deployments for model serving workloads with different routing and monitoring needs.
- **Design** Seldon `Model`, `Server`, `Pipeline`, `SeldonRuntime`, and `Experiment` resources that compose into a production inference application.
- **Implement** a multi-framework Seldon deployment with two model variants, a chained inference graph, traffic splitting, and Alibi explainability.
- **Diagnose** model loading, runtime selection, pipeline routing, and data science monitoring failures by following Seldon status and data-plane signals.
- **Evaluate** when Seldon Core is the better platform choice than KServe, and when KServe remains the cleaner fit.

## Why This Module Matters

A lending company shipped a credit-risk model behind a normal Kubernetes Deployment.
The first version was a small scikit-learn classifier, and the platform team wrapped it in a Flask API.
The endpoint looked like every other internal service: Deployment, Service, readiness probe, HPA, and a dashboard showing HTTP latency.
For two months, that was enough.
Then the data science team introduced a second model for a different applicant segment, a preprocessing step trained in MLflow, and an explanation requirement from the compliance team.
The application wrapper grew into a hand-written router, artifact downloader, metrics adapter, and audit logger.
During a Friday rollout, 18% of applications were scored by the wrong model branch because a feature-normalization response was passed into the wrong downstream endpoint.

The outage did not look like a broken pod.
All pods were ready.
HTTP 200 rates were high.
The damage appeared later, when analysts found inconsistent decision reasons across customer cohorts.
The company spent the next sprint reconciling decisions, rerunning applications, and proving to auditors that rejected applicants had not been processed by an unapproved model path.
The financial impact was measured in manual review hours, delayed loan decisions, and risk exceptions rather than a clean cloud bill line item.

Seldon Core exists for that exact class of failure.
It treats inference as a system of models, routes, pipelines, explainers, detectors, traffic splits, and model runtimes instead of pretending a model is just another web container.
This module teaches Seldon Core 2 because Core 2 is the current architecture for data-centric pipelines, multi-model serving, and Kubernetes-native model management.
You will still learn where Core 1 fits historically, because many teams are migrating from Core 1 and need to recognize the old inference graph model when they see it.

## Seldon Core Architecture: What Kubernetes Does Not Know About Models

A plain Kubernetes Deployment can run a model server.
It can restart the container.
It can scale replicas.
It can expose a Service.
It cannot tell whether a `joblib` artifact should be loaded by MLServer, whether a TensorRT model belongs on Triton, whether two model versions should split traffic 80/20, or whether a drift detector should observe the request stream without delaying the response.

Seldon Core adds model-serving intent on top of Kubernetes.
You declare resources such as `Model`, `Server`, `Pipeline`, `Experiment`, and `SeldonRuntime`.
The Seldon controller reconciles those resources.
The Scheduler decides where models, pipelines, and experiments belong.
The Agent sits next to model servers and manages model loading, unloading, proxying, and metrics.
Envoy receives inference traffic and routes it to the right server or gateway.

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                         Seldon Core 2 Control Plane                        │
│                                                                            │
│  Kubernetes API                                                            │
│       │                                                                    │
│       ▼                                                                    │
│  ┌────────────────────┐       reconcile       ┌─────────────────────────┐  │
│  │ Model / Server     │──────────────────────▶│ Seldon Controller       │  │
│  │ Pipeline / Runtime │                       └─────────────┬───────────┘  │
│  │ Experiment         │                                     │              │
│  └────────────────────┘                                     ▼              │
│                                                   ┌─────────────────────┐  │
│                                                   │ Scheduler           │  │
│                                                   │ load, unload, place │  │
│                                                   └──────────┬──────────┘  │
└──────────────────────────────────────────────────────────────┼─────────────┘
                                                               │
┌──────────────────────────────────────────────────────────────┼─────────────┐
│                         Seldon Core 2 Data Plane             ▼             │
│                                                                            │
│  Client ──HTTP/gRPC──▶ Envoy ──▶ Agent ──▶ MLServer or Triton               │
│                          │                                                 │
│                          └──▶ Pipeline Gateway ──▶ Kafka ──▶ Dataflow      │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

Core 2 is preferred for new Kubernetes serving platforms because it separates the control plane from the data plane and uses a dataflow design for pipelines.
If the Scheduler has a temporary control-plane problem, already-loaded model data-plane traffic can still continue.
If a pipeline needs asynchronous processing, Kafka topics can preserve intermediate data.
If model teams deploy many small models, shared MLServer or Triton server farms can host multiple models rather than one Deployment per model.

Core 1 used `SeldonDeployment` and an inference graph expressed inside that deployment.
It was powerful and widely used, but the graph was evaluated through a more centralized orchestration style.
Core 2 moved to separate resources and a Scheduler-centered model-management design.
The practical migration shift is this: in Core 1, a deployment often described the serving graph and its pods together; in Core 2, models, servers, pipelines, experiments, and runtimes are independent resources that compose.

Core 1 is still relevant when you inherit older installations or enterprise environments that have standardized on its API.
Core 2 is the better default when you want shared servers, Kafka-backed dataflow, native Core 2 pipelines, and a clearer control-plane/data-plane split.
That does not make Core 2 simpler in every case.
It adds moving parts, especially Kafka when pipelines are enabled.
It earns those moving parts when model serving is no longer a single endpoint.

**Pause and predict:** if you deploy ten sklearn models with nearly identical dependencies, should each one become its own Kubernetes Deployment, or should they share a Seldon `Server` farm?
Sharing a server farm is usually the better Seldon Core 2 shape because the `Server` owns the runtime capacity and each `Model` declares requirements.
That lets the Scheduler place compatible models onto existing serving infrastructure.

### The Resource Map

Seldon Core 2 resources divide responsibilities sharply.
That division is the main thing to learn before writing YAML.
If you put a responsibility in the wrong object, the manifest may apply, but the platform will feel harder to operate.

| Resource | Owns | Reconciles Toward | Why It Exists |
|---|---|---|---|
| `Model` | A model-like artifact and its runtime requirements | A loaded model on a compatible server | Keeps model identity, artifact location, memory, and monitoring roles separate from pod templates |
| `Server` | A runtime farm such as MLServer or Triton | Pods and server capacity with declared capabilities | Lets many models share runtime infrastructure |
| `Pipeline` | A graph of model steps and tensor flow | Scheduler/dataflow pipeline state and endpoint routing | Makes chains, joins, conditional routes, and async paths declarative |
| `SeldonRuntime` | A namespace-level Seldon runtime instance | Core components such as gateways and supporting services | Gives platform teams a way to stamp Seldon into namespaces with overrides |
| `Experiment` | Traffic split or mirror between models or pipelines | Experiment endpoint and routing state | Lets teams test variants without writing custom routers |

### Why a Deployment Is Not Enough

A Deployment knows images and replicas.
A model-serving platform must know artifacts and contracts between artifacts.
An sklearn model might be a `model.joblib` plus `model-settings.json`.
An MLflow artifact might include environment metadata and a pyfunc wrapper.
A HuggingFace model might require tokenizer files and text-specific runtime support.
A Triton model repository might contain versioned directories and backend configuration.

With raw Kubernetes, each team has to encode these differences into custom containers.
With Seldon, the platform team standardizes runtimes through `Server` and `ServerConfig`.
Model teams declare `storageUri`, `requirements`, and resource estimates on `Model`.
The Scheduler matches the two.

This is similar to a train station.
The train is the model artifact.
The platform is not asking every passenger to build their own track.
The `Server` is the track and station capacity.
The `Model` is the passenger's destination and requirements.
The Scheduler decides which platform can take the train.

## CRDs in Detail: Model, Server, Pipeline, SeldonRuntime, Experiment

The Seldon CRDs are not just API decoration.
Each one gives the controller and Scheduler a smaller, clearer job.
This section walks through the important fields and the reasoning behind them.
It is not a field catalog.
The goal is to know which object should change when a model fails to load, a graph routes incorrectly, or a tenant needs isolated runtime components.

### Model

`Model` is the atomic serving unit in Core 2.
It can represent a predictive model, a preprocessor, a drift detector, an outlier detector, an explainer, or another model-like component.
The most important fields are `storageUri`, `requirements`, and resource estimates such as `memory`.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: iris-sklearn
  namespace: seldon-mesh
spec:
  storageUri: "gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn"
  requirements:
    - sklearn
  memory: 100Ki
```

`storageUri` tells Seldon where the artifact lives.
The URI may point at cloud storage, object storage, or another rclone-supported location.
This is important because the model artifact changes more often than the serving runtime image.
You do not want to rebuild a container every time a retraining job writes a new artifact.

`requirements` is how the model asks for a compatible runtime.
A model requiring `sklearn` should land on a server with sklearn capability.
A model requiring `triton` should land on a Triton-capable server.
This is not a label for humans.
It is an input to scheduling.

`memory` gives the Scheduler a placement signal.
Multi-model serving becomes risky if every model claims to need almost nothing.
The Scheduler can only make good placement decisions when model memory estimates are realistic.
The same applies to GPU-backed servers: if a model actually consumes large device memory but declares too little, one "successful" deployment can become a latency problem for every colocated model.

The reconciliation loop for a `Model` is roughly:

1. The Kubernetes controller observes the `Model`.
2. It sends model intent to the Scheduler.
3. The Scheduler finds a compatible `Server`.
4. The Agent on that server loads the artifact into MLServer or Triton.
5. Status updates show whether the model is ready, loading, failed, or not scheduled.

When a model is stuck, read the status first.
Then check whether any server has matching capabilities.
Then inspect Agent and runtime logs.
Do not start by editing the model image, because the image often belongs to `Server`, not `Model`.

### Server

`Server` defines a runtime farm.
It says which server configuration to use, which capabilities it exposes, and how the underlying pod should be shaped.
Core 2 commonly installs MLServer and Triton servers by default.
MLServer covers frameworks such as sklearn, XGBoost, MLflow, HuggingFace, LightGBM, Python, Alibi Explain, and Alibi Detect.
Triton covers high-performance inference backends such as TensorFlow, PyTorch, ONNX, TensorRT, OpenVINO, and Python backends.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Server
metadata:
  name: mlserver-custom
  namespace: seldon-mesh
spec:
  serverConfig: mlserver
  capabilities:
    - sklearn
    - xgboost
    - mlflow
    - alibi-explain
  podSpec:
    containers:
      - name: mlserver
        image: seldonio/mlserver:1.6.0
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2"
            memory: "4Gi"
```

`serverConfig` references a reusable configuration for a runtime type.
The `Server` can inherit defaults and override only the parts that matter.
That is useful when the platform team wants one standard MLServer image for ordinary models and a second image with custom Python dependencies.

`capabilities` replaces the inherited capability list.
Use it when the server image is intentionally narrow.
`extraCapabilities` appends to inherited capabilities.
Use it when the server is mostly standard but adds one tag, such as a custom dependency bundle.

`podSpec` is where Kubernetes scheduling detail belongs.
If the runtime needs GPU resources, node selectors, tolerations, memory limits, or a custom image, put that on the `Server`.
Do not copy pod details into every `Model`.
That defeats the point of separating artifacts from runtime infrastructure.

The reconciliation loop for a `Server` is:

1. The controller observes the `Server`.
2. It creates or updates serving pods according to `serverConfig` and `podSpec`.
3. Agents register available capacity and capabilities with the Scheduler.
4. The Scheduler places compatible `Model` resources onto server replicas.
5. Status reports readiness, replica count, and loaded model count.

### Pipeline

`Pipeline` is Seldon's Core 2 inference graph resource.
It describes a flow of model steps.
Each step normally refers to a `Model` with the same name.
Inputs define which upstream step outputs feed the current step.
The `output` section defines what the synchronous caller receives.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Pipeline
metadata:
  name: risk-chain
  namespace: seldon-mesh
spec:
  steps:
    - name: risk-preprocess
    - name: risk-score
      inputs:
        - risk-preprocess
      tensorMap:
        risk-preprocess.outputs.OUTPUT0: INPUT0
  output:
    steps:
      - risk-score
```

`steps` is the ordered inventory of graph nodes.
The list order is not the only thing that matters.
The data dependencies in `inputs`, `triggers`, and tensor references define when a step can run.

`inputs` points at upstream step outputs.
If the entry is just `risk-preprocess`, Seldon treats it as the output of that step.
If you need one tensor, use the dot notation, such as `risk-preprocess.outputs.OUTPUT0`.

`tensorMap` renames upstream tensors for downstream models.
This solves a real integration problem.
One model may emit `OUTPUT0`; the next runtime may expect `INPUT0`.
Without explicit mapping, teams often hide that mismatch in brittle wrapper code.

`output.steps` defines the returned value for synchronous calls.
A pipeline may include monitoring or detector steps that are not on the synchronous return path.
Those steps can still consume data and emit Kafka topics.
That is one of the main reasons Core 2 pipelines are useful in production.

The reconciliation loop for a `Pipeline` is:

1. The controller observes the `Pipeline`.
2. It submits graph intent to the Scheduler.
3. The Scheduler validates referenced models and graph shape.
4. Pipeline gateway and dataflow components create routing and Kafka-backed flow.
5. Status moves to ready when the graph and required model steps are available.

### SeldonRuntime

`SeldonRuntime` creates a Seldon Core instance in a namespace.
Platform teams use it to install runtime components with namespace-specific overrides.
This matters for multi-tenancy.
One tenant may need a small runtime with default MLServer.
Another tenant may need isolated gateways, larger Scheduler timeouts, or disabled components.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: SeldonRuntime
metadata:
  name: seldon
  namespace: seldon-mesh
spec:
  seldonConfig: default
  overrides:
    - name: hodometer
      podSpec:
        containers:
          - name: hodometer
            resources:
              limits:
                cpu: 20m
                memory: 64Mi
```

`seldonConfig` points to a baseline platform configuration.
That baseline is usually installed by Helm.
It lets the organization keep common defaults in one place.

`overrides` changes a component without forking the entire installation.
In production, this is where you would set resource limits, replica counts, service type, or component-level pod settings.
Treat these overrides like platform operations, not model-team tuning knobs.

The reconciliation loop for `SeldonRuntime` is:

1. The controller observes a runtime request in a namespace.
2. It reads the referenced `SeldonConfig`.
3. It creates or updates the runtime components for that namespace.
4. It applies component overrides.
5. It updates status as the runtime becomes ready.

### Experiment

`Experiment` defines traffic splitting or mirroring between models or pipelines.
It is the Seldon-native way to run A/B tests without writing custom routing code.
Candidates get weights.
The percentage of traffic is each weight divided by the total weight.
An optional `default` can expose the experiment on an existing model or pipeline endpoint.
An optional `mirror` receives a copy of traffic without returning its response to the caller.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Experiment
metadata:
  name: risk-ab
  namespace: seldon-mesh
spec:
  default: risk-v1
  candidates:
    - name: risk-v1
      weight: 80
    - name: risk-v2
      weight: 20
```

The `default` field is powerful because it lets a team preserve an existing endpoint while splitting traffic behind it.
That is safer for consumers than inventing a new endpoint name for every test.
If you omit `default`, the experiment exposes its own endpoint and callers route with an experiment-specific header.

For pipeline experiments, add `resourceType: pipeline`.
The candidates then refer to pipeline names rather than model names.
This is useful when the thing being tested is not just a model artifact but an entire graph.

The reconciliation loop for an `Experiment` is:

1. The controller observes the `Experiment`.
2. The Scheduler checks that candidates are ready.
3. Seldon configures the experiment route.
4. Inference requests route according to candidate weights.
5. Status reflects whether the experiment is active.

## Multi-Framework Model Loading

Multi-framework serving is one of the reasons teams choose Seldon.
A mature ML platform rarely serves only one kind of artifact.
One team ships sklearn classifiers.
Another ships XGBoost ranking models.
A forecasting group exports MLflow artifacts.
An NLP group wants HuggingFace models.
A computer vision team needs custom Triton backends.
If each team brings its own HTTP server, the platform becomes a museum of wrappers.

Seldon Core 2 pushes that diversity into runtime capabilities.
The `Server` advertises capabilities.
The `Model` requests capabilities.
The Scheduler matches them.
The artifact stays separate from the container image, so retraining does not always imply rebuilding infrastructure.

```ascii
┌───────────────────────┐       requirements       ┌───────────────────────┐
│ Model: churn-sklearn  │─────────────────────────▶│ Server: mlserver      │
│ storageUri: gs://...  │                          │ capabilities: sklearn │
└───────────────────────┘                          └───────────────────────┘

┌───────────────────────┐       requirements       ┌───────────────────────┐
│ Model: vision-triton  │─────────────────────────▶│ Server: triton        │
│ storageUri: s3://...  │                          │ capabilities: onnx    │
└───────────────────────┘                          └───────────────────────┘
```

Here is a concrete sklearn model.
It requests `sklearn`, so any compatible MLServer farm can host it.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: credit-sklearn-v1
  namespace: seldon-mesh
spec:
  storageUri: "gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn"
  requirements:
    - sklearn
  memory: 100Ki
```

Here is an XGBoost-style model.
The important change is not the shape of the Kubernetes object.
The important change is the runtime requirement.
That one word changes where the Scheduler is allowed to place the artifact.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: credit-xgboost-v2
  namespace: seldon-mesh
spec:
  storageUri: "s3://example-model-bucket/credit/xgboost/v2"
  requirements:
    - xgboost
  memory: 256Mi
```

Here is an MLflow artifact.
MLflow models often bring richer packaging metadata.
That can reduce custom serving code, but it can also make dependency management stricter.
If the pyfunc model depends on packages not present in the standard runtime, create a custom `Server` image and expose a matching capability.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: churn-mlflow
  namespace: seldon-mesh
spec:
  storageUri: "s3://example-model-bucket/churn/mlflow/2026-04-15"
  requirements:
    - mlflow
    - churn-deps
  memory: 512Mi
```

Here is a custom MLServer runtime that can satisfy `churn-deps`.
The custom image should be built and scanned by the platform pipeline.
The model team should not smuggle dependency installation into model startup.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Server
metadata:
  name: mlserver-churn
  namespace: seldon-mesh
spec:
  serverConfig: mlserver
  extraCapabilities:
    - churn-deps
  podSpec:
    containers:
      - name: mlserver
        image: ghcr.io/example/mlserver-churn:2026-04-15
        resources:
          requests:
            cpu: "1"
            memory: "2Gi"
          limits:
            cpu: "2"
            memory: "4Gi"
```

HuggingFace models are also typically loaded by MLServer when the runtime supports the relevant dependencies.
They need special attention because tokenizer files, model weights, and CPU/GPU memory can be large.
Do not estimate memory from the size of the request payload.
Estimate it from the model weights and runtime behavior.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: sentiment-huggingface
  namespace: seldon-mesh
spec:
  storageUri: "s3://example-model-bucket/nlp/sentiment/hf-distilbert"
  requirements:
    - huggingface
  memory: 2Gi
```

Custom Triton runtimes are a better match when the artifact is already a Triton model repository or when GPU inference performance is the dominant concern.
Triton is also a common choice for ONNX, TensorRT, TensorFlow, and PyTorch-backed deployments.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Server
metadata:
  name: triton-gpu
  namespace: seldon-mesh
spec:
  serverConfig: triton
  extraCapabilities:
    - tensorrt
    - fraud-gpu
  podSpec:
    containers:
      - name: triton
        image: nvcr.io/nvidia/tritonserver:24.10-py3
        resources:
          limits:
            nvidia.com/gpu: "1"
            memory: "12Gi"
          requests:
            cpu: "2"
            memory: "8Gi"
```

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: fraud-triton-v1
  namespace: seldon-mesh
spec:
  storageUri: "s3://example-model-bucket/fraud/triton-repository/v1"
  requirements:
    - triton
    - tensorrt
    - fraud-gpu
  memory: 4Gi
```

Before running a multi-framework deployment, ask one question: which team owns the runtime image?
If model teams own runtime images independently, you will get fast experimentation and inconsistent operations.
If the platform owns all runtime images, you will get consistency and slower dependency updates.
Many organizations split the difference: platform owns the base MLServer and Triton images, while model teams can request a reviewed dependency bundle exposed as a capability.

**Before running this, what output do you expect?**
If a `Model` requests `xgboost` but no `Server` exposes `xgboost`, the model should not become ready.
The failure is a scheduling mismatch, not an HTTP serving failure.

## Inference Graphs: Pipelines as Server-Side Dataflow

An inference graph is a directed flow of inference work.
One request can move through a preprocessor, a model, an explainer, an outlier detector, a ranker, a business-rule model, or several model variants.
The graph exists because real inference applications are rarely a single function call.
They are chains, ensembles, conditional routes, monitoring side paths, and traffic experiments.

Seldon Core 2 expresses inference graphs with the `Pipeline` CRD.
The graph is server-side.
The client does not call model A, parse the response, call model B, and decide what to do next.
The client sends one request to Seldon, and Seldon evaluates the declared graph.

```ascii
Client Request
     │
     ▼
┌───────────────┐
│ Pipeline      │
│ risk-review   │
└──────┬────────┘
       │
       ▼
┌───────────────┐       outputs.OUTPUT0       ┌───────────────┐
│ normalize     │────────────────────────────▶│ risk-score    │
└───────────────┘                              └──────┬────────┘
                                                      │
                                                      ▼
                                             Pipeline Response
```

The `steps` structure is the core of the graph.
Each step has a `name`.
The name usually matches a `Model`.
A step can define `inputs` to consume upstream outputs.
A step can define `tensorMap` to rename tensors.
A step can define triggers and join types for more advanced control flow.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Pipeline
metadata:
  name: credit-review
  namespace: seldon-mesh
spec:
  steps:
    - name: credit-normalize
    - name: credit-sklearn-v1
      inputs:
        - credit-normalize.outputs.OUTPUT0
      tensorMap:
        credit-normalize.outputs.OUTPUT0: INPUT0
  output:
    steps:
      - credit-sklearn-v1
```

Walk the request through that graph:

1. The client sends an Open Inference Protocol request to the `credit-review` pipeline endpoint.
2. Envoy receives the request and routes it toward the pipeline path.
3. The Pipeline Gateway turns the synchronous request into pipeline input data.
4. The `credit-normalize` model receives the original input.
5. Its `OUTPUT0` tensor becomes the input source for `credit-sklearn-v1`.
6. `tensorMap` renames that upstream tensor to `INPUT0`.
7. `credit-sklearn-v1` returns prediction output.
8. The pipeline returns the `credit-sklearn-v1` output because it is listed under `output.steps`.

The important point is that the graph owns the data movement.
If the feature normalization step changes tensor names, you update the pipeline mapping.
You do not hide the change in a client library or a web wrapper.

### Chains, Joins, Conditional Routing, and A/B Routing

A chain feeds one step into the next.
Use it when model B depends on model A's output.
Preprocessing is the common example.

A join combines outputs from multiple steps.
Use it when a downstream model needs several upstream tensors.
Seldon supports join behavior such as `inner`, `outer`, and `any` for appropriate graph shapes.

A conditional route lets data choose a path.
In Seldon pipelines, that can be expressed by tensors, triggers, and join behavior.
For example, a routing model may emit `OUTPUT0` for a low-risk branch and `OUTPUT1` for a high-risk branch.
Downstream steps can depend on those named tensors.

A/B routing can be expressed with `Experiment`.
That is cleaner than encoding random routing in a model step.
The graph should describe inference dataflow.
The experiment should describe traffic allocation.

Here is a simple conditional pattern.
The routing model emits one of two tensors.
Only the matching downstream step receives input.
The pipeline output uses `stepsJoin: any`, because only one path returns data for a request.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Pipeline
metadata:
  name: credit-conditional
  namespace: seldon-mesh
spec:
  steps:
    - name: segment-router
    - name: retail-risk
      inputs:
        - segment-router.outputs.OUTPUT0
      tensorMap:
        segment-router.outputs.OUTPUT0: INPUT0
    - name: business-risk
      inputs:
        - segment-router.outputs.OUTPUT1
      tensorMap:
        segment-router.outputs.OUTPUT1: INPUT0
  output:
    steps:
      - retail-risk
      - business-risk
    stepsJoin: any
```

### Seldon Pipeline vs KServe InferenceGraph

KServe also has an `InferenceGraph`.
The difference is architectural and operational, not merely naming.
KServe's `InferenceGraph` is a graph router around `InferenceService` targets.
Its nodes use router types such as `Sequence`, `Switch`, `Ensemble`, and `Splitter`.
Each step targets an `InferenceService`, another node, or an external service URL.
It is a good fit when you already use KServe `InferenceService` as the unit of serving and want declarative HTTP graph routing.

Seldon's `Pipeline` is Core 2's dataflow resource.
It is tied into Seldon's Scheduler, model gateways, pipeline gateway, and Kafka-backed data movement.
It can treat intermediate step data as observable stream data.
It can run asynchronous paths naturally.
It fits teams that want model serving, routing, detector side paths, and data lineage in one serving fabric.

| Axis | Seldon Core 2 `Pipeline` | KServe `InferenceGraph` |
|---|---|---|
| Primary unit | `Model` steps scheduled onto `Server` farms | `InferenceService` targets or graph nodes |
| Routing shape | Dataflow steps with inputs, tensor references, joins, triggers, and output selection | Node router types: `Sequence`, `Switch`, `Ensemble`, `Splitter` |
| Data path | Envoy, gateways, Agent, optional Kafka-backed pipeline dataflow | Graph router forwarding to inference services |
| Async support | Native Kafka-backed pipeline path when dataflow components are installed | Primarily request/response graph routing |
| Best fit | Complex pipelines, audit trails, detectors, shared model servers | KServe-first platforms needing graph routing across existing inference services |
| Operational tradeoff | More Seldon-specific components, especially for Kafka dataflow | Simpler if KServe is already the platform baseline |

Neither is "just a DAG."
KServe's graph vocabulary is explicit router nodes.
Seldon's graph vocabulary is model-step dataflow.
That difference affects debugging.
In KServe, you inspect the graph router and target `InferenceService` objects.
In Seldon, you inspect the `Pipeline`, the Scheduler state, model readiness, gateway logs, and Kafka/dataflow behavior when enabled.

### Worked Pipeline: Preprocess, Score, and Monitor

The next example has two synchronous steps and one asynchronous monitoring side path.
The client receives only the score.
The drift detector observes batched data but is not on the synchronous output path.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Pipeline
metadata:
  name: credit-production
  namespace: seldon-mesh
spec:
  steps:
    - name: credit-normalize
    - name: credit-sklearn-v1
      inputs:
        - credit-normalize.outputs.OUTPUT0
      tensorMap:
        credit-normalize.outputs.OUTPUT0: INPUT0
    - name: credit-drift
      inputs:
        - credit-normalize.outputs.OUTPUT0
      batch:
        size: 20
  output:
    steps:
      - credit-sklearn-v1
```

Step by step:

1. The original request enters the pipeline.
2. `credit-normalize` transforms raw features into model-ready tensors.
3. `credit-sklearn-v1` receives the normalized tensor and returns a prediction.
4. `credit-drift` receives the same normalized tensor in batches of 20.
5. The caller receives only the prediction.
6. Drift signals can be read from monitoring output, Kafka topics, or Prometheus/Grafana integrations depending on the deployment.

This is the practical fork from a normal web wrapper.
The detector does not need to sit in the latency-critical path.
The pipeline can preserve the synchronous response shape while still producing monitoring evidence.

## Explainability with Alibi

Seldon and Alibi are closely related projects.
Alibi provides algorithms for explaining model behavior.
Seldon Core 2 can serve Alibi explainers as `Model` resources with an `explainer` section.
That means explanation can be attached to a deployed model or pipeline without turning every model team into an explanation-service team.
Some older Seldon material and team runbooks call this role an `AlibiExplainer`.
In current Core 2 manifests, the explainer is expressed as a `Model` with `spec.explainer`.
The operational idea is the same: an explainer artifact is deployed beside a model or pipeline and receives explanation requests through Seldon's serving plane.

Alibi covers several explanation families.
Alibi Anchors explain predictions through high-precision feature rules discovered by perturbing inputs.
<!-- alibi-anchor: technical use of anchor, not meta-diction -->
Integrated Gradients attributes predictions to input features for differentiable models, often deep learning models.
Counterfactual explanations ask what minimal input changes would alter the prediction.
These techniques answer different questions, so do not treat "explainability" as one feature.

| Method | Best Question | Typical Fit | Caution |
|---|---|---|---|
| Alibi Anchors | Which feature conditions are sufficient for this prediction? | Tabular and text black-box classification | The rule can be precise locally without covering many cases |
| Integrated Gradients | Which input dimensions contributed to this neural prediction? | Differentiable models, especially deep learning | Requires model gradients or framework support |
| Counterfactual | What would need to change to get a different outcome? | Decision support and model debugging | Must respect immutable or protected features |

Here is a Core 2 explainer model attached to a deployed `income` model.
The explainer is itself a `Model`.
The `explainer` block tells Seldon this artifact explains another model rather than producing a normal prediction.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: income-explainer
  namespace: seldon-mesh
spec:
  storageUri: "gs://seldon-models/scv2/samples/mlserver_1.5.0/income-sklearn/anchor-explainer"
  explainer:
    type: anchor_tabular
    modelRef: income
```

`type` selects the supported Alibi explainer type.
`modelRef` points at the model being explained.
For a pipeline explanation, use `pipelineRef` instead.
Only one of `modelRef` and `pipelineRef` should be used.

Do not confuse an explainer artifact with a checkbox on the model.
Many explainers need training data, background data, feature metadata, or preprocessing assumptions.
If the model input schema changes, the explainer may become stale even when the model still serves predictions.
Treat explainer artifacts as versioned model artifacts.

Here is a pipeline explainer shape for a HuggingFace-style sentiment pipeline.
The explainer references the pipeline rather than a single model.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: sentiment-explainer
  namespace: seldon-mesh
spec:
  storageUri: "gs://seldon-models/scv2/examples/huggingface/speech-sentiment/explainer"
  explainer:
    type: anchor_text
    pipelineRef: sentiment-explain
```

Explanations should be designed around the consumer.
A data scientist may need local feature attribution for debugging.
A support analyst may need a short rule that can be interpreted consistently.
A regulator may need an audit record showing which model and explainer versions produced a decision.
Seldon gives you the serving hooks, but the organization still needs policy around when explanations are requested, stored, and reviewed.

## Outlier and Drift Detection with Alibi-Detect

Alibi-Detect provides detectors for outliers, adversarial behavior, and data drift.
In Seldon Core 2, these detectors are commonly served as `Model` resources that require `alibi-detect`.
They can be placed in a pipeline side path so detection does not delay the primary prediction response.

Outlier detection asks whether an input looks unusual compared with expected data.
That might catch malformed requests, sensor failures, adversarial examples, or rare production cases.
Drift detection asks whether a batch or stream of production data has shifted away from a reference distribution.
That matters because model accuracy can decay even when code and pods are unchanged.

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: cifar10-outlier
  namespace: seldon-mesh
spec:
  storageUri: "gs://seldon-models/scv2/examples/mlserver_1.3.5/cifar10/outlier-detector"
  requirements:
    - mlserver
    - alibi-detect
```

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: cifar10-drift
  namespace: seldon-mesh
spec:
  storageUri: "gs://seldon-models/scv2/examples/mlserver_1.3.5/cifar10/drift-detector"
  requirements:
    - mlserver
    - alibi-detect
```

Core 2 documentation describes drift and outlier detectors as models rather than separate top-level `OutlierDetector` or `DriftDetector` CRDs.
You may still hear teams use those names as operational roles.
In Core 2 YAML, the detector role is represented by a `Model` with `alibi-detect` requirements and by where that model sits in a `Pipeline`.
In older Seldon Core 1 and adjacent tooling, you may encounter detector-specific resource names or deployment sections.
When working in Core 2, inspect the installed CRDs before copying old examples.

If your platform distribution exposes `OutlierDetector` or `DriftDetector` resources, read them as higher-level wrappers around the same responsibilities.
The detector resource owns a detector artifact, a reference to the model or pipeline stream it observes, and the output channel where detection signals are published.
Its reconciliation loop should create or update the detector serving component, subscribe it to the right inference data, and report readiness or detector failures.
Core 2's open documentation represents that composition directly with `Model` plus `Pipeline`, which is why the manifests below use those resources.

```bash
k api-resources | grep -E 'models|pipelines|experiments|outlier|drift'
```

A detector pipeline often looks like this:

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Pipeline
metadata:
  name: vision-production
  namespace: seldon-mesh
spec:
  steps:
    - name: cifar10
    - name: cifar10-outlier
    - name: cifar10-drift
      batch:
        size: 20
  output:
    steps:
      - cifar10
      - cifar10-outlier.outputs.is_outlier
```

The model prediction is returned.
The outlier signal can also be returned if you list the detector tensor in `output.steps`.
The drift detector may run in batches and emit alerts or output records without being part of the synchronous response.
The detector signal can flow to Kafka topics, Prometheus metrics, dashboards, or alerting rules depending on the installed monitoring stack.

Drift detection is not a replacement for labels.
It is an early-warning system.
If a retail model trained on winter purchasing behavior suddenly receives summer behavior, drift can warn you before labeled outcomes arrive.
If an upstream team changes categorical encoding, drift can tell you the input distribution changed even while HTTP requests remain valid.
The hard part is response policy: what happens when drift is detected?
Good teams predefine whether to alert, shadow a fallback model, pause rollout, or start data review.

## Production Concerns: Kafka, Observability, Tenancy, and Scaling

Seldon Core 2 is a platform, not a tiny library.
That gives it power, but it also means production teams must own the operating model.
The most common production risks are dataflow dependencies, observability gaps, tenant isolation, and misunderstood scaling.

Kafka-backed pipelines are the big architectural choice.
If you use simple model endpoints without pipeline dataflow, you can run a smaller installation.
If you use pipelines with asynchronous steps, Seldon uses Kafka to preserve and move data between steps.
That gives auditability, replay possibilities, and decoupled detector paths.
It also adds Kafka capacity planning, retention policy, topic monitoring, and failure handling.

```ascii
Pipeline Input Topic
        │
        ▼
┌──────────────────┐      Step Output Topic      ┌──────────────────┐
│ Model Gateway    │────────────────────────────▶│ Dataflow Engine  │
└──────────────────┘                             └────────┬─────────┘
                                                           │
                                                           ▼
                                                  Pipeline Output Topic
```

Prometheus metrics are essential.
Seldon components and deployed models can expose metrics for scraping.
A production dashboard should separate control-plane health, data-plane latency, model load status, pipeline lag, Kafka health, and model-specific inference metrics.
One graph called "latency" is not enough.

Tracing is equally important for pipelines.
Jaeger or OpenTelemetry-style tracing helps answer where latency was introduced.
Was the request slow in Envoy?
Was the first model slow?
Was Kafka lagging?
Was the downstream model waiting on a join?
Without trace context, teams argue from partial logs.

Multi-tenancy can be handled with multiple namespaces and multiple `SeldonRuntime` instances.
That gives each tenant separate runtime components and policies.
It also creates more components to upgrade.
Use namespace isolation for real operational or compliance boundaries, not just team branding.

Scaling `Server` replicas is different from scaling a single-model Deployment.
A server replica is runtime capacity that may host multiple models.
More replicas can improve concurrency and availability, but each replica may need to load model artifacts.
For stateless model loading, that is normally fine.
For very large models, scaling can multiply memory use and warm-up time.

Overcommit is useful but not magic.
Seldon can register more model memory than active capacity and evict less-used models.
That can be efficient for long-tail model fleets.
It can also add reload latency when an evicted model receives traffic.
Use overcommit for workloads that tolerate occasional reload costs, not for strict low-latency paths.

War story: a platform team placed dozens of small tabular models on a shared MLServer farm and saved a meaningful amount of cluster overhead.
Then a model team deployed one large NLP model with a low memory estimate.
The Scheduler accepted it, but the server started evicting active models under load.
The incident looked like random p95 latency spikes until the team correlated model load events with prediction latency.
The fix was not a bigger HPA.
The fix was accurate model memory declarations and a separate server capability for large NLP workloads.

## Patterns & Anti-Patterns

| Pattern | When to Use | Why It Works | Scaling Consideration |
|---|---|---|---|
| Shared runtime farm | Many models use the same framework and dependency set | `Server` capacity is reused while `Model` artifacts stay independent | Track memory estimates and model load churn |
| Capability-based dependency bundles | A subset of models need extra packages | Custom `Server` exposes a tag such as `churn-deps` | Keep image count small enough to patch quickly |
| Pipeline side paths for monitoring | Drift or outlier checks should observe traffic without delaying predictions | Detector steps can consume data while `output.steps` stays focused | Monitor Kafka lag and detector batch size |
| Experiment CRD for A/B tests | You need weighted traffic between models or pipelines | Traffic policy is visible in Kubernetes instead of hidden in code | Define rollback and success metrics before splitting traffic |

| Anti-Pattern | What Goes Wrong | Why Teams Fall Into It | Better Alternative |
|---|---|---|---|
| One custom web service per model | Every model has different logging, auth, routes, and model loading behavior | It feels fastest for the first model | Standardize `Server` runtimes and use `Model` artifacts |
| Runtime dependencies hidden in artifacts | Model loads fail only after scheduling | Teams assume `storageUri` can include everything | Build reviewed runtime images and expose capabilities |
| Drift detector on the critical response path | Prediction latency rises and detector failures block users | Teams want every signal returned immediately | Put drift in an async pipeline side path |
| Experiments implemented in client code | Different clients see different routing behavior | Application teams already own SDKs | Use `Experiment` so traffic policy is centralized |
| Memory estimates copied from examples | Shared servers thrash or reject models | Example YAML is treated as production sizing | Measure loaded model memory and update `memory` |
| One namespace for every tenant and workload | RBAC, upgrades, and noisy-neighbor issues become hard to reason about | The first demo used `seldon-mesh` | Use namespace-level `SeldonRuntime` where isolation matters |

## Decision Framework

Use this table to make a concrete platform decision.
The recommendation is intentionally opinionated.
You can override it, but only with a reason stronger than tool familiarity.

| Scenario Axis | Seldon Core Wins When | KServe Wins When | Recommendation |
|---|---|---|---|
| Routing complexity | You need dataflow pipelines, joins, detector side paths, and Kafka-backed auditability | You need `Sequence`, `Switch`, `Ensemble`, or `Splitter` routing across `InferenceService` objects | Choose Seldon for dataflow-heavy graphs; choose KServe for KServe-native HTTP graph routing |
| Explainability depth | You want first-class Alibi explainers attached to models or pipelines | You need lighter predictor/explainer patterns already standardized in KServe | Choose Seldon when Alibi explainability is central to operations |
| Multi-tenancy support | You want namespace-level Seldon runtime instances with server farms per tenant | You already isolate tenants with KServe namespaces, runtimes, and Knative/networking policy | Choose the platform that matches your existing tenant boundary; avoid running both without a platform reason |
| Kafka integration | You need async inference paths, preserved intermediate data, and detector streams | You want simpler request/response serving and do not want Kafka in the serving path | Choose Seldon only if Kafka's operational cost buys real audit or async value |
| Community/support | Your organization uses Seldon tooling, Alibi, or Seldon Enterprise support | Your organization is standardized on KServe, Kubeflow, or Knative patterns | Choose the supported ecosystem your platform team can operate at 3 a.m. |
| When each wins | Complex regulated ML application with monitoring, explainers, and multi-model runtime sharing | Standard model endpoints, serverless/raw KServe modes, and graph routing over existing `InferenceService` resources | For one-off endpoints choose KServe or plain Deployment; for model-serving fabric with dataflow choose Seldon |

If you are building a platform from scratch for many traditional ML models, Seldon Core 2 is attractive because `Server` farms, `Model` resources, `Pipeline`, `Experiment`, and Alibi tooling form one coherent serving fabric.
If your organization already uses KServe for model endpoints and only needs a few graph routes, KServe's `InferenceGraph` will be easier to adopt.
If you have one model, one team, no explainability requirement, and no traffic split, a plain Deployment may still be enough.
Do not install a platform just to avoid writing ten lines of service YAML.

## Did You Know?

1. Seldon Core 2 installation docs describe four Helm chart roles: CRDs, setup, runtime, and servers.
That split mirrors the platform lifecycle: install APIs, install managers and config, stamp runtimes into namespaces, then add server farms.

2. The default MLServer capability list documented by Seldon includes 10 capability tags, including `alibi-detect`, `alibi-explain`, `huggingface`, `mlflow`, `sklearn`, and `xgboost`.
The default Triton list includes 9 tags, including `onnx`, `openvino`, `pytorch`, `tensorflow`, and `tensorrt`.

3. Seldon's multi-model overcommit documentation describes a default overcommit setting of 10%.
It also notes that reloading an evicted model from local disk can have a lower-bound extra latency around 100 ms, which is fine for some fleets and painful for strict latency services.

4. Seldon Core 2's Scheduler startup synchronization has a documented default timeout of 10 minutes.
That number matters during incident response because control-plane status updates can lag while data-plane inference continues.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Putting framework dependencies in every model artifact | Teams think artifact portability means runtime portability | Build a `Server` image with reviewed dependencies and expose a capability tag |
| Using `requirements` as documentation only | The field looks like a human-readable label | Treat requirements as scheduling inputs and verify matching server capabilities |
| Returning every detector output synchronously | Teams want one response with every signal | Return only user-critical outputs and route drift signals through async paths |
| Reusing a pipeline name as a step name | The graph seems small enough that duplicate names feel harmless | Give the pipeline a distinct application name and steps model-like names |
| Forgetting tensor names between steps | Example models happen to use matching names | Use explicit `tensorMap` whenever model output and input tensor names differ |
| Running A/B tests in application clients | The API team already owns routing code | Use `Experiment` so traffic split, default endpoint, and mirror policy are visible |
| Scaling servers without estimating load behavior | A `Server` feels like a normal Deployment | Model load time, artifact cache behavior, and memory determine whether scaling helps |
| Ignoring Kafka when pipelines are enabled | The endpoint looks synchronous to callers | Monitor Kafka topics, lag, retention, and dataflow components as serving dependencies |

## Quiz

<details>
<summary>Your team deploys an sklearn model with `requirements: ["sklearn"]`, but the `Model` never becomes ready. The MLServer pods are running. What do you check first?</summary>

Start with the `Model` status and the available `Server` resources in the namespace.
The pods being up only proves runtime capacity exists, not that the Scheduler found a server whose capabilities match the model requirements.
Check `k get servers -n seldon-mesh` and inspect whether a server advertises `sklearn`.
If capability matching looks correct, move to Agent and MLServer logs for artifact loading errors.
</details>

<details>
<summary>A product team wants to add drift detection to a latency-sensitive payment model. They propose putting the drift detector before the model and blocking requests when drift is detected. How would you redesign it?</summary>

Put the primary prediction on the synchronous path and run drift detection as a side path in the pipeline.
Drift is usually a batch or streaming signal, not a per-request authorization decision.
The detector can consume normalized inputs and emit Kafka or monitoring signals without delaying the payment response.
Define the operational response to drift separately, such as alerting, investigation, or routing a later experiment to a safer model.
</details>

<details>
<summary>Your organization already has 40 KServe `InferenceService` resources and needs a simple sequence from preprocessor to classifier. Should you introduce Seldon Core 2 just for that graph?</summary>

Probably not.
KServe `InferenceGraph` can express a sequence over existing KServe services, so adopting Seldon would add another serving platform for limited benefit.
Seldon becomes more compelling when you also need Seldon server farms, Alibi explainability, Kafka-backed dataflow, or detector side paths.
For this scenario, prefer KServe unless a broader platform migration is already planned.
</details>

<details>
<summary>A model team asks for a custom image because their MLflow model needs two extra Python packages. What platform design avoids image sprawl?</summary>

Create a reviewed custom `Server` image for that dependency set and expose a capability such as `churn-deps`.
Then require models needing those packages to declare both `mlflow` and `churn-deps`.
This keeps the dependency boundary visible to the Scheduler and avoids one image per model.
If many teams need similar packages, promote the bundle into a standard server image.
</details>

<details>
<summary>An A/B test sends 20% of requests to a new model. Support reports that one user gets different variants on repeated calls. What Seldon feature or limitation do you discuss?</summary>

Seldon experiments can return an `x-seldon-route` header that can be passed on later requests to keep a consistent route through an experiment.
The client must still include the normal `seldon-model` header.
This controls routing through model or pipeline choices, but it does not guarantee the same replica instance for stateful models.
If the model is stateful per replica, the model design needs to change before relying on experiment stickiness.
</details>

<details>
<summary>A pipeline step fails because the first model emits `OUTPUT0`, but the second model expects `INPUT0`. Where should this be fixed?</summary>

Fix it in the `Pipeline` with `tensorMap`.
The graph is the right place to describe how data moves between steps.
Changing client code would hide a server-side integration detail outside the platform.
Changing the model artifact may be appropriate later, but explicit tensor mapping is the fastest clear fix.
</details>

<details>
<summary>A shared MLServer farm shows random p95 latency spikes after a large text model was added. What is your diagnostic path?</summary>

Check whether the large model's `memory` estimate is realistic and whether overcommit is causing eviction and reload behavior.
Look at Agent logs, model load events, and latency correlation by model name.
Scaling replicas may help concurrency, but it can also multiply load and memory costs if each replica loads the large model.
The cleaner fix may be a separate server capability for large NLP models.
</details>

## Hands-On Exercise

You will build a progressive Seldon Core 2 deployment on a kind cluster.
The final task combines two model variants, an A/B `Experiment`, a two-step pipeline, and an Alibi explainer.
The commands assume Docker, kind, Helm, kubectl, and curl are installed.
Seldon examples commonly use the `seldon-mesh` namespace.

Run this once before the tasks:

```bash
alias k=kubectl
```

### Task 1: Install Seldon Core 2 on kind and Verify CRDs

Theory first: installation is split because cluster APIs, control-plane setup, namespace runtime, and default servers have different lifecycles.
CRDs are cluster-wide.
Runtime components are namespace-scoped.
Servers are model-serving capacity.

<details>
<summary>Solution</summary>

```bash
kind create cluster --name seldon-core2
k cluster-info --context kind-seldon-core2

helm repo add seldon-charts https://seldonio.github.io/helm-charts/
helm repo update

k create namespace seldon-system
k create namespace seldon-mesh

helm upgrade --install seldon-core-v2-crds seldon-charts/seldon-core-v2-crds \
  --namespace seldon-system

helm upgrade --install seldon-core-v2-setup seldon-charts/seldon-core-v2-setup \
  --namespace seldon-system \
  --wait

helm upgrade --install seldon-core-v2-runtime seldon-charts/seldon-core-v2-runtime \
  --namespace seldon-mesh \
  --wait

helm upgrade --install seldon-core-v2-servers seldon-charts/seldon-core-v2-servers \
  --namespace seldon-mesh \
  --wait
```

Expected output snippets:

```text
Release "seldon-core-v2-crds" has been upgraded
Release "seldon-core-v2-setup" has been upgraded
Release "seldon-core-v2-runtime" has been upgraded
Release "seldon-core-v2-servers" has been upgraded
```

Verify resources:

```bash
k api-resources | grep -E 'models|servers|pipelines|experiments|seldonruntimes'
k get seldonruntime,servers -n seldon-mesh
```

Expected output snippet:

```text
models           mlops.seldon.io/v1alpha1
servers          mlops.seldon.io/v1alpha1
pipelines        mlops.seldon.io/v1alpha1
experiments      mlops.seldon.io/v1alpha1
```

- [ ] A kind cluster named `seldon-core2` exists.
- [ ] Seldon CRDs are visible through `k api-resources`.
- [ ] At least one MLServer or Triton `Server` is visible in `seldon-mesh`.

</details>

### Task 2: Deploy a Simple sklearn Model with `Model` and `Server`

Theory first: the `Model` declares the artifact and requirement.
The `Server` declares runtime capability.
If a default MLServer already exists, you can use it.
This task creates an explicit server so the scheduling relationship is visible.

<details>
<summary>Solution</summary>

```bash
cat > /tmp/seldon-server-sklearn.yaml <<'EOF'
apiVersion: mlops.seldon.io/v1alpha1
kind: Server
metadata:
  name: mlserver-sklearn
  namespace: seldon-mesh
spec:
  serverConfig: mlserver
  extraCapabilities:
    - sklearn
EOF

k apply -f /tmp/seldon-server-sklearn.yaml
```

```bash
cat > /tmp/seldon-model-iris-a.yaml <<'EOF'
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: iris-a
  namespace: seldon-mesh
spec:
  storageUri: "gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn"
  requirements:
    - sklearn
  memory: 100Ki
EOF

k apply -f /tmp/seldon-model-iris-a.yaml
k wait --for condition=ready --timeout=300s model/iris-a -n seldon-mesh
```

Expected output snippet:

```text
server.mlops.seldon.io/mlserver-sklearn created
model.mlops.seldon.io/iris-a created
model.mlops.seldon.io/iris-a condition met
```

Send an inference request.
The exact ingress service depends on your Seldon installation and service mesh.
For a local installation, port-forward Envoy or the ingress gateway that fronts Seldon.

```bash
k port-forward -n seldon-mesh svc/seldon-mesh 8080:80 >/tmp/seldon-port-forward.log 2>&1 &
PF_PID=$!
sleep 3

curl -s http://127.0.0.1:8080/v2/models/iris-a/infer \
  -H "Host: seldon-mesh.inference.seldon" \
  -H "Content-Type: application/json" \
  -H "Seldon-Model: iris-a" \
  -d '{
    "inputs": [
      {
        "name": "predict",
        "shape": [1, 4],
        "datatype": "FP32",
        "data": [[1, 2, 3, 4]]
      }
    ]
  }'

kill "${PF_PID}"
```

Expected output snippet:

```json
{"model_name":"iris-a_1","outputs":[{"name":"predict","shape":[1,1],"datatype":"INT64","data":[2]}]}
```

- [ ] `iris-a` reaches Ready.
- [ ] The inference request returns an Open Inference Protocol response.
- [ ] The response contains an `outputs` array.

</details>

### Task 3: Deploy a Second Model Variant

Theory first: a variant is not always a new framework.
It can be a new artifact version, a different runtime, or a different preprocessing assumption.
For this exercise, use a second model name so traffic splitting and graph composition are easy to see.

<details>
<summary>Solution</summary>

```bash
cat > /tmp/seldon-model-iris-b.yaml <<'EOF'
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: iris-b
  namespace: seldon-mesh
spec:
  storageUri: "gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn"
  requirements:
    - sklearn
  memory: 100Ki
EOF

k apply -f /tmp/seldon-model-iris-b.yaml
k wait --for condition=ready --timeout=300s model/iris-b -n seldon-mesh
k get models -n seldon-mesh
```

Expected output snippet:

```text
model.mlops.seldon.io/iris-b created
model.mlops.seldon.io/iris-b condition met
NAME     READY
iris-a   True
iris-b   True
```

Test the second variant:

```bash
k port-forward -n seldon-mesh svc/seldon-mesh 8080:80 >/tmp/seldon-port-forward.log 2>&1 &
PF_PID=$!
sleep 3

curl -s http://127.0.0.1:8080/v2/models/iris-b/infer \
  -H "Host: seldon-mesh.inference.seldon" \
  -H "Content-Type: application/json" \
  -H "Seldon-Model: iris-b" \
  -d '{
    "inputs": [
      {
        "name": "predict",
        "shape": [1, 4],
        "datatype": "FP32",
        "data": [[1, 2, 3, 4]]
      }
    ]
  }'

kill "${PF_PID}"
```

Expected output snippet:

```json
{"model_name":"iris-b_1","outputs":[{"name":"predict","shape":[1,1],"datatype":"INT64","data":[2]}]}
```

- [ ] `iris-b` reaches Ready.
- [ ] Both variants are visible as `Model` resources.
- [ ] Each model can be called independently.

</details>

### Task 4: Create a Two-Step Pipeline

Theory first: this exercise chains two model calls to teach graph mechanics.
In a real application, the first step would often be a preprocessor and the second step would be a predictor.
Using two compatible demo models keeps the focus on Seldon routing rather than model training.

<details>
<summary>Solution</summary>

```bash
cat > /tmp/seldon-pipeline-iris-chain.yaml <<'EOF'
apiVersion: mlops.seldon.io/v1alpha1
kind: Pipeline
metadata:
  name: iris-chain
  namespace: seldon-mesh
spec:
  steps:
    - name: iris-a
    - name: iris-b
      inputs:
        - iris-a.outputs.predict
      tensorMap:
        iris-a.outputs.predict: predict
  output:
    steps:
      - iris-b
EOF

k apply -f /tmp/seldon-pipeline-iris-chain.yaml
k wait --for condition=ready --timeout=300s pipeline/iris-chain -n seldon-mesh
```

Expected output snippet:

```text
pipeline.mlops.seldon.io/iris-chain created
pipeline.mlops.seldon.io/iris-chain condition met
```

Call the pipeline endpoint:

```bash
k port-forward -n seldon-mesh svc/seldon-mesh 8080:80 >/tmp/seldon-port-forward.log 2>&1 &
PF_PID=$!
sleep 3

curl -s http://127.0.0.1:8080/v2/models/iris-chain/infer \
  -H "Host: seldon-mesh.inference.seldon" \
  -H "Content-Type: application/json" \
  -H "Seldon-Model: iris-chain.pipeline" \
  -d '{
    "inputs": [
      {
        "name": "predict",
        "shape": [1, 4],
        "datatype": "FP32",
        "data": [[1, 2, 3, 4]]
      }
    ]
  }'

kill "${PF_PID}"
```

Expected output snippet:

```json
{"model_name":"","outputs":[{"name":"predict","shape":[1,1],"datatype":"INT64","data":[2]}]}
```

- [ ] `iris-chain` reaches Ready.
- [ ] The request uses `Seldon-Model: iris-chain.pipeline`.
- [ ] The response comes from the pipeline output step.

</details>

### Task 5: Create an 80/20 Experiment Between Model Variants

Theory first: an `Experiment` makes traffic policy visible.
An 80/20 split is a common first canary shape because it limits blast radius while still producing enough variant traffic to inspect.
Do not declare success by traffic percentage alone.
You need business and model metrics before increasing the split.

<details>
<summary>Solution</summary>

```bash
cat > /tmp/seldon-experiment-iris-ab.yaml <<'EOF'
apiVersion: mlops.seldon.io/v1alpha1
kind: Experiment
metadata:
  name: iris-ab
  namespace: seldon-mesh
spec:
  default: iris-a
  candidates:
    - name: iris-a
      weight: 80
    - name: iris-b
      weight: 20
EOF

k apply -f /tmp/seldon-experiment-iris-ab.yaml
k wait --for condition=ready --timeout=300s experiment/iris-ab -n seldon-mesh
k get experiment iris-ab -n seldon-mesh
```

Expected output snippet:

```text
experiment.mlops.seldon.io/iris-ab created
experiment.mlops.seldon.io/iris-ab condition met
```

Send repeated requests and inspect route headers:

```bash
k port-forward -n seldon-mesh svc/seldon-mesh 8080:80 >/tmp/seldon-port-forward.log 2>&1 &
PF_PID=$!
sleep 3

for i in $(seq 1 10); do
  curl -s -D - http://127.0.0.1:8080/v2/models/iris-a/infer \
    -H "Host: seldon-mesh.inference.seldon" \
    -H "Content-Type: application/json" \
    -H "Seldon-Model: iris-a" \
    -d '{
      "inputs": [
        {
          "name": "predict",
          "shape": [1, 4],
          "datatype": "FP32",
          "data": [[1, 2, 3, 4]]
        }
      ]
    }' | grep -E 'x-seldon-route|model_name|outputs' || true
done

kill "${PF_PID}"
```

Expected output snippet:

```text
x-seldon-route: ...
{"model_name":"iris-a_1",...}
{"model_name":"iris-b_1",...}
```

- [ ] `iris-ab` reaches Ready.
- [ ] The experiment references both model variants.
- [ ] Repeated requests show routing evidence for the split or route headers.

</details>

### Task 6: Apex Task: Two Variants, A/B Experiment, Pipeline, and Alibi Explainer

Theory first: the final task combines the serving pieces you would use in a real rollout.
The pipeline gives a server-side graph.
The experiment splits traffic between variants.
The explainer provides a governed explanation endpoint for one model.
These are separate resources because rollout, routing, and explanation have different lifecycles.

<details>
<summary>Solution</summary>

Apply the explainer model:

```bash
cat > /tmp/seldon-model-iris-a-explainer.yaml <<'EOF'
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: iris-a-explainer
  namespace: seldon-mesh
spec:
  storageUri: "gs://seldon-models/scv2/samples/mlserver_1.5.0/income-sklearn/anchor-explainer"
  explainer:
    type: anchor_tabular
    modelRef: iris-a
EOF

k apply -f /tmp/seldon-model-iris-a-explainer.yaml
k wait --for condition=ready --timeout=300s model/iris-a-explainer -n seldon-mesh
```

Expected output snippet:

```text
model.mlops.seldon.io/iris-a-explainer created
model.mlops.seldon.io/iris-a-explainer condition met
```

Create a pipeline that represents the production path for variant A.
In real life, the first step would be a preprocessor model.
Here, the two-step chain is kept small enough for a local cluster.

```bash
cat > /tmp/seldon-pipeline-iris-a-production.yaml <<'EOF'
apiVersion: mlops.seldon.io/v1alpha1
kind: Pipeline
metadata:
  name: iris-a-production
  namespace: seldon-mesh
spec:
  steps:
    - name: iris-a
    - name: iris-b
      inputs:
        - iris-a.outputs.predict
      tensorMap:
        iris-a.outputs.predict: predict
  output:
    steps:
      - iris-b
EOF

k apply -f /tmp/seldon-pipeline-iris-a-production.yaml
k wait --for condition=ready --timeout=300s pipeline/iris-a-production -n seldon-mesh
```

Now create a pipeline experiment between two production shapes.
This example uses one pipeline and one already deployed model as separate experiment resources only if your installed version allows mixed routing through model endpoints.
If your version requires homogeneous resource type, keep this as a model experiment with `iris-a` and `iris-b`, and run the pipeline separately.
The more common Core 2 production pattern is homogeneous: model experiment or pipeline experiment.

```bash
cat > /tmp/seldon-experiment-iris-final.yaml <<'EOF'
apiVersion: mlops.seldon.io/v1alpha1
kind: Experiment
metadata:
  name: iris-final-ab
  namespace: seldon-mesh
spec:
  default: iris-a
  candidates:
    - name: iris-a
      weight: 80
    - name: iris-b
      weight: 20
EOF

k apply -f /tmp/seldon-experiment-iris-final.yaml
k wait --for condition=ready --timeout=300s experiment/iris-final-ab -n seldon-mesh
```

Retrieve an Alibi explanation.
The path and response shape vary by installed explainer runtime and model artifact.
Use the Seldon model header to route to the explainer model.

```bash
k port-forward -n seldon-mesh svc/seldon-mesh 8080:80 >/tmp/seldon-port-forward.log 2>&1 &
PF_PID=$!
sleep 3

curl -s http://127.0.0.1:8080/v2/models/iris-a-explainer/infer \
  -H "Host: seldon-mesh.inference.seldon" \
  -H "Content-Type: application/json" \
  -H "Seldon-Model: iris-a-explainer" \
  -d '{
    "inputs": [
      {
        "name": "predict",
        "shape": [1, 4],
        "datatype": "FP32",
        "data": [[1, 2, 3, 4]]
      }
    ]
  }'

kill "${PF_PID}"
```

Expected output snippet:

```json
{"meta":{"name":"iris-a-explainer"},"data":{"anchor":["feature condition"],"precision":0.95}}
```

Validate the complete state:

```bash
k get models,pipelines,experiments,servers -n seldon-mesh
```

Expected output snippet:

```text
model.mlops.seldon.io/iris-a             True
model.mlops.seldon.io/iris-b             True
model.mlops.seldon.io/iris-a-explainer   True
pipeline.mlops.seldon.io/iris-a-production True
experiment.mlops.seldon.io/iris-final-ab True
```

- [ ] Two model variants are deployed and ready.
- [ ] A two-step pipeline is deployed and ready.
- [ ] An 80/20 `Experiment` is deployed and ready.
- [ ] An Alibi explainer model is attached to `iris-a`.
- [ ] A sample explanation request returns explanation-shaped output.

</details>

## Next Module

Next: Module 9.10 — BentoML: Unified Model Packaging and Deployment

## Sources

- https://docs.seldon.ai/seldon-core-2/
- https://docs.seldon.ai/seldon-core-2/about/architecture
- https://docs.seldon.ai/seldon-core-2/installation/installation
- https://docs.seldon.ai/seldon-core-2/installation/test-installation
- https://docs.seldon.ai/seldon-core-2/installation/advanced-configurations/seldonruntime
- https://docs.seldon.ai/seldon-core-2/user-guide/servers
- https://docs.seldon.ai/seldon-core-2/user-guide/models
- https://docs.seldon.ai/seldon-core-2/user-guide/models/mms
- https://docs.seldon.ai/seldon-core-2/user-guide/pipelines
- https://docs.seldon.ai/seldon-core-2/user-guide/experiment
- https://docs.seldon.ai/seldon-core-2/user-guide/data-science-monitoring/drift
- https://docs.seldon.ai/seldon-core-2/user-guide/data-science-monitoring/outlier
- https://docs.seldon.ai/seldon-core-2/v2.10/user-guide/data-science-monitoring/explainers
- https://docs.seldon.ai/seldon-core-2/user-guide/operational-monitoring/observability
- https://docs.seldon.ai/alibi-explain
- https://docs.seldon.ai/alibi-explain/overview/algorithms
- https://docs.seldon.ai/alibi-detect/algorithms
- https://github.com/SeldonIO/seldon-core
- https://github.com/SeldonIO/alibi
- https://github.com/SeldonIO/alibi-detect
- https://github.com/SeldonIO/helm-charts
- https://kserve.github.io/website/docs/concepts/resources/inferencegraph
- https://kserve.github.io/website/docs/model-serving/inferencegraph/overview
