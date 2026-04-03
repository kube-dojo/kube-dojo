---
title: "Module 4.1: CI/CD Fundamentals"
slug: k8s/kcna/part4-application-delivery/module-4.1-ci-cd
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Delivery concepts
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: Part 3 (Cloud Native Architecture)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** the difference between Continuous Integration, Continuous Delivery, and Continuous Deployment
2. **Identify** the stages of a typical CI/CD pipeline and what each stage validates
3. **Compare** CI/CD tools (Jenkins, GitHub Actions, GitLab CI, Tekton) by architecture and use case
4. **Evaluate** GitOps as a deployment model and how it differs from traditional push-based CI/CD

---

## Why This Module Matters

Modern software delivery requires automation. **Continuous Integration** and **Continuous Delivery/Deployment** (CI/CD) are foundational practices for getting code from development to production reliably. KCNA tests your understanding of these concepts.

---

## What is CI/CD?

```
┌─────────────────────────────────────────────────────────────┐
│              CI/CD OVERVIEW                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONTINUOUS INTEGRATION (CI)                               │
│  ─────────────────────────────────────────────────────────  │
│  Frequently merge code changes into a shared repository   │
│  Automatically build and test each change                 │
│                                                             │
│  Code → Build → Test → Merge                              │
│                                                             │
│  CONTINUOUS DELIVERY (CD)                                 │
│  ─────────────────────────────────────────────────────────  │
│  Automatically prepare code for release to production     │
│  Deployment is manual (button click)                      │
│                                                             │
│  CI → Package → Stage → [Manual Deploy]                  │
│                                                             │
│  CONTINUOUS DEPLOYMENT (CD)                               │
│  ─────────────────────────────────────────────────────────  │
│  Automatically deploy every change to production         │
│  No manual intervention                                   │
│                                                             │
│  CI → Package → Stage → [Auto Deploy]                    │
│                                                             │
│  The difference:                                          │
│  • Continuous Delivery: CAN deploy at any time           │
│  • Continuous Deployment: DOES deploy automatically      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## CI/CD Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│              CI/CD PIPELINE                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Code                                                      │
│    │                                                       │
│    ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  1. SOURCE                                          │   │
│  │     Developer commits code to Git                   │   │
│  │     Triggers pipeline                               │   │
│  └─────────────────────────────────────────────────────┘   │
│    │                                                       │
│    ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  2. BUILD                                           │   │
│  │     Compile code, resolve dependencies             │   │
│  │     Create container image                          │   │
│  └─────────────────────────────────────────────────────┘   │
│    │                                                       │
│    ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  3. TEST                                            │   │
│  │     Unit tests, integration tests                   │   │
│  │     Security scans, linting                         │   │
│  └─────────────────────────────────────────────────────┘   │
│    │                                                       │
│    ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  4. PACKAGE                                         │   │
│  │     Push container image to registry               │   │
│  │     Create Helm chart/manifests                    │   │
│  └─────────────────────────────────────────────────────┘   │
│    │                                                       │
│    ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  5. DEPLOY                                          │   │
│  │     Deploy to staging/production                    │   │
│  │     Run smoke tests                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│    │                                                       │
│    ▼                                                       │
│  Production                                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## CI/CD Benefits

```
┌─────────────────────────────────────────────────────────────┐
│              CI/CD BENEFITS                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WITHOUT CI/CD:                                            │
│  ─────────────────────────────────────────────────────────  │
│  • Manual builds ("works on my machine")                  │
│  • Infrequent releases (big bang)                        │
│  • Manual testing (error-prone)                          │
│  • Long feedback loops                                    │
│  • Risky deployments                                      │
│                                                             │
│  WITH CI/CD:                                              │
│  ─────────────────────────────────────────────────────────  │
│  • Automated builds (reproducible)                       │
│  • Frequent releases (small changes)                     │
│  • Automated testing (consistent)                        │
│  • Fast feedback (minutes, not days)                     │
│  • Safe deployments (rollback ready)                     │
│                                                             │
│  Key metrics:                                              │
│  ─────────────────────────────────────────────────────────  │
│  • Deployment frequency (how often)                       │
│  • Lead time (commit to production)                       │
│  • Change failure rate (% that cause issues)             │
│  • Mean time to recovery (fix production issues)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## CI/CD Tools

### General CI/CD Platforms

| Tool | Description |
|------|-------------|
| **Jenkins** | Self-hosted, highly customizable |
| **GitHub Actions** | Built into GitHub |
| **GitLab CI** | Built into GitLab |
| **CircleCI** | Cloud-native CI/CD |
| **Travis CI** | Simple CI/CD |

### Kubernetes-Native CI/CD

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES-NATIVE CI/CD                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TEKTON (CNCF)                                            │
│  ─────────────────────────────────────────────────────────  │
│  • CI/CD as Kubernetes resources                          │
│  • Tasks, Pipelines, PipelineRuns                        │
│  • Cloud-native, serverless                               │
│                                                             │
│  ARGO CD (CNCF Graduated)                                 │
│  ─────────────────────────────────────────────────────────  │
│  • GitOps continuous delivery                             │
│  • Declarative, Git as source of truth                   │
│  • Sync cluster state with Git                           │
│                                                             │
│  FLUX (CNCF Graduated)                                    │
│  ─────────────────────────────────────────────────────────  │
│  • GitOps continuous delivery                             │
│  • Similar to Argo CD                                     │
│  • Tight Helm integration                                │
│                                                             │
│  ARGO WORKFLOWS (CNCF)                                    │
│  ─────────────────────────────────────────────────────────  │
│  • Workflow engine for Kubernetes                        │
│  • DAG-based workflows                                    │
│  • CI/CD and data pipelines                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## GitOps vs Traditional CI/CD

```
┌─────────────────────────────────────────────────────────────┐
│              GITOPS vs TRADITIONAL CI/CD                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TRADITIONAL (Push-based):                                │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Git → CI Server → Push to Cluster                        │
│                                                             │
│  ┌──────┐    ┌─────────┐    ┌─────────────┐              │
│  │ Git  │ →  │   CI    │ →  │  Cluster    │              │
│  │      │    │ Server  │    │             │              │
│  └──────┘    └─────────┘    └─────────────┘              │
│                                                             │
│  • CI needs cluster credentials                           │
│  • External system pushes changes                         │
│                                                             │
│  GITOPS (Pull-based):                                     │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Git ← Pull from Cluster                                  │
│                                                             │
│  ┌──────┐              ┌─────────────┐                    │
│  │ Git  │ ←────────── │  Cluster    │                    │
│  │      │   agent     │  (Argo CD)  │                    │
│  └──────┘   pulls     └─────────────┘                    │
│                                                             │
│  • Cluster pulls from Git                                 │
│  • No external access needed                              │
│  • Git = source of truth                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Deployment Strategies

```
┌─────────────────────────────────────────────────────────────┐
│              DEPLOYMENT STRATEGIES                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ROLLING UPDATE (Kubernetes default)                      │
│  ─────────────────────────────────────────────────────────  │
│  Gradually replace old pods with new                      │
│                                                             │
│  [v1][v1][v1] → [v1][v1][v2] → [v1][v2][v2] → [v2][v2][v2]│
│                                                             │
│  + Zero downtime                                          │
│  + Simple                                                  │
│  - Slow rollback                                          │
│                                                             │
│  BLUE-GREEN                                               │
│  ─────────────────────────────────────────────────────────  │
│  Run both versions, switch traffic instantly              │
│                                                             │
│  [Blue v1] ← traffic     [Blue v1]                        │
│  [Green v2]         →    [Green v2] ← traffic             │
│                                                             │
│  + Instant rollback                                       │
│  + Full testing before switch                             │
│  - Double resources needed                                │
│                                                             │
│  CANARY                                                   │
│  ─────────────────────────────────────────────────────────  │
│  Route small % of traffic to new version                  │
│                                                             │
│  [v1][v1][v1] ← 90% traffic                              │
│  [v2]         ← 10% traffic (canary)                     │
│                                                             │
│  + Test with real traffic                                 │
│  + Gradual rollout                                        │
│  + Quick rollback (just remove canary)                   │
│  - More complex setup                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Strategy Comparison

| Strategy | Downtime | Rollback | Resource Cost | Complexity |
|----------|----------|----------|---------------|------------|
| **Rolling** | None | Slow | Normal | Low |
| **Blue-Green** | None | Instant | 2x during deploy | Medium |
| **Canary** | None | Fast | Slight increase | High |
| **Recreate** | Yes | Slow | Normal | Lowest |

---

## Container Registries

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER REGISTRIES                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Where container images are stored                        │
│                                                             │
│  CI builds image → Push to registry → K8s pulls image    │
│                                                             │
│  Public registries:                                       │
│  ─────────────────────────────────────────────────────────  │
│  • Docker Hub (docker.io)                                │
│  • GitHub Container Registry (ghcr.io)                   │
│  • Google Container Registry (gcr.io)                    │
│  • Quay.io                                               │
│                                                             │
│  Private registries:                                      │
│  ─────────────────────────────────────────────────────────  │
│  • Harbor (CNCF Graduated)                               │
│  • AWS ECR                                               │
│  • Azure ACR                                             │
│  • Google Artifact Registry                              │
│                                                             │
│  Harbor features:                                         │
│  • Vulnerability scanning                                 │
│  • Image signing                                          │
│  • Role-based access                                      │
│  • Replication                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Continuous Deployment requires confidence** - You need comprehensive automated testing and monitoring to deploy every commit automatically.

- **GitOps was coined by Weaveworks** - The term and practice were popularized by Weaveworks, creators of Flux.

- **Canary comes from coal mining** - Miners used canaries to detect toxic gases. In deployments, a canary release detects issues with real traffic.

- **DORA metrics** - DevOps Research and Assessment (DORA) identified deployment frequency, lead time, change failure rate, and MTTR as key performance indicators.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| No automated tests | Broken deploys | Tests are essential for CI |
| Manual deployments | Inconsistent, error-prone | Automate everything |
| Big bang releases | High risk | Small, frequent changes |
| No rollback plan | Stuck with bad version | Always have rollback ready |

---

## Quiz

1. **What's the difference between Continuous Delivery and Continuous Deployment?**
   <details>
   <summary>Answer</summary>
   Continuous Delivery means code is always ready to deploy (manual trigger). Continuous Deployment automatically deploys every change that passes tests. Delivery = CAN deploy; Deployment = DOES deploy.
   </details>

2. **What is GitOps?**
   <details>
   <summary>Answer</summary>
   A CD approach where Git is the source of truth for infrastructure and application state. An agent in the cluster pulls desired state from Git and reconciles it. Changes are made via Git commits, not direct kubectl commands.
   </details>

3. **What is a canary deployment?**
   <details>
   <summary>Answer</summary>
   A deployment strategy where a small percentage of traffic is routed to the new version while most traffic goes to the old version. If the canary performs well, traffic is gradually shifted. If not, the canary is removed.
   </details>

4. **Name two Kubernetes-native CI/CD tools.**
   <details>
   <summary>Answer</summary>
   Tekton (CI/CD pipelines as Kubernetes resources), Argo CD (GitOps continuous delivery), Flux (GitOps), Argo Workflows (workflow engine). All are CNCF projects.
   </details>

5. **What are the DORA metrics?**
   <details>
   <summary>Answer</summary>
   Deployment Frequency (how often you deploy), Lead Time (time from commit to production), Change Failure Rate (% of deployments causing issues), Mean Time to Recovery (time to fix production issues). These measure DevOps performance.
   </details>

---

## Summary

**CI/CD concepts**:
- **CI**: Integrate and test code frequently
- **CD (Delivery)**: Always ready to deploy
- **CD (Deployment)**: Auto-deploy everything

**Pipeline stages**:
Source → Build → Test → Package → Deploy

**Deployment strategies**:
- **Rolling**: Gradual replacement (default)
- **Blue-Green**: Switch traffic between versions
- **Canary**: Test with small traffic percentage

**GitOps**:
- Git = source of truth
- Pull-based (cluster pulls from Git)
- Tools: Argo CD, Flux

---

## Next Module

[Module 4.2: Application Packaging](../module-4.2-application-packaging/) - Helm, Kustomize, and other tools for packaging Kubernetes applications.
