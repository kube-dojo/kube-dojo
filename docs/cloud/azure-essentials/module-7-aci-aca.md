# ACI & Azure Container Apps
**Complexity**: [COMPLEX] | **Time to Complete**: 3h | **Prerequisites**: Module 6 (ACR), Module 1 (Entra ID)

## Why This Module Matters

In early 2023, a media streaming company needed to process video transcoding jobs during live events. Their traffic was extremely spiky---zero jobs during off-hours, then 500+ concurrent transcoding tasks during a live broadcast. Their existing solution used a pool of 20 always-on VMs that cost $2,800/month. During events, the pool was overwhelmed and jobs queued for 15+ minutes. During off-hours, the VMs sat idle burning money. They migrated the transcoding workers to Azure Container Apps with KEDA scaling triggered by Azure Service Bus queue depth. During live events, Container Apps scaled from zero to 200 instances in under 90 seconds. After the event, it scaled back to zero. Their monthly compute bill dropped from $2,800 to $340---an 88% reduction---while simultaneously eliminating the 15-minute queue backlog entirely.

Containers have become the standard unit of deployment, but not every workload needs the complexity of Kubernetes. Azure offers two serverless container platforms that abstract away cluster management: **Azure Container Instances (ACI)**, a raw container execution engine for simple workloads, and **Azure Container Apps (ACA)**, a higher-level platform built on Kubernetes that handles scaling, traffic routing, and service-to-service communication automatically.

In this module, you will learn when to use ACI versus Container Apps, how container groups work in ACI, how Container Apps manages revisions and traffic splitting, how KEDA auto-scaling responds to event-driven triggers, and how Dapr simplifies microservice communication. By the end, you will build an event-driven worker on Container Apps that scales based on queue length.

---

## Azure Container Instances (ACI): Containers Without Infrastructure

ACI is the simplest way to run a container in Azure. There is no cluster to manage, no orchestrator to configure, no nodes to patch. You provide a container image, specify CPU and memory, and Azure runs it. Think of ACI as the "function" of the container world---instant, stateless, and pay-per-second.

### When to Use ACI

ACI is ideal for:
- **Batch jobs and tasks**: Data processing, report generation, ETL pipelines
- **CI/CD build agents**: Ephemeral agents that spin up for a build and disappear
- **Dev/test environments**: Quick deployment without cluster overhead
- **Sidecar scenarios**: Running a container alongside another (container groups)
- **Burstable workloads from AKS**: Virtual Kubelet integration for overflow

ACI is **not** ideal for long-running web services (use Container Apps), complex microservice architectures (use AKS), or workloads needing auto-scaling (use Container Apps or AKS).

```bash
# Run a simple container
az container create \
  --resource-group myRG \
  --name hello-world \
  --image mcr.microsoft.com/azuredocs/aci-helloworld \
  --cpu 1 \
  --memory 1.5 \
  --ports 80 \
  --dns-name-label hello-kubedojo \
  --location eastus2

# View the running container
az container show -g myRG -n hello-world \
  --query '{FQDN:ipAddress.fqdn, State:provisioningState, IP:ipAddress.ip}' -o table

# View logs
az container logs -g myRG -n hello-world

# Execute a command inside the container
az container exec -g myRG -n hello-world --exec-command "/bin/sh"

# Delete when done
az container delete -g myRG -n hello-world --yes
```

### Container Groups: The ACI Pod

A **container group** is ACI's equivalent of a Kubernetes Pod. It is a collection of containers that are scheduled on the same host, share the same network namespace (they can reach each other on `localhost`), and can share volumes.

```text
    ┌──────────────────────────────────────────────────┐
    │            Container Group (= K8s Pod)            │
    │                                                  │
    │  ┌──────────────┐  ┌──────────────────────────┐  │
    │  │ App Container│  │ Sidecar Container        │  │
    │  │              │  │                          │  │
    │  │ nginx:alpine │  │ fluentd:latest           │  │
    │  │ Port 80      │  │ Reads /var/log/nginx     │  │
    │  │              │  │ Ships to Log Analytics   │  │
    │  └──────────────┘  └──────────────────────────┘  │
    │                                                  │
    │  Shared: Network (localhost), Volumes, Lifecycle  │
    │  Public IP: 20.50.100.150                        │
    │  DNS: myapp.eastus2.azurecontainer.io            │
    └──────────────────────────────────────────────────┘
```

```yaml
# container-group.yaml
apiVersion: "2023-05-01"
name: web-with-sidecar
location: eastus2
properties:
  containers:
    - name: web
      properties:
        image: nginx:alpine
        ports:
          - port: 80
        resources:
          requests:
            cpu: 0.5
            memoryInGb: 0.5
        volumeMounts:
          - name: shared-logs
            mountPath: /var/log/nginx

    - name: log-shipper
      properties:
        image: fluent/fluentd:latest
        resources:
          requests:
            cpu: 0.25
            memoryInGb: 0.25
        volumeMounts:
          - name: shared-logs
            mountPath: /var/log/nginx
            readOnly: true

  osType: Linux
  ipAddress:
    type: Public
    ports:
      - protocol: TCP
        port: 80
  volumes:
    - name: shared-logs
      emptyDir: {}
```

```bash
# Deploy the container group
az container create -g myRG --file container-group.yaml

# View individual container logs within a group
az container logs -g myRG -n web-with-sidecar --container-name web
az container logs -g myRG -n web-with-sidecar --container-name log-shipper
```

### ACI Networking

ACI containers can be deployed with a **public IP** (internet-accessible) or into a **VNet subnet** (private, for internal workloads).

```bash
# Deploy ACI into a VNet (private, no public IP)
az container create \
  --resource-group myRG \
  --name private-worker \
  --image myregistry.azurecr.io/worker:latest \
  --cpu 2 \
  --memory 4 \
  --vnet hub-vnet \
  --subnet aci-subnet \
  --registry-login-server myregistry.azurecr.io \
  --registry-username "$SP_APP_ID" \
  --registry-password "$SP_PASSWORD"
```

### ACI Resource Limits and Pricing

| Resource | Linux | Windows |
| :--- | :--- | :--- |
| **Max CPU per group** | 4 cores | 4 cores |
| **Max Memory per group** | 16 GiB | 16 GiB |
| **Max containers per group** | 60 | 60 |
| **GPU support** | Yes (limited regions) | No |
| **Pricing (per vCPU/sec)** | ~$0.0000135 | ~$0.0000180 |
| **Pricing (per GB memory/sec)** | ~$0.0000015 | ~$0.0000020 |

A container running 1 vCPU and 2 GB for an hour costs approximately: (0.0000135 x 3600) + (0.0000015 x 2 x 3600) = $0.049 + $0.011 = **$0.06/hour** or about **$43/month** if running 24/7.

---

## Azure Container Apps (ACA): The Sweet Spot

Azure Container Apps is built on Kubernetes (specifically, a managed AKS cluster running KEDA, Envoy, and Dapr) but abstracts away all Kubernetes complexity. You define your container, scaling rules, and networking---Container Apps handles the rest.

### Architecture

```text
    ┌──────────────────────────────────────────────────────────────┐
    │            Azure Container Apps Environment                  │
    │            (Shared boundary for related apps)                │
    │                                                              │
    │  ┌─────────────────────────────────────────────────────┐     │
    │  │                    Envoy Proxy                      │     │
    │  │         (Ingress, Traffic Splitting)                │     │
    │  └──────────────────┬──────────────────┬───────────────┘     │
    │                     │                  │                     │
    │       80% traffic   │    20% traffic   │                     │
    │                     ▼                  ▼                     │
    │  ┌──────────────────────┐  ┌──────────────────────┐         │
    │  │  Container App:      │  │  Container App:      │         │
    │  │  web-api              │  │  web-api              │         │
    │  │  Revision: v2        │  │  Revision: v3        │         │
    │  │  (3 replicas)        │  │  (1 replica)         │         │
    │  └──────────────────────┘  └──────────────────────┘         │
    │                                                              │
    │  ┌──────────────────────┐  ┌──────────────────────┐         │
    │  │  Container App:      │  │  Container App:      │         │
    │  │  worker               │  │  queue-processor     │         │
    │  │  (KEDA: scale on     │  │  (KEDA: scale on     │         │
    │  │   HTTP concurrency)  │  │   queue depth)       │         │
    │  │  (0-20 replicas)     │  │  (0-50 replicas)     │         │
    │  └──────────────────────┘  └──────────────────────┘         │
    │                                                              │
    │  Shared: Log Analytics workspace, virtual network            │
    │  Built on: Managed Kubernetes + KEDA + Envoy + Dapr          │
    └──────────────────────────────────────────────────────────────┘
```

### Container Apps vs ACI vs AKS

| Feature | ACI | Container Apps | AKS |
| :--- | :--- | :--- | :--- |
| **Complexity** | Lowest | Medium | Highest |
| **Auto-scaling** | No | Yes (KEDA) | Yes (HPA, KEDA, Karpenter) |
| **Scale to zero** | N/A (stops = deletes) | Yes | No (minimum 1 node) |
| **Traffic splitting** | No | Yes (revision-based) | Yes (manual with Istio/etc) |
| **Service mesh** | No | Dapr (built-in) | Istio/Linkerd (you manage) |
| **Custom domains + TLS** | No (IP/FQDN only) | Yes (auto-cert) | Yes (you manage) |
| **Persistent volumes** | Azure Files | Azure Files | Full PV/PVC support |
| **Max CPU per container** | 4 cores | 4 cores (Consumption) | Unlimited (node size) |
| **Ideal for** | Batch jobs, simple tasks | Web APIs, workers, microservices | Complex platforms, full K8s control |
| **Monthly cost baseline** | Pay per second | Free tier (180K vCPU-sec) | ~$73 (1 node min) |

```bash
# Create a Container Apps Environment
az containerapp env create \
  --resource-group myRG \
  --name kubedojo-env \
  --location eastus2

# Deploy a Container App (web API)
az containerapp create \
  --resource-group myRG \
  --name web-api \
  --environment kubedojo-env \
  --image mcr.microsoft.com/k8se/quickstart:latest \
  --target-port 80 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 10 \
  --cpu 0.5 \
  --memory 1.0Gi

# Get the app URL
az containerapp show -g myRG -n web-api --query properties.configuration.ingress.fqdn -o tsv
```

### Revisions and Traffic Splitting

Every time you update a Container App's configuration or image, a new **revision** is created. You can control how traffic is split between revisions, enabling canary deployments and blue/green deployments.

```bash
# Enable multiple active revisions
az containerapp revision set-mode \
  --resource-group myRG \
  --name web-api \
  --mode multiple

# Deploy a new revision with an updated image
az containerapp update \
  --resource-group myRG \
  --name web-api \
  --image myregistry.azurecr.io/web-api:v2.0.0 \
  --revision-suffix v2

# Split traffic: 80% to current, 20% to new revision
az containerapp ingress traffic set \
  --resource-group myRG \
  --name web-api \
  --revision-weight "web-api--v1=80" "web-api--v2=20"

# Promote: shift all traffic to the new revision
az containerapp ingress traffic set \
  --resource-group myRG \
  --name web-api \
  --revision-weight "web-api--v2=100"

# List revisions
az containerapp revision list -g myRG -n web-api \
  --query '[].{Name:name, Active:properties.active, TrafficWeight:properties.trafficWeight, Created:properties.createdTime}' -o table
```

### KEDA Auto-Scaling

Container Apps uses KEDA (Kubernetes Event-Driven Autoscaling) to scale based on event sources, not just CPU/memory. This is the killer feature for event-driven architectures.

```bash
# Scale based on HTTP concurrent requests
az containerapp create \
  --resource-group myRG \
  --name http-api \
  --environment kubedojo-env \
  --image myregistry.azurecr.io/api:v1 \
  --target-port 8080 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 30 \
  --scale-rule-name http-rule \
  --scale-rule-type http \
  --scale-rule-http-concurrency 50

# Scale based on Azure Service Bus queue depth
az containerapp create \
  --resource-group myRG \
  --name queue-worker \
  --environment kubedojo-env \
  --image myregistry.azurecr.io/worker:v1 \
  --min-replicas 0 \
  --max-replicas 50 \
  --scale-rule-name queue-rule \
  --scale-rule-type azure-servicebus \
  --scale-rule-metadata "queueName=processing" "namespace=my-sb-ns" "messageCount=5" \
  --scale-rule-auth "connection=sb-connection-string" \
  --secrets "sb-connection-string=$SB_CONNECTION_STRING"
```

Available KEDA scale triggers in Container Apps:

| Trigger | Scales On | Example Use Case |
| :--- | :--- | :--- |
| **HTTP** | Concurrent requests | Web APIs |
| **Azure Service Bus** | Queue/topic message count | Async processing |
| **Azure Storage Queue** | Queue message count | Batch processing |
| **Azure Event Hubs** | Unprocessed event count | Event streaming |
| **Cron** | Schedule | Scheduled batch jobs |
| **TCP** | Concurrent TCP connections | TCP-based services |
| **Custom** | Any Prometheus metric | Custom workloads |

### Dapr Integration

Dapr (Distributed Application Runtime) is built into Container Apps and provides building blocks for microservice communication without requiring you to learn Kubernetes networking.

```text
    ┌─────────────────────────────────────────────────────────┐
    │              Dapr Building Blocks in Container Apps      │
    ├─────────────────┬───────────────────────────────────────┤
    │ Service Invoke  │ Call other services by name            │
    │ Pub/Sub         │ Publish/subscribe messaging            │
    │ State Store     │ Key/value state management             │
    │ Bindings        │ Input/output bindings (queues, DBs)    │
    │ Secrets         │ Secret store integration               │
    └─────────────────┴───────────────────────────────────────┘

    Without Dapr:
    App → HTTP call → http://web-api.internal.company.com:8080/orders

    With Dapr:
    App → Dapr sidecar → http://localhost:3500/v1.0/invoke/web-api/method/orders
    (Dapr handles service discovery, retries, mTLS, observability)
```

```bash
# Enable Dapr on a Container App
az containerapp create \
  --resource-group myRG \
  --name order-service \
  --environment kubedojo-env \
  --image myregistry.azurecr.io/order-service:v1 \
  --target-port 8080 \
  --ingress internal \
  --enable-dapr true \
  --dapr-app-id order-service \
  --dapr-app-port 8080 \
  --dapr-app-protocol http

# Configure a Dapr pub/sub component
az containerapp env dapr-component set \
  --resource-group myRG \
  --name kubedojo-env \
  --dapr-component-name pubsub \
  --yaml '{
    componentType: pubsub.azure.servicebus.topics,
    version: v1,
    metadata: [
      {name: connectionString, secretRef: sb-connection},
    ],
    secrets: [
      {name: sb-connection, value: "<connection-string>"}
    ],
    scopes: [order-service, notification-service]
  }'
```

**War Story**: A logistics startup had 8 microservices communicating via direct HTTP calls. When one service was slow, the calling services would timeout and retry, creating cascading failures. They enabled Dapr on Container Apps, which added automatic retries with exponential backoff, circuit breaking, and distributed tracing---all without changing application code. Their P99 latency dropped from 2.3 seconds to 180 milliseconds, and cascading failures stopped entirely because Dapr's circuit breaker would trip before the cascade could propagate.

---

## Did You Know?

1. **Azure Container Instances can burst to thousands of simultaneous container groups.** During the first weeks of the COVID-19 pandemic, a European government agency used ACI to process 2 million pandemic benefit applications. They spun up 3,000 container instances simultaneously, processed the applications in 6 hours, and shut everything down. Total cost: approximately $240. Running equivalent VMs 24/7 for a week would have cost over $12,000.

2. **Container Apps' free grant covers approximately 6.2 million requests per month** at 50ms average execution time. The free tier includes 180,000 vCPU-seconds and 360,000 GiB-seconds per subscription per month. For a lightweight API that processes requests in 50ms with 0.25 vCPU, you get roughly 720,000 seconds of runtime per month before paying anything.

3. **KEDA can scale Container Apps from zero to 200 replicas in under 2 minutes.** The scale-from-zero cold start adds approximately 5-10 seconds (image pull + container startup), which is significantly faster than the 3-5 minutes it takes to add a new AKS node via cluster autoscaler. For event-driven workloads with bursty traffic, this responsiveness is transformative.

4. **Container Apps runs on a fully managed AKS cluster** that Microsoft operates. Each Container Apps environment maps to a dedicated Kubernetes namespace in this cluster. You can see evidence of this in the resource IDs and in the way networking is configured. However, you have zero direct access to the underlying Kubernetes API---Container Apps exposes only its own simplified API surface.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Using ACI for long-running web services that need auto-scaling | ACI is the first container service teams discover | Use Container Apps for HTTP workloads that need scaling. ACI has no built-in auto-scaling or load balancing. |
| Setting min-replicas to 1 when the workload can tolerate cold starts | Fear of cold start latency | If your workload is event-driven (queue processor, scheduled job), set min-replicas to 0. You only pay when processing events. The 5-10 second cold start is usually acceptable. |
| Not configuring health probes on Container Apps | The app "works" without them | Without health probes, Container Apps cannot detect unhealthy replicas. Configure both liveness and readiness probes at minimum. |
| Using Container Apps for workloads that need Kubernetes-level control | Container Apps seems easier than AKS | If you need custom CRDs, direct pod scheduling, DaemonSets, StatefulSets with complex storage, or host-level access, you need AKS. Container Apps is not a Kubernetes replacement for complex scenarios. |
| Hardcoding connection strings in container environment variables | It works and is easy to set up | Use Container Apps secrets (which map to Kubernetes secrets) and reference them in env vars. Better yet, use Managed Identity to eliminate connection strings entirely. |
| Ignoring revision cleanup | Old revisions accumulate and count toward limits | Deactivate old revisions after promoting new ones. Container Apps has a limit on the number of revisions per app. |
| Not setting resource limits (CPU/memory) per container | Defaults "seem fine" in dev | Without limits, a misbehaving container can consume all available resources and affect other apps in the same environment. Set realistic CPU and memory limits based on load testing. |
| Using Dapr for simple point-to-point HTTP calls between two services | Dapr sounds beneficial and is free to enable | Dapr adds a sidecar container that consumes CPU and memory. For simple architectures with 2-3 services, direct HTTP is simpler. Dapr shines when you have many services and need pub/sub, state management, or cross-cutting concerns. |

---

## Quiz

<details>
<summary>1. What is the fundamental architectural difference between ACI and Azure Container Apps?</summary>

ACI is a raw container execution engine---you provide a container image and resources, and Azure runs it. There is no orchestration, no auto-scaling, no traffic management, and no service discovery. Each container group is an independent unit. Azure Container Apps is built on a managed Kubernetes cluster with KEDA, Envoy, and Dapr. It provides auto-scaling (including scale to zero), traffic splitting between revisions, built-in service discovery, custom domains with automatic TLS, and microservice communication building blocks. Container Apps abstracts the Kubernetes layer so you never interact with it directly.
</details>

<details>
<summary>2. When would you choose ACI over Container Apps?</summary>

Choose ACI for simple, short-lived tasks that do not need scaling: batch jobs, CI/CD build agents, one-off data processing tasks, or sidecar patterns with container groups. ACI is also the right choice for burstable overflow from AKS via virtual nodes. The key criteria: if your workload is a "run once and exit" task, or if it has a fixed number of instances with no need for auto-scaling, load balancing, or traffic management, ACI is simpler and often cheaper. If your workload needs any of those features, Container Apps is the better choice.
</details>

<details>
<summary>3. How does KEDA scaling in Container Apps differ from traditional CPU-based auto-scaling?</summary>

Traditional auto-scaling (like HPA on CPU/memory) reacts to resource utilization---it scales when CPU exceeds a threshold. KEDA scaling reacts to external event sources---queue depth, HTTP concurrency, topic lag, cron schedules, or custom metrics. This is fundamentally different because the scaling signal comes from the demand source, not from the compute resource. A queue-based worker with KEDA scales when messages arrive in the queue, even if current CPU is at 0%. CPU-based scaling would not scale because there is nothing using CPU yet. KEDA also supports scale-to-zero, which traditional CPU-based scaling cannot do (you need at least one instance to measure CPU).
</details>

<details>
<summary>4. You deploy a Container App with two revisions and configure 80/20 traffic splitting. What happens to existing client connections when you change the split to 100/0?</summary>

Existing connections to the 20% revision continue to be served until they naturally close or timeout. Container Apps (via Envoy proxy) performs graceful drain on the deactivated revision, meaning it stops sending new connections but allows existing ones to complete. New connections are immediately routed 100% to the promoted revision. The old revision's replicas are eventually scaled down after the drain period completes. This ensures zero-downtime traffic shifts.
</details>

<details>
<summary>5. What problem does Dapr solve that direct HTTP calls between Container Apps do not?</summary>

Dapr provides a service mesh with built-in retries, circuit breaking, timeouts, mutual TLS, distributed tracing, and observability---all without application code changes. Direct HTTP calls between services have none of these features unless you implement them yourself. Additionally, Dapr provides abstractions for pub/sub messaging, state stores, and bindings, meaning your application code interacts with Dapr's API and Dapr handles the underlying infrastructure (Service Bus, Redis, Cosmos DB, etc.). This makes your application portable across different backends. Swap Redis for Cosmos DB by changing a Dapr component YAML---zero code changes.
</details>

<details>
<summary>6. A Container App processes messages from a Service Bus queue. You set min-replicas to 0 and max-replicas to 50. Describe what happens when 1,000 messages arrive in the queue simultaneously.</summary>

KEDA detects the queue depth increasing and begins scaling from zero. The first replica starts in 5-10 seconds (cold start: image pull + container initialization). KEDA evaluates the scale rule metadata (e.g., messageCount=5, meaning 1 replica per 5 messages) and calculates the desired replica count: 1000/5 = 200, but capped at max-replicas of 50. Over the next 30-60 seconds, Container Apps scales to 50 replicas. Each replica processes messages concurrently. As messages are consumed, queue depth decreases. When the queue empties, KEDA begins the cool-down period (default 300 seconds). If no new messages arrive during cool-down, replicas scale back to zero.
</details>

---

## Hands-On Exercise: Event-Driven Worker on Container Apps Scaling on Queue Length

In this exercise, you will deploy an Azure Container App that processes messages from a Storage Queue, auto-scales based on queue depth using KEDA, and scales to zero when idle.

**Prerequisites**: Azure CLI installed and authenticated.

### Task 1: Create Infrastructure

```bash
RG="kubedojo-aca-lab"
LOCATION="eastus2"
STORAGE_NAME="kubedojoaca$(openssl rand -hex 4)"
ENV_NAME="kubedojo-env"

# Create resource group
az group create --name "$RG" --location "$LOCATION"

# Create storage account for the queue
az storage account create \
  --name "$STORAGE_NAME" \
  --resource-group "$RG" \
  --location "$LOCATION" \
  --sku Standard_LRS

# Create a queue
az storage queue create \
  --name "work-items" \
  --account-name "$STORAGE_NAME"

# Get the storage connection string
STORAGE_CONN=$(az storage account show-connection-string \
  --name "$STORAGE_NAME" -g "$RG" --query connectionString -o tsv)
```

<details>
<summary>Verify Task 1</summary>

```bash
az storage queue list --account-name "$STORAGE_NAME" --query '[].name' -o tsv
```

You should see `work-items`.
</details>

### Task 2: Create the Container Apps Environment

```bash
# Create a Log Analytics workspace (required for Container Apps)
az monitor log-analytics workspace create \
  --resource-group "$RG" \
  --workspace-name kubedojo-logs

LOG_ANALYTICS_ID=$(az monitor log-analytics workspace show \
  -g "$RG" -n kubedojo-logs --query customerId -o tsv)
LOG_ANALYTICS_KEY=$(az monitor log-analytics workspace get-shared-keys \
  -g "$RG" -n kubedojo-logs --query primarySharedKey -o tsv)

# Create Container Apps environment
az containerapp env create \
  --resource-group "$RG" \
  --name "$ENV_NAME" \
  --location "$LOCATION" \
  --logs-workspace-id "$LOG_ANALYTICS_ID" \
  --logs-workspace-key "$LOG_ANALYTICS_KEY"
```

<details>
<summary>Verify Task 2</summary>

```bash
az containerapp env show -g "$RG" -n "$ENV_NAME" \
  --query '{Name:name, State:provisioningState, Location:location}' -o table
```

State should be `Succeeded`.
</details>

### Task 3: Deploy the Queue Worker Container App

```bash
# Deploy a worker that reads from the storage queue
# Using a simple Alpine container that simulates message processing
az containerapp create \
  --resource-group "$RG" \
  --name queue-worker \
  --environment "$ENV_NAME" \
  --image mcr.microsoft.com/k8se/quickstart:latest \
  --cpu 0.25 \
  --memory 0.5Gi \
  --min-replicas 0 \
  --max-replicas 10 \
  --secrets "storage-connection=$STORAGE_CONN" \
  --env-vars "STORAGE_CONNECTION=secretref:storage-connection" "QUEUE_NAME=work-items" \
  --scale-rule-name queue-scaling \
  --scale-rule-type azure-queue \
  --scale-rule-metadata "queueName=work-items" "queueLength=5" "accountName=$STORAGE_NAME" \
  --scale-rule-auth "connection=storage-connection"
```

<details>
<summary>Verify Task 3</summary>

```bash
az containerapp show -g "$RG" -n queue-worker \
  --query '{Name:name, MinReplicas:properties.template.scale.minReplicas, MaxReplicas:properties.template.scale.maxReplicas}' -o table
```

Min should be 0, max should be 10.
</details>

### Task 4: Verify Scale to Zero

```bash
# Check current replica count (should be 0 since queue is empty)
az containerapp replica list -g "$RG" -n queue-worker \
  --query 'length(@)' -o tsv

echo "Current replicas: $(az containerapp replica list -g "$RG" -n queue-worker --query 'length(@)' -o tsv)"
echo "(Should be 0 -- no messages in queue)"
```

<details>
<summary>Verify Task 4</summary>

The replica count should be 0 (or the command returns an empty list). This confirms scale-to-zero is working---no compute cost when idle.
</details>

### Task 5: Generate Load and Observe Scaling

```bash
# Send 50 messages to the queue
for i in $(seq 1 50); do
  az storage message put \
    --queue-name "work-items" \
    --content "work-item-$i" \
    --account-name "$STORAGE_NAME" \
    --connection-string "$STORAGE_CONN"
done

echo "Sent 50 messages. Waiting 30 seconds for KEDA to detect..."
sleep 30

# Check replica count (should have scaled up)
echo "Current replicas: $(az containerapp replica list -g "$RG" -n queue-worker --query 'length(@)' -o tsv)"

# Check the queue length
az storage queue metadata show \
  --queue-name "work-items" \
  --account-name "$STORAGE_NAME" \
  --connection-string "$STORAGE_CONN" \
  --query approximateMessageCount -o tsv
```

<details>
<summary>Verify Task 5</summary>

The replica count should have increased from 0. With 50 messages and a queueLength of 5, KEDA targets 50/5 = 10 replicas (matching our max). The exact number depends on timing and how quickly messages are processed.
</details>

### Task 6: Monitor via Log Analytics

```bash
# View container app system logs
az containerapp logs show \
  --resource-group "$RG" \
  --name queue-worker \
  --type system \
  --follow false

# Query Log Analytics for scaling events (may take a few minutes to appear)
az monitor log-analytics query \
  --workspace "$LOG_ANALYTICS_ID" \
  --analytics-query "ContainerAppSystemLogs_CL | where RevisionName_s contains 'queue-worker' | project TimeGenerated, Log_s | order by TimeGenerated desc | take 20" \
  --output table 2>/dev/null || echo "Logs may take 5-10 minutes to appear in Log Analytics"
```

<details>
<summary>Verify Task 6</summary>

You should see system logs showing replica creation events as the worker scales to meet queue demand. If logs are not yet available, wait a few minutes---Log Analytics ingestion has a delay.
</details>

### Cleanup

```bash
az group delete --name "$RG" --yes --no-wait
```

### Success Criteria

- [ ] Storage queue created with messages successfully sent
- [ ] Container Apps environment created with Log Analytics integration
- [ ] Queue worker deployed with KEDA scale rule on queue depth
- [ ] Worker scaled to zero when queue is empty (no compute cost)
- [ ] Worker scaled up when messages were added to the queue
- [ ] Logs visible showing scaling events

---

## Next Module

[Module 8: Azure Functions & Serverless](module-8-functions.md) --- Learn Azure's function-as-a-service platform with triggers, bindings, and Durable Functions for orchestrating complex serverless workflows.
