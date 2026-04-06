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

Imagine a nightclub with a strict, unbribable bouncer at the door to the VIP lounge (the Linux kernel). Instead of checking IDs, this bouncer checks every single request a guest (container process) makes. Want to read a file? "Allowed." Want to change the system clock or trace another process? "Absolutely not." That bouncer is Seccomp (Secure Computing Mode). 

Containers share the host kernel. Because of this, a compromised container can weaponize obscure or dangerous system calls to attack the host or escape its isolation. By strictly limiting which syscalls a process can execute, Seccomp dramatically shrinks the attack surface. CKS tests your ability to configure this bouncer by applying default policies and writing custom rules.

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

> **Stop and think**: A container application only needs about 40-50 system calls out of 300+ available in the Linux kernel. The rest are potential attack surface. If you set `defaultAction: SCMP_ACT_ERRNO` (deny all by default) and only allow the 50 syscalls your app needs, what percentage of the kernel's syscall attack surface have you eliminated?

## Default Seccomp Profile

> **War Story: Stopping Dirty COW and Container Escapes**
> In 2016, the "Dirty COW" vulnerability (CVE-2016-5195) allowed privilege escalation via the `ptrace` system call. Attackers who compromised a container could use `ptrace` to manipulate host processes and break out. Simply having a Seccomp profile that blocked `ptrace` stopped this container escape dead in its tracks, long before patches were applied.

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

### Operational Overhead: Custom vs. RuntimeDefault

Writing custom Seccomp profiles for every application offers the absolute lowest attack surface, but it comes with immense operational overhead. Every time an application updates a library or changes its behavior, it might need a new syscall (like `epoll_wait` instead of `select`), instantly crashing the app in production. 

For 95% of workloads, the `RuntimeDefault` profile strikes the perfect balance. It automatically blocks the ~40 most dangerous system calls (like `ptrace`, `mount`, and `kexec_load` used for container escapes) while allowing the standard ~260 syscalls that normal applications need. You should only maintain custom profiles for highly sensitive, static workloads where the exact system call footprint is known and heavily tested.

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

> **What would happen if**: You create a custom seccomp profile and place it in `/etc/seccomp/profiles/custom.json` on the node. Your pod spec references `localhostProfile: profiles/custom.json`. The pod fails to start. The profile JSON is valid. What path mistake did you make?

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

> **Pause and predict**: You apply a seccomp profile with `defaultAction: SCMP_ACT_KILL` instead of `SCMP_ACT_ERRNO`. Your application makes an unlisted syscall. What happens to the container process compared to using `SCMP_ACT_ERRNO`?

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

1. **An application container keeps crashing with "operation not permitted" errors. The pod has a custom seccomp profile applied. The same container runs fine without the profile. How do you identify which syscalls the profile is blocking, and what's the safest debugging approach?**
   <details>
   <summary>Answer</summary>
   Use `SCMP_ACT_LOG` as the default action temporarily -- this allows all syscalls but logs the ones that would have been blocked. Check kernel logs with `dmesg | grep seccomp` or `journalctl | grep seccomp` to see which syscalls are being denied. Alternatively, use `strace -c -f <command>` on a test system to enumerate all syscalls the application uses. Once you know the needed syscalls, add them to the allow list. Never debug in production by switching to `Unconfined` -- use `SCMP_ACT_LOG` to maintain visibility while temporarily allowing traffic. The safest approach is to run `strace` in a staging environment and build the profile from that data.
   </details>

2. **During a CKS exam, you create a seccomp profile at `/var/lib/kubelet/seccomp/profiles/block-mount.json` and reference it as `localhostProfile: block-mount.json` in the pod spec. The pod enters `CreateContainerError`. What's wrong with the path?**
   <details>
   <summary>Answer</summary>
   The `localhostProfile` path is relative to `/var/lib/kubelet/seccomp/`, so the full path Kubernetes looks for is `/var/lib/kubelet/seccomp/block-mount.json` -- but your file is at `/var/lib/kubelet/seccomp/profiles/block-mount.json`. The correct reference is `localhostProfile: profiles/block-mount.json` (include the `profiles/` subdirectory). This is a common exam gotcha because the path is relative, not absolute. Always verify the file exists at the expected full path: `ls /var/lib/kubelet/seccomp/<localhostProfile-value>`.
   </details>

3. **Your security team wants to block the `ptrace` syscall cluster-wide because it enables container escape techniques. You have 50 namespaces with different workloads. What's the most efficient way to enforce this without creating 50 individual seccomp profiles?**
   <details>
   <summary>Answer</summary>
   Use the `RuntimeDefault` seccomp profile which already blocks `ptrace` (along with ~44 other dangerous syscalls). Apply it cluster-wide by configuring Pod Security Admission with the `restricted` profile in `enforce` mode on all workload namespaces -- this requires `RuntimeDefault` or `Localhost` seccomp. Alternatively, create a single custom profile that uses `defaultAction: SCMP_ACT_ALLOW` with only `ptrace` blocked, and deploy it to all nodes via a DaemonSet. Then reference it at the pod level. The `RuntimeDefault` approach is simpler and blocks more than just ptrace, providing broader security.
   </details>

4. **You have a multi-container pod with an nginx reverse proxy and a Python application. The nginx container needs `accept`, `bind`, and `listen` syscalls for networking. The Python container needs `fork` and `execve` for subprocesses. Can you apply different seccomp profiles to each container, and how?**
   <details>
   <summary>Answer</summary>
   Yes, seccomp profiles can be set at the container level, not just the pod level. Set `securityContext.seccompProfile` on each container individually: nginx gets a profile allowing network-related syscalls, Python gets a profile allowing process-related syscalls. Place each profile in `/var/lib/kubelet/seccomp/profiles/` and reference them separately. If set at both pod and container level, the container-level setting takes precedence. This follows least privilege -- each container only gets the syscalls it needs, reducing attack surface. A compromised nginx container can't fork subprocesses, and a compromised Python container can't bind to ports.
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