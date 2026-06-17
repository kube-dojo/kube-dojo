---
title: "Module 5.6: Project Calico - The Full-Stack Networking and Security Platform"
slug: platform/toolkits/infrastructure-networking/networking/module-5.6-calico
sidebar:
  order: 7
revision_pending: false
---
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

This module teaches you Calico from the ground up -- architecture, BGP, IPAM, policy, eBPF, WireGuard, and operations -- so that you understand every moving piece well enough to prevent incidents like this one.

**Prerequisites**:
- Kubernetes networking basics (Services, Pods, CNI)
- [Module 5.1: Cilium](../module-5.1-cilium/) (for comparison context)
- Basic understanding of BGP (helpful, not required -- we cover it here)
- [Security Principles Foundations](/platform/foundations/security-principles/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Calico with BGP-based networking for high-performance Kubernetes pod networking**
- **Configure Calico network policies using both Kubernetes and Calico-specific policy resources, including tiers and global policies**
- **Select the appropriate Calico dataplane (iptables, eBPF, or nftables) based on cluster requirements and kernel support**
- **Implement Calico's eBPF dataplane for improved performance and native kube-proxy replacement**
- **Integrate Calico with enterprise firewalls and network infrastructure using BGP peering, and choose the right Tigera edition for your organization**

---

## Why This Module Matters

Calico is a full networking and security platform that runs on everything from a single-node kind cluster to thousand-node bare-metal deployments peered with physical routers. While Cilium innovates with eBPF, Calico has been the production workhorse of Kubernetes networking since before Kubernetes was mainstream -- and it has evolved well beyond its iptables origins.

Here is what makes Calico different from every other CNI:

**It speaks BGP natively.** Calico does not require overlay networks. It assigns real, routable IP addresses to pods and distributes routes using the same protocol that powers the global internet. This means your pods can talk to physical servers, VMs, and legacy infrastructure without NAT, encapsulation, or tunnels. For organizations with existing network infrastructure, this capability transforms how Kubernetes integrates into the datacenter -- pods become first-class network citizens alongside bare-metal servers.

**It has the most comprehensive policy model in the ecosystem.** Standard Kubernetes NetworkPolicy is limited -- it cannot do host-level protection, DNS-based rules, application-layer filtering, or policy ordering across teams. Calico extends all of these with GlobalNetworkPolicy, HostEndpoint, policy tiers, and L7 rules that compose cleanly across security, platform, and application teams. No other CNI gives you policy tiers with explicit pass-through delegation.

**It scales to thousands of nodes.** With the Typha proxy layer, Calico handles clusters that would overwhelm the Kubernetes API server if every agent talked to it directly. The architecture was designed from the start for carrier-grade deployments where routing tables may contain tens of thousands of entries and where failure domains must be rigorously isolated.

**An important clarification on project governance.** Calico is a Tigera-stewarded open-source project. It is not a CNCF-hosted project -- it has no CNCF maturity tier (sandbox, incubating, or graduated). Tigera participates in the CNCF ecosystem as a member organization, but corporate membership is fundamentally different from donating a project to the CNCF for community governance. For comparison, Calico's peer Cilium is a CNCF Graduated project, meaning it has passed the CNCF's due diligence for project maturity, community health, and adoption. Calico follows a vendor-stewarded model where Tigera drives the roadmap and maintains the core repositories. Both models can produce excellent software -- Calico has been production-grade since 2015 and Cilium has thrived under CNCF governance since its graduation -- but the governance structure affects how features are prioritized, how the community participates in decision-making, and how the project responds to security vulnerabilities. Understanding this distinction matters when you are making a long-term platform commitment that may span five or more years of Kubernetes operations.

These four characteristics — BGP-native routing, comprehensive policy, architecture-level scalability, and clear (if vendor-stewarded) governance — converge on a single proposition: Calico treats Kubernetes networking as a first-class enterprise infrastructure concern, not as a container-specific hack layered on top of whatever your cloud provider gives you. Whether you are running on bare metal with spine-leaf fabrics, in a hybrid cloud spanning multiple providers, or in a regulated environment where security auditors need to see network segmentation at the IP level, Calico provides a consistent networking model that does not change when your infrastructure changes.

### Landscape snapshot — as of 2026-06

This changes fast; verify against vendor docs before relying on specifics. The current **Calico Open Source** release is **v3.32.0**, with the documentation site tracking version 3.32 as "latest." Version **3.29 introduced the nftables dataplane**, giving operators a third dataplane option alongside iptables and eBPF. Tigera ships three editions built on the open-source project: **Calico Open Source** (free, Apache 2.0 licensed), **Calico Enterprise** (self-managed commercial with additional security and compliance features), and **Calico Cloud** (SaaS offering with managed control plane and global visibility). All three share the same core dataplane and policy engine, differing in management capabilities, observability depth, and enterprise integrations. If you are reading this module more than six months after June 2026, check the Calico release page on GitHub and the Tigera documentation for the current version — the dataplane options and edition feature split are the most likely things to change between releases.

---

## CNI Fundamentals: Where Calico Fits

Before diving into Calico's architecture, it is worth understanding the problem that every CNI plugin solves. The Container Network Interface (CNI) specification defines a standard for how container runtimes configure network connectivity for containers. When the kubelet creates a pod, it calls a CNI plugin with three operations: ADD (attach a network interface to the pod's network namespace), DEL (tear it down), and CHECK (verify the configuration is still valid). The plugin receives a JSON configuration blob and is expected to return the result, including the assigned IP address, routes, and DNS configuration.

Under the hood, a pod's network lifecycle starts when the container runtime creates a new network namespace -- an isolated network stack with its own interfaces, routing table, and firewall rules. The runtime then creates a virtual Ethernet pair (veth): one end stays in the host's root namespace, and the other end is moved into the pod's namespace. At this point, the pod has a network interface but no IP address and no connectivity. The CNI plugin is invoked to assign an IP from its IPAM subsystem, configure routes so the pod can reach other pods and the outside world, and set up any necessary policy rules. The plugin is also responsible for cleaning up when the pod is deleted -- releasing the IP back to the pool and removing the veth pair. This entire ADD/DEL cycle happens in milliseconds on a healthy node, but when something goes wrong -- a misconfigured IP pool, a missing route, a policy that blocks the pod's own DNS requests -- the failure manifests as a pod that starts but cannot communicate, and the troubleshooting path leads directly into the CNI plugin's logs and configuration.

Calico implements this CNI contract with a distinctive approach: it does not create a network bridge per node. Instead, it programs the Linux kernel's routing table directly, treating every pod as a routable endpoint on a flat L3 network. When a pod is created, Calico's CNI plugin creates the veth pair, assigns an IP from the node's allocated block, and installs a route in the host's routing table pointing that pod's IP to the veth interface. Other nodes learn about this pod through BGP route distribution, so every node knows how to reach every pod without any overlay encapsulation. This design trades the simplicity of L2 bridging for the scalability and operability of L3 routing -- a tradeoff that pays enormous dividends when your cluster grows beyond a handful of nodes and when you need to integrate with existing network infrastructure. The absence of a per-node bridge also eliminates a common failure mode: bridge ARP table overflows that can cause "mysterious" connectivity failures in L2-based CNI plugins when pod density exceeds a few hundred per node.

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

Felix is the brain on every node. It watches the Kubernetes API (or Typha) for changes to pods, services, network policies, and Calico-specific resources. When something changes, Felix programs the dataplane -- either iptables rules, eBPF programs, or nftables rules -- to enforce the desired state. Felix is responsible for four distinct tasks on every reconciliation cycle: programming routes in the Linux routing table so the kernel knows how to reach pods on other nodes, creating ACLs that implement network policies in whichever dataplane is active, configuring tunnel interfaces when overlay mode (IPIP or VXLAN) is needed, and reporting node health and connectivity status back to the Calico datastore.

```bash
# See Felix's logs on a node
kubectl logs -n calico-system -l k8s-app=calico-node -c calico-node | grep Felix

# Check Felix's configuration
kubectl get felixconfiguration default -o yaml
```

Felix is remarkably efficient in how it handles rapid change. It uses a batching algorithm that collects changes over a short window (configurable, typically 2-10 seconds) and applies them as a single atomic update. This prevents the "iptables thrashing" problem where rapid pod creation would cause rule table rebuilds dozens of times per second. Instead of one expensive operation per change, Felix accumulates all pending changes and replays them in one efficient batch.

#### BIRD: The BGP Daemon (Per-Node)

BIRD (BIRD Internet Routing Daemon) runs on every node and speaks BGP with other nodes (or external routers). Its job is simple but critical: tell the rest of the network which pod CIDRs live on this node. When a pod is created on Node A with IP 10.244.1.15, BIRD on Node A announces to all its BGP peers: "To reach 10.244.1.0/26, send traffic to me." Every other node's BIRD daemon receives this announcement and programs a route into its local routing table.

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

**Important**: When using Calico's eBPF dataplane, BIRD is still used for route distribution. eBPF replaces iptables for policy enforcement and Service handling, not BGP route propagation. The routing plane and the dataplane are independent concerns, and Calico keeps them cleanly separated.

#### confd: The Configuration Generator

confd watches the Calico datastore for BGP configuration changes -- peers, ASN settings, route reflector configurations -- and generates BIRD configuration files in BIRD's native syntax. When you create a BGPPeer CRD, confd translates that declarative resource into imperative BIRD configuration and triggers BIRD to reload. You rarely interact with confd directly, but it is the glue between Calico's declarative Kubernetes-native CRDs and BIRD's imperative configuration files. Without confd, you would need to write BIRD configuration by hand and restart BIRD manually whenever the topology changes -- a fragile approach that the opening incident demonstrates is not just inconvenient but dangerous.

#### Typha: The Scaling Proxy

On a 50-node cluster, every Felix instance opens a watch connection to the Kubernetes API server. That is 50 watch connections -- manageable. On a 500-node cluster, however, 500 simultaneous watches would overwhelm the API server. Typha sits between Felix and the API server, acting as a fan-out proxy. A small number of Typha instances (typically 3-5) maintain watch connections to the API server, then fan out updates to all the Felix instances on their assigned nodes. This reduces API server load from O(n) to O(k), where k is the number of Typha replicas.

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

The Tigera operator automatically deploys Typha when needed, scaling the replica count based on node count. For clusters over 200 nodes, Typha is not optional -- it is required for stability, and production deployments should monitor Typha's own resource consumption since a misbehaving Typha instance can delay policy propagation across the cluster.

#### Calico API Server

The Calico API server extends the Kubernetes API with Calico-specific resource types. It handles validation and admission control for resources including `IPPool`, `IPReservation`, `BGPPeer`, `BGPConfiguration`, `FelixConfiguration`, `GlobalNetworkPolicy`, `NetworkPolicy` (Calico-flavored), `HostEndpoint`, `GlobalNetworkSet`, and `CalicoNodeStatus`. This means you can manage Calico entirely through `kubectl` -- no separate CLI required, though `calicoctl` still exists and is particularly useful for diagnostics like `calicoctl node status` and `calicoctl ipam show`.

---

## Part 2: BGP Deep Dive

BGP (Border Gateway Protocol) is the protocol that holds the internet together. Every ISP, every cloud provider, every content delivery network uses BGP to exchange routing information. Calico brings this same proven, battle-tested protocol to Kubernetes networking, and understanding its fundamentals is essential for any operator running Calico on bare metal or in hybrid environments.

### Why BGP Matters for Kubernetes

Most CNI plugins use **overlay networks** -- they encapsulate pod traffic inside VXLAN or Geneve tunnels to cross node boundaries. This approach works reliably, but it imposes real costs: extra headers consume 50 bytes per packet for VXLAN, encapsulation and decapsulation consume CPU cycles on every node, debugging becomes harder because tcpdump shows tunnel packets instead of real application traffic, and the effective MTU drops from 1500 to 1450, which can cause subtle TCP performance issues with path MTU discovery. Calico's BGP mode uses **native routing** instead. Pod IPs are real, routable addresses on the network. No encapsulation, no tunnels, no overhead. Packets go directly from one node to another using standard Linux routing, and a network engineer with a packet capture can see exactly which pod is talking to which other pod.

### Node-to-Node Mesh (Default)

Out of the box, Calico configures a **full mesh** BGP topology. Every node peers with every other node. This is simple, requires zero configuration, and works well for small to medium clusters. But the number of BGP sessions grows quadratically: N nodes produce N×(N−1)/2 sessions. Four nodes means 6 sessions, which is trivial. Twenty nodes means 190 sessions, which is manageable. Fifty nodes means 1,225 sessions, which starts to strain BIRD's memory and CPU. One hundred nodes means 4,950 sessions, which is well past the point where the full mesh becomes a liability rather than an asset.

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

Above approximately 50 nodes, the full mesh becomes a scaling bottleneck, not because BGP itself cannot handle it but because every node must maintain a TCP session with every other node and process every route update from every peer. This is where route reflectors enter the picture.

### Route Reflectors (50+ Nodes)

Instead of every node peering with every other node, you designate a few nodes as **route reflectors**. All other nodes (called clients) peer only with the route reflectors. The reflectors forward routes between their clients, drastically reducing the session count. In a 100-node cluster with 3 route reflectors, the session count drops from 4,950 to approximately 303 -- a 94% reduction. For redundancy, always deploy at least two route reflectors so that a single reflector failure does not partition the BGP topology.

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

First, disable the full mesh so nodes stop peering with each other directly:

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

Label the nodes that will serve as route reflectors. These should be nodes with stable networking and sufficient CPU and memory, since they will process every route in the cluster:

```bash
# Designate specific nodes as route reflectors
kubectl label node worker-01 calico-route-reflector=true
kubectl label node worker-02 calico-route-reflector=true
kubectl label node worker-03 calico-route-reflector=true
```

Configure the route reflector nodes with a cluster ID so that BGP can correctly identify which reflector originated a route and prevent loops when multiple reflectors peer with each other:

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

Create BGPPeer resources so non-reflector nodes peer with reflectors, and reflectors peer with each other:

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
---
apiVersion: projectcalico.org/v3
kind: BGPPeer
metadata:
  name: rr-to-rr-mesh
spec:
  nodeSelector: has(calico-route-reflector)
  peerSelector: has(calico-route-reflector)
```

### Peering with Physical Infrastructure

This is where Calico truly distinguishes itself in enterprise environments. You can peer Calico nodes directly with your datacenter's Top-of-Rack (ToR) switches, spine switches, or even external routers. This gives pod IPs full reachability across your physical network without any NAT or tunneling -- a pod can be reached from outside the cluster at its native IP address, subject only to policy rules.

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

Configure peering with a specific ToR switch using a node selector so that only nodes in the correct rack establish peering with that rack's switch:

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

The BGPConfiguration resource controls global BGP behavior, including whether to advertise Service ClusterIPs, external IPs, and LoadBalancer IPs via BGP -- a feature that lets external routers reach Kubernetes Services without a separate load balancer:

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

In BGP, every autonomous system (AS) needs a unique number. Calico supports both private ASNs in the range 64512-65534 (16-bit) or 4200000000-4294967294 (32-bit) for internal cluster networking, and per-node ASN overrides for deployments where nodes span multiple racks or datacenters with different AS assignments:

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

Calico's IPAM is more sophisticated than most CNI plugins. It pre-allocates blocks of IPs to nodes, supports multiple pools, and handles edge cases like IP exhaustion gracefully through borrowing. Understanding how Calico manages IP addresses is essential for capacity planning and for troubleshooting connectivity problems that trace back to IP pool configuration.

### IP Pools

An IP Pool defines a range of IP addresses available for pod allocation. The pool configuration controls encapsulation mode, NAT behavior, block size, and which nodes are eligible to use the pool:

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

The choice of encapsulation mode has significant implications for performance, debuggability, and compatibility with your network infrastructure. The fundamental question is whether your physical network can route pod CIDRs natively. If it can, you should use no encapsulation at all -- this gives you the best performance and the most transparent networking. If it cannot, you need an overlay, and the choice between IPIP and VXLAN depends on your network's capabilities.

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

Calico does not assign IPs one at a time. Instead, it carves the IP pool into **blocks** (default: /26 = 64 addresses) and assigns entire blocks to nodes. Pods on a node get IPs from that node's block. Why blocks? **Route aggregation.** Instead of advertising one route per pod (potentially thousands), each node advertises one route per block. A node with 50 pods might only need one /26 block -- a single route entry. This design is what makes Calico's BGP-based approach scale: the routing table size is proportional to the number of blocks, not the number of pods.

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

You can assign different IP pools to different namespaces, which is powerful for multi-tenancy, compliance, or network segmentation. All pods in a namespace receive IPs from a dedicated CIDR range, making firewall rules and audit controls dramatically simpler:

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

Every pod in the `finance` namespace will now get an IP from 10.245.0.0/24. This makes firewall rules trivial: "All traffic from 10.245.0.0/24 is the finance team." Compliance auditors can verify network segmentation without understanding Kubernetes internals.

### IP Borrowing

What happens when a node's block is full but there are free IPs in other blocks? Calico supports **IP borrowing** -- a node can allocate individual IPs from blocks that belong to other nodes, if those blocks have spare capacity. This is a safety mechanism that prevents pod scheduling failures due to IP exhaustion on a single node, even when the overall pool has plenty of capacity. The trade-off is slightly less efficient routing: the borrowed IP creates an additional /32 host route instead of being covered by the block's aggregate route.

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

Calico's network policy engine is the most feature-rich in the Kubernetes ecosystem. It supports everything from basic Kubernetes NetworkPolicy to advanced features that no other CNI offers, including policy tiers, host endpoint protection, and DNS-based egress rules.

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

However, standard Kubernetes NetworkPolicy has significant limitations that become apparent as soon as you move beyond basic allow-listing: it cannot apply to host traffic (only pod traffic), it has no explicit deny rules, policies are namespace-scoped with no global baseline capability, all matching policies are OR'd together with no ordering or priority, there is no L7 filtering by HTTP method or path, and there is no ability to write rules based on DNS domain names rather than IP addresses. Each of these limitations makes sense for the minimal viable NetworkPolicy API, but each becomes a blocker in production environments with multiple teams and compliance requirements.

### Calico NetworkPolicy (Namespace-Scoped)

Calico's own NetworkPolicy CRD extends the standard with all the missing features, adding explicit Allow and Deny actions, egress rules alongside ingress, and richer selector syntax:

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

GlobalNetworkPolicy applies across all namespaces, which is essential for platform teams that need cluster-wide security baselines that no individual team can override. A typical pattern is a global egress policy that blocks all outbound internet access by default, then allows specific destinations:

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

Unlike any other CNI, Calico can protect the host itself -- not just pods. HostEndpoints let you apply policies to the node's physical interfaces, treating the Kubernetes worker as a managed network endpoint with the same policy engine that governs pod traffic:

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

Now you can write policies for the host that allow SSH only from a bastion, restrict which IP ranges can reach the kubelet, and ensure that host-level rules compose cleanly with pod-level policies:

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

This is one of Calico's most powerful and distinctive features. Policy tiers let different teams manage policies at different priority levels, with explicit pass-through semantics that prevent teams from accidentally blocking each other. The security team can enforce compliance rules at the highest tier, the platform team can define infrastructure-level rules in the middle, and application teams can write their own allow-list policies at the lowest tier -- all without coordination or conflict.

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

Create a tier and assign a policy to it. The **Pass** action is the key mechanism: it means "I have no opinion on this traffic -- let the next tier decide." This is how tiers compose without stepping on each other:

```yaml
apiVersion: projectcalico.org/v3
kind: Tier
metadata:
  name: security
spec:
  order: 100
---
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

### Application Layer Policy (L7)

Calico can integrate with Envoy to provide L7 (HTTP) policy enforcement, allowing rules that filter by HTTP method and URL path:

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

L7 policies require the Envoy proxy deployed as a DaemonSet or sidecar, which adds some operational overhead but enables powerful HTTP-aware security that goes well beyond what IP-and-port rules can express.

### DNS-Based Policies

Allow pods to reach specific domains without knowing their IP addresses. Calico intercepts DNS responses and dynamically creates IP-based rules for the resolved addresses, transparently and without application changes:

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

---

## Part 5: eBPF Dataplane

Calico's eBPF dataplane replaces iptables for packet processing, delivering better performance and more consistent behavior at scale. Instead of traversing linear chains of iptables rules, eBPF programs use hash maps for O(1) lookups regardless of how many Services or policies exist in the cluster.

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

### Performance Characteristics

The key advantage of eBPF is **constant-time lookups**. With iptables, every packet traverses a chain of rules sequentially -- more Services means more rules means higher and higher latency. With eBPF hash maps, lookup time is constant regardless of table size. The following figures come from Calico project benchmarks and represent illustrative orders of magnitude; your specific results will depend on hardware, kernel version, and workload patterns.

| Metric | iptables | eBPF | Improvement |
|--------|----------|------|-------------|
| **Connections/sec** (1000 Services) | 18,500 | 26,200 | +42% |
| **P99 latency** (1000 Services) | 4.2ms | 1.8ms | -57% |
| **CPU per node** (idle) | 2.1% | 1.4% | -33% |
| **Rule update time** (adding a Service) | 120ms | 8ms | -93% |
| **Latency scaling** (10→10,000 Services) | Linear increase | Constant | O(1) vs O(n) |

### Enabling eBPF Mode

Using the Tigera operator, you enable the eBPF dataplane with a single field in the Installation resource. Once eBPF is active, you can remove kube-proxy entirely since Calico's eBPF programs handle Service routing natively:

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

```bash
# Disable kube-proxy (Calico eBPF handles Services natively)
kubectl patch ds -n kube-system kube-proxy -p \
  '{"spec":{"template":{"spec":{"nodeSelector":{"non-calico": "true"}}}}}'

# Verify eBPF mode is active
kubectl get felixconfiguration default -o yaml | grep -i bpf
# bpfEnabled: true
```

### eBPF Limitations

Be aware of these constraints before enabling eBPF mode. It requires Linux kernel 5.3 or newer, with 5.8 or later recommended for full feature support. Some HostEndpoint features are limited or unavailable in eBPF mode (check the release notes for your specific version). eBPF mode supports VXLAN encapsulation but not IPIP, so use VXLAN or no encapsulation. Traditional iptables debugging tools like `iptables-save` and `conntrack` do not show eBPF decisions -- instead, you use Calico's built-in BPF diagnostic commands:

```bash
# Debug eBPF dataplane
# View BPF program status
kubectl exec -n calico-system calico-node-xxxxx -- calico-node -bpf tc dump eth0

# View BPF conntrack table
kubectl exec -n calico-system calico-node-xxxxx -- calico-node -bpf conntrack dump

# View BPF routes
kubectl exec -n calico-system calico-node-xxxxx -- calico-node -bpf routes dump
```

### The nftables Dataplane (v3.29+)

Starting with Calico v3.29, a third dataplane option became available: **nftables**. The nftables dataplane uses the modern Linux kernel nftables subsystem, which replaces the legacy iptables framework with a more efficient, unified API. The nftables dataplane sits between iptables and eBPF in the performance spectrum: it outperforms iptables by avoiding the linear rule-chain traversal that plagues large iptables rulesets, but it does not match eBPF's O(1) hash-map lookups. Its primary value is for operators who cannot meet eBPF's kernel version requirements (they may be on kernels between 4.x and 5.3, or on distributions that ship without eBPF support) but still want better performance and maintainability than iptables provides. Configuration is straightforward: set `linuxDataplane: NFTables` in the Installation resource. The nftables dataplane supports the same policy model as iptables, making it a drop-in upgrade path for clusters that have outgrown iptables but cannot yet adopt eBPF.

---

## Part 6: WireGuard Encryption

Calico can encrypt all pod-to-pod traffic using WireGuard, a modern VPN protocol built into the Linux kernel. No certificates, no PKI infrastructure, no sidecars -- just kernel-level encryption with minimal overhead.

### Why WireGuard?

Traditional options for pod traffic encryption each carry significant costs. Service mesh mTLS adds a sidecar to every pod, consuming 50-100MB of memory per pod and requiring complex certificate management infrastructure. IPsec is heavyweight, configuration-intensive, and CPU-hungry. WireGuard, by contrast, runs in the kernel with approximately 3-5% CPU overhead and requires zero per-pod configuration. WireGuard encrypts traffic between nodes transparently -- pods do not know encryption is happening because it occurs at the node level, below the pod network stack. Every node generates a WireGuard keypair, exchanges keys through the Calico datastore, and establishes encrypted tunnels to every peer automatically.

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

That is the entire configuration. No per-node setup, no certificate rotation, no sidecars:

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

WireGuard is fast because it runs in the kernel and uses modern, efficient cryptography (ChaCha20-Poly1305):

| Metric | Without WireGuard | With WireGuard | Overhead |
|--------|-------------------|----------------|----------|
| **Throughput** (TCP) | 9.4 Gbps | 8.9 Gbps | ~5% |
| **Latency** (P50) | 0.12ms | 0.14ms | +0.02ms |
| **CPU per node** | 1.4% | 2.1% | +0.7% |
| **MTU overhead** | 0 bytes | 60 bytes | Reduces effective MTU |

For most workloads, WireGuard overhead is negligible. The main consideration is the MTU reduction -- ensure your pod MTU accounts for the WireGuard header, typically set to 1440 when using WireGuard without other encapsulation.

### WireGuard + eBPF

WireGuard works with both iptables and eBPF dataplanes. When combined with eBPF, you get kernel-level packet processing (eBPF), kernel-level encryption (WireGuard), no kube-proxy, no sidecars, and no iptables. This is arguably the most streamlined Kubernetes networking stack possible -- every critical path runs in the kernel with minimal userspace involvement.

---

## Part 7: Installation and Operations

### Tigera Operator (Recommended)

The Tigera operator is the recommended installation method. It manages the Calico lifecycle, handles upgrades, and ensures components are configured correctly:

```bash
# Install the Tigera operator
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.32.0/manifests/tigera-operator.yaml

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

For environments where operators are not preferred, Calico also supports direct manifest installation, though this gives you less lifecycle management:

```bash
# Direct manifest installation (includes CRDs, DaemonSets, Deployments)
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.32.0/manifests/calico.yaml
```

### calicoctl CLI Tool

While Calico resources can be managed with `kubectl`, the `calicoctl` CLI provides additional diagnostics that are essential for troubleshooting:

```bash
# Install calicoctl
curl -L https://github.com/projectcalico/calico/releases/download/v3.32.0/calicoctl-linux-amd64 -o calicoctl
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

### Editions: Open Source, Enterprise, and Cloud

Tigera ships three editions built on the same core open-source project, and understanding the differences is essential when planning a production deployment. **Calico Open Source** is the free, Apache 2.0 licensed project available on GitHub. It includes the full dataplane (iptables, eBPF, nftables), BGP routing, WireGuard encryption, and the complete policy model with tiers. This is what most clusters run, and it is fully production-grade on its own. The Open Source edition is where all dataplane innovation happens first -- eBPF support, nftables, and WireGuard all landed in Open Source before becoming available in the commercial editions.

**Calico Enterprise** adds self-managed commercial features on top of the same dataplane: a web console called Calico Whisker for policy visualization and management, compliance reporting with audit-ready output, SIEM integrations for security operations teams, multi-cluster management, and enterprise support with defined SLAs. Enterprise is deployed on your own infrastructure, so you retain full control of the data plane while gaining the operational tooling that larger organizations require.

**Calico Cloud** is a SaaS offering that adds a managed control plane with global visibility across all connected clusters, dynamic threat detection and scoring, and a free tier for individual clusters running Calico Open Source 3.30 or higher. The managed control plane reduces the operational burden of running Calico API servers and Typha at scale, while providing a single pane of glass for policy, compliance, and observability across your entire fleet. All three editions share the same dataplane and policy engine, so policies you develop on the open-source edition work identically on Enterprise and Cloud, and a cluster can be upgraded from Open Source to Enterprise or connected to Cloud without recreating any policy resources.

### Observability

Calico Open Source provides basic flow logs through the calico-node containers, and `calicoctl` gives you node-level diagnostics including BGP session status, IPAM block allocation, and policy evaluation. For deeper observability, you can inspect BIRD's BGP logs to trace route propagation events, Felix's per-node policy programming logs to understand why a specific rule is or is not being applied to a pod, and the IPAM state to audit IP utilization across blocks. These logs are structured and can be forwarded to your existing logging infrastructure for correlation with application and infrastructure events. For teams needing richer observability, Calico Enterprise and Cloud add flow visualizers that show traffic patterns as interactive service graphs, dynamic threat detection that scores flows against known-bad indicators, and integration with external logging and SIEM platforms for centralized security operations. The open-source edition gives you enough signal to troubleshoot most issues; the commercial editions give you the dashboards and alerting that make proactive monitoring practical at scale.

---

## Part 8: Scaling Calico to 1,000+ Nodes

### Typha Deployment

For large clusters, Typha is essential. The Tigera operator handles this automatically, but understanding the resource implications and failure modes will help you configure it correctly. Typha acts as a fan-out proxy: it maintains a small number of watch connections to the Kubernetes API server and relays updates to all Felix instances assigned to it. This means Typha's memory consumption scales with the number of connected Felix instances and the volume of watched resources (pods, network policies, IP pools), not with the raw node count. In practice, a single Typha replica can comfortably serve 200-300 Felix instances, and the operator deploys additional replicas as the cluster grows. Each Typha replica is stateless, so losing one simply means its Felix instances reconnect to another replica — there is no data loss and no manual intervention required. The operational guidelines below are starting points; you should monitor Typha's own CPU and memory usage and adjust replica counts based on actual utilization rather than blindly following a static table.

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

Calico stores all its state in the Kubernetes API (backed by etcd). At scale, this means thousands of WorkloadEndpoint objects (one per pod), high watch connection counts mitigated by Typha, and update storms during pod churn that Typha batches. Recommendations for large clusters: use SSDs for etcd storage (mandatory above 500 nodes), monitor `etcd_disk_wal_fsync_duration_seconds` and keep it below 10ms, consider dedicated etcd nodes rather than co-locating with control plane workloads, and enable etcd compaction and defragmentation on a regular schedule.

---

## CNI / Dataplane Rosetta

This table compares durable capabilities across three commonly deployed CNI plugins on Kubernetes. The capabilities listed are design characteristics that change slowly; implementation details (kernel version requirements, exact performance numbers, specific feature flags) are volatile and should be checked against vendor documentation.

| Capability | **Calico** | **Cilium** | **Flannel** |
|---|---|---|---|
| **Routing model** | BGP native L3 routing (optionally VXLAN/IPIP overlay) | Overlay (VXLAN/Geneve) with eBPF-based routing | VXLAN overlay only |
| **Policy model** | K8s NetworkPolicy + extended CRDs + tiers + host endpoints | K8s NetworkPolicy + CiliumNetworkPolicy + DNS-based rules | None (requires Calico or Cilium add-on) |
| **Dataplanes** | iptables, eBPF, nftables, Windows, VPP | eBPF (primary), iptables (fallback) | iptables only |
| **No-kube-proxy** | Yes (eBPF and nftables modes) | Yes (eBPF mode, default) | No |
| **Encryption** | WireGuard (node-to-node) | WireGuard or IPsec (node-to-node) | None |
| **Host protection** | Yes (HostEndpoint CRD with policy tiers) | Yes (CiliumHostPolicy) | No |
| **Observability** | Basic flow logs; richer in Enterprise/Cloud editions | Hubble (advanced flow observability, service map) | None |
| **Governance** | Tigera-stewarded (vendor-led) | CNCF Graduated (community-governed) | CNCF Graduated |
| **Best fit** | BGP integration, bare-metal, enterprise policy tiers, hybrid cloud | eBPF-first stack, Hubble observability, sidecar-free service mesh | Simple overlay for small to medium clusters |

No single CNI is "best" -- the right choice depends on your existing network infrastructure, team expertise, security requirements, and observability needs. Calico's unique strengths are BGP-native routing and policy tiers; Cilium's are eBPF-native observability and the sidecar-free mesh; Flannel's is operational simplicity. Many organizations run Calico on bare metal and Cilium in cloud environments within the same company, choosing the right tool for each deployment context.

---

## Patterns and Anti-Patterns

### Patterns

1. **GitOps-managed BGPPeer resources.** Store all BGP peer configurations as version-controlled YAML and require pull request review for any ASN or peer IP change. The opening incident of this module -- a $180,000 outage from a single wrong ASN -- would have been caught in code review. Use `nodeSelector` and `peerSelector` to target peer configurations to specific racks or availability zones rather than maintaining per-node BGPPeer resources.

2. **Three-tier policy architecture.** Deploy three tiers in every cluster: a `security` tier owned by the security team for compliance rules, a `platform` tier owned by the platform team for infrastructure policies like DNS and monitoring access, and an `application` tier where development teams write their own allow-list policies. End the security and platform tiers with `action: Pass` rules so unmatched traffic delegates to the next tier. This pattern eliminates the coordination overhead of a single shared policy namespace.

3. **Route reflectors before 50 nodes.** Do not wait until the full mesh becomes painful. Deploy two or three route reflector nodes when your cluster crosses 50 worker nodes. The migration is straightforward -- disable `nodeToNodeMeshEnabled`, label the reflector nodes, and create the BGPPeer resources. Doing this proactively avoids an emergency migration when BIRD memory exhaustion starts causing session flaps.

4. **Per-namespace IP pools for compliance segmentation.** Assign dedicated IP pools to namespaces that fall under specific regulatory regimes (PCI-DSS, HIPAA, SOX) so that network-level firewall rules and audit tools can distinguish compliance-scoped traffic from general workload traffic without understanding Kubernetes internals. The IP address becomes the compliance boundary.

### Anti-Patterns

1. **Disabling `natOutgoing` without return routes.** If your pod CIDR is not routable from your infrastructure (common in cloud environments where pod IPs are private and unknown to the VPC router), pods will be unable to reach external services because the return traffic has no path back to the source pod. The pod sends a packet to an external IP, the packet reaches the destination, but the destination's reply is routed to a black hole because no route exists for the pod's source IP. This manifests as pods that can resolve DNS but cannot establish TCP connections to external endpoints — a classic troubleshooting dead end. Always set `natOutgoing: true` on every IPPool unless you have explicit return routes for pod CIDRs configured on your physical or cloud network infrastructure and have verified those routes end-to-end.

2. **Enabling eBPF on unsupported kernels.** If the kernel does not meet the minimum version (5.3, ideally 5.8+ for full feature support), Felix may crash on startup with a BPF program load error or silently fall back to iptables with only partial functionality enabled, leaving you with a mix of behaviors that is nearly impossible to reason about. Always run `calicoctl node checksystem` before enabling a new dataplane, verify the kernel version with `uname -r` on every node (not just the control plane), and test in a staging cluster before promoting to production.

3. **Using `action: Deny` without `action: Pass` as the last rule in a tier.** A tier that ends with an explicit Deny as its final rule silently blocks all unmatched traffic from ever reaching lower tiers, making application-level policies completely ineffective — your developers' carefully crafted allow-list policies simply never get evaluated. Always end non-terminal tiers with `action: Pass` as the final rule to delegate unmatched traffic downward to the next tier. Reserve `action: Deny` as a terminal rule for the last tier only, where there is no lower tier to delegate to.

4. **Allowing IP pool CIDR overlap.** If two IPPools share overlapping CIDR ranges, Calico's IPAM may assign the same IP address to two different pods on different nodes, causing intermittent and nearly impossible-to-diagnose connectivity failures — one pod works, the other gets TCP RSTs, and the failure moves when either pod restarts. Audit all IPPool CIDRs regularly with `calicoctl get ippool -o yaml` and ensure they do not overlap with each other or with the Service CIDR, node CIDR, or any other routable prefix in your network.

### Decision Framework: Choosing Your Calico Stack

When designing a Calico deployment, work through these questions in order. Each choice constrains the options available for subsequent decisions, so resist the temptation to jump ahead:

1. **Networking model**: Can your physical network route pod CIDRs? If yes, use BGP with no encapsulation for maximum performance and the ability to peer directly with your datacenter's spine-leaf fabric. If no, use VXLAN -- it is preferred over IPIP because it supports IPv6 and traverses NAT devices more reliably. The CrossSubnet variants give you the best of both worlds when nodes span subnets: encapsulation only when needed.

2. **Dataplane**: Are you on kernel 5.8+ and comfortable with eBPF debugging? Use the eBPF dataplane and remove kube-proxy entirely for consistent, O(1) Service routing. On kernels between 4.x and 5.3 where eBPF is not available? Use the nftables dataplane (v3.29+) for better performance and maintainability than iptables. On older kernels or in environments where your team needs traditional debugging tools? Use iptables.

3. **Policy model**: Do you have multiple teams needing independent policy management? Deploy policy tiers from day one, even if you start with only the platform tier. Adding the security tier later is a single CRD operation -- setting up tiers proactively costs nothing and prevents a migration project when compliance requirements appear. End every non-terminal tier with `action: Pass` to ensure unmatched traffic delegates properly.

4. **Encryption**: Do you have a compliance requirement for encryption in transit? Enable WireGuard. It has negligible overhead, zero per-pod configuration, and encrypts all node-to-node traffic automatically. For per-service identity with cryptographic SPIFFE certificates, you can layer a service mesh on top, but for blanket compliance encryption, WireGuard alone is sufficient and dramatically simpler to operate.

5. **Edition**: Are you running a single cluster with basic networking and policy needs? Calico Open Source is sufficient, and it is fully production-grade. Do you need multi-cluster visibility, compliance reporting with audit trails, a web console for policy management, or enterprise support with SLAs? Evaluate Calico Enterprise. Are you operating a SaaS platform and want to offload the control plane management? Calico Cloud provides a managed experience with a free tier for qualifying clusters running Calico Open Source 3.30 or higher.

---

## Did You Know?

1. **Calico was born from carrier-grade telecom routing.** Tigera was founded in 2015 by engineers from Metaswitch Networks, a telecommunications company that built carrier-grade routing software for phone networks. The BGP expertise that routes phone calls across continents is the same technology that now routes Kubernetes pod traffic. This is not a CNI built by generalists learning networking -- it was built by networking experts learning containers.

2. **Calico powers over 8 million nodes across 166 countries.** It is deployed at major banks, telecoms, government agencies, and three of the top five cloud providers. When AWS launched EKS, Calico was one of the first supported CNI options alongside AWS's own VPC CNI. This breadth of deployment means Calico has been tested against an extraordinary range of network topologies and failure modes.

3. **Calico's eBPF dataplane can replace kube-proxy entirely**, eliminating iptables overhead for Service routing just as Cilium does. In benchmarks, Calico's eBPF mode maintains consistent latency regardless of the number of Services in the cluster, while iptables latency grows linearly with the rule count.

4. **Project Calico is named after a calico cat.** The project's creators wanted a name that was friendly and memorable, and the calico cat's distinctive patches of different colors inspired the metaphor of networking patches -- connecting different network segments into one cohesive fabric. The project mascot, a calico cat, appears throughout the documentation and community materials.

---

## Common Mistakes

| # | Mistake | What Happens | How to Fix |
|---|---------|-------------|------------|
| 1 | **Using full mesh BGP on 100+ nodes** | Thousands of BGP sessions, BIRD memory exhaustion, slow convergence | Switch to route reflectors; disable `nodeToNodeMeshEnabled` and deploy 2-3 RR nodes |
| 2 | **Wrong ASN in BGP peer config** | Asymmetric routing, session flapping, intermittent packet loss | Manage BGPPeer CRDs in Git; require PR review for all BGP changes; verify with `calicoctl node status` |
| 3 | **Forgetting natOutgoing on IP pools** | Pods cannot reach the internet; DNS to external domains fails silently | Set `natOutgoing: true` on the IPPool unless you have explicit return routes for pod CIDRs |
| 4 | **Enabling eBPF without checking kernel version** | Felix crashes or falls back to iptables silently; partial functionality | Verify kernel 5.3+ with `uname -r`; check `calicoctl node checksystem` before enabling |
| 5 | **Not deploying Typha on large clusters** | API server overwhelmed by watch connections; Felix instances disconnected; policies not applied | Deploy Typha when cluster exceeds 100 nodes; the Tigera operator does this automatically |
| 6 | **Overlapping IP pools** | IPAM assigns the same IP to two pods; conflict causes intermittent connectivity failures | Audit all IPPool CIDRs; ensure they do not overlap with each other or with Service/node CIDRs |
| 7 | **Using `action: Deny` without `action: Pass`** in tiered policies | Traffic blocked by a higher-tier policy never reaches lower tiers; application policies silently ignored | Use `action: Pass` as the final rule in a tier to delegate unmatched traffic to the next tier |
| 8 | **Not setting MTU correctly with encapsulation** | Packet fragmentation, degraded throughput, intermittent TCP connection hangs | Set MTU to 1450 for VXLAN, 1480 for IPIP, 1440 for WireGuard + VXLAN; verify with `ping -s 1472 -M do <pod-ip>` |

---

## Quiz

Test your understanding of Calico's architecture, BGP, policy model, and operational features.

<details>
<summary><strong>Question 1</strong>: What are the three main components inside the calico/node container, and what does each one do?</summary>

**Answer:**

1. **Felix** -- The policy engine. Watches the Calico datastore (via API server or Typha) for changes and programs the Linux dataplane (iptables rules, eBPF programs, or nftables rules) to enforce network policy, routes, and IPAM.

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

**Answer:** WireGuard encryption in Calico operates fundamentally differently from service mesh mTLS, and understanding their tradeoffs helps you choose the right tool for each compliance and security requirement.

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

**Use both** when compliance requires node-level encryption AND you need service-level identity. This combination is common in regulated financial environments where PCI-DSS or equivalent frameworks demand encryption at every layer: WireGuard covers the network layer transparently, and the service mesh provides cryptographic workload identity for audit purposes.

</details>

<details>
<summary><strong>Question 7</strong>: You configure a BGPPeer with the wrong ASN and traffic starts dropping. How would you diagnose this issue step by step?</summary>

**Answer:**

1. **Check BGP session status** with `calicoctl node status`. Look for sessions in "Connect" or "Active" state (not "Established"). Flapping sessions will alternate between states.

2. **Check BIRD logs** with `kubectl logs -n calico-system -l k8s-app=calico-node -c calico-node | grep -i bgp`. Look for "BGP Error" or "Notification" messages indicating ASN mismatch.

3. **Verify the BGPPeer configuration** with `calicoctl get bgppeer -o yaml`. Cross-reference the `asNumber` with the actual ASN configured on the peer device.

4. **Check routing tables** with `ip route | grep bird`. Missing or incorrect routes indicate BGP is not exchanging information correctly.

5. **Fix**: Update the BGPPeer CRD with the correct ASN. BGP sessions will re-establish within the hold timer interval (default 90 seconds).

</details>

<details>
<summary><strong>Question 8</strong>: Explain how Calico's per-namespace IP pool assignment works and describe a real compliance scenario where it solves a genuine operational problem.</summary>

**Answer:**

You annotate a namespace with `cni.projectcalico.org/ipv4pools: '["pool-name"]'`, and all pods created in that namespace receive IPs from the specified IPPool.

**Use case: PCI-DSS compliance for a payment service.** A company runs a mixed Kubernetes cluster where the payment processing service must comply with PCI-DSS, which requires network segmentation -- the cardholder data environment (CDE) must be isolated and auditable. By creating a dedicated IP pool (e.g., 10.245.0.0/24) for the `payment` namespace, all payment pods get IPs from a known, documented range. Firewall rules on physical infrastructure can specifically allow or deny 10.245.0.0/24. Network flow logs can be audited by CIDR range. Compliance auditors can verify segmentation without understanding Kubernetes internals. Without per-namespace pools, pod IPs are scattered across the global pool, making network-level segmentation much harder.

</details>

---

Now that you understand Calico's architecture, policy model, dataplanes, and operational considerations, it is time to put that knowledge into practice. The following hands-on exercise walks you through deploying Calico on a local kind cluster, creating a three-tier policy architecture, and verifying that the policies correctly enforce the intended traffic flows. You will also have the opportunity to enable WireGuard encryption and confirm it is protecting your pod traffic.

## Hands-On Exercise: Deploy Calico on kind and Implement Tiered Policies

### Objective

Deploy a Calico-powered kind cluster, create policy tiers, implement namespace-scoped policies, and verify BGP peering between nodes. This exercise takes approximately 45 to 60 minutes to complete, depending on your internet connection speed for pulling container images.

### Step 1: Create a kind Cluster with Calico

```bash
# Create a multi-node kind cluster WITHOUT the default CNI
cat <<EOF > calico-kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  # Disable default CNI so we can install Calico
  disableDefaultCNI: true
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
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.32.0/manifests/tigera-operator.yaml

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
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.32.0/manifests/calicoctl.yaml

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

1. **Calico is a platform, not just a CNI.** It handles routing (BGP), policy (L3-L7), encryption (WireGuard), and IPAM in a single integrated system. Calico is Tigera-stewarded (vendor-led), not a CNCF-hosted project -- its peer Cilium is CNCF Graduated.

2. **BGP gives you native routing.** No overlays, no encapsulation overhead, full integration with existing datacenter networking -- this is Calico's unique strength. Use route reflectors to avoid the O(n²) full-mesh scaling problem above 50 nodes.

3. **Policy tiers solve the multi-team problem.** Security teams, platform teams, and developers can all write policies without stepping on each other, using `action: Pass` to delegate unmatched traffic downward.

4. **Typha is mandatory at scale.** Without it, the API server becomes the bottleneck. Deploy it before you hit 100 nodes, not after.

5. **eBPF, nftables, and WireGuard represent the modern dataplane.** Together they give you kernel-level packet processing and encryption with no sidecars and minimal overhead. The nftables dataplane (v3.29+) provides a middle ground for clusters that cannot meet eBPF's kernel requirements.

6. **calicoctl is your best friend.** `calicoctl node status` and `calicoctl ipam show` will save you hours of debugging.

---

## Further Reading

- [Calico Documentation](https://docs.tigera.io/calico/latest/) - Official docs (comprehensive and well-maintained)
- [Calico GitHub Repository](https://github.com/projectcalico/calico) - Source code, issues, and releases
- [BGP Explained for Kubernetes Engineers](https://www.tigera.io/blog/what-is-bgp/) - Tigera blog post on BGP fundamentals
- [Calico eBPF Dataplane](https://docs.tigera.io/calico/latest/operations/ebpf/) - Full guide to enabling and operating eBPF mode
- [calicoctl Reference](https://docs.tigera.io/calico/latest/reference/calicoctl/) - CLI command reference
- [Calico Network Policy Guide](https://docs.tigera.io/calico/latest/network-policy/) - Comprehensive policy documentation
- [Calico Product Editions](https://docs.tigera.io/calico/latest/about/calico-product-editions) - Comparison of Open Source, Enterprise, and Cloud
- [Calico VXLAN and IPIP Configuration](https://docs.tigera.io/calico/latest/networking/configuring/vxlan-ipip) - Overlay networking details
- [CNI Specification](https://github.com/containernetworking/cni/blob/main/SPEC.md) - The Container Network Interface spec that defines how every Kubernetes CNI plugin works
- [CNCF Cilium Project](https://www.cncf.io/projects/cilium/) - Governance and maturity comparison; Cilium is a CNCF Graduated project
- *Kubernetes Networking* by James Strong and Vallery Lancey (O'Reilly) - Covers Calico in depth

---

## Next Module

Continue to [Module 5.1: Cilium](../module-5.1-cilium/) if you have not already, or return to the [Networking Toolkit README]() to explore other networking modules.

---

*"BGP has been routing the internet since 1994. Calico brings that same battle-tested protocol to every pod in your cluster. There is no more proven foundation for production networking."*

## Sources

- [Project Calico GitHub Repository](https://github.com/projectcalico/calico) — Primary upstream project entry point for releases, code, and high-level feature references.
- [Calico Documentation](https://docs.tigera.io/calico/latest/) — Authoritative source for architecture, configuration, and operational guidance.
- [Calico Product Editions](https://docs.tigera.io/calico/latest/about/calico-product-editions) — Official comparison of Calico Open Source, Enterprise, and Cloud editions.
- [Tigera: About Calico](https://docs.tigera.io/calico/latest/about/about-calico) — Project overview, stewardship model, and community information.
- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/) — Authoritative baseline for what the core Kubernetes NetworkPolicy API does and does not provide.
- [Kubernetes Network Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/) — CNI plugin overview, how Calico fits into the Kubernetes networking model.
- [CNI Specification](https://github.com/containernetworking/cni/blob/main/SPEC.md) — The Container Network Interface specification that defines ADD/DEL/CHECK operations.
- [RFC 4456: BGP Route Reflection](https://www.rfc-editor.org/rfc/rfc4456) — Canonical reference for the route-reflector model used to avoid full-mesh BGP scaling problems.
- [Calico eBPF Dataplane](https://docs.tigera.io/calico/latest/operations/ebpf/) — Complete guide to enabling, operating, and debugging the eBPF dataplane.
- [Calico Network Policy](https://docs.tigera.io/calico/latest/network-policy/) — Comprehensive policy documentation covering tiers, GlobalNetworkPolicy, and L7 rules.
- [CNCF: Cilium](https://www.cncf.io/projects/cilium/) — CNCF project page for Cilium, referenced for governance comparison.
