---
title: "LFCS Learning Path"
sidebar:
  order: 1
  label: "LFCS"
---
> **Linux Foundation Certified System Administrator** - Performance-based Linux sysadmin certification

## About LFCS

The LFCS is a **performance-based (hands-on) exam** that validates practical Linux system administration skills. Unlike Kubernetes certifications, this is **pure Linux** — no containers, no orchestration, just system administration fundamentals.

| Aspect | Details |
|--------|---------|
| **Format** | Performance-based (hands-on CLI tasks) |
| **Duration** | 2 hours |
| **Passing Score** | 67% |
| **Cost** | $445 (includes one free retake) |
| **Validity** | 3 years |
| **Distribution** | Ubuntu 22.04 |

> **Important**: This is NOT a Kubernetes certification. It lives under `docs/k8s/` for organizational purposes alongside other Linux Foundation certs, but the content maps entirely to our [Linux Deep Dive Track](../../linux/).

---

## Why LFCS?

- **Foundation for everything** — Solid Linux skills make Kubernetes, DevOps, and SRE work dramatically easier
- **Performance-based** — Like CKA/CKAD/CKS, you prove skills by doing, not by picking answers
- **Career differentiator** — Many "DevOps engineers" can't troubleshoot a Linux box. You won't be one of them
- **Gateway cert** — Builds confidence for CKA/CKAD hands-on exam format

---

## Exam-Prep Modules

| # | Module |
|---|--------|
| 1.1 | [LFCS Exam Strategy and Workflow](./module-1.1-exam-strategy-and-workflow/) |
| 1.2 | [LFCS Essential Commands Practice](./module-1.2-essential-commands-practice/) |
| 1.3 | [LFCS Running Systems and Networking Practice](./module-1.3-running-systems-and-networking-practice/) |
| 1.4 | [LFCS Storage, Services, and Users Practice](./module-1.4-storage-services-and-users-practice/) |
| 1.5 | [LFCS Full Mock Exam](./module-1.5-full-mock-exam/) |

---

## LFCS Domains & KubeDojo Coverage

Important principle:
- `covered elsewhere` is not always good enough for exam prep
- if an LFCS skill is only touched partially inside a broader Linux module, that should be treated as prep debt until we have dedicated LFCS-facing practice for it
- this page therefore distinguishes between strong coverage and remaining dedicated-prep gaps

### Domain 1: Essential Commands (20%)

**Coverage: Good** — command fundamentals are strong and the LFCS practice path now includes direct exam-facing drills rather than relying only on broader Linux reuse.

| LFCS Topic | KubeDojo Module | Status |
|-----------|-----------------|--------|
| Log into local & remote graphical/text consoles | [1.2 Processes & systemd](../../linux/foundations/system-essentials/module-1.2-processes-systemd/) | Covered |
| Search for files | [7.2 Text Processing](../../linux/operations/shell-scripting/module-7.2-text-processing/) | Covered |
| Evaluate & compare basic file system features | [1.3 Filesystem Hierarchy](../../linux/foundations/system-essentials/module-1.3-filesystem-hierarchy/) | Covered |
| Compare & manipulate file content | [7.2 Text Processing](../../linux/operations/shell-scripting/module-7.2-text-processing/) | Covered |
| Use input/output redirection | [7.1 Bash Fundamentals](../../linux/operations/shell-scripting/module-7.1-bash-fundamentals/) | Covered |
| Analyze text using basic regex | [7.2 Text Processing](../../linux/operations/shell-scripting/module-7.2-text-processing/) | Covered |
| Archive, backup, compress files | [1.2 LFCS Essential Commands Practice](./module-1.2-essential-commands-practice/) | Covered |
| Create, delete, copy, move files/dirs | [1.3 Filesystem Hierarchy](../../linux/foundations/system-essentials/module-1.3-filesystem-hierarchy/) | Covered |
| Create/manage hard and soft links | [1.3 Filesystem Hierarchy](../../linux/foundations/system-essentials/module-1.3-filesystem-hierarchy/) | Covered |
| List, set, change standard permissions | [1.4 Users & Permissions](../../linux/foundations/system-essentials/module-1.4-users-permissions/) | Covered |
| Read and use system documentation | General CLI skills | Covered |

### Domain 2: Operation of Running Systems (25%)

**Coverage: Good** — the dedicated LFCS running-systems practice module now covers boot targets, scheduling, service recovery, shutdown discipline, and kernel-module workflow directly.

| LFCS Topic | KubeDojo Module | Status |
|-----------|-----------------|--------|
| Boot, reboot, shut down safely | [1.3 LFCS Running Systems and Networking Practice](./module-1.3-running-systems-and-networking-practice/) | Covered |
| Boot into different targets (runlevels) | [1.3 LFCS Running Systems and Networking Practice](./module-1.3-running-systems-and-networking-practice/) | Covered |
| Install, configure, troubleshoot bootloaders | [1.2 Processes & systemd](../../linux/foundations/system-essentials/module-1.2-processes-systemd/) | Covered |
| Manage processes (ps, top, kill, nice) | [1.2 Processes & systemd](../../linux/foundations/system-essentials/module-1.2-processes-systemd/) | Covered |
| Manage startup services (systemctl) | [1.2 Processes & systemd](../../linux/foundations/system-essentials/module-1.2-processes-systemd/) | Covered |
| Diagnose and manage processes | [6.3 Process Debugging](../../linux/operations/troubleshooting/module-6.3-process-debugging/) | Covered |
| Locate and analyze system log files | [6.2 Log Analysis](../../linux/operations/troubleshooting/module-6.2-log-analysis/) | Covered |
| Schedule tasks (cron, at) | [1.3 LFCS Running Systems and Networking Practice](./module-1.3-running-systems-and-networking-practice/) | Covered |
| Verify system integrity | [4.1 Kernel Hardening](../../linux/security/hardening/module-4.1-kernel-hardening/) | Covered |
| List and load kernel modules | [1.3 LFCS Running Systems and Networking Practice](./module-1.3-running-systems-and-networking-practice/) | Covered |

### Domain 3: User and Group Management (10%)

**Coverage: Good** — user and privilege work is strong, and the LFCS storage/users practice module now includes direct resource-limit and PAM-facing verification.

| LFCS Topic | KubeDojo Module | Status |
|-----------|-----------------|--------|
| Create, delete, modify local users/groups | [1.4 Users & Permissions](../../linux/foundations/system-essentials/module-1.4-users-permissions/) | Covered |
| Manage user/group properties | [1.4 Users & Permissions](../../linux/foundations/system-essentials/module-1.4-users-permissions/) | Covered |
| Configure user resource limits | [1.4 LFCS Storage, Services, and Users Practice](./module-1.4-storage-services-and-users-practice/) | Covered |
| Manage user privileges (sudo) | [1.4 Users & Permissions](../../linux/foundations/system-essentials/module-1.4-users-permissions/) | Covered |
| Configure PAM | [1.4 Users & Permissions](../../linux/foundations/system-essentials/module-1.4-users-permissions/) | Covered |

### Domain 4: Networking (25%)

**Coverage: Good** — networking fundamentals remain strong, and static-route plus network-service persistence tasks now have direct LFCS-oriented practice.

| LFCS Topic | KubeDojo Module | Status |
|-----------|-----------------|--------|
| Configure networking (IP, subnet, gateway) | [3.1 TCP/IP Essentials](../../linux/foundations/networking/module-3.1-tcp-ip-essentials/) | Covered |
| Configure hostname resolution | [3.2 DNS in Linux](../../linux/foundations/networking/module-3.2-dns-linux/) | Covered |
| Configure network services to start at boot | [1.3 LFCS Running Systems and Networking Practice](./module-1.3-running-systems-and-networking-practice/) | Covered |
| Implement packet filtering (firewalld/nftables) | [**8.2 Network Administration**](../../linux/operations/module-8.2-network-administration/) | **New** |
| Configure firewall settings | [**8.2 Network Administration**](../../linux/operations/module-8.2-network-administration/) | **New** |
| Configure NAT/masquerading | [**8.2 Network Administration**](../../linux/operations/module-8.2-network-administration/) | **New** |
| Network bonding/bridging | [**8.2 Network Administration**](../../linux/operations/module-8.2-network-administration/) | **New** |
| Statically route IP traffic | [1.3 LFCS Running Systems and Networking Practice](./module-1.3-running-systems-and-networking-practice/) | Covered |
| Synchronize time (NTP/chrony) | [**8.2 Network Administration**](../../linux/operations/module-8.2-network-administration/) | **New** |

### Domain 5: Storage Management (20%)

**Coverage: Good** — storage is in the strongest position because dedicated Linux storage content already maps much more directly to LFCS tasks.

| LFCS Topic | KubeDojo Module | Status |
|-----------|-----------------|--------|
| List, create, delete partitions | [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management/) | **New** |
| Create/configure file systems (ext4, xfs) | [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management/) | **New** |
| Mount filesystems at boot (fstab) | [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management/) | **New** |
| Configure and manage LVM | [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management/) | **New** |
| Create and manage RAID (mdadm) | [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management/) | Covered |
| Configure NFS server/client | [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management/) | **New** |
| Configure swap space | [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management/) | **New** |
| Manage automount (autofs) | [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management/) | **New** |
| Monitor storage (df, du, iostat) | [5.4 I/O Performance](../../linux/operations/performance/module-5.4-io-performance/) | Covered |

---

## Recommended Study Order

If you are specifically preparing for LFCS, follow this sequence through our Linux track:

### Phase 1: Foundations (Week 1-2)
1. [1.1 Kernel Architecture](../../linux/foundations/system-essentials/module-1.1-kernel-architecture/)
2. [1.2 Processes & systemd](../../linux/foundations/system-essentials/module-1.2-processes-systemd/)
3. [1.3 Filesystem Hierarchy](../../linux/foundations/system-essentials/module-1.3-filesystem-hierarchy/)
4. [1.4 Users & Permissions](../../linux/foundations/system-essentials/module-1.4-users-permissions/)

### Phase 2: Networking Basics (Week 2-3)
5. [3.1 TCP/IP Essentials](../../linux/foundations/networking/module-3.1-tcp-ip-essentials/)
6. [3.2 DNS in Linux](../../linux/foundations/networking/module-3.2-dns-linux/)
7. [3.4 iptables & netfilter](../../linux/foundations/networking/module-3.4-iptables-netfilter/)

### Phase 3: Operations (Week 3-4)
8. [7.1 Bash Fundamentals](../../linux/operations/shell-scripting/module-7.1-bash-fundamentals/)
9. [7.2 Text Processing](../../linux/operations/shell-scripting/module-7.2-text-processing/)
10. [6.1 Systematic Troubleshooting](../../linux/operations/troubleshooting/module-6.1-systematic-troubleshooting/)
11. [6.2 Log Analysis](../../linux/operations/troubleshooting/module-6.2-log-analysis/)

### Phase 4: LFCS-Specific (Week 4-5)
12. [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management/) — LVM, NFS, filesystems
13. [**8.2 Network Administration**](../../linux/operations/module-8.2-network-administration/) — Firewall, NAT, bonding

### Phase 5: Performance & Polish (Week 5-6)
14. [5.1 The USE Method](../../linux/operations/performance/module-5.1-use-method/)
15. [5.4 I/O Performance](../../linux/operations/performance/module-5.4-io-performance/)
16. [6.3 Process Debugging](../../linux/operations/troubleshooting/module-6.3-process-debugging/)

---

## Exam Tips

### It's Performance-Based
Just like CKA/CKAD, you get a terminal and must complete tasks. No multiple choice. Practice by actually running commands, not by reading about them.

### Time Management
- **2 hours** for all tasks
- Use the [Three-Pass Strategy](../../prerequisites/philosophy-design/):
  - **Pass 1**: Quick wins — file creation, user management, basic commands
  - **Pass 2**: Medium tasks — filesystem, systemd, networking config
  - **Pass 3**: Complex tasks — LVM, NFS, firewall rules

### Key Differences from CKA/CKAD
| Aspect | LFCS | CKA/CKAD |
|--------|------|----------|
| Topic | Pure Linux sysadmin | Kubernetes |
| kubectl needed | No | Yes |
| Distribution | Ubuntu 22.04 | Ubuntu-based |
| Pass score | 67% | 66% |
| Duration | 2 hours | 2 hours |

### Practice Environment
- Use a VM or container running Ubuntu 22.04
- Vagrant + VirtualBox or Multipass are great options
- Practice everything in a terminal — no GUI on the exam

---

## Previously Identified Gaps (Now Covered)

These LFCS topics were previously gaps in KubeDojo but are now covered:

| Topic | Covered In |
|-------|------------|
| Bootloader (GRUB2) installation/troubleshooting | [1.2 Processes & systemd](../../linux/foundations/system-essentials/module-1.2-processes-systemd/) |
| RAID management (mdadm) | [8.1 Storage Management](../../linux/operations/module-8.1-storage-management/) |
| PAM configuration | [1.4 Users & Permissions](../../linux/foundations/system-essentials/module-1.4-users-permissions/) |
| System integrity verification (AIDE, rpm -V) | [4.1 Kernel Hardening](../../linux/security/hardening/module-4.1-kernel-hardening/) |

Focus your time on the high-weight domains (Networking 25%, Operations 25%, Storage 20%) first.

---

## Current Dedicated LFCS Gap Register

The major dedicated exam-prep gaps identified in the previous audit have now been closed inside the LFCS modules themselves.

Current state:
- archive/compression drills are covered in `1.2`
- boot targets, shutdown discipline, `cron`/`at`, kernel modules, and static routes are covered in `1.3`
- user resource limits and PAM-oriented checks are covered in `1.4`

This does not mean LFCS is "finished forever." It means the track no longer depends on hand-waving phrases like `partial coverage elsewhere` for core exam tasks.

---

## Resources

- [LFCS Exam Curriculum (Linux Foundation)](https://training.linuxfoundation.org/certification/linux-foundation-certified-sysadmin-lfcs/)
- [Ubuntu 22.04 Server Guide](https://ubuntu.com/server/docs)
- [KubeDojo Linux Track](../../linux/) — Our primary content source
