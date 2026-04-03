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

> **Stop and think**: Seccomp filters system calls, AppArmor restricts file/network access, and capabilities limit root privileges. If you could only enable ONE of these for all pods, which would provide the broadest security improvement and why?

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

> **Pause and predict**: Your cluster runs both trusted internal microservices and untrusted third-party plugins. All currently use the default runc runtime. What would change if you assigned the plugins to a gVisor RuntimeClass?

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

1. **After enabling seccomp RuntimeDefault profile on all pods, an application that was working perfectly starts failing with "operation not permitted" errors. The application uses `ptrace` for debugging child processes. How would you resolve this without disabling seccomp entirely?**
   <details>
   <summary>Answer</summary>
   The RuntimeDefault seccomp profile blocks `ptrace` because it's a dangerous syscall used in container escape techniques. Resolution: create a custom seccomp profile (Localhost type) that starts with the RuntimeDefault allowed syscalls and adds `ptrace` specifically for this application. Apply it only to this pod using `seccompProfile: { type: Localhost, localhostProfile: "profiles/debug-app.json" }`. This follows least privilege — the specific pod gets the specific syscall it needs, while all other pods remain on RuntimeDefault. Additionally, consider whether the application truly needs ptrace in production, or if it's a development-only requirement that should be disabled in production builds.
   </details>

2. **Your cluster runs on Ubuntu nodes (AppArmor available) and you need to restrict a container from accessing `/etc/shadow` and making raw network connections. Would seccomp or AppArmor be more appropriate for these specific restrictions?**
   <details>
   <summary>Answer</summary>
   AppArmor is more appropriate for these specific restrictions. Seccomp operates at the syscall level — it can block the `open` syscall entirely, but cannot distinguish between opening `/etc/shadow` vs. opening `/var/log/app.log`. AppArmor operates at the path level — you can write `deny /etc/shadow rw` to block that specific file while allowing other file access. Similarly, AppArmor's `deny network raw` blocks raw sockets specifically while allowing TCP/UDP. Seccomp and AppArmor are complementary: seccomp provides broad syscall filtering, AppArmor provides fine-grained file and network path restrictions. Use both for defense in depth.
   </details>

3. **A multi-tenant SaaS platform runs customer-provided code in containers. The platform team uses runc (standard runtime) with strict seccomp profiles and dropped capabilities. A security consultant recommends switching to gVisor. What specific threat does gVisor mitigate that seccomp+capabilities cannot?**
   <details>
   <summary>Answer</summary>
   Kernel vulnerabilities. With runc, all containers share the host kernel. A kernel zero-day (like Dirty Pipe or Dirty COW) allows container escape regardless of seccomp profiles or capability restrictions — these are kernel features that the exploit bypasses. gVisor runs a user-space kernel (Sentry) that intercepts syscalls before they reach the host kernel, so kernel vulnerabilities aren't directly exploitable. The trade-off: gVisor has performance overhead (varies by workload, typically 5-50%) and doesn't support all syscalls (~70% coverage). For a multi-tenant platform running untrusted customer code, the kernel isolation justifies the performance cost — a single tenant's container escape would compromise all tenants on that node.
   </details>

4. **A Kyverno policy blocks all pods without `seccompProfile: RuntimeDefault`. Your cluster also has OPA/Gatekeeper installed for other policies. A developer asks: "Why do we need both Kyverno and Gatekeeper? Isn't that redundant?" How would you respond?**
   <details>
   <summary>Answer</summary>
   Having both is defense in depth at the admission layer, but it introduces operational complexity. The question of whether to use both depends on context: if Kyverno handles pod security policies and Gatekeeper handles organizational policies (labeling requirements, resource naming), they serve different purposes and aren't redundant. If they enforce overlapping policies, you risk conflicts, harder debugging, and doubled maintenance. The better question is: what happens if one fails? If Kyverno's webhook goes down, does Gatekeeper still catch the violation? If so, the overlap provides resilience. Best practice: use one primary policy engine consistently, and if using a second, ensure clear responsibility boundaries (Kyverno for security, Gatekeeper for governance, for example).
   </details>

5. **You need to design a runtime security strategy for three workload tiers: (1) public-facing web servers, (2) internal microservices processing PII, and (3) batch jobs running third-party data transformation scripts. What combination of runtime, seccomp, capabilities, and monitoring would you assign to each tier?**
   <details>
   <summary>Answer</summary>
   Tier 1 (web servers): runc runtime, seccomp RuntimeDefault, drop all capabilities except NET_BIND_SERVICE, AppArmor profile restricting file access to web content only, Falco monitoring for shell spawns and unexpected network connections. Tier 2 (PII microservices): runc runtime, custom seccomp profile (tighter than RuntimeDefault — block everything the app doesn't need), drop ALL capabilities, AppArmor with strict file and network restrictions, Falco with enhanced rules for sensitive data access, egress NetworkPolicies restricting data flow. Tier 3 (third-party scripts): gVisor runtime (untrusted code needs kernel isolation), strictest seccomp profile possible, drop ALL capabilities, dedicated namespace with Privileged PSS exemption only for gVisor's needs, intensive Falco monitoring, strict egress controls to prevent data exfiltration. Each tier's controls match its threat level — higher risk workloads get stronger isolation.
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
