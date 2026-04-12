---
title: "Module 2.2: OS Provisioning & PXE Boot"
slug: on-premises/provisioning/module-2.2-pxe-provisioning
sidebar:
  order: 3
---

> **Complexity**: `[COMPLEX]` | Time: 60 minutes
>
> **Prerequisites**: [Module 2.1: Datacenter Fundamentals](../module-2.1-datacenter-fundamentals/), [Linux: Kernel Architecture](../../linux/foundations/system-essentials/module-1.1-kernel-architecture/)

## Why This Module Matters

In August 2012, Knight Capital Group deployed a new software update to their SMARS high-frequency trading servers. Because the deployment and configuration process involved manual steps instead of an automated, strictly declarative provisioning pipeline, a technician missed one of the eight core servers. The stale code on that single server went rogue, causing erratic trading behavior that resulted in a staggering loss of $460 million in just 45 minutes, leading directly to the subsequent bankruptcy of the firm. 

While Knight Capital's failure manifested at the application layer, the root cause—manual, inconsistent server configuration—plagues infrastructure teams daily. When you purchase 20 bare-metal servers for a Kubernetes cluster, they arrive as completely blank hardware. On-premises, you must solve the fundamental bootstrapping problem: how do you install an operating system on 20 servers that have no OS, ensuring absolute consistency across the entire fleet?

You could walk to each server with a bootable USB stick. For three servers, this is annoying but workable. For 20 servers, it is a full day of repetitive, error-prone work. For 200 servers, it is impossible. Furthermore, every time you need to reprovision a node—after a hardware failure, a security incident, or a major Kubernetes version upgrade—you would need to perform this manual process again. 

PXE (Preboot Execution Environment) solves this fundamental infrastructure challenge by booting servers directly over the network. The server's Network Interface Card (NIC) downloads a boot image from a central provisioning server, automatically installs the operating system, applies declarative configurations, and prepares the machine to join your Kubernetes cluster—all without a single human touching the physical machine.

> **The Vending Machine Analogy**
>
> PXE operates like a vending machine for operating systems. The bare-metal server powers on (boots from the network), identifies itself via its MAC address, receives its specific order (DHCP offer plus a boot image), and receives its product (a fully installed OS). The vending machine (PXE server) can serve hundreds of customers simultaneously, whereas a human operator with a USB stick can only serve one customer at a time.

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Design** a resilient PXE boot infrastructure using DHCP, TFTP, and UEFI HTTP Boot to automate bare-metal OS provisioning.
2. **Implement** unattended installation configurations using cloud-init, autoinstall, or Ignition to bootstrap identical Kubernetes cluster nodes.
3. **Compare** legacy BIOS and UEFI PXE bootloaders, evaluating the security benefits of modern bootloaders like iPXE and Secure Boot integrations.
4. **Evaluate** bare-metal provisioning platforms such as MAAS, Metal3, and Tinkerbell for declarative lifecycle management.
5. **Diagnose** common network boot failures by analyzing DHCP relay misconfigurations, TFTP timeouts, and firmware architecture mismatches.

---

## Core Content 1: The Boot Sequence & PXE Fundamentals

The canonical PXE specification is version 2.1, published by Intel on September 20, 1999; no newer official PXE specification has been published. Despite its age, it remains the backbone of datacenter automation. The traditional PXE boot process relies heavily on a sequence of network protocols working in tandem.

> **Pause and predict**: You have 20 new servers that just arrived in the datacenter. They have no operating system. You need them running Ubuntu with containerd by end of day. If you used USB sticks, how long would it take? What if a server fails next month and needs reprovisioning -- how does PXE change that recovery time?

When a bare-metal server first powers on and attempts to network boot, it broadcasts a DHCP Discover packet. However, a standard DHCP Offer containing just an IP address and a default gateway is insufficient for PXE. The DHCP server must provide specific PXE-related options to guide the bare-metal hardware.

DHCP option 66 (TFTP Server Name) and option 67 (Boot File Name) are used by PXE clients to locate the TFTP server and download the Network Bootstrap Program (NBP). Furthermore, RFC 4578 defines PXE-specific DHCP options including option 93 (Client System Architecture Type), which is used to differentiate BIOS from UEFI clients. This allows the DHCP server to dynamically assign the correct bootloader based on the hardware requesting it.

Once the DHCP lease is acquired, the server must download the bootloader. TFTP is defined by RFC 1350 (published July 1992) and remains the primary transport protocol for the legacy PXE network boot file transfer stage.

### The Network Boot Sequence

*Legacy ASCII representation (preserved for historical reference):*
```text
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
│     ├── IP address (10.0.5.50)                              │
│     ├── Gateway, DNS                                        │
│     └── Next-server: 10.0.5.1 (TFTP server)                │
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

*Modern Architectural View:*
```mermaid
sequenceDiagram
    participant S as Server (BIOS/UEFI)
    participant N as NIC
    participant D as DHCP Server
    participant T as TFTP/HTTP Server
    S->>S: 1. Power on & POST
    S->>N: 2. Try PXE Network Boot
    N->>D: 3. DHCP Discover (Need IP & boot file)
    D-->>N: 4. DHCP Offer (IP: 10.0.5.50, TFTP: 10.0.5.1, File: pxelinux.0)
    N->>T: 5. Download boot loader (TFTP/HTTP)
    T-->>N: pxelinux.0 or grubx64.efi
    N->>T: 6. Download kernel + initrd
    T-->>N: vmlinuz + initrd.img
    N->>S: 7. Start kernel & run installer
    S->>S: Download packages, partition disks
    S->>S: Run post-install scripts
    S->>S: 8. Reboot into installed OS
```

### Essential PXE Server Components

To implement this flow, you need several interconnected services. 

*Legacy ASCII representation:*
```text
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

*Modern Architectural View:*
```mermaid
flowchart TD
    subgraph PXEServer[PXE SERVER COMPONENTS]
        direction LR
        A[DHCP Server<br/>Assigns IPs & boot filename]
        B[TFTP Server<br/>Serves boot loader & kernel]
        C[HTTP Server<br/>Serves OS repo packages]
        D[Autoinstall Config<br/>Answers installer questions]
    end
    note[Can be one server or split across multiple.<br/>In practice: dnsmasq handles DHCP + TFTP in one process.]
    PXEServer --- note
```

### Quick PXE Server with dnsmasq

We use dnsmasq rather than separate DHCP and TFTP servers because it handles both protocols elegantly in a single lightweight process. This simplifies the PXE infrastructure to a single daemon that manages IP assignment and boot file delivery:

```bash
# Install dnsmasq (handles DHCP + TFTP)
sudo apt-get install -y dnsmasq

# Create directory structure
sudo mkdir -p /srv/tftp/pxelinux.cfg
sudo mkdir -p /srv/http/ubuntu

# Download Ubuntu 22.04 server ISO and extract
wget https://releases.ubuntu.com/22.04/ubuntu-22.04-live-server-amd64.iso
sudo mount -o loop ubuntu-22.04-live-server-amd64.iso /mnt
sudo cp -r /mnt/* /srv/http/ubuntu/
sudo umount /mnt

# Copy UEFI boot files
sudo cp /srv/http/ubuntu/casper/vmlinuz /srv/tftp/
sudo cp /srv/http/ubuntu/casper/initrd /srv/tftp/

# Configure dnsmasq
cat | sudo tee /etc/dnsmasq.d/pxe.conf << 'EOF'
# DHCP range for PXE clients
dhcp-range=10.0.5.50,10.0.5.150,255.255.255.0,1h

# PXE boot options
dhcp-boot=grubx64.efi
enable-tftp
tftp-root=/srv/tftp

# UEFI-specific boot
dhcp-match=set:efi-x86_64,option:client-arch,7
dhcp-boot=tag:efi-x86_64,grubx64.efi
EOF

sudo systemctl restart dnsmasq
```

---

## Core Content 2: UEFI vs Legacy BIOS PXE

As physical servers evolved, the limitations of Legacy BIOS became apparent. All enterprise servers from 2015 onwards support UEFI. Legacy BIOS is restricted to MBR partitioning (which has a 2TB limit) and lacks cryptographic verification mechanisms.

The current UEFI specification version is 2.11, released December 17, 2024. UEFI completely overhauls the boot process. One of the most significant changes is how network payloads are delivered. While older servers rely entirely on TFTP, modern UEFI firmware supports HTTP Boot. UEFI HTTP Boot allows firmware to fetch OS images directly from an HTTP server, eliminating the need for TFTP entirely. While secondary sources state that HTTP Boot was introduced in UEFI 2.5, no direct press release from the UEFI forum was retrieved in this research session to independently verify the exact version introduction; however, it remains a standard part of modern UEFI specifications.

It is critical to note that many current firmware implementations of UEFI HTTP Boot support only plain HTTP, not HTTPS, and do not follow HTTP redirects (301/302). You must configure your web servers accordingly.

For bootloaders, PXELINUX (part of the Syslinux project) is the traditional legacy-BIOS NBP; however, the Syslinux project is discontinued with no stable releases since 2019. Modern infrastructure uses GRUB2, which supports network booting for both legacy BIOS systems (core.0) and UEFI systems (core.efi) via the `grub2-mknetdir` command.

| Aspect | Legacy BIOS PXE | UEFI PXE |
|--------|----------------|----------|
| Boot loader | `pxelinux.0` (SYSLINUX) | `grubx64.efi` or `shimx64.efi` |
| Protocol | TFTP only | TFTP or HTTP (faster) |
| Secure Boot | Not supported | Supported (recommended) |
| Disk support | MBR (2TB limit) | GPT (no size limit) |
| Status | Legacy, being phased out | Current standard |

> **War Story: The Legacy Transfer Bottleneck**
> In a massive cluster deployment, an engineering team attempted to PXE boot 500 servers simultaneously. Because they were using legacy TFTP, which operates on a strict stop-and-wait mechanism (acknowledging every 512-byte block before sending the next), the network saturated with acknowledgments. Booting a single 1GB kernel took hours. The immediate mitigation was implementing the TFTP windowsize option (RFC 7440), which was published in January 2015 and substantially improves PXE boot transfer performance by allowing multiple data packets in flight. Eventually, they migrated to UEFI HTTP Boot to leverage TCP's native windowing, dropping the boot time to under two minutes.

---

## Core Content 3: Modern Bootloaders: iPXE and netboot.xyz

Standard firmware PXE implementations are often limited in scope. To gain advanced scripting, protocol support, and cryptographic verification, administrators often chain-load into iPXE. 

The latest stable iPXE release is v2.0.0, released March 6, 2026. This is a monumental release because iPXE v2.0.0 is the first iPXE release to include official UEFI Secure Boot support via a dedicated shim. This allows you to construct a fully trusted, end-to-end verified boot chain without disabling Secure Boot in the physical server's BIOS.

Another excellent tool built on top of iPXE is netboot.xyz. netboot.xyz is an iPXE-based multi-OS network bootloader; its latest release is version 3.0.0 (released January 24, 2026). It provides a dynamic menu system to pull down hundreds of different operating system images directly from the internet, making it fantastic for lab environments.

---

## Core Content 4: Unattended Installation Formats

Once the kernel boots, the operating system installer takes over. Without intervention, it would halt and wait for a human to select a language, partition disks, and set a password. We bypass this using unattended installation files.

1. **Ubuntu Autoinstall:** Ubuntu adopted the autoinstall (Subiquity) YAML format for unattended installs starting with Ubuntu Server 20.04 and Ubuntu Desktop 23.04. Ubuntu autoinstall uses a YAML configuration file passed via a cloud-init datasource or kernel parameter (e.g., `autoinstall ds=nocloud`).
2. **Debian Preseed:** Debian uses the preseed format (debian-installer/d-i) for unattended installation; preseed is actively maintained and not deprecated for Debian as of 2026.
3. **RHEL/Fedora Kickstart:** RHEL and Fedora use the Kickstart format for unattended installation, handled by the pykickstart library and invoked through the Anaconda installer.
4. **Ignition:** Ignition is the first-boot provisioning format for Flatcar Container Linux and Fedora CoreOS; the current specification is version 3.3.0. Note that the current Ignition spec v2.x (last version 2.3.0) is no longer actively developed but remains supported in existing Flatcar and RHCOS deployments.

These tools heavily integrate with cloud-init, which is the industry standard for cloud/bare-metal instance initialisation; its latest stable release is 26.1, released February 27, 2026.

### Ubuntu Autoinstall Configuration Example

The following configuration answers every prompt the Ubuntu installer would normally ask interactively:

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

## Core Content 5: Bare-Metal Provisioning Platforms

Managing DHCP, TFTP, and configuration files manually scales poorly. Enterprise environments utilize orchestrators that act as the control plane for bare metal. These tools often integrate closely with Baseboard Management Controllers (BMCs) using modern API standards. For example, the DMTF Redfish standard for out-of-band hardware management (BMC API) has its latest protocol specification at DSP0266 version 1.23.1 (December 4, 2025), which allows orchestrators to power cycle nodes, mount virtual media, and configure BIOS settings programmatically.

### MAAS (Metal as a Service)

Canonical MAAS (Metal as a Service) is an active bare-metal lifecycle management tool; its latest stable release is version 3.7 (released February 13, 2026). It treats physical servers like cloud instances. It was originally built for Ubuntu's own infrastructure and later open-sourced.

*Legacy ASCII representation:*
```text
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

*Modern Architectural View:*
```mermaid
flowchart TD
    subgraph Region[MAAS Region Controller]
        RAPI[REST API]
        RUI[Web UI]
        RPDB[(PostgreSQL\nstate)]
        RIMG[(Image Store)]
    end
    subgraph Rack[MAAS Rack Controller]
        RDHCP[DHCP]
        RTFTP[TFTP]
        RHTTP[HTTP]
        RDNS[DNS]
        RPRX[Proxy]
    end
    Region --> Rack
    Rack --> S1[Server 01]
    Rack --> S2[Server 02]
    Rack --> S3[Server 03]
    Rack --> S4[Server 04]

    subgraph States[Machine States]
        direction LR
        N[New] --> C[Commissioning] --> R[Ready] --> D[Deploying] --> DP[Deployed]
        DP --> RL[Releasing] --> R
    end
```

| Feature | Description |
|---------|-------------|
| **Discovery** | Automatically detects new servers via DHCP |
| **Commissioning** | Inventories hardware (CPU, RAM, disks, NICs) |
| **Deployment** | Installs Ubuntu, CentOS, RHEL, or custom images |
| **Networking** | Manages VLANs, bonds, bridges, DNS |
| **Storage** | LVM, RAID, bcache configuration |
| **API** | Full REST API for automation |
| **Juju integration** | Deploy applications via Juju charms |

MAAS is incredibly easy to bootstrap on an Ubuntu host:

```bash
# Install MAAS (snap)
sudo snap install maas --channel=3.7

# Initialize
sudo maas init region+rack \
  --database-uri "postgres://maas:password@localhost/maas"

# Create admin user
sudo maas createadmin \
  --username admin \
  --password secure-password \
  --email admin@kubedojo.local

# Access web UI: http://localhost:5240/MAAS/
```

### Tinkerbell, Metal3, and Matchbox

While MAAS relies heavily on a monolithic Postgres database and Ubuntu-centric tooling, the Cloud Native Computing Foundation (CNCF) hosts several alternative orchestrators.

Metal3 (Metal Cubed) is a CNCF Incubating project for Kubernetes-native bare-metal provisioning; it moved from Sandbox to Incubating on August 27, 2025. It integrates tightly with the Cluster API framework.

Tinkerbell is a CNCF Sandbox bare-metal provisioning project originally donated by Equinix Metal (formerly Packet) to manage their bare metal cloud fleet. It remains at Sandbox maturity as of April 2026 and is used by Spectro Cloud, Platform9, and other bare metal Kubernetes providers. The project has undergone significant architectural shifts; its `tink` (workflow engine) repository was archived by the project on December 2, 2025 and is now read-only. 

For immutable operating systems, Matchbox (poseidon/matchbox) is an active bare-metal provisioner that matches machines by MAC/UUID and serves iPXE scripts and Ignition configs specifically designed for Flatcar and Fedora CoreOS clusters.

> **Pause and predict**: Tinkerbell defines provisioning steps as container actions. How does this differ from a traditional kickstart/autoinstall approach? What advantage does containerized provisioning give you for reproducibility and testing?

*Legacy ASCII representation (Tinkerbell):*
```text
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

*Modern Architectural View:*
```mermaid
flowchart TD
    subgraph Stack[Tinkerbell Stack]
        TINK[Tink Server\nWorkflow engine\nDefines steps as containers]
        BOOTS[Boots\nDHCP + PXE + OSIE\nHandles network boot]
        HEGEL[Hegel\nObject storage\nMetadata service]
    end

    subgraph CRDs[Provisioning defined as Kubernetes CRDs]
        H[Hardware: describes physical machine]
        T[Template: defines provisioning steps]
        W[Workflow: links Hardware to Template]
        H --- W
        T --- W
    end
    Stack --- CRDs
```

The Tinkerbell workflow below shows the declarative approach to provisioning. Each action is an OCI container image that performs one specific step—streaming the OS image, writing configuration files, or setting up networking.

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
          address: 10.0.5.51
          netmask: 255.255.255.0
          gateway: 10.0.5.1
```
```yaml
# Template (provisioning steps as container actions)
apiVersion: tinkerbell.org/v1alpha1
kind: Template
metadata:
  name: ubuntu-k8s
spec:
  data: |
    version: "3.0"
    name: ubuntu-k8s-install
    global_timeout: 1800
    tasks:
      - name: os-installation
        worker: "{{.device_1}}"
        actions:
          - name: stream-ubuntu-image
            image: quay.io/tinkerbell-actions/image2disk:v3.0.0
            timeout: 600
            environment:
              IMG_URL: http://10.0.5.1/images/ubuntu-22.04.raw.gz
              DEST_DISK: /dev/sda
              COMPRESSED: true
          - name: install-containerd
            image: quay.io/tinkerbell-actions/writefile:v3.0.0
            timeout: 90
            environment:
              DEST_DISK: /dev/sda1
              DEST_PATH: /etc/modules-load.d/k8s.conf
              CONTENTS: |
                overlay
                br_netfilter
          - name: configure-network
            image: quay.io/tinkerbell-actions/writefile:v3.0.0
            timeout: 90
            environment:
              DEST_DISK: /dev/sda1
              DEST_PATH: /etc/netplan/01-netcfg.yaml
              CONTENTS: |
                network:
                  version: 2
                  ethernets:
                    eno1:
                      addresses: [10.0.5.51/24]
                      gateway4: 10.0.5.1
                      nameservers:
                        addresses: [10.0.5.1]
```
```yaml
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

## Hands-On Exercise: PXE Boot a Virtual Machine

**Task**: Set up a minimal PXE server and boot a virtual machine from it entirely over the network.

> **Note**: This exercise uses QEMU/KVM to simulate a PXE-booting bare metal server. No physical hardware is required to complete this task.

### Step 1: Install Required Dependencies and Prepare Directory Structures

First, we need to install our core routing and virtualization tools. We use `dnsmasq` rather than separate DHCP and TFTP servers because it handles both protocols elegantly in a single lightweight process.

```bash
# Install dependencies
sudo apt-get install -y dnsmasq nginx qemu-kvm

# Create TFTP directory
sudo mkdir -p /srv/tftp

# Download Ubuntu 22.04 Live Server ISO and extract boot files
# Note: Canonical removed debian-installer netboot images after 20.04.
# Extract vmlinuz and initrd from the ISO's casper directory instead.
wget https://releases.ubuntu.com/22.04/ubuntu-22.04.5-live-server-amd64.iso
sudo mkdir -p /mnt/iso
sudo mount -o loop ubuntu-22.04.5-live-server-amd64.iso /mnt/iso
sudo cp /mnt/iso/casper/vmlinuz /srv/tftp/vmlinuz
sudo cp /mnt/iso/casper/initrd /srv/tftp/initrd
sudo umount /mnt/iso

# Install and copy pxelinux bootloader files
sudo apt-get install -y pxelinux syslinux-common
sudo cp /usr/lib/PXELINUX/pxelinux.0 /srv/tftp/
sudo cp /usr/lib/syslinux/modules/bios/ldlinux.c32 /srv/tftp/

# Create bridge interface for QEMU and assign IP for dnsmasq
sudo ip link add name virbr1 type bridge
sudo ip addr add 192.168.100.1/24 dev virbr1
sudo ip link set dev virbr1 up

# Allow QEMU to use the bridge
sudo mkdir -p /etc/qemu
echo "allow virbr1" | sudo tee -a /etc/qemu/bridge.conf
```

**Checkpoint Verification:** Verify that the `virbr1` bridge interface is active and has the correct IP address assigned before continuing:
```bash
ip addr show dev virbr1
```

### Step 2: Configure the dnsmasq Service for Network Booting

> **Stop and think**: The dnsmasq configuration below responds to any DHCP request on the PXE network with a boot image. What would happen if a production server accidentally rebooted with PXE as its first boot device? How would you prevent this?

```bash
# Configure dnsmasq
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

**Checkpoint Verification:** Ensure that the `dnsmasq` service is active and listening before attempting to boot the VM:
```bash
sudo systemctl status dnsmasq --no-pager
```

### Step 3: Execute the Virtual Machine Network Boot

With the backend services running, we will instruct QEMU to launch a virtual machine without any local ISO attached, forcing it to fall back to a network boot.

```bash
# Create a disk for the VM
qemu-img create -f qcow2 /tmp/pxe-test.qcow2 20G

# Boot VM with PXE (network boot)
sudo qemu-system-x86_64 \
  -m 2048 \
  -boot n \
  -net nic \
  -net bridge,br=virbr1 \
  -drive file=/tmp/pxe-test.qcow2,format=qcow2 \
  -nographic
```

### Step 4: Watch the PXE boot process

You should see DHCP discovery, TFTP download, and the Ubuntu installer starting.

### Success Criteria Checklist
- [ ] The `dnsmasq` service is actively running and listening on both DHCP and TFTP ports.
- [ ] The QEMU Virtual Machine successfully initiates a PXE boot sequence over the bridge interface.
- [ ] A new DHCP lease is visibly assigned and logged within the `/var/lib/misc/dnsmasq.leases` file.
- [ ] The TFTP transfer of the `pxelinux.0` (or EFI) boot loader completes successfully.
- [ ] The target operating system installer initiates its automated routine over the network.

---

## Did You Know?

- The canonical PXE specification is version 2.1, published by Intel on September 20, 1999 as part of the Wired for Management specification; remarkably, no newer official PXE spec has ever been published since. The protocol has barely changed — it still uses TFTP, a protocol from 1981.
- The latest stable iPXE release is v2.0.0, released on March 6, 2026, marking the first time the bootloader included official UEFI Secure Boot support via a dedicated shim.
- The TFTP windowsize option (RFC 7440) was published in January 2015 and substantially improves PXE boot transfer performance by allowing multiple data packets in flight over the network.
- Canonical MAAS (Metal as a Service) is an active bare-metal lifecycle management tool; its latest stable release is version 3.7, released on February 13, 2026. MAAS manages over 1 million machines worldwide according to Canonical, with the largest known deployment managing 30,000+ servers.

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
A newly racked physical server is attempting to PXE boot but inexplicably hangs at "Waiting for DHCP..." for 60 seconds before failing. What are the most likely causes?

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
Why is it a critical security and operational requirement to restrict PXE provisioning to a dedicated VLAN rather than exposing it on the production network?

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
Your infrastructure team is evaluating bare-metal orchestrators. Compare the design philosophies of MAAS and Tinkerbell. When would you strategically choose each?

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
Your organization strictly requires UEFI Secure Boot to be enabled for all production servers before they enter the cluster. How does this cryptographic requirement affect your PXE provisioning pipeline?

<details>
<summary>Answer</summary>

With Secure Boot enabled, the UEFI firmware cryptographically verifies the signature of every boot component. Only code signed by a trusted certificate authority can execute:

1. **Boot loader must be signed**: Use `shimx64.efi` (signed by Microsoft's UEFI CA) which then loads `grubx64.efi` (signed by your distribution's key).

2. **Kernel must be signed**: Ubuntu and RHEL ship signed kernels. Custom kernels must be enrolled in the Secure Boot database (MOK — Machine Owner Key).

3. **initrd is not signed** but is loaded by the signed kernel, which verifies it.

4. **TFTP path changes**: Instead of `pxelinux.0` (unsigned BIOS loader), you must use `shimx64.efi` → `grubx64.efi` → signed kernel.

**Impact on provisioning**:
- Cannot boot unsigned custom images.
- Must strictly use the distribution-provided, cryptographically signed boot chain.
- Custom kernels require MOK enrollment, which adds manual intervention overhead unless automated via physical BMC tooling or `mokutil`.
- This substantially increases security but heavily adds complexity to the boot chain.

For Talos Linux and Flatcar (covered in Module 2.3), both provide Secure Boot-compatible signed images out of the box.
</details>

### Question 5
You are configuring a fleet of Fedora CoreOS servers for a Kubernetes cluster using the Matchbox provisioner. The servers successfully pull their initial binaries via iPXE, but the operating system completely fails to apply your declarative configurations upon the first boot. What is the most likely provisioning format mismatch?

<details>
<summary>Answer</summary>

You are likely attempting to use a traditional `cloud-init` or Kickstart format rather than Ignition. Ignition is the strict first-boot provisioning format mandated for Flatcar Container Linux and Fedora CoreOS. The current specification is version 3.3.0. Unlike cloud-init, which typically executes during the late boot process (after the network stack is up), Ignition executes deeply within the initramfs stage before the real root filesystem is fully mounted. This architectural difference makes Ignition ideal for strictly immutable operating systems.
</details>

### Question 6
A major datacenter refresh replaces all legacy physical hardware with modern UEFI systems. Your existing deployment infrastructure relies heavily on `pxelinux.0` and the TFTP protocol. Why will your provisioning pipelines suddenly fail, and what modern equivalents should you architect to resolve this?

<details>
<summary>Answer</summary>

Modern UEFI firmware categorically rejects legacy BIOS bootstrap programs. It requires a UEFI-compatible bootloader such as `grubx64.efi` or a Secure Boot shim (`shimx64.efi`), rather than the legacy `pxelinux.0` (which is part of the discontinued Syslinux project). Furthermore, relying solely on TFTP is outdated and exceptionally slow. Modern UEFI HTTP Boot (introduced in UEFI 2.5) allows the physical firmware to download the bootloader and kernel directly via plain HTTP. This is significantly faster due to larger packet sizes and native TCP windowing. To remediate the failure, you must update DHCP option 67 to point to a valid EFI binary and transition your file hosting from a TFTP root to a standard HTTP web server.
</details>

---

## Next Module

Continue to [Module 2.3: Immutable OS for Kubernetes](../module-2.3-immutable-os/) to learn why Talos Linux and Flatcar Container Linux are fundamentally better architectural choices than traditional distributions for operating bare-metal Kubernetes clusters.