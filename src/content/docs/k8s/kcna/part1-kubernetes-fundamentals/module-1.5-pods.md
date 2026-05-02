---
revision_pending: false
title: "Module 1.5: Pods"
slug: k8s/kcna/part1-kubernetes-fundamentals/module-1.5-pods
sidebar:
  order: 6
---

# Module 1.5: Pods

> **Complexity**: `[MEDIUM]` - Core resource concept
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Modules 1.1-1.4, especially API objects and control-plane concepts.

## What You'll Be Able to Do

After completing this module, you will be able to connect Pod design choices to concrete debugging, rollout, and ownership decisions instead of treating Pods as anonymous containers.

1. **Debug** Pod lifecycle issues by interpreting phase, conditions, events, restarts, and container status.
2. **Design** single-container and multi-container Pod patterns that use shared network and storage correctly.
3. **Evaluate** when a standalone Pod is the wrong tool and a Deployment, Job, or DaemonSet should own the Pod.
4. **Implement** a Kubernetes 1.35+ Pod manifest with labels, ports, resources, and volumes that match the workload's intent.

## Why This Module Matters

In February 2017, GitLab.com suffered a production database incident that became public because the team documented the recovery in detail. The failure was not caused by Kubernetes Pods, but the lesson lands directly in Kubernetes operations: systems become fragile when engineers confuse temporary runtime units with durable service ownership. A process, a container, or a Pod can disappear faster than the business impact can be explained, and when the platform has no controller maintaining the desired state, every restart becomes a manual recovery exercise.

Now imagine the same pattern inside a Kubernetes cluster during a payment-service release. A developer creates a single Pod for a hotfix because it is fast, the Pod receives real traffic through an improvised selector, and the application works long enough for everyone to move on. Hours later, the node drains for maintenance, the Pod vanishes, and the service does not come back because no Deployment, ReplicaSet, Job, or DaemonSet owns it. The incident review does not say "Kubernetes failed"; it says the team deployed the wrong abstraction and skipped the part of Kubernetes that continuously reconciles desired state.

Pods are where every Kubernetes workload becomes concrete. Deployments, StatefulSets, Jobs, CronJobs, and DaemonSets all create Pods because the kubelet ultimately starts containers on nodes, attaches volumes, wires networking, and reports status through Pod objects. If you can read a Pod well, you can diagnose why a workload is pending, why traffic is missing, why logs moved, why a sidecar cannot see a file, or why a "Running" application is still unavailable. This module builds that skill carefully: first the Pod model, then networking and storage, then lifecycle, then the decision line between direct Pods and controller-managed workloads.

## The Pod Boundary: One Scheduling Unit, Shared Context

A Pod is the smallest deployable and schedulable unit in Kubernetes, but that sentence hides the most important part of the design. Kubernetes does not schedule individual containers directly because containers sometimes need a shared context that is stronger than "two processes happen to exist in the same cluster." A Pod gives Kubernetes a single object that can be placed on one node, assigned one network identity, attached to the same volumes, and observed as one unit of desired runtime state.

```text
┌─────────────────────────────────────────────────────────────┐
│              WHAT IS A POD?                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  A Pod is:                                                 │
│  • A group of one or more containers                       │
│  • The atomic unit of scheduling                           │
│  • Containers that share storage and network               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                      POD                             │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │  Shared Network Namespace                      │  │   │
│  │  │  • All containers share same IP                │  │   │
│  │  │  • Containers communicate via localhost        │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  │                                                      │   │
│  │  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │ Container 1 │  │ Container 2 │                  │   │
│  │  │   (app)     │  │  (sidecar)  │                  │   │
│  │  └─────────────┘  └─────────────┘                  │   │
│  │                                                      │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │  Shared Storage (Volumes)                      │  │   │
│  │  │  • Both containers can access same files       │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The apartment analogy is useful because it separates a container's identity from the Pod's shared address. A container is like a person with its own job and habits, while a Pod is the apartment where those people live together. They share the same street address, they can talk across the room without going through the public lobby, and they may share a kitchen where files appear for everyone who is allowed to use it. That shared arrangement is powerful when the containers are tightly coupled, and it is costly when they should scale or fail independently.

```text
┌─────────────────────────────────────────────────────────────┐
│              POD vs CONTAINER                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Container:                    Pod:                        │
│  ─────────────────────────────────────────────────────────  │
│  • Single process              • One or more containers    │
│  • Runtime concept             • Kubernetes concept        │
│  • No shared context           • Shared network/storage    │
│  • Isolated                    • Co-located               │
│                                                             │
│  Analogy:                                                  │
│  ─────────────────────────────────────────────────────────  │
│  Container = Person                                        │
│  Pod = Apartment where people live together                │
│                                                             │
│  People in the same apartment:                             │
│  • Share the same address (IP)                            │
│  • Share kitchen and bathroom (volumes)                   │
│  • Can talk directly (localhost)                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

This is why "Pod equals container" is an attractive but incomplete shortcut. Many Pods contain exactly one application container, so the shortcut works during the first week of learning. It breaks the moment you add an init container, a service-mesh proxy, a log shipper, a metrics adapter, or a shared volume. The Pod object is the thing Kubernetes schedules and tracks; the container is one process environment inside that object. That distinction explains why `k get pods` shows Pod state, while `k describe pod` and `k logs` often require you to choose a specific container inside the Pod.

For the rest of this module, assume the common shell alias `alias k=kubectl` is configured before the first command. Kubernetes documentation and production runbooks often use the full `kubectl` name for clarity, but this course uses `k` after introducing the alias once so commands stay readable. The alias does not change behavior; it only shortens the client command that talks to the Kubernetes API server.

```bash
alias k=kubectl
k version --client
```

Pause and predict: if Kubernetes scheduled containers directly instead of Pods, what would happen to two helper containers that must always land on the same node and share the same files? The scheduler would need a second abstraction to express "place these together," and operators would need another place to inspect their combined networking and volume behavior. The Pod solves that by making co-location part of the API object instead of a loose convention in deployment scripts.

The Pod boundary is also the first place beginners meet Kubernetes tradeoffs. Putting two containers in the same Pod gives them fast localhost communication and shared files, but it also couples their scheduling, lifetime, and scale. If one helper must run next to every application replica, the coupling is correct. If the helper is really a shared database, cache, or queue, the coupling is usually wrong because every application replica would drag a separate copy of that stateful dependency along with it.

## Single-Container Pods: The Default Shape

Most Pods in application clusters contain one main container because most services are easiest to reason about when each replica has one primary responsibility. A web API replica, a queue worker replica, or a static file server replica usually needs its own image, environment, ports, resource requests, and probes. Kubernetes still wraps that one container in a Pod because the Pod supplies the node placement, network identity, volume mounts, and lifecycle status used by the rest of the control plane.

```text
┌─────────────────────────────────────────────────────────────┐
│              SINGLE-CONTAINER POD                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                      POD                             │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │           Main Application Container         │    │   │
│  │  │              (e.g., nginx)                   │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  This is the most common pattern:                          │
│  • One container per Pod                                   │
│  • Simple to manage                                        │
│  • Each Pod runs one instance of your app                  │
│                                                             │
│  "One-container-per-Pod" is the standard use case         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A single-container Pod is not a weaker concept than a multi-container Pod. It is simply the most economical expression of the workload. You still get labels for selection, resource requests for scheduling, restart policy behavior, security context, image pull configuration, service account identity, projected configuration, and volume mounts. The key point is that Kubernetes keeps the container runtime detail behind a stable API object, which lets controllers and Services reason about workload instances without depending on Docker, containerd, or CRI-O internals.

When you create a Deployment later in the course, you will write a Pod template inside the Deployment specification. That template is not decorative YAML; it is the blueprint the ReplicaSet controller uses whenever it needs another Pod. If a node fails, the controller does not resurrect the same Pod object. It creates a replacement Pod from the template, with a new identity, a new UID, and often a new IP. Treating Pods as replaceable replicas is one of the mental shifts that separates Kubernetes operations from traditional server administration.

The following conceptual Pod specification is intentionally small, but it captures the pieces you should recognize for KCNA and for real debugging. Metadata gives the Pod a name and labels, `spec.containers` describes what should run, `ports` documents expected container ports, `resources` gives the scheduler and kubelet guardrails, and `volumes` defines shared storage that containers can mount. You do not need to memorize every field, but you should be able to point at a broken Pod manifest and ask which section controls the observed behavior.

```yaml
# Pod Specification - Key Parts
apiVersion: v1
kind: Pod
metadata:
  name: my-pod          # Pod name
  labels:               # Labels for selection
    app: web
spec:
  containers:           # List of containers
  - name: app           # Container name
    image: nginx:1.25   # Container image
    ports:              # Exposed ports
    - containerPort: 80
    resources:          # Resource limits
      limits:
        memory: "128Mi"
        cpu: "500m"
  volumes:              # Shared storage
  - name: data
    emptyDir: {}
```

The manifest above is also a useful diagnostic checklist. If the Pod never schedules, inspect resource requests, node selectors, tolerations, affinity, and quota before staring at application code. If the Pod schedules but the container cannot start, inspect the image name, image pull credentials, command, arguments, environment, mounted configuration, and volume references. If the container starts but the service has no endpoints, inspect labels, readiness probes, and the Service selector. The Pod is not the whole application, but it is the most honest place to see whether the application replica actually exists.

Before running this, what output do you expect from a standalone Pod that has one container and no Service? You should expect `k get pod` to show a Pod and `k get pod -o wide` to show a cluster-internal IP, but you should not expect a stable external address. A Pod IP is an implementation detail of one replica, not a durable contract for clients. Services, Ingress, and Gateway API resources exist because clients need a stable way to find changing Pods.

```bash
k run pod-demo --image=nginx:1.25 --restart=Never --port=80
k get pod pod-demo -o wide
k describe pod pod-demo
k delete pod pod-demo
```

The command above is useful for learning and quick experiments, not as a production deployment pattern. A standalone Pod has no controller maintaining a replica count, no rolling update strategy, and no automatic replacement after deletion. Kubernetes may restart containers inside the same Pod according to the Pod restart policy while the Pod remains on the node, but if the Pod object is deleted or the node disappears, a direct Pod has no higher-level owner to recreate it. That is why the right production question is rarely "how do I create a Pod?" and more often "which controller should own this Pod template?"

## Multi-Container Pods: Sidecars, Ambassadors, and Adapters

Multi-container Pods exist for containers that form one tightly coupled unit of work. The important phrase is not "multiple containers"; it is "tightly coupled." Containers in the same Pod share a network namespace, can share volumes, are scheduled together, and are usually created and removed together. That makes the pattern valuable for helper responsibilities that are inseparable from one application replica, but it makes the pattern risky for dependencies that deserve independent scaling, independent upgrades, or independent persistence.

```text
┌─────────────────────────────────────────────────────────────┐
│              MULTI-CONTAINER PATTERNS                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SIDECAR PATTERN                                           │
│  ─────────────────────────────────────────────────────────  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  POD                                                 │   │
│  │  ┌─────────────────┐  ┌─────────────────┐          │   │
│  │  │   Main App      │  │   Log Shipper   │          │   │
│  │  │   (writes logs) │─→│   (reads logs)  │          │   │
│  │  └─────────────────┘  └─────────────────┘          │   │
│  │               └────────────┘                        │   │
│  │                Shared volume                        │   │
│  └─────────────────────────────────────────────────────┘   │
│  Example: Main app + Fluentd sidecar for logging          │
│                                                             │
│  AMBASSADOR PATTERN                                        │
│  ─────────────────────────────────────────────────────────  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  POD                                                 │   │
│  │  ┌─────────────────┐  ┌─────────────────┐          │   │
│  │  │   Main App      │  │    Proxy        │          │   │
│  │  │   (localhost)   │─→│   (outbound)    │─→ External│   │
│  │  └─────────────────┘  └─────────────────┘          │   │
│  └─────────────────────────────────────────────────────┘   │
│  Example: App + Envoy proxy for service mesh              │
│                                                             │
│  ADAPTER PATTERN                                           │
│  ─────────────────────────────────────────────────────────  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  POD                                                 │   │
│  │  ┌─────────────────┐  ┌─────────────────┐          │   │
│  │  │   Main App      │  │    Adapter      │          │   │
│  │  │  (custom format)│─→│(standard format)│─→ Monitor │   │
│  │  └─────────────────┘  └─────────────────┘          │   │
│  └─────────────────────────────────────────────────────┘   │
│  Example: App + Prometheus exporter adapter               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The sidecar pattern is the easiest one to justify because the helper exists to extend the main container without changing the main image. A log shipper can read a shared file volume, a configuration reloader can watch projected ConfigMap data, or a service-mesh proxy can intercept local traffic. The application remains focused on business logic while the sidecar handles a cross-cutting responsibility. The tradeoff is operational coupling: every replica now consumes resources for both containers, and a broken sidecar can make a healthy application replica unready or noisy.

The ambassador pattern puts a proxy next to the application so the application talks to `localhost` while the proxy handles external connection details. This was common before service meshes became mainstream, and it remains useful when one process needs a narrow network helper with the same lifecycle. The adapter pattern normalizes output from the main application, such as converting a custom metrics format into something a monitoring system can scrape. Both patterns are useful only when the helper is part of the same replica-level behavior, not when it is a general shared service.

Stop and think: in the sidecar pattern, a log shipper container runs alongside the main application. Why put them in the same Pod instead of separate Pods? The answer is not "because Kubernetes supports it." The answer is that a same-Pod sidecar can read the same volume path and coordinate with the application over localhost without inventing a network file-sharing system or a second discovery mechanism. If separate Pods need the same data, you are now designing distributed storage and service discovery, which is a larger problem than log shipping.

The most common mistake is to use a multi-container Pod as a small private server group. For example, placing an API container and a Redis cache in the same Pod may feel efficient because the API can reach Redis on localhost. It also means every API replica carries its own cache, Redis cannot scale or upgrade independently, and persistent data becomes tangled with application rollout cadence. If Redis is a real service dependency, run it through its own controller and expose it with a Service. If it is a disposable per-replica helper, then a same-Pod pattern may be appropriate.

Init containers are a related but distinct Pod feature. They run to completion before the app containers start, and they are useful for setup tasks such as waiting for a dependency, generating a file, or preparing permissions. They are not long-running sidecars, and they should not be used to hide fragile startup assumptions. If an application cannot start until a database migration completes, that deserves an explicit rollout design, not an init container that quietly loops forever and leaves the Pod in an unhelpful waiting state.

Which approach would you choose here and why: a metrics exporter that reads a local Unix socket created by the application, or a shared Postgres database used by every application replica? The exporter is a strong sidecar candidate because it is attached to one replica's local process boundary. The database is not a sidecar candidate because it is a stateful service with its own availability, backup, scaling, and upgrade needs. This question is the heart of multi-container Pod design: co-locate what is inseparable, separate what has its own lifecycle.

## Pod Networking and Storage: One IP, Many Ports, Shared Volumes

Every Pod receives its own network namespace and usually one routable cluster IP address. Containers inside that Pod share the namespace, which means they see the same network interfaces and can reach each other through `localhost` on different ports. From outside the Pod, other Pods do not address individual containers; they address the Pod IP and a port. This is why two containers in one Pod cannot both bind the same port on the same interface, just as two processes on one Linux host cannot both listen on `0.0.0.0:8080`.

```text
┌─────────────────────────────────────────────────────────────┐
│              POD NETWORKING                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Each Pod gets:                                            │
│  • Its own unique IP address                               │
│  • Can be reached directly by other Pods                   │
│  • Containers in Pod share this IP                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  POD (IP: 10.1.1.5)                                 │   │
│  │  ┌────────────┐    ┌────────────┐                  │   │
│  │  │Container A │    │Container B │                  │   │
│  │  │ Port 80    │    │ Port 8080  │                  │   │
│  │  └────────────┘    └────────────┘                  │   │
│  │         │                  │                        │   │
│  │         └────────┬─────────┘                        │   │
│  │                  │                                  │   │
│  │           localhost:80   localhost:8080             │   │
│  │           (within Pod)   (within Pod)              │   │
│  └─────────────────────────────────────────────────────┘   │
│                     │                                       │
│              10.1.1.5:80    10.1.1.5:8080                  │
│              (from outside Pod)                            │
│                                                             │
│  Within Pod: Use localhost                                 │
│  Between Pods: Use Pod IP                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The Pod network model is deliberately simpler than traditional host networking. Kubernetes expects every Pod to be able to communicate with every other Pod without network address translation inside the cluster, although network policies and cloud routing determine what is actually allowed in a given environment. The practical result is that application authors can think in terms of Pod IPs and Services instead of manually mapping host ports. The operational result is that Pod IPs are disposable, so stable client traffic must go through a Service, Ingress, Gateway, or another deliberate routing layer.

Storage follows the same "shared context, disposable Pod" pattern. A Pod can define volumes, and containers can mount those volumes at paths inside their filesystems. An `emptyDir` volume is created when the Pod is assigned to a node and removed when the Pod is removed from that node, making it useful for scratch space and same-Pod file exchange. Persistent storage uses PersistentVolumeClaims and storage classes, but the Pod still mounts the claim as a volume. The Pod is the place where storage is attached to a running replica, not the place where durable application ownership should be hidden.

A small reference table helps keep the container comparison precise while avoiding a false either-or mindset. Containers are runtime units, Pods are Kubernetes API units, and controllers are desired-state managers that create and replace Pods. When debugging, identify which level owns the symptom before changing anything. A container crash may need image or command fixes, a Pod scheduling failure may need resource or placement fixes, and a Deployment rollout issue may need template or strategy fixes.

| Concept | Scope | Shared Context | Operational Question |
|---------|-------|----------------|----------------------|
| Container | One process environment | Shares only what the Pod grants | Why did this process start, stop, or fail? |
| Pod | One schedulable Kubernetes unit | Network namespace and selected volumes | Why did this replica schedule, run, or become ready? |
| Controller | Desired state over many Pods | Pod template and reconciliation loop | Why are the expected replicas not present or updated? |
| Service | Stable access to selected Pods | Virtual IP or DNS name over endpoints | Why can or cannot clients reach healthy replicas? |

The beginner mistake table is compact because these four distinctions are the minimum conceptual traps. In a mature cluster, the same misunderstandings show up in more expensive forms: dashboards that page on container status but ignore Pod readiness, scripts that call Pod IPs directly, and rollout plans that treat one replacement Pod as if it were the same machine returning to service. Keep the table close when diagnosing a beginner explanation or an incident narrative.

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| "Pod = Container" | Missing Pod abstraction | Pod contains container(s) |
| "Pods have multiple IPs" | Misunderstanding networking | One IP per Pod, shared by containers |
| "Create Pods directly" | No resilience | Use Deployments instead |
| "Pods persist after deletion" | Treating as VMs | Pods are ephemeral |

Networking and storage also explain why readiness matters. A Pod can have an IP before the application is safe to receive traffic, and a container can have a mounted volume before the data inside it is ready. Readiness probes give Kubernetes a workload-specific answer to "should this Pod receive traffic now?" Liveness probes answer a different question: "should this container be restarted because it appears stuck?" Startup probes protect slow-starting applications from being killed before they have a fair chance to initialize. None of those probes change what a Pod is, but they make the Pod's status more useful to controllers and traffic routers.

## Pod Lifecycle: From Scheduling to Termination

Pod lifecycle debugging starts with phases, but phases are only the outer shell of the truth. A Pod can be `Pending`, `Running`, `Succeeded`, `Failed`, or `Unknown`, yet the reason behind that phase lives in conditions, container states, events, and controller ownership. KCNA expects you to recognize the basic phases, while real operations requires you to connect the phase to the next diagnostic command. The habit to build is simple: read the phase, then immediately ask which component is responsible for the transition that did not happen.

```text
┌─────────────────────────────────────────────────────────────┐
│              POD LIFECYCLE PHASES                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pending ──────→ Running ──────→ Succeeded/Failed         │
│                                                             │
│  PENDING:                                                  │
│  • Pod accepted but not running yet                        │
│  • Waiting for scheduling                                  │
│  • Waiting for image pull                                  │
│                                                             │
│  RUNNING:                                                  │
│  • Pod bound to a node                                     │
│  • At least one container running                          │
│  • Or starting/restarting                                  │
│                                                             │
│  SUCCEEDED:                                                │
│  • All containers terminated successfully                  │
│  • Won't be restarted                                      │
│  • Common for Jobs                                         │
│                                                             │
│  FAILED:                                                   │
│  • All containers terminated                               │
│  • At least one failed (non-zero exit)                    │
│                                                             │
│  UNKNOWN:                                                  │
│  • Cannot get Pod state                                    │
│  • Usually communication error                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

`Pending` means the API server accepted the Pod object, but the Pod is not fully running on a node. That could mean the scheduler has not found a node because requests are too large, node selectors do not match, taints are not tolerated, or quotas block admission. It could also mean the Pod is already assigned to a node but a container image is still pulling. Those are different problems, so a useful runbook does not stop at "Pending." It reads `k describe pod`, checks events, and identifies whether the scheduler, kubelet, container runtime, registry, or admission layer is the current blocker.

`Running` means the Pod is bound to a node and at least one container is running or in the process of starting or restarting. It does not guarantee the application is healthy, reachable, or ready for traffic. A Pod can be Running while its only container loops through crashes, while a sidecar is healthy but the main app is broken, or while readiness is false because the application has not warmed its caches. This is why production dashboards that treat Running as "good" create blind spots. For service availability, readiness and endpoint membership usually matter more than the broad Pod phase.

`Succeeded` and `Failed` matter most for finite workloads such as Jobs, one-time maintenance tasks, and batch processing. A Deployment Pod should not normally end in Succeeded because a web server is expected to keep running. A Job Pod, however, should end in Succeeded when all containers complete with exit code zero. If a Job Pod fails repeatedly, the question is not "how do I keep this Pod alive?" but "why does this finite task exit non-zero, and what does the Job controller's retry policy do next?" The Pod phase tells you what happened to one attempt; the controller tells you what happens next.

`Unknown` is a communication symptom, not an application diagnosis. The control plane cannot determine the Pod state, often because the node is unreachable or the kubelet stopped reporting. During node failures, this is where the distinction between a Pod and its owner becomes operationally important. A directly created Pod may remain in a confusing state until cleanup, while a controller-managed workload can create replacement Pods elsewhere according to its reconciliation logic and disruption rules.

A practical debugging flow starts with a wide listing, moves to a detailed description, then inspects logs and events. Use `k get pod -o wide` to learn the node, IP, readiness, restarts, and age. Use `k describe pod` to see conditions, container states, image pull messages, scheduling events, and volume mount errors. Use `k logs` for application output, and add `-c <container>` when a Pod has more than one container. If the container restarted, `k logs --previous` often gives the only clue from the failed process.

```bash
k get pods -o wide
k describe pod pod-demo
k logs pod-demo
k logs pod-demo -c app --previous
```

War story: a platform team once chased a "network outage" because customers saw intermittent 503 responses after a release. The Pods all showed `Running`, which delayed the investigation. The real issue was a readiness probe that pointed at a shallow TCP port instead of an application health endpoint, so Pods entered the Service before their dependency cache had loaded. The fix was not a network change; it was a better readiness probe and a rollout policy that respected application warm-up. The Pod phase was technically true and operationally insufficient.

The most useful question during lifecycle work is "who can make this state change?" The scheduler can place a pending Pod on a node, the kubelet can start containers and report status, the container runtime can pull and launch images, the application can pass or fail probes, and controllers can create replacement Pods. A human with `k delete pod` can force a controller to create a new replica, but that only helps when the owner and template are correct. Deleting a standalone Pod is not healing; it is removal.

## Pod Ownership: Direct Pods vs Deployments, Jobs, and DaemonSets

The rule of thumb is intentionally blunt: almost never create Pods directly for production services. Direct Pods are helpful for learning, troubleshooting, and short-lived experiments because they expose the raw object without controller machinery. Production workloads need desired-state ownership. A Deployment maintains a replicated stateless service, a Job manages finite work, a CronJob schedules repeated finite work, a DaemonSet runs one Pod per selected node, and a StatefulSet manages stateful replicas with stable identities. Those controllers all create Pods, but they answer different operational questions.

```text
┌─────────────────────────────────────────────────────────────┐
│              POD vs DEPLOYMENT                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Creating a Pod directly:                                  │
│  • Pod dies → It's gone                                    │
│  • No automatic restart                                    │
│  • No scaling                                              │
│  • Manual management                                       │
│                                                             │
│  Using a Deployment:                                       │
│  • Deployment manages Pods                                 │
│  • Pod dies → Deployment creates new one                  │
│  • Easy scaling (replicas: 3)                             │
│  • Rolling updates                                         │
│                                                             │
│  Rule of thumb:                                            │
│  ─────────────────────────────────────────────────────────  │
│  Almost NEVER create Pods directly                        │
│  Use Deployments, Jobs, DaemonSets instead                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

This distinction is not academic because every controller encodes a recovery promise. A Deployment says, "keep this many replicas of this Pod template available and roll template changes gradually." A Job says, "run this task until the required completions succeed or the retry policy says stop." A DaemonSet says, "ensure each matching node runs a copy." A direct Pod says almost none of that. It records an instruction to run containers as one schedulable unit, and once that object is gone, Kubernetes has no higher-level desired state to restore.

When evaluating whether a standalone Pod is acceptable, ask what should happen after failure, deletion, rollout, scale change, and node maintenance. If the answer includes "another copy should appear," "traffic should keep flowing," "I need multiple replicas," or "I need rollout history," the answer is not a direct Pod. If the answer is "I need to reproduce a container startup issue once," "I need a temporary network test," or "I am learning the fields in a Pod spec," a direct Pod can be appropriate. The tool is not forbidden; it is narrow.

Kubernetes ownership also affects how you interpret labels. A Service selects Pods by labels, not by controller names, so a direct Pod with matching labels can accidentally receive production traffic if it shares selectors with a real application. This is one reason temporary Pods should use clearly isolated labels and namespaces. Labels are powerful because they decouple traffic routing from object names, but the same decoupling can route traffic to the wrong replica if you casually copy labels from a Deployment template into an experimental Pod.

The lifecycle relationship between Deployment, ReplicaSet, and Pod will matter more in the next module, but you need the concept now. A Deployment owns a ReplicaSet, and the ReplicaSet owns Pods created from a specific Pod template. During a rolling update, the Deployment creates a new ReplicaSet and gradually shifts replicas from the old template to the new one. The Pod is the visible runtime object, but the owner references tell you which controller will react if that Pod disappears. In incident work, checking `OwnerReferences` is often the difference between a safe deletion and a service outage.

If you are unsure whether a Pod is directly created or controller-managed, inspect its owner. `k get pod <name> -o yaml` shows metadata, including owner references when present. A Deployment-managed Pod usually shows a ReplicaSet owner, and the ReplicaSet is in turn owned by a Deployment. A direct Pod lacks that chain. That absence is a warning for long-running services because there is no controller waiting to replace it after deletion or node loss.

```bash
k get pod pod-demo -o yaml
k get pod pod-demo -o jsonpath='{.metadata.ownerReferences[0].kind}{"\n"}'
```

### Worked Example: Reading a Pod Like a Runbook

A strong Pod troubleshooting habit is to read from the outside inward. Start with the owner because ownership tells you whether the Pod is supposed to be replaced, retried, or left alone. Then read placement because node assignment tells you whether the scheduler already made a decision. Then read container states because the kubelet and container runtime report image, command, restart, and exit behavior there. Finally read application logs because logs explain what the process did after Kubernetes successfully handed it a runtime environment.

Suppose a payment worker has one Pod in `CrashLoopBackOff`, while the Deployment still shows the desired replica count. The first useful conclusion is that the controller is doing its job: it has a Pod, and the kubelet is repeatedly trying to run the container. The second useful conclusion is that deleting the Pod may create a replacement with the same broken template. A better first action is to read the previous container logs and termination state, then decide whether the image, command, environment, mounted Secret, or application configuration is wrong.

Now suppose another Pod is `Pending` and has no node assigned. Logs will not help because no container has started. The useful evidence lives in events and scheduling constraints: insufficient memory, untolerated taints, node affinity that matches no nodes, a missing PersistentVolume, or a namespace quota that blocks the request. Rebuilding the image is wasted effort in that situation because the application process has not had a chance to run. This is the kind of distinction KCNA scenarios test indirectly: the right next step depends on which layer owns the current state.

Finally suppose a Pod is `Running`, all containers show zero restarts, and the Service still sends no traffic. That is not a contradiction. The Service may select labels that the Pod does not have, the readiness probe may be failing, or the EndpointSlice controller may be correctly excluding the Pod because it is not ready. The runbook should compare labels, readiness conditions, and endpoints before changing the container image. In Kubernetes, availability is a chain of objects, and the Pod is only one link in that chain.

This worked example also explains why one command rarely proves the whole story. `k get pods` is a summary, not a diagnosis. `k describe pod` adds events and conditions, but it can be noisy and historical. `k logs` sees only container output, not scheduler decisions. YAML output exposes ownership and exact spec fields, but it can hide the human narrative inside hundreds of lines. Experienced operators move between these views because each one answers a different question about the same Pod.

The final discipline is to separate observation from repair. If a controller owns the Pod and the template is wrong, fix the controller's template rather than patching one replacement Pod by hand. If a direct Pod exists only for a lab, deleting it may be a clean reset. If a direct Pod carries production traffic, deletion can be an outage. The same API command can be harmless, helpful, or destructive depending on ownership, labels, and traffic routing, which is why Pod literacy matters before you reach for fast fixes.

## Patterns & Anti-Patterns

Patterns help you choose the Pod shape that matches the operational behavior you actually want. The same YAML can look harmless in a review and still encode the wrong lifecycle. Good Pod design starts by deciding which containers must be co-located, which resources must be shared, which dependencies need independent control, and which controller should own replacement behavior. The patterns below are less about memorizing names and more about building the judgment to explain your choice during an incident or design review.

| Pattern | When to Use | Why It Works | Scaling Consideration |
|---------|-------------|--------------|-----------------------|
| Single application container | Stateless service replica, worker, or simple utility process | Keeps each Pod focused on one main process and one health model | Scale replicas through a Deployment, Job, or other owner |
| Sidecar helper | Logging, mesh proxy, local metrics exporter, or config helper tied to each replica | Shares localhost and volumes without modifying the main image | Every replica pays the helper's CPU and memory cost |
| Init container setup | One-time preparation before app containers start | Separates setup logic from the long-running app image | Long init waits delay readiness and can hide dependency problems |
| Controller-owned Pod template | Any production workload that must recover, scale, or update predictably | Lets controllers reconcile desired state after Pod loss | Choose Deployment, Job, DaemonSet, or StatefulSet by workload behavior |

Anti-patterns usually come from convenience under pressure. A direct Pod is faster than writing a Deployment, a same-Pod database feels simpler than creating a Service, and copying labels from production makes test traffic easy. Those shortcuts are dangerous because they blur ownership boundaries. Kubernetes gives you sharp tools for placement, identity, and selection, so a small YAML mistake can change who receives traffic, who owns recovery, and where state lives.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|-------------------|
| Direct Pod for a production web service | Pod loss becomes service loss because no controller recreates it | Use a Deployment with replicas and probes |
| Database inside every app Pod | State scales with app replicas and upgrades become tangled | Run the database as its own managed service or StatefulSet |
| Sidecar for unrelated shared dependency | Independent service becomes coupled to one app lifecycle | Expose the dependency through a Service |
| Reusing production labels on test Pods | Services may send real traffic to experiments | Use isolated namespaces and labels |
| Treating Running as healthy | Traffic can reach an app that is alive but not ready | Configure readiness, liveness, and startup probes deliberately |

The repeatable pattern is to draw the lifecycle first. If two processes must start together, share files, and disappear together, a Pod boundary may be right. If two components need different replica counts, upgrade windows, data retention, or ownership teams, put them behind a network contract instead of forcing them into one Pod. Kubernetes makes both options possible, so the engineer's job is to make the coupling explicit before the platform enforces it for you.

## Decision Framework

Use this decision framework when you are reviewing a Pod design, debugging a failed workload, or answering a KCNA-style scenario. Start with the business behavior, then map it to Kubernetes ownership. Do not start with "how many containers can I fit in one Pod?" because that question optimizes for YAML shape instead of operational correctness. The better question is "what should Kubernetes preserve, replace, scale, and expose?"

```text
Need to run workload?
        │
        ├─ One-time or finite task?
        │       ├─ Yes → Job or CronJob owns the Pod template
        │       └─ No
        │
        ├─ Long-running stateless service?
        │       ├─ Yes → Deployment owns replicated Pods
        │       └─ No
        │
        ├─ One Pod on each selected node?
        │       ├─ Yes → DaemonSet owns Pods
        │       └─ No
        │
        ├─ Stable identity or ordered stateful replicas?
        │       ├─ Yes → StatefulSet owns Pods
        │       └─ No
        │
        └─ Temporary experiment or diagnostic?
                ├─ Yes → Direct Pod may be acceptable
                └─ No → Revisit workload requirements
```

The second layer of the framework decides whether the Pod should contain one container or several. Start with one main container because it gives you the clearest health, resource, log, and rollout model. Add a sidecar only when the helper must share the same Pod-level network or storage boundary as each replica. Add an init container only when the setup is finite, deterministic, and safe to repeat. If you cannot explain the shared boundary in one sentence, the components probably belong in separate Pods.

| Decision | Choose This | Avoid This |
|----------|-------------|------------|
| Production stateless API | Deployment with one main container per Pod | Direct Pod copied from a debugging command |
| Per-replica log file shipper | Sidecar with shared volume | Separate Pod that scrapes node files with broad permissions |
| Startup file generation | Init container writing to shared volume | Main app image bloated with cluster-specific setup scripts |
| Shared cache or database | Separate controller and Service | Same Pod as every application replica |
| Cluster-level node agent | DaemonSet | Manually created Pod on selected nodes |
| One-off data repair | Job with explicit completion behavior | Long-running Deployment that exits immediately |

Apply the framework to the Redis example in the quiz. If Redis is a real cache shared by multiple application replicas, it has its own lifecycle and should not be in the same Pod as the app. If each app replica needs a tiny disposable local cache that is valid only for that replica, a same-Pod helper might make sense. The technical difference is not "Redis is special"; the difference is whether the dependency is per-replica and disposable or shared and independently operated.

The framework becomes more useful when you write the reason beside the YAML. A review comment such as "sidecar shares an `emptyDir` with the app so every replica ships its own local log file" is clear and testable. A comment such as "Redis is in the Pod because localhost is faster" is a warning because it optimizes one connection path while ignoring lifecycle and state. Good Kubernetes design records why a component shares the Pod boundary, why another component gets a Service boundary, and why a controller owns replacement behavior. Those reasons help future operators debug the system without rediscovering the design from scattered manifests.

In exam scenarios, watch for verbs that imply ownership. "Scale," "roll out," "replace," "run on every node," "complete once," and "schedule every night" are controller words, not direct-Pod words. Watch for phrases that imply shared context, such as "same local file," "same network namespace," "localhost proxy," or "per-replica helper." Those phrases point toward Pod composition decisions. If a question mixes the two, solve ownership first and composition second. A well-designed Deployment can still have a bad sidecar, but a perfect sidecar inside a direct production Pod still leaves the service without replacement semantics.

## Did You Know?

- **Pods are ephemeral** - They're designed to be disposable. When a Pod dies, it's gone forever, and even a replacement with the same generated name is a new object with a new UID.

- **The pause container** - Every Pod has a hidden "pause" or sandbox container that holds network namespaces. Application containers join its namespace so they can share the Pod IP and localhost.

- **Pod IP is internal** - Pod IPs are only routable within the cluster network. You can't reach them from outside the cluster without a Service, Ingress, Gateway, port-forward, or another exposure mechanism.

- **Pods have unique names** - In a namespace, Pod names must be unique. Controllers commonly add generated suffixes, such as `nginx-7b8d6c-xk4dz`, so replacement Pods do not pretend to be the same object.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Treating a Pod as a durable server | Traditional operations trained teams to repair named machines in place | Treat Pods as replaceable replicas and put durable behavior in controllers, volumes, and Services |
| Creating a direct Pod for a production service | `k run` is fast and gives instant feedback during experiments | Use a Deployment or another controller so failed or deleted Pods are recreated |
| Assuming `Running` means ready for traffic | The Pod phase is visible, simple, and easy to put on a dashboard | Check readiness, endpoint membership, container states, restarts, and application logs |
| Placing shared databases in application Pods | Localhost feels simpler than Service discovery | Run stateful dependencies with their own lifecycle, storage, backups, and network contract |
| Forgetting that containers in a Pod share one IP | People picture each container as a tiny VM with its own address | Use different ports on localhost inside the Pod and the same Pod IP from outside |
| Reusing production selectors on temporary Pods | Copying YAML is faster than designing test labels | Isolate experiments with distinct namespaces and labels before creating Services or Pods |
| Ignoring owner references during cleanup | A Pod name looks like the only object involved | Inspect owners before deleting so you know whether a controller will replace the Pod |

## Quiz

<details>
<summary>Your team deployed a checkout API as a direct Pod during an incident. The node is drained for maintenance and checkout disappears. What failed in the design, and what should own the replacement behavior?</summary>

The design failed because a direct Pod records one desired runtime object but does not maintain a replica count after deletion or node loss. A long-running stateless checkout API should normally be owned by a Deployment, which creates ReplicaSets and replacement Pods from a template. The Deployment gives the team rolling updates, scaling, and reconciliation instead of relying on a human to recreate a Pod. The immediate recovery may be to create a Deployment from the same template, but the lasting fix is to remove the direct-Pod deployment path.
</details>

<details>
<summary>A Pod is `Running`, but the Service has no ready endpoints and users receive 503 responses. What do you inspect first, and why is the Pod phase not enough?</summary>

Start by checking readiness status, Service selectors, endpoint objects, and `k describe pod` events. The `Running` phase only says the Pod is bound to a node and at least one container is running or starting; it does not prove the application passed its readiness probe. A wrong selector can also keep healthy Pods out of the Service. The right diagnosis compares the Pod labels, readiness condition, and Service endpoint membership instead of treating the phase as availability.
</details>

<details>
<summary>An application writes logs to `/var/log/app.log`, and a log shipper must send that file to a central system. Should the shipper be a sidecar or a separate shared service?</summary>

A sidecar is a strong fit when the shipper is tied to one application replica and needs direct access to a shared volume path. The application writes the file, the sidecar reads the same mounted volume, and both containers follow the same replica lifecycle. A separate shared service would need another mechanism to read the file, which usually means broader permissions or a more complicated storage design. The sidecar still needs resource limits and health behavior because a broken helper can affect every replica.
</details>

<details>
<summary>Two containers in the same Pod both try to bind port 8080. The first starts, and the second fails. What Kubernetes concept explains the failure?</summary>

Containers in the same Pod share one network namespace, so they behave like processes on the same machine from a port-binding perspective. Only one process can listen on the same address and port combination at a time. The fix is to configure distinct ports, such as 8080 for the application and 9090 for the helper, or to separate the containers into different Pods if they do not need shared localhost behavior. Giving each container a different name does not give it a separate Pod IP.
</details>

<details>
<summary>A Job Pod ends in `Succeeded`, but a Deployment Pod ending in `Succeeded` would be suspicious. Why do those cases mean different things?</summary>

A Job is designed for finite work, so `Succeeded` means the task completed with successful container exits. A Deployment usually represents a long-running service, so a Pod that exits successfully may mean the application process ended when it was expected to keep serving. The same Pod phase must be interpreted through the owner and workload type. That is why lifecycle debugging includes owner references and controller intent, not only the phase string.
</details>

<details>
<summary>Your team wants to put Redis in the same Pod as every API replica for faster localhost access. What tradeoff should make you push back?</summary>

Putting Redis in every API Pod couples cache lifecycle and scale to API replicas. If the API scales to many replicas, the team gets many Redis instances, each with separate memory, data, upgrade timing, and failure behavior. A shared cache usually needs its own controller, Service, resource plan, backup story if data matters, and independent rollout. Same-Pod placement is only reasonable if the cache is disposable and strictly per-replica.
</details>

<details>
<summary>A Pod stays `Pending` after creation. Which categories of evidence help you debug the lifecycle issue before changing the application image?</summary>

Inspect scheduling and kubelet evidence before changing application code. `k describe pod` events can show insufficient CPU or memory, node selector mismatch, untolerated taints, quota problems, image pull errors, or volume mount failures. `k get pod -o wide` can show whether a node has been assigned. A pending Pod often means the platform cannot place or prepare the Pod, so rebuilding the image may be unrelated to the actual blocker.
</details>

## Hands-On Exercise

This exercise uses a temporary namespace and direct Pods because the goal is to inspect raw Pod behavior before the next module adds workload controllers. You can run it on a local learning cluster or a disposable namespace in a shared cluster. Keep the direct Pods out of production labels and delete the namespace when finished so no temporary object can accidentally match a real Service selector.

- [ ] Implement a Kubernetes 1.35+ namespace named `pod-lab` and create a single-container Pod with the `nginx:1.25` image, label `app=pod-lab-web`, container port 80, and modest CPU and memory limits.
- [ ] Compare the Pod's container view and Pod view with `k get pod -n pod-lab -o wide`, `k describe pod -n pod-lab`, and `k logs -n pod-lab`.
- [ ] Design a multi-container Pod in `pod-lab` with one application container and one sidecar that share an `emptyDir` volume for a simple file handoff.
- [ ] Debug a Pod lifecycle issue by intentionally using a bad image tag, then inspect phase, conditions, events, and container status until you can explain the failure.
- [ ] Evaluate whether each Pod in the lab should remain standalone or be owned by a Deployment, Job, or DaemonSet in a real environment.
- [ ] Clean up every lab object and confirm the namespace no longer contains Pods.

<details>
<summary>Suggested solution</summary>

Create the namespace first, then apply a Pod manifest rather than relying only on generated commands. The manifest should use a unique label that cannot overlap with production selectors. After the Pod starts, inspect the wide output for node and IP, describe it for conditions and events, and read logs from the container. For the sidecar task, mount the same `emptyDir` volume into both containers and make one container write a file while the other reads or serves it. For the bad image task, use a clearly invalid tag such as `nginx:no-such-training-tag`, then use events and container state to explain the image pull failure. Finally, delete the namespace with `k delete namespace pod-lab` and verify no Pods remain.
</details>

<details>
<summary>Success criteria</summary>

You are finished when you can point to the Pod IP, node name, labels, owner references, container states, restart count, and recent events for each lab Pod. You should also be able to explain why the single-container Pod is simple, why the sidecar Pod shares network and storage, why the broken image Pod is a lifecycle failure rather than an application readiness failure, and why production services should be moved into controllers. If you cannot explain which controller would own a real version of each Pod, repeat the decision framework before moving on.
</details>

## Sources

- [Kubernetes documentation: Pods](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Kubernetes documentation: Pod lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Kubernetes documentation: Init containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [Kubernetes documentation: Sidecar containers](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/)
- [Kubernetes documentation: Workload resources](https://kubernetes.io/docs/concepts/workloads/)
- [Kubernetes documentation: Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kubernetes documentation: Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [Kubernetes documentation: DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)
- [Kubernetes documentation: Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Kubernetes documentation: Configure probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Kubernetes documentation: Resource management for Pods and containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Kubernetes documentation: Volumes](https://kubernetes.io/docs/concepts/storage/volumes/)
- [GitLab: GitLab.com Database Incident](https://about.gitlab.com/blog/gitlab-dot-com-database-incident/)

## Next Module

[Module 1.6: Workload Resources](../module-1.6-workload-resources/) - Deployments, ReplicaSets, Jobs, DaemonSets, and other controllers that manage Pods instead of leaving replicas alone.
