# Module 5.6: Project Calico - The Full-Stack Networking and Security Platform

> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 90-120 minutes

## The BGP Misconfiguration That Cost $180,000

*A 200-node production cluster at a financial services company. Everything running smoothly. Then a new network engineer made a single configuration change.*

```
[Tuesday, 2:14 PM] @network-eng  Adding BGP peering to the new ToR switch in rack 7.
                                  Following the runbook.
[Tuesday, 2:17 PM] @network-eng  BGP peer configured. ASN set to 64512.
[Tuesday, 2:19 PM] @monitoring   ALERT: Latency spike on payment-gateway.
                                  P99 jumped from 12ms to 340ms.
[Tuesday, 2:22 PM] @monitoring   ALERT: 502 errors on checkout-service. Rate: 38%.
[Tuesday, 2:25 PM] @sre-lead     Something's wrong with the network. Pods can still
                                  reach each other but packets are being dropped.
[Tuesday, 2:31 PM] @sre-lead     tcpdump shows packets arriving but responses going
                                  somewhere else. Asymmetric routing?
[Tuesday, 2:44 PM] @network-eng  Wait—the ToR switch in rack 7 is AS 64513, not 64512.
                                  I used the wrong ASN from the old rack.
[Tuesday, 2:47 PM] @sre-lead     That would explain it. The switch is accepting routes
                                  but the return path goes through a different peer.
[Tuesday, 3:02 PM] @sre-lead     Confirming: calicoctl node status shows BGP session
                                  to 10.0.7.1 flapping. State: "Established" then
                                  "Connect" every 30 seconds.
[Tuesday, 3:08 PM] @network-eng  Fixed the ASN. Sessions stabilizing.
[Tuesday, 3:14 PM] @sre-lead     BGP sessions stable. Packet loss dropping.
[Tuesday, 3:22 PM] @monitoring   All services recovered. Latency back to normal.

[Wednesday, 9:00 AM]
@cto          Impact report: 40% packet loss for 68 minutes.
              $180,000 in failed transactions.
              Root cause: wrong ASN in a single BGP peer configuration.
```

One wrong number. Four characters. $180,000 in lost revenue and a very uncomfortable post-mortem. The engineer followed the runbook -- but the runbook had rack 6's ASN, not rack 7's. The lesson was not about blame. It was about automation: after this incident, the team moved to Calico's BGPPeer CRDs managed through GitOps, where every change was reviewed in a pull request before applying.

This module teaches you Calico from the ground up -- architecture, BGP, IPAM, policy, eBPF, WireGuard -- so that you understand every moving piece well enough to prevent incidents like this one.

**What You'll Learn**:
- Calico's architecture: Felix, BIRD, Typha, and how they work together
- BGP networking: node-to-node mesh, route reflectors, peering with physical infrastructure
- IP address management: pools, blocks, affinity, and borrowing
- Network policy: Kubernetes native, Calico-specific, tiers, L7, and DNS-based policies
- eBPF dataplane: when to use it and how to enable it
- WireGuard encryption: zero-config pod-to-pod encryption
- Scaling Calico to 1,000+ nodes

**Prerequisites**:
- Kubernetes networking basics (Services, Pods, CNI)
- [Module 5.1: Cilium](module-5.1-cilium.md) (for comparison context)
- Basic understanding of BGP (helpful, not required -- we cover it here)
- [Security Principles Foundations](../../foundations/security-principles/README.md)

---

## Why This Module Matters

Calico is not just a CNI plugin. It is a full networking and security platform that runs on everything from a single-node kind cluster to thousand-node bare-metal deployments peered with physical routers. While Cilium innovates with eBPF, Calico has been the production workhorse of Kubernetes networking since before Kubernetes was mainstream.

Here is what makes Calico different from every other CNI:

**It speaks BGP natively.** Calico does not use overlay networks by default. It assigns real, routable IP addresses to pods and distributes routes using the same protocol that runs the internet. This means your pods can talk to physical servers, VMs, and legacy infrastructure without NAT, encapsulation, or tunnels. For organizations with existing network infrastructure, this is transformative.

**It has the most comprehensive policy model in the ecosystem.** Standard Kubernetes NetworkPolicy is limited -- it cannot do host-level protection, DNS-based rules, application-layer filtering, or policy ordering. Calico extends all of these with GlobalNetworkPolicy, HostEndpoint, policy tiers, and L7 rules.

**It scales to thousands of nodes.** With the Typha proxy layer, Calico handles clusters that would overwhelm the Kubernetes API server if every agent talked to it directly.

> **Did You Know?**
>
> 1. Calico was originally developed by Tigera (founded in 2015 by engineers from Metaswitch Networks, a telecoms company). The BGP expertise came directly from building carrier-grade routing software -- the same technology that routes phone calls across continents now routes your Kubernetes pods.
>
> 2. Over 8 million nodes run Calico worldwide, making it the most widely deployed Kubernetes networking solution. It powers clusters at major banks, telecoms, government agencies, and 3 of the top 5 cloud providers. When AWS launched EKS, Calico was one of the first supported CNI options alongside their own VPC CNI.
>
> 3. Calico's eBPF dataplane can replace kube-proxy entirely -- just like Cilium -- eliminating iptables overhead for Service routing. In benchmarks, Calico's eBPF mode matches or exceeds traditional iptables performance by 30-40%, with consistent latency regardless of the number of Services in the cluster.
>
> 4. Project Calico is named after a calico cat. The project's creators wanted a name that was friendly and memorable. The calico cat's distinctive patches of different colors inspired the metaphor of networking patches -- connecting different network segments into one cohesive fabric.

---

## Part 1: Calico Architecture

Understanding Calico's architecture is essential before configuring anything. Every component exists for a reason, and knowing which component does what will save you hours of debugging.

### The Big Picture

```
CALICO ARCHITECTURE ON A KUBERNETES CLUSTER
═══════════════════════════════════════════════════════════════════════

                    ┌───────────────────────────────┐
                    │      Kubernetes API Server     │
                    │   (stores all Calico CRDs)     │
                    └───────────┬───────────────────┘
                                │
                    ┌───────────▼───────────────────┐
                    │     Calico API Server          │
                    │  (validates Calico resources)  │
                    └───────────┬───────────────────┘
                                │
              ┌─────────────────┼─────────────────────┐
              │                 │                       │
              ▼                 ▼                       ▼
     ┌────────────────┐ ┌────────────────┐  ┌────────────────┐
     │  Typha (opt.)  │ │  Typha (opt.)  │  │  Typha (opt.)  │
     │  (proxy/cache) │ │  (proxy/cache) │  │  (proxy/cache) │
     └───────┬────────┘ └───────┬────────┘  └───────┬────────┘
             │                  │                    │
      ┌──────┼──────┐   ┌──────┼──────┐      ┌─────┼──────┐
      │      │      │   │      │      │      │     │      │
      ▼      ▼      ▼   ▼      ▼      ▼      ▼     ▼      ▼
   ┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐
   │Node1││Node2││Node3││Node4││Node5││Node6││Node7││Node8│
   └─────┘└─────┘└─────┘└─────┘└─────┘└─────┘└─────┘└─────┘

   Each node runs calico/node (DaemonSet) containing:
   ┌────────────────────────────────────────────┐
   │              calico/node                    │
   │  ┌──────────┐ ┌──────┐ ┌───────────────┐  │
   │  │  Felix    │ │ BIRD │ │    confd       │  │
   │  │(iptables/ │ │(BGP  │ │(config from   │  │
   │  │ eBPF      │ │daemon│ │ API → BIRD)   │  │
   │  │ rules)    │ │routes│ │               │  │
   │  └──────────┘ └──────┘ └───────────────┘  │
   └────────────────────────────────────────────┘
```

### Component Deep Dive

#### Felix: The Policy Engine (Per-Node)

Felix is the brain on every node. It watches the Kubernetes API (or Typha) for changes to pods, services, network policies, and Calico-specific resources. When something changes, Felix programs the dataplane -- either iptables rules or eBPF programs -- to enforce the desired state.

What Felix does on every update cycle:
1. **Routes**: Programs the Linux routing table so the kernel knows how to reach pods on other nodes
2. **ACLs**: Creates iptables chains (or eBPF maps) that implement network policies
3. **IPIP/VXLAN**: Configures tunnel interfaces when overlay mode is needed
4. **Health**: Reports node health and connectivity status back to the API

```bash
# See Felix's logs on a node
kubectl logs -n calico-system -l k8s-app=calico-node -c calico-node | grep Felix

# Check Felix's configuration
kubectl get felixconfiguration default -o yaml
```

Felix is remarkably efficient. It uses a batching algorithm that collects changes over a short window and applies them as a single atomic update. This prevents the "iptables thrashing" problem where rapid pod creation would cause rule table rebuilds dozens of times per second.

#### BIRD: The BGP Daemon (Per-Node)

BIRD (BIRD Internet Routing Daemon) runs on every node and speaks BGP with other nodes (or external routers). Its job is simple but critical: tell the rest of the network which pod CIDRs live on this node.

When a pod is created on Node A with IP 10.244.1.15, BIRD on Node A announces to all its BGP peers: "To reach 10.244.1.0/26, send traffic to me." Every other node's BIRD daemon receives this announcement and programs a route.

```
HOW BIRD DISTRIBUTES ROUTES
═══════════════════════════════════════════════════════════════

Node A (10.0.1.10)                  Node B (10.0.1.11)
Pod CIDR: 10.244.1.0/26            Pod CIDR: 10.244.2.0/26

BIRD announces:                     BIRD announces:
"10.244.1.0/26 via 10.0.1.10"      "10.244.2.0/26 via 10.0.1.11"
         │                                    │
         └──────────── BGP ──────────────────┘

Result on Node A:                   Result on Node B:
  10.244.1.0/26 → local             10.244.1.0/26 → via 10.0.1.10
  10.244.2.0/26 → via 10.0.1.11    10.244.2.0/26 → local
```

**Important**: When using Calico's eBPF dataplane, BIRD is still used for route distribution. eBPF replaces iptables for policy enforcement and Service handling, not BGP.

#### confd: The Configuration Generator

confd watches the Calico datastore for BGP configuration changes (peers, ASN settings, route reflectors) and generates BIRD configuration files. When you create a BGPPeer CRD, confd translates it into BIRD syntax and triggers BIRD to reload.

You rarely interact with confd directly, but it is the glue between Calico's declarative CRDs and BIRD's imperative configuration files.

#### Typha: The Scaling Proxy

On a 50-node cluster, every Felix instance opens a watch connection to the Kubernetes API server. That is 50 watch connections -- manageable. On a 500-node cluster? 500 connections. On 2,000 nodes? The API server starts struggling.

Typha sits between Felix and the API server. A small number of Typha instances (typically 3-5) watch the API server, then fan out updates to all the Felix instances on their assigned nodes. This reduces API server load from O(n) to O(k), where k is the number of Typha replicas.

```
WITHOUT TYPHA (Small Clusters, < 100 nodes)
═══════════════════════════════════════════════

  ┌────────────────────┐
  │   API Server       │ ← 100 watch connections
  └────┬──┬──┬──┬──┬───┘
       │  │  │  │  │
       ▼  ▼  ▼  ▼  ▼
      Felix instances (one per node)


WITH TYPHA (Large Clusters, 100+ nodes)
═══════════════════════════════════════════════

  ┌────────────────────┐
  │   API Server       │ ← Only 3 watch connections
  └────┬─────┬─────┬───┘
       │     │     │
       ▼     ▼     ▼
    Typha1  Typha2  Typha3
     /|\     /|\     /|\
    / | \   / | \   / | \
   ▼  ▼  ▼ ▼  ▼  ▼ ▼  ▼  ▼
   Felix instances (hundreds per Typha)
```

The Tigera operator automatically deploys Typha when needed. For clusters over 200 nodes, Typha is not optional -- it is required for stability.

#### Calico API Server

The Calico API server extends the Kubernetes API with Calico-specific resource types. It handles validation and admission control for resources like:

- `IPPool`, `IPReservation`
- `BGPPeer`, `BGPConfiguration`
- `FelixConfiguration`
- `GlobalNetworkPolicy`, `NetworkPolicy` (Calico-flavored)
- `HostEndpoint`, `GlobalNetworkSet`
- `CalicoNodeStatus`

This means you can manage Calico entirely through `kubectl` -- no separate CLI required (though `calicoctl` still exists and is useful for diagnostics).

---

## Part 2: BGP Deep Dive

BGP (Border Gateway Protocol) is the protocol that holds the internet together. Every ISP, every cloud provider, every content delivery network uses BGP to exchange routing information. Calico brings this same proven, battle-tested protocol to Kubernetes networking.

### Why BGP Matters for Kubernetes

Most CNI plugins use **overlay networks** -- they encapsulate pod traffic inside VXLAN or Geneve tunnels to cross node boundaries. This works, but it adds overhead:

- Extra headers (50 bytes per packet for VXLAN)
- Encapsulation/decapsulation CPU cost
- Debugging difficulty (tcpdump shows tunnel packets, not the real traffic)
- MTU reduction (1500 - 50 = 1450 effective MTU)

Calico's BGP mode uses **native routing**. Pod IPs are real, routable addresses on the network. No encapsulation, no tunnels, no overhead. Packets go directly from one node to another using standard Linux routing.

### Node-to-Node Mesh (Default)

Out of the box, Calico configures a **full mesh** BGP topology. Every node peers with every other node. This is simple and works well for small clusters.

```
NODE-TO-NODE MESH (Full Mesh BGP)
═══════════════════════════════════════════════════════════════

  Node1 ◄──────► Node2
    ▲ \          / ▲
    │   \      /   │
    │    \   /     │
    │     \/       │
    │     /\       │
    │   /    \     │
    ▼ /        \   ▼
  Node3 ◄──────► Node4

  Every node peers with every other node.
  N nodes = N×(N-1)/2 BGP sessions.

  4 nodes  = 6 sessions    ✓ Fine
  20 nodes = 190 sessions  ✓ OK
  50 nodes = 1,225 sessions ⚠ Getting heavy
  100 nodes = 4,950 sessions ✗ Too many
```

The full mesh is the default because it is zero-configuration. But the number of BGP sessions grows quadratically: O(n^2). Above 50 nodes, you should switch to route reflectors.

```bash
# Check current BGP mesh status
calicoctl node status

# Output shows all peers:
# Calico process is running.
#
# IPv4 BGP status
# +--------------+-------------------+-------+----------+-------------+
# | PEER ADDRESS |     PEER TYPE     | STATE |  SINCE   |    INFO     |
# +--------------+-------------------+-------+----------+-------------+
# | 10.0.1.11    | node-to-node mesh | up    | 09:12:34 | Established |
# | 10.0.1.12    | node-to-node mesh | up    | 09:12:35 | Established |
# | 10.0.1.13    | node-to-node mesh | up    | 09:12:36 | Established |
# +--------------+-------------------+-------+----------+-------------+
```

### Route Reflectors (50+ Nodes)

Instead of every node peering with every other node, you designate a few nodes as **route reflectors**. All other nodes peer only with the route reflectors. The reflectors forward routes between their clients.

```
ROUTE REFLECTOR TOPOLOGY
═══════════════════════════════════════════════════════════════

                    ┌───────────────────┐
                    │  Route Reflector 1 │
                    │    (RR1)           │
                    └───────┬───────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
       Node1            Node2            Node3
       Node4            Node5            Node6
       ...              ...              ...

  For redundancy, use 2-3 route reflectors:

       ┌──────────┐              ┌──────────┐
       │   RR1    │◄────────────►│   RR2    │
       └────┬─────┘              └────┬─────┘
            │                         │
     ┌──────┼──────┐           ┌──────┼──────┐
     ▼      ▼      ▼           ▼      ▼      ▼
   Node1  Node2  Node3       Node4  Node5  Node6

  N nodes + K reflectors = N×K + K×(K-1)/2 sessions
  100 nodes + 3 RRs = 303 sessions (vs 4,950 in full mesh)
```

#### Setting Up Route Reflectors

First, disable the full mesh:

```yaml
apiVersion: projectcalico.org/v3
kind: BGPConfiguration
metadata:
  name: default
spec:
  # Disable the default node-to-node mesh
  nodeToNodeMeshEnabled: false
  # Default AS number for the cluster
  asNumber: 64512
```

Label the nodes that will be route reflectors:

```bash
# Designate specific nodes as route reflectors
kubectl label node worker-01 calico-route-reflector=true
kubectl label node worker-02 calico-route-reflector=true
kubectl label node worker-03 calico-route-reflector=true
```

Configure the route reflector nodes with a cluster ID:

```yaml
apiVersion: projectcalico.org/v3
kind: Node
metadata:
  name: worker-01
  labels:
    calico-route-reflector: "true"
spec:
  bgp:
    routeReflectorClusterID: 224.0.0.1
```

Create BGPPeer resources so non-reflector nodes peer with reflectors:

```yaml
apiVersion: projectcalico.org/v3
kind: BGPPeer
metadata:
  name: peer-to-rr
spec:
  # Every node that is NOT a route reflector...
  nodeSelector: "!has(calico-route-reflector)"
  # ...peers with every node that IS a route reflector
  peerSelector: has(calico-route-reflector)
```

And ensure route reflectors peer with each other:

```yaml
apiVersion: projectcalico.org/v3
kind: BGPPeer
metadata:
  name: rr-to-rr-mesh
spec:
  nodeSelector: has(calico-route-reflector)
  peerSelector: has(calico-route-reflector)
```

### Peering with Physical Infrastructure

This is where Calico truly shines in enterprise environments. You can peer Calico nodes directly with your datacenter's Top-of-Rack (ToR) switches, giving pod IPs full reachability across your physical network.

```
PEERING WITH PHYSICAL INFRASTRUCTURE
═══════════════════════════════════════════════════════════════

         ┌──────────────────────────┐
         │       Spine Switch       │
         │       AS 65000           │
         └──────┬──────────┬───────┘
                │          │
     ┌──────────▼──┐  ┌───▼──────────┐
     │  ToR Switch │  │  ToR Switch  │
     │  Rack 1     │  │  Rack 2      │
     │  AS 64512   │  │  AS 64513    │
     └──┬──┬──┬────┘  └──┬──┬──┬────┘
        │  │  │           │  │  │
        ▼  ▼  ▼           ▼  ▼  ▼
       K8s nodes         K8s nodes
       (Calico BGP       (Calico BGP
        peers with        peers with
        their ToR)        their ToR)
```

Configure peering with a specific ToR switch:

```yaml
apiVersion: projectcalico.org/v3
kind: BGPPeer
metadata:
  name: rack1-tor
spec:
  # Only nodes in rack 1 peer with this switch
  nodeSelector: rack == "rack1"
  peerIP: 10.0.1.1
  asNumber: 64512
```

### BGPConfiguration CRD

The BGPConfiguration resource controls global BGP behavior:

```yaml
apiVersion: projectcalico.org/v3
kind: BGPConfiguration
metadata:
  name: default
spec:
  # Disable full mesh when using route reflectors
  nodeToNodeMeshEnabled: false

  # Default AS number (can be overridden per node)
  asNumber: 64512

  # Which networks to advertise
  serviceClusterIPs:
  - cidr: 10.96.0.0/12    # Advertise ClusterIP ranges
  serviceExternalIPs:
  - cidr: 192.168.100.0/24  # Advertise external IPs
  serviceLoadBalancerIPs:
  - cidr: 192.168.200.0/24  # Advertise LoadBalancer IPs

  # Community tags for route filtering
  communities:
  - name: cluster-pods
    value: "64512:100"
  prefixAdvertisements:
  - cidr: 10.244.0.0/16
    communities:
    - cluster-pods
```

### AS Number Management

In BGP, every autonomous system (AS) needs a unique number. Calico supports:

- **Private ASNs**: 64512-65534 (16-bit) or 4200000000-4294967294 (32-bit). Use these for internal cluster networking.
- **Per-node ASN override**: Different nodes can use different AS numbers, useful when nodes span multiple racks or datacenters.

```yaml
# Override ASN for a specific node
apiVersion: projectcalico.org/v3
kind: Node
metadata:
  name: worker-rack2-01
spec:
  bgp:
    asNumber: 64513
    ipv4Address: 10.0.2.10/24
```

---

## Part 3: IPAM (IP Address Management)

Calico's IPAM is more sophisticated than most CNI plugins. It pre-allocates blocks of IPs to nodes, supports multiple pools, and handles edge cases like IP exhaustion gracefully.

### IP Pools

An IP Pool defines a range of IP addresses available for pod allocation:

```yaml
apiVersion: projectcalico.org/v3
kind: IPPool
metadata:
  name: default-pool
spec:
  cidr: 10.244.0.0/16
  # Encapsulation mode: None, IPIP, VXLAN, IPIPCrossSubnet, VXLANCrossSubnet
  ipipMode: Never
  vxlanMode: Never
  # Enable NAT for outgoing traffic to the internet
  natOutgoing: true
  # Controls which nodes can use this pool
  nodeSelector: all()
  # Block size: each node gets a /26 (64 IPs) by default
  blockSize: 26
```

#### Encapsulation Modes Explained

```
ENCAPSULATION DECISION TREE
═══════════════════════════════════════════════════════════════

Q: Can your physical network route pod CIDRs?

YES → ipipMode: Never, vxlanMode: Never
      ✓ Best performance (no encap overhead)
      ✓ Full visibility (real IPs in tcpdump)
      ✓ Requires BGP peering with infrastructure

NO  → Q: Are all nodes on the same L2 subnet?

      YES → ipipMode: Never, vxlanMode: CrossSubnet
            ✓ No encap within subnet
            ✓ VXLAN only for cross-subnet traffic
            ✓ Good compromise

      NO  → vxlanMode: Always
            (or ipipMode: Always)
            ✓ Works everywhere
            ✗ 50-byte overhead per packet
            ✗ Reduced MTU (1450 vs 1500)

NOTE: VXLAN is preferred over IPIP because:
  - VXLAN works with both IPv4 and IPv6
  - VXLAN traverses more NAT devices
  - IPIP is blocked by some cloud provider security groups
```

### Block Sizes and Affinity

Calico does not assign IPs one at a time. Instead, it carves the IP pool into **blocks** (default: /26 = 64 addresses) and assigns entire blocks to nodes. Pods on a node get IPs from that node's block.

```
IP BLOCK ALLOCATION
═══════════════════════════════════════════════════════════════

IP Pool: 10.244.0.0/16 (65,536 IPs)
Block Size: /26 (64 IPs per block)
Total Blocks: 1,024

Node A claims block: 10.244.0.0/26   (IPs .0 - .63)
Node B claims block: 10.244.0.64/26  (IPs .64 - .127)
Node C claims block: 10.244.0.128/26 (IPs .128 - .191)

Pod on Node A gets: 10.244.0.12
Pod on Node A gets: 10.244.0.13
Pod on Node B gets: 10.244.0.78
```

Why blocks? **Route aggregation.** Instead of advertising one route per pod (potentially thousands), each node advertises one route per block. A node with 50 pods might only need one /26 block -- a single route entry.

```bash
# View IPAM block allocations
calicoctl ipam show --show-blocks

# Output:
# +----------+--------------+-----------+------------+-----------+
# | GROUPING |     CIDR     | IPS TOTAL | IPS IN USE | IPS FREE  |
# +----------+--------------+-----------+------------+-----------+
# | Block    | 10.244.0.0/26|        64 |         12 |        52 |
# | Block    | 10.244.0.64/26|       64 |         31 |        33 |
# | Block    | 10.244.0.128/26|      64 |          8 |        56 |
# +----------+--------------+-----------+------------+-----------+
```

### Per-Namespace IP Pool Assignment

You can assign different IP pools to different namespaces. This is powerful for multi-tenancy, compliance, or network segmentation:

```yaml
# Create a dedicated pool for the finance namespace
apiVersion: projectcalico.org/v3
kind: IPPool
metadata:
  name: finance-pool
spec:
  cidr: 10.245.0.0/24
  ipipMode: Never
  vxlanMode: Never
  natOutgoing: true
  blockSize: 28   # Smaller blocks (16 IPs) for tighter packing
```

Annotate the namespace to use the pool:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: finance
  annotations:
    cni.projectcalico.org/ipv4pools: '["finance-pool"]'
```

Every pod in the `finance` namespace will now get an IP from 10.245.0.0/24. This makes firewall rules trivial: "All traffic from 10.245.0.0/24 is the finance team."

### IP Borrowing

What happens when a node's block is full but there are free IPs in other blocks? Calico supports **IP borrowing** -- a node can allocate individual IPs from blocks that belong to other nodes, if those blocks have spare capacity.

This is a safety mechanism. It prevents pod scheduling failures due to IP exhaustion on a single node, even when the overall pool has plenty of capacity. The trade-off is slightly less efficient routing (the borrowed IP creates an additional /32 route).

```bash
# Check for borrowed IPs
calicoctl ipam show --show-borrowed

# If you see borrowed IPs, consider:
# 1. Adding more IP pools
# 2. Reducing the block size for denser packing
# 3. Rebalancing blocks across nodes
```

### IP Reservations

Need to reserve specific IPs (for example, for a service that must always have a known address)?

```yaml
apiVersion: projectcalico.org/v3
kind: IPReservation
metadata:
  name: reserved-ips
spec:
  reservedCIDRs:
  - 10.244.0.1/32    # Reserved for gateway
  - 10.244.0.2/32    # Reserved for DNS
  - 10.244.100.0/24  # Reserved for future use
```

---

## Part 4: Network Policy

Calico's network policy engine is the most feature-rich in the Kubernetes ecosystem. It supports everything from basic Kubernetes NetworkPolicy to advanced features that no other CNI offers.

### Standard Kubernetes NetworkPolicy

Calico fully implements the Kubernetes NetworkPolicy API. If you already have NetworkPolicy resources, they work with Calico out of the box:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-api
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - port: 8080
      protocol: TCP
```

But standard NetworkPolicy has significant limitations:
- Cannot apply to host traffic (only pod traffic)
- No deny rules (only allow rules when a policy selects a pod)
- No global policies (must be created per-namespace)
- No policy ordering (all policies are OR'd together)
- No L7 rules (cannot filter by HTTP method or path)
- No DNS-based rules (cannot allow/deny by domain name)

### Calico NetworkPolicy (Namespace-Scoped)

Calico's own NetworkPolicy CRD extends the standard with all the missing features:

```yaml
apiVersion: projectcalico.org/v3
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-api
  namespace: production
spec:
  selector: app == "api"
  types:
  - Ingress
  - Egress
  ingress:
  - action: Allow
    source:
      selector: app == "frontend"
    destination:
      ports:
      - 8080
  egress:
  - action: Allow
    destination:
      selector: app == "database"
    destination:
      ports:
      - 5432
  # Explicit deny for everything else (logged)
  - action: Deny
```

### GlobalNetworkPolicy

GlobalNetworkPolicy applies across all namespaces. This is essential for platform teams that need cluster-wide security baselines:

```yaml
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: deny-external-egress
spec:
  # Apply to all pods in all namespaces
  selector: all()
  types:
  - Egress
  egress:
  # Allow DNS
  - action: Allow
    protocol: UDP
    destination:
      ports:
      - 53
  # Allow traffic within the cluster
  - action: Allow
    destination:
      nets:
      - 10.244.0.0/16   # Pod CIDR
      - 10.96.0.0/12     # Service CIDR
  # Deny everything else (no internet access by default)
  - action: Deny
```

### HostEndpoint Protection

Unlike any other CNI, Calico can protect the host itself -- not just pods. HostEndpoints let you apply policies to the node's physical interfaces:

```yaml
apiVersion: projectcalico.org/v3
kind: HostEndpoint
metadata:
  name: worker-01-eth0
  labels:
    role: worker
    rack: rack1
spec:
  interfaceName: eth0
  node: worker-01
  expectedIPs:
  - 10.0.1.10
```

Now you can write policies for the host:

```yaml
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: restrict-host-ssh
spec:
  selector: role == "worker"
  types:
  - Ingress
  ingress:
  # Only allow SSH from the bastion host
  - action: Allow
    protocol: TCP
    source:
      nets:
      - 10.0.0.5/32     # Bastion host
    destination:
      ports:
      - 22
  # Allow all pod traffic (don't break Kubernetes)
  - action: Allow
    source:
      nets:
      - 10.244.0.0/16
  # Allow Kubernetes API
  - action: Allow
    protocol: TCP
    destination:
      ports:
      - 6443
      - 10250
  # Deny all other host ingress
  - action: Deny
  applyOnForward: true
  preDNAT: true
```

### Policy Tiers and Ordering

This is one of Calico's most powerful features. Policy tiers let different teams manage policies at different priority levels:

```
POLICY TIERS (Evaluated Top to Bottom)
═══════════════════════════════════════════════════════════════

  ┌─────────────────────────────────────────────────────┐
  │  TIER: security (order: 100)                        │
  │  Owner: Security Team                               │
  │  Purpose: Compliance, PCI-DSS, zero-trust baseline  │
  │                                                     │
  │  Policies:                                          │
  │   - block-known-bad-ips (GlobalNetworkPolicy)       │
  │   - require-mtls-for-pci (GlobalNetworkPolicy)      │
  │   - deny-metadata-service (GlobalNetworkPolicy)     │
  │                                                     │
  │  If no policy matches → fall through to next tier   │
  └──────────────────────┬──────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────┐
  │  TIER: platform (order: 200)                        │
  │  Owner: Platform Team                               │
  │  Purpose: Infrastructure-level rules                │
  │                                                     │
  │  Policies:                                          │
  │   - allow-dns-everywhere (GlobalNetworkPolicy)      │
  │   - allow-monitoring-scrape (GlobalNetworkPolicy)   │
  │   - allow-ingress-controller (GlobalNetworkPolicy)  │
  │                                                     │
  │  If no policy matches → fall through to next tier   │
  └──────────────────────┬──────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────┐
  │  TIER: application (order: 300)                     │
  │  Owner: Development Teams                           │
  │  Purpose: App-specific allow rules                  │
  │                                                     │
  │  Policies:                                          │
  │   - frontend-to-api (NetworkPolicy)                 │
  │   - api-to-database (NetworkPolicy)                 │
  │                                                     │
  │  If no policy matches → default deny                │
  └─────────────────────────────────────────────────────┘
```

Create a tier:

```yaml
apiVersion: projectcalico.org/v3
kind: Tier
metadata:
  name: security
spec:
  order: 100
```

Assign a policy to a tier:

```yaml
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: security.block-metadata-service
spec:
  tier: security
  order: 10
  selector: all()
  types:
  - Egress
  egress:
  # Block access to cloud metadata service (169.254.169.254)
  - action: Deny
    destination:
      nets:
      - 169.254.169.254/32
  # Pass everything else to the next tier
  - action: Pass
```

The **Pass** action is key. It means "I don't have an opinion on this traffic -- let the next tier decide." This is how tiers compose without stepping on each other.

### Application Layer Policy (L7)

Calico can integrate with Envoy to provide L7 (HTTP) policy enforcement:

```yaml
apiVersion: projectcalico.org/v3
kind: NetworkPolicy
metadata:
  name: allow-get-only
  namespace: production
spec:
  selector: app == "api"
  types:
  - Ingress
  ingress:
  - action: Allow
    source:
      selector: app == "frontend"
    http:
      methods:
      - GET
      paths:
      - exact: /api/v1/products
      - prefix: /api/v1/health
  # Block POST, PUT, DELETE from frontend
  - action: Deny
    source:
      selector: app == "frontend"
```

L7 policies require the Envoy proxy (deployed as a DaemonSet or sidecar). This adds some overhead but enables powerful HTTP-aware security.

### DNS-Based Policies

Allow pods to reach specific domains without knowing their IP addresses:

```yaml
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: allow-github-egress
spec:
  selector: role == "ci-runner"
  types:
  - Egress
  egress:
  # Allow DNS resolution
  - action: Allow
    protocol: UDP
    destination:
      ports:
      - 53
  # Allow HTTPS to GitHub
  - action: Allow
    protocol: TCP
    destination:
      domains:
      - "*.github.com"
      - "github.com"
      - "*.githubusercontent.com"
      ports:
      - 443
  # Deny all other egress
  - action: Deny
```

DNS policies work by intercepting DNS responses and dynamically creating IP-based rules for the resolved addresses. This is done transparently -- no application changes needed.

---

## Part 5: eBPF Dataplane

Calico's eBPF dataplane replaces iptables for packet processing, delivering better performance and more consistent behavior at scale.

### When to Use eBPF vs iptables

```
eBPF vs IPTABLES DECISION GUIDE
═══════════════════════════════════════════════════════════════

USE eBPF WHEN:
  ✓ Running Linux kernel 5.3+ (ideally 5.8+)
  ✓ Want to replace kube-proxy entirely
  ✓ Have 1,000+ Services (iptables becomes slow)
  ✓ Need consistent latency regardless of rule count
  ✓ Want direct server return (DSR) for LoadBalancer services
  ✓ Need source IP preservation without externalTrafficPolicy

USE IPTABLES WHEN:
  ✓ Running older kernels (< 5.3)
  ✓ Need HostEndpoint policies (limited in eBPF mode)
  ✓ Using non-standard network setups
  ✓ Regulatory requirement for well-known technology
  ✓ Team is more familiar with iptables debugging
```

### Performance Numbers

Benchmarks from the Calico project (your numbers will vary):

| Metric | iptables | eBPF | Improvement |
|--------|----------|------|-------------|
| **Connections/sec** (1000 Services) | 18,500 | 26,200 | +42% |
| **P99 latency** (1000 Services) | 4.2ms | 1.8ms | -57% |
| **CPU per node** (idle) | 2.1% | 1.4% | -33% |
| **Rule update time** (adding a Service) | 120ms | 8ms | -93% |
| **Latency scaling** (10→10,000 Services) | Linear increase | Constant | O(1) vs O(n) |

The key advantage is **constant-time lookups**. With iptables, every packet traverses a chain of rules -- more Services means more rules means more latency. With eBPF hash maps, lookup time is constant regardless of table size.

### Enabling eBPF Mode

Using the Tigera operator:

```yaml
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  calicoNetwork:
    linuxDataplane: BPF
    # When using eBPF, VXLAN is currently the supported overlay
    ipPools:
    - cidr: 10.244.0.0/16
      encapsulation: VXLAN
      blockSize: 26
```

After enabling eBPF, you can remove kube-proxy:

```bash
# Disable kube-proxy (Calico eBPF handles Services natively)
kubectl patch ds -n kube-system kube-proxy -p \
  '{"spec":{"template":{"spec":{"nodeSelector":{"non-calico": "true"}}}}}'

# Verify eBPF mode is active
kubectl get felixconfiguration default -o yaml | grep -i bpf
# bpfEnabled: true
```

### eBPF Limitations

Be aware of these limitations before enabling eBPF mode:

- **Kernel version**: Requires Linux 5.3+, recommended 5.8+ for full feature support
- **HostEndpoint policies**: Some HostEndpoint features are limited or unavailable in eBPF mode (check the release notes for your version)
- **IPIP encapsulation**: eBPF mode supports VXLAN but not IPIP (use VXLAN or no encapsulation)
- **Debugging tools**: Traditional iptables debugging tools (iptables-save, conntrack) do not show eBPF decisions; use `calico-bpf` tool instead
- **Feature parity**: Some newer eBPF features are in tech preview; check compatibility matrix

```bash
# Debug eBPF dataplane
# View BPF program status
kubectl exec -n calico-system calico-node-xxxxx -- calico-node -bpf tc dump eth0

# View BPF conntrack table
kubectl exec -n calico-system calico-node-xxxxx -- calico-node -bpf conntrack dump

# View BPF routes
kubectl exec -n calico-system calico-node-xxxxx -- calico-node -bpf routes dump
```

---

## Part 6: WireGuard Encryption

Calico can encrypt all pod-to-pod traffic using WireGuard, a modern VPN protocol built into the Linux kernel. No certificates, no PKI infrastructure, no sidecars.

### Why WireGuard?

Traditional options for pod traffic encryption:
- **Service mesh mTLS**: Adds a sidecar to every pod, 50-100MB memory overhead per pod, complex certificate management
- **IPsec**: Heavyweight, complex configuration, CPU-intensive
- **WireGuard**: Kernel-level, ~3-5% CPU overhead, zero configuration per pod

WireGuard encrypts traffic between nodes transparently. Pods do not know encryption is happening -- it occurs at the node level, below the pod network stack.

### Enabling WireGuard

```yaml
apiVersion: projectcalico.org/v3
kind: FelixConfiguration
metadata:
  name: default
spec:
  wireguardEnabled: true
  # Optional: also encrypt IPv6 traffic
  wireguardEnabledV6: true
```

That is it. No per-node configuration, no certificate rotation, no sidecars. Every node generates a WireGuard keypair, exchanges keys through the Calico datastore, and establishes encrypted tunnels to every peer automatically.

```bash
# Verify WireGuard is active on nodes
kubectl exec -n calico-system calico-node-xxxxx -- wg show

# Output:
# interface: wireguard.cali
#   public key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
#   listening port: 51820
#
# peer: yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
#   endpoint: 10.0.1.11:51820
#   allowed ips: 10.244.0.64/26, 10.244.0.128/26
#   latest handshake: 12 seconds ago
#   transfer: 1.24 GiB received, 983.11 MiB sent
```

### Performance Overhead

WireGuard is fast because it runs in the kernel and uses modern cryptography (ChaCha20-Poly1305):

| Metric | Without WireGuard | With WireGuard | Overhead |
|--------|-------------------|----------------|----------|
| **Throughput** (TCP) | 9.4 Gbps | 8.9 Gbps | ~5% |
| **Latency** (P50) | 0.12ms | 0.14ms | +0.02ms |
| **CPU per node** | 1.4% | 2.1% | +0.7% |
| **MTU overhead** | 0 bytes | 60 bytes | Reduces effective MTU |

For most workloads, WireGuard overhead is negligible. The main consideration is the MTU reduction -- ensure your pod MTU accounts for the WireGuard header (typically set to 1440 when using WireGuard without other encapsulation).

### WireGuard + eBPF

WireGuard works with both iptables and eBPF dataplanes. When combined with eBPF, you get:
- Kernel-level packet processing (eBPF)
- Kernel-level encryption (WireGuard)
- No kube-proxy
- No sidecars
- No iptables

This is arguably the most streamlined Kubernetes networking stack possible.

---

## Part 7: Installation

### Tigera Operator (Recommended)

The Tigera operator is the recommended installation method. It manages the Calico lifecycle, handles upgrades, and ensures components are configured correctly.

```bash
# Install the Tigera operator
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/tigera-operator.yaml

# Create the Installation resource
cat <<EOF | kubectl apply -f -
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  calicoNetwork:
    # Use BGP with no encapsulation (best for bare metal)
    bgp: Enabled
    ipPools:
    - cidr: 10.244.0.0/16
      encapsulation: None
      natOutgoing: Enabled
      nodeSelector: all()
      blockSize: 26
    # Or for cloud environments, use VXLAN:
    # - cidr: 10.244.0.0/16
    #   encapsulation: VXLAN
    #   natOutgoing: Enabled
---
apiVersion: operator.tigera.io/v1
kind: APIServer
metadata:
  name: default
spec: {}
EOF
```

```bash
# Watch the installation progress
watch kubectl get tigerastatus

# Output when healthy:
# NAME        AVAILABLE   PROGRESSING   DEGRADED   SINCE
# apiserver   True        False         False      2m
# calico      True        False         False      90s
```

### Manifest-Based Installation

For environments where operators are not preferred:

```bash
# Direct manifest installation (includes CRDs, DaemonSets, Deployments)
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/calico.yaml
```

The manifest method gives you less lifecycle management but is simpler for testing and development.

### calicoctl CLI Tool

While Calico resources can be managed with `kubectl`, the `calicoctl` CLI provides additional diagnostics:

```bash
# Install calicoctl
curl -L https://github.com/projectcalico/calico/releases/download/v3.28.0/calicoctl-linux-amd64 -o calicoctl
chmod +x calicoctl
sudo mv calicoctl /usr/local/bin/

# Node status (shows BGP peering)
calicoctl node status

# IPAM diagnostics
calicoctl ipam show
calicoctl ipam show --show-blocks
calicoctl ipam show --show-borrowed

# Check for configuration issues
calicoctl node checksystem

# View applied policies
calicoctl get networkpolicy --all-namespaces
calicoctl get globalnetworkpolicy
```

---

## Part 8: Scaling Calico to 1,000+ Nodes

### Typha Deployment

For large clusters, Typha is essential. The Tigera operator handles this automatically, but here are the guidelines:

| Cluster Size | Typha Replicas | Notes |
|--------------|----------------|-------|
| < 100 nodes | 0 (optional) | Felix connects directly to API server |
| 100-200 nodes | 1-2 | Reduces API server load by 50-100x |
| 200-500 nodes | 3 | Standard HA deployment |
| 500-1,000 nodes | 3-5 | Monitor Typha CPU/memory |
| 1,000+ nodes | 5-7 | Consider splitting into multiple clusters |

```yaml
# Scale Typha manually if needed
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  typhaDeployment:
    spec:
      minReadySeconds: 30
      template:
        spec:
          terminationGracePeriodSeconds: 60
```

### Route Reflector Topology for Scale

For very large clusters, use a hierarchical route reflector topology:

```
HIERARCHICAL ROUTE REFLECTORS (1,000+ Nodes)
═══════════════════════════════════════════════════════════════

            ┌──────────┐     ┌──────────┐
            │ Super RR │◄───►│ Super RR │
            │  (Tier 1)│     │  (Tier 1)│
            └──┬───┬───┘     └──┬───┬───┘
               │   │            │   │
        ┌──────┘   └──────┐    │   └──────────┐
        ▼                 ▼    ▼              ▼
  ┌──────────┐     ┌──────────┐      ┌──────────┐
  │  RR-AZ1  │     │  RR-AZ2  │      │  RR-AZ3  │
  │ (Tier 2) │     │ (Tier 2) │      │ (Tier 2) │
  └──┬──┬──┬─┘     └──┬──┬──┬─┘      └──┬──┬──┬─┘
     │  │  │          │  │  │            │  │  │
     ▼  ▼  ▼          ▼  ▼  ▼            ▼  ▼  ▼
   Nodes in AZ1     Nodes in AZ2       Nodes in AZ3
   (300+ nodes)     (300+ nodes)       (300+ nodes)
```

### etcd Performance (Kubernetes Datastore)

Calico stores all its state in the Kubernetes API (backed by etcd). At scale, this means:

- **Watch connections**: Typha dramatically reduces these
- **Object count**: Thousands of WorkloadEndpoint objects (one per pod)
- **Update rate**: Pod churn creates update storms; Typha batches these

Recommendations for large clusters:
1. Use SSDs for etcd storage (mandatory above 500 nodes)
2. Monitor etcd latency: `etcd_disk_wal_fsync_duration_seconds` should be < 10ms
3. Consider dedicated etcd nodes (not co-located with control plane workloads)
4. Enable etcd compaction and defragmentation on a schedule

---

## Comparison: Calico vs Cilium vs Flannel

| Feature | **Calico** | **Cilium** | **Flannel** |
|---------|-----------|-----------|------------|
| **Primary technology** | BGP + iptables/eBPF | eBPF | VXLAN overlay |
| **NetworkPolicy** | Full K8s + extended | Full K8s + extended | None (requires Calico addon) |
| **BGP support** | Native, first-class | Limited (via MetalLB) | None |
| **eBPF dataplane** | Yes (optional) | Yes (default) | No |
| **Overlay options** | IPIP, VXLAN, none | VXLAN, Geneve, none | VXLAN only |
| **WireGuard encryption** | Yes | Yes | No |
| **Host protection** | Yes (HostEndpoint) | Yes (Host Policies) | No |
| **L7 policy** | Yes (via Envoy) | Yes (native eBPF) | No |
| **DNS-based policy** | Yes | Yes | No |
| **Policy tiers** | Yes | No | No |
| **Observability** | Basic flow logs | Hubble (advanced) | None |
| **Service mesh** | No (integrates with others) | Sidecar-free mesh | No |
| **Replace kube-proxy** | Yes (eBPF mode) | Yes (default) | No |
| **Maturity** | Since 2015 (oldest) | Since 2017 | Since 2014 |
| **Scaling (tested)** | 5,000+ nodes | 5,000+ nodes | 5,000+ nodes |
| **Enterprise version** | Calico Cloud/Enterprise | Isovalent Enterprise | None |
| **Best for** | BGP, bare metal, enterprise policy | eBPF-first, observability | Simple overlay, getting started |
| **Complexity** | Medium-High | Medium-High | Low |

### When to Choose What

```
CHOOSING YOUR CNI
═══════════════════════════════════════════════════════════════

"I need to peer with physical network infrastructure"
└──▶ Calico (BGP is first-class, not bolted on)

"I want the best observability (Hubble)"
└──▶ Cilium (Hubble is unmatched)

"I just need something simple that works"
└──▶ Flannel (but add Calico for NetworkPolicy)

"My security team needs policy tiers and HostEndpoint"
└──▶ Calico (only CNI with policy tiers)

"I'm all-in on eBPF and want a sidecar-free service mesh"
└──▶ Cilium (eBPF-native from the ground up)

"I'm running bare metal with spine/leaf networking"
└──▶ Calico (designed for this exact use case)

"I want both options open"
└──▶ Calico with eBPF dataplane (BGP + eBPF)
```

---

## Common Mistakes

| # | Mistake | What Happens | How to Fix |
|---|---------|-------------|------------|
| 1 | **Using full mesh BGP on 100+ nodes** | Thousands of BGP sessions, BIRD memory exhaustion, slow convergence | Switch to route reflectors; disable `nodeToNodeMeshEnabled` and deploy 2-3 RR nodes |
| 2 | **Wrong ASN in BGP peer config** | Asymmetric routing, session flapping, intermittent packet loss that is incredibly hard to diagnose | Manage BGPPeer CRDs in Git; require PR review for all BGP changes; use `calicoctl node status` to verify sessions |
| 3 | **Forgetting natOutgoing on IP pools** | Pods cannot reach the internet; DNS to external domains fails silently | Set `natOutgoing: true` on the IPPool unless you have explicit return routes for pod CIDRs on your infrastructure |
| 4 | **Enabling eBPF without checking kernel version** | Felix crashes or falls back to iptables silently; partial functionality | Verify kernel 5.3+ with `uname -r`; check `calicoctl node checksystem` before enabling |
| 5 | **Not deploying Typha on large clusters** | API server overwhelmed by watch connections; Felix instances disconnected; policies not applied | Deploy Typha when cluster exceeds 100 nodes; the Tigera operator does this automatically |
| 6 | **Overlapping IP pools** | IPAM assigns the same IP to two pods; conflict causes intermittent connectivity failures | Audit all IPPool CIDRs with `calicoctl get ippool -o yaml`; ensure CIDRs do not overlap with each other or with Service/node CIDRs |
| 7 | **Using `action: Deny` without `action: Pass`** in tiered policies | Traffic blocked by a higher-tier policy never reaches lower tiers; application policies silently ignored | Use `action: Pass` as the final rule in a tier to delegate unmatched traffic to the next tier |
| 8 | **IPIP mode in cloud environments that block IP protocol 4** | Pods on different nodes cannot communicate; only same-node pods work | Switch to VXLAN encapsulation (uses UDP, not a custom IP protocol); check cloud security group rules |
| 9 | **Block size too large for small clusters** | Wasted IPs; only a few pods per node but each node claims a /26 (64 IPs) | Reduce `blockSize` to 28 (16 IPs) or 29 (8 IPs) for dev/test clusters |
| 10 | **Not setting MTU correctly with encapsulation** | Packet fragmentation, degraded throughput, intermittent TCP connection hangs | Set MTU to 1450 for VXLAN, 1480 for IPIP, 1440 for WireGuard + VXLAN; check with `ping -s 1472 -M do <pod-ip>` |

---

## Quiz

Test your understanding of Calico's architecture, BGP, policy model, and operational features.

<details>
<summary><strong>Question 1</strong>: What are the three main components inside the calico/node container, and what does each one do?</summary>

**Answer:**

1. **Felix** -- The policy engine. Watches the Calico datastore (via API server or Typha) for changes and programs the Linux dataplane (iptables rules or eBPF programs) to enforce network policy, routes, and IPAM.

2. **BIRD** -- The BGP daemon. Distributes routing information between nodes so that each node knows how to reach pods on other nodes. Speaks standard BGP protocol.

3. **confd** -- The configuration generator. Watches the Calico datastore for BGP configuration changes (peers, ASN, route reflectors) and generates BIRD configuration files, then signals BIRD to reload.

</details>

<details>
<summary><strong>Question 2</strong>: A cluster has 80 nodes using full-mesh BGP. How many BGP sessions exist? At what point should you switch to route reflectors?</summary>

**Answer:**

Full mesh sessions = N x (N-1) / 2 = 80 x 79 / 2 = **3,160 BGP sessions**.

You should switch to route reflectors around **50 nodes** (1,225 sessions). The general guideline is that full mesh is fine under 50 nodes, workable up to 100, and problematic beyond that.

With 3 route reflectors, the same 80-node cluster would have: 77 x 3 + 3 = **234 sessions** -- a 93% reduction.

</details>

<details>
<summary><strong>Question 3</strong>: Explain the difference between <code>action: Deny</code> and <code>action: Pass</code> in a Calico GlobalNetworkPolicy within a policy tier.</summary>

**Answer:**

- **`action: Deny`** -- Explicitly drops the packet. The decision is final; no lower-priority tier gets to evaluate this traffic. Use this for hard security boundaries (block metadata service, block known-bad IPs).

- **`action: Pass`** -- Skips the current tier and passes the packet to the next tier for evaluation. This is how tiers delegate decisions. For example, a security tier might block known threats but Pass everything else to the platform tier for further evaluation.

If a policy in a tier neither matches the traffic with Allow/Deny nor has a Pass rule, and the traffic is selected by any policy in the tier, it is implicitly denied (default deny within a tier).

</details>

<details>
<summary><strong>Question 4</strong>: A pod on Node A has IP 10.244.0.45 (from block 10.244.0.0/26, which belongs to Node A). The block is full. A new pod is scheduled on Node A. What happens?</summary>

**Answer:**

Calico uses **IP borrowing**. When a node's allocated block is full, Calico's IPAM can borrow an individual IP from another node's block that has spare capacity. The new pod gets an IP like 10.244.0.100 (from Node B's block 10.244.0.64/26).

The trade-off is that this borrowed IP creates an additional /32 host route instead of being covered by the block's aggregate route. This slightly increases the routing table size but prevents pod scheduling failures.

To avoid frequent borrowing, you can: allocate additional blocks to the node, use a larger IP pool, or reduce block size for denser packing.

</details>

<details>
<summary><strong>Question 5</strong>: What is Typha and when is it required? What happens if you do not deploy it on a 500-node cluster?</summary>

**Answer:**

Typha is a proxy that sits between the Kubernetes API server and Felix agents. Instead of each Felix instance opening its own watch connection to the API server, a small number of Typha instances (3-5) watch the API and fan out updates.

On a 500-node cluster without Typha, you would have 500 simultaneous watch connections to the API server. Each watch duplicates the same data. This causes:
- **API server CPU/memory exhaustion** from serving 500 identical watches
- **Increased etcd load** from 500 parallel list/watch operations
- **Slow policy propagation** because the API server is overwhelmed
- **Potential API server crashes** during large-scale updates (e.g., applying a GlobalNetworkPolicy)

With 3 Typha replicas, the API server handles 3 watches instead of 500 -- a 99.4% reduction.

</details>

<details>
<summary><strong>Question 6</strong>: You want to encrypt all pod-to-pod traffic. Compare WireGuard encryption in Calico to mTLS via a service mesh. When would you choose each?</summary>

**Answer:**

**WireGuard (Calico)**:
- Operates at the node level (Layer 3) -- encrypts all traffic between nodes transparently
- Zero per-pod overhead (no sidecars)
- ~5% throughput overhead, ~0.02ms latency
- No application changes needed
- Encrypts ALL traffic (including non-HTTP protocols like databases, gRPC, custom TCP)
- No identity beyond "this node is in the cluster"

**mTLS (Service Mesh)**:
- Operates at the pod level (Layer 4/7) -- encrypts specific pod-to-pod connections
- Sidecar per pod (50-100MB memory for Envoy)
- Higher latency (~2ms for Istio)
- Provides cryptographic identity per service (SPIFFE)
- Enables L7 authorization (allow GET but deny POST)
- Only encrypts proxied traffic (misses raw TCP unless explicitly configured)

**Choose WireGuard** when you need blanket encryption for compliance (encrypt everything at rest and in transit) without the complexity of a service mesh.

**Choose mTLS** when you need per-service identity, L7 authorization, or traffic management features alongside encryption.

**Use both** when compliance requires node-level encryption AND you need service-level identity.

</details>

<details>
<summary><strong>Question 7</strong>: You configure a BGPPeer with the wrong ASN and traffic starts dropping. How would you diagnose this issue?</summary>

**Answer:**

Step-by-step diagnosis:

1. **Check BGP session status**:
   ```bash
   calicoctl node status
   ```
   Look for sessions in "Connect" or "Active" state (not "Established"). Flapping sessions will alternate between states.

2. **Check BIRD logs**:
   ```bash
   kubectl logs -n calico-system -l k8s-app=calico-node -c calico-node | grep -i bgp
   ```
   Look for "BGP Error" or "Notification" messages indicating ASN mismatch.

3. **Verify the BGPPeer configuration**:
   ```bash
   calicoctl get bgppeer -o yaml
   ```
   Cross-reference the `asNumber` with the actual ASN configured on the peer device.

4. **Check routing tables**:
   ```bash
   ip route | grep bird
   ```
   Missing or incorrect routes indicate BGP is not exchanging information correctly.

5. **Fix**: Update the BGPPeer CRD with the correct ASN. BGP sessions will re-establish within the hold timer interval (default 90 seconds).

</details>

<details>
<summary><strong>Question 8</strong>: Explain how Calico's per-namespace IP pool assignment works and give a use case where it solves a real problem.</summary>

**Answer:**

You annotate a namespace with `cni.projectcalico.org/ipv4pools: '["pool-name"]'`, and all pods created in that namespace receive IPs from the specified IPPool.

**Use case: PCI-DSS compliance for a payment service.**

A company runs a mixed Kubernetes cluster. The payment processing service must comply with PCI-DSS, which requires network segmentation -- the cardholder data environment (CDE) must be isolated and auditable.

By creating a dedicated IP pool (e.g., 10.245.0.0/24) for the `payment` namespace:
- All payment pods get IPs from a known, documented range
- Firewall rules on physical infrastructure can specifically allow/deny 10.245.0.0/24
- Network flow logs can be audited by CIDR range
- Compliance auditors can verify segmentation without understanding Kubernetes internals

Without per-namespace pools, pod IPs are scattered across the global pool, making network-level segmentation impossible without Calico-specific policies everywhere.

</details>

---

## Hands-On Exercise: Deploy Calico on kind and Implement Tiered Policies

### Objective

Deploy a Calico-powered kind cluster, create policy tiers, implement namespace-scoped policies, and verify BGP peering between nodes.

**Time**: 45-60 minutes

### Step 1: Create a kind Cluster with Calico

```bash
# Create a multi-node kind cluster WITHOUT the default CNI
cat <<EOF > calico-kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  # Disable default CNI so we can install Calico
  disableDefaultCNI: true
  # Disable kube-proxy if you want to test eBPF (optional)
  # kubeProxyMode: "none"
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/12"
nodes:
- role: control-plane
- role: worker
- role: worker
- role: worker
EOF

kind create cluster --name calico-lab --config calico-kind-config.yaml
```

### Step 2: Install Calico

```bash
# Install the Tigera operator
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/tigera-operator.yaml

# Wait for the operator to be ready
kubectl wait --for=condition=Available deployment/tigera-operator \
  -n tigera-operator --timeout=120s

# Create the Calico installation
cat <<EOF | kubectl apply -f -
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  calicoNetwork:
    ipPools:
    - cidr: 10.244.0.0/16
      encapsulation: VXLANCrossSubnet
      natOutgoing: Enabled
      nodeSelector: all()
      blockSize: 26
---
apiVersion: operator.tigera.io/v1
kind: APIServer
metadata:
  name: default
spec: {}
EOF

# Wait for Calico to be ready (this takes 2-3 minutes)
echo "Waiting for Calico to be ready..."
kubectl wait --for=condition=Available tigerastatus/calico --timeout=300s
kubectl wait --for=condition=Available tigerastatus/apiserver --timeout=300s

echo "Calico is ready!"
```

### Step 3: Install calicoctl and Verify

```bash
# Install calicoctl as a kubectl plugin
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/calicoctl.yaml

# Or install as a standalone binary (Linux example)
# curl -L https://github.com/projectcalico/calico/releases/download/v3.28.0/calicoctl-linux-amd64 -o calicoctl
# chmod +x calicoctl && sudo mv calicoctl /usr/local/bin/

# Check node status and BGP peering
kubectl calico node status
# You should see BGP sessions between all nodes (node-to-node mesh)

# Check IPAM
kubectl calico ipam show --show-blocks
```

### Step 4: Deploy Test Applications

```bash
# Create namespaces
kubectl create namespace frontend
kubectl create namespace backend
kubectl create namespace database

# Deploy a frontend app
kubectl -n frontend run frontend --image=nginx:1.27 --port=80 \
  --labels="app=frontend,tier=web"
kubectl -n frontend expose pod frontend --port=80

# Deploy a backend API
kubectl -n backend run api --image=nginx:1.27 --port=80 \
  --labels="app=api,tier=backend"
kubectl -n backend expose pod api --port=80

# Deploy a database
kubectl -n database run db --image=nginx:1.27 --port=80 \
  --labels="app=db,tier=data"
kubectl -n database expose pod db --port=80

# Wait for pods
kubectl wait --for=condition=Ready pod -l app=frontend -n frontend --timeout=60s
kubectl wait --for=condition=Ready pod -l app=api -n backend --timeout=60s
kubectl wait --for=condition=Ready pod -l app=db -n database --timeout=60s

# Verify connectivity (everything should work - no policies yet)
kubectl -n frontend exec frontend -- curl -s --max-time 3 api.backend.svc.cluster.local && echo "frontend -> api: OK"
kubectl -n backend exec api -- curl -s --max-time 3 db.database.svc.cluster.local && echo "api -> db: OK"
kubectl -n frontend exec frontend -- curl -s --max-time 3 db.database.svc.cluster.local && echo "frontend -> db: OK (should be blocked later)"
```

### Step 5: Create Policy Tiers

```bash
# Create the security tier (highest priority)
cat <<EOF | kubectl apply -f -
apiVersion: projectcalico.org/v3
kind: Tier
metadata:
  name: security
spec:
  order: 100
EOF

# Create the platform tier
cat <<EOF | kubectl apply -f -
apiVersion: projectcalico.org/v3
kind: Tier
metadata:
  name: platform
spec:
  order: 200
EOF

# Create the application tier
cat <<EOF | kubectl apply -f -
apiVersion: projectcalico.org/v3
kind: Tier
metadata:
  name: application
spec:
  order: 300
EOF

echo "Tiers created:"
kubectl get tiers
```

### Step 6: Implement Security Tier Policies

```bash
# Security tier: Block access to cloud metadata service
cat <<EOF | kubectl apply -f -
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: security.block-metadata
spec:
  tier: security
  order: 10
  selector: all()
  types:
  - Egress
  egress:
  - action: Deny
    destination:
      nets:
      - 169.254.169.254/32
  - action: Pass
EOF

# Security tier: Default pass (let other tiers decide)
echo "Security tier policies applied."
```

### Step 7: Implement Platform Tier Policies

```bash
# Platform tier: Allow DNS everywhere
cat <<EOF | kubectl apply -f -
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: platform.allow-dns
spec:
  tier: platform
  order: 10
  selector: all()
  types:
  - Egress
  egress:
  - action: Allow
    protocol: UDP
    destination:
      ports:
      - 53
  - action: Allow
    protocol: TCP
    destination:
      ports:
      - 53
  - action: Pass
EOF

echo "Platform tier policies applied."
```

### Step 8: Implement Application Tier Policies

```bash
# Application tier: frontend can only talk to API
cat <<EOF | kubectl apply -f -
apiVersion: projectcalico.org/v3
kind: NetworkPolicy
metadata:
  name: application.frontend-policy
  namespace: frontend
spec:
  tier: application
  order: 10
  selector: app == "frontend"
  types:
  - Egress
  egress:
  - action: Allow
    destination:
      selector: app == "api"
      namespaceSelector: projectcalico.org/name == "backend"
    destination:
      ports:
      - 80
  - action: Deny
EOF

# Application tier: API can talk to database
cat <<EOF | kubectl apply -f -
apiVersion: projectcalico.org/v3
kind: NetworkPolicy
metadata:
  name: application.api-policy
  namespace: backend
spec:
  tier: application
  order: 20
  selector: app == "api"
  types:
  - Egress
  egress:
  - action: Allow
    destination:
      selector: app == "db"
      namespaceSelector: projectcalico.org/name == "database"
    destination:
      ports:
      - 80
  - action: Deny
EOF

# Application tier: database accepts only from API
cat <<EOF | kubectl apply -f -
apiVersion: projectcalico.org/v3
kind: NetworkPolicy
metadata:
  name: application.db-policy
  namespace: database
spec:
  tier: application
  order: 30
  selector: app == "db"
  types:
  - Ingress
  ingress:
  - action: Allow
    source:
      selector: app == "api"
      namespaceSelector: projectcalico.org/name == "backend"
    destination:
      ports:
      - 80
  - action: Deny
EOF

echo "Application tier policies applied."
```

### Step 9: Test the Policies

```bash
echo "=== Testing Tiered Policies ==="
echo ""

# Test 1: Frontend -> API (should succeed)
echo -n "Test 1 - Frontend -> API: "
kubectl -n frontend exec frontend -- curl -s --max-time 3 -o /dev/null -w "%{http_code}" api.backend.svc.cluster.local 2>/dev/null && echo " PASS (allowed)" || echo " PASS (blocked as expected? Check output)"

# Test 2: Frontend -> DB (should be BLOCKED by application tier)
echo -n "Test 2 - Frontend -> DB (should be blocked): "
kubectl -n frontend exec frontend -- curl -s --max-time 3 -o /dev/null -w "%{http_code}" db.database.svc.cluster.local 2>/dev/null && echo " FAIL (should be blocked)" || echo " PASS (blocked)"

# Test 3: API -> DB (should succeed)
echo -n "Test 3 - API -> DB: "
kubectl -n backend exec api -- curl -s --max-time 3 -o /dev/null -w "%{http_code}" db.database.svc.cluster.local 2>/dev/null && echo " PASS (allowed)" || echo " CHECK (may need DNS egress)"

# Test 4: DB -> Frontend (should be BLOCKED)
echo -n "Test 4 - DB -> Frontend (should be blocked): "
kubectl -n database exec db -- curl -s --max-time 3 -o /dev/null -w "%{http_code}" frontend.frontend.svc.cluster.local 2>/dev/null && echo " FAIL (should be blocked)" || echo " PASS (blocked)"

echo ""
echo "=== Policy Verification ==="
kubectl get globalnetworkpolicies
kubectl get networkpolicies.p -A
```

### Step 10: Verify BGP Peering

```bash
# Check BGP status on all nodes
echo "=== BGP Status ==="
for node in $(kubectl get nodes -o name); do
  echo "--- $node ---"
  kubectl calico node status 2>/dev/null || echo "(Run calicoctl node status on the node)"
done

# View IP block allocation
echo ""
echo "=== IPAM Block Allocation ==="
kubectl calico ipam show --show-blocks 2>/dev/null || echo "(Run calicoctl ipam show --show-blocks)"

# View all Calico resources
echo ""
echo "=== Calico Resources ==="
kubectl get ippools -o wide
kubectl get bgpconfigurations
kubectl get felixconfigurations
```

### Success Criteria

- [ ] kind cluster with 4 nodes running Calico as CNI
- [ ] All nodes show Established BGP sessions (node-to-node mesh)
- [ ] Three policy tiers created: security, platform, application
- [ ] Frontend CAN reach API (port 80)
- [ ] Frontend CANNOT reach Database directly (blocked by application tier)
- [ ] API CAN reach Database (port 80)
- [ ] Database CANNOT initiate connections to Frontend (blocked)
- [ ] DNS resolution works in all namespaces (platform tier allows it)

### Bonus Challenge

Enable WireGuard encryption and verify it is active:

```bash
# Enable WireGuard
cat <<EOF | kubectl apply -f -
apiVersion: projectcalico.org/v3
kind: FelixConfiguration
metadata:
  name: default
spec:
  wireguardEnabled: true
EOF

# Wait for WireGuard to initialize (30-60 seconds)
sleep 30

# Verify on a calico-node pod
CALICO_POD=$(kubectl -n calico-system get pod -l k8s-app=calico-node -o name | head -1)
kubectl -n calico-system exec $CALICO_POD -- wg show 2>/dev/null || echo "WireGuard may not be available in kind (requires kernel support)"
```

---

## Cleanup

```bash
# Delete the lab cluster
kind delete cluster --name calico-lab

# Remove the kind config file
rm -f calico-kind-config.yaml
```

---

## Key Takeaways

1. **Calico is a platform, not just a CNI.** It handles routing (BGP), policy (L3-L7), encryption (WireGuard), and IPAM in a single integrated system.

2. **BGP gives you native routing.** No overlays, no encapsulation overhead, full integration with existing datacenter networking -- this is Calico's unique strength.

3. **Policy tiers solve the multi-team problem.** Security teams, platform teams, and developers can all write policies without stepping on each other.

4. **Typha is mandatory at scale.** Without it, the API server becomes the bottleneck. Deploy it before you hit 100 nodes, not after.

5. **eBPF and WireGuard are the future.** Together they give you kernel-level packet processing and encryption with no sidecars and minimal overhead.

6. **calicoctl is your best friend.** `calicoctl node status` and `calicoctl ipam show` will save you hours of debugging.

---

## Further Reading

- [Calico Documentation](https://docs.tigera.io/calico/latest/) - Official docs (comprehensive and well-maintained)
- [Calico GitHub Repository](https://github.com/projectcalico/calico) - Source code, issues, and releases
- [BGP Explained for Kubernetes Engineers](https://www.tigera.io/blog/what-is-bgp/) - Tigera blog post on BGP fundamentals
- [Calico eBPF Dataplane](https://docs.tigera.io/calico/latest/operations/ebpf/) - Full guide to enabling and operating eBPF mode
- [calicoctl Reference](https://docs.tigera.io/calico/latest/reference/calicoctl/) - CLI command reference
- [Calico Network Policy Guide](https://docs.tigera.io/calico/latest/network-policy/) - Comprehensive policy documentation
- *Kubernetes Networking* by James Strong and Vallery Lancey (O'Reilly) - Covers Calico in depth

---

## Next Module

Continue to [Module 5.1: Cilium](module-5.1-cilium.md) if you have not already, or return to the [Networking Toolkit README](README.md) to explore other networking modules.

---

*"BGP has been routing the internet since 1994. Calico brings that same battle-tested protocol to every pod in your cluster. There is no more proven foundation for production networking."*
