# CNPE - Certified Cloud Native Platform Engineer

> **Performance-based exam** | 120 minutes | Passing score: TBD | $445 USD | **Launched November 2025**

## Overview

The CNPE (Certified Cloud Native Platform Engineer) validates skills in designing, building, and operating Internal Developer Platforms on Kubernetes. It's a **hands-on exam** — you'll configure real infrastructure, not answer multiple-choice questions.

**KubeDojo covers ~90% of CNPE topics** through our existing Platform Engineering track. This page maps CNPE domains to existing modules so you can prepare efficiently.

> **Unlike other certifications**, CNPE is NOT K8s-version-specific. It tests platform engineering practices, not raw kubectl skills. Think of it as "CKA for platform teams."

---

## Exam Domains

| Domain | Weight | KubeDojo Coverage |
|--------|--------|-------------------|
| GitOps & Continuous Delivery | 25% | Excellent (6 discipline + 7 toolkit modules) |
| Platform APIs & Self-Service | 25% | Excellent (6 discipline + 4 toolkit modules) |
| Observability & Operations | 20% | Excellent (4 foundation + 7 discipline + 10 toolkit modules) |
| Platform Architecture | 15% | Excellent (7 foundation + 3 discipline modules) |
| Security & Policy | 15% | Excellent (4 foundation + 6 discipline + 6 toolkit modules) |

---

## Domain 1: GitOps & Continuous Delivery (25%)

### Competencies
- Implementing GitOps workflows for application and infrastructure deployment
- Building and configuring CI/CD pipelines integrated with Kubernetes
- Deploying applications using progressive delivery strategies (blue/green, canary)

### KubeDojo Learning Path

**Theory (start here):**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [GitOps 3.1](../../platform/disciplines/gitops/module-3.1-what-is-gitops.md) | What is GitOps? OpenGitOps 4 principles | Direct |
| [GitOps 3.2](../../platform/disciplines/gitops/module-3.2-repository-strategies.md) | Repository strategies, mono vs multi-repo | Direct |
| [GitOps 3.3](../../platform/disciplines/gitops/module-3.3-environment-promotion.md) | Environment promotion patterns | Direct |
| [GitOps 3.4](../../platform/disciplines/gitops/module-3.4-drift-detection.md) | Drift detection and reconciliation | Direct |
| [GitOps 3.5](../../platform/disciplines/gitops/module-3.5-secrets.md) | Secrets management in GitOps | Direct |
| [GitOps 3.6](../../platform/disciplines/gitops/module-3.6-multi-cluster.md) | Multi-cluster GitOps | Direct |

**Tools (hands-on):**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [ArgoCD](../../platform/toolkits/gitops-deployments/module-2.1-argocd.md) | ArgoCD: Application CRD, sync, RBAC, ApplicationSet | Direct |
| [Argo Rollouts](../../platform/toolkits/gitops-deployments/module-2.2-argo-rollouts.md) | Progressive delivery: canary, blue-green, analysis | Direct |
| [Flux](../../platform/toolkits/gitops-deployments/module-2.3-flux.md) | Flux CD: 5 controllers, GitRepository, HelmRelease | Direct |
| [Helm & Kustomize](../../platform/toolkits/gitops-deployments/module-2.4-helm-kustomize.md) | Packaging and customization | Direct |
| [Dagger](../../platform/toolkits/ci-cd-pipelines/module-3.1-dagger.md) | CI/CD pipeline design | Direct |
| [Tekton](../../platform/toolkits/ci-cd-pipelines/module-3.2-tekton.md) | K8s-native CI/CD pipelines | Direct |
| [Argo Workflows](../../platform/toolkits/ci-cd-pipelines/module-3.3-argo-workflows.md) | Workflow automation | Direct |

---

## Domain 2: Platform APIs & Self-Service (25%)

### Competencies
- Designing and creating CRDs for platform services
- Implementing self-service provisioning using platform APIs
- Using Kubernetes Operators for platform automation
- Using automation frameworks for self-service provisioning

### KubeDojo Learning Path

**Theory:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Platform Eng 2.1](../../platform/disciplines/platform-engineering/module-2.1-what-is-platform-engineering.md) | What is Platform Engineering? | Direct |
| [Platform Eng 2.2](../../platform/disciplines/platform-engineering/module-2.2-developer-experience.md) | Developer Experience (DevEx) | Direct |
| [Platform Eng 2.3](../../platform/disciplines/platform-engineering/module-2.3-internal-developer-platforms.md) | Internal Developer Platforms | Direct |
| [Platform Eng 2.4](../../platform/disciplines/platform-engineering/module-2.4-golden-paths.md) | Golden Paths and paved roads | Direct |
| [Platform Eng 2.5](../../platform/disciplines/platform-engineering/module-2.5-self-service-infrastructure.md) | Self-Service Infrastructure | Direct |
| [Platform Eng 2.6](../../platform/disciplines/platform-engineering/module-2.6-platform-maturity.md) | Platform Maturity Models | Direct |

**Tools:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Backstage](../../platform/toolkits/platforms/module-7.1-backstage.md) | Software Catalog, Templates, TechDocs | Direct |
| [Crossplane](../../platform/toolkits/platforms/module-7.2-crossplane.md) | XRDs, Compositions, Providers | Direct |
| [Kubebuilder](../../platform/toolkits/platforms/module-3.4-kubebuilder.md) | Building custom operators | Direct |
| [Cluster API](../../platform/toolkits/platforms/module-3.5-cluster-api.md) | Declarative cluster lifecycle | Direct |
| [vCluster](../../platform/toolkits/platforms/module-3.6-vcluster.md) | Virtual clusters for self-service | Direct |
| [CKA CRDs](../../k8s/cka/part1-cluster-architecture/module-1.5-crds-operators.md) | CRD creation and operator pattern | Direct |

---

## Domain 3: Observability & Operations (20%)

### Competencies
- Implementing monitoring, alerting, logging, and tracing solutions
- Measuring platform efficiency using deployment metrics (DORA)
- Diagnosing and remediating platform issues

### KubeDojo Learning Path

**Theory:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Observability 3.1](../../platform/foundations/observability-theory/module-3.1-what-is-observability.md) | What is Observability? | Direct |
| [Observability 3.2](../../platform/foundations/observability-theory/module-3.2-the-three-pillars.md) | Metrics, Logs, Traces | Direct |
| [Observability 3.3](../../platform/foundations/observability-theory/module-3.3-instrumentation-principles.md) | Instrumentation principles | Direct |
| [SRE 1.1](../../platform/disciplines/sre/module-1.1-what-is-sre.md) | What is SRE? | Direct |
| [SRE 1.2](../../platform/disciplines/sre/module-1.2-slos.md) | SLOs (SLIs, SLAs) | Direct |
| [SRE 1.3](../../platform/disciplines/sre/module-1.3-error-budgets.md) | Error Budgets and burn rates | Direct |
| [SRE 1.5](../../platform/disciplines/sre/module-1.5-incident-management.md) | Incident Management | Direct |

**Tools:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Prometheus](../../platform/toolkits/observability/module-1.1-prometheus.md) | Pull-based monitoring, PromQL, ServiceMonitor | Direct |
| [OpenTelemetry](../../platform/toolkits/observability/module-1.2-opentelemetry.md) | OTel Collector, auto-instrumentation | Direct |
| [Grafana](../../platform/toolkits/observability/module-1.3-grafana.md) | Dashboards, data sources, provisioning | Direct |
| [Loki](../../platform/toolkits/observability/module-1.4-loki.md) | Log aggregation, LogQL | Direct |
| [Tracing](../../platform/toolkits/observability/module-1.5-tracing.md) | Jaeger/Tempo, context propagation | Direct |
| [SLO Tooling](../../platform/toolkits/observability/module-1.10-slo-tooling.md) | Sloth, Pyrra, error budget dashboards | Direct |
| [Continuous Profiling](../../platform/toolkits/observability/module-1.9-continuous-profiling.md) | Parca, Pyroscope (4th pillar) | Partial |
| [FinOps](../../platform/toolkits/scaling-reliability/module-6.4-finops-opencost.md) | OpenCost, cost allocation, right-sizing | Direct |

---

## Domain 4: Platform Architecture (15%)

### Competencies
- Applying best practices for networking, storage, and compute
- Using cost management solutions for right-sizing and scaling
- Optimizing multi-tenancy resource usage

### KubeDojo Learning Path

**Theory:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Systems Thinking 1.1](../../platform/foundations/systems-thinking/module-1.1-what-is-systems-thinking.md) | Systems thinking for architects | Partial |
| [Distributed Systems 5.1](../../platform/foundations/distributed-systems/module-5.1-what-makes-systems-distributed.md) | Distributed systems fundamentals | Direct |
| [Distributed Systems 5.2](../../platform/foundations/distributed-systems/module-5.2-consensus-and-coordination.md) | Consensus and coordination | Direct |
| [Reliability 2.3](../../platform/foundations/reliability-engineering/module-2.3-redundancy-and-fault-tolerance.md) | Redundancy and fault tolerance | Direct |
| [IaC 6.1](../../platform/disciplines/iac/module-6.1-iac-fundamentals.md) | Infrastructure as Code | Direct |
| [IaC 6.4](../../platform/disciplines/iac/module-6.4-iac-at-scale.md) | IaC at Scale | Direct |

**Tools:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Karpenter](../../platform/toolkits/scaling-reliability/module-6.1-karpenter.md) | Autoscaling, right-sizing | Direct |
| [KEDA](../../platform/toolkits/scaling-reliability/module-6.2-keda.md) | Event-driven autoscaling | Direct |
| [FinOps](../../platform/toolkits/scaling-reliability/module-6.4-finops-opencost.md) | Cost management, OpenCost | Direct |
| [vCluster](../../platform/toolkits/platforms/module-3.6-vcluster.md) | Multi-tenancy with virtual clusters | Direct |
| [Cilium](../../platform/toolkits/networking/module-5.1-cilium.md) | eBPF networking, policies | Direct |

---

## Domain 5: Security & Policy (15%)

### Competencies
- Configuring secure service-to-service communication
- Applying RBAC and security controls
- Generating audit trails and enforcing compliance (SBOM)
- Using policy engines and admission controllers
- Integrating security scanning into pipelines

### KubeDojo Learning Path

**Theory:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Security 4.1](../../platform/foundations/security-principles/module-4.1-security-mindset.md) | Security mindset | Direct |
| [Security 4.2](../../platform/foundations/security-principles/module-4.2-defense-in-depth.md) | Defense in depth | Direct |
| [DevSecOps 4.1](../../platform/disciplines/devsecops/module-4.1-devsecops-fundamentals.md) | DevSecOps fundamentals | Direct |
| [DevSecOps 4.2](../../platform/disciplines/devsecops/module-4.2-shift-left-security.md) | Shift-left security | Direct |
| [DevSecOps 4.3](../../platform/disciplines/devsecops/module-4.3-security-cicd.md) | Security in CI/CD | Direct |
| [DevSecOps 4.4](../../platform/disciplines/devsecops/module-4.4-supply-chain-security.md) | Supply chain security, SBOM | Direct |
| [DevSecOps 4.5](../../platform/disciplines/devsecops/module-4.5-runtime-security.md) | Runtime security | Direct |

**Tools:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [OPA/Gatekeeper](../../platform/toolkits/security-tools/module-4.2-opa-gatekeeper.md) | Policy engine (Rego), admission control | Direct |
| [Kyverno](../../platform/toolkits/security-tools/module-4.7-kyverno.md) | YAML-native policy engine | Direct |
| [Falco](../../platform/toolkits/security-tools/module-4.3-falco.md) | Runtime threat detection | Direct |
| [Supply Chain](../../platform/toolkits/security-tools/module-4.4-supply-chain.md) | Sigstore/Cosign, image signing, SBOM | Direct |
| [Vault & ESO](../../platform/toolkits/security-tools/module-4.1-vault-eso.md) | Secrets management | Direct |
| [SPIFFE/SPIRE](../../platform/toolkits/security-tools/module-4.8-spiffe-spire.md) | Workload identity, mTLS | Direct |
| [Service Mesh](../../platform/toolkits/networking/module-5.2-service-mesh.md) | Istio/Linkerd mTLS | Direct |

---

## Study Strategy

```
CNPE PREPARATION PATH (recommended order)
══════════════════════════════════════════════════════════════

Week 1-2: Foundations
├── Platform Engineering discipline (6 modules)
├── Security Principles foundation (4 modules)
└── Observability Theory foundation (4 modules)

Week 3-4: GitOps & CD (25% of exam!)
├── GitOps discipline (6 modules)
├── ArgoCD + Flux toolkit modules
└── Argo Rollouts (progressive delivery)

Week 5-6: Platform APIs & Self-Service (25% of exam!)
├── Backstage + Crossplane toolkit modules
├── CKA CRDs/Operators module
├── Kubebuilder module (build an operator)
└── vCluster for multi-tenancy

Week 7-8: Observability & Operations (20%)
├── SRE discipline (SLOs, error budgets, incidents)
├── Prometheus + OTel + Grafana + Loki toolkit
├── SLO Tooling (Sloth/Pyrra)
└── FinOps / OpenCost

Week 9-10: Security & Policy (15%)
├── DevSecOps discipline (5 modules)
├── OPA/Gatekeeper + Kyverno
├── Supply chain security (Sigstore/SBOM)
└── SPIFFE/SPIRE + Service Mesh mTLS

Week 11-12: Architecture & Practice (15%)
├── Distributed Systems foundation
├── Karpenter + KEDA (autoscaling)
├── Chaos Engineering (resilience testing)
└── Mock exercises, killer.sh equivalent
```

---

## Exam Tips

- **This is a hands-on exam** — you'll configure real clusters, not answer theory questions
- **Focus on ArgoCD and Crossplane** — they're the most heavily tested tools (GitOps + Self-Service = 50% of exam)
- **Know your CRDs** — designing and creating CRDs is a core skill
- **Practice PromQL** — you'll need to write queries and create alerts
- **RBAC + OPA/Kyverno policies** — security is tested with real policy enforcement scenarios
- **Time management**: 120 minutes for ~15-20 tasks. Budget ~6-8 minutes per task.

---

## Gap Analysis

Our Platform Engineering track covers ~95%+ of the CNPE curriculum. Remaining minor gaps:

| Topic | Status | Notes |
|-------|--------|-------|
| Argo Events (event-driven automation) | Covered | See [Argo Events](../capa/module-2-argo-events.md) in the CAPA track — EventSource, Sensor, EventBus, Triggers |
| DORA metrics implementation | Covered | DORA metrics now covered in the SRE discipline modules; SLOs and error budgets provide the measurement framework |
| Hierarchical Namespaces | Minor gap (niche topic) | Niche multi-tenancy topic, unlikely to be exam-critical; vCluster module covers multi-tenancy alternatives |

These gaps are minor. The 60+ modules mapped above provide comprehensive CNPE preparation.

---

## Related Certifications

```
CERTIFICATION PATH
══════════════════════════════════════════════════════════════

Entry Level:
├── KCNA (Cloud Native Associate) — K8s fundamentals
├── KCSA (Security Associate) — Security fundamentals
└── CNPA (Platform Engineering Associate) — Platform basics

Professional Level:
├── CKA (K8s Administrator) — Cluster operations
├── CKAD (K8s Developer) — Application deployment
├── CKS (K8s Security Specialist) — Security hardening
└── CNPE (Platform Engineer) ← YOU ARE HERE

Specialist (Coming):
└── CKNE (K8s Network Engineer) — Advanced networking
```

The CNPE complements CKA/CKS by testing platform-level skills rather than cluster-level operations. If you've completed KubeDojo's CKA + Platform Engineering tracks, you're well-prepared.
