---
title: "Module 3.8: Cluster Networking Data Path"
slug: k8s/cka/part3-services-networking/module-3.8-cluster-networking-data-path
sidebar:
  order: 9
---
> **Complexity**: `[MEDIUM]` - Core troubleshooting topic
>
> **Time to Complete**: ~35 minutes
>
> **Prerequisites**: [Module 3.1 (Services)](../module-3.1-services/), [Module 3.6 (Network Policies)](../module-3.6-network-policies/), [Module 3.7 (CNI)](../module-3.7-cni/)

---

## Why This Module Matters

You can create Services and write NetworkPolicies all day, but when something breaks in production at 3 AM, you need to understand **where packets actually go**. This module teaches you the mental model that turns networking mysteries into solvable puzzles.

> **War Story: The Silent MTU Drop**
>
> A platform team migrated a cluster from Flannel with `host-gw` to Flannel with `vxlan` encapsulation. Everything seemed fine -- small health-check probes succeeded, pod-to-pod pings worked, and Services resolved correctly. But every few minutes, a critical batch job would hang and eventually time out.
>
> After two days of fruitless debugging (restarting pods, checking DNS, blaming the application), a junior engineer ran `tcpdump` on a node and noticed something peculiar: TCP SYN packets crossed nodes fine, but the large data payloads were being silently dropped. The culprit? VXLAN adds a 50-byte header, reducing the effective MTU from 1500 to 1450. The CNI was configured for MTU 1500, so any packet close to the limit was too large for the tunnel, and the `Don't Fragment` bit caused the kernel to drop it silently instead of fragmenting.
>
> The fix was a one-line config change (`"MTU": 1450`), but finding it required understanding the actual data path -- where packets enter the kernel, how they get encapsulated, and where they exit. That is exactly what this module teaches.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Trace a packet from a client pod through kube-proxy rules to a backend pod
- Distinguish between CNI responsibilities and kube-proxy responsibilities
- Explain how CoreDNS resolution works end-to-end
- Use `tcpdump`, `iptables-save`, `conntrack`, and `nslookup` to debug real networking issues
- Apply a systematic troubleshooting mental model for cluster networking

---

## Did You Know?

- **kube-proxy does not proxy anything** (despite its name). In iptables mode, it simply programs DNAT rules in the kernel. Actual packet forwarding is handled entirely by the Linux networking stack -- kube-proxy never sees the data packets themselves.

- **A single Service with 1000 backends generates ~8000 iptables rules** in iptables mode. This is why large clusters (5000+ Services) often switch to IPVS mode or eBPF-based solutions like Cilium, which can handle hundreds of thousands of backends without linear rule scanning.

- **Kubernetes requires a flat network**: every pod must be able to reach every other pod without NAT. This single design decision (documented in the Kubernetes networking model) is what makes the entire Service abstraction possible -- and it is the reason CNI plugins exist.

- **CoreDNS handles roughly 10,000-50,000 queries per second** in a typical production cluster. A single misconfigured `ndots` value can multiply that by 5x, because each lookup triggers search-domain expansion (e.g., `api.example.com` becomes 5 separate DNS queries before the final one succeeds).

---

## Part 1: Service to Pod Flow -- The Packet Walk

Understanding the exact path a packet takes is the foundation of all network troubleshooting. Let's trace a request from Pod A to a ClusterIP Service that routes to Pod B.

### 1.1 ClusterIP Packet Walk

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   ClusterIP Packet Walk (iptables mode)                  │
│                                                                         │
│  Pod A (10.244.1.5)                        Pod B (10.244.2.8)          │
│  ┌─────────────────┐                       ┌─────────────────┐         │
│  │ curl 10.96.0.50 │                       │ nginx :80       │         │
│  └────────┬────────┘                       └────────▲────────┘         │
│           │                                         │                   │
│           ▼                                         │                   │
│  ┌─────────────────┐                       ┌────────┴────────┐         │
│  │ 1. veth pair    │                       │ 7. veth pair    │         │
│  │    (pod → node) │                       │    (node → pod) │         │
│  └────────┬────────┘                       └────────▲────────┘         │
│           │                                         │                   │
│           ▼                                         │                   │
│  ┌─────────────────┐                                │                   │
│  │ 2. iptables     │  PREROUTING chain              │                   │
│  │    DNAT rule    │  dst: 10.96.0.50:80            │                   │
│  │    rewrites dst │  → 10.244.2.8:80               │                   │
│  └────────┬────────┘                                │                   │
│           │                                         │                   │
│           ▼                                         │                   │
│  ┌─────────────────┐                                │                   │
│  │ 3. conntrack    │  Records the NAT               │                   │
│  │    table entry  │  mapping for return             │                   │
│  └────────┬────────┘  traffic                       │                   │
│           │                                         │                   │
│           ▼                                         │                   │
│  ┌─────────────────┐                       ┌────────┴────────┐         │
│  │ 4. Routing      │                       │ 6. Routing      │         │
│  │    decision     │                       │    decision     │         │
│  │    (same node   │──── same node? ──────►│    (deliver     │         │
│  │     or tunnel?) │                       │     locally)    │         │
│  └────────┬────────┘                       └─────────────────┘         │
│           │ different node                                              │
│           ▼                                                             │
│  ┌─────────────────┐                       ┌─────────────────┐         │
│  │ 5a. CNI encap   │ ═══ VXLAN/Geneve ═══►│ 5b. CNI decap   │         │
│  │    (if overlay) │      tunnel           │    (on dst node)│         │
│  └─────────────────┘                       └────────┬────────┘         │
│       Node 1                                        │  Node 2          │
│                                                     └──► step 6        │
└─────────────────────────────────────────────────────────────────────────┘
```

Here is what happens at each step:

1. **veth pair**: The packet leaves Pod A's network namespace through a virtual ethernet pair that connects it to the host (node) network namespace.
2. **iptables DNAT**: kube-proxy has programmed iptables rules. The PREROUTING chain matches the destination `10.96.0.50` (the Service ClusterIP) and rewrites it to a backend pod IP -- say `10.244.2.8`. If multiple backends exist, a random or round-robin selection happens via iptables probability rules.
3. **conntrack**: The kernel's connection tracking module records this NAT mapping. When Pod B replies, conntrack automatically reverses the translation so Pod A sees the response coming from the Service IP, not the pod IP.
4. **Routing decision**: The kernel routes the packet based on the rewritten destination. If Pod B is on the same node, it goes directly to Pod B's veth pair. If Pod B is on another node, it goes to the CNI.
5. **CNI encapsulation**: For overlay networks (VXLAN, Geneve), the CNI wraps the packet in an outer header to tunnel it to the destination node. For routed networks (BGP, host-gw), the kernel forwards it directly.
6. **Delivery**: On the destination node, the packet is decapsulated (if needed) and routed to Pod B's veth pair.
7. **Pod receives**: Pod B sees a packet from Pod A's IP destined for its own IP on port 80.

### 1.2 NodePort Packet Walk

NodePort adds an extra step at the front:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     NodePort Packet Walk                                │
│                                                                         │
│  External Client                                                        │
│  ┌─────────────────┐                                                    │
│  │ curl             │                                                    │
│  │ 192.168.1.10:    │                                                    │
│  │      30080       │                                                    │
│  └────────┬────────┘                                                    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐    Node 1 (192.168.1.10)                          │
│  │ 1. Node eth0    │                                                    │
│  │    receives on  │                                                    │
│  │    port 30080   │                                                    │
│  └────────┬────────┘                                                    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │ 2. iptables     │    KUBE-NODEPORTS chain:                           │
│  │    DNAT         │    dst-port 30080 → 10.96.0.50:80 (ClusterIP)     │
│  │                 │    → then selects backend: 10.244.2.8:80           │
│  └────────┬────────┘                                                    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │ 3. SNAT (maybe) │    If externalTrafficPolicy: Cluster (default)    │
│  │                 │    source is rewritten to node IP so return        │
│  │                 │    traffic comes back through this node            │
│  └────────┬────────┘                                                    │
│           │                                                             │
│           ▼                                                             │
│      (same as ClusterIP flow from step 4 onward)                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key detail**: With `externalTrafficPolicy: Cluster` (the default), kube-proxy SNATs the source address, which means the backend pod sees the node's IP, not the client's real IP. Setting `externalTrafficPolicy: Local` preserves the client IP but only routes to pods on the receiving node -- if none exist there, the connection is dropped.

### 1.3 Hairpin Traffic

When a pod calls its own Service (e.g., a pod behind `web-svc` curls `web-svc`), the packet might get routed back to itself. This is called **hairpin** or **hairpin NAT**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Hairpin Flow                               │
│                                                               │
│  Pod A sends to Service IP                                    │
│       │                                                       │
│       ▼                                                       │
│  iptables DNAT selects... Pod A itself!                       │
│       │                                                       │
│       ▼                                                       │
│  Packet must exit Pod A's netns and re-enter it               │
│  (requires hairpin mode on the bridge/veth)                   │
│                                                               │
│  If hairpin mode is OFF → packet is silently dropped          │
│  If hairpin mode is ON  → packet loops back correctly         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

Most CNI plugins enable hairpin mode by default. If you see intermittent failures where a pod sometimes cannot reach its own Service, hairpin is the likely suspect. Check with:

```bash
# Check hairpin mode on a veth interface
k exec <pod> -- cat /sys/class/net/eth0/brport/hairpin_mode
# Or on the node:
cat /sys/devices/virtual/net/<veth-name>/brport/hairpin_mode
```

---

## Part 2: CNI vs. kube-proxy Responsibilities

This is one of the most misunderstood distinctions in Kubernetes networking. Getting it wrong leads to debugging the wrong component.

### 2.1 Responsibility Split

```
┌─────────────────────────────────────────────────────────────────────────┐
│                CNI vs. kube-proxy: Who Does What?                       │
│                                                                         │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐    │
│  │          CNI Plugin           │  │         kube-proxy            │    │
│  │                               │  │                               │    │
│  │  ✓ Assign pod IPs            │  │  ✓ Service → Pod DNAT        │    │
│  │  ✓ Create veth pairs         │  │  ✓ ClusterIP routing         │    │
│  │  ✓ Configure pod routes      │  │  ✓ NodePort rules            │    │
│  │  ✓ Inter-node tunneling      │  │  ✓ LoadBalancer rules        │    │
│  │    (VXLAN, Geneve, BGP)      │  │  ✓ Session affinity          │    │
│  │  ✓ Network Policy            │  │  ✓ Endpoint selection        │    │
│  │    enforcement (some CNIs)   │  │                               │    │
│  │  ✓ Pod-to-pod connectivity   │  │  ✗ Does NOT assign IPs       │    │
│  │                               │  │  ✗ Does NOT create tunnels   │    │
│  │  ✗ Does NOT handle Services  │  │  ✗ Does NOT enforce policies  │    │
│  │    (unless eBPF replaces     │  │    (except via DNAT rules)    │    │
│  │     kube-proxy, e.g. Cilium) │  │                               │    │
│  └──────────────────────────────┘  └──────────────────────────────┘    │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │              Quick Diagnosis                                   │      │
│  │                                                                │      │
│  │  "Pod A cannot reach Pod B by pod IP"                         │      │
│  │     → Problem is CNI (routing, encapsulation, MTU)            │      │
│  │                                                                │      │
│  │  "Pod A cannot reach Service, but CAN reach Pod B by pod IP"  │      │
│  │     → Problem is kube-proxy (DNAT rules, endpoints)           │      │
│  │                                                                │      │
│  │  "Pod A cannot resolve service-name"                          │      │
│  │     → Problem is CoreDNS (see Part 3)                         │      │
│  │                                                                │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 CNI Quick Matrix

Different CNI plugins take different approaches. Here is a comparison relevant to troubleshooting:

| Feature | Calico | Flannel | Cilium |
|---------|--------|---------|--------|
| **Data plane** | iptables or eBPF | VXLAN or host-gw | eBPF |
| **Default routing** | BGP (no encap) | VXLAN overlay | eBPF direct routing |
| **Network Policies** | Yes (native) | No (needs add-on) | Yes (L3-L7) |
| **Can replace kube-proxy** | Yes (eBPF mode) | No | Yes (kube-proxy replacement) |
| **MTU concern** | None (no encap) | Yes (-50 bytes for VXLAN) | Depends on config |
| **Troubleshooting tool** | `calicoctl node status` | Check VXLAN interface | `cilium status` |

### 2.3 kube-proxy Modes

kube-proxy can operate in different modes. The mode affects how Services are implemented in the kernel:

```bash
# Check which mode kube-proxy is using
k get configmap kube-proxy -n kube-system -o yaml | grep mode

# Or check the kube-proxy logs
k logs -n kube-system -l k8s-app=kube-proxy | head -20
```

| Mode | How It Works | Performance | When to Use |
|------|-------------|-------------|-------------|
| **iptables** | DNAT rules per Service/Endpoint | O(n) rule evaluation | Default, fine for < 5000 Services |
| **IPVS** | Virtual server with real backends | O(1) lookup via hash table | Large clusters (5000+ Services) |
| **nftables** | Next-gen replacement for iptables | Better than iptables | K8s 1.31+ recommended path |

---

## Part 3: DNS Resolution Path (CoreDNS)

DNS is the glue that makes Service names work. When a pod calls `curl web-service`, here is what actually happens.

### 3.1 The Full DNS Resolution Path

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DNS Resolution Path                                   │
│                                                                         │
│  Pod (10.244.1.5)                                                       │
│  ┌──────────────────────────────┐                                       │
│  │ curl http://web-svc          │                                       │
│  │                              │                                       │
│  │ 1. glibc reads               │                                       │
│  │    /etc/resolv.conf:         │                                       │
│  │    nameserver 10.96.0.10     │  ◄── CoreDNS ClusterIP               │
│  │    search default.svc.       │                                       │
│  │      cluster.local           │                                       │
│  │      svc.cluster.local       │                                       │
│  │      cluster.local           │                                       │
│  │    options ndots:5           │                                       │
│  └──────────┬───────────────────┘                                       │
│             │                                                           │
│             │ 2. "web-svc" has 0 dots, which is < ndots (5)            │
│             │    So search domains are tried FIRST:                     │
│             │                                                           │
│             │    Query 1: web-svc.default.svc.cluster.local  ← HIT!    │
│             │    (If miss: web-svc.svc.cluster.local)                   │
│             │    (If miss: web-svc.cluster.local)                       │
│             │    (If miss: web-svc.)  ← absolute query last            │
│             │                                                           │
│             ▼                                                           │
│  ┌──────────────────────────────┐                                       │
│  │ 3. UDP packet to             │                                       │
│  │    10.96.0.10:53             │                                       │
│  │    (CoreDNS ClusterIP)       │                                       │
│  └──────────┬───────────────────┘                                       │
│             │                                                           │
│             ▼                                                           │
│  ┌──────────────────────────────┐                                       │
│  │ 4. kube-proxy DNAT           │                                       │
│  │    10.96.0.10 → 10.244.0.3  │  ◄── Actual CoreDNS pod IP           │
│  └──────────┬───────────────────┘                                       │
│             │                                                           │
│             ▼                                                           │
│  ┌──────────────────────────────┐                                       │
│  │ 5. CoreDNS pod               │                                       │
│  │    - Checks kubernetes       │                                       │
│  │      plugin (in-cluster      │                                       │
│  │      records)                │                                       │
│  │    - Returns A record:       │                                       │
│  │      10.96.45.123            │  ◄── Service ClusterIP               │
│  └──────────┬───────────────────┘                                       │
│             │                                                           │
│             ▼                                                           │
│  Pod receives IP, connects to 10.96.45.123                              │
│  (then the Service → Pod flow from Part 1 takes over)                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 The ndots Trap

The `ndots:5` default in Kubernetes means any name with fewer than 5 dots is treated as a relative name. This triggers search domain expansion:

```bash
# Querying "api.example.com" (2 dots, < 5) generates these lookups:
#   1. api.example.com.default.svc.cluster.local  → NXDOMAIN
#   2. api.example.com.svc.cluster.local           → NXDOMAIN
#   3. api.example.com.cluster.local               → NXDOMAIN
#   4. api.example.com.                            → SUCCESS

# That's 4 DNS queries instead of 1!
```

For pods that frequently call external domains, reduce `ndots` or use trailing dots:

```yaml
# Option 1: Set ndots in pod spec
apiVersion: v1
kind: Pod
metadata:
  name: optimized-dns
spec:
  dnsConfig:
    options:
    - name: ndots
      value: "2"
  containers:
  - name: app
    image: nginx
```

```bash
# Option 2: Use trailing dot (absolute name, skips search)
curl http://api.example.com.
#                           ^ trailing dot = absolute, no search expansion
```

### 3.3 Common DNS Failure Modes

| Symptom | Likely Cause | How to Check |
|---------|-------------|--------------|
| All DNS fails | CoreDNS pods down | `k get pods -n kube-system -l k8s-app=kube-dns` |
| Intermittent DNS timeouts | CoreDNS overloaded or NetworkPolicy blocking UDP/53 | `k top pods -n kube-system`, check policies |
| External names fail | CoreDNS cannot reach upstream DNS | Check CoreDNS `forward` plugin config, node DNS |
| Cross-namespace fails | Wrong FQDN or search domain | Use full FQDN: `svc.ns.svc.cluster.local` |
| DNS works, connection fails | DNS is fine, problem is Service/CNI | `nslookup` succeeds but `curl` fails = not DNS |

```bash
# Quick DNS health check from any pod
k run dns-check --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup kubernetes.default

# Check CoreDNS logs for errors
k logs -n kube-system -l k8s-app=kube-dns --tail=50
```

---

## Part 4: Troubleshooting Mental Model

When networking breaks, you need a systematic approach. Do not guess -- follow the packet.

### 4.1 The Three-Layer Diagnosis

```
┌─────────────────────────────────────────────────────────────────────────┐
│             Networking Troubleshooting Decision Tree                     │
│                                                                         │
│  "Pod A cannot reach Service X"                                         │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────┐                                    │
│  │ Layer 1: DNS                     │                                    │
│  │ Can Pod A resolve the name?      │                                    │
│  │ nslookup <service>               │                                    │
│  └──────┬──────────┬───────────────┘                                    │
│      NO │          │ YES                                                │
│         │          │                                                    │
│         ▼          ▼                                                    │
│  Check CoreDNS     │                                                    │
│  pods, resolv.conf │                                                    │
│  NetworkPolicy     │                                                    │
│  on UDP/53         │                                                    │
│                    │                                                    │
│  ┌─────────────────▼───────────────┐                                    │
│  │ Layer 2: Service (kube-proxy)    │                                    │
│  │ Does the Service have endpoints? │                                    │
│  │ k get endpoints <service>        │                                    │
│  └──────┬──────────┬───────────────┘                                    │
│      NO │          │ YES                                                │
│         │          │                                                    │
│         ▼          ▼                                                    │
│  Check selector    │                                                    │
│  matches, pod      │                                                    │
│  readiness probes  │                                                    │
│                    │                                                    │
│  ┌─────────────────▼───────────────┐                                    │
│  │ Layer 3: Pod-to-Pod (CNI)        │                                    │
│  │ Can Pod A reach the endpoint     │                                    │
│  │ IP directly?                     │                                    │
│  │ curl <endpoint-ip>:<port>        │                                    │
│  └──────┬──────────┬───────────────┘                                    │
│      NO │          │ YES                                                │
│         │          │                                                    │
│         ▼          ▼                                                    │
│  CNI issue:        Pod is not                                           │
│  routes, encap,    listening on                                         │
│  MTU, Network      the port or                                          │
│  Policies          app is broken                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Essential Debugging Commands

```bash
# === Layer 1: DNS ===
# Test DNS from inside a pod
k run debug --rm -it --image=busybox:1.36 --restart=Never -- nslookup web-svc

# Check resolv.conf inside a pod
k exec <pod> -- cat /etc/resolv.conf

# === Layer 2: Service / kube-proxy ===
# Check endpoints exist
k get endpoints <service-name>

# Check iptables rules for a specific service (on the node)
iptables-save | grep <service-name>

# Check conntrack table for stale entries
conntrack -L -d <service-clusterip>

# === Layer 3: Pod-to-Pod / CNI ===
# Test direct pod-to-pod connectivity
k run debug --rm -it --image=busybox:1.36 --restart=Never -- \
  wget -qO- --timeout=5 http://<pod-ip>:<port>

# Capture packets on a node (run on the node, not in a pod)
tcpdump -i any -nn host <pod-ip> and port <port>

# Check MTU
k exec <pod> -- ip link show eth0
# Look for "mtu" value -- should match CNI config

# Check routes inside a pod
k exec <pod> -- ip route
```

### 4.3 Conntrack: The Hidden State

Conntrack (connection tracking) is the kernel module that makes NAT work. It remembers which connections map to which translations. Stale conntrack entries are a common source of mysterious failures:

```bash
# List all conntrack entries for a Service IP
conntrack -L -d 10.96.0.50

# Count entries (high numbers may indicate connection leak)
conntrack -C

# Delete stale entries (careful in production)
conntrack -D -d 10.96.0.50 -p tcp --dport 80
```

**When conntrack bites you**: If a pod is deleted and recreated with the same IP (rare but possible), conntrack may still have entries pointing to the old connection state. Symptoms include connections that hang or reset for no apparent reason, but only to specific pods.

### 4.4 Cross-Node Drop Checklist

When packets are dropped between nodes, work through this list:

1. **MTU mismatch**: Does the CNI use encapsulation? If so, is the MTU reduced accordingly?
   ```bash
   # Check MTU on pod interface vs node tunnel interface
   ip link show vxlan.calico  # or flannel.1, cilium_vxlan
   ```

2. **Firewall rules**: Are the node firewalls (iptables, firewalld, cloud security groups) allowing the CNI protocol?
   - VXLAN: UDP port 4789
   - Geneve: UDP port 6081
   - BGP: TCP port 179
   - Wireguard: UDP port 51820

3. **CNI health**: Is the CNI daemon running on all nodes?
   ```bash
   k get pods -n kube-system -l k8s-app=calico-node  # or flannel, cilium
   ```

4. **IP exhaustion**: Has the pod CIDR run out of IPs on a specific node?
   ```bash
   k describe node <node> | grep -A5 "PodCIDR"
   ```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Debugging DNS when the issue is kube-proxy | Wasted time on wrong layer | Follow the three-layer model: DNS first, then Service, then CNI |
| Ignoring MTU after switching CNI modes | Large packets silently dropped | Always set MTU = physical MTU minus encap overhead (50 for VXLAN) |
| Not checking conntrack | Stale NAT entries cause intermittent failures | Use `conntrack -L` to inspect state when connections hang |
| Forgetting `externalTrafficPolicy` | Client source IP lost, or no backends on node | Understand `Cluster` (SNAT, all backends) vs `Local` (preserves IP, local only) |
| Setting `ndots` too high | DNS query amplification, slow lookups | Use `ndots: 2` for pods calling external services, or use trailing dots |
| Testing from outside the cluster for ClusterIP | Connection timeout | ClusterIP only works inside the cluster; use NodePort/port-forward for external tests |
| Running tcpdump on wrong interface | Captures show nothing | Use `tcpdump -i any` to capture on all interfaces, then narrow down |
| Blaming the application before checking the network | Hours wasted debugging app code | Always verify network connectivity first with simple tools (`wget`, `curl`) |

---

## Quiz

**1. A pod can reach another pod by its IP (10.244.2.8), but cannot reach it via the Service ClusterIP (10.96.0.50). Which component is most likely at fault?**

<details>
<summary>Answer</summary>

**kube-proxy** is most likely at fault. Since pod-to-pod connectivity works, the CNI is functioning correctly. The Service ClusterIP is handled by kube-proxy's iptables/IPVS/nftables rules. Check:
- `k get endpoints <service>` -- are there endpoints?
- `iptables-save | grep <service-name>` -- are the DNAT rules present?
- Is kube-proxy running? `k get pods -n kube-system -l k8s-app=kube-proxy`

</details>

**2. You switch your CNI from Flannel with `host-gw` to Flannel with `vxlan`. Small requests (health checks, pings) work fine, but large HTTP responses are dropped. What is the likely cause and fix?**

<details>
<summary>Answer</summary>

**MTU mismatch**. VXLAN encapsulation adds a 50-byte header. If the pod MTU is still 1500 (the default for `host-gw`), packets near 1500 bytes will exceed the tunnel's capacity after encapsulation.

Fix: Set the CNI MTU to 1450 (1500 - 50 for VXLAN overhead). In Flannel's ConfigMap:
```json
{
  "Network": "10.244.0.0/16",
  "Backend": {
    "Type": "vxlan",
    "MTU": 1450
  }
}
```
Then restart the Flannel pods so all nodes pick up the new MTU.

</details>

**3. A developer reports that `curl api.external.com` from a pod takes 2 seconds, but only 50ms from their laptop. DNS is the bottleneck. Explain why and how to fix it.**

<details>
<summary>Answer</summary>

The default `ndots:5` in Kubernetes means `api.external.com` (2 dots, which is less than 5) is treated as a relative name. The resolver tries these lookups in order before succeeding:
1. `api.external.com.default.svc.cluster.local` -- NXDOMAIN (~500ms)
2. `api.external.com.svc.cluster.local` -- NXDOMAIN (~500ms)
3. `api.external.com.cluster.local` -- NXDOMAIN (~500ms)
4. `api.external.com.` -- SUCCESS (~50ms)

That is 3 wasted queries adding ~1.5 seconds of latency.

Fixes (pick one):
- Use a trailing dot: `curl api.external.com.`
- Set `dnsConfig.options.ndots: 2` in the pod spec
- Use the FQDN with trailing dot in application configuration

</details>

**4. You run `k get endpoints my-service` and see `<none>`. The pods are running and have the correct labels. What else could cause empty endpoints?**

<details>
<summary>Answer</summary>

Even if pods are running with correct labels, endpoints will be empty if:

1. **Pods are not Ready** -- the readiness probe is failing. Only pods that pass their readiness probe are added to the Endpoints object. Check: `k get pods` (look for `0/1 READY`).
2. **The Service selector requires labels the pods do not have** -- double check with `k describe svc my-service` and compare against `k get pods --show-labels`.
3. **The pods are in a different namespace** than the Service. Services only select pods in their own namespace.
4. **The endpoint controller is not running** -- extremely rare, but check the kube-controller-manager pod in `kube-system`.

Most commonly, the answer is failed readiness probes.

</details>

**5. After deleting and recreating a backend pod, some existing connections to the Service hang for 30+ seconds before recovering. New connections work fine. What is happening?**

<details>
<summary>Answer</summary>

**Stale conntrack entries**. The kernel's connection tracking table still has entries mapping existing connections to the old pod's IP. Since that IP no longer exists (or belongs to a different pod), packets are being sent into a void.

The entries will eventually expire (TCP timeout, typically 120 seconds for established connections), which is why it eventually recovers. New connections work because they create fresh conntrack entries pointing to valid backends.

To fix immediately: `conntrack -D -d <service-clusterip> -p tcp --dport <port>`. To prevent: use graceful pod termination (preStop hooks, connection draining) so the pod removes itself from endpoints before the process exits.

</details>

---

## Hands-On Exercise: Packet Trace Challenge

**Objective**: Trace a request end-to-end from a client pod through DNS, kube-proxy, and CNI to a backend pod. You will use `tcpdump`, `nslookup`, and `iptables-save` to observe each layer.

**Environment**: kind or minikube cluster (single node is fine for this exercise).

### Setup

```bash
# Create a backend deployment and service
k create deployment trace-backend --image=nginx --replicas=2
k expose deployment trace-backend --port=80 --name=trace-svc

# Wait for pods to be ready
k wait --for=condition=ready pod -l app=trace-backend --timeout=60s

# Create a debug pod that stays running
k run trace-client --image=nicolaka/netshoot --restart=Never -- sleep 3600

# Wait for it
k wait --for=condition=ready pod/trace-client --timeout=60s
```

### Step 1: Inspect the DNS Layer

```bash
# Check the client pod's DNS config
k exec trace-client -- cat /etc/resolv.conf
# Note: nameserver should be the CoreDNS ClusterIP

# Resolve the service name
k exec trace-client -- nslookup trace-svc
# Should return the ClusterIP of trace-svc

# Try the FQDN
k exec trace-client -- nslookup trace-svc.default.svc.cluster.local

# Compare: resolve with trailing dot (skips search domains)
k exec trace-client -- nslookup trace-svc.default.svc.cluster.local.
```

**Record**: What IP did `trace-svc` resolve to? This is the ClusterIP.

### Step 2: Inspect the Service Layer

```bash
# Get the Service details
k get svc trace-svc -o wide

# Get the endpoints (backend pod IPs)
k get endpoints trace-svc

# Look at iptables rules for this service (requires node access)
# On minikube: minikube ssh
# On kind: docker exec -it <node-container> bash
# Then run:
iptables-save | grep trace-svc
# You should see KUBE-SERVICES, KUBE-SVC-*, and KUBE-SEP-* chains

# The KUBE-SVC chain contains probability rules for load balancing
# The KUBE-SEP chains contain the DNAT rules to specific pod IPs
```

**Record**: How many KUBE-SEP entries exist? Should match your replica count (2).

### Step 3: Trace the Packet with tcpdump

```bash
# In one terminal, start tcpdump on the node (requires node access)
# On kind: docker exec -it <node-container> bash
tcpdump -i any -nn port 80 and host $(k get pod trace-client -o jsonpath='{.status.podIP}')

# In another terminal, make a request from the client pod
k exec trace-client -- curl -s http://trace-svc

# Observe the tcpdump output:
# 1. You should see the initial SYN from trace-client IP to ClusterIP
# 2. Then the DNAT'd packet from trace-client IP to a backend pod IP
# 3. The response from the backend pod IP to trace-client IP
# 4. Conntrack reverses the NAT, so trace-client sees the ClusterIP
```

### Step 4: Inspect conntrack

```bash
# On the node, check conntrack entries
conntrack -L -d $(k get svc trace-svc -o jsonpath='{.spec.clusterIP}') 2>/dev/null

# You should see entries showing:
# src=<client-pod-ip> dst=<clusterIP> dport=80
# and the reply mapping:
# src=<backend-pod-ip> dst=<client-pod-ip>
```

### Step 5: Test Network Policy Impact

```bash
# Apply a policy that blocks traffic to the backend
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-trace-backend
spec:
  podSelector:
    matchLabels:
      app: trace-backend
  policyTypes:
  - Ingress
  ingress: []   # Empty = deny all ingress
EOF

# Try the request again (should fail/timeout)
k exec trace-client -- curl -s --connect-timeout 5 http://trace-svc
# Expected: timeout or connection refused (depends on CNI)

# Check DNS still works (it should, DNS goes to CoreDNS, not backend)
k exec trace-client -- nslookup trace-svc

# Remove the policy
k delete networkpolicy deny-trace-backend

# Verify connectivity is restored
k exec trace-client -- curl -s --connect-timeout 5 http://trace-svc
```

### Cleanup

```bash
k delete pod trace-client --force
k delete deployment trace-backend
k delete svc trace-svc
```

**Success Criteria**:
- [ ] Can identify the ClusterIP from DNS resolution
- [ ] Can find iptables DNAT rules for a Service
- [ ] Can observe the packet flow in tcpdump (pre-DNAT and post-DNAT)
- [ ] Can inspect conntrack entries for active connections
- [ ] Understand that NetworkPolicy blocks pod-to-pod traffic but not DNS
- [ ] Can articulate the three-layer troubleshooting model (DNS, Service, CNI)

---

## Key Takeaways

1. **Follow the packet, not your assumptions**. Use `tcpdump`, `iptables-save`, and `conntrack` to see what is actually happening instead of guessing.
2. **The three layers** (DNS, kube-proxy/Service, CNI/pod-to-pod) are independent. Isolate which layer is broken before deep-diving.
3. **MTU matters**. Any time encapsulation is involved, the effective MTU decreases. Silent drops on large packets are the classic symptom.
4. **conntrack is invisible but critical**. It maintains NAT state for every connection through a Service. Stale entries cause some of the most confusing intermittent failures.
5. **ndots:5 is expensive**. For workloads calling external services, either reduce `ndots` or use trailing dots on domain names.

---

## Further Reading

- [Module 3.1: Services Deep-Dive](../module-3.1-services/) - Service types, selectors, and endpoints
- [Module 3.6: Network Policies](../module-3.6-network-policies/) - How policies interact with the data path
- [Module 3.7: CNI Plugins](../module-3.7-cni/) - Deep-dive into CNI architecture and configuration
- [Module 3.3: DNS in Kubernetes](../module-3.3-dns/) - Full CoreDNS configuration and troubleshooting

---

## Next Module

[Module 3.3: DNS in Kubernetes](../module-3.3-dns/) - Deep-dive into CoreDNS configuration, custom DNS policies, and advanced troubleshooting.
