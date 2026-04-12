---
title: "Private MLOps Platform"
description: "Architecting and operating a bare-metal MLOps stack for model tracking, feature stores, and inference."
sidebar:
  order: 94
---

# Private MLOps Platform

Operating machine learning infrastructure on bare metal requires replacing managed cloud services (like AWS SageMaker or Google Vertex AI) with self-hosted, scalable equivalents. A production-grade MLOps platform on Kubernetes is not a single monolithic application; it is a loosely coupled ecosystem of stateful data stores, stateless API servers, and workflow orchestrators.

This module details the architecture, deployment, and operation of a private MLOps stack, focusing on feature stores, experiment tracking, data versioning, and model serving.

## Learning Outcomes

*   Architect a modular MLOps stack on Kubernetes utilizing self-hosted components.
*   Deploy and configure MLflow with a highly available PostgreSQL backend and MinIO artifact store.
*   Implement Feast as a bare-metal feature store utilizing Redis for online serving and PostgreSQL/Parquet for offline batching.
*   Configure model serving pipelines using KServe for A/B testing and canary rollouts.
*   Diagnose common stateful ML component failures, including artifact sync errors and inference memory exhaustion.

## Architecting the Private MLOps Stack

A functional MLOps platform handles four distinct lifecycles: Data, Experimentation, Orchestration, and Serving. On bare metal, you must provision the underlying storage (block, file, and object) and routing infrastructure that managed services typically abstract away.

### Cloud to Bare Metal Mapping

| Managed Cloud Service (AWS/GCP) | Bare Metal Kubernetes Equivalent | Primary Storage Backend |
| :--- | :--- | :--- |
| S3 / GCS | MinIO / Ceph Object Gateway | Physical NVMe / HDD |
| SageMaker Experiments / Vertex ML Metadata | MLflow Tracking Server | PostgreSQL + MinIO |
| Vertex Feature Store / SageMaker Feature Store | Feast | Redis (Online) + Postgres (Offline)|
| SageMaker Pipelines / Vertex Pipelines | Kubeflow Pipelines (KFP) / Argo | MinIO (Artifacts) + MySQL |
| SageMaker Endpoints / Vertex Prediction | KServe / Seldon Core | Knative / Istio |

### System Architecture

The following diagram illustrates how these components interact within a Kubernetes cluster.

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

## Data Versioning on Bare Metal

Machine learning models are functions of the code and the data they are trained on. Versioning data on bare metal requires an object storage backend (typically MinIO or Ceph) and a tracking layer.

### DVC (Data Version Control)
DVC operates directly on top of Git. It tracks large datasets by storing metadata pointers (`.dvc` files) in Git while pushing the actual payload to MinIO.
*   **Pros:** Requires zero additional infrastructure beyond your Git server and an S3-compatible endpoint.
*   **Cons:** Client-side heavy. Engineers must configure their local environment with S3 credentials.

### LakeFS
LakeFS provides Git-like operations (branch, commit, merge, revert) directly over object storage via an API proxy.
*   **Pros:** Server-side implementation. Zero-copy branching (branching a 10TB dataset takes milliseconds and consumes no extra storage).
*   **Cons:** Requires running a dedicated LakeFS PostgreSQL database and API server on the cluster. Applications must use the LakeFS S3 gateway endpoint instead of the direct MinIO endpoint.

:::tip
For smaller teams, DVC is sufficient. Once you exceed 50TB of training data or require strict isolation between concurrent training runs accessing the same dataset, deploy LakeFS.
:::

## Feature Stores: Feast on Kubernetes

A feature store ensures that the data features used for training (historical data) exactly match the features used for serving (real-time data), preventing training-serving skew. Feast is the standard open-source choice.

Feast relies on two storage tiers:
1.  **Offline Store:** Used for batch training. On bare metal, this is typically Apache Parquet files stored in MinIO or tables in a centralized PostgreSQL/Greenplum instance.
2.  **Online Store:** Used for low-latency inference lookups. On bare metal, this is exclusively Redis.

### Feast Configuration (`feature_store.yaml`)

To run Feast on bare metal, you must abandon cloud-native integrations (like BigQuery or DynamoDB) and point the registry and stores to internal cluster endpoints.

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

When deploying Feast materialization jobs (moving data from offline to online stores), use Kubernetes CronJobs that execute `feast materialize` rather than relying on external workflow orchestrators.

## Experiment Tracking: MLflow Architecture

MLflow requires a carefully architected deployment to prevent data loss and ensure high availability. By default, running `mlflow server` writes data to the local container filesystem, which is immediately lost upon pod termination.

A production MLflow deployment requires three distinct components:
1.  **Tracking Server:** A stateless Python/Gunicorn API server running as a Kubernetes Deployment.
2.  **Backend Store:** An external SQL database storing parameters, metrics, and run metadata.
3.  **Artifact Store:** An S3-compatible bucket storing output models, plots, and large files.

### Critical Environment Variables

When running MLflow on Kubernetes with MinIO, the tracking server and the client pods (the workloads logging the data) must both be configured to communicate with the S3 API.

You must inject the following environment variables into both the MLflow server pod and any training pods:

```yaml
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

:::caution
If `MLFLOW_S3_ENDPOINT_URL` is omitted, the underlying `boto3` library defaults to public AWS S3 endpoints. Network policies will block this, resulting in silent timeout failures during artifact upload.
:::

## Model Serving: KServe

KServe (formerly KFServing) provides a Kubernetes Custom Resource Definition (CRD) for serving ML models. It handles autoscaling, networking, health checking, and server configuration across multiple frameworks (TensorFlow, PyTorch, Scikit-Learn, XGBoost).

KServe requires Knative Serving, which in turn requires a networking layer like Istio.

### A/B Testing and Canary Rollouts

KServe supports native traffic splitting using Knative's routing capabilities. You can deploy a new model version as a canary and route a specific percentage of traffic to it.

```yaml
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

To route traffic securely from the edge, map your Istio VirtualService to the Knative local gateway, ensuring the `Host` header matches the KServe InferenceService URL.

## Hands-on Lab

In this lab, we will deploy a production-ready MLflow stack backed by PostgreSQL and MinIO, and log a test model to verify the configuration.

### Prerequisites
*   A running Kubernetes cluster (`kind` or `k3s`).
*   `kubectl` and `helm` installed locally.
*   A default StorageClass configured.

### Step 1: Deploy MinIO (Artifact Store)

We use the Bitnami MinIO chart for a quick, single-node object store.

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

### Step 2: Deploy PostgreSQL (Backend Store)

Deploy PostgreSQL to store MLflow run metadata.

```bash
helm install mlflow-db bitnami/postgresql \
  --namespace mlops \
  --set global.postgresql.auth.postgresPassword=postgres \
  --set global.postgresql.auth.database=mlflow
```

### Step 3: Deploy the MLflow Tracking Server

Create a file named `mlflow-deployment.yaml`. This manifest builds the stateless tracking server, connects it to the DB, and configures the S3 endpoint.

```yaml
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
        image: bitnami/mlflow:2.11.0
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

### Step 4: Verify Logging

Launch a temporary Python pod to act as a training job. This pod needs the `boto3` library to communicate with MinIO.

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

**Expected Output:**
```text
Run logged successfully!
```

### Troubleshooting the Lab

*   **Error: `psycopg2.OperationalError: could not translate host name`**
    *   *Cause:* The `backend-store-uri` string in the MLflow deployment contains a typo or PostgreSQL has not finished initializing. Verify the Service name of your PostgreSQL deployment.
*   **Error: `botocore.exceptions.EndpointConnectionError: Could not connect to the endpoint URL`**
    *   *Cause:* `MLFLOW_S3_ENDPOINT_URL` is missing or the MinIO service name is incorrect. Ensure the client pod (the `mlflow-test` pod) has the environment variable set explicitly; it does not inherit it from the server.

## Practitioner Gotchas

### 1. The MinIO Signature Version V4 Mismatch
Older machine learning libraries or older versions of the `boto3` AWS SDK default to S3 Signature Version 2. Modern MinIO deployments strictly require Signature Version 4. If training jobs fail to upload artifacts with an `InvalidSignature` error, you must explicitly set the environment variable `S3_SIGNATURE_VERSION=s3v4` or configure the MLflow client to enforce V4 signatures.

### 2. Feast Redis OOM Kills
During batch materialization (moving data from PostgreSQL to Redis), Feast can ingest data faster than Redis can handle it, leading to Redis consuming all node memory and being OOM (Out Of Memory) killed by the kubelet. Always set a hard `memory.limit` in the Redis StatefulSet and configure Redis eviction policies (`maxmemory-policy allkeys-lru`) to prevent node-level degradation.

### 3. KServe Cold Start Latencies
KServe utilizes Knative, which scales pods to zero when no traffic is detected. For large language models or deep neural networks, pulling a 5GB model from MinIO and loading it into GPU memory can take several minutes, causing HTTP timeouts for the first request. In production, disable scale-to-zero for heavy models by adding the annotation `serving.knative.dev/minScale: "1"` to the InferenceService.

### 4. Database Connection Pool Exhaustion in MLflow
During distributed hyperparameter tuning, hundreds of worker pods may attempt to log metrics simultaneously. MLflow uses SQLAlchemy to connect to the backend store. Without a connection pooler, the PostgreSQL instance will exhaust its `max_connections` limit. Deploy PgBouncer in front of the PostgreSQL instance and route MLflow's DB URI through PgBouncer.

## Quiz

**1. Your data scientists report that their training jobs successfully log parameters (like learning rate) to the MLflow UI, but fail with a connection timeout when attempting to save the final model weights. What is the most likely architectural misconfiguration?**
A) The MLflow tracking server does not have write access to the PostgreSQL database.
B) The training pod lacks the `MLFLOW_S3_ENDPOINT_URL` environment variable, defaulting to public AWS endpoints.
C) The MLflow tracking server pod lacks the `AWS_ACCESS_KEY_ID` environment variable.
D) The Kubernetes cluster default StorageClass is exhausted.
*Correct Answer: B. The client pod making the API call requires the S3 endpoint URL to push the artifact directly to MinIO; parameters are sent via HTTP to the tracking server, which is why they succeed.*

**2. You are tasked with migrating an offline feature store from Google Vertex AI to an on-premises Kubernetes environment. Which storage backend combination correctly implements Feast on bare metal?**
A) BigQuery for offline storage, DynamoDB for online serving.
B) MinIO (S3) for offline storage, MySQL for online serving.
C) PostgreSQL or MinIO/Parquet for offline storage, Redis for online serving.
D) DVC for offline storage, LakeFS for online serving.
*Correct Answer: C. Feast on bare metal typically utilizes PostgreSQL or object storage (Parquet) for batch offline features and Redis for low-latency online serving.*

**3. You deploy a 4GB deep learning model via KServe. The service works during the day, but the first request sent at 3:00 AM times out with an HTTP 504 Gateway Timeout. Subsequent requests succeed. What is the standard practitioner fix for this?**
A) Increase the Istio Gateway timeout duration to 15 minutes.
B) Set the annotation `serving.knative.dev/minScale: "1"` on the InferenceService to prevent scale-to-zero.
C) Switch the underlying object storage from MinIO to Ceph.
D) Add a Redis cache sidecar to the KServe pod to keep the model in memory.
*Correct Answer: B. Knative scales to zero by default. Loading large models incurs massive cold-start penalties, requiring a minimum scale of 1 to ensure instant responses.*

**4. When comparing DVC and LakeFS for managing a 100TB image dataset on an on-premises MinIO cluster, why might a platform team choose LakeFS?**
A) LakeFS requires no additional infrastructure or databases on the cluster.
B) LakeFS allows zero-copy branching via an API gateway, preventing duplication of the 100TB dataset across different experimental branches.
C) LakeFS uses Git hooks to store the actual images directly inside the Git repository.
D) DVC cannot communicate with bare-metal MinIO instances.
*Correct Answer: B. LakeFS provides server-side, zero-copy branching, which is highly efficient for massive datasets, whereas DVC is client-side and tracks files via Git.*

**5. You need to perform an A/B test routing exactly 10% of real-time inference traffic to a new model version (v2) while the rest goes to v1. How is this natively achieved in a KServe deployment?**
A) Deploying two separate InferenceServices and using a custom NGINX ingress controller script to split traffic based on headers.
B) Using the `canaryTrafficPercent: 10` spec in the InferenceService resource.
C) Configuring MLflow to intercept requests and round-robin the traffic.
D) Scaling the v2 deployment to 1 replica and the v1 deployment to 9 replicas manually.
*Correct Answer: B. KServe (via Knative) natively supports traffic splitting through the `canaryTrafficPercent` field in the InferenceService specification.*

## Further Reading

*   [MLflow Tracking on Kubernetes](https://mlflow.org/docs/latest/tracking.html#tracking-server)
*   [Feast Architecture and Concepts](https://docs.feast.dev/getting-started/architecture-and-components)
*   [KServe InferenceService Architecture](https://kserve.github.io/website/latest/modelserving/v1beta1/inferenceservice/)
*   [LakeFS Object Storage Integration](https://docs.lakefs.io/understand/architecture.html)