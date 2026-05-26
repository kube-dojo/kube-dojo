---
name: platform-expert
description: Platform Engineering discipline expertise (SRE, GitOps, DevSecOps, MLOps, Platform Eng). Use for discipline content, tool recommendations, architecture patterns. Triggers on "SRE", "GitOps", "DevSecOps", "MLOps", "platform engineering", "SLO", "ArgoCD", "Falco".
---

# Platform Expert

Consolidated knowledge for all Platform Engineering disciplines and toolkits. Use when writing, reviewing, or verifying platform content.

## Disciplines Overview

| Discipline | Modules | Core Concepts |
|-----------|---------|---------------|
| SRE | 7 | SLOs, error budgets, toil, incident management, capacity planning |
| Platform Engineering | 6 | IDPs, golden paths, self-service, developer experience, SPACE metrics |
| GitOps | 6 | Declarative config, reconciliation, ArgoCD, Flux, progressive delivery |
| DevSecOps | 6 + guide | Shift-left, CI/CD security, supply chain, runtime, security culture |
| MLOps | 6 | Feature stores, model serving, monitoring, Kubeflow, MLflow |
| AIOps | 6 | Anomaly detection, event correlation, observability AI |
| Release Engineering | 5 | Release pipelines, feature flags, canary, blue-green |
| Chaos Engineering | 5 | Failure injection, game days, steady state hypothesis |
| FinOps | 6 | Cloud cost optimization, showback, rightsizing, spot instances |
| Data Engineering | 6 | Streaming, batch, data mesh, Kafka, Spark on K8s |
| Advanced Networking | 6 | DNS at scale, CDN, WAF, BGP, load balancing, zero trust |
| AI/GPU Infrastructure | 6 | GPU scheduling, vGPU, model serving infra, training clusters |
| Engineering Leadership | 6 | Incident command, postmortems, on-call, ADRs, stakeholders |

## SRE Core

**Service Level Hierarchy**: SLI (what you measure) → SLO (target) → SLA (contract). SLA < SLO always.

**Error Budget**: `1 - SLO target`. At 99.9% = 43.2 min/month. Healthy budget → ship fast. Depleted → freeze + fix.

**Four Golden Signals**: Latency, Traffic, Errors, Saturation.

**Toil**: Manual, repetitive, automatable work. Target <50% of SRE time. Measure and eliminate.

## GitOps Core

**Four Principles**: Declarative, versioned, pulled automatically, continuously reconciled.

**Tool Comparison**:
| | ArgoCD | Flux |
|---|---|---|
| UI | Rich web UI | CLI-first |
| Multi-cluster | App-of-apps | Kustomization |
| RBAC | Built-in | K8s native |
| Notifications | Built-in | Controllers |

## DevSecOps Core

**Pipeline Stages**: Source (secrets scan) → Build (SAST, SCA, image scan) → Test (DAST) → Deploy (policy, sign, admit)

**Supply Chain**: SBOM (know ingredients), Sigstore/Cosign (verify origin), SLSA (provenance levels), admission control (enforce at deploy).

**Runtime**: Falco (detect), Tetragon (enforce at kernel), KubeArmor (least privilege), NetworkPolicies (segment).

## Platform Engineering Core

**IDP Layers**: Infrastructure (Crossplane, Terraform) → Platform (K8s, service mesh) → Developer (Backstage, golden paths)

**Maturity Levels**: L1 (ad-hoc) → L2 (standardized) → L3 (self-service) → L4 (optimized) → L5 (innovation)

**SPACE Framework**: Satisfaction, Performance, Activity, Communication, Efficiency.

## MLOps Core

**ML Lifecycle**: Data → Features → Train → Validate → Serve → Monitor → Retrain

**Drift Types**: Data drift (input distribution), concept drift (relationship changes), prediction drift (output shifts)

**Key Tools**: Kubeflow (pipelines), MLflow (tracking), Feast (features), KServe (serving), Evidently (monitoring)

## Toolkits (17 categories, 96 modules)

| Category | Key Tools |
|----------|-----------|
| Observability | Prometheus, OpenTelemetry, Grafana, Loki, Jaeger |
| GitOps & Deploy | ArgoCD, Argo Rollouts, Flux, Helm/Kustomize |
| CI/CD | Dagger, Tekton, Argo Workflows |
| Security | Vault+ESO, OPA, Falco, Tetragon, KubeArmor, Supply Chain |
| Networking | Cilium, Service Mesh (Istio) |
| Scaling | Karpenter, KEDA, Velero |
| Platforms | Backstage, Crossplane, cert-manager |
| Developer Exp | k9s, Telepresence, DevPod, Gitpod |
| ML Platforms | Kubeflow, MLflow, Feast, vLLM, Ray Serve |
| Code Quality | SonarQube, Semgrep, CodeQL, Snyk, Trivy |
| Storage | Rook/Ceph, MinIO, Longhorn |
| K8s Distros | k3s, k0s, MicroK8s, Talos, OpenShift |
| IaC | Terraform, OpenTofu, Pulumi, Ansible, CloudFormation, Bicep |

## KubeDojo Module Counts

| Section | Modules | Path |
|---------|---------|------|
| Foundations | 32 | docs/platform/foundations/ |
| Disciplines | 71 | docs/platform/disciplines/ |
| Toolkits | 96 | docs/platform/toolkits/ |
| **Total** | **199** | |
