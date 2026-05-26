---
title: "Module 2.2: OS Provisioning & PXE Boot"
slug: on-premises/provisioning/module-2.2-pxe-provisioning
sidebar:
  order: 3
---

> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 80 minutes
>
> **Prerequisites**: [Module 2.1: Datacenter Fundamentals](../module-2.1-datacenter-fundamentals/), [Linux: Kernel Architecture](/linux/foundations/system-essentials/module-1.1-kernel-architecture/)

---

## What You'll Be Able to Do

1. **Design** a PXE boot chain that moves a bare-metal server from firmware to installer without manual console work.
2. **Compare** DHCP-owned PXE, proxyDHCP, TFTP, HTTP Boot, and iPXE chain-loading for real datacenter constraints.
3. **Implement** dynamic iPXE and unattended installer handoff patterns for RHEL, Debian, Ubuntu, SUSE, and first-boot cloud-init.
4. **Diagnose** provisioning failures involving DHCP races, TFTP loss, firmware architecture mismatch, Secure Boot policy, and node identity drift.
5. **Evaluate** how PXE-installed hosts should register into kubeadm, k0s, k3s, Tinkerbell, Metal3, or a later Cluster API workflow.

## Why This Module Matters

Hypothetical scenario: a platform team receives a new rack of bare-metal servers for a Kubernetes 1.35 cluster on Tuesday morning. The hardware is powered, cabled, and reachable through the BMC network from the previous module, but every local disk is blank and every machine has a slightly different firmware default. One engineer suggests installing the first three hosts from USB and cloning the rest after lunch; another suggests waiting until the future declarative bare-metal platform is ready. The hidden problem is that the cluster cannot become reliable while the operating system install path is still a manual ritual.

PXE provisioning is the bridge between physical inventory and repeatable Kubernetes capacity. It takes a server that only knows how to run firmware code, gives it temporary network identity, loads a boot program, downloads a kernel and initramfs, starts an installer, writes an operating system, and hands the machine to first-boot configuration. That chain is not glamorous, but it is where most on-prem fleet drift is either prevented or baked in. If the boot chain gives every worker the same hostname, the same disk layout, or the same stale join token, the cluster failure is created before Kubernetes ever starts.

This module focuses on that boot chain, not on rack design, immutable operating-system philosophy, or full Cluster API reconciliation. Module 2.1 already covered BMCs, power, cabling, and out-of-band control. Module 2.3 will go deeper on Talos, Flatcar, and immutable host models. Module 2.4 will treat Metal3, Sidero-style flows, and Cluster API as the long-running lifecycle control plane. Here, your job is narrower and more foundational: make the first operating-system install deterministic, observable, secure enough for production, and easy to replace later with a stronger orchestrator.

Think of PXE as a loading dock rather than as the finished warehouse. It does not decide your complete platform architecture, but it decides whether every server enters that architecture with a verified identity, a known boot path, and a reproducible base state. A good PXE design lets you rebuild a failed worker during a maintenance window without searching for a USB drive. A bad PXE design turns reboot order, DHCP timing, and firmware quirks into unscheduled change management.

## The PXE Boot Chain as a Contract

PXE starts before Linux exists, before systemd exists, and before any Kubernetes component can help you. The only code running is firmware from the server, the NIC, and whichever UEFI or legacy BIOS path the hardware selected. That means the early boot path must be deliberately simple. Firmware can broadcast for network configuration, download a small boot program, and execute it. Everything else must be staged after that first handoff.

The canonical PXE sequence is easier to reason about if you treat it as a contract between components. The NIC PXE ROM asks for enough network configuration to find a Network Bootstrap Program. DHCP or proxyDHCP answers with an address, a next-server value, and a boot filename or URI. TFTP, HTTP Boot, or iPXE retrieves the boot program. The boot program retrieves a kernel, an initramfs, and command-line arguments. The kernel starts the installer or an in-memory provisioning environment. The installer writes the target OS and prepares the first real boot.

```text
+----------------+       +----------------+       +----------------+
| Firmware / NIC | ----> | DHCP / ProxyDHCP| ----> | Boot Transport |
| PXE or UEFI    |       | IP + boot hint  |       | TFTP or HTTP   |
+----------------+       +----------------+       +----------------+
        |                         |                         |
        v                         v                         v
+----------------+       +----------------+       +----------------+
| Boot Loader    | ----> | Kernel+initramfs| ----> | Installer      |
| iPXE or GRUB   |       | with arguments |       | OS automation  |
+----------------+       +----------------+       +----------------+
                                                          |
                                                          v
                                               +--------------------+
                                               | First real OS boot |
                                               | kubelet joins next |
                                               +--------------------+
```

The important design point is that each stage should know only the minimum needed to reach the next stage. Firmware should not carry per-node Kubernetes policy. DHCP should not contain disk partitioning logic. The boot loader should not become a secret store. The installer should not decide long-term node ownership by reading a spreadsheet. Keeping those boundaries clean makes the boot path easier to test, easier to replace, and easier to audit when a server does the wrong thing.

Legacy PXE normally begins with DHCP and TFTP. DHCP is responsible for network configuration, while TFTP is a small UDP file-transfer protocol used to deliver the boot file. That split survived because early firmware needed a minimal implementation that could fit in NIC ROM. It also creates obvious operational limits: TFTP is simple and widely supported, but it has weak error handling, no authentication, and poor behavior on lossy or high-latency networks unless extensions and server tuning are in place.

Modern UEFI systems add more options. UEFI HTTP Boot can retrieve a boot image by URI instead of using only TFTP, which makes larger boot programs and installer media more practical. Some hardware also supports HTTPS Boot, but you cannot assume consistent TLS behavior across vendors, firmware versions, and Secure Boot policies without testing the exact server model. In production designs, the conservative move is to support the firmware path you know works, chain-load into iPXE when you need richer features, and document the tested firmware matrix.

Pause and predict: if the same server receives a correct IP address but the wrong boot file, which component is probably healthy and which component is suspect? The DHCP address allocation path is likely working, so your next investigation should focus on PXE option selection, architecture detection, boot filename templating, and the transport server that hosts the referenced file.

The boot chain also has a cost surface. A small environment can run DHCP, TFTP, HTTP, and templating on one hardened management VM. A larger environment usually splits those roles for availability, logging, and blast-radius control. The direct cost is modest compared with servers, but the indirect cost of a broken provisioning lane is high: hardware sits idle, failed nodes stay failed longer, and engineers spend maintenance windows debugging firmware rather than replacing capacity.

The safest mental model is to make PXE idempotent. If a machine boots from the network twice, the second boot should not accidentally reinstall a production disk unless the inventory state explicitly says "provision this host." Many teams use BMC one-time boot overrides, per-node allow lists, short-lived workflow state, or an iPXE menu that defaults to local disk after a timeout. Your goal is to make the dangerous action explicit and the boring local-boot path automatic.

That idempotence requirement is what separates a provisioning lane from a rescue menu. A rescue menu is interactive and assumes a human is watching the console. A provisioning lane is unattended and assumes a server may reboot at the least convenient time. If the unattended path can destroy data without current desired state, the design is not production-safe yet.

## DHCP Ownership, ProxyDHCP, and Boot Identity

DHCP is the first trust boundary in most PXE environments because it decides who is allowed to answer a new server and what boot path that server receives. Standard DHCP allocates an address, router, DNS information, lease lifetime, and optional boot fields. PXE adds the need to select the correct boot program for the client's firmware architecture. RFC 4578 defines PXE-oriented DHCP options such as the client system architecture type, which is how a server can distinguish legacy BIOS from x86_64 UEFI.

There are two common ownership models. In a DHCP-owned PXE design, the same DHCP server assigns addresses and supplies boot options. This is simple when the platform team owns the provisioning VLAN and no other DHCP service exists there. In a proxyDHCP design, the existing DHCP server keeps assigning addresses, while a separate PXE-aware service responds only with boot information. That second pattern is common in enterprises where network teams own DHCP and platform teams cannot safely modify production scopes.

```text
DHCP-owned PXE:
  client broadcast -> provisioning DHCP -> IP address + boot file

ProxyDHCP:
  client broadcast -> enterprise DHCP  -> IP address
                   -> PXE proxy        -> boot file only
```

ProxyDHCP is not just a political workaround. It is a risk-control pattern. If the enterprise DHCP service already feeds thousands of clients, changing it to add PXE options can have surprising effects on laptops, appliances, and existing imaging systems. A proxy service can be constrained to a provisioning VLAN, configured to answer only PXE clients, and rolled back without disturbing normal address allocation. The tradeoff is more packet timing complexity and more places where relay configuration can be wrong.

The most common DHCP failure is not a daemon crash; it is an ownership mistake. Two responders answer the same client, the wrong one wins, and the firmware follows whichever offer it accepts first. Because early firmware screens are terse, this looks like random boot behavior even when the network is behaving exactly as configured. Packet captures on the switch span port or provisioning server are more reliable than firmware screenshots because they show every Discover, Offer, Request, ACK, and proxy response.

Identity is the second trust boundary. MAC addresses are convenient because every NIC has one and PXE clients naturally expose them. They are also fragile identifiers because a multi-port server has many MACs, a motherboard replacement changes them, and virtual lab hardware can reuse them accidentally. SMBIOS or DMI system UUIDs are more stable across NIC swaps, but some vendors historically encoded UUID byte order inconsistently, and some lab hypervisors generate duplicates if templates are cloned carelessly.

The practical answer is to use a layered fingerprint. The boot service can key first on a known system UUID when available, fall back to a registered boot MAC, and cross-check asset tag, chassis serial, rack position, and BMC address from inventory. If the signals disagree, serve a quarantine script instead of an installer. That script can print the observed values, report them to the inventory API, and boot local disk or stop, but it should not guess a production role.

Deterministic naming belongs in this same conversation. A hostname such as `worker-12` is only useful if it maps back to an asset, a BMC, a rack unit, and a Kubernetes node lifecycle record. Names based purely on order of arrival create confusion when a failed server is replaced. Names based purely on MAC addresses are difficult for humans to operate. A better pattern is to assign an inventory identity first and derive installer hostname, DNS, labels, and bootstrap role from that record.

Pause and predict: if a server has four physical NICs and PXE boots from the second port, what happens to a design that assumes the first MAC address is the host identity? It may register the host under the wrong inventory record, configure networking for the wrong interface, or generate a hostname that no one expects. That is why the boot MAC should be recorded as one signal, not treated as the whole machine identity.

Here is a minimal dnsmasq-style example that illustrates the difference between direct DHCP ownership and proxy mode. The values are deliberately documentation examples, not a copy-paste production scope. In a real datacenter, the network team should review relay behavior, lease ranges, VLAN boundaries, and whether DHCP options belong in the central service or in a scoped PXE responder.

```ini
# DHCP-owned PXE on an isolated provisioning VLAN.
interface=prov0
bind-interfaces
dhcp-range=10.20.0.50,10.20.0.200,255.255.255.0,30m
dhcp-option=option:router,10.20.0.1
dhcp-option=option:dns-server,10.20.0.10
enable-tftp
tftp-root=/srv/pxe/tftp

# Architecture tags from RFC 4578 option 93.
dhcp-match=set:bios,option:client-arch,0
dhcp-match=set:uefi-x64,option:client-arch,7
dhcp-boot=tag:bios,undionly.kpxe
dhcp-boot=tag:uefi-x64,ipxe.efi
```

```ini
# ProxyDHCP when another service owns address allocation.
interface=prov0
bind-interfaces
dhcp-range=10.20.0.0,proxy,255.255.255.0
enable-tftp
tftp-root=/srv/pxe/tftp
pxe-service=x86PC,"iPXE BIOS",undionly.kpxe
pxe-service=x86-64_EFI,"iPXE UEFI",ipxe.efi
```

Notice the policy difference. The first example allocates addresses and must be isolated from normal client networks. The second example cooperates with another DHCP server and should be tested for race behavior. Neither example embeds Kubernetes secrets, disk choices, or role decisions. Those belong in later dynamic boot scripts and installer configuration where you can template them per registered machine.

For regulated environments, DHCP logs are also audit evidence. They show when a machine requested network boot, which address it received, which boot service responded, and which filename or service class was offered. Those records are not enough to prove a correct installation, but they are enough to reconstruct the early path when an installation starts unexpectedly or fails before Linux logging exists.

## From TFTP to HTTP Boot and iPXE Scripting

TFTP remains useful because firmware support is broad and predictable. It is also the part of PXE that most visibly shows its age. It runs over UDP, has tiny default transfer semantics, and lacks the ergonomics that operators expect from HTTP services: access logs, caching, TLS, redirects, structured error pages, and easy artifact publishing. For a small boot loader, TFTP is fine. For large initramfs images, firmware bundles, or repeated fleet boots, HTTP is usually easier to operate.

UEFI HTTP Boot moves some of that burden into firmware by letting the firmware fetch a URI directly. That can remove TFTP from the first hop on hardware that implements the feature well. The catch is that firmware HTTP clients are not browsers. Some implementations support only a subset of redirects, TLS, DNS behavior, or proxy behavior. A design that boots perfectly on one vendor generation can fail on another because the failing client never reaches your Linux logs.

iPXE is the usual escape hatch because it gives you a programmable boot environment. You can chain-load iPXE from the NIC's PXE ROM or from UEFI HTTP Boot, and then let iPXE retrieve scripts, kernels, initramfs files, and checksums over HTTP or HTTPS. You can also use conditionals, retries, variables, and dynamic script URLs. That does not make the first stage disappear, but it makes the second stage much more controllable.

The chain-loading pattern is intentionally small. Firmware retrieves `undionly.kpxe` for legacy BIOS or `ipxe.efi` for UEFI. iPXE then performs its own network initialization and chains to a script URL. That script can include the observed MAC, UUID, architecture, serial, or asset tag in the query string. The web service can look up the machine in inventory and return a tailored script. Unknown machines receive a safe quarantine response.

```text
Firmware PXE
    |
    | TFTP or UEFI HTTP
    v
iPXE binary
    |
    | HTTP(S) dynamic script request
    v
Inventory-aware boot API
    |
    +--> known control plane: installer kernel + control-plane config
    +--> known worker: installer kernel + worker config
    +--> unknown host: quarantine script, no disk writes
```

The dynamic script should be boring and explicit. It should identify the host, select the kernel and initramfs by architecture, pass only the installer arguments required for that OS, and fail closed if the response is incomplete. It should not contain long-lived bootstrap tokens or private signing keys. If a secret is needed later, deliver it through a short-lived first-boot mechanism tied to inventory state, not as a static query parameter copied into boot logs.

```text
#!ipxe
set boot-api http://10.20.0.10/boot
set host-id ${uuid}
isset ${host-id} || set host-id ${net0/mac}
chain --replace ${boot-api}/script?host=${host-id}&mac=${net0/mac}&arch=${buildarch}
```

A generated script for an Ubuntu worker might then look like this. The server returns concrete kernel paths, a NoCloud seed URL, and an explicit failure mode. It serves kernel and initramfs over HTTP because those files are much larger than the first iPXE binary. The seed URL can be generated per machine and retired after the installer has fetched it.

```text
#!ipxe
set base-url http://10.20.0.10/images/ubuntu-24.04/amd64
kernel ${base-url}/casper/vmlinuz ip=dhcp autoinstall ds=nocloud-net;s=http://10.20.0.10/seed/host-0008/
initrd ${base-url}/casper/initrd
boot || goto failed

:failed
echo Provisioning failed for host-0008
sleep 15
exit
```

For Secure Boot, the problem changes from "can firmware download this binary?" to "will firmware execute this binary?" Secure Boot validates the EFI boot path against trusted keys. A legacy `pxelinux.0` file is not a signed UEFI application. A custom iPXE build is not automatically trusted just because it came from your server. You need a signed shim, a signed GRUB or iPXE path that your firmware trusts, or an organizational key-management process that enrolls the right keys.

There is a useful distinction between transport trust and execution trust. HTTPS can protect the file transfer to iPXE when iPXE is built with HTTPS support and appropriate trust roots. Code signing can verify images downloaded by iPXE when that feature is enabled and used. UEFI Secure Boot verifies the EFI images that firmware and shim are willing to execute. You may need all three, but they solve different problems and fail in different places.

Signed bundles are one way to reduce confusion. Instead of letting a boot script fetch arbitrary kernel and initramfs names, publish a versioned manifest with checksums or signatures, and make the provisioning API return only approved artifact sets. That gives operations a simple rollback handle: `ubuntu-24.04-k8s-2026-05-a` can point to a known kernel, initramfs, installer seed schema, and post-install validation script. When a new hardware generation needs a driver fix, create a new bundle rather than silently changing the old one.

The bundle idea also keeps troubleshooting honest. If host A and host B claim to have installed from the same bundle, they should have used the same kernel, initramfs, repository snapshot, and seed template version. If their behavior differs, you can focus on hardware, firmware, networking, or per-host metadata instead of wondering whether the boot server changed underneath one of them.

## Automating the Installer Without Creating Drift

PXE only gets you to an installer. The installer is where disks are partitioned, packages are selected, users are created, network files are written, and first-boot services are enabled. Each Linux family has its own automation language. RHEL and Fedora use Kickstart through Anaconda. Debian uses preseed with debian-installer. Ubuntu Server uses Subiquity autoinstall, commonly delivered through cloud-init style data. SUSE uses AutoYaST profiles. Cloud-init often runs after the installed OS first boots.

The installer automation file should answer every prompt that would otherwise block an unattended install. It should also do less than many engineers first attempt. The installer is good at disk layout, package sources, base users, network configuration, and handing off a small first-boot service. It is a poor place to encode long cluster policy, mutable application configuration, or multi-node orchestration. A clean design installs the node, proves the node is healthy, and lets Kubernetes or a cluster bootstrap tool take over.

Kickstart is powerful because it combines declarative installation choices with `%pre` and `%post` script hooks. That power needs discipline. A `%post` script can register a system, install a container runtime, write kubelet drop-ins, and fetch a bootstrap artifact. It can also become a hidden configuration-management system that no one tests outside the installer. For production, keep Kickstart short enough to review and run most host preparation from versioned scripts or packages.

```text
# RHEL-style sketch, not a complete production Kickstart.
url --url=http://10.20.0.10/repos/rhel
text
keyboard --xlayouts=us
lang en_US.UTF-8
network --bootproto=dhcp --device=link --activate
rootpw --lock
timezone UTC --utc
zerombr
clearpart --all --initlabel
autopart --type=lvm
reboot

%packages
@^minimal-environment
containerd
curl
%end

%post --log=/root/provision-post.log
curl -fsS http://10.20.0.10/bootstrap/host-0008.sh -o /root/bootstrap.sh
chmod 0700 /root/bootstrap.sh
/root/bootstrap.sh
%end
```

Debian preseed is older and maps to debconf answers. It is excellent when you understand the installer questions, but it can be brittle when a package prompt changes or when you try to configure network details that must exist before the network-loaded preseed file can be fetched. Use it with a known installer version, keep a reference install log, and test that a new ISO still consumes your preseed without falling back to an interactive prompt.

Ubuntu autoinstall is YAML and is validated more explicitly than older preseed flows. That is a major operational benefit because mistakes can fail early instead of pausing at a console. Autoinstall also integrates naturally with NoCloud data sources, which makes per-node seed directories easy to serve from the same HTTP service that generates iPXE scripts. The cost is that YAML structure matters, and changes in installer validation can expose files that were previously accepted with warnings.

```yaml
# user-data served from /seed/host-0008/user-data
#cloud-config
autoinstall:
  version: 1
  locale: en_US.UTF-8
  keyboard:
    layout: us
  identity:
    hostname: worker-0008
    username: bootstrap
    password: "$6$example$replace-this-with-a-real-hash"
  ssh:
    install-server: true
    allow-pw: false
    authorized-keys:
      - ssh-ed25519 YOUR_PUBLIC_KEY_HERE platform@example.com
  storage:
    layout:
      name: lvm
  packages:
    - containerd
    - curl
  late-commands:
    - curtin in-target -- systemctl enable containerd
    - curtin in-target -- mkdir -p /opt/kubedojo
    - curtin in-target -- curl -fsS http://10.20.0.10/bootstrap/host-0008.sh -o /opt/kubedojo/bootstrap.sh
    - curtin in-target -- chmod 0700 /opt/kubedojo/bootstrap.sh
```

AutoYaST fills the same role in SUSE environments. It uses an XML profile that YaST consumes to drive storage, packages, services, users, and post-install actions. The most important design constraint is the same as with Kickstart and autoinstall: profile generation must be deterministic. If a template engine can produce a profile that destroys the wrong disk or assigns the wrong hostname, the provisioning system needs a validation stage before the server ever reboots.

Cloud-init is often misunderstood in bare-metal provisioning because it is not an installer by itself. It runs inside a booted operating system and applies instance data from a datasource. In Ubuntu autoinstall, cloud-init can help deliver the installer configuration. In image-based flows, cloud-init can configure the first real boot of an already written image. Treat it as the first-boot personalization layer, not as a substitute for knowing how the OS image reached the disk.

The most dangerous installer drift comes from shared files that look harmless. A single `user-data` file reused by every host may set the same hostname, reuse the same machine-id, leave the same bootstrap token on disk, or write the same static IP. A single late-command script may install whatever package versions are current today and a different set tomorrow. Pin the OS artifact, the package repository snapshot, the bootstrap script version, and the per-node identity source.

Disk selection deserves special attention because installer automation is allowed to erase storage. Device names such as `/dev/sda` can change when RAID controllers, NVMe drives, USB media, or SAN adapters appear in a different order. Prefer stable hints such as WWN, serial number, controller slot, or a hardware profile generated during commissioning. When no stable hint exists, fail the install instead of guessing.

Before running this in a lab, what output do you expect from a validator that sees an autoinstall file without `identity.hostname`? It should fail before the boot starts. Installer automation is too destructive to trust by inspection alone, so a platform team should lint YAML or XML, check required inventory substitutions, verify URLs, and reject missing hostnames, missing checksum references, ambiguous target disks, and secrets embedded in clear text.

## From Installed Host to Kubernetes Node

After the OS writes to disk and reboots, the provisioning problem changes. The machine is no longer a firmware client; it is a Linux host with an installed network stack, logs, services, and a persistent identity. That is the right time to prepare container runtime settings, kernel modules, sysctl values, kubelet configuration, and a controlled join path. The wrong move is to make the PXE layer pretend it is a full cluster orchestrator.

For kubeadm, the first-boot script usually installs or enables containerd, writes kernel prerequisites, configures the kubelet package, and runs a join command that uses a bootstrap token and discovery hash. Kubernetes bootstrap tokens are Secret objects in `kube-system`, and kubeadm uses them for temporary TLS bootstrap. That token should be short-lived, role-scoped, logged as an issued credential, and rotated or deleted after the node joins.

```bash
#!/usr/bin/env bash
set -euo pipefail

modprobe overlay
modprobe br_netfilter

cat >/etc/modules-load.d/kubernetes.conf <<'MODULES'
overlay
br_netfilter
MODULES

cat >/etc/sysctl.d/99-kubernetes.conf <<'SYSCTL'
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
SYSCTL

sysctl --system
systemctl enable --now containerd

# Retrieve a short-lived join command from a trusted internal endpoint.
curl -fsS http://10.20.0.10/bootstrap/kubeadm/host-0008/join.sh -o /root/kubeadm-join.sh
chmod 0700 /root/kubeadm-join.sh
/root/kubeadm-join.sh
```

k0s and k3s move some of that complexity into their installers and services. k0s can install itself as a system service with controller or worker roles. k3s can persist install-script configuration through environment variables and service arguments. Those simpler paths are attractive for edge and small on-prem clusters, but the same provisioning rules apply: avoid static tokens in boot scripts, pin versions, log what was installed, and make first-boot idempotent.

The node should register with Kubernetes only after the host has proven basic readiness. That readiness check is not the same as a Kubernetes `Ready` condition because the kubelet may not exist yet. Check that the expected disk is mounted, the machine identity file exists, the hostname matches inventory, time synchronization is active, containerd starts, required kernel modules load, and the bootstrap endpoint is reachable. If any of those fail, stop and leave evidence on the node and the provisioning API.

Hardware fingerprinting matters after the join too. Kubernetes nodes are easy to delete and recreate; physical servers are not. A node label such as `node.kubedojo.io/asset=server-0008` or an annotation that references the inventory UUID lets incident responders connect a Kubernetes symptom back to a rack unit, BMC address, disk serial, firmware version, and provisioning record. Without that join, "worker-0008 is NotReady" becomes a hunt through separate systems.

Provisioning systems such as Tinkerbell and Metal3 formalize this handoff. Tinkerbell uses a network-booted in-memory environment and workflow actions to write disks and metadata. Metal3 and its Cluster API provider represent hardware through Kubernetes resources and can provision a user-provided image with checksums and first-boot customization. You do not need those platforms to understand PXE, but PXE literacy makes them less mysterious because they still depend on early network boot and host identity.

Keep the distinction clear: PXE and installer automation create a prepared node; kubeadm, k0s, k3s, or a Cluster API provider creates and maintains cluster membership. When those roles blur, reinstallation becomes the only remediation tool. When those roles are separated, you can reinstall a failed OS, rotate a bootstrap token, drain a Kubernetes node, or return hardware to inventory without rewriting the whole provisioning stack.

A clean handoff also helps incident response. If the node fails before kubelet registration, the provisioning team owns the evidence and should inspect installer logs, seed data, and first-boot scripts. If the node registers and later becomes unhealthy, the Kubernetes operations team owns scheduling, runtime, CNI, and workload evidence. Clear ownership shortens outages because teams stop debating which tool should have fixed which stage.

Cost shows up here as waiting time. If a full reinstall plus node join takes thirty minutes and you have no warm spare capacity, every failed worker consumes cluster redundancy for that long. If a tiny k3s edge node can reinstall in under ten minutes but a GPU worker requires a large driver image and manual Secure Boot enrollment, those are different capacity-recovery budgets. PXE design should feed your maintenance and spare-hardware model, not just your installation checklist.

## Failure Analysis and Secure Boot Operations

PXE failures are frustrating because they happen before normal observability exists. There is no kubelet log, no node exporter, and often no persistent disk log. Your evidence comes from switch counters, DHCP logs, TFTP or HTTP access logs, BMC console capture, firmware event logs, packet captures, and the provisioning API. A good design centralizes those clues so an engineer can answer where the chain stopped without standing in front of a crash cart.

Start with the last known successful stage. If the BMC console shows no link, investigate cabling, VLAN assignment, NIC enablement, and firmware boot order. If DHCP never answers, inspect relay helpers, DHCP scope, proxyDHCP listener binding, and whether the request reached the right VLAN. If the boot file downloads but the kernel fails to load, focus on architecture mismatch, corrupt artifact, Secure Boot rejection, or an initramfs that lacks the required driver.

```text
Symptom                                    Most useful first evidence
----------------------------------------   --------------------------------
No PXE attempt visible                     BMC boot order and NIC link state
DHCP timeout                               Packet capture and relay config
Wrong boot file                            DHCP option 93 and boot filename
TFTP starts then stalls                    TFTP server logs and packet loss
Kernel starts, installer cannot fetch seed HTTP logs and installer console
Reboot loops into installer                Inventory state and boot order
Secure Boot violation                      Firmware event log and key policy
Node installed, never joins Kubernetes     First-boot logs and join token state
```

DHCP races are easiest to miss in shared networks. A PXE client broadcasts, multiple services respond, and the firmware picks one. Sometimes the failure appears only under load because timing changes when many servers reboot together. The disciplined fix is not to add sleeps to boot scripts. It is to isolate the provisioning VLAN, define DHCP ownership, configure relays intentionally, and capture enough packets to prove which responder won.

TFTP failures look different. The client gets an address, asks for the named file, and then the transfer stalls or restarts. This can be packet loss, firewall behavior, MTU mismatch, server root path mistakes, file permissions, or a boot file too large for the firmware's implementation. Moving the large artifacts to HTTP after a small iPXE handoff reduces the pain, but the first handoff must still be tested on the hardware you actually bought.

BIOS versus UEFI mismatch is another classic failure. Legacy BIOS expects a legacy boot program such as an iPXE `undionly` build. UEFI expects a PE/COFF EFI application such as `ipxe.efi`, `grubx64.efi`, or `shimx64.efi`. Serving the wrong one often produces vague firmware errors. RFC 4578 architecture data, DHCP tags, and separate boot filenames are the fix; guessing based on server model names is not.

Secure Boot key management needs an operations plan before the first production install. Ubuntu, RHEL, and other distributions commonly use shim as the first Linux bootloader step trusted by firmware, with distribution keys embedded or validated along the chain. Machine Owner Keys can extend trust for custom modules or binaries, but enrolling them is a privileged action that may require console confirmation or controlled firmware tooling. If your PXE design depends on custom EFI binaries, decide who signs them and how revocation works.

The secure design is not always the most complex design. For many enterprises, the practical path is to use vendor-supported signed shim and GRUB, boot a distribution-signed kernel and initramfs, and keep iPXE only where the organization can support signed binaries and trust roots. If you need custom iPXE with HTTPS and code signing, treat it like production cryptographic software: build reproducibly, store signing keys outside the web server, publish checksums, and test revocation.

Finally, decide how the system fails. Unknown machines should not install. Known machines with identity mismatch should not install. Machines with stale workflow state should not install. Machines that finish installing should be switched back to local disk or marked complete so a later reboot does not wipe them. The failure mode should be visible, logged, and boring, because boring failures are recoverable failures.

The best failure screen is not a clever menu; it is a precise diagnostic. It should print the observed MAC, UUID, architecture, boot server, and inventory decision, then stop or boot local disk according to policy. That output lets a remote engineer compare the BMC console with inventory without inferring what the firmware saw. The same data should be sent to the provisioning API for correlation.

Hypothetical scenario: a worker reboots after a power event, receives a valid PXE response, reinstalls itself, and rejoins the cluster empty. That is not a Kubernetes bug. It is a provisioning-state bug. The server was allowed to perform a destructive install when the desired state should have been local boot. Fixing that class of failure requires inventory state, boot allow lists, BMC one-time boot, and installer completion records, not a different container runtime.

## Patterns & Anti-Patterns

Good PXE designs are boring because they separate identity, transport, installation, and cluster enrollment. The provisioning server can be small, but its state model must be explicit. Every host should have a known inventory state such as `new`, `quarantine`, `provisioning`, `installed`, `failed`, or `retired`. The boot API should return different scripts based on that state, and destructive installer scripts should be available only while a host is intentionally being provisioned.

| Pattern | Use When | Why It Works | Scaling Consideration |
|---|---|---|---|
| Isolated provisioning VLAN | The platform team owns a new rack or lab network | Limits accidental PXE responses and simplifies packet capture | Requires relay and firewall ownership with network teams |
| iPXE second stage | Firmware support is inconsistent or TFTP is too limiting | Keeps the firmware handoff small and moves logic to HTTP scripts | Requires signed binary planning under Secure Boot |
| Inventory-driven scripts | Hosts have known asset records before install | Prevents MAC-only identity drift and repeated manual edits | Needs a reliable inventory API and quarantine state |
| Versioned boot bundles | Kernel, initramfs, and seed schema change over time | Gives rollback and auditability for destructive installs | Requires artifact publishing discipline |
| Short-lived cluster join | Nodes join kubeadm, k0s, or k3s after install | Reduces risk from leaked bootstrap material | Needs token issuance and expiry automation |

The anti-patterns mostly come from using PXE as a quick imaging trick instead of as a production control point. A single global boot menu feels convenient until the wrong server selects the wrong item. A shared autoinstall file feels efficient until every host receives the same identity. A permanent bootstrap token feels simple until it is copied into logs, screenshots, and old initramfs command lines. These shortcuts work in a weekend lab and fail in an audited fleet.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|---|---|---|
| PXE enabled on the production VLAN | Any rebooted host can receive an installer | Isolate provisioning or require per-host allow state |
| One boot file for every architecture | UEFI hosts receive BIOS binaries or the reverse | Match on client architecture and test each hardware class |
| Static installer seed | Hostnames, IPs, and roles drift or duplicate | Generate per-host seed data from inventory |
| Long-lived join token in iPXE | Token leaks through HTTP logs and console capture | Fetch short-lived join material after OS install |
| Manual Secure Boot exceptions | Each server differs and future rebuilds fail | Define signed boot chain and key ownership up front |

The strongest pattern is a measured migration path. Start with a simple DHCP and iPXE design on a lab VLAN. Add inventory lookup before production. Add first-boot validation before cluster join. Add Secure Boot signing and key-management checks before regulated workloads. Add Tinkerbell, Metal3, or Cluster API when you need lifecycle reconciliation rather than only installation. That sequence improves quality without forcing the team to swallow the entire bare-metal ecosystem at once.

## Decision Framework

Use direct DHCP-owned PXE when the platform team controls the provisioning subnet, the VLAN is isolated, and the network team is comfortable delegating address allocation. Use proxyDHCP when the address plan is owned elsewhere or when the existing DHCP service cannot be modified safely. Use TFTP only for the smallest first-stage binaries or where firmware forces it. Use HTTP or HTTPS for large artifacts and for any stage where logging, caching, and artifact naming matter.

| Decision | Prefer This | When | Avoid When |
|---|---|---|---|
| DHCP-owned PXE | dnsmasq, Kea, or ISC DHCP with boot options | Dedicated provisioning VLAN | Shared client networks |
| ProxyDHCP | PXE responder beside existing DHCP | Enterprise DHCP cannot change | Relay behavior cannot be tested |
| TFTP first stage | `undionly.kpxe`, `ipxe.efi`, GRUB EFI | Broad firmware compatibility | Large files or lossy links |
| UEFI HTTP Boot | Firmware loads URI directly | Hardware matrix is tested | HTTPS behavior is unknown |
| iPXE dynamic scripts | Inventory-generated boot decisions | Per-host identity and roles matter | Secure Boot signing is unsupported |
| Installer automation | Kickstart, preseed, autoinstall, AutoYaST | Mutable OS install is required | Immutable OS image flow is preferred |
| Image-based workflow | Tinkerbell or Metal3 writes an image | Fleet needs lifecycle automation | Team needs only a small lab bootstrap |

The simplest safe architecture for many teams is a two-stage boot. Firmware uses DHCP and TFTP only long enough to start signed GRUB or iPXE. The second stage uses HTTP to fetch a dynamic script and large artifacts. The installer uses per-host seed data generated from inventory. First boot retrieves short-lived cluster bootstrap material, joins the selected cluster, and reports success. Completion flips inventory state so the next reboot returns to local disk.

Choose immutable OS flows when you want the operating system to be treated as an appliance rather than as a mutable Linux host. That is the path Module 2.3 explores. Choose Cluster API and Metal3-style reconciliation when the problem is not "install these hosts once" but "maintain many clusters and replace failed machines declaratively." That is the path Module 2.4 explores. Choose the plain PXE patterns here when you need to understand, debug, or bootstrap the lower layers those tools still depend on.

## Did You Know?

- RFC 2131 describes DHCP as both an address-allocation mechanism and a way to deliver host-specific configuration parameters, which is why PXE can reuse DHCP as its first coordination point.
- RFC 4578 defines PXE client architecture information for DHCP, and that small detail is what lets one boot service choose different files for BIOS and UEFI clients.
- UEFI HTTP Boot was announced with UEFI 2.5 support in 2015, giving firmware a standards-based path to fetch boot images by URI rather than relying only on TFTP.
- Tinkerbell's documented stack requires machines to network boot using iPXE, showing that modern bare-metal platforms still depend on the early PXE concepts in this module.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Serving PXE on a normal production VLAN | PXE feels like just another DHCP option until a rebooted host follows it | Use a provisioning VLAN, proxyDHCP filters, and explicit per-host install state |
| Treating MAC address as the only identity | The boot MAC is easy to read during DHCP | Cross-check UUID, serial, asset tag, BMC address, and inventory state |
| Sending one boot file to all clients | Early labs often have one firmware type | Match RFC 4578 architecture values and test BIOS and UEFI paths separately |
| Putting secrets in iPXE query strings | Boot scripts are convenient and visible | Retrieve short-lived secrets after OS install through a trusted first-boot path |
| Using TFTP for every artifact | It works for the first small boot file | Chain-load to iPXE or UEFI HTTP Boot and move large files to HTTP |
| Disabling Secure Boot to make PXE work | Unsigned boot files fail at the firmware boundary | Use a signed shim/GRUB path or a documented custom signing process |
| Reinstalling on every network boot | The boot service lacks completion state | Flip inventory to local-boot or installed state after successful provisioning |
| Letting installer scripts become configuration management | `%post` and late-commands can do almost anything | Keep installers minimal and move long-term policy into packages, GitOps, or node bootstrap |

## Quiz

<details>
<summary>Question 1: A new worker receives an IP address but tries to download `pxelinux.0` even though it is a UEFI-only server. What do you check first?</summary>

Start with DHCP architecture matching and boot filename selection. The address allocation path is working, so the problem is likely not the whole DHCP service. Check whether the client sent option 93, whether your DHCP or proxyDHCP rules map that architecture to an EFI binary, and whether a default rule is overriding the UEFI-specific rule. Then confirm the file exists on the transport server and is signed if Secure Boot is enabled.
</details>

<details>
<summary>Question 2: Your enterprise DHCP service cannot be changed, but you need PXE boot on a new provisioning VLAN. Which model should you propose and what risk must you test?</summary>

Propose proxyDHCP so the existing service continues assigning addresses while a PXE-aware responder supplies boot information. The key risk is response timing and relay behavior, because the client must receive compatible information from both services. You should test packet captures from real hardware, not just virtual machines. The design should also restrict responses to PXE clients and known provisioning networks.
</details>

<details>
<summary>Question 3: A server finishes installing Ubuntu but rejoins with the same hostname as another worker. Which part of the provisioning design failed?</summary>

The installer seed or first-boot identity generation failed. PXE got the machine far enough to install, but the per-host data was not unique or was not tied to inventory. Fix the seed-generation path so hostname, instance identity, network metadata, and Kubernetes labels are derived from a registered host record. Add validation that rejects duplicate hostnames before the installer starts.
</details>

<details>
<summary>Question 4: Secure Boot blocks your custom `ipxe.efi` during a production hardware refresh. Why did the same script work in the lab, and what must change?</summary>

The lab probably ran with Secure Boot disabled or with firmware that did not enforce the same trust chain. In production, UEFI will execute only trusted EFI binaries, so an unsigned custom iPXE build is rejected before its script logic matters. You need a signed boot path through shim, GRUB, a trusted iPXE release, or an organization-controlled key-enrollment process. You should also document how keys are rotated and revoked.
</details>

<details>
<summary>Question 5: During a rack reboot, half the hosts PXE boot into the installer even though they were already cluster nodes. What is the root design flaw?</summary>

The provisioning system allowed destructive install behavior without checking desired state. A completed host should normally boot local disk unless inventory explicitly marks it for reprovisioning. Fix this with one-time BMC PXE overrides, installed-state records, allow lists, and an iPXE safe default that exits or boots local disk for hosts not in provisioning state. Do not solve this by asking operators to remember firmware settings manually.
</details>

<details>
<summary>Question 6: An installer can fetch the kernel and initramfs, but it fails when retrieving NoCloud seed data. Which logs and boundaries matter?</summary>

The boot transport is working, so move to HTTP access logs for the seed URL, installer console logs, DNS resolution, and any firewall between the installer environment and the seed server. Confirm that the URL passed on the kernel command line is correct and includes the expected trailing path format for the datasource. Also verify that per-host seed generation did not reject the machine because of missing or mismatched inventory identity.
</details>

<details>
<summary>Question 7: Your team wants one PXE flow that can later migrate to Metal3 or Tinkerbell. What design choices keep that migration easy?</summary>

Keep identity, artifacts, and workflow state separate from ad hoc shell scripts. Use inventory records, versioned image or boot bundles, per-host metadata, and explicit provisioning states. Avoid baking long-term cluster policy into DHCP or global installer files. Those choices map naturally to Tinkerbell hardware and workflow records or Metal3 `BareMetalHost` objects when the team adopts a declarative lifecycle controller.
</details>

## Hands-On Exercise: Design a Safe PXE Provisioning Lane

This exercise builds a rootless provisioning model in a temporary directory. It does not start a real DHCP server or write to a disk, because the learning goal is to design and validate the files that a production PXE lane would serve. You will create direct and proxy DHCP examples, a dynamic iPXE script, per-host Ubuntu autoinstall seed files, and a validation checklist that catches common destructive mistakes before a server boots.

### Task 1: Create the lab tree and inventory record

```bash
mkdir -p /tmp/kubedojo-pxe-lab/{dhcp,tftp,http/boot,http/seed/host-0008,http/bootstrap}
cd /tmp/kubedojo-pxe-lab

cat > inventory.env <<'EOF'
HOST_ID=host-0008
HOST_UUID=11111111-2222-3333-4444-555555555555
BOOT_MAC=52:54:00:12:34:56
ARCH=uefi-x64
ROLE=worker
HOSTNAME=worker-0008
BOOT_BUNDLE=ubuntu-24.04-k8s-2026-05-a
EOF
```

<details>
<summary>Solution notes</summary>

The inventory file is intentionally tiny, but it includes the signals the boot service should care about: host identity, UUID, boot MAC, architecture, role, hostname, and bundle version. A real system would store this in NetBox, an internal database, Tinkerbell Hardware objects, or Metal3 `BareMetalHost` resources. The key point is that scripts should read identity from a source of truth rather than inventing it during boot.
</details>

### Task 2: Draft direct DHCP and proxyDHCP configurations

```bash
cat > dhcp/direct-pxe.conf <<'EOF'
interface=prov0
bind-interfaces
dhcp-range=10.20.0.50,10.20.0.200,255.255.255.0,30m
dhcp-option=option:router,10.20.0.1
dhcp-option=option:dns-server,10.20.0.10
enable-tftp
tftp-root=/srv/pxe/tftp
dhcp-match=set:bios,option:client-arch,0
dhcp-match=set:uefi-x64,option:client-arch,7
dhcp-boot=tag:bios,undionly.kpxe
dhcp-boot=tag:uefi-x64,ipxe.efi
EOF

cat > dhcp/proxy-pxe.conf <<'EOF'
interface=prov0
bind-interfaces
dhcp-range=10.20.0.0,proxy,255.255.255.0
enable-tftp
tftp-root=/srv/pxe/tftp
pxe-service=x86PC,"iPXE BIOS",undionly.kpxe
pxe-service=x86-64_EFI,"iPXE UEFI",ipxe.efi
EOF
```

<details>
<summary>Solution notes</summary>

The direct file owns address allocation, while the proxy file assumes another service owns addresses. In a production review, you would ask which VLAN each file is allowed to bind to, whether relays forward both normal DHCP and proxy responses, and whether unknown hosts are blocked from destructive install state. The lab files are not meant to be copied into `/etc`; they are design artifacts for review.
</details>

### Task 3: Generate an iPXE entry script and a per-host installer script

```bash
cat > tftp/autoexec.ipxe <<'EOF'
#!ipxe
set boot-api http://10.20.0.10/boot
set host-id ${uuid}
isset ${host-id} || set host-id ${net0/mac}
chain --replace ${boot-api}/script?host=${host-id}&mac=${net0/mac}&arch=${buildarch}
EOF

cat > http/boot/host-0008.ipxe <<'EOF'
#!ipxe
set base-url http://10.20.0.10/images/ubuntu-24.04/amd64
kernel ${base-url}/casper/vmlinuz ip=dhcp autoinstall ds=nocloud-net;s=http://10.20.0.10/seed/host-0008/
initrd ${base-url}/casper/initrd
boot || goto failed

:failed
echo Provisioning failed for host-0008
sleep 15
exit
EOF
```

<details>
<summary>Solution notes</summary>

The first script is generic and safe to serve from the TFTP root after iPXE starts. The second script is per-host and should be returned only when inventory says `host-0008` is allowed to provision. Notice that no Kubernetes join token appears in either script. The installer seed and first-boot bootstrap path handle later configuration after the OS exists.
</details>

### Task 4: Write a NoCloud seed and first-boot bootstrap script

```bash
cat > http/seed/host-0008/meta-data <<'EOF'
instance-id: host-0008
local-hostname: worker-0008
EOF

cat > http/seed/host-0008/user-data <<'EOF'
#cloud-config
autoinstall:
  version: 1
  identity:
    hostname: worker-0008
    username: bootstrap
    password: "$6$example$replace-this-with-a-real-hash"
  ssh:
    install-server: true
    allow-pw: false
    authorized-keys:
      - ssh-ed25519 YOUR_PUBLIC_KEY_HERE platform@example.com
  storage:
    layout:
      name: lvm
  packages:
    - containerd
    - curl
  late-commands:
    - curtin in-target -- mkdir -p /opt/kubedojo
    - curtin in-target -- curl -fsS http://10.20.0.10/bootstrap/host-0008.sh -o /opt/kubedojo/bootstrap.sh
    - curtin in-target -- chmod 0700 /opt/kubedojo/bootstrap.sh
EOF

cat > http/bootstrap/host-0008.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "Bootstrap would configure containerd, kubelet prerequisites, and a short-lived join command."
echo "In production, retrieve the join command from a trusted internal service after host validation."
EOF
chmod 0755 http/bootstrap/host-0008.sh
```

<details>
<summary>Solution notes</summary>

The seed files demonstrate the handoff between installer identity and first-boot behavior. The bootstrap script is deliberately harmless in the lab. In production, it would validate hostname, asset identity, time sync, runtime health, and then retrieve a short-lived kubeadm, k0s, or k3s join credential from a trusted endpoint. It should report success back to inventory so the host stops receiving destructive installer scripts.
</details>

### Task 5: Run a simple safety validation

```bash
test -f inventory.env
test -f tftp/autoexec.ipxe
test -f http/boot/host-0008.ipxe
test -f http/seed/host-0008/user-data
test -f http/seed/host-0008/meta-data
grep -q 'hostname: worker-0008' http/seed/host-0008/user-data
grep -q 'ds=nocloud-net;s=http://10.20.0.10/seed/host-0008/' http/boot/host-0008.ipxe
! grep -R "kubeadm join .*--token" .
! grep -R "K3S_TOKEN=" .
! grep -R "password123" .
printf 'PXE lab validation passed\n'
```

<details>
<summary>Solution notes</summary>

This is not a full linter, but it catches the safety posture we care about in this module. The lab must have inventory, boot scripts, NoCloud seed files, a hostname, and no obvious long-lived cluster token in boot-served files. A production version would also parse YAML, verify checksums, confirm artifact URLs, check architecture mapping, and fail closed for unknown inventory records.
</details>

### Success Criteria

- [ ] You can explain which DHCP file owns address allocation and which file only supplies PXE boot data.
- [ ] The iPXE entry script passes MAC, UUID-derived identity, and architecture toward a dynamic boot API.
- [ ] The per-host installer script serves kernel and initramfs over HTTP rather than relying on TFTP for large artifacts.
- [ ] The NoCloud seed gives `host-0008` a deterministic hostname and instance identity.
- [ ] The bootstrap script contains no static kubeadm, k0s, or k3s join token.
- [ ] The validation commands pass and print `PXE lab validation passed`.

## Sources

- [RFC 2131: Dynamic Host Configuration Protocol](https://www.rfc-editor.org/rfc/rfc2131)
- [RFC 4578: DHCP Options for PXE](https://www.rfc-editor.org/rfc/rfc4578)
- [RFC 1350: The TFTP Protocol](https://www.rfc-editor.org/rfc/rfc1350)
- [dnsmasq documentation](https://dnsmasq.org/doc.html)
- [UEFI Specification 2.11: Network Protocols, PXE, and HTTP Boot](https://uefi.org/specs/UEFI/2.11/24_Network_Protocols_SNP_PXE_BIS.html)
- [UEFI Forum announcement for UEFI 2.5 HTTP Boot support](https://uefi.org/press-release/uefi-forum-launches-non-volatile-memory-and-boot-http-support-across-three)
- [iPXE chainloading guide](https://ipxe.org/howto/chainloading)
- [iPXE scripting guide](https://ipxe.org/scripting)
- [iPXE cryptography guide](https://ipxe.org/crypto)
- [Anaconda Kickstart documentation](https://anaconda-installer.readthedocs.io/en/latest/user-guide/kickstart.html)
- [Ubuntu autoinstall reference](https://canonical-subiquity.readthedocs-hosted.com/en/latest/reference/autoinstall-reference.html)
- [Debian installer preseeding guide](https://www.debian.org/releases/stable/amd64/apbs02.en.html)
- [SUSE AutoYaST Guide](https://documentation.suse.com/en-us/sles/15-SP7/single-html/SLES-autoyast/index.html)
- [cloud-init NoCloud datasource documentation](https://docs.cloud-init.io/en/latest/reference/datasources/nocloud.html)
- [Tinkerbell architecture documentation](https://tinkerbell.org/docs/v0.22/reference/architecture/)
- [Tinkerbell Smee service documentation](https://tinkerbell.org/docs/v0.22/services/smee/)
- [Cluster API Provider Tinkerbell documentation](https://tinkerbell.org/docs/services/cluster-api-provider-tinkerbell/)
- [Cluster API Provider Metal3 introduction](https://book.metal3.io/capm3/introduction)
- [Metal3 Bare Metal Operator provisioning documentation](https://book.metal3.io/bmo/provisioning)
- [Kubernetes kubeadm token reference](https://kubernetes.io/docs/reference/setup-tools/kubeadm/kubeadm-token/)
- [Kubernetes bootstrap tokens documentation](https://kubernetes.io/docs/reference/access-authn-authz/bootstrap-tokens/)
- [Ubuntu Secure Boot documentation](https://documentation.ubuntu.com/security/security-features/platform-protections/secure-boot/)
- [Red Hat Secure Boot kernel and module signing documentation](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/8/html/managing_monitoring_and_updating_the_kernel/signing-a-kernel-and-modules-for-secure-boot_managing-monitoring-and-updating-the-kernel)
- [k0s installation documentation](https://docs.k0sproject.io/stable/install/)
- [K3s configuration options documentation](https://docs.k3s.io/installation/configuration)

## Next Module

Continue to [Module 2.3: Immutable OS for Kubernetes](../module-2.3-immutable-os/) to compare this mutable installer path with Talos, Flatcar, and other image-first operating-system models for bare-metal Kubernetes.
