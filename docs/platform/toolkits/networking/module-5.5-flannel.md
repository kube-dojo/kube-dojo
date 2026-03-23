# Module 5.5: Flannel - Overlay Networking from the Ground Up

> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 60-75 minutes

## The Packets That Vanished at 1451 Bytes

*Three days. Three days of chasing ghosts through a Kubernetes cluster.*

```
[Day 1, 09:14 AM]
@backend-lead    File uploads are failing intermittently.
@backend-lead    But only large files. Small files work fine.
@sre-team        Define "large."
@backend-lead    Anything over... I don't know, maybe 1400 bytes?
@sre-team        That's oddly specific. Checking network.

[Day 1, 02:30 PM]
@sre-team        tcpdump shows the packets leaving the source pod.
@sre-team        tcpdump shows the packets never arriving at the dest pod.
@sre-team        They just... vanish. In the middle of the cluster.
@backend-lead    How do packets vanish?
@sre-team        Great question. I'll let you know when I figure it out.

[Day 2, 10:00 AM]
@sre-team        Tried everything. iptables look fine. Routes look fine.
@sre-team        The CNI says everything is healthy. Nodes can ping each other.
@sre-team        Small payloads work. Large payloads don't.
@sre-team        I'm losing my mind.

[Day 3, 11:47 AM]
@sre-team        FOUND IT.
@sre-team        Node MTU is 1500. VXLAN overlay adds a 50-byte header.
@sre-team        Effective pod MTU should be 1450. But Flannel was configured
                 with the default 1500.
@sre-team        Any packet over 1450 bytes gets silently dropped after
                 encapsulation because it exceeds the physical NIC MTU.
@sre-team        We've been dropping oversized encapsulated packets for weeks.
@backend-lead    Weeks?!
@sre-team        Small API calls worked fine. Only large payloads triggered it.
@sre-team        Nobody noticed until the file upload feature shipped.

[Day 3, 11:52 AM]
@sre-team        One line fix: set pod MTU to 1450 in the Flannel config.
@sre-team        Three days of debugging. One line fix.
@sre-team        We missed our SLA by two days.
```

That team learned something the hard way: overlay networking adds bytes to every packet. If you do not account for that overhead, packets silently disappear once they exceed the physical MTU. No error message. No ICMP unreachable. Just silence. And because small packets always work fine, the failure pattern looks completely random until you understand the math.

This module will make sure you never burn three days on that problem. By the end, you will understand exactly how every packet travels across a Kubernetes cluster, byte by byte.

**What You'll Learn**:
- Why overlay networks exist and how they solve the Kubernetes networking problem
- VXLAN encapsulation -- what happens to a packet, header by header
- Flannel's architecture: flanneld, subnet leases, backend options
- How to install and configure Flannel on a real cluster
- The NetworkPolicy gap and what to do about it
- MTU math that will save you from the scenario above

**Prerequisites**:
- Kubernetes networking basics (Pods, Services, CNI)
- [Linux Networking fundamentals](../../../linux/networking/)
- Basic understanding of TCP/IP and Ethernet frames
- A kind cluster for the hands-on exercise

---

## Why This Module Matters

Flannel is the simplest Kubernetes CNI plugin that actually works in production. It was one of the first CNI plugins ever created for Kubernetes, built by CoreOS in 2014, and it remains one of the most widely deployed. If you have ever used kubeadm to bootstrap a cluster and followed the official documentation, there is a good chance your first cluster ran Flannel.

But Flannel's real value in this curriculum is not the tool itself. It is what Flannel teaches you about overlay networking. Flannel is transparent enough that you can trace every step of a packet's journey: from pod to veth pair, across a bridge, through VXLAN encapsulation, over the wire, and back out the other side. More sophisticated CNIs like Cilium and Calico build on these same concepts but hide them behind layers of abstraction.

Understanding Flannel means understanding the networking primitives that all CNI plugins rely on. Once you grasp overlays, MTU, and subnet allocation at this level, debugging any CNI becomes dramatically easier.

> **Did You Know?**
>
> 1. Flannel was created by CoreOS (now part of Red Hat) in 2014, making it one of the oldest Kubernetes networking projects. It predates the CNI specification itself -- Flannel originally used its own plugin model and was later adapted to the CNI standard. More than a decade later, it still receives active maintenance and has over 8,800 GitHub stars.
>
> 2. The name "Flannel" comes from the idea of a "flannel layer" -- a soft overlay that sits on top of the existing network. The project was originally called "rudder" before being renamed. The flannel metaphor is surprisingly accurate: it is a thin, comfortable layer you probably do not think about until it develops a hole (usually an MTU hole).
>
> 3. k3s, the lightweight Kubernetes distribution from Rancher, ships with Flannel as its default CNI. Every k3s cluster in the world -- and there are millions of them running on edge devices, IoT gateways, and Raspberry Pis -- uses Flannel unless explicitly configured otherwise. For many engineers, Flannel is the first CNI they ever encounter.
>
> 4. VXLAN (Virtual Extensible LAN) was originally designed by VMware and Cisco in 2011 to solve a completely different problem: VLAN exhaustion in large data centers. Traditional VLANs are limited to 4,094 segments. VXLAN supports over 16 million. Kubernetes adopted VXLAN not for its scale, but because it provides a clean way to create virtual L2 networks over L3 infrastructure -- exactly what pod networking needs.

---

## Part 1: Why Overlay Networks Exist

### The Kubernetes Networking Problem

Kubernetes makes a bold promise in its networking model:

1. Every Pod gets its own IP address
2. Pods can communicate with any other Pod without NAT
3. Pods on the same node can communicate with each other
4. Pods on different nodes can communicate with each other

Requirements 1 through 3 are relatively straightforward. You create a virtual ethernet pair (veth), assign an IP, and connect it to a bridge on the node. Pods on the same node share a bridge and can talk to each other directly.

Requirement 4 is where things get complicated. Consider this scenario:

```
Node A (10.0.1.10)                    Node B (10.0.1.11)
+------------------+                  +------------------+
| Pod: 10.244.0.5  |                  | Pod: 10.244.1.8  |
|   "Hey Pod B,    |                  |   "I'm waiting   |
|    send me data" |                  |    for traffic"   |
+------------------+                  +------------------+
        |                                      |
   Physical Network (10.0.1.0/24)
   Knows about: 10.0.1.10, 10.0.1.11
   Does NOT know about: 10.244.0.0/16
```

The physical network knows how to route traffic to Node A (10.0.1.10) and Node B (10.0.1.11). But it has absolutely no idea what 10.244.0.5 or 10.244.1.8 are. Those pod IPs exist only inside Kubernetes. If Pod A sends a packet to 10.244.1.8, the physical network will drop it because it cannot route to that address.

You have two choices:

**Option 1: Teach the physical network about pod IPs.** Configure your routers and switches to route 10.244.0.0/24 to Node A and 10.244.1.0/24 to Node B. This works (it is called "host-gw" mode), but it requires control over the physical network infrastructure. In a cloud environment, you usually cannot modify the underlying network routing.

**Option 2: Wrap the pod packet inside a node packet.** Take the original packet (from 10.244.0.5 to 10.244.1.8) and put it inside a new packet (from 10.0.1.10 to 10.0.1.11). The physical network knows how to deliver that outer packet. When it arrives at Node B, Node B unwraps it and delivers the inner packet to the correct pod.

Option 2 is an overlay network. And that is exactly what Flannel's VXLAN backend does.

### VXLAN: Packets Inside Packets

VXLAN stands for Virtual Extensible LAN. The concept is simple: take a complete Ethernet frame, wrap it in a UDP packet, and send it across the network. The receiving end unwraps the UDP packet and recovers the original frame.

Here is what a VXLAN-encapsulated packet actually looks like:

```
Original Pod-to-Pod Packet:
+-------------------------------------------------------+
| Inner Ethernet | Inner IP      | TCP/UDP | Payload    |
| dst: Pod B MAC | src: 10.244.0.5        | "Hello"    |
| src: Pod A MAC | dst: 10.244.1.8        |            |
| (14 bytes)     | (20 bytes)    | (8-20)  | (variable) |
+-------------------------------------------------------+

After VXLAN Encapsulation:
+------------------------------------------------------------------+
| Outer      | Outer IP      | Outer UDP | VXLAN  | [Original     ]|
| Ethernet   | src: 10.0.1.10| dst: 8472 | Header | [Pod-to-Pod   ]|
| (14 bytes) | dst: 10.0.1.11| (8 bytes) | (8 B)  | [Packet Above ]|
|            | (20 bytes)    |           |        |                |
+------------------------------------------------------------------+
              \_____________ 50 bytes overhead _____________/
```

The critical math: VXLAN adds 50 bytes of overhead (20-byte outer IP + 8-byte outer UDP + 8-byte VXLAN header + 14-byte outer Ethernet). If your physical network MTU is 1500 bytes, the maximum payload your pod can send without fragmentation is 1500 - 50 = **1450 bytes**.

This is exactly the MTU problem from our opening war story. If a pod sends a 1500-byte packet, after encapsulation it becomes 1550 bytes. The physical NIC has an MTU of 1500 and cannot send it. Depending on the path MTU discovery settings and DF (Don't Fragment) bit, the packet is either fragmented (causing performance issues) or silently dropped (causing the mysterious failures).

### The Full Packet Walk

Let us trace a packet from Pod A on Node 1 to Pod B on Node 2, step by step. This is the core knowledge of this module -- if you understand this diagram, you understand overlay networking:

```
Pod A (10.244.0.5)              Pod B (10.244.1.8)
Node 1 (10.0.1.10)             Node 2 (10.0.1.11)

     [Pod A]                         [Pod B]
       |                               ^
       | 1. App sends data             | 10. Data delivered
       |    to 10.244.1.8              |     to application
       v                               |
   +--------+                      +--------+
   | veth0  | 2. Packet enters     | veth0  | 9. Packet exits
   | (pod)  |    veth pair          | (pod)  |    veth pair
   +--------+                      +--------+
       |                               ^
       v                               |
   +--------+                      +--------+
   | vethXX | 3. Host-side veth    | vethYY | 8. Host-side veth
   | (host) |    receives packet   | (host) |    receives packet
   +--------+                      +--------+
       |                               ^
       v                               |
   +----------+                    +----------+
   | cni0     | 4. Bridge checks   | cni0     | 7. Bridge forwards
   | (bridge) |    routing table    | (bridge) |    to local veth
   +----------+                    +----------+
       |                               ^
       | dst 10.244.1.0/24             |
       | -> via flannel.1              |
       v                               |
   +----------+                    +----------+
   | flannel.1| 5. VXLAN device    | flannel.1| 6. VXLAN device
   | (VTEP)   |    encapsulates:   | (VTEP)   |    decapsulates:
   |          |    inner frame     |          |    recovers inner
   |          |    wrapped in      |          |    frame from UDP
   |          |    UDP to Node 2   |          |    packet
   +----------+                    +----------+
       |                               ^
       v                               |
   +--------+  ==================  +--------+
   | eth0   |  Physical Network    | eth0   |
   | Node 1 |  =================>  | Node 2 |
   +--------+  Wire / Switch       +--------+
   10.0.1.10                       10.0.1.11
```

**Step by step:**

1. **Pod A's application** sends a TCP packet to 10.244.1.8 (Pod B).
2. **The packet enters the veth pair.** Every pod has a virtual ethernet pair -- one end inside the pod's network namespace (usually `eth0` inside the pod), the other end on the host (named something like `vethXXXXXX`).
3. **The host-side veth** passes the packet to the bridge (`cni0`).
4. **The bridge consults the routing table.** The kernel sees that 10.244.1.0/24 is reachable via the `flannel.1` device and forwards the packet there.
5. **The `flannel.1` VTEP (VXLAN Tunnel Endpoint)** encapsulates the packet. It wraps the entire inner Ethernet frame in an outer IP/UDP/VXLAN header, addressed from Node 1 (10.0.1.10) to Node 2 (10.0.1.11) on UDP port 8472.
6. **On Node 2, the `flannel.1` VTEP** receives the UDP packet on port 8472, strips the outer headers, and recovers the original inner frame.
7. **The bridge (`cni0`) on Node 2** receives the inner frame and looks up the destination MAC to find which local veth pair to forward to.
8. **The host-side veth** delivers the packet to Pod B's network namespace.
9. **Pod B's veth** receives the packet.
10. **Pod B's application** receives the data.

All of this happens in microseconds. The pods have no idea they are on different nodes. As far as they can tell, they are on the same flat L2 network. That is the magic of overlay networking.

---

## Part 2: Flannel Architecture

### How Flannel Works

Flannel is composed of a few simple components:

```
+------------------------------------------------------------------+
|                     Kubernetes API Server                         |
|  Stores: Node.Spec.PodCIDR (subnet assignments per node)         |
+------------------------------------------------------------------+
         |                    |                    |
    Watches for          Watches for          Watches for
    node changes         node changes         node changes
         |                    |                    |
         v                    v                    v
+----------------+   +----------------+   +----------------+
| flanneld       |   | flanneld       |   | flanneld       |
| (DaemonSet pod)|   | (DaemonSet pod)|   | (DaemonSet pod)|
| Node 1         |   | Node 2         |   | Node 3         |
+----------------+   +----------------+   +----------------+
| - Reads subnet |   | - Reads subnet |   | - Reads subnet |
|   from API     |   |   from API     |   |   from API     |
| - Configures   |   | - Configures   |   | - Configures   |
|   flannel.1    |   |   flannel.1    |   |   flannel.1    |
| - Writes       |   | - Writes       |   | - Writes       |
|   subnet.env   |   |   subnet.env   |   |   subnet.env   |
| - Sets routes  |   | - Sets routes  |   | - Sets routes  |
+----------------+   +----------------+   +----------------+
```

**flanneld** is the heart of Flannel. It runs as a DaemonSet -- one pod on every node in the cluster. Here is what it does on startup:

1. **Reads the Pod CIDR.** When `kubeadm init --pod-network-cidr=10.244.0.0/16` is run, the controller manager allocates a `/24` subnet to each node (e.g., Node 1 gets 10.244.0.0/24, Node 2 gets 10.244.1.0/24). flanneld reads this from the Kubernetes API (specifically `Node.Spec.PodCIDR`).

2. **Creates the VXLAN device.** flanneld creates a network device called `flannel.1` (the VTEP) on each node. This device handles encapsulation and decapsulation.

3. **Writes `/run/flannel/subnet.env`.** This file tells the CNI plugin which subnet to assign pod IPs from:

```bash
# /run/flannel/subnet.env on Node 1
FLANNEL_NETWORK=10.244.0.0/16
FLANNEL_SUBNET=10.244.0.1/24
FLANNEL_MTU=1450
FLANNEL_IPMASQ=true
```

4. **Configures routes.** For every other node in the cluster, flanneld adds a route so the kernel knows where to send traffic for that node's pod subnet:

```bash
# Routes on Node 1
10.244.0.0/24 dev cni0          # local pods - go to bridge
10.244.1.0/24 via 10.244.1.0 dev flannel.1  # Node 2's pods - go via VXLAN
10.244.2.0/24 via 10.244.2.0 dev flannel.1  # Node 3's pods - go via VXLAN
```

5. **Watches for changes.** When nodes join or leave the cluster, flanneld updates routes and VXLAN FDB (forwarding database) entries accordingly.

### The CNI Plugin

flanneld itself does not assign IPs to pods. That is the job of the CNI plugin. When a new pod is scheduled on a node:

1. The kubelet calls the Flannel CNI plugin (`/opt/cni/bin/flannel`)
2. The Flannel CNI plugin reads `/run/flannel/subnet.env`
3. It delegates to the `bridge` CNI plugin, which:
   - Creates a veth pair
   - Attaches one end to the pod, the other to the `cni0` bridge
   - Assigns an IP from the node's subnet (e.g., 10.244.0.5 from 10.244.0.0/24)
4. The pod is now connected to the overlay network

This delegation model is elegant. Flannel handles the overlay (cross-node traffic). The bridge plugin handles the local plumbing (creating interfaces and assigning IPs). Each component does one thing well.

---

## Part 3: Flannel Backends -- Choosing Your Overlay

Flannel supports multiple backends for cross-node communication. The backend determines how packets are transported between nodes.

### VXLAN (Default)

VXLAN is Flannel's default and most widely used backend. It works everywhere -- cloud, bare metal, virtual machines -- because it only requires UDP connectivity between nodes.

**How it works:**
- Creates a `flannel.1` VXLAN device on each node
- Encapsulates pod traffic in UDP packets (port 8472)
- Works across L3 boundaries (nodes can be on different subnets)

**Performance:** Roughly 5-10% overhead compared to native networking, due to the encapsulation/decapsulation cost and the extra bytes per packet.

```yaml
# net-conf.json for VXLAN backend
{
  "Network": "10.244.0.0/16",
  "Backend": {
    "Type": "vxlan"
  }
}
```

### host-gw (Host Gateway)

host-gw does not use encapsulation at all. Instead, it adds static routes on each node pointing directly to other nodes.

**How it works:**
- Adds a route: `10.244.1.0/24 via 10.0.1.11 dev eth0` (use Node 2 as the gateway for Node 2's pods)
- No encapsulation overhead -- packets go directly
- Requires all nodes to be on the **same L2 subnet** (same broadcast domain)

**Performance:** Near-native. No encapsulation means no overhead.

```yaml
{
  "Network": "10.244.0.0/16",
  "Backend": {
    "Type": "host-gw"
  }
}
```

**The L2 constraint is serious.** If your nodes are in different subnets (separated by a router), host-gw will not work. The router does not know about pod CIDRs and will drop the traffic. This is why VXLAN is the default -- it works regardless of network topology.

### WireGuard

WireGuard provides an encrypted overlay. It uses the WireGuard kernel module (available in Linux 5.6+) for fast encryption.

**How it works:**
- Creates WireGuard tunnels between all nodes
- All pod traffic is encrypted in transit
- Better performance than IPsec due to WireGuard's modern cryptography

**Performance:** 5-15% overhead depending on CPU. Modern CPUs with AES-NI make the encryption nearly free.

```yaml
{
  "Network": "10.244.0.0/16",
  "Backend": {
    "Type": "wireguard"
  }
}
```

### Backend Comparison

| Feature | VXLAN | host-gw | WireGuard |
|---------|-------|---------|-----------|
| **Network requirement** | L3 (any topology) | L2 (same subnet) | L3 (any topology) |
| **Encapsulation** | UDP/VXLAN | None | WireGuard tunnel |
| **Encryption** | No | No | Yes (ChaCha20-Poly1305) |
| **Performance overhead** | ~5-10% | ~0% (near-native) | ~5-15% |
| **MTU reduction** | 50 bytes | 0 bytes | 60 bytes |
| **Pod MTU (1500 NIC)** | 1450 | 1500 | 1440 |
| **Complexity** | Low | Low | Low-Medium |
| **Cloud compatible** | Yes | Depends on provider | Yes |
| **Best for** | General use | Same-subnet clusters | Security-sensitive |

**Which should you pick?**

- **VXLAN**: When in doubt, use VXLAN. It works everywhere and the overhead is acceptable for most workloads.
- **host-gw**: When all nodes are on the same L2 subnet and you need maximum performance. Common in on-prem clusters with a flat network.
- **WireGuard**: When you need encryption in transit and your nodes run Linux 5.6+. Good for multi-tenant clusters or compliance requirements.

---

## Part 4: Installing Flannel

### Option 1: Raw Manifest (kubeadm)

The most common way to install Flannel, especially after bootstrapping with kubeadm:

```bash
# Step 1: Initialize the cluster with the correct pod CIDR
# Flannel defaults to 10.244.0.0/16 -- this MUST match
kubeadm init --pod-network-cidr=10.244.0.0/16

# Step 2: Apply the Flannel manifest
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

The `--pod-network-cidr` flag is critical. If you forget it or use a different CIDR, Flannel will not work because the Node.Spec.PodCIDR values will not match Flannel's expected network.

### Option 2: Helm Chart

```bash
# Add the Flannel Helm repo
helm repo add flannel https://flannel-io.github.io/flannel/
helm repo update

# Install with default settings (VXLAN backend)
helm install flannel flannel/flannel \
  --namespace kube-flannel \
  --create-namespace

# Install with custom settings
helm install flannel flannel/flannel \
  --namespace kube-flannel \
  --create-namespace \
  --set podCidr=10.244.0.0/16 \
  --set flannel.backend=host-gw
```

### Option 3: kind Cluster (For Learning)

This is what we will use in the hands-on exercise:

```yaml
# kind-flannel.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true   # Disable kindnet so we can install Flannel
  podSubnet: "10.244.0.0/16"
nodes:
  - role: control-plane
  - role: worker
  - role: worker
```

```bash
# Create the cluster
kind create cluster --config kind-flannel.yaml --name flannel-lab

# Nodes will be NotReady until we install a CNI
kubectl get nodes
# NAME                        STATUS     ROLES           AGE   VERSION
# flannel-lab-control-plane   NotReady   control-plane   30s   v1.31.0
# flannel-lab-worker          NotReady   <none>          20s   v1.31.0
# flannel-lab-worker2         NotReady   <none>          20s   v1.31.0

# Install Flannel
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml

# Wait for Flannel pods to be ready
kubectl -n kube-flannel wait pod --all --for=condition=Ready --timeout=60s

# Nodes should now be Ready
kubectl get nodes
# NAME                        STATUS   ROLES           AGE   VERSION
# flannel-lab-control-plane   Ready    control-plane   60s   v1.31.0
# flannel-lab-worker          Ready    <none>          50s   v1.31.0
# flannel-lab-worker2         Ready    <none>          50s   v1.31.0
```

### Verifying the Installation

After Flannel is running, you should see:

```bash
# Flannel DaemonSet pods (one per node)
kubectl -n kube-flannel get pods -o wide
# NAME                    READY   STATUS    NODE
# kube-flannel-ds-abc12   1/1     Running   flannel-lab-control-plane
# kube-flannel-ds-def34   1/1     Running   flannel-lab-worker
# kube-flannel-ds-ghi56   1/1     Running   flannel-lab-worker2

# The flannel.1 VXLAN device on each node
kubectl debug node/flannel-lab-worker -it --image=busybox -- ip -d link show flannel.1
# flannel.1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 ...
#     vxlan id 1 ... port 0 0 ...

# Routes pointing to other nodes' pod subnets
kubectl debug node/flannel-lab-worker -it --image=busybox -- ip route
# 10.244.0.0/24 via 10.244.0.0 dev flannel.1 onlink
# 10.244.1.0/24 dev cni0 proto kernel scope link src 10.244.1.1
# 10.244.2.0/24 via 10.244.2.0 dev flannel.1 onlink

# The subnet.env file
kubectl debug node/flannel-lab-worker -it --image=busybox -- cat /run/flannel/subnet.env
# FLANNEL_NETWORK=10.244.0.0/16
# FLANNEL_SUBNET=10.244.1.1/24
# FLANNEL_MTU=1450
# FLANNEL_IPMASQ=true
```

---

## Part 5: The NetworkPolicy Gap

This is the single most important thing to know about Flannel: **Flannel does not implement Kubernetes NetworkPolicies.**

This is not a bug. It is an intentional design decision. Flannel's scope is pod connectivity -- making sure pods can reach each other across nodes. It does not handle access control.

### What This Means in Practice

```yaml
# This NetworkPolicy will be accepted by the API server...
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

```bash
kubectl apply -f deny-all.yaml
# networkpolicy.networking.k8s.io/deny-all created
```

The API server accepted it. Kubernetes stored it in etcd. Everything looks fine. But **nothing is enforced.** Traffic flows exactly as it did before. The policy is decoration.

This is dangerous because it creates a false sense of security. You think you have network segmentation. You tell your security auditor you have network policies. But there is no enforcement layer.

### Your Options

**Option 1: Canal (Flannel + Calico)**

Canal combines Flannel for networking with Calico for network policy enforcement. You get Flannel's simplicity for the overlay plus Calico's mature policy engine.

```bash
# Install Canal (replaces standalone Flannel)
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/canal.yaml
```

**Option 2: Replace Flannel Entirely**

If you need NetworkPolicies, consider whether Flannel is the right choice at all:

- **[Calico](https://www.projectcalico.org/)**: Full CNI with built-in NetworkPolicies, BGP support, and eBPF dataplane
- **[Cilium](module-5.1-cilium.md)**: eBPF-based CNI with identity-aware policies, observability (Hubble), and more
- **[Weave Net](https://www.weave.works/oss/net/)**: Mesh overlay with built-in NetworkPolicies (note: Weaveworks shut down in 2024, community-maintained)

**Option 3: Accept the Tradeoff**

In certain environments -- learning clusters, isolated development environments, air-gapped networks with strong perimeter security -- you may decide that NetworkPolicies are unnecessary. This is a valid choice, but it must be a conscious decision, not an oversight.

### This Is the #1 Reason Teams Move Away from Flannel

Almost every team that starts with Flannel eventually migrates to Calico or Cilium. The story is always the same:

1. Bootstrap cluster with kubeadm and Flannel (because the tutorial said so)
2. Deploy workloads, everything works great
3. Security team asks about network segmentation
4. Team creates NetworkPolicies, declares victory
5. Penetration test reveals all traffic still flows freely
6. Panicked migration to Calico or Cilium

If you know from day one that you will need NetworkPolicies, skip Flannel and start with a CNI that implements them.

---

## Part 6: Troubleshooting Flannel

### Problem 1: MTU Mismatch (The Classic)

**Symptoms:** Large packets fail, small packets succeed. File transfers time out. gRPC streams drop intermittently. Health checks pass (small payloads) but data transfers fail.

**The math:**

```
Physical NIC MTU:    1500 bytes (standard Ethernet)
VXLAN overhead:      - 50 bytes (20 IP + 8 UDP + 8 VXLAN + 14 Ethernet)
                     ─────────
Pod MTU should be:   1450 bytes

If pod MTU is set to 1500 (wrong):
  Pod sends 1500-byte packet
  After VXLAN encapsulation: 1500 + 50 = 1550 bytes
  Physical NIC cannot send 1550 bytes (MTU is 1500)
  Packet is DROPPED (if DF bit is set) or fragmented (if not)
```

**Diagnosis:**

```bash
# Check the pod MTU
kubectl exec -it <pod> -- cat /sys/class/net/eth0/mtu
# Should be 1450 for VXLAN, not 1500

# Check the flannel.1 device MTU
kubectl debug node/<node> -it --image=busybox -- cat /sys/class/net/flannel.1/mtu
# Should be 1450

# Check subnet.env
kubectl debug node/<node> -it --image=busybox -- cat /run/flannel/subnet.env
# FLANNEL_MTU should be 1450

# Test with specific packet sizes
kubectl exec -it <pod-on-node-1> -- ping -s 1422 -M do <pod-ip-on-node-2>
# -s 1422 + 28 (IP+ICMP headers) = 1450 -- should work
kubectl exec -it <pod-on-node-1> -- ping -s 1423 -M do <pod-ip-on-node-2>
# -s 1423 + 28 = 1451 -- should FAIL if MTU is 1450
```

**Fix:**

```bash
# In the kube-flannel ConfigMap, set the correct MTU
kubectl -n kube-flannel edit configmap kube-flannel-cfg
```

```json
{
  "Network": "10.244.0.0/16",
  "Backend": {
    "Type": "vxlan",
    "MTU": 1450
  }
}
```

Then restart the Flannel DaemonSet:

```bash
kubectl -n kube-flannel rollout restart daemonset kube-flannel-ds
```

**For non-standard physical MTUs:** If your nodes use jumbo frames (MTU 9000), your pod MTU should be 9000 - 50 = 8950. If your cloud provider uses a smaller MTU (e.g., AWS instances in some VPCs use 9001), calculate accordingly.

### Problem 2: Subnet Exhaustion

**Symptoms:** New pods stuck in `ContainerCreating`. Events show `failed to allocate for range 0: no IP addresses available in range set`.

**Root cause:** Each node gets a `/24` subnet by default, which provides 254 pod IPs per node. If a node runs more than 254 pods (unlikely) or if subnet leases become corrupted, you run out.

More commonly, the cluster-wide `/16` supports 256 nodes. If you have more than 256 nodes, you need a larger pod CIDR.

```bash
# Check subnet allocation
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.podCIDR}{"\n"}{end}'
# flannel-lab-control-plane   10.244.0.0/24
# flannel-lab-worker          10.244.1.0/24
# flannel-lab-worker2         10.244.2.0/24

# Check available IPs on a node
kubectl debug node/<node> -it --image=busybox -- cat /var/lib/cni/networks/cbr0/ 2>/dev/null | wc -l
```

### Problem 3: Cross-Node Pod Communication Fails

**Symptoms:** Pods on the same node can communicate. Pods on different nodes cannot.

**Debugging checklist:**

```bash
# 1. Can nodes reach each other?
kubectl debug node/node-1 -it --image=busybox -- ping <node-2-ip>

# 2. Is the flannel.1 device up?
kubectl debug node/node-1 -it --image=busybox -- ip link show flannel.1

# 3. Are routes in place?
kubectl debug node/node-1 -it --image=busybox -- ip route | grep flannel

# 4. Is UDP port 8472 open between nodes?
# (VXLAN uses port 8472 by default in Flannel, not the IANA standard 4789)
kubectl debug node/node-1 -it --image=nicolaka/netshoot -- \
  nc -zu <node-2-ip> 8472

# 5. Check flanneld logs
kubectl -n kube-flannel logs -l app=flannel --tail=50

# 6. Check for iptables rules blocking VXLAN traffic
kubectl debug node/node-1 -it --image=busybox -- iptables -L -n | grep -i drop
```

### Problem 4: Pods Stuck in ContainerCreating After Node Reboot

**Symptoms:** After a node reboots, new pods on that node fail with CNI errors.

**Root cause:** `/run/flannel/subnet.env` is on a tmpfs and is lost on reboot. If flanneld has not started yet when the kubelet tries to create pods, the CNI plugin cannot find its config.

**Fix:** Ensure flanneld starts before kubelet, or tolerate the brief startup delay. The Flannel DaemonSet has `priorityClassName: system-node-critical` to ensure it starts early.

---

## Common Mistakes

| Mistake | What Goes Wrong | How to Fix |
|---------|-----------------|------------|
| Forgetting `--pod-network-cidr` in kubeadm init | Nodes get no PodCIDR, Flannel fails to start | Re-init with the flag, or manually patch Node.Spec.PodCIDR |
| Using a CIDR other than 10.244.0.0/16 | Flannel defaults to 10.244.0.0/16 -- mismatch causes routing failures | Either match the Flannel default or configure both to the same value |
| Not accounting for VXLAN MTU overhead | Silent packet drops for payloads above 1450 bytes | Set pod MTU to physical MTU minus 50 (e.g., 1450 for 1500 NIC) |
| Assuming NetworkPolicies work with Flannel | Policies are stored but never enforced -- traffic flows freely | Use Canal, Calico, or Cilium for NetworkPolicy enforcement |
| Installing multiple CNI plugins | Undefined behavior -- pods may get IPs from either CNI | Remove one CNI completely before installing another |
| Running flanneld with wrong network interface | flanneld picks the wrong node IP, breaks overlay | Use `--iface=eth0` flag or `--iface-regex` to specify the correct interface |
| Ignoring flanneld logs after upgrade | New version may change defaults (backend type, MTU) | Always check flanneld logs after upgrading |
| Using Flannel in multi-tenant production | No network isolation between tenants | Use Calico or Cilium for multi-tenant clusters |

---

## Quiz

Test your understanding of Flannel and overlay networking:

**Question 1:** Your physical network has an MTU of 9000 (jumbo frames). What should you set the pod MTU to when using Flannel with the VXLAN backend?

<details>
<summary>Show Answer</summary>

**8950 bytes.** VXLAN adds 50 bytes of overhead (20 IP + 8 UDP + 8 VXLAN + 14 Ethernet). So 9000 - 50 = 8950. Setting the pod MTU to anything higher risks fragmentation or silent packet drops for large payloads.

</details>

**Question 2:** You create a NetworkPolicy in a cluster running Flannel. `kubectl get networkpolicy` shows it exists. Is traffic being filtered?

<details>
<summary>Show Answer</summary>

**No.** Flannel does not implement NetworkPolicies. The Kubernetes API server accepts the resource (it is a valid Kubernetes object), but no component enforces it. Traffic flows exactly as before. This is arguably the most dangerous pitfall of using Flannel -- the false sense of security. To enforce policies, you need Canal (Flannel + Calico), or replace Flannel with Calico or Cilium.

</details>

**Question 3:** What is the key difference between Flannel's VXLAN backend and host-gw backend?

<details>
<summary>Show Answer</summary>

**VXLAN encapsulates packets in UDP**, adding a 50-byte overhead. It works across any network topology (L3). **host-gw adds static routes** without encapsulation, achieving near-native performance, but requires all nodes to be on the **same L2 subnet** (same broadcast domain). If nodes are separated by a router, host-gw will not work because routers do not know about pod CIDRs.

</details>

**Question 4:** A pod on Node 1 (10.0.1.10) sends a packet to a pod on Node 2 (10.0.1.11) via Flannel's VXLAN backend. What is the destination IP in the outer packet header?

<details>
<summary>Show Answer</summary>

**10.0.1.11** (Node 2's IP). The outer packet is addressed from Node 1 to Node 2 using their physical IPs. The inner packet (containing the original pod-to-pod traffic with pod IPs) is encapsulated inside. The physical network only sees the outer header and routes it based on node IPs. The inner packet with pod IPs is invisible to the network until Node 2 decapsulates it.

</details>

**Question 5:** You add a fourth node to your cluster but pods on the new node cannot communicate with pods on existing nodes. flanneld logs show no errors. What is the most likely cause?

<details>
<summary>Show Answer</summary>

**UDP port 8472 is blocked by a firewall between the new node and existing nodes.** Flannel's VXLAN backend uses UDP port 8472 (not the IANA standard 4789) for encapsulated traffic. flanneld may start without errors because it can communicate with the API server on port 6443, but the VXLAN data plane requires port 8472 between all nodes. Check firewall rules with: `nc -zu <other-node-ip> 8472`.

</details>

**Question 6:** Your cluster has 300 nodes. You used `--pod-network-cidr=10.244.0.0/16` during kubeadm init. What problem will you hit, and how do you solve it?

<details>
<summary>Show Answer</summary>

**Subnet exhaustion.** A /16 network with /24 per-node subnets supports only 256 nodes (2^8). With 300 nodes, 44 nodes will not receive a PodCIDR allocation. The fix: use a larger CIDR at init time, such as `--pod-network-cidr=10.244.0.0/14` (which gives 1024 /24 subnets). This must be set during cluster creation -- changing it later requires rebuilding the cluster or advanced manual intervention.

</details>

**Question 7:** You are running Flannel with VXLAN. A coworker says "just switch to host-gw for better performance." Your nodes span two subnets: 10.0.1.0/24 and 10.0.2.0/24, separated by a router. Should you make the switch?

<details>
<summary>Show Answer</summary>

**No.** host-gw requires all nodes to be on the same L2 subnet. With nodes on 10.0.1.0/24 and 10.0.2.0/24 separated by a router, host-gw routes will not work. The router between the subnets does not have routes for pod CIDRs and will drop the traffic. VXLAN is the correct choice here because it encapsulates traffic in UDP, which the router can forward normally using node IPs. If performance is critical, consider WireGuard backend (encrypted but still L3) or work with the network team to add pod CIDR routes to the router.

</details>

---

## Hands-On Exercise: Deploy Flannel, Test Connectivity, and Break MTU

**Objective:** Deploy Flannel on a kind cluster, verify cross-node pod communication, and reproduce the MTU mismatch issue from the opening war story.

**Time:** 20-25 minutes

**What you need:** Docker, kind, kubectl

### Step 1: Create a Multi-Node kind Cluster Without a CNI

```bash
cat <<'EOF' > /tmp/kind-flannel.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  podSubnet: "10.244.0.0/16"
nodes:
  - role: control-plane
  - role: worker
  - role: worker
EOF

kind create cluster --config /tmp/kind-flannel.yaml --name flannel-lab
```

### Step 2: Observe the Broken State

```bash
# Nodes are NotReady -- no CNI means no pod networking
kubectl get nodes
# All nodes should show NotReady

# CoreDNS pods are Pending -- they need a network
kubectl -n kube-system get pods
```

This is what a cluster looks like without a CNI. Kubernetes cannot schedule most pods because there is no way to assign them IP addresses or create network interfaces.

### Step 3: Install Flannel

```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml

# Watch the Flannel pods come up
kubectl -n kube-flannel get pods -w
# Wait until all show Running (1/1)

# Nodes should become Ready
kubectl get nodes
# All nodes should show Ready
```

### Step 4: Deploy Test Pods on Different Nodes

```bash
# Create a namespace for testing
kubectl create namespace flannel-test

# Deploy two pods, pinned to different nodes
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pod-a
  namespace: flannel-test
  labels:
    app: pod-a
spec:
  nodeName: flannel-lab-worker
  containers:
    - name: netshoot
      image: nicolaka/netshoot
      command: ["sleep", "3600"]
---
apiVersion: v1
kind: Pod
metadata:
  name: pod-b
  namespace: flannel-test
  labels:
    app: pod-b
spec:
  nodeName: flannel-lab-worker2
  containers:
    - name: netshoot
      image: nicolaka/netshoot
      command: ["sleep", "3600"]
EOF

# Wait for pods to be running
kubectl -n flannel-test wait pod --all --for=condition=Ready --timeout=60s
```

### Step 5: Verify Cross-Node Connectivity

```bash
# Get Pod B's IP
POD_B_IP=$(kubectl -n flannel-test get pod pod-b -o jsonpath='{.status.podIP}')
echo "Pod B IP: $POD_B_IP"

# Ping from Pod A to Pod B (cross-node!)
kubectl -n flannel-test exec pod-a -- ping -c 3 $POD_B_IP
# Should succeed -- packets are traversing the VXLAN overlay

# Verify the MTU
kubectl -n flannel-test exec pod-a -- cat /sys/class/net/eth0/mtu
# Should show 1450 (1500 - 50 VXLAN overhead)
```

### Step 6: Test MTU Boundaries

This is where we reproduce the war story. We will send packets of increasing size to find the exact byte boundary where things break.

```bash
# Send a packet that fits within the MTU (should work)
# -s 1422 = 1422 payload + 8 ICMP header + 20 IP header = 1450 total
# -M do = set Don't Fragment bit
kubectl -n flannel-test exec pod-a -- ping -c 1 -s 1422 -M do $POD_B_IP
# PING should succeed

# Send a packet exactly one byte too large (should fail)
# -s 1423 = 1423 + 8 + 20 = 1451 total -- exceeds 1450 MTU
kubectl -n flannel-test exec pod-a -- ping -c 1 -s 1423 -M do $POD_B_IP
# Expected: "ping: local error: message too long, mtu=1450"
# Or: packet dropped/timeout

# Send a much larger packet (definitely fails)
kubectl -n flannel-test exec pod-a -- ping -c 1 -s 1472 -M do $POD_B_IP
# This would work on a normal network (1472 + 28 = 1500)
# But fails here because of VXLAN overhead
```

**This is exactly what happened in the war story.** The 1422-byte ping works. The 1423-byte ping fails. The boundary is sharp and unforgiving. Without the `-M do` (Don't Fragment) flag, the kernel might fragment the packet instead of rejecting it -- causing latency and throughput issues instead of outright failure, which makes the problem even harder to diagnose.

### Step 7: Inspect the Overlay

```bash
# See the VXLAN device
kubectl -n flannel-test exec pod-a -- ip link show eth0

# From the node's perspective, see the flannel.1 device and routes
docker exec flannel-lab-worker ip -d link show flannel.1
docker exec flannel-lab-worker ip route | grep flannel
docker exec flannel-lab-worker cat /run/flannel/subnet.env
```

### Step 8: Verify NetworkPolicies Do NOT Work

```bash
# Create a "deny all" NetworkPolicy
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: flannel-test
spec:
  podSelector: {}
  policyTypes:
    - Ingress
EOF

# The policy exists
kubectl -n flannel-test get networkpolicy
# NAME               POD-SELECTOR   AGE
# deny-all-ingress   <none>         5s

# But traffic STILL flows!
kubectl -n flannel-test exec pod-a -- ping -c 2 $POD_B_IP
# Pings succeed -- the policy is not enforced

# Clean up the useless policy
kubectl -n flannel-test delete networkpolicy deny-all-ingress
```

This demonstrates the NetworkPolicy gap. In a production cluster, this would be a security issue.

### Success Criteria

You have completed this exercise if:
- [x] kind cluster created with 3 nodes and no default CNI
- [x] Flannel installed and all nodes show Ready
- [x] Cross-node ping between pods succeeds
- [x] MTU boundary verified: 1422-byte payload works, 1423-byte payload fails
- [x] NetworkPolicy demonstrated to be unenforced

### Cleanup

```bash
kind delete cluster --name flannel-lab
rm /tmp/kind-flannel.yaml
```

---

## When to Use Flannel (and When Not To)

### Use Flannel When:

- **Learning Kubernetes networking.** Flannel is transparent enough to understand every layer. Start here before Calico or Cilium.
- **Simple, single-tenant clusters.** Development environments, CI runners, small staging clusters where network isolation is not a requirement.
- **Air-gapped or constrained environments.** Flannel has minimal dependencies and works without internet access once installed.
- **k3s edge deployments.** k3s ships Flannel by default and it runs well on resource-constrained hardware like Raspberry Pis and IoT gateways.
- **Quick prototyping.** When you need a cluster running in minutes and network policy is not a concern.

### Do NOT Use Flannel When:

- **You need NetworkPolicies.** This is non-negotiable. If your security requirements include network segmentation, Flannel alone cannot help.
- **Large clusters (500+ nodes).** Flannel's simple architecture does not scale as gracefully as Calico or Cilium, which have more sophisticated control planes.
- **Multi-tenant production.** Without NetworkPolicies, tenants can see each other's traffic. This is a compliance failure in most regulated industries.
- **You need advanced observability.** Flannel has no equivalent to Hubble (Cilium) or Calico's flow logs. Debugging means manual tcpdump.
- **You need BGP peering.** Flannel's host-gw mode is L2 only. For BGP integration with your datacenter network, use Calico.
- **Performance-critical workloads.** The VXLAN overhead, while small, matters at high throughput. Cilium's eBPF dataplane or Calico's native routing avoid encapsulation entirely.

### The Migration Path

Most teams follow this journey:

```
Flannel (learning)
    |
    | "We need NetworkPolicies"
    v
Canal (Flannel + Calico policies)
    |
    | "We need more features"
    v
Calico or Cilium (full CNI replacement)
```

There is nothing wrong with starting at Flannel. Just know where the road leads.

---

## Key Takeaways

1. **Overlay networks exist because pod IPs are not routable on the physical network.** VXLAN solves this by wrapping pod packets inside node packets.

2. **VXLAN adds 50 bytes of overhead.** If your physical MTU is 1500, your pod MTU must be 1450. Get this wrong and you will spend days debugging intermittent failures.

3. **Flannel is deliberately simple.** It handles pod connectivity and nothing else. This is a strength for learning and simple environments, and a limitation for production.

4. **NetworkPolicies are not enforced by Flannel.** If you create them, they will be stored in etcd but have zero effect on traffic. Use Canal, Calico, or Cilium for enforcement.

5. **The packet walk is the foundation.** Pod -> veth -> bridge -> VXLAN encap -> wire -> VXLAN decap -> bridge -> veth -> Pod. Once you understand this path, debugging any CNI becomes an exercise in checking each hop.

6. **Choose your backend wisely.** VXLAN works everywhere. host-gw is faster but L2-only. WireGuard adds encryption. Most clusters should start with VXLAN.

---

## Next Steps

- **[Module 5.1: Cilium](module-5.1-cilium.md)** -- The eBPF-powered CNI that replaces iptables and kube-proxy. If Flannel is the bicycle, Cilium is the fighter jet.
- **[Module 5.2: Service Mesh](module-5.2-service-mesh.md)** -- mTLS and advanced traffic management at Layer 7
- **[Module 5.3: DNS Deep Dive](module-5.3-dns-deep-dive.md)** -- How pod DNS resolution works after packets can flow
- **[Module 5.4: MetalLB](module-5.4-metallb.md)** -- Load balancing for bare-metal clusters where Flannel provides the underlay
- **[CKA Module 3.2: Networking Fundamentals](../../../k8s/cka/part3-services-networking/module-3.2-endpoints.md)** -- The Kubernetes networking model that CNIs implement

---

*"Flannel is the 'Hello World' of Kubernetes networking. Simple enough to understand completely, limited enough to make you want more. And that is exactly the right place to start."*
