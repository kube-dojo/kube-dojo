---
title: "Module 2.4: Declarative Bare Metal with Cluster API"
slug: on-premises/provisioning/module-2.4-declarative-bare-metal
sidebar:
  order: 5
---

> **Complexity**: `[COMPLEX]` | Time: 60 minutes
>
> **Prerequisites**: [Module 2.3: Immutable OS](../module-2.3-immutable-os/), [Cluster API](../../platform/toolkits/infrastructure-networking/platforms/module-3.5-cluster-api/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Implement** Cluster API with Metal3 or Sidero providers to declaratively provision bare-metal Kubernetes clusters
2. **Configure** a bare-metal host inventory with BMC credentials, hardware profiles, and network templates
3. **Deploy** new Kubernetes clusters using `kubectl apply` with version-controlled YAML manifests
4. **Design** a GitOps-driven cluster lifecycle workflow that covers provisioning, scaling, and decommissioning

---

## Why This Module Matters

A financial services company with 8 Kubernetes clusters across two datacenters managed their infrastructure with a combination of Ansible playbooks, shell scripts, and a shared spreadsheet tracking which server was in which cluster. Creating a new cluster took 3 days: 1 day to allocate servers (manually checking the spreadsheet), 1 day to PXE boot and install the OS, and 1 day to run kubeadm and configure networking. Decommissioning a cluster was worse — nobody was sure which servers could be safely wiped because the spreadsheet was 4 months out of date.

When they needed to spin up an emergency cluster for a regulatory audit, it took 5 days instead of the promised 1. The CTO asked: "Why can't we create a cluster as easily as we create a pod?" The answer was that their bare metal had no declarative API — no equivalent of `kubectl apply -f cluster.yaml`.

Cluster API (CAPI) with bare metal providers (Metal3/Sidero) solves this by treating physical servers like cloud instances. You define a cluster in YAML, apply it, and the system provisions hardware, installs the OS, bootstraps Kubernetes, and joins nodes — all declaratively, all auditable, all version-controlled in Git.

> **The Valet Parking Analogy**
>
> Without Cluster API, provisioning bare metal is like parking your own car in a multi-story garage: you walk around looking for a space, park, and try to remember where you left it. With Cluster API, it is valet parking: you hand over the keys (hardware inventory), say what you need ("3 control planes, 5 workers"), and the valet (CAPI) handles everything. When you are done, you get your car back (server released to the pool).

---

## What You'll Learn

- How Cluster API extends Kubernetes to manage infrastructure
- Metal3 (CAPM3): IPMI/Redfish-based bare metal provisioning
- Sidero: Talos-native bare metal management
- Hardware inventory and machine lifecycle
- GitOps-driven cluster lifecycle (create, upgrade, scale, delete)
- Multi-cluster management from a single management cluster

---

## Cluster API Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           CLUSTER API ON BARE METAL                          │
│                                                               │
│  ┌────────────────────────────────────────────┐             │
│  │        Management Cluster                   │             │
│  │                                             │             │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │             │
│  │  │ CAPI     │  │ Bootstrap│  │ Infra    │ │             │
│  │  │Controller│  │ Provider │  │ Provider │ │             │
│  │  │          │  │ (Talos/  │  │ (Metal3/ │ │             │
│  │  │ Manages  │  │  kubeadm)│  │  Sidero) │ │             │
│  │  │ Cluster, │  │          │  │          │ │             │
│  │  │ Machine  │  │ Generates│  │ Provisions│ │             │
│  │  │ CRDs     │  │ bootstrap│  │ bare     │ │             │
│  │  │          │  │ config   │  │ metal    │ │             │
│  │  └──────────┘  └──────────┘  └──────────┘ │             │
│  └──────────────────┬─────────────────────────┘             │
│                     │ Provisions                             │
│         ┌───────────▼───────────┐                           │
│         │   Workload Cluster    │                           │
│         │                       │                           │
│         │  ┌────┐ ┌────┐ ┌────┐│                           │
│         │  │CP-1│ │CP-2│ │CP-3││                           │
│         │  └────┘ └────┘ └────┘│                           │
│         │  ┌────┐ ┌────┐ ┌────┐│                           │
│         │  │W-1 │ │W-2 │ │W-3 ││                           │
│         │  └────┘ └────┘ └────┘│                           │
│         └───────────────────────┘                           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Key CRDs

| CRD | Purpose |
|-----|---------|
| `Cluster` | Defines a K8s cluster (name, version, networking) |
| `Machine` | Represents a single node (control plane or worker) |
| `MachineDeployment` | Manages a set of worker machines (like a Deployment for pods) |
| `MachineHealthCheck` | Auto-remediation for unhealthy nodes |
| `BareMetalHost` (Metal3) | Represents a physical server |
| `ServerClass` (Sidero) | Groups servers by hardware capabilities |

---

## Metal3 (CAPM3)

Metal3 uses IPMI/Redfish to control bare metal servers. It integrates with Ironic (the OpenStack bare metal provisioner) to handle PXE boot, OS installation, and machine lifecycle.

### Metal3 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    METAL3 STACK                               │
│                                                               │
│  Management Cluster                                          │
│  ┌──────────────────────────────────────────┐               │
│  │  ┌──────────────┐  ┌──────────────┐      │               │
│  │  │ CAPM3        │  │ Ironic       │      │               │
│  │  │ (controller) │  │ (provisioner)│      │               │
│  │  └──────┬───────┘  └──────┬───────┘      │               │
│  │         │                  │               │               │
│  │  ┌──────▼──────────────────▼──────┐       │               │
│  │  │     BareMetalHost CRDs         │       │               │
│  │  │                                │       │               │
│  │  │  bmh-01: available             │       │               │
│  │  │  bmh-02: provisioned (cp-1)    │       │               │
│  │  │  bmh-03: provisioned (cp-2)    │       │               │
│  │  │  bmh-04: provisioning...       │       │               │
│  │  └────────────────────────────────┘       │               │
│  └──────────────────────────────────────────┘               │
│                     │                                        │
│                     │ IPMI/Redfish                           │
│                     ▼                                        │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                      │
│  │ BMC  │ │ BMC  │ │ BMC  │ │ BMC  │                      │
│  │srv-01│ │srv-02│ │srv-03│ │srv-04│                      │
│  └──────┘ └──────┘ └──────┘ └──────┘                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### BareMetalHost Definition

```yaml
apiVersion: metal3.io/v1alpha1
kind: BareMetalHost
metadata:
  name: server-01
  namespace: metal3
spec:
  online: true
  bootMACAddress: "aa:bb:cc:dd:ee:01"
  bmc:
    address: ipmi://10.0.100.10
    credentialsName: server-01-bmc-credentials
  rootDeviceHints:
    deviceName: /dev/sda
  # Hardware profile auto-detected during inspection
---
apiVersion: v1
kind: Secret
metadata:
  name: server-01-bmc-credentials
  namespace: metal3
type: Opaque
data:
  username: YWRtaW4=  # admin
  password: cGFzc3dvcmQ=  # password
```

### Machine Lifecycle States

```
┌─────────────────────────────────────────────────────────────┐
│           BAREMETAL HOST LIFECYCLE                            │
│                                                               │
│  Registering → Inspecting → Available → Provisioning         │
│                                            │                 │
│                                            ▼                 │
│                                        Provisioned           │
│                                            │                 │
│                                            ▼                 │
│                                     Deprovisioning           │
│                                            │                 │
│                                            ▼                 │
│                                        Available             │
│                                    (ready for reuse)         │
│                                                               │
│  Registering: BMC credentials verified                      │
│  Inspecting: Hardware inventory (CPU, RAM, disks, NICs)     │
│  Available: Ready for cluster allocation                     │
│  Provisioning: PXE booting, OS installing                   │
│  Provisioned: Running as K8s node                           │
│  Deprovisioning: Wiping disks, returning to pool            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Sidero (Talos-Native)

Sidero is Sidero Labs' bare metal provider for Cluster API, designed specifically for Talos Linux. It is simpler than Metal3 (no Ironic dependency) and uses IPMI/Redfish directly.

### Sidero vs Metal3

| Feature | Metal3 (CAPM3) | Sidero |
|---------|---------------|--------|
| OS support | Any (Ubuntu, Flatcar, etc.) | Talos Linux only |
| Provisioner | Ironic (complex, OpenStack heritage) | Built-in (simpler) |
| BMC protocol | IPMI, Redfish, iDRAC, iLO | IPMI, Redfish |
| Server discovery | Manual BareMetalHost CRDs | Auto-discovery via DHCP |
| Image delivery | Ironic Python Agent (IPA) | Talos PXE image |
| Complexity | Higher (Ironic is a large system) | Lower (fewer moving parts) |
| Maturity | Older, more tested | Newer, less battle-tested |
| Best for | Multi-OS environments | Talos-only environments |

### Sidero Server Discovery

```yaml
# Sidero auto-discovers servers when they PXE boot
# Servers appear as Server CRDs automatically

# Check discovered servers
kubectl get servers -n sidero-system
# NAME                                   HOSTNAME      BMC              ACCEPTED
# 00000000-0000-0000-0000-aabbccddeef1   server-01     10.0.100.10     false
# 00000000-0000-0000-0000-aabbccddeef2   server-02     10.0.100.11     false

# Accept a server into the pool
kubectl patch server 00000000-0000-0000-0000-aabbccddeef1 \
  --type merge -p '{"spec":{"accepted": true}}'

# Group servers by capability
apiVersion: metal.sidero.dev/v1alpha2
kind: ServerClass
metadata:
  name: worker-large
spec:
  qualifiers:
    cpu:
      - manufacturer: "AMD"
        version: "EPYC.*"
    systemInformation:
      - manufacturer: "Dell Inc."
  selector:
    matchLabels:
      rack: "rack-a"
```

### Creating a Cluster with Sidero

```yaml
# Define the workload cluster
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: production
  namespace: default
spec:
  clusterNetwork:
    pods:
      cidrBlocks: ["10.244.0.0/16"]
    services:
      cidrBlocks: ["10.96.0.0/12"]
  controlPlaneRef:
    apiVersion: controlplane.cluster.x-k8s.io/v1alpha3
    kind: TalosControlPlane
    name: production-cp
  infrastructureRef:
    apiVersion: infrastructure.cluster.x-k8s.io/v1alpha3
    kind: MetalCluster
    name: production
---
# Control plane (3 nodes from 'control-plane' server class)
apiVersion: controlplane.cluster.x-k8s.io/v1alpha3
kind: TalosControlPlane
metadata:
  name: production-cp
spec:
  replicas: 3
  version: v1.35.0
  infrastructureTemplate:
    apiVersion: infrastructure.cluster.x-k8s.io/v1alpha3
    kind: MetalMachineTemplate
    name: production-cp
  controlPlaneConfig:
    controlplane:
      generateType: controlplane
---
# Worker machines (5 nodes from 'worker-large' server class)
apiVersion: cluster.x-k8s.io/v1beta1
kind: MachineDeployment
metadata:
  name: production-workers
spec:
  replicas: 5
  clusterName: production
  selector:
    matchLabels:
      cluster.x-k8s.io/cluster-name: production
  template:
    metadata:
      labels:
        cluster.x-k8s.io/cluster-name: production
    spec:
      clusterName: production
      version: v1.35.0
      bootstrap:
        configRef:
          apiVersion: bootstrap.cluster.x-k8s.io/v1alpha3
          kind: TalosConfigTemplate
          name: production-workers
      infrastructureRef:
        apiVersion: infrastructure.cluster.x-k8s.io/v1alpha3
        kind: MetalMachineTemplate
        name: production-workers
---
apiVersion: infrastructure.cluster.x-k8s.io/v1alpha3
kind: MetalMachineTemplate
metadata:
  name: production-workers
spec:
  template:
    spec:
      serverClassRef:
        apiVersion: metal.sidero.dev/v1alpha2
        kind: ServerClass
        name: worker-large
```

```bash
# Apply the cluster definition
kubectl apply -f production-cluster.yaml

# Watch the provisioning
kubectl get machines -w
# NAME                          PHASE
# production-cp-abc12           Provisioning
# production-cp-def34           Pending
# production-cp-ghi56           Pending
# production-workers-jkl78      Pending
# ...

# After ~10-15 minutes:
# production-cp-abc12           Running
# production-cp-def34           Running
# production-cp-ghi56           Running
# production-workers-jkl78      Running
# production-workers-mno90      Running

# Get the workload cluster kubeconfig
kubectl get secret production-kubeconfig -o jsonpath='{.data.value}' | base64 -d > production.kubeconfig
kubectl --kubeconfig production.kubeconfig get nodes
```

---

## Machine Health Checks

Automatically remediate failed nodes by replacing them with fresh hardware from the pool:

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: MachineHealthCheck
metadata:
  name: production-worker-health
spec:
  clusterName: production
  selector:
    matchLabels:
      cluster.x-k8s.io/deployment-name: production-workers
  unhealthyConditions:
    - type: Ready
      status: "False"
      timeout: 5m
    - type: Ready
      status: Unknown
      timeout: 5m
  maxUnhealthy: "40%"  # Don't remediate if >40% are unhealthy (likely a systemic issue)
  nodeStartupTimeout: 10m
```

When a node is unhealthy for >5 minutes:
1. CAPI marks the Machine for deletion
2. The infrastructure provider deprovisions the bare metal host (wipes disk)
3. The host returns to "Available" in the pool
4. CAPI creates a new Machine, which provisions a new host
5. The new node joins the cluster automatically

---

## GitOps-Driven Cluster Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│           GITOPS CLUSTER LIFECYCLE                           │
│                                                               │
│  Git Repository                                              │
│  ├── clusters/                                               │
│  │   ├── production/                                         │
│  │   │   ├── cluster.yaml        (Cluster definition)       │
│  │   │   ├── control-plane.yaml  (TalosControlPlane)        │
│  │   │   ├── workers.yaml        (MachineDeployment)        │
│  │   │   └── health-checks.yaml  (MachineHealthCheck)       │
│  │   ├── staging/                                            │
│  │   │   └── ...                                             │
│  │   └── dev/                                                │
│  │       └── ...                                             │
│  └── infrastructure/                                         │
│      ├── servers.yaml            (BareMetalHost inventory)  │
│      └── server-classes.yaml     (ServerClass definitions)  │
│                                                               │
│  ArgoCD/Flux watches → applies to management cluster        │
│  Management cluster → provisions workload clusters          │
│                                                               │
│  To create a cluster: git commit + push                     │
│  To scale workers: change replicas, git push                │
│  To upgrade K8s: change version, git push                   │
│  To delete a cluster: remove YAML, git push                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Cluster API was created by Kubernetes SIG Cluster Lifecycle** specifically because every cloud provider had built their own incompatible cluster management tooling. CAPI provides a single API that works across AWS, Azure, GCP, vSphere, and bare metal.

- **Metal3 stands for "Metal Kubed"** (Metal^3). It was created by Red Hat and is the bare metal infrastructure provider used by OpenShift's Assisted Installer for on-premises deployments.

- **Sidero was created by the same team that built Talos Linux** (Sidero Labs). The name comes from the Greek word for "iron" — fitting for bare metal management.

- **The largest known Cluster API deployment manages over 4,000 clusters** across multiple infrastructure providers. Organizations like Deutsche Telekom and SAP use CAPI to manage their multi-cluster Kubernetes platforms at enterprise scale.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No management cluster HA | Management cluster dies = cannot manage anything | Run 3-node HA management cluster with etcd backup |
| BMC credentials in plain text | Security risk | Use Kubernetes secrets + external secrets operator |
| No server pool buffer | MachineHealthCheck tries to replace but no servers available | Maintain 2-3 spare servers in the pool |
| Skipping hardware inspection | Deploying on servers with failed RAM or disks | Always let CAPI inspect hardware before marking available |
| No disk wipe on deprovision | Previous tenant's data visible to next | Enable secure erase in Metal3/Sidero deprovisioning |
| Single management cluster | Management cluster failure = total loss of control | Backup management cluster state; consider multi-site mgmt |
| Not using GitOps | Cluster definitions are imperative and unauditable | Store all CAPI YAMLs in Git; deploy via ArgoCD/Flux |

---

## Quiz

### Question 1
What happens if the management cluster goes down? Can the workload clusters still function?

<details>
<summary>Answer</summary>

**Yes, workload clusters continue to function normally.** The management cluster only manages the lifecycle (creation, scaling, upgrades, health checks) of workload clusters. Once a workload cluster is provisioned, it operates independently — its control plane, workers, and workloads are self-contained.

However, you lose:
- **Scaling**: Cannot add/remove worker nodes
- **Upgrades**: Cannot trigger K8s or OS upgrades
- **Auto-remediation**: MachineHealthChecks stop working (unhealthy nodes are not replaced)
- **New cluster creation**: Cannot provision new clusters

**Mitigation**: Run the management cluster with 3-node HA, back up its etcd regularly, and consider a standby management cluster in a second datacenter.
</details>

### Question 2
You need to upgrade Kubernetes from 1.34 to 1.35 on a 50-node production cluster managed by Cluster API. How does this work?

<details>
<summary>Answer</summary>

**Rolling upgrade via CAPI:**

1. **Update the version field** in the control plane and MachineDeployment YAMLs:
   ```yaml
   # TalosControlPlane — version is at spec.version
   spec:
     version: v1.35.0  # was v1.34.0

   # MachineDeployment — version is at spec.template.spec.version
   spec:
     template:
       spec:
         version: v1.35.0  # was v1.34.0
   ```

2. **Apply** (or Git push if using GitOps). CAPI detects the version change.

3. **CAPI performs a rolling update:**
   - Creates a new Machine with v1.35.0
   - Waits for it to join the cluster and become Ready
   - Cordons and drains an old v1.34.0 Machine
   - Deletes the old Machine (hardware returns to pool)
   - Repeats until all machines are upgraded

4. **Control plane upgrades first**, then workers.

This is exactly like a Deployment rollout — CAPI manages Machine objects the same way the Deployment controller manages Pods. The `maxSurge` and `maxUnavailable` settings on MachineDeployment control the rollout speed.

**Key consideration on bare metal**: This requires spare servers in the pool. CAPI needs to provision a new machine before deprovisioning the old one (surge). If your pool has no spare servers, the upgrade blocks.
</details>

### Question 3
Compare Metal3 and Sidero. When would you choose each?

<details>
<summary>Answer</summary>

**Metal3:**
- Supports any OS (Ubuntu, Flatcar, RHEL, etc.)
- Uses Ironic (OpenStack heritage) — more complex but battle-tested
- Backed by Red Hat, used in OpenShift bare metal deployments
- Better for multi-OS environments or organizations already using OpenStack
- More mature ecosystem and documentation

**Sidero:**
- Talos Linux only (no other OS support)
- Simpler architecture (no Ironic dependency)
- Auto-discovers servers via PXE (no manual BareMetalHost creation)
- ServerClass grouping for hardware-aware scheduling
- Best for all-Talos environments where simplicity is valued

**Decision**: If you chose Talos Linux in Module 2.3, use Sidero. If you need Ubuntu/Flatcar/RHEL, use Metal3.
</details>

### Question 4
How do you handle a server with a failed disk in a Cluster API-managed cluster?

<details>
<summary>Answer</summary>

**Automatic remediation via MachineHealthCheck:**

1. The disk failure causes kubelet to report NotReady (or the node stops responding entirely).

2. MachineHealthCheck detects the `Ready=False` condition persisting beyond the timeout (e.g., 5 minutes).

3. CAPI marks the Machine for deletion.

4. The infrastructure provider (Metal3/Sidero):
   - Deprovisions the server (marks as "needs maintenance")
   - The server does NOT return to the available pool (bad hardware)

5. CAPI creates a new Machine, which is provisioned on a healthy server from the pool.

6. The new node joins the cluster and workloads are scheduled on it.

**Manual steps still needed:**
- Someone must physically replace the failed disk
- After repair, re-register the server (update BareMetalHost or re-PXE for Sidero)
- The server goes through inspection and returns to the available pool

**This is why spare servers matter.** If your pool is empty, the MachineHealthCheck cannot create a replacement, and the unhealthy machine stays in the cluster.
</details>

---

## Hands-On Exercise: Cluster API with Docker (Simulation)

**Task**: Use Cluster API with the Docker provider to simulate the bare metal workflow.

> **Note**: The Docker provider is CAPI's testing/development provider. It creates "machines" as Docker containers. The workflow is identical to bare metal — only the infrastructure layer differs.

```bash
# Install clusterctl
curl -L https://github.com/kubernetes-sigs/cluster-api/releases/latest/download/clusterctl-linux-amd64 -o clusterctl
chmod +x clusterctl && sudo mv clusterctl /usr/local/bin/

# Create a kind cluster as the management cluster
kind create cluster --name capi-mgmt

# Initialize CAPI with Docker provider
clusterctl init --infrastructure docker

# Generate a workload cluster manifest
clusterctl generate cluster demo-cluster \
  --infrastructure docker \
  --kubernetes-version v1.35.0 \
  --control-plane-machine-count 1 \
  --worker-machine-count 2 \
  > demo-cluster.yaml

# Apply the cluster definition
kubectl apply -f demo-cluster.yaml

# Watch machines being provisioned
kubectl get machines -w

# Get the workload cluster kubeconfig
clusterctl get kubeconfig demo-cluster > demo.kubeconfig

# Verify the workload cluster
kubectl --kubeconfig demo.kubeconfig get nodes

# Scale workers
kubectl patch machinedeployment demo-cluster-md-0 \
  --type merge -p '{"spec":{"replicas": 4}}'

# Watch new machines appear
kubectl get machines -w

# Cleanup
kubectl delete cluster demo-cluster
kind delete cluster --name capi-mgmt
```

### Success Criteria
- [ ] Management cluster created (kind)
- [ ] CAPI initialized with Docker provider
- [ ] Workload cluster provisioned (1 CP + 2 workers)
- [ ] kubeconfig retrieved and kubectl works against workload cluster
- [ ] Workers scaled from 2 to 4
- [ ] Cluster deleted cleanly (all machines deprovisioned)

---

## Next Module

Continue to [Module 3.1: Datacenter Network Architecture](../networking/module-3.1-datacenter-networking/) to learn about spine-leaf topology, VLANs, and network design for on-premises Kubernetes.
