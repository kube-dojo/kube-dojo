---
title: "Extending Kubernetes"
sidebar:
  order: 1
  label: "Extending Kubernetes"
---
**Build ON Kubernetes, not just USE it.**

This track is for engineers who need to extend the Kubernetes platform itself — writing custom controllers, operators, admission webhooks, and scheduler plugins. It's the difference between a K8s user and a K8s platform builder.

All modules include real, compilable Go code.

---

## Modules

| # | Module | Time | What You'll Build |
|---|--------|------|-------------------|
| 1.1 | [API & Extensibility Architecture](module-1.1-api-deep-dive/) | 3h | Go program with client-go Informer |
| 1.2 | [CRDs Deep Dive](module-1.2-crds-advanced/) | 3h | Complex CRD with validation, versioning, subresources |
| 1.3 | [Controllers with client-go](module-1.3-controllers-client-go/) | 5h | Custom controller from scratch (no frameworks) |
| 1.4 | [Kubebuilder & Operators](module-1.4-kubebuilder/) | 4h | Scaffolded Operator with Reconciler |
| 1.5 | [Advanced Operator Development](module-1.5-advanced-operators/) | 5h | Finalizers, Conditions, Events, envtest |
| 1.6 | [Admission Webhooks](module-1.6-admission-webhooks/) | 4h | Sidecar-injecting mutating webhook |
| 1.7 | [Scheduler Plugins](module-1.7-scheduler-plugins/) | 4h | Custom Score plugin + secondary scheduler |
| 1.8 | [API Aggregation](module-1.8-api-aggregation/) | 5h | Extension API Server |

**Total time**: ~33 hours

---

## Prerequisites

- CKA certification or equivalent Kubernetes experience
- Go programming (basic to intermediate)
- [CKA Module 1.5: CRDs & Operators](../cka/part1-cluster-architecture/module-1.5-crds-operators/) is the intro — this goes much deeper
