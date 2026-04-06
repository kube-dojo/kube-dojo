---
title: "Module 7.1: AKS Architecture & Node Management"
slug: cloud/aks-deep-dive/module-7.1-aks-architecture
sidebar:
  order: 2
---
**Complexity**: [MEDIUM] | **Time to Complete**: 2h | **Prerequisites**: Azure Essentials, Cloud Architecture Patterns

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure AKS clusters with system and user node pools, availability zones, and ephemeral OS disks**
- **Implement AKS auto-upgrade channels and planned maintenance windows for controlled Kubernetes version updates**
- **Deploy AKS with Entra ID RBAC integration to replace certificate-based kubeconfig with identity-driven access**
- **Design AKS node pool strategies with VM Scale Sets, taints, labels, and node selectors for workload isolation**

---

## Why This Module Matters

In September 2023, a fintech company running their payment processing platform on Azure Kubernetes Service experienced a cascading failure that brought down all customer-facing services for nearly four hours. The root cause was not a bug in their application code. It was an architecture decision made months earlier: every workload, from critical payment APIs to batch reporting jobs, ran in a single system node pool on three Standard_D4s_v3 instances. When Azure initiated a routine host maintenance event on one of the underlying physical servers, the node drained its pods. The remaining two nodes could not absorb the spike, and Kubernetes started evicting pods with the lowest priority---which happened to include their payment reconciliation service. The reconciliation service held database locks that the payment API depended on, and within minutes the entire cluster was in a death spiral. The four-hour outage cost the company an estimated $2.6 million in lost transactions and regulatory penalties.

The lesson is brutal but simple: AKS gives you a managed Kubernetes control plane, but the architecture decisions around node pools, availability zones, upgrade strategies, and identity integration are entirely yours. Get them wrong and you build a house of cards. Get them right and you have a platform that can survive node failures, zone outages, and even botched upgrades without your customers noticing.

In this module, you will learn how AKS is structured underneath the managed surface. You will understand the difference between system and user node pools, how Virtual Machine Scale Sets power your nodes, how availability zones protect you from datacenter failures, how upgrade channels keep your clusters current without surprises, how ephemeral OS disks dramatically improve node startup times, and how Entra ID integration replaces fragile kubeconfig certificates with proper identity management. By the end, you will deploy a production-grade AKS cluster using Bicep with Entra ID RBAC---the foundation for everything that follows in this deep dive.

---

## The AKS Control Plane: What Microsoft Manages (and What You Own)

When you create an AKS cluster, Microsoft provisions and manages the Kubernetes control plane: the API server, etcd, the controller manager, and the scheduler. You never see these components directly, you never SSH into them, and you never pay separately for them (the control plane is free as of the current pricing model). This is the core value proposition of a managed Kubernetes service.

But "managed" does not mean "hands-off." You still make critical decisions that determine how the control plane behaves:

```text
    ┌──────────────────────────────────────────────────────────────────┐
    │                    Microsoft-Managed Control Plane                │
    │                                                                  │
    │   ┌─────────┐  ┌─────────┐  ┌──────────────────┐  ┌──────────┐  │
    │   │   API   │  │  etcd   │  │   Controller     │  │Scheduler │  │
    │   │  Server │  │         │  │   Manager        │  │          │  │
    │   └────┬────┘  └─────────┘  └──────────────────┘  └──────────┘  │
    │        │                                                         │
    │        │  SLA: 99.95% (with AZs) / 99.9% (without AZs)         │
    │        │  Free tier: no SLA, no uptime guarantee                 │
    └────────┼─────────────────────────────────────────────────────────┘
             │
             │  kubelet communicates over TLS
             │
    ┌────────┼─────────────────────────────────────────────────────────┐
    │        ▼              Customer-Managed Data Plane                │
    │                                                                  │
    │   ┌────────────────────┐    ┌────────────────────────────────┐   │
    │   │  System Node Pool  │    │      User Node Pool(s)         │   │
    │   │  (CoreDNS, tunnel, │    │  (Your workloads, your apps,   │   │
    │   │   metrics-server)  │    │   your responsibility)         │   │
    │   └────────────────────┘    └────────────────────────────────┘   │
    │                                                                  │
    │   You choose: VM size, node count, OS disk type, OS SKU,        │
    │   availability zones, auto-scaling, upgrade strategy             │
    └──────────────────────────────────────────────────────────────────┘
```

The SLA numbers matter. If you deploy AKS across availability zones with the Standard tier, Microsoft guarantees 99.95% uptime for the API server. Without zones, you get 99.9%. On the Free tier, you get zero uptime guarantee---fine for dev, unacceptable for production. The Premium tier adds a 99.99% SLA for mission-critical workloads.

```bash
# Create a cluster on the Standard tier (required for production SLA)
az aks create \
  --resource-group rg-aks-prod \
  --name aks-prod-westeurope \
  --tier standard \
  --kubernetes-version 1.30.7 \
  --location westeurope

# Check your cluster's current tier
az aks show --resource-group rg-aks-prod --name aks-prod-westeurope \
  --query "sku.{Name:name, Tier:tier}" -o table
```

---

## System Pools vs User Pools: Separation of Concerns

Every AKS cluster must have at least one system node pool. This pool runs the critical add-ons that keep Kubernetes functioning: CoreDNS, the metrics server, the Azure cloud-provider integration, and the konnectivity-agent tunnel that connects your nodes to the managed control plane.

Think of system pools like the engine room on a ship. You do not put passenger luggage in the engine room, and you do not run your application workloads on system nodes. Why? Because if a misbehaving application pod consumes all CPU or memory on a system node, it can starve CoreDNS. When CoreDNS goes down, every single pod in your cluster loses DNS resolution, and your entire platform goes dark.

```bash
# Create a cluster with a dedicated system pool (small, reliable VMs)
az aks create \
  --resource-group rg-aks-prod \
  --name aks-prod-westeurope \
  --nodepool-name system \
  --node-count 3 \
  --node-vm-size Standard_D2s_v5 \
  --zones 1 2 3 \
  --mode System \
  --max-pods 30

# Add a user pool for application workloads
az aks nodepool add \
  --resource-group rg-aks-prod \
  --cluster-name aks-prod-westeurope \
  --name apps \
  --node-count 3 \
  --node-vm-size Standard_D4s_v5 \
  --zones 1 2 3 \
  --mode User \
  --max-pods 110 \
  --enable-cluster-autoscaler \
  --min-count 3 \
  --max-count 12 \
  --labels workload=general
```

### Taints and Tolerations: Enforcing the Boundary

System pools automatically receive the taint `CriticalAddonsOnly=true:NoSchedule`. This means your application pods will not be scheduled on system nodes unless they explicitly tolerate this taint. You should never add that toleration to your application deployments.

> **Stop and think**: A developer creates a massive video-processing deployment but forgets to specify any node selectors or tolerations. You have a System pool (with the default taint) and a User pool. Which pool will the Kubernetes scheduler place these pods in, and why?

For user pools, you can add your own taints to create specialized pools:

```bash
# GPU pool with a taint so only GPU-requiring workloads land here
az aks nodepool add \
  --resource-group rg-aks-prod \
  --cluster-name aks-prod-westeurope \
  --name gpu \
  --node-count 1 \
  --node-vm-size Standard_NC6s_v3 \
  --node-taints "gpu=true:NoSchedule" \
  --labels accelerator=nvidia \
  --mode User

# Spot pool for fault-tolerant batch jobs (up to 90% cheaper)
az aks nodepool add \
  --resource-group rg-aks-prod \
  --cluster-name aks-prod-westeurope \
  --name spot \
  --node-count 0 \
  --node-vm-size Standard_D8s_v5 \
  --priority Spot \
  --eviction-policy Delete \
  --spot-max-price -1 \
  --enable-cluster-autoscaler \
  --min-count 0 \
  --max-count 20 \
  --mode User \
  --node-taints "kubernetes.azure.com/scalesetpriority=spot:NoSchedule"
```

| Pool Type | Purpose | Min Nodes | Taint Applied | When to Scale |
| :--- | :--- | :--- | :--- | :--- |
| **System** | CoreDNS, konnectivity, metrics-server | 3 (for HA across AZs) | `CriticalAddonsOnly` (auto) | Rarely---keep stable |
| **User (general)** | Standard application workloads | 3 (one per AZ) | None (or custom) | Autoscaler based on load |
| **User (GPU)** | ML inference, video processing | 0-1 | Custom GPU taint | Scale to zero when idle |
| **User (Spot)** | Batch jobs, CI runners, non-critical work | 0 | Spot taint (auto) | Aggressive autoscaling |

---

## Virtual Machine Scale Sets: The Engine Behind Node Pools

Every AKS node pool is backed by an Azure Virtual Machine Scale Set (VMSS). When the cluster autoscaler decides you need more nodes, it tells the VMSS to add instances. When it scales down, instances are removed from the VMSS. Understanding this relationship helps you troubleshoot node issues, because many problems that look like Kubernetes problems are actually VMSS problems.

```bash
# Find the VMSS backing your node pool
# AKS creates a separate resource group for infrastructure (MC_* prefix)
INFRA_RG=$(az aks show --resource-group rg-aks-prod --name aks-prod-westeurope \
  --query nodeResourceGroup -o tsv)

# List all VMSS in the infrastructure resource group
az vmss list --resource-group $INFRA_RG \
  --query "[].{Name:name, VMSize:sku.name, Capacity:sku.capacity}" -o table

# View instances in a specific VMSS
az vmss list-instances --resource-group $INFRA_RG \
  --name aks-apps-12345678-vmss \
  --query "[].{InstanceId:instanceId, Zone:zones[0], State:provisioningState}" -o table
```

### The Infrastructure Resource Group (MC_*)

When AKS creates your cluster, it also creates a second resource group with the naming convention `MC_{resource-group}_{cluster-name}_{region}`. This resource group contains all the infrastructure AKS manages on your behalf: the VMSS instances, load balancers, public IPs, managed disks, and virtual network interfaces.

A critical rule: **never manually modify resources in the MC_ resource group**. AKS reconciles this resource group continuously. If you manually delete a load balancer rule or resize a VMSS, AKS may revert your change on the next reconciliation cycle, creating confusing and hard-to-debug behavior. If you need to customize infrastructure, use the AKS API or supported extensions.

```bash
# View what AKS has created in the infrastructure resource group
az resource list --resource-group $INFRA_RG \
  --query "[].{Name:name, Type:type}" -o table
```

---

## Availability Zones: Surviving Datacenter Failures

An Azure region typically contains three availability zones. Each zone is a physically separate datacenter (or group of datacenters) with independent power, cooling, and networking. When you deploy AKS nodes across all three zones, a complete datacenter failure takes out at most one-third of your capacity.

```text
    Azure Region: West Europe
    ┌──────────────────────────────────────────────────────────────┐
    │                                                              │
    │  Zone 1              Zone 2              Zone 3              │
    │  ┌──────────┐       ┌──────────┐       ┌──────────┐         │
    │  │ node-01  │       │ node-02  │       │ node-03  │         │
    │  │ node-04  │       │ node-05  │       │ node-06  │         │
    │  └──────────┘       └──────────┘       └──────────┘         │
    │                                                              │
    │  If Zone 1 fails:   nodes 02,03,05,06 continue serving      │
    │  Autoscaler adds    new nodes in zones 2 and 3               │
    └──────────────────────────────────────────────────────────────┘
```

There is a catch that trips up many teams: **AKS does not guarantee even distribution across zones**. If you request 5 nodes across 3 zones, you might get 2-2-1 or even 3-1-1 distribution. The VMSS tries to balance, but it is not guaranteed. You should always deploy node counts that are multiples of your zone count (3, 6, 9, 12) to maximize balance.

Another critical detail: **persistent volumes (Azure Disks) are zone-locked**.

> **Pause and predict**: Imagine you have a stateful application pod running in Zone 1, connected to an Azure Disk PersistentVolume. The physical host running this node experiences a hardware failure, and the node goes offline. The cluster autoscaler spins up a replacement node in Zone 2, and the Kubernetes scheduler attempts to move your pod there. What will happen to your application?

An Azure Disk created in Zone 1 cannot be attached to a node in Zone 2. If a pod with a PVC backed by an Azure Disk gets rescheduled to a different zone, it will be stuck in `Pending` forever. You must use topology-aware scheduling or switch to Azure Files (which are zone-redundant) for workloads that need cross-zone mobility.

```yaml
# Pod topology spread constraint to enforce even zone distribution
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-api
spec:
  replicas: 6
  selector:
    matchLabels:
      app: payment-api
  template:
    metadata:
      labels:
        app: payment-api
    spec:
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: payment-api
      containers:
        - name: payment-api
          image: myregistry.azurecr.io/payment-api:v3.2.1
          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
            limits:
              cpu: "1"
              memory: "1Gi"
```

---

## Upgrade Channels: Keeping Current Without Breaking Things

Kubernetes releases a new minor version roughly every four months. AKS supports three minor versions at any time, and you are responsible for upgrading before your version falls out of support. The upgrade channel feature automates this process, but choosing the right channel is critical.

| Channel | Behavior | Best For |
| :--- | :--- | :--- |
| **none** | No automatic upgrades. You upgrade manually. | Teams needing full control over upgrade timing |
| **patch** | Automatically applies the latest patch within your current minor version (e.g., 1.30.5 to 1.30.7) | Most production clusters |
| **stable** | Upgrades to the latest patch of the N-1 minor version (one behind latest) | Conservative production environments |
| **rapid** | Upgrades to the latest patch of the latest minor version | Dev/test environments, early adopters |
| **node-image** | Only upgrades the node OS image, not the Kubernetes version | When you want OS patches but not K8s version changes |

```bash
# Set the upgrade channel
az aks update \
  --resource-group rg-aks-prod \
  --name aks-prod-westeurope \
  --auto-upgrade-channel stable

# Configure a maintenance window (avoid upgrades during business hours)
az aks maintenanceconfiguration add \
  --resource-group rg-aks-prod \
  --cluster-name aks-prod-westeurope \
  --name default \
  --schedule-type Weekly \
  --day-of-week Saturday \
  --start-time 02:00 \
  --duration 4 \
  --utc-offset "+01:00"
```

### How AKS Upgrades Work Under the Hood

When you trigger an upgrade (manually or via an auto-upgrade channel), AKS performs a rolling update of your nodes. The process for each node is:

1. AKS creates a new node with the target version (using a surge node)
2. The old node is cordoned (no new pods scheduled)
3. The old node is drained (existing pods are evicted with respect to PodDisruptionBudgets)
4. Once the old node is empty, it is deleted
5. AKS moves to the next node

> **Pause and predict**: You have a 10-node user pool running at 90% utilization. You trigger a Kubernetes version upgrade. If AKS were to take down 3 old nodes simultaneously before provisioning new ones, what would happen to your application performance? How does AKS prevent this?

The **max surge** setting controls how many extra nodes AKS creates during the upgrade. A higher surge means faster upgrades but higher temporary costs. For production clusters, a max surge of 33% is a solid default---it upgrades one-third of your nodes at a time.

```bash
# Set max surge for a node pool
az aks nodepool update \
  --resource-group rg-aks-prod \
  --cluster-name aks-prod-westeurope \
  --name apps \
  --max-surge 33%

# Manually trigger a cluster upgrade
az aks upgrade \
  --resource-group rg-aks-prod \
  --name aks-prod-westeurope \
  --kubernetes-version 1.30.7

# Check upgrade progress
az aks show --resource-group rg-aks-prod --name aks-prod-westeurope \
  --query "provisioningState" -o tsv
```

---

## Ephemeral OS Disks: Faster Nodes, Lower Costs

By default, AKS nodes use managed OS disks backed by Azure Premium SSD. These disks are persistent---if a node is deallocated and reallocated, the OS disk retains its data. But this durability comes at a cost: slower node startup times and additional storage charges.

Ephemeral OS disks use the local temporary storage on the VM host. This means:

- **Faster node startup**: No need to create and attach a remote disk. Nodes boot in roughly 20-30 seconds instead of 60-90 seconds.
- **Lower latency for OS operations**: The disk is local NVMe or SSD, not a network-attached disk.
- **No additional disk cost**: The local storage is included in the VM price.
- **Reimaged on every reboot**: If a node is deallocated and reallocated, it gets a fresh OS image.

The "reimaged on reboot" behavior is actually a benefit for security and consistency. Your nodes are always in a known-good state. Any drift, malware, or leftover state from previous workloads is wiped clean.

```bash
# Create a node pool with ephemeral OS disks
az aks nodepool add \
  --resource-group rg-aks-prod \
  --cluster-name aks-prod-westeurope \
  --name fastapps \
  --node-count 3 \
  --node-vm-size Standard_D4s_v5 \
  --os-disk-type Ephemeral \
  --zones 1 2 3 \
  --mode User
```

Not all VM sizes support ephemeral OS disks. The VM's temporary storage or cache must be large enough to hold the OS image (typically 128 GB). Standard_D4s_v5 has a 100 GB cache, which works with the default 128 GB OS disk size if you set `--os-disk-size-gb 100` or use a VM with larger cache. Check the [VM sizes documentation](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes) to confirm support.

---

## Entra ID Integration: Identity-First Cluster Access

The default AKS authentication mechanism uses x509 client certificates embedded in the kubeconfig file. This is terrible for production. Certificates do not expire on a reasonable schedule, cannot be individually revoked without rotating the entire cluster CA, and provide no audit trail of who did what.

Entra ID integration replaces certificates with OAuth 2.0 tokens. When a user runs `kubectl get pods`, the kubeconfig triggers a browser-based login flow (or uses a cached token) against Entra ID. The API server validates the token, extracts the user's group memberships, and applies Kubernetes RBAC rules based on those groups.

```text
    Developer runs                   Entra ID validates
    "kubectl get pods"               and issues token
          │                                │
          ▼                                ▼
    ┌──────────┐     OAuth2 flow     ┌──────────────┐
    │ kubelogin │ ──────────────────► │  Entra ID    │
    │ (kubectl  │ ◄────────────────── │  Tenant      │
    │  plugin)  │     JWT token       └──────────────┘
    └─────┬────┘
          │  Bearer token in Authorization header
          ▼
    ┌──────────────┐    Validate token,    ┌──────────────────┐
    │  AKS API     │    extract groups ──► │  K8s RBAC        │
    │  Server      │                       │  ClusterRole     │
    │              │ ◄──────────────────── │  Bindings map    │
    └──────────────┘    allow/deny         │  Entra groups    │
                                           └──────────────────┘
```

### Setting Up Entra ID Integration

There are two modes: **AKS-managed Entra ID** (simpler, recommended) and **legacy Azure AD integration** (deprecated). Always use AKS-managed.

```bash
# Create the cluster with AKS-managed Entra ID
az aks create \
  --resource-group rg-aks-prod \
  --name aks-prod-westeurope \
  --enable-aad \
  --aad-admin-group-object-ids "$(az ad group show --group 'AKS-Admins' --query id -o tsv)" \
  --enable-azure-rbac

# For existing clusters, enable Entra ID integration
az aks update \
  --resource-group rg-aks-prod \
  --name aks-prod-westeurope \
  --enable-aad \
  --aad-admin-group-object-ids "$(az ad group show --group 'AKS-Admins' --query id -o tsv)"
```

The `--enable-azure-rbac` flag is especially powerful. It lets you use Azure RBAC role assignments directly for Kubernetes authorization, without needing to create separate ClusterRoleBindings. Azure provides four built-in roles:

| Azure RBAC Role | Kubernetes Equivalent | Use Case |
| :--- | :--- | :--- |
| **Azure Kubernetes Service RBAC Cluster Admin** | cluster-admin | Platform team, break-glass access |
| **Azure Kubernetes Service RBAC Admin** | admin (namespaced) | Team leads, namespace owners |
| **Azure Kubernetes Service RBAC Writer** | edit (namespaced) | Developers who deploy workloads |
| **Azure Kubernetes Service RBAC Reader** | view (namespaced) | Read-only dashboards, auditors |

```bash
# Grant a developer group write access to the "payments" namespace
az role assignment create \
  --assignee-object-id "$(az ad group show --group 'Payments-Developers' --query id -o tsv)" \
  --role "Azure Kubernetes Service RBAC Writer" \
  --scope "$(az aks show -g rg-aks-prod -n aks-prod-westeurope --query id -o tsv)/namespaces/payments"
```

---

## Did You Know?

1. **AKS control plane costs nothing.** Microsoft does not charge for the Kubernetes control plane. You only pay for the VMs (nodes) in your cluster and any associated resources like load balancers and disks. The Standard tier ($0.10/cluster-hour as of 2025) adds the SLA guarantee and advanced features like long-term support versions, but the core control plane itself remains free.

2. **The MC_ resource group naming convention has a 80-character limit.** If your resource group name, cluster name, and region combine to exceed 80 characters, AKS truncates the infrastructure resource group name. This has caused automation scripts to break when they construct the MC_ name programmatically. Use `az aks show --query nodeResourceGroup` instead of string concatenation.

3. **AKS nodes run a Microsoft-maintained Linux distribution called Azure Linux (formerly CBL-Mariner).** Since late 2023, Azure Linux has been the default OS for new AKS clusters, replacing Ubuntu. Azure Linux is optimized for container workloads with a smaller attack surface, faster boot times, and automatic security patches through the node image upgrade mechanism.

4. **The cluster autoscaler in AKS checks for pending pods every 10 seconds by default.** When it finds pods that cannot be scheduled due to insufficient resources, it calculates the minimum number of nodes needed across all configured node pools and issues a scale-up request to the VMSS. Scale-down is more conservative: nodes must be below 50% utilization for 10 minutes (by default) before they are candidates for removal.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Running workloads on system node pools | Default cluster creation puts everything in one pool | Always create separate user pools; system pools should only run critical add-ons |
| Using Free tier for production | Cost savings temptation or oversight during initial setup | Use Standard tier minimum for production; Premium for mission-critical workloads |
| Deploying nodes in a single availability zone | Not specifying `--zones` during pool creation | Always pass `--zones 1 2 3` for production pools; use multiples of 3 for node counts |
| Ignoring PodDisruptionBudgets during upgrades | Teams deploy without PDBs, then upgrades drain all replicas simultaneously | Create PDBs for every production deployment with `minAvailable` or `maxUnavailable` |
| Manually modifying resources in the MC_ resource group | Trying to fix networking or disk issues directly | Always use AKS APIs and az aks commands; manual changes get overwritten |
| Using certificate-based auth in production | It is the default and "just works" for initial setup | Enable Entra ID integration and Azure RBAC before onboarding any team |
| Setting max-pods too low on user pools | Copying system pool settings (30 pods) to user pools | Use 110 (default) or higher for user pools; calculate based on CNI and subnet sizing |
| Not configuring maintenance windows | Auto-upgrades happen at random times, causing surprise disruptions | Set maintenance windows to off-peak hours for both node OS and Kubernetes version upgrades |

---

## Quiz

<details>
<summary>1. Your team is deploying a new microservice architecture and decides to place all workloads into the default system node pool to save costs. During a load test, the new services consume 99% of the node's memory. Suddenly, every other application in the cluster starts reporting DNS resolution failures. What architectural mistake caused this cascading failure?</summary>

You ran application workloads on the system node pool, which shares resources with critical infrastructure like CoreDNS and the metrics server. When your application consumed all the memory, it starved CoreDNS, causing it to crash or become unresponsive. Because CoreDNS is responsible for resolving internal Kubernetes services, its failure caused every pod in the cluster to lose DNS resolution, effectively bringing down the entire platform. System pools should always be isolated using the `CriticalAddonsOnly` taint to prevent exactly this scenario.
</details>

<details>
<summary>2. During a routine maintenance event, a node in Zone 1 is drained, and its pods are evicted. One of the evicted pods is a PostgreSQL database using an Azure Disk for its PersistentVolumeClaim. The Kubernetes scheduler decides to place the replacement pod on a node in Zone 2. What will be the state of the PostgreSQL pod, and why?</summary>

The PostgreSQL pod will be stuck in a `Pending` state indefinitely. This happens because Azure Disks are zone-locked resources; a disk created in Zone 1 physically exists in Zone 1's datacenter and cannot be attached to a Virtual Machine in Zone 2. The Kubernetes scheduler cannot satisfy both the PVC requirement (which is bound to the Zone 1 disk) and the node placement in Zone 2 simultaneously. To prevent this, you must use topology-aware scheduling to force the pod into Zone 1, or use a zone-redundant storage solution like Azure Files.
</details>

<details>
<summary>3. Your company operates in a highly regulated financial industry where stability is prioritized above all else. However, you still need automated patching for security vulnerabilities. You are debating between the 'patch' and 'stable' auto-upgrade channels for your AKS clusters. Which should you choose to minimize the risk of introducing breaking changes from new Kubernetes features?</summary>

You should choose the 'stable' channel. While both channels provide automated updates, they behave fundamentally differently regarding minor versions. The 'patch' channel automatically upgrades to the latest patch release within your *current* minor version, but it requires you to manually bump the minor version before it falls out of support. The 'stable' channel automatically upgrades your cluster to the latest patch of the N-1 minor version (one version behind the latest General Availability release). This ensures you are always on a proven, community-tested version without bleeding-edge features that might introduce instability.
</details>

<details>
<summary>4. You are planning a Kubernetes version upgrade for a massive 30-node user pool that processes real-time telemetry data. You want the upgrade to finish as quickly as possible and are willing to pay for extra temporary infrastructure. You set the max surge to 50%. Describe exactly what AKS will do during the first wave of this upgrade.</summary>

Setting max surge to 50% on a 30-node pool means AKS will create 15 additional "surge" nodes simultaneously with the new Kubernetes version. Once these 15 new nodes are ready, AKS will cordon and drain 15 of the old nodes, moving their workloads to the surge nodes or other available capacity. After the old nodes are empty, they are deleted. This aggressive surge drastically reduces the total time required to upgrade the cluster, but it means you will temporarily pay for 45 nodes instead of 30.
</details>

<details>
<summary>5. Your e-commerce application experiences massive, unpredictable traffic spikes during flash sales. The cluster autoscaler successfully requests new nodes, but you notice it takes over 90 seconds for a new node to become `Ready`, which is too slow to handle the sudden influx of users. How can changing the OS disk type solve this problem, and what are the trade-offs?</summary>

You should switch the node pool to use Ephemeral OS disks instead of standard managed disks. Ephemeral OS disks use the virtual machine's local temporary storage (NVMe or SSD) rather than provisioning and attaching a remote network disk. This eliminates the storage provisioning overhead, allowing nodes to boot and become `Ready` in roughly 20-30 seconds instead of 60-90 seconds. The trade-off is that the disk is wiped clean if the node is deallocated, but for stateless Kubernetes nodes, this is actually a benefit as it ensures a pristine, known-good state upon reboot.
</details>

<details>
<summary>6. Your security compliance team requires a unified audit trail for all access grants and the ability to instantly revoke a user's access across all cloud resources, including Kubernetes clusters. They are frustrated by the current process of manually updating `ClusterRoleBindings` in each AKS cluster. How does integrating Entra ID and Azure RBAC solve their problem?</summary>

Integrating Entra ID with Azure RBAC allows you to manage Kubernetes authorization using the exact same Azure role assignment model used for storage accounts or virtual machines. Instead of maintaining disconnected `ClusterRoleBindings` inside each cluster, you assign built-in Azure roles (like 'Azure Kubernetes Service RBAC Writer') directly to Entra ID groups at the cluster or namespace scope. This provides the security team with a single pane of glass for auditing access via the Azure Activity Log, allows them to enforce access via Azure Policy, and ensures that removing a user from an Entra ID group instantly revokes their Kubernetes access without running any `kubectl` commands.
</details>

<details>
<summary>7. A junior administrator notices that the AKS cluster is running out of public IP addresses for new LoadBalancer services. To fix this "quickly", they navigate to the `MC_rg-aks-prod_aks-prod-westeurope_westeurope` resource group in the Azure Portal and manually attach a new Public IP prefix to the cluster's load balancer. A few hours later, the new IPs mysteriously disappear. What went wrong?</summary>

The administrator violated the cardinal rule of AKS: never manually modify resources inside the infrastructure (`MC_`) resource group. AKS uses a continuous reconciliation loop to ensure the actual state of the infrastructure matches the desired state defined in the AKS control plane. When the administrator manually added the IP prefix, they created configuration drift. During the next reconciliation cycle, the AKS resource provider detected this drift and reverted the load balancer back to its original, declared state, deleting the manual changes. All infrastructure changes must be made through the AKS API or `az aks` CLI commands.
</details>

---

## Hands-On Exercise: Production-Grade AKS Cluster with Bicep and Entra ID RBAC

In this exercise, you will deploy a production-ready AKS cluster using Bicep (Azure's infrastructure-as-code language) with Entra ID integration, multiple node pools, availability zones, and proper RBAC.

### Prerequisites

- Azure CLI installed and authenticated (`az login`)
- An Azure subscription with Contributor access
- Bicep CLI (bundled with Azure CLI 2.20+)

### Task 1: Create the Entra ID Groups

Before deploying the cluster, create the Entra ID groups that will map to Kubernetes roles.

<details>
<summary>Solution</summary>

```bash
# Create an admin group for cluster-admin access
az ad group create \
  --display-name "AKS-Prod-Admins" \
  --mail-nickname "aks-prod-admins"

# Create a developer group for namespace-scoped write access
az ad group create \
  --display-name "AKS-Prod-Developers" \
  --mail-nickname "aks-prod-developers"

# Store the group object IDs for use in Bicep
ADMIN_GROUP_ID=$(az ad group show --group "AKS-Prod-Admins" --query id -o tsv)
DEV_GROUP_ID=$(az ad group show --group "AKS-Prod-Developers" --query id -o tsv)

echo "Admin Group ID: $ADMIN_GROUP_ID"
echo "Developer Group ID: $DEV_GROUP_ID"

# Add yourself to the admin group
MY_USER_ID=$(az ad signed-in-user show --query id -o tsv)
az ad group member add --group "AKS-Prod-Admins" --member-id "$MY_USER_ID"
```

</details>

### Task 2: Write the Bicep Template

Create a Bicep file that defines the AKS cluster with all production best practices.

<details>
<summary>Solution</summary>

```bicep
// main.bicep
@description('Location for all resources')
param location string = resourceGroup().location

@description('Entra ID admin group object ID')
param adminGroupObjectId string

@description('Kubernetes version')
param kubernetesVersion string = '1.30.7'

var clusterName = 'aks-prod-${location}'
var systemPoolName = 'system'
var appsPoolName = 'apps'

resource aksCluster 'Microsoft.ContainerService/managedClusters@2024-09-01' = {
  name: clusterName
  location: location
  sku: {
    name: 'Base'
    tier: 'Standard'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    kubernetesVersion: kubernetesVersion
    dnsPrefix: clusterName
    enableRBAC: true

    aadProfile: {
      managed: true
      enableAzureRBAC: true
      adminGroupObjectIDs: [
        adminGroupObjectId
      ]
    }

    autoUpgradeProfile: {
      upgradeChannel: 'stable'
      nodeOSUpgradeChannel: 'NodeImage'
    }

    networkProfile: {
      networkPlugin: 'azure'
      networkPolicy: 'cilium'
      networkDataplane: 'cilium'
      loadBalancerSku: 'standard'
      serviceCidr: '10.0.0.0/16'
      dnsServiceIP: '10.0.0.10'
    }

    agentPoolProfiles: [
      {
        name: systemPoolName
        mode: 'System'
        count: 3
        vmSize: 'Standard_D2s_v5'
        availabilityZones: [ '1', '2', '3' ]
        osDiskType: 'Ephemeral'
        osDiskSizeGB: 64
        osType: 'Linux'
        osSKU: 'AzureLinux'
        maxPods: 30
        enableAutoScaling: false
        upgradeSettings: {
          maxSurge: '33%'
        }
      }
      {
        name: appsPoolName
        mode: 'User'
        count: 3
        vmSize: 'Standard_D4s_v5'
        availabilityZones: [ '1', '2', '3' ]
        osDiskType: 'Ephemeral'
        osDiskSizeGB: 100
        osType: 'Linux'
        osSKU: 'AzureLinux'
        maxPods: 110
        enableAutoScaling: true
        minCount: 3
        maxCount: 12
        upgradeSettings: {
          maxSurge: '33%'
        }
        nodeTaints: []
        nodeLabels: {
          workload: 'general'
        }
      }
    ]
  }
}

output clusterName string = aksCluster.name
output clusterFqdn string = aksCluster.properties.fqdn
output nodeResourceGroup string = aksCluster.properties.nodeResourceGroup
```

</details>

### Task 3: Deploy the Cluster

Deploy the Bicep template and verify the cluster is healthy.

<details>
<summary>Solution</summary>

```bash
# Create the resource group
az group create --name rg-aks-prod --location westeurope

# Deploy the Bicep template
az deployment group create \
  --resource-group rg-aks-prod \
  --template-file main.bicep \
  --parameters adminGroupObjectId="$ADMIN_GROUP_ID"

# Get cluster credentials (Entra ID mode)
az aks get-credentials \
  --resource-group rg-aks-prod \
  --name aks-prod-westeurope \
  --overwrite-existing

# Verify connectivity (this will trigger Entra ID login)
k get nodes -o wide

# Verify node distribution across zones
k get nodes -o custom-columns=NAME:.metadata.name,ZONE:.metadata.labels.'topology\.kubernetes\.io/zone',VERSION:.status.nodeInfo.kubeletVersion
```

</details>

### Task 4: Configure Azure RBAC Role Assignments

Grant the developer group scoped access to a specific namespace.

<details>
<summary>Solution</summary>

```bash
# Create the namespace
k create namespace payments

# Get the cluster resource ID
CLUSTER_ID=$(az aks show -g rg-aks-prod -n aks-prod-westeurope --query id -o tsv)

# Assign the developer group "RBAC Writer" scoped to the payments namespace
az role assignment create \
  --assignee-object-id "$DEV_GROUP_ID" \
  --assignee-principal-type Group \
  --role "Azure Kubernetes Service RBAC Writer" \
  --scope "${CLUSTER_ID}/namespaces/payments"

# Verify the role assignment
az role assignment list \
  --scope "${CLUSTER_ID}/namespaces/payments" \
  --query "[].{Principal:principalName, Role:roleDefinitionName, Scope:scope}" -o table
```

</details>

### Task 5: Add a Maintenance Window and Verify Upgrade Channel

Configure maintenance windows so upgrades only happen during off-peak hours.

<details>
<summary>Solution</summary>

```bash
# Add a weekly maintenance window for Kubernetes upgrades
az aks maintenanceconfiguration add \
  --resource-group rg-aks-prod \
  --cluster-name aks-prod-westeurope \
  --name aksManagedAutoUpgradeSchedule \
  --schedule-type Weekly \
  --day-of-week Saturday \
  --start-time 02:00 \
  --duration 4 \
  --utc-offset "+01:00"

# Add a separate window for node OS image upgrades
az aks maintenanceconfiguration add \
  --resource-group rg-aks-prod \
  --cluster-name aks-prod-westeurope \
  --name aksManagedNodeOSUpgradeSchedule \
  --schedule-type Weekly \
  --day-of-week Sunday \
  --start-time 02:00 \
  --duration 4 \
  --utc-offset "+01:00"

# Verify the configuration
az aks maintenanceconfiguration list \
  --resource-group rg-aks-prod \
  --cluster-name aks-prod-westeurope -o table

# Verify the upgrade channel
az aks show -g rg-aks-prod -n aks-prod-westeurope \
  --query "autoUpgradeProfile" -o json
```

</details>

### Success Criteria

- [ ] Entra ID groups created for admin and developer roles
- [ ] AKS cluster deployed via Bicep with Standard tier
- [ ] System pool: 3 nodes, Standard_D2s_v5, across 3 availability zones, ephemeral OS disks
- [ ] Apps pool: 3-12 nodes (autoscaler enabled), Standard_D4s_v5, across 3 AZs, ephemeral OS disks
- [ ] Entra ID integration enabled with Azure RBAC
- [ ] Developer group has scoped write access to the payments namespace only
- [ ] Maintenance windows configured for Saturday and Sunday off-peak hours
- [ ] Upgrade channel set to "stable"

---

## Next Module

[Module 7.2: AKS Advanced Networking](../module-7.2-aks-networking/) --- Dive into the networking layer: compare Azure CNI, Kubenet, CNI Overlay, and CNI Powered by Cilium. Learn when to use each, how to implement network policies, and how to expose services through AGIC and Private Link.