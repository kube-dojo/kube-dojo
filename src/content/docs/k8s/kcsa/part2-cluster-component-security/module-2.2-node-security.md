---
title: "Module 2.2: Node Security"
slug: k8s/kcsa/part2-cluster-component-security/module-2.2-node-security
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Core knowledge
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 2.1: Control Plane Security](../module-2.1-control-plane-security/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Assess** the risk of privileged containers and host namespace access on worker nodes
2. **Evaluate** kubelet security settings including authentication, authorization, and read-only ports
3. **Identify** node-level attack vectors: exposed kubelet API, writable hostPath, kernel exploits
4. **Explain** node hardening strategies including minimal OS images and automatic patching

---

## Why This Module Matters

Worker nodes run your actual workloads. They have direct access to your containers and sensitive data. A compromised node means compromised pods—and potentially the entire cluster if the attacker can escalate from node to control plane.

Understanding node security helps you assess the risk of privileged containers and node-level attacks.

---

## Node Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES NODE                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    KUBELET                           │   │
│  │  • Node agent                                       │   │
│  │  • Manages pod lifecycle                            │   │
│  │  • Communicates with API server                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              CONTAINER RUNTIME                       │   │
│  │  containerd, CRI-O                                  │   │
│  │  • Actually runs containers                         │   │
│  │  • Pulls images                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │  CONTAINER  │ │  CONTAINER  │ │     CONTAINER       │   │
│  │   Pod A     │ │   Pod B     │ │      Pod C          │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   KUBE-PROXY                         │   │
│  │  • Network rules (iptables/IPVS)                    │   │
│  │  • Service routing                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Kubelet Security

The kubelet is the most security-critical component on a node.

### Kubelet API

The kubelet exposes an API that can be dangerous if exposed:

```
┌─────────────────────────────────────────────────────────────┐
│              KUBELET API SECURITY                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  KUBELET API CAPABILITIES (if exposed)                     │
│  • Execute commands in containers                          │
│  • Read container logs                                     │
│  • Port-forward to containers                              │
│  • View pods on the node                                   │
│                                                             │
│  DANGEROUS ENDPOINTS                                        │
│  • /exec - Execute arbitrary commands                      │
│  • /run - Run commands in containers                       │
│  • /pods - List all pods                                   │
│  • /logs - Read container logs                             │
│                                                             │
│  ATTACK SCENARIO                                            │
│  1. Attacker finds exposed kubelet (port 10250)            │
│  2. Connects without authentication                        │
│  3. Executes into any container on that node               │
│  4. Steals secrets, pivots to other systems                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Kubelet Security Configuration

| Flag | Purpose | Secure Setting |
|------|---------|----------------|
| `--anonymous-auth` | Allow anonymous requests | `false` |
| `--authorization-mode` | How to authorize | `Webhook` (checks with API server) |
| `--client-ca-file` | CA for client certs | Set to cluster CA |
| `--read-only-port` | Read-only API port | `0` (disabled) |
| `--protect-kernel-defaults` | Protect kernel settings | `true` |
| `--hostname-override` | Override hostname | Avoid (can bypass authorization) |

```yaml
# Example kubelet configuration (kubelet-config.yaml)
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authentication:
  anonymous:
    enabled: false
  webhook:
    enabled: true
authorization:
  mode: Webhook
readOnlyPort: 0
protectKernelDefaults: true
```

---

## Container Runtime Security

The container runtime (containerd, CRI-O) is responsible for actual container isolation.

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER RUNTIME ISOLATION                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LINUX ISOLATION MECHANISMS                                │
│                                                             │
│  NAMESPACES (Process isolation)                            │
│  ├── pid    - Process IDs                                  │
│  ├── net    - Network stack                                │
│  ├── mnt    - Mount points                                 │
│  ├── uts    - Hostname                                     │
│  ├── ipc    - Inter-process communication                  │
│  ├── user   - User/group IDs                               │
│  └── cgroup - Cgroup membership                            │
│                                                             │
│  CGROUPS (Resource limits)                                 │
│  ├── CPU limits                                            │
│  ├── Memory limits                                         │
│  └── Block I/O limits                                      │
│                                                             │
│  SECURITY MODULES                                          │
│  ├── seccomp  - System call filtering                      │
│  ├── AppArmor - Mandatory access control (Ubuntu/Debian)   │
│  └── SELinux  - Mandatory access control (RHEL/CentOS)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Runtime Classes

Kubernetes supports different runtime classes for stronger isolation:

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER RUNTIME OPTIONS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STANDARD RUNTIMES                                         │
│  ├── containerd (default)                                  │
│  └── CRI-O                                                 │
│  Good isolation, shares kernel with host                   │
│                                                             │
│  SANDBOXED RUNTIMES (Stronger isolation)                   │
│  ├── gVisor (runsc)                                        │
│  │   └── User-space kernel, intercepts syscalls            │
│  │                                                          │
│  └── Kata Containers                                       │
│      └── Lightweight VMs, separate kernel                  │
│                                                             │
│  Use sandboxed runtimes for:                               │
│  • Untrusted workloads                                     │
│  • Multi-tenant environments                               │
│  • Sensitive data processing                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Node-Level Attacks

### Container Escape

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER ESCAPE VECTORS                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MISCONFIGURATION-BASED                                    │
│                                                             │
│  Privileged containers                                     │
│  ├── privileged: true                                      │
│  ├── Full access to host devices                           │
│  └── Can mount host filesystem, load kernel modules        │
│                                                             │
│  Host namespaces                                           │
│  ├── hostPID: true - See host processes                    │
│  ├── hostNetwork: true - Use host network                  │
│  └── hostIPC: true - Share host IPC                        │
│                                                             │
│  Host path mounts                                          │
│  ├── Mount sensitive paths (/, /etc, /var/run/docker.sock)│
│  └── Can read/write host filesystem                        │
│                                                             │
│  VULNERABILITY-BASED                                        │
│                                                             │
│  Runtime vulnerabilities                                   │
│  ├── CVE-2019-5736 (runc)                                  │
│  └── CVE-2020-15257 (containerd)                           │
│                                                             │
│  Kernel vulnerabilities                                    │
│  └── Privilege escalation through kernel exploits          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Node Compromise Impact

```
┌─────────────────────────────────────────────────────────────┐
│              NODE COMPROMISE IMPACT                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  IF A NODE IS COMPROMISED, ATTACKER CAN:                   │
│                                                             │
│  ON THAT NODE                                              │
│  ├── Access all containers on the node                     │
│  ├── Read secrets mounted in pods                          │
│  ├── Impersonate any pod's service account                 │
│  ├── Access node's kubelet credentials                     │
│  └── Intercept pod network traffic                         │
│                                                             │
│  WITH NODE KUBELET CREDENTIALS                             │
│  ├── Query API server for node's pods                      │
│  ├── Cannot (with Node authz) access other nodes' data     │
│  └── Limited blast radius if Node authz mode is enabled    │
│                                                             │
│  DEFENSE: Node authorization mode limits what kubelet      │
│  credentials can access to resources for that node only    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Node Security Best Practices

### Operating System Hardening

```
┌─────────────────────────────────────────────────────────────┐
│              NODE OS HARDENING                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MINIMIZE ATTACK SURFACE                                   │
│  ├── Use minimal OS (Bottlerocket, Flatcar, Talos)         │
│  ├── Remove unnecessary packages                           │
│  ├── Disable unnecessary services                          │
│  └── Use immutable infrastructure                          │
│                                                             │
│  KEEP UPDATED                                              │
│  ├── Regular security patches                              │
│  ├── Automated patching where possible                     │
│  └── Container runtime updates                             │
│                                                             │
│  RESTRICT ACCESS                                           │
│  ├── Disable SSH if possible                               │
│  ├── If SSH needed, key-only authentication               │
│  ├── Use bastion hosts                                     │
│  └── Audit all node access                                 │
│                                                             │
│  ENABLE SECURITY FEATURES                                  │
│  ├── SELinux or AppArmor enforcing mode                   │
│  ├── Seccomp default profile                              │
│  └── Kernel parameter hardening                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Minimal Node Operating Systems

| OS | Description |
|------|-------------|
| **Bottlerocket** | AWS-developed, purpose-built for containers |
| **Flatcar Container Linux** | CoreOS successor, minimal and immutable |
| **Talos** | API-driven, no SSH, fully immutable |
| **Container-Optimized OS** | Google's minimal container host |

Benefits of minimal OS:
- Smaller attack surface
- Faster patching
- Immutable (changes require rebuild)
- Designed for container workloads

---

## Did You Know?

- **The kubelet read-only port (10255)** was historically used for debugging but exposed pod information without authentication. It's now disabled by default but worth checking in older clusters.

- **Container escape vulnerabilities** are regularly discovered. CVE-2019-5736 in runc allowed a container to overwrite the host runc binary and gain root access.

- **gVisor** was developed by Google specifically because they needed stronger isolation for their multi-tenant Cloud Run service.

- **Node authorization mode** was introduced in Kubernetes 1.7 specifically to limit the blast radius of a compromised node.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Kubelet anonymous auth enabled | Anyone can control pods on node | Disable anonymous auth |
| Read-only port exposed | Pod information disclosed | Set readOnlyPort=0 |
| Not patching nodes | Known vulnerabilities exploitable | Regular update process |
| SSH keys spread everywhere | Hard to revoke, over-privileged | Bastion host, audit logging |
| Standard runtime for untrusted workloads | Container escape possible | Use sandboxed runtime |

---

## Quiz

1. **What is the kubelet's role in node security?**
   <details>
   <summary>Answer</summary>
   The kubelet is the primary node agent. It manages pod lifecycle, communicates with the API server, and controls container operations. Its security is critical because it can execute commands in any container on the node.
   </details>

2. **Why should `--read-only-port` be set to 0?**
   <details>
   <summary>Answer</summary>
   The read-only port (10255) exposes pod and node information without authentication. Disabling it (setting to 0) prevents information disclosure that could aid attackers in reconnaissance.
   </details>

3. **What Linux mechanisms provide container isolation?**
   <details>
   <summary>Answer</summary>
   Namespaces (process, network, mount, etc. isolation), cgroups (resource limits), and security modules (seccomp, AppArmor, SELinux for system call and access control).
   </details>

4. **What is a sandboxed runtime and when should you use it?**
   <details>
   <summary>Answer</summary>
   Sandboxed runtimes (gVisor, Kata Containers) provide stronger isolation than standard runtimes. Use them for untrusted workloads, multi-tenant environments, or when processing sensitive data where container escape risk must be minimized.
   </details>

5. **How does Node authorization mode limit blast radius?**
   <details>
   <summary>Answer</summary>
   Node authorization mode restricts kubelet credentials to only access resources for pods scheduled on that node. If a node is compromised, the attacker can't use its credentials to access secrets or pods on other nodes.
   </details>

---

## Hands-On Exercise: Node Security Assessment

**Scenario**: Review this kubelet configuration and identify security issues:

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authentication:
  anonymous:
    enabled: true
  webhook:
    enabled: false
authorization:
  mode: AlwaysAllow
readOnlyPort: 10255
protectKernelDefaults: false
```

**Identify the security issues:**

<details>
<summary>Security Issues</summary>

1. **`anonymous.enabled: true`**
   - Allows unauthenticated access to kubelet API
   - Should be `false`

2. **`webhook.enabled: false`**
   - Disables authentication webhook
   - Should be `true` to validate client certificates

3. **`authorization.mode: AlwaysAllow`**
   - No authorization checking
   - Should be `Webhook` to check with API server

4. **`readOnlyPort: 10255`**
   - Read-only port enabled
   - Should be `0` (disabled)

5. **`protectKernelDefaults: false`**
   - Kubelet won't error if kernel parameters differ from expected
   - Should be `true` to ensure kernel hardening

**Secure configuration:**
```yaml
authentication:
  anonymous:
    enabled: false
  webhook:
    enabled: true
authorization:
  mode: Webhook
readOnlyPort: 0
protectKernelDefaults: true
```

</details>

---

## Summary

Node security involves multiple layers:

| Component | Key Security Controls |
|-----------|----------------------|
| **Kubelet** | Disable anonymous auth, use webhook authorization, disable read-only port |
| **Container Runtime** | Keep updated, use seccomp/AppArmor, consider sandboxed runtimes |
| **OS** | Minimal images, regular patching, immutable infrastructure |
| **Access** | Restrict SSH, use bastion hosts, audit access |

Key concepts:
- Kubelet API is powerful and must be protected
- Container isolation relies on Linux kernel features
- Sandboxed runtimes provide stronger isolation
- Node authorization limits blast radius
- Minimal, immutable OS reduces attack surface

---

## Next Module

[Module 2.3: Network Security](../module-2.3-network-security/) - CNI plugins, service mesh security, and network-level controls.
