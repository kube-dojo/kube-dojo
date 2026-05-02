---
title: "Module 3.1: Pod Security"
slug: k8s/kcsa/part3-security-fundamentals/module-3.1-pod-security
sidebar:
  order: 2
revision_pending: false
---

> **Complexity**: `[MEDIUM]` - Core knowledge for engineers who need to evaluate pod runtime risk and admission behavior
>
> **Time to Complete**: 40-50 minutes of reading, manifest review, and practical remediation work
>
> **Prerequisites**: [Module 2.4: PKI and Certificates](/k8s/kcsa/part2-cluster-component-security/module-2.4-pki-certificates/), plus basic comfort reading Pod YAML and namespace labels

## What You'll Be Able to Do

After completing this module, you will be able to review real Pod manifests, diagnose Pod Security Admission behavior, and explain the security tradeoffs behind each recommended change:

1. **Evaluate** Pod and container `securityContext` settings to separate acceptable hardening choices from configurations that enable privilege escalation, host access, or persistence.
2. **Compare** the `privileged`, `baseline`, and `restricted` Pod Security Standards profiles and recommend the least permissive profile that fits a workload class.
3. **Debug** Pod Security Admission rejections and warnings by mapping the API response back to the exact field that violates the namespace policy.
4. **Design** a hardened pod specification that runs as non-root, drops unnecessary Linux capabilities, uses seccomp, and preserves application functionality with explicit writable paths.
5. **Assess** when a workload exception is justified, then contain that exception with namespace labels, workload isolation, and documented compensating controls.

## Why This Module Matters

A platform team inherits a cluster where every application namespace allows privileged pods because one monitoring agent needed host access years ago. Months later, a vulnerable web application is compromised, and the attacker discovers that the container can run as root, add broad Linux capabilities, write to its filesystem, and share the node network. The original application bug was ordinary; the blast radius became dangerous because the pod was allowed to behave like part of the host.

Pod security is the boundary between "the attacker controls one process" and "the attacker can interact with the node." Kubernetes does not make every pod safe by default, because many legitimate system components need powerful access to networking, devices, or host namespaces. That flexibility is useful for cluster operators, but it means application teams must learn which fields are routine hardening, which fields are exceptions, and which fields should trigger a design review.

The business impact is not theoretical. In incident reviews, the expensive part is often not the original remote code execution bug; it is the investigation, credential rotation, node rebuilds, emergency firewall work, and customer-facing downtime caused by unclear containment. If a compromised pod can only write to `/tmp` and speak through the application network path, responders have one kind of night. If the same pod can inspect host processes, mount sensitive host paths, or load kernel-facing tools, responders must assume the node boundary is suspect and widen the incident.

This module teaches pod security as a decision process rather than a checklist. You will first build a mental model of where pod controls apply, then inspect common dangerous fields, then connect those fields to Pod Security Standards and Pod Security Admission. By the end, you should be able to look at a pod manifest and explain not only whether it is allowed, but why the risk exists and how to reduce it without breaking the workload.

## Pod Security Starts With Boundaries

A container is isolated by Linux kernel features such as namespaces, cgroups, capabilities, and seccomp filters. Kubernetes exposes many of those controls through the Pod spec so teams can decide how much of the host a workload should be allowed to see or influence. The important idea is that pod security is not a single switch; it is a set of layers that either preserve or weaken isolation.

```text
┌───────────────────────────────────────────────────────────────┐
│                    POD SECURITY LAYERS                        │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  POD-LEVEL SETTINGS                                           │
│  Apply to the whole pod unless a container overrides them      │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ securityContext:                                       │  │
│  │   runAsUser, runAsGroup, fsGroup                       │  │
│  │   seccompProfile                                       │  │
│  │ hostNetwork, hostPID, hostIPC                          │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  CONTAINER-LEVEL SETTINGS                                     │
│  Apply to one container and can be more specific               │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ securityContext:                                       │  │
│  │   runAsUser, runAsNonRoot                              │  │
│  │   readOnlyRootFilesystem                               │  │
│  │   allowPrivilegeEscalation                             │  │
│  │   capabilities, privileged, seccompProfile             │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ADMISSION ENFORCEMENT                                        │
│  Decides whether the API server accepts the pod                │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Pod Security Standards                                  │  │
│  │ Pod Security Admission                                  │  │
│  │ Optional policy engines such as Kyverno or Gatekeeper   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

A useful way to reason about a pod is to ask three questions in order. First, what identity does the process run as inside the container? Second, what extra kernel privileges does that process receive? Third, what parts of the host does the pod share or mount? Most dangerous pod configurations are risky because they answer one of those questions too generously.

For example, a pod that runs as UID `0` is not automatically a host compromise, but it is a larger starting point for an attacker. A pod that runs as UID `0`, keeps default capabilities, allows privilege escalation, and mounts host paths is much closer to a node-level problem. Kubernetes security is often about preventing those small permissions from stacking into a serious escape path.

Think of these settings like the keys issued to a contractor entering a secure building. A badge for one office is different from a badge for the server room, and both are different from a master key plus permission to disable alarms. Pod security works the same way: the review must consider the combination of identity, capabilities, namespaces, volumes, and admission labels. A field that looks manageable alone can become dangerous when paired with another field that removes a separate layer of isolation.

> **Stop and think**: A developer argues that their container needs `privileged: true` because it must bind to port `80`. Before reading further, decide whether that justification is valid and name the smallest permission that would solve the stated problem.

The minimum-privilege answer is usually `NET_BIND_SERVICE`, not `privileged: true`. Binding to ports below `1024` is controlled by a specific Linux capability, so granting every capability and device on the host would be a poor trade. This pattern appears often in security reviews: the workload has a real need, but the proposed permission is much broader than the need.

That distinction matters on the KCSA exam and in production reviews because Kubernetes gives you several ways to meet the same application requirement. A Service can expose port `80` while the container listens on `8080`. A non-root image can own the directories it actually needs. An `emptyDir` can provide scratch space without making the image filesystem mutable. The skill is not memorizing every possible field; the skill is matching a need to the smallest Kubernetes or Linux mechanism that satisfies it.

## SecurityContext: The Main Control Surface

The `securityContext` field is where Kubernetes lets you set user identity, filesystem behavior, privilege escalation rules, Linux capabilities, and seccomp profile selection. It can appear at the pod level and at the container level. Pod-level settings are convenient defaults, while container-level settings are useful when an init container or sidecar needs something different from the main application.

A hardened container spec usually starts by removing broad permissions before adding narrow exceptions. The following manifest is intentionally small enough to study field by field. It uses `kubectl`, commonly aliased as `k`; after the first command, this module uses `k` in examples to match common exam and operations practice.

```bash
kubectl create namespace pod-security-demo
alias k=kubectl
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-web
  namespace: pod-security-demo
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: web
      image: nginx:1.27
      ports:
        - containerPort: 8080
      securityContext:
        runAsNonRoot: true
        readOnlyRootFilesystem: true
        allowPrivilegeEscalation: false
        privileged: false
        capabilities:
          drop:
            - ALL
      volumeMounts:
        - name: cache
          mountPath: /var/cache/nginx
        - name: run
          mountPath: /var/run
        - name: tmp
          mountPath: /tmp
  volumes:
    - name: cache
      emptyDir: {}
    - name: run
      emptyDir: {}
    - name: tmp
      emptyDir: {}
```

This manifest separates security intent from application needs. The root filesystem is read-only, but NGINX still receives writable directories for runtime files through `emptyDir` volumes. The process runs as a non-root UID, privilege escalation is disabled, and Linux capabilities are dropped. The seccomp profile is set to `RuntimeDefault`, which gives the container runtime a chance to block dangerous system calls without requiring the learner to write a custom profile.

Notice that the pod-level `securityContext` expresses defaults shared by the pod, while the container-level block expresses constraints specific to the `web` process. This division is more than style. Pod-level identity settings reduce repetition and make the manifest easier to scan, but container-level settings are still required for controls such as `readOnlyRootFilesystem`, `allowPrivilegeEscalation`, `privileged`, and capabilities. Reviewers should therefore read both levels as one combined policy rather than treating either block as complete by itself.

The writable mounts are also part of the security design, not a convenience added after the fact. Many images assume they can create cache files, PID files, temporary files, or sockets under paths that live in the image filesystem. When you make that filesystem read-only, those assumptions become visible. A careful engineer uses the failure to learn exactly which paths need writes, then grants those paths explicitly. A rushed engineer disables the read-only setting and loses a useful containment control.

| Field | Secure Direction | Why It Matters | Common Trade-Off |
|---|---|---|---|
| `runAsNonRoot` | Set to `true` | Prevents accidental root execution when an image default changes | Requires the image to work with a non-root UID |
| `runAsUser` | Use a non-zero UID | Makes the runtime identity explicit and reviewable | File ownership may need adjustment |
| `runAsGroup` | Use a non-zero GID | Avoids default root group behavior | Shared volumes may need group permissions |
| `fsGroup` | Use only when volumes need it | Lets mounted volumes be writable by the workload group | Can slow volume startup on some storage types |
| `readOnlyRootFilesystem` | Set to `true` | Reduces persistence and tampering inside the container image filesystem | Apps need explicit writable mounts |
| `allowPrivilegeEscalation` | Set to `false` | Blocks setuid and similar privilege-gaining paths | Some legacy tools stop working |
| `privileged` | Keep `false` or omit | Avoids broad host device and capability access | System agents may need a dedicated exception |
| `capabilities.drop` | Drop `ALL` first | Removes ambient Linux privileges the app may not need | Add back narrow capabilities only when justified |
| `seccompProfile` | Use `RuntimeDefault` | Filters risky system calls through runtime defaults | Very specialized apps may need a custom profile |

Worked example: suppose a web container fails after you enable `readOnlyRootFilesystem: true`. A weak response would be to turn the control off because "the application needs writes." A stronger response is to find the exact paths the application writes to and mount those paths explicitly. This keeps the immutable application filesystem protected while still giving the process a controlled scratch area.

```bash
k apply -f secure-web.yaml
k -n pod-security-demo describe pod secure-web
k -n pod-security-demo logs secure-web
```

If the logs mention a path such as `/var/cache/nginx` or `/var/run`, add an `emptyDir` mount for that path and try again. This is an example of a senior security habit: preserve the control when possible, and make the exception precise enough that it can be reviewed.

> **Pause and predict**: If a pod-level `runAsUser: 1000` is set, but one container sets `runAsUser: 0`, which value applies to that container? Explain why this override behavior matters during manifest review.

Container-level `securityContext` is more specific, so it overrides the pod-level default for that container. During review, this means you cannot stop at the pod-level block and assume every container is safe. Init containers, sidecars, and application containers all need inspection because a single overriding container can weaken the pod.

A practical review habit is to read the manifest twice. On the first pass, look for broad danger signs: host namespaces, `privileged`, `hostPath`, added capabilities, and root execution. On the second pass, look for consistency: do all containers inherit the intended user, do any init containers override the defaults, and do writable mounts match the application’s real write paths? That second pass catches many mistakes because platform teams often harden the main container but forget the helper container that runs before it.

## Linux Capabilities: Smaller Than Root, Still Powerful

Linux capabilities split the old "root can do everything" model into narrower privileges. This is useful because an application may need one special action, such as binding to a low-numbered port, without needing permission to administer the network stack or mount filesystems. Kubernetes lets you drop capabilities and add back only the ones that are justified.

```text
┌───────────────────────────────────────────────────────────────┐
│                    LINUX CAPABILITIES                         │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  TRADITIONAL MODEL                                            │
│                                                               │
│  ┌───────────────┐                 ┌───────────────────────┐  │
│  │ UID 0 root    │  ────────────▶  │ Broad system powers   │  │
│  └───────────────┘                 └───────────────────────┘  │
│                                                               │
│  CAPABILITY MODEL                                             │
│                                                               │
│  ┌───────────────┐                 ┌───────────────────────┐  │
│  │ Process       │  ────────────▶  │ Specific permissions  │  │
│  └───────────────┘                 └───────────────────────┘  │
│                                                               │
│  HIGH-RISK CAPABILITIES                                       │
│                                                               │
│  ┌───────────────────┬─────────────────────────────────────┐  │
│  │ SYS_ADMIN         │ Mounts, namespaces, broad admin use  │  │
│  │ NET_ADMIN         │ Network configuration and routing    │  │
│  │ SYS_PTRACE        │ Inspect or manipulate processes      │  │
│  │ DAC_OVERRIDE      │ Bypass file permission checks        │  │
│  │ SYS_RAWIO         │ Raw I/O access                       │  │
│  └───────────────────┴─────────────────────────────────────┘  │
│                                                               │
│  SAFER REVIEW PATTERN                                         │
│                                                               │
│  capabilities:                                                │
│    drop:                                                      │
│      - ALL                                                    │
│    add:                                                       │
│      - NET_BIND_SERVICE                                       │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

The most important review rule is to treat `SYS_ADMIN` as a near-privileged request. Its name sounds narrow, but in practice it gates many kernel operations that can break isolation. A developer who says "we are not privileged because `privileged: true` is absent" may still be requesting a dangerous pod if broad capabilities are added.

A good capability review asks for the operation, not the capability name. If the workload needs port `80`, `NET_BIND_SERVICE` may be enough. If it needs to change routes or iptables rules, `NET_ADMIN` may be technically relevant, but that should usually push the workload into a tightly controlled system namespace rather than a general application namespace. If it needs `SYS_ADMIN`, the team should treat it as an exception requiring architecture review.

Capabilities are easy to underestimate because their names look precise, but the operational consequence depends on the surrounding workload. `NET_ADMIN` in a CNI daemon that is owned by the platform team, deployed from a reviewed image, and isolated in a system namespace is a very different risk from `NET_ADMIN` in a customer-facing web application. The field is the same; the trust boundary is not. That is why pod security review combines technical field inspection with ownership and namespace design.

| Capability | Typical Request | Risk Level | Better Question During Review |
|---|---|---:|---|
| `NET_BIND_SERVICE` | Bind to ports below `1024` | Low when isolated | Could the app listen on a high port behind a Service instead? |
| `CHOWN` | Change file ownership | Medium | Can ownership be fixed in the image or volume setup? |
| `SETUID` / `SETGID` | Change process identity | Medium | Is this a legacy image pattern that can be removed? |
| `NET_ADMIN` | Change routes, iptables, interfaces | High | Is this really a system agent rather than an app workload? |
| `SYS_PTRACE` | Debug or inspect processes | High | Can debugging happen in a separate temporary workflow? |
| `SYS_ADMIN` | Broad kernel administration | Critical | Is the workload effectively asking for host-level trust? |

Consider this insecure snippet. It avoids `privileged: true`, but still grants a broad capability and allows privilege escalation. That combination is exactly the sort of thing a reviewer should challenge because it weakens more than one layer of isolation at the same time.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: risky-capability
spec:
  containers:
    - name: app
      image: busybox:1.36
      command: ["sh", "-c", "sleep 3600"]
      securityContext:
        allowPrivilegeEscalation: true
        capabilities:
          add:
            - SYS_ADMIN
```

A safer pattern starts with no capabilities and adds only the smallest permission that maps to the application behavior. When there is no narrow capability that fits, the answer is not automatically to grant a broad one. The answer may be to redesign the workload, move it to a dedicated namespace, or use a purpose-built Kubernetes feature instead of host-level access.

One subtle point for Kubernetes 1.35+ environments is that default runtime behavior and admission policy are separate concerns. A runtime may already apply a default seccomp profile or a container image may already run as a non-root user, but those facts are not as reviewable as explicit manifest intent. Explicit settings make drift visible during code review, policy evaluation, and incident response. When a future image update changes the image user or writes to a new path, the manifest-level controls help turn that drift into a clear failure instead of silent weakening.

## Host Namespaces: Where Isolation Can Disappear

Namespaces are one of the mechanisms that make a container feel isolated from the host. When a pod uses `hostNetwork`, `hostPID`, or `hostIPC`, it deliberately shares part of the node's namespace. That is sometimes necessary for cluster infrastructure, but it is rarely appropriate for ordinary application workloads.

```text
┌───────────────────────────────────────────────────────────────┐
│                    HOST NAMESPACE RISKS                       │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  hostPID: true                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Container can see processes from the host PID namespace │  │
│  │ Risk: process discovery, signals, ptrace-style attacks  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  hostNetwork: true                                            │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Container uses the node network namespace               │  │
│  │ Risk: port conflicts, traffic visibility, spoofing      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  hostIPC: true                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Container shares host inter-process communication       │  │
│  │ Risk: shared memory leakage and process interference    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  secure default: omit these fields or set them to false        │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

Host namespace settings are dangerous because they change what the container can observe and influence. With `hostPID`, a process inside the container may be able to list host processes, discover command lines, and attempt to signal processes if other permissions allow it. With `hostNetwork`, a container bypasses the usual pod network namespace and can conflict with host ports or behave like a node-local service. With `hostIPC`, shared memory and IPC mechanisms become a data exposure concern.

The right question is not "does Kubernetes support this field?" The right question is "what trusted component requires this, and why must it run on the host boundary?" CNI plugins, node monitoring agents, device plugins, and some storage components may have valid answers. A web application, queue worker, or API service usually does not.

Host namespaces deserve special attention because they can make ordinary troubleshooting feel deceptively easy. If a container cannot see a process, `hostPID` makes the process visible. If a network probe behaves differently from inside the pod, `hostNetwork` removes part of the network abstraction. Those quick fixes teach the wrong lesson when they remain in production manifests. Temporary diagnostic access should be handled through a controlled workflow, while steady-state application pods should keep their own namespaces unless there is a strong node-level reason.

| Host Setting | What It Shares | Typical Legitimate Use | Application Namespace Default |
|---|---|---|---|
| `hostNetwork: true` | Node network namespace | CNI, node-local DNS, selected monitoring agents | Block or require exception |
| `hostPID: true` | Node process namespace | Deep node diagnostics or security agents | Block |
| `hostIPC: true` | Node IPC namespace | Rare legacy or specialized node workloads | Block |
| `hostPath` volume | Files or directories from the node | Device plugins, log collectors, kubelet-facing agents | Block sensitive paths |

> **What would happen if** a team moved a node monitoring agent and a public web application into the same namespace, then labeled that namespace `pod-security.kubernetes.io/enforce: privileged` so the agent could run? Describe the risk created for the web application.

The web application inherits the namespace's relaxed admission policy even though it does not need host access. If that application is compromised, the attacker can submit or modify pods that use the same broad permissions allowed for the monitoring agent. A better design is to isolate trusted system workloads in a dedicated namespace and keep application namespaces at `baseline` or `restricted`.

This is the main reason namespace layout is a security decision. A namespace is not only an organizational folder; for PSA it is the boundary where labels decide what pod specs are admitted. If a platform team mixes node agents, batch jobs, public APIs, and tenant workloads in the same namespace, the strictest workload may be constrained by the most permissive exception. Separating workload classes lets the team protect ordinary applications without pretending trusted node components can always run under the same profile.

## Pod Security Standards: Three Profiles, Different Purposes

Pod Security Standards, usually abbreviated PSS, define three policy profiles for pod specifications. They are not a complete security program, and they do not replace image scanning, RBAC, NetworkPolicy, or runtime detection. They are a built-in vocabulary for deciding what pod features should be allowed at admission time.

```text
┌───────────────────────────────────────────────────────────────┐
│                    POD SECURITY STANDARDS                     │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  PRIVILEGED                                                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ No meaningful restrictions on pod security fields       │  │
│  │ Use only for trusted system workloads that need host    │  │
│  │ access, devices, or broad kernel interaction            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  BASELINE                                                     │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Blocks common privilege-escalation paths                │  │
│  │ Suitable as a minimum bar for many application teams    │  │
│  │ Still allows some settings that Restricted forbids      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  RESTRICTED                                                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Enforces stronger hardening expectations                │  │
│  │ Requires non-root behavior and tighter runtime controls │  │
│  │ Best target for sensitive or mature application teams   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  PRACTICAL STARTING POINT                                     │
│  Use Restricted when workloads are ready. Use Baseline as a    │
│  minimum guardrail while teams remediate Restricted warnings.  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

The profile names describe the policy posture, not the workload value. A namespace labeled `privileged` is not more important than one labeled `restricted`; it is less constrained. This matters because teams sometimes ask for "privileged" as if it were a badge of seniority. In a mature cluster, privileged namespaces should be rare, named clearly, and limited to trusted system components.

`baseline` is useful when a cluster needs immediate protection against obvious escalation paths without breaking many existing images. It blocks fields such as `privileged`, host namespaces, and dangerous capabilities, but it does not require every workload to run as non-root. `restricted` is stronger because it expects non-root execution, disabled privilege escalation, dropped capabilities, and seccomp. Moving from `baseline` to `restricted` often requires image and filesystem cleanup, not just a label change.

The profiles are best understood as a migration ladder. `privileged` says the namespace is outside the normal application boundary and must be governed by compensating controls. `baseline` says the platform will block the most common escalation routes while giving legacy images room to keep working. `restricted` says the workload has been engineered to run with a narrow identity, a narrow filesystem, narrow capabilities, and runtime guardrails. Teams that treat the profiles as labels to debate usually struggle; teams that treat them as engineering targets can plan the work.

| Control | Privileged | Baseline | Restricted |
|---|---|---|---|
| `hostNetwork` | Allowed | Blocked | Blocked |
| `hostPID` | Allowed | Blocked | Blocked |
| `hostIPC` | Allowed | Blocked | Blocked |
| `privileged: true` | Allowed | Blocked | Blocked |
| Dangerous capabilities | Allowed | Blocked | Blocked |
| Sensitive `hostPath` usage | Allowed | Blocked | Blocked |
| Running as UID `0` | Allowed | Allowed | Blocked |
| `allowPrivilegeEscalation: true` | Allowed | Sometimes allowed | Blocked |
| Missing seccomp profile | Allowed | Allowed | Blocked |
| Unrestricted volume types | Allowed | Limited | More limited |

When choosing a profile, start from the workload class. Application namespaces should aim for `restricted`, especially for internet-facing or tenant-facing services. Legacy applications that still need root may temporarily fit `baseline` while the team fixes image ownership and write paths. Cluster infrastructure should not share a namespace with applications simply because it needs privileged access.

There is no shame in using `baseline` as a temporary step, but it should not become a permanent excuse. A reasonable migration plan names the blockers: which images still run as root, which paths still need writable mounts, which containers still rely on default capabilities, and which teams own the fixes. Without that inventory, a namespace can sit at `baseline` for years while everyone assumes someone else will make it restricted-ready. Admission warnings, audit events, and deployment review checklists turn that vague intention into actionable work.

The following decision path is a practical review tool. It is intentionally conservative: it pushes ordinary applications toward `restricted`, gives legacy workloads a remediation path through `baseline`, and reserves `privileged` for workloads that act on the node itself.

```text
┌───────────────────────────────────────────────────────────────┐
│                    PROFILE SELECTION PATH                     │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Does the workload administer node networking, devices,        │
│  storage, process visibility, or other host-level features?    │
│                                                               │
│       yes ──▶ dedicated system namespace ──▶ privileged        │
│        │                                                      │
│        no                                                     │
│        ▼                                                      │
│  Can the image run as non-root with explicit writable mounts,  │
│  dropped capabilities, no privilege escalation, and seccomp?   │
│                                                               │
│       yes ────────────────────────────────▶ restricted         │
│        │                                                      │
│        no                                                     │
│        ▼                                                      │
│  Is there a time-boxed remediation plan to remove root,        │
│  mutable filesystem assumptions, or legacy privileges?         │
│                                                               │
│       yes ────────────────────────────────▶ baseline + warn    │
│        │                                                      │
│        no                                                     │
│        ▼                                                      │
│  Escalate for architecture review before admitting workload    │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Pod Security Admission: Enforcing Standards With Namespace Labels

Pod Security Admission, usually abbreviated PSA, is the built-in Kubernetes admission controller that applies Pod Security Standards. In Kubernetes 1.35 and current supported versions, it is the standard built-in replacement for the removed PodSecurityPolicy feature. PSA is intentionally simpler than a full policy engine: it evaluates pods against profile labels on the namespace.

```text
┌───────────────────────────────────────────────────────────────┐
│                    PSA ENFORCEMENT MODES                      │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ENFORCE                                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Blocks pods that violate the selected profile           │  │
│  │ Use when the namespace is ready for hard enforcement    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  WARN                                                         │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Allows the pod but returns warnings to the API client   │  │
│  │ Use to teach developers before raising enforcement      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  AUDIT                                                        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Allows the pod but records violations in audit events   │  │
│  │ Use to measure readiness and find hidden violations     │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  COMMON COMBINATION                                           │
│  enforce baseline, warn restricted, audit restricted           │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

The three modes let teams raise the bar without creating an outage. A namespace can enforce `baseline` so obviously dangerous pods are blocked, while also warning and auditing against `restricted`. Developers can continue shipping compatible workloads, but they see warnings showing which fields must change before the namespace can move to stricter enforcement.

This separation between `enforce`, `warn`, and `audit` is one of the most useful operational features of PSA. Enforcement protects the cluster immediately, warnings teach the person submitting a manifest, and audit records let platform teams measure work that happens outside an interactive terminal. In a healthy rollout, the warning and audit modes run ahead of enforcement. They reveal which workloads would break under the next stricter profile before the platform team flips the blocking label.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest
```

The `latest` version label means the policy follows the current Kubernetes server's definition of the profile. Some organizations pin profile versions during upgrades to avoid surprise changes in admission behavior. For KCSA-level understanding, know that the profile label selects the standard, the mode label selects the behavior, and the version label controls which Kubernetes version of the standard is used.

Pinned versions are a change-management tool, not a way to avoid upgrades forever. If a cluster pins the policy version during a Kubernetes upgrade, the platform team should schedule a follow-up review to compare the pinned profile with the new default profile. Otherwise, the organization can accidentally freeze old assumptions and miss improvements in the standard. For exam purposes, the important pattern is that each mode can have a matching `*-version` label, and the profile name alone is not the whole policy.

```bash
k label namespace pod-security-demo \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/enforce-version=latest \
  pod-security.kubernetes.io/warn=restricted \
  pod-security.kubernetes.io/warn-version=latest \
  --overwrite
```

Now imagine a developer submits a pod that runs as root but does not use `privileged: true`, host namespaces, or dangerous capabilities. With `enforce: baseline`, the pod may be admitted because baseline focuses on known privilege escalation paths and does not fully require non-root execution. With `warn: restricted`, the developer still receives feedback because restricted expects non-root settings and other hardening controls.

> **Pause and predict**: Your cluster enforces `baseline` and warns on `restricted`. A team submits a pod that runs as UID `0`, sets `allowPrivilegeEscalation: false`, drops all capabilities, and uses `RuntimeDefault` seccomp. Will the pod be blocked, warned, both, or neither? Explain which profile drives each result.

A good answer separates enforcement from warning. The pod is not blocked merely for running as root under `baseline`, assuming it avoids the fields baseline forbids. It should still receive a restricted warning because restricted expects the workload to run as non-root. This is why PSA mode combinations are useful: they let platform teams enforce a minimum while signaling the next target.

When debugging real warnings, copy the warning text into the pull request or ticket and translate it into manifest changes. "Violates restricted" is less useful than "container `api` must set `runAsNonRoot: true`, use a non-zero UID, drop all capabilities, and set `allowPrivilegeEscalation: false`." That translation step helps application owners learn the rule and gives reviewers a concrete way to verify the next revision.

## Worked Example: Debugging a PSA Rejection

A Pod Security Admission error is useful if you read it as a map back to fields in the manifest. The API server usually reports the profile that was violated and names the offending settings. Instead of guessing, copy each violation into a small remediation list, then decide whether to fix the workload or move it to a namespace where the exception is justified.

This workflow is especially important during incident response or migration work because PSA messages can list several violations at once. Teams sometimes fix the first named field, retry, then discover the next blocker, which wastes time and encourages frustration with the policy. A better habit is to collect the entire rejection, identify every field category, and decide whether the manifest describes an ordinary application or a host-level component. That decision determines whether you harden the pod or isolate it as an exception.

Start with a namespace that enforces `baseline`, because this gives you a clear rejection whenever the manifest crosses the minimum application-safety boundary.

```bash
k create namespace psa-debug
k label namespace psa-debug \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/enforce-version=latest \
  --overwrite
```

Apply a pod that violates baseline in several ways, then read the response as structured evidence rather than as a generic failure message.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: blocked-debug
  namespace: psa-debug
spec:
  hostNetwork: true
  hostPID: true
  containers:
    - name: app
      image: busybox:1.36
      command: ["sh", "-c", "sleep 3600"]
      securityContext:
        privileged: true
        capabilities:
          add:
            - NET_ADMIN
            - SYS_ADMIN
```

```bash
k apply -f blocked-debug.yaml
```

The exact message can vary by Kubernetes version, but the structure is consistent: it says the pod violates the enforced profile and lists fields such as host namespaces, privileged containers, or forbidden capabilities. Your task is to translate that message into a corrected design. In this case, the pod does not describe a normal application; it asks for host networking, host process visibility, full privilege, and broad capabilities.

| Rejection Clue | Field to Inspect | Likely Fix | When an Exception Might Be Valid |
|---|---|---|---|
| Uses host network | `spec.hostNetwork` | Remove the field and expose via Service | Node-local networking components |
| Uses host PID namespace | `spec.hostPID` | Remove the field | Security agents or deep diagnostics |
| Privileged container | `securityContext.privileged` | Set `false` or omit | Device plugins or specific node agents |
| Adds forbidden capability | `securityContext.capabilities.add` | Drop `ALL`, add narrow capability only if needed | CNI or node networking components |
| Runs as root under restricted | `runAsUser`, image `USER` | Set non-zero UID and `runAsNonRoot: true` | Temporary legacy migration under baseline |

A corrected ordinary application pod would remove host namespace sharing and broad privileges. It would also use the hardened defaults you saw earlier. If the workload owner says the pod is actually a node networking agent, then the fix is not to weaken the application namespace; the fix is to place the agent in a dedicated system namespace with explicit ownership, monitoring, and review.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: corrected-app
  namespace: psa-debug
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      image: busybox:1.36
      command: ["sh", "-c", "sleep 3600"]
      securityContext:
        runAsNonRoot: true
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
      volumeMounts:
        - name: tmp
          mountPath: /tmp
  volumes:
    - name: tmp
      emptyDir: {}
```

Notice the review sequence. First, identify what the workload is supposed to do. Second, map each rejected field to a risk. Third, remove the field or replace it with a narrower mechanism. Fourth, if the field is truly required, isolate the workload instead of changing the policy for unrelated applications.

The corrected pod is intentionally boring. It sleeps, runs as a non-root user, drops capabilities, uses a runtime seccomp profile, and writes only to a named temporary volume. That boring shape is exactly what you want for most application workloads because boring manifests are easier to review, easier to template, and easier to enforce consistently. If an application cannot fit this shape, the review should reveal a specific reason rather than a vague claim that "security breaks the app."

## Privileged Containers: Treat Them as Node-Trust Decisions

`privileged: true` is one of the clearest danger signs in a pod manifest. It grants the container broad access to host devices and capabilities, which can make the container behave much more like a process on the node than an isolated application process. Some cluster infrastructure needs this power, but most application workloads do not.

```text
┌───────────────────────────────────────────────────────────────┐
│                    PRIVILEGED CONTAINERS                      │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  privileged: true grants                                      │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Access to host devices                                  │  │
│  │ Broad Linux capability set                              │  │
│  │ Weakened runtime isolation                              │  │
│  │ Much larger node-compromise blast radius                │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  legitimate examples                                          │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ CNI plugins that configure node networking              │  │
│  │ Device plugins that expose hardware                     │  │
│  │ Selected node monitoring or security agents             │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  review expectation                                           │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Dedicated namespace                                     │  │
│  │ Narrow service account and RBAC                         │  │
│  │ Clear owner and documented justification                │  │
│  │ No co-location with ordinary application workloads      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

The common beginner mistake is to view `privileged` as a troubleshooting tool. Something fails, the team sets `privileged: true`, and the application starts. That result proves only that the original problem involved permissions; it does not prove the broad permission was necessary. A senior review pushes for the smallest successful permission and asks whether the application design can avoid the host dependency entirely.

For example, a service that needs a low port can use a Kubernetes Service mapping port `80` to a high `containerPort`. A process that needs temporary writes can use an `emptyDir`. A process that needs to read configuration can use a ConfigMap or Secret. A pod that asks for privileged mode should be able to explain why Kubernetes-native abstractions are not enough.

There is also an accountability problem with permanent privileged settings. Six months after an urgent fix, the person who added `privileged: true` may have moved teams, the application may have changed, and the original reason may no longer exist. If the manifest does not include a documented exception path outside the YAML, future reviewers see only a powerful setting with no context. Treating privileged access as a node-trust decision forces the team to record ownership, technical necessity, and revalidation expectations.

| Claimed Need | Avoid `privileged` By Trying | Why This Is Safer |
|---|---|---|
| Bind to port `80` | Service `port: 80` to `targetPort: 8080`, or `NET_BIND_SERVICE` | Keeps host devices and broad capabilities away |
| Write temporary files | `emptyDir` mounted at the specific path | Preserves read-only root filesystem |
| Read application config | ConfigMap or Secret volume | Avoids host filesystem mounts |
| Collect app metrics | Sidecar or ServiceMonitor pattern | Avoids host network and process visibility |
| Debug a process | Ephemeral debug workflow with controlled RBAC | Avoids permanent elevated runtime settings |

> **Stop and think**: If a pod is denied by `baseline` because it sets `privileged: true`, what evidence would convince you it belongs in a privileged namespace rather than being redesigned? Write the evidence as if you were leaving a review comment.

A strong review comment names the host-level operation, explains why a narrower capability or Kubernetes abstraction cannot satisfy it, identifies the owning team, and confirms that the workload is isolated from ordinary applications. A weak comment says only "needed for monitoring" or "it works this way." Privileged access is a node-trust decision, so the justification must be specific enough for future maintainers to audit.

The same standard applies to vendor agents. A chart from a respected vendor can still request permissions that are too broad for your cluster’s risk model. Before installing it into a privileged namespace, read the generated manifests, understand which DaemonSet needs host access, and restrict deployment rights around that namespace. Vendor trust reduces some supply-chain questions; it does not remove the need to contain powerful pods.

## Seccomp and Privilege Escalation: Runtime Guardrails

Seccomp filters system calls, which are the interface processes use to ask the kernel to do work. A container may not need every possible syscall to serve HTTP, process messages, or run a batch job. The runtime default seccomp profile blocks selected dangerous or unusual syscalls while preserving compatibility for normal workloads.

```text
┌───────────────────────────────────────────────────────────────┐
│                    SECCOMP PROFILES                           │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Unconfined                                                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ No seccomp syscall filtering from the container runtime │  │
│  │ Highest compatibility, weakest syscall restriction      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  RuntimeDefault                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Uses the container runtime's default seccomp profile    │  │
│  │ Good default for most application workloads             │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  Localhost                                                    │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Uses a custom profile installed on the node             │  │
│  │ Useful for specialized hardening with operational care  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  recommended application setting                              │
│                                                               │
│  securityContext:                                             │
│    seccompProfile:                                            │
│      type: RuntimeDefault                                     │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

`allowPrivilegeEscalation: false` is another runtime guardrail. It prevents a process from gaining more privileges than its parent process through mechanisms such as setuid binaries. This is especially useful when the image contains legacy tools the application does not need. If a setuid helper unexpectedly stops working after this setting is applied, that is a design signal: either the helper is unnecessary and should be removed, or the workload requires an explicit exception that must be reviewed.

Seccomp, dropped capabilities, and disabled privilege escalation are strongest when used together. Dropping capabilities removes broad kernel powers. Disabling privilege escalation prevents the process from gaining new powers later. Seccomp reduces the set of kernel operations available even if the process is compromised. None of these controls is perfect alone, but together they make post-compromise movement harder.

It is useful to separate compatibility problems from security problems when these controls expose old assumptions. If a helper binary fails because privilege escalation is disabled, the team should ask whether the helper belongs in the image at all. If a syscall is blocked by the runtime default seccomp profile, the team should identify the syscall and the feature that needs it rather than switching to `Unconfined` immediately. The goal is not to make every failure disappear; it is to make the permission requirement precise.

| Control | Blocks or Reduces | Failure Symptom When App Depends on It | Review Response |
|---|---|---|---|
| `seccompProfile: RuntimeDefault` | Some risky syscalls | App logs mention operation not permitted for a syscall-like action | Confirm need, then consider custom profile only if justified |
| `allowPrivilegeEscalation: false` | setuid and similar elevation | Legacy helper binary fails to gain elevated permissions | Remove helper or document exception |
| `capabilities.drop: ["ALL"]` | Ambient Linux capabilities | Low-port bind or ownership operation fails | Add a narrow capability or redesign |
| `readOnlyRootFilesystem: true` | Writes to image filesystem | App cannot write cache, pid, temp, or log files | Mount explicit writable volumes |

> **What would happen if** you set `allowPrivilegeEscalation: false` but leave `privileged: true` on the same container? Explain why contradictory settings make security reviews harder.

The manifest communicates mixed intent. One field says the workload should not gain extra privileges, while another grants broad host-level privilege from the start. Reviewers should not treat a single hardening field as proof of safety when a stronger field weakens the boundary. Security review is about the combined effect of the pod spec, not the presence of isolated good-looking settings.

This combined-effect rule is a recurring theme across pod security. `runAsNonRoot: true` is valuable, but less convincing if the same container adds broad capabilities. A read-only root filesystem is valuable, but less convincing if the pod mounts a sensitive host path read-write. Seccomp is valuable, but less convincing if the container runs privileged. The KCSA-level habit is to read the manifest as a system of permissions, not as a checklist of individual good and bad fields.

## Designing Exceptions Without Weakening Everyone

Real clusters contain exceptions. The goal is not to pretend every pod can be restricted immediately; the goal is to prevent one exception from becoming the default for unrelated workloads. Namespaces are the main PSA boundary, so exception design starts with namespace separation.

A mature exception has five properties. It has a specific workload name and owner. It has a stated technical reason tied to a host-level operation. It uses the least permissive profile and fields that still work. It is isolated from ordinary applications. It has a review path so the exception can be removed or revalidated later.

Exception design is where security and operations either cooperate or fight. If the security team simply says "no privileged pods," platform teams will work around the rule because some node-level agents really do need elevated access. If the platform team labels broad namespaces as privileged without review, application teams inherit risk they did not ask for. A usable process names the exception, narrows the namespace, restricts who can deploy there, and keeps the default application path as close to restricted as possible.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: node-agents
  labels:
    pod-security.kubernetes.io/enforce: privileged
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: privileged
    pod-security.kubernetes.io/audit-version: latest
```

This namespace label alone is not enough to be safe. A privileged namespace should also have narrow RBAC, controlled deployment permissions, clear ownership, and monitoring. PSA decides whether pod specs are admitted; it does not decide who may create pods, which images are trusted, or whether the workload behaves correctly at runtime.

| Exception Control | Purpose | Example Review Question |
|---|---|---|
| Dedicated namespace | Prevents permission spillover to apps | Are unrelated workloads forbidden from this namespace? |
| Narrow RBAC | Limits who can create powerful pods | Which identities can create or update pods here? |
| Workload owner | Creates accountability | Which team responds if the agent is compromised? |
| Image control | Reduces supply-chain risk | Is the image pinned and sourced from an approved registry? |
| Runtime monitoring | Detects misuse after admission | Are privileged workload events visible to security teams? |
| Time-boxed review | Prevents permanent accidental exceptions | When will the exception be revalidated? |

For KCSA exam purposes, know that PSA is namespace-scoped and profile-based. For real operations, go one level deeper: namespace labels are only one part of the control plane. RBAC, image policy, NetworkPolicy, node isolation, logging, and incident response all determine whether a privileged exception remains contained.

One practical pattern is to maintain an exception register outside the manifests. The register does not need to be fancy, but it should record the namespace, workload, owner, reason, requested fields, approval date, and next review date. During cluster upgrades or security incidents, that register helps responders identify which workloads have host-level trust and which teams can explain them. Without it, privileged namespaces become institutional memory hidden in labels.

## Patterns & Anti-Patterns

Pod security patterns are most useful when they connect a workload class to a repeatable review shape. A platform team should not make every developer rediscover the same non-root, read-only, capability-dropping manifest from scratch, and it should not approve every exception as a one-off conversation. Good patterns turn the secure path into the easy path while still leaving a controlled route for workloads that genuinely sit on the node boundary.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---|---|---|---|
| Restricted-by-default application namespaces | New services, internet-facing workloads, and teams with modern images | It makes non-root execution, dropped capabilities, seccomp, and explicit writable paths the normal expectation | Provide templates and CI checks so developers get feedback before admission rejects the pod |
| Baseline enforce with restricted warn during migration | Legacy namespaces that still contain root-running images or mutable filesystem assumptions | It blocks the highest-risk fields immediately while showing the remaining work for restricted readiness | Track warning counts by owner, otherwise the migration stalls at baseline |
| Dedicated privileged system namespaces | CNI, storage, device, and node-security agents that need host-level access | It prevents node-trust exceptions from spilling into ordinary application workloads | Restrict deployment rights and review vendor manifests before granting namespace access |
| Explicit writable path design | Applications that need cache, PID, socket, or temporary file locations | It preserves a read-only image filesystem while giving the process the minimum scratch space it needs | Keep write paths documented in the chart or manifest so future image changes remain reviewable |

Anti-patterns usually start as shortcuts. A team wants to fix a failing deploy, a monitoring chart needs host access, or an old image assumes root ownership everywhere. The shortcut becomes dangerous when it is copied into templates, shared namespaces, or permanent exceptions. The cure is not only a stricter setting; it is a review process that asks for the workload’s actual operation, the smallest permission that enables it, and the boundary that contains it.

| Anti-Pattern | What Goes Wrong | Why Teams Fall Into It | Better Alternative |
|---|---|---|---|
| Privileged as a debugging switch | The pod receives broad host-level trust for an unknown problem | It is fast, it often makes the symptom disappear, and it avoids learning the exact missing permission | Reproduce the failure, identify the operation, and grant a narrow capability or writable mount only if needed |
| One namespace for apps and node agents | Application pods inherit relaxed admission because a system agent needs host access | Namespace layout follows team ownership instead of security boundaries | Split workload classes into namespaces with different PSA labels and RBAC controls |
| Hardened main container with weak init container | The pod still violates policy or starts with a high-risk helper path | Reviews focus on the long-running app container and skip setup logic | Inspect every container-level `securityContext`, including init containers and sidecars |
| Warnings without ownership | Restricted warnings accumulate until nobody trusts or reads them | Warn mode is enabled as a checkbox, not as a migration program | Route warnings to service owners, create remediation tickets, and raise enforcement only after testing |

## Decision Framework

Use this framework when reviewing a new workload, a chart upgrade, or a PSA rejection. Start by classifying the workload, then choose the least permissive profile that supports its real behavior, then decide whether any exception is narrow enough to approve. The framework is intentionally conservative because most application pods should not touch host namespaces, host devices, broad capabilities, or mutable image filesystems.

| Review Question | If the Answer Is Yes | If the Answer Is No |
|---|---|---|
| Does the workload configure node networking, storage, devices, process visibility, or another host-level feature? | Treat it as a system workload, place it in a dedicated namespace, and review privileged or baseline exceptions with RBAC and ownership controls | Continue reviewing it as an application workload that should target restricted |
| Can every container run as a non-zero UID with `runAsNonRoot: true`? | Keep or require restricted-compatible identity settings | Use baseline temporarily only with an image remediation plan and owner |
| Can the root filesystem be read-only with explicit writable mounts? | Set `readOnlyRootFilesystem: true` and name the write paths | Identify exact writes before relaxing the control; avoid broad mutable filesystems |
| Are all Linux capabilities unnecessary or narrow enough to justify? | Drop `ALL` and add only the reviewed capability if there is no better design | Reject broad additions such as `SYS_ADMIN` for ordinary apps and escalate host-level cases |
| Can PSA warnings be resolved before enforcement changes? | Move the namespace toward restricted enforcement after testing | Keep enforce at baseline, warn on restricted, and track the remaining blockers |

The final decision should read like an engineering note, not a slogan. "Approved for restricted because all containers run as UID `1000`, drop capabilities, use `RuntimeDefault`, and write only to `/tmp` and `/var/cache/app`" is useful. "Approved because it passed security" is not. Clear decisions teach future reviewers what evidence mattered and make it easier to spot drift when the workload changes.

## Did You Know?

- **Pod Security Admission replaced PodSecurityPolicy** after PodSecurityPolicy was deprecated and removed from Kubernetes. PSA is simpler because it uses standard profiles and namespace labels instead of custom policy objects.

- **Restricted does not mean unusable** for normal applications. Most HTTP services, workers, and batch jobs can run under restricted settings once images avoid root ownership assumptions and write only to explicit mounted paths.

- **A pod can look partly hardened and still be dangerous** if one field grants broad access. For example, `allowPrivilegeEscalation: false` does not make a privileged container an ordinary application container.

- **Warnings are a migration tool** because `warn: restricted` can teach developers which fields to fix before the platform team changes `enforce` from `baseline` to `restricted`.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Running application containers as root by default | A compromised process starts with more filesystem and process authority inside the container | Set `runAsNonRoot: true` and a non-zero `runAsUser` that the image supports |
| Setting `privileged: true` to fix an unexplained failure | It grants broad host-level access and hides the real permission requirement | Identify the failing operation, then use a narrower capability, volume, or Kubernetes abstraction |
| Forgetting to drop Linux capabilities | Default or added capabilities may allow actions the application does not need | Use `capabilities.drop: ["ALL"]` and add only a reviewed narrow capability |
| Enforcing `privileged` on a mixed application namespace | Every workload in the namespace inherits a relaxed admission boundary | Move system agents to a dedicated namespace and keep app namespaces at `baseline` or `restricted` |
| Enabling `readOnlyRootFilesystem` without writable mounts | The application may fail when it writes cache, pid, temp, or runtime files | Keep the root filesystem read-only and mount `emptyDir` at explicit writable paths |
| Treating PSA warnings as harmless noise | Warnings often show exactly what blocks future migration to stricter enforcement | Track warnings, assign owners, and remediate them before raising enforcement |
| Reviewing only the pod-level `securityContext` | A container-level override can weaken one container even when pod defaults look safe | Inspect every app, sidecar, and init container for overrides |
| Using host namespaces for ordinary troubleshooting | Host network or PID access exposes node-level information and can create escalation paths | Use controlled debug workflows and remove host namespace settings from application specs |

## Quiz

1. **Your team deploys an API pod into a namespace with `enforce: baseline` and `warn: restricted`. The pod runs as UID `0`, drops all capabilities, uses `RuntimeDefault` seccomp, and does not use host namespaces. The deployment succeeds but prints a warning. How should you interpret the result, and what should the team change before the namespace moves to restricted enforcement?**

   <details>
   <summary>Answer</summary>

   The pod passes baseline because it avoids the major escalation fields that baseline blocks, such as privileged mode, host namespaces, and dangerous capabilities. It warns under restricted because restricted expects non-root execution and stronger hardening. The team should update the image or pod spec so the process runs as a non-zero UID, set `runAsNonRoot: true`, confirm file permissions and writable mounts, and keep the existing dropped capabilities and seccomp settings. The key is to treat the warning as migration feedback, not as an error to ignore.

   </details>

2. **A developer says their service needs `privileged: true` because it must listen on port `80`. You are reviewing the manifest for an application namespace that targets restricted security. What alternative design would you recommend, and why is it safer?**

   <details>
   <summary>Answer</summary>

   Recommend listening on a high container port such as `8080` and exposing it through a Kubernetes Service with `port: 80` and `targetPort: 8080`. If the process truly must bind to a low port inside the container, consider adding only `NET_BIND_SERVICE` after dropping all capabilities. Both options are safer than privileged mode because they avoid granting host devices, broad capabilities, and weakened runtime isolation for a narrow networking need.

   </details>

3. **A monitoring agent fails after a platform team changes its namespace from `privileged` to `baseline`. The rejection mentions `hostNetwork` and `hostPID`. The agent collects node-level metrics, while ordinary web applications also run in the same namespace. What is the best remediation plan?**

   <details>
   <summary>Answer</summary>

   Do not relax the shared application namespace back to privileged. Create a dedicated namespace for trusted node agents, apply the least permissive labels that allow the agent, restrict who can deploy there with RBAC, and keep ordinary web applications in a baseline or restricted namespace. The monitoring agent may have a legitimate host-level need, but co-locating it with regular applications spreads the exception to workloads that do not need it.

   </details>

4. **A pod is rejected by restricted enforcement after you add `readOnlyRootFilesystem: true`. The application writes temporary files under `/tmp` and runtime files under `/var/run/app`. A teammate proposes setting `readOnlyRootFilesystem: false`. How would you fix the pod while preserving the security control?**

   <details>
   <summary>Answer</summary>

   Keep `readOnlyRootFilesystem: true` and mount explicit writable volumes at the paths the application needs, such as `emptyDir` volumes for `/tmp` and `/var/run/app`. This satisfies the application requirement without allowing writes across the image filesystem. The result is more reviewable because the writable locations are named in the manifest, and an attacker has fewer places to modify binaries or create persistence.

   </details>

5. **During a review, you find a pod with `capabilities.add: ["SYS_ADMIN"]`, `allowPrivilegeEscalation: false`, and `privileged: false`. The owner argues that the pod is safe because it is not privileged and escalation is disabled. What risk remains, and what should you ask next?**

   <details>
   <summary>Answer</summary>

   `SYS_ADMIN` remains a high-risk capability even without `privileged: true`; it covers broad kernel operations and can undermine container isolation. `allowPrivilegeEscalation: false` prevents gaining new privileges later, but it does not remove the broad privilege already granted. Ask which exact operation requires `SYS_ADMIN`, whether a narrower capability or Kubernetes abstraction can replace it, and whether the workload belongs in a dedicated system namespace if the need is truly host-level.

   </details>

6. **A pod-level `securityContext` sets `runAsUser: 1000` and `seccompProfile: RuntimeDefault`. One init container overrides `runAsUser: 0` and adds `NET_ADMIN`. The main application container looks restricted-compatible. How should you evaluate this pod?**

   <details>
   <summary>Answer</summary>

   Evaluate every container, including init containers and sidecars, because container-level security context can override pod-level defaults. The init container weakens the pod by running as root and adding `NET_ADMIN`, which may violate restricted and possibly baseline depending on the exact policy. The review should ask why the init container needs network administration, whether that work can be moved out of the pod, and whether the pod can keep non-root execution consistently across all containers.

   </details>

7. **A team wants to move a legacy namespace from no PSA labels directly to `enforce: restricted`. A dry run shows many pods fail because images run as root and write under `/var/cache`. What staged migration would reduce risk without leaving the namespace unprotected?**

   <details>
   <summary>Answer</summary>

   Start with `enforce: baseline` to block the most dangerous pod features, and add `warn: restricted` plus `audit: restricted` to identify the remaining work. Then remediate images by setting non-root users, fixing file ownership, and mounting explicit writable paths such as `emptyDir` for `/var/cache`. After warnings are resolved and deployments are tested, raise enforcement to restricted. This staged approach improves security immediately while avoiding a large outage.

   </details>

8. **An incident review finds that a compromised app pod could create files inside its container image filesystem, run as root, and use default capabilities. The app did not use host namespaces or privileged mode. Which hardening controls would you add first, and how do they reduce post-compromise impact?**

   <details>
   <summary>Answer</summary>

   Add non-root execution with `runAsNonRoot: true` and a non-zero `runAsUser`, set `readOnlyRootFilesystem: true` with explicit writable mounts, drop all capabilities, set `allowPrivilegeEscalation: false`, and use `seccompProfile: RuntimeDefault`. These controls do not fix the original application vulnerability, but they reduce what an attacker can do after code execution. The attacker has less process authority, fewer kernel privileges, fewer writable persistence locations, and a narrower syscall surface.

   </details>

## Hands-On Exercise: Security Analysis and Remediation

**Scenario**: A team asks you to approve the following pod for an application namespace. The namespace currently enforces `baseline` and warns on `restricted`. Your job is to analyze the manifest, predict which settings create admission or warning problems, then produce a safer replacement that preserves the application requirement to write temporary files.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
  namespace: production
spec:
  hostNetwork: true
  hostPID: true
  containers:
    - name: app
      image: myapp:latest
      ports:
        - containerPort: 80
      securityContext:
        runAsUser: 0
        privileged: true
        readOnlyRootFilesystem: false
        allowPrivilegeEscalation: true
        capabilities:
          add:
            - SYS_ADMIN
```

### Step 1: Classify Each Risk

Read the manifest from top to bottom and classify each risky field as one of three categories: host boundary risk, privilege escalation risk, or operational hygiene risk. Do not jump straight to the final YAML. The skill you are practicing is review reasoning: identify the mechanism, explain the harm, and only then choose the fix.

| Issue | Category | Risk | Safer Direction |
|---|---|---|---|
| `hostNetwork: true` | Host boundary | Shares the node network namespace and can create traffic visibility or port conflict risks | Remove for ordinary apps; use a Service |
| `hostPID: true` | Host boundary | Exposes host process information and possible process interference paths | Remove for ordinary apps |
| `runAsUser: 0` | Privilege | Runs as root inside the container | Use a non-zero UID and `runAsNonRoot: true` |
| `privileged: true` | Privilege | Grants broad host device and capability access | Set `false` or omit |
| `readOnlyRootFilesystem: false` | Persistence | Allows writes into the image filesystem | Set `true` and mount explicit writable paths |
| `allowPrivilegeEscalation: true` | Privilege | Allows setuid-style elevation | Set `false` |
| `SYS_ADMIN` | Privilege | Grants broad kernel administration capability | Drop all capabilities; avoid unless deeply justified |
| `image: myapp:latest` | Hygiene | Mutable tag makes review and rollback less predictable | Use an immutable version tag or digest |
| `containerPort: 80` | Design pressure | May encourage unnecessary low-port privileges | Listen on `8080` and expose port `80` through a Service |

### Step 2: Predict the PSA Result

In a namespace with `enforce: baseline`, this pod should be rejected because it uses host namespaces, privileged mode, and a dangerous capability. In a namespace with only `warn: restricted`, it would also produce warnings about root execution and other hardening gaps. Write down which fields are baseline blockers before checking the answer, because that prediction is the part that builds exam and operations judgment.

### Step 3: Produce a Hardened Pod

The corrected version below assumes the application can listen on `8080` and needs writable `/tmp` plus `/var/cache/app`. If your real application needs different writable paths, keep the same pattern and change only the mount paths. The important design is that writes are explicit, not spread across the image filesystem.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
  namespace: production
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      image: myapp@sha256:abc123def456
      ports:
        - containerPort: 8080
      securityContext:
        runAsNonRoot: true
        privileged: false
        readOnlyRootFilesystem: true
        allowPrivilegeEscalation: false
        capabilities:
          drop:
            - ALL
      volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: app-cache
          mountPath: /var/cache/app
  volumes:
    - name: tmp
      emptyDir: {}
    - name: app-cache
      emptyDir: {}
```

### Step 4: Add a Service Instead of Low-Port Container Binding

If clients need port `80`, expose that port at the Service layer and keep the container listening on a high port. This avoids granting low-port binding permissions inside the container and keeps the pod compatible with stricter security settings.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-app
  namespace: production
spec:
  selector:
    app: web-app
  ports:
    - name: http
      port: 80
      targetPort: 8080
```

### Step 5: Verification Checklist

- [ ] I identified at least eight security or hygiene issues in the original manifest and mapped each one to a concrete risk.
- [ ] I explained which original fields would be blocked by `baseline` enforcement and which would still matter for `restricted` migration.
- [ ] I removed host namespace sharing from the application pod instead of moving the whole application namespace to `privileged`.
- [ ] I replaced root execution with a non-zero UID and added `runAsNonRoot: true`.
- [ ] I kept `readOnlyRootFilesystem: true` and provided explicit writable mounts for application runtime paths.
- [ ] I dropped all Linux capabilities and did not add broad capabilities such as `SYS_ADMIN`.
- [ ] I set `allowPrivilegeEscalation: false` and `seccompProfile.type: RuntimeDefault`.
- [ ] I used a Service to expose port `80` while keeping the container on a high port.

<details>
<summary>Security Issues and Fixes</summary>

| Issue | Risk | Fix |
|---|---|---|
| `runAsUser: 0` | The process runs as root inside the container | Use `runAsUser: 1000` and `runAsNonRoot: true` |
| `privileged: true` | The container receives broad host-level access | Set `privileged: false` or omit the field |
| `readOnlyRootFilesystem: false` | An attacker can modify files inside the image filesystem | Set `readOnlyRootFilesystem: true` and mount explicit writable volumes |
| `allowPrivilegeEscalation: true` | Setuid-style elevation paths remain available | Set `allowPrivilegeEscalation: false` |
| `hostNetwork: true` | The pod shares the node network namespace | Remove it and expose traffic through a Service |
| `hostPID: true` | The pod can see host processes | Remove it for ordinary applications |
| `capabilities.add: ["SYS_ADMIN"]` | The pod receives a broad, high-risk capability | Drop `ALL` capabilities and avoid broad additions |
| `image: myapp:latest` | The reviewed image can change without a manifest change | Use an immutable version or digest |
| Missing pod seccomp profile | The pod may lack runtime syscall filtering expected by restricted | Set `seccompProfile.type: RuntimeDefault` |
| Missing explicit writable mounts | Enabling a read-only root filesystem may break runtime writes | Add `emptyDir` only where the app must write |

The secure version is not "secure forever" just because the manifest looks better. It still needs normal operational controls such as image scanning, RBAC, NetworkPolicy, logging, and patching. Pod security reduces the blast radius when something else fails.

</details>

## Summary

Pod security is the practice of preserving container isolation while granting only the runtime permissions a workload can justify. The most important review habit is to evaluate the combined effect of the pod spec: user identity, capabilities, privilege escalation, filesystem mutability, seccomp, host namespaces, and admission policy all interact. A pod with one hardened field can still be risky if another field grants broad host access.

| Control | Purpose | Secure Setting |
|---|---|---|
| `runAsNonRoot` | Prevent accidental root execution | `true` |
| `runAsUser` | Make runtime identity explicit | Non-zero UID |
| `readOnlyRootFilesystem` | Reduce tampering and persistence | `true` with explicit writable mounts |
| `allowPrivilegeEscalation` | Block setuid-style elevation | `false` |
| `privileged` | Avoid broad host-level access | `false` or omitted |
| `capabilities` | Limit Linux privileges | `drop: ["ALL"]`, add narrow exceptions only |
| `seccompProfile` | Filter risky syscalls | `RuntimeDefault` |
| `hostNetwork`, `hostPID`, `hostIPC` | Avoid sharing host namespaces | `false` or omitted |

Use Pod Security Standards as a shared language. `privileged` is for trusted system workloads that truly need host-level access. `baseline` is a useful minimum bar that blocks common escalation paths. `restricted` is the target for well-hardened application workloads. Use Pod Security Admission labels to enforce, warn, and audit those standards at the namespace boundary.

The senior-level move is not memorizing a perfect YAML block. It is asking why a permission is needed, choosing the smallest mechanism that satisfies the need, and containing exceptions so they do not become the default for everyone else.

## Sources

- Kubernetes documentation: Pod Security Standards, https://kubernetes.io/docs/concepts/security/pod-security-standards/
- Kubernetes documentation: Pod Security Admission, https://kubernetes.io/docs/concepts/security/pod-security-admission/
- Kubernetes documentation: Configure a Security Context for a Pod or Container, https://kubernetes.io/docs/tasks/configure-pod-container/security-context/
- Kubernetes documentation: Linux kernel security constraints for Pods and containers, https://kubernetes.io/docs/concepts/security/linux-kernel-security-constraints/
- Kubernetes documentation: Seccomp, https://kubernetes.io/docs/tutorials/security/seccomp/
- Kubernetes documentation: Admission Controllers, https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/
- Kubernetes documentation: Namespaces, https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/
- Kubernetes documentation: Volumes, https://kubernetes.io/docs/concepts/storage/volumes/
- Kubernetes documentation: Debug running Pods, https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/
- Kubernetes documentation: Kubernetes API reference for Pod security context fields, https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/
- Linux manual pages: capabilities, https://man7.org/linux/man-pages/man7/capabilities.7.html
- Linux manual pages: seccomp, https://man7.org/linux/man-pages/man2/seccomp.2.html

## Next Module

Continue with [Module 3.2: RBAC Fundamentals](../module-3.2-rbac/) to connect pod admission controls with Kubernetes authorization decisions and workload identity design.
