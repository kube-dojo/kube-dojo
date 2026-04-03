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

1. **What is the kubelet read-only port and why should it be disabled?**
   <details>
   <summary>Answer</summary>
   Port 10255 serves pod information without authentication. Attackers can enumerate pods, containers, and their configurations. Disable with `readOnlyPort: 0` in kubelet config.
   </details>

2. **Which pods bypass Kubernetes NetworkPolicies?**
   <details>
   <summary>Answer</summary>
   Pods with `hostNetwork: true` bypass NetworkPolicies because they use the host's network namespace directly instead of the pod network managed by the CNI.
   </details>

3. **What ports does etcd use and who should access them?**
   <details>
   <summary>Answer</summary>
   Port 2379 for client connections (only API server should access) and 2380 for peer connections (only other etcd nodes). Both should be firewalled.
   </details>

4. **How can you verify that insecure ports are disabled?**
   <details>
   <summary>Answer</summary>
   Use `ss -tlnp | grep -E '10255|8080'` to check if these ports are listening. Empty output means they're disabled.
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
