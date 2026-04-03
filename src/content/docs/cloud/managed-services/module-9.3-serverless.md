---
title: "Module 9.3: Serverless Interoperability (Lambda / Cloud Functions / Knative)"
slug: cloud/managed-services/module-9.3-serverless
sidebar:
  order: 4
---
**Complexity**: [COMPLEX] | **Time to Complete**: 2h | **Prerequisites**: Module 9.2 (Message Brokers), Kubernetes Services and Ingress basics

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design hybrid architectures that combine Kubernetes workloads with serverless functions (Lambda, Cloud Functions, Azure Functions)**
- **Implement Knative Serving on Kubernetes for serverless-style scale-to-zero with portable container workloads**
- **Configure event bridges between Kubernetes and cloud-native serverless triggers (EventBridge, Eventarc, Event Grid)**
- **Evaluate serverless vs container trade-offs for latency-sensitive, batch, and event-driven workload patterns**

---

## Why This Module Matters

In 2023, a healthcare startup ran their entire platform on EKS -- 42 microservices, 180 pods, three node groups. Their monthly Kubernetes bill was $18,000. During a cost optimization sprint, an engineer noticed that 11 of those microservices handled fewer than 100 requests per day. One service -- the PDF report generator -- was called exactly 23 times per day but required 2 pods (for HA) running 24/7. Another service processed insurance eligibility checks at 3 AM, running idle for 23 hours daily.

They moved those 11 services to AWS Lambda. The combined monthly cost dropped from $4,200 to $38. Not a typo -- thirty-eight dollars. The remaining 31 services stayed on EKS, where their steady-state traffic justified always-on compute. The lesson was not "serverless is better" or "Kubernetes is better." It was that the best architecture uses both, placing each workload where it makes economic and operational sense.

This module teaches you how to think about the serverless-Kubernetes boundary. You will learn when to use Lambda, Cloud Functions, or Azure Functions alongside your cluster, how to trigger serverless functions from Kubernetes events, how API Gateways route between both worlds, how Knative brings serverless semantics into Kubernetes itself, and how Fargate and Autopilot blur the line between containers and functions.

---

## When Serverless vs When Kubernetes

This is not a religious debate. It is a cost and operational decision matrix.

### Decision Framework

| Factor | Favor Serverless | Favor Kubernetes |
|--------|-----------------|-----------------|
| **Traffic pattern** | Spiky, long idle periods | Steady, predictable load |
| **Request volume** | < 1M requests/month | > 10M requests/month |
| **Execution duration** | < 15 minutes | Long-running processes |
| **State** | Stateless | Stateful, persistent connections |
| **Cold start tolerance** | Acceptable (100-500ms) | Unacceptable (real-time APIs) |
| **Dependencies** | Few, small packages | Complex runtimes, GPU, large models |
| **Team expertise** | Small team, want less ops | Platform team maintaining K8s already |
| **Cost at scale** | Expensive per-invocation | Cheaper with reserved/spot capacity |

### The Cost Crossover Point

```
Cost ($)
  |
  |   Serverless
  |   /
  |  /
  | /          Kubernetes (on-demand)
  |/          /
  +----------/---------------------> Requests/month
  |         /
  |        / Kubernetes (spot/reserved)
  |       /
  |      /
  |     /

  ~2M requests/month: serverless and K8s cost roughly the same
  Below: serverless wins
  Above: K8s wins (especially with spot instances)
```

The exact crossover depends on execution time, memory, and provider pricing. But the general shape is always the same: serverless is cheaper at low volume, Kubernetes is cheaper at scale.

---

## Triggering Cloud Functions from Kubernetes

The most common pattern is using Kubernetes workloads as producers and cloud functions as async processors.

### Pattern 1: Queue-Triggered Functions

```
  K8s Pod (producer)
       |
       | publish message
       v
  [ SQS Queue / Pub/Sub Topic ]
       |
       | event trigger
       v
  Lambda / Cloud Function
       |
       | write result
       v
  [ S3 / GCS / Database ]
```

```bash
# AWS: Create Lambda triggered by SQS
aws lambda create-function \
  --function-name process-report \
  --runtime python3.12 \
  --handler app.handler \
  --role arn:aws:iam::123456789:role/LambdaExecRole \
  --zip-file fileb://function.zip \
  --timeout 300 \
  --memory-size 1024

# Map SQS as event source
aws lambda create-event-source-mapping \
  --function-name process-report \
  --event-source-arn arn:aws:sqs:us-east-1:123456789:report-requests \
  --batch-size 5 \
  --maximum-batching-window-in-seconds 30
```

The Kubernetes side simply publishes messages to SQS:

```python
# From a K8s pod
import boto3
import json

sqs = boto3.client('sqs')

def request_report(user_id, report_type):
    sqs.send_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/123456789/report-requests',
        MessageBody=json.dumps({
            'user_id': user_id,
            'report_type': report_type,
            'requested_at': '2025-11-15T10:30:00Z'
        })
    )
```

### Pattern 2: HTTP-Triggered Functions via API Gateway

```
  Client
    |
    v
  [ API Gateway ]
    |         |
    | /api/*  | /reports/*
    v         v
  K8s ALB   Lambda Function URL
  Ingress
```

```bash
# AWS: API Gateway with routes split between K8s and Lambda
aws apigatewayv2 create-api \
  --name hybrid-api \
  --protocol-type HTTP

# Route /api/* to K8s ALB
aws apigatewayv2 create-integration \
  --api-id $API_ID \
  --integration-type HTTP_PROXY \
  --integration-uri arn:aws:elasticloadbalancing:us-east-1:123456789:listener/app/k8s-alb/abc123 \
  --integration-method ANY

# Route /reports/* to Lambda
aws apigatewayv2 create-integration \
  --api-id $API_ID \
  --integration-type AWS_PROXY \
  --integration-uri arn:aws:lambda:us-east-1:123456789:function:process-report \
  --payload-format-version "2.0"
```

### Pattern 3: Kubernetes Job Spawning Functions

Sometimes a K8s batch job needs to fan out work to many parallel functions:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: image-resize-orchestrator
spec:
  template:
    spec:
      restartPolicy: OnFailure
      serviceAccountName: lambda-invoker
      containers:
        - name: orchestrator
          image: mycompany/resize-orchestrator:1.0.0
          env:
            - name: LAMBDA_FUNCTION
              value: "image-resizer"
            - name: S3_BUCKET
              value: "user-uploads"
          command:
            - python
            - -c
            - |
              import boto3, json
              s3 = boto3.client('s3')
              lam = boto3.client('lambda')

              # List all images needing resize
              objects = s3.list_objects_v2(Bucket='user-uploads', Prefix='raw/')

              # Fan out to Lambda for parallel processing
              for obj in objects.get('Contents', []):
                  lam.invoke(
                      FunctionName='image-resizer',
                      InvocationType='Event',  # async
                      Payload=json.dumps({'key': obj['Key']})
                  )
                  print(f"Dispatched: {obj['Key']}")
```

---

## API Gateways: Bridging Both Worlds

Cloud API Gateways sit in front of both Kubernetes services and serverless functions, providing a unified entry point.

### Multi-Backend Architecture

```
                         Internet
                            |
                    +-------+-------+
                    | Cloud API GW  |
                    | (rate limit,  |
                    |  auth, WAF)   |
                    +---+---+---+---+
                        |   |   |
           +------------+   |   +------------+
           |                |                |
     /api/v1/*        /webhooks/*       /reports/*
           |                |                |
    +------+------+  +-----+------+  +------+------+
    | K8s Service |  | Lambda     |  | Cloud       |
    | (ALB/NLB)   |  | Functions  |  | Function    |
    +-------------+  +------------+  +-------------+
```

### GCP: Cloud Endpoints with GKE and Cloud Functions

```yaml
# GCP Cloud Endpoints OpenAPI spec
swagger: "2.0"
info:
  title: "Hybrid API"
  version: "1.0.0"
host: "api.example.com"
basePath: "/"
schemes:
  - "https"
paths:
  /api/v1/{resource}:
    get:
      x-google-backend:
        address: https://gke-ingress.example.com
        protocol: h2
      parameters:
        - name: resource
          in: path
          required: true
          type: string
  /reports/{id}:
    get:
      x-google-backend:
        address: https://us-central1-myproject.cloudfunctions.net/report-generator
      parameters:
        - name: id
          in: path
          required: true
          type: string
```

---

## Knative: Serverless on Kubernetes

Knative brings serverless semantics directly into your cluster. Instead of deploying to Lambda or Cloud Functions, you deploy to Knative, which manages scaling (including to zero), revisions, and traffic splitting -- all using standard Kubernetes resources.

### Knative Architecture

```
                    +-------------------+
                    | Knative Serving   |
                    |                   |
  Request -------> | Activator         |
                    |   |               |
                    |   v               |
                    | Queue-Proxy       |
                    |   |               |
                    |   v               |
                    | Your Container    |
                    |                   |
                    | Autoscaler (KPA)  |
                    | (scale 0 -> N)    |
                    +-------------------+
```

### Installing Knative

```bash
# Install Knative Serving
k apply -f https://github.com/knative/serving/releases/download/knative-v1.16.0/serving-crds.yaml
k apply -f https://github.com/knative/serving/releases/download/knative-v1.16.0/serving-core.yaml

# Install networking layer (Kourier is lightweight)
k apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.16.0/kourier.yaml

# Configure Knative to use Kourier
k patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'

# Install Knative Eventing
k apply -f https://github.com/knative/eventing/releases/download/knative-v1.16.0/eventing-crds.yaml
k apply -f https://github.com/knative/eventing/releases/download/knative-v1.16.0/eventing-core.yaml
```

### Knative Service (Serving)

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: report-generator
  namespace: production
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/min-scale: "0"
        autoscaling.knative.dev/max-scale: "20"
        autoscaling.knative.dev/target: "10"
        autoscaling.knative.dev/scale-down-delay: "30s"
    spec:
      containerConcurrency: 10
      timeoutSeconds: 300
      containers:
        - image: mycompany/report-generator:2.0.0
          ports:
            - containerPort: 8080
          env:
            - name: S3_BUCKET
              value: reports-output
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: "2"
              memory: 2Gi
```

Key annotations explained:
- `min-scale: "0"` -- Scale to zero when idle (true serverless)
- `max-scale: "20"` -- Never exceed 20 pods
- `target: "10"` -- Each pod handles 10 concurrent requests before scaling out
- `scale-down-delay: "30s"` -- Wait 30 seconds of idle before scaling down

### Knative Eventing: CloudEvents Pipeline

Knative Eventing connects event sources to services using CloudEvents, a CNCF-standard event format.

```yaml
# Source: Receive events from a message broker
apiVersion: sources.knative.dev/v1
kind: ApiServerSource
metadata:
  name: pod-events
  namespace: production
spec:
  serviceAccountName: event-watcher
  mode: Resource
  resources:
    - apiVersion: v1
      kind: Pod
  sink:
    ref:
      apiVersion: serving.knative.dev/v1
      kind: Service
      name: pod-event-processor
---
# Broker: Central event routing
apiVersion: eventing.knative.dev/v1
kind: Broker
metadata:
  name: default
  namespace: production
---
# Trigger: Filter and route events
apiVersion: eventing.knative.dev/v1
kind: Trigger
metadata:
  name: report-trigger
  namespace: production
spec:
  broker: default
  filter:
    attributes:
      type: com.example.report.requested
  subscriber:
    ref:
      apiVersion: serving.knative.dev/v1
      kind: Service
      name: report-generator
```

### Traffic Splitting for Canary Deployments

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: report-generator
  namespace: production
spec:
  template:
    metadata:
      name: report-generator-v2
    spec:
      containers:
        - image: mycompany/report-generator:3.0.0
  traffic:
    - revisionName: report-generator-v1
      percent: 90
    - revisionName: report-generator-v2
      percent: 10
```

---

## Fargate vs Autopilot: Serverless Containers

Fargate (AWS) and Autopilot (GCP) remove node management entirely. You define pods, and the cloud runs them without you provisioning or managing nodes.

### Comparison

| Feature | EKS Fargate | GKE Autopilot | AKS Virtual Nodes |
|---------|-------------|---------------|-------------------|
| Billing unit | Per pod (vCPU + memory per second) | Per pod (vCPU + memory per second) | Per container group (ACI pricing) |
| DaemonSets | Not supported | Supported (since 2024) | Not supported |
| GPUs | Supported (limited) | Supported | Not supported |
| Persistent storage | EBS CSI (since 2024) | GCE PD | Azure Files |
| Max pods per node | 1 pod = 1 "node" | Managed by GKE | Burstable |
| Startup time | 30-60 seconds | Transparent | 15-30 seconds |
| Best for | Batch, low-traffic services | Entire cluster, hands-off | Burst capacity |

### EKS Fargate Profile

```bash
# Create Fargate profile for specific namespaces
aws eks create-fargate-profile \
  --cluster-name my-cluster \
  --fargate-profile-name serverless-workloads \
  --pod-execution-role-arn arn:aws:iam::123456789:role/EKSFargatePodRole \
  --subnets subnet-0a1b2c3d subnet-0e5f6a7b \
  --selectors '[
    {"namespace": "batch-jobs"},
    {"namespace": "reports", "labels": {"compute": "fargate"}}
  ]'
```

Any pod deployed to the `batch-jobs` namespace or the `reports` namespace with the label `compute: fargate` will run on Fargate automatically. No node groups needed.

```yaml
# This pod runs on Fargate (matches the profile above)
apiVersion: batch/v1
kind: Job
metadata:
  name: nightly-report
  namespace: batch-jobs
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: report
          image: mycompany/report-generator:2.0.0
          resources:
            requests:
              cpu: "1"
              memory: 2Gi
            limits:
              cpu: "2"
              memory: 4Gi
```

### Cold Start Mitigation

Cold starts are the primary drawback of serverless. Here are practical mitigations:

| Strategy | How | Latency Reduction |
|----------|-----|-------------------|
| **Provisioned concurrency** (Lambda) | Pre-warm N instances | Eliminates cold start for N concurrent requests |
| **min-scale: 1** (Knative) | Keep one pod always running | First request is always warm |
| **Warm-up endpoints** | Health check that loads dependencies | Reduces initialization overhead |
| **Smaller images** | Alpine/distroless base images | Faster pull and startup |
| **SnapStart** (Lambda Java) | Snapshot after init, restore on invocation | 90% reduction for JVM cold starts |
| **GraalVM native images** | Ahead-of-time compilation | 10-50ms startup for Java |

```bash
# AWS: Provisioned concurrency for Lambda
aws lambda put-provisioned-concurrency-config \
  --function-name process-report \
  --qualifier prod \
  --provisioned-concurrent-executions 5
```

---

## Hybrid Architecture Example

A real-world architecture combining Kubernetes and serverless:

```
                          Internet
                             |
                     [ API Gateway + WAF ]
                        |            |
                   /api/*        /webhooks/*
                        |            |
              [ ALB Ingress ]   [ Lambda ]
                   |                 |
          +--------+--------+        |
          |        |        |        |
       +--+--+ +--+--+ +--+--+  Process
       | API | | API | | API |   webhook
       | Pod | | Pod | | Pod |   payload
       +-----+ +-----+ +-----+    |
          |                        |
     [ RDS PostgreSQL ]      [ SQS Queue ]
                                   |
                             [ Lambda ]
                              Generate
                               report
                                   |
                              [ S3 Bucket ]
                                   |
                             [ SNS Topic ]
                                   |
                          Email notification
```

- **API pods on EKS**: Steady traffic, complex logic, persistent DB connections
- **Webhook Lambda**: Spiky, unpredictable, stateless
- **Report Lambda**: Infrequent, CPU-intensive for short bursts, output to S3

---

## Did You Know?

1. **AWS Lambda processes over 10 trillion invocations per month** as of 2025. To handle this, Lambda's internal architecture uses a purpose-built microVM technology called Firecracker, which can spin up a new VM in under 125 milliseconds.

2. **Knative was originally created by Google, Pivotal, and IBM in 2018** to bring serverless to Kubernetes. It is now a CNCF Incubating project and forms the basis of Google Cloud Run, which is essentially managed Knative under the hood.

3. **GKE Autopilot charges you for pod resource requests, not limits**, which means over-requesting CPU or memory directly increases your bill. This pricing model forces teams to be precise about resource requests -- a good habit that most teams on standard Kubernetes ignore.

4. **The longest-running Lambda function in 2024 ran for the full 15-minute timeout** processing satellite imagery for a climate research project. Before the 2018 limit increase from 5 to 15 minutes, the team had to split their pipeline into six chained functions -- a painful reminder that serverless time limits shape architecture.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Moving high-traffic services to Lambda for "simplicity" | Assuming serverless is always simpler | Calculate cost at your volume; K8s is often cheaper above 2M requests/month |
| Not accounting for cold start in P99 latency | Testing with warm functions only | Test cold starts explicitly; use provisioned concurrency for latency-sensitive paths |
| Running Knative on a cluster without enough baseline capacity | Knative's activator and autoscaler need resources | Dedicate 2-3 nodes to Knative system components |
| Using Fargate for DaemonSet-dependent workloads | Fargate does not support DaemonSets | Use node groups for workloads requiring log agents, monitoring sidecars via DaemonSets |
| Ignoring the 256 KB message size limit when triggering Lambda from SQS | Works in dev with small payloads | Store large payloads in S3; pass only the S3 key through the queue |
| Deploying Knative Services without resource limits | Knative autoscaler cannot make good decisions | Always set `containerConcurrency` and resource requests/limits |
| Not setting up dead-letter destinations for async Lambda invocations | Failures silently disappear | Configure DLQ (SQS) or on-failure destination for every async invocation |
| Using API Gateway as a pass-through without caching | Every request hits the backend | Enable API Gateway response caching for read-heavy endpoints |

---

## Quiz

<details>
<summary>1. At roughly what request volume does Kubernetes become more cost-effective than serverless functions?</summary>

The crossover point is typically around 2 million requests per month, though it varies by execution duration and memory allocation. Below this threshold, serverless pay-per-invocation pricing wins because you are not paying for idle time. Above it, Kubernetes on reserved or spot instances becomes cheaper because the per-request cost of always-on compute decreases as utilization increases. The crossover shifts higher if your functions have very short execution times (< 100ms) and lower if they run for seconds.
</details>

<details>
<summary>2. What is Knative's Activator component and why is it necessary for scale-to-zero?</summary>

The Activator is a Knative component that receives requests when a Service has been scaled to zero pods. When no pods are running and a request arrives, the Activator buffers the request, tells the Autoscaler to create a pod, waits for the pod to become ready, and then forwards the buffered request to the new pod. Without the Activator, requests to a scaled-to-zero Service would get connection refused errors. The Activator acts as a proxy that absorbs the cold-start delay, making the experience seamless for callers.
</details>

<details>
<summary>3. Why does EKS Fargate not support DaemonSets, and what is the workaround?</summary>

Fargate runs each pod in its own isolated microVM -- there is no shared node. DaemonSets run one pod per node, but in Fargate there are no "nodes" in the traditional sense. The workaround is to use sidecars instead. If you need a log collector (Fluent Bit) or monitoring agent (Datadog), add it as a sidecar container in the pod spec. AWS also provides native Fargate logging via the `fluentbit` log router that can be configured through pod annotations without a sidecar.
</details>

<details>
<summary>4. Explain the queue-triggered Lambda pattern and why it works well with Kubernetes producers.</summary>

In this pattern, Kubernetes pods publish messages to a managed queue (SQS, Pub/Sub), and a Lambda function is configured with the queue as an event source trigger. Lambda automatically polls the queue, batches messages, and invokes the function. This works well because it decouples the Kubernetes workload (which handles steady-state traffic) from burst processing. The K8s pods write at their natural rate, the queue buffers load, and Lambda scales independently to process messages. The Kubernetes side does not need to know or care that Lambda is doing the processing -- it just publishes messages.
</details>

<details>
<summary>5. What is the difference between GKE Autopilot and EKS Fargate in how they handle pod scheduling?</summary>

GKE Autopilot manages the entire cluster -- all pods run on Google-managed nodes, and you never see or configure node pools. It supports DaemonSets, GPUs, and behaves like a normal GKE cluster from the user's perspective. EKS Fargate is selective -- you create Fargate profiles that match specific namespaces and labels. Only matching pods run on Fargate; other pods still need managed node groups. Autopilot replaces cluster node management entirely, while Fargate adds serverless compute alongside existing node groups.
</details>

<details>
<summary>6. How does Knative traffic splitting differ from a standard Kubernetes canary deployment?</summary>

Knative traffic splitting is built into the Service resource as a first-class feature. You specify percentage weights for each revision (e.g., 90% to v1, 10% to v2), and Knative's networking layer routes traffic accordingly at the request level. Standard Kubernetes canary deployments typically use replica ratios (e.g., 9 pods of v1 and 1 pod of v2) which gives approximate but not precise traffic splitting. Knative's approach is more accurate and does not require adjusting replica counts. Additionally, Knative automatically creates new revisions on each update, maintaining a history for easy rollback.
</details>

---

## Hands-On Exercise: Knative Service with Scale-to-Zero

### Setup

```bash
# Create kind cluster with extra ports for Knative
cat > /tmp/kind-knative.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 31080
        hostPort: 8080
  - role: worker
  - role: worker
EOF

kind create cluster --name knative-lab --config /tmp/kind-knative.yaml

# Install Knative Serving
k apply -f https://github.com/knative/serving/releases/download/knative-v1.16.0/serving-crds.yaml
k apply -f https://github.com/knative/serving/releases/download/knative-v1.16.0/serving-core.yaml

# Install Kourier networking
k apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.16.0/kourier.yaml

k patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'

# Wait for Knative to be ready
k wait --for=condition=ready pod --all -n knative-serving --timeout=180s

# Configure DNS (use sslip.io for local testing)
k patch configmap/config-domain \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"127.0.0.1.sslip.io":""}}'
```

### Task 1: Deploy a Knative Service

Create a Knative Service that returns "Hello from Knative" and scales to zero.

<details>
<summary>Solution</summary>

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: hello
  namespace: default
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/min-scale: "0"
        autoscaling.knative.dev/max-scale: "5"
        autoscaling.knative.dev/window: "30s"
    spec:
      containerConcurrency: 5
      containers:
        - image: gcr.io/knative-samples/helloworld-go
          ports:
            - containerPort: 8080
          env:
            - name: TARGET
              value: "Knative"
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
```

```bash
k apply -f /tmp/knative-hello.yaml
# Wait for it to be ready
k wait ksvc hello --for=condition=Ready --timeout=60s
```
</details>

### Task 2: Test Scale-to-Zero Behavior

Verify the service scales to zero and then scales back up on request.

<details>
<summary>Solution</summary>

```bash
# Check current pods
k get pods -l serving.knative.dev/service=hello

# Wait 60 seconds for scale-to-zero
echo "Waiting for scale-to-zero..."
sleep 60
k get pods -l serving.knative.dev/service=hello
# Should show no pods (or Terminating)

# Get the Knative URL
KSVC_URL=$(k get ksvc hello -o jsonpath='{.status.url}')
echo "Service URL: $KSVC_URL"

# Send a request (triggers scale-from-zero)
KOURIER_IP=$(k get svc kourier -n kourier-system -o jsonpath='{.spec.clusterIP}')
k run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -H "Host: hello.default.127.0.0.1.sslip.io" http://$KOURIER_IP

# Check pods again -- should see one running
k get pods -l serving.knative.dev/service=hello
```
</details>

### Task 3: Deploy a Second Revision and Split Traffic

Update the service with a new environment variable and split traffic 80/20.

<details>
<summary>Solution</summary>

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: hello
  namespace: default
spec:
  template:
    metadata:
      name: hello-v2
      annotations:
        autoscaling.knative.dev/min-scale: "0"
        autoscaling.knative.dev/max-scale: "5"
    spec:
      containerConcurrency: 5
      containers:
        - image: gcr.io/knative-samples/helloworld-go
          ports:
            - containerPort: 8080
          env:
            - name: TARGET
              value: "Knative v2"
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
  traffic:
    - revisionName: hello-v2
      percent: 20
    - revisionName: hello-00001
      percent: 80
```

```bash
k apply -f /tmp/knative-v2.yaml

# Verify traffic split
k get ksvc hello -o yaml | grep -A 10 "traffic:"

# Send 20 requests and count responses
KOURIER_IP=$(k get svc kourier -n kourier-system -o jsonpath='{.spec.clusterIP}')
for i in $(seq 1 20); do
  k run curl-$i --rm -it --image=curlimages/curl --restart=Never -- \
    curl -s -H "Host: hello.default.127.0.0.1.sslip.io" http://$KOURIER_IP 2>/dev/null
done
```
</details>

### Task 4: Configure Knative Eventing with a PingSource

Set up a cron-based event source that triggers the Knative service every minute.

<details>
<summary>Solution</summary>

```bash
# Install Knative Eventing
k apply -f https://github.com/knative/eventing/releases/download/knative-v1.16.0/eventing-crds.yaml
k apply -f https://github.com/knative/eventing/releases/download/knative-v1.16.0/eventing-core.yaml
k wait --for=condition=ready pod --all -n knative-eventing --timeout=120s
```

```yaml
apiVersion: sources.knative.dev/v1
kind: PingSource
metadata:
  name: heartbeat
  namespace: default
spec:
  schedule: "*/1 * * * *"
  contentType: "application/json"
  data: '{"message": "heartbeat check"}'
  sink:
    ref:
      apiVersion: serving.knative.dev/v1
      kind: Service
      name: hello
```

```bash
k apply -f /tmp/pingsource.yaml

# Wait for the next minute tick, then check logs
sleep 90
k logs -l serving.knative.dev/service=hello --tail=10
```
</details>

### Success Criteria

- [ ] Knative Service deploys and responds to HTTP requests
- [ ] Service scales to zero after idle period
- [ ] Service scales back from zero when receiving a request
- [ ] Traffic splits between v1 (80%) and v2 (20%)
- [ ] PingSource triggers the service every minute

### Cleanup

```bash
kind delete cluster --name knative-lab
```

---

**Next Module**: [Module 9.4: Object Storage Patterns (S3 / GCS / Blob)](../module-9.4-object-storage/) -- Learn how to access cloud object storage from Kubernetes pods using CSI drivers, pre-signed URLs, and cross-region replication patterns.
