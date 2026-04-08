---
title: "CAPA - Certified Argo Project Associate"
sidebar:
  order: 0
  label: "CAPA"
---
> **Multiple-choice exam** | 90 minutes | Passing score: 75% | $250 USD | **CNCF Certification**

## Overview

The CAPA (Certified Argo Project Associate) validates knowledge of the four Argo projects: Argo Workflows, Argo CD, Argo Rollouts, and Argo Events. It's a **theory exam** — multiple-choice questions testing your understanding of Argo concepts, architecture, and usage patterns.

**KubeDojo covers ~95% of CAPA topics** through existing Platform Engineering toolkit and discipline modules, plus two dedicated CAPA modules covering advanced Argo Workflows and Argo Events.

> **The Argo project is the second-most popular CNCF graduated project** after Kubernetes itself. Over 300 organizations use Argo in production, including Intuit (its creator), Tesla, Google, Red Hat, and GitHub. Understanding the full Argo ecosystem — not just ArgoCD — is increasingly a baseline skill for Kubernetes platform teams.

---

## Exam Domains

| Domain | Weight | KubeDojo Coverage |
|--------|--------|-------------------|
| Argo Workflows | 36% | Excellent (toolkit module + [Advanced Argo Workflows](module-1.1-advanced-argo-workflows/)) |
| Argo CD | 34% | Excellent (1 toolkit + 6 discipline modules) |
| Argo Rollouts | 18% | Excellent (1 dedicated toolkit module) |
| Argo Events | 12% | Excellent ([Argo Events](module-1.2-argo-events/)) |

---

## CAPA-Specific Modules

These modules cover the areas between KubeDojo's existing Platform Engineering content and the CAPA exam requirements:

| # | Module | Topic | Relevance |
|---|--------|-------|-----------|
| 1 | [Advanced Argo Workflows](module-1.1-advanced-argo-workflows/) | All 7 template types, artifacts, CronWorkflows, memoization, lifecycle hooks | Domain 1 (36%) |
| 2 | [Argo Events](module-1.2-argo-events/) | EventSource, Sensor, Trigger, EventBus architecture, event-driven automation | Domain 4 (12%) |

---

## Domain 1: Argo Workflows (36%)

### Competencies
- Understanding the Workflow CRD and its lifecycle
- Using all 7 template types (container, script, resource, suspend, DAG, steps, HTTP)
- Configuring artifact passing between workflow steps
- Building DAG and steps-based workflow structures
- Scheduling workflows with CronWorkflow
- Using parameters, variables, and workflow-level configurations

### KubeDojo Learning Path

**Core module:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Argo Workflows](../../platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.3-argo-workflows/) | Workflow CRD, DAG/steps, templates, parameters | Direct |
| [Advanced Argo Workflows](module-1.1-advanced-argo-workflows/) | All 7 template types, artifacts, CronWorkflows, retries, memoization | Direct |

### Supplementary Study Topics

The existing Argo Workflows module covers architecture, DAGs, steps, and parameters well. For CAPA, ensure you also study:

| Topic | What to Know | Study Resource |
|-------|-------------|----------------|
| **All 7 template types** | container, script, resource, suspend, DAG, steps, HTTP — when to use each | [Argo Docs: Templates](https://argo-workflows.readthedocs.io/en/latest/workflow-concepts/#template-types) |
| **Artifacts** | S3/GCS/MinIO artifact repos, artifact passing between steps, `inputs.artifacts` / `outputs.artifacts` | [Argo Docs: Artifacts](https://argo-workflows.readthedocs.io/en/latest/walk-through/artifacts/) |
| **CronWorkflow** | Scheduling syntax, concurrency policies, timezone handling | [Argo Docs: CronWorkflows](https://argo-workflows.readthedocs.io/en/latest/cron-workflows/) |
| **WorkflowTemplate** | Reusable templates, `templateRef`, cluster-scoped vs namespace-scoped | [Argo Docs: WorkflowTemplates](https://argo-workflows.readthedocs.io/en/latest/workflow-templates/) |
| **Resource template** | Creating/patching K8s resources from within a workflow | [Argo Docs: Resource Template](https://argo-workflows.readthedocs.io/en/latest/walk-through/kubernetes-resources/) |
| **Retry strategies** | `retryStrategy`, backoff, node/pod failure handling | [Argo Docs: Retries](https://argo-workflows.readthedocs.io/en/latest/retries/) |

### Key Concepts for the Exam

```
ARGO WORKFLOWS - 7 TEMPLATE TYPES
══════════════════════════════════════════════════════════════

container     → Runs a container (most common)
script        → container + inline script (source field)
resource      → Creates/patches K8s resources (like kubectl apply)
suspend       → Pauses workflow, waits for manual approval or duration
dag           → Defines tasks with dependency graph
steps         → Defines sequential/parallel step groups
http          → Makes HTTP requests (added in v3.4)

WORKFLOW LIFECYCLE
══════════════════════════════════════════════════════════════
Pending → Running → Succeeded/Failed/Error

ARTIFACT FLOW
══════════════════════════════════════════════════════════════
Step A (outputs.artifacts.data) → Artifact Repo (S3/MinIO) → Step B (inputs.artifacts.data)
```

---

## Domain 2: Argo CD (34%)

### Competencies
- Understanding the Application CRD and its sync lifecycle
- Configuring sync policies (auto-sync, self-heal, prune)
- Using ApplicationSet for multi-cluster/multi-tenant deployment
- Implementing the App-of-Apps pattern
- Configuring RBAC with projects and roles
- Managing multi-cluster deployments with Argo CD

### KubeDojo Learning Path

**Theory (start here):**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [GitOps 3.1](../../platform/disciplines/delivery-automation/gitops/module-3.1-what-is-gitops/) | What is GitOps? OpenGitOps 4 principles | Direct |
| [GitOps 3.2](../../platform/disciplines/delivery-automation/gitops/module-3.2-repository-strategies/) | Repository strategies, mono vs multi-repo | Direct |
| [GitOps 3.3](../../platform/disciplines/delivery-automation/gitops/module-3.3-environment-promotion/) | Environment promotion patterns | Direct |
| [GitOps 3.4](../../platform/disciplines/delivery-automation/gitops/module-3.4-drift-detection/) | Drift detection and reconciliation | Direct |
| [GitOps 3.5](../../platform/disciplines/delivery-automation/gitops/module-3.5-secrets/) | Secrets management in GitOps | Direct |
| [GitOps 3.6](../../platform/disciplines/delivery-automation/gitops/module-3.6-multi-cluster/) | Multi-cluster GitOps | Direct |

**Tools (hands-on):**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [ArgoCD](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd/) | Application CRD, sync policies, RBAC, ApplicationSet, App-of-Apps | Direct |

### Key Concepts for the Exam

```
ARGO CD APPLICATION CRD
══════════════════════════════════════════════════════════════
apiVersion: argoproj.io/v1alpha1
kind: Application
spec:
  source:       → WHERE to get manifests (Git repo, Helm chart, OCI)
  destination:  → WHERE to deploy (cluster + namespace)
  project:      → RBAC boundary (which sources, destinations, resources allowed)
  syncPolicy:   → HOW to sync (auto/manual, prune, self-heal)

SYNC STATUS vs HEALTH STATUS
══════════════════════════════════════════════════════════════
Sync:   Synced / OutOfSync        (does cluster match Git?)
Health: Healthy / Degraded / Progressing / Missing / Suspended

APPLICATIONSET GENERATORS (know all of them!)
══════════════════════════════════════════════════════════════
list          → Static list of clusters/values
cluster       → Auto-discover registered clusters
git           → Generate apps from directory structure or files
matrix        → Combine two generators (cross product)
merge         → Combine generators with override logic
pull-request  → Generate apps from PRs (preview environments)
scm-provider  → Discover repos from GitHub/GitLab orgs

APP-OF-APPS PATTERN
══════════════════════════════════════════════════════════════
Root Application
├── Application: frontend (→ git/apps/frontend)
├── Application: backend  (→ git/apps/backend)
├── Application: database (→ git/apps/database)
└── Application: monitoring (→ git/apps/monitoring)

One "parent" Application manages child Application manifests.
Bootstrap entire platforms with a single Application.
```

---

## Domain 3: Argo Rollouts (18%)

### Competencies
- Configuring canary and blue-green deployment strategies
- Writing AnalysisTemplates for automated rollback
- Integrating with traffic management providers (Istio, Nginx, ALB)
- Understanding the Rollout CRD lifecycle and promotion flow

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Argo Rollouts](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.2-argo-rollouts/) | Canary, blue-green, analysis templates, traffic management | Direct |

### Key Concepts for the Exam

```
ROLLOUT CRD (replaces Deployment)
══════════════════════════════════════════════════════════════
apiVersion: argoproj.io/v1alpha1
kind: Rollout
spec:
  strategy:
    canary:                    OR    blueGreen:
      steps:                          activeService: active-svc
      - setWeight: 10                 previewService: preview-svc
      - pause: {duration: 5m}        autoPromotionEnabled: false
      - analysis:                     prePromotionAnalysis: ...
          templates: [...]            postPromotionAnalysis: ...

CANARY vs BLUE-GREEN
══════════════════════════════════════════════════════════════
Canary:     Gradual traffic shift (10% → 30% → 60% → 100%)
Blue-Green: Full parallel environment, instant switch

ANALYSIS TEMPLATES
══════════════════════════════════════════════════════════════
AnalysisTemplate     → Namespace-scoped, defines metric queries
ClusterAnalysisTemplate → Cluster-scoped, shared across namespaces
AnalysisRun          → Instance of a template (like Job from CronJob)

Providers: Prometheus, Datadog, NewRelic, Wavefront, CloudWatch, Web (generic)

TRAFFIC MANAGEMENT
══════════════════════════════════════════════════════════════
Without traffic manager: Pod-ratio splitting only
With Istio/Nginx/ALB:   Fine-grained traffic percentage control
```

---

## Domain 4: Argo Events (12%)

### Competencies
- Understanding the EventSource, Sensor, and Trigger architecture
- Configuring event sources (webhook, S3, Kafka, GitHub, cron, etc.)
- Writing Sensors with event filters and dependencies
- Triggering Argo Workflows, K8s resources, or HTTP endpoints from events

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Argo Events](module-1.2-argo-events/) | EventSource, Sensor, EventBus, Trigger architecture, event-driven patterns | Direct |

### Study Resources

| Resource | What It Covers |
|----------|---------------|
| [Argo Events Docs: Concepts](https://argoproj.github.io/argo-events/concepts/architecture/) | Architecture, EventSource, Sensor, EventBus |
| [Argo Events Docs: EventSource](https://argoproj.github.io/argo-events/eventsources/setup/webhook/) | Configuring event sources |
| [Argo Events Docs: Sensors](https://argoproj.github.io/argo-events/sensors/triggers/argo-workflow/) | Trigger configuration, filters, dependencies |
| [Argo Events Quick Start](https://argoproj.github.io/argo-events/quick_start/) | Hands-on setup and first event pipeline |

### Key Concepts for the Exam

```
ARGO EVENTS ARCHITECTURE
══════════════════════════════════════════════════════════════

EventSource → EventBus (NATS/Jetstream/Kafka) → Sensor → Trigger

EventSource:  Connects to external systems, emits events
EventBus:     Transport layer (NATS Streaming by default)
Sensor:       Listens to EventBus, evaluates filters/dependencies
Trigger:      Action to take when sensor conditions are met

EVENT SOURCES (know the common ones)
══════════════════════════════════════════════════════════════
webhook       → HTTP endpoint that receives POST requests
github        → GitHub webhooks (push, PR, release events)
s3            → S3 bucket notifications (new object, delete)
kafka         → Kafka topic consumer
calendar/cron → Time-based events (like CronWorkflow but event-driven)
sns/sqs       → AWS messaging services
resource      → Kubernetes resource changes (watch API)
slack         → Slack messages/commands
amqp          → RabbitMQ messages

SENSOR DEPENDENCIES & FILTERS
══════════════════════════════════════════════════════════════
dependencies:
- name: webhook-dep
  eventSourceName: my-webhook
  eventName: example
  filters:
    data:
    - path: body.action        # Filter on event payload
      type: string
      value: ["opened"]

TRIGGER TYPES
══════════════════════════════════════════════════════════════
Argo Workflow    → Submit a Workflow (most common with Argo)
K8s Object       → Create/update any K8s resource
HTTP             → Call an external HTTP endpoint
AWS Lambda       → Invoke a Lambda function
Slack            → Send a Slack notification
Log              → Log the event (debugging)

COMMON PATTERN: GitHub Push → Argo Workflow
══════════════════════════════════════════════════════════════
EventSource (GitHub webhook)
    ↓ push event
EventBus (NATS)
    ↓
Sensor (filters: branch=main)
    ↓
Trigger (submits Argo Workflow for CI/CD)
```

---

## Study Strategy

```
CAPA PREPARATION PATH (recommended order)
══════════════════════════════════════════════════════════════

Week 1-2: GitOps Foundations + Argo CD (34% of exam!)
├── GitOps discipline modules 3.1-3.6 (theory)
├── ArgoCD toolkit module (hands-on)
├── Focus: Application CRD, sync policies, ApplicationSet
└── Practice: Deploy apps, configure auto-sync, set up RBAC

Week 3-4: Argo Workflows (36% of exam!)
├── Argo Workflows toolkit module (hands-on)
├── Supplement: All 7 template types (see domain 1 resources)
├── Practice: Build DAGs, pass artifacts, use CronWorkflow
└── Deep-dive: WorkflowTemplate, retries, resource templates

Week 5: Argo Rollouts (18%)
├── Argo Rollouts toolkit module (hands-on)
├── Focus: Canary vs blue-green, AnalysisTemplate
└── Practice: Deploy a canary with Prometheus analysis

Week 6: Argo Events (12%) + Review
├── Self-study: Argo Events docs (see domain 4 resources)
├── Practice: Set up webhook → sensor → workflow pipeline
├── Focus: EventSource types, Sensor filters, Trigger types
└── Review all domains, take practice questions
```

---

## Exam Tips

- **This is a theory exam** — no hands-on terminal, but practical experience helps you reason about questions faster
- **Argo Workflows + Argo CD = 70% of the exam** — invest most of your time here
- **Know the CRD fields** — the exam tests whether you understand what each spec field does (e.g., `syncPolicy.automated.selfHeal` vs `syncPolicy.automated.prune`)
- **Template types matter** — expect questions distinguishing between the 7 Argo Workflows template types and when to use each
- **ApplicationSet generators** — know all generator types and their use cases (especially list, cluster, git, matrix)
- **AnalysisTemplate vs ClusterAnalysisTemplate** — understand scope differences and when to use each
- **Argo Events architecture** — even at 12%, expect 5-6 questions on EventSource/Sensor/Trigger flow
- **Kubernetes fundamentals required** — CAPA assumes you know CRDs, RBAC, Services, and ConfigMaps

---

## Gap Analysis

KubeDojo's existing modules plus the two dedicated CAPA modules now cover ~95% of the CAPA curriculum:

| Topic | Domain | Weight Impact | Status | Notes |
|-------|--------|---------------|--------|-------|
| Argo Events | Domain 4 | 12% | Covered | [Argo Events](module-1.2-argo-events/) — EventSource, Sensor, EventBus, Triggers |
| Argo Workflows template types (all 7) | Domain 1 | Part of 36% | Covered | [Advanced Argo Workflows](module-1.1-advanced-argo-workflows/) — all 7 template types |
| Argo Workflows artifacts | Domain 1 | Part of 36% | Covered | [Advanced Argo Workflows](module-1.1-advanced-argo-workflows/) — S3/MinIO artifact configuration |
| CronWorkflow | Domain 1 | Part of 36% | Covered | [Advanced Argo Workflows](module-1.1-advanced-argo-workflows/) — scheduling, concurrency policies |
| Exit handlers / lifecycle hooks | Domain 1 | Part of 36% | Covered | [Advanced Argo Workflows](module-1.1-advanced-argo-workflows/) |
| Synchronization / memoization | Domain 1 | Part of 36% | Covered | [Advanced Argo Workflows](module-1.1-advanced-argo-workflows/) |

All four Argo domains are now fully covered by existing KubeDojo modules.

---

## Related Certifications

```
ARGO & GITOPS CERTIFICATION PATH
══════════════════════════════════════════════════════════════

Associate Level:
├── KCNA (Cloud Native Associate) — K8s fundamentals
└── CAPA (Argo Project Associate) ← YOU ARE HERE

Professional Level:
├── CKA (K8s Administrator) — Cluster operations
├── CKAD (K8s Developer) — Application deployment
└── CNPE (Platform Engineer) — Platform engineering (heavy Argo CD)

Complementary KubeDojo Tracks:
├── GitOps Discipline — Theory behind what Argo implements
├── Platform Engineering — Where Argo fits in the bigger picture
└── DevSecOps — Security in CI/CD (pairs with Argo Workflows)
```

The CAPA validates Argo-specific knowledge while CNPE tests broader platform engineering skills. If you're pursuing both, start with CAPA — the Argo depth transfers directly to CNPE's GitOps domain (25% of that exam).
