---
title: "Module 1.7: Services"
slug: k8s/kcna/part1-kubernetes-fundamentals/module-1.7-services
sidebar:
  order: 8
---
> **Complexity**: `[MEDIUM]` - Core networking concept
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: Modules 1.5, 1.6

---

## Why This Module Matters

Pods come and go—their IPs change constantly. **Services** provide stable endpoints to access Pods. Understanding Services is critical for KCNA and for understanding how Kubernetes networking works.

---

## The Problem Services Solve

```
┌─────────────────────────────────────────────────────────────┐
│              THE PROBLEM WITH POD IPs                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Without Services:                                         │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Time T1:                                                  │
│  Frontend → 10.1.1.5 (backend pod)  ✓ Works               │
│                                                             │
│  Time T2: Backend pod dies, new one created                │
│  Frontend → 10.1.1.5  ✗ Dead                              │
│  New backend pod has IP: 10.1.1.9                          │
│                                                             │
│  Problem:                                                  │
│  • Pod IPs are ephemeral                                   │
│  • Clients can't track changing IPs                        │
│  • No load balancing across replicas                       │
│                                                             │
│  With Services:                                            │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Frontend → backend-service (stable) → Backend pods       │
│                                                             │
│  Service provides:                                         │
│  • Stable IP and DNS name                                  │
│  • Automatic discovery of healthy Pods                    │
│  • Load balancing                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## What is a Service?

A **Service** is an abstraction that defines a logical set of Pods and a policy to access them:

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICE CONCEPT                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                                                       │ │
│  │    Client                                             │ │
│  │       │                                               │ │
│  │       │ Request to my-service:80                      │ │
│  │       ▼                                               │ │
│  │  ┌──────────────────────────────────────────┐        │ │
│  │  │            SERVICE                        │        │ │
│  │  │  Name: my-service                        │        │ │
│  │  │  IP: 10.96.45.23 (stable ClusterIP)     │        │ │
│  │  │  Port: 80                                │        │ │
│  │  │  Selector: app=backend                   │        │ │
│  │  └──────────────────────────────────────────┘        │ │
│  │       │                                               │ │
│  │       │ Load balanced to matching Pods               │ │
│  │       ▼                                               │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐              │ │
│  │  │  Pod    │  │  Pod    │  │  Pod    │              │ │
│  │  │app=back │  │app=back │  │app=back │              │ │
│  │  │10.1.1.5 │  │10.1.1.6 │  │10.1.1.7 │              │ │
│  │  └─────────┘  └─────────┘  └─────────┘              │ │
│  │                                                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Service uses LABELS to find Pods                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Service Types

### 1. ClusterIP (Default)

```
┌─────────────────────────────────────────────────────────────┐
│              CLUSTERIP SERVICE                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  • Internal cluster IP only                                │
│  • Not accessible from outside cluster                     │
│  • Default type                                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   CLUSTER                            │   │
│  │                                                      │   │
│  │   Frontend Pod ──→ backend-svc ──→ Backend Pods    │   │
│  │                    (ClusterIP)                      │   │
│  │                    10.96.0.50                       │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  External: ✗ Cannot reach 10.96.0.50                      │
│                                                             │
│  Use case: Internal services (databases, caches, APIs)    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. NodePort

```
┌─────────────────────────────────────────────────────────────┐
│              NODEPORT SERVICE                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  • Exposes Service on each node's IP at a static port      │
│  • Port range: 30000-32767                                 │
│  • Accessible from outside cluster                         │
│                                                             │
│  External: http://node-ip:30080                           │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Node 1 (:30080)  Node 2 (:30080)  Node 3 (:30080) │   │
│  │       │               │               │             │   │
│  │       └───────────────┼───────────────┘             │   │
│  │                       │                              │   │
│  │                       ▼                              │   │
│  │              ┌─────────────┐                        │   │
│  │              │   Service   │                        │   │
│  │              │  NodePort   │                        │   │
│  │              └─────────────┘                        │   │
│  │                       │                              │   │
│  │              ┌────────┼────────┐                    │   │
│  │              ▼        ▼        ▼                    │   │
│  │            Pod      Pod      Pod                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Use case: Development, testing, simple external access   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. LoadBalancer

```
┌─────────────────────────────────────────────────────────────┐
│              LOADBALANCER SERVICE                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  • Provisions external load balancer (cloud provider)      │
│  • Gets external IP address                                │
│  • Most common for production external access              │
│                                                             │
│  External: http://203.0.113.50                            │
│       │                                                     │
│       ▼                                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Cloud Load Balancer (ELB, GLB, etc.)         │  │
│  │                 203.0.113.50                          │  │
│  └──────────────────────────────────────────────────────┘  │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Node 1          Node 2          Node 3             │   │
│  │    │               │               │                │   │
│  │    ▼               ▼               ▼                │   │
│  │  Pod             Pod             Pod                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Use case: Production external access in cloud            │
│  Note: Costs money in cloud environments!                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. ExternalName

```
┌─────────────────────────────────────────────────────────────┐
│              EXTERNALNAME SERVICE                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  • Maps Service to external DNS name                       │
│  • No proxying—returns CNAME record                       │
│  • No selector (no Pods)                                   │
│                                                             │
│  Pod → my-database → database.example.com                 │
│                                                             │
│  Use case: Accessing external services with internal name │
│  Example: External database, SaaS services                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Service Type Comparison

| Type | Internal | External | Use Case |
|------|----------|----------|----------|
| **ClusterIP** | ✓ | ✗ | Internal communication |
| **NodePort** | ✓ | ✓ (via node IP) | Development/testing |
| **LoadBalancer** | ✓ | ✓ (via LB IP) | Production external |
| **ExternalName** | ✓ | N/A | External DNS mapping |

---

## Service Discovery

Kubernetes provides two ways to discover Services:

### 1. DNS (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│              DNS-BASED DISCOVERY                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Every Service gets a DNS entry:                           │
│                                                             │
│  <service-name>.<namespace>.svc.cluster.local              │
│                                                             │
│  Examples:                                                 │
│  ─────────────────────────────────────────────────────────  │
│  backend.default.svc.cluster.local                        │
│  database.production.svc.cluster.local                    │
│  redis.cache.svc.cluster.local                            │
│                                                             │
│  Shortcuts (within same namespace):                        │
│  ─────────────────────────────────────────────────────────  │
│  backend                    (same namespace)               │
│  backend.default            (namespace specified)          │
│  backend.default.svc        (svc added)                   │
│                                                             │
│  Pod can just use: http://backend:80                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Environment Variables

```
┌─────────────────────────────────────────────────────────────┐
│              ENVIRONMENT VARIABLE DISCOVERY                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Kubernetes injects environment variables into Pods:       │
│                                                             │
│  For Service "backend" on port 80:                        │
│  ─────────────────────────────────────────────────────────  │
│  BACKEND_SERVICE_HOST=10.96.45.23                         │
│  BACKEND_SERVICE_PORT=80                                   │
│  BACKEND_PORT=tcp://10.96.45.23:80                        │
│                                                             │
│  Limitation:                                               │
│  Service must exist BEFORE Pod is created                 │
│  (DNS doesn't have this limitation)                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Endpoints

Services use **Endpoints** to track Pod IPs:

```
┌─────────────────────────────────────────────────────────────┐
│              ENDPOINTS                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Service: backend                                          │
│  Selector: app=backend                                     │
│                                                             │
│       │                                                     │
│       │ Kubernetes finds matching Pods                     │
│       ▼                                                     │
│                                                             │
│  Endpoints: backend                                        │
│  Addresses:                                                │
│    - 10.1.1.5:8080                                        │
│    - 10.1.1.6:8080                                        │
│    - 10.1.1.7:8080                                        │
│                                                             │
│  When Pods change, Endpoints update automatically         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **ClusterIP is virtual** - The ClusterIP doesn't actually exist on any interface. It's handled by kube-proxy rules that redirect traffic.

- **LoadBalancer includes NodePort** - When you create a LoadBalancer Service, you also get a ClusterIP and NodePort automatically.

- **Headless Services** - Setting `clusterIP: None` creates a headless Service that returns Pod IPs directly via DNS (useful for StatefulSets).

- **Services are namespace-scoped** - A Service in namespace "dev" can only directly select Pods in "dev" namespace.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Using Pod IPs directly | IPs change | Use Services for stable access |
| LoadBalancer everywhere | Expensive, wasteful | Use Ingress for HTTP routing |
| Wrong selector labels | Service finds no Pods | Labels must match exactly |
| Expecting external IP for ClusterIP | Won't work | Use NodePort or LoadBalancer |

---

## Quiz

1. **What is the default Service type?**
   <details>
   <summary>Answer</summary>
   ClusterIP. It provides internal cluster access only—no external access.
   </details>

2. **How does a Service find which Pods to route to?**
   <details>
   <summary>Answer</summary>
   Using label selectors. The Service's selector matches Pod labels. Kubernetes automatically creates Endpoints listing matching Pod IPs.
   </details>

3. **What's the DNS format for a Service?**
   <details>
   <summary>Answer</summary>
   `<service>.<namespace>.svc.cluster.local`. For example, `backend.production.svc.cluster.local`.
   </details>

4. **When would you use NodePort vs LoadBalancer?**
   <details>
   <summary>Answer</summary>
   NodePort for development/testing or when you manage your own load balancer. LoadBalancer for production external access in cloud environments (it provisions a cloud load balancer).
   </details>

5. **What is a headless Service?**
   <details>
   <summary>Answer</summary>
   A Service with `clusterIP: None`. Instead of a single ClusterIP, DNS returns the IPs of all matching Pods. Used with StatefulSets for direct Pod access.
   </details>

---

## Summary

**Services provide**:
- Stable IP and DNS name
- Load balancing across Pods
- Service discovery

**Service types**:

| Type | Access | Use Case |
|------|--------|----------|
| **ClusterIP** | Internal only | Backend services |
| **NodePort** | Via node IP:port | Testing |
| **LoadBalancer** | Via cloud LB | Production external |
| **ExternalName** | DNS alias | External services |

**Discovery methods**:
- DNS: `service.namespace.svc.cluster.local` (preferred)
- Environment variables (legacy)

---

## Next Module

[Module 1.8: Namespaces and Labels](../module-1.8-namespaces-labels/) - Organizing and selecting resources in Kubernetes.
