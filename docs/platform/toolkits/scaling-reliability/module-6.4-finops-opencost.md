# Module 6.4: FinOps with OpenCost

> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes

## Overview

Your cluster is running. Pods are healthy. Alerts are quiet. But nobody can answer the question: "How much does Team Alpha's microservice actually cost us?" This module teaches you to see, allocate, and reduce Kubernetes spending using OpenCost and FinOps practices.

**What You'll Learn**:
- OpenCost installation, dashboard, and cost allocation
- Resource right-sizing: finding and eliminating waste
- Spot and preemptible instance strategies for workloads
- Idle resource cleanup patterns
- Cost-aware architecture with namespace quotas and LimitRanges

**Prerequisites**:
- Kubernetes resource requests and limits
- [Module 6.1: Karpenter](module-6.1-karpenter.md) — Node provisioning and spot strategies
- Helm basics
- Namespace and RBAC fundamentals

---

## Why This Module Matters

A platform team at a Series B startup ran 14 microservices on EKS. Monthly bill: $38,000. After one week of FinOps analysis with OpenCost, they discovered three things. A forgotten load-test namespace was burning $4,200/month. The payments service requested 4 CPU but averaged 0.3 CPU utilization. And the staging cluster ran 24/7 for a team that worked 9-to-5. They cut their bill to $17,000 in a single sprint. No features removed. No performance degraded. Just waste, made visible and eliminated.

That is FinOps: the practice of making cloud spending visible, accountable, and optimized. Without it, Kubernetes becomes a black box that eats money.

---

## Did You Know?

- The average Kubernetes cluster wastes **60-70%** of its provisioned compute resources. For a company spending $100,000/month on cloud, that is $60,000-$70,000 burned on idle CPU and memory every month.
- OpenCost was donated to the CNCF by Kubecost in 2022 and became a **CNCF Sandbox project**. It provides real-time cost monitoring without requiring a commercial license, saving teams the **$5,000-$50,000/year** that enterprise cost tools charge.
- Switching from on-demand to spot instances for stateless workloads typically saves **60-90%** on compute. A workload costing $1,000/month on-demand drops to $100-$400/month on spot.
- Companies that implement FinOps practices report an average of **20-30% cloud cost reduction** in the first year, according to the FinOps Foundation's annual survey.

---

## FinOps and Kubernetes Cost Model

Before you can optimize, you need to understand what drives cost in a cluster.

```
KUBERNETES COST BREAKDOWN
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                      TOTAL CLUSTER COST                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  COMPUTE (typically 60-70% of total)                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Node cost = instance price x hours running               │  │
│  │  Allocated = sum of pod resource requests                 │  │
│  │  Idle = node capacity - allocated (THIS IS YOUR WASTE)    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  STORAGE (typically 15-25%)                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  PersistentVolumes (provisioned, not necessarily used)    │  │
│  │  Snapshots and backups                                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  NETWORK (typically 5-15%)                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Load balancers, NAT gateways, cross-AZ traffic          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

KEY INSIGHT: Kubernetes charges nothing. The CLOUD charges for
resources Kubernetes requests. Your goal is to minimize the gap
between what pods USE and what nodes PROVIDE.
```

---

## OpenCost: Installation and Setup

OpenCost is a CNCF project that provides real-time Kubernetes cost monitoring. It reads node pricing from cloud provider APIs and allocates costs to namespaces, pods, labels, and teams.

### Install with Helm

```bash
# Add the OpenCost Helm repository
helm repo add opencost https://opencost.github.io/opencost-helm-chart
helm repo update

# Install OpenCost (requires Prometheus already running)
helm upgrade --install opencost opencost/opencost \
  --namespace opencost \
  --create-namespace \
  --set opencost.prometheus.internal.enabled=false \
  --set opencost.prometheus.external.url="http://prometheus-server.monitoring.svc:80" \
  --set opencost.ui.enabled=true

# Verify installation
kubectl get pods -n opencost
kubectl get svc -n opencost
```

### Access the Dashboard

```bash
# Port-forward the OpenCost UI
kubectl port-forward -n opencost svc/opencost 9090:9090

# Open http://localhost:9090 in your browser
# You'll see cost breakdowns by namespace, controller, and pod
```

### Query the API Directly

```bash
# Get cost allocation for the last 24 hours, grouped by namespace
kubectl port-forward -n opencost svc/opencost 9003:9003 &

curl -s "http://localhost:9003/allocation/compute?window=24h&aggregate=namespace" \
  | python3 -m json.tool

# Get cost by label (e.g., team label)
curl -s "http://localhost:9003/allocation/compute?window=7d&aggregate=label:team" \
  | python3 -m json.tool

# Get cost by controller (deployments, statefulsets)
curl -s "http://localhost:9003/allocation/compute?window=24h&aggregate=controller" \
  | python3 -m json.tool
```

```
OPENCOST ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐
│  Cloud       │     │  Kubernetes  │     │    Prometheus        │
│  Pricing API │     │  API Server  │     │    (metrics store)   │
│  ($/hour per │     │  (node specs,│     │    (CPU/mem usage    │
│   instance)  │     │   pod specs) │     │     over time)       │
└──────┬───────┘     └──────┬───────┘     └──────────┬───────────┘
       │                    │                         │
       └────────────────────┼─────────────────────────┘
                            │
                   ┌────────▼────────┐
                   │    OPENCOST     │
                   │                 │
                   │  Combines:      │
                   │  • Node price   │
                   │  • Pod requests │
                   │  • Actual usage │
                   │                 │
                   │  Calculates:    │
                   │  • Cost per pod │
                   │  • Cost per NS  │
                   │  • Idle cost    │
                   │  • Efficiency % │
                   └────────┬────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
                ▼           ▼           ▼
           Dashboard    REST API    Prometheus
           (UI)        (JSON)      (metrics export)
```

---

## Resource Right-Sizing

The single biggest source of Kubernetes waste is over-requested resources. Developers set `requests: cpu: "2"` during a panic and never revisit it.

### Identifying Waste

```bash
# Find pods where actual CPU usage is far below requests
# Using kubectl top (requires metrics-server)
kubectl top pods -A --sort-by=cpu

# Compare requests vs actual usage for a namespace
kubectl top pods -n production
kubectl get pods -n production -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].resources.requests.cpu}{"\t"}{.spec.containers[0].resources.requests.memory}{"\n"}{end}'
```

### Right-Sizing Workflow

```
RESOURCE RIGHT-SIZING WORKFLOW
════════════════════════════════════════════════════════════════════

Step 1: MEASURE (1-2 weeks of data)
─────────────────────────────────────────────────────────
  • Collect CPU/memory usage via Prometheus
  • Record P50, P95, P99, and MAX usage per container
  • Note: weekend vs weekday patterns matter

Step 2: ANALYZE
─────────────────────────────────────────────────────────
  • Compare requests vs P95 actual usage
  • Flag containers where requests > 2x P95 usage
  • Identify containers with NO requests set (dangerous!)

Step 3: RECOMMEND
─────────────────────────────────────────────────────────
  • Set requests = P95 usage + 20% buffer
  • Set limits  = P99 usage + 50% buffer (or no limit for CPU)
  • Exception: latency-sensitive services get more headroom

Step 4: APPLY AND MONITOR
─────────────────────────────────────────────────────────
  • Roll out changes gradually (one service at a time)
  • Watch for OOMKills (memory too tight)
  • Watch for CPU throttling (CPU limit too tight)
  • Re-evaluate monthly
```

### Example: Before and After

```yaml
# BEFORE: Developer guessed high during an outage
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: user-api
        resources:
          requests:
            cpu: "2"         # Actual P95 usage: 200m
            memory: "2Gi"    # Actual P95 usage: 350Mi
          limits:
            cpu: "4"
            memory: "4Gi"
        # Cost: 3 replicas x 2 CPU = 6 CPU requested
        # Waste: 3 x (2000m - 200m) = 5400m CPU wasted

---
# AFTER: Right-sized based on 2 weeks of metrics
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: user-api
        resources:
          requests:
            cpu: "250m"      # P95 (200m) + 20% buffer
            memory: "512Mi"  # P95 (350Mi) + ~45% buffer
          limits:
            memory: "768Mi"  # P99 + headroom (no CPU limit)
        # Cost: 3 replicas x 250m = 750m CPU requested
        # Savings: 6000m - 750m = 5250m CPU freed = ~87% reduction
```

---

## Spot and Preemptible Strategies

Spot instances (AWS), preemptible VMs (GCP), and spot VMs (Azure) offer 60-90% discounts but can be reclaimed with short notice.

### What Can Run on Spot

```
SPOT INSTANCE DECISION TREE
════════════════════════════════════════════════════════════════════

Is the workload stateless?
├── YES ──▶ Is it fault-tolerant (handles restarts)?
│           ├── YES ──▶ SPOT: Great candidate
│           │           Examples: web servers, API pods,
│           │           batch jobs, CI/CD runners
│           └── NO  ──▶ FIX FIRST: Add graceful shutdown,
│                       health checks, then use spot
│
└── NO (stateful) ──▶ Does it use replicated storage?
                      ├── YES ──▶ SPOT: Maybe (careful testing)
                      │           Examples: Kafka brokers,
                      │           Elasticsearch data nodes
                      └── NO  ──▶ ON-DEMAND: Keep it safe
                                  Examples: single-replica DBs,
                                  etcd, controllers
```

### Spot-Friendly Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: batch-processor
spec:
  replicas: 5
  template:
    metadata:
      labels:
        app: batch-processor
        spot-eligible: "true"
    spec:
      # Tolerate spot node taints
      tolerations:
      - key: "karpenter.sh/capacity-type"
        operator: "Equal"
        value: "spot"
        effect: "NoSchedule"
      # Prefer spot but allow on-demand fallback
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 90
            preference:
              matchExpressions:
              - key: karpenter.sh/capacity-type
                operator: In
                values: ["spot"]
      # Spread across AZs for spot diversity
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: batch-processor
      containers:
      - name: processor
        image: myapp/batch-processor:v2
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
        # Handle graceful termination on spot reclamation
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15 && kill -SIGTERM 1"]
      terminationGracePeriodSeconds: 30
```

See [Module 6.1: Karpenter](module-6.1-karpenter.md) for configuring NodePools that mix spot and on-demand capacity automatically.

---

## Idle Resource Cleanup

Forgotten resources are silent cost killers. A load-test namespace, an orphaned PVC, a scaled-up deployment nobody scaled back down.

### Common Idle Resources

```bash
# Find namespaces with no running pods (potential cleanup targets)
for ns in $(kubectl get ns -o jsonpath='{.items[*].metadata.name}'); do
  pod_count=$(kubectl get pods -n "$ns" --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
  if [ "$pod_count" -eq 0 ]; then
    echo "EMPTY NAMESPACE: $ns"
  fi
done

# Find PVCs not mounted by any pod
kubectl get pvc -A -o json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for pvc in data['items']:
    ns = pvc['metadata']['namespace']
    name = pvc['metadata']['name']
    phase = pvc['status'].get('phase', 'unknown')
    if phase == 'Bound':
        print(f'CHECK: {ns}/{name} - bound but verify if pod exists')
"

# Find deployments scaled to 0 for more than 7 days (stale)
kubectl get deployments -A -o json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for d in data['items']:
    if d['spec'].get('replicas', 1) == 0:
        ns = d['metadata']['namespace']
        name = d['metadata']['name']
        print(f'SCALED TO ZERO: {ns}/{name}')
"

# Find LoadBalancer services (each one costs ~$18/month on AWS)
kubectl get svc -A --field-selector spec.type=LoadBalancer
```

### Scheduled Non-Production Shutdown

```yaml
# CronJob to scale down staging at 7 PM and scale up at 8 AM
# Use kube-downscaler or a simple script
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-down-staging
  namespace: staging
spec:
  schedule: "0 19 * * 1-5"  # 7 PM weekdays
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: scaler
          containers:
          - name: scaler
            image: bitnami/kubectl:1.31
            command:
            - /bin/sh
            - -c
            - |
              kubectl get deployments -n staging -o name | \
              xargs -I{} kubectl scale {} --replicas=0 -n staging
          restartPolicy: OnFailure
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-up-staging
  namespace: staging
spec:
  schedule: "0 8 * * 1-5"  # 8 AM weekdays
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: scaler
          containers:
          - name: scaler
            image: bitnami/kubectl:1.31
            command:
            - /bin/sh
            - -c
            - |
              kubectl get deployments -n staging -o name | \
              xargs -I{} kubectl scale {} --replicas=1 -n staging
          restartPolicy: OnFailure
```

Shutting down non-production environments outside business hours saves roughly **65%** on those environments (13 off-hours out of 24, plus weekends).

---

## Cost-Aware Architecture

Namespace quotas and LimitRanges are your guardrails. They prevent cost surprises by capping what teams can consume.

### ResourceQuotas for Team Budgets

```yaml
# Each team namespace gets a compute budget
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-alpha-quota
  namespace: team-alpha
spec:
  hard:
    requests.cpu: "20"         # Max 20 CPU across all pods
    requests.memory: "40Gi"    # Max 40 GB memory
    limits.cpu: "40"
    limits.memory: "80Gi"
    persistentvolumeclaims: "10"  # Max 10 PVCs
    services.loadbalancers: "2"   # Max 2 LBs (~$36/month cap)
    pods: "100"                   # Max 100 pods
```

### LimitRanges for Sane Defaults

```yaml
# Prevent individual pods from being too big or having no requests
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: team-alpha
spec:
  limits:
  - type: Container
    default:           # Applied if no limits specified
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:    # Applied if no requests specified
      cpu: "100m"
      memory: "128Mi"
    max:               # Hard ceiling per container
      cpu: "4"
      memory: "8Gi"
    min:               # Floor (prevents tiny requests that waste scheduling)
      cpu: "50m"
      memory: "64Mi"
```

### Cost Allocation Labels

Apply labels consistently so OpenCost can attribute costs to teams.

```yaml
# Enforce these labels on all workloads via admission policy
metadata:
  labels:
    team: "alpha"              # Which team owns this
    environment: "production"  # prod, staging, dev
    cost-center: "engineering" # For finance reporting
    app: "user-api"            # Which application
```

---

## Comparison: Cost Monitoring Tools

| Feature | OpenCost | Kubecost | Cloud-Native (AWS Cost Explorer, GCP Billing) |
|---------|----------|----------|------------------------------------------------|
| **License** | Free, open-source (CNCF) | Free tier + paid enterprise | Included with cloud |
| **Kubernetes-aware** | Yes, pod/namespace level | Yes, pod/namespace level | No, only instance level |
| **Real-time** | Yes | Yes | Delayed (hours to days) |
| **Multi-cluster** | Community-supported | Enterprise feature | Yes |
| **Recommendations** | Basic (via metrics) | Built-in right-sizing | Basic (instance-level) |
| **Alerting** | Via Prometheus rules | Built-in | Via cloud alerts |
| **Idle cost tracking** | Yes | Yes | No |
| **Showback/chargeback** | API-driven | Built-in dashboards | Tag-based only |
| **Best for** | Teams wanting free, extensible cost visibility | Teams wanting turnkey solution | Finance teams needing invoice-level data |

**Recommendation**: Start with OpenCost. It is free and gives you 80% of what you need. If you outgrow it and need built-in recommendations, alerts, and multi-cluster views, evaluate Kubecost Enterprise.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No resource requests set | Pods look "free" to schedulers, waste is invisible | Enforce requests via LimitRange and admission policies |
| Right-sizing based on 1 day of data | Misses weekly traffic patterns, batch jobs | Use at least 7-14 days of metrics for right-sizing |
| Running spot for stateful singletons | Data loss or extended downtime on reclamation | Reserve on-demand for databases and controllers |
| Ignoring idle namespaces | Forgotten environments burn money 24/7 | Audit namespaces monthly, schedule non-prod shutdowns |
| Setting CPU limits too tight | Causes throttling, increases latency | Set memory limits (OOMKill is clear), skip CPU limits or set them generous |
| No cost labels on workloads | Cannot attribute spend to teams | Enforce labels via OPA/Kyverno admission policies |
| Optimizing before measuring | Guessing leads to wrong priorities | Install OpenCost first, measure for a week, then optimize |

---

## Quiz

### Question 1
What are the three main cost categories in a Kubernetes cluster, and which is typically the largest?

<details>
<summary>Show Answer</summary>

The three main categories are:

1. **Compute** (60-70%) - Node instance costs based on CPU, memory, and GPU
2. **Storage** (15-25%) - PersistentVolumes, snapshots, and backups
3. **Network** (5-15%) - Load balancers, NAT gateways, cross-AZ traffic

Compute is almost always the largest. This is why right-sizing resource requests and using spot instances have the biggest impact on cost reduction.

</details>

### Question 2
Why should you set resource requests based on P95 usage rather than average usage?

<details>
<summary>Show Answer</summary>

Average usage hides traffic spikes. If your service averages 100m CPU but hits 400m during peak hours, setting requests to 100m means:

- The scheduler places the pod on a node assuming it only needs 100m
- During peaks, the pod competes for CPU with other pods
- Performance degrades or the pod gets throttled

P95 usage captures the realistic high-water mark while ignoring rare outlier spikes. Adding a 20% buffer on top of P95 gives you headroom for organic growth without massively over-provisioning.

P99 or MAX is too aggressive for requests (wastes capacity for rare events) but reasonable for limits.

</details>

### Question 3
A team has 10 LoadBalancer-type Services in their namespace. Why is this a cost concern, and what would you recommend?

<details>
<summary>Show Answer</summary>

Each LoadBalancer Service provisions a cloud load balancer. On AWS, each ALB/NLB costs approximately $18-25/month in base charges, plus data processing fees. Ten load balancers cost $180-250/month just in base fees.

**Recommendation**: Use a single Ingress controller (like NGINX Ingress or AWS ALB Ingress Controller) that routes traffic to multiple services through one load balancer. This consolidates 10 load balancers into 1, saving $160-225/month.

Also set `services.loadbalancers` in a ResourceQuota to prevent this from happening again.

</details>

### Question 4
Why is OpenCost more useful than AWS Cost Explorer for Kubernetes cost management?

<details>
<summary>Show Answer</summary>

AWS Cost Explorer sees EC2 instances. OpenCost sees pods, namespaces, and labels.

**Example**: A single m5.4xlarge node ($0.768/hour) runs pods from three teams. AWS Cost Explorer shows one $553/month line item tagged to "EKS." It cannot tell you that Team Alpha uses $200, Team Beta uses $150, and $203 is idle waste.

OpenCost breaks down that same node's cost by:
- **Namespace**: team-alpha ($200), team-beta ($150)
- **Idle**: $203 of unused capacity
- **Label**: cost-center=engineering ($350), cost-center=data ($50)

This granularity is essential for chargeback (billing teams for their usage) and identifying which specific workloads to optimize.

</details>

---

## Hands-On Exercise

### Objective

Install OpenCost, identify waste, and apply cost-saving configurations.

### Environment Setup

```bash
# Start a local cluster with metrics-server
# (kind or minikube)
kind create cluster --name finops-lab

# Install metrics-server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
# For kind, patch metrics-server to work without TLS
kubectl patch deployment metrics-server -n kube-system --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'

# Install Prometheus (OpenCost dependency)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring --create-namespace \
  --set server.persistentVolume.enabled=false \
  --set alertmanager.enabled=false

# Install OpenCost
helm repo add opencost https://opencost.github.io/opencost-helm-chart
helm install opencost opencost/opencost \
  --namespace opencost --create-namespace \
  --set opencost.prometheus.internal.enabled=false \
  --set opencost.prometheus.external.url="http://prometheus-server.monitoring.svc:80" \
  --set opencost.ui.enabled=true
```

### Tasks

1. **Create two team namespaces with quotas**:
   ```bash
   # Create namespaces
   kubectl create namespace team-alpha
   kubectl create namespace team-beta

   # Apply ResourceQuota to team-alpha
   kubectl apply -f - <<EOF
   apiVersion: v1
   kind: ResourceQuota
   metadata:
     name: compute-quota
     namespace: team-alpha
   spec:
     hard:
       requests.cpu: "4"
       requests.memory: "4Gi"
       limits.cpu: "8"
       limits.memory: "8Gi"
       pods: "20"
   EOF

   # Apply LimitRange to team-alpha
   kubectl apply -f - <<EOF
   apiVersion: v1
   kind: LimitRange
   metadata:
     name: default-limits
     namespace: team-alpha
   spec:
     limits:
     - type: Container
       default:
         cpu: "200m"
         memory: "256Mi"
       defaultRequest:
         cpu: "100m"
         memory: "128Mi"
   EOF
   ```

2. **Deploy workloads with deliberate over-provisioning**:
   ```bash
   # Over-provisioned deployment (the "waste")
   kubectl apply -f - <<EOF
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: wasteful-api
     namespace: team-alpha
     labels:
       team: alpha
       app: wasteful-api
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: wasteful-api
     template:
       metadata:
         labels:
           app: wasteful-api
           team: alpha
       spec:
         containers:
         - name: nginx
           image: nginx:1.27
           resources:
             requests:
               cpu: "500m"
               memory: "512Mi"
             limits:
               cpu: "1"
               memory: "1Gi"
   EOF

   # Right-sized deployment (the "good example")
   kubectl apply -f - <<EOF
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: efficient-api
     namespace: team-beta
     labels:
       team: beta
       app: efficient-api
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: efficient-api
     template:
       metadata:
         labels:
           app: efficient-api
           team: beta
       spec:
         containers:
         - name: nginx
           image: nginx:1.27
           resources:
             requests:
               cpu: "50m"
               memory: "64Mi"
             limits:
               memory: "128Mi"
   EOF
   ```

3. **Compare resource usage vs requests**:
   ```bash
   # Wait 2 minutes for metrics to populate
   kubectl top pods -n team-alpha
   kubectl top pods -n team-beta

   # Compare: wasteful-api requests 500m CPU but uses ~1-2m
   # efficient-api requests 50m CPU and uses ~1-2m
   ```

4. **Check OpenCost allocation**:
   ```bash
   kubectl port-forward -n opencost svc/opencost 9090:9090 &
   # Open http://localhost:9090
   # Navigate to see cost breakdown by namespace
   ```

5. **Verify quota enforcement**:
   ```bash
   # Try to exceed the quota
   kubectl apply -f - <<EOF
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: quota-buster
     namespace: team-alpha
   spec:
     replicas: 10
     selector:
       matchLabels:
         app: quota-buster
     template:
       metadata:
         labels:
           app: quota-buster
       spec:
         containers:
         - name: nginx
           image: nginx:1.27
           resources:
             requests:
               cpu: "500m"
               memory: "512Mi"
   EOF

   # Check how many pods actually scheduled
   kubectl get pods -n team-alpha
   kubectl describe resourcequota compute-quota -n team-alpha
   # The quota should prevent all 10 replicas from running
   ```

### Success Criteria

- [ ] OpenCost is running and accessible on port 9090
- [ ] Two namespaces exist with different resource efficiency profiles
- [ ] `kubectl top pods` shows the wasteful-api uses far less CPU than it requests
- [ ] ResourceQuota prevents team-alpha from exceeding their compute budget
- [ ] LimitRange applies default requests to pods that do not specify them
- [ ] You can articulate why wasteful-api should be right-sized to ~50-100m CPU

### Cleanup

```bash
kind delete cluster --name finops-lab
```

---

## Further Reading

- [OpenCost Documentation](https://www.opencost.io/docs/)
- [FinOps Foundation - Kubernetes Cost Optimization](https://www.finops.org/)
- [Kubecost Documentation](https://docs.kubecost.com/)
- [AWS Spot Instance Best Practices](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-best-practices.html)

---

## Next Module

You have completed the Scaling and Reliability Toolkit. Continue to the [Platforms Toolkit](../platforms/README.md) to learn about building internal developer platforms with Backstage, Crossplane, and more.

**Related modules**:
- [Module 6.1: Karpenter](module-6.1-karpenter.md) — Configure spot instances and node consolidation that directly reduce compute costs
- [Module 6.3: Velero](module-6.3-velero.md) — Backup strategies that affect storage costs

---

*"You can't optimize what you can't see. Make every dollar visible, and waste has nowhere to hide."*
