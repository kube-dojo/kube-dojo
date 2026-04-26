---
title: "Module 6.1: Karpenter"
slug: platform/toolkits/developer-experience/scaling-reliability/module-6.1-karpenter
sidebar:
  order: 2
---

> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 55-65 minutes

## Prerequisites

Before you start, you should be comfortable with Kubernetes scheduling basics, including resource requests, node selectors, taints, tolerations, and topology spread constraints. You should also understand why platform teams use autoscaling: demand changes faster than humans can safely resize clusters by hand, and idle capacity is expensive when it repeats across every environment.

You do not need to be an AWS expert, but the examples in this module use EKS because Karpenter's most mature provider implementation is for AWS. The same mental model applies across providers: Karpenter watches unschedulable pods, reasons about their requirements, creates a cloud instance that can run them, and later removes or replaces nodes when the cluster can run more efficiently.

In this module, `kubectl` is the full command name. After the first worked example, the shorthand alias `k` is used in commands where a fast operator workflow matters. If you do not already have the alias, create it with `alias k=kubectl` in your shell.

## Learning Outcomes

After completing this module, you will be able to:

- **Compare** Karpenter's pod-driven provisioning model with Cluster Autoscaler's node-group model and justify which approach fits a given platform constraint.
- **Design** Karpenter `NodePool` and `EC2NodeClass` resources that express workload requirements, security defaults, capacity boundaries, and disruption controls.
- **Debug** pending workloads, failed `NodeClaim` objects, and unexpected node churn by reading scheduler events, Karpenter logs, and resource status fields.
- **Evaluate** spot, on-demand, architecture, availability-zone, and consolidation trade-offs for production workloads with different reliability profiles.
- **Implement** a safe scaling experiment that proves Karpenter can add capacity, place pods, and consolidate idle nodes without hiding cost or availability risk.

## Why This Module Matters

A platform engineer joins an incident bridge at 09:14 on a Monday. The payments team has a deployment stuck at half capacity, customer-facing latency is climbing, and the cluster still has "nodes available" according to the dashboard. Ten minutes later, the real shape of the problem appears: the available nodes are the wrong shape. They have spare CPU, but not enough memory; they are in the wrong availability zone for a topology constraint; and the only autoscaling group allowed to grow is pinned to an instance family that is temporarily capacity-constrained.

That incident is not caused by a lack of autoscaling. It is caused by autoscaling at the wrong abstraction level. Cluster Autoscaler can increase the desired size of a pre-declared node group, but it cannot invent a new node shape that better matches the pods waiting in the scheduler queue. When a platform team has many workload profiles, node groups multiply into a fragile planning exercise: general-purpose nodes, high-memory nodes, GPU nodes, spot nodes, on-demand nodes, Arm nodes, zonal nodes, and exception nodes for every team that does not fit the previous buckets.

Karpenter changes the operating question. Instead of asking, "Which node group should grow?" it asks, "What node would make these pending pods schedulable right now?" That difference matters because Kubernetes already knows why a pod cannot be scheduled. Karpenter takes those constraints seriously: CPU and memory requests, pod affinity, node affinity, taints, topology spread, architecture, accelerator needs, and allowed capacity types. It then calls the cloud provider directly to create capacity that satisfies the workload rather than waiting for a fixed group to scale.

This module teaches Karpenter as a production platform tool, not as a faster button for adding nodes. You will learn where the speed comes from, what the custom resources mean, how to design safe boundaries, and how to debug the places where automation can still do the wrong thing quickly. A senior platform engineer does not merely enable Karpenter; they constrain it, observe it, and make its decisions explainable to application teams, finance partners, and incident commanders.

## 1. From Node Groups to Pod-Driven Capacity

Cluster Autoscaler solves an important problem: when pods cannot schedule because the cluster lacks capacity, it can grow a node group. The hidden cost is that a node group is a pre-commitment. You decide the instance family, purchase option, labels, taints, zones, and scaling limits before the workload appears. That works well when workloads are predictable and homogeneous, but it becomes difficult when dozens of teams deploy services with different resource profiles and different reliability needs.

Karpenter starts from the pod instead. When the Kubernetes scheduler marks a pod unschedulable, Karpenter inspects the pod's constraints and groups compatible pending pods into a provisioning decision. It then searches the allowed cloud capacity options and creates a `NodeClaim`, which represents the specific node it intends to launch. The result is still a Kubernetes node, but the path to that node is more direct and more responsive to the workload's actual requirements.

```ascii
CLUSTER AUTOSCALER PATH

┌─────────────────────┐
│ Pending Pod         │
│ needs 4 CPU, 8 GiB  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Cluster Autoscaler  │
│ selects node group  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Auto Scaling Group  │
│ grows by one node   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Fixed node shape    │
│ from launch config  │
└─────────────────────┘
```

```ascii
KARPENTER PATH

┌─────────────────────┐
│ Pending Pod         │
│ needs 4 CPU, 8 GiB  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Karpenter Controller│
│ reads pod constraints│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ NodePool boundaries │
│ define allowed nodes│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ EC2 CreateFleet     │
│ launches a fit node │
└─────────────────────┘
```

The diagrams are intentionally simple because the first mental model should be simple. Cluster Autoscaler scales a known pool; Karpenter creates a node from a permitted search space. In both cases, the scheduler remains the authority that places pods. Karpenter does not bypass scheduling; it creates capacity that the scheduler can use.

The practical difference shows up when a team deploys a workload with a narrow constraint. Imagine a batch job that requests `arm64`, needs 16 GiB memory, and tolerates spot interruptions. With Cluster Autoscaler, the platform team must already have an Arm spot node group with a suitable instance shape and enough maximum size. With Karpenter, the platform team expresses the allowed categories, architecture, zones, and capacity types in a `NodePool`, and Karpenter chooses an instance type that satisfies the pending pods inside those limits.

**Pause and predict:** A pod requests `kubernetes.io/arch=arm64`, but your only `NodePool` allows `amd64` nodes. Karpenter is installed and healthy. Will it create a node, leave the pod pending, or create an `amd64` node that the scheduler later rejects? Write down your prediction before reading on.

The answer is that Karpenter should not create a node that violates the allowed requirements. The pod remains pending because the intersection between the pod's requirements and the `NodePool` requirements is empty. This is a useful failure mode: it preserves the scheduling contract instead of launching useless capacity. When debugging, you look for that empty intersection by comparing pod constraints, `NodePool` requirements, and events on the pod or `NodeClaim`.

| Feature | Cluster Autoscaler | Karpenter |
|---|---|---|
| Scaling unit | Existing node group | Individual node represented by a `NodeClaim` |
| Capacity search | Limited to configured groups | Searches allowed instance options inside `NodePool` requirements |
| Typical scale-up path | Scheduler event, autoscaler loop, group resize, provider launch | Scheduler event, Karpenter provisioning loop, provider launch |
| Workload fit | Good when node groups match workload shapes | Strong when pod requirements vary across teams |
| Operational burden | More node groups as workload profiles multiply | More policy design in `NodePool` and provider class resources |
| Cost controls | Group min, max, and purchase option planning | Limits, consolidation, disruption budgets, and capacity-type constraints |
| Failure mode | Wrong group grows or no group fits | No compatible `NodePool`, provider launch failure, or disruption blocked |
| Best use | Stable, homogeneous fleets with simple scaling needs | Mixed workloads with variable shape, architecture, and capacity preferences |

A fair comparison does not say that Cluster Autoscaler is obsolete for every cluster. Some organizations value the simplicity of a few fixed node groups, especially where workload shapes are stable and change control around instance types is strict. Karpenter becomes more compelling when the number of node groups grows because the platform is trying to model every possible workload ahead of time. It replaces much of that pre-modeling with policy: define what is allowed, then let pending pods drive the exact choice.

The senior-level design question is therefore not, "Is Karpenter faster?" The better question is, "What freedom should Karpenter have, and where must the platform set hard boundaries?" Too much freedom can surprise finance, security, or availability planning. Too little freedom turns Karpenter back into a complicated version of fixed node groups. The rest of the module builds the pieces you need to strike that balance.

## 2. Karpenter Architecture and the Scheduling Loop

Karpenter is a controller that runs inside the cluster and reconciles Kubernetes resources. It watches pending pods, `NodePool` resources, cloud-provider class resources such as `EC2NodeClass`, existing nodes, and its own `NodeClaim` resources. It then creates, updates, or removes capacity based on the current desired state. This is normal Kubernetes controller design, but the resource being controlled is expensive cloud infrastructure, so every field deserves operational attention.

```ascii
KARPENTER CONTROL LOOP

┌────────────────────────────────────────────────────────────────────┐
│ Kubernetes Cluster                                                  │
│                                                                    │
│  ┌─────────────────────┐        ┌──────────────────────────────┐   │
│  │ Scheduler           │        │ Karpenter Controller          │   │
│  │ marks pod pending   │───────▶│ watches unschedulable pods    │   │
│  └─────────────────────┘        └──────────────┬───────────────┘   │
│                                                │                   │
│                                                ▼                   │
│  ┌─────────────────────┐        ┌──────────────────────────────┐   │
│  │ NodePool            │───────▶│ Provisioning decision         │   │
│  │ allowed constraints │        │ pod needs + policy boundaries │   │
│  └─────────────────────┘        └──────────────┬───────────────┘   │
│                                                │                   │
│                                                ▼                   │
│  ┌─────────────────────┐        ┌──────────────────────────────┐   │
│  │ EC2NodeClass        │───────▶│ NodeClaim                     │   │
│  │ launch configuration│        │ one intended cloud node       │   │
│  └─────────────────────┘        └──────────────┬───────────────┘   │
│                                                │                   │
└────────────────────────────────────────────────┼───────────────────┘
                                                 │
                                                 ▼
                         ┌──────────────────────────────────────────┐
                         │ Cloud Provider API                       │
                         │ create instance, attach networking, boot │
                         └──────────────────────────────────────────┘
```

A `NodePool` answers the policy question: which kinds of nodes may Karpenter create for this class of workload? It contains requirements, labels, taints, resource limits, expiration settings, and disruption policies. If you are designing a platform interface for application teams, the `NodePool` is one of the main places where platform policy becomes visible.

An `EC2NodeClass` answers the provider question: how should AWS launch those nodes? It names the AMI family, IAM role, subnet selectors, security group selectors, block devices, metadata service settings, and tags. The separation is useful because several `NodePool` resources can share a secure provider configuration while expressing different workload constraints. For example, a `default` pool and a `batch-spot` pool might both use the same subnet and security group discovery rules, but only the batch pool allows interruption-prone spot capacity.

A `NodeClaim` is the concrete provisioning object Karpenter creates when it decides to launch a node. Treat it like a receipt and a debugging handle. If a pod remains pending after Karpenter tries to help, `NodeClaim` status often tells you whether the problem is instance selection, cloud capacity, IAM, subnet discovery, AMI discovery, or node registration. In production, operators should be comfortable reading `NodeClaim` objects before escalating to the cloud console.

| Component | Main question answered | Operator action |
|---|---|---|
| `NodePool` | What nodes are allowed for this workload class? | Tune requirements, limits, taints, labels, and disruption rules |
| `EC2NodeClass` | How should AWS launch the instance? | Configure AMIs, IAM role, networking, storage, metadata, and tags |
| `NodeClaim` | What exact node did Karpenter try to create? | Inspect status, events, selected instance type, and failure messages |
| Pending pod | What capacity does the workload need? | Check requests, selectors, affinity, tolerations, and topology constraints |
| Existing node | Can current capacity be reused or consolidated? | Inspect utilization, labels, taints, pods, and disruption blockers |

The loop has two major sides: provisioning and disruption. Provisioning adds nodes for unschedulable pods. Disruption removes or replaces nodes when they are empty, underutilized, expired, interrupted, drifted from desired configuration, or otherwise ready for controlled turnover. Many beginners only study scale-up because it is dramatic during demos, but production safety often depends more on the disruption side. A platform that can add nodes but cannot safely remove them becomes expensive. A platform that removes nodes too aggressively becomes unreliable.

```ascii
PROVISIONING AND DISRUPTION

          SCALE UP                                         SCALE DOWN / REPLACE
┌──────────────────────────┐                      ┌──────────────────────────┐
│ Pods cannot schedule     │                      │ Node empty, drifted, old,│
│ because capacity is short│                      │ interrupted, or wasteful │
└────────────┬─────────────┘                      └────────────┬─────────────┘
             │                                                 │
             ▼                                                 ▼
┌──────────────────────────┐                      ┌──────────────────────────┐
│ Karpenter creates        │                      │ Karpenter checks budgets,│
│ NodeClaim for new node   │                      │ PDBs, and policy         │
└────────────┬─────────────┘                      └────────────┬─────────────┘
             │                                                 │
             ▼                                                 ▼
┌──────────────────────────┐                      ┌──────────────────────────┐
│ Node joins and scheduler │                      │ Node is cordoned, drained│
│ places pending pods      │                      │ and terminated safely    │
└──────────────────────────┘                      └──────────────────────────┘
```

**Active check:** A team says, "Karpenter deleted our node and caused an outage." Before agreeing with that conclusion, what three Kubernetes objects would you inspect? A strong answer includes the workload's `PodDisruptionBudget`, the `NodePool` disruption policy, and the affected pod events. The node deletion might be a Karpenter decision, but the outage usually reflects a missing availability contract between the workload and the platform.

Karpenter does not remove the need for good Kubernetes hygiene. Pods still need accurate requests so Karpenter can calculate useful capacity. Deployments still need enough replicas for disruption. Services still need graceful termination behavior. Stateful systems still need storage and availability-zone design. Karpenter can make capacity more responsive, but it cannot infer a business requirement that the workload never encoded.

A useful operating habit is to trace from symptom to decision. If a pod is pending, start with `kubectl describe pod` and read the scheduler message. Then inspect matching `NodePool` requirements and any `NodeClaim` attempts. If nodes are churning, inspect `NodePool` disruption settings, events on the node, and workload disruption budgets. This disciplined path prevents the common mistake of starting in the cloud console, where you can see instances but not the Kubernetes constraints that caused them.

## 3. Designing NodePools and EC2NodeClasses

A good `NodePool` is a contract, not just a manifest. It says what the platform is willing to create automatically and what it refuses to create even when pods are waiting. That contract should be wide enough for Karpenter to find capacity and narrow enough to keep security, cost, and reliability within agreed bounds. The most common design failure is making requirements so narrow that Karpenter loses the flexibility that made it valuable.

Start with a general-purpose pool for ordinary stateless services. It should allow several instance categories, multiple sizes, multiple zones through the provider class, and both spot and on-demand only if your reliability model can tolerate that mix. It should also set hard limits because an autoscaler without limits is a billing incident waiting for a trigger. Limits are not a substitute for observability, but they are a last line of defense when an HPA, queue consumer, or load test behaves unexpectedly.

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  template:
    metadata:
      labels:
        workload-tier: general
    spec:
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64", "arm64"]
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]
        - key: karpenter.k8s.aws/instance-size
          operator: In
          values: ["large", "xlarge", "2xlarge", "4xlarge"]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
      expireAfter: 720h
  limits:
    cpu: 1000
    memory: 2000Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 2m
    budgets:
      - nodes: "10%"
      - nodes: "0"
        schedule: "0 9 * * 1-5"
        duration: 8h
```

The example allows Karpenter to search a useful set of compute, general-purpose, and memory-optimized instances. It excludes very small instances because tiny nodes often increase overhead and fragmentation for production services. It allows both `amd64` and `arm64`, which can reduce cost if workloads publish multi-architecture images. It also includes a business-hours disruption freeze, which is not always required but illustrates how platform teams can align automation with support expectations.

The matching `EC2NodeClass` should be treated like infrastructure security policy. Subnet and security group discovery should be deterministic, node storage should be encrypted, and the instance metadata service should require IMDSv2. Tags should make ownership and cost allocation visible. The provider class is also where many failed launches originate, so do not hide it from operators who are expected to debug Karpenter.

```yaml
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: default
spec:
  amiFamily: AL2023
  role: "KarpenterNodeRole-my-cluster"
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: "my-cluster"
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: "my-cluster"
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
    httpPutResponseHopLimit: 1
    httpTokens: required
  tags:
    Environment: production
    ManagedBy: karpenter
    CostCenter: platform
```

A beginner might read the two manifests as separate objects to memorize. A senior engineer reads the relationship between them. The `NodePool` says which nodes may exist for scheduling purposes; the `EC2NodeClass` says how those nodes are created in AWS. A workload never references an `EC2NodeClass` directly. It expresses pod-level requirements, and Karpenter finds a `NodePool` whose requirements can satisfy them.

Now consider specialized workloads. A GPU pool should not be a slightly modified general pool. It should use taints so ordinary pods do not consume expensive accelerator nodes, and it should require GPU-capable instance families. The workload must then opt in with tolerations and resource requests. That opt-in matters because a GPU node that runs web pods is one of the easiest ways to waste budget without noticing.

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: gpu
spec:
  template:
    metadata:
      labels:
        workload-tier: accelerator
    spec:
      requirements:
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["g", "p"]
        - key: karpenter.k8s.aws/instance-gpu-count
          operator: Gt
          values: ["0"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand"]
      taints:
        - key: nvidia.com/gpu
          value: "true"
          effect: NoSchedule
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: gpu
  limits:
    nvidia.com/gpu: 32
  disruption:
    consolidationPolicy: WhenEmpty
```

A high-memory pool has a different design pressure. It may not need a taint if ordinary pods cannot fit efficiently on the selected memory-optimized nodes, but taints are still useful when you want explicit placement. Memory-heavy workloads are also sensitive to incorrect requests. If a team requests much less memory than it actually uses, Karpenter can choose a node that looks correct at scheduling time but later experiences eviction pressure. That is not a Karpenter bug; it is an inaccurate contract between the workload and scheduler.

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: high-memory
spec:
  template:
    metadata:
      labels:
        workload-tier: memory
    spec:
      requirements:
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["r", "x"]
        - key: karpenter.k8s.aws/instance-memory
          operator: Gt
          values: ["65536"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand"]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
  limits:
    cpu: 500
    memory: 4000Gi
  disruption:
    consolidationPolicy: WhenEmpty
```

**Pause and decide:** Your platform supports a latency-sensitive checkout service and a nightly image-processing batch job. Both can run on `amd64`, but only the batch job can tolerate spot interruptions. Should you put both workloads in one `NodePool` that allows `spot` and `on-demand`, or create separate pools? A strong design separates them unless the checkout service has explicit scheduling constraints that prevent spot placement. Separation makes the reliability contract visible and reduces the chance that a critical workload lands on capacity with interruption risk.

Workload manifests complete the contract. If a pod needs a specific architecture, it must say so. If it wants to use a tainted pool, it must tolerate the taint. If it needs a topology spread, it must declare that constraint. Karpenter reacts to Kubernetes scheduling semantics, so vague workload manifests produce vague provisioning outcomes.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arm-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: arm-api
  template:
    metadata:
      labels:
        app: arm-api
    spec:
      nodeSelector:
        kubernetes.io/arch: arm64
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: arm-api
      containers:
        - name: api
          image: public.ecr.aws/nginx/nginx:1.27
          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
            limits:
              memory: "1Gi"
```

The worked example above gives Karpenter enough signal to act. If no existing node can run the pod, Karpenter must find a compatible `NodePool` that allows Arm nodes and zones that satisfy the topology requirement. If the only Arm-capable capacity is temporarily unavailable in one zone, the pod may remain pending until Karpenter finds a valid option or the constraint is relaxed. This is why platform policy and workload policy must be reviewed together.

## 4. Worked Example: Debugging a Pending Pod

A useful Karpenter troubleshooting flow begins with the pod, not the node. The pod is where the scheduler records why placement failed. If you skip that step, you risk debugging cloud capacity when the real issue is a typo in a selector, a missing toleration, or a `NodePool` that excludes the requested architecture. The following worked example shows the sequence an operator should follow before making changes.

The scenario is simple: an application team deploys a service that requests Arm nodes, but the pods remain pending. Karpenter is installed and its controller pod is running. The team assumes Karpenter is broken because no new nodes appear.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: receipt-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: receipt-worker
  template:
    metadata:
      labels:
        app: receipt-worker
    spec:
      nodeSelector:
        kubernetes.io/arch: arm64
      containers:
        - name: worker
          image: public.ecr.aws/nginx/nginx:1.27
          resources:
            requests:
              cpu: "1"
              memory: "1Gi"
```

First, inspect the pod events. This tells you whether the scheduler sees a resource shortage, a selector mismatch, a taint problem, or a topology issue. The exact message varies, but the important habit is to read it before touching Karpenter configuration.

```bash
kubectl get pods -l app=receipt-worker
kubectl describe pod -l app=receipt-worker
```

If you have the `k` alias configured, the same check is faster during an incident:

```bash
k get pods -l app=receipt-worker
k describe pod -l app=receipt-worker
```

Assume the event says no nodes match the pod's node selector and the pod is unschedulable. That alone does not prove Karpenter should create a node. Karpenter can only create nodes allowed by a matching `NodePool`. The next check is the `NodePool` requirements.

```bash
kubectl get nodepool
kubectl get nodepool default -o yaml
```

The platform finds this requirement in the `default` pool:

```yaml
requirements:
  - key: kubernetes.io/arch
    operator: In
    values: ["amd64"]
```

Now the failure is explainable. The pod requires `arm64`; the only `NodePool` allows `amd64`. Karpenter correctly refuses to launch capacity that cannot satisfy both the workload and platform constraints. The fix is not to restart Karpenter. The fix is to decide whether Arm capacity is allowed for this platform and then update or add a `NodePool` accordingly.

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: arm-general
spec:
  template:
    metadata:
      labels:
        workload-tier: arm-general
    spec:
      requirements:
        - key: kubernetes.io/arch
          operator: In
          values: ["arm64"]
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
  limits:
    cpu: 200
    memory: 400Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 2m
```

After applying a compatible pool, inspect `NodeClaim` objects. A new `NodeClaim` means Karpenter has moved from policy matching to provider launch. If the `NodeClaim` becomes ready and a node joins, the scheduler should place the pod. If it fails, the problem has moved to the cloud-provider side or node registration.

```bash
kubectl get nodeclaims
kubectl describe nodeclaim <nodeclaim-name>
kubectl get nodes -L kubernetes.io/arch,node.kubernetes.io/instance-type,karpenter.sh/capacity-type
```

A good troubleshooting note includes the decision trail. For this example, the note would say: "The pod remained pending because it required `arm64`, and the existing `default` `NodePool` allowed only `amd64`. We added an `arm-general` `NodePool` with bounded CPU and memory limits, then verified that Karpenter created a `NodeClaim` and the node joined with the expected architecture label." That kind of note is better than "Karpenter fixed" because it teaches the next responder how the system actually behaved.

**Active check:** Suppose the `NodeClaim` exists but never becomes ready, and its status mentions subnet discovery. Which resource do you inspect next: the workload Deployment, the `NodePool`, or the `EC2NodeClass`? The `EC2NodeClass` is the right next stop because subnet and security group selectors live in the provider launch configuration. The Deployment shaped the demand, and the `NodePool` allowed the node, but the provider class tells AWS how to create it.

This worked example is deliberately narrow, but the method generalizes. Start with the pending pod's scheduling reason. Check whether any `NodePool` can legally satisfy those requirements. If Karpenter creates a `NodeClaim`, inspect its status to see what happened during provider launch. If the node joins but the pod still does not schedule, return to scheduler events because a new constraint may now be visible.

## 5. Cost, Spot Capacity, and Consolidation

Karpenter can reduce waste because it is allowed to replace bad fits with better fits. That power comes from consolidation, which evaluates whether pods on current nodes could run on fewer, cheaper, or better-shaped nodes. Consolidation is not a magic cost switch. It is controlled disruption, and controlled disruption must respect workload availability, budgets, and business hours.

```ascii
CONSOLIDATION EXAMPLE

Before consolidation:

┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ Node A           │   │ Node B           │   │ Node C           │
│ m6i.xlarge       │   │ m6i.xlarge       │   │ m6i.xlarge       │
│                  │   │                  │   │                  │
│ api-1  600m CPU  │   │ api-2  600m CPU  │   │ worker 500m CPU  │
│ api-3  600m CPU  │   │                  │   │                  │
│                  │   │                  │   │                  │
│ lightly used     │   │ lightly used     │   │ lightly used     │
└──────────────────┘   └──────────────────┘   └──────────────────┘

After consolidation:

┌────────────────────────────┐
│ Replacement Node           │
│ m6i.2xlarge or similar     │
│                            │
│ api-1    api-2    api-3    │
│ worker                     │
│                            │
│ fewer nodes, less overhead │
└────────────────────────────┘
```

The example shows the idea, but production consolidation has more checks than the picture can show. Karpenter must consider whether pods can move, whether PodDisruptionBudgets allow voluntary disruption, whether the destination capacity is permitted, whether replacement cost is lower, and whether the `NodePool` budget allows a node to be disrupted now. If any of those checks block the action, consolidation waits.

A safe default for many production pools is `WhenEmptyOrUnderutilized` with a small delay and a disruption budget. The delay prevents immediate churn after short-lived pods exit. The budget prevents too many nodes from being disrupted at once. A scheduled freeze can protect high-support windows, though it may also defer savings and leave waste in place during the day.

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: production-general
spec:
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 5m
    budgets:
      - nodes: "10%"
      - nodes: "1"
        reasons:
          - "Empty"
      - nodes: "0"
        schedule: "0 8 * * 1-5"
        duration: 10h
```

Spot capacity adds a different trade-off. It can be much cheaper than on-demand capacity, but it can be interrupted. Karpenter can integrate spot into provisioning decisions and respond to interruption notices when the interruption queue is configured, but your workload still needs to behave well during termination. A service with one replica, no graceful shutdown, and no disruption budget is not made reliable by Karpenter.

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: batch-spot
spec:
  template:
    metadata:
      labels:
        workload-tier: batch
    spec:
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot"]
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]
        - key: karpenter.k8s.aws/instance-size
          operator: NotIn
          values: ["nano", "micro", "small"]
      taints:
        - key: workload-tier
          value: batch
          effect: NoSchedule
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
  limits:
    cpu: 800
    memory: 1600Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 2m
```

The workload must opt in to that pool. The toleration below is not decoration; it is the application team's acknowledgement that this job can run on batch spot capacity. For real batch jobs, also ensure checkpointing or retry behavior exists outside the manifest.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: image-thumbnailer
spec:
  backoffLimit: 4
  template:
    metadata:
      labels:
        app: image-thumbnailer
    spec:
      restartPolicy: Never
      tolerations:
        - key: workload-tier
          operator: Equal
          value: batch
          effect: NoSchedule
      terminationGracePeriodSeconds: 60
      containers:
        - name: worker
          image: public.ecr.aws/docker/library/busybox:1.36
          command: ["/bin/sh", "-c", "sleep 120"]
          resources:
            requests:
              cpu: "2"
              memory: "2Gi"
```

For long-running services, mixed spot and on-demand pools require careful placement policy. One common approach is to reserve on-demand pools for critical services and use spot pools for stateless or batch workloads that can tolerate retry. Another approach is to run a baseline of critical services on on-demand capacity and overflow onto spot only for replicas that can disappear without violating service objectives. The right answer depends on the service's error budget, traffic pattern, startup time, and dependency behavior.

Cost optimization also requires limits and alerts. `NodePool` limits prevent an unbounded scale event, but they do not explain why demand increased. You still need alerts for node count, CPU requested, pending pods, Karpenter provisioning failures, interruption frequency, and cloud spend. In a mature platform, Karpenter events become part of the capacity story, not a hidden subsystem only the platform team can see.

```yaml
spec:
  limits:
    cpu: 500
    memory: 1000Gi
```

That small fragment may be the difference between a contained incident and a costly weekend. If an HPA scales to thousands of replicas because it is reading the wrong metric, Karpenter will try to satisfy the resulting pending pods until it hits the boundary you set. The boundary should be high enough for legitimate bursts and low enough to force human review before a runaway system creates financial damage.

**Pause and evaluate:** A service has four replicas, a `PodDisruptionBudget` requiring three available replicas, and each pod takes eight minutes to become ready. Would you use aggressive underutilized consolidation during business hours? A cautious answer is no unless the service has been tested under voluntary disruption and the rollout strategy can absorb slow readiness. Karpenter may respect the disruption budget, but a system that spends long periods at minimum availability can still create operational risk.

## 6. Production Operating Model

Installing Karpenter is the easiest part of adoption. The harder part is defining an operating model that application teams can understand. If teams do not know how to request a workload shape, how to opt into spot, how to avoid expensive nodes, or how to debug pending pods, they will treat Karpenter as unpredictable infrastructure. Good platform teams publish a small number of supported patterns and explain the contract behind each one.

A practical operating model starts with a small pool catalog. You might offer `default`, `batch-spot`, `high-memory`, and `gpu` pools. Each pool should have a clear purpose, allowed workload types, capacity limits, disruption policy, and example workload manifest. Avoid creating one pool per team unless teams truly need different policies. Too many pools recreate the node-group sprawl that Karpenter was meant to reduce.

```ascii
POOL CATALOG EXAMPLE

┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ default          │   │ batch-spot       │   │ high-memory      │
│ stateless apps   │   │ retryable jobs   │   │ memory-heavy svc │
│ mixed capacity   │   │ spot only        │   │ on-demand only   │
│ moderate churn   │   │ accepts churn    │   │ conservative     │
└──────────────────┘   └──────────────────┘   └──────────────────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ Pod requirements │   │ toleration opt-in │   │ node selector or │
│ requests, spread │   │ retry semantics   │   │ workload label   │
└──────────────────┘   └──────────────────┘   └──────────────────┘
```

Observability should cover both provisioning and disruption. For provisioning, track pending pods, provisioning latency, `NodeClaim` failures, cloud capacity errors, and nodes that fail to register. For disruption, track consolidation decisions, blocked disruptions, voluntary evictions, interruption handling, and node lifetime. The goal is not to create a dashboard full of Karpenter internals; the goal is to answer two operational questions quickly: "Why did we add capacity?" and "Why did we remove or replace capacity?"

Runbooks should be scenario-based. A runbook that merely lists commands is less useful than one that starts from symptoms. For pending pods, the first section should say: inspect pod events, compare requirements to `NodePool` constraints, inspect `NodeClaim`, then inspect provider configuration. For unexpected node removal, the runbook should say: inspect node events, Karpenter events, `NodePool` disruption budgets, affected `PodDisruptionBudget` objects, and workload readiness behavior.

```bash
kubectl get events --all-namespaces --field-selector involvedObject.kind=Node
kubectl get nodeclaims
kubectl describe nodeclaim <nodeclaim-name>
kubectl logs -n kube-system -l app.kubernetes.io/name=karpenter --tail=200
kubectl get pdb --all-namespaces
```

Security review should include the node IAM role, metadata service settings, subnet selection, security group selection, AMI family, bootstrap configuration, and tagging. Karpenter is powerful because it can create infrastructure automatically. That same power means a loose provider class can spread mistakes across every new node. Treat `EC2NodeClass` changes with the same care you would apply to Terraform for a shared worker-node fleet.

Upgrade strategy matters as well. Karpenter has evolved its APIs over time, and production clusters should not treat controller upgrades as routine dependency bumps. Review release notes, test `NodePool` and provider-class compatibility in a non-production cluster, and watch for changes to disruption behavior. When possible, keep the controller highly available and avoid combining Karpenter upgrades with unrelated cluster changes. If a capacity incident occurs after a multi-change deployment, debugging becomes unnecessarily difficult.

Finally, decide what application teams own. Platform teams usually own Karpenter installation, pool definitions, provider classes, limits, and global observability. Application teams own resource requests, workload disruption budgets, architecture compatibility, graceful shutdown, and opt-in placement constraints. The line is important because Karpenter cannot compensate for a pod that requests no memory, a service with a single replica, or a batch job that cannot retry after interruption.

## Did You Know?

1. Karpenter was originally created by AWS and open-sourced to address limitations that appear when node-group-based autoscaling has to support many workload shapes. The key architectural difference is that Karpenter reasons from pending pods and directly provisions cloud instances that fit allowed constraints.

2. Karpenter can consider a broad range of EC2 instance types inside the boundaries you define, which is especially useful for spot capacity. Wider compatible requirements usually improve the chance of finding available and cost-effective capacity, while overly narrow requirements can make pending pods wait even when the cloud has plenty of other usable instances.

3. Consolidation can reduce compute waste, but it is not just "delete empty nodes." Karpenter can evaluate whether pods could be repacked onto fewer or better-shaped nodes, then uses disruption policy and Kubernetes availability controls to decide whether the change is allowed.

4. A `NodeClaim` is one of the most useful debugging objects in Karpenter. It connects the high-level policy in a `NodePool` to the concrete cloud instance Karpenter attempted to create, which makes it the natural place to inspect selected capacity, launch errors, and readiness status.

## Common Mistakes

| Mistake | Why it hurts | Better practice |
|---|---|---|
| Allowing Karpenter to scale without `NodePool` limits | A bad HPA, queue backlog, or load test can create a large bill before a human notices | Set CPU and memory limits per pool, then alert when usage approaches them |
| Making instance requirements too narrow | Karpenter loses the ability to find available or cheaper capacity, especially for spot | Allow multiple categories, sizes, architectures, or zones when the workload can tolerate them |
| Mixing critical services and interruption-tolerant jobs in one loose pool | Important workloads may land on capacity with the wrong reliability profile | Separate pools or require explicit workload constraints for spot and batch placement |
| Forgetting taints on expensive specialized pools | Ordinary pods can consume GPU or high-memory nodes and waste budget | Add taints to specialized pools and require workloads to opt in with tolerations |
| Treating consolidation as risk-free | Voluntary disruption can expose weak readiness, too few replicas, or missing `PodDisruptionBudget` objects | Use disruption budgets, conservative schedules, and workload-level availability controls |
| Debugging from the cloud console first | Cloud instances show symptoms but not the scheduler constraints that caused them | Start with pod events, then inspect `NodePool`, `NodeClaim`, and provider-class status |
| Using inaccurate CPU and memory requests | Karpenter provisions based on declared requests, so bad inputs create bad capacity decisions | Tune requests with real usage data and review outliers with application teams |
| Hiding Karpenter policy from application teams | Teams cannot predict placement, cost, or disruption behavior if pool contracts are undocumented | Publish pool purposes, opt-in examples, reliability expectations, and troubleshooting steps |

## Quiz

### Question 1

Your team deploys a new service with this pod constraint: `nodeSelector: kubernetes.io/arch: arm64`. The pods remain pending, Karpenter is healthy, and no new nodes appear. The only `NodePool` in the cluster allows `kubernetes.io/arch` values of `amd64`. What should you check and change first?

<details>
<summary>Show Answer</summary>

Start with the pod events to confirm the scheduler is reporting an architecture mismatch, then inspect the `NodePool` requirements. In this scenario, the pod requires `arm64`, but the only pool allows `amd64`, so Karpenter has no legal node it can create. The correct change is to add or update a `NodePool` that permits `arm64` within safe limits. Restarting Karpenter or manually launching an `amd64` node would not satisfy the pod's scheduling contract.

</details>

### Question 2

A batch-processing team asks to use spot capacity because their jobs can retry. A checkout service team also wants lower cost, but their service has strict latency objectives and only three replicas. Both teams currently use the same general `NodePool`, which allows `spot` and `on-demand`. What design would you recommend?

<details>
<summary>Show Answer</summary>

Create a separate spot-oriented pool for retryable batch work and require explicit opt-in through taints and tolerations. Keep the checkout service on a pool whose capacity type matches its reliability needs, usually on-demand or a carefully designed mixed strategy with strong safeguards. The key is to make the reliability contract visible in placement policy. A single loose pool makes it too easy for a critical service to land on capacity that can be interrupted.

</details>

### Question 3

During a cost review, you notice three underutilized nodes that seem like obvious consolidation candidates. Karpenter does not remove them. The workloads on those nodes each have one replica, no `PodDisruptionBudget`, and long startup times. How should you interpret Karpenter's behavior and what should you fix?

<details>
<summary>Show Answer</summary>

Do not assume Karpenter is broken. Consolidation has to respect whether pods can be moved safely, and single-replica workloads with slow readiness often create disruption risk. The fix is to improve workload availability first: add enough replicas, define appropriate `PodDisruptionBudget` objects, and verify graceful startup and shutdown behavior. After the workloads can tolerate voluntary disruption, consolidation policy can safely remove waste.

</details>

### Question 4

A `NodeClaim` is created for a pending workload, but it never becomes ready. The pod events show unschedulable capacity was needed, the `NodePool` requirements look compatible, and the `NodeClaim` status mentions security group discovery. Where do you investigate next?

<details>
<summary>Show Answer</summary>

Investigate the `EC2NodeClass`, because security group and subnet selector terms live in the provider launch configuration. The pod shaped the demand, and the `NodePool` allowed Karpenter to act, but the provider class controls how AWS launches the node. Check selector tags, IAM permissions, subnet availability, and related Karpenter controller logs.

</details>

### Question 5

An HPA bug causes a Deployment to scale from ten replicas to thousands of replicas. Karpenter begins creating nodes quickly, and cloud spend rises before the team notices. Which Karpenter configuration should have reduced the blast radius, and which observability signals should alert the platform team?

<details>
<summary>Show Answer</summary>

`NodePool` resource limits should cap the maximum CPU and memory Karpenter can provision for that pool. Those limits do not fix the HPA bug, but they prevent unlimited capacity creation. The platform should also alert on fast node-count growth, pending pods, high requested CPU, provisioning rate, spend anomalies, and usage approaching pool limits. Autoscaling needs both boundaries and visibility.

</details>

### Question 6

A GPU training job is pending. The cluster has a GPU `NodePool`, but ordinary web pods sometimes land on GPU nodes after they join. The training team complains that expensive nodes are being consumed by unrelated workloads. What is wrong with the pool design?

<details>
<summary>Show Answer</summary>

The GPU pool is missing an effective isolation contract, most commonly a taint that only GPU workloads tolerate. Add a taint such as `nvidia.com/gpu=true:NoSchedule` to the GPU `NodePool`, and require GPU workloads to include the matching toleration and GPU resource requests. This prevents ordinary pods from scheduling onto expensive accelerator nodes.

</details>

### Question 7

A platform team enables `WhenEmptyOrUnderutilized` consolidation with an aggressive delay in a production pool. The next day, an application team reports frequent voluntary restarts during business hours. The pods have valid requests and multiple replicas, but the team has no clear disruption expectations. How would you adjust the design?

<details>
<summary>Show Answer</summary>

Add a more conservative disruption policy and align it with workload availability expectations. Use `budgets` to limit how many nodes Karpenter can disrupt at once, consider a scheduled freeze during support-critical hours, and require application teams to define `PodDisruptionBudget` objects for services that need protection. Consolidation is valuable, but it should be governed by explicit reliability policy rather than left as an invisible cost optimization.

</details>

### Question 8

A service remains pending even though Karpenter created a new node. The node is ready, but the pod still does not schedule. What troubleshooting path should you follow instead of immediately changing the `NodePool`?

<details>
<summary>Show Answer</summary>

Return to the scheduler's view of the pod. Run `kubectl describe pod` and inspect events for remaining constraints such as taints, affinity, topology spread, volume zone binding, or insufficient allocatable resources after daemonsets are accounted for. A ready node only proves that Karpenter launched capacity; it does not prove the node satisfies every scheduling rule for that pod. Adjust the workload or pool only after identifying the remaining scheduler blocker.

</details>

## Hands-On Exercise

### Objective

Deploy or review a Karpenter configuration, create a workload that forces new capacity, and prove that you can explain both the scale-up and scale-down behavior. If you do not have an EKS cluster available, perform the manifest review steps locally and write the expected observations as a design exercise. The goal is not merely to run commands; the goal is to connect workload constraints to Karpenter decisions.

### Safety Notes

Use a non-production cluster for this exercise. Set conservative `NodePool` limits before creating workloads that request new nodes. Delete the test workload at the end and verify that any temporary capacity is removed or intentionally retained by policy. If your organization has a shared sandbox, confirm that spot usage, instance categories, and regional capacity choices are allowed before applying manifests.

### Step 1: Verify the Controller

Confirm that the Karpenter controller is running and that you can read its logs. This step proves the control loop is present before you test provisioning.

```bash
kubectl get pods -n kube-system -l app.kubernetes.io/name=karpenter
kubectl logs -n kube-system -l app.kubernetes.io/name=karpenter --tail=100
```

Record the controller namespace, controller pod name, and any recent errors. If the controller is not healthy, stop and fix the installation before continuing. A provisioning exercise is not meaningful when the controller is already failing.

### Step 2: Apply a Bounded General NodePool

Apply a small general-purpose pool that allows enough flexibility for Karpenter to choose capacity while keeping a hard ceiling on the experiment. Replace the `role`, discovery tag values, and region-specific provider prerequisites with the values from your cluster setup.

```yaml
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: exercise-default
spec:
  amiFamily: AL2023
  role: "KarpenterNodeRole-my-cluster"
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: "my-cluster"
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: "my-cluster"
  metadataOptions:
    httpEndpoint: enabled
    httpProtocolIPv6: disabled
    httpPutResponseHopLimit: 1
    httpTokens: required
  tags:
    Environment: sandbox
    ManagedBy: karpenter
---
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: exercise-default
spec:
  template:
    metadata:
      labels:
        exercise: karpenter
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
          values: ["large", "xlarge", "2xlarge"]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: exercise-default
  limits:
    cpu: 20
    memory: 80Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
```

Apply the manifest from a file so your shell history preserves what you tested.

```bash
kubectl apply -f karpenter-exercise.yaml
kubectl get nodepool exercise-default -o yaml
kubectl get ec2nodeclass exercise-default -o yaml
```

### Step 3: Create a Workload That Needs Capacity

Create a Deployment with resource requests large enough to require new capacity in your sandbox cluster. Adjust the replica count downward if your environment is very small, but keep the requests explicit so Karpenter has a real scheduling signal.

```yaml
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
      nodeSelector:
        kubernetes.io/arch: amd64
      containers:
        - name: pause
          image: public.ecr.aws/eks-distro/kubernetes/pause:3.7
          resources:
            requests:
              cpu: "1"
              memory: "1Gi"
```

Apply the workload and watch the scheduling path. Keep one terminal on pods, one on `NodeClaim` objects, and one on Karpenter logs if possible.

```bash
kubectl apply -f inflate.yaml
kubectl get pods -l app=inflate -w
kubectl get nodeclaims -w
kubectl logs -n kube-system -l app.kubernetes.io/name=karpenter -f
```

### Step 4: Explain the Provisioning Decision

After the pods run, gather the evidence that explains what happened. This is the part that turns the exercise from a demo into operator practice.

```bash
kubectl get nodes -L kubernetes.io/arch,node.kubernetes.io/instance-type,karpenter.sh/capacity-type,topology.kubernetes.io/zone
kubectl get nodeclaims
kubectl describe nodeclaim <nodeclaim-name>
kubectl describe pod -l app=inflate
```

Write a short note that answers these questions in your own words. Which pod requirement forced new capacity? Which `NodePool` matched the workload? Which instance type or capacity type did Karpenter choose? Did the chosen node satisfy the labels and architecture you expected? If the answer is not clear from your evidence, collect more events before moving on.

### Step 5: Trigger and Observe Consolidation

Scale the workload down and observe what happens to the node. Depending on your cluster's daemonsets, disruption settings, and timing, the node may disappear quickly or after the configured delay. If it does not disappear, inspect why before changing policy.

```bash
kubectl scale deployment inflate --replicas=0
kubectl get pods -l app=inflate
kubectl get nodes -w
kubectl get events --all-namespaces --field-selector involvedObject.kind=Node
```

If the node remains, inspect Karpenter logs and node details. Common reasons include non-daemonset pods still running, disruption budgets blocking movement, the node not being considered underutilized yet, or a consolidation policy that only removes empty nodes.

```bash
kubectl describe node <node-name>
kubectl logs -n kube-system -l app.kubernetes.io/name=karpenter --tail=200
```

### Step 6: Break One Constraint on Purpose

Modify the workload to request an architecture your exercise pool does not allow, such as `arm64` when the pool allows only `amd64`. Apply the change and predict the result before you observe it.

```yaml
spec:
  template:
    spec:
      nodeSelector:
        kubernetes.io/arch: arm64
```

Now inspect the pod events and verify that the failure is explainable from the mismatch between workload constraints and `NodePool` requirements.

```bash
kubectl apply -f inflate.yaml
kubectl describe pod -l app=inflate
kubectl get nodeclaims
```

Do not fix this by making random changes. State the exact policy decision: either Arm nodes are not allowed in this sandbox pool, or the platform should add a bounded Arm pool for workloads that need that architecture.

### Step 7: Clean Up

Remove the workload and the exercise Karpenter resources when you are done. Watch the cluster until temporary capacity is gone or until you can explain why it remains.

```bash
kubectl delete deployment inflate
kubectl delete nodepool exercise-default
kubectl delete ec2nodeclass exercise-default
kubectl get nodeclaims
kubectl get nodes -L exercise
```

### Success Criteria

- [ ] Karpenter controller health was verified before the provisioning test.
- [ ] A bounded `NodePool` and matching `EC2NodeClass` were applied or reviewed.
- [ ] A workload with explicit resource requests forced a clear scheduling decision.
- [ ] At least one `NodeClaim` was inspected and connected to the pending workload.
- [ ] The provisioned node's labels, architecture, instance type, and capacity type were checked.
- [ ] Consolidation or non-consolidation was explained using events, logs, or policy.
- [ ] A deliberate constraint mismatch was diagnosed from pod events and `NodePool` requirements.
- [ ] Cleanup was completed, or remaining capacity was explained by a specific policy or workload.

### Bonus Challenge

Design two production-ready pools on paper: one for latency-sensitive services and one for retryable batch jobs. For each pool, specify allowed capacity types, instance categories, disruption policy, limits, taints, and the workload fields teams must set to use it correctly. Then compare the two designs and explain which risks each pool accepts and which risks it refuses.

## Next Module

Continue to [Module 6.2: KEDA](../module-6.2-keda/) to learn how event-driven workload autoscaling complements Karpenter's node provisioning model. KEDA changes the number of pods based on external demand signals; Karpenter creates the node capacity those pods may need after the scheduler cannot place them.
