---
title: "Module 1.5: Storage & Network Cost Management"
slug: platform/disciplines/business-value/finops/module-1.5-storage-network-costs
sidebar:
  order: 6
---
> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 2h

## Prerequisites

Before starting this module:
- **Required**: [Module 1.1: FinOps Fundamentals](../module-1.1-finops-fundamentals/) — FinOps lifecycle, billing concepts
- **Required**: Understanding of Kubernetes Persistent Volumes and StorageClasses
- **Required**: Basic networking concepts (VPC, subnets, NAT, load balancers)
- **Recommended**: AWS or GCP experience (examples use AWS terminology)
- **Recommended**: Familiarity with cloud storage tiers (S3, EBS, EFS)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Implement storage cost optimization through lifecycle policies, tiering, and right-sized volume claims**
- **Design network cost reduction strategies that minimize cross-AZ traffic and egress charges**
- **Analyze storage and network spending to identify the largest cost drivers in your Kubernetes environment**
- **Build monitoring dashboards that track storage utilization and network transfer costs by namespace and service**

## Why This Module Matters

Everyone optimizes compute. It's the obvious line item — the big EC2 or GCE charges that dominate the bill. But lurking beneath are two cost categories that grow silently and are far harder to control: **storage** and **networking**.

Here's what makes them dangerous:

**Storage**: Resources that persist after workloads die. Delete a Deployment, and the PersistentVolume stays. Terminate a node, and the EBS volume remains. Take a snapshot "just in case," and it lives forever. Storage costs accumulate like sediment — slowly, quietly, and expensively.

**Networking**: The invisible tax on everything. Every cross-AZ call costs money. Every response to a user costs money. Every NAT Gateway byte costs money. And nobody budgets for it because nobody can predict it.

```
Typical cloud bill breakdown:
┌───────────────────────────────────────────┐
│                                           │
│  Compute   ████████████████████   58%     │
│            (everyone optimizes this)      │
│                                           │
│  Storage   ██████████              22%    │
│            (few people optimize this)     │
│                                           │
│  Network   █████                   12%    │
│            (nobody optimizes this)        │
│                                           │
│  Other     ███                      8%    │
│                                           │
└───────────────────────────────────────────┘
```

The 34% that's storage and network? That's where the hidden waste lives. This module shows you how to find it and fix it.

---

## Did You Know?

- **AWS data transfer costs can be the third-largest line item** on a cloud bill, after compute and storage. Cross-AZ data transfer alone costs $0.01/GB in each direction — which sounds cheap until you realize a busy microservice architecture can generate terabytes of cross-AZ traffic monthly. One company discovered their service mesh was costing $23,000/month just in cross-AZ data transfer.

- **Orphaned EBS volumes are one of the most common sources of cloud waste.** When a Kubernetes node is terminated or a PV is released with a `Retain` reclaim policy, the underlying EBS volume persists — and you keep paying for it. AWS estimates that 20-30% of EBS volumes in a typical account are unattached.

- **NAT Gateway pricing is often the biggest networking surprise.** At $0.045/GB for data processing plus $0.045/hour for the gateway itself, a NAT Gateway processing 5 TB/month costs over $250 — just for routing traffic. VPC Endpoints for AWS services (S3, DynamoDB, ECR) can eliminate most of this cost for free.

---

## Storage Cost Management

### EBS Volume Types and Costs

Understanding which storage type to use is the first optimization lever:

| Volume Type | IOPS | Throughput | Cost ($/GB/mo) | Best For |
|-------------|------|------------|-----------------|----------|
| gp3 (General Purpose SSD) | 3,000 baseline (free) | 125 MB/s baseline | $0.08 | Most workloads (default) |
| gp2 (Older GP SSD) | 3 IOPS/GB (min 100) | Tied to IOPS | $0.10 | Legacy — migrate to gp3 |
| io2 (Provisioned IOPS) | Up to 64,000 | Up to 1,000 MB/s | $0.125 + $0.065/IOPS | Databases needing guaranteed IOPS |
| st1 (Throughput HDD) | 500 | 500 MB/s | $0.045 | Big data, sequential reads |
| sc1 (Cold HDD) | 250 | 250 MB/s | $0.015 | Infrequent access, archives |

### Quick Win: gp2 to gp3 Migration

gp3 is almost always cheaper than gp2 — with better baseline performance:

```
gp2 vs gp3 for 500 GB volume:
┌──────────────────────────────────────────────────┐
│ gp2:                                             │
│   Cost: 500 GB × $0.10 = $50/mo                 │
│   IOPS: 1,500 (3 per GB)                        │
│   Throughput: 250 MB/s (tied to IOPS)            │
│                                                  │
│ gp3:                                             │
│   Cost: 500 GB × $0.08 = $40/mo                 │
│   IOPS: 3,000 baseline (free, 2x more!)         │
│   Throughput: 125 MB/s (upgradeable)             │
│                                                  │
│ Savings: $10/mo per volume (20%)                 │
│ Plus: 2x the IOPS at no extra cost               │
│                                                  │
│ × 40 volumes in your cluster = $400/mo saved     │
└──────────────────────────────────────────────────┘
```

### Kubernetes StorageClass for Cost Optimization

```yaml
# Cost-optimized gp3 StorageClass
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-cost-optimized
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  fsType: ext4
  encrypted: "true"
reclaimPolicy: Delete      # Auto-cleanup when PVC deleted
allowVolumeExpansion: true  # Grow without recreating
volumeBindingMode: WaitForFirstConsumer  # Bind to same AZ as pod
---
# Cold storage for infrequent access (logs, archives)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: cold-storage
provisioner: ebs.csi.aws.com
parameters:
  type: sc1
  fsType: ext4
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

### Orphaned Volumes: The Silent Cost Drain

Orphaned volumes happen when:
1. A PVC is deleted but the PV has `reclaimPolicy: Retain`
2. A node is terminated but the EBS volume isn't cleaned up
3. A StatefulSet is deleted but its PVCs persist (by design)
4. Terraform creates volumes that aren't managed by Kubernetes

```
Orphaned Volume Lifecycle:
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Created  │────▶│ In Use   │────▶│ Released │────▶│ Orphaned │
│ (PVC     │     │ (Pod     │     │ (Pod gone│     │ (Nobody  │
│  created)│     │  running)│     │  PV stays│     │  knows   │
│          │     │          │     │          │     │  it exists│
│ $0.08/GB │     │ $0.08/GB │     │ $0.08/GB │     │ $0.08/GB │
│ /month   │     │ /month   │     │ /month   │     │ FOREVER  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

### Finding Orphaned PVs in Kubernetes

```bash
# Find PVs that are Released (no longer bound to a PVC)
# Note: PVs only support metadata.name and metadata.namespace field selectors,
# so we filter by phase using grep or jq instead
kubectl get pv | grep Released

# Find PVs that are Available (never claimed)
kubectl get pv | grep Available

# For structured output, use jq:
# kubectl get pv -o json | jq '.items[] | select(.status.phase=="Released") | .metadata.name'

# Detailed view with age
kubectl get pv -o custom-columns=\
NAME:.metadata.name,\
STATUS:.status.phase,\
CAPACITY:.spec.capacity.storage,\
RECLAIM:.spec.persistentVolumeReclaimPolicy,\
STORAGECLASS:.spec.storageClassName,\
AGE:.metadata.creationTimestamp
```

### Snapshot Management

Snapshots are another silent cost accumulator:

```
Snapshot Cost:
┌──────────────────────────────────────────────────┐
│ EBS Snapshot pricing: $0.05/GB/month             │
│                                                  │
│ "Let's keep daily snapshots for safety"          │
│                                                  │
│ 500 GB volume × 30 daily snapshots               │
│ (incremental, but ~60% of full size)             │
│ = ~300 GB effective snapshot storage              │
│ = $15/month per volume                           │
│                                                  │
│ × 40 volumes = $600/month just for snapshots     │
│                                                  │
│ Most of these are never accessed.                │
│ They exist "just in case."                       │
│ That "just in case" costs $7,200/year.           │
└──────────────────────────────────────────────────┘
```

### Snapshot Lifecycle Policy

```json
{
  "Description": "Cost-optimized snapshot lifecycle",
  "Rules": [
    {
      "Name": "daily-snapshots-7-day-retention",
      "Schedule": "cron(0 2 * * *)",
      "Retain": 7,
      "CopyTags": true,
      "Tags": {
        "lifecycle": "managed",
        "retention": "7-days"
      }
    },
    {
      "Name": "weekly-snapshots-30-day-retention",
      "Schedule": "cron(0 3 * * 0)",
      "Retain": 4,
      "CopyTags": true,
      "Tags": {
        "lifecycle": "managed",
        "retention": "30-days"
      }
    }
  ]
}
```

---

## S3 Storage Tiering

For object storage, choosing the right tier can save 50-90%:

| Tier | Cost ($/GB/mo) | Retrieval Cost | Access Pattern |
|------|----------------|----------------|----------------|
| S3 Standard | $0.023 | Free | Frequent access |
| S3 Intelligent-Tiering | $0.023-$0.004 | Free | Unknown/changing patterns |
| S3 Standard-IA | $0.0125 | $0.01/GB | Monthly access |
| S3 One Zone-IA | $0.01 | $0.01/GB | Reproducible data, monthly |
| S3 Glacier Instant | $0.004 | $0.03/GB | Quarterly, instant retrieval |
| S3 Glacier Flexible | $0.0036 | Minutes to hours | Annual compliance |
| S3 Glacier Deep Archive | $0.00099 | 12-48 hours | Regulatory retention |

### Lifecycle Policy Example

```json
{
  "Rules": [
    {
      "ID": "logs-lifecycle",
      "Filter": { "Prefix": "logs/" },
      "Status": "Enabled",
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
      ],
      "Expiration": {
        "Days": 2555
      }
    }
  ]
}
```

```
Cost savings over 7 years for 1 TB of logs:
┌─────────────────────────────────────────────────────┐
│ Without lifecycle:                                   │
│   7 years × 12 months × $23/TB = $1,932             │
│                                                      │
│ With lifecycle:                                      │
│   First 30 days: Standard = $23                      │
│   Days 31-90: Standard-IA = $25 (2 months × $12.50) │
│   Days 91-365: Glacier IR = $36 (9 months × $4)     │
│   Years 2-7: Deep Archive = $71 (72 months × $0.99) │
│   Total: $155                                        │
│                                                      │
│ Savings: $1,777 per TB (92% reduction!)              │
└─────────────────────────────────────────────────────┘
```

---

## Network Cost Management

### The Data Transfer Cost Map

Understanding where data transfer charges apply:

```
AWS Data Transfer Cost Map:
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Internet ──────$0.09/GB──────▶ AWS (ingress is free)  │
│  AWS ──────$0.09/GB──────▶ Internet (egress)           │
│                                                         │
│  ┌──── Region A ────────────────────────┐               │
│  │                                      │               │
│  │  AZ-1 ◄──$0.01/GB──▶ AZ-2          │               │
│  │   │                    │             │               │
│  │   │ (same AZ = FREE)  │             │               │
│  │   │                    │             │               │
│  │  EC2 ◄─── FREE ──▶ EC2             │               │
│  │  (same AZ)                          │               │
│  └──────────────────────────────────────┘               │
│          │                                              │
│    $0.02/GB                                             │
│          │                                              │
│  ┌──── Region B ────────────────────────┐               │
│  │                                      │               │
│  └──────────────────────────────────────┘               │
│                                                         │
│  VPC Endpoint to S3/DynamoDB: FREE (Gateway endpoint)  │
│  NAT Gateway processing: $0.045/GB                     │
│  Load Balancer: $0.008/GB processed                    │
└─────────────────────────────────────────────────────────┘
```

### Cross-AZ Traffic: The Kubernetes Hidden Tax

In Kubernetes, services communicate across AZs constantly. Every cross-AZ call costs $0.01/GB in each direction ($0.02/GB round-trip).

```
Microservice Communication (3 AZs):
┌─────────────────────────────────────────────────┐
│                                                 │
│  AZ-a              AZ-b              AZ-c      │
│  ┌────────┐        ┌────────┐        ┌────────┐│
│  │ API    │──$──▶  │ Search │──$──▶  │ Cache  ││
│  │ (Pod)  │        │ (Pod)  │        │ (Pod)  ││
│  └────────┘        └────────┘        └────────┘│
│       │                                  ▲      │
│       │               $0.01/GB           │      │
│       └──────────────each way────────────┘      │
│                                                 │
│  100 GB/day cross-AZ traffic:                   │
│  = 100 × $0.02 × 30 days = $60/month           │
│                                                 │
│  For a busy cluster with 500 GB/day:            │
│  = 500 × $0.02 × 30 = $300/month               │
│  = $3,600/year just for cross-AZ traffic        │
└─────────────────────────────────────────────────┘
```

### Reducing Cross-AZ Traffic

**Strategy 1: Topology-Aware Service Routing**

```yaml
# Route traffic to same-AZ endpoints first
apiVersion: v1
kind: Service
metadata:
  name: search-api
  namespace: search
  annotations:
    service.kubernetes.io/topology-mode: Auto
spec:
  selector:
    app: search-api
  ports:
  - port: 80
    targetPort: 8080
```

With `topology-mode: Auto`, Kubernetes routes traffic to same-zone endpoints when possible, falling back to cross-zone only when needed.

**Strategy 2: Pod Topology Spread with Zone Awareness**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: search-api
spec:
  replicas: 6
  template:
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: search-api
```

This ensures pods are evenly distributed across AZs, so each AZ has local endpoints to talk to.

**Strategy 3: Zone-Affine Deployments**

For services that communicate heavily, co-locate them in the same AZ:

```yaml
# Co-locate API and its cache in the same AZ
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  template:
    spec:
      affinity:
        podAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: redis-cache
              topologyKey: topology.kubernetes.io/zone
```

### NAT Gateway vs VPC Endpoints

NAT Gateway is one of the most expensive networking components — and often unnecessary.

```
NAT Gateway Cost:
┌──────────────────────────────────────────────────┐
│ NAT Gateway hourly charge: $0.045/hr             │
│ Monthly fixed: $32.85/month per gateway          │
│                                                  │
│ Data processing: $0.045/GB                       │
│                                                  │
│ Common traffic through NAT:                      │
│   ECR image pulls:        50 GB/mo = $2.25       │
│   S3 access (logs):      200 GB/mo = $9.00       │
│   External API calls:     30 GB/mo = $1.35       │
│   DynamoDB:              100 GB/mo = $4.50       │
│   Monitoring/telemetry:   80 GB/mo = $3.60       │
│                                                  │
│ Total processing:                   $20.70       │
│ + Fixed cost:                       $32.85       │
│ + Per-AZ (usually 3):              × 3           │
│ = Total NAT cost:                  $160.65/mo    │
└──────────────────────────────────────────────────┘
```

### VPC Endpoints Eliminate Most NAT Costs

```
VPC Endpoints:
┌──────────────────────────────────────────────────┐
│ Gateway Endpoints (FREE):                        │
│   • S3           → saves $9.00/mo in NAT fees   │
│   • DynamoDB     → saves $4.50/mo in NAT fees   │
│                                                  │
│ Interface Endpoints ($0.01/hr + $0.01/GB):       │
│   • ECR/ECR API  → $7.30/mo + $0.50 = $7.80    │
│   • CloudWatch   → $7.30/mo + $0.30 = $7.60    │
│   • STS          → $7.30/mo + $0.01 = $7.31    │
│                                                  │
│ Still need NAT for:                              │
│   • External API calls ($1.35/mo)                │
│   • Third-party services                         │
│                                                  │
│ Before VPC Endpoints: $160.65/mo                 │
│ After VPC Endpoints:   $55.41/mo                 │
│ Savings:              $105.24/mo (65%)           │
└──────────────────────────────────────────────────┘
```

### Essential VPC Endpoints for EKS

```hcl
# Terraform: Create VPC Endpoints for EKS cost optimization
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = aws_route_table.private[*].id
  # Gateway endpoints are FREE
}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
}

resource "aws_vpc_endpoint" "logs" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.logs"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
}
```

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Using gp2 instead of gp3 | Default in many tools/templates | Change default StorageClass to gp3 |
| PVs with Retain policy and no cleanup | Safety-first mentality | Use Delete policy for non-critical data, automate cleanup for Retain |
| No snapshot lifecycle policy | "Snapshots are cheap" | Implement DLM policies: 7 daily, 4 weekly |
| All traffic through NAT Gateway | Simple architecture | Add Gateway endpoints (S3, DynamoDB) and Interface endpoints (ECR, CloudWatch) |
| Ignoring cross-AZ data transfer | Invisible on most dashboards | Enable topology-aware routing, monitor with VPC Flow Logs |
| Over-sized EBS volumes "just in case" | Can't shrink EBS | Start small with volume expansion enabled |
| S3 Standard for everything | Default tier | Implement lifecycle policies for logs and backups |
| No volume encryption | "We'll do it later" | Encrypt by default — gp3 encrypted costs the same |

---

## Quiz

### Question 1
Your cluster has 35 gp2 EBS volumes averaging 200 GB each. What's the annual savings from migrating to gp3?

<details>
<summary>Show Answer</summary>

**gp2 cost**: 35 volumes × 200 GB × $0.10/GB/mo = **$700/month**
**gp3 cost**: 35 volumes × 200 GB × $0.08/GB/mo = **$560/month**
**Monthly savings**: $140/month
**Annual savings**: **$1,680/year**

Bonus: gp3 also gives you 3,000 baseline IOPS (free) compared to gp2's 600 IOPS (3 IOPS/GB × 200 GB). So you get better performance AND lower cost. This is one of the easiest wins in FinOps.
</details>

### Question 2
Your EKS cluster has a NAT Gateway processing 8 TB/month. You discover that 5 TB is S3 traffic and 2 TB is ECR image pulls. How much can you save with VPC Endpoints?

<details>
<summary>Show Answer</summary>

**Current NAT cost for this traffic**:
- S3: 5,000 GB × $0.045/GB = $225/month
- ECR: 2,000 GB × $0.045/GB = $90/month
- Other: 1,000 GB × $0.045/GB = $45/month
- Total data processing: $360/month (+ fixed gateway cost)

**With VPC Endpoints**:
- S3 Gateway Endpoint: **FREE** (saves $225/month)
- ECR Interface Endpoints (api + dkr): 2 × $7.30/mo + 2,000 GB × $0.01/GB = $34.60/month (saves $55.40/month)
- Other still via NAT: $45/month (unchanged)

**Monthly savings**: ~$280/month
**Annual savings**: ~$3,360/year

The S3 Gateway Endpoint alone saves $225/month and takes 5 minutes to create.
</details>

### Question 3
Why does Kubernetes cross-AZ traffic cost money, and how do you reduce it?

<details>
<summary>Show Answer</summary>

AWS charges $0.01/GB for data transfer between Availability Zones (in each direction, so $0.02/GB round-trip). In Kubernetes, kube-proxy load-balances service traffic across all endpoints, regardless of AZ. A pod in AZ-a calling a service with endpoints in AZ-a, AZ-b, and AZ-c will send ~66% of traffic cross-AZ.

**Reduction strategies**:
1. **Topology-aware routing** (`service.kubernetes.io/topology-mode: Auto`) — routes to same-AZ endpoints first
2. **Pod topology spread** — ensure each AZ has local endpoints
3. **Pod affinity** — co-locate heavily communicating services in the same AZ
4. **Internal traffic policies** (`internalTrafficPolicy: Local`) — restrict to same-node endpoints
5. **Monitor with VPC Flow Logs** — identify top cross-AZ talkers
</details>

### Question 4
A team has 50 EBS snapshots from a daily backup of a 500 GB database, going back 50 days with no expiration. What's the monthly cost, and what retention policy would you recommend?

<details>
<summary>Show Answer</summary>

**Snapshot cost** (incremental, typically ~60% of volume size after first full):
- First snapshot: ~500 GB
- Subsequent 49: ~300 GB each (incremental average)
- Total storage: 500 + (49 × 300) = ~15,200 GB
- Monthly cost: 15,200 GB × $0.05/GB = **$760/month**

**Recommended policy**:
- Keep 7 daily snapshots (last week)
- Keep 4 weekly snapshots (last month)
- Keep 3 monthly snapshots (last quarter)
- Total: 14 snapshots instead of 50+
- Estimated storage: ~4,200 GB
- New cost: ~$210/month
- **Savings: $550/month ($6,600/year)**
</details>

### Question 5
What is the difference between a VPC Gateway Endpoint and an Interface Endpoint? When would you use each?

<details>
<summary>Show Answer</summary>

**Gateway Endpoints**:
- Support only S3 and DynamoDB
- **Free** (no hourly or per-GB charges)
- Work by adding routes to your route table
- Traffic stays within AWS network
- No DNS changes needed

**Interface Endpoints** (powered by AWS PrivateLink):
- Support 100+ AWS services (ECR, CloudWatch, STS, etc.)
- Cost: ~$0.01/hour per AZ + $0.01/GB processed
- Create ENIs in your subnets
- Support private DNS
- Can be used across VPC peering

**Use Gateway Endpoints** for S3 and DynamoDB (always — they're free). **Use Interface Endpoints** for other high-traffic AWS services (ECR, CloudWatch, STS) when the per-GB savings vs NAT Gateway exceed the endpoint hourly cost.
</details>

---

## Hands-On Exercise: Find Unattached PVs and Old Snapshots

Write scripts to identify storage waste in your Kubernetes cluster.

### Step 1: Setup

```bash
# Create a kind cluster
kind create cluster --name storage-lab

# Create namespace
kubectl create namespace storage-lab
```

### Step 2: Create Storage Resources (Simulated Waste)

```bash
# Create PVs and PVCs to simulate various states
kubectl apply -f - << 'EOF'
# PV with Retain policy (will become orphaned)
apiVersion: v1
kind: PersistentVolume
metadata:
  name: orphaned-pv-001
  labels:
    type: database-backup
spec:
  capacity:
    storage: 100Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /tmp/pv-001
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: orphaned-pv-002
  labels:
    type: log-archive
spec:
  capacity:
    storage: 250Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /tmp/pv-002
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: orphaned-pv-003
  labels:
    type: ml-model-store
spec:
  capacity:
    storage: 500Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /tmp/pv-003
---
# Active PV with PVC (this one is in use)
apiVersion: v1
kind: PersistentVolume
metadata:
  name: active-pv-001
spec:
  capacity:
    storage: 50Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Delete
  storageClassName: manual
  hostPath:
    path: /tmp/pv-active
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: active-pvc
  namespace: storage-lab
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: manual
  resources:
    requests:
      storage: 50Gi
EOF

echo "Storage resources created."
```

### Step 3: Write the Waste Detection Script

```bash
cat > /tmp/storage_audit.sh << 'SCRIPT'
#!/bin/bash
echo "============================================"
echo "  Storage Waste Audit Report"
echo "  Date: $(date +%Y-%m-%d)"
echo "============================================"
echo ""

# Section 1: Unbound PVs (Available or Released)
echo "--- Unbound Persistent Volumes ---"
echo ""
UNBOUND=$(kubectl get pv -o json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
items = [pv for pv in data.get('items', []) if pv['status']['phase'] != 'Bound']
json.dump({'items': items}, sys.stdout)
" 2>/dev/null)
UNBOUND_COUNT=$(echo "$UNBOUND" | python3 -c "
import json, sys
data = json.load(sys.stdin)
pvs = data.get('items', [])
print(len(pvs))
" 2>/dev/null)

if [ "$UNBOUND_COUNT" -gt 0 ]; then
  echo "Found $UNBOUND_COUNT unbound PV(s):"
  echo ""
  echo "$UNBOUND" | python3 -c "
import json, sys
data = json.load(sys.stdin)
total_gb = 0
for pv in data.get('items', []):
    name = pv['metadata']['name']
    phase = pv['status']['phase']
    cap = pv['spec']['capacity']['storage']
    reclaim = pv['spec']['persistentVolumeReclaimPolicy']
    created = pv['metadata']['creationTimestamp']
    pv_type = pv['metadata'].get('labels', {}).get('type', 'unknown')

    # Parse capacity
    gb = 0
    if 'Gi' in cap:
        gb = int(cap.replace('Gi', ''))
    elif 'Ti' in cap:
        gb = int(cap.replace('Ti', '')) * 1024

    total_gb += gb
    cost_mo = gb * 0.08  # gp3 pricing

    print(f'  {name}')
    print(f'    Status: {phase} | Size: {cap} | Reclaim: {reclaim}')
    print(f'    Type: {pv_type} | Created: {created}')
    print(f'    Estimated cost: \${cost_mo:.2f}/month')
    print()

total_cost = total_gb * 0.08
print(f'  TOTAL UNBOUND: {total_gb} Gi = \${total_cost:.2f}/month (\${total_cost * 12:.2f}/year)')
"
else
  echo "  No unbound PVs found."
fi

echo ""

# Section 2: PVCs without active Pods
echo "--- PVCs Not Mounted by Any Pod ---"
echo ""

# Get all PVC names that are currently mounted
MOUNTED_PVCS=$(kubectl get pods -A -o json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
mounted = set()
for pod in data.get('items', []):
    ns = pod['metadata']['namespace']
    for vol in pod['spec'].get('volumes', []):
        pvc = vol.get('persistentVolumeClaim', {}).get('claimName')
        if pvc:
            mounted.add(f'{ns}/{pvc}')
for m in sorted(mounted):
    print(m)
" 2>/dev/null)

# Get all PVCs and check if they're mounted
kubectl get pvc -A -o json 2>/dev/null | python3 -c "
import json, sys

mounted = set(line.strip() for line in '''$MOUNTED_PVCS'''.strip().split('\n') if line.strip())

data = json.load(sys.stdin)
unmounted = []
for pvc in data.get('items', []):
    ns = pvc['metadata']['namespace']
    name = pvc['metadata']['name']
    key = f'{ns}/{name}'
    if key not in mounted:
        cap = pvc['status'].get('capacity', {}).get('storage', 'unknown')
        unmounted.append((ns, name, cap))

if unmounted:
    for ns, name, cap in unmounted:
        print(f'  {ns}/{name} ({cap}) — not mounted by any pod')
    print(f'\n  Total unmounted PVCs: {len(unmounted)}')
else:
    print('  All PVCs are actively mounted.')
"

echo ""

# Section 3: Storage class analysis
echo "--- StorageClass Summary ---"
echo ""
kubectl get sc -o custom-columns=\
NAME:.metadata.name,\
PROVISIONER:.provisioner,\
RECLAIM:.reclaimPolicy,\
BINDING:.volumeBindingMode 2>/dev/null

echo ""

# Section 4: Recommendations
echo "--- Recommendations ---"
echo ""
echo "  1. Review all Released/Available PVs — delete if data is no longer needed"
echo "  2. Change default StorageClass to gp3 if currently using gp2"
echo "  3. Set reclaim policy to Delete for non-critical PVs"
echo "  4. Implement snapshot lifecycle policies (7 daily, 4 weekly)"
echo "  5. Use volume expansion instead of creating oversized volumes"
echo ""
echo "============================================"
SCRIPT

chmod +x /tmp/storage_audit.sh
bash /tmp/storage_audit.sh
```

### Step 4: AWS-Specific Audit (Reference)

For real AWS environments, extend the audit to EBS and snapshots:

```bash
# Find unattached EBS volumes (AWS CLI)
cat > /tmp/aws_storage_audit.sh << 'AWSSCRIPT'
#!/bin/bash
# NOTE: This requires AWS CLI configured with appropriate permissions

echo "--- Unattached EBS Volumes ---"
aws ec2 describe-volumes \
  --filters Name=status,Values=available \
  --query 'Volumes[].{ID:VolumeId,Size:Size,Type:VolumeType,Created:CreateTime,AZ:AvailabilityZone}' \
  --output table 2>/dev/null || echo "  (AWS CLI not configured — skipping)"

echo ""
echo "--- Old EBS Snapshots (>90 days) ---"
NINETY_DAYS_AGO=$(date -v-90d +%Y-%m-%dT00:00:00 2>/dev/null || date -d "90 days ago" +%Y-%m-%dT00:00:00 2>/dev/null)
aws ec2 describe-snapshots \
  --owner-ids self \
  --query "Snapshots[?StartTime<='${NINETY_DAYS_AGO}'].{ID:SnapshotId,Size:VolumeSize,Started:StartTime,Description:Description}" \
  --output table 2>/dev/null || echo "  (AWS CLI not configured — skipping)"

echo ""
echo "--- EBS Volume Type Distribution ---"
aws ec2 describe-volumes \
  --query 'Volumes[].VolumeType' \
  --output text 2>/dev/null | tr '\t' '\n' | sort | uniq -c | sort -rn || \
  echo "  (AWS CLI not configured — skipping)"
AWSSCRIPT

chmod +x /tmp/aws_storage_audit.sh
echo "AWS audit script created at /tmp/aws_storage_audit.sh"
echo "(Run manually if you have AWS CLI configured)"
```

### Step 5: Cleanup

```bash
kind delete cluster --name storage-lab
```

### Success Criteria

You've completed this exercise when you:
- [ ] Created PVs simulating both active and orphaned states
- [ ] Ran the storage audit script and identified 3 orphaned PVs
- [ ] Calculated the monthly cost of orphaned storage ($68/month for 850Gi at gp3 rates)
- [ ] Reviewed the AWS audit script for finding unattached EBS volumes and old snapshots
- [ ] Listed at least 3 storage optimization recommendations for your environment

---

## Key Takeaways

1. **Storage costs accumulate silently** — orphaned PVs, unmanaged snapshots, and wrong volume types add up fast
2. **gp2 to gp3 is a no-brainer** — 20% cheaper with 2x baseline IOPS, zero downside
3. **Cross-AZ data transfer is the hidden Kubernetes tax** — use topology-aware routing to keep traffic local
4. **NAT Gateways are expensive** — VPC Gateway Endpoints for S3/DynamoDB are free and save hundreds monthly
5. **S3 lifecycle policies save 80-90%** — move logs and backups through storage tiers automatically

---

## Further Reading

**Articles**:
- **"Understanding AWS Data Transfer Costs"** — aws.amazon.com/blogs/architecture
- **"EBS Volume Types Explained"** — docs.aws.amazon.com/ebs/latest/userguide
- **"Kubernetes Storage Best Practices"** — cloud.google.com/architecture

**Tools**:
- **AWS Cost Explorer** — Filter by service/usage type to find storage and network waste
- **S3 Storage Lens** — Dashboard for S3 usage patterns and optimization recommendations
- **VPC Flow Logs** — Analyze network traffic patterns for cross-AZ cost optimization

**Talks**:
- **"Taming Data Transfer Costs"** — AWS re:Invent (YouTube)
- **"Storage Cost Optimization in Kubernetes"** — KubeCon (YouTube)

---

## Summary

Storage and network costs are the silent budget killers in cloud. While compute gets all the optimization attention, storage grows through orphaned volumes, unmanaged snapshots, and wrong tier choices. Network costs compound through cross-AZ traffic, NAT Gateways, and data egress. The fixes are often straightforward — migrate to gp3, add VPC endpoints, enable topology-aware routing, implement lifecycle policies — but they require awareness first. Regular storage audits and network flow analysis should be part of every FinOps practice.

---

## Next Module

Continue to [Module 1.6: FinOps Culture & Automation](../module-1.6-finops-culture/) to learn how to build organizational habits, automate cost governance, and embed FinOps into your CI/CD pipeline.

---

*"Data has mass. And mass has cost."* — Cloud networking truth
