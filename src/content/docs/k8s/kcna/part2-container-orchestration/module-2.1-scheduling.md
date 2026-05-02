---
title: "Module 2.1: Scheduling"
slug: k8s/kcna/part2-container-orchestration/module-2.1-scheduling
sidebar:
  order: 2
revision_pending: false
---

# Module 2.1: Scheduling

> **Complexity**: `[MEDIUM]` - Orchestration concepts
>
> **Time to Complete**: 60-75 minutes
>
> **Prerequisites**: Part 1 (Kubernetes Fundamentals), basic Pod and Deployment YAML, and access to a Kubernetes 1.35 or newer cluster

## Learning Outcomes

After completing this module, you will be able to perform these scheduling tasks from evidence rather than intuition, which means each outcome connects to a concrete event, manifest choice, quiz scenario, or lab action:

1. **Diagnose** Pending Pods by interpreting `FailedScheduling` events, node capacity, and resource requests.
2. **Design** highly available replicas with Pod anti-affinity and topology spread constraints.
3. **Compare** node affinity with taints and tolerations for dedicated hardware node pools.
4. **Implement** resource requests and limits that support predictable scheduling and runtime behavior.
5. **Evaluate** scheduler placement choices for latency, utilization, availability, and operational recovery.

## Why This Module Matters

During the 2020 holiday season, a large global retailer hit a failure pattern that looked, at first, like ordinary traffic pressure. Checkout traffic climbed, the Horizontal Pod Autoscaler created more replicas, and the platform team expected the cluster to absorb the surge. Instead, hundreds of checkout Pods stayed in `Pending` while the existing replicas grew hotter, restarted under memory pressure, and left customers unable to complete purchases during a peak shopping window. The finance team later estimated that the interruption cost about fifteen million dollars in lost revenue and manual recovery work, but the underlying machines were not physically exhausted.

The root cause was a scheduling misunderstanding. Application teams had set CPU requests equal to generous CPU limits because that felt safe, and the scheduler treated those requests as reservations against node allocatable capacity. The nodes were often using only a small fraction of their real CPU, but they were full on paper, so the kube-scheduler correctly refused to bind new Pods. Nothing was broken in the scheduler, the kubelet, or the cloud provider; the system was obeying a contract that the teams had written without understanding the operational consequences.

Scheduling is the control-plane decision that turns a Pod record into a workload running on a real node. It decides whether a replica can launch during an incident, whether a database survives a node failure, whether expensive GPU nodes stay reserved for the team that needs them, and whether a cluster scales efficiently or wastes capacity. In this module, you will learn how the kube-scheduler filters, scores, and binds Pods, then you will practice reading scheduling failures as evidence rather than guessing at causes.

For command examples, this module uses `k` as the local alias for `kubectl`, which mirrors the short form many cluster operators use during troubleshooting. You can create it in your shell with `alias k=kubectl`, and every `k get`, `k describe`, `k apply`, or `k taint` command shown here is just the standard `kubectl` command through that alias. The concepts apply to Kubernetes 1.35 and newer, including the stable scheduling primitives that KCNA candidates are expected to recognize.

## The Anatomy of the Kube-Scheduler

A Pod is only a desired record until it is bound to a node. When you create a Deployment, the Deployment controller creates or updates a ReplicaSet, and the ReplicaSet controller creates Pod objects that usually begin with an empty `spec.nodeName`. Those Pod objects exist in the API server, but no container has started yet, no image has been pulled, and no kubelet has accepted responsibility for them. Scheduling is the moment when Kubernetes chooses the node that should make the desired state real.

The kube-scheduler is a control-plane component that watches for Pods without an assigned node. For each unscheduled Pod, it runs a scheduling cycle that evaluates the cluster against the Pod's requirements, preferences, and policy constraints. That cycle is not a single "find the least busy node" operation. It is a layered decision that first removes impossible nodes, then ranks the feasible nodes, then writes a binding decision back through the API server so the selected kubelet can start the runtime work.

The filtering phase is the hard gate. A node can have plenty of spare CPU in a dashboard and still fail filtering if the Pod asks for a label the node lacks, a taint the Pod does not tolerate, a host port already in use, or more requested memory than the node has available on paper. Filtering is deliberately strict because placing a Pod on a node that cannot satisfy its contract would create a later failure that is harder to diagnose. A `Pending` Pod is often safer than a Pod that starts on the wrong hardware and fails under load.

The scheduler asks a practical sequence of questions during filtering. Does the node have enough unreserved CPU and memory for the Pod's requests? Do the node labels match any required node affinity or `nodeSelector` rules? Are required volumes compatible with the node's topology, such as the same availability zone as a zonal persistent disk? Does the Pod tolerate every relevant taint on the node? If a node fails any hard requirement, the scheduler excludes it from the rest of that cycle.

Once filtering leaves a feasible set, scoring chooses the best candidate among the survivors. Scoring is where soft preferences matter: nodes with better resource balance can score higher, nodes that already have the requested image may start the Pod faster, and nodes matching preferred affinity rules can receive additional weight. This is why scheduling rules come in hard and soft forms. Hard rules protect correctness, while soft rules express preferences that should improve placement without turning normal capacity pressure into an outage.

The final binding step is easy to overlook because it is not where containers start. The scheduler submits a binding decision through the API server, which sets the Pod's `spec.nodeName` to the winning node. The kubelet on that node watches the API server, sees a Pod assigned to itself, and then pulls images, configures networking, mounts volumes, and asks the container runtime to start containers. If you remember that separation, troubleshooting becomes clearer: the scheduler decides placement, while kubelet and runtime events explain what happens after placement.

```text
+-----------------------------------------------------------------------+
|                   THE SCHEDULING ALGORITHM                            |
+-----------------------------------------------------------------------+
|                                                                       |
|  1. WATCH: kube-scheduler sees Pod with no nodeName                   |
|                                                                       |
|  2. FILTERING (Hard Constraints)                                      |
|     Node A: Fails (Insufficient Memory)                               |
|     Node B: Passes                                                    |
|     Node C: Fails (Missing required label)                            |
|     Node D: Passes                                                    |
|                                                                       |
|  3. SCORING (Soft Preferences on Feasible Nodes)                      |
|     Node B:                                                           |
|       - Image already cached: +20 points                              |
|       - High available CPU:   +50 points                              |
|       Total Score: 70                                                 |
|                                                                       |
|     Node D:                                                           |
|       - Image not cached:       0 points                              |
|       - Very high avail CPU:  +90 points                              |
|       Total Score: 90  <--- WINNER                                    |
|                                                                       |
|  4. BINDING: Scheduler tells API server to assign Pod to Node D       |
|                                                                       |
|  5. EXECUTION: Kubelet on Node D sees assignment and starts Pod       |
|                                                                       |
+-----------------------------------------------------------------------+
```

Pause and predict: if a cluster has hundreds of nodes, should the scheduler spend equal effort scoring every possible node for every new Pod, or should it stop once it has enough feasible candidates to make a good decision? The real scheduler balances placement quality against scheduling latency, which matters when a controller creates many replacement Pods during an incident. A perfect decision that arrives too late can be operationally worse than a good decision that arrives quickly and keeps the rollout moving.

A useful mental model is airport gate assignment. Filtering removes gates that physically cannot accept the aircraft because the gate is too small, closed, or assigned to another airline's restricted operation. Scoring chooses among the remaining gates based on convenience, taxi time, and operational preference. Binding is the official assignment that tells the ground crew where to prepare, but the assignment itself does not unload passengers; it merely hands execution to the team responsible for that gate.

War Story: a payments team once blamed "slow Kubernetes" because replacement Pods took several minutes to appear during a database failover drill. The actual `FailedScheduling` events showed that every node matching the database affinity rule also carried a maintenance taint that the replacement Pods did not tolerate. Once the team saw scheduling as a filter-and-score pipeline, they stopped restarting controllers and fixed the conflicting placement contract instead. The cluster had been giving them the answer the whole time.

There is one more practical implication for operators: scheduling is repeatable enough to diagnose, but dynamic enough that timing still matters. A Pod may fail scheduling at noon because every matching node is full, then schedule successfully two minutes later when another rollout terminates old replicas and frees requested capacity. That does not make the earlier event wrong. It means the scheduler made a decision from the cluster snapshot available in that cycle, then tried again when cluster state changed. Treat events as time-stamped evidence, not permanent verdicts.

## Resource Requests and Limits: The Foundation of Placement

Resource requests are the scheduler's currency. A CPU request says, "reserve at least this much CPU capacity for placement," and a memory request says the same for memory. The scheduler compares those requests with node allocatable capacity, which is node capacity after Kubernetes and operating system reservations are removed. It then subtracts the requests of Pods already assigned to the node, not the real-time usage shown in a monitoring dashboard.

That paper-reservation model is the reason resource sizing has such a large effect on reliability and cost. If a node has four allocatable CPU cores and four existing Pods each requested one full core, the scheduler treats the node as full for CPU even if all four Pods are idle. This behavior is not a bug. Kubernetes made a promise to the running Pods when it scheduled them, and breaking that promise because a graph is quiet right now would make overloads unpredictable.

Requests also influence Quality of Service classes and eviction behavior, but the KCNA-level scheduling lesson is straightforward: requests decide whether a Pod can be placed. If you omit requests, you may get a Pod that schedules easily but becomes the first victim during node pressure. If you overstate requests, you may get a Pod that is protected on paper but impossible to place at scale. Good requests come from measurement, load testing, and iteration, not from copying the highest value that made an outage feel less likely.

Limits serve a different purpose. The scheduler does not use a CPU limit as the reservation unless admission defaults or namespace policies copy limits into requests. At runtime, the kubelet and Linux enforce limits after the Pod has already been placed. CPU is compressible, so exceeding a CPU limit usually throttles the process and makes it slower. Memory is incompressible, so exceeding a memory limit can trigger an Out Of Memory kill, restarting the container and possibly causing a `CrashLoopBackOff`.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-demonstration-pod
spec:
  containers:
  - name: heavy-processing-app
    image: custom-processor:v2
    resources:
      requests:
        memory: "1Gi"
        cpu: "500m"
      limits:
        memory: "2Gi"
        cpu: "1000m"
```

In this Pod, the scheduler only needs a node with at least one gibibyte of unreserved memory and half a CPU core available in allocatable capacity. After the Pod starts, the container can burst up to the memory and CPU limits if the node can supply them, but the consequences differ when it crosses those boundaries. CPU pressure produces throttling and latency. Memory overage produces termination, which is why memory limits that are too low can convert a schedulable Pod into a runtime failure loop.

Before running this in a lab, predict which failure you would see first if the Pod requested `500m` CPU but had a `50Mi` memory limit while the process needed `500Mi` to initialize. The scheduler would probably place the Pod because the request is modest, but the kubelet would later report repeated restarts after the process exceeded the memory limit. Scheduling success and runtime health are related, but they are not the same signal.

For operators, the practical diagnostic move is to compare three numbers: node allocatable capacity, total requested capacity already assigned to that node, and the new Pod's requests. `k describe node <node-name>` gives allocatable values and a summary of allocated requests, while `k describe pod <pod-name>` shows the exact scheduling event if placement failed. When a `Pending` Pod says "Insufficient cpu" despite low real CPU use, the scheduler is telling you that reservations, not usage, exhausted the placement budget.

Resource sizing also affects autoscaling. A cluster autoscaler can add nodes when Pods are unschedulable because of resource shortage, but excessive requests cause it to buy more capacity than the application actually needs. Under-requesting has the opposite risk: Pods pack densely, appear cheap, and then fight at runtime when traffic arrives. The scheduler is only as honest as the requests you give it, so accurate requests are both a reliability practice and a cost-control practice.

Namespace policy often shapes this behavior before application teams notice it. LimitRanges can default requests or limits, and ResourceQuotas can reject Pods that omit required resource fields. Those policies are useful guardrails, but they should be documented because they change what the scheduler sees. When a manifest does not include a request, do not assume the scheduler sees zero. Check the admitted Pod after creation, because admission controllers may have filled in defaults that alter placement.

## Directing Traffic: Node Selectors and Affinity

Resource capacity is rarely enough information to place production workloads. Some Pods need GPU devices, high-IOPS disks, kernel features, compliance zones, or network proximity to a dependent service. Kubernetes represents those node facts as labels, and scheduling rules let a Pod require or prefer nodes with matching labels. The important distinction is whether the rule is a hard requirement that filters nodes or a soft preference that changes scoring.

The simplest mechanism is `nodeSelector`, which matches exact key-value labels. If a Pod has `nodeSelector: {disktype: ssd}`, every eligible node must have that exact label. The simplicity is useful for demos and very stable environments, but it gives you only equality matching and logical AND. It cannot express "zone A or zone B," "prefer NVMe but fall back to standard disks," or "avoid nodes with this label." When a `nodeSelector` is too strict, the Pod stays `Pending` even if a nearby acceptable alternative exists.

Node affinity is the more expressive form. `requiredDuringSchedulingIgnoredDuringExecution` is a hard filter, similar in consequence to `nodeSelector` but much more flexible because it supports operators such as `In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, and `Lt`. `preferredDuringSchedulingIgnoredDuringExecution` is a scoring preference with weights, which means a node can become more attractive without becoming mandatory. That split lets you reserve hard rules for correctness and use preferences for optimization.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: advanced-affinity-pod
spec:
  affinity:
    nodeAffinity:
      # HARD CONSTRAINT: Must be in us-east-1a or us-east-1b
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: topology.kubernetes.io/zone
            operator: In
            values:
            - us-east-1a
            - us-east-1b
      # SOFT PREFERENCE: Strongly prefer nodes with dedicated SSDs
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 80
        preference:
          matchExpressions:
          - key: hardware-profile/disk
            operator: In
            values:
            - dedicated-nvme
  containers:
  - name: data-processor
    image: data-processor:latest
```

This Pod can run only in the two listed zones, so a node in another zone fails filtering even if it has abundant CPU and memory. Within the feasible zones, a node labeled with `hardware-profile/disk=dedicated-nvme` receives an additional score because the preference has a weight of eighty. If the NVMe nodes are full, the Pod can still run on a standard-disk node in the allowed zones. That fallback behavior is the reason preferred affinity is safer for performance hints than hard selectors.

The phrase `IgnoredDuringExecution` matters because the scheduler makes a placement decision at one point in time. If a Pod was scheduled onto a node because the node had `environment=production`, and an administrator later removes that label, the existing Pod keeps running. Kubernetes does not continuously re-evaluate ordinary affinity and evict running Pods for drift. If you need active correction after placement, you use operational actions such as deleting Pods, draining nodes, using `NoExecute` taints, or deploying a descheduler policy.

Which approach would you choose here and why: a hard node affinity rule for `accelerator=nvidia` on a machine learning training job, or a preferred node affinity rule for `hardware-profile/disk=dedicated-nvme` on a batch analytics job? The GPU rule is probably hard because the workload cannot run without the device. The disk rule is probably preferred because slower disks may be acceptable when the faster pool is busy. Scheduling design begins by separating correctness from optimization.

War Story: a data platform team once required every analytics Pod to run on NVMe nodes because early benchmarks looked better there. During a quarterly report run, those nodes filled, new jobs remained `Pending`, and the team had to manually edit manifests under pressure. After converting the storage preference to weighted node affinity, jobs still preferred NVMe but continued on standard nodes when capacity was tight. The report took longer, but it finished without human intervention.

Label quality is the quiet dependency behind every affinity rule. If labels are applied manually and inconsistently, the scheduler will faithfully enforce a map that does not match reality. Platform teams should treat node labels for zones, hardware, compliance, and lifecycle state as managed infrastructure data, preferably set by automation or admission policy. The more business-critical the placement rule, the less acceptable it is for the backing label to depend on a one-off command someone might forget during node replacement.

## Pod Affinity, Anti-Affinity, and Topology Spread

Node affinity describes how a Pod relates to hardware. Pod affinity and anti-affinity describe how a Pod relates to other Pods that already exist. That distinction is crucial for distributed systems because replicas are not independent decorations on a cluster map. Web frontends may need to stay close to caches for latency, while replicas of the same critical service should often stay apart so one node or zone failure does not remove all capacity at once.

Pod affinity pulls workloads toward matching Pods in a topology domain. A high-traffic web service that repeatedly reads from Redis may benefit from running in the same zone, or in rare cases the same node, as the cache. The scheduler evaluates existing Pods matching a label selector and asks whether the candidate node shares the requested topology key with those Pods. This is powerful, but it can also create tight coupling, so you use it when latency or data locality clearly justifies the placement constraint.

Pod anti-affinity pushes workloads away from matching Pods. If a Deployment has three replicas and all three land on one node, a single node loss can erase the whole service. Anti-affinity can require replicas to spread across hostnames or zones by rejecting nodes whose topology domain already contains a matching Pod. The tradeoff is availability versus schedulability: strict spreading is excellent until the cluster lacks enough domains, at which point extra replicas stay `Pending` instead of violating the rule.

The `topologyKey` defines the meaning of "near" or "away." With `kubernetes.io/hostname`, the domain is an individual node, so anti-affinity prevents two matching replicas from sharing a physical or virtual machine. With `topology.kubernetes.io/zone`, the domain is an availability zone, so anti-affinity can keep replicas in separate failure domains. If you choose the wrong topology key, the YAML may be valid while the availability outcome is wrong.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: highly-available-web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-frontend
  template:
    metadata:
      labels:
        app: web-frontend
    spec:
      affinity:
        podAntiAffinity:
          # Force the scheduler to place every replica in a DIFFERENT availability zone
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: web-frontend
            topologyKey: "topology.kubernetes.io/zone"
      containers:
      - name: web-server
        image: nginx:alpine
```

This Deployment makes a strong promise: no two `web-frontend` replicas should run in the same zone. That promise works only if the cluster has enough labeled zones to host the requested replica count. If you ask for five replicas in a three-zone cluster with required zone anti-affinity, the scheduler can place three and must leave the remaining replicas `Pending`. Kubernetes will not break the hard rule just because the Deployment wants more replicas.

Topology spread constraints provide a more flexible alternative for many availability designs. Instead of saying "never co-locate these Pods," you define a maximum skew between topology domains and choose whether the scheduler must enforce the rule or should merely prefer it. For example, a service can require that zones stay within one replica of each other, which prevents accidental pileups while avoiding some of the harsh all-or-nothing behavior of strict anti-affinity. This is especially useful for larger replica counts where exact one-per-zone placement is not the goal.

Pause and predict: in a three-zone cluster with six frontend replicas, what operational difference would you expect between strict zone anti-affinity and a topology spread constraint with low skew? Strict anti-affinity may block after three replicas because each zone already contains a matching Pod. A spread constraint can allow two replicas per zone while still preventing an uneven placement such as five replicas in one zone and one in another.

War Story: a team running a status API thought they were highly available because every replica used `kubernetes.io/hostname` anti-affinity. A cloud zone outage still removed most of the service because all replicas had landed on different nodes inside the same zone. After the incident, they moved from host-only anti-affinity to zone-aware topology spread constraints, then verified placement with `k get pods -o wide` during every release rehearsal. The rule they needed was not "different machines"; it was "different failure domains."

For KCNA-level reasoning, the main habit is to name the failure domain before choosing the primitive. If the feared event is a node reboot, hostname spreading is relevant. If the feared event is a zone outage, zone spreading is relevant. If the feared event is overload from all replicas sharing the same cache dependency, affinity may be relevant instead of anti-affinity. The YAML should follow the failure model, not the other way around.

## Taints and Tolerations: Dedicated Nodes and Evictions

Affinity is an attraction mechanism, while taints are a repulsion mechanism. Node affinity lets Pods seek nodes with certain properties, but it does not stop unrelated Pods from landing on those same nodes. Taints solve that second problem by marking a node so the scheduler rejects Pods that lack a matching toleration. In practice, dedicated hardware pools almost always need both tools: affinity to pull the intended workloads in, and taints to keep the unintended workloads out.

Imagine a cluster with expensive GPU nodes for model training. If you only label those nodes and give machine learning Pods node affinity, the ML jobs can find them, but ordinary web Pods can still use the spare CPU and memory there whenever the scheduler thinks the placement is good. That wastes specialized hardware and can block the next training job. A taint such as `dedicated=machine-learning:NoSchedule` turns the GPU nodes into a restricted pool.

The existing command form is simple, and with the local alias it becomes `k taint nodes gpu-node-01 dedicated=machine-learning:NoSchedule`. The taint has a key, a value, and an effect. A Pod's toleration must match those fields, depending on its operator, before the scheduler can consider the node. A toleration is not a request to run on the node; it is permission to pass the taint. You usually combine it with node affinity or a selector when the Pod should actively target the pool.

Taint effects determine how forceful the repulsion is. `NoSchedule` blocks new non-tolerating Pods but leaves existing Pods alone. `PreferNoSchedule` is a soft preference that discourages placement but may allow it when the cluster has no better options. `NoExecute` is the aggressive form: it blocks new non-tolerating Pods and evicts existing non-tolerating Pods from the node. Kubernetes uses `NoExecute` style behavior internally for serious node conditions such as unreachable nodes.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: data-science-job
spec:
  # The VIP pass to bypass the node's defensive taint
  tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "machine-learning"
    effect: "NoSchedule"
  # Optional: Also add nodeSelector so it ONLY goes to these nodes
  nodeSelector:
    accelerator: nvidia-tesla-v100
  containers:
  - name: ml-processor
    image: tensor-flow-custom:v4
```

This Pod has both permission and direction. The toleration lets it pass the `dedicated=machine-learning:NoSchedule` taint, while the `nodeSelector` ensures it targets nodes labeled with the GPU accelerator. If you remove the toleration, the Pod may match the node label but fail the taint filter. If you remove the selector, the Pod may tolerate the GPU pool but still schedule elsewhere if another node scores better.

The operational trap is assuming tolerations are exclusive reservations. They are not. A toleration says, "I am allowed to run there," not "I must run there" or "only I may run there." Exclusivity comes from the combination of node taints, workload tolerations, and workload selection rules. For dedicated pools, you also need naming and label conventions that humans can audit easily during incidents.

War Story: a platform team created a database node pool and gave database Pods tolerations, but they forgot to add required node affinity. During a quiet period, the scheduler placed some database replicas on ordinary nodes because those nodes scored well and the Pods were not required to choose the database pool. The fix was not another taint. The fix was to express both halves of the contract: repel general workloads from database nodes and require database workloads to select them.

Taints are also valuable during operations because they can communicate temporary intent. A `NoSchedule` maintenance taint can keep new work away from a node before a drain, giving the platform team time to inspect what is already running. A `NoExecute` taint is much stronger and should be used with care because it changes running workload state. The distinction matters during incident response: one effect prevents new risk, while the other actively moves work and can create load elsewhere.

## Diagnosing Pending Pods: The Operator's Mindset

A Pod in `Pending` is not a mystery; it is an unsatisfied scheduling contract. The scheduler evaluated the Pod against the cluster and could not find a node that passed every hard filter. Your first diagnostic step is not to restart the Deployment, delete random Pods, or add a bigger node blindly. Your first step is to read the event written by the scheduler and translate it into a concrete list of failed constraints.

The most important command is `k describe pod <pod-name>`, then the `Events:` section at the bottom. A typical event might say: `0/15 nodes are available: 5 node(s) didn't match Pod's node affinity/selector, 6 Insufficient memory, 4 node(s) had taint {dedicated: database}, that the pod didn't tolerate.` That sentence is a compressed incident report. It tells you the total cluster size, which filters rejected nodes, and whether the problem is labels, resources, taints, ports, topology, or storage.

You should read the event as a partition of the cluster. In that example, five nodes failed label or affinity requirements, six nodes failed memory requests, and four nodes failed taint toleration. There is no need to wonder whether the scheduler forgot about a node. Every node failed at least one hard condition. The fix must change one of those conditions: adjust requests, add capacity, correct labels, change affinity, add a toleration, or move the workload to a better-suited pool.

The event also helps you avoid false conclusions from dashboards. Low observed CPU usage does not contradict `Insufficient cpu`, because the scheduler works from requests. High free disk space does not fix a missing volume topology match. A healthy node status does not override a taint. Good scheduling diagnosis means respecting the scheduler's vocabulary and then checking the specific object fields that produce that vocabulary.

When you troubleshoot, move from the Pod outward. Start with the Pod spec and events, then inspect candidate node labels with `k get nodes --show-labels`, node taints with `k describe node`, allocatable capacity with `k describe node`, and existing requested capacity in the allocated resources section. For topology problems, verify that node labels such as `topology.kubernetes.io/zone` exist and are consistent. For storage problems, check whether PersistentVolumes and nodes live in compatible zones.

A worked example makes the method concrete. Suppose a payments Pod says `0/8 nodes are available: 3 node(s) didn't match Pod's node affinity/selector, 5 Insufficient cpu.` The wrong response is to say, "CPU is only ten percent used, so Kubernetes is broken." The better response is to inspect the requested CPU already assigned to those five nodes, then decide whether the Pod's request is honest, old workloads are over-requested, or the cluster needs more capacity.

Before changing anything, predict which fix would be least risky in that payments example: lowering the new Pod's CPU request, adding labels to the three rejected nodes, or adding nodes. If the request is inflated compared with measured load, lowering it may be correct. If the labels are wrong because the nodes really are suitable, fixing labels may be correct. If requests are accurate and the workload is business critical, adding capacity is the honest solution. The event tells you where to look, but engineering judgment chooses the remedy.

Good teams turn this diagnostic process into a runbook. The runbook should tell responders to capture the `FailedScheduling` event, inspect the Pod's requests and placement rules, inspect candidate node labels and taints, and record the chosen fix. That record becomes training data for future sizing, policy, and architecture reviews. Scheduling incidents repeat when teams fix the symptom without preserving the evidence that explained the contract mismatch.

## Patterns & Anti-Patterns

Scheduling patterns are reusable contracts between application teams and the platform. They work best when they are easy to explain during an incident, observable from Kubernetes objects, and tested by failure drills. The goal is not to make every Pod specification clever. The goal is to encode the few placement rules that actually protect reliability, performance, or cost, while leaving the scheduler enough freedom to keep the cluster usable.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---------|----------------|--------------|-----------------------|
| Requests from measured baselines | You have production or load-test data for CPU and memory behavior. | The scheduler receives realistic reservations, so placement reflects real demand without buying idle capacity. | Revisit requests after major releases because initialization, caches, and traffic shape can change. |
| Required affinity for correctness | A workload cannot function without a hardware, compliance, or topology property. | Filtering prevents the Pod from starting somewhere that would fail later or violate policy. | Keep the required label set small and consistently applied, or rollouts can become fragile. |
| Preferred affinity for optimization | A workload benefits from a node property but can tolerate fallback. | Scoring improves placement without turning temporary scarcity into `Pending` replicas. | Use weights intentionally and monitor whether preferences are actually satisfied under load. |
| Taint plus affinity for dedicated pools | You run GPUs, database nodes, regulated zones, or isolation pools. | Taints repel general workloads, while affinity pulls intended workloads into the pool. | Audit both sides together; a toleration alone does not require placement on the pool. |
| Topology spread for many replicas | You need balanced replicas across zones or nodes, especially above one replica per domain. | Skew limits prevent pileups while preserving more scheduling flexibility than strict anti-affinity. | Choose `whenUnsatisfiable` carefully because strict enforcement can still block rollouts. |

Anti-patterns usually come from treating one scheduling primitive as if it solved every placement problem. A `nodeSelector` looks simple, so teams use it for preferences and accidentally create hard outages. A toleration sounds like a reservation, so teams forget affinity and wonder why workloads land elsewhere. A memory limit looks protective, so teams set it too low and create restarts. The primitives are reliable, but they do exactly what they say, not what a team hoped they implied.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|-------------------|
| Hard selectors for nice-to-have hardware | Pods remain `Pending` when preferred nodes are full even though acceptable nodes exist. | Use preferred node affinity with a clear fallback expectation. |
| Requests copied from limits without measurement | The scheduler sees the cluster as full while real CPU may be idle. | Set requests from observed steady-state and startup needs, then adjust with evidence. |
| Tolerations without node selection | Workloads may run anywhere because toleration is permission, not attraction. | Pair tolerations with required affinity or a selector when the pool is mandatory. |
| Zone anti-affinity with too many replicas | Extra replicas cannot schedule once every zone already has a matching Pod. | Use topology spread constraints when balanced distribution is better than one-per-zone exclusivity. |
| Treating label drift as automatic eviction | Existing Pods keep running after ordinary affinity labels change. | Use controlled rollouts, drains, `NoExecute` taints, or descheduler policies when correction is required. |

The pattern language should show up in reviews. When someone proposes a scheduling rule, ask whether it is protecting correctness, improving performance, isolating cost, or supporting recovery. If the answer is unclear, the rule may be accidental complexity. If the answer is clear, choose the least strict primitive that still protects the required outcome, because excessive strictness is one of the fastest ways to manufacture unschedulable Pods.

Patterns also need owners. A team that owns the application can usually tune requests and decide whether a faster disk is optional. A platform team usually owns node labels, taints, topology naming, and cluster autoscaler behavior. If those ownership boundaries are vague, scheduling bugs become political arguments during incidents. Make the contract explicit: application manifests declare workload needs, while platform automation keeps node facts accurate and capacity policies understandable.

## Decision Framework

Use scheduling constraints by starting with the failure you are trying to prevent. A workload that needs a GPU has a correctness requirement, so it needs a hard node rule and probably a dedicated pool. A workload that runs faster on NVMe has a performance preference, so it probably needs preferred affinity. A service that must survive a zone outage needs zone-aware spreading, not merely host spreading. A node that should reject general workloads needs a taint, not just a label.

```text
Need a placement rule?
  |
  +-- Must the Pod have a node property to function?
  |     |
  |     +-- yes --> required node affinity or nodeSelector
  |     |
  |     +-- no --> preferred node affinity
  |
  +-- Must ordinary Pods stay off a node pool?
  |     |
  |     +-- yes --> taint the nodes and add tolerations only to allowed Pods
  |
  +-- Must replicas survive node or zone failure?
  |     |
  |     +-- few replicas, strict isolation --> pod anti-affinity
  |     |
  |     +-- many replicas, balanced domains --> topology spread constraints
  |
  +-- Is a Pod Pending?
        |
        +-- read FailedScheduling events before changing YAML
```

| Decision | Prefer This | Avoid This | Reason |
|----------|-------------|------------|--------|
| Correct hardware is mandatory | Required node affinity | Preferred affinity alone | The scheduler must filter out nodes that cannot run the workload. |
| Hardware is faster but optional | Preferred node affinity | `nodeSelector` | The Pod should keep running on fallback nodes when preferred capacity is gone. |
| Dedicated pool needs protection | Taint plus toleration plus affinity | Label only | Labels attract selected Pods but do not repel unrelated Pods. |
| Replicas must avoid one node | Pod anti-affinity on `kubernetes.io/hostname` | Zone-only assumptions | Host spreading protects against a single node failure. |
| Replicas must survive zone loss | Topology spread or anti-affinity on `topology.kubernetes.io/zone` | Host-only spreading | Different nodes in one zone still share a zone failure domain. |
| Placement is failing | `k describe pod` and node inspection | Random restarts | Scheduler events identify the filters that rejected every node. |

A good design review can use three questions. First, what is the minimum placement guarantee the workload needs to be correct? Second, what placement preference would improve performance, cost, or recovery if capacity allows? Third, what evidence will operators inspect when the Pod is `Pending`? If the YAML answers those questions, the scheduling contract is likely understandable during a real incident.

The framework is intentionally conservative because schedulers work best when they have room to optimize. Every hard rule removes nodes from consideration, which can be exactly right for correctness and exactly wrong for preference. Every soft rule influences ranking but may be ignored when capacity pressure narrows the feasible set. The senior operator's habit is to ask, "What happens when the ideal node is unavailable?" If the answer is an acceptable fallback, make the rule soft. If the answer is a broken or unsafe workload, make it hard and ensure capacity exists.

## Did You Know?

1. **Scheduler scale is intentionally bounded**: In large clusters, the kube-scheduler can stop searching after it finds a configured percentage of feasible nodes, with defaults that trade perfect global scoring for lower scheduling latency.
2. **Custom schedulers can coexist**: Kubernetes lets a Pod specify `schedulerName`, so clusters can run specialized schedulers beside the default scheduler for unusual placement policies.
3. **The default scheduler does not rebalance running Pods**: Once a Pod is bound, ordinary scheduler logic does not move it later just because the cluster becomes uneven or labels drift.
4. **Topology spread became stable in Kubernetes 1.19**: The feature gives operators skew-based spreading that is often more flexible than strict one-Pod-per-domain anti-affinity.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Using `nodeSelector` for soft preferences | `nodeSelector` is easy to read, so teams use it for nice-to-have hardware and accidentally create a hard scheduling requirement. | Use preferred node affinity when fallback nodes are acceptable, and reserve hard selectors for correctness. |
| Setting limits without thoughtful requests | Teams focus on runtime containment and forget that requests are what the scheduler uses for placement capacity. | Define explicit requests from observed baselines, then set limits only where runtime enforcement is useful. |
| Misunderstanding `topologyKey` | The YAML accepts many label keys, so an operator can choose a key that does not represent the intended failure domain. | Use `kubernetes.io/hostname` for node separation and `topology.kubernetes.io/zone` for zone separation. |
| Relying on `IgnoredDuringExecution` for cleanup | The phrase sounds policy-like, but it means ordinary affinity is checked during scheduling, not continuously enforced later. | Restart or drain Pods deliberately, use `NoExecute` taints, or use a descheduler when active correction is required. |
| Applying only affinity to dedicated hardware | Affinity attracts intended Pods but does not keep ordinary Pods away from expensive or restricted nodes. | Add taints to the dedicated nodes and matching tolerations plus selection rules to the intended workloads. |
| Setting overly strict CPU limits | Teams try to prevent noisy neighbors but cause throttling during startup, compilation, or request bursts. | Use realistic CPU requests for placement and apply CPU limits cautiously after measuring latency effects. |
| Adding a toleration without a matching selector | A toleration is mistaken for a destination rule, so Pods can still schedule outside the dedicated pool. | Pair tolerations with required node affinity or selectors when the workload must land on that pool. |

## Quiz: Operational Scenarios

<details><summary>Question 1: A payment Pod is `Pending`, and `k describe pod` reports `0/8 nodes are available: 3 node(s) didn't match Pod's node affinity/selector, 5 Insufficient cpu`. Dashboards show the five CPU-failing nodes are only ten percent busy. What should you check before changing the Deployment?</summary>

Check the requested CPU already assigned to those nodes, not only real-time CPU usage. The scheduler filters by allocatable capacity minus existing requests, so a node can look quiet while being full on paper. You should compare the new Pod's CPU request with node allocated resources and decide whether existing requests are inflated, the new request is inflated, or more capacity is required. The event also says three nodes failed affinity or selector rules, so labels and required affinity should be inspected separately.
</details>

<details><summary>Question 2: Your team wants three replicas of a customer-facing API to survive a zone outage, but the current anti-affinity rule uses `kubernetes.io/hostname`. The rollout looks healthy. What risk remains?</summary>

The replicas may be on different nodes while still sharing the same availability zone. Hostname anti-affinity protects against a single node failure, but it does not guarantee zone diversity. To protect against zone loss, use `topology.kubernetes.io/zone` in a suitable anti-affinity or topology spread rule. You should verify node labels and actual Pod placement with `k get pods -o wide` during the rollout.
</details>

<details><summary>Question 3: A machine learning job uses required node affinity for `accelerator=nvidia`, but ordinary web Pods are also running on the GPU nodes and blocking new jobs. Which scheduling mechanism is missing?</summary>

The GPU nodes need a taint, and the ML Pods need a matching toleration. Node affinity pulls ML workloads toward the GPU nodes, but it does not repel unrelated workloads. A taint such as `dedicated=machine-learning:NoSchedule` keeps ordinary Pods away unless they tolerate it. The ML Pods should also keep their node selection rule so they both tolerate and target the dedicated pool.
</details>

<details><summary>Question 4: A Deployment sets CPU request to `4000m` and memory limit to `50Mi`, while the app normally needs `200m` CPU and `500Mi` memory. What happens during scheduling and runtime?</summary>

During scheduling, the Pod demands four full CPU cores of unreserved capacity, so it may stay `Pending` even though the application usually needs far less CPU. If it does schedule, the memory limit is far below the application's actual startup need. The process will exceed an incompressible memory boundary and can be OOMKilled by the kernel. This is a combined placement and runtime sizing failure, not a single scheduler issue.
</details>

<details><summary>Question 5: An administrator applies `disk-failure=true:NoExecute` to a node with five running Pods, and none of those Pods has a matching toleration. What should controllers and operators expect?</summary>

`NoExecute` affects running Pods as well as future scheduling, so the non-tolerating Pods are evicted from the node. If those Pods are managed by controllers such as Deployments or ReplicaSets, the controllers create replacements. The scheduler then places replacements on nodes that pass their constraints. Operators should still confirm that enough healthy capacity exists, because eviction only starts recovery; it does not guarantee successful replacement placement.
</details>

<details><summary>Question 6: Analytics Pods should prefer high-speed NVMe nodes but still run on standard disks when the fast pool is full. Which placement rule fits this goal?</summary>

Use preferred node affinity with a weight for the NVMe label. That rule participates in scoring, so NVMe nodes become more attractive when they are feasible. If those nodes fail filtering because they are full or unavailable, the Pod can still schedule on a standard node. A hard `nodeSelector` or required affinity rule would block fallback and turn a performance preference into an availability problem.
</details>

<details><summary>Question 7: A team wants six replicas balanced across three zones and does not require exactly one replica per zone. Why might topology spread constraints be better than strict zone anti-affinity?</summary>

Strict zone anti-affinity can block scheduling after each zone already contains one matching replica, depending on the exact selector and topology. Topology spread constraints let you express balanced skew, such as keeping zones within one replica of each other. That allows two replicas per zone while still preventing a lopsided placement. It is usually a better fit for larger replica counts where balance matters more than total separation.
</details>

## Hands-On Exercise: Engineering Availability

In this exercise, you will build a small scheduling scenario that exposes the difference between placement, spreading, and taint-based isolation. Use a disposable Kubernetes 1.35 or newer lab cluster with at least three worker nodes if possible. If your local cluster has fewer nodes, the `Pending` behavior is still useful because it shows how strict rules fail when the cluster lacks enough topology domains.

Start by creating the local command alias if your shell does not already have it. The rest of the exercise uses `k`, and the commands are intentionally short because real scheduling incidents often involve repeated inspection. You will create a Redis Deployment, add strict anti-affinity, taint a node, then create an administrative Pod that is allowed to bypass the taint.

```bash
alias k=kubectl
k create deployment ha-cache --image=redis:alpine --replicas=3 --dry-run=client -o yaml > ha-cache.yaml
```

Task 1: Create the `ha-cache` Deployment manifest with three replicas, then inspect the generated YAML before applying it. The important observation is that a plain Deployment does not guarantee node separation. Without an affinity or spread rule, the scheduler is free to place replicas wherever resources, scoring, and existing cluster state lead it.

<details><summary>Solution for Task 1</summary>

The command above writes `ha-cache.yaml`. Review it, then apply it with `k apply -f ha-cache.yaml` and inspect placement with `k get pods -o wide`. If all replicas happen to land on separate nodes, remember that this is an outcome, not a guarantee. Delete and recreate enough times on a busy cluster and you may eventually see co-location.
</details>

Task 2: Modify `ha-cache.yaml` so no two Redis replicas can run on the same physical node, then apply the file. This task maps directly to the design outcome: you are using Pod anti-affinity to encode high availability against a single node failure.

```yaml
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: ha-cache
            topologyKey: kubernetes.io/hostname
      containers:
      - image: redis:alpine
```

<details><summary>Solution for Task 2</summary>

Place the `affinity` block under `spec.template.spec`, not under the Deployment's top-level `spec`. Apply the updated manifest with `k apply -f ha-cache.yaml`, then run `k get pods -o wide` to verify that replicas are on different nodes. If you have fewer than three schedulable nodes, one or more replicas should remain `Pending`, which is the correct result for a strict rule that cannot be satisfied.
</details>

Task 3: Select one worker node and apply a `NoSchedule` taint with key `maintenance` and value `true`. This task demonstrates that a taint changes eligibility for future Pods, but it does not evict running Pods unless the effect is `NoExecute`.

```bash
# Get your node names
k get nodes

# Apply the taint to one node, replacing the placeholder with a real node name
k taint nodes <node-2-name> maintenance=true:NoSchedule
```

<details><summary>Solution for Task 3</summary>

After applying the taint, run `k describe node <node-2-name>` and find the `Taints:` line. Existing Pods on that node should continue running because `NoSchedule` affects new placements. If you accidentally taint the wrong node, remove it with `k taint nodes <node-name> maintenance=true:NoSchedule-` and repeat the task on the intended node.
</details>

Task 4: Scale `ha-cache` to five replicas and diagnose any `Pending` Pods using scheduler events. This task maps to the diagnostic outcome: you should read `FailedScheduling` details and explain whether anti-affinity, taints, or capacity caused the block.

```bash
k scale deployment ha-cache --replicas=5
k get pods
```

<details><summary>Solution for Task 4</summary>

If your lab has only three or four usable nodes, at least one new Pod may remain `Pending`. Run `k describe pod <pending-pod-name>` and inspect the `FailedScheduling` event. You should see reasons tied to anti-affinity, the maintenance taint, insufficient resources, or a combination. The point is not to force all five replicas to run; the point is to explain exactly why the scheduler rejected each candidate node.
</details>

Task 5: Create a standalone `admin-toolkit` Pod that can run on the tainted node by combining a node selector with the matching toleration. This task maps to the comparison outcome because the selector attracts the Pod to the node, while the toleration lets it pass the taint.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: admin-toolkit
spec:
  nodeSelector:
    kubernetes.io/hostname: <node-2-name>
  tolerations:
  - key: "maintenance"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
  containers:
  - name: shell
    image: busybox
    command: ["sleep", "3600"]
```

<details><summary>Solution for Task 5</summary>

Save the Pod manifest as `admin-pod.yaml`, replace `<node-2-name>` with the exact node hostname label value, then run `k apply -f admin-pod.yaml`. Verify placement with `k get pod admin-toolkit -o wide`. If the Pod is still `Pending`, describe it and compare the node selector value, taint key, taint value, toleration operator, and effect.
</details>

Task 6: Clean up the lab and write down the scheduling evidence you observed. Cleanup is part of the exercise because taints left behind in a shared lab can confuse the next deployment and create misleading failures.

<details><summary>Solution for Task 6</summary>

Run `k delete deployment ha-cache`, `k delete pod admin-toolkit`, and remove the taint with `k taint nodes <node-2-name> maintenance=true:NoSchedule-`. Then record one example `FailedScheduling` message and the exact fix you would choose in a production incident. That final note should mention whether the root cause was resource requests, anti-affinity, taints, labels, or topology.
</details>

Use these success criteria as a final check against the learning outcomes, and do not mark the exercise complete until each item is backed by a command output, an event message, or a placement decision you can explain:

- [ ] Diagnose Pending Pods by quoting one `FailedScheduling` event and mapping each phrase to a failed scheduler filter.
- [ ] Design highly available replicas by applying Pod anti-affinity and verifying replica placement with `k get pods -o wide`.
- [ ] Compare node affinity with taints and tolerations by explaining why the admin Pod needs both selection and permission.
- [ ] Implement resource-aware scheduling checks by inspecting node allocatable capacity or allocated requests before changing replica counts.
- [ ] Evaluate scheduler placement choices by deciding whether strict anti-affinity or topology spread would be better for your lab cluster.

## Sources

- [Kubernetes Documentation: Scheduling, Preemption and Eviction](https://kubernetes.io/docs/concepts/scheduling-eviction/)
- [Kubernetes Documentation: Assign Pods to Nodes](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/)
- [Kubernetes Documentation: Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Kubernetes Documentation: Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)
- [Kubernetes Documentation: Pod Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)
- [Kubernetes Documentation: Pod Priority and Preemption](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/)
- [Kubernetes Documentation: Node Pressure Eviction](https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/)
- [Kubernetes Documentation: kube-scheduler](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-scheduler/)
- [Kubernetes Documentation: Scheduler Configuration](https://kubernetes.io/docs/reference/scheduling/config/)
- [Kubernetes Documentation: Well-Known Labels, Annotations and Taints](https://kubernetes.io/docs/reference/labels-annotations-taints/)

## Next Module

[Module 2.2: Scaling](../module-2.2-scaling/) - Discover how Kubernetes moves from static placement to automated growth by adjusting replicas from workload demand and cluster signals.
