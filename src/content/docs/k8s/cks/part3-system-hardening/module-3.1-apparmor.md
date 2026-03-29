---
title: "Module 3.1: AppArmor for Containers"
slug: k8s/cks/part3-system-hardening/module-3.1-apparmor
sidebar:
  order: 1
---
> **Complexity**: `[MEDIUM]` - Linux security essential
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: Linux basics, container runtime knowledge

---

## Why This Module Matters

AppArmor is a Linux security module that restricts what applications can do—which files they can access, which network operations they can perform, which capabilities they can use. When applied to containers, AppArmor adds a security layer beyond the container runtime.

CKS tests your ability to create AppArmor profiles and apply them to pods.

---

## What is AppArmor?

```
┌─────────────────────────────────────────────────────────────┐
│              APPARMOR OVERVIEW                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AppArmor = Application Armor                              │
│  ─────────────────────────────────────────────────────────  │
│  • Mandatory Access Control (MAC) system                   │
│  • Restricts per-program capabilities                      │
│  • Default on Ubuntu, Debian                               │
│  • Alternative to SELinux (RHEL/CentOS)                   │
│                                                             │
│  How it works:                                             │
│                                                             │
│  ┌─────────────────┐     ┌─────────────────┐              │
│  │  Application    │────►│  System Call    │              │
│  │  (Container)    │     │                 │              │
│  └─────────────────┘     └────────┬────────┘              │
│                                   │                        │
│                                   ▼                        │
│                          ┌─────────────────┐              │
│                          │  AppArmor       │              │
│                          │  Profile Check  │              │
│                          └────────┬────────┘              │
│                                   │                        │
│                      ┌────────────┴────────────┐          │
│                      ▼                         ▼          │
│                 ┌─────────┐              ┌─────────┐      │
│                 │ ALLOWED │              │ DENIED  │      │
│                 └─────────┘              └─────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## AppArmor Modes

```
┌─────────────────────────────────────────────────────────────┐
│              APPARMOR PROFILE MODES                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Enforce Mode                                              │
│  └── Policy is enforced, violations are blocked AND logged │
│      aa-enforce /path/to/profile                           │
│                                                             │
│  Complain Mode                                             │
│  └── Policy violations are logged but NOT blocked          │
│      aa-complain /path/to/profile                          │
│      (Useful for testing new profiles)                     │
│                                                             │
│  Disabled/Unconfined                                       │
│  └── No restrictions applied                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Checking AppArmor Status

```bash
# Check if AppArmor is enabled
cat /sys/module/apparmor/parameters/enabled
# Output: Y (enabled) or N (disabled)

# Check AppArmor status
sudo aa-status

# Output example:
# apparmor module is loaded.
# 47 profiles are loaded.
# 47 profiles are in enforce mode.
#    /usr/bin/evince
#    /usr/sbin/cupsd
#    docker-default
# 0 profiles are in complain mode.
# 10 processes have profiles defined.

# List loaded profiles
sudo aa-status --profiles

# Check if container runtime supports AppArmor
docker info | grep -i apparmor
# Output: Security Options: apparmor
```

---

## Default Container Profile

```bash
# Docker/containerd use 'docker-default' profile
# This profile:
# - Denies mounting filesystems
# - Denies access to /proc/sys
# - Denies raw network access
# - Allows normal container operations

# Check default profile
cat /etc/apparmor.d/containers/docker-default 2>/dev/null || \
  cat /etc/apparmor.d/docker 2>/dev/null
```

---

## Creating Custom AppArmor Profiles

### Profile Location

```bash
# AppArmor profiles are stored in:
/etc/apparmor.d/

# For Kubernetes, create in:
/etc/apparmor.d/
# Profile must be loaded on each node where pod might run
```

### Profile Structure

```
#include <tunables/global>

profile my-container-profile flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # File access rules
  /etc/passwd r,                    # Read /etc/passwd
  /var/log/myapp/** rw,            # Read/write to log directory
  /tmp/** rw,                       # Read/write to tmp

  # Network rules
  network inet tcp,                 # Allow TCP
  network inet udp,                 # Allow UDP

  # Capability rules
  capability net_bind_service,      # Allow binding to ports < 1024

  # Deny rules
  deny /etc/shadow r,               # Deny reading shadow
  deny /proc/sys/** w,              # Deny writing to /proc/sys
}
```

### Rule Syntax

```
┌─────────────────────────────────────────────────────────────┐
│              APPARMOR RULE SYNTAX                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  File Access:                                              │
│  ─────────────────────────────────────────────────────────  │
│  /path/to/file r,        # Read                            │
│  /path/to/file w,        # Write                           │
│  /path/to/file rw,       # Read and Write                  │
│  /path/to/file a,        # Append                          │
│  /path/to/file ix,       # Execute, inherit profile        │
│  /path/to/dir/ r,        # Read directory                  │
│  /path/to/dir/** rw,     # Recursive read/write            │
│                                                             │
│  Network:                                                  │
│  ─────────────────────────────────────────────────────────  │
│  network,                # Allow all networking            │
│  network inet,           # IPv4                            │
│  network inet6,          # IPv6                            │
│  network inet tcp,       # IPv4 TCP only                   │
│  network inet udp,       # IPv4 UDP only                   │
│                                                             │
│  Capabilities:                                             │
│  ─────────────────────────────────────────────────────────  │
│  capability dac_override,    # Bypass file permissions     │
│  capability net_admin,       # Network admin               │
│  capability sys_ptrace,      # Trace processes             │
│                                                             │
│  Deny:                                                     │
│  ─────────────────────────────────────────────────────────  │
│  deny /path/file w,      # Explicitly deny (logs)          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Creating a Profile for Kubernetes

### Step 1: Write the Profile

```bash
# Create profile on each node
sudo tee /etc/apparmor.d/k8s-deny-write << 'EOF'
#include <tunables/global>

profile k8s-deny-write flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Allow most read operations
  file,

  # Deny all write operations except /tmp
  deny /** w,
  /tmp/** rw,

  # Allow network
  network,
}
EOF
```

### Step 2: Load the Profile

```bash
# Parse and load the profile
sudo apparmor_parser -r /etc/apparmor.d/k8s-deny-write

# Verify it's loaded
sudo aa-status | grep k8s-deny-write

# To remove a profile
sudo apparmor_parser -R /etc/apparmor.d/k8s-deny-write
```

### Step 3: Apply to Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secured-pod
  annotations:
    # Format: container.apparmor.security.beta.kubernetes.io/<container-name>: <profile>
    container.apparmor.security.beta.kubernetes.io/app: localhost/k8s-deny-write
spec:
  containers:
  - name: app
    image: nginx
```

---

## AppArmor Profile Reference Values

```yaml
# Annotation format:
container.apparmor.security.beta.kubernetes.io/<container-name>: <profile-ref>

# Profile reference options:
# runtime/default    - Use container runtime's default profile
# localhost/<name>   - Use profile loaded on node with <name>
# unconfined        - No AppArmor restrictions (dangerous!)
```

---

## Common Profiles for Containers

### Deny Write to Root Filesystem

```
#include <tunables/global>

profile k8s-readonly flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Read everything
  /** r,

  # Write only to specific paths
  /tmp/** rw,
  /var/tmp/** rw,
  /run/** rw,

  # Deny write elsewhere
  deny /** w,

  network,
}
```

### Deny Network Access

```
#include <tunables/global>

profile k8s-deny-network flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  file,

  # Deny all network access
  deny network,
}
```

### Deny Sensitive File Access

```
#include <tunables/global>

profile k8s-deny-sensitive flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  file,
  network,

  # Deny access to sensitive files
  deny /etc/shadow r,
  deny /etc/gshadow r,
  deny /etc/sudoers r,
  deny /etc/sudoers.d/** r,
  deny /root/** rwx,
}
```

---

## Real Exam Scenarios

### Scenario 1: Apply Existing Profile

```bash
# Check if profile is loaded
sudo aa-status | grep my-profile

# Apply to pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  annotations:
    container.apparmor.security.beta.kubernetes.io/nginx: localhost/my-profile
spec:
  containers:
  - name: nginx
    image: nginx
EOF
```

### Scenario 2: Create and Apply Profile

```bash
# Create profile that denies write to /etc
sudo tee /etc/apparmor.d/k8s-deny-etc-write << 'EOF'
#include <tunables/global>

profile k8s-deny-etc-write flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  file,
  network,
  deny /etc/** w,
}
EOF

# Load profile
sudo apparmor_parser -r /etc/apparmor.d/k8s-deny-etc-write

# Apply to pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secured-nginx
  annotations:
    container.apparmor.security.beta.kubernetes.io/nginx: localhost/k8s-deny-etc-write
spec:
  containers:
  - name: nginx
    image: nginx
EOF

# Verify
kubectl exec secured-nginx -- touch /etc/test
# Should fail due to AppArmor
```

### Scenario 3: Debug AppArmor Issues

```bash
# Check pod events
kubectl describe pod secured-pod | grep -i apparmor

# Check if profile is loaded on node
ssh node1 'sudo aa-status | grep k8s'

# Check audit logs for denials
sudo dmesg | grep -i apparmor | tail -10

# Or check audit log
sudo journalctl -k | grep -i apparmor
```

---

## Did You Know?

- **AppArmor profiles must be loaded on every node** where a pod might run. DaemonSets can help distribute profiles.

- **The 'flags=(attach_disconnected,mediate_deleted)' part** is essential for container profiles because containers may have disconnected paths and deleted files.

- **AppArmor is Ubuntu/Debian default**, while SELinux is RHEL/CentOS default. The CKS exam uses Ubuntu, so AppArmor is the focus.

- **You can generate profiles** using `aa-genprof` or `aa-logprof` which monitor application behavior and create profiles based on observed actions.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Profile not loaded on node | Pod fails to schedule | Load on all nodes |
| Wrong annotation format | Profile not applied | Check exact annotation key |
| Missing abstractions | Profile too restrictive | Include base abstractions |
| Using 'unconfined' | No security | Use runtime/default minimum |
| Not testing in complain mode | Breaks application | Test with aa-complain first |

---

## Quiz

1. **What annotation applies an AppArmor profile to a container?**
   <details>
   <summary>Answer</summary>
   `container.apparmor.security.beta.kubernetes.io/<container-name>: localhost/<profile-name>` - The container name must match the container in the pod spec.
   </details>

2. **How do you load an AppArmor profile on a node?**
   <details>
   <summary>Answer</summary>
   `sudo apparmor_parser -r /etc/apparmor.d/<profile-file>` - The -r flag reloads if already loaded.
   </details>

3. **What is complain mode used for?**
   <details>
   <summary>Answer</summary>
   Testing profiles without blocking. In complain mode, AppArmor logs violations but allows them, letting you refine the profile before enforcing.
   </details>

4. **What happens if the specified AppArmor profile doesn't exist on the node?**
   <details>
   <summary>Answer</summary>
   The pod fails to start with an error indicating the profile cannot be found. The kubelet validates profile existence before running the container.
   </details>

---

## Hands-On Exercise

**Task**: Create and apply an AppArmor profile that denies network access.

```bash
# Step 1: Check AppArmor is enabled (run on node)
cat /sys/module/apparmor/parameters/enabled
# Should output: Y

# Step 2: Create the profile
sudo tee /etc/apparmor.d/k8s-deny-network << 'EOF'
#include <tunables/global>

profile k8s-deny-network flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Allow file operations
  file,

  # Deny network access
  deny network,
}
EOF

# Step 3: Load the profile
sudo apparmor_parser -r /etc/apparmor.d/k8s-deny-network

# Step 4: Verify it's loaded
sudo aa-status | grep k8s-deny-network

# Step 5: Create pod with the profile
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: no-network-pod
  annotations:
    container.apparmor.security.beta.kubernetes.io/app: localhost/k8s-deny-network
spec:
  containers:
  - name: app
    image: curlimages/curl
    command: ["sleep", "3600"]
EOF

# Step 6: Wait for pod
kubectl wait --for=condition=Ready pod/no-network-pod --timeout=60s

# Step 7: Test network is blocked
kubectl exec no-network-pod -- curl -s https://kubernetes.io --connect-timeout 5
# Should fail due to AppArmor denying network

# Step 8: Create pod without restriction for comparison
kubectl run network-allowed --image=curlimages/curl --rm -it --restart=Never -- \
  curl -s https://kubernetes.io -o /dev/null -w "%{http_code}"
# Should succeed (200)

# Cleanup
kubectl delete pod no-network-pod
```

**Success criteria**: Pod with AppArmor profile cannot make network connections.

---

## Summary

**AppArmor Basics**:
- Linux Mandatory Access Control
- Per-program restrictions
- Profiles loaded on nodes

**Profile Application**:
```yaml
annotations:
  container.apparmor.security.beta.kubernetes.io/<container>: localhost/<profile>
```

**Common Profile Rules**:
- `deny /path w,` - Deny write
- `deny network,` - Deny networking
- `capability X,` - Allow capability

**Exam Tips**:
- Know annotation format
- Practice loading profiles
- Understand profile locations

---

## Next Module

[Module 3.2: Seccomp Profiles](../module-3.2-seccomp/) - System call filtering for containers.
