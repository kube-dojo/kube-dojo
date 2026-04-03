---
title: "Module 5.2: Multi-Cluster Control Planes"
slug: on-premises/multi-cluster/module-5.2-multi-cluster-control-planes
sidebar:
  order: 3
---

> **Complexity**: `[ADVANCED]` | Time: 50 minutes
>
> **Prerequisites**: [Module 5.1: Private Cloud Platforms](../module-5.1-private-cloud/), [Module 1.3: Cluster Topology](../../planning/module-1.3-cluster-topology/)

---

## Why This Module Matters

A managed services provider needed to give each of their 40 customers an isolated Kubernetes cluster. They had 12 bare-metal servers. Traditional approach: 40 clusters x 3 control plane nodes = 120 control plane VMs, consuming all 12 servers before a single workload was scheduled.

They deployed Kamaji. Each tenant got a dedicated Kubernetes API server, controller manager, and scheduler -- but all running as pods inside a single management cluster, sharing a central etcd cluster. The 40 control planes consumed 40 GB of RAM total instead of 480 GB. The remaining 11.5 servers were available for workloads.

On-premises hardware is finite. Every control plane node you provision is a node that cannot run workloads. vCluster and Kamaji solve this by virtualizing control planes -- running them as regular pods instead of dedicated machines. This module covers both approaches, plus the traditional kubeadm HA topology with external etcd, so you can choose the right architecture for your constraints.

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Deploy** virtual control planes using vCluster or Kamaji to maximize hardware utilization on constrained bare-metal infrastructure
2. **Design** multi-tenant cluster architectures that provide strong isolation without dedicating physical nodes per tenant
3. **Configure** external etcd topologies for high-availability control planes with proper backup and recovery procedures
4. **Evaluate** virtual vs. dedicated control plane tradeoffs based on tenant count, isolation requirements, and resource constraints

---

## What You'll Learn

- Traditional kubeadm HA topology with external etcd
- vCluster: virtual clusters inside a host cluster
- Kamaji: managed Kubernetes control planes as a service
- Shared vs dedicated control planes on limited hardware
- Cost and resource savings calculations
- When each approach is appropriate

---

## Traditional HA Control Plane (kubeadm)

Before examining virtual control planes, understand what a traditional HA setup requires.

### Stacked etcd Topology

```
┌──────────────────────────────────────────────────────────────┐
│            STACKED ETCD TOPOLOGY (kubeadm default)           │
│                                                                │
│   ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐│
│   │  Control Plane 1 │  │  Control Plane 2 │  │ Control Plane││
│   │                  │  │                  │  │     3        ││
│   │  API Server      │  │  API Server      │  │ API Server   ││
│   │  Controller Mgr  │  │  Controller Mgr  │  │ Controller   ││
│   │  Scheduler       │  │  Scheduler       │  │ Scheduler    ││
│   │  etcd member     │  │  etcd member     │  │ etcd member  ││
│   │  ──────────────  │  │  ──────────────  │  │ ──────────── ││
│   │  4 CPU, 8 GB RAM │  │  4 CPU, 8 GB RAM │  │ 4 CPU, 8 GB ││
│   └─────────────────┘  └─────────────────┘  └──────────────┘│
│                                                                │
│   Total per cluster: 12 CPU, 24 GB RAM                        │
│   5 clusters = 60 CPU, 120 GB RAM (just for control planes)  │
│                                                                │
│   Pro: Simple, kubeadm handles everything                     │
│   Con: Expensive, etcd failure takes down the whole node      │
└──────────────────────────────────────────────────────────────┘
```

### External etcd Topology

```
┌──────────────────────────────────────────────────────────────┐
│            EXTERNAL ETCD TOPOLOGY                             │
│                                                                │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│   │ API Server 1 │ │ API Server 2 │ │ API Server 3 │        │
│   │ Ctrl Mgr     │ │ Ctrl Mgr     │ │ Ctrl Mgr     │        │
│   │ Scheduler    │ │ Scheduler    │ │ Scheduler    │        │
│   │ 2 CPU, 4 GB  │ │ 2 CPU, 4 GB  │ │ 2 CPU, 4 GB  │        │
│   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘        │
│          │                │                │                  │
│          └────────────────┼────────────────┘                  │
│                           │                                    │
│   ┌──────────────┐ ┌──────┴──────┐ ┌──────────────┐         │
│   │   etcd 1     │ │   etcd 2    │ │   etcd 3     │         │
│   │ 2 CPU, 4 GB  │ │ 2 CPU, 4 GB │ │ 2 CPU, 4 GB  │         │
│   │ NVMe SSD     │ │ NVMe SSD    │ │ NVMe SSD     │         │
│   └──────────────┘ └─────────────┘ └──────────────┘         │
│                                                                │
│   Pro: etcd on dedicated nodes with NVMe (best performance)  │
│   Pro: API server failure does not affect etcd                │
│   Con: More nodes to manage (6 instead of 3)                  │
│   Con: More complex setup with kubeadm                        │
│                                                                │
│   Best for: Large clusters (100+ nodes, 5000+ pods)           │
│   or environments where etcd performance is critical.         │
└──────────────────────────────────────────────────────────────┘
```

To use external etcd with kubeadm, configure `etcd.external.endpoints` in the `ClusterConfiguration`, pointing to your 3 etcd nodes with TLS certificates. Then `kubeadm init --config` and `kubeadm join --control-plane` as usual.

---

> **Pause and predict**: A traditional HA control plane with stacked etcd requires 12 CPU and 24 GB RAM per cluster. If you need 10 clusters on 12 bare-metal servers, how much of your total hardware would be consumed by control planes alone? What approach could recover most of that capacity?

## vCluster: Virtual Clusters

vCluster creates lightweight virtual Kubernetes clusters inside a host cluster. Each vCluster has its own API server and data store but shares the host cluster's worker nodes and container runtime.

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    vCLUSTER ARCHITECTURE                      │
│                                                                │
│   Host Cluster (physical nodes + real control plane)          │
│   ┌──────────────────────────────────────────────────────┐   │
│   │                                                       │   │
│   │  Namespace: vcluster-team-a                          │   │
│   │  ┌────────────────────────────┐                      │   │
│   │  │  vCluster "team-a"        │                      │   │
│   │  │                           │                      │   │
│   │  │  ┌─────────┐ ┌────────┐  │                      │   │
│   │  │  │ API Svr  │ │ Syncer │  │  Syncer maps         │   │
│   │  │  │ (k3s or  │ │        │  │  virtual resources   │   │
│   │  │  │ vanilla) │ │        │  │  to host namespace   │   │
│   │  │  └─────────┘ └────────┘  │                      │   │
│   │  │  ┌─────────┐             │                      │   │
│   │  │  │ SQLite/  │             │                      │   │
│   │  │  │ etcd     │             │                      │   │
│   │  │  └─────────┘             │                      │   │
│   │  └────────────────────────────┘                      │   │
│   │                                                       │   │
│   │  Namespace: vcluster-team-b                          │   │
│   │  ┌────────────────────────────┐                      │   │
│   │  │  vCluster "team-b"        │                      │   │
│   │  │  (same structure)          │                      │   │
│   │  └────────────────────────────┘                      │   │
│   │                                                       │   │
│   │  Worker nodes are shared. Pods from vCluster          │   │
│   │  appear as regular pods in the host namespace.        │   │
│   └──────────────────────────────────────────────────────┘   │
│                                                                │
│   Key insight: vCluster pods run on host worker nodes.        │
│   The virtual API server only manages metadata.               │
│   No extra VMs or physical nodes needed.                      │
└──────────────────────────────────────────────────────────────┘
```

### vCluster Deployment

The following commands install the vCluster CLI, create a virtual cluster using the lightweight k3s backend, and demonstrate how resources inside a vCluster are mapped to the host cluster's namespace through the syncer component.

```bash
# Install vCluster CLI
curl -L -o vcluster \
  "https://github.com/loft-sh/vcluster/releases/latest/download/vcluster-linux-amd64"
chmod +x vcluster && sudo mv vcluster /usr/local/bin/

# Create a vCluster with k3s backend (lightest)
vcluster create team-a --namespace vcluster-team-a

# This creates:
# - A StatefulSet with k3s API server
# - A syncer deployment
# - A service for the API endpoint
# Total resources: ~250 MB RAM, 0.5 CPU

# Connect to the vCluster
vcluster connect team-a --namespace vcluster-team-a

# Inside the vCluster, you see a clean cluster
kubectl get namespaces
# NAME              STATUS   AGE
# default           Active   2m
# kube-system       Active   2m
# kube-public       Active   2m

# Create resources inside the vCluster
kubectl create namespace my-app
kubectl -n my-app run nginx --image=nginx

# On the HOST cluster, the pod appears in the vCluster namespace
# (exit vCluster context first)
vcluster disconnect
kubectl -n vcluster-team-a get pods
# nginx-x-my-app-x-team-a   1/1   Running   (synced from vCluster)
```

For production, use vanilla K8s API server instead of k3s by setting `controlPlane.distro.k8s.enabled: true` in a values file, with proper resource limits and an embedded etcd backing store.

---

## Kamaji: Managed Control Planes

Kamaji takes a different approach than vCluster. Instead of running a full virtual cluster inside a namespace, Kamaji runs only the control plane components (API server, controller manager, scheduler) as pods, connecting them to tenant worker nodes that join from outside.

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    KAMAJI ARCHITECTURE                         │
│                                                                │
│   Management Cluster (admin/infra nodes)                      │
│   ┌──────────────────────────────────────────────────────┐   │
│   │                                                       │   │
│   │  Kamaji Controller Manager                           │   │
│   │                                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐                 │   │
│   │  │ Tenant CP 1  │  │ Tenant CP 2  │   Control       │   │
│   │  │              │  │              │   planes as     │   │
│   │  │ API Server   │  │ API Server   │   pods          │   │
│   │  │ Ctrl Manager │  │ Ctrl Manager │                 │   │
│   │  │ Scheduler    │  │ Scheduler    │                 │   │
│   │  └──────┬───────┘  └──────┬───────┘                 │   │
│   │         │                 │                           │   │
│   │  ┌──────┴─────────────────┴──────┐                  │   │
│   │  │     Shared etcd cluster       │   Multi-tenant   │   │
│   │  │  (or per-tenant datastores)   │   data store     │   │
│   │  └───────────────────────────────┘                  │   │
│   └──────────────────────────────────────────────────────┘   │
│                     │                    │                     │
│            ┌────────┴───────┐   ┌────────┴───────┐           │
│            │  Tenant 1      │   │  Tenant 2      │           │
│            │  Worker Nodes  │   │  Worker Nodes  │           │
│            │  (bare metal   │   │  (bare metal   │           │
│            │   or VMs)      │   │   or VMs)      │           │
│            │                │   │                │           │
│            │  kubelet joins │   │  kubelet joins │           │
│            │  tenant CP via │   │  tenant CP via │           │
│            │  API endpoint  │   │  API endpoint  │           │
│            └────────────────┘   └────────────────┘           │
│                                                                │
│   Key difference from vCluster:                               │
│   - Tenant worker nodes are REAL nodes (not shared)           │
│   - Only the control plane is virtualized                     │
│   - Workers join via standard kubeadm join                    │
│   - True network isolation between tenants                    │
└──────────────────────────────────────────────────────────────┘
```

> **Stop and think**: vCluster shares worker nodes between tenants -- pods from different vClusters run on the same physical nodes. Kamaji gives each tenant dedicated worker nodes. Under what circumstances would shared workers be unacceptable, and when is the hardware savings worth the isolation trade-off?

### Kamaji Deployment

The Kamaji operator runs on a management cluster and manages tenant control planes as pods. Each tenant gets a dedicated API server, controller manager, and scheduler, but they share a centralized etcd cluster by default.

```bash
# Install Kamaji operator
helm repo add kamaji https://clastix.github.io/kamaji
helm install kamaji kamaji/kamaji \
  --namespace kamaji-system --create-namespace \
  --set etcd.deploy=true  # Deploy a shared etcd cluster

# Create a tenant control plane
kubectl apply -f - <<EOF
apiVersion: kamaji.clastix.io/v1alpha1
kind: TenantControlPlane
metadata:
  name: tenant-alpha
  namespace: kamaji-system
spec:
  dataStore: default
  controlPlane:
    deployment:
      replicas: 2
      resources:
        apiServer:
          requests:
            cpu: "250m"
            memory: "512Mi"
        controllerManager:
          requests:
            cpu: "125m"
            memory: "256Mi"
        scheduler:
          requests:
            cpu: "125m"
            memory: "256Mi"
  kubernetes:
    version: "v1.32.0"
    kubelet:
      cgroupfs: systemd
  networkProfile:
    port: 6443
    address: "10.0.0.100"  # Tenant API endpoint
    serviceCidr: "10.96.0.0/12"
    podCidr: "10.244.0.0/16"
EOF

After the TenantControlPlane resource is created, Kamaji generates a kubeconfig. Worker nodes then join the tenant cluster using standard `kubeadm join`, connecting to the API server endpoint specified in `networkProfile`.

# Get the tenant kubeconfig
kubectl -n kamaji-system get secret tenant-alpha-admin-kubeconfig \
  -o jsonpath='{.data.admin\.conf}' | base64 -d > tenant-alpha.kubeconfig

# Join a worker node to the tenant cluster
# On the worker node:
kubeadm join 10.0.0.100:6443 \
  --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash>
```

---

## Shared vs Dedicated Control Planes

```
┌──────────────────────────────────────────────────────────────┐
│        CONTROL PLANE STRATEGIES COMPARISON                    │
│                                                                │
│  Strategy       Resources/Cluster  Isolation  Use Case        │
│  ─────────────  ────────────────   ─────────  ─────────────  │
│  Dedicated      12 CPU, 24 GB     Full       Production,     │
│  (kubeadm HA)   (3 nodes)                     compliance      │
│                                                                │
│  vCluster       0.5 CPU, 512 MB   Logical    Dev/test,       │
│  (k3s)          (1 pod)                       previews        │
│                                                                │
│  vCluster       2 CPU, 2 GB       Logical    Multi-tenant    │
│  (vanilla K8s)  (2-3 pods)                    production      │
│                                                                │
│  Kamaji         1 CPU, 1 GB       Network    MSP, managed    │
│  (shared etcd)  (2-3 pods)                    K8s service     │
│                                                                │
│  Kamaji         1.5 CPU, 1.5 GB   Network+   Enterprise      │
│  (per-tenant    (2-3 pods +        Data       multi-tenant   │
│   etcd)          etcd pod)                                     │
└──────────────────────────────────────────────────────────────┘
```

### Resource Savings Calculation

```
Scenario: 10 Kubernetes clusters on 12 bare-metal servers
          Each server: 32 CPU, 128 GB RAM

Traditional (kubeadm HA, stacked etcd):
  Control planes: 10 clusters x 3 nodes = 30 CP nodes
  Per CP node: 4 CPU, 8 GB RAM (reserved for CP components)
  CP total: 120 CPU, 240 GB RAM
  Available hardware: 12 servers x 32 CPU = 384 CPU, 1536 GB RAM
  Remaining for workloads: 264 CPU, 1296 GB RAM
  CP overhead: 31% of CPU, 16% of RAM

vCluster (k3s backend, all on 1 management cluster):
  Management cluster CP: 3 nodes x 4 CPU, 8 GB = 12 CPU, 24 GB
  vCluster pods: 10 x 0.5 CPU, 512 MB = 5 CPU, 5 GB
  CP total: 17 CPU, 29 GB
  Remaining for workloads: 367 CPU, 1507 GB RAM
  CP overhead: 4.4% of CPU, 1.9% of RAM
  Savings vs traditional: 103 CPU, 211 GB RAM

Kamaji (shared etcd):
  Management cluster CP: 3 nodes x 4 CPU, 8 GB = 12 CPU, 24 GB
  Shared etcd: 3 pods x 1 CPU, 2 GB = 3 CPU, 6 GB
  Tenant CPs: 10 x 1 CPU, 1 GB = 10 CPU, 10 GB
  CP total: 25 CPU, 40 GB
  Remaining for workloads: 359 CPU, 1496 GB RAM
  CP overhead: 6.5% of CPU, 2.6% of RAM
  Savings vs traditional: 95 CPU, 200 GB RAM
```

---

## Decision Framework

- **Dedicated workers needed + many clusters (>20)**: Kamaji
- **Dedicated workers needed + few clusters + enough hardware**: kubeadm HA
- **Dedicated workers needed + few clusters + limited hardware**: Kamaji
- **Shared workers + strong multi-tenancy**: vCluster Pro
- **Shared workers + basic isolation**: vCluster OSS (k3s backend, cheapest option)

---

## Did You Know?

- **vCluster was created by Loft Labs** and is one of the fastest-growing CNCF sandbox projects. It can create a fully functional Kubernetes cluster in under 5 seconds because it does not need to provision any infrastructure -- it just starts a pod with an API server and a syncer.

- **Kamaji uses a single etcd cluster for multiple tenants by default**, with key-prefix isolation. Each tenant's data is stored under a unique prefix (e.g., `/tenant-alpha/`). This contrasts with managed Kubernetes services (EKS, GKE, AKS), which provision dedicated etcd instances per tenant cluster to guarantee strict isolation and prevent noisy-neighbor failures.

- **The Kubernetes control plane components are stateless** (except etcd). The API server, controller manager, and scheduler can be restarted at any time without data loss. This is what makes vCluster and Kamaji possible -- you can run these components as regular pods with restart policies.

- **External etcd topology was the original kubeadm HA design.** Stacked etcd (where etcd runs on the same nodes as the API server) was added later as a simplification. Google's GKE and Amazon's EKS both use external etcd clusters, typically with dedicated NVMe-backed instances for maximum performance.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| vCluster for compliance workloads | vCluster shares host kernel, network namespace boundaries can be crossed | Use dedicated clusters or Kamaji with dedicated workers for compliance |
| Shared etcd without backups | etcd corruption affects all tenants simultaneously | Automated etcd snapshots every 30 minutes, tested restore procedure |
| Too many vClusters on one host | Each vCluster API server consumes memory even when idle | Monitor per-vCluster resource usage, set resource limits |
| Kamaji without load balancer | Tenant API endpoints need stable addresses for kubelet join | Use MetalLB or kube-vip for tenant control plane services |
| No network policy between vClusters | Pods in different vClusters can communicate via pod IPs | Apply NetworkPolicies to isolate vCluster namespaces on the host |
| Stacked etcd on slow disks | etcd fsync latency > 10ms causes leader elections, API instability | NVMe SSDs for etcd, or use external etcd on dedicated fast storage |
| Not testing etcd failover | etcd quorum loss = total cluster outage | Regular chaos testing: kill an etcd member, verify recovery |

---

## Quiz

### Question 1
You run a platform for 25 development teams. Each team needs their own Kubernetes cluster to install CRDs, set RBAC policies, and run admission webhooks. You have 8 bare-metal servers. Which approach do you use?

<details>
<summary>Answer</summary>

**vCluster.** The requirements point to vCluster over Kamaji or dedicated clusters:

1. **25 clusters on 8 servers**: Dedicated clusters are impossible (would need 75 control plane nodes minimum). Kamaji could work but is more complex.

2. **CRDs, RBAC, admission webhooks**: These are control plane features. vCluster gives each team a full API server where they can install CRDs and webhooks without affecting other teams.

3. **Development teams**: The workloads are dev/test, not production. vCluster's shared-worker model is acceptable -- dev teams do not need hardware-level isolation.

**Setup**:
- 1 management cluster on 3 servers (control plane)
- 5 servers as worker nodes
- 25 vClusters (k3s backend), each consuming ~250 MB RAM
- Total vCluster overhead: ~6.25 GB RAM (negligible)

```bash
for team in $(seq 1 25); do
  vcluster create "team-${team}" \
    --namespace "vcluster-team-${team}" \
    --set controlPlane.statefulSet.resources.limits.memory=512Mi
done
```
</details>

### Question 2
What is the fundamental architectural difference between vCluster and Kamaji?

<details>
<summary>Answer</summary>

**vCluster virtualizes the entire cluster (control plane + worker view), while Kamaji virtualizes only the control plane.**

**vCluster**:
- Runs API server + syncer inside a host cluster namespace
- Worker nodes are **shared** with the host cluster
- Pods created in a vCluster actually run on host worker nodes
- The syncer translates between vCluster resources and host namespace resources
- Tenant sees virtual nodes (mapped from host nodes)
- Use case: multi-tenancy on shared infrastructure

**Kamaji**:
- Runs API server + controller manager + scheduler as pods in a management cluster
- Worker nodes are **dedicated** per tenant -- real nodes that join via kubeadm
- Pods run on the tenant's own worker nodes, not shared
- No syncer needed -- it is a real cluster with real workers
- Use case: managed Kubernetes service where tenants get their own machines

**Analogy**:
- vCluster is like shared office space (WeWork) -- same building, partitioned
- Kamaji is like a property management company -- they manage the leasing office (control plane) but each tenant has their own building (workers)
</details>

### Question 3
Your Kamaji setup has 15 tenant control planes sharing a single etcd cluster. The etcd cluster's database size is 4 GB. Should you be concerned?

<details>
<summary>Answer</summary>

**Yes, you should be concerned.** etcd has a default space quota of 2 GB (configurable up to a recommended maximum of 8 GB). At 4 GB with 15 tenants, you have already exceeded the default quota and would need an explicitly configured `--quota-backend-bytes` to reach this size.

**Risks**:
- If one tenant creates thousands of ConfigMaps or Secrets, they can push etcd past the quota
- Once the quota is exceeded, etcd becomes read-only -- ALL 15 tenants lose write access simultaneously
- etcd performance degrades as the database grows (compaction takes longer, snapshots are larger)

**Solutions**:

1. **Monitor etcd database size** per tenant (using key-prefix metrics):
   ```bash
   etcdctl endpoint status --write-out=table
   # Check DB SIZE column
   ```

2. **Set per-tenant resource quotas** in Kamaji to limit the number of objects:
   ```yaml
   spec:
     resourceQuotas:
       items:
         - hard:
             configmaps: "100"
             secrets: "100"
             services: "50"
   ```

3. **Consider per-tenant etcd** for tenants that need more space:
   ```yaml
   spec:
     dataStore: tenant-alpha-etcd  # Dedicated etcd
   ```

4. **Enable etcd compaction** to reclaim space from deleted keys:
   ```bash
   etcdctl compact $(etcdctl endpoint status -w json | jq '.[0].Status.header.revision')
   etcdctl defrag
   ```
</details>

### Question 4
You need to run 3 production Kubernetes clusters with strict PCI-DSS compliance. Each cluster handles credit card data. Can you use vCluster?

<details>
<summary>Answer</summary>

**No. vCluster is not appropriate for PCI-DSS compliance with credit card data.**

PCI-DSS requires:
- **Network segmentation**: Cardholder data environment (CDE) must be isolated. vCluster pods share the host network stack -- NetworkPolicies help but are not considered sufficient segmentation for PCI.
- **Unique system components**: PCI requires dedicated system components for the CDE. Shared worker nodes violate this requirement.
- **Access control**: vCluster shares the host kubelet, container runtime, and kernel. A container escape in one vCluster could access another tenant's data.

**Correct approach for PCI-DSS**:
1. **Dedicated clusters** (kubeadm HA) on isolated hardware for each PCI scope
2. **Kamaji** with dedicated worker nodes per tenant -- control planes are shared but workers are physically isolated
3. Physical network segmentation (VLANs, firewalls) between clusters

**Kamaji can work** because:
- Each tenant has its own worker nodes (physical isolation)
- The management cluster does not process cardholder data
- Network segmentation is between tenant worker networks, not namespaces

```
PCI scope: Tenant workers only (dedicated hardware)
Non-PCI scope: Kamaji management cluster (shared, no card data)
```
</details>

---

## Hands-On Exercise: Deploy vCluster

```bash
# Create a kind cluster to act as the host
kind create cluster --name host-cluster

# Install vCluster CLI
curl -L -o vcluster \
  "https://github.com/loft-sh/vcluster/releases/latest/download/vcluster-linux-amd64"
chmod +x vcluster && sudo mv vcluster /usr/local/bin/

# Create two vClusters simulating multi-tenancy
vcluster create team-alpha --namespace vc-alpha
vcluster create team-beta --namespace vc-beta

# Connect to team-alpha
vcluster connect team-alpha --namespace vc-alpha

# Verify: clean cluster with no other tenant's resources
kubectl get namespaces
kubectl get nodes

# Create a deployment inside team-alpha
kubectl create namespace app
kubectl -n app create deployment nginx --image=nginx --replicas=2
kubectl -n app get pods

# Disconnect and connect to team-beta
vcluster disconnect
vcluster connect team-beta --namespace vc-beta

# Verify: team-beta sees a different clean cluster
kubectl get namespaces
# No "app" namespace -- that belongs to team-alpha

# Disconnect and check the host cluster
vcluster disconnect

# On the host, both vCluster pods are visible
kubectl get pods -n vc-alpha
# nginx-xxx-x-app-x-team-alpha   1/1   Running

kubectl get pods -n vc-beta
# (no nginx pods -- team-beta has no deployments)

# Cleanup
vcluster delete team-alpha --namespace vc-alpha
vcluster delete team-beta --namespace vc-beta
kind delete cluster --name host-cluster
```

### Success Criteria

- [ ] Two vClusters created in the same host cluster
- [ ] Each vCluster shows an independent namespace list
- [ ] Resources created in one vCluster are invisible from the other
- [ ] Host cluster shows synced pods in the vCluster namespaces
- [ ] Understood the syncer pattern (virtual resources mapped to host namespace)

---

## Next Module

Continue to [Module 5.3: Cluster API on Bare Metal](../module-5.3-cluster-api-bare-metal/) to learn how to manage Kubernetes cluster lifecycle declaratively using Cluster API with Metal3 and vSphere providers.
