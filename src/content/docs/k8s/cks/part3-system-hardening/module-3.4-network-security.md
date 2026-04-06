---
title: "Module 3.4: Host Network Security"
slug: k8s/cks/part3-system-hardening/module-3.4-network-security
sidebar:
  order: 4
lab:
  id: cks-3.4-network-security
  url: https://killercoda.com/kubedojo/scenario/cks-3.4-network-security
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Network administration with security focus
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: Module 3.3 (Kernel Hardening), basic networking knowledge

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Configure** host-level firewalls (iptables/nftables) to protect Kubernetes node ports
2. **Audit** exposed node services and ports for unnecessary attack surface
3. **Implement** network segmentation between control plane, worker nodes, and external networks
4. **Diagnose** host network security issues that bypass container-level NetworkPolicies

---

## Why This Module Matters

While Kubernetes NetworkPolicies control pod-to-pod traffic, host-level network security protects the nodes themselves. Open ports, exposed services, and unfiltered traffic at the host level can bypass container isolation entirely.

CKS expects you to understand both container and host network security.

---

## Host Network Attack Surface

```
┌─────────────────────────────────────────────────────────────┐
│              HOST NETWORK ATTACK SURFACE                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Internet / External Network                               │
│     │                                                       │
│     ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              HOST (Kubernetes Node)                  │   │
│  │                                                      │   │
│  │  Exposed Services:                                  │   │
│  │  ├── :22    SSH (management)                        │   │
│  │  ├── :6443  API Server (control plane)              │   │
│  │  ├── :10250 Kubelet API                             │   │
│  │  ├── :10255 Kubelet read-only (should be disabled!) │   │
│  │  ├── :2379  etcd (control plane)                    │   │
│  │  └── :30000-32767 NodePort services                 │   │
│  │                                                      │   │
│  │  Pod with hostNetwork: true                         │   │
│  │  └── Has access to ALL host network interfaces      │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ⚠️  Each open port is a potential entry point            │
│  ⚠️  hostNetwork pods bypass CNI isolation                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Pause and predict**: Beyond the listed services, what other components on a Linux node (e.g., system services, container runtimes, other applications) could expose network ports and become part of the attack surface, potentially bypassing Kubernetes controls?

---

## Essential Kubernetes Ports

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES REQUIRED PORTS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Control Plane:                                            │
│  ─────────────────────────────────────────────────────────  │
│  6443   - Kubernetes API server (HTTPS)                    │
│  2379   - etcd client (only from API server)               │
│  2380   - etcd peer (only between etcd nodes)              │
│  10250  - Kubelet API (authenticated)                      │
│  10259  - kube-scheduler (HTTPS, localhost)                │
│  10257  - kube-controller-manager (HTTPS, localhost)       │
│                                                             │
│  Worker Nodes:                                             │
│  ─────────────────────────────────────────────────────────  │
│  10250  - Kubelet API (authenticated)                      │
│  30000-32767 - NodePort services (if used)                 │
│                                                             │
│  Should be DISABLED:                                       │
│  ─────────────────────────────────────────────────────────  │
│  10255  - Kubelet read-only port (unauthenticated!)       │
│  8080   - Insecure API server port (deprecated)            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

> **Stop and think**: The kubelet read-only port (10255) exposes pod information without any authentication. An attacker on the network can enumerate every pod, container, and their images just by curling that port. Why would this exist, and why is it a goldmine for reconnaissance?

## Checking Open Ports

```bash
# List all listening ports
ss -tlnp

# List all listening ports with process names
sudo netstat -tlnp

# Check specific Kubernetes ports
ss -tlnp | grep -E '6443|10250|2379'

# Check for insecure ports
ss -tlnp | grep -E '10255|8080'

# Using nmap from external host
nmap -p 6443,10250,10255,2379 <node-ip>
```

---

## Firewall Configuration

### Using iptables

```bash
# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow Kubernetes API (from specific networks)
iptables -A INPUT -p tcp --dport 6443 -s 10.0.0.0/8 -j ACCEPT

# Allow kubelet API (from control plane)
iptables -A INPUT -p tcp --dport 10250 -s 10.0.0.10/32 -j ACCEPT

# Allow NodePort range (if needed)
iptables -A INPUT -p tcp --dport 30000:32767 -j ACCEPT

# Block everything else
iptables -A INPUT -p tcp --dport 6443 -j DROP
iptables -A INPUT -p tcp --dport 10250 -j DROP

# Save rules
iptables-save > /etc/iptables/rules.v4
```

### Using UFW (Ubuntu)

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow Kubernetes API from internal network
sudo ufw allow from 10.0.0.0/8 to any port 6443

# Allow kubelet from control plane
sudo ufw allow from 10.0.0.10 to any port 10250

# Check status
sudo ufw status verbose
```

### Using firewalld (RHEL/CentOS)

```bash
# Allow Kubernetes API
sudo firewall-cmd --permanent --add-port=6443/tcp

# Allow kubelet
sudo firewall-cmd --permanent --add-port=10250/tcp

# Reload
sudo firewall-cmd --reload

# Check open ports
sudo firewall-cmd --list-ports
```

> **Stop and think**: You've configured your firewall rules. How would you *test* these rules to ensure they are actually blocking unwanted traffic and allowing legitimate traffic, especially from a remote machine? What tools would you use?

---

## Disabling Insecure Ports

### Kubelet Read-Only Port

```yaml
# /var/lib/kubelet/config.yaml
readOnlyPort: 0  # Disable read-only port (10255)

# Restart kubelet
sudo systemctl restart kubelet

# Verify
ss -tlnp | grep 10255  # Should return nothing
```

### Check API Server Insecure Port

```bash
# The insecure port (8080) is removed in Kubernetes 1.24+
# For older versions, ensure it's disabled:
# --insecure-port=0 in API server flags

# Verify no insecure port
ss -tlnp | grep 8080
```

---

## Host Network Pods

### The Risk

```yaml
# hostNetwork: true bypasses CNI
apiVersion: v1
kind: Pod
metadata:
  name: host-network-pod
spec:
  hostNetwork: true  # Pod uses node's network namespace!
  containers:
  - name: app
    image: nginx

# This pod can:
# - Bind to any port on the host
# - See all network traffic
# - Access localhost services
# - Bypass NetworkPolicies
```

> **What would happen if**: A pod is deployed with `hostNetwork: true` in a namespace that has a strict default-deny NetworkPolicy. Does the NetworkPolicy apply to this pod? Think about which network namespace the pod is using.

### Restricting hostNetwork

```yaml
# Use Pod Security Admission to block
apiVersion: v1
kind: Namespace
metadata:
  name: secure-ns
  labels:
    pod-security.kubernetes.io/enforce: restricted
    # 'restricted' blocks hostNetwork: true
```

---

## Network Hardening Checklist

```
┌─────────────────────────────────────────────────────────────┐
│              NETWORK SECURITY CHECKLIST                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  □ Disable kubelet read-only port (10255)                  │
│    readOnlyPort: 0 in kubelet config                       │
│                                                             │
│  □ Restrict API server access                              │
│    Firewall rules to limit source IPs                      │
│                                                             │
│  □ Block hostNetwork for regular workloads                 │
│    Use Pod Security Admission                               │
│                                                             │
│  □ Limit NodePort exposure                                 │
│    Use LoadBalancer or Ingress instead                     │
│                                                             │
│  □ etcd accessible only from API server                    │
│    Firewall rules for 2379/2380                            │
│                                                             │
│  □ Use encryption in transit                               │
│    TLS for all components                                  │
│                                                             │
│  □ Regular port scanning                                   │
│    Audit for unexpected open ports                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Sysctl Network Settings

```bash
# /etc/sysctl.d/99-network-security.conf

# Disable ICMP redirects (prevent MITM)
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# Disable source routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# Enable SYN cookies (SYN flood protection)
net.ipv4.tcp_syncookies = 1

# Log martian packets
net.ipv4.conf.all.log_martians = 1

# Ignore broadcast ICMP
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Ignore bogus ICMP errors
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Apply
sudo sysctl -p /etc/sysctl.d/99-network-security.conf
```

> **Pause and predict**: Why are `net.ipv4.conf.all.accept_redirects = 0` and `net.ipv4.conf.all.send_redirects = 0` important for security, particularly in a multi-host Kubernetes environment where network traffic might be routed between nodes? What attack does this prevent?

---

## Real Exam Scenarios

### Scenario 1: Disable Kubelet Read-Only Port

```bash
# Check if port 10255 is open
ss -tlnp | grep 10255

# Edit kubelet config
sudo vi /var/lib/kubelet/config.yaml

# Add or modify:
# readOnlyPort: 0

# Restart kubelet
sudo systemctl restart kubelet

# Verify
ss -tlnp | grep 10255  # Should be empty
```

### Scenario 2: Audit Open Ports

```bash
# List all listening ports
ss -tlnp

# Compare with expected ports
echo "Expected: 22, 6443, 10250, 10256 (kube-proxy)"
echo "Unexpected ports should be investigated"

# Check for insecure ports
ss -tlnp | grep -E ':10255|:8080'
```

### Scenario 3: Configure Firewall

```bash
# Block external access to kubelet
sudo iptables -A INPUT -p tcp --dport 10250 ! -s 10.0.0.0/8 -j DROP

# Allow only control plane to access kubelet
sudo iptables -I INPUT -p tcp --dport 10250 -s 10.0.0.10 -j ACCEPT

# Verify
sudo iptables -L INPUT -n | grep 10250
```

---

> **Pause and predict**: You run `ss -tlnp` on a worker node and see port 10255 listening. You set `readOnlyPort: 0` in kubelet config and restart kubelet. You run `ss -tlnp` again and still see 10255. What could cause it to persist?

## Securing etcd Network Access

```bash
# etcd should only accept connections from API server
# On etcd node:
sudo iptables -A INPUT -p tcp --dport 2379 -s <api-server-ip> -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 2379 -j DROP

# For etcd peer traffic (multi-node etcd)
sudo iptables -A INPUT -p tcp --dport 2380 -s <etcd-node-1-ip> -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 2380 -s <etcd-node-2-ip> -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 2380 -j DROP
```

> **Stop and think**: etcd is often described as the "brain" of Kubernetes. If an attacker gains full access to etcd, what is the worst-case scenario for your cluster? Consider both data confidentiality and cluster integrity.

---

## Did You Know?

- **The kubelet read-only port (10255)** exposes pod information without authentication. It was useful for debugging but is a security risk. Modern Kubernetes uses authenticated metrics endpoints instead.

- **Cloud providers often manage firewall rules** through Security Groups (AWS), Firewall Rules (GCP), or Network Security Groups (Azure). These complement host-level firewalls.

- **NodePort services expose on all nodes**, even if the pod runs on just one. This increases attack surface. Use LoadBalancer or Ingress to limit exposure.

- **CNI plugins handle pod network isolation**, but hostNetwork pods bypass this entirely, operating directly on the host network stack.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Leaving 10255 open | Unauthenticated info leak | Set readOnlyPort: 0 |
| No host firewall | All ports exposed | Configure iptables/ufw |
| Using NodePort publicly | Every node is entry point | Use LoadBalancer/Ingress |
| Allowing hostNetwork | Bypasses network isolation | Block with PSA |
| etcd open to cluster | Data can be stolen | Restrict to API server |

---

## Quiz

1. **A penetration tester on your corporate network runs `curl http://<worker-node-ip>:10255/pods` and gets a full JSON listing of every pod on the node -- including environment variables and image names. Your NetworkPolicies are all in place. How did the tester bypass them, and what two changes stop this?**
   <details>
   <summary>Answer</summary>
   The tester accessed the kubelet's read-only port (10255), which serves pod information without any authentication and operates at the host network level -- completely outside the scope of Kubernetes NetworkPolicies. NetworkPolicies only control pod-to-pod traffic through the CNI, not direct host port access. Two fixes: (1) Set `readOnlyPort: 0` in `/var/lib/kubelet/config.yaml` and restart kubelet to disable the unauthenticated endpoint. (2) Add host-level firewall rules (`iptables -A INPUT -p tcp --dport 10255 -j DROP`) as defense in depth. The authenticated kubelet API on port 10250 provides the same information but requires valid credentials.
   </details>

2. **Your security policy says "no pods may use hostNetwork." You enforce this with Pod Security Admission in `restricted` mode. However, you notice the Calico CNI pods, kube-proxy, and Falco all use `hostNetwork: true` and are in `kube-system`. How do you enforce the policy for application namespaces while allowing system components to function?**
   <details>
   <summary>Answer</summary>
   Pod Security Admission is applied per-namespace via labels, so don't apply the `restricted` profile to `kube-system` (or use `privileged` mode there). Apply `pod-security.kubernetes.io/enforce: restricted` to all workload namespaces (production, staging, etc.) where hostNetwork should be blocked. System namespaces (`kube-system`, `calico-system`, `falco`) legitimately need hostNetwork for CNI, kube-proxy, and security monitoring. This is intentional -- system components require host access to function, while application pods should never need it. Document the exception and audit `kube-system` separately for unauthorized workloads.
   </details>

3. **During a security audit, you run `nmap -p 2379 <control-plane-ip>` from a worker node and discover etcd is accessible. The auditor says this is critical because etcd stores all cluster data including secrets in plain text. What firewall rules do you add, and what happens if you accidentally block the API server's access to etcd?**
   <details>
   <summary>Answer</summary>
   Add iptables rules on the control plane node: `iptables -A INPUT -p tcp --dport 2379 -s <api-server-ip> -j ACCEPT` followed by `iptables -A INPUT -p tcp --dport 2379 -j DROP`. This allows only the API server to connect. For multi-node etcd, also allow peer traffic on 2380 from other etcd nodes. If you accidentally block the API server's access, the entire cluster becomes non-functional: no API calls work, no pod scheduling occurs, and `kubectl` hangs. Recovery requires SSH to the control plane node and removing the misconfigured iptables rule. Always test firewall changes in a maintenance window and have SSH access as a backup path.
   </details>

4. **You discover that a NodePort service on port 31337 is exposed on all 10 worker nodes, even though the backing pod only runs on 2 of them. An attacker is scanning all nodes on the NodePort range. What's the security implication, and what alternatives reduce the attack surface?**
   <details>
   <summary>Answer</summary>
   NodePort services expose on every node's IP in the 30000-32767 range, regardless of where pods actually run. This means all 10 nodes become entry points for the service, multiplying the attack surface by 5x compared to the 2 nodes running the pods. Alternatives: (1) Use a LoadBalancer Service which provides a single entry point with cloud provider firewalling. (2) Use Ingress/Gateway API to route through a controlled ingress point with TLS, rate limiting, and authentication. (3) If NodePort is required, add host-level firewall rules to restrict source IPs on the NodePort range. (4) Use `externalTrafficPolicy: Local` to make the service only respond on nodes where pods actually run, reducing the responding surface to 2 nodes.
   </details>

---

## Hands-On Exercise

**Task**: Audit and secure node network configuration.

```bash
# Step 1: Check all open ports
echo "=== Open Ports ==="
ss -tlnp

# Step 2: Check for insecure ports
echo "=== Insecure Ports Check ==="
ss -tlnp | grep -E ':10255|:8080' && echo "WARNING: Insecure ports open!" || echo "OK: No insecure ports"

# Step 3: Check kubelet read-only port configuration
echo "=== Kubelet Config ==="
grep -i readOnlyPort /var/lib/kubelet/config.yaml 2>/dev/null || echo "Check on actual node"

# Step 4: Check network sysctl settings
echo "=== Network Security Sysctl ==="
sysctl net.ipv4.conf.all.accept_redirects
sysctl net.ipv4.conf.all.send_redirects
sysctl net.ipv4.tcp_syncookies

# Step 5: List current firewall rules (if any)
echo "=== Firewall Rules ==="
sudo iptables -L INPUT -n --line-numbers 2>/dev/null | head -20 || echo "Check iptables on actual node"

# Step 6: Check for pods with hostNetwork
echo "=== Pods with hostNetwork ==="
kubectl get pods -A -o json | jq -r '.items[] | select(.spec.hostNetwork==true) | "\(.metadata.namespace)/\(.metadata.name)"'

# Success criteria:
# - No insecure ports open
# - readOnlyPort: 0 in kubelet config
# - Minimal pods using hostNetwork
```

**Success criteria**: Identify security issues and know how to remediate them.

---

## Summary

**Essential Ports**:
- 6443: API server
- 10250: Kubelet (authenticated)
- 2379/2380: etcd (restricted)

**Disable These**:
- 10255: Kubelet read-only
- 8080: Insecure API port

**Firewall Strategy**:
- Allow only required ports
- Restrict source IPs
- Block hostNetwork for workloads

**Exam Tips**:
- Know how to check open ports
- Disable kubelet read-only port
- Understand hostNetwork risks

---

## Part 3 Complete!

You've finished **System Hardening** (15% of CKS). You now understand:
- AppArmor profiles for containers
- Seccomp system call filtering
- Linux kernel and OS hardening
- Host network security

**Next Part**: [Part 4: Minimize Microservice Vulnerabilities](../part4-microservice-vulnerabilities/module-4.1-security-contexts/) - Security contexts, Pod Security, and secrets management.