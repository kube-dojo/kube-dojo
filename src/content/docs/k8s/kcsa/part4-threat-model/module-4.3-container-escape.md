---
title: "Module 4.3: Container Escape"
slug: k8s/kcsa/part4-threat-model/module-4.3-container-escape
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]` - Threat awareness
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 4.2: Common Vulnerabilities](../module-4.2-vulnerabilities/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Identify** configurations that enable container escape: privileged mode, hostPID, hostNetwork, writable hostPath
2. **Assess** the blast radius of a container escape based on node-level access and RBAC
3. **Evaluate** prevention strategies: security contexts, PSA enforcement, and runtime sandboxing
4. **Explain** real-world container escape scenarios and the defense layers that block them

---

## Why This Module Matters

Container escape—breaking out of a container to access the host—is the most severe container security failure. Understanding which configurations make escape possible helps you build secure defaults and recognize dangerous settings before they reach production.

KCSA tests your ability to identify configurations that enable container escape and understand prevention strategies. You don't need to know specific exploitation commands—that's [CKS territory](../../cks/)—but you must recognize the risky settings and know how to prevent them.

---

## What is Container Escape?

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER ESCAPE DEFINED                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  NORMAL CONTAINER ISOLATION:                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  HOST                                               │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │   │
│  │  │ Container A │ │ Container B │ │ Container C │   │   │
│  │  │ (isolated)  │ │ (isolated)  │ │ (isolated)  │   │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│  Containers can't see or affect host or each other         │
│                                                             │
│  CONTAINER ESCAPE:                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  HOST ← COMPROMISED                                 │   │
│  │  ┌─────────────┐                                    │   │
│  │  │ Container A │──→ ESCAPE ──→ Full host access    │   │
│  │  │ (attacker)  │                                    │   │
│  │  └─────────────┘                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│  Attacker breaks isolation, gains host access              │
│                                                             │
│  IMPACT: Node compromise, lateral movement, cluster        │
│  compromise possible                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Risk Factors: What Makes Escape Possible?

### 1. Privileged Containers

```
┌─────────────────────────────────────────────────────────────┐
│              PRIVILEGED CONTAINER RISK                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONFIGURATION:                                            │
│  securityContext:                                          │
│    privileged: true                                        │
│                                                             │
│  WHAT IT GRANTS:                                           │
│  • All Linux capabilities                                  │
│  • Access to all host devices (/dev/*)                     │
│  • No seccomp filtering                                    │
│  • SELinux/AppArmor bypassed                              │
│                                                             │
│  WHY IT'S DANGEROUS:                                       │
│  An attacker inside a privileged container can mount the   │
│  host filesystem, access sensitive host files, and modify  │
│  host configurations—effectively gaining full host control │
│  with minimal effort.                                      │
│                                                             │
│  TRIVIAL ESCAPE - Never use privileged: true              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Stop and think**: A container running as root inside the container does NOT necessarily have root access on the host. What determines the boundary between container root and host root?

### 2. Host Namespace Sharing

```
┌─────────────────────────────────────────────────────────────┐
│              HOST NAMESPACE RISKS                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  hostPID: true                                             │
│  ├── Container sees all host processes                     │
│  ├── Can send signals to host processes                    │
│  └── An attacker could inspect or interact with host       │
│      processes, potentially gaining host-level access      │
│                                                             │
│  hostNetwork: true                                         │
│  ├── Container uses host's network stack                   │
│  ├── Can bind to any host port                             │
│  └── Can sniff all host network traffic                    │
│                                                             │
│  hostIPC: true                                             │
│  ├── Access to host shared memory                          │
│  └── Can communicate with host processes via IPC           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. Dangerous Volume Mounts

```
┌─────────────────────────────────────────────────────────────┐
│              HOST PATH RISKS                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DANGEROUS MOUNTS:                                         │
│                                                             │
│  hostPath: { path: / }                                     │
│  └── Full host filesystem access                           │
│                                                             │
│  hostPath: { path: /etc }                                  │
│  └── Can read/modify host credentials and configuration   │
│                                                             │
│  hostPath: { path: /var/run/docker.sock }                  │
│  └── Control Docker daemon → create privileged containers  │
│                                                             │
│  hostPath: { path: /var/log }                              │
│  └── Read logs, potential sensitive data                   │
│                                                             │
│  hostPath: { path: /root/.ssh }                            │
│  └── Steal SSH keys                                        │
│                                                             │
│  WHY DOCKER SOCKET IS ESPECIALLY DANGEROUS:                │
│  Access to the Docker socket gives full control over the   │
│  container runtime. An attacker could use it to launch     │
│  new privileged containers with host filesystem access,    │
│  effectively escaping to the host.                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. Dangerous Capabilities

```
┌─────────────────────────────────────────────────────────────┐
│              DANGEROUS CAPABILITIES                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CAP_SYS_ADMIN                                             │
│  ├── Nearly equivalent to root                             │
│  ├── Allows mounting filesystems                           │
│  └── Can be used to break container isolation              │
│                                                             │
│  CAP_SYS_PTRACE                                            │
│  ├── Allows debugging processes                            │
│  └── Combined with hostPID, can interact with host         │
│      processes in dangerous ways                           │
│                                                             │
│  CAP_NET_ADMIN                                             │
│  ├── Configure network interfaces                          │
│  └── Capture traffic, modify routing                       │
│                                                             │
│  CAP_DAC_READ_SEARCH                                       │
│  ├── Bypass file read permission checks                    │
│  └── Read any file regardless of ownership                 │
│                                                             │
│  CAP_DAC_OVERRIDE                                          │
│  ├── Bypass all file permission checks                     │
│  └── Write to any file regardless of ownership             │
│                                                             │
│  BEST PRACTICE: Drop ALL capabilities, then add back only  │
│  the specific ones your application needs.                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5. Kernel Vulnerabilities

```
┌─────────────────────────────────────────────────────────────┐
│              KERNEL EXPLOIT ESCAPE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONCEPT:                                                  │
│  • Containers share the host kernel                        │
│  • Kernel vulnerability = escape opportunity               │
│  • Works even with "secure" container settings             │
│                                                             │
│  EXAMPLES:                                                 │
│  ├── Dirty COW (CVE-2016-5195)                            │
│  ├── Dirty Pipe (CVE-2022-0847)                           │
│  └── Various privilege escalation CVEs                     │
│                                                             │
│  MITIGATION:                                               │
│  • Keep kernel updated                                     │
│  • Use seccomp to limit syscalls                          │
│  • Consider sandboxed runtimes (gVisor, Kata)             │
│  • Sandboxed runtimes use different kernel or intercept   │
│    syscalls, reducing kernel attack surface               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

> **Pause and predict**: If a container has `hostPath: { path: /var/run/docker.sock }` mounted but runs as non-root with all capabilities dropped, can an attacker still escape to the host? Why or why not?

## Prevention Strategies

### Pod Security Standards

```
┌─────────────────────────────────────────────────────────────┐
│              PSS PREVENTS ESCAPE                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BASELINE STANDARD BLOCKS:                                 │
│  ├── privileged: true                                      │
│  ├── hostNetwork: true                                     │
│  ├── hostPID: true                                         │
│  ├── hostIPC: true                                         │
│  └── Sensitive hostPath mounts                             │
│                                                             │
│  RESTRICTED STANDARD ADDITIONALLY:                         │
│  ├── Requires non-root                                     │
│  ├── Requires seccomp profile                              │
│  ├── Drops all capabilities                                │
│  └── Requires read-only root filesystem                    │
│                                                             │
│  ENABLE IN NAMESPACE:                                      │
│  kubectl label ns production \                             │
│    pod-security.kubernetes.io/enforce=restricted           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER ESCAPE PREVENTION                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LAYER 1: POD SECURITY                                     │
│  ├── Pod Security Standards (Restricted)                   │
│  ├── No privileged containers                              │
│  ├── No host namespace sharing                             │
│  ├── No dangerous hostPath mounts                          │
│  └── Drop all capabilities                                 │
│                                                             │
│  LAYER 2: RUNTIME SECURITY                                 │
│  ├── Seccomp profiles (RuntimeDefault minimum)             │
│  ├── AppArmor/SELinux profiles                             │
│  ├── Read-only root filesystem                             │
│  └── Run as non-root user                                  │
│                                                             │
│  LAYER 3: RUNTIME ISOLATION                                │
│  ├── Consider gVisor for untrusted workloads              │
│  ├── Consider Kata Containers for strong isolation         │
│  └── Runtime classes for different security levels         │
│                                                             │
│  LAYER 4: MONITORING                                       │
│  ├── Runtime security (Falco)                              │
│  ├── File integrity monitoring                             │
│  └── Anomaly detection                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Sandboxed Runtimes

```
┌─────────────────────────────────────────────────────────────┐
│              SANDBOXED RUNTIME OPTIONS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  gVisor (runsc)                                            │
│  ├── User-space kernel                                     │
│  ├── Intercepts and emulates syscalls                      │
│  ├── Container doesn't directly touch host kernel          │
│  ├── Performance overhead                                  │
│  └── Good for: Untrusted workloads, multi-tenant           │
│                                                             │
│  Kata Containers                                           │
│  ├── Lightweight VM per container                          │
│  ├── Separate kernel from host                             │
│  ├── Hardware virtualization isolation                     │
│  ├── More overhead than gVisor                             │
│  └── Good for: Maximum isolation, compliance               │
│                                                             │
│  USING RUNTIME CLASSES:                                    │
│  apiVersion: node.k8s.io/v1                                │
│  kind: RuntimeClass                                        │
│  metadata:                                                 │
│    name: gvisor                                            │
│  handler: runsc                                            │
│  ---                                                       │
│  spec:                                                     │
│    runtimeClassName: gvisor  # Use in pod spec            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Most container escapes are misconfigurations**, not zero-days. Proper configuration prevents most escape scenarios.

- **Docker socket mount** is one of the most common escape vectors. It gives an attacker full control over the container runtime, making it trivial to compromise the host.

- **gVisor intercepts over 200 syscalls** and implements them in user-space, dramatically reducing kernel attack surface.

- **Kata Containers** use the same hypervisor technology (QEMU/KVM) as virtual machines, providing VM-level isolation for containers.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| privileged: true for convenience | Trivial escape | Use specific capabilities |
| Mounting Docker socket | Container controls all containers | Use alternatives |
| hostPath to sensitive dirs | Direct host access | Use PV/PVC instead |
| Not enforcing PSS | Allows dangerous configs | Enable PSS in namespaces |
| Running as root | Higher privilege post-exploit | runAsNonRoot: true |

---

## Quiz

1. **A security review finds a debugging pod in production with `privileged: true`, `hostPID: true`, and a `hostPath` mount to `/`. The ops team says "it's only used during incidents." Explain the risk even if the pod is only deployed temporarily, and propose a safer alternative for production debugging.**
   <details>
   <summary>Answer</summary>
   Even temporary privileged pods are dangerous: the time window of exposure is a risk (an attacker who compromises any other pod during that time can pivot to the debugging pod), the pod's ServiceAccount token grants API access, and if the pod spec is stored in a manifest or Helm chart, anyone with access can deploy it. With privileged + hostPID + hostPath:/, an attacker has trivial full host access. Safer alternative: use `kubectl debug` with ephemeral containers (requires no privileged pod spec), or create a dedicated debugging namespace with time-limited RBAC access that requires approval. If host access is truly needed, use a minimal set of capabilities (not full privileged mode) and limit the hostPath to the specific directory needed.
   </details>

2. **A container image mounts `/var/run/docker.sock` as a hostPath volume but runs as non-root (UID 1000) with all capabilities dropped. An attacker compromises the application. Can they still escape to the host through the Docker socket?**
   <details>
   <summary>Answer</summary>
   Yes, likely. The Docker socket is a UNIX socket that grants full control over the container runtime. If the socket's file permissions allow the container's UID to access it (which is common), the attacker can use the Docker API to create a new privileged container that mounts the host filesystem — effectively escaping to the host through a two-step process. Dropping capabilities and running non-root don't protect against this because the escape happens through the Docker API, not through Linux kernel mechanisms. This is why Docker socket mounts are one of the most dangerous configurations — they bypass nearly all container security hardening.
   </details>

3. **Your cluster runs standard containerd runtime. A kernel vulnerability (like Dirty Pipe, CVE-2022-0847) is announced. All your containers run non-root with dropped capabilities, seccomp RuntimeDefault, and read-only filesystems. Are you still vulnerable, and what additional defense could help?**
   <details>
   <summary>Answer</summary>
   You are still potentially vulnerable. Kernel vulnerabilities bypass all container security settings because containers share the host kernel — namespaces, cgroups, seccomp, and capabilities are all kernel features that a kernel exploit can circumvent. Seccomp helps if the exploit requires a syscall that's blocked by the RuntimeDefault profile, but sophisticated kernel exploits often use allowed syscalls. Additional defense: sandboxed runtimes (gVisor or Kata Containers) provide protection because they don't share the host kernel directly. gVisor intercepts syscalls in user-space, so the kernel vulnerability isn't reachable. Kata Containers use a separate VM kernel. For high-security workloads, these are the only reliable defense against kernel zero-days.
   </details>

4. **A pod has `hostNetwork: true` but no other dangerous settings (non-root, no capabilities, read-only filesystem). The team says it's needed for a network monitoring agent. What specific escape-adjacent risks does `hostNetwork` alone introduce?**
   <details>
   <summary>Answer</summary>
   hostNetwork alone (without privileged/hostPID) doesn't enable direct container escape, but it significantly expands the attack surface: the pod can bind to any port on the node (potentially impersonating the kubelet or other services), sniff all network traffic on the node, access services listening on localhost (kubelet health endpoints, cloud metadata service at 169.254.169.254), bypass all NetworkPolicies (which only apply to pod-network traffic), and communicate with any endpoint without egress restrictions. If combined with a code vulnerability, these capabilities dramatically increase the attacker's ability to move laterally. The network monitoring use case is legitimate, but should use a dedicated namespace with strict RBAC and audit logging.
   </details>

5. **You enforce the Restricted Pod Security Standard across all production namespaces. A new third-party monitoring tool requires `privileged: true` to function. The vendor says there's no alternative. How would you handle this without relaxing security for the entire production environment?**
   <details>
   <summary>Answer</summary>
   Never relax the production namespace PSS. Instead: (1) Create a dedicated `monitoring-system` namespace with Privileged PSS — isolate the privileged workload away from application pods; (2) Apply strict NetworkPolicies so the monitoring namespace can only reach the specific ports it needs to scrape; (3) Use a dedicated ServiceAccount with minimal RBAC; (4) Enable enhanced audit logging for all actions in this namespace; (5) Deploy runtime monitoring (Falco) with extra scrutiny on this namespace; (6) Evaluate alternatives — many modern monitoring tools (Prometheus node-exporter, Tetragon) don't actually need privileged mode. The vendor claim should be challenged: what specific capability do they need? Often it's a specific capability (NET_ADMIN, SYS_PTRACE) rather than full privileged mode.
   </details>

---

## Hands-On Exercise: Escape Path Analysis

**Scenario**: Analyze this pod specification and identify escape paths:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: risky-pod
spec:
  hostPID: true
  containers:
  - name: app
    image: ubuntu:20.04
    securityContext:
      capabilities:
        add:
        - SYS_ADMIN
        - SYS_PTRACE
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run/docker.sock
    - name: host-root
      mountPath: /host
  volumes:
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
  - name: host-root
    hostPath:
      path: /
```

**Tasks:**
1. Identify all the escape risk factors in this pod spec
2. Explain why each one is dangerous
3. Write a fixed version that follows the Restricted Pod Security Standard

<details>
<summary>Risk Factors</summary>

This pod has **multiple** escape risk factors:

**1. Docker Socket Mount** (`/var/run/docker.sock`)
- Gives full control over the container runtime
- An attacker could launch new privileged containers with host access

**2. Host Root Filesystem Mount** (`/` mounted to `/host`)
- Direct read/write access to the entire host filesystem
- Credentials, configuration, and SSH keys are all exposed

**3. hostPID + CAP_SYS_PTRACE**
- Container can see all host processes and interact with them
- Could be used to inspect host process memory or gain host access

**4. hostPID + CAP_SYS_ADMIN**
- Combined with host PID visibility, allows namespace manipulation
- Nearly equivalent to running directly on the host

**Prevention**: Remove ALL of these settings. Enforce the Restricted Pod Security Standard.

</details>

<details>
<summary>Fixed Pod Spec</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  # No hostPID, hostNetwork, or hostIPC
  containers:
  - name: app
    image: ubuntu:20.04
    securityContext:
      runAsNonRoot: true
      runAsUser: 1000
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
      seccompProfile:
        type: RuntimeDefault
    # No hostPath volumes — use PVCs if storage is needed
```

</details>

> **Want to learn hands-on exploitation and security testing techniques?** See the [CKS track](../../cks/) for offensive security labs.

---

## Summary

Container escape breaks the fundamental isolation promise:

| Escape Vector | Configuration | Prevention |
|--------------|---------------|------------|
| Privileged | `privileged: true` | Never use in production |
| Host namespaces | `hostPID/Network/IPC` | Block via PSS |
| Host paths | `hostPath: /` | Use PV/PVC instead |
| Capabilities | `CAP_SYS_ADMIN` | Drop all, add minimal |
| Kernel exploits | Shared kernel | Sandboxed runtimes |

Defense strategy:
- Enforce Pod Security Standards (Baseline minimum, Restricted preferred)
- Use seccomp and AppArmor/SELinux
- Consider sandboxed runtimes for untrusted workloads
- Monitor for escape attempts with Falco

---

## Next Module

[Module 4.4: Supply Chain Threats](../module-4.4-supply-chain/) - Understanding and mitigating software supply chain risks.
