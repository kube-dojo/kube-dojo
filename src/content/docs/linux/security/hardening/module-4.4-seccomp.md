---
title: "Module 4.4: seccomp Profiles"
slug: linux/security/hardening/module-4.4-seccomp
sidebar:
  order: 5
lab:
  id: "linux-4.4-seccomp"
  url: "https://killercoda.com/kubedojo/scenario/linux-4.4-seccomp"
  duration: "30 min"
  difficulty: "advanced"
  environment: "ubuntu"
---
> **Linux Security** | Complexity: `[MEDIUM]` | Time: 25-30 min

## Prerequisites

Before starting this module:
- **Required**: [Module 2.3: Capabilities & LSMs](../../foundations/container-primitives/module-2.3-capabilities-lsms/)
- **Required**: [Module 1.1: Kernel & Architecture](../../foundations/system-essentials/module-1.1-kernel-architecture/) (system calls)
- **Helpful**: Understanding of BPF concepts

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Write** custom seccomp profiles that allow only the system calls a container needs
- **Apply** seccomp profiles to Kubernetes pods using the security context
- **Debug** seccomp violations by tracing blocked syscalls with strace and audit logs
- **Evaluate** the default Docker/containerd seccomp profile and decide when a custom profile is needed

---

## Why This Module Matters

**seccomp (Secure Computing Mode)** filters system calls at the kernel level. Unlike AppArmor or SELinux which control resource access, seccomp controls which kernel functions a process can call at all.

> **Stop and think**: If AppArmor is already restricting a container from accessing `/etc/shadow`, what additional security value does blocking the `open` system call via seccomp provide? Consider the difference between restricting *targets* versus restricting *actions*.

Understanding seccomp helps you:

- **Reduce attack surface** — Block dangerous syscalls entirely
- **Harden containers** — Default Docker/K8s profiles block ~44 syscalls
- **Pass CKS exam** — seccomp profiles are directly tested
- **Debug "operation not permitted"** — When even capabilities aren't the issue

When a container gets "operation not permitted" for something root should be able to do, seccomp might be blocking the underlying syscall.

---

## Did You Know?

- **Linux has over 300 system calls** — seccomp can filter any of them. Most applications use fewer than 100.

- **seccomp-bpf uses Berkeley Packet Filter** — The same technology used for network packet filtering is used to filter syscalls. It's incredibly efficient.

- **Chrome was an early seccomp adopter** — Google implemented seccomp in Chrome's sandbox in 2012 to protect against renderer exploits.

- **A seccomp violation is fatal by default** — Unlike AppArmor (returns error), seccomp typically kills the process. This makes debugging harder but security tighter.

---

## How seccomp Works

### System Call Filtering

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECCOMP FILTERING                             │
│                                                                  │
│  Application                                                     │
│       │                                                          │
│       │ write(fd, buf, size)                                    │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    glibc wrapper                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│       │                                                          │
│       │ syscall(1, ...)  // SYS_write = 1                       │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                SECCOMP BPF FILTER                        │    │
│  │                                                          │    │
│  │   if (syscall_nr == SYS_write) → ALLOW                  │    │
│  │   if (syscall_nr == SYS_ptrace) → KILL                  │    │
│  │   if (syscall_nr == SYS_reboot) → ERRNO(EPERM)          │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│       │                                                          │
│       ▼                                                          │
│  Kernel executes syscall (if allowed)                           │
└─────────────────────────────────────────────────────────────────┘
```

> **Pause and predict**: If a seccomp filter evaluates a syscall and encounters multiple matching rules with different actions (e.g., one rule says `SCMP_ACT_ALLOW` and another says `SCMP_ACT_KILL`), how should the kernel resolve the conflict to prioritize security?

### seccomp Actions

| Action | Effect | Return |
|--------|--------|--------|
| `SCMP_ACT_ALLOW` | Permit syscall | Normal execution |
| `SCMP_ACT_ERRNO` | Deny with error | Error code (e.g., EPERM) |
| `SCMP_ACT_KILL` | Kill thread | SIGSYS |
| `SCMP_ACT_KILL_PROCESS` | Kill process | SIGSYS |
| `SCMP_ACT_TRAP` | Send SIGSYS | Can be handled |
| `SCMP_ACT_LOG` | Allow but log | Normal execution |
| `SCMP_ACT_TRACE` | Notify tracer | For debugging |

---

## seccomp Modes

### Strict Mode

Original seccomp—extremely restrictive:
- Only `read`, `write`, `exit`, `sigreturn` allowed
- Any other syscall kills the process
- Rarely used directly

### Filter Mode (seccomp-bpf)

Flexible filtering with BPF programs:
- Define custom allow/deny rules
- Check syscall arguments
- What Docker/Kubernetes use

```bash
# Check if seccomp is enabled
grep SECCOMP /boot/config-$(uname -r)
# CONFIG_SECCOMP=y
# CONFIG_SECCOMP_FILTER=y

# Check process seccomp status
grep Seccomp /proc/$$/status
# Seccomp:        0  (0=disabled, 1=strict, 2=filter)
```

---

## Profile Format

### Docker/Kubernetes JSON Format

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
        "read",
        "write",
        "open",
        "close",
        "stat",
        "fstat",
        "lseek",
        "mmap",
        "mprotect",
        "munmap"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": ["ptrace"],
      "action": "SCMP_ACT_ERRNO",
      "args": [],
      "errnoRet": 1
    }
  ]
}
```

### Profile Structure

| Field | Purpose |
|-------|---------|
| `defaultAction` | What to do if no rule matches |
| `architectures` | CPU architectures to support |
| `syscalls` | List of rules |
| `syscalls[].names` | System call names |
| `syscalls[].action` | What to do |
| `syscalls[].args` | Argument conditions |

---

## Default Profiles

### Docker Default Profile

Docker blocks ~44 dangerous syscalls:

```bash
# Syscalls blocked by Docker default profile:
# - acct            - kernel accounting
# - add_key         - kernel keyring
# - bpf             - BPF programs
# - clock_adjtime   - adjust system clock
# - clock_settime   - set system clock
# - clone           - with dangerous flags
# - create_module   - load kernel modules
# - delete_module   - unload kernel modules
# - finit_module    - load kernel modules
# - get_kernel_syms - kernel symbols
# - init_module     - load kernel modules
# - ioperm          - I/O port permissions
# - iopl            - I/O privilege level
# - kcmp            - compare kernel objects
# - kexec_load      - load new kernel
# - keyctl          - kernel keyring
# - lookup_dcookie  - kernel profiling
# - mount           - mount filesystems
# - move_pages      - move memory pages
# - open_by_handle_at - bypass permissions
# - perf_event_open - kernel profiling
# - pivot_root      - change root filesystem
# - process_vm_*    - access other process memory
# - ptrace          - debug other processes
# - query_module    - query kernel modules
# - reboot          - reboot system
# - request_key     - kernel keyring
# - set_mempolicy   - NUMA policy
# - setns           - enter namespaces
# - settimeofday    - set system time
# - swapoff/swapon  - swap management
# - sysfs           - deprecated
# - umount          - unmount filesystems
# - unshare         - create namespaces
# - userfaultfd     - page fault handling
```

### Checking Container Profile

```bash
# Docker
docker inspect <container> | jq '.[0].HostConfig.SecurityOpt'

# See if seccomp is active in container
docker exec <container> grep Seccomp /proc/1/status
# Seccomp:        2  (filter mode)
```

---

## Container seccomp

### Docker seccomp

```bash
# Use default profile (automatic)
docker run nginx

# Custom profile
docker run --security-opt seccomp=/path/to/profile.json nginx

# Disable seccomp (dangerous!)
docker run --security-opt seccomp=unconfined nginx
```

> **Stop and think**: Kubernetes provides a `RuntimeDefault` seccomp profile. In a highly locked-down environment, why might relying solely on `RuntimeDefault` be insufficient for a container that only runs a simple static Go web server?

### Kubernetes seccomp

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault    # Use container runtime's default
  containers:
  - name: app
    image: nginx
    securityContext:
      seccompProfile:
        type: Localhost
        localhostProfile: profiles/my-profile.json
```

### Profile Types in Kubernetes

| Type | Description |
|------|-------------|
| `RuntimeDefault` | Container runtime's default profile |
| `Localhost` | Custom profile on node |
| `Unconfined` | No seccomp (dangerous) |

### Profile Locations

```bash
# Kubernetes looks for profiles at:
/var/lib/kubelet/seccomp/profiles/

# Example
/var/lib/kubelet/seccomp/profiles/my-profile.json

# Reference in pod:
seccompProfile:
  type: Localhost
  localhostProfile: profiles/my-profile.json
```

---

## Creating Custom Profiles

### Audit Mode Profile

Start with logging to see what syscalls your app needs:

```json
{
  "defaultAction": "SCMP_ACT_LOG",
  "syscalls": []
}
```

### Generating from Audit

```bash
# Run with audit profile
docker run --security-opt seccomp=/path/to/audit-profile.json myapp

# Check audit log
sudo dmesg | grep seccomp
# Or
sudo ausearch -m SECCOMP

# Use tools like strace to see syscalls
strace -f -c myapp
```

### Restrictive Profile Example

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "accept", "accept4", "access", "bind", "brk",
        "chdir", "chmod", "chown", "close", "connect",
        "dup", "dup2", "dup3", "epoll_create", "epoll_ctl",
        "epoll_wait", "execve", "exit", "exit_group",
        "fcntl", "fstat", "futex", "getcwd", "getdents",
        "getegid", "geteuid", "getgid", "getpid", "getppid",
        "getuid", "ioctl", "listen", "lseek", "mmap",
        "mprotect", "munmap", "nanosleep", "open", "openat",
        "pipe", "poll", "read", "readlink", "recvfrom",
        "recvmsg", "rename", "rt_sigaction", "rt_sigprocmask",
        "sendto", "set_tid_address", "setsockopt", "socket",
        "stat", "statfs", "unlink", "write", "writev"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

### Argument Filtering

```json
{
  "syscalls": [
    {
      "names": ["socket"],
      "action": "SCMP_ACT_ALLOW",
      "args": [
        {
          "index": 0,
          "value": 2,
          "valueTwo": 0,
          "op": "SCMP_CMP_EQ"
        }
      ],
      "comment": "Only allow AF_INET sockets"
    }
  ]
}
```

---

## Debugging seccomp

### Finding Blocked Syscalls

```bash
# Check dmesg for seccomp kills
sudo dmesg | grep -i seccomp

# Example output:
# audit: type=1326 audit(...): avc:  denied  { sys_admin }
#   for  pid=1234 comm="myapp" syscall=157 compat=0
#   syscall=157 → look up in syscall table

# Look up syscall number
ausyscall 157
# or check /usr/include/asm/unistd_64.h

# Use strace to see what syscalls app makes
strace -f -o /tmp/strace.log myapp
grep -E "^[0-9]" /tmp/strace.log | awk '{print $2}' | sort | uniq -c | sort -rn
```

### Common Issues

```bash
# Issue: Process killed immediately
# Cause: Critical syscall blocked (like mmap, brk)
# Fix: Add to allow list

# Issue: "Operation not permitted" but not killed
# Cause: SCMP_ACT_ERRNO returning EPERM
# Fix: Add syscall or check args filter

# Issue: Works without seccomp, fails with
# Debug: Use SCMP_ACT_LOG temporarily
```

### Testing Profiles

```bash
# Test with a simple profile
cat > /tmp/test-seccomp.json << 'EOF'
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "syscalls": [
    {
      "names": ["read", "write", "exit", "exit_group", "rt_sigreturn"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
EOF

# Test
docker run --rm --security-opt seccomp=/tmp/test-seccomp.json alpine echo "hello"
# Should fail (echo needs more syscalls)
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Disabling seccomp | Dangerous syscalls allowed | Use RuntimeDefault at minimum |
| Profile too restrictive | App crashes | Use audit mode first |
| Missing architecture | Fails on ARM | Include all target archs |
| Not testing profile | Production failures | Test thoroughly in staging |
| Using unconfined | No syscall filtering | Always use a profile |
| KILL vs ERRNO | Hard to debug | Use ERRNO for debugging |

---

## Quiz

### Question 1
You are deploying a legacy third-party application in a container. During staging, the application unexpectedly crashes immediately upon startup without writing any error logs. You suspect a seccomp violation. If the current profile uses `SCMP_ACT_KILL` as the default action, why would changing it to `SCMP_ACT_ERRNO` help diagnose the issue, and what are the security trade-offs of leaving it as `SCMP_ACT_ERRNO` in production?

<details>
<summary>Show Answer</summary>

Changing the action to `SCMP_ACT_ERRNO` prevents the kernel from immediately terminating the process with a `SIGSYS` signal, which is what `SCMP_ACT_KILL` does. Instead, the kernel blocks the system call and returns an error code (like `EPERM`) back to the application. This allows the application to handle the error gracefully or log a descriptive error message indicating that a specific operation was not permitted, making debugging significantly easier. However, leaving `SCMP_ACT_ERRNO` in production reduces security because an attacker exploiting the application can probe the system to map out exactly which system calls are permitted and which are blocked. `SCMP_ACT_KILL` is strictly safer because it instantly neutralizes compromised threads the moment they attempt an unauthorized action, giving the attacker no feedback.

</details>

### Question 2
You have perfectly configured AppArmor to ensure a web server container can only read files in `/var/www/html` and cannot write anywhere on the filesystem. A colleague argues that applying a seccomp profile is redundant since the file access is already locked down. Based on how system calls function compared to Mandatory Access Control (MAC) systems, why is your colleague incorrect?

<details>
<summary>Show Answer</summary>

Your colleague is incorrect because AppArmor and seccomp operate at different conceptual layers and mitigate different classes of vulnerabilities. AppArmor and SELinux are Mandatory Access Control systems that mediate access to specific resources, such as file paths or network sockets, after the application has already invoked a system call. In contrast, seccomp filters the invocation of the system calls themselves, completely removing kernel surface area. For example, an attacker who finds a remote code execution vulnerability might attempt to execute system calls like `ptrace` or `unshare` to exploit kernel bugs or manipulate memory, which do not involve file paths at all. By using seccomp to block system calls the web server never needs, you eliminate the kernel attack surface entirely, providing defense in depth even if the MAC system is bypassed.

</details>

### Question 3
A security audit requires you to apply a custom, highly restrictive seccomp profile named `api-strict.json` to a deployment of API pods. You have placed the JSON file in the correct directory on all Kubernetes worker nodes. When configuring the Pod specification, what exact fields must you define in the `securityContext` to ensure the pod utilizes this specific file rather than the container runtime's default?

<details>
<summary>Show Answer</summary>

To apply a custom profile located on the worker nodes, you must configure the `seccompProfile` field within the pod's or container's `securityContext` to use the `Localhost` type. Specifically, you need to set `type: Localhost` and provide the relative path to the profile using the `localhostProfile` field, such as `localhostProfile: profiles/api-strict.json`. This tells the Kubelet to look in its default seccomp profile directory (typically `/var/lib/kubelet/seccomp/`) for the specified file and instruct the container runtime to apply it. If you were to use `type: RuntimeDefault`, the container would simply inherit the generic, broad profile provided by Docker or containerd, which would fail to meet the strict requirements of your security audit.

</details>

### Question 4
An automated security scanner flags your container image because it requires the `CAP_SYS_ADMIN` capability to perform its legitimate function. To mitigate the risk of a container escape, you decide to write a custom seccomp profile. Which specific system calls should you explicitly ensure are blocked to prevent an attacker from creating new namespaces or mounting the host filesystem, and why?

<details>
<summary>Show Answer</summary>

To prevent namespace manipulation and filesystem mounting—common techniques for container escapes—you must explicitly block the `unshare`, `setns`, and `mount` system calls. The `unshare` system call allows a process to disassociate parts of its execution context, effectively allowing an attacker to create new, isolated namespaces where they might gain elevated privileges. The `setns` system call allows a process to enter an existing namespace, which could be abused to break out of the container's isolation and join the host's namespaces. Finally, the `mount` system call must be blocked because an attacker with `CAP_SYS_ADMIN` could use it to mount the host's underlying root filesystem into the container, granting them full read and write access to the host node's files. Blocking these system calls neutralizes the most direct vectors for escaping the container boundary.

</details>

### Question 5
You are migrating a complex Java application to a hardened Kubernetes cluster that enforces a strict custom seccomp profile. Upon deployment, the application pod repeatedly enters a `CrashLoopBackOff` state. You suspect a critical system call is being denied, but the application logs show no errors before terminating. Outline the exact steps you would take at the host kernel level to identify the specific blocked system call.

<details>
<summary>Show Answer</summary>

Because seccomp violations often result in immediate process termination via `SIGSYS` (if `SCMP_ACT_KILL` is used), the application will not have a chance to write to its standard error logs. The most reliable way to identify the blocked system call is to inspect the kernel audit logs on the host node where the pod was scheduled. You can do this by SSHing into the worker node and running `sudo dmesg | grep -i seccomp` or `sudo ausearch -m SECCOMP` to view the audit trails. The kernel logs will display an audit event indicating that a system call was denied, along with the PID and the numeric system call ID (e.g., `syscall=157`). Once you have the numeric ID, you can use a tool like `ausyscall <number>` or reference the kernel header files (like `unistd_64.h`) to translate the number into the human-readable system call name, which you can then evaluate for inclusion in your custom profile.

</details>

---

## Hands-On Exercise

### Working with seccomp

**Objective**: Understand seccomp profiles and testing.

**Environment**: Linux with Docker installed

#### Part 1: Check seccomp Status

```bash
# 1. Kernel support
grep SECCOMP /boot/config-$(uname -r)

# 2. Your process
grep Seccomp /proc/$$/status

# 3. Container process
docker run --rm alpine grep Seccomp /proc/1/status
```

#### Part 2: Test Default Profile

```bash
# 1. Run with default seccomp
docker run --rm alpine sh -c 'grep Seccomp /proc/1/status'
# Should show: Seccomp: 2

# 2. Try to run unconfined
docker run --rm --security-opt seccomp=unconfined alpine grep Seccomp /proc/1/status
# Should show: Seccomp: 0

# 3. Test a blocked syscall
# reboot should fail silently
docker run --rm alpine reboot
# No effect (blocked by default profile)
```

#### Part 3: Create Custom Profile

```bash
# 1. Create a restrictive profile
cat > /tmp/restrictive.json << 'EOF'
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_AARCH64"],
  "syscalls": [
    {
      "names": [
        "read", "write", "open", "openat", "close",
        "stat", "fstat", "lstat", "mmap", "mprotect",
        "munmap", "brk", "exit_group", "arch_prctl",
        "access", "getuid", "getgid", "geteuid", "getegid",
        "execve", "fcntl", "dup2", "pipe", "rt_sigaction",
        "rt_sigprocmask", "rt_sigreturn", "clone", "wait4",
        "futex", "set_tid_address", "set_robust_list"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
EOF

# 2. Test ls (should work)
docker run --rm --security-opt seccomp=/tmp/restrictive.json alpine ls /

# 3. Test something more complex (might fail)
docker run --rm --security-opt seccomp=/tmp/restrictive.json alpine ping -c 1 127.0.0.1
# May fail due to missing syscalls
```

#### Part 4: Audit Mode

```bash
# 1. Create audit profile
cat > /tmp/audit.json << 'EOF'
{
  "defaultAction": "SCMP_ACT_LOG",
  "syscalls": []
}
EOF

# 2. Run with audit
docker run --rm --security-opt seccomp=/tmp/audit.json alpine ls /

# 3. Check what was logged
sudo dmesg | grep seccomp | tail -20
```

#### Part 5: Debug Blocked Syscalls

```bash
# 1. Create overly restrictive profile
cat > /tmp/broken.json << 'EOF'
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "syscalls": [
    {
      "names": ["exit_group"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
EOF

# 2. Try to run (will fail)
docker run --rm --security-opt seccomp=/tmp/broken.json alpine echo hello 2>&1
# Error or no output

# 3. Check what failed
sudo dmesg | grep seccomp | tail -10
```

### Success Criteria

- [ ] Verified seccomp is enabled
- [ ] Compared default vs unconfined profiles
- [ ] Created and tested custom profile
- [ ] Used audit mode to see syscalls
- [ ] Debugged a blocked syscall

---

## Key Takeaways

1. **Syscall-level filtering** — More fundamental than file/network controls

2. **Default profiles block 40+ syscalls** — Docker/K8s have sane defaults

3. **KILL vs ERRNO** — Kill is secure, ERRNO is debuggable

4. **Audit mode for development** — Log all syscalls to build profile

5. **Defense in depth** — Use with AppArmor/SELinux, not instead of

---

## What's Next?

Congratulations! You've completed the **Security/Hardening** section. You now understand:
- Kernel hardening via sysctl
- AppArmor profiles and MAC
- SELinux contexts and type enforcement
- seccomp system call filtering

Next, continue to **Operations/Performance** to learn about system performance analysis.

---

## Further Reading

- [seccomp man page](https://man7.org/linux/man-pages/man2/seccomp.2.html)
- [Docker seccomp profiles](https://docs.docker.com/engine/security/seccomp/)
- [Kubernetes seccomp](https://kubernetes.io/docs/tutorials/security/seccomp/)
- [BPF and seccomp](https://lwn.net/Articles/656307/)