---
title: "Module 3.5: Cluster API (CAPI)"
slug: platform/toolkits/infrastructure-networking/platforms/module-3.5-cluster-api
sidebar:
  order: 6
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: ~50 minutes

## Overview

It was 2 AM when the Slack alert fired: "Production cluster unreachable." A platform engineer at a mid-sized fintech had been manually upgrading their 50 Kubernetes clusters, one `kubeadm upgrade` at a time. Cluster 37 got a botched etcd migration--wrong flags, no rollback plan. The blast radius? Payment processing for 200,000 users, down for four hours. The post-mortem was brutal: "We treat clusters like pets. We need cattle." That team adopted Cluster API. They never had another manual upgrade incident.

Cluster API (CAPI) brings the declarative, reconciliation-driven model of Kubernetes to Kubernetes itself. You define your clusters as YAML, apply them to a management cluster, and CAPI handles provisioning, scaling, upgrading, and deleting workload clusters across any infrastructure--AWS, Azure, GCP, vSphere, bare metal, even Docker on your laptop.

**What You'll Learn**:
- CAPI architecture: management clusters, workload clusters, providers
- Core resources: Cluster, Machine, MachineDeployment, MachineSet
- ClusterClass for templated, repeatable cluster creation
- Hands-on with Docker provider (CAPD) for local testing
- Infrastructure provider landscape and GitOps integration

**Prerequisites**:
- [Kubernetes Fundamentals](../../../../prerequisites/kubernetes-basics/)
- [kubeadm cluster setup](../../../../k8s/cka/) (understanding of cluster bootstrapping)
- Familiarity with Custom Resource Definitions (CRDs)

---

## Why This Module Matters

Managing one Kubernetes cluster is hard enough. Managing 10 is a full-time job. Managing 50+ without automation is a recipe for outages, configuration drift, and burnout. Cluster API treats clusters as disposable, reproducible infrastructure--the same way Deployments treat Pods. If a cluster drifts, reconcile it. If you need 20 more, declare them.

> **Did You Know?**
>
> - Cluster API was started by the Kubernetes SIG Cluster Lifecycle team in 2018--the same group responsible for kubeadm. They saw teams reinventing cluster provisioning and wanted a universal, declarative solution.
> - CAPI manages over 15,000 production clusters at companies like Deutsche Telekom, Giantswarm, and SUSE. It is a graduated component of the Kubernetes ecosystem with providers for every major cloud and bare-metal platform.
> - The Docker provider (CAPD) creates real multi-node Kubernetes clusters using Docker containers as "machines." This means you can test full cluster lifecycle operations--create, scale, upgrade, delete--on your laptop without spending a cent on cloud resources.
> - ClusterClass, introduced in CAPI v1beta1, lets you define a cluster "template" once and stamp out hundreds of consistent clusters. Think of it as a Helm chart, but for entire Kubernetes clusters.

---

## CAPI Architecture

The central idea: one Kubernetes cluster (the **management cluster**) runs CAPI controllers that provision and manage other Kubernetes clusters (the **workload clusters**).

```
CLUSTER API ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌───────────────────────────────────────────────────────────────┐
│                   MANAGEMENT CLUSTER                          │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                  CAPI CORE CONTROLLERS                  │  │
│  │                                                         │  │
│  │  Cluster Controller    Machine Controller               │  │
│  │  MachineSet Controller MachineDeployment Controller     │  │
│  │  ClusterClass Controller                                │  │
│  └──────────────────────────┬──────────────────────────────┘  │
│                             │                                  │
│  ┌──────────────┐  ┌───────▼────────┐  ┌──────────────────┐  │
│  │  Bootstrap   │  │ Infrastructure │  │  Control Plane   │  │
│  │  Provider    │  │   Provider     │  │    Provider      │  │
│  │  (CABPK)    │  │ (CAPA/CAPZ/..) │  │    (KCP)         │  │
│  │             │  │               │  │                  │  │
│  │ Generates   │  │ Creates VMs/  │  │ Manages etcd +   │  │
│  │ cloud-init  │  │ networks/LBs  │  │ control plane    │  │
│  └──────────────┘  └───────────────┘  └──────────────────┘  │
│                             │                                  │
└─────────────────────────────┼──────────────────────────────────┘
                              │ provisions & manages
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │  Workload    │ │  Workload    │ │  Workload    │
     │  Cluster A   │ │  Cluster B   │ │  Cluster C   │
     │  (prod-east) │ │  (prod-west) │ │  (staging)   │
     │              │ │              │ │              │
     │  CP: 3 nodes │ │  CP: 3 nodes │ │  CP: 1 node  │
     │  W:  50 nodes│ │  W:  30 nodes│ │  W:  5 nodes │
     └──────────────┘ └──────────────┘ └──────────────┘
```

### Provider Types

| Provider Type | Purpose | Examples |
|---|---|---|
| **Infrastructure** | Creates machines, networks, load balancers | CAPA (AWS), CAPZ (Azure), CAPG (GCP), CAPV (vSphere), CAPD (Docker) |
| **Bootstrap** | Generates node boot scripts (cloud-init) | CABPK (kubeadm), Talos, MicroK8s |
| **Control Plane** | Manages control plane nodes and etcd | KubeadmControlPlane (KCP), Talos, k0s |

The beauty is composability: mix any infrastructure provider with any bootstrap provider. Want kubeadm-bootstrapped clusters on AWS? CAPA + CABPK. Want Talos Linux on bare metal? CAPM3 + Talos bootstrap.

---

## Core Resources

CAPI introduces several CRDs that model the cluster lifecycle declaratively.

```
CAPI RESOURCE HIERARCHY
════════════════════════════════════════════════════════════════

  Cluster                          (top-level, owns everything)
    ├── InfrastructureCluster      (provider-specific: AWSCluster, DockerCluster)
    ├── KubeadmControlPlane (KCP)  (manages control plane Machines)
    │     └── Machine              (one per control plane node)
    │           └── InfraMachine   (AWSMachine, DockerMachine)
    └── MachineDeployment          (manages worker nodes, like Deployment)
          └── MachineSet           (like ReplicaSet)
                └── Machine        (one per worker node)
                      └── InfraMachine
```

### Cluster

The root resource. References the infrastructure-specific cluster object and control plane provider. It defines the cluster network CIDRs and links to a `KubeadmControlPlane` (control plane) and an infrastructure-specific cluster resource like `AWSCluster` or `DockerCluster`.

### MachineDeployment

Think of it exactly like a Kubernetes Deployment, but for cluster nodes instead of Pods. It manages MachineSets, which manage Machines, which map to actual VMs or containers. Each Machine references a bootstrap config (how to install K8s) and an infrastructure machine template (what VM specs to use).

Scaling workers? Change `replicas: 5` to `replicas: 10` on the MachineDeployment. CAPI reconciles the difference--creating new Machines, joining them to the cluster automatically.

---

## ClusterClass: Templated Clusters

Creating individual Cluster, MachineDeployment, and KubeadmControlPlane objects for every cluster is verbose. ClusterClass solves this by defining a reusable template. A ClusterClass references templates for the control plane, infrastructure, and worker machine deployments. Once defined, you stamp out clusters with minimal YAML:

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: team-payments-prod
spec:
  topology:
    class: standard-production
    version: v1.31.0
    controlPlane:
      replicas: 3
    workers:
      machineDeployments:
        - class: default-worker
          name: worker-pool
          replicas: 10
```

That is it. Dozens of underlying resources are created from one concise definition.

---

## Infrastructure Providers

| Provider | Code | Infrastructure | Maturity |
|---|---|---|---|
| AWS | CAPA | EC2, ELB, VPC | Stable (v2+) |
| Azure | CAPZ | VMs, VMSS, AKS | Stable (v1+) |
| GCP | CAPG | GCE, GKE | Stable |
| vSphere | CAPV | vSphere VMs | Stable |
| Metal3 | CAPM3 | Bare-metal via Ironic | Stable |
| Docker | CAPD | Docker containers | Development/testing only |
| OpenStack | CAPO | OpenStack VMs | Stable |
| Hetzner | CAPH | Hetzner Cloud + bare-metal | Community |

> Cross-reference: For lightweight distributions that CAPI can bootstrap, see [K3s](../k8s-distributions/module-14.1-k3s/), [Talos](../k8s-distributions/module-14.4-talos/), and [k0s](../k8s-distributions/module-14.2-k0s/). For understanding kubeadm (the default bootstrap provider), see the [CKA track](../../../../k8s/cka/).

---

## Hands-On: CAPI with Docker Provider (CAPD)

No cloud account needed. We use Docker containers as "machines" to experience the full cluster lifecycle locally.

### Prerequisites

```bash
# Install clusterctl (CAPI CLI)
curl -L https://github.com/kubernetes-sigs/cluster-api/releases/latest/download/clusterctl-$(uname -s | tr '[:upper:]' '[:lower:]')-amd64 -o clusterctl
chmod +x clusterctl
sudo mv clusterctl /usr/local/bin/

# Verify
clusterctl version

# You also need: Docker, kind, kubectl
```

### Step 1: Create a Management Cluster

```bash
# Create a kind cluster to serve as management cluster
kind create cluster --name capi-management

# Initialize CAPI with Docker infrastructure provider
clusterctl init --infrastructure docker

# Watch providers come up
k get pods -A --watch
# Wait until all pods in capi-system, capd-system, capi-kubeadm-* are Running
```

### Step 2: Create a Workload Cluster

```bash
# Generate workload cluster manifest using Docker provider
clusterctl generate cluster my-workload \
  --flavor development \
  --kubernetes-version v1.31.0 \
  --control-plane-machine-count 1 \
  --worker-machine-count 2 \
  > my-workload-cluster.yaml

# Review what will be created
k apply -f my-workload-cluster.yaml --dry-run=client

# Apply it
k apply -f my-workload-cluster.yaml
```

### Step 3: Watch the Cluster Come to Life

```bash
# Watch cluster provisioning (this is the fun part)
clusterctl describe cluster my-workload

# Watch machines being created
k get machines -w

# Check cluster status
k get cluster my-workload -o yaml | grep -A 5 status
```

### Step 4: Access the Workload Cluster

```bash
# Get the kubeconfig for the workload cluster
clusterctl get kubeconfig my-workload > my-workload.kubeconfig

# Use it
k --kubeconfig my-workload.kubeconfig get nodes
# You should see 1 control-plane + 2 worker nodes

# Install a CNI (workload clusters need one)
k --kubeconfig my-workload.kubeconfig apply -f \
  https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/calico.yaml
```

### Step 5: Scale Workers

```bash
# Scale from 2 to 4 workers
k patch machinedeployment my-workload-md-0 \
  --type merge \
  -p '{"spec":{"replicas": 4}}'

# Watch new machines appear
k get machines -w
```

### Step 6: Clean Up

```bash
# Delete the workload cluster
k delete cluster my-workload

# CAPI handles teardown: drains nodes, deletes machines, cleans up infra
k get machines -w  # Watch them disappear

# Delete the management cluster
kind delete cluster --name capi-management
```

**Success Criteria**: You created a workload cluster, accessed it, scaled workers, and deleted it--all declaratively from a management cluster.

---

## Cluster Lifecycle Operations

| Operation | How | What Happens |
|---|---|---|
| **Create** | `kubectl apply -f cluster.yaml` | CAPI provisions infrastructure, bootstraps nodes, forms cluster |
| **Scale workers** | Patch MachineDeployment replicas | New Machines created, joined to cluster |
| **Scale control plane** | Patch KubeadmControlPlane replicas (1 to 3) | New CP nodes added, etcd membership updated |
| **Upgrade** | Patch version on KCP + MachineDeployment | Rolling replacement: new node up, old node drained and removed |
| **Delete** | `kubectl delete cluster <name>` | Nodes drained, machines deleted, infrastructure cleaned up |
| **Repair** | Automatic reconciliation | If a Machine fails health checks, CAPI replaces it |

The upgrade strategy deserves emphasis: CAPI does **immutable infrastructure** upgrades. It does not run `kubeadm upgrade` on existing nodes. Instead, it creates a new node at the target version, waits for it to be healthy, then drains and removes the old node. This is safer and more predictable than in-place upgrades.

---

## GitOps Integration with ArgoCD

CAPI resources are just Kubernetes objects. This makes GitOps integration natural.

Store your cluster definitions in Git, point ArgoCD at the management cluster, and every cluster change goes through pull request review.

```yaml
# argocd/cluster-fleet-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: cluster-fleet
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/cluster-fleet
    targetRevision: main
    path: clusters
  destination:
    server: https://kubernetes.default.svc  # management cluster
    namespace: default
  syncPolicy:
    automated:
      prune: false    # IMPORTANT: never auto-delete clusters
      selfHeal: true
```

With this setup, adding a new cluster means committing a YAML file. Upgrading a fleet means bumping the version in Git. Every change is auditable, reviewable, and reversible.

> Cross-reference: See [ArgoCD](../../cicd-delivery/gitops-deployments/module-2.1-argocd/) and [Flux](../../cicd-delivery/gitops-deployments/module-2.3-flux/) for GitOps fundamentals.

---

## CAPI vs Terraform vs Crossplane

| Dimension | Cluster API | Terraform | Crossplane |
|---|---|---|---|
| **Model** | Kubernetes-native CRDs | HCL declarative | Kubernetes-native CRDs |
| **Reconciliation** | Continuous (controller loop) | One-shot (`apply`) | Continuous (controller loop) |
| **Scope** | Kubernetes clusters only | Any infrastructure | Any cloud resource |
| **State** | Kubernetes etcd | Terraform state file | Kubernetes etcd |
| **Drift detection** | Automatic, continuous | Manual (`plan`) | Automatic, continuous |
| **Cluster upgrades** | Built-in rolling upgrades | Manual scripting | Not cluster-aware |
| **Multi-cluster** | First-class (fleet management) | Possible but manual | Can provision clusters but not manage lifecycle |
| **Best for** | Managing Kubernetes clusters at scale | General infrastructure | Cloud resources as K8s APIs |

**When to use what**:
- **CAPI**: You manage multiple Kubernetes clusters and want declarative lifecycle management with rolling upgrades, health checks, and remediation.
- **Terraform**: You need to provision the base infrastructure (VPCs, IAM, DNS) that CAPI clusters run on. Many teams use Terraform for foundations + CAPI for clusters.
- **Crossplane**: You want to expose cloud resources (databases, queues, storage) as Kubernetes APIs for developers. Crossplane and CAPI complement each other well.

---

## Common Mistakes

| Mistake | Why It's Wrong | What To Do Instead |
|---|---|---|
| Running workloads on the management cluster | If the management cluster goes down, you lose the ability to manage all workload clusters | Keep the management cluster dedicated; run workloads on workload clusters only |
| No backup of management cluster | Losing the management cluster means losing cluster definitions and state | Back up etcd and CAPI resources regularly; consider Velero or clusterctl move |
| Skipping CNI installation on workload clusters | CAPI provisions nodes but does not install a CNI; Pods will stay Pending | Always install a CNI (Calico, Cilium) as a post-create step or via ClusterResourceSet |
| Upgrading multiple minor versions at once | CAPI follows Kubernetes skew policy; jumping versions can break clusters | Upgrade one minor version at a time (e.g., 1.30 to 1.31, not 1.29 to 1.31) |
| Using CAPD (Docker provider) in production | CAPD is for development and testing only; Docker "machines" are not production-grade | Use a real infrastructure provider (CAPA, CAPZ, CAPV) for production |
| Ignoring MachineHealthChecks | Without health checks, failed nodes sit broken indefinitely | Define MachineHealthCheck resources to auto-replace unhealthy nodes |
| Setting `prune: true` in ArgoCD for clusters | ArgoCD could delete cluster resources if they disappear from Git | Always set `prune: false` for cluster fleet ArgoCD Applications |

---

## Quiz

Test your understanding of Cluster API concepts.

**Q1: What is the role of the management cluster in CAPI?**

<details>
<summary>Show Answer</summary>

The management cluster runs CAPI controllers (core, infrastructure, bootstrap, control plane providers) that provision and manage workload clusters. It is the "cluster that manages clusters." It stores the desired state of all workload clusters as Kubernetes resources in its own etcd.
</details>

**Q2: How does CAPI handle Kubernetes version upgrades differently from `kubeadm upgrade`?**

<details>
<summary>Show Answer</summary>

CAPI uses an immutable infrastructure approach: it creates a new Machine at the target Kubernetes version, waits for it to become healthy, then cordons, drains, and deletes the old Machine. This is a rolling replacement, not an in-place upgrade. kubeadm upgrade modifies the existing node in place, which carries more risk of leaving the node in a broken state.
</details>

**Q3: What are the three types of CAPI providers and what does each do?**

<details>
<summary>Show Answer</summary>

1. **Infrastructure Provider** - Creates the actual compute resources (VMs, networks, load balancers) on the target platform (AWS, Azure, vSphere, Docker, etc.).
2. **Bootstrap Provider** - Generates the configuration (typically cloud-init scripts) that turns a bare machine into a Kubernetes node. The default is CABPK (kubeadm bootstrap).
3. **Control Plane Provider** - Manages the lifecycle of control plane nodes, including etcd membership. The default is KubeadmControlPlane (KCP).
</details>

**Q4: What problem does ClusterClass solve, and how?**

<details>
<summary>Show Answer</summary>

ClusterClass solves the problem of verbose, repetitive cluster definitions. Without it, creating a cluster requires defining Cluster, KubeadmControlPlane, MachineDeployment, and all their infrastructure-specific counterparts individually. ClusterClass lets you define a reusable template once, then create clusters by referencing the class with only the parameters that differ (name, version, replica counts). It is analogous to a class/instance relationship in object-oriented programming.
</details>

---

## Hands-On Exercise

**Scenario**: Your team manages three environments (dev, staging, prod) and wants to standardize cluster creation with CAPI.

**Tasks**:

1. Set up a management cluster using kind and initialize CAPI with the Docker provider
2. Create a workload cluster named `dev-cluster` with 1 control plane node and 1 worker
3. Verify the cluster is healthy and install a CNI
4. Scale the worker pool to 3 nodes
5. Create a second cluster named `staging-cluster` with the same configuration
6. Delete the `dev-cluster` and verify all resources are cleaned up

**Success Criteria**:
- [ ] Management cluster running with CAPI controllers
- [ ] `dev-cluster` provisioned and accessible via kubeconfig
- [ ] Workers scaled from 1 to 3 (verified with `kubectl get machines`)
- [ ] `staging-cluster` running alongside (two workload clusters managed simultaneously)
- [ ] `dev-cluster` deleted cleanly (no orphaned Machines)

**Bonus Challenge**: Write a ClusterClass that encapsulates your cluster template, then create both clusters using `spec.topology.class` references instead of individual resources.

---

## Current Landscape

- **CAPI** is the standard for declarative Kubernetes lifecycle management
- **Rancher** and **Gardener** are alternative fleet management tools with their own provisioning models
- **EKS Anywhere**, **AKS Arc**, and **GKE On-Prem** use CAPI under the hood for hybrid deployments

## Best Practices

1. **Dedicate the management cluster** -- no application workloads, high availability
2. **Use ClusterClass** -- avoid copy-paste cluster definitions; template everything
3. **Define MachineHealthChecks** -- auto-replace nodes that fail health checks
4. **GitOps your fleet** -- store all cluster definitions in Git
5. **Back up the management cluster** -- use Velero or `clusterctl move`

## Further Reading

- [Cluster API Book (official docs)](https://cluster-api.sigs.k8s.io/)
- [SIG Cluster Lifecycle](https://github.com/kubernetes/community/tree/master/sig-cluster-lifecycle)
- [CAPI Visualizer](https://github.com/Jont828/cluster-api-visualizer) - Visual tool for understanding CAPI resources
- [ClusterClass Deep Dive (KubeCon talk)](https://www.youtube.com/results?search_query=clusterclass+kubecon)

---

**Next Module**: [Module 7.1: Backstage](../module-7.1-backstage/) - Build an Internal Developer Portal to give developers self-service access to these clusters.
