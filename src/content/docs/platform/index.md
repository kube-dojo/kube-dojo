---
title: "Platform Engineering"
sidebar:
  order: 1
  label: "Platform Engineering"
---
Platform Engineering at KubeDojo is the track for people moving from "I can use Kubernetes" to "I can design, operate, secure, and evolve production platforms." It connects SRE, developer experience, delivery automation, security, data platforms, AI infrastructure, and leadership into one systems-oriented curriculum for operators, platform builders, senior developers, and architects.

## Do Not Start Here Yet

Start with [Fundamentals](/prerequisites/) if you are still learning the terminal, Git, containers, Kubernetes objects, YAML, or basic networking.

Before this track, you should already be comfortable with:

- `kubectl`, Pods, Deployments, Services, ConfigMaps, Secrets, namespaces, and labels
- basic Linux process, file, package, service, and network troubleshooting
- Git as a collaboration workflow, not only a file backup tool
- cloud-native vocabulary: containers, clusters, declarative configuration, CI/CD, and observability
- at least one Kubernetes route such as [Kubernetes Basics](/prerequisites/kubernetes-basics/), [KCNA](/k8s/kcna/), [CKA](/k8s/cka/), or equivalent production experience

If you are brand new, take this route first:

```text
Fundamentals
   |
Kubernetes Basics
   |
Linux or Cloud depth
   |
Platform Engineering
```

If you are exam-driven, use [Kubernetes Certifications](/k8s/) before this track. If you are provider-driven, use [Cloud](/cloud/) before or alongside this track. Platform Engineering assumes the basic cluster and infrastructure layer no longer feels mysterious.

## Choose Your Entry Route

### The SRE

You operate production systems, own incidents, care about reliability, and want stronger theory behind day-two decisions.

Quick-Start:

| Step | Module |
|---|---|
| 1 | [What is Systems Thinking?](/platform/foundations/systems-thinking/module-1.1-what-is-systems-thinking/) |
| 2 | [SLIs, SLOs, and Error Budgets](/platform/foundations/reliability-engineering/module-2.5-slos-slis-error-budgets/) |
| 3 | [Instrumentation Principles](/platform/foundations/observability-theory/module-3.3-instrumentation-principles/) |
| 4 | [What is SRE?](/platform/disciplines/core-platform/sre/module-1.1-what-is-sre/) |

When to come back: after you have lived through incidents or on-call handoffs, return for [Chaos Engineering](/platform/disciplines/reliability-security/chaos-engineering/) and [Engineering Leadership](/platform/foundations/engineering-leadership/).

### The DevEx Builder

You build internal workflows, golden paths, templates, portals, and self-service infrastructure for developers.

Quick-Start:

| Step | Module |
|---|---|
| 1 | [Mental Models for Operations](/platform/foundations/systems-thinking/module-1.3-mental-models-for-operations/) |
| 2 | [What is Platform Engineering?](/platform/disciplines/core-platform/platform-engineering/module-2.1-what-is-platform-engineering/) |
| 3 | [Developer Experience](/platform/disciplines/core-platform/platform-engineering/module-2.2-developer-experience/) |
| 4 | [Golden Paths](/platform/disciplines/core-platform/platform-engineering/module-2.4-golden-paths/) |

When to come back: after your first self-service workflow is in use, return for [Platform as Product](/platform/disciplines/core-platform/leadership/module-1.3-platform-as-product/), [Adoption and Migration](/platform/disciplines/core-platform/leadership/module-1.4-adoption-migration/), and [DevEx Toolkits](/platform/toolkits/developer-experience/devex-tools/).

### The Platform Architect

You make cross-team platform decisions about reliability, networking, security, delivery, cost, and long-term operating models.

Quick-Start:

| Step | Module |
|---|---|
| 1 | [What Makes Systems Distributed](/platform/foundations/distributed-systems/module-5.1-what-makes-systems-distributed/) |
| 2 | [Defense in Depth](/platform/foundations/security-principles/module-4.2-defense-in-depth/) |
| 3 | [Load Balancing](/platform/foundations/advanced-networking/module-1.5-load-balancing/) |
| 4 | [Platform Maturity](/platform/disciplines/core-platform/platform-engineering/module-2.6-platform-maturity/) |

When to come back: after you have a real platform roadmap, return for [Infrastructure as Code](/platform/disciplines/delivery-automation/iac/), [FinOps](/platform/disciplines/business-value/finops/), and [Platform Leadership](/platform/disciplines/core-platform/leadership/).

## Track Structure

| Area | Use it for | Start here |
|---|---|---|
| [Foundations](/platform/foundations/) | timeless theory: systems, reliability, observability, security, distributed systems, networking, leadership | when you need stronger mental models |
| [Disciplines](/platform/disciplines/) | applied platform practices: SRE, GitOps, DevSecOps, MLOps, FinOps, delivery, platform teams | when you know the job you need to do |
| [Toolkits](/platform/toolkits/) | current tools and implementation references | when you are choosing or operating a concrete tool |

Read Foundations to understand why the practices work. Read Disciplines to learn the work. Use Toolkits when implementation details matter.

## Exit Ramps

| If your route is... | Go next |
|---|---|
| If you came from [Kubernetes Certifications](/k8s/) | continue into [SRE](/platform/disciplines/core-platform/sre/) or [GitOps](/platform/disciplines/delivery-automation/gitops/) when exams stop answering production design questions |
| If you need provider-specific production depth | go to [Cloud](/cloud/) for AWS, Google Cloud, Azure, managed Kubernetes, networking, identity, and enterprise patterns |
| If you are going to cloud next | use [Cloud Architecture Patterns](/cloud/architecture-patterns/) after Foundations so provider details attach to sound platform decisions |
| If you want AI/ML next | use [MLOps](/platform/disciplines/data-ai/mlops/) and [AI Infrastructure](/platform/disciplines/data-ai/ai-infrastructure/) before [AI/ML Engineering](/ai-ml-engineering/) infrastructure depth |
| If private infrastructure is your target | go to [On-Premises Kubernetes](/on-premises/) after Linux, Cloud, and Platform foundations are no longer shaky |

## Common Entry Mistakes

- jumping into Disciplines (SRE, GitOps, MLOps) before any Foundations module — the practices stop making sense once the underlying theory is fuzzy
- choosing a Toolkit page (ArgoCD, Falco, Backstage) as the first read — implementation details land without grounding, and the wrong tool gets picked
- treating the alphabetical section list as a study order — Platform Engineering is role-shaped, not catalog-shaped
- skipping the readiness check above and returning later confused about why YAML, networking, or Git workflows feel underwater
- expecting cert-style scope here — Platform Engineering is operating-model territory, not exam scope

## What's Not Here Yet

Our current focus is on refining route design and tightening entry guidance. The roadmap includes improving cross-track bridges and learner handoffs to ensure the Platform track feels less like a catalog and more like a set of deliberate career routes.
