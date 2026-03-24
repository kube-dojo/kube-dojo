# Chaos Engineering

**Break things on purpose — before they break on their own.**

Chaos Engineering is the discipline of proactively injecting failures into your systems to discover weaknesses before they cause outages. It's not about randomly destroying things — it's the scientific method applied to distributed systems resilience.

---

## Modules

| # | Module | Time | What You'll Learn |
|---|--------|------|-------------------|
| 1.1 | [Chaos Principles & Resilience](module-1.1-chaos-principles.md) | 1.5h | Scientific method, blast radius, steady state, game days |
| 1.2 | [Chaos Mesh Fundamentals](module-1.2-chaos-mesh.md) | 2.5h | Pod/Network/Stress chaos, CRDs, RBAC |
| 1.3 | [Network & App Fault Injection](module-1.3-network-fault-injection.md) | 3h | Latency, DNS failure, HTTP chaos, clock skew |
| 1.4 | [Stateful Chaos: Databases & Storage](module-1.4-stateful-chaos.md) | 3h | IO chaos, DB failover, split-brain, PV detachment |
| 1.5 | [Automating Chaos & Game Days](module-1.5-automating-chaos.md) | 2h | CI/CD integration, automated abort, game day facilitation |

**Total time**: ~12 hours

---

## Prerequisites

- [Release Engineering](/platform/disciplines/release-engineering/) — progressive delivery mechanisms are what chaos tests validate
- Kubernetes basics (Pods, Deployments, Services)
- Prometheus/Grafana basics (for automated abort conditions)
