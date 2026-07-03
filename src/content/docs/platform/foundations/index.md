---
title: "Platform Foundations"
sidebar:
  order: 1
  label: "Foundations"
---
Platform Foundations covers the theory that changes slowly: systems thinking, reliability, observability, security, distributed systems, networking, eBPF, and engineering leadership. Use this section to build durable judgment before moving into [Platform Disciplines](/platform/disciplines/), where the same ideas become SRE, platform engineering, GitOps, DevSecOps, MLOps, FinOps, and delivery practice.

## Default Order

There is no single perfect order for every learner. Use the sequence that matches the work you are moving toward.

| Route | Recommended sequence |
|---|---|
| SRE | [Systems Thinking](/platform/foundations/systems-thinking/) -> [Reliability Engineering](/platform/foundations/reliability-engineering/) -> [Observability Theory](/platform/foundations/observability-theory/) -> [Distributed Systems](/platform/foundations/distributed-systems/) -> [Security Principles](/platform/foundations/security-principles/) -> [Advanced Networking](/platform/foundations/advanced-networking/) -> [eBPF Fundamentals](/platform/foundations/ebpf/) -> [Engineering Leadership](/platform/foundations/engineering-leadership/) |
| DevEx Builder | [Systems Thinking](/platform/foundations/systems-thinking/) -> [Engineering Leadership](/platform/foundations/engineering-leadership/) -> [Reliability Engineering](/platform/foundations/reliability-engineering/) -> [Observability Theory](/platform/foundations/observability-theory/) -> [Security Principles](/platform/foundations/security-principles/) -> [Distributed Systems](/platform/foundations/distributed-systems/) -> [Advanced Networking](/platform/foundations/advanced-networking/) -> [eBPF Fundamentals](/platform/foundations/ebpf/) |
| Platform Architect | [Systems Thinking](/platform/foundations/systems-thinking/) -> [Distributed Systems](/platform/foundations/distributed-systems/) -> [Advanced Networking](/platform/foundations/advanced-networking/) -> [eBPF Fundamentals](/platform/foundations/ebpf/) -> [Security Principles](/platform/foundations/security-principles/) -> [Reliability Engineering](/platform/foundations/reliability-engineering/) -> [Observability Theory](/platform/foundations/observability-theory/) -> [Engineering Leadership](/platform/foundations/engineering-leadership/) |

If you are unsure, start with [Systems Thinking](/platform/foundations/systems-thinking/). It is the common base for every route.

## Foundation Sections

| Section | Modules | Best for | Pair with |
|---|---:|---|---|
| [Systems Thinking](/platform/foundations/systems-thinking/) | 4 | everyone entering Platform | [SRE](/platform/disciplines/core-platform/sre/) and [Platform Engineering](/platform/disciplines/core-platform/platform-engineering/) |
| [Reliability Engineering](/platform/foundations/reliability-engineering/) | 5 | SRE, operators, service owners | [SRE](/platform/disciplines/core-platform/sre/) and [Chaos Engineering](/platform/disciplines/reliability-security/chaos-engineering/) |
| [Observability Theory](/platform/foundations/observability-theory/) | 4 | SRE, DevEx builders, platform operators | [Observability Toolkits](/platform/toolkits/observability-intelligence/observability/) and [AIOps](/platform/disciplines/data-ai/aiops/) |
| [Security Principles](/platform/foundations/security-principles/) | 4 | architects, DevSecOps learners, platform owners | [DevSecOps](/platform/disciplines/reliability-security/devsecops/) and [Security Tools](/platform/toolkits/security-quality/security-tools/) |
| [Distributed Systems](/platform/foundations/distributed-systems/) | 5 | architects, SREs, data and AI platform builders | [GitOps](/platform/disciplines/delivery-automation/gitops/), [MLOps](/platform/disciplines/data-ai/mlops/), and [Data Engineering](/platform/disciplines/data-ai/data-engineering/) |
| [Advanced Networking](/platform/foundations/advanced-networking/) | 9 | architects, network-heavy operators, multi-cluster teams | [Kubernetes Networking](/platform/disciplines/reliability-security/networking/) and [Networking Toolkits](/platform/toolkits/infrastructure-networking/networking/) |
| [eBPF Fundamentals](/platform/foundations/ebpf/) | 2 | platform operators using kernel-powered networking, observability, and security tools | [Cilium](/platform/toolkits/infrastructure-networking/networking/module-5.1-cilium/), [Tetragon](/platform/toolkits/security-quality/security-tools/module-4.5-tetragon/), and [Pixie](/platform/toolkits/observability-intelligence/observability/module-1.6-pixie/) |
| [Engineering Leadership](/platform/foundations/engineering-leadership/) | 6 | senior engineers, leads, platform owners | [Platform Leadership](/platform/disciplines/core-platform/leadership/) and [Platform Engineering](/platform/disciplines/core-platform/platform-engineering/) |

## Prerequisites Check

Before you read Foundations, you should already understand:

- terminal, files, SSH, Git basics, and package installation from [Fundamentals](/prerequisites/)
- containers, Kubernetes basics, declarative YAML, and `kubectl`
- Services, Deployments, ConfigMaps, Secrets, namespaces, and labels
- basic Linux networking and troubleshooting, especially if you plan to study reliability or networking
- why CI/CD, observability, and infrastructure as code matter, even if you have not mastered the tools yet

If those topics still feel new, start with [Fundamentals](/prerequisites/), then return here after [Kubernetes Basics](/prerequisites/kubernetes-basics/) or a core [Kubernetes Certifications](/k8s/) route.

## Next Handoffs

Move into [Disciplines](/platform/disciplines/) when you can explain the theory and want to apply it to a job role.

| When you are ready to... | Go next |
|---|---|
| define service health, incidents, toil, and error budgets | [SRE](/platform/disciplines/core-platform/sre/) |
| build self-service paths for developers | [Platform Engineering](/platform/disciplines/core-platform/platform-engineering/) |
| turn delivery into a reconciled operating model | [GitOps](/platform/disciplines/delivery-automation/gitops/) or [Release Engineering](/platform/disciplines/delivery-automation/release-engineering/) |
| integrate security into delivery and runtime operations | [DevSecOps](/platform/disciplines/reliability-security/devsecops/) |
| choose concrete tools | [Toolkits](/platform/toolkits/) |
| strengthen missing background instead | [Linux](/linux/), [Cloud](/cloud/), or [Kubernetes Certifications](/k8s/) |
