---
title: "Module 6.1: Karpenter"
slug: platform/toolkits/developer-experience/scaling-reliability/module-6.1-karpenter
sidebar:
  order: 2
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45-50 minutes

## Overview

Cluster Autoscaler was fine. Karpenter is better. Instead of scaling node groups, Karpenter provisions individual nodes matched to pending pod requirements—in seconds, not minutes. This module covers Karpenter's architecture, NodePools, and strategies for efficient autoscaling.

**What You'll Learn**:
- Karpenter architecture and how it differs from Cluster Autoscaler
- NodePools and NodeClasses configuration
- Consolidation and cost optimization
- Multi-architecture and spot instance strategies

**Prerequisites**:
- Kubernetes scheduling concepts
- [SRE Discipline](../../disciplines/core-platform/sre/) — Capacity planning basics
- Cloud provider fundamentals (EC2, instance types)

---

## Why This Module Matters

Cluster Autoscaler thinks in node groups. "Need more capacity? Add another node from this pre-defined group." Karpenter thinks in pods. "This pod needs 4 CPU, 8GB RAM, ARM64, and GPU? I'll provision exactly that." The result: faster scaling, better bin-packing, and lower costs.

> 💡 **Did You Know?** Karpenter was created by AWS and open-sourced in 2021. It can provision a node in under 60 seconds, compared to 5-10 minutes with Cluster Autoscaler. The difference is architectural: Cluster Autoscaler triggers ASG scaling and waits; Karpenter directly calls EC2 APIs to create instances.

---

## Karpenter vs Cluster Autoscaler

```
CLUSTER AUTOSCALER (OLD WAY)
════════════════════════════════════════════════════════════════════

1. Pod pending → scheduler can't place it
2. Cluster Autoscaler detects pending pod
3. CA increases desired count in ASG
4. ASG launches new node (from fixed instance type)
5. Node joins cluster
6. Pod scheduled

Time: 5-10 minutes
Limitation: Must pre-define node groups
Problem: Instance type might not match pod needs

═══════════════════════════════════════════════════════════════════

KARPENTER (NEW WAY)
════════════════════════════════════════════════════════════════════

1. Pod pending → scheduler can't place it
2. Karpenter detects pending pod immediately
3. Karpenter analyzes pod requirements:
   - CPU/memory requests
   - Node selectors
   - Tolerations
   - Topology constraints
4. Karpenter selects optimal instance type
5. Karpenter calls EC2 API directly → node launches
6. Node joins cluster
7. Pod scheduled

Time: < 60 seconds
Advantage: Right-sized instances for actual needs
Benefit: No node groups to manage
```

### Feature Comparison

| Feature | Cluster Autoscaler | Karpenter |
|---------|-------------------|-----------|
| **Scale-up time** | 5-10 minutes | < 60 seconds |
| **Instance selection** | Pre-defined node groups | Dynamic, per-pod |
| **Bin-packing** | Basic | Intelligent |
| **Spot handling** | Separate ASGs | Native, mixed |
| **Consolidation** | Manual | Automatic |
| **Multi-arch** | Separate node groups | Native |
| **GPU workloads** | Separate node groups | Native |

---

## Architecture

```
KARPENTER ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                      KUBERNETES CLUSTER                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    KARPENTER CONTROLLER                   │  │
│  │                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │  Provisioner│  │ Consolidator│  │  Disruption │      │  │
│  │  │  (scale up) │  │ (optimize)  │  │  (scale down)│      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  │                                                           │  │
│  └───────────────────────────┬──────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────▼──────────────────────────────┐  │
│  │                      KUBERNETES API                       │  │
│  │                                                           │  │
│  │  NodePool ─────▶ "What constraints?"                     │  │
│  │  EC2NodeClass ──▶ "How to launch?"                       │  │
│  │  Pending Pods ──▶ "What's needed?"                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         AWS EC2 API                              │
│                                                                  │
│  Karpenter calls CreateFleet → EC2 launches instance            │
│  Instance registers with cluster via bootstrap script           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose |
|-----------|---------|
| **NodePool** | Defines constraints and requirements for nodes (replaces old Provisioner) |
| **EC2NodeClass** | AWS-specific launch configuration (AMI, subnets, security groups) |
| **NodeClaim** | Represents a request for a node (created by Karpenter) |

---

## Installation

```bash
# Set environment variables
export KARPENTER_NAMESPACE="kube-system"
export KARPENTER_VERSION="1.0.1"
export CLUSTER_NAME="my-cluster"
export AWS_PARTITION="aws"
export AWS_REGION="us-west-2"
export AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

# Install Karpenter
helm upgrade --install karpenter oci://public.ecr.aws/karpenter/karpenter \
  --version "${KARPENTER_VERSION}" \
  --namespace "${KARPENTER_NAMESPACE}" \
  --create-namespace \
  --set "settings.clusterName=${CLUSTER_NAME}" \
  --set "settings.interruptionQueue=${CLUSTER_NAME}" \
  --set controller.resources.requests.cpu=1 \
  --set controller.resources.requests.memory=1Gi \
  --set controller.resources.limits.cpu=1 \
  --set controller.resources.limits.memory=1Gi \
  --wait

# Verify installation
kubectl get pods -n kube-system -l app.kubernetes.io/name=karpenter
kubectl logs -n kube-system -l app.kubernetes.io/name=karpenter -f
```

---

## NodePool Configuration

### Basic NodePool

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      requirements:
        # Instance types Karpenter can choose from
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64", "arm64"]
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]  # Compute, General, Memory optimized
        - key: karpenter.k8s.aws/instance-size
          operator: In
          values: ["medium", "large", "xlarge", "2xlarge"]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
      expireAfter: 720h  # 30 days - nodes replaced to stay fresh
  limits:
    cpu: 1000        # Max 1000 vCPUs in this NodePool
    memory: 2000Gi   # Max 2000 GB memory
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
```

### EC2NodeClass

```yaml
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: default
spec:
  amiFamily: AL2023  # Amazon Linux 2023
  role: "KarpenterNodeRole-${CLUSTER_NAME}"
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: "${CLUSTER_NAME}"
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: "${CLUSTER_NAME}"
  blockDeviceMappings:
    - deviceName: /dev/xvda
      ebs:
        volumeSize: 100Gi
        volumeType: gp3
        encrypted: true
        deleteOnTermination: true
  metadataOptions:
    httpEndpoint: enabled
    httpProtocolIPv6: disabled
    httpPutResponseHopLimit: 1  # IMDSv2 requirement
    httpTokens: required        # IMDSv2 requirement
  tags:
    Environment: production
    ManagedBy: karpenter
```

> 💡 **Did You Know?** Karpenter can choose from all 500+ EC2 instance types automatically. It calculates the best price-performance ratio for your specific workload requirements. You don't need to manually select m5.large vs m5.xlarge—Karpenter does the math in real-time based on current pricing.

---

## Workload-Specific Scaling

### GPU Workloads

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: gpu
spec:
  template:
    spec:
      requirements:
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["g", "p"]  # GPU instance families
        - key: karpenter.k8s.aws/instance-gpu-count
          operator: Gt
          values: ["0"]
        - key: nvidia.com/gpu
          operator: Exists
      taints:
        - key: nvidia.com/gpu
          effect: NoSchedule
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: gpu
  limits:
    nvidia.com/gpu: 100
```

### ARM64 Workloads (Graviton)

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: graviton
spec:
  template:
    spec:
      requirements:
        - key: kubernetes.io/arch
          operator: In
          values: ["arm64"]
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]  # Graviton versions of these
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
```

### High-Memory Workloads

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: high-memory
spec:
  template:
    spec:
      requirements:
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["r", "x"]  # Memory-optimized
        - key: karpenter.k8s.aws/instance-memory
          operator: Gt
          values: ["32768"]  # > 32GB memory
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
```

---

## Cost Optimization

### Spot Instance Strategy

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: spot-first
spec:
  template:
    spec:
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
        # Wide instance type selection = better spot availability
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]
        - key: karpenter.k8s.aws/instance-size
          operator: NotIn
          values: ["nano", "micro", "small"]  # Too small
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
  # Karpenter prefers spot when available
  # Falls back to on-demand if spot unavailable
```

### Consolidation

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  disruption:
    # Options: WhenEmpty, WhenEmptyOrUnderutilized
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m  # Wait before consolidating

    # Budgets limit disruption rate
    budgets:
    - nodes: "10%"  # Max 10% of nodes disrupted at once
    - nodes: "0"
      schedule: "0 9 * * 1-5"  # No disruption 9 AM weekdays
      duration: 8h             # For 8 hours
```

### How Consolidation Works

```
CONSOLIDATION EXAMPLE
════════════════════════════════════════════════════════════════════

BEFORE CONSOLIDATION:
─────────────────────────────────────────────────────────────────
Node 1 (m5.xlarge)     Node 2 (m5.xlarge)     Node 3 (m5.xlarge)
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ Pod A (2 CPU)    │   │ Pod C (1 CPU)    │   │ Pod E (1 CPU)    │
│ Pod B (1 CPU)    │   │                  │   │                  │
│                  │   │                  │   │                  │
│ (4 CPU total)    │   │ (4 CPU total)    │   │ (4 CPU total)    │
│ 3 CPU used       │   │ 1 CPU used       │   │ 1 CPU used       │
└──────────────────┘   └──────────────────┘   └──────────────────┘

Total: 12 CPU capacity, 5 CPU used (42% utilization)

AFTER CONSOLIDATION:
─────────────────────────────────────────────────────────────────
Node 1 (m5.xlarge)
┌──────────────────┐
│ Pod A (2 CPU)    │
│ Pod B (1 CPU)    │
│ Pod C (1 CPU)    │
│ Pod E (1 CPU)    │
│ (4 CPU total)    │
│ 5 CPU used       │   Nodes 2 and 3 TERMINATED
└──────────────────┘

Total: 4 CPU capacity, 5 CPU used → switch to m5.2xlarge
Final: 8 CPU capacity, 5 CPU used (63% utilization)

COST SAVINGS: 3 nodes → 1 node = 66% reduction
```

> 💡 **Did You Know?** Karpenter's consolidation can save 30-50% on compute costs for typical workloads. It continuously evaluates whether pods could be repacked more efficiently and automatically replaces underutilized nodes. This runs every 15 seconds by default.

---

## Handling Spot Interruptions

```yaml
# Karpenter handles spot interruptions automatically
# when settings.interruptionQueue is configured

# EC2 sends interruption notice (2 min warning)
# Karpenter cordons node
# Karpenter drains pods gracefully
# New node provisioned for displaced pods

# Your pods should handle graceful termination:
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      terminationGracePeriodSeconds: 60  # Time to shutdown gracefully
      containers:
      - name: app
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 30"]  # Drain connections
```

> 💡 **Did You Know?** Karpenter was built after AWS spent years running Cluster Autoscaler at scale and understanding its limitations. The key insight was that Cluster Autoscaler works at the node group level, but Karpenter works at the pod level—it looks at what pods need and provisions exactly the right nodes. This "just-in-time" approach is why provisioning is so fast.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Too narrow instance types | Spot unavailable, higher costs | Allow many instance types |
| No CPU/memory limits on NodePool | Runaway scaling | Set reasonable limits |
| No disruption budgets | Consolidation causes outages | Use budgets to limit churn |
| Single AZ | AZ failure = total outage | Multi-AZ subnets in EC2NodeClass |
| No taints for specialized nodes | Wrong pods land on GPU nodes | Use taints + tolerations |
| IMDSv1 enabled | Security risk | Use httpTokens: required |

---

## War Story: The $50,000 Weekend

*A team deployed Karpenter without CPU limits. A bug in their HPA created infinite scaling. Monday morning: 2,000 nodes, $50,000 bill.*

**What went wrong**:
1. HPA misconfigured with wrong metric
2. HPA kept requesting more replicas
3. Karpenter dutifully provisioned nodes
4. No alerts on node count or spend

**The fix**:
```yaml
spec:
  limits:
    cpu: 500      # Hard limit on total CPUs
    memory: 1000Gi

# Plus alerts:
# - Alert when node count > threshold
# - Alert when hourly spend > threshold
# - Alert when scaling rate > threshold
```

---

## Quiz

### Question 1
Why is Karpenter faster than Cluster Autoscaler?

<details>
<summary>Show Answer</summary>

**Cluster Autoscaler**:
1. Detects pending pods
2. Increases ASG desired count
3. ASG calls EC2 to launch from launch template
4. EC2 provisions instance
5. Instance bootstraps, joins cluster

Steps 2-3 involve ASG reconciliation loops = slow

**Karpenter**:
1. Detects pending pods
2. Calls EC2 CreateFleet API directly
3. EC2 provisions instance
4. Instance bootstraps, joins cluster

Karpenter bypasses ASG entirely = faster

</details>

### Question 2
What's the difference between a NodePool and EC2NodeClass?

<details>
<summary>Show Answer</summary>

**NodePool** (cloud-agnostic):
- What kind of nodes are acceptable
- Instance requirements (CPU, memory, arch)
- Capacity limits
- Disruption policies
- Taints and labels

**EC2NodeClass** (AWS-specific):
- How to launch nodes on AWS
- AMI family and version
- Subnets and security groups
- IAM role
- Block device configuration
- User data/bootstrap scripts

One NodePool references one EC2NodeClass. Multiple NodePools can share an EC2NodeClass.

</details>

### Question 3
How does consolidation save money?

<details>
<summary>Show Answer</summary>

Consolidation identifies underutilized nodes and repacks pods:

1. **Detects** nodes with low utilization
2. **Simulates** where pods could move
3. **Cordons** the underutilized node
4. **Drains** pods to other nodes
5. **Terminates** the empty node

Also:
- Replaces larger nodes with smaller ones when possible
- Combines multiple small nodes into fewer large ones
- Respects disruption budgets to avoid outages

Typical savings: 30-50% compute cost reduction

</details>

---

## Hands-On Exercise

### Objective
Deploy Karpenter and observe dynamic node provisioning.

### Environment Setup

```bash
# For this exercise, you need an EKS cluster
# Follow AWS documentation to set up Karpenter prerequisites:
# https://karpenter.sh/docs/getting-started/

# Create basic NodePool
kubectl apply -f - <<EOF
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      requirements:
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m"]
        - key: karpenter.k8s.aws/instance-size
          operator: In
          values: ["medium", "large", "xlarge"]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
  limits:
    cpu: 100
    memory: 200Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 30s
EOF
```

### Tasks

1. **Watch Karpenter logs**:
   ```bash
   kubectl logs -n kube-system -l app.kubernetes.io/name=karpenter -f
   ```

2. **Create workload that needs new node**:
   ```bash
   kubectl apply -f - <<EOF
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: inflate
   spec:
     replicas: 5
     selector:
       matchLabels:
         app: inflate
     template:
       metadata:
         labels:
           app: inflate
       spec:
         containers:
         - name: inflate
           image: public.ecr.aws/eks-distro/kubernetes/pause:3.7
           resources:
             requests:
               cpu: "1"
               memory: "1Gi"
   EOF
   ```

3. **Observe node provisioning**:
   ```bash
   kubectl get nodes -w
   # Watch for new node to appear
   ```

4. **Check NodeClaim**:
   ```bash
   kubectl get nodeclaims
   kubectl describe nodeclaim <name>
   ```

5. **Scale down and observe consolidation**:
   ```bash
   kubectl scale deployment inflate --replicas=0
   # Watch nodes get consolidated/terminated
   kubectl get nodes -w
   ```

### Success Criteria
- [ ] Karpenter controller running
- [ ] NodePool created successfully
- [ ] New node provisioned in < 2 minutes
- [ ] Node has correct labels (instance type, capacity type)
- [ ] Consolidation removes empty node after scale-down

### Bonus Challenge
Create a separate NodePool for ARM64/Graviton instances and deploy a workload that specifically requests ARM64.

---

## Further Reading

- [Karpenter Documentation](https://karpenter.sh/)
- [Karpenter Best Practices](https://aws.github.io/aws-eks-best-practices/karpenter/)
- [Instance Type Selection](https://karpenter.sh/docs/concepts/instance-types/)

---

## Next Module

Continue to [Module 6.2: KEDA](module-6.2-keda/) to learn event-driven autoscaling for workloads based on metrics, queues, and custom triggers.

---

*"The best infrastructure is invisible. Karpenter makes capacity planning disappear."*
