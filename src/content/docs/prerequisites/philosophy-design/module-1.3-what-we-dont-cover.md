---
title: "Module 1.3: What We Don't Cover (and Why)"
slug: prerequisites/philosophy-design/module-1.3-what-we-dont-cover
sidebar:
  order: 4
---
> **Complexity**: `[QUICK]` - Setting expectations
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: Module 1, Module 2

---

## Why This Module Matters

Here's a secret that paid certification courses won't tell you: **you can waste 100+ hours studying topics that will never appear on the exam.** We've seen it happen — engineers spending weeks deep-diving into etcd internals or building custom CNI plugins, only to discover the CKA doesn't test any of it.

KubeDojo is surgical about what we teach. Every module exists because it either appears on the exam or is essential for understanding something that does. This module tells you exactly what we skip and why — so you don't waste a single hour on the wrong thing.

---

## Our Philosophy: Exam-Focused, Not Exhaustive

KubeDojo exists to help you pass certifications efficiently. We apply the 80/20 rule:

```
┌─────────────────────────────────────────────────────────────┐
│              THE 80/20 RULE FOR CERTIFICATIONS              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ████████████████████████████████████████ 80% of exam      │
│  █ Core topics we cover deeply          █ questions        │
│  ████████████████████████████████████████                   │
│                                                             │
│  ████████████ 20% of exam questions                        │
│  █ Edge cases, rarely tested, advanced  █                  │
│  ████████████                                               │
│                                                             │
│  Result: Maximum pass probability with efficient study      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

We don't try to cover everything. We cover what matters for passing.

---

## What We Deliberately Skip

### 1. Cloud Provider Specifics

| Topic | Why We Skip | Where to Learn |
|-------|-------------|----------------|
| AWS EKS details | Exam uses generic K8s, not cloud-specific | AWS documentation, eksctl docs |
| GKE features | Same reason | Google Cloud documentation |
| AKS specifics | Same reason | Azure documentation |
| Cloud IAM integration | Provider-specific | Provider documentation |

**Our approach**: We teach Kubernetes. Cloud providers add their own layers. Learn the platform, then learn your provider's implementation.

### 2. Production Operations at Scale

| Topic | Why We Skip | Where to Learn |
|-------|-------------|----------------|
| Multi-cluster federation | Beyond certification scope | K8s docs, KubeFed project |
| Cluster autoscaling | Cloud-specific implementations | Provider docs |
| Disaster recovery | Organization-specific | SRE books, your company runbooks |
| Cost optimization | Cloud-specific | FinOps resources, cloud calculators |

**Our approach**: Certifications test fundamentals. Production operations require experience plus company-specific context.

### 3. Deep Networking

| Topic | Why We Skip | Where to Learn |
|-------|-------------|----------------|
| BGP configuration | CKA touches basics only | Network engineering resources |
| Service mesh internals | Istio/Linkerd are separate domains | Project documentation |
| eBPF/Cilium internals | Advanced networking topic | Cilium documentation |
| Custom CNI development | Developer topic, not admin | CNI specification |

**Our approach**: We cover networking concepts the exam tests. Deep networking is a separate specialization.

### 4. Specific Tools/Projects

| Tool | Why We Skip | Where to Learn |
|------|-------------|----------------|
| ArgoCD | GitOps tool, not on exam | ArgoCD documentation |
| Istio | Service mesh, separate certification track | Istio documentation |
| Terraform | IaC tool, not K8s-specific | HashiCorp Learn |
| Prometheus/Grafana | Observability tools, briefly touched | Project documentation |

**Our approach**: We mention these tools for context but don't teach them deeply. Each deserves its own curriculum.

---

## Why We Make These Choices

### Reason 1: Time Efficiency

```
Learning everything about Kubernetes: 6-12 months
Passing CKA with focused study: 4-8 weeks

The difference: Focus
```

Certifications are gates, not destinations. Pass efficiently, then go deep on what your job requires.

### Reason 2: Exam Relevance

The CKA, CKAD, and CKS have defined curricula. We align to those curricula. Adding content beyond the exam:
- Increases study time
- Adds confusion
- Doesn't improve pass rates

### Reason 3: Avoiding Outdated Content

Kubernetes moves fast. The more topics we cover, the more we must maintain. By focusing on exam-relevant content:
- Less content to keep updated
- Higher quality on what we cover
- More sustainable long-term

---

## The "Just Enough" Principle

For topics we do cover, we aim for exam sufficiency, not exhaustive mastery:

```
┌─────────────────────────────────────────────────────────────┐
│              DEPTH LEVELS BY TOPIC                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Topic              Exam    KubeDojo   Expert Level        │
│                     Needs   Coverage                        │
│  ──────────────────────────────────────────────────────    │
│  Pods               ████    ████       ████████████        │
│  Deployments        ████    ████       ██████████          │
│  Services           ████    ████       █████████████       │
│  NetworkPolicy      ███     ███        ████████████        │
│  RBAC               ███     ███        ██████████████      │
│  Helm               ██      ██         ████████████        │
│  etcd backup        █       █          ████████████████    │
│                                                             │
│  Key: █ = coverage depth                                   │
│  We match exam needs, not expert level                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Where We Suggest Going Deeper

After passing certifications, you'll want to go deeper. Here's our recommended path:

### For Platform Engineers
- Cluster API
- GitOps (ArgoCD/Flux)
- Multi-tenancy patterns
- Platform engineering resources

### For Developers
- Kubernetes patterns (sidecar, ambassador, adapter)
- Operators and CRD development
- Kubernetes API programming
- Kubectl plugins

### For Security Focus
- OPA/Gatekeeper deep dive
- Falco and runtime security
- Supply chain security (Sigstore)
- Network policy advanced patterns

### For SRE/Operations
- SLO-based alerting
- Chaos engineering
- Capacity planning
- Incident response

---

## Visualization: KubeDojo Scope

```
┌─────────────────────────────────────────────────────────────┐
│            THE KUBERNETES KNOWLEDGE UNIVERSE                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    ┌─────────────────────────────────────────────────┐     │
│    │                                                 │     │
│    │              CNCF Landscape                     │     │
│    │           (1000+ projects)                      │     │
│    │                                                 │     │
│    │    ┌───────────────────────────────────┐       │     │
│    │    │                                   │       │     │
│    │    │     Production Operations         │       │     │
│    │    │   (Company-specific, tools, etc)  │       │     │
│    │    │                                   │       │     │
│    │    │    ┌───────────────────────┐     │       │     │
│    │    │    │                       │     │       │     │
│    │    │    │  ╔═══════════════╗   │     │       │     │
│    │    │    │  ║   KubeDojo    ║   │     │       │     │
│    │    │    │  ║  (Cert Focus) ║   │     │       │     │
│    │    │    │  ╚═══════════════╝   │     │       │     │
│    │    │    │   Certification      │     │       │     │
│    │    │    │   Curricula          │     │       │     │
│    │    │    └───────────────────────┘     │       │     │
│    │    │                                   │       │     │
│    │    └───────────────────────────────────┘       │     │
│    │                                                 │     │
│    └─────────────────────────────────────────────────┘     │
│                                                             │
│  We focus on the certification core.                        │
│  The broader ecosystem is beyond our scope.                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **The CNCF landscape has 1000+ projects.** No human can master them all. Specialization is necessary.

- **Most production K8s users know ~20% of Kubernetes deeply.** They know what their job requires. Certifications prove breadth, work builds depth.

- **Certification curricula change.** Topics get added and removed. We track changes and update accordingly.

- **"Expert" is context-dependent.** A networking expert knows different things than a security expert. There's no universal "Kubernetes expert" checklist.

---

## Common Questions

### "But I might need [topic] at work!"

Possibly. Our suggestion:
1. Pass the certification first (validates fundamentals)
2. Learn job-specific topics on the job
3. Use project documentation for tools (ArgoCD, Istio, etc.)

### "Why not include everything to be complete?"

Completeness is impossible and counterproductive:
- K8s changes constantly
- More content = more maintenance = stale content
- Focused content = higher quality

### "What if the exam asks about something you didn't cover?"

Our curriculum matches official exam objectives. If something appears on the exam, it's in our curriculum. Edge cases that rarely appear aren't worth the study time.

---

## Quiz

1. **Why does KubeDojo skip cloud provider specifics (EKS, GKE, AKS)?**
   <details>
   <summary>Answer</summary>
   Certification exams test generic Kubernetes, not cloud-specific implementations. Learning provider specifics after understanding core K8s is more efficient. Provider documentation covers their specific features.
   </details>

2. **What is the 80/20 rule as applied to certification study?**
   <details>
   <summary>Answer</summary>
   80% of exam questions come from core topics. Focusing study on these core topics maximizes pass probability with minimum time investment. Edge cases and rarely-tested topics aren't worth extensive study.
   </details>

3. **Why doesn't KubeDojo teach ArgoCD, Istio, or Terraform?**
   <details>
   <summary>Answer</summary>
   These are separate tools with their own learning curves. They're not part of core Kubernetes certifications. Each deserves its own dedicated curriculum. We mention them for context but don't teach them deeply.
   </details>

4. **What should you do after passing a certification?**
   <details>
   <summary>Answer</summary>
   Go deeper on topics your job requires. The certification validates breadth; work builds depth. Use project documentation for specific tools, and specialize based on your role (platform engineering, security, SRE, etc.).
   </details>

---

## Reflection Exercise

This module sets expectations—reflect on your learning journey:

**1. Your learning goals:**
- Why are you learning Kubernetes?
- Is certification the end goal, or a stepping stone?
- What specific job role or project motivates you?

**2. The 80/20 principle:**
- In your field, what 20% of knowledge handles 80% of situations?
- Does going deeper always help, or can it distract?

**3. Scope discipline:**
- Have you ever wasted time learning something that turned out irrelevant?
- How do you decide what's worth learning deeply vs. just knowing exists?

**4. After certification:**
- Which specialization interests you? (Platform engineering, security, SRE, development?)
- What would your ideal Kubernetes job look like?

**5. Time budgeting:**
- How much time can you dedicate to this?
- Given KubeDojo's focus, do you need additional resources for your specific goals?

Understanding scope helps you learn efficiently and plan beyond certification.

---

## Summary

KubeDojo makes deliberate choices about scope:

- **We cover**: Certification curricula thoroughly
- **We skip**: Cloud specifics, production operations at scale, deep networking, specific tools
- **Our philosophy**: Exam-focused efficiency over exhaustive coverage
- **After certification**: Specialize based on your role and job requirements

Understanding these boundaries helps you set expectations and plan your broader learning journey.

---

## Next Module

[Module 1.4: Dead Ends - Technologies We Skip](../module-1.4-dead-ends/) - Why certain technologies are deprecated and shouldn't be learned.
