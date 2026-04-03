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

> **Pause and predict**: A container runs as root inside the container. Does that mean it has root access on the host node? What determines whether the container's root user maps to the host's root user?

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

> **Stop and think**: If a node is compromised and the attacker gains kubelet credentials, what limits the damage they can do to the rest of the cluster? What if Node authorization mode is not enabled?

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

1. **A security scan reveals that kubelet on your worker nodes has `--anonymous-auth=true` and `--authorization-mode=AlwaysAllow`. An attacker on the same network can reach port 10250. Describe the attack scenario and the potential impact.**
   <details>
   <summary>Answer</summary>
   The attacker can connect to the kubelet API without authentication and execute commands in any container on that node via the `/exec` endpoint. They can also read container logs via `/logs`, list all pods via `/pods`, and port-forward to containers. Impact: the attacker can steal secrets from any pod on the node, install backdoors, pivot to other systems using extracted credentials, and potentially escape to the host. Fix: set `anonymous.enabled: false`, `authorization.mode: Webhook`, and ensure the kubelet's client CA is configured. This is one of the most critical node-level misconfigurations.
   </details>

2. **Your team debates whether to use gVisor or standard containerd for a multi-tenant platform where different customer workloads share nodes. What are the security trade-offs of each choice?**
   <details>
   <summary>Answer</summary>
   Standard containerd (runc): containers share the host kernel, so a kernel vulnerability could allow one tenant's container to escape and access another tenant's workloads. Performance is optimal but isolation relies solely on namespaces, cgroups, and seccomp — all bypassed by kernel exploits. gVisor: provides a user-space kernel that intercepts syscalls, so containers never directly touch the host kernel. Kernel vulnerabilities don't enable escape. Trade-off: gVisor has performance overhead (varies by workload), doesn't support all syscalls (~70% coverage), and some applications may not work. For multi-tenant with untrusted workloads, gVisor's stronger isolation typically justifies the overhead.
   </details>

3. **Container-Optimized OS, Bottlerocket, and Talos are all "minimal" node operating systems. What specific security advantage does an immutable, minimal OS provide over a traditional Linux distribution like Ubuntu on Kubernetes nodes?**
   <details>
   <summary>Answer</summary>
   Minimal OSes have dramatically smaller attack surfaces: fewer installed packages means fewer CVEs to patch and fewer tools available to attackers who gain node access. Immutability means the OS filesystem is read-only — attackers cannot persist changes, install rootkits, or modify system binaries. Traditional Ubuntu has hundreds of packages (shell utilities, package managers, compilers) that attackers use post-compromise. Talos goes further by removing SSH entirely, making the OS API-driven only. The security benefit is both preventive (fewer vulnerabilities) and detective (any filesystem change is anomalous and detectable).
   </details>

4. **A pod specification includes `hostPID: true` and the container has `CAP_SYS_PTRACE`. The container image is a legitimate debugging tool used by the operations team. Is this configuration acceptable, and what risks does it introduce?**
   <details>
   <summary>Answer</summary>
   This combination is extremely dangerous even for legitimate use. hostPID lets the container see all host processes, and CAP_SYS_PTRACE allows attaching to and inspecting those processes — including reading process memory. An attacker who compromises this container could extract secrets from any process on the host, including kubelet credentials, other containers' environment variables, and encryption keys in memory. If this debugging tool is necessary, it should only run in dedicated maintenance namespaces with strict network policies, never in production, require manual approval, and be time-limited. Pod Security Standards (Baseline and above) block this configuration.
   </details>

5. **Node authorization mode was introduced specifically to address a real attack vector. Describe the attack that Node authorization prevents and explain why standard RBAC alone wasn't sufficient.**
   <details>
   <summary>Answer</summary>
   The attack: if a single node is compromised, the attacker gets the kubelet's credentials. Without Node authorization, those credentials could access secrets and configmaps for pods on ANY node — because RBAC only checks "can this identity access this resource type?" not "is this resource relevant to this node?" The attacker could enumerate and steal secrets from every pod in the cluster. Node authorization adds identity-awareness: it restricts kubelet credentials to only access resources for pods actually scheduled on that specific node. Standard RBAC lacks this node-affinity concept — it can grant or deny access to resource types but cannot scope access based on pod-to-node scheduling relationships.
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
