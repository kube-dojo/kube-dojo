---
title: "Module 4.4: SecurityContexts"
slug: k8s/ckad/part4-environment/module-4.4-securitycontext
sidebar:
  order: 4
revision_pending: false
lab:
  id: ckad-4.4-securitycontext
  url: https://killercoda.com/kubedojo/scenario/ckad-4.4-securitycontext
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Important for security, multiple settings
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Basic Linux user/group concepts, [Module 1.1 (Pods)](../part1-design-build/module-1.3-multi-container-pods/)

---

## Learning Outcomes

After completing this module, you will be able to:

- **Implement** pod-level and container-level SecurityContexts for `runAsUser`, `runAsGroup`, `fsGroup`, and `runAsNonRoot`
- **Diagnose** failed pod starts and permission errors caused by `runAsNonRoot`, `readOnlyRootFilesystem`, and volume ownership
- **Evaluate** Linux capability and privilege escalation settings to choose least-privilege container access
- **Design** a CKAD-ready secure pod manifest that preserves writable paths with `emptyDir` volumes and passes Kubernetes 1.35+ Pod Security expectations

## Why This Module Matters

Hypothetical scenario: a team ships a small HTTP service into a shared Kubernetes cluster, and the image works perfectly on a laptop because it runs as root and can write anywhere inside the container filesystem. In the cluster, the same deployment lands in a namespace with restricted Pod Security settings, the container refuses to start, and the only visible clue is a terse event about running as root. The application is not broken, but the manifest has failed to describe the security contract the cluster expects.

SecurityContext is the part of a pod specification where you turn Linux security assumptions into Kubernetes configuration. It answers practical questions that show up during deployments and CKAD troubleshooting: which UID runs the process, which group owns mounted volume files, whether the root filesystem is writable, whether a process can gain more privilege, and which narrowly scoped Linux capabilities remain available. Those settings are not decorative hardening knobs. They directly influence whether a container starts, whether it can open files, and whether it matches the cluster's admission policy.

The CKAD exam usually keeps SecurityContext tasks small, but it tests the same mental model that production clusters need. You may be asked to make a pod run as a non-root UID, repair a volume permission problem, add a writable `emptyDir` for an application with a read-only root filesystem, or inspect the effective settings of a running pod. Each task is fast only if you already know which settings belong at pod level, which settings belong at container level, and how Kubernetes resolves conflicts.

Treat SecurityContext like building access control. A building policy can define the default badge every tenant receives, but one room might still require a stronger restriction or a different key. A pod-level SecurityContext provides defaults for the containers in that pod, while a container-level SecurityContext can override selected process and privilege settings for one container. Mounted volumes are the shared rooms, so group ownership and writable directories must be planned with every container in mind.

This module teaches SecurityContext as a debugging tool as much as a security tool. You will start with the hierarchy, then move through identity, volume ownership, writable paths, Linux capabilities, and verification commands. By the end, a manifest with `runAsNonRoot`, `fsGroup`, `readOnlyRootFilesystem`, and dropped capabilities should read like a clear operating contract instead of a pile of YAML fragments.

## SecurityContext Levels

Kubernetes has two related SecurityContext locations, and confusing them is the fastest way to write a manifest that looks secure but behaves differently than expected. The pod-level `spec.securityContext` sets defaults and pod-wide behavior, especially identity defaults and volume group handling. The container-level `containers[].securityContext` controls settings that belong to one container process, such as privilege escalation, capabilities, read-only root filesystem, and a container-specific `runAsUser` override.

That separation exists because a pod can contain more than one container. A main application container might run as UID `1000`, while a sidecar image might require UID `2000` because its filesystem paths were built with different ownership. The pod can still define an `fsGroup` for shared volumes, because the volume must be usable by both containers. Kubernetes gives you a defaulting model rather than forcing every container to repeat the same identity fields.

The precedence rule is simple: when the same supported field exists at both levels, the container-level value wins for that container. That does not mean the pod-level value disappears. Other containers still inherit it, and pod-only settings such as `fsGroup` remain pod-scoped. A good manifest uses pod-level settings for shared defaults and container-level settings when one image has a legitimate reason to differ.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-demo
spec:
  securityContext:        # Pod-level (applies to all containers)
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
  containers:
  - name: app
    image: nginx
    securityContext:      # Container-level (overrides pod-level)
      runAsUser: 2000
      allowPrivilegeEscalation: false
```

In this example, the `app` container runs as UID `2000` because the container-level `runAsUser` overrides the pod-level default. The group ownership behavior still comes from the pod-level context: `runAsGroup: 3000` supplies the primary group when not overridden, and `fsGroup: 2000` is used for mounted volumes that support ownership management. If you add another container without a container-level `runAsUser`, that second container inherits UID `1000`.

Pause and predict: if a pod sets `runAsNonRoot: true` at pod level and one container sets `runAsUser: 0`, what do you expect Kubernetes to do when it tries to start that container? The important detail is that `runAsNonRoot` is not a request to change the UID. It is a guardrail that says the container must not run as UID `0`, so an explicit root override conflicts with the guardrail and the start should fail.

The hierarchy is easier to remember if you separate defaults from exceptions. Put a default identity at pod level when every container can share it, put shared volume ownership at pod level because volumes are pod resources, and put privilege-sensitive settings at container level because privileges attach to individual processes. When a sidecar needs a different UID, make the override explicit and keep the reason visible in the manifest.

```
┌─────────────────────────────────────────────────────────────┐
│                SecurityContext Hierarchy                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pod Security Context                                       │
│  ┌─────────────────────────────────────────────────┐       │
│  │ runAsUser: 1000                                 │       │
│  │ runAsGroup: 3000                                │       │
│  │ fsGroup: 2000 (for volumes)                     │       │
│  │                                                 │       │
│  │  Container A           Container B              │       │
│  │  ┌────────────────┐   ┌────────────────┐       │       │
│  │  │ (inherits pod) │   │ runAsUser: 2000│       │       │
│  │  │ runAsUser:1000 │   │ (overrides pod)│       │       │
│  │  │                │   │                │       │       │
│  │  │ capabilities:  │   │ readOnly: true │       │       │
│  │  │  drop: [ALL]   │   │                │       │       │
│  │  └────────────────┘   └────────────────┘       │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The diagram shows the operational rule you will use during troubleshooting. First inspect pod-level defaults, then inspect each container for overrides, and finally remember that some fields never become container-level decisions. That order prevents a common mistake: changing the pod-level value repeatedly when the actual behavior is coming from a container override farther down in the spec.

## Identity, Groups, and Volume Ownership

Linux processes run with a numeric user ID and group ID, and Kubernetes SecurityContext lets you set those numbers without rebuilding the image. The image can still declare a default user, but `runAsUser` in the pod or container spec is more explicit from the cluster's point of view. On the exam, using a numeric UID is usually safer than relying on a username, because usernames require `/etc/passwd` entries inside the image while numeric IDs are understood by the kernel directly.

```yaml
securityContext:
  runAsUser: 1000       # UID to run as
  runAsGroup: 3000      # GID for the process
  fsGroup: 2000         # GID for mounted volumes
```

`runAsUser` changes the UID of the main process in the container, and `runAsGroup` changes its primary group. `fsGroup` is different: it is a pod-level setting that gives containers an additional group for supported volume mounts and can adjust the group ownership of volume contents. The distinction matters because application files baked into the image are part of the container root filesystem, while mounted volumes are attached by Kubernetes at runtime.

If a container can start as UID `1000` but cannot write to `/data`, the UID may not be the real problem. The directory could be mounted from a volume whose group ownership does not match the process groups. In that case, `fsGroup` often fixes the volume access while preserving a non-root process. This is why volume permission debugging starts with `id` and `ls -la`, not with random changes to every SecurityContext field.

```yaml
securityContext:
  runAsNonRoot: true    # Fail if image tries to run as root
```

`runAsNonRoot: true` is frequently misunderstood because its name sounds like an instruction. It is better to read it as an assertion: "this container must not run as root." If Kubernetes can determine that the image would run as UID `0`, or if you explicitly set `runAsUser: 0`, the container is rejected. If the image uses a named user and Kubernetes cannot verify the numeric UID, behavior can depend on runtime details, so explicit numeric `runAsUser` remains the clearer choice.

Before running this, what output do you expect from `id` if the pod sets `runAsUser: 1000`, `runAsGroup: 3000`, and `fsGroup: 2000`? A correct prediction should mention UID `1000`, primary GID `3000`, and a supplementary group that includes `2000`. That prediction gives you a concrete target when you later inspect the pod and avoids treating every permission error as a mystery.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: volume-perms
spec:
  securityContext:
    runAsUser: 1000
    fsGroup: 2000         # Volume files owned by this group
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'ls -la /data && sleep 3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir: {}
```

This `volume-perms` pod is intentionally small because it isolates the behavior. The process runs as UID `1000`, the mounted `emptyDir` appears at `/data`, and `fsGroup: 2000` gives the container a group relationship to that volume. In real storage systems, ownership changes can have performance and driver-specific behavior, but the CKAD-level decision remains the same: use `fsGroup` for pod volume access, not for files already inside the image.

Some images fail after a UID change because their writable directories were owned by root when the image was built. That failure is not Kubernetes being inconsistent; it is Linux permissions doing exactly what they should do. If an image expects to write under `/var/cache/app`, you either need the image to support the non-root UID, or you need to mount a writable volume at the path that should remain mutable.

The most reliable troubleshooting sequence is narrow and repeatable. Inspect events first to distinguish admission and runtime failures, inspect the SecurityContext hierarchy second, then run `id` and directory listings if the container starts. If the container never starts, compare the image default user with your `runAsNonRoot` and `runAsUser` settings. If it starts but cannot write, inspect the target path and decide whether `fsGroup`, an `emptyDir`, or an image rebuild is the right fix.

## Filesystems, Writable Paths, and Read-Only Roots

`readOnlyRootFilesystem: true` makes the container's root filesystem immutable from the process's point of view. That is valuable because an attacker or buggy process cannot rewrite application binaries, configuration files, package manager state, or startup scripts in the image layer. The tradeoff is immediate: many normal applications write temporary files, sockets, PID files, caches, or logs under paths that live on the root filesystem unless you give them explicit writable mounts.

```yaml
securityContext:
  readOnlyRootFilesystem: true     # Container can't write to filesystem
```

A read-only root does not mean the container cannot write anywhere. It means writes must go to mounted volumes or other writable filesystems that you intentionally provide. For short-lived scratch space, `emptyDir` is the usual CKAD answer because it is easy to declare, tied to the pod lifecycle, and does not require a separate storage object. For durable application data, you would choose a persistent volume instead, but that is a storage design decision rather than a SecurityContext shortcut.

The secure nginx-style example below preserves the original module's shape because it demonstrates the exact pairing that learners need to recognize. The container has a read-only root filesystem, drops capabilities, and disables privilege escalation, but it still mounts writable `emptyDir` volumes at `/tmp`, `/var/cache/nginx`, and `/var/run`. The security control remains intact because only the known runtime paths are writable.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    volumeMounts:
    - name: tmp
      mountPath: /tmp
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

The official nginx image listens on port 80 by default. Ports below 1024 traditionally required the `NET_BIND_SERVICE` capability, yet this example drops all capabilities and still starts on many practice clusters because modern container runtimes may set `net.ipv4.ip_unprivileged_port_start=0`, which lets unprivileged processes bind low ports. CKAD tasks that explicitly require binding a port below 1024 still expect you to add `NET_BIND_SERVICE` rather than relying on that runtime sysctl behavior.

Stop and think: if the application now fails with `permission denied` while writing `/var/log/nginx/access.log`, should you disable `readOnlyRootFilesystem`, change the UID, or add a writable mount for the log path? The best answer depends on whether the application truly needs to write there. If the write is expected runtime behavior, add a specific volume mount or reconfigure the app to log to stdout; do not remove the broader read-only root protection just to hide one missing writable path.

The operational habit is to make writable paths boring and explicit. A reviewer should be able to scan the manifest and see that `/tmp` is writable because it is scratch space, `/var/run` is writable because a socket or PID file may be created there, and application data is handled by the right storage type. When those paths are not explicit, an application can pass development tests and fail only after a cluster policy enforces a read-only root.

There is also a packaging lesson here. A well-built container image can run as a non-root UID, write temporary data only to documented paths, and send logs to stdout or stderr. SecurityContext can enforce those expectations, but it cannot magically repair an image that assumes root access to every directory. For CKAD tasks, you usually fix the manifest; for production work, you often fix both the image and the manifest so the contract is clear at every layer.

## Capabilities and Privilege Boundaries

Linux capabilities split some root powers into named privileges. Instead of making a container fully privileged, you can grant a narrow capability such as `NET_BIND_SERVICE` when the process must bind a low-numbered port, or `NET_ADMIN` when it must configure network settings. The safer default is to drop all capabilities and add back only the ones the workload demonstrably needs.

```yaml
securityContext:
  capabilities:
    add:
    - NET_ADMIN          # Network configuration
    - SYS_TIME           # System clock
    drop:
    - ALL                # Remove all capabilities first
```

Capabilities are powerful because they sit below Kubernetes in the Linux kernel. A capability mistake can matter even when the process is not running as UID `0`, because capabilities grant selected privileged operations. That is why "non-root" and "least privilege" are related but not identical. A non-root process with excessive capabilities can still do things that an ordinary application process should never be able to do.

| Capability | Purpose |
|------------|---------|
| `NET_ADMIN` | Network configuration |
| `NET_BIND_SERVICE` | Bind to ports < 1024 |
| `SYS_TIME` | Modify system clock |
| `SYS_PTRACE` | Debug other processes |
| `CHOWN` | Change file ownership |

The table lists common capabilities you may see in examples, not a recommendation to use them casually. `NET_BIND_SERVICE` is much narrower than `NET_ADMIN`, and `SYS_TIME` is rarely appropriate for an application container. When a task asks you to bind a port below 1024, add `NET_BIND_SERVICE` even if your local cluster happens to allow unprivileged low ports through `ip_unprivileged_port_start`. `SYS_PTRACE` can be useful for debugging tools but is risky in normal workloads. `CHOWN` can hide image-permission problems if you use it as a crutch instead of fixing ownership during the build.

```yaml
securityContext:
  allowPrivilegeEscalation: false  # Prevent gaining more privileges
```

`allowPrivilegeEscalation: false` prevents a process from gaining more privileges than its parent process, including through setuid binaries. In Kubernetes, this setting is closely tied to the Linux `no_new_privs` behavior. It is a strong default for application containers because ordinary services should not need to turn a lower-privilege start into a higher-privilege runtime state.

```yaml
securityContext:
  privileged: true      # Full host access (DANGEROUS - rarely needed)
```

`privileged: true` is the opposite end of the spectrum. It gives the container broad host access, including capabilities and device access that bypass the normal confinement model. Some node-level system agents need that kind of access, but most CKAD application pods do not. If a task asks for a capability, add the capability; if it asks for non-root execution, privileged mode is almost certainly the wrong direction.

Which approach would you choose here and why: granting `privileged: true` to let a container adjust iptables rules, or dropping all capabilities and adding only `NET_ADMIN`? The second approach is the minimum-privilege answer because it grants the specific kernel operation without giving the container every privileged operation available. You should still ask whether the application should be changing iptables at all, but the manifest-level choice is clear.

```yaml
securityContext:
  capabilities:
    drop:
    - ALL
    add:
    - NET_BIND_SERVICE
```

The "drop all, add specific" pattern is easy to defend because it makes the exception visible. Reviewers do not need to guess which default capabilities the runtime supplied, and future maintainers can see exactly why a capability was added. In CKAD work, this pattern also prevents accidental over-granting when a question asks for one named capability and nothing more.

Capabilities interact with other controls rather than replacing them. You can run as a non-root UID, disallow privilege escalation, use a read-only root filesystem, and still add one specific capability when needed. That layered approach is practical because each field handles a different failure mode: identity controls the process owner, privilege escalation controls runtime changes, capabilities control kernel powers, and filesystem settings control writable surfaces.

## Verification and Debugging Workflow

SecurityContext debugging should be evidence-driven. Start with the API object's configured fields, then inspect runtime evidence inside the container if it starts. A failed start can be caused by admission policy, image user conflicts, or a runtime check such as `runAsNonRoot`. A running container with permission errors needs a different path: inspect UID, groups, mount ownership, and the exact directory that failed.

```bash
# Check what user process runs as
kubectl exec my-pod -- id
# uid=1000 gid=3000 groups=2000

# Check file ownership in volume
kubectl exec my-pod -- ls -la /data
# drwxrwsrwx 2 root 2000 ...

# Check capabilities
kubectl exec my-pod -- cat /proc/1/status | grep Cap
```

The `id` command tells you the process identity that Linux is actually using. The directory listing tells you whether the target path is writable by that identity or one of its groups. The capability status in `/proc/1/status` is lower-level and encoded, but it is still useful when you need proof that capabilities changed. For CKAD speed, the first two commands usually solve most SecurityContext permission questions.

Do not skip `kubectl describe pod` when a container fails before you can exec into it. Events often say whether Kubernetes refused the container because it would run as root, whether a volume mount failed, or whether the container entered a crash loop after the process started. The difference matters because a SecurityContext admission failure is fixed in the manifest, while an application crash may require writable paths or image-level permission changes.

```yaml
# Pod-level
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
    runAsNonRoot: true

# Container-level
containers:
- name: app
  securityContext:
    runAsUser: 1000
    allowPrivilegeEscalation: false
    readOnlyRootFilesystem: true
    privileged: false
    capabilities:
      drop: ["ALL"]
      add: ["NET_BIND_SERVICE"]
```

This quick reference is intentionally split by level. If you are editing quickly during an exam, it reminds you not to put `fsGroup` under an individual container and not to bury container-only settings at the wrong level. Kubernetes rejects some misplaced fields during validation, but other mistakes are subtler because a valid value at the wrong level changes the wrong scope.

When you inspect a live pod, prefer direct questions over broad dumps. `kubectl get pod secure-pod -o yaml` is useful, but it can bury the relevant lines in a long document. A focused JSONPath can be faster when you know the field, while `describe` is better for events and high-level state. The key is to move from symptom to evidence, not from symptom to guess.

```bash
kubectl get pod secure-pod -o jsonpath='{.spec.securityContext}{"\n"}'
kubectl get pod secure-pod -o jsonpath='{.spec.containers[0].securityContext}{"\n"}'
kubectl describe pod secure-pod
```

If a pod runs as the wrong user, inspect both pod and container contexts before editing. If a volume is not writable, inspect `id`, the mount path, and the pod-level `fsGroup`. If a read-only root breaks startup, identify the exact path being written and mount a volume there. If the issue involves privileged behavior, compare the requested operation with the current capabilities instead of jumping directly to `privileged: true`.

## Worked Example: Designing a Secure Pod

Exercise scenario: you receive a CKAD task that asks for a pod named `secure-pod` running `nginx`, with a non-root UID, no privilege escalation, a read-only root filesystem, and writable temporary directories. The naive version sets `runAsNonRoot: true` and `readOnlyRootFilesystem: true`, then fails because nginx expects runtime write paths. The successful version pairs each restriction with the minimal supporting configuration.

The first decision is identity. Because the task requires non-root behavior, set `runAsNonRoot: true` and specify a numeric `runAsUser`, rather than relying on the image default. The second decision is writable paths. Because the root filesystem is read-only, add `emptyDir` mounts for paths that nginx writes at runtime. The third decision is privilege. Because the application does not need extra kernel powers, disable privilege escalation and drop all capabilities.

This example is not asking you to memorize nginx internals. It is teaching the diagnostic shape that applies to many images: after you lock down identity and the root filesystem, watch for specific paths that still need runtime writes. Mount only those paths, keep the rest of the image immutable, and leave capability additions out unless the task gives you a concrete reason.

The resulting manifest is the earlier secure pod example, and it is deliberately CKAD-friendly. It uses one pod, one container, clear numeric IDs, and explicit volume mounts. During verification, you can run `kubectl logs secure-pod` to confirm the process starts, `kubectl exec secure-pod -- id` to confirm identity, and `kubectl exec secure-pod -- touch /test` to confirm the root remains read-only. Those checks tie the YAML to observable behavior.

The same reasoning also applies when you are repairing an existing manifest. Read the current fields, identify which requirement is missing, and make the smallest change that satisfies that requirement without weakening another one. Adding an `emptyDir` to `/tmp` is a small change. Removing `readOnlyRootFilesystem` because one path needs writes is a broad weakening, and broad weakenings are rarely the correct answer in an exam or in review.

## Policy Context and Exam Triage

SecurityContext is workload configuration, not cluster policy, but the two meet at admission time. A namespace can run an admission policy that checks the pod before it is scheduled, and a pod that violates that policy may never create a running container. That is why the first debugging question is whether Kubernetes rejected the pod specification or whether the container process started and then failed. The same YAML field can be part of both stories, but the evidence appears in different places.

Kubernetes Pod Security Admission uses namespace labels to apply Pod Security Standards such as privileged, baseline, and restricted. As a CKAD candidate, you are not expected to administer the whole admission system, but you are expected to write workloads that can survive restricted environments. When a namespace enforces a restricted profile, settings such as `privileged: true`, broad capabilities, missing non-root controls, and privilege escalation become more than review comments. They can become hard rejection reasons before the scheduler gets involved.

The restricted profile is useful because it translates a broad security goal into concrete manifest checks. It does not merely say "be safer"; it looks for specific high-risk settings. A privileged container is rejected because it receives broad host-level access. A container that allows privilege escalation is rejected because it can gain more privilege after start. Capability rules push you toward dropping `ALL` and adding back only narrowly allowed exceptions such as `NET_BIND_SERVICE`.

Admission errors are often more actionable than they first appear. They usually name a field path, a denied value, or the control family that failed. If the message points at `securityContext.privileged`, remove privileged mode and decide which smaller capability, if any, the workload really needs. If the message points at capability additions, compare the requested capability with the restricted profile. If it points at non-root execution, inspect whether the pod sets `runAsNonRoot`, `runAsUser`, or a container override that contradicts the pod default.

Runtime errors tell a different story because the container has already started. A log line about failing to write a cache file is not an admission failure; it is the process meeting Linux permissions. A crash after enabling a read-only root filesystem is not proof that the policy is too strict; it is evidence that the manifest has not declared all writable runtime paths. Keeping those categories separate prevents you from fixing a runtime path problem by weakening admission-facing security controls.

Exercise scenario: a pod is accepted in a development namespace but rejected in a restricted practice namespace. The manifest runs as UID `1000`, but one sidecar sets `allowPrivilegeEscalation: true` and adds `SYS_PTRACE` for debugging. The correct repair is not to change the main container identity. The correct repair is to remove or justify the sidecar privilege settings, because the rejection comes from a container-level exception that violates the namespace policy.

The same reasoning helps with warnings. Some clusters configure Pod Security labels in warn or audit mode before they enforce the policy. A warning is not a pass; it is a preview of a future rejection. If you see a warning about a SecurityContext field while practicing, treat it as a free hint. Repair the manifest while the workload still starts, then verify that the warning disappears before relying on the pod in a stricter namespace.

Kubernetes 1.35+ work should use Pod Security Admission terminology rather than older PodSecurityPolicy assumptions. PodSecurityPolicy was removed from Kubernetes years earlier, so a modern CKAD answer should not depend on creating or binding a PSP object. For workload authors, the practical outcome is simpler: write pod specs that satisfy the namespace policy directly. SecurityContext fields are the workload-side controls you can edit without needing cluster-admin permissions.

When an exam task mentions a restricted namespace, read that as a constraint on the manifest design. Start with non-root identity, avoid privileged mode, disable privilege escalation, drop capabilities, and provide explicit writable paths if you enable a read-only root. Then check whether the task asks for a specific exception. If it does not, do not add one. A manifest that passes without an exception is easier to explain and less likely to collide with admission.

There is one subtle trap: admission can validate fields without knowing every runtime file permission problem. A pod can satisfy restricted policy and still fail because the image writes to a root-owned directory. That is not a policy failure; it is an image and filesystem contract failure. The repair is to mount the required writable path, configure the application to write somewhere appropriate, or rebuild the image with ownership that matches the configured UID.

Use a two-column mental checklist even when you do not write it down. On the policy side, ask whether the manifest uses forbidden privileges, allows escalation, runs as root, or keeps broad capabilities. On the runtime side, ask whether the process identity can read and write the paths it actually needs. A secure pod must satisfy both columns. Passing admission is necessary, but it does not prove the application has the right writable directories.

This policy context is also why SecurityContext belongs in application reviews. The fields are close to the workload, but they express cluster-wide expectations about blast radius and isolation. A reviewer can compare the declared exception with the application need: a web server may need a writable cache directory, but it should not need `SYS_TIME`; a metrics sidecar may need a mounted socket, but it should not automatically receive privileged mode. That review discipline turns YAML fields into enforceable engineering decisions.

## Patterns & Anti-Patterns

SecurityContext patterns are useful only when they preserve a specific property. "Secure everything" is too vague to guide a manifest edit, so each pattern below names the situation where it applies and the tradeoff it introduces. The common theme is explicit least privilege: state the user, state the writable paths, state the capabilities, and let Kubernetes reject configurations that violate the contract.

| Pattern | When to Use | Why It Works | Scaling Consideration |
|---------|-------------|--------------|-----------------------|
| Pod-level identity defaults | All containers can share the same UID, GID, and volume group | Reduces repeated YAML while keeping the pod contract visible | Sidecars with different image ownership may need container overrides |
| Read-only root plus named writable mounts | Application needs runtime scratch paths but should not mutate image files | Keeps the image layer immutable while allowing expected writes | Document every writable path so later changes do not add hidden state |
| Drop all capabilities and add one back | A workload needs one named kernel permission | Makes the exception reviewable and avoids runtime defaults | Capability additions should be tied to an application requirement |
| Runtime verification after manifest edits | Security fields were changed under time pressure | Confirms the effective UID, groups, and writable paths | Automate checks in CI for repeated workloads, but know the manual commands |

Anti-patterns usually come from trying to fix a symptom without identifying the layer that caused it. A pod that cannot write to a mounted volume does not automatically need root. A container that needs port binding does not automatically need privileged mode. A startup failure after `runAsNonRoot` does not mean the setting is bad; it means the image or manifest still wants root.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Setting `privileged: true` to fix unknown errors | Grants broad host-level access and hides the real failure | Inspect events, UID, groups, paths, and capabilities first |
| Using `runAsNonRoot` without a numeric UID | The image may still resolve to root or be unverifiable | Pair it with `runAsUser: 1000` or another known non-zero UID |
| Disabling `readOnlyRootFilesystem` for one write path | Makes the whole image layer mutable again | Mount an `emptyDir` or suitable volume at the required path |
| Adding broad capabilities before testing | Gives the process kernel powers it may not need | Drop all capabilities, then add only the named requirement |

These patterns scale because they keep troubleshooting local. When a pod fails, you can ask which promise is broken: identity, writable path, capability, or privilege escalation. When the answer is local, the fix is usually local too. That habit matters in larger clusters, where a quick but broad relaxation can create a policy exception that outlives the original incident.

## Decision Framework

Use this framework when you are deciding where to place a setting or how to repair a failure. The goal is not to make every workload identical. The goal is to make every workload explicit enough that Kubernetes, reviewers, and future operators can understand the security boundary. Move from identity to filesystem to privileges because that order matches the most common CKAD symptoms.

```
Start with the symptom
        |
        v
Does the pod fail before the process starts?
        |
        +-- yes --> Check events for runAsNonRoot, UID, policy, or validation errors
        |
        +-- no  --> Can the process write the path it needs?
                       |
                       +-- no  --> Check id, ls -la, fsGroup, and writable volume mounts
                       |
                       +-- yes --> Does the app need a kernel-level operation?
                                      |
                                      +-- yes --> Drop ALL capabilities, add the named capability
                                      |
                                      +-- no  --> Keep privilege escalation false and root read-only
```

The first branch separates configuration rejection from application behavior. If the container never starts, `kubectl exec` cannot help yet, so events and manifest inspection come first. If the process starts and then logs permission errors, the kernel is already enforcing identity and filesystem rules, so your evidence should come from `id`, directory ownership, and the specific write target.

| Question | Choose This | Avoid This |
|----------|-------------|------------|
| Do all containers share the same UID and GID? | Pod-level `runAsUser` and `runAsGroup` | Repeating identical values in every container without reason |
| Does one container need a different UID? | Container-level `runAsUser` override | Changing the pod default and breaking other containers |
| Does a mounted volume need group write access? | Pod-level `fsGroup` | Trying to set `fsGroup` under one container |
| Does the image need `/tmp` while root is read-only? | `emptyDir` mounted at `/tmp` | Disabling `readOnlyRootFilesystem` globally |
| Does the process need one kernel privilege? | Drop `ALL`, add the named capability | Setting `privileged: true` |

The framework also tells you when SecurityContext is not the only answer. If the image writes into hard-coded root-owned application directories, a manifest can mount over those paths, but the better long-term fix may be rebuilding the image with correct ownership and configurable paths. Kubernetes can enforce a safer runtime, yet image design still determines how easy that runtime is to achieve.

For CKAD speed, memorize the decision order rather than every possible field. Identity failures need `runAsUser`, `runAsGroup`, and `runAsNonRoot`. Volume permission failures point toward `fsGroup` and directory ownership. Read-only filesystem failures point toward explicit writable mounts. Privilege requests point toward capabilities first and privileged mode only when a workload is truly a node-level system component.

## Did You Know?

- Kubernetes documents SecurityContext separately for pods and containers because `PodSecurityContext` and `SecurityContext` are different API objects with overlapping but non-identical fields.
- `NET_BIND_SERVICE` exists because Unix-like systems historically restricted binding ports below `1024` to privileged processes; some modern runtimes relax that through `ip_unprivileged_port_start`, but CKAD still expects the capability when a task requires a low port.
- `allowPrivilegeEscalation: false` maps to the Linux `no_new_privs` idea, which prevents a process from gaining privilege through exec transitions.
- `fsGroup` affects supported mounted volumes, not ordinary files already baked into the container image layer.

## Common Mistakes

Most SecurityContext mistakes are small YAML choices with large runtime effects. The fix is usually not to remove security controls, but to put the right control at the right level and verify the result with one concrete command. Use this table as a debugging checklist when a pod fails under a restricted policy or starts with file permission errors.

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| `runAsNonRoot` with an image that still runs as root | The flag validates non-root behavior but does not choose a UID | Add a numeric non-zero `runAsUser`, then verify with `kubectl exec POD -- id` |
| `readOnlyRootFilesystem` without writable runtime mounts | The image writes temp files, sockets, caches, or PID files under root paths | Mount `emptyDir` volumes at the exact writable paths, such as `/tmp` or `/var/run` |
| Not dropping capabilities before adding one | Runtime defaults may leave more kernel powers than the workload needs | Set `capabilities.drop: ["ALL"]`, then add only the named capability |
| Confusing pod-level and container-level context | Some fields overlap, while others are valid only at one level | Put shared defaults and `fsGroup` at pod level; put privilege controls at container level |
| Using `privileged: true` as a generic fix | It bypasses many normal isolation boundaries and hides the real requirement | Identify whether the workload needs identity, filesystem, or one capability change |
| Setting `fsGroup` to fix image-layer permissions | `fsGroup` is aimed at supported volumes, not files baked into the image | Rebuild the image with correct ownership or mount a writable volume at the path |
| Ignoring events when a pod never starts | There is no container process to inspect yet, so `exec` cannot work | Use `kubectl describe pod` and read the failure reason before changing YAML |

## Quiz

<details>
<summary>Question 1: Your pod sets `runAsNonRoot: true`, but the container fails with a message saying the image will run as root. What is the problem, and what manifest change should you make?</summary>

`runAsNonRoot: true` is a validation check, not a UID assignment. Kubernetes is refusing to start the container because the effective image user is root or cannot be accepted as non-root. Add an explicit numeric non-zero `runAsUser`, such as `1000`, at the pod or container level that matches the workload. If the image then hits file permission errors, keep the non-root setting and repair writable paths or image ownership instead of removing the guardrail.

</details>

<details>
<summary>Question 2: After enabling `readOnlyRootFilesystem: true`, an nginx container fails while writing `/var/cache/nginx`. How do you keep the security benefit and make the pod start?</summary>

Keep the read-only root filesystem and mount a writable volume at the specific path that needs runtime writes. For this image shape, an `emptyDir` at `/var/cache/nginx` is appropriate, and the manifest may also need writable mounts at `/tmp` and `/var/run`. Disabling `readOnlyRootFilesystem` would make the whole image layer mutable again, which is a broader change than the symptom requires. The correct fix preserves the restriction and documents the expected writable directories.

</details>

<details>
<summary>Question 3: A pod has `spec.securityContext.runAsUser: 1000`. Container A has no container SecurityContext, while Container B sets `runAsUser: 2000`. Which UID does each container use, and what should you inspect next if a shared volume is not writable?</summary>

Container A inherits UID `1000` from the pod-level SecurityContext, while Container B runs as UID `2000` because the container-level field overrides the pod default for that container. If a shared volume is not writable, inspect the pod-level `fsGroup`, the process groups with `id`, and the directory ownership with `ls -la`. The UID override explains process identity, but volume access often depends on group ownership. Changing both containers to root would hide the real volume permission issue.

</details>

<details>
<summary>Question 4: Your team needs a container to bind a low-numbered port, and someone proposes `privileged: true`. What is the least-privilege SecurityContext approach?</summary>

Do not use privileged mode for a narrow port-binding requirement. Drop all capabilities first, then add `NET_BIND_SERVICE` if the process truly must bind a port below `1024`. This grants the specific kernel permission without broad host access. You should also consider whether the application can listen on a higher container port and let the Service expose the desired port, because avoiding the capability entirely is even simpler when the application supports it.

</details>

<details>
<summary>Question 5: A pod starts successfully as UID `1000`, but `touch /data/file` fails with permission denied on an `emptyDir` mounted at `/data`. What do you check and change?</summary>

First run `id` inside the container and `ls -la /data` to compare the process UID and groups with the directory ownership and mode. If the directory needs group access for the pod, set a pod-level `fsGroup` that matches the intended group ownership. `fsGroup` is the right lever for supported mounted volumes, while `runAsUser` controls the process UID. If the path were inside the image rather than a volume, an image ownership fix or writable mount would be more appropriate.

</details>

<details>
<summary>Question 6: You inspect a manifest and find `fsGroup` under `containers[0].securityContext`. Why is that suspicious, and where should the setting live?</summary>

`fsGroup` is pod-scoped because it affects supported mounted volumes for the pod, not just one container's process. It belongs under `spec.securityContext`, alongside other pod-level defaults. Container-level SecurityContext is the place for fields such as `allowPrivilegeEscalation`, `readOnlyRootFilesystem`, and per-container capability changes. Moving `fsGroup` to the pod level makes the scope match the resource being configured.

</details>

<details>
<summary>Question 7: A restricted namespace rejects a pod that sets `privileged: true`, but the workload only needs to inspect its own process identity and write temporary files. How would you redesign the pod?</summary>

Remove `privileged: true` because the described workload does not need host-level access. Set a non-root UID with `runAsUser` and `runAsNonRoot`, disable privilege escalation, drop all capabilities, and enable a read-only root filesystem if the image can support it. Add an `emptyDir` at `/tmp` or any other documented temporary path. This design satisfies the actual needs while aligning with restricted policy expectations.

</details>

## Hands-On Exercise

This exercise turns the module's decisions into observable pod behavior. Run the commands in a disposable namespace if you are using a shared cluster, and delete each pod before moving on if your environment has tight resource quotas. The manifests use BusyBox and nginx because they make identity, file writes, and runtime directories easy to inspect without additional application code.

The tasks progress from identity to volume ownership to read-only filesystem behavior and finally to a combined secure pod. For each task, predict the result before running the verification command. That habit matters because SecurityContext work is easier when you know whether you are testing UID, group ownership, writable paths, or capabilities.

**Task**: Configure security settings for pods.

- [ ] Implement a pod-level `runAsUser` and `runAsGroup`, then verify the process identity with logs.
- [ ] Diagnose how `fsGroup` changes mounted volume ownership for a non-root process.
- [ ] Prove that `readOnlyRootFilesystem` blocks writes to the image layer while keeping the pod running.
- [ ] Evaluate a capability-only change by dropping all capabilities and adding `NET_BIND_SERVICE`.
- [ ] Design a CKAD-ready secure pod manifest with non-root identity, read-only root, dropped capabilities, and a writable mounted path.

### Part 1: Run as Non-Root

The first pod is a minimal identity check. It sets a UID and primary GID at pod level, runs `id`, and then sleeps so you can inspect it if needed. The expected output should show the configured UID and GID, which proves the process identity came from the SecurityContext rather than from the image default.

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: nonroot-pod
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'id && sleep 3600']
EOF

kubectl wait --for=condition=ready pod/nonroot-pod --timeout=30s
kubectl logs nonroot-pod
# Should show: uid=1000 gid=3000 groups=3000
```

<details>
<summary>Solution notes for Part 1</summary>

If the pod becomes ready, `kubectl logs nonroot-pod` should show UID `1000` and GID `3000`. If it does not, inspect `kubectl describe pod nonroot-pod` for image pull or scheduling problems before changing the SecurityContext. This task isolates process identity only; it does not test `fsGroup` because no volume is mounted.

</details>

### Part 2: fsGroup Demo

The second pod adds a mounted `emptyDir` and a pod-level `fsGroup`. This is the smallest useful demonstration of the difference between process identity and volume ownership. The process still runs as UID `1000`, but the mounted directory should show group behavior associated with `2000`.

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: fsgroup-pod
spec:
  securityContext:
    runAsUser: 1000
    fsGroup: 2000
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'ls -la /data && id && sleep 3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir: {}
EOF

kubectl wait --for=condition=ready pod/fsgroup-pod --timeout=30s
kubectl logs fsgroup-pod
# Files in /data owned by group 2000
```

<details>
<summary>Solution notes for Part 2</summary>

The log output should show the `/data` directory and the process identity. Look for group `2000` in the ownership or group list. If your storage driver handles ownership differently, focus on the concept: `fsGroup` is declared at pod level because mounted volumes are pod resources, and you verify it by comparing `id` with `ls -la`.

</details>

### Part 3: Read-Only Filesystem

The third pod intentionally attempts to write to the root filesystem. The command catches the failure and prints a clear message, so the pod should still become ready. This gives you a safe way to prove that the root filesystem is read-only without turning the exercise into a crash-loop debugging task.

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: readonly-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'touch /test 2>&1 || echo "Cannot write!"; sleep 3600']
    securityContext:
      readOnlyRootFilesystem: true
EOF

kubectl wait --for=condition=ready pod/readonly-pod --timeout=30s
kubectl logs readonly-pod
# Should show: Cannot write!
```

<details>
<summary>Solution notes for Part 3</summary>

The message confirms that writes to `/test` are blocked by the read-only root filesystem. This is expected and desirable. If an application genuinely needs a writable path, mount a volume at that path instead of disabling the security setting for the whole root filesystem.

</details>

### Cleanup

Clean up the first three pods before running the drills if your cluster has tight pod quotas. The force flags are acceptable for this disposable exercise because the pods do not manage durable state. In a production namespace, prefer normal deletion unless you have a reason to bypass graceful termination.

```bash
kubectl delete pod nonroot-pod fsgroup-pod readonly-pod --force --grace-period=0
```

### Drill 1: Run As User

This drill repeats the UID assignment without the extra group field. Its purpose is speed: you should be able to produce the manifest, wait for readiness, read the log, and delete the pod without looking up field placement. The verification signal is the `id` output.

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill1
spec:
  securityContext:
    runAsUser: 1000
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'id && sleep 3600']
EOF

kubectl wait --for=condition=ready pod/drill1 --timeout=30s
kubectl logs drill1
kubectl delete pod drill1 --force --grace-period=0
```

### Drill 2: Non-Root Enforcement

This drill pairs `runAsNonRoot` with an explicit UID so the guardrail has a concrete non-root identity to enforce. If you remove `runAsUser`, the behavior can depend on the image's declared user. With the UID present, the pod specification communicates the non-root requirement clearly.

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill2
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
  containers:
  - name: app
    image: busybox
    command: ['sleep', '3600']
EOF

kubectl wait --for=condition=ready pod/drill2 --timeout=30s
kubectl get pod drill2
kubectl delete pod drill2 --force --grace-period=0
```

### Drill 3: Capabilities

This drill demonstrates the minimum-privilege capability pattern. The container drops every capability and adds back only `NET_BIND_SERVICE`. The `/proc/1/status` output is encoded, so do not treat it as a beginner-friendly report; use it as proof that capability state is observable from inside the container.

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill3
spec:
  containers:
  - name: app
    image: busybox
    command: ['sleep', '3600']
    securityContext:
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
EOF

kubectl wait --for=condition=ready pod/drill3 --timeout=30s
kubectl exec drill3 -- cat /proc/1/status | grep Cap
kubectl delete pod drill3 --force --grace-period=0
```

### Drill 4: Read-Only with Temp

This drill combines a read-only root filesystem with a writable `/tmp` mount. The command writes to `/tmp`, not to the image root, so it should succeed. The pattern is the one you will use whenever an application needs scratch space but the rest of the filesystem should remain immutable.

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill4
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'touch /tmp/test && echo "Wrote to /tmp" && sleep 3600']
    securityContext:
      readOnlyRootFilesystem: true
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
EOF

kubectl wait --for=condition=ready pod/drill4 --timeout=30s
kubectl logs drill4
kubectl delete pod drill4 --force --grace-period=0
```

### Drill 5: fsGroup Verification

This drill writes a file into a mounted volume and lists the directory. It helps connect `fsGroup` to the files created under a volume mount. If the output differs across storage backends, explain the difference in terms of volume ownership behavior rather than changing the pod to root.

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill5
spec:
  securityContext:
    fsGroup: 2000
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'touch /data/file && ls -la /data && sleep 3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir: {}
EOF

kubectl wait --for=condition=ready pod/drill5 --timeout=30s
kubectl logs drill5
# File should be owned by group 2000
kubectl delete pod drill5 --force --grace-period=0
```

### Drill 6: Complete Secure Pod

The final drill combines the pieces into one secure pod. It runs as a non-root UID, supplies a group for volume access, disables privilege escalation, makes the root filesystem read-only, and drops capabilities. The mounted `/data` path gives the process a deliberate writable location without weakening the image layer.

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill6
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 2000
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'id && ls -la /data && sleep 3600']
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir: {}
EOF

kubectl wait --for=condition=ready pod/drill6 --timeout=30s
kubectl logs drill6
kubectl get pod drill6 -o yaml | grep -A20 securityContext
kubectl delete pod drill6 --force --grace-period=0
```

<details>
<summary>Solution notes for Drill 6</summary>

The logs should show UID `1000`, primary GID `1000`, and group access that includes the volume group. The YAML inspection should show both pod-level and container-level security settings. If the pod fails, use `kubectl describe pod drill6` first, then check whether the failure is identity validation, image behavior, or a writable path issue.

</details>

## Learner check

> CKAD tasks that explicitly require binding a port below 1024 still expect you to add `NET_BIND_SERVICE` rather than relying on that runtime sysctl behavior.

## Sources

- https://kubernetes.io/docs/tasks/configure-pod-container/security-context/
- https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.35/#securitycontext-v1-core
- https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.35/#podsecuritycontext-v1-core
- https://kubernetes.io/docs/concepts/security/pod-security-standards/
- https://kubernetes.io/docs/concepts/security/linux-kernel-security-constraints/
- https://kubernetes.io/docs/concepts/storage/volumes/#emptydir
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_exec/
- https://man7.org/linux/man-pages/man7/capabilities.7.html
- https://man7.org/linux/man-pages/man2/setuid.2.html
- https://man7.org/linux/man-pages/man2/setgid.2.html

## Next Module

[Module 4.5: ServiceAccounts](../module-4.5-serviceaccounts/) - Next you will connect pod identity to Kubernetes API access, where ServiceAccounts determine what a workload can authenticate as and which permissions it can request inside the cluster.
