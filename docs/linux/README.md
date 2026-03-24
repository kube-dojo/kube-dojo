# Linux Deep Dive Track

> **Essential Linux knowledge for Kubernetes and DevOps practitioners.**

The foundation that makes everything else make sense. You can't debug Kubernetes if you don't understand Linux. Every container issue is ultimately a Linux issue.

## Who This Track Is For

- **Kubernetes practitioners** who want to understand what's happening beneath containers
- **DevOps engineers** who need Linux fundamentals for automation and troubleshooting
- **SREs** who need deep system knowledge for incident response
- **Anyone** starting their cloud-native journey

## Track Structure

```
linux/
├── foundations/              # Core Linux (must-know)
│   ├── system-essentials/       # Kernel, processes, filesystem, permissions
│   ├── container-primitives/    # Namespaces, cgroups, capabilities, overlayfs
│   └── networking/              # TCP/IP, DNS, network namespaces, iptables
│
├── security/                 # Linux security
│   └── hardening/               # sysctl, AppArmor, SELinux, seccomp
│
├── sysadmin/                # System administration
│   └── sysadmin/                # Storage, networking, packages, scheduling
│
└── operations/               # SRE/DevOps skills
    ├── performance/             # USE method, CPU, memory, I/O
    ├── troubleshooting/         # Systematic debugging, logs, process, network
    └── shell-scripting/         # Bash, text processing, practical automation
```

**Total: 32 modules**

---

## Learning Path

### Start Here: Foundations (12 modules)

#### 1. System Essentials (4 modules)
| Module | Description | Time |
|--------|-------------|------|
| [1.1 Kernel Architecture](foundations/system-essentials/module-1.1-kernel-architecture.md) | Kernel vs userspace, system calls, why containers share kernels | 25-30 min |
| [1.2 Processes & systemd](foundations/system-essentials/module-1.2-processes-systemd.md) | PIDs, process lifecycle, signals, systemctl | 30-35 min |
| [1.3 Filesystem Hierarchy](foundations/system-essentials/module-1.3-filesystem-hierarchy.md) | FHS, /proc, /sys, inodes, mount points | 25-30 min |
| [1.4 Users & Permissions](foundations/system-essentials/module-1.4-users-permissions.md) | UIDs, rwx, setuid, sudo, least privilege | 25-30 min |

#### 2. Container Primitives (4 modules)
| Module | Description | Time |
|--------|-------------|------|
| [2.1 Linux Namespaces](foundations/container-primitives/module-2.1-namespaces.md) | PID, network, mount, user isolation | 30-35 min |
| [2.2 Control Groups](foundations/container-primitives/module-2.2-cgroups.md) | CPU/memory limits, v1 vs v2, Kubernetes integration | 30-35 min |
| [2.3 Capabilities & LSMs](foundations/container-primitives/module-2.3-capabilities-lsms.md) | CAP_*, AppArmor, SELinux, seccomp overview | 25-30 min |
| [2.4 Union Filesystems](foundations/container-primitives/module-2.4-union-filesystems.md) | OverlayFS, layers, storage drivers | 25-30 min |

#### 3. Networking (4 modules)
| Module | Description | Time |
|--------|-------------|------|
| [3.1 TCP/IP Essentials](foundations/networking/module-3.1-tcp-ip-essentials.md) | OSI model, TCP vs UDP, routing, ports | 30-35 min |
| [3.2 DNS in Linux](foundations/networking/module-3.2-dns-linux.md) | resolv.conf, dig, DNS debugging, CoreDNS | 25-30 min |
| [3.3 Network Namespaces](foundations/networking/module-3.3-network-namespaces.md) | veth pairs, bridges, pod networking | 30-35 min |
| [3.4 iptables & netfilter](foundations/networking/module-3.4-iptables-netfilter.md) | Packet filtering, NAT, kube-proxy internals | 35-40 min |

### Then: Security (4 modules)

#### 4. Hardening
| Module | Description | Time |
|--------|-------------|------|
| [4.1 Kernel Hardening](security/hardening/module-4.1-kernel-hardening.md) | sysctl, network stack, memory protection | 25-30 min |
| [4.2 AppArmor Profiles](security/hardening/module-4.2-apparmor.md) | MAC, profile modes, K8s integration | 30-35 min |
| [4.3 SELinux Contexts](security/hardening/module-4.3-selinux.md) | Policies, contexts, troubleshooting | 35-40 min |
| [4.4 seccomp Profiles](security/hardening/module-4.4-seccomp.md) | System call filtering, custom profiles | 25-30 min |

### Then: System Administration (4 modules)

#### 8. System Administration
| Module | Description | Time |
|--------|-------------|------|
| [8.1 Storage Management](operations/module-8.1-storage-management.md) | LVM, RAID, NFS | 30-35 min |
| [8.2 Network Administration](operations/module-8.2-network-administration.md) | firewalld, bonding, chrony | 30-35 min |
| [8.3 Package & User Management](operations/module-8.3-package-user-management.md) | apt/dnf, useradd/visudo | 25-30 min |
| [8.4 Scheduling & Backups](operations/module-8.4-scheduling-backups.md) | cron, tar, rsync | 25-30 min |

### Then: Operations (12 modules)

#### 5. Performance (4 modules)
| Module | Description | Time |
|--------|-------------|------|
| [5.1 The USE Method](operations/performance/module-5.1-use-method.md) | Utilization, Saturation, Errors | 25-30 min |
| [5.2 CPU & Scheduling](operations/performance/module-5.2-cpu-scheduling.md) | CPU metrics, CFS scheduler, K8s CPU limits | 30-35 min |
| [5.3 Memory Management](operations/performance/module-5.3-memory-management.md) | Virtual memory, caching, OOM killer | 30-35 min |
| [5.4 I/O Performance](operations/performance/module-5.4-io-performance.md) | iostat, block scheduling, storage tuning | 25-30 min |

#### 6. Troubleshooting (4 modules)
| Module | Description | Time |
|--------|-------------|------|
| [6.1 Systematic Troubleshooting](operations/troubleshooting/module-6.1-systematic-troubleshooting.md) | Scientific method, divide & conquer, timeline | 25-30 min |
| [6.2 Log Analysis](operations/troubleshooting/module-6.2-log-analysis.md) | journalctl, dmesg, log correlation | 25-30 min |
| [6.3 Process Debugging](operations/troubleshooting/module-6.3-process-debugging.md) | strace, /proc, lsof, hung processes | 30-35 min |
| [6.4 Network Debugging](operations/troubleshooting/module-6.4-network-debugging.md) | tcpdump, ss, connection troubleshooting | 30-35 min |

#### 7. Shell Scripting (4 modules)
| Module | Description | Time |
|--------|-------------|------|
| [7.1 Bash Fundamentals](operations/shell-scripting/module-7.1-bash-fundamentals.md) | Variables, control flow, functions | 30-35 min |
| [7.2 Text Processing](operations/shell-scripting/module-7.2-text-processing.md) | grep, sed, awk, jq, pipelines | 30-35 min |
| [7.3 Practical Scripts](operations/shell-scripting/module-7.3-practical-scripts.md) | Error handling, logging, common patterns | 25-30 min |
| [7.4 DevOps Automation](operations/shell-scripting/module-7.4-devops-automation.md) | kubectl scripts, CI/CD helpers, operational tools | 30-35 min |

---

## Why This Track Matters

### For Kubernetes

- **Namespaces and cgroups ARE containers** — Understanding these demystifies container technology
- **Network policies use iptables/eBPF** — Can't debug networking without understanding the stack
- **Security contexts use capabilities/AppArmor/seccomp** — Pod security requires Linux security knowledge
- **Resource limits are cgroup configurations** — Understanding cgroups explains Kubernetes resource management

### For DevOps

- **CI/CD runs on Linux** — Your pipelines execute shell commands
- **Automation requires shell scripting** — You'll write bash whether you like it or not
- **Troubleshooting needs system understanding** — Can't fix what you don't understand
- **Performance tuning needs kernel knowledge** — Optimization requires understanding the system

### For SRE

- **Incident response requires deep system knowledge** — The 3am call needs expertise
- **Performance analysis uses Linux tools** — USE method depends on Linux metrics
- **Capacity planning needs resource understanding** — Memory, CPU, I/O all work differently

---

## Prerequisites

**None.** This track IS the prerequisite for everything else.

Start here if you're new to Linux or want to fill gaps in your knowledge.

---

## Recommended After

After completing this track, you'll be ready for:

- **[Cloud Native 101](../prerequisites/cloud-native-101/README.md)** — Apply Linux knowledge to cloud-native concepts
- **[CKA/CKAD/CKS certifications](../k8s/README.md)** — Linux knowledge is essential for these exams
- **[Platform Engineering Track](../platform/README.md)** — Build on the foundation

---

## Progress Tracking

### Foundations
- [ ] System Essentials (4 modules)
- [ ] Container Primitives (4 modules)
- [ ] Networking (4 modules)

### Security
- [ ] Hardening (4 modules)

### System Administration
- [ ] System Administration (4 modules)

### Operations
- [ ] Performance (4 modules)
- [ ] Troubleshooting (4 modules)
- [ ] Shell Scripting (4 modules)

---

## Contributing

Found an issue? Have a suggestion? This track is part of [KubeDojo](https://github.com/krisztiankoos/kubedojo), an open-source Kubernetes curriculum.
