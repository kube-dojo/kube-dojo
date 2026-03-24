# ICA - Istio Certified Associate

> **Performance-based exam** | 120 minutes | Passing score: 68% | $250 USD

## Overview

The ICA (Istio Certified Associate) validates your ability to install, configure, and operate Istio service mesh in Kubernetes environments. It's a **hands-on exam** — you'll configure real Istio resources on live clusters, not answer multiple-choice questions.

**KubeDojo covers ~90%+ of ICA topics** through existing modules plus this dedicated ICA track with 4 modules covering all domains. This page maps ICA domains to all relevant content.

> **Why ICA matters**: Istio is the most widely deployed service mesh. As microservice architectures grow, service mesh skills become essential for traffic management, security (mTLS), and observability. ICA proves you can actually do the work, not just talk about it.

---

## Exam Details

| Aspect | Details |
|--------|---------|
| **Format** | Performance-based (hands-on) |
| **Duration** | 120 minutes |
| **Passing Score** | 68% |
| **Environment** | Real Kubernetes clusters with Istio |
| **Validity** | 3 years |
| **Cost** | $250 USD (includes one free retake) |
| **Kubernetes Version** | 1.31+ |
| **Istio Version** | 1.22+ |

### Three-Pass Strategy for ICA

Like CKA/CKS, the three-pass approach works well:

```
Pass 1 (0-40 min):  Quick wins — label namespaces, apply basic policies
Pass 2 (40-90 min): Medium tasks — VirtualService routing, DestinationRules
Pass 3 (90-120 min): Complex tasks — multi-step traffic management, debugging
```

> **Tip**: `istioctl` is your best friend. Unlike kubectl-only exams, ICA expects you to use `istioctl` for installation, diagnostics, and proxy inspection.

---

## Exam Domains

| Domain | Weight | Module | Status |
|--------|--------|--------|--------|
| Installation, Upgrade & Configuration | 20% | [Module 1](module-1-istio-installation-architecture.md) | New |
| Traffic Management | 35% | [Module 2](module-2-istio-traffic-management.md) | New |
| Resilience and Fault Injection | 10% | [Module 2](module-2-istio-traffic-management.md) (included) | New |
| Security | 15% | [Module 3](module-3-istio-security-troubleshooting.md) | New |
| Observability | 10% | [Module 4](module-4-istio-observability.md) | New |
| Troubleshooting | 10% | [Module 3](module-3-istio-security-troubleshooting.md) (included) | New |

### Domain Weight Visualization

```
┌──────────────────────────────────────────────────────────────────────┐
│ ICA Exam Domains by Weight                                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Traffic Management     ████████████████████████████████████  35%    │
│  Installation & Config  ████████████████████               20%      │
│  Security               ███████████████                    15%      │
│  Resilience & Fault Inj ██████████                         10%      │
│  Observability          ██████████                         10%      │
│  Troubleshooting        ██████████                         10%      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Learning Path

### Step 1: Prerequisites

Before starting ICA prep, ensure you have:

| Prerequisite | Where to Learn |
|-------------|----------------|
| Kubernetes Services & Networking | [CKA Part 3](../cka/part3-services-networking/README.md) |
| Gateway API | [CKA Module 3.5](../cka/part3-services-networking/module-3.5-gateway-api.md) |
| Service Mesh Concepts | [Platform Networking 5.2](../../platform/toolkits/networking/module-5.2-service-mesh.md) |
| TLS/mTLS Fundamentals | [Security Principles](../../platform/foundations/security-principles/README.md) |

### Step 2: ICA Modules (This Track)

Follow these in order:

| # | Module | Domain | Time |
|---|--------|--------|------|
| 1 | [Installation & Architecture](module-1-istio-installation-architecture.md) | Installation, Upgrade & Configuration (20%) | 50-60 min |
| 2 | [Traffic Management](module-2-istio-traffic-management.md) | Traffic Management (35%) + Resilience (10%) | 60-75 min |
| 3 | [Security & Troubleshooting](module-3-istio-security-troubleshooting.md) | Security (15%) + Troubleshooting (10%) | 50-60 min |
| 4 | [Observability](module-4-istio-observability.md) | Observability (10%) | 40-50 min |

### Step 3: Cross-Reference Modules

These existing KubeDojo modules cover ICA-relevant topics:

**Observability (deeper dives):**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Platform Observability Theory](../../platform/foundations/observability-theory/README.md) | Metrics, logs, traces fundamentals | Background |
| [Platform Observability Tools](../../platform/toolkits/observability/README.md) | Prometheus, Grafana, Jaeger | Direct — Istio integrates with all three |

**Service Mesh Foundations:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Service Mesh](../../platform/toolkits/networking/module-5.2-service-mesh.md) | When to use service mesh, Istio vs Linkerd | Background |
| [Cilium](../../platform/toolkits/networking/module-5.1-cilium.md) | eBPF networking (alternative to sidecar mesh) | Contextual |

---

## ICA vs Other Certifications

| Aspect | ICA | CKA | CKS |
|--------|-----|-----|-----|
| Focus | Service mesh | Cluster admin | Cluster security |
| Tool | istioctl + kubectl | kubectl | kubectl + security tools |
| Resources | VirtualService, DestinationRule, etc. | Pods, Services, etc. | NetworkPolicy, RBAC, etc. |
| Overlap | Networking, TLS | Foundation for ICA | mTLS concepts overlap |
| Recommended Order | After CKA | First | After CKA |

---

## Exam Tips

1. **Know `istioctl` cold** — Installation, diagnostics, proxy inspection. This is not optional.
2. **VirtualService + DestinationRule = 35% of the exam** — Practice traffic splitting, fault injection, retries until it's muscle memory.
3. **Label your namespaces** — Sidecar injection via `istio-injection=enabled` is fundamental. Miss it and nothing works.
4. **mTLS modes matter** — Know STRICT vs PERMISSIVE and when each is appropriate.
5. **Use `istioctl analyze`** — It catches misconfigurations faster than staring at YAML.
6. **Practice on kind clusters** — `istioctl install --set profile=demo` works perfectly on kind.
7. **Bookmark the Istio docs** — You'll have access during the exam. Know where things are.

---

## Practice Environment Setup

```bash
# Create a kind cluster for ICA practice
kind create cluster --name ica-practice --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOF

# Install Istio with demo profile (all features enabled)
istioctl install --set profile=demo -y

# Enable sidecar injection in default namespace
kubectl label namespace default istio-injection=enabled

# Deploy sample application
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/bookinfo/platform/kube/bookinfo.yaml

# Verify everything is running
kubectl get pods
istioctl analyze
```

---

## Start Learning

Begin with [Module 1: Installation & Architecture](module-1-istio-installation-architecture.md) to understand how Istio works under the hood, then proceed through modules in order.

Good luck on your ICA journey!
