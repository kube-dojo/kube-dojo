---
title: "Module 7.4: AKS Storage, Observability & Scaling"
slug: cloud/aks-deep-dive/module-7.4-aks-production
sidebar:
  order: 5
---
**Complexity**: [MEDIUM] | **Time to Complete**: 2.5h | **Prerequisites**: [Module 7.1: AKS Architecture & Node Management](../module-7.1-aks-architecture/)

## Why This Module Matters

In November 2023, an online retailer running on AKS experienced a catastrophic failure during their Black Friday sale. Their order processing service used Azure Premium SSD disks for a write-ahead log. When traffic spiked to 15x normal levels, the disk IOPS ceiling was hit and writes started queuing. The application had no metrics on disk I/O latency---their observability stack only monitored CPU and memory. Without visibility into the real bottleneck, the on-call engineer scaled the deployment from 6 to 30 replicas, which made things dramatically worse: 30 pods now competed for the same disk's IOPS budget. The queue grew, timeouts cascaded, and the entire order pipeline froze for 90 minutes during peak sales hours. Post-incident analysis estimated $4.2 million in lost revenue. The fix was straightforward: migrate to Ultra Disks with provisioned IOPS, add disk I/O metrics to their Grafana dashboards, and implement KEDA-based scaling that responded to queue depth rather than CPU utilization.

This story illustrates a pattern that repeats across organizations: storage, observability, and scaling are treated as afterthoughts during initial cluster setup, then become the root cause of the most painful production incidents. The three topics are deeply interconnected. Without proper observability, you cannot make informed scaling decisions. Without proper scaling, your storage layer gets overwhelmed. Without proper storage, your observability pipeline loses data during the exact moments you need it most.

In this module, you will learn how to choose between Azure Disks and Azure Files for different workload patterns, configure Container Insights with Managed Prometheus and Grafana for full-stack observability, and implement event-driven autoscaling with the KEDA add-on. By the end, you will have a cluster that monitors itself, scales based on real business signals, and stores data on the right tier for each workload.

---

## Azure Storage for Kubernetes: Disks vs Files

AKS integrates with two primary Azure storage services for persistent volumes: Azure Disks and Azure Files. The choice between them depends on your access patterns, performance requirements, and cross-zone needs.

### Azure Disks: Block Storage for Single-Pod Workloads

Azure Disks provide block-level storage that attaches to a single node at a time. This maps to `ReadWriteOnce` (RWO) access mode in Kubernetes---only one pod on one node can mount the disk for read-write access.

```text
    Azure Disk Types for AKS:
    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                 │
    │  Standard HDD     Standard SSD     Premium SSD     Ultra Disk   │
    │  ────────────     ────────────     ───────────     ──────────   │
    │  Max IOPS: 2000   Max IOPS: 6000   Max IOPS: 20k  Max IOPS:   │
    │  Max BW: 500MB/s  Max BW: 750MB/s  Max BW: 900MB  160,000     │
    │  Latency: ~10ms   Latency: ~4ms    Latency: ~1ms  Max BW: 4GB │
    │                                                    Latency:     │
    │  Use: backups,    Use: dev/test,   Use: most      sub-ms       │
    │  cold data        light workloads  production     Use: high-   │
    │                                    databases      perf DBs,    │
    │                                                   real-time    │
    │                                                   analytics    │
    │  Cost: $          Cost: $$         Cost: $$$      Cost: $$$$   │
    └─────────────────────────────────────────────────────────────────┘
```

AKS uses CSI (Container Storage Interface) drivers for storage. The `disk.csi.azure.com` driver handles Azure Disks. You create a StorageClass that specifies the disk type, then reference it in PersistentVolumeClaims.

```yaml
# StorageClass for Premium SSD v2 with provisioned IOPS
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: premium-ssd-v2
provisioner: disk.csi.azure.com
parameters:
  skuName: PremiumV2_LRS
  DiskIOPSReadWrite: "5000"
  DiskMBpsReadWrite: "200"
  cachingMode: None
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true

---
# PVC using the StorageClass
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
  namespace: database
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: premium-ssd-v2
  resources:
    requests:
      storage: 256Gi
```

The `volumeBindingMode: WaitForFirstConsumer` setting is critical for AKS clusters with availability zones. It delays disk creation until a pod actually needs it, ensuring the disk is created in the same zone as the node where the pod is scheduled. Without this, the disk might be created in Zone 1 while the pod gets scheduled to Zone 2, causing a permanent scheduling failure.

### Ultra Disks: When Premium SSD Is Not Enough

Ultra Disks allow you to independently provision IOPS and throughput, decoupled from disk size. A 64 GB Ultra Disk can deliver 50,000 IOPS if you need it. This makes them ideal for databases like PostgreSQL, MySQL, and Cassandra that have high I/O requirements relative to their data size.

```bash
# Enable Ultra Disk support on a node pool
az aks nodepool add \
  --resource-group rg-aks-prod \
  --cluster-name aks-prod-westeurope \
  --name dbpool \
  --node-count 3 \
  --node-vm-size Standard_D8s_v5 \
  --zones 1 2 3 \
  --enable-ultra-ssd \
  --mode User \
  --node-taints "workload=database:NoSchedule" \
  --labels workload=database
```

```yaml
# StorageClass for Ultra Disk
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ultra-disk
provisioner: disk.csi.azure.com
parameters:
  skuName: UltraSSD_LRS
  DiskIOPSReadWrite: "50000"
  DiskMBpsReadWrite: "1000"
  cachingMode: None
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### Azure Files: Shared Storage for Multi-Pod Access

Azure Files provides SMB and NFS file shares that multiple pods across multiple nodes can mount simultaneously (`ReadWriteMany` / RWX). This is essential for workloads that need shared storage: CMS platforms, shared configuration files, machine learning training data, and legacy applications that expect a shared filesystem.

```text
    Azure Files Access Patterns:
    ┌───────────────────────────────────────────────────────────────┐
    │                                                               │
    │  SMB Protocol (default)          NFS Protocol (Premium only)  │
    │  ─────────────────────          ──────────────────────────── │
    │  Windows + Linux                Linux only                    │
    │  Broad compatibility            POSIX-compliant               │
    │  AD-based authentication        No authentication overhead    │
    │  Lower throughput               Higher throughput              │
    │                                                               │
    │  Use: general shared            Use: high-performance         │
    │  storage, Windows               shared storage, ML training   │
    │  workloads                      data, media processing        │
    └───────────────────────────────────────────────────────────────┘
```

```yaml
# StorageClass for Azure Files NFS (Premium tier)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: azure-files-nfs-premium
provisioner: file.csi.azure.com
parameters:
  protocol: nfs
  skuName: Premium_LRS
mountOptions:
  - nconnect=4
  - noresvport
reclaimPolicy: Retain
volumeBindingMode: Immediate
allowVolumeExpansion: true

---
# PVC for shared ML training data
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: training-data
  namespace: ml-pipeline
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: azure-files-nfs-premium
  resources:
    requests:
      storage: 1Ti
```

### Shared Disks for High Availability

Azure Shared Disks allow a single Premium SSD or Ultra Disk to be attached to multiple nodes simultaneously. This enables cluster-aware applications (like SQL Server Failover Cluster Instances or custom HA storage engines) to share a disk at the block level.

```yaml
# StorageClass for shared disks
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: shared-premium-disk
provisioner: disk.csi.azure.com
parameters:
  skuName: Premium_LRS
  maxShares: "3"
  cachingMode: None
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
```

**Warning**: Shared Disks do not provide a filesystem. The application must handle concurrent block-level access using a cluster filesystem (like GFS2) or its own coordination protocol. Do not mount a shared disk with ext4 or xfs from multiple nodes---you will corrupt your data.

### The Storage Decision Matrix

| Criteria | Azure Disk (Premium) | Azure Disk (Ultra) | Azure Files (SMB) | Azure Files (NFS) |
| :--- | :--- | :--- | :--- | :--- |
| **Access mode** | RWO | RWO | RWX | RWX |
| **Max IOPS** | 20,000 | 160,000 | 10,000 | 100,000 |
| **Cross-zone** | No (zone-locked) | No (zone-locked) | Yes (ZRS available) | Yes (ZRS available) |
| **Latency** | ~1ms | Sub-ms | ~5-10ms | ~2-5ms |
| **Windows support** | Yes | Yes | Yes | No |
| **Best for** | Databases, stateful apps | High-IOPS databases | Shared config, CMS | ML data, media |
| **Cost** | $$$ | $$$$ | $$ | $$$ |

---

## Container Insights and Azure Monitor

Container Insights is Azure's native observability solution for AKS. It collects logs, metrics, and performance data from your cluster and presents them in the Azure portal with pre-built dashboards and query capabilities.

### Enabling Container Insights

```bash
# Create a Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group rg-aks-prod \
  --workspace-name law-aks-prod \
  --location westeurope \
  --retention-in-days 90

WORKSPACE_ID=$(az monitor log-analytics workspace show \
  -g rg-aks-prod -n law-aks-prod --query id -o tsv)

# Enable Container Insights
az aks enable-addons \
  --resource-group rg-aks-prod \
  --name aks-prod-westeurope \
  --addons monitoring \
  --workspace-resource-id "$WORKSPACE_ID"

# Verify the monitoring agent is running
k get pods -n kube-system -l component=ama-logs
```

### What Container Insights Collects

Container Insights deploys a monitoring agent (Azure Monitor Agent) as a DaemonSet on each node. This agent collects:

- **Node metrics**: CPU, memory, disk I/O, network throughput per node
- **Pod metrics**: CPU/memory requests vs actual usage, restart counts, OOM kills
- **Container logs**: stdout/stderr from all containers (sent to Log Analytics)
- **Kubernetes events**: Pod scheduling, image pulls, resource quota violations
- **Inventory data**: Running pods, nodes, deployments, services

```bash
# Query container logs in Log Analytics
az monitor log-analytics query \
  --workspace "$WORKSPACE_ID" \
  --analytics-query "ContainerLogV2 | where ContainerName == 'payment-service' | where LogMessage contains 'error' | top 20 by TimeGenerated desc" \
  --timespan "PT6H"
```

### Cost Control for Container Insights

Container Insights can generate significant Log Analytics costs if you send every log line from every container. Use the ConfigMap to control what gets collected:

```yaml
# Save as container-insights-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: container-azm-ms-agentconfig
  namespace: kube-system
data:
  schema-version: v1
  config-version: v1
  log-data-collection-settings: |
    [log_collection_settings]
      [log_collection_settings.stdout]
        enabled = true
        exclude_namespaces = ["kube-system", "gatekeeper-system"]
      [log_collection_settings.stderr]
        enabled = true
        exclude_namespaces = ["kube-system"]
      [log_collection_settings.env_var]
        enabled = false
  prometheus-data-collection-settings: |
    [prometheus_data_collection_settings.cluster]
      interval = "60s"
      monitor_kubernetes_pods = true
```

```bash
k apply -f container-insights-config.yaml
```

---

## Managed Prometheus and Grafana: Cloud-Native Monitoring

While Container Insights works well for logs and basic metrics, production teams often need Prometheus for application-specific metrics and Grafana for custom dashboards. Azure offers fully managed versions of both, eliminating the operational burden of running your own Prometheus server and Grafana instance.

### Setting Up Managed Prometheus

Azure Monitor managed service for Prometheus stores metrics in an Azure Monitor workspace. AKS ships metrics using a Prometheus-compatible agent.

```bash
# Create an Azure Monitor workspace (for Prometheus)
az monitor account create \
  --resource-group rg-aks-prod \
  --name amw-aks-prod \
  --location westeurope

MONITOR_WORKSPACE_ID=$(az monitor account show \
  -g rg-aks-prod -n amw-aks-prod --query id -o tsv)

# Enable Managed Prometheus on the cluster
az aks update \
  --resource-group rg-aks-prod \
  --name aks-prod-westeurope \
  --enable-azure-monitor-metrics \
  --azure-monitor-workspace-resource-id "$MONITOR_WORKSPACE_ID"

# Verify the Prometheus agent is running
k get pods -n kube-system -l rsName=ama-metrics
```

### Setting Up Managed Grafana

```bash
# Create a Managed Grafana instance
az grafana create \
  --resource-group rg-aks-prod \
  --name grafana-aks-prod \
  --location westeurope

# Link Grafana to the Azure Monitor workspace
GRAFANA_ID=$(az grafana show -g rg-aks-prod -n grafana-aks-prod --query id -o tsv)

az monitor account update \
  --resource-group rg-aks-prod \
  --name amw-aks-prod \
  --linked-grafana "$GRAFANA_ID"

# Get the Grafana URL
az grafana show -g rg-aks-prod -n grafana-aks-prod --query "properties.endpoint" -o tsv
```

Once linked, Managed Grafana automatically discovers the Prometheus data source. Azure provides pre-built dashboards for Kubernetes cluster monitoring, node performance, pod resource usage, and more.

### Custom Prometheus Metrics from Your Application

Your application can expose custom Prometheus metrics, and the managed Prometheus agent will scrape them automatically if you annotate your pods correctly.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
  namespace: payments
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        - name: payment
          image: myregistry.azurecr.io/payment-service:v2.1.0
          ports:
            - containerPort: 8080
              name: http
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "1"
              memory: "512Mi"
```

### Creating Alert Rules

```bash
# Create a Prometheus alert rule for high error rate
az monitor metrics alert create \
  --resource-group rg-aks-prod \
  --name "payment-high-error-rate" \
  --scopes "$MONITOR_WORKSPACE_ID" \
  --condition "avg http_requests_total{status=~'5..',service='payment-service'} by (service) / avg http_requests_total{service='payment-service'} by (service) > 0.05" \
  --description "Payment service error rate exceeds 5%" \
  --severity 1 \
  --window-size 5m \
  --evaluation-frequency 1m
```

For more flexible alerting, use Prometheus-native alert rules through the Azure Monitor workspace:

```yaml
# PrometheusRuleGroup for custom alerts
apiVersion: alerts.monitor.azure.com/v1
kind: PrometheusRuleGroup
metadata:
  name: payment-alerts
spec:
  rules:
    - alert: PaymentServiceHighLatency
      expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{service="payment-service"}[5m])) > 2
      for: 3m
      labels:
        severity: warning
      annotations:
        summary: "Payment service p99 latency exceeds 2 seconds"
    - alert: PaymentServiceDown
      expr: up{job="payment-service"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Payment service is down"
```

---

## KEDA: Event-Driven Autoscaling

The standard Kubernetes Horizontal Pod Autoscaler (HPA) scales based on CPU and memory utilization. This works for stateless web servers but fails spectacularly for event-driven workloads: message queue consumers, batch processors, and services that need to scale based on business metrics rather than infrastructure metrics.

KEDA (Kubernetes Event-Driven Autoscaler) extends the HPA with over 60 scalers that can trigger scaling from external event sources: Azure Service Bus queue depth, Azure Event Hubs partition lag, PostgreSQL query results, Prometheus metrics, and many more.

```text
    Traditional HPA:                    KEDA:
    ┌──────────────────┐               ┌──────────────────┐
    │ Metrics Server   │               │ KEDA Operator    │
    │ (CPU/memory only)│               │ (60+ scalers)    │
    │                  │               │                  │
    │ "Pod at 80% CPU" │               │ "Queue has 500   │
    │ → scale up       │               │  messages"       │
    │                  │               │ → scale up       │
    │ Cannot scale     │               │                  │
    │ to zero          │               │ Can scale to     │
    └──────────────────┘               │ zero (!)         │
                                       └──────────────────┘
```

### Enabling the KEDA Add-on

```bash
# Enable KEDA as an AKS add-on
az aks update \
  --resource-group rg-aks-prod \
  --name aks-prod-westeurope \
  --enable-keda

# Verify KEDA pods are running
k get pods -n kube-system -l app.kubernetes.io/name=keda-operator
```

### Scaling Based on Azure Service Bus Queue Depth

This is the most common KEDA pattern in Azure: scale your consumer pods based on how many messages are waiting in a queue.

```yaml
# ScaledObject: scale order-processor based on Service Bus queue depth
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: order-processor-scaler
  namespace: orders
spec:
  scaleTargetRef:
    name: order-processor
  pollingInterval: 15
  cooldownPeriod: 120
  minReplicaCount: 0      # Scale to zero when queue is empty!
  maxReplicaCount: 50
  triggers:
    - type: azure-servicebus
      metadata:
        queueName: incoming-orders
        namespace: sb-prod-westeurope
        messageCount: "10"  # 1 pod per 10 messages
      authenticationRef:
        name: servicebus-auth
```

The `messageCount: "10"` means KEDA targets 1 pod for every 10 messages in the queue. If there are 250 messages, KEDA will scale to 25 replicas. When the queue drains to zero, KEDA scales the deployment down to 0 replicas, saving costs entirely.

### KEDA Authentication with Workload Identity

KEDA needs credentials to check the queue depth. Using Workload Identity (from Module 7.3), you can avoid storing connection strings:

```yaml
# TriggerAuthentication using Workload Identity
apiVersion: keda.sh/v1alpha1
kind: TriggerAuthentication
metadata:
  name: servicebus-auth
  namespace: orders
spec:
  podIdentity:
    provider: azure-workload
    identityId: "<CLIENT_ID_OF_MANAGED_IDENTITY>"
```

The managed identity needs the "Azure Service Bus Data Receiver" role on the Service Bus namespace to check queue metrics.

### Scaling Based on Prometheus Metrics

KEDA can also scale based on custom Prometheus metrics from your Azure Monitor workspace. This lets you scale on any business metric your application exposes.

```yaml
# Scale based on a custom Prometheus metric
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: api-gateway-scaler
  namespace: gateway
spec:
  scaleTargetRef:
    name: api-gateway
  pollingInterval: 30
  cooldownPeriod: 180
  minReplicaCount: 2
  maxReplicaCount: 30
  triggers:
    - type: prometheus
      metadata:
        serverAddress: "http://prometheus-server.monitoring:9090"
        metricName: http_requests_per_second
        query: "sum(rate(http_requests_total{service='api-gateway'}[2m]))"
        threshold: "100"  # 1 pod per 100 requests/sec
```

### KEDA Scaling Strategies Compared

| Scaler | Trigger Source | Scale to Zero | Typical Use Case |
| :--- | :--- | :--- | :--- |
| **azure-servicebus** | Queue message count | Yes | Order processing, async tasks |
| **azure-eventhub** | Consumer group lag | Yes | Event streaming, IoT data |
| **azure-queue** | Storage queue length | Yes | Background jobs, batch processing |
| **prometheus** | Any Prometheus metric | No (min 1) | RPS-based scaling, custom metrics |
| **cron** | Time schedule | Yes | Predictable traffic patterns |
| **azure-monitor** | Azure Monitor metrics | Yes | Infrastructure-based triggers |

### Combining KEDA with Cluster Autoscaler

KEDA scales pods. The cluster autoscaler scales nodes. They work together beautifully:

1. KEDA detects 500 messages in the queue and scales the deployment to 50 replicas
2. The scheduler finds that existing nodes can only fit 30 of those pods
3. 20 pods go to `Pending` state
4. The cluster autoscaler detects pending pods and adds nodes to the VMSS
5. New nodes register, and the scheduler places the remaining pods
6. Messages get processed. Queue drains.
7. KEDA scales pods down to 0
8. Cluster autoscaler detects underutilized nodes and removes them after the cool-down period

```text
    Queue depth: 500 messages
    ┌─────────────────────────────────────────────────────────────────┐
    │ t=0s   KEDA: 0 pods → 50 pods (target)                         │
    │ t=10s  Scheduler: 30 pods running, 20 pending                   │
    │ t=20s  Cluster Autoscaler: adding 4 nodes to VMSS               │
    │ t=80s  New nodes ready: 50/50 pods running                      │
    │ t=300s Queue drained to 0 messages                              │
    │ t=420s KEDA: 50 pods → 0 pods                                   │
    │ t=1020s Cluster Autoscaler: removing 4 underutilized nodes      │
    └─────────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

1. **Azure Disk IOPS scale with disk size on Premium SSD, but Ultra Disk decouples them.** A 256 GB Premium SSD v1 gets 1,100 IOPS. To get 5,000 IOPS you need a 1 TB disk, even if you only store 50 GB of data. Ultra Disk lets you provision 50,000 IOPS on a 64 GB disk. This decoupling can save thousands of dollars per month for I/O-intensive databases that do not need large storage volumes.

2. **KEDA can scale to zero replicas, which the standard HPA cannot do.** The HPA requires a minimum of 1 replica. KEDA's ability to scale to zero is transformative for cost optimization on batch processing workloads. A cluster with 200 different queue consumers that are each idle 95% of the time can run zero pods for most of those consumers, only spinning them up when messages arrive. Combined with the cluster autoscaler, this means you can run a multi-tenant batch processing platform where idle tenants cost nothing.

3. **Azure Managed Prometheus stores metrics for 18 months at no additional retention cost.** Self-hosted Prometheus typically requires careful capacity planning for long-term storage (using Thanos or Cortex). Azure Monitor workspace handles this natively, making it possible to query 18 months of historical metrics for capacity planning and trend analysis without managing any storage infrastructure.

4. **The `nconnect` mount option for Azure Files NFS multiplies throughput by opening multiple TCP connections.** A single NFS connection typically tops out at 300-400 MB/s due to TCP window limitations. Setting `nconnect=4` in your StorageClass mount options opens 4 parallel TCP connections per mount, effectively quadrupling throughput. This is essential for ML training workloads that read large datasets from shared storage.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Using Premium SSD when IOPS requirement exceeds the disk-size-to-IOPS ratio | Not understanding that Premium SSD IOPS are tied to disk size | Calculate required IOPS first. If you need high IOPS on small storage, use Ultra Disk or Premium SSD v2 |
| Mounting Azure Disks without `WaitForFirstConsumer` binding mode | Copying StorageClass examples that use `Immediate` binding | Always use `volumeBindingMode: WaitForFirstConsumer` on zone-aware clusters to prevent zone mismatches |
| Sending all container logs to Log Analytics without filtering | Default Container Insights config collects everything | Use the ConfigMap to exclude noisy namespaces (kube-system, monitoring) and disable env_var collection |
| Setting KEDA minReplicaCount to 0 for latency-sensitive services | Attracted by cost savings of scale-to-zero | Only scale to zero for batch/queue consumers. Latency-sensitive services need minReplicaCount >= 1 to avoid cold start delays |
| Not configuring PodDisruptionBudgets for KEDA-scaled workloads | PDBs seem unnecessary for "elastic" workloads | KEDA scales pods, but node upgrades drain them. Without PDBs, all replicas can be evicted simultaneously during cluster upgrades |
| Mounting Azure Files SMB when NFS would perform better | SMB is the default and works on both Windows and Linux | For Linux-only workloads needing high throughput, always use NFS with the `nconnect` mount option |
| Creating Grafana dashboards without alert rules | "We will check the dashboards when something is wrong" | If nobody is watching the dashboard when the incident starts, it has zero value. Always pair dashboards with alert rules |
| Ignoring disk I/O metrics in observability setup | CPU and memory are the default metrics; disk I/O requires explicit configuration | Add disk IOPS, throughput, and latency to your monitoring ConfigMap and Grafana dashboards |

---

## Quiz

<details>
<summary>1. Why is `volumeBindingMode: WaitForFirstConsumer` critical for Azure Disk StorageClasses in AKS?</summary>

Azure Disks are zone-locked---a disk created in Availability Zone 1 can only be attached to a node in Zone 1. With `Immediate` binding mode, the PVC creates the disk as soon as the PVC is created, before any pod references it. If the disk lands in Zone 1 but the pod gets scheduled to Zone 2, the pod will be stuck in Pending forever because the disk cannot be attached across zones. `WaitForFirstConsumer` delays disk creation until a pod actually claims the PVC, ensuring the disk is created in the same zone as the node where the pod will run.
</details>

<details>
<summary>2. When should you choose Ultra Disk over Premium SSD?</summary>

Choose Ultra Disk when your workload requires high IOPS or throughput that exceeds what Premium SSD can deliver at your needed storage size. Premium SSD ties IOPS to disk size (a 256 GB P15 provides only 1,100 IOPS), so getting 20,000 IOPS requires provisioning a 1 TB+ disk even if you store far less data. Ultra Disk decouples IOPS, throughput, and capacity---you can provision 50,000 IOPS on a 64 GB disk. Ultra Disk also delivers sub-millisecond latency compared to Premium SSD's ~1ms. The trade-off is higher cost per GB and the requirement to enable Ultra Disk support on the node pool.
</details>

<details>
<summary>3. What is the difference between Azure Files SMB and NFS, and when should you use each?</summary>

SMB (Server Message Block) is the default protocol for Azure Files, supported on both Windows and Linux. It uses authentication-based access (AD/Entra ID) and is broadly compatible with applications. NFS (Network File System) is available only on Premium tier, supports only Linux, and provides POSIX-compliant file system semantics with higher throughput. Use SMB when you need Windows compatibility or AD-based access control. Use NFS for Linux workloads that need high throughput (ML training data, media processing), especially with the `nconnect=4` mount option that multiplies throughput by opening multiple parallel TCP connections.
</details>

<details>
<summary>4. How does KEDA differ from the standard Kubernetes HPA?</summary>

KEDA extends the HPA in three important ways: (1) it can scale based on external event sources beyond CPU and memory---Azure Service Bus queue depth, Event Hub consumer lag, Prometheus metrics, cron schedules, and over 60 other triggers, (2) it can scale to zero replicas, which the HPA cannot do (HPA minimum is 1), and (3) it supports authentication to external systems through TriggerAuthentication resources that integrate with Workload Identity. KEDA works alongside the HPA, not instead of it---KEDA creates and manages HPA objects under the hood.
</details>

<details>
<summary>5. How do KEDA and the cluster autoscaler work together?</summary>

They operate at different levels. KEDA scales pods based on external event sources (e.g., queue depth). When KEDA scales a deployment to many replicas and the existing nodes do not have enough resources, some pods enter Pending state. The cluster autoscaler detects pending pods, calculates how many additional nodes are needed, and scales the VMSS. When the workload completes and KEDA scales pods back down, the cluster autoscaler detects underutilized nodes (below 50% utilization for 10 minutes by default) and removes them. The full cycle---from zero pods to many pods on new nodes, back to zero pods with nodes removed---is fully automated.
</details>

<details>
<summary>6. Why should you filter container logs in Container Insights rather than collecting everything?</summary>

Container Insights sends logs to Azure Log Analytics, which charges based on data ingestion volume. A typical AKS cluster generates gigabytes of logs daily, and much of it is low-value noise from system namespaces (kube-system, gatekeeper-system), health checks, and verbose debug logging. Without filtering, Log Analytics costs can easily exceed the cost of the cluster itself. Use the Container Insights ConfigMap to exclude noisy namespaces from stdout/stderr collection, disable environment variable collection, and set appropriate Prometheus scrape intervals. Start with aggressive filtering and add log sources as needed, not the other way around.
</details>

<details>
<summary>7. What does the `maxShares` parameter on an Azure Disk StorageClass enable, and what is the critical caveat?</summary>

The `maxShares` parameter enables Azure Shared Disks, allowing a single Premium SSD or Ultra Disk to be attached to multiple nodes simultaneously. This is used for cluster-aware applications like SQL Server Failover Cluster Instances that need shared block storage. The critical caveat is that Shared Disks provide raw block access, not a shared filesystem. You must NOT mount a shared disk with a standard filesystem like ext4 or xfs from multiple nodes, because these filesystems are not cluster-aware and concurrent writes will corrupt your data. You need a cluster filesystem (like GFS2 or OCFS2) or an application that coordinates its own block-level access.
</details>

---

## Hands-On Exercise: KEDA + Azure Service Bus Queue Scaling + Monitor Alerts

In this exercise, you will set up event-driven autoscaling where a consumer deployment scales from zero to many replicas based on Azure Service Bus queue depth, with monitoring alerts that fire when the queue exceeds a threshold.

### Prerequisites

- AKS cluster with KEDA add-on enabled
- Azure CLI authenticated
- Workload Identity configured (from Module 7.3)

### Task 1: Create the Azure Service Bus Namespace and Queue

<details>
<summary>Solution</summary>

```bash
# Create the Service Bus namespace
az servicebus namespace create \
  --resource-group rg-aks-prod \
  --name sb-aks-lab-$(openssl rand -hex 4) \
  --location westeurope \
  --sku Standard

SB_NAMESPACE=$(az servicebus namespace list -g rg-aks-prod \
  --query "[0].name" -o tsv)

# Create the queue
az servicebus queue create \
  --resource-group rg-aks-prod \
  --namespace-name "$SB_NAMESPACE" \
  --name incoming-orders \
  --max-size 1024 \
  --default-message-time-to-live "PT1H"

# Get the connection string for the producer script
SB_CONNECTION=$(az servicebus namespace authorization-rule keys list \
  --resource-group rg-aks-prod \
  --namespace-name "$SB_NAMESPACE" \
  --name RootManageSharedAccessKey \
  --query primaryConnectionString -o tsv)

echo "Service Bus Namespace: $SB_NAMESPACE"
```

</details>

### Task 2: Set Up Workload Identity for KEDA and the Consumer

Create a managed identity that KEDA and the consumer pods will use to read from the queue.

<details>
<summary>Solution</summary>

```bash
# Get the OIDC issuer
OIDC_ISSUER=$(az aks show -g rg-aks-prod -n aks-prod-westeurope \
  --query "oidcIssuerProfile.issuerUrl" -o tsv)

# Create the managed identity
az identity create \
  --resource-group rg-aks-prod \
  --name id-order-processor \
  --location westeurope

SB_CLIENT_ID=$(az identity show -g rg-aks-prod -n id-order-processor \
  --query clientId -o tsv)
SB_PRINCIPAL_ID=$(az identity show -g rg-aks-prod -n id-order-processor \
  --query principalId -o tsv)

# Grant Service Bus Data Receiver role
SB_ID=$(az servicebus namespace show -g rg-aks-prod -n "$SB_NAMESPACE" --query id -o tsv)

az role assignment create \
  --assignee-object-id "$SB_PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Azure Service Bus Data Receiver" \
  --scope "$SB_ID"

# Create federated credential
az identity federated-credential create \
  --name fed-order-processor \
  --identity-name id-order-processor \
  --resource-group rg-aks-prod \
  --issuer "$OIDC_ISSUER" \
  --subject "system:serviceaccount:orders:order-processor-sa" \
  --audiences "api://AzureADTokenExchange"

# Create the namespace and service account
k create namespace orders

k apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: order-processor-sa
  namespace: orders
  annotations:
    azure.workload.identity/client-id: "$SB_CLIENT_ID"
  labels:
    azure.workload.identity/use: "true"
EOF
```

</details>

### Task 3: Deploy the Consumer Application and KEDA ScaledObject

Deploy the consumer and configure KEDA to scale it based on queue depth.

<details>
<summary>Solution</summary>

```bash
# Deploy the order processor (a simple consumer simulator)
k apply -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-processor
  namespace: orders
spec:
  replicas: 0
  selector:
    matchLabels:
      app: order-processor
  template:
    metadata:
      labels:
        app: order-processor
    spec:
      serviceAccountName: order-processor-sa
      containers:
        - name: processor
          image: busybox:1.36
          command:
            - /bin/sh
            - -c
            - |
              echo "Order processor started. Processing messages..."
              while true; do
                echo "$(date): Processing order batch..."
                sleep 5
              done
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "250m"
              memory: "256Mi"
EOF

# Create the KEDA TriggerAuthentication
TENANT_ID=$(az account show --query tenantId -o tsv)

k apply -f - <<EOF
apiVersion: keda.sh/v1alpha1
kind: TriggerAuthentication
metadata:
  name: servicebus-workload-auth
  namespace: orders
spec:
  podIdentity:
    provider: azure-workload
    identityId: "$SB_CLIENT_ID"
EOF

# Create the ScaledObject
k apply -f - <<EOF
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: order-processor-scaler
  namespace: orders
spec:
  scaleTargetRef:
    name: order-processor
  pollingInterval: 10
  cooldownPeriod: 60
  minReplicaCount: 0
  maxReplicaCount: 20
  triggers:
    - type: azure-servicebus
      metadata:
        queueName: incoming-orders
        namespace: $SB_NAMESPACE
        messageCount: "5"
      authenticationRef:
        name: servicebus-workload-auth
EOF

# Verify KEDA is watching the queue
k get scaledobject -n orders
k get hpa -n orders
```

</details>

### Task 4: Send Messages and Observe Scaling

Flood the queue with messages and watch KEDA scale the consumer.

<details>
<summary>Solution</summary>

```bash
# Verify current state: 0 replicas
k get deployment order-processor -n orders

# Send 100 messages to the queue
for i in $(seq 1 100); do
  az servicebus queue message send \
    --resource-group rg-aks-prod \
    --namespace-name "$SB_NAMESPACE" \
    --queue-name incoming-orders \
    --body "{\"orderId\": \"ORD-$i\", \"amount\": $((RANDOM % 1000 + 1))}"
done

echo "Sent 100 messages. Watching KEDA scale..."

# Watch the scaling happen (KEDA polls every 10 seconds)
# Run this in a loop or use watch
k get deployment order-processor -n orders -w

# After a few moments, you should see replicas increasing:
# order-processor   0/20   0  0  0s
# order-processor   20/20  20 0  15s
# (KEDA targets 1 pod per 5 messages: 100/5 = 20 pods)

# Check the HPA that KEDA created
k describe hpa -n orders

# Check queue depth decreasing (in a real app, consumers would drain the queue)
az servicebus queue show \
  --resource-group rg-aks-prod \
  --namespace-name "$SB_NAMESPACE" \
  --name incoming-orders \
  --query "countDetails.activeMessageCount" -o tsv
```

</details>

### Task 5: Set Up Azure Monitor Alert for Queue Backlog

Create an alert that fires when the queue depth exceeds a threshold, indicating consumers cannot keep up.

<details>
<summary>Solution</summary>

```bash
# Create an action group for notifications
az monitor action-group create \
  --resource-group rg-aks-prod \
  --name ag-aks-oncall \
  --short-name aks-oncall \
  --email-receiver name="Platform Team" address="platform-oncall@contoso.com"

ACTION_GROUP_ID=$(az monitor action-group show \
  -g rg-aks-prod -n ag-aks-oncall --query id -o tsv)

# Create metric alert on Service Bus queue depth
az monitor metrics alert create \
  --resource-group rg-aks-prod \
  --name "high-order-queue-depth" \
  --scopes "$SB_ID" \
  --condition "avg ActiveMessages > 200" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --severity 2 \
  --description "Order queue has more than 200 active messages for 5 minutes. Consumers may not be keeping up." \
  --action "$ACTION_GROUP_ID"

# Verify the alert rule
az monitor metrics alert show \
  -g rg-aks-prod -n "high-order-queue-depth" -o table

# Create a second alert for KEDA scaling failures
# (when KEDA hits maxReplicaCount but queue is still growing)
az monitor metrics alert create \
  --resource-group rg-aks-prod \
  --name "order-queue-critical" \
  --scopes "$SB_ID" \
  --condition "avg ActiveMessages > 1000" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --severity 1 \
  --description "CRITICAL: Order queue exceeds 1000 messages. KEDA may have hit maxReplicaCount. Investigate immediately." \
  --action "$ACTION_GROUP_ID"
```

</details>

### Task 6: Verify Scale-to-Zero

Drain the queue and confirm KEDA scales the deployment back to zero.

<details>
<summary>Solution</summary>

```bash
# In a real scenario, consumers process messages. For the lab, purge the queue:
az servicebus queue message purge \
  --resource-group rg-aks-prod \
  --namespace-name "$SB_NAMESPACE" \
  --queue-name incoming-orders

# Watch the deployment scale down (takes cooldownPeriod seconds: 60s in our config)
echo "Waiting for KEDA cooldown (60 seconds)..."
k get deployment order-processor -n orders -w

# After ~60-90 seconds:
# order-processor   20/0   20  20  2m
# order-processor   0/0    0   0   3m

# Verify final state
k get pods -n orders
# Expected: No resources found in orders namespace

# Verify the ScaledObject status
k describe scaledobject order-processor-scaler -n orders | grep -A5 "Status:"

echo "Scale-to-zero verified. Clean up when ready:"
echo "az group delete --name rg-aks-prod --yes --no-wait"
```

</details>

### Success Criteria

- [ ] Azure Service Bus namespace and queue created
- [ ] Workload Identity configured for the consumer (managed identity + federated credential + service account)
- [ ] Consumer deployment starts at 0 replicas
- [ ] KEDA ScaledObject and TriggerAuthentication deployed
- [ ] Sending 100 messages causes KEDA to scale to 20 replicas (100 messages / 5 per pod)
- [ ] HPA created by KEDA is visible with `kubectl get hpa`
- [ ] Azure Monitor alert configured for queue depth > 200 (warning) and > 1000 (critical)
- [ ] After queue is drained, deployment scales back to 0 replicas within the cooldown period
- [ ] No credentials stored in Kubernetes Secrets (Workload Identity used throughout)

---

## Next Module

This is the final module in the AKS Deep Dive series. You now have the knowledge to architect, secure, network, observe, and scale production AKS clusters. For further learning, explore the [Platform Engineering Track](../../platform/) to deepen your understanding of SRE practices, GitOps workflows, and DevSecOps pipelines that build on this AKS foundation.
