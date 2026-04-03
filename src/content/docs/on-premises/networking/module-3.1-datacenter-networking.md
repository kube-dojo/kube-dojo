---
title: "Module 3.1: Datacenter Network Architecture"
slug: on-premises/networking/module-3.1-datacenter-networking
sidebar:
  order: 2
---

> **Complexity**: `[COMPLEX]` | Time: 60 minutes
>
> **Prerequisites**: [Module 2.1: Datacenter Fundamentals](../provisioning/module-2.1-datacenter-fundamentals/), [Linux: TCP/IP Essentials](../../linux/foundations/networking/module-3.1-tcp-ip-essentials/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Design** leaf-spine network topologies with appropriate oversubscription ratios for Kubernetes east-west traffic patterns
2. **Evaluate** switch selection, uplink bandwidth, and ECMP configuration for bare-metal cluster networking
3. **Configure** VLANs, jumbo frames, and network segmentation to isolate management, storage, and pod traffic
4. **Diagnose** network bottlenecks caused by oversubscription, MTU mismatches, and switch fabric limitations

---

## Why This Module Matters

In March 2022, a media streaming company deployed a 60-node Kubernetes cluster on bare metal in their colocation facility. They connected all servers to a single pair of 48-port top-of-rack switches. For the first three months, everything worked. Then they deployed a real-time video transcoding pipeline that generated 8 Gbps of east-west traffic between pods. The ToR switches — rated for 48x 10GbE ports with a 480 Gbps switching fabric — became the bottleneck. The uplinks to the core switches were only 2x 40GbE, creating a 6:1 oversubscription ratio. During peak transcoding, packet drops hit 3%, causing TCP retransmissions that increased video processing latency from 200ms to 4 seconds. Viewers saw buffering. Revenue dropped $12,000/hour during prime time.

The fix required adding spine switches, upgrading to 25GbE server connections, and implementing a proper leaf-spine topology with ECMP (Equal-Cost Multi-Path) routing. The migration took 3 weeks of weekend maintenance windows. Total cost: $85,000 in new switches plus $40,000 in engineering time. The CTO's postmortem note: "We designed our network for the workload we had, not the workload we would have in 6 months."

In the cloud, you never think about switch oversubscription or uplink bandwidth. AWS and GCP handle it. On-premises, the network is yours to design, and mistakes are expensive to fix because they require physical hardware changes.

> **The Highway Analogy**
>
> A datacenter network is like a highway system. The ToR switches are local roads (one per rack). The spine switches are highways connecting all the local roads. If your local roads are 2-lane but your highway is 8-lane, traffic flows. But if your highway is only 2-lane while every local road feeds 10 lanes of traffic, you get gridlock at the on-ramps. Oversubscription ratio is the ratio of total local road capacity to highway capacity.

---

## What You'll Learn

- Spine-leaf vs traditional 3-tier topology
- Oversubscription ratios and bandwidth planning
- VLAN design for Kubernetes (management, production, storage, PXE)
- MTU configuration (jumbo frames for overlay networks)
- L2 vs L3 boundaries and when to route
- How to connect Kubernetes CNI to datacenter fabric

---

## Spine-Leaf Topology

### Why Not Traditional 3-Tier?

The traditional datacenter network (access → aggregation → core) was designed for north-south traffic (client → server). Kubernetes generates massive east-west traffic (pod → pod, pod → service, pod → storage). The aggregation layer becomes a bottleneck.

```
┌─────────────────────────────────────────────────────────────┐
│          TRADITIONAL 3-TIER (avoid for K8s)                  │
│                                                               │
│                    ┌──────────┐                              │
│                    │   Core   │ ← single bottleneck          │
│                    └────┬─────┘                              │
│               ┌─────────┼─────────┐                         │
│          ┌────▼────┐         ┌────▼────┐                    │
│          │  Aggr 1 │         │  Aggr 2 │ ← oversubscribed   │
│          └────┬────┘         └────┬────┘                    │
│        ┌──────┼──────┐     ┌──────┼──────┐                  │
│     ┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐              │
│     │ToR 1│ │ToR 2│ │ToR 3│ │ToR 4│ │ToR 5│              │
│     └─────┘ └─────┘ └─────┘ └─────┘ └─────┘              │
│                                                               │
│  Problem: East-west traffic between ToR 1 and ToR 5        │
│  must traverse aggregation + core = high latency + overload │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│          SPINE-LEAF (recommended for K8s)                    │
│                                                               │
│     ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐                │
│     │Spine │  │Spine │  │Spine │  │Spine │                │
│     │  1   │  │  2   │  │  3   │  │  4   │                │
│     └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘                │
│        │ ╲       │ ╲       │ ╲       │ ╲                    │
│        │  ╲      │  ╲      │  ╲      │  ╲                   │
│     ┌──▼──┐╲  ┌──▼──┐╲  ┌──▼──┐╲  ┌──▼──┐                │
│     │Leaf │ ╲ │Leaf │ ╲ │Leaf │ ╲ │Leaf │                │
│     │  1  │  ╲│  2  │  ╲│  3  │  ╲│  4  │                │
│     │(ToR)│   │(ToR)│   │(ToR)│   │(ToR)│                │
│     └─────┘   └─────┘   └─────┘   └─────┘                │
│                                                               │
│  Every leaf connects to EVERY spine (full mesh)             │
│  Any-to-any traffic: max 2 hops (leaf → spine → leaf)      │
│  Equal-cost paths: ECMP load-balances across spines         │
│  Add capacity: add more spines (horizontal scaling)         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

> **Pause and predict**: Looking at the spine-leaf diagram above, count the number of hops a packet takes from a server in rack 1 to a server in rack 4. Now count the hops in the traditional 3-tier topology. Why does this difference matter for Kubernetes east-west traffic?

### Spine-Leaf Sizing

| Component | Speed | Ports | Use Case |
|-----------|-------|-------|----------|
| **Leaf (ToR)** | 25GbE down, 100GbE up | 48x 25G + 6x 100G | Per-rack switch |
| **Spine** | 100GbE | 32x 100G | Interconnect fabric |
| **Border leaf** | 100GbE down, 400GbE up | 48x 100G + 8x 400G | WAN/internet uplinks |

**Oversubscription calculation:**

```
Leaf: 48 x 25GbE = 1,200 Gbps downlink
      6 x 100GbE = 600 Gbps uplink

Oversubscription ratio = 1,200 / 600 = 2:1

For Kubernetes east-west heavy workloads:
  Target: 2:1 or better (3:1 acceptable for light workloads)
  Avoid: 5:1+ (will cause drops under load)
```

---

## VLAN Design for Kubernetes

### Recommended VLANs

```
┌─────────────────────────────────────────────────────────────┐
│              VLAN ARCHITECTURE                               │
│                                                               │
│  VLAN 10: Management                                        │
│  ├── BMC/IPMI interfaces (out-of-band)                     │
│  ├── Jump hosts, monitoring                                 │
│  └── Subnet: 10.0.10.0/24                                  │
│                                                               │
│  VLAN 20: Kubernetes Node Network                           │
│  ├── kubelet, API server, etcd communication                │
│  ├── Pod-to-pod traffic (if using host networking CNI)      │
│  └── Subnet: 10.0.20.0/22 (1,022 hosts)                   │
│                                                               │
│  VLAN 30: Storage Network                                   │
│  ├── Ceph public + cluster networks                         │
│  ├── NFS, iSCSI traffic                                     │
│  └── Subnet: 10.0.30.0/24                                  │
│  └── MTU: 9000 (jumbo frames for storage performance)      │
│                                                               │
│  VLAN 40: PXE / Provisioning                                │
│  ├── DHCP for PXE boot                                      │
│  ├── TFTP/HTTP for OS images                                │
│  └── Subnet: 10.0.40.0/24                                  │
│  └── Isolated: only accessible from provisioning server     │
│                                                               │
│  VLAN 50: External / Ingress                                │
│  ├── Load balancer VIPs (MetalLB)                           │
│  ├── External-facing services                               │
│  └── Subnet: 10.0.50.0/24                                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

> **Stop and think**: You are designing VLANs for a new cluster. A colleague suggests putting storage traffic (Ceph replication) and Kubernetes pod traffic on the same VLAN to simplify the network. What problems would this cause during a Ceph rebalancing event, and how would it affect application latency?

### Server NIC Assignment

```
┌─────────────────────────────────────────────────────────────┐
│              SERVER NIC CONFIGURATION                        │
│                                                               │
│  NIC 0 (25GbE) ─── Bond (LACP) ─── Trunk port             │
│  NIC 1 (25GbE) ─── Bond (LACP) ─── (carries VLAN 20,30,50)│
│                                                               │
│  NIC 2 (1GbE)  ─── Management ──── Access port (VLAN 10)   │
│                                                               │
│  BMC NIC (1GbE) ── IPMI ────────── Access port (VLAN 10)   │
│                                                               │
│  Bond configuration (LACP/802.3ad):                         │
│  ├── Active-active (doubles bandwidth: 50 Gbps)            │
│  ├── Failover if one NIC or cable fails                    │
│  └── Switch must support LACP (most enterprise switches do)│
│                                                               │
│  Linux bond setup:                                           │
│  # /etc/netplan/01-bond.yaml (Ubuntu)                       │
│  network:                                                    │
│    version: 2                                                │
│    bonds:                                                    │
│      bond0:                                                  │
│        interfaces: [eno1, eno2]                             │
│        parameters:                                           │
│          mode: 802.3ad                                       │
│          lacp-rate: fast                                     │
│          transmit-hash-policy: layer3+4                      │
│    vlans:                                                    │
│      vlan20:                                                 │
│        id: 20                                                │
│        link: bond0                                           │
│        addresses: [10.0.20.10/22]                           │
│      vlan30:                                                 │
│        id: 30                                                │
│        link: bond0                                           │
│        addresses: [10.0.30.10/24]                           │
│        mtu: 9000                                             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## MTU Configuration

### Why Jumbo Frames Matter

Default Ethernet MTU is 1500 bytes. Kubernetes overlay networks (VXLAN, Geneve) add headers:

```
┌─────────────────────────────────────────────────────────────┐
│              MTU AND OVERLAY OVERHEAD                        │
│                                                               │
│  Standard MTU (1500 bytes):                                 │
│  ┌──────┬──────────────────────────────┐                    │
│  │ VXLAN│ Inner Ethernet │ IP │ TCP │ Payload              │
│  │  50B │     14B        │20B │20B  │ 1396B                │
│  └──────┴──────────────────────────────┘                    │
│  Overhead: 104 bytes (7% of each packet wasted)             │
│                                                               │
│  Jumbo MTU (9000 bytes):                                    │
│  ┌──────┬──────────────────────────────────────────────┐    │
│  │ VXLAN│ Inner Ethernet │ IP │ TCP │  Payload (8896B)  │   │
│  │  50B │     14B        │20B │20B  │                    │   │
│  └──────┴──────────────────────────────────────────────┘    │
│  Overhead: 104 bytes (1.2% of each packet wasted)           │
│                                                               │
│  With jumbo frames:                                          │
│  ✓ 6x less header overhead per byte of data                │
│  ✓ Fewer packets per data transfer (less CPU interrupt load)│
│  ✓ Critical for storage traffic (Ceph, NFS)                │
│                                                               │
│  IMPORTANT: ALL devices in the path must support jumbo:     │
│  Server NICs, bonds, VLANs, switches, routers               │
│  One device with MTU 1500 = fragmentation = performance drop│
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### MTU Settings by Network

| Network | MTU | Reason |
|---------|-----|--------|
| Management (VLAN 10) | 1500 | Low traffic, no overlay |
| K8s Node (VLAN 20) | 9000 or 1500 | 9000 if CNI uses VXLAN overlay; 1500 if native routing |
| Storage (VLAN 30) | 9000 | Always jumbo for storage performance |
| PXE (VLAN 40) | 1500 | PXE/TFTP doesn't benefit from jumbo |
| External (VLAN 50) | 1500 | Internet-facing, standard MTU |

```bash
# Verify MTU on a path
ping -M do -s 8972 10.0.30.1
# -M do: don't fragment
# -s 8972: 8972 + 28 (IP+ICMP header) = 9000
# If this works, the path supports MTU 9000
# If "Message too long", something in the path has a smaller MTU

# Check interface MTU
ip link show bond0
# ... mtu 9000 ...

# Set MTU on Linux
ip link set bond0 mtu 9000
# Or permanently in netplan/interfaces config
```

---

## L2 vs L3: Where to Route

### L2 Domain Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│           L2 vs L3 DESIGN                                    │
│                                                               │
│  SMALL CLUSTER (< 3 racks):                                │
│  ┌──────────────────────────────────────┐                   │
│  │          L2 Domain (one VLAN)        │                   │
│  │  ┌────┐  ┌────┐  ┌────┐             │                   │
│  │  │Rack│  │Rack│  │Rack│             │                   │
│  │  │ A  │  │ B  │  │ C  │             │                   │
│  │  └────┘  └────┘  └────┘             │                   │
│  │  All nodes in same broadcast domain  │                   │
│  │  Simple: ARP works, no routing needed│                   │
│  └──────────────────────────────────────┘                   │
│                                                               │
│  LARGE CLUSTER (> 5 racks):                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ L2: Rack │  │ L2: Rack │  │ L2: Rack │                  │
│  │ A (VLAN  │  │ B (VLAN  │  │ C (VLAN  │                  │
│  │ 20a)     │  │ 20b)     │  │ 20c)     │                  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
│       │              │              │                        │
│       └──────── L3 Routing ─────────┘                       │
│              (BGP between leaves)                            │
│                                                               │
│  Each rack gets its own /24 or /25 subnet                   │
│  L3 routing between racks (no broadcast flooding)           │
│  BGP advertises routes between leaf switches                │
│  Scales to thousands of nodes                                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Rule of thumb:**
- < 200 nodes, < 3 racks: L2 (single broadcast domain) is fine
- \> 200 nodes or > 5 racks: L3 routing between racks with BGP

---

## CNI Integration with Datacenter Fabric

> **Pause and predict**: Your cluster uses VXLAN overlay networking (the default for most CNIs). Each packet adds 50 bytes of overhead. At 1 million packets per second (common for microservices), how much bandwidth is wasted on headers alone? Would switching to BGP native routing eliminate this overhead?

### Calico BGP Mode (No Overlay)

The diagram below shows Calico peering directly with the datacenter ToR switches via BGP. This eliminates the VXLAN encapsulation layer entirely -- pod IPs become first-class citizens in the datacenter routing table, meaning external systems can reach pods without NAT or proxy:

```
┌─────────────────────────────────────────────────────────────┐
│           CALICO BGP WITH DATACENTER FABRIC                  │
│                                                               │
│  Spine Switches                                              │
│  ┌──────┐  ┌──────┐                                        │
│  │Spine1│  │Spine2│  ← Route reflectors (optional)         │
│  └──┬───┘  └──┬───┘                                        │
│     │╲        │╲                                             │
│  ┌──▼──┐   ┌──▼──┐                                         │
│  │Leaf1│   │Leaf2│  ← BGP peers with Calico                │
│  └──┬──┘   └──┬──┘                                         │
│     │         │                                              │
│  ┌──▼──────┐ ┌──▼──────┐                                    │
│  │ Node 1  │ │ Node 2  │                                    │
│  │         │ │         │                                    │
│  │ Calico  │ │ Calico  │  ← Calico peers with leaf switch  │
│  │ BGP     │ │ BGP     │                                    │
│  │         │ │         │                                    │
│  │ Pod     │ │ Pod     │  ← Pod IPs advertised via BGP     │
│  │10.244.  │ │10.244.  │    to datacenter fabric            │
│  │  1.0/24 │ │  2.0/24 │                                    │
│  └─────────┘ └─────────┘                                    │
│                                                               │
│  Result: Pod IPs are routable on the datacenter network     │
│  No overlay (VXLAN/Geneve) needed = no encapsulation overhead│
│  External services can reach pods directly                  │
│  Leaf switches have routes to pod CIDRs                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

```yaml
# Calico BGPConfiguration
apiVersion: projectcalico.org/v3
kind: BGPConfiguration
metadata:
  name: default
spec:
  asNumber: 64512
  nodeToNodeMeshEnabled: false  # Disable full mesh, use route reflectors
  serviceClusterIPs:
    - cidr: 10.96.0.0/12

---
# Peer with ToR switch
apiVersion: projectcalico.org/v3
kind: BGPPeer
metadata:
  name: rack-a-tor
spec:
  peerIP: 10.0.20.1  # ToR switch IP
  asNumber: 64501      # ToR AS number
  nodeSelector: "rack == 'rack-a'"
```

### Cilium Native Routing

```yaml
# Cilium with native routing (no overlay)
apiVersion: cilium.io/v2alpha1
kind: CiliumBGPPeeringPolicy
metadata:
  name: rack-a-peering
spec:
  nodeSelector:
    matchLabels:
      rack: rack-a
  virtualRouters:
    - localASN: 64512
      exportPodCIDR: true
      neighbors:
        - peerAddress: "10.0.20.1/32"
          peerASN: 64501
```

---

## Did You Know?

- **Meta's datacenter fabric uses a 4-plane spine-leaf topology** (F4 architecture) with custom switches running FBOSS (Facebook Open Switching System). Each fabric plane has independent failure domains, so a spine switch failure only affects 1/4th of inter-rack bandwidth. Newer designs scale to 16-plane (F16) for even larger fabrics.

- **The term "Top of Rack" is becoming misleading** as many modern deployments use "End of Row" (EoR) or "Middle of Row" (MoR) switch placements. But "ToR" persists in the industry vocabulary regardless of physical placement.

- **Jumbo frames (9000 MTU) were standardized in 1998** but still are not universally supported. Many enterprise firewalls, VPN concentrators, and WAN links silently fragment jumbo frames, causing performance degradation. Always test the full path.

- **BGP was designed for internet routing between ISPs** but has been adopted for datacenter use because of its simplicity, stability, and scalability. Modern datacenter BGP uses unnumbered interfaces and EVPN-VXLAN for multi-tenancy — a far cry from its 1989 origins.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Single ToR switch (no redundancy) | Switch failure = rack offline | Dual ToR with MLAG or MC-LAG |
| MTU mismatch in path | Silent fragmentation, TCP retransmissions | Verify MTU end-to-end with `ping -M do -s 8972` |
| Flat L2 network at scale | Broadcast storms, ARP floods | Route between racks at L3 with BGP |
| Oversubscribed uplinks | Packet drops under east-west load | Target 2:1 or better oversubscription |
| No separate storage VLAN | Storage traffic competes with pod traffic | Dedicated VLAN with jumbo frames for Ceph/NFS |
| CNI overlay when unnecessary | Extra encapsulation overhead | Use Calico/Cilium BGP mode on bare metal |
| Not monitoring switch ports | Don't know about drops until users complain | SNMP/gNMI monitoring on all switch ports |
| PXE on production VLAN | Risk of accidental OS reimaging | Isolated PXE VLAN with restricted DHCP |

---

## Quiz

### Question 1
Your leaf switch has 48x 25GbE downlink ports and 4x 100GbE uplink ports. What is the oversubscription ratio, and is it acceptable for Kubernetes?

<details>
<summary>Answer</summary>

**Oversubscription ratio: 3:1.**

Calculation:
- Total downlink: 48 x 25 Gbps = 1,200 Gbps
- Total uplink: 4 x 100 Gbps = 400 Gbps
- Ratio: 1,200 / 400 = 3:1

**Is it acceptable?** For most Kubernetes workloads, 3:1 is acceptable. Standard microservices with moderate east-west traffic will not saturate the uplinks.

However, for:
- **Storage-heavy workloads** (Ceph, distributed databases): 3:1 may cause congestion during rebalancing. Target 2:1.
- **ML/AI training** (GPU clusters with all-reduce): Very high east-west. Target 1:1 (non-blocking).
- **Video transcoding**: High sustained bandwidth. Target 2:1.

To improve: add 2 more 100GbE uplinks (6x 100G = 600 Gbps, ratio becomes 2:1).
</details>

### Question 2
Why should you use native routing (BGP) instead of VXLAN overlay for Kubernetes on bare metal?

<details>
<summary>Answer</summary>

**Native routing advantages on bare metal:**

1. **No encapsulation overhead**: VXLAN adds 50 bytes per packet. On a 1500 MTU network, that is 3.3% overhead. With millions of packets per second, this adds up to measurable CPU load and bandwidth waste.

2. **Pod IPs are routable**: External systems (load balancers, monitoring, databases) can reach pods directly without NAT or proxy. This simplifies debugging and architecture.

3. **Existing datacenter fabric integration**: Your ToR switches already run BGP. Calico/Cilium can peer directly with them, making pod CIDRs part of the datacenter routing table.

4. **Better performance**: No encap/decap CPU cost. Packet headers are standard IP — hardware offloading works (TSO, GRO, checksum offload).

5. **Simpler debugging**: `tcpdump` shows real source/destination IPs, not VXLAN-wrapped packets.

**When VXLAN is still needed**: Multi-tenant environments where tenants need overlapping IP ranges, or when the datacenter network team will not allow BGP peering with Kubernetes nodes.
</details>

### Question 3
You are designing the network for a 200-node Kubernetes cluster across 8 racks. Should you use L2 or L3 between racks?

<details>
<summary>Answer</summary>

**L3 (routed) between racks.**

At 200 nodes across 8 racks:
- An L2 domain spanning 8 racks means ~200 nodes in one broadcast domain
- ARP traffic scales with N^2 — 200 nodes = 40,000 potential ARP entries
- Broadcast storms can propagate across all 8 racks
- A spanning-tree reconvergence (if using STP) can cause seconds of network outage

**L3 design:**
- Each rack gets its own /25 subnet (126 hosts per rack)
- Leaf switches route between subnets via BGP
- No broadcast domain spans more than one rack
- Adding more racks = adding more L3 routes, not expanding L2 domain
- Calico/Cilium BGP peers with the leaf switches

**L2 is fine for**: < 3 racks, < 100 nodes (small enough that broadcast is manageable).
</details>

### Question 4
A server's bonded interface shows 50 Gbps capacity (2x 25GbE LACP), but `iperf3` between two servers shows only 24 Gbps. Why?

<details>
<summary>Answer</summary>

**LACP bond bandwidth is per-flow, not aggregate.**

LACP (802.3ad) distributes traffic across links based on a hash of the packet header (source/destination IP and port). A single TCP connection (single flow) can only use one physical link — 25 Gbps maximum.

The 50 Gbps aggregate bandwidth is only achievable with multiple concurrent flows. `iperf3` with a single connection tests single-flow performance.

**To verify aggregate bandwidth:**
```bash
# Run iperf3 with multiple parallel flows
iperf3 -c 10.0.20.20 -P 8  # 8 parallel connections
# This should achieve close to 50 Gbps
```

**Hash policy also matters:**
- `layer2`: Hash on MAC addresses (poor distribution for same-subnet traffic)
- `layer3+4`: Hash on IP + port (much better distribution for K8s traffic)

```bash
# Set the bond hash policy
ip link set bond0 type bond xmit_hash_policy layer3+4
```
</details>

---

## Hands-On Exercise: Design a Network for a K8s Cluster

**Task**: Design the network architecture for a 100-node Kubernetes cluster in 4 racks.

### Requirements
- 100 worker nodes + 3 control plane nodes
- Ceph storage cluster (3 dedicated OSD nodes)
- MetalLB for external load balancing
- Calico CNI with BGP mode
- PXE provisioning capability

### Steps

1. **Define the VLAN structure:**

```
VLAN 10: Management (10.0.10.0/24) — BMC, jump hosts
VLAN 20: Kubernetes (10.0.20.0/22) — node communication, pod traffic
VLAN 30: Storage (10.0.30.0/24) — Ceph cluster + public network, MTU 9000
VLAN 40: Provisioning (10.0.40.0/24) — PXE boot, isolated
VLAN 50: External (10.0.50.0/24) — MetalLB VIP range
```

2. **Design the switching fabric:**

```
Spine: 2x 100GbE switches (32 ports each)
Leaf: 4x 25GbE ToR switches (48 down + 6x 100G up), one per rack
Oversubscription: 48x25=1200 / 6x100=600 = 2:1 ✓
```

3. **Plan server NIC assignment:**

```
Per server:
  bond0 (eno1+eno2, LACP, 2x 25GbE): VLAN 20 + 30 + 50 trunk
  eno3 (1GbE): VLAN 10 management
  BMC (1GbE): VLAN 10
```

4. **Define BGP peering:**

```
Leaf AS numbers: 64501 (rack-a), 64502 (rack-b), etc.
Spine AS: 64500
Calico node AS: 64512
Each node peers with its local leaf switch
Leaf switches peer with both spines
```

5. **Calculate bandwidth:**

```
25 nodes per rack × 25 Gbps = 625 Gbps intra-rack
6 × 100 Gbps = 600 Gbps to spine (effective ~1:1 for connected hosts; 2:1 at full switch capacity)
Total spine bandwidth: 2 × 32 × 100G = 6,400 Gbps
```

### Success Criteria
- [ ] VLAN design documented with subnets and purposes
- [ ] Spine-leaf topology sized with oversubscription ratio < 3:1
- [ ] Server NIC assignment defined (bond + management + BMC)
- [ ] BGP AS numbers assigned
- [ ] MTU documented per VLAN (9000 for storage)
- [ ] PXE VLAN isolated from production
- [ ] MetalLB VIP range defined on external VLAN

---

## Next Module

Continue to [Module 3.2: BGP & Routing for Kubernetes](../module-3.2-bgp-routing/) to deep-dive into BGP peering between Kubernetes nodes and datacenter switches.
