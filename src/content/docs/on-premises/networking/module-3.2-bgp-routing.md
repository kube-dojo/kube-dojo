---
title: "Module 3.2: BGP & Routing for Kubernetes"
slug: on-premises/networking/module-3.2-bgp-routing
sidebar:
  order: 3
---

> **Complexity**: `[COMPLEX]` | Time: 60 minutes
>
> **Prerequisites**: [Module 3.1: Datacenter Network Architecture](module-3.1-datacenter-networking/), [Advanced Networking: BGP Routing](../../platform/foundations/advanced-networking/module-1.4-bgp-routing/)

---

## Why This Module Matters

In a cloud-managed Kubernetes service, pod networking "just works." AWS VPC CNI assigns ENI IPs, GKE uses Dataplane V2, Azure CNI plugs into the VNet. On bare metal, there is no underlying cloud network — you must integrate Kubernetes pod networking with your datacenter's physical network fabric.

BGP (Border Gateway Protocol) is the standard way to do this. It was designed for internet-scale routing between ISPs, but it has been adopted by datacenter networks because it is simple, stable, and scales horizontally. When Kubernetes nodes announce their pod CIDRs via BGP to the datacenter switches, every pod becomes directly routable on the physical network — no overlay, no encapsulation, no NAT.

This module teaches you how to configure BGP peering between Kubernetes CNIs (Calico, Cilium) and datacenter switches, how to use route reflectors to scale beyond direct peering, and how to handle multi-site routing.

---

## What You'll Learn

- BGP fundamentals for datacenter use (eBGP, iBGP, AS numbers)
- Calico BGP peering with ToR switches
- Cilium BGP peering with CiliumBGPPeeringPolicy
- Route reflectors for scaling BGP
- Service IP advertisement (MetalLB + BGP)
- Multi-site BGP design

---

## BGP for Datacenter Kubernetes

### Why BGP Instead of OSPF/IS-IS?

| Protocol | Best For | Why Not for K8s |
|----------|---------|-----------------|
| **OSPF** | Enterprise campus | Complex, stateful, hard to troubleshoot at scale |
| **IS-IS** | Service provider | Requires all nodes to run IS-IS (complex) |
| **BGP** | Everything | Simple, policy-rich, runs on every datacenter switch |

BGP won the datacenter because:
- **Simplicity**: Peer with a neighbor, announce routes, done
- **Policy**: Can filter, tag, and manipulate routes per-peer
- **Scalability**: Designed for the internet (900K+ routes); your datacenter is trivial
- **Tooling**: Every switch vendor supports it; every K8s CNI supports it

### BGP Concepts for K8s

```
┌─────────────────────────────────────────────────────────────┐
│               BGP KEY CONCEPTS                               │
│                                                               │
│  AS (Autonomous System):                                    │
│  A group of routers under one administrative domain.        │
│  Each gets a number: 64512-65534 (private range)            │
│                                                               │
│  eBGP (External BGP):                                       │
│  Peering between DIFFERENT AS numbers.                      │
│  Used: K8s node (AS 64512) ↔ ToR switch (AS 64501)         │
│                                                               │
│  iBGP (Internal BGP):                                       │
│  Peering between SAME AS number.                            │
│  Used: Node-to-node mesh within the cluster                 │
│                                                               │
│  Route Advertisement:                                        │
│  "I have these networks: 10.244.1.0/24, 10.244.2.0/24"     │
│  Node tells the switch about its pod CIDR                   │
│                                                               │
│  Route Reflector:                                            │
│  Reduces iBGP mesh: instead of N×N peerings,               │
│  all nodes peer with 2-3 reflectors                         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Calico BGP Configuration

### Step 1: Disable Node-to-Node Mesh

By default, Calico creates a full mesh of iBGP sessions between all nodes. At 100+ nodes, this means 4,950 BGP sessions. Replace with route reflectors:

```yaml
# Disable full mesh, use route reflectors instead
apiVersion: projectcalico.org/v3
kind: BGPConfiguration
metadata:
  name: default
spec:
  logSeverityScreen: Info
  nodeToNodeMeshEnabled: false
  asNumber: 64512
  # Advertise service ClusterIPs externally
  serviceClusterIPs:
    - cidr: 10.96.0.0/12
  # Advertise external IPs (LoadBalancer services)
  serviceExternalIPs:
    - cidr: 10.0.50.0/24
```

### Step 2: Configure Route Reflectors

Designate 2-3 nodes as route reflectors (typically control plane nodes):

```bash
# Label nodes as route reflectors
kubectl label node cp-01 route-reflector=true
kubectl label node cp-02 route-reflector=true
kubectl label node cp-03 route-reflector=true

# Set route reflector cluster ID on each
kubectl annotate node cp-01 projectcalico.org/RouteReflectorClusterID=1.0.0.1
kubectl annotate node cp-02 projectcalico.org/RouteReflectorClusterID=1.0.0.1
kubectl annotate node cp-03 projectcalico.org/RouteReflectorClusterID=1.0.0.1
```

```yaml
# Non-RR nodes peer with route reflectors
apiVersion: projectcalico.org/v3
kind: BGPPeer
metadata:
  name: peer-with-route-reflectors
spec:
  nodeSelector: "route-reflector != 'true'"
  peerSelector: route-reflector == 'true'

---
# Route reflectors peer with each other
apiVersion: projectcalico.org/v3
kind: BGPPeer
metadata:
  name: rr-mesh
spec:
  nodeSelector: route-reflector == 'true'
  peerSelector: route-reflector == 'true'
```

### Step 3: Peer with ToR Switches

```yaml
# Peer all nodes in rack-a with their ToR switch
apiVersion: projectcalico.org/v3
kind: BGPPeer
metadata:
  name: rack-a-tor
spec:
  peerIP: 10.0.20.1
  asNumber: 64501
  nodeSelector: rack == 'rack-a'

---
# Rack B ToR
apiVersion: projectcalico.org/v3
kind: BGPPeer
metadata:
  name: rack-b-tor
spec:
  peerIP: 10.0.20.65
  asNumber: 64502
  nodeSelector: rack == 'rack-b'
```

### Step 4: Configure the ToR Switch (Example: Cumulus/SONiC)

```bash
# /etc/frr/frr.conf on the ToR switch (FRRouting)
router bgp 64501
  bgp router-id 10.0.20.1
  bgp bestpath as-path multipath-relax

  # Peer with all K8s nodes in this rack
  neighbor K8S_NODES peer-group
  neighbor K8S_NODES remote-as 64512
  neighbor 10.0.20.10 peer-group K8S_NODES  # worker-01
  neighbor 10.0.20.11 peer-group K8S_NODES  # worker-02
  neighbor 10.0.20.12 peer-group K8S_NODES  # worker-03

  # Accept pod CIDR routes from K8s nodes
  address-family ipv4 unicast
    neighbor K8S_NODES soft-reconfiguration inbound
    neighbor K8S_NODES route-map ACCEPT-K8S in
    neighbor K8S_NODES route-map ADVERTISE-DEFAULT out
  exit-address-family

  # Peer with spine switches
  neighbor 10.0.20.254 remote-as 64500  # spine-1
  neighbor 10.0.20.253 remote-as 64500  # spine-2

! Route maps
route-map ACCEPT-K8S permit 10
  match ip address prefix-list K8S-PODS
ip prefix-list K8S-PODS seq 10 permit 10.244.0.0/16 le 26
ip prefix-list K8S-PODS seq 20 permit 10.96.0.0/12 le 32
```

### Verify BGP State

```bash
# On a K8s node (Calico)
calicoctl node status
# Calico process is running.
#
# IPv4 BGP status
# +--------------+-------------------+-------+----------+-------+
# | PEER ADDRESS |     PEER TYPE     | STATE |  SINCE   | INFO  |
# +--------------+-------------------+-------+----------+-------+
# | 10.0.20.1    | node-to-node mesh | up    | 08:15:30 | Est.  |
# | 10.0.20.10   | node-to-node mesh | up    | 08:15:31 | Est.  |
# +--------------+-------------------+-------+----------+-------+

# Check advertised routes
calicoctl get bgpPeer -o wide

# On the ToR switch
show bgp ipv4 unicast summary
# Neighbor        V   AS    MsgRcvd  MsgSent  Up/Down  State
# 10.0.20.10      4  64512    1234     5678   12:34:56 Estab
# 10.0.20.11      4  64512    1234     5678   12:34:56 Estab

show bgp ipv4 unicast
# Network          Next Hop       Metric  Path
# 10.244.1.0/24    10.0.20.10     0       64512 i
# 10.244.2.0/24    10.0.20.11     0       64512 i
# 10.96.0.0/12     10.0.20.10     0       64512 i
```

---

## Cilium BGP Configuration

Cilium uses CiliumBGPPeeringPolicy CRDs:

```yaml
apiVersion: cilium.io/v2alpha1
kind: CiliumBGPPeeringPolicy
metadata:
  name: rack-a
spec:
  nodeSelector:
    matchLabels:
      rack: rack-a
  virtualRouters:
    - localASN: 64512
      exportPodCIDR: true
      serviceSelector:
        matchExpressions:
          - key: somekey
            operator: NotIn
            values: ["never-match"]  # Advertise all services
      neighbors:
        - peerAddress: "10.0.20.1/32"
          peerASN: 64501
          connectRetryTimeSeconds: 30
          holdTimeSeconds: 90
          keepAliveTimeSeconds: 30
          gracefulRestart:
            enabled: true
            restartTimeSeconds: 120
```

```bash
# Verify Cilium BGP status
cilium bgp peers
# Node       Local AS  Peer AS  Peer Address  Session State  Uptime
# worker-01  64512     64501    10.0.20.1     established    4h32m
# worker-02  64512     64501    10.0.20.1     established    4h32m

cilium bgp routes advertised ipv4 unicast
# Prefix            Next Hop    AS Path
# 10.244.1.0/24     10.0.20.10  64512
# 10.96.0.1/32      10.0.20.10  64512
```

---

## Multi-Site BGP Design

For clusters spanning two datacenters:

```
┌─────────────────────────────────────────────────────────────┐
│              MULTI-SITE BGP                                  │
│                                                               │
│  DC-East (AS 64510)              DC-West (AS 64520)         │
│  ┌──────────────────┐           ┌──────────────────┐        │
│  │ Spines           │           │ Spines           │        │
│  │ ┌──────┐┌──────┐ │           │ ┌──────┐┌──────┐ │        │
│  │ │Spine1││Spine2│ │◄── DCI ──►│ │Spine1││Spine2│ │        │
│  │ └──────┘└──────┘ │  (dark    │ └──────┘└──────┘ │        │
│  │                  │  fiber)   │                  │        │
│  │ Leaves + K8s     │           │ Leaves + K8s     │        │
│  │ Pod CIDR:        │           │ Pod CIDR:        │        │
│  │ 10.244.0.0/17    │           │ 10.244.128.0/17  │        │
│  │ Service CIDR:    │           │ Service CIDR:    │        │
│  │ 10.96.0.0/13     │           │ 10.96.128.0/17   │        │
│  └──────────────────┘           └──────────────────┘        │
│                                                               │
│  Key rules:                                                  │
│  1. Non-overlapping pod/service CIDRs per DC                │
│  2. DCI link carries only summarized routes                 │
│  3. etcd stays within one DC (latency constraint)           │
│  4. BGP communities tag routes by origin DC                 │
│  5. Services can be exposed in both DCs via anycast         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **BGP manages over 900,000 routes on the public internet** as of 2024. Your datacenter with a few hundred pod CIDRs is trivially small by comparison. BGP will never be the bottleneck.

- **Calico's BGP implementation uses BIRD** (BIRD Internet Routing Daemon), the same software used by many internet exchange points. Cilium uses GoBGP, a Go-native BGP implementation that is lighter weight.

- **Facebook's datacenter network uses eBGP everywhere** — even between switches in the same rack. They eliminated iBGP entirely because eBGP is simpler (no route reflectors needed, clear AS path). This pattern is called "BGP unnumbered" and is increasingly adopted.

- **Route reflectors should be on control plane nodes** because they are the most stable nodes in the cluster. Worker nodes that get drained, rescheduled, or replaced would cause BGP session flaps if they were route reflectors.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Full mesh at scale | N^2 BGP sessions (100 nodes = 4,950 sessions) | Use route reflectors with 2-3 RR nodes |
| Wrong AS number | Private range is 64512-65534; using public AS causes conflicts | Always use private AS numbers for internal BGP |
| No graceful restart | BGP session reset during node maintenance = route withdrawal | Enable BFD + graceful restart on all peers |
| Advertising too many routes | Every /32 pod IP advertised = huge routing table | Advertise /24 or /26 per-node aggregates |
| No route filtering on switch | K8s node announces default route → hijacks all traffic | Apply prefix-list to accept only pod/service CIDRs |
| Forgetting service CIDRs | ClusterIP services not reachable from outside | Advertise service CIDR in BGP (Calico serviceClusterIPs) |
| Single route reflector | RR failure = cluster-wide route convergence | Always deploy 2-3 RRs across failure domains |

---

## Quiz

### Question 1
Your cluster has 200 nodes. How many BGP sessions exist with full mesh vs route reflectors (3 RRs)?

<details>
<summary>Answer</summary>

**Full mesh**: N × (N-1) / 2 = 200 × 199 / 2 = **19,900 BGP sessions**. Every node peers with every other node. This is unsustainable — each session consumes memory, CPU for keepalives, and causes convergence storms when a node goes down.

**Route reflectors (3 RRs)**:
- 197 non-RR nodes × 3 RR peers = 591 sessions
- 3 RR nodes × 2 RR-to-RR peers = 6 sessions
- 200 nodes × 1 ToR peer each = 200 sessions (eBGP)
- **Total: ~797 sessions** — 25x fewer than full mesh.

This is why route reflectors are essential beyond ~50 nodes.
</details>

### Question 2
A pod on node A (rack 1) needs to reach a pod on node B (rack 3). Trace the packet path with Calico BGP mode (no overlay).

<details>
<summary>Answer</summary>

```
Pod A (10.244.1.5) → Node A kernel → routing table lookup
  → 10.244.3.0/24 via 10.0.20.130 (learned from BGP via ToR)
  → Packet sent to ToR switch (rack 1, leaf-1)
  → Leaf-1 routing table: 10.244.3.0/24 via spine
  → Packet to Spine switch (ECMP across available spines)
  → Spine routing table: 10.244.3.0/24 via leaf-3
  → Packet to Leaf-3 (ToR, rack 3)
  → Leaf-3 routing table: 10.244.3.0/24 via 10.0.20.130 (node B)
  → Packet to Node B
  → Node B kernel → routing table → veth → Pod B (10.244.3.8)
```

**Total hops**: Node A → Leaf-1 → Spine → Leaf-3 → Node B (4 L3 hops)

**Key advantage**: No encapsulation. The packet carries the real pod IPs the entire way. `tcpdump` on any switch shows source 10.244.1.5, destination 10.244.3.8.
</details>

### Question 3
Your ToR switch shows that a K8s node is advertising a default route (0.0.0.0/0) via BGP. What is the impact and how do you fix it?

<details>
<summary>Answer</summary>

**Impact**: The ToR switch installs the default route pointing to the K8s node. All traffic that doesn't match a more specific route (including internet-bound traffic from other servers in the rack) gets sent to the K8s node. This effectively makes a K8s worker node the default gateway for the rack, which will:
1. Overload the node with non-K8s traffic
2. Black-hole internet traffic (the node is not a router)
3. Potentially cause a routing loop

**Fix on the switch** (immediate):
```
ip prefix-list K8S-PODS seq 5 deny 0.0.0.0/0
ip prefix-list K8S-PODS seq 10 permit 10.244.0.0/16 le 26
ip prefix-list K8S-PODS seq 20 permit 10.96.0.0/12 le 32
```
This denies the default route and only accepts pod and service CIDRs.

**Fix on Calico** (root cause):
Check if a node has `CALICO_ADVERTISE_CLUSTER_IPS` or a BGP configuration that advertises the default route. Ensure only pod and service CIDRs are in the advertisement configuration.
</details>

### Question 4
When should you use eBGP between K8s nodes and the ToR switch instead of iBGP?

<details>
<summary>Answer</summary>

**Almost always use eBGP** between K8s nodes and ToR switches. This is the industry standard for datacenter BGP.

**Why eBGP:**
- K8s nodes (AS 64512) and ToR switches (AS 64501) are different administrative domains
- eBGP has a TTL of 1 by default (packets don't leak beyond one hop)
- eBGP does not require route reflectors for the switch-to-node peering
- eBGP path selection is simpler (shortest AS path wins)
- Clear boundary between "Kubernetes routing" and "datacenter routing"

**Use iBGP only** for node-to-node peering within the Kubernetes cluster (same AS 64512). This is what Calico's node-to-node mesh does before you replace it with route reflectors.

**Summary:**
- Node ↔ Node: iBGP (AS 64512) via route reflectors
- Node ↔ ToR switch: eBGP (AS 64512 ↔ AS 64501)
- ToR ↔ Spine: eBGP (AS 64501 ↔ AS 64500)
</details>

---

## Hands-On Exercise: Configure Calico BGP Peering

**Task**: Set up Calico BGP configuration in a local kind cluster — disable the node-to-node mesh and configure route reflectors.

```bash
# Create a kind cluster with Calico
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  podSubnet: "10.244.0.0/16"
nodes:
  - role: control-plane
  - role: worker
    kubeadmConfigPatches:
      - |
        kind: JoinConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "rack=rack-a"
  - role: worker
    kubeadmConfigPatches:
      - |
        kind: JoinConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "rack=rack-b"
EOF

# Install Calico
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.29.0/manifests/calico.yaml

# Wait for Calico to be ready
kubectl wait --for=condition=Ready pods -l k8s-app=calico-node -n kube-system --timeout=120s

# Install calicoctl
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.29.0/manifests/calicoctl.yaml

# Check default BGP configuration
kubectl exec -n kube-system calicoctl -- /calicoctl get bgpConfiguration -o yaml

# Check node BGP status
kubectl exec -n kube-system calicoctl -- /calicoctl node status

# Disable node-to-node mesh and configure BGP
kubectl exec -i -n kube-system calicoctl -- /calicoctl apply -f - <<EOF
apiVersion: projectcalico.org/v3
kind: BGPConfiguration
metadata:
  name: default
spec:
  nodeToNodeMeshEnabled: false
  asNumber: 64512
  serviceClusterIPs:
    - cidr: 10.96.0.0/12
EOF

# Verify BGP peers
kubectl exec -n kube-system calicoctl -- /calicoctl get bgpPeer -o wide
```

### Success Criteria
- [ ] Kind cluster with Calico CNI running
- [ ] BGP configuration applied with node-to-node mesh disabled
- [ ] Service CIDR (10.96.0.0/12) configured for advertisement
- [ ] `calicoctl get bgpConfiguration` shows the expected settings

---

## Next Module

Continue to [Module 3.3: Load Balancing Without Cloud](module-3.3-load-balancing/) to learn how MetalLB, kube-vip, and HAProxy replace cloud load balancers on bare metal.
