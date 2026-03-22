# CNPA - Certified Cloud Native Platform Engineering Associate

> **Multiple-choice exam** | 120 minutes | Passing score: 75% | $250 USD

## Overview

The CNPA (Certified Cloud Native Platform Engineering Associate) validates foundational knowledge of platform engineering concepts, practices, and tooling in the cloud native ecosystem. It's a **multiple-choice exam** — you need to understand concepts, not configure live clusters.

**KubeDojo covers ~80%+ of CNPA topics** through our existing Platform Engineering track. This page maps CNPA domains to existing modules so you can prepare efficiently.

> **CNPA is the associate-level companion to CNPE.** If CNPE is "prove you can build a platform," CNPA is "prove you understand what a platform is and why it matters." Pass CNPA first, then level up to the hands-on CNPE.

---

## Exam Domains

| Domain | Weight | KubeDojo Coverage |
|--------|--------|-------------------|
| Platform Engineering Core Fundamentals | 36% | Excellent (6 discipline + 6 GitOps + 7 toolkit modules) |
| Platform Observability, Security & Conformance | 20% | Excellent (4 foundation + 5 discipline + 10 toolkit modules) |
| Continuous Delivery & Platform Engineering | 16% | Excellent (6 discipline + 7 toolkit modules) |
| Platform APIs and Provisioning Infrastructure | 12% | Excellent (6 discipline + 5 toolkit modules) |
| IDPs and Developer Experience | 8% | Excellent (6 discipline + 6 toolkit modules) |
| Measuring Your Platform | 8% | Good (7 SRE discipline + 2 toolkit modules) |

---

## Domain 1: Platform Engineering Core Fundamentals (36%)

### Competencies
- Declarative resource management
- DevOps principles and culture
- Application environments and lifecycle
- Platform architecture concepts
- Continuous Integration and Continuous Delivery
- GitOps fundamentals

### KubeDojo Learning Path

**Platform Engineering (start here):**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Platform Eng 2.1](../../platform/disciplines/platform-engineering/module-2.1-what-is-platform-engineering.md) | What is Platform Engineering? | Direct |
| [Platform Eng 2.2](../../platform/disciplines/platform-engineering/module-2.2-developer-experience.md) | Developer Experience (DevEx) | Direct |
| [Platform Eng 2.3](../../platform/disciplines/platform-engineering/module-2.3-internal-developer-platforms.md) | Internal Developer Platforms | Direct |
| [Platform Eng 2.4](../../platform/disciplines/platform-engineering/module-2.4-golden-paths.md) | Golden Paths and paved roads | Direct |
| [Platform Eng 2.5](../../platform/disciplines/platform-engineering/module-2.5-self-service-infrastructure.md) | Self-Service Infrastructure | Direct |
| [Platform Eng 2.6](../../platform/disciplines/platform-engineering/module-2.6-platform-maturity.md) | Platform Maturity Models | Direct |

**GitOps:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [GitOps 3.1](../../platform/disciplines/gitops/module-3.1-what-is-gitops.md) | What is GitOps? OpenGitOps 4 principles | Direct |
| [GitOps 3.2](../../platform/disciplines/gitops/module-3.2-repository-strategies.md) | Repository strategies, mono vs multi-repo | Direct |
| [GitOps 3.3](../../platform/disciplines/gitops/module-3.3-environment-promotion.md) | Environment promotion patterns | Direct |
| [GitOps 3.4](../../platform/disciplines/gitops/module-3.4-drift-detection.md) | Drift detection and reconciliation | Direct |
| [GitOps 3.5](../../platform/disciplines/gitops/module-3.5-secrets.md) | Secrets management in GitOps | Direct |
| [GitOps 3.6](../../platform/disciplines/gitops/module-3.6-multi-cluster.md) | Multi-cluster GitOps | Direct |

**Architecture & IaC:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Distributed Systems 5.1](../../platform/foundations/distributed-systems/module-5.1-what-makes-systems-distributed.md) | Distributed systems fundamentals | Direct |
| [IaC 6.1](../../platform/disciplines/iac/module-6.1-iac-fundamentals.md) | Infrastructure as Code fundamentals | Direct |
| [Systems Thinking 1.1](../../platform/foundations/systems-thinking/module-1.1-what-is-systems-thinking.md) | Systems thinking for platform design | Partial |

**Tools (conceptual understanding):**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [ArgoCD](../../platform/toolkits/gitops-deployments/module-2.1-argocd.md) | ArgoCD: GitOps delivery | Direct |
| [Flux](../../platform/toolkits/gitops-deployments/module-2.3-flux.md) | Flux CD: GitOps controllers | Direct |
| [Helm & Kustomize](../../platform/toolkits/gitops-deployments/module-2.4-helm-kustomize.md) | Declarative packaging and customization | Direct |
| [Dagger](../../platform/toolkits/ci-cd-pipelines/module-3.1-dagger.md) | CI/CD pipeline design | Direct |
| [Tekton](../../platform/toolkits/ci-cd-pipelines/module-3.2-tekton.md) | K8s-native CI/CD pipelines | Direct |
| [Argo Workflows](../../platform/toolkits/ci-cd-pipelines/module-3.3-argo-workflows.md) | Workflow automation | Direct |
| [Argo Rollouts](../../platform/toolkits/gitops-deployments/module-2.2-argo-rollouts.md) | Progressive delivery: canary, blue-green | Direct |

---

## Domain 2: Platform Observability, Security & Conformance (20%)

### Competencies
- Observability fundamentals (metrics, logs, traces)
- Secure communication patterns
- Policy engines and admission controllers
- Kubernetes security concepts
- CI/CD pipeline security

### KubeDojo Learning Path

**Observability Theory:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Observability 3.1](../../platform/foundations/observability-theory/module-3.1-what-is-observability.md) | What is Observability? | Direct |
| [Observability 3.2](../../platform/foundations/observability-theory/module-3.2-the-three-pillars.md) | Metrics, Logs, Traces | Direct |
| [Observability 3.3](../../platform/foundations/observability-theory/module-3.3-instrumentation-principles.md) | Instrumentation principles | Direct |
| [Observability 3.4](../../platform/foundations/observability-theory/module-3.4-from-data-to-insight.md) | From data to insight | Direct |

**Security:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Security 4.1](../../platform/foundations/security-principles/module-4.1-security-mindset.md) | Security mindset | Direct |
| [Security 4.2](../../platform/foundations/security-principles/module-4.2-defense-in-depth.md) | Defense in depth | Direct |
| [Security 4.3](../../platform/foundations/security-principles/module-4.3-identity-and-access.md) | Identity and access management | Direct |
| [DevSecOps 4.1](../../platform/disciplines/devsecops/module-4.1-devsecops-fundamentals.md) | DevSecOps fundamentals | Direct |
| [DevSecOps 4.3](../../platform/disciplines/devsecops/module-4.3-security-cicd.md) | Security in CI/CD | Direct |

**Tools (know what they do):**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Prometheus](../../platform/toolkits/observability/module-1.1-prometheus.md) | Pull-based monitoring, PromQL | Direct |
| [OpenTelemetry](../../platform/toolkits/observability/module-1.2-opentelemetry.md) | OTel Collector, auto-instrumentation | Direct |
| [Grafana](../../platform/toolkits/observability/module-1.3-grafana.md) | Dashboards, data sources | Direct |
| [Loki](../../platform/toolkits/observability/module-1.4-loki.md) | Log aggregation, LogQL | Direct |
| [Tracing](../../platform/toolkits/observability/module-1.5-tracing.md) | Jaeger/Tempo, context propagation | Direct |
| [OPA/Gatekeeper](../../platform/toolkits/security-tools/module-4.2-opa-gatekeeper.md) | Policy engine, admission control | Direct |
| [Kyverno](../../platform/toolkits/security-tools/module-4.7-kyverno.md) | YAML-native policy engine | Direct |
| [SPIFFE/SPIRE](../../platform/toolkits/security-tools/module-4.8-spiffe-spire.md) | Workload identity, mTLS | Direct |
| [Service Mesh](../../platform/toolkits/networking/module-5.2-service-mesh.md) | Istio/Linkerd mTLS | Direct |
| [CKA RBAC](../../k8s/cka/part1-cluster-architecture/module-1.6-rbac.md) | RBAC fundamentals | Direct |

---

## Domain 3: Continuous Delivery & Platform Engineering (16%)

### Competencies
- CI pipeline concepts and design
- Incident response and management
- GitOps basics and workflows

### KubeDojo Learning Path

**Theory:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [GitOps 3.1](../../platform/disciplines/gitops/module-3.1-what-is-gitops.md) | What is GitOps? OpenGitOps principles | Direct |
| [GitOps 3.3](../../platform/disciplines/gitops/module-3.3-environment-promotion.md) | Environment promotion patterns | Direct |
| [GitOps 3.4](../../platform/disciplines/gitops/module-3.4-drift-detection.md) | Drift detection and reconciliation | Direct |
| [SRE 1.5](../../platform/disciplines/sre/module-1.5-incident-management.md) | Incident Management | Direct |
| [SRE 1.6](../../platform/disciplines/sre/module-1.6-postmortems.md) | Blameless Postmortems | Direct |
| [DevSecOps 4.2](../../platform/disciplines/devsecops/module-4.2-shift-left-security.md) | Shift-left (CI integration) | Partial |

**Tools:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [ArgoCD](../../platform/toolkits/gitops-deployments/module-2.1-argocd.md) | ArgoCD: Application CRD, sync, RBAC | Direct |
| [Flux](../../platform/toolkits/gitops-deployments/module-2.3-flux.md) | Flux CD: GitRepository, HelmRelease | Direct |
| [Argo Rollouts](../../platform/toolkits/gitops-deployments/module-2.2-argo-rollouts.md) | Progressive delivery strategies | Direct |
| [Dagger](../../platform/toolkits/ci-cd-pipelines/module-3.1-dagger.md) | CI/CD pipeline design | Direct |
| [Tekton](../../platform/toolkits/ci-cd-pipelines/module-3.2-tekton.md) | K8s-native CI/CD pipelines | Direct |
| [Argo Workflows](../../platform/toolkits/ci-cd-pipelines/module-3.3-argo-workflows.md) | Workflow automation | Direct |
| [Supply Chain](../../platform/toolkits/security-tools/module-4.4-supply-chain.md) | Sigstore/Cosign, image signing | Partial |

---

## Domain 4: Platform APIs and Provisioning Infrastructure (12%)

### Competencies
- Reconciliation loop pattern
- Custom Resource Definitions (CRDs)
- Infrastructure provisioning as code
- Kubernetes Operators

### KubeDojo Learning Path

**Theory:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Platform Eng 2.5](../../platform/disciplines/platform-engineering/module-2.5-self-service-infrastructure.md) | Self-Service Infrastructure | Direct |
| [IaC 6.1](../../platform/disciplines/iac/module-6.1-iac-fundamentals.md) | Infrastructure as Code | Direct |
| [IaC 6.4](../../platform/disciplines/iac/module-6.4-iac-at-scale.md) | IaC at Scale | Direct |
| [Distributed Systems 5.2](../../platform/foundations/distributed-systems/module-5.2-consensus-and-coordination.md) | Consensus and coordination (reconciliation) | Partial |
| [CKA CRDs](../../k8s/cka/part1-cluster-architecture/module-1.5-crds-operators.md) | CRD creation and operator pattern | Direct |
| [CKA Extension Interfaces](../../k8s/cka/part1-cluster-architecture/module-1.2-extension-interfaces.md) | K8s extension points | Direct |

**Tools:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Crossplane](../../platform/toolkits/platforms/module-7.2-crossplane.md) | XRDs, Compositions, Providers | Direct |
| [Kubebuilder](../../platform/toolkits/platforms/module-3.4-kubebuilder.md) | Building custom operators | Direct |
| [Cluster API](../../platform/toolkits/platforms/module-3.5-cluster-api.md) | Declarative cluster lifecycle | Direct |
| [Helm & Kustomize](../../platform/toolkits/gitops-deployments/module-2.4-helm-kustomize.md) | Declarative resource packaging | Partial |
| [vCluster](../../platform/toolkits/platforms/module-3.6-vcluster.md) | Virtual clusters for provisioning | Partial |

---

## Domain 5: IDPs and Developer Experience (8%)

### Competencies
- Service catalogs and software templates
- Developer portals
- AI/ML in platform automation

### KubeDojo Learning Path

**Theory:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Platform Eng 2.2](../../platform/disciplines/platform-engineering/module-2.2-developer-experience.md) | Developer Experience (DevEx) | Direct |
| [Platform Eng 2.3](../../platform/disciplines/platform-engineering/module-2.3-internal-developer-platforms.md) | Internal Developer Platforms | Direct |
| [Platform Eng 2.4](../../platform/disciplines/platform-engineering/module-2.4-golden-paths.md) | Golden Paths and templates | Direct |
| [Platform Eng 2.6](../../platform/disciplines/platform-engineering/module-2.6-platform-maturity.md) | Platform Maturity Models | Direct |
| [AIOps 6.1](../../platform/disciplines/aiops/module-6.1-aiops-foundations.md) | AIOps foundations | Direct |
| [AIOps 6.6](../../platform/disciplines/aiops/module-6.6-auto-remediation.md) | Auto-remediation with AI | Partial |

**Tools:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Backstage](../../platform/toolkits/platforms/module-7.1-backstage.md) | Software Catalog, Templates, TechDocs | Direct |
| [K9s CLI](../../platform/toolkits/developer-experience/module-8.1-k9s-cli.md) | Developer CLI tooling | Partial |
| [Telepresence/Tilt](../../platform/toolkits/developer-experience/module-8.2-telepresence-tilt.md) | Inner-loop development | Partial |
| [DevPod](../../platform/toolkits/developer-experience/module-8.4-devpod.md) | Reproducible dev environments | Partial |
| [Gitpod/Codespaces](../../platform/toolkits/developer-experience/module-8.5-gitpod-codespaces.md) | Cloud development environments | Partial |
| [AIOps Tools](../../platform/toolkits/aiops-tools/module-10.3-observability-ai-features.md) | AI-powered observability features | Partial |

---

## Domain 6: Measuring Your Platform (8%)

### Competencies
- DORA metrics (deployment frequency, lead time, MTTR, change failure rate)
- Platform efficiency and adoption metrics
- SLOs and error budgets for platforms

### KubeDojo Learning Path

**Theory:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [SRE 1.2](../../platform/disciplines/sre/module-1.2-slos.md) | SLOs (SLIs, SLAs) | Direct |
| [SRE 1.3](../../platform/disciplines/sre/module-1.3-error-budgets.md) | Error Budgets and burn rates | Direct |
| [SRE 1.4](../../platform/disciplines/sre/module-1.4-toil-automation.md) | Toil and automation metrics | Direct |
| [SRE 1.7](../../platform/disciplines/sre/module-1.7-capacity-planning.md) | Capacity Planning | Partial |
| [Platform Eng 2.6](../../platform/disciplines/platform-engineering/module-2.6-platform-maturity.md) | Platform Maturity Models | Direct |
| [Reliability 2.4](../../platform/foundations/reliability-engineering/module-2.4-measuring-and-improving-reliability.md) | Measuring reliability | Direct |
| [Reliability 2.5](../../platform/foundations/reliability-engineering/module-2.5-slos-slis-error-budgets.md) | SLOs, SLIs, error budgets (theory) | Direct |

**Tools:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [SLO Tooling](../../platform/toolkits/observability/module-1.10-slo-tooling.md) | Sloth, Pyrra, error budget dashboards | Direct |
| [FinOps](../../platform/toolkits/scaling-reliability/module-6.4-finops-opencost.md) | OpenCost, cost allocation, efficiency | Direct |

---

## Study Strategy

```
CNPA PREPARATION PATH (recommended order)
══════════════════════════════════════════════════════════════

Week 1-2: Core Fundamentals (36% of exam!)
├── Platform Engineering discipline (6 modules)
├── GitOps discipline (6 modules)
├── IaC 6.1 (Infrastructure as Code basics)
└── Distributed Systems 5.1 (architecture concepts)

Week 3: Observability, Security & Conformance (20%)
├── Observability Theory foundation (4 modules)
├── Security Principles foundation (4 modules)
├── DevSecOps 4.1 + 4.3 (fundamentals + CI/CD security)
└── Know your tools: Prometheus, OTel, OPA, Kyverno

Week 4: Continuous Delivery (16%)
├── Review GitOps discipline modules (from Week 1)
├── SRE 1.5 + 1.6 (incident response + postmortems)
├── CI/CD pipeline tools: Dagger, Tekton, Argo Workflows
└── ArgoCD + Flux (conceptual understanding)

Week 5: Platform APIs & IDPs (12% + 8%)
├── CKA CRDs/Operators module (reconciliation loop)
├── Crossplane + Kubebuilder (conceptual)
├── Backstage (service catalogs, developer portals)
└── AIOps 6.1 (AI/ML in automation)

Week 6: Measuring & Review (8% + exam prep)
├── SRE modules: SLOs, error budgets, toil
├── DORA metrics concepts (review Platform Eng 2.6)
├── FinOps / OpenCost (platform efficiency)
└── Full domain review, focus on 36% core fundamentals
```

---

## Exam Tips

- **This is a multiple-choice exam** — focus on conceptual understanding, not hands-on configuration
- **Core Fundamentals = 36% of the exam** — nail platform engineering concepts, GitOps, and DevOps principles first
- **Know the "why" not just the "what"** — understand why GitOps uses pull-based reconciliation, why platforms need golden paths, etc.
- **DORA metrics come up everywhere** — know the four key metrics and what they measure
- **GitOps principles** — memorize the OpenGitOps four principles (declarative, versioned, automated, reconciled)
- **Policy engines** — understand OPA vs Kyverno at a conceptual level (when to use each)
- **Time management**: 120 minutes for multiple-choice is generous. Read questions carefully, flag uncertain ones, review at the end.

---

## Gap Analysis

Our Platform Engineering track covers ~80%+ of the CNPA curriculum. Remaining minor gaps:

| Topic | Status | Notes |
|-------|--------|-------|
| DORA metrics implementation | Minor gap | SRE modules cover SLOs/error budgets; DORA metrics (deployment frequency, lead time, MTTR, change failure rate) discussed conceptually but no dedicated DORA module |
| DevOps culture & history | Minor gap | Platform Eng modules assume DevOps context; KCNA cloud-native modules provide additional background |
| Application environment lifecycle | Covered | Spread across GitOps environment promotion and IaC modules |

These gaps are minor. The 50+ modules mapped above provide comprehensive CNPA preparation.

---

## Related Certifications

```
CERTIFICATION PATH
══════════════════════════════════════════════════════════════

Entry Level:
├── KCNA (Cloud Native Associate) — K8s fundamentals
├── KCSA (Security Associate) — Security fundamentals
└── CNPA (Platform Engineering Associate) ← YOU ARE HERE

Professional Level:
├── CKA (K8s Administrator) — Cluster operations
├── CKAD (K8s Developer) — Application deployment
├── CKS (K8s Security Specialist) — Security hardening
└── CNPE (Platform Engineer) — Hands-on platform engineering

Specialist (Coming):
└── CKNE (K8s Network Engineer) — Advanced networking
```

The CNPA is the natural stepping stone to CNPE. CNPA tests your conceptual understanding of platform engineering; CNPE tests your ability to build and operate platforms hands-on. If you pass CNPA, continue with KubeDojo's platform toolkit modules to build hands-on skills for CNPE.
