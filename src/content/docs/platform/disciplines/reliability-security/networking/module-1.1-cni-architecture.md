---
title: "Module 1.1: CNI Architecture & Selection"
slug: platform/disciplines/reliability-security/networking/module-1.1-cni-architecture
sidebar:
  order: 2
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 55-65 min

## Prerequisites

Before starting this module:
- **Required**: [Kubernetes Basics](../../../../prerequisites/kubernetes-basics/) — Pod, Service, and Namespace concepts
- **Required**: [Advanced Networking foundations](../../../foundations/advanced-networking/) — IP addressing, routing, overlay networks
- **Recommended**: Linux networking fundamentals (network namespaces, iptables, bridges)
- **Helpful**: Experience running a Kubernetes cluster (kind, minikube, or kubeadm)

---

## Why This Module Matters

In March 2023, a fintech company migrated their 200-node production cluster from Flannel to Calico to gain network policy support. The migration seemed straightforward — swap the CNI plugin, restart nodes in a rolling fashion, done. Twelve minutes into the migration, every Pod on the third node batch lost connectivity. The CNI's IPAM (IP Address Management) assigned IPs from the old Flannel CIDR range that Calico didn't recognize. The cross-node Pod traffic that had been flowing through VXLAN tunnels now tried to route through BGP peering that hadn't fully converged. The outage lasted 94 minutes and affected every customer-facing service.

The root cause wasn't a bug in either CNI. It was a fundamental misunderstanding of how CNI plugins interact with the Linux networking stack. The team treated "swap out one binary for another" like changing a database driver. In reality, CNI plugins rewire your node's entire network topology — bridges, routes, iptables rules, tunnel interfaces, and IP allocation tables all change.

After this module, you'll understand exactly what happens when a Pod gets an IP address, how different CNI plugins implement Pod-to-Pod connectivity, and how to make an informed choice (or migration) without nuking your cluster's network.

---

## Did You Know?

> The CNI specification is remarkably small — just 5 operations: ADD, DEL, CHECK, VERSION, and GC. Every CNI plugin, from Flannel's 2,000 lines of Go to Cilium's 500,000+, implements this same minimal interface. The complexity lives entirely in what happens *after* the CNI binary is invoked.

> Cilium processes over 1 million packets per second per node using eBPF programs attached directly to the Linux kernel's network hooks. Traditional iptables-based CNIs like Calico (in iptables mode) rebuild the entire rule table on every Service change — a 5,000-Service cluster can have 40,000+ iptables rules.

> AWS EKS, GKE, and AKS all ship with their own CNI plugins (aws-vpc-cni, GKE dataplane v2/Cilium, Azure CNI). These are tightly integrated with the cloud provider's VPC networking and cannot be easily swapped without losing cloud-specific features like native VPC routing and security groups.

> The CNI `GC` (garbage collection) verb was only added in CNI spec v1.1.0 (2023). Before that, if a container runtime crashed between creating and registering a network interface, the orphaned interface and IP address leaked permanently. Clusters running for months would accumulate hundreds of zombie veth pairs.

---

## How CNI Plugins Work

### The Container Runtime to CNI Interface

When kubelet needs to start a Pod, it doesn't set up networking itself. It delegates to a CNI plugin through a well-defined contract:

```
┌─────────────────────────────────────────────────────────────┐
│                        kubelet                               │
│  1. Creates Pod sandbox (pause container)                    │
│  2. Creates network namespace                                │
│  3. Calls CNI binary with ADD command                        │
└────────────────────────┬────────────────────────────────────┘
                         │  stdin: JSON config
                         │  env: CNI_COMMAND=ADD
                         │       CNI_CONTAINERID=...
                         │       CNI_NETNS=/proc/.../ns/net
                         │       CNI_IFNAME=eth0
                         v
┌─────────────────────────────────────────────────────────────┐
│                    CNI Plugin Binary                          │
│  1. Reads config from stdin                                  │
│  2. Creates veth pair                                        │
│  3. Moves one end into Pod namespace                         │
│  4. Assigns IP (via IPAM)                                    │
│  5. Sets up routes                                           │
│  6. Returns IP/gateway to kubelet on stdout                  │
└─────────────────────────────────────────────────────────────┘
```

The CNI configuration lives in `/etc/cni/net.d/` and the binaries in `/opt/cni/bin/`:

```bash
# View CNI configuration on a node
ls /etc/cni/net.d/
# 10-calico.conflist  (or 10-flannel.conflist, 05-cilium.conflist)

# View installed CNI binaries
ls /opt/cni/bin/
# bandwidth  bridge  calico  calico-ipam  flannel  host-local
# loopback  portmap  tuning  vrf
```

### CNI Plugin Chain

CNI plugins can be chained — each performs one job:

```json
{
  "cniVersion": "1.0.0",
  "name": "k8s-pod-network",
  "plugins": [
    {
      "type": "calico",
      "ipam": { "type": "calico-ipam" },
      "policy": { "type": "k8s" }
    },
    {
      "type": "bandwidth",
      "capabilities": { "bandwidth": true }
    },
    {
      "type": "portmap",
      "capabilities": { "portMappings": true }
    }
  ]
}
```

In this example: Calico handles the core networking, the bandwidth plugin enforces Pod-level rate limits, and portmap handles hostPort mappings.

### The Lifecycle of a Pod IP

Understanding the full path helps you troubleshoot:

```
Pod creation:
  1. kubelet creates pause container → new network namespace
  2. CNI ADD called → veth pair created
  3. eth0 (Pod side) gets IP from IPAM
  4. Routes added: default via gateway, pod CIDR routes
  5. Node's routing table updated (BGP or tunnel entries)
  6. Pod containers start, sharing the pause container's namespace

Pod deletion:
  7. Containers stop
  8. CNI DEL called → veth pair destroyed
  9. IPAM releases IP back to pool
  10. Routes cleaned up
```

```bash
# Inspect a Pod's network namespace
POD_PID=$(crictl inspect $(crictl ps --name my-app -q) | jq .info.pid)
nsenter -t $POD_PID -n ip addr show
nsenter -t $POD_PID -n ip route show

# See the veth pair on the host side
ip link show type veth
# Output: cali1234abcd@if3: <BROADCAST,MULTICAST,UP>
```

---

## CNI Plugin Deep Dive

### Flannel: The Simple Overlay

Flannel is the simplest CNI — it only handles L3 Pod-to-Pod connectivity using an overlay network. It does NOT support network policies natively.

**How Flannel works (VXLAN mode):**

```
Node A (10.244.0.0/24)              Node B (10.244.1.0/24)
┌──────────────────────┐            ┌──────────────────────┐
│  Pod A: 10.244.0.5   │            │  Pod B: 10.244.1.12  │
│    │                  │            │    │                  │
│    └── cni0 (bridge)  │            │    └── cni0 (bridge)  │
│         │             │            │         │             │
│    flannel.1 (vxlan)  │            │    flannel.1 (vxlan)  │
│         │             │            │         │             │
│    eth0: 192.168.1.10 │            │    eth0: 192.168.1.11 │
└─────────┼─────────────┘            └─────────┼─────────────┘
          │        VXLAN tunnel (UDP 8472)      │
          └────────────────────────────────────┘
```

Flannel allocates a /24 subnet per node from the cluster CIDR, uses a bridge on each node, and encapsulates cross-node traffic in VXLAN packets.

```yaml
# Flannel DaemonSet (typical deployment via kube-flannel.yml)
# Key config in ConfigMap:
apiVersion: v1
kind: ConfigMap
metadata:
  name: kube-flannel-cfg
  namespace: kube-flannel
data:
  net-conf.json: |
    {
      "Network": "10.244.0.0/16",
      "EnableNFTables": true,
      "Backend": {
        "Type": "vxlan",
        "VNI": 1,
        "Port": 8472
      }
    }
```

**When to use Flannel**: Development clusters, environments with no network policy needs, or extremely resource-constrained nodes. Flannel's CPU/memory overhead is near zero.

### Calico: The Enterprise Workhorse

Calico offers three networking modes, rich network policy, and can run with or without an overlay:

| Mode | How It Works | Performance | Use Case |
|------|-------------|-------------|----------|
| **BGP (no overlay)** | Peers with ToR switches via BGP | Fastest (native routing) | On-prem with BGP-capable switches |
| **VXLAN overlay** | Encapsulates cross-node traffic | Good (~5% overhead) | Cloud/on-prem without BGP |
| **IPinIP** | IP-in-IP encapsulation | Good (~3% overhead) | Legacy; VXLAN preferred now |
| **eBPF dataplane** | Replaces iptables with eBPF | Excellent at scale | High-performance clusters |

```yaml
# Calico Installation with Tigera Operator (recommended for 1.31+)
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  calicoNetwork:
    ipPools:
      - name: default-ipv4-ippool
        cidr: 10.244.0.0/16
        encapsulation: VXLAN
        natOutgoing: Enabled
        nodeSelector: all()
    linuxDataplane: BPF    # Use eBPF dataplane
    bgp: Disabled           # Disable BGP when using VXLAN
  typhaDeployment:
    spec:
      template:
        spec:
          tolerations:
            - effect: NoSchedule
              operator: Exists
```

```bash
# Install Calico with Tigera Operator
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.29/manifests/tigera-operator.yaml

# Verify installation
kubectl get pods -n calico-system
kubectl get ippool -o yaml

# Check BGP peering (if using BGP mode)
calicoctl node status
# Returns: peering state with neighbor nodes

# View Calico's eBPF programs (if BPF dataplane)
tc filter show dev eth0 ingress
```

### Cilium: The eBPF-Native CNI

Cilium is built from the ground up on eBPF. Instead of iptables rules, it attaches eBPF programs to kernel hooks that process packets at near-wire speed.

```
Traditional (iptables)              Cilium (eBPF)
┌─────────────────────┐            ┌──────────────────────┐
│ Packet arrives      │            │ Packet arrives       │
│   │                 │            │   │                  │
│   v                 │            │   v                  │
│ PREROUTING chain    │            │ eBPF tc-ingress      │
│   │                 │            │ (single program      │
│   v                 │            │  handles routing,    │
│ FORWARD chain       │            │  policy, NAT, LB)    │
│   │                 │            │   │                  │
│   v                 │            │   v                  │
│ POSTROUTING chain   │            │ Delivered to Pod     │
│   │                 │            │                      │
│   v                 │            │ Kernel version: 5.10+│
│ (40,000+ rules)     │            │                      │
└─────────────────────┘            └──────────────────────┘
```

```bash
# Install Cilium via Helm (K8s 1.31+)
helm repo add cilium https://helm.cilium.io/
helm install cilium cilium/cilium --version 1.16.5 \
  --namespace kube-system \
  --set kubeProxyReplacement=true \
  --set k8sServiceHost=${API_SERVER_IP} \
  --set k8sServicePort=6443 \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true

# Verify Cilium status
cilium status
# Output shows: OK for all components

# View eBPF maps and programs
cilium bpf endpoint list
cilium bpf ct list global | head -20

# Hubble: observe network flows in real time
hubble observe --namespace production --protocol TCP
hubble observe --verdict DROPPED  # See blocked traffic
```

**Cilium's killer features:**

| Feature | Description |
|---------|-------------|
| **L7 network policies** | Filter by HTTP method, path, headers — not just L3/L4 |
| **Hubble observability** | Real-time network flow visibility without tcpdump |
| **kube-proxy replacement** | eBPF-based Service routing (no iptables) |
| **Bandwidth Manager** | EDT-based rate limiting with BBR support |
| **Transparent encryption** | WireGuard or IPsec between nodes |
| **Service mesh** | Sidecarless L7 traffic management |
| **ClusterMesh** | Multi-cluster connectivity |

---

## CNI Comparison Matrix

| Criteria | Flannel | Calico | Cilium |
|----------|---------|--------|--------|
| **Network Policy** | None | L3/L4 (+ L7 with Envoy) | L3/L4/L7 native |
| **Dataplane** | iptables/nftables | iptables, eBPF, or nftables | eBPF |
| **Encryption** | None | WireGuard | WireGuard, IPsec |
| **Overlay modes** | VXLAN, host-gw | VXLAN, IPinIP, none (BGP) | VXLAN, Geneve, native |
| **kube-proxy replacement** | No | Yes (eBPF mode) | Yes |
| **Observability** | None | Basic flow logs | Hubble (deep L7) |
| **Multi-cluster** | No | Federation (Enterprise) | ClusterMesh |
| **Min kernel** | 3.10 | 3.10 (iptables), 5.3 (eBPF) | 5.4 (5.10+ recommended) |
| **Memory per node** | ~15 MB | ~60-120 MB | ~150-300 MB |
| **CNCF status** | Sandbox | None (Tigera) | Graduated |
| **Best for** | Dev/test, simple setups | Enterprise, BGP environments | Modern, eBPF-capable |

### Performance Benchmarks (Approximate)

These vary enormously by hardware, kernel version, and workload. Use them as relative guidance only:

| Scenario | Flannel VXLAN | Calico BGP | Calico eBPF | Cilium eBPF |
|----------|:------------:|:----------:|:-----------:|:-----------:|
| TCP throughput (% of bare metal) | ~92% | ~98% | ~97% | ~97% |
| Latency overhead (P99) | +15-25 us | +3-5 us | +5-8 us | +5-8 us |
| New connections/sec (10K Services) | ~45K | ~65K | ~120K | ~130K |
| Memory at 500 nodes | Low | Medium | Medium | Medium-High |

---

## Choosing the Right CNI

### Decision Framework

```
Start here:
  │
  ├── Development/test cluster?
  │     └── YES → Flannel (simplest, lowest overhead)
  │
  ├── Need network policies?
  │     └── YES → Calico or Cilium
  │           │
  │           ├── Need L7 policies (HTTP path/method filtering)?
  │           │     └── YES → Cilium
  │           │
  │           ├── Running on-prem with BGP-capable switches?
  │           │     └── YES → Calico (BGP mode, no overlay)
  │           │
  │           └── Kernel 5.10+ available?
  │                 ├── YES → Cilium (best observability, performance)
  │                 └── NO → Calico (iptables mode)
  │
  ├── Running on managed K8s (EKS/GKE/AKS)?
  │     └── Consider the cloud CNI first (best VPC integration)
  │         Then evaluate Calico or Cilium as add-on/replacement
  │
  └── Multi-cluster networking needed?
        └── YES → Cilium ClusterMesh (easiest)
              or Calico Federation (Enterprise license)
```

### Cloud Provider CNI Considerations

| Provider | Default CNI | Pod IP Model | Swap Possible? |
|----------|------------|-------------|----------------|
| **EKS** | aws-vpc-cni | VPC-native (ENI) | Yes, but lose SG-for-Pods |
| **GKE** | GKE Dataplane v2 (Cilium) | VPC-native | Standard: yes. Autopilot: no |
| **AKS** | Azure CNI | VNet-native or overlay | Yes (kubenet or Cilium) |

---

## CNI Migration Strategies

Migrating CNI plugins is one of the most dangerous cluster operations. There is no in-place swap — the cluster must be drained and rebuilt.

### Strategy 1: Rolling Node Replacement (Recommended)

```bash
# For each node (start with non-critical workloads):

# 1. Cordon the node
kubectl cordon node-03

# 2. Drain all Pods
kubectl drain node-03 --ignore-daemonsets --delete-emptydir-data --timeout=120s

# 3. Stop kubelet
ssh node-03 "sudo systemctl stop kubelet"

# 4. Remove old CNI config and state
ssh node-03 "sudo rm -rf /etc/cni/net.d/*"
ssh node-03 "sudo rm -rf /var/lib/cni/"
ssh node-03 "sudo rm -rf /var/run/calico/"  # if migrating FROM calico

# 5. Clean up old network interfaces
ssh node-03 "sudo ip link delete flannel.1 2>/dev/null; sudo ip link delete cni0 2>/dev/null"

# 6. Install new CNI (e.g., Cilium DaemonSet will deploy to this node)
ssh node-03 "sudo systemctl start kubelet"

# 7. Wait for new CNI pod to be ready
kubectl wait --for=condition=ready pod -l k8s-app=cilium -n kube-system \
  --field-selector spec.nodeName=node-03 --timeout=120s

# 8. Uncordon
kubectl uncordon node-03

# 9. Verify Pod connectivity from this node before proceeding
kubectl run test-net --image=busybox:1.36 --overrides='{"spec":{"nodeName":"node-03"}}' \
  --rm -it --restart=Never -- wget -qO- http://kubernetes.default.svc.cluster.local/healthz
```

### Strategy 2: Blue-Green Cluster (Safest)

Build a new cluster with the target CNI, migrate workloads via DNS cutover or load balancer switching. More expensive but zero-risk to the existing cluster.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Running Flannel and expecting network policies to work | Flannel has no policy engine; `NetworkPolicy` resources are silently ignored | Use Calico or Cilium, or add Calico as a policy-only addon alongside Flannel |
| Choosing a CNI without checking kernel version | Cilium eBPF requires 5.4+, Calico eBPF needs 5.3+; old distros ship 4.x | Run `uname -r` on all nodes; upgrade kernel first or choose iptables-based CNI |
| Overlapping Pod CIDR with node/service network | Cluster bootstrapped with default CIDR that collides with corporate LAN | Plan CIDRs carefully at cluster creation; use `--pod-network-cidr` and `--service-cidr` flags |
| Not monitoring IPAM exhaustion | Each node gets a /24 (256 IPs) by default; high-density nodes run out | Configure IPAM with larger node allocations or use Calico/Cilium's per-node pool sizing |
| Migrating CNI without draining nodes first | Assuming CNI swap is like upgrading a DaemonSet | Always drain, clean old state, then restart — treat it as a node rebuild |
| Ignoring MTU configuration | VXLAN/Geneve adds 50-byte overhead; jumbo frames not supported in some clouds | Set MTU explicitly in CNI config: typically 1450 for VXLAN, 1500 for native routing |
| Using IPinIP when VXLAN is better | IPinIP is Calico-legacy; VXLAN is more widely supported and firewall-friendly | Prefer VXLAN for new Calico installs; IPinIP only if you have a specific need for it |

---

## Hands-On Exercises

### Exercise 1: Explore CNI Internals on a kind Cluster

```bash
# Create a kind cluster (uses kindnetd CNI by default)
cat <<'EOF' > kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/12"
nodes:
  - role: control-plane
  - role: worker
  - role: worker
EOF
kind create cluster --name cni-lab --config kind-config.yaml
```

**Task 1**: Install Calico and verify Pod connectivity.

```bash
# Install Calico operator and custom resource
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.29/manifests/tigera-operator.yaml

cat <<'EOF' | kubectl apply -f -
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  calicoNetwork:
    ipPools:
      - name: default-ipv4-ippool
        cidr: 10.244.0.0/16
        encapsulation: VXLANCrossSubnet
        natOutgoing: Enabled
        nodeSelector: all()
EOF

# Wait for all calico pods to be ready
kubectl wait --for=condition=ready pod -l k8s-app=calico-node -n calico-system --timeout=300s
```

**Task 2**: Deploy two Pods on different nodes and verify cross-node communication.

```bash
# Create test pods pinned to different nodes
WORKERS=$(kubectl get nodes --no-headers -l '!node-role.kubernetes.io/control-plane' -o name)
NODE1=$(echo "$WORKERS" | head -1 | cut -d/ -f2)
NODE2=$(echo "$WORKERS" | tail -1 | cut -d/ -f2)

kubectl run pod-a --image=busybox:1.36 --overrides="{\"spec\":{\"nodeName\":\"$NODE1\"}}" \
  --command -- sleep 3600
kubectl run pod-b --image=busybox:1.36 --overrides="{\"spec\":{\"nodeName\":\"$NODE2\"}}" \
  --command -- sleep 3600

kubectl wait --for=condition=ready pod/pod-a pod/pod-b --timeout=120s

# Get Pod B's IP and ping from Pod A
POD_B_IP=$(kubectl get pod pod-b -o jsonpath='{.status.podIP}')
kubectl exec pod-a -- ping -c 3 $POD_B_IP
```

**Task 3**: Examine the CNI plumbing on the node.

```bash
# Exec into the kind node container to inspect networking
docker exec -it cni-lab-worker bash

# Inside the node:
ip link show type veth          # See veth pairs to Pods
ip route show                   # See per-Pod routes (Calico adds /32 routes)
cat /etc/cni/net.d/*.conflist   # CNI configuration
ls /opt/cni/bin/                # CNI binaries
iptables-save | head -50        # iptables rules (if not using eBPF)
```

<details>
<summary>What to observe</summary>

- Each Pod has a `cali*` veth pair on the host
- Calico adds /32 routes pointing to each veth interface (no bridge)
- The CNI conflist shows the Calico plugin chain
- Cross-node traffic goes through VXLAN tunnel (`vxlan.calico` interface)

</details>

### Exercise 2: Install Cilium and Enable Hubble

```bash
# Delete previous cluster and create fresh one
kind delete cluster --name cni-lab
kind create cluster --name cilium-lab --config kind-config.yaml

# Install Cilium CLI (detect OS and architecture)
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
CLI_ARCH=amd64
if [ "$(uname -m)" = "aarch64" ] || [ "$(uname -m)" = "arm64" ]; then CLI_ARCH=arm64; fi
curl -L --fail --remote-name-all \
  https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-$(uname -s | tr '[:upper:]' '[:lower:]')-${CLI_ARCH}.tar.gz
sudo tar xzvfC cilium-$(uname -s | tr '[:upper:]' '[:lower:]')-${CLI_ARCH}.tar.gz /usr/local/bin
rm cilium-$(uname -s | tr '[:upper:]' '[:lower:]')-${CLI_ARCH}.tar.gz

# Install Cilium
cilium install --version 1.16.5

# Wait for Cilium to be ready
cilium status --wait

# Enable Hubble
cilium hubble enable --ui

# Run connectivity test
cilium connectivity test
```

**Task**: Deploy a workload and observe traffic flows with Hubble.

```bash
# Deploy sample app
kubectl create deployment nginx --image=nginx:1.27 --replicas=2
kubectl expose deployment nginx --port=80

# Port-forward Hubble UI
cilium hubble ui &

# Observe flows from CLI
hubble observe --namespace default --follow
```

### Exercise 3: Compare CNI Performance

```bash
# Install iperf3 on both clusters to compare throughput
kubectl run iperf-server --image=networkstatic/iperf3 --command -- iperf3 -s
kubectl wait --for=condition=ready pod/iperf-server --timeout=60s

SERVER_IP=$(kubectl get pod iperf-server -o jsonpath='{.status.podIP}')
kubectl run iperf-client --image=networkstatic/iperf3 --rm -it --restart=Never \
  --command -- iperf3 -c $SERVER_IP -t 10 -P 4

# Record: bandwidth, retransmits, CPU usage
# Compare results across CNI installs
```

**Success Criteria:**
- [ ] Installed Calico on a kind cluster and verified cross-node Pod connectivity
- [ ] Inspected veth pairs, routes, and CNI config on the node
- [ ] Installed Cilium with Hubble and observed live traffic flows
- [ ] Ran iperf3 throughput test and recorded baseline numbers

---

## War Story

**The 10,000-Service iptables Meltdown**

A SaaS platform running 800 microservices on a 150-node Calico cluster (iptables mode) started experiencing intermittent 2-5 second latency spikes during deployments. The spikes correlated perfectly with Service or Endpoint changes.

**Timeline:**

- **Day 1**: Engineering notices P99 latency spikes during peak deployment hours (2-4 PM). Each spike lasts 2-5 seconds. Customer-facing APIs return 504 Gateway Timeout.
- **Day 3**: Investigation reveals that kube-proxy is rebuilding ~38,000 iptables rules on every EndpointSlice update. Each rebuild takes 1.8 seconds and blocks packet processing.
- **Day 5**: Team adds `--iptables-min-sync-period=5s` to kube-proxy to batch updates. Spikes reduce from 30/hour to 8/hour during deployments.
- **Day 12**: Root cause: the combination of high churn (120 deployments/day) and many Services means iptables is being rewritten constantly. The team migrates to Calico's eBPF dataplane over a weekend maintenance window.
- **Day 14**: After eBPF migration, latency spikes disappear entirely. Service routing happens in eBPF maps (O(1) lookup) instead of iptables chains (O(n) traversal).

**Business impact**: $340K in SLA credits over 12 days. Two enterprise customers began evaluating competitors.

**Lesson**: iptables-based networking does not scale linearly with Service count. If you're running more than 3,000 Services, evaluate eBPF-based dataplanes (Cilium, Calico eBPF) or IPVS mode as a minimum.

---

## Knowledge Check

<details>
<summary>1. What are the five CNI specification operations, and which one was added most recently?</summary>

The five operations are **ADD**, **DEL**, **CHECK**, **VERSION**, and **GC** (garbage collection). GC was added in CNI spec v1.1.0 (2023) to address the problem of orphaned network interfaces and leaked IP addresses when container runtimes crash between creating and registering a network interface. Before GC, operators had to manually clean up zombie veth pairs on long-running nodes.
</details>

<details>
<summary>2. Why does Calico in BGP mode offer better raw throughput than Calico in VXLAN mode?</summary>

BGP mode uses **native routing** — packets are forwarded using standard Linux routing tables with no encapsulation overhead. VXLAN mode wraps every cross-node packet in a UDP/VXLAN header (50 bytes of overhead), which reduces the effective MTU and adds CPU cost for encapsulation/decapsulation. BGP mode is ~5-6% faster in throughput benchmarks because it avoids this overhead entirely. The trade-off is that BGP mode requires the underlying network infrastructure to support BGP peering.
</details>

<details>
<summary>3. A cluster has 5,000 Services. Why might you see latency spikes with iptables-based kube-proxy?</summary>

With iptables-based kube-proxy, every Service creates multiple iptables rules (for ClusterIP, endpoints, load balancing). At 5,000 Services, you can have 40,000+ rules. When any Service or EndpointSlice changes, kube-proxy rewrites the **entire** iptables table atomically — this takes 1-3 seconds during which packet processing stalls. eBPF or IPVS mode solves this because they use hash-map lookups (O(1)) instead of sequential chain traversal (O(n)).
</details>

<details>
<summary>4. You're deploying a new cluster in AWS EKS. Should you replace the aws-vpc-cni with Cilium?</summary>

Not necessarily. The aws-vpc-cni provides **VPC-native Pod IPs** — each Pod gets a real ENI IP from the VPC subnet. This enables native AWS security groups for Pods, VPC Flow Logs, and direct routing without overlay overhead. Replacing it with Cilium means you lose these VPC-native features. However, if you need advanced L7 network policies, Hubble observability, or ClusterMesh, you might install Cilium alongside or instead. Evaluate the trade-offs: cloud integration vs. advanced networking features.
</details>

<details>
<summary>5. What is the purpose of the pause container in Kubernetes Pod networking?</summary>

The pause container creates and holds the **network namespace** for the Pod. All other containers in the Pod share this namespace (same IP, same ports, same interfaces). The pause container starts first, the CNI plugin configures networking in its namespace, and then application containers join. If an application container crashes and restarts, the network namespace (and IP) persist because the pause container is still running.
</details>

<details>
<summary>6. Scenario: After migrating from Flannel to Calico, some Pods on migrated nodes can reach each other, but Pods on migrated nodes cannot reach Pods on not-yet-migrated nodes. What's likely wrong?</summary>

The two CNIs use **different overlay protocols** and **different tunnel interfaces**. Flannel uses VXLAN with a `flannel.1` interface, while Calico uses its own VXLAN tunnel (`vxlan.calico`) or IPinIP (`tunl0`). Packets from Calico nodes are encapsulated in a format that Flannel nodes don't understand, and vice versa. This is why CNI migration requires draining all nodes — you cannot run two different overlay CNIs simultaneously. The fix is to complete the migration by draining and converting the remaining nodes.
</details>

<details>
<summary>7. Why does Cilium require a minimum kernel version of 5.4?</summary>

Cilium's core functionality relies on **eBPF features** that were only added in Linux kernel 5.x. Specifically: BPF-to-BPF function calls (4.16), bounded loops (5.3), and BTF (BPF Type Format) for CO-RE (Compile Once, Run Everywhere) portability (5.4). Without these features, Cilium cannot compile or load its eBPF programs. Kernel 5.10+ is recommended because it adds additional features like BPF LSM hooks and improved memory management for BPF maps.
</details>

<details>
<summary>8. Your cluster runs Flannel but you need network policies. What are your options without a full CNI migration?</summary>

You can install **Calico in policy-only mode**. Calico can run alongside Flannel, handling only network policy enforcement while Flannel continues to manage the actual Pod networking (IP assignment, routing). This is sometimes called "Canal" (Calico + Flannel). Install Calico with `CALICO_NETWORKING_BACKEND=none` and it will enforce NetworkPolicy resources without interfering with Flannel's data plane. This avoids a full CNI migration while adding policy support.
</details>

---

## Summary

CNI plugins are the foundation of Kubernetes networking — they determine how Pods get IPs, how traffic flows between nodes, and what policy enforcement is available. The three main choices today are:

- **Flannel** — Simple, lightweight, no policies. Use for dev/test.
- **Calico** — Feature-rich, supports BGP and eBPF, enterprise proven. Best for on-prem and mixed environments.
- **Cilium** — eBPF-native, L7 policies, Hubble observability, service mesh. Best for modern stacks on recent kernels.

Choosing a CNI is a long-term architectural decision. Migration is possible but disruptive. Make the right choice early by evaluating your kernel version, policy needs, observability requirements, and whether you need multi-cluster connectivity.

## What's Next

In [Module 1.2: Network Policy Design Patterns](../module-1.2-network-policy-design/), you'll learn how to use the policy engine your CNI provides — designing default-deny strategies, namespace isolation, and zero-trust microsegmentation patterns that keep your cluster secure without breaking connectivity.
