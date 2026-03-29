---
title: "Module 5.2: CPU & Scheduling"
slug: linux/operations/performance/module-5.2-cpu-scheduling
sidebar:
  order: 3
---
> **Linux Performance** | Complexity: `[MEDIUM]` | Time: 30-35 min

## Prerequisites

Before starting this module:
- **Required**: [Module 5.1: USE Method](../module-5.1-use-method/)
- **Required**: [Module 2.2: cgroups](../../foundations/container-primitives/module-2.2-cgroups/)
- **Helpful**: Understanding of processes and threads

---

## Why This Module Matters

When your pod gets "throttled" or applications seem slow despite available CPU, the scheduler is involved. Understanding how Linux schedules processes explains why Kubernetes CPU limits work the way they do.

Understanding CPU scheduling helps you:

- **Debug CPU throttling** — Why your pod runs slowly at "low" CPU
- **Set proper limits** — CPU limits vs requests in Kubernetes
- **Understand performance** — Why load average and CPU% tell different stories
- **Optimize workloads** — Right-size containers based on actual behavior

CPU limits in Kubernetes are more complex than "use X amount of CPU."

---

## Did You Know?

- **Linux uses the Completely Fair Scheduler (CFS)** — Since 2007, CFS replaced the O(1) scheduler. It uses red-black trees to ensure every process gets fair CPU time.

- **CPU "millicores" are a Kubernetes abstraction** — Linux doesn't know about millicores. Kubernetes translates `100m` into cgroup CPU shares and quotas.

- **Throttling happens in 100ms periods** — CFS enforces quotas in periods. A container with 100m (10% CPU) can burst for 10ms, then waits 90ms. This causes latency spikes.

- **Nice values range from -20 to 19** — Lower is higher priority. Only root can set negative nice. A nice difference of 1 means ~10% more/less CPU.

---

## CPU Fundamentals

### CPU Time Breakdown

```bash
# View CPU time categories
top -bn1 | grep "Cpu(s)"
# %Cpu(s):  5.2 us,  2.1 sy,  0.0 ni, 92.0 id,  0.5 wa,  0.0 hi,  0.2 si,  0.0 st

# What each means:
```

| Category | Meaning | High Value Indicates |
|----------|---------|---------------------|
| `us` | User - Application code | Application CPU usage |
| `sy` | System - Kernel code | System calls, drivers |
| `ni` | Nice - Low priority user | Nice'd processes running |
| `id` | Idle - Nothing to do | Unused CPU capacity |
| `wa` | I/O Wait - Waiting for disk | I/O bottleneck |
| `hi` | Hardware IRQ - Interrupts | High interrupt load |
| `si` | Software IRQ - Soft interrupts | Network/timer handling |
| `st` | Steal - VM overhead | Hypervisor stealing time |

### Understanding Load Average

```bash
# Show load average
uptime
# 10:23:45 up 5 days,  3 users,  load average: 2.15, 1.87, 1.42
#                                              1m    5m    15m

cat /proc/loadavg
# 2.15 1.87 1.42 3/245 12345
# load averages   running/total  last PID
```

**Load average** = processes wanting to run + processes waiting for I/O

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOAD AVERAGE                                  │
│                                                                  │
│  4-core system with load average of 4.0:                        │
│                                                                  │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                               │
│  │ P1  │ │ P2  │ │ P3  │ │ P4  │  ← 4 processes running        │
│  │CPU 0│ │CPU 1│ │CPU 2│ │CPU 3│                               │
│  └─────┘ └─────┘ └─────┘ └─────┘                               │
│  Load = 4.0 = Perfect utilization                               │
│                                                                  │
│  4-core system with load average of 8.0:                        │
│                                                                  │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                               │
│  │ P1  │ │ P2  │ │ P3  │ │ P4  │  ← 4 running                  │
│  │CPU 0│ │CPU 1│ │CPU 2│ │CPU 3│                               │
│  └─────┘ └─────┘ └─────┘ └─────┘                               │
│                                                                  │
│  Queue: [P5] [P6] [P7] [P8]      ← 4 waiting                   │
│                                                                  │
│  Load = 8.0 = 100% utilized + 4 waiting                        │
└─────────────────────────────────────────────────────────────────┘
```

### CPU Count

```bash
# Number of CPUs
nproc
# 4

# Detailed CPU info
lscpu
# CPU(s):              4
# Thread(s) per core:  2
# Core(s) per socket:  2
# Socket(s):           1

# Per-CPU info
cat /proc/cpuinfo | grep "processor\|model name" | head -8
```

---

## The Linux Scheduler

### Completely Fair Scheduler (CFS)

CFS is the default Linux scheduler. It tracks **virtual runtime** for each process—the amount of CPU time weighted by priority.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CFS SCHEDULER                                 │
│                                                                  │
│  Goal: Every process gets fair share of CPU                     │
│                                                                  │
│  Process with LOWEST vruntime runs next                         │
│                                                                  │
│  ┌─────────────────────────────────────────┐                    │
│  │          Red-Black Tree                  │                    │
│  │                                          │                    │
│  │             [P3: 5000]                   │ ← Highest vruntime│
│  │            /          \                  │                    │
│  │     [P1: 3000]    [P5: 4500]            │                    │
│  │      /     \                             │                    │
│  │ [P2: 2000] [P4: 2800]                   │                    │
│  │                                          │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                  │
│  Next to run: P2 (lowest vruntime = 2000)                       │
│                                                                  │
│  vruntime increases as process uses CPU                         │
│  Higher priority = vruntime increases slower                    │
└─────────────────────────────────────────────────────────────────┘
```

### Nice Values and Priority

```bash
# View process nice values
ps -eo pid,ni,comm | head -10
#   PID  NI COMMAND
#     1   0 systemd
#   123 -20 migration/0
#   456  19 backup

# Nice range: -20 (highest priority) to 19 (lowest priority)
# Default: 0

# Start process with nice value
nice -n 10 ./my-script.sh

# Change running process
renice 10 -p 1234

# Only root can set negative nice (higher priority)
sudo nice -n -10 ./critical-process
```

### Real-Time Scheduling

```bash
# Check scheduling policy
chrt -p 1234
# pid 1234's current scheduling policy: SCHED_OTHER
# pid 1234's current scheduling priority: 0

# Policies:
# SCHED_OTHER - Normal (CFS)
# SCHED_FIFO  - Real-time FIFO
# SCHED_RR    - Real-time Round Robin
# SCHED_BATCH - Batch processing
# SCHED_IDLE  - Very low priority

# Set real-time priority (careful!)
sudo chrt -f -p 50 1234
```

---

## CPU Metrics Deep Dive

### Per-CPU Statistics

```bash
# Per-CPU utilization
mpstat -P ALL 1
# 10:30:01  CPU    %usr   %sys  %idle  %iowait
# 10:30:02  all    15.2    3.1   80.5     1.2
# 10:30:02    0    20.0    5.0   74.0     1.0
# 10:30:02    1    10.0    2.0   87.0     1.0
# 10:30:02    2    18.0    3.0   78.0     1.0
# 10:30:02    3    13.0    2.0   83.0     2.0
```

### Context Switches

```bash
# System-wide context switches
vmstat 1
#  r  b   swpd   free  ...   in   cs
#  2  0      0 123456  ...  500 2000
#                            │    │
#                            │    └── Context switches/sec
#                            └── Interrupts/sec

# Per-process context switches
cat /proc/1234/status | grep ctxt
# voluntary_ctxt_switches:    1000
# nonvoluntary_ctxt_switches: 500

# Voluntary = Process yielded (I/O, sleep)
# Nonvoluntary = Preempted by scheduler
```

### Run Queue

```bash
# Processes in run queue
vmstat 1
#  r  b   swpd   free ...
#  4  0      0 123456 ...
#  │
#  └── Runnable processes

# Alternative
cat /proc/loadavg
# 4.00 3.50 3.00 2/150 12345
#                 │
#                 └── 2 currently running / 150 total
```

---

## Kubernetes CPU Limits

### How CPU Limits Work

```yaml
resources:
  requests:
    cpu: "100m"     # Guaranteed minimum
  limits:
    cpu: "500m"     # Maximum allowed
```

```
┌─────────────────────────────────────────────────────────────────┐
│                 KUBERNETES CPU TRANSLATION                       │
│                                                                  │
│  Kubernetes          Linux cgroups                              │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  cpu: "100m"    →    cpu.shares = 102                           │
│  (request)           (1024 * 0.1 = ~102)                        │
│                      Relative weight for scheduling             │
│                                                                  │
│  cpu: "500m"    →    cpu.cfs_quota_us = 50000                   │
│  (limit)             cpu.cfs_period_us = 100000                 │
│                      50ms of every 100ms period                 │
│                                                                  │
│  "1 CPU"        →    cpu.cfs_quota_us = 100000                  │
│                      Full period allowed                        │
│                                                                  │
│  "2 CPU"        →    cpu.cfs_quota_us = 200000                  │
│                      Can use 2 cores simultaneously             │
└─────────────────────────────────────────────────────────────────┘
```

### CPU Throttling

```bash
# Check container throttling
cat /sys/fs/cgroup/cpu/docker/<container-id>/cpu.stat
# nr_periods 1000
# nr_throttled 150
# throttled_time 30000000000

# Interpretation:
# 1000 periods (100ms each = 100 seconds)
# 150 throttled (15% of periods had throttling)
# 30 billion nanoseconds = 30 seconds throttled
```

**Throttling is binary** — either your container runs or waits. This causes latency spikes even at "low" CPU usage.

### CPU Shares vs Quotas

| Mechanism | Effect | When Applied |
|-----------|--------|--------------|
| **Shares** (requests) | Relative weight | Only under contention |
| **Quotas** (limits) | Hard cap | Always enforced |

```
┌─────────────────────────────────────────────────────────────────┐
│                    CPU SHARES                                    │
│                                                                  │
│  Pod A: 100m request = 102 shares                               │
│  Pod B: 200m request = 205 shares                               │
│                                                                  │
│  When both compete for CPU:                                     │
│  Pod A gets: 102/(102+205) = 33%                               │
│  Pod B gets: 205/(102+205) = 67%                               │
│                                                                  │
│  When only Pod A runs: Pod A can use 100%                       │
│  (Shares only matter during contention)                         │
├─────────────────────────────────────────────────────────────────┤
│                    CPU QUOTAS                                    │
│                                                                  │
│  Pod A: 500m limit = 50ms per 100ms                            │
│                                                                  │
│  Even if CPU is idle, Pod A is capped at 50%                   │
│  This causes throttling (latency spikes)                       │
└─────────────────────────────────────────────────────────────────┘
```

### Viewing Container CPU

```bash
# Pod CPU usage
kubectl top pod

# Detailed metrics (if metrics-server installed)
kubectl get --raw /apis/metrics.k8s.io/v1beta1/pods

# cgroup files for a container
# Find container ID first
crictl ps
crictl inspect <container-id> | grep cgroupsPath
cat /sys/fs/cgroup/cpu/<path>/cpu.stat
```

---

## Tuning and Troubleshooting

### High Load Average

```bash
# Diagnosis steps:
# 1. Is it CPU or I/O?
vmstat 1
#  r  b    ← r=CPU, b=I/O
#  8  0    ← High r = CPU bound
#  2  6    ← High b = I/O bound

# 2. What's using CPU?
top -bn1 | head -15
ps aux --sort=-%cpu | head -10

# 3. Check for throttling
cat /sys/fs/cgroup/cpu/*/cpu.stat | grep throttled
```

### CPU Throttling Debug

```bash
# Find throttled containers
for cg in /sys/fs/cgroup/cpu/kubepods/*/pod*/; do
  throttled=$(cat $cg/cpu.stat 2>/dev/null | grep nr_throttled | awk '{print $2}')
  if [ "$throttled" -gt 0 ] 2>/dev/null; then
    echo "$cg: $throttled throttled periods"
  fi
done

# Solution: Increase CPU limit or remove limit
# Note: Some orgs remove CPU limits entirely
```

### Latency from Throttling

```
┌─────────────────────────────────────────────────────────────────┐
│                    THROTTLING LATENCY                            │
│                                                                  │
│  Container with 100m limit (10ms per 100ms period):             │
│                                                                  │
│  Request arrives at 0ms                                          │
│  Processing starts at 0ms                                        │
│  CPU quota exhausted at 10ms                                     │
│  WAIT until 100ms (new period)                                  │
│  Processing continues at 100ms                                  │
│  Response at 120ms                                               │
│                                                                  │
│  Without throttling: 20ms latency                               │
│  With throttling: 120ms latency (6x slower)                     │
│                                                                  │
│  This is why low CPU% can still cause latency issues!           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Setting CPU limits too low | Throttling causes latency | Test under load, consider removing limits |
| Confusing requests and limits | Overcommitment or waste | Requests for scheduling, limits for protection |
| Ignoring iowait | Blaming CPU when disk is slow | Check wa% in top |
| Not checking per-CPU | One core saturated, others idle | Use mpstat -P ALL |
| Assuming nice values matter | Containers use cgroups, not nice | Set via resource requests |
| High context switches | Too many threads | Reduce thread count |

---

## Quiz

### Question 1
What's the difference between CPU requests and limits in Kubernetes?

<details>
<summary>Show Answer</summary>

**Requests** (cpu.shares):
- Minimum guaranteed CPU
- Used for scheduling decisions
- Only enforced during contention
- Relative weight, not absolute

**Limits** (cpu.quota):
- Maximum CPU allowed
- Always enforced (hard cap)
- Causes throttling when exceeded
- Can be higher than node CPU (burstable)

Example: `requests: 100m, limits: 500m` means guaranteed 10% during contention, but can burst to 50%.

</details>

### Question 2
Why can a container with low CPU utilization still experience latency?

<details>
<summary>Show Answer</summary>

**CPU throttling** happens in periods (default 100ms).

A container with 10% CPU limit (100m):
- Gets 10ms of CPU time
- Then waits 90ms for next period
- Even if only using 5ms, gets throttled after 10ms

A request arriving at 9ms might:
1. Start processing
2. Get throttled at 10ms
3. Wait until 100ms
4. Complete at 105ms

Total latency: 96ms instead of 5ms.

Average utilization looks low, but p99 latency is terrible.

</details>

### Question 3
What does a load average of 2.0 on a 2-core system indicate?

<details>
<summary>Show Answer</summary>

**Perfect utilization** — both cores are fully busy but nothing is waiting.

Load average interpretation:
- < cores: Idle capacity
- = cores: Full utilization, no wait
- > cores: Saturation (queue forming)

2.0 on 2 cores = optimal use. Going above 2.0 means processes start queuing.

Note: Load average includes I/O wait, so 2.0 could also mean 1 running + 1 waiting for disk.

</details>

### Question 4
How does CFS ensure fair CPU distribution?

<details>
<summary>Show Answer</summary>

CFS tracks **virtual runtime (vruntime)** for each process:

1. All processes start with vruntime = 0
2. As process uses CPU, vruntime increases
3. Process with **lowest** vruntime runs next
4. Higher priority = vruntime increases slower

This ensures:
- Every process eventually runs
- Priority affects rate, not exclusion
- No process starves (vruntime always increases)

CFS uses a red-black tree for O(log n) scheduling decisions.

</details>

### Question 5
How do you identify CPU throttling in a Kubernetes pod?

<details>
<summary>Show Answer</summary>

Check cgroup statistics:

```bash
# Find container cgroup path
cat /sys/fs/cgroup/cpu/kubepods/*/pod<uid>/<container-id>/cpu.stat

# Look for:
nr_periods 10000        # Total periods
nr_throttled 500        # Periods with throttling
throttled_time 50000000 # Nanoseconds throttled
```

If `nr_throttled` is high relative to `nr_periods`, the container is being throttled.

Solutions:
1. Increase CPU limit
2. Remove CPU limit entirely
3. Optimize application CPU usage

</details>

---

## Hands-On Exercise

### Understanding CPU Scheduling

**Objective**: Observe CPU scheduling, priority, and throttling behavior.

**Environment**: Linux system with root access

#### Part 1: CPU Metrics

```bash
# 1. Check CPU info
nproc
lscpu | grep -E "CPU|Thread|Core|Socket"

# 2. View current load
uptime
cat /proc/loadavg

# 3. CPU time breakdown
top -bn1 | head -8

# 4. Per-CPU stats
mpstat -P ALL 1 3
```

#### Part 2: Nice Values

```bash
# 1. Start two CPU-intensive processes
nice -n 19 sha256sum /dev/zero &
PID1=$!

nice -n 0 sha256sum /dev/zero &
PID2=$!

# 2. Check their nice values
ps -o pid,ni,%cpu,comm -p $PID1,$PID2
sleep 3
ps -o pid,ni,%cpu,comm -p $PID1,$PID2

# 3. Notice the CPU% difference
# nice 0 gets more CPU than nice 19

# 4. Clean up
kill $PID1 $PID2
```

#### Part 3: Observe Scheduling

```bash
# 1. Context switches
vmstat 1 5
# Watch the 'cs' column

# 2. Run queue depth
# r column shows runnable processes
vmstat 1 5

# 3. Create load
stress --cpu 4 --timeout 30 &

# 4. Watch load average change
watch -n 1 uptime
# Wait 1-2 minutes to see 1min average rise
```

#### Part 4: cgroup CPU (if available)

```bash
# 1. Create a cgroup (if not in container)
sudo mkdir /sys/fs/cgroup/cpu/test

# 2. Set CPU quota (10%)
echo 10000 | sudo tee /sys/fs/cgroup/cpu/test/cpu.cfs_quota_us
echo 100000 | sudo tee /sys/fs/cgroup/cpu/test/cpu.cfs_period_us

# 3. Run process in cgroup
echo $$ | sudo tee /sys/fs/cgroup/cpu/test/cgroup.procs
sha256sum /dev/zero &
PID=$!

# 4. Check throttling
sleep 5
cat /sys/fs/cgroup/cpu/test/cpu.stat

# 5. Clean up
kill $PID
echo $$ | sudo tee /sys/fs/cgroup/cpu/cgroup.procs
sudo rmdir /sys/fs/cgroup/cpu/test
```

#### Part 5: Container CPU (Docker/Podman)

```bash
# 1. Run container with CPU limit
docker run -d --name cpu-test --cpus="0.5" nginx sleep 3600

# 2. Check cgroup settings
docker exec cpu-test cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us
docker exec cpu-test cat /sys/fs/cgroup/cpu/cpu.cfs_period_us

# 3. Generate load inside container
docker exec cpu-test sh -c "sha256sum /dev/zero &"

# 4. Check throttling after a minute
sleep 60
docker exec cpu-test cat /sys/fs/cgroup/cpu/cpu.stat

# 5. Clean up
docker rm -f cpu-test
```

### Success Criteria

- [ ] Identified CPU count and load average
- [ ] Observed nice value effect on CPU allocation
- [ ] Monitored context switches and run queue
- [ ] Understood cgroup CPU quota mechanism
- [ ] Observed CPU throttling in containers

---

## Key Takeaways

1. **Load average ≠ CPU utilization** — Load includes I/O wait

2. **CFS ensures fairness** — Lowest vruntime runs next

3. **Requests = shares, Limits = quotas** — Different mechanisms

4. **Throttling causes latency** — Even at low average CPU

5. **Check per-CPU stats** — One saturated core hides in averages

---

## What's Next?

In **Module 5.3: Memory Management**, you'll learn how Linux manages memory, what happens when it runs out, and how Kubernetes memory limits differ from CPU limits.

---

## Further Reading

- [CFS Scheduler Documentation](https://www.kernel.org/doc/Documentation/scheduler/sched-design-CFS.txt)
- [CPU Bandwidth Control](https://www.kernel.org/doc/Documentation/scheduler/sched-bwc.txt)
- [Kubernetes CPU Management](https://kubernetes.io/docs/tasks/administer-cluster/cpu-management-policies/)
- [For the Love of God, Stop Using CPU Limits](https://home.robusta.dev/blog/stop-using-cpu-limits)
