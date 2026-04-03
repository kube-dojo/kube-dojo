---
title: "Module 1.5: Pods"
slug: k8s/kcna/part1-kubernetes-fundamentals/module-1.5-pods
sidebar:
  order: 6
---
> **Complexity**: `[MEDIUM]` - Core resource concept
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: Modules 1.1-1.4

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** what a Pod is and why it is the smallest deployable unit in Kubernetes
2. **Identify** when to use single-container vs. multi-container Pod patterns (sidecar, init)
3. **Compare** Pod lifecycle phases and understand what each status indicates
4. **Evaluate** whether a given scenario requires a standalone Pod or a higher-level workload resource

---

## Why This Module Matters

The Pod is the **most fundamental concept** in Kubernetes. Every workload runs in a Pod. KCNA will test your understanding of what Pods are, what they contain, and how they work.

---

## What is a Pod?

A **Pod** is the smallest deployable unit in Kubernetes:

```
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

---

## Pods vs Containers

```
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

---

## Single-Container Pods

Most Pods have just one container:

```
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

---

## Multi-Container Pods

Sometimes you need multiple containers in one Pod:

```
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

---

## Pod Networking

```
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

---

## Pod Lifecycle

```
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

---

## Pod Specification (Conceptual)

You don't need to memorize YAML for KCNA, but understand what a Pod contains:

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

**Key parts to understand**:
- **metadata**: Name and labels
- **spec.containers**: The containers to run
- **spec.volumes**: Shared storage

---

## Pod vs Deployment

```
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

---

## Did You Know?

- **Pods are ephemeral** - They're designed to be disposable. When a Pod dies, it's gone forever (even with the same name, it's a new Pod).

- **The pause container** - Every Pod has a hidden "pause" container that holds network namespaces. Application containers join its namespace.

- **Pod IP is internal** - Pod IPs are only routable within the cluster. You can't reach them from outside without a Service.

- **Pods have unique names** - In a namespace, Pod names must be unique. Deployments add random suffixes (e.g., nginx-7b8d6c-xk4dz).

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| "Pod = Container" | Missing Pod abstraction | Pod contains container(s) |
| "Pods have multiple IPs" | Misunderstanding networking | One IP per Pod, shared by containers |
| "Create Pods directly" | No resilience | Use Deployments instead |
| "Pods persist after deletion" | Treating as VMs | Pods are ephemeral |

---

## Quiz

1. **What is the smallest deployable unit in Kubernetes?**
   <details>
   <summary>Answer</summary>
   The Pod. Not the container—Kubernetes schedules and manages Pods, not containers directly.
   </details>

2. **How many IP addresses does a Pod get?**
   <details>
   <summary>Answer</summary>
   One. All containers in a Pod share the same IP address and can communicate via localhost.
   </details>

3. **What do containers in the same Pod share?**
   <details>
   <summary>Answer</summary>
   Network namespace (same IP, can use localhost), storage volumes, and IPC namespace. They do NOT share filesystem unless via volumes.
   </details>

4. **What is the sidecar pattern?**
   <details>
   <summary>Answer</summary>
   A multi-container Pod pattern where a helper container runs alongside the main application container to provide supporting functionality (logging, monitoring, proxying).
   </details>

5. **Why shouldn't you create Pods directly?**
   <details>
   <summary>Answer</summary>
   Pods are ephemeral—if they die, they're gone. Deployments manage Pods and ensure the desired number always exist, providing resilience, scaling, and rolling updates.
   </details>

---

## Summary

**Pods are**:
- The smallest deployable unit
- One or more containers
- Shared network (same IP)
- Shared storage (volumes)

**Key characteristics**:
- Each Pod has unique IP
- Containers communicate via localhost
- Pods are ephemeral (not persistent)
- Usually managed by Deployments

**Multi-container patterns**:
- Sidecar (helper alongside main)
- Ambassador (proxy for outbound)
- Adapter (format conversion)

---

## Next Module

[Module 1.6: Workload Resources](../module-1.6-workload-resources/) - Deployments, ReplicaSets, and other controllers that manage Pods.
