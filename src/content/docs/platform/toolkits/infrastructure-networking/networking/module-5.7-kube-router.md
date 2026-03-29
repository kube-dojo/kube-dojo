---
title: "Module 5.7: Kube-Router - The Swiss Army Knife in a Single Binary"
slug: platform/toolkits/infrastructure-networking/networking/module-5.7-kube-router
sidebar:
  order: 8
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 45-55 minutes

## The Bare-Metal Startup That Ditched Three Tools for One

*Fifteen bare-metal nodes. One overworked platform engineer. And a networking stack that was falling apart.*

```
[2 months ago]
@platform-eng  OK so here's our stack: Flannel for CNI, kube-proxy for
               service routing, and we manually manage iptables for
               network policies. Three moving parts, three sets of logs,
               three things to debug at 2 AM.

@platform-eng  The real problem: kube-proxy in iptables mode. We have
               ~600 services now. That's 12,000+ iptables rules.

@platform-eng  Service routing latency: 200ms. For INTERNAL traffic.
               Our users think the app is slow but it's the network.

@cto           Can we move to the cloud?
@platform-eng  Our budget says no.
@cto           Can we buy a load balancer?
@platform-eng  Our budget REALLY says no.

[1 month ago]
@platform-eng  Found kube-router. One binary. Replaces Flannel AND
               kube-proxy. Uses IPVS instead of iptables for services.
               Also does NetworkPolicy. All three controllers in one
               process.

@cto           That sounds too good to be true.
@platform-eng  Migrating the staging cluster this weekend.

[Monday morning]
@platform-eng  Done. Results:
               - IPVS service routing latency: 2ms (was 200ms)
               - iptables rules: 47 (was 12,000+)
               - Memory usage per node: 35MB (Flannel+kube-proxy was 180MB)
               - Number of DaemonSets to manage: 1 (was 2)
               - Things I have to debug at 2 AM: fewer

@cto           Ship it to production.
@platform-eng  Already did.
```

One binary. Three jobs. 100x latency improvement. That is kube-router.

**What You'll Learn**:
- Why kube-router exists and what problem it solves
- The three-controller architecture: routes, services, policies
- How BGP replaces overlay networks on flat L2 networks
- IPVS service proxying and why it crushes iptables at scale
- When kube-router is the right choice (and when it is not)

**Prerequisites**:
- Kubernetes Services and networking basics (ClusterIP, NodePort, kube-proxy)
- [Module 5.1: Cilium](../module-5.1-cilium/) (helpful for comparison, not required)
- Basic understanding of Linux networking (routing tables, iptables)
- Familiarity with BGP concepts (we will explain what you need)

---

## Why This Module Matters

There is a quiet revolution happening in Kubernetes networking, and it is not about eBPF or service meshes. It is about simplicity.

Most Kubernetes clusters run at least two networking components: a CNI plugin (Calico, Flannel, Cilium) for pod-to-pod communication, and kube-proxy for Service routing. Some clusters add a third component for NetworkPolicy enforcement. That is three DaemonSets, three configuration surfaces, three sets of logs, three things that can fail independently.

Kube-router says: what if one binary did all three?

This is not a theoretical exercise. For teams running small-to-medium bare-metal clusters on tight budgets, kube-router is a legitimate choice. It is used in production by companies that need Kubernetes networking without the overhead of Calico's multiple daemons or Cilium's kernel requirements.

> **Did You Know?** Kube-router was one of the first CNI plugins to implement IPVS-based service proxying, beating even kube-proxy's own IPVS mode to production readiness. The kube-proxy IPVS mode was partly inspired by kube-router's proof that IPVS was viable for Kubernetes service routing.

---

## Part 1: Understanding the Architecture

### One Binary, Three Controllers

Kube-router is a single Go binary that runs as a DaemonSet on every node. Inside that binary, three independent controllers handle the three core networking concerns:

```
KUBE-ROUTER ARCHITECTURE
═══════════════════════════════════════════════════════════════════

                    ┌─────────────────────────────────┐
                    │         Kubernetes API           │
                    │    (watches Nodes, Services,     │
                    │     Endpoints, NetworkPolicies)  │
                    └──────────┬──────────────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │     kube-router (single binary)  │
                    │                                   │
                    │  ┌─────────────────────────────┐ │
                    │  │  Network Routes Controller   │ │
                    │  │  ─────────────────────────── │ │
                    │  │  BGP peering with GoBGP      │ │
                    │  │  Advertises pod CIDRs        │ │
                    │  │  Programs host routing table │ │
                    │  │  → Replaces: Flannel/CNI     │ │
                    │  └─────────────────────────────┘ │
                    │                                   │
                    │  ┌─────────────────────────────┐ │
                    │  │  Network Services Controller │ │
                    │  │  ─────────────────────────── │ │
                    │  │  IPVS virtual servers        │ │
                    │  │  Load balancing algorithms   │ │
                    │  │  Direct Server Return (DSR)  │ │
                    │  │  → Replaces: kube-proxy      │ │
                    │  └─────────────────────────────┘ │
                    │                                   │
                    │  ┌─────────────────────────────┐ │
                    │  │  Network Policy Controller   │ │
                    │  │  ─────────────────────────── │ │
                    │  │  iptables + ipsets           │ │
                    │  │  Efficient rule matching     │ │
                    │  │  Full NetworkPolicy spec     │ │
                    │  │  → Replaces: Calico policies │ │
                    │  └─────────────────────────────┘ │
                    │                                   │
                    └──────────┬──────────────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │         Linux Kernel             │
                    │  ┌────────┐ ┌──────┐ ┌────────┐│
                    │  │Routing │ │ IPVS │ │iptables││
                    │  │ Table  │ │      │ │+ipsets ││
                    │  └────────┘ └──────┘ └────────┘│
                    └─────────────────────────────────┘
```

Each controller can be enabled or disabled independently. You can run kube-router as:
- **Full replacement**: All three controllers (CNI + kube-proxy + NetworkPolicy)
- **kube-proxy replacement only**: Just the Network Services Controller
- **NetworkPolicy only**: Just the Network Policy Controller alongside your existing CNI
- **Any combination**: Mix and match based on your needs

This flexibility is a killer feature. You can adopt kube-router incrementally.

### How It Watches the API Server

All three controllers share a single connection to the Kubernetes API server. They watch:

- **Nodes**: To learn about peer nodes and their pod CIDRs
- **Services and EndpointSlices**: To program IPVS virtual servers
- **NetworkPolicies**: To generate iptables rules
- **Pods**: To map pod IPs to nodes for routing decisions

One watch connection, one binary, one DaemonSet. Compare that to Calico, which runs `calico-node`, `calico-kube-controllers`, and optionally `calico-typha` -- three separate processes with their own API watchers.

> **Did You Know?** Kube-router uses GoBGP, a pure Go implementation of BGP written by the team at NTT Communications. GoBGP supports the full BGP specification (RFC 4271) and is also used by other networking projects like MetalLB and Cilium for their BGP implementations.

---

## Part 2: BGP Routing (Network Routes Controller)

### The Overlay Tax

Most CNI plugins use overlay networks. Flannel wraps every pod packet inside a VXLAN header. Calico can do either overlay or native routing. Cilium supports both.

Overlays have a cost:

```
OVERLAY NETWORKING (Flannel VXLAN)
═══════════════════════════════════════════════════════════════════

Pod A (10.244.1.5) on Node 1 → Pod B (10.244.2.8) on Node 2

Step 1: Pod A sends packet to 10.244.2.8
Step 2: Node 1 kernel doesn't know 10.244.2.0/24
Step 3: Flannel catches it, wraps in VXLAN header
        Original packet: [IP: 10.244.1.5 → 10.244.2.8] [data]
        VXLAN packet:    [IP: 192.168.1.10 → 192.168.1.11]
                         [VXLAN header]
                         [IP: 10.244.1.5 → 10.244.2.8] [data]
Step 4: Outer packet routed via physical network
Step 5: Node 2 receives, strips VXLAN header
Step 6: Inner packet delivered to Pod B

Cost: +50 bytes per packet, encap/decap CPU overhead, MTU reduction
```

### Kube-Router's Approach: Just Use BGP

If your nodes are on the same L2 network (same switch, same VLAN), you do not need an overlay. You just need every node to know "pod CIDR 10.244.2.0/24 lives on Node 2." That is a routing problem, and BGP has been solving routing problems since 1989.

```
KUBE-ROUTER BGP ROUTING (No Overlay)
═══════════════════════════════════════════════════════════════════

Pod A (10.244.1.5) on Node 1 → Pod B (10.244.2.8) on Node 2

Step 1: Pod A sends packet to 10.244.2.8
Step 2: Node 1 kernel checks routing table:
        10.244.2.0/24 via 192.168.1.11 dev eth0  ← learned via BGP
Step 3: Packet sent directly to Node 2's IP
        Packet: [IP: 10.244.1.5 → 10.244.2.8] [data]
Step 4: Node 2 receives, routes to Pod B

Cost: Zero overhead. Native IP routing. Full MTU preserved.

How the routes got there:
─────────────────────────────────────────────────────────────────
Node 1 kube-router ←──BGP──→ Node 2 kube-router

"Hey, I'm responsible for 10.244.1.0/24"
                    "Cool, I've got 10.244.2.0/24"

Both nodes add routes to their kernel routing table.
Done. No overlay, no encapsulation, no tunnel interfaces.
```

### Full-Mesh BGP vs Route Reflectors

By default, kube-router establishes BGP sessions between every pair of nodes (full mesh). This works great for small clusters:

```
FULL MESH BGP (default, good for < 50 nodes)
═══════════════════════════════════════════════════════════════════

    Node 1 ◄─────────► Node 2
      ▲  ╲               ╱  ▲
      │    ╲             ╱    │
      │      ╲         ╱      │
      │        ╲     ╱        │
      ▼          ╲ ╱          ▼
    Node 4 ◄─────────► Node 3

    4 nodes = 6 BGP sessions (n*(n-1)/2)
    10 nodes = 45 sessions
    50 nodes = 1,225 sessions  ← getting uncomfortable
    100 nodes = 4,950 sessions ← too many
```

For larger clusters, use BGP route reflectors. A few nodes act as central hubs:

```
ROUTE REFLECTOR TOPOLOGY (for larger clusters)
═══════════════════════════════════════════════════════════════════

                 ┌──────────────────┐
                 │  Route Reflector  │
                 │  (Node 1)        │
                 └────────┬─────────┘
                    ╱     │     ╲
                 ╱        │        ╲
              ╱           │           ╲
    ┌────────┐    ┌───────┐    ┌────────┐
    │ Node 2 │    │ Node 3│    │ Node 4 │
    └────────┘    └───────┘    └────────┘

    Each node peers only with the route reflector(s).
    100 nodes = 100 BGP sessions (vs 4,950 in full mesh)
```

Configure route reflectors with annotations:

```bash
# Designate nodes as route reflectors
kubectl annotate node node1 \
  kube-router.io/node.bgp.routereflector.cluster-id=1.0.0.1

# Client nodes peer only with reflectors (configured via kube-router flags)
# --nodes-full-mesh=false
# --peer-router-asns=64512
# --peer-router-ips=192.168.1.10,192.168.1.11
```

### When Overlays Are Still Needed

BGP routing only works when the underlying network can route pod CIDRs. This means:
- **Same L2 network**: Nodes on the same switch or VLAN -- BGP works perfectly
- **Across L3 boundaries**: Nodes on different subnets -- you need either overlay or your physical routers to participate in BGP
- **Cloud environments**: Cloud VPCs usually do not forward arbitrary IP ranges -- overlay required

Kube-router supports IPIP and VXLAN overlays as fallback for cross-subnet communication. You can even mix: native routing within a subnet, overlay between subnets.

---

## Part 3: IPVS Service Proxy (Network Services Controller)

### The iptables Problem at Scale

This is the core insight that makes kube-router compelling. Let's understand why iptables falls apart.

When kube-proxy uses iptables mode, every Kubernetes Service gets a chain of rules. For each Service, there are rules for ClusterIP, NodePort (if applicable), and one rule per endpoint (pod). The packet must traverse these rules sequentially:

```
IPTABLES SERVICE ROUTING (kube-proxy default)
═══════════════════════════════════════════════════════════════════

Packet arrives for Service ClusterIP 10.96.0.100:80

  Rule 1:  Does packet match Service A? No → next rule
  Rule 2:  Does packet match Service B? No → next rule
  Rule 3:  Does packet match Service C? No → next rule
  ...
  Rule 437: Does packet match Service D? YES!
    → Sub-rule 1: 33% chance → endpoint 10.244.1.5:8080
    → Sub-rule 2: 50% chance → endpoint 10.244.2.8:8080
    → Sub-rule 3: 100% chance → endpoint 10.244.3.2:8080

Performance: O(n) — every packet walks the chain.
500 services × ~10 rules each = 5,000+ rules to traverse.
```

### IPVS: O(1) Service Routing

IPVS (IP Virtual Server) is a Linux kernel module built specifically for load balancing. It uses hash tables internally, so looking up a service is O(1) regardless of how many services you have:

```
IPVS SERVICE ROUTING (kube-router)
═══════════════════════════════════════════════════════════════════

Packet arrives for Service ClusterIP 10.96.0.100:80

  Step 1: Hash lookup: 10.96.0.100:80 → found!
  Step 2: Apply scheduling algorithm (round-robin, least-connections, etc.)
  Step 3: Forward to selected endpoint: 10.244.2.8:8080

Performance: O(1) — constant time regardless of service count.
500 services or 50,000 services — same lookup speed.
```

Here are real numbers that illustrate the difference:

| Services | iptables Rules | iptables Latency | IPVS Latency | Improvement |
|----------|---------------|------------------|--------------|-------------|
| 100 | ~1,500 | ~1ms | ~0.1ms | 10x |
| 500 | ~7,000 | ~5ms | ~0.1ms | 50x |
| 1,000 | ~14,000 | ~15ms | ~0.1ms | 150x |
| 5,000 | ~65,000 | ~100ms+ | ~0.1ms | 1000x |
| 10,000 | ~130,000 | ~200ms+ | ~0.1ms | 2000x |

The scaling characteristics are completely different. IPVS does not care how many services you have.

### Scheduling Algorithms

Unlike kube-proxy's iptables mode (which can only do random probability-based balancing), IPVS supports real load-balancing algorithms:

| Algorithm | Flag | How It Works | Best For |
|-----------|------|-------------|----------|
| **Round Robin** | `rr` | Rotate through backends equally | Equal-capacity backends |
| **Least Connection** | `lc` | Send to backend with fewest active connections | Variable request duration |
| **Weighted Least Connection** | `wlc` | Like `lc` but respects backend weights | Mixed-capacity backends |
| **Source Hashing** | `sh` | Same client IP always hits same backend | Session affinity |
| **Destination Hashing** | `dh` | Same destination always uses same route | Caching proxies |
| **Shortest Expected Delay** | `sed` | Minimizes expected delay based on connections | Latency-sensitive apps |
| **Never Queue** | `nq` | Send to idle server, or fall back to `sed` | Avoiding request queuing |

Configure the algorithm in kube-router:

```bash
# Set scheduling algorithm globally
kube-router --run-service-proxy=true \
            --service-proxy-scheduling-algorithm=lc

# Or per-service via annotation
kubectl annotate service my-service \
  kube-router.io/service.scheduler=wlc
```

### Direct Server Return (DSR)

This is one of kube-router's most powerful features for performance-sensitive workloads. Normally, return traffic from a backend pod travels back through the same node that received the original request. With DSR, the response goes directly to the client:

```
NORMAL SERVICE ROUTING (without DSR)
═══════════════════════════════════════════════════════════════════

Client ──request──▶ Node 1 (IPVS) ──forward──▶ Pod on Node 2
Client ◀─response── Node 1 (IPVS) ◀─response── Pod on Node 2
                     ▲
                     └── Return path goes back through Node 1.
                         Extra hop. Extra latency. Extra load
                         on Node 1's network stack.


DIRECT SERVER RETURN (with DSR)
═══════════════════════════════════════════════════════════════════

Client ──request──▶ Node 1 (IPVS) ──forward──▶ Pod on Node 2
Client ◀─response────────────────────────────── Pod on Node 2
                                                 ▲
                     Response goes DIRECTLY back to client.
                     Node 1 only handles the inbound packet.
                     Response packets (often much larger than
                     requests) bypass the proxy entirely.
```

DSR is especially valuable for:
- **Streaming workloads**: Video, large file downloads -- response is much bigger than request
- **High-throughput services**: Reduces load on the proxy node by ~50%
- **Latency-sensitive paths**: Eliminates one network hop from the response

Enable DSR:

```bash
kube-router --run-service-proxy=true \
            --service-proxy-dsr=true
```

> **Did You Know?** DSR is a technique borrowed from traditional hardware load balancers like F5 and Citrix. In the hardware world, it is called "Direct Server Return" or "nPath routing." Kube-router brought this enterprise load-balancing technique to Kubernetes, making it available for free on commodity hardware.

---

## Part 4: NetworkPolicy Enforcement (Network Policy Controller)

### iptables + ipsets = Efficient Matching

Kube-router implements the standard Kubernetes NetworkPolicy API using iptables rules combined with ipsets. The key insight is using ipsets for group matching rather than individual iptables rules per IP.

Without ipsets:
```bash
# Blocking 50 IPs requires 50 individual rules:
iptables -A INPUT -s 10.244.1.5 -j DROP
iptables -A INPUT -s 10.244.1.6 -j DROP
iptables -A INPUT -s 10.244.1.7 -j DROP
# ... 47 more rules
# Packet must check each rule sequentially
```

With ipsets:
```bash
# Same 50 IPs in a single hash set:
ipset create blocked-pods hash:ip
ipset add blocked-pods 10.244.1.5
ipset add blocked-pods 10.244.1.6
# ... add all IPs

# One iptables rule matches the entire set:
iptables -A INPUT -m set --match-set blocked-pods src -j DROP
# O(1) hash lookup regardless of set size
```

Kube-router creates ipsets for each NetworkPolicy selector and references them in iptables rules. This means even with hundreds of pods matching a policy, the matching overhead stays constant.

### Example: Default Deny + Allow

```yaml
# Default deny all ingress in namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
---
# Allow frontend to reach backend on port 8080
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

What kube-router does behind the scenes:

```bash
# Creates ipsets for the selectors
ipset list | grep kube-router
# kube-router-frontend-pods: {10.244.1.5, 10.244.1.6, 10.244.2.3}
# kube-router-backend-pods:  {10.244.2.8, 10.244.3.2}

# Creates iptables rules referencing ipsets
iptables -A KUBE-ROUTER-INPUT \
  -m set --match-set kube-router-backend-pods dst \
  -m set --match-set kube-router-frontend-pods src \
  -p tcp --dport 8080 \
  -j ACCEPT

iptables -A KUBE-ROUTER-INPUT \
  -m set --match-set kube-router-backend-pods dst \
  -j DROP
```

This is standard Kubernetes NetworkPolicy. No custom CRDs, no vendor-specific extensions. If you later switch to Calico or Cilium, your policies work unchanged.

> **Did You Know?** Kube-router was the first Kubernetes networking solution to combine all three functions -- CNI, service proxy, and network policy -- into a single binary. Before kube-router, the minimum viable networking stack required at least two components (a CNI plugin and kube-proxy), and network policies needed a third.

---

## Part 5: Installation and Configuration

### Deploying Kube-Router

Kube-router runs as a DaemonSet. The deployment varies depending on which controllers you enable.

#### Full Replacement (CNI + Service Proxy + NetworkPolicy)

For a new cluster where kube-router handles everything:

```bash
# Step 1: Create cluster without kube-proxy
# If using kubeadm:
kubeadm init --pod-network-cidr=10.244.0.0/16 --skip-phases=addon/kube-proxy

# Step 2: Deploy kube-router as DaemonSet
kubectl apply -f https://raw.githubusercontent.com/cloudnativelabs/kube-router/master/daemonset/kubeadm/kube-router-all-features.yaml
```

Or with a custom DaemonSet for more control:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: kube-router
  namespace: kube-system
  labels:
    k8s-app: kube-router
spec:
  selector:
    matchLabels:
      k8s-app: kube-router
  template:
    metadata:
      labels:
        k8s-app: kube-router
    spec:
      hostNetwork: true
      tolerations:
      - effect: NoSchedule
        operator: Exists
      - key: CriticalAddonsOnly
        operator: Exists
      - effect: NoExecute
        operator: Exists
      serviceAccountName: kube-router
      containers:
      - name: kube-router
        image: docker.io/cloudnativelabs/kube-router:latest
        args:
        - --run-router=true
        - --run-firewall=true
        - --run-service-proxy=true
        - --bgp-graceful-restart=true
        - --kubeconfig=/var/lib/kube-router/kubeconfig
        env:
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        securityContext:
          privileged: true
        volumeMounts:
        - name: lib-modules
          mountPath: /lib/modules
          readOnly: true
        - name: cni-conf-dir
          mountPath: /etc/cni/net.d
        - name: kubeconfig
          mountPath: /var/lib/kube-router
          readOnly: true
      volumes:
      - name: lib-modules
        hostPath:
          path: /lib/modules
      - name: cni-conf-dir
        hostPath:
          path: /etc/cni/net.d
      - name: kubeconfig
        configMap:
          name: kube-router-cfg
```

#### Service Proxy Only (Replacing kube-proxy)

If you already have a CNI and just want IPVS service routing:

```bash
# Delete kube-proxy first
kubectl -n kube-system delete ds kube-proxy
# Clean up kube-proxy's iptables rules
kubectl -n kube-system exec <kube-router-pod> -- kube-router --cleanup-config

# Deploy kube-router with only service proxy
# Args:
# --run-router=false       (don't manage routes)
# --run-firewall=false     (don't manage network policies)
# --run-service-proxy=true (replace kube-proxy)
```

#### NetworkPolicy Only

If you use Flannel (which has no NetworkPolicy support) and just want policy enforcement:

```bash
# Deploy kube-router alongside Flannel
# Args:
# --run-router=false         (Flannel handles routes)
# --run-firewall=true        (enforce NetworkPolicies)
# --run-service-proxy=false  (kube-proxy handles services)
```

### Key Configuration Flags

| Flag | Default | What It Does |
|------|---------|-------------|
| `--run-router` | `true` | Enable BGP routing (CNI) |
| `--run-firewall` | `true` | Enable NetworkPolicy enforcement |
| `--run-service-proxy` | `true` | Enable IPVS service proxy |
| `--nodes-full-mesh` | `true` | BGP full mesh between all nodes |
| `--enable-overlay` | `false` | Use IPIP/VXLAN overlay for cross-subnet |
| `--overlay-type` | `subnet` | `subnet` (IPIP) or `full` (always overlay) |
| `--service-proxy-scheduling-algorithm` | `rr` | IPVS scheduling: rr, lc, wlc, sh, dh |
| `--service-proxy-dsr` | `false` | Enable Direct Server Return |
| `--bgp-graceful-restart` | `false` | BGP graceful restart on kube-router restart |
| `--cluster-asn` | `64512` | BGP Autonomous System Number |
| `--hairpin-mode` | `false` | Allow pod to reach itself via Service IP |
| `--metrics-port` | `0` (disabled) | Prometheus metrics port |

### Verifying the Installation

```bash
# Check kube-router pods are running
kubectl -n kube-system get pods -l k8s-app=kube-router

# Check BGP peering status
kubectl -n kube-system exec <kube-router-pod> -- \
  kube-router --show-bgp-peers

# Check IPVS virtual servers
kubectl -n kube-system exec <kube-router-pod> -- ipvsadm -Ln

# Check ipsets for network policies
kubectl -n kube-system exec <kube-router-pod> -- ipset list

# Check routing table on a node
kubectl -n kube-system exec <kube-router-pod> -- ip route show
# You should see routes like:
# 10.244.1.0/24 via 192.168.1.11 dev eth0 proto 17
# 10.244.2.0/24 via 192.168.1.12 dev eth0 proto 17
```

---

## Part 6: When to Use Kube-Router

### The Sweet Spot

Kube-router shines in specific scenarios. Here is an honest assessment.

**Use kube-router when:**

- **Small-to-medium bare-metal clusters (5-50 nodes)**: This is kube-router's home turf. No cloud load balancer integration needed, BGP just works on L2 networks, and the single binary keeps operational overhead minimal.

- **Resource-constrained environments**: Edge deployments, IoT gateways, Raspberry Pi clusters. Kube-router's single binary uses significantly less memory and CPU than Calico's multi-component stack or Cilium's eBPF infrastructure.

- **Teams that value simplicity**: If your team does not need L7 policies, eBPF observability, or encryption, kube-router does the basics really well. One binary, one config, one log stream to debug.

- **Flannel users who need NetworkPolicy**: Flannel does not support NetworkPolicy. Instead of migrating your entire CNI, you can add kube-router's firewall controller alongside Flannel.

- **Replacing kube-proxy on any cluster**: Even if you use a different CNI, kube-router's IPVS service proxy is a solid kube-proxy replacement.

**Do NOT use kube-router when:**

- **Large clusters (100+ nodes)**: BGP full mesh does not scale. You can use route reflectors, but at that scale, Calico or Cilium have more mature BGP implementations with better tooling.

- **You need L7 policies**: Kube-router implements standard Kubernetes NetworkPolicy only (L3/L4). If you need HTTP method/path-based policies, you need Cilium or a service mesh.

- **You need eBPF-level observability**: Kube-router has no equivalent to Hubble. If you need per-flow visibility, packet drop reasons, and DNS-aware policies, Cilium is the answer.

- **You need encryption**: Kube-router does not provide transparent encryption (WireGuard/IPsec). You would need a service mesh or Cilium for mTLS.

- **Cloud-managed Kubernetes**: EKS, GKE, and AKS come with their own CNI and service proxy integrations. Replacing them with kube-router would lose cloud-specific features (like security group integration, VPC routing).

### Comparison Table

| Feature | kube-router | Calico | Cilium | Flannel |
|---------|------------|--------|--------|---------|
| **Architecture** | Single binary | Multiple daemons | Agent + Operator | Single binary |
| **CNI** | Yes (BGP) | Yes (BGP/VXLAN/IPIP) | Yes (eBPF/VXLAN) | Yes (VXLAN) |
| **Service proxy** | Yes (IPVS) | Yes (eBPF/iptables) | Yes (eBPF) | No |
| **NetworkPolicy** | Yes (iptables/ipsets) | Yes (iptables/eBPF) | Yes (eBPF) | No |
| **L7 policy** | No | No (basic) | Yes | No |
| **Encryption** | No | Yes (WireGuard) | Yes (WireGuard/IPsec) | No |
| **Observability** | Basic (metrics) | Flow logs | Hubble (rich) | None |
| **BGP support** | Full mesh + RR | Full mesh + RR + peering | Basic BGP | No |
| **DSR** | Yes | No | Yes | No |
| **eBPF** | No | Optional | Core | No |
| **Memory (per node)** | ~30-50 MB | ~100-200 MB | ~200-400 MB | ~30-50 MB |
| **Maturity** | Medium | High | High | High |
| **CNCF status** | Not CNCF | CNCF Graduated | CNCF Graduated | CNCF project |
| **Best for** | Bare-metal, simple | Enterprise, hybrid | Modern, feature-rich | Development, simple |

---

## Part 7: Monitoring and Troubleshooting

### Prometheus Metrics

Enable metrics by setting `--metrics-port=8080`:

```bash
kube-router --run-service-proxy=true \
            --run-router=true \
            --run-firewall=true \
            --metrics-port=8080
```

Key metrics to monitor:

```bash
# BGP session status
kube_router_bgp_session_up{neighbor="192.168.1.11"} 1

# IPVS connections
kube_router_service_proxy_ipvs_connections_total

# NetworkPolicy rule count
kube_router_firewall_iptables_rules_total

# Controller sync time
kube_router_controller_sync_duration_seconds
```

### Common Troubleshooting

```bash
# 1. Check if BGP peers are established
kubectl -n kube-system exec <kube-router-pod> -- \
  gobgp neighbor
# Look for "Established" state

# 2. Check if IPVS is programming services correctly
kubectl -n kube-system exec <kube-router-pod> -- \
  ipvsadm -Ln
# Every ClusterIP should appear as a virtual server

# 3. Verify routes are learned
ip route show proto 17
# Should see routes to other nodes' pod CIDRs

# 4. Check iptables rules for network policies
kubectl -n kube-system exec <kube-router-pod> -- \
  iptables -L KUBE-ROUTER-INPUT -n -v
# Should show rules matching your NetworkPolicies

# 5. Check ipsets
kubectl -n kube-system exec <kube-router-pod> -- \
  ipset list -name
# Should show sets like KUBE-ROUTER-<hash>

# 6. Check kube-router logs
kubectl -n kube-system logs -l k8s-app=kube-router --tail=50
```

---

## Common Mistakes

| Mistake | Why It Hurts | How to Avoid |
|---------|-------------|--------------|
| **Forgetting to disable kube-proxy** | Both kube-proxy and kube-router try to manage IPVS/iptables rules, causing conflicts and flapping services | Always delete the kube-proxy DaemonSet and clean its rules before enabling kube-router's service proxy |
| **Using full-mesh BGP on 100+ nodes** | BGP session count grows quadratically (n*(n-1)/2). At 100 nodes that is 4,950 sessions, causing CPU and memory pressure | Switch to route reflectors (`--nodes-full-mesh=false`) for clusters larger than 50 nodes |
| **Enabling DSR without understanding limitations** | DSR does not work with NodePort services or when source and destination pods are on the same node (hairpin). Packets may be silently dropped | Test DSR in staging first; only enable for LoadBalancer and ClusterIP services that do not need hairpin |
| **Not enabling `--bgp-graceful-restart`** | When kube-router restarts, BGP sessions drop and routes disappear. Pods lose connectivity for 30-90 seconds until sessions re-establish | Always set `--bgp-graceful-restart=true` to preserve routes during restarts |
| **Mixing CNI plugins** | Running kube-router's router controller alongside Calico or Cilium's routing creates conflicting routes, breaking pod networking | Use only ONE routing solution. If you want kube-router's service proxy only, set `--run-router=false` |
| **Forgetting IPVS kernel modules** | IPVS requires kernel modules (`ip_vs`, `ip_vs_rr`, `ip_vs_wrr`, etc.). If not loaded, kube-router silently falls back to iptables mode | Load IPVS modules at boot: `modprobe ip_vs ip_vs_rr ip_vs_wrr ip_vs_sh` and verify with `lsmod | grep ip_vs` |
| **Not setting `--cluster-asn` in multi-cluster** | Default ASN 64512 is the same for all clusters. If clusters share a network, BGP routes will leak between them causing cross-cluster routing chaos | Use unique ASNs per cluster: `--cluster-asn=64512` for cluster A, `--cluster-asn=64513` for cluster B |
| **Skipping hairpin mode for self-referencing services** | Pods that call their own Service IP (common with leader election and health checks) get packets dropped | Enable `--hairpin-mode=true` if pods need to reach themselves via Service IPs |

---

## Quiz

### Question 1
What are the three controllers inside kube-router, and which Kubernetes component does each replace?

<details>
<summary>Show Answer</summary>

1. **Network Routes Controller** -- Replaces the CNI plugin (Flannel, Calico's routing). Uses BGP to distribute pod CIDR routes between nodes, enabling direct pod-to-pod communication without overlay networks.

2. **Network Services Controller** -- Replaces kube-proxy. Uses IPVS instead of iptables for Service routing, providing O(1) lookup performance and real load-balancing algorithms.

3. **Network Policy Controller** -- Replaces network policy enforcement (which Flannel lacks entirely). Uses iptables with ipsets to implement the standard Kubernetes NetworkPolicy API.

Each controller can be independently enabled or disabled using `--run-router`, `--run-service-proxy`, and `--run-firewall` flags.

</details>

### Question 2
Why does IPVS outperform iptables for service routing at scale? What is the algorithmic difference?

<details>
<summary>Show Answer</summary>

**iptables** processes rules sequentially. Every packet walks the rule chain from top to bottom until a match is found. With 5,000 services generating ~65,000 rules, every single packet must potentially traverse all 65,000 rules. This is **O(n)** where n is the number of rules.

**IPVS** uses hash tables internally. When a packet arrives for a Service IP, IPVS computes a hash of the destination IP and port, then does a single lookup in its hash table. This is **O(1)** -- constant time regardless of whether you have 50 services or 50,000 services.

Additionally, iptables rule updates require rewriting the entire chain (which takes seconds at scale), while IPVS can add/remove individual virtual servers atomically in milliseconds.

</details>

### Question 3
Your 80-node bare-metal cluster uses kube-router with default settings. BGP CPU usage is climbing. What is happening and how do you fix it?

<details>
<summary>Show Answer</summary>

The default setting is full-mesh BGP (`--nodes-full-mesh=true`). With 80 nodes, that creates `80 * 79 / 2 = 3,160` BGP sessions. Each session requires keepalive messages, route updates, and state tracking.

**Fix**: Switch to BGP route reflectors.

1. Designate 2-3 nodes as route reflectors:
```bash
kubectl annotate node rr-node-1 \
  kube-router.io/node.bgp.routereflector.cluster-id=1.0.0.1
kubectl annotate node rr-node-2 \
  kube-router.io/node.bgp.routereflector.cluster-id=1.0.0.1
```

2. Disable full mesh and configure peering:
```bash
kube-router --nodes-full-mesh=false \
            --peer-router-ips=192.168.1.10,192.168.1.11
```

Now each node has only 2 BGP sessions (one per reflector) instead of 79. Total sessions: `80 * 2 = 160` instead of 3,160.

</details>

### Question 4
Explain Direct Server Return (DSR). When would you enable it, and what are its limitations?

<details>
<summary>Show Answer</summary>

**DSR** changes the return path for service traffic. Normally, response packets travel back through the IPVS node that received the original request. With DSR, the backend pod sends its response directly to the client, bypassing the proxy node entirely.

**When to enable DSR**:
- Streaming or download-heavy workloads where response packets are much larger than requests
- High-throughput services where the proxy node becomes a bottleneck
- Latency-sensitive paths where eliminating the extra hop matters

**Limitations**:
- Does not work with NodePort services (the client expects a response from the node's IP)
- Hairpin traffic (pod reaching itself via Service IP) will not work
- Backend pods must be able to route directly to the client (which is usually fine within a cluster)
- Health checks from the proxy node may not work as expected since the response does not return through IPVS
- Not compatible with all scheduling algorithms

</details>

### Question 5
You want to add NetworkPolicy enforcement to a cluster that uses Flannel for CNI and kube-proxy for services. How do you deploy kube-router for this use case?

<details>
<summary>Show Answer</summary>

Deploy kube-router with only the firewall controller enabled:

```bash
# In the kube-router DaemonSet args:
args:
- --run-router=false         # Don't touch routing (Flannel handles it)
- --run-service-proxy=false  # Don't touch services (kube-proxy handles it)
- --run-firewall=true        # Enable NetworkPolicy enforcement
```

This way:
- Flannel continues to manage pod-to-pod networking via VXLAN
- kube-proxy continues to manage Service routing via iptables
- Kube-router watches NetworkPolicy resources and enforces them using iptables + ipsets

This is a common pattern because Flannel has zero NetworkPolicy support. You get policy enforcement without migrating your entire networking stack.

</details>

### Question 6
A team switches from kube-proxy (iptables mode) to kube-router's IPVS service proxy. After the migration, some pods cannot reach themselves via their own Service ClusterIP. What is the issue?

<details>
<summary>Show Answer</summary>

This is the **hairpin problem**. When a pod sends traffic to its own Service ClusterIP, the packet goes to IPVS, which may load-balance it back to the same pod. The packet arrives at the pod with a source IP that is the pod's own IP, which confuses the kernel's connection tracking.

**Fix**: Enable hairpin mode in kube-router:

```bash
kube-router --run-service-proxy=true \
            --hairpin-mode=true
```

Hairpin mode configures the network bridge to allow packets to be sent back out on the same interface they arrived on. This is needed when:
- Pods call their own Service IP (common with leader election, self-health-checks)
- A Service has only one endpoint and that endpoint calls the Service

Kube-proxy in iptables mode handles this automatically via masquerade rules, but IPVS requires explicit hairpin configuration.

</details>

---

## Hands-On Exercise: Deploy Kube-Router on a Kind Cluster

### Objective

Deploy a Kubernetes cluster with kube-router as the networking solution, verify BGP routing, test IPVS service proxying, and enforce a NetworkPolicy.

### Prerequisites

- `kind` installed
- `kubectl` installed
- `docker` installed

### Part 1: Create a Cluster Without Default Networking

```bash
# Create a kind cluster without kube-proxy and default CNI
cat > kind-kube-router.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  kubeProxyMode: none
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/16"
nodes:
- role: control-plane
- role: worker
- role: worker
EOF

kind create cluster --config kind-kube-router.yaml --name kube-router-lab

# Verify nodes are NotReady (no CNI yet)
kubectl get nodes
# NAME                             STATUS     ROLES           AGE   VERSION
# kube-router-lab-control-plane    NotReady   control-plane   30s   v1.31.0
# kube-router-lab-worker           NotReady   <none>          15s   v1.31.0
# kube-router-lab-worker2          NotReady   <none>          15s   v1.31.0
```

### Part 2: Install Kube-Router

```bash
# Deploy kube-router with all features enabled
kubectl apply -f https://raw.githubusercontent.com/cloudnativelabs/kube-router/master/daemonset/kube-router-all-service-daemonset.yaml

# Wait for kube-router pods to be running
kubectl -n kube-system wait --for=condition=Ready \
  pod -l k8s-app=kube-router --timeout=120s

# Verify nodes are now Ready
kubectl get nodes
# NAME                             STATUS   ROLES           AGE   VERSION
# kube-router-lab-control-plane    Ready    control-plane   2m    v1.31.0
# kube-router-lab-worker           Ready    <none>          90s   v1.31.0
# kube-router-lab-worker2          Ready    <none>          90s   v1.31.0
```

### Part 3: Verify BGP Routing

```bash
# Check routing table on a node (via kube-router pod)
KR_POD=$(kubectl -n kube-system get pod -l k8s-app=kube-router \
  -o jsonpath='{.items[0].metadata.name}')

# See the BGP-learned routes (proto 17 = BGP)
kubectl -n kube-system exec $KR_POD -- ip route show proto 17
# Expected output like:
# 10.244.1.0/24 via 172.18.0.3 dev eth0
# 10.244.2.0/24 via 172.18.0.4 dev eth0
```

### Part 4: Deploy Test Workloads and Verify IPVS

```bash
# Create test namespace
kubectl create namespace test

# Deploy a simple web server
kubectl -n test apply -f - << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
EOF

# Wait for pods
kubectl -n test wait --for=condition=Ready pod -l app=web --timeout=60s

# Check IPVS virtual servers -- the web service should appear
kubectl -n kube-system exec $KR_POD -- ipvsadm -Ln | grep -A5 "$(kubectl -n test get svc web -o jsonpath='{.spec.clusterIP}')"
# Expected: virtual server with 3 real servers (one per pod)

# Deploy a client pod and test connectivity
kubectl -n test run client --image=busybox:1.36 --restart=Never -- sleep 3600
kubectl -n test wait --for=condition=Ready pod/client --timeout=30s

# Test service routing
kubectl -n test exec client -- wget -qO- http://web
# Should return nginx welcome page
echo "Service routing via IPVS works!"
```

### Part 5: Test NetworkPolicy Enforcement

```bash
# First, verify the client can reach the web service
kubectl -n test exec client -- wget -qO- --timeout=5 http://web > /dev/null 2>&1 \
  && echo "BEFORE POLICY: client -> web: ALLOWED"

# Apply a default deny policy
kubectl -n test apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF

# Test again -- should be blocked
kubectl -n test exec client -- wget -qO- --timeout=5 http://web > /dev/null 2>&1 \
  || echo "AFTER DENY: client -> web: BLOCKED (expected!)"

# Now allow traffic from client to web
kubectl -n test apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-client-to-web
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          run: client
    ports:
    - protocol: TCP
      port: 80
EOF

# Test again -- should work now
kubectl -n test exec client -- wget -qO- --timeout=5 http://web > /dev/null 2>&1 \
  && echo "AFTER ALLOW: client -> web: ALLOWED (policy working!)"

# Deploy a second client that should NOT have access
kubectl -n test run unauthorized --image=busybox:1.36 --restart=Never -- sleep 3600
kubectl -n test wait --for=condition=Ready pod/unauthorized --timeout=30s

kubectl -n test exec unauthorized -- wget -qO- --timeout=5 http://web > /dev/null 2>&1 \
  || echo "UNAUTHORIZED: unauthorized -> web: BLOCKED (policy enforced!)"
```

### Part 6: Inspect What Kube-Router Created

```bash
# Check ipsets created for the NetworkPolicy
kubectl -n kube-system exec $KR_POD -- ipset list -name 2>/dev/null | head -20

# Check iptables rules
kubectl -n kube-system exec $KR_POD -- \
  iptables -L -n -v 2>/dev/null | grep -A5 "KUBE-ROUTER" | head -30

# Check the number of IPVS services
kubectl -n kube-system exec $KR_POD -- \
  ipvsadm -Ln --stats 2>/dev/null | head -20
```

### Success Criteria

- [ ] Cluster nodes reach `Ready` status with kube-router as CNI
- [ ] BGP routes visible in routing table (`ip route show proto 17`)
- [ ] IPVS virtual servers created for the `web` Service
- [ ] Client pod can reach `web` Service via ClusterIP
- [ ] Default deny policy blocks all ingress traffic
- [ ] Specific allow policy permits `client` to reach `web`
- [ ] Unauthorized pod remains blocked by NetworkPolicy

### Cleanup

```bash
kind delete cluster --name kube-router-lab
```

---

## Further Reading

- [Kube-Router Documentation](https://www.kube-router.io/) -- Official docs with architecture details
- [Kube-Router GitHub](https://github.com/cloudnativelabs/kube-router) -- Source code and issue tracker
- [IPVS-Based In-Cluster Load Balancing Deep Dive](https://kubernetes.io/blog/2018/07/09/ipvs-based-in-cluster-load-balancing-deep-dive/) -- Kubernetes blog on IPVS
- [GoBGP Documentation](https://github.com/osrg/gobgp) -- The BGP library kube-router uses
- [LVS Documentation](http://www.linuxvirtualserver.org/) -- Linux Virtual Server project (IPVS)
- [BGP in the Data Center (O'Reilly)](https://www.oreilly.com/library/view/bgp-in-the/9781491983416/) -- Deep BGP knowledge for networking teams

---

## Next Module

Continue to [Module 5.1: Cilium](../module-5.1-cilium/) for the full-featured eBPF-powered CNI, or explore [Module 5.4: MetalLB](../module-5.4-metallb/) to pair load balancing with kube-router's BGP capabilities.

---

*"Simplicity is the ultimate sophistication. Kube-router proves that one binary, doing three things well, can outperform three binaries each doing one thing poorly."*
