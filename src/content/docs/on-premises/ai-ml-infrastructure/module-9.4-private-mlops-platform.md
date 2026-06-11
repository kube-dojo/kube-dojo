---
citations_verified: true
title: "Private MLOps Platform"
description: "Architecting and operating a bare-metal MLOps stack for model tracking, feature stores, and inference."
slug: on-premises/ai-ml-infrastructure/module-9.4-private-mlops-platform
sidebar:
  order: 94
revision_pending: false
---

> **Complexity**: Complex
>
> **Time to Complete**: 3-4 hours
>
> **Prerequisites**: Kubernetes 1.35+, Helm, persistent storage, basic PostgreSQL, object storage, and prior modules in the on-premises AI/ML infrastructure track

---

## Learning Outcomes

* **Architect** a modular private MLOps stack on bare-metal Kubernetes using self-hosted storage, tracking, feature, orchestration, and serving components.
* **Deploy** and configure MLflow with a PostgreSQL backend store, a MinIO artifact store, and explicit client-side S3 endpoint configuration.
* **Implement** a Feast feature-store pattern that separates offline training data from Redis-backed online serving data.
* **Design** controlled model-serving rollouts with KServe, traffic splitting, warm replicas, and GPU-aware failure boundaries.
* **Diagnose** private MLOps failures involving artifact uploads, feature materialization, database connection pools, cold starts, and tenant isolation gaps.

Operating machine learning infrastructure on bare metal requires replacing managed cloud services with self-hosted, scalable equivalents. A production-grade MLOps platform on Kubernetes is not a single monolithic application; it is a loosely coupled ecosystem of stateful data stores, stateless API servers, and workflow orchestrators.

## Why This Module Matters

Hypothetical scenario: your organization trains forecasting, fraud, and recommendation models on regulated data that cannot leave the data center, but the product teams still expect the ergonomics they had in a managed cloud platform. They want experiment tracking, repeatable pipelines, searchable artifacts, feature reuse, canary releases, drift alerts, and an audit trail that explains which model version made which decision. The hard part is that none of those requirements disappear just because the cluster is private; they become your responsibility instead of a vendor's responsibility.

A private MLOps platform therefore sits at an awkward but important boundary. It must feel simple enough for data scientists to use every day, yet it must expose enough operational truth that platform engineers can debug storage, networking, admission policy, database pressure, GPU scheduling, and inference latency when something breaks. If the platform only gives users notebooks and a bucket, every team reinvents deployment in a different way. If the platform hides too much behind a polished portal, the on-call engineer cannot reason about the actual Kubernetes resources during an incident.

This module builds the mental model for that boundary. You will map managed cloud services to self-hosted equivalents, wire MLflow to PostgreSQL and MinIO, reason about Feast's split offline and online stores, choose an orchestrator for training pipelines, and design KServe rollouts that can survive real traffic. The goal is not to memorize a tool catalog; it is to learn which state belongs where, which components are on the request path, and which failures should page a platform engineer versus a model owner.

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

Machine learning models are functions of the code and the data they are trained on. Versioning data on bare metal requires an object storage backend and a tracking layer. For bare metal, MinIO is the standard choice. [The MinIO server is licensed under GNU AGPLv3, while its commercial enterprise offering is called AIStor](https://github.com/minio/minio).

### DVC (Data Version Control)

DVC operates directly on top of Git. It tracks large datasets by storing metadata pointers (`.dvc` files) in Git while pushing the actual payload to MinIO. [As of 2026-06, DVC remained on the 3.x release line and was released under the Apache 2.0 license; verify the exact patch version against the releases page before pinning it in production](https://github.com/iterative/dvc/releases).
*   **Pros:** Requires zero additional infrastructure beyond your Git server and an S3-compatible endpoint. It leverages the developer's existing Git workflow seamlessly.
*   **Cons:** Client-side heavy. Engineers must configure their local environment with S3 credentials, which can become an operational burden as the team scales across many projects.

### LakeFS

LakeFS provides Git-like operations (branch, commit, merge, revert) directly over object storage via an API proxy. 
*   **Pros:** Server-side implementation. Zero-copy branching is near-instant in normal operation because a branch records metadata pointers instead of copying every object.
*   **Cons:** Requires running a dedicated LakeFS PostgreSQL database and API server on the cluster. Applications must use the LakeFS S3 gateway endpoint instead of the direct MinIO endpoint.

:::tip
For smaller teams, DVC is usually sufficient. Treat the LakeFS cutover as a local benchmark decision rather than a universal capacity number: when dataset volume, concurrent branch isolation, or audit requirements outgrow client-side Git-pointer workflows on your hardware, move the branch semantics into LakeFS.
:::

For massive relational data warehousing on-prem, teams often rely on Greenplum or distributed PostgreSQL extensions, treating them as equivalent to cloud-native BigQuery.

## Feature Stores: Feast on Kubernetes

A feature store solves a fundamental problem: bridging the gap between historical data (used for batch training) and real-time data (used for millisecond-latency inference serving). It ensures that the data features used for training exactly match the features used for serving, preventing training-serving skew. 

Feast is a prominent open-source choice. [As of 2026-06, Feast was on the 0.x release line and licensed under Apache 2.0; verify the exact release against the project releases page before pinning a deployment](https://github.com/feast-dev/feast/releases). Notably, Feast is not a CNCF project, operating independently as an open standard for feature engineering.

Feast relies on two storage tiers:
1.  **Offline Store:** Used for batch training. On bare metal, this is typically Apache Parquet files stored in MinIO or tables in a centralized PostgreSQL instance. It stores the historical data required to generate training datasets.
2.  **Online Store:** Used for low-latency inference lookups. Redis is the usual low-latency default we use in this module, but Feast also supports online stores such as Dragonfly, PostgreSQL, MySQL, Cassandra, MongoDB, and others; verify the supported list against the Feast documentation before standardizing. The online tier serves only the latest real-time data points needed by live models.

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

MLflow is hosted under the LF AI & Data Foundation (it is not a CNCF project) and is Apache 2.0 licensed. As of 2026-06, MLflow was on its 3.x release line, moving well past the legacy v2 architecture; verify the exact patch version against the project releases page before pinning production images. MLflow officially supports Kubernetes as a backend for running MLflow Projects, allowing it to build Docker images and submit Kubernetes Jobs seamlessly without external orchestrators.

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

The reflexive on-prem answer for "S3-compatible storage" is Ceph via the Rook operator, but that choice is too heavy for many early MLOps deployments whose object-store workload is mostly experiment artifacts and model checkpoints. MinIO is a **single-binary object server** that stores data on the host filesystem with optional erasure coding across drives; on your hardware, benchmark latency, throughput, erasure-coding overhead, and failure recovery before declaring it sufficient for production. Ceph, by contrast, is a **distributed storage system** that provides block (RBD), file (CephFS), and object (RGW) interfaces simultaneously, with a CRUSH map, monitors, OSDs, and an MDS to coordinate. Operating Ceph competently is a full-time discipline; the cluster requires multiple monitor nodes, careful network sizing, and operational familiarity with PG balancing and scrubbing.

The break-even point depends on workload, but a useful rule of thumb is: stay on MinIO until benchmarking shows that artifact volume, recovery time, multi-site replication, or shared storage strategy requires Ceph. Below that locally measured threshold, MinIO's operational simplicity often dominates; above it, Ceph's broader storage model may justify the extra planning, network tuning, and failover practice. Teams that pick Ceph "because it scales further" without first measuring MinIO's limits typically discover that unfamiliar failure modes — placement-group degradation, slow `osd_op_complaint_time` warnings, MDS rank failures — pull more SRE time than they expected.

The exception worth flagging: if the cluster is *already* running Ceph for stateful workloads (Postgres PVCs, Redis AOF, or RWX volumes for shared notebook home directories), enabling RGW costs essentially nothing and centralises object storage on the same operational substrate. In that environment, MinIO becomes redundant infrastructure. The decision is contextual, not categorical.

:::caution
**Boto3 Connection Timeouts**
When configuring MLflow client pods to talk to MinIO, you must explicitly set connection timeouts in boto3. If `MLFLOW_S3_ENDPOINT_URL` is inaccessible or misconfigured, boto3 can wait through multiple high-latency retry attempts, causing training pods to hang for minutes before finally failing. [Always set `AWS_METADATA_SERVICE_TIMEOUT=1` and `AWS_MAX_ATTEMPTS=2`](https://docs.aws.amazon.com/sdkref/latest/guide/settings-reference.html) to ensure the pod fails fast and frees up cluster resources.
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
    E --> G[Assign @challenger<br/>KServe canary]
```

Steps A and B are I/O bound and fail most often due to upstream data drift; they should retry aggressively (up to 5 times with exponential backoff). Steps C and D are compute bound on GPU nodes; retrying a 4-hour training run blindly burns expensive cycles, so retry policy here should be `OnFailure` with a strict count of 1 and clear escalation to a human. Step E is a transactional write to MLflow and PostgreSQL; idempotency must be guaranteed by hashing the model artifact rather than the wall-clock timestamp, otherwise a partial failure leaves duplicate registry entries.

### Kubeflow & KFP
[Kubeflow is a CNCF Incubating project (accepted July 2023, not yet Graduated)](https://www.cncf.io/blog/2023/07/25/kubeflow-brings-mlops-to-the-cncf-incubator/). As of 2026-06, Kubeflow remained in the 1.x platform release line; verify the exact patch version before pinning platform manifests. Kubeflow Pipelines (KFP) SDK v1 is frozen on the legacy 1.x line, while SDK v2 is the actively developed line. Crucially, [the KFP v2 SDK compiles pipelines to a backend-agnostic `PipelineSpec` intermediate representation](https://kubeflow-pipelines.readthedocs.io/en/sdk-2.16.0/source/overview.html), a protobuf/JSON structure that is distinct from Argo Workflow YAML and Argo runtime status.

For model training, [Kubeflow Trainer's v2-era `TrainJob` API supports PyTorch, JAX, XGBoost, MPI, and Flux distributed training under a single unified CRD](https://github.com/kubeflow/trainer). Hyperparameter optimization is handled by [Katib, whose 0.x release line supports algorithms including grid search, random search, Bayesian optimization, Hyperband, TPE, multivariate-TPE, CMA-ES, Sobol, and Population Based Training (PBT)](https://github.com/kubeflow/katib); verify the exact Katib release before selecting CRD versions.

### Argo & Tekton
As of 2026-06, Argo Workflows maintained both v4 and v3 LTS release lines, and [the Argo project as a whole is a CNCF Graduated project](https://www.cncf.io/projects/argo/); verify the exact controller patch before installing CRDs. Alternatively, [Tekton Pipelines is a CNCF Incubating project as of March 2026, having moved from the Continuous Delivery Foundation](https://www.cncf.io/blog/2026/03/24/tekton-becomes-a-cncf-incubating-project/), and its exact release should be checked against the Tekton releases page before pinning pipeline manifests.

A minimal Argo Workflow excerpt that mirrors the canonical DAG above looks like this. It is intentionally abbreviated: the DAG wiring and GPU `pytorch-train` template are shown, while the `ge-validate`, `feast-materialize`, and `holdout-eval` step templates are elided for brevity. Note the explicit `artifacts` block that hands the trained model from the `train` step to the `evaluate` step via the cluster's MinIO bucket — without this declaration, Argo would not know how to wire pod outputs into pod inputs.

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

#### Authored Workflow, Runtime Status, and KFP IR

The YAML above is the *authored* Argo Workflow form — what a platform engineer types into version control. Once submitted, the Argo controller creates pods, records node state, resolves artifact locations, and stores runtime details under `status.nodes`; that runtime status is what `argo get -o yaml <workflow-name>` shows. KFP v2 is a separate layer: the SDK compiler emits a backend-agnostic `PipelineSpec` IR as a protobuf/JSON structure before any backend turns it into runnable resources. Do not treat Argo `status.nodes` as KFP IR, and do not expect a KFP run lookup to dump the same Argo runtime object.

```yaml
# Argo runtime status excerpt — representative output shape from `argo get -o yaml`
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

Three things are worth noticing in the runtime status. First, the `from:` reference in the authored YAML has been resolved into a concrete `s3.bucket` + `s3.key` pair pointing at the workflow-scoped MinIO prefix; this is why two simultaneous runs of the same pipeline do not collide on artifact paths. Artifact cleanup is a separate control: Argo deletes object-store artifacts only when artifact garbage collection is explicitly configured through `spec.artifactGC` and the artifact repository policy, so never assume Workflow deletion alone cleans the bucket. Second, the `resourcesDuration` block under each Pod node records how many GPU-seconds and memory-megabyte-seconds that step consumed; your chargeback dashboard can use this runtime field, but it is not part of the authored KFP `PipelineSpec`. Third, `boundaryID` ties child nodes to their parent DAG node, which is how Argo prunes a sub-tree when a parent fails — without it, a failed `train` step would orphan `evaluate` rather than mark it `Omitted`.

When debugging a stuck Argo-backed pipeline, fetch runtime status with `argo get -o yaml <workflow-name>` rather than re-reading the authored template. The authored template tells you what was *supposed* to happen; the Argo status tells you what the controller actually scheduled, which step is currently `Running`, and which artifact key downstream pods are blocking on. For KFP v2, inspect the compiled `PipelineSpec` when validating the portable pipeline contract, then inspect the backend-specific run or Argo Workflow status when debugging a concrete execution.

### KubeRay
For heavy distributed computing, [KubeRay is used in the Ray ecosystem and, as of 2026-06, remained on the 1.x release line rather than being a CNCF project](https://github.com/ray-project/kuberay). Ray is the right choice when a single training step needs to fan out across dozens of pods (distributed XGBoost, distributed hyperparameter tuning, or large-scale data preprocessing); Argo and KFP remain the right choice for stitching coarse-grained steps into a multi-stage pipeline.

> **Pause and predict**: A team complains that their nightly KFP pipeline succeeds in development but fails in production with `artifact not found` errors at the `evaluate` step. The pipeline definitions are byte-identical between environments. What is the most likely root cause?
> *Answer*: The production cluster is using a different MinIO bucket prefix than the artifact repository the pipeline expects, and the `artifactRepositoryRef` ConfigMap is missing or misconfigured in the production namespace. Argo and KFP resolve artifact paths at scheduling time using the cluster-scoped artifact repository configuration; pipeline YAML alone never carries the bucket name. Verify the ConfigMap in each target namespace before promoting pipelines across environments.

## Model Serving: KServe & Triton

KServe provides a Kubernetes Custom Resource Definition (CRD) for serving ML models. It handles autoscaling, networking, health checking, and server configuration across multiple frameworks. [It is a CNCF Incubating project; the public CNCF announcement for incubation is dated November 11, 2025, and as of 2026-06 KServe remained on the 0.x release line, so verify the exact controller version before installing CRDs](https://www.cncf.io/projects/kserve/).

While historically widely referred to as KFServing in community lore—though this historical rename is unverified in current official documentation—[canonical documentation today refers to it exclusively as KServe. The KServe InferenceService API version is `serving.kserve.io/v1beta1`](https://www.cncf.io/blog/2025/11/11/kserve-becomes-a-cncf-incubating-project/); it has not yet graduated to a v1 stable release. You will often see `modelserving/v1beta1` in legacy deployment descriptors.

As of 2026-06, Knative Serving remained on the 1.x release line. It is optional for KServe; Knative is only required for the serverless scale-to-zero deployment mode. Standard deployments can run without Knative if autoscaling to zero is not required or desired.

### Supported Runtimes
KServe built-in runtimes include TensorFlow Serving, NVIDIA Triton, Hugging Face Server, LightGBM, XGBoost, SKLearn, MLflow, OpenVINO Model Server, and a TorchServe runtime. PyTorch's TorchServe project is in limited maintenance with no planned fixes or security patches, so treat TorchServe as a legacy option and prefer Triton for new PyTorch serving. [As of 2026-06, NVIDIA Triton Inference Server remained on the v2 release line with NGC container releases and supported TensorRT, PyTorch (TorchScript), TensorFlow, ONNX Runtime, OpenVINO, Python, RAPIDS FIL, and vLLM backends](https://github.com/triton-inference-server/server/releases).

As an alternative to KServe, Seldon Core v2 uses the Business Source License (BSL), not Apache 2.0, which may impact your deployment compliance. As of 2026-06, BentoML was on the 1.x release line and commonly understood to be Apache 2.0 licensed, though you must always verify repository licenses in enterprise contexts because the license is unverified in our authoritative fact ledger.

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
3. **Eviction by GPU pressure on shared nodes.** When a higher-priority training job lands on the same GPU node, the kubelet evicts the inference pod even if its CPU and memory budgets are well within limits. Mitigation: separate inference and training into distinct node pools using `nodeSelector` and a dedicated `kserve-gpu` taint, or define a custom application PriorityClass such as `mlops-inference-critical` with a value below the reserved system priority range. Built-in `system-cluster-critical` and `system-node-critical` priorities are for cluster components, not ordinary inference workloads.

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
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sgpumemorylimit
spec:
  crd:
    spec:
      names:
        kind: K8sGpuMemoryLimit
      validation:
        openAPIV3Schema:
          type: object
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8sgpumemorylimit

      import rego.v1

      violation contains {"msg": msg} if {
        input.review.object.kind == "Pod"
        container := input.review.object.spec.containers[_]
        gpu_request := container.resources.requests["nvidia.com/gpu"]
        not container.resources.limits.memory
        msg := sprintf(
          "container %q requests %v GPU(s) but does not set resources.limits.memory",
          [container.name, gpu_request],
        )
      }

      violation contains {"msg": msg} if {
        input.review.object.kind == "Pod"
        container := input.review.object.spec.initContainers[_]
        gpu_request := container.resources.requests["nvidia.com/gpu"]
        not container.resources.limits.memory
        msg := sprintf(
          "initContainer %q requests %v GPU(s) but does not set resources.limits.memory",
          [container.name, gpu_request],
        )
      }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sGpuMemoryLimit
metadata:
  name: gpu-pods-must-set-memory-limit
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    namespaces: ["mlops", "training"]
```

When a pipeline submits a training pod that requests a GPU but omits `resources.limits.memory`, the admission webhook rejects the pod and writes a structured deny event to the audit log. The pipeline step fails fast at submission rather than mid-run, which prevents wasted GPU time and produces a clear, actionable error message for the data scientist who authored the manifest.

#### Enforcing Model-Promotion Rules in Rego

Resource policies are the easy half of governance. The harder half is policies that gate *what* gets shipped — specifically, the rule that a model version should receive an MLflow alias such as `@champion` or `@challenger`, plus the required environment tags, only after (a) a passing evaluation score on a holdout dataset, (b) a signed-off model card, and (c) provenance that ties the artifact back to a known training run. MLflow Model Registry stages are deprecated, so do not build new promotion workflows around those stage fields. These checks must happen at admission time on the KServe `InferenceService` resource, not only in CI, because a determined operator can always `kubectl apply` directly and bypass any pipeline-level gate. Below is a ConstraintTemplate plus the corresponding Rego module that encodes the KServe-side deployment guard: production is a deployment environment label, while the MLflow model version is identified by annotations carrying model name, version, alias, run ID, and environment tag. The Rego is valid against OPA's `v1` (formerly `rego.v1`) syntax and uses the standard `gatekeeper.sh/v1` ConstraintTemplate shape.

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
            allowedAliases:
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
        input.review.object.metadata.labels["mlops.kubedojo.io/environment"] == "production"
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
        input.review.object.metadata.labels["mlops.kubedojo.io/environment"] == "production"
        required := input.parameters.requiredAnnotations
        some key in required
        not input.review.object.metadata.annotations[key]
        msg := sprintf("promotion blocked: missing required annotation %q", [key])
      }

      violation contains {"msg": msg} if {
        input.review.object.kind == "InferenceService"
        input.review.object.metadata.labels["mlops.kubedojo.io/environment"] == "production"
        alias := input.review.object.metadata.annotations["mlops.kubedojo.io/mlflow-model-alias"]
        not alias_allowed(alias)
        msg := sprintf("promotion blocked: MLflow alias %q is not allowed for production deployment", [alias])
      }

      violation contains {"msg": msg} if {
        input.review.object.kind == "InferenceService"
        input.review.object.metadata.labels["mlops.kubedojo.io/environment"] == "production"
        run_id := input.review.object.metadata.annotations["mlops.kubedojo.io/mlflow-run-id"]
        not regex.match(`^[a-f0-9]{32}$`, run_id)
        msg := "promotion blocked: mlflow-run-id annotation must be a 32-char hex string"
      }

      alias_allowed(alias) if {
        alias == input.parameters.allowedAliases[_]
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
    allowedAliases:
    - "@champion"
    - "@challenger"
    requiredAnnotations:
    - mlops.kubedojo.io/holdout-auc
    - mlops.kubedojo.io/model-card-url
    - mlops.kubedojo.io/mlflow-run-id
    - mlops.kubedojo.io/mlflow-model-name
    - mlops.kubedojo.io/mlflow-model-version
    - mlops.kubedojo.io/mlflow-model-alias
    - mlops.kubedojo.io/mlflow-env-tag
    - mlops.kubedojo.io/signed-off-by
```

The policy contains four independent `violation` rules. The first parses the `holdout-auc` annotation and rejects any production deployment whose evaluation score is below the configured threshold (here `0.85`); a deploy that ships a regressed model will fail at admission with a human-readable message instead of silently degrading user experience. The second iterates the operator-supplied `requiredAnnotations` list and asserts every name resolves to a non-empty value, so a manifest that simply omits the model-card URL, MLflow alias, or environment tag is rejected the same way as one with a deliberately wrong score. The third rule limits production manifests to explicitly allowed model-version aliases, such as `@champion` or `@challenger`, rather than accepting an arbitrary alias like `"@untested"`. The fourth rule enforces the *shape* of the MLflow run ID — a 32-character hex string — which catches copy-paste errors and accidental promotion of a temporary value like `"replace-me"`.

Together these four rules close the gap between CI promotion (which any operator can bypass) and a cluster-side admission gate (which is the last line of defence). The Rego runs quickly against every `InferenceService` apply, the deny message points the responsible engineer directly at the missing field, and the `K8sAuditLogs` Loki stream captures every rejection so a release retrospective can answer the question "which promotions did Gatekeeper block this quarter?" without spelunking through individual `kubectl describe` outputs. This is how a small platform team enforces model-promotion governance at scale without slowing down the data-science teams that consume the platform.

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

For specialized ML monitoring, tools like Evidently AI and ZenML offer drift detection and pipeline management; as of 2026-06, both projects were still in pre-1.0 release lines, so verify exact versions and APIs before adopting them. If you prefer managed platforms, Weights & Biases (wandb) provides an MIT-licensed Python SDK, but the W&B platform itself is a commercial SaaS with no open-source self-hosted server edition.

## Patterns & Anti-Patterns

The most reliable private MLOps platforms are built as small, explicit contracts between components rather than as one enormous application. MLflow owns run metadata and artifact pointers, MinIO or Ceph owns object bytes, Feast owns feature definitions and materialization, Argo or KFP owns step orchestration, KServe owns the live inference resource, and Gatekeeper owns the admission-time rules. This separation makes the platform easier to debug because each failure has a narrower blast radius. When a model upload fails, you inspect the client pod's S3 endpoint and MinIO credentials; when a run disappears from the UI, you inspect the backend database and MLflow server logs.

**Pattern: keep serving independent from experiment tracking.** A production InferenceService should pull immutable model artifacts from object storage and should not depend on the MLflow UI being healthy at request time. MLflow is the system of record for experiments and model registry metadata, but it is not a low-latency dependency for every prediction. This pattern works because it turns the serving path into a small chain: ingress, model server, feature lookup, and object storage during startup. It scales well when model promotion writes a new immutable artifact URI and the serving controller rolls pods against that URI.

**Pattern: treat online stores as derived caches.** Redis, DragonflyDB, or another online feature store should be rebuilt from the offline store through materialization jobs, not treated as the only source of truth. The operational benefit is enormous: backup policy focuses on PostgreSQL, Parquet, and object storage, while Redis recovery becomes a repeatable rebuild procedure. This pattern also clarifies ownership during incidents. Platform engineers restore the service and materialization job, while model owners verify whether a recent feature definition change produced the wrong values.

**Pattern: enforce promotion rules at admission time.** CI checks are useful, but they are not the last line of defense in a cluster where operators can apply Kubernetes manifests directly. Gatekeeper constraints on KServe resources let you require holdout scores, model-card URLs, MLflow aliases, environment tags, run provenance, and resource limits before production objects are accepted by the API server. This pattern scales because policy becomes part of the control plane rather than a spreadsheet maintained by release managers. It also produces auditable denial events that can be routed to logs and reviewed after a failed promotion.

**Anti-pattern: building the platform around notebooks.** Notebooks are excellent for exploration, but a notebook server is not an MLOps platform. Teams fall into this trap because early prototypes feel productive: a scientist can load data, fit a model, and upload a file in one place. The problem appears later when nobody can reproduce the environment, locate the exact training data, or prove which code generated a model in production. Keep notebooks as clients of the platform, then require experiments, artifacts, feature definitions, and serving manifests to flow through versioned interfaces.

**Anti-pattern: using object storage as the online feature path.** Object storage is durable and cheap, so it is tempting to make every feature lookup read from MinIO or Ceph. That design fails under live traffic because object stores optimize throughput and durability, not one-key millisecond reads for every prediction request. The better design is to materialize current features into Redis and reserve object storage for batch datasets, model artifacts, and workflow outputs. You pay for memory where latency matters and use cheaper storage where scans and history matter.

**Anti-pattern: sharing credentials across tenants.** A single MinIO access key, a single MLflow service account, and broad namespace permissions make a demo easier, but they destroy tenant isolation the moment multiple teams use the same cluster. The common excuse is operational simplicity, yet shared credentials make it impossible to prove which team accessed which artifact and impossible to revoke one team's access without rotating everyone. Use tenant-scoped service accounts, bucket or prefix policies, namespace-bound RBAC, and policy tests that deliberately attempt cross-tenant reads.

## Decision Framework

Start every private MLOps design with the request path, not the tool list. Ask what happens when a user sends a prediction request: which gateway receives it, which model server handles it, whether a feature lookup occurs, whether that lookup touches Redis or another online store, and whether any call reaches a database that was meant only for training. If the answer includes MLflow, PostgreSQL scans, a notebook server, or a human-controlled script on the live path, the design is not ready for production inference. Serving should be boring, narrow, and mostly independent of the experimentation plane.

For experiment tracking, choose MLflow with PostgreSQL and MinIO when teams need a common registry, common metrics view, and artifact lineage across many frameworks. Add PgBouncer when parallel tuning or batch training can create more client connections than PostgreSQL should hold directly. Choose a separate MLflow deployment per tenant when isolation and chargeback matter more than centralized convenience; choose a shared deployment only if you also have an authorization layer that can enforce per-tenant experiment boundaries. MLflow's open API surface is valuable, but it does not remove the need for tenancy controls.

For feature storage, choose the offline store based on history size and query shape, then choose the online store based on lookup latency and memory cost. PostgreSQL or Parquet on object storage is a reasonable offline start for moderate tabular data, while ClickHouse or another analytical store becomes attractive when feature history grows into very large event tables. Redis is the default online store because its operational model is familiar and its latency profile is appropriate for inference. Before running this in production, pause and predict: if Redis disappears at noon, can your team rebuild the online store from authoritative history without changing model code?

For orchestration, choose Argo Workflows when platform engineers want Kubernetes-native YAML, explicit artifact wiring, and direct control over pod templates. Choose Kubeflow Pipelines when data science teams want a Python SDK, reusable components, experiment UI integration, and a pipeline abstraction that can compile beyond one backend. Choose KubeRay for distributed compute inside a training or preprocessing step, not as a replacement for the workflow orchestrator that sequences validation, training, evaluation, and promotion. The practical decision is about authoring experience and debugging visibility, not about which project has the longest feature list.

For serving, choose KServe when you want Kubernetes-native model serving with runtime abstraction, traffic splitting, autoscaling, and integration with Istio or Knative. Use warm replicas for latency-sensitive services and reserve scale-to-zero for internal or batch endpoints whose callers can tolerate startup delay. Use Triton when the model format, GPU usage, batching, or multi-framework serving requirements justify its operational complexity. Which approach would you choose for a model that loads in 90 seconds but receives only one request per hour, and why? The correct answer depends on whether the caller values cost or latency more, and the platform should make that tradeoff explicit.

## Did You Know?

*   [Argo Workflows graduated from the CNCF on December 6, 2022](https://www.cncf.io/projects/argo/), cementing its status in cloud-native orchestration.
*   As of 2026-06, MLflow's 3.x release line represented the current architecture for experiment tracking and officially supported Kubernetes as a native backend for MLflow Projects.
*   Kubeflow was accepted into the CNCF Incubator on July 25, 2023, transitioning away from standard Google governance.
*   As of 2026-06, NVIDIA Triton's v2 release line included NGC container releases and direct vLLM backend integration; verify the exact tag before pinning serving images.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **MinIO Signature Version V4 Mismatch** | Older machine learning libraries or older versions of the `boto3` SDK default to S3 Signature Version 2, but MinIO requires Version 4. | Explicitly set `S3_SIGNATURE_VERSION=s3v4` in the container environment variables. |
| **Feast Redis OOM Kills** | Batch materialization from PostgreSQL pushes data faster than Redis can handle, causing memory exhaustion and kubelet termination. | Set a hard `memory.limit` in the Redis StatefulSet and configure `maxmemory-policy allkeys-lru`. |
| **KServe Cold Start Latencies** | Knative scales model pods to zero. Loading a multi-gigabyte neural network into GPU memory causes severe HTTP timeouts. | Add the annotation `serving.knative.dev/minScale: "1"` to the InferenceService. |
| **MLflow DB Connection Exhaustion** | Hundreds of concurrent tuning workers attempt to log metrics to PostgreSQL without a connection pooler. | Deploy PgBouncer in front of PostgreSQL and route the `backend-store-uri` through it. |
| **Missing S3 Endpoints** | Client pods assume public AWS because `MLFLOW_S3_ENDPOINT_URL` is completely absent from their environment definition. | Inject the MinIO endpoint URL into every training pod's environment variables. |
| **Mixing KFP SDKs** | Engineers attempt to compile KFP v2 Python code directly into Argo Workflow YAML manifests. | Use the KFP v2 compiler to generate a `PipelineSpec` IR, then inspect the backend-specific runtime object separately. |
| **Boto3 Silent Hangs** | Pods without correct MinIO routing attempt to reach public AWS and hang silently due to high default timeout limits. | [Set `AWS_METADATA_SERVICE_TIMEOUT=1`](https://docs.aws.amazon.com/sdkref/latest/guide/settings-reference.html) to force early failures and surface the error. |

## Quiz

<details>
<summary>Question 1: Your team is architecting a modular private MLOps stack on Kubernetes. Training jobs can log MLflow parameters, but saving model artifacts times out after several minutes. Which component boundary do you inspect first?</summary>

A) The MLflow tracking server's write access to PostgreSQL.

B) The training pod's `MLFLOW_S3_ENDPOINT_URL` and S3 credentials.

C) The default Kubernetes StorageClass used by PostgreSQL.

D) The KServe InferenceService rollout status.

**Answer:** B is the best first check because MLflow parameters are sent to the tracking server, while artifacts are commonly uploaded from the client pod to the object store using the S3-compatible endpoint. A is wrong for this symptom because the parameters already prove the server can write metadata to PostgreSQL. C could matter for database persistence, but it does not explain an artifact upload timeout from a training client. D is unrelated because KServe serving resources are not involved when a training pod logs an artifact.
</details>

<details>
<summary>Question 2: A data engineering team proposes using MinIO as both the Feast offline store and the online store for real-time feature lookups. Why is this design unsafe for production serving?</summary>

A) MinIO cannot store Parquet files used by training jobs.

B) Object storage does not provide the low-latency keyed reads expected on the online inference path.

C) Feast requires PostgreSQL as the online store in all bare-metal deployments.

D) MinIO credentials cannot be mounted safely into Kubernetes jobs.

**Answer:** B is correct because the online store serves one-key lookups during live inference and must respond in milliseconds under repeated access to hot entities. A is wrong because object storage is commonly used for Parquet and other batch artifacts. C is wrong because Redis or another low-latency key-value store is the usual online choice, while PostgreSQL is more appropriate for offline history or metadata. D is a security design concern, not the fundamental latency reason the architecture fails.
</details>

<details>
<summary>Question 3: A KServe model loads a large GPU-backed runtime from MinIO. The first request after a quiet night returns a gateway timeout, but later requests are fast. What rollout setting most directly addresses this?</summary>

A) Increase the gateway timeout until the model finishes loading.

B) Set a minimum warm replica, such as `serving.knative.dev/minScale: "1"`.

C) Move the model artifact from MinIO to PostgreSQL.

D) Remove the readiness probe so the pod enters service sooner.

**Answer:** B is correct because the symptom is a cold start: no pod is warm, so the first request waits for scheduling, image startup, artifact download, and model load. A hides the user-facing timeout but still violates a low-latency serving objective. C is wrong because PostgreSQL is not a model-weight artifact store. D is dangerous because it can route traffic to a pod before the model is ready, making failures less predictable rather than fixing them.
</details>

<details>
<summary>Question 4: Two teams need different views of the same large image dataset. One team must filter blurry images while the other must keep the original. Which data-versioning approach avoids duplicating the whole dataset?</summary>

A) Client-side DVC metadata files only.

B) LakeFS server-side zero-copy branching over object storage.

C) Converting all images into Feast online features.

D) KServe traffic splitting between two model versions.

**Answer:** B is the strongest fit because LakeFS creates branch and commit semantics over object storage without copying every underlying object. A can track dataset pointers, but it still relies heavily on client workflow discipline and does not give the same server-side branch isolation. C confuses training datasets with online feature serving and would be impractical for large image history. D controls prediction traffic after models are served; it does not version source datasets.
</details>

<details>
<summary>Question 5: You need to route a small percentage of live inference traffic to a new model while most requests continue using the stable version. Which KServe mechanism should you design around?</summary>

A) Two unrelated InferenceServices and a hand-written NGINX split.

B) The `canaryTrafficPercent` field on the InferenceService.

C) MLflow round-robin routing between registered models.

D) Manually scaling old and new Deployments to different replica counts.

**Answer:** B is correct because KServe exposes declarative traffic splitting through the InferenceService and translates the intent into the underlying serving and routing resources. A can work in a custom platform, but it discards the controller's native rollout behavior and creates more hand-managed ingress state. C is wrong because MLflow tracks and registers models; it is not the live request router. D is unreliable because replica ratios do not guarantee request ratios when load balancing, readiness, and autoscaling change over time.
</details>

<details>
<summary>Question 6: A platform team wants Kubeflow Pipelines authoring, but security reviewers do not want teams hand-editing raw Argo Workflow manifests. How does KFP v2 change the discussion?</summary>

A) KFP v2 submits pods directly and no longer needs any orchestrator.

B) KFP v2 compiles pipeline definitions into a backend-agnostic intermediate representation.

C) KFP v2 requires Tekton as the only supported execution engine.

D) KFP v2 stores every artifact in the MLflow backend database.

**Answer:** B is correct because the v2 SDK's intermediate representation separates authoring from a single YAML shape and gives platform teams a clearer boundary for validation, compilation, and execution. A is wrong because a real pipeline still needs a controller or backend to schedule steps and manage artifacts. C overstates the dependency; the point is portability of the compiled representation, not a single mandatory engine. D is wrong because artifacts should remain in object storage rather than the MLflow relational backend.
</details>

<details>
<summary>Question 7: A Feast materialization job repeatedly crashes Redis, and the node hosting Redis becomes unstable during the batch load. What failure mode should you diagnose first?</summary>

A) PostgreSQL rejecting historical reads because KServe is scaling down.

B) Redis missing a memory limit and eviction policy during bulk materialization.

C) MLflow refusing to log materialization metrics.

D) Gatekeeper blocking the KServe canary rollout.

**Answer:** B is correct because materialization pushes many feature values into the online store, and an unconstrained Redis pod can consume node memory until the kubelet intervenes. A mixes the offline store with serving autoscaling and does not explain Redis pressure. C might affect observability but not the online store's memory exhaustion. D is unrelated because this failure happens in the feature pipeline before an InferenceService rollout is evaluated.
</details>

## Hands-On Exercise: Deploy MLflow locally

In this exercise, you will deploy a production-ready MLflow stack backed by PostgreSQL and MinIO, and log a test model. This simulates establishing the experimentation layer of a private platform.

### Prerequisites
*   A running Kubernetes v1.35 cluster (`kind` or `k3s`).
*   `kubectl` and `helm` installed locally.
*   A default StorageClass configured.

### Task 1: Deploy MinIO (Artifact Store)

Use Helm to deploy a single-node object store for lab purposes. A production installation would use stronger credentials, persistent capacity planning, network policy, and a backup design, but the single-node deployment keeps the exercise focused on the MLflow-to-object-storage contract.

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm install minio bitnami/minio \
  --namespace mlops --create-namespace \
  --set auth.rootUser=admin \
  --set auth.rootPassword=supersecret \
  --set defaultBuckets=mlflow-artifacts
```

Wait for the MinIO pod to become ready before installing the tracking server. This step matters because MLflow clients will later authenticate directly to the object store, so a partially initialized MinIO deployment can create misleading artifact errors that look like MLflow failures.

```bash
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=minio -n mlops --timeout=90s
```

### Task 2: Deploy PostgreSQL (Backend Store)

Deploy the relational backend for tracking metadata, parameters, metrics, and run state. PostgreSQL is not where large model artifacts belong; it is the durable index that lets the MLflow UI and API locate those artifacts and explain how they were produced.

```bash
helm install mlflow-db bitnami/postgresql \
  --namespace mlops \
  --set global.postgresql.auth.postgresPassword=postgres \
  --set global.postgresql.auth.database=mlflow
```
Wait for the PostgreSQL pod to become ready before wiring the tracking server to it. If the service DNS name resolves before the database accepts connections, the first MLflow pod can crash-loop and hide the real timing issue behind generic connection errors.

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

Apply the deployment and wait for the tracking server to become ready. This gives you one stateless API pod connected to two stateful backends, which is the smallest useful slice of a private experimentation platform.

```bash
kubectl apply -f mlflow-deployment.yaml
kubectl wait --for=condition=ready pod -l app=mlflow -n mlops --timeout=90s
```

### Task 4: Verify Logging

Launch a temporary Python pod to act as a training job. Notice that the client pod receives the tracking URI and the S3 endpoint; this is the critical detail that many first-time MLflow deployments miss, because artifact upload happens from the client environment rather than magically through the server for every backend.

```bash
kubectl run mlflow-test -n mlops -i --tty --image=python:3.10-slim --rm \
  --env="MLFLOW_TRACKING_URI=http://mlflow-server.mlops.svc.cluster.local:5000" \
  --env="MLFLOW_S3_ENDPOINT_URL=http://minio.mlops.svc.cluster.local:9000" \
  --env="AWS_ACCESS_KEY_ID=admin" \
  --env="AWS_SECRET_ACCESS_KEY=supersecret" \
  -- sh
```

Once inside the pod, install dependencies and run a test that writes both metadata and an artifact. If parameters appear in the UI but `model.txt` does not appear in the artifact pane, you have proven that metadata and artifact paths can fail independently.

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

Navigate to `http://127.0.0.1:5000`. You should see your recent run logged. Click into the run to verify that `model.txt` is visible in the Artifacts pane.

<details>
<summary>Solution & Expected Output</summary>
The MLflow UI should load correctly, demonstrating that the frontend API server successfully queries the PostgreSQL database for metadata and retrieves the artifact byte stream directly from MinIO.

**Success Checklist:**
- [ ] MLflow UI is accessible via `127.0.0.1`.
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

### Task 7 — Extended Transfer Challenge

You have just built and operated a single-tenant MLflow + MinIO + PostgreSQL stack inside one namespace. The transfer ask is harder: redesign the same MLflow tracking + Feast feature-store flow for a **multi-tenant on-prem cluster** where three independent ML teams (`fraud`, `pricing`, `forecast`) must each run experiments, register features, and serve models without ever seeing each other's experiments, runs, datasets, or model artifacts. The cluster has no internet egress and a single MLflow Tracking Server deployment must be shared across all three tenants for cost reasons.

There is no provided solution. Work this on paper for at least an hour before searching for references — the goal is synthesis, not recall.

**Concretely, sketch and defend:**
1. The **namespace topology** — one namespace per tenant, one shared `mlops-system`, or a different cut entirely. State which CRDs live in which namespace and why.
2. The **RBAC model** — which Roles, RoleBindings, and ServiceAccounts gate which MLflow REST endpoints. Note that MLflow Tracking does not natively enforce per-experiment ACLs; describe how you bridge that gap (proxy, OPA, OAuth2-proxy, or a fork). Pick one and justify.
3. The **MinIO bucket-and-credential layout** — bucket-per-tenant with disjoint access keys, single bucket with prefix-scoped IAM policies, or separate MinIO tenancies. Score each on isolation strength, backup ergonomics, and quota enforceability.
4. The **failure mode you are most worried about**, and the smoke test you would run quarterly to prove the isolation still holds. (Hint: the dangerous failure is rarely "tenant A reads tenant B's data on day one"; it is usually "a refactor six months later silently broadens an IAM policy and nobody notices.")

**Defend your design against an adversary.** Assume a curious but non-malicious data scientist on team `pricing` who has full `kubectl` access to the `pricing` namespace. Walk through every API path they could plausibly use to enumerate, read, or modify `fraud` artifacts — the MinIO API, the MLflow REST API, the Kubernetes API, the Feast registry, raw `psycopg2` against the shared Postgres — and explain which control on your design blocks each path. If any path is unblocked, your design is incomplete; iterate until every adversary path terminates in a denial.

The point of this exercise is not to produce a perfect manifest. It is to surface the gap between *plausible-sounding* multi-tenant designs and *actually adversary-resistant* ones — a gap that consumes most platform teams' second year.

## Sources

* [MLflow Tracking Server docs](https://mlflow.org/docs/latest/tracking.html#tracking-server)
* [MLflow artifact stores](https://mlflow.org/docs/latest/ml/tracking/artifact-stores/)
* [Feast architecture and components](https://docs.feast.dev/getting-started/architecture)
* [Feast online stores](https://docs.feast.dev/reference/online-stores)
* [KServe InferenceService architecture](https://kserve.github.io/website/latest/modelserving/control_plane/)
* [KServe canary rollout docs](https://kserve.github.io/website/latest/modelserving/v1beta1/rollout/canary/)
* [Argo Workflows artifact repository docs](https://argo-workflows.readthedocs.io/en/latest/configure-artifact-repository/)
* [Kubeflow Pipelines v2 concepts](https://www.kubeflow.org/docs/components/pipelines/overview/)
* [MinIO Kubernetes documentation](https://min.io/docs/minio/kubernetes/upstream/index.html)
* [LakeFS architecture](https://docs.lakefs.io/understand/architecture.html)
* [OPA Gatekeeper ConstraintTemplates](https://open-policy-agent.github.io/gatekeeper/website/docs/constrainttemplates/)
* [NVIDIA Triton Inference Server user guide](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/)
- [github.com: minio](https://github.com/minio/minio) — The MinIO repository identifies the project and its AGPL-3.0 license; the commercial AIStor naming is vendor-specific and should be checked against MinIO's own materials if the allowlist expands.
- [github.com: releases](https://github.com/iterative/dvc/releases) — The GitHub releases page supports the dated DVC release-line snapshot, and the repository exposes the Apache-2.0 license.
- [github.com: releases](https://github.com/feast-dev/feast/releases) — The Feast GitHub releases and repository license support the version and license; CNCF project status can be checked against the CNCF project index.
- [docs.aws.amazon.com: settings reference.html](https://docs.aws.amazon.com/sdkref/latest/guide/settings-reference.html) — AWS SDK settings documentation covers retry attempts and metadata-service timeout environment variables; the exact observed duration may still vary by SDK configuration.
- [cncf.io: kubeflow brings mlops to the cncf incubator](https://www.cncf.io/blog/2023/07/25/kubeflow-brings-mlops-to-the-cncf-incubator/) — The CNCF announcement directly states Kubeflow's acceptance into the CNCF Incubator on July 25, 2023.
- [kubeflow-pipelines.readthedocs.io: overview.html](https://kubeflow-pipelines.readthedocs.io/en/sdk-2.16.0/source/overview.html) — The KFP SDK documentation describes the v2 IR and compilation model on an allowlisted readthedocs.io host.
- [github.com: trainer](https://github.com/kubeflow/trainer) — The Kubeflow Trainer repository and release notes describe the v2-era Trainer API and the supported runtimes/frameworks.
- [github.com: katib](https://github.com/kubeflow/katib) — Katib's repository and documentation list hyperparameter tuning and supported algorithms; exact release version should be checked against the release page.
- [cncf.io: argo](https://www.cncf.io/projects/argo/) — CNCF's Argo project page states the graduation date; release-specific versions should be validated on the Argo Workflows GitHub releases page.
- [cncf.io: tekton becomes a cncf incubating project](https://www.cncf.io/blog/2026/03/24/tekton-becomes-a-cncf-incubating-project/) — The CNCF announcement supports Tekton's incubation and CDF-to-CNCF transition; check Tekton's release page for the exact pipeline version to install.
- [github.com: kuberay](https://github.com/ray-project/kuberay) — The KubeRay repository identifies the project and releases; CNCF project membership can be checked against the CNCF project index.
- [cncf.io: kserve](https://www.cncf.io/projects/kserve/) — CNCF's KServe project page identifies the project status; KServe's GitHub releases page should be checked for the exact controller version.
- [cncf.io: kserve becomes a cncf incubating project](https://www.cncf.io/blog/2025/11/11/kserve-becomes-a-cncf-incubating-project/) — The CNCF KServe incubation post states the KFServing-to-KServe rebrand, and KServe examples use serving.kserve.io/v1beta1.
- [github.com: releases](https://github.com/triton-inference-server/server/releases) — The Triton GitHub release page supports the dated v2-line snapshot, and Triton backend repositories document supported backends.
- [MLflow GitHub Repository](https://github.com/mlflow/mlflow) — Authoritative source for MLflow releases, license, and top-level platform capabilities.
- [Feast GitHub Repository](https://github.com/feast-dev/feast) — Authoritative source for Feast releases, license, and supported feature-store architecture.

## Next Module

Ready to move from platform assembly into closed-loop operations? Proceed to [Module 9.5: Private AIOps](/on-premises/ai-ml-infrastructure/module-9.5-private-aiops/), where we explore how to monitor, automate, and operate internal AI platforms at scale.
