---
revision_pending: false
title: "Module 1.3: Kubernetes Architecture - Control Plane"
slug: k8s/kcna/part1-kubernetes-fundamentals/module-1.3-control-plane
sidebar:
  order: 4
---

# Module 1.3: Kubernetes Architecture - Control Plane

> **Complexity**: `[MEDIUM]` - Core architecture concepts
>
> **Time to Complete**: 60-75 minutes
>
> **Prerequisites**: Modules 1.1 and 1.2
>
> **Kubernetes Version**: 1.35+

Commands in this module use `k` as the short alias for `kubectl`. If your shell does not already define it, run the following once before the hands-on work so every command matches the examples.

```bash
alias k=kubectl
```

## Learning Outcomes

After completing this module, you will be able to perform the following diagnostic and design tasks against a Kubernetes 1.35+ cluster:

1. **Diagnose** control plane component failures by matching API server, etcd, scheduler, controller manager, and cloud-controller-manager symptoms to likely causes.
2. **Trace** a Pod creation request through API server validation, etcd persistence, controller reconciliation, scheduler assignment, and kubelet execution.
3. **Compare** single-node and high-availability control plane designs, including API server scaling, leader election, and etcd quorum behavior.
4. **Evaluate** operational evidence from `k` commands, events, and object fields to decide what the control plane has already completed.

## Why This Module Matters

In December 2021, a large trading platform suffered a public outage after a control plane upgrade exposed a weakness in its Kubernetes management layer. Customer-facing applications did not all crash at once; many containers kept running where they already were. The business impact still became painful because engineers could not reliably create new workloads, move failed Pods, or apply urgent configuration changes while the control plane was unhealthy. The lesson is direct: Kubernetes application availability depends not only on containers, but also on the management system that records desired state and turns it into action.

The same pattern appears in less dramatic internal incidents. A team sees web traffic degrade after a node failure, yet the first instinct is to inspect the Deployment, the container image, or the Service. Those checks matter, but they can miss the real fault if the scheduler cannot bind replacement Pods, if the controller manager is not creating new Pods, or if etcd cannot accept writes. Control plane architecture is therefore not trivia for certification questions; it is the map that lets you separate workload bugs from cluster management failures under pressure.

This module teaches the control plane as a set of cooperating control loops rather than as a memorized list of daemons. You will connect each component to an operational responsibility, follow a request from `k create deployment` to a running container, and compare a small learning cluster with a high-availability production design. When the KCNA asks which component stores cluster state, assigns Pods, or reconciles desired state, you will have a mental model grounded in real request flow instead of isolated definitions.

The practical payoff is confidence during diagnosis. If an API request is rejected, you know to reason about admission, authorization, validation, and storage. If a Pod is created but remains `Pending`, you know to inspect scheduling evidence. If a Deployment exists but no ReplicaSet or Pod appears, you look toward controller reconciliation. That component-by-component separation is what turns Kubernetes from a black box into a system you can debug.

## Kubernetes Cluster Architecture

Kubernetes separates responsibility between the control plane and the worker nodes. The control plane is the management layer that accepts desired state, stores it, and coordinates controllers that try to make reality match that desired state. Worker nodes run containers, report status, and execute the assignments they receive. This split is similar to an airport operations center and the individual ground crews: the operations center does not physically load every bag, but it owns the schedule, the plan, and the decisions that coordinate the work.

The important boundary is that users and automation normally talk to the API server, not directly to kubelets or etcd. A `k apply` request enters the control plane, is checked against policy, and is persisted as part of the cluster record. Other components then observe that record and take action. This architecture lets Kubernetes remain extensible because new controllers can watch the same API, and it keeps responsibility clean because every actor sees the same source of truth.

```text
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES CLUSTER ARCHITECTURE                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              CONTROL PLANE (Master)                 │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐           │   │
│  │  │  API     │ │ Scheduler│ │Controller│           │   │
│  │  │ Server   │ │          │ │ Manager  │           │   │
│  │  └──────────┘ └──────────┘ └──────────┘           │   │
│  │         ┌──────────┐  ┌──────────┐                 │   │
│  │         │   etcd   │  │  Cloud   │                 │   │
│  │         │          │  │Controller│                 │   │
│  │         └──────────┘  └──────────┘                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          │ API calls                        │
│                          │                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   WORKER NODES                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │   Node 1    │  │   Node 2    │  │   Node 3    │ │   │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │ │   │
│  │  │ │ kubelet │ │  │ │ kubelet │ │  │ │ kubelet │ │ │   │
│  │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │ │   │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │ │   │
│  │  │ │kube-proxy│ │  │ │kube-proxy│ │  │ │kube-proxy│ │ │   │
│  │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │ │   │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │ │   │
│  │  │ │Container│ │  │ │Container│ │  │ │Container│ │ │   │
│  │  │ │ Runtime │ │  │ │ Runtime │ │  │ │ Runtime │ │ │   │
│  │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Do not let the historical word "master" distract you from the actual design. Modern Kubernetes documentation uses "control plane" because the role is broader than a single machine and because production clusters usually run several control plane nodes. The components may run as static Pods on nodes created by kubeadm, as managed processes in a cloud service, or as hidden provider-managed infrastructure. The KCNA concept stays the same: these components implement the Kubernetes API, persistence, scheduling, reconciliation, and cloud integration responsibilities.

The diagram also shows why control plane problems often feel strange during an outage. Running containers on worker nodes can keep serving existing traffic even when some management actions fail, because kubelet and the container runtime already have local instructions. At the same time, the cluster may be unable to accept new desired state or repair failed capacity. That split between "existing Pods keep running" and "new decisions stop happening" is a recurring diagnostic clue.

You can remember the control plane by the type of question each component answers. The API server answers, "Is this request allowed and valid?" etcd answers, "What is the recorded cluster state?" The scheduler answers, "Where should this unscheduled Pod run?" The controller manager answers, "What work is needed to make current state match desired state?" The cloud-controller-manager answers, "What must be created or updated in the external cloud provider?"

| Component | Primary responsibility | Operational symptom when unhealthy |
|-----------|------------------------|------------------------------------|
| kube-apiserver | API entry point, authentication, authorization, admission, validation | `k` commands fail, controllers and kubelets cannot reliably read or write state |
| etcd | Durable distributed storage for Kubernetes objects and metadata | Writes fail, cluster state may be stale, recovery depends on quorum or backups |
| kube-scheduler | Pod placement decision for Pods without `.spec.nodeName` | New Pods remain `Pending` with no assigned node |
| kube-controller-manager | Built-in reconciliation loops for Deployments, ReplicaSets, Nodes, Jobs, and more | Desired objects exist, but dependent objects or repairs do not appear |
| cloud-controller-manager | Cloud-specific integration for nodes, routes, and load balancers | cloud load balancers, node lifecycle, or routes do not match Kubernetes objects |

Pause and predict: if a Deployment object exists, but no Pod objects are being created, which component would you investigate before blaming the scheduler? The scheduler only sees Pods that already exist and lack a node assignment, so a missing Pod points earlier in the chain toward controller reconciliation.

## API Server and etcd: The Front Door and the Source of Truth

The kube-apiserver is the only component most users touch directly, yet it is more than a simple HTTP proxy. It terminates Kubernetes API requests, authenticates the caller, checks authorization, runs admission logic, validates object schemas, and coordinates storage. Every controller, kubelet, scheduler, and external tool depends on the API server because it is the consistent doorway into cluster state. That central doorway is deliberate: one enforcement point is easier to secure, audit, scale, and extend than dozens of components writing state independently.

The request path through the API server is also why Kubernetes can add policy without rewriting every controller. Authentication establishes who is calling, authorization decides whether that identity may perform the requested verb on the requested resource, admission can mutate or reject the object, and validation confirms the final object matches the API schema. Only after those steps does the request become durable cluster state. When a command fails, the exact failure stage often tells you whether you are facing credentials, RBAC, admission policy, malformed YAML, or storage trouble.

This matters during upgrades because Kubernetes APIs evolve while clients, controllers, and admission webhooks may not all move at the same time. The API server is where deprecated fields, removed versions, feature-gated behavior, and admission side effects become visible. A careful operator reads API errors as structured evidence rather than as generic failure text. If a custom admission webhook is unreachable, for example, the API server may reject writes even though etcd and scheduler are perfectly healthy.

```text
┌─────────────────────────────────────────────────────────────┐
│              KUBE-APISERVER                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Exposes the Kubernetes API (REST interface)             │
│  • All communication goes through it                       │
│  • Authenticates and authorizes requests                   │
│  • Validates API objects                                   │
│  • Only component that talks to etcd                       │
│                                                             │
│  Who talks to it:                                          │
│  ─────────────────────────────────────────────────────────  │
│  kubectl ────────→ ┌──────────────┐                       │
│  Dashboard ──────→ │ API Server   │ ←──── kubelet          │
│  Other tools ────→ └──────────────┘ ←──── Controllers      │
│                                                             │
│  Key point:                                                │
│  The API server is the ONLY component that reads/writes    │
│  to etcd. Everything else talks to the API server.        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The API server being stateless is a major scaling advantage. If one API server process fails in a high-availability cluster, another can answer the same kind of request because the durable state is not stored on the local disk of that process. This is why production clusters place several API server instances behind a load balancer. The load balancer gives clients a stable endpoint, while the API servers share the same backing etcd cluster.

etcd is the durable store behind that doorway. It is a distributed key-value database that stores Kubernetes objects, resource versions, leases, node records, Secrets, ConfigMaps, RBAC objects, and the metadata controllers use to coordinate work. Kubernetes uses etcd because control plane state needs strong consistency. If two API servers accept conflicting writes, every controller would be working from a different version of reality, which is the fastest path to unpredictable automation.

Backups are part of the architecture, not an optional operations chore. In a self-managed cluster, an etcd snapshot is the difference between recovering the recorded desired state and rebuilding namespaces, RBAC, Deployments, Services, Secrets, and configuration from scattered manifests or memory. Snapshot practice should include restore drills because a backup that no one can restore under pressure is only a comforting file. Managed services often hide etcd operations, but the concept still appears in disaster recovery guarantees and provider documentation.

etcd performance also affects the whole control plane because many small Kubernetes actions become storage reads, writes, or watches. Slow disks, saturated networks, or overloaded API servers can make reconciliation look sluggish even when controllers are logically correct. When you see broad symptoms across unrelated workloads, include the shared control plane path in your thinking. A single broken Deployment may be an application issue, but many unrelated writes timing out together often points toward API or storage health.

```text
┌─────────────────────────────────────────────────────────────┐
│              ETCD                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it is:                                               │
│  ─────────────────────────────────────────────────────────  │
│  • Distributed key-value store                             │
│  • Stores ALL cluster state                                │
│  • Highly available (usually 3 or 5 nodes)                 │
│  • Uses Raft consensus algorithm                           │
│                                                             │
│  What it stores:                                           │
│  ─────────────────────────────────────────────────────────  │
│  • Pod definitions                                         │
│  • Service configurations                                  │
│  • Secrets and ConfigMaps                                  │
│  • Node information                                        │
│  • RBAC policies                                           │
│  • Everything in the cluster!                              │
│                                                             │
│  Key point:                                                │
│  If etcd is lost, the entire cluster state is lost.       │
│  Backup etcd regularly!                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Think of etcd as the cluster's legal record, not as a runtime engine. It does not run Pods, pull images, route packets, or decide placement. It records the desired and observed facts that other components read through the API server. If etcd loses quorum, the cluster protects consistency by refusing writes rather than guessing. That behavior can feel harsh during an incident, but accepting conflicting writes would be worse because reconciliation loops would act on state that might later be discarded.

The API server and etcd also explain why Kubernetes clients use optimistic concurrency. Objects include resource versions, and watches stream changes after a known version. A controller can say, in effect, "I observed this version and want to update it." If another actor changed the object first, the update can be rejected and retried. This is how many independent controllers cooperate without taking a giant global lock around the whole cluster.

Before running this, what output do you expect if your cluster is reachable but your account lacks permission to list Secrets? The API server should still answer, but authorization should reject that specific request. That difference matters because an authorization denial proves the API server is alive and enforcing policy, while a network timeout or connection refusal points to connectivity, endpoint, or API server availability.

```bash
k cluster-info
k auth can-i list secrets --all-namespaces
k get --raw=/readyz
```

When diagnosing an API path, read the error carefully. `Forbidden` means the authenticated identity reached the API server but lacks permission. `Unauthorized` often means credentials were missing or invalid. `The connection to the server was refused` points before authorization, often to a dead endpoint, wrong kubeconfig, failed local tunnel, or unavailable API server. `etcdserver: request timed out` points behind the API server toward persistence pressure or quorum trouble.

War story: a platform team once blamed a new admission policy because developers could not create Deployments after a maintenance window. The actual failure was an etcd member replacement that left the etcd cluster without quorum. The API server process still listened on its port, which made simple health checks look misleadingly alive, but writes could not be committed. The useful clue was that read-only requests sometimes worked while object creation consistently stalled or failed.

The certification angle is straightforward, but the operational angle is richer. If a question asks where Kubernetes state is stored, answer etcd. If it asks which component validates API objects or exposes the REST API, answer kube-apiserver. If it asks whether every component writes directly to etcd, reject that model. The API server is the mediated, auditable path, and etcd is the consistent backing store that makes the rest of the control plane safe to automate.

## Scheduling and Reconciliation: Decisions Become Work

The scheduler and the controller manager are often confused because both react after a user creates an object. The difference is that controllers create or update the objects needed to match desired state, while the scheduler assigns already-created Pods to nodes. A Deployment controller does not choose a node, and the scheduler does not decide that a Deployment needs a ReplicaSet. Each component watches the API for a specific kind of gap, then writes a small correction back through the API server.

The kube-scheduler watches for Pods that exist but do not yet have `.spec.nodeName` set. For each unscheduled Pod, it filters nodes that cannot run the Pod, scores the nodes that remain, and binds the Pod to a selected node by updating the API server. The filtering phase rejects impossible choices such as nodes without enough CPU, nodes blocked by taints, or nodes that do not match selectors. The scoring phase ranks possible choices based on policies such as spreading load or satisfying affinity preferences.

```text
┌─────────────────────────────────────────────────────────────┐
│              KUBE-SCHEDULER                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Watches for newly created Pods with no node assigned    │
│  • Selects a node for each Pod to run on                  │
│  • Does NOT run the Pod (kubelet does)                    │
│                                                             │
│  How it decides:                                           │
│  ─────────────────────────────────────────────────────────  │
│  Filtering:                                                │
│  • Does node have enough resources?                        │
│  • Does node match Pod's node selector?                   │
│  • Does node satisfy affinity rules?                      │
│                                                             │
│  Scoring:                                                  │
│  • Spread Pods across nodes (balance)                     │
│  • Prefer nodes with image already cached                 │
│  • Consider custom priorities                              │
│                                                             │
│  New Pod → Scheduler → "Run on Node 2" → kubelet runs it  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The scheduler's output is small but decisive. It writes the chosen node onto the Pod, and then the kubelet on that node sees the assignment. The kubelet pulls images through the local container runtime, mounts volumes, starts containers, and reports status back to the API server. This separation is why "the scheduler runs Pods" is wrong. The scheduler makes the placement decision; the worker node's kubelet performs the local execution.

Scheduling is not merely a search for any free node. Kubernetes has to respect hard requirements such as resource requests, node selectors, required affinity, taints without tolerations, topology constraints, and volume placement. It can also consider softer preferences during scoring. That distinction explains why a Pod can be unschedulable even in a cluster with apparently idle machines. A node with spare memory is still invalid if the Pod requires a label the node does not have or lacks a toleration for a taint.

For KCNA-level reasoning, focus on the scheduler's contract rather than every plugin detail. The scheduler observes Pods without node assignments, evaluates feasible nodes, chooses one, and records the binding. It does not change the container image, create the Pod, bypass resource requests, or repair a failed node. If the scheduler says no node fits, the useful response is to inspect the constraints and capacity that produced that answer, not to assume the scheduler is broken because it refused an impossible placement.

The kube-controller-manager runs many built-in controllers in one process. A controller is a reconciliation loop: observe desired state, observe current state, compare them, and make the smallest useful change. The Deployment controller creates ReplicaSets. The ReplicaSet controller creates or deletes Pods to match replica counts. The Node controller responds to node health changes. Other controllers manage Jobs, endpoints, service accounts, namespaces, and more. They all follow the same pattern of watching the API and writing corrections through the API.

```text
┌─────────────────────────────────────────────────────────────┐
│              KUBE-CONTROLLER-MANAGER                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Runs controller processes                               │
│  • Each controller watches for specific resources          │
│  • Controllers make current state match desired state     │
│                                                             │
│  Important controllers:                                    │
│  ─────────────────────────────────────────────────────────  │
│  Node Controller:                                          │
│  • Monitors node health                                    │
│  • Responds when nodes go down                            │
│                                                             │
│  Replication Controller:                                   │
│  • Maintains correct number of Pods                       │
│  • Creates/deletes Pods as needed                         │
│                                                             │
│  Endpoints Controller:                                     │
│  • Populates Endpoints objects                            │
│  • Links Services to Pods                                 │
│                                                             │
│  ServiceAccount Controller:                                │
│  • Creates default ServiceAccounts                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Reconciliation is the idea that makes Kubernetes feel self-healing. A human does not continually restart every failed container or create every replacement Pod by hand. Instead, users declare a desired state, such as "this Deployment should have three replicas," and controllers keep working toward that state. If a Pod disappears, the ReplicaSet controller notices the count is too low and creates another Pod. If a node becomes unhealthy, the Node controller updates node condition and taint information that other controllers can use.

Controllers are intentionally repetitive because the world keeps changing. A controller may try to update an object and lose a race with another actor, so it retries after seeing the new resource version. It may create a dependent object and then wait for status to catch up. It may observe that nothing needs to change and simply continue watching. This steady loop is more robust than a one-shot script because temporary failures, delayed status, and competing changes are normal in distributed systems.

Owner references help make reconciliation visible. A Pod created for a ReplicaSet records ownership metadata, and that ReplicaSet records its relationship to a Deployment. Garbage collection and rollout history depend on these relationships. When you trace a problem, owner references tell you which controller should care about a dependent object. If a Pod lacks the owner you expected, you may be looking at a manually created Pod, a different controller, or a broken generation path.

This is also why Kubernetes troubleshooting benefits from asking, "Which gap has not been closed yet?" If the Deployment exists but no ReplicaSet exists, the Deployment controller gap remains open. If the ReplicaSet exists but no Pods exist, inspect ReplicaSet events and quotas. If Pods exist but have no node, inspect scheduler events, node capacity, selectors, affinities, and taints. If Pods have a node but containers are not running, inspect the kubelet, image pulls, volumes, and container runtime on that node.

Pause and predict: a Pod stays `Pending`, and `k get pod -o wide` shows no node name. Would you start by debugging container logs? Container logs probably do not exist yet because no kubelet has been asked to start the container. The better first move is to inspect Pod events and scheduling constraints, because the failure is still in the placement stage.

```bash
k get pods -o wide
k describe pod <pending-pod-name>
k get events --sort-by=.lastTimestamp
k explain pod.spec.nodeName
```

A simple Deployment gives you a worked example of the controller and scheduler boundary. The Deployment object is the user's desired state. The Deployment controller creates a ReplicaSet to represent a versioned replica target. The ReplicaSet controller creates Pod objects. The scheduler assigns each Pod to a node. Finally, kubelet on the selected node runs the containers. No single component performs the whole operation, which is exactly why diagnosis works best when you trace the object chain.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: control-plane-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: control-plane-demo
  template:
    metadata:
      labels:
        app: control-plane-demo
    spec:
      containers:
        - name: web
          image: nginx:1.29
          ports:
            - containerPort: 80
```

That YAML is intentionally ordinary because the architecture lesson is in the side effects. Applying it creates one top-level desired object, then controllers and the scheduler create and update several dependent objects. A useful exercise is to run `k get deployment,replicaset,pods -w` in one terminal while applying the file in another. You will see Kubernetes gradually close the gaps between desired state and observed state.

War story: an application team once increased a Deployment from two replicas to eight during a traffic spike and watched six Pods sit in `Pending`. They assumed the image registry was slow, but `k describe pod` showed `Insufficient cpu` scheduling events. The scheduler was functioning correctly; it was refusing to bind Pods to nodes that could not honor requests. The fix was capacity and request tuning, not restarting scheduler or changing the image.

## Control Plane Communication and Request Flow

Kubernetes components communicate through the API server, which means request flow is mostly a story about watched objects and updates rather than direct remote procedure calls between every pair of components. Controllers do not phone the scheduler to ask for placement. The scheduler does not phone kubelet to start a container. Instead, each actor watches the API server for resources relevant to its job, writes updates through the API server, and relies on the next actor to observe the new state.

```text
┌─────────────────────────────────────────────────────────────┐
│              HOW COMPONENTS COMMUNICATE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    ┌──────────────┐                        │
│                    │   kubectl    │                        │
│                    └──────┬───────┘                        │
│                           │                                 │
│                           ▼                                 │
│                    ┌──────────────┐                        │
│  Controller ─────→ │  API Server  │ ←───── Scheduler       │
│  Manager           └──────┬───────┘                        │
│                           │                                 │
│                           ▼                                 │
│                    ┌──────────────┐                        │
│                    │     etcd     │                        │
│                    └──────────────┘                        │
│                                                             │
│  Flow example - Creating a Deployment:                    │
│                                                             │
│  1. kubectl creates Deployment via API Server             │
│  2. API Server stores it in etcd                          │
│  3. Deployment Controller sees new Deployment             │
│  4. Controller creates ReplicaSet                         │
│  5. ReplicaSet Controller creates Pods                    │
│  6. Scheduler sees unscheduled Pods                       │
│  7. Scheduler assigns Pods to nodes                       │
│  8. kubelet on node sees assignment, runs Pods           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The watch pattern is efficient because components do not have to constantly list every object and compare everything from scratch. A controller can establish a watch and receive changes for the resource type it owns. The API server uses resource versions to let clients continue from a known point in the event stream. When a watch is interrupted, the client can relist and resume. That design is why controllers can react quickly without turning the API server into a polling bottleneck.

This watch-based architecture also explains why status can lag desired state without meaning the cluster is broken. Creating an object is often immediate, but the status fields reflect work performed by other components after they observe that object. A Deployment can exist before its ReplicaSet exists, a Pod can exist before it is scheduled, and a scheduled Pod can exist before its containers become ready. The time between these stages is where events, conditions, and resource versions provide useful context.

Conditions are especially helpful because they summarize a component's current judgment in a way machines and humans can both read. A Deployment condition may say progress is happening or has stalled. A Pod condition may show whether scheduling, initialization, readiness, or container startup has completed. Good operators do not treat status as decorative output; they read it as the control plane's explanation of what has happened so far and what remains blocked.

Tracing a Deployment request gives you a reliable mental debugger. First, the client sends the Deployment to the API server. Second, the API server authenticates, authorizes, admits, validates, and persists the object to etcd. Third, the Deployment controller notices a desired Deployment without the necessary ReplicaSet and creates one. Fourth, the ReplicaSet controller notices the replica count is below the desired count and creates Pods. Fifth, the scheduler binds those Pods to nodes. Sixth, the kubelet on each selected node starts containers and reports status.

| Stage | Component that acts | Evidence to inspect |
|-------|---------------------|---------------------|
| Request accepted | kube-apiserver | API response, audit logs, object exists in `k get` |
| Desired state stored | etcd through API server | Resource version changes, object can be read again |
| ReplicaSet created | kube-controller-manager | `k get rs`, Deployment conditions, events |
| Pods created | ReplicaSet controller | `k get pods`, owner references, ReplicaSet events |
| Pods assigned | kube-scheduler | `.spec.nodeName`, scheduler events |
| Containers started | kubelet and runtime | Pod conditions, container status, node events |

Which approach would you choose here and why: if a user reports that `k create deployment` returned success but no containers are running, would you inspect the API server first or trace object stages? In most cases, the successful response already proves the first stage worked, so tracing Deployment, ReplicaSet, Pod, scheduler events, and kubelet status gives better evidence than staring at the API server alone.

The stage model also prevents noisy restarts. Restarting the scheduler will not help if no Pod object exists. Restarting kubelet will not help if the Pod has no assigned node. Restarting the API server may make an incident worse if etcd is the true bottleneck and clients are already retrying. Good Kubernetes operations depend on narrowing the failed stage before touching components, especially in production clusters where control plane restarts can affect many teams at once.

`k describe` remains useful because it gathers events and status produced by several components. For a Deployment, it can reveal rollout conditions and ReplicaSet creation. For a Pod, it can reveal scheduler decisions, image pull errors, volume mount errors, and readiness failures. Treat events as breadcrumbs from the control plane. They are not a perfect audit log, but they often identify the component that most recently tried and failed to advance the object.

Events are temporary and can be compacted or rotated, so they should guide diagnosis rather than serve as the only record. If an incident matters, capture relevant object YAML, events, controller logs, and timing before cleanup removes the evidence. The shorter the failure, the easier it is to lose context after retries succeed. This is another reason to diagnose by stage: even when events disappear, the object chain and status fields often preserve enough structure to reconstruct where the request stopped.

```bash
k create deployment control-plane-demo --image=nginx:1.29 --replicas=2
k get deployment,replicaset,pods -o wide
k describe deployment control-plane-demo
k describe pod <new-pod-name>
```

War story: during a platform migration, a team opened an incident because a Deployment showed the correct replica count while traffic still dropped. The object chain revealed that Pods were created and scheduled, but readiness probes failed after kubelet started the containers. The control plane had done its job; the application was refusing to become ready. Without tracing the stages, the team would have wasted time blaming scheduler and controllers for a workload-level health check problem.

## Cloud Integration and High Availability

The cloud-controller-manager exists because Kubernetes needed a cleaner boundary between core orchestration and cloud-provider-specific behavior. A cluster running on a laptop has no cloud load balancer API, no provider route table, and no instance metadata service. A cluster running on AWS, Google Cloud, Azure, or another infrastructure provider often needs Kubernetes Services, Nodes, and routes to reflect external provider resources. Splitting cloud logic into cloud-controller-manager lets core Kubernetes evolve without embedding every provider integration directly into the central controller manager.

```text
┌─────────────────────────────────────────────────────────────┐
│              CLOUD-CONTROLLER-MANAGER                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Cloud-specific control logic                            │
│  • Only present in cloud environments                      │
│  • Separates cloud code from core K8s                     │
│                                                             │
│  Controllers it runs:                                      │
│  ─────────────────────────────────────────────────────────  │
│  Node Controller:                                          │
│  • Checks if node still exists in cloud                   │
│                                                             │
│  Route Controller:                                         │
│  • Sets up routes in cloud infrastructure                 │
│                                                             │
│  Service Controller:                                       │
│  • Creates cloud load balancers for Services              │
│                                                             │
│  Example:                                                  │
│  Service type: LoadBalancer → cloud-controller creates    │
│  an AWS ELB, GCP Load Balancer, or Azure LB              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The most visible cloud-controller-manager behavior for beginners is a Service of type `LoadBalancer`. The Service object is stored in Kubernetes, but the actual load balancer is created in a cloud provider API. That work is asynchronous. The Service may exist immediately while the external address remains pending until the provider creates and reports the resource. If the cloud integration is unhealthy or misconfigured, Kubernetes can record the desired Service forever without receiving a usable external endpoint.

Cloud integration is a good example of Kubernetes extending the reconciliation model beyond the cluster boundary. The Service controller does not become the cloud load balancer; it asks the provider API to make external infrastructure match the Kubernetes Service. That means failures can live outside the cluster while still appearing as Kubernetes status. Provider IAM, subnet discovery, quota, firewall rules, and regional service limits can all block the final result even when the Service YAML is valid.

Managed Kubernetes services can hide these details, but the architecture still matters. When a managed cluster cannot provision a load balancer, the failure may be in Kubernetes Service configuration, cloud IAM permissions, provider quotas, subnet tags, or the cloud-controller integration. The control plane model helps you avoid a shallow conclusion such as "Kubernetes networking is broken." You can ask which reconciliation loop owns the external resource and what evidence it has recorded on the Service.

High availability applies the same responsibility model across multiple machines. API servers can be replicated horizontally because they are stateless. Schedulers and controller managers can run multiple instances, but leader election ensures only one active leader performs a given control loop at a time. etcd runs as a quorum-based cluster because it stores the durable state. A production design must keep these differences straight; duplicating processes is not the same as protecting the data store.

```text
┌─────────────────────────────────────────────────────────────┐
│              HIGH AVAILABILITY SETUP                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Load Balancer                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│         ┌────────────────┼────────────────┐                │
│         │                │                │                 │
│         ▼                ▼                ▼                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ Master 1   │  │ Master 2   │  │ Master 3   │           │
│  │            │  │            │  │            │           │
│  │ API Server │  │ API Server │  │ API Server │           │
│  │ Scheduler  │  │ Scheduler  │  │ Scheduler  │           │
│  │ Controller │  │ Controller │  │ Controller │           │
│  │ etcd       │  │ etcd       │  │ etcd       │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│                                                             │
│  • Multiple API servers (all active)                       │
│  • Scheduler/Controller use leader election               │
│  • etcd requires quorum (odd number: 3, 5, 7)            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Quorum is the reason etcd clusters commonly use an odd number of members. In a three-member etcd cluster, two members form quorum, so the cluster can survive one member failure. In a five-member cluster, three members form quorum, so it can survive two member failures. Adding a fourth member to a three-member cluster does not improve tolerated failures because quorum becomes three; it can still survive only one failure. Odd membership usually gives better fault tolerance per machine.

Leader election is different from etcd quorum. The scheduler and controller manager can run several replicas, but only the elected leader actively writes decisions for a given control loop. Standby replicas keep watching and can take over if the leader disappears. This avoids conflicting actions such as two schedulers trying to bind the same Pod differently or two controllers racing to make duplicate repairs. The lease object used for leader election is itself stored through the API server.

Single-control-plane clusters are appropriate for learning, local development, and some noncritical environments because they are simpler and cheaper. They are also easier to reason about at first: one API server, one scheduler, one controller manager, and usually one local etcd. The tradeoff is obvious during maintenance or failure. If that one control plane node is unavailable, management operations pause even if worker node containers continue running.

High-availability control planes cost more and introduce more moving pieces, but they reduce single points of failure for cluster management. You need a reliable endpoint for API servers, careful certificate and configuration management, etcd backup and restore practice, and monitoring that distinguishes API server health from etcd health. A cluster can have several healthy API server processes and still be unable to write if etcd lacks quorum, so monitoring only process liveness is not enough.

A mature HA design also considers maintenance behavior. Upgrades, certificate rotation, node replacement, and backup restore all stress the same control plane pieces that failures stress. If the only documented recovery plan is "the provider handles it" or "restart the node," the team has not actually compared failure modes. Even managed clusters deserve runbooks that identify which symptoms belong to the provider, which belong to user-managed node pools, and which can be verified through Kubernetes objects.

For self-managed clusters, etcd restore is the scenario to practice before anyone needs it. Restoring a snapshot usually means making careful decisions about cluster identity, member configuration, certificates, and the point in time you are restoring. A sloppy restore can resurrect old desired state or conflict with workloads that continued running after the snapshot. The safe operational habit is to rehearse the procedure on an isolated cluster and document exactly what application teams should expect after recovery.

War story: a team ran three API servers but placed all etcd members on the same underlying virtualization host. Their architecture diagram looked highly available, yet a single host outage removed the entire data store. The API endpoint still had multiple configured backends, but none could commit state. High availability is not a checkbox counted by process replicas; it is a failure-domain design that asks which physical, network, and storage failures the cluster can actually survive.

## Patterns & Anti-Patterns

Good control plane operations start with evidence-first diagnosis. Instead of restarting components because a workload is unhealthy, operators trace the object chain and ask which control loop has not completed its responsibility. This pattern scales because it works the same way for beginner examples and production outages. A Deployment, a Job, a Service, and a Node each have desired state, observed state, events, and controller ownership that can be inspected before changing the system.

| Pattern | When to use it | Why it works |
|---------|----------------|--------------|
| Trace the object chain | A workload request succeeded but the result is incomplete | It separates API acceptance, controller reconciliation, scheduling, and kubelet execution |
| Read events before restarting components | Pods remain `Pending`, Services are stuck, or rollouts stall | Events usually identify the component that tried to advance the object and why it failed |
| Back up and test restore for etcd | Any self-managed production control plane | etcd is the durable cluster record, and untested backups are only hopeful files |
| Use HA with real failure domains | Production clusters with shared teams or revenue impact | Multiple replicas only help when they survive different machine, zone, and storage failures |

The strongest pattern is to treat the API as the coordination contract. Controllers, schedulers, kubelets, and cloud integrations should communicate through Kubernetes objects and status rather than hidden side channels. That keeps the system inspectable. If a tool creates external resources without writing useful status or events back to Kubernetes, operators lose the trail that makes control plane debugging practical.

Anti-patterns usually come from collapsing responsibilities in your head. If you believe the scheduler creates Pods, you will debug the wrong component when a ReplicaSet fails to create them. If you believe the API server stores durable data locally, you will underinvest in etcd backup. If you believe all control plane replicas are active writers, you will misunderstand leader election. These mistakes are common because the final user experience feels like one command, even though many components did the work.

| Anti-pattern | What goes wrong | Better alternative |
|--------------|-----------------|--------------------|
| Restarting scheduler for every `Pending` Pod | Capacity, taints, affinity, or quotas may be the true reason | Inspect Pod events and node constraints first |
| Treating etcd backup as optional | A lost data store can mean rebuilding the cluster's desired state | Automate snapshots and practice restore on a nonproduction cluster |
| Monitoring only API server process liveness | The API can be alive while storage writes fail | Monitor readiness, request errors, latency, and etcd health together |
| Running "HA" components in one failure domain | One host, rack, or zone failure can remove all replicas | Spread control plane and etcd members across independent failure domains |

There is a practical reason to keep these patterns disciplined. During an incident, every broad restart or speculative config change adds noise to the evidence. Kubernetes already records a lot of state for you, but only if you read it before overwriting it. The better habit is to move from user request to API object, from owner reference to dependent object, from events to component responsibility, and from component responsibility to the narrowest fix.

## Decision Framework

When you face a control plane symptom, start by deciding whether the failure is at the API edge, in durable storage, in reconciliation, in scheduling, or on the node. The first question is whether the API server responds at all. If `k get namespaces` cannot connect, fix kubeconfig, network path, load balancer, certificates, or API server availability before investigating controllers. If the API responds but write operations fail or time out, include etcd health and quorum in the next checks.

If the API accepts the top-level object, trace dependent objects next. A Deployment without a ReplicaSet points toward controller manager behavior, admission side effects, or invalid controller ownership. A ReplicaSet without enough Pods points toward ReplicaSet reconciliation, quotas, or related events. Pods without node assignments point toward scheduler decisions. Pods with node assignments but unhealthy containers point toward kubelet, image, volume, probe, runtime, or application issues.

| Symptom | First likely layer | Useful first checks |
|---------|--------------------|---------------------|
| `k` cannot connect to the cluster | API endpoint or kubeconfig | `k cluster-info`, kubeconfig context, API server endpoint, load balancer health |
| Reads work but writes time out | API server to etcd path | API server readiness, etcd quorum, storage latency, control plane logs |
| Deployment exists but no ReplicaSet appears | Controller manager | Deployment conditions, controller manager health, events, quotas |
| Pod exists but has no node | Scheduler | `k describe pod`, node resources, taints, selectors, affinities |
| Pod has a node but containers are waiting | Kubelet or runtime | Pod events, image pull status, volume mounts, node conditions |
| LoadBalancer Service stays pending | Cloud-controller-manager or cloud provider | Service events, provider permissions, subnets, quotas, cloud integration logs |

For architecture decisions, compare blast radius against complexity. A learning cluster can run a single control plane because downtime is acceptable and simpler operations help students focus. A shared staging cluster may need backup and monitoring even if it does not need full multi-zone HA. A production cluster that supports customer traffic usually needs replicated API servers, reliable etcd quorum, tested restore, and explicit failure-domain planning. There is no magic threshold, but the operational question is whether the business can tolerate losing cluster management during the expected repair window.

Use this decision flow when you need to choose where to look next, and treat each answer as evidence that narrows the next command rather than as a reason to jump randomly across the cluster:

```text
Request or workload symptom
        │
        ▼
Can the API server answer basic reads?
        │
        ├── No  → Check kubeconfig, network, load balancer, API server health
        │
        └── Yes
             │
             ▼
Do writes succeed and persist?
        │
        ├── No  → Check admission failures, authorization, API readiness, etcd quorum
        │
        └── Yes
             │
             ▼
Do dependent objects appear?
        │
        ├── No  → Check controller manager, owner references, quotas, events
        │
        └── Yes
             │
             ▼
Do Pods receive node assignments?
        │
        ├── No  → Check scheduler events, node fit, taints, affinity, resources
        │
        └── Yes → Check kubelet, runtime, image pulls, volumes, probes
```

The framework is intentionally staged because Kubernetes itself is staged. You avoid guessing by following the same path the control plane follows. First a request becomes stored desired state. Then controllers create dependent desired state. Then the scheduler chooses nodes. Then kubelets run containers and report status. A problem can still be subtle, but the search space becomes smaller at every step.

The framework also helps during exam questions because it turns wording into component ownership. Words such as validate, authenticate, authorize, admit, and expose the API point toward kube-apiserver. Words such as store, snapshot, quorum, or durable cluster state point toward etcd. Words such as assign, bind, node selection, taints, and affinities point toward scheduler. Words such as reconcile, desired state, ReplicaSet, node health, and endpoints point toward controller manager. Words such as cloud load balancer, route, and provider node lifecycle point toward cloud-controller-manager.

When you are unsure, ask what object should exist next. If the next missing object is a ReplicaSet, a controller should have created it. If the next missing field is `.spec.nodeName`, the scheduler should have written it. If the next missing status is container readiness, kubelet and the workload are now involved. This object-first framing is simple, but it prevents many expensive detours because it follows Kubernetes' own contract.

## Did You Know?

- **etcd means "/etc distributed"** - The name combines the Unix `/etc` configuration directory with the idea of distributed storage, which fits its role as the cluster's durable configuration record.
- **Leader election prevents conflicting writers** - Multiple scheduler or controller-manager replicas can run, but only the elected leader actively performs a given responsibility while standby replicas wait to take over.
- **The API server is stateless** - API server instances store durable cluster state in etcd rather than local process memory, which is why they can be scaled behind a load balancer.
- **Controllers use watches instead of blind polling** - Watch streams let controllers react to object changes efficiently, using resource versions so they can resume from known points after interruptions.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Saying the scheduler runs Pods | The user sees one `k create deployment` command and assumes one component does all the work | Remember that the scheduler assigns `.spec.nodeName`, while kubelet on that node starts containers |
| Treating etcd as optional | Small clusters hide etcd behind static Pods or managed services | Identify where etcd lives, monitor quorum, and keep tested backups for self-managed clusters |
| Believing the API server stores durable data locally | The API server is the visible entry point for every request | Separate request handling from persistence: API server validates and coordinates, etcd stores state |
| Restarting control plane components before reading events | Incidents create pressure to "do something" quickly | Trace objects and events first so the fix targets the failed stage |
| Expecting every controller-manager replica to act at once | High availability sounds like all replicas are actively writing | Learn leader election: standby replicas are ready, but one leader performs active reconciliation |
| Ignoring cloud-controller-manager during LoadBalancer failures | The Service object exists inside Kubernetes, so the cloud part is easy to forget | Inspect Service events and provider integration when external addresses remain pending |
| Calling a cluster highly available because it has several processes | Diagrams can hide shared hosts, storage, or network failure domains | Spread API servers and etcd members across real failure domains and test failover behavior |

## Quiz

<details><summary>Your team creates a Deployment, the API command returns success, and the Deployment object exists, but no ReplicaSet appears after several minutes. Which control plane area do you investigate first, and why?</summary>

Start with controller reconciliation, especially the kube-controller-manager and the Deployment controller's evidence. The API server already accepted and stored the Deployment, so the request edge is probably not the first failure. The scheduler is also too late in the chain because it only acts on Pods that already exist. Check Deployment conditions, events, controller-manager health, quotas, and owner-reference related errors before changing scheduler settings.
</details>

<details><summary>A Pod is stuck in `Pending`, and `k get pod -o wide` shows an empty node column. What does this tell you about the request flow, and what should you inspect next?</summary>

The Pod has been created, but the scheduler has not successfully bound it to a node. That means controller reconciliation got far enough to create the Pod, while kubelet execution has not started because no node owns the Pod yet. Inspect `k describe pod`, recent events, node capacity, taints, selectors, affinity rules, and resource requests. Container logs are unlikely to help because the container probably has not started.
</details>

<details><summary>An API server process is healthy enough to answer some read requests, but every attempt to create or update objects times out. Which component becomes a serious suspect, and what design principle explains the symptom?</summary>

etcd becomes a serious suspect because writes must be committed to the durable backing store before cluster state can advance. The API server is stateless and coordinates storage rather than keeping the permanent record locally. If etcd has quorum loss, severe latency, or storage pressure, the API endpoint may still appear partially alive while writes fail. Check API readiness, etcd health, quorum, and storage latency together.
</details>

<details><summary>Your colleague says a three-node control plane is automatically highly available because there are three API servers. What important question would you ask before accepting that claim?</summary>

Ask where the etcd members and control plane nodes actually run from a failure-domain perspective. Three API server processes help only if the backing state store and endpoint path can survive realistic failures. If all etcd members sit on the same host, rack, disk system, or zone, one infrastructure failure can still remove the cluster's durable state. High availability requires independent failure domains, quorum planning, and tested recovery, not just process count.
</details>

<details><summary>A LoadBalancer Service stays pending in a managed cloud cluster. The Service object exists, and normal ClusterIP Services work. Which control plane component or integration should you include in the investigation?</summary>

Include the cloud-controller-manager or the managed provider's equivalent cloud integration. A LoadBalancer Service requires Kubernetes desired state to be reconciled into an external cloud load balancer, which depends on provider APIs, permissions, quotas, subnet configuration, and controller health. The core API server may be working perfectly while the external resource remains uncreated. Service events and provider-side diagnostics usually provide the next useful evidence.
</details>

<details><summary>A running application keeps serving traffic after the API server becomes unavailable, but scaling the Deployment fails. How can both observations be true?</summary>

Existing containers can continue running because kubelet and the local container runtime already have the instructions needed to keep them alive. Scaling requires a new write to the Kubernetes API, controller reconciliation, Pod creation, scheduling, and kubelet execution for the new Pods. If the API server is unavailable, that management path cannot advance even though existing runtime state continues. This split is a classic sign that workload execution and control plane management are related but separate.
</details>

<details><summary>You are asked to evaluate whether a failed rollout is a scheduler problem. The Deployment, ReplicaSet, and Pods exist, and each Pod has a node name, but containers are waiting on image pulls. What is your conclusion?</summary>

This is not primarily a scheduler problem because the scheduler has already completed its key responsibility by assigning nodes. The failure is now on the node execution side, involving kubelet, the container runtime, registry access, image name, credentials, or network policy. You should inspect Pod events, image pull error messages, and node-level access to the registry. Restarting scheduler would not address a container image pull failure.
</details>

## Hands-On Exercise

Goal: observe the Kubernetes control plane in action, identify what each core component does, and trace a Pod request from API submission to node placement.

- [ ] Confirm cluster access and identify the control plane node or nodes.
  ```bash
  k cluster-info
  k get nodes -o wide
  ```
  Verification commands:
  ```bash
  k get nodes
  k get namespaces
  ```

- [ ] Inspect the control plane components running in `kube-system`.
  ```bash
  k get pods -n kube-system -o wide
  k get pods -n kube-system | grep -E 'apiserver|etcd|scheduler|controller-manager'
  ```
  Verification commands:
  ```bash
  k get pods -n kube-system --show-labels
  k describe pod -n kube-system <control-plane-pod-name>
  ```

- [ ] Examine the API server and confirm it is the main entry point for cluster operations.
  ```bash
  k describe pod -n kube-system <kube-apiserver-pod-name>
  k get --raw=/readyz
  ```
  Verification commands:
  ```bash
  k api-resources | head
  k version
  ```

- [ ] Inspect `etcd` and connect it to stored cluster state.
  ```bash
  k describe pod -n kube-system <etcd-pod-name>
  k get configmaps,secrets,serviceaccounts -A | head -20
  ```
  Verification commands:
  ```bash
  k get pods -A
  k get svc -A
  ```

- [ ] Inspect the scheduler and controller manager, then identify their separate responsibilities.
  ```bash
  k describe pod -n kube-system <kube-scheduler-pod-name>
  k describe pod -n kube-system <kube-controller-manager-pod-name>
  ```
  Verification commands:
  ```bash
  k get events -A --sort-by=.lastTimestamp | tail -20
  k explain pod.spec.nodeName
  ```

- [ ] Create a Deployment and watch the control plane process it.
  ```bash
  k create deployment control-plane-demo --image=nginx:1.29 --replicas=2
  k get deployment,pods -w
  ```
  Verification commands:
  ```bash
  k describe deployment control-plane-demo
  k describe pod <new-pod-name>
  ```

- [ ] Trace scheduling by checking which node each Pod was assigned to and what events were recorded.
  ```bash
  k get pods -o wide
  k get events --sort-by=.lastTimestamp
  ```
  Verification commands:
  ```bash
  k get pod <new-pod-name> -o jsonpath='{.spec.nodeName}{"\n"}'
  k describe pod <new-pod-name> | grep -A5 Events
  ```

- [ ] Compare your cluster to a high-availability design by counting control plane instances and the Kubernetes service endpoint.
  ```bash
  k get nodes -l node-role.kubernetes.io/control-plane
  k get endpoints kubernetes -n default
  ```
  Verification commands:
  ```bash
  k cluster-info
  k get componentstatuses 2>/dev/null || true
  ```

- [ ] Clean up the exercise resources.
  ```bash
  k delete deployment control-plane-demo
  ```
  Verification commands:
  ```bash
  k get deployment control-plane-demo
  k get pods | grep control-plane-demo
  ```

<details><summary>Solution guidance for tracing the Deployment</summary>

After creating the Deployment, inspect the Deployment first, then the ReplicaSet, then the Pods. The expected object chain is Deployment to ReplicaSet to Pods. The Deployment and ReplicaSet are controller-manager evidence, while the Pod node assignment is scheduler evidence. If the Pods have node names and container statuses, kubelet has already begun the node-side execution stage.
</details>

<details><summary>Solution guidance for identifying component ownership</summary>

Use the symptom-to-component map from the lesson. API connection and validation problems point first to kube-apiserver. Durable write and state recovery problems point toward etcd. Missing dependent objects point toward controller-manager reconciliation. Pods without node names point toward scheduler. Pods with node names but runtime failures point toward kubelet or the node's container runtime.
</details>

Success criteria for this lab are listed below; use them as a final self-check that connects your observed command output back to the architecture model:

- [ ] API server, etcd, scheduler, and controller manager were located in `kube-system` or identified as provider-managed components.
- [ ] The role of each control plane component was matched to real cluster objects or events.
- [ ] A Deployment was created and its Pods were observed moving from requested state to scheduled state.
- [ ] The node assignment for at least one Pod was identified with `k`.
- [ ] The difference between a single control plane and a high-availability layout was described using observed cluster output.
- [ ] The exercise Deployment was removed after verification.

## Sources

- [Kubernetes Documentation: Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/)
- [Kubernetes Documentation: The Kubernetes API](https://kubernetes.io/docs/concepts/overview/kubernetes-api/)
- [Kubernetes Documentation: kube-apiserver](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-apiserver/)
- [Kubernetes Documentation: etcd in Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/#etcd)
- [etcd Documentation: Disaster Recovery](https://etcd.io/docs/v3.6/op-guide/recovery/)
- [Kubernetes Documentation: kube-scheduler](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-scheduler/)
- [Kubernetes Documentation: kube-controller-manager](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-controller-manager/)
- [Kubernetes Documentation: Cloud Controller Manager Administration](https://kubernetes.io/docs/tasks/administer-cluster/running-cloud-controller/)
- [Kubernetes Documentation: Controllers](https://kubernetes.io/docs/concepts/architecture/controller/)
- [Kubernetes Documentation: Highly Available Clusters with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)
- [Kubernetes Documentation: Assigning Pods to Nodes](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/)
- [Kubernetes Documentation: kubectl Quick Reference](https://kubernetes.io/docs/reference/kubectl/quick-reference/)

## Next Module

[Module 1.4: Kubernetes Architecture - Node Components](../module-1.4-node-components/) - Understanding the workers that run your applications and complete the control plane decisions described here.
