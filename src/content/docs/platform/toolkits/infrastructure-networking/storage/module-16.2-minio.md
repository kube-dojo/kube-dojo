---
title: "Module 16.2: MinIO - High-Performance Object Storage for Kubernetes"
slug: platform/toolkits/infrastructure-networking/storage/module-16.2-minio
sidebar:
  order: 3
---

## Complexity: [MEDIUM]

## Time to Complete: 55-70 minutes

---

## Prerequisites

Before starting this module, you should have completed:

- [Distributed Systems Foundation](/platform/foundations/distributed-systems/) - replication, consensus, quorum, and failure domains
- Kubernetes fundamentals: Deployments, StatefulSets, Services, PersistentVolumeClaims, Secrets, and probes
- Basic S3 concepts: buckets, objects, access keys, presigned URLs, and lifecycle policies
- [Module 16.1: Rook/Ceph](../module-16.1-rook-ceph/) - recommended for comparing object, block, and filesystem storage trade-offs

You do not need to be a storage specialist before starting. You should, however, be comfortable reading Kubernetes manifests and thinking about what happens when a pod, node, disk, or network path fails.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a MinIO deployment topology for Kubernetes by matching server pools, drives, erasure coding, and failure domains to workload requirements.
- **Configure** MinIO tenants, buckets, policies, lifecycle rules, and application integrations without leaking root credentials into workloads.
- **Debug** common MinIO-on-Kubernetes failures involving DNS style, TLS, bucket permissions, drive health, and client endpoint configuration.
- **Evaluate** when MinIO is a better fit than cloud S3, Ceph object storage, or block storage for platform workloads.
- **Implement** a working MinIO lab with object upload, checksum verification, lifecycle policy validation, and operational health checks.

---

## Why This Module Matters

A platform team at a healthcare analytics company inherited a problem that looked like a machine learning bottleneck but was really a storage architecture failure. Their GPU jobs spent more time waiting for medical imaging objects than training models, and the monthly cloud bill kept rising because the data moved across availability zones, development clusters, and external build systems. The application code was already written for the S3 API, so the team did not want to rewrite every data pipeline. They needed the same API closer to the workloads, with predictable cost and enough durability to protect irreplaceable datasets.

| Problem | Impact |
|---------|--------|
| Remote object storage on a hot training path | GPUs sat idle while jobs waited for image batches and model artifacts. |
| Cross-zone and cross-environment transfers | The bill increased whenever teams copied data into another cluster or pipeline. |
| S3-specific code embedded in scripts | A replacement that broke the S3 API would force a risky application migration. |
| No local disaster-recovery target | Backups and model artifacts depended on one external storage region. |

MinIO gave the team a different operating model. They kept the S3 API, but moved the storage endpoint into Kubernetes near the workloads that used it. Training jobs could read artifacts over the cluster network, Velero could write backups to an internal S3-compatible target, and observability systems could store logs and traces without depending on a public cloud bucket. The technical win was not simply "self-host S3"; the win was controlling where the data path, cost model, and failure domains lived.

| Metric | Remote Cloud S3 Path | MinIO In-Cluster Path |
|--------|----------------------|-----------------------|
| Application API | S3-compatible | S3-compatible |
| Typical data path | Pod to external region or cloud endpoint | Pod to Kubernetes Service and MinIO pods |
| Cost driver | Storage, operations, egress, and cross-zone transfer | Cluster storage, node capacity, and operations |
| Failure ownership | Cloud provider plus network path | Platform team, Kubernetes, nodes, disks, and replication target |
| Best fit | Global managed object storage | Local high-performance object storage and controlled environments |

This module teaches MinIO as a platform engineering decision, not just a Helm chart. You will learn how the architecture works, how to deploy it safely, how to connect real workloads, and how to reason through failures before they become incidents.

---

## MinIO's Job in a Kubernetes Platform

MinIO is S3-compatible object storage. That sentence is short, but the platform implication is large: many modern tools already know how to store data in S3, so a MinIO endpoint can become shared infrastructure for backups, logs, traces, machine learning artifacts, build caches, and data-processing pipelines. The client usually thinks in buckets and objects, while the platform team thinks in tenants, PVCs, drives, policies, metrics, and recovery procedures.

Object storage is different from block storage and filesystem storage. A database that needs a mounted volume usually wants block storage through a PersistentVolumeClaim. A legacy application that expects shared POSIX file operations may need a filesystem. MinIO is for object workflows: upload an artifact, read it by key, set lifecycle rules, expose a presigned URL, or stream chunks from a bucket. Choosing MinIO for the wrong workload creates pain, but choosing it for S3-native workflows can remove a surprising amount of operational friction.

```ascii
STORAGE DECISION SHAPE
──────────────────────────────────────────────────────────────────────────────

                 ┌────────────────────────────────────────────────────┐
                 │              Application Need                       │
                 └────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
│ Block Storage    │        │ File Storage     │        │ Object Storage   │
│ PVC per workload │        │ Shared path      │        │ Bucket + object  │
├──────────────────┤        ├──────────────────┤        ├──────────────────┤
│ Databases        │        │ Shared configs   │        │ Backups          │
│ Stateful apps    │        │ POSIX workflows  │        │ Logs and traces  │
│ Low-latency disk │        │ Legacy apps      │        │ ML artifacts     │
└──────────────────┘        └──────────────────┘        └──────────────────┘
                                                                   │
                                                                   ▼
                                                        ┌──────────────────┐
                                                        │ MinIO fits here  │
                                                        │ when S3 API is   │
                                                        │ the contract.    │
                                                        └──────────────────┘
```

A good MinIO design starts with the contract the application needs. If the application can use S3 operations such as `PutObject`, `GetObject`, multipart upload, bucket lifecycle, and presigned URLs, MinIO is a candidate. If the application needs `fsync`, file locking, or a mounted directory with POSIX semantics, MinIO is probably the wrong abstraction even if it happens to run on disks.

**Pause and predict:** A team asks to mount a MinIO bucket as a filesystem for a write-heavy database because they heard MinIO is fast. Before reading further, decide what failure or performance behavior you would expect. The key reasoning step is that object storage optimizes whole-object operations and S3 semantics, while databases rely on block-level writes, ordering, and filesystem guarantees.

MinIO is also not a shortcut around storage engineering. It still depends on physical or virtual disks, Kubernetes scheduling, node health, network reliability, TLS, identity management, and backups. The difference is that those responsibilities become visible to the platform team instead of hidden behind a managed service boundary. That visibility is useful only when the team designs, monitors, and tests the system deliberately.

---

## Core Architecture: API, Erasure Coding, and Server Pools

MinIO has three layers that matter most when you operate it on Kubernetes. The S3 API layer receives client requests and enforces authentication, authorization, bucket features, object locking, lifecycle rules, and notifications. The erasure coding layer splits objects into data and parity shards so the cluster can tolerate disk or node failures. The server pool layer maps that storage model onto pods, PVCs, and drives.

```ascii
MINIO ARCHITECTURE
──────────────────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────────────────┐
│                              MINIO CLUSTER                                 │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  S3 API LAYER                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ GetObject, PutObject, multipart upload, bucket policy, STS, events   │  │
│  │ Clients use S3 SDKs, mc, Velero, Loki, MLflow, BuildKit, or custom    │  │
│  │ applications. This layer decides who can do what to which bucket.     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                      │                                     │
│                                      ▼                                     │
│  ERASURE CODING LAYER                                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Object data is split into data shards and parity shards. MinIO can   │  │
│  │ reconstruct an object when enough shards remain available. Checksums  │  │
│  │ help detect corruption so healing can repair damaged or missing data. │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                      │                                     │
│                                      ▼                                     │
│  SERVER POOL LAYER                                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ pool-0                                                               │  │
│  │ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐         │  │
│  │ │ minio-0    │ │ minio-1    │ │ minio-2    │ │ minio-3    │         │  │
│  │ │ pvc-a pvc-b│ │ pvc-a pvc-b│ │ pvc-a pvc-b│ │ pvc-a pvc-b│         │  │
│  │ └────────────┘ └────────────┘ └────────────┘ └────────────┘         │  │
│  │                                                                      │  │
│  │ Objects are distributed across drives in the pool, so drive count,   │  │
│  │ node placement, and PVC backing storage all affect durability.       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

Erasure coding is the mechanism that prevents every object from needing three full replicas. In a simple eight-drive example, MinIO can store four data shards and four parity shards. The object can still be read when enough shards remain available, because the missing pieces can be reconstructed from the surviving data and parity. This is not magic compression; it is a durability trade-off that uses parity math to reduce storage overhead while retaining failure tolerance.

```ascii
ERASURE CODING EXAMPLE: 4 DATA SHARDS + 4 PARITY SHARDS
──────────────────────────────────────────────────────────────────────────────

Original object:
┌────────────────────────────────────────────────────────────────────────────┐
│ model-checkpoint.bin                                                       │
└────────────────────────────────────────────────────────────────────────────┘

Stored across eight drives:
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Data 1   │ │ Data 2   │ │ Data 3   │ │ Data 4   │
│ Drive 1  │ │ Drive 2  │ │ Drive 3  │ │ Drive 4  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Parity 1 │ │ Parity 2 │ │ Parity 3 │ │ Parity 4 │
│ Drive 5  │ │ Drive 6  │ │ Drive 7  │ │ Drive 8  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘

If several drives fail, MinIO can reconstruct the object as long as enough
shards remain. More parity improves tolerance but increases storage overhead.
```

The important senior-level point is that erasure coding does not remove the need to think about failure domains. If eight PVCs all sit on the same worker node, the cluster may look durable on paper while still being vulnerable to one node failure. If the backing StorageClass already replicates data elsewhere, you may be layering MinIO erasure coding on top of storage replication and paying for more redundancy than you intended. A platform engineer should map MinIO pods, PVCs, disks, nodes, and zones before declaring the design production-ready.

**Active check:** Imagine a four-pod MinIO tenant where every pod is scheduled onto the same Kubernetes node because no topology spread constraint exists. Which component would appear healthy during deployment, and which real-world failure would still be dangerous? The operator may report the tenant ready, but a single node outage can remove every MinIO server at once, collapsing the intended failure model.

Use this decision table when evaluating the first version of a MinIO design. The exact sizing depends on workload and hardware, but the reasoning categories stay stable.

| Design Question | Good Signal | Risk Signal |
|-----------------|-------------|-------------|
| Does the workload use S3 semantics? | Application already supports S3 endpoint, bucket, and credentials. | Application expects a mounted filesystem or block device. |
| Are failure domains separated? | Pods and PVCs spread across nodes or zones where possible. | All drives depend on one node, one disk shelf, or one storage backend path. |
| Is redundancy counted once? | Team understands both MinIO erasure coding and StorageClass replication. | Team assumes more layers always mean better durability. |
| Are credentials scoped? | Each application has a bucket-level or prefix-level policy. | Workloads use root credentials because it was faster during setup. |
| Can the team observe healing? | Metrics and alerts cover nodes, drives, capacity, and heal errors. | Only pod readiness is monitored. |

---

## Deploying MinIO with the Operator

For production-like Kubernetes deployments, the MinIO Operator is the preferred control plane because it represents a MinIO cluster as a Kubernetes custom resource called a Tenant. The operator creates StatefulSets, Services, certificates, console resources, and supporting secrets. You still need to make design choices, but the operator gives those choices a Kubernetes-native API instead of a hand-built collection of manifests.

The operator pattern is useful because object storage is stateful and long-lived. A Deployment can restart pods, but it does not understand MinIO tenants, server pools, certificate management, or pool expansion. A Tenant resource captures intent: how many servers, how many volumes per server, which image, which credentials, and whether automatic certificates should be requested.

```ascii
MINIO OPERATOR ARCHITECTURE
──────────────────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────────────────┐
│                            KUBERNETES CLUSTER                              │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                           MINIO OPERATOR                             │  │
│  │                                                                      │  │
│  │ Watches Tenant resources and reconciles the expected MinIO state.    │  │
│  │ It creates StatefulSets, Services, certificates, console access,     │  │
│  │ users, and pool configuration needed by each tenant.                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                      │                                     │
│                                      ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                            MINIO TENANT                              │  │
│  │                                                                      │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │ minio-0    │  │ minio-1    │  │ minio-2    │  │ minio-3    │     │  │
│  │  │ pvc-a pvc-b│  │ pvc-a pvc-b│  │ pvc-a pvc-b│  │ pvc-a pvc-b│     │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘     │  │
│  │                                                                      │  │
│  │ Services expose the S3 API and console. PVCs provide persistent      │  │
│  │ drives. Scheduling rules should keep failure domains separated.      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

Install the operator first. The chart version below may need to be updated in your own environment, but the sequence is the important part: add the repository, install into a dedicated namespace, then verify the controller rollout before creating tenants.

```bash
helm repo add minio-operator https://operator.min.io
helm repo update

helm install --create-namespace --namespace minio-operator \
  minio-operator minio-operator/operator \
  --version 6.0.4

kubectl -n minio-operator rollout status deployment/minio-operator
kubectl -n minio-operator get pods
```

The next manifest creates a small tenant with four servers and two volumes per server. This shape gives eight PVC-backed drives, which is enough to demonstrate distributed MinIO behavior without pretending the example is a full production design. In a real platform, you would also review node placement, StorageClass behavior, resource limits, TLS integration, backup targets, and access policies before accepting the design.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: minio-tenant
---
apiVersion: v1
kind: Secret
metadata:
  name: minio-user-secret
  namespace: minio-tenant
stringData:
  CONSOLE_ACCESS_KEY: admin
  CONSOLE_SECRET_KEY: minio-secret-key-change-me
---
apiVersion: minio.min.io/v2
kind: Tenant
metadata:
  name: minio
  namespace: minio-tenant
spec:
  image: quay.io/minio/minio:RELEASE.2024-11-07T00-52-20Z
  pools:
    - name: pool-0
      servers: 4
      volumesPerServer: 2
      volumeClaimTemplate:
        metadata:
          name: data
        spec:
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: 50Gi
      resources:
        requests:
          cpu: "500m"
          memory: "1Gi"
        limits:
          cpu: "2"
          memory: "4Gi"
  mountPath: /export
  requestAutoCert: true
  users:
    - name: minio-user-secret
  features:
    domains:
      console: console.minio.example.com
      minio:
        - minio.example.com
```

Apply the tenant and watch both the Kubernetes resources and the MinIO-specific status. The alias `k` is commonly used for `kubectl`; this module spells out `kubectl` first and then uses `k` in later snippets where the command is repetitive.

```bash
kubectl apply -f minio-tenant.yaml

kubectl -n minio-tenant get tenant
kubectl -n minio-tenant get pods -w
kubectl -n minio-tenant get pvc
kubectl -n minio-tenant get svc
```

A successful rollout is not the same thing as a safe rollout. The pod status tells you that containers started. The PVC status tells you that Kubernetes attached storage. The Service tells you that clients have an endpoint. None of those prove that the application has the right bucket policy, that the drives are spread across failure domains, or that lifecycle management is preventing unbounded growth.

**Pause and predict:** If the tenant pods are Running but every S3 client receives TLS or certificate errors, should you first edit the bucket policy, recreate the PVCs, or inspect endpoint and certificate configuration? The best first move is to inspect how the client reaches the Service and what certificate name it expects, because bucket policy failures usually produce authorization errors rather than TLS handshake failures.

For local development, a standalone MinIO deployment can be useful. It is not a substitute for a production tenant, but it is excellent for learning the S3 workflow and testing application configuration. The lab later in this module uses standalone MinIO so you can run it quickly in a kind cluster.

```bash
helm repo add minio https://charts.min.io
helm repo update

helm install minio minio/minio \
  --namespace minio \
  --create-namespace \
  --set rootUser=admin \
  --set rootPassword=minio-secret-key-change-me \
  --set mode=standalone \
  --set persistence.size=20Gi \
  --set resources.requests.memory=512Mi
```

---

## Worked Example: Debug a Broken MLflow Artifact Store

Before you configure your own workloads, study a realistic failure. An ML platform team deploys MLflow in Kubernetes and points it at MinIO for model artifacts. The UI starts, experiments can be created, but model uploads fail with an S3 error. The team initially blames MinIO performance, but the failure happens before any meaningful object transfer begins.

The deployment uses an internal MinIO Service. The problem is hidden in the endpoint style and protocol assumptions. Many S3 clients default to virtual-hosted bucket addressing, where the bucket name becomes part of the hostname. That works for AWS endpoints with public DNS patterns, but it often fails inside Kubernetes because `mlflow-artifacts.minio.minio-tenant.svc` is not a normal Service name. Path-style addressing keeps the bucket in the URL path and uses the Kubernetes Service name as the host.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow
  namespace: ml-platform
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
          image: ghcr.io/mlflow/mlflow:v2.16.0
          command:
            - mlflow
            - server
            - --backend-store-uri=sqlite:////mlflow/mlflow.db
            - --default-artifact-root=s3://mlflow-artifacts/
            - --host=0.0.0.0
          env:
            - name: MLFLOW_S3_ENDPOINT_URL
              value: "http://minio.minio-tenant.svc:9000"
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: mlflow-minio-credentials
                  key: access-key
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: mlflow-minio-credentials
                  key: secret-key
          ports:
            - containerPort: 5000
```

The first debugging step is to test from inside the same network context as the application. A laptop test may pass while the pod still fails because DNS, certificates, NetworkPolicies, or Service names differ. Use a temporary pod with a client image when you need to separate application bugs from connectivity and credential bugs.

```bash
kubectl -n ml-platform run s3-debug \
  --rm -it \
  --image=minio/mc:RELEASE.2024-10-08T09-37-26Z \
  --restart=Never \
  --command -- sh

mc alias set platform http://minio.minio-tenant.svc:9000 "$AWS_ACCESS_KEY_ID" "$AWS_SECRET_ACCESS_KEY"
mc ls platform/
mc mb --ignore-existing platform/mlflow-artifacts
mc cp /etc/hosts platform/mlflow-artifacts/debug/hosts.txt
mc ls platform/mlflow-artifacts/debug/
```

If the debug pod can upload an object but MLflow cannot, inspect the SDK configuration and application logs. If neither can upload, inspect credentials, bucket existence, bucket policy, endpoint protocol, TLS, and MinIO health. This sequence prevents random changes because each command narrows the fault domain.

```ascii
S3 FAILURE TRIAGE
──────────────────────────────────────────────────────────────────────────────

          ┌──────────────────────────────────────┐
          │ App cannot write object to MinIO      │
          └──────────────────────────────────────┘
                           │
                           ▼
          ┌──────────────────────────────────────┐
          │ Test from debug pod in same namespace │
          └──────────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
┌──────────────────────┐        ┌──────────────────────────┐
│ Debug pod works      │        │ Debug pod also fails     │
├──────────────────────┤        ├──────────────────────────┤
│ Check app SDK style, │        │ Check Service DNS, TLS,  │
│ endpoint variables,  │        │ credentials, bucket,     │
│ bucket path, and app │        │ policy, and MinIO health.│
│ logs.                │        │                          │
└──────────────────────┘        └──────────────────────────┘
```

In this example, the fix is to configure the application or SDK for path-style access when required by that client. Different libraries expose this setting differently. Loki calls it `s3ForcePathStyle`. Some AWS SDKs use `forcePathStyle`. Other tools infer it from the endpoint or provide an S3-compatible mode. The concept is the same: keep the Kubernetes Service name as the DNS host, and put the bucket name in the path.

This worked example matters because many MinIO incidents are integration mistakes rather than MinIO storage failures. A senior platform engineer does not start by restarting pods or expanding disks. They identify whether the failure is client configuration, authentication, network path, certificate trust, bucket authorization, capacity, or drive health.

---

## Configuring Buckets, Policies, and Lifecycle Rules

Running MinIO is only the first half of the job. The next half is making it safe for multiple platform workloads to share the service without sharing root credentials or filling the cluster with forgotten objects. Buckets are administrative boundaries, but policies and lifecycle rules are what turn buckets into usable platform contracts.

Start with a simple convention: one bucket per major workload unless the workload has a clear reason to share. For example, MLflow artifacts, Velero backups, Loki chunks, and BuildKit cache should usually be separate buckets. That separation makes lifecycle rules, access policies, cost attribution, and incident response easier.

```bash
mc alias set platform http://127.0.0.1:9000 admin minio-secret-key-change-me

mc mb --ignore-existing platform/mlflow-artifacts
mc mb --ignore-existing platform/velero-backups
mc mb --ignore-existing platform/loki-chunks
mc mb --ignore-existing platform/buildkit-cache

mc ls platform/
```

Root credentials should be treated like cluster-admin credentials. They are useful during initial setup and emergency recovery, but application pods should receive scoped credentials. The policy below allows an MLflow service account to list the bucket and read or write objects only under the `mlflow-artifacts` bucket.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::mlflow-artifacts"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::mlflow-artifacts/*"
      ]
    }
  ]
}
```

Apply the policy with `mc`, then create a user and attach the policy. In production, you would store the resulting access key and secret key in a Kubernetes Secret managed by your normal secret-management process, not as hard-coded values in a manifest committed to Git.

```bash
cat > mlflow-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::mlflow-artifacts"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::mlflow-artifacts/*"
      ]
    }
  ]
}
EOF

mc admin policy create platform mlflow-artifacts-rw mlflow-policy.json
mc admin user add platform mlflow-app mlflow-secret-change-me
mc admin policy attach platform mlflow-artifacts-rw --user mlflow-app
```

Lifecycle rules prevent object storage from becoming a silent landfill. Backups, logs, traces, caches, and temporary training artifacts all have different retention needs. A build cache may be useful for days. Compliance backups may need months or years. ML model artifacts may need promotion workflows where temporary experiment outputs expire quickly but production models are retained.

```json
{
  "Rules": [
    {
      "ID": "expire-old-build-cache",
      "Status": "Enabled",
      "Expiration": {
        "Days": 14
      }
    }
  ]
}
```

```bash
cat > buildkit-cache-lifecycle.json << 'EOF'
{
  "Rules": [
    {
      "ID": "expire-old-build-cache",
      "Status": "Enabled",
      "Expiration": {
        "Days": 14
      }
    }
  ]
}
EOF

mc ilm import platform/buildkit-cache < buildkit-cache-lifecycle.json
mc ilm ls platform/buildkit-cache
```

**Active check:** Your Loki bucket grows faster than expected after a traffic spike, but MinIO capacity metrics are healthy today. What should you inspect before adding disks? Check retention and compaction settings in Loki, lifecycle rules on the bucket, object growth rate, and whether the data is still needed. Adding disks fixes an immediate capacity symptom, but it does not correct an unbounded retention policy.

Lifecycle design is an example of constructive alignment between platform intent and storage behavior. If the platform says logs are retained for thirty days, the object store should enforce or support that policy. If backups must survive cluster loss, a lifecycle rule inside the same cluster is not enough; you also need replication or an external target.

---

## Integrating MinIO with Platform Workloads

MinIO becomes valuable when platform tools use it through the S3 API. Each integration has the same core shape: endpoint, bucket, credentials, region placeholder, path-style behavior, and TLS settings. The details differ, but the debugging model stays consistent.

For MLflow, MinIO stores experiment artifacts, model files, and dataset references while the backend database stores metadata. This separation is important. Do not put large model binaries into the metadata database, and do not expect MinIO to query experiment metadata like a relational store.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mlflow-minio-credentials
  namespace: ml-platform
stringData:
  access-key: mlflow-app
  secret-key: mlflow-secret-change-me
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow
  namespace: ml-platform
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
          image: ghcr.io/mlflow/mlflow:v2.16.0
          command:
            - mlflow
            - server
            - --backend-store-uri=sqlite:////mlflow/mlflow.db
            - --default-artifact-root=s3://mlflow-artifacts/
            - --host=0.0.0.0
          env:
            - name: MLFLOW_S3_ENDPOINT_URL
              value: "http://minio.minio-tenant.svc:9000"
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: mlflow-minio-credentials
                  key: access-key
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: mlflow-minio-credentials
                  key: secret-key
          ports:
            - containerPort: 5000
```

For Loki, MinIO stores chunks and index data depending on the schema configuration. The highest-risk mistakes are usually endpoint formatting, missing path-style configuration, weak retention planning, and treating object storage as a substitute for correct Loki compaction settings.

```yaml
loki:
  storage:
    type: s3
    s3:
      endpoint: minio.minio-tenant.svc:9000
      bucketnames: loki-chunks
      access_key_id: ${MINIO_ACCESS_KEY}
      secret_access_key: ${MINIO_SECRET_KEY}
      s3ForcePathStyle: true
      insecure: true
  schemaConfig:
    configs:
      - from: "2026-01-01"
        store: tsdb
        object_store: s3
        schema: v13
        index:
          prefix: index_
          period: 24h
```

For Velero, MinIO can be a local backup target in development, air-gapped environments, or clusters that replicate onward to another site. Be careful with the phrase "backup target" here. If the MinIO tenant runs in the same cluster and on the same failure domain as the workloads being backed up, it helps with namespace or application recovery but may not protect against full cluster loss.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: minio-credentials
  namespace: velero
stringData:
  cloud: |
    [default]
    aws_access_key_id=velero-app
    aws_secret_access_key=velero-secret-change-me
```

```bash
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.10.0 \
  --bucket velero-backups \
  --secret-file ./minio-credentials \
  --backup-location-config \
    region=us-east-1,s3ForcePathStyle=true,s3Url=http://minio.minio-tenant.svc:9000
```

For BuildKit, MinIO can store remote build cache objects so repeated CI builds do not rebuild every layer from scratch. This is a good fit because cache entries are objects, retention can be short, and the cost of losing the cache is usually performance rather than data loss.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: buildkit
  namespace: ci
spec:
  containers:
    - name: buildkit
      image: moby/buildkit:latest
      args:
        - --oci-worker-no-process-sandbox
      env:
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: buildkit-minio-credentials
              key: access-key
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: buildkit-minio-credentials
              key: secret-key
```

```bash
buildctl build \
  --frontend dockerfile.v0 \
  --local context=. \
  --local dockerfile=. \
  --export-cache type=s3,endpoint_url=http://minio.minio-tenant.svc:9000,region=us-east-1,bucket=buildkit-cache,use_path_style=true \
  --import-cache type=s3,endpoint_url=http://minio.minio-tenant.svc:9000,region=us-east-1,bucket=buildkit-cache,use_path_style=true \
  --output type=image,name=registry.example.com/app:latest,push=false
```

The pattern across these examples is deliberate. Each tool receives a workload-specific bucket, a scoped credential, an internal endpoint, and a client setting that matches Kubernetes DNS. When a production incident happens, that consistency makes failures easier to isolate.

---

## Monitoring, Capacity, and Recovery

A MinIO pod can be Running while the storage service is already in trouble. The platform team should monitor capacity, request errors, latency, node and drive availability, healing status, and certificate or authentication failures. MinIO also exposes Prometheus metrics, which makes it fit naturally into Kubernetes observability stacks.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: minio
  namespace: minio-tenant
spec:
  selector:
    matchLabels:
      app: minio
  endpoints:
    - port: http-minio
      path: /minio/v2/metrics/cluster
      interval: 30s
      bearerTokenSecret:
        name: minio-prometheus-token
        key: token
```

```ascii
KEY MINIO METRICS
──────────────────────────────────────────────────────────────────────────────

Capacity
├── minio_cluster_capacity_usable_total_bytes      Total usable capacity
├── minio_cluster_capacity_usable_free_bytes       Free usable capacity
└── minio_bucket_usage_total_bytes                 Per-bucket object usage

Performance
├── minio_s3_requests_total                        Request volume by API
├── minio_s3_requests_errors_total                 Error volume by API
├── minio_s3_ttfb_seconds                          Time to first byte
├── minio_s3_traffic_received_bytes                Client upload traffic
└── minio_s3_traffic_sent_bytes                    Client download traffic

Health
├── minio_cluster_nodes_online_total               Online MinIO servers
├── minio_cluster_nodes_offline_total              Offline MinIO servers
├── minio_cluster_drive_online_total               Online drives
├── minio_cluster_drive_offline_total              Offline drives
└── minio_heal_objects_errors_total                Healing failures
```

Capacity monitoring should focus on trend and usable capacity, not only raw disk size. Erasure coding, reserved space, object growth, lifecycle rules, and healing overhead all influence how much capacity is actually available. Alerting at a single high-water mark is better than nothing, but mature teams also watch growth rate so they can act before an emergency expansion.

```bash
mc admin info platform
mc admin heal platform --scan deep
mc admin prometheus generate platform
mc admin trace --errors platform
```

Recovery planning has two levels. The first level is local recovery from disk, pod, or node failures where MinIO healing can restore redundancy after the failed component returns or is replaced. The second level is disaster recovery where the entire cluster, site, or storage backend is lost. MinIO can participate in replication strategies, but a copy inside the same failure domain should not be described as disaster recovery.

```ascii
RECOVERY THINKING
──────────────────────────────────────────────────────────────────────────────

┌─────────────────────────┐        ┌─────────────────────────────────────┐
│ Local component failure │        │ Site or cluster failure             │
├─────────────────────────┤        ├─────────────────────────────────────┤
│ One pod restarts        │        │ Control plane unavailable           │
│ One drive fails         │        │ Storage backend unavailable         │
│ One node drains         │        │ Entire region or data center lost   │
└─────────────────────────┘        └─────────────────────────────────────┘
            │                                      │
            ▼                                      ▼
┌─────────────────────────┐        ┌─────────────────────────────────────┐
│ MinIO healing and       │        │ Replication, external backup,       │
│ Kubernetes rescheduling │        │ restore testing, and runbooks       │
└─────────────────────────┘        └─────────────────────────────────────┘
```

When you design alerts, pair symptoms with operator actions. An alert for offline drives should point to commands that identify the affected pod, PVC, node, and physical or virtual disk. An alert for rising S3 errors should distinguish authentication failures, client misconfiguration, capacity exhaustion, and backend health. Alerts that merely say "MinIO is bad" are too vague to shorten an incident.

**Pause and predict:** If `minio_s3_requests_errors_total` rises but drive and node metrics remain healthy, what is your first hypothesis? A client-side change, credential expiration, bucket policy regression, TLS trust issue, or endpoint-style mismatch is more likely than disk failure. Storage health metrics and request error metrics answer different questions.

---

## When to Choose MinIO, Cloud S3, or Ceph

MinIO is a strong option, but it is not automatically the right answer. Platform engineering is mostly trade-off management: who operates the service, where the data path lives, what failure domains are acceptable, and which API the application expects. The best design may use MinIO for local hot-path artifacts and cloud S3 for off-site retention, or Ceph for block storage and MinIO for S3-compatible workloads.

Cloud S3 is usually the right default when you want a managed global object store, broad ecosystem integration, and minimal operational ownership. MinIO is attractive when you need local performance, air-gapped operation, predictable internal traffic, S3 compatibility, or control over data placement. Ceph is attractive when you need a broader storage system that can provide block, file, and object interfaces, though that breadth comes with operational complexity.

| Requirement | MinIO | Cloud S3 | Ceph |
|-------------|-------|----------|------|
| S3-compatible API | Strong fit | Native fit | Available through object gateway |
| In-cluster low-latency access | Strong fit when deployed near workloads | Depends on network and region | Possible, depending on deployment |
| Managed operations | Platform team owns it | Provider owns much of it | Platform team owns it |
| Block storage for PVCs | Not a fit | Not a fit | Strong fit through RBD |
| Air-gapped environments | Strong fit | Usually not a fit | Strong fit |
| Broad multi-interface storage | Object only | Object only | Block, file, and object |
| Local cost control | Strong fit with owned capacity | Depends on provider pricing | Strong fit with owned capacity |
| Disaster recovery simplicity | Requires deliberate replication | Strong managed options | Requires deliberate replication |

A useful senior design pattern is to separate hot-path object storage from retention storage. For example, training jobs may read and write artifacts to MinIO inside the cluster, while a scheduled replication process copies promoted models or backups to another MinIO cluster or a managed cloud bucket. That design keeps the fast path local without pretending that one cluster is its own disaster-recovery site.

The wrong pattern is using MinIO because it feels cheaper while ignoring the cost of operations. Someone must patch it, monitor it, manage disks, test restores, rotate credentials, expand capacity, and respond to alerts. MinIO can reduce cloud bills and improve performance, but those benefits are real only when the platform team is prepared to operate the service as critical infrastructure.

---

## Did You Know?

- **MinIO is designed around S3 compatibility rather than POSIX compatibility.** That design choice is why it works well with tools like MLflow, Velero, Loki, Tempo, and BuildKit, but it is also why you should not treat it as a mounted filesystem for databases or applications that need file-locking semantics.

- **Erasure coding changes the durability conversation from "how many copies" to "how many shards can disappear."** This is more storage-efficient than full replication for many object workloads, but it only helps when shards are placed across meaningful failure domains.

- **Path-style S3 access is often the difference between a working in-cluster integration and a confusing DNS failure.** Kubernetes Services have predictable names, while virtual-hosted bucket names require DNS patterns that internal clusters may not provide.

- **A MinIO bucket without lifecycle rules can become an operational liability even when the service is healthy.** Logs, traces, build caches, and temporary experiment artifacts often grow quietly until capacity pressure turns a housekeeping issue into an outage.

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Using MinIO for workloads that require block or POSIX filesystem semantics | S3 object operations do not provide the same write, lock, and mount behavior as a disk or shared filesystem. | Use PVC-backed block storage or a filesystem service for those workloads, and reserve MinIO for object workflows. |
| Treating Running pods as proof of a durable storage design | Kubernetes readiness does not prove that drives, nodes, and zones are separated into useful failure domains. | Map pods, PVCs, nodes, zones, and backing storage before calling the tenant production-ready. |
| Putting root credentials into application Secrets | Root credentials create broad blast radius and make audit or revocation difficult. | Create per-application users or service accounts with bucket-scoped policies. |
| Forgetting `s3ForcePathStyle` or equivalent client settings | Virtual-hosted bucket addressing can fail against internal Kubernetes Service DNS. | Configure path-style access when using in-cluster MinIO endpoints unless your DNS and certificates explicitly support virtual-hosted style. |
| Skipping lifecycle rules for logs, traces, backups, or caches | Object growth continues silently until capacity pressure affects every tenant. | Define retention by bucket and validate lifecycle rules with `mc ilm ls`. |
| Assuming local MinIO is disaster recovery for the same cluster | A full cluster or storage-backend loss can remove both the workload and its backup target. | Replicate critical buckets to another cluster, site, or managed object store and test restores. |
| Ignoring heal and drive metrics | A cluster can serve traffic while redundancy is degraded, leaving less margin for the next failure. | Alert on offline nodes, offline drives, heal errors, capacity trend, and request errors. |
| Layering replication without understanding the total cost | MinIO erasure coding on top of a replicated StorageClass can consume more capacity than planned. | Document redundancy at each layer and choose the minimum design that satisfies durability and recovery requirements. |

---

## Quiz

### Question 1

Your team deploys MinIO for ML artifacts in a Kubernetes cluster. The tenant has four MinIO pods and eight PVCs, but all pods land on the same worker node. The operator reports the tenant as ready. What risk remains, and what would you change before calling this production-ready?

<details>
<summary>Show Answer</summary>

The remaining risk is failure-domain collapse. The tenant may be ready at the Kubernetes and MinIO control-plane level, but one worker-node outage can remove every MinIO server at the same time. That defeats the purpose of distributing erasure-coded shards across multiple servers.

Before calling it production-ready, add scheduling controls such as topology spread constraints, pod anti-affinity, and node or zone-aware placement where the cluster supports it. Also verify where the PVCs are physically or logically backed, because spreading pods across nodes is less useful if all volumes depend on the same underlying failure point.
</details>

### Question 2

An application can create buckets through `mc`, but the same application fails when writing to `s3://reports/2026/run.json` from inside the cluster. Logs show DNS lookups for `reports.minio.minio-tenant.svc` failing. What is the likely configuration issue, and how would you fix it?

<details>
<summary>Show Answer</summary>

The client is likely using virtual-hosted-style S3 addressing, where the bucket name becomes part of the hostname. Kubernetes DNS normally resolves the Service name, such as `minio.minio-tenant.svc`, but not arbitrary bucket-prefixed hostnames.

Configure the client for path-style access, using the equivalent of `s3ForcePathStyle: true`, `forcePathStyle: true`, or `use_path_style=true` depending on the tool. The endpoint should remain the MinIO Service name, and the bucket should appear in the URL path rather than the hostname.
</details>

### Question 3

A platform team wants to use MinIO as the target for Velero backups in the same cluster that runs all application workloads. They say this gives them disaster recovery because Velero now writes to object storage. How would you evaluate that claim?

<details>
<summary>Show Answer</summary>

The claim is only partly true. MinIO in the same cluster can help recover from namespace mistakes, accidental deletes, or some application-level failures. It does not automatically provide disaster recovery for full cluster loss, storage-backend loss, or a site outage.

For disaster recovery, critical backups should be replicated or copied to a separate failure domain, such as another cluster, another site, or a managed object store. The team should also test restores from that external copy, because an untested backup target is only an assumption.
</details>

### Question 4

A Loki deployment using MinIO starts consuming capacity much faster after a product launch. MinIO nodes and drives are healthy, and request latency is normal. What should you check before adding storage, and why?

<details>
<summary>Show Answer</summary>

Check Loki retention, compaction, schema configuration, object growth rate, and the bucket lifecycle policy before adding disks. The healthy MinIO metrics indicate that the storage service is handling requests, but they do not prove that the data-retention policy is correct.

Adding storage may buy time, but it does not fix unbounded retention or a misconfigured logging pipeline. The better response is to confirm what data should be retained, enforce that policy in Loki and bucket lifecycle rules, and then expand capacity only if the corrected retention target still requires it.
</details>

### Question 5

A team stores BuildKit cache, MLflow artifacts, and compliance backups in one shared MinIO bucket using one shared access key. During an incident, a CI job deletes several backup objects. What design choices caused the blast radius, and how would you redesign it?

<details>
<summary>Show Answer</summary>

The blast radius came from sharing both the bucket and the credentials across unrelated workloads. A CI cache job should not have permission to delete compliance backups, and backup retention should not depend on the behavior of build tooling.

Redesign with separate buckets for BuildKit cache, MLflow artifacts, and backups. Create scoped users or service accounts with policies limited to the required bucket and actions. Apply different lifecycle rules to each bucket so short-lived cache objects and long-lived backup objects follow different retention policies.
</details>

### Question 6

After replacing a failed node, MinIO is serving traffic again, but a dashboard shows healing errors and fewer online drives than expected. A teammate says the incident is over because applications can read and write objects. What is your response?

<details>
<summary>Show Answer</summary>

The incident is not fully resolved just because the S3 API is serving traffic. MinIO may be operating with reduced redundancy, which means the next drive or node failure could cause a larger outage or data-loss risk.

Investigate the offline drive count, affected pods, PVCs, node events, and heal errors. Run appropriate `mc admin info` and healing diagnostics, then confirm that the expected number of drives is online and healing completes without errors. Application success is a symptom check, not a redundancy check.
</details>

### Question 7

A database team asks to move a write-heavy PostgreSQL data directory to MinIO because the S3-compatible service has excellent throughput numbers. How would you explain the problem with that plan and propose a better storage option?

<details>
<summary>Show Answer</summary>

PostgreSQL needs filesystem and block-device semantics such as ordered writes, syncing, and data-directory behavior that S3 object storage does not provide. MinIO is fast for object operations, but it is not a drop-in replacement for a mounted database volume.

Use a proper PersistentVolume backed by block storage for the PostgreSQL data directory. MinIO may still be useful for database backups, exported reports, WAL archive workflows that explicitly support S3, or long-term dump retention, but not as the live database filesystem.
</details>

### Question 8

You are reviewing a MinIO proposal where the team uses erasure coding inside MinIO and a StorageClass that already keeps three replicated copies of every PVC. The design is durable but expensive. What question should you ask, and how might the answer change the architecture?

<details>
<summary>Show Answer</summary>

Ask what durability and recovery objectives the workload actually needs, and where redundancy is being counted. The team may be paying for replication at the storage layer and erasure coding at the MinIO layer without understanding the combined capacity cost.

If the workload needs strong local durability and the platform accepts the cost, the design may be justified. If the goal is efficient object storage, the team might choose a different StorageClass, adjust MinIO topology, or use replication to another failure domain instead of stacking multiple local redundancy mechanisms blindly.
</details>

---

## Hands-On Exercise

### Task: Deploy MinIO, Create Buckets, Scope Access, and Verify Object Behavior

In this exercise you will deploy a standalone MinIO instance in a kind cluster, create workload-specific buckets, upload and download objects, verify checksums, apply a lifecycle rule, and inspect basic operational state. The standalone deployment is intentionally smaller than a production tenant so the workflow is easy to run locally. The reasoning you practice still applies to operator-managed tenants.

### Success Criteria

- [ ] A kind cluster named `minio-lab` is running.
- [ ] A MinIO pod and Service are deployed in the `minio` namespace.
- [ ] The `mc` client can connect to MinIO through a local port-forward.
- [ ] Separate buckets exist for ML artifacts, backups, logs, and build cache.
- [ ] A test object is uploaded, downloaded, and verified with matching checksums.
- [ ] A lifecycle rule is applied to the build-cache bucket and verified.
- [ ] `mc admin info` shows the MinIO server is reachable.
- [ ] Cleanup removes the port-forward and kind cluster.

### Step 1: Create the Lab Cluster

```bash
kind create cluster --name minio-lab
kubectl cluster-info --context kind-minio-lab
```

### Step 2: Deploy Standalone MinIO

```bash
kubectl create namespace minio

cat > minio-standalone.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: minio-credentials
  namespace: minio
stringData:
  root-user: "admin"
  root-password: "minio-secret-key-change-me"
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: minio-data
  namespace: minio
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: minio
spec:
  replicas: 1
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
        - name: minio
          image: quay.io/minio/minio:RELEASE.2024-11-07T00-52-20Z
          command:
            - /bin/sh
            - -c
            - minio server /data --console-address ":9001"
          env:
            - name: MINIO_ROOT_USER
              valueFrom:
                secretKeyRef:
                  name: minio-credentials
                  key: root-user
            - name: MINIO_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: minio-credentials
                  key: root-password
          ports:
            - containerPort: 9000
              name: api
            - containerPort: 9001
              name: console
          volumeMounts:
            - name: data
              mountPath: /data
          readinessProbe:
            httpGet:
              path: /minio/health/ready
              port: 9000
            initialDelaySeconds: 10
            periodSeconds: 10
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: minio-data
---
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: minio
spec:
  ports:
    - port: 9000
      targetPort: 9000
      name: api
    - port: 9001
      targetPort: 9001
      name: console
  selector:
    app: minio
EOF

kubectl apply -f minio-standalone.yaml
kubectl -n minio rollout status deployment/minio --timeout=120s
kubectl -n minio get pods,pvc,svc
```

### Step 3: Connect with the MinIO Client

If you do not already have `mc`, install it from the MinIO client package for your operating system. On macOS with Homebrew, `brew install minio/stable/mc` is the quickest path. On Linux, use the MinIO client release appropriate for your architecture.

```bash
kubectl -n minio port-forward svc/minio 9000:9000 9001:9001 &
MINIO_PF_PID=$!
sleep 3

mc alias set lab http://127.0.0.1:9000 admin minio-secret-key-change-me
mc admin info lab
```

### Step 4: Create Buckets for Different Workloads

```bash
mc mb --ignore-existing lab/ml-artifacts
mc mb --ignore-existing lab/velero-backups
mc mb --ignore-existing lab/loki-chunks
mc mb --ignore-existing lab/buildkit-cache

mc ls lab/
```

After creating the buckets, pause and connect the exercise back to the design lesson. These buckets represent different retention and access patterns. ML artifacts may need promotion rules, backups may need stronger retention, logs may be controlled by observability policy, and build cache can usually expire quickly.

### Step 5: Upload, Download, and Verify Objects

```bash
echo "Hello from MinIO on Kubernetes" > /tmp/minio-test-file.txt
dd if=/dev/urandom of=/tmp/minio-large-file.bin bs=1M count=10 2>/dev/null

mc cp /tmp/minio-test-file.txt lab/ml-artifacts/
mc cp /tmp/minio-large-file.bin lab/ml-artifacts/models/

mc ls lab/ml-artifacts/
mc ls lab/ml-artifacts/models/

md5sum /tmp/minio-large-file.bin
mc cp lab/ml-artifacts/models/minio-large-file.bin /tmp/minio-downloaded-file.bin
md5sum /tmp/minio-downloaded-file.bin

diff <(md5sum /tmp/minio-large-file.bin | cut -d' ' -f1) \
     <(md5sum /tmp/minio-downloaded-file.bin | cut -d' ' -f1) \
  && echo "CHECKSUM MATCH - object round trip passed" \
  || echo "CHECKSUM MISMATCH - investigate upload or download path"
```

The checksum step is not busywork. Object storage integrations often fail in ways that are not obvious from a successful command alone, especially when scripts hide errors or upload the wrong file. Verifying content gives you a simple end-to-end proof that the client, endpoint, bucket, object path, and download path all behaved as expected.

### Step 6: Apply and Verify a Lifecycle Rule

```bash
cat > /tmp/buildkit-cache-lifecycle.json << 'EOF'
{
  "Rules": [
    {
      "ID": "expire-old-build-cache",
      "Status": "Enabled",
      "Expiration": {
        "Days": 14
      }
    }
  ]
}
EOF

mc ilm import lab/buildkit-cache < /tmp/buildkit-cache-lifecycle.json
mc ilm ls lab/buildkit-cache
```

### Step 7: Inspect Health and Practice Failure Thinking

```bash
mc admin info lab
mc ls --recursive lab/ml-artifacts/
kubectl -n minio describe pod -l app=minio
kubectl -n minio logs deployment/minio --tail=50
```

Use the output to answer three questions in your own notes. First, which endpoint did the client use? Second, which bucket policy or credential would you scope for an application instead of using root? Third, what would be different in a production tenant with multiple pods and PVCs? These questions force you to move from command execution to operational reasoning.

### Step 8: Clean Up

```bash
kill "$MINIO_PF_PID" 2>/dev/null || true
kind delete cluster --name minio-lab
rm -f minio-standalone.yaml
```

---

## Next Module

Next: [Module 16.3: Longhorn](../module-16.3-longhorn/) - lightweight distributed block storage for Kubernetes workloads that need PVC-backed volumes rather than S3-compatible object storage.
