---
title: "Module 8.8: Cloud Cost Optimization (Advanced)"
slug: cloud/advanced-operations/module-8.8-cloud-cost
sidebar:
  order: 9
---
> **Complexity**: `[MEDIUM]`
>
> **Time to Complete**: 2 hours
>
> **Prerequisites**: Basic understanding of Kubernetes resource requests/limits and cloud billing concepts
>
> **Track**: Advanced Cloud Operations

---

## Why This Module Matters

**Q1 2024. A Series C startup. $8 million annual cloud spend.**

The CFO called an all-hands meeting. Cloud costs had grown 340% year-over-year while revenue grew 180%. The engineering team had no visibility into which teams, services, or features drove the cost. The finance team's cloud bill showed 12,000 line items per month. When the VP of Engineering was asked "how much does the recommendation engine cost?", the honest answer was "we have no idea."

Three months of forensic analysis revealed: 38% of EC2 instances were running at under 10% CPU utilization. The company was paying on-demand prices for workloads that ran 24/7 (perfect candidates for reserved instances or savings plans). Twenty-six EBS volumes were orphaned -- detached from any instance but still accruing charges. A development EKS cluster that was "temporary" had been running for 14 months. And the biggest surprise: cross-AZ data transfer for their Kubernetes pods cost $14,000 per month -- a line item nobody had ever noticed because it was buried in the EC2 data transfer category.

After implementing the techniques in this module -- right-sizing, committed use discounts, Kubecost for allocation, VPA for resource optimization, and spot instances for non-critical workloads -- they reduced cloud spend by 42% ($3.36 million annually) without changing a single line of application code.

---

## The Four Pillars of Cloud Cost Optimization

```
COST OPTIMIZATION FRAMEWORK
════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────┐
  │                    COST OPTIMIZATION                      │
  │                                                          │
  │  1. VISIBILITY         2. RIGHT-SIZING                   │
  │  "Where does the       "Are resources matched             │
  │   money go?"            to actual usage?"                 │
  │                                                          │
  │  - Cost allocation     - CPU/memory utilization          │
  │  - Showback/chargeback - VPA recommendations             │
  │  - Kubecost/OpenCost   - Node right-sizing               │
  │                                                          │
  │  3. RATE OPTIMIZATION  4. ARCHITECTURAL                  │
  │  "Are we paying the    "Can we change HOW                │
  │   best price?"          we run things?"                   │
  │                                                          │
  │  - Savings Plans/CUDs  - Spot/preemptible instances      │
  │  - Reserved Instances  - Topology-aware routing           │
  │  - Committed Use       - Ephemeral environments          │
  │                        - Orphaned resource cleanup       │
  └──────────────────────────────────────────────────────────┘

  Implementation order: 1 -> 2 -> 3 -> 4
  You can't optimize what you can't see.
```

---

## Pillar 1: Visibility with Kubecost and OpenCost

Kubernetes makes cost allocation hard because workloads share nodes. If three teams run pods on the same node, who pays for that node?

### Kubecost Architecture

```
KUBECOST COST ALLOCATION
════════════════════════════════════════════════════════════════

  Cloud Billing API              Kubernetes Metrics
  (AWS CUR / GCP Billing /      (Prometheus / metrics-server)
   Azure Cost Export)
       │                              │
       ▼                              ▼
  ┌──────────────────────────────────────────┐
  │              Kubecost                     │
  │                                          │
  │  Cost allocation engine:                 │
  │  1. Get actual cloud cost per node       │
  │  2. Get resource usage per pod per node  │
  │  3. Allocate node cost to pods based on  │
  │     resource consumption                 │
  │  4. Aggregate by namespace, label, team  │
  │                                          │
  │  Example:                                │
  │  Node cost: $100/day (m7i.xlarge)        │
  │  Pod A uses 40% CPU, 30% memory         │
  │  Pod B uses 20% CPU, 50% memory         │
  │  Pod C uses 10% CPU, 10% memory         │
  │                                          │
  │  Allocation (weighted average):          │
  │  Pod A: $100 * (0.4+0.3)/2 = $35/day    │
  │  Pod B: $100 * (0.2+0.5)/2 = $35/day    │
  │  Pod C: $100 * (0.1+0.1)/2 = $10/day    │
  │  Idle: $100 - $35 - $35 - $10 = $20/day │
  └──────────────────────────────────────────┘
```

### Installing Kubecost

```bash
# Install Kubecost via Helm
helm repo add kubecost https://kubecost.github.io/cost-analyzer/
helm repo update

helm install kubecost kubecost/cost-analyzer \
  --namespace kubecost \
  --create-namespace \
  --set kubecostToken="YOUR_TOKEN" \
  --set prometheus.server.retention="30d" \
  --set kubecostProductConfigs.clusterName="prod-us-east-1"

# For multi-cluster, install the agent on each cluster
# and point to a central Kubecost instance
helm install kubecost kubecost/cost-analyzer \
  --namespace kubecost \
  --create-namespace \
  --set agent.enabled=true \
  --set kubecostProductConfigs.clusterName="prod-eu-west-1" \
  --set federatedETL.primaryCluster="https://kubecost.prod-us-east-1.internal"

# Access the Kubecost UI
kubectl port-forward -n kubecost svc/kubecost-cost-analyzer 9090:9090
```

### OpenCost: The Open-Source Alternative

```bash
# OpenCost is CNCF-supported and free
helm repo add opencost https://opencost.github.io/opencost-helm-chart
helm repo update

helm install opencost opencost/opencost \
  --namespace opencost \
  --create-namespace \
  --set opencost.exporter.defaultClusterId="prod-us-east-1" \
  --set opencost.ui.enabled=true

# Query the API for cost allocation
curl http://localhost:9003/allocation/compute \
  --data-urlencode "window=7d" \
  --data-urlencode "aggregate=namespace" \
  --data-urlencode "accumulate=true" | jq '.data[0]'
```

### Multi-Tenant Cost Allocation

```yaml
# Label-based cost allocation strategy
# Every workload MUST have these labels for cost tracking
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recommendation-engine
  namespace: ml-platform
  labels:
    team: ml-engineering
    cost-center: CC-4200
    product: recommendations
    environment: production
spec:
  template:
    metadata:
      labels:
        team: ml-engineering
        cost-center: CC-4200
        product: recommendations
        environment: production
    spec:
      containers:
        - name: engine
          image: company/rec-engine:v2.1.0
          resources:
            requests:
              cpu: "2"
              memory: "4Gi"
            limits:
              cpu: "4"
              memory: "8Gi"
```

```bash
# Enforce required labels with Kyverno
kubectl apply -f - <<'EOF'
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-cost-labels
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-cost-labels
      match:
        any:
          - resources:
              kinds:
                - Deployment
                - StatefulSet
                - Job
      validate:
        message: "All workloads must have 'team', 'cost-center', and 'environment' labels"
        pattern:
          metadata:
            labels:
              team: "?*"
              cost-center: "?*"
              environment: "production|staging|development"
EOF
```

---

## Pillar 2: Right-Sizing with VPA and HPA

The most common waste pattern in Kubernetes: developers set resource requests based on guesswork, then never revisit them.

### Vertical Pod Autoscaler (VPA) for Right-Sizing

```
VPA RIGHT-SIZING EXAMPLE
════════════════════════════════════════════════════════════════

  Before VPA analysis:                After VPA recommendation:
  ┌──────────────────────┐           ┌──────────────────────┐
  │  Request: 4 CPU      │           │  Request: 800m CPU   │
  │  ████                │           │  ██                  │
  │  ████                │           │  Actual usage: 600m  │
  │  ████                │           │                      │
  │  Actual: 600m        │           │  Request: 2Gi mem    │
  │                      │           │  ████████            │
  │  Request: 8Gi mem    │           │  Actual usage: 1.5Gi │
  │  ████████████████    │           │                      │
  │  Actual: 1.5Gi      │           │  Savings: 80% CPU    │
  │                      │           │           75% memory │
  └──────────────────────┘           └──────────────────────┘

  Over-provisioning wastes money because K8s schedules based on
  REQUESTS, not actual usage. A pod requesting 4 CPU blocks
  4 CPU from being used by other pods, even if it only uses 600m.
```

```yaml
# VPA in recommendation mode (safe -- doesn't change anything)
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: recommendation-engine-vpa
  namespace: ml-platform
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: recommendation-engine
  updatePolicy:
    updateMode: "Off"  # Only recommend, don't auto-apply
  resourcePolicy:
    containerPolicies:
      - containerName: engine
        minAllowed:
          cpu: "100m"
          memory: "256Mi"
        maxAllowed:
          cpu: "8"
          memory: "16Gi"
```

```bash
# Check VPA recommendations
k get vpa recommendation-engine-vpa -n ml-platform -o yaml

# The recommendation section shows:
# - lowerBound: minimum safe resources
# - target: recommended resources
# - upperBound: maximum expected resources
# - uncappedTarget: ideal without min/max constraints

# Example output:
# recommendation:
#   containerRecommendations:
#     - containerName: engine
#       lowerBound:
#         cpu: 500m
#         memory: 1Gi
#       target:
#         cpu: 800m
#         memory: 2Gi
#       upperBound:
#         cpu: 1500m
#         memory: 4Gi
```

### HPA for Cost-Efficient Scaling

```yaml
# HPA with both CPU and custom metrics
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-server-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 2
  maxReplicas: 20
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
      policies:
        - type: Percent
          value: 25      # Scale down max 25% at a time
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
        - type: Percent
          value: 100     # Can double immediately under load
          periodSeconds: 60
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70  # Target 70% CPU utilization
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 75
```

---

## Pillar 3: Rate Optimization

### Savings Plans and Committed Use Discounts

```
RATE OPTIMIZATION COMPARISON
════════════════════════════════════════════════════════════════

AWS:
  On-Demand:          $0.192/hr (m7i.xlarge)
  1yr Savings Plan:   $0.121/hr (-37%)
  3yr Savings Plan:   $0.077/hr (-60%)
  Spot:               $0.058/hr (-70%, but can be interrupted)

GCP:
  On-Demand:          $0.189/hr (n2-standard-4)
  1yr CUD:            $0.119/hr (-37%)
  3yr CUD:            $0.085/hr (-55%)
  Spot:               $0.057/hr (-70%)
  SUDs (automatic):   $0.151/hr (-20%, auto-applied after 25% month)

Azure:
  On-Demand:          $0.192/hr (D4s v5)
  1yr Reserved:       $0.124/hr (-35%)
  3yr Reserved:       $0.079/hr (-59%)
  Spot:               ~$0.038/hr (-80%, varies)

  STRATEGY:
  ┌─────────────────────────────────────────────────────┐
  │  Baseline (24/7 workloads)    → Savings Plan / CUD  │
  │  Bursty (predictable peaks)   → On-demand           │
  │  Fault-tolerant (batch, CI)   → Spot instances       │
  │  Development                  → Spot + auto-shutdown │
  └─────────────────────────────────────────────────────┘
```

### Calculating Your Savings Plan Commitment

```bash
# AWS: Analyze your usage to determine the right commitment
aws ce get-savings-plans-purchase-recommendation \
  --savings-plans-type COMPUTE_SAVINGS_PLANS \
  --term-in-years ONE_YEAR \
  --payment-option NO_UPFRONT \
  --lookback-period-in-days SIXTY_DAYS \
  --output json | jq '.SavingsPlansPurchaseRecommendation'

# The output tells you:
# - Recommended hourly commitment (e.g., $12.50/hr)
# - Estimated monthly savings (e.g., $2,800/month)
# - Coverage percentage (e.g., 72% of on-demand usage)

# GCP: Analyze committed use
gcloud billing accounts describe BILLING_ACCOUNT_ID --format=json
# Use the GCP Billing Console > Committed use discounts > Analysis
```

---

## Pillar 4: Spot Instance Lifecycle

Spot instances (AWS) / Preemptible VMs (GCP) / Spot VMs (Azure) offer 60-90% discounts but can be interrupted with short notice. Kubernetes makes them practical by handling rescheduling automatically.

### Spot-Friendly Node Groups

```yaml
# EKS managed node group with Spot instances
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: prod-cluster
  region: us-east-1
nodeGroups:
  # On-demand for critical workloads
  - name: on-demand-critical
    instanceType: m7i.xlarge
    desiredCapacity: 3
    minSize: 3
    maxSize: 6
    labels:
      node-type: on-demand
      workload-class: critical
    taints:
      - key: workload-class
        value: critical
        effect: NoSchedule

  # Spot for non-critical workloads
  - name: spot-general
    instanceTypes:
      - m7i.xlarge
      - m6i.xlarge
      - m5.xlarge
      - c7i.xlarge    # Diversify instance types
    spot: true
    desiredCapacity: 5
    minSize: 2
    maxSize: 15
    labels:
      node-type: spot
      workload-class: general
```

### Pod Scheduling for Spot

```yaml
# Non-critical workload: prefers Spot, tolerates interruption
apiVersion: apps/v1
kind: Deployment
metadata:
  name: batch-processor
  namespace: data-pipeline
spec:
  replicas: 8
  selector:
    matchLabels:
      app: batch-processor
  template:
    metadata:
      labels:
        app: batch-processor
    spec:
      # Prefer Spot nodes
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 90
              preference:
                matchExpressions:
                  - key: node-type
                    operator: In
                    values:
                      - spot
      # Tolerate Spot taints
      tolerations:
        - key: "kubernetes.io/spot"
          operator: "Exists"
          effect: "NoSchedule"
      # Handle graceful shutdown on Spot interruption
      terminationGracePeriodSeconds: 120
      containers:
        - name: processor
          image: company/batch-processor:v1.8.0
          resources:
            requests:
              cpu: "1"
              memory: "2Gi"
          # Checkpoint progress periodically so interruption loses minimal work
          env:
            - name: CHECKPOINT_INTERVAL_SECONDS
              value: "30"
```

### Spot Interruption Handling

```yaml
# AWS Node Termination Handler (NTH)
# Detects Spot interruption notices and gracefully drains nodes
# Install via Helm:
# helm install aws-node-termination-handler \
#   eks/aws-node-termination-handler \
#   --namespace kube-system

# Karpenter: Automatically replaces interrupted Spot nodes
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: spot-pool
spec:
  template:
    spec:
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot"]
        - key: node.kubernetes.io/instance-type
          operator: In
          values:
            - m7i.xlarge
            - m7i.2xlarge
            - m6i.xlarge
            - m6i.2xlarge
            - c7i.xlarge
            - r7i.xlarge
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
  disruption:
    consolidationPolicy: WhenEmpty
    consolidateAfter: 60s
  limits:
    cpu: "100"
    memory: "400Gi"
```

---

## Orphaned Resource Cleanup

Orphaned resources are cloud resources that are no longer attached to any active workload but continue accruing charges. They are the silent budget killer.

### Common Orphaned Resources

| Resource | How It Gets Orphaned | Monthly Cost (typical) |
|---|---|---|
| Unattached EBS volumes | PVC deleted, PV not reclaimed | $8-$80 per volume |
| Unused Elastic IPs | Service deleted, EIP not released | $3.65 each |
| Old EBS snapshots | Backup policy with no expiry | $0.05/GB |
| Idle load balancers | Service deleted, LB remains | $16-$25 each |
| Stopped EC2 instances | "Paused" but never terminated | EBS costs continue |
| Orphaned NAT Gateways | VPC deleted, NAT GW remains | $32 each |
| Unused RDS snapshots | Manual snapshots accumulated | $0.095/GB |

### Automated Cleanup

```bash
# Find unattached EBS volumes
aws ec2 describe-volumes \
  --filters Name=status,Values=available \
  --query 'Volumes[*].{ID:VolumeId,Size:Size,Created:CreateTime,AZ:AvailabilityZone}' \
  --output table

# Find unused Elastic IPs
aws ec2 describe-addresses \
  --query 'Addresses[?AssociationId==null].{IP:PublicIp,AllocID:AllocationId}' \
  --output table

# Find load balancers with no targets
for LB_ARN in $(aws elbv2 describe-load-balancers --query 'LoadBalancers[*].LoadBalancerArn' --output text); do
  TG_COUNT=$(aws elbv2 describe-target-groups \
    --load-balancer-arn $LB_ARN \
    --query 'length(TargetGroups)' --output text)
  if [ "$TG_COUNT" = "0" ]; then
    LB_NAME=$(aws elbv2 describe-load-balancers \
      --load-balancer-arns $LB_ARN \
      --query 'LoadBalancers[0].LoadBalancerName' --output text)
    echo "ORPHANED LB: $LB_NAME ($LB_ARN)"
  fi
done

# Find EBS snapshots older than 90 days
NINETY_DAYS_AGO=$(date -u -v-90d +%Y-%m-%dT%H:%M:%S 2>/dev/null || date -u -d '90 days ago' +%Y-%m-%dT%H:%M:%S)
aws ec2 describe-snapshots \
  --owner-ids self \
  --query "Snapshots[?StartTime<='${NINETY_DAYS_AGO}'].{ID:SnapshotId,Size:VolumeSize,Date:StartTime}" \
  --output table
```

```yaml
# CronJob to detect and report orphaned resources
apiVersion: batch/v1
kind: CronJob
metadata:
  name: orphan-detector
  namespace: finops
spec:
  schedule: "0 8 * * 1"  # Every Monday at 8 AM
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: orphan-detector
          containers:
            - name: detector
              image: company/orphan-detector:v1.2.0
              env:
                - name: SLACK_WEBHOOK
                  valueFrom:
                    secretKeyRef:
                      name: slack-webhook
                      key: url
                - name: STALE_THRESHOLD_DAYS
                  value: "30"
              command:
                - /bin/sh
                - -c
                - |
                  echo "Scanning for orphaned resources..."
                  # Detect unattached volumes
                  VOLUMES=$(aws ec2 describe-volumes --filters Name=status,Values=available \
                    --query 'length(Volumes)' --output text)
                  # Detect unused EIPs
                  EIPS=$(aws ec2 describe-addresses \
                    --query 'length(Addresses[?AssociationId==null])' --output text)
                  # Send report to Slack
                  curl -X POST "$SLACK_WEBHOOK" -H 'Content-type: application/json' \
                    --data "{\"text\":\"Orphan Report: $VOLUMES unattached volumes, $EIPS unused EIPs\"}"
          restartPolicy: OnFailure
```

---

## Did You Know?

1. **Kubernetes clusters typically run at 30-50% resource utilization** according to data from Kubecost across thousands of clusters. This means 50-70% of compute spend is wasted on idle resources. The primary cause is over-provisioned resource requests: developers set CPU and memory requests based on worst-case scenarios and never revisit them. VPA in recommendation mode can identify right-sizing opportunities without any risk.

2. **AWS Spot instances have been interrupted less than 5% of the time** for the most popular instance types (m5.xlarge, m6i.xlarge) in US regions, based on the AWS Spot Instance Advisor. The interruption rate varies dramatically by instance type and region: r5.8xlarge in ap-southeast-1 might see 15-20% interruption rate, while m7i.xlarge in us-east-1 sees under 3%. Diversifying across instance types and AZs is the key to reliable Spot usage.

3. **Cross-AZ data transfer is one of the top 5 cost categories** for most Kubernetes deployments on AWS. A company running 20 microservices with 100 pods across 3 AZs can easily spend $2,000-$5,000/month on cross-AZ traffic alone. GCP made cross-zone traffic free in 2022. AWS has not followed suit, making topology-aware routing a significant cost optimization lever for AWS-based Kubernetes deployments.

4. **OpenCost became a CNCF Sandbox project in 2022** and reached Incubation status in 2024. It was originally developed by Kubecost as the open-source core of their commercial product. The CNCF adoption signaled that Kubernetes cost management was becoming a first-class concern alongside security and observability. OpenCost's cost allocation API is now integrated into several commercial FinOps platforms.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Setting resource requests to match limits | "Same value means guaranteed QoS" | Requests should reflect typical usage, limits reflect peak. VPA recommendations help find the right values. Over-requesting wastes money. |
| Buying Savings Plans based on current usage | "We're using $10K/month now, commit to $10K" | Usage fluctuates. Commit to 60-70% of your average usage. The rest stays on-demand for flexibility. Over-commitment is worse than no commitment. |
| Running dev/staging clusters 24/7 | "Someone might need them on weekends" | Implement auto-shutdown for non-production clusters. Scale to zero outside business hours. A $3,000/month staging cluster running only business hours costs $900. |
| Not diversifying Spot instance types | "We need m7i.xlarge specifically" | Spot pools with a single instance type have higher interruption rates. Specify 4-6 compatible instance types. Karpenter handles this automatically. |
| Ignoring namespace-level resource quotas | "Trust developers to be reasonable" | Without quotas, one team can consume the entire cluster. Set ResourceQuotas per namespace based on team budgets. |
| No cost alerts or budgets | "We check the bill monthly" | By the time you see the monthly bill, the damage is done. Set budget alerts at 50%, 80%, and 100% thresholds for each account. |
| Deleting Spot nodes during business hours | "Karpenter consolidated idle nodes" | Configure consolidation windows to avoid Spot node replacement during peak hours. Use `disruption.consolidateAfter` to delay. |
| Not accounting for EBS costs separately from EC2 | "Compute is our biggest cost" | EBS volumes persist after pods are deleted. Monitor PVC lifecycle and implement `reclaimPolicy: Delete` for non-production volumes. |

---

## Quiz

<details>
<summary>1. Why can't you simply look at the cloud bill to determine per-team Kubernetes costs?</summary>

Cloud bills show costs per resource (EC2 instances, EBS volumes, load balancers), not per workload. In Kubernetes, multiple teams' pods share the same nodes. A $500/month EC2 instance might run pods from three different teams, but the bill shows one line item for the instance. Cost allocation requires understanding which pods ran on which nodes, for how long, and how much CPU/memory they consumed. Tools like Kubecost and OpenCost perform this allocation by combining cloud billing data (actual cost per node) with Kubernetes metrics (resource usage per pod), then aggregating by team labels to produce per-team costs. Without this layer, the best you can do is per-account or per-cluster costs, which are too coarse for team-level accountability.
</details>

<details>
<summary>2. What is the difference between VPA and HPA, and how do they optimize costs differently?</summary>

VPA (Vertical Pod Autoscaler) adjusts resource requests and limits for individual pods based on observed usage. It optimizes cost by reducing over-provisioned requests, allowing more pods to fit on each node. HPA (Horizontal Pod Autoscaler) adjusts the number of pod replicas based on metrics (CPU, memory, custom). It optimizes cost by scaling down replicas during low-traffic periods. VPA answers "how big should each pod be?" while HPA answers "how many pods should we run?" They complement each other: VPA right-sizes each pod, and HPA scales the count based on demand. Using both together (with VPA in recommendation mode) provides the best cost optimization.
</details>

<details>
<summary>3. You have $10,000/month in on-demand EC2 usage that runs 24/7. Should you commit to a $10,000/month Savings Plan?</summary>

No. Commit to $6,000-$7,000 (60-70% of current usage). Savings Plans commit you to a minimum hourly spend regardless of actual usage. If your usage drops (due to right-sizing, traffic changes, or migration), you still pay the committed amount. The remaining 30-40% stays on-demand, giving you flexibility. Over time, as you're confident in your baseline, you can increase the commitment. Also consider: some of that $10K might be better served by Spot instances (for fault-tolerant workloads), which provide deeper discounts without long-term commitment. The optimal strategy is often: 60% Savings Plans + 20% Spot + 20% On-demand.
</details>

<details>
<summary>4. How do Spot instance interruptions affect Kubernetes workloads, and what makes them safe for some workloads?</summary>

When a Spot instance is interrupted, AWS sends a 2-minute warning. The Node Termination Handler detects this and cordons the node (preventing new scheduling) then drains it (evicting pods with graceful termination). Kubernetes' ReplicaSet controller detects the missing pods and schedules replacements on other nodes. This makes Spot safe for workloads that are: (a) stateless (no local data to lose), (b) replicated (losing one pod doesn't affect availability if others run on non-Spot nodes), (c) fault-tolerant (batch jobs that can checkpoint and resume), or (d) have PodDisruptionBudgets that ensure enough replicas survive the drain. Spot is NOT safe for: single-replica stateful workloads, control plane components, or workloads that take more than 2 minutes to gracefully shutdown.
</details>

<details>
<summary>5. A development EKS cluster costs $3,000/month and is used Monday-Friday, 9AM-6PM. How much can you save?</summary>

Business hours represent roughly 45 hours per week out of 168 total hours (27% of the time). If you scale the cluster to zero (or minimum) outside business hours, you save approximately 73% of compute costs: $3,000 x 0.73 = $2,190/month saved. Implementation options: (a) Karpenter with consolidation + scheduled scaling to zero, (b) a CronJob that scales node groups to 0 at 6PM and back to desired count at 9AM, (c) tools like kube-downscaler that annotate deployments with shutdown schedules. Additional savings: shut down NAT Gateways and load balancers when the cluster is empty. Caveat: factor in the 10-15 minute spin-up time each morning.
</details>

<details>
<summary>6. What are the most commonly orphaned cloud resources in Kubernetes environments?</summary>

The most common orphans are: (1) EBS volumes from deleted PVCs where the StorageClass had `reclaimPolicy: Retain` -- the PV is released but the underlying volume persists and incurs charges. (2) Load balancers from deleted Services of type LoadBalancer -- if the Service is deleted without proper finalizers, the cloud LB may remain. (3) Elastic IPs allocated for Services that are later deleted. (4) EBS snapshots from old Velero backups with no TTL configured. (5) Target groups in ALBs that no longer have any registered targets. (6) Security groups created by Kubernetes that are no longer referenced. These accumulate over months and can represent 5-15% of total cloud spend. Weekly automated scans with alerts are the most effective prevention.
</details>

---

## Hands-On Exercise: Cost Optimization Audit

In this exercise, you will perform a cost optimization audit on a Kubernetes cluster.

### Prerequisites

- A running Kubernetes cluster (kind, minikube, or cloud)
- kubectl installed
- Metrics server installed (for VPA)

### Task 1: Identify Over-Provisioned Workloads

Deploy some intentionally over-provisioned workloads and use kubectl to identify waste.

<details>
<summary>Solution</summary>

```bash
# Create a kind cluster with metrics server
kind create cluster --name cost-lab

# Install metrics server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch for kind (insecure kubelet)
kubectl patch deployment metrics-server -n kube-system \
  --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

# Wait for metrics server
sleep 30
kubectl wait --for=condition=Ready pod -l k8s-app=metrics-server -n kube-system --timeout=120s

# Deploy over-provisioned workloads
kubectl create namespace cost-audit

kubectl apply -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server-wasteful
  namespace: cost-audit
  labels:
    team: backend
    cost-center: CC-1000
spec:
  replicas: 5
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
        team: backend
    spec:
      containers:
        - name: api
          image: nginx:stable
          resources:
            requests:
              cpu: "2"
              memory: "4Gi"
            limits:
              cpu: "4"
              memory: "8Gi"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker-wasteful
  namespace: cost-audit
  labels:
    team: data
    cost-center: CC-2000
spec:
  replicas: 3
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
        team: data
    spec:
      containers:
        - name: worker
          image: nginx:stable
          resources:
            requests:
              cpu: "1"
              memory: "2Gi"
            limits:
              cpu: "2"
              memory: "4Gi"
EOF

# Wait for pods (some will be Pending due to insufficient resources)
sleep 15

# Check actual usage vs requests
echo "=== Pod Resource Usage vs Requests ==="
kubectl top pods -n cost-audit 2>/dev/null || echo "Metrics not ready yet, wait 60s"

# Compare requests to actual usage
kubectl get pods -n cost-audit -o custom-columns=\
NAME:.metadata.name,\
CPU_REQ:.spec.containers[0].resources.requests.cpu,\
MEM_REQ:.spec.containers[0].resources.requests.memory,\
STATUS:.status.phase
```
</details>

### Task 2: Calculate the Waste

<details>
<summary>Solution</summary>

```bash
# Calculate total requested vs actual
echo "=== Requested Resources ==="
echo "api-server: 5 pods x 2 CPU = 10 CPU requested"
echo "api-server: 5 pods x 4Gi = 20Gi memory requested"
echo "worker: 3 pods x 1 CPU = 3 CPU requested"
echo "worker: 3 pods x 2Gi = 6Gi memory requested"
echo ""
echo "TOTAL REQUESTED: 13 CPU, 26Gi memory"
echo ""
echo "At m7i.xlarge pricing ($0.192/hr, 4 CPU, 16Gi):"
echo "13 CPU / 4 CPU per node = 4 nodes needed (by CPU)"
echo "26Gi / 16Gi per node = 2 nodes needed (by memory)"
echo "Limiting factor: CPU (4 nodes)"
echo ""
echo "Cost: 4 nodes x $0.192/hr x 730 hours = $561/month"
echo ""
echo "=== Actual Usage (nginx idle) ==="
echo "Each nginx pod uses ~5m CPU and ~5Mi memory"
echo "Total actual: ~40m CPU, ~40Mi memory"
echo "Actual need: 1 node (easily)"
echo ""
echo "WASTE: $561 - $140 (1 node) = $421/month (75% waste)"
echo ""
echo "=== VPA Recommendations ==="
echo "api-server: request 50m CPU, 64Mi memory (from 2 CPU, 4Gi)"
echo "worker: request 50m CPU, 64Mi memory (from 1 CPU, 2Gi)"
```
</details>

### Task 3: Apply Right-Sizing

<details>
<summary>Solution</summary>

```bash
# Right-size the deployments based on "VPA recommendations"
kubectl patch deployment api-server-wasteful -n cost-audit --type=json -p='[
  {"op": "replace", "path": "/spec/template/spec/containers/0/resources/requests/cpu", "value": "100m"},
  {"op": "replace", "path": "/spec/template/spec/containers/0/resources/requests/memory", "value": "128Mi"},
  {"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/cpu", "value": "500m"},
  {"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value": "256Mi"}
]'

kubectl patch deployment worker-wasteful -n cost-audit --type=json -p='[
  {"op": "replace", "path": "/spec/template/spec/containers/0/resources/requests/cpu", "value": "100m"},
  {"op": "replace", "path": "/spec/template/spec/containers/0/resources/requests/memory", "value": "128Mi"},
  {"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/cpu", "value": "500m"},
  {"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value": "256Mi"}
]'

# Verify all pods are now Running (they fit on fewer nodes)
kubectl get pods -n cost-audit

echo "=== After Right-Sizing ==="
echo "api-server: 5 pods x 100m CPU = 500m CPU requested"
echo "worker: 3 pods x 100m CPU = 300m CPU requested"
echo "TOTAL: 800m CPU, ~1Gi memory"
echo "Fits on 1 node easily. Savings: 75%"
```
</details>

### Task 4: Create a Cost Optimization Report

Write a cost optimization report for a fictional team based on the audit findings.

<details>
<summary>Solution</summary>

```markdown
# Cost Optimization Report: Cost-Audit Namespace

## Executive Summary
Current monthly spend: ~$561 (4 nodes at on-demand pricing)
Optimized monthly spend: ~$140 (1 node at on-demand pricing)
Potential savings: $421/month ($5,052/year) -- 75% reduction

## Findings

### 1. Over-Provisioned Resources (Impact: $421/month)
- api-server requests 2 CPU per pod but uses ~5m (0.25%)
- worker requests 1 CPU per pod but uses ~5m (0.5%)
- Total CPU requested: 13 cores. Total used: 40 millicores.
- Recommendation: Reduce requests to 100m CPU, 128Mi memory

### 2. No Horizontal Pod Autoscaler (Impact: TBD)
- api-server runs 5 replicas constantly
- Likely needs 2 replicas at baseline, scale to 5 during peak
- Recommendation: Add HPA with min=2, max=8, target CPU=70%
- Estimated additional savings: 40% during off-peak

### 3. On-Demand Pricing (Impact: ~$50/month)
- Workloads run 24/7, perfect for Savings Plans
- With 1-year Compute Savings Plan: $140 * 0.63 = $88/month
- Savings: $52/month

## Recommended Actions (priority order)
1. Apply right-sized resource requests (immediate, $421/month)
2. Add HPA for api-server (1 day, ~$30/month additional)
3. Purchase Savings Plan for baseline compute (1 week, ~$50/month)

## Total Estimated Savings: $501/month ($6,012/year)
```
</details>

### Clean Up

```bash
kind delete cluster --name cost-lab
```

### Success Criteria

- [ ] Over-provisioned workloads deployed and identified
- [ ] Waste quantified in dollar terms
- [ ] Right-sized resource requests applied
- [ ] All pods running after right-sizing (no OOM or throttling)
- [ ] Cost optimization report includes specific dollar savings

---

## Next Module

[Module 8.9: Large-Scale Observability & Telemetry](module-8.9-observability-scale/) -- You can see where the money goes. Now learn how to see where the problems are. Multi-cluster Prometheus with Thanos, OpenTelemetry at scale, and the art of monitoring Kubernetes without drowning in data.
