---
title: "Private MLOps Platform"
description: "Architecting and operating a bare-metal MLOps stack for model tracking, feature stores, and inference."
slug: on-premises/ai-ml-infrastructure/module-9.4-private-mlops-platform
sidebar:
  order: 94
---

# Private MLOps Platform

Operating machine learning infrastructure on bare metal requires replacing managed cloud services with self-hosted, scalable equivalents. A production-grade MLOps platform on Kubernetes is not a single monolithic application; it is a loosely coupled ecosystem of stateful data stores, stateless API servers, and workflow orchestrators.

## Why This Module Matters

In early 2024, a major retail analytics firm named Zephyr Analytics suffered a catastrophic financial loss exceeding $5.2 million over a single holiday weekend. Their cloud-managed ML pipelines, relying on a fully managed feature store, silently failed due to an unannounced and unpinned API deprecation pushed by their cloud vendor. The models began serving predictions using stale, fallback data, leading to massive mispricing of inventory across their entire European market. The incident was not caught by standard Application Performance Monitoring tools because the managed service endpoints returned HTTP 200 OK statuses, completely masking the underlying data drift and schema resolution failures.

Following this disaster, the engineering organization made a strategic pivot: they migrated their entire predictive infrastructure to a bare-metal Kubernetes v1.35 environment. By utilizing open-source tools like MLflow, Feast, and KServe, they regained absolute control over their data plane and model execution environments. This transition required significant upfront engineering to replace managed components, but it eliminated vendor lock-in, reduced their monthly compute bill by over sixty percent, and most importantly, provided deterministic control over every layer of their MLOps stack. 

When you build a private MLOps platform, you are taking responsibility for the statefulness, the networking, and the lifecycle of the models. You are no longer renting an abstraction; you are operating the engine. This module equips you with the knowledge to architect, deploy, secure, and troubleshoot that engine from the ground up, ensuring you never fall victim to black-box vendor failures.

## Learning Outcomes

*   **Architect** a modular MLOps stack on bare-metal Kubernetes utilizing self-hosted components.
*   **Deploy** and configure MLflow with a highly available PostgreSQL backend and MinIO artifact store.
*   **Implement** Feast as a bare-metal feature store utilizing Redis for online serving and PostgreSQL for offline batching.
*   **Design** model serving pipelines using KServe for A/B testing and canary rollouts.
*   **Diagnose** common stateful ML component failures, including artifact sync errors and inference memory exhaustion.
*   **Evaluate** orchestration tools like Kubeflow Pipelines and Argo Workflows for complex ML lifecycle management.

## Architecting the Private MLOps Stack

A functional MLOps platform handles four distinct lifecycles: Data, Experimentation, Orchestration, and Serving. On bare metal, you must provision the underlying storage (block, file, and object) and routing infrastructure that managed services typically abstract away. Without a solid foundation, the higher-level machine learning tools will suffer from extreme latency and data corruption.

### Cloud to Bare Metal Mapping

When moving away from managed environments, engineers must map cloud primitives to their open-source equivalents. Teams migrating from comprehensive platforms like AWS SageMaker or Google Cloud's BigQuery must fundamentally rethink their data pipelines to utilize open-source bare-metal equivalents.

| Managed Cloud Service (AWS/GCP) | Bare Metal Kubernetes Equivalent | Primary Storage Backend |
| :--- | :--- | :--- |
| S3 / GCS | MinIO / Ceph Object Gateway | Physical NVMe / HDD |
| SageMaker Experiments / Vertex ML Metadata | MLflow Tracking Server | PostgreSQL + MinIO |
| Vertex Feature Store / SageMaker Feature Store | Feast | Redis (Online) + Postgres (Offline)|
| SageMaker Pipelines / Vertex Pipelines | Kubeflow Pipelines (KFP) / Argo | MinIO (Artifacts) + MySQL |
| SageMaker Endpoints / Vertex Prediction | KServe / Seldon Core | Knative / Istio |

To visualize this transition logically, consider the flow mapping from proprietary to open ecosystems:

```mermaid
flowchart LR
    subgraph Proprietary Cloud Services
        S3[S3 / GCS]
        Sagemaker[SageMaker Experiments]
        VertexFS[Vertex Feature Store]
        SagemakerPipelines[SageMaker Pipelines]
        SagemakerEndpoints[SageMaker Endpoints]
    end
    subgraph Bare Metal Equivalents
        MinIO[MinIO / Ceph]
        MLflow[MLflow Tracking Server]
        Feast[Feast]
        KFP[Kubeflow Pipelines / Argo]
        KServe[KServe / Seldon Core]
    end
    S3 -.->|Maps to| MinIO
    Sagemaker -.->|Maps to| MLflow
    VertexFS -.->|Maps to| Feast
    SagemakerPipelines -.->|Maps to| KFP
    SagemakerEndpoints -.->|Maps to| KServe
```

### System Architecture

The following diagram illustrates how these open-source components interact within a Kubernetes cluster to form a cohesive, production-ready platform. 

```mermaid
flowchart TD
    subgraph Data Layer
        DS[Object Storage / MinIO]
        DB[(PostgreSQL)]
        Cache[(Redis)]
    end

    subgraph Feature Engineering
        Feast[Feast Registry]
        Feast -->|Materialize| Cache
        Feast -->|Historical| DB
    end

    subgraph Experimentation
        MLflow[MLflow Tracking Server]
        MLflow -->|Metadata| DB
        MLflow -->|Models/Artifacts| DS
    end

    subgraph Orchestration
        Argo[Argo Workflows / KFP]
        Argo -->|Fetch Data| Feast
        Argo -->|Log Metrics| MLflow
    end

    subgraph Serving
        KServe[KServe Inference]
        Istio[Istio Ingress]
        Istio --> KServe
        KServe -->|Pull Model| DS
    end
```

> **Pause and predict**: Looking at the architecture diagram, what happens to the Serving layer if the MLflow Tracking Server goes offline? Predict the impact on real-time inference. 
> *Answer*: Nothing. The Serving layer (KServe) pulls models directly from Object Storage (MinIO). MLflow is used for experimentation and metadata tracking, not for serving live traffic. This decoupling is a critical design principle in robust MLOps platforms.

## Data Versioning on Bare Metal

Machine learning models are functions of the code and the data they are trained on. Versioning data on bare metal requires an object storage backend and a tracking layer. For bare metal, MinIO is the standard choice. The MinIO server is licensed under GNU AGPLv3, while its commercial enterprise offering is called AIStor.

### DVC (Data Version Control)

DVC operates directly on top of Git. It tracks large datasets by storing metadata pointers (`.dvc` files) in Git while pushing the actual payload to MinIO. The latest stable version of DVC is 3.67.1, released under the Apache 2.0 license.
*   **Pros:** Requires zero additional infrastructure beyond your Git server and an S3-compatible endpoint. It leverages the developer's existing Git workflow seamlessly.
*   **Cons:** Client-side heavy. Engineers must configure their local environment with S3 credentials, which can become an operational burden as the team scales across many projects.

### LakeFS

LakeFS provides Git-like operations (branch, commit, merge, revert) directly over object storage via an API proxy. 
*   **Pros:** Server-side implementation. Zero-copy branching (branching a ten-terabyte dataset takes milliseconds and consumes no extra storage).
*   **Cons:** Requires running a dedicated LakeFS PostgreSQL database and API server on the cluster. Applications must use the LakeFS S3 gateway endpoint instead of the direct MinIO endpoint.

:::tip
For smaller teams, DVC is sufficient. Once you exceed 50TB of training data or require strict isolation between concurrent training runs accessing the same dataset, deploy LakeFS.
:::

For massive relational data warehousing on-prem, teams often rely on Greenplum or distributed PostgreSQL extensions, treating them as equivalent to cloud-native BigQuery.

## Feature Stores: Feast on Kubernetes

A feature store solves a fundamental problem: bridging the gap between historical data (used for batch training) and real-time data (used for millisecond-latency inference serving). It ensures that the data features used for training exactly match the features used for serving, preventing training-serving skew. 

Feast is a prominent open-source choice. Currently at v0.62.0, Feast is licensed under Apache 2.0. Notably, Feast is not a CNCF project, operating independently as an open standard for feature engineering.

Feast relies on two storage tiers:
1.  **Offline Store:** Used for batch training. On bare metal, this is typically Apache Parquet files stored in MinIO or tables in a centralized PostgreSQL instance. It stores the historical data required to generate training datasets.
2.  **Online Store:** Used for low-latency inference lookups. On bare metal, this is exclusively Redis. It serves only the latest real-time data points needed by live models.

### Feast Configuration (`feature_store.yaml`)

To run Feast on bare metal, you must abandon cloud-native integrations and point the registry and stores to internal cluster endpoints via your `feature_store.yaml` file.

```yaml
project: on_prem_mlops
registry:
  registry_type: sql
  path: postgresql://feast-user:secret@feast-postgres.mlops.svc.cluster.local:5432/feast_registry
provider: local
offline_store:
  type: file
online_store:
  type: redis
  connection_string: feast-redis-master.mlops.svc.cluster.local:6379
```

When deploying Feast materialization jobs, use Kubernetes CronJobs that execute `feast materialize` rather than relying on external workflow orchestrators. This keeps the data movement logic tightly bound to the feature definitions.

### Why Two Stores? The Read-Pattern Argument

The split between PostgreSQL (offline) and Redis (online) is the single most important design decision in any feature-store deployment, and it follows directly from a quantitative property of each store rather than from convention. Training jobs read **billions of rows in a single sequential scan**, accept latencies measured in minutes, and never read the same row twice in a tight loop; inference services read **one row per request** keyed by entity ID, must respond within milliseconds, and re-read the same hot keys thousands of times per second. No single storage engine optimises both workloads. PostgreSQL with appropriate indexes and a columnar extension can serve the offline scan economically — its B-tree and BRIN indexes are well-tuned for range scans over partitioned event tables — but it would buckle under one hundred thousand point queries per second from a busy fraud-detection model. Redis serves the point query at sub-millisecond latency from RAM, but storing a year of historical events in Redis would cost tens of times more than the PostgreSQL equivalent and provide no analytical query capability beyond `GET key`.

A second consequence falls out of the same split: **the materialization job is the only writer that crosses the boundary**. Training writes only to the offline store (or to MinIO Parquet files registered as offline sources); the inference path reads only from the online store and never queries Postgres directly. This one-way data flow is what guarantees training-serving consistency: as long as the materialization job runs correctly, the row a model sees at serving time is *byte-identical* to the row it was trained on. Teams that try to "simplify" by reading directly from Postgres at serving time inevitably hit two failure modes within months — first, latency spikes when Postgres autovacuum runs; second, training-serving skew when an analyst alters a Postgres view that the offline path uses but the online path does not.

A third consequence governs disaster recovery. Postgres holds the system-of-record historical features and **must be backed up to an off-cluster location** (typically WAL-E or pgBackRest streaming to a separate MinIO tenancy or external S3). Redis is intentionally treated as a recoverable cache — if the entire Redis StatefulSet is destroyed, the operator runs `feast materialize-incremental $(date -d '1 day ago' -Iseconds)` and the online store rebuilds from Postgres in minutes. Keeping this asymmetry explicit in your runbook removes the temptation to over-engineer Redis HA (Redis Sentinel + AOF persistence + cross-DC replication) for what is, by design, a derived view.

Finally, this design generalises: any feature store you evaluate (Tecton, Hopsworks, Vertex Feature Store) implements the same two-tier pattern under the hood, and the on-prem decision reduces to "which key-value store serves the online tier and which OLAP-friendly database serves the offline tier?" Common alternatives include DragonflyDB or KeyDB instead of Redis when license terms matter, or ClickHouse instead of Postgres when feature volume crosses ten billion rows. The architectural shape — single materialization writer, dual reader paths, asymmetric DR posture — does not change.

## Experiment Tracking: MLflow Architecture

MLflow is hosted under the LF AI & Data Foundation (it is not a CNCF project) and is Apache 2.0 licensed. The current stable release is in major version 3 (v3.11.1), moving well past the legacy v2 architecture. MLflow officially supports Kubernetes as a backend for running MLflow Projects, allowing it to build Docker images and submit Kubernetes Jobs seamlessly without external orchestrators.

MLflow requires a carefully architected deployment to prevent data loss and ensure high availability. By default, running `mlflow server` writes data to the local container filesystem, which is immediately lost upon pod termination.

A production MLflow deployment requires three distinct components:
1.  **Tracking Server:** A stateless Python API server handling HTTP requests from clients.
2.  **Backend Store:** An external SQL database storing parameters, metrics, and run metadata.
3.  **Artifact Store:** An S3-compatible bucket storing massive serialized models and deep learning checkpoints.

### Critical Environment Variables

When running MLflow on Kubernetes with MinIO, the tracking server and client pods must be configured to communicate with the S3 API directly. You must inject these variables securely.

```kubernetes
env:
  - name: MLFLOW_S3_ENDPOINT_URL
    value: "http://minio.storage.svc.cluster.local:9000"
  - name: AWS_ACCESS_KEY_ID
    valueFrom:
      secretKeyRef:
        name: minio-credentials
        key: access-key
  - name: AWS_SECRET_ACCESS_KEY
    valueFrom:
      secretKeyRef:
        name: minio-credentials
        key: secret-key
```

> **Stop and think**: Why do we inject AWS credentials when communicating with a local MinIO instance? MinIO implements the AWS S3 API protocol exactly, so standard AWS SDKs (like `boto3`) require these standard environment variables to authenticate, even if the endpoint is a local Kubernetes service running down the hall.

### Backend Store Tradeoffs: Why PostgreSQL Wins for MLflow

MLflow supports four backend store types — local filesystem, SQLite, PostgreSQL, and MySQL — and the choice is consequential enough to warrant explicit reasoning. The local filesystem backend is acceptable only for solo experimentation: there is no concurrency control beyond OS-level file locks, and `mlflow.log_metric` calls from two pods racing for the same run will silently corrupt the run's `metrics/` directory. SQLite removes that race because it serialises writes through a single file lock, but the same lock makes it unusable above roughly twenty concurrent writers; a Katib hyperparameter sweep with two hundred parallel trials will see sustained `database is locked` errors within minutes.

PostgreSQL is the production default for three measurable reasons. First, its MVCC implementation lets hundreds of concurrent training pods log metrics without blocking each other, because each writer sees its own snapshot of the database; the `runs.update_at` timestamp updates without read-write contention. Second, MLflow's schema relies on foreign keys and JSON-typed columns for tags, both of which Postgres handles natively without extension; MySQL works but requires care around `utf8mb4` character sets to store non-ASCII parameter values. Third, the operational ecosystem around Postgres on Kubernetes is mature — operators like CloudNativePG and Zalando's `postgres-operator` provide point-in-time recovery, streaming replication, and connection-pooling integration with PgBouncer that the MySQL ecosystem matches less consistently.

The connection-pool sizing rule that catches most teams off-guard is worth memorising. MLflow's Python client opens **one PostgreSQL connection per active run**, and a Katib sweep with one hundred parallel trials therefore needs at minimum one hundred connections plus a margin for the tracking server's own UI traffic. Postgres defaults to `max_connections = 100`. A naive deployment will refuse new connections halfway through the sweep with a cryptic `FATAL: sorry, too many clients already`. The fix is to deploy PgBouncer in transaction-pooling mode in front of Postgres and route MLflow's `--backend-store-uri` through it; PgBouncer multiplexes thousands of client connections onto a small fixed pool of backend connections, which is exactly the workload pattern MLflow generates.

### Why MinIO over Ceph for the Small-Cluster Case

The reflexive on-prem answer for "S3-compatible storage" is Ceph via the Rook operator, but that choice is wrong for most MLOps deployments below roughly fifty terabytes of artifacts. MinIO is a **single-binary object server** that stores data on the host filesystem with optional erasure coding across drives; a four-node MinIO cluster on commodity NVMe hardware consistently delivers single-digit-millisecond `GET` latencies and is operationally trivial to deploy via the Bitnami chart used in this module's lab. Ceph, by contrast, is a **distributed storage system** that provides block (RBD), file (CephFS), and object (RGW) interfaces simultaneously, with a CRUSH map, monitors, OSDs, and an MDS to coordinate. Operating Ceph competently is a full-time discipline; the cluster requires a minimum of three monitor nodes, careful network sizing (separate front-end and back-end networks for OSD recovery traffic), and operational familiarity with PG balancing and scrubbing.

The break-even point depends on workload, but a useful rule of thumb is: stay on MinIO until at least one of these is true — total artifact volume exceeds fifty terabytes, multi-region replication is a hard requirement, or the same cluster must already host Ceph for block storage (in which case running RGW on top of the existing OSDs costs nothing extra). Below that threshold, MinIO's operational simplicity dominates: a single SRE can confidently take MinIO from zero to production in an afternoon, while Ceph will require weeks of capacity planning, network tuning, and failover drills before it is trustworthy enough to back a model registry. Teams that pick Ceph "because it scales further" without first hitting MinIO's limits typically discover that the unfamiliar failure modes — placement-group degradation, slow `osd_op_complaint_time` warnings, MDS rank failures — pull more SRE time than they ever save.

The exception worth flagging: if the cluster is *already* running Ceph for stateful workloads (Postgres PVCs, Redis AOF, or RWX volumes for shared notebook home directories), enabling RGW costs essentially nothing and centralises object storage on the same operational substrate. In that environment, MinIO becomes redundant infrastructure. The decision is contextual, not categorical.

:::caution
**Boto3 Connection Timeouts**
When configuring MLflow client pods to talk to MinIO, you must explicitly set connection timeouts in boto3. If `MLFLOW_S3_ENDPOINT_URL` is inaccessible or misconfigured, boto3 defaults to a high-latency timeout with multiple retries, causing training pods to hang silently for over five minutes before finally failing. Always set `AWS_METADATA_SERVICE_TIMEOUT=1` and `AWS_MAX_ATTEMPTS=2` to ensure the pod fails fast and frees up cluster resources.
:::

## Orchestration & Pipelines

Orchestrating machine learning workflows requires handling Directed Acyclic Graphs (DAGs) of tasks securely and efficiently. A typical training pipeline fans out across data validation, feature materialization, model training, evaluation, and conditional registration — each step running in its own pod, each producing artifacts that downstream steps must locate deterministically. Without an orchestrator that understands artifact passing, retry semantics, and pod-level resource isolation, teams end up gluing pipelines together with bash scripts that silently drop failures.

### A Canonical Training DAG

Most production ML pipelines on bare metal share the same skeleton regardless of which orchestrator is chosen. Visualizing the DAG before reading any YAML helps you reason about where failures concentrate and which steps need the most generous retry budgets.

```mermaid
flowchart LR
    A[Validate Schema<br/>Great Expectations] --> B[Materialize Features<br/>Feast]
    B --> C[Train Model<br/>PyTorch / XGBoost]
    C --> D[Evaluate Holdout<br/>scikit-learn]
    D -->|metric &gt; threshold| E[Register Model<br/>MLflow]
    D -->|metric &le; threshold| F[Notify Owner<br/>Alertmanager]
    E --> G[Promote to Staging<br/>KServe canary]
```

Steps A and B are I/O bound and fail most often due to upstream data drift; they should retry aggressively (up to 5 times with exponential backoff). Steps C and D are compute bound on GPU nodes; retrying a 4-hour training run blindly burns expensive cycles, so retry policy here should be `OnFailure` with a strict count of 1 and clear escalation to a human. Step E is a transactional write to MLflow and PostgreSQL; idempotency must be guaranteed by hashing the model artifact rather than the wall-clock timestamp, otherwise a partial failure leaves duplicate registry entries.

### Kubeflow & KFP
Kubeflow is a CNCF Incubating project (accepted July 2023, not yet Graduated), with its latest stable release at v1.10.0. Kubeflow Pipelines (KFP) SDK v1 is frozen at v1.8.22; SDK v2 (v2.16.0) is the only actively developed version. Crucially, the KFP v2 SDK compiles pipelines to a backend-agnostic IR YAML format, moving away from the Argo Workflow YAML dependency of v1.

For model training, Kubeflow Trainer v2.2 supports PyTorch, JAX, XGBoost, MPI, and Flux distributed training under a single unified `TrainJob` CRD. Hyperparameter optimization is handled by Katib (v0.19.0), which supports algorithms including grid search, random search, Bayesian optimization, Hyperband, TPE, multivariate-TPE, CMA-ES, Sobol, and Population Based Training (PBT).

### Argo & Tekton
Argo Workflows maintains both a v4.x branch (v4.0.4) and a v3.x LTS branch (v3.7.13) simultaneously, and the Argo project as a whole is a CNCF Graduated project. Alternatively, Tekton Pipelines (latest v1.11.0) is a CNCF Incubating project as of March 2026, having moved from the Continuous Delivery Foundation.

A minimal Argo Workflow that mirrors the canonical DAG above looks like this. Note the explicit `artifacts` block that hands the trained model from the `train` step to the `evaluate` step via the cluster's MinIO bucket — without this declaration, Argo would not know how to wire pod outputs into pod inputs.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: train-fraud-model-
  namespace: mlops
spec:
  entrypoint: pipeline
  artifactRepositoryRef:
    configMap: artifact-repositories
    key: minio-mlops
  templates:
  - name: pipeline
    dag:
      tasks:
      - name: validate
        template: ge-validate
      - name: materialize
        template: feast-materialize
        dependencies: [validate]
      - name: train
        template: pytorch-train
        dependencies: [materialize]
      - name: evaluate
        template: holdout-eval
        dependencies: [train]
        arguments:
          artifacts:
          - name: model
            from: "{{tasks.train.outputs.artifacts.model}}"
  - name: pytorch-train
    retryStrategy:
      limit: "1"
      retryPolicy: "OnFailure"
    container:
      image: registry.mlops.svc.cluster.local/trainer:1.4
      resources:
        limits:
          nvidia.com/gpu: "1"
    outputs:
      artifacts:
      - name: model
        path: /workspace/model.pt
```

The `retryStrategy` is intentionally tight on GPU steps: silently retrying a failed training job consumes hours of accelerator time and almost never succeeds the second time without human intervention. The `arguments.artifacts` block uses Argo's `from:` syntax to reference an upstream task's output, which the controller resolves to a MinIO presigned URL at scheduling time.

#### From High-Level Template to Compiled IR

The YAML above is the *authored* form — what a platform engineer types into version control. What actually runs on the cluster is the *compiled* form: the Argo controller takes the templates, resolves all `{{tasks.*.outputs.*}}` references, expands artifact arguments, and synthesises a `WorkflowTaskResult` plus per-step `Pod` specs. KFP v2 makes this lowering explicit: the SDK emits a backend-agnostic IR YAML where every step is a fully-qualified executor spec with its inputs and outputs already resolved. Reading this lowered form is the difference between debugging a pipeline by guessing and debugging it by inspection.

```yaml
# Argo / KFP v2 lowered IR — what the controller actually executes
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: train-fraud-model-9c2f1
  namespace: mlops
  labels:
    workflows.argoproj.io/completed: "false"
    workflows.argoproj.io/phase: Running
spec:
  entrypoint: pipeline
  arguments: {}
status:
  nodes:
    train-fraud-model-9c2f1-2154:
      id: train-fraud-model-9c2f1-2154
      displayName: train
      type: Pod
      templateName: pytorch-train
      phase: Succeeded
      inputs:
        artifacts:
        - name: features
          s3:
            bucket: mlops-artifacts
            key: train-fraud-model-9c2f1/materialize/features.parquet
            endpoint: minio.storage.svc.cluster.local:9000
            insecure: true
      outputs:
        artifacts:
        - name: model
          path: /workspace/model.pt
          s3:
            bucket: mlops-artifacts
            key: train-fraud-model-9c2f1/train/model.pt
            endpoint: minio.storage.svc.cluster.local:9000
        exitCode: "0"
      resourcesDuration:
        nvidia.com/gpu: 3812
        memory: 14503
    train-fraud-model-9c2f1-3071:
      id: train-fraud-model-9c2f1-3071
      displayName: evaluate
      type: Pod
      templateName: holdout-eval
      phase: Running
      inputs:
        artifacts:
        - name: model
          s3:
            bucket: mlops-artifacts
            key: train-fraud-model-9c2f1/train/model.pt
            endpoint: minio.storage.svc.cluster.local:9000
      boundaryID: train-fraud-model-9c2f1
```

Three things are worth noticing in the lowered form. First, the `from:` reference in the authored YAML has been resolved into a concrete `s3.bucket` + `s3.key` pair pointing at the workflow-scoped MinIO prefix — this is why two simultaneous runs of the same pipeline never collide on artifact paths, and why deleting a workflow safely garbage-collects its artifacts. Second, the `resourcesDuration` block under each Pod node records exactly how many GPU-seconds and memory-megabyte-seconds that step consumed; the cluster autoscaler and your chargeback dashboard read this same field, so a pipeline whose IR is missing `resourcesDuration` is invisible to FinOps. Third, `boundaryID` ties child nodes to their parent DAG node, which is how Argo prunes a sub-tree when a parent fails — without it, a failed `train` step would orphan `evaluate` rather than mark it `Omitted`.

When debugging a stuck pipeline, fetch the lowered IR with `argo get -o yaml <workflow-name>` rather than re-reading the authored template. The authored template tells you what was *supposed* to happen; the IR tells you what the controller actually scheduled, which step is currently `Running`, and which artifact key downstream pods are blocking on. KFP v2 users get the same view through `kfp run get --output yaml`, which dumps the same IR structure with KFP's wrapper fields.

### KubeRay
For heavy distributed computing, KubeRay (v1.6.0) is utilized. KubeRay is not a CNCF project; it is maintained under the Ray project ecosystem originating at Anyscale. Ray is the right choice when a single training step needs to fan out across dozens of pods (distributed XGBoost, distributed hyperparameter tuning, or large-scale data preprocessing); Argo and KFP remain the right choice for stitching coarse-grained steps into a multi-stage pipeline.

> **Pause and predict**: A team complains that their nightly KFP pipeline succeeds in development but fails in production with `artifact not found` errors at the `evaluate` step. The pipeline definitions are byte-identical between environments. What is the most likely root cause?
> *Answer*: The production cluster is using a different MinIO bucket prefix than the artifact repository the pipeline expects, and the `artifactRepositoryRef` ConfigMap is missing or misconfigured in the production namespace. Argo and KFP resolve artifact paths at scheduling time using the cluster-scoped artifact repository configuration; pipeline YAML alone never carries the bucket name. Verify the ConfigMap in each target namespace before promoting pipelines across environments.

## Model Serving: KServe & Triton

KServe provides a Kubernetes Custom Resource Definition (CRD) for serving ML models. It handles autoscaling, networking, health checking, and server configuration across multiple frameworks. It is a CNCF Incubating project (accepted September 2025). The latest stable release is v0.17.0. 

While historically widely referred to as KFServing in community lore—though this historical rename is unverified in current official documentation—canonical documentation today refers to it exclusively as KServe. The KServe InferenceService API version is `serving.kserve.io/v1beta1`; it has not yet graduated to a v1 stable release. You will often see `modelserving/v1beta1` in legacy deployment descriptors.

Knative Serving (latest v1.21.2) is optional for KServe; it is only required for the serverless (scale-to-zero) deployment mode. Standard deployments can run without Knative if autoscaling to zero is not required or desired.

### Supported Runtimes
KServe built-in runtimes include TensorFlow Serving, NVIDIA Triton, Hugging Face Server, LightGBM, XGBoost, SKLearn, MLflow, and OpenVINO Model Server. TorchServe is not a built-in runtime; PyTorch models are served via Triton. NVIDIA Triton Inference Server (v2.67.0, NGC container release 26.03) is particularly powerful, supporting TensorRT, PyTorch (TorchScript), TensorFlow, ONNX Runtime, OpenVINO, Python, RAPIDS FIL, and vLLM backends. 

As an alternative to KServe, Seldon Core v2 uses the Business Source License (BSL), not Apache 2.0, which may impact your deployment compliance. BentoML (v1.4.38) is another alternative, commonly understood to be Apache 2.0 licensed, though you must always verify repository licenses in enterprise contexts (as the license is unverified in our authoritative fact ledger).

### A/B Testing and Canary Rollouts

KServe supports native traffic splitting using Knative's routing capabilities. To route traffic securely from the edge, map your Istio VirtualService to the Knative local gateway, ensuring the `Host` header matches the KServe InferenceService URL.

```kubernetes
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: fraud-detection
  namespace: mlops
spec:
  predictor:
    canaryTrafficPercent: 20
    model:
      modelFormat:
        name: xgboost
      storageUri: s3://models/fraud-detection/v2
---
# The previous version remains defined or defaults to the rest of the traffic
```

### Scaling and Failure Modes

KServe inference pods scale through one of two controllers depending on whether Knative is installed. The Knative Pod Autoscaler (KPA) reacts to `concurrency` (in-flight requests per pod) within a few seconds and is the only path to scale-to-zero; the Horizontal Pod Autoscaler (HPA) reacts to CPU or custom Prometheus metrics on a longer cycle (15–60 seconds default) but cannot drop replicas below `minReplicas: 1`. For latency-sensitive serving on GPU nodes, KPA with `containerConcurrency: 4` and `minScale: 1` is the standard production choice — the floor of one replica eliminates cold-start penalties on the multi-gigabyte model weights, while concurrency-based scaling responds to bursty inference traffic faster than CPU-based HPA.

GPU-backed serving introduces failure modes you will never see on CPU-only workloads. Three are worth memorizing:

1. **GPU memory exhaustion under concurrent requests.** A model that fits in 12 GB of VRAM at batch size 1 may overflow at batch size 8 because the framework allocates intermediate activation tensors per request. The pod does not crash cleanly — `nvidia-smi` reports `out of memory` and Triton or TorchServe returns HTTP 500 for that request only, leaving the pod in a degraded state where every fourth or fifth request fails. Mitigation: enforce a `containerConcurrency` ceiling derived from a load test, not from CPU intuition.
2. **Model loading hangs at pod startup.** When a 30 GB LLM weight file pulls slowly from MinIO, the readiness probe times out before the model finishes loading, Kubernetes marks the pod unhealthy, and rolling updates stall indefinitely. Mitigation: set `readinessProbe.initialDelaySeconds` to at least the 95th-percentile model load time observed in staging, and prefer `storageInitializer` sidecars that pre-stage weights to a `RWO` PVC during the init phase.
3. **Eviction by GPU pressure on shared nodes.** When a higher-priority training job lands on the same GPU node, the kubelet evicts the inference pod even if its CPU and memory budgets are well within limits. Mitigation: separate inference and training into distinct node pools using `nodeSelector` and a dedicated `kserve-gpu` taint, or use Kubernetes Pod Priority classes with a `system-cluster-critical` priority for production inference services.

> **Stop and think**: If your serving SLO is p99 < 200 ms and your model takes 90 seconds to load from MinIO, why is `minScale: 0` always wrong even when traffic is sparse?
> *Answer*: A scale-from-zero event introduces a worst-case 90-second pod startup tail before the first byte of response, which is 450× the SLO budget. Cost-conscious teams sometimes accept this for internal-only batch APIs, but any externally-facing inference service must use `minScale: 1` (or higher) to keep at least one warm replica in memory.

## Monitoring & Governance

Monitoring an MLOps platform requires three independent surfaces stitched together: **policy enforcement** at admission time (does this workload comply with resource and security rules?), **infrastructure metrics and alerts** during steady state (are pods healthy and responsive?), and **model-level observability** (are predictions still trustworthy?). A platform that handles only the first two will pass every SRE review and still serve stale or biased predictions for weeks before anyone notices. The diagram below shows how audit signals flow from cluster components into a centralized governance plane.

```mermaid
flowchart LR
    subgraph Cluster
        OPA[OPA Gatekeeper<br/>admission deny]
        Prom[Prometheus<br/>node + pod metrics]
        KServe[KServe predictor<br/>request logs]
        Evidently[Evidently AI<br/>drift scores]
    end
    subgraph Governance Plane
        Loki[Loki<br/>structured logs]
        AM[Alertmanager<br/>routing]
        SIEM[(SIEM / audit DB)]
    end
    OPA -->|deny event| Loki
    Prom -->|alert fires| AM
    KServe -->|prediction log| Loki
    Evidently -->|drift breach| AM
    Loki --> SIEM
    AM -->|page oncall| SIEM
```

### Admission-Time Policy with OPA Gatekeeper

OPA Gatekeeper compiles Rego policies into ConstraintTemplates and enforces them via Kubernetes admission webhooks. A common ML platform requirement is forbidding any pod that requests a GPU without also declaring a memory limit — without the limit, a runaway training job can starve every other pod on the node.

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredResources
metadata:
  name: gpu-pods-must-set-memory-limit
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    namespaces: ["mlops", "training"]
  parameters:
    limits: ["memory"]
    selectors:
      resourceRequests: ["nvidia.com/gpu"]
```

When a pipeline submits a training pod that requests a GPU but omits `resources.limits.memory`, the admission webhook rejects the pod and writes a structured deny event to the audit log. The pipeline step fails fast at submission rather than mid-run, which prevents wasted GPU time and produces a clear, actionable error message for the data scientist who authored the manifest.

#### Enforcing Model-Promotion Rules in Rego

Resource policies are the easy half of governance. The harder half is policies that gate *what* gets shipped — specifically, the rule that no model artifact may move from the `staging` to the `production` MLflow stage without (a) a passing evaluation score on a holdout dataset, (b) a signed-off model card, and (c) provenance that ties the artifact back to a known training run. These checks must happen at admission time on the KServe `InferenceService` resource, not in CI, because a determined operator can always `kubectl apply` directly and bypass any pipeline-level gate. Below is a ConstraintTemplate plus the corresponding Rego module that encodes all three rules. The Rego is valid against OPA's `v1` (formerly `rego.v1`) syntax and uses the standard `gatekeeper.sh/v1` ConstraintTemplate shape.

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: kservepromotionguard
spec:
  crd:
    spec:
      names:
        kind: KServePromotionGuard
      validation:
        openAPIV3Schema:
          type: object
          properties:
            minHoldoutAuc:
              type: number
            requiredAnnotations:
              type: array
              items:
                type: string
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package kservepromotionguard

      import rego.v1

      violation contains {"msg": msg} if {
        input.review.object.kind == "InferenceService"
        input.review.object.metadata.labels["mlops.kubedojo.io/stage"] == "production"
        ann := input.review.object.metadata.annotations
        score := to_number(ann["mlops.kubedojo.io/holdout-auc"])
        score < input.parameters.minHoldoutAuc
        msg := sprintf(
          "promotion blocked: holdout AUC %.3f below required %.3f",
          [score, input.parameters.minHoldoutAuc],
        )
      }

      violation contains {"msg": msg} if {
        input.review.object.kind == "InferenceService"
        input.review.object.metadata.labels["mlops.kubedojo.io/stage"] == "production"
        required := input.parameters.requiredAnnotations
        some key in required
        not input.review.object.metadata.annotations[key]
        msg := sprintf("promotion blocked: missing required annotation %q", [key])
      }

      violation contains {"msg": msg} if {
        input.review.object.kind == "InferenceService"
        input.review.object.metadata.labels["mlops.kubedojo.io/stage"] == "production"
        run_id := input.review.object.metadata.annotations["mlops.kubedojo.io/mlflow-run-id"]
        not regex.match(`^[a-f0-9]{32}$`, run_id)
        msg := "promotion blocked: mlflow-run-id annotation must be a 32-char hex string"
      }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: KServePromotionGuard
metadata:
  name: production-promotion-rules
spec:
  match:
    kinds:
    - apiGroups: ["serving.kserve.io"]
      kinds: ["InferenceService"]
    namespaces: ["mlops-prod"]
  parameters:
    minHoldoutAuc: 0.85
    requiredAnnotations:
    - mlops.kubedojo.io/holdout-auc
    - mlops.kubedojo.io/model-card-url
    - mlops.kubedojo.io/mlflow-run-id
    - mlops.kubedojo.io/signed-off-by
```

The policy contains three independent `violation` rules. The first parses the `holdout-auc` annotation and rejects any promotion whose evaluation score is below the configured threshold (here `0.85`); a deploy that ships a regressed model will fail at admission with a human-readable message instead of silently degrading user experience. The second iterates the operator-supplied `requiredAnnotations` list and asserts every name resolves to a non-empty value, so a manifest that simply omits the model-card URL is rejected the same way as one with a deliberately wrong score. The third rule enforces the *shape* of the MLflow run ID — a 32-character hex string — which catches copy-paste errors and accidental promotion of a placeholder string like `"TODO"` or `"latest"`.

Together these three rules close the gap between CI promotion (which any operator can bypass) and a cluster-side admission gate (which is the last line of defence). The Rego runs in milliseconds against every `InferenceService` apply, the deny message points the responsible engineer directly at the missing field, and the `K8sAuditLogs` Loki stream captures every rejection so a release retrospective can answer the question "which promotions did Gatekeeper block this quarter?" without spelunking through individual `kubectl describe` outputs. This is how a small platform team enforces model-promotion governance at scale without slowing down the data-science teams that consume the platform.

### Infrastructure Alerting with Prometheus

Prometheus alert rules sit on top of metrics scraped from KServe, Argo, MLflow, and the underlying Kubernetes nodes. The most important alert on a serving stack catches sustained elevated error rates before customers do. The rule below fires when more than five percent of a model's responses return non-2xx for ten consecutive minutes:

```yaml
groups:
- name: kserve-inference-slo
  rules:
  - alert: KServeHighErrorRate
    expr: |
      sum by (inference_service) (
        rate(revision_request_count{response_code_class!="2xx"}[5m])
      )
      /
      sum by (inference_service) (
        rate(revision_request_count[5m])
      ) > 0.05
    for: 10m
    labels:
      severity: page
      team: mlops
    annotations:
      summary: "{{ $labels.inference_service }} error rate above 5%"
      runbook: "https://runbooks.mlops.internal/kserve-error-budget"
```

The `for: 10m` clause is deliberate: short error spikes during canary rollouts or pod restarts are normal, and a tighter window would page oncall for benign churn. Pair this rule with one that watches `nvidia_gpu_memory_used_bytes` to catch the GPU-OOM failure mode described earlier, and one on `kserve_revision_request_latency_seconds` (p95) to enforce the latency half of your SLO.

### Model-Level Observability and Drift

Pod-level metrics tell you the platform is healthy; they do not tell you the model is still correct. Evidently AI runs as a Kubernetes Deployment that periodically pulls recent prediction logs and reference data, computes statistical distance metrics (Kolmogorov-Smirnov for numeric features, chi-squared for categoricals), and exports drift scores to Prometheus. When the drift score on a critical input feature crosses the configured threshold, Alertmanager routes the alert to the model owner — not to the platform oncall — because the remediation is retraining, not infrastructure work.

The clearest separation of concerns: platform engineers own the Gatekeeper constraints and the Prometheus alert rules; model owners own the Evidently drift thresholds and the retraining cadence. Both signals land in the same SIEM so that the audit trail tells a coherent story when an incident reconstruction asks who knew what and when.

For specialized ML monitoring, tools like Evidently AI (v0.7.21, Apache 2.0) and ZenML (0.94.2, Apache 2.0) offer drift detection and pipeline management. If you prefer managed platforms, Weights & Biases (wandb) provides an MIT-licensed Python SDK, but the W&B platform itself is a commercial SaaS with no open-source self-hosted server edition.

## Did You Know?

*   Argo Workflows graduated from the CNCF on December 6, 2022, cementing its status in cloud-native orchestration.
*   MLflow v3.11.1 represents a major milestone in experiment tracking, officially supporting Kubernetes as a native backend for MLflow Projects.
*   Kubeflow was accepted into the CNCF Incubator on July 25, 2023, transitioning away from standard Google governance.
*   NVIDIA Triton v2.67.0 (NGC container release 26.03) integrates directly with the vLLM backend, offering massive throughput improvements for LLM serving.

## Practitioner Gotchas and Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **MinIO Signature Version V4 Mismatch** | Older machine learning libraries or older versions of the `boto3` SDK default to S3 Signature Version 2, but MinIO requires Version 4. | Explicitly set `S3_SIGNATURE_VERSION=s3v4` in the container environment variables. |
| **Feast Redis OOM Kills** | Batch materialization from PostgreSQL pushes data faster than Redis can handle, causing memory exhaustion and kubelet termination. | Set a hard `memory.limit` in the Redis StatefulSet and configure `maxmemory-policy allkeys-lru`. |
| **KServe Cold Start Latencies** | Knative scales model pods to zero. Loading a multi-gigabyte neural network into GPU memory causes severe HTTP timeouts. | Add the annotation `serving.knative.dev/minScale: "1"` to the InferenceService. |
| **MLflow DB Connection Exhaustion** | Hundreds of concurrent tuning workers attempt to log metrics to PostgreSQL without a connection pooler. | Deploy PgBouncer in front of PostgreSQL and route the `backend-store-uri` through it. |
| **Missing S3 Endpoints** | Client pods assume public AWS because `MLFLOW_S3_ENDPOINT_URL` is completely absent from their environment definition. | Inject the MinIO endpoint URL into every training pod's environment variables. |
| **Mixing KFP SDKs** | Engineers attempt to compile KFP v2 Python code directly into Argo Workflow YAML manifests. | Use the KFP v2 compiler to generate IR YAML, as Argo YAML generation is deprecated. |
| **Boto3 Silent Hangs** | Pods without correct MinIO routing attempt to reach public AWS and hang silently due to high default timeout limits. | Set `AWS_METADATA_SERVICE_TIMEOUT=1` to force early failures and surface the error. |

## Hands-on Exercise: Deploy MLflow locally

In this exercise, you will deploy a production-ready MLflow stack backed by PostgreSQL and MinIO, and log a test model. This simulates establishing the experimentation layer of a private platform.

### Prerequisites
*   A running Kubernetes v1.35 cluster (`kind` or `k3s`).
*   `kubectl` and `helm` installed locally.
*   A default StorageClass configured.

### Task 1: Deploy MinIO (Artifact Store)

Use Helm to deploy a single-node object store.

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm install minio bitnami/minio \
  --namespace mlops --create-namespace \
  --set auth.rootUser=admin \
  --set auth.rootPassword=supersecret \
  --set defaultBuckets=mlflow-artifacts
```

Wait for the MinIO pod to become ready:
```bash
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=minio -n mlops --timeout=90s
```

### Task 2: Deploy PostgreSQL (Backend Store)

Deploy the relational backend for tracking metrics.

```bash
helm install mlflow-db bitnami/postgresql \
  --namespace mlops \
  --set global.postgresql.auth.postgresPassword=postgres \
  --set global.postgresql.auth.database=mlflow
```
Wait for the PostgreSQL pod to become ready:
```bash
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgresql -n mlops --timeout=90s
```

### Task 3: Deploy the MLflow Tracking Server

Create a file named `mlflow-deployment.yaml`. This manifest builds the stateless tracking server, connects it to the DB, and configures the S3 endpoint.

```kubernetes
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow-server
  namespace: mlops
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
        image: bitnami/mlflow:3.11.1
        command:
        - sh
        - -c
        - |
          mlflow server \
            --host 0.0.0.0 \
            --port 5000 \
            --backend-store-uri postgresql://postgres:postgres@mlflow-db-postgresql.mlops.svc.cluster.local:5432/mlflow \
            --default-artifact-root s3://mlflow-artifacts/
        ports:
        - containerPort: 5000
        env:
        - name: MLFLOW_S3_ENDPOINT_URL
          value: "http://minio.mlops.svc.cluster.local:9000"
        - name: AWS_ACCESS_KEY_ID
          value: "admin"
        - name: AWS_SECRET_ACCESS_KEY
          value: "supersecret"
---
apiVersion: v1
kind: Service
metadata:
  name: mlflow-server
  namespace: mlops
spec:
  selector:
    app: mlflow
  ports:
  - port: 5000
    targetPort: 5000
```

Apply the deployment:
```bash
kubectl apply -f mlflow-deployment.yaml
kubectl wait --for=condition=ready pod -l app=mlflow -n mlops --timeout=90s
```

### Task 4: Verify Logging

Launch a temporary Python pod to act as a training job. 

```bash
kubectl run mlflow-test -n mlops -i --tty --image=python:3.10-slim --rm \
  --env="MLFLOW_TRACKING_URI=http://mlflow-server.mlops.svc.cluster.local:5000" \
  --env="MLFLOW_S3_ENDPOINT_URL=http://minio.mlops.svc.cluster.local:9000" \
  --env="AWS_ACCESS_KEY_ID=admin" \
  --env="AWS_SECRET_ACCESS_KEY=supersecret" \
  -- sh
```

Once inside the pod, install dependencies and run a test:

```bash
# Inside the pod
pip install mlflow boto3 psycopg2-binary

python -c "
import mlflow
import os

with mlflow.start_run():
    mlflow.log_param('learning_rate', 0.01)
    mlflow.log_metric('accuracy', 0.95)
    
    # Create a dummy artifact
    with open('model.txt', 'w') as f:
        f.write('dummy model weights')
        
    mlflow.log_artifact('model.txt')
    print('Run logged successfully!')
"
```

<details>
<summary>Solution & Expected Output</summary>

If your environment variables are correctly injected, the Python script will successfully authenticate against the local MinIO bucket and write the metric to PostgreSQL. 

**Expected Output:**
```text
Run logged successfully!
```

**Success Checklist:**
- [ ] MinIO bucket is accessible locally.
- [ ] PostgreSQL connection resolves without `OperationalError`.
- [ ] Artifacts sync successfully without `InvalidSignature` errors.
</details>

### Task 5: Verify Model Artifacts and Cleanup

Exit the Python shell to terminate the temporary client pod. Then, utilize a port-forward to verify the MLflow tracking server UI in your local browser, confirming the model artifact synced correctly to MinIO.

```bash
kubectl port-forward svc/mlflow-server -n mlops 5000:5000
```

Navigate to `http://localhost:5000`. You should see your recent run logged. Click into the run to verify that `model.txt` is visible in the Artifacts pane.

<details>
<summary>Solution & Expected Output</summary>
The MLflow UI should load correctly, demonstrating that the frontend API server successfully queries the PostgreSQL database for metadata and retrieves the artifact byte stream directly from MinIO.

**Success Checklist:**
- [ ] MLflow UI is accessible via localhost.
- [ ] Run parameter `learning_rate` displays `0.01`.
- [ ] The `model.txt` artifact is visible and downloadable.
</details>


### Troubleshooting the Lab

*   **Error: `psycopg2.OperationalError: could not translate host name`**
    *   *Cause:* The `backend-store-uri` string in the MLflow deployment contains a typo or PostgreSQL has not finished initializing. Verify the Service name of your PostgreSQL deployment.
*   **Error: `botocore.exceptions.EndpointConnectionError: Could not connect to the endpoint URL`**
    *   *Cause:* `MLFLOW_S3_ENDPOINT_URL` is missing or the MinIO service name is incorrect. Ensure the client pod (the `mlflow-test` pod) has the environment variable set explicitly; it does not inherit it from the server.

### Task 6 — Transfer Challenge: Multi-Tenant Isolation

The single-namespace deployment you just built works for one team. A real platform must serve at least three tenant teams (`fraud`, `pricing`, `forecast`) sharing the same physical cluster, where each team can read and write only its own MLflow runs and its own MinIO objects, and where any cross-tenant access attempt is denied at admission time.

This challenge is intentionally open-ended — no single solution YAML is provided. Use the patterns from this module and prior modules in the track to design and defend your approach. Aim to spend 60–90 minutes here.

**Required outcomes:**
1.  Tenant `fraud` can `mlflow.log_artifact` to its own bucket prefix but receives `AccessDenied` when targeting `s3://mlflow-artifacts/pricing/`.
2.  A pod in namespace `pricing` cannot read MLflow runs registered by namespace `fraud`, even though both teams share a single MLflow Tracking Server pod.
3.  Any `Deployment` submitted to the `forecast` namespace that requests a GPU but omits a memory limit is rejected by Gatekeeper with a clear error.

**Design questions to answer in your writeup:**
- Will you run one MLflow Tracking Server per tenant, or one shared server with experiment-level ACLs? What are the operational costs of each path on a 50-tenant platform?
- How do you scope MinIO credentials per tenant — IAM-style policies on a single root bucket, or one bucket per tenant with separate access keys? Which path makes Backups & Disaster Recovery (covered in module 9.6) easier?
- If a tenant exhausts their PostgreSQL connection pool, how do you prevent the noisy neighbor from degrading the other tenants' MLflow logging latency?

**Stretch goal — swap the storage backend.** Reproduce Tasks 1 through 5 with Ceph RGW (via the Rook operator) substituted for the bitnami MinIO chart. Document every place the manifests changed: which environment variables, which Service DNS names, which signature versions. The point of the stretch goal is to feel where MinIO assumptions are baked into the rest of the stack — many teams discover their "S3-compatible" tooling is actually MinIO-compatible only after they try a real swap.

### Transfer Challenge

You have just built and operated a single-tenant MLflow + MinIO + PostgreSQL stack inside one namespace. The transfer ask is harder: redesign the same MLflow tracking + Feast feature-store flow for a **multi-tenant on-prem cluster** where three independent ML teams (`fraud`, `pricing`, `forecast`) must each run experiments, register features, and serve models without ever seeing each other's experiments, runs, datasets, or model artifacts. The cluster has no internet egress and a single MLflow Tracking Server deployment must be shared across all three tenants for cost reasons.

There is no provided solution. Work this on paper for at least an hour before searching for references — the goal is synthesis, not recall.

**Concretely, sketch and defend:**
1. The **namespace topology** — one namespace per tenant, one shared `mlops-system`, or a different cut entirely. State which CRDs live in which namespace and why.
2. The **RBAC model** — which Roles, RoleBindings, and ServiceAccounts gate which MLflow REST endpoints. Note that MLflow Tracking does not natively enforce per-experiment ACLs; describe how you bridge that gap (proxy, OPA, OAuth2-proxy, or a fork). Pick one and justify.
3. The **MinIO bucket-and-credential layout** — bucket-per-tenant with disjoint access keys, single bucket with prefix-scoped IAM policies, or separate MinIO tenancies. Score each on isolation strength, backup ergonomics, and quota enforceability.
4. The **failure mode you are most worried about**, and the smoke test you would run quarterly to prove the isolation still holds. (Hint: the dangerous failure is rarely "tenant A reads tenant B's data on day one"; it is usually "a refactor six months later silently broadens an IAM policy and nobody notices.")

**Defend your design against an adversary.** Assume a curious but non-malicious data scientist on team `pricing` who has full `kubectl` access to the `pricing` namespace. Walk through every API path they could plausibly use to enumerate, read, or modify `fraud` artifacts — the MinIO API, the MLflow REST API, the Kubernetes API, the Feast registry, raw `psycopg2` against the shared Postgres — and explain which control on your design blocks each path. If any path is unblocked, your design is incomplete; iterate until every adversary path terminates in a denial.

The point of this exercise is not to produce a perfect manifest. It is to surface the gap between *plausible-sounding* multi-tenant designs and *actually adversary-resistant* ones — a gap that consumes most platform teams' second year.

## Quiz

**1. Your data scientists report that their training jobs successfully log parameters (like learning rate) to the MLflow UI, but fail with a connection timeout when attempting to save the final model weights. What is the most likely architectural misconfiguration?**
- A) The MLflow tracking server does not have write access to the PostgreSQL database.
- B) The training pod lacks the `MLFLOW_S3_ENDPOINT_URL` environment variable, defaulting to public AWS endpoints.
- C) The MLflow tracking server pod lacks the `AWS_ACCESS_KEY_ID` environment variable.
- D) The Kubernetes cluster default StorageClass is exhausted.

<details>
<summary>Answer</summary>
**Correct Answer: B.** The client pod making the API call requires the S3 endpoint URL to push the artifact directly to MinIO. Parameters are sent via HTTP to the tracking server, which succeeds, but the artifact upload fails because the pod defaults to public AWS endpoints when `MLFLOW_S3_ENDPOINT_URL` is omitted. Without this specific environment variable injected into the training pod, the underlying `boto3` library attempts to route traffic to the public internet instead of your internal cluster service. This results in a silent hang and eventual connection timeout because the internal pod cannot reach AWS S3, or the bucket simply does not exist there.
</details>

**2. A data engineering team proposes using a single MinIO bucket to act as both the Feast offline store for batch training and the Feast online store for real-time model serving. Why will this architectural design fail in production?**
- A) MinIO does not support the Apache Parquet file format required by Feast.
- B) Object storage like MinIO cannot provide the millisecond latency required for the online serving of real-time features.
- C) Feast requires a relational database like PostgreSQL for its online store on bare metal.
- D) MinIO requires AWS credentials, which cannot be securely injected into Feast materialization jobs.

<details>
<summary>Answer</summary>
**Correct Answer: B.** Feast relies on two distinct storage tiers to handle the fundamentally different access patterns of training and serving. While MinIO (Object Storage) is excellent for the batch offline store due to its high throughput for massive datasets, it cannot provide the millisecond latency required for the online serving of real-time features. The online store requires exclusively a low-latency key-value store like Redis on bare metal to achieve the instant lookups needed by live models during inference. Using an object store for both would result in unacceptable latency spikes during real-time prediction requests.
</details>

**3. You deploy a 4GB deep learning model via KServe. The service works during the day, but the first request sent at 3:00 AM times out with an HTTP 504 Gateway Timeout. Subsequent requests succeed. What is the standard practitioner fix for this?**
- A) Increase the Istio Gateway timeout duration to 15 minutes.
- B) Set the annotation `serving.knative.dev/minScale: "1"` on the InferenceService to prevent scale-to-zero.
- C) Switch the underlying object storage from MinIO to Ceph.
- D) Add a Redis cache sidecar to the KServe pod to keep the model in memory.

<details>
<summary>Answer</summary>
**Correct Answer: B.** By default, when Knative Serving is used with KServe, it scales idle services to zero replicas to conserve cluster resources. When a request arrives after a period of inactivity, Knative must spin up a new pod, pull the multi-gigabyte neural network from storage, and load it into GPU memory. This cold-start penalty often exceeds the ingress gateway's timeout threshold, resulting in a 504 error. Setting a minimum scale of 1 (`serving.knative.dev/minScale: "1"`) ensures that at least one replica is always running in memory, providing instant responses at the cost of dedicated idle resources.
</details>

**4. Two data science teams are concurrently training models on the same 100TB image dataset stored in MinIO. Team A needs to aggressively filter out blurry images, while Team B needs the unfiltered original dataset. How does LakeFS solve this conflict without requiring an additional 100TB of physical storage?**
- A) By utilizing Git hooks to track `.dvc` metadata files on the client side.
- B) By providing server-side, zero-copy branching via an API gateway.
- C) By converting the dataset into Parquet files and querying it via Feast.
- D) By utilizing Knative Serving to scale the dataset access dynamically.

<details>
<summary>Answer</summary>
**Correct Answer: B.** LakeFS provides server-side, zero-copy branching via an API gateway that sits in front of your object storage. This is highly efficient for massive datasets because branching takes milliseconds and requires no additional physical storage space to maintain multiple divergent states of the data concurrently. Instead of copying the actual image files, LakeFS simply creates a new metadata pointer to the existing objects. This allows Team A to logically 'delete' images in their branch without affecting Team B's view of the data, all while keeping storage costs identical to a single copy.
</details>

**5. You need to perform an A/B test routing exactly 10% of real-time inference traffic to a new model version (v2) while the rest goes to v1. How is this natively achieved in a KServe deployment?**
- A) Deploying two separate InferenceServices and using a custom NGINX ingress controller script to split traffic based on headers.
- B) Using the `canaryTrafficPercent: 10` spec in the InferenceService resource.
- C) Configuring MLflow to intercept requests and round-robin the traffic.
- D) Scaling the v2 deployment to 1 replica and the v1 deployment to 9 replicas manually.

<details>
<summary>Answer</summary>
**Correct Answer: B.** KServe integrates deeply with Knative's native routing capabilities to handle traffic splitting at the ingress layer. You achieve this by configuring the `canaryTrafficPercent: 10` field within the InferenceService specification. KServe automatically translates this declarative specification into the underlying Knative and Istio routing rules, offloading the traffic split to the gateway automatically. This eliminates the need for manual replica scaling or custom NGINX proxy scripts to achieve weighted traffic distribution.
</details>

**6. Your platform team is deploying Kubeflow Pipelines (KFP) v2, but the security team explicitly forbids installing Argo Workflows in the cluster. How does the KFP v2 architecture allow you to proceed?**
- A) KFP v2 bypasses orchestrators and submits raw Pods directly to the Kubernetes API.
- B) KFP v2 SDK compiles pipelines to a backend-agnostic Intermediate Representation (IR) YAML format, allowing alternative orchestrators to execute them.
- C) KFP v2 relies exclusively on Tekton Pipelines as its default execution engine.
- D) You cannot proceed; KFP v2 still has a hard dependency on Argo Workflows.

<details>
<summary>Answer</summary>
**Correct Answer: B.** The KFP v2 SDK fundamentally redesigns how pipelines are compiled by generating a backend-agnostic Intermediate Representation (IR) YAML format. This is a significant shift from the KFP v1 SDK, which had a hard dependency on generating Argo Workflow-specific YAML manifests. Because the output is now an agnostic IR, it allows alternative execution engines (like Vertex AI Pipelines or customized Kubernetes operators) to run the pipeline without relying on Argo Workflows. This decoupling provides enterprise teams the flexibility to choose their preferred orchestration layer while standardizing on the KFP SDK for authoring.
</details>

**7. A data science team complains that their Feast materialization jobs keep failing halfway through the process. Upon inspection, you notice the Kubernetes node hosting the Feast online store is experiencing heavy swapping and intermittent kubelet unresponsiveness. What architectural flaw is causing this?**
- A) The Feast offline store in PostgreSQL is rejecting concurrent reads due to missing indexes.
- B) The Redis pod lacks memory limits, allowing Feast batch materialization to consume all node memory and trigger an Out Of Memory (OOM) kill.
- C) Knative Serving is autoscaling the Feast pods to zero during materialization.
- D) The MLflow Tracking Server is rejecting the logged materialization metrics.

<details>
<summary>Answer</summary>
**Correct Answer: B.** During batch materialization, data is moved in bulk from the offline store (like PostgreSQL or MinIO) into the online store (Redis). If the Redis pod lacks strictly defined Kubernetes resource limits, it will attempt to consume all available memory on the host node as it ingests the massive influx of feature data. To prevent node-level degradation or an Out Of Memory (OOM) kill by the kubelet, you must set a hard `memory.limit` on the Redis container and configure the `maxmemory-policy allkeys-lru` setting. This ensures Redis evicts older keys when full rather than crashing the node.
</details>

## Further Reading

*   [MLflow Tracking on Kubernetes](https://mlflow.org/docs/latest/tracking.html#tracking-server)
*   [Feast Architecture and Concepts](https://docs.feast.dev/getting-started/architecture-and-components)
*   [KServe InferenceService Architecture](https://kserve.github.io/website/latest/modelserving/v1beta1/inferenceservice/)
*   [LakeFS Object Storage Integration](https://docs.lakefs.io/understand/architecture.html)

## Next Module

Ready to move from platform assembly into closed-loop operations? Proceed to [Module 9.5: Private AIOps](/on-premises/ai-ml-infrastructure/module-9.5-private-aiops/), where we explore how to monitor, automate, and operate internal AI platforms at scale.