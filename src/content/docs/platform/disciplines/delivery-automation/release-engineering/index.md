---
title: "Release Engineering"
sidebar:
  order: 0
  label: "Release Engineering"
---
**How to ship software reliably at scale.**

This is NOT basic CI/CD — that's covered in [Modern DevOps](../../../../prerequisites/modern-devops/module-1.3-cicd-pipelines/). Release Engineering is about release strategy, progressive delivery, feature management, and coordinating releases across many services and regions.

---

## Modules

| # | Module | Time | What You'll Learn |
|---|--------|------|-------------------|
| 1.1 | [Release Strategies & Progressive Delivery](module-1.1-release-strategies/) | 2h | Blue/Green, Canary, Shadow, blast radius, DB migrations |
| 1.2 | [Advanced Canary with Argo Rollouts](module-1.2-argo-rollouts/) | 3h | Rollouts CRDs, AnalysisRuns, metrics-driven promotion |
| 1.3 | [Feature Management at Scale](module-1.3-feature-flags/) | 2.5h | OpenFeature, Unleash, flag lifecycle, kill switches |
| 1.4 | [Multi-Region & Global Release Orchestration](module-1.4-global-releases/) | 3h | Ring deployments, ApplicationSets, traffic shifting |
| 1.5 | [Release Engineering Metrics](module-1.5-release-metrics/) | 2h | DORA metrics, release health, deployment observability |

**Total time**: ~12.5 hours

---

## Prerequisites

- [CI/CD Pipelines](../../../../prerequisites/modern-devops/module-1.3-cicd-pipelines/) — basic pipeline concepts
- [Kubernetes Deployments](../../../../prerequisites/kubernetes-basics/module-1.4-deployments/) — rolling updates
- Prometheus/Grafana basics (for metrics modules)

## What's Next

After Release Engineering, continue to [Chaos Engineering](../../reliability-security/chaos-engineering/) — test your releases with controlled failure injection.
