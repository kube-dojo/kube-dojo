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

## Why This Module Matters

In 2018, a major online retailer experienced a catastrophic global outage during their peak holiday sales event. The root cause was not a complex network intrusion, a massive denial-of-service attack, or database corruption. Instead, it was a simple, subtle memory leak in a third-party logging daemon deployed as a DaemonSet across all their worker nodes. As the daemon quietly consumed system memory over several days, individual worker nodes sequentially exhausted their physical capacities. Each node independently hit `MemoryPressure`, abruptly stopped accepting new pods, and began aggressively evicting existing production workloads to protect its own kernel integrity.

Because the underlying issue was not immediately diagnosed or properly isolated by the operations team, the Kubernetes scheduler desperately scrambled to place the newly evicted pods onto the remaining "healthy" nodes. This cascading failure created a massive "thundering herd" effect across the infrastructure. The surviving worker nodes were instantaneously overwhelmed by the flood of rescheduled pods, causing them to rapidly run out of memory as well. Within minutes, the entire e-commerce platform collapsed, resulting in six hours of downtime and an estimated $15 million in lost revenue. This incident underscores a brutal truth in distributed systems: a localized node failure, if left unchecked and improperly managed, can quickly metastasize into a global cluster outage.

Worker nodes are the fundamental workhorses of your Kubernetes cluster. They provide the CPU, memory, and networking primitives where your applications actually execute. When a node fails, the applications running on it suffer immediately. Understanding how to definitively diagnose and fix worker node issues—whether it is a crashed kubelet agent, an unresponsive container runtime, or critical resource exhaustion—is essential for maintaining cluster health. This module prepares you to jump into a failing node, interpret the low-level system signals, and confidently restore service before the cascading effects take hold of your infrastructure.

> **The Factory Floor Analogy**
>
> If the control plane is management, worker nodes are the factory floor. The kubelet is the floor supervisor - if they are out, nothing gets done. The container runtime is the heavy machinery - if it breaks, production stops. Node resources (CPU, memory, disk) are the raw materials - run out, and the factory grinds to a halt.

## What You'll Learn

- **Diagnose** the root cause of `NotReady` and `Unknown` node states using systematic debugging techniques and system logs.
- **Evaluate** node resource pressure conditions and implement immediate remediation strategies to prevent cascading failures across the cluster.
- **Debug** kubelet and container runtime integration failures by analyzing systemd service states, journalctl logs, and CRI socket configurations.
- **Implement** safe node recovery and maintenance procedures, including cordoning, draining, and component restarts while respecting workload disruption budgets.
- **Design** eviction strategies that account for taint-based eviction and node-pressure soft and hard thresholds.

## Did You Know?

- **10-second heartbeats**: The kubelet reports its node status to the API server every 10 seconds. If 40 seconds pass without a heartbeat, the node is marked `Unknown`.
- **5-minute eviction threshold**: By default, pods running on a `NotReady` node are tolerated for exactly 300 seconds (5 minutes) before the control plane initiates eviction.
- **15 percent disk threshold**: The kubelet automatically triggers `DiskPressure` and begins garbage collecting unused container images when the node's root filesystem drops below 15% available space.
- **65536 PID limit**: In many default Linux distributions configured for Kubernetes, the `pid_max` limit is historically set to 32768, which can easily be exhausted by rogue microservices, causing `PIDPressure`.

---

## Part 1: Node Status Overview

Before diving into the command line, it is critical to understand how Kubernetes thinks about node health. The Kubernetes control plane does not actively poll the worker nodes; instead, it relies on a push-based mechanism. The `kubelet` agent running on each worker node is responsible for periodically evaluating the node's health and pushing a status update (a heartbeat) back to the API server. The Node Controller, running inside the `kube-controller-manager` on the control plane, monitors these heartbeats. If the heartbeats stop, or if the kubelet explicitly reports a problem, the Node Controller changes the node's status to reflect the failure.

To diagnose a node, you must first interrogate the API server to see what it believes the node's state is. You can start with a broad overview and then drill down into the specific conditions of a problematic node.

A Node is marked `Ready=True` when it is schedulable and fully functional. It is marked `Ready=False` when it is known to be unhealthy. However, if the node controller has not received a status update for the default node-monitor grace interval, the node is marked as `Ready=Unknown`.

Under the hood, Kubernetes controller manager defaults include a `node-monitor-period` of 5s and a `node-monitor-grace-period` of 50s for node liveness tracking. This means the Node Controller checks the node's status every 5 seconds. If a node fails to report back within 50 seconds, its status automatically transitions to Unknown. After a node is unreachable for the default eviction timeout (which is 5 minutes), the node is treated as unhealthy long enough to start API-initiated pod eviction handling.

The node's status is expressed through a set of boolean flags. A healthy node expects `Ready` to be `True`, while all pressure conditions (`MemoryPressure`, `DiskPressure`, `PIDPressure`) and `NetworkUnavailable` must be `False`. Any deviation indicates a degraded state.

Architecturally, we can visualize the relationship between these conditions and the overall node readiness as follows:

```mermaid
graph TD
    A[Node Conditions] --> B{Ready?}
    B -->|True| C[Healthy, can run pods]
    B -->|False/Unknown| D[NotReady, scheduling problems]
    A --> E[Resource Pressures]
    E --> F[MemoryPressure]
    E --> G[DiskPressure]
    E --> H[PIDPressure]
    E --> I[NetworkUnavailable]
    F -.->|True| D
    G -.->|True| D
    H -.->|True| D
    I -.->|True| D
```

When you query the node status, you will typically see one of the following states. Understanding the distinction between `NotReady` and `Unknown` is particularly important for troubleshooting.

| Status | Meaning | Common Causes |
|--------|---------|---------------|
| Ready | Healthy and accepting pods | Normal operation |
| NotReady | Unhealthy | kubelet down, network issues |
| Unknown | No heartbeat received | Node unreachable, kubelet crashed |
| SchedulingDisabled | Cordoned | Manual cordon or maintenance |

Here are the primary commands for inspecting node status from the control plane perspective:

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

> **Stop and think**: If a node transitions to the `Unknown` state, does that mean the applications running on it have crashed? 
> *Think about the separation of concerns between the control plane and the runtime before moving on.*

---

## Part 2: Taint-Based Evictions and Throttling

When a node transitions to a not-ready or unreachable state, Kubernetes applies specific taints to the node object to drive scheduling and eviction behaviors. Specifically, when a node is not-ready or unreachable, Kubernetes applies taints `node.kubernetes.io/not-ready` and `node.kubernetes.io/unreachable` with `NoSchedule` and `NoExecute` effects for pod scheduling and eviction behavior. 

To ensure pods are not immediately evicted during brief network partitions, Kubernetes adds default tolerations (without any user intent required) for these node failure taints with `tolerationSeconds: 300`. This aligns perfectly with the 5-minute eviction timeout. Only explicitly set toleration seconds on a pod specification will override that default.

From Kubernetes v1.29 onward, taint-based eviction is handled entirely by the `taint-eviction-controller`. Cluster operators can disable this behavior by explicitly omitting it via the controller-manager `--controllers` flag, though this is rarely recommended for standard clusters.

To prevent catastrophic cascading failures during massive network outages or data center partitions, the control plane employs strict eviction throttles. The default eviction throttles are configured as `node-eviction-rate=0.1` pods per second and `secondary-node-eviction-rate=0.01` pods per second. Furthermore, the controller protects the cluster using an `unhealthy-zone-threshold=0.55` and a `large-cluster-size-threshold=50`. If more than 55 percent of the nodes in a zone become unhealthy, and the cluster has more than 50 nodes, the eviction rate is aggressively reduced to the secondary rate to prevent overwhelming the remaining healthy nodes.

Understanding these mechanics allows operators to correctly diagnose why pods are lingering on broken nodes instead of immediately failing over to healthy ones.

---

## Part 3: The kubelet and Container Runtime Integration

The `kubelet` is the most critical Kubernetes component running on a worker node. It is the primary node agent, the direct representative of the control plane on the factory floor. If the kubelet is not functioning, the node is effectively severed from the cluster, regardless of whether the physical server is perfectly healthy.

The kubelet does not actually run containers itself; it delegates that responsibility to a Container Runtime via the Container Runtime Interface (CRI). If the container runtime crashes, hangs, or corrupts its local storage, the kubelet will be unable to spin up new pods or retrieve the status of existing ones. Note that the kubelet runs as a native systemd service directly on the host OS, while control plane components (API server, scheduler, etc.) typically run as static pods managed by the kubelet. If the kubelet crashes, the container runtime keeps the existing static pods running independently.

Here is a structural view of the kubelet's responsibilities and the consequences of its failure:

```mermaid
flowchart TD
    K[kubelet] --> R[Registers node with API server]
    K --> W[Watches for pod assignments]
    K --> M[Manages container lifecycle via runtime]
    K --> S[Reports node/pod status]
    K --> H[Handles probes: liveness, readiness]
    K --> V[Mounts volumes]
    K --> P[Runs static pods]
    K -.->|Fails| N[Node goes NotReady]
    N -.->|Result| X[Pods stop working or face eviction]
```

When a node is `NotReady`, your very first step should be to bypass Kubernetes entirely, SSH directly into the affected node, and check the health of the kubelet service using the Linux system manager, `systemd`.

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

Based on the output of the commands above, you can categorize the failure into one of several common buckets. 

| Issue | Symptom | Diagnosis | Fix |
|-------|---------|-----------|-----|
| kubelet stopped | Node NotReady | `systemctl status kubelet` | `systemctl start kubelet` |
| kubelet crash loop | Node flapping | `journalctl -u kubelet` | Fix config, check logs |
| Wrong config | Can't start | Error in logs | Fix `/var/lib/kubelet/config.yaml` |
| Can't reach API | NotReady | Network timeout in logs | Check network, firewall |
| Certificate issues | TLS errors | Cert errors in logs | Renew certs |
| Container runtime down | Can't create pods | Runtime errors | Fix containerd/docker |

If the kubelet is simply stopped (perhaps due to an accidental administrative command or an abrupt system restart where the service wasn't enabled), starting it is straightforward:

```bash
# Start kubelet
sudo systemctl start kubelet

# Enable on boot
sudo systemctl enable kubelet

# Check status
sudo systemctl status kubelet
```

More often, the kubelet is in a crash loop due to a configuration error. The kubelet's configuration is typically split between a YAML file and a set of systemd drop-in arguments. A typo in either will prevent the daemon from starting.

```bash
# Check kubelet config file
cat /var/lib/kubelet/config.yaml

# Check kubelet flags
cat /etc/systemd/system/kubelet.service.d/10-kubeadm.conf

# After fixing config, reload and restart
sudo systemctl daemon-reload
sudo systemctl restart kubelet
sudo systemctl status kubelet  # Verify service started
```

Another pernicious issue is certificate expiration. The kubelet authenticates to the API server using client certificates. If these expire (usually after one year in a kubeadm-provisioned cluster), the API server will reject the kubelet's heartbeats, and the node will drop offline silently.

```bash
# Check certificate paths
cat /var/lib/kubelet/config.yaml | grep -i cert

# Verify certificates exist
ls -la /var/lib/kubelet/pki/

# For expired certs, may need to rejoin node
# On control plane: kubeadm token create --print-join-command
# On worker: kubeadm reset && kubeadm join ...
```

The flow of instructions down the container runtime stack looks like this:

```mermaid
flowchart TD
    K[kubelet] -->|CRI - gRPC via unix socket| C[containerd / cri-o]
    C -->|OCI - JSON spec| R[runc / crun - low-level runtime]
    R -->|System Calls| L[Linux kernel: cgroups, namespaces]
```

To troubleshoot the runtime, we use `crictl`, a CLI tool specifically designed for CRI-compatible runtimes. It is invaluable because it allows you to inspect the state of containers directly on the node without needing the Kubernetes API server to be reachable.

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

Runtime issues often manifest as pods stuck in the `ContainerCreating` state, or as cryptic CRI integration errors inside the kubelet logs.

| Issue | Symptom | Diagnosis | Fix |
|-------|---------|-----------|-----|
| containerd stopped | Pods ContainerCreating | `systemctl status containerd` | `systemctl start containerd` |
| Socket missing | kubelet errors | Check socket path | Restart containerd |
| Disk full | Container create fails | `df -h` | Clean up disk |
| Image pull fails | ImagePullBackOff | Check registry access | Fix registry auth |
| Resource exhausted | Random container failures | Check cgroups | Increase resources |

If containerd has crashed, restarting it via systemd is the immediate remediation:

```bash
# Start containerd
sudo systemctl start containerd

# Check status
sudo systemctl status containerd

# Check logs for issues
sudo journalctl -u containerd --since "10 minutes ago"
```

If you need to dig deeper into why a specific container is failing to start, configuring and using `crictl` is your best path forward. Ensure `crictl` knows where your CRI socket is located by writing a quick config file.

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

Worker nodes possess finite physical resources. When a node begins to run out of memory, disk space, or process IDs, the kubelet detects this via `cAdvisor` (Container Advisor, which is embedded in the kubelet) and asserts a resource pressure condition.

Default hard node-pressure eviction thresholds include `memory.available<100Mi || <5%`, `nodefs.available<10%`, `nodefs.inodesFree<5%`, and `imagefs.available<15% || imagefs.inodesFree<5%`. These thresholds define the critical red line; once crossed, the node acts defensively to prevent complete system lockup.

Node pressure evictions are enforced directly by the kubelet. Crucially, because these evictions are local emergency measures to save the node from locking up, they bypass PodDisruptionBudgets entirely. Furthermore, in severe eviction situations, the kubelet can ignore the per-pod `terminationGracePeriodSeconds` to reclaim resources instantly. 

To prevent the node from oscillating between healthy and pressured states—often referred to as flapping—node pressure eviction uses soft and hard thresholds combined with a default 5-minute `eviction-transition-period`. This period ensures the pressure signal is sustained before full eviction protocols are enacted. Note that as of Kubernetes v1.35, custom thresholds for the `containerfs.available` hard eviction threshold are not supported. Operators must rely on the default configurations or focus their custom thresholds on `nodefs` and `imagefs`.

```mermaid
mindmap
  root((Resource Pressure))
    Memory
      Available memory below threshold
      Triggers pod eviction
      Check: free -m
    Disk
      Usage above threshold
      Triggers image GC
      Check: df -h
    PID
      Process IDs exhausted
      Cannot fork processes
      Check: pid_max
```

When diagnosing resource exhaustion, you must check both the Kubernetes API's view of the node and the raw operating system metrics.

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

The kubelet determines when a node is under pressure based on configured eviction thresholds. These are defined in the kubelet's configuration YAML.

```yaml
evictionHard:
  memory.available: "100Mi"
  nodefs.available: "10%"
  nodefs.inodesFree: "5%"
  imagefs.available: "15%"
```

When these thresholds are crossed, the kubelet acts defensively:
1. Node condition set to True (e.g., `MemoryPressure=True`).
2. The scheduler stops assigning new pods to the node.
3. The kubelet begins evicting existing pods to reclaim resources, starting with `BestEffort` pods.

> **Pause and predict**: If a runaway pod is consuming all the memory on a node, and the kubelet decides to evict it, what happens to the pod's data if it was using an `emptyDir` volume? 
> *Think about the ephemeral nature of local storage before proceeding.*

To fix memory pressure, you need to identify the culprit and intervene:

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

For disk pressure, the solution is aggressive cleanup. A node with a completely full disk will often completely freeze up, requiring a hard reboot.

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

PID pressure is an insidious problem. The Linux kernel limits the maximum number of Process IDs that can exist simultaneously. If a container forks processes rapidly without cleaning them up (a fork bomb), the node will hit its PID limit, preventing any new processes (including basic shell commands) from running.

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

Even if the kubelet is healthy and resources are abundant, a node must have robust network connectivity to function within the cluster. It must be able to reach the API server to send heartbeats, reach other nodes for overlay networking, and reach container registries to pull images.

```mermaid
flowchart LR
    Node -->|port 6443| API[API Server]
    Node -->|varies based on CNI| Nodes[Other Nodes]
    Node -->|port 53| DNS[DNS Servers]
    Node -->|port 443| Reg[Container Registry]
    style API stroke:#f66,stroke-width:2px
```

When diagnosing a network partition, use standard Linux networking tools directly from the affected worker node to trace the connection failure.

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

Common network issues range from aggressive firewall rules dropping packets to asymmetric routing configurations causing silent timeouts.

| Issue | Symptom | Diagnosis | Fix |
|-------|---------|-----------|-----|
| Firewall blocking | Can't reach API | `telnet api-server 6443` | Open firewall ports |
| DNS failure | Name resolution fails | `nslookup` | Fix /etc/resolv.conf |
| IP address change | Node NotReady | Check IP in node spec | Reconfigure or rejoin |
| CNI plugin issues | Pod networking fails | Check CNI pods | Restart CNI, fix config |
| MTU mismatch | Intermittent failures | Check MTU settings | Align MTU values |

Familiarize yourself with the default ports required for Kubernetes components to communicate securely.

| Port | Protocol | Component | Purpose |
|------|----------|-----------|---------|
| 6443 | TCP | API Server | Kubernetes API |
| 10250 | TCP | kubelet | kubelet API |
| 10259 | TCP | kube-scheduler | Scheduler metrics |
| 10257 | TCP | kube-controller-manager | Controller metrics |
| 2379-2380 | TCP | etcd | Client and peer |
| 30000-32767 | TCP | NodePort | Service NodePorts |

---

## Part 6: Node Shutdown and Recovery Procedures

When you have exhausted your troubleshooting options and need to perform deep maintenance on a node, you must follow safe recovery procedures. A chaotic recovery approach causes more downtime than the initial failure.

Kubernetes recognizes that nodes must sometimes be rebooted or taken offline for maintenance. Graceful node shutdown is documented as a core feature, boasting Linux support from v1.21 and Windows support from v1.34. By default, the graceful-shutdown knobs are set to a zero-duration (`shutdownGracePeriod=0s` and `shutdownGracePeriodCriticalPods=0s`). When a node entering shutdown is detected, it is instantly marked `NotReady` with scheduling blocked for new pods.

To provide more nuanced control, pod-priority-aware graceful shutdown allows critical workloads to terminate cleanly before best-effort pods. This priority-aware mechanism is a versioned feature path; it was introduced as alpha in v1.24 and has graduated to beta in v1.35, offering refined control over shutdown sequencing.

However, system crashes do not always provide a warning. For non-graceful node shutdown, there is documented behavior to attach a `node.kubernetes.io/out-of-service` taint. When this taint is applied, the controller-manager can forcefully detach node volumes after the timeout window, bypassing normal safe-detach protocols, unless that timeout behavior is explicitly disabled.

```mermaid
flowchart TD
    A{Node NotReady?} -->|Yes| B{Can SSH to node?}
    B -->|YES| C{kubelet running?}
    B -->|NO| D[Check physical/VM, cloud console]
    C -->|YES| E[Check logs, certs, API connectivity]
    C -->|NO| F[Start kubelet]
    E --> G{Still NotReady after fixes?}
    F --> G
    G -->|Yes| H[Drain and rejoin node]
```

Before rebooting a node or ripping out its configuration, you must safely remove the workloads it is hosting. The `cordon` command marks the node as unschedulable, and the `drain` command safely evicts all running pods (respecting PodDisruptionBudgets and graceful termination periods). You must include `--ignore-daemonsets` because DaemonSet pods cannot be evicted, and `--delete-emptydir-data` to authorize the loss of ephemeral local volumes.

```bash
# Drain node (evicts pods safely)
k drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Cordon only (prevent new pods)
k cordon <node-name>

# Uncordon (allow scheduling again)
k uncordon <node-name>
```

If the node's local configuration is entirely corrupted (e.g., messed up certificates or network configurations), the fastest path to recovery is often to wipe the node's Kubernetes state and rejoin it to the cluster from scratch.

```bash
# On the worker node
sudo kubeadm reset -f

# On control plane - generate new join token
kubeadm token create --print-join-command

# On worker - rejoin
sudo kubeadm join <api-server>:6443 --token <token> --discovery-token-ca-cert-hash <hash>
```

If a node has suffered catastrophic hardware failure and will never return, you must clean it out of the API server to prevent the cluster from waiting for it forever.

```bash
# Drain first
k drain <node> --ignore-daemonsets --delete-emptydir-data

# Delete node from cluster
k delete node <node-name>
k get nodes  # Verify node is removed

# On the node itself
sudo kubeadm reset -f
```

---

## Common Mistakes

When troubleshooting worker nodes, panic often leads to rushed commands that exacerbate the problem. Avoid these common pitfalls:

| Mistake | Why | Fix |
|---------|-----|-----|
| Not checking kubelet first | Miss obvious issue | Always start with `systemctl status kubelet` |
| Ignoring node conditions | Miss resource pressure | Check all conditions, not just Ready |
| Deleting node before drain | Pod disruption | Always drain before delete |
| Forgetting DaemonSet pods | Drain fails | Use `--ignore-daemonsets` |
| Not checking runtime | Blame kubelet | Check containerd status too |
| Ignoring disk usage | Node degradation | Monitor disk, clean regularly |
| Restarting without reload | Changes to systemd drop-ins do not take effect | Always run `systemctl daemon-reload` before restart |
| Skipping CNI checks | Assume node is broken when only pod networking is down | Verify CNI binary paths and configurations |

---

## Quiz

### Q1: Node Heartbeat
A worker node in your production cluster suffers a sudden, permanent network hardware failure. A junior engineer immediately checks the workloads and is confused why the pods on that node are still showing as `Running` rather than being instantly rescheduled. Walk through the exact timeline and control plane mechanisms that explain this delay.

<details>
<summary>Answer</summary>

First, the API server must miss 4 consecutive kubelet heartbeats (10s each), taking **40 seconds** before the Node Controller marks the node as `Unknown`. Second, when the node becomes `Unknown`, Kubernetes applies a `node.kubernetes.io/unreachable` taint. Pods have a default toleration of **300 seconds** (5 minutes) for this taint. Therefore, the control plane will intentionally wait ~5 minutes and 40 seconds before initiating pod eviction to avoid unnecessary thrashing during transient network blips.

</details>

### Q2: kubelet vs Static Pods
You discover a critical control plane component is failing on a master node, but when you run `crictl ps`, you see the container still running. You then check `systemctl status kubelet` and see it has crashed. What is the key difference between how the kubelet and control plane components run that explains this?

<details>
<summary>Answer</summary>

The **kubelet** runs as a **systemd service** directly on the host OS, while **control plane components** (API server, scheduler, etc.) run as **static pods** managed by the kubelet. If the kubelet crashes, the container runtime (containerd) keeps the existing static pods running independently. However, the kubelet is no longer around to report their status or apply updates, meaning Kubernetes loses management visibility over them.

</details>

### Q3: MemoryPressure
A node in your cluster is marked with `MemoryPressure=True`. A developer complains that their newly deployed pod is stuck in the `Pending` state. How does the node's condition directly affect the scheduler's behavior regarding new workloads?

<details>
<summary>Answer</summary>

New pods will **not be scheduled** to this node. The kube-scheduler actively filters out nodes that have resource pressure conditions set to True during its predicate evaluation phase. Additionally, the kubelet on that node will begin actively **evicting** existing pods to free up memory, starting with BestEffort pods, to prevent the entire node from freezing.

</details>

### Q4: crictl vs kubectl
During a severe API server outage, you need to inspect the logs of a failing ingress controller pod on a worker node. `kubectl` commands are timing out globally. What is the most effective approach to retrieve these logs?

<details>
<summary>Answer</summary>

You should use **crictl** directly on the worker node. Use `crictl ps` to find the container ID, and `crictl logs <container-id>` to view the output. Because crictl communicates directly with the container runtime (containerd) over the local Unix socket, it bypasses the Kubernetes API entirely, allowing you to debug even when the control plane is unreachable.

</details>

### Q5: Drain vs Cordon
You need to perform emergency kernel patching on a worker node. You execute `kubectl cordon <node-name>`. Five minutes later, you notice that all the original pods are still running on the node, blocking your maintenance window. What operational misunderstanding caused this delay?

<details>
<summary>Answer</summary>

The **cordon** command only marks the node as unschedulable (preventing new pods from arriving); it does not stop or move existing workloads. To properly clear a node for maintenance, you must use the **drain** command. Draining will cordon the node AND safely evict all existing pods (except DaemonSets, which you ignore with a flag) while respecting PodDisruptionBudgets.

</details>

### Q6: Container Runtime Socket
A worker node's kubelet fails to start. Reviewing the logs with `journalctl -u kubelet`, you see connection refused errors targeting `unix:///run/containerd/containerd.sock`. What is the most likely root cause, and how would you verify it before blindly restarting the kubelet?

<details>
<summary>Answer</summary>

The most likely root cause is that the **containerd** service has crashed or stopped, meaning the CRI socket (`/run/containerd/containerd.sock`) is no longer available for the kubelet to connect to. You should verify this by checking `systemctl status containerd` and running `ls -la /run/containerd/containerd.sock` before attempting to restart any services.

</details>

### Q7: Certificate Expiration
You notice a node flipping between `Ready` and `NotReady` states every few minutes. Upon inspecting the kubelet logs, you see repeated TLS handshake timeouts. The cluster was provisioned exactly one year ago. What is the most highly probable root cause of this flapping behavior?

<details>
<summary>Answer</summary>

The most highly probable root cause is an expired kubelet client certificate. By default, kubeadm-provisioned clusters issue kubelet client certificates with a one-year validity period. When the certificate expires, the kubelet can no longer authenticate with the API server to send heartbeats, causing total communication failure until the certificate is rotated or the node is rejoined.

</details>

---

## Hands-On Exercise: Node Troubleshooting Simulation

### Scenario

You are the on-call engineer. Monitoring has alerted you that a critical worker node is experiencing intermittent instability and resource spikes. You need to log into the environment, systematically diagnose the health of the node, inspect its core services, evaluate its resources, and safely prepare it for maintenance.

### Prerequisites

- Access to a Kubernetes cluster
- SSH access to at least one worker node

### Task 1: Node Health Assessment

Begin by evaluating the cluster-wide state from the perspective of the control plane. Identify the node you want to investigate.

<details>
<summary>Solution</summary>

```bash
# Check all nodes
k get nodes -o wide

# Get detailed node information
k describe node <node-name>

# Check node conditions specifically
k get node <node-name> -o jsonpath='{.status.conditions[*].type}' | tr ' ' '\n'
```
</details>

### Task 2: kubelet Investigation

Assume the node is showing signs of distress. SSH directly into the node and interrogate the primary agent.

<details>
<summary>Solution</summary>

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
</details>

### Task 3: Container Runtime Check

The kubelet relies entirely on the container runtime. Verify that containerd is healthy and properly managing containers.

<details>
<summary>Solution</summary>

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
</details>

### Task 4: Resource Assessment

The node is healthy at the service level, but it might be starving for resources. Check the physical resource consumption.

<details>
<summary>Solution</summary>

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
</details>

### Task 5: Cordon and Uncordon (Safe)

You have decided the node needs a reboot to clear a suspected memory leak. Safely cordon the node and verify that the scheduler respects your command.

<details>
<summary>Solution</summary>

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

# Verify node is schedulable again
k get node <node-name>

# Cleanup
k delete pod test-pod
```
</details>

### Success Criteria

- [ ] Checked node conditions for all nodes using jsonpath.
- [ ] Verified kubelet is running and inspected the systemd logs.
- [ ] Verified containerd is running and used crictl to list images.
- [ ] Assessed node resource usage at both the OS and cluster levels.
- [ ] Successfully cordoned a node, tested scheduler avoidance, and uncordoned it.

### Cleanup

Ensure the node is uncordoned and the test pod is deleted after completing the exercise.

---

## Practice Drills

Develop muscle memory for node troubleshooting by executing these rapid-fire drills.

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

Continue to [Module 5.5: Network Troubleshooting](../module-5.5-networking/) to learn how to diagnose and fix pod-to-pod, pod-to-service, and external connectivity issues that plague distributed systems.