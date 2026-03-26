---
title: "Module 7.5: Capacity Expansion & Hardware Refresh"
slug: on-premises/operations/module-7.5-capacity-expansion
sidebar:
  order: 6
---

> **Complexity**: `[COMPLEX]` | Time: 60 minutes
>
> **Prerequisites**: [Module 7.4: Observability Without Cloud Services](module-7.4-observability/), [Module 1.2: Server Sizing](../planning/module-1.2-server-sizing/)

---

## Why This Module Matters

In January 2024, a gaming company running a 120-node bare metal Kubernetes cluster needed to add 40 new servers for a game launch. Their existing cluster used Intel Xeon Silver 4214 (Cascade Lake, 2019) processors. The procurement team ordered Dell R760 servers with AMD EPYC 9354 (Genoa, 2023) processors because they offered better price/performance. The infrastructure team racked the servers, PXE-booted them, and joined them to the cluster. Everything appeared fine until the scheduler started placing workloads on the new nodes.

The Java applications ran 15% faster on the AMD nodes due to higher single-thread performance. The data science team's TensorFlow jobs ran 40% faster because the EPYC CPUs had AVX-512 support. But here was the problem: the Kubernetes scheduler does not understand CPU performance differences. It sees "48 CPU cores available" on both the old Intel and new AMD nodes. The scheduler distributed pods evenly, but the AMD nodes could handle more work per core. Some teams manually pinned their pods to AMD nodes using nodeSelectors, creating an uneven resource distribution. Other teams complained that their pods were "slow" when scheduled on the older Intel nodes.

The real disaster came when the team tried to decommission 20 of the oldest Intel servers. They had not configured topology spread constraints, so draining those nodes pushed 300 pods onto nodes that were already at 75% utilization. The cluster hit 95% CPU utilization, OOM kills spiked, and the monitoring stack (also on the cluster) slowed to a crawl -- right when they needed it most.

The lesson: adding hardware to a Kubernetes cluster is not just racking and stacking. You need to account for CPU generation differences, topology constraints, scheduling policies, and a decommission plan that respects capacity limits.

---

## What You'll Learn

- Adding new racks and nodes to existing clusters
- Managing mixed CPU generations (Intel and AMD)
- Topology spread constraints for heterogeneous hardware
- Decommissioning old nodes safely
- 3-year vs 5-year hardware refresh cycles
- Capacity planning with hardware generations

---

## Adding New Racks to Existing Clusters

### Physical and Network Prerequisites

```
+---------------------------------------------------------------+
|        ADDING A NEW RACK TO AN EXISTING CLUSTER                |
|                                                                |
|  Before racking servers:                                       |
|  1. Network: leaf switch installed, cabled to spines           |
|  2. Power: PDUs installed, circuits provisioned                |
|  3. VLANs: management, production, storage trunked on leaf    |
|  4. BGP: leaf peering with spines (new AS number for rack)     |
|  5. PXE: DHCP relay configured for new subnet                 |
|  6. DNS: reverse DNS entries for new BMC/management IPs        |
|  7. IPAM: IP ranges allocated for nodes, pods, services        |
|                                                                |
|  After racking servers:                                        |
|  1. BMC configured (IP, credentials, NTP)                      |
|  2. PXE boot OS image                                          |
|  3. Configure networking (bonds, VLANs, routes)                |
|  4. Install kubelet, kubeadm, container runtime                |
|  5. Join cluster with kubeadm join                             |
|  6. Label nodes (rack, generation, hardware model)             |
|  7. Verify CNI connectivity to existing nodes                  |
|  8. Verify CSI storage access                                  |
+---------------------------------------------------------------+
```

### Node Provisioning Script for New Rack

```bash
#!/bin/bash
# provision-new-rack.sh — add a rack of servers to existing cluster
set -euo pipefail

RACK_ID="$1"             # e.g., rack-e
NODES_FILE="$2"          # hostname,bmc-ip,mgmt-ip
JOIN_TOKEN="$3"          # from kubeadm token create
CA_CERT_HASH="$4"        # from kubeadm
API_SERVER="$5"          # e.g., 10.0.10.10:6443

while IFS=, read -r HOSTNAME BMC_IP MGMT_IP; do
  echo "=== Provisioning ${HOSTNAME} in ${RACK_ID} ==="

  # Wait for node to be PXE booted and accessible
  echo "Waiting for ${HOSTNAME} to be reachable via SSH..."
  until ssh -o ConnectTimeout=5 root@"$MGMT_IP" true 2>/dev/null; do
    sleep 10
  done

  # Configure node labels and join cluster
  ssh root@"$MGMT_IP" bash <<REMOTE_EOF
    # Join the cluster
    kubeadm join ${API_SERVER} \
      --token ${JOIN_TOKEN} \
      --discovery-token-ca-cert-hash sha256:${CA_CERT_HASH}
REMOTE_EOF

  # Label the node from a control plane
  echo "Labeling ${HOSTNAME}..."
  kubectl label node "$HOSTNAME" \
    topology.kubernetes.io/zone="${RACK_ID}" \
    kubedojo.io/rack="${RACK_ID}" \
    kubedojo.io/hardware-gen="gen4" \
    kubedojo.io/cpu-vendor="amd" \
    kubedojo.io/cpu-model="epyc-9354" \
    --overwrite

  echo "=== ${HOSTNAME} joined and labeled ==="
done < "$NODES_FILE"

echo "All nodes in ${RACK_ID} provisioned."
echo "Run: kubectl get nodes -l kubedojo.io/rack=${RACK_ID}"
```

---

## Mixed CPU Generations

### The Problem with Heterogeneous Performance

```
+---------------------------------------------------------------+
|        CPU PERFORMANCE ACROSS GENERATIONS                      |
|                                                                |
|  Model              Year  Cores  Single-Thread  Passmark       |
|  ───────────────────────────────────────────────────           |
|  Xeon Silver 4214   2019  12     1,800          15,200         |
|  Xeon Gold 6330     2021  28     2,100          35,000         |
|  EPYC 9354          2023  32     2,600          53,000         |
|                                                                |
|  The EPYC 9354 delivers ~44% more single-thread and           |
|  ~3.5x more multi-thread performance than the 4214.           |
|                                                                |
|  Kubernetes sees: "32 cores available" on both.               |
|  Reality: 32 EPYC cores >> 32 Xeon Silver cores.              |
|                                                                |
+---------------------------------------------------------------+
```

### Labeling Hardware Generations

```bash
# Label all nodes with their hardware generation
# This enables scheduling policies based on performance tier

# Gen 1: 2019 hardware (Cascade Lake)
kubectl label nodes -l kubedojo.io/cpu-model=xeon-4214 \
  kubedojo.io/performance-tier=standard

# Gen 2: 2021 hardware (Ice Lake)
kubectl label nodes -l kubedojo.io/cpu-model=xeon-6330 \
  kubedojo.io/performance-tier=high

# Gen 3: 2023 hardware (Genoa)
kubectl label nodes -l kubedojo.io/cpu-model=epyc-9354 \
  kubedojo.io/performance-tier=premium
```

### Scheduling Policies for Mixed Hardware

```yaml
# Option 1: Prefer newer hardware (soft preference)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: latency-sensitive-app
spec:
  template:
    spec:
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              preference:
                matchExpressions:
                  - key: kubedojo.io/performance-tier
                    operator: In
                    values: [premium]
            - weight: 50
              preference:
                matchExpressions:
                  - key: kubedojo.io/performance-tier
                    operator: In
                    values: [high]
      containers:
        - name: app
          image: my-app:latest
          resources:
            requests:
              cpu: "4"
              memory: 8Gi
---
# Option 2: Require specific hardware (hard requirement)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-training-job
spec:
  template:
    spec:
      nodeSelector:
        kubedojo.io/cpu-vendor: amd          # Needs AVX-512
        kubedojo.io/performance-tier: premium
      containers:
        - name: training
          image: tensorflow:latest
          resources:
            requests:
              cpu: "16"
              memory: 64Gi
```

### Weighted Resource Capacity

Kubernetes sees all CPU cores as equal, but they are not. Use benchmark scores (e.g., Passmark single-thread) to calculate "normalized" capacity. Example: decommissioning 20 older Xeon 4214 nodes from a 120-node mixed cluster removes only ~8% of effective compute capacity, not the 17% that a simple node count would suggest. Always use weighted capacity calculations when planning decommissions.

---

## Topology Spread Constraints for Heterogeneous Hardware

When you have multiple hardware generations across multiple racks, topology spread constraints ensure workloads are distributed to survive rack failures and hardware-specific issues.

### Multi-Dimensional Topology Spread

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: critical-service
spec:
  replicas: 6
  template:
    metadata:
      labels:
        app: critical-service
    spec:
      topologySpreadConstraints:
        # Spread across racks (survive rack failure)
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: critical-service
        # Spread across hardware generations (survive generation-specific bug)
        - maxSkew: 2
          topologyKey: kubedojo.io/hardware-gen
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app: critical-service
      containers:
        - name: app
          image: critical-service:latest
          resources:
            requests:
              cpu: "2"
              memory: 4Gi
```

### Visualizing Topology Distribution

```
+---------------------------------------------------------------+
|     TOPOLOGY SPREAD: 6 REPLICAS ACROSS 3 RACKS, 2 GENS        |
|                                                                |
|  Rack A (Gen 1 + Gen 3):                                      |
|    [worker-01 gen1] pod-1                                      |
|    [worker-02 gen1]                                            |
|    [worker-21 gen3] pod-2                                      |
|                                                                |
|  Rack B (Gen 1 + Gen 2):                                      |
|    [worker-05 gen1] pod-3                                      |
|    [worker-11 gen2] pod-4                                      |
|    [worker-12 gen2]                                            |
|                                                                |
|  Rack C (Gen 2 + Gen 3):                                      |
|    [worker-15 gen2] pod-5                                      |
|    [worker-25 gen3] pod-6                                      |
|    [worker-26 gen3]                                            |
|                                                                |
|  Result: 2 pods per rack (maxSkew=1 satisfied)                 |
|  Gen distribution: gen1=2, gen2=2, gen3=2 (maxSkew=2 OK)      |
|  Rack failure: lose 2/6 pods = service continues               |
|  Gen-specific bug: affects 2/6 pods = service continues        |
+---------------------------------------------------------------+
```

---

## Decommissioning Old Nodes

Removing nodes requires careful capacity planning to avoid overloading the remaining cluster.

### Decommission Checklist

```bash
#!/bin/bash
# decommission-node.sh — safely remove a node from the cluster
set -euo pipefail

NODE="$1"

echo "=== Pre-decommission checks for ${NODE} ==="

# Check 1: Will remaining capacity handle the load?
TOTAL_CPU=$(kubectl get nodes -o json | jq '[.items[].status.allocatable.cpu | rtrimstr("m") | tonumber] | add')
NODE_CPU=$(kubectl get node "$NODE" -o json | jq '.status.allocatable.cpu | rtrimstr("m") | tonumber')
REMAINING_CPU=$((TOTAL_CPU - NODE_CPU))
REQUESTED_CPU=$(kubectl get pods -A -o json | jq '[.items[].spec.containers[].resources.requests.cpu // "0" | rtrimstr("m") | tonumber] | add')

echo "Total allocatable CPU: ${TOTAL_CPU}m"
echo "This node CPU: ${NODE_CPU}m"
echo "Remaining CPU after removal: ${REMAINING_CPU}m"
echo "Total requested CPU: ${REQUESTED_CPU}m"
echo "Utilization after removal: $((REQUESTED_CPU * 100 / REMAINING_CPU))%"

if [ $((REQUESTED_CPU * 100 / REMAINING_CPU)) -gt 80 ]; then
  echo "WARNING: Cluster will be at >80% CPU utilization after removing this node."
  echo "Consider adding capacity before decommissioning."
  read -p "Continue anyway? (y/N) " -n 1 -r
  echo
  [[ $REPLY =~ ^[Yy]$ ]] || exit 1
fi

# Check 2: Any local PVs on this node?
LOCAL_PVS=$(kubectl get pv -o json | jq -r --arg node "$NODE" '
  .items[] | select(
    .spec.nodeAffinity.required.nodeSelectorTerms[].matchExpressions[].values[] == $node
  ) | .metadata.name')

if [ -n "$LOCAL_PVS" ]; then
  echo "WARNING: Node has local PVs that will be lost:"
  echo "$LOCAL_PVS"
  echo "Migrate data before proceeding."
  exit 1
fi

# Check 3: Drain the node
echo "Draining ${NODE}..."
kubectl drain "$NODE" \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --timeout=600s

# Check 4: Remove from cluster
echo "Removing ${NODE} from cluster..."
kubectl delete node "$NODE"

# Check 5: On the node itself (via SSH or BMC):
# kubeadm reset
# Clean up iptables, IPVS rules, CNI config

echo "=== ${NODE} decommissioned ==="
echo "Remember to:"
echo "  1. Power off the server"
echo "  2. Update CMDB/inventory"
echo "  3. Reclaim rack space"
echo "  4. Update monitoring targets"
echo "  5. Update PXE/DHCP reservations"
```

When decommissioning in batches, remove 5 nodes at a time over 1-2 day phases. Monitor utilization overnight after each batch. Never exceed 80% cluster utilization during the process. After all nodes are removed, verify no orphaned PVs remain and update monitoring targets, alerting thresholds, and spare node counts.

---

## 3-Year vs 5-Year Hardware Refresh Cycles

### Cost Comparison

For a 100-node cluster at $10,000/node:

| Factor | 3-Year Cycle | 5-Year Cycle |
|--------|-------------|-------------|
| Amortized CapEx/year | $333,333 | $200,000 |
| Support contracts | $150,000 total | $310,000 total (higher in years 4-5) |
| Power (total) | $360,000 | $648,000 (efficiency degrades ~5%/year) |
| Failure rate (end of life) | 1-2% | 5-8% |
| Performance vs current gen | 100% at refresh | 60% at end of life |
| **Total cost** | **$1.52M ($506k/yr)** | **$2.04M ($407k/yr)** |

The 3-year cycle is 24% more expensive per year but keeps you on the latest hardware with lower failure rates and power costs.

Choose 3-year cycles for performance-sensitive workloads, rapid growth, or when power efficiency matters. Choose 5-year cycles for budget-constrained environments with stable, predictable loads that are not CPU-bound.

### Staggered Refresh Strategy

```
+---------------------------------------------------------------+
|        STAGGERED REFRESH (recommended for large clusters)      |
|                                                                |
|  Instead of replacing all 100 nodes every 3 years:             |
|  Replace ~33 nodes every year                                  |
|                                                                |
|  Year 1: Buy 33 new nodes (Gen N+3), decommission 33 oldest   |
|  Year 2: Buy 33 new nodes (Gen N+4), decommission 33 oldest   |
|  Year 3: Buy 34 new nodes (Gen N+5), decommission 34 oldest   |
|  Year 4: Buy 33 new nodes (Gen N+6), decommission 33 oldest   |
|  ...                                                           |
|                                                                |
|  Benefits:                                                     |
|  - Smooth CapEx ($333k/year instead of $1M every 3 years)     |
|  - Always have recent hardware in the fleet                    |
|  - Never need to decommission more than 33% at once            |
|  - Team practices add/remove procedure regularly               |
|  - Each year you learn what works for the new hardware gen     |
|                                                                |
|  Challenge:                                                    |
|  - 3 hardware generations in the cluster simultaneously        |
|  - Must handle CPU/memory heterogeneity in scheduling          |
|  - Firmware update process covers multiple vendor models       |
+---------------------------------------------------------------+
```

---

## Capacity Planning with Hardware Generations

### Monitoring Capacity Trends

Create Prometheus recording rules that track CPU capacity and utilization broken down by hardware generation. The most valuable metric is `cluster:capacity_days_remaining`, which uses `deriv()` over a 30-day window to project when current capacity will be exhausted at the current growth rate. Alert when this drops below 60 days to trigger procurement.

---

## Did You Know?

- **Intel and AMD use different socket standards, so you cannot swap CPUs between vendors in the same server chassis.** A hardware refresh that switches from Intel to AMD (or vice versa) requires entirely new servers, not just new CPUs. This is why vendor choice in the initial purchase has long-term implications.

- **The US Department of Energy's supercomputing centers use a 5-year refresh cycle** because their systems cost hundreds of millions of dollars. They plan each refresh 3 years in advance, with a 2-year overlap period where old and new systems run simultaneously. This staggered approach is now being adopted by large Kubernetes operators.

- **Kubernetes 1.24 added the `MinDomainsInPodTopologySpread` feature** (stable in 1.30) that lets you specify the minimum number of topology domains a workload should span. This is particularly useful during hardware refresh: you can require pods to be spread across at least 2 hardware generations, ensuring a generation-specific bug does not take down all replicas.

- **A 2023 Uptime Institute report found that the average server lifespan has increased from 3.5 years in 2015 to 5.2 years in 2023**, driven by companies extending server lifecycles to reduce CapEx during economic uncertainty. However, power efficiency improvements mean newer servers often pay for themselves in energy savings within 2 years.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No node labels for hardware generation | Cannot schedule based on performance tier | Label all nodes with generation, CPU model, and tier |
| Assuming all CPU cores are equal | Uneven performance across hardware generations | Use weighted capacity calculations for planning |
| Decommissioning without capacity check | Cluster overloaded after removing nodes | Calculate post-removal utilization before draining |
| No topology spread across generations | Generation-specific bug (BIOS, kernel) affects all replicas | Use topologySpreadConstraints with hardware-gen key |
| Big-bang hardware refresh | All 100 nodes replaced at once = massive risk | Stagger refreshes: 33 nodes/year rolling |
| Ignoring power efficiency in refresh math | Old servers cost more to power | Include power costs in TCO comparison |
| Not updating monitoring after adding rack | New nodes invisible to alerting | Add new BMC addresses to IPMI exporter, update Prometheus targets |
| Mixing Intel and AMD without testing | Application-level differences (AVX, memory model) | Test workloads on new architecture in staging first |

---

## Quiz

### Question 1
You have a 100-node cluster: 60 nodes with Intel Xeon Silver 4214 (12 cores, 2019) and 40 nodes with AMD EPYC 9354 (32 cores, 2023). You need to decommission 20 of the oldest Intel nodes. What is the actual capacity impact, and how do you validate that the cluster can handle it?

<details>
<summary>Answer</summary>

**Capacity impact analysis:**

**Before decommission:**
- Intel nodes: 60 x 12 cores = 720 cores
- AMD nodes: 40 x 32 cores = 1,280 cores
- Total: 2,000 cores

**After decommission (remove 20 Intel):**
- Intel nodes: 40 x 12 cores = 480 cores
- AMD nodes: 40 x 32 cores = 1,280 cores
- Total: 1,760 cores
- Reduction: 240 cores = **12% of total core count**

**However, performance-adjusted capacity:**
- Intel 4214 passmark per core: ~1,800
- AMD 9354 passmark per core: ~2,600
- Before: (720 x 1,800) + (1,280 x 2,600) = 1,296,000 + 3,328,000 = 4,624,000 units
- After: (480 x 1,800) + (1,280 x 2,600) = 864,000 + 3,328,000 = 4,192,000 units
- Actual performance reduction: **9.3%** (less than the 12% core count suggests)

**Validation steps:**
1. Check current cluster-wide CPU utilization:
   ```bash
   kubectl top nodes --sort-by=cpu
   ```
2. Calculate requested vs allocatable:
   ```bash
   kubectl describe nodes | grep -A 5 "Allocated resources"
   ```
3. Verify no workloads are pinned to the Intel nodes being removed
4. Check PDBs and topology constraints will still be satisfiable with 80 nodes
5. Run the decommission in batches (5 nodes at a time) with monitoring
</details>

### Question 2
Your cluster runs on 3 racks with 20 nodes each. You are adding a 4th rack with 20 new nodes (newer hardware generation). Your critical service has a topology spread constraint of `maxSkew: 1` on `topology.kubernetes.io/zone`. After adding the new rack, new pods are not scheduling on the 4th rack. Why?

<details>
<summary>Answer</summary>

**The topology spread constraint is preventing scheduling on the new rack.**

**The math:**
- Existing: 3 racks, each with some pods of the critical service
- Say the service has 9 replicas: 3 per rack (skew = 0, within maxSkew=1)
- New rack-d has 0 replicas

When a new pod needs to be scheduled:
- rack-a: 3, rack-b: 3, rack-c: 3, rack-d: 0
- Minimum count: 0 (rack-d), maximum count: 3 (any existing rack)
- Skew = 3 - 0 = 3, which exceeds maxSkew=1
- **Result**: Pod CAN schedule on rack-d (it would reduce the skew to 3-1=2... wait, no)

Actually, the topology spread constraint evaluates where scheduling the new pod would produce the lowest skew:
- Schedule on rack-d: counts become 3,3,3,1 -> max-min = 3-1 = 2 -> skew=2 > maxSkew=1 -> **rejected if `DoNotSchedule`**
- Schedule on rack-a: counts become 4,3,3,0 -> skew=4 -> worse

**The problem**: With `whenUnsatisfiable: DoNotSchedule`, no placement satisfies maxSkew=1 because the new rack starts at 0.

**Fix options:**
1. Temporarily relax the constraint:
   ```yaml
   maxSkew: 2  # allow wider skew during expansion
   ```
2. Use `whenUnsatisfiable: ScheduleAnyway` (soft constraint)
3. Scale up the deployment so pods can be placed on rack-d, then scale back down
4. Manually trigger a rollout:
   ```bash
   kubectl rollout restart deployment critical-service
   # This reschedules all pods, distributing across 4 racks
   ```

After rebalancing: 9 replicas across 4 racks = 3,2,2,2 or 2,3,2,2 (skew=1, satisfied).
</details>

### Question 3
Your company uses a 5-year refresh cycle. It is now year 4 and disk failure rates have increased from 1% to 6% annually. The CFO asks whether to extend to 7 years to save money. How do you argue against this?

<details>
<summary>Answer</summary>

**Argument against extending to 7 years:**

**1. Disk failure cost escalation:**
- Year 4: 6% failure rate across 200 disks = 12 failures/year
- Year 5 (projected): 10% = 20 failures
- Year 6 (projected): 15% = 30 failures
- Year 7 (projected): 22% = 44 failures
- Each disk replacement: $500 (disk) + $200 (labor) + risk of data loss
- Years 6-7 disk costs: 74 failures x $700 = $51,800

**2. Increasing support contract costs:**
- Vendors charge 30-60% more for extended support beyond 5 years
- Some vendors refuse to support hardware past 7 years
- Parts availability decreases (end-of-life components)

**3. Power efficiency gap:**
- Year 4 hardware uses ~30% more power per compute unit than current generation
- Year 7: ~50% more power per compute unit
- At $0.10/kWh with 100 servers at 500W: $438,000/year
- New servers at 350W equivalent performance: $306,600/year
- Power savings: $131,400/year (pays for 13 new servers)

**4. Performance opportunity cost:**
- Applications running on 7-year-old hardware are 2-3x slower per core
- Need 2-3x more servers to achieve the same throughput
- Hiring developers is more expensive than buying faster hardware

**5. Risk:**
- Cascading failures become more likely (correlated aging)
- If 5 nodes fail in the same week (common in aging batches), the cluster may not have spare capacity
- Security patches may stop being available for older firmware

**Summary for the CFO:**
"Extending to 7 years saves $200,000 in deferred CapEx but adds $150,000+ in disk replacements, $130,000 in excess power costs, and significant operational risk. The net savings is near zero, but the risk is substantially higher."
</details>

### Question 4
You are planning a staggered refresh, replacing 33 nodes per year in a 100-node cluster. You currently have Intel Xeon Gold 6330 nodes. Next year's refresh will use AMD EPYC 9554. What testing should you do before deploying the AMD nodes into your production cluster?

<details>
<summary>Answer</summary>

**Testing plan for cross-vendor CPU migration:**

**Phase 1: Hardware validation (1 week)**
- Boot the AMD servers, verify BIOS settings (SR-IOV, VT-x/AMD-V, NUMA, power management)
- Run hardware stress tests: `stress-ng`, `memtester`, `fio`
- Verify NIC driver compatibility (especially if using Mellanox/Broadcom with RDMA)
- Confirm container runtime works (containerd, kernel cgroup v2)
- Test storage: Ceph OSD performance, CSI driver compatibility

**Phase 2: Kubernetes integration (1 week)**
- Join 3 AMD nodes to a staging cluster alongside Intel nodes
- Verify kubelet starts correctly
- Test CNI (Calico/Cilium) BGP peering from AMD nodes
- Verify pod scheduling, inter-node networking (pod-to-pod across architectures)
- Run the standard networking test suite (iperf3, curl, DNS resolution)

**Phase 3: Application testing (2 weeks)**
- Deploy representative workloads on AMD nodes
- Compare performance metrics: latency, throughput, CPU utilization
- Test language-specific behavior:
  - **Java**: JVM may select different JIT optimizations on AMD vs Intel
  - **Go**: Should work identically (portable assembly)
  - **Python/NumPy**: May use different BLAS/LAPACK optimizations
  - **TensorFlow**: Check AVX-512 compatibility
- Run load tests comparing AMD vs Intel node behavior

**Phase 4: Production canary (1 week)**
- Add 3 AMD nodes to production
- Do NOT label them differently from production nodes
- Let the scheduler place normal workloads
- Monitor for 7 days: error rates, latency distributions, resource usage
- If stable, proceed with full 33-node deployment

**Key risk areas:**
- Memory model differences (AMD uses a different NUMA topology)
- `numactl` and CPU pinning may need reconfiguration
- BIOS power management settings affect performance under load
- Some monitoring tools report different CPU metrics on AMD vs Intel
</details>

---

## Hands-On Exercise: Plan a Hardware Expansion

**Task**: Design a capacity expansion plan for adding a new rack of servers to an existing cluster.

### Scenario

You have a 60-node cluster across 3 racks (20 nodes each) running at 65% CPU utilization. You need to add 20 new nodes in a 4th rack to support a 40% growth forecast.

### Steps

1. **Document current state:**
   ```bash
   kubectl get nodes -o custom-columns=\
     NAME:.metadata.name,\
     CPU:.status.allocatable.cpu,\
     MEM:.status.allocatable.memory,\
     RACK:.metadata.labels.kubedojo\\.io/rack,\
     GEN:.metadata.labels.kubedojo\\.io/hardware-gen
   ```

2. **Calculate post-expansion capacity:**
   - Current: 60 nodes x 32 cores = 1,920 cores at 65% = 1,248 cores used
   - After: 80 nodes x average cores = ? cores
   - Target utilization: < 60% (headroom for spikes)

3. **Design the node labeling scheme** for the new rack (rack, generation, performance tier)

4. **Write topology spread constraints** that span all 4 racks

5. **Create a decommission plan** for 10 oldest nodes (to happen 3 months after new rack is stable)

### Success Criteria

- [ ] Calculated current and projected utilization accurately
- [ ] Defined label taxonomy for mixed hardware
- [ ] Topology spread constraints cover rack and generation dimensions
- [ ] Decommission plan respects 80% utilization ceiling
- [ ] Monitoring plan includes new rack in all dashboards and alerts

---

## Next Module

This concludes the Day-2 Operations section. Return to the [Operations index](../operations/) to review all modules, or continue to the next section in the on-premises track.
