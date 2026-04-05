---
title: "Module 2.2: Control Groups (cgroups)"
slug: linux/foundations/container-primitives/module-2.2-cgroups
sidebar:
  order: 3
---
> **Linux Foundations** | Complexity: `[MEDIUM]` | Time: 30-35 min

## Prerequisites

Before starting this module:
- **Required**: [Module 2.1: Linux Namespaces](../module-2.1-namespaces/)
- **Helpful**: Understanding of CPU and memory concepts

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Configure** cgroup resource limits for CPU, memory, and I/O
- **Explain** how Kubernetes requests and limits map to cgroup settings
- **Diagnose** OOMKilled containers by reading cgroup memory accounting
- **Compare** cgroups v1 and v2 and explain why the industry is migrating to v2

---

## Why This Module Matters

While namespaces provide **isolation** (what a process can see), cgroups provide **limits** (how much a process can use).

Every Kubernetes resource request and limit, every Docker memory constraint, every container CPU throttle—they all use cgroups.

Understanding cgroups helps you:

- **Debug OOM kills** — Why did my container get killed?
- **Tune resource limits** — Set appropriate requests and limits
- **Understand throttling** — Why is my container slow but not using 100% CPU?
- **Troubleshoot systemd** — Services use cgroups too

When a pod is evicted for memory pressure or your application is mysteriously slow, cgroups are involved.

---

## Did You Know?

- **cgroups were originally developed by Google** engineers Paul Menage and Rohit Seth in 2006. They wanted a way to control resource usage in their massive data centers.

- **Kubernetes memory limits trigger the OOM killer** — When a container exceeds its memory limit, the kernel's Out-Of-Memory killer terminates it. There's no gradual slowdown—it's sudden death.

- **CPU limits use CFS bandwidth control** — Your container might use less than 100% CPU even under load because it's being "throttled" for using too much CPU in a given period.

- **cgroups v2 is now the default** — Kubernetes 1.25+ uses cgroups v2 by default. It provides a unified hierarchy and better resource control, but some older tools may not support it.

---

## What Are cgroups?

**Control groups (cgroups)** organize processes into hierarchical groups whose resource usage can be limited, monitored, and controlled.

```
┌─────────────────────────────────────────────────────────────────┐
│                          CGROUP HIERARCHY                        │
│                                                                  │
│                            / (root)                              │
│                               │                                  │
│              ┌────────────────┼────────────────┐                 │
│              ▼                ▼                ▼                 │
│        ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│        │ system   │    │  user    │    │ kubepods │             │
│        └────┬─────┘    └────┬─────┘    └────┬─────┘             │
│             │               │               │                    │
│        ┌────┴────┐         ...        ┌─────┴─────┐             │
│        ▼         ▼                    ▼           ▼             │
│   ┌─────────┐ ┌─────────┐      ┌──────────┐ ┌──────────┐        │
│   │  sshd   │ │ docker  │      │ burstable│ │guaranteed│        │
│   │ 512 MB  │ │ 2 GB    │      │          │ │          │        │
│   └─────────┘ └─────────┘      └────┬─────┘ └────┬─────┘        │
│                                     │            │               │
│                                 pod-abc...   pod-xyz...          │
└─────────────────────────────────────────────────────────────────┘
```

### What cgroups Control

| Resource | Controller | What It Controls |
|----------|------------|------------------|
| CPU | cpu, cpuset | CPU time, CPU cores |
| Memory | memory | RAM usage, swap |
| I/O | io (v2), blkio (v1) | Disk bandwidth |
| PIDs | pids | Number of processes |
| Network | net_cls, net_prio | Network priority (limited) |
| Devices | devices | Access to devices |
| Freezer | freezer | Suspend/resume processes |

---

## cgroups v1 vs v2

> **Critical: Kubernetes 1.35+ Requires cgroup v2**
>
> Starting with Kubernetes 1.35 (December 2025), cgroup v1 support is **disabled by default**. The kubelet will fail to start on cgroup v1 nodes. If you're running Kubernetes, you must be on cgroup v2. Check with: `stat -fc %T /sys/fs/cgroup` — must return `cgroup2fs`. Affected OS versions: CentOS 7, RHEL 7, Ubuntu 18.04.

### The Problem with v1

cgroups v1 had separate hierarchies per controller:

```
# v1: Multiple hierarchies (messy)
/sys/fs/cgroup/
├── cpu/            ← CPU hierarchy
│   └── docker/
│       └── container1/
├── memory/         ← Memory hierarchy
│   └── docker/
│       └── container1/
└── pids/           ← PIDs hierarchy
    └── docker/
        └── container1/
```

Each controller had its own tree, leading to:
- Complex management
- Inconsistent process groupings
- No single place to see a process's resources

### v2: Unified Hierarchy

```
# v2: Single hierarchy (clean)
/sys/fs/cgroup/
└── docker/
    └── container1/
        ├── cpu.max          ← CPU settings
        ├── memory.max       ← Memory settings
        └── pids.max         ← PIDs settings
```

### Check Your Version

```bash
# Check cgroup version
mount | grep cgroup

# v1 shows: cgroup on /sys/fs/cgroup/cpu type cgroup
# v2 shows: cgroup2 on /sys/fs/cgroup type cgroup2

# Or check directly
cat /sys/fs/cgroup/cgroup.controllers 2>/dev/null && echo "v2" || echo "v1 or mixed"
```

### Feature Comparison

| Feature | v1 | v2 |
|---------|----|----|
| Hierarchy | Multiple (per controller) | Single (unified) |
| Process membership | Can be in different groups per controller | One group for all controllers |
| Memory pressure | Not available | Available (memory.pressure) |
| I/O control | Limited (blkio) | Better (io) |
| Kubernetes support | Legacy | Default (1.25+) |

---

## Memory Limits

### How Memory Limits Work

> **Stop and think**: If a Java application with a 512MB heap size is placed in a container with a 512MB cgroup memory limit, it will almost certainly be OOMKilled. Why? Consider what else inside the container's environment or the JVM process requires memory beyond just the allocated heap space.

```
┌────────────────────────────────────────────────────────────────┐
│                    CONTAINER MEMORY                             │
│                                                                 │
│  memory.max = 512MB                                            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Used: 400MB                           │   │
│  │  ███████████████████████████████████████░░░░░░░░░░░░░░  │   │
│  │  ◄──────── 400MB ─────────►│◄── 112MB ──►              │   │
│  │              Used           │   Available                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  If usage reaches 512MB → OOM KILL                             │
└────────────────────────────────────────────────────────────────┘
```

### The OOM Killer

When memory exceeds the limit:

1. Kernel invokes OOM killer
2. Process is immediately killed (SIGKILL)
3. Container/pod is restarted
4. No graceful shutdown possible

```bash
# Check if OOM killed
dmesg | grep -i "oom"
# or
journalctl -k | grep -i "oom"

# In Kubernetes
kubectl describe pod <pod-name> | grep -i oom
# Look for: OOMKilled
```

### Viewing Memory cgroup

```bash
# v2
cat /sys/fs/cgroup/user.slice/user-1000.slice/memory.max
cat /sys/fs/cgroup/user.slice/user-1000.slice/memory.current

# For a container (path varies)
# Find container cgroup
find /sys/fs/cgroup -name "memory.max" 2>/dev/null | head -5
```

### Memory Accounting

```bash
# v2 memory statistics
cat /sys/fs/cgroup/user.slice/memory.stat

# Key values:
# anon - anonymous memory (heap, stack)
# file - file cache
# kernel - kernel memory
# shmem - shared memory
```

---

## CPU Limits

### How CPU Limits Work

> **Pause and predict**: If you set a CPU limit of `0.5` (500m) for a single-threaded Node.js application, and it receives a massive spike in traffic, what will happen to the response time? Will the container crash, or will something else occur at the kernel level?

Unlike memory, CPU doesn't trigger kills—it **throttles**.

```
┌────────────────────────────────────────────────────────────────┐
│                    CPU CFS BANDWIDTH                            │
│                                                                 │
│  Period: 100ms                                                  │
│  Quota: 50ms (50% of one CPU = "500m" in Kubernetes)           │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Time: 0ms                                    100ms     │    │
│  │ ├─────────────────────────────────────────────────────►│    │
│  │                                                         │    │
│  │ ████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░ │    │
│  │ ◄──── Running (50ms) ────►│◄──── Throttled ────────► │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  After using 50ms in 100ms period → throttled until next period│
└────────────────────────────────────────────────────────────────┘
```

### Kubernetes CPU Units

| Kubernetes | Meaning | cgroup quota/period |
|------------|---------|---------------------|
| 1 | 1 full CPU | 100000/100000 |
| 500m | 0.5 CPU (50%) | 50000/100000 |
| 100m | 0.1 CPU (10%) | 10000/100000 |
| 2 | 2 full CPUs | 200000/100000 |

### Viewing CPU Throttling

```bash
# v2 CPU controls
cat /sys/fs/cgroup/cpu.max
# Format: quota period
# "50000 100000" = 50ms per 100ms = 50%

# Check throttling stats (v2)
cat /sys/fs/cgroup/cpu.stat
# Look for:
# nr_throttled - number of times throttled
# throttled_usec - total time throttled
```

### CPU Throttling in Practice

```bash
# Run a CPU-intensive process
stress --cpu 1 --timeout 30 &

# Watch throttling (in another terminal)
watch -n1 'cat /sys/fs/cgroup/user.slice/cpu.stat | grep throttled'
```

---

## Kubernetes and cgroups

### Resource Requests vs Limits

```yaml
resources:
  requests:        # Scheduling guarantee
    memory: "256Mi"
    cpu: "250m"
  limits:          # Hard limit (cgroup)
    memory: "512Mi"
    cpu: "500m"
```

| Setting | Purpose | cgroup Behavior |
|---------|---------|-----------------|
| request.memory | Scheduling | Not directly enforced by cgroup |
| request.cpu | Scheduling | Sets cpu.weight (shares) |
| limit.memory | Hard limit | memory.max |
| limit.cpu | Throttling | cpu.max |

### QoS Classes and cgroups

```
┌─────────────────────────────────────────────────────────────────┐
│                    KUBEPODS CGROUP HIERARCHY                     │
│                                                                  │
│  /sys/fs/cgroup/kubepods.slice/                                 │
│  │                                                               │
│  ├── kubepods-burstable.slice/          ← Burstable pods        │
│  │   └── kubepods-burstable-pod<uid>/   ← Individual pod        │
│  │       └── cri-containerd-<id>/       ← Container             │
│  │                                                               │
│  ├── kubepods-besteffort.slice/         ← BestEffort pods       │
│  │   └── ...                                                     │
│  │                                                               │
│  └── kubepods-pod<uid>/                 ← Guaranteed pods       │
│      └── ...                            (directly under kubepods)│
└─────────────────────────────────────────────────────────────────┘
```

### Finding Pod cgroups

```bash
# Find cgroup for a container
# 1. Get container ID
docker ps
crictl ps

# 2. Find its cgroup
cat /proc/<container-pid>/cgroup

# 3. Or search
find /sys/fs/cgroup -name "*<container-id-prefix>*" 2>/dev/null
```

---

## systemd and cgroups

systemd uses cgroups extensively for service management.

### Viewing systemd Slices

```bash
# See cgroup hierarchy
systemd-cgls

# Resource usage by service
systemd-cgtop

# Specific service resources
systemctl show docker.service | grep -E "(Memory|CPU)"
```

### Setting Limits via systemd

```ini
# /etc/systemd/system/myapp.service
[Service]
MemoryMax=512M
CPUQuota=50%
TasksMax=100

# Apply
systemctl daemon-reload
systemctl restart myapp
```

### Service Resource Control

```bash
# Set runtime limit
sudo systemctl set-property docker.service MemoryMax=2G

# View current settings
systemctl show docker.service -p MemoryMax
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No memory limit | Pod can consume all node memory | Always set memory limits |
| Limit = Request | No burst capacity | Set limit > request for burstable |
| Ignoring throttling | Slow application, blame network | Check cpu.stat for throttling |
| OOM without logs | Don't know why container died | Check dmesg, set proper logging |
| Not understanding v1 vs v2 | Tooling differences | Check version, use appropriate paths |
| Too low CPU limit | Constant throttling | Monitor and adjust based on usage |

---

## Quiz

### Question 1
You are deploying a critical database pod and set its memory request to 4GB and memory limit to 8GB. During a sudden traffic spike, the pod's memory usage reaches 6GB, and the Node it is running on experiences severe memory pressure, running out of allocatable RAM. What will the kubelet and the kernel do to this pod, and why?

<details>
<summary>Show Answer</summary>

The pod is at risk of being evicted or OOMKilled, despite being under its 8GB limit. **Why?** When a node experiences memory pressure, Kubernetes evicts pods to reclaim memory. Because the pod is using more than its 4GB *request* (it's using 6GB), it falls into the "Burstable" QoS class and is actively consuming resources beyond its guaranteed baseline. The kernel's OOM killer or the kubelet eviction manager will target pods that exceed their requests before touching pods that are strictly within their requested boundaries. Setting requests equal to limits (Guaranteed QoS) would have protected this critical database from being the first victim.

</details>

### Question 2
Your team deploys a video encoding application. The developers complain that the application is running slowly, but when they check monitoring tools, the container is only using 40% of the node's CPU capacity. They insist the node must have a hardware issue. How do you explain this behavior using cgroups?

<details>
<summary>Show Answer</summary>

The container is experiencing CPU throttling enforced by the Completely Fair Scheduler (CFS) bandwidth control in cgroups. **Why?** The deployment likely has a CPU limit set (e.g., `limit: 400m` on a 1-core node). The cgroup translates this limit into a specific quota of CPU time allowed per period (usually 100ms). Once the video encoder uses up its allotted quota (e.g., 40ms) within that period, the kernel pauses the process until the next period begins. This manifests as the application artificially running slowly without ever reaching 100% host CPU utilization, as the cgroup restricts its access to the physical cores.

</details>

### Question 3
A developer sets a memory limit of 512MB for a Python data processing container. The application attempts to load a 600MB dataset entirely into RAM. The developer expects the application to throw a catchable `MemoryError` exception so they can log it and gracefully exit. Instead, the container simply vanishes and restarts. What kernel mechanism caused this, and why didn't the application catch the error?

<details>
<summary>Show Answer</summary>

The kernel's Out-Of-Memory (OOM) killer intervened and terminated the container abruptly. **Why?** cgroup memory limits represent a hard boundary enforced by the Linux kernel, not the language runtime. When the container's total memory footprint attempts to exceed the `memory.max` value set in its cgroup, the kernel immediately sends a `SIGKILL` signal to the process. A `SIGKILL` cannot be caught, blocked, or handled by the application code (unlike a soft memory exception thrown by a runtime). Therefore, the Python process never gets a chance to log the error or gracefully shut down before the container is restarted by Kubernetes or Docker.

</details>

### Question 4
You are upgrading your Kubernetes cluster to a version that enforces cgroups v2. A legacy monitoring daemonset in your cluster fails to start, complaining that it cannot find `/sys/fs/cgroup/memory/memory.usage_in_bytes`. What architectural change between cgroups v1 and v2 is causing this failure?

<details>
<summary>Show Answer</summary>

The monitoring tool is failing because cgroups v2 uses a unified hierarchy, whereas cgroups v1 used separate hierarchies for every resource controller. **Why?** In cgroups v1, CPU, memory, and PIDs were mounted in different directory trees (e.g., `/sys/fs/cgroup/memory/...` and `/sys/fs/cgroup/cpu/...`), allowing a process to belong to different groups for different resources. cgroups v2 simplifies this by placing a process in exactly one cgroup path (e.g., `/sys/fs/cgroup/user.slice/...`), and all resource controllers (memory, CPU, I/O) are managed via files in that single directory (like `memory.current` and `cpu.max`). The legacy tool is hardcoded to look for the v1 split-directory structure and specific v1 filenames, which no longer exist in a v2 environment.

</details>

### Question 5
You are investigating a node where a specific Docker container is mysteriously running very slowly. You want to manually check the raw kernel values to see if the container's CPU quota has been artificially restricted. Walk through the exact steps you would take on the host system to find this container's specific CPU limit configuration in cgroups v2.

<details>
<summary>Show Answer</summary>

You must first find the process ID (PID) of the container and then trace it to its cgroup path. **Why?** Containers are just isolated processes to the kernel, so their cgroup configurations are tied to their PID. First, you would run `docker inspect <container_name> --format '{{.State.Pid}}'` to get the host PID. Next, you read `/proc/<PID>/cgroup` to discover the exact unified cgroup path assigned to that process (e.g., `0::/system.slice/docker-<id>.scope`). Finally, you append that path to the cgroup mount point (`/sys/fs/cgroup`) and inspect the `cpu.max` file (e.g., `cat /sys/fs/cgroup/system.slice/docker-<id>.scope/cpu.max`) to see the raw quota and period values causing the throttling.

</details>

---

## Hands-On Exercise

### Exploring cgroups

**Objective**: Understand cgroup structure, limits, and throttling.

**Environment**: Linux system with cgroups (v1 or v2)

#### Part 1: Identify cgroup Version

```bash
# 1. Check mount type
mount | grep cgroup

# 2. Check for v2
if [ -f /sys/fs/cgroup/cgroup.controllers ]; then
    echo "cgroups v2"
    cat /sys/fs/cgroup/cgroup.controllers
else
    echo "cgroups v1 or mixed"
    ls /sys/fs/cgroup/
fi
```

#### Part 2: Explore cgroup Hierarchy

```bash
# 1. Your process's cgroup
cat /proc/$$/cgroup

# 2. View hierarchy (v2)
ls /sys/fs/cgroup/

# 3. See systemd slices
systemd-cgls | head -50

# 4. Resource usage
systemd-cgtop
```

#### Part 3: Memory cgroup

```bash
# 1. Find memory settings (v2)
cat /sys/fs/cgroup/user.slice/memory.max 2>/dev/null || \
cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null

# 2. Current usage
cat /sys/fs/cgroup/user.slice/memory.current 2>/dev/null || \
cat /sys/fs/cgroup/memory/memory.usage_in_bytes 2>/dev/null

# 3. Memory statistics
cat /sys/fs/cgroup/user.slice/memory.stat 2>/dev/null | head -10
```

#### Part 4: CPU cgroup

```bash
# 1. CPU settings (v2)
cat /sys/fs/cgroup/user.slice/cpu.max 2>/dev/null

# 2. CPU statistics
cat /sys/fs/cgroup/user.slice/cpu.stat 2>/dev/null

# 3. Check for throttling
cat /sys/fs/cgroup/user.slice/cpu.stat 2>/dev/null | grep throttled
```

#### Part 5: Create a cgroup (v2, requires root)

```bash
# 1. Create a test cgroup
sudo mkdir /sys/fs/cgroup/test-cgroup

# 2. Enable controllers
echo "+memory +cpu" | sudo tee /sys/fs/cgroup/test-cgroup/cgroup.subtree_control

# 3. Set memory limit (100MB)
echo "104857600" | sudo tee /sys/fs/cgroup/test-cgroup/memory.max

# 4. Check it
cat /sys/fs/cgroup/test-cgroup/memory.max

# 5. Move current shell to this cgroup
echo $$ | sudo tee /sys/fs/cgroup/test-cgroup/cgroup.procs

# 6. Verify
cat /proc/$$/cgroup

# 7. Check memory usage
cat /sys/fs/cgroup/test-cgroup/memory.current

# 8. Exit shell to leave cgroup, then cleanup
exit
sudo rmdir /sys/fs/cgroup/test-cgroup
```

### Success Criteria

- [ ] Identified cgroup version on your system
- [ ] Explored the cgroup hierarchy
- [ ] Found memory and CPU settings
- [ ] Understood throttling statistics
- [ ] (Optional) Created and tested a custom cgroup

---

## Key Takeaways

1. **cgroups limit resources** — While namespaces isolate views, cgroups enforce limits

2. **Memory limits are fatal** — Exceeding them triggers OOM kill (SIGKILL)

3. **CPU limits cause throttling** — Process is paused, not killed

4. **v2 is the future** — Single hierarchy, better features, Kubernetes default

5. **Kubernetes uses cgroups** — Every limit you set becomes a cgroup configuration

---

## What's Next?

In **Module 2.3: Capabilities & LSMs**, you'll learn how Linux provides fine-grained privilege control beyond just root/non-root.

---

## Further Reading

- [cgroups v2 Documentation](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)
- [Red Hat cgroups Guide](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/managing_monitoring_and_updating_the_kernel/using-cgroups-v2-to-control-distribution-of-cpu-time-for-applications_managing-monitoring-and-updating-the-kernel)
- [Kubernetes Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Understanding CFS Bandwidth Throttling](https://engineering.indeedblog.com/blog/2019/12/cpu-throttling-regression-fix/)