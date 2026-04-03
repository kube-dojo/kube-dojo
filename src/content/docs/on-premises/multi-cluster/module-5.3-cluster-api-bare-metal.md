---
title: "Module 5.3: Cluster API on Bare Metal"
slug: on-premises/multi-cluster/module-5.3-cluster-api-bare-metal
sidebar:
  order: 4
---

> **Complexity**: `[ADVANCED]` | Time: 50 minutes
>
> **Prerequisites**: [Module 5.2: Multi-Cluster Control Planes](../module-5.2-multi-cluster-control-planes/), [Module 2.4: Declarative Bare Metal](../../provisioning/module-2.4-declarative-bare-metal/)

---

## Why This Module Matters

A telecommunications company managed 60 Kubernetes clusters across 15 data centers. Each cluster was provisioned manually: an engineer would PXE-boot servers, install the OS, run kubeadm, configure CNI, and hand the cluster to a team. Provisioning took 3 days per cluster. When a node failed, the replacement process took 4-8 hours because the engineer had to physically identify the server, reconfigure BIOS settings, reinstall the OS, and rejoin the cluster.

They adopted Cluster API with the Metal3 provider (CAPM3). Now, provisioning a new cluster is a `kubectl apply` of a YAML manifest. Node failures trigger automatic remediation: MachineHealthCheck detects the unhealthy node, deprovisions it, and provisions a replacement from the bare-metal inventory -- all without human intervention. The 3-day provisioning cycle dropped to 45 minutes. The 4-8 hour node replacement dropped to 15 minutes.

Cluster API (CAPI) treats Kubernetes clusters as declarative resources, just like Deployments or Services. You define the desired state (3 control plane nodes, 10 workers, Kubernetes v1.32) and CAPI makes it happen. On bare metal, this means integrating with BMC (Baseboard Management Controller) protocols to power on servers, PXE-boot them, install an OS, and join them to the cluster -- all automatically.

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Implement** Cluster API with Metal3 (CAPM3) to declaratively provision and manage bare-metal Kubernetes clusters
2. **Configure** MachineHealthChecks for automatic node failure detection and remediation via BMC power cycling
3. **Deploy** a bare-metal inventory management system with BareMetalHost resources, hardware inspection, and firmware configuration
4. **Design** a multi-cluster lifecycle pipeline that handles provisioning, upgrades, scaling, and decommissioning through Git

---

## What You'll Learn

- Cluster API architecture and core concepts
- CAPM3 (Metal3): bare-metal infrastructure provider
- CAPV: vSphere infrastructure provider
- BareMetalHost inventory management
- MachineHealthCheck for automatic node remediation
- GitOps-driven cluster lifecycle with Flux or ArgoCD
- Declarative cluster upgrades and scaling

---

## Cluster API Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                 CLUSTER API ARCHITECTURE                      │
│                                                                │
│   Management Cluster                                          │
│   ┌──────────────────────────────────────────────────────┐   │
│   │                                                       │   │
│   │  CAPI Core Controllers:                              │   │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────────┐ │   │
│   │  │ Cluster    │  │ Machine    │  │ MachineHealth  │ │   │
│   │  │ Controller │  │ Controller │  │ Check Ctrl     │ │   │
│   │  └────────────┘  └────────────┘  └────────────────┘ │   │
│   │                                                       │   │
│   │  Infrastructure Provider (e.g., Metal3):             │   │
│   │  ┌────────────────────────────────────────────────┐  │   │
│   │  │ Metal3Cluster    Metal3Machine                 │  │   │
│   │  │ Controller       Controller                    │  │   │
│   │  │                                                │  │   │
│   │  │ Ironic (bare-metal provisioner)               │  │   │
│   │  │ - IPMI/Redfish for power management           │  │   │
│   │  │ - PXE boot for OS installation                │  │   │
│   │  │ - Inspection for hardware inventory           │  │   │
│   │  └────────────────────────────────────────────────┘  │   │
│   │                                                       │   │
│   │  Bootstrap Provider (e.g., kubeadm):                 │   │
│   │  ┌────────────────────────────────────────────────┐  │   │
│   │  │ Generates kubeadm configs + cloud-init         │  │   │
│   │  │ Handles certificate rotation                   │  │   │
│   │  └────────────────────────────────────────────────┘  │   │
│   │                                                       │   │
│   │  Control Plane Provider (e.g., KubeadmControlPlane): │   │
│   │  ┌────────────────────────────────────────────────┐  │   │
│   │  │ Manages CP lifecycle: scale, upgrade, rollback │  │   │
│   │  └────────────────────────────────────────────────┘  │   │
│   └──────────────────────────────────────────────────────┘   │
│                          │                                     │
│              Creates and manages                               │
│                          │                                     │
│            ┌─────────────┴────────────┐                       │
│            │     Workload Cluster     │                       │
│            │                          │                       │
│            │  CP1   CP2   CP3        │                       │
│            │  W1    W2    W3   W4    │                       │
│            │  (bare-metal servers)    │                       │
│            └──────────────────────────┘                       │
└──────────────────────────────────────────────────────────────┘
```

The resource hierarchy mirrors Kubernetes workload resources: `Cluster` (top-level) owns a `KubeadmControlPlane` (manages CP Machines) and `MachineDeployment` (manages worker Machines via MachineSets). Each Machine references an infrastructure-specific template (Metal3MachineTemplate) and a bootstrap config (KubeadmConfig). A `MachineHealthCheck` adds auto-remediation.

---

## CAPM3: Metal3 for Bare Metal

Metal3 (pronounced "metal-cubed") is the Cluster API infrastructure provider for bare-metal servers. It uses OpenStack Ironic under the hood to manage server power state, PXE booting, and OS provisioning -- but you interact with it through Kubernetes CRDs, not OpenStack APIs.

### BareMetalHost Inventory

Before you can create clusters, you register your bare-metal servers as `BareMetalHost` resources. This is your hardware inventory.

```yaml
# Register a bare-metal server
apiVersion: metal3.io/v1alpha1
kind: BareMetalHost
metadata:
  name: server-rack1-u10
  namespace: metal3
spec:
  online: true
  bootMACAddress: "aa:bb:cc:dd:ee:01"
  bmc:
    address: "ipmi://192.168.1.10"      # Or redfish://
    credentialsName: server-rack1-u10-bmc
    disableCertificateVerification: true
  rootDeviceHints:
    deviceName: "/dev/nvme0n1"           # Install OS here
  hardwareProfile: "unknown"              # Let Ironic inspect
---
apiVersion: v1
kind: Secret
metadata:
  name: server-rack1-u10-bmc
  namespace: metal3
type: Opaque
stringData:
  username: admin
  password: "CHANGE_ME_IN_VAULT"
```

### BareMetalHost Lifecycle

The state machine is: **Registering** (BMC credentials validated) -> **Inspecting** (Ironic discovers CPU, RAM, disks, NICs) -> **Available** (ready to be claimed by a Machine) -> **Provisioning** (PXE boot, OS install, cloud-init; 5-15 min) -> **Provisioned** (kubelet joined cluster) -> **Deprovisioning** (wipe disks, power off when Machine is deleted) -> **Available** (back in the pool for reuse).

### Creating a Cluster with CAPM3

```yaml
# 1. Cluster definition
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: production
  namespace: clusters
spec:
  clusterNetwork:
    pods:
      cidrBlocks: ["10.244.0.0/16"]
    services:
      cidrBlocks: ["10.96.0.0/12"]
  controlPlaneRef:
    apiVersion: controlplane.cluster.x-k8s.io/v1beta1
    kind: KubeadmControlPlane
    name: production-cp
  infrastructureRef:
    apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
    kind: Metal3Cluster
    name: production
---
# 2. Metal3 cluster config
apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
kind: Metal3Cluster
metadata:
  name: production
  namespace: clusters
spec:
  controlPlaneEndpoint:
    host: 10.0.0.100
    port: 6443
  noCloudProvider: true
---
# 3. Control plane (3 nodes, auto-managed)
apiVersion: controlplane.cluster.x-k8s.io/v1beta1
kind: KubeadmControlPlane
metadata:
  name: production-cp
  namespace: clusters
spec:
  replicas: 3
  version: v1.32.0
  machineTemplate:
    infrastructureRef:
      apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
      kind: Metal3MachineTemplate
      name: production-cp
  kubeadmConfigSpec:
    initConfiguration:
      nodeRegistration:
        kubeletExtraArgs:
          node-labels: "node-role.kubernetes.io/control-plane="
    joinConfiguration:
      nodeRegistration:
        kubeletExtraArgs:
          node-labels: "node-role.kubernetes.io/control-plane="
---
# 4. Machine template for control plane
apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
kind: Metal3MachineTemplate
metadata:
  name: production-cp
  namespace: clusters
spec:
  template:
    spec:
      image:
        url: "https://images.example.com/ubuntu-22.04-k8s.qcow2"
        checksum: "sha256:abc123..."
        checksumType: sha256
        format: qcow2
      hostSelector:
        matchLabels:
          role: control-plane
---
# 5. Worker MachineDeployment
apiVersion: cluster.x-k8s.io/v1beta1
kind: MachineDeployment
metadata:
  name: production-workers
  namespace: clusters
spec:
  clusterName: production
  replicas: 5
  selector:
    matchLabels:
      cluster.x-k8s.io/cluster-name: production
  template:
    metadata:
      labels:
        cluster.x-k8s.io/cluster-name: production
    spec:
      clusterName: production
      version: v1.32.0
      bootstrap:
        configRef:
          apiVersion: bootstrap.cluster.x-k8s.io/v1beta1
          kind: KubeadmConfigTemplate
          name: production-workers
      infrastructureRef:
        apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
        kind: Metal3MachineTemplate
        name: production-workers
```

---

## CAPV: vSphere Provider

If you run vSphere (Module 5.1), CAPV (Cluster API Provider vSphere) manages Kubernetes clusters as vSphere VMs instead of bare metal. CAPV uses `VSphereCluster` and `VSphereMachineTemplate` CRDs to define VM specs (CPU, memory, disk, network, VM template). Key advantages over CAPM3: faster provisioning (2-5 min vs 5-15 min for bare metal), unlimited node pool (VM clones vs fixed hardware inventory), and VM snapshot rollback.

| Dimension | CAPM3 (Bare Metal) | CAPV (vSphere) |
|-----------|-------------------|----------------|
| Provision time | 5-15 minutes | 2-5 minutes |
| Prerequisites | Ironic, DHCP, PXE, BMC | vCenter, templates |
| Node pool | BareMetalHost inventory (fixed) | Unlimited (VM clone) |
| Rollback | Wipe + reprovision | VM snapshot/rollback |
| Best for | Maximum perf, no hypervisor tax | Flexibility, fast iteration |

---

## MachineHealthCheck: Automatic Remediation

MachineHealthCheck watches node conditions and automatically replaces unhealthy nodes. This is the most valuable CAPI feature for on-premises operations.

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: MachineHealthCheck
metadata:
  name: production-worker-health
  namespace: clusters
spec:
  clusterName: production
  selector:
    matchLabels:
      cluster.x-k8s.io/deployment-name: production-workers
  unhealthyConditions:
    - type: Ready
      status: "False"
      timeout: 300s       # Node NotReady for 5 minutes
    - type: Ready
      status: "Unknown"
      timeout: 300s       # Node unreachable for 5 minutes
  maxUnhealthy: "40%"     # Safety: do not remediate if > 40% nodes are unhealthy
  nodeStartupTimeout: 600s # New nodes must be Ready within 10 minutes
```

### Remediation Flow

```
┌──────────────────────────────────────────────────────────────┐
│           MACHINEHEALTHCHECK REMEDIATION FLOW                 │
│                                                                │
│   1. Node "worker-03" becomes NotReady                        │
│      (disk failure, kernel panic, network partition)          │
│                                                                │
│   2. MachineHealthCheck detects:                              │
│      condition Ready=False for > 300 seconds                  │
│                                                                │
│   3. Safety check: is < 40% of the pool unhealthy?           │
│      Yes (1 of 5 = 20%) -> proceed                           │
│      No  (3 of 5 = 60%) -> do NOT remediate (likely          │
│                             infrastructure issue, not node)   │
│                                                                │
│   4. Machine "worker-03" is deleted                           │
│      - Node is cordoned and drained                           │
│      - BareMetalHost is deprovisioned (disk wipe, power off) │
│                                                                │
│   5. MachineDeployment sees replicas=5 but only 4 exist      │
│      - Creates new Machine "worker-06"                        │
│      - Selects an Available BareMetalHost from inventory      │
│      - Provisions OS, joins cluster                           │
│                                                                │
│   6. New node "worker-06" becomes Ready                       │
│      Total time: 5-15 minutes (bare metal)                    │
│      Total time: 2-5 minutes (vSphere)                        │
│                                                                │
│   CRITICAL: You need spare BareMetalHosts in the inventory.  │
│   If all hosts are in use, remediation creates a Machine      │
│   that stays Pending until a host becomes available.          │
└──────────────────────────────────────────────────────────────┘
```

---

## GitOps-Driven Cluster Management

Storing Cluster API manifests in Git enables GitOps-driven cluster lifecycle. Changes to cluster definitions (scaling, upgrades, new clusters) are pull requests, reviewed and merged like application code.

```
┌──────────────────────────────────────────────────────────────┐
│           GITOPS CLUSTER LIFECYCLE                             │
│                                                                │
│   Git Repository                                              │
│   ├── clusters/                                               │
│   │   ├── production/                                         │
│   │   │   ├── cluster.yaml          # Cluster + Metal3Cluster │
│   │   │   ├── control-plane.yaml    # KubeadmControlPlane     │
│   │   │   ├── workers.yaml          # MachineDeployment       │
│   │   │   └── health-checks.yaml    # MachineHealthCheck      │
│   │   ├── staging/                                            │
│   │   │   └── ...                                             │
│   │   └── dev/                                                │
│   │       └── ...                                             │
│   └── inventory/                                              │
│       ├── rack1-hosts.yaml          # BareMetalHost CRDs      │
│       ├── rack2-hosts.yaml                                    │
│       └── bmc-secrets.yaml          # Sealed/SOPS encrypted   │
│                                                                │
│   Flux/ArgoCD                                                 │
│   ├── Watches git repo                                        │
│   ├── Applies changes to management cluster                   │
│   └── CAPI controllers reconcile desired state               │
│                                                                │
│   Workflow:                                                    │
│   1. Engineer opens PR: "Scale production workers 5 -> 8"    │
│   2. PR review: team approves the hardware allocation         │
│   3. Merge: Flux applies updated MachineDeployment            │
│   4. CAPI: provisions 3 new BareMetalHosts as workers        │
│   5. Audit: git log shows who scaled, when, and why          │
└──────────────────────────────────────────────────────────────┘
```

Use a Flux `Kustomization` with `prune: false` (critical -- never auto-delete cluster resources) to sync the git repo to the management cluster. To upgrade a cluster, change the `version` field in git and merge. CAPI performs a rolling upgrade: create new node, wait for Ready, remove old node, repeat.

---

## Did You Know?

- **Metal3 uses OpenStack Ironic without requiring a full OpenStack deployment.** Ironic runs as a standalone service (or as a pod in the management cluster) and communicates with servers via IPMI or Redfish. You get the bare-metal provisioning capabilities of OpenStack without Nova, Neutron, Keystone, or any other OpenStack service.

- **Cluster API was inspired by the Kubernetes controller pattern applied to infrastructure.** Just as a Deployment controller ensures the right number of pods exist, the MachineDeployment controller ensures the right number of nodes exist. The same reconciliation loop that makes Kubernetes self-healing for applications now makes it self-healing for infrastructure.

- **CAPM3 can manage servers from any vendor** -- Dell iDRAC, HPE iLO, Supermicro IPMI, Lenovo XClarity -- as long as they support IPMI or Redfish protocols. Redfish is the modern standard (REST API over HTTPS) and is replacing IPMI (which sends credentials in plaintext over UDP).

- **The largest known CAPI deployments manage thousands of clusters.** Deutsche Telekom's Das Schiff platform uses Cluster API to manage Kubernetes across edge locations. Each cell tower runs a small cluster, and CAPI on a central management cluster handles the lifecycle of all of them.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No spare BareMetalHosts | MachineHealthCheck creates replacement Machine but no host is available | Keep 10-15% of inventory as spare (e.g., 2 spares for 15 servers) |
| BMC credentials in plain Secrets | IPMI/Redfish credentials exposed in etcd | Use SealedSecrets or SOPS encryption for BMC credentials |
| `prune: true` in Flux for clusters | Flux deletes cluster resources if removed from git | Set `prune: false` for cluster Kustomizations |
| `maxUnhealthy: 100%` | Cascading failure: MHC replaces all nodes simultaneously during network partition | Set `maxUnhealthy` to 30-40% to prevent mass remediation |
| No OS image versioning | Cannot reproduce node state, drift between nodes | Version OS images, store in HTTP server, reference by checksum |
| Skipping hardware inspection | CAPI provisions a server with bad RAM or failed disk | Let Ironic inspect all hosts before marking them Available |
| Manual changes to CAPI clusters | Drift between desired state (git) and actual state | All changes via git PRs, never `kubectl edit` on CAPI resources |

---

## Quiz

### Question 1
You have 20 bare-metal servers and need to run 3 Kubernetes clusters (dev: 3 nodes, staging: 5 nodes, production: 9 nodes). How many BareMetalHosts should you register, and how many should be spare?

<details>
<summary>Answer</summary>

**Register all 20 servers. Keep 3 as spares.**

Allocation:
- Dev cluster: 1 CP + 2 workers = 3 nodes
- Staging cluster: 1 CP + 4 workers = 5 nodes (control plane nodes must always be an odd number -- 1 or 3 -- to maintain etcd quorum; 2 CP nodes are worse than 1 because a single failure loses quorum)
- Production cluster: 3 CP + 6 workers = 9 nodes
- Total allocated: 17 nodes
- Spare: 3 nodes (15% of total)

**Why 3 spares matters**:

1. **MachineHealthCheck remediation**: When a production worker fails, MHC needs an Available BareMetalHost to provision as a replacement. Without spares, the replacement Machine stays Pending indefinitely.

2. **Concurrent failures**: If two nodes fail simultaneously (e.g., shared power circuit), you need 2 spares. The third spare covers the period while a failed server is being physically repaired.

3. **Scaling**: If production needs to temporarily scale to 12 nodes (e.g., during peak traffic), the 3 spares provide this capacity without stealing from other clusters.

```yaml
# Label spares for easy identification
apiVersion: metal3.io/v1alpha1
kind: BareMetalHost
metadata:
  name: spare-01
  labels:
    role: spare
spec:
  online: false  # Keep powered off until needed
```
</details>

### Question 2
Your MachineHealthCheck has `maxUnhealthy: 40%` and you have 10 worker nodes. 5 nodes simultaneously become NotReady due to a switch failure. What happens?

<details>
<summary>Answer</summary>

**MachineHealthCheck does NOT remediate any nodes.** 5 of 10 nodes = 50%, which exceeds the `maxUnhealthy: 40%` threshold.

**This is correct behavior.** The `maxUnhealthy` safeguard exists precisely for this scenario:
- A network switch failure is an infrastructure problem, not a node problem
- Remediating 5 nodes simultaneously would be catastrophic -- wiping and reprovisioning half the cluster while the real issue is a switch
- When the switch is fixed, all 5 nodes will return to Ready state without any action

**What you should do**:
1. Check the management cluster for MachineHealthCheck events:
   ```bash
   kubectl describe machinehealthcheck production-worker-health -n clusters
   # Events: "Remediation is not allowed, total unhealthy: 50%, max: 40%"
   ```
2. Investigate the infrastructure issue (switch, power, network)
3. Fix the root cause
4. Nodes recover automatically

**If it were a single node failure** (1 of 10 = 10% < 40%), MHC would remediate: delete the Machine, deprovision the BareMetalHost, and create a replacement.
</details>

### Question 3
You want to upgrade your production cluster from Kubernetes v1.31.0 to v1.32.0 using Cluster API. Describe the upgrade process and what happens if a new control plane node fails to start.

<details>
<summary>Answer</summary>

**Upgrade process** (KubeadmControlPlane rolling upgrade):

1. Update the `version` field in the KubeadmControlPlane spec (via git PR + merge)
2. CAPI creates a **new** Machine with v1.32.0 (does not modify existing nodes)
3. The new Machine is provisioned: BareMetalHost selected, OS installed, kubeadm join with v1.32.0
4. CAPI waits for the new node to be Ready and etcd to be healthy
5. CAPI removes one old v1.31.0 control plane node
6. Repeats steps 2-5 for each remaining control plane node
7. After all CP nodes are upgraded, MachineDeployment rolls workers similarly

**If a new CP node fails to start**:
- CAPI detects that the Machine is not Ready within `nodeStartupTimeout`
- The upgrade **pauses** -- it does not remove any old nodes
- The cluster continues running on the existing v1.31.0 nodes
- The failed Machine is reported in events and status
- You investigate (bad OS image? network issue? disk failure?) and fix it
- CAPI retries automatically once the issue is resolved

**Key safety guarantee**: CAPI never removes an old node until the new replacement is confirmed healthy. This means an upgrade failure leaves you with your existing working cluster, not a broken one.

```bash
# Monitor upgrade progress
kubectl get machines -n clusters -l cluster.x-k8s.io/cluster-name=production
# NAME              PHASE         VERSION
# production-cp-1   Running       v1.31.0   (old, will be removed last)
# production-cp-2   Running       v1.31.0
# production-cp-3   Running       v1.31.0
# production-cp-4   Provisioning  v1.32.0   (new, being created)
```
</details>

### Question 4
Why should you set `prune: false` in Flux Kustomizations that manage Cluster API resources?

<details>
<summary>Answer</summary>

**Because Flux pruning would delete cluster resources if they are removed from git, which would destroy running clusters.**

Flux pruning works like this: if a resource exists in the cluster but its YAML is no longer in the git repository, Flux deletes the resource. This is safe for Deployments and ConfigMaps but catastrophic for CAPI resources:

1. Engineer accidentally deletes `clusters/production/` directory from git
2. Flux detects the resources are gone from git
3. With `prune: true`: Flux deletes the Cluster, KubeadmControlPlane, MachineDeployment
4. CAPI sees the Cluster is deleted and begins deprovisioning ALL nodes
5. All BareMetalHosts are wiped and powered off
6. **Entire production cluster destroyed**

With `prune: false`:
1. Engineer accidentally deletes files from git
2. Flux does NOT delete the cluster resources
3. Cluster continues running
4. Engineer restores the files in a follow-up commit
5. No impact

**Additional safety measures**:
```yaml
# Add finalizer protection to critical resources
metadata:
  annotations:
    kustomize.toolkit.fluxcd.io/prune: "disabled"
```

This is the same principle as `reclaimPolicy: Retain` on PersistentVolumes -- critical resources should not be automatically deleted.
</details>

---

## Hands-On Exercise: Explore Cluster API with Docker Provider

The Docker provider (CAPD) uses Docker containers as "machines" instead of real bare-metal servers.

```bash
# Install clusterctl and create management cluster
curl -L https://github.com/kubernetes-sigs/cluster-api/releases/latest/download/clusterctl-linux-amd64 -o clusterctl
chmod +x clusterctl && sudo mv clusterctl /usr/local/bin/
kind create cluster --name capi-mgmt

# Initialize CAPI with Docker provider
export CLUSTER_TOPOLOGY=true
clusterctl init --infrastructure docker

# Generate and create a workload cluster
clusterctl generate cluster dev-cluster \
  --infrastructure docker \
  --kubernetes-version v1.31.0 \
  --control-plane-machine-count 1 \
  --worker-machine-count 2 > dev-cluster.yaml
kubectl apply -f dev-cluster.yaml

# Watch provisioning and get kubeconfig
kubectl get cluster,machines -A
kubectl wait cluster/dev-cluster --for=condition=Ready --timeout=300s
clusterctl get kubeconfig dev-cluster > dev-cluster.kubeconfig

# Scale the workload cluster
kubectl patch machinedeployment dev-cluster-md-0 \
  --type merge -p '{"spec":{"replicas":3}}'

# Cleanup
kubectl delete cluster dev-cluster
kind delete cluster --name capi-mgmt
```

### Success Criteria

- [ ] Workload cluster provisioned (1 CP + 2 workers)
- [ ] Cluster scaled from 2 to 3 workers
- [ ] Understood the Machine lifecycle (Pending -> Provisioning -> Running)

---

## Next Module

This is the final module in the Multi-Cluster & Platform section. Continue to [Module 6.1: Physical Security & Air-Gapped Environments](../security/module-6.1-air-gapped/) to learn how to secure on-premises Kubernetes clusters from network to workload layer.
