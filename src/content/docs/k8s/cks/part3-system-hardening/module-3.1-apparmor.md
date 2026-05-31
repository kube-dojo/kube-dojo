---
title: "Module 3.1: AppArmor for Containers"
slug: k8s/cks/part3-system-hardening/module-3.1-apparmor
revision_pending: false
sidebar:
  order: 1
lab:
  id: cks-3.1-apparmor
  url: https://killercoda.com/kubedojo/scenario/cks-3.1-apparmor
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Linux security essential
>
> **Time to Complete**: 40 minutes
>
> **Prerequisites**: Linux basics, container runtime knowledge

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Design** AppArmor profiles that restrict container file access, network use, and selected Linux capabilities without breaking normal application startup.
2. **Apply** AppArmor confinement to Kubernetes 1.35+ pods with `securityContext.appArmorProfile`, while recognizing the older annotation format used in legacy examples.
3. **Diagnose** AppArmor denials by combining pod events, node profile state, `/proc` inspection, `dmesg`, and `journalctl` evidence.
4. **Audit** node and workload configuration to confirm that every scheduled container is running under the intended AppArmor profile.

---

## Why This Module Matters

Hypothetical scenario: a containerized web application is compromised through an application bug, and the attacker tries the next ordinary moves: read sensitive local files, write a helper binary into a writable path, change kernel-facing settings, and open network connections that the application never needed. Kubernetes RBAC does not stop that sequence because the attacker is already inside the process. NetworkPolicy may limit some traffic, and a read-only root filesystem may block some writes, but neither one describes the full set of file, network, and capability operations that the process should be allowed to perform on the node.

AppArmor is one of the tools that narrows that gap. It is a Linux Security Module that labels a running program with a named profile, then asks that profile whether each sensitive operation should be allowed. In container work, that profile becomes a second perimeter around the process. The container image still supplies the filesystem, Kubernetes still schedules the pod, and the runtime still creates the sandbox, but the kernel enforces the final yes-or-no decision when the process touches files, uses networking, or requests Linux capabilities.

For CKS work, the skill is not memorizing every AppArmor rule. The skill is translating an operational intent into a small profile, loading that profile on the right nodes, applying it with the current Kubernetes API, and proving that the kernel is enforcing what you think it is enforcing. This module keeps the original exam-flavored examples, updates the Kubernetes surface for 1.35+, and gives you a repeatable debugging path for the moments when a pod fails because the profile is missing, too strict, or applied to the wrong container.

---

## How AppArmor Fits Into Container Defense

AppArmor is easiest to reason about if you separate discretionary access control from mandatory access control. Traditional Unix permissions ask whether the user ID and group ID are allowed to touch an object. Mandatory access control adds a second question: even if the process has normal Unix permission, does the policy assigned by the operating system allow this program to perform this operation? That second question matters for containers because a compromised process often runs with all the ordinary permissions its application needed before compromise.

The container runtime may already apply a default AppArmor profile, especially on Ubuntu-style nodes. That default profile is useful, but it is deliberately generic because it has to run many workloads without knowing their business logic. A custom profile is different: it describes one workload's expected behavior. A static web server and a log shipper both need files and networking, yet they need different paths, different write locations, and different tolerance for privileged kernel operations.

The original overview diagram is worth preserving because it shows the decision point correctly: the application does not call AppArmor directly. The process makes a system call, the kernel reaches the AppArmor hook for the relevant operation, and the active profile decides whether that operation continues. The practical consequence is that an AppArmor denial can appear as an ordinary application error, such as "permission denied," even though Unix file mode bits look permissive.

```text
+-----------------------------------------------------------+
|              APPARMOR OVERVIEW                            |
+-----------------------------------------------------------+
|                                                           |
|  AppArmor = Application Armor                             |
|  -------------------------------------------------------  |
|  - Mandatory Access Control (MAC) system                  |
|  - Restricts per-program capabilities                     |
|  - Default on Ubuntu, Debian                              |
|  - Alternative to SELinux on many RHEL-family systems     |
|                                                           |
|  How it works:                                            |
|                                                           |
|  +-----------------+     +-----------------+              |
|  |  Application    | --> |  System Call    |              |
|  |  (Container)    |     |                 |              |
|  +-----------------+     +--------+--------+              |
|                                   |                       |
|                                   v                       |
|                          +-----------------+              |
|                          |  AppArmor       |              |
|                          |  Profile Check  |              |
|                          +--------+--------+              |
|                                   |                       |
|                      +------------+------------+          |
|                      v                         v          |
|                 +---------+              +---------+      |
|                 | ALLOWED |              | DENIED  |      |
|                 +---------+              +---------+      |
|                                                           |
+-----------------------------------------------------------+
```

The mode of a profile changes how that decision point behaves. Enforce mode blocks operations that the profile does not allow and records the denial. Complain mode records what would have been denied but lets the application continue. Disabled or unconfined execution removes that profile from the process, which may be acceptable for a short diagnostic comparison but should not be the steady state for a production workload that can be confined.

```text
+-----------------------------------------------------------+
|              APPARMOR PROFILE MODES                       |
+-----------------------------------------------------------+
|                                                           |
|  Enforce Mode                                             |
|  - Policy is enforced, violations are blocked and logged  |
|    aa-enforce /path/to/profile                            |
|                                                           |
|  Complain Mode                                            |
|  - Policy violations are logged but not blocked           |
|    aa-complain /path/to/profile                           |
|    Useful for testing new profiles                        |
|                                                           |
|  Disabled / Unconfined                                    |
|  - No AppArmor restrictions applied                       |
|                                                           |
+-----------------------------------------------------------+
```

Complain mode is where many successful profiles begin. You place the profile around a realistic workload, exercise normal behavior, read the logged would-be denials, and decide whether the application truly needs those operations. That workflow is slower than writing a deny rule and hoping, but it avoids an unsafe trade: a profile that looks strict in a manifest and then prevents the application from starting under real traffic.

Pause and predict: if a new profile denies writes under `/etc/**`, what do you expect from an image that generates configuration files in `/etc/nginx/conf.d/` before launching nginx? The important answer is not just "it might fail." The important answer is that the failure will surface at the application layer first, while the reason you trust is in the kernel log where AppArmor records the blocked write.

You can inspect a node before you touch a pod. The first command checks whether the kernel module is enabled. The second asks the AppArmor tooling for a summary. The third confirms that the kernel has loaded profiles registered for enforcement. In a CKS-style environment, these checks also keep you from debugging a Kubernetes manifest when the real problem is that the node cannot enforce the profile. CKS and kind lab nodes are containerd-first; `docker` is often absent, so do not rely on `docker info` for AppArmor support.

```bash
# Check if AppArmor is enabled (kernel module)
cat /sys/module/apparmor/parameters/enabled
# Output: Y (enabled) or N (disabled)

# Check AppArmor status (loaded profiles and modes)
sudo aa-status

# Output example:
# apparmor module is loaded.
# 39 profiles are loaded.
# 38 profiles are in enforce mode.
#    /usr/bin/evince
#    /usr/sbin/cupsd
#    docker-default
# 1 profiles are in complain mode.
# 10 processes have profiles defined.

# List loaded profiles
sudo aa-status --profiles

# containerd / CRI nodes: confirm profiles are visible to the kernel
# (no docker CLI required)
sudo grep -E '^profile ' /sys/kernel/security/apparmor/profiles | head
# Or list profile names from aa-status
sudo aa-status --profiles
```

The container runtime's default profile is a baseline, not a workload policy. Docker historically called its default profile `docker-default`, and containerd installations often expose a runtime default profile through Kubernetes as `RuntimeDefault`. These profiles usually block dangerous operations such as mounting filesystems, writing to sensitive `/proc` paths, and using raw network features, while allowing enough behavior for normal containers to start.

```bash
# Docker/containerd use a runtime default profile
# This profile commonly:
# - Denies mounting filesystems
# - Denies access to /proc/sys
# - Denies raw network access
# - Allows normal container operations

# Check a Docker default profile location when present
cat /etc/apparmor.d/containers/docker-default 2>/dev/null || \
  cat /etc/apparmor.d/docker 2>/dev/null
```

The default profile is the right first step when a workload has no reason to run unconfined. A custom profile is the next step when you can describe a tighter intent, such as "this container may read most files, write only to `/tmp`, and never open a network socket." Treat those custom profiles as node assets. Kubernetes references the profile by name, but the kernel on the selected node must already know that name before kubelet can run the container with it.

---

## Designing Profiles That Match Container Behavior

An AppArmor profile is a contract between the application behavior you expect and the kernel operations you will tolerate. Good profiles start with a narrow statement of purpose: this process reads its packaged assets, writes temporary files, serves HTTP, and never needs to read account databases or rewrite node-level kernel settings. Poor profiles start with a copied deny list and no model of the application, which means the first production traffic spike becomes the real test suite.

Profiles are stored and loaded on each node, not stored inside the Kubernetes API. That distinction is easy to miss because the pod manifest looks like the place where the security decision lives. The manifest only names the profile. The profile content is local to the host, parsed by AppArmor tooling, and registered with the kernel. If two nodes have different files under `/etc/apparmor.d/`, the same pod manifest can behave differently after rescheduling.

```bash
# AppArmor profiles are stored in:
/etc/apparmor.d/

# For Kubernetes, create profiles in:
/etc/apparmor.d/
# Profile must be loaded on each node where pod might run
```

The profile skeleton below is intentionally small but representative. It includes global tunables, base abstractions, file rules, network rules, capability rules, and explicit deny rules. The `attach_disconnected` and `mediate_deleted` flags are commonly used for container profiles because containers can expose paths that do not look like ordinary host paths from the kernel's point of view, especially around mount namespaces and deleted-but-still-open files.

```text
#include <tunables/global>

profile my-container-profile flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # File access rules
  /etc/passwd r,                    # Read /etc/passwd
  /var/log/myapp/** rw,             # Read/write to log directory
  /tmp/** rw,                       # Read/write to tmp

  # Network rules
  network inet tcp,                 # Allow TCP
  network inet udp,                 # Allow UDP

  # Capability rules
  capability net_bind_service,      # Allow binding to ports < 1024

  # Deny rules
  deny /etc/shadow r,               # Deny reading shadow
  deny /proc/sys/** w,              # Deny writing to /proc/sys
}
```

The syntax looks compact because AppArmor is designed to be read as policy rather than as program code. A path followed by `r` grants read access. A path followed by `w` grants write access. A trailing `/**` applies recursively beneath a directory. Network and capability rules use their own namespaces, so `network inet tcp,` is not a file path, and `capability net_bind_service,` is not a Linux command.

```text
+-----------------------------------------------------------+
|              APPARMOR RULE SYNTAX                         |
+-----------------------------------------------------------+
|                                                           |
|  File Access:                                             |
|  -------------------------------------------------------  |
|  /path/to/file r,        # Read                           |
|  /path/to/file w,        # Write                          |
|  /path/to/file rw,       # Read and Write                 |
|  /path/to/file a,        # Append                         |
|  /path/to/file ix,       # Execute, inherit profile       |
|  /path/to/dir/ r,        # Read directory                 |
|  /path/to/dir/** rw,     # Recursive read/write           |
|                                                           |
|  Network:                                                 |
|  -------------------------------------------------------  |
|  network,                # Allow all networking           |
|  network inet,           # IPv4                           |
|  network inet6,          # IPv6                           |
|  network inet tcp,       # IPv4 TCP only                  |
|  network inet udp,       # IPv4 UDP only                  |
|                                                           |
|  Capabilities:                                            |
|  -------------------------------------------------------  |
|  capability dac_override, # Bypass file permissions       |
|  capability net_admin,    # Network admin                 |
|  capability sys_ptrace,   # Trace processes               |
|                                                           |
|  Deny:                                                    |
|  -------------------------------------------------------  |
|  deny /path/file w,      # Explicitly deny and log        |
|                                                           |
+-----------------------------------------------------------+
```

The following profile preserves the original module's deny-write example. It allows general file reads through the `file,` rule, then explicitly denies writes everywhere except `/tmp`. That shape is useful for a training lab because a single `touch /etc/test` should fail, while a `touch /tmp/test` should still succeed. In real workloads, you would tighten the file rules further after observing what the process actually reads.

```bash
# Create profile on each node
sudo tee /etc/apparmor.d/k8s-deny-write << 'EOF'
#include <tunables/global>

profile k8s-deny-write flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Allow most read operations
  file,

  # Deny all write operations except /tmp
  deny /** w,
  /tmp/** rw,

  # Allow network
  network,
}
EOF
```

Loading the profile is a node operation. The parser validates the profile syntax and registers the profile with the kernel. The `-r` flag replaces an existing loaded version with the file you provide, which is convenient during iterative development. The remove command is equally important in a lab because stale profiles can make later tests confusing if a pod keeps referencing an old name.

```bash
# Parse and load the profile
sudo apparmor_parser -r /etc/apparmor.d/k8s-deny-write

# Verify it's loaded
sudo aa-status | grep k8s-deny-write

# To remove a profile
sudo apparmor_parser -R /etc/apparmor.d/k8s-deny-write
```

Before running this, what output do you expect from `sudo aa-status | grep k8s-deny-write` after a successful load, and what would you check if it prints nothing? The useful debugging split is syntax versus registration. A syntax error should appear when `apparmor_parser` runs, while a missing profile after a clean parser run usually points to the wrong node, the wrong file path, or AppArmor not being enabled on that host.

Most profile mistakes come from granting and denying at the wrong level of detail. Denying `/** w,` is powerful, but it can break package caches, PID files, generated configuration, runtime sockets, or application log paths. Allowing `file,` is convenient, but it may be broader than a final production profile should be. The point of the first draft is not perfection; it is a measurable policy you can exercise, observe, and refine.

---

## Applying Profiles in Kubernetes 1.35+

Kubernetes 1.35+ should use `securityContext.appArmorProfile` rather than the older AppArmor annotation. The API accepts three profile types: `RuntimeDefault`, `Localhost`, and `Unconfined`. `RuntimeDefault` asks the runtime to apply its default profile, `Localhost` names a profile already loaded on the node, and `Unconfined` deliberately removes AppArmor confinement. For CKS practice, `Localhost` is the profile type that tests whether you understand both the node step and the pod step.

The modern equivalent of the original `secured-pod` example applies the `k8s-deny-write` profile at the container level. Container-level configuration is explicit and avoids ambiguity in multi-container pods, where one sidecar may need a different policy from the main application. A pod-level `securityContext.appArmorProfile` can set a default for every container, but the container-level value takes precedence when both are present.

Init containers, sidecars, and ephemeral debug containers deserve the same attention as the primary application container. A pod-level profile can provide a default, but a container that needs different behavior should state its own profile directly. This matters during debugging because an ephemeral container that runs with a broader profile than the failed application may hide the denial you are trying to investigate. Compare the profile labels for the process you are actually testing.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secured-pod
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      appArmorProfile:
        type: Localhost
        localhostProfile: k8s-deny-write
```

The older annotation form is preserved here because many old notes, old exam writeups, and older clusters still show it. In Kubernetes documentation, that form is described as the pre-v1.30 API. In a current cluster, prefer the structured field above; keep the annotation shape in your memory only so you can recognize legacy manifests and migrate them without misreading the profile reference.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secured-pod
  annotations:
    # Legacy format used before Kubernetes v1.30:
    # container.apparmor.security.beta.kubernetes.io/<container-name>: <profile>
    container.apparmor.security.beta.kubernetes.io/app: localhost/k8s-deny-write
spec:
  containers:
  - name: app
    image: nginx
```

The profile reference values changed shape when Kubernetes moved AppArmor into `securityContext`. The old annotation encoded both the source and the name in a single string such as `localhost/k8s-deny-write`. The modern API separates the source into `type: Localhost` and the name into `localhostProfile: k8s-deny-write`. That separation is easier for admission policy and tooling to reason about, and it makes invalid combinations more obvious.

```yaml
# Kubernetes 1.35+ structured field:
securityContext:
  appArmorProfile:
    type: RuntimeDefault

securityContext:
  appArmorProfile:
    type: Localhost
    localhostProfile: k8s-deny-write

securityContext:
  appArmorProfile:
    type: Unconfined

# Legacy annotation format:
container.apparmor.security.beta.kubernetes.io/<container-name>: <profile-ref>

# Legacy profile reference options:
# runtime/default    - Use container runtime's default profile
# localhost/<name>   - Use profile loaded on node with <name>
# unconfined         - No AppArmor restrictions
```

What would happen if you create an AppArmor profile and load it on `node-1`, but not on `node-2`, then let a pod with no `nodeSelector` move during a drain? The scheduler does not understand which AppArmor profiles are loaded on which nodes. Kubelet on the selected node performs the final check, so the pod can work on one node and be rejected on another because the named local profile is missing.

That behavior creates an operational rule: custom profiles are cluster rollout artifacts, not one-off files. If every worker node may run the pod, every worker node needs the profile loaded before the manifest is applied. If only a subset of nodes has the profile, label those nodes and constrain the workload there. Without that discipline, a reschedule event can turn a successful security change into an availability incident.

AppArmor also interacts with Pod Security Admission. Under Pod Security **Baseline** (and therefore Restricted), `Unconfined` AppArmor profiles are rejected at admission; `Localhost` profiles missing on the node still fail at the kubelet. That means AppArmor configuration is not just a node concern; admission can block unsafe profile types before scheduling, while node-local profile loading remains your responsibility for `Localhost` references.

Auditing a running container should include the kernel's view, not only the YAML you submitted. The reliable check is to read `/proc/1/attr/current` inside the container. If the output says `k8s-deny-write (enforce)`, the root process is running under that profile. If it says a runtime default profile, an unexpected profile, or `unconfined`, your manifest, node state, or runtime configuration does not match your intent.

```bash
# Verify the active AppArmor label from inside the container
kubectl exec secured-pod -- cat /proc/1/attr/current

# Check pod events for profile load or admission problems
kubectl describe pod secured-pod | grep -i apparmor

# Confirm the profile exists on a specific node
ssh node1 'sudo aa-status | grep k8s-deny-write'
```

The most common decision in Kubernetes is whether to use `RuntimeDefault` or a custom `Localhost` profile. Use `RuntimeDefault` when you need a broad baseline quickly and the workload has not been profiled yet. Use `Localhost` when the application behavior is well enough understood that a custom policy can remove meaningful access. Avoid `Unconfined` except as a temporary diagnostic control, and remove it as soon as the comparison is complete.

---

## Node Rollout and Drift Control

Custom AppArmor profiles introduce a lifecycle problem that ordinary Kubernetes objects do not have. A Deployment, ConfigMap, or Secret is stored in the API server and reconciled by controllers. A `Localhost` AppArmor profile is a file and kernel registration on each node. Kubernetes can reference the name, but it does not distribute the file, reload the parser, or prove that every eligible node has the same profile content. That makes drift control part of the security design.

There are four common ways to distribute profiles. You can bake them into a node image, install them with configuration management, load them with a privileged DaemonSet, or create them manually in a short-lived exam environment. Baking into the image is predictable for managed fleets because replacement nodes start with the profile already present. Configuration management is flexible for long-lived hosts. A DaemonSet is attractive in Kubernetes-first teams, but it must be privileged enough to write host files and run the parser, which means it deserves careful review.

Manual profile loading is acceptable in a CKS lab because the environment is small and the task is time-boxed. It is a poor production pattern because a new node, node repair, or autoscaler event can silently remove the assumption that made the manifest work. The distinction is not about whether the commands are correct. It is about whether the organization has a mechanism that will make the correct state true again after the node changes.

The first drift category is a missing profile. The file may not exist, the parser may never have run, or the profile may have been removed after cleanup. The second category is stale content, where the name exists but its rules differ from the version the workload was tested against. The third category is mode drift, where one node has the profile in complain mode while another enforces it. The fourth category is node capability drift, where AppArmor itself is disabled or unsupported.

You can check those categories with simple host commands before debugging the workload. The checksum proves whether the file content is the expected version. `aa-status` proves whether the profile is registered and whether it is in enforce or complain mode. The kernel module check proves whether the host can enforce AppArmor at all. None of those checks depend on the pod manifest, which is why they are useful when kubelet rejects a container before it fully starts.

```bash
PROFILE=/etc/apparmor.d/k8s-deny-write

# Check whether the node can enforce AppArmor
cat /sys/module/apparmor/parameters/enabled

# Check the local profile file content
sudo sha256sum "$PROFILE"

# Check whether the profile is loaded and which mode it uses
sudo aa-status | grep k8s-deny-write
```

Node labels are a practical bridge between node-local profile state and Kubernetes scheduling. If only a subset of nodes has a profile, label those nodes and use a `nodeSelector` or node affinity on the workload. The label does not load the profile, and it does not prove the profile content is correct. It simply prevents the scheduler from sending the pod to nodes that you have not declared eligible for that profile.

```bash
kubectl label node node-1 apparmor.kubedojo.io/k8s-deny-write=true
kubectl label node node-2 apparmor.kubedojo.io/k8s-deny-write=true
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secured-pod
spec:
  nodeSelector:
    apparmor.kubedojo.io/k8s-deny-write: "true"
  containers:
  - name: app
    image: nginx
    securityContext:
      appArmorProfile:
        type: Localhost
        localhostProfile: k8s-deny-write
```

The scheduling label should be treated as an assertion that must be maintained, not as a decorative tag. If a node loses the profile during an upgrade but keeps the label, the workload can still land there and fail. If a node has the profile but lacks the label, the workload may have less capacity than expected. In production, the same automation that loads the profile should set or verify the scheduling label after the profile is successfully registered.

Versioning profile names can make changes safer. Instead of editing `k8s-web` in place while pods are still running, create `k8s-web-v2`, load it everywhere, update one test workload to reference the new name, and observe the result. After the rollout succeeds, move the remaining pods and retire the old profile. This costs a little more bookkeeping, but it avoids a hard-to-debug state where the same profile name means different policy on different nodes during rollout.

Mode changes deserve the same care as rule changes. A profile in complain mode may appear to "work" because the application continues to run, yet the logs show operations that would fail in enforce mode. A profile in enforce mode may be too strict but expose the issue quickly. When you move from complain to enforce, write down the workload behavior you exercised. Startup-only testing is not enough if the process writes files during rotation, reloads configuration on a signal, or opens network sockets only during a scheduled job.

```bash
# Put a profile into complain mode while observing normal behavior
sudo aa-complain /etc/apparmor.d/k8s-deny-write

# Switch the same profile back to enforce mode after review
sudo aa-enforce /etc/apparmor.d/k8s-deny-write
```

Multi-container pods add another rollout wrinkle. A pod-level AppArmor profile is convenient when every container can share the same restriction, but sidecars often behave differently from main containers. A proxy sidecar may need network access that a file-processing main container does not. An init container may write files that the application later reads. If you apply one profile at the pod level, test every container path, not just the primary process.

For audits, record evidence in a way that distinguishes desired policy from observed state. Desired policy is the manifest field, the profile source file, and the release record. Observed state is the node checksum, the loaded profile mode, the pod event history, and `/proc/1/attr/current` from the container. A security reviewer should be able to trace from "we intended `k8s-deny-network`" to "this process is currently labeled with `k8s-deny-network (enforce)`" without trusting memory or screenshots.

Before you change a profile, ask which workloads currently reference it. Kubernetes does not maintain a first-class index of profile names, so you usually search manifests, Helm values, GitOps repositories, and live pods. The live check can catch emergency edits that never made it back to source control. The source check can catch workloads that are scaled to zero today but will use the profile later. Both views matter when you remove or rename a profile.

```bash
# Search live pod specs for AppArmor profile references
kubectl get pods --all-namespaces -o yaml | grep -i apparmor -C 3

# Search local manifests in a repository
rg -n "appArmorProfile|container.apparmor.security.beta.kubernetes.io" .
```

The exam version of this workflow is smaller but follows the same logic. Load the profile on the node you will use, verify it with `aa-status`, make the pod land where the profile exists, and prove enforcement from inside the container. If a task provides a specific node name, do the node work there. If it does not, either load the profile on every worker or deliberately constrain the pod after labeling the prepared node.

For long-lived clusters, include AppArmor in node replacement planning. Autoscaled nodes, repaired virtual machines, and rebuilt bare-metal hosts can all join the cluster without the local profiles that older workloads assume. A good readiness check for a hardened node pool should include kernel support, expected profile checksums, enforce-mode status, and the scheduling labels that advertise those profiles. That check turns AppArmor from a manual security tweak into a condition of node eligibility.

This rollout thinking prevents a misleading success condition. A pod that starts once is not proof that the cluster is ready for AppArmor. A stronger success condition says that every eligible node can enforce the named profile, the workload is constrained to those nodes when necessary, the running container has the intended label, and denial logs match the policy you wanted to test. That is the difference between a working demo and a maintainable security control.

---

## Operational Rollout and Debugging

The safest rollout pattern is observe, constrain, verify, and then widen the deployment. Start with a profile in complain mode or in a narrow test environment, exercise the workload, inspect the logs, and adjust the rules. Then switch to enforce mode and repeat the same workload. After enforcement works on one node, distribute the profile to every node that may run the pod, and only then apply or update the workload manifest.

The following preserved profiles show three useful policy families. The first blocks writes to the root filesystem except for temporary runtime locations. The second blocks network access for workloads that should never call out. The third denies reads of sensitive account and privilege files. These are lab patterns, not universal production profiles, but they teach the shape of a rule you can refine for a specific process.

```text
#include <tunables/global>

profile k8s-readonly flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Read everything
  /** r,

  # Write only to specific paths
  /tmp/** rw,
  /var/tmp/** rw,
  /run/** rw,

  # Deny write elsewhere
  deny /** w,

  network,
}
```

The read-only-root pattern is useful when the container image should be immutable during runtime but the process still needs scratch space. It pairs well with `readOnlyRootFilesystem: true`, yet it is not identical. The Kubernetes setting changes the mount behavior of the container root filesystem, while AppArmor can mediate additional file paths and make the denial visible in the kernel audit trail.

```text
#include <tunables/global>

profile k8s-deny-network flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  file,

  # Deny all network access
  deny network,
}
```

The deny-network pattern is intentionally blunt. It is excellent for a batch job that only transforms local input, or for a sidecar that should communicate through shared files rather than sockets. It is a poor fit for a web server, DNS client, package installer, or telemetry exporter. When you see `deny network,`, immediately ask whether startup scripts, health checks, or library code create sockets before the main application starts.

```text
#include <tunables/global>

profile k8s-deny-sensitive flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  file,
  network,

  # Deny access to sensitive files
  deny /etc/shadow r,
  deny /etc/gshadow r,
  deny /etc/sudoers r,
  deny /etc/sudoers.d/** r,
  deny /root/** rwx,
}
```

The sensitive-file pattern is a good teaching example because it blocks behavior that almost no application container should need. Be careful, though, not to generalize it into "deny all of `/etc`." Many applications read CA bundles, resolver configuration, service account mounts, or application configuration beneath paths that look sensitive at first glance. A senior profile review asks whether each denied path is harmful and whether each allowed path is necessary.

Pause and predict: you apply an AppArmor profile that has `deny /etc/** w,` to a container running nginx, and that image writes generated configuration beneath `/etc/nginx/conf.d/` during startup. The pod may schedule, the container may begin to start, and then the process can crash when the write is denied. Your next check should be the kernel log, not another blind edit to the manifest.

The original CKS-style scenario for applying an existing profile used the legacy annotation. In a current cluster, translate the intent to `appArmorProfile`; in an older exam environment, recognize why the annotation key must include the container name exactly. The protected example remains below as a compatibility reference because it captures the old pitfall: the annotation names a container, not an image.

```bash
# Check if profile is loaded
sudo aa-status | grep my-profile

# Legacy annotation example for older clusters
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  annotations:
    container.apparmor.security.beta.kubernetes.io/nginx: localhost/my-profile
spec:
  containers:
  - name: nginx
    image: nginx
EOF
```

The second preserved scenario creates and applies a profile that denies writes beneath `/etc`. The operational lesson is still current even if the manifest surface has changed: write the profile, load it, apply it to a container, and verify with an operation that should fail. In Kubernetes 1.35+, you would replace the annotation block with the structured field shown earlier, but the profile authoring and denial test remain the same.

```bash
# Create profile that denies write to /etc
sudo tee /etc/apparmor.d/k8s-deny-etc-write << 'EOF'
#include <tunables/global>

profile k8s-deny-etc-write flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  file,
  network,
  deny /etc/** w,
}
EOF

# Load profile
sudo apparmor_parser -r /etc/apparmor.d/k8s-deny-etc-write

# Kubernetes 1.35+ — apply with securityContext.appArmorProfile
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secured-nginx
spec:
  containers:
  - name: nginx
    image: nginx
    securityContext:
      appArmorProfile:
        type: Localhost
        localhostProfile: k8s-deny-etc-write
EOF

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/secured-nginx --timeout=60s

# Verify
kubectl exec secured-nginx -- touch /etc/test
# Should fail due to AppArmor
```

Legacy recognition only (deprecated since v1.30; emits a warning on v1.35 — do not use in new manifests):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secured-nginx
  annotations:
    container.apparmor.security.beta.kubernetes.io/nginx: localhost/k8s-deny-etc-write
spec:
  containers:
  - name: nginx
    image: nginx
```

Debugging AppArmor issues is a layered process. Pod events tell you whether Kubernetes or kubelet rejected the profile reference. Node commands tell you whether the profile exists and whether AppArmor is enabled. Kernel logs tell you which exact operation, profile, process, path, and requested mask caused a denial. You need all three layers because any one layer by itself can point you in the wrong direction.

```bash
# Check pod events
kubectl describe pod secured-pod | grep -i apparmor

# Check if profile is loaded on node
ssh node1 'sudo aa-status | grep k8s'

# Check audit logs for denials
sudo dmesg | grep -i apparmor | tail -10

# Or check audit log
sudo journalctl -k | grep -i apparmor
```

When the denial appears in `dmesg` or `journalctl`, read it as evidence rather than noise. The profile name tells you which policy was active. The operation describes what the process attempted, such as file read, file write, execute, mmap, or network. The requested and denied masks show which permission was blocked. The path gives you the next rule to review, but it does not automatically prove the application should be allowed to use that path.

A common troubleshooting trap is to loosen the profile until the symptom disappears, then stop. That approach makes the profile a slow way to rediscover `unconfined`. Instead, record the denied operation, map it to application behavior, and decide whether the operation is part of the expected contract. If it is expected, add the narrowest allow rule that supports it. If it is unexpected, keep the denial and fix the application, startup script, or image.

Exercise scenario: a pod runs successfully for several days, then fails after a node upgrade even though the manifest has not changed. AppArmor should be on your shortlist if the container reports permission errors at startup, the active profile differs across nodes, or `aa-status` shows a profile missing on the upgraded node. The manifest did not change, but the node-local security asset did, and the node is where AppArmor actually lives.

---

## Patterns & Anti-Patterns

The strongest AppArmor pattern is to treat profiles as versioned node configuration. Keep the profile text in source control, roll it out through a controlled node-management path, and make the workload reference a profile name that exists everywhere the workload can schedule. This works because it turns a local kernel dependency into an auditable release artifact. At scale, combine that with node labels only when a profile is intentionally limited to a smaller pool.

The second pattern is to start with `RuntimeDefault` and reserve custom `Localhost` profiles for workloads where the extra restriction is specific and testable. A blanket custom profile for every service sounds disciplined, but it often produces shallow copies that nobody understands. Runtime defaults give broad baseline coverage immediately, while custom profiles deliver value when they encode real differences between a web server, a batch worker, and a file-processing job.

The third pattern is to verify enforcement from inside the container and from the node. The container-side `/proc/1/attr/current` check proves what label the process actually carries. The node-side `aa-status` or `/sys/kernel/security/apparmor/profiles` check proves the host knows the profile. The pod manifest only proves intent. Security work needs the intent, the host state, and the runtime result to agree.

The most tempting anti-pattern is setting `Unconfined` to make a failing pod start, then leaving it there because the incident is over. That trades a visible outage for an invisible security regression. If you must use `Unconfined` during diagnosis, treat it like a temporary feature flag with an owner, a removal step, and a replacement profile. The better alternative is a complain-mode profile in a test path or a narrow allow rule based on a logged denial.

Another anti-pattern is assuming that a DaemonSet pod running on every node means the profile is loaded on every node. The DaemonSet proves a container was scheduled; it does not prove the parser command succeeded, AppArmor was enabled, or the profile name reached the kernel. A good rollout checks the command exit code, captures logs, and verifies `aa-status` on the host. That verification is the difference between distributing a file and enforcing a policy.

A subtler anti-pattern is copying a deny-focused profile from one image to another. Deny rules are only meaningful inside a complete allow model. A path that is suspicious for one workload may be normal for another, and a broad `file,` allow may hide the fact that the deny list is incomplete. Use copied profiles as starting templates, not as proof. The proof is a workload-specific test that exercises startup, steady-state behavior, health checks, and shutdown.

| Pattern or Anti-Pattern | Use It When | Why It Works or Fails | Scaling Consideration |
|---|---|---|---|
| Version profiles with node configuration | Custom `Localhost` profiles protect production workloads | The node-local profile becomes reviewable and repeatable | Pair with rollout verification on every schedulable node |
| Use `RuntimeDefault` as the baseline | Workloads have not been profiled yet | It gives immediate generic confinement with low breakage risk | Make it the default policy, then tighten high-risk workloads |
| Verify from `/proc` and `aa-status` | You need proof that enforcement is active | It checks runtime label and node profile state, not just YAML | Automate these checks in smoke tests or security audits |
| Leave `Unconfined` after debugging | A profile blocks startup and pressure is high | It removes the security control while making the symptom disappear | Require removal tracking and an explicit replacement profile |
| Trust DaemonSet presence alone | Profiles are distributed by a privileged helper | The helper may run even when parsing or loading failed | Verify parser exit codes and host-visible profile state |
| Copy profiles without workload tests | Teams want fast standardization | The policy may encode the wrong application's behavior | Template only the structure; test the specific workload path |

Patterns and anti-patterns are useful only when they produce a decision you can act on. For AppArmor, the decision is usually about rollout confidence: do you have a profile that matches the workload, do all eligible nodes have it, and can you prove the running process uses it? If one of those answers is missing, the next action is not another policy slogan. It is a concrete check against the node, the pod, or the logs.

---

## Decision Framework

Use this framework when you need to choose between the runtime default profile, a custom local profile, and a temporary unconfined comparison. Start with the risk of the workload, then ask what behavior you can describe and verify. A high-risk workload with well-known behavior deserves a custom profile. A low-risk workload with unknown behavior should begin with the runtime default and move to a custom profile after observation. An unconfined run is a diagnostic control, not a destination.

```text
+-----------------------------------------------------------+
|            APPARMOR PROFILE DECISION FLOW                 |
+-----------------------------------------------------------+
|                                                           |
|  Is AppArmor enabled on every eligible node?              |
|       |                                                   |
|       +-- no --> fix node support before using profiles   |
|       |                                                   |
|       +-- yes                                             |
|            |                                              |
|            v                                              |
|  Do you only need a broad baseline today?                 |
|       |                                                   |
|       +-- yes --> use RuntimeDefault                      |
|       |                                                   |
|       +-- no                                              |
|            |                                              |
|            v                                              |
|  Can you describe and test expected file/network use?     |
|       |                                                   |
|       +-- yes --> create Localhost profile                |
|       |                                                   |
|       +-- no --> observe in complain mode or test env     |
|                                                           |
|  Is the profile needed only for debugging?                |
|       |                                                   |
|       +-- yes --> use Unconfined briefly, then remove     |
|       +-- no  --> keep enforce mode and audit regularly   |
|                                                           |
+-----------------------------------------------------------+
```

The profile decision also depends on where failure should happen. If a workload explicitly requests `RuntimeDefault` and AppArmor is disabled on the node, Kubernetes can reject the pod rather than silently running without the profile. If the field is omitted, the runtime default may apply only when the node supports it. That difference matters in regulated environments because "fail closed" and "best effort" are not the same operational contract.

| Choice | Best Fit | Main Tradeoff | Verification Command |
|---|---|---|---|
| `RuntimeDefault` | Fast baseline for most containers | Generic policy, not workload-specific | `kubectl exec <pod> -- cat /proc/1/attr/current` |
| `Localhost` | Known workload with specific restrictions | Requires node-local profile rollout | `sudo aa-status | grep <profile>` |
| `Unconfined` | Short diagnostic comparison | Removes AppArmor protection | `kubectl exec <pod> -- cat /proc/1/attr/current` |
| Complain mode | Profile development before enforcement | Logs may grow noisy during testing | `sudo aa-status` and `journalctl -k` |
| Node label plus selector | Profile exists only on a subset of nodes | Reduces scheduler flexibility | `kubectl get nodes --show-labels` |

Which approach would you choose for a job that reads a ConfigMap, writes one output file to an emptyDir volume, and never needs the network? A reasonable path is a custom `Localhost` profile that allows the expected file paths and denies network, but only after you confirm the image does not use DNS, package downloads, or telemetry during startup. If you cannot yet confirm that behavior, begin in a test namespace with complain mode rather than shipping a guessed enforce profile.

The decision framework should also influence how you write the lab evidence. "Applied profile" is weaker than "applied profile, verified active label, attempted denied operation, and found matching kernel denial." The stronger statement contains the desired result and the proof path. In exam work, that proof path helps you avoid losing time when a manifest looks correct but kubelet rejected the container because the profile was absent on the node.

---

## Did You Know?

- AppArmor support for Kubernetes profiles is stable as of Kubernetes v1.31, and Kubernetes 1.35+ uses the structured `appArmorProfile` field rather than the older beta annotation.
- The AppArmor profile must be loaded into the node kernel before kubelet can run a container with `type: Localhost`; the Kubernetes API does not store the profile text for you.
- Container-level `appArmorProfile` configuration takes precedence over pod-level configuration, which matters when a main container and sidecar need different confinement.
- Tools such as `aa-genprof` and `aa-logprof` can help generate or refine profiles from observed application behavior, but the result still needs human review before enforcement.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Loading the profile on only one node | The first test pod works, so the node-local dependency is forgotten | Load and verify the profile on every eligible node or constrain scheduling with labels |
| Using legacy annotations in a Kubernetes 1.35+ manifest | Older examples still show the pre-v1.30 API shape | Use `securityContext.appArmorProfile` and keep annotations only for migration recognition |
| Matching the profile to the image name instead of the container name | Legacy annotation examples embed a name in the key, which invites confusion | For old manifests, match the container name exactly; for current manifests, set the container security context directly |
| Skipping complain-mode or test-environment observation | A deny rule looks obvious during review but blocks startup behavior | Exercise startup, health checks, steady-state work, and shutdown before switching to enforce mode |
| Assuming DaemonSet rollout equals kernel registration | The distribution helper can run even if `apparmor_parser` failed | Check parser exit codes and confirm with `aa-status` or `/sys/kernel/security/apparmor/profiles` |
| Treating `Unconfined` as a permanent fix | It makes an outage disappear quickly under pressure | Use it only for short diagnosis, then replace it with `RuntimeDefault` or a tested custom profile |
| Auditing only the manifest | YAML shows requested configuration, not the label applied to the process | Verify from inside the container with `/proc/1/attr/current` and from the node with AppArmor tooling |

---

## Quiz

<details>
<summary>1. Your team designed a `k8s-deny-write` profile, loaded it on one worker node, and applied a pod with `type: Localhost`. The pod runs during the first test but fails after a drain moves it to another node. What should you check first, and why?</summary>

Check whether the profile is loaded on the new node with `sudo aa-status | grep k8s-deny-write` or by reading `/sys/kernel/security/apparmor/profiles`. A `Localhost` profile is a node-local kernel asset, not an object stored in the Kubernetes API. The scheduler does not select nodes based on loaded AppArmor profiles unless you add your own labels and constraints. If the profile is missing, load it on every eligible node or restrict the pod to nodes where the profile is intentionally present.

</details>

<details>
<summary>2. A pod manifest for Kubernetes 1.35 uses `container.apparmor.security.beta.kubernetes.io/app: localhost/k8s-deny-network`. The profile works on an older cluster but your reviewer asks for the current API. How do you rewrite the manifest?</summary>

Move the profile reference into the container's `securityContext.appArmorProfile` field. Use `type: Localhost` and `localhostProfile: k8s-deny-network` on the container named `app`. The old annotation was the pre-v1.30 way to express the same intent, but current Kubernetes documentation directs users to the structured field. This rewrite also makes the configuration easier for admission policy and schema-aware tooling to validate.

</details>

<details>
<summary>3. A container starts under a new profile and immediately exits with a normal application error about being unable to write a generated file. Unix permissions look fine. What evidence would confirm AppArmor as the cause?</summary>

Look for an AppArmor denial in `sudo dmesg | grep -i apparmor` or `sudo journalctl -k | grep -i apparmor`. The log entry should name the active profile, operation, path, and denied mask. Also verify the running label with `kubectl exec <pod> -- cat /proc/1/attr/current` if the container stays up long enough. If the denial path matches the generated file, decide whether to allow that exact path or change the application behavior.

</details>

<details>
<summary>4. You are asked to improve confinement across many existing workloads this week, but you do not yet have workload-specific behavior profiles. Which AppArmor option gives immediate value with the lowest breakage risk?</summary>

Use `RuntimeDefault` as the immediate baseline. It applies the container runtime's default AppArmor profile, which usually blocks common dangerous operations while allowing ordinary container behavior. Custom `Localhost` profiles can provide stronger workload-specific restriction later, after observation and testing. Do not use `Unconfined` as a broad baseline because it deliberately removes AppArmor enforcement.

</details>

<details>
<summary>5. A DaemonSet that distributes profiles is running on every worker, but one node still rejects pods that request `k8s-deny-sensitive`. What does that tell you about the rollout?</summary>

It tells you that DaemonSet scheduling is not the same thing as successful profile registration. The helper container may have started while its parser command failed, AppArmor may be disabled on that node, or the profile file may have a syntax problem. Check the DaemonSet pod logs and the `apparmor_parser` exit status, then verify the profile from the host with `aa-status`. The fix is to make profile loading observable, not merely to restart the DaemonSet.

</details>

<details>
<summary>6. A security review finds `type: Unconfined` on a production pod that previously had startup failures under a custom profile. What is the safer remediation path?</summary>

First confirm whether `Unconfined` was added as a temporary diagnostic step or as an undocumented permanent workaround. Replace it with `RuntimeDefault` if you need immediate baseline confinement and no custom profile is ready. Then reproduce the startup failure in a test environment, inspect AppArmor logs, and add narrow allow rules only for behavior the application legitimately needs. The goal is to remove the unconfined state without guessing at a broad custom profile.

</details>

<details>
<summary>7. You need to audit whether a pod is actually running under the intended profile after a manifest update. Why is reading the YAML alone insufficient, and what should you run?</summary>

The YAML shows the requested configuration, but it does not prove kubelet admitted the pod with that profile or that the process carries the expected kernel label. Run `kubectl exec <pod> -- cat /proc/1/attr/current` to inspect the active label inside the container. Also check the node with `sudo aa-status | grep <profile>` when the profile type is `Localhost`. A complete audit compares manifest intent, node profile state, and runtime process state.

</details>

---

## Hands-On Exercise

**Prerequisite:** This lab requires an AppArmor-enabled Linux worker (typical CKS/killercoda Ubuntu). If `cat /sys/module/apparmor/parameters/enabled` does not return `Y`, run the node-side profile steps on a supported host before applying pods.

In this exercise you will create a custom AppArmor profile that denies network access, load it on a node, apply it to a pod with the Kubernetes 1.35+ security context field, and verify both the intended failure and a control case. The original lab command sequence is preserved in spirit, but the manifest uses `appArmorProfile` instead of the legacy annotation. Run the node commands on the worker that will host the pod, or use a single-node lab cluster where the control plane node also runs workloads.

- [ ] Confirm that AppArmor is enabled on the node and that `aa-status` can report loaded profiles.
- [ ] Create and load a `k8s-deny-network` profile with `apparmor_parser`.
- [ ] Launch a pod that uses `type: Localhost` and `localhostProfile: k8s-deny-network`.
- [ ] Verify the active profile through `/proc/1/attr/current` inside the container.
- [ ] Prove that network access fails in the confined pod and succeeds in an unconfined comparison pod.
- [ ] Clean up the pods and remove the profile if this is a temporary lab node.

```bash
# Step 1: Check AppArmor is enabled (run on node)
cat /sys/module/apparmor/parameters/enabled
# Should output: Y

# Step 2: Create the profile
sudo tee /etc/apparmor.d/k8s-deny-network << 'EOF'
#include <tunables/global>

profile k8s-deny-network flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Allow file operations
  file,

  # Deny network access
  deny network,
}
EOF

# Step 3: Load the profile
sudo apparmor_parser -r /etc/apparmor.d/k8s-deny-network

# Step 4: Verify it's loaded
sudo aa-status | grep k8s-deny-network

# Step 5: Create pod with the profile using Kubernetes 1.35+ appArmorProfile
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: no-network-pod
spec:
  containers:
  - name: app
    image: curlimages/curl
    command: ["sleep", "3600"]
    securityContext:
      appArmorProfile:
        type: Localhost
        localhostProfile: k8s-deny-network
EOF

# Step 6: Wait for pod
kubectl wait --for=condition=Ready pod/no-network-pod --timeout=60s

# Step 7: Verify the profile label
kubectl exec no-network-pod -- cat /proc/1/attr/current

# Step 8: Test network is blocked
kubectl exec no-network-pod -- curl -s https://kubernetes.io --connect-timeout 5
# Should fail due to AppArmor denying network

# Step 9: Create pod without restriction for comparison
kubectl run network-allowed --image=curlimages/curl --rm -i --restart=Never -- \
  curl -s https://kubernetes.io -o /dev/null -w "%{http_code}"
# Should succeed (200)

# Cleanup
kubectl delete pod no-network-pod --grace-period=0
sudo apparmor_parser -R /etc/apparmor.d/k8s-deny-network
```

<details>
<summary>Solution notes for tasks 1-3</summary>

The node check should return `Y` from `/sys/module/apparmor/parameters/enabled`, and `sudo aa-status` should report that the AppArmor module is loaded. The profile file belongs under `/etc/apparmor.d/`, and `sudo apparmor_parser -r /etc/apparmor.d/k8s-deny-network` should exit successfully. If `aa-status | grep k8s-deny-network` prints nothing, fix the node state before you debug Kubernetes. A pod cannot use a `Localhost` profile that the selected node has not loaded.

</details>

<details>
<summary>Solution notes for tasks 4-5</summary>

The `/proc/1/attr/current` output should include `k8s-deny-network` and an enforce-mode marker. The curl command inside `no-network-pod` should fail because the profile denies network operations before the process can complete the connection. The comparison pod should return an HTTP status code because it does not use the deny-network profile. If both pods fail, debug DNS or general cluster egress before blaming AppArmor.

</details>

<details>
<summary>Solution notes for task 6</summary>

Deleting the pod removes the workload, but it does not remove the host profile. Use `sudo apparmor_parser -R /etc/apparmor.d/k8s-deny-network` only when the profile was created for this lab and no other pod depends on it. In a shared training cluster, check for references before removal. In a real cluster, profile removal should follow the same release process as profile rollout.

</details>

The success criteria are deliberately evidence-based. You should be able to show that the node has the profile, the container runs with that profile, the denied operation fails, the control operation succeeds outside the profile, and the cleanup step leaves no temporary pod behind. If any one of those claims is unsupported, continue debugging until the observed state and the intended policy match.

---

## Learner check

> AppArmor profiles are node-local kernel assets: Kubernetes 1.35+ references them with `securityContext.appArmorProfile`, but every worker that may run the pod must load the profile before kubelet can enforce `type: Localhost`.

Before you move on, explain why a pod can pass admission yet fail on a drained node, and which three checks prove enforcement (node profile state, pod events, and `/proc/1/attr/current`). A solid answer names Pod Security Admission limits on `Unconfined`, distinguishes missing `Localhost` profiles at the kubelet from admission rejection, and cites at least one kernel denial log path.

---

## Sources

- https://kubernetes.io/docs/tutorials/security/apparmor/
- https://kubernetes.io/docs/tasks/configure-pod-container/security-context/
- https://kubernetes.io/docs/concepts/security/linux-kernel-security-constraints/
- https://kubernetes.io/docs/concepts/security/pod-security-standards/
- https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.35/#apparmorprofile-v1-core
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_exec/
- https://apparmor-documentation-c38b15.gitlab.io/documentation/getting-started/profiles-basics/
- https://apparmor-documentation-c38b15.gitlab.io/documentation/in-depth/profiles/core-policy-reference/
- https://apparmor-documentation-c38b15.gitlab.io/documentation/getting-started/complain-mode/
- https://manpages.ubuntu.com/manpages/noble/en/man8/aa-status.8.html
- https://manpages.ubuntu.com/manpages/noble/en/man8/apparmor_parser.8.html
- https://docs.docker.com/engine/security/apparmor/

## Next Module

[Module 3.2: Seccomp Profiles](../module-3.2-seccomp/) - System call filtering for containers.
