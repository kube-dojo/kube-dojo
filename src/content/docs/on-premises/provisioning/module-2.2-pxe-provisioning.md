---
title: "Module 2.2: OS Provisioning & PXE Boot"
slug: on-premises/provisioning/module-2.2-pxe-provisioning
sidebar:
  order: 3
---

> **Complexity**: `[COMPLEX]` | Time: 60 minutes
>
> **Prerequisites**: [Module 2.1: Datacenter Fundamentals](../module-2.1-datacenter-fundamentals/), [Linux: Kernel Architecture](../../linux/foundations/system-essentials/module-1.1-kernel-architecture/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Implement** a PXE boot infrastructure with DHCP, TFTP, and HTTP servers for automated OS provisioning
2. **Configure** kickstart/preseed/autoinstall files that produce consistent, repeatable node installations
3. **Deploy** bare-metal servers from power-on to Kubernetes-ready state without manual intervention
4. **Troubleshoot** PXE boot failures across DHCP relay, TFTP timeouts, and UEFI/BIOS compatibility issues

---

## Why This Module Matters

When you buy 20 servers, they arrive as blank hardware — no operating system, no configuration, no identity. In the cloud, you click "Launch Instance" and an OS appears in 30 seconds. On-premises, you need to solve the bootstrapping problem: how do you install an OS on 20 servers that have no OS?

You could walk to each server with a USB stick. For 3 servers, this is annoying but workable. For 20, it is a full day of repetitive work. For 200, it is impossible. And every time you need to reprovision a node — after a disk failure, a security incident, or a Kubernetes version change — you would need to do it again.

PXE (Preboot Execution Environment) solves this by booting servers over the network. The server's NIC downloads a boot image from a central server, installs the OS automatically, and the machine is ready to join your Kubernetes cluster — all without anyone touching it.

> **The Vending Machine Analogy**
>
> PXE is like a vending machine for operating systems. The server walks up (boots from network), identifies itself (MAC address), receives its order (DHCP offer + boot image), and gets its product (fully installed OS). The vending machine (PXE server) can serve hundreds of customers simultaneously. Compare this to a human (USB stick) who can only serve one customer at a time.

---

## What You'll Learn

- How PXE boot works (DHCP → TFTP → kernel → installer)
- Setting up a basic PXE server for Ubuntu/RHEL autoinstall
- MAAS (Metal as a Service) for fleet management
- Tinkerbell for cloud-native bare metal provisioning
- How to integrate PXE with Kubernetes cluster bootstrapping

---

## How PXE Boot Works

### The Boot Sequence

```
┌─────────────────────────────────────────────────────────────┐
│                  PXE BOOT SEQUENCE                           │
│                                                               │
│  1. Server powers on (via BMC or button)                    │
│     └── BIOS/UEFI starts POST (Power-On Self-Test)         │
│                                                               │
│  2. BIOS tries boot devices in order:                       │
│     └── PXE Network Boot (configured in BIOS boot order)    │
│                                                               │
│  3. NIC broadcasts DHCP Discover                            │
│     └── "I need an IP address and a boot file"              │
│                                                               │
│  4. DHCP server responds with:                              │
│     ├── IP address (10.0.1.50)                              │
│     ├── Gateway, DNS                                        │
│     └── Next-server: 10.0.1.1 (TFTP server)                │
│         Filename: pxelinux.0 (boot loader)                  │
│                                                               │
│  5. NIC downloads boot loader via TFTP                      │
│     └── pxelinux.0 or grubx64.efi (for UEFI)              │
│                                                               │
│  6. Boot loader downloads kernel + initrd                   │
│     └── vmlinuz + initrd.img via TFTP or HTTP               │
│                                                               │
│  7. Kernel starts, runs installer (autoinstall/kickstart)   │
│     └── Downloads packages from HTTP repo                    │
│     └── Partitions disks, installs OS                       │
│     └── Runs post-install scripts (join K8s cluster)        │
│                                                               │
│  8. Server reboots into installed OS                        │
│     └── Ready for kubeadm join or Cluster API enrollment    │
│                                                               │
│  Total time: 5-15 minutes per server (parallel)             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### UEFI vs Legacy BIOS PXE

| Aspect | Legacy BIOS PXE | UEFI PXE |
|--------|----------------|----------|
| Boot loader | `pxelinux.0` (SYSLINUX) | `grubx64.efi` or `shimx64.efi` |
| Protocol | TFTP only | TFTP or HTTP (faster) |
| Secure Boot | Not supported | Supported (recommended) |
| Disk support | MBR (2TB limit) | GPT (no size limit) |
| Status | Legacy, being phased out | Current standard |

**All modern servers use UEFI.** If your servers support it (all enterprise servers from 2015+ do), use UEFI PXE. It supports Secure Boot, larger disks, and HTTP boot (faster than TFTP).

---

## Setting Up a Basic PXE Server

### Components Needed

```
┌─────────────────────────────────────────────────────────────┐
│              PXE SERVER COMPONENTS                           │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  DHCP    │  │  TFTP    │  │  HTTP    │  │ Autoinstall│   │
│  │  Server  │  │  Server  │  │  Server  │  │  Config   │   │
│  │          │  │          │  │          │  │           │   │
│  │ Assigns  │  │ Serves   │  │ Serves   │  │ Answers   │   │
│  │ IPs +    │  │ boot     │  │ OS repo  │  │ all       │   │
│  │ boot     │  │ loader   │  │ packages │  │ installer │   │
│  │ filename │  │ + kernel │  │          │  │ questions │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                               │
│  Can be one server or split across multiple                 │
│  In practice: dnsmasq handles DHCP + TFTP in one process   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

> **Pause and predict**: You have 20 new servers that just arrived in the datacenter. They have no operating system. You need them running Ubuntu with containerd by end of day. If you used USB sticks, how long would it take? What if a server fails next month and needs reprovisioning -- how does PXE change that recovery time?

### Quick PXE Server with dnsmasq

We use dnsmasq rather than separate DHCP and TFTP servers because it handles both protocols in a single lightweight process. This simplifies the PXE infrastructure to a single daemon that manages IP assignment and boot file delivery:

```bash
# Install dnsmasq (handles DHCP + TFTP)
apt-get install dnsmasq

# Create directory structure
mkdir -p /srv/tftp/pxelinux.cfg
mkdir -p /srv/http/ubuntu

# Download Ubuntu 22.04 server ISO and extract
wget https://releases.ubuntu.com/22.04/ubuntu-22.04-live-server-amd64.iso
mount -o loop ubuntu-22.04-live-server-amd64.iso /mnt
cp -r /mnt/* /srv/http/ubuntu/
umount /mnt

# Copy UEFI boot files
cp /srv/http/ubuntu/casper/vmlinuz /srv/tftp/
cp /srv/http/ubuntu/casper/initrd /srv/tftp/

# Configure dnsmasq
cat > /etc/dnsmasq.d/pxe.conf << 'EOF'
# DHCP range for PXE clients
dhcp-range=10.0.1.50,10.0.1.150,255.255.255.0,1h

# PXE boot options
dhcp-boot=grubx64.efi
enable-tftp
tftp-root=/srv/tftp

# UEFI-specific boot
dhcp-match=set:efi-x86_64,option:client-arch,7
dhcp-boot=tag:efi-x86_64,grubx64.efi
EOF

systemctl restart dnsmasq
```

> **Stop and think**: The dnsmasq configuration above responds to any DHCP request on the PXE network with a boot image. What would happen if a production server accidentally rebooted with PXE as its first boot device? How would you prevent this?

### Ubuntu Autoinstall Configuration

The autoinstall file below answers every question the Ubuntu installer would normally ask interactively. This is what makes the installation fully hands-off -- from disk partitioning to user creation to Kubernetes prerequisite packages. The `late-commands` section runs after the OS is installed and configures the kernel modules and sysctl settings that Kubernetes requires:

```yaml
# /srv/http/autoinstall/user-data
#cloud-config
autoinstall:
  version: 1
  locale: en_US.UTF-8
  keyboard:
    layout: us

  # Network: DHCP on first interface
  network:
    version: 2
    ethernets:
      id0:
        match:
          name: en*
        dhcp4: true

  # Storage: entire first disk
  storage:
    layout:
      name: lvm
      sizing-policy: all

  # Users
  identity:
    hostname: k8s-node
    username: kubedojo
    # password: "changeme" (hashed)
    password: "$6$rounds=4096$xyz$..."

  # SSH
  ssh:
    install-server: true
    authorized-keys:
      - ssh-ed25519 AAAA... admin@kubedojo

  # Packages for Kubernetes
  packages:
    - containerd
    - apt-transport-https
    - curl

  # Post-install: prepare for K8s
  late-commands:
    - |
      cat > /target/etc/modules-load.d/k8s.conf << 'MODULES'
      overlay
      br_netfilter
      MODULES
    - |
      cat > /target/etc/sysctl.d/k8s.conf << 'SYSCTL'
      net.bridge.bridge-nf-call-iptables = 1
      net.bridge.bridge-nf-call-ip6tables = 1
      net.ipv4.ip_forward = 1
      SYSCTL
    # Disable swap
    - curtin in-target -- swapoff -a
    - curtin in-target -- sed -i '/swap/d' /etc/fstab
```

---

## MAAS (Metal as a Service)

MAAS by Canonical provides a full lifecycle management platform for bare metal:

```
┌─────────────────────────────────────────────────────────────┐
│                    MAAS ARCHITECTURE                         │
│                                                               │
│  ┌──────────────────────────────────────┐                   │
│  │           MAAS Region Controller      │                   │
│  │  ┌──────────┐  ┌──────────┐          │                   │
│  │  │ REST API │  │ Web UI   │          │                   │
│  │  └──────────┘  └──────────┘          │                   │
│  │  ┌──────────┐  ┌──────────┐          │                   │
│  │  │PostgreSQL│  │  Image   │          │                   │
│  │  │  (state) │  │  Store   │          │                   │
│  │  └──────────┘  └──────────┘          │                   │
│  └───────────────────┬──────────────────┘                   │
│                      │                                       │
│  ┌───────────────────▼──────────────────┐                   │
│  │        MAAS Rack Controller           │                   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐         │                   │
│  │  │ DHCP │ │ TFTP │ │ HTTP │         │                   │
│  │  └──────┘ └──────┘ └──────┘         │                   │
│  │  ┌──────┐ ┌──────┐                  │                   │
│  │  │ DNS  │ │ Proxy│                  │                   │
│  │  └──────┘ └──────┘                  │                   │
│  └───────────────────┬──────────────────┘                   │
│                      │                                       │
│  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐                  │
│  │Server │ │Server │ │Server │ │Server │                  │
│  │  01   │ │  02   │ │  03   │ │  04   │                  │
│  └───────┘ └───────┘ └───────┘ └───────┘                  │
│                                                               │
│  Machine States:                                             │
│  New → Commissioning → Ready → Deploying → Deployed         │
│                                    ↓                         │
│                               Releasing → Ready (recycled)  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### MAAS Key Features

| Feature | Description |
|---------|-------------|
| **Discovery** | Automatically detects new servers via DHCP |
| **Commissioning** | Inventories hardware (CPU, RAM, disks, NICs) |
| **Deployment** | Installs Ubuntu, CentOS, RHEL, or custom images |
| **Networking** | Manages VLANs, bonds, bridges, DNS |
| **Storage** | LVM, RAID, bcache configuration |
| **API** | Full REST API for automation |
| **Juju integration** | Deploy applications via Juju charms |

```bash
# Install MAAS (snap)
sudo snap install maas --channel=3.4

# Initialize
sudo maas init region+rack \
  --database-uri "postgres://maas:password@localhost/maas"

# Create admin user
sudo maas createadmin \
  --username admin \
  --password secure-password \
  --email admin@kubedojo.local

# Access web UI: http://maas-server:5240/MAAS/
```

---

## Tinkerbell: Cloud-Native Bare Metal

Tinkerbell is a CNCF project for declarative bare metal provisioning — it treats hardware like Kubernetes treats pods:

```
┌─────────────────────────────────────────────────────────────┐
│               TINKERBELL ARCHITECTURE                        │
│                                                               │
│  ┌──────────────────────────────────────┐                   │
│  │           Tinkerbell Stack            │                   │
│  │                                       │                   │
│  │  ┌──────────┐  Workflow engine       │                   │
│  │  │  Tink    │  Defines provisioning  │                   │
│  │  │  Server  │  steps as containers   │                   │
│  │  └──────────┘                        │                   │
│  │  ┌──────────┐  DHCP + PXE + OSIE    │                   │
│  │  │  Boots   │  Handles network boot  │                   │
│  │  └──────────┘                        │                   │
│  │  ┌──────────┐  Object storage       │                   │
│  │  │  Hegel   │  Metadata service     │                   │
│  │  └──────────┘  (like cloud metadata) │                   │
│  └──────────────────────────────────────┘                   │
│                                                               │
│  Provisioning defined as Kubernetes CRDs:                   │
│  - Hardware: describes physical machine                      │
│  - Template: defines provisioning steps                      │
│  - Workflow: links Hardware to Template                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

> **Pause and predict**: Tinkerbell defines provisioning steps as container actions. How does this differ from a traditional kickstart/autoinstall approach? What advantage does containerized provisioning give you for reproducibility and testing?

### Tinkerbell Workflow Example

The Tinkerbell workflow below shows the declarative approach to provisioning. Each action is a container image that performs one step -- streaming the OS image, writing configuration files, or setting up networking. Because these are standard OCI containers, you can test and version them independently:

```yaml
# Hardware definition (like a cloud instance profile)
apiVersion: tinkerbell.org/v1alpha1
kind: Hardware
metadata:
  name: worker-01
spec:
  disks:
    - device: /dev/sda
  metadata:
    facility:
      plan_slug: "c3.small.x86"
    instance:
      hostname: k8s-worker-01
      operating_system:
        slug: ubuntu_22_04
  interfaces:
    - dhcp:
        mac: "aa:bb:cc:dd:ee:01"
        ip:
          address: 10.0.1.51
          netmask: 255.255.255.0
          gateway: 10.0.1.1
---
# Template (provisioning steps as container actions)
apiVersion: tinkerbell.org/v1alpha1
kind: Template
metadata:
  name: ubuntu-k8s
spec:
  data: |
    version: "0.1"
    name: ubuntu-k8s-install
    global_timeout: 1800
    tasks:
      - name: os-installation
        worker: "{{.device_1}}"
        actions:
          - name: stream-ubuntu-image
            image: quay.io/tinkerbell-actions/image2disk:v1.0.0
            timeout: 600
            environment:
              IMG_URL: http://10.0.1.1/images/ubuntu-22.04.raw.gz
              DEST_DISK: /dev/sda
              COMPRESSED: true
          - name: install-containerd
            image: quay.io/tinkerbell-actions/writefile:v1.0.0
            timeout: 90
            environment:
              DEST_DISK: /dev/sda1
              DEST_PATH: /etc/modules-load.d/k8s.conf
              CONTENTS: |
                overlay
                br_netfilter
          - name: configure-network
            image: quay.io/tinkerbell-actions/writefile:v1.0.0
            timeout: 90
            environment:
              DEST_DISK: /dev/sda1
              DEST_PATH: /etc/netplan/01-netcfg.yaml
              CONTENTS: |
                network:
                  version: 2
                  ethernets:
                    eno1:
                      addresses: [10.0.1.51/24]
                      gateway4: 10.0.1.1
                      nameservers:
                        addresses: [10.0.1.1]
---
# Workflow (connects hardware to template)
apiVersion: tinkerbell.org/v1alpha1
kind: Workflow
metadata:
  name: provision-worker-01
spec:
  templateRef: ubuntu-k8s
  hardwareRef: worker-01
```

---

## Did You Know?

- **PXE was invented by Intel in 1999** as part of the Wired for Management specification. Over 25 years later, it remains the standard way to network-boot servers. The protocol has barely changed — it still uses TFTP, a protocol from 1981.

- **MAAS manages over 1 million machines worldwide** according to Canonical. It was originally built for Ubuntu's own infrastructure and later open-sourced. The largest known MAAS deployment manages 30,000+ servers.

- **HTTP Boot (UEFI)** is replacing TFTP for PXE. UEFI firmware can download boot files via HTTP instead of TFTP, which is significantly faster (HTTP supports parallel downloads and larger block sizes). Most servers from 2020+ support HTTP Boot.

- **Tinkerbell was created by Equinix Metal** (formerly Packet) to manage their bare metal cloud fleet. It is now a CNCF Sandbox project and is used by Spectro Cloud, Platform9, and other bare metal Kubernetes providers.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| PXE on production VLAN | Any new server auto-installs, destroying data | Isolate PXE DHCP to a dedicated provisioning VLAN |
| No DHCP relay | Servers in other VLANs cannot PXE boot | Configure DHCP relay (ip helper-address) on switches |
| TFTP through firewall | TFTP uses random UDP ports; firewalls block it | Use HTTP Boot or configure firewall for TFTP passive mode |
| Static autoinstall | Every server gets identical config | Template with MAC-based customization (hostname, IP, role) |
| No post-install validation | Server installs but has wrong config | Add verification step (check containerd, sysctl, hostname) |
| Skipping Secure Boot | Anyone can PXE boot malicious images | Enable UEFI Secure Boot with signed boot chain |
| Manual BIOS config | Each server has different BIOS settings | Use Redfish API to configure BIOS programmatically |
| Not backing up PXE server | PXE server dies = cannot provision new nodes | Replicate PXE config via Git; have a standby PXE server |

---

## Quiz

### Question 1
A server is PXE booting but hangs at "Waiting for DHCP..." for 60 seconds. What are the most likely causes?

<details>
<summary>Answer</summary>

In order of likelihood:

1. **DHCP server not running** or not configured for the PXE VLAN. Check `systemctl status dnsmasq` and verify the DHCP range covers the server's subnet.

2. **VLAN mismatch**: The server's port is in a different VLAN than the DHCP server. Check the switch port VLAN assignment and ensure DHCP relay is configured if they are on different VLANs.

3. **Firewall blocking DHCP**: UDP ports 67/68 must be open between the server and the DHCP server.

4. **DHCP range exhausted**: All IPs in the range are leased. Check `cat /var/lib/misc/dnsmasq.leases` for active leases.

5. **NIC boot order**: The server is trying to PXE boot from the wrong NIC (e.g., the BMC NIC instead of the production NIC). Check BIOS boot order.

Debug:
```bash
# On the DHCP server, watch for DHCP requests:
tcpdump -i eth0 -n port 67 or port 68
# You should see DHCPDISCOVER from the server's MAC
```
</details>

### Question 2
Why should PXE provisioning use a dedicated VLAN instead of the production network?

<details>
<summary>Answer</summary>

**Safety and security:**

1. **Accidental reimaging**: If a production server reboots and its BIOS has PXE as the first boot device, it will DHCP discover and potentially start a fresh OS install — wiping the existing OS and all data. A dedicated provisioning VLAN prevents this because production servers are not on the PXE VLAN.

2. **DHCP conflicts**: PXE requires a DHCP server with `next-server` and `filename` options. Running this on the production VLAN risks conflicting with the production DHCP server, causing IP assignment issues for existing infrastructure.

3. **Attack surface**: The PXE server can push arbitrary OS images to any server that PXE boots. An attacker on the PXE VLAN could install a compromised OS on any server that reboots with PXE enabled.

**Best practice**:
- Provisioning VLAN (e.g., VLAN 100) — only new/reprovisioning servers
- Production VLAN (e.g., VLAN 200) — running K8s nodes
- After OS installation, the server's network config switches to the production VLAN
</details>

### Question 3
Compare MAAS and Tinkerbell. When would you choose each?

<details>
<summary>Answer</summary>

**MAAS**:
- Full lifecycle management with Web UI
- Ubuntu-centric (best for Ubuntu/RHEL)
- Includes networking, DNS, DHCP, storage management
- PostgreSQL backend, monolithic architecture
- Best for: organizations standardizing on Ubuntu, teams that want a GUI, environments where MAAS manages the full network stack

**Tinkerbell**:
- Kubernetes-native (CRD-based, declarative)
- OS-agnostic (streams raw disk images)
- Lightweight, microservices architecture
- Integrates with Cluster API (Sidero/Metal3)
- Best for: GitOps-driven environments, teams already running Kubernetes, integration with Cluster API for declarative cluster lifecycle

**Decision guide**:
- If you want a "cloud-like" bare metal experience with a UI → MAAS
- If you want declarative, Kubernetes-native provisioning → Tinkerbell
- If you are using Cluster API for cluster lifecycle → Tinkerbell + Sidero
</details>

### Question 4
Your organization requires Secure Boot for all production servers. How does this affect PXE provisioning?

<details>
<summary>Answer</summary>

With Secure Boot enabled, the UEFI firmware verifies the cryptographic signature of every boot component. Only signed code can execute:

1. **Boot loader must be signed**: Use `shimx64.efi` (signed by Microsoft's UEFI CA) which then loads `grubx64.efi` (signed by your distribution's key).

2. **Kernel must be signed**: Ubuntu and RHEL ship signed kernels. Custom kernels must be enrolled in the Secure Boot database (MOK — Machine Owner Key).

3. **initrd is not signed** but is loaded by the signed kernel, which verifies it.

4. **TFTP path changes**: Instead of `pxelinux.0` (unsigned BIOS loader), use `shimx64.efi` → `grubx64.efi` → signed kernel.

**Impact on provisioning**:
- Cannot boot unsigned custom images
- Must use distribution-provided boot chain
- Custom kernels require MOK enrollment (manual step per server, or automated via `mokutil`)
- Increases security but adds complexity to the boot chain

For Talos Linux and Flatcar (covered in Module 2.3), both provide Secure Boot-compatible images.
</details>

---

## Hands-On Exercise: PXE Boot a Virtual Machine

**Task**: Set up a minimal PXE server and boot a VM from it.

> **Note**: This exercise uses QEMU/KVM to simulate a PXE-booting bare metal server. No physical hardware required.

### Steps

1. **Create the PXE server** (Ubuntu host):

```bash
# Install dependencies
sudo apt-get install -y dnsmasq nginx qemu-kvm

# Create TFTP directory
sudo mkdir -p /srv/tftp

# Download Ubuntu 22.04 Live Server ISO and extract boot files
# Note: Canonical removed debian-installer netboot images after 20.04.
# Extract vmlinuz and initrd from the ISO's casper directory instead.
wget https://releases.ubuntu.com/22.04/ubuntu-22.04-live-server-amd64.iso
mkdir -p /mnt/iso
sudo mount -o loop ubuntu-22.04-live-server-amd64.iso /mnt/iso
cp /mnt/iso/casper/vmlinuz /srv/tftp/vmlinuz
cp /mnt/iso/casper/initrd /srv/tftp/initrd
sudo umount /mnt/iso
```

2. **Configure dnsmasq for PXE**:

```bash
cat | sudo tee /etc/dnsmasq.d/pxe.conf << 'EOF'
interface=virbr1
dhcp-range=192.168.100.50,192.168.100.100,255.255.255.0,1h
dhcp-boot=pxelinux.0
enable-tftp
tftp-root=/srv/tftp
EOF

# Create PXE menu
sudo mkdir -p /srv/tftp/pxelinux.cfg
cat | sudo tee /srv/tftp/pxelinux.cfg/default << 'EOF'
DEFAULT install
LABEL install
  KERNEL vmlinuz
  APPEND initrd=initrd
EOF

sudo systemctl restart dnsmasq
```

3. **Boot a VM via PXE**:

```bash
# Create a disk for the VM
qemu-img create -f qcow2 /tmp/pxe-test.qcow2 20G

# Boot VM with PXE (network boot)
qemu-system-x86_64 \
  -m 2048 \
  -boot n \
  -net nic \
  -net bridge,br=virbr1 \
  -drive file=/tmp/pxe-test.qcow2,format=qcow2 \
  -nographic
```

4. **Watch the PXE boot process**: You should see DHCP discovery, TFTP download, and the Ubuntu installer starting.

### Success Criteria
- [ ] dnsmasq running with DHCP + TFTP
- [ ] VM successfully PXE boots from network
- [ ] DHCP lease visible in dnsmasq logs
- [ ] TFTP transfer visible (boot loader download)
- [ ] OS installer starts automatically

---

## Next Module

Continue to [Module 2.3: Immutable OS for Kubernetes](../module-2.3-immutable-os/) to learn why Talos Linux and Flatcar Container Linux are better choices than traditional distributions for bare metal Kubernetes.
