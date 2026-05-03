---
title: "Module 5.3: Runtime Security"
slug: k8s/kcsa/part5-platform-security/module-5.3-runtime-security
sidebar:
  order: 4
revision_pending: false
---

# Module 5.3: Runtime Security

> **Complexity**: `[MEDIUM]` - Core knowledge
>
> **Time to Complete**: 60-75 minutes
>
> **Prerequisites**: [Module 5.2: Security Observability](../module-5.2-observability/)

## Learning Outcomes

After completing this module, you will be able to:

1. **Implement** seccomp profiles and Kubernetes security contexts that reduce the Linux kernel attack surface for Kubernetes 1.35+ workloads.
2. **Compare** AppArmor and SELinux enforcement models, then select the Mandatory Access Control approach that fits the worker node operating system.
3. **Diagnose** failures caused by capability drops, read-only filesystems, privilege escalation controls, and runtime profile enforcement.
4. **Evaluate** standard OCI runtimes, gVisor, and Kata Containers for trusted, untrusted, and multi-tenant workload isolation.
5. **Design** admission and policy guardrails that keep runtime security controls consistent across teams without hiding operational tradeoffs.

## Why This Module Matters

In early 2018, researchers found that Tesla's Kubernetes administrative console had been exposed to the public internet without authentication. Attackers used that access to deploy malicious pods into the cluster, then ran cryptocurrency mining software that consumed AWS compute resources while trying to stay quiet. The public reporting focused on the exposed console, but the runtime lesson was just as important: once hostile code was running inside the cluster, weak runtime controls gave the attackers room to execute, consume resources, and blend into normal workload activity.

That incident is a useful warning because it separates configuration security from runtime security. Static scanners can tell you whether a manifest asks for privileged mode, and image scanners can warn about vulnerable packages before deployment, but neither one can stop an exploited process that is already making system calls on a worker node. Runtime security accepts that applications fail, dependencies contain bugs, and humans occasionally ship dangerous manifests; its job is to make the successful exploit disappointingly small.

Runtime controls are the difference between "the attacker reached one web process" and "the attacker can trace neighboring processes, mount host filesystems, load kernel features, or abuse a shared kernel bug." In this module, you will start with the Linux primitives that Kubernetes exposes, then connect them to admission policy and runtime selection. The point is not to memorize every security field in a Pod spec, but to learn how to build a layered boundary that still lets production software run.

## The Runtime Security Stack

A container is not a miniature virtual machine with a private kernel. It is a process on the worker node, wrapped in Linux namespaces for visibility boundaries, cgroups for resource accounting, filesystem layers for packaging, and a container runtime that starts the process with a selected set of restrictions. That distinction matters because a compromised process does not attack an abstract "container"; it asks the host kernel to perform operations on its behalf, and runtime security decides which of those requests should be allowed.

```text
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

The stack executes from the bottom upward, but operators configure it from the top downward. A developer submits a Pod manifest to the API server, admission controllers decide whether that manifest is acceptable, the scheduler assigns the Pod to a node, and the kubelet asks the container runtime to create the container. Only then does the runtime apply seccomp, AppArmor or SELinux, capabilities, filesystem flags, namespace choices, and the selected runtime handler before the application process begins.

This ordering creates an important design rule: kernel enforcement is strong only for Pods that actually request or receive the right settings. If one team remembers to set `seccompProfile: RuntimeDefault` and another team forgets, the node kernel cannot infer intent from the deployment name. Good runtime security therefore has two halves, a workload-level configuration that expresses least privilege and a cluster-level policy layer that prevents insecure workloads from arriving by accident.

Before using the examples, define the usual Kubernetes shortcut once in your shell with `alias k=kubectl`. The module uses `k` as the alias for `kubectl`, and commands such as `k apply -f runtime-lab.yaml` assume that alias is available.

Pause and predict: if a Pod is blocked by an admission policy before it reaches the kubelet, which layers of the runtime security stack never get a chance to enforce anything? The answer should shape how you debug security failures, because a rejected manifest and a killed process produce very different evidence.

Runtime security is also where Kubernetes forces you to think like both a platform engineer and a Linux operator. The Kubernetes API gives you fields such as `securityContext`, `runtimeClassName`, and Pod Security labels, but the actual enforcement happens in node software that may differ by operating system, image build, runtime configuration, and kernel version. A manifest that looks portable can therefore behave differently across node pools unless the platform publishes clear runtime classes, node labels, and security baselines.

The safest mental model is to treat each layer as a separate question. Admission asks whether the cluster should accept the object. The runtime asks how the process should be started. Linux security modules ask which kernel operations, file paths, labels, and privileges remain available after startup. A failure at any one layer should not tempt you to disable the whole stack, because the layers are deliberately narrow and become strong only when combined.

## System Call Filtering with Seccomp

Every meaningful action a process performs against the operating system eventually becomes a system call. Reading a file, creating a socket, changing ownership, asking for the current time, mapping memory, and starting another process all require a syscall boundary crossing from user space into the kernel. The Linux kernel exposes hundreds of these entry points, while a normal web service usually needs a much smaller subset to accept connections, read configuration, write logs, allocate memory, and serve responses.

```text
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

Seccomp is best understood as a syscall filter rather than a general sandbox. It does not know whether `/etc/passwd` is sensitive, whether a request came from a trusted customer, or whether an application version is vulnerable. It evaluates the syscall and its configured action, then allows it, denies it with an error, logs it, or kills the process depending on the profile and runtime behavior. That narrowness is a strength because it places a small, predictable guard at a high-value boundary.

The container runtime's `RuntimeDefault` seccomp profile is the practical baseline for most Kubernetes workloads. It blocks families of system calls commonly used for kernel manipulation, namespace creation, tracing, module loading, and other activities that ordinary application containers rarely need. Kubernetes 1.35 clusters should treat explicit `RuntimeDefault` as the minimum acceptable setting in manifests, even though modern Kubernetes releases default new Pods more safely than older clusters did, because explicit manifests survive migrations and make review easier.

Think about what an attacker does after gaining command execution in a web process. They often try to learn where they are, fetch tools, inspect credentials, trace processes, create namespaces, or interact with kernel features that were never part of the service's design. Seccomp does not need to understand the attacker's intent to frustrate several of those moves. It simply makes parts of the kernel vocabulary unavailable, so the exploit chain has fewer reliable verbs to use.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-nginx
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: nginx
    image: nginx:1.25.3
    securityContext:
      # You can also define it at the container level
      # which overrides the pod-level setting
      seccompProfile:
        type: RuntimeDefault
```

The Pod-level setting is useful when every container in the Pod should inherit the same syscall baseline. The container-level setting is useful when one sidecar has a different syscall profile than the main workload, but overrides should be rare enough to attract review. A common production mistake is to fix a crash by setting one container to `Unconfined`; that turns a local compatibility issue into a node-level attack surface issue, especially when the workload is exposed to untrusted input.

When a seccomp denial occurs, the symptom depends on the syscall, the profile action, and the application error handling. Some programs receive `EPERM` and log a clear permission problem, while others crash during initialization because a library assumes the syscall will always be available. That is why a good rollout plan includes representative traffic, startup tests, and audit log review instead of a single "container started" check. A profile that only survives the first health probe is not production evidence.

For very sensitive workloads, `RuntimeDefault` may still allow more than the application needs. A custom `Localhost` profile can make the default action deny and then allow a carefully profiled set of syscalls. This model is powerful, but it carries operational cost: the profile must exist on every eligible node, it must match the processor architecture, it must be updated when the application or base image changes, and it can fail in ways that look like ordinary application bugs.

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": [
    "SCMP_ARCH_X86_64",
    "SCMP_ARCH_X86",
    "SCMP_ARCH_X32"
  ],
  "syscalls": [
    {
      "names": [
        "accept4",
        "bind",
        "close",
        "epoll_ctl",
        "epoll_pwait",
        "listen",
        "read",
        "write"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

The profile above is intentionally strict because `SCMP_ACT_ERRNO` denies every syscall not listed. In real systems, you would build a candidate profile by observing the workload under representative traffic, running integration tests, reading audit logs, and then gradually tightening. If you profile only the happy path, your first production incident may discover that TLS reloads, DNS lookups, log rotation, or crash reporting need syscalls that never appeared during a simple health check.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-seccomp-pod
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: custom-profiles/strict-web.json
  containers:
  - name: web
    image: my-secure-app:v2
```

The `Localhost` reference is relative to the kubelet seccomp profile root on the node, commonly under `/var/lib/kubelet/seccomp/`. That is why custom profiles are easiest in controlled node pools and harder in clusters where nodes are replaced frequently by autoscaling. If a Pod can land on a node that lacks the profile, the kubelet cannot apply the promised boundary, so node labeling, runtime configuration management, and scheduling constraints become part of the security design.

Custom profiles are most defensible when they protect a small number of high-value workloads with stable behavior. A public reverse proxy, a signing service, or a payment component may justify the profiling effort because the attack surface reduction is meaningful and the workload changes carefully. A fast-moving internal batch job that changes base images every week may be a poor candidate, because the maintenance burden can push teams toward unsafe shortcuts when the profile breaks.

> **Stop and think**: If an attacker exploits a remote code execution vulnerability in your application and attempts to download a malware payload using `curl`, will a strict seccomp profile that only allows `read`, `write`, `open`, and `close` prevent the download? Why or why not?

The most precise answer is that seccomp would likely block the network operations needed by `curl`, but it would not block "downloading malware" as a human concept. It blocks specific syscalls such as socket creation, connection setup, DNS-related file access, or process execution depending on the profile. That distinction matters when writing policies, because runtime controls are strongest when you express them as concrete kernel behaviors instead of broad attacker goals.

Seccomp also pairs well with read-only filesystems and non-root execution because those controls frustrate different parts of the same post-exploitation path. A blocked socket creation may prevent a tool download, while a read-only root filesystem prevents writing into common binary locations, and non-root execution reduces the usefulness of filesystem ownership tricks. None of those controls proves the application is safe, but together they turn a remote code execution bug into a constrained process with fewer follow-on options.

## Mandatory Access Control: AppArmor and SELinux

Seccomp limits the verbs a process can use when speaking to the kernel, but Mandatory Access Control limits the objects that process can touch. On ordinary Linux discretionary access control, a process running as root can often bypass file permission checks or make changes that a non-root process cannot. MAC systems add a kernel-enforced policy layer that still applies when the process is root, which is exactly why they matter in container environments where "root inside the container" is easy to create accidentally.

```text
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

AppArmor is path-oriented and tends to feel approachable because a profile can say that a process may read one directory, write another directory, deny shell execution, and deny raw networking. That makes it attractive on Ubuntu, Debian, and SUSE fleets where the node operating system already supports it. Its operational edge is readability, but its limitation is that path-based policy requires careful thinking around mounted volumes, symlinks, generated files, and workload layouts that change between image versions.

The easiest way to misuse AppArmor is to treat a copied profile as a universal answer. A profile designed for NGINX static content may be reasonable for one container image and painfully wrong for another image that writes cache files, loads modules, or shells out during startup. Platform teams should version profiles like code, test them with the images they protect, and keep the profile name meaningful enough that a reviewer can connect the Pod annotation to an owned policy artifact.

```text
#include <tunables/global>

profile custom-nginx flags=(attach_disconnected) {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  # Allow read access to web content
  /usr/share/nginx/html/** r,
  
  # Allow read/write to specific log and cache directories
  /var/log/nginx/** rw,
  /var/cache/nginx/** rw,
  /run/nginx.pid rw,

  # Explicitly deny access to sensitive files
  deny /etc/passwd r,
  deny /etc/shadow r,
  deny /etc/kubernetes/** r,

  # Deny the ability to execute shells
  deny /bin/sh x,
  deny /bin/bash x,
  
  # Deny raw sockets (prevents certain types of network spoofing)
  deny network raw,
}
```

Profiles must be loaded into the worker node kernel before Pods can use them. Many teams distribute AppArmor profiles with a privileged DaemonSet or node image configuration, then reference the loaded profile from the Pod. Kubernetes has been moving AppArmor toward structured `securityContext` fields, but many production clusters still contain annotation-based examples because they supported the feature for years and remain common in platform runbooks.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: apparmor-protected
  annotations:
    container.apparmor.security.beta.kubernetes.io/web: localhost/custom-nginx
spec:
  containers:
  - name: web
    image: nginx:alpine
```

War story: during a red-team exercise, a Java service had a path traversal bug that allowed attackers to request files outside the intended content directory. The application ran as root in its container, so normal file ownership would not have been enough protection. The AppArmor profile denied reads from sensitive host and system paths, so the exploit still manipulated strings successfully, but the kernel rejected the file operation and produced audit evidence that defenders could investigate.

That story is also a reminder that MAC is not only about prevention. A well-named AppArmor or SELinux denial gives defenders a high-signal event because ordinary applications should not attempt to read Kubernetes node credentials, host configuration, or shadow password files. Runtime security observability from the previous module becomes more useful when the enforced profile is specific enough that a violation says something meaningful about the workload's behavior.

```text
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

SELinux enforces the same broad idea through labels rather than paths. Processes, files, directories, and sometimes ports receive security contexts with user, role, type, and level components. Container platforms on RHEL-family systems normally label container processes with a container type and assign Multi-Category Security labels so that two containers with similar permissions still cannot casually read each other's private volume content.

The label model can feel less intuitive at first because the policy decision is not written as a visible path rule in the Pod manifest. The payoff is that labels can travel with files and volumes in ways that are less brittle than raw paths. In Kubernetes, the difficult parts tend to appear around hostPath volumes, storage drivers, and migrations from non-SELinux systems, where files may carry labels that do not match the container process context.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: selinux-custom-pod
spec:
  securityContext:
    seLinuxOptions:
      level: "s0:c99,c100"
  containers:
  - name: worker
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      seLinuxOptions:
        type: "container_t"
        user: "system_u"
        role: "system_r"
```

The practical difference is visible during troubleshooting. AppArmor failures often lead you toward profile names and denied paths, while SELinux failures lead you toward process labels, file labels, and audit messages that explain a type enforcement denial. A Kubernetes operator does not choose between them per Pod like choosing an image tag; the worker node operating system and kernel security module decide which MAC system is available, and Pod manifests must match that reality.

When a team reports "permission denied" from a volume mount, resist the urge to fix only Unix ownership. The user ID, group ID, filesystem mode, SELinux label, AppArmor profile, and storage provider behavior can all participate in the final decision. Good diagnosis asks which layer denied the access, because changing `fsGroup` may solve a discretionary permission issue but do nothing for an SELinux type mismatch.

Which approach would you choose here and why: an Ubuntu node pool running internet-facing NGINX ingress, or a RHEL node pool running regulated financial workloads with existing SELinux operations expertise? The right answer is less about which acronym sounds stronger and more about which enforcement model your platform team can deploy, observe, tune, and repair during an outage.

For KCSA-level practice, focus on recognizing the boundary each MAC system enforces and the operational prerequisite it requires. AppArmor requires loaded profiles and a compatible node kernel. SELinux requires correct labels and policy support on the node. Kubernetes exposes hooks for both, but it cannot make an unsupported kernel module enforce policy, and it cannot make a mislabeled host directory safe by wishful manifest design.

## Deconstructing Root with Capabilities

Linux capabilities exist because the old root-versus-not-root model was too blunt. Historically, a process that needed one privileged operation, such as binding to a low-numbered port, often had to run as root and received many unrelated powers at the same time. Capabilities split that bundle into narrower privileges, so Kubernetes can remove most of root's power even when an image still starts a process with user ID zero.

```text
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

Container runtimes usually start containers with a limited default capability set, not with every possible root privilege. That default is safer than an unrestricted root process, but it is still broader than many applications need. `CAP_NET_RAW` can support packet crafting and network spoofing; `CAP_DAC_OVERRIDE` can bypass normal file permission checks; `CAP_SYS_ADMIN` is so broad that teams should treat it as a privileged-mode warning unless there is a very specific kernel-facing reason.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: capability-tuned-pod
spec:
  containers:
  - name: application
    image: my-golang-service:1.0
    securityContext:
      capabilities:
        drop:
          - ALL
        add:
          - NET_BIND_SERVICE
```

The safest default is `drop: ["ALL"]`, followed by explicit additions only after the application proves it needs them. A service listening on port 8080 does not need `NET_BIND_SERVICE`, because the port is not privileged. A packet capture troubleshooting container may need `NET_RAW` and often `NET_ADMIN`, but that should be a temporary, isolated debugging tool rather than a capability set copied into every application deployment.

Capability design is where least privilege becomes concrete. Instead of saying "this container is secure," you ask whether the process needs to change file ownership, bypass file permissions, create device nodes, trace other processes, administer networking, or bind to privileged ports. Most application services need none of those abilities. When one does need an ability, the manifest should make that exception obvious enough that a future reviewer can challenge it.

> **Pause and predict**: You drop `ALL` capabilities on a container running `tcpdump` for network troubleshooting. The container immediately crashes on startup. Which specific capability must you add back for `tcpdump` to function, and why does dropping it break the application?

Capability failures are often diagnosed by combining application errors, runtime events, and a small reproduction. If a process reports "operation not permitted" while binding to port 80, `NET_BIND_SERVICE` is a candidate. If a process fails to change routing tables, `NET_ADMIN` is more likely. If a tool cannot inspect another process, `SYS_PTRACE` may be involved, but adding it to an ordinary application container would create a serious lateral inspection risk.

The hard part is that many permission errors look alike to application owners. A developer may not know whether `EPERM` came from a missing capability, a seccomp denial, an AppArmor rule, an SELinux label, or a read-only filesystem. Platform teams can reduce confusion by documenting a triage checklist: inspect Pod events, review admission responses, check kernel audit logs, look at the container security context, and reproduce with the smallest temporary exception before changing production policy.

The companion control is `allowPrivilegeEscalation: false`, which sets Linux `no_new_privs` behavior for the container process. That setting prevents a process from gaining more privileges through setuid binaries or similar execution transitions. It does not replace dropping capabilities, running as non-root, or using seccomp, but it closes a common path where an attacker searches the image for a forgotten helper binary and tries to turn a small foothold into a stronger one.

This is why hardened images and hardened Pod specs should be reviewed together. Removing setuid binaries from the image is better than merely depending on `no_new_privs`, but `allowPrivilegeEscalation: false` protects you when an image contains something unexpected. Likewise, running as non-root reduces the starting privilege, while dropping capabilities reduces the special kernel powers that may remain. The controls overlap in purpose but not in exact enforcement.

## Policy Engines and Admission Guardrails

Runtime security fields protect a Pod only after someone has put those fields into the manifest or a mutating admission controller has added them. In a small cluster, a careful platform engineer might review every manifest by hand, but that model fails as soon as multiple teams, Helm charts, operators, and generated manifests arrive. Admission policy turns the security baseline from a style guide into an API contract.

Admission control should be designed with developer feedback in mind. A rejected Pod should explain what field violated the baseline and how to fix it, because unclear rejection messages train teams to look for bypasses. The best policies are boring in daily use: they catch insecure defaults, point to a clear remediation, and provide a documented exception path for workloads that genuinely need unusual privileges.

```text
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

OPA Gatekeeper is powerful when an organization wants reusable constraints backed by Rego logic. A `ConstraintTemplate` defines the policy machinery, and a `Constraint` applies that machinery to selected resource kinds, namespaces, or parameters. This split is valuable for platform teams that need consistent policy primitives, but it also means the team must maintain Rego expertise and test policies carefully before they become a production admission dependency.

Gatekeeper is a strong fit when policy logic needs expressive evaluation across arbitrary Kubernetes resources or when an organization already uses Open Policy Agent elsewhere. For example, a platform team might enforce registry allowlists, namespace ownership labels, or custom relationships between workload annotations and service accounts. Those policies can complement runtime security, but they should be tested like application code because a broken validating webhook can block legitimate cluster changes.

```text
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

Kyverno uses Kubernetes-flavored YAML and is often easier for application and platform teams to read together. It can validate that a Pod sets `runAsNonRoot`, mutate a missing `seccompProfile` into place, generate supporting resources, and verify image signatures. That accessibility does not remove the need for discipline, because mutating security fields can surprise developers unless the platform documents what gets changed and how exceptions are requested.

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: disallow-root-user
spec:
  validationFailureAction: Enforce
  background: true
  rules:
  - name: validate-runAsNonRoot
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Running as root is not allowed. Set runAsNonRoot to true."
      pattern:
        spec:
          securityContext:
            runAsNonRoot: true
          containers:
          - =(securityContext):
              =(runAsNonRoot): true
```

This policy rejects Pods that fail to declare non-root execution in the expected places. In real clusters, teams often begin with audit mode, collect violations, fix the most common chart templates, and then move high-confidence rules into enforcement. That progression matters because a policy engine that blocks emergency deployments without a tested exception path will be bypassed politically even if it is technically correct.

Mutation requires even more care than validation. Adding `RuntimeDefault` automatically may be a reasonable platform default because the field is low risk for most workloads, but mutating user IDs, volume mounts, or capabilities can break applications in ways that surprise owners. If you mutate security settings, expose the final rendered object through review tooling or policy reports so developers can see the security context their Pod actually received.

Before running this, what output do you expect from `k apply -f root-pod.yaml` if the Kyverno policy is already enforced? You should expect an admission rejection from the API server, not a Pod that starts and then crashes, because the policy engine evaluates the object before the kubelet ever creates a container.

Do not use both Kyverno and Gatekeeper to enforce the same field unless you have a specific migration plan or failure-domain reason. Duplicate checks create two sources of truth, two styles of error messages, and two places where exceptions can drift. Defense in depth is usually better expressed by layering different controls, such as Pod Security Admission for broad baseline behavior, one policy engine for organization-specific rules, and kernel enforcement for the running process.

## RuntimeClass and Sandboxed Runtimes

Seccomp, capabilities, and MAC all reduce what a process can do to a shared kernel, but standard OCI runtimes still share that kernel. For trusted internal services, that is usually a reasonable tradeoff because runc and crun are fast, well understood, and compatible with the broad Kubernetes ecosystem. For untrusted code execution, customer plugins, browser automation at scale, or multi-tenant CI workloads, the shared-kernel assumption deserves much more scrutiny.

```text
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

gVisor inserts a user-space kernel called the Sentry between the application and the host kernel. When the application makes a syscall, gVisor intercepts and implements much of the expected kernel behavior outside the host kernel's direct syscall path. This can reduce exposure to host kernel bugs, but it may add overhead and compatibility gaps for workloads that rely on unusual kernel features, low-level networking behavior, or performance-sensitive syscall patterns.

That compatibility tradeoff is why sandboxed runtimes should be introduced with a workload qualification process. A simple HTTP service may run with little drama, while a build runner that uses nested tooling, special filesystems, or advanced networking may expose missing behavior quickly. The right pilot includes performance measurements, syscall-heavy tests, and clear rollback steps, not only a successful Pod creation event.

Kata Containers takes a different route by running Pods inside lightweight virtual machines with their own guest kernels. That gives a stronger isolation boundary for teams that need hardware virtualization as part of their risk model, at the cost of higher startup and resource overhead than a normal runc container. The design question is therefore not "which runtime is most secure" in isolation; it is whether the workload's trust level justifies the operational and performance cost.

Kata is especially relevant when auditors, tenant isolation requirements, or internal risk models demand a VM-like boundary while retaining Kubernetes scheduling and workflow. It does not remove the need for image hygiene, network policy, admission control, or least-privilege Pod specs. A vulnerable application inside a micro-VM can still leak its own data or attack reachable services, even if the host kernel is better protected.

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
# The handler matches the runtime configured in containerd/CRI-O on the node
handler: runsc 
---
apiVersion: v1
kind: Pod
metadata:
  name: untrusted-customer-script
spec:
  runtimeClassName: gvisor
  containers:
  - name: runner
    image: python:3.11-alpine
```

`RuntimeClass` lets Kubernetes select a runtime handler configured on the node's container runtime. The manifest alone is not enough; containerd or CRI-O must know what `runsc` or the Kata handler means, the node must have the required runtime installed, and scheduling must keep those Pods on compatible nodes. If a platform offers sandboxing as a service to application teams, it should publish runtime classes with clear names, documented limitations, and example manifests that include the normal security context controls as well.

Scheduling is part of the runtime boundary. If only some nodes support gVisor, a `RuntimeClass` can include scheduling hints or the platform can pair it with node selectors, taints, and admission checks. Without that coordination, teams may see confusing failures where the manifest is valid but no compatible node can actually run the Pod. Runtime isolation is therefore a platform feature, not just a line in a workload YAML file.

A useful rule is to reserve sandboxed runtimes for a trust boundary, not for a vague feeling of importance. A payment API that your organization writes, scans, deploys, and monitors may be better served by runc plus strict least privilege. A hosted build runner executing arbitrary customer scripts should use stronger isolation because the business model assumes hostile input from the start.

The same trust-tier thinking helps control cost. If every Pod receives the heaviest runtime, teams may pay unnecessary overhead and then pressure the platform to relax the standard. If only the riskiest workloads receive stronger isolation, the platform can focus testing and capacity planning where the security return is highest. Clear tier definitions make that tradeoff explicit before an incident forces a rushed migration.

## Patterns & Anti-Patterns

Runtime security works best when teams treat it as a productized platform capability instead of a collection of heroic manifest tweaks. The patterns below are deliberately operational: they describe how controls survive chart upgrades, incident pressure, new node pools, and different workload trust levels. The anti-patterns are common because they feel convenient in the moment, especially when a production workload is broken and the fastest local fix is to remove the control that exposed the issue.

Notice that the patterns are not exotic. They mostly turn implicit runtime behavior into explicit, reviewable, testable configuration. The hard work is consistency: getting every service template, operator, and exception process to express the same baseline without forcing teams to memorize every kernel detail. That is why the most successful platforms pair strict defaults with practical documentation and fast support for legitimate edge cases.

| Pattern | When to Use | Why It Works | Scaling Consideration |
|---------|-------------|--------------|-----------------------|
| Default-deny capability posture | Most application workloads that do not need kernel administration privileges | Dropping all capabilities turns privilege into an explicit design choice rather than runtime inheritance | Keep exception examples small and reviewed, because copied capability blocks spread quickly through Helm values |
| RuntimeDefault everywhere | General workloads on Kubernetes 1.35+ clusters | The runtime's maintained seccomp baseline blocks dangerous kernel entry points without requiring custom profiling | Enforce with admission so forgotten security contexts do not become the common case |
| MAC profiles for high-risk paths | Ingress controllers, node agents, and services handling untrusted file paths | AppArmor or SELinux still constrains root processes when normal permissions are not enough | Match the profile model to the node OS and keep audit logs searchable during rollout |
| RuntimeClass by trust tier | Customer code execution, hosted CI, plugin systems, and compliance-sensitive tenants | Sandboxed runtimes move untrusted code away from direct host-kernel reliance | Publish compatibility notes and schedule only onto nodes with the handler installed |

| Anti-Pattern | What Goes Wrong | Why Teams Fall Into It | Better Alternative |
|--------------|-----------------|------------------------|--------------------|
| Setting `Unconfined` after one crash | The workload starts, but a broad syscall boundary disappears for every future exploit | The error looks like an application failure and the deadline is close | Profile the denied syscall, use a narrow `Localhost` profile, or adjust the application design |
| Adding `CAP_SYS_ADMIN` as a universal fix | A near-root privilege enters the container and invalidates much of the least-privilege model | Many unrelated operations fail with similar permission messages | Identify the exact capability or redesign the workload to avoid host administration |
| Mixing duplicate policy engines for the same field | Developers see confusing rejection messages and API admission latency rises | "Defense in depth" is interpreted as repeating identical checks | Assign clear ownership, such as Kyverno for Pod security and Gatekeeper for custom organization rules |
| Treating sandboxed runtime as a silver bullet | Compatibility problems, cost increases, and weak Pod security contexts remain unsolved | Strong isolation sounds like it should replace lower-level controls | Use sandboxing for trust boundaries while keeping seccomp, capabilities, and MAC in place |

## Decision Framework

Choose runtime controls by starting with the workload's trust model, then work downward into kernel permissions and upward into policy enforcement. A service maintained by your team and exposed only through normal ingress still needs least privilege, but it probably does not need a micro-VM per Pod. A customer-submitted script runner starts from the opposite assumption: the code may be hostile by design, so the runtime boundary needs to be stronger before you discuss convenience.

```text
START
  |
  v
Is the workload executing untrusted customer or tenant code?
  |-- yes --> Use RuntimeClass for gVisor or Kata, then still enforce least privilege.
  |
  |-- no --> Does it need host namespaces, privileged mode, or broad capabilities?
              |-- yes --> Treat as node-adjacent infrastructure; isolate nodes and review manually.
              |
              |-- no --> Use RuntimeDefault, drop all capabilities, run as non-root, and enforce by policy.
```

| Decision | Prefer This | Avoid This | Reasoning |
|----------|-------------|------------|-----------|
| Syscall baseline | `RuntimeDefault` for most Pods | `Unconfined` as a compatibility shortcut | The runtime default removes dangerous kernel entry points with low operational cost |
| Custom syscall profile | `Localhost` after profiling and node distribution | Handwritten deny lists with no test coverage | Default-deny profiles are brittle unless exercised under realistic traffic |
| MAC selection | AppArmor on AppArmor-capable distributions, SELinux on RHEL-family distributions | Manifests that assume the wrong node security module | The kernel cannot enforce a module that the node does not run |
| Capabilities | `drop: ["ALL"]` plus exact additions | Default capabilities copied into every chart | Least privilege is easier to review when additions are rare and named |
| Runtime choice | runc for trusted workloads, gVisor or Kata for untrusted code | One runtime for every risk tier | Runtime overhead should track the value of the isolation boundary |
| Admission | One clear policy owner per security domain | Duplicate rules across engines without ownership | Operators need predictable rejection messages and exception paths |

The framework also gives you a debugging sequence. If the API server rejects the object, inspect admission policy and Pod Security settings first. If the Pod starts and the process receives `EPERM`, inspect seccomp, capabilities, `allowPrivilegeEscalation`, and MAC audit logs. If a workload behaves differently only on some nodes, inspect node labels, runtime handler configuration, profile distribution, and operating system security modules.

When you are unsure which control to tighten first, prefer the broad, low-risk defaults before custom engineering. Run as non-root, disable privilege escalation, drop capabilities, use `RuntimeDefault`, make the root filesystem read-only where the application permits, and block host namespaces. Once those are routine, add MAC profiles for workloads with meaningful file access risk and sandboxed runtimes for workloads that cross trust boundaries. This sequence gives teams visible wins without making the first rollout depend on custom kernel policy for every service.

## Did You Know?

- **Kubernetes enabled `RuntimeDefault` seccomp by default in version 1.27**, which means Kubernetes 1.35+ operators inherit a safer baseline than older clusters but should still declare it explicitly for reviewability.
- **gVisor's Sentry is written in Go and implements a substantial user-space kernel surface**, so many application syscalls are handled before they can directly reach the host kernel.
- **SELinux labels commonly include four fields in the form `user:role:type:level`**, and the `type` and MCS level are especially important for container process and volume isolation.
- **`CAP_SYS_ADMIN` is intentionally broad enough that kernel documentation has long described it as overloaded**, so adding it to a container should trigger the same scrutiny as privileged mode.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Leaving Pods effectively unconfined | Teams rely on cluster defaults or old manifests and never verify the resulting seccomp profile | Set `seccompProfile: type: RuntimeDefault` explicitly and enforce the baseline through admission policy |
| Retaining default capabilities | The application works during development, so nobody notices the inherited privilege set | Use `drop: ["ALL"]`, add only proven requirements, and document each addition in the workload review |
| Applying AppArmor manifests to SELinux nodes | Engineers copy examples from Ubuntu clusters into RHEL-family environments | Match MAC controls to the node operating system and use `seLinuxOptions` where SELinux is the enforcing module |
| Enforcing custom profiles without audit rollout | A strict profile blocks a rare but legitimate path that tests did not cover | Start with audit or complain behavior where possible, review logs, then enforce after representative traffic |
| Using one runtime for every tenant | Standardization feels simpler than maintaining runtime classes and node pools | Define runtime classes by trust level and schedule untrusted workloads only onto compatible sandbox nodes |
| Adding `CAP_SYS_ADMIN` to solve vague permission errors | Many kernel operations fail with similar "operation not permitted" messages | Reproduce the failure, identify the exact capability or syscall, and prefer application redesign when possible |
| Depending only on namespaces for containment | Namespace isolation looks strong because the process view is limited | Layer namespaces with seccomp, capabilities, MAC, read-only filesystems, and admission policy |
| Duplicating the same validation in Kyverno and Gatekeeper | Teams confuse repeated checks with stronger defense | Assign each policy domain to one engine and use monitoring plus tests to verify that enforcement works |

## Quiz

<details>
<summary>1. Your team deploys a Go API on Kubernetes 1.35 with `runAsNonRoot`, `readOnlyRootFilesystem`, and dropped capabilities, but the manifest omits `seccompProfile`. A reviewer asks whether this is acceptable because modern clusters already default seccomp more safely. How should you respond?</summary>

The workload may receive a safer default on a modern cluster, but the manifest should still declare `seccompProfile: type: RuntimeDefault`. Explicit configuration makes the intended boundary visible during review, survives migration to clusters with different defaults, and gives admission policy a clear field to validate. The other security context settings are valuable, but they do not replace syscall filtering because capabilities and filesystem flags control different kernel behaviors.
</details>

<details>
<summary>2. A RHEL-based node pool ignores an AppArmor annotation that worked in a previous Ubuntu cluster, and the container can still read files the team expected to deny. What is the most likely architecture problem, and how do you correct the design?</summary>

The likely problem is that the node pool uses SELinux rather than AppArmor as its Mandatory Access Control system. AppArmor annotations cannot enforce path policy if the node kernel is not running AppArmor for containers, so the manifest gives a false sense of protection. Correct the design by using SELinux labels and `seLinuxOptions`, or by scheduling the workload to an AppArmor-capable node pool with the required profiles loaded.
</details>

<details>
<summary>3. A legacy application crashes after moving from an unconfined seccomp profile to `RuntimeDefault`, and audit evidence points to the blocked `unshare` syscall. The business wants the app online without returning to fully unconfined execution. What strategy should you propose?</summary>

Start by confirming that the application genuinely needs `unshare` and that the behavior cannot be removed or isolated into a safer helper. If the requirement is real, build a custom seccomp profile from the runtime default, add only the required syscall, distribute that profile to the intended nodes, and reference it with `type: Localhost`. This preserves most of the runtime default protections while making the exception explicit and testable.
</details>

<details>
<summary>4. A hosted CI service runs arbitrary customer shell scripts in Pods using runc, `RuntimeDefault`, dropped capabilities, and non-root users. A new local kernel privilege escalation vulnerability is announced. Are these customer Pods adequately isolated from the host kernel?</summary>

They are better hardened than default Pods, but they are not adequately isolated for arbitrary hostile code if the threat is a host kernel vulnerability. With runc, the containers still share the worker node kernel, so a successful kernel exploit can cross beneath seccomp and capability boundaries. A service that intentionally executes untrusted customer code should evaluate gVisor or Kata through `RuntimeClass`, while keeping the existing least-privilege settings as additional layers.
</details>

<details>
<summary>5. A developer adds `CAP_SYS_ADMIN` because their container receives "operation not permitted" while starting a filesystem-heavy tool. The Pod now runs, and the team wants to merge the change. What should you check before approving?</summary>

You should treat `CAP_SYS_ADMIN` as a major privilege expansion rather than a routine compatibility flag. Reproduce the failure, identify the exact kernel operation, check whether a narrower capability or different volume design solves the problem, and decide whether the workload belongs on isolated nodes if it truly needs broad host-facing power. Approval should require a documented reason because this capability weakens the containment story for future compromises.
</details>

<details>
<summary>6. A Kyverno policy rejects a Pod before it is scheduled, but the application team keeps searching container logs for an explanation and finds nothing. How do you redirect the investigation?</summary>

There will be no container logs because the Pod never reached the kubelet and no container process started. The investigation should move to the API server response, the Kyverno policy report, admission controller logs, and the manifest fields matched by the rule. This distinction matters operationally because admission failures are configuration contract failures, while runtime denials leave evidence in kubelet events, application errors, or kernel audit logs.
</details>

<details>
<summary>7. A hardened API runs as user 10001 with all capabilities dropped, but a penetration test finds a setuid helper binary inside the image. Which security context setting limits the danger, and why is it not enough by itself?</summary>

`allowPrivilegeEscalation: false` limits the danger by setting `no_new_privs`, which prevents the process and its children from gaining additional privileges through setuid or similar execution transitions. It is not enough by itself because the image still contains unnecessary risky software, and other attack paths may not depend on setuid behavior. The correct response is to keep the setting, remove the helper from the image, run as non-root, drop capabilities, and use filesystem and syscall restrictions.
</details>

## Hands-On Exercise: Engineering a Hardened Security Context

You are migrating a critical backend API service to a Kubernetes 1.35 production cluster. The service is written in Go, listens on port 8080, reads configuration from a mounted volume, writes temporary processing data, and does not need host namespaces, raw sockets, tracing, filesystem administration, or low-numbered port binding. Your objective is to construct a Pod manifest that expresses least privilege clearly enough for a reviewer and strict enough for an attacker to find very little room after compromise.

Use a scratch file named `runtime-lab.yaml` and apply it with `k apply -f runtime-lab.yaml` when you are ready to test. If your cluster has Pod Security Admission or Kyverno policies enabled, compare the API server response with your expectations before changing the manifest, because a rejection may mean your platform is already enforcing part of the baseline.

The exercise is intentionally centered on a normal service rather than a privileged daemon. Most Kubernetes security work is not about rare node agents that truly need unusual access; it is about making the default application path boringly safe. If you can harden this API without breaking its basic needs, you can use the same reasoning when reviewing Helm values, generated manifests, or pull requests from application teams.

**Requirements Checklist:**

- [ ] The application must run as a non-root user with user ID 10001 and group ID 10001.
- [ ] The application must be explicitly prevented from escalating privileges through setuid or similar transitions.
- [ ] The root filesystem must be read-only, with a writable temporary directory mounted at `/tmp/workdir`.
- [ ] All Linux capabilities must be dropped because the service listens on port 8080 and needs no privileged port binding.
- [ ] The runtime default seccomp profile must be declared explicitly.
- [ ] Host process, network, and IPC namespaces must remain disabled.

**Task 1:** Draft the Pod structure, name the container, and set `hostNetwork`, `hostPID`, and `hostIPC` so the Pod cannot view or join host namespaces.

**Task 2:** Configure the Pod-level `securityContext` with non-root identity, group ownership for mounted files, and the explicit runtime seccomp profile.

**Task 3:** Configure the container-level `securityContext` with `allowPrivilegeEscalation: false`, `privileged: false`, a read-only root filesystem, and a capability set that drops everything.

**Task 4:** Add an `emptyDir` volume and mount it at `/tmp/workdir` so the application has a deliberate writable location while the image filesystem remains immutable.

**Task 5:** Apply the manifest, inspect the resulting Pod with `k describe pod hardened-api-service`, and explain whether a failure came from admission, image pulling, or runtime enforcement.

<details>
<summary>View the Solution and Explanation</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hardened-api-service
  labels:
    app: api-backend
spec:
  # Task 1: Prevent host namespace access
  hostNetwork: false
  hostPID: false
  hostIPC: false

  # Task 2: Pod-level security context
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001
    # Apply standard syscall filtering
    seccompProfile:
      type: RuntimeDefault

  containers:
  - name: api-service
    image: my-company/backend-api:v2.4.1
    ports:
    - containerPort: 8080

    # Task 3: Container-level security context
    securityContext:
      # Prevent privilege escalation (no_new_privs)
      allowPrivilegeEscalation: false
      # Ensure container is not privileged
      privileged: false
      
      # Enforce immutability
      readOnlyRootFilesystem: true
      
      # Drop all capabilities. Since the app listens on 8080 
      # (an unprivileged port > 1024), we do not need NET_BIND_SERVICE.
      capabilities:
        drop:
          - ALL

    # Task 4: Provide explicit writable areas
    volumeMounts:
    - name: tmp-workdir
      mountPath: /tmp/workdir

  volumes:
  - name: tmp-workdir
    emptyDir: {}
```

This configuration layers several independent protections. The process runs as user 10001 rather than root, cannot gain new privileges through setuid execution, cannot write into the image filesystem, and has no Linux capabilities left to spend after compromise. The Pod also declares the runtime default seccomp filter and refuses host namespaces, so an attacker who reaches the Go process cannot casually inspect host processes, use broad kernel privileges, or persist changes into the container image layer.

The manifest is intentionally strict but not magical. If the application expects to write under `/var/cache`, it will fail until you either change the application path or mount a deliberate writable volume there. If the image requires root during startup, the non-root setting will expose that packaging problem. Those failures are useful because they move privilege decisions into reviewable YAML instead of leaving them hidden inside a container startup script.
</details>

Success criteria:

- [ ] `k apply -f runtime-lab.yaml` creates the Pod or returns a policy message you can explain precisely.
- [ ] `k get pod hardened-api-service -o yaml` shows `seccompProfile.type: RuntimeDefault`.
- [ ] The container security context shows `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`, and `capabilities.drop` containing `ALL`.
- [ ] The Pod spec shows `hostNetwork: false`, `hostPID: false`, and `hostIPC: false`.
- [ ] You can explain which setting prevents setuid escalation and which setting reduces the syscall attack surface.

## Next Module

[Module 5.4: Security Tooling](../module-5.4-security-tooling/) - Now that you understand the low-level primitives of runtime security, you will examine tools such as Falco and Trivy that observe, verify, and automate these controls at scale.

## Sources

- [Kubernetes Documentation: Configure a Security Context for a Pod or Container](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [Kubernetes Documentation: Restrict a Container's Syscalls with seccomp](https://kubernetes.io/docs/tutorials/security/seccomp/)
- [Kubernetes Documentation: Seccomp default tutorial](https://kubernetes.io/docs/tutorials/security/seccomp-default/)
- [Kubernetes Documentation: Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes Documentation: RuntimeClass](https://kubernetes.io/docs/concepts/containers/runtime-class/)
- [Kubernetes Documentation: AppArmor](https://kubernetes.io/docs/tutorials/security/apparmor/)
- [Linux manual page: capabilities](https://man7.org/linux/man-pages/man7/capabilities.7.html)
- [Linux kernel documentation: Seccomp BPF](https://docs.kernel.org/userspace-api/seccomp_filter.html)
- [Red Hat Documentation: Using SELinux](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/using_selinux/index)
- [gVisor Documentation: Architecture Guide](https://gvisor.dev/docs/architecture_guide/)
- [Kata Containers Documentation: What is Kata Containers?](https://katacontainers.io/docs/)
- [Kyverno Documentation: Validate Rules](https://kyverno.io/docs/policy-types/cluster-policy/validate/)
- [Open Policy Agent Gatekeeper Documentation](https://open-policy-agent.github.io/gatekeeper/website/docs/)
