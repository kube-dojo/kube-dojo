---
title: "Module 2.3: Immutable OS for Kubernetes"
slug: on-premises/provisioning/module-2.3-immutable-os
sidebar:
  order: 4
---

> **Complexity**: `[MEDIUM]` | Time: 45 minutes
>
> **Prerequisites**: [Module 2.2: OS Provisioning & PXE Boot](../module-2.2-pxe-provisioning/), [K8s Distributions](../../platform/toolkits/infrastructure-networking/k8s-distributions/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** immutable OS options (Talos, Flatcar, Bottlerocket) against traditional Linux distributions for Kubernetes node hosting
2. **Implement** an immutable OS deployment pipeline that produces identical, reproducible node images
3. **Design** an image update strategy with atomic rollouts and rollback capabilities across bare-metal fleets
4. **Diagnose** configuration drift issues in mutable environments and implement immutable alternatives that prevent recurrence

---

## Why This Module Matters

In May 2023, a manufacturing company running Kubernetes on Ubuntu 22.04 across 80 bare metal nodes discovered that 23 of their nodes had diverged from the expected state. Over 14 months, engineers had SSH'd into nodes to debug issues and made "temporary" changes: installing tcpdump here, modifying a sysctl there, adding a cron job on another. Some nodes had different kernel versions because an engineer had manually run `apt upgrade` on a subset. Three nodes had leftover debugging containers that consumed 4GB of RAM each. Two nodes had modified iptables rules that broke pod networking for certain CIDR ranges.

The platform team spent 3 weeks auditing all 80 nodes, found 47 undocumented changes, and rebuilt 23 nodes from scratch. The postmortem identified the root cause: **mutable infrastructure.** When any engineer can SSH into a node and change anything, configuration drift is inevitable. It is not a question of discipline — it is a property of the system.

Immutable operating systems solve this by making the root filesystem read-only. You cannot SSH in and `apt install` something. You cannot edit `/etc/sysctl.conf`. You cannot add cron jobs. The entire OS is a single image that is deployed atomically and replaced atomically. If you need a change, you build a new image and roll it out.

> **The Printer Cartridge Analogy**
>
> A mutable OS is like a refillable ink cartridge — you can add more ink, change the color, clean the nozzle, but eventually it gets messy and inconsistent. An immutable OS is like a sealed cartridge — when it runs out, you replace the entire unit. It is always in a known state. You never debug "why is this cartridge printing blue instead of black" because every cartridge from the factory is identical.

---

## What You'll Learn

- Why immutable OS matters more on bare metal than in cloud
- Talos Linux: Kubernetes-native, API-driven, no SSH
- Flatcar Container Linux: CoreOS successor, systemd-based
- Red Hat CoreOS (RHCOS): OpenShift's immutable foundation
- How to choose between them
- Upgrade strategies for immutable OS on bare metal

---

## Why Immutable Matters More on Bare Metal

In the cloud, you can terminate and recreate instances. Configuration drift is less dangerous because you can destroy the drifted instance and launch a fresh one in minutes. On bare metal, reprovisioning means PXE booting, waiting for OS installation, and rejoining the cluster — a 15-30 minute process that requires network infrastructure (DHCP, TFTP).

Immutable OS on bare metal gives you:

```
┌─────────────────────────────────────────────────────────────┐
│          MUTABLE vs IMMUTABLE ON BARE METAL                  │
│                                                               │
│  MUTABLE (Ubuntu, RHEL)         IMMUTABLE (Talos, Flatcar)  │
│  ────────────────────           ──────────────────────────   │
│  ✗ SSH access = drift risk     ✓ No SSH (Talos) or limited  │
│  ✗ apt/yum = untracked pkgs   ✓ Read-only rootfs            │
│  ✗ Config files editable       ✓ Config via API/ignition     │
│  ✗ Manual kernel updates       ✓ Atomic OS upgrades          │
│  ✗ Node identity unclear       ✓ Node = disposable image     │
│  ✗ Security: large attack      ✓ Minimal surface (no pkg    │
│    surface (systemd, cron,     │  manager, no shell, no      │
│    sshd, package manager)      │  cron, minimal userspace)   │
│                                                               │
│  On cloud: you can destroy and recreate easily              │
│  On bare metal: reprovisioning is slow and expensive        │
│  → Immutable prevents the need to reprovision               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Talos Linux

Talos Linux is purpose-built for Kubernetes. There is no SSH, no shell, no package manager. The entire OS is managed via a gRPC API.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TALOS LINUX                                │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Kernel (Linux 6.x, minimal config)                  │   │
│  │  └── Only modules needed for K8s + hardware drivers  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  machined (PID 1, replaces systemd)                  │   │
│  │  ├── apid (gRPC API for management)                  │   │
│  │  ├── trustd (certificate management)                 │   │
│  │  ├── networkd (network configuration)                │   │
│  │  └── containerd (container runtime)                  │   │
│  │       ├── kubelet                                     │   │
│  │       ├── etcd (control plane nodes)                 │   │
│  │       └── kube-apiserver, etc.                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  No SSH. No shell. No package manager. No cron.             │
│  Everything is managed via talosctl (CLI) or API.           │
│                                                               │
│  Root filesystem: SquashFS (read-only, compressed)          │
│  Ephemeral data: /var (writable, reset on upgrade)          │
│  Persistent data: /system/state (survives upgrades)         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

> **Stop and think**: An engineer on your team says "I need SSH access to debug networking issues on the nodes." With Talos Linux, SSH does not exist. Before reading the operations below, think about how you would debug a networking problem on a node with no shell access. What tools or approaches would you use?

### Talos Key Operations

Every operation below is performed through the Talos gRPC API via `talosctl`, not SSH. This is a fundamental paradigm shift -- instead of connecting to a node and running commands, you send API requests from your workstation. The API enforces what operations are allowed, creating an auditable, reproducible management model:

```bash
# Install talosctl
curl -sL https://talos.dev/install | sh

# Generate cluster configuration
talosctl gen config my-cluster https://10.0.1.10:6443 \
  --output _out

# Apply config to a node (via API, not SSH)
talosctl apply-config --insecure \
  --nodes 10.0.1.10 \
  --file _out/controlplane.yaml

# Bootstrap the cluster (first control plane node)
talosctl bootstrap --nodes 10.0.1.10

# Get kubeconfig
talosctl kubeconfig --nodes 10.0.1.10

# Check node health
talosctl health --nodes 10.0.1.10

# View system logs (no SSH needed)
talosctl logs kubelet --nodes 10.0.1.10

# Upgrade Talos OS (atomic, in-place)
talosctl upgrade --nodes 10.0.1.10 \
  --image ghcr.io/siderolabs/installer:v1.9.0

# Upgrade Kubernetes version
talosctl upgrade-k8s --nodes 10.0.1.10 \
  --to 1.35.0
```

### Talos Machine Configuration

```yaml
# controlplane.yaml (abbreviated)
version: v1alpha1
machine:
  type: controlplane
  token: <generated>
  ca:
    crt: <generated>
    key: <generated>
  network:
    hostname: cp-01
    interfaces:
      - interface: eth0
        addresses:
          - 10.0.1.10/24
        routes:
          - network: 0.0.0.0/0
            gateway: 10.0.1.1
  install:
    disk: /dev/sda
    image: ghcr.io/siderolabs/installer:v1.9.0
  kubelet:
    extraArgs:
      rotate-server-certificates: "true"
  sysctls:
    net.core.somaxconn: "65535"
    net.ipv4.ip_forward: "1"
cluster:
  controlPlane:
    endpoint: https://10.0.1.10:6443
  clusterName: my-cluster
  network:
    podSubnets:
      - 10.244.0.0/16
    serviceSubnets:
      - 10.96.0.0/12
    cni:
      name: cilium
```

---

## Flatcar Container Linux

Flatcar is the community successor to CoreOS Container Linux. It uses systemd and Ignition for configuration, and provides a familiar Linux environment with an immutable root filesystem.

> **Pause and predict**: Your team is split: half want Talos (maximum security, no SSH) and half want Flatcar (familiar Linux, SSH available). The team has 2 engineers with deep Linux experience and 3 with mostly Kubernetes experience. Which would you recommend as a starting point, and what would your migration path look like?

### Flatcar vs Talos

| Feature | Talos Linux | Flatcar Container Linux |
|---------|-------------|------------------------|
| Shell access | None (no SSH, no shell) | SSH available (optional) |
| Init system | machined (custom) | systemd |
| Configuration | Machine config (YAML) | Ignition (JSON) |
| Package manager | None | None (but can run toolbox) |
| Root filesystem | SquashFS (read-only) | dm-verity (read-only) |
| Update mechanism | talosctl upgrade | Nebraska/Omaha (auto-update) |
| K8s integration | Built-in (machined runs kubelet) | External (kubeadm, etc.) |
| Debugging | talosctl logs, talosctl dashboard | SSH + journalctl |
| Learning curve | Higher (new paradigm) | Lower (familiar Linux) |
| Best for | Maximum security, zero-touch ops | Teams that need occasional SSH |

### Flatcar Ignition Configuration

```json
{
  "ignition": { "version": "3.3.0" },
  "storage": {
    "files": [
      {
        "path": "/etc/hostname",
        "contents": { "source": "data:,k8s-worker-01" },
        "mode": 420
      },
      {
        "path": "/etc/sysctl.d/k8s.conf",
        "contents": {
          "source": "data:,net.bridge.bridge-nf-call-iptables%3D1%0Anet.ipv4.ip_forward%3D1"
        },
        "mode": 420
      }
    ]
  },
  "systemd": {
    "units": [
      {
        "name": "containerd.service",
        "enabled": true
      },
      {
        "name": "kubelet.service",
        "enabled": true,
        "contents": "[Unit]\nDescription=kubelet\nAfter=containerd.service\n[Service]\nExecStart=/opt/bin/kubelet ...\nRestart=always\n[Install]\nWantedBy=multi-user.target"
      }
    ]
  },
  "passwd": {
    "users": [
      {
        "name": "core",
        "sshAuthorizedKeys": ["ssh-ed25519 AAAA... admin@kubedojo"]
      }
    ]
  }
}
```

---

## Red Hat CoreOS (RHCOS)

RHCOS is the immutable OS for OpenShift. It is not used standalone — it is tightly coupled with the OpenShift Machine Config Operator (MCO).

| Aspect | Details |
|--------|---------|
| Base | RHEL kernel + rpm-ostree |
| Management | OpenShift MCO (MachineConfig CRDs) |
| Updates | Coordinated with OpenShift cluster upgrades |
| Standalone use | Not supported (OpenShift only) |
| SSH | Available but discouraged (use `oc debug node`) |

If you are running OpenShift, RHCOS is your OS. If you are running vanilla Kubernetes, use Talos or Flatcar.

---

> **Pause and predict**: A defense contractor needs an air-gapped Kubernetes cluster with Secure Boot, no SSH access, and FIPS-compliant cryptography. Which immutable OS would you recommend and why? What if they also need to run legacy applications that require custom kernel modules?

## Choosing the Right Immutable OS

```
┌─────────────────────────────────────────────────────────────┐
│              DECISION TREE                                    │
│                                                               │
│  Running OpenShift?                                          │
│  └── Yes → RHCOS (no choice, it's built in)                │
│  └── No → Continue                                          │
│                                                               │
│  Need maximum security (no SSH, minimal surface)?           │
│  └── Yes → Talos Linux                                      │
│  └── No → Continue                                          │
│                                                               │
│  Team comfortable with no shell access?                     │
│  └── Yes → Talos Linux                                      │
│  └── No → Flatcar Container Linux                           │
│                                                               │
│  Need auto-update mechanism without Cluster API?            │
│  └── Yes → Flatcar (Nebraska/Omaha updates)                │
│  └── No → Either works                                      │
│                                                               │
│  Using Sidero/Metal3 for declarative provisioning?          │
│  └── Yes → Talos (native Sidero integration)               │
│  └── No → Either works                                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Talos Linux has no `/bin/sh`.** There is literally no shell binary on the system. Even if an attacker gains code execution inside a container and escapes to the host, there is no shell to drop into. This is the most extreme form of attack surface reduction in any Linux distribution.

- **Flatcar Container Linux was forked from CoreOS in 2018** when Red Hat acquired CoreOS and discontinued the community edition. Kinvolk (later acquired by Microsoft) maintained the fork. Today it is managed by the Flatcar community and Microsoft contributes regularly.

- **Google's GKE nodes run Container-Optimized OS (COS)**, Google's own immutable Linux distribution. Amazon EKS uses Amazon Linux 2 or Bottlerocket (Amazon's immutable OS). The hyperscalers all converged on immutable OS independently because the benefits are overwhelming at scale.

- **The immutable OS concept dates back to ChromeOS (2011)** and even earlier to Plan 9 from Bell Labs (1992). Kubernetes made it mainstream for servers because containers already provide the application isolation that a full OS traditionally provided.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Choosing Talos without team buy-in | Engineers panic when they cannot SSH | Start with Flatcar, graduate to Talos |
| Not testing upgrades | Atomic upgrade fails and node is bricked | Test upgrades in staging first; always |
| Ignoring BIOS/firmware | Immutable OS does not update BIOS | Separate firmware management process |
| Custom kernel modules | Immutable OS has fixed kernel | Use Talos extensions or Flatcar's custom image builder |
| Mixing mutable and immutable | Two operational models = double complexity | Commit to one approach per environment |
| No rollback plan | Bad OS image = all nodes broken | A/B partition scheme (both Talos and Flatcar support this) |
| Hardcoded IPs in config | Cannot scale or replace nodes | Use DHCP or dynamic config generation |

---

## Quiz

### Question 1
An engineer needs to install `tcpdump` on a Talos Linux node to debug a networking issue. How do they do it?

<details>
<summary>Answer</summary>

**They don't install anything on the node.** Talos has no package manager, no shell, and no SSH. Instead:

1. **Use `talosctl` to capture packets:**
   ```bash
   talosctl pcap --nodes 10.0.1.50 --interface eth0 \
     --output capture.pcap
   ```

2. **Use a debug pod on the node:**
   ```bash
   kubectl debug node/worker-01 -it --image=nicolaka/netshoot
   # Inside the debug pod:
   tcpdump -i eth0 -nn port 6443
   ```

3. **Use `talosctl logs` to examine network-related logs:**
   ```bash
   talosctl logs networkd --nodes 10.0.1.50
   ```

The key insight: you never modify the node OS. You bring your debugging tools to the node via containers, or you use the management API.
</details>

### Question 2
Your Talos cluster upgrade from v1.8.0 to v1.9.0 fails on the third control plane node. The node is stuck in a boot loop. What do you do?

<details>
<summary>Answer</summary>

Talos uses an A/B partition scheme for atomic upgrades:

1. **The old OS image is still on partition A.** The upgrade wrote the new image to partition B. Since the boot failed, Talos's bootloader will automatically fall back to partition A after a configurable number of boot failures.

2. **If automatic rollback does not trigger**, use the BMC to power cycle the node. The A/B fallback should activate.

3. **If the node is truly bricked**, use `talosctl reset` via the API (if the API is still reachable) to wipe and reprovision.

4. **If the API is unreachable**, PXE boot the node with a fresh Talos image and apply the control plane config.

**Prevention:**
- Always upgrade one node at a time
- Verify each node is healthy before upgrading the next
- Test the upgrade in a non-production cluster first
- Ensure BMC access is working (your last resort for bricked nodes)
</details>

### Question 3
Why is an immutable OS more important on bare metal than in the cloud?

<details>
<summary>Answer</summary>

Three reasons:

1. **Reprovisioning cost**: In the cloud, replacing a drifted VM takes 30 seconds (terminate + launch). On bare metal, reprovisioning requires PXE boot, OS installation, and cluster rejoin — 15-30 minutes minimum. Preventing drift is cheaper than fixing it.

2. **Hardware lifetime**: A bare metal server runs for 3-5 years. Over that time, the accumulation of manual changes (configuration drift) is much higher than a cloud VM that is routinely replaced during scaling events or deployments.

3. **No hypervisor isolation**: In the cloud, the hypervisor provides a security boundary between your VM and the host. On bare metal, the OS IS the host. A compromised mutable OS with SSH, package managers, and a full userspace gives attackers much more to work with than an immutable OS with no shell.
</details>

### Question 4
Your organization uses Ansible for server management. Is an immutable OS compatible with Ansible?

<details>
<summary>Answer</summary>

**Partially, depending on the OS:**

- **Talos Linux**: **Not compatible with Ansible.** Talos has no SSH, no Python interpreter, and no shell — Ansible cannot connect to or execute on Talos nodes. All management is done via `talosctl` or the Talos gRPC API. You would use Ansible only to manage the `talosctl` commands from a management node.

- **Flatcar Container Linux**: **Partially compatible.** Flatcar supports SSH and has Python available via the `toolbox` container. Ansible can connect and gather facts, but the read-only root filesystem means you cannot use Ansible to install packages or modify system files in the traditional way. You can manage containerized services and configuration files in writable areas (`/etc`, `/opt`).

- **Transition strategy**: Use Ansible to manage your PXE/provisioning infrastructure and to orchestrate `talosctl` commands. Treat nodes as cattle (replace, don't repair) rather than pets (configure in place).
</details>

---

## Hands-On Exercise: Deploy Talos Linux in Docker

**Task**: Create a minimal Talos Linux cluster using Docker (no bare metal needed).

```bash
# Install talosctl
curl -sL https://talos.dev/install | sh

# Create a local Talos cluster (3 CP + 1 worker in Docker)
talosctl cluster create \
  --name demo \
  --controlplanes 3 \
  --workers 1

# Get the kubeconfig
talosctl kubeconfig --nodes 10.5.0.2

# Verify the cluster
kubectl get nodes
# NAME                     STATUS   ROLES           AGE   VERSION
# demo-controlplane-1      Ready    control-plane   2m    v1.35.0
# demo-controlplane-2      Ready    control-plane   2m    v1.35.0
# demo-controlplane-3      Ready    control-plane   2m    v1.35.0
# demo-worker-1            Ready    <none>          2m    v1.35.0

# Try to SSH into a node (this will fail — no SSH on Talos)
ssh root@10.5.0.2
# Connection refused

# Instead, use talosctl for management
talosctl dashboard --nodes 10.5.0.2
# Shows real-time node metrics, logs, services

# View system services
talosctl services --nodes 10.5.0.2

# Cleanup
talosctl cluster destroy --name demo
```

### Success Criteria
- [ ] Talos cluster created with 3 CP + 1 worker
- [ ] kubeconfig retrieved and kubectl works
- [ ] SSH connection attempt fails (as expected)
- [ ] talosctl dashboard shows node status
- [ ] Cluster destroyed cleanly

---

## Next Module

Continue to [Module 2.4: Declarative Bare Metal](../module-2.4-declarative-bare-metal/) to learn how Sidero and Metal3 bring Cluster API to bare metal, enabling GitOps-driven hardware lifecycle management.
