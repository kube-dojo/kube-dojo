---
title: "Module 5.1: Private Cloud Platforms"
slug: on-premises/multi-cluster/module-5.1-private-cloud
sidebar:
  order: 2
---

> **Complexity**: `[INTERMEDIATE]` | Time: 45 minutes
>
> **Prerequisites**: [Module 1.1: The Case for On-Premises](../../planning/module-1.1-case-for-on-prem/), [Module 2.4: Declarative Bare Metal](../../provisioning/module-2.4-declarative-bare-metal/)

---

## Why This Module Matters

A mid-size bank ran Kubernetes on bare metal for two years. Their platform team of three engineers spent 40% of their time on hardware lifecycle: firmware updates required draining nodes manually, disk replacements meant SSH sessions and fdisk, and provisioning a new cluster took two weeks of BIOS configuration, OS installs, and kubeadm bootstrapping.

They migrated to VMware vSphere with Tanzu. Provisioning a new cluster dropped from two weeks to 45 minutes. When a physical host needed firmware updates, vSphere live-migrated the VMs automatically. Disk failures were handled by vSAN without any Kubernetes disruption. The platform team's hardware toil dropped from 40% to 5% of their time.

The tradeoff: VMware licensing cost them $180,000/year for 20 hosts. An equivalent OpenStack deployment would cost $0 in licensing but require two additional engineers to operate. A third option, Harvester, offered a middle ground: open-source, simpler than OpenStack, and purpose-built for running Kubernetes VMs on bare metal.

This module covers when to virtualize, when to stay on bare metal, and how to choose between the three dominant private cloud platforms.

---

## What You'll Learn

- VMware vSphere architecture and Tanzu Kubernetes Grid
- OpenStack components relevant to Kubernetes (Nova, Cinder, Neutron, Magnum)
- Harvester as a cloud-native HCI alternative
- vSphere CSI and OpenStack Cinder for persistent storage
- When to virtualize vs run Kubernetes on bare metal
- Cost comparison framework for platform decisions

---

## Bare Metal vs Virtualized Kubernetes

```
┌─────────────────────────────────────────────────────────────────┐
│          BARE METAL vs VIRTUALIZED KUBERNETES                    │
│                                                                   │
│   Bare Metal:                                                    │
│   ┌──────────────────────────────────┐                          │
│   │  Kubernetes (kubeadm/k3s)        │                          │
│   │  Linux OS (Ubuntu/RHEL/Talos)    │                          │
│   │  Physical Server Hardware        │                          │
│   └──────────────────────────────────┘                          │
│   + Maximum performance (no hypervisor tax)                      │
│   + No licensing costs                                           │
│   - Hardware lifecycle is manual                                 │
│   - No live migration (node drain required)                      │
│                                                                   │
│   Virtualized:                                                   │
│   ┌──────────────────────────────────┐                          │
│   │  Kubernetes (TKG/Magnum/k3s)     │                          │
│   │  Guest OS (Ubuntu/Flatcar)       │                          │
│   │  Virtual Machine                 │                          │
│   │  Hypervisor (ESXi/KVM/Harvester) │                          │
│   │  Physical Server Hardware        │                          │
│   └──────────────────────────────────┘                          │
│   + Live migration for maintenance                               │
│   + VM snapshots for rollback                                    │
│   + Multi-tenancy isolation (hardware-level)                     │
│   - 5-15% CPU overhead from hypervisor                           │
│   - Licensing cost (VMware) or operational cost (OpenStack)      │
│                                                                   │
│   Decision: Virtualize unless you need every last CPU cycle      │
│   (HPC, ML training, real-time systems) or run < 5 servers.     │
└─────────────────────────────────────────────────────────────────┘
```

---

## VMware vSphere + Tanzu

VMware vSphere is the dominant enterprise hypervisor. Tanzu Kubernetes Grid (TKG) is VMware's Kubernetes distribution that runs on top of vSphere, using the vSphere infrastructure for VM lifecycle, storage (vSAN/VMFS), and networking (NSX or standard vSwitch).

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                vSPHERE + TANZU ARCHITECTURE                   │
│                                                                │
│   ┌─────────────────────────────────────┐                    │
│   │        vCenter Server               │  Management        │
│   │   - Cluster management              │  plane             │
│   │   - DRS (auto VM placement)         │                    │
│   │   - HA (auto VM restart)            │                    │
│   │   - vMotion (live migration)        │                    │
│   └─────────────────────────────────────┘                    │
│                     │                                         │
│   ┌─────────────────┴───────────────────┐                    │
│   │        Supervisor Cluster           │  TKG management    │
│   │   - Runs on vSphere control plane   │                    │
│   │   - Manages TKC lifecycle           │                    │
│   │   - Integrates with vSphere auth    │                    │
│   └─────────────────────────────────────┘                    │
│         │               │              │                      │
│   ┌─────┴────┐   ┌─────┴────┐   ┌─────┴────┐               │
│   │  TKC 1   │   │  TKC 2   │   │  TKC 3   │  Workload     │
│   │  (dev)   │   │  (staging)│   │  (prod)  │  clusters     │
│   │  3 VMs   │   │  5 VMs   │   │  9 VMs   │               │
│   └──────────┘   └──────────┘   └──────────┘               │
│                                                                │
│   Each TKC (TanzuKubernetesCluster) is a set of VMs          │
│   running a full Kubernetes cluster.                           │
│   vSphere handles: VM placement, storage, networking, HA.     │
│                                                                │
│   Storage: vSphere CSI driver provisions VMDKs as PVs        │
│   Networking: NSX-T or Antrea for pod networking              │
└──────────────────────────────────────────────────────────────┘
```

### vSphere CSI Driver

The vSphere CSI driver creates VMDK (Virtual Machine Disk) files on vSphere datastores and attaches them to Kubernetes nodes as block devices.

```yaml
# vSphere StorageClass
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: vsphere-sc
provisioner: csi.vsphere.vmware.com
parameters:
  storagepolicyname: "vSAN Default Storage Policy"
  datastoreurl: "ds:///vmfs/volumes/vsan-datastore/"
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

```bash
# Verify vSphere CSI is running
kubectl get pods -n vmware-system-csi
# vsphere-csi-controller-0   Running
# vsphere-csi-node-xxxxx     Running (DaemonSet)

# Create a PVC backed by vSphere storage
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: vsphere-pvc
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: vsphere-sc
  resources:
    requests:
      storage: 10Gi
EOF

# The PV is a VMDK on the vSphere datastore
kubectl get pv -o jsonpath='{.items[0].spec.csi.volumeHandle}'
# file:///vmfs/volumes/vsan-datastore/fcd/abc123.vmdk
```

---

## OpenStack + Magnum

OpenStack is the open-source alternative to vSphere. It provides compute (Nova), storage (Cinder), networking (Neutron), identity (Keystone), and image management (Glance). Magnum is the OpenStack project that manages Kubernetes clusters as a service.

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│             OPENSTACK + MAGNUM ARCHITECTURE                   │
│                                                                │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│   │Keystone  │  │ Glance  │  │  Nova   │  │ Neutron │      │
│   │(identity)│  │ (images)│  │(compute)│  │ (network│      │
│   └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐                    │
│   │ Cinder  │  │  Heat   │  │ Magnum  │                    │
│   │(block   │  │ (orch-  │  │ (K8s    │                    │
│   │ storage)│  │ estrat.)│  │ clusters│                    │
│   └─────────┘  └─────────┘  └─────────┘                    │
│                                  │                           │
│                    ┌─────────────┴────────────┐             │
│                    │      Magnum Cluster       │             │
│                    │                           │             │
│                    │  ┌────┐ ┌────┐ ┌────┐   │             │
│                    │  │ CP │ │ W1 │ │ W2 │   │  Nova VMs   │
│                    │  └────┘ └────┘ └────┘   │             │
│                    │                           │             │
│                    │  Cinder volumes as PVs   │             │
│                    │  Neutron for pod network  │             │
│                    └───────────────────────────┘             │
│                                                                │
│   Magnum uses Heat templates to orchestrate VM creation.      │
│   Each K8s cluster = Heat stack = set of Nova instances.      │
│   Cinder CSI provides persistent volumes.                     │
└──────────────────────────────────────────────────────────────┘
```

### Magnum Cluster Creation

```bash
# Create a cluster template
openstack coe cluster template create k8s-template \
  --image fedora-coreos-40 \
  --external-network public \
  --master-flavor m1.large \
  --flavor m1.xlarge \
  --docker-volume-size 50 \
  --network-driver flannel \
  --volume-driver cinder \
  --coe kubernetes

# Create a cluster
openstack coe cluster create prod-k8s \
  --cluster-template k8s-template \
  --master-count 3 \
  --node-count 5 \
  --keypair my-key

# Get kubeconfig
openstack coe cluster config prod-k8s --dir ~/.kube/
export KUBECONFIG=~/.kube/config

# Cinder CSI is auto-configured by Magnum
kubectl get sc
# NAME            PROVISIONER                  VOLUMEBINDINGMODE
# cinder-default  cinder.csi.openstack.org     Immediate
```

### OpenStack Cinder CSI

```yaml
# Cinder StorageClass with SSD backend
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: cinder-ssd
provisioner: cinder.csi.openstack.org
parameters:
  type: "SSD"       # Must match a Cinder volume type
  availability: "nova"
reclaimPolicy: Delete
allowVolumeExpansion: true
```

---

## Harvester (SUSE)

Harvester is a purpose-built HCI (Hyper-Converged Infrastructure) platform for running VMs on bare metal. It combines KubeVirt (VMs as Kubernetes pods), Longhorn (distributed storage), and a web UI into a single installable ISO. Harvester is designed specifically as an infrastructure layer for running Kubernetes clusters.

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                 HARVESTER ARCHITECTURE                        │
│                                                                │
│   ┌──────────────────────────────────────┐                   │
│   │          Harvester Cluster           │  Runs on          │
│   │       (Kubernetes + KubeVirt)        │  bare metal       │
│   │                                      │                   │
│   │  ┌──────────┐  ┌──────────────────┐ │                   │
│   │  │ Longhorn  │  │ KubeVirt         │ │                   │
│   │  │ (storage) │  │ (VM management)  │ │                   │
│   │  └──────────┘  └──────────────────┘ │                   │
│   │  ┌──────────┐  ┌──────────────────┐ │                   │
│   │  │ Harvester │  │ Rancher MCM      │ │                   │
│   │  │ UI / API  │  │ (optional)       │ │                   │
│   │  └──────────┘  └──────────────────┘ │                   │
│   └──────────────────────────────────────┘                   │
│              │              │              │                   │
│   ┌──────────┴──┐   ┌──────┴───┐   ┌─────┴────┐            │
│   │  Guest K8s  │   │ Guest K8s│   │ Guest K8s│  Workload   │
│   │  Cluster 1  │   │ Cluster 2│   │ Cluster 3│  clusters   │
│   │  (VMs)      │   │ (VMs)    │   │ (VMs)    │  inside VMs │
│   └─────────────┘   └──────────┘   └──────────┘            │
│                                                                │
│   Key difference from vSphere/OpenStack:                      │
│   - Harvester IS a Kubernetes cluster running VMs via KubeVirt│
│   - No separate hypervisor layer (KVM is the hypervisor)      │
│   - Longhorn provides replicated storage automatically        │
│   - Free and open-source (Apache 2.0 license)                │
└──────────────────────────────────────────────────────────────┘
```

### Harvester VM Creation

```yaml
# Harvester VirtualMachine CRD (KubeVirt)
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: k8s-worker-01
  namespace: k8s-prod
spec:
  running: true
  template:
    spec:
      domain:
        cpu:
          cores: 8
        resources:
          requests:
            memory: 16Gi
        devices:
          disks:
            - name: rootdisk
              disk:
                bus: virtio
            - name: datadisk
              disk:
                bus: virtio
      volumes:
        - name: rootdisk
          dataVolume:
            name: k8s-worker-01-root
        - name: datadisk
          dataVolume:
            name: k8s-worker-01-data
---
# Data volume backed by Longhorn
apiVersion: cdi.kubevirt.io/v1beta1
kind: DataVolume
metadata:
  name: k8s-worker-01-root
spec:
  source:
    http:
      url: "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img"
  pvc:
    accessModes: ["ReadWriteOnce"]
    storageClassName: longhorn
    resources:
      requests:
        storage: 50Gi
```

---

## Platform Comparison

| Dimension | VMware vSphere | OpenStack | Harvester |
|-----------|---------------|-----------|-----------|
| License cost (20 hosts) | ~$180K/year | $0 | $0 |
| Engineering staff | 1-2 VMware admins | 3-5 OpenStack engineers | 1-2 platform engineers |
| Setup time | 2-3 days | 2-4 weeks | 4-8 hours |
| Live migration | vMotion (mature) | Nova live-migrate (works) | KubeVirt live migration |
| Storage | vSAN, VMFS, NFS | Cinder (pluggable) | Longhorn (built-in) |
| Networking | NSX-T, vSwitch | Neutron (OVS, OVN) | Multus, VLAN |
| K8s integration | TKG (native) | Magnum (separate) | Rancher (native) |
| GPU passthrough | Good (vGPU) | Good (PCI passthrough) | KubeVirt GPU support |
| Maturity | 20+ years | 12+ years | 3+ years |
| Best for | Enterprise, compliance | Large-scale, customization | SMB, edge, new deployments |

### Total Cost of Ownership (3-Year, 20 Hosts)

```
┌────────────────────────────────────────────────────────────┐
│          3-YEAR TCO COMPARISON (20 HOSTS)                   │
│                                                              │
│   VMware vSphere:                                           │
│   License:        $180K/yr x 3 = $540K                      │
│   Staff (1.5 FTE): $195K/yr x 3 = $585K                    │
│   Support:        $36K/yr x 3  = $108K                      │
│   Total:                         $1,233K                     │
│                                                              │
│   OpenStack:                                                 │
│   License:        $0                                         │
│   Staff (4 FTE):  $520K/yr x 3 = $1,560K                   │
│   Training:       $50K                                       │
│   Total:                         $1,610K                     │
│                                                              │
│   Harvester:                                                 │
│   License:        $0                                         │
│   Staff (1.5 FTE): $195K/yr x 3 = $585K                    │
│   SUSE support:   $24K/yr x 3 = $72K (optional)            │
│   Total:                         $585K-$657K                │
│                                                              │
│   Note: Staff costs assume US market rates.                 │
│   OpenStack requires more engineers due to component        │
│   complexity (15+ services to operate).                      │
└────────────────────────────────────────────────────────────┘
```

---

## When to Virtualize vs Stay on Bare Metal

```bash
# Decision checklist (answer yes/no)

# 1. Do you run > 10 physical servers?
#    Yes -> Virtualize (hardware lifecycle savings outweigh overhead)
#    No  -> Bare metal may be simpler

# 2. Do you need multiple isolated clusters?
#    Yes -> Virtualize (VMs provide hardware-level isolation)
#    No  -> Bare metal with namespaces may suffice

# 3. Is maximum CPU/GPU performance critical?
#    Yes -> Bare metal (no hypervisor tax: 5-15% CPU, 2-5% memory)
#    No  -> Virtualize

# 4. Do you have VMware expertise in-house?
#    Yes -> vSphere + Tanzu (leverage existing skills)
#    No  -> Harvester (lowest learning curve)

# 5. Budget for licensing?
#    Yes -> vSphere (most mature, best enterprise support)
#    No  -> Harvester (free) or OpenStack (free but complex)
```

---

## Did You Know?

- **VMware was acquired by Broadcom in 2023 for $61 billion**, and subsequent licensing changes drove many organizations to evaluate alternatives. Broadcom eliminated perpetual licenses in favor of subscription-only models and consolidated product bundles, increasing costs for some customers by 2-10x. This accelerated interest in Harvester and OpenStack.

- **OpenStack runs some of the largest private clouds in the world.** Walmart operates one of the biggest OpenStack deployments: over 200,000 cores across multiple data centers. CERN runs OpenStack for physics research computing alongside their massive Ceph deployment. The scale ceiling is effectively unlimited.

- **Harvester was built specifically because Rancher Labs needed a VM platform for their Kubernetes customers.** Before Harvester, customers had to choose between expensive VMware licenses or complex OpenStack deployments just to run VMs that would host Kubernetes. Harvester runs KubeVirt on bare metal, eliminating the need for a traditional hypervisor.

- **The "hypervisor tax" is real but often overstated.** Modern CPUs with VT-x/VT-d hardware virtualization extensions reduce the overhead to 2-5% for CPU-bound workloads. The real cost of virtualization is memory overhead (each VM needs its own kernel, ~200-500 MB) and I/O overhead for storage and network (mitigated by virtio and SR-IOV).

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Running OpenStack without dedicated team | OpenStack has 15+ services, each with its own failure modes | Budget 3-5 FTEs or use a managed OpenStack distribution |
| vSphere without vSAN | VMFS on local disks means no live migration (shared storage required) | Deploy vSAN or connect to external NFS/iSCSI storage |
| Harvester on < 3 nodes | Longhorn needs 3 nodes for replica placement, etcd needs quorum | Minimum 3 nodes for production Harvester |
| Not sizing VMs for K8s | VMs too small for kubelet overhead (~500 MB) + workloads | Minimum 4 vCPU, 8 GB RAM per K8s node VM |
| Ignoring nested virtualization | Running KubeVirt inside VMs requires nested virt support | Enable nested virtualization in hypervisor or avoid KubeVirt-in-VM |
| No storage tiering | All VMs on the same datastore, databases compete with logs | Create separate storage policies for fast (NVMe) and bulk (HDD) |
| Skipping HA for vCenter/Keystone | Management plane outage prevents all VM operations | Deploy vCenter HA or Keystone with Galera + HAProxy |

---

## Quiz

### Question 1
Your company has 30 bare-metal servers, 3 VMware admins, and wants to run 5 Kubernetes clusters (dev, staging, prod, ML, data). Should you use vSphere+Tanzu, OpenStack+Magnum, or Harvester?

<details>
<summary>Answer</summary>

**vSphere + Tanzu.** The decision factors:

1. **Existing expertise**: 3 VMware admins already know vSphere. Switching to OpenStack or Harvester means retraining and a productivity dip during migration.

2. **Scale**: 30 servers is well within vSphere's sweet spot. OpenStack's operational complexity is not justified at this scale. Harvester could work but is less mature.

3. **5 clusters**: Tanzu Kubernetes Grid makes multi-cluster management straightforward with the Supervisor Cluster managing all TKC lifecycle.

4. **Licensing cost**: At 30 hosts, VMware licensing will be ~$270K/year. This is significant but justified by the reduced staffing needs (3 existing admins vs hiring 3-5 OpenStack engineers).

**When the answer would change**:
- If the VMware admins are leaving or the budget is cut: Harvester
- If you are scaling to 100+ hosts: OpenStack becomes more cost-effective
- If these are GPU servers for ML: Bare metal for the ML cluster, vSphere for the rest
</details>

### Question 2
You are running Kubernetes on vSphere. A physical ESXi host needs a firmware update that requires a reboot. What happens to the Kubernetes nodes (VMs) on that host?

<details>
<summary>Answer</summary>

**vSphere DRS and vMotion handle this automatically** if configured correctly:

1. Put the ESXi host into **maintenance mode** (via vCenter)
2. vSphere **live-migrates** (vMotion) all VMs to other ESXi hosts in the cluster
3. VMs continue running during migration -- Kubernetes sees no interruption
4. The ESXi host reboots, applies firmware, and returns to the cluster
5. DRS may migrate some VMs back to rebalance load

**Requirements for this to work**:
- Shared storage (vSAN, NFS, or iSCSI) -- VMs must be accessible from any host
- vMotion network configured between hosts (dedicated VLAN, low latency)
- DRS enabled in at least "partially automated" mode
- Enough capacity on remaining hosts to absorb migrated VMs

**If shared storage is NOT configured**: VMs must be powered off, which means Kubernetes node drain first, then VM shutdown, then firmware update, then VM restart. This is no better than bare metal.
</details>

### Question 3
An organization wants to run Harvester on 3 servers with 64 GB RAM each. How many Kubernetes cluster VMs can they reasonably run?

<details>
<summary>Answer</summary>

**Calculate available resources**:

Total RAM: 3 x 64 GB = 192 GB

Harvester overhead (per node):
- Harvester OS + K8s: ~4 GB
- Longhorn: ~2 GB
- KubeVirt + system: ~2 GB
- Total per node: ~8 GB
- Total overhead: 3 x 8 GB = 24 GB

Available for guest VMs: 192 - 24 = **168 GB**

Minimum K8s node sizing:
- Control plane VM: 4 GB RAM
- Worker VM: 8 GB RAM
- Minimum cluster (1 CP + 2 workers): 20 GB

**Reasonable allocation**:
- Production cluster (3 CP + 3 workers): 3x4 + 3x8 = 36 GB
- Staging cluster (1 CP + 2 workers): 4 + 16 = 20 GB
- Dev cluster (1 CP + 1 worker): 4 + 8 = 12 GB
- Total: 68 GB used, 100 GB remaining for workloads

**Answer**: 3-4 small clusters, or 2 production-sized clusters. Keep 20% RAM headroom for Longhorn rebuilds and VM live migration.
</details>

### Question 4
Why would you choose OpenStack over Harvester for a 200-server deployment, despite OpenStack's higher operational complexity?

<details>
<summary>Answer</summary>

At 200 servers, OpenStack's advantages outweigh its operational cost:

1. **Multi-tenancy**: OpenStack Keystone provides project-level isolation with quotas, RBAC, and billing integration. Harvester's multi-tenancy is based on Kubernetes namespaces, which is less mature for large organizations with many teams.

2. **Networking**: Neutron with OVN/OVS provides sophisticated virtual networking -- routers, floating IPs, security groups, VPN-as-a-service, load-balancer-as-a-service. Harvester's networking is simpler (VLAN-based) and may not meet complex enterprise requirements.

3. **Storage flexibility**: Cinder supports dozens of storage backends (NetApp, Pure Storage, Ceph, LVM). Harvester is locked to Longhorn, which may not meet enterprise storage requirements (e.g., deduplication, thin provisioning at scale).

4. **Ecosystem**: At 200 servers, you likely need bare-metal management (Ironic), DNS (Designate), key management (Barbican), and container registry (Harbor via Kolla). OpenStack has mature projects for each.

5. **Proven scale**: OpenStack is proven at 200+ server scale at Walmart, CERN, and dozens of telecoms. Harvester's largest deployments are typically 10-30 nodes.

**The cost tradeoff**: 4-5 OpenStack engineers at $130K each = $520-650K/year. At 200 servers, this is $2,600-3,250 per server per year -- far less than VMware licensing.
</details>

---

## Hands-On Exercise: Explore Harvester with a Nested Lab

```bash
# Requirements: Linux host with KVM and 32+ GB RAM

# Step 1: Download Harvester ISO
HARVESTER_VERSION="v1.3.1"
wget "https://releases.rancher.com/harvester/${HARVESTER_VERSION}/harvester-${HARVESTER_VERSION}-amd64.iso"

# Step 2: Create a virtual network
sudo virsh net-define /dev/stdin <<EOF
<network>
  <name>harvester</name>
  <forward mode='nat'/>
  <bridge name='virbr-harv' stp='on' delay='0'/>
  <ip address='192.168.200.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='192.168.200.10' end='192.168.200.254'/>
    </dhcp>
  </ip>
</network>
EOF
sudo virsh net-start harvester

# Step 3: Create the first Harvester node
sudo virt-install \
  --name harvester-node1 \
  --ram 16384 --vcpus 4 --cpu host-passthrough \
  --disk size=120,bus=virtio --disk size=50,bus=virtio \
  --cdrom "harvester-${HARVESTER_VERSION}-amd64.iso" \
  --network network=harvester,model=virtio \
  --graphics vnc,listen=0.0.0.0 --os-variant generic --boot uefi

# Step 4: After installation, access UI at https://192.168.200.10
# Step 5: Create VMs via KubeVirt CRDs for K8s nodes
```

### Success Criteria

- [ ] Harvester ISO downloaded and virtual network created
- [ ] First Harvester node created (or understood the process)
- [ ] Understood the VM creation workflow via KubeVirt CRDs

---

## Next Module

Continue to [Module 5.2: Multi-Cluster Control Planes](module-5.2-multi-cluster-control-planes/) to learn how vCluster and Kamaji let you run dozens of Kubernetes control planes on limited hardware.
