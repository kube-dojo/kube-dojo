# System Essentials

> **The foundation of Linux knowledge. Understanding these concepts makes everything else click.**

## Overview

This section covers the core building blocks of Linux that every DevOps/SRE professional needs to understand. These aren't just theoretical concepts—they're the reality you interact with every time you run a command or debug an issue.

## Modules

| # | Module | Description | Time |
|---|--------|-------------|------|
| 1.1 | [Kernel & Architecture](module-1.1-kernel-architecture.md) | Kernel vs userspace, modules, why containers share kernels | 25-30 min |
| 1.2 | [Processes & systemd](module-1.2-processes-systemd.md) | PIDs, process lifecycle, signals, systemctl, units | 30-35 min |
| 1.3 | [Filesystem Hierarchy](module-1.3-filesystem-hierarchy.md) | /etc, /var, /proc, /sys, inodes, mount points | 25-30 min |
| 1.4 | [Users & Permissions](module-1.4-users-permissions.md) | UIDs, groups, rwx, setuid, sudo, least privilege | 25-30 min |

## Why This Section Matters

Every single thing you do on Linux touches these concepts:

- **Running a container?** The kernel provides process isolation
- **Debugging a crash?** Understanding processes helps you investigate
- **Checking configuration?** You need to know where files live
- **Running kubectl?** Permissions determine what you can do

## Prerequisites

None. This is where you start.

## Key Takeaways

After completing this section, you'll understand:

1. How the Linux kernel manages everything (and why containers share it)
2. What processes are and how they're managed by systemd
3. Where everything lives in Linux (and why it's organized that way)
4. How users and permissions protect systems

## Related Sections

- **Next**: [Container Primitives](../container-primitives/README.md) — Apply these concepts to containerization
- **Uses**: These concepts underpin everything in the track
