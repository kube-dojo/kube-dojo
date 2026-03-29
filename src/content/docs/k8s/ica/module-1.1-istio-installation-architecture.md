---
title: "Module 1.1: Istio Installation & Architecture"
slug: k8s/ica/module-1.1-istio-installation-architecture/
sidebar:
  order: 2
---
## Complexity: `[MEDIUM]`
## Time to Complete: 50-60 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [CKA Part 3: Services & Networking](../cka/part3-services-networking/) — Kubernetes networking fundamentals
- [Service Mesh Concepts](../../platform/toolkits/infrastructure-networking/networking/module-5.2-service-mesh/) — Why service mesh exists
- Basic understanding of proxies and TLS

---

## Why This Module Matters

Installation & Architecture is **20% of the ICA exam**. You'll be expected to install Istio using different methods, understand when to use each installation profile, configure sidecar injection, and troubleshoot installation issues.

More importantly, understanding Istio's architecture lets you reason about *why* things break. When a VirtualService doesn't route traffic correctly (Module 2) or mTLS fails (Module 3), the answer is almost always in the architecture — a missing sidecar, a misconfigured istiod, or a control plane that can't push config to proxies.

> **The Hospital Analogy**
>
> Think of Istio like a hospital's nervous system. istiod is the brain — it makes decisions about routing, security, and policy. Envoy sidecars are the nerve endings in every organ (pod) — they execute those decisions locally. If the brain goes down, the nerve endings keep working with their last instructions. If a nerve ending is missing (no sidecar), that organ operates blind.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Install Istio using `istioctl`, Helm, and the IstioOperator CRD
- Choose the right installation profile for your use case
- Configure automatic and manual sidecar injection
- Understand Istio's control plane architecture
- Upgrade Istio safely using canary and in-place methods
- Explain Ambient mode and when to use it

---

## Did You Know?

- **Istio was originally three components**: Pilot (config), Mixer (telemetry), and Citadel (security). In Istio 1.5+ they were merged into a single binary called `istiod`. This reduced resource usage by 50% and simplified operations dramatically.

- **Every Envoy sidecar uses ~50-100MB of memory**: In a cluster with 1,000 pods, that's 50-100GB just for proxies. This is why Ambient mode (sidecar-less) was developed — it moves proxy functions to shared per-node ztunnels.

- **Istio's adoption outpaces all other service meshes combined**: According to the CNCF Annual Survey, Istio has >50% market share among service mesh users, and was the first service mesh to graduate from CNCF (July 2023).

---

## War Story: The Profile That Ate Production

**Characters:**
- Alex: DevOps engineer (3 years experience)
- Team: 5 engineers running 30 microservices

**The Incident:**

Alex had been running Istio in development for months using `istioctl install --set profile=demo`. Everything worked beautifully — Kiali dashboards, Jaeger traces, Grafana metrics. On deployment day, Alex ran the same command on the production cluster.

Three hours later, the billing team reported that their monthly invoice showed a 40% spike in compute costs. The `demo` profile deploys all optional components with generous resource allocations. Kiali, Jaeger, and Grafana were each consuming 2GB+ of RAM across 3 replicas they didn't need.

But the real problem came a week later. The `demo` profile sets permissive mTLS — meaning services accept both encrypted and unencrypted traffic. Alex assumed mTLS was enforced. The security audit found plaintext traffic flowing between payment services.

**The Fix:**

```bash
# What Alex should have done for production:
istioctl install --set profile=default

# Then explicitly set STRICT mTLS:
kubectl apply -f - <<EOF
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT
EOF
```

**Lesson**: Profiles are not "sizes" — they're configurations with security implications. Always use `default` or `minimal` in production.

---

## Part 1: Istio Architecture

### 1.1 The Control Plane: istiod

Istio's control plane is a single binary called `istiod` that runs as a Deployment in the `istio-system` namespace. It combines what used to be three separate components:

```
┌─────────────────────────────────────────────────────────┐
│                        istiod                            │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   Pilot      │  │  Citadel    │  │   Galley        │ │
│  │             │  │             │  │                 │ │
│  │  Config     │  │  Certificate│  │  Config         │ │
│  │  distribution│  │  management │  │  validation     │ │
│  │  (xDS API)  │  │  (mTLS)     │  │  (webhooks)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
│                                                          │
│           Watches K8s API ◄──── Service Registry         │
│           Pushes config  ────► Envoy Proxies (xDS)       │
└─────────────────────────────────────────────────────────┘
```

**What each component does:**

| Component | Responsibility | How It Works |
|-----------|---------------|--------------|
| **Pilot** | Service discovery & traffic config | Watches K8s Services, converts to Envoy config, pushes via xDS API |
| **Citadel** | Certificate authority | Issues SPIFFE certs to each proxy, rotates automatically |
| **Galley** | Config validation | Validates Istio resources via admission webhooks |

### 1.2 The Data Plane: Envoy Proxies

Every pod in the mesh gets an Envoy sidecar container injected alongside the application container. The sidecar intercepts all inbound and outbound traffic:

```
┌─────────────── Pod ──────────────────┐
│                                       │
│  ┌──────────────┐  ┌──────────────┐  │
│  │  Application  │  │  Envoy       │  │
│  │  Container    │  │  Sidecar     │  │
│  │              │  │              │  │
│  │  Port 8080   │◄─┤  Port 15001  │  │
│  │              │  │  (outbound)  │  │
│  │              │  │  Port 15006  │  │
│  │              │  │  (inbound)   │  │
│  └──────────────┘  └──────┬───────┘  │
│                           │          │
│         iptables rules redirect      │
│         all traffic through Envoy    │
└───────────────────────────┬──────────┘
                            │
                    xDS config from istiod
```

**Key Envoy ports:**

| Port | Purpose |
|------|---------|
| 15001 | Outbound traffic listener |
| 15006 | Inbound traffic listener |
| 15010 | xDS (plaintext, istiod) |
| 15012 | xDS (mTLS, istiod) |
| 15014 | Control plane metrics |
| 15020 | Health checks |
| 15021 | Health check endpoint |
| 15090 | Envoy Prometheus metrics |

### 1.3 How Traffic Flows

```
Service A (Pod)                              Service B (Pod)
┌────────────────────┐                      ┌────────────────────┐
│ App ──► Envoy ─────┼──── mTLS tunnel ────►┼── Envoy ──► App   │
│         Sidecar     │                      │   Sidecar          │
└────────────────────┘                      └────────────────────┘

1. App sends request to Service B (thinks it's plaintext HTTP)
2. iptables redirects to local Envoy sidecar (outbound)
3. Envoy applies routing rules (VirtualService, DestinationRule)
4. Envoy establishes mTLS connection to destination Envoy
5. Destination Envoy decrypts, applies inbound policies
6. Destination Envoy forwards to local application
```

---

## Part 2: Installation Methods

### 2.1 Installing with istioctl (Recommended for Exam)

`istioctl` is Istio's CLI tool. It's the fastest way to install and the most likely method on the ICA exam.

```bash
# Download istioctl
curl -L https://istio.io/downloadIstio | sh -
cd istio-1.22.0
export PATH=$PWD/bin:$PATH

# Install with default profile
istioctl install --set profile=default -y

# Verify installation
istioctl verify-install
```

**What `istioctl install` does:**
1. Generates Kubernetes manifests from the selected profile
2. Applies them to the cluster
3. Waits for components to be ready
4. Reports success or errors

### 2.2 Installation Profiles

Profiles are pre-configured sets of components and settings. **Know these for the exam:**

| Profile | istiod | Ingress GW | Egress GW | Use Case |
|---------|--------|-----------|----------|----------|
| `default` | Yes | Yes | No | **Production** |
| `demo` | Yes | Yes | Yes | Learning/testing |
| `minimal` | Yes | No | No | Control plane only |
| `remote` | No | No | No | Multi-cluster remote |
| `empty` | No | No | No | Custom build |
| `ambient` | Yes | Yes | No | Ambient mode (no sidecars) |

```bash
# See what a profile installs (without applying)
istioctl profile dump default

# Compare profiles
istioctl profile diff default demo

# Install with specific profile
istioctl install --set profile=demo -y

# Install with customizations
istioctl install --set profile=default \
  --set meshConfig.accessLogFile=/dev/stdout \
  --set values.global.proxy.resources.requests.memory=128Mi \
  -y
```

**Profile component comparison:**

```
                    default    demo    minimal   ambient
                    ───────    ────    ───────   ───────
istiod              ✓          ✓       ✓         ✓
istio-ingressgateway ✓         ✓       ✗         ✓
istio-egressgateway  ✗         ✓       ✗         ✗
ztunnel              ✗         ✗       ✗         ✓
istio-cni            ✗         ✗       ✗         ✓
```

### 2.3 Installing with Helm

Helm gives more control over individual values and integrates better with GitOps workflows.

```bash
# Add Istio Helm repo
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update

# Install in order: base → istiod → gateway
# Step 1: CRDs and cluster-wide resources
helm install istio-base istio/base -n istio-system --create-namespace

# Step 2: Control plane
helm install istiod istio/istiod -n istio-system --wait

# Step 3: Ingress gateway (optional)
kubectl create namespace istio-ingress
helm install istio-ingress istio/gateway -n istio-ingress

# Verify
kubectl get pods -n istio-system
kubectl get pods -n istio-ingress
```

**When to use Helm vs istioctl:**

| Scenario | Method |
|----------|--------|
| ICA exam | `istioctl` (fastest) |
| GitOps / ArgoCD | Helm charts |
| Custom operator pattern | IstioOperator CRD |
| Quick testing | `istioctl` |

### 2.4 IstioOperator CRD

The IstioOperator resource lets you declaratively manage Istio configuration. The istio-operator controller watches for these resources and reconciles the installation.

```yaml
# istio-operator.yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: istio-control-plane
  namespace: istio-system
spec:
  profile: default
  meshConfig:
    accessLogFile: /dev/stdout
    enableTracing: true
    defaultConfig:
      tracing:
        zipkin:
          address: zipkin.istio-system:9411
  components:
    ingressGateways:
    - name: istio-ingressgateway
      enabled: true
      k8s:
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
    egressGateways:
    - name: istio-egressgateway
      enabled: false
  values:
    global:
      proxy:
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
```

```bash
# Apply with istioctl
istioctl install -f istio-operator.yaml -y

# Or install the operator and apply the CR
istioctl operator init
kubectl apply -f istio-operator.yaml
```

---

## Part 3: Sidecar Injection

### 3.1 Automatic Sidecar Injection

The most common method. Label a namespace and all new pods get sidecars automatically:

```bash
# Enable automatic injection for a namespace
kubectl label namespace default istio-injection=enabled

# Verify the label
kubectl get namespace default --show-labels

# Deploy an app — sidecar is injected automatically
kubectl run nginx --image=nginx -n default
kubectl get pod nginx -o jsonpath='{.spec.containers[*].name}'
# Output: nginx istio-proxy

# Disable injection for a specific pod (opt-out)
kubectl run skip-mesh --image=nginx \
  --overrides='{"metadata":{"annotations":{"sidecar.istio.io/inject":"false"}}}'
```

**How it works:**

```
1. Namespace has label: istio-injection=enabled
2. Pod is created
3. K8s API server calls istiod's MutatingWebhook
4. istiod injects istio-init (iptables setup) + istio-proxy (Envoy) containers
5. Pod starts with sidecar
```

### 3.2 Manual Sidecar Injection

Use when you can't label the namespace or need fine-grained control:

```bash
# Inject sidecar into a deployment YAML
istioctl kube-inject -f deployment.yaml | kubectl apply -f -

# Inject into an existing deployment
kubectl get deployment myapp -o yaml | istioctl kube-inject -f - | kubectl apply -f -

# Check injection status
istioctl analyze -n default
```

### 3.3 Controlling Injection

```yaml
# Per-pod annotation to disable injection
apiVersion: v1
kind: Pod
metadata:
  annotations:
    sidecar.istio.io/inject: "false"
spec:
  containers:
  - name: app
    image: myapp:latest
---
# Per-pod annotation to enable injection (even without namespace label)
apiVersion: v1
kind: Pod
metadata:
  annotations:
    sidecar.istio.io/inject: "true"
  labels:
    sidecar.istio.io/inject: "true"
spec:
  containers:
  - name: app
    image: myapp:latest
```

**Injection priority (highest to lowest):**

1. Pod annotation `sidecar.istio.io/inject`
2. Pod label `sidecar.istio.io/inject`
3. Namespace label `istio-injection`
4. Global mesh config default policy

### 3.4 Revision-Based Injection (for Upgrades)

Instead of the `istio-injection` label, use revision labels for canary upgrades:

```bash
# Install a specific revision
istioctl install --set revision=1-22 -y

# Label namespace with revision (not istio-injection)
kubectl label namespace default istio.io/rev=1-22

# This allows running two Istio versions simultaneously
```

---

## Part 4: Ambient Mode

Ambient mode is Istio's **sidecar-less** data plane. Instead of injecting a proxy into every pod, it uses:

1. **ztunnel** — A per-node L4 proxy (handles mTLS, L4 auth)
2. **waypoint proxies** — Optional per-namespace L7 proxies (handles routing, L7 policies)

```
Traditional Sidecar Mode:
┌─────────────────┐  ┌─────────────────┐
│ Pod A            │  │ Pod B            │
│ ┌─────┐ ┌─────┐ │  │ ┌─────┐ ┌─────┐ │
│ │ App │ │Envoy│ │  │ │ App │ │Envoy│ │
│ └─────┘ └─────┘ │  │ └─────┘ └─────┘ │
└─────────────────┘  └─────────────────┘
   ~100MB overhead      ~100MB overhead

Ambient Mode:
┌──────────┐  ┌──────────┐
│ Pod A    │  │ Pod B    │
│ ┌──────┐ │  │ ┌──────┐ │
│ │ App  │ │  │ │ App  │ │
│ └──────┘ │  │ └──────┘ │
└────┬─────┘  └────┬─────┘
     │              │
┌────▼──────────────▼─────┐  ◄── Shared per-node
│       ztunnel (L4)       │
└──────────────────────────┘
         ~40MB per node (not per pod)
```

```bash
# Install Istio with ambient profile
istioctl install --set profile=ambient -y

# Add a namespace to the ambient mesh
kubectl label namespace default istio.io/dataplane-mode=ambient

# Deploy a waypoint proxy for L7 features (optional)
istioctl waypoint apply -n default --enroll-namespace
```

**When to use Ambient vs Sidecar:**

| Factor | Sidecar | Ambient |
|--------|---------|---------|
| Resource overhead | High (per-pod proxy) | Low (per-node ztunnel) |
| L7 features | Always available | Requires waypoint proxy |
| Maturity | Production-ready | GA as of Istio 1.24 |
| Application restarts | Required for injection | Not required |
| ICA exam | Primary focus | May appear |

---

## Part 5: Upgrading Istio

### 5.1 In-Place Upgrade

Simplest method — upgrade the control plane, then restart workloads:

```bash
# Download new version
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.23.0 sh -

# Upgrade control plane
istioctl upgrade -y

# Verify
istioctl version

# Restart workloads to get new sidecar version
kubectl rollout restart deployment -n default
```

### 5.2 Canary Upgrade (Recommended for Production)

Run two versions of istiod simultaneously, migrate workloads gradually:

```bash
# Step 1: Install new revision alongside existing
istioctl install --set revision=1-23 -y

# Verify both versions running
kubectl get pods -n istio-system -l app=istiod

# Step 2: Move namespaces to new revision
kubectl label namespace default istio.io/rev=1-23 --overwrite
kubectl label namespace default istio-injection-  # Remove old label

# Step 3: Restart workloads to pick up new sidecars
kubectl rollout restart deployment -n default

# Step 4: Verify workloads use new proxy
istioctl proxy-status

# Step 5: Remove old control plane
istioctl uninstall --revision 1-22 -y
```

**Canary upgrade flow:**

```
Time ────────────────────────────────────────────────►

istiod v1.22  ████████████████████████░░░░░  (uninstall)
istiod v1.23  ░░░░░░░████████████████████████████████

Namespace A   ──── v1.22 sidecars ──── restart ──── v1.23 sidecars ────
Namespace B   ──── v1.22 sidecars ────────── restart ──── v1.23 sidecars
```

---

## Part 6: Verifying Your Installation

These commands are critical for both the exam and production:

```bash
# Check all Istio components are healthy
istioctl verify-install

# Analyze configuration for issues
istioctl analyze --all-namespaces

# Check proxy sync status
istioctl proxy-status

# Check Istio version (client + control plane + data plane)
istioctl version

# List installed Istio components
kubectl get pods -n istio-system
kubectl get svc -n istio-system

# Check MutatingWebhookConfiguration (sidecar injection)
kubectl get mutatingwebhookconfigurations | grep istio

# Check if a namespace has injection enabled
kubectl get ns --show-labels | grep istio
```

---

## Common Mistakes

| Mistake | Symptom | Solution |
|---------|---------|----------|
| Using `demo` profile in production | High resource usage, permissive mTLS | Use `default` or `minimal` profile |
| Forgetting namespace label | Pods have no sidecar, no mesh features | `kubectl label ns <name> istio-injection=enabled` |
| Not restarting pods after labeling | Existing pods don't get sidecars | `kubectl rollout restart deployment -n <ns>` |
| Running `istioctl install` without `-y` | Hangs waiting for confirmation | Add `-y` flag (exam time is precious) |
| Ignoring `istioctl analyze` warnings | Misconfigurations go unnoticed | Run `istioctl analyze` after every change |
| Mixing injection label and revision label | Unpredictable injection behavior | Use one method per namespace |
| Not checking proxy-status after upgrade | Stale sidecars running old config | `istioctl proxy-status` to verify sync |

---

## Quiz

Test your knowledge before moving on:

**Q1: Which installation profile is recommended for production?**

<details>
<summary>Show Answer</summary>

`default` — It installs istiod and the ingress gateway with production-appropriate resource settings. Unlike `demo`, it does not install the egress gateway or set permissive defaults.

</details>

**Q2: What is the correct command to enable automatic sidecar injection?**

<details>
<summary>Show Answer</summary>

```bash
kubectl label namespace <namespace> istio-injection=enabled
```

After labeling, existing pods must be restarted to get sidecars:
```bash
kubectl rollout restart deployment -n <namespace>
```

</details>

**Q3: What are the three components merged into istiod?**

<details>
<summary>Show Answer</summary>

1. **Pilot** — Service discovery and traffic configuration (xDS)
2. **Citadel** — Certificate management for mTLS
3. **Galley** — Configuration validation

All merged into the single `istiod` binary since Istio 1.5.

</details>

**Q4: How do you perform a canary upgrade of Istio?**

<details>
<summary>Show Answer</summary>

1. Install new version with `--set revision=<new>`: `istioctl install --set revision=1-23 -y`
2. Label namespaces with new revision: `kubectl label ns <ns> istio.io/rev=1-23`
3. Restart workloads: `kubectl rollout restart deployment -n <ns>`
4. Verify with `istioctl proxy-status`
5. Remove old version: `istioctl uninstall --revision <old> -y`

</details>

**Q5: What is the difference between Ambient mode's ztunnel and waypoint proxy?**

<details>
<summary>Show Answer</summary>

- **ztunnel**: Per-node L4 proxy. Handles mTLS encryption/decryption and L4 authorization. Runs as a DaemonSet. Always active in ambient mode.
- **waypoint proxy**: Optional per-namespace L7 proxy. Handles HTTP routing, L7 authorization policies, traffic management. Only deployed when L7 features are needed.

</details>

**Q6: You install Istio and label a namespace, but pods don't get sidecars. What do you check?**

<details>
<summary>Show Answer</summary>

1. Verify label: `kubectl get ns <ns> --show-labels` (look for `istio-injection=enabled`)
2. Check MutatingWebhook: `kubectl get mutatingwebhookconfigurations | grep istio`
3. Check istiod is running: `kubectl get pods -n istio-system`
4. Check if pod has opt-out annotation: `sidecar.istio.io/inject: "false"`
5. Restart pods (existing pods don't get retroactive injection): `kubectl rollout restart deployment -n <ns>`

</details>

**Q7: What Helm charts are needed for a complete Istio installation, and in what order?**

<details>
<summary>Show Answer</summary>

1. `istio/base` — CRDs and cluster-wide resources (namespace: `istio-system`)
2. `istio/istiod` — Control plane (namespace: `istio-system`)
3. `istio/gateway` — Ingress/egress gateway (namespace: `istio-ingress` or similar)

Order matters because istiod depends on the CRDs from base, and gateways depend on istiod.

</details>

---

## Hands-On Exercise: Install and Explore Istio

### Objective
Install Istio, deploy a sample application with sidecars, and verify the mesh is working.

### Setup

```bash
# Create a kind cluster (if not already running)
kind create cluster --name istio-lab

# Download and install Istio
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.22.0 sh -
export PATH=$PWD/istio-1.22.0/bin:$PATH
```

### Tasks

**Task 1: Install Istio with the demo profile**

```bash
istioctl install --set profile=demo -y
```

Verify:
```bash
# All pods should be Running
kubectl get pods -n istio-system

# Should show client, control plane, and data plane versions
istioctl version
```

**Task 2: Enable sidecar injection and deploy an app**

```bash
# Label the default namespace
kubectl label namespace default istio-injection=enabled

# Deploy the Bookinfo sample app
kubectl apply -f istio-1.22.0/samples/bookinfo/platform/kube/bookinfo.yaml

# Wait for pods
kubectl wait --for=condition=ready pod --all -n default --timeout=120s

# Verify each pod has 2 containers (app + istio-proxy)
kubectl get pods -n default
```

**Task 3: Check proxy sync status**

```bash
# All proxies should show SYNCED
istioctl proxy-status
```

Expected output:
```
NAME                                    CLUSTER   CDS    LDS    EDS    RDS    ECDS   ISTIOD
details-v1-xxx.default                  Synced    Synced Synced Synced Synced istiod-xxx
productpage-v1-xxx.default              Synced    Synced Synced Synced Synced istiod-xxx
ratings-v1-xxx.default                  Synced    Synced Synced Synced Synced istiod-xxx
reviews-v1-xxx.default                  Synced    Synced Synced Synced Synced istiod-xxx
```

**Task 4: Analyze configuration**

```bash
# Should report no issues
istioctl analyze --all-namespaces
```

**Task 5: Compare profiles**

```bash
# See the difference between default and demo
istioctl profile diff default demo
```

### Success Criteria

- [ ] Istio is installed with all components running in `istio-system`
- [ ] Bookinfo pods each have 2 containers (application + istio-proxy)
- [ ] `istioctl proxy-status` shows all proxies as SYNCED
- [ ] `istioctl analyze` reports no critical issues
- [ ] You can explain the difference between `default` and `demo` profiles

### Cleanup

```bash
kubectl delete -f istio-1.22.0/samples/bookinfo/platform/kube/bookinfo.yaml
istioctl uninstall --purge -y
kubectl delete namespace istio-system
kind delete cluster --name istio-lab
```

---

## Next Module

Continue to [Module 2: Traffic Management](module-1.2-istio-traffic-management/) — the heaviest ICA domain at 35%, covering VirtualService, DestinationRule, Gateway, traffic shifting, fault injection, and more.
