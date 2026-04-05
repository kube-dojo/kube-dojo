---
title: "Module 3.4: iptables & netfilter"
slug: linux/foundations/networking/module-3.4-iptables-netfilter
sidebar:
  order: 5
lab:
  id: "linux-3.4-iptables"
  url: "https://killercoda.com/kubedojo/scenario/linux-3.4-iptables"
  duration: "45 min"
  difficulty: "advanced"
  environment: "ubuntu"
---
> **Linux Foundations** | Complexity: `[COMPLEX]` | Time: 35-40 min

## Prerequisites

Before starting this module:
- **Required**: [Module 3.1: TCP/IP Essentials](../module-3.1-tcp-ip-essentials/)
- **Required**: [Module 3.3: Network Namespaces](../module-3.3-network-namespaces/)
- **Helpful**: Basic understanding of firewalls

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Explain** the netfilter hook points and how iptables rules are evaluated (tables, chains, targets)
- **Trace** how Kubernetes Services use iptables rules for load balancing (kube-proxy iptables mode)
- **Write** iptables rules for basic packet filtering, NAT, and port forwarding
- **Debug** network connectivity issues by reading iptables counters and rule chains

---

## Why This Module Matters

iptables (and netfilter) is the packet filtering and manipulation framework in Linux. It powers:

- **Kubernetes Services** — ClusterIP, NodePort use iptables rules
- **Network Policies** — Filtering between pods
- **NAT** — How containers reach the internet
- **Load Balancing** — kube-proxy iptables mode

When services don't work, pods can't communicate, or traffic doesn't flow as expected—understanding iptables is essential for debugging.

---

## Did You Know?

- **A busy Kubernetes node can have 10,000+ iptables rules** — Each service creates multiple rules. Kubernetes 1.35 deprecated IPVS mode in kube-proxy and is moving toward **nftables** as the recommended backend for better performance at scale.

- **iptables is just the CLI** — The actual packet filtering happens in the kernel's netfilter subsystem. iptables is the user-space tool to configure it.

- **nftables is replacing iptables** — Modern Linux distributions (RHEL 9+, Debian 11+) ship nftables by default. Kubernetes 1.35 deprecated IPVS mode in kube-proxy and recommends nftables. The `nft` command replaces `iptables` with a cleaner syntax and better performance.

- **Every Kubernetes service creates at least 5 iptables rules** — For the KUBE-SERVICES chain, plus per-endpoint rules. With 100 services x 3 endpoints each, that's 1500+ rules — one reason the ecosystem is moving to nftables.

---

## Netfilter Architecture

### Packet Flow Through Netfilter

```
┌─────────────────────────────────────────────────────────────────┐
│                    NETFILTER PACKET FLOW                         │
│                                                                  │
│                       Incoming Packet                            │
│                            │                                     │
│                            ▼                                     │
│                     ┌──────────────┐                            │
│                     │  PREROUTING  │  (raw, mangle, nat)        │
│                     └──────┬───────┘                            │
│                            │                                     │
│               ┌────────────▼────────────┐                       │
│               │    Routing Decision     │                       │
│               └────────────┬────────────┘                       │
│                    ┌───────┴───────┐                            │
│                    ▼               ▼                            │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │      INPUT          │  │     FORWARD         │              │
│  │  (for this host)    │  │  (for other host)   │              │
│  └──────────┬──────────┘  └──────────┬──────────┘              │
│             │                        │                          │
│             ▼                        │                          │
│     Local Process                    │                          │
│             │                        │                          │
│             ▼                        │                          │
│  ┌─────────────────────┐            │                          │
│  │      OUTPUT         │            │                          │
│  │  (from this host)   │            │                          │
│  └──────────┬──────────┘            │                          │
│             │                        │                          │
│             └────────────┬───────────┘                          │
│                          ▼                                      │
│                   ┌──────────────┐                              │
│                   │ POSTROUTING  │  (mangle, nat)               │
│                   └──────┬───────┘                              │
│                          │                                      │
│                          ▼                                      │
│                    Outgoing Packet                              │
└─────────────────────────────────────────────────────────────────┘
```

### The Five Chains

| Chain | Purpose | When |
|-------|---------|------|
| PREROUTING | Before routing decision | Incoming packets |
| INPUT | For local delivery | Destined for this host |
| FORWARD | For routing | Passing through this host |
| OUTPUT | From local processes | Generated by this host |
| POSTROUTING | After routing | Leaving this host |

> **Stop and think**: If a packet needs to be dropped to block an attacker, in which chain of the `filter` table should you place the rule to drop it as early as possible before it reaches a local process?

### The Tables

| Table | Purpose | Chains |
|-------|---------|--------|
| filter | Accept/drop packets | INPUT, FORWARD, OUTPUT |
| nat | Address translation | PREROUTING, OUTPUT, POSTROUTING |
| mangle | Packet modification | All chains |
| raw | Connection tracking exceptions | PREROUTING, OUTPUT |

---

## iptables Basics

### Rule Structure

```
iptables -t <table> -A <chain> <match> -j <target>

Example:
iptables -t filter -A INPUT -p tcp --dport 22 -j ACCEPT
         │         │        │                   │
         │         │        │                   └── Action: Accept
         │         │        └── Match: TCP port 22
         │         └── Append to INPUT chain
         └── Table: filter (default)
```

### Common Targets

| Target | Action |
|--------|--------|
| ACCEPT | Allow packet |
| DROP | Silently discard |
| REJECT | Discard with error |
| LOG | Log and continue |
| SNAT | Source NAT |
| DNAT | Destination NAT |
| MASQUERADE | Dynamic SNAT |
| RETURN | Return from chain |

### Viewing Rules

```bash
# List all filter rules
sudo iptables -L -n -v

# List specific chain
sudo iptables -L INPUT -n -v

# List nat table
sudo iptables -t nat -L -n -v

# Show line numbers (useful for deletion)
sudo iptables -L INPUT -n --line-numbers

# Show rules as commands
sudo iptables-save
```

---

## Practical iptables

### Basic Firewall Rules

```bash
# Accept established connections
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Accept loopback
sudo iptables -A INPUT -i lo -j ACCEPT

# Accept SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Accept HTTP/HTTPS
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Drop everything else
sudo iptables -A INPUT -j DROP
```

### NAT Examples

```bash
# MASQUERADE: Source NAT for containers (dynamic)
sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE

# SNAT: Source NAT with specific IP
sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j SNAT --to-source 192.168.1.100

# DNAT: Destination NAT (port forwarding)
sudo iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 10.0.0.5:80

# Redirect to local port
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080
```

### Managing Rules

```bash
# Insert at position (vs append)
sudo iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT

# Delete by specification
sudo iptables -D INPUT -p tcp --dport 22 -j ACCEPT

# Delete by line number
sudo iptables -D INPUT 3

# Flush all rules in chain
sudo iptables -F INPUT

# Flush all rules
sudo iptables -F

# Save rules (Debian/Ubuntu)
sudo iptables-save > /etc/iptables/rules.v4

# Restore rules
sudo iptables-restore < /etc/iptables/rules.v4
```

---

## Kubernetes and iptables

### kube-proxy iptables Mode

kube-proxy creates iptables rules for Services.

```
┌─────────────────────────────────────────────────────────────────┐
│              KUBERNETES SERVICE IPTABLES                         │
│                                                                  │
│  Service: my-svc (ClusterIP: 10.96.0.100, Port: 80)            │
│  Endpoints: 10.244.1.5:8080, 10.244.2.6:8080                   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ KUBE-SERVICES chain:                                     │   │
│  │   -d 10.96.0.100/32 -p tcp --dport 80 -j KUBE-SVC-XXX   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ KUBE-SVC-XXX chain (load balancing):                    │   │
│  │   -m statistic --probability 0.5 -j KUBE-SEP-AAA        │   │
│  │   -j KUBE-SEP-BBB                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                    │                  │                         │
│                    ▼                  ▼                         │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ KUBE-SEP-AAA:       │  │ KUBE-SEP-BBB:       │              │
│  │  DNAT to 10.244.1.5 │  │  DNAT to 10.244.2.6 │              │
│  └─────────────────────┘  └─────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

> **Pause and predict**: If you list the nat table on a Kubernetes node running kube-proxy, what chains do you expect to see custom rules heavily populated in?

### Viewing Kubernetes iptables Rules

```bash
# All service-related rules
sudo iptables -t nat -L KUBE-SERVICES -n

# Find rules for a specific service
sudo iptables-save | grep "my-service"

# Count rules
sudo iptables-save | wc -l
sudo iptables -t nat -L | wc -l
```

### NodePort Implementation

```
┌─────────────────────────────────────────────────────────────────┐
│                  NODEPORT IPTABLES                               │
│                                                                  │
│  Service: my-svc NodePort 30080                                 │
│                                                                  │
│  1. KUBE-NODEPORTS chain catches traffic to 30080              │
│     -p tcp --dport 30080 -j KUBE-SVC-XXX                       │
│                                                                  │
│  2. KUBE-SVC-XXX forwards to endpoints (same as ClusterIP)     │
│                                                                  │
│  3. If externalTrafficPolicy: Local, only local endpoints      │
│     KUBE-XLB-XXX chain filters                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Network Policies

Network policies also use iptables (or eBPF in Cilium).

```bash
# Network policy rules (typically in KUBE-NWPLCY chains)
sudo iptables -L KUBE-NWPLCY-* -n 2>/dev/null

# Calico uses its own chains
sudo iptables -L cali-* -n 2>/dev/null | head -50
```

---

## iptables vs IPVS vs eBPF

### Comparison

| Feature | iptables | IPVS | eBPF (Cilium) |
|---------|----------|------|---------------|
| Rule complexity | O(n) | O(1) hash | O(1) |
| Large clusters | Slow | Fast | Fastest |
| Setup complexity | Simple | Medium | Complex |
| Load balancing | Random | Multiple algos | Multiple algos |
| Connection tracking | conntrack | Built-in | Efficient |

### When to Use What

```
Small cluster (< 100 services): iptables is fine
Medium cluster (100-1000 services): Consider IPVS
Large cluster (1000+ services): IPVS or eBPF
Advanced features needed: eBPF (Cilium)
```

### Checking kube-proxy Mode

```bash
# Check kube-proxy mode
kubectl get configmap kube-proxy -n kube-system -o yaml | grep mode

# Or check logs
kubectl logs -n kube-system -l k8s-app=kube-proxy | head -50
```

---

## Debugging iptables

### Tracing Packets

```bash
# Enable tracing
sudo iptables -t raw -A PREROUTING -p tcp --dport 80 -j TRACE
sudo iptables -t raw -A OUTPUT -p tcp --dport 80 -j TRACE

# View traces
sudo dmesg | grep TRACE

# Or
sudo tail -f /var/log/kern.log | grep TRACE

# Don't forget to remove trace rules when done!
```

### Common Issues

```bash
# Check if traffic is hitting rules
sudo iptables -L INPUT -n -v
# Look at packet/byte counters

# Check NAT
sudo iptables -t nat -L -n -v

# Check for DROP rules
sudo iptables-save | grep DROP

# Watch counters in real-time
watch -n1 'sudo iptables -L INPUT -n -v'
```

### Packet Counters

```bash
# Reset counters
sudo iptables -Z

# View counters (pkts and bytes columns)
sudo iptables -L -n -v

# Find rules with traffic
sudo iptables-save -c | grep -v "0:0"
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Rule order wrong | Traffic hits wrong rule | Check order, use -I for priority |
| Forgot state tracking | Responses blocked | Add ESTABLISHED,RELATED rule |
| Flushed rules remotely | Locked out | Use iptables-apply or console |
| Missing FORWARD rules | Containers can't route | Enable and configure FORWARD |
| NAT without forwarding | NAT doesn't work | Enable ip_forward sysctl |
| Too many rules | Performance degradation | Consider IPVS |

---

## Quiz

### Question 1
You are designing a firewall policy for a public-facing Kubernetes node. Your security team wants to minimize the information an attacker can gather from port scanning, while your developers want immediate feedback when their internal tools try to hit blocked ports. Which targets (DROP or REJECT) should you use for the external-facing rules versus the internal-facing rules, and why?

<details>
<summary>Show Answer</summary>

- **DROP**: Silently discards the packet. Sender gets no response and eventually times out.
- **REJECT**: Sends an ICMP error back (e.g., "port unreachable"). Sender knows immediately.

For the external-facing rules, you should use the DROP target. This is because DROP silently discards packets, forcing an attacker's port scanner to wait for timeouts, which drastically slows down their reconnaissance and reveals no information about the firewall's existence. For the internal-facing rules, you should use the REJECT target. REJECT actively sends an ICMP error back to the sender, which allows internal developer tools to fail fast and immediately log a "connection refused" or "unreachable" error, saving time during internal troubleshooting.

</details>

### Question 2
You have deployed a new microservice with three replica Pods, and exposed it via a ClusterIP Service. When you send 100 requests to the Service IP, you notice the traffic is roughly distributed across all three Pods. Since iptables evaluates rules sequentially top-to-bottom, how exactly is kube-proxy configuring iptables to achieve this probabilistic load balancing instead of sending all traffic to the first matching rule?

<details>
<summary>Show Answer</summary>

Using the **statistic module** with probability:

```
-m statistic --mode random --probability 0.5 -j KUBE-SEP-AAA
-j KUBE-SEP-BBB
```

For 2 endpoints: 50% chance of first rule (endpoint A), otherwise falls through to endpoint B.
For 3 endpoints: 33% first, 50% of remaining (33%) second, rest to third.

Because iptables rules are processed in order, kube-proxy must use the `statistic` module to create a random chance of matching a specific endpoint's rule. If the first rule has a 33% probability and matches, traffic goes to the first Pod; if it doesn't match, the packet falls through to the next rule. The subsequent rules adjust their probabilities (e.g., 50% of the remaining 66%) so that mathematically, each of the three endpoints ends up receiving an equal 33% share of the overall traffic.

</details>

### Question 3
A pod is trying to reach an external API, but the external API server requires traffic to come from your Node's public IP address, not the Pod's internal 10.x.x.x IP. To fix this, you need to configure masquerading (SNAT) for outgoing traffic. Which specific netfilter table and chain must you add your rule to, and why?

<details>
<summary>Show Answer</summary>

The **nat** table. It has three chains:
- **PREROUTING**: DNAT (change destination before routing)
- **OUTPUT**: DNAT for locally-generated packets
- **POSTROUTING**: SNAT/MASQUERADE (change source after routing)

You must add the rule to the `nat` table because it is specifically designed and optimized by the kernel for translating source or destination IP addresses. Within the `nat` table, you must place the rule in the `POSTROUTING` chain. This is because Source NAT (modifying the packet's source IP to match the Node's IP) must happen after the kernel has already made the routing decision and determined which outbound network interface the packet will leave from.

</details>

### Question 4
Your organization recently scaled its Kubernetes cluster from 50 microservices to over 2,000 services. Suddenly, you notice that new connections are experiencing high latency, and the nodes are seeing increased CPU usage in the kernel space. A senior engineer suggests switching kube-proxy from `iptables` mode to `ipvs` or an eBPF-based solution like Cilium. Why is the current `iptables` mode causing these performance issues at this scale?

<details>
<summary>Show Answer</summary>

iptables rule matching is **O(n)** — packets traverse rules sequentially until a match.

With 1000 services × ~5 rules each = 5000+ rules. Each packet potentially traverses thousands of rules.

Solutions:
- Use **IPVS mode** (O(1) hash lookup)
- Use **Cilium/eBPF** (kernel-level efficiency)
- Reduce number of services

The performance degradation occurs because iptables was originally designed as a simple firewall, evaluating rules linearly from top to bottom. In a cluster with 2,000 services, kube-proxy creates tens of thousands of iptables rules, meaning every new connection must sequentially check against a massive list until it finds a match. This O(n) linear lookup consumes significant kernel CPU time and introduces latency, whereas IPVS or eBPF use highly efficient O(1) hash tables that can instantly route packets regardless of how many services exist.

</details>

### Question 5
Your developer team has deployed several containers on a custom Linux host using a bridge network (`10.0.0.0/24`). The containers can ping each other, but they cannot download packages from the internet. You execute the command `iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE` and the internet connectivity instantly starts working. What exactly did this command do to fix the outbound traffic?

<details>
<summary>Show Answer</summary>

**Source NAT for outgoing traffic**:
- `-t nat`: NAT table
- `-A POSTROUTING`: After routing decision
- `-s 10.0.0.0/24`: Source is internal network
- `-o eth0`: Going out eth0
- `-j MASQUERADE`: Replace source IP with eth0's IP

The command fixed the issue by enabling Source NAT (Network Address Translation) for the containers. Internet routers do not know how to route traffic back to your internal private `10.0.0.0/24` subnet, so packets were being dropped. By appending a `MASQUERADE` rule to the `POSTROUTING` chain, the Linux host now dynamically rewrites the source IP of the outbound packets from the container's private IP to the host's public `eth0` IP before they leave the machine, allowing the return traffic to successfully find its way back.

</details>

---

## Hands-On Exercise

### iptables Exploration

**Objective**: Understand iptables rules and how Kubernetes uses them.

**Environment**: Linux system, ideally with Kubernetes

#### Part 1: Basic iptables

```bash
# 1. View current rules
sudo iptables -L -n -v

# 2. View NAT rules
sudo iptables -t nat -L -n -v

# 3. Save current rules
sudo iptables-save > /tmp/iptables-backup.txt
cat /tmp/iptables-backup.txt
```

#### Part 2: Create Simple Rules

```bash
# 1. Create a test chain
sudo iptables -N TEST_CHAIN

# 2. Add rules to chain
sudo iptables -A TEST_CHAIN -p icmp -j LOG --log-prefix "PING: "
sudo iptables -A TEST_CHAIN -p icmp -j ACCEPT

# 3. Link from INPUT
sudo iptables -A INPUT -j TEST_CHAIN

# 4. Test (ping yourself)
ping -c 2 127.0.0.1

# 5. Check logs
sudo dmesg | grep "PING:" | tail -5

# 6. Check counters
sudo iptables -L TEST_CHAIN -n -v

# 7. Cleanup
sudo iptables -D INPUT -j TEST_CHAIN
sudo iptables -F TEST_CHAIN
sudo iptables -X TEST_CHAIN
```

#### Part 3: NAT Example

```bash
# 1. Enable forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# 2. View current NAT
sudo iptables -t nat -L -n -v

# 3. Add a port redirect (local)
sudo iptables -t nat -A OUTPUT -p tcp --dport 8888 -j REDIRECT --to-port 80

# 4. Test (if web server on 80)
# curl localhost:8888  # Would go to localhost:80

# 5. Remove rule
sudo iptables -t nat -D OUTPUT -p tcp --dport 8888 -j REDIRECT --to-port 80
```

#### Part 4: Kubernetes iptables (if available)

```bash
# 1. Count Kubernetes rules
sudo iptables-save | grep -c KUBE

# 2. View service chains
sudo iptables -t nat -L KUBE-SERVICES -n | head -20

# 3. Trace a specific service
# Find your service's ClusterIP
kubectl get svc my-service -o wide

# Find iptables rules for it
sudo iptables-save | grep <ClusterIP>

# 4. View DNAT rules
sudo iptables -t nat -L -n | grep DNAT | head -10
```

#### Part 5: Rule Analysis

```bash
# 1. Find busiest rules (most packets)
sudo iptables -L -n -v | sort -k1 -n -r | head -10

# 2. Find all DROP rules
sudo iptables-save | grep DROP

# 3. Count rules by table
echo "filter: $(sudo iptables -L | wc -l)"
echo "nat: $(sudo iptables -t nat -L | wc -l)"
echo "mangle: $(sudo iptables -t mangle -L | wc -l)"
```

### Success Criteria

- [ ] Viewed and understood iptables output
- [ ] Created and tested a custom chain
- [ ] Understood NAT rule syntax
- [ ] (Kubernetes) Found service-related iptables rules
- [ ] Can interpret rule counters

---

## Key Takeaways

1. **netfilter is the engine** — iptables is just the configuration tool

2. **Five chains, four tables** — Know the packet flow through them

3. **Kubernetes relies on iptables** — Services, NodePorts, network policies

4. **Rule order matters** — First match wins

5. **Performance at scale** — Consider IPVS or eBPF for large clusters

---

## What's Next?

Congratulations! You've completed the **Networking** section of Linux Foundations. You now understand:
- TCP/IP fundamentals
- DNS resolution
- Network namespaces and container networking
- iptables and how Kubernetes uses it

Next, continue to **Section 4: Security/Hardening** to learn about kernel hardening, AppArmor, SELinux, and seccomp.

---

## Further Reading

- [Netfilter Documentation](https://netfilter.org/documentation/)
- [iptables Tutorial](https://www.frozentux.net/iptables-tutorial/iptables-tutorial.html)
- [Kubernetes Network Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/)
- [Life of a Packet in Kubernetes](https://dramasamy.medium.com/life-of-a-packet-in-kubernetes-part-1-f9bc0909e051)