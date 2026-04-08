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

```mermaid
flowchart TB
    subgraph CNCF [CLOUD NATIVE COMPUTING FOUNDATION]
        direction TB
        Info["<b>Part of the Linux Foundation</b><br>Mission: 'Make cloud native computing ubiquitous'"]
        
        Actions["<b>What CNCF does:</b><br>• Hosts open source projects<br>• Provides governance and support<br>• Certifies Kubernetes distributions<br>• Runs KubeCon conferences<br>• Creates training and certifications (like KCNA!)<br>• Maintains the Cloud Native Landscape"]
        
        History["<b>History:</b><br>Founded: 2015<br>First project: Kubernetes (donated by Google)"]
        
        Info ~~~ Actions ~~~ History
    end
```

---

## Project Maturity Levels

CNCF projects have three maturity levels:

```mermaid
flowchart TD
    subgraph Maturity [CNCF PROJECT MATURITY]
        direction TB
        G["<b>GRADUATED</b><br>Production ready<br>Proven adoption<br>Strong governance"]
        I["<b>INCUBATING</b><br>Growing adoption<br>Healthy community<br>Technical due diligence passed"]
        S["<b>SANDBOX</b><br>Early stage<br>Experimental<br>Promising technology"]
        
        S -->|Journey| I
        I -->|Journey| G
    end
```

---

> **Pause and predict**: CNCF has sandbox, incubating, and graduated project levels. If you were evaluating two monitoring tools -- one Graduated and one Sandbox -- for your company's production Kubernetes cluster, what does the maturity level tell you about risk, governance, and long-term viability?

## Key Graduated Projects

These are production-ready projects you should know:

```mermaid
flowchart TB
    subgraph GraduatedProjects [GRADUATED PROJECTS]
        direction TB
        K8s["<b>KUBERNETES</b><br>Container orchestration platform<br>The foundation of cloud native"]
        Prom["<b>PROMETHEUS</b><br>Monitoring and alerting<br>Time-series database for metrics"]
        Env["<b>ENVOY</b><br>Service proxy / data plane<br>Used by service meshes (Istio)"]
        Cont["<b>CONTAINERD</b><br>Container runtime<br>Default runtime for Kubernetes"]
        Helm["<b>HELM</b><br>Package manager for Kubernetes<br>Charts for installing applications"]
        Etcd["<b>ETCD</b><br>Distributed key-value store<br>Kubernetes uses it for state"]
        Flu["<b>FLUENTD</b><br>Log collection and forwarding<br>Unified logging layer"]
        Harb["<b>HARBOR</b><br>Container registry<br>With security scanning"]
        More["And many more..."]
        
        K8s ~~~ Prom ~~~ Env ~~~ Cont ~~~ Helm ~~~ Etcd ~~~ Flu ~~~ Harb ~~~ More
    end
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

```mermaid
flowchart TB
    subgraph Landscape [CNCF LANDSCAPE - landscape.cncf.io]
        direction TB
        Info["<b>What it is:</b><br>• Interactive map of cloud native technologies<br>• Includes CNCF projects AND commercial products<br>• Organized by category"]
        
        subgraph Categories [Categories Include:]
            direction LR
            Prov[Provisioning]
            Run[Runtime]
            Orch[Orchestration]
            App[App Def]
            Plat[Platform]
            Obs[Observability]
            Serv[Serverless]
            Spec[Special]
            
            Prov ~~~ Run ~~~ Orch ~~~ App
            Plat ~~~ Obs ~~~ Serv ~~~ Spec
        end
        
        Stats["1000+ projects and products!"]
        
        Usage["<b>Use it to:</b><br>• Discover tools for specific needs<br>• Compare alternatives<br>• See what's popular/mature"]
        
        Info ~~~ Categories ~~~ Stats ~~~ Usage
    end
```

---

## Key Projects to Know for KCNA

### Observability Stack

```mermaid
flowchart TB
    subgraph Observability [OBSERVABILITY]
        direction TB
        Prom["<b>PROMETHEUS (Graduated)</b><br>• Metrics collection and storage<br>• Pull-based model<br>• PromQL query language<br>• AlertManager for alerting"]
        Graf["<b>GRAFANA (Not CNCF, but commonly paired)</b><br>• Dashboards and visualization<br>• Works with Prometheus"]
        Jaeg["<b>JAEGER (Graduated)</b><br>• Distributed tracing<br>• Track requests across services"]
        Flu["<b>FLUENTD (Graduated)</b><br>• Log collection<br>• Routes logs to storage"]
        Otel["<b>OPENTELEMETRY (Incubating)</b><br>• Unified observability framework<br>• Traces, metrics, logs<br>• Vendor-neutral"]
        
        Prom ~~~ Graf ~~~ Jaeg ~~~ Flu ~~~ Otel
    end
```

### Networking & Service Mesh

```mermaid
flowchart TB
    subgraph Networking [NETWORKING]
        direction TB
        Env["<b>ENVOY (Graduated)</b><br>• L7 proxy<br>• Data plane for service meshes<br>• Dynamic configuration via API"]
        Istio["<b>ISTIO (Not CNCF - but very popular)</b><br>• Service mesh<br>• Uses Envoy<br>• Traffic management, security, observability"]
        Link["<b>LINKERD (Graduated)</b><br>• Service mesh<br>• Lightweight, focused on simplicity"]
        Cil["<b>CILIUM (Graduated)</b><br>• eBPF-based networking<br>• CNI plugin<br>• Network policies, observability"]
        Core["<b>COREDNS (Graduated)</b><br>• DNS server for Kubernetes<br>• Default DNS in Kubernetes"]
        
        Env ~~~ Istio ~~~ Link ~~~ Cil ~~~ Core
    end
```

### Security

```mermaid
flowchart TB
    subgraph Security [SECURITY]
        direction TB
        Falco["<b>FALCO (Graduated)</b><br>• Runtime security<br>• Detects abnormal behavior<br>• Uses syscall monitoring"]
        OPA["<b>OPA - OPEN POLICY AGENT (Graduated)</b><br>• Policy as code<br>• Admission control<br>• General-purpose policy engine"]
        Spiffe["<b>SPIFFE/SPIRE (Graduated)</b><br>• Service identity<br>• Workload authentication<br>• Zero-trust security"]
        
        Falco ~~~ OPA ~~~ Spiffe
    end
```

---

> **Stop and think**: The CNCF Landscape has over 1,000 entries, but not all of them are CNCF projects. Many are commercial products or projects hosted elsewhere. Why would the landscape include non-CNCF tools, and how could this be misleading for someone choosing production tooling?

## CNCF Certifications

```mermaid
flowchart TB
    subgraph Certs [CNCF CERTIFICATIONS]
        direction TB
        KCNA["<b>KCNA - Kubernetes and Cloud Native Associate</b><br>• Entry-level, multiple choice<br>• Foundational knowledge<br>• THIS exam!"]
        KCSA["<b>KCSA - Kubernetes and Cloud Native Security Associate</b><br>• Security fundamentals<br>• Multiple choice"]
        CKA["<b>CKA - Certified Kubernetes Administrator</b><br>• Hands-on, performance-based<br>• Cluster administration"]
        CKAD["<b>CKAD - Certified Kubernetes Application Developer</b><br>• Hands-on, performance-based<br>• Application deployment"]
        CKS["<b>CKS - Certified Kubernetes Security Specialist</b><br>• Hands-on, performance-based<br>• Security hardening<br>• Requires CKA first"]
        
        KCNA --> CKA
        KCNA --> CKAD
        CKA --> CKS
        
        Path["<b>Path:</b> KCNA → CKA/CKAD → CKS<br>All five = Kubestronaut!"]
        KCSA ~~~ Path
    end
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

1. **Your team needs a container registry with built-in vulnerability scanning and image signing for production use. A colleague suggests Docker Hub. What CNCF Graduated project is designed specifically for this use case, and what advantages does it offer over a public registry?**
   <details>
   <summary>Answer</summary>
   Harbor is a CNCF Graduated container registry that provides vulnerability scanning, image signing (with Notary/cosign), role-based access control, and image replication across registries. Unlike Docker Hub, Harbor can be self-hosted within your infrastructure, giving you control over where images are stored (important for compliance and data residency). It integrates with Trivy for scanning and supports OCI artifacts beyond container images. Its Graduated status means it has passed independent security audits and has proven production governance.
   </details>

2. **A startup is evaluating two service mesh options: Linkerd (CNCF Graduated) and a newer mesh that just entered CNCF Sandbox with more features. The startup handles financial transactions. Which factors from the CNCF maturity model should guide their decision?**
   <details>
   <summary>Answer</summary>
   For financial transactions, the Graduated project (Linkerd) is the safer choice. Graduated status means: independent security audit completed, diverse maintainer base (no single-vendor dependency), proven production adoption across many organizations, and committed long-term governance. The Sandbox project may have attractive features, but it has not proven its security posture or governance resilience. Sandbox projects are early-stage experiments -- good for evaluation in non-critical environments, but risky for production financial workloads. Features matter less than stability and security when processing money.
   </details>

3. **An engineer says "we need monitoring, so let's install Prometheus for metrics, Fluentd for logs, and Jaeger for traces." Map each tool to which observability pillar it serves and explain why all three are needed together rather than just one.**
   <details>
   <summary>Answer</summary>
   Prometheus serves the metrics pillar (numerical measurements over time -- CPU usage, request rates, error counts). Fluentd serves the logs pillar (event records with context -- error messages, audit trails, application events). Jaeger serves the traces pillar (request paths across distributed services -- which service is slow, where did the request fail). All three are needed because each answers a different question: metrics detect that something is wrong, traces locate where the problem is across services, and logs explain why the problem occurred. Using only one pillar leaves you blind to the other two dimensions.
   </details>

4. **A developer asks why Kubernetes uses CoreDNS instead of just relying on the standard DNS server that comes with the operating system. What role does CoreDNS (a CNCF Graduated project) play specifically in Kubernetes?**
   <details>
   <summary>Answer</summary>
   CoreDNS is the cluster DNS server in Kubernetes. It provides DNS-based service discovery -- when a Pod looks up `backend.default.svc.cluster.local`, CoreDNS resolves it to the Service's ClusterIP. The host OS DNS server does not know about Kubernetes Services, Pods, or the `cluster.local` domain. CoreDNS watches the Kubernetes API to maintain an up-to-date mapping of Service names to IPs, enabling Pods to discover each other by name rather than hardcoded IP addresses. It is the default DNS server in Kubernetes and is essential for Service discovery to work.
   </details>

5. **After passing KCNA, you want to pursue more Kubernetes certifications. You have a developer background and want to eventually earn all five for Kubestronaut status. In what order should you take the remaining certifications, and why does CKS require CKA first?**
   <details>
   <summary>Answer</summary>
   A recommended path after KCNA: take CKAD (since you have a developer background, application development is the natural next step), then CKA (administration skills build on your CKAD experience), then CKS (security specialization). KCSA can be taken at any time since it is multiple-choice like KCNA. CKS requires a valid CKA certification because security hardening requires hands-on cluster administration skills -- you need to know how to configure RBAC, admission controllers, and audit logging before you can secure them. The Kubestronaut title requires all five to be valid simultaneously.
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