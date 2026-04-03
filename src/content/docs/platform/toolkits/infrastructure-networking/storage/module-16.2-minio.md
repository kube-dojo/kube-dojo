---
title: "Module 16.2: MinIO - High-Performance Object Storage for Kubernetes"
slug: platform/toolkits/infrastructure-networking/storage/module-16.2-minio
sidebar:
  order: 3
---
## Complexity: [MEDIUM]
## Time to Complete: 45-50 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Distributed Systems Foundation](../../../foundations/distributed-systems/) - Replication, erasure coding
- Kubernetes fundamentals (Deployments, Services, PVCs, Secrets)
- Basic understanding of S3 API concepts (buckets, objects, presigned URLs)
- [Module 16.1: Rook/Ceph](../module-16.1-rook-ceph/) (recommended, not required)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy MinIO for high-performance S3-compatible object storage on Kubernetes**
- **Configure MinIO with erasure coding, bucket policies, and identity management for multi-tenant access**
- **Implement MinIO bucket replication and lifecycle rules for data management across environments**
- **Integrate MinIO as a backing store for Velero backups, MLflow artifacts, and application data**


## Why This Module Matters

**The $1.7 Million Data Pipeline That Almost Died**

The ML engineering team at a healthcare analytics startup was two weeks from their Series B funding round when their data pipeline collapsed. They had been storing 40TB of medical imaging data, trained models, and experiment artifacts on AWS S3—all routed through a single region.

Then the AWS bill arrived: $23,000 for the month, and climbing 30% month-over-month. Worse, their model training jobs in Kubernetes were spending 60% of their time waiting on S3 network transfers rather than doing actual computation.

| Problem | Impact |
|---------|--------|
| S3 egress fees | $8,400/month for cross-AZ data transfer |
| Training latency | 60% of GPU time wasted on I/O waits |
| Vendor lock-in | S3-specific APIs embedded in 200+ scripts |
| Single-region data | No DR for irreplaceable medical datasets |

Their principal engineer proposed MinIO. Within two weeks, they deployed a 12-node MinIO cluster inside their existing Kubernetes infrastructure. The results changed their trajectory:

| Metric | AWS S3 | MinIO on K8s |
|--------|--------|-------------|
| Object read latency | 15-80ms (network) | 2-5ms (local) |
| Training job duration | 4.2 hours | 1.6 hours |
| Monthly storage cost | $23,000 | $3,200 (hardware amortized) |
| Egress fees | $8,400/month | $0 |
| S3 API compatible | Yes | Yes (zero code changes) |

The model training speedup alone justified the migration—they shipped three additional model versions before the funding round, directly contributing to a $28M Series B.

**MinIO is the fastest S3-compatible object storage you can self-host, and it runs natively on Kubernetes. Same S3 API, local-network speed, zero egress fees.**

---

## Did You Know?

- **MinIO consistently tops S3-compatible benchmarks at 325+ GiB/s throughput** — On 32 NVMe drives, MinIO has demonstrated read throughput exceeding 325 GiB/s. That is faster than most S3 implementations including some cloud providers' own offerings. The secret is a purpose-built Go codebase with zero dependencies and direct-to-disk I/O.

- **MinIO is the default storage backend for MLflow, Kubeflow, and most ML platforms** — When ML frameworks need an artifact store, they default to S3. MinIO provides that S3 API locally, eliminating network roundtrips and egress costs. Hugging Face, LangChain, and Ray all document MinIO as a recommended backend.

- **Grafana Loki and Tempo use MinIO as their primary self-hosted backend** — When you deploy Loki for logs or Tempo for traces, they need object storage. In self-hosted environments, MinIO is the standard answer. Your observability stack probably already depends on S3-compatible storage.

- **MinIO uses erasure coding instead of replication to save space** — While Ceph replicates data 3x (300% overhead), MinIO uses Reed-Solomon erasure coding. With the default EC:4 configuration on 8 drives, you get the same fault tolerance as 3x replication but use only 2x the raw capacity. Half the disk cost for the same durability.

---

## MinIO Architecture

```
MINIO ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                       MINIO CLUSTER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  S3 API Layer                                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Full S3 API compatibility (GetObject, PutObject, etc.) │  │
│  │  • Bucket notifications (webhook, AMQP, Kafka, NATS)      │  │
│  │  • IAM policies and STS (Security Token Service)          │  │
│  │  • Versioning, lifecycle rules, object locking            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            ▼                                     │
│  Erasure Coding Layer                                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Reed-Solomon erasure coding                            │  │
│  │  • Data + parity shards across drives                     │  │
│  │  • Bitrot protection (HighwayHash checksums)              │  │
│  │  • Self-healing: automatically repairs corrupt shards     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            ▼                                     │
│  Distributed Mode (Server Pools)                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  Server Pool 1              Server Pool 2                  │  │
│  │  ┌────┐ ┌────┐ ┌────┐     ┌────┐ ┌────┐ ┌────┐          │  │
│  │  │Srv1│ │Srv2│ │Srv3│     │Srv4│ │Srv5│ │Srv6│          │  │
│  │  │    │ │    │ │    │     │    │ │    │ │    │          │  │
│  │  │d1  │ │d1  │ │d1  │     │d1  │ │d1  │ │d1  │          │  │
│  │  │d2  │ │d2  │ │d2  │     │d2  │ │d2  │ │d2  │          │  │
│  │  │d3  │ │d3  │ │d3  │     │d3  │ │d3  │ │d3  │          │  │
│  │  │d4  │ │d4  │ │d4  │     │d4  │ │d4  │ │d4  │          │  │
│  │  └────┘ └────┘ └────┘     └────┘ └────┘ └────┘          │  │
│  │                                                            │  │
│  │  Erasure Set: data sharded across drives in the pool       │  │
│  │  Each object = N data shards + M parity shards             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

ERASURE CODING EXAMPLE (4 data + 4 parity on 8 drives):
─────────────────────────────────────────────────────────────────

Original Object: [████████████████████████████████]

Split into shards:
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Data 1│ │Data 2│ │Data 3│ │Data 4│ │Par. 1│ │Par. 2│ │Par. 3│ │Par. 4│
│Drive1│ │Drive2│ │Drive3│ │Drive4│ │Drive5│ │Drive6│ │Drive7│ │Drive8│
└──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘

Can lose ANY 4 of 8 drives and still read the object.
Storage overhead: 2x (not 3x like replication).
```

### MinIO on Kubernetes

```
MINIO OPERATOR ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                             │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  MINIO OPERATOR                             │  │
│  │                                                             │  │
│  │  Watches CRDs:                                              │  │
│  │  • Tenant  → Deploys MinIO StatefulSet, Services, TLS       │  │
│  │                                                             │  │
│  │  Manages:                                                   │  │
│  │  • Auto TLS certificate generation                          │  │
│  │  • Tenant scaling (add server pools)                        │  │
│  │  • Console (Web UI) deployment                              │  │
│  │  • Health monitoring                                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    MINIO TENANT                             │  │
│  │                                                             │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │ minio-0  │  │ minio-1  │  │ minio-2  │  │ minio-3  │  │  │
│  │  │ PVC×2    │  │ PVC×2    │  │ PVC×2    │  │ PVC×2    │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │  │
│  │                                                             │  │
│  │  Services:                                                  │  │
│  │  • minio.tenant-ns.svc    (S3 API, port 443)               │  │
│  │  • console.tenant-ns.svc  (Web UI, port 9443)              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installation via Helm

### Step 1: Install the MinIO Operator

```bash
# Add the MinIO Operator Helm repository
helm repo add minio-operator https://operator.min.io
helm repo update

# Install the operator
helm install --create-namespace --namespace minio-operator \
  minio-operator minio-operator/operator \
  --version 6.0.4

# Verify operator is running
kubectl -n minio-operator rollout status deployment/minio-operator
```

### Step 2: Create a MinIO Tenant

```yaml
# minio-tenant.yaml
apiVersion: minio.min.io/v2
kind: Tenant
metadata:
  name: minio
  namespace: minio-tenant
spec:
  image: quay.io/minio/minio:RELEASE.2024-11-07T00-52-20Z
  pools:
    - name: pool-0
      servers: 4                 # 4 MinIO server pods
      volumesPerServer: 2        # 2 PVCs per server = 8 drives total
      volumeClaimTemplate:
        metadata:
          name: data
        spec:
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: 50Gi
          # storageClassName: rook-ceph-block  # Or your StorageClass
      resources:
        requests:
          cpu: "500m"
          memory: "1Gi"
        limits:
          cpu: "2"
          memory: "4Gi"
  mountPath: /export
  requestAutoCert: true          # Auto-generate TLS certificates
  users:
    - name: minio-user-secret
  features:
    domains:
      console: console.minio.example.com
      minio:
        - minio.example.com
```

```bash
# Create the namespace and credentials secret
kubectl create namespace minio-tenant

kubectl -n minio-tenant create secret generic minio-user-secret \
  --from-literal=CONSOLE_ACCESS_KEY=admin \
  --from-literal=CONSOLE_SECRET_KEY=minio-secret-key-change-me

# Deploy the tenant
kubectl apply -f minio-tenant.yaml

# Wait for the tenant to be ready
kubectl -n minio-tenant get pods -w
# Wait until all minio-pool-0-{0,1,2,3} pods are Running
```

### Lightweight Alternative: Standalone MinIO (No Operator)

For development and testing, you can run MinIO without the operator:

```bash
# Single-node MinIO for dev/test
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

## Use Cases

### 1. ML Model and Artifact Storage

```yaml
# mlflow-with-minio.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow
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
            - --backend-store-uri=sqlite:///mlflow/mlflow.db
            - --default-artifact-root=s3://mlflow-artifacts/
            - --host=0.0.0.0
          env:
            - name: MLFLOW_S3_ENDPOINT_URL
              value: "http://minio.minio-tenant.svc:443"
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
          ports:
            - containerPort: 5000
```

### 2. Loki Log Backend

```yaml
# loki-with-minio-storage.yaml (values for Helm chart)
loki:
  storage:
    type: s3
    s3:
      endpoint: minio.minio-tenant.svc:443
      bucketnames: loki-chunks
      access_key_id: ${MINIO_ACCESS_KEY}
      secret_access_key: ${MINIO_SECRET_KEY}
      s3ForcePathStyle: true
      insecure: false
  schemaConfig:
    configs:
      - from: "2024-01-01"
        store: tsdb
        object_store: s3
        schema: v13
        index:
          prefix: index_
          period: 24h
```

### 3. Velero Backup Target

```yaml
# velero-with-minio.yaml
apiVersion: v1
kind: Secret
metadata:
  name: minio-credentials
  namespace: velero
stringData:
  cloud: |
    [default]
    aws_access_key_id=admin
    aws_secret_access_key=minio-secret-key-change-me
---
# Install Velero pointing to MinIO
# velero install \
#   --provider aws \
#   --plugins velero/velero-plugin-for-aws:v1.10.0 \
#   --bucket velero-backups \
#   --secret-file ./minio-credentials \
#   --backup-location-config \
#     region=us-east-1,s3ForcePathStyle=true,s3Url=http://minio.minio-tenant.svc:443
```

### 4. Container Image Build Cache

```yaml
# buildkit-with-minio-cache.yaml
apiVersion: v1
kind: Pod
metadata:
  name: buildkit
spec:
  containers:
    - name: buildkit
      image: moby/buildkit:latest
      args:
        - --oci-worker-no-process-sandbox
      env:
        - name: AWS_ACCESS_KEY_ID
          value: "admin"
        - name: AWS_SECRET_ACCESS_KEY
          value: "minio-secret-key-change-me"
      # Use: buildctl build \
      #   --export-cache type=s3,endpoint_url=http://minio.minio-tenant.svc:443,region=us-east-1,bucket=buildkit-cache \
      #   --import-cache type=s3,endpoint_url=http://minio.minio-tenant.svc:443,region=us-east-1,bucket=buildkit-cache \
      #   ...
```

---

## Working with MinIO

### The `mc` (MinIO Client) CLI

```bash
# Install mc (MinIO Client)
# macOS:
brew install minio/stable/mc
# Linux:
curl -O https://dl.min.io/client/mc/release/linux-amd64/mc && chmod +x mc

# Configure an alias for your MinIO instance
mc alias set myminio http://localhost:9000 admin minio-secret-key-change-me

# Bucket operations
mc mb myminio/my-bucket                    # Create bucket
mc ls myminio/                             # List buckets
mc ls myminio/my-bucket                    # List objects in bucket

# Object operations
mc cp myfile.tar.gz myminio/my-bucket/     # Upload object
mc cp myminio/my-bucket/myfile.tar.gz ./   # Download object
mc cat myminio/my-bucket/config.json       # Print object contents
mc rm myminio/my-bucket/old-file.tar.gz    # Delete object

# Useful admin commands
mc admin info myminio                      # Cluster info
mc admin heal myminio                      # Trigger healing scan
mc admin prometheus generate myminio       # Generate Prometheus config
```

### Bucket Notifications

```bash
# Set up webhook notification when objects are created
mc event add myminio/my-bucket arn:minio:sqs::1:webhook \
  --event put \
  --suffix .csv

# This triggers a webhook POST to your endpoint whenever a .csv is uploaded
# Useful for triggering ML training pipelines on new data
```

---

## Monitoring MinIO

```yaml
# ServiceMonitor for Prometheus
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

```
KEY MINIO METRICS
─────────────────────────────────────────────────────────────────

Capacity:
├── minio_cluster_capacity_usable_total_bytes     # Total usable
├── minio_cluster_capacity_usable_free_bytes      # Free space
├── minio_bucket_usage_total_bytes                # Per-bucket usage

Performance:
├── minio_s3_requests_total                       # Request count
├── minio_s3_requests_errors_total                # Error count
├── minio_s3_ttfb_seconds                         # Time to first byte
├── minio_s3_traffic_received_bytes               # Inbound traffic
├── minio_s3_traffic_sent_bytes                   # Outbound traffic

Health:
├── minio_cluster_nodes_online_total              # Online servers
├── minio_cluster_nodes_offline_total             # Should be 0
├── minio_cluster_drive_online_total              # Online drives
├── minio_cluster_drive_offline_total             # Should be 0
├── minio_heal_objects_errors_total               # Heal failures
```

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Using fewer than 4 servers for distributed mode | Cannot form erasure sets | Minimum 4 servers for distributed MinIO |
| Skipping TLS | S3 credentials transmitted in plaintext | Always use `requestAutoCert: true` or provide certs |
| Not setting lifecycle rules | Old objects consume storage forever | Configure lifecycle policies to expire old data |
| Using root credentials in apps | Security risk, no audit trail | Create per-app service accounts with scoped policies |
| Ignoring drive health metrics | Silent data corruption | Monitor `minio_cluster_drive_offline_total`, enable bitrot scanning |
| Single server pool without DR | Cluster failure = data loss | Replicate to a second MinIO cluster or S3 for DR |
| Not using `s3ForcePathStyle: true` | Virtual-hosted style fails on internal DNS | Always set path-style for internal MinIO endpoints |
| PVCs on slow storage | MinIO performance bottlenecked by disk I/O | Use NVMe-backed StorageClass or local-path provisioner |

---

## Hands-On Exercise

### Task: Deploy MinIO, Create Buckets, and Upload/Download Objects

**Objective**: Deploy a MinIO instance on Kubernetes, create a bucket, and verify object upload and download using the `mc` CLI.

**Success Criteria**:
1. MinIO pod running and accessible
2. Bucket created via `mc` CLI
3. File uploaded and downloaded successfully with checksum verification
4. Bucket lifecycle policy configured
5. MinIO console (Web UI) accessible

### Steps

```bash
# 1. Create a kind cluster
kind create cluster --name minio-lab

# 2. Deploy standalone MinIO for the lab (simpler than operator)
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

# 3. Port-forward to access MinIO
kubectl -n minio port-forward svc/minio 9000:9000 9001:9001 &
MINIO_PF_PID=$!
sleep 3

# 4. Configure mc CLI
mc alias set lab http://localhost:9000 admin minio-secret-key-change-me

# 5. Create buckets
mc mb lab/ml-artifacts
mc mb lab/backups
mc mb lab/logs

# Verify
mc ls lab/
# Should show: ml-artifacts, backups, logs

# 6. Upload objects
echo "Hello from MinIO on Kubernetes!" > /tmp/test-file.txt
dd if=/dev/urandom of=/tmp/large-file.bin bs=1M count=10 2>/dev/null

mc cp /tmp/test-file.txt lab/ml-artifacts/
mc cp /tmp/large-file.bin lab/ml-artifacts/models/

# 7. List objects
mc ls lab/ml-artifacts/
mc ls lab/ml-artifacts/models/

# 8. Download and verify checksum
md5sum /tmp/large-file.bin
mc cp lab/ml-artifacts/models/large-file.bin /tmp/downloaded-file.bin
md5sum /tmp/downloaded-file.bin
# Checksums should match

# 9. Set bucket lifecycle (expire objects after 30 days in backups bucket)
cat > /tmp/lifecycle.json << 'EOF'
{
  "Rules": [
    {
      "ID": "expire-old-backups",
      "Status": "Enabled",
      "Expiration": {
        "Days": 30
      }
    }
  ]
}
EOF

mc ilm import lab/backups < /tmp/lifecycle.json
mc ilm ls lab/backups

# 10. View MinIO server info
mc admin info lab

echo ""
echo "MinIO Console available at: http://localhost:9001"
echo "Login with: admin / minio-secret-key-change-me"
```

### Verification

```bash
# Confirm MinIO is healthy
mc admin info lab | grep -i status

# Confirm objects exist
mc ls --recursive lab/ml-artifacts/

# Confirm lifecycle policy
mc ilm ls lab/backups

# Confirm checksum match
diff <(md5sum /tmp/large-file.bin | cut -d' ' -f1) \
     <(md5sum /tmp/downloaded-file.bin | cut -d' ' -f1) \
  && echo "CHECKSUM MATCH - Test PASSED" \
  || echo "CHECKSUM MISMATCH - Test FAILED"

# Clean up
kill $MINIO_PF_PID 2>/dev/null
kind delete cluster --name minio-lab
```

---

## Quiz

### Question 1
How does MinIO's erasure coding differ from Ceph's default replication, and what is the storage overhead advantage?

<details>
<summary>Show Answer</summary>

Ceph's default replication stores **3 complete copies** of every object (3x storage overhead). MinIO uses **Reed-Solomon erasure coding**, which splits objects into data shards and parity shards.

With the default EC:4 configuration on 8 drives, MinIO stores 4 data shards + 4 parity shards. This provides the same fault tolerance (survive 4 drive failures) but uses only **2x storage overhead** instead of 3x. For a 100TB dataset, that is 200TB with MinIO versus 300TB with Ceph replication—saving 100TB of disk capacity.
</details>

### Question 2
What is the minimum number of servers required for MinIO distributed mode, and why?

<details>
<summary>Show Answer</summary>

**4 servers minimum** for distributed mode.

MinIO needs at least 4 drives to form an erasure set (minimum 2 data + 2 parity shards). In distributed mode, drives are spread across servers, so 4 servers with 1 drive each is the minimum. This allows surviving the loss of up to 2 drives (or servers) while maintaining read access. For write access, MinIO needs at least N/2+1 drives (3 out of 4) to be available.
</details>

### Question 3
Name three common Kubernetes use cases where MinIO serves as the storage backend.

<details>
<summary>Show Answer</summary>

1. **ML artifact storage** — MLflow, Kubeflow, and experiment tracking systems store model weights, datasets, and training artifacts in MinIO buckets via the S3 API.

2. **Observability backends** — Grafana Loki (logs) and Tempo (traces) use S3-compatible storage for their chunk stores. MinIO eliminates the need for cloud S3 in self-hosted deployments.

3. **Backup targets** — Velero and database backup tools write backups to S3-compatible storage. MinIO provides a local target that avoids egress fees and works in air-gapped environments.

Other valid answers include: container image build caches, CI/CD artifact storage, and data lake storage.
</details>

### Question 4
Why should you always set `s3ForcePathStyle: true` when configuring applications to use MinIO inside Kubernetes?

<details>
<summary>Show Answer</summary>

S3 supports two URL styles:
- **Virtual-hosted style**: `bucket-name.s3.amazonaws.com/key` — requires DNS resolution for `bucket-name.minio.svc`
- **Path style**: `minio.svc:9000/bucket-name/key` — works with standard Kubernetes DNS

Inside a Kubernetes cluster, virtual-hosted style fails because Kubernetes DNS does not resolve arbitrary subdomains of service names. Path style works because it uses the service name directly. Setting `s3ForcePathStyle: true` (or the equivalent in your SDK) tells the S3 client to use path-style URLs.
</details>

---

## Key Takeaways

1. **S3-compatible** — Drop-in replacement for AWS S3; existing code works with zero changes
2. **Erasure coding** — Better storage efficiency than replication (2x overhead vs 3x)
3. **High performance** — Purpose-built Go codebase, 325+ GiB/s throughput demonstrated
4. **ML ecosystem standard** — Default backend for MLflow, Kubeflow, and most ML platforms
5. **Observability backend** — Powers Loki, Tempo, and Thanos in self-hosted environments
6. **Kubernetes-native** — Operator manages Tenants with auto-TLS and scaling
7. **No egress fees** — In-cluster storage eliminates cloud data transfer costs
8. **Object storage only** — Not a block or filesystem solution; use Rook/Ceph or Longhorn for PVCs

---

## Next Steps

- **Next Module**: [Module 16.3: Longhorn](../module-16.3-longhorn/) — Lightweight distributed block storage
- **Related**: [ML Platforms Toolkit](../../data-ai-platforms/ml-platforms/) — ML workflows that use MinIO for artifact storage
- **Related**: [Observability Toolkit](../../observability-intelligence/observability/) — Loki and Tempo with MinIO backends

---

## Further Reading

- [MinIO Documentation](https://min.io/docs/minio/kubernetes/upstream/)
- [MinIO Operator GitHub](https://github.com/minio/operator)
- [MinIO Erasure Code Calculator](https://min.io/product/erasure-code-calculator)
- [S3 API Compatibility Reference](https://min.io/docs/minio/linux/reference/s3-api-compatibility.html)
- [MinIO Benchmarks](https://blog.min.io/minio-benchmarks/)

---

*"MinIO is what happens when you build S3-compatible object storage from scratch with performance as the primary design goal. It runs everywhere Kubernetes runs, and everything that speaks S3 can talk to it."*
