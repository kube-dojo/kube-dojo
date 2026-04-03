---
title: "Module 3.2: CNCF Ecosystem"
slug: k8s/kcna/part3-cloud-native-architecture/module-3.2-cncf-ecosystem
sidebar:
  order: 3
---
> **Complexity**: `[QUICK]` - Knowledge-based
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: Module 3.1 (Cloud Native Principles)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** the CNCF's role in governing cloud native projects and Kubernetes
2. **Compare** project maturity levels: sandbox, incubating, and graduated
3. **Identify** key CNCF projects by category (monitoring, networking, storage, security)
4. **Evaluate** the CNCF landscape to find tools that solve specific infrastructure problems

---

## Why This Module Matters

The **Cloud Native Computing Foundation (CNCF)** is the home of Kubernetes and hundreds of other cloud native projects. KCNA tests your knowledge of the CNCF, its projects, and how they fit together. Understanding this ecosystem is essential.

---

## What is the CNCF?

```
┌─────────────────────────────────────────────────────────────┐
│              CLOUD NATIVE COMPUTING FOUNDATION              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Part of the Linux Foundation                              │
│                                                             │
│  Mission:                                                  │
│  "Make cloud native computing ubiquitous"                 │
│                                                             │
│  What CNCF does:                                           │
│  ─────────────────────────────────────────────────────────  │
│  • Hosts open source projects                              │
│  • Provides governance and support                         │
│  • Certifies Kubernetes distributions                      │
│  • Runs KubeCon conferences                               │
│  • Creates training and certifications (like KCNA!)       │
│  • Maintains the Cloud Native Landscape                   │
│                                                             │
│  Founded: 2015                                             │
│  First project: Kubernetes (donated by Google)            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Maturity Levels

CNCF projects have three maturity levels:

```
┌─────────────────────────────────────────────────────────────┐
│              CNCF PROJECT MATURITY                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    GRADUATED                                │
│                        │                                    │
│                        │ Production ready                  │
│                        │ Proven adoption                   │
│                        │ Strong governance                 │
│                        │                                    │
│                   INCUBATING                               │
│                        │                                    │
│                        │ Growing adoption                  │
│                        │ Healthy community                 │
│                        │ Technical due diligence passed   │
│                        │                                    │
│                    SANDBOX                                 │
│                        │                                    │
│                        │ Early stage                       │
│                        │ Experimental                      │
│                        │ Promising technology             │
│                                                             │
│  Journey: Sandbox → Incubating → Graduated                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Graduated Projects

These are production-ready projects you should know:

```
┌─────────────────────────────────────────────────────────────┐
│              GRADUATED PROJECTS                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  KUBERNETES                                                │
│  Container orchestration platform                          │
│  The foundation of cloud native                            │
│                                                             │
│  PROMETHEUS                                                │
│  Monitoring and alerting                                   │
│  Time-series database for metrics                         │
│                                                             │
│  ENVOY                                                     │
│  Service proxy / data plane                               │
│  Used by service meshes (Istio)                           │
│                                                             │
│  CONTAINERD                                                │
│  Container runtime                                         │
│  Default runtime for Kubernetes                           │
│                                                             │
│  HELM                                                      │
│  Package manager for Kubernetes                           │
│  Charts for installing applications                       │
│                                                             │
│  ETCD                                                      │
│  Distributed key-value store                              │
│  Kubernetes uses it for state                             │
│                                                             │
│  FLUENTD                                                   │
│  Log collection and forwarding                            │
│  Unified logging layer                                     │
│                                                             │
│  HARBOR                                                    │
│  Container registry                                        │
│  With security scanning                                   │
│                                                             │
│  And many more...                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Project Categories

| Category | Examples |
|----------|----------|
| **Container Runtime** | containerd, CRI-O |
| **Orchestration** | Kubernetes |
| **Service Mesh** | Istio, Linkerd |
| **Observability** | Prometheus, Jaeger, Fluentd |
| **Storage** | Rook, Longhorn |
| **Networking** | Cilium, Calico, CoreDNS |
| **Security** | Falco, OPA, SPIFFE |
| **CI/CD** | Argo, Flux, Tekton |
| **Package Management** | Helm |

---

## The CNCF Landscape

```
┌─────────────────────────────────────────────────────────────┐
│              CNCF LANDSCAPE                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  landscape.cncf.io                                         │
│                                                             │
│  What it is:                                               │
│  • Interactive map of cloud native technologies           │
│  • Includes CNCF projects AND commercial products         │
│  • Organized by category                                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │   │
│  │  │Provision│ │ Runtime │ │ Orchestr│ │ App Def │  │   │
│  │  │ ing     │ │         │ │ ation   │ │         │  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘  │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │   │
│  │  │Platform │ │Observab │ │Serverles│ │ Special │  │   │
│  │  │         │ │ility    │ │ s       │ │         │  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  1000+ projects and products!                             │
│                                                             │
│  Use it to:                                               │
│  • Discover tools for specific needs                      │
│  • Compare alternatives                                    │
│  • See what's popular/mature                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Projects to Know for KCNA

### Observability Stack

```
┌─────────────────────────────────────────────────────────────┐
│              OBSERVABILITY                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PROMETHEUS (Graduated)                                    │
│  ─────────────────────────────────────────────────────────  │
│  • Metrics collection and storage                         │
│  • Pull-based model                                        │
│  • PromQL query language                                  │
│  • AlertManager for alerting                              │
│                                                             │
│  GRAFANA (Not CNCF, but commonly paired)                  │
│  ─────────────────────────────────────────────────────────  │
│  • Dashboards and visualization                           │
│  • Works with Prometheus                                  │
│                                                             │
│  JAEGER (Graduated)                                        │
│  ─────────────────────────────────────────────────────────  │
│  • Distributed tracing                                     │
│  • Track requests across services                         │
│                                                             │
│  FLUENTD (Graduated)                                       │
│  ─────────────────────────────────────────────────────────  │
│  • Log collection                                          │
│  • Routes logs to storage                                 │
│                                                             │
│  OPENTELEMETRY (Incubating)                               │
│  ─────────────────────────────────────────────────────────  │
│  • Unified observability framework                        │
│  • Traces, metrics, logs                                  │
│  • Vendor-neutral                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Networking & Service Mesh

```
┌─────────────────────────────────────────────────────────────┐
│              NETWORKING                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ENVOY (Graduated)                                         │
│  ─────────────────────────────────────────────────────────  │
│  • L7 proxy                                               │
│  • Data plane for service meshes                          │
│  • Dynamic configuration via API                          │
│                                                             │
│  ISTIO (Not CNCF - but very popular)                      │
│  ─────────────────────────────────────────────────────────  │
│  • Service mesh                                           │
│  • Uses Envoy                                             │
│  • Traffic management, security, observability           │
│                                                             │
│  LINKERD (Graduated)                                       │
│  ─────────────────────────────────────────────────────────  │
│  • Service mesh                                           │
│  • Lightweight, focused on simplicity                     │
│                                                             │
│  CILIUM (Graduated)                                        │
│  ─────────────────────────────────────────────────────────  │
│  • eBPF-based networking                                  │
│  • CNI plugin                                             │
│  • Network policies, observability                        │
│                                                             │
│  COREDNS (Graduated)                                       │
│  ─────────────────────────────────────────────────────────  │
│  • DNS server for Kubernetes                              │
│  • Default DNS in Kubernetes                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Security

```
┌─────────────────────────────────────────────────────────────┐
│              SECURITY                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  FALCO (Graduated)                                         │
│  ─────────────────────────────────────────────────────────  │
│  • Runtime security                                        │
│  • Detects abnormal behavior                              │
│  • Uses syscall monitoring                                │
│                                                             │
│  OPA - OPEN POLICY AGENT (Graduated)                      │
│  ─────────────────────────────────────────────────────────  │
│  • Policy as code                                         │
│  • Admission control                                       │
│  • General-purpose policy engine                          │
│                                                             │
│  SPIFFE/SPIRE (Graduated)                                 │
│  ─────────────────────────────────────────────────────────  │
│  • Service identity                                        │
│  • Workload authentication                                │
│  • Zero-trust security                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## CNCF Certifications

```
┌─────────────────────────────────────────────────────────────┐
│              CNCF CERTIFICATIONS                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Kubernetes Certifications:                                │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  KCNA - Kubernetes and Cloud Native Associate             │
│  • Entry-level, multiple choice                           │
│  • Foundational knowledge                                 │
│  • THIS exam!                                             │
│                                                             │
│  KCSA - Kubernetes and Cloud Native Security Associate    │
│  • Security fundamentals                                   │
│  • Multiple choice                                        │
│                                                             │
│  CKA - Certified Kubernetes Administrator                 │
│  • Hands-on, performance-based                            │
│  • Cluster administration                                 │
│                                                             │
│  CKAD - Certified Kubernetes Application Developer        │
│  • Hands-on, performance-based                            │
│  • Application deployment                                 │
│                                                             │
│  CKS - Certified Kubernetes Security Specialist           │
│  • Hands-on, performance-based                            │
│  • Security hardening                                     │
│  • Requires CKA first                                     │
│                                                             │
│  Path: KCNA → CKA/CKAD → CKS                             │
│  All five = Kubestronaut!                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Kubernetes was first** - Kubernetes was Google's first major open source donation to CNCF in 2015.

- **TOC decides graduation** - The Technical Oversight Committee (TOC) votes on which projects graduate based on adoption and technical criteria.

- **KubeCon is massive** - KubeCon + CloudNativeCon is one of the largest open source conferences, with 10,000+ attendees.

- **Landscape is huge** - The CNCF landscape has 1000+ projects and products. It can be overwhelming—focus on graduated/incubating projects first.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Thinking all landscape tools are CNCF | Landscape includes non-CNCF tools | Check project affiliation |
| Ignoring maturity levels | May use experimental projects in prod | Prefer graduated for production |
| Confusing similar projects | Using wrong tool for the job | Understand project purposes |
| Memorizing all projects | There are too many | Focus on graduated ones |

---

## Quiz

1. **What are the three CNCF project maturity levels?**
   <details>
   <summary>Answer</summary>
   Sandbox (early stage), Incubating (growing adoption), and Graduated (production ready). Projects progress through these levels based on adoption and technical criteria.
   </details>

2. **What is Prometheus used for?**
   <details>
   <summary>Answer</summary>
   Monitoring and alerting. It collects and stores metrics as time-series data, provides PromQL for querying, and AlertManager for alerting. It's a graduated CNCF project.
   </details>

3. **What is Envoy?**
   <details>
   <summary>Answer</summary>
   A graduated CNCF project that provides L7 proxy functionality. It's the data plane for service meshes like Istio. It handles traffic routing, load balancing, and observability at the network edge.
   </details>

4. **What is the CNCF Landscape?**
   <details>
   <summary>Answer</summary>
   An interactive map at landscape.cncf.io showing cloud native technologies. It includes CNCF projects and commercial products, organized by category. It helps discover and compare tools.
   </details>

5. **What five certifications make a Kubestronaut?**
   <details>
   <summary>Answer</summary>
   KCNA (Associate), KCSA (Security Associate), CKA (Administrator), CKAD (Application Developer), and CKS (Security Specialist). All five must be earned and maintained.
   </details>

---

## Summary

**CNCF**:
- Cloud Native Computing Foundation
- Part of Linux Foundation
- Hosts Kubernetes and 100+ projects

**Project maturity**:
- Sandbox → Incubating → Graduated
- Graduated = production ready

**Key projects by category**:
- **Orchestration**: Kubernetes
- **Runtime**: containerd
- **Observability**: Prometheus, Jaeger, Fluentd
- **Networking**: Envoy, CoreDNS, Cilium
- **Security**: Falco, OPA
- **Package management**: Helm

**Certifications**:
- KCNA → CKA/CKAD → CKS
- All five = Kubestronaut

---

## Next Module

[Module 3.3: Cloud Native Patterns](../module-3.3-patterns/) - Service mesh, serverless, and other cloud native architectural patterns.
