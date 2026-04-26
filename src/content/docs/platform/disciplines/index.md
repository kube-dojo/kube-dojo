---
title: "Platform Disciplines"
sidebar:
  order: 1
  label: "Disciplines"
---
Platform Disciplines turns foundation theory into operating practice: SRE, platform engineering, delivery automation, security, data, AI, cost, and leadership. Use [Platform Foundations](/platform/foundations/) when the underlying concepts are shaky, and move to [Platform Toolkits](/platform/toolkits/) when you need concrete tools and implementation patterns. The path through Disciplines is role-shaped.

## Default Order

There is no single perfect order for every learner. Use the sequence that matches the work you are moving toward.

| Route | Recommended sequence |
|---|---|
| SRE | [SRE](/platform/disciplines/core-platform/sre/) -> [Kubernetes Networking](/platform/disciplines/reliability-security/networking/) -> [DevSecOps](/platform/disciplines/reliability-security/devsecops/) -> [Chaos Engineering](/platform/disciplines/reliability-security/chaos-engineering/) -> [Release Engineering](/platform/disciplines/delivery-automation/release-engineering/) |
| DevEx Builder | [Platform Engineering](/platform/disciplines/core-platform/platform-engineering/) -> [GitOps](/platform/disciplines/delivery-automation/gitops/) -> [Infrastructure as Code](/platform/disciplines/delivery-automation/iac/) -> [Release Engineering](/platform/disciplines/delivery-automation/release-engineering/) -> [Platform Leadership](/platform/disciplines/core-platform/leadership/) |
| Platform Architect | [Platform Engineering](/platform/disciplines/core-platform/platform-engineering/) -> [Kubernetes Networking](/platform/disciplines/reliability-security/networking/) -> [Infrastructure as Code](/platform/disciplines/delivery-automation/iac/) -> [AI Infrastructure](/platform/disciplines/data-ai/ai-infrastructure/) -> [FinOps](/platform/disciplines/business-value/finops/) -> [Platform Leadership](/platform/disciplines/core-platform/leadership/) |

If you are unsure, start with [Platform Engineering](/platform/disciplines/core-platform/platform-engineering/). It is the common product layer for most platform work.

## Discipline Sections

| Section | Modules | Best for | Pair with |
|---|---:|---|---|
| [SRE](/platform/disciplines/core-platform/sre/) | — | SREs and operators responsible for reliability, incident response, and service ownership | [Reliability Engineering](/platform/foundations/reliability-engineering/) and [Observability Theory](/platform/foundations/observability-theory/) |
| [Platform Engineering](/platform/disciplines/core-platform/platform-engineering/) | — | platform teams building internal products for developers | [Systems Thinking](/platform/foundations/systems-thinking/) and [Engineering Leadership](/platform/foundations/engineering-leadership/) |
| [Platform Leadership](/platform/disciplines/core-platform/leadership/) | — | leads shaping adoption, team structure, roadmaps, and operating models | [Engineering Leadership](/platform/foundations/engineering-leadership/) and [Platform Engineering](/platform/disciplines/core-platform/platform-engineering/) |
| [GitOps](/platform/disciplines/delivery-automation/gitops/) | — | teams managing infrastructure and applications through reviewed Git workflows | [Infrastructure as Code](/platform/disciplines/delivery-automation/iac/) and [Security Principles](/platform/foundations/security-principles/) |
| [Release Engineering](/platform/disciplines/delivery-automation/release-engineering/) | — | teams shipping software through repeatable build, test, rollout, and rollback systems | [Reliability Engineering](/platform/foundations/reliability-engineering/) and [GitOps](/platform/disciplines/delivery-automation/gitops/) |
| [Infrastructure as Code](/platform/disciplines/delivery-automation/iac/) | — | engineers standardizing environments, cloud resources, policy, and lifecycle management | [Distributed Systems](/platform/foundations/distributed-systems/) and [GitOps](/platform/disciplines/delivery-automation/gitops/) |
| [DevSecOps](/platform/disciplines/reliability-security/devsecops/) | — | security-minded platform and delivery teams embedding controls into pipelines | [Security Principles](/platform/foundations/security-principles/) and [Release Engineering](/platform/disciplines/delivery-automation/release-engineering/) |
| [Chaos Engineering](/platform/disciplines/reliability-security/chaos-engineering/) | — | SREs and resilience teams validating failure behavior before incidents | [Reliability Engineering](/platform/foundations/reliability-engineering/) and [Distributed Systems](/platform/foundations/distributed-systems/) |
| [Kubernetes Networking](/platform/disciplines/reliability-security/networking/) | — | platform operators and architects responsible for CNI, ingress, service mesh, and policy | [Advanced Networking](/platform/foundations/advanced-networking/) and [Security Principles](/platform/foundations/security-principles/) |
| [MLOps](/platform/disciplines/data-ai/mlops/) | — | teams operating model training, deployment, governance, and lifecycle workflows | [Distributed Systems](/platform/foundations/distributed-systems/) and [Data Engineering](/platform/disciplines/data-ai/data-engineering/) |
| [AIOps](/platform/disciplines/data-ai/aiops/) | — | operations teams applying machine learning to events, incidents, and observability signals | [Observability Theory](/platform/foundations/observability-theory/) and [SRE](/platform/disciplines/core-platform/sre/) |
| [AI Infrastructure](/platform/disciplines/data-ai/ai-infrastructure/) | — | architects and platform teams running GPU scheduling, distributed training, and LLM serving | [Distributed Systems](/platform/foundations/distributed-systems/) and [Kubernetes Networking](/platform/disciplines/reliability-security/networking/) |
| [Data Engineering](/platform/disciplines/data-ai/data-engineering/) | — | data platform teams running pipelines, storage, orchestration, and streaming on Kubernetes | [Distributed Systems](/platform/foundations/distributed-systems/) and [Infrastructure as Code](/platform/disciplines/delivery-automation/iac/) |
| [FinOps](/platform/disciplines/business-value/finops/) | — | platform owners and engineering leaders accountable for cloud cost, usage, and value | [Systems Thinking](/platform/foundations/systems-thinking/) and [Platform Leadership](/platform/disciplines/core-platform/leadership/) |

## Prerequisites Check

Before you read Disciplines, you should already understand:

- core Kubernetes objects, scheduling, services, storage, and workload lifecycle from a base Kubernetes route
- Linux, networking, and cloud fundamentals well enough to troubleshoot a running service
- the main ideas in [Platform Foundations](/platform/foundations/), especially systems thinking, reliability, observability, security, and distributed systems
- Git workflows, CI/CD basics, environment promotion, and rollback concepts
- how teams own production systems: alerts, incidents, postmortems, service levels, and change management
- the difference between learning a discipline and selecting a specific implementation tool

## Next Handoffs

Move into [Toolkits](/platform/toolkits/) when you are ready to implement the practices with concrete systems.

| When you are ready to... | Go next |
|---|---|
| choose concrete tools for delivery, operations, security, or data platforms | [Platform Toolkits](/platform/toolkits/) |
| repair weak theory behind a discipline | [Platform Foundations](/platform/foundations/) |
| go deeper on Kubernetes administration or certification scope | [Kubernetes](/k8s/) |
| strengthen Linux, networking, and troubleshooting basics | [Linux](/linux/) |
| connect platform work to cloud provider architecture | [Cloud](/cloud/) |
