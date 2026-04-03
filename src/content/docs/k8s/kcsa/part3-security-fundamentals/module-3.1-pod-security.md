---
title: "Module 3.1: Pod Security"
slug: k8s/kcsa/part3-security-fundamentals/module-3.1-pod-security
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Core knowledge
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: [Module 2.4: PKI and Certificates](../part2-cluster-component-security/module-2.4-pki-certificates/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** SecurityContext settings to identify dangerous configurations (privileged, hostPID, root)
2. **Assess** the risk level of Pod Security Standards profiles: privileged, baseline, and restricted
3. **Explain** how Pod Security Admission enforces security standards at the namespace level
4. **Identify** pod specifications that enable container escape or privilege escalation

---

## Why This Module Matters

Pods are where your code runs. They're also where attackers try to gain access and escalate privileges. Pod security controls determine whether a container can escape to the host, access sensitive resources, or move laterally through your cluster.

Understanding SecurityContext and Pod Security Standards is essential for both the KCSA exam and securing real Kubernetes workloads.

---

## Pod Security Concepts

```
┌─────────────────────────────────────────────────────────────┐
│              POD SECURITY LAYERS                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  POD-LEVEL SETTINGS                                        │
│  Applied to all containers in the pod                      │
│  • runAsUser, runAsGroup, fsGroup                         │
│  • seccompProfile                                          │
│  • hostNetwork, hostPID, hostIPC                          │
│                                                             │
│  CONTAINER-LEVEL SETTINGS                                  │
│  Applied to specific containers                            │
│  • runAsUser, runAsGroup (overrides pod)                  │
│  • readOnlyRootFilesystem                                  │
│  • allowPrivilegeEscalation                               │
│  • capabilities                                            │
│  • privileged                                              │
│                                                             │
│  ADMISSION ENFORCEMENT                                     │
│  Prevents insecure pods from being created                 │
│  • Pod Security Standards (PSS)                           │
│  • Pod Security Admission (PSA)                           │
│  • Third-party (OPA Gatekeeper, Kyverno)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## SecurityContext

The SecurityContext defines privilege and access control settings:

### Container SecurityContext

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  containers:
  - name: app
    image: nginx:1.25
    securityContext:
      # USER SETTINGS
      runAsUser: 1000          # Run as non-root user
      runAsGroup: 1000         # Primary group
      runAsNonRoot: true       # Fail if image runs as root

      # FILESYSTEM
      readOnlyRootFilesystem: true  # Prevent writes

      # PRIVILEGE ESCALATION
      allowPrivilegeEscalation: false  # Block setuid/setgid
      privileged: false                 # Not privileged

      # CAPABILITIES
      capabilities:
        drop:
          - ALL                # Drop all capabilities
        add:
          - NET_BIND_SERVICE   # Add only what's needed

      # SECCOMP
      seccompProfile:
        type: RuntimeDefault   # Use container runtime's profile
```

### Pod-Level SecurityContext

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 2000           # Group for volume ownership
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: nginx:1.25
    # Container settings can override pod settings
```

### Key SecurityContext Fields

| Field | Purpose | Secure Setting |
|-------|---------|----------------|
| `runAsNonRoot` | Prevent running as root | `true` |
| `runAsUser` | Specific user ID | Non-zero (not root) |
| `readOnlyRootFilesystem` | Prevent filesystem writes | `true` |
| `allowPrivilegeEscalation` | Block setuid/setgid | `false` |
| `privileged` | Full host access | `false` |
| `capabilities.drop` | Remove Linux capabilities | `["ALL"]` |
| `seccompProfile` | System call filtering | `RuntimeDefault` |

---

## Linux Capabilities

Capabilities split root privileges into discrete units:

```
┌─────────────────────────────────────────────────────────────┐
│              LINUX CAPABILITIES                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TRADITIONAL MODEL:                                        │
│  • Root (UID 0) = all privileges                           │
│  • Non-root = limited privileges                           │
│                                                             │
│  CAPABILITIES MODEL:                                       │
│  • Privileges split into ~40 capabilities                  │
│  • Can grant specific capabilities without full root       │
│                                                             │
│  DANGEROUS CAPABILITIES (avoid granting):                  │
│  ├── CAP_SYS_ADMIN    - Almost root, too broad            │
│  ├── CAP_NET_ADMIN    - Network configuration             │
│  ├── CAP_SYS_PTRACE   - Debug any process                 │
│  ├── CAP_DAC_OVERRIDE - Bypass file permissions           │
│  └── CAP_SYS_RAWIO    - Direct I/O access                 │
│                                                             │
│  COMMONLY NEEDED CAPABILITIES:                             │
│  ├── CAP_NET_BIND_SERVICE - Bind to ports < 1024          │
│  ├── CAP_CHOWN           - Change file ownership          │
│  └── CAP_SETUID/SETGID   - Change user/group              │
│                                                             │
│  BEST PRACTICE:                                            │
│  capabilities:                                             │
│    drop: ["ALL"]           # Drop everything               │
│    add: ["NET_BIND_SERVICE"] # Add only what's needed      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Host Namespaces

Sharing host namespaces breaks container isolation:

```
┌─────────────────────────────────────────────────────────────┐
│              HOST NAMESPACE RISKS                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  hostPID: true                                             │
│  ├── Container sees ALL host processes                     │
│  ├── Can signal host processes (kill, ptrace)              │
│  └── Risk: Process manipulation, info disclosure           │
│                                                             │
│  hostNetwork: true                                         │
│  ├── Container uses host's network stack                   │
│  ├── Can bind to any host port                             │
│  ├── Sees all host network traffic                         │
│  └── Risk: Network eavesdropping, service impersonation   │
│                                                             │
│  hostIPC: true                                             │
│  ├── Container shares host IPC namespace                   │
│  ├── Can access host shared memory                         │
│  └── Risk: Data leakage, process interference             │
│                                                             │
│  SECURE DEFAULT: All false (isolated from host)           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Pod Security Standards (PSS)

Pod Security Standards define three security profiles:

```
┌─────────────────────────────────────────────────────────────┐
│              POD SECURITY STANDARDS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PRIVILEGED (Most permissive)                              │
│  ├── No restrictions                                       │
│  ├── Use for: Trusted system workloads, CNI, logging      │
│  └── Risk: Full host access possible                       │
│                                                             │
│  BASELINE (Moderate)                                       │
│  ├── Prevents known privilege escalations                  │
│  ├── Blocks: hostNetwork, hostPID, privileged             │
│  ├── Allows: root user, most capabilities                  │
│  └── Use for: Most applications                            │
│                                                             │
│  RESTRICTED (Most secure)                                  │
│  ├── Heavily restricted, follows hardening best practices │
│  ├── Requires: non-root, read-only fs, dropped caps       │
│  ├── Blocks: Almost everything dangerous                   │
│  └── Use for: Security-sensitive workloads                │
│                                                             │
│  RECOMMENDATION: Start with Restricted, relax if needed   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### What Each Standard Blocks

| Control | Privileged | Baseline | Restricted |
|---------|-----------|----------|------------|
| hostNetwork | Allowed | Blocked | Blocked |
| hostPID | Allowed | Blocked | Blocked |
| hostIPC | Allowed | Blocked | Blocked |
| privileged | Allowed | Blocked | Blocked |
| capabilities (dangerous) | Allowed | Blocked | Blocked |
| hostPath (sensitive) | Allowed | Blocked | Blocked |
| runAsRoot | Allowed | Allowed | Blocked |
| allowPrivilegeEscalation | Allowed | Allowed | Blocked |
| seccompProfile | Allowed | Allowed | Required |

---

## Pod Security Admission (PSA)

PSA is the built-in enforcement mechanism for Pod Security Standards:

### PSA Modes

```
┌─────────────────────────────────────────────────────────────┐
│              PSA ENFORCEMENT MODES                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ENFORCE                                                   │
│  • Blocks pods that violate the standard                   │
│  • Pod creation fails                                      │
│  • Use for: Production enforcement                         │
│                                                             │
│  AUDIT                                                     │
│  • Logs violations but allows pod creation                 │
│  • Records to audit log                                    │
│  • Use for: Discovering violations before enforcement      │
│                                                             │
│  WARN                                                      │
│  • Shows warning to user but allows pod creation           │
│  • Warning in API response                                 │
│  • Use for: Developer education                            │
│                                                             │
│  COMBINATION EXAMPLE:                                      │
│  • enforce: baseline (block dangerous)                     │
│  • warn: restricted (educate about best practices)         │
│  • audit: restricted (log for review)                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Configuring PSA

PSA is configured via namespace labels:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    # Enforce baseline, warn and audit on restricted
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest
```

---

## Privileged Containers

```
┌─────────────────────────────────────────────────────────────┐
│              PRIVILEGED CONTAINERS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  privileged: true GRANTS:                                  │
│  • All host devices (/dev/*)                               │
│  • All Linux capabilities                                  │
│  • Effectively root on the host                            │
│                                                             │
│  LEGITIMATE USES:                                          │
│  • CNI plugins (need network configuration)                │
│  • Device plugins (GPU access)                             │
│  • Some monitoring agents                                  │
│                                                             │
│  ATTACK SCENARIO:                                          │
│  1. Attacker compromises app in privileged container       │
│  2. Mounts host filesystem: mount /dev/sda1 /mnt          │
│  3. Reads /etc/shadow, SSH keys, etc.                     │
│  4. Writes malicious binaries to host                      │
│  5. Complete host compromise                               │
│                                                             │
│  MITIGATION:                                               │
│  • Almost never use privileged: true                       │
│  • If needed, use specific capabilities instead            │
│  • Enforce PSS to block privileged in most namespaces     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Seccomp Profiles

Seccomp filters which system calls a container can make:

```
┌─────────────────────────────────────────────────────────────┐
│              SECCOMP PROFILES                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PROFILE TYPES:                                            │
│                                                             │
│  Unconfined                                                │
│  • No syscall filtering                                    │
│  • Container can call any syscall                          │
│  • NOT RECOMMENDED                                         │
│                                                             │
│  RuntimeDefault                                            │
│  • Container runtime's default profile                     │
│  • Blocks dangerous syscalls (ptrace, reboot, etc.)       │
│  • RECOMMENDED for most workloads                          │
│                                                             │
│  Localhost                                                 │
│  • Custom profile on the node                              │
│  • Fine-grained control                                    │
│  • Used for specific hardening needs                       │
│                                                             │
│  CONFIGURATION:                                            │
│  securityContext:                                          │
│    seccompProfile:                                         │
│      type: RuntimeDefault   # Use runtime's profile        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Pod Security Admission replaced PodSecurityPolicy** (PSP) which was deprecated in 1.21 and removed in 1.25. PSA is simpler but less flexible.

- **Docker's default seccomp profile** blocks about 44 system calls out of ~300+. This provides meaningful protection with minimal compatibility impact.

- **The restricted PSS** is based on CIS Benchmark and real-world hardening practices. Following it significantly reduces attack surface.

- **allowPrivilegeEscalation: false** prevents setuid binaries from working. This is why some containers that work as root break with this setting.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Running as root | Higher privilege if compromised | runAsNonRoot: true |
| Not dropping capabilities | Container has more privileges than needed | capabilities.drop: ["ALL"] |
| privileged: true | Full host access | Use specific capabilities instead |
| Writable root filesystem | Attacker can persist changes | readOnlyRootFilesystem: true |
| No seccomp profile | All syscalls available | type: RuntimeDefault |

---

## Quiz

1. **What's the difference between runAsNonRoot and runAsUser?**
   <details>
   <summary>Answer</summary>
   runAsNonRoot is a boolean that makes the container fail to start if the image would run as root (UID 0). runAsUser explicitly sets the UID to run as. They work together - runAsUser: 1000 sets the UID, runAsNonRoot: true verifies it's not 0.
   </details>

2. **What does allowPrivilegeEscalation: false prevent?**
   <details>
   <summary>Answer</summary>
   It prevents processes from gaining more privileges than their parent, blocking setuid and setgid binaries from working. This stops common privilege escalation techniques.
   </details>

3. **Which Pod Security Standard is appropriate for most production applications?**
   <details>
   <summary>Answer</summary>
   Baseline for most applications (prevents known privilege escalations), Restricted for security-sensitive workloads. Start with Restricted and relax if needed.
   </details>

4. **What's the difference between PSA modes enforce, warn, and audit?**
   <details>
   <summary>Answer</summary>
   Enforce blocks non-compliant pods from being created. Warn allows the pod but shows a warning to the user. Audit allows the pod but logs the violation. You can use different modes at different levels.
   </details>

5. **Why is privileged: true dangerous?**
   <details>
   <summary>Answer</summary>
   It gives the container all Linux capabilities and access to all host devices. A compromised privileged container can mount the host filesystem, access all host resources, and effectively has root access to the host.
   </details>

---

## Hands-On Exercise: Security Analysis

**Scenario**: Analyze this pod specification and identify all security issues:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  containers:
  - name: app
    image: myapp:latest
    securityContext:
      runAsUser: 0
      privileged: true
      readOnlyRootFilesystem: false
      allowPrivilegeEscalation: true
  hostNetwork: true
  hostPID: true
```

**List the security issues and how to fix them:**

<details>
<summary>Security Issues and Fixes</summary>

| Issue | Risk | Fix |
|-------|------|-----|
| `runAsUser: 0` | Running as root | `runAsUser: 1000`, `runAsNonRoot: true` |
| `privileged: true` | Full host access | `privileged: false` |
| `readOnlyRootFilesystem: false` | Attacker can write to filesystem | `readOnlyRootFilesystem: true` |
| `allowPrivilegeEscalation: true` | Setuid exploits possible | `allowPrivilegeEscalation: false` |
| `hostNetwork: true` | Uses host network, can sniff traffic | Remove or set to false |
| `hostPID: true` | Can see/kill host processes | Remove or set to false |
| `image: myapp:latest` | Mutable tag, unpredictable | Use immutable tag with digest |
| Missing `capabilities` | Default capabilities available | `capabilities.drop: ["ALL"]` |
| Missing `seccompProfile` | No syscall filtering | `seccompProfile.type: RuntimeDefault` |

**Secure version:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  containers:
  - name: app
    image: myapp@sha256:abc123...
    securityContext:
      runAsUser: 1000
      runAsGroup: 1000
      runAsNonRoot: true
      privileged: false
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      seccompProfile:
        type: RuntimeDefault
```

</details>

---

## Summary

Pod security is about restricting what containers can do:

| Control | Purpose | Secure Setting |
|---------|---------|----------------|
| **runAsNonRoot** | Prevent root user | `true` |
| **readOnlyRootFilesystem** | Prevent writes | `true` |
| **allowPrivilegeEscalation** | Block setuid | `false` |
| **privileged** | Block host access | `false` |
| **capabilities** | Limit privileges | `drop: ["ALL"]` |
| **seccompProfile** | Filter syscalls | `RuntimeDefault` |
| **hostNetwork/PID/IPC** | Block host sharing | `false` or omit |

Pod Security Standards:
- **Privileged**: No restrictions (system workloads)
- **Baseline**: Prevents known privilege escalations
- **Restricted**: Heavily hardened, best practice

---

## Next Module

[Module 3.2: RBAC Fundamentals](../module-3.2-rbac/) - Role-based access control for Kubernetes authorization.
