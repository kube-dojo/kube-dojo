---
revision_pending: false
title: "Module 4.1: Security Contexts"
slug: k8s/cks/part4-microservice-vulnerabilities/module-4.1-security-contexts
sidebar:
  order: 1
lab:
  id: cks-4.1-security-contexts
  url: https://killercoda.com/kubedojo/scenario/cks-4.1-security-contexts
  duration: "45-50 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Core CKS skill
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: CKA pod spec knowledge, basic Linux security concepts

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Configure** pod and container security contexts that enforce non-root execution, dropped capabilities, and read-only filesystems.
2. **Audit** workloads for privileged mode, host namespaces, unsafe capabilities, and privilege escalation paths.
3. **Diagnose** startup and runtime failures caused by `runAsNonRoot`, missing writable mounts, seccomp, or capability restrictions.
4. **Design** a defense-in-depth pod manifest for Kubernetes 1.35+ that balances least privilege with application needs.

---

## Why This Module Matters

Hypothetical scenario: your team inherits a namespace full of small services that were created during a fast product launch. The pods start cleanly, the deployment dashboards are green, and the application owners insist that nothing is wrong. During a CKS-style audit, you discover that one web container runs as UID 0, another can write anywhere in its image filesystem, and a troubleshooting pod still has `privileged: true` because someone needed fast access to a network device during an outage. Nothing has failed yet, but the blast radius of any application bug is much larger than it needs to be.

Security contexts matter because Kubernetes does not automatically know the minimum privileges your application needs. A container image can declare a default user, a runtime can add a default capability set, and the kubelet can apply pod-level ownership to mounted volumes, but those defaults are not the same as a security design. Security contexts are where you turn a vague instruction like "run this workload safely" into concrete controls: which UID should execute the process, which group should own mounted files, whether privilege escalation is blocked, which Linux capabilities remain, and whether the root filesystem is writable.

For the CKS exam and for production work, the important skill is not memorizing one hardened YAML template. The important skill is reading a pod spec, predicting how the runtime will combine pod-level and container-level settings, and then choosing the least invasive control that still lets the application run. In this module you will build that judgment by hardening a pod in layers, debugging the failures those layers can cause, and connecting each manifest field to the Linux behavior it changes.

---

## What Security Contexts Control

A security context is Kubernetes' way to pass privilege and access-control instructions from the pod spec to the container runtime and, ultimately, to the Linux kernel. Think of it as a contract between the scheduler's workload description and the node's process model. The API object says what identity, filesystem, capability, and syscall boundaries the workload expects; the kubelet and runtime translate those fields into process attributes before the container's first process starts.

The first practical distinction is scope. `spec.securityContext` applies defaults to the whole pod, while `containers[].securityContext` applies to one container and can override fields that exist at both levels. That split is useful because some settings naturally describe a pod-wide relationship, such as shared volume ownership, while other settings belong to a single process, such as whether a sidecar needs a specific capability. CKS tasks often hide the bug in that override behavior.

```text
┌─────────────────────────────────────────────────────────────┐
│              SECURITY CONTEXT SCOPE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pod-Level (spec.securityContext):                         │
│  ├── runAsUser           - UID for all containers         │
│  ├── runAsGroup          - GID for all containers         │
│  ├── fsGroup             - GID for volume ownership       │
│  ├── runAsNonRoot        - Prevent running as root        │
│  ├── supplementalGroups  - Additional group memberships   │
│  ├── seccompProfile      - Seccomp profile               │
│  └── sysctls             - Kernel parameters              │
│                                                             │
│  Container-Level (containers[].securityContext):           │
│  ├── runAsUser           - Override pod-level UID         │
│  ├── runAsGroup          - Override pod-level GID         │
│  ├── runAsNonRoot        - Container-specific check       │
│  ├── privileged          - Full host access (dangerous!)  │
│  ├── allowPrivilegeEscalation - Prevent privilege gain   │
│  ├── capabilities        - Linux capabilities             │
│  ├── readOnlyRootFilesystem - Immutable container        │
│  ├── seccompProfile      - Container-specific seccomp    │
│  └── seLinuxOptions      - SELinux labels                │
│                                                             │
│  Container settings OVERRIDE pod settings                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The diagram is deliberately split into pod-level and container-level fields because that is how you should read every workload. Start with pod defaults, then check each container for overrides, then check pod fields outside `securityContext` that still affect isolation. A spec can look hardened at the top while one container quietly opts back into a dangerous identity or namespace. The final effective behavior is the combination, not the prettiest block of YAML. SELinux and AppArmor profile configuration (`seLinuxOptions`, annotations) are out of scope for this module; focus here on UID/GID, capabilities, filesystem, and seccomp fields.

Security contexts do not replace admission policy. If a user can create pods in a namespace, that user can also write an unsafe security context unless something validates the request before it is stored. Pod Security Admission, covered in the next module, is the cluster-side guardrail that rejects pods violating the baseline or restricted policy. This module focuses on the workload authoring skill: writing, auditing, and debugging the fields that admission policy will later enforce.

The next example shows a common non-root starting point. `runAsNonRoot: true` is not a UID assignment by itself. It is a validation instruction that tells Kubernetes the container must not start as UID 0. If the image metadata or explicit `runAsUser` shows root, the kubelet rejects the start rather than silently choosing a safer account.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: non-root-pod
spec:
  securityContext:
    runAsNonRoot: true  # Pod-level enforcement
  containers:
  - name: app
    image: nginx
    securityContext:
      runAsUser: 1000  # Must specify non-root UID
      runAsGroup: 1000
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

# If image tries to run as root (UID 0), pod fails to start:
# Error: container has runAsNonRoot and image will run as root
# Stock nginx as UID 1000 also needs writable cache/runtime paths (emptyDir above).
```

Pause and predict: if you remove `runAsUser: 1000` from this manifest but leave `runAsNonRoot: true`, what should happen when the selected image declares or implies UID 0? The useful mental model is that `runAsNonRoot` is a guard, not a repair tool. It blocks a root process from starting, but it does not edit the image, create a user, or fix file permissions inside the image.

Kubernetes also exposes settings that are not inside `securityContext` but must be audited with the same seriousness. `hostPID`, `hostNetwork`, and `hostIPC` join host namespaces instead of using isolated namespaces for the pod. A pod with host process visibility, a writable host mount, and the wrong capability set can become a node-level problem even when the container-level security context looks modest. Treat these fields as part of the same review pass.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: host-namespaces
spec:
  hostPID: true      # Can see all processes on the node
  hostNetwork: true  # Uses node's network namespace
  hostIPC: true      # Can access node's IPC mechanisms
  containers:
  - name: app
    image: nginx
```

Host namespace settings are not always malicious. Some node agents, CNI components, CSI drivers, and observability tools legitimately need a wider view of the node than a normal application pod. The audit question is whether the workload's purpose justifies that view and whether the namespace access is paired with tight capabilities, read-only host mounts where possible, and admission controls that prevent ordinary application namespaces from copying the exception.

---

## Identity and Filesystem Boundaries

The most visible part of a security context is process identity. Linux uses numeric user and group IDs for file ownership and permission checks, and Kubernetes passes the configured UID and GID into the container process. Names like `nginx` or `appuser` are conveniences from `/etc/passwd`; the kernel enforces numbers. That is why security contexts use `runAsUser`, `runAsGroup`, `fsGroup`, and supplemental groups instead of relying on a friendly username in the image.

Running as non-root is valuable because many filesystem and kernel operations are denied to non-zero UIDs unless a specific capability grants them back. It is not a magic sandbox, and it does not make application bugs harmless, but it removes a large category of easy follow-on actions after compromise. An attacker who can execute code as a non-root UID usually has to find an additional misconfiguration before changing system files, binding privileged ports, or taking ownership of mounted data.

The tradeoff is that images built around root assumptions may fail. They might write PID files under `/var/run`, create cache files under `/var/cache`, change ownership during startup, or bind to a low port. A good fix changes the workload to match least privilege; a weak fix removes the guard. In practice that means choosing a non-root image, rebuilding the image with correct ownership, changing the application port, or mounting specific writable paths.

The following `allowPrivilegeEscalation` example adds a second layer. This field controls whether the process can gain more privilege than its parent process, which maps to Linux `no_new_privs` behavior in the runtime. It is especially important when an image contains setuid or setgid binaries. Without this setting, a non-root process may still be able to execute a binary that temporarily grants elevated rights.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: no-escalation
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false  # Prevent setuid, setgid

# This prevents:
# - setuid binaries from gaining privileges
# - Container processes from becoming root
# - Exploits that rely on privilege escalation
```

Before running this, what output do you expect if the container image has a startup script that tries to change ownership under a root-owned directory? The identity boundary and the escalation boundary work together, but they do not grant write access to paths the user cannot modify. The startup will still fail if the image needs root-owned directories and you have not rebuilt the image or provided a writable volume at the specific path.

`readOnlyRootFilesystem` handles a different part of the post-compromise story. The container image layers become read-only, so the process cannot drop a modified binary, overwrite configuration in the image, or persist a script under an arbitrary path. This setting does not make every write impossible. It pushes legitimate writes into declared volumes, which makes review easier because the writable surface is visible in the pod spec.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: readonly-pod
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      readOnlyRootFilesystem: true  # Can't write to container filesystem
    volumeMounts:
    - name: tmp
      mountPath: /tmp  # Must provide writable volume for temp files
    - name: cache
      mountPath: /var/cache/nginx
    - name: run
      mountPath: /var/run
  volumes:
  - name: tmp
    emptyDir: {}
  - name: cache
    emptyDir: {}
  - name: run
    emptyDir: {}
```

The design rule is to mount writable volumes for data, not for laziness. `/tmp`, application cache directories, upload directories, and runtime sockets are reasonable candidates when the application requires them. Making `/etc`, `/usr`, or the whole application directory writable often recreates the risk you were trying to remove. If the application must generate configuration, prefer an init container that writes into a shared volume, then mount that volume read-only into the main container when possible.

`fsGroup` solves one common volume problem. When a pod mounts a volume, the kubelet can arrange group ownership so a non-root process can write to the volume without running as root. That makes `fsGroup` a pod-level concern because volumes are shared at pod scope. The cost is that recursive ownership changes can be expensive on large volumes, so modern clusters also use `fsGroupChangePolicy` when they need to avoid repeated deep permission walks.

Container-level overrides are useful but risky. The next manifest shows a pod default of UID 1000 and a sidecar override to UID 2000. That is a legitimate pattern when containers use different images with different file ownership, but it is also the place where an accidental `runAsUser: 0` can undo a pod-level standard. During review, read overrides as intentional exceptions that need a reason.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mixed-context
spec:
  securityContext:
    runAsUser: 1000        # Default for all containers
    runAsGroup: 1000
  containers:
  - name: app
    image: myapp
    # Inherits runAsUser: 1000 from pod
  - name: sidecar
    image: sidecar
    securityContext:
      runAsUser: 2000      # Overrides pod-level setting
      # This container runs as UID 2000, not 1000
```

When debugging identity failures, resist the urge to patch every field at once. First identify whether the failure is admission-time, start-time, or runtime. Admission failures usually come from policy. Start failures often mention `runAsNonRoot` or an image user. Runtime failures usually say `permission denied`, `read-only file system`, or `operation not permitted`. The message tells you which boundary you crossed.

---

## Capabilities, Privilege Escalation, and Host Risk

Linux capabilities split the historical power of root into smaller named permissions. A process can be UID 0 but still lack a particular capability, and a non-root process can receive a narrowly scoped capability when the workload genuinely needs it. Containers rely on this split because many applications need one privileged action, such as binding to a low port, without needing every permission that root traditionally had.

The important detail is that the default capability set is still broader than most application containers need. A simple HTTP service on port 8080 usually does not need packet crafting, ownership changes, raw sockets, or setuid transitions. Keeping default capabilities because "the pod runs fine" is like leaving every key on a ring because one door still needs to open. The safer workflow is to drop all capabilities, then add back the one you can defend.

```text
┌─────────────────────────────────────────────────────────────┐
│              LINUX CAPABILITIES                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Capabilities split root powers into fine-grained units:   │
│                                                             │
│  CAP_NET_BIND_SERVICE  - Bind to ports < 1024             │
│  CAP_NET_ADMIN         - Configure network interfaces      │
│  CAP_NET_RAW           - Use raw sockets (ping, etc.)     │
│  CAP_SYS_ADMIN         - Many syscalls (mount, etc.)      │
│  CAP_SYS_PTRACE        - Debug other processes            │
│  CAP_CHOWN             - Change file ownership             │
│  CAP_DAC_OVERRIDE      - Bypass file permissions          │
│  CAP_SETUID/SETGID     - Change UID/GID                   │
│  CAP_KILL              - Send signals to any process       │
│                                                             │
│  Default container capabilities (Docker):                  │
│  CHOWN, DAC_OVERRIDE, FOWNER, FSETID, KILL,              │
│  SETGID, SETUID, SETPCAP, NET_BIND_SERVICE, NET_RAW,      │
│  SYS_CHROOT, MKNOD, AUDIT_WRITE, SETFCAP                  │
│                                                             │
│  Best practice: Drop ALL, add only what's needed          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The capability names in Kubernetes omit the `CAP_` prefix. For example, Linux calls the low-port permission `CAP_NET_BIND_SERVICE`, while Kubernetes manifests use `NET_BIND_SERVICE`. That naming difference is small but exam-relevant because a misspelled capability is not the same as a denied capability. Always read the API field as a list of Linux capabilities with the prefix removed.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: minimal-caps
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      capabilities:
        drop:
          - ALL  # Drop all capabilities
        add:
          - NET_BIND_SERVICE  # Only add what's needed
```

Pause and predict: you set `capabilities.drop: ["ALL"]` on a container that binds to port 80 and the process exits with `permission denied`. Diagnose the failure mode before adding capabilities. If logs show `mkdir() "/var/cache/nginx/client_temp" failed (13: Permission denied)`, the process never reached port binding — fix writable cache/runtime paths with `emptyDir` mounts, `fsGroup`, or image ownership first. If nginx starts cleanly but cannot bind port 80, the bind failure is separate: non-root processes need `NET_BIND_SERVICE` (or a high port such as 8080). The smallest capability to add back for a low-port bind is `NET_BIND_SERVICE`, but the better long-term question is whether the application should listen on 8080 instead. Changing the application port removes the capability need entirely, while adding the capability keeps a narrow exception that you must review later.

`allowPrivilegeEscalation: false` should travel with capability reduction. Dropping capabilities removes permissions from the process, while blocking privilege escalation prevents common paths for gaining them back through setuid binaries or related mechanisms. Kubernetes documentation notes that privilege escalation is always true for privileged containers and for containers with `CAP_SYS_ADMIN`, so `allowPrivilegeEscalation: false` is not a universal override. If you grant broad power, the runtime cannot pretend the process is tightly confined.

`privileged: true` is the field that should make you stop. A privileged container receives access that is much closer to the host's power model, including broad device access and a capability set that undermines the normal container boundary. There are legitimate system-level use cases, but ordinary application pods should not use this field as a shortcut for a missing permission. If the workload is not a node agent, storage driver, network component, or tightly controlled maintenance tool, the default answer is no.

```yaml
# DON'T DO THIS in production
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      privileged: true  # Full access to host!

# privileged: true means:
# - Access to all host devices
# - Can load kernel modules
# - Can modify iptables
# - Dramatically increases node-compromise blast radius; may enable
#   container breakout depending on kernel/runtime bugs and host config
# - ONLY use for system-level daemons (CNI, CSI drivers)
```

Hypothetical scenario: an application team cannot get packet capture working during an incident, so they change a web deployment to `privileged: true` and plan to revert it after the call. The next sprint ships other changes, the pod spec stays privileged, and a later application bug gives an attacker a shell with far more node influence than the service ever needed. The safer incident response pattern is to use a dedicated debug workflow with explicit time limits, separate RBAC, and a reviewed exception rather than widening the production deployment.

Host namespace fields compound privileged risk because they remove isolation around process IDs, networking, or IPC. `hostPID: true` lets the pod see node processes. `hostNetwork: true` places the pod directly in the node's network namespace, which can affect port conflicts and network policy assumptions. `hostIPC: true` exposes interprocess communication mechanisms that normal application pods rarely need. These fields are not hidden, so a disciplined review can catch them quickly.

The combination matters more than any single field. A pod with `hostPID: true`, a hostPath mount, and `SYS_PTRACE` is very different from a pod that merely sets `runAsUser: 1000`. A pod with `NET_ADMIN` and `hostNetwork: true` can affect networking in ways a normal web service cannot. Audit security context fields and host namespace fields together because attackers chain permissions in the same way operators compose features.

---

## Seccomp and a Complete Hardened Pod

Seccomp filters system calls between the process and the kernel. That matters because containers share the host kernel, even when namespaces and cgroups isolate many resources. A runtime default seccomp profile blocks or restricts syscall families that ordinary applications should not need. It is not a substitute for non-root execution or capability dropping, but it closes a different door by reducing the kernel interface available to the process.

In Kubernetes 1.35+, the practical baseline is `seccompProfile.type: RuntimeDefault` unless the workload has a measured reason to use a local profile. `Unconfined` should be treated as an exception because it removes a kernel-level filter. A custom `Localhost` profile can be powerful, but it also creates node management overhead because the profile file must exist where the kubelet expects it. For most CKS tasks, `RuntimeDefault` is the secure answer.

The complete hardened pod below combines identity, filesystem, capability, seccomp, and resource controls. Resource limits are not security contexts, but they belong in the same hardening conversation because uncontrolled memory and CPU can become denial-of-service paths. The example intentionally uses an application placeholder image so you focus on the spec shape rather than on one vendor image's startup behavior.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hardened-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault  # Block dangerous kernel syscalls
  containers:
  - name: app
    image: myapp:1.0
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
    resources:  # Prevent resource exhaustion (DoS)
      limits:
        memory: "128Mi"
        cpu: "500m"
      requests:
        memory: "64Mi"
        cpu: "250m"
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
```

Read the manifest from top to bottom and ask what each layer contributes. The pod-level identity sets the default user and group. `fsGroup` makes mounted data accessible to that group. `RuntimeDefault` reduces the syscall surface for every container that inherits it. The container-level block then prevents privilege escalation, removes image-layer writes, and drops capabilities. None of those fields alone is a complete answer; together they reduce several independent failure paths.

This layered approach also explains why hardened pods can fail in ways insecure pods do not. If the image expects to write under `/var/cache`, the read-only root filesystem will reveal that assumption. If the process expects to bind port 80 as a non-root UID, the capability drop will reveal that assumption. If the image entrypoint tries to change ownership at startup, the non-root identity will reveal that assumption. A failure after hardening is often useful information about the image contract.

The correct repair depends on which assumption failed. Rebuilding the image with correct ownership is usually better than granting `CHOWN`. Listening on a high port is usually better than adding `NET_BIND_SERVICE`. Mounting `emptyDir` at `/tmp` is usually better than disabling `readOnlyRootFilesystem`. Those choices keep the security context narrow and make the required exceptions visible to reviewers.

Security contexts should also be readable by the next person. Put pod-wide defaults at pod scope, put container-specific exceptions at container scope, and avoid duplicating fields unless the duplication clarifies a deliberate override. When every container repeats the same long block, reviewers have a harder time finding the one container that differs. When the pod-level default is clear and exceptions are local, the manifest tells its own story.

---

## Worked Exam-Style Diagnostics

CKS tasks often give you a failing pod and ask for the smallest secure fix. The trick is to diagnose the class of failure before editing the YAML. A start error about `runAsNonRoot` points to image user or UID selection. A runtime write error points to `readOnlyRootFilesystem` or volume paths. An `operation not permitted` error often points to a missing capability or seccomp restriction. The fastest path is to map the symptom to the boundary.

The first scenario fixes a pod that would otherwise run as root. The insecure version omits both pod-level and container-level security context. The secure version keeps the non-root guard and sets a numeric UID so the runtime has an unambiguous identity. It also blocks privilege escalation at container scope because that setting is about the process, not the pod's shared volume ownership.

```yaml
# Before (insecure)
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod
spec:
  containers:
  - name: app
    image: nginx

# After (secure) — exam-minimum identity fields only
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
```

The manifest above shows the smallest exam-style identity fix. It is display-only for stock nginx: without writable cache/runtime paths, UID 1000 fails on `mkdir()` under `/var/cache/nginx` before any capability question arises. The runnable hardened lab manifest later in this module adds the required `emptyDir` mounts. On an exam, the prompt may only require the security context change. In a production review, you would also validate whether UID 1000 can read the configured content, whether nginx needs writable cache or runtime directories, and whether the service can use a high port so no low-port capability is needed.

The second scenario handles a workload that needs to bind to port 80 without running as root. This is the classic capability exception. The manifest drops every capability first, then adds `NET_BIND_SERVICE` back. It also keeps `allowPrivilegeEscalation: false`, because adding one capability should not turn into a general privilege path. The exception is visible, narrow, and tied to a specific application requirement. Stock nginx as UID 1000 needs writable runtime paths before port binding can even be reached — the `emptyDir` mounts below satisfy cache and PID/socket directories nginx creates at startup.

```bash
# Pod needs to bind to port 80 but shouldn't run as root
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: web-server
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
  containers:
  - name: nginx
    image: nginx
    securityContext:
      capabilities:
        drop:
          - ALL
        add:
          - NET_BIND_SERVICE  # Allow binding to port 80
      allowPrivilegeEscalation: false
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
EOF

kubectl wait --for=condition=Ready pod/web-server --timeout=60s
kubectl exec web-server -- sh -c 'grep -q ":0050" /proc/net/tcp && echo "nginx listening on port 80"'
```

Which approach would you choose here and why: keep port 80 with `NET_BIND_SERVICE`, or change the application to listen on 8080 and let the Service expose port 80? The second option usually wins when you own the application because it removes the capability exception. The first option can be acceptable when a legacy binary cannot change its listen port and the exception is documented.

The third scenario adds a read-only root filesystem while preserving the paths nginx commonly needs for cache and runtime files. This is the safe pattern: start from read-only, then make the minimum writable paths explicit. If the application also needs `/tmp`, add a volume there. If it needs logs, prefer stdout and stderr first, then add a writable log directory only when a file-based integration truly requires it.

```bash
# Add read-only filesystem with required writable mounts
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: readonly-nginx
spec:
  containers:
  - name: nginx
    image: nginx
    securityContext:
      readOnlyRootFilesystem: true
    volumeMounts:
    - name: cache
      mountPath: /var/cache/nginx
    - name: run
      mountPath: /var/run
  volumes:
  - name: cache
    emptyDir: {}
  - name: run
    emptyDir: {}
EOF
```

The fastest debugging commands are the ones that show the effective spec and the events. `kubectl get -o yaml` shows what was stored. JSONPath helps inspect one field quickly. `kubectl describe` shows start failures, admission messages, and event text. You are not looking for every possible detail; you are looking for the first boundary that explains the observed failure. Replace `mypod` with your pod name in the snippets below.

```bash
# Check pod's effective security context
kubectl get pod mypod -o yaml | grep -A 20 securityContext

# Check container's security context
kubectl get pod mypod -o jsonpath='{.spec.containers[0].securityContext}' | jq .

# Check if pod failed due to security context
kubectl describe pod mypod | grep -i error

# Common errors:
# "container has runAsNonRoot and image will run as root"
# "unable to write to read-only filesystem"
# "operation not permitted" (missing capability)
```

Do not treat these commands as a substitute for understanding the spec. They are a way to confirm the hypothesis you already formed from the symptom. If the event says `runAsNonRoot`, inspect image user and `runAsUser`. If the process logs say read-only filesystem, inspect volume mounts. If a syscall or privileged operation fails, inspect capabilities, seccomp, and whether the operation should be allowed at all.

---

## Auditing an Existing Workload

Auditing a pod for security-context risk is different from writing a clean manifest from scratch. In a rewrite, you can choose a tidy baseline and add only the exceptions you want. In an audit, the workload already exists, the image may have undocumented assumptions, and the dangerous field may be outside the obvious `securityContext` block. Your job is to reconstruct the effective privilege model before proposing a patch.

Start with the pod as Kubernetes stores it, not with the template someone pasted into a ticket. Controllers, Helm charts, Kustomize overlays, mutating admission webhooks, and defaulting can all change the final pod spec. Read pod-level `securityContext`, every container-level `securityContext`, init containers, and ephemeral containers if they exist. Then read `hostPID`, `hostNetwork`, `hostIPC`, hostPath volumes, service account, and volume mounts because those fields can make a modest-looking container much more powerful.

The identity audit asks one concrete question: what numeric UID and GID will each process use when it starts? If a container has no explicit `runAsUser`, you need to know whether the image declares a non-root user. If the image defaults to root, `runAsNonRoot: true` will expose the problem at start time. If the image defaults to a named user, remember that Kubernetes and Linux ultimately care about the numeric UID behind that name.

The filesystem audit asks where the process can write after startup. `readOnlyRootFilesystem: true` is only meaningful when you also inspect the writable volume mounts. A pod that makes `/tmp` writable is normal. A pod that mounts a broad hostPath or makes an application binary directory writable deserves closer review. The audit should distinguish runtime data from configuration and executable content because those categories have very different risk profiles.

The capability audit should begin with the `add` list, then confirm the `drop` list. A manifest that adds `SYS_ADMIN`, `NET_ADMIN`, or `SYS_PTRACE` needs a stronger explanation than a manifest that adds `NET_BIND_SERVICE`. A manifest that drops `ALL` and adds one capability is easier to review than a manifest that keeps defaults and removes one risky capability. Privileged mode short-circuits this reasoning because it grants broad power instead of a narrow capability exception.

The namespace audit looks for combinations. `hostNetwork: true` with `NET_ADMIN` is a very different risk from `hostNetwork: true` on a tightly controlled node exporter that only reads metrics. `hostPID: true` becomes more serious when paired with process inspection tools, `SYS_PTRACE`, or host mounts. Do not score these fields in isolation. Score the path they create from application compromise to node influence.

Pause and predict: a pod has `runAsNonRoot: true`, drops all capabilities, and uses `RuntimeDefault`, but it also mounts `/var/lib/kubelet` from the host read-write. Would you call the workload hardened? The answer should be no, because a powerful host mount can outweigh otherwise strong process-level controls. Security context review must include the data and namespace edges around the process.

Admission labels are part of the audit even though they are not workload fields. If the namespace enforces the restricted profile, many dangerous settings will be rejected before the pod exists. If it only warns or audits, unsafe pods may still run while producing warning or audit signals. That distinction changes your remediation plan. In an enforce namespace, fix the manifest before deployment; in a warn namespace, find already-running workloads that need cleanup.

Multi-container pods deserve extra attention because shared resources blur ownership. One container might run as a safe UID while another sidecar has a root override. One container might have a read-only root filesystem while an init container writes generated files into a shared volume. Those patterns can be legitimate, but the audit should explain which container needs each exception and whether the shared volume lets a weaker container affect a stronger one.

Runtime evidence should confirm the static read. Events tell you why a pod failed. Process checks can confirm the effective UID once a container is running. Write tests can prove whether the root filesystem is actually read-only. Capability-sensitive operations can confirm whether an exception is required. Use runtime evidence to validate your interpretation, but do not use a successful test as proof that the permissions are safe.

For CKS-style remediation, produce a patch that removes the highest-risk field first and then restores application function with a narrow alternative. Remove `privileged: true` before tuning smaller fields. Replace root execution with a numeric non-root UID before polishing volume ownership. Drop all capabilities before adding a specific exception. This ordering matters because it reduces the largest blast radius quickly while keeping the workload behavior testable.

The audit result should be a short technical argument, not just a YAML diff. State the risky field, the concrete risk it creates, the application requirement if one exists, and the safer replacement. That explanation is what lets another engineer decide whether an exception belongs in a system namespace, an application namespace, or nowhere at all. Good security context work is visible in the manifest and defensible in the review.

---

## Patterns & Anti-Patterns

The strongest pattern is to design the workload around least privilege before the first production deployment. That means choosing an image that can run as a non-root UID, placing writable state under predictable directories, using stdout for logs, and avoiding privileged ports when the application does not need them. Security contexts are easier to keep strict when the image contract is clean. Retrofitting them after months of root-based assumptions often turns into a long exception list.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---|---|---|---|
| Pod-level defaults with local exceptions | Multiple containers share the same UID, GID, seccomp profile, or volume group | Reviewers can see the intended baseline once and focus on the containers that differ | Keep exceptions near the container that needs them, and require a comment or policy exception for risky fields |
| Drop all capabilities first | Application containers that do not need Linux root powers | The manifest starts from zero ambient capability and adds only a defended permission | Build a small catalog of approved capability exceptions so reviews stay consistent |
| Read-only image filesystem plus explicit writable volumes | Services that write cache, sockets, temp files, or upload data | Legitimate writes are visible in `volumeMounts`, and image layers stay immutable at runtime | Standardize writable paths in base images so teams do not mount broad directories |
| RuntimeDefault seccomp | General Linux application pods on Kubernetes 1.35+ | The runtime blocks risky syscall patterns without requiring a custom profile | Track exceptions because custom profiles create node distribution and lifecycle work |

Anti-patterns usually begin as convenience. A developer is blocked, an incident is loud, or an image was built years before the cluster adopted stronger standards. The fix that makes the pod start quickly can become permanent if nobody records why it exists. Treat every widening field as technical debt with a blast radius, not as harmless YAML noise.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|---|---|---|
| Setting `privileged: true` to fix one denied operation | The container receives broad host-level power instead of one narrow permission | Identify the exact capability, device, or namespace need, then isolate it in a reviewed system namespace |
| Removing `runAsNonRoot` after a start failure | The workload returns to UID 0 and hides the image's root assumption | Set a numeric non-root UID, fix file ownership, or rebuild the image with a non-root `USER` |
| Making broad directories writable under a read-only root filesystem | Attackers can modify configuration or binaries in places reviewers assume are immutable | Mount only the application data paths that must be writable, and keep configuration read-only |
| Adding `NET_ADMIN` because networking is confusing | The pod can change networking behavior far beyond a simple bind or connect need | Use `NET_BIND_SERVICE` for low ports, or move diagnostics into a controlled debug pod |

One subtle pattern is to separate application hardening from node-agent hardening. A CNI plugin, CSI driver, or node observability daemon may need host namespaces, devices, or elevated capabilities. That does not mean the same fields are acceptable in the application namespace. Put exceptional workloads in dedicated namespaces with clear labels, narrow RBAC, admission policy exceptions, and review trails, then keep ordinary application namespaces aligned with restricted expectations.

Another useful pattern is to make security context failures part of image acceptance. If a service cannot start with non-root execution and a read-only root filesystem, ask whether the image layout is the real defect. Moving cache paths, setting file ownership during the image build, and avoiding privileged ports usually make the runtime manifest simpler. The best pod security context is often enabled by a better container image.

---

## Decision Framework

Use a decision framework when you are unsure whether to tighten a field, add an exception, or change the image. The goal is to avoid both extremes: accepting unsafe defaults because they are convenient, or adding controls that break the workload without a repair plan. Start with the application behavior, then choose the Kubernetes control that matches the behavior. If the behavior itself is unnecessary, remove the behavior instead of granting permission.

```text
Start with the failing or unaudited pod
        |
        v
Does it need to run as UID 0?
        |-- no  -> set runAsNonRoot + numeric runAsUser
        |-- yes -> challenge the image design before approving
        |
        v
Does it need to write to image paths?
        |-- no  -> set readOnlyRootFilesystem
        |-- yes -> mount narrow writable volumes or rebuild paths
        |
        v
Does it need a Linux capability?
        |-- no  -> drop ALL
        |-- yes -> drop ALL, add one named capability, document reason
        |
        v
Does it need host namespaces or privileged mode?
        |-- no  -> keep them false or unset
        |-- yes -> move to controlled system namespace with policy review
```

For identity decisions, prefer a numeric non-root UID that matches image ownership. `runAsNonRoot: true` catches mistakes, but `runAsUser` removes ambiguity. If the image has no non-root user and all files are owned by root, changing only the pod spec may surface permission errors. That is not a reason to remove the control. It is a signal to rebuild the image or mount data where the chosen UID can write.

For filesystem decisions, ask whether the path is data, configuration, or executable content. Data paths can be writable when the application needs them. Configuration should usually come from ConfigMaps, Secrets, or init-generated files mounted with narrow permissions. Executable content should stay immutable. This classification prevents the common mistake of mounting a writable directory high in the filesystem tree because one subpath failed.

For capabilities, start from the operation rather than the error message. Binding to port 80 maps to `NET_BIND_SERVICE`. Capturing raw packets maps to broader network permissions and should raise a stronger review question. Changing file ownership during startup may tempt you toward `CHOWN`, but a build-time ownership fix is often cleaner. The capability list should explain the workload, not compensate for an avoidable image design.

For seccomp, choose `RuntimeDefault` when the application is a normal Linux service and there is no evidence of syscall incompatibility. If the application fails under `RuntimeDefault`, examine whether the blocked syscall is genuinely required. A local profile can allow a carefully selected syscall set, but it requires node distribution, version tracking, and testing across runtime upgrades. That operational cost belongs in the decision.

For privileged mode and host namespaces, require a different standard of proof. An application team saying "it works only this way" is not enough. Ask what host resource is required, whether a purpose-built node agent already provides it, whether a debug workflow can handle the case, and whether the pod can live in a restricted namespace. These fields move the workload closer to node trust, so the approval path should be explicit.

| Workload Need | Preferred Setting | Exception Path | Review Question |
|---|---|---|---|
| Normal HTTP service on high port | Non-root UID, drop all capabilities, read-only root filesystem | Writable `/tmp` or cache volume if required | Can the image run without root-owned startup writes? |
| HTTP service on port 80 | Change app to high port and map Service port 80 | Add `NET_BIND_SERVICE` after dropping all capabilities | Is the low port required inside the container? |
| Writes cache or temp files | `readOnlyRootFilesystem: true` plus narrow `emptyDir` mounts | Persistent volume only for durable state | Are any writable paths configuration or executable paths? |
| Node-level network or storage agent | Dedicated namespace and reviewed elevated fields | `privileged`, host namespaces, or device access as justified | Is this workload a system component rather than an app? |

This framework is also useful during incident response. If a team proposes a quick permission change, map it to the table before applying it to a production deployment. A temporary `NET_BIND_SERVICE` exception is easier to reason about than temporary privileged mode. A debug pod in a controlled namespace is easier to clean up than a widened application deployment. The decision should leave the steady-state manifest safer than the emergency.

---

## Did You Know?

The details below are small enough to remember during an exam but important enough to change a production review. Each one points to a behavior that surprises teams when security contexts move from theory into real workloads.

- **`runAsNonRoot` does not pick a UID for you.** If the image runs as root and you set `runAsNonRoot: true` without a non-root image user or explicit `runAsUser`, the container fails instead of silently choosing a safer user.
- **Default container capability sets are still larger than many apps need.** Docker's commonly documented default set contains 14 capabilities, which is why `drop: ["ALL"]` is a clearer baseline than auditing one default at a time.
- **The `nobody` user is commonly UID 65534.** It is sometimes used for non-root execution, but a workload-specific UID is easier to connect to image ownership and volume permissions during review.
- **Seccomp has been stable in Kubernetes since v1.19.** For Kubernetes 1.35+ workloads, `RuntimeDefault` should be the ordinary starting point unless testing shows a specific incompatibility.

---

## Common Mistakes

Most security context mistakes are not syntax errors. They are mismatches between what the manifest promises and what the image, runtime, or application actually does. The table below ties each mistake to the usual cause and the repair that preserves the security intent.

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| `runAsNonRoot` without a non-root image user or `runAsUser` | The author expects Kubernetes to choose a UID, but the field only validates that UID 0 is not used | Specify a numeric non-root `runAsUser`, or rebuild the image with a non-root `USER` and matching file ownership |
| Using `privileged: true` to bypass one denied operation | Troubleshooting pressure hides the difference between one permission and host-level power | Identify the exact capability, device, or namespace need, then isolate and document the smallest exception |
| Not dropping capabilities | The default capability set is invisible during normal testing, so excessive permissions feel harmless | Set `capabilities.drop: ["ALL"]`, add back only named capabilities that map to a required operation |
| Forgetting writable volumes with `readOnlyRootFilesystem` | The image writes cache, PID, temp, or log files under paths that used to be writable | Mount narrow `emptyDir` or persistent volumes at required data paths, or change the image to write elsewhere |
| Only setting pod-level identity | A container-level `securityContext` can override pod-level fields for that container | Review every container and use admission policy to reject root overrides in application namespaces |
| Adding broad writable mounts under `/etc` or the app directory | A quick fix for startup-generated configuration makes sensitive paths writable at runtime | Generate configuration in an init container, mount only the generated file or directory, and prefer read-only mounts |
| Treating host namespaces as harmless because they are outside `securityContext` | Reviewers focus only on the nested security context block and miss pod-level namespace fields | Audit `hostPID`, `hostNetwork`, `hostIPC`, hostPath mounts, and capabilities in the same review pass |

---

## Quiz

Use these questions as scenario drills rather than recall checks. The answer block explains the reasoning because the exam rewards fast diagnosis, while production work rewards knowing why a field is the right fix.

<details>
<summary>Question 1: Your team deploys an nginx pod with `runAsNonRoot: true`, no explicit `runAsUser`, and an image that starts as root. The pod fails before the app logs appear. What secure fix should you make?</summary>

Keep `runAsNonRoot: true` and give the workload a valid non-root identity, either by specifying a numeric `runAsUser` that can read the image files or by using an image that declares a non-root user. Removing `runAsNonRoot` would only hide the root assumption and weaken the workload. If the new UID cannot write required paths, fix ownership in the image or add narrow writable volumes rather than reverting to root.
</details>

<details>
<summary>Question 2: A web service runs on port 8080 and has the runtime's default capabilities. A security review asks you to reduce packet-level abuse risk. What should the security context do?</summary>

Drop all capabilities and do not add `NET_BIND_SERVICE`, because a process listening on port 8080 does not need the low-port bind capability. Pair the capability drop with `allowPrivilegeEscalation: false` so the process cannot regain permissions through setuid-style paths. This is stronger than deleting only `NET_RAW` because it makes the manifest start from no ambient capability and documents any future exception.
</details>

<details>
<summary>Question 3: You set `readOnlyRootFilesystem: true`, and the application fails when writing `/tmp/session` and `/var/log/app/current.log`. What repair keeps the root filesystem read-only?</summary>

Mount writable volumes only at the paths that need runtime data, such as `/tmp` and `/var/log/app`, or change the application to log to stdout if file logs are not required. Do not disable `readOnlyRootFilesystem` just because one path needs writes. Also avoid making broad paths like `/` or `/etc` writable, because that gives an attacker room to alter configuration or executable content.
</details>

<details>
<summary>Question 4: A pod has `runAsUser: 1000` at pod scope, but one sidecar sets `runAsUser: 0` in its container security context. Which UID runs for the sidecar, and what prevents this bypass across a namespace?</summary>

The sidecar runs as UID 0 because container-level fields override pod-level fields for that container. To prevent this in a shared namespace, use Pod Security Admission or another admission controller to reject root containers before they are persisted. The workload manifest should still be fixed, but policy is what stops a user with pod creation rights from writing the override again.
</details>

<details>
<summary>Question 5: A developer asks for `privileged: true` because a diagnostic command needs raw packet access during an outage. What should you check before approving the change?</summary>

First check whether the diagnostic can run in a dedicated debug pod or controlled system namespace rather than widening the production deployment. Then identify the exact capability or host access required, because privileged mode grants far more power than raw packet access alone. If an exception is truly required, make it time-limited, reviewed, and isolated from ordinary application workloads.
</details>

<details>
<summary>Question 6: A hardened pod fails with `operation not permitted` after you drop all capabilities and set `RuntimeDefault` seccomp. How do you decide whether to add a capability or change seccomp?</summary>

Start from the operation that failed, not from a guess. If the failure is a privileged network, ownership, or low-port bind operation, map it to a named Linux capability and decide whether the application should do that operation at all. If logs or audit data point to a blocked syscall under seccomp, test whether `RuntimeDefault` is incompatible with a real workload requirement before considering a local profile.
</details>

<details>
<summary>Question 7: A storage node agent needs host device access, while a normal API deployment in the same cluster requests `hostPID: true` for debugging. Should both be handled the same way?</summary>

No. The storage agent may have a defensible system-level reason for host access, but it should live in a controlled namespace with reviewed permissions and admission exceptions. The normal API deployment should not carry host process visibility for debugging. Use a separate debug workflow or temporary diagnostic pod instead of baking host namespace access into an application deployment.
</details>

---

## Hands-On Exercise

In this exercise you will create an insecure pod, replace it with a hardened pod, and verify that the hardened settings behave the way the manifest claims. The commands assume you have a Kubernetes 1.35+ cluster and a working `kubectl` context. The exercise uses nginx because it is familiar, but the same workflow applies to internal services after you account for their write paths and image ownership.

Exercise scenario: you are reviewing a service before it can move into a namespace that enforces a restricted policy. The current pod has no explicit security context. Your job is to create a hardened version that runs as non-root, blocks privilege escalation, drops all capabilities then adds back `NET_BIND_SERVICE` so nginx can bind port 80, uses a read-only root filesystem, and provides writable volumes only where nginx needs them for this test.

- [ ] Task 1: Create the insecure pod and inspect whether it declares any pod or container security context.
- [ ] Task 2: Apply the hardened pod manifest with non-root identity, `RuntimeDefault` seccomp, dropped capabilities with `NET_BIND_SERVICE` added back, and writable runtime directories.
- [ ] Task 3: Verify the stored pod-level and container-level security context fields with `kubectl`, and confirm nginx is listening on port 80.
- [ ] Task 4: Prove that writing to the image filesystem fails while writing to `/tmp` succeeds.
- [ ] Task 5: Clean up both pods and record which security context field explained each observed behavior.

<details>
<summary>Solution commands</summary>

```bash
# Step 1: Create an insecure pod first
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: insecure
spec:
  containers:
  - name: app
    image: nginx
EOF

# Step 2: Check its security context
kubectl get pod insecure -o yaml | grep -A 20 securityContext
# (Likely empty or minimal)

# Step 3: Create hardened version
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: hardened
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault  # Block dangerous kernel syscalls
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
        add:
          - NET_BIND_SERVICE
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
EOF

# Step 4: Wait for pods
kubectl wait --for=condition=Ready pod/hardened --timeout=60s

# Step 5: Verify security context
kubectl get pod hardened -o jsonpath='{.spec.securityContext}' | jq .
kubectl get pod hardened -o jsonpath='{.spec.containers[0].securityContext}' | jq .

# Step 6: Test that writing to root filesystem fails
kubectl exec hardened -- touch /etc/test 2>&1 || echo "Write blocked (expected)"

# Step 7: Test that writable volume works
kubectl exec hardened -- touch /tmp/test && echo "Write to /tmp succeeded"

# Step 8: Verify nginx bound port 80 with NET_BIND_SERVICE (capability lesson)
kubectl exec hardened -- sh -c 'grep -q ":0050" /proc/net/tcp && echo "nginx listening on port 80"'

# Cleanup
kubectl delete pod insecure hardened
```

</details>

<details>
<summary>What success looks like</summary>

The hardened pod should store pod-level `runAsNonRoot`, numeric UID and GID settings, `fsGroup`, and `seccompProfile.type: RuntimeDefault`. Its container security context should show `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`, and a capability set that drops `ALL` while adding only `NET_BIND_SERVICE`. Nginx should reach Ready and listen on port 80 — proving the capability exception works once writable cache/runtime paths exist. The write to `/etc/test` should fail because the image filesystem is read-only, and the write to `/tmp/test` should succeed because `/tmp` is backed by an `emptyDir` volume.
</details>

The most valuable part of the lab is the explanation you can give afterward. `runAsNonRoot` and `runAsUser` control process identity. `readOnlyRootFilesystem` controls writes to image layers. `emptyDir` restores writes only where the application needs runtime data. Capability dropping removes ambient Linux privileges, while `NET_BIND_SERVICE` is the single exception for a low port — verified when `/proc/net/tcp` shows a listener on port 80 (`:0050`). `RuntimeDefault` adds a syscall boundary that does not depend on the application UID.

---

## Learner check

> Security contexts are where you turn a vague instruction like "run this workload safely" into concrete controls: which UID should execute the process, which group should own mounted files, whether privilege escalation is blocked, which Linux capabilities remain, and whether the root filesystem is writable.

---

## Sources

- [Kubernetes: Configure a Security Context for a Pod or Container](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [Kubernetes API reference: Pod securityContext](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/#security-context)
- [Kubernetes API reference: PodSpec host namespace fields](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/#PodSpec)
- [Kubernetes: Linux kernel security constraints for Pods and containers](https://kubernetes.io/docs/concepts/security/linux-kernel-security-constraints/)
- [Kubernetes: Seccomp and Kubernetes](https://kubernetes.io/docs/reference/node/seccomp/)
- [Kubernetes tutorial: Restrict a Container's Syscalls with seccomp](https://kubernetes.io/docs/tutorials/security/seccomp/)
- [Kubernetes: Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes: Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
- [Kubernetes: Enforce Pod Security Standards with namespace labels](https://kubernetes.io/docs/tasks/configure-pod-container/enforce-standards-namespace-labels/)
- [Kubernetes: Mapping PodSecurityPolicies to Pod Security Standards](https://kubernetes.io/docs/reference/access-authn-authz/psp-to-pod-security-standards/)
- [Linux manual: capabilities(7)](https://man7.org/linux/man-pages/man7/capabilities.7.html)

## Next Module

[Module 4.2: Pod Security Admission](../module-4.2-pod-security-admission/) - Enforcing security standards at namespace level.
