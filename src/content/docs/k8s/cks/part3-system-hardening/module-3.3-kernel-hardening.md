---
title: "Module 3.3: Linux Kernel and OS Hardening"
slug: k8s/cks/part3-system-hardening/module-3.3-kernel-hardening
sidebar:
  order: 3
revision_pending: false
lab:
  id: cks-3.3-kernel-hardening
  url: https://killercoda.com/kubedojo/scenario/cks-3.3-kernel-hardening
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - System administration with security focus
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: Basic Linux administration, container runtime knowledge

---

## What You'll Be Able to Do

This module treats kernel hardening as an operational design problem rather than a list of magic sysctl names. By the end, you should be able to look at a Kubernetes 1.35 worker node, separate settings that Kubernetes requires from settings that merely widen exposure, and justify the exact host controls you would change before a production rollout.

1. **Diagnose** Kubernetes node sysctl settings and explain which values protect the shared kernel without breaking pod networking
2. **Design** a minimal host OS baseline that reduces packages, services, SSH exposure, filesystem risk, and patch lag
3. **Audit** kubelet, certificate, `/proc`, `/sys`, and auditd configuration for evidence of host hardening drift
4. **Evaluate** container runtime isolation choices such as seccomp, user namespaces, read-only filesystems, and privilege escalation controls

---

## Why This Module Matters

Exercise scenario: your cluster passes admission policy checks, every application Pod has a non-root security context, and the network team has shipped namespace NetworkPolicies. During a node review, you discover that the worker image still runs printing, discovery, and remote procedure services, permits password SSH, exposes kernel messages to unprivileged users, and has not applied a kernel security update. The applications looked hardened from the Kubernetes API, yet the node itself still offers attackers a large host-level surface after any container escape.

That tension is the heart of kernel and OS hardening in Kubernetes. A container is not a tiny virtual machine with its own kernel; it is a process tree isolated by Linux namespaces, cgroups, capabilities, LSM hooks, seccomp filters, mount options, and runtime configuration. Those layers are powerful, but they all terminate at the same host kernel, so a bug or misconfiguration below the kubelet can affect every workload scheduled on the node.

The CKS exam does not expect you to become a kernel developer, but it does expect you to recognize which host settings matter for a Kubernetes node. You need to preserve required networking behavior such as IP forwarding, reduce unnecessary local tools and daemons, restrict information leaks from `/proc`, `/sys`, and kernel logs, and connect runtime controls back to the shared-kernel model. The goal is not a node that looks locked down in a generic scanner; the goal is a node that runs Kubernetes correctly while removing avoidable paths from container compromise to host control.

---

## The Shared Kernel Problem

The most important mental model is simple: a Pod is scheduled through Kubernetes, but its containers ultimately become Linux processes on a node. The container runtime asks the kernel for namespaces, cgroups, mounts, capabilities, and seccomp behavior, then the kernel enforces those boundaries. If the kernel or host OS exposes too much information, runs vulnerable services, or leaves dangerous permissions in place, Kubernetes cannot fully compensate from above.

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER KERNEL SHARING                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Container A │  │ Container B │  │ Container C │        │
│  │  (nginx)    │  │  (redis)    │  │ (attacker?) │        │
│  └─────┬───────┘  └─────┬───────┘  └─────┬───────┘        │
│        │                │                │                 │
│        └────────────────┼────────────────┘                 │
│                         │                                  │
│                         ▼                                  │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                    HOST KERNEL                        │ │
│  │                                                       │ │
│  │  All containers use the SAME kernel                  │ │
│  │  Kernel exploit = compromise ALL containers          │ │
│  │  Privilege escalation = host access                  │ │
│  │                                                       │ │
│  └──────────────────────────────────────────────────────┘ │
│                         │                                  │
│                         ▼                                  │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                    HARDWARE                           │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

This diagram is the reason host hardening belongs in a Kubernetes security curriculum. Containers A and B may be ordinary services, while Container C may be a compromised workload that has gained code execution. If Container C can learn kernel addresses, read host process details, load a kernel attack chain, or abuse an unnecessary node daemon, the blast radius is no longer limited to that Pod.

Virtual machines draw the boundary differently. A VM normally brings its own guest kernel, so a guest kernel flaw does not automatically become a host kernel flaw, although hypervisor escapes remain possible. Containers trade that stronger kernel boundary for speed, density, and operational simplicity, which means you must strengthen the shared kernel and the host OS around it.

Kernel hardening also has a directionality problem. Kubernetes objects such as PodSecurity admission, `securityContext`, and NetworkPolicy are visible through the API server, so teams often review them first. Host controls are distributed across system packages, services, sysctl files, kubelet paths, runtime configuration, mount options, and audit rules, so drift can hide until a node image is rebuilt or an incident forces inspection.

Pause and predict: if an attacker escapes one unprivileged container and lands as a low-privilege user on the node, which host information would help them choose the next exploit path? Think about kernel version, loaded modules, process lists, kubelet credentials, writable filesystems, local compilers, and network daemons before you look at the commands later in the module.

The practical hardening sequence follows the same path an attacker would use. First, reduce what is installed and running so there are fewer local tools and vulnerable services. Next, tune kernel parameters so common reconnaissance and network tricks fail. Then protect sensitive host files and pseudo-filesystems, harden runtime isolation, and leave enough audit evidence to prove the node stayed in that condition.

One subtle point matters for exam questions and real operations: not every generic Linux hardening rule belongs unchanged on a Kubernetes node. A normal server might disable IP forwarding, but a worker node usually needs forwarding for Pod and Service traffic. Senior judgment is knowing when a setting is truly dangerous, when it is required for the platform, and which compensating controls make the required exception acceptable.

The shared-kernel model also explains why container boundaries are made from several smaller controls instead of one large switch. Namespaces limit what a process can see, cgroups limit what it can consume, capabilities divide root-like power into narrower privileges, seccomp filters block selected syscalls, and Linux Security Modules add policy decisions around files and operations. Weakness in one layer does not always mean immediate host control, but it gives attackers more room to combine mistakes.

Node pool design is another part of kernel hardening because the scheduler decides which workloads share the same kernel. If high-risk workloads, privileged system agents, and ordinary application Pods all run on the same pool, a host flaw has a broader operational consequence. Taints, tolerations, node labels, RuntimeClasses, and admission policy let you separate workloads that need extra privilege from workloads that should remain on a tighter baseline.

Threat modeling keeps the module practical. You are not trying to stop an attacker who already has unrestricted root on the physical host and full access to your cloud control plane. You are reducing the steps between application compromise and node compromise, limiting useful reconnaissance, and making node drift visible before it turns into an easy post-escape path across the cluster.

---

## Design a Minimal, Patchable Host OS Baseline

Host hardening starts before kubelet ever runs. A worker node should look more like a sealed appliance than a general-purpose login server, because every installed package becomes maintenance load and every active daemon becomes a possible entry point. Minimal images such as Talos, Flatcar, Bottlerocket, and other container-optimized operating systems embody this idea by removing interactive administration paths and focusing on the components needed to run containers.

Minimal does not mean mysterious. A Kubernetes node still needs a container runtime, kubelet, CNI support, time synchronization, logging or monitoring agents, and whatever host management channel your organization approves. What it should not need is desktop software, printing, Bluetooth, language toolchains, office packages, unplanned shells for every user, or network discovery services that have no role in scheduling Pods.

The first audit pass is intentionally boring: count installed packages, identify obvious non-node software, and confirm the image owner can explain every category that remains. Package counts are not a security score by themselves, because distributions package components differently, but a sudden jump in packages across one node pool is a useful drift signal. Treat the count as a smoke alarm, not as the final diagnosis.

```bash
# List installed packages
dpkg -l | wc -l  # Debian/Ubuntu
rpm -qa | wc -l  # RHEL/CentOS

# Remove unnecessary packages
sudo apt remove -y --purge $(dpkg -l | grep -E 'games|office' | awk '{print $2}')

# Kubernetes nodes should have minimal software:
# - Container runtime (containerd, CRI-O)
# - kubelet
# - kube-proxy (if not running as pod)
# - Networking tools
# - Monitoring agents
```

Be careful with package removal on a live node. The safe production pattern is to fix the node image, roll a replacement pool, cordon and drain old nodes, and let the scheduler move workloads. Emergency cleanup on an existing node can be appropriate during a lab or a contained incident, but rebuilding from a known image gives you a repeatable control that will survive reboot, autoscaling, and node repair.

Running services deserve the same treatment as packages, but with a stronger operational dependency check. `cups`, `avahi-daemon`, `bluetooth`, and similar services are easy examples because a Kubernetes worker has no reason to advertise printers, participate in local discovery, or expose wireless interfaces. Other services may be vendor agents, node problem detectors, storage plugins, or network components, so confirm ownership before stopping anything on production infrastructure.

```bash
# List running services
systemctl list-units --type=service --state=running

# Disable unnecessary services
sudo systemctl disable --now cups      # Printing
sudo systemctl disable --now avahi-daemon  # mDNS
sudo systemctl disable --now bluetooth  # Bluetooth

# Essential services to keep:
# - containerd or docker
# - kubelet
# - SSH (for management)
# - NTP/chrony (time sync)
```

The safest disabling order is reversible and measured. Capture the current service list, stop one candidate service, verify kubelet and the runtime remain healthy, run a simple Pod scheduling test, and only then disable the service persistently. If your organization uses immutable nodes, encode the change in image build configuration instead of treating `systemctl disable` as the long-term fix.

Patch management is the second half of the baseline. Kernel and OS hardening is not only about secure defaults; it is also about closing known vulnerabilities before they become routine exploitation paths. A node pool that cannot be patched because it is too fragile is not hardened, even if its current sysctl file looks tidy.

```bash
# Check for security updates (Ubuntu)
sudo apt update
sudo apt list --upgradable | grep -i security

# Apply security updates only
sudo unattended-upgrades

# Check kernel version
uname -r

# Check for known kernel CVEs
# https://www.kernel.org/
```

Automatic updates require a policy, not just a package. On pets-style servers, unattended upgrades may be configured to patch in place and reboot during maintenance windows. On container-optimized or autoscaled worker pools, a safer pattern is often image rebuild, node replacement, and Pod disruption budget-aware draining, because it avoids accumulating one-off state on long-lived machines.

SSH hardening belongs in the same baseline because emergency shell access is powerful and often forgotten. If SSH exists, root login should be disabled, password authentication should be disabled, allowed users should be narrow, and access should be logged. If the platform supports a no-SSH model, prefer a controlled break-glass workflow and Kubernetes-native debugging for routine application investigation.

```text
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no
AllowUsers admin
```

```bash
# Restart SSH
sudo systemctl restart sshd
```

User cleanup is less glamorous than a new runtime feature, but it often reveals drift. Old local accounts, shared emergency users, and inactive admin accounts create paths around your identity provider and audit model. Locking an account before deleting it gives you a safer rollback during an investigation, while image-level removal prevents the same account from reappearing on the next node replacement.

```bash
# List users that can login
grep -v '/nologin\|/false' /etc/passwd

# Lock unnecessary accounts
sudo usermod -L olduser

# Remove user
sudo userdel -r unnecessaryuser
```

Before running removal commands in a real environment, ask what workflow would break if the node could no longer accept an interactive login. The answer should point to deliberate replacements: `kubectl debug` for workload troubleshooting, serial console or cloud session manager for break-glass access, node image pipelines for permanent changes, and centralized logs for evidence. If no one can answer, the team is relying on informal access rather than hardened operations.

Image provenance belongs in the baseline because a minimal image built from unclear inputs is still a weak foundation. The node image should have a known source, repeatable build steps, recorded package versions, and a patch history that security reviewers can inspect. This does not require a heavy process for every lab cluster, but production worker pools should not depend on a one-time manually customized machine that nobody can recreate.

Package managers create another operational choice. Some container-optimized systems avoid a traditional package manager on the node, which reduces the chance that an operator installs tools during troubleshooting and forgets to remove them. General-purpose distributions can still be hardened, but the team needs controls around package installation, repository trust, and post-install drift detection so a node does not gradually become a utility server.

Reboots are part of patching, not an embarrassing exception to uptime. Kernel fixes often require reboot or node replacement before the running kernel changes, so the cluster must tolerate planned rotation. Pod disruption budgets, multiple replicas, surge capacity, topology spread, and drain automation are not separate from kernel hardening; they are the mechanisms that let you apply hardening without creating a service outage.

Rollback planning is just as important as rollout planning. If a kernel update breaks a storage driver, CNI module, or monitoring agent, operators need a tested way to stop the rollout and return to the previous image. That rollback should preserve the security investigation trail, because reverting blindly can hide whether the issue was a bad package, an incompatible driver, or an undocumented dependency in the node pool.

---

## Tune Sysctl Settings for the Shared Kernel

Sysctl settings are runtime kernel knobs exposed through `/proc/sys` and persisted through files under locations such as `/etc/sysctl.d/`. They are attractive because a single line can change real kernel behavior, but they are also risky because a generic hardening baseline can conflict with Kubernetes networking. You should evaluate every setting in terms of what it blocks, what Kubernetes requires, and how you will verify the effect.

The first group reduces network abuse that should not be needed on a worker node. ICMP redirects and source routing are old mechanisms that can help redirect traffic in ways a modern cluster should not trust. SYN cookies protect against some SYN flood pressure, martian logging records suspicious packets, and broadcast ping suppression removes a noisy amplification behavior.

```bash
# View current settings
sysctl -a | grep -E "net.ipv4|kernel" | head -20
```

Add the hardened values to a managed sysctl file rather than pasting the configuration lines directly into a shell prompt.

```ini
# /etc/sysctl.d/99-kubernetes-security.conf
# Disable IP forwarding if not needed (kubelets need it!)
# net.ipv4.ip_forward = 0  # Don't disable on K8s nodes!

# Ignore ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0

# Enable SYN flood protection
net.ipv4.tcp_syncookies = 1

# Log suspicious packets
net.ipv4.conf.all.log_martians = 1

# Ignore broadcast ping
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Disable source routing
net.ipv4.conf.all.accept_source_route = 0

# Enable ASLR
kernel.randomize_va_space = 2

# Restrict dmesg access
kernel.dmesg_restrict = 1

# Restrict kernel pointers
kernel.kptr_restrict = 1
```

```bash
# Apply settings
sudo sysctl -p /etc/sysctl.d/99-kubernetes-security.conf
```

The kernel settings in that file do not all protect the same phase of an attack. `kernel.randomize_va_space = 2` enables full address space layout randomization for user processes, making memory corruption exploitation less predictable. `kernel.dmesg_restrict = 1` blocks unprivileged users from reading kernel ring buffer details, while `kernel.kptr_restrict = 1` or a stricter value reduces exposure of kernel pointer addresses that can make exploitation easier.

Network sysctls need special attention because Kubernetes networking uses forwarding deliberately. Pod traffic may cross veth pairs, bridges, overlay interfaces, and the node's primary interface, depending on the CNI. If a generic compliance rule says every Linux host must disable forwarding, applying it blindly can break cross-node Pod communication and Service routing even though the node looks more secure to the scanner.

```ini
# /etc/sysctl.d/99-kubernetes.conf

# Required for Kubernetes networking
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1

# For pod networking
net.ipv4.conf.all.forwarding = 1

# Connection tracking for services
net.netfilter.nf_conntrack_max = 131072
```

Pause and predict: you set `net.ipv4.ip_forward = 0` on a Kubernetes worker node to satisfy a generic server hardening checklist. Which traffic path fails first, and what evidence would you collect to prove that Kubernetes requires forwarding while still rejecting source routing and redirects?

The answer depends on the CNI, but the reasoning is stable. Packets must move between Pod interfaces and other network interfaces, and the node participates in forwarding those packets under rules installed by kube-proxy, the CNI, or an eBPF dataplane. You can keep forwarding enabled while still disabling redirects, source routing, and other behaviors that let untrusted hosts influence routing decisions.

Treat sysctl files as configuration artifacts that require review and ownership. A handwritten change made during an incident can disappear on reboot if it was only applied with `sysctl -w`, and a cloud image update can overwrite a file if the image pipeline is not the source of truth. The durable pattern is to manage these settings through the node image, machine configuration, or a privileged node bootstrap mechanism that your security team approves.

Linux often has `all`, `default`, and interface-specific forms of the same network setting, and the distinction matters. `all` can affect existing interfaces, `default` influences interfaces created later, and a specific interface value may still surprise you when a CNI creates bridge, veth, tunnel, or eBPF-related devices. When a setting appears correct in one place but behavior disagrees, inspect the per-interface values rather than assuming the global value won.

Kubernetes also exposes a limited sysctl surface through Pod security context, but that is not the same as host kernel hardening. Namespaced sysctls can be safe for a Pod because they affect only that Pod's namespace, while unsafe sysctls can affect the node or other workloads and require explicit kubelet allowance. On a hardened cluster, you should be skeptical of `allowedUnsafeSysctls` unless there is a narrow workload reason and a dedicated node boundary.

Connection tracking is a good example of tuning that can be both availability-related and security-relevant. A value that is too low can drop legitimate Service traffic under load, while an unbounded or poorly understood value can hide exhaustion risk. The right setting depends on node size, workload connection patterns, kube-proxy or eBPF dataplane behavior, and the observability you have for conntrack pressure.

Validation should include negative expectations. If `kernel.dmesg_restrict` is enabled, an unprivileged user should fail to read kernel messages; if redirects are disabled, the node should not accept redirect-based route influence; if forwarding is enabled for Kubernetes, ordinary workload traffic should still pass. Hardening checks become more credible when they show both what still works and what is intentionally blocked.

The CKS exam tends to test recognition and diagnosis rather than long kernel theory. You may be asked to inspect current values, apply a small hardening file, or identify why a "secure" change broke the cluster. The right habit is to read the current value first, apply one well-scoped file, verify the value afterwards, and explain any Kubernetes-required exception rather than hiding it.

```bash
# Check sysctl settings
sysctl net.ipv4.ip_forward
sysctl kernel.randomize_va_space

# Check for unnecessary services
systemctl list-units --type=service --state=running | wc -l

# Check SSH configuration
grep -E "PermitRootLogin|PasswordAuthentication" /etc/ssh/sshd_config
```

The previous check is intentionally small because an exam terminal rewards precise inspection. `net.ipv4.ip_forward` tells you whether basic forwarding is available, `kernel.randomize_va_space` confirms ASLR behavior, the service count gives a quick signal for node drift, and the SSH grep checks two high-value access controls. From there, you can inspect the exact file that owns a surprising value.

```bash
# Create hardening config
sudo tee /etc/sysctl.d/99-cks-hardening.conf << 'EOF'
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
EOF

# Apply
sudo sysctl -p /etc/sysctl.d/99-cks-hardening.conf

# Verify
sysctl kernel.dmesg_restrict
```

When you set `kernel.kptr_restrict = 2`, you are choosing a stricter posture than the earlier example value of `1`. That may be appropriate for production nodes where observability tooling does not need unredacted kernel pointers from unprivileged contexts. If a diagnostic tool breaks, the fix should be a narrowly authorized debugging path, not a permanent relaxation across every worker.

---

## Protect Host Files, `/proc`, `/sys`, and Mount Boundaries

The Linux kernel exposes enormous amounts of system information through pseudo-filesystems such as `/proc` and `/sys`. That visibility is useful for administrators and monitoring agents, but it can also help attackers enumerate processes, kernel modules, command lines, device information, and runtime state. Host hardening therefore includes both what ordinary users can see on the node and what containers are allowed to see through their mounts.

```text
# Restrict access to process information
# In /etc/fstab or mount options:
proc    /proc    proc    defaults,hidepid=2    0    0

# hidepid options:
# 0 = default (all users can see all processes)
# 1 = users can see their own processes only
# 2 = users can't see other users' processes

# For containers, Kubernetes manages these mounts
# But host should restrict access
```

The `hidepid` option is a host-level control, so do not confuse it with Pod-level process namespace behavior. Kubernetes can decide whether a Pod shares a process namespace, and the runtime creates container-specific views, but the host still needs a policy for local users and node agents. If an unprivileged local account can inspect every host process, a container escape gains an easier map of credentials, command lines, and running services.

`/sys` has a different flavor of risk because it exposes kernel and device interfaces rather than ordinary process metadata. Many legitimate node components need parts of it, especially storage, networking, and hardware-related agents. The hardening question is not whether `/sys` exists; the question is whether containers receive privileged host mounts or broad write access that lets them influence kernel or device behavior.

Sensitive Kubernetes files deserve explicit permission checks. Kubelet configuration, kubelet client credentials, kubeadm-generated certificates, and private keys are high-value files because they can let an attacker authenticate to the API server or impersonate node components. Restrictive permissions do not fix a stolen root shell, but they reduce accidental exposure to unprivileged users and poorly isolated processes.

```bash
# Secure kubelet files
sudo chmod 600 /var/lib/kubelet/config.yaml
sudo chmod 600 /etc/kubernetes/kubelet.conf
sudo chown root:root /var/lib/kubelet/config.yaml

# Secure certificates
sudo chmod 600 /etc/kubernetes/pki/*.key
sudo chmod 644 /etc/kubernetes/pki/*.crt
```

The difference between private keys and certificates matters. Private keys should be readable only by root or the specific service account that needs them, because possession of the key can enable impersonation. Certificates are public by design, so read-only permissions are normally fine, but broad write permissions on either kind of file are a serious integrity problem.

```bash
# Fix kubelet config permissions
sudo chmod 600 /var/lib/kubelet/config.yaml
sudo chown root:root /var/lib/kubelet/config.yaml

# Verify
ls -la /var/lib/kubelet/config.yaml
```

Filesystem mount options add another layer of defense after a process gains some write access. `nodev` prevents device files from being interpreted on that filesystem, `nosuid` prevents setuid bits from granting privilege, and `noexec` prevents direct execution from paths that should only store data or logs. These controls are not perfect bypass-proof walls, but they force attackers to work harder and remove common shortcuts.

```text
# /etc/fstab entries with security options

# Separate partitions for:
# /var/lib/containerd  - Container data
# /var/log             - Logs
# /tmp                 - Temporary files

# Example secure mount options:
/dev/sda3  /var/lib/containerd  ext4  defaults,nodev,nosuid  0  2
/dev/sda4  /tmp                 ext4  defaults,nodev,nosuid,noexec  0  2
/dev/sda5  /var/log             ext4  defaults,nodev,nosuid,noexec  0  2

# Options:
# nodev   - No device files
# nosuid  - No setuid executables
# noexec  - No execution
```

Mount choices must respect workload reality. Applying `noexec` to `/tmp` on the host is often sensible, but applying it to a path where a runtime or storage plugin expects to execute helper binaries can break node operation. The decision belongs in node image testing, not as an after-hours manual change across a live pool.

Read-only root filesystems are the strongest version of this idea. In immutable infrastructure, the node image is replaced instead of modified, writable state is isolated, and configuration comes from a controlled pipeline. This model sharply reduces drift, but it requires good operational tooling because the old habit of "SSH in and edit a file" no longer works.

```text
# For immutable infrastructure:
# Mount root as read-only, use overlay for writes

# This is often handled by the OS distribution
# (CoreOS, Flatcar, Talos, etc.)
```

Before running this, what output do you expect from `ls -la /var/lib/kubelet/config.yaml` on a hardened kubeadm-style node? A useful answer names both ownership and permissions: root should own the file, ordinary users should not be able to read it, and any surprising group or world permissions should send you to the image build or bootstrap scripts that created the drift.

HostPath volumes are where file hardening and Kubernetes policy meet directly. A Pod that mounts `/var/lib/kubelet`, `/etc/kubernetes`, `/var/run`, or broad host paths can bypass many of the assumptions you made about container isolation. Privileged DaemonSets sometimes need host access for networking, storage, or monitoring, but they should live in tightly controlled namespaces with reviewed manifests, dedicated service accounts, and node placement rules.

Device plugins and hardware agents deserve similar scrutiny. GPU, storage, and networking integrations may legitimately expose devices or host paths, yet they also expand what a compromised Pod can touch. The senior move is not to ban every plugin; it is to isolate the nodes that need them, review their required privileges, and avoid scheduling ordinary application workloads onto the same high-privilege pool without a reason.

Kubelet credentials connect node hardening to cluster authorization. A stolen kubelet client credential may not grant unlimited cluster-admin power, but it can still expose node and workload operations that help an attacker pivot. File permissions, certificate rotation, Node authorizer behavior, and NodeRestriction admission are separate controls that work together, so a host audit should note both local file exposure and API permissions.

---

## Evaluate Runtime Isolation and Audit Evidence

Container runtime hardening is where host controls meet Pod controls. The runtime chooses how to create containers, which seccomp profile applies by default, how cgroups integrate with systemd, and whether user namespace or alternative runtime support is available. Kubernetes 1.35 still depends on this lower layer, so a clean Pod manifest cannot rescue a runtime configured with weak defaults.

```toml
# /etc/containerd/config.toml

[plugins."io.containerd.grpc.v1.cri"]
  # Disable privileged containers (if possible)
  # Note: Some system pods need privileges

  [plugins."io.containerd.grpc.v1.cri".containerd]
    # Use native (not kata) for performance
    default_runtime_name = "runc"

    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
      runtime_type = "io.containerd.runc.v2"

      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
        # Use systemd cgroups
        SystemdCgroup = true
```

This containerd snippet preserves the common `runc` path while showing where runtime choices live. `SystemdCgroup = true` aligns the runtime with systemd-managed cgroups, which is the expected posture for many Kubernetes distributions. It is not a seccomp switch. Teach seccomp at the Pod layer with `securityContext.seccompProfile.type: RuntimeDefault`, and on clusters that deliberately default every workload, verify kubelet `--seccomp-default` behavior instead of assuming the cgroup setting filtered syscalls.

Some environments still use Docker Engine for adjacent build hosts, so the same hardening ideas appear in Docker configuration even when Kubernetes nodes run containerd. User namespace remapping can make container root map to a less privileged host identity, `no-new-privileges` blocks privilege escalation across exec, and seccomp profiles constrain syscall access. Inter-container communication and live restore settings then become additional operational decisions.

```json
{
  "userns-remap": "default",
  "no-new-privileges": true,
  "seccomp-profile": "/path/to/seccomp-profile.json",
  "icc": false,
  "live-restore": true
}
```

Runtime isolation is also visible from Kubernetes manifests. A Pod that runs as non-root, drops capabilities, prevents privilege escalation, uses the runtime default seccomp profile, and mounts a read-only root filesystem gives the kernel fewer dangerous operations to mediate. These controls are not replacements for host hardening; they reduce the chance that a compromised application reaches the host boundary with enough power to exploit it.

The old habit of leaving debugging tools permanently installed on the node conflicts with runtime hardening. Kubernetes gives you better tools now, including ephemeral debug containers and node debugging workflows, so you can investigate without keeping compilers, scanners, and shell utilities on every worker forever. That distinction matters because a tool that helps an administrator after login can also help an attacker after escape.

Audit evidence closes the loop. Hardening without audit gives you a desired state but little proof that it stayed true, while audit without hardening gives you detailed records of preventable exposure. The useful middle ground is to monitor high-value runtime binaries, configuration directories, container storage paths, kubelet configuration, and Kubernetes certificate locations for changes that should be rare. Start with the paths that exist on the node; for example, kind nodes running containerd expose the runtime binary at `/usr/local/bin/containerd`, so do not assume a distribution-specific binary location.

```bash
# Install auditd
sudo apt install -y auditd

# Configure containerd-first audit rules
sudo install -m 0640 /dev/null /etc/audit/rules.d/container-runtime.rules
for rule in \
  "containerd:/usr/local/bin/containerd" \
  "containerd-storage:/var/lib/containerd" \
  "containerd-config:/etc/containerd" \
  "kubernetes:/etc/kubernetes" \
  "kubelet:/var/lib/kubelet"
do
  key="${rule%%:*}"
  path="${rule#*:}"
  if sudo test -e "$path"; then
    printf -- "-w %s -p wa -k %s\n" "$path" "$key" | sudo tee -a /etc/audit/rules.d/container-runtime.rules >/dev/null
  else
    echo "Skipping missing audit path: $path"
  fi
done

# Legacy Docker Engine watches belong only on nodes where these paths exist.
# Add dockerd, Docker config, and Docker storage watches after test -e confirms them.

# Apply rules
sudo augenrules --load
```

These audit rules are intentionally focused on change evidence, not on logging every syscall made by every container. Excessive audit volume can hide the signal you need, exhaust disk, and make responders ignore the system. Good audit design asks which file or binary changes would surprise you on an immutable or tightly managed node, then records those events with keys that make searching practical.

The Hands-On Exercise later ties node hardening back to Pod-level behavior with an insecure Pod and a hardened Pod. It does not claim that a secure Pod fixes a weak host, but it shows how the same ideas appear at different layers: identity, filesystem writes, capabilities, seccomp, and privilege escalation all affect what a compromised process can ask the shared kernel to do. The node still needs host hardening underneath both Pods.

Privileged DaemonSets are the exception that proves the rule. Networking, storage, logging, and security agents often need host namespaces, device access, or elevated capabilities, which means they can become powerful post-compromise targets. Harden them by minimizing their image contents, pinning their privileges to exact needs, using dedicated namespaces and service accounts, and scheduling them only where the node role requires them.

Alternative runtimes can change the kernel-sharing tradeoff, but they introduce their own cost. Sandboxed runtimes or lightweight virtual machine approaches may provide a stronger boundary for risky workloads, while ordinary `runc` keeps performance and operational simplicity. The decision should be workload-specific: use heavier isolation where tenant risk or untrusted code justifies it, and keep the standard runtime for workloads that already fit the hardened baseline.

Kubernetes audit logs and Linux auditd logs answer different questions. Kubernetes audit records API decisions such as creating a privileged Pod or changing a DaemonSet, while auditd can record changes to host binaries, configuration files, and certificate paths after a process reaches the node. Mature investigations correlate both streams instead of expecting one layer to explain activity that happened in the other.

Evidence retention needs an owner before an incident. If audit logs live only on the node, an attacker with host access may delete or alter the most useful records. Forwarding audit events to a central system, protecting timestamps with reliable time sync, and keeping enough retention for delayed discovery turn auditd from a local troubleshooting tool into a security control.

---

## Patterns & Anti-Patterns

Patterns and anti-patterns are useful only when they change a decision you would make under pressure. For kernel hardening, the common split is between controls that make the node simpler, controls that make exploitation less informative, and controls that make drift visible. The table below keeps those categories separate so you can defend a change without claiming that one setting solves every host risk.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---------|----------------|--------------|-----------------------|
| Immutable or tightly rebuilt worker images | Node pools managed by autoscaling, managed Kubernetes, or image pipelines | Replaces manual drift with repeatable build inputs and makes patch rollout auditable | Requires reliable drain, replacement, and rollback automation |
| Kubernetes-aware sysctl baseline | Any worker node that must run Pod networking while reducing network abuse | Keeps required forwarding while disabling redirects, source routing, and kernel information leaks | Needs CNI-specific validation and a documented exception for forwarding |
| Runtime default seccomp plus explicit Pod security contexts | Application namespaces where workloads can run with reduced privilege | Narrows syscall, capability, identity, and filesystem exposure before host controls are tested | Requires workload owners to handle writable paths and non-root image compatibility |
| Focused audit rules for node-critical files | Regulated or incident-sensitive clusters where evidence matters | Records changes to runtime, kubelet, certificate, and container storage paths that should be rare | Needs log retention, alert routing, and noise control to stay useful |

The strongest anti-pattern is generic hardening without platform knowledge. Disabling IP forwarding, removing a CNI dependency, or applying `noexec` to a runtime path may satisfy a checklist line while breaking the cluster. A better approach is to document why Kubernetes needs a setting, then apply adjacent controls that reduce the actual risk without disabling the platform behavior.

| Anti-Pattern | What Goes Wrong | Why Teams Fall Into It | Better Alternative |
|--------------|-----------------|------------------------|--------------------|
| Treating node hardening as only Pod admission policy | Host packages, services, files, and kernel settings drift outside the API server view | Kubernetes-native controls are easier to inspect than operating system state | Pair Pod security review with node image, sysctl, service, and runtime checks |
| Leaving debugging tools installed forever | Escaped containers inherit compilers, shells, scanners, and network utilities on the host | Operators want fast incident response and fear losing emergency access | Use ephemeral debug containers, break-glass access, and temporary tooling workflows |
| Applying generic Linux baselines blindly | Required Kubernetes networking or runtime paths stop working | Compliance templates often target ordinary servers, not worker nodes | Translate each control into Kubernetes terms and record justified exceptions |
| Auditing everything instead of important changes | Logs become noisy, expensive, and ignored during incidents | More audit rules feel safer than choosing a small set of signals | Monitor high-value binaries, configs, credentials, and storage paths first |

The pattern table should also make tradeoffs visible. Immutable nodes reduce drift but demand better automation, strict runtime settings reduce attack surface but may require application fixes, and audit rules improve evidence but consume storage and attention. A hardened node is therefore an engineered operating model, not just a pasted sysctl file.

---

## Decision Framework

Use this framework when you must decide whether a host hardening change belongs in a Kubernetes worker image, a runtime configuration, a Pod manifest, or an operational procedure. The first question is whether the control changes required platform behavior. If it does, test it in a node pool that matches the CNI, storage, and runtime stack before calling it a baseline.

| Decision Point | Choose This When | Avoid It When | Verification Signal |
|----------------|------------------|---------------|---------------------|
| Node image package removal | Software is not required for kubelet, runtime, CNI, storage, monitoring, or approved access | The package belongs to a managed agent or node bootstrap dependency | New node joins, schedules Pods, and package count stays stable across rebuilds |
| Service disabling | The service has no Kubernetes or management role and listens locally or on the network | Ownership is unclear or dependencies point to runtime, network, storage, or monitoring | `systemctl` shows the service disabled and workload smoke tests still pass |
| Sysctl hardening | The value blocks information leaks or unsafe network behavior without breaking required forwarding | A generic baseline conflicts with CNI or kube-proxy behavior | `sysctl` values match the file and Pod-to-Pod plus Service traffic works |
| File permission correction | Kubelet config, kubeconfig, private keys, or runtime config are readable beyond their owner | A vendor-managed agent rewrites the file and needs a documented permission model | `ls -la` shows expected owner and mode after reboot or node replacement |
| Runtime isolation | Workloads can run with fewer capabilities, non-root identity, seccomp, and read-only roots | Legacy images require root writes and cannot be changed quickly | Pod starts successfully and denied operations fail as expected |
| Audit rule deployment | The path is high value and should change rarely | The rule logs high-volume normal runtime activity | Audit events are searchable by key and alert volume stays actionable |

For exam speed, compress the framework into three questions. Does Kubernetes need this behavior to route, schedule, or run containers? If not, can you remove or restrict it at the node image or runtime layer? If yes, what compensating control proves that the required behavior is constrained rather than forgotten?

In production, add one more question: where does the change live so it survives replacement? A sysctl typed into a node shell is a temporary experiment, while a machine configuration, image build, or documented bootstrap script is a baseline. The same distinction applies to service state, package removal, file permissions, audit rules, and runtime settings.

The framework also helps resolve disagreements with compliance teams. You can show that disabling forwarding is inappropriate for a worker node, but accepting redirects and source routing is unnecessary. That creates a precise exception rather than a vague request to ignore Linux hardening, and it gives auditors concrete values to check.

The final decision rule is to test from both sides of the boundary. From the host, inspect packages, services, sysctls, files, runtime config, and audit rules. From Kubernetes, create a workload that proves the runtime settings behave as expected, then verify that ordinary application traffic still works. A control that cannot be observed is difficult to defend during an incident or an exam.

Prioritize changes by blast radius and reversibility. Patching a critical kernel flaw or removing an exposed unnecessary service may outrank a cosmetic benchmark finding, while changing a networking sysctl across every node pool deserves staged testing because the rollback cost is higher. A good hardening plan names which control fails closed, which fails open, and which failure mode the platform can tolerate during rollout.

Use node pools as the unit of change. Applying a setting to one hand-edited node teaches you very little about autoscaling behavior, replacement behavior, or heterogeneous workload needs. Applying it to a small canary pool with representative CNI, storage, runtime, and monitoring agents gives you real evidence before the same baseline reaches every worker.

Finally, record the reason for each exception beside the control. "IP forwarding enabled because Kubernetes networking requires it on this CNI, with redirects and source routing disabled" is useful; "scanner exception approved" is not. Future reviewers need enough context to distinguish a deliberate platform requirement from a forgotten security gap.

---

## Did You Know?

- **Container-optimized OSes** like Flatcar, Talos, and Bottlerocket are purpose-built for running containers with minimal attack surface, and they usually push teams toward image replacement instead of manual host repair.

- **ASLR (Address Space Layout Randomization)** makes many memory corruption attacks less reliable because process memory locations change instead of staying fixed, which is why `kernel.randomize_va_space = 2` is a common baseline check.

- **User namespaces** can provide additional isolation by mapping container root to an unprivileged host user, but support and operational defaults vary by runtime, distribution, and Kubernetes feature maturity.

- **Kernel live patching** systems such as Ubuntu Livepatch and RHEL kpatch can reduce reboot pressure for some security fixes, but they do not remove the need for planned node replacement and full kernel lifecycle management.

---

## Common Mistakes

Most kernel-hardening mistakes are not caused by ignorance of a command; they are caused by applying the command in the wrong layer or without a rollback path. Use this table as a diagnostic checklist when a scanner, an exam question, or a production review reports a weak node posture.

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Not patching regularly | Known CVEs remain exploitable because node images or live nodes are treated as stable forever | Automate image rebuilds or approved security updates, then drain and replace nodes on a tested schedule |
| Default SSH config | Root login or password authentication survives because SSH is considered an operations concern instead of a node security boundary | Disable root SSH, disable passwords, restrict allowed users, and prefer controlled break-glass workflows |
| Too many services | Base images inherit printing, discovery, wireless, or RPC daemons that do not serve Kubernetes workloads | Inventory running services, identify ownership, disable unnecessary units in the image, and retest scheduling |
| Wrong file permissions | Kubelet configs, kubeconfigs, or private keys are created by bootstrap scripts with broad read access | Set root ownership, restrict private files to mode `600`, and verify permissions after node replacement |
| No audit logging | Incident responders cannot prove whether runtime binaries, kubelet files, or certificate paths changed | Deploy focused auditd rules for high-value paths and route keyed events into retained logs |
| Blindly disabling IP forwarding | A generic Linux baseline is copied onto worker nodes without understanding Pod networking | Keep required forwarding enabled, document the Kubernetes exception, and disable redirects and source routing instead |
| Leaving debug tools on nodes | Troubleshooting convenience slowly turns into permanent attacker tooling after a container escape | Move routine debugging to `kubectl debug`, ephemeral containers, and temporary approved access paths |

---

## Quiz

Each question describes a node-hardening decision rather than asking for a memorized command. Read the scenario, choose the first thing you would verify, and then compare your reasoning with the answer before moving on.

<details>
<summary>Your team sets `net.ipv4.ip_forward = 0` on every worker because a generic Linux benchmark recommends disabling forwarding. Pod-to-Pod traffic across nodes immediately fails, but the security team still wants evidence that the exception is justified. What do you check and how do you explain the safer hardening path?</summary>

Check the current forwarding value, verify the CNI or kube-proxy traffic path that requires forwarding, and collect a simple Pod-to-Pod or Pod-to-Service failure that recovers when forwarding is restored. Kubernetes worker nodes often need forwarding because packets move between Pod interfaces, overlay or bridge devices, and the node interface. The safer path is not to accept every network feature; keep forwarding as a documented Kubernetes requirement while disabling redirects, source routing, and other behaviors that let untrusted peers influence routing. That answer aligns the sysctl diagnosis with the shared-kernel networking model.
</details>

<details>
<summary>An attacker escapes a container as an unprivileged host user and tries to read `dmesg` plus kernel pointer information to select a privilege escalation exploit. Which sysctl values reduce that reconnaissance, and why are they useful even though they do not patch the vulnerability itself?</summary>

Set `kernel.dmesg_restrict = 1` so unprivileged users cannot read kernel ring buffer messages, and set `kernel.kptr_restrict = 1` or `2` to reduce exposure of kernel pointer addresses. These settings do not remove a kernel bug, but they remove information that can make exploitation more reliable. They are defense-in-depth controls for the phase after an attacker has gained some local execution but before they have a dependable host exploit. Pair them with timely kernel patching, because secrecy controls are not substitutes for vulnerability remediation.
</details>

<details>
<summary>A worker image includes desktop utilities, build tools, network troubleshooting binaries, and several services that no one owns. The operations team says the tools make outages easier to debug. How do you design a minimal host OS baseline without leaving responders blind?</summary>

Start by defining the node's required functions: container runtime, kubelet, CNI support, time sync, approved monitoring, and controlled management access. Remove unrelated packages and services in the image pipeline rather than by one-off shell cleanup, then validate that a fresh node can join, schedule Pods, and report health. For response needs, use ephemeral debug containers, approved break-glass access, and temporary tooling workflows instead of permanent tools on every worker. This preserves operational visibility while reducing what an escaped container can reuse on the host.
</details>

<details>
<summary>During a host audit, `/var/lib/kubelet/config.yaml` is world-readable and a private key under `/etc/kubernetes/pki` has broad permissions. What risk does this create, and what evidence should your fix leave behind?</summary>

The risk is exposure of kubelet configuration, kubeconfigs, certificates, or private keys that may help an attacker authenticate to the API server or impersonate node components. Fix ownership and permissions so sensitive kubelet files and private keys are root-owned with restrictive modes such as `600`, while public certificates remain read-only. The evidence should include `ls -la` output after the change and, ideally, the image or bootstrap configuration that will recreate the same permissions on replacement nodes. Without persistence, the fix can disappear at the next rebuild.
</details>

<details>
<summary>A scanner flags missing `hidepid=2` on `/proc`, but a monitoring agent relies on process visibility. How do you decide whether to apply the setting, and what Kubernetes concept must you avoid confusing it with?</summary>

First identify whether the monitoring agent truly needs host-wide process visibility and whether it can run with a dedicated group or alternative collection method. `hidepid=2` is a host mount behavior for local process visibility, while Kubernetes Pod process namespace settings control what containers see inside their own namespaces. Do not claim that a Pod security context automatically fixes host `/proc` exposure. If you keep broader visibility for an agent, document that exception and restrict the agent's identity and access path.
</details>

<details>
<summary>A secure Pod manifest sets `runAsNonRoot`, drops all capabilities, uses `RuntimeDefault` seccomp, disables privilege escalation, and sets a read-only root filesystem. The node still runs old services and has weak kernel sysctls. Has the team solved kernel hardening?</summary>

No. The Pod manifest reduces what that workload can do before it reaches the kernel boundary, which is valuable, but it does not patch the host, remove unnecessary daemons, protect kubelet files, or restrict kernel information leaks for other local users. Kernel and OS hardening must happen at the node image, runtime configuration, sysctl, filesystem, and audit layers as well. The correct evaluation is layered: the Pod is better isolated, but the node still has host-level gaps that can affect every workload scheduled there.
</details>

<details>
<summary>You enable auditd and create broad rules that log a huge volume of container runtime activity. After a week, the security team ignores the alerts because nearly everything looks noisy. How would you redesign the audit rules for kernel and node hardening?</summary>

Focus audit rules on high-value paths where change should be rare: runtime binaries, runtime configuration directories, Kubernetes configuration, kubelet state, certificates, and container storage metadata. Use meaningful keys so responders can search for `containerd`, `kubelet`, or `kubernetes` events quickly. Avoid logging normal high-volume container activity unless there is a specific investigation need, because excessive volume hides important changes and can exhaust storage. Good audit design proves drift and tampering without turning every normal workload into alert noise.
</details>

---

## Learner check

> A hardening lab is only useful when you can name the exact kernel boundary it proved and the boundary it merely inspected.

Before you trust a command as evidence, ask whether it tests the control named in the lesson. A failed read of `/etc/shadow` from a non-root container proves ordinary file permissions and user identity, not `allowPrivilegeEscalation: false`. For that control, inspect the Linux `NoNewPrivs` flag or run a deliberately scoped setuid demonstration in a disposable lab.

---

## Hands-On Exercise

This exercise uses Kubernetes security contexts to demonstrate host-hardening concepts safely. You will compare an insecure Pod with a hardened Pod, then map each observed difference back to the kernel or OS control it resembles. If you are working on a real cluster, use a disposable namespace and avoid running privileged experiments on production nodes.

### Setup

Run the preserved lab script below in a test cluster where you can create and delete a namespace. The script deploys two BusyBox Pods, compares identity, filesystem, default Pod PID namespace, `/proc`, `NoNewPrivs`, and security context behavior, then prints host sysctl checks you would run on the actual node. It intentionally uses full `kubectl` commands so the block works in non-interactive shells.

### Tasks

- [ ] Diagnose the current security difference between the insecure Pod and the secure Pod by comparing user identity, security context output, and write behavior.
- [ ] Design a minimal host OS baseline for the same node pool by listing which packages, services, SSH settings, and patch workflow you would require before production.
- [ ] Audit kubelet configuration, certificate permissions, `/proc` visibility, `/sys` exposure, and auditd coverage on a real or simulated worker node.
- [ ] Evaluate container runtime isolation by explaining how seccomp, dropped capabilities, read-only root filesystems, and privilege escalation controls reduce kernel-facing risk.
- [ ] Verify the Kubernetes-required sysctl exception for IP forwarding while confirming that redirects, source routing, dmesg access, and kernel pointer exposure are restricted.

<details>
<summary>Solution guide for task 1</summary>

The insecure Pod should run with default identity and a writable filesystem, while the secure Pod should run as UID `1000`, show a Pod-level security context, and fail writes that target the read-only root filesystem. Treat each difference as a kernel-facing constraint: identity reduces root assumptions, the read-only root reduces write targets, dropped capabilities remove privileged operations, and seccomp narrows syscall access. If one of these checks behaves differently in your cluster, inspect admission policies and runtime defaults before assuming the manifest was ignored.
</details>

<details>
<summary>Solution guide for task 2</summary>

A minimal baseline includes the container runtime, kubelet, CNI dependencies, time synchronization, approved monitoring, and a controlled management path. Remove unrelated packages and services from the node image, disable root SSH and password authentication if SSH exists, and choose a patch workflow such as image replacement or approved unattended security updates. The success condition is not a perfect package count; it is that a fresh node can join the cluster, run workloads, and reproduce the same hardened state.
</details>

<details>
<summary>Solution guide for task 3</summary>

Check that kubelet configuration and kubeconfigs are root-owned and restrictive, private keys under Kubernetes certificate paths are not broadly readable, and host `/proc` visibility is intentionally configured. Review whether containers or agents receive broad `/sys` mounts, then confirm that auditd watches runtime binaries, runtime configuration, kubelet paths, and Kubernetes certificate directories. Evidence should survive node replacement, so prefer image or bootstrap configuration over manual repair.
</details>

<details>
<summary>Solution guide for task 4</summary>

Evaluate runtime isolation by asking what the workload can ask the kernel to do after compromise. `RuntimeDefault` seccomp removes many unnecessary syscall paths, dropping capabilities reduces privileged kernel operations, `allowPrivilegeEscalation: false` maps to the Linux `NoNewPrivs` flag, and a read-only root filesystem removes easy persistence locations. These controls are strongest when paired with host patching, sysctl restrictions, minimal packages, and focused audit evidence.
</details>

<details>
<summary>Solution guide for task 5</summary>

Check `net.ipv4.ip_forward`, `net.bridge.bridge-nf-call-iptables`, and the CNI documentation for your cluster before changing forwarding behavior. Keep forwarding enabled when the dataplane requires it, then verify that `accept_redirects`, `send_redirects`, and `accept_source_route` are disabled and that `kernel.dmesg_restrict` plus `kernel.kptr_restrict` are set. A good answer distinguishes required Kubernetes forwarding from unnecessary network trust features.
</details>

### Lab Script

```bash
# Since we can't modify the host kernel from Kubernetes, we'll demonstrate
# how kernel hardening concepts translate to container security.

# Step 1: Create namespace for testing
kubectl create namespace kernel-test

# Step 2: Deploy pod WITHOUT security hardening (insecure baseline)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod
  namespace: kernel-test
spec:
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    # No security context = dangerous!
EOF

# Step 3: Deploy pod WITH security hardening (secure)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
  namespace: kernel-test
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
EOF

# Wait for pods to be ready
kubectl wait --for=condition=Ready pod/insecure-pod -n kernel-test --timeout=60s
kubectl wait --for=condition=Ready pod/secure-pod -n kernel-test --timeout=60s

# Step 4: Compare what each pod can do
echo "=== Insecure Pod: Who am I? ==="
kubectl exec -n kernel-test insecure-pod -- id

echo "=== Secure Pod: Who am I? ==="
kubectl exec -n kernel-test secure-pod -- id

# Step 5: Test filesystem access
echo "=== Insecure Pod: Can write to /tmp? ==="
kubectl exec -n kernel-test insecure-pod -- sh -c "echo 'test' > /tmp/test.txt && echo 'Write succeeded' || echo 'Write failed'"

echo "=== Secure Pod: Can write to /tmp? (should fail - readOnlyRootFilesystem) ==="
kubectl exec -n kernel-test secure-pod -- sh -c "echo 'test' > /tmp/test.txt && echo 'Write succeeded' || echo 'Write blocked!'"

# Step 6: Observe default Pod PID namespace visibility
echo "=== Insecure Pod: Process list inside its Pod PID namespace ==="
kubectl exec -n kernel-test insecure-pod -- ps aux | head -5

echo "=== Secure Pod: Process list inside its Pod PID namespace ==="
kubectl exec -n kernel-test secure-pod -- ps aux | head -5
echo "Both Pods use normal isolated Pod PID namespaces; host hidepid must be checked on the node."

# Step 7: Check proc access
echo "=== Checking /proc access in secure pod ==="
kubectl exec -n kernel-test secure-pod -- cat /proc/1/cmdline 2>&1 | tr '\0' ' ' && echo ""

# Step 8: Check security context applied
echo "=== Security Context Comparison ==="
echo "Insecure pod security context:"
kubectl get pod insecure-pod -n kernel-test -o jsonpath='{.spec.securityContext}' && echo ""
echo "Secure pod security context:"
kubectl get pod secure-pod -n kernel-test -o jsonpath='{.spec.securityContext}' && echo ""

# Step 9: Verify allowPrivilegeEscalation through no_new_privs
echo "=== no_new_privs flag (allowPrivilegeEscalation=false) ==="
echo "Insecure pod:"
kubectl exec -n kernel-test insecure-pod -- sh -c "grep NoNewPrivs /proc/self/status"
echo "Secure pod:"
kubectl exec -n kernel-test secure-pod -- sh -c "grep NoNewPrivs /proc/self/status"

# Step 10: Check non-root permissions without confusing them for no_new_privs
echo "=== Non-root file permission check ==="
kubectl exec -n kernel-test secure-pod -- sh -c "cat /etc/shadow 2>&1" || echo "Root-only file blocked for non-root user (expected)"

# Step 11: Check host sysctl (if running on actual node)
echo ""
echo "=== Host Kernel Checks (run on actual node) ==="
echo "To check on your actual cluster nodes:"
echo "  sysctl kernel.randomize_va_space    # Should be 2"
echo "  sysctl kernel.dmesg_restrict        # Should be 1"
echo "  sysctl kernel.kptr_restrict         # Should be 1 or 2"
echo "  sysctl net.ipv4.conf.all.accept_redirects  # Should be 0"
echo "  findmnt -no OPTIONS /proc           # Check host hidepid options on the node"

# Cleanup
echo ""
echo "=== Cleanup ==="
kubectl delete namespace kernel-test

echo ""
echo "=== Exercise Complete ==="
echo "Key learnings demonstrated:"
echo "1. ✓ runAsNonRoot prevents root execution"
echo "2. ✓ readOnlyRootFilesystem blocks writes"
echo "3. ✓ Dropping capabilities limits syscalls"
echo "4. ✓ allowPrivilegeEscalation=false maps to NoNewPrivs"
echo "5. ✓ seccompProfile applies syscall filtering"
echo "6. ✓ default Pod PID namespaces are not the same as host hidepid"
```

### Success Criteria

- [ ] You can explain why containers share the host kernel and why that makes node hardening different from virtual-machine hardening.
- [ ] You can show at least three host-level checks for packages, services, SSH, sysctl, kubelet files, or audit rules.
- [ ] You can identify the Kubernetes networking settings that must remain enabled and the unsafe network behaviors that should remain disabled.
- [ ] You can connect each secure Pod setting in the lab to a kernel-facing risk reduction.
- [ ] You can describe where each hardening change should live so it survives reboot, autoscaling, and node replacement.

---

## Sources

- [Kubernetes documentation: Linux kernel security constraints for Pods and containers](https://kubernetes.io/docs/concepts/security/linux-kernel-security-constraints/)
- [Kubernetes documentation: Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes documentation: Configure a Security Context for a Pod or Container](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [Kubernetes documentation: Restrict a Container's Syscalls with seccomp](https://kubernetes.io/docs/tutorials/security/seccomp/)
- [Kubernetes documentation: Debug Running Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/)
- [Kubernetes documentation: Debug Kubernetes Nodes with crictl](https://kubernetes.io/docs/tasks/debug/debug-cluster/crictl/)
- [Linux kernel documentation: sysctl kernel parameters](https://www.kernel.org/doc/html/latest/admin-guide/sysctl/kernel.html)
- [Linux kernel documentation: IP sysctl settings](https://www.kernel.org/doc/html/latest/networking/ip-sysctl.html)
- [Kernel project homepage](https://www.kernel.org/)
- [containerd documentation: configuration](https://github.com/containerd/containerd/blob/main/docs/man/containerd-config.toml.5.md)
- [Open Container Initiative runtime specification: Linux configuration](https://github.com/opencontainers/runtime-spec/blob/main/config-linux.md)
- [Docker documentation: Docker Engine security](https://docs.docker.com/engine/security/)
- [CISA and NSA Kubernetes Hardening Guidance](https://www.cisa.gov/resources-tools/resources/kubernetes-hardening-guidance)

---

## Next Module

[Module 3.4: Network Security](../module-3.4-network-security/) - Host-level network hardening.
