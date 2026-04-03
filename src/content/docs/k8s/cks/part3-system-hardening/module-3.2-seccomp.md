---
title: "Module 3.2: Seccomp Profiles"
slug: k8s/cks/part3-system-hardening/module-3.2-seccomp
sidebar:
  order: 2
lab:
  id: cks-3.2-seccomp
  url: https://killercoda.com/kubedojo/scenario/cks-3.2-seccomp
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - System-level security
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: Module 3.1 (AppArmor), Linux system calls knowledge

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Create** custom seccomp profiles that allow only required system calls for a workload
2. **Configure** pods to use seccomp profiles via the securityContext field
3. **Trace** blocked syscalls to diagnose application failures under seccomp enforcement
4. **Audit** running containers for missing or overly permissive seccomp profiles

---

## Why This Module Matters

Seccomp (Secure Computing Mode) restricts which system calls a process can make. Containers use syscalls to interact with the kernel—file operations, network connections, process management. Limiting syscalls reduces the attack surface dramatically.

CKS tests your ability to apply and create seccomp profiles.

---

## What is Seccomp?

```
┌─────────────────────────────────────────────────────────────┐
│              SECCOMP OVERVIEW                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Seccomp = Secure Computing Mode                           │
│  ─────────────────────────────────────────────────────────  │
│  • Linux kernel feature (since 2.6.12)                     │
│  • Filters system calls at kernel level                    │
│  • Very low overhead                                       │
│  • Works with Docker, containerd, CRI-O                    │
│                                                             │
│  Application ──► syscall ──► Seccomp Filter ──► Kernel    │
│                                    │                        │
│                           ┌────────┴────────┐              │
│                           ▼                 ▼              │
│                     ┌─────────┐       ┌─────────┐          │
│                     │ ALLOW   │       │ BLOCK   │          │
│                     │ execute │       │ or KILL │          │
│                     └─────────┘       └─────────┘          │
│                                                             │
│  Actions when syscall matches:                             │
│  • SCMP_ACT_ALLOW  - Allow syscall                        │
│  • SCMP_ACT_ERRNO  - Block, return error                   │
│  • SCMP_ACT_KILL   - Kill the process                      │
│  • SCMP_ACT_TRAP   - Send SIGSYS signal                    │
│  • SCMP_ACT_LOG    - Log and allow                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Seccomp vs AppArmor

```
┌─────────────────────────────────────────────────────────────┐
│              SECCOMP vs APPARMOR                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Seccomp                    │ AppArmor                     │
│  ──────────────────────────────────────────────────────────│
│  Filters syscalls           │ Filters file/network access │
│  Very low level             │ Higher level abstraction    │
│  JSON profiles              │ Text-based profiles         │
│  No file path awareness     │ File path based rules       │
│  Lightweight                │ More complex rules          │
│  Defense in depth           │ Defense in depth            │
│                                                             │
│  Best practice: Use BOTH together                          │
│  Seccomp: Block dangerous syscalls                         │
│  AppArmor: Control resource access                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Default Seccomp Profile

Kubernetes 1.22+ applies the `RuntimeDefault` profile by default when Pod Security Admission is configured.

```bash
# Check if default seccomp is applied
kubectl get pod mypod -o jsonpath='{.spec.securityContext.seccompProfile}'

# The RuntimeDefault profile typically blocks:
# - keyctl (kernel keyring)
# - ptrace (process tracing)
# - personality (change execution domain)
# - unshare (namespace manipulation)
# - mount/umount (filesystem mounting)
# - clock_settime (change system time)
# And about 40+ other dangerous syscalls
```

---

## Seccomp Profile Location

```bash
# Kubernetes looks for profiles in:
/var/lib/kubelet/seccomp/

# Profile path in pod spec is relative to this directory
# Example: profiles/my-profile.json
# Full path: /var/lib/kubelet/seccomp/profiles/my-profile.json

# Create directory if it doesn't exist
sudo mkdir -p /var/lib/kubelet/seccomp/profiles
```

---

## Profile Structure

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": [
    "SCMP_ARCH_X86_64",
    "SCMP_ARCH_X86",
    "SCMP_ARCH_AARCH64"
  ],
  "syscalls": [
    {
      "names": [
        "accept",
        "access",
        "arch_prctl",
        "bind",
        "brk"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": [
        "ptrace"
      ],
      "action": "SCMP_ACT_ERRNO",
      "errnoRet": 1
    }
  ]
}
```

### Profile Fields Explained

```
┌─────────────────────────────────────────────────────────────┐
│              SECCOMP PROFILE FIELDS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  defaultAction                                             │
│  └── What to do for syscalls not explicitly listed         │
│      SCMP_ACT_ALLOW = allow by default (whitelist others)  │
│      SCMP_ACT_ERRNO = deny by default (blacklist others)   │
│                                                             │
│  architectures                                             │
│  └── CPU architectures to apply (x86_64, arm64, etc.)     │
│                                                             │
│  syscalls                                                  │
│  └── Array of syscall rules:                              │
│      names: ["syscall1", "syscall2"]                      │
│      action: SCMP_ACT_ALLOW | SCMP_ACT_ERRNO | etc.       │
│      errnoRet: error number to return (optional)          │
│      args: filter on syscall arguments (optional)          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Applying Seccomp in Kubernetes

### Method 1: Pod Security Context (Recommended)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: seccomp-pod
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault  # Use runtime's default profile
  containers:
  - name: app
    image: nginx
```

### Method 2: Localhost Profile

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-seccomp-pod
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/custom.json  # Relative to /var/lib/kubelet/seccomp/
  containers:
  - name: app
    image: nginx
```

### Method 3: Container-Level Profile

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-pod
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      seccompProfile:
        type: RuntimeDefault
  - name: sidecar
    image: busybox
    securityContext:
      seccompProfile:
        type: Localhost
        localhostProfile: profiles/sidecar.json
```

---

## Seccomp Profile Types

```yaml
# RuntimeDefault - Container runtime's default profile
seccompProfile:
  type: RuntimeDefault

# Localhost - Custom profile from node filesystem
seccompProfile:
  type: Localhost
  localhostProfile: profiles/my-profile.json

# Unconfined - No seccomp filtering (dangerous!)
seccompProfile:
  type: Unconfined
```

---

## Creating Custom Profiles

### Profile That Blocks ptrace

```json
// /var/lib/kubelet/seccomp/profiles/deny-ptrace.json
{
  "defaultAction": "SCMP_ACT_ALLOW",
  "syscalls": [
    {
      "names": ["ptrace"],
      "action": "SCMP_ACT_ERRNO",
      "errnoRet": 1
    }
  ]
}
```

### Profile That Only Allows Specific Syscalls

```json
// /var/lib/kubelet/seccomp/profiles/minimal.json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "read", "write", "open", "close",
        "fstat", "lseek", "mmap", "mprotect",
        "munmap", "brk", "exit_group"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

### Profile That Logs Suspicious Calls

```json
// /var/lib/kubelet/seccomp/profiles/audit.json
{
  "defaultAction": "SCMP_ACT_ALLOW",
  "syscalls": [
    {
      "names": ["ptrace", "process_vm_readv", "process_vm_writev"],
      "action": "SCMP_ACT_LOG"
    },
    {
      "names": ["mount", "umount2", "pivot_root"],
      "action": "SCMP_ACT_ERRNO"
    }
  ]
}
```

---

## Real Exam Scenarios

### Scenario 1: Apply RuntimeDefault

```yaml
# Create pod with RuntimeDefault seccomp
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: nginx
EOF

# Verify
kubectl get pod secure-pod -o jsonpath='{.spec.securityContext.seccompProfile}' | jq .
```

### Scenario 2: Apply Custom Profile

```bash
# Create profile on node
sudo mkdir -p /var/lib/kubelet/seccomp/profiles
sudo tee /var/lib/kubelet/seccomp/profiles/block-chmod.json << 'EOF'
{
  "defaultAction": "SCMP_ACT_ALLOW",
  "syscalls": [
    {
      "names": ["chmod", "fchmod", "fchmodat"],
      "action": "SCMP_ACT_ERRNO",
      "errnoRet": 1
    }
  ]
}
EOF

# Apply to pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: no-chmod-pod
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/block-chmod.json
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
EOF

# Test chmod is blocked
kubectl exec no-chmod-pod -- chmod 777 /tmp
# Should fail with "Operation not permitted"
```

### Scenario 3: Debug Seccomp Issues

```bash
# Check if seccomp is applied
kubectl get pod mypod -o yaml | grep -A5 seccompProfile

# Check node audit logs for seccomp denials
sudo dmesg | grep -i seccomp
sudo journalctl | grep -i seccomp

# Common error messages
# "seccomp: syscall X denied"
# "operation not permitted"
```

---

## Finding Syscalls Used by Application

```bash
# Use strace to find syscalls (on a test system, not production)
strace -c -f <command>

# Example output:
# % time     seconds  usecs/call     calls    errors syscall
# ------ ----------- ----------- --------- --------- ----------------
#  25.00    0.000010           0        50           read
#  25.00    0.000010           0        30           write
#  12.50    0.000005           0        20           open
# ...

# Or use sysdig
sysdig -p "%proc.name %syscall.type" container.name=mycontainer
```

---

## Did You Know?

- **Docker's default seccomp profile** blocks about 44 syscalls out of 300+. It's a good baseline but may need customization.

- **Seccomp-bpf (Berkeley Packet Filter)** is the modern implementation. It allows complex filtering logic beyond simple allow/deny.

- **Breaking a seccomp profile** is extremely difficult. Unlike AppArmor which can be tricked with symlinks sometimes, seccomp operates at syscall level.

- **The `RuntimeDefault` profile became default** in Kubernetes 1.22 with Pod Security Admission. Before that, containers ran unconfined.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Profile path wrong | Pod fails to start | Check /var/lib/kubelet/seccomp/ |
| Missing syscall | App crashes | Audit with strace first |
| Using Unconfined | No protection | Use RuntimeDefault minimum |
| Profile not on all nodes | Pod scheduling fails | Use DaemonSet to deploy |
| JSON syntax error | Profile fails to load | Validate JSON |

---

## Quiz

1. **What is the default seccomp profile in Kubernetes 1.22+?**
   <details>
   <summary>Answer</summary>
   `RuntimeDefault` - The container runtime's default profile. This is applied when Pod Security Admission is configured appropriately.
   </details>

2. **Where should custom seccomp profiles be placed?**
   <details>
   <summary>Answer</summary>
   `/var/lib/kubelet/seccomp/` - Profiles are specified relative to this directory in pod specs.
   </details>

3. **What does `SCMP_ACT_ERRNO` do?**
   <details>
   <summary>Answer</summary>
   It blocks the syscall and returns an error to the calling process. The process doesn't crash but the operation fails.
   </details>

4. **How do you apply a seccomp profile to a specific container in a multi-container pod?**
   <details>
   <summary>Answer</summary>
   Set `securityContext.seccompProfile` at the container level instead of pod level. Each container can have its own profile.
   </details>

---

## Hands-On Exercise

**Task**: Create and apply a seccomp profile that blocks ptrace syscall.

```bash
# Step 1: Create profile directory on node
sudo mkdir -p /var/lib/kubelet/seccomp/profiles

# Step 2: Create the profile
sudo tee /var/lib/kubelet/seccomp/profiles/no-ptrace.json << 'EOF'
{
  "defaultAction": "SCMP_ACT_ALLOW",
  "syscalls": [
    {
      "names": ["ptrace"],
      "action": "SCMP_ACT_ERRNO",
      "errnoRet": 1
    }
  ]
}
EOF

# Step 3: Verify file exists
cat /var/lib/kubelet/seccomp/profiles/no-ptrace.json

# Step 4: Create pod with the profile
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: no-ptrace-pod
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/no-ptrace.json
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
EOF

# Step 5: Wait for pod
kubectl wait --for=condition=Ready pod/no-ptrace-pod --timeout=60s

# Step 6: Verify seccomp is applied
kubectl get pod no-ptrace-pod -o jsonpath='{.spec.securityContext.seccompProfile}' | jq .

# Step 7: Test that ptrace would be blocked
# (strace uses ptrace internally)
kubectl exec no-ptrace-pod -- strace -f echo test 2>&1 || echo "strace blocked (expected)"

# Step 8: Create comparison pod without seccomp restriction
kubectl run allowed-pod --image=busybox --rm -it --restart=Never -- \
  sh -c "ls /proc/self/status && echo 'No seccomp issues'"

# Cleanup
kubectl delete pod no-ptrace-pod
```

**Success criteria**: Pod runs but ptrace operations are blocked.

---

## Summary

**Seccomp Basics**:
- Linux kernel syscall filter
- JSON-based profiles
- Low overhead, high security

**Profile Types**:
- `RuntimeDefault` - Use runtime's default
- `Localhost` - Custom profile
- `Unconfined` - No filtering (avoid!)

**Profile Location**:
- `/var/lib/kubelet/seccomp/`
- Path in pod spec is relative

**Actions**:
- `SCMP_ACT_ALLOW` - Allow syscall
- `SCMP_ACT_ERRNO` - Block with error
- `SCMP_ACT_KILL` - Kill process

**Exam Tips**:
- Know profile syntax
- Practice creating profiles
- Understand RuntimeDefault

---

## Next Module

[Module 3.3: Linux Kernel Hardening](../module-3.3-kernel-hardening/) - Reducing OS attack surface.
