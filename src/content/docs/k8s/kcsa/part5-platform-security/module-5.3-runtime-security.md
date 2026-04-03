---
title: "Module 5.3: Runtime Security"
slug: k8s/kcsa/part5-platform-security/module-5.3-runtime-security
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]` - Core knowledge
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 5.2: Security Observability](../module-5.2-observability/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** runtime security controls: seccomp profiles, AppArmor, SELinux, and Falco rules
2. **Assess** which runtime threats each enforcement mechanism is designed to detect or prevent
3. **Compare** kernel-level enforcement (seccomp, AppArmor) with behavioral detection (Falco)
4. **Identify** runtime security gaps where an attacker could operate undetected

---

## Why This Module Matters

Runtime security enforces security policies while workloads are running. Unlike build-time or deploy-time controls that prevent bad configurations, runtime security detects and responds to active threats—when an attacker has already gained access and is trying to move laterally or exfiltrate data.

KCSA tests your understanding of runtime security concepts, including seccomp, AppArmor, SELinux, and enforcement tools.

---

## Runtime Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│              RUNTIME SECURITY STACK                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LAYER 4: KUBERNETES ADMISSION                             │
│  ├── Validates pods before scheduling                      │
│  ├── Pod Security Standards                                │
│  └── Policy engines (OPA, Kyverno)                        │
│                                                             │
│  LAYER 3: CONTAINER RUNTIME                                │
│  ├── OCI runtime (runc, crun)                             │
│  ├── Sandboxed runtimes (gVisor, Kata)                    │
│  └── Runtime security configuration                        │
│                                                             │
│  LAYER 2: LINUX SECURITY MODULES                           │
│  ├── seccomp (syscall filtering)                          │
│  ├── AppArmor (file/network restrictions)                 │
│  ├── SELinux (mandatory access control)                   │
│  └── Capabilities (privilege restrictions)                 │
│                                                             │
│  LAYER 1: KERNEL                                           │
│  ├── Namespaces (isolation)                               │
│  ├── cgroups (resource limits)                            │
│  └── Core security features                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Seccomp Profiles

### What is Seccomp?

```
┌─────────────────────────────────────────────────────────────┐
│              SECCOMP (SECURE COMPUTING MODE)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PURPOSE:                                                  │
│  • Filter which system calls a process can make            │
│  • Block dangerous syscalls (mount, ptrace, etc.)          │
│  • Reduce kernel attack surface                            │
│                                                             │
│  HOW IT WORKS:                                             │
│  Application → Syscall → Seccomp Filter → Allow/Deny/Log  │
│                                                             │
│  PROFILE TYPES:                                            │
│  ├── RuntimeDefault - Container runtime's default profile │
│  ├── Unconfined - No filtering (dangerous)                │
│  └── Localhost - Custom profile from node                 │
│                                                             │
│  KUBERNETES 1.27+:                                         │
│  RuntimeDefault is the default for new clusters            │
│                                                             │
│  BLOCKED BY DEFAULT (RuntimeDefault):                      │
│  • mount, umount                                          │
│  • ptrace                                                 │
│  • reboot                                                 │
│  • Most kernel module operations                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Seccomp in Pods

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault  # Use container runtime's default
  containers:
  - name: app
    image: myapp:1.0
```

```yaml
# Custom seccomp profile
apiVersion: v1
kind: Pod
metadata:
  name: custom-seccomp
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/my-profile.json  # On node
  containers:
  - name: app
    image: myapp:1.0
```

### Custom Seccomp Profile

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "read", "write", "open", "close",
        "stat", "fstat", "lstat",
        "poll", "lseek", "mmap",
        "exit", "exit_group"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

---

## AppArmor Profiles

### What is AppArmor?

```
┌─────────────────────────────────────────────────────────────┐
│              APPARMOR                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PURPOSE:                                                  │
│  • Mandatory Access Control (MAC)                          │
│  • Restrict file access, network, capabilities             │
│  • Program-specific security policies                      │
│                                                             │
│  AVAILABLE ON:                                             │
│  • Ubuntu, Debian, SUSE                                   │
│  • NOT on RHEL/CentOS (use SELinux instead)               │
│                                                             │
│  PROFILE MODES:                                            │
│  ├── Enforce - Block violations                           │
│  ├── Complain - Log but allow (learning mode)             │
│  └── Unconfined - No restrictions                         │
│                                                             │
│  EXAMPLE RESTRICTIONS:                                     │
│  • Deny write to /etc/*                                   │
│  • Allow read from /var/log/*                             │
│  • Deny network raw access                                │
│  • Deny mount operations                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### AppArmor in Kubernetes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: apparmor-pod
  annotations:
    # Apply AppArmor profile to container
    container.apparmor.security.beta.kubernetes.io/app: localhost/my-profile
spec:
  containers:
  - name: app
    image: nginx:1.25
```

### Example AppArmor Profile

```
#include <tunables/global>

profile my-profile flags=(attach_disconnected) {
  #include <abstractions/base>

  # Allow reading from specific directories
  /var/www/** r,
  /etc/nginx/** r,

  # Allow writing to logs
  /var/log/nginx/** rw,

  # Deny writing to sensitive files
  deny /etc/passwd w,
  deny /etc/shadow rw,

  # Network restrictions
  network inet tcp,
  network inet udp,
  deny network raw,

  # Deny mount operations
  deny mount,
  deny umount,
}
```

---

## SELinux

### What is SELinux?

```
┌─────────────────────────────────────────────────────────────┐
│              SELINUX                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PURPOSE:                                                  │
│  • Mandatory Access Control (MAC)                          │
│  • Label-based security                                    │
│  • Every file, process has a security context              │
│                                                             │
│  AVAILABLE ON:                                             │
│  • RHEL, CentOS, Fedora                                   │
│  • NOT on Ubuntu/Debian (use AppArmor)                    │
│                                                             │
│  MODES:                                                    │
│  ├── Enforcing - Block violations                         │
│  ├── Permissive - Log but allow                           │
│  └── Disabled - No SELinux                                │
│                                                             │
│  CONTEXT FORMAT:                                           │
│  user:role:type:level                                      │
│  system_u:system_r:container_t:s0                         │
│                                                             │
│  KUBERNETES USES:                                          │
│  • seLinuxOptions in securityContext                      │
│  • Labels for pod processes and volumes                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### SELinux in Kubernetes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: selinux-pod
spec:
  securityContext:
    seLinuxOptions:
      level: "s0:c123,c456"  # MCS labels
  containers:
  - name: app
    image: myapp:1.0
    securityContext:
      seLinuxOptions:
        type: "container_t"
```

---

## Linux Capabilities

```
┌─────────────────────────────────────────────────────────────┐
│              LINUX CAPABILITIES                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PURPOSE:                                                  │
│  • Break down root privileges into discrete units          │
│  • Grant specific privileges without full root             │
│  • Reduce privilege if container is compromised            │
│                                                             │
│  DEFAULT CAPABILITIES (container runtime):                 │
│  • CHOWN, DAC_OVERRIDE, FSETID, FOWNER                    │
│  • MKNOD, NET_RAW, SETGID, SETUID                         │
│  • SETFCAP, SETPCAP, NET_BIND_SERVICE                     │
│  • SYS_CHROOT, KILL, AUDIT_WRITE                          │
│                                                             │
│  DANGEROUS CAPABILITIES:                                   │
│  • CAP_SYS_ADMIN - Near-root privileges                   │
│  • CAP_NET_ADMIN - Network configuration                  │
│  • CAP_SYS_PTRACE - Debug any process                     │
│  • CAP_DAC_READ_SEARCH - Bypass read permissions          │
│                                                             │
│  BEST PRACTICE:                                            │
│  Drop all, add only what's needed                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Capabilities in Pods

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: minimal-caps
spec:
  containers:
  - name: app
    image: myapp:1.0
    securityContext:
      capabilities:
        drop:
          - ALL         # Drop all capabilities
        add:
          - NET_BIND_SERVICE  # Add back only what's needed
```

---

## Runtime Enforcement Tools

### OPA Gatekeeper

```
┌─────────────────────────────────────────────────────────────┐
│              OPA GATEKEEPER                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT IT IS:                                               │
│  • Policy engine for Kubernetes                            │
│  • Admission controller                                    │
│  • Uses Rego language for policies                         │
│                                                             │
│  USE CASES:                                                │
│  • Require labels on resources                             │
│  • Block privileged containers                             │
│  • Enforce resource limits                                 │
│  • Restrict registries                                     │
│  • Custom organizational policies                          │
│                                                             │
│  COMPONENTS:                                               │
│  ├── ConstraintTemplate - Define policy type              │
│  ├── Constraint - Apply policy with parameters            │
│  └── Gatekeeper controller - Enforce policies             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Kyverno

```
┌─────────────────────────────────────────────────────────────┐
│              KYVERNO                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT IT IS:                                               │
│  • Kubernetes-native policy engine                         │
│  • No new language (uses YAML)                            │
│  • Admission controller                                    │
│                                                             │
│  POLICY TYPES:                                             │
│  ├── Validate - Check and reject                          │
│  ├── Mutate - Automatically modify                        │
│  ├── Generate - Create new resources                      │
│  └── Verify Images - Signature verification               │
│                                                             │
│  ADVANTAGES:                                               │
│  • Familiar YAML syntax                                   │
│  • Kubernetes-native                                      │
│  • Easy to get started                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Kyverno Policy Example

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: disallow-privileged
spec:
  validationFailureAction: Enforce
  rules:
  - name: deny-privileged
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Privileged containers are not allowed"
      pattern:
        spec:
          containers:
          - securityContext:
              privileged: "!true"
```

---

## Sandboxed Runtimes

```
┌─────────────────────────────────────────────────────────────┐
│              SANDBOXED RUNTIME COMPARISON                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STANDARD RUNTIME (runc)                                   │
│  ├── Direct syscalls to host kernel                       │
│  ├── Fastest performance                                  │
│  ├── Kernel vulnerability = container escape              │
│  └── Use for: Trusted workloads                           │
│                                                             │
│  gVisor (runsc)                                           │
│  ├── User-space kernel (Sentry)                           │
│  ├── Intercepts and emulates syscalls                     │
│  ├── ~70% syscall coverage                                │
│  ├── Performance overhead (varies by workload)            │
│  └── Use for: Untrusted workloads, multi-tenant           │
│                                                             │
│  Kata Containers                                          │
│  ├── Lightweight VM per container                         │
│  ├── Separate kernel (not shared)                         │
│  ├── Hardware virtualization (KVM)                        │
│  ├── Higher overhead than gVisor                          │
│  └── Use for: Maximum isolation, compliance               │
│                                                             │
│  CHOOSING A RUNTIME:                                       │
│  Trusted internal workloads → runc                        │
│  Untrusted/multi-tenant → gVisor                         │
│  Maximum isolation → Kata                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### RuntimeClass Configuration

```yaml
# Define RuntimeClass
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc  # Handler name configured on nodes
---
# Use in Pod
apiVersion: v1
kind: Pod
metadata:
  name: sandboxed-pod
spec:
  runtimeClassName: gvisor  # Use gVisor
  containers:
  - name: app
    image: myapp:1.0
```

---

## Runtime Security Checklist

```
┌─────────────────────────────────────────────────────────────┐
│              RUNTIME SECURITY CHECKLIST                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SYSTEM CALL FILTERING                                     │
│  ☐ Enable seccomp (RuntimeDefault minimum)                 │
│  ☐ Custom profiles for sensitive workloads                 │
│  ☐ Test profiles don't break applications                  │
│                                                             │
│  MANDATORY ACCESS CONTROL                                  │
│  ☐ AppArmor or SELinux enabled on nodes                   │
│  ☐ Profiles applied to pods                                │
│  ☐ Start in complain mode, then enforce                    │
│                                                             │
│  CAPABILITIES                                              │
│  ☐ Drop all capabilities by default                        │
│  ☐ Add back only what's needed                             │
│  ☐ Never add CAP_SYS_ADMIN                                 │
│                                                             │
│  RUNTIME SELECTION                                         │
│  ☐ Consider sandboxed runtime for untrusted workloads      │
│  ☐ Define RuntimeClasses for different isolation levels    │
│                                                             │
│  POLICY ENFORCEMENT                                        │
│  ☐ Deploy policy engine (Kyverno/OPA)                     │
│  ☐ Enforce Pod Security Standards                          │
│  ☐ Block privileged/host namespace access                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Seccomp can block over 300 syscalls**. Most applications only need 50-100. Blocking the rest dramatically reduces attack surface.

- **gVisor implements its own network stack** (netstack). This means network-based kernel exploits don't affect gVisor containers.

- **AppArmor and SELinux are mutually exclusive**—a system uses one or the other, based on the distribution.

- **RuntimeDefault seccomp** became the default in Kubernetes 1.27, improving security for all new clusters automatically.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| seccomp: Unconfined | No syscall filtering | Use RuntimeDefault |
| Not dropping capabilities | Excess privileges | Drop ALL, add minimal |
| No AppArmor/SELinux | Missing MAC layer | Enable and apply profiles |
| Single runtime for all | Over/under isolation | Use RuntimeClasses |
| Not testing profiles | Breaks applications | Test in staging first |

---

## Quiz

1. **What does seccomp do?**
   <details>
   <summary>Answer</summary>
   Seccomp (Secure Computing Mode) filters which system calls a process can make. It allows you to define a whitelist or blacklist of syscalls, blocking dangerous ones like mount, ptrace, and reboot that could be used for container escape or privilege escalation.
   </details>

2. **What's the difference between AppArmor and SELinux?**
   <details>
   <summary>Answer</summary>
   Both provide Mandatory Access Control (MAC). AppArmor uses path-based rules and profiles per program (common on Ubuntu/Debian). SELinux uses label-based rules where every file and process has a security context (common on RHEL/CentOS). They're mutually exclusive—a system uses one or the other.
   </details>

3. **Why should you drop all capabilities and add back only what's needed?**
   <details>
   <summary>Answer</summary>
   Capabilities break root privileges into discrete units. By dropping all and adding back only required ones, you minimize what an attacker can do if they compromise the container. For example, a web server might only need NET_BIND_SERVICE to bind to port 80.
   </details>

4. **When would you use gVisor vs Kata Containers?**
   <details>
   <summary>Answer</summary>
   gVisor is good for untrusted workloads with moderate isolation needs—it has lower overhead but doesn't cover all syscalls. Kata Containers provides maximum isolation using VMs with separate kernels—better for compliance requirements or highly sensitive workloads but with more overhead.
   </details>

5. **What's the role of a RuntimeClass?**
   <details>
   <summary>Answer</summary>
   RuntimeClass allows you to select different container runtimes (like runc, runsc for gVisor, or kata for Kata Containers) for different pods. This lets you run trusted workloads on fast runc while running untrusted workloads on sandboxed runtimes.
   </details>

---

## Hands-On Exercise: Security Context Configuration

**Scenario**: Configure the most restrictive security context for a web application:

**Requirements:**
- Must run as non-root
- Should not be able to escalate privileges
- Read-only filesystem (with writable /tmp)
- Drop all capabilities except NET_BIND_SERVICE
- Use RuntimeDefault seccomp
- No access to host namespaces

**Create the secure pod spec:**

<details>
<summary>Secure Pod Configuration</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-webapp
spec:
  # Pod-level security settings
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault

  # Ensure no host access
  hostNetwork: false
  hostPID: false
  hostIPC: false

  containers:
  - name: webapp
    image: mywebapp:1.0
    ports:
    - containerPort: 8080

    securityContext:
      # Prevent privilege escalation
      allowPrivilegeEscalation: false
      privileged: false

      # Read-only root filesystem
      readOnlyRootFilesystem: true

      # Drop all capabilities, add only what's needed
      capabilities:
        drop:
          - ALL
        add:
          - NET_BIND_SERVICE

    # Volume mounts for writable directories
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: cache
      mountPath: /var/cache/nginx

    # Resource limits (defense against DoS)
    resources:
      limits:
        cpu: "500m"
        memory: "256Mi"
      requests:
        cpu: "100m"
        memory: "128Mi"

  # Temporary writable volumes
  volumes:
  - name: tmp
    emptyDir: {}
  - name: cache
    emptyDir: {}

  # Service account with no token
  serviceAccountName: webapp-sa
  automountServiceAccountToken: false
```

**Additional ServiceAccount:**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: webapp-sa
automountServiceAccountToken: false
```

**Key security features:**
1. Non-root execution (runAsNonRoot, runAsUser)
2. No privilege escalation (allowPrivilegeEscalation: false)
3. Read-only filesystem with emptyDir for temp
4. Minimal capabilities (only NET_BIND_SERVICE)
5. Seccomp RuntimeDefault profile
6. No host namespace access
7. No service account token mounted
8. Resource limits set

</details>

---

## Summary

Runtime security provides multiple defense layers:

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Syscall Filter** | Seccomp | Block dangerous system calls |
| **MAC** | AppArmor/SELinux | File, network, capability restrictions |
| **Capabilities** | Linux | Granular privilege control |
| **Sandboxing** | gVisor/Kata | Kernel isolation |
| **Policy** | Kyverno/OPA | Admission enforcement |

Key principles:
- Enable seccomp RuntimeDefault at minimum
- Use AppArmor/SELinux where available
- Drop all capabilities, add minimal
- Consider sandboxed runtimes for untrusted workloads
- Enforce policies at admission

---

## Next Module

[Module 5.4: Security Tooling](../module-5.4-security-tooling/) - Overview of security tools in the Kubernetes ecosystem.
