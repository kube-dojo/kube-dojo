# LFCS Learning Path

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

## LFCS Domains & KubeDojo Coverage

### Domain 1: Essential Commands (20%)

**Coverage: Good** — Our Linux foundations and shell scripting modules cover this well.

| LFCS Topic | KubeDojo Module | Status |
|-----------|-----------------|--------|
| Log into local & remote graphical/text consoles | [1.2 Processes & systemd](../../linux/foundations/system-essentials/module-1.2-processes-systemd.md) | Covered |
| Search for files | [7.2 Text Processing](../../linux/operations/shell-scripting/module-7.2-text-processing.md) | Covered |
| Evaluate & compare basic file system features | [1.3 Filesystem Hierarchy](../../linux/foundations/system-essentials/module-1.3-filesystem-hierarchy.md) | Covered |
| Compare & manipulate file content | [7.2 Text Processing](../../linux/operations/shell-scripting/module-7.2-text-processing.md) | Covered |
| Use input/output redirection | [7.1 Bash Fundamentals](../../linux/operations/shell-scripting/module-7.1-bash-fundamentals.md) | Covered |
| Analyze text using basic regex | [7.2 Text Processing](../../linux/operations/shell-scripting/module-7.2-text-processing.md) | Covered |
| Archive, backup, compress files | [7.3 Practical Scripts](../../linux/operations/shell-scripting/module-7.3-practical-scripts.md) | Partial |
| Create, delete, copy, move files/dirs | [1.3 Filesystem Hierarchy](../../linux/foundations/system-essentials/module-1.3-filesystem-hierarchy.md) | Covered |
| Create/manage hard and soft links | [1.3 Filesystem Hierarchy](../../linux/foundations/system-essentials/module-1.3-filesystem-hierarchy.md) | Covered |
| List, set, change standard permissions | [1.4 Users & Permissions](../../linux/foundations/system-essentials/module-1.4-users-permissions.md) | Covered |
| Read and use system documentation | General CLI skills | Covered |

### Domain 2: Operation of Running Systems (25%)

**Coverage: Partial** — Process management and systemd are covered. Boot process and kernel modules need supplementation.

| LFCS Topic | KubeDojo Module | Status |
|-----------|-----------------|--------|
| Boot, reboot, shut down safely | [1.2 Processes & systemd](../../linux/foundations/system-essentials/module-1.2-processes-systemd.md) | Partial |
| Boot into different targets (runlevels) | [1.2 Processes & systemd](../../linux/foundations/system-essentials/module-1.2-processes-systemd.md) | Partial |
| Install, configure, troubleshoot bootloaders | — | Gap |
| Manage processes (ps, top, kill, nice) | [1.2 Processes & systemd](../../linux/foundations/system-essentials/module-1.2-processes-systemd.md) | Covered |
| Manage startup services (systemctl) | [1.2 Processes & systemd](../../linux/foundations/system-essentials/module-1.2-processes-systemd.md) | Covered |
| Diagnose and manage processes | [6.3 Process Debugging](../../linux/operations/troubleshooting/module-6.3-process-debugging.md) | Covered |
| Locate and analyze system log files | [6.2 Log Analysis](../../linux/operations/troubleshooting/module-6.2-log-analysis.md) | Covered |
| Schedule tasks (cron, at) | [7.4 DevOps Automation](../../linux/operations/shell-scripting/module-7.4-devops-automation.md) | Partial |
| Verify system integrity | — | Gap |
| List and load kernel modules | [1.1 Kernel Architecture](../../linux/foundations/system-essentials/module-1.1-kernel-architecture.md) | Partial |

### Domain 3: User and Group Management (10%)

**Coverage: Good** — Well covered in our permissions module.

| LFCS Topic | KubeDojo Module | Status |
|-----------|-----------------|--------|
| Create, delete, modify local users/groups | [1.4 Users & Permissions](../../linux/foundations/system-essentials/module-1.4-users-permissions.md) | Covered |
| Manage user/group properties | [1.4 Users & Permissions](../../linux/foundations/system-essentials/module-1.4-users-permissions.md) | Covered |
| Configure user resource limits | [2.2 Control Groups](../../linux/foundations/container-primitives/module-2.2-cgroups.md) | Partial |
| Manage user privileges (sudo) | [1.4 Users & Permissions](../../linux/foundations/system-essentials/module-1.4-users-permissions.md) | Covered |
| Configure PAM | — | Gap |

### Domain 4: Networking (25%)

**Coverage: Partial** — TCP/IP and DNS are solid. Firewall configuration, NAT, bonding are gaps.

| LFCS Topic | KubeDojo Module | Status |
|-----------|-----------------|--------|
| Configure networking (IP, subnet, gateway) | [3.1 TCP/IP Essentials](../../linux/foundations/networking/module-3.1-tcp-ip-essentials.md) | Covered |
| Configure hostname resolution | [3.2 DNS in Linux](../../linux/foundations/networking/module-3.2-dns-linux.md) | Covered |
| Configure network services to start at boot | [1.2 Processes & systemd](../../linux/foundations/system-essentials/module-1.2-processes-systemd.md) | Partial |
| Implement packet filtering (firewalld/nftables) | [**8.2 Network Administration**](../../linux/operations/module-8.2-network-administration.md) | **New** |
| Configure firewall settings | [**8.2 Network Administration**](../../linux/operations/module-8.2-network-administration.md) | **New** |
| Configure NAT/masquerading | [**8.2 Network Administration**](../../linux/operations/module-8.2-network-administration.md) | **New** |
| Network bonding/bridging | [**8.2 Network Administration**](../../linux/operations/module-8.2-network-administration.md) | **New** |
| Statically route IP traffic | [3.1 TCP/IP Essentials](../../linux/foundations/networking/module-3.1-tcp-ip-essentials.md) | Partial |
| Synchronize time (NTP/chrony) | [**8.2 Network Administration**](../../linux/operations/module-8.2-network-administration.md) | **New** |

### Domain 5: Storage Management (20%)

**Coverage: Gap** — This is our biggest gap. Filesystem hierarchy is covered, but LVM, NFS, swap, and automount are not.

| LFCS Topic | KubeDojo Module | Status |
|-----------|-----------------|--------|
| List, create, delete partitions | [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management.md) | **New** |
| Create/configure file systems (ext4, xfs) | [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management.md) | **New** |
| Mount filesystems at boot (fstab) | [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management.md) | **New** |
| Configure and manage LVM | [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management.md) | **New** |
| Create and manage RAID (mdadm) | — | Gap |
| Configure NFS server/client | [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management.md) | **New** |
| Configure swap space | [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management.md) | **New** |
| Manage automount (autofs) | [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management.md) | **New** |
| Monitor storage (df, du, iostat) | [5.4 I/O Performance](../../linux/operations/performance/module-5.4-io-performance.md) | Covered |

---

## Recommended Study Order

If you are specifically preparing for LFCS, follow this sequence through our Linux track:

### Phase 1: Foundations (Week 1-2)
1. [1.1 Kernel Architecture](../../linux/foundations/system-essentials/module-1.1-kernel-architecture.md)
2. [1.2 Processes & systemd](../../linux/foundations/system-essentials/module-1.2-processes-systemd.md)
3. [1.3 Filesystem Hierarchy](../../linux/foundations/system-essentials/module-1.3-filesystem-hierarchy.md)
4. [1.4 Users & Permissions](../../linux/foundations/system-essentials/module-1.4-users-permissions.md)

### Phase 2: Networking Basics (Week 2-3)
5. [3.1 TCP/IP Essentials](../../linux/foundations/networking/module-3.1-tcp-ip-essentials.md)
6. [3.2 DNS in Linux](../../linux/foundations/networking/module-3.2-dns-linux.md)
7. [3.4 iptables & netfilter](../../linux/foundations/networking/module-3.4-iptables-netfilter.md)

### Phase 3: Operations (Week 3-4)
8. [7.1 Bash Fundamentals](../../linux/operations/shell-scripting/module-7.1-bash-fundamentals.md)
9. [7.2 Text Processing](../../linux/operations/shell-scripting/module-7.2-text-processing.md)
10. [6.1 Systematic Troubleshooting](../../linux/operations/troubleshooting/module-6.1-systematic-troubleshooting.md)
11. [6.2 Log Analysis](../../linux/operations/troubleshooting/module-6.2-log-analysis.md)

### Phase 4: LFCS-Specific (Week 4-5)
12. [**8.1 Storage Management**](../../linux/operations/module-8.1-storage-management.md) — LVM, NFS, filesystems
13. [**8.2 Network Administration**](../../linux/operations/module-8.2-network-administration.md) — Firewall, NAT, bonding

### Phase 5: Performance & Polish (Week 5-6)
14. [5.1 The USE Method](../../linux/operations/performance/module-5.1-use-method.md)
15. [5.4 I/O Performance](../../linux/operations/performance/module-5.4-io-performance.md)
16. [6.3 Process Debugging](../../linux/operations/troubleshooting/module-6.3-process-debugging.md)

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

## Remaining Gaps

These LFCS topics are NOT yet covered in KubeDojo and would need self-study:

| Topic | Notes |
|-------|-------|
| Bootloader (GRUB2) installation/troubleshooting | Rarely needed in cloud/container environments |
| RAID management (mdadm) | Increasingly handled by cloud providers |
| PAM configuration | Niche but can appear on exam |
| System integrity verification (AIDE, rpm -V) | Study the man pages |

These gaps represent edge topics. Focus your time on the high-weight domains (Networking 25%, Operations 25%, Storage 20%) first.

---

## Resources

- [LFCS Exam Curriculum (Linux Foundation)](https://training.linuxfoundation.org/certification/linux-foundation-certified-sysadmin-lfcs/)
- [Ubuntu 22.04 Server Guide](https://ubuntu.com/server/docs)
- [KubeDojo Linux Track](../../linux/) — Our primary content source
