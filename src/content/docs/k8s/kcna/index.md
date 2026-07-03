---
title: "KCNA Curriculum"
sidebar:
  order: 1
  label: "KCNA"
---
> **Kubernetes and Cloud Native Associate** - Entry-level certification for cloud native fundamentals

## About KCNA

The KCNA is a **multiple-choice exam** (not hands-on) that validates foundational knowledge of Kubernetes and cloud native technologies. It's ideal for those new to cloud native or as preparation for CKA/CKAD.

| Aspect | Details |
|--------|---------|
| **Format** | Multiple choice |
| **Duration** | 90 minutes |
| **Questions** | ~60 questions |
| **Passing Score** | 75% |
| **Validity** | 2 years (3 years if earned before April 1, 2024) |

## Curriculum Structure

*Updated November 2025 - Observability merged into Cloud Native Architecture*

| Part | Topic | Weight | Modules |
|------|-------|--------|---------|
| [Part 0](part0-introduction/) | Introduction | - | 2 |
| [Part 1](part1-kubernetes-fundamentals/) | Kubernetes Fundamentals | 44% | 9 |
| [Part 2](part2-container-orchestration/) | Container Orchestration | 28% | 4 |
| [Part 3](part3-cloud-native-architecture/) | Cloud Native Architecture | 12% | 10 |
| [Part 4](part4-application-delivery/) | Application Delivery | 16% | 3 |
| **Total** | | **100%** | **28** |

## Module Overview

### Part 0: Introduction (2 modules)
- [0.1 KCNA Overview](part0-introduction/module-0.1-kcna-overview/) - Exam format and domains
- [0.2 Study Strategy](part0-introduction/module-0.2-study-strategy/) - Multiple-choice exam techniques

### Part 1: Kubernetes Fundamentals (9 modules) — 44%
- [1.1 What is Kubernetes](part1-kubernetes-fundamentals/module-1.1-what-is-kubernetes/) - Purpose and architecture
- [1.2 Container Fundamentals](part1-kubernetes-fundamentals/module-1.2-container-fundamentals/) - Container concepts
- [1.3 Control Plane](part1-kubernetes-fundamentals/module-1.3-control-plane/) - API server, etcd, scheduler
- [1.4 Node Components](part1-kubernetes-fundamentals/module-1.4-node-components/) - kubelet, kube-proxy
- [1.5 Pods](part1-kubernetes-fundamentals/module-1.5-pods/) - Basic workload unit
- [1.6 Workload Resources](part1-kubernetes-fundamentals/module-1.6-workload-resources/) - Deployments, StatefulSets
- [1.7 Services](part1-kubernetes-fundamentals/module-1.7-services/) - Service types and discovery
- [1.8 Namespaces and Labels](part1-kubernetes-fundamentals/module-1.8-namespaces-labels/) - Organization
- [1.9 Debugging Basics](part1-kubernetes-fundamentals/module-1.9-debugging-basics/) - Basic troubleshooting theory

### Part 2: Container Orchestration (4 modules) — 28%
- [2.1 Scheduling](part2-container-orchestration/module-2.1-scheduling/) - How pods get assigned
- [2.2 Scaling](part2-container-orchestration/module-2.2-scaling/) - HPA, VPA, Cluster Autoscaler
- [2.3 Storage](part2-container-orchestration/module-2.3-storage/) - PV, PVC, StorageClass
- [2.4 Configuration](part2-container-orchestration/module-2.4-configuration/) - ConfigMaps and Secrets

### Part 3: Cloud Native Architecture (10 modules) — 12%
*Includes Observability (merged November 2025)*

- [3.1 Cloud Native Principles](part3-cloud-native-architecture/module-3.1-cloud-native-principles/) - 12-factor apps
- [3.2 CNCF Ecosystem](part3-cloud-native-architecture/module-3.2-cncf-ecosystem/) - Projects and landscape
- [3.3 Cloud Native Patterns](part3-cloud-native-architecture/module-3.3-patterns/) - Service mesh, GitOps
- [3.4 Observability Fundamentals](part3-cloud-native-architecture/module-3.4-observability-fundamentals/) - Metrics, logs, traces
- [3.5 Observability Tools](part3-cloud-native-architecture/module-3.5-observability-tools/) - Prometheus, Grafana, Jaeger
- [3.6 Security Basics](part3-cloud-native-architecture/module-3.6-security-basics/) - Cloud native security foundations
- [3.7 Community and Collaboration](part3-cloud-native-architecture/module-3.7-community-collaboration/) - CNCF governance, SIGs, and project collaboration
- [3.8 AI/ML in Cloud Native](part3-cloud-native-architecture/module-3.8-ai-ml-cloud-native/) - AI/LLM workloads, GPU scheduling, model serving
- [3.9 WebAssembly](part3-cloud-native-architecture/module-3.9-webassembly/) - Wasm as container alternative, WASI, SpinKube
- [3.10 Green Computing & Sustainability](part3-cloud-native-architecture/module-3.10-green-computing/) - Carbon-aware scheduling, resource efficiency

### Part 4: Application Delivery (3 modules) — 16%
- [4.1 CI/CD Fundamentals](part4-application-delivery/module-4.1-ci-cd/) - Pipelines and deployment
- [4.2 Application Packaging](part4-application-delivery/module-4.2-application-packaging/) - Helm and Kustomize
- [4.3 Release Strategies](part4-application-delivery/module-4.3-release-strategies/) - Progressive delivery and rollout patterns

## How to Use This Curriculum

1. **Follow the order** - Modules build on each other
2. **Read actively** - Don't just skim, understand concepts
3. **Take quizzes** - Each module has quiz questions
4. **Review diagrams** - Visual learning is key for multiple-choice
5. **Focus on "why"** - KCNA tests understanding, not commands

## Key Differences from CKA/CKAD

| Aspect | KCNA | CKA/CKAD |
|--------|------|----------|
| Format | Multiple choice | Hands-on lab |
| Focus | Concepts | Commands |
| Difficulty | Entry-level | Professional |
| Kubernetes access | None | Full cluster |

## Gap Analysis (Nov 2025 Update)

The November 2025 KCNA curriculum update introduced several emerging topics that are minor exam areas but worth being aware of:

- **AI/LLM Workloads on Kubernetes** — Running inference and training workloads, GPU scheduling, model serving
- **WebAssembly (Wasm)** — Wasm as a lightweight alternative to containers, WASI, SpinKube
- **Green Computing** — Carbon-aware scheduling, resource efficiency, sustainability in cloud native

These topics represent a small percentage of questions but signal where the cloud native ecosystem is heading. See Modules 3.8-3.10 above.

## Study Tips

- **Understand, don't memorize** - The exam tests concepts
- **Know CNCF projects** - Especially graduated ones
- **Focus on Parts 1 & 2** - They're 72% of the exam combined
- **Review diagrams** - Visuals help with multiple-choice
- **Take practice tests** - Get comfortable with the format

## Start Learning

Begin with [Part 0: Introduction](part0-introduction/module-0.1-kcna-overview/) to understand the exam format, then proceed through each part in order.

Good luck on your KCNA journey!
