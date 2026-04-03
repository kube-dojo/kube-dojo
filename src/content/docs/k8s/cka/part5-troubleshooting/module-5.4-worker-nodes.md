---
title: "Module 5.4: Worker Node Failures"
slug: k8s/cka/part5-troubleshooting/module-5.4-worker-nodes
sidebar:
  order: 5
lab:
  id: cka-5.4-worker-nodes
  url: https://killercoda.com/kubedojo/scenario/cka-5.4-worker-nodes
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical for cluster operations
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 5.1 (Methodology), Module 1.1 (Cluster Architecture)

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Diagnose** worker node NotReady status by checking kubelet, container runtime, and network
- **Fix** kubelet failures caused by configuration errors, certificate expiry, and resource pressure
- **Recover** a node from disk pressure, memory pressure, and PID pressure conditions
- **Drain** and cordon nodes safely during maintenance while respecting PodDisruptionBudgets

---

## Why This Module Matters

Worker nodes are where your applications actually run. When a node fails, pods get evicted or stuck, services become unavailable, and applications suffer. Understanding how to diagnose and fix worker node issues is essential for maintaining cluster health and application availability.

> **The Factory Floor Analogy**
>
> If the control plane is management, worker nodes are the factory floor. The kubelet is the floor supervisor - if they're out, nothing gets done. The container runtime is the machinery - if it breaks, production stops. Node resources (CPU, memory, disk) are the raw materials - run out, and the factory grinds to a halt.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Diagnose NotReady node status
- Troubleshoot kubelet issues
- Fix container runtime problems
- Handle node resource exhaustion
- Recover from node network failures

---

## Did You Know?

- **Node heartbeat every 10 seconds**: kubelet reports to API server every 10s. After 40s of no heartbeat, node is marked Unknown
- **Pod eviction after 5 minutes**: By default, pods on NotReady nodes are evicted after 5 minutes (pod-eviction-timeout)
- **Three conditions trigger pressure**: MemoryPressure, DiskPressure, PIDPressure - any true causes scheduling issues
- **kubelet is not a pod**: Unlike control plane components, kubelet runs as a systemd service, not a container

---

## Part 1: Node Status Overview

### 1.1 Understanding Node Conditions

```
┌──────────────────────────────────────────────────────────────┐
│                    NODE CONDITIONS                            │
│                                                               │
│   Condition          Healthy    Meaning                       │
│   ─────────────────────────────────────────────────────────  │
│   Ready              True       Node is healthy, can run pods │
│   MemoryPressure     False      Memory is sufficient          │
│   DiskPressure       False      Disk space is sufficient      │
│   PIDPressure        False      Process IDs are available     │
│   NetworkUnavailable False      Network is configured         │
│                                                               │
│   Any unhealthy condition → scheduling problems               │
│   Ready=False or Unknown → node is NotReady                   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Checking Node Status

```bash
# Quick status
k get nodes

# Detailed conditions
k describe node <node-name> | grep -A 10 Conditions

# All nodes with conditions
k get nodes -o custom-columns='NAME:.metadata.name,READY:.status.conditions[?(@.type=="Ready")].status,REASON:.status.conditions[?(@.type=="Ready")].reason'

# Check for resource pressure
k describe node <node-name> | grep -E "MemoryPressure|DiskPressure|PIDPressure"
```

### 1.3 Node Status States

| Status | Meaning | Common Causes |
|--------|---------|---------------|
| Ready | Healthy and accepting pods | Normal operation |
| NotReady | Unhealthy | kubelet down, network issues |
| Unknown | No heartbeat received | Node unreachable, kubelet crashed |
| SchedulingDisabled | Cordoned | Manual cordon or maintenance |

---

## Part 2: kubelet Troubleshooting

### 2.1 kubelet Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    KUBELET RESPONSIBILITIES                   │
│                                                               │
│   ┌──────────────────────────────────────────────────────┐   │
│   │                      kubelet                          │   │
│   │                                                       │   │
│   │  • Registers node with API server                    │   │
│   │  • Watches for pod assignments                       │   │
│   │  • Manages container lifecycle (via runtime)         │   │
│   │  • Reports node/pod status                           │   │
│   │  • Handles probes (liveness, readiness)              │   │
│   │  • Mounts volumes                                    │   │
│   │  • Runs static pods                                  │   │
│   │                                                       │   │
│   └──────────────────────────────────────────────────────┘   │
│                                                               │
│   If kubelet fails → Node goes NotReady → Pods stop working  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Checking kubelet Status

```bash
# SSH to the node first
ssh <node-name>

# Check kubelet service status
sudo systemctl status kubelet

# Check if kubelet is running
ps aux | grep kubelet

# Check kubelet logs
sudo journalctl -u kubelet -f

# Check recent kubelet errors
sudo journalctl -u kubelet --since "10 minutes ago" | grep -i error
```

### 2.3 Common kubelet Issues

| Issue | Symptom | Diagnosis | Fix |
|-------|---------|-----------|-----|
| kubelet stopped | Node NotReady | `systemctl status kubelet` | `systemctl start kubelet` |
| kubelet crash loop | Node flapping | `journalctl -u kubelet` | Fix config, check logs |
| Wrong config | Can't start | Error in logs | Fix `/var/lib/kubelet/config.yaml` |
| Can't reach API | NotReady | Network timeout in logs | Check network, firewall |
| Certificate issues | TLS errors | Cert errors in logs | Renew certs |
| Container runtime down | Can't create pods | Runtime errors | Fix containerd/docker |

### 2.4 Fixing kubelet Issues

**kubelet not running**:
```bash
# Start kubelet
sudo systemctl start kubelet

# Enable on boot
sudo systemctl enable kubelet

# Check status
sudo systemctl status kubelet
```

**kubelet configuration issues**:
```bash
# Check kubelet config file
cat /var/lib/kubelet/config.yaml

# Check kubelet flags
cat /etc/systemd/system/kubelet.service.d/10-kubeadm.conf

# After fixing config, reload and restart
sudo systemctl daemon-reload
sudo systemctl restart kubelet
```

**kubelet certificate issues**:
```bash
# Check certificate paths
cat /var/lib/kubelet/config.yaml | grep -i cert

# Verify certificates exist
ls -la /var/lib/kubelet/pki/

# For expired certs, may need to rejoin node
# On control plane: kubeadm token create --print-join-command
# On worker: kubeadm reset && kubeadm join ...
```

---

## Part 3: Container Runtime Troubleshooting

### 3.1 Container Runtime Overview

```
┌──────────────────────────────────────────────────────────────┐
│                CONTAINER RUNTIME STACK                        │
│                                                               │
│   kubelet                                                     │
│      │                                                        │
│      │ CRI (Container Runtime Interface)                     │
│      ▼                                                        │
│   containerd (or docker, cri-o)                              │
│      │                                                        │
│      │ OCI (Open Container Initiative)                       │
│      ▼                                                        │
│   runc (low-level runtime)                                   │
│      │                                                        │
│      ▼                                                        │
│   Linux kernel (cgroups, namespaces)                         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Checking Container Runtime

```bash
# Check containerd (most common)
sudo systemctl status containerd
sudo crictl info

# Check container runtime socket
ls -la /run/containerd/containerd.sock

# List containers with crictl
sudo crictl ps

# List images
sudo crictl images
```

### 3.3 Common Runtime Issues

| Issue | Symptom | Diagnosis | Fix |
|-------|---------|-----------|-----|
| containerd stopped | Pods ContainerCreating | `systemctl status containerd` | `systemctl start containerd` |
| Socket missing | kubelet errors | Check socket path | Restart containerd |
| Disk full | Container create fails | `df -h` | Clean up disk |
| Image pull fails | ImagePullBackOff | Check registry access | Fix registry auth |
| Resource exhausted | Random container failures | Check cgroups | Increase resources |

### 3.4 Fixing Runtime Issues

**containerd not running**:
```bash
# Start containerd
sudo systemctl start containerd

# Check status
sudo systemctl status containerd

# Check logs for issues
sudo journalctl -u containerd --since "10 minutes ago"
```

**crictl troubleshooting**:
```bash
# Configure crictl for containerd
cat <<EOF | sudo tee /etc/crictl.yaml
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 10
debug: false
EOF

# List all containers (including stopped)
sudo crictl ps -a

# Get container logs
sudo crictl logs <container-id>

# Inspect container
sudo crictl inspect <container-id>
```

---

## Part 4: Node Resource Exhaustion

### 4.1 Resource Pressure Conditions

```
┌──────────────────────────────────────────────────────────────┐
│                 RESOURCE PRESSURE TYPES                       │
│                                                               │
│   MEMORY PRESSURE                                             │
│   • Available memory below threshold                          │
│   • Triggers pod eviction                                     │
│   • Check: free -m, cat /proc/meminfo                        │
│                                                               │
│   DISK PRESSURE                                               │
│   • Disk usage above threshold                                │
│   • Triggers image garbage collection                        │
│   • Check: df -h                                              │
│                                                               │
│   PID PRESSURE                                                │
│   • Process IDs exhausted                                     │
│   • Can't fork new processes                                 │
│   • Check: cat /proc/sys/kernel/pid_max                      │
│                                                               │
│   When any pressure is True, node may not accept new pods     │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Diagnosing Resource Issues

```bash
# Check node conditions
k describe node <node> | grep -A 10 Conditions

# On the node - check memory
free -m
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable"

# Check disk
df -h
du -sh /var/lib/containerd/*  # Container storage
du -sh /var/log/*             # Log storage

# Check PIDs
cat /proc/sys/kernel/pid_max
ps aux | wc -l
```

### 4.3 Eviction Thresholds

Default kubelet eviction thresholds:
```yaml
evictionHard:
  memory.available: "100Mi"
  nodefs.available: "10%"
  nodefs.inodesFree: "5%"
  imagefs.available: "15%
```

When these thresholds are crossed:
1. Node condition set to True (e.g., MemoryPressure)
2. No new pods scheduled
3. Existing pods may be evicted

### 4.4 Fixing Resource Issues

**Memory pressure**:
```bash
# Find memory-hungry processes
ps aux --sort=-%mem | head -20

# Find pods using most memory
k top pods -A --sort-by=memory

# Options:
# 1. Kill unnecessary processes
# 2. Evict low-priority pods
# 3. Add more memory to node
```

**Disk pressure**:
```bash
# Find large files
sudo find / -type f -size +100M -exec ls -lh {} \;

# Clean up container images
sudo crictl rmi --prune

# Clean up old logs
sudo journalctl --vacuum-time=3d

# Clean up unused containers
sudo crictl rm $(sudo crictl ps -a -q --state exited)
```

**PID pressure**:
```bash
# Check current PID limit
cat /proc/sys/kernel/pid_max

# Increase limit temporarily
echo 65536 | sudo tee /proc/sys/kernel/pid_max

# Find processes by count
ps aux | awk '{print $1}' | sort | uniq -c | sort -rn | head
```

---

## Part 5: Node Network Issues

### 5.1 Node Network Requirements

```
┌──────────────────────────────────────────────────────────────┐
│                NODE NETWORK REQUIREMENTS                      │
│                                                               │
│   Node needs connectivity to:                                 │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ API Server     (port 6443)    - Required            │    │
│   │ Other nodes    (varies)       - For pod networking  │    │
│   │ DNS servers    (port 53)      - For name resolution │    │
│   │ Registry       (port 443)     - For pulling images  │    │
│   └─────────────────────────────────────────────────────┘    │
│                                                               │
│   Network failures → Node NotReady or Unknown                │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Diagnosing Network Issues

```bash
# Check basic connectivity
ping <api-server-ip>

# Check API server reachability
curl -k https://<api-server>:6443/healthz

# Check DNS
nslookup kubernetes.default.svc.cluster.local
cat /etc/resolv.conf

# Check firewall
sudo iptables -L -n
sudo firewall-cmd --list-all  # If using firewalld

# Check network interfaces
ip addr
ip route
```

### 5.3 Common Network Issues

| Issue | Symptom | Diagnosis | Fix |
|-------|---------|-----------|-----|
| Firewall blocking | Can't reach API | `telnet api-server 6443` | Open firewall ports |
| DNS failure | Name resolution fails | `nslookup` | Fix /etc/resolv.conf |
| IP address change | Node NotReady | Check IP in node spec | Reconfigure or rejoin |
| CNI plugin issues | Pod networking fails | Check CNI pods | Restart CNI, fix config |
| MTU mismatch | Intermittent failures | Check MTU settings | Align MTU values |

### 5.4 Required Ports

| Port | Protocol | Component | Purpose |
|------|----------|-----------|---------|
| 6443 | TCP | API Server | Kubernetes API |
| 10250 | TCP | kubelet | kubelet API |
| 10259 | TCP | kube-scheduler | Scheduler metrics |
| 10257 | TCP | kube-controller-manager | Controller metrics |
| 2379-2380 | TCP | etcd | Client and peer |
| 30000-32767 | TCP | NodePort | Service NodePorts |

---

## Part 6: Node Recovery Procedures

### 6.1 Recovery Decision Tree

```
┌──────────────────────────────────────────────────────────────┐
│                  NODE RECOVERY DECISION TREE                  │
│                                                               │
│   Node NotReady?                                              │
│        │                                                      │
│        ├── Can SSH to node?                                   │
│        │        │                                             │
│        │        ├── YES → Check kubelet, runtime, network     │
│        │        │                                             │
│        │        └── NO  → Check physical/VM, cloud console    │
│        │                                                      │
│        ├── kubelet running?                                   │
│        │        │                                             │
│        │        ├── YES → Check logs, certs, API connectivity │
│        │        │                                             │
│        │        └── NO  → Start kubelet                       │
│        │                                                      │
│        └── Still NotReady after fixes?                        │
│                 │                                             │
│                 └── Drain and rejoin node                     │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Draining a Node

```bash
# Drain node (evicts pods safely)
k drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Cordon only (prevent new pods)
k cordon <node-name>

# Uncordon (allow scheduling again)
k uncordon <node-name>
```

### 6.3 Rejoining a Node

If node needs to be completely reset:

```bash
# On the worker node
sudo kubeadm reset

# On control plane - generate new join token
kubeadm token create --print-join-command

# On worker - rejoin
sudo kubeadm join <api-server>:6443 --token <token> --discovery-token-ca-cert-hash <hash>
```

### 6.4 Removing a Node

```bash
# Drain first
k drain <node> --ignore-daemonsets --delete-emptydir-data

# Delete node from cluster
k delete node <node-name>

# On the node itself
sudo kubeadm reset
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Not checking kubelet first | Miss obvious issue | Always start with `systemctl status kubelet` |
| Ignoring node conditions | Miss resource pressure | Check all conditions, not just Ready |
| Deleting node before drain | Pod disruption | Always drain before delete |
| Forgetting DaemonSet pods | Drain fails | Use `--ignore-daemonsets` |
| Not checking runtime | Blame kubelet | Check containerd status too |
| Ignoring disk usage | Node degradation | Monitor disk, clean regularly |

---

## Quiz

### Q1: Node Heartbeat
How long after the last heartbeat does a node become Unknown?

<details>
<summary>Answer</summary>

**40 seconds**. kubelet sends heartbeats every 10 seconds. After 4 missed heartbeats (40s), the node-controller marks the node as Unknown. After 5 minutes (by default), pods on that node are scheduled for eviction.

</details>

### Q2: kubelet vs Static Pods
What's the key difference between kubelet and control plane components in terms of how they run?

<details>
<summary>Answer</summary>

**kubelet** runs as a **systemd service** on the host, while **control plane components** (API server, scheduler, controller manager, etcd) run as **static pods** managed by kubelet.

This means:
- kubelet: Check with `systemctl status kubelet`
- Control plane: Check with `crictl ps` or `k get pods -n kube-system`

</details>

### Q3: MemoryPressure
A node has MemoryPressure=True. What happens to new pods?

<details>
<summary>Answer</summary>

New pods will **not be scheduled** to this node. The scheduler considers node conditions when making placement decisions. Additionally, existing pods may be **evicted** to free memory, starting with BestEffort pods (no resource requests/limits), then Burstable, then Guaranteed.

</details>

### Q4: crictl vs kubectl
When should you use crictl instead of kubectl?

<details>
<summary>Answer</summary>

Use **crictl** when:
- kubelet or API server is down (kubectl won't work)
- Debugging container runtime issues
- Inspecting containers at the runtime level
- The node is NotReady

crictl talks directly to the container runtime (containerd), bypassing the Kubernetes API entirely.

</details>

### Q5: Drain vs Cordon
What's the difference between `kubectl drain` and `kubectl cordon`?

<details>
<summary>Answer</summary>

- **cordon**: Marks node as unschedulable (no new pods). Existing pods keep running.
- **drain**: Cordons the node AND evicts all pods (except DaemonSet pods). Prepares node for maintenance.

Use cordon for "soft" maintenance, drain for taking node offline.

</details>

### Q6: Container Runtime Socket
Where is the containerd socket typically located?

<details>
<summary>Answer</summary>

`/run/containerd/containerd.sock`

This is the Unix socket that kubelet uses to communicate with containerd via CRI. If this socket is missing or containerd isn't listening on it, kubelet can't manage containers.

Check with: `ls -la /run/containerd/containerd.sock`

</details>

---

## Hands-On Exercise: Node Troubleshooting Simulation

### Scenario

Practice diagnosing node issues using available commands.

### Prerequisites

- Access to a Kubernetes cluster
- SSH access to at least one worker node

### Task 1: Node Health Assessment

```bash
# Check all nodes
k get nodes -o wide

# Get detailed node information
k describe node <node-name>

# Check node conditions specifically
k get node <node-name> -o jsonpath='{.status.conditions[*].type}' | tr ' ' '\n'
```

### Task 2: kubelet Investigation

```bash
# SSH to a worker node
ssh <node>

# Check kubelet status
sudo systemctl status kubelet

# View recent kubelet logs
sudo journalctl -u kubelet --since "5 minutes ago" | tail -50

# Check kubelet configuration
cat /var/lib/kubelet/config.yaml | head -30
```

### Task 3: Container Runtime Check

```bash
# Check containerd status
sudo systemctl status containerd

# List running containers
sudo crictl ps

# Check container runtime info
sudo crictl info

# List images on node
sudo crictl images
```

### Task 4: Resource Assessment

```bash
# Check memory
free -m

# Check disk
df -h

# Check what's using resources
k top node <node-name>

# See allocated resources
k describe node <node-name> | grep -A 10 "Allocated resources"
```

### Task 5: Cordon and Uncordon (Safe)

```bash
# Cordon a node (prevents new scheduling)
k cordon <node-name>

# Verify it's unschedulable
k get node <node-name>

# Try to schedule a pod
k run test-pod --image=nginx
k get pods test-pod -o wide  # Should NOT be on cordoned node

# Uncordon
k uncordon <node-name>

# Cleanup
k delete pod test-pod
```

### Success Criteria

- [ ] Checked node conditions for all nodes
- [ ] Verified kubelet is running
- [ ] Verified containerd is running
- [ ] Assessed node resource usage
- [ ] Successfully cordoned and uncordoned a node

### Cleanup

Node should be uncordoned after exercise.

---

## Practice Drills

### Drill 1: Node Status Check (30 sec)
```bash
# Task: List all nodes with their status
k get nodes
```

### Drill 2: Node Conditions (1 min)
```bash
# Task: Check all conditions for a specific node
k describe node <node> | grep -A 10 Conditions
```

### Drill 3: kubelet Status (30 sec)
```bash
# Task: Check if kubelet is running (on node)
sudo systemctl status kubelet
```

### Drill 4: kubelet Logs (1 min)
```bash
# Task: View last 20 lines of kubelet logs
sudo journalctl -u kubelet -n 20
```

### Drill 5: Container Runtime Status (30 sec)
```bash
# Task: Check containerd and list containers
sudo systemctl status containerd
sudo crictl ps
```

### Drill 6: Resource Usage (1 min)
```bash
# Task: Check node resource usage
k top nodes
k describe node <node> | grep -A 5 "Allocated resources"
```

### Drill 7: Drain Node (1 min)
```bash
# Task: Safely drain a node
k drain <node> --ignore-daemonsets --delete-emptydir-data
```

### Drill 8: Disk Usage (30 sec)
```bash
# Task: Check disk usage on node
df -h
du -sh /var/lib/containerd/
```

---

## Next Module

Continue to [Module 5.5: Network Troubleshooting](../module-5.5-networking/) to learn how to diagnose and fix pod-to-pod, pod-to-service, and external connectivity issues.
