---
title: "Module 9.11: Bare-Metal MLOps — Building a Production ML Platform Without Managed Cloud"
sidebar:
  order: 12
slug: module-9.11-bare-metal-mlops
---

## Complexity: [COMPLEX]

**Time to Complete**: Plan for 60-70 minutes if you already know Kubernetes fundamentals, and reserve extra time if you want to run the production-realistic lab path.

**Prerequisites**: This capstone assumes you can read Kubernetes manifests, recognize common control-plane and workload failures, and connect storage, networking, GPU, and serving behavior into one operational picture.

- Kubernetes basics with a kubeadm cluster or equivalent
- Module 9.7: GPU Scheduling, because the GPU Operator and MIG appear throughout this module
- At least one serving module: Module 9.8 KServe, Module 9.9 Seldon Core, or Module 9.10 BentoML
- Comfort reading Kubernetes manifests, Helm values, and production troubleshooting output

For command examples, configure the `kubectl` alias once so the later troubleshooting flow stays readable while still using standard Kubernetes commands underneath:

```bash
alias k=kubectl
```

From here on, commands use `k`, and all Kubernetes examples target Kubernetes **1.35+** so API behavior, resource names, and serving assumptions stay consistent across the module.

---

## Learning Outcomes

After completing this module, you will be able to reason about a self-hosted ML platform as a connected system rather than a bag of individually installed tools:

- **Design** a seven-layer bare-metal ML platform that replaces managed-cloud services with Kubernetes-native components.
- **Evaluate** storage, networking, GPU, serving, registry, orchestration, and observability trade-offs for production ML workloads.
- **Implement** a minimal self-hosted MLOps path using MinIO, MLflow, Argo Workflows, KServe, and Prometheus.
- **Diagnose** failures across the request path from ingress to service mesh, transformer, predictor pod, GPU, and response.
- **Compare** bare-metal platform ownership against managed-cloud equivalents and choose when each approach is justified.

---

## Why This Module Matters

A regulated health analytics company had a clean managed-cloud ML workflow on paper.
Training data landed in a cloud object bucket, feature jobs ran in managed notebooks, models were served from a hosted endpoint, and experiment metadata lived inside the provider account.
Then procurement changed one line in the risk register: raw patient data could no longer leave facilities controlled by the company.
The team had six months to bring model training and inference on premises without losing reproducibility, audit trails, or GPU throughput.

Their first attempt was a pile of servers with manually installed CUDA, a shared NAS folder, shell scripts, and a wiki page of deployment steps.
It worked for a demo and collapsed under production pressure.
One training node had a driver mismatch.
Another node wrote checkpoints to local disk that was never backed up.
The model registry was a spreadsheet.
An inference pod got scheduled on the wrong GPU class and started timing out during a clinical scoring run.
The engineering team did not need more enthusiasm for Kubernetes.
They needed an integrated platform recipe.

Bare-metal MLOps is achievable.
It can give you data sovereignty, predictable cost at scale, direct control over GPU placement, and freedom from one cloud provider's ML product lifecycle.
It also moves work back onto your team.
You own the storage layer, load balancer bring-up, CNI policy, GPU operator lifecycle, metrics stack, trace plumbing, and backup story.
This module is the capstone recipe for assembling the tools you have already met into a coherent production platform.

---

## 1. Reference Architecture: The 7-Layer Stack

Bare-metal MLOps starts with a simple truth: managed clouds hide whole platform layers behind one API call.
On bare metal, those layers still exist.
You just choose, install, monitor, upgrade, and back them up yourself.

The goal is not to recreate every managed-cloud feature.
The goal is to build a dependable platform where training jobs, model registries, inference services, and observability all share stable contracts.
Each layer below replaces a managed-cloud capability with an open component that runs in your own cluster.

```text
+----------------------------------------------------------------------------------+
|                    Bare-Metal ML Platform Reference Stack                         |
+----------------------------------------------------------------------------------+
| LAYER 7: Orchestration   Argo Workflows for training pipelines                    |
|                          ArgoCD for GitOps deployments                            |
+----------------------------------------------------------------------------------+
| LAYER 6: Tracking        MLflow self-hosted                                       |
|                          PostgreSQL backend + MinIO artifact root                 |
|                          Optional: Yatai for BentoML, Aim for lightweight teams   |
+----------------------------------------------------------------------------------+
| LAYER 5: Serving         KServe, Seldon Core, BentoML, or a mix by workload       |
+----------------------------------------------------------------------------------+
| LAYER 4: GPU             NVIDIA GPU Operator                                      |
|                          device plugin + DCGM + MIG manager + feature labels      |
+----------------------------------------------------------------------------------+
| LAYER 3: Storage         Longhorn or OpenEBS for block PVCs                       |
|                          MinIO for S3-compatible artifacts and datasets           |
+----------------------------------------------------------------------------------+
| LAYER 2: Networking      Cilium CNI + NetworkPolicy + Hubble                      |
|                          MetalLB for LoadBalancer IPs in L2 or BGP mode           |
+----------------------------------------------------------------------------------+
| LAYER 1: Compute         kubeadm for multi-node production                        |
|                          k3s for single-node, lab, or edge deployments            |
+----------------------------------------------------------------------------------+
```

Layer one is compute.
For production, kubeadm is the conservative choice because it keeps you close to upstream Kubernetes behavior.
For small labs or edge inference, k3s can be appropriate because it lowers the operational footprint.
The decision is not about which project is more modern.
It is about whether you need multi-node control-plane rigor, strict addon selection, and explicit upgrade control.

Layer two is networking.
Cloud clusters usually hand you a managed CNI and a managed load balancer.
On bare metal, Cilium gives you Kubernetes networking, policy enforcement, observability through Hubble, and an optional lower-overhead service mesh path.
MetalLB gives services a real `LoadBalancer` IP from your local network.
Without MetalLB or an equivalent, many ML serving examples silently stop being realistic because there is no external endpoint to hit.

Layer three is storage.
MinIO gives you S3-compatible object storage for artifacts, datasets, and model binaries.
Longhorn or OpenEBS gives you replicated block volumes for PostgreSQL, MLflow metadata, and training checkpoints that benefit from filesystem semantics.
Do not treat object and block storage as interchangeable.
They solve different failure and access patterns.

Layer four is GPU.
Managed GPU node pools often arrive with drivers and device plugin wiring.
Bare-metal nodes do not.
The NVIDIA GPU Operator is the practical default because it manages drivers, the container toolkit, device plugin, DCGM exporter, GPU feature discovery, and MIG manager as one lifecycle.

Layer five is serving.
KServe is a strong default for Kubernetes-native `InferenceService` resources, autoscaling, canary traffic, and model storage integration.
Seldon Core fits teams that need graph-style inference pipelines and richer production inference compositions.
BentoML fits teams that package model code as a service artifact and want strong developer ergonomics.
A real platform may run more than one serving layer.
That is acceptable if each has a clear use case.

Layer six is tracking.
MLflow gives a common registry and experiment tracker that works across many frameworks.
The important bare-metal pattern is PostgreSQL for metadata and MinIO for artifacts.
Yatai is worth considering when BentoML is the dominant serving path.
Aim is a leaner option when a team needs experiment tracking without a full registry workflow.

Layer seven is orchestration.
Argo Workflows handles training and registration pipelines.
ArgoCD handles GitOps deployment of platform services and inference manifests.
Together they make the platform reproducible.
Training logic, serving configuration, and rollout policy become reviewable changes in Git rather than hand-edited cluster state.

| Platform Layer | Bare-Metal Component | Managed-Cloud Equivalent | Why This Choice Works | What You Own |
|---|---|---|---|---|
| Compute | kubeadm or k3s | EKS, GKE, AKS | Direct control over nodes, versions, and GPU hosts | Control-plane upgrades and node repair |
| Networking | Cilium + MetalLB | VPC CNI + cloud load balancer | Policy, observability, and real external IPs without cloud LB APIs | IP pools, BGP or L2 design, ingress routing |
| Block storage | Longhorn or OpenEBS | EBS, Persistent Disk, Azure Disk | Replicated PVCs for databases and checkpoints | Disk health, replicas, restore drills |
| Object storage | MinIO | S3, GCS, Azure Blob | S3-compatible model and artifact API on premises | Erasure coding, bucket policy, replication |
| GPU lifecycle | NVIDIA GPU Operator | Managed GPU node image | Full driver, device plugin, DCGM, MIG lifecycle | Operator upgrades and host compatibility |
| Serving | KServe, Seldon Core, BentoML | SageMaker Endpoints, Vertex AI Endpoints, Azure ML Online Endpoints | Portable serving abstractions on Kubernetes | Runtime images, scaling, ingress, rollout policy |
| Tracking | MLflow self-hosted | SageMaker Experiments, Vertex ML Metadata, Azure ML registry | Open registry and experiment metadata across tools | Database, artifact storage, auth, backups |
| Pipelines | Argo Workflows | SageMaker Pipelines, Vertex Pipelines | Native Kubernetes workflows with GPU scheduling | Workflow controller and artifact repository |
| GitOps | ArgoCD | CodePipeline, Cloud Build, Azure DevOps release | Declarative platform and model deployments | Repository layout, sync order, drift response |
| Observability | kube-prometheus-stack, Loki, Tempo | CloudWatch, Cloud Monitoring, Azure Monitor | Unified metrics, logs, traces in your cluster | Retention, dashboards, alert routing |

The table is intentionally blunt.
Bare metal does not remove platform complexity.
It changes who pays the complexity bill.
You choose bare metal when control, sovereignty, or scale economics matter more than managed convenience.

The architectural habit to build early is dependency mapping. A serving outage may look like a KServe problem while the real fault is a MinIO credential, a MetalLB announcement, a Cilium policy, or a GPU runtime mismatch. When each layer has a documented owner and a small set of health checks, incident response becomes a sequence of falsifiable tests instead of a debate about which tool is probably guilty.
Those checks should live beside the platform runbooks and be rehearsed before production traffic and planned upgrades arrive.

**Worked example: choosing the serving mix** The scenario below shows why a platform can support more than one serving path without becoming incoherent, provided each path has a clear workload boundary and shares the same registry and artifact contracts.

A manufacturing company runs two ML families.
Computer-vision defect detection uses Triton and needs GPU-aware canaries.
Internal tabular models are small Python services maintained by data scientists.
The platform team can run KServe for the Triton path and BentoML for the Python path, both backed by the same MinIO artifact store and the same MLflow registry.
That is cleaner than forcing all workloads into one serving abstraction.

**Active learning prompt:** Pause and predict: if MinIO is reachable from MLflow but not from KServe, which layer is probably broken first: storage, networking, serving configuration, or model registry?
Write down two commands you would run before reading ahead.

---

## 2. Storage Discipline: Artifacts, Models, Backups

Storage discipline is the difference between a platform and a folder full of files.
ML workloads produce datasets, checkpoints, feature extracts, trained model artifacts, container images, registry metadata, evaluation reports, and serving manifests.
Each object has a different access pattern.
Treating them all as "files somewhere" creates failures that are hard to debug.

MinIO should be the default artifact layer.
It exposes an S3-compatible API, which means MLflow, Argo Workflows, KServe storage initializers, Python clients, and data tooling can all speak the same protocol.
That common protocol matters more than convenience.
It keeps a training pipeline from writing to one storage system while serving expects another.

Longhorn or OpenEBS should be the default block layer.
PostgreSQL needs a real filesystem and predictable block behavior.
Training checkpoints can also benefit from block storage when jobs write frequent sequential snapshots during long runs.
If a training job writes a large checkpoint every few minutes, a PVC mounted close to the workload may be better than object storage calls for every update.

| Workload | Prefer MinIO | Prefer Longhorn or OpenEBS |
|---|---|---|
| Final model artifacts | Yes, easy to share across tools | Only for temporary staging |
| MLflow artifacts | Yes, standard artifact root | No, unless MLflow is single-node only |
| PostgreSQL data | No | Yes, database storage belongs on block |
| Training checkpoints | Sometimes, for less frequent durable checkpoints | Yes, for frequent checkpoint writes |
| Shared datasets | Yes, especially read-many datasets | No, unless POSIX access is required |
| Argo artifacts | Yes, object artifact repository | No, except for local scratch volumes |
| KServe model loading | Yes, `s3://` model paths are natural | No, avoid tying serving to one node volume |

Versioning also needs discipline.
MinIO bucket versioning tracks object changes.
MLflow model versions track model lifecycle metadata.
They are related but not substitutes.
Use MinIO versioning to recover object-level mistakes.
Use MLflow model versions and aliases to express model identity, lineage, and promotion state.

A practical storage rule is to place each artifact where its access pattern and failure mode make sense, then document that rule before teams create their own exceptions under delivery pressure:

- Put raw run artifacts, metrics exports, model binaries, and evaluation outputs in MinIO.
- Put experiment metadata, model version records, aliases, and run lineage in MLflow PostgreSQL.
- Put database data, workflow controller data, and high-write checkpoint volumes on Longhorn or OpenEBS.
- Put release intent in Git, not in a bucket or a notebook.

Pruning policies prevent storage from becoming a hidden tax.
Experiment runs can generate thousands of intermediate artifacts.
Set lifecycle policies for old scratch artifacts.
Archive stale MLflow model versions instead of deleting them immediately.
Keep promoted model artifacts longer than failed experiment artifacts.
Retention should reflect audit needs, not just disk pressure.

Backups must cover both metadata and objects.
A Velero backup that captures only Kubernetes manifests is not enough if MinIO buckets contain your actual models.
A MinIO bucket backup without PostgreSQL is also incomplete because the registry loses lineage and version state.
For production, combine Velero for cluster resources, scheduled PostgreSQL backups, and cross-cluster MinIO replication for disaster recovery.

Restore testing is where storage designs become honest. Practice restoring an MLflow run, its registered model version, the referenced artifact object, and the serving manifest into a clean namespace or secondary cluster. If those pieces cannot be reconnected without a tribal-memory checklist, the platform is not yet auditable. A good restore drill should prove both data recovery and operational interpretation, including which model version should receive traffic after recovery.

MinIO can be installed as a standalone deployment for a lab, but the MinIO Operator is a better production base.
The operator manages tenant resources, pools, certificates, and tenant-level isolation.
For multi-tenant ML platforms, give each team a bucket or tenant model that matches your governance needs.
Shared object storage is convenient, but shared credentials are a common source of audit pain.

### Minimal MinIO Tenant Example

This example is intentionally compact.
For production, increase server count, disk count, storage class, TLS configuration, and network policy.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ml-storage
---
apiVersion: v1
kind: Secret
metadata:
  name: minio-root
  namespace: ml-storage
type: Opaque
stringData:
  config.env: |
    export MINIO_ROOT_USER=minio-admin
    export MINIO_ROOT_PASSWORD=your-minio-root-password-here
---
apiVersion: minio.min.io/v2
kind: Tenant
metadata:
  name: ml-artifacts
  namespace: ml-storage
spec:
  configuration:
    name: minio-root
  pools:
    - name: pool-0
      servers: 1
      volumesPerServer: 2
      volumeClaimTemplate:
        metadata:
          name: data
        spec:
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: 200Gi
          storageClassName: longhorn
  buckets:
    - name: mlflow-artifacts
    - name: training-datasets
    - name: kserve-models
  requestAutoCert: false
```

Apply the operator first, then apply the tenant, because the tenant custom resource depends on the operator controllers and CRDs being present before Kubernetes can reconcile storage pools:

```bash
helm repo add minio-operator https://operator.min.io
helm repo update
helm upgrade --install minio-operator minio-operator/operator \
  --namespace minio-operator \
  --create-namespace

k apply -f minio-tenant.yaml
k get tenant -n ml-storage
k get pods -n ml-storage
```

### MLflow Artifact Root Pointing to MinIO

MLflow needs a metadata backend and an artifact root.
PostgreSQL stores experiments, runs, registered models, versions, aliases, and lifecycle state.
MinIO stores the artifact bytes.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mlflow-s3
  namespace: ml-platform
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: minio-admin
  AWS_SECRET_ACCESS_KEY: your-minio-root-password-here
  MLFLOW_S3_ENDPOINT_URL: http://ml-artifacts-hl.ml-storage.svc.cluster.local:9000
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow-tracking
  namespace: ml-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mlflow-tracking
  template:
    metadata:
      labels:
        app: mlflow-tracking
    spec:
      containers:
        - name: mlflow
          image: ghcr.io/mlflow/mlflow:v2.22.0
          envFrom:
            - secretRef:
                name: mlflow-s3
          command:
            - mlflow
          args:
            - server
            - --host=0.0.0.0
            - --port=5000
            - --backend-store-uri=postgresql://mlflow:your-db-password-here@mlflow-postgresql.ml-platform.svc.cluster.local:5432/mlflow
            - --default-artifact-root=s3://mlflow-artifacts
          ports:
            - name: http
              containerPort: 5000
```

Notice the separation.
The deployment does not store model files on its own filesystem.
If the pod restarts, model artifacts remain in MinIO and registry state remains in PostgreSQL.

---

## 3. GPU Scheduling on Bare Metal

GPU scheduling on bare metal is not just "install the device plugin."
The device plugin only advertises GPU resources to kubelet.
Production GPU nodes also need drivers, the NVIDIA container toolkit, monitoring, feature labels, and optional MIG configuration.
Managed clouds often bake some of that into node images.
On your own servers, you must own it.

The NVIDIA GPU Operator is the production default because it manages the full GPU software stack.
It installs and reconciles the driver, container toolkit, device plugin, DCGM exporter, GPU Feature Discovery, and MIG manager.
That matters during upgrades.
A manual driver update on one node can make scheduling appear normal while workloads fail at runtime.
The operator gives you one control plane for the node GPU lifecycle.

### GPU Operator Install

```bash
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

helm upgrade --install gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --create-namespace \
  --set driver.enabled=true \
  --set toolkit.enabled=true \
  --set devicePlugin.enabled=true \
  --set dcgmExporter.enabled=true \
  --set migManager.enabled=true \
  --set gfd.enabled=true

k get pods -n gpu-operator
k describe node gpu-node-a | grep -E 'nvidia.com/gpu|nvidia.com/gpu.product'
```

MIG, or Multi-Instance GPU, is available on supported data-center GPUs such as A100 and H100 families.
It partitions one physical GPU into isolated GPU instances with their own memory and compute slices.
MIG is ideal for predictable inference and smaller training jobs because it gives stronger isolation than software time-slicing.

The GPU Operator supports MIG strategies.
`single` means a node exposes one MIG layout consistently.
`mixed` means a node can advertise different MIG profiles at the same time.
Use `single` when you want simpler scheduling and easier capacity planning.
Use `mixed` when platform utilization matters more and your scheduler policies are mature.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: custom-mig-parted-config
  namespace: gpu-operator
data:
  config.yaml: |
    version: v1
    mig-configs:
      all-1g.10gb:
        - devices: all
          mig-enabled: true
          mig-devices:
            "1g.10gb": 7
      balanced-inference:
        - devices: all
          mig-enabled: true
          mig-devices:
            "2g.20gb": 2
            "1g.10gb": 3
```

Apply a label to choose the desired MIG layout for a node, then watch the state label because MIG reconfiguration changes real accelerator capacity and can disrupt workloads:

```bash
k label node gpu-node-a nvidia.com/mig.config=balanced-inference --overwrite
k get node gpu-node-a -o jsonpath='{.metadata.labels.nvidia\.com/mig\.config\.state}'
```

Consumer GPUs such as RTX 3090 and RTX 4090 do not support MIG.
For those nodes, time-slicing can improve utilization for inference and development workloads.
Time-slicing shares a GPU across multiple pods through software scheduling.
It does not provide the same memory isolation as MIG, so use it for lower-criticality workloads and set expectations with users.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: gpu-time-slicing
  namespace: gpu-operator
data:
  any: |-
    version: v1
    sharing:
      timeSlicing:
        renameByDefault: false
        resources:
          - name: nvidia.com/gpu
            replicas: 4
```

Multiple GPU models in one cluster are normal.
The platform may have A100 nodes for training, V100 nodes for batch inference, and L4 nodes for lower-cost online inference.
Do not rely only on `nvidia.com/gpu: 1`.
Use node labels such as `nvidia.com/gpu.product` to steer workloads to the right hardware.

Admission control is the next maturity step after labels. Without it, a team can accidentally request a generic GPU and consume premium training hardware for a lightweight notebook or low-priority inference service. A validating policy can require approved GPU product selectors, namespace-specific quotas, and workload labels before pods reach the scheduler. That keeps placement discipline from depending on everyone remembering the same convention during a release.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: train-resnet-a100
  namespace: ml-training
spec:
  backoffLimit: 2
  template:
    spec:
      restartPolicy: Never
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: nvidia.com/gpu.product
                    operator: In
                    values:
                      - NVIDIA-A100-SXM4-80GB
      containers:
        - name: trainer
          image: ghcr.io/example/ml-trainer:1.0.0
          command:
            - python
            - train.py
          resources:
            limits:
              nvidia.com/gpu: 1
            requests:
              cpu: "8"
              memory: 32Gi
```

DCGM monitoring closes the loop.
DCGM exporter surfaces GPU utilization, memory use, temperature, power, error counters, and interconnect metrics where available.
Prometheus scrapes those metrics.
Grafana turns them into questions your team can answer quickly:

- Which GPU nodes are hot but idle?
- Which inference service is leaking GPU memory?
- Which training jobs reserve A100s but show near-zero utilization?
- Which nodes show ECC or XID errors before workloads fail?

Sample GPU dashboard panels should tie device behavior back to pods, namespaces, and owners, because raw accelerator metrics are much less useful when nobody can identify the workload causing them:

| Panel | PromQL Direction |
|---|---|
| GPU utilization by pod | `avg by (pod, gpu) (DCGM_FI_DEV_GPU_UTIL)` |
| GPU memory used | `avg by (pod, gpu) (DCGM_FI_DEV_FB_USED)` |
| GPU temperature | `max by (Hostname, gpu) (DCGM_FI_DEV_GPU_TEMP)` |
| GPU power draw | `avg by (Hostname, gpu) (DCGM_FI_DEV_POWER_USAGE)` |
| GPU error events | `increase(DCGM_FI_DEV_XID_ERRORS[5m])` |

**Active learning prompt:** Which GPU policy would you choose for a mixed cluster with A100 training nodes and RTX 4090 development nodes: MIG, time-slicing, strict node affinity, or a combination?
Explain the failure you are trying to prevent.

---

## 4. Self-Hosted Model Registry

A model registry is not just a file store.
Operationally, it is evidence.
It is the system that answers "which model did we train, from which data, with which parameters, under which run, and why is this version serving traffic?"
On bare metal, MLflow is a practical default because it separates experiment tracking, artifact storage, and model registry concepts while staying portable.

The production layout separates state, credentials, and traffic paths so the tracking server can be rescheduled without losing lineage or forcing teams to rebuild training images:

- MLflow tracking server as a Kubernetes deployment or Helm release.
- PostgreSQL as the backend store.
- MinIO as the artifact root.
- Kubernetes Secrets for database credentials and object storage credentials.
- Ingress or internal service exposure based on team access needs.

CloudNativePG is a strong production PostgreSQL option when you want operator-managed backups and failover.
A plain PostgreSQL Helm chart is acceptable for a learning environment.
The important design point is that the MLflow pod is stateless.
It can be rescheduled without losing experiments or artifacts.

### MLflow Helm Values

The exact chart keys vary by chart, but the shape below is the pattern you should preserve.
It uses PostgreSQL for metadata and MinIO for artifacts.

```yaml
tracking:
  enabled: true
  service:
    type: ClusterIP
    port: 5000
  extraEnvVars:
    - name: MLFLOW_S3_ENDPOINT_URL
      value: http://ml-artifacts-hl.ml-storage.svc.cluster.local:9000
    - name: AWS_ACCESS_KEY_ID
      valueFrom:
        secretKeyRef:
          name: mlflow-s3
          key: AWS_ACCESS_KEY_ID
    - name: AWS_SECRET_ACCESS_KEY
      valueFrom:
        secretKeyRef:
          name: mlflow-s3
          key: AWS_SECRET_ACCESS_KEY
  backendStoreUri: postgresql://mlflow:your-db-password-here@mlflow-postgresql.ml-platform.svc.cluster.local:5432/mlflow
  defaultArtifactRoot: s3://mlflow-artifacts

postgresql:
  enabled: true
  auth:
    username: mlflow
    password: your-db-password-here
    database: mlflow
  primary:
    persistence:
      enabled: true
      storageClass: longhorn
      size: 100Gi
```

### MLflow Credentials Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mlflow-client-env
  namespace: ml-training
type: Opaque
stringData:
  MLFLOW_TRACKING_URI: http://mlflow-tracking.ml-platform.svc.cluster.local:5000
  MLFLOW_TRACKING_USERNAME: your-mlflow-user
  MLFLOW_TRACKING_PASSWORD: your-mlflow-password
  MLFLOW_S3_ENDPOINT_URL: http://ml-artifacts-hl.ml-storage.svc.cluster.local:9000
  AWS_ACCESS_KEY_ID: minio-admin
  AWS_SECRET_ACCESS_KEY: your-minio-root-password-here
```

Training jobs should not hard-code registry endpoints.
Inject them from Kubernetes Secrets or ConfigMaps.
That keeps the same image portable between a local lab, staging cluster, and production cluster.

### Training Job Logging to Self-Hosted MLflow

```python
import os

import mlflow
import mlflow.sklearn
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
mlflow.set_experiment("bare-metal-iris")

data = load_iris()
x_train, x_test, y_train, y_test = train_test_split(
    data.data,
    data.target,
    test_size=0.2,
    random_state=35,
)

with mlflow.start_run(run_name="iris-random-forest") as run:
    model = RandomForestClassifier(n_estimators=120, max_depth=5, random_state=35)
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    accuracy = accuracy_score(y_test, predictions)

    mlflow.log_param("n_estimators", 120)
    mlflow.log_param("max_depth", 5)
    mlflow.log_metric("accuracy", accuracy)

    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="model",
        registered_model_name="iris-bare-metal",
    )

    print(f"registered iris-bare-metal from run {run.info.run_id}")
```

MLflow 2.x supports model versions, stages in older workflows, and aliases in modern workflows.
Aliases are useful because serving manifests can point to a semantic name such as `champion` or `candidate` instead of embedding a numeric version everywhere.
For regulated deployments, keep the immutable model version in the manifest or release metadata as well.
Semantic aliases help humans.
Immutable versions help audits.

Yatai is the alternative when BentoML dominates your platform.
If most services are Bento packages and your teams already use BentoML's build and serve workflow, Yatai gives a registry and deployment model aligned to Bento artifacts.
Choose Yatai when packaging and serving ergonomics matter more than general framework-neutral experiment tracking.

Aim is the lightweight alternative.
It is useful for teams that need fast experiment tracking and comparisons but do not need a full promotion workflow.
Aim can be a good early-stage tool, but a platform serving production traffic usually needs a clearer registry and deployment handshake.

The model promotion workflow should be explicit because the registry proves what was produced, while Git and the deployment controller prove what the platform intentionally serves:

```text
Training job
  -> logs metrics and artifacts to MLflow
  -> registers a model version
  -> evaluation job compares candidate against policy
  -> human or automated approval updates Git
  -> ArgoCD syncs new InferenceService or runtime config
  -> KServe rolls out the new model version
```

Do not let a training job directly mutate production serving resources.
That shortcut feels fast until a bad model reaches users without review.
The registry records what exists.
Git records what should run.
ArgoCD reconciles the cluster to that desired state.

---

## 5. CI/CD for ML on Bare Metal

ML CI/CD is different from application CI/CD because the artifact is not only a container image.
The release includes training code, data references, parameters, evaluation metrics, model files, serving runtime configuration, and rollout policy.
Bare metal does not change that.
It makes the automation more important because you cannot lean on a cloud ML product to glue the pieces together.

Argo Workflows is a good fit for training pipelines because it runs native Kubernetes pods.
A workflow step can request GPUs, mount PVCs, read and write MinIO artifacts, and retry on node-level failures.
DAG templates are best when independent steps can run in parallel.
Steps templates are simpler when the pipeline is mostly linear.

ArgoCD is the deployment controller.
It syncs platform components and inference manifests from Git.
Use sync waves so dependencies appear in order.
For example, storage comes before MLflow, MLflow comes before training workflows, and serving runtimes come before `InferenceService` objects.

```text
+------------------+       +------------------+       +------------------+
| Git: training    | ----> | ArgoCD syncs     | ----> | Argo Workflow    |
| workflow YAML    |       | workflow object  |       | trains model     |
+------------------+       +------------------+       +------------------+
                                                           |
                                                           v
+------------------+       +------------------+       +------------------+
| Git: serving     | <---- | promotion job    | <---- | MLflow registry  |
| manifest update  |       | opens PR         |       | new version      |
+------------------+       +------------------+       +------------------+
         |
         v
+------------------+       +------------------+       +------------------+
| ArgoCD syncs     | ----> | KServe rollout   | ----> | Prometheus and   |
| InferenceService |       | with canary      |       | Grafana observe  |
+------------------+       +------------------+       +------------------+
```

Tekton is the main alternative.
Choose Tekton when your organization already uses it for application delivery and wants one pipeline model for code, containers, and models.
Choose Argo Workflows when data and ML teams need Kubernetes-native DAGs, artifact passing, and simple workflow submission.
Both can work.
The platform should avoid running two pipeline systems unless there is a clear team boundary.

### Argo Workflow: Train and Register Iris Model

This workflow uses MinIO as the artifact repository and MLflow as the registry.
In production, package the Python script into a reviewed image instead of using inline shell.
For a learning lab, the inline script makes the integration visible.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: iris-train-register-
  namespace: ml-training
spec:
  entrypoint: train-register
  serviceAccountName: argo-workflow
  arguments:
    parameters:
      - name: model-name
        value: iris-bare-metal
  templates:
    - name: train-register
      dag:
        tasks:
          - name: train
            template: train
          - name: register
            dependencies:
              - train
            template: register
            arguments:
              artifacts:
                - name: model
                  from: "{{tasks.train.outputs.artifacts.model}}"
    - name: train
      retryStrategy:
        limit: 2
        retryPolicy: Always
      container:
        image: ghcr.io/example/sklearn-mlflow-trainer:1.0.0
        command:
          - bash
          - -lc
        args:
          - |
            python /app/train.py --output /tmp/model
        envFrom:
          - secretRef:
              name: mlflow-client-env
        resources:
          requests:
            cpu: "2"
            memory: 4Gi
          limits:
            nvidia.com/gpu: 1
      outputs:
        artifacts:
          - name: model
            path: /tmp/model
            s3:
              endpoint: ml-artifacts-hl.ml-storage.svc.cluster.local:9000
              bucket: mlflow-artifacts
              key: workflows/{{workflow.name}}/model
              insecure: true
              accessKeySecret:
                name: mlflow-client-env
                key: AWS_ACCESS_KEY_ID
              secretKeySecret:
                name: mlflow-client-env
                key: AWS_SECRET_ACCESS_KEY
    - name: register
      inputs:
        artifacts:
          - name: model
            path: /tmp/model
      container:
        image: ghcr.io/example/sklearn-mlflow-trainer:1.0.0
        command:
          - bash
          - -lc
        args:
          - |
            python /app/register.py \
              --model-dir /tmp/model \
              --model-name "{{workflow.parameters.model-name}}"
        envFrom:
          - secretRef:
              name: mlflow-client-env
        resources:
          requests:
            cpu: "1"
            memory: 2Gi
```

GPU workflow templates should request GPUs only in the steps that need them.
Do not put `nvidia.com/gpu` on a registration or evaluation step unless it genuinely uses GPU compute.
That mistake turns your most expensive nodes into general-purpose runners.

### ArgoCD Application for Inference Services

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ml-inference-services
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "30"
spec:
  project: default
  source:
    repoURL: https://github.com/example/ml-platform-gitops.git
    targetRevision: main
    path: inference/kserve
  destination:
    server: https://kubernetes.default.svc
    namespace: ml-serving
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

Canary deployments are where the integration becomes valuable.
KServe supports traffic splitting between predictor revisions.
Argo Rollouts can add richer analysis and automated rollback if your organization already uses it.
The key is to connect rollout decisions to metrics, not hope.
If p99 latency or error rate breaches the SLO during a canary, the rollout should stop before full promotion.

---

## 6. Observability Stack on Bare Metal

Managed ML platforms usually arrive with a metrics and logging story.
Bare-metal platforms need one installed on purpose.
For Kubernetes, `kube-prometheus-stack` is the right starting point because it installs Prometheus, Alertmanager, Grafana, node-exporter, kube-state-metrics, and the Prometheus Operator.
That gives you the control plane for metrics collection and alert rules.

Metrics answer "what is happening?"
Logs answer "what did this process say?"
Traces answer "where did time go?"
For ML serving, you need all three.
A slow inference request may be caused by ingress queueing, transformer validation, model runtime latency, GPU memory pressure, or object storage fetches during cold start.
One signal rarely explains the whole path.

ServiceMonitors are the bridge between Kubernetes services and Prometheus scraping.
KServe, Seldon, and BentoML can expose Prometheus metrics.
Make the metric endpoint and labels consistent across serving runtimes so dashboards can compare them.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kserve-predictor-metrics
  namespace: monitoring
  labels:
    release: kube-prometheus-stack
spec:
  namespaceSelector:
    matchNames:
      - ml-serving
  selector:
    matchLabels:
      serving.kserve.io/inferenceservice: iris-bare-metal
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
      scrapeTimeout: 10s
```

GPU dashboards should come from DCGM exporter metrics.
Start with utilization, memory used, temperature, power, and XID errors.
Then add team and workload labels so you can connect utilization to cost accountability.
A GPU panel that cannot identify the owning namespace is a pretty graph, not an operational tool.

```json
{
  "title": "GPU Utilization by Pod",
  "type": "timeseries",
  "targets": [
    {
      "expr": "avg by (namespace, pod, gpu) (DCGM_FI_DEV_GPU_UTIL)",
      "legendFormat": "{{namespace}}/{{pod}} gpu={{gpu}}"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "percent",
      "min": 0,
      "max": 100
    }
  }
}
```

Loki adds log aggregation.
Deploy promtail as a DaemonSet and use labels intentionally.
At minimum, include namespace, pod, container, app, model name, model version, and workload type.
For training jobs, include workflow name and step name.
For inference, include serving runtime and `InferenceService` name.

A useful Loki query pattern starts with stable labels and then narrows to structured error text, which keeps incident response fast without requiring broad log searches across every workload:

```text
{namespace="ml-serving", model_name="iris-bare-metal"} |= "error" | json
```

Tempo adds distributed tracing.
OpenTelemetry instrumentation in transformers and custom predictors lets you follow a request across the path.
The best developer experience is inside Grafana:
click a slow Prometheus exemplar, open the trace in Tempo, then jump to Loki logs for the same pod and request ID.

Alert on symptoms users feel and resources operators can act on, then keep lower-level signals available for diagnosis rather than paging on every noisy internal fluctuation:

- Inference p99 latency is above the service objective.
- Model error rate spikes after a deployment.
- GPU memory utilization stays above 90 percent.
- GPU utilization is near zero while jobs are pending.
- MinIO disk usage exceeds 80 percent.
- MLflow backend database has replication or backup failures.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: ml-serving-slo
  namespace: monitoring
  labels:
    release: kube-prometheus-stack
spec:
  groups:
    - name: ml-serving.rules
      rules:
        - alert: KServeLatencySLOBreach
          expr: |
            histogram_quantile(
              0.99,
              sum by (le, namespace, service) (
                rate(revision_app_request_latencies_bucket{namespace="ml-serving"}[5m])
              )
            ) > 1.5
          for: 10m
          labels:
            severity: page
          annotations:
            summary: "KServe p99 latency is above SLO"
            description: "Service {{ $labels.service }} in {{ $labels.namespace }} has p99 latency above 1.5 seconds for 10 minutes."
```

**Active learning prompt:** Before adding a new alert, ask what action an on-call engineer should take when it fires.
If the answer is "look around," the alert is probably too vague.

---

## 7. Networking and Ingress on Bare Metal

Networking is where many bare-metal ML platforms lose production realism.
Inside a managed cloud, a `Service` of type `LoadBalancer` usually triggers an external load balancer.
Inside a bare-metal cluster, nothing magical happens unless you install a load-balancer implementation.
MetalLB fills that gap.

MetalLB has two common modes.
L2 mode is simple.
It works well in single-switch or lab environments where one node announces ownership of a service IP on the local network.
BGP mode is the production path when you have routers that can peer with MetalLB speakers.
BGP enables better failover behavior and equal-cost multipath routing when your network supports it.

```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: ml-platform-pool
  namespace: metallb-system
spec:
  addresses:
    - 192.168.20.240-192.168.20.250
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: ml-platform-l2
  namespace: metallb-system
spec:
  ipAddressPools:
    - ml-platform-pool
```

Cilium should be viewed as more than the pod network.
It provides network policy, service visibility, Hubble flow inspection, and a service mesh option that does not require classic sidecars for every workload.
That matters for GPU-bound inference pods where every extra container, hop, and memory overhead deserves scrutiny.

Use internal and external endpoints intentionally.
MinIO, PostgreSQL, and MLflow backend traffic should usually be internal `ClusterIP` traffic.
Public inference APIs should pass through ingress with authentication.
Training jobs should reach MinIO and MLflow internally.
Users should not need direct database access to inspect an experiment.

TLS termination belongs at the edge for public endpoints.
Use cert-manager with Let's Encrypt when endpoints are public and routable.
Use an internal CA for private service-to-service trust.
If you enable Cilium service mesh features, decide which namespaces require mutual TLS and test latency impact under inference load.

### Ingress NGINX for a KServe Endpoint with JWT Auth

This example routes a public host to a KServe local gateway service and delegates authentication to an OAuth2 proxy endpoint.
Adapt the service name to your KServe installation mode.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: iris-bare-metal
  namespace: ml-serving
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/auth-url: "https://auth.example.com/oauth2/auth"
    nginx.ingress.kubernetes.io/auth-signin: "https://auth.example.com/oauth2/start?rd=$escaped_request_uri"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "120"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "120"
spec:
  tls:
    - hosts:
        - iris.example.com
      secretName: iris-example-tls
  rules:
    - host: iris.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: kserve-local-gateway
                port:
                  number: 80
```

### Cilium Network Policy for Team Isolation

This policy lets inference pods receive ingress traffic from ingress-nginx and talk to MinIO and MLflow.
It blocks casual cross-namespace access from other teams.

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: ml-serving-isolation
  namespace: ml-serving
spec:
  endpointSelector:
    matchLabels:
      workload-type: inference
  ingress:
    - fromEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: ingress-nginx
      toPorts:
        - ports:
            - port: "8080"
              protocol: TCP
  egress:
    - toEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: ml-storage
      toPorts:
        - ports:
            - port: "9000"
              protocol: TCP
    - toEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: ml-platform
      toPorts:
        - ports:
            - port: "5000"
              protocol: TCP
```

Multi-tenancy is mostly a policy discipline.
Use namespaces per team.
Give teams RBAC to create `InferenceService` resources only in their namespace.
Give platform engineers ownership of cluster-scoped serving runtimes, GPU operator settings, MetalLB pools, and storage operators.
Do not let every team define its own ingress and object storage credential pattern.
That is how a platform becomes a collection of exceptions.

Network design also needs a change-management habit. Adding a model endpoint is not just a YAML apply; it consumes an address, a certificate, a route, an authentication rule, and egress permissions to internal services. Review those changes together so a public endpoint cannot accidentally expose MLflow, bypass authentication, or use a broad MinIO credential. Bare metal gives you freedom from cloud load-balancer APIs, but it does not remove the need for careful edge governance.

---

## 8. End-to-End Request Traceability

The final test of a production ML platform is whether you can explain one request.
Not the average request.
One specific request.
Where did it enter?
Which model version handled it?
Which pod ran it?
How long did transformation take?
Was the GPU saturated?
Did the response error come from validation, runtime, or ingress?

```text
Client
  -> Ingress NGINX
  -> Cilium or Istio service path
  -> KServe ingress gateway
  -> Transformer
  -> Predictor pod
  -> GPU runtime such as Triton or custom Python
  -> Response
```

At each hop, emit three kinds of data.
Trace spans describe timing and parent-child relationships.
Structured logs describe events with fields humans and machines can query.
Metrics describe aggregate behavior over time.

The traceability design should be part of the service contract, not an afterthought added during an outage. Platform teams can provide common libraries or sidecar-free instrumentation templates, but model teams still need to supply model names, versions, input-size summaries, and validation outcomes. The goal is a request record that is specific enough to debug and audit, yet careful enough to avoid storing sensitive payloads in observability systems.

| Hop | Trace Span | Structured Log Fields | Metrics | Failure Modes |
|---|---|---|---|---|
| Client | client request span | request_id, model_name, input_bytes | client latency histogram | timeout, retry storm |
| Ingress | ingress route span | request_id, host, status, latency_ms | request count, status codes | auth failure, body too large |
| Service path | mesh forwarding span | source, destination, policy verdict | flow count, drops | policy deny, DNS failure |
| KServe gateway | route to revision span | inference_service, revision, status | revision latency | wrong host, cold start |
| Transformer | validation and transform spans | request_id, model_version, input_tokens, output_bytes | transform latency, validation errors | schema mismatch, payload issue |
| Predictor | predict span | request_id, model_version, runtime, latency_ms | inference latency, error counter | model load error, runtime exception |
| GPU | runtime child span where possible | gpu_uuid, memory_mb, batch_size | GPU utilization, memory, temperature | OOM kill, memory leak, XID error |
| Response | response serialization span | request_id, status, output_bytes | response latency | serialization error, client disconnect |

Use a generated request ID if the client does not send one.
Propagate it through headers, logs, and trace attributes.
For sensitive workloads, log sizes, schema names, model metadata, and validation results rather than raw payloads.
Traceability should help debug production without leaking private data into logs.

### OpenTelemetry in a Custom KServe Transformer

```python
import json
import logging
import time
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


resource = Resource.create(
    {
        "service.name": "iris-transformer",
        "deployment.environment": "production",
    }
)
provider = TracerProvider(resource=resource)
provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(endpoint="http://tempo-distributor.monitoring.svc.cluster.local:4317")
    )
)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)
logger = logging.getLogger("iris-transformer")


def transform(request: dict[str, Any]) -> dict[str, Any]:
    request_id = request.get("headers", {}).get("x-request-id", "generated-request-id")
    model_name = "iris-bare-metal"
    model_version = "1"
    start = time.perf_counter()

    with tracer.start_as_current_span("transform.iris") as span:
        instances = request["instances"]
        span.set_attribute("request.id", request_id)
        span.set_attribute("model.name", model_name)
        span.set_attribute("model.version", model_version)
        span.set_attribute("input.records", len(instances))

        transformed = {"instances": instances}
        latency_ms = (time.perf_counter() - start) * 1000

        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "model_name": model_name,
                    "model_version": model_version,
                    "latency_ms": round(latency_ms, 2),
                    "input_bytes": len(json.dumps(request)),
                    "output_bytes": len(json.dumps(transformed)),
                }
            )
        )
        return transformed
```

### Prometheus Exemplars Linked to Tempo

Grafana can link exemplars from Prometheus metrics to Tempo traces when trace IDs are attached to observations.
The exact application code depends on the metrics library, but the Grafana data source relationship looks like this:

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://kube-prometheus-stack-prometheus.monitoring.svc.cluster.local:9090
    jsonData:
      exemplarTraceIdDestinations:
        - name: trace_id
          datasourceUid: tempo
  - name: Tempo
    uid: tempo
    type: tempo
    url: http://tempo.monitoring.svc.cluster.local:3200
    jsonData:
      tracesToLogs:
        datasourceUid: loki
        tags:
          - namespace
          - pod
          - container
```

The operator workflow should feel evidence-driven, with each observability system contributing a different part of the explanation instead of forcing engineers to infer causality from one dashboard:

1. Grafana alert fires because p99 latency breached the objective.
2. The engineer opens the latency graph and clicks a slow exemplar.
3. Tempo shows the request spent most time in the transformer or predictor.
4. Grafana jumps to Loki logs for the same pod and request ID.
5. The engineer overlays GPU memory and sees a spike during the same window.
6. The rollback decision uses trace, log, and metric evidence, not guesswork.

That is the confidence target for bare-metal MLOps.
You do not need a managed service to have professional traceability.
You do need to wire the path intentionally.

---

## Patterns & Anti-Patterns

### Patterns

| Pattern | When to Use It | Why It Works | Scaling Considerations |
|---|---|---|---|
| Shared S3-compatible artifact layer | Multiple tools need model artifacts | MinIO gives MLflow, Argo, KServe, and clients one API | Add bucket policies, lifecycle rules, replication, and per-team credentials |
| GitOps promotion | Production serving changes require review | Git records desired state and ArgoCD applies it consistently | Use sync waves and separate platform, model, and runtime repositories when teams grow |
| GPU node labeling | Cluster has mixed GPU models | Workloads land on hardware that matches cost and performance needs | Standardize labels and admission checks so teams do not bypass placement |
| Registry plus immutable artifacts | Audits require lineage | MLflow records model identity while MinIO preserves bytes | Keep aliases human-friendly but store immutable version metadata in releases |
| Three-signal observability | Inference outages are hard to localize | Metrics, logs, and traces answer different questions | Enforce request IDs and label standards at runtime boundaries |

### Anti-Patterns

| Anti-Pattern | Why Teams Fall Into It | Better Alternative |
|---|---|---|
| One giant NFS share for everything | It is familiar and quick to mount | Use MinIO for artifacts and block PVCs for databases and checkpoints |
| Training job updates production directly | It feels automated | Have training register the model, then promote through GitOps |
| GPU requests without node affinity | Early clusters have one GPU type | Use GPU product labels before adding the second hardware class |
| Metrics only at the ingress | Edge latency is easy to scrape | Instrument transformer, predictor, runtime, and GPU metrics |
| Shared object storage credentials | It avoids credential management work | Use per-team or per-service credentials with narrow bucket policy |
| Treating `LoadBalancer` as automatic | Cloud examples hide the provider integration | Install MetalLB and design IP pools before exposing inference APIs |

---

## Decision Framework

Use this framework when designing a bare-metal ML platform for an organization.
It starts with constraints, then chooses layers.

```text
Start
  |
  v
Is data allowed in managed cloud?
  |-- yes --> Compare cloud ML platform cost and lock-in against team capacity
  |
  |-- no --> Bare-metal or private cloud required
             |
             v
Do you have multi-node production requirements?
  |-- no --> k3s lab or edge design
  |-- yes --> kubeadm production cluster
             |
             v
Do workloads need GPUs?
  |-- no --> skip GPU Operator, keep observability labels ready
  |-- yes --> install NVIDIA GPU Operator, DCGM, feature discovery
             |
             v
Are GPUs A100/H100 class?
  |-- yes --> evaluate MIG profiles and node affinity
  |-- no --> evaluate time-slicing only for lower-criticality sharing
             |
             v
Which serving path dominates?
  |-- Kubernetes-native CRDs --> KServe
  |-- inference graphs --> Seldon Core
  |-- Bento developer workflow --> BentoML + optional Yatai
             |
             v
Is auditability required?
  |-- yes --> MLflow registry, immutable versions, GitOps promotion
  |-- no --> still keep MLflow or Aim for reproducibility
```

| Decision | Choose Option A When | Choose Option B When | Watch For |
|---|---|---|---|
| kubeadm vs k3s | You need multi-node production control | You need a compact lab or edge cluster | Do not let lab convenience leak into production design |
| L2 vs BGP MetalLB | Network is simple and local | Routers can peer and production failover matters | Reserve IP ranges with network operations |
| MinIO standalone vs Operator | Single-node lab | Multi-tenant production storage | Operator setup adds concepts but improves lifecycle |
| Longhorn vs OpenEBS | You want simple replicated block storage | You already run OpenEBS or need its engine choices | Test restore, not just install |
| KServe vs Seldon vs BentoML | Standard model serving and canaries | Graph inference or Bento packaging dominates | More serving stacks mean more platform ownership |
| MLflow vs Yatai vs Aim | Framework-neutral registry | BentoML-native registry or lightweight tracking | Keep promotion workflow explicit |
| Argo Workflows vs Tekton | Data pipelines and DAGs dominate | App CI/CD already uses Tekton | Avoid duplicate pipeline cultures |

The most important decision is not a tool choice.
It is whether your team can operate the platform.
Bare metal rewards disciplined teams with control and predictable cost.
It punishes vague ownership.

Use the framework as a review artifact before purchasing hardware or installing operators. Ask who patches each layer, who owns restore tests, who approves model promotion, who responds to GPU health alerts, and who changes network exposure. If those answers are unclear, managed cloud may still be the more responsible option even when bare metal looks cheaper on a spreadsheet. The platform decision is operational capacity first and component selection second.

---

## Did You Know?

- NVIDIA announced the Kubernetes GPU device plugin beta era around Kubernetes 1.10 in 2018; before that, GPU scheduling often depended on custom cluster conventions.
- An NVIDIA A100 can expose up to 7 MIG instances, which lets one physical accelerator host several isolated inference or development workloads.
- MetalLB was created because bare-metal Kubernetes clusters do not automatically receive cloud load balancers when a Service uses type `LoadBalancer`.
- The original MLflow project was announced by Databricks in 2018, and its open design is one reason it remains common in self-hosted registries.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Installing only the NVIDIA device plugin on bare metal | Cloud examples assume drivers already exist | Use the GPU Operator so drivers, toolkit, DCGM, GFD, and MIG lifecycle are reconciled together |
| Storing MLflow artifacts on the MLflow pod filesystem | It works during the first demo | Use PostgreSQL for metadata and MinIO as the default artifact root |
| Using MinIO for high-frequency training checkpoints without testing | S3 compatibility feels universal | Benchmark checkpoint write patterns and use block PVCs where filesystem writes perform better |
| Exposing every platform service through ingress | Teams want browser access quickly | Keep databases and internal APIs as ClusterIP; expose only user-facing services with auth |
| Letting teams choose arbitrary GPU labels | Early cluster growth feels informal | Standardize GPU product labels, node affinity templates, and admission policy |
| Deploying observability after the first outage | Metrics work is seen as optional | Install kube-prometheus-stack, Loki, Tempo, and DCGM before production traffic |
| Treating model version and object version as the same thing | Both sound like versioning | Use MLflow versions for lifecycle and MinIO versioning for object recovery |
| Running canaries without SLO checks | Traffic splitting looks like enough | Connect canary rollout to latency, error rate, and GPU memory alerts |

---

## Quiz

<details>
<summary>Your training job requests one GPU but DCGM shows zero utilization for the pod. What do you check first, and why?</summary>

Start with scheduling and runtime placement.
Confirm the pod is on a GPU node, the node exposes `nvidia.com/gpu`, and the pod received the device allocation.
Then check the container image has the CUDA or runtime libraries it expects and that the training process actually uses GPU code.
If the pod is on the wrong GPU class, add node affinity using `nvidia.com/gpu.product`.
</details>

<details>
<summary>A model was promoted in MLflow, but KServe still serves the previous version. What is the likely design gap?</summary>

MLflow promotion records registry intent, but it does not automatically update production serving unless you built that automation.
Check whether a GitOps change updated the `InferenceService` storage URI, model version, or runtime configuration.
The robust pattern is registry event or approval creates a Git change, then ArgoCD reconciles KServe.
Direct registry mutation alone should not be treated as deployment.
</details>

<details>
<summary>Inference latency spikes only during cold starts, and logs show model downloads taking too long. Which layers are involved?</summary>

This crosses serving, storage, and networking.
KServe is starting a predictor revision, the storage initializer is pulling from MinIO, and the network path to MinIO may be slow or policy-constrained.
Check MinIO performance, pod-to-MinIO network policy, object size, and whether the serving runtime can cache models.
For large models, consider pre-warming, local cache strategies, or rollout windows that avoid user-facing cold pulls.
</details>

<details>
<summary>Your team wants to use RTX 4090 GPUs for shared inference. Should you use MIG?</summary>

No, RTX 4090 class consumer GPUs do not provide MIG in the way A100 or H100 class data-center GPUs do.
Use time-slicing only when the workloads can tolerate weaker isolation and possible noisy-neighbor effects.
Set clear resource expectations and monitor GPU memory closely.
For strict production isolation, use MIG-capable data-center GPUs or dedicate GPUs per workload.
</details>

<details>
<summary>A Velero restore brings back Kubernetes objects, but MLflow runs are missing artifacts. What was incomplete?</summary>

The backup covered cluster resources but not the object storage contents or registry database state.
MLflow needs PostgreSQL metadata and MinIO artifacts to be restored together.
A complete disaster recovery plan includes Velero for Kubernetes objects, database backups for MLflow metadata, and MinIO replication or bucket backups for artifacts.
Test restore order before depending on it.
</details>

<details>
<summary>A team proposes one shared MinIO access key for all training jobs. How do you evaluate the risk?</summary>

Shared credentials make access easy but destroy useful ownership boundaries.
If one job leaks credentials or deletes objects, attribution and containment are weak.
Use per-team or per-service credentials, bucket policies, and namespace-scoped secrets.
The platform should make the secure path easy enough that teams do not invent shortcuts.
</details>

<details>
<summary>Argo Workflows and Tekton are both available in your company. How do you decide which one runs ML training pipelines?</summary>

Choose based on existing platform ownership and workflow shape.
Argo Workflows is strong for Kubernetes-native DAGs, artifact passing, and data pipeline ergonomics.
Tekton is attractive when the organization already uses it for application CI/CD and wants one pipeline framework.
Avoid running both for the same team unless there is a clear operational reason.
</details>

---

## Hands-On Exercise

The full production lab takes longer than this module.
You have two paths.
The minimal path takes about 30-40 minutes and proves the integration pattern on one machine.
The production-realistic path takes about 2-3 hours and uses real infrastructure decisions.

Both paths follow the same six tasks, but they exercise different failure modes, so choose the path that matches your hardware and be honest about what the result proves.

### Path A: Minimal Lab

Use this path when you have a laptop or workstation and want the workflow shape.
It uses kind, a simulated GPU resource, MinIO, MLflow, Argo Workflows, KServe, and kube-prometheus-stack.
The fake GPU is not for performance testing.
It lets you practice manifests that request GPU resources.

### Path B: Production-Realistic Lab

Use this path when you have a kubeadm cluster with at least one NVIDIA GPU node.
It adds Cilium, MetalLB, Longhorn, NVIDIA GPU Operator, MinIO, MLflow, Argo Workflows, KServe, and kube-prometheus-stack.
This is the path that exposes real driver, network, storage, and observability behavior.

### Task 1: Cluster Foundation

Minimal path: use the following kind configuration to create a small cluster where you can practice the platform wiring without claiming that GPU performance has been validated.

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
```

```bash
kind create cluster --name baremetal-mlops --config kind-mlops.yaml
k cluster-info
k get nodes
```

For a fake GPU resource in kind, label one worker and use a device-plugin simulator only for scheduling practice.
Do not treat fake resources as GPU validation.

```bash
k label node baremetal-mlops-worker accelerator=fake-gpu
```

Production path: initialize a kubeadm cluster only on infrastructure you control, then treat every subsequent component as part of the production dependency chain.

```bash
sudo kubeadm init --pod-network-cidr=10.244.0.0/16
mkdir -p "$HOME/.kube"
sudo cp /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
```

Join workers using the command printed by `kubeadm init`, then install Cilium and MetalLB so pod networking, policy enforcement, and external service IP assignment exist before platform services depend on them:

```bash
helm repo add cilium https://helm.cilium.io
helm repo update
helm upgrade --install cilium cilium/cilium \
  --namespace kube-system \
  --set kubeProxyReplacement=true

helm repo add metallb https://metallb.github.io/metallb
helm repo update
helm upgrade --install metallb metallb/metallb \
  --namespace metallb-system \
  --create-namespace
```

<details>
<summary>Solution notes for Task 1</summary>

Minimal success means `k get nodes` shows the control-plane and workers as `Ready`.
Production success means all kube-system pods are healthy, Cilium reports ready agents, and MetalLB controller and speaker pods are running.
Do not proceed to serving until basic pod networking and service DNS work.
</details>

### Task 2: Storage Layer

Install MinIO Operator before creating buckets, because the operator owns the tenant lifecycle and gives the lab the same control shape you would use in production:

```bash
helm repo add minio-operator https://operator.min.io
helm repo update
helm upgrade --install minio-operator minio-operator/operator \
  --namespace minio-operator \
  --create-namespace
```

Create a tenant and bucket using the MinIO tenant pattern from section two.
For a minimal lab, use local-path or standard storage.
For production, install Longhorn first:

```bash
helm repo add longhorn https://charts.longhorn.io
helm repo update
helm upgrade --install longhorn longhorn/longhorn \
  --namespace longhorn-system \
  --create-namespace
```

Create buckets after the tenant is ready, since MLflow, Argo Workflows, and KServe will all depend on predictable bucket names and endpoint behavior:

```bash
k -n ml-storage port-forward svc/ml-artifacts-console 9001:9001
```

Use the MinIO console to create the shared buckets below, then record which bucket is for artifacts, datasets, and serving models so later manifests do not drift:

- `mlflow-artifacts`
- `training-datasets`
- `kserve-models`

<details>
<summary>Solution notes for Task 2</summary>

Minimal success means the MinIO tenant pods are running and the console opens locally.
Production success also includes a default or named storage class suitable for PostgreSQL and checkpoint PVCs.
Record the internal MinIO endpoint because MLflow and Argo need it later.
</details>

### Task 3: Model Registry

Create the MLflow namespace and credentials before deployment, because the tracking server, training pods, and artifact clients need the same service discovery and secret boundaries:

```bash
k create namespace ml-platform
k create namespace ml-training
```

Install PostgreSQL for the lab as the MLflow backend store, keeping registry metadata on block storage rather than inside the tracking container filesystem:

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm upgrade --install mlflow-postgresql bitnami/postgresql \
  --namespace ml-platform \
  --set auth.username=mlflow \
  --set auth.password=your-db-password-here \
  --set auth.database=mlflow \
  --set primary.persistence.storageClass=longhorn
```

Deploy MLflow using the values pattern in section four, then expose the UI locally so you can verify both the web service and its backend dependencies before submitting workflows:

```bash
k -n ml-platform port-forward svc/mlflow-tracking 5000:5000
```

Open `http://127.0.0.1:5000` and confirm the interface loads before continuing, because a broken registry will make later training and serving failures harder to interpret.

<details>
<summary>Solution notes for Task 3</summary>

The UI should load without the pod writing artifacts to local disk.
Check the MLflow pod environment for `MLFLOW_S3_ENDPOINT_URL`.
If run logging fails, inspect MinIO credentials, bucket existence, service DNS, and PostgreSQL connectivity.
</details>

### Task 4: Training Pipeline with Argo Workflows

Install Argo Workflows after the registry and object storage are reachable, because the workflow controller will coordinate jobs that read credentials, write artifacts, and register models:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm upgrade --install argo-workflows argo/argo-workflows \
  --namespace argo \
  --create-namespace \
  --set server.authModes[0]=server
```

Create a workflow service account with permissions in `ml-training`, then submit the workflow from section five and watch both Kubernetes events and Argo node status during the run:

```bash
k apply -f iris-train-register-workflow.yaml
k get workflows -n ml-training
k logs -n ml-training -l workflows.argoproj.io/workflow
```

The workflow should prove the registry path end to end, so treat each expected result as a contract between training code, object storage, and MLflow metadata:

- Train a small scikit-learn iris classifier.
- Log parameters and metrics to MLflow.
- Register the model in the MLflow model registry.
- Save the model artifact to MinIO.

<details>
<summary>Solution notes for Task 4</summary>

A healthy run has green Argo nodes, an MLflow run with parameters and metrics, and artifacts stored under the MinIO bucket.
If the training pod is pending in production, check GPU capacity and node affinity.
If it fails after starting, check MLflow tracking URI, S3 endpoint, and credentials.
</details>

### Task 5: Inference Serving with KServe

Install KServe using the current project installation guide for your chosen mode.
For a compact lab, use the quick install path and local gateway.
For production, integrate it with your ingress, certificates, and network policy.

Create a namespace for serving workloads so inference resources, network policies, runtime credentials, and observability labels have a clear ownership boundary:

```bash
k create namespace ml-serving
```

Create an `InferenceService` that points to the model artifact.
The exact storage URI depends on how your MLflow artifact path is organized.

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: iris-bare-metal
  namespace: ml-serving
  labels:
    workload-type: inference
    model_name: iris-bare-metal
    model_version: "1"
spec:
  predictor:
    model:
      modelFormat:
        name: sklearn
      storageUri: s3://mlflow-artifacts/models/iris-bare-metal/1
      resources:
        requests:
          cpu: "1"
          memory: 2Gi
        limits:
          cpu: "2"
          memory: 4Gi
```

Test with curl only after the `InferenceService` reports ready, because otherwise you may confuse rollout, gateway, and model-loading problems in the same request:

```bash
SERVICE_HOSTNAME=$(k get inferenceservice iris-bare-metal \
  -n ml-serving \
  -o jsonpath='{.status.url}' | cut -d / -f 3)

curl -s \
  -H "Host: ${SERVICE_HOSTNAME}" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8080/v1/models/iris-bare-metal:predict \
  -d '{"instances": [[5.1, 3.5, 1.4, 0.2]]}'
```

<details>
<summary>Solution notes for Task 5</summary>

`k get inferenceservice -n ml-serving` should show `READY=True`.
If the service is not ready, inspect the revision, predictor pod, storage initializer logs, and MinIO access.
If curl fails but the pod is ready, check ingress host headers and gateway routing.
</details>

### Task 6: Observe It All

Install kube-prometheus-stack before declaring the lab complete, since production readiness depends on seeing request behavior rather than merely receiving one successful prediction:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

Apply the KServe ServiceMonitor from section six, then open Prometheus to verify that scraping works and that labels match the service you expect to observe:

```bash
k -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090
```

Open Grafana after Prometheus is scraping targets, because dashboards without live metrics can hide configuration mistakes behind empty panels:

```bash
k -n monitoring port-forward svc/kube-prometheus-stack-grafana 3000:80
```

Send repeated requests to create enough traffic for latency and request-rate panels to show useful patterns rather than isolated single-sample behavior:

```bash
for i in $(seq 1 100); do
  curl -s \
    -H "Host: ${SERVICE_HOSTNAME}" \
    -H "Content-Type: application/json" \
    http://127.0.0.1:8080/v1/models/iris-bare-metal:predict \
    -d '{"instances": [[5.9, 3.0, 5.1, 1.8]]}' >/dev/null
done
```

Check Prometheus for request metrics and Grafana for latency.
Then check MLflow to confirm the registered model and artifact path.

<details>
<summary>Solution notes for Task 6</summary>

The goal is not a perfect dashboard.
The goal is to prove that one model movement is visible across storage, registry, workflow, serving, and metrics.
If Prometheus does not scrape KServe metrics, verify ServiceMonitor labels match the Prometheus release label and that the target service exposes `/metrics`.
</details>

### Success Criteria

- [ ] MinIO bucket created and accessible via S3 API
- [ ] MLflow UI shows experiment with logged run, including parameters, metrics, and artifacts
- [ ] Model registered in MLflow model registry with version 1
- [ ] Argo Workflow completed successfully with all steps green
- [ ] KServe InferenceService in `Ready` state
- [ ] Inference curl returns a valid prediction
- [ ] Prometheus scrapes KServe metrics, verified through `k port-forward` to Prometheus
- [ ] Grafana shows inference request latency

---

## Sources

- NVIDIA GPU Operator documentation: https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/index.html
- NVIDIA GPU sharing documentation: https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html
- NVIDIA DCGM user guide: https://docs.nvidia.com/datacenter/dcgm/latest/user-guide/index.html
- MetalLB concepts: https://metallb.io/concepts/
- Longhorn overview: https://longhorn.io/docs/latest/what-is-longhorn/
- MinIO Kubernetes documentation: https://min.io/docs/minio/kubernetes/upstream/index.html
- MLflow tracking documentation: https://mlflow.org/docs/latest/ml/tracking/
- MLflow model registry documentation: https://mlflow.org/docs/latest/ml/model-registry/
- Argo Workflows documentation: https://argoproj.github.io/argo-workflows/
- Argo Workflows artifact documentation: https://argo-workflows.readthedocs.io/en/latest/walk-through/artifacts/
- Argo CD documentation: https://argo-cd.readthedocs.io/en/stable/
- Argo CD sync waves: https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/
- KServe predictive inference service documentation: https://kserve.github.io/website/docs/getting-started/predictive-first-isvc
- Cilium documentation: https://docs.cilium.io/en/stable/
- Prometheus community Helm charts: https://prometheus-community.github.io/helm-charts/
- Grafana Loki documentation: https://grafana.com/docs/loki/latest/
- Grafana Tempo documentation: https://grafana.com/docs/tempo/latest/
- OpenTelemetry Python instrumentation documentation: https://opentelemetry.io/docs/instrumentation/python/
- CloudNativePG documentation: https://cloudnative-pg.io/documentation/current/
- Velero documentation: https://velero.io/docs/main/

---

**End of ML Platforms Toolkit.** Continue to the next category in the Data & AI Platforms family:
[Cloud-Native Databases Toolkit](/platform/toolkits/data-ai-platforms/cloud-native-databases/) — CockroachDB, CloudNativePG, Neon/PlanetScale, and Vitess for production database management on Kubernetes.
