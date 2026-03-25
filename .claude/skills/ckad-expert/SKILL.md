---
name: ckad-expert
description: CKAD exam knowledge. Use for Kubernetes developer certification, application deployment, multi-container pods. Triggers on "CKAD", "developer certification", "application developer".
---

# CKAD Expert Skill

Authoritative knowledge source for CKAD (Certified Kubernetes Application Developer) exam preparation. Developer-focused certification with emphasis on application deployment and lifecycle.

## When to Use
- Writing or reviewing CKAD curriculum content
- Answering questions about CKAD exam topics
- Comparing CKAD vs CKA scope
- Application deployment best practices

## CKAD Exam Overview

### Exam Format
- **Duration**: 2 hours (120 minutes)
- **Questions**: ~15-20 performance-based tasks
- **Passing Score**: 66%
- **Environment**: Ubuntu-based, kubeadm clusters
- **Resources Allowed**: kubernetes.io, helm.sh, github.com/kubernetes

### Domain Weights

| Domain | Weight |
|--------|--------|
| Application Design and Build | 20% |
| Application Deployment | 20% |
| Application Observability and Maintenance | 15% |
| Application Environment, Configuration and Security | 25% |
| Services and Networking | 20% |

## Key Topics

### Application Design and Build (20%)
- Define, build and modify container images
- Jobs and CronJobs
- Multi-container pod design patterns (sidecar, init, ambassador)
- Utilize persistent and ephemeral volumes

### Application Deployment (20%)
- Deployments and rolling updates
- Helm package manager
- Kustomize
- Blue/green, canary deployments

### Application Observability (15%)
- API deprecations
- Implement probes (liveness, readiness, startup)
- Monitor applications
- Container logging
- Debugging in Kubernetes

### Application Environment (25%)
- CRDs (Custom Resource Definitions)
- ConfigMaps and Secrets
- ServiceAccounts
- Resource requirements and limits
- SecurityContexts

### Services and Networking (20%)
- Service types and endpoints
- Ingress controllers and resources
- NetworkPolicies

## Overlap with CKA (~60%)

Shared topics:
- Pods, Deployments, Services
- ConfigMaps, Secrets
- PersistentVolumes, PersistentVolumeClaims
- RBAC basics
- NetworkPolicies
- Helm, Kustomize

## CKAD-Specific Focus

Topics emphasized more in CKAD:
- Multi-container pod patterns (sidecar, init containers)
- Application probes (liveness, readiness, startup)
- Jobs and CronJobs
- API deprecations awareness
- Container image building

## Exam Strategy

Same three-pass method as CKA:
1. **Pass 1**: Quick imperative commands (create pod, expose service)
2. **Pass 2**: Medium tasks (probes, multi-container pods)
3. **Pass 3**: Complex scenarios (debugging, CRDs)

## Official Resources

- [CNCF Curriculum](https://github.com/cncf/curriculum)
- [CKAD Program](https://training.linuxfoundation.org/certification/certified-kubernetes-application-developer-ckad/)
- [kubernetes.io/docs](https://kubernetes.io/docs/)
