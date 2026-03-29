---
title: "Module 3.3: Cloud Native Patterns"
slug: k8s/kcna/part3-cloud-native-architecture/module-3.3-patterns
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]` - Architecture concepts
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: Module 3.2 (CNCF Ecosystem)

---

## Why This Module Matters

Beyond basic concepts, cloud native includes patterns for solving complex problems—service mesh for microservice communication, serverless for event-driven workloads, GitOps for deployment automation. KCNA tests your understanding of these architectural patterns.

---

## Service Mesh

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICE MESH                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Problem: Microservices need:                              │
│  • Service-to-service communication                        │
│  • Load balancing                                          │
│  • Security (mTLS)                                         │
│  • Observability (traces, metrics)                         │
│  • Traffic management (canary, retries)                   │
│                                                             │
│  Without service mesh:                                     │
│  ─────────────────────────────────────────────────────────  │
│  Each service implements this itself = duplication        │
│                                                             │
│  With service mesh:                                        │
│  ─────────────────────────────────────────────────────────  │
│  Infrastructure layer handles it transparently            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                CONTROL PLANE                        │   │
│  │  (Istio/Linkerd control plane)                     │   │
│  │  Configuration, certificates, policies             │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│                         │ configures                       │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                DATA PLANE                           │   │
│  │                                                      │   │
│  │  ┌───────────────┐      ┌───────────────┐          │   │
│  │  │ Service A     │      │ Service B     │          │   │
│  │  │ ┌───────────┐ │      │ ┌───────────┐ │          │   │
│  │  │ │   App     │ │      │ │   App     │ │          │   │
│  │  │ └───────────┘ │      │ └───────────┘ │          │   │
│  │  │ ┌───────────┐ │      │ ┌───────────┐ │          │   │
│  │  │ │  Sidecar  │ │←────→│ │  Sidecar  │ │          │   │
│  │  │ │  (Envoy)  │ │      │ │  (Envoy)  │ │          │   │
│  │  │ └───────────┘ │      │ └───────────┘ │          │   │
│  │  └───────────────┘      └───────────────┘          │   │
│  │                                                      │   │
│  │  All traffic goes through sidecars                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Service Mesh Benefits

| Feature | Description |
|---------|-------------|
| **mTLS** | Automatic encryption between services |
| **Traffic management** | Canary releases, A/B testing |
| **Retries/Timeouts** | Automatic retry with backoff |
| **Circuit breaking** | Fail fast when service is down |
| **Observability** | Automatic metrics, traces, logs |
| **Access control** | Service-to-service authorization |

### Popular Service Meshes

| Mesh | Key Characteristics |
|------|---------------------|
| **Istio** | Feature-rich, uses Envoy, complex |
| **Linkerd** | Lightweight, simple, CNCF graduated |
| **Cilium** | eBPF-based, no sidecars needed |

---

## Serverless / FaaS

```
┌─────────────────────────────────────────────────────────────┐
│              SERVERLESS                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What is serverless?                                       │
│  ─────────────────────────────────────────────────────────  │
│  • Run code without managing servers                       │
│  • Pay only when code runs                                 │
│  • Automatic scaling (including to zero)                  │
│                                                             │
│  Types:                                                    │
│                                                             │
│  FaaS (Function as a Service):                            │
│  ─────────────────────────────────────────────────────────  │
│  Event → Function executes → Result                       │
│                                                             │
│  ┌─────────┐     ┌─────────────┐     ┌─────────┐          │
│  │  Event  │ ──→ │  Function   │ ──→ │ Result  │          │
│  │(HTTP,   │     │(Your code)  │     │         │          │
│  │ Queue,  │     │             │     │         │          │
│  │ Timer)  │     └─────────────┘     └─────────┘          │
│  └─────────┘                                               │
│                                                             │
│  Example: Process uploaded image                          │
│  1. Image uploaded to S3 (event)                          │
│  2. Function triggered                                     │
│  3. Function resizes image                                │
│  4. Function saves result                                 │
│                                                             │
│  Kubernetes Serverless:                                   │
│  ─────────────────────────────────────────────────────────  │
│  • Knative: Serverless on Kubernetes                      │
│  • OpenFaaS: Functions on Kubernetes                      │
│  • KEDA: Event-driven autoscaling                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Serverless Characteristics

| Aspect | Description |
|--------|-------------|
| **No server management** | Platform handles infrastructure |
| **Auto-scaling** | Scales up with load, down to zero |
| **Event-driven** | Triggered by events |
| **Pay-per-use** | Billed per execution |
| **Stateless** | Functions don't maintain state |
| **Short-lived** | Functions have time limits |

---

## GitOps

```
┌─────────────────────────────────────────────────────────────┐
│              GITOPS                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Git = Single source of truth                             │
│                                                             │
│  Traditional CI/CD:                                        │
│  ─────────────────────────────────────────────────────────  │
│  Git → CI → Build → Push to cluster                       │
│                                                             │
│  GitOps:                                                   │
│  ─────────────────────────────────────────────────────────  │
│  Git ← Pull ← Agent in cluster                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │  ┌──────────┐                    ┌──────────────┐   │   │
│  │  │   Git    │                    │  Kubernetes  │   │   │
│  │  │   Repo   │←─── Agent pulls ───│   Cluster    │   │   │
│  │  │(desired) │                    │  (actual)    │   │   │
│  │  └──────────┘                    └──────────────┘   │   │
│  │       │                                │             │   │
│  │       │                                │             │   │
│  │       └──── Agent reconciles ──────────┘             │   │
│  │             (makes actual = desired)                │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  GitOps tools:                                             │
│  • Argo CD (CNCF Graduated)                               │
│  • Flux (CNCF Graduated)                                  │
│                                                             │
│  Benefits:                                                 │
│  • Declarative (Git stores desired state)                │
│  • Auditable (Git history = change log)                  │
│  • Reversible (git revert = rollback)                    │
│  • Secure (cluster pulls, no push credentials needed)    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### GitOps Principles

| Principle | Description |
|-----------|-------------|
| **Declarative** | Desired state in Git |
| **Versioned** | Git provides history |
| **Automated** | Changes auto-applied |
| **Audited** | Git log = audit trail |

---

## Autoscaling Patterns

```
┌─────────────────────────────────────────────────────────────┐
│              AUTOSCALING PATTERNS                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  HORIZONTAL POD AUTOSCALER (HPA)                          │
│  ─────────────────────────────────────────────────────────  │
│  Scale based on metrics (CPU, memory, custom)             │
│  [Pod][Pod] → [Pod][Pod][Pod][Pod]                       │
│                                                             │
│  VERTICAL POD AUTOSCALER (VPA)                            │
│  ─────────────────────────────────────────────────────────  │
│  Adjust resource requests/limits                          │
│  [100m CPU] → [500m CPU]                                 │
│                                                             │
│  CLUSTER AUTOSCALER                                       │
│  ─────────────────────────────────────────────────────────  │
│  Add/remove nodes based on pending pods                   │
│  [Node 1][Node 2] → [Node 1][Node 2][Node 3]            │
│                                                             │
│  KEDA (Kubernetes Event-Driven Autoscaler)                │
│  ─────────────────────────────────────────────────────────  │
│  Scale on external events                                 │
│  • Queue messages                                         │
│  • Database connections                                   │
│  • Custom metrics                                         │
│  • Scale to zero!                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Operators and CRDs

```
┌─────────────────────────────────────────────────────────────┐
│              OPERATORS                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What is an Operator?                                      │
│  ─────────────────────────────────────────────────────────  │
│  Software that extends Kubernetes to manage complex apps  │
│  "Human operator knowledge, codified"                     │
│                                                             │
│  How it works:                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  1. Custom Resource Definition (CRD):                     │
│     Defines new resource type                             │
│     kind: PostgresCluster                                 │
│                                                             │
│  2. Custom Resource (CR):                                 │
│     Instance of the CRD                                   │
│     "I want a 3-node Postgres cluster"                   │
│                                                             │
│  3. Operator (Controller):                                │
│     Watches CRs, takes action                             │
│     Creates Pods, Services, PVCs as needed               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │  You write:              Operator creates:          │   │
│  │  ──────────────          ─────────────────          │   │
│  │  kind: PostgresCluster   • StatefulSet              │   │
│  │  spec:                   • Service                  │   │
│  │    replicas: 3           • PVCs                     │   │
│  │    version: 14           • ConfigMaps               │   │
│  │                          • Secrets                  │   │
│  │                          • Handles backups          │   │
│  │                          • Handles failover         │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Popular Operators:                                        │
│  • Prometheus Operator                                    │
│  • cert-manager                                           │
│  • Strimzi (Kafka)                                        │
│  • PostgreSQL Operators                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Multi-Tenancy Patterns

```
┌─────────────────────────────────────────────────────────────┐
│              MULTI-TENANCY                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Running multiple tenants on same cluster                 │
│                                                             │
│  NAMESPACE-BASED:                                          │
│  ─────────────────────────────────────────────────────────  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Cluster                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │ NS: team-a  │  │ NS: team-b  │  │ NS: team-c  │ │   │
│  │  │ [Pods]      │  │ [Pods]      │  │ [Pods]      │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Isolation via:                                            │
│  • RBAC (who can access what)                             │
│  • ResourceQuotas (limit resources per namespace)         │
│  • NetworkPolicies (network isolation)                    │
│  • LimitRanges (default resource limits)                 │
│                                                             │
│  CLUSTER-PER-TENANT:                                       │
│  ─────────────────────────────────────────────────────────  │
│  Strongest isolation, higher cost                         │
│                                                             │
│  VIRTUAL CLUSTERS:                                         │
│  ─────────────────────────────────────────────────────────  │
│  Tools like vCluster create isolated "virtual" clusters   │
│  Stronger isolation than namespaces, less than clusters  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Sidecars are going away** - Service meshes like Cilium use eBPF to avoid sidecar containers. Istio now supports "ambient mesh" without sidecars.

- **GitOps coined by Weaveworks** - The term and practice were popularized by Weaveworks, creators of Flux.

- **Operators have a maturity model** - From basic install (Level 1) to auto-pilot (Level 5), measuring automation capability.

- **KEDA is CNCF Graduated** - Kubernetes Event-Driven Autoscaler became a graduated project, showing the importance of event-driven patterns.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Service mesh for simple apps | Adds unnecessary complexity | Use when microservice complexity justifies it |
| Confusing serverless and containers | Different models | Serverless = event-triggered, auto-scale to zero |
| Push-based CD as GitOps | Not true GitOps | GitOps = cluster pulls from Git |
| Operators for simple apps | Over-engineering | Use Operators for complex stateful apps |

---

## Quiz

1. **What is a service mesh?**
   <details>
   <summary>Answer</summary>
   An infrastructure layer that handles service-to-service communication. It provides mTLS, traffic management, observability, and retries transparently via sidecar proxies or eBPF, without changing application code.
   </details>

2. **What is the difference between control plane and data plane in a service mesh?**
   <details>
   <summary>Answer</summary>
   The control plane manages configuration, certificates, and policies. The data plane consists of proxies (sidecars like Envoy) that handle actual network traffic between services.
   </details>

3. **What makes GitOps different from regular CI/CD?**
   <details>
   <summary>Answer</summary>
   In GitOps, an agent in the cluster pulls desired state from Git and reconciles it. Git is the source of truth. Traditional CI/CD pushes changes to the cluster from outside.
   </details>

4. **What is an Operator in Kubernetes?**
   <details>
   <summary>Answer</summary>
   Software that extends Kubernetes to manage complex applications. It uses Custom Resource Definitions (CRDs) to define new resource types and controllers that automate operational tasks like backups, scaling, and failover.
   </details>

5. **What is KEDA used for?**
   <details>
   <summary>Answer</summary>
   Kubernetes Event-Driven Autoscaler. It scales workloads based on external events like queue length, database metrics, or custom sources. It can scale to zero, unlike standard HPA.
   </details>

---

## Summary

**Service Mesh**:
- Handles service-to-service communication
- mTLS, traffic management, observability
- Control plane + data plane (sidecars)
- Examples: Istio, Linkerd, Cilium

**Serverless**:
- Run code without managing servers
- Event-driven, scale to zero
- Pay per execution
- Kubernetes: Knative, OpenFaaS, KEDA

**GitOps**:
- Git = source of truth
- Agent pulls and reconciles
- Auditable, reversible
- Tools: Argo CD, Flux

**Operators**:
- Extend Kubernetes with CRDs
- Automate complex app management
- Codify operational knowledge

---

## Next Module

[Module 3.4: Observability Fundamentals](../module-3.4-observability-fundamentals/) - Understanding the three pillars of observability: metrics, logs, and traces.
