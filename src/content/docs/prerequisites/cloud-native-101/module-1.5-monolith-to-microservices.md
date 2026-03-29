---
title: "Module 1.5: From Monolith to Microservices"
slug: prerequisites/cloud-native-101/module-1.5-monolith-to-microservices/
sidebar:
  order: 6
---
> **Complexity**: `[QUICK]` - Architectural concepts
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: Module 3 (What Is Kubernetes?)

---

## Why This Module Matters

Kubernetes is designed for distributed, containerized applications—typically microservices. Understanding the evolution from monoliths to microservices helps you:

1. Know why Kubernetes features exist
2. Make better architectural decisions
3. Understand when microservices are (and aren't) appropriate
4. Speak the language of modern software architecture

---

## The Monolith

### What Is a Monolith?

A monolithic application is a single deployable unit containing all functionality:

```
┌─────────────────────────────────────────────────────────────┐
│              MONOLITHIC APPLICATION                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 MyApp.jar (or .exe)                 │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│  │  │  User   │ │ Product │ │  Order  │ │ Payment │   │   │
│  │  │ Module  │ │ Module  │ │ Module  │ │ Module  │   │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │   │
│  │       │           │           │           │         │   │
│  │       └───────────┴───────────┴───────────┘         │   │
│  │                       │                             │   │
│  │              ┌────────┴────────┐                    │   │
│  │              │    Database     │                    │   │
│  │              │   (shared)      │                    │   │
│  │              └─────────────────┘                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Deploy: One unit                                          │
│  Scale: All or nothing                                     │
│  Database: Shared by all modules                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Monolith Advantages

```
✅ Simple to develop initially
✅ Easy to test (one application)
✅ Simple deployment (one artifact)
✅ Easy to debug (one process)
✅ No network latency between components
✅ ACID transactions are straightforward
```

### Monolith Challenges (At Scale)

```
❌ Changes require full redeploy
❌ Long build/test cycles
❌ Scaling means scaling everything
❌ Technology choices affect entire app
❌ One bug can crash everything
❌ Team coordination becomes difficult
❌ Codebase becomes unwieldy
```

---

## The Microservices Approach

### What Are Microservices?

Microservices decompose an application into small, independent services:

```
┌─────────────────────────────────────────────────────────────┐
│              MICROSERVICES ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐            │
│  │   User    │   │  Product  │   │   Order   │            │
│  │  Service  │   │  Service  │   │  Service  │            │
│  │  ┌─────┐  │   │  ┌─────┐  │   │  ┌─────┐  │            │
│  │  │ DB  │  │   │  │ DB  │  │   │  │ DB  │  │            │
│  │  └─────┘  │   │  └─────┘  │   │  └─────┘  │            │
│  └─────┬─────┘   └─────┬─────┘   └─────┬─────┘            │
│        │               │               │                    │
│        └───────────────┼───────────────┘                    │
│                        │                                    │
│                ┌───────┴───────┐                           │
│                │  API Gateway  │                           │
│                └───────────────┘                           │
│                        │                                    │
│                    Clients                                  │
│                                                             │
│  Deploy: Each service independently                        │
│  Scale: Per service based on need                          │
│  Database: Each service owns its data                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Microservices Advantages

```
✅ Independent deployment
✅ Scale individual services
✅ Technology diversity (right tool for job)
✅ Fault isolation (one service down ≠ all down)
✅ Team autonomy
✅ Smaller, focused codebases
```

### Microservices Challenges

```
❌ Network complexity
❌ Distributed system failures
❌ Data consistency challenges
❌ Testing is harder
❌ Operational complexity
❌ Debugging across services
❌ Need for robust infrastructure
```

---

## When to Choose What

### Monolith is Often Better When:

```
✅ Small team (< 10 developers)
✅ New product/startup phase
✅ Simple domain
✅ Tight deadlines
✅ Unknown requirements
✅ Single deployment target
```

### Microservices Make Sense When:

```
✅ Large, multiple teams
✅ Need independent scaling
✅ Different technology requirements per component
✅ High availability requirements
✅ Frequent releases needed
✅ Clear domain boundaries
```

### The Reality

```
┌─────────────────────────────────────────────────────────────┐
│              THE TYPICAL JOURNEY                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Stage 1: Start with Monolith                              │
│  ├── Fast development                                      │
│  ├── Simple operations                                     │
│  └── Learn the domain                                      │
│                                                             │
│  Stage 2: Grow (Still Monolith)                            │
│  ├── Team grows                                            │
│  ├── Features accumulate                                   │
│  └── Pain points emerge                                    │
│                                                             │
│  Stage 3: Strategic Decomposition                          │
│  ├── Extract services where it hurts                       │
│  ├── Clear boundaries                                      │
│  └── Incremental migration                                 │
│                                                             │
│  DON'T: Start with microservices for a new product        │
│  DON'T: Decompose without clear boundaries                │
│  DON'T: Microservices for small teams                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## How Kubernetes Enables Microservices

Kubernetes solves microservices operational challenges:

| Challenge | Kubernetes Solution |
|-----------|---------------------|
| Service discovery | Services, DNS |
| Load balancing | Services, Ingress |
| Scaling | Deployments, HPA |
| Configuration | ConfigMaps, Secrets |
| Health monitoring | Probes |
| Rolling updates | Deployments |
| Fault tolerance | ReplicaSets, self-healing |
| Resource management | Requests/Limits |

```
Without Kubernetes:
├── Manual service registration
├── Custom load balancer configuration
├── Script-based deployments
├── Hope things restart when they crash
└── Configuration files everywhere

With Kubernetes:
├── Automatic service discovery
├── Built-in load balancing
├── Declarative deployments
├── Self-healing by default
└── Centralized configuration
```

---

## Microservices Patterns

### API Gateway

```
                    ┌───────────────┐
                    │  API Gateway  │
                    └───────┬───────┘
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
      ┌─────────┐     ┌─────────┐     ┌─────────┐
      │ Service │     │ Service │     │ Service │
      │    A    │     │    B    │     │    C    │
      └─────────┘     └─────────┘     └─────────┘

Purpose:
- Single entry point
- Authentication/Authorization
- Rate limiting
- Request routing

In K8s: Ingress Controller or dedicated gateway
```

### Service Mesh

```
      ┌─────────────────────────────────────────┐
      │             Service Mesh                │
      │  ┌────────┐        ┌────────┐          │
      │  │Svc A   │◄──────►│Svc B   │          │
      │  │┌─────┐ │        │┌─────┐ │          │
      │  ││Proxy│ │        ││Proxy│ │          │
      │  │└─────┘ │        │└─────┘ │          │
      │  └────────┘        └────────┘          │
      └─────────────────────────────────────────┘

Purpose:
- Traffic management
- Security (mTLS)
- Observability

Examples: Istio, Linkerd
```

### Sidecar Pattern

```
      ┌─────────────────────────────────────────┐
      │                 Pod                     │
      │  ┌─────────────┐  ┌─────────────┐      │
      │  │   Main      │  │   Sidecar   │      │
      │  │ Application │◄►│   (Proxy)   │      │
      │  └─────────────┘  └─────────────┘      │
      └─────────────────────────────────────────┘

Purpose:
- Add functionality without changing app
- Logging, monitoring, security

K8s: Multi-container pods
```

---

## Visualization: Communication Patterns

```
┌─────────────────────────────────────────────────────────────┐
│              MICROSERVICES COMMUNICATION                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SYNCHRONOUS (Request/Response)                            │
│  ┌─────────┐  HTTP/gRPC   ┌─────────┐                     │
│  │Service A│─────────────►│Service B│                     │
│  └─────────┘◄─────────────└─────────┘                     │
│              Response                                       │
│  Use: When you need immediate response                     │
│  Risk: Tight coupling, cascading failures                  │
│                                                             │
│  ASYNCHRONOUS (Events/Messages)                            │
│  ┌─────────┐    Event    ┌─────────┐   ┌─────────┐       │
│  │Service A│────────────►│  Queue  │──►│Service B│       │
│  └─────────┘             └─────────┘   └─────────┘       │
│  Use: Decoupled systems, eventual consistency             │
│  Benefit: Loose coupling, resilience                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Amazon pioneered microservices.** Their 2002 mandate required all teams to communicate via APIs. This eventually became AWS.

- **Netflix has 1000+ microservices.** They also created many tools now in the cloud native ecosystem (Zuul, Eureka, Hystrix).

- **The "two pizza rule"** suggests teams should be small enough to feed with two pizzas. This aligns with microservice team ownership.

- **Monoliths can scale too.** Shopify handles massive traffic with a monolithic Rails app. Architecture choices depend on context.

---

## Common Misconceptions

| Misconception | Reality |
|---------------|---------|
| "Microservices are always better" | They add complexity. Often overkill for small teams/products. |
| "Monoliths don't scale" | They do! Shopify, Stack Overflow prove it. Different tradeoffs. |
| "Microservices = using Kubernetes" | You can run monoliths on K8s. K8s is infrastructure, not architecture. |
| "Each microservice needs its own database" | Common pattern but not required. Shared databases are sometimes OK. |

---

## Quiz

1. **What is the primary advantage of microservices over monoliths?**
   <details>
   <summary>Answer</summary>
   Independent deployment and scaling. Each service can be developed, deployed, and scaled independently by separate teams. This enables faster release cycles and better resource utilization.
   </details>

2. **When would a monolith be a better choice than microservices?**
   <details>
   <summary>Answer</summary>
   Small teams, new products, simple domains, unknown requirements, tight deadlines. Microservices add operational complexity that isn't justified without scale.
   </details>

3. **How does Kubernetes help with microservices?**
   <details>
   <summary>Answer</summary>
   K8s provides service discovery (DNS), load balancing, scaling, configuration management, health monitoring, rolling updates, and self-healing—all challenges that become critical with many services.
   </details>

4. **What is a service mesh?**
   <details>
   <summary>Answer</summary>
   Infrastructure layer for service-to-service communication. Handles traffic management, security (mTLS), and observability. Implemented via sidecar proxies. Examples: Istio, Linkerd.
   </details>

---

## Reflection Exercise

This module covers architectural concepts that don't have a CLI exercise. Instead, reflect on these questions:

**1. Think about applications you've used or built:**
- Were they monoliths or microservices?
- What signs indicated this? (Deployment frequency, team structure, scaling patterns)

**2. Consider a hypothetical e-commerce site:**
- What services might you extract? (Users, Products, Orders, Payments, Inventory)
- Which would need to scale independently? (Product search? Payment processing?)
- What data would each service own?

**3. Evaluate this scenario:**
> A 3-person startup is building a new product. They're considering microservices "to be modern."
- Is this a good idea? (Probably not)
- What would you recommend? (Monolith first, decompose when pain points emerge)
- Why?

**4. Research one company:**
- Look up how Netflix, Amazon, or Spotify approaches microservices
- What challenges did they face?
- Would their approach work for a smaller company?

These questions prepare you to make architectural decisions in your career, not just pass exams.

---

## Summary

**Monoliths**:
- Single deployable unit
- Simpler to develop and operate initially
- Scale everything together
- Challenges emerge with growth

**Microservices**:
- Independent services
- Scale and deploy individually
- Technology flexibility
- Operational complexity

**Key Insights**:
- Start simple (often monolith)
- Decompose when pain points emerge
- Kubernetes enables microservices patterns
- Architecture should match team and product needs

---

## Track Complete!

You've finished the **Cloud Native 101** prerequisite track. You now understand:

1. What containers are and why they matter
2. Docker fundamentals for building and running containers
3. What Kubernetes is and why it exists
4. The cloud native ecosystem landscape
5. Monolith vs microservices tradeoffs

**Next Steps**:
- [Kubernetes Basics](../kubernetes-basics/module-1.1-first-cluster/) - Hands-on with your first cluster
- [CKA Curriculum](../../k8s/cka/part0-environment/module-0.1-cluster-setup/) - Start certification prep
- [CKAD Curriculum](../../k8s/ckad/part0-environment/module-0.1-ckad-overview/) - Developer certification path
