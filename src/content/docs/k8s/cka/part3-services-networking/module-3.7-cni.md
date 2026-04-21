---
title: "Module 3.7: CNI & Cluster Networking"
slug: k8s/cka/part3-services-networking/module-3.7-cni
sidebar:
  order: 8
lab:
  id: cka-3.7-cni
  url: https://killercoda.com/kubedojo/scenario/cka-3.7-cni
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Understanding network infrastructure
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 1.2 (Extension Interfaces), Module 3.1 (Services)

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Explain** how CNI plugins assign IP addresses and configure routes for pods
- **Compare** Calico, Cilium, and Flannel on features, performance, and NetworkPolicy support
- **Diagnose** CNI failures by checking pod networking, CNI configuration files, and plugin logs
- **Trace** pod-to-pod traffic through the CNI overlay or native routing path

---

## Why This Module Matters

The Container Network Interface (CNI) is the plugin system that gives pods their network connectivity. Without CNI, pods can't communicate. Understanding CNI helps you troubleshoot network issues, choose the right network plugin, and understand why pods can (or can't) talk to each other.

The CKA exam expects you to understand pod networking fundamentals, troubleshoot network issues, and know how different CNI plugins affect cluster behavior (especially Network Policy support).

> **The City Infrastructure Analogy**
>
> Think of CNI as the city planning department. They decide how streets (networks) are laid out, how addresses (IPs) are assigned to buildings (pods), and which neighborhoods (nodes) connect to which. Different CNI plugins are like different city designs—some have highways (high performance), some have security checkpoints (Network Policy).

---

## What You'll Learn

By the end of this module, you'll be able to:
- Understand the Kubernetes network model
- Know how CNI plugins work
- Compare popular CNI options
- Troubleshoot pod networking issues
- Understand how kube-proxy manages service traffic

---

## Did You Know?

- **No built-in networking**: Kubernetes doesn't ship with networking. You must install a CNI plugin for pods to communicate.

- **Flannel = no NetworkPolicy**: The popular Flannel CNI doesn't support Network Policies. If you need policies, use Calico or Cilium.

- **Pod CIDR is per-node**: Each node typically gets its own IP range (e.g., 10.244.1.0/24), and pods on that node get IPs from that range.

---

## Part 1: Kubernetes Network Model

### 1.1 The Four Requirements

Kubernetes networking has four fundamental requirements:

```
┌────────────────────────────────────────────────────────────────┐
│                Kubernetes Network Requirements                  │
│                                                                 │
│   1. Pod-to-Pod: All pods can communicate with all pods        │
│      without NAT                                                │
│      ┌─────┐      ┌─────┐                                      │
│      │Pod A│◄────►│Pod B│  (direct IP, no NAT)                │
│      └─────┘      └─────┘                                      │
│                                                                 │
│   2. Node-to-Pod: Nodes can communicate with all pods          │
│      without NAT                                                │
│      ┌─────┐      ┌─────┐                                      │
│      │Node │◄────►│ Pod │  (direct access)                    │
│      └─────┘      └─────┘                                      │
│                                                                 │
│   3. Pod IP = Seen IP: The IP a pod sees is the same IP        │
│      others see                                                 │
│      Pod thinks: "My IP is 10.244.1.5"                         │
│      Others see: "Pod's IP is 10.244.1.5"                      │
│                                                                 │
│   4. Pod-to-Service: Pods can reach services by ClusterIP      │
│      ┌─────┐      ┌───────────┐      ┌─────┐                  │
│      │ Pod │─────►│  Service  │─────►│ Pod │                  │
│      └─────┘      └───────────┘      └─────┘                  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 What CNI Provides

| Responsibility | Component |
|----------------|-----------|
| Pod IP allocation | CNI plugin (IPAM) |
| Pod-to-pod routing | CNI plugin |
| Cross-node networking | CNI plugin |
| Network Policy enforcement | CNI plugin (if supported) |
| Service ClusterIP routing | kube-proxy |

### 1.3 Network Namespaces

```
┌────────────────────────────────────────────────────────────────┐
│                   Network Namespaces                            │
│                                                                 │
│   Node                                                          │
│   ┌────────────────────────────────────────────────────────┐   │
│   │  Host Network Namespace                                 │   │
│   │  eth0: 192.168.1.10                                    │   │
│   │                                                         │   │
│   │     ┌─────────────────┐     ┌─────────────────┐        │   │
│   │     │ Pod A           │     │ Pod B           │        │   │
│   │     │ Network NS      │     │ Network NS      │        │   │
│   │     │                 │     │                 │        │   │
│   │     │ eth0:10.244.1.5 │     │ eth0:10.244.1.6 │        │   │
│   │     │                 │     │                 │        │   │
│   │     └────────┬────────┘     └────────┬────────┘        │   │
│   │              │                       │                  │   │
│   │              └───────────┬───────────┘                  │   │
│   │                          │                              │   │
│   │                    ┌─────┴─────┐                        │   │
│   │                    │   Bridge  │                        │   │
│   │                    │  (cni0)   │                        │   │
│   │                    └─────┬─────┘                        │   │
│   │                          │                              │   │
│   └──────────────────────────┼──────────────────────────────┘   │
│                              │                                   │
│                         To other nodes                           │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Part 2: CNI Plugins

> **Pause and predict**: You are choosing a CNI for a new cluster. The requirements are: must support NetworkPolicy, must work on bare metal (no cloud), and the team has limited networking expertise. Looking at the comparison table below, which CNI would you choose and why?

### 2.1 Popular CNI Plugins

| Plugin | Network Policy | Performance | Use Case |
|--------|----------------|-------------|----------|
| **Calico** | Yes | High | Enterprise, security-focused |
| **Cilium** | Yes (advanced) | Very high | eBPF, observability |
| **Flannel** | No | Medium | Simple clusters |
| **Canal** | Yes | Medium | Calico policy + Flannel networking |
| **AWS VPC CNI** | Via Calico | High | EKS native |

### 2.2 How CNI Works

```
┌────────────────────────────────────────────────────────────────┐
│                   CNI Plugin Flow                               │
│                                                                 │
│   1. Pod Created                                               │
│      │                                                          │
│      ▼                                                          │
│   2. Kubelet calls CNI plugin (ADD)                            │
│      │                                                          │
│      ▼                                                          │
│   3. CNI creates network namespace                             │
│      │                                                          │
│      ▼                                                          │
│   4. CNI assigns IP address (IPAM)                             │
│      │                                                          │
│      ▼                                                          │
│   5. CNI sets up veth pair                                     │
│      │                                                          │
│      ▼                                                          │
│   6. CNI configures routing                                    │
│      │                                                          │
│      ▼                                                          │
│   7. Pod is network-ready                                      │
│                                                                 │
│   Pod Deleted:                                                  │
│      CNI plugin called with DEL → Cleanup                      │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.3 CNI Configuration Location

```bash
# CNI binary location
ls /opt/cni/bin/

# CNI configuration location
ls /etc/cni/net.d/

# Example: View CNI config
cat /etc/cni/net.d/10-calico.conflist
```

### 2.4 Checking CNI Status

```bash
# Check which CNI is installed
ls /etc/cni/net.d/

# Check CNI pods
k get pods -n kube-system | grep -E "calico|flannel|cilium"

# Check CNI daemonset
k get daemonset -n kube-system

# View CNI configuration
cat /etc/cni/net.d/*.conf* 2>/dev/null
```

---

## Part 3: Pod Networking Deep Dive

### 3.1 Pod IP Allocation

```
┌────────────────────────────────────────────────────────────────┐
│                   IP Allocation                                 │
│                                                                 │
│   Cluster CIDR: 10.244.0.0/16                                  │
│                                                                 │
│   Node 1: 10.244.0.0/24        Node 2: 10.244.1.0/24          │
│   ┌──────────────────────┐     ┌──────────────────────┐        │
│   │ Pod: 10.244.0.5      │     │ Pod: 10.244.1.3      │        │
│   │ Pod: 10.244.0.6      │     │ Pod: 10.244.1.4      │        │
│   │ Pod: 10.244.0.7      │     │ Pod: 10.244.1.5      │        │
│   └──────────────────────┘     └──────────────────────┘        │
│                                                                 │
│   Node 3: 10.244.2.0/24                                        │
│   ┌──────────────────────┐                                     │
│   │ Pod: 10.244.2.2      │                                     │
│   │ Pod: 10.244.2.3      │                                     │
│   └──────────────────────┘                                     │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Viewing Pod Network Configuration

```bash
# Get pod IP
k get pod <pod> -o wide
k get pod <pod> -o jsonpath='{.status.podIP}'

# Get all pod IPs
k get pods -o custom-columns='NAME:.metadata.name,IP:.status.podIP'

# Check which node a pod is on
k get pod <pod> -o jsonpath='{.spec.nodeName}'

# View pod network namespace (from node)
# First, get container ID
crictl ps | grep <pod-name>
# Then inspect network
crictl inspect <container-id> | jq '.info.runtimeSpec.linux.namespaces'
```

### 3.3 Pod-to-Pod Communication (Same Node)

```
┌────────────────────────────────────────────────────────────────┐
│                   Same-Node Communication                       │
│                                                                 │
│   Node                                                          │
│   ┌────────────────────────────────────────────────────────┐   │
│   │                                                         │   │
│   │   Pod A                     Pod B                      │   │
│   │   10.244.1.5                10.244.1.6                 │   │
│   │   ┌─────────┐               ┌─────────┐                │   │
│   │   │  eth0   │               │  eth0   │                │   │
│   │   └────┬────┘               └────┬────┘                │   │
│   │        │ veth pair               │ veth pair           │   │
│   │        │                         │                      │   │
│   │   ┌────┴────┐               ┌────┴────┐                │   │
│   │   │ veth-a  │               │ veth-b  │                │   │
│   │   └────┬────┘               └────┬────┘                │   │
│   │        │                         │                      │   │
│   │        └───────────┬─────────────┘                      │   │
│   │                    │                                    │   │
│   │              ┌─────┴─────┐                              │   │
│   │              │  Bridge   │ (cni0 or cbr0)              │   │
│   │              │10.244.1.1 │                              │   │
│   │              └───────────┘                              │   │
│   │                                                         │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                 │
│   Traffic: Pod A → veth-a → bridge → veth-b → Pod B           │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.4 Pod-to-Pod Communication (Different Nodes)

```
┌────────────────────────────────────────────────────────────────┐
│                 Cross-Node Communication                        │
│                                                                 │
│   Node 1 (192.168.1.10)          Node 2 (192.168.1.11)        │
│   ┌───────────────────────┐      ┌───────────────────────┐    │
│   │                       │      │                       │    │
│   │  Pod A: 10.244.1.5    │      │  Pod B: 10.244.2.6    │    │
│   │  ┌─────────┐          │      │          ┌─────────┐  │    │
│   │  │  veth   │          │      │          │  veth   │  │    │
│   │  └────┬────┘          │      │          └────┬────┘  │    │
│   │       │               │      │               │       │    │
│   │  ┌────┴────┐          │      │          ┌────┴────┐  │    │
│   │  │ Bridge  │          │      │          │ Bridge  │  │    │
│   │  └────┬────┘          │      │          └────┬────┘  │    │
│   │       │               │      │               │       │    │
│   │  ┌────┴────┐          │      │          ┌────┴────┐  │    │
│   │  │  eth0   │          │      │          │  eth0   │  │    │
│   │  └────┬────┘          │      │          └────┬────┘  │    │
│   │       │               │      │               │       │    │
│   └───────┼───────────────┘      └───────────────┼───────┘    │
│           │                                      │             │
│           └──────────────────────────────────────┘             │
│                   Overlay or Routing                            │
│                (VXLAN, IPIP, BGP, etc.)                        │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Part 4: kube-proxy and Services

### 4.1 kube-proxy Modes

| Mode | Description | Performance | Use Case |
|------|-------------|-------------|----------|
| **nftables** | Uses nftables | Best | Default in modern clusters (k8s v1.33+) |
| **iptables** | Uses iptables rules | Good | Legacy default, most older clusters |
| **IPVS** | Uses kernel IPVS | Better | High pod count (has known edge cases) |
| **userspace** | Legacy, user-space proxy | Poor | Avoid using; deprecated |

### 4.2 How kube-proxy Works

```
┌────────────────────────────────────────────────────────────────┐
│                   kube-proxy Flow                               │
│                                                                 │
│   Client Pod                                                   │
│       │                                                         │
│       │ Request to Service IP 10.96.45.123:80                  │
│       ▼                                                         │
│   ┌───────────────────────────────────────────────────────┐    │
│   │                  iptables / IPVS                       │    │
│   │                                                        │    │
│   │  PREROUTING chain:                                    │    │
│   │  10.96.45.123:80 → DNAT to pod IP (random selection)  │    │
│   │                                                        │    │
│   │  Selected: 10.244.1.5:8080                            │    │
│   └───────────────────────────────────────────────────────┘    │
│       │                                                         │
│       ▼                                                         │
│   Backend Pod (10.244.1.5:8080)                                │
│                                                                 │
│   kube-proxy watches API server for Service/Endpoint changes  │
│   and updates iptables/IPVS rules accordingly                 │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.3 Checking kube-proxy

```bash
# Check kube-proxy pods
k get pods -n kube-system -l k8s-app=kube-proxy

# Check kube-proxy mode
k logs -n kube-system -l k8s-app=kube-proxy | grep "Using"

# View kube-proxy configmap
k get configmap kube-proxy -n kube-system -o yaml

# Check iptables rules (on node)
iptables -t nat -L KUBE-SERVICES -n | head -20

# Check IPVS rules (if using IPVS mode, on node)
ipvsadm -Ln
```

---

> **Stop and think**: A new pod is stuck in `ContainerCreating` state. You check events and see "network plugin is not ready". Before you start changing CNI configuration, what three things would you check first to determine if this is a CNI installation issue or a node-specific problem?

## Part 5: Troubleshooting Network Issues

### 5.1 Network Debugging Workflow

```
Pod Network Issue?
    │
    ├── kubectl get pod -o wide (check pod IP, node)
    │
    ├── Pod has IP?
    │   ├── No → CNI issue
    │   │        Check: CNI pods, /etc/cni/net.d/, CNI logs
    │   │
    │   └── Yes → Continue
    │
    ├── Can reach other pods on same node?
    │   ├── No → Bridge/veth issue
    │   │
    │   └── Yes → Continue
    │
    ├── Can reach pods on other nodes?
    │   ├── No → Overlay/routing issue
    │   │        Check: CNI config, node routes, firewall
    │   │
    │   └── Yes → Continue
    │
    ├── Can reach services?
    │   ├── No → kube-proxy or DNS issue
    │   │        Check: kube-proxy, CoreDNS, iptables
    │   │
    │   └── Yes → Network is fine, check app
    │
    └── Check NetworkPolicy
        kubectl get networkpolicy
```

### 5.2 Common Debugging Commands

```bash
# Check pod network
k exec <pod> -- ip addr
k exec <pod> -- ip route
k exec <pod> -- cat /etc/resolv.conf

# Test connectivity
k exec <pod> -- ping <other-pod-ip>
k exec <pod> -- nc -zv <service> <port>
k exec <pod> -- wget --spider --timeout=1 http://<service>

# Check CNI pods
k get pods -n kube-system | grep -E "calico|flannel|cilium"
k logs -n kube-system <cni-pod>

# Check kube-proxy
k get pods -n kube-system -l k8s-app=kube-proxy
k logs -n kube-system -l k8s-app=kube-proxy

# Check CoreDNS
k get pods -n kube-system -l k8s-app=kube-dns
k logs -n kube-system -l k8s-app=kube-dns
```

### 5.3 Common Network Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Pod stuck in ContainerCreating | CNI not installed or failing | Install/fix CNI plugin |
| Pod has no IP | IPAM exhausted or CNI error | Check CNI logs, expand CIDR |
| Can't reach pods on other nodes | Overlay misconfigured | Check CNI network config |
| Services unreachable | kube-proxy not running | Check kube-proxy pods |
| DNS not working | CoreDNS down | Check CoreDNS pods |
| NetworkPolicy not working | CNI doesn't support it | Use Calico or Cilium |

---

## Part 6: Cluster CIDR Configuration

### 6.1 Understanding CIDRs

| CIDR Type | Description | Example |
|-----------|-------------|---------|
| **Pod CIDR** | IP range for all pods | 10.244.0.0/16 |
| **Service CIDR** | IP range for services | 10.96.0.0/12 |
| **Node CIDR** | Pod range per node | 10.244.1.0/24 |

### 6.2 Checking CIDR Configuration

```bash
# Check pod CIDR (from kube-controller-manager)
k get cm kubeadm-config -n kube-system -o yaml | grep -i cidr

# Check from nodes
k get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.podCIDR}{"\n"}{end}'

# Check service CIDR
k cluster-info dump | grep -m 1 service-cluster-ip-range
```

### 6.3 kubeadm CIDR Configuration

```bash
# During cluster init
kubeadm init --pod-network-cidr=10.244.0.0/16 --service-cidr=10.96.0.0/12

# The CNI plugin must match this CIDR
# Example: Calico installation with matching CIDR
```

---

> **Pause and predict**: You set `hostNetwork: true` on a pod running nginx on port 80, and there is already another pod with `hostNetwork: true` running on port 80 on the same node. What happens when Kubernetes tries to schedule your pod?

## Part 7: Host Network and Node Ports

### 7.1 hostNetwork Pods

```yaml
# Pod using host network
apiVersion: v1
kind: Pod
metadata:
  name: host-network-pod
spec:
  hostNetwork: true         # Uses node's network namespace
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80     # Binds to node's port 80!
```

When to use:
- Network tools that need raw access
- Some CNI components
- High-performance networking

### 7.2 hostPort

```yaml
# Pod with host port mapping
apiVersion: v1
kind: Pod
metadata:
  name: hostport-pod
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 8080
      hostPort: 80           # Node's port 80 → container 8080
```

Differences:
- `hostNetwork: true` - Pod uses node's entire network stack
- `hostPort` - Only maps specific port, pod still has its own IP

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No CNI installed | Pods can't get IPs | Install CNI before deploying pods |
| CIDR mismatch | CNI and kubeadm disagree | Ensure pod-network-cidr matches CNI config |
| Flannel + NetworkPolicy | Policies ignored | Use Calico or Cilium |
| hostNetwork without dnsPolicy | DNS breaks | Set `dnsPolicy: ClusterFirstWithHostNet` |
| Port exhaustion | Can't schedule pods | Check CIDR size, clean up pods |

---

## Quiz

1. **After initializing a cluster with `kubeadm init`, you notice all pods except those in `kube-system` are stuck in `Pending` or `ContainerCreating`. CoreDNS pods also show `ContainerCreating`. What is the root cause and what must you do before deploying any workloads?**
   <details>
   <summary>Answer</summary>
   No CNI plugin is installed. Kubernetes does not ship with networking -- you must install a CNI plugin (Calico, Cilium, Flannel, etc.) before pods can get IP addresses and communicate. CoreDNS pods are also stuck because they need pod networking to start. The fix: install a CNI plugin that matches the `--pod-network-cidr` specified during `kubeadm init`. For example, if you used `--pod-network-cidr=10.244.0.0/16`, install Calico or Flannel configured for that CIDR. Until the CNI is installed, the node will show `NotReady` status.
   </details>

2. **Your cluster uses Flannel and a security team member creates NetworkPolicies to isolate the production namespace. After deploying the policies, they test and find that pods can still communicate freely across namespaces. The YAML is correct. What went wrong?**
   <details>
   <summary>Answer</summary>
   Flannel does not support NetworkPolicy enforcement. The API server accepts the NetworkPolicy objects (they are valid Kubernetes resources), but without a CNI that implements the network policy controller, they are never enforced. This is a dangerous situation because it gives a false sense of security. The options are: (1) Replace Flannel with Calico or Cilium which natively support NetworkPolicy; (2) Install Canal, which combines Flannel's networking with Calico's policy engine; or (3) add a standalone policy engine alongside Flannel (e.g., Calico policy-only mode).
   </details>

3. **Pods on Node A can reach pods on Node A, but cannot reach pods on Node B. All pods have IPs and are in Running state. Both nodes show `Ready`. Where in the networking stack is the problem, and how would you diagnose it?**
   <details>
   <summary>Answer</summary>
   This is a CNI cross-node routing issue. Same-node traffic works (the bridge handles it), but cross-node traffic fails, pointing to the overlay or routing layer. Diagnosis steps: (1) Check CNI daemon pods on both nodes: `k get pods -n kube-system -o wide | grep -E "calico|flannel|cilium"`. (2) Check if the CNI tunnel interface exists on both nodes (e.g., `flannel.1` for VXLAN, `tunl0` for Calico IPIP). (3) Verify the node-to-node path allows the CNI protocol (VXLAN uses UDP 4789, BGP uses TCP 179 -- check cloud security groups or host firewalls). (4) Check routes on each node: `ip route` should show routes to the other node's pod CIDR.
   </details>

4. **Your cluster runs 8,000 Services. During peak traffic, kube-proxy on each node takes 30 seconds to update rules after a Service change, and CPU spikes on all nodes. The cluster uses iptables mode. What is happening and what is the recommended fix?**
   <details>
   <summary>Answer</summary>
   In iptables mode, kube-proxy creates iptables rules for every Service and Endpoint combination. With 8,000 Services, this generates tens of thousands of rules. Every change requires rewriting a large portion of the iptables ruleset, causing the CPU spike. Rule evaluation is also O(n), slowing packet processing. The fix is to switch kube-proxy to nftables mode (kernel 5.13+, k8s v1.33+) which provides significantly better performance, or IPVS mode if nftables is unavailable. Alternatively, for even better performance, consider using Cilium in eBPF kube-proxy replacement mode, which moves Service routing entirely into eBPF programs.
   </details>

5. **A developer created a pod with `hostNetwork: true` but did not set `dnsPolicy`. The pod can reach external websites by IP but cannot resolve any cluster service names. External DNS resolution (like `google.com`) works fine. Explain the root cause and the one-line fix.**
   <details>
   <summary>Answer</summary>
   When `hostNetwork: true` is set, the pod shares the node's network namespace, including its `/etc/resolv.conf`. The node's resolv.conf points to the infrastructure DNS server (e.g., the cloud provider's DNS or a corporate DNS), not CoreDNS. This DNS server knows about external names like `google.com` but nothing about cluster-internal names like `my-svc.default.svc.cluster.local`. The fix: set `dnsPolicy: ClusterFirstWithHostNet` in the pod spec. This tells the kubelet to inject the CoreDNS address into the pod's resolv.conf, enabling cluster DNS resolution even though the pod uses the host network.
   </details>

---

## Hands-On Exercise

**Task**: Investigate cluster networking configuration.

**Steps**:

1. **Check CNI plugin installed**:
```bash
# Check CNI pods
k get pods -n kube-system | grep -E "calico|flannel|cilium|cni"

# Check CNI configuration
ls /etc/cni/net.d/ 2>/dev/null || echo "Run on node"
```

2. **Check pod CIDR**:
```bash
# Get node CIDRs
k get nodes -o jsonpath='{range .items[*]}{.metadata.name}{": "}{.spec.podCIDR}{"\n"}{end}'
```

3. **Create test pods**:
```bash
k run pod1 --image=busybox:1.36 --command -- sleep 3600
k run pod2 --image=busybox:1.36 --command -- sleep 3600

# Wait for ready
k wait --for=condition=ready pod/pod1 pod/pod2 --timeout=60s
```

4. **Check pod network configuration**:
```bash
# Get pod IPs
k get pods -o wide

# Check pod network interface
k exec pod1 -- ip addr
k exec pod1 -- ip route

# Check DNS configuration
k exec pod1 -- cat /etc/resolv.conf
```

5. **Test pod-to-pod connectivity**:
```bash
POD2_IP=$(k get pod pod2 -o jsonpath='{.status.podIP}')
k exec pod1 -- ping -c 3 $POD2_IP
```

6. **Check kube-proxy**:
```bash
# Check kube-proxy pods
k get pods -n kube-system -l k8s-app=kube-proxy

# Check kube-proxy logs for mode
k logs -n kube-system -l k8s-app=kube-proxy --tail=5 | grep -i mode
```

7. **Test service connectivity**:
```bash
# Create service
k create deployment web --image=nginx
k expose deployment web --port=80

# Wait for deployment
k wait --for=condition=available deployment/web --timeout=60s

# Test DNS and connectivity
k exec pod1 -- wget --spider --timeout=2 http://web
```

8. **Cleanup**:
```bash
k delete pod pod1 pod2
k delete deployment web
k delete svc web
```

**Success Criteria**:
- [ ] Can identify CNI plugin in use
- [ ] Understand pod CIDR allocation
- [ ] Can verify pod-to-pod connectivity
- [ ] Know how to check kube-proxy
- [ ] Understand network troubleshooting

---

## Practice Drills

### Drill 1: Identify CNI (Target: 2 minutes)

```bash
# Check CNI pods in kube-system
k get pods -n kube-system | grep -E "calico|flannel|cilium|canal"

# Check CNI daemonsets
k get ds -n kube-system

# Check node annotations for CNI
k get nodes -o jsonpath='{.items[0].metadata.annotations}' | jq 'keys'
```

### Drill 2: Check Pod CIDR (Target: 2 minutes)

```bash
# Get pod CIDR from nodes
k get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.podCIDR}{"\n"}{end}'

# Check from kubeadm config (if available)
k get cm kubeadm-config -n kube-system -o yaml 2>/dev/null | grep -i cidr

# Check from controller-manager
k get pods -n kube-system -l component=kube-controller-manager -o yaml | grep cluster-cidr
```

### Drill 3: Pod Network Info (Target: 3 minutes)

```bash
# Create test pod
k run net-test --image=busybox:1.36 --command -- sleep 3600
k wait --for=condition=ready pod/net-test --timeout=60s

# Check network info
k exec net-test -- ip addr
k exec net-test -- ip route
k exec net-test -- cat /etc/resolv.conf

# Cleanup
k delete pod net-test
```

### Drill 4: kube-proxy Mode (Target: 2 minutes)

```bash
# Check kube-proxy configmap
k get configmap kube-proxy -n kube-system -o yaml | grep -A5 "mode:"

# Check from logs
k logs -n kube-system -l k8s-app=kube-proxy --tail=20 | grep -i "using"

# List kube-proxy pods
k get pods -n kube-system -l k8s-app=kube-proxy -o wide
```

### Drill 5: Test Pod Connectivity (Target: 4 minutes)

```bash
# Create pods
k run client --image=busybox:1.36 --command -- sleep 3600
k run server --image=nginx
k wait --for=condition=ready pod/client pod/server --timeout=60s

# Get server IP
SERVER_IP=$(k get pod server -o jsonpath='{.status.podIP}')

# Test connectivity
k exec client -- ping -c 2 $SERVER_IP
k exec client -- wget --spider --timeout=2 http://$SERVER_IP

# Cleanup
k delete pod client server
```

### Drill 6: Service Routing Check (Target: 3 minutes)

```bash
# Create deployment and service
k create deployment svc-test --image=nginx
k expose deployment svc-test --port=80
k wait --for=condition=available deployment/svc-test --timeout=60s

# Get ClusterIP
CLUSTER_IP=$(k get svc svc-test -o jsonpath='{.spec.clusterIP}')

# Test service
k run test --rm -i --image=busybox:1.36 --restart=Never -- \
  wget --spider --timeout=2 http://$CLUSTER_IP

# Cleanup
k delete deployment svc-test
k delete svc svc-test
```

### Drill 7: hostNetwork Pod (Target: 3 minutes)

```bash
# Create hostNetwork pod
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: host-net
spec:
  hostNetwork: true
  dnsPolicy: ClusterFirstWithHostNet
  containers:
  - name: test
    image: busybox:1.36
    command: ["sleep", "3600"]
EOF

k wait --for=condition=ready pod/host-net --timeout=60s

# Check - IP should match node IP
k get pod host-net -o wide

# Compare with node
k exec host-net -- ip addr

# Test can still resolve services
k exec host-net -- nslookup kubernetes

# Cleanup
k delete pod host-net
```

### Drill 8: Challenge - Network Troubleshooting

Without looking at solutions:

1. Create two pods: `client` and `server` (nginx)
2. Get both pod IPs
3. Test ping from client to server
4. Create a service for server
5. Test DNS resolution of service from client
6. Test HTTP connectivity to service from client
7. Check which CNI is running
8. Cleanup everything

```bash
# YOUR TASK: Complete in under 5 minutes
```

<details>
<summary>Solution</summary>

```bash
# 1. Create pods
k run client --image=busybox:1.36 --command -- sleep 3600
k run server --image=nginx
k wait --for=condition=ready pod/client pod/server --timeout=60s

# 2. Get IPs
k get pods -o wide

# 3. Test ping
SERVER_IP=$(k get pod server -o jsonpath='{.status.podIP}')
k exec client -- ping -c 2 $SERVER_IP

# 4. Create service
k expose pod server --port=80 --name=server-svc

# 5. Test DNS
k exec client -- nslookup server-svc

# 6. Test HTTP
k exec client -- wget --spider --timeout=2 http://server-svc

# 7. Check CNI
k get pods -n kube-system | grep -E "calico|flannel|cilium"

# 8. Cleanup
k delete pod client server
k delete svc server-svc
```

</details>

---

## Next Steps

Congratulations on completing Part 3! You now understand:
- Services and how to expose applications
- Endpoints and how services track pods
- DNS and service discovery
- Ingress for HTTP routing
- Gateway API for next-gen routing
- Network Policies for security
- CNI and cluster networking

Take the [Part 3 Cumulative Quiz](../part3-cumulative-quiz/) to test your knowledge.

## Sources

- [Cluster Networking](https://kubernetes.io/docs/concepts/cluster-administration/networking/) — Best Kubernetes-side overview of the network model, IP ranges, and where CNI fits.
- [CNI Specification](https://github.com/containernetworking/cni/blob/main/SPEC.md) — Defines the runtime-plugin contract, including ADD/DEL, namespaces, and attachment lifecycle.
- [Virtual IPs and Service Proxies](https://kubernetes.io/docs/reference/networking/virtual-ips/) — Covers kube-proxy behavior, EndpointSlice watching, and the current state of iptables, IPVS, and nftables modes.
