---
title: "Module 2.3: Capabilities & Linux Security Modules"
slug: linux/foundations/container-primitives/module-2.3-capabilities-lsms
sidebar:
  order: 4
---
> **Linux Foundations** | Complexity: `[MEDIUM]` | Time: 25-30 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.4: Users & Permissions](../system-essentials/module-1.4-users-permissions/)
- **Required**: [Module 2.1: Linux Namespaces](../module-2.1-namespaces/)
- **Helpful**: Understanding of basic security concepts

---

## Why This Module Matters

Traditional Unix had a simple security model: root can do everything, everyone else is restricted. This all-or-nothing approach is dangerous—why give a process full root power when it only needs to bind to port 80?

**Capabilities** break root's superpowers into granular pieces. **Linux Security Modules (LSMs)** add mandatory access controls beyond discretionary permissions.

Understanding these helps you:

- **Secure containers** — Drop unnecessary capabilities
- **Debug permission errors** — Why can't my container do X?
- **Implement least privilege** — Give only the access needed
- **Understand Kubernetes security** — SecurityContext, PodSecurityPolicies, seccomp

When your container fails with "operation not permitted" despite running as root, capabilities are usually the answer.

---

## Did You Know?

- **There are over 40 different capabilities** in modern Linux. CAP_NET_ADMIN alone controls dozens of networking operations, from configuring interfaces to modifying routing tables.

- **Docker drops many capabilities by default** — A container with "root" is missing CAP_SYS_ADMIN, CAP_NET_ADMIN, and others. This is why root in a container isn't the same as root on the host.

- **The `ping` command used to require setuid root** — Now it uses CAP_NET_RAW capability instead. This is much safer because ping can only send raw packets, not do everything root can.

- **seccomp can block over 300 system calls** — Kubernetes and Docker apply a default seccomp profile that blocks dangerous syscalls like `kexec_load` (which loads a new kernel) and `reboot`.

---

## Linux Capabilities

### The Problem with Root

Traditional Unix:

```
┌─────────────────────────────────────────────────────────────────┐
│                     TRADITIONAL MODEL                            │
│                                                                  │
│  Root (UID 0)                    Normal User (UID 1000)         │
│  ┌──────────────────────┐       ┌──────────────────────┐        │
│  │ ALL PRIVILEGES       │       │ Limited privileges   │        │
│  │ - Bind any port      │       │ - Can't bind < 1024  │        │
│  │ - Read any file      │       │ - Own files only     │        │
│  │ - Kill any process   │       │ - Own processes only │        │
│  │ - Load kernel modules│       │ - No kernel access   │        │
│  │ - Reboot system      │       │ - Can't reboot       │        │
│  │ - Change any config  │       │ - Limited config     │        │
│  └──────────────────────┘       └──────────────────────┘        │
│                                                                  │
│  ALL or NOTHING - dangerous for services that need only ONE     │
│  capability from the "ALL" bucket                                │
└─────────────────────────────────────────────────────────────────┘
```

### Capabilities: Granular Privileges

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPABILITIES MODEL                            │
│                                                                  │
│  Root's powers split into ~40 capabilities:                     │
│                                                                  │
│  ┌───────────────┬───────────────┬───────────────┐              │
│  │ CAP_NET_BIND_ │ CAP_CHOWN     │ CAP_KILL      │              │
│  │ SERVICE       │               │               │              │
│  │ Bind < 1024   │ Change owner  │ Kill any proc │              │
│  └───────────────┴───────────────┴───────────────┘              │
│  ┌───────────────┬───────────────┬───────────────┐              │
│  │ CAP_SYS_ADMIN │ CAP_NET_ADMIN │ CAP_SYS_PTRACE│              │
│  │ Many things!  │ Network cfg   │ Trace procs   │              │
│  └───────────────┴───────────────┴───────────────┘              │
│  ┌───────────────┬───────────────┬───────────────┐              │
│  │ CAP_NET_RAW   │ CAP_SETUID    │ CAP_SETGID    │              │
│  │ Raw sockets   │ Set UID       │ Set GID       │              │
│  └───────────────┴───────────────┴───────────────┘              │
│                         ...                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Common Capabilities

| Capability | What It Allows | Used By |
|------------|----------------|---------|
| CAP_NET_BIND_SERVICE | Bind to ports < 1024 | Web servers |
| CAP_NET_RAW | Raw sockets, ping | ping, network tools |
| CAP_NET_ADMIN | Network configuration | Network management |
| CAP_SYS_ADMIN | Many admin operations | Container escapes! |
| CAP_CHOWN | Change file ownership | File management |
| CAP_SETUID/SETGID | Change process UID/GID | su, sudo |
| CAP_KILL | Send signals to any process | Process management |
| CAP_SYS_PTRACE | Trace/debug processes | Debuggers, strace |
| CAP_MKNOD | Create device nodes | Device setup |
| CAP_DAC_OVERRIDE | Bypass file permissions | Full file access |

### Viewing Capabilities

```bash
# View capabilities of current process
cat /proc/$$/status | grep Cap

# Decode capability hex values
capsh --decode=0000003fffffffff

# View capabilities of a file
getcap /usr/bin/ping

# View capabilities of running process
getpcaps $$

# List all capabilities
capsh --print
```

### Capability Sets

Each process has multiple capability sets:

| Set | Purpose |
|-----|---------|
| Permitted | Maximum capabilities available |
| Effective | Currently active capabilities |
| Inheritable | Can be passed to children |
| Bounding | Limits what can be gained |
| Ambient | Preserved across execve() |

```bash
# View all sets
cat /proc/$$/status | grep Cap
# CapInh: Inheritable
# CapPrm: Permitted
# CapEff: Effective
# CapBnd: Bounding
# CapAmb: Ambient
```

### Setting File Capabilities

```bash
# Give a program capability without setuid
sudo setcap 'cap_net_bind_service=+ep' /path/to/program

# Verify
getcap /path/to/program

# Remove capabilities
sudo setcap -r /path/to/program
```

---

## Container Capabilities

### Docker Default Capabilities

Docker containers run with a restricted set:

```
Default Docker capabilities:
- CAP_CHOWN
- CAP_DAC_OVERRIDE
- CAP_FSETID
- CAP_FOWNER
- CAP_MKNOD
- CAP_NET_RAW
- CAP_SETGID
- CAP_SETUID
- CAP_SETFCAP
- CAP_SETPCAP
- CAP_NET_BIND_SERVICE
- CAP_SYS_CHROOT
- CAP_KILL
- CAP_AUDIT_WRITE

NOT included (dangerous):
- CAP_SYS_ADMIN    ← Container escape risk!
- CAP_NET_ADMIN    ← Network manipulation
- CAP_SYS_PTRACE   ← Debug other processes
- CAP_SYS_MODULE   ← Load kernel modules
```

### Modifying Container Capabilities

```bash
# Drop all capabilities
docker run --cap-drop=ALL nginx

# Add specific capability
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE nginx

# Run privileged (ALL capabilities - dangerous!)
docker run --privileged nginx
```

### Kubernetes SecurityContext

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    securityContext:
      capabilities:
        drop:
          - ALL                    # Drop everything first
        add:
          - NET_BIND_SERVICE       # Add only what's needed
```

---

## Linux Security Modules (LSMs)

Beyond DAC (discretionary access control) and capabilities, LSMs provide **mandatory access control (MAC)**.

### LSM Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SECURITY STACK                            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Application                           │    │
│  └────────────────────────────┬────────────────────────────┘    │
│                               │                                  │
│                          System Call                             │
│                               │                                  │
│  ┌────────────────────────────▼────────────────────────────┐    │
│  │           DAC (Discretionary Access Control)             │    │
│  │                 File permissions (rwx)                   │    │
│  └────────────────────────────┬────────────────────────────┘    │
│                               │                                  │
│  ┌────────────────────────────▼────────────────────────────┐    │
│  │                      Capabilities                        │    │
│  │               Does process have CAP_*?                   │    │
│  └────────────────────────────┬────────────────────────────┘    │
│                               │                                  │
│  ┌────────────────────────────▼────────────────────────────┐    │
│  │                          LSM                             │    │
│  │        AppArmor / SELinux / Seccomp / SMACK             │    │
│  │           Mandatory Access Control (MAC)                 │    │
│  └────────────────────────────┬────────────────────────────┘    │
│                               │                                  │
│                          Kernel                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Available LSMs

| LSM | Distribution | Approach |
|-----|-------------|----------|
| SELinux | RHEL, CentOS, Fedora | Label-based, complex |
| AppArmor | Ubuntu, Debian, SUSE | Path-based, simpler |
| Seccomp | All (filter) | System call filtering |
| SMACK | Embedded systems | Simplified labels |

### Check What's Active

```bash
# Which LSM is active
cat /sys/kernel/security/lsm

# AppArmor status
sudo aa-status

# SELinux status
sestatus
getenforce
```

---

## AppArmor

Path-based mandatory access control. Simpler than SELinux.

### Profile Modes

| Mode | Behavior |
|------|----------|
| Enforce | Blocks and logs violations |
| Complain | Logs but doesn't block |
| Unconfined | No restrictions |

### Viewing Profiles

```bash
# List profiles
sudo aa-status

# Sample output:
# apparmor module is loaded.
# 32 profiles are loaded.
# 30 profiles are in enforce mode.
#    /usr/bin/evince
#    /usr/sbin/cups-browsed
#    docker-default

# View a profile
cat /etc/apparmor.d/usr.bin.evince
```

### AppArmor Profile Structure

```
# /etc/apparmor.d/usr.sbin.nginx
#include <tunables/global>

/usr/sbin/nginx {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  # Allow network access
  network inet tcp,
  network inet udp,

  # Allow reading config
  /etc/nginx/** r,

  # Allow writing logs
  /var/log/nginx/** rw,

  # Allow web root
  /var/www/** r,

  # Deny everything else by default
}
```

### Container AppArmor

```bash
# Docker default profile
docker run --security-opt apparmor=docker-default nginx

# Custom profile
docker run --security-opt apparmor=my-custom-profile nginx

# No AppArmor (dangerous!)
docker run --security-opt apparmor=unconfined nginx
```

### Kubernetes AppArmor

```yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    container.apparmor.security.beta.kubernetes.io/app: localhost/my-profile
spec:
  containers:
  - name: app
    image: nginx
```

---

## Seccomp

**Secure Computing Mode** — Filters system calls at the kernel level.

### How Seccomp Works

```
┌─────────────────────────────────────────────────────────────────┐
│                      SECCOMP FILTER                              │
│                                                                  │
│  Application wants to call: open("/etc/passwd", O_RDONLY)       │
│                               │                                  │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Seccomp BPF Filter                    │    │
│  │                                                          │    │
│  │   Is syscall "open" (nr=2) allowed?                     │    │
│  │     → Check profile rules                                │    │
│  │     → ALLOW / ERRNO / KILL / LOG                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                               │                                  │
│            ┌──────────────────┼──────────────────┐              │
│            ▼                  ▼                  ▼              │
│       ALLOW              ERRNO(EPERM)         KILL              │
│    (proceed)           (return error)     (kill process)        │
└─────────────────────────────────────────────────────────────────┘
```

### Default Docker Seccomp Profile

Docker blocks ~44 syscalls by default:

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "syscalls": [
    {
      "names": ["accept", "accept4", "access", "..."],
      "action": "SCMP_ACT_ALLOW"
    }
  ],
  "blocked": [
    "kexec_load",        // Load new kernel
    "reboot",            // Reboot system
    "mount",             // Mount filesystems (by default)
    "ptrace",            // Trace processes (often blocked)
    "...40+ others"
  ]
}
```

### Seccomp Actions

| Action | Effect |
|--------|--------|
| SCMP_ACT_ALLOW | Allow syscall |
| SCMP_ACT_ERRNO | Return error code |
| SCMP_ACT_KILL | Kill process |
| SCMP_ACT_KILL_PROCESS | Kill all threads |
| SCMP_ACT_LOG | Allow but log |
| SCMP_ACT_TRACE | Notify tracer |

### Container Seccomp

```bash
# Use default profile (recommended)
docker run nginx

# Custom profile
docker run --security-opt seccomp=/path/to/profile.json nginx

# No seccomp (dangerous!)
docker run --security-opt seccomp=unconfined nginx
```

### Kubernetes Seccomp

```yaml
apiVersion: v1
kind: Pod
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault  # Use container runtime's default
  containers:
  - name: app
    securityContext:
      seccompProfile:
        type: Localhost
        localhostProfile: profiles/my-profile.json
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Running containers as privileged | Full capabilities, escape risk | Use specific capabilities instead |
| Not dropping capabilities | Unnecessary attack surface | Drop ALL, add only needed |
| Disabling seccomp | Allows dangerous syscalls | Use RuntimeDefault or custom profile |
| Ignoring AppArmor/SELinux | Missing MAC protection | Keep enabled, use container profiles |
| CAP_SYS_ADMIN "for convenience" | Major security risk | Find specific capability needed |
| No capabilities understanding | Can't debug permission issues | Learn common capabilities |

---

## Quiz

### Question 1
Why is CAP_SYS_ADMIN considered dangerous for containers?

<details>
<summary>Show Answer</summary>

CAP_SYS_ADMIN is a "catch-all" capability that grants many privileges including:
- Mounting filesystems
- Using ptrace on processes
- Configuring namespaces
- Many other administrative operations

With CAP_SYS_ADMIN, a container can often escape to the host. It's sometimes called "the new root."

</details>

### Question 2
What's the difference between AppArmor and seccomp?

<details>
<summary>Show Answer</summary>

| AppArmor | Seccomp |
|----------|---------|
| Path-based access control | System call filtering |
| Controls file/network access | Controls which syscalls allowed |
| Profiles per application | Filters per process |
| Higher level (paths, networks) | Lower level (syscall numbers) |

They complement each other—AppArmor controls what resources are accessed, seccomp controls how they're accessed (which syscalls).

</details>

### Question 3
How do you give a container only the capability to bind to port 80?

<details>
<summary>Show Answer</summary>

```bash
# Docker
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE nginx
```

```yaml
# Kubernetes
securityContext:
  capabilities:
    drop:
      - ALL
    add:
      - NET_BIND_SERVICE
```

This follows least privilege—drop all capabilities, add only what's needed.

</details>

### Question 4
What does `--privileged` do in Docker?

<details>
<summary>Show Answer</summary>

`--privileged` gives the container:
- ALL capabilities
- Access to all devices
- Disables seccomp
- Disables AppArmor
- Mounts /dev fully

The container is essentially as powerful as root on the host. **Never use in production** unless absolutely necessary (and even then, reconsider).

</details>

### Question 5
What happens when a process tries to make a syscall blocked by seccomp?

<details>
<summary>Show Answer</summary>

Depends on the action configured:
- **SCMP_ACT_ERRNO**: Returns error (like EPERM)
- **SCMP_ACT_KILL**: Process is terminated immediately
- **SCMP_ACT_LOG**: Allowed but logged

Default Docker profile uses ERRNO for most blocked calls, allowing the process to handle the error gracefully.

</details>

---

## Hands-On Exercise

### Capabilities and Security Modules

**Objective**: Explore capabilities, AppArmor, and seccomp.

**Environment**: Linux system (Ubuntu/Debian for AppArmor examples)

#### Part 1: Viewing Capabilities

```bash
# 1. Your process capabilities
cat /proc/$$/status | grep Cap

# 2. Decode them
capsh --decode=$(grep CapEff /proc/$$/status | cut -f2)

# 3. Check a common program
getcap /usr/bin/ping 2>/dev/null || getcap /bin/ping

# 4. List all files with capabilities
getcap -r / 2>/dev/null | head -20
```

#### Part 2: File Capabilities (requires root)

```bash
# 1. Create a test program
cat > /tmp/test-bind.c << 'EOF'
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h>

int main() {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port = htons(80),
        .sin_addr.s_addr = INADDR_ANY
    };
    if (bind(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind failed");
        return 1;
    }
    printf("Successfully bound to port 80!\n");
    return 0;
}
EOF

# 2. Compile
gcc /tmp/test-bind.c -o /tmp/test-bind

# 3. Try as normal user (should fail)
/tmp/test-bind
# bind failed: Permission denied

# 4. Add capability
sudo setcap 'cap_net_bind_service=+ep' /tmp/test-bind

# 5. Verify
getcap /tmp/test-bind

# 6. Try again (should work)
/tmp/test-bind

# 7. Clean up
rm /tmp/test-bind /tmp/test-bind.c
```

#### Part 3: AppArmor (Ubuntu/Debian)

```bash
# 1. Check AppArmor status
sudo aa-status

# 2. List profiles
ls /etc/apparmor.d/

# 3. View a profile
cat /etc/apparmor.d/usr.sbin.tcpdump 2>/dev/null || \
    cat /etc/apparmor.d/usr.bin.firefox 2>/dev/null | head -50
```

#### Part 4: Seccomp Information

```bash
# 1. Check if seccomp is enabled
grep SECCOMP /boot/config-$(uname -r)

# 2. View process seccomp status
grep Seccomp /proc/$$/status

# 3. If Docker installed, view default profile
docker run --rm alpine cat /proc/1/status | grep Seccomp
```

#### Part 5: Container Capabilities (if Docker available)

```bash
# 1. Default capabilities
docker run --rm alpine sh -c 'cat /proc/1/status | grep Cap'

# 2. Drop all capabilities
docker run --rm --cap-drop=ALL alpine sh -c 'cat /proc/1/status | grep Cap'

# 3. Try privileged operations
docker run --rm alpine ping -c 1 8.8.8.8  # Works (CAP_NET_RAW)
docker run --rm --cap-drop=ALL alpine ping -c 1 8.8.8.8  # Fails
docker run --rm --cap-drop=ALL --cap-add=NET_RAW alpine ping -c 1 8.8.8.8  # Works
```

### Success Criteria

- [ ] Viewed and decoded process capabilities
- [ ] Found programs with file capabilities
- [ ] (Optional) Set and used file capabilities
- [ ] Explored AppArmor status
- [ ] Understood seccomp status
- [ ] (Docker) Tested capability dropping

---

## Key Takeaways

1. **Capabilities split root power** — 40+ specific privileges instead of all-or-nothing

2. **Drop ALL, add specific** — Best practice for container security

3. **LSMs add MAC** — Beyond DAC, mandatory controls enforce policy

4. **AppArmor = paths, seccomp = syscalls** — Complementary security layers

5. **--privileged is dangerous** — Gives ALL capabilities, disables protections

---

## What's Next?

In **Module 2.4: Union Filesystems**, you'll learn how container images use layered filesystems for efficient storage and sharing.

---

## Further Reading

- [Linux Capabilities man page](https://man7.org/linux/man-pages/man7/capabilities.7.html)
- [AppArmor Documentation](https://gitlab.com/apparmor/apparmor/-/wikis/Documentation)
- [Docker Security](https://docs.docker.com/engine/security/)
- [Kubernetes Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [Seccomp BPF](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html)
