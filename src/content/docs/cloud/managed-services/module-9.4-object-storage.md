---
title: "Module 9.4: Object Storage Patterns (S3 / GCS / Blob)"
slug: cloud/managed-services/module-9.4-object-storage
sidebar:
  order: 5
---
**Complexity**: [MEDIUM] | **Time to Complete**: 2h | **Prerequisites**: Module 9.1 (Databases), Kubernetes PersistentVolumes and CSI concepts

## Why This Module Matters

In January 2024, a media streaming company stored 4.2 petabytes of video content in Amazon S3. Their transcoding pipeline ran on EKS -- 60 pods processing uploaded videos into multiple formats. The architecture worked, but their S3 costs were $127,000 per month. A junior engineer noticed that 78% of the data had not been accessed in over 90 days. The team implemented S3 Lifecycle policies, moving cold content to S3 Glacier Instant Retrieval. Monthly costs dropped to $41,000 -- a $86,000/month saving from a 15-line configuration change.

In the same cluster, the application team was generating pre-signed URLs for video playback. A misconfiguration set the URL expiration to 30 days instead of 4 hours. A security audit discovered that shared URLs were being forwarded and reused across the internet, effectively giving unauthenticated users perpetual access to premium content. The fix took five minutes; the brand damage took months to recover from.

Object storage is deceptively simple -- "just upload a file." But from Kubernetes, the integration patterns are rich and the pitfalls are expensive. This module teaches you how to access S3, GCS, and Azure Blob from pods using workload identity, CSI drivers for filesystem-style access, pre-signed URLs for secure client-side access, lifecycle policies for cost optimization, cross-region replication for disaster recovery, and bucket security hardening.

---

## Pod-to-Storage Access Patterns

There are three primary ways Kubernetes pods interact with object storage:

```
Pattern 1: SDK/API Access (most common)
  Pod --> AWS SDK / gcloud SDK --> S3/GCS/Blob API

Pattern 2: CSI Driver Mount (filesystem illusion)
  Pod --> /mnt/data/ --> CSI Driver --> S3/GCS/Blob

Pattern 3: Pre-signed URL (client-side access)
  Pod generates URL --> Client downloads directly from S3/GCS/Blob
```

### Pattern 1: SDK Access with Workload Identity

The most common and flexible pattern. Your application uses the cloud SDK to interact with the storage API directly.

```yaml
# AWS: Pod with IRSA for S3 access
apiVersion: v1
kind: ServiceAccount
metadata:
  name: storage-writer
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/S3WriterRole
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: video-processor
  namespace: production
spec:
  replicas: 5
  selector:
    matchLabels:
      app: video-processor
  template:
    metadata:
      labels:
        app: video-processor
    spec:
      serviceAccountName: storage-writer
      containers:
        - name: processor
          image: mycompany/video-processor:3.1.0
          env:
            - name: S3_BUCKET
              value: video-content-prod
            - name: S3_REGION
              value: us-east-1
          resources:
            requests:
              cpu: "2"
              memory: 4Gi
```

The IAM policy for the role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::video-content-prod",
        "arn:aws:s3:::video-content-prod/*"
      ]
    }
  ]
}
```

### GCP Workload Identity for GCS

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gcs-writer
  namespace: production
  annotations:
    iam.gke.io/gcp-service-account: gcs-writer@my-project.iam.gserviceaccount.com
```

```bash
# Bind the Kubernetes SA to the GCP SA
gcloud iam service-accounts add-iam-policy-binding \
  gcs-writer@my-project.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:my-project.svc.id.goog[production/gcs-writer]"

# Grant GCS access to the GCP SA
gcloud storage buckets add-iam-policy-binding gs://video-content-prod \
  --member="serviceAccount:gcs-writer@my-project.iam.gserviceaccount.com" \
  --role="roles/storage.objectUser"
```

### Azure Workload Identity for Blob

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: blob-writer
  namespace: production
  annotations:
    azure.workload.identity/client-id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  labels:
    azure.workload.identity/use: "true"
```

```bash
# Create federated credential
az identity federated-credential create \
  --identity-name blob-writer-identity \
  --resource-group myRG \
  --issuer "https://oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B716D3041E" \
  --subject system:serviceaccount:production:blob-writer

# Assign Storage Blob Data Contributor role
az role assignment create \
  --assignee-object-id $(az identity show -n blob-writer-identity -g myRG --query principalId -o tsv) \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/SUB_ID/resourceGroups/myRG/providers/Microsoft.Storage/storageAccounts/videostorage"
```

---

## CSI Drivers: Mounting Object Storage as a Filesystem

Sometimes your application expects a filesystem path, not an SDK. CSI drivers bridge this gap by presenting object storage as a POSIX-like mount.

### Mountpoint for Amazon S3 CSI Driver

```bash
# Install the driver as an EKS add-on
aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name aws-mountpoint-s3-csi-driver \
  --service-account-role-arn arn:aws:iam::123456789:role/S3CSIDriverRole
```

```yaml
# StorageClass for S3
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: s3-storage
provisioner: s3.csi.aws.com
parameters:
  bucketName: data-pipeline-prod
mountOptions:
  - allow-delete
  - region us-east-1
  - prefix data/
---
# PersistentVolumeClaim
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: s3-data
  namespace: production
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: s3-storage
  resources:
    requests:
      storage: 1Ti    # Not enforced -- S3 is unlimited, but required by K8s API
---
# Pod using the mount
apiVersion: v1
kind: Pod
metadata:
  name: data-processor
  namespace: production
spec:
  serviceAccountName: storage-writer
  containers:
    - name: processor
      image: mycompany/data-processor:1.0.0
      volumeMounts:
        - name: s3-data
          mountPath: /mnt/data
      command:
        - /bin/sh
        - -c
        - |
          # Read files from S3 as if they were local
          ls /mnt/data/
          cat /mnt/data/config.json

          # Write files -- they appear in S3
          echo '{"processed": true}' > /mnt/data/output/result.json
  volumes:
    - name: s3-data
      persistentVolumeClaim:
        claimName: s3-data
```

### CSI Driver Limitations

| Feature | Mountpoint for S3 | GCS FUSE | Azure Blob CSI |
|---------|-------------------|----------|----------------|
| Read performance | Good (sequential) | Good | Good |
| Write performance | Good (new files) | Moderate | Good |
| Random I/O | Poor (not a block device) | Poor | Poor |
| Rename/move | Not atomic | Not atomic | Not atomic |
| Hard links | Not supported | Not supported | Not supported |
| File locking | Not supported | Not supported | Not supported |
| Best for | Data pipelines, ML training data | Data analytics | Batch processing |

**Critical warning**: Object storage CSI mounts are NOT suitable for databases, caches, or any workload requiring random I/O, atomic operations, or POSIX compliance. Use them for read-heavy data pipelines and write-once-read-many workloads.

### GCS FUSE CSI Driver

```yaml
# GKE: Enable GCS FUSE on the cluster
# gcloud container clusters update my-cluster \
#   --update-addons GcsFuseCsiDriver=ENABLED

apiVersion: v1
kind: Pod
metadata:
  name: ml-trainer
  namespace: ml
  annotations:
    gke-gcsfuse/volumes: "true"
    gke-gcsfuse/cpu-limit: "500m"
    gke-gcsfuse/memory-limit: "256Mi"
spec:
  serviceAccountName: gcs-writer
  containers:
    - name: trainer
      image: mycompany/ml-trainer:2.0.0
      volumeMounts:
        - name: training-data
          mountPath: /data
          readOnly: true
  volumes:
    - name: training-data
      csi:
        driver: gcsfuse.csi.storage.gke.io
        readOnly: true
        volumeAttributes:
          bucketName: ml-training-data
          mountOptions: "implicit-dirs"
```

---

## Pre-Signed URLs: Secure Direct Access

Pre-signed URLs allow clients to upload or download directly from object storage without passing through your Kubernetes pods. This offloads bandwidth from your cluster and reduces latency.

### Architecture

```
1. Client requests upload URL from K8s API
2. K8s pod generates pre-signed PUT URL
3. Client uploads directly to S3/GCS/Blob
4. S3 sends event notification
5. Processing pipeline triggers

  Client                K8s Pod              S3/GCS
    |                     |                    |
    |-- POST /uploads --->|                    |
    |                     |-- generate URL --->|
    |<-- pre-signed URL --|                    |
    |                                          |
    |---------- PUT (direct upload) ---------->|
    |                                          |
    |<--------- 200 OK -----------------------|
```

### Generating Pre-Signed URLs

```python
# AWS S3 pre-signed URL generation
import boto3
from datetime import timedelta

s3 = boto3.client('s3')

def generate_upload_url(filename, content_type):
    """Generate a pre-signed URL for direct client upload."""
    key = f"uploads/{filename}"

    url = s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': 'user-uploads-prod',
            'Key': key,
            'ContentType': content_type,
            'ServerSideEncryption': 'aws:kms',
        },
        ExpiresIn=3600,  # 1 hour -- NOT 30 days!
        HttpMethod='PUT'
    )
    return url

def generate_download_url(key):
    """Generate a pre-signed URL for client download."""
    url = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': 'user-uploads-prod',
            'Key': key,
        },
        ExpiresIn=14400,  # 4 hours
    )
    return url
```

```python
# GCS pre-signed URL generation
from google.cloud import storage
from datetime import timedelta

client = storage.Client()
bucket = client.bucket('user-uploads-prod')

def generate_upload_url(filename, content_type):
    blob = bucket.blob(f"uploads/{filename}")
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="PUT",
        content_type=content_type,
    )
    return url
```

### Pre-Signed URL Security Best Practices

| Practice | Why |
|----------|-----|
| Set short expiration (1-4 hours for downloads, 15-60 min for uploads) | Limits exposure window if URL is leaked |
| Restrict Content-Type in upload URLs | Prevents uploading unexpected file types |
| Use separate buckets for uploads vs processed content | Isolates raw uploads from verified content |
| Require server-side encryption in the URL parameters | Ensures all uploads are encrypted at rest |
| Log all pre-signed URL generations | Audit trail for access tracking |
| Never expose bucket credentials; only expose URLs | Pre-signed URLs are scoped and temporary |

---

## Lifecycle Policies for Cost Optimization

Object storage costs are dominated by storage volume, not access. Moving infrequently accessed data to cheaper tiers can save 60-90%.

### Storage Tier Comparison

| Tier | AWS | GCP | Azure | Cost (per GB/month) | Use Case |
|------|-----|-----|-------|-------------------|----------|
| Hot | S3 Standard | Standard | Hot | $0.023 | Frequently accessed |
| Infrequent | S3 Standard-IA | Nearline | Cool | $0.0125 | Monthly access |
| Archive | S3 Glacier IR | Coldline | Cold | $0.004 | Quarterly access |
| Deep archive | S3 Glacier Deep | Archive | Archive | $0.00099 | Yearly/compliance |

### AWS S3 Lifecycle Configuration

```json
{
  "Rules": [
    {
      "ID": "optimize-video-storage",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "videos/"
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER_IR"
        },
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ]
    },
    {
      "ID": "cleanup-temp-uploads",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "tmp-uploads/"
      },
      "Expiration": {
        "Days": 7
      },
      "AbortIncompleteMultipartUpload": {
        "DaysAfterInitiation": 1
      }
    }
  ]
}
```

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket video-content-prod \
  --lifecycle-configuration file://lifecycle.json
```

### GCS Lifecycle

```bash
cat > /tmp/gcs-lifecycle.json << 'EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {"age": 30, "matchesPrefix": ["videos/"]}
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
        "condition": {"age": 90, "matchesPrefix": ["videos/"]}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"age": 7, "matchesPrefix": ["tmp-uploads/"]}
      }
    ]
  }
}
EOF

gcloud storage buckets update gs://video-content-prod \
  --lifecycle-file=/tmp/gcs-lifecycle.json
```

### Incomplete Multipart Upload Cleanup

One of the most overlooked cost leaks: incomplete multipart uploads. When a large upload fails midway, the partial parts sit in S3 forever, incurring storage charges. The lifecycle rule `AbortIncompleteMultipartUpload` cleans these up automatically.

```bash
# Check for incomplete multipart uploads
aws s3api list-multipart-uploads --bucket video-content-prod

# You may be shocked at how many orphaned parts exist
```

---

## Cross-Region Replication

For disaster recovery or serving content from multiple regions, cross-region replication copies objects automatically.

### AWS S3 Cross-Region Replication

```bash
# Enable versioning (required for replication)
aws s3api put-bucket-versioning \
  --bucket video-content-prod \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-versioning \
  --bucket video-content-dr \
  --versioning-configuration Status=Enabled

# Create replication configuration
cat > /tmp/replication.json << 'EOF'
{
  "Role": "arn:aws:iam::123456789:role/S3ReplicationRole",
  "Rules": [
    {
      "ID": "dr-replication",
      "Status": "Enabled",
      "Filter": {
        "Prefix": ""
      },
      "Destination": {
        "Bucket": "arn:aws:s3:::video-content-dr",
        "StorageClass": "STANDARD_IA",
        "ReplicationTime": {
          "Status": "Enabled",
          "Time": {"Minutes": 15}
        },
        "Metrics": {
          "Status": "Enabled",
          "EventThreshold": {"Minutes": 15}
        }
      },
      "DeleteMarkerReplication": {
        "Status": "Enabled"
      }
    }
  ]
}
EOF

aws s3api put-bucket-replication \
  --bucket video-content-prod \
  --replication-configuration file:///tmp/replication.json
```

### Multi-Region Access from Kubernetes

When pods in different regions need the closest bucket:

```yaml
# Region-specific ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: storage-config
  namespace: production
data:
  BUCKET_NAME: "video-content-prod"     # US region
  # In EU cluster, this would be: "video-content-eu"
  BUCKET_REGION: "us-east-1"
```

For AWS, S3 Multi-Region Access Points provide a single endpoint that automatically routes to the nearest bucket:

```bash
aws s3control create-multi-region-access-point \
  --account-id 123456789 \
  --details '{
    "Name": "video-global",
    "Regions": [
      {"Bucket": "video-content-prod"},
      {"Bucket": "video-content-eu"},
      {"Bucket": "video-content-ap"}
    ]
  }'
```

---

## Bucket Security Hardening

### Defense-in-Depth Configuration

```bash
# 1. Block all public access (do this first, always)
aws s3api put-public-access-block \
  --bucket video-content-prod \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# 2. Enable default encryption with KMS
aws s3api put-bucket-encryption \
  --bucket video-content-prod \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {
      "SSEAlgorithm": "aws:kms",
      "KMSMasterKeyID": "alias/s3-encryption-key"
    }, "BucketKeyEnabled": true}]
  }'

# 3. Enable access logging
aws s3api put-bucket-logging \
  --bucket video-content-prod \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "access-logs-prod",
      "TargetPrefix": "s3/video-content-prod/"
    }
  }'

# 4. Enable versioning (protects against accidental deletion)
aws s3api put-bucket-versioning \
  --bucket video-content-prod \
  --versioning-configuration Status=Enabled

# 5. Require TLS (deny non-HTTPS requests)
aws s3api put-bucket-policy --bucket video-content-prod \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Sid": "DenyNonHTTPS",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::video-content-prod",
        "arn:aws:s3:::video-content-prod/*"
      ],
      "Condition": {"Bool": {"aws:SecureTransport": "false"}}
    }]
  }'
```

### Bucket Security Checklist

| Control | AWS | GCP | Azure |
|---------|-----|-----|-------|
| Block public access | Public Access Block | Uniform bucket-level access | Disable anonymous access |
| Encryption at rest | SSE-S3/SSE-KMS | Google-managed/CMEK | Microsoft-managed/CMK |
| Encryption in transit | Enforce HTTPS via bucket policy | HTTPS by default | Require secure transfer |
| Access logging | Server access logging | Cloud Audit Logs | Diagnostic logs |
| Versioning | Bucket versioning | Object versioning | Blob versioning |
| Immutability | Object Lock | Retention policies | Immutable storage |

---

## Did You Know?

1. **Amazon S3 stores over 350 trillion objects** as of 2025 and handles tens of millions of requests per second. S3 was designed to provide 99.999999999% (11 nines) durability, meaning you would statistically lose one object per 10 million years if you stored 10 million objects.

2. **Incomplete multipart uploads are a hidden cost bomb.** A 2023 study by Vantage found that 15% of companies surveyed had over $10,000/month in charges from orphaned multipart upload parts. Most had no idea these partial uploads existed until they added lifecycle rules to clean them up.

3. **GCS FUSE can cache frequently-read files on local SSD**, reducing read latency from ~50ms (network) to ~1ms (local). This makes it practical for ML training workloads that read the same dataset files thousands of times per epoch. The cache is configured via annotations on the pod.

4. **Azure Blob Storage supports "immutable storage" with legal hold and time-based retention** that even a subscription owner cannot override. This is used by financial institutions for SEC 17a-4 compliance, where records must be stored in a non-erasable, non-rewritable format for specified retention periods.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Using CSI mount for database files | "It mounts like a disk, right?" | CSI object storage mounts lack POSIX semantics; use EBS/PD for databases |
| Setting pre-signed URL expiration to 30 days | Copy-pasted from example code | Use 1-4 hours for downloads, 15-60 minutes for uploads |
| Not blocking public access on new buckets | Default is private, but one wrong policy makes it public | Enable account-level public access block as a guardrail |
| Ignoring incomplete multipart uploads | Not visible in normal S3 listings | Add `AbortIncompleteMultipartUpload` lifecycle rule to every bucket |
| Using IAM user access keys instead of workload identity | "Quickest way to get it working" | Use IRSA (EKS), Workload Identity (GKE), or Workload Identity Federation (AKS) |
| Not enabling versioning before replication | Replication requires versioning, easy to forget | Script bucket creation to always enable versioning |
| Downloading large files through the pod when pre-signed URLs exist | Simpler code path | Generate pre-signed URLs to offload bandwidth; your pod should not proxy large files |
| No lifecycle policy on any bucket | "We will clean up later" | Define lifecycle rules at bucket creation time; "later" never comes |

---

## Quiz

<details>
<summary>1. What are the three primary patterns for accessing object storage from Kubernetes pods, and when would you choose each?</summary>

The three patterns are: (1) SDK/API access -- the most common, where your application uses the cloud SDK (boto3, google-cloud-storage) to interact with the storage API. Choose this for most application workloads. (2) CSI driver mount -- presents the bucket as a filesystem directory. Choose this for workloads that expect file paths (ML training, legacy applications, data pipelines). (3) Pre-signed URLs -- the pod generates a temporary URL and the client accesses storage directly. Choose this for uploads and downloads of large files to offload bandwidth from your cluster. The key decision factor is whether your application needs a filesystem interface, an API interface, or wants to delegate access to clients.
</details>

<details>
<summary>2. Why are CSI-mounted object storage volumes unsuitable for databases?</summary>

Object storage CSI drivers like Mountpoint for S3 and GCS FUSE present object storage with a filesystem interface, but they lack critical POSIX semantics. They do not support random I/O (seeking within files), atomic rename operations, file locking, or hard links. Databases rely on all of these: they seek within data files, use write-ahead logs with atomic operations, and depend on file locking for concurrency control. Using an object storage mount for a database would result in data corruption, because operations that the database assumes are atomic are not. Use EBS, Persistent Disk, or managed disks for database workloads.
</details>

<details>
<summary>3. How do incomplete multipart uploads become a hidden cost, and how do you prevent it?</summary>

When a large file upload using the multipart API fails midway (network error, timeout, client crash), the already-uploaded parts remain stored in the bucket. These parts do not appear in normal `ls` or `list-objects` output -- you need `list-multipart-uploads` to see them. They accumulate silently and incur standard storage charges. Over months, this can grow to terabytes of wasted storage. Prevention is a lifecycle rule: `AbortIncompleteMultipartUpload` with `DaysAfterInitiation: 1` automatically deletes partial uploads older than one day. This rule should be on every bucket you create.
</details>

<details>
<summary>4. Explain the security benefit of using pre-signed URLs instead of passing cloud credentials to the client.</summary>

Pre-signed URLs encode a specific operation (GET or PUT), a specific object key, an expiration time, and a cryptographic signature -- all in the URL itself. The client needs no AWS credentials, no SDK, and no IAM role. The URL is scoped to exactly one operation on one object and becomes invalid after expiration. If the URL leaks, the damage is limited to one object for a short time window. Passing cloud credentials to the client would give them broad access to potentially many buckets and operations, with no automatic expiration. Pre-signed URLs follow the principle of least privilege by design.
</details>

<details>
<summary>5. What is S3 Multi-Region Access Points and how does it simplify multi-region Kubernetes deployments?</summary>

S3 Multi-Region Access Points provide a single global endpoint that automatically routes requests to the closest S3 bucket based on the requester's network location. Instead of configuring each Kubernetes cluster with a region-specific bucket name, all clusters use the same Multi-Region Access Point ARN. Requests from a US-based cluster route to the US bucket, while requests from an EU cluster route to the EU bucket. This eliminates the need for region-specific ConfigMaps and simplifies application configuration. Combined with cross-region replication, it provides a globally consistent, low-latency storage layer.
</details>

<details>
<summary>6. Why should you require HTTPS via bucket policy rather than relying on application configuration?</summary>

Requiring HTTPS at the bucket policy level is a defense-in-depth measure. Even if an application misconfiguration, a debugging tool, or a third-party integration makes an HTTP (non-TLS) request, the bucket policy will deny it. Relying solely on application configuration means any new pod or tool that accesses the bucket without TLS will silently transfer data unencrypted. The bucket policy is a guardrail that catches configuration errors regardless of which client connects. It also satisfies compliance requirements (PCI-DSS, HIPAA) that mandate encryption in transit.
</details>

---

## Hands-On Exercise: Object Storage Access Patterns with MinIO

This exercise uses MinIO (S3-compatible) running locally in a kind cluster to practice all three access patterns.

### Setup

```bash
# Create kind cluster
kind create cluster --name storage-lab

# Install MinIO
helm repo add minio https://charts.min.io/
helm install minio minio/minio \
  --namespace storage --create-namespace \
  --set replicas=1 \
  --set persistence.enabled=false \
  --set rootUser=minioadmin \
  --set rootPassword=minioadmin123 \
  --set resources.requests.memory=256Mi \
  --set mode=standalone

k wait --for=condition=ready pod -l app=minio -n storage --timeout=120s
```

### Task 1: SDK-Style Access from a Pod

Create a pod that uses the AWS CLI (configured for MinIO) to create a bucket and upload files.

<details>
<summary>Solution</summary>

```bash
# Create a Secret with MinIO credentials
k create secret generic minio-creds -n storage \
  --from-literal=AWS_ACCESS_KEY_ID=minioadmin \
  --from-literal=AWS_SECRET_ACCESS_KEY=minioadmin123

# Run a pod with AWS CLI
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: s3-client
  namespace: storage
spec:
  restartPolicy: Never
  containers:
    - name: aws-cli
      image: amazon/aws-cli:2.22.0
      command:
        - /bin/sh
        - -c
        - |
          # Configure endpoint
          export AWS_DEFAULT_REGION=us-east-1

          # Create bucket
          aws --endpoint-url http://minio:9000 s3 mb s3://test-bucket

          # Upload files
          echo "Hello from Kubernetes" > /tmp/hello.txt
          aws --endpoint-url http://minio:9000 s3 cp /tmp/hello.txt s3://test-bucket/hello.txt

          # Create multiple files
          for i in $(seq 1 10); do
            echo "File content $i - $(date)" > /tmp/file-$i.txt
            aws --endpoint-url http://minio:9000 s3 cp /tmp/file-$i.txt s3://test-bucket/data/file-$i.txt
          done

          # List bucket contents
          aws --endpoint-url http://minio:9000 s3 ls s3://test-bucket/ --recursive

          echo "Upload complete!"
          sleep 300
      envFrom:
        - secretRef:
            name: minio-creds
EOF

k wait --for=condition=ready pod/s3-client -n storage --timeout=60s
k logs s3-client -n storage
```
</details>

### Task 2: Generate Pre-Signed URLs

Create a pod that generates pre-signed download URLs for the uploaded files.

<details>
<summary>Solution</summary>

```bash
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: url-generator
  namespace: storage
spec:
  restartPolicy: Never
  containers:
    - name: python
      image: python:3.12-slim
      command:
        - /bin/sh
        - -c
        - |
          pip install boto3 -q

          python3 << 'PYEOF'
          import boto3

          s3 = boto3.client(
              's3',
              endpoint_url='http://minio:9000',
              aws_access_key_id='minioadmin',
              aws_secret_access_key='minioadmin123',
              region_name='us-east-1'
          )

          # Generate pre-signed download URL
          url = s3.generate_presigned_url(
              'get_object',
              Params={'Bucket': 'test-bucket', 'Key': 'hello.txt'},
              ExpiresIn=3600
          )
          print(f"Download URL (1h expiry): {url}")

          # Generate pre-signed upload URL
          upload_url = s3.generate_presigned_url(
              'put_object',
              Params={
                  'Bucket': 'test-bucket',
                  'Key': 'uploads/new-file.txt',
                  'ContentType': 'text/plain'
              },
              ExpiresIn=900
          )
          print(f"Upload URL (15m expiry): {upload_url}")

          # List all objects and generate URLs
          response = s3.list_objects_v2(Bucket='test-bucket', Prefix='data/')
          for obj in response.get('Contents', []):
              url = s3.generate_presigned_url(
                  'get_object',
                  Params={'Bucket': 'test-bucket', 'Key': obj['Key']},
                  ExpiresIn=3600
              )
              print(f"{obj['Key']}: {url[:80]}...")
          PYEOF
      envFrom:
        - secretRef:
            name: minio-creds
EOF

k wait --for=condition=ready pod/url-generator -n storage --timeout=120s
k logs url-generator -n storage
```
</details>

### Task 3: Implement Lifecycle-Like Cleanup

Create a CronJob that cleans up files older than a specified age (simulating lifecycle policies).

<details>
<summary>Solution</summary>

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: storage-cleanup
  namespace: storage
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: cleanup
              image: python:3.12-slim
              command:
                - /bin/sh
                - -c
                - |
                  pip install boto3 -q
                  python3 << 'PYEOF'
                  import boto3
                  from datetime import datetime, timezone, timedelta

                  s3 = boto3.client(
                      's3',
                      endpoint_url='http://minio:9000',
                      aws_access_key_id='minioadmin',
                      aws_secret_access_key='minioadmin123',
                      region_name='us-east-1'
                  )

                  MAX_AGE = timedelta(minutes=10)
                  now = datetime.now(timezone.utc)

                  response = s3.list_objects_v2(Bucket='test-bucket', Prefix='data/')
                  deleted = 0
                  for obj in response.get('Contents', []):
                      age = now - obj['LastModified']
                      if age > MAX_AGE:
                          s3.delete_object(Bucket='test-bucket', Key=obj['Key'])
                          print(f"Deleted: {obj['Key']} (age: {age})")
                          deleted += 1

                  print(f"Cleanup complete: {deleted} objects deleted")
                  PYEOF
```

```bash
k apply -f /tmp/cleanup-cronjob.yaml
```
</details>

### Task 4: Verify Bucket Security

Write a script that checks bucket security settings.

<details>
<summary>Solution</summary>

```bash
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: security-audit
  namespace: storage
spec:
  restartPolicy: Never
  containers:
    - name: auditor
      image: python:3.12-slim
      command:
        - /bin/sh
        - -c
        - |
          pip install boto3 -q
          python3 << 'PYEOF'
          import boto3

          s3 = boto3.client(
              's3',
              endpoint_url='http://minio:9000',
              aws_access_key_id='minioadmin',
              aws_secret_access_key='minioadmin123',
              region_name='us-east-1'
          )

          bucket = 'test-bucket'
          print(f"=== Security Audit: {bucket} ===")

          # Check versioning
          try:
              v = s3.get_bucket_versioning(Bucket=bucket)
              status = v.get('Status', 'Disabled')
              print(f"Versioning: {status}")
              if status != 'Enabled':
                  print("  WARNING: Versioning is not enabled!")
          except Exception as e:
              print(f"  Versioning check failed: {e}")

          # Check encryption
          try:
              enc = s3.get_bucket_encryption(Bucket=bucket)
              print(f"Encryption: Enabled")
          except Exception:
              print("Encryption: Not configured")
              print("  WARNING: Default encryption not set!")

          # Check bucket policy
          try:
              policy = s3.get_bucket_policy(Bucket=bucket)
              print(f"Bucket policy: Present")
          except Exception:
              print("Bucket policy: None")
              print("  INFO: No bucket policy (relying on IAM only)")

          # List objects to verify access
          objects = s3.list_objects_v2(Bucket=bucket)
          count = objects.get('KeyCount', 0)
          print(f"Object count: {count}")

          print("=== Audit Complete ===")
          PYEOF
EOF

k wait --for=condition=ready pod/security-audit -n storage --timeout=120s
k logs security-audit -n storage
```
</details>

### Success Criteria

- [ ] S3 client pod creates bucket and uploads 11 files
- [ ] Pre-signed URL generator produces valid download and upload URLs
- [ ] CronJob runs and reports cleanup activity
- [ ] Security audit pod reports versioning and encryption status

### Cleanup

```bash
kind delete cluster --name storage-lab
```

---

**Next Module**: [Module 9.5: Advanced Caching Services (ElastiCache / Memorystore)](module-9.5-caching/) -- Learn Redis and Memcached architectures for Kubernetes workloads, caching strategies, cache stampede prevention, and using Envoy as a sidecar cache.
