---
revision_pending: false
title: "Module 4.3: Container Escape"
slug: k8s/kcsa/part4-threat-model/module-4.3-container-escape
sidebar:
  order: 4
---

# Module 4.3: Container Escape

> **Complexity**: `[MEDIUM]` - Threat awareness
>
> **Time to Complete**: 55-65 minutes
>
> **Prerequisites**: [Module 4.2: Common Vulnerabilities](../module-4.2-vulnerabilities/)

## Learning Outcomes

After completing this module, you will be able to review a Pod spec like a security engineer, explain which host boundary is being weakened, and choose prevention controls that match the workload rather than relying on generic hardening advice:

1. **Diagnose** container escape risk in Pod specifications by tracing privileged mode, host namespaces, hostPath volumes, Linux capabilities, and runtime choices.
2. **Evaluate** the blast radius of node-level access by connecting host files, process namespaces, network namespaces, and Kubernetes ServiceAccount permissions.
3. **Implement** prevention using Pod Security Admission, restricted security contexts, and runtime sandboxing for Kubernetes 1.35 clusters.
4. **Compare** sandboxed runtimes and standard runtime hardening to choose controls for trusted, third-party, and multi-tenant workloads.

## Why This Module Matters

In 2019, a cloud provider disclosed that a flaw in its hosted container service could let a customer container reach host-level credentials under certain conditions. The public write-up was careful, the technical details were controlled, and the affected platform moved quickly, but the lesson was hard to miss: the business impact of container escape is not limited to one compromised application. A single boundary failure can turn a web shell into node access, node access into credential theft, and credential theft into a cluster-wide incident that pulls engineers, legal teams, and customers into the same emergency call.

The same pattern appears in less famous incidents inside ordinary engineering teams. A vendor agent asks for `privileged: true`, a debugging Pod mounts `/`, or a CI runner receives access to the runtime socket because it makes image builds convenient. Nothing looks malicious during deployment, yet the cluster has quietly changed from "containers are isolated workloads" to "any application compromise can become host access." That is why the KCSA expects you to recognize escape-enabling configurations before you memorize exploit commands.

This module teaches container escape as a threat-modeling problem. You will learn how Linux isolation normally protects a node, which Kubernetes settings intentionally weaken that isolation, how the blast radius changes when a container reaches host resources, and where prevention belongs in a Kubernetes 1.35 environment. We will use the shell alias `alias k=kubectl` in examples and prose; after that first explanation, commands such as `k apply` and `k get` refer to `kubectl`.

## Container Escape Changes the Trust Boundary

Container escape means a process that should be confined inside a container gains meaningful access to the node that runs it. The phrase can sound dramatic, but the underlying idea is simple: a container is not a tiny virtual machine with its own kernel. It is a set of Linux processes using namespaces, cgroups, capabilities, filesystem mounts, security profiles, and runtime policy to create a limited view of the host.

The trust boundary matters because Kubernetes schedules many workloads onto the same node. When isolation holds, a vulnerable application may lose its own data, its mounted Secrets, and the permissions of its ServiceAccount. When isolation fails, the attacker may read host files, inspect other containers, tamper with node services, access container runtime APIs, or harvest credentials used by infrastructure components. The incident has moved from application response to node and cluster response.

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

Notice the important wording in the diagram: "full host access" is a possible result, not the only result. Some escape paths grant direct root-equivalent control, while others grant a narrow but dangerous path such as access to the runtime socket or visibility into host processes. In threat modeling, your job is to identify which host resource has crossed the boundary and what that resource can do next.

The easiest mistake is to treat "root in a container" as the same thing as "root on the host." They are related, but they are not identical. A root process inside a default, well-confined container may still be blocked by namespaces, dropped capabilities, seccomp filtering, read-only mounts, and file permissions. A non-root process with access to a powerful host socket may be more dangerous than a root process without that socket.

Pause and predict: if an attacker compromises a non-root web application that can reach only its own process namespace and a read-only application filesystem, what host resource would they still need before this becomes a container escape investigation? Write down the boundary they would have to cross, because that answer is more useful than memorizing a list of scary settings.

Think of a container like a hotel room rather than a separate building. The guest has a door, walls, a key, and rules about where they may go, but the room still shares plumbing, wiring, staff access, and emergency systems with the rest of the hotel. Container escape happens when the guest receives a master key, finds a service corridor, convinces staff to open restricted doors, or breaks a shared utility that everyone depends on.

Kubernetes adds another layer to this model. A Pod spec is not merely application configuration; it is a request for specific host interactions. A setting such as `hostPID: true` asks the kubelet to place the container in the host process namespace. A hostPath volume asks the kubelet to make part of the node filesystem visible inside the container. A capability asks the kernel to permit operations that ordinary application code rarely needs.

KCSA-level knowledge is about recognizing when those requests are legitimate, when they are excessive, and how they compose. A single setting may be tolerable for a narrowly scoped system agent, but the same setting in a business application namespace may violate the cluster's threat model. Multiple settings together often matter more than any one setting alone, because attackers chain visibility, write access, and execution control.

## Risk Factors That Turn a Pod Into a Host Door

The highest-risk container escape configurations are rarely subtle. They ask Kubernetes to give a container host-level authority because a workload, operator, or vendor tool claims it needs that authority. The operational challenge is that some infrastructure workloads really do need unusual access, so the secure answer is not "never run system agents." The secure answer is to understand exactly what was granted and to isolate it with intent.

Privileged mode is the clearest example. A privileged container receives broad access to Linux capabilities and host devices, and many runtime security restrictions are relaxed. It exists for node-level system workloads, hardware agents, low-level networking components, and break-glass operations. It is dangerous because an application compromise no longer has to defeat many separate isolation controls; the Pod was already launched with much of the host boundary removed.

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

For exams and real reviews, read `privileged: true` as a cluster-risk finding unless the Pod is a known infrastructure component in a tightly controlled namespace. It is not a harmless convenience flag for debugging. If an incident responder leaves a privileged Pod manifest in a repository, any identity that can deploy it later has a reusable host-access mechanism, even if nobody intended to create a backdoor.

Host namespace sharing is more nuanced. Namespaces normally make a container see its own processes, network interfaces, IPC objects, and filesystem mount view. Setting `hostPID`, `hostNetwork`, or `hostIPC` tells the runtime to share part of the node's view. That does not always grant immediate write access, but it gives an attacker information and reach that ordinary application Pods should not have.

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

With `hostPID`, a container can observe host processes and sometimes signal them, depending on its user, capabilities, and other protections. Combined with `CAP_SYS_PTRACE`, that visibility can become process inspection. Combined with writable host filesystem access, it can help an attacker identify which service files, credentials, or runtime artifacts are worth targeting. The setting is common in node troubleshooting tools, but that does not make it safe for normal application workloads.

With `hostNetwork`, the container uses the node network namespace. That can be legitimate for certain network plugins, DNS agents, or monitoring components, but it bypasses assumptions built around Pod networking. The workload may bind host ports, contact services listening on localhost, reach link-local metadata endpoints where available, and avoid NetworkPolicy controls that were written for the Pod network. It expands blast radius even when it is not a direct escape by itself.

HostPath volumes are often the most concrete risk because they place host files inside the container's filesystem. A read-only mount of a narrow log directory is different from a writable mount of `/`, and a path to a runtime socket is different again. The question to ask is not "is hostPath allowed somewhere?" but "what exact host object crossed into the container, with what access mode, and what can that object control?"

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

The Docker socket example remains important even in clusters that use containerd, because the lesson generalizes to runtime and node-control sockets. A Unix socket is not just a file. If it exposes an API that can start containers, mount paths, or control workloads, then access to that socket may be equivalent to asking a privileged helper to act for the attacker. File permissions and group membership become part of your escape analysis.

Pause and predict: if a Pod mounts `/var/run/docker.sock` but sets `runAsNonRoot: true`, `allowPrivilegeEscalation: false`, and `capabilities.drop: ["ALL"]`, what control still matters more than the process UID? The key is whether the process can speak to the socket and whether that socket can ask the node to create a stronger container.

Linux capabilities are another common source of confusion. Instead of treating root as one giant permission, Linux divides many privileged operations into named capabilities. Kubernetes lets a container add or drop capabilities in its security context. Dropping all capabilities and adding back only the required ones is a strong pattern, but adding the wrong one can be nearly as risky as privileged mode for a specific escape path.

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

`CAP_SYS_ADMIN` deserves special attention because it covers a broad set of operations, including mount-related behavior, and has long been described as overloaded. If a vendor asks for it, do not accept "the agent needs admin" as an explanation. Ask which kernel operation requires it, whether a narrower design exists, and whether the workload belongs in a privileged system namespace rather than beside business applications.

`CAP_SYS_PTRACE` is dangerous when the process namespace is also expanded. Debugging one process inside the same container is different from tracing host processes. The same capability that helps developers inspect a failing binary can help an attacker inspect process memory, tokens, arguments, and environment variables if the namespace boundary has been widened. This is why escape analysis is compositional rather than checkbox-based.

Kernel vulnerabilities form the final category. Containers share the host kernel unless a sandboxed runtime or virtualized isolation layer changes that model. If the kernel contains a reachable privilege escalation bug, then a container with otherwise reasonable settings may still become an entry point. Seccomp and least privilege reduce reachable attack surface, but they do not make kernel patching optional.

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

Kernel escape risk is one reason managed Kubernetes upgrades, node image maintenance, and runtime default profiles belong in security conversations. A team can write excellent Pod specs and still carry old kernel exposure if nodes lag behind. Conversely, patched nodes do not excuse dangerous Pod specs, because misconfiguration remains the more common way organizations hand host access to workloads.

Before running this mental review on a real manifest, predict which finding would matter most in your own environment: a privileged Pod in a locked system namespace, a non-root Pod with a writable `/` hostPath, or a normal Pod running on nodes with old kernels. There is no universal answer without context, and that is the point. Threat modeling ranks risk by path, exposure, and control, not by keyword alone.

## Prevention Starts With Admission and Least Privilege

The most reliable container escape prevention happens before the Pod starts. Once a dangerous Pod is admitted and scheduled, the node has already honored the request. You can still detect, respond, and kill the workload, but prevention belongs in policy, review, and namespace design. Kubernetes gives you a native starting point with Pod Security Standards and Pod Security Admission.

Pod Security Standards define three policy profiles: Privileged, Baseline, and Restricted. Baseline blocks many known privilege escalation paths while allowing common application patterns. Restricted is stricter and pushes workloads toward non-root execution, dropped capabilities, seccomp, and reduced filesystem mutation. In production application namespaces, Restricted should be the default starting point unless a specific workload proves it cannot run there.

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

In Kubernetes 1.35, the operational pattern is to label namespaces with Pod Security Admission modes and versions. Use `enforce` for the standard that must be blocked, `warn` to teach developers before enforcement expands, and `audit` to generate records for security review. For example, a team may use `k label ns production pod-security.kubernetes.io/enforce=restricted pod-security.kubernetes.io/enforce-version=v1.35` after validating workloads in a staging namespace.

Admission is powerful because it removes debate from every deployment. A developer does not need to remember that `hostPID` is risky if the namespace policy rejects it. A reviewer does not need to catch every privileged sidecar if CI and admission catch it first. The tradeoff is that legitimate system components need a different path, and that path must be explicit rather than accidental.

Least privilege starts inside the Pod spec. A hardened application container runs as a non-root user, disallows privilege escalation, drops Linux capabilities, uses a runtime default seccomp profile, avoids host namespaces, avoids hostPath volumes, and uses a read-only root filesystem when possible. These controls do not make the application invulnerable, but they force an attacker to defeat multiple separate barriers.

The order of those barriers matters. `runAsNonRoot` reduces the authority of the process. `allowPrivilegeEscalation: false` blocks common setuid-style privilege gains inside the container. Dropping capabilities removes privileged kernel operations. Seccomp limits syscall reach. Read-only filesystems reduce persistence and tampering. None of them replaces admission policy, but together they make "one web bug equals node compromise" far less likely.

Many teams struggle when a workload fails under Restricted policy. The useful response is not to switch the namespace to Privileged. Instead, identify the exact control that breaks the workload. Does the image assume root because it writes under `/var`? Change the image or mount an `emptyDir` at the write path. Does it need a low port? Use a higher container port and map it through a Service. Does it need host metrics? Consider a dedicated agent with bounded access.

This is where threat modeling becomes practical engineering. You are not trying to win an argument against the application team. You are trying to preserve the boundary while giving the workload enough authority to do its job. If the answer requires an exception, the exception should name the namespace, workload, field, reason, owner, review date, and compensating controls.

A realistic production cluster often uses at least three namespace classes. Application namespaces enforce Restricted. Platform system namespaces allow carefully reviewed exceptions for networking, storage, observability, and node management. Experimental or break-glass namespaces may permit stronger access for short windows, but they should have separate RBAC, audit visibility, and cleanup. The goal is to keep unusual power away from routine deployment paths.

Worked example: a third-party monitoring agent asks for `hostPID`, `hostNetwork`, and `privileged: true`. Instead of granting those fields in every application namespace, create a dedicated namespace such as `monitoring-system`, apply the least permissive Pod Security mode that admits the agent, restrict who can deploy there, and confirm the agent's ServiceAccount cannot mutate arbitrary workloads. Then ask the vendor which fields are truly required, because many agents ask for more than they use.

Which approach would you choose here and why: relaxing Restricted in the `payments` namespace so one vendor DaemonSet can deploy, or isolating the DaemonSet in a dedicated namespace with targeted RBAC and network controls? The second path is more work during setup, but it keeps a vendor exception from becoming a default permission for unrelated application Pods.

Prevention also includes reviewing image and runtime assumptions. A Pod that runs as UID 1000 may still write to a hostPath if the path permissions allow it. A read-only root filesystem does not protect a writable mounted host directory. A dropped capability set does not protect a powerful runtime socket. Each control must be evaluated against the resource it is supposed to protect, not admired in isolation.

## Runtime Sandboxing and Detection Add Separate Layers

Admission and least privilege reduce the chance that a workload starts with dangerous host access. Runtime isolation and detection address the remaining risk: bugs, kernel vulnerabilities, untrusted code, tenant separation, and mistakes that slip through review. This is where seccomp, AppArmor, SELinux, gVisor, Kata Containers, and runtime monitoring become part of the container escape story.

Defense in depth is not a slogan here. It means each layer blocks a different failure mode. Pod Security Admission blocks risky specifications. Security contexts reduce process authority. Seccomp and Linux security modules reduce kernel attack surface. Sandboxed runtimes change how directly the workload reaches the host kernel. Monitoring looks for behavior that should never happen from an ordinary application container.

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

Seccomp is often the first runtime layer teams adopt because Kubernetes can request `RuntimeDefault` profiles directly in the Pod security context. A seccomp profile limits which system calls a container process may make. If an exploit depends on a blocked syscall, seccomp can stop the path even after application code is compromised. The tradeoff is compatibility, because unusual applications may require syscalls outside the default profile.

AppArmor and SELinux add mandatory access controls that can limit what a process may do even when Unix permissions would otherwise allow it. These systems are node and distribution dependent, so cluster teams need to understand what their managed platform supports. They are valuable because they provide another policy layer outside the application image, but they require operational maturity to profile and troubleshoot without weakening policy during incidents.

Sandboxed runtimes change the relationship between the container and the host kernel. A standard runtime still depends heavily on the shared host kernel for isolation. gVisor intercepts and implements many syscalls in user space, reducing direct kernel exposure. Kata Containers run workloads inside lightweight virtual machines, giving each sandbox a separate guest kernel and hardware virtualization boundary.

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

Kubernetes uses RuntimeClass to select an alternate runtime handler when the node supports one. That makes sandboxing a scheduling and policy choice rather than a rewrite of the application. A Pod can set `runtimeClassName: gvisor` or another configured class, and the kubelet asks the container runtime to use the matching handler. Platform teams must still install, test, and capacity-plan those runtimes on the nodes.

The tradeoff is performance, compatibility, and operational complexity. gVisor can break workloads that depend on unusual kernel behavior. Kata can have higher startup and memory overhead because it adds virtualization. Neither option removes the need for Pod Security Admission, because a sandboxed privileged workload can still create risk inside its own sandbox or through exposed host integrations. Sandboxing is a strong extra layer for selected workloads, not permission to ignore basic hardening.

Runtime detection completes the picture by assuming that prevention may fail. Tools such as Falco can detect suspicious behavior like shell execution in a container, writes to sensitive paths, unexpected access to runtime sockets, or processes attempting namespace changes. Detection does not stop every attack by itself, but it shortens the time between boundary violation and human response.

Detection rules should map to your escape model. If ordinary application Pods should never open `/var/run/docker.sock`, alert on that access. If only node agents should use host namespaces, alert when an unexpected namespace uses them. If a business service suddenly executes package managers, shells, or mount utilities, treat that as a compromise signal. Good alerts are tied to expectations that can be defended.

A useful war story is the "temporary debug Pod" that becomes permanent. During an outage, a team deploys a privileged Ubuntu Pod with host mounts because it is faster than SSH access. The outage ends, the Pod is forgotten, and weeks later a separate application bug gives an attacker a path to the same namespace. The privileged debug manifest has converted a routine app compromise into a node compromise because operational cleanup failed.

The fix is not to ban troubleshooting. The fix is to create safer debugging paths. Use ephemeral containers when they fit, restrict who can create them, avoid host mounts by default, and require explicit approval for node-level debugging. If host access is required, prefer short-lived access controlled outside the application namespace, with audit records and documented cleanup criteria.

## Worked Review: Escape Path Analysis

The fastest way to diagnose container escape risk is to read a Pod spec from the node outward. First, ask whether the container sees host namespaces. Next, ask whether it can read or write host filesystem paths. Then check whether it has capabilities that make those paths more useful. Finally, check whether it has API access, runtime socket access, or a sandboxed runtime that changes the model.

Here is the intentionally risky Pod from the original exercise. Do not start by fixing it. Start by naming the host resources that were made available to the container, because that keeps your review grounded in cause and consequence rather than fear of individual keywords.

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

The first finding is `hostPID: true`, which places the container in the host process namespace. That alone expands visibility, but its impact becomes larger because the Pod also adds `SYS_PTRACE`. Together, the settings suggest the container may be able to inspect or interact with processes beyond its own container boundary. In a real review, that combination deserves a high-severity finding unless the workload is a tightly controlled node diagnostic tool.

The second finding is the host root mount. Mounting `/` at `/host` gives the container a view of the node filesystem. The impact depends on write access, file ownership, user identity, and mount options, but the design is dangerous even before you inspect those details. Host files often contain kubelet state, runtime data, logs, service credentials, certificates, and configuration that can help an attacker move from one foothold to broader control.

The third finding is the runtime socket. The manifest uses `/var/run/docker.sock`, which is a classic example of handing a container the ability to talk to the Docker daemon. In a modern Kubernetes cluster, you may see containerd or CRI-related sockets instead, but the reasoning stays the same. If a socket lets the process ask a privileged node service to create workloads or mount host paths, then filesystem hardening inside the original container may not save you.

The fourth finding is `SYS_ADMIN`, which is often too broad for application workloads. In the presence of a host filesystem mount, host PID visibility, or privileged helper APIs, broad capabilities make follow-on actions easier. The right review question is not "can we leave it because the application starts only with this capability?" It is "which exact operation needs this capability, and can that operation be removed, isolated, or replaced?"

Before looking at the fixed Pod, predict which single removal would reduce the most risk if you had only one emergency change window. Removing the host root mount often has the largest immediate effect, but in some environments the runtime socket could be even worse because it delegates powerful actions to the node runtime. Your answer should cite the path an attacker would use, not merely name a field.

Now compare the risky spec to a Restricted-style application Pod. The fixed version does not try to preserve every behavior from the risky Pod, because a normal application should not need those host resources. It removes host namespace sharing, removes hostPath volumes, runs as a non-root user, drops capabilities, disables privilege escalation, uses seccomp, and makes the root filesystem read-only.

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

This fixed spec is not a universal template, because applications differ. Some need writable temporary storage, so you may add an `emptyDir` mounted at `/tmp` rather than making the whole root filesystem writable. Some need a specific Linux capability, so you may add one back after review rather than accepting the default set. The teaching point is that each exception should be narrow, named, and tested against the threat model.

If this workload truly needed node-level behavior, the better design would move it out of the application namespace and into a controlled system namespace. The ServiceAccount would receive only the permissions it needs. Network access would be restricted. Runtime monitoring would be tuned around its expected behavior. The exception would be visible to platform owners rather than hidden inside a normal deployment path.

You can use `k get pod risky-pod -o yaml` during a review to confirm the live spec, but do not stop at the submitted manifest. Mutating admission webhooks, defaults, Helm templates, and operator controllers can change what actually runs. The escaped boundary belongs to the live Pod on the node, not to the file someone intended to deploy.

## Patterns & Anti-Patterns

Good container escape prevention patterns make dangerous authority explicit. They do not rely on every developer remembering every field, and they do not pretend that system workloads are the same as web applications. The strongest organizations separate normal application deployment from node-level tooling, enforce policy by namespace, and keep exception review close to the people who operate the cluster.

The first pattern is "Restricted by default, exceptions by namespace." Application teams should start inside namespaces that enforce the Restricted Pod Security Standard for the current Kubernetes minor version. Infrastructure components that need stronger access should live in dedicated namespaces with different labels, tighter RBAC, and explicit ownership. This scales because the default path is safe while exceptions remain inspectable.

The second pattern is "drop first, add deliberately." A Pod should drop all capabilities and then add only the capability required for a documented operation. This works because it reverses the usual failure mode, where workloads inherit authority they never use. It also makes review easier, since every added capability becomes a question with a concrete answer instead of an unnoticed default.

The third pattern is "replace hostPath with Kubernetes storage or purpose-built APIs." Application teams often ask for hostPath because it looks like the simplest way to share files with a node. PersistentVolumes, ConfigMaps, Secrets, projected volumes, and node agents often provide safer alternatives. When hostPath is unavoidable, it should be read-only where possible, limited to a narrow path, and isolated from general application namespaces.

The fourth pattern is "sandbox the workloads you do not fully trust." Multi-tenant build systems, user-submitted code, classroom labs, preview environments, and third-party plugin execution carry different assumptions than first-party services. A sandboxed runtime gives those workloads a stronger boundary, but it should be paired with resource quotas, network controls, and admission policy. Sandboxing changes the risk equation; it does not erase operations work.

Anti-patterns usually come from time pressure. The most common is deploying a privileged debug Pod during an incident and leaving the manifest available afterward. Teams fall into this because outages reward speed, and node-level debugging sometimes feels like the only way to see the problem. The better alternative is to pre-build approved troubleshooting workflows with time limits, audit records, and cleanup steps.

Another anti-pattern is using vendor requirements as policy. A vendor chart may request privileged mode, host networking, and broad RBAC because that works across many customer environments. Your cluster is not every customer environment. Ask the vendor for a minimal mode, test which permissions are actually used, and deploy the component in a namespace designed for that risk if it truly requires host access.

A subtler anti-pattern is treating non-root as a complete answer. Running as non-root is important, but it does not neutralize a writable hostPath, a runtime socket, or a ServiceAccount with broad API permissions. Non-root is one control in a layered model. It reduces some actions and post-exploitation options, but it cannot protect a resource that the Pod was intentionally allowed to access.

| Pattern | When to Use | Why It Works | Scaling Consideration |
|---------|-------------|--------------|-----------------------|
| Restricted namespaces by default | Application and team-owned services | Blocks common escape-enabling fields before scheduling | Requires onboarding guidance for images that assume root or writable roots |
| Dedicated system namespaces | Node agents, CNI, CSI, observability components | Keeps privileged exceptions away from normal deployment paths | Needs strict RBAC, audit review, and owner accountability |
| Drop all capabilities first | Nearly all application containers | Removes unused privileged kernel operations | Add exceptions only with documented kernel operation and test evidence |
| Sandboxed runtime classes | Untrusted, third-party, or multi-tenant workloads | Reduces direct exposure to the host kernel | Requires node support, performance testing, and workload compatibility checks |

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Privileged debug Pods in application namespaces | A temporary incident tool becomes a reusable host-access path | Use controlled debugging workflows, ephemeral containers, and short-lived approval |
| Runtime socket mounts for builds | A compromised build job can ask the node runtime to create stronger containers | Use rootless builders, remote builders, or dedicated isolated build nodes |
| Broad hostPath mounts | Application compromise exposes host files and node credentials | Use PVCs, projected volumes, or narrow read-only mounts in controlled namespaces |
| Relaxing Pod Security for one workload | Every workload in the namespace inherits the weaker boundary | Move the exception to a dedicated namespace with compensating controls |

These patterns should be reviewed during design, not only after a scan fails. If a team knows in advance that a workload needs host networking, the platform team can design a safe placement strategy. If the requirement appears only as a surprise field in a pull request, the review becomes a negotiation under deadline pressure, and shortcuts become more likely.

## Decision Framework

Use container escape review as a structured decision rather than a gut feeling. Start with the workload's purpose, then identify host resources, then select controls that match the exposure. A user-facing application, a node exporter, a CI builder, and a multi-tenant lab runner should not receive the same answer because they do not create the same risk.

```
Workload needs host access?
  |
  +-- No --> Enforce Restricted, drop capabilities, no hostPath, RuntimeDefault seccomp.
  |
  +-- Yes --> Is it a platform-owned node agent?
             |
             +-- No --> Redesign with Kubernetes APIs, PVCs, Services, or external builders.
             |
             +-- Yes --> Dedicated namespace, narrow host resources, strict RBAC, audit, monitoring.
                         |
                         +-- Runs untrusted code or tenants? --> Add sandboxed runtime or isolation nodes.
                         |
                         +-- Trusted system component? -------> Keep least privilege and review exceptions.
```

The first branch asks whether host access is truly required. Many requests collapse under this question. Applications ask for hostPath because they need storage, but a PVC is enough. Services ask for host networking because a port was hard-coded, but a Service can front a normal Pod network. Images ask for root because file permissions are wrong, but the image can be corrected. Removing the need is stronger than controlling the exception.

The second branch asks who owns the workload. Platform-owned node agents have a different trust relationship than product-team applications. They are often part of the cluster's control or observability plane, and they may need host reach. That does not mean they are automatically safe. It means they belong in a namespace, RBAC boundary, and monitoring profile that reflects their authority.

The third branch asks whether the code itself is trusted. A first-party node agent from your platform team is not the same as customer-submitted build scripts or browser-executed challenge code. If the workload executes untrusted or third-party code, consider sandboxed runtimes, isolated node pools, tighter egress, and aggressive cleanup. The higher overhead is justified when the alternative is tenant-to-node compromise.

| Decision Question | Low-Risk Answer | High-Risk Answer | Recommended Control |
|-------------------|-----------------|------------------|---------------------|
| Does the Pod need host namespaces? | No host namespace sharing | `hostPID`, `hostNetwork`, or `hostIPC` requested | Block in app namespaces; isolate system agents |
| Does it need host files? | Uses PVC, Secret, ConfigMap, or projected volume | Broad or writable hostPath | Replace storage design or narrow and isolate the mount |
| Does it need privileged operations? | Drops all capabilities | Adds `SYS_ADMIN`, `SYS_PTRACE`, or privileged mode | Document exact operation; avoid full privileged mode |
| Does it run untrusted code? | First-party service with controlled inputs | Builds, plugins, labs, tenant code | Add sandboxed runtime and isolated nodes |
| Can compromise reach the Kubernetes API? | Minimal ServiceAccount permissions | Broad RBAC or mounted tokens with write access | Use least-privilege RBAC and token controls |

When you evaluate blast radius, include both node access and API access. A container escape may expose kubelet data, runtime state, host credentials, and other containers on the node. Separately, the Pod's ServiceAccount may allow Kubernetes API actions. A weak ServiceAccount does not make host access safe, and a strong ServiceAccount does not require host access to cause damage. Treat both paths as part of the same incident model.

The final decision should produce a clear outcome: reject the Pod, accept it under Restricted, accept a narrow exception in a dedicated namespace, or move it to a sandboxed or isolated node pool. Avoid vague outcomes such as "monitor closely" without changing the permission model. Monitoring is a compensating control, not a substitute for deciding whether the workload should have host authority.

## Did You Know?

- **Most practical container escapes begin with configuration, not zero-days.** A writable hostPath, privileged mode, or runtime socket mount is easier to abuse than a kernel exploit, which is why admission policy has such high defensive value.
- **Dirty COW was assigned CVE-2016-5195 and Dirty Pipe was assigned CVE-2022-0847.** These examples are memorable because they remind defenders that containers share kernel risk unless an extra isolation layer changes that relationship.
- **Kubernetes Pod Security Admission graduated to stable in Kubernetes 1.25.** By Kubernetes 1.35, teams should treat namespace labels for `enforce`, `audit`, and `warn` as normal cluster hygiene rather than an advanced feature.
- **gVisor and Kata solve different isolation problems.** gVisor reduces direct host-kernel syscall exposure with a user-space kernel, while Kata uses lightweight virtual machines to provide a separate guest kernel boundary.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Using `privileged: true` for convenience | Debugging and vendor charts often work faster when all restrictions are removed | Require a named exception, move it to a system namespace, and replace privileged mode with specific capabilities where possible |
| Mounting a runtime socket into a workload | Build and automation jobs want local runtime control | Use rootless or remote builders, isolated build nodes, and avoid exposing node-control sockets to application Pods |
| Treating non-root as complete protection | Teams correctly value `runAsNonRoot` but forget that mounted host resources keep their own power | Pair non-root execution with no dangerous hostPath, dropped capabilities, seccomp, and admission policy |
| Allowing broad writable hostPath volumes | Local files look like the simplest way to share data with a node | Use PVCs or projected volumes, and restrict any unavoidable hostPath to a narrow read-only path in a controlled namespace |
| Relaxing Pod Security labels on a shared namespace | One workload fails Restricted, so the whole namespace is weakened | Move the exception into a dedicated namespace and keep application namespaces Restricted |
| Ignoring ServiceAccount permissions during escape analysis | Reviewers focus only on Linux controls and miss API blast radius | Evaluate node access and Kubernetes API permissions together during threat modeling |
| Delaying node patching because Pods are hardened | Teams overestimate what security contexts can do against kernel vulnerabilities | Keep node images current and consider sandboxed runtimes for workloads with untrusted code |

## Quiz

<details><summary>Your team finds a production Pod with `privileged: true`, `hostPID: true`, and a hostPath mount to `/`. The owner says it is used only during incidents. How do you evaluate the risk and what safer path do you propose?</summary>

This is a high-risk escape path because it combines broad capability, host process visibility, and direct host filesystem access. The temporary nature does not remove the risk, since any identity that can deploy or reuse the manifest can recreate the host-access path. A safer approach is to remove the Pod from application namespaces, use controlled debugging workflows such as approved ephemeral containers where possible, and require short-lived, audited access for true node-level debugging. The key reasoning is that incident speed should not leave a reusable privileged workload in normal deployment paths.

</details>

<details><summary>A non-root container drops all capabilities but mounts `/var/run/docker.sock`. Can the attacker still escape after compromising the app, and why?</summary>

Yes, if the process can access the socket, the risk remains severe. The socket exposes a privileged API to the container runtime, so the attacker may be able to ask the daemon to create a new container with stronger host access. The process UID and capability set inside the original container help only if they prevent access to that socket. This is why runtime socket mounts are reviewed as host-control delegation, not as ordinary file mounts.

</details>

<details><summary>A cluster enforces Restricted Pod Security, but a kernel privilege escalation is announced for the node OS. What do you check first, and what extra defense can help for untrusted workloads?</summary>

You first check node image versions, patch availability, and which nodes run workloads that could reach the vulnerable kernel path. Restricted Pod Security reduces many misconfiguration paths, but standard containers still share the host kernel. Seccomp may help if the exploit needs blocked syscalls, but it is not a substitute for patching. For untrusted workloads, sandboxed runtimes such as gVisor or Kata can reduce direct exposure to the host kernel.

</details>

<details><summary>A monitoring vendor requests `hostNetwork: true` for a DaemonSet. What escape-adjacent risks does that create even if the container is not privileged?</summary>

Host networking places the workload in the node network namespace, which expands what it can see and reach. It may bind host ports, reach localhost-only node services, bypass Pod-network assumptions, and avoid NetworkPolicy rules written for normal Pod traffic. That does not automatically grant host filesystem access, but it increases lateral movement and impersonation risk after compromise. The safer design is a dedicated namespace, narrow RBAC, documented need, and monitoring around expected network behavior.

</details>

<details><summary>You need to implement a prevention policy for a payments namespace in Kubernetes 1.35. Which controls should be enforced and how would you handle one workload that fails?</summary>

The namespace should enforce the Restricted Pod Security Standard for the current Kubernetes version, and workloads should run non-root, drop capabilities, use RuntimeDefault seccomp, avoid host namespaces, and avoid dangerous hostPath volumes. If one workload fails, do not relax the whole payments namespace. Identify the exact failing field and redesign the workload if possible. If a real exception remains, move it to a dedicated namespace with explicit ownership, tighter RBAC, audit visibility, and compensating controls.

</details>

<details><summary>A CI runner executes third-party build scripts. It currently uses a standard runtime and a hostPath cache. How would you compare standard hardening with sandboxed runtime isolation?</summary>

Standard hardening is still required: drop capabilities, avoid privileged mode, restrict ServiceAccount permissions, and replace broad hostPath mounts. However, third-party build scripts are untrusted code, so a stronger boundary is usually justified. A sandboxed runtime or isolated node pool reduces the chance that a build escape reaches the host kernel or neighboring workloads. The tradeoff is performance and compatibility testing, which is reasonable for this risk class.

</details>

<details><summary>A reviewer sees `SYS_PTRACE` in a Pod spec but no `hostPID`. Is that automatically a node escape, and what follow-up question should they ask?</summary>

It is not automatically a node escape, because the capability may apply only within the container's process namespace. The reviewer should ask why the workload needs tracing and whether it can inspect only its own processes. They should also check for combinations such as `hostPID`, privileged mode, broad hostPath, or sensitive tokens that would increase blast radius. The reasoning matters because capabilities become much more dangerous when paired with widened namespaces or host resources.

</details>

## Hands-On Exercise: Escape Path Analysis

In this exercise, you will review the risky Pod from the worked example as if it arrived in a pull request for a Kubernetes 1.35 production cluster. The goal is not to exploit anything. The goal is to diagnose escape risk, evaluate blast radius, implement a safer spec, and compare whether the workload belongs in a normal application namespace or in a special system path.

Use a scratch namespace in a disposable cluster if you choose to apply examples. If you do not have a cluster available, complete the review on paper from the manifest. The important skill is explaining how each setting changes the node trust boundary and which control would block that path before the Pod starts.

### Tasks

- [ ] Identify every field in the risky Pod that increases container escape risk, and group the findings by namespace sharing, host filesystem access, runtime control, and capabilities.
- [ ] Evaluate the blast radius if the application process is compromised, including node files, host processes, runtime socket access, and Kubernetes API permissions.
- [ ] Implement a Restricted-style replacement spec that removes host namespace sharing, removes hostPath volumes, drops capabilities, uses non-root execution, sets `allowPrivilegeEscalation: false`, and uses `RuntimeDefault` seccomp.
- [ ] Compare two exception designs if the workload is actually a node agent: a relaxed application namespace versus a dedicated system namespace with targeted RBAC and monitoring.
- [ ] Define success criteria for admission policy by writing which Pod Security labels should exist on the application namespace and which namespace, if any, may hold the exception.

<details><summary>Solution: Risk Factors</summary>

The risky Pod has multiple escape risk factors. The runtime socket mount at `/var/run/docker.sock` can delegate host-control operations to the Docker daemon if the process can access the socket. The host root filesystem mount exposes the node filesystem under `/host`, which may reveal credentials, kubelet state, service configuration, and other sensitive data. `hostPID: true` expands process visibility to the node, and `SYS_PTRACE` makes that visibility more dangerous because tracing is no longer limited to ordinary application processes. `SYS_ADMIN` is broad and should be treated as a serious exception because it enables many privileged kernel operations.

</details>

<details><summary>Solution: Blast Radius</summary>

The blast radius includes both node-level and Kubernetes-level paths. On the node, the attacker may inspect host processes, read or modify host files depending on permissions and mount mode, and use the runtime socket to request new containers with stronger access. In Kubernetes, the Pod's ServiceAccount token may allow API actions, so RBAC must be reviewed even though it is not visible in the snippet. The combined risk is higher than any single field because process visibility, filesystem access, capabilities, and runtime control can reinforce each other.

</details>

<details><summary>Solution: Fixed Pod Spec</summary>

Use the fixed spec shown in the worked example as the baseline. It removes host namespace sharing and hostPath volumes, runs as UID 1000 with `runAsNonRoot: true`, sets `readOnlyRootFilesystem: true`, blocks privilege escalation, drops all capabilities, and requests `RuntimeDefault` seccomp. If the application needs writable temporary storage, add a narrow `emptyDir` for that path instead of making the root filesystem writable. If it needs a capability, document the exact operation and add only that capability after review.

</details>

<details><summary>Solution: Exception Design</summary>

Do not relax a shared application namespace for a node agent. Create a dedicated namespace with the minimum Pod Security level that admits the agent, limit who can deploy there, bind a minimal ServiceAccount, restrict network access where practical, and monitor behavior that would be suspicious for that component. If the code is untrusted or third-party, evaluate a sandboxed runtime or isolated node pool. The exception should be visible, owned, and reviewed rather than hidden beside ordinary applications.

</details>

### Success Criteria

- [ ] You can explain why `privileged: true`, host namespaces, broad hostPath, runtime sockets, and dangerous capabilities are separate escape risk factors.
- [ ] You can rank blast radius by the host resource exposed and the follow-on action it enables.
- [ ] Your fixed spec follows Restricted-style security context expectations for an application workload.
- [ ] Your exception design keeps node-level authority out of normal application namespaces.
- [ ] You can justify whether standard runtime hardening is enough or whether sandboxed runtime isolation is warranted.

## Sources

- [Kubernetes: Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes: Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
- [Kubernetes: Configure a Security Context for a Pod or Container](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [Kubernetes: hostPath volume documentation](https://kubernetes.io/docs/concepts/storage/volumes/#hostpath)
- [Kubernetes: RuntimeClass](https://kubernetes.io/docs/concepts/containers/runtime-class/)
- [Kubernetes: Restrict a Container's Syscalls with seccomp](https://kubernetes.io/docs/tutorials/security/seccomp/)
- [Kubernetes: Seccomp reference](https://kubernetes.io/docs/reference/node/seccomp/)
- [Kubernetes: Linux kernel security constraints for Pods and containers](https://kubernetes.io/docs/concepts/security/linux-kernel-security-constraints/)
- [gVisor documentation](https://gvisor.dev/docs/)
- [Kata Containers documentation](https://katacontainers.io/docs/)
- [Falco documentation](https://falco.org/docs/)
- [Docker: Protect the Docker daemon socket](https://docs.docker.com/engine/security/protect-access/)

## Next Module

[Module 4.4: Supply Chain Threats](../module-4.4-supply-chain/) - Learn how compromised images, dependencies, build systems, and registries can become the next path into a cluster.
