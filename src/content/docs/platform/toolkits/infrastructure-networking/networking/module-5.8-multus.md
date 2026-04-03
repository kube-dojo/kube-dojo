---
title: "Module 5.8: Multus CNI - Multi-Network Pods for Specialized Workloads"
slug: platform/toolkits/infrastructure-networking/networking/module-5.8-multus
sidebar:
  order: 9
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 55-70 minutes

## The Pod That Needed Three Networks

*A telecom provider is deploying their 5G core on Kubernetes. The project is six months in, and the architects hit a wall.*

```
[ARCHITECTURE REVIEW - Week 24]

Lead Architect:  "Each 5G network function needs three interfaces."
K8s Engineer:    "Kubernetes gives you one. That's the CNI model."
Lead Architect:  "One interface can't meet 3GPP requirements."
K8s Engineer:    "What exactly do you need?"

Lead Architect:  "Interface 1 - Management plane: 10.0.0.0/8
                  Standard pod networking via Calico. Health checks,
                  API calls, orchestration. Normal stuff.

                  Interface 2 - Signaling plane: 172.16.0.0/12
                  SIP, Diameter, GTP-C protocols via Macvlan.
                  Must be isolated from management traffic.

                  Interface 3 - User data plane: direct SR-IOV
                  25 Gbps line rate. Real user traffic - voice, video,
                  data sessions. Cannot go through the kernel stack.
                  Every microsecond of latency costs call quality."

K8s Engineer:    "So we need a pod with three network interfaces,
                  each on a different physical network, with different
                  performance characteristics?"
Lead Architect:  "Exactly. And the data plane must bypass the kernel
                  entirely. We measured 40% packet loss at peak load
                  going through the standard network stack."
K8s Engineer:    "There's a project called Multus..."
```

That conversation happens in some form at every telecom company, every financial trading firm, and every HPC lab that tries to run specialized workloads on Kubernetes. The standard Kubernetes networking model -- one interface per pod, managed by one CNI plugin -- is elegant and sufficient for 90% of workloads. But for the other 10%, it is a dealbreaker.

Multus breaks the "one network per pod" assumption. By the end of this module, you will understand how to give pods multiple network interfaces, when you actually need this, and how to avoid the pitfalls that catch every team on their first deployment.

**What You'll Learn**:
- Why the single-network model breaks down for telecom, finance, and HPC
- How Multus works as a "meta-plugin" that delegates to other CNIs
- NetworkAttachmentDefinition CRD for defining secondary networks
- Macvlan, IPvlan, Bridge, and SR-IOV network types
- IP address management with Whereabouts
- Real-world multi-network pod configurations

**Prerequisites**:
- Kubernetes networking basics (Pods, Services, CNI)
- [Module 5.1: Cilium](../module-5.1-cilium/) or equivalent CNI knowledge
- Linux networking fundamentals (interfaces, VLANs, bridges)
- Basic understanding of container networking

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Multus CNI to attach multiple network interfaces to Kubernetes pods**
- **Configure NetworkAttachmentDefinitions for SR-IOV, Macvlan, and IPVLAN secondary networks**
- **Implement Multus with Whereabouts IPAM for consistent IP address management across interfaces**
- **Evaluate multi-network pod architectures for NFV, telco, and data-intensive workload requirements**


## Why This Module Matters

Kubernetes was designed for web applications. The networking model reflects this: every pod gets one IP address on one flat network, and Services handle load balancing. For microservices serving HTTP APIs, this is perfect.

But the world runs on more than HTTP APIs.

A 5G core network function processes millions of voice and data sessions simultaneously. A high-frequency trading system needs sub-microsecond latency on its market data feed. An HPC cluster runs MPI jobs across hundreds of nodes using InfiniBand. A storage appliance needs a dedicated iSCSI network that never, under any circumstances, shares bandwidth with application traffic.

These workloads all share one requirement: **multiple, isolated network paths with different performance characteristics**. Standard Kubernetes cannot provide this. Multus can.

> **Did You Know?** Multus is a Latin word meaning "many" or "multiple." The project was created by Intel to solve exactly the telecom use case described in our opening story. It became a CNCF Sandbox project and is now the de facto standard for multi-network Kubernetes deployments. Every major telecom provider running 5G on Kubernetes -- including Verizon, AT&T, and Vodafone -- uses Multus.

---

## Part 1: Why Multiple Networks?

### The Four Reasons You Need More Than One Interface

#### 1. Separation of Concerns

Different traffic types have fundamentally different requirements:

```
SINGLE NETWORK (standard Kubernetes)
═══════════════════════════════════════════════════════════════
                    ┌─────────────┐
  Management ──────▶│             │
  Signaling  ──────▶│  eth0       │  All traffic shares
  User Data  ──────▶│  10.244.1.5 │  one interface, one
  Storage    ──────▶│             │  network, one fate.
                    └─────────────┘

  Problem: A storage backup saturates the link.
           Signaling traffic gets delayed.
           Users hear choppy audio on their calls.


MULTIPLE NETWORKS (with Multus)
═══════════════════════════════════════════════════════════════
                    ┌─────────────┐
  Management ──────▶│ eth0        │  Calico overlay
                    │ 10.244.1.5  │  (standard K8s networking)
                    ├─────────────┤
  Signaling  ──────▶│ net1        │  Macvlan on VLAN 100
                    │ 172.16.1.10 │  (isolated L2 segment)
                    ├─────────────┤
  User Data  ──────▶│ net2        │  SR-IOV VF
                    │ 192.168.1.5 │  (hardware-accelerated)
                    ├─────────────┤
  Storage    ──────▶│ net3        │  IPvlan on VLAN 200
                    │ 10.10.1.5   │  (dedicated storage net)
                    └─────────────┘

  Each traffic type has its own path.
  Storage backup? Doesn't touch signaling.
```

#### 2. Performance (SR-IOV and Kernel Bypass)

Standard Kubernetes networking goes through the Linux kernel network stack. For most workloads this is fine. For line-rate packet processing, the kernel is the bottleneck:

| Path | Throughput | Latency | Use Case |
|------|-----------|---------|----------|
| Standard CNI (kernel) | ~10 Gbps | ~50-100 us | Web apps, APIs |
| Macvlan | ~15 Gbps | ~20-40 us | Moderate performance needs |
| SR-IOV | 25-100 Gbps | ~5-10 us | Telecom data plane, HPC |
| DPDK + SR-IOV | Line rate | ~1-2 us | Packet processing, NFV |

SR-IOV (Single Root I/O Virtualization) creates virtual functions directly on the NIC hardware. The pod talks to the NIC without the kernel ever seeing the packets. This is how you get 25 Gbps with predictable latency.

#### 3. Compliance and Isolation

Some regulatory requirements mandate physical network separation:

- **PCI DSS**: Cardholder data must traverse specific network segments
- **HIPAA**: Patient data networks must be isolated
- **3GPP**: Telecom signaling and user data planes must be separated
- **MiFID II**: Financial trading audit trails on dedicated networks

You cannot satisfy "this traffic must stay on VLAN 100 connected to physical switch port Gi0/24" with an overlay network. You need a direct connection to the physical infrastructure.

#### 4. Legacy Integration

Kubernetes does not exist in a vacuum. Real enterprises have:

- Bare-metal database servers on specific VLANs
- Network appliances (firewalls, load balancers) expecting traffic on particular subnets
- Monitoring infrastructure that taps specific physical segments
- Non-Kubernetes workloads that pods must communicate with on existing networks

Multus lets pods join these existing networks without re-architecting the entire infrastructure.

> **Did You Know?** The Kubernetes CNI specification was deliberately designed to support chaining and multiple plugins from the beginning. The spec allows a runtime to call multiple CNI plugins in sequence. Multus leverages this by acting as the first (and only) CNI the kubelet calls, then delegating to other plugins internally. The spec authors anticipated that "one size fits all" networking would not be enough.

---

## Part 2: Multus Architecture

### The Meta-Plugin Concept

Multus is not a CNI plugin in the traditional sense. It does not configure networks itself. Instead, it is a **meta-plugin** -- a CNI that calls other CNIs:

```
HOW MULTUS WORKS
═══════════════════════════════════════════════════════════════

Normal Kubernetes (without Multus):

  kubelet ──▶ CNI Plugin (e.g., Calico) ──▶ Creates eth0

  Result: Pod has one interface (eth0)


With Multus:

  kubelet ──▶ Multus (meta-plugin)
                │
                ├──▶ Delegate 1: Calico  ──▶ Creates eth0 (default)
                │
                ├──▶ Delegate 2: Macvlan ──▶ Creates net1
                │
                └──▶ Delegate 3: SR-IOV  ──▶ Creates net2

  Result: Pod has three interfaces (eth0, net1, net2)
```

The key insight: **Multus does not replace your existing CNI. It wraps it.** Your primary CNI (Calico, Cilium, Flannel -- whatever you already use) remains the default network. Multus adds the ability to attach additional networks on top.

### The Full Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        KUBERNETES NODE                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     kubelet                               │  │
│  │  "Create pod X" ──▶ calls CNI binary                     │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 Multus CNI (meta-plugin)                   │  │
│  │                                                            │  │
│  │  1. Read pod annotations                                  │  │
│  │  2. Look up NetworkAttachmentDefinitions                  │  │
│  │  3. Call delegate CNIs in order                            │  │
│  │  4. Return combined result to kubelet                     │  │
│  └───┬──────────────┬──────────────┬────────────────────────┘  │
│      │              │              │                             │
│      ▼              ▼              ▼                             │
│  ┌────────┐   ┌──────────┐   ┌──────────┐                     │
│  │ Calico │   │ Macvlan  │   │  SR-IOV  │   Delegate Plugins  │
│  │ (eth0) │   │ (net1)   │   │  (net2)  │                     │
│  └───┬────┘   └────┬─────┘   └────┬─────┘                     │
│      │              │              │                             │
│  ┌───┴──────────────┴──────────────┴─────────────────────────┐ │
│  │                    POD NETWORK NAMESPACE                    │ │
│  │                                                             │ │
│  │   eth0: 10.244.1.5/24    (Calico overlay - default)       │ │
│  │   net1: 172.16.1.10/24   (Macvlan on VLAN 100)            │ │
│  │   net2: 192.168.1.5/24   (SR-IOV VF - hardware)           │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Physical NICs:                                                   │
│  ┌──────┐  ┌──────┐  ┌──────────────┐                          │
│  │ ens3 │  │ens4  │  │ ens5 (SR-IOV)│                          │
│  │      │  │VLAN  │  │ VF0 VF1 VF2  │                          │
│  │      │  │100   │  │              │                           │
│  └──┬───┘  └──┬───┘  └──────┬───────┘                          │
│     │         │              │                                   │
└─────┼─────────┼──────────────┼───────────────────────────────────┘
      │         │              │
   Overlay   VLAN 100      Direct NIC
   Network   (signaling)   (data plane)
```

### The Request Flow

Here is exactly what happens when a pod with multiple networks is created:

1. **User creates Pod** with annotation `k8s.v1.cni.cncf.io/networks: macvlan-conf`
2. **kubelet** sees the pod needs networking, calls the CNI binary
3. **Multus** is the configured CNI. It reads `/etc/cni/net.d/00-multus.conf`
4. **Multus calls the default delegate** (e.g., Calico) to create `eth0`
5. **Multus reads the pod annotation** to find additional networks
6. **Multus looks up the NetworkAttachmentDefinition** `macvlan-conf` from the Kubernetes API
7. **Multus calls the Macvlan CNI plugin** with the config from the NetworkAttachmentDefinition
8. **Macvlan plugin creates `net1`** in the pod's network namespace
9. **Multus returns the combined result** (both interfaces) to kubelet
10. **Pod starts** with `eth0` (Calico) and `net1` (Macvlan)

> **Did You Know?** Multus supports two modes of operation: "thick" and "thin." In thin mode (the default since Multus v4), a lightweight shim binary on each node communicates with a Multus daemon running as a DaemonSet. This makes upgrades easier -- you update the DaemonSet instead of replacing binaries on every node. The thick mode embeds all logic in the CNI binary itself, which was the original design but harder to manage at scale.

---

## Part 3: NetworkAttachmentDefinition CRD

The `NetworkAttachmentDefinition` (often abbreviated `net-attach-def`) is how you tell Multus about additional networks. It is a Custom Resource Definition that wraps a CNI plugin configuration.

### Macvlan (Most Common Secondary Network)

Macvlan creates virtual interfaces that share a physical interface but have their own MAC and IP addresses. Each virtual interface appears as a separate device on the physical network.

```yaml
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: macvlan-conf
  namespace: default
spec:
  config: '{
    "cniVersion": "0.3.1",
    "type": "macvlan",
    "master": "eth0",
    "mode": "bridge",
    "ipam": {
      "type": "whereabouts",
      "range": "172.16.1.0/24",
      "range_start": "172.16.1.100",
      "range_end": "172.16.1.200"
    }
  }'
```

**Macvlan modes explained:**

| Mode | Description | Use Case |
|------|-------------|----------|
| `bridge` | VMs can communicate with each other and external | Most common, general purpose |
| `vepa` | All traffic goes to external switch first | When switch-level policy is needed |
| `private` | VMs completely isolated from each other | Maximum isolation |
| `passthru` | Entire interface passed to one container | Single-tenant high performance |

**Important limitation**: In Macvlan, the host cannot communicate with the Macvlan interfaces. Traffic between the host and a Macvlan sub-interface must go through an external switch (or router). This catches everyone the first time.

### IPvlan (Shares MAC Address)

IPvlan is similar to Macvlan but all virtual interfaces share the parent's MAC address. This matters in environments that restrict MAC addresses (some cloud providers, certain switch configurations):

```yaml
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: ipvlan-conf
  namespace: default
spec:
  config: '{
    "cniVersion": "0.3.1",
    "type": "ipvlan",
    "master": "eth0",
    "mode": "l2",
    "ipam": {
      "type": "whereabouts",
      "range": "10.10.1.0/24",
      "range_start": "10.10.1.100",
      "range_end": "10.10.1.200"
    }
  }'
```

**IPvlan modes:**

| Mode | Layer | Description |
|------|-------|-------------|
| `l2` | Layer 2 | Frames switched based on MAC (but all share one MAC) |
| `l3` | Layer 3 | Routing between subnets, no broadcast/multicast |
| `l3s` | Layer 3 + source | Like L3 but with iptables/connection tracking support |

**When to choose IPvlan over Macvlan:**
- Cloud environments that limit MAC addresses per interface (AWS, some OpenStack setups)
- When you need more than ~512 virtual interfaces (Macvlan has MAC table limits)
- When you need L3 mode for routing between subnets

### Bridge (Virtual Bridge on the Node)

The bridge plugin creates a Linux bridge on the node and attaches pod interfaces to it. Pods on the same node connected to the same bridge can communicate at L2:

```yaml
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: bridge-conf
  namespace: default
spec:
  config: '{
    "cniVersion": "0.3.1",
    "type": "bridge",
    "bridge": "mybridge0",
    "isGateway": true,
    "ipMasq": true,
    "ipam": {
      "type": "whereabouts",
      "range": "10.20.0.0/24"
    }
  }'
```

**Bridge use cases:**
- Inter-pod communication on the same node without traversing the overlay
- Connecting pods to node-local resources
- Lab/testing environments where you want a simple secondary network

**Limitation**: Bridge networks are node-local by default. Pods on different nodes cannot communicate over a bridge network unless you configure VXLAN tunneling or similar on top.

### SR-IOV (Hardware-Accelerated Networking)

SR-IOV is the performance tier. It creates Virtual Functions (VFs) on a physical NIC that are passed directly into the pod's network namespace. The pod talks to the hardware without kernel involvement:

```yaml
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: sriov-net
  namespace: default
  annotations:
    k8s.v1.cni.cncf.io/resourceName: intel.com/sriov_netdevice
spec:
  config: '{
    "cniVersion": "0.3.1",
    "type": "sriov",
    "vlan": 1000,
    "ipam": {
      "type": "whereabouts",
      "range": "192.168.100.0/24"
    }
  }'
```

SR-IOV requires additional components:
- **SR-IOV Network Device Plugin**: Discovers and advertises VFs as extended resources
- **SR-IOV CNI Plugin**: Moves VFs into pod network namespaces
- **Compatible NIC**: Intel X710/XXV710, Mellanox ConnectX-4/5/6, Broadcom BCM57xx

```
SR-IOV ARCHITECTURE
═══════════════════════════════════════════════════════════════

Physical NIC (e.g., Intel XXV710 25GbE)
┌─────────────────────────────────────────────────────┐
│                                                       │
│  PF (Physical Function) ── Full NIC control           │
│    │                                                   │
│    ├── VF0 ──▶ Pod A (net2: 192.168.100.10)          │
│    ├── VF1 ──▶ Pod B (net2: 192.168.100.11)          │
│    ├── VF2 ──▶ Pod C (net2: 192.168.100.12)          │
│    ├── VF3 ──▶ (available)                            │
│    └── ...up to 128 VFs per PF                        │
│                                                       │
│  Hardware switching between VFs (no kernel involved)  │
│  Each VF: own MAC, own VLAN, own QoS                 │
└─────────────────────────────────────────────────────┘

Pod A's perspective:
  eth0  ──▶ Calico overlay (management)
  net2  ──▶ SR-IOV VF (25 Gbps, ~5us latency)
```

Pods request SR-IOV VFs through Kubernetes resource limits:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sriov-pod
  annotations:
    k8s.v1.cni.cncf.io/networks: sriov-net
spec:
  containers:
  - name: app
    image: my-nf-image
    resources:
      requests:
        intel.com/sriov_netdevice: '1'
      limits:
        intel.com/sriov_netdevice: '1'
```

---

## Part 4: Whereabouts IPAM

When you have multiple networks, IP address management becomes critical. The default `host-local` IPAM plugin assigns IPs per node, but has no cluster-wide coordination. Two pods on different nodes can get the same IP on a secondary network.

**Whereabouts** solves this by storing IP allocations in Kubernetes Custom Resources, providing cluster-wide coordination:

```
IP ALLOCATION: host-local vs. Whereabouts
═══════════════════════════════════════════════════════════════

host-local (built-in, per-node):
  Node 1: Assigns 172.16.1.10 to Pod A
  Node 2: Assigns 172.16.1.10 to Pod B   ← CONFLICT!
  (Each node tracks its own range independently)

Whereabouts (cluster-wide):
  Node 1: Assigns 172.16.1.10 to Pod A
           Records allocation in K8s CR
  Node 2: Checks K8s CR, sees .10 is taken
           Assigns 172.16.1.11 to Pod B   ← No conflict
```

### Whereabouts Configuration

```yaml
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: macvlan-whereabouts
  namespace: default
spec:
  config: '{
    "cniVersion": "0.3.1",
    "type": "macvlan",
    "master": "eth0",
    "mode": "bridge",
    "ipam": {
      "type": "whereabouts",
      "range": "172.16.1.0/24",
      "range_start": "172.16.1.100",
      "range_end": "172.16.1.200",
      "gateway": "172.16.1.1",
      "exclude": [
        "172.16.1.150/32",
        "172.16.1.160/32"
      ]
    }
  }'
```

Key Whereabouts features:
- **Range-based allocation**: Define start and end of the pool
- **Exclusions**: Reserve specific IPs (for gateways, existing hosts)
- **Overlapping ranges**: Support for overlapping ranges across different NetworkAttachmentDefinitions with different namespaces
- **Garbage collection**: Automatically reclaims IPs from deleted pods via a cron job

### Checking IP Allocations

```bash
# List all IP allocations managed by Whereabouts
k get ippools.whereabouts.cni.cncf.io -A

# See detailed allocation for a specific pool
k get ippools.whereabouts.cni.cncf.io -n whereabouts -o yaml

# Check for leaked IPs (allocated but pod is gone)
k get overlappingrangeipreservations.whereabouts.cni.cncf.io -A
```

> **Did You Know?** Before Whereabouts existed, operators using Multus had to manually partition IP ranges per node (e.g., Node 1 gets .100-.120, Node 2 gets .121-.140). This was error-prone and made scaling painful. Whereabouts was created specifically to eliminate this operational burden. It uses optimistic locking on Kubernetes resources to handle concurrent allocations without a separate database or coordination service.

---

## Part 5: Pod Annotations - Attaching Networks

Pods request additional networks through the `k8s.v1.cni.cncf.io/networks` annotation. The default network (eth0) is always attached automatically.

### Basic Annotation

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-net-pod
  annotations:
    k8s.v1.cni.cncf.io/networks: macvlan-conf
spec:
  containers:
  - name: app
    image: alpine
    command: ["sleep", "infinity"]
```

Result: Pod gets `eth0` (default CNI) + `net1` (Macvlan).

### Multiple Networks

```yaml
annotations:
  k8s.v1.cni.cncf.io/networks: macvlan-conf, bridge-conf, sriov-net
```

Result: Pod gets `eth0` + `net1` (Macvlan) + `net2` (bridge) + `net3` (SR-IOV).

### JSON Annotation (Advanced Control)

For fine-grained control over interface names, IPs, and namespaces:

```yaml
annotations:
  k8s.v1.cni.cncf.io/networks: '[
    {
      "name": "macvlan-conf",
      "namespace": "default",
      "interface": "mgmt1",
      "ips": ["172.16.1.50"]
    },
    {
      "name": "sriov-net",
      "namespace": "default",
      "interface": "data0"
    }
  ]'
```

Result: Pod gets `eth0` + `mgmt1` (Macvlan at 172.16.1.50) + `data0` (SR-IOV).

### Checking Network Status

After the pod starts, Multus writes the result back as an annotation:

```bash
# See what networks were actually attached
k get pod multi-net-pod -o jsonpath='{.metadata.annotations.k8s\.v1\.cni\.cncf\.io/network-status}' | jq .
```

Output:
```json
[
  {
    "name": "cbr0",
    "interface": "eth0",
    "ips": ["10.244.1.5"],
    "mac": "0a:58:0a:f4:01:05",
    "default": true,
    "dns": {}
  },
  {
    "name": "default/macvlan-conf",
    "interface": "net1",
    "ips": ["172.16.1.100"],
    "mac": "02:42:ac:10:01:64",
    "dns": {}
  }
]
```

---

## Part 6: Use Cases Deep Dive

### 5G Core Network Functions

The canonical Multus use case. Every 5G network function (AMF, SMF, UPF) requires multiple interfaces:

```
5G CORE ON KUBERNETES
═══════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────┐
  │                    AMF Pod                             │
  │  (Access and Mobility Management Function)            │
  │                                                        │
  │   eth0 ──▶ Management (Calico)                        │
  │   n2   ──▶ N2 interface to gNB (Macvlan, SCTP)       │
  │   sbi  ──▶ Service Based Interface (Macvlan, HTTP/2) │
  └──────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────┐
  │                    UPF Pod                             │
  │  (User Plane Function) - the data plane workhorse     │
  │                                                        │
  │   eth0 ──▶ Management (Calico)                        │
  │   n3   ──▶ N3 from gNB - user traffic IN (SR-IOV)    │
  │   n6   ──▶ N6 to data network - user traffic OUT      │
  │   n4   ──▶ N4 from SMF - control (Macvlan)           │
  └──────────────────────────────────────────────────────┘

  The UPF is where performance matters most.
  N3 and N6 interfaces use SR-IOV + DPDK for line-rate
  packet forwarding (25-100 Gbps per pod).
```

### Financial Trading Systems

Low-latency trading systems use dedicated networks for market data to eliminate jitter:

```
TRADING SYSTEM ARCHITECTURE
═══════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────┐
  │           Trading Engine Pod                   │
  │                                                │
  │   eth0   ──▶ Corporate network (Calico)       │
  │              Monitoring, logging, deployment   │
  │                                                │
  │   mktdata ──▶ Market data feed (SR-IOV)       │
  │              Multicast from exchange           │
  │              Latency: < 5 microseconds         │
  │                                                │
  │   order   ──▶ Order entry (Macvlan on VLAN)   │
  │              Dedicated link to exchange         │
  │              Encrypted, audited, isolated       │
  └──────────────────────────────────────────────┘
```

### HPC with InfiniBand/RDMA

High-performance computing jobs use RDMA (Remote Direct Memory Access) for inter-node communication:

```yaml
# NetworkAttachmentDefinition for InfiniBand SR-IOV
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: ib-sriov
  annotations:
    k8s.v1.cni.cncf.io/resourceName: mellanox.com/mlnx_sriov_rdma
spec:
  config: '{
    "cniVersion": "0.3.1",
    "type": "sriov",
    "ipam": {
      "type": "whereabouts",
      "range": "10.56.0.0/16"
    }
  }'
```

### Storage Networks

Dedicated network for storage traffic prevents application I/O from competing with storage I/O:

```yaml
# Dedicated storage network for iSCSI/NFS traffic
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: storage-net
spec:
  config: '{
    "cniVersion": "0.3.1",
    "type": "ipvlan",
    "master": "eth1",
    "mode": "l2",
    "ipam": {
      "type": "whereabouts",
      "range": "10.10.0.0/16",
      "range_start": "10.10.1.1",
      "range_end": "10.10.1.254"
    }
  }'
```

---

## Part 7: Limitations and Challenges

Multus solves real problems, but it brings real complexity. Be honest about the trade-offs before adopting it.

### No Built-in DNS for Secondary Networks

Kubernetes DNS (CoreDNS) only knows about Services, which use the default network. If Pod A wants to reach Pod B on the secondary Macvlan network, there is no DNS name for it. You must:

- Use static IPs (with Whereabouts reservations)
- Build your own service discovery for secondary networks
- Use a sidecar that registers secondary IPs with an external DNS

### Debugging is Harder

With one network per pod, `kubectl exec -- ip addr` shows you everything. With three networks, you need to understand which interface carries which traffic, check routes in the pod, and trace issues across multiple network paths:

```bash
# Inside a multi-network pod
ip addr show          # See all interfaces
ip route show         # Check routing table -- which traffic goes where?
ip route get 172.16.1.1   # Which interface reaches this destination?
```

### Kubernetes Services Do Not Work on Secondary Networks

This is the biggest gotcha. Kubernetes Services (ClusterIP, NodePort, LoadBalancer) only operate on the default (eth0) network. If you expose a Service, it routes through the primary CNI. Secondary network traffic must be handled at the application layer or with external load balancers.

### Network Policies Are Limited

Standard Kubernetes NetworkPolicy and most CNI-specific policies (CiliumNetworkPolicy, Calico policies) only apply to the default network interface. Securing secondary networks requires:

- Network-level controls (switch ACLs, VLAN isolation)
- Application-level security
- iptables rules inside the pod or on the node

---

## Common Mistakes

| Mistake | What Happens | Solution |
|---------|-------------|----------|
| Forgetting that Services only work on the default network | Try to expose secondary network via Service, traffic never arrives | Use application-level load balancing or external LB for secondary networks |
| Using `host-local` IPAM across multiple nodes | IP conflicts on secondary networks; two pods get the same IP | Use `whereabouts` for cluster-wide IP coordination |
| Not setting the `master` interface correctly in Macvlan/IPvlan | Pod creation fails with `"master" field is required` or attaches to wrong NIC | Verify interface names with `ip link show` on each node; names vary between distros |
| Expecting the host to reach Macvlan interfaces | Host cannot ping pods on Macvlan sub-interfaces | This is by design in Macvlan; use a bridge network or route through external switch |
| Putting NetworkAttachmentDefinition in wrong namespace | Pod cannot find the net-attach-def; fails with `cannot find network` | Create net-attach-def in the same namespace as the pod, or use the JSON annotation with explicit namespace |
| Not requesting SR-IOV resources in pod spec | Pod scheduled but SR-IOV interface not attached; VF not allocated | Add `resources.requests` and `resources.limits` for the SR-IOV resource name |
| Ignoring routing inside multi-interface pods | Traffic leaves via the wrong interface; response packets take a different path (asymmetric routing) | Configure policy-based routing in the pod or use `default-route` annotation to control default gateway per network |
| Deploying Multus without understanding the default network dependency | Deleting or misconfiguring the default CNI breaks all pods, not just multi-network ones | Multus always calls the default delegate first; keep your primary CNI healthy |

---

## Quiz

Test your understanding of Multus and multi-network pods.

**Question 1**: What is Multus in terms of CNI architecture?

<details>
<summary>Show Answer</summary>

Multus is a **meta-plugin** (or meta-CNI). It is the CNI plugin that kubelet calls, but instead of configuring networks itself, it delegates to other CNI plugins. It calls the default plugin first (creating eth0), then calls additional plugins for each secondary network requested by pod annotations. It acts as a dispatcher that chains multiple CNI plugins together for a single pod.
</details>

**Question 2**: A pod has the annotation `k8s.v1.cni.cncf.io/networks: macvlan-conf, bridge-conf`. How many network interfaces will the pod have, and what are their names?

<details>
<summary>Show Answer</summary>

The pod will have **three** interfaces:
1. `eth0` -- the default network (always present, from the cluster's primary CNI)
2. `net1` -- the Macvlan interface (from macvlan-conf)
3. `net2` -- the bridge interface (from bridge-conf)

Additional networks are numbered sequentially as `net1`, `net2`, `net3`, etc., unless custom interface names are specified using the JSON annotation format.
</details>

**Question 3**: Why can the host (node) not communicate directly with a pod's Macvlan interface?

<details>
<summary>Show Answer</summary>

This is a fundamental property of Macvlan. The Linux kernel blocks traffic between a Macvlan parent interface and its child (sub) interfaces. Traffic between the host's physical interface and a Macvlan sub-interface on the same parent must go through an external switch -- out the physical port and back in. This is not a bug; it is how Macvlan isolates virtual interfaces at the kernel level. If host-to-pod communication on the secondary network is required, use a bridge network instead, or configure an additional Macvlan interface on the host in the same network namespace workaround.
</details>

**Question 4**: What problem does Whereabouts solve that the built-in `host-local` IPAM cannot?

<details>
<summary>Show Answer</summary>

**Cluster-wide IP coordination**. The `host-local` IPAM plugin manages IP allocations independently per node. If two nodes both have the range `172.16.1.0/24`, they can assign the same IP to different pods, causing conflicts. Whereabouts stores IP allocations as Kubernetes Custom Resources, so all nodes share the same allocation state. Before assigning an IP, a node checks the cluster-wide pool to avoid duplicates.
</details>

**Question 5**: You create a Kubernetes Service that selects pods running a 5G UPF (User Plane Function). The UPF processes user data traffic on its SR-IOV interface (net2). Will the Service route traffic to the SR-IOV interface?

<details>
<summary>Show Answer</summary>

**No.** Kubernetes Services only operate on the default pod network (eth0). The Service will route traffic to the pod's primary IP address assigned by the cluster CNI (e.g., Calico). It has no awareness of secondary interfaces like the SR-IOV `net2`. For data plane traffic on secondary networks, you must handle load balancing and routing outside of Kubernetes Services -- using external load balancers, application-level routing, or dedicated control plane software (e.g., a 5G SMF directing traffic to specific UPF data plane IPs).
</details>

**Question 6**: When would you choose IPvlan over Macvlan for a secondary network?

<details>
<summary>Show Answer</summary>

Choose IPvlan over Macvlan when:
1. **Cloud environments** that limit the number of MAC addresses per interface (e.g., AWS ENIs have MAC limits). IPvlan shares the parent's MAC address.
2. **Scale**: When you need more than ~512 virtual interfaces on one parent. Macvlan creates a unique MAC per interface, which can overflow switch MAC tables.
3. **L3 routing mode**: When you want routing between subnets without broadcast/multicast traffic, IPvlan's L3 mode provides this.
4. **Switch port security**: When network switches are configured to allow only one MAC per port, Macvlan (which creates new MACs) would be blocked.
</details>

---

## Hands-On Exercise: Multus with Macvlan on kind

### What You'll Build

A kind cluster with Multus installed, where pods get both a primary network (kindnet/default CNI) and a secondary Macvlan network. You will verify that pods can communicate on both networks independently.

### Part 1: Create kind Cluster

```bash
# Create a kind cluster
cat <<'EOF' | kind create cluster --name multus-lab --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOF

# Verify the cluster is running
k get nodes
```

### Part 2: Install Multus

```bash
# Install Multus using the official thick plugin DaemonSet
# (thick mode works best in kind since we have direct access to the nodes)
k apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/master/deployments/multus-daemonset-thick.yml

# Wait for Multus pods to be ready
k rollout status daemonset/kube-multus-ds -n kube-system --timeout=120s

# Verify Multus is running
k get pods -n kube-system -l app=multus
```

### Part 3: Create a NetworkAttachmentDefinition

```bash
# Find the interface name inside kind nodes
# (kind nodes use 'eth0' as their primary interface)
docker exec multus-lab-worker ip link show

# Create a Macvlan NetworkAttachmentDefinition
k apply -f - <<'EOF'
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: macvlan-conf
  namespace: default
spec:
  config: '{
    "cniVersion": "0.3.1",
    "type": "macvlan",
    "master": "eth0",
    "mode": "bridge",
    "ipam": {
      "type": "host-local",
      "subnet": "172.16.1.0/24",
      "rangeStart": "172.16.1.100",
      "rangeEnd": "172.16.1.200"
    }
  }'
EOF

# Verify the NetworkAttachmentDefinition was created
k get net-attach-def
```

> **Note**: We use `host-local` IPAM here because Whereabouts requires a separate installation. In production, you would install Whereabouts and use it instead to avoid IP conflicts across nodes.

### Part 4: Deploy Pods with Multiple Networks

```bash
# Create Pod A on the secondary network
k apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: pod-a
  annotations:
    k8s.v1.cni.cncf.io/networks: macvlan-conf
spec:
  containers:
  - name: toolbox
    image: nicolaka/netshoot
    command: ["sleep", "infinity"]
EOF

# Create Pod B on the secondary network
k apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: pod-b
  annotations:
    k8s.v1.cni.cncf.io/networks: macvlan-conf
spec:
  containers:
  - name: toolbox
    image: nicolaka/netshoot
    command: ["sleep", "infinity"]
EOF

# Create Pod C WITHOUT the secondary network (control group)
k apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: pod-c
spec:
  containers:
  - name: toolbox
    image: nicolaka/netshoot
    command: ["sleep", "infinity"]
EOF

# Wait for all pods to be running
k wait --for=condition=Ready pod/pod-a pod/pod-b pod/pod-c --timeout=120s
```

### Part 5: Verify Multi-Network Connectivity

```bash
# Check interfaces in Pod A (should have eth0 AND net1)
echo "=== Pod A interfaces ==="
k exec pod-a -- ip addr show

# Check interfaces in Pod B (should have eth0 AND net1)
echo "=== Pod B interfaces ==="
k exec pod-b -- ip addr show

# Check interfaces in Pod C (should have ONLY eth0)
echo "=== Pod C interfaces (no secondary network) ==="
k exec pod-c -- ip addr show

# Check network status annotation on Pod A
echo "=== Pod A network status ==="
k get pod pod-a -o jsonpath='{.metadata.annotations.k8s\.v1\.cni\.cncf\.io/network-status}' | python3 -m json.tool
```

```bash
# Get the secondary IP of Pod B
POD_B_SECONDARY_IP=$(k exec pod-b -- ip -4 addr show net1 | grep inet | awk '{print $2}' | cut -d/ -f1)
echo "Pod B secondary IP: $POD_B_SECONDARY_IP"

# Ping Pod B from Pod A on the SECONDARY network (net1 → net1)
echo "=== Ping on secondary network (Macvlan) ==="
k exec pod-a -- ping -c 3 -I net1 "$POD_B_SECONDARY_IP"

# Get the primary IP of Pod B
POD_B_PRIMARY_IP=$(k get pod pod-b -o jsonpath='{.status.podIP}')
echo "Pod B primary IP: $POD_B_PRIMARY_IP"

# Ping Pod B from Pod A on the PRIMARY network (eth0 → eth0)
echo "=== Ping on primary network (default CNI) ==="
k exec pod-a -- ping -c 3 "$POD_B_PRIMARY_IP"
```

### Part 6: Verify Isolation

```bash
# Pod C does NOT have a secondary network.
# It cannot reach Pod A's Macvlan IP directly.
POD_A_SECONDARY_IP=$(k exec pod-a -- ip -4 addr show net1 | grep inet | awk '{print $2}' | cut -d/ -f1)
echo "Pod A secondary IP: $POD_A_SECONDARY_IP"

echo "=== Pod C trying to reach Pod A on secondary network ==="
k exec pod-c -- ping -c 3 -W 2 "$POD_A_SECONDARY_IP" || echo "EXPECTED: Pod C cannot reach secondary network"

# But Pod C CAN reach Pod A on the primary network
POD_A_PRIMARY_IP=$(k get pod pod-a -o jsonpath='{.status.podIP}')
echo "=== Pod C reaching Pod A on primary network ==="
k exec pod-c -- ping -c 3 "$POD_A_PRIMARY_IP"
```

### Part 7: Inspect Routing Inside Multi-Network Pod

```bash
# See the routing table inside Pod A
echo "=== Pod A routing table ==="
k exec pod-a -- ip route show

# Notice: default route goes via eth0 (primary network)
# Secondary network has a direct route for its subnet only
# This means: internet traffic → eth0, 172.16.1.0/24 traffic → net1
```

### Success Criteria

- [ ] Multus DaemonSet is running on all nodes
- [ ] NetworkAttachmentDefinition `macvlan-conf` is created
- [ ] Pod A and Pod B each have two interfaces (`eth0` and `net1`)
- [ ] Pod C has only one interface (`eth0`)
- [ ] Pod A can ping Pod B on the secondary network (Macvlan)
- [ ] Pod A can ping Pod B on the primary network (default CNI)
- [ ] Pod C cannot reach pods on the secondary Macvlan network
- [ ] Network status annotation shows both networks on Pod A

### Bonus Challenge

Create a second NetworkAttachmentDefinition using the `bridge` type on a different subnet. Attach both `macvlan-conf` and the new bridge network to a pod so it has three interfaces total (`eth0`, `net1`, `net2`). Verify all three are present and have IPs from the correct subnets.

---

## Cleanup

```bash
# Delete the lab cluster
kind delete cluster --name multus-lab
```

---

## Further Reading

- [Multus CNI GitHub](https://github.com/k8snetworkplumbingwg/multus-cni) - Source code, docs, and examples
- [Network Plumbing Working Group](https://github.com/k8snetworkplumbingwg) - The NPWG maintains Multus and related projects
- [Whereabouts IPAM](https://github.com/k8snetworkplumbingwg/whereabouts) - Cluster-wide IPAM for secondary networks
- [SR-IOV Network Device Plugin](https://github.com/k8snetworkplumbingwg/sriov-network-device-plugin) - VF discovery and management
- [Kubernetes Network Custom Resource Definition De-facto Standard (v1)](https://docs.google.com/document/d/1Ny03h6IDVy_e_vmElOqR7UdTPAG_RNydhVE1Kx54kFQ) - The spec behind NetworkAttachmentDefinition

---

## Next Module

Continue to [Module 5.2: Service Mesh](../module-5.2-service-mesh/) to learn about traffic management, mTLS, and when service mesh patterns complement multi-network architectures.

---

*"The pod that needs three networks is the pod doing the real work. Multus makes sure Kubernetes can handle it."*
