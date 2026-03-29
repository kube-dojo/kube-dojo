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
What's the difference between memory request and limit in Kubernetes?

<details>
<summary>Show Answer</summary>

- **Request**: Used for **scheduling** — Kubernetes ensures the node has this much memory available. The container is guaranteed this amount.

- **Limit**: Used for **enforcement** — Kernel enforces via cgroup. If exceeded, the container is OOM killed.

Request affects where the pod lands; limit affects what happens if it uses too much.

</details>

### Question 2
Why might a container use less than 100% CPU even under load?

<details>
<summary>Show Answer</summary>

**CPU throttling**. If a CPU limit is set, the container can only use a certain amount of CPU time per period (typically 100ms). After using its quota, it's throttled until the next period.

Example: 500m limit = 50ms per 100ms period. Container runs at 100% for 50ms, then waits 50ms.

Check `cpu.stat` for `nr_throttled` and `throttled_usec`.

</details>

### Question 3
What happens when a container exceeds its memory limit?

<details>
<summary>Show Answer</summary>

The kernel's **OOM killer immediately terminates** the process (SIGKILL). There's no warning, no graceful shutdown, no chance to save state.

This is why:
- Memory limits must be appropriate for the workload
- Applications should handle restart gracefully
- Monitoring memory usage is critical

</details>

### Question 4
How is cgroups v2 different from v1?

<details>
<summary>Show Answer</summary>

Key differences:

| Aspect | v1 | v2 |
|--------|----|----|
| Hierarchy | Multiple (per controller) | Single unified |
| Process membership | Different groups per controller | One group |
| Memory pressure | Not available | Available |
| Management | Complex | Simpler |

v2 is now default in Kubernetes 1.25+.

</details>

### Question 5
Where would you find a container's cgroup settings?

<details>
<summary>Show Answer</summary>

```bash
# 1. Get container PID
docker inspect <container> --format '{{.State.Pid}}'

# 2. Find its cgroup
cat /proc/<pid>/cgroup

# 3. Access settings (v2 example)
cat /sys/fs/cgroup/<cgroup-path>/memory.max
cat /sys/fs/cgroup/<cgroup-path>/cpu.max
```

Or search:
```bash
find /sys/fs/cgroup -name "*<container-id>*" 2>/dev/null
```

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
