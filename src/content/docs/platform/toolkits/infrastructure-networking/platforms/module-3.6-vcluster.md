---
title: "Module 3.6: vCluster"
slug: platform/toolkits/infrastructure-networking/platforms/module-3.6-vcluster
sidebar:
  order: 7
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: ~40 minutes

## Overview

Every developer wants their own Kubernetes cluster. Nobody wants to pay for it. vCluster creates fully functional virtual Kubernetes clusters inside namespaces of a host cluster—giving teams real cluster-level isolation at a fraction of the cost and operational overhead of separate physical clusters.

**What You'll Learn**:
- vCluster architecture: virtual control planes, syncers, and host clusters
- Installing and creating virtual clusters
- Resource synchronization and isolation model
- Use cases: dev environments, CI/CD, multi-tenancy, upgrade testing
- How vCluster compares to namespaces and dedicated clusters

**Prerequisites**:
- Kubernetes fundamentals (Pods, Deployments, Services, Namespaces)
- Multi-tenancy concepts ([Security Principles](../../../foundations/security-principles/))
- kubectl basics
- Helm basics

---

## Why This Module Matters

Kubernetes multi-tenancy is one of the hardest problems in platform engineering. Namespaces are too weak—tenants can interfere with each other through CRDs, cluster-scoped resources, and admission webhooks. Dedicated clusters are too expensive and too slow to provision. vCluster sits in the sweet spot: real cluster-level isolation without the blast radius or bill of separate clusters.

If you are building an Internal Developer Platform, vCluster is one of the most powerful tools in your arsenal for self-service cluster provisioning.

> **Did You Know?**
>
> - vCluster is open source (Apache 2.0) and created by Loft Labs. It became a CNCF Sandbox project in 2024, joining the same ecosystem as Kubernetes itself.
> - A virtual cluster runs its own API server, controller manager, and etcd (or SQLite/PostgreSQL as a lightweight backend)—but it schedules workloads on the host cluster. The host cluster has no idea it is running "clusters within clusters."
> - vCluster can run different Kubernetes versions than the host cluster. You can test a Kubernetes 1.32 upgrade by spinning up a virtual cluster running 1.32 on a 1.31 host—in seconds, at zero extra infrastructure cost.
> - Companies have replaced fleets of 50+ development clusters with a single host cluster running vClusters, cutting infrastructure costs by over 90% while actually improving isolation compared to shared-namespace approaches.

---

## War Story: 30 Clusters, $60K/Month, Zero Sleep

*A mid-stage startup had 30 development teams. Each team demanded their own Kubernetes cluster for isolation—fair enough, after a bad incident where one team's broken admission webhook took down staging for everyone.*

*The platform team obliged. Thirty EKS clusters at roughly $2,000/month each: $60,000/month just for dev environments. Each cluster needed its own monitoring stack, ingress controllers, and cert-manager installation. The platform team of three spent 80% of their time babysitting clusters instead of building the platform.*

*Then they discovered vCluster. They consolidated everything onto two host clusters (one per region), created a self-service portal where developers could spin up a virtual cluster in 30 seconds, and tore down the 30 standalone clusters. Monthly bill: under $6,000. Same isolation. Better developer experience. The platform team finally had time to build things that mattered.*

*The lesson: throwing hardware at multi-tenancy problems is the expensive way to avoid solving them properly.*

---

## Architecture

### How vCluster Works

```
vCLUSTER ARCHITECTURE
════════════════════════════════════════════════════════════════════

HOST CLUSTER (real Kubernetes)
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Namespace: vcluster-team-alpha                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  VIRTUAL CLUSTER (team-alpha)                              │  │
│  │                                                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐   │  │
│  │  │  API Server  │  │  Controller  │  │  etcd / SQLite │   │  │
│  │  │  (k8s 1.31)  │  │  Manager     │  │  (virtual)     │   │  │
│  │  └──────┬───────┘  └──────────────┘  └────────────────┘   │  │
│  │         │                                                  │  │
│  │  ┌──────▼───────┐                                          │  │
│  │  │   Syncer     │  Syncs selected resources between        │  │
│  │  │              │  virtual cluster ←→ host cluster          │  │
│  │  └──────┬───────┘                                          │  │
│  │         │                                                  │  │
│  └─────────┼──────────────────────────────────────────────────┘  │
│            │                                                     │
│            ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Host Pods (scheduled by virtual cluster, run on host)      │ │
│  │  pod-abc-x-team-ns-x-vcluster-team-alpha                   │ │
│  │  pod-def-x-team-ns-x-vcluster-team-alpha                   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Namespace: vcluster-team-beta                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  VIRTUAL CLUSTER (team-beta)                               │  │
│  │  (same structure, completely isolated control plane)        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Key components**:

| Component | Role |
|-----------|------|
| **Virtual API Server** | Handles all kubectl requests for the virtual cluster |
| **Virtual Controller Manager** | Runs controllers (Deployments, ReplicaSets, etc.) inside the virtual cluster |
| **Backing Store** | etcd, SQLite, or PostgreSQL stores virtual cluster state |
| **Syncer** | Translates and copies resources between virtual and host cluster |

### The Syncer: How Resources Flow

When a developer creates a Pod in the virtual cluster, here is what happens:

1. kubectl request hits the **virtual API server**
2. Virtual controller manager creates the Pod object in **virtual etcd**
3. The **syncer** detects the new Pod and creates a corresponding Pod in the **host namespace**
4. The host cluster's kubelet schedules and runs the Pod on a real node
5. Status updates flow back: host Pod status is synced to virtual Pod

The developer sees a normal Kubernetes experience. The host cluster sees Pods in a namespace.

---

## Installation

### Install the vCluster CLI

```bash
# macOS
brew install loft-sh/tap/vcluster

# Linux (amd64)
curl -L -o vcluster "https://github.com/loft-sh/vcluster/releases/latest/download/vcluster-linux-amd64"
chmod +x vcluster
sudo mv vcluster /usr/local/bin/

# Verify installation
vcluster --version
```

### Install via Helm (for automation)

```bash
# Add the Loft Helm repository
helm repo add loft-sh https://charts.loft.sh
helm repo update
```

---

## Creating Virtual Clusters

### Quick Start with CLI

```bash
# Create a virtual cluster named "dev" in a new namespace
vcluster create dev

# This does three things:
# 1. Creates namespace "vcluster-dev" on the host
# 2. Deploys virtual control plane components
# 3. Switches your kubeconfig to the virtual cluster

# Verify you are inside the virtual cluster
kubectl get namespaces
# You will see: default, kube-system, kube-public
# NOT the host cluster namespaces

# Create resources inside the virtual cluster
kubectl create namespace my-app
kubectl create deployment nginx --image=nginx -n my-app
kubectl get pods -n my-app
```

### Create with Helm (GitOps-friendly)

```yaml
# vcluster-team-alpha.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: vcluster-team-alpha
---
# Install via Helm
# helm install team-alpha loft-sh/vcluster \
#   -n vcluster-team-alpha \
#   -f values.yaml
```

```yaml
# values.yaml
controlPlane:
  distro:
    k8s:
      enabled: true
      version: "1.31"
  backingStore:
    etcd:
      embedded:
        enabled: true
  coredns:
    enabled: true
sync:
  toHost:
    pods:
      enabled: true
    services:
      enabled: true
    persistentvolumeclaims:
      enabled: true
  fromHost:
    nodes:
      enabled: true
    storageClasses:
      enabled: true
```

### Connecting to a Virtual Cluster

```bash
# Connect to an existing virtual cluster
vcluster connect dev

# Connect without switching kubeconfig (outputs a kubeconfig file)
vcluster connect dev --update-current=false -- kubectl get pods

# List virtual clusters
vcluster list

# Disconnect (switch back to host cluster)
vcluster disconnect

# Delete a virtual cluster
vcluster delete dev
```

---

## Resource Synchronization

Understanding what syncs and what stays isolated is critical.

### Default Sync Behavior

| Resource | Direction | Behavior |
|----------|-----------|----------|
| **Pods** | virtual → host | Synced. Pods run on host nodes. |
| **Services** | virtual → host | Synced. Services are created on host. |
| **Endpoints** | virtual → host | Synced automatically with Services. |
| **PersistentVolumeClaims** | virtual → host | Synced. Use host storage classes. |
| **ConfigMaps** | virtual → host | Synced (only those referenced by Pods). |
| **Secrets** | virtual → host | Synced (only those referenced by Pods). |
| **Ingresses** | virtual → host | Synced. Use host ingress controller. |
| **Nodes** | host → virtual | Synced (read-only). Virtual cluster sees host nodes. |
| **StorageClasses** | host → virtual | Synced (read-only). |
| **Namespaces** | isolated | Virtual namespaces exist only in virtual etcd. |
| **CRDs** | isolated | Each virtual cluster can have its own CRDs. |
| **RBAC** | isolated | Virtual cluster has its own RBAC. |
| **ServiceAccounts** | isolated | Separate from host ServiceAccounts. |

### Isolation Model

```
ISOLATION BOUNDARY
════════════════════════════════════════════════════════════════════

ISOLATED (per virtual cluster)     SHARED (from host)
─────────────────────────────      ─────────────────────────
CRDs                               Node capacity
RBAC (Roles, ClusterRoles)         Container runtime
Admission webhooks                 CNI (networking)
Namespaces                         CSI (storage)
ServiceAccounts                    Host kernel
API server configuration           Load balancers
Controller manager                 Ingress controller

Each virtual cluster is a FULL Kubernetes API.
Tenants can install Helm charts, CRDs, operators—
without affecting other tenants or the host.
```

---

## Use Cases

### 1. Development Environments

Give every developer (or team) an isolated cluster that spins up in seconds:

```bash
# Developer self-service
vcluster create dev-alice --namespace vcluster-alice
# Alice has her own cluster: CRDs, RBAC, namespaces, the works

vcluster create dev-bob --namespace vcluster-bob
# Bob has his own cluster, completely isolated from Alice
```

### 2. CI/CD Pipeline Isolation

Each CI pipeline run gets a fresh cluster, then tears it down:

```bash
# In your CI pipeline
vcluster create ci-${BUILD_ID} --connect=false
vcluster connect ci-${BUILD_ID} -- kubectl apply -f manifests/
vcluster connect ci-${BUILD_ID} -- kubectl wait --for=condition=ready pod -l app=myapp
vcluster connect ci-${BUILD_ID} -- ./run-integration-tests.sh
vcluster delete ci-${BUILD_ID}
```

### 3. Multi-Tenant Platforms

Platform teams can offer "Cluster as a Service" without provisioning real infrastructure:

```yaml
# Platform API: developer requests a cluster
apiVersion: platform.example.com/v1alpha1
kind: TeamCluster
metadata:
  name: team-payments
spec:
  team: payments
  kubernetesVersion: "1.31"
  resourceQuota:
    cpu: "8"
    memory: "16Gi"
```

### 4. Testing Kubernetes Upgrades

Test workload compatibility with a new Kubernetes version without touching production:

```bash
# Host runs 1.31, test with 1.32
vcluster create upgrade-test \
  --set controlPlane.distro.k8s.version=1.32

# Deploy your workloads, run tests, validate
vcluster connect upgrade-test -- kubectl apply -f production-manifests/
vcluster connect upgrade-test -- ./smoke-tests.sh

# Clean up
vcluster delete upgrade-test
```

---

## Comparison: Namespaces vs vCluster vs Separate Clusters

| Dimension | Namespaces | vCluster | Separate Clusters |
|-----------|------------|----------|-------------------|
| **Isolation level** | Low (shared API, shared CRDs) | High (separate API server) | Complete |
| **CRD isolation** | None (cluster-wide) | Full | Full |
| **RBAC isolation** | Partial (namespace-scoped only) | Full (own ClusterRoles) | Full |
| **Admission webhook isolation** | None | Full | Full |
| **Provisioning speed** | Instant | ~30 seconds | 5-15 minutes |
| **Cost per tenant** | Near zero | Very low (1-2 Pods overhead) | High ($100-2000+/month) |
| **Operational overhead** | Low | Low-Medium | High |
| **Different K8s versions** | No | Yes | Yes |
| **Tenant can install operators** | No | Yes | Yes |
| **Network isolation** | Via NetworkPolicies | Via NetworkPolicies + separate API | Full by default |

**When to use what**:

- **Namespaces**: Trusted teams, simple workloads, no CRD conflicts
- **vCluster**: Untrusted or semi-trusted tenants, teams needing cluster-admin, CI/CD isolation, upgrade testing
- **Separate clusters**: Regulatory requirements, completely different environments (production vs staging), extreme blast radius concerns

---

## Platform Integration

### Self-Service Cluster Provisioning

Combine vCluster with [Backstage](module-7.1-backstage/) for a self-service developer experience:

```
SELF-SERVICE PLATFORM
════════════════════════════════════════════════════════════════════

Developer                    Platform Team
    │                             │
    │  "I need a cluster"         │
    │  (Backstage template)       │
    ▼                             │
┌─────────────┐                   │
│  Backstage  │                   │
│  Template   │                   │
└──────┬──────┘                   │
       │ Creates                  │
       ▼                          ▼
┌─────────────────────────────────────────┐
│  GitOps Repo                            │
│  └─ clusters/team-alpha/vcluster.yaml   │
└──────────────────┬──────────────────────┘
                   │ ArgoCD syncs
                   ▼
┌─────────────────────────────────────────┐
│  Host Cluster                           │
│  └─ vCluster "team-alpha" created       │
└──────────────────┬──────────────────────┘
                   │ Kubeconfig
                   ▼
           Developer accesses
           their virtual cluster
```

This pattern ties directly into the principles covered in [Platform Engineering Discipline](../../../disciplines/core-platform/platform-engineering/)—golden paths, self-service, and reducing cognitive load.

### Resource Quotas on Host

Limit what each virtual cluster can consume on the host:

```yaml
# Apply to the vCluster's host namespace
apiVersion: v1
kind: ResourceQuota
metadata:
  name: vcluster-team-alpha-quota
  namespace: vcluster-team-alpha
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "50"
    services: "20"
    persistentvolumeclaims: "10"
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No resource quotas on host namespace | A single virtual cluster consumes all host resources | Always apply ResourceQuotas to the host namespace |
| Forgetting to sync Ingresses | Services inside vCluster are not reachable externally | Enable ingress sync in vCluster config |
| Running etcd for every vCluster | High memory overhead in large deployments | Use SQLite or embedded etcd for dev clusters, dedicated etcd only for production-grade vClusters |
| Not cleaning up CI vClusters | Orphaned virtual clusters accumulate and waste resources | Set TTL or add cleanup jobs to your CI pipeline |
| Expecting full network isolation by default | Pods from different vClusters can communicate on the host network | Apply NetworkPolicies on the host namespace for true network isolation |
| Syncing too many resources | Performance degradation, unexpected side effects | Start with defaults, add sync rules only as needed |

---

## Quiz

### Question 1
What is the role of the syncer in vCluster architecture?

<details>
<summary>Show Answer</summary>

The **syncer** is the bridge between the virtual cluster and the host cluster. It watches for resources created in the virtual cluster (like Pods, Services, and PVCs) and creates corresponding real resources in the host cluster namespace. It also syncs status updates back from the host to the virtual cluster.

For example, when a developer creates a Deployment in the virtual cluster, the virtual controller manager creates Pods in virtual etcd, then the syncer creates real Pods in the host namespace. The host kubelet runs those Pods, and the syncer copies the status back so `kubectl get pods` in the virtual cluster shows the correct state.

</details>

### Question 2
Why would you choose vCluster over simple namespace-based multi-tenancy?

<details>
<summary>Show Answer</summary>

Namespaces provide only basic isolation. Key limitations:

- **CRDs are cluster-scoped**: One tenant's CRD installation affects all tenants
- **Admission webhooks are cluster-scoped**: A broken webhook blocks all tenants
- **ClusterRoles cannot be scoped**: Tenants cannot have cluster-admin safely
- **No API server isolation**: All tenants share the same API server rate limits

vCluster solves all of these by giving each tenant a **separate API server and control plane**. Tenants can install their own CRDs, operators, admission webhooks, and ClusterRoles without affecting anyone else—while still sharing the underlying compute, networking, and storage of the host cluster.

Use namespaces when tenants are trusted and have simple needs. Use vCluster when tenants need cluster-level permissions or CRD isolation.

</details>

### Question 3
How does vCluster handle Pods? Where do they actually run?

<details>
<summary>Show Answer</summary>

Pods created in a virtual cluster **run on the host cluster's nodes**, not inside the virtual control plane. The flow is:

1. Developer runs `kubectl create deployment nginx` against the virtual API server
2. The virtual controller manager creates Pod objects in virtual etcd
3. The syncer detects these Pods and creates real Pods in the host namespace (e.g., `vcluster-team-alpha`)
4. The host cluster scheduler places them on host nodes
5. The host kubelet runs the containers
6. Pod status syncs back to the virtual cluster

The Pod names are rewritten on the host (e.g., `nginx-abc123-x-default-x-vcluster-dev`) to avoid collisions. The developer sees clean names in their virtual cluster.

</details>

### Question 4
A company runs 20 separate EKS clusters for development teams at $2,000/month each. How would you propose consolidating with vCluster, and what would you need to watch out for?

<details>
<summary>Show Answer</summary>

**Proposal**:
1. Provision 1-2 host EKS clusters (two for regional redundancy)
2. Create one vCluster per team (20 virtual clusters)
3. Apply ResourceQuotas to each host namespace to prevent resource hogging
4. Apply NetworkPolicies for network isolation between vClusters
5. Set up a self-service portal (Backstage template) for cluster creation

**Cost reduction**: From ~$40,000/month to ~$4,000-6,000/month (host cluster costs + overhead).

**Watch out for**:
- **NetworkPolicies**: Must be explicitly configured; vCluster does not isolate network traffic by default
- **Resource quotas**: Without them, one team can starve others
- **Node capacity**: Size host clusters for total workload, add cluster autoscaler
- **Monitoring**: Set up observability on both host and virtual cluster levels
- **Compliance**: Some regulations may require physical cluster separation—vClusters may not satisfy those requirements

</details>

---

## Hands-On Exercise

### Objective
Create a virtual cluster, deploy workloads inside it, and verify isolation from the host.

### Environment Setup

```bash
# Requirement: a running Kubernetes cluster (kind or minikube)
# Create a kind cluster if you do not have one
kind create cluster --name vcluster-host

# Install vCluster CLI (if not already installed)
brew install loft-sh/tap/vcluster
# or: curl -L -o vcluster "https://github.com/loft-sh/vcluster/releases/latest/download/vcluster-linux-amd64" && chmod +x vcluster && sudo mv vcluster /usr/local/bin/
```

### Tasks

**1. Create a virtual cluster**:
```bash
vcluster create my-vcluster
```

**2. Verify isolation**:
```bash
# Inside the virtual cluster - should see only default namespaces
kubectl get namespaces

# Create a namespace and deployment
kubectl create namespace demo
kubectl create deployment web --image=nginx --replicas=2 -n demo
kubectl get pods -n demo
```

**3. Check the host perspective**:
```bash
# Disconnect from vCluster
vcluster disconnect

# On the host, look at the vCluster namespace
kubectl get pods -n vcluster-my-vcluster
# You should see: the vCluster control plane Pods AND
# the synced "web" Pods with rewritten names
```

**4. Create a second virtual cluster and verify isolation**:
```bash
vcluster create my-vcluster-2
kubectl get namespaces
# This cluster has NO "demo" namespace - it is fully isolated

vcluster disconnect
```

**5. Clean up**:
```bash
vcluster delete my-vcluster
vcluster delete my-vcluster-2
```

### Success Criteria
- [ ] Virtual cluster created and accessible via kubectl
- [ ] Namespace and Deployment created inside virtual cluster
- [ ] Host cluster shows synced Pods with rewritten names in the vCluster namespace
- [ ] Second virtual cluster has no visibility into the first
- [ ] Both virtual clusters cleaned up

---

## Further Reading

- [vCluster Documentation](https://www.vcluster.com/docs)
- [vCluster GitHub Repository](https://github.com/loft-sh/vcluster)
- [CNCF Sandbox: vCluster](https://www.cncf.io/projects/vcluster/)
- [Loft Labs Blog: Multi-Tenancy Patterns](https://loft.sh/blog)

## Cross-References

- [Module 7.1: Backstage](module-7.1-backstage/) — Build a self-service portal that provisions vClusters
- [Module 7.2: Crossplane](module-7.2-crossplane/) — Combine with Crossplane for full infrastructure self-service
- [Platform Engineering Discipline](../../../disciplines/core-platform/platform-engineering/) — The principles behind self-service platforms
- [Security Principles](../../../foundations/security-principles/) — Multi-tenancy and isolation theory

---

## Next Module

Continue to [Module 7.1: Backstage](module-7.1-backstage/) to learn how to build an Internal Developer Portal that ties vCluster provisioning into a self-service experience.

---

*"The best cluster is one your developers didn't have to ask for. vCluster makes 'Cluster as a Service' a reality without the infrastructure bill."*
