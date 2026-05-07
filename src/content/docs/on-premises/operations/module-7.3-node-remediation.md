---
revision_pending: true
title: "Module 7.3: Node Failure & Auto-Remediation"
slug: on-premises/operations/module-7.3-node-remediation
sidebar:
  order: 4
---

> **Complexity**: `[COMPLEX]` | Time: 60 minutes
>
> **Prerequisites**: [Module 7.2: Hardware Lifecycle & Firmware](../module-7.2-hardware-lifecycle/), [Module 1.3: Cluster Topology](/on-premises/planning/module-1.3-cluster-topology/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Implement** automated node remediation with MachineHealthChecks, BMC power cycling, and fencing for unresponsive nodes
2. **Configure** Node Problem Detector and custom health checks that detect hardware failures before they cascade
3. **Design** failure blast radius containment using rack-aware scheduling, topology spread constraints, and storage isolation
4. **Optimize** node failure recovery times by tuning taint tolerations, pod eviction timeouts, and Ceph recovery throttling

---

## Why This Module Matters

A single hardware fault can escalate quickly when there is no hardware-level alerting and workloads stay bound to a failed node until default node-failure tolerations expire.

If a failed node also hosts storage or participates in a busy replicated storage system, recovery traffic can stress the surrounding failure domain and turn one node failure into a wider availability problem.

Without automated remediation, on-call response and manual hardware recovery can stretch a node outage from minutes into a much longer incident.

With automated remediation and workload-specific eviction settings, many node failures can be handled much faster and with less manual intervention.

---

## What You'll Learn

- Machine Health Checks with Cluster API (CAPI)
- Node Problem Detector for kernel and runtime issues
- Automated reboot and reprovisioning strategies
- Spare node pools for instant replacement capacity
- Handling common hardware failures (RAM ECC, NIC flap, PSU, disk)
- Tuning eviction timeouts for bare metal

---

## Node Failure Detection Architecture

```
+---------------------------------------------------------------+
|          NODE FAILURE DETECTION & REMEDIATION STACK             |
|                                                                |
|  Layer 4: Remediation Controller (CAPI / custom)               |
|    Action: reboot, reprovision, or fence                       |
|         ^                                                      |
|         |  unhealthy signal                                    |
|  Layer 3: Machine Health Check (MHC)                           |
|    Rule: if condition X for Y minutes, remediate               |
|         ^                                                      |
|         |  node conditions                                     |
|  Layer 2: Node Problem Detector (NPD)                          |
|    Detects: kernel panics, OOM, filesystem corruption          |
|    Reports: Kubernetes node conditions                         |
|         ^                                                      |
|         |  system signals                                      |
|  Layer 1: Hardware / OS                                        |
|    Sources: dmesg, journald, SMART, IPMI sensors               |
|                                                                |
+---------------------------------------------------------------+
```

---

> **Pause and predict**: Kubernetes marks a node unhealthy only after missed heartbeats accumulate for about 50 seconds by default. During those 40 seconds, pods on the node are running but potentially broken. What types of hardware failures would be invisible to the kubelet heartbeat mechanism?

## Node Problem Detector

[Node Problem Detector (NPD) is a DaemonSet that monitors system logs and reports problems as Kubernetes node conditions.](https://github.com/kubernetes/node-problem-detector) Without NPD, Kubernetes only knows a node is unhealthy when kubelet stops reporting -- which can take minutes.

### Deploying Node Problem Detector

NPD runs with `hostNetwork` and `hostPID` access so it can read kernel logs (`/dev/kmsg`), system logs, and detect hardware-level issues that the kubelet cannot see. It translates these low-level signals into Kubernetes node conditions that Machine Health Checks can act on.

```yaml
# node-problem-detector.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-problem-detector
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: node-problem-detector
  template:
    metadata:
      labels:
        app: node-problem-detector
    spec:
      hostNetwork: true
      hostPID: true
      containers:
        - name: node-problem-detector
          image: registry.k8s.io/node-problem-detector/node-problem-detector:v0.8.19
          command:
            - /node-problem-detector
            - --logtostderr
            - --config.system-log-monitor=/config/kernel-monitor.json
            - --config.system-log-monitor=/config/containerd-monitor.json
            - --config.custom-plugin-monitor=/config/health-checker-kubelet.json
          securityContext:
            privileged: true
          volumeMounts:
            - name: log
              mountPath: /var/log
              readOnly: true
            - name: kmsg
              mountPath: /dev/kmsg
              readOnly: true
            - name: config
              mountPath: /config
      volumes:
        - name: log
          hostPath:
            path: /var/log
        - name: kmsg
          hostPath:
            path: /dev/kmsg
        - name: config
          configMap:
            name: npd-config
```

NPD supports custom health check plugins. For example, you can add a custom health-check plugin that periodically inspects EDAC counters and disk SMART health, then sets a custom node condition when those checks fail.

---

## Machine Health Checks (Cluster API)

[Machine Health Checks (MHC) are a Cluster API resource that watches node conditions and triggers remediation when conditions are unhealthy for a specified duration.](https://cluster-api.sigs.k8s.io/tasks/automated-machine-management/healthchecking.html)

### MHC Configuration

```yaml
# machine-health-check.yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: MachineHealthCheck
metadata:
  name: worker-health-check
  namespace: default
spec:
  clusterName: production
  # Which machines to watch
  selector:
    matchLabels:
      cluster.x-k8s.io/deployment-name: worker-pool
  # Conditions that trigger remediation
  unhealthyConditions:
    - type: Ready
      status: "False"
      timeout: 300s       # 5 min of NotReady = remediate
    - type: Ready
      status: Unknown
      timeout: 300s       # 5 min of Unknown = remediate
    - type: HardwareHealthy
      status: "False"
      timeout: 60s        # hardware failure = remediate fast
  # Safety: never remediate more than 40% at once
  maxUnhealthy: 40%
  # How long to wait for a new node before considering
  # the remediation failed
  nodeStartupTimeout: 600s
```

### How MHC Remediation Works

```
+---------------------------------------------------------------+
|              MHC REMEDIATION FLOW                              |
|                                                                |
|  1. Node condition becomes unhealthy                           |
|     (kubelet stops reporting, NPD sets condition)              |
|                                                                |
|  2. MHC controller notices condition duration > timeout        |
|                                                                |
|  3. MHC checks maxUnhealthy                                   |
|     - If > 40% nodes already unhealthy, STOP                  |
|       (prevents cascade remediation)                           |
|     - If < 40%, proceed                                        |
|                                                                |
|  4. MHC deletes the Machine object                             |
|     (this triggers the infrastructure provider)                |
|                                                                |
|  5. For bare metal (CAPM3 / Metal3):                           |
|     a. Power off server via BMC/IPMI                           |
|     b. Wipe disk (if configured)                               |
|     c. PXE boot new OS image                                   |
|     d. Join cluster as new node                                |
|                                                                |
|  6. For simpler setups (no CAPI):                              |
|     a. Custom controller attempts BMC power cycle              |
|     b. If node returns, done                                   |
|     c. If not, alert on-call for physical intervention         |
|                                                                |
+---------------------------------------------------------------+
```

---

## Automated Reboot and Reprovisioning

Not every environment uses Cluster API. Here is a lightweight auto-remediation approach using a custom controller.

> **Stop and think**: The MHC remediation flow deletes and reprovisions machines, which works with Cluster API. But many bare-metal clusters do not use CAPI. How would you build automatic remediation without CAPI? What is the simplest approach?

### Simple Node Watchdog

This lightweight script provides automatic remediation without Cluster API. It runs as a CronJob, finds nodes that have been NotReady beyond a threshold, and attempts a BMC power cycle. A cooldown timer prevents reboot loops.

```bash
#!/bin/bash
# node-watchdog.sh — run as CronJob on a management node
set -euo pipefail

NOTREADY_THRESHOLD=300  # seconds before attempting reboot

# Find nodes NotReady for > threshold
UNHEALTHY=$(kubectl get nodes -o json | jq -r --argjson t "$NOTREADY_THRESHOLD" '
  .items[] | select(.status.conditions[] |
    select(.type == "Ready" and .status != "True") |
    (now - (.lastTransitionTime | fromdateiso8601)) > $t
  ) | .metadata.name')

for NODE in $UNHEALTHY; do
  BMC_ADDR=$(kubectl get node "$NODE" \
    -o jsonpath='{.metadata.annotations.bmc\.kubedojo\.io/address}')
  [ -z "$BMC_ADDR" ] && { echo "No BMC for ${NODE}, alerting"; continue; }

  # Skip if rebooted < 30 min ago (prevent reboot loops)
  LAST=$(kubectl get node "$NODE" \
    -o jsonpath='{.metadata.annotations.remediation\.kubedojo\.io/last-reboot}' \
    2>/dev/null || echo "0")
  [ $(($(date +%s) - LAST)) -lt 1800 ] && { echo "Recent reboot, skipping"; continue; }

  # Power cycle via IPMI and record attempt
  ipmitool -I lanplus -H "$BMC_ADDR" -U admin -P "$(get_bmc_pass "$NODE")" \
    chassis power cycle
  kubectl annotate node "$NODE" \
    "remediation.kubedojo.io/last-reboot=$(date +%s)" --overwrite
done
```

### Escalation Logic

```
+---------------------------------------------------------------+
|            REMEDIATION ESCALATION LADDER                       |
|                                                                |
|  Level 1: Automatic (no human needed)                         |
|  +---------+    +---------+    +----------+                   |
|  | Detect  |--->| Wait    |--->| BMC      |                   |
|  | NotReady|    | 5 min   |    | power    |                   |
|  |         |    |         |    | cycle    |                   |
|  +---------+    +---------+    +----------+                   |
|                                     |                          |
|                                     v                          |
|  Level 2: Automatic with alert      |                          |
|  +---------+    +---------+    +----+-----+                   |
|  | Node    |--->| Wait    |--->| PXE      |                   |
|  | still   |    | 10 min  |    | repro-   |                   |
|  | down    |    |         |    | vision   |                   |
|  +---------+    +---------+    +----------+                   |
|                                     |                          |
|                                     v                          |
|  Level 3: Human intervention        |                          |
|  +---------+    +---------+    +----+-----+                   |
|  | Node    |--->| Page    |--->| Physical |                   |
|  | still   |    | on-call |    | inspect  |                   |
|  | down    |    | (30min) |    | /replace |                   |
|  +---------+    +---------+    +----------+                   |
|                                                                |
+---------------------------------------------------------------+
```

---

## Spare Node Pools

On bare metal, you cannot create new nodes on demand. Spare nodes must be physically present, powered on, and ready to accept workloads.

### Spare Node Strategy

```
+---------------------------------------------------------------+
|            SPARE NODE POOL DESIGN                              |
|                                                                |
|  Cluster: 80 worker nodes across 4 racks                      |
|                                                                |
|  Spare nodes: 4 (5% of fleet)                                 |
|    spare-01 (rack-a) — cordoned, no workloads                  |
|    spare-02 (rack-b) — cordoned, no workloads                  |
|    spare-03 (rack-c) — cordoned, no workloads                  |
|    spare-04 (rack-d) — cordoned, no workloads                  |
|                                                                |
|  Why cordoned, not powered off?                                |
|  - Instant availability (no boot time)                         |
|  - Kubelet is running, node is Ready                           |
|  - Just uncordon to accept workloads                           |
|  - Hardware health is continuously monitored                   |
|                                                                |
|  Auto-failover:                                                |
|  1. Worker-27 fails                                            |
|  2. Watchdog detects NotReady > 5 min                          |
|  3. Watchdog uncordons spare-02 (same rack)                    |
|  4. Pods reschedule to spare-02                                |
|  5. Watchdog alerts on-call: "Spare used, investigate"         |
|  6. Engineer fixes worker-27, re-cordons it as new spare       |
|                                                                |
+---------------------------------------------------------------+
```

> **Pause and predict**: Why are spare nodes kept cordoned but powered on, rather than powered off? What is the trade-off in power cost versus recovery time?

### Managing Spare Nodes

```bash
# Label and cordon spare nodes
kubectl label node spare-01 node-role.kubernetes.io/spare="" kubedojo.io/rack=rack-a
kubectl cordon spare-01

# Auto-failover: find a spare in the same rack as the failed node, uncordon it
# If no same-rack spare, use any available spare
# Alert on-call: "Spare activated, investigate failed node"
# After fix: re-cordon the recovered node as the new spare
```

---

## Handling Common Hardware Failures

### RAM ECC Errors

```bash
# Detect ECC errors
cat /sys/devices/system/edac/mc/mc*/csrow*/ch*_ce_count

# Prometheus query for ECC trend
# rate(node_edac_correctable_errors_total[1h]) > 0

# Action levels:
# < 10 correctable errors/day: monitor
# 10-100 correctable errors/day: schedule DIMM replacement
# > 100 correctable errors/day: drain and replace immediately
# Any uncorrectable error: drain IMMEDIATELY (data corruption risk)
```

### NIC Flapping

```bash
# Detect NIC flap (link up/down cycles)
dmesg | grep -i "link is down\|link is up" | tail -20

# Prometheus alert rule
# changes(node_network_carrier{device="eth0"}[10m]) > 4

# Causes:
# - Failing NIC port (replace NIC or use different port)
# - Failing cable (replace cable)
# - Failing switch port (move to different switch port)
# - Driver bug (update NIC firmware/driver)

# Immediate action: if NIC flaps > 3 times in 10 min
kubectl cordon affected-node  # prevent new pods
# Investigate root cause before draining
```

### PSU Failure

```bash
# Check PSU status via IPMI
ipmitool -I lanplus -H bmc-addr -U admin -P pass sdr type "Power Supply"

# Example output:
# PS1 Status     | ok     | Power Supply | Presence detected
# PS2 Status     | cr     | Power Supply | Failure detected

# Action:
# PSU failure with redundancy = WARN, schedule replacement
# PSU failure without redundancy = CRITICAL, drain node
```

---

## Blast Radius Containment

To prevent a single hardware failure from taking down an entire application, you must design for failure domain isolation. On bare metal, failure domains are physical: Top-of-Rack (ToR) switches, power circuits, and storage arrays.

### Topology Spread Constraints & Rack-Aware Scheduling
[Use `topologySpreadConstraints` to ensure pods are distributed across physical racks.](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/) If a ToR switch fails, only a fraction of the application's pods go down.

```yaml
# Example: Rack-aware scheduling
spec:
  topologySpreadConstraints:
    - maxSkew: 1
      topologyKey: kubedojo.io/rack
      whenUnsatisfiable: ScheduleAnyway
      labelSelector:
        matchLabels:
          app: critical-workload
```

### Storage Isolation
Stateful workloads create data gravity. If a node with dense storage fails, rebuilding that data heavily stresses the network.
- **Dedicated Storage Networks**: Isolate storage replication traffic onto a separate VLAN to prevent it from starving kubelet heartbeats.
- **Failure Domain Mapping**: Configure your storage system (like Ceph's CRUSH map) to mirror data across racks, reducing the chance that a single rack failure results in data unavailability.

---

## Tuning Eviction Timeouts

Default Kubernetes eviction settings are tuned for cloud environments. On bare metal, you may want faster or slower eviction depending on the failure mode.

Node-failure eviction relies on taint-based eviction and per-pod `NoExecute` tolerations. [When a node becomes `NotReady`, the node lifecycle controller adds a `node.kubernetes.io/not-ready` taint. Pods are evicted when their toleration for this taint expires.](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)

```bash
# Default behavior:
#   kube-controller-manager:
#     --node-monitor-period=5s         (check node status every 5s)
#     --node-monitor-grace-period=40s  (mark NotReady after 40s no heartbeat)
#
#   kube-apiserver:
#     --default-not-ready-toleration-seconds=300     (evict 5 min after NotReady taint)
#     --default-unreachable-toleration-seconds=300   (evict 5 min after Unreachable taint)

# For faster bare metal remediation:
# Edit kube-apiserver manifest (/etc/kubernetes/manifests/kube-apiserver.yaml)
#   --default-not-ready-toleration-seconds=120      (evict after 2 min instead of 5)
#   --default-unreachable-toleration-seconds=120
#
# Or set tolerationSeconds directly on pods for fine-grained control:
# spec.tolerations:
#   - key: "node.kubernetes.io/not-ready"
#     operator: "Exists"
#     effect: "NoExecute"
#     tolerationSeconds: 60   # evict after 60s for this specific workload

# Also tune node-monitor-grace-period for faster NotReady detection:
# Edit kube-controller-manager manifest
#   --node-monitor-grace-period=30s  (mark NotReady after 30s instead of 40s)
```

### Tuning Storage Recovery Throttling

When a node fails, distributed storage systems like Ceph will attempt to rebuild missing data replicas on surviving nodes. Unthrottled recovery can saturate the network and cause otherwise healthy nodes to drop kubelet heartbeats, triggering cascade failures.

```bash
# Throttle Ceph recovery to prevent network saturation during node failure
# Apply these dynamically to running OSDs
ceph tell 'osd.*' injectargs '--osd-recovery-max-active 1'
ceph tell 'osd.*' injectargs '--osd-max-backfills 1'
ceph tell 'osd.*' injectargs '--osd-recovery-op-priority 1'
```

---

## Did You Know?

- **Large production schedulers are designed to absorb regular machine failures.** Even smaller bare-metal clusters should assume node loss is a routine event and automate remediation accordingly.

- **Machine Health Checks play a similar role to health-check-based replacement in cloud autoscaling systems**, but bare-metal recovery usually takes longer because rebooting or reprovisioning physical hardware takes time.

- **ECC memory can catch many memory faults, and recurring ECC alerts are a strong warning sign that a DIMM needs attention before it causes wider disruption.**

- **The "Pets vs Cattle" metaphor applies to bare metal nodes too.** Even though the hardware is physical and unique, your automation should treat nodes as replaceable. If a node fails, the system should automatically replace it without human intervention (at least for the first attempt). The node's identity comes from its Kubernetes registration, not from its hardware serial number.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No auto-remediation for NotReady nodes | 5+ min downtime waiting for human response at 3 AM | Deploy MHC or custom watchdog with BMC power cycle |
| Remediating too aggressively | Cascade failure if root cause affects multiple nodes | Set maxUnhealthy in MHC (40% is a safe default) |
| No spare nodes | Failed node reduces capacity until physically fixed | Keep 5% spare nodes cordoned and ready |
| Default taint toleration (5 min) | Pods on failed node unavailable for 5 minutes | Tune `--default-not-ready-toleration-seconds` on kube-apiserver or set `tolerationSeconds` on pods |
| Not monitoring ECC errors | DIMM failure is a surprise | Deploy edac monitoring, alert at >10 errors/day |
| NIC flap not detected | Intermittent connectivity causes random pod failures | Monitor `node_network_carrier` changes |
| No BMC connectivity | Cannot remotely power cycle failed nodes | Ensure BMC network is on a separate, reliable management VLAN |
| Reprovisioning without root cause analysis | Same failure repeats on the reprovisioned node | Log all remediation events, review weekly |

---

## Quiz

### Question 1
Your MHC is configured with `maxUnhealthy: 40%` and you have 10 worker nodes. Node-03 is `NotReady` for 6 minutes. The MHC triggers remediation. While node-03 is being rebooted, node-07 and node-09 also go `NotReady`. What happens?

<details>
<summary>Answer</summary>

**The MHC WILL remediate node-07 and node-09.**

With 10 nodes and 3 unhealthy (30%), the MHC checks: is 30% >= 40%? No, so it proceeds. The MHC checks `maxUnhealthy` before each remediation:

- Node-03: 1/10 unhealthy = 10% < 40% -> remediate
- Node-07: 3/10 unhealthy = 30% < 40% -> remediate
- Node-09: still 3/10 unhealthy (or 2/10 if node-03 recovered) -> remediate

If a 5th node fails while these are being remediated: 5/10 = 50%, which exceeds the threshold, so MHC stops further remediation until the cluster is healthier.

**The safety mechanism**: `maxUnhealthy` prevents the MHC from rebooting your entire cluster in a cascade. If 40%+ of nodes are unhealthy, the problem is systemic and needs human investigation (bad switch, power issue, control plane failure).
</details>

### Question 2
A node shows `Ready` status in Kubernetes but is experiencing intermittent packet loss due to a failing NIC. Pods on this node have random timeouts. How would you detect and remediate this?

<details>
<summary>Answer</summary>

**This is a "gray failure" -- the node appears healthy but is degraded.**

**Detection:**
1. **Node Problem Detector custom check**: Monitor NIC link state changes
   ```bash
   # NPD script: detect NIC flapping
   FLAPS=$(dmesg --time-format iso | grep -c "link is down" | tail -1)
   if [ "$FLAPS" -gt 3 ]; then
     echo "NIC flapping detected: ${FLAPS} link-down events"
     exit 1  # Sets node condition to unhealthy
   fi
   ```

2. **Prometheus network metrics**:
   ```
   rate(node_network_receive_errs_total{device="eth0"}[5m]) > 0
   rate(node_network_transmit_drop_total{device="eth0"}[5m]) > 0
   changes(node_network_carrier{device="eth0"}[10m]) > 2
   ```

3. **Application-level signals**: Increased error rates, latency spikes correlated with specific node.

**Remediation:**
1. NPD sets a custom condition: `NetworkHealthy = False`
2. MHC watches for `NetworkHealthy = False` with timeout 60s
3. MHC triggers remediation (cordon + reboot)
4. If NIC flapping persists after reboot, the node stays unhealthy and gets escalated to Level 3 (physical NIC replacement)

**Workaround while waiting for fix:**
```bash
kubectl cordon affected-node
kubectl drain affected-node --ignore-daemonsets --delete-emptydir-data
```
</details>

### Question 3
You are designing a spare node strategy for a 60-node cluster across 3 racks (20 nodes per rack). How many spare nodes do you need and where do you place them?

<details>
<summary>Answer</summary>

**Recommended: 3 spare nodes, one per rack.**

**Reasoning:**
- A practical starting point is at least one spare per rack, then adjust based on utilization and recovery targets.
- One per rack usually means a same-rack spare is available
- Same-rack replacement minimizes network topology changes
- If a rack loses power, the spare in that rack is also lost -- but the other 2 racks still have spares

**Placement:**
```
Rack A: worker-01..20 + spare-a (21 servers total)
Rack B: worker-21..40 + spare-b (21 servers total)
Rack C: worker-41..60 + spare-c (21 servers total)
```

**Configuration:**
- All spares are cordoned (schedulable=false) but powered on and joined to the cluster
- Spares run the same OS, kubelet version, and configuration as production nodes
- Spares are included in firmware update rotations

**Cost justification:**
- 3 spare nodes at $10,000 each = $30,000
- One 2-hour outage costs $50,000+ in engineering time, lost revenue, SLA penalties
- Spares pay for themselves after preventing a single extended outage

**When 5% is not enough:**
- Clusters with very high utilization (>80%) may need 10% spares
- Clusters running stateful workloads with strict anti-affinity need one spare per failure domain
</details>

### Question 4
Your custom node watchdog script attempts a BMC power cycle on a failed node. The power cycle succeeds, the node boots, but it does not rejoin the Kubernetes cluster. kubelet logs show `certificate has expired`. What happened and how do you fix it?

<details>
<summary>Answer</summary>

**The node's kubelet client certificate expired while the node was down.**

**What happened:**
1. Kubernetes uses TLS certificates for kubelet-to-apiserver communication
2. These certificates are commonly issued for one year by default, and kubelet requests a replacement as expiration approaches
3. If the node was down for an extended period (or if the certificate was already near expiration), the certificate may have expired before kubelet could rotate it
4. When the node reboots, kubelet tries to connect with the expired certificate -> rejected

**Fix:**
```bash
# Option 1: Approve the new CSR (kubelet generated a new one)
kubectl get csr | grep Pending
kubectl certificate approve <csr-name>

# Option 2: If no CSR was generated, delete the old certificate
# On the node:
rm /var/lib/kubelet/pki/kubelet-client-current.pem
systemctl restart kubelet
# Then approve the CSR on the control plane

# Option 3: Bootstrap with a new token
# On a control plane node:
kubeadm token create --print-join-command
# On the failed node — remove old PKI artifacts first, or kubeadm join
# will fail pre-flight checks because existing files are detected:
rm /etc/kubernetes/kubelet.conf
rm /var/lib/kubelet/pki/kubelet-client-current.pem
kubeadm join <api-server>:6443 --token <new-token> \
  --discovery-token-ca-cert-hash sha256:<hash>
```

**Prevention:**
- Monitor certificate expiration as part of cluster health checks
- Ensure kubelet auto-rotation is enabled (default in kubeadm clusters)
- If a node is down for more than a few days, assume certificate issues and plan accordingly
- Include CSR auto-approval in your remediation pipeline for known nodes
</details>

---

## Hands-On Exercise: Deploy Node Problem Detector

**Task**: Deploy NPD on a kind cluster and trigger a simulated node condition.

### Setup

```bash
# Create a kind cluster
kind create cluster --name npd-lab --config - <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
EOF
```

### Steps

1. **Deploy Node Problem Detector:**
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/node-problem-detector/master/deployment/node-problem-detector.yaml
   ```

2. **Check NPD is running:**
   ```bash
   kubectl get pods -n kube-system -l app=node-problem-detector
   ```

3. **Check node conditions added by NPD:**
   ```bash
   kubectl get nodes -o json | jq '.items[].status.conditions[] | select(.type != "Ready" and .type != "MemoryPressure" and .type != "DiskPressure" and .type != "PIDPressure" and .type != "NetworkUnavailable")'
   ```

4. **Simulate a kernel issue:**
   ```bash
   # Exec into the worker node container (kind-specific)
   # Write to /dev/kmsg so the message is picked up by journald and NPD
   # (kind nodes use journald, not traditional syslog, so /var/log/kern.log may not exist)
   docker exec npd-lab-worker bash -c \
     'echo "kernel: BUG: unable to handle kernel NULL pointer dereference" > /dev/kmsg'
   ```

5. **Observe NPD reporting the condition:**
   ```bash
   kubectl get node npd-lab-worker -o json | jq '.status.conditions'
   ```

### Success Criteria

- [ ] NPD DaemonSet is running on all nodes
- [ ] Can view NPD-reported conditions via `kubectl get node`
- [ ] Understand the difference between transient events and permanent conditions
- [ ] Know how MHC uses these conditions to trigger remediation
- [ ] Can explain the escalation ladder: detect -> reboot -> reprovision -> alert human

### Cleanup

```bash
kind delete cluster --name npd-lab
```

---

## Next Module

Continue to [Module 7.4: Observability Without Cloud Services](/on-premises/operations/module-7.4-observability/) to learn how to build a self-hosted monitoring stack with Prometheus, Thanos, Grafana, and Loki.

## Sources

- [kubernetes.io: taint and toleration](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) — Explains how the node lifecycle controller applies NotReady/unreachable taints and how pod tolerationSeconds governs eviction timing during node remediation.
- [Node Problem Detector](https://github.com/kubernetes/node-problem-detector) — Supports claims about detecting kernel, filesystem, runtime, and hardware-adjacent node problems and surfacing them to Kubernetes as Events and NodeConditions for higher-level remediation.
- [Cluster API MachineHealthCheck](https://cluster-api.sigs.k8s.io/tasks/automated-machine-management/healthchecking.html) — Supports claims about MachineHealthCheck remediation triggers, unhealthy-condition timeouts, short-circuit safeguards, remediation limits, and delete-and-recreate behavior for unhealthy machines.
- [Pod Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/) — Backs rack/zone spread behavior, topology keys, default spread behavior, and cluster scheduling policy claims when distributing workloads across mixed racks or hardware domains.
- [kubernetes.io: troubleshooting kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/troubleshooting-kubeadm/) — The kubeadm troubleshooting docs explicitly describe expired kubelet client certificates causing authentication and rejoin problems.
- [Node Status](https://kubernetes.io/docs/reference/node/node-status) — Documents `Ready` and `Unknown` semantics and the current default node-monitor-grace-period.
