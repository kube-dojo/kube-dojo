---
title: "Module 3.3: Linux Kernel and OS Hardening"
slug: k8s/cks/part3-system-hardening/module-3.3-kernel-hardening
sidebar:
  order: 3
lab:
  id: cks-3.3-kernel-hardening
  url: https://killercoda.com/kubedojo/scenario/cks-3.3-kernel-hardening
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - System administration with security focus
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: Basic Linux administration, container runtime knowledge

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Configure** sysctl parameters to harden kernel settings on Kubernetes nodes
2. **Implement** host-level protections including minimal OS images and automatic updates
3. **Audit** node configurations for dangerous kernel parameters and missing hardening
4. **Evaluate** container runtime isolation options to reduce kernel attack surface

---

## Why This Module Matters

Containers share the host kernel. A vulnerability in the kernel can compromise all containers on that host. Hardening the host OS and kernel settings reduces the attack surface that containers can exploit.

CKS tests your understanding of OS-level security measures.

---

## The Shared Kernel Problem

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER KERNEL SHARING                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Container A │  │ Container B │  │ Container C │        │
│  │  (nginx)    │  │  (redis)    │  │ (attacker?) │        │
│  └─────┬───────┘  └─────┬───────┘  └─────┬───────┘        │
│        │                │                │                 │
│        └────────────────┼────────────────┘                 │
│                         │                                  │
│                         ▼                                  │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                    HOST KERNEL                        │ │
│  │                                                       │ │
│  │  All containers use the SAME kernel                  │ │
│  │  Kernel exploit = compromise ALL containers          │ │
│  │  Privilege escalation = host access                  │ │
│  │                                                       │ │
│  └──────────────────────────────────────────────────────┘ │
│                         │                                  │
│                         ▼                                  │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                    HARDWARE                           │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Host OS Hardening Checklist

### 1. Minimize Installed Packages

```bash
# List installed packages
dpkg -l | wc -l  # Debian/Ubuntu
rpm -qa | wc -l  # RHEL/CentOS

# Remove unnecessary packages
sudo apt remove --purge $(dpkg -l | grep -E 'games|office' | awk '{print $2}')

# Kubernetes nodes should have minimal software:
# - Container runtime (containerd, CRI-O)
# - kubelet
# - kube-proxy (if not running as pod)
# - Networking tools
# - Monitoring agents
```

### 2. Disable Unnecessary Services

```bash
# List running services
systemctl list-units --type=service --state=running

# Disable unnecessary services
sudo systemctl disable --now cups      # Printing
sudo systemctl disable --now avahi-daemon  # mDNS
sudo systemctl disable --now bluetooth  # Bluetooth

# Essential services to keep:
# - containerd or docker
# - kubelet
# - SSH (for management)
# - NTP/chrony (time sync)
```

### 3. Keep System Updated

```bash
# Check for security updates (Ubuntu)
sudo apt update
sudo apt list --upgradable | grep -i security

# Apply security updates only
sudo unattended-upgrades

# Check kernel version
uname -r

# Check for known kernel CVEs
# https://www.kernel.org/
```

---

## Kernel Security Parameters

### Essential sysctl Settings

```bash
# View current settings
sysctl -a | grep -E "net.ipv4|kernel" | head -20

# Recommended security settings
# Add to /etc/sysctl.d/99-kubernetes-security.conf

# Disable IP forwarding if not needed (kubelets need it!)
# net.ipv4.ip_forward = 0  # Don't disable on K8s nodes!

# Ignore ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0

# Enable SYN flood protection
net.ipv4.tcp_syncookies = 1

# Log suspicious packets
net.ipv4.conf.all.log_martians = 1

# Ignore broadcast ping
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Disable source routing
net.ipv4.conf.all.accept_source_route = 0

# Enable ASLR
kernel.randomize_va_space = 2

# Restrict dmesg access
kernel.dmesg_restrict = 1

# Restrict kernel pointers
kernel.kptr_restrict = 1

# Apply settings
sudo sysctl -p /etc/sysctl.d/99-kubernetes-security.conf
```

### Kubernetes-Specific Settings

```bash
# /etc/sysctl.d/99-kubernetes.conf

# Required for Kubernetes networking
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1

# For pod networking
net.ipv4.conf.all.forwarding = 1

# Connection tracking for services
net.netfilter.nf_conntrack_max = 131072
```

---

## Protecting /proc and /sys

```bash
# Restrict access to process information
# In /etc/fstab or mount options:
proc    /proc    proc    defaults,hidepid=2    0    0

# hidepid options:
# 0 = default (all users can see all processes)
# 1 = users can see their own processes only
# 2 = users can't see other users' processes

# For containers, Kubernetes manages these mounts
# But host should restrict access
```

---

## User and Permission Hardening

### Disable Root SSH Login

```bash
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no
AllowUsers admin

# Restart SSH
sudo systemctl restart sshd
```

### Remove Unnecessary Users

```bash
# List users that can login
grep -v '/nologin\|/false' /etc/passwd

# Lock unnecessary accounts
sudo usermod -L olduser

# Remove user
sudo userdel -r unnecessaryuser
```

### File Permissions

```bash
# Secure kubelet files
sudo chmod 600 /var/lib/kubelet/config.yaml
sudo chmod 600 /etc/kubernetes/kubelet.conf
sudo chown root:root /var/lib/kubelet/config.yaml

# Secure certificates
sudo chmod 600 /etc/kubernetes/pki/*.key
sudo chmod 644 /etc/kubernetes/pki/*.crt
```

---

## Filesystem Hardening

### Mount Options

```bash
# /etc/fstab entries with security options

# Separate partitions for:
# /var/lib/containerd  - Container data
# /var/log             - Logs
# /tmp                 - Temporary files

# Example secure mount options:
/dev/sda3  /var/lib/containerd  ext4  defaults,nodev,nosuid  0  2
/dev/sda4  /tmp                 ext4  defaults,nodev,nosuid,noexec  0  2
/dev/sda5  /var/log             ext4  defaults,nodev,nosuid,noexec  0  2

# Options:
# nodev   - No device files
# nosuid  - No setuid executables
# noexec  - No execution
```

### Read-Only Root Filesystem

```bash
# For immutable infrastructure:
# Mount root as read-only, use overlay for writes

# This is often handled by the OS distribution
# (CoreOS, Flatcar, Talos, etc.)
```

---

## Container Runtime Hardening

### Containerd Security

```toml
# /etc/containerd/config.toml

[plugins."io.containerd.grpc.v1.cri"]
  # Disable privileged containers (if possible)
  # Note: Some system pods need privileges

  [plugins."io.containerd.grpc.v1.cri".containerd]
    # Use native (not kata) for performance
    default_runtime_name = "runc"

    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
      runtime_type = "io.containerd.runc.v2"

      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
        # Enable seccomp
        SystemdCgroup = true
```

### Docker Security (if used)

```bash
# /etc/docker/daemon.json
{
  "userns-remap": "default",
  "no-new-privileges": true,
  "seccomp-profile": "/etc/docker/seccomp.json",
  "icc": false,
  "live-restore": true
}
```

---

## Audit System Configuration

### Enable auditd

```bash
# Install auditd
sudo apt install auditd

# Configure audit rules for container security
# /etc/audit/rules.d/docker.rules

# Monitor Docker daemon
-w /usr/bin/dockerd -k docker
-w /usr/bin/containerd -k containerd

# Monitor Docker config
-w /etc/docker -k docker-config

# Monitor container directories
-w /var/lib/docker -k docker-storage
-w /var/lib/containerd -k containerd-storage

# Monitor Kubernetes files
-w /etc/kubernetes -k kubernetes
-w /var/lib/kubelet -k kubelet

# Apply rules
sudo augenrules --load
```

---

## Real Exam Scenarios

### Scenario 1: Check Host Security Settings

```bash
# Check sysctl settings
sysctl net.ipv4.ip_forward
sysctl kernel.randomize_va_space

# Check for unnecessary services
systemctl list-units --type=service --state=running | wc -l

# Check SSH configuration
grep -E "PermitRootLogin|PasswordAuthentication" /etc/ssh/sshd_config
```

### Scenario 2: Apply Kernel Hardening

```bash
# Create hardening config
sudo tee /etc/sysctl.d/99-cks-hardening.conf << 'EOF'
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
EOF

# Apply
sudo sysctl -p /etc/sysctl.d/99-cks-hardening.conf

# Verify
sysctl kernel.dmesg_restrict
```

### Scenario 3: Secure Kubelet Files

```bash
# Fix kubelet config permissions
sudo chmod 600 /var/lib/kubelet/config.yaml
sudo chown root:root /var/lib/kubelet/config.yaml

# Verify
ls -la /var/lib/kubelet/config.yaml
```

---

## Hardening Summary Table

| Area | Recommendation | Command/Config |
|------|----------------|----------------|
| Packages | Minimal install | Remove unused packages |
| Services | Disable unused | `systemctl disable <service>` |
| Updates | Regular patching | `apt update && apt upgrade` |
| SSH | No root, key only | `/etc/ssh/sshd_config` |
| sysctl | Restrictive settings | `/etc/sysctl.d/*.conf` |
| Files | Proper permissions | `chmod 600` for sensitive files |
| Audit | Enable auditd | `/etc/audit/rules.d/` |

---

## Did You Know?

- **Container-optimized OSes** like Flatcar, Talos, and Bottlerocket are purpose-built for running containers with minimal attack surface.

- **ASLR (Address Space Layout Randomization)** makes buffer overflow attacks much harder. It's enabled by default on modern Linux.

- **User namespaces** can provide additional isolation by mapping container root to unprivileged host user. Enable with `userns-remap` in Docker.

- **Kernel live patching** (Ubuntu Livepatch, RHEL kpatch) allows applying security patches without rebooting.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Not patching regularly | Known CVEs remain | Automated updates |
| Default SSH config | Root login, passwords | Harden sshd_config |
| Too many services | Increased attack surface | Minimize services |
| Wrong file permissions | Unauthorized access | Audit permissions |
| No audit logging | Can't investigate incidents | Enable auditd |

---

## Quiz

1. **Why is it important that containers share the host kernel?**
   <details>
   <summary>Answer</summary>
   A kernel vulnerability can be exploited by any container to compromise the host and all other containers. The kernel is the shared security boundary.
   </details>

2. **What sysctl parameter enables Address Space Layout Randomization?**
   <details>
   <summary>Answer</summary>
   `kernel.randomize_va_space = 2` - Value 2 enables full randomization for the stack, VDSO, shared memory, and data segments.
   </details>

3. **Why should Kubernetes node hosts have minimal packages installed?**
   <details>
   <summary>Answer</summary>
   Each installed package is potential attack surface. Fewer packages mean fewer vulnerabilities to patch and fewer tools available to attackers who compromise the system.
   </details>

4. **What file contains SSH server security settings?**
   <details>
   <summary>Answer</summary>
   `/etc/ssh/sshd_config` - Configure `PermitRootLogin no` and `PasswordAuthentication no` for better security.
   </details>

---

## Hands-On Exercise

**Task**: Demonstrate kernel hardening concepts using Kubernetes security contexts.

```bash
# Since we can't modify the host kernel from Kubernetes, we'll demonstrate
# how kernel hardening concepts translate to container security.

# Step 1: Create namespace for testing
kubectl create namespace kernel-test

# Step 2: Deploy pod WITHOUT security hardening (insecure baseline)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod
  namespace: kernel-test
spec:
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    # No security context = dangerous!
EOF

# Step 3: Deploy pod WITH security hardening (secure)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
  namespace: kernel-test
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
EOF

# Wait for pods to be ready
kubectl wait --for=condition=Ready pod/insecure-pod -n kernel-test --timeout=60s
kubectl wait --for=condition=Ready pod/secure-pod -n kernel-test --timeout=60s

# Step 4: Compare what each pod can do
echo "=== Insecure Pod: Who am I? ==="
kubectl exec -n kernel-test insecure-pod -- id

echo "=== Secure Pod: Who am I? ==="
kubectl exec -n kernel-test secure-pod -- id

# Step 5: Test filesystem access
echo "=== Insecure Pod: Can write to /tmp? ==="
kubectl exec -n kernel-test insecure-pod -- sh -c "echo 'test' > /tmp/test.txt && echo 'Write succeeded' || echo 'Write failed'"

echo "=== Secure Pod: Can write to /tmp? (should fail - readOnlyRootFilesystem) ==="
kubectl exec -n kernel-test secure-pod -- sh -c "echo 'test' > /tmp/test.txt && echo 'Write succeeded' || echo 'Write blocked!'"

# Step 6: Test process visibility (demonstrates hidepid concept)
echo "=== Insecure Pod: Process list ==="
kubectl exec -n kernel-test insecure-pod -- ps aux | head -5

echo "=== Secure Pod: Process list (limited view) ==="
kubectl exec -n kernel-test secure-pod -- ps aux | head -5

# Step 7: Check proc access
echo "=== Checking /proc access in secure pod ==="
kubectl exec -n kernel-test secure-pod -- cat /proc/1/cmdline 2>&1 | tr '\0' ' ' && echo ""

# Step 8: Check security context applied
echo "=== Security Context Comparison ==="
echo "Insecure pod security context:"
kubectl get pod insecure-pod -n kernel-test -o jsonpath='{.spec.securityContext}' && echo ""
echo "Secure pod security context:"
kubectl get pod secure-pod -n kernel-test -o jsonpath='{.spec.securityContext}' && echo ""

# Step 9: Test privilege escalation (critical kernel hardening)
echo "=== Testing Privilege Escalation Prevention ==="
# Secure pod should block this
kubectl exec -n kernel-test secure-pod -- sh -c "cat /etc/shadow 2>&1" || echo "Access denied (expected)"

# Step 10: Check host sysctl (if running on actual node)
echo ""
echo "=== Host Kernel Checks (run on actual node) ==="
echo "To check on your actual cluster nodes:"
echo "  sysctl kernel.randomize_va_space    # Should be 2"
echo "  sysctl kernel.dmesg_restrict        # Should be 1"
echo "  sysctl kernel.kptr_restrict         # Should be 1 or 2"
echo "  sysctl net.ipv4.conf.all.accept_redirects  # Should be 0"

# Cleanup
echo ""
echo "=== Cleanup ==="
kubectl delete namespace kernel-test

echo ""
echo "=== Exercise Complete ==="
echo "Key learnings demonstrated:"
echo "1. ✓ runAsNonRoot prevents root execution"
echo "2. ✓ readOnlyRootFilesystem blocks writes"
echo "3. ✓ Dropping capabilities limits syscalls"
echo "4. ✓ allowPrivilegeEscalation=false prevents escalation"
echo "5. ✓ seccompProfile applies syscall filtering"
```

**Success criteria**: Deploy insecure and secure pods, observe the security differences, understand how pod security contexts implement kernel hardening concepts.

---

## Summary

**OS Hardening Principles**:
- Minimize packages and services
- Keep system updated
- Restrict SSH access
- Proper file permissions

**Kernel Hardening**:
- Enable ASLR (`kernel.randomize_va_space = 2`)
- Restrict dmesg (`kernel.dmesg_restrict = 1`)
- Disable dangerous network features

**Container Runtime**:
- Enable security features
- Use seccomp profiles
- Consider user namespaces

**Exam Tips**:
- Know key sysctl parameters
- Understand file permission requirements
- Be able to check current configuration

---

## Next Module

[Module 3.4: Network Security](../module-3.4-network-security/) - Host-level network hardening.
